# pipeline/ — rules for the build pipeline

The pipeline compiles human-editable sources into what the phone uses. Read
`docs/DATA_MODEL.md` and `docs/PACK_SPEC.md` first.

## Outputs

1. `core.sqlite` — taxonomy, characters, states, resolved likelihood matrix,
   minerals, kit, text (all languages), pages, glossary, timescale, media
   records. Bundled inside the app.
2. Per pack (`gb-southwest` first):
   - `<pack>.sqlite` — named units, crosswalk, context weights, stories, walks,
     sites, collecting rules, text.
   - `<pack>-geology.pmtiles` — bedrock polygons with unit codes.
   - `<pack>-prior.*` — precomputed prior grid (see PACK_SPEC.md).
   - `<pack>-collecting.pmtiles` — simplified collecting zones.
   - `<pack>-basemap-basic.pmtiles`, `<pack>-basemap-detail.pmtiles` (OSM).
   - optional `<pack>-hillshade.pmtiles`.
3. `packs/index.json` — list of packs with version, size, sha256, URLs.

## Rules

- Deterministic builds: same inputs → byte-identical outputs where feasible.
- Validate all inputs against `schemas/` before building; fail loudly.
- Resolve matrix inheritance at build time; detect cycles.
- Every spatial source must be listed in the pack manifest `sources` with its
  licence and attribution; the pipeline refuses unlisted sources.
- Attribution strings are written into the outputs so the app can display them.
- Raw third-party downloads go in a cache directory ignored by git, never
  committed unless their licence allows redistribution and size is small.
- Heavy geospatial work (catchments, superficial deposits, transport priors)
  happens here, never on the phone.
- Publishing: GitHub Actions builds packs and attaches them to a GitHub Release.
