# Milestone prompts for Claude Code

Paste one prompt at a time, in order. Each asks Claude Code to plan first and
wait for your approval. You can add your own comments after the prompt.

---

## M0 — Repository set-up

```
Read CLAUDE.md, docs/PROJECT_SPEC.md, docs/ROADMAP.md and docs/DECISIONS.md.
We are starting milestone M0 (repository set-up). I am the product owner and
not a developer, so explain anything I need to do step by step.

Goals:
1. Initialise git in this folder and connect it to my GitHub repository
   "geology-rocks" (help me sign in or create it if needed).
2. Check `reuse lint` passes (GPL-3.0-or-later and CC-BY-SA-4.0 texts are
   already in LICENSES/). Third-party licences such as ODbL-1.0 and
   OGL-UK-3.0 are added later, when the first files using them arrive.
3. Add a code of conduct (Contributor Covenant) and GitHub issue templates
   (bug report, content correction, new rock request).
4. Set up GitHub Actions CI that runs `reuse lint` and a placeholder content
   validation job.
5. Push everything.

First give me a short plain-language plan and wait for my approval. Finish
with a milestone report following CLAUDE.md, including how to see the green
CI tick on GitHub. Update docs/ROADMAP.md and docs/DECISIONS.md.
```

---

## M1 — Content schemas, validator and seed content

```
Read CLAUDE.md, content/CLAUDE.md, docs/DATA_MODEL.md, docs/TESTING.md and
the schemas/ folder. We are starting milestone M1.

Goals:
1. Build the content validator in Python (in pipeline/), covering everything
   in docs/TESTING.md section 1, runnable with one command and in CI.
2. Run it on the seed content in content/ and scenarios/. Fix structural
   problems; for any geology problem, do NOT change the science — list it
   for me to review.
3. Produce a readable Markdown report: counts by review status, all TODOs,
   all errors and warnings.
4. Add tests for the validator itself (good and deliberately broken files).

Plan first and wait for approval. End with a milestone report and a
"what to try" list that includes breaking a file on purpose to see the error.
```

---

## M2 — Scoring engine prototype and web key

```
Read CLAUDE.md, engine/CLAUDE.md, docs/SCORING.md, docs/TESTING.md and the
scenarios/ folder. We are starting milestone M2.

Goals:
1. Pipeline step: compile content (resolve matrix inheritance) into a single
   file the engine reads.
2. Python engine implementing docs/SCORING.md exactly, with property tests for
   every invariant in engine/CLAUDE.md.
3. Scenario runner: run every file in scenarios/ and report pass/fail in plain
   language. If a scenario fails because the content seems wrong, tell me —
   don't change the scenario or the science yourself.
4. Simulation report (confusion matrix, 10 most-confused pairs, average
   number of questions) as Markdown + CSV.
5. A simple local web prototype of the key that I can start with one command
   and use in my browser: choose find context and my kit, answer questions
   (with "Not sure" and "Skip"), jump to any question, see the candidates panel
   with probabilities and my answer path, see the result at the reported level
   with the explanation of each step. Use the content text; show a placeholder
   box where hint images are TODO.

Plan first and wait for approval. Keep the web prototype simple — it is a
testing tool, not the final app. End with a milestone report and step-by-step
instructions to start the prototype on my laptop.
```

---

## M3 — Specimen testing support

```
Read CLAUDE.md and docs/TESTING.md section 5. We are starting milestone M3.

Goals:
1. Add run logging to the web prototype: each identification is saved to a CSV
   with the answers, result, timestamp, and a field to enter the true rock type
   afterwards (plus specimen ID and tester name).
2. A summary report generator: accuracy by rock type, most common wrong
   answers, questions that were most often skipped or answered "not sure".
3. A one-page printable instruction sheet for student testers.

Plan first and wait for approval. After I run a testing session, I'll share
the CSV and we'll review findings together; content changes stay draft until
I approve them.
```

---

## Phase 1 kick-off (after M3)

```
Read CLAUDE.md, app/CLAUDE.md, pipeline/CLAUDE.md, docs/ARCHITECTURE.md and
docs/ROADMAP.md (Phase 1). Propose a detailed plan for milestones M4–M10,
including how I will install and test each build on my Android phone, and
what you need from me (content, decisions). Wait for approval before starting M4.
```

---

## Handy one-off prompts

- **Add a scenario**: "Add a scenario: a [rock] found [context] near
  [place]. My observations: [list]. I expect [result]. Use
  scenarios/_template.yaml."
- **Review queue**: "List all draft content grouped by type, most important first."
- **Explain a result**: "In the prototype, why did [answers] give [result]?
  Show the explanation trace in plain language."
- **Weekly check**: "Run all checks (reuse, validator, tests, scenarios,
  simulation) and summarise in five bullet points."
