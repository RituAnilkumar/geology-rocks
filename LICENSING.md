# Licensing — plain-English summary

Geology Rocks is free and open source (FLOSS) throughout.

| What | Licence | What it means |
|---|---|---|
| App code, pipeline, engine | **GPL-3.0-or-later** | Anyone may use, study, change and share it. Anyone who distributes a modified version must publish its full source under the same licence. |
| Identification data (taxonomy, characters, matrix) | **CC BY-SA 4.0** | Free to reuse with credit; adaptations must be shared under the same licence. |
| Our own photos, drawings, explanations, stories, field card | **CC BY-SA 4.0** | As above. |
| Third-party material (e.g. BGS data, OpenStreetMap, Wikimedia images) | **Its own licence** | Recorded file by file. Only free licences are accepted (no "non-commercial" or "no-derivatives" terms). |

## How licences are recorded

We follow the [REUSE specification](https://reuse.software): every file states
its copyright and licence, either in a header, in a `<file>.license` companion
file, or via `REUSE.toml`. Full licence texts live in `LICENSES/`. CI runs
`reuse lint` and fails if anything is missing. The app's credits screen is
generated from the same information.

## Contributions

By contributing code you agree it is licensed GPL-3.0-or-later; by contributing
content or media you agree it is licensed CC BY-SA 4.0 (or you state another
free licence for third-party material you have the right to share). See
`CONTRIBUTING.md`.

## Required attributions (examples, kept up to date by the pipeline)

- Contains British Geological Survey materials © UKRI [year].
- Map data © OpenStreetMap contributors (ODbL).

This summary is not legal advice; the licence texts in `LICENSES/` are authoritative.
