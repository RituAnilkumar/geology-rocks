# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""python -m compiler [--root DIR]  ->  build/core.json"""
import argparse
import sys
from pathlib import Path

from . import CompileError, write_core


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="compiler")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    try:
        out = write_core(Path(args.root))
    except CompileError as exc:
        print(f"❌ {exc}")
        return 1
    print(f"Compiled content to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
