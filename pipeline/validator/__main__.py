# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Command line: python -m validator [--root DIR] [--report FILE]

Exit code 0 = no errors, 1 = errors found.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checks import validate
from .report import markdown_report, terminal_summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="validator", description="Check Geology Rocks content.")
    ap.add_argument("--root", default=".", help="repository folder (default: current folder)")
    ap.add_argument("--report", default="reports/content-report.md",
                    help="where to write the Markdown report ('-' to skip)")
    args = ap.parse_args(argv)

    root = Path(args.root)
    result = validate(root)
    report_path = None
    if args.report != "-":
        path = Path(args.report)
        if not path.is_absolute():
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown_report(result), encoding="utf-8")
        report_path = args.report
    print(terminal_summary(result, report_path))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
