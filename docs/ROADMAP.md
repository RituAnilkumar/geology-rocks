# Roadmap

Current milestone: **M0** — local set-up done; waiting for the first push to
GitHub and a green CI tick (update this line as milestones complete).

Each milestone ends with a plain-language report, a demo and a "what to try"
checklist for the product owner. Acceptance criteria are what "done" means.

## Phase 0 — Foundations

### M0 — Repository set-up
Status: licence texts, `reuse lint`, code of conduct, issue forms and CI done
locally (25 Nov 2026). Remaining: push to GitHub and confirm green CI.
- Git initialised, pushed to GitHub (`geology-rocks`).
- Licence texts in `LICENSES/` (GPL-3.0-or-later and CC-BY-SA-4.0 included in
  the bundle; third-party ones such as ODbL-1.0 and OGL-UK-3.0 added when
  first used) via `reuse download`.
- `reuse lint` passes. Code of conduct added (Contributor Covenant).
- GitHub Actions CI: reuse lint + (placeholder) content validation job.
- Issue templates: bug, content correction, new rock request.
- **Demo:** the GitHub page with a green CI tick; explanation of where things live.

### M1 — Content schemas, validator, seed content
- Validator (Python) implementing TESTING.md §1, run by a single command and in CI.
- Seed content in this bundle passes (or failures are explained and fixed).
- Validator report readable by a non-developer (Markdown summary).
- **Demo:** run the validator; see the report of drafts and TODOs; deliberately
  break a file and see a clear error.

### M2 — Scoring engine prototype (Python)
- Pipeline step: resolve inheritance → compiled matrix (SQLite or JSON).
- Engine per SCORING.md with all property tests.
- Scenario runner; all `scenarios/` pass or failures are reported for review.
- Simulation report (confusion matrix, most-confused pairs).
- Simple **local web prototype** of the key (runs on Ritu's laptop with one
  command; works in a browser; picture placeholders where hints are TODO):
  find context, question screen, candidates panel, result with explanation.
- **Demo:** key out "a Cornish beach granite" in the browser; read the
  simulation report.

### M3 — Specimen testing support
- Prototype logs every run to a CSV (answers, result, true answer entered
  afterwards).
- Summary report generator.
- Fixes to content/engine from findings (content changes stay draft until reviewed).
- **Demo:** testing session with a teaching collection; summary report.

## Phase 1 — Android MVP (gb-southwest)

- M4 Android project skeleton, F-Droid-friendly build, Kotlin engine passing scenarios.
- M5 Key UI (question, multi-access list, candidates panel, result), beginner/expert.
- M6 Rock and mineral pages; mineral module feeding the key.
- M7 Pipeline builds core.sqlite and gb-southwest pack (625k geology, crosswalk,
  prior grid, basic basemap); pack download manager; location priors.
- M8 Field notebook + export; My kit; field card PDF.
- M9 Collecting layer + universal rules; named-unit inference and provenance.
- M10 Beta release on F-Droid (and GitHub APK).

## Phase 2 — Context and Learn (gb-southwest)

- Learn module: "what am I standing on?", regional story, formations, sites,
  stratigraphic column; walks with detailed basemap download.
- Online WMS layers (BGS 50K) after terms check.
- Optional hillshade.

## Phase 3 — Community and growth

- Contributor workflow, Weblate translations (Welsh first), more curated areas,
  GB-wide pack.

## PARKED — do not start without the product owner un-parking

- 🔒 AI photo identification
- 🔒 India pack (and Indian languages)
- 🔒 Funding applications
