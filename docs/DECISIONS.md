# Decisions log

Newest first. Format: date — decision — reason — alternatives considered.

## 2026-11-25 — M3 specimen testing tools (Claude, approved plan with Ritu)

- **Session set-up (product owner)**: one laptop per session for now; testers
  with their own laptops download the repository (GitHub "Download ZIP" or git)
  and run the key themselves, then email their test file. *Alternative*:
  testers' phones on the same Wi-Fi (deferred — would open the prototype to
  the local network).
- **Tester details (product owner)**: first name or initials plus experience
  level (beginner / geology student / geologist). **Tester confidence
  (product owner)**: asked when saving ("How sure are you that the key's
  answer is right?"; four options).
- **Where tests are kept**: CSV files in `testing/`, git-ignored because they
  hold testers' names; nothing is uploaded. Every `.csv` in the folder (and
  sub-folders) is read; rows carry a random `run_id`, so a test sent twice is
  counted once. Files are UTF-8 with a byte-order mark so Excel and
  LibreOffice show text correctly. Free text is kept to one line and can never
  be read as a spreadsheet formula. *Alternative*: SQLite (rejected — testers
  and Ritu should be able to open the file in a spreadsheet).
- **One column per question**, holding the option id(s), `NOT SURE`,
  `SKIPPED`, `(none ticked)` or blank (not reached), plus `answer_order`. The
  key result, most likely rock and runner-up are stored as at the time.
- **True rock type** is filled in afterwards on a "Test results" page (choice
  saved immediately), so labels stay covered during testing. It can also be
  typed in a spreadsheet by id or English name; unrecognised names are
  flagged in the report, not guessed.
- **Outcomes**: named the right rock type / right group (reported node
  contains the true rock) / not sure yet (nothing reached τ) / wrong (reported
  node does not contain it), plus "most likely rock type right" as in the
  simulation. The report also **replays** each test through today's content.
- **"Answers that disagree with the content"**: an answer the matrix gives
  < 10 % chance for the true rock. Flags either a tester misreading or a
  probability to review. 10 % is a reporting threshold only, not science.
- **Windows launcher** `run-key.bat` (untested on Windows at time of writing)
  and a Python ≥ 3.11 check with a clear message in `tools/env.sh`.
  `.gitattributes` fixes line endings for `.bat` and shell scripts.
- No new dependencies (standard library `csv`, `statistics`).

## 2026-11-25 — M2 scoring engine prototype (Claude, approved plan with Ritu)

- **Inheritance**: a missing character takes the nearest ancestor's values;
  uninformative only if nothing up the tree lists it. The seed content relies
  on this (no file says `inherit`; values sit on group nodes). DATA_MODEL.md
  wording clarified. With two parents, the first parent's line is used first.
- **Multi-select (product owner)**: ticked = present; unticked = no
  information. Each ticked option uses L = (1−ε)·P(present) + ε/2.
- **Find context before location priors (product owner)**: the context's
  `human` weight (pack `context.yaml`) goes to human-made rock types, shared by
  `human_made` proportions; natural rock types share the rest equally; then
  floor ρ. Replaced by the proper prior grid in M7. Human-made types are found
  through `human_made` entries, not hard-coded IDs.
- **Compiled core format**: `build/core.json` (sorted keys, repeatable) rather
  than SQLite for now: simplest for the Python prototype and easy to inspect.
  SQLite (`core.sqlite`) arrives with the Android build (M4/M7). Built fresh by
  every `./run-*` command; refuses to build if the validator finds errors.
- **Multi-select information gain**: exact expected entropy reduction over all
  2^m tick patterns, using the same "ticked only" update the engine applies.
  Tested against a brute-force calculation. Portable to Kotlin.
- **Eligibility**: "depth reached" = level of the reported node (−1 when
  nothing is reported). Skipped / "not sure" questions are not suggested again
  but leave probabilities unchanged. Ties in gain broken (to 1e−12) by `order`.
- **Missing kit in scenarios**: a scenario without a `kit` list uses the
  default-owned kit.
- **Simulation**: two modes — (A) all questions answered, (B) following the
  key's top suggestion with full kit until the top rock type reaches τ.
  Each simulated answer is replaced by a random one with probability ε.
  Fixed seed so reports are repeatable. 300 / 60 specimens per rock type.
- **Web prototype**: Python standard library `http.server` on 127.0.0.1 only
  plus one plain HTML/CSS/JS page; no web framework, no external scripts or
  fonts (works offline). A testing tool, not the app's design.
- **Dependencies** (pinned in root `requirements.txt`, which replaces
  `pipeline/requirements.txt`): NumPy 2.5.5 (BSD-3-Clause) for engine maths;
  Hypothesis 6.170.17 (MPL-2.0) for property tests. *Alternative*: pure Python
  (multi-select gain made the simulation ~50× slower).
- **Shared set-up**: `tools/env.sh` is used by `./check-content`, `./run-key`,
  `./run-scenarios`, `./run-simulation`.

## 2026-11-25 — M1 content validator (Claude, approved plan with Ritu)

- **Location and command**: Python package `pipeline/validator/`, tests in
  `pipeline/tests/`, run with `./check-content` (repository root). The script
  creates a private `.venv` on first run. *Alternatives*: `uv` (not installed
  on the product owner's machine; plain `venv` + `pip` needs nothing extra),
  a `pyproject.toml` package (unnecessary until the pipeline grows).
- **Dependencies** (pinned in `pipeline/requirements.txt`, all MIT): PyYAML
  6.0.2, jsonschema 4.23.0 (draft 2020-12 support, with `referencing` for
  `$ref` between schema files), pytest 8.3.4.
- **Errors vs warnings** (product owner's choices): `TODO` markers never fail
  the check, they are listed and grouped by type in the report; probabilities
  of exactly 0 or 1 are warnings; TODO `label`/`tells_you` text is a warning.
- **Pages linked but not yet written** are warnings (and listed under TODOs),
  not errors: 35 seed taxa name planned pages. A broken link to any other kind
  of item is an error. Same for named-unit `story` files.
- **Files that break the schema** are reported once and skipped for deeper
  checks, but their IDs still count as existing, so one mistake gives one
  error rather than a cascade.
- **`inherit`** takes values from the nearest ancestor that lists the
  character (values are set high in the tree). With two parents that disagree,
  the first parent wins and a warning is shown.
- **Licence allow-list** for media: CC0-1.0, CC-BY-4.0, CC-BY-SA-4.0,
  OGL-UK-3.0, ODbL-1.0, `LicenseRef-PublicDomain` (public domain). Anything
  else is an error for media, a warning for pack data sources (e.g. BGS WMS
  terms, which are online-only and still to be checked).
- **Extra checks beyond TESTING.md §1** (cheap and catch real mistakes):
  crosswalk rows, find-context weights and `human_made` sum to 1; clast suites
  ≤ 1; every pack layer's source is listed under `sources`; `approved` needs a
  reviewer and date; scenario answers/kit/find contexts exist; child level is
  exactly one below its parent.
- **Report**: `reports/content-report.md` (git-ignored, regenerated each run)
  and the GitHub Actions run summary page. Replaces the M0 placeholder check.

## 2026-11-25 — M0 repository set-up (Claude)

- **Code of conduct licence**: Contributor Covenant 2.1 is itself licensed
  CC-BY-4.0, so `LICENSES/CC-BY-4.0.txt` was added and `CODE_OF_CONDUCT.md`
  is annotated as CC-BY-4.0 in `REUSE.toml`. Text adapted to British English.
  Enforcement contact is a `TODO` until the product owner chooses a project
  email. *Alternative*: write our own code of conduct (rejected — the
  Covenant is the widely recognised standard).
- **CI**: GitHub Actions with two jobs: `reuse lint` via the official
  `fsfe/reuse-action`, and a placeholder content job
  (`.github/scripts/check_wellformed.py`) that only checks every YAML/JSON file
  in `content/`, `scenarios/` and `schemas/` can be read. Replaced by the real
  validator in M1. *Alternative*: an empty placeholder job (rejected — a
  parse check is cheap and already catches broken files).
- **GitHub config licensing**: workflows and CI scripts GPL-3.0-or-later (code);
  issue forms CC-BY-SA-4.0 (text). Recorded in `REUSE.toml`.
- **Issue forms**: GitHub YAML issue forms (bug report, content correction,
  new rock request); blank issues disabled so reports arrive structured.
  Forms remind reporters not to share sensitive sites or personal data.
- **Default branch**: `main`.
- **`.gitignore`**: added `.claude/settings.local.json` (personal, may hold
  private settings).
- **Dependency** (CI only, not shipped): PyYAML (MIT) for the placeholder check.

## 2026-11-25 — Initial design decisions (product owner + Claude, chat session)

- **Name**: Geology Rocks. Check Play Store/F-Droid for clashes before first release.
- **Licensing**: FLOSS throughout. Code GPL-3.0-or-later; own data/text/media
  CC BY-SA 4.0; third-party keeps its own free licence; REUSE enforced.
  *Alternatives*: non-commercial content licence (rejected — product owner
  chose FLOSS everywhere); PolyForm Noncommercial for code (rejected — not open
  source, excluded from F-Droid).
- **Platform**: Android first, native Kotlin + Jetpack Compose; F-Droid.
  *Alternative*: Flutter (cross-platform) — not needed now.
- **Prototype first in Python** to iterate on the matrix before building the app.
- **Key design**: multi-access probabilistic key, L0–L4 hierarchy in the key,
  named units (L5) as inferred context only; hierarchical reporting with τ = 0.8.
- **Scope**: global core + `gb-southwest` pack first. AI, India, funding PARKED.
- **Maps**: OSM vector basemap (basic = water, land cover, major places;
  detailed optional); no political boundaries ever; geology from BGS 625k;
  BGS 50K via WMS online only; hillshade optional.
- **Distribution of packs**: GitHub Release assets + `packs/index.json`; no server, no domain.
- **Content workflow**: YAML in git, JSON Schema validation, review status,
  British English default, translation maps for future languages.
