# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Command line for the engine prototype.

  python -m geology_engine scenarios     run scenarios/, exit 1 if any fail
  python -m geology_engine simulate      write reports/simulation-*.md/csv
  python -m geology_engine web           start the browser key
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compiler import CompileError, write_core

from .config import load_params
from .core import Core


def _core(root: Path) -> Core:
    return Core.load(write_core(root))      # always rebuild from current content


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geology_engine")
    ap.add_argument("command", choices=["scenarios", "simulate", "web"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--specimens", type=int, default=None, help="simulation: specimens per rock type")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        core = _core(root)
    except CompileError as exc:
        print(f"❌ {exc}")
        return 1
    params = load_params()

    if args.command == "scenarios":
        from .scenarios import format_results, run_all
        results = run_all(core, params, root / "scenarios")
        print(format_results(results))
        return 0 if all(r.ok for r in results) else 1
    if args.command == "simulate":
        from .simulate import run_and_write
        kwargs = {} if args.specimens is None else {"n_all": args.specimens, "n_key": args.specimens}
        print(run_and_write(core, params, root / "reports", **kwargs))
        return 0
    from .web.server import serve
    serve(core, params, port=args.port, open_browser=not args.no_browser)
    return 0


if __name__ == "__main__":
    sys.exit(main())
