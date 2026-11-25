# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Placeholder content check (M0): every YAML/JSON file must parse.

Replaced by the full validator in milestone M1.
Usage: python check_wellformed.py DIR [DIR ...]
"""
import json
import sys
from pathlib import Path

import yaml


def main(dirs):
    errors, count = [], 0
    for d in dirs:
        for path in sorted(Path(d).rglob("*")):
            if path.suffix not in {".yaml", ".yml", ".json"}:
                continue
            count += 1
            try:
                with path.open(encoding="utf-8") as f:
                    if path.suffix == ".json":
                        json.load(f)
                    else:
                        list(yaml.safe_load_all(f))
            except Exception as exc:  # report every file, not just the first
                errors.append(f"{path}: {exc}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"Checked {count} files: {count - len(errors)} OK, {len(errors)} with errors.")
    return 1 if errors or count == 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["content", "scenarios", "schemas"]))
