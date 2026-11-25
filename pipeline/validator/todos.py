# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Find every TODO marker and group it by what kind of gap it is."""
from __future__ import annotations

from typing import Any

from .loading import Content
from .model import Finding, Todo

# Last field name (or file type + field) -> group shown in the report.
GROUPS = {
    "bgs_rcs": "BGS Rock Classification Scheme codes",
    "hint_media": "Hint pictures",
    "media": "Kit pictures",
    "ma_min": "Ages of named units",
    "ma_max": "Ages of named units",
    "summary": "Summaries",
    "where_to_get": "Kit: where to get it",
    "map_unit": "BGS 625k map unit codes (crosswalk)",
    "tells_you": "“What this tells you” text",
    "label": "Labels",
    "how_to": "“How to” instructions",
    "how_to_spot": "Minerals: how to spot",
    "url": "Pack sources: URLs and terms",
    "terms": "Pack sources: URLs and terms",
    "notes": "Pack sources: URLs and terms",
}
FINDING_GROUPS = {
    "Rock page not yet written": "Rock pages not yet written",
    "Story not yet written": "Named unit stories not yet written",
}


def _field(path: tuple) -> str:
    return ".".join(f"[{p + 1}]" if isinstance(p, int) else str(p) for p in path).replace(".[", "[")


def _walk(value: Any, path: tuple = ()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, path + (i,))
    elif isinstance(value, str) and "TODO" in value:
        yield path


def _group(ftype: str, path: tuple) -> str:
    names = [p for p in path if isinstance(p, str)]
    if len(names) > 1 and len(names[-1]) == 2:      # language key, e.g. summary.en
        names = names[:-1]
    last = names[-1] if names else ftype
    if ftype == "pack_manifest" and last in ("url", "terms", "notes"):
        return GROUPS[last]
    if last in ("url", "terms", "notes"):
        return f"Other ({last})"
    return GROUPS.get(last, f"Other ({last})")


def collect_todos(content: Content, findings: list[Finding]) -> list[Todo]:
    todos: list[Todo] = []
    for ftype, docs in content.docs.items():
        for d in docs:
            for path in _walk(d.data):
                todos.append(Todo(_group(ftype, path), d.rel, d.line(*path), _field(path)))
    for stem, (path, _front, text) in sorted(content.pages.items()):
        relp = path.relative_to(content.root).as_posix()
        for n, line in enumerate(text.splitlines(), start=1):
            if "TODO" in line:
                todos.append(Todo("Rock page text", relp, n, line.strip()[:80]))
    for f in findings:
        if f.kind in FINDING_GROUPS:
            todos.append(Todo(FINDING_GROUPS[f.kind], f.file, f.line, f.message.split(",")[0]))
    return todos
