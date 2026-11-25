# engine/ — rules for the scoring engine

The engine turns answers into probabilities. It is the scientific heart of the
app, so correctness matters more than speed or elegance. Read `docs/SCORING.md`
in full before touching anything here.

## Two implementations, one behaviour

1. **Python prototype** (`engine/python/`, milestone M2) — used for fast
   iteration on the matrix and for Ritu's specimen testing.
2. **Kotlin implementation** (`engine/kotlin/` or inside `app/`, Phase 1) — what
   ships in the app.

Both must pass **exactly the same scenario files** in `scenarios/` and the same
property tests. The scenario files are the contract between them. If they
disagree, the Python prototype + SCORING.md is the reference until a decision
in DECISIONS.md says otherwise.

## Invariants (must have property tests)

1. Posterior probabilities over leaf taxa always sum to 1 (±1e-9).
2. **Robustness**: a single answer contradicting the true taxon never drives its
   probability to zero (error rate ε > 0).
3. **Skipping is neutral**: "skip" or "not sure" leaves the posterior unchanged.
4. **Order independence**: the same set of answers in any order gives the same
   posterior.
5. **No over-claiming**: the reported node is the deepest node whose summed
   descendant probability ≥ threshold τ; never deeper.
6. **Kit filter**: a question needing kit the user doesn't have is never
   *suggested* (it can still be answered if the user chooses it).
7. **Question choice**: the suggested next question is the one with the highest
   expected information gain among eligible questions (ties broken
   deterministically by character order).
8. Priors from the location/find context never set any taxon to exactly zero
   (floor ρ > 0).

## Rules

- Pure functions, no I/O inside the scoring core. Inputs: compiled core data,
  optional pack prior vector, answers. Outputs: posterior, reported node,
  ranked next questions, explanation trace.
- Every result must carry an **explanation trace**: which answers moved which
  candidates and by how much, so the app can explain its reasoning.
- Parameters (ε, τ, ρ) live in one config file with documented defaults.
- Never hard-code taxon IDs or geology in engine code.
