# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the content validator. Each test breaks one rule on purpose."""
from __future__ import annotations

from conftest import REPO_ROOT, messages
from validator import validate
from validator.__main__ import main
from validator.report import markdown_report

TAXON = "content/core/taxonomy/rock/igneous.yaml"
PLUTONIC = "content/core/taxonomy/rock/igneous/plutonic.yaml"
CHAR = "content/core/characters/grain_size.yaml"
PACK = "content/packs/test-pack"


def only_error(result, *fragments):
    """Exactly one error, and it mentions every fragment."""
    errs = messages(result)
    assert len(errs) == 1, errs
    for frag in fragments:
        assert frag in errs[0], errs[0]
    return result.errors[0]


# -- baseline -----------------------------------------------------------

def test_minimal_repository_is_clean(repo):
    result = repo.check()
    assert messages(result) == []
    assert messages(result, "warning") == []
    assert result.ok


def test_real_repository_has_no_errors():
    result = validate(REPO_ROOT)
    assert messages(result) == []


# -- reading and structure ----------------------------------------------

def test_broken_yaml_is_reported_with_line(repo):
    repo.write_text(TAXON, "id: rock.igneous\nlevel: L1\nparents: [rock\nname: {en: X}\n")
    result = repo.check()
    err = next(f for f in result.errors if f.kind == "Unreadable file")
    assert err.file == TAXON
    assert err.line is not None


def test_missing_required_field(repo):
    repo.edit(TAXON, lambda d: d.pop("level"))
    only_error(repo.check(), "required field 'level' is missing")


def test_unknown_field_suggests_spelling(repo):
    repo.edit(TAXON, lambda d: d.update(parnets=["rock"]))
    only_error(repo.check(), "parnets", "spelling")


def test_probability_above_one_is_structure_error(repo):
    repo.edit(TAXON, lambda d: d["characters"]["char.minerals"].update(quartz=1.5))
    err = only_error(repo.check(), "1.5", "maximum")
    lines = repo.path(TAXON).read_text().splitlines()
    assert "quartz: 1.5" in lines[err.line - 1]


def test_misspelt_inherit(repo):
    repo.edit(PLUTONIC, lambda d: d["characters"].update({"char.grain_size": "inhert"}))
    only_error(repo.check(), "should be 'inherit'")


def test_maps_must_not_draw_boundaries(repo):
    repo.edit(f"{PACK}/manifest.yaml", lambda d: d["map_style"].update(draw_boundaries=True))
    only_error(repo.check(), "draw_boundaries", "must be False")


def test_unrecognised_yaml_file_warns(repo):
    repo.write("content/core/stray.yaml", {"a": 1})
    assert any("not in a known place" in m for m in messages(repo.check(), "warning"))


# -- IDs and references -------------------------------------------------

def test_duplicate_id(repo):
    repo.write("content/core/taxonomy/rock/igneous_copy.yaml", repo.load(TAXON))
    only_error(repo.check(), "'rock.igneous' is already used")


def test_missing_parent(repo):
    repo.edit(PLUTONIC, lambda d: d.update(parents=["rock.igneus"]))
    errs = messages(repo.check())
    assert any("Parent 'rock.igneus'" in e for e in errs)


def test_unknown_character_in_matrix(repo):
    repo.edit(TAXON, lambda d: d["characters"].update({"char.lustre": {"dull": 1.0}}))
    only_error(repo.check(), "char.lustre", "does not exist")


def test_unknown_state_in_matrix(repo):
    repo.edit(TAXON, lambda d: d["characters"].update(
        {"char.grain_size": {"coarse": 0.7, "medium": 0.3}}))
    only_error(repo.check(), "'medium' is not an answer", "Allowed: coarse, fine")


def test_missing_kit_item(repo):
    repo.edit(CHAR, lambda d: d.update(kit_required=["kit.magnifier"]))
    only_error(repo.check(), "kit.magnifier")


def test_mineral_points_to_missing_rock(repo):
    repo.edit("content/core/minerals/quartz.yaml",
              lambda d: d.update(indicates=[{"taxon": "rock.granite", "strength": "strong"}]))
    only_error(repo.check(), "rock.granite")


def test_hint_picture_must_have_media_record(repo):
    repo.edit(CHAR, lambda d: d["states"][0].update(hint_media="hints/coarse.webp"))
    only_error(repo.check(), "hints/coarse.webp", "media.yaml")


# -- taxonomy -----------------------------------------------------------

def test_level_must_be_one_below_parent(repo):
    repo.edit(PLUTONIC, lambda d: d.update(level="L3"))
    only_error(repo.check(), "exactly one level below")


def test_top_level_cannot_have_parent(repo):
    repo.edit("content/core/taxonomy/rock.yaml", lambda d: d.update(parents=["rock.igneous"]))
    errs = messages(repo.check())
    assert any("cannot have parents" in e for e in errs)


def test_circular_parents(repo):
    repo.write("content/core/taxonomy/a.yaml", {
        "id": "a", "level": "L1", "parents": ["b"], "name": {"en": "A"}, "review": {"status": "draft"}})
    repo.write("content/core/taxonomy/b.yaml", {
        "id": "b", "level": "L1", "parents": ["a"], "name": {"en": "B"}, "review": {"status": "draft"}})
    errs = messages(repo.check())
    assert sum("Circular parents" in e for e in errs) == 1


# -- probabilities ------------------------------------------------------

def test_single_choice_must_sum_to_one(repo):
    repo.edit(TAXON, lambda d: d["characters"].update(
        {"char.grain_size": {"coarse": 0.7, "fine": 0.2}}))
    only_error(repo.check(), "add up to 0.9, not 1", "How big are the grains?")


def test_small_rounding_is_allowed(repo):
    repo.edit(TAXON, lambda d: d["characters"].update(
        {"char.grain_size": {"coarse": 0.7005, "fine": 0.3}}))
    assert repo.check().ok


def test_multi_choice_need_not_sum_to_one(repo):
    repo.edit(TAXON, lambda d: d["characters"].update(
        {"char.minerals": {"quartz": 0.9, "mica": 0.8}}))
    assert repo.check().ok


def test_inherit_needs_something_to_inherit(repo):
    repo.edit(PLUTONIC, lambda d: d["characters"].update({"char.minerals": "inherit"}))
    assert repo.check().ok          # rock.igneous has values: fine
    repo.edit(TAXON, lambda d: d["characters"].pop("char.minerals"))
    only_error(repo.check(), "says 'inherit'", "no parent")


def test_exact_zero_or_one_is_a_warning_not_error(repo):
    repo.edit(TAXON, lambda d: d["characters"].update(
        {"char.grain_size": {"coarse": 1, "fine": 0}}))
    result = repo.check()
    assert result.ok
    assert sum("exactly" in w for w in messages(result, "warning")) == 2


def test_crosswalk_must_sum_to_one(repo):
    repo.edit(f"{PACK}/crosswalk.yaml", lambda d: d[0]["taxa"].update({"rock.sedimentary": 0.3}))
    only_error(repo.check(), "map unit 'X1'", "add up to 1.2")


def test_find_context_weights_must_sum_to_one(repo):
    repo.edit(f"{PACK}/context.yaml", lambda d: d["contexts"]["beach"].update(human=0.2))
    only_error(repo.check(), "beach", "not 1")


# -- media and licences -------------------------------------------------

def _add_media(repo, licence="CC-BY-SA-4.0", create_file=True):
    if create_file:
        repo.write_text("content/core/media/hints/coarse.webp", "fake image")
    repo.write("content/core/media/media.yaml", [{
        "file": "hints/coarse.webp", "licence": licence, "author": "R. Example",
        "source": "original", "alt_text": {"en": "Coarse granite"}, "review": {"status": "draft"}}])


def test_media_with_allowed_licence_is_fine(repo):
    _add_media(repo)
    repo.edit(CHAR, lambda d: d["states"][0].update(hint_media="hints/coarse.webp"))
    assert repo.check().ok


def test_non_commercial_licence_is_rejected(repo):
    _add_media(repo, licence="CC-BY-NC-4.0")
    only_error(repo.check(), "CC-BY-NC-4.0", "not on the allowed list")


def test_media_record_without_file(repo):
    _add_media(repo, create_file=False)
    only_error(repo.check(), "file does not exist")


def test_media_file_without_record(repo):
    repo.write_text("content/core/media/hints/mystery.jpg", "fake image")
    only_error(repo.check(), "no record in media.yaml")


# -- text, pages, review ------------------------------------------------

def test_todo_tells_you_is_warning(repo):
    repo.edit(CHAR, lambda d: d["states"][1].update(tells_you={"en": "TODO"}))
    result = repo.check()
    assert result.ok
    assert any("what this tells you" in w for w in messages(result, "warning"))


def test_missing_page_is_warning_and_todo(repo):
    repo.edit(TAXON, lambda d: d.update(page="igneous"))
    result = repo.check()
    assert result.ok
    assert any("igneous.md" in w for w in messages(result, "warning"))
    assert any(t.group == "Rock pages not yet written" for t in result.todos)


def test_page_front_matter_checked(repo):
    repo.write_text("content/core/pages/igneous.md",
                    "---\nid: igneous\ntaxon: rock.igneus\nreview: {status: draft}\n---\n\nText\n")
    only_error(repo.check(), "rock.igneus")


def test_approved_needs_reviewer_and_date(repo):
    repo.edit(TAXON, lambda d: d.update(review={"status": "approved", "reviewer": None, "date": None}))
    only_error(repo.check(), "reviewer")
    repo.edit(TAXON, lambda d: d.update(
        review={"status": "approved", "reviewer": "Ritu", "date": "2026-12-01"}))
    result = repo.check()
    assert result.ok
    assert result.review_counts["Rock types and groups (taxonomy)"]["approved"] == 1


def test_todos_grouped_by_type(repo):
    repo.edit(TAXON, lambda d: d.update(refs={"bgs_rcs": "TODO"}))
    repo.edit(f"{PACK}/named_units/x.yaml", lambda d: d.update(summary={"en": "TODO"}))
    groups = {t.group for t in repo.check().todos}
    assert {"BGS Rock Classification Scheme codes", "Summaries", "Hint pictures"} <= groups


# -- packs and scenarios ------------------------------------------------

def test_layer_source_must_be_listed(repo):
    repo.edit(f"{PACK}/manifest.yaml",
              lambda d: d["layers"]["offline"].append({"id": "x", "source": "secret", "required": False}))
    only_error(repo.check(), "secret", "not listed under sources")


def test_named_unit_must_exist(repo):
    repo.edit(f"{PACK}/crosswalk.yaml", lambda d: d[0].update(named_unit="nu.y"))
    only_error(repo.check(), "nu.y")


def test_scenario_unknown_answer(repo):
    repo.edit("scenarios/basic.yaml", lambda d: d["steps"][0]["answer"].update(state="huge"))
    only_error(repo.check(), "'huge' is not an answer")


def test_scenario_list_for_single_choice(repo):
    repo.edit("scenarios/basic.yaml",
              lambda d: d["steps"][0]["answer"].update(state=["coarse", "fine"]))
    only_error(repo.check(), "only one answer")


def test_scenario_unknown_find_context(repo):
    repo.edit("scenarios/basic.yaml", lambda d: d["setup"].update(find_context="moon"))
    only_error(repo.check(), "moon")


def test_scenario_templates_are_ignored(repo):
    repo.write("scenarios/_template.yaml", {"id": "TODO"})
    assert repo.check().ok


# -- report and command line --------------------------------------------

def test_report_lists_errors_and_review_table(repo):
    repo.edit(TAXON, lambda d: d["characters"].update(
        {"char.grain_size": {"coarse": 0.7, "fine": 0.2}}))
    text = markdown_report(repo.check())
    assert "❌ 1 error" in text
    assert "igneous.yaml" in text
    assert "## Review status" in text and "## TODOs by type" in text


def test_command_line_exit_codes(repo, capsys):
    assert main(["--root", str(repo.root)]) == 0
    assert (repo.root / "reports/content-report.md").is_file()
    repo.edit(TAXON, lambda d: d.pop("name"))
    assert main(["--root", str(repo.root), "--report", "-"]) == 1
    assert "FAILED" in capsys.readouterr().out


def test_error_points_at_the_right_line(repo):
    repo.edit(TAXON, lambda d: d["characters"].update(
        {"char.grain_size": {"coarse": 0.7, "medium": 0.3}}))
    err = repo.check().errors[0]
    lines = repo.path(TAXON).read_text().splitlines()
    assert "medium" in lines[err.line - 1]
