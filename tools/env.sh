# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Shared set-up for the ./check-content, ./run-* commands. Sourced, not run.
# Creates a private Python environment in .venv on first use and keeps its
# packages in step with requirements.txt.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  if ! command -v python3 >/dev/null || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
    echo "Geology Rocks needs Python 3.11 or newer. Install it from https://www.python.org/downloads/"
    echo "(on Ubuntu/WSL: sudo apt install python3 python3-venv), then try again."
    exit 2
  fi
  echo "First run: setting up (this takes a minute or two)..."
  if ! python3 -m venv .venv; then
    echo "Could not set up Python. On Ubuntu/WSL, run:  sudo apt install python3-venv"
    exit 2
  fi
fi
if ! cmp -s requirements.txt .venv/.requirements-installed; then
  echo "Installing or updating Python packages..."
  .venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt
  cp requirements.txt .venv/.requirements-installed
fi
export PYTHONPATH="$PWD/pipeline:$PWD/engine/python"
PY=.venv/bin/python
