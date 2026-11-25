# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Plain-language Markdown report and a short terminal summary."""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict

from .model import Finding, Result

STATUSES = [("draft", "Draft"), ("in_review", "In review"), ("approved", "Approved")]


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _loc(f) -> str:
    return f"`{f.file}`" + (f" line {f.line}" if f.line else "")


def _findings_table(items: list[Finding]) -> list[str]:
    out = ["| Where | Problem |", "|---|---|"]
    for f in sorted(items, key=lambda f: (f.file, f.line or 0)):
        out.append(f"| {_loc(f)} | {_cell(f.message)} |")
    return out


def _details(summary: str, body: list[str], open_: bool = False) -> list[str]:
    return [f"<details{' open' if open_ else ''}><summary>{summary}</summary>", "", *body, "",
            "</details>", ""]


def markdown_report(result: Result, today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    errors, warnings, todos = result.errors, result.warnings, result.todos
    lines = ["# Content check report", ""]
    if errors:
        lines.append(f"**Result: \u274c {len(errors)} error{'s' if len(errors) != 1 else ''} "
                     f"\u2014 these must be fixed.**")
    else:
        lines.append("**Result: \u2705 no errors.** The content is consistent and can be built.")
    lines += [
        "",
        f"Checked {result.files_checked} files on {today:%d %B %Y}. "
        f"Errors: {len(errors)} \u00b7 Warnings: {len(warnings)} \u00b7 TODOs: {len(todos)}",
        "",
        "- **Errors** are mistakes that would break the app (a broken link between files, "
        "probabilities that don't add up, a missing licence). They make the check fail.",
        "- **Warnings** are worth a look but don't fail the check.",
        "- **TODOs** are gaps deliberately left to fill in later.",
        "",
    ]

    lines += [f"## Errors ({len(errors)})", ""]
    if errors:
        by_kind = defaultdict(list)
        for f in errors:
            by_kind[f.kind].append(f)
        for kind in sorted(by_kind):
            lines += [f"### {kind} ({len(by_kind[kind])})", "", *_findings_table(by_kind[kind]), ""]
    else:
        lines += ["None.", ""]

    lines += [f"## Warnings ({len(warnings)})", ""]
    if warnings:
        by_kind = defaultdict(list)
        for f in warnings:
            by_kind[f.kind].append(f)
        for kind in sorted(by_kind):
            lines += _details(f"<b>{kind}</b> ({len(by_kind[kind])})", _findings_table(by_kind[kind]))
    else:
        lines += ["None.", ""]

    lines += ["## Review status", "",
              "Nothing is used in a release until a reviewer marks it approved.", "",
              "| Item type | " + " | ".join(n for _, n in STATUSES) + " | Total |",
              "|---|" + "---:|" * (len(STATUSES) + 1)]
    totals = Counter()
    for label in sorted(result.review_counts):
        c = result.review_counts[label]
        totals.update(c)
        lines.append(f"| {label} | " + " | ".join(str(c.get(s, 0)) for s, _ in STATUSES) +
                     f" | {sum(c.values())} |")
    lines.append("| **All** | " + " | ".join(f"**{totals.get(s, 0)}**" for s, _ in STATUSES) +
                 f" | **{sum(totals.values())}** |")
    lines.append("")

    lines += [f"## TODOs by type ({len(todos)})", ""]
    if todos:
        groups = defaultdict(list)
        for t in todos:
            groups[t.group].append(t)
        order = sorted(groups, key=lambda g: (g.startswith("Other"), -len(groups[g]), g))
        lines += ["| Type | Count |", "|---|---:|"]
        lines += [f"| {_cell(g)} | {len(groups[g])} |" for g in order]
        lines.append("")
        for g in order:
            body = [f"- `{t.file}`" + (f" line {t.line}" if t.line else "") + f" \u2014 {_cell(t.where)}"
                    for t in sorted(groups[g], key=lambda t: (t.file, t.line or 0))]
            lines += _details(f"<b>{_cell(g)}</b> ({len(groups[g])})", body)
    else:
        lines += ["None.", ""]
    return "\n".join(lines).rstrip() + "\n"


def terminal_summary(result: Result, report_path: str | None) -> str:
    out = []
    if result.ok:
        out.append(f"\u2705 Content check passed: {result.files_checked} files, no errors.")
    else:
        out.append(f"\u274c Content check FAILED: {len(result.errors)} error(s) in "
                   f"{result.files_checked} files.")
        out.append("")
        for f in sorted(result.errors, key=lambda f: (f.file, f.line or 0)):
            where = f.file + (f":{f.line}" if f.line else "")
            out.append(f"  ERROR  {where}")
            out.append(f"         {f.message}")
        out.append("")
    out.append(f"   Warnings: {len(result.warnings)}   TODOs: {len(result.todos)}")
    if report_path:
        out.append(f"   Full report: {report_path}")
    return "\n".join(out)
