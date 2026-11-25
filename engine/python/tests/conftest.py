# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Engine tests run against the real compiled content."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "engine/python"))

from compiler import compile_core          # noqa: E402
from geology_engine.config import load_params  # noqa: E402
from geology_engine.core import Core       # noqa: E402

_CORE = None


def real_core() -> Core:
    global _CORE
    if _CORE is None:
        _CORE = Core(compile_core(ROOT, check=False))
    return _CORE


@pytest.fixture(scope="session")
def core() -> Core:
    return real_core()


@pytest.fixture(scope="session")
def params():
    return load_params()
