# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Property tests: the eight invariants in engine/CLAUDE.md.

Hypothesis generates many random sets of answers (any questions, any states,
any order) and checks each invariant holds for all of them.
"""
from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from conftest import real_core
from geology_engine.config import load_params
from geology_engine.engine import (
    evaluate, expected_gain, log_likelihood, make_prior, node_probability, posterior)

CORE = real_core()
PARAMS = load_params()
CHARS = CORE.char_order
KIT_IDS = [k["id"] for k in CORE.kit]
CONTEXTS = sorted({c for p in CORE.packs.values() for c in p["contexts"]})
SETTINGS = settings(max_examples=150, deadline=None)


@st.composite
def answer_sets(draw, min_size=0):
    """A random set of answers to distinct questions, in random order."""
    chosen = draw(st.lists(st.sampled_from(CHARS), unique=True, min_size=min_size))
    answers = []
    for cid in chosen:
        c = CORE.characters[cid]
        if c.kind == "single":
            answers.append((cid, draw(st.sampled_from(c.states))))
        else:
            answers.append((cid, draw(st.lists(st.sampled_from(c.states), unique=True))))
    return answers


kits = st.lists(st.sampled_from(KIT_IDS), unique=True)
contexts = st.one_of(st.none(), st.sampled_from(CONTEXTS))


# 1. Posterior sums to 1 -------------------------------------------------------

@SETTINGS
@given(answer_sets(), contexts)
def test_1_posterior_sums_to_one(answers, ctx):
    post = evaluate(CORE, PARAMS, answers=answers, find_context=ctx).posterior
    assert abs(post.sum() - 1) < 1e-9
    assert (post >= 0).all()


# 2. Robustness: no answer drives a rock type to zero --------------------------

def test_2_every_single_answer_keeps_every_rock_possible():
    prior = make_prior(CORE, PARAMS)
    for cid in CHARS:
        c = CORE.characters[cid]
        for s in c.states:
            state = s if c.kind == "single" else [s]
            post = posterior(CORE, PARAMS, prior, [(cid, state)])
            assert (post > 0).all(), (cid, s)
            # The least likely answer still has likelihood at least ε/k.
            k = len(c.states) if c.kind == "single" else 2
            assert np.exp(log_likelihood(CORE, PARAMS, cid, state)).min() >= PARAMS.error_rate / k - 1e-15


@SETTINGS
@given(st.sampled_from(CORE.leaves), answer_sets(min_size=1))
def test_2_true_rock_never_eliminated(leaf, answers):
    post = evaluate(CORE, PARAMS, answers=answers).posterior
    assert post[CORE.leaf_index[leaf]] > 0


# 3. Skipping is neutral ------------------------------------------------------

@SETTINGS
@given(answer_sets(), st.lists(st.sampled_from(CHARS), unique=True))
def test_3_skip_and_not_sure_leave_posterior_unchanged(answers, skipped):
    answered = {c for c, _ in answers}
    skipped = [c for c in skipped if c not in answered]
    a = evaluate(CORE, PARAMS, answers=answers).posterior
    b = evaluate(CORE, PARAMS, answers=answers, skipped=skipped).posterior
    assert np.array_equal(a, b)


# 4. Order independence -------------------------------------------------------

@SETTINGS
@given(answer_sets(min_size=2), st.randoms())
def test_4_order_does_not_matter(answers, rnd):
    shuffled = list(answers)
    rnd.shuffle(shuffled)
    a = evaluate(CORE, PARAMS, answers=answers)
    b = evaluate(CORE, PARAMS, answers=shuffled)
    np.testing.assert_allclose(a.posterior, b.posterior, rtol=0, atol=1e-12)
    assert a.report.node == b.report.node


# 5. No over-claiming ---------------------------------------------------------

@SETTINGS
@given(answer_sets(), st.sampled_from(["expert", "beginner"]))
def test_5_reports_only_as_deep_as_evidence_supports(answers, mode):
    r = evaluate(CORE, PARAMS, answers=answers, mode=mode)
    rep, tau = r.report, PARAMS.report_threshold
    if rep.node is None:
        assert all(node_probability(CORE, r.posterior, t) < tau for t in CORE.roots)
        return
    assert rep.p >= tau
    assert abs(rep.p - node_probability(CORE, r.posterior, rep.node)) < 1e-12
    # Every step on the path was confident too.
    assert all(p >= tau for _, p in rep.path)
    children = CORE.taxa[rep.node]["children"]
    if mode == "expert":
        assert all(node_probability(CORE, r.posterior, c) < tau for c in children)
    else:
        assert CORE.level(rep.node) <= 3
        if CORE.level(rep.node) < 3:
            assert all(node_probability(CORE, r.posterior, c) < tau for c in children)


# 6. Kit filter ---------------------------------------------------------------

@SETTINGS
@given(answer_sets(), kits)
def test_6_questions_needing_missing_kit_are_never_suggested(answers, kit):
    r = evaluate(CORE, PARAMS, answers=answers, kit=kit)
    for cid in r.suggested:
        assert set(CORE.characters[cid].kit_required) <= set(kit)


def test_6_kit_questions_can_still_be_answered_without_the_kit():
    r = evaluate(CORE, PARAMS, answers=[("char.acid_reaction", "fizzes")], kit=[])
    assert abs(r.posterior.sum() - 1) < 1e-9


# 7. Question choice ----------------------------------------------------------

@SETTINGS
@given(answer_sets(), kits, st.lists(st.sampled_from(CHARS), unique=True, max_size=3))
def test_7_first_suggestion_has_highest_gain(answers, kit, skipped):
    answered = {c for c, _ in answers}
    r = evaluate(CORE, PARAMS, answers=answers, kit=kit, skipped=skipped)
    eligible = [q for q in r.questions
                if q.eligible and q.kit_ok and q.char not in skipped and q.gain >= PARAMS.min_gain_bits]
    if not eligible:
        assert r.suggested == []
        return
    best = max(q.gain for q in eligible)
    tied = [q.char for q in eligible if round(q.gain, 12) == round(best, 12)]
    first_by_order = min(tied, key=lambda c: CORE.char_order.index(c))
    assert r.suggested[0] == first_by_order
    assert len(r.suggested) == min(PARAMS.max_suggestions, len(eligible))
    assert not set(r.suggested) & answered


@SETTINGS
@given(answer_sets())
def test_7_gain_is_never_negative_for_single_choice(answers):
    post = evaluate(CORE, PARAMS, answers=answers).posterior
    for cid in CHARS:
        if CORE.characters[cid].kind == "single":
            assert expected_gain(CORE, PARAMS, post, cid) >= -1e-9


# 8. Prior floor --------------------------------------------------------------

@SETTINGS
@given(contexts, st.one_of(st.none(), st.dictionaries(
    st.sampled_from(sorted(CORE.taxa)), st.floats(0.0, 1.0), min_size=1, max_size=4)))
def test_8_prior_never_zero(ctx, explicit):
    if explicit is not None and sum(explicit.values()) == 0:
        explicit = None
    prior = make_prior(CORE, PARAMS, find_context=ctx, explicit=explicit)
    assert abs(prior.sum() - 1) < 1e-9
    assert prior.min() > 0
    # Floor ρ applied before normalising: the smallest share can't fall far below it.
    assert prior.min() >= PARAMS.prior_floor / (1 + CORE.n * PARAMS.prior_floor)
