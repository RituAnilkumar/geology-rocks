# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""All content checks (docs/TESTING.md section 1).

Each check adds Findings to the Result. Errors make the check fail;
warnings are shown in the report but do not fail it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .loading import Content, load_content
from .model import ERROR, WARNING, Doc, Finding, Result
from .todos import collect_todos

TOLERANCE = 0.001
LEVELS = ["L0", "L1", "L2", "L3", "L4"]

# Free licences accepted for media and data (content/core/media/README.md,
# docs/CONTENT_GUIDE.md). Change only with a DECISIONS.md entry.
ALLOWED_LICENCES = {
    "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "OGL-UK-3.0", "ODbL-1.0",
    "LicenseRef-PublicDomain",
}

# Plain names for item types in the review table.
REVIEW_LABELS = {
    "taxon": "Rock types and groups (taxonomy)",
    "character": "Questions (characters)",
    "mineral": "Minerals",
    "media": "Pictures and media",
    "page": "Rock pages",
    "pack_manifest": "Pack manifest",
    "crosswalk": "Map unit crosswalk rows",
    "context": "Find context and clast suites",
    "named_unit": "Named units",
    "scenario": "Scenarios",
}


def is_todo(value: Any) -> bool:
    return isinstance(value, str) and "TODO" in value


class Checker:
    def __init__(self, content: Content, result: Result):
        self.c = content
        self.r = result
        self.taxa: dict[str, Doc] = {}
        self.chars: dict[str, Doc] = {}
        self.minerals: dict[str, Doc] = {}
        self.kit: set[str] = set()
        self.media_files: set[str] = set()
        self.children: dict[str, list[str]] = {}
        # IDs (and media files, pack folders) from files that failed the
        # structure check. They count as existing to avoid knock-on errors.
        self.known: set[str] = set()
        for d in content.broken:
            items = d.data if isinstance(d.data, list) else [d.data]
            for item in items:
                if isinstance(item, dict):
                    for key in ("id", "file"):
                        if isinstance(item.get(key), str):
                            self.known.add(item[key])
            self.known.add(d.rel)

    # -- helpers ---------------------------------------------------------
    def add(self, severity, kind, doc_or_file, line, message):
        file = doc_or_file.rel if isinstance(doc_or_file, Doc) else doc_or_file
        self.r.findings.append(Finding(severity, kind, file, line, message))

    def error(self, kind, doc, line, message):
        self.add(ERROR, kind, doc, line, message)

    def warn(self, kind, doc, line, message):
        self.add(WARNING, kind, doc, line, message)

    def char_label(self, cid: str) -> str:
        doc = self.chars.get(cid)
        q = doc.data["question"]["en"] if doc else None
        return f"{cid} (“{q}”)" if q else cid

    def state_ids(self, cid: str) -> list[str]:
        return [s["id"] for s in self.chars[cid].data["states"]]

    def exists(self, id_, table) -> bool:
        return id_ in table or id_ in self.known

    def docs(self, ftype) -> list[Doc]:
        return self.c.docs.get(ftype, [])

    # -- run -------------------------------------------------------------
    def run(self):
        self.index()
        self.check_characters()
        self.check_kit()
        self.check_media()
        self.check_taxonomy()
        self.check_matrix()
        self.check_minerals()
        self.check_pages()
        self.check_packs()
        self.check_scenarios()
        self.check_review()

    def index(self):
        """Collect all IDs and report duplicates."""
        seen: dict[str, str] = {}

        def register(id_, doc, line, table):
            if id_ in seen:
                self.error("Duplicate ID", doc, line,
                           f"ID '{id_}' is already used in {seen[id_]}. IDs must be unique.")
                return
            seen[id_] = doc.rel
            if table is not None:
                table[id_] = doc

        for d in self.docs("taxon"):
            register(d.data["id"], d, d.line("id"), self.taxa)
        for d in self.docs("character"):
            register(d.data["id"], d, d.line("id"), self.chars)
        for d in self.docs("mineral"):
            register(d.data["id"], d, d.line("id"), self.minerals)
        for d in self.docs("kit"):
            for i, item in enumerate(d.data):
                if item["id"] in self.kit:
                    self.error("Duplicate ID", d, d.line(i, "id"),
                               f"Kit item '{item['id']}' is listed twice.")
                self.kit.add(item["id"])
        for d in self.docs("media"):
            for i, m in enumerate(d.data):
                if m["file"] in self.media_files:
                    self.error("Duplicate ID", d, d.line(i, "file"),
                               f"Media file '{m['file']}' has two records.")
                self.media_files.add(m["file"])
        for t in self.taxa:
            self.children[t] = []
        for t, d in self.taxa.items():
            for p in d.data["parents"]:
                if p in self.children:
                    self.children[p].append(t)

    def check_media_ref(self, doc, line, ref, what):
        if ref is None or is_todo(ref):
            return
        if not self.exists(ref, self.media_files):
            self.error("Missing reference", doc, line,
                       f"{what} points to picture '{ref}', which has no record in "
                       f"content/core/media/media.yaml.")

    # -- characters ------------------------------------------------------
    def check_characters(self):
        for cid, d in self.chars.items():
            ids = [s["id"] for s in d.data["states"]]
            for dup in sorted({i for i in ids if ids.count(i) > 1}):
                self.error("Duplicate ID", d, d.line("states"),
                           f"Answer '{dup}' appears more than once in {cid}.")
            for i, k in enumerate(d.data.get("kit_required", [])):
                if not self.exists(k, self.kit):
                    self.error("Missing reference", d, d.line("kit_required", i),
                               f"Kit item '{k}' is not in content/core/kit/kit.yaml.")
            for i, s in enumerate(d.data["states"]):
                for fld, name in (("label", "label"), ("tells_you", "“what this tells you” text")):
                    if is_todo(s[fld]["en"]):
                        self.warn("Unfinished answer text", d, d.line("states", i, fld),
                                  f"Answer '{s['id']}' of {cid} has a TODO {name}.")
                self.check_media_ref(d, d.line("states", i, "hint_media"), s.get("hint_media"),
                                     f"Answer '{s['id']}' of {cid}")

    # -- kit -------------------------------------------------------------
    def check_kit(self):
        for d in self.docs("kit"):
            for i, item in enumerate(d.data):
                self.check_media_ref(d, d.line(i, "media"), item.get("media"),
                                     f"Kit item '{item['id']}'")

    # -- media -----------------------------------------------------------
    def check_media(self):
        media_dir = self.c.root / "content/core/media"
        for d in self.docs("media"):
            for i, m in enumerate(d.data):
                if not (media_dir / m["file"]).is_file():
                    self.error("Media", d, d.line(i, "file"),
                               f"Record for '{m['file']}' but the file does not exist.")
                if m["licence"] not in ALLOWED_LICENCES:
                    self.error("Media", d, d.line(i, "licence"),
                               f"'{m['file']}' has licence '{m['licence']}', which is not on the "
                               f"allowed list ({', '.join(sorted(ALLOWED_LICENCES))}).")
                for fld in ("author", "source"):
                    if not str(m[fld]).strip() or is_todo(m[fld]):
                        self.error("Media", d, d.line(i, fld),
                                   f"'{m['file']}' needs a real {fld} before it can be used.")
        if media_dir.is_dir():
            for path in sorted(media_dir.rglob("*")):
                if not path.is_file() or path.suffix in (".md", ".yaml", ".license"):
                    continue
                name = path.relative_to(media_dir).as_posix()
                if name not in self.media_files:
                    self.error("Media", path.relative_to(self.c.root).as_posix(), None,
                               "This picture has no record in media.yaml (licence, author, "
                               "source, alt text). Every media file needs one.")

    # -- taxonomy --------------------------------------------------------
    def check_taxonomy(self):
        for tid, d in self.taxa.items():
            level = LEVELS.index(d.data["level"])
            parents = d.data["parents"]
            if level == 0 and parents:
                self.error("Taxonomy", d, d.line("parents"),
                           f"{tid} is a top-level (L0) group, so it cannot have parents.")
            if level > 0 and not parents:
                self.error("Taxonomy", d, d.line("parents"),
                           f"{tid} is at level {d.data['level']} but has no parent.")
            for i, p in enumerate(parents):
                if not self.exists(p, self.taxa):
                    self.error("Missing reference", d, d.line("parents", i),
                               f"Parent '{p}' of {tid} does not exist.")
                    continue
                if p not in self.taxa:      # parent file has its own structure error
                    continue
                plevel = LEVELS.index(self.taxa[p].data["level"])
                if plevel != level - 1:
                    self.error("Taxonomy", d, d.line("level"),
                               f"{tid} is at level {d.data['level']} but its parent {p} is at "
                               f"{self.taxa[p].data['level']}; a child must be exactly one level below.")
            rb = d.data.get("replaced_by")
            if rb and not self.exists(rb, self.taxa):
                self.error("Missing reference", d, d.line("replaced_by"),
                           f"replaced_by points to '{rb}', which does not exist.")
            if rb and not d.data.get("deprecated"):
                self.warn("Taxonomy", d, d.line("replaced_by"),
                          f"{tid} has replaced_by but is not marked deprecated: true.")

        # Cycles and reaching a root.
        state: dict[str, int] = {}          # 1 = visiting, 2 = done
        in_cycle: set[str] = set()

        def visit(t, stack):
            state[t] = 1
            stack.append(t)
            for p in self.taxa[t].data["parents"]:
                if p not in self.taxa:
                    continue
                if state.get(p) == 1:
                    cycle = stack[stack.index(p):] + [p]
                    if not in_cycle.intersection(cycle):
                        self.error("Taxonomy", self.taxa[t], self.taxa[t].line("parents"),
                                   "Circular parents: " + " → ".join(cycle) +
                                   ". A rock cannot be its own ancestor.")
                    in_cycle.update(cycle)
                elif state.get(p) is None:
                    visit(p, stack)
            stack.pop()
            state[t] = 2

        for t in sorted(self.taxa):
            if t not in state:
                visit(t, [])

        reaches: dict[str, bool] = {}

        def reaches_root(t, seen=()):
            if t in reaches:
                return reaches[t]
            if t in seen:
                return False
            if t not in self.taxa:
                return t in self.known      # broken file: don't add a knock-on error
            d = self.taxa[t]
            if d.data["level"] == "L0" and not d.data["parents"]:
                ok = True
            else:
                ok = any(reaches_root(p, seen + (t,)) for p in d.data["parents"])
            reaches[t] = ok
            return ok

        for t, d in sorted(self.taxa.items()):
            if t not in in_cycle and not reaches_root(t):
                self.error("Taxonomy", d, d.line("parents"),
                           f"{t} does not connect up to a top-level (L0) group.")

    # -- matrix ----------------------------------------------------------
    def resolved(self, tid: str, cid: str, seen=()) -> dict | None:
        """Probabilities for (taxon, character) after following 'inherit'."""
        if tid in seen or tid not in self.taxa:
            return None
        val = (self.taxa[tid].data.get("characters") or {}).get(cid)
        if isinstance(val, dict):
            return val
        if val == "inherit":
            for p in self.taxa[tid].data["parents"]:
                got = self.resolved_any(p, cid, seen + (tid,))
                if got is not None:
                    return got
        return None

    def resolved_any(self, tid, cid, seen):
        """Like resolved(), but a parent that doesn't list the character
        passes the question further up (values set high in the tree)."""
        if tid in seen or tid not in self.taxa:
            return None
        val = (self.taxa[tid].data.get("characters") or {}).get(cid)
        if val is not None:
            return self.resolved(tid, cid, seen)
        for p in self.taxa[tid].data["parents"]:
            got = self.resolved_any(p, cid, seen + (tid,))
            if got is not None:
                return got
        return None

    def ancestor_broken(self, tid, seen=()) -> bool:
        if tid in seen:
            return False
        if tid not in self.taxa:
            return tid in self.known
        return any(self.ancestor_broken(p, seen + (tid,)) for p in self.taxa[tid].data["parents"])

    def check_matrix(self):
        for tid, d in sorted(self.taxa.items()):
            for cid, vals in (d.data.get("characters") or {}).items():
                line = d.line("characters", cid)
                if cid not in self.chars:
                    if cid not in self.known:
                        self.error("Missing reference", d, line,
                                   f"Question '{cid}' does not exist in content/core/characters/.")
                    continue
                if vals == "inherit":
                    parents = d.data["parents"]
                    found = [self.resolved_any(p, cid, (tid,)) for p in parents]
                    found = [f for f in found if f is not None]
                    if not found and not self.ancestor_broken(tid):
                        self.error("Probabilities", d, line,
                                   f"{self.char_label(cid)} says 'inherit', but no parent group "
                                   f"has values to inherit.")
                    elif len(found) > 1 and any(f != found[0] for f in found[1:]):
                        self.warn("Probabilities", d, line,
                                  f"{tid} has two parents with different values for "
                                  f"{self.char_label(cid)}; 'inherit' will use the first "
                                  f"({parents[0]}). Consider giving explicit values.")
                    continue
                valid = set(self.state_ids(cid))
                for sid, p in vals.items():
                    if sid not in valid:
                        self.error("Missing reference", d, d.line("characters", cid, sid),
                                   f"'{sid}' is not an answer of {self.char_label(cid)}. "
                                   f"Allowed: {', '.join(sorted(valid))}.")
                    elif p in (0, 1):
                        self.warn("Probabilities", d, d.line("characters", cid, sid),
                                  f"{tid}: '{sid}' for {cid} is exactly {p}. The content guide "
                                  f"suggests 0.01–0.99 so the key stays honest about variation.")
                if self.chars[cid].data["kind"] == "single":
                    total = sum(vals.values())
                    if abs(total - 1) > TOLERANCE:
                        self.error("Probabilities", d, line,
                                   f"Probabilities for {self.char_label(cid)} add up to "
                                   f"{round(total, 4)}, not 1.")

    # -- minerals --------------------------------------------------------
    def check_minerals(self):
        for mid, d in self.minerals.items():
            for i, la in enumerate(d.data.get("look_alikes", [])):
                if not self.exists(la["id"], self.minerals):
                    self.error("Missing reference", d, d.line("look_alikes", i, "id"),
                               f"Look-alike '{la['id']}' is not a mineral in content/core/minerals/.")
            for i, ind in enumerate(d.data.get("indicates", [])):
                if not self.exists(ind["taxon"], self.taxa):
                    self.error("Missing reference", d, d.line("indicates", i, "taxon"),
                               f"'{ind['taxon']}' is not a rock type or group.")
            for i, ref in enumerate(d.data.get("hint_media", [])):
                self.check_media_ref(d, d.line("hint_media", i), ref, f"Mineral {mid}")
            hm = d.data["properties"].get("hardness_mohs")
            if hm and hm[0] > hm[1]:
                self.error("Minerals", d, d.line("properties", "hardness_mohs"),
                           f"Hardness range {hm} has the lower value second.")

    # -- pages -----------------------------------------------------------
    def check_pages(self):
        root = self.c.root
        for stem, (path, front, _text) in sorted(self.c.pages.items()):
            relp = path.relative_to(root).as_posix()
            if front is None:
                continue
            if front.get("id") != stem:
                self.error("Pages", relp, 2, f"Front matter id is '{front.get('id')}' but the "
                                             f"file is called {stem}.md; they must match.")
            t = front.get("taxon")
            if t and not self.exists(t, self.taxa):
                self.error("Missing reference", relp, 3, f"Page is about '{t}', which does not exist.")
            rv = front.get("review")
            if not isinstance(rv, dict) or rv.get("status") not in ("draft", "in_review", "approved"):
                self.error("Pages", relp, 4, "Page needs a review block with status "
                                             "draft, in_review or approved.")
        for tid, d in sorted(self.taxa.items()):
            page = d.data.get("page")
            if page and not is_todo(page) and page not in self.c.pages:
                self.warn("Rock page not yet written", d, d.line("page"),
                          f"{tid} links to page '{page}', but content/core/pages/{page}.md "
                          f"doesn't exist yet.")

    # -- packs -----------------------------------------------------------
    def check_packs(self):
        packs: dict[str, dict[str, Any]] = {}
        for ftype in ("pack_manifest", "crosswalk", "context", "named_unit"):
            for d in self.docs(ftype):
                pack_id = Path(d.rel).parts[2]
                packs.setdefault(pack_id, {"named_unit": []})
                if ftype == "named_unit":
                    packs[pack_id]["named_unit"].append(d)
                else:
                    packs[pack_id][ftype] = d
        self.packs = packs

        for pack_id, p in sorted(packs.items()):
            pack_dir = self.c.root / "content/packs" / pack_id
            units = {d.data["id"]: d for d in p["named_unit"]}
            m = p.get("pack_manifest")
            if m is None and f"content/packs/{pack_id}/manifest.yaml" not in self.known:
                self.error("Packs", f"content/packs/{pack_id}", None,
                           "This pack has no manifest.yaml (or it failed to load).")
            elif m is not None:
                self.check_manifest(pack_id, m)
            if "crosswalk" in p:
                self.check_crosswalk(p["crosswalk"], units)
            if "context" in p:
                self.check_context(p["context"])
            for uid, d in sorted(units.items()):
                pt = d.data["parent_taxon"]
                if not self.exists(pt, self.taxa):
                    self.error("Missing reference", d, d.line("parent_taxon"),
                               f"Parent rock type '{pt}' does not exist.")
                po = d.data.get("part_of")
                if po and not self.exists(po, units):
                    self.error("Missing reference", d, d.line("part_of"),
                               f"part_of points to '{po}', which is not a named unit in this pack.")
                story = d.data.get("story")
                if story and not is_todo(story) and not (pack_dir / story).is_file():
                    self.warn("Story not yet written", d, d.line("story"),
                              f"Story file '{story}' doesn't exist yet in this pack.")
                age = d.data.get("age") or {}
                lo, hi = age.get("ma_min"), age.get("ma_max")
                if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo > hi:
                    self.error("Packs", d, d.line("age"),
                               f"Age range is back to front: ma_min {lo} is larger than ma_max {hi}.")

    def check_manifest(self, pack_id, m):
        data = m.data
        if data["id"] != pack_id:
            self.error("Packs", m, m.line("id"),
                       f"Pack id '{data['id']}' must match its folder name '{pack_id}'.")
        for i, t in enumerate(data.get("taxa_present", [])):
            if not self.exists(t, self.taxa):
                self.error("Missing reference", m, m.line("taxa_present", i),
                           f"'{t}' is listed as present but is not a rock type.")
        sources = {s["id"]: s for s in data["sources"]}
        for i, s in enumerate(data["sources"]):
            if s["licence"] not in ALLOWED_LICENCES:
                self.warn("Pack source licence", m, m.line("sources", i, "licence"),
                          f"Source '{s['id']}' has licence '{s['licence']}', which is not on the "
                          f"standard allowed list. Check the terms before release.")
        for kind in ("offline", "online"):
            for i, layer in enumerate(data["layers"].get(kind, [])):
                src = layer["source"]
                if src not in sources and src != "derived":
                    self.error("Missing reference", m, m.line("layers", kind, i, "source"),
                               f"Layer '{layer['id']}' uses source '{src}', which is not listed "
                               f"under sources. Every source needs its licence recorded.")

    def check_crosswalk(self, d, units):
        seen = set()
        for i, row in enumerate(d.data):
            if row["map_unit"] in seen:
                self.error("Duplicate ID", d, d.line(i, "map_unit"),
                           f"Map unit '{row['map_unit']}' appears twice.")
            seen.add(row["map_unit"])
            for t in row["taxa"]:
                if not self.exists(t, self.taxa):
                    self.error("Missing reference", d, d.line(i, "taxa", t),
                               f"'{t}' is not a rock type or group.")
            total = sum(row["taxa"].values())
            if abs(total - 1) > TOLERANCE:
                self.error("Probabilities", d, d.line(i, "taxa"),
                           f"Rock probabilities for map unit '{row['map_unit']}' add up to "
                           f"{round(total, 4)}, not 1.")
            nu = row.get("named_unit")
            if nu and not self.exists(nu, units):
                self.error("Missing reference", d, d.line(i, "named_unit"),
                           f"Named unit '{nu}' is not in this pack's named_units/.")

    def check_context(self, d):
        for name, c in d.data["contexts"].items():
            total = c["local"] + c["transported"] + c["human"]
            if abs(total - 1) > TOLERANCE:
                self.error("Probabilities", d, d.line("contexts", name),
                           f"Find context '{name}': local + transported + human = "
                           f"{round(total, 4)}, not 1.")
        hm = d.data.get("human_made") or {}
        for t in hm:
            if not self.exists(t, self.taxa):
                self.error("Missing reference", d, d.line("human_made", t),
                           f"'{t}' is not a rock type or group.")
        if hm and abs(sum(hm.values()) - 1) > TOLERANCE:
            self.error("Probabilities", d, d.line("human_made"),
                       f"human_made probabilities add up to {round(sum(hm.values()), 4)}, not 1.")
        for i, suite in enumerate(d.data.get("clast_suites", [])):
            for t in suite["taxa"]:
                if not self.exists(t, self.taxa):
                    self.error("Missing reference", d, d.line("clast_suites", i, "taxa", t),
                               f"'{t}' is not a rock type or group.")
            total = sum(suite["taxa"].values())
            if total > 1 + TOLERANCE:
                self.error("Probabilities", d, d.line("clast_suites", i, "taxa"),
                           f"Clast suite '{suite['zone']}' adds up to {round(total, 4)}, "
                           f"more than 1.")

    # -- scenarios -------------------------------------------------------
    def check_scenarios(self):
        contexts_by_pack = {
            pid: set(p["context"].data["contexts"]) for pid, p in self.packs.items() if "context" in p
        }
        all_contexts = set().union(*contexts_by_pack.values()) if contexts_by_pack else set()
        for d in self.docs("scenario"):
            setup = d.data["setup"]
            pack = setup.get("pack")
            if pack and pack not in self.packs and \
                    f"content/packs/{pack}/manifest.yaml" not in self.known:
                self.error("Missing reference", d, d.line("setup", "pack"),
                           f"Pack '{pack}' does not exist in content/packs/.")
            fc = setup.get("find_context")
            context_broken = any(k.endswith("/context.yaml") for k in self.known)
            if fc and not context_broken:
                allowed = contexts_by_pack.get(pack, set()) if pack else all_contexts
                if fc not in allowed:
                    self.error("Missing reference", d, d.line("setup", "find_context"),
                               f"Find context '{fc}' is not defined. Known: {', '.join(sorted(allowed))}.")
            for i, k in enumerate(setup.get("kit", [])):
                if not self.exists(k, self.kit):
                    self.error("Missing reference", d, d.line("setup", "kit", i),
                               f"Kit item '{k}' is not in content/core/kit/kit.yaml.")
            for t in (setup.get("explicit_prior") or {}):
                self.need_taxon(d, d.line("setup", "explicit_prior", t), t)
            for i, step in enumerate(d.data["steps"]):
                ans = step.get("answer")
                if ans:
                    self.check_answer(d, i, ans)
                for key, val in (step.get("expect") or {}).items():
                    line = d.line("steps", i, "expect", key)
                    if key in ("reported_node_is", "reported_node_is_ancestor_of", "top_leaf_is"):
                        self.need_taxon(d, line, val)
                    elif key == "top_leaf_in":
                        for t in val:
                            self.need_taxon(d, line, t)
                    elif key in ("p_at_least", "p_at_most"):
                        for t in val:
                            self.need_taxon(d, line, t)
                    elif key in ("not_suggested", "suggested_first_in"):
                        for c in val:
                            if not self.exists(c, self.chars):
                                self.error("Missing reference", d, line, f"Question '{c}' does not exist.")
                    elif key == "reported_level_at_least" and val not in LEVELS:
                        self.error("Scenarios", d, line, f"'{val}' is not a level (L0–L4).")

    def need_taxon(self, d, line, t):
        if not self.exists(t, self.taxa):
            self.error("Missing reference", d, line, f"'{t}' is not a rock type or group.")

    def check_answer(self, d, i, ans):
        cid = ans["char"]
        line = d.line("steps", i, "answer")
        if cid not in self.chars:
            if cid not in self.known:
                self.error("Missing reference", d, line, f"Question '{cid}' does not exist.")
            return
        states = ans["state"] if isinstance(ans["state"], list) else [ans["state"]]
        valid = set(self.state_ids(cid))
        for s in states:
            if s not in valid:
                self.error("Missing reference", d, line,
                           f"'{s}' is not an answer of {self.char_label(cid)}. "
                           f"Allowed: {', '.join(sorted(valid))}.")
        if isinstance(ans["state"], list) and self.chars[cid].data["kind"] == "single":
            self.error("Scenarios", d, line,
                       f"{cid} allows only one answer, but a list was given.")

    # -- review status ---------------------------------------------------
    def check_review(self):
        def count(ftype, doc, line_keys, review):
            status = review["status"]
            self.r.review_counts[REVIEW_LABELS[ftype]][status] += 1
            if status == "approved" and not (review.get("reviewer") and review.get("date")):
                self.error("Review", doc, doc.line(*line_keys),
                           "Marked approved but the reviewer's name or the date is missing.")

        for ftype, docs in self.c.docs.items():
            for d in docs:
                if isinstance(d.data, list):
                    for i, item in enumerate(d.data):
                        if "review" in item:
                            count(ftype, d, (i, "review"), item["review"])
                    continue
                if "review" in d.data:
                    count(ftype, d, ("review",), d.data["review"])
                if ftype == "context":
                    for i, s in enumerate(d.data.get("clast_suites", [])):
                        if "review" in s:
                            count(ftype, d, ("clast_suites", i, "review"), s["review"])
        for stem, (path, front, _t) in self.c.pages.items():
            rv = (front or {}).get("review")
            if isinstance(rv, dict) and rv.get("status") in ("draft", "in_review", "approved"):
                self.r.review_counts[REVIEW_LABELS["page"]][rv["status"]] += 1
                if rv["status"] == "approved" and not (rv.get("reviewer") and rv.get("date")):
                    self.error("Review", path.relative_to(self.c.root).as_posix(), 4,
                               "Marked approved but the reviewer's name or the date is missing.")


def validate(root: Path) -> Result:
    """Run every check on the repository at root and return the result."""
    root = Path(root).resolve()
    result = Result()
    content = load_content(root, result.findings)
    result.files_checked = content.files_checked
    Checker(content, result).run()
    result.todos = collect_todos(content, result.findings)
    return result
