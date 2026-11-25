# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Simulation: synthetic specimens drawn from the matrix (docs/TESTING.md §4).

For each rock type, invent specimens by sampling an answer to every question
from that rock type's probabilities, then flip each answer to a random one with
the error rate ε (a user's mistake). Two ways of identifying them:

  A. "All questions": every question answered. Shows how well the content
     can separate rock types at all.
  B. "Following the key": answer the engine's top suggestion each time (full
     kit) until the most likely rock type reaches τ or nothing useful is left.
     Shows what a real user would see, and how many questions it takes.

Fixed random seed: the same content always gives the same report.
"""
from __future__ import annotations

import csv
import datetime as dt
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .config import Params
from .core import Core
from .engine import make_prior, posterior, rank_questions, report, suggestions

SEED = 20261125


def sample_specimen(core: Core, params: Params, leaf: str, rng: np.random.Generator) -> dict:
    """Answers a user might give for one specimen of leaf."""
    i = core.leaf_index[leaf]
    answers = {}
    for cid in core.char_order:
        c = core.characters[cid]
        if c.kind == "single":
            s = rng.choice(len(c.states), p=c.P[i] / c.P[i].sum())
            if rng.random() < params.error_rate:
                s = rng.integers(len(c.states))
            answers[cid] = c.states[s]
        else:
            present = rng.random(len(c.states)) < c.P[i]
            flip = rng.random(len(c.states)) < params.error_rate
            ticked = present ^ flip
            answers[cid] = [o for o, t in zip(c.states, ticked) if t]
    return answers


@dataclass
class SimResult:
    name: str
    confusion: dict[tuple[str, str], int] = field(default_factory=Counter)
    per_leaf_total: Counter = field(default_factory=Counter)
    per_leaf_correct: Counter = field(default_factory=Counter)
    reported_correct: int = 0      # reported group contains the true rock type
    reported_levels: list[int] = field(default_factory=list)
    questions: list[int] = field(default_factory=list)
    total: int = 0

    @property
    def accuracy(self) -> float:
        return sum(self.per_leaf_correct.values()) / self.total if self.total else 0.0


def _record(core: Core, res: SimResult, leaf: str, post: np.ndarray, params: Params):
    rep = report(core, params, post, "expert")
    res.total += 1
    res.per_leaf_total[leaf] += 1
    res.confusion[(leaf, rep.top_leaf)] += 1
    if rep.top_leaf == leaf:
        res.per_leaf_correct[leaf] += 1
    if rep.node is not None and core.is_ancestor_or_self(rep.node, leaf):
        res.reported_correct += 1
    res.reported_levels.append(core.level(rep.node) if rep.node else -1)


def simulate_all_questions(core: Core, params: Params, n: int, rng) -> SimResult:
    res = SimResult("All questions answered")
    prior = make_prior(core, params)
    for leaf in core.leaves:
        for _ in range(n):
            spec = sample_specimen(core, params, leaf, rng)
            post = posterior(core, params, prior, list(spec.items()))
            _record(core, res, leaf, post, params)
    return res


def simulate_key(core: Core, params: Params, n: int, rng) -> SimResult:
    res = SimResult("Following the key's suggestions")
    prior = make_prior(core, params)
    kit = [k["id"] for k in core.kit]
    for leaf in core.leaves:
        for _ in range(n):
            spec = sample_specimen(core, params, leaf, rng)
            answers = []
            post = prior
            while True:
                rep = report(core, params, post, "expert")
                if rep.p_top >= params.report_threshold:
                    break
                depth = core.level(rep.node) if rep.node else -1
                infos = rank_questions(core, params, post, answered=[c for c, _ in answers],
                                       kit=kit, depth=depth)
                nxt = suggestions(infos)
                if not nxt:
                    break
                answers.append((nxt[0], spec[nxt[0]]))
                post = posterior(core, params, prior, answers)
            res.questions.append(len(answers))
            _record(core, res, leaf, post, params)
    return res


def _most_confused(core: Core, res: SimResult, k: int = 10) -> list[tuple[str, str, float]]:
    pairs = [(t, p, cnt / res.per_leaf_total[t]) for (t, p), cnt in res.confusion.items() if t != p]
    pairs.sort(key=lambda x: (-x[2], x[0], x[1]))
    return pairs[:k]


def write_csv(core: Core, res: SimResult, path: Path):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["true rock type \\ identified as"] + [core.name(l) for l in core.leaves])
        for t in core.leaves:
            w.writerow([core.name(t)] + [res.confusion.get((t, p), 0) for p in core.leaves])


def markdown(core: Core, params: Params, a: SimResult, b: SimResult, n_all: int, n_key: int) -> str:
    name = core.name
    pct = lambda x: f"{x * 100:.0f}%"
    L = ["# Simulation report", "",
         f"Generated {dt.date.today():%d %B %Y} from the current content. "
         f"Error rate ε = {params.error_rate}, report threshold τ = {params.report_threshold}.", "",
         "The computer invents specimens of each rock type by picking answers from that rock "
         f"type's probabilities, with {pct(params.error_rate)} of answers deliberately wrong "
         "(as a real user sometimes is). It then tries to identify each one. "
         "This tests the **content**: where rock types are hard to tell apart, the "
         "probabilities or the questions need attention. Real specimens come in M3.", "",
         "## Summary", "",
         "| | All questions answered | Following the key |", "|---|---:|---:|",
         f"| Specimens per rock type | {n_all} | {n_key} |",
         f"| Most likely rock type is correct | {pct(a.accuracy)} | {pct(b.accuracy)} |",
         f"| Reported group contains the right rock type (honesty) | "
         f"{pct(a.reported_correct / a.total)} | {pct(b.reported_correct / b.total)} |",
         f"| Average questions asked | {len(core.char_order)} (all) | "
         f"{np.mean(b.questions):.1f} (range {min(b.questions)}–{max(b.questions)}) |", "",
         "“Honesty”: the app reports only as deep as the evidence supports, so "
         "it can be right at the group level even when the most likely rock type is wrong.", "",
         "## The 10 most-confused pairs (all questions answered)", "",
         "| True rock type | Identified as | How often |", "|---|---|---:|"]
    L += [f"| {name(t)} | {name(p)} | {pct(r)} |" for t, p, r in _most_confused(core, a)]
    L += ["", "## The 10 most-confused pairs (following the key)", "",
          "| True rock type | Identified as | How often |", "|---|---|---:|"]
    L += [f"| {name(t)} | {name(p)} | {pct(r)} |" for t, p, r in _most_confused(core, b)]
    L += ["", "## Accuracy by rock type", "",
          "| Rock type | All questions | Following the key | Questions (key, average) |",
          "|---|---:|---:|---:|"]
    qs_by_leaf: dict[str, list[int]] = {}
    i = 0
    for leaf in core.leaves:
        qs_by_leaf[leaf] = b.questions[i: i + n_key]
        i += n_key
    rows = sorted(core.leaves, key=lambda l: (a.per_leaf_correct[l] / a.per_leaf_total[l], name(l)))
    for l in rows:
        L.append(f"| {name(l)} | {pct(a.per_leaf_correct[l] / a.per_leaf_total[l])} | "
                 f"{pct(b.per_leaf_correct[l] / b.per_leaf_total[l])} | {np.mean(qs_by_leaf[l]):.1f} |")
    L += ["", "Full confusion tables (open in a spreadsheet): "
          "`simulation-confusion-all-questions.csv`, `simulation-confusion-key.csv`.", ""]
    return "\n".join(L)


def run_and_write(core: Core, params: Params, out_dir: Path, n_all: int = 300, n_key: int = 60) -> str:
    rng = np.random.default_rng(SEED)
    a = simulate_all_questions(core, params, n_all, rng)
    b = simulate_key(core, params, n_key, rng)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "simulation-report.md").write_text(markdown(core, params, a, b, n_all, n_key), encoding="utf-8")
    write_csv(core, a, out_dir / "simulation-confusion-all-questions.csv")
    write_csv(core, b, out_dir / "simulation-confusion-key.csv")
    return (f"Simulation done: {pct(a.accuracy)} correct with all questions, "
            f"{pct(b.accuracy)} following the key ({np.mean(b.questions):.1f} questions on average).\n"
            f"Report: {out_dir / 'simulation-report.md'}")


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"
