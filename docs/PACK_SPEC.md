# Regional pack specification

First pack: **`gb-southwest`** (South West England).
Extent: bounding box approx. [-6.5, 49.8, -1.8, 51.8] (lon/lat, WGS84) —
a geographic box, not an administrative boundary.

## Files produced per pack

| File | Required | Contents | Est. size |
|---|---|---|---|
| `<pack>.sqlite` | yes | named units, crosswalk, context weights, clast suites, stories, sites, walks, collecting rules, text | 5–30 MB incl. images |
| `<pack>-geology.pmtiles` | yes | bedrock polygons with unit codes (BGS 625k) | 5–20 MB |
| `<pack>-prior.sqlite` (or raster) | yes | precomputed prior per grid cell × find context (sparse, top-N taxa per cell) | 5–15 MB |
| `<pack>-collecting.pmtiles` | yes | simplified collecting zones | 2–10 MB |
| `<pack>-basemap-basic.pmtiles` | yes | OSM: water, land cover, major place names | 5–15 MB |
| `<pack>-basemap-detail.pmtiles` | optional | OSM: roads, paths, minor places, buildings, parking | 50–150 MB |
| `<pack>-hillshade.pmtiles` | optional | hillshade from OS Terrain 50 | 50–400 MB |

Sizes are estimates until the pipeline produces real files.

## Manifest (`manifest.yaml`)

See `content/packs/gb-southwest/manifest.yaml` and `schemas/pack_manifest.schema.json`.
Key fields: `id`, `name`, `extent.bbox`, `version`, `requires_core`,
`taxa_present`, `sources[]` (id, name, licence SPDX, attribution, url, notes),
`layers.offline[]`, `layers.online[]`, `map_style.draw_boundaries: false`.

## Data sources for gb-southwest

| Source | Use | Licence | Status |
|---|---|---|---|
| BGS Geology 625k | bedrock polygons, unit codes, prior | OGL v3 | Open — usable |
| BGS Geology 50K | detailed display | Licensed download; free to view via WMS | Online WMS only unless BGS grants permission. Check WMS terms. |
| BGS superficial thickness 1 km hex grid | transported-material weighting | OGL | Check availability/format |
| OS Terrain 50 | hillshade, catchments | OGL v3 | Open — usable |
| OpenStreetMap | basemap | ODbL 1.0 | Open — usable with attribution |
| Natural England SSSI boundaries | collecting layer | OGL v3 | Open — usable |
| Local codes (e.g. Jurassic Coast fossil collecting code) | rules text | Link + paraphrase | Content task |

The pipeline refuses any source not listed in the manifest.

## Prior grid computation (pipeline)

1. Grid: ~250 m cells covering the extent (configurable).
2. `P_bedrock(t | cell)`: from the geology map unit(s) in the cell via the
   crosswalk (area-weighted if several units).
3. `P_transport(t | cell)`: per find context —
   - river: area-weighted bedrock composition of the upstream catchment
     (from DEM flow accumulation), decayed by distance;
   - beach: clast suite for the coastal zone (from `context.yaml`);
   - glacial: limited in most of SW England, which lay largely beyond the main
     ice limits (exceptions to be checked by the science lead, e.g. the Isles
     of Scilly and parts of the Bristol Channel coast) — keep the mechanism,
     use small weights; document in DECISIONS.md;
   - loose on slope: bedrock of upslope cells.
4. `P_human(t)`: from `context.yaml` (brick, concrete, slag, building stone).
5. Combine with context weights `w_local, w_transport, w_human`.
6. Store per cell and context only taxa above a small threshold (sparse).
7. Apply floor ρ in the engine, not here.

## Legend crosswalk

```yaml
- map_unit: TODO_BGS_CODE        # never invent codes; fill from the BGS data
  label: "..."
  named_unit: nu.<id> | null
  taxa: {<taxon id>: p, ...}     # sums to 1
  review: {status: draft}
```

Building the crosswalk is the largest per-pack content task. The pipeline
should generate a starter list of all unit codes and descriptions found in the
BGS data so a geologist can fill in the taxa.

## Collecting zones

States: `restricted` | `code_of_conduct` | (absent = "no data — check before
collecting"). The app always shows the universal rules too. The text must make
clear that absence of data is not permission.

## Online layers

WMS layers listed in `layers.online`. Clearly labelled "online". Never used by
the engine.
