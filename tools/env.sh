# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Shared set-up for the ./check-content, ./run-* commands. Sourced, not run.
# Creates a private Python environment in .venv on first use and keeps its
# packages in step with requirements.txt.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
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
