# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Worked examples of SCORING.md, plus scenario and simulation checks."""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pytest
import yaml

from conftest import ROOT
from geology_engine.engine import (
    AnswerError, evaluate, expected_gain, log_likelihood, make_prior, posterior)
from geology_engine.scenarios import run_scenario
from geology_engine.simulate import run_and_write

SCENARIOS = sorted(p for p in (ROOT / "scenarios").glob("*.yaml") if not p.name.startswith("_"))


def test_uniform_prior(core, params):
    prior = make_prior(core, params)
    assert np.allclose(prior, 1 / core.n)


def test_find_context_sets_human_made_share(core, params):
    """Agreed with the product owner for M2: the find context only changes the
    chance of human-made material (context.yaml 'human' weight)."""
    for ctx_id, ctx in core.packs["gb-southwest"]["contexts"].items():
        prior = make_prior(core, params, find_context=ctx_id)
        human_roots = [r for r in core.roots
                       if any(core.is_ancestor_or_self(r, t) for t in core.packs["gb-southwest"]["human_made"])]
        human = sum(prior[core.mask[r]].sum() for r in human_roots)
        assert human == pytest.approx(ctx["human"], abs=0.01), ctx_id


def test_likelihood_formula(core, params):
    """L(s|t) = (1−ε)·P(s|t) + ε/k."""
    c = core.characters["char.grain_size"]
    i = core.leaf_index[core.leaves[0]]
    expected = (1 - params.error_rate) * c.P[i, 0] + params.error_rate / len(c.states)
    assert np.exp(log_likelihood(core, params, c.id, c.states[0]))[i] == pytest.approx(expected)


def test_unticked_options_carry_no_information(core, params):
    """Product owner's choice (M2): only ticked minerals count."""
    prior = make_prior(core, params)
    none_ticked = posterior(core, params, prior, [("char.minerals_visible", [])])
    assert np.allclose(none_ticked, prior)


def test_bad_answers_are_rejected(core, params):
    with pytest.raises(AnswerError):
        evaluate(core, params, answers=[("char.grain_size", "enormous")])
    with pytest.raises(AnswerError):
        evaluate(core, params, answers=[("char.nonexistent", "x")])
    with pytest.raises(AnswerError):
        evaluate(core, params, answers=[("char.grain_size", "fine"), ("char.grain_size", "coarse")])


def test_multi_select_gain_matches_brute_force(core, params):
    """The fast multi-select gain equals a slow, obvious calculation."""
    post = evaluate(core, params, answers=[("char.texture", "interlocking")]).posterior
    c = core.characters["char.minerals_visible"]
    eps = params.error_rate
    q = (1 - eps) * c.P + eps / 2
    H = lambda p: -sum(x * np.log2(x) for x in p if x > 0)
    total = 0.0
    for pattern in itertools.product([0, 1], repeat=len(c.states)):
        b = np.array(pattern)
        like = np.prod(np.where(b == 1, q, 1 - q), axis=1)
        p_pattern = float((post * like).sum())
        upd = post * np.prod(np.where(b == 1, q, 1.0), axis=1)
        total += p_pattern * H(upd / upd.sum())
    assert expected_gain(core, params, post, c.id) == pytest.approx(H(post) - total, abs=1e-9)


def test_trace_explains_each_answer(core, params):
    answers = [("char.texture", "interlocking"), ("char.grain_size", "coarse")]
    r = evaluate(core, params, answers=answers)
    assert [s.char for s in r.trace] == ["char.texture", "char.grain_size"]
    assert len(r.trace[0].changes) == params.trace_top
    last = r.trace[-1].changes[0]
    assert last["after"] == pytest.approx(r.posterior[core.leaf_index[last["leaf"]]])


def test_beginner_mode_stops_at_l3(core, params):
    answers = [("char.natural", "looks_natural"), ("char.texture", "interlocking"),
               ("char.foliation", "none"), ("char.grain_size", "coarse"),
               ("char.dark_minerals", "lt20"), ("char.colour", "pink"),
               ("char.minerals_visible", ["quartz", "k_feldspar"])]
    expert = evaluate(core, params, answers=answers, mode="expert").report
    beginner = evaluate(core, params, answers=answers, mode="beginner").report
    assert core.taxa[expert.node]["level"] == "L4"
    assert core.taxa[beginner.node]["level"] == "L3"
    assert beginner.top_leaf == expert.top_leaf


@pytest.mark.parametrize("path", SCENARIOS, ids=lambda p: p.stem)
def test_scenario_passes(core, params, path):
    res = run_scenario(core, params, yaml.safe_load(path.read_text(encoding="utf-8")), path.name)
    failures = [f"step {c.step}: expected {c.expected}, but {c.actual}" for c in res.checks if not c.ok]
    assert res.error is None, res.error
    assert not failures, "\n".join(failures)


def test_simulation_writes_reports(core, params, tmp_path: Path):
    msg = run_and_write(core, params, tmp_path, n_all=3, n_key=2)
    assert "Simulation done" in msg
    text = (tmp_path / "simulation-report.md").read_text()
    assert "most-confused pairs" in text
    rows = (tmp_path / "simulation-confusion-key.csv").read_text().splitlines()
    assert len(rows) == core.n + 1


# -- Web prototype API (called directly, no network) -----------------------

def test_web_payloads(core, params):
    from geology_engine.web.server import core_payload, evaluate_payload
    cp = core_payload(core, params)
    assert {c["id"] for c in cp["characters"]} == set(core.characters)
    assert cp["contexts"], "find contexts come from the pack"
    out = evaluate_payload(core, params, {
        "answers": [{"char": "char.texture", "state": "interlocking"},
                    {"char": "char.minerals_visible", "state": ["quartz", "k_feldspar"]}],
        "skipped": ["char.colour"], "kit": ["kit.hand_lens"], "mode": "beginner",
        "find_context": "beach"})
    assert "most likely granite" in out["phrase"]
    assert abs(sum(c["p"] for c in out["candidates"]) - 1) < 1e-9
    assert "char.colour" not in out["suggested"]
    assert [t["char"] for t in out["trace"]] == ["char.texture", "char.minerals_visible"]
    assert out["trace"][0]["answers"][0]["tells_you"]


def test_web_rejects_bad_answer(core, params):
    from geology_engine.web.server import evaluate_payload
    with pytest.raises(AnswerError):
        evaluate_payload(core, params, {"answers": [{"char": "char.texture", "state": "wobbly"}]})
