# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Local web prototype of the key (a testing tool, not the app).

Serves one page and a small JSON API on http://127.0.0.1:<port>/ only — it is
not reachable from other computers. Python standard library only.

  GET  /api/core      questions, kit, find contexts, rock names
  POST /api/evaluate  {answers:[{char,state}], skipped:[char], kit:[id],
                       mode, find_context}  ->  result for the page
"""
from __future__ import annotations

import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ..config import Params
from ..core import Core
from ..engine import AnswerError, evaluate

STATIC = Path(__file__).parent / "static"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8"}


def pct(p: float) -> str:
    if p >= 0.995:
        return ">99%"
    if p < 0.01:
        return "<1%"
    return f"{p * 100:.0f}%"


def factor_phrase(f: float) -> str:
    if f >= 3:
        return "much more likely"
    if f >= 1.25:
        return "more likely"
    if f <= 1 / 3:
        return "much less likely"
    if f <= 0.8:
        return "less likely"
    return "little change"


def core_payload(core: Core, params: Params) -> dict:
    pack_id = next(iter(core.packs), None)
    contexts = []
    if pack_id:
        contexts = [{"id": k, "label": v["label"]["en"], "human": v["human"]}
                    for k, v in core.packs[pack_id]["contexts"].items()]
    return {
        "characters": [{
            "id": c.id, "kind": c.kind, "order": c.order,
            "question": c.data["question"]["en"],
            "how_to": (c.data.get("how_to") or {}).get("en"),
            "safety": (c.data.get("safety") or {}).get("en"),
            "kit_required": c.kit_required,
            "states": [{"id": s["id"], "label": s["label"]["en"], "tells_you": s["tells_you"]["en"],
                        "picture": s.get("hint_media") not in (None, "TODO")}
                       for s in c.data["states"]],
        } for c in (core.characters[i] for i in core.char_order)],
        "kit": [{"id": k["id"], "name": k["name"]["en"], "default_owned": k["default_owned"],
                 "safety": (k.get("safety") or {}).get("en") if isinstance(k.get("safety"), dict) else None}
                for k in core.kit],
        "pack": pack_id,
        "contexts": contexts,
        "params": {"tau": params.report_threshold, "epsilon": params.error_rate},
    }


def evaluate_payload(core: Core, params: Params, body: dict) -> dict:
    answers = [(a["char"], a["state"]) for a in body.get("answers", [])]
    r = evaluate(core, params, answers=answers, skipped=body.get("skipped", []),
                 kit=body.get("kit"), mode=body.get("mode", "expert"),
                 find_context=body.get("find_context") or None)
    rep = r.report
    name = core.name
    top_name, node_name = name(rep.top_leaf), name(rep.node) if rep.node else None
    if rep.node is None:
        phrase = f"Not sure yet — most likely {top_name.lower()} ({pct(rep.p_top)})"
    elif rep.node == rep.top_leaf:
        phrase = f"{node_name} ({pct(rep.p)})"
    else:
        phrase = f"{node_name} ({pct(rep.p)}) — most likely {top_name.lower()} ({pct(rep.p_top)})"

    def group_of(leaf: str) -> str:
        t = core.taxa[leaf]
        while t["parents"] and core.taxa[t["parents"][0]]["level"] != "L0":
            t = core.taxa[t["parents"][0]]
        return t["name"]["en"]

    trace = []
    for step in r.trace:
        c = core.characters[step.char]
        states = step.state if isinstance(step.state, list) else [step.state]
        st = {s["id"]: s for s in c.data["states"]}
        trace.append({
            "char": step.char, "question": c.data["question"]["en"],
            "answers": [{"label": st[s]["label"]["en"], "tells_you": st[s]["tells_you"]["en"]} for s in states],
            "changes": [{"name": name(ch["leaf"]), "before": pct(ch["before"]), "after": pct(ch["after"]),
                         "factor": round(ch["factor"], 2), "phrase": factor_phrase(ch["factor"])}
                        for ch in step.changes],
        })
    return {
        "phrase": phrase,
        "report": {"node": rep.node, "p": rep.p, "top_leaf": rep.top_leaf, "p_top": rep.p_top,
                   "path": [{"id": n, "name": name(n), "p": pct(p), "level": core.taxa[n]["level"]}
                            for n, p in rep.path]},
        "candidates": [{"id": l, "name": name(l), "p": p, "pct": pct(p), "group": group_of(l)}
                       for l, p in rep.ranked],
        "suggested": r.suggested,
        "questions": [{"char": q.char, "gain": round(q.gain, 3), "kit_ok": q.kit_ok,
                       "eligible": q.eligible, "suggested": q.suggested} for q in r.questions],
        "trace": trace,
        "done": not r.suggested,
    }


def make_handler(core: Core, params: Params):
    core_json = json.dumps(core_payload(core, params)).encode()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):      # keep the terminal quiet
            pass

        def _send(self, status, body: bytes, ctype="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/api/core":
                return self._send(HTTPStatus.OK, core_json)
            name = "index.html" if path in ("/", "") else path.lstrip("/")
            f = (STATIC / name).resolve()
            if STATIC.resolve() not in f.parents or not f.is_file():
                return self._send(HTTPStatus.NOT_FOUND, b"Not found", "text/plain")
            self._send(HTTPStatus.OK, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))

        def do_POST(self):
            if self.path != "/api/evaluate":
                return self._send(HTTPStatus.NOT_FOUND, b"{}")
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                out = evaluate_payload(core, params, body)
            except (AnswerError, KeyError, ValueError) as exc:
                return self._send(HTTPStatus.BAD_REQUEST, json.dumps({"error": str(exc)}).encode())
            self._send(HTTPStatus.OK, json.dumps(out).encode())

    return Handler


def serve(core: Core, params: Params, port: int = 8765, open_browser: bool = True):
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(core, params))
    url = f"http://localhost:{port}/"
    print(f"Geology Rocks key prototype is running.\n\n  Open this in your browser:  {url}\n\n"
          f"Leave this window open while you use it. Press Ctrl+C here to stop.")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
