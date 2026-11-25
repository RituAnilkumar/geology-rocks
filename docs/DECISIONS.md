# Decisions log

Newest first. Format: date — decision — reason — alternatives considered.

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
