# SPDX-FileCopyrightText: Geology Rocks contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Finding and reading content files."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

from .model import ERROR, WARNING, Doc, Finding

# Which schema applies to which files (glob relative to the repository root).
FILE_TYPES: list[tuple[str, str]] = [
    ("content/core/taxonomy/**/*.yaml", "taxon"),
    ("content/core/characters/*.yaml", "character"),
    ("content/core/minerals/*.yaml", "mineral"),
    ("content/core/kit/kit.yaml", "kit"),
    ("content/core/media/media.yaml", "media"),
    ("content/packs/*/manifest.yaml", "pack_manifest"),
    ("content/packs/*/crosswalk.yaml", "crosswalk"),
    ("content/packs/*/context.yaml", "context"),
    ("content/packs/*/named_units/*.yaml", "named_unit"),
    ("scenarios/*.yaml", "scenario"),
]


@dataclass
class Content:
    root: Path
    docs: dict[str, list[Doc]] = field(default_factory=dict)   # by file type
    # Files that loaded but broke the schema rules: not checked further, but
    # their IDs still count as existing, so one mistake gives one error.
    broken: list[Doc] = field(default_factory=list)
    pages: dict[str, tuple[Path, dict | None, str]] = field(default_factory=dict)
    files_checked: int = 0


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def load_yaml(root: Path, path: Path, findings: list[Finding]) -> Doc | None:
    text = path.read_text(encoding="utf-8")
    try:
        node = yaml.compose(text)
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        findings.append(Finding(
            ERROR, "Unreadable file", rel(root, path),
            mark.line + 1 if mark else None,
            f"This file is not valid YAML, so nothing in it could be checked "
            f"({getattr(exc, 'problem', None) or exc}). Often a missing space after ':' "
            f"or wrong indentation."))
        return None
    return Doc(path, rel(root, path), data, node)


def schema_validators(root: Path) -> dict[str, Draft202012Validator]:
    registry = Registry()
    schemas = {}
    for f in sorted((root / "schemas").glob("*.schema.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        registry = registry.with_resource(d["$id"], Resource.from_contents(d))
        schemas[f.name.removesuffix(".schema.json")] = d
    return {name: Draft202012Validator(s, registry=registry) for name, s in schemas.items()}


def _field_name(path) -> str:
    parts = [f"[{p + 1}]" if isinstance(p, int) else str(p) for p in path]
    return ".".join(parts).replace(".[", "[") or "(whole file)"


def focus(err):
    """Several shapes may be allowed (oneOf/anyOf). If one shape nearly fits
    (the problem is deeper inside), point at that deeper problem instead."""
    if err.validator in ("oneOf", "anyOf"):
        deeper = [e for e in err.context if len(e.absolute_path) > len(err.absolute_path)]
        if deeper:
            return focus(best_match(deeper))
    return err


def explain_schema_error(err) -> str:
    """Turn a (focused) jsonschema error into a plain-language sentence."""
    where = _field_name(err.absolute_path)
    if err.validator in ("oneOf", "anyOf"):
        if list(err.absolute_path)[:1] == ["characters"]:
            return f"{where}: should be 'inherit' or a set of state probabilities, found {err.instance!r}"
        return f"{where}: {err.instance!r} does not have an allowed form"
    v, val = err.validator, err.validator_value
    if v == "required":
        missing = err.message.split("'")[1] if "'" in err.message else err.message
        return f"{where}: required field '{missing}' is missing"
    if v == "additionalProperties":
        return f"{where}: {err.message.replace('Additional properties are not allowed', 'unknown field')} — check the spelling"
    if v == "enum":
        return f"{where}: '{err.instance}' is not allowed; use one of: {', '.join(map(str, val))}"
    if v == "const":
        return f"{where}: must be {val!r}, not {err.instance!r}"
    if v == "type":
        return f"{where}: should be {' or '.join(val) if isinstance(val, list) else val}, found {err.instance!r}"
    if v == "pattern":
        return f"{where}: '{err.instance}' is not in the expected format (pattern {val})"
    if v in ("minimum", "maximum"):
        return f"{where}: {err.instance} is {'below the minimum' if v == 'minimum' else 'above the maximum'} of {val}"
    if v in ("minItems", "maxItems", "minProperties", "minLength"):
        return f"{where}: {err.message}"
    return f"{where}: {err.message}"


def load_content(root: Path, findings: list[Finding]) -> Content:
    content = Content(root)
    validators = schema_validators(root)
    claimed: set[Path] = set()

    for pattern, ftype in FILE_TYPES:
        docs: list[Doc] = []
        for path in sorted(root.glob(pattern)):
            if ftype == "scenario" and path.name.startswith("_"):
                claimed.add(path)          # templates are not checked
                continue
            claimed.add(path)
            content.files_checked += 1
            doc = load_yaml(root, path, findings)
            if doc is None:
                continue
            errors = sorted((focus(e) for e in validators[ftype].iter_errors(doc.data)),
                            key=lambda e: list(map(str, e.absolute_path)))
            for err in errors:
                findings.append(Finding(ERROR, "Wrong structure", doc.rel,
                                        doc.line(*err.absolute_path), explain_schema_error(err)))
            if errors:
                content.broken.append(doc)  # deeper checks assume a well-formed file
                continue
            docs.append(doc)
        content.docs[ftype] = docs

    # Any other YAML file is probably misplaced.
    for base in ("content", "scenarios"):
        for path in sorted((root / base).rglob("*.y*ml")):
            if path not in claimed:
                findings.append(Finding(WARNING, "Unrecognised file", rel(root, path), None,
                                        "This YAML file is not in a known place, so it is not "
                                        "checked or used. Move or rename it (see content/CLAUDE.md)."))

    # Rock and mineral pages: Markdown with YAML front matter.
    for path in sorted((root / "content/core/pages").glob("*.md")):
        content.files_checked += 1
        text = path.read_text(encoding="utf-8")
        front = None
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) == 3:
                try:
                    front = yaml.safe_load(parts[1])
                except yaml.YAMLError:
                    front = None
        if not isinstance(front, dict):
            findings.append(Finding(ERROR, "Wrong structure", rel(root, path), 1,
                                    "Page must start with a front-matter block between '---' lines "
                                    "(id, taxon, review)."))
        content.pages[path.stem] = (path, front if isinstance(front, dict) else None, text)
    return content
