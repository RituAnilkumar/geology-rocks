# app/ — rules for the Android app (Phase 1 onwards)

Do not start this folder until milestones M0–M3 are complete (see ROADMAP).

## Stack

Kotlin, Jetpack Compose, Room (reads the compiled core and pack SQLite files),
MapLibre Native Android with PMTiles for offline maps. Gradle build that
F-Droid can reproduce. No Google Play Services or proprietary dependencies.

## Product rules

- **Offline-first**: the key, pages, notebook and downloaded packs work with no
  network. Online WMS layers are optional and clearly labelled.
- **Maps**: OSM vector basemap; style must not render boundary layers. Basic
  basemap = water, land cover, major place names only. Detailed layer (roads,
  paths, minor places) is an optional download, offered when starting a walk.
- **Key UI** (see `docs/PROJECT_SPEC.md` §6): one question per screen with
  picture answers + "Not sure" + "Skip"; full question list for multi-access;
  swipe-up candidates panel with live probabilities and editable answer path;
  result shown at the reported hierarchy level with path, inferred named unit,
  story, collecting status and "Save to notebook".
- **Beginner / expert mode**: beginner reports at L2–L3 by default; expert shows
  L4 and the full probability spread.
- **Review status**: content with `draft` status shows a small "draft" badge in
  debug builds and is excluded from release builds unless a build flag allows it.
- **Accessibility**: every image has alt text from content; minimum touch target
  48dp; works with TalkBack; respects system font size; colour is never the only
  signal.
- **Privacy**: notebook stored locally only; export via Android share sheet;
  option to strip or round coordinates on export. No network calls except pack
  downloads and optional WMS, both user-initiated.
- **Localisation**: all strings come from content text keys or Android string
  resources; en-GB default.

## Testing

Unit tests for the Kotlin engine against `scenarios/`; Compose UI tests for the
key flow; screenshot tests for main screens. Every milestone produces a debug
APK with step-by-step install instructions for Ritu.
