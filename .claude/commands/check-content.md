---
description: Run all content and licence checks and summarise in plain language
---

Run every check available at this stage of the project:
`reuse lint`, the content validator, engine tests, the scenario runner and the
simulation report (whichever exist yet).

Then give me a plain-language summary:
- Overall: all good / problems found
- Errors (must fix), with file and a one-line explanation each
- Warnings and TODOs, grouped by type
- Review status counts (draft / in_review / approved)
- Scenario results, and for any failure: what the engine concluded vs what
  the scenario expected
- The five most-confused rock pairs from the simulation, if available

Don't change any geology content. Suggest fixes and wait for my decision.
