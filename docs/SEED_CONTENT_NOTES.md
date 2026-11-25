# Seed content — notes for the science lead

Everything in `content/` and `scenarios/` was drafted by Claude in the design
chat (25 Nov 2026) as a **first pass to give structure to the project**. All of
it is `draft`. Nothing should be treated as scientifically checked until you
approve it.

## What's there

- **19 characters** with states, questions, how-to text and "what this tells
  you" explanations (`content/core/characters/`).
- **74 taxonomy nodes, 36 leaf rock types** chosen for South West England,
  including weathering products (kaolin) and human-made materials (brick,
  concrete, slag) (`content/core/taxonomy/`).
- **A first-pass probability matrix**, mostly set on higher nodes and
  inherited, with overrides on leaves.
- **12 minerals**, **12 kit items**, one example rock page (granite).
- **gb-southwest pack seed**: manifest, find-context weights, two example
  clast suites, three PLACEHOLDER crosswalk rows, eight named units with
  TODO ages.
- **9 golden scenarios** plus a template.

## Checks already run (with a throwaway engine, not shipped)

- All 9 scenarios pass against the seed matrix.
- Simulation with all single-choice characters answered: about 75% top-1
  accuracy. The most-confused pairs were:

| True rock | Confused with | Rate |
|---|---|---|
| slate | phyllite | 38% |
| chert | flint | 28% |
| sandstone | greywacke | 27% |
| peridotite | gabbro | 17% |
| basalt | hornfels | 17% |
| gneiss | schist | 17% |
| siltstone | mudstone | 17% |
| breccia | conglomerate | 15% |
| mudstone | shale | 13% |

These are geologically sensible confusions, which suggests the structure works.
Each one points to where a character or probability needs your attention.

## Suggested review order

1. **Taxonomy** — are these the right 36 rock types for the South West? Missing:
   greisen, pegmatite, ball clay, Devonian/Carboniferous volcanic varieties,
   ironstone? Any that should be merged?
2. **Characters** — wording of questions and "what this tells you"; missing
   diagnostic characters (e.g. cleavage sheen vs. bedding for slate/phyllite,
   sorting for greywacke).
3. **Matrix** — start with the confused pairs above.
4. **Scenarios** — confirm or correct; add your own real examples.
5. **Pack** — named units, periods, clast suites, context weights.

## Things deliberately left as TODO

- All hint images and media (none exist yet).
- BGS RCS codes (`refs.bgs_rcs: TODO`).
- BGS 625k map unit codes in the crosswalk (never to be invented).
- Ages of named units; source URLs in the pack manifest; WMS terms.
- Kit "where to get" text.
