# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scoring engine: the reference implementation of docs/SCORING.md.

Pure functions, no file or network access. Section numbers refer to SCORING.md.

An answer is (char_id, state) where state is a state id for single-choice
characters, or a list of ticked option ids for multi-select characters
(unticked options carry no information). "Skip" and "Not sure" are not answers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable, Sequence

import numpy as np

from .config import Params
from .core import Core, level_index

Answer = tuple[str, "str | Sequence[str]"]


class AnswerError(ValueError):
    pass


# -- 1. Prior ----------------------------------------------------------------

def make_prior(core: Core, params: Params, *, find_context: str | None = None,
               pack: str | None = None, explicit: dict[str, float] | None = None) -> np.ndarray:
    """Starting probabilities over rock types (leaves).

    - explicit: weights on any nodes; a node's weight is shared equally by its leaves.
    - find_context (until location priors exist, M7): the context's 'human' weight
      goes to human-made rock types, shared by the pack's human_made proportions;
      the rest is shared equally by all natural rock types.
    - otherwise uniform.
    Every rock type gets at least the floor ρ, then the whole is normalised.
    """
    if explicit:
        raw = np.zeros(core.n)
        for node, w in explicit.items():
            m = core.mask[node]
            raw[m] += w / m.sum()
    elif find_context:
        raw = _context_prior(core, find_context, pack)
    else:
        raw = np.full(core.n, 1.0 / core.n)
    raw = raw / raw.sum() if raw.sum() > 0 else np.full(core.n, 1.0 / core.n)
    floored = np.maximum(raw, params.prior_floor)
    return floored / floored.sum()


def _context_prior(core: Core, find_context: str, pack: str | None) -> np.ndarray:
    if pack is None:
        packs = [p for p in core.packs if find_context in core.packs[p]["contexts"]]
        if not packs:
            raise AnswerError(f"Unknown find context '{find_context}'")
        pack = packs[0]
    ctx = core.packs[pack]["contexts"].get(find_context)
    if ctx is None:
        raise AnswerError(f"Unknown find context '{find_context}' in pack {pack}")
    human_made = core.packs[pack]["human_made"]
    # Human-made rock types: every leaf under the top-level group(s) that the
    # pack's human_made entries belong to (no IDs hard-coded here).
    human_roots = {r for r in core.roots for t in human_made if core.is_ancestor_or_self(r, t)}
    human = np.zeros(core.n, dtype=bool)
    for r in human_roots:
        human |= core.mask[r]
    raw = np.zeros(core.n)
    weights = np.zeros(core.n)
    for t, w in human_made.items():
        m = core.mask[t]
        weights[m] += w / m.sum()
    if human.any():
        if weights[human].sum() > 0:
            raw[human] = ctx["human"] * weights[human] / weights[human].sum()
        else:
            raw[human] = ctx["human"] / human.sum()
    natural = ~human
    if natural.any():
        raw[natural] = (1.0 - ctx["human"]) / natural.sum()
    return raw


# -- 2. Likelihood ------------------------------------------------------------

def log_likelihood(core: Core, params: Params, char_id: str, state) -> np.ndarray:
    """log L(answer | rock type) for every rock type."""
    if char_id not in core.characters:
        raise AnswerError(f"Unknown question '{char_id}'")
    c = core.characters[char_id]
    eps = params.error_rate
    if c.kind == "single":
        if not isinstance(state, str):
            raise AnswerError(f"{char_id} takes one answer")
        if state not in c.states:
            raise AnswerError(f"'{state}' is not an answer of {char_id}")
        k = len(c.states)
        return np.log((1 - eps) * c.P[:, c.states.index(state)] + eps / k)
    ticked = [state] if isinstance(state, str) else list(state)
    out = np.zeros(core.n)
    for o in ticked:
        if o not in c.states:
            raise AnswerError(f"'{o}' is not an option of {char_id}")
        out += np.log((1 - eps) * c.P[:, c.states.index(o)] + eps / 2)
    return out


# -- 3. Posterior -------------------------------------------------------------

def _normalise_log(logp: np.ndarray) -> np.ndarray:
    m = logp.max()
    p = np.exp(logp - m)
    return p / p.sum()


def posterior(core: Core, params: Params, prior: np.ndarray, answers: Iterable[Answer]) -> np.ndarray:
    seen = set()
    logp = np.log(prior)
    for char_id, state in answers:
        if char_id in seen:
            raise AnswerError(f"{char_id} answered twice")
        seen.add(char_id)
        logp = logp + log_likelihood(core, params, char_id, state)
    return _normalise_log(logp)


def node_probability(core: Core, post: np.ndarray, node: str) -> float:
    return float(post[core.mask[node]].sum())


# -- 4. Hierarchical reporting ------------------------------------------------

@dataclass
class Report:
    node: str | None              # None = nothing confident yet (not even natural vs human-made)
    p: float
    path: list[tuple[str, float]]  # from top level down to node
    top_leaf: str
    p_top: float
    ranked: list[tuple[str, float]]


def report(core: Core, params: Params, post: np.ndarray, mode: str = "expert") -> Report:
    cap = level_index(params.beginner_max_level) if mode == "beginner" else len(core.raw["taxa"])
    children, node, p_node, path = core.roots, None, 1.0, []
    while children:
        probs = [(node_probability(core, post, c), c) for c in children]
        best_p = max(p for p, _ in probs)
        best = [c for p, c in probs if p == best_p][0]   # first in display order on ties
        if best_p < params.report_threshold or core.level(best) > cap:
            break
        node, p_node = best, best_p
        path.append((best, best_p))
        children = core.taxa[best]["children"]
    order = sorted(range(core.n), key=lambda i: (-post[i], core.leaves[i]))
    ranked = [(core.leaves[i], float(post[i])) for i in order]
    return Report(node, p_node, path, ranked[0][0], ranked[0][1], ranked)


# -- 5. Next-question selection -----------------------------------------------

def entropy_bits(p: np.ndarray) -> np.ndarray:
    """Entropy along the last axis, in bits."""
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(p > 0, p * np.log2(p), 0.0)
    return -terms.sum(axis=-1)


@lru_cache(maxsize=None)
def _tick_patterns(m: int) -> np.ndarray:
    """All 2^m tick patterns for an m-option multi-select question."""
    return ((np.arange(2 ** m)[:, None] >> np.arange(m)) & 1).astype(float)


def expected_gain(core: Core, params: Params, post: np.ndarray, char_id: str) -> float:
    """Expected information gain (bits) of asking char_id now (SCORING.md §5).

    Multi-select: outcomes are all tick patterns; a pattern's probability uses
    each option's present/absent likelihood, and the resulting posterior uses
    ticked options only (unticked = no information), exactly as the engine
    will update after the answer.
    """
    c = core.characters[char_id]
    eps = params.error_rate
    h0 = float(entropy_bits(post))
    if c.kind == "single":
        L = (1 - eps) * c.P + eps / len(c.states)          # (n, k)
        joint = post[:, None] * L                           # (n, k)
        p_s = joint.sum(axis=0)                             # (k,)
        post_s = (joint / p_s).T                            # (k, n)
        return h0 - float((p_s * entropy_bits(post_s)).sum())
    q = (1 - eps) * c.P + eps / 2                           # (n, m) P(ticked | rock)
    B = _tick_patterns(len(c.states))                       # (2^m, m)
    log_q, log_not = np.log(q), np.log1p(-q)
    p_pattern_given_t = np.exp(B @ log_q.T + (1 - B) @ log_not.T)   # (2^m, n)
    p_pattern = p_pattern_given_t @ post                    # (2^m,)
    upd = post[None, :] * np.exp(B @ log_q.T)               # update from ticked only
    upd = upd / upd.sum(axis=1, keepdims=True)
    return h0 - float((p_pattern * entropy_bits(upd)).sum())


@dataclass
class QuestionInfo:
    char: str
    gain: float
    kit_ok: bool
    eligible: bool       # level reached allows it (applies_from)
    suggested: bool = False


def rank_questions(core: Core, params: Params, post: np.ndarray, *, answered: Iterable[str],
                   skipped: Iterable[str] = (), kit: Iterable[str] | None = None,
                   depth: int = -1) -> list[QuestionInfo]:
    """Every unanswered question with its gain; the top κ eligible ones are marked suggested.

    depth = level index of the reported node (-1 when nothing is reported yet).
    kit=None means "kit unknown": no kit filter.
    """
    answered, skipped = set(answered), set(skipped)
    kit = None if kit is None else set(kit)
    infos = []
    for cid in core.char_order:
        if cid in answered:
            continue
        c = core.characters[cid]
        infos.append(QuestionInfo(
            char=cid, gain=expected_gain(core, params, post, cid),
            kit_ok=kit is None or set(c.kit_required) <= kit,
            eligible=c.applies_from <= depth + 1))
    candidates = [q for q in infos
                  if q.eligible and q.kit_ok and q.char not in skipped and q.gain >= params.min_gain_bits]
    # Highest gain first; ties (to 1e-12) broken by character order.
    order = {cid: i for i, cid in enumerate(core.char_order)}
    candidates.sort(key=lambda q: (-round(q.gain, 12), order[q.char]))
    for q in candidates[: params.max_suggestions]:
        q.suggested = True
    return infos


def suggestions(infos: list[QuestionInfo]) -> list[str]:
    s = [q for q in infos if q.suggested]
    s.sort(key=lambda q: -round(q.gain, 12))  # stable: keeps character order on ties
    return [q.char for q in s]


# -- 6. Explanation trace -----------------------------------------------------

@dataclass
class TraceStep:
    char: str
    state: object
    changes: list[dict] = field(default_factory=list)   # {leaf, before, after, factor}


def explain(core: Core, params: Params, prior: np.ndarray, answers: Sequence[Answer],
            final: np.ndarray) -> list[TraceStep]:
    """For each answer, in the order given: how it changed the final top candidates."""
    top = np.argsort(-final, kind="stable")[: params.trace_top]
    logp = np.log(prior)
    trace = []
    for char_id, state in answers:
        before = _normalise_log(logp)
        logp = logp + log_likelihood(core, params, char_id, state)
        after = _normalise_log(logp)
        trace.append(TraceStep(char_id, state, [
            {"leaf": core.leaves[i], "before": float(before[i]), "after": float(after[i]),
             "factor": float(after[i] / before[i])} for i in top]))
    return trace


# -- Everything at once -------------------------------------------------------

@dataclass
class Result:
    posterior: np.ndarray
    report: Report
    questions: list[QuestionInfo]
    suggested: list[str]
    trace: list[TraceStep]
    prior: np.ndarray


def evaluate(core: Core, params: Params, *, answers: Sequence[Answer] = (), skipped: Iterable[str] = (),
             kit: Iterable[str] | None = None, mode: str = "expert", find_context: str | None = None,
             pack: str | None = None, explicit_prior: dict | None = None) -> Result:
    answers = [(c, s) for c, s in answers]
    prior = make_prior(core, params, find_context=find_context, pack=pack, explicit=explicit_prior)
    post = posterior(core, params, prior, answers)
    rep = report(core, params, post, mode)
    depth = core.level(rep.node) if rep.node else -1
    infos = rank_questions(core, params, post, answered=[c for c, _ in answers],
                           skipped=skipped, kit=kit, depth=depth)
    return Result(post, rep, infos, suggestions(infos), explain(core, params, prior, answers, post), prior)
