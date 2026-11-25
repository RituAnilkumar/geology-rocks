# Architecture

## Big picture

```
  content/ (YAML, Markdown, media)        sources (BGS, OSM, SSSI ...)
            │                                        │
            ▼                                        ▼
      pipeline/  ── validate (schemas/) ── build ── precompute priors
            │                                        │
            ├── core.sqlite  (bundled in app)        │
            └── packs/<id>/*.sqlite, *.pmtiles  ◄────┘
                         │
                 GitHub Release assets + packs/index.json
                         │
                         ▼
   Android app:  engine (Kotlin) + UI (Compose) + maps (MapLibre/PMTiles)
                 notebook (local SQLite, user data)
```

## Layers of data

1. **Global core** — bundled in the APK. Works with no pack: the key runs with
   a flat (or global-fallback) prior.
2. **Global fallback prior** — coarse lithology → taxon probabilities for places
   without a pack (later; small).
3. **Regional packs** — downloaded on demand. Add named units, a detailed prior
   grid, collecting layers, Learn content, basemap tiles. **Packs never modify
   the core**; they only add children (named units) and priors.
4. **User data** — notebook entries and photos, created on the phone, never
   uploaded.

## Components

| Component | Language | Responsibility |
|---|---|---|
| `schemas/` | JSON Schema | Contract for all content files |
| `pipeline/` | Python | Validate, resolve inheritance, compile SQLite, build PMTiles, compute prior grids, write `packs/index.json` |
| `engine/python` | Python | Reference implementation of SCORING.md; simulation; CLI/web prototype for testing |
| `engine` (Kotlin) | Kotlin | Same behaviour in the app; must pass `scenarios/` |
| `app/` | Kotlin/Compose | UI, maps, notebook, pack manager, export |
| `scenarios/` | YAML | Golden tests shared by both engines |

## Runtime flow of an identification

1. Get location (if permitted) and find context.
2. If a pack covers the location: look up the prior vector for that grid cell
   and find context. Otherwise: fallback prior or uniform.
3. User answers questions (any order). Engine updates the posterior after each.
4. Engine suggests the next question (information gain, kit-filtered).
5. Engine reports the deepest confident node; app looks up the named unit at
   the location's map unit (crosswalk) and checks consistency with the result.
6. App shows result + explanation trace + story + collecting status.
7. User saves to notebook (stores key path, so it is reproducible).

## Pack delivery

- `packs/index.json` on GitHub Releases lists packs: id, name, version,
  required core version, files (name, size, sha256, url, required/optional).
- App downloads chosen files, verifies checksums, stores them in app storage.
- Content updates ship as new pack versions without an app update.

## Why these choices

- **YAML + JSON Schema**: human-readable, reviewable on GitHub by geologists.
- **SQLite**: universal, fast, offline, easy to inspect.
- **PMTiles**: single-file tile archives, no tile server needed, ideal offline.
- **Precomputed priors**: heavy GIS work done once in CI, phone just looks up.
- **Two engine implementations with shared scenarios**: fast science iteration
  in Python, guaranteed identical behaviour in the app.
