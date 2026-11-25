# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compiled content (build/core.json) arranged as arrays for scoring."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

LEVELS = ["L0", "L1", "L2", "L3", "L4"]


def level_index(level: str) -> int:
    return LEVELS.index(level)


@dataclass
class Character:
    id: str
    order: int
    kind: str                 # "single" or "multi"
    states: list[str]
    applies_from: int         # level index
    kit_required: list[str]
    data: dict                # full compiled record (texts etc.)
    # single: P[leaf, state]; multi: P[leaf, option] = P(option present).
    # Rows for rock types with no information are uniform (single) or 0.5 (multi).
    P: np.ndarray


class Core:
    def __init__(self, compiled: dict):
        self.raw = compiled
        self.taxa: dict[str, dict] = {t["id"]: t for t in compiled["taxa"]}
        self.leaves: list[str] = [t["id"] for t in compiled["taxa"] if t["leaf"]]
        self.leaf_index = {t: i for i, t in enumerate(self.leaves)}
        self.n = len(self.leaves)
        self.roots: list[str] = sorted(
            (t for t in self.taxa.values() if not t["parents"]),
            key=lambda t: (t["order"], t["id"]))
        self.roots = [t["id"] for t in self.roots]

        # Descendant leaves of every node, as a boolean mask over leaves.
        self.mask: dict[str, np.ndarray] = {}
        for tid in self.taxa:
            self.mask[tid] = self._mask(tid)

        self.characters: dict[str, Character] = {}
        for c in compiled["characters"]:
            states = [s["id"] for s in c["states"]]
            k = len(states)
            fill = 1.0 / k if c["kind"] == "single" else 0.5
            P = np.full((self.n, k), fill)
            for leaf, i in self.leaf_index.items():
                row = compiled["matrix"].get(leaf, {}).get(c["id"])
                if row is None:
                    continue
                if c["kind"] == "single":
                    P[i] = [row.get(s, 0.0) for s in states]
                else:
                    P[i] = [row.get(s, 0.5) for s in states]
            self.characters[c["id"]] = Character(
                id=c["id"], order=c["order"], kind=c["kind"], states=states,
                applies_from=level_index(c["applies_from"]),
                kit_required=list(c["kit_required"]), data=c, P=P)
        self.char_order = sorted(self.characters, key=lambda c: (self.characters[c].order, c))
        self.kit = compiled["kit"]
        self.packs = compiled["packs"]

    def _mask(self, tid: str) -> np.ndarray:
        m = np.zeros(self.n, dtype=bool)
        stack, seen = [tid], set()
        while stack:
            t = stack.pop()
            if t in seen:
                continue
            seen.add(t)
            if t in self.leaf_index:
                m[self.leaf_index[t]] = True
            stack.extend(self.taxa[t]["children"])
        return m

    def name(self, tid: str) -> str:
        return self.taxa[tid]["name"]["en"]

    def level(self, tid: str) -> int:
        return level_index(self.taxa[tid]["level"])

    def is_ancestor_or_self(self, node: str, leaf_or_node: str) -> bool:
        """True if node is leaf_or_node or one of its ancestors."""
        stack, seen = [leaf_or_node], set()
        while stack:
            t = stack.pop()
            if t == node:
                return True
            if t in seen:
                continue
            seen.add(t)
            stack.extend(self.taxa[t]["parents"])
        return False

    @classmethod
    def load(cls, path: Path) -> "Core":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))
