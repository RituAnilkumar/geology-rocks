@echo off
REM SPDX-FileCopyrightText: Geology Rocks contributors
REM SPDX-License-Identifier: GPL-3.0-or-later
REM
REM Windows: start the key prototype in your browser (http://localhost:8765/).
REM Double-click this file, or type run-key in a Command Prompt in this folder.
REM Close the window (or press Ctrl+C) to stop.
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe goto installed
set "BASEPY="
REM Prefer the Python that is active now (e.g. a conda environment), then the py launcher.
python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1 && set "BASEPY=python"
if not defined BASEPY py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1 && set "BASEPY=py -3"
if not defined BASEPY (
  echo Geology Rocks needs Python 3.11 or newer.
  echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH", then try again.
  pause
  exit /b 2
)
echo First run: setting up (this takes a minute or two)...
%BASEPY% -m venv .venv || (pause & exit /b 2)
:installed
fc /b requirements.txt .venv\.requirements-installed >nul 2>&1
if errorlevel 1 (
  echo Installing or updating Python packages...
  .venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements.txt || (pause & exit /b 2)
  copy /y requirements.txt .venv\.requirements-installed >nul
)
set "PYTHONPATH=%CD%\pipeline;%CD%\engine\python"
.venv\Scripts\python.exe -m geology_engine web %*
pause
