# Testing strategy

Six layers, from automatic to hands-on.

## 1. Content validator (M1)
Runs on every commit and in CI.
- Every file matches its JSON Schema.
- All referenced IDs exist (parents, states, media, kit, named units, pages).
- No inheritance cycles; every L4 taxon reaches an L0 root.
- Each character's probabilities sum to 1 (±0.001); values in [0, 1].
- Every media file has licence metadata; licence is on the allow-list.
- Every state has a label and `tells_you` (warning if `TODO`).
- Report: counts of draft / in_review / approved items; list of TODOs.

## 2. Engine property tests (M2)
The invariants in `engine/CLAUDE.md` as automated (ideally property-based,
e.g. Hypothesis) tests.

## 3. Scenario (golden) tests (M2 onwards)
Files in `scenarios/` written by the science lead. Each gives a context and a
sequence of answers, and expectations at checkpoints. Shared by the Python and
Kotlin engines. See `schemas/scenario.schema.json` and existing examples.
Files starting with `_` (e.g. `_template.yaml`) are ignored by the runner.

Expectation types:
- `reported_node_is` / `reported_node_is_ancestor_of`
- `top_leaf_is`, `top_leaf_in` (list)
- `p_at_least: {node: p}` / `p_at_most: {node: p}`
- `not_suggested: [char ids]` (e.g. acid test without acid in kit)
- `suggested_first_in: [char ids]`

## 4. Simulation (M2)
Synthetic specimens sampled from the matrix with noise → confusion matrix,
overall accuracy, most-confused pairs, average number of questions to reach τ.
Output a short human-readable report (Markdown) plus a CSV.

## 5. Specimen testing (M3)
Real specimens from a teaching collection. The prototype logs each run
(answers, result, correct answer). Summary report: accuracy by rock type,
where users went wrong, questions that confused people.

## 6. App tests (Phase 1)
Kotlin engine vs scenarios; Compose UI tests for the key flow; screenshot
tests; manual checklist on a real phone each milestone.
