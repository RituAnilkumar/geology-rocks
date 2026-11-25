# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Summary of specimen testing (docs/TESTING.md section 5).

Reads every test file in the testing folder and writes
  reports/specimen-test-report.md    readable summary
  reports/specimen-test-runs.csv     all tests in one table, with outcomes
  reports/specimen-test-by-rock.csv  accuracy by rock type
"""
from __future__ import annotations

import csv
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .config import Params
from .core import Core
from .engine import AnswerError, evaluate
from .testlog import (CONFIDENCE, EXPERIENCE, NOT_IN_KEY, NOT_SURE, SKIPPED, TestLog, column,
                      parse_answers, resolve_rock)

# An answer is "surprising" when the content gives it less than this chance
# for the true rock: either the tester misread the specimen or the content
# needs another look.
SURPRISE = 0.10

OUTCOMES = {
    "named": "Named the right rock type",
    "group": "Right group, not the exact rock type",
    "undecided": "Not sure yet (no group reached the threshold)",
    "wrong": "Wrong group or rock type",
}


def outcome(core: Core, node: str, true: str) -> str:
    if not node:
        return "undecided"
    if node not in core.taxa:
        return "wrong"
    if node == true:
        return "named"
    return "group" if core.is_ancestor_or_self(node, true) else "wrong"


@dataclass
class Test:
    row: dict
    true: str | None            # leaf id, NOT_IN_KEY, "" (blank) or None (not recognised)
    then: str | None = None     # outcome as recorded at the time
    then_top_ok: bool = False
    now: str | None = None      # outcome when replayed with today's content
    now_top: str | None = None

    @property
    def label(self) -> str:
        return f"specimen {self.row.get('specimen', '?')} ({self.row.get('tester', '?')})"


def analyse(core: Core, params: Params, rows: list[dict]) -> list[Test]:
    tests = []
    for row in rows:
        t = Test(row, resolve_rock(core, row.get("true_rock", "")))
        if t.true and t.true != NOT_IN_KEY:
            t.then = outcome(core, (row.get("key_result") or "").strip(), t.true)
            t.then_top_ok = (row.get("top_rock") or "").strip() == t.true
            parsed = parse_answers(core, row)
            if parsed is not None:
                answers, skipped = parsed
                try:
                    r = evaluate(core, params, answers=answers, skipped=skipped,
                                 kit=[k for k in (row.get("kit") or "").split(";") if k] or None,
                                 mode=row.get("mode") or "expert",
                                 find_context=row.get("find_context") or None)
                    t.now = outcome(core, r.report.node or "", t.true)
                    t.now_top = r.report.top_leaf
                except AnswerError:
                    pass
        tests.append(t)
    return tests


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.0f}%" if d else "–"


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) or str(v).rstrip("%").replace(".", "", 1).isdigit() \
        or str(v) == "–" or bool(re.fullmatch(r"\d+ \(\d+%\)", str(v)))


def _table(head: list[str], rows: list[list]) -> list[str]:
    """Markdown table; columns holding only numbers are right-aligned."""
    align = ["---:" if rows and all(_is_number(r[i]) for r in rows) else "---" for i in range(len(head))]
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(align) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def _name(core: Core, tid: str) -> str:
    return core.name(tid) if tid in core.taxa else (tid or "–")


def build_report(core: Core, params: Params, tests: list[Test], files: list[str]) -> str:
    scored = [t for t in tests if t.then]
    blank = [t for t in tests if t.true == ""]
    unknown = [t for t in tests if t.true is None]
    not_in_key = [t for t in tests if t.true == NOT_IN_KEY]
    L = ["# Specimen testing report", ""]
    L.append(f"Tests found: **{len(tests)}** in {len(files)} file(s) "
             f"({', '.join(files) if files else 'none'}). "
             f"Testers: {len({t.row.get('tester') for t in tests})}. "
             f"Specimens: {len({t.row.get('specimen') for t in tests})}.")
    L.append("")
    L.append(f"- With the true rock type filled in: **{len(scored)}** (these are scored below)")
    L.append(f"- True rock type not filled in yet: {len(blank)}")
    L.append(f"- Rock not in the key: {len(not_in_key)}")
    if unknown:
        L.append(f"- ⚠ True rock type not recognised: {len(unknown)} — check the spelling: "
                 + "; ".join(f"{t.label}: “{t.row.get('true_rock')}”" for t in unknown))
    L.append("")
    if not scored:
        L.append("Nothing to score yet: fill in the true rock type for each test on the "
                 "**Test results** page of the key prototype, then run this report again.")
        return "\n".join(L) + "\n"

    # -- Overall -------------------------------------------------------------
    replayed = [t for t in scored if t.now]
    L += ["## Overall", "",
          "How the key's result compared with the true rock type. “At the time” is what "
          "the tester saw. “With today's content” replays the same answers through the "
          "current content, so you can see whether content changes since the test helped.", ""]
    rows = []
    for key, text in OUTCOMES.items():
        n_then = sum(t.then == key for t in scored)
        n_now = sum(t.now == key for t in replayed)
        rows.append([text, f"{n_then} ({_pct(n_then, len(scored))})",
                     f"{n_now} ({_pct(n_now, len(replayed))})"])
    top_then = sum(t.then_top_ok for t in scored)
    top_now = sum(t.now_top == t.true for t in replayed)
    rows.append(["Most likely rock type was the right one", f"{top_then} ({_pct(top_then, len(scored))})",
                 f"{top_now} ({_pct(top_now, len(replayed))})"])
    L += _table(["", "At the time", "With today's content"], rows)
    if len(replayed) < len(scored):
        L += ["", f"{len(scored) - len(replayed)} test(s) could not be replayed because a "
              "question or option they used has since changed."]
    L += ["", "“Wrong” is the result that matters most: the key claimed a group that does "
          "not contain the true rock. In beginner mode the key stops at the group level, "
          "so “right group” is the best possible result there.", ""]

    # -- By experience ---------------------------------------------------------
    L += ["## By tester experience", ""]
    rows = []
    for exp, text in EXPERIENCE.items():
        g = [t for t in scored if t.row.get("experience") == exp]
        if g:
            rows.append([text, len(g)] + [_pct(sum(t.then == k for t in g), len(g)) for k in OUTCOMES]
                        + [_pct(sum(t.then_top_ok for t in g), len(g))])
    L += _table(["Experience", "Tests", "Named", "Right group", "Not sure yet", "Wrong", "Most likely right"], rows)
    L.append("")

    # -- By rock type ------------------------------------------------------------
    L += ["## Accuracy by rock type", ""]
    by_rock = defaultdict(list)
    for t in scored:
        by_rock[t.true].append(t)
    rows = []
    for leaf in sorted(by_rock, key=lambda l: (-sum(t.then == "wrong" for t in by_rock[l]), _name(core, l))):
        g = by_rock[leaf]
        rows.append([_name(core, leaf), len(g)] + [sum(t.then == k for t in g) for k in OUTCOMES]
                    + [_pct(sum(t.then_top_ok for t in g), len(g))])
    L += _table(["True rock", "Tests", "Named", "Right group", "Not sure yet", "Wrong", "Most likely right"], rows)
    L += ["", "Rocks with the most wrong results are listed first.", ""]

    # -- Most common wrong answers --------------------------------------------------
    L += ["## Most common wrong answers", "",
          "When the key's most likely rock type was not the true one: what it was mistaken for.", ""]
    pairs = defaultdict(list)
    for t in scored:
        if not t.then_top_ok:
            try:
                p = float(t.row.get("top_rock_p") or 0)
            except ValueError:
                p = 0.0
            pairs[(t.true, (t.row.get("top_rock") or "").strip())].append(p)
    if pairs:
        top = sorted(pairs.items(), key=lambda kv: (-len(kv[1]), -statistics.median(kv[1])))[:10]
        L += _table(["True rock", "Key's most likely rock type", "Times", "Key's chance (median)"],
                    [[_name(core, a), _name(core, b), len(ps), f"{statistics.median(ps):.0%}"]
                     for (a, b), ps in top])
        L += ["", "A low chance means the key was still unsure and only guessing; a high chance "
              "means it was confidently wrong, which matters more."]
    else:
        L.append("None — the most likely rock type was right every time.")
    L.append("")

    # -- Questions people found hard ---------------------------------------------
    L += ["## Questions people skipped or were not sure about", "",
          "Counted over all tests, whether or not the true rock type is filled in.", ""]
    stats = {cid: Counter() for cid in core.char_order}
    for t in tests:
        for cid in core.char_order:
            v = (t.row.get(column(cid)) or "").strip()
            if v:
                stats[cid]["not_sure" if v == NOT_SURE else "skip" if v == SKIPPED else "answered"] += 1
    rows = []
    for cid, s in stats.items():
        seen = sum(s.values())
        if seen:
            hard = s["not_sure"] + s["skip"]
            rows.append((hard / seen, [core.characters[cid].data["question"]["en"], seen, s["answered"],
                                       s["not_sure"], s["skip"], _pct(hard, seen)]))
    rows.sort(key=lambda x: -x[0])
    L += _table(["Question", "Times reached", "Answered", "Not sure", "Skipped", "Not sure or skipped"],
                [r for _, r in rows])
    L.append("")

    # -- Answers that disagree with the content ----------------------------------
    L += ["## Answers that disagree with the content", "",
          f"Answers the content gives less than {SURPRISE:.0%} chance for the true rock. Each one "
          "is either a tester misreading the specimen (the question may need a clearer "
          "picture or wording) or a probability in the content that needs another look.", ""]
    surprises, answered_by_q = [], Counter()
    for t in scored:
        parsed = parse_answers(core, t.row)
        if parsed is None:
            continue
        i = core.leaf_index[t.true]
        for cid, st in parsed[0]:
            c = core.characters[cid]
            answered_by_q[cid] += 1
            labels = {s["id"]: s["label"]["en"] for s in c.data["states"]}
            if c.kind == "multi":
                for s in st:
                    p = float(c.P[i, c.states.index(s)])
                    if p < SURPRISE:
                        surprises.append((t, cid, f"ticked “{labels[s]}”", p))
            else:
                p = float(c.P[i, c.states.index(st)])
                if p < SURPRISE:
                    surprises.append((t, cid, labels[st], p))
    if surprises:
        per_q = Counter(cid for _, cid, _, _ in surprises)
        L += _table(["Question", "Surprising answers", "Out of", "Share"],
                    [[core.characters[c].data["question"]["en"], n, answered_by_q[c], _pct(n, answered_by_q[c])]
                     for c, n in per_q.most_common()])
        L += ["", "Details (up to 40):", ""]
        L += _table(["Test", "True rock", "Question", "Answer", "Content's chance"],
                    [[t.label, _name(core, t.true), core.characters[c].data["question"]["en"], a, f"{p:.0%}"]
                     for t, c, a, p in sorted(surprises, key=lambda x: x[3])[:40]])
    else:
        L.append("None.")
    L.append("")

    # -- Confidence -----------------------------------------------------------------
    rated = [t for t in scored if t.row.get("tester_confidence") in CONFIDENCE]
    if rated:
        L += ["## Tester confidence compared with the result", "",
              "Did people's gut feeling about the key's answer match how it actually did?", ""]
        rows = []
        for key, text in CONFIDENCE.items():
            g = [t for t in rated if t.row.get("tester_confidence") == key]
            if g:
                rows.append([text, len(g), _pct(sum(t.then_top_ok for t in g), len(g)),
                             _pct(sum(t.then == "wrong" for t in g), len(g))])
        L += _table(["Tester said", "Tests", "Most likely rock right", "Key's result wrong"], rows)
        L.append("")

    if not_in_key:
        L += ["## Specimens not in the key", ""]
        L += [f"- {t.label}: {t.row.get('notes') or 'no notes'}" for t in not_in_key]
        L.append("")
    noted = [t for t in tests if (t.row.get("notes") or "").strip() and t.true != NOT_IN_KEY]
    if noted:
        L += ["## Testers' notes", ""]
        L += [f"- {t.label}, true rock {_name(core, t.true) if t.true and t.true != NOT_IN_KEY else 'not filled in'}: "
              f"{t.row['notes']}" for t in noted]
        L.append("")
    return "\n".join(L) + "\n"


def write_csvs(core: Core, tests: list[Test], out: Path) -> None:
    with (out / "specimen-test-runs.csv").open("w", encoding="utf-8-sig", newline="") as f:
        cols = ["run_id", "saved_at", "tester", "experience", "specimen", "mode", "true_rock",
                "key_result", "top_rock", "outcome", "most_likely_right", "outcome_today", "file"]
        w = csv.writer(f)
        w.writerow(cols)
        for t in tests:
            r = t.row
            w.writerow([r.get("run_id"), r.get("saved_at"), r.get("tester"), r.get("experience"),
                        r.get("specimen"), r.get("mode"), _name(core, t.true) if t.true else r.get("true_rock", ""),
                        _name(core, r.get("key_result", "")), _name(core, r.get("top_rock", "")),
                        t.then or "", ("yes" if t.then_top_ok else "no") if t.then else "", t.now or "",
                        r.get("_file", "")])
    by_rock = defaultdict(list)
    for t in tests:
        if t.then:
            by_rock[t.true].append(t)
    with (out / "specimen-test-by-rock.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rock", "tests"] + list(OUTCOMES) + ["most_likely_right"])
        for leaf in sorted(by_rock, key=lambda l: _name(core, l)):
            g = by_rock[leaf]
            w.writerow([_name(core, leaf), len(g)] + [sum(t.then == k for t in g) for k in OUTCOMES]
                       + [sum(t.then_top_ok for t in g)])


def run_and_write(core: Core, params: Params, testing_dir: Path, out: Path) -> str:
    log = TestLog(testing_dir)
    files = [str(p.relative_to(log.folder)) for p in log.files()]
    tests = analyse(core, params, log.load())
    out.mkdir(parents=True, exist_ok=True)
    (out / "specimen-test-report.md").write_text(build_report(core, params, tests, files), encoding="utf-8")
    write_csvs(core, tests, out)
    scored = [t for t in tests if t.then]
    return (f"Specimen testing report written: {len(tests)} test(s), {len(scored)} with the true rock type.\n"
            f"  Report:      {out / 'specimen-test-report.md'}\n"
            f"  Spreadsheets: {out / 'specimen-test-runs.csv'}, {out / 'specimen-test-by-rock.csv'}")

