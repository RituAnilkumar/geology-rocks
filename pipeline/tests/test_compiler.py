# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for compiling content into build/core.json."""
from __future__ import annotations

import pytest

from compiler import CompileError, compile_core, write_core

TAXON = "content/core/taxonomy/rock/igneous.yaml"
PLUTONIC = "content/core/taxonomy/rock/igneous/plutonic.yaml"


def test_leaves_and_children(repo):
    core = compile_core(repo.root)
    leaves = {t["id"] for t in core["taxa"] if t["leaf"]}
    assert leaves == {"rock.igneous.plutonic", "rock.sedimentary"}
    igneous = next(t for t in core["taxa"] if t["id"] == "rock.igneous")
    assert igneous["children"] == ["rock.igneous.plutonic"]


def test_explicit_inherit_takes_parent_values(repo):
    core = compile_core(repo.root)
    assert core["matrix"]["rock.igneous.plutonic"]["char.grain_size"] == {"coarse": 0.7, "fine": 0.3}


def test_missing_entry_inherits_from_nearest_ancestor(repo):
    # plutonic doesn't list char.minerals at all: it takes igneous's values.
    core = compile_core(repo.root)
    assert core["matrix"]["rock.igneous.plutonic"]["char.minerals"] == {"quartz": 0.6, "mica": 0.4}


def test_own_values_override_ancestor(repo):
    repo.edit(PLUTONIC, lambda d: d["characters"].update({"char.grain_size": {"coarse": 0.9, "fine": 0.1}}))
    core = compile_core(repo.root)
    assert core["matrix"]["rock.igneous.plutonic"]["char.grain_size"] == {"coarse": 0.9, "fine": 0.1}


def test_no_entry_anywhere_is_left_out(repo):
    core = compile_core(repo.root)
    assert "char.grain_size" not in core["matrix"]["rock.sedimentary"]


def test_content_errors_stop_the_build(repo):
    repo.edit(TAXON, lambda d: d["characters"].update({"char.grain_size": {"coarse": 0.7, "fine": 0.1}}))
    with pytest.raises(CompileError, match="add up to"):
        compile_core(repo.root)


def test_build_is_repeatable(repo):
    out = write_core(repo.root)
    first = out.read_bytes()
    assert write_core(repo.root).read_bytes() == first


def test_pack_contexts_included(repo):
    core = compile_core(repo.root)
    assert core["packs"]["test-pack"]["contexts"]["beach"]["human"] == 0.1
