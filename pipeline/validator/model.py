# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Small data classes shared by the validator."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    severity: str           # ERROR or WARNING
    kind: str               # short group name, e.g. "Probabilities"
    file: str               # path relative to the repository root
    line: int | None
    message: str            # plain-language explanation


@dataclass(frozen=True)
class Todo:
    group: str              # e.g. "BGS rock codes"
    file: str
    line: int | None
    where: str              # field, e.g. "refs.bgs_rcs"


@dataclass
class Result:
    findings: list[Finding] = field(default_factory=list)
    todos: list[Todo] = field(default_factory=list)
    # review_counts[item type][status] = number
    review_counts: dict[str, Counter] = field(default_factory=lambda: defaultdict(Counter))
    files_checked: int = 0

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors


class Doc:
    """A loaded YAML file that remembers line numbers of its parts."""

    def __init__(self, path: Path, rel: str, data: Any, node: yaml.Node | None):
        self.path = path
        self.rel = rel
        self.data = data
        self._node = node

    def line(self, *keys: Any) -> int | None:
        """1-based line of the value at keys (str for mappings, int for lists).

        Falls back to the deepest part of the path that exists.
        """
        node = self._node
        best = node.start_mark.line + 1 if node is not None else None
        for key in keys:
            child = None
            if isinstance(node, yaml.MappingNode):
                for k, v in node.value:
                    if k.value == str(key):
                        child = v
                        best = k.start_mark.line + 1
                        break
            elif isinstance(node, yaml.SequenceNode) and isinstance(key, int):
                if 0 <= key < len(node.value):
                    child = node.value[key]
                    best = child.start_mark.line + 1
            if child is None:
                break
            node = child
        return best
