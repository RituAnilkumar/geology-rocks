# Getting started — for Ritu (no coding experience needed)

This guide takes you from this folder to a working project on GitHub, with
Claude Code doing the building. You act as product owner: you give direction,
try the demos and review the geology.

## One-time setup (about an hour)

1. **Create a GitHub account** (if you don't have one) at github.com.
2. **Create a new, empty repository** called `geology-rocks`.
   Public visibility (it's open source). Don't add a README or licence —
   this bundle already has them.
3. **Install Claude Code** on your computer, following Anthropic's official
   installation instructions (search "Claude Code install"). You'll also want
   `git` installed; Claude Code can help you with that.
4. **Unzip this bundle** into a folder, e.g. `Documents/geology-rocks`.
5. Open a terminal in that folder and start Claude Code (`claude`).
6. Paste the **M0 prompt** from `docs/PROMPTS.md`. Claude Code will set up git,
   connect to your GitHub repository, add licence texts and set up the
   automatic checks. It will explain anything it needs from you (for example,
   signing in to GitHub).

## The rhythm of each milestone

1. Open Claude Code in the project folder.
2. Paste the next milestone prompt from `docs/PROMPTS.md`.
3. Claude Code replies with a **plan in plain language**. Read it. Ask
   questions. Say "approved" or tell it what to change.
4. It builds, tests, and ends with a **milestone report**: what was built, how
   to try it, and a "what to try" checklist.
5. **Try it.** Follow the checklist. Tell Claude Code what felt wrong — in your
   own words, e.g. "the key asked about acid before asking if it's crystalline;
   that's the wrong order for a beginner".
6. **Review the geology** it lists as draft. Correct it directly in the YAML
   files (they're readable text) or tell Claude Code what to change. Only you
   mark content `approved`.
7. When you're happy, say "milestone complete — commit and push". Then move to
   the next prompt.

## How to tell if it's doing what you want

- **The scenario files** in `scenarios/` are your expert walkthroughs, like the
  Cornish granite example. They are automatic tests: if a change breaks one,
  the build fails. **Writing more scenarios is the single best way to steer the
  project.** Copy an existing one and change the answers and expected result.
- **The simulation report** (from milestone M2) shows which rocks the key
  confuses. Look for pairs that a geologist would separate easily — that means
  a character or probability is missing.
- **Specimen testing** (M3): key out real rocks and note where it went wrong.
- **The demos**: if something looks or reads wrong to you, it is wrong.

## Useful things to say to Claude Code

- "Explain that in plain language."
- "Show me what changed, without code."
- "Add a scenario for [rock] found at [place] with these observations: ..."
- "Why did the key suggest that question?"
- "Run all checks and tell me if anything is failing."
- "Update DECISIONS.md with what we just decided."
- Custom commands (type them in Claude Code): `/check-content`,
  `/add-rock <name>`, `/add-scenario <description>`, `/milestone-report`
  (defined in `.claude/commands/`)

## Your first review

Read `docs/SEED_CONTENT_NOTES.md`. It lists the draft geology content created
during the design chat, the checks already run, and a suggested review order.

## When to pause and ask a human expert

- Anything legal (collecting rules, licences you're unsure about).
- Data permissions from BGS (draft the email with Claude, send it yourself).
