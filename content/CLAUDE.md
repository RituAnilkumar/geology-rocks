# content/ — rules for geology content

Everything in this folder is **scientific content** that Ritu (science lead) and
later other experts review. Your job here is mostly structural: scaffolding
files, keeping them valid, wiring references. Read `docs/DATA_MODEL.md` and
`docs/CONTENT_GUIDE.md` before editing.

## Golden rules

1. **Never mark anything `approved`.** Only a human reviewer does that.
   New or changed content gets `review: {status: draft}`.
2. **Never invent facts**: no made-up map unit codes, ages, site names,
   localities, legal rules, mineral properties or probabilities presented as
   final. Use `TODO:` markers and list them in your report.
3. Drafting is allowed when asked (e.g. a first pass at state probabilities or
   a "tells you" sentence), but always as `draft` and always flagged.
4. **Every media file needs licence metadata** (see `content/core/media/README.md`).
   No media file may be added without an SPDX licence, author and source.
   Only free licences (CC0, CC-BY, CC-BY-SA, OGL, ODbL, public domain). No NC/ND.
5. All user-facing text is **British English** and lives in `{en: "..."}`
   translation maps so other languages can be added later.
6. IDs are permanent. Never rename an ID once it exists; deprecate instead
   (`deprecated: true`, `replaced_by: <id>`).

## File types and locations

| What | Where | Schema |
|---|---|---|
| Taxonomy nodes (L0–L4) | `core/taxonomy/**/<id-tail>.yaml` | `schemas/taxon.schema.json` |
| Characters + states | `core/characters/<id-tail>.yaml` | `schemas/character.schema.json` |
| Minerals | `core/minerals/<id-tail>.yaml` | `schemas/mineral.schema.json` |
| Kit items | `core/kit/kit.yaml` | `schemas/kit.schema.json` |
| Long text pages | `core/pages/<id>.md` | Markdown with front matter |
| Media + licence records | `core/media/**` + `<file>.license` or `REUSE.toml` | `schemas/media.schema.json` |
| Pack manifest | `packs/<pack>/manifest.yaml` | `schemas/pack_manifest.schema.json` |
| Legend crosswalk | `packs/<pack>/crosswalk.yaml` | `schemas/crosswalk.schema.json` |
| Find context + clast suites | `packs/<pack>/context.yaml` | `schemas/context.schema.json` |
| Named units (L5) | `packs/<pack>/named_units/*.yaml` | `schemas/named_unit.schema.json` |

## Matrix (state probabilities)

- Live inside each taxon file under `characters:`.
- For `kind: single` characters, probabilities for one character must sum to 1.0 (±0.001).
- For `kind: multi` characters (e.g. minerals visible), each value is an
  independent probability that the option is present; they do not sum to 1.
- Use `inherit` to take the parent's values; the pipeline resolves inheritance.
- A character not listed for a taxon (and not inherited) is uninformative for
  that taxon — the engine treats it as uniform. Do not fill gaps with guesses.
- Avoid exact 0 or 1; the engine applies an error rate, but keep values in
  [0.01, 0.99] so content stays honest about variability.

## Validation

Run the content validator (built in milestone M1) before every commit. It
checks schemas, ID references, probability sums, inheritance cycles, media
licences and review status. CI runs it too.
