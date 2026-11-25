# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scenario (golden test) runner: docs/TESTING.md section 3.

Plays each scenario's answers through the engine and checks every expectation.
Results are written for a non-developer: what was expected, what the engine
concluded instead.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import Params
from .core import Core, level_index
from .engine import Result, evaluate


@dataclass
class Check:
    step: int                 # 1-based step number
    expectation: str          # e.g. "top_leaf_is"
    ok: bool
    expected: str             # plain-language
    actual: str               # plain-language


@dataclass
class ScenarioResult:
    id: str
    title: str
    file: str
    checks: list[Check] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and all(c.ok for c in self.checks)


def _pct(p: float) -> str:
    return f"{p * 100:.0f}%"


def _describe(core: Core, r: Result) -> str:
    rep = r.report
    where = f"{core.name(rep.node)} ({_pct(rep.p)})" if rep.node else "nothing yet"
    return f"reported {where}; most likely {core.name(rep.top_leaf)} ({_pct(rep.p_top)})"


def _check(core: Core, r: Result, key: str, val) -> tuple[bool, str, str]:
    """Return (ok, expected text, actual text) for one expectation."""
    rep = r.report
    name = core.name
    p = lambda node: float(r.posterior[core.mask[node]].sum())
    if key == "top_leaf_is":
        return rep.top_leaf == val, f"most likely rock is {name(val)}", _describe(core, r)
    if key == "top_leaf_in":
        return rep.top_leaf in val, "most likely rock is one of " + ", ".join(map(name, val)), _describe(core, r)
    if key == "reported_node_is":
        return rep.node == val, f"reports {name(val)}", _describe(core, r)
    if key == "reported_node_is_ancestor_of":
        ok = rep.node is not None and core.is_ancestor_or_self(rep.node, val)
        return ok, f"reports {name(val)} or a broader group containing it", _describe(core, r)
    if key == "reported_level_at_least":
        got = core.level(rep.node) if rep.node else -1
        return got >= level_index(val), f"reports at level {val} or deeper", \
            _describe(core, r) + f" (level {rep.node and core.taxa[rep.node]['level'] or 'none'})"
    if key == "p_at_least":
        bad = {n: p(n) for n, v in val.items() if p(n) < v}
        exp = "; ".join(f"{name(n)} at least {_pct(v)}" for n, v in val.items())
        act = "; ".join(f"{name(n)} is {_pct(p(n))}" for n in val)
        return not bad, exp, act
    if key == "p_at_most":
        bad = {n: p(n) for n, v in val.items() if p(n) > v}
        exp = "; ".join(f"{name(n)} at most {_pct(v)}" for n, v in val.items())
        act = "; ".join(f"{name(n)} is {_pct(p(n))}" for n in val)
        return not bad, exp, act
    q = lambda c: core.characters[c].data["question"]["en"]
    if key == "not_suggested":
        hit = [c for c in val if c in r.suggested]
        return not hit, "never suggests: " + "; ".join(map(q, val)), \
            "suggested: " + ("; ".join(map(q, r.suggested)) or "nothing")
    if key == "suggested_first_in":
        first = r.suggested[0] if r.suggested else None
        return first in val, "first suggestion is one of: " + "; ".join(map(q, val)), \
            "first suggestion: " + (q(first) if first else "nothing")
    raise ValueError(f"Unknown expectation '{key}'")


def run_scenario(core: Core, params: Params, data: dict, file: str = "") -> ScenarioResult:
    res = ScenarioResult(data["id"], data["title"], file)
    setup = data.get("setup") or {}
    kit = setup.get("kit")
    if kit is None:
        kit = [k["id"] for k in core.kit if k["default_owned"]]
        res.notes.append("No kit listed: used the default kit.")
    prior_kind = setup.get("prior", "uniform")
    find_context = setup.get("find_context")
    explicit = setup.get("explicit_prior") if prior_kind == "explicit" else None
    if setup.get("location"):
        res.notes.append("Location priors are not built yet (milestone M7); location ignored.")
    answers, skipped = [], []
    try:
        for i, step in enumerate(data["steps"], start=1):
            ans = step.get("answer")
            if ans:
                answers.append((ans["char"], ans["state"]))
            expect = step.get("expect") or {}
            if not expect:
                continue
            r = evaluate(core, params, answers=answers, skipped=skipped, kit=kit,
                         mode=setup.get("mode", "expert"), find_context=find_context,
                         pack=setup.get("pack"), explicit_prior=explicit)
            for key, val in expect.items():
                ok, exp, act = _check(core, r, key, val)
                res.checks.append(Check(i, key, ok, exp, act))
    except Exception as exc:          # report, don't crash the whole run
        res.error = f"Could not run: {exc}"
    return res


def run_all(core: Core, params: Params, scenario_dir: Path) -> list[ScenarioResult]:
    results = []
    for path in sorted(Path(scenario_dir).glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        results.append(run_scenario(core, params, data, path.name))
    return results


def format_results(results: list[ScenarioResult]) -> str:
    passed = sum(r.ok for r in results)
    lines = []
    for r in results:
        lines.append(f"{'PASS' if r.ok else 'FAIL'}  {r.title}  ({r.file})")
        if r.error:
            lines.append(f"      {r.error}")
        for c in r.checks:
            if not c.ok:
                lines.append(f"      step {c.step}: expected {c.expected}")
                lines.append(f"              but {c.actual}")
        for n in r.notes:
            lines.append(f"      note: {n}")
    lines.append("")
    icon = "✅" if passed == len(results) else "❌"
    lines.append(f"{icon} {passed} of {len(results)} scenarios passed.")
    return "\n".join(lines)
