# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Content validator for Geology Rocks (milestone M1).

Checks everything in content/ and scenarios/ against schemas/ and the rules in
docs/TESTING.md section 1, and writes a plain-language Markdown report.

Use from code:   result = validate(Path("."))
Use from shell:  python -m validator   (with pipeline/ on PYTHONPATH)
"""
from .model import Finding, Result, Todo
from .checks import validate

__all__ = ["validate", "Finding", "Result", "Todo"]
