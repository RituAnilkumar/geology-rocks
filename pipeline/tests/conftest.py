# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test helpers: a tiny, valid content repository built in a temporary folder.

Each test breaks one thing and checks the validator reports it.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import yaml

PIPELINE = Path(__file__).resolve().parents[1]
REPO_ROOT = PIPELINE.parent
sys.path.insert(0, str(PIPELINE))

from validator import validate  # noqa: E402

DRAFT = {"status": "draft", "reviewer": None, "date": None}


def en(text):
    return {"en": text}


def taxon(id_, level, parents, **extra):
    d = {"id": id_, "level": level, "parents": parents, "name": en(id_.split(".")[-1].title()),
         "review": dict(DRAFT)}
    d.update(extra)
    return d


BASE_FILES = {
    "content/core/taxonomy/rock.yaml": taxon("rock", "L0", []),
    "content/core/taxonomy/rock/igneous.yaml": taxon(
        "rock.igneous", "L1", ["rock"],
        characters={"char.grain_size": {"coarse": 0.7, "fine": 0.3},
                    "char.minerals": {"quartz": 0.6, "mica": 0.4}}),
    "content/core/taxonomy/rock/igneous/plutonic.yaml": taxon(
        "rock.igneous.plutonic", "L2", ["rock.igneous"],
        characters={"char.grain_size": "inherit"}),
    "content/core/taxonomy/rock/sedimentary.yaml": taxon("rock.sedimentary", "L1", ["rock"]),
    "content/core/characters/grain_size.yaml": {
        "id": "char.grain_size", "order": 1, "kind": "single",
        "question": en("How big are the grains?"), "kit_required": ["kit.hand_lens"],
        "states": [
            {"id": "coarse", "label": en("Coarse"), "hint_media": "TODO", "tells_you": en("Slow cooling.")},
            {"id": "fine", "label": en("Fine"), "hint_media": None, "tells_you": en("Fast cooling.")},
        ],
        "review": dict(DRAFT)},
    "content/core/characters/minerals.yaml": {
        "id": "char.minerals", "order": 2, "kind": "multi",
        "question": en("Which minerals can you see?"),
        "states": [
            {"id": "quartz", "label": en("Quartz"), "tells_you": en("Felsic.")},
            {"id": "mica", "label": en("Mica"), "tells_you": en("Shiny flakes.")},
        ],
        "review": dict(DRAFT)},
    "content/core/minerals/quartz.yaml": {
        "id": "mineral.quartz", "name": en("Quartz"), "properties": {"hardness_mohs": [7, 7]},
        "indicates": [{"taxon": "rock.igneous", "strength": "strong"}],
        "review": dict(DRAFT)},
    "content/core/kit/kit.yaml": [{"id": "kit.hand_lens", "name": en("Hand lens")}],
    "content/core/media/media.yaml": [],
    "content/packs/test-pack/manifest.yaml": {
        "id": "test-pack", "name": en("Test"), "extent": {"bbox": [0, 0, 1, 1]},
        "version": "0.1.0", "requires_core": ">=0.1.0",
        "sources": [{"id": "osm", "name": "OSM", "licence": "ODbL-1.0", "attribution": "© OSM"}],
        "layers": {"offline": [{"id": "basemap", "source": "osm", "required": True}]},
        "map_style": {"draw_boundaries": False},
        "review": dict(DRAFT)},
    "content/packs/test-pack/crosswalk.yaml": [
        {"map_unit": "X1", "label": "Unit X", "named_unit": "nu.x",
         "taxa": {"rock.igneous.plutonic": 0.9, "rock.sedimentary": 0.1}, "review": dict(DRAFT)}],
    "content/packs/test-pack/context.yaml": {
        "contexts": {"beach": {"label": en("Beach"), "local": 0.5, "transported": 0.4, "human": 0.1}},
        "review": dict(DRAFT)},
    "content/packs/test-pack/named_units/x.yaml": {
        "id": "nu.x", "name": en("X Granite"), "parent_taxon": "rock.igneous.plutonic",
        "review": dict(DRAFT)},
    "scenarios/basic.yaml": {
        "id": "basic", "title": "Basic", "author": "test",
        "setup": {"pack": "test-pack", "find_context": "beach", "kit": ["kit.hand_lens"]},
        "steps": [{"answer": {"char": "char.grain_size", "state": "coarse"},
                   "expect": {"p_at_least": {"rock.igneous": 0.5}}}],
        "review": dict(DRAFT)},
}


class Repo:
    def __init__(self, root: Path):
        self.root = root

    def path(self, rel: str) -> Path:
        return self.root / rel

    def write(self, rel: str, data) -> None:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    def write_text(self, rel: str, text: str) -> None:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def load(self, rel: str):
        return yaml.safe_load(self.path(rel).read_text(encoding="utf-8"))

    def edit(self, rel: str, change) -> None:
        """Load a file, let change() modify it in place, and save it."""
        data = self.load(rel)
        change(data)
        self.write(rel, data)

    def check(self):
        return validate(self.root)


@pytest.fixture
def repo(tmp_path) -> Repo:
    shutil.copytree(REPO_ROOT / "schemas", tmp_path / "schemas")
    r = Repo(tmp_path)
    for rel, data in BASE_FILES.items():
        r.write(rel, data)
    return r


def messages(result, severity="error"):
    items = result.errors if severity == "error" else result.warnings
    return [f.message for f in items]
