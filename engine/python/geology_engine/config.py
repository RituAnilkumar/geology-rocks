# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Engine parameters (engine/config.yaml)."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config.yaml"


@dataclass(frozen=True)
class Params:
    error_rate: float = 0.05
    report_threshold: float = 0.80
    prior_floor: float = 0.002
    max_suggestions: int = 3
    min_gain_bits: float = 0.01
    beginner_max_level: str = "L3"
    trace_top: int = 5

    def with_(self, **changes) -> "Params":
        return replace(self, **changes)


def load_params(path: Path | None = None) -> Params:
    data = yaml.safe_load(Path(path or DEFAULT_CONFIG).read_text(encoding="utf-8")) or {}
    return Params(**data)
