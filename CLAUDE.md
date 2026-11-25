# Geology Rocks — instructions for Claude Code

Read this file fully at the start of every session. Then read `docs/ROADMAP.md`
to find the current milestone, and `docs/DECISIONS.md` for choices already made.

## What we are building

**Geology Rocks** is a free, open-source (FLOSS) Android field companion that
teaches people to *read* rocks, not just name them. It works fully offline,
explains its reasoning at every step, and places every find in its local
geological story.

- Core feature: a **multi-access, probabilistic interactive key** with picture
  hints and a "what this tells you" explanation for every answer.
- Supporting modules: mineral module, rock/mineral pages, provenance stories,
  "Learn the local geology", field notebook with export, responsible-collecting
  layers, "My kit" + printable field card.
- First release scope: **global core + one regional pack, `gb-southwest`
  (South West England)**. GB-wide, India and AI identification come later —
  see `docs/ROADMAP.md` (items marked PARKED). Do not build parked features.

Full specification: `docs/PROJECT_SPEC.md`. Seed content status:
`docs/SEED_CONTENT_NOTES.md`. Treat the docs folder as the
source of truth; if the code and the docs disagree, stop and ask.

## Who you are working with

**Ritu is the product owner and science lead, not a software developer.**
She is a glaciologist and geoscientist. She decides *what* the app does and
reviews all geology content. You decide *how* it is built.

Therefore:

1. **Plan before coding.** At the start of each milestone, write a short plan in
   plain language (what you will build, how she will be able to see it, any
   decisions needing her input) and wait for approval.
2. **Make technical decisions yourself** within the constraints below, and log
   each significant one in `docs/DECISIONS.md` (date, decision, reason,
   alternatives considered). Don't ask her to choose between libraries.
3. **Ask her only about product and science questions**: what users should see,
   geology content, classification choices, scope. Ask concisely, with a
   recommended option.
4. **End every milestone with a demo and a plain-language report**:
   - What was built (no jargon; explain any term you must use)
   - How to try it: an APK to install, a command to run, or a page to open —
     with exact step-by-step instructions assuming no developer knowledge
   - A short "what to try" checklist, including things that *should* fail
   - Known limitations and what comes next
5. **Never invent or finalise geology content.** You may draft content to fill
   structures, but it must carry `review: {status: draft}` and be listed in the
   milestone report for her review. Never mark content `approved` yourself.
   Never invent map unit codes, ages, site names or legal rules — use
   `TODO` placeholders and flag them.
6. Use **British English** in all user-facing text (en-GB is the default locale).

## Non-negotiable constraints

- **Licensing** (see `LICENSING.md`):
  - Code: `GPL-3.0-or-later`. Our own content and media: `CC-BY-SA-4.0`.
  - Third-party material keeps its own licence, recorded per file. Only accept
    free licences (no NC, no ND). If in doubt, don't add it — ask.
  - Every file must carry REUSE-compliant licence information
    (`reuse lint` must pass in CI). The build fails on any missing licence.
- **FLOSS only, F-Droid compatible**: no Google Play Services, Firebase,
  Crashlytics, proprietary SDKs, analytics or trackers. Every dependency must
  have an OSI/FSF-approved licence. Log each new dependency in DECISIONS.md.
- **Offline-first**: identification must work with no network. Online layers
  (WMS) are optional extras and must never change identification results.
- **Privacy**: no accounts, no servers, no data leaves the phone except by
  explicit user export. No telemetry.
- **Maps never draw political boundaries** (`draw_boundaries: false` in every
  style). Basemap is OSM vector tiles; hillshade is optional.
- **Honest uncertainty**: never report a more specific answer than the evidence
  supports (see `docs/SCORING.md`, hierarchical reporting).
- **Content is data, not code**: geology lives in `content/` as YAML and is
  compiled into SQLite/PMTiles by `pipeline/`. Never hard-code geology in the app.

## Repository layout

```
CLAUDE.md               this file
docs/                   specifications (source of truth)
schemas/                JSON Schemas for every content file type
content/core/           global core: taxonomy, characters, minerals, pages, media
content/packs/<id>/     regional packs (first: gb-southwest)
scenarios/              golden test cases (expert walkthroughs)
pipeline/               build scripts: YAML/GeoJSON -> SQLite + PMTiles (to be built)
engine/                 scoring engine (Python prototype first, then Kotlin) (to be built)
app/                    Android app (to be built in Phase 1)
.claude/commands/       custom commands for common tasks
```

Each of `content/`, `engine/`, `app/`, `pipeline/` has its own CLAUDE.md with
area-specific rules. Read it before working in that folder.

## Technology defaults (change only with a logged decision)

- Content: YAML (source), validated by JSON Schema (draft 2020-12).
- Pipeline and engine prototype: Python 3.11+, managed with `uv` or `pip`;
  tests with `pytest`.
- Android: Kotlin, Jetpack Compose, Room (SQLite), MapLibre Native for maps,
  PMTiles for offline tiles. Minimum SDK chosen to support older/cheaper phones.
- Distribution: pack files published as GitHub Release assets; app distributed
  via F-Droid (and optionally GitHub Releases APKs).
- CI: GitHub Actions — `reuse lint`, content validation, engine tests,
  scenario tests, (later) Android build and tests.

## Definition of done (every milestone)

- [ ] All tests pass locally and in CI (including `reuse lint` and content validation)
- [ ] New behaviour has tests written *before* or alongside the code
- [ ] Every scenario in `scenarios/` still passes (or a change is explained and approved)
- [ ] Docs updated if behaviour or structure changed; DECISIONS.md updated
- [ ] Draft content listed for review; nothing marked approved by you
- [ ] Plain-language milestone report with demo instructions and "what to try"

## Working style

- Small steps, frequent commits, clear commit messages.
- Prefer simple, readable solutions over clever ones; this project must be
  maintainable by volunteers.
- When something in the spec seems wrong or underspecified, say so and propose
  a fix rather than silently working around it.
- Before large changes (new dependency, schema change, restructuring), explain
  the impact in plain language and get approval.
