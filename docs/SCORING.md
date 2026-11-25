# Scoring engine specification

This is the reference for both the Python prototype and the Kotlin engine.

## Notation

- `T` = set of **leaf** taxa (L4 rock types; or the deepest defined level).
- Each internal node `n` has descendant leaves `D(n)`.
- Characters `c` with discrete states `s ∈ S(c)`.
- Matrix: `P(s | t, c)` for leaf `t` (inheritance resolved at build time).
  If `t` has no entry for `c`, use uniform `1/|S(c)|` (uninformative).
- Answers `A = {(c_i, s_i)}`. "Skip" and "Not sure" are not answers.

## Parameters (defaults; in one config file)

| Symbol | Name | Default | Meaning |
|---|---|---|---|
| ε | error rate | 0.05 | Probability the user's answer is wrong (misread, bad light) |
| τ | report threshold | 0.80 | Summed probability needed to report a node |
| ρ | prior floor | 0.002 | Minimum prior for any taxon after normalisation inputs |
| κ | max suggestions | 3 | Number of next-question suggestions shown |

## 1. Prior

Inputs: optional pack prior for the location's grid cell and the chosen find
context, else the global fallback, else uniform.

```
π(t) = max(prior_input(t), ρ)    then normalise so Σ π(t) = 1
```

Pack prior construction (done in the pipeline, see PACK_SPEC.md):

```
prior_input(t) = w_local(ctx) · P_bedrock(t | cell)
               + w_transport(ctx) · P_transport(t | cell)
               + w_human(ctx) · P_human(t)
```

Human-made taxa (L0 = human-made) only receive mass from `P_human`.

## 2. Likelihood with error rate

For an answer state `s` on character `c` with `k = |S(c)|` states:

```
L(s | t) = (1 − ε) · P(s | t, c) + ε / k
```

This guarantees `L > 0`, so no single answer eliminates a taxon (robustness
invariant).

### Multi-select characters
Some characters allow several states at once (e.g. minerals present). They are
modelled as independent binary sub-characters (`present` / `absent`) per option,
each with its own probabilities. "Not checked" options are skipped (neutral).

### Ordinal characters
For ordered states (grain size, hardness bands) the matrix already encodes
spread across neighbouring states; no special handling in v1.

## 3. Posterior

```
post(t) ∝ π(t) · Π_{(c,s)∈A} L(s | t)
```

Compute in log space; normalise over `T`. Order of answers must not matter.

Node probability: `P(n) = Σ_{t ∈ D(n)} post(t)`.
For multi-parent taxa, a leaf contributes its full probability to each parent's
sum (sums can then exceed 1 across siblings; the reporting rule below is
unaffected because it walks one path at a time).

## 4. Hierarchical reporting

```
start at the root's children
repeat:
    among children of the current node, pick the child with highest P(child)
    if P(child) ≥ τ: move to child
    else: stop
report the current node and P(node)
also report the top leaf and its probability as "most likely"
```

- Beginner mode: cap reporting depth at L3 (show L4 as "most likely ...").
- Expert mode: no cap; show the full ranked leaf list.
- Output phrase example: "Felsic plutonic rock (88%) — most likely granite (78%)".

## 5. Next-question selection

Eligible characters: not yet answered, `applies_from` level ≤ depth reached so
far + 1, and (for *suggestions*) all `kit_required` items in the user's kit.

Expected information gain:

```
H(post) = − Σ_t post(t) log post(t)
P(s) = Σ_t post(t) · L(s | t)
post_s(t) ∝ post(t) · L(s | t)
EIG(c) = H(post) − Σ_s P(s) · H(post_s)
```

Suggest the top κ characters by EIG; ties broken by the character's `order`
field. Characters with EIG below 0.01 bits are not suggested.

Optional (later): a small "cost" per character so cheap observations are
preferred over kit tests when gains are similar: score = EIG − λ·cost.

## 6. Explanation trace

For each answer, record the change in log-probability of the top 5 candidates.
The app turns this into sentences like "Interlocking crystals made sandstone
much less likely". The trace is part of the engine output.

## 7. Named-unit inference (context, not scoring)

After reporting: look up the map unit at the location (pack crosswalk).
- If the reported node is an ancestor of, or equal to, the unit's dominant
  taxon → "very likely <named unit>".
- Else → "doesn't match the local bedrock; it may have been transported"
  (and, if a clast suite exists, suggest its likely sources).

## 8. Required tests

Property tests for all invariants listed in `engine/CLAUDE.md`, plus:
- all `scenarios/*.yaml` pass;
- simulation: for each leaf `t`, sample answers to every character from
  `P(·|t)` with ε noise, run the engine, record the top leaf → confusion matrix.
  Report overall accuracy and the 10 most-confused pairs (human-readable).
