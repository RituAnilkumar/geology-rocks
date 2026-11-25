# Decisions log

Newest first. Format: date — decision — reason — alternatives considered.

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
