# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile content/ into one file the engine reads (build/core.json).

Inheritance rule (docs/DECISIONS.md, M2): a rock type's value for a question
is its own entry if it has one; otherwise the entry of its nearest ancestor
that has one ('inherit' means the same thing, written out). A question with no
entry anywhere up the tree is uninformative for that rock type and is left
out of the matrix.

Format of build/core.json (schema_version 1):
  taxa:        [{id, level, parents, children, order, name, field_label, page, leaf}]
  characters:  [{id, order, kind, question, how_to, safety, kit_required,
                 applies_from, cost, states: [{id, label, tells_you, hint_media}]}]
  matrix:      {leaf id: {char id: {state id: probability}}}   leaves only
  kit:         [{id, name, use, safety, default_owned}]
  packs:       {pack id: {name, contexts, human_made}}
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

SCHEMA_VERSION = 1


class CompileError(Exception):
    pass


def _load_all(root: Path, pattern: str) -> list:
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(root.glob(pattern))]


def _resolve(taxa: dict, tid: str, cid: str, seen: tuple = ()) -> dict | None:
    if tid in seen:
        raise CompileError(f"Circular parents at {tid}")
    t = taxa[tid]
    val = (t.get("characters") or {}).get(cid)
    if isinstance(val, dict):
        return val
    for parent in t["parents"]:                 # val is None or 'inherit'
        got = _resolve(taxa, parent, cid, seen + (tid,))
        if got is not None:
            return got
    return None


def compile_core(root: Path, check: bool = True) -> dict:
    """Read content under root and return the compiled core as a dict.

    With check=True the content validator runs first and any error stops the
    build (pipeline/CLAUDE.md: validate all inputs, fail loudly).
    """
    root = Path(root)
    if check:
        from validator import validate
        result = validate(root)
        if not result.ok:
            lines = [f"  {e.file}:{e.line}  {e.message}" for e in result.errors[:20]]
            raise CompileError("Content has errors; run ./check-content.\n" + "\n".join(lines))

    taxa = {t["id"]: t for t in _load_all(root, "content/core/taxonomy/**/*.yaml")}
    chars = sorted(_load_all(root, "content/core/characters/*.yaml"), key=lambda c: (c["order"], c["id"]))
    kit = yaml.safe_load((root / "content/core/kit/kit.yaml").read_text(encoding="utf-8")) or []

    children: dict[str, list[str]] = {t: [] for t in taxa}
    for tid, t in taxa.items():
        for p in t["parents"]:
            children[p].append(tid)
    for tid in children:
        children[tid].sort(key=lambda c: (taxa[c].get("order", 0), c))

    out_taxa = []
    for tid in sorted(taxa, key=lambda t: (taxa[t]["level"], taxa[t].get("order", 0), t)):
        t = taxa[tid]
        out_taxa.append({
            "id": tid, "level": t["level"], "parents": list(t["parents"]),
            "children": children[tid], "order": t.get("order", 0),
            "name": t["name"], "field_label": t.get("field_label"),
            "page": t.get("page"), "leaf": not children[tid],
            "review": t["review"]["status"],
        })

    matrix: dict[str, dict] = {}
    for t in out_taxa:
        if not t["leaf"]:
            continue
        row = {}
        for c in chars:
            vals = _resolve(taxa, t["id"], c["id"])
            if vals is not None:
                row[c["id"]] = {k: float(v) for k, v in vals.items()}
        matrix[t["id"]] = row

    out_chars = [{
        "id": c["id"], "order": c["order"], "kind": c["kind"], "question": c["question"],
        "how_to": c.get("how_to"), "safety": c.get("safety"),
        "kit_required": c.get("kit_required", []), "applies_from": c.get("applies_from", "L0"),
        "cost": c.get("cost", 1),
        "states": [{"id": s["id"], "label": s["label"], "tells_you": s["tells_you"],
                    "hint_media": s.get("hint_media")} for s in c["states"]],
        "review": c["review"]["status"],
    } for c in chars]

    out_kit = [{"id": k["id"], "name": k["name"], "use": k.get("use"), "safety": k.get("safety"),
                "default_owned": bool(k.get("default_owned", False))} for k in kit]

    packs = {}
    for manifest_path in sorted(root.glob("content/packs/*/manifest.yaml")):
        pack_dir = manifest_path.parent
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        ctx_path = pack_dir / "context.yaml"
        ctx = yaml.safe_load(ctx_path.read_text(encoding="utf-8")) if ctx_path.exists() else {}
        packs[manifest["id"]] = {
            "name": manifest["name"],
            "contexts": ctx.get("contexts", {}),
            "human_made": ctx.get("human_made", {}),
        }

    return {"schema_version": SCHEMA_VERSION, "taxa": out_taxa, "characters": out_chars,
            "matrix": matrix, "kit": out_kit, "packs": packs}


def write_core(root: Path, out: Path | None = None) -> Path:
    root = Path(root)
    out = out or root / "build/core.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    core = compile_core(root)
    # Sorted keys and fixed formatting: same content gives a byte-identical file.
    out.write_text(json.dumps(core, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out
