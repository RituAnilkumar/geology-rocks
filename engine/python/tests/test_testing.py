# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Specimen testing (M3): saving runs, filling in true rocks, the summary report."""
from __future__ import annotations

import csv
import json
import shutil
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer

import pytest

from geology_engine.engine import AnswerError, evaluate
from geology_engine.testlog import (NOT_IN_KEY, TestLog, TestLogError, columns, make_row,
                                    parse_answers, resolve_rock)
from geology_engine.testreport import analyse, build_report, outcome, run_and_write

GRANITE_ANSWERS = [
    {"char": "char.natural", "state": "looks_natural"},
    {"char": "char.texture", "state": "interlocking"},
    {"char": "char.grain_size", "state": "coarse"},
    {"char": "char.minerals_visible", "state": ["quartz", "k_feldspar"]},
]


def body(**over):
    b = {"tester": "RA", "experience": "geologist", "specimen": "12", "confidence": "fairly_sure",
         "notes": "", "order": ["char.natural", "char.colour", "char.texture", "char.grain_size",
                                "char.minerals_visible", "char.lustre"],
         "answers": GRANITE_ANSWERS, "skipped": {"char.colour": "not_sure", "char.lustre": "skip"},
         "kit": ["kit.hand_lens"], "mode": "expert", "find_context": "beach"}
    b.update(over)
    return b


def granite(core):
    return next(l for l in core.leaves if core.name(l) == "Granite")


# -- Saving ------------------------------------------------------------------

def test_row_records_answers_result_and_order(core, params):
    row = make_row(core, params, body(), now=datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc),
                   run_id="abc")
    r = evaluate(core, params, answers=[(a["char"], a["state"]) for a in GRANITE_ANSWERS],
                 skipped=["char.colour", "char.lustre"], kit=["kit.hand_lens"], find_context="beach")
    assert row["run_id"] == "abc" and row["saved_at"].startswith("2026-11-25")
    assert row["top_rock"] == r.report.top_leaf == granite(core)
    assert row["key_result"] == (r.report.node or "")
    assert row["minerals_visible"] == "quartz;k_feldspar"
    assert row["colour"] == "NOT SURE" and row["lustre"] == "SKIPPED"
    assert row["hardness"] == ""                      # never reached
    assert row["answer_order"] == "natural > colour > texture > grain_size > minerals_visible > lustre"
    assert (row["questions_answered"], row["not_sure"], row["skipped"]) == ("4", "1", "1")
    assert set(columns(core)) == set(row)


def test_nothing_ticked_is_recorded(core, params):
    row = make_row(core, params, body(answers=[{"char": "char.minerals_visible", "state": []}], skipped={}))
    assert row["minerals_visible"] == "(none ticked)"
    assert parse_answers(core, row) == ([("char.minerals_visible", [])], [])


@pytest.mark.parametrize("bad", [{"tester": " "}, {"specimen": ""}, {"experience": ""},
                                 {"experience": "wizard"}, {"answers": [], "skipped": {}}])
def test_missing_details_are_refused_with_a_clear_message(core, params, bad):
    with pytest.raises(TestLogError):
        make_row(core, params, body(**bad))


def test_bad_answers_are_refused(core, params):
    with pytest.raises(AnswerError):
        make_row(core, params, body(answers=[{"char": "char.texture", "state": "wobbly"}]))
    with pytest.raises(AnswerError):
        make_row(core, params, body(skipped={"char.colour": "maybe"}))


def test_free_text_cannot_become_a_spreadsheet_formula(core, params):
    row = make_row(core, params, body(tester="=HYPERLINK(1)", notes="line one\nline two"))
    assert row["tester"].startswith("'=")
    assert row["notes"] == "line one line two"


def test_save_load_replay_round_trip(core, params, tmp_path):
    log = TestLog(tmp_path)
    row = make_row(core, params, body())
    assert log.append(row, columns(core)) == 1
    assert log.append(make_row(core, params, body(specimen="13")), columns(core)) == 2
    loaded = log.load()
    assert [r["specimen"] for r in loaded] == ["12", "13"]
    answers, skipped = parse_answers(core, loaded[0])
    assert answers == [(a["char"], a["state"]) for a in GRANITE_ANSWERS]
    assert sorted(skipped) == ["char.colour", "char.lustre"]
    # Excel-friendly: UTF-8 with a byte-order mark.
    assert log.default_file.read_bytes().startswith(b"\xef\xbb\xbf")


def test_true_rock_is_filled_in_and_duplicates_count_once(core, params, tmp_path):
    log = TestLog(tmp_path)
    row = make_row(core, params, body(), run_id="r1")
    log.append(row, columns(core))
    (tmp_path / "from-alex").mkdir()
    shutil.copy(log.default_file, tmp_path / "from-alex" / "copy.csv")    # same test sent twice
    assert len(log.load()) == 1
    log.set_truth("r1", granite(core))
    assert all(r["true_rock"] == granite(core)
               for p in log.files() for r in csv.DictReader(p.open(encoding="utf-8-sig")))
    with pytest.raises(TestLogError):
        log.set_truth("nope", granite(core))


def test_new_questions_extend_the_file_header(core, params, tmp_path):
    log = TestLog(tmp_path)
    log.append(make_row(core, params, body(), run_id="a"), columns(core))
    log.append(make_row(core, params, body(), run_id="b"), columns(core) + ["new_question"])
    header = next(csv.reader(log.default_file.open(encoding="utf-8-sig")))
    assert header[-1] == "new_question" and len(log.load()) == 2


def test_true_rock_can_be_typed_by_name(core):
    g = granite(core)
    assert resolve_rock(core, "granite") == g
    assert resolve_rock(core, " Granite ") == g
    assert resolve_rock(core, g) == g
    assert resolve_rock(core, "Not in key") == NOT_IN_KEY
    assert resolve_rock(core, "") == ""
    assert resolve_rock(core, "granit") is None


# -- Report --------------------------------------------------------------------

def test_outcome_categories(core):
    g = granite(core)
    parent = core.taxa[g]["parents"][0]
    other = next(l for l in core.leaves if not core.is_ancestor_or_self(parent, l))
    assert outcome(core, g, g) == "named"
    assert outcome(core, parent, g) == "group"
    assert outcome(core, "", g) == "undecided"
    assert outcome(core, other, g) == "wrong"


def saved(core, params, tmp_path, truths):
    log = TestLog(tmp_path)
    for i, truth in enumerate(truths):
        log.append(make_row(core, params, body(specimen=str(i)), run_id=f"r{i}"), columns(core))
        if truth is not None:
            log.set_truth(f"r{i}", truth)
    return log


def test_report_scores_filled_in_tests_and_flags_problems(core, params, tmp_path):
    g = granite(core)
    slate = next(l for l in core.leaves if core.name(l) == "Slate")
    log = saved(core, params, tmp_path, [g, slate, None, "granitte", NOT_IN_KEY])
    tests = analyse(core, params, log.load())
    text = build_report(core, params, tests, ["test-runs.csv"])
    assert "With the true rock type filled in: **2**" in text
    assert "True rock type not filled in yet: 1" in text
    assert "not recognised: 1" in text and "granitte" in text
    assert "Rock not in the key: 1" in text
    # Granite answers given for a slate: slate not named, listed as a confusion,
    # and the answers disagree with the slate content.
    t_slate = next(t for t in tests if t.true == slate)
    assert t_slate.then != "named" and not t_slate.then_top_ok and t_slate.now == t_slate.then
    assert "| Slate | Granite | 1 |" in text and "Key's chance (median)" in text
    assert "Answers that disagree with the content" in text and "specimen 1 (RA)" in text
    assert "Tester confidence compared with the result" in text
    assert "Questions people skipped or were not sure about" in text


def test_report_with_nothing_scored_explains_what_to_do(core, params, tmp_path):
    log = saved(core, params, tmp_path, [None])
    text = build_report(core, params, analyse(core, params, log.load()), ["test-runs.csv"])
    assert "Nothing to score yet" in text


def test_report_files_are_written(core, params, tmp_path):
    saved(core, params, tmp_path / "testing", [granite(core)])
    msg = run_and_write(core, params, tmp_path / "testing", tmp_path / "reports")
    assert "1 test(s), 1 with the true rock type" in msg
    for name in ("specimen-test-report.md", "specimen-test-runs.csv", "specimen-test-by-rock.csv"):
        assert (tmp_path / "reports" / name).exists()
    rows = list(csv.DictReader((tmp_path / "reports/specimen-test-by-rock.csv").open(encoding="utf-8-sig")))
    assert rows[0]["rock"] == "Granite" and rows[0]["tests"] == "1"


# -- Web pages, through a real local server --------------------------------------

@pytest.fixture
def server(core, params, tmp_path):
    from geology_engine.web.server import make_handler
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(core, params, TestLog(tmp_path)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def call(url, data=None):
    req = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_web_save_and_fill_in_flow(core, server):
    for page in ("/", "/results.html", "/results.js", "/sheet.html"):
        assert call(server + page)[0] == 200, page
    status, out = call(server + "/api/save-test", body())
    assert status == 200 and json.loads(out)["count"] == 1
    status, out = call(server + "/api/save-test", body(tester=""))
    assert status == 400 and "tester" in json.loads(out)["error"]
    tests = json.loads(call(server + "/api/tests")[1])
    assert len(tests["rocks"]) == core.n
    [t] = tests["tests"]
    assert t["top_rock"] == "Granite" and t["confidence"] == "Fairly sure" and t["true_rock"] == ""
    assert call(server + "/api/set-truth", {"run_id": t["run_id"], "true_rock": "rock.made_up"})[0] == 400
    assert call(server + "/api/set-truth", {"run_id": t["run_id"], "true_rock": granite(core)})[0] == 200
    assert json.loads(call(server + "/api/tests")[1])["tests"][0]["true_rock"] == granite(core)
