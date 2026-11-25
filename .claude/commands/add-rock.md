---
description: Scaffold a new rock type (taxon) with all required fields
argument-hint: <rock name> [parent node id]
---

Add a new rock type called "$ARGUMENTS" to the taxonomy.

1. Read content/CLAUDE.md and docs/DATA_MODEL.md section 1.
2. Propose where it sits in the hierarchy (parent node and level) and explain
   why in one or two sentences. If a parent was given, check it is sensible.
   Wait for my confirmation.
3. Create the YAML file in the right folder under content/core/taxonomy/ with:
   id, level, parents, order, name, field_label, synonyms, tags,
   refs (bgs_rcs: TODO), page, characters (only the ones that differ from the
   parent — use inherit otherwise; leave out anything you're unsure of),
   review: {status: draft}.
4. Create a stub page in content/core/pages/ with TODO sections.
5. Run the content validator and the scenario runner; report results.
6. List everything you drafted so I can review it. Never mark it approved.
