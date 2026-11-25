# Content guide (for geologists and contributors)

## Writing "what this tells you"

Each answer state has a `tells_you` sentence. It explains what the observation
*means geologically*, not just what it is.

- One or two sentences, plain English, no unexplained jargon.
- Say what it suggests **and** what it doesn't rule out.
- Good: "Big, interlocking crystals need slow cooling, usually deep
  underground. Some metamorphic rocks look similar, so check for layering next."
- Avoid: "Phaneritic texture indicates plutonic origin."

## Setting probabilities (the matrix)

For each rock type and character, ask: "Out of 100 typical hand specimens of
this rock that a hobbyist might pick up, how many would show each state?"

- Think about **real field specimens**, including weathered ones.
- Avoid 0 and 1; use 0.01 for "very rare" and 0.99 for "almost always".
- Set values on the **highest sensible node** (e.g. felsic plutonic) and use
  `inherit` below, overriding only where a child differs.
- Leave a character out if it genuinely doesn't help for that rock —
  don't guess.
- Write your reasoning in `review.notes` if a value is debatable.

## Classification references

Follow, in simplified field-usable form:
- BGS Rock Classification Scheme (overall names, structure)
- IUGS (igneous via simplified QAPF; metamorphic)
- Folk and Dunham (carbonates), Wentworth (grain size)

Where a precise name needs chemistry or a thin section, use a field label
(e.g. "fine-grained intermediate volcanic rock (andesite-like)").

## Photo protocol (hint images and reference specimens)

- Fresh, broken surface where possible; also a weathered surface if typical.
- Scale card with colour patches in frame (field card).
- Diffuse daylight or a daylight lamp; no flash glare.
- Set: (1) whole specimen, (2) close-up of texture, (3) hand-lens macro,
  (4) wet surface. Optional: (5) in situ outcrop.
- Record: specimen ID, collection (if any), locality (can be coarse), rock
  type, who identified it.
- Files: JPEG/PNG originals kept by the contributor; the repo stores WebP
  (pipeline converts). Max long edge 1600 px for hints.

## Licensing your contribution

Your own photos and text: CC BY-SA 4.0. Third-party: free licences only (CC0,
CC BY, CC BY-SA, OGL, ODbL, public domain) — record source URL, author and
licence. No NC or ND material.

## Review

Everything starts as `draft`. A reviewer sets `approved` with their name and
date. Draft content does not appear in release builds.

## Learn stories

- Short chapters (150–300 words), each anchored to an age range and to rocks
  you can actually find in the area.
- Distinguish clearly between well-established interpretation and debate.
- Link to sites where people can see the rocks legally and safely.
- Cite sources in the file's `sources:` list (for reviewers; not shown in full
  in the app).
