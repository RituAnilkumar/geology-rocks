# Geology Rocks — project specification

Status: agreed with product owner (Ritu), 25 November 2026. Changes require a
DECISIONS.md entry.

## 1. Vision

A free, open-source Android field companion that teaches people to read rocks,
not just name them. Offline-first, explains its reasoning, and puts every find
in its local geological story. For curious travellers, hobbyists, students and
teachers. Never monetised.

## 2. Principles

1. **Teach, don't just answer** — "what this tells you" at every step; provenance stories.
2. **Honest uncertainty** — probabilistic; report at the deepest level the evidence supports.
3. **Offline-first** — region packs downloaded in advance (like Merlin bird packs).
4. **FLOSS everywhere, no tracking**, F-Droid compatible, no Google services.
5. **No political boundaries** on any map.
6. **Responsible collecting** built in.
7. **Scientific rigour** — standard classification schemes; expert review of all content.

## 3. Licensing

Code GPL-3.0-or-later; our data, text and media CC BY-SA 4.0; third-party
material keeps its own (free) licence; REUSE-enforced. See `LICENSING.md`.

## 4. Scope

### In scope now
- **Global core**: L0–L4 taxonomy, characters, matrix, rock and mineral pages,
  hint media, engine, kit, field card.
- **Global fallback prior**: coarse lithology so generic ID works anywhere
  (source to be decided; GLiM or Macrostrat — check licences).
- **Regional pack `gb-southwest`** (South West England) with curated areas:
  Bristol and the Avon Gorge, Mendips, Cornish granites (Land's End, St Austell),
  the Lizard, Jurassic Coast (Dorset and East Devon).

### PARKED (do not build until un-parked in ROADMAP)
- AI photo identification (multi-view, Bayesian classifier, conformal sets)
- India pack and Indian languages
- GB-wide pack beyond the South West
- Funding applications (non-software)

The data model already accommodates all parked items.

## 5. Identification design

### Hierarchy (used by the key)
- **L0 Material**: natural rock | weathering product | human-made
  (loose sediment reserved for later)
- **L1 Class**: igneous | sedimentary | metamorphic
- **L2 Group**: e.g. plutonic, hypabyssal, volcanic, pyroclastic; clastic,
  carbonate, chemical/biogenic; foliated, non-foliated, special
- **L3 Subgroup**: composition (felsic → ultramafic) or grain size
- **L4 Rock type**: generic, global (e.g. granite, slate, oolitic limestone)

A few taxa may have two parents (e.g. tuff). Cross-cutting properties
(colour, composition, fossils) are tags, not levels.

### Named units (L5) — context, not key
Inferred from location + L4 result ("very likely the Land's End Granite"),
never chosen by the user. If the identified rock doesn't match the mapped unit,
the app suggests it may be transported.

### Scoring (detail in SCORING.md)
Prior (location + find context) × likelihood of each answer with error rate ε;
skips neutral; next question by expected information gain, filtered by kit;
report the deepest node with summed probability ≥ τ (default 0.8).
Beginner mode reports at L2–L3; expert mode shows L4 and the full spread.

### Find context
outcrop | loose on slope | river | beach | glacial deposit | garden/building.
Sets mixture weights: local bedrock / transported / human-made.

## 6. Modules (first release)

1. **Interactive key** — one question per screen with picture answers +
   "Not sure" + "Skip"; full question list (multi-access); swipe-up candidates
   panel with live probabilities, editable answer path and suggested next test;
   result screen with hierarchy path, inferred named unit + story, collecting
   status, Save, Learn.
2. **Mineral module** — ~20 rock-forming minerals as seen with a hand lens;
   minerals ticked + abundance estimates feed the rock key (incl. simplified QAPF).
3. **Rock and mineral pages** — formation, look-alikes and how to tell apart, uses.
4. **Provenance** — generic formation story + local story when matched.
5. **Learn the local geology** — "what am I standing on?", deep-time story of
   the region, formations to look for, where to see them, landscape links,
   GPS-triggered walks, interactive stratigraphic column. Content tiers:
   automatic vs curated, always labelled.
6. **Field notebook** — local-only SQLite; GPS, photos, notes, find context,
   full key path, result; export CSV, GeoJSON, KML + photos zip via share sheet;
   option to strip/round coordinates.
7. **Responsible collecting** — three states: restricted / code of conduct /
   no data ("check before collecting"); universal rules (landowner permission,
   Coast Protection Act 1949 on beach material in GB, don't hammer outcrops,
   prefer photos).
8. **My kit + field card** — kit set-up (lens, streak plate, nail/knife, glass,
   magnet, vinegar/dilute HCl, water spray, grain-size card, scale card, UV
   torch, hammer + glasses), safety notes, printable A5 field card (grain size,
   scale bar, colour patches, percentage and roundness charts).

## 7. Maps

- Offline basemap: OSM vector tiles (PMTiles). **Basic** (required): water,
  land cover, major place names only. **Detailed** (optional): roads, paths,
  minor places, buildings — offered when starting a walk.
- Geology layer from the pack (BGS 625k, OGL) for priors and display.
- Online extras when connected: BGS Geology 50K WMS and other WMS layers —
  never affect identification. Check WMS terms before release.
- Optional hillshade download.
- Never draw boundaries.

## 8. Roles

- **Ritu** — product owner and science lead: priorities, content review,
  field testing, demos.
- **Claude Code** — implementation, tests, decisions log, plain-language reports.
- **Contributors** (later) — content, photos, translations, regional curation.

## 9. Testing

Content validator; engine property tests; scenario (golden) tests; simulated
confusion matrix; real-specimen field tests; app UI tests. See TESTING.md.

## 10. Open items

- Confirm "Geology Rocks" name is free on Play Store/F-Droid; GitHub repo name.
- Contact BGS about 50K data use and WMS terms (draft email with Claude).
- Teaching collection for specimen testing (M3).
- Indian pilot region (PARKED).
