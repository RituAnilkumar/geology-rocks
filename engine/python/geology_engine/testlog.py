# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Specimen testing log (docs/TESTING.md section 5).

Each saved test is one row in a CSV file in the testing folder (default
`testing/`, git-ignored: it holds testers' names). Files from other testers'
laptops can be dropped into the same folder; rows are matched by `run_id`, so
the same test appearing in two files is only counted once.

Answer cells hold state ids (several ticked options joined with ";"), or the
markers below. Files are written as UTF-8 with a byte-order mark so that
spreadsheet programs show accents and dashes correctly.
"""
from __future__ import annotations

import csv
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import Params
from .core import Core
from .engine import AnswerError, evaluate

NOT_SURE = "NOT SURE"
SKIPPED = "SKIPPED"
NONE_TICKED = "(none ticked)"
NOT_IN_KEY = "not_in_key"

EXPERIENCE = {"beginner": "Beginner", "student": "Geology student", "geologist": "Geologist"}
CONFIDENCE = {"very_sure": "Very sure", "fairly_sure": "Fairly sure", "unsure": "Not sure",
              "think_wrong": "I think it's wrong"}

FIXED = ["run_id", "saved_at", "tester", "experience", "specimen", "find_context", "mode", "kit",
         "key_result", "key_result_p", "top_rock", "top_rock_p", "second_rock", "second_rock_p",
         "questions_answered", "not_sure", "skipped", "tester_confidence", "true_rock", "notes",
         "answer_order"]


class TestLogError(ValueError):
    """A problem the person using the page can fix (shown to them as is)."""
    __test__ = False          # not a pytest test class, despite the name


def column(char_id: str) -> str:
    return char_id.removeprefix("char.")


def columns(core: Core) -> list[str]:
    return FIXED + [column(c) for c in core.char_order]


def _text(value, limit: int = 500) -> str:
    """Free text from the page: one line, trimmed, and never read as a
    spreadsheet formula."""
    s = " ".join(str(value or "").split())[:limit]
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


def make_row(core: Core, params: Params, body: dict, *, now: datetime | None = None,
             run_id: str | None = None) -> dict:
    tester, specimen = _text(body.get("tester"), 80), _text(body.get("specimen"), 80)
    if not tester or not specimen:
        raise TestLogError("Please fill in the specimen number and the tester's name before saving.")
    experience = body.get("experience") or ""
    if experience not in EXPERIENCE:
        raise TestLogError("Please choose the tester's experience level before saving.")
    confidence = body.get("confidence") or ""
    if confidence and confidence not in CONFIDENCE:
        raise TestLogError(f"Unknown confidence {confidence!r}.")

    answers = [(a["char"], a["state"]) for a in body.get("answers", [])]
    skipped = dict(body.get("skipped") or {})
    if not answers and not skipped:
        raise TestLogError("There are no answers to save yet.")
    for cid, kind in skipped.items():
        if cid not in core.characters or kind not in ("skip", "not_sure"):
            raise AnswerError(f"Unknown skipped question {cid!r} ({kind!r}).")
    r = evaluate(core, params, answers=answers, skipped=list(skipped), kit=body.get("kit"),
                 mode=body.get("mode", "expert"), find_context=body.get("find_context") or None)
    rep = r.report

    order = [c for c in body.get("order", []) if c in skipped or c in dict(answers)]
    order += [c for c, _ in answers if c not in order] + [c for c in skipped if c not in order]
    second = rep.ranked[1] if len(rep.ranked) > 1 else (None, 0.0)
    row = {
        "run_id": run_id or uuid.uuid4().hex[:12],
        "saved_at": (now or datetime.now(timezone.utc)).astimezone().isoformat(timespec="seconds"),
        "tester": tester, "experience": experience, "specimen": specimen,
        "find_context": body.get("find_context") or "", "mode": body.get("mode", "expert"),
        "kit": ";".join(sorted(body.get("kit") or [])),
        "key_result": rep.node or "", "key_result_p": f"{rep.p:.3f}" if rep.node else "",
        "top_rock": rep.top_leaf, "top_rock_p": f"{rep.p_top:.3f}",
        "second_rock": second[0] or "", "second_rock_p": f"{second[1]:.3f}" if second[0] else "",
        "questions_answered": str(len(answers)),
        "not_sure": str(sum(k == "not_sure" for k in skipped.values())),
        "skipped": str(sum(k == "skip" for k in skipped.values())),
        "tester_confidence": confidence, "true_rock": "", "notes": _text(body.get("notes")),
        "answer_order": " > ".join(column(c) for c in order),
    }
    for cid in core.char_order:
        row[column(cid)] = ""
    for cid, st in answers:
        row[column(cid)] = (";".join(st) or NONE_TICKED) if isinstance(st, list) else st
    for cid, kind in skipped.items():
        row[column(cid)] = NOT_SURE if kind == "not_sure" else SKIPPED
    return row


def parse_answers(core: Core, row: dict):
    """Turn a saved row back into (answers, skipped) for the current content.
    Returns None if the row uses questions or options that no longer exist."""
    answers, skipped = [], []
    order = [c.strip() for c in (row.get("answer_order") or "").split(">") if c.strip()]
    cols = order + [column(c) for c in core.char_order if column(c) not in order]
    for col in cols:
        value = (row.get(col) or "").strip()
        if not value:
            continue
        cid = "char." + col
        if cid not in core.characters:
            return None
        c = core.characters[cid]
        if value in (NOT_SURE, SKIPPED):
            skipped.append(cid)
        elif c.kind == "multi":
            ticks = [] if value == NONE_TICKED else [s.strip() for s in value.split(";") if s.strip()]
            if any(s not in c.states for s in ticks):
                return None
            answers.append((cid, ticks))
        else:
            if value not in c.states:
                return None
            answers.append((cid, value))
    return answers, skipped


def resolve_rock(core: Core, value: str) -> str | None:
    """The true rock as typed (id, or English name in any case). Returns a
    leaf id, NOT_IN_KEY, "" (not filled in) or None (not recognised)."""
    v = (value or "").strip()
    if not v:
        return ""
    low = v.lower().replace("_", " ")
    if low in ("not in key", "not in the key"):
        return NOT_IN_KEY
    if v in core.leaf_index:
        return v
    for leaf in core.leaves:
        if core.name(leaf).lower() == low:
            return leaf
    return None


class TestLog:
    """All test files in one folder. Safe to use from several web requests."""
    __test__ = False

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.default_file = self.folder / "test-runs.csv"
        self._lock = threading.Lock()

    def files(self) -> list[Path]:
        if not self.folder.is_dir():
            return []
        return sorted(p for p in self.folder.rglob("*.csv") if p.is_file())

    @staticmethod
    def _read(path: Path) -> tuple[list[str], list[dict]]:
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = [dict(r) for r in reader]
            return list(reader.fieldnames or []), rows

    @staticmethod
    def _write(path: Path, header: list[str], rows: list[dict]) -> None:
        tmp = path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        try:
            os.replace(tmp, path)
        except PermissionError as exc:
            tmp.unlink(missing_ok=True)
            raise TestLogError(f"Could not save to {path.name}: it may be open in a spreadsheet "
                               "program. Close it there and try again.") from exc

    def load(self) -> list[dict]:
        """Every test from every file, each once. Adds a `_file` key."""
        seen, out = set(), []
        for path in self.files():
            try:
                _, rows = self._read(path)
            except (OSError, csv.Error, UnicodeDecodeError):
                continue
            for r in rows:
                rid = (r.get("run_id") or "").strip()
                if not rid or rid in seen:
                    continue
                seen.add(rid)
                r["_file"] = str(path.relative_to(self.folder))
                out.append(r)
        return out

    def append(self, row: dict, header: list[str]) -> int:
        with self._lock:
            self.folder.mkdir(parents=True, exist_ok=True)
            rows, old = [], []
            if self.default_file.exists():
                old, rows = self._read(self.default_file)
            full = old + [h for h in header if h not in old]
            rows.append(row)
            self._write(self.default_file, full, rows)
            return len(rows)

    def set_truth(self, run_id: str, true_rock: str) -> None:
        found = False
        with self._lock:
            for path in self.files():
                header, rows = self._read(path)
                hit = [r for r in rows if r.get("run_id") == run_id]
                if not hit:
                    continue
                found = True
                if "true_rock" not in header:
                    header.append("true_rock")
                for r in hit:
                    r["true_rock"] = true_rock
                self._write(path, header, rows)
        if not found:
            raise TestLogError("That test could not be found; reload the page.")
