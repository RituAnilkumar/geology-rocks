# Contributing to Geology Rocks

Thank you! This project needs geologists, photographers, illustrators,
translators, testers and developers.

## Ways to help

- **Geology content**: rock and mineral descriptions, "what this tells you"
  explanations, state probabilities, local geological stories, walks. See
  `docs/CONTENT_GUIDE.md`.
- **Photos and drawings**: hint images and reference specimens. Follow the photo
  protocol in `docs/CONTENT_GUIDE.md`. You must own the image (or it must be
  under a free licence) and agree to license it CC BY-SA 4.0.
- **Field testing**: try the key on real specimens and report where it goes
  wrong (include your answers — the app's notebook export does this for you).
- **Translations** (later, via Weblate).
- **Code**: see `CLAUDE.md` and `docs/ARCHITECTURE.md`.

## Checking your changes

Before committing content, run the content checker from the project folder:

```
./check-content
```

It prints a short result and writes a full report to
`reports/content-report.md` (errors, warnings, review status and TODOs).
Errors must be fixed; warnings and TODOs are listed for information.

Other commands (each rebuilds from the current content first):

| Command | What it does |
|---|---|
| `./run-key` | Opens the key prototype in your browser (Ctrl+C in the terminal stops it) |
| `./run-scenarios` | Plays every scenario in `scenarios/` and says which pass or fail |
| `./run-simulation` | Writes `reports/simulation-report.md` and confusion tables (CSV) | The same
check runs automatically on GitHub for every push, and the report appears on
the run's summary page. Developers can add `--tests` to also run the
checker's own tests.

## Review process

All geology content starts as `draft`. A named reviewer checks it and sets
`review: {status: approved, reviewer: <name>, date: <date>}`. Draft content is
hidden from release builds.

## Licensing of contributions

- Code: GPL-3.0-or-later.
- Content and media you create: CC BY-SA 4.0.
- Third-party material: only free licences (CC0, CC BY, CC BY-SA, OGL, ODbL,
  public domain). No NC or ND. Record the source, author and licence.

## Conduct

Be kind, be constructive, credit others. See `CODE_OF_CONDUCT.md`.
