#!/usr/bin/env python3
"""Check that every research document follows the structure AGENTS.md fixes.

Every agent's document under `collectors/research/` and `analyzer/research/`
(not the two README indexes and not `collectors/research/frameworks.md`) has
one H1 equal to the agent's catalog name, one unheaded intro paragraph, then
the numbered sections of its directory's outline in order, each with the
fixed subsections AGENTS.md names (the "Research document structure"
subsection of "Validating catalog entries from source"). This checks, for
each such file:

- the H1 is `# <agent>` where `<agent>` is the file's stem;
- the H2 headings are exactly the outline's, in order, with their numbers;
- the fixed H3 subsections sit under the right H2 (`### Observed` and
  `### Source reviews` under section 1; `### Scratch directories` under the
  collector document's section 2; `### What survives a delete` under the
  analyzer document's section 2; the eight requirement-class subsections,
  in order, before any other H3 of the analyzer document's section 8);
- no bold label stands in for a heading: a paragraph may not open with
  `**Label**` or `**Label.**` or `**Label:**` followed by prose (a list
  item or table row may);
- no prose line is longer than `--width` characters (default 100) unless it
  carries a URL, since a citation link cannot be wrapped.

With `--before DIR`, where DIR holds the `collectors/` and `analyzer/`
trees of the documents as they were before a rewrite, it also reports every
citation URL, code span, fenced-block line, number and bold label that the
old document holds and the new one lacks, as `path: lost <kind>: <text>`.
A rewrite that merges a repeated statement loses nothing; a rewrite that
drops a file name, a key, a size or a citation shows up here.

Usage: tools/check_research_structure.py [--before DIR] [--width N] [FILE...]

Every failure is printed as `path[:line]: message`; the exit status is 1
when any check failed.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = {"README.md", "frameworks.md"}

COLLECTOR_H2 = (
    "1. Source and evidence",
    "2. Per-user storage",
    "3. Credentials",
    "4. Exclusions",
    "5. Project-local files",
    "6. Where the project path is recorded",
    "7. Confidence",
)
ANALYZER_H2 = (
    "1. Source and evidence",
    "2. Transcript stores",
    "3. Record schema",
    "4. Joins and timestamps",
    "5. Other stores",
    "6. Format versions",
    "7. Secrets",
    "8. Parser plan",
)
PLAN_H3 = (
    "Permission state",
    "Model",
    "Past use and secondary sources",
    "Sync, relay and origin",
    "Scratch directories",
    "Deletion",
    "Bad lines",
    "Fixtures",
)
# Fixed H3s per directory, keyed by the section number they sit under.
COLLECTOR_H3 = {1: ("Observed", "Source reviews"), 2: ("Scratch directories",)}
ANALYZER_H3 = {1: ("Observed", "Source reviews"), 2: ("What survives a delete",), 8: PLAN_H3}

ATX = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BOLD_LEAD = re.compile(r"^\*\*[^*]+\*\*[.:]?(\s|$)")
URL = re.compile(r"https?://[^\s)\]>]+")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
BOLD = re.compile(r"\*\*([^*\n]+)\*\*")
NUMBER = re.compile(r"(?<![\w/.-])\d[\d,.]*(?:\s?(?:[KMGT]i?B|B|bytes|ms|s|%))?(?![\w/.-])")


def load_link_check():
    """Import tools/check_doc_links.py, the oracle for fences and headings."""
    path = ROOT / "tools" / "check_doc_links.py"
    spec = importlib.util.spec_from_file_location("check_doc_links", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def research_files() -> list[pathlib.Path]:
    files = []
    for part in ("collectors", "analyzer"):
        files += sorted((ROOT / part / "research").glob("*.md"))
    return [f for f in files if f.name not in SKIP]


def kind_of(path: pathlib.Path) -> str | None:
    parts = path.resolve().parts
    if "research" not in parts or path.name in SKIP:
        return None
    idx = parts.index("research")
    return parts[idx - 1] if idx > 0 and parts[idx - 1] in ("collectors", "analyzer") else None


def headings(text: str) -> list[tuple[int, int, str]]:
    """(line number, level, text) of every ATX heading outside fences."""
    found = []
    for n, line in enumerate(text.split("\n"), 1):
        m = ATX.match(line)
        if m:
            found.append((n, len(m.group(1)), m.group(2).strip()))
    return found


def check_structure(path: pathlib.Path, text: str, width: int, link_check) -> list[str]:
    kind = kind_of(path)
    if kind is None:
        return []
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    problems: list[str] = []
    stripped = link_check.strip_fences(text)
    heads = headings(stripped)
    h1 = [h for h in heads if h[1] == 1]
    if len(h1) != 1 or h1[0][2] != path.stem:
        problems.append("%s:%d: H1 must be `# %s`" % (rel, h1[0][0] if h1 else 1, path.stem))
    want_h2 = COLLECTOR_H2 if kind == "collectors" else ANALYZER_H2
    want_h3 = COLLECTOR_H3 if kind == "collectors" else ANALYZER_H3
    h2 = [h for h in heads if h[1] == 2]
    if [h[2] for h in h2] != list(want_h2):
        problems.append(
            "%s: H2 headings must be, in order: %s; found: %s"
            % (rel, " | ".join(want_h2), " | ".join(h[2] for h in h2) or "none")
        )
    # H3s grouped under the H2 that precedes them.
    section = 0
    under: dict[int, list[str]] = {}
    for _, level, title in heads:
        if level == 2:
            section = int(title.split(".", 1)[0]) if title[:1].isdigit() else 0
        elif level == 3:
            under.setdefault(section, []).append(title)
    for num, fixed in want_h3.items():
        have = under.get(num, [])
        missing = [t for t in fixed if t not in have]
        if missing:
            problems.append(
                "%s: section %d lacks the fixed subsection(s): %s" % (rel, num, ", ".join(missing))
            )
        elif len(fixed) > 1 and [t for t in have if t in fixed] != list(fixed):
            problems.append(
                "%s: section %d fixed subsections out of order; want %s"
                % (rel, num, ", ".join(fixed))
            )
        elif num == 8 and have[: len(fixed)] != list(fixed):
            problems.append(
                "%s: section 8's eight fixed subsections must come before any other H3" % rel
            )
    first_h2 = next((h[0] for h in h2), None)
    lines = stripped.split("\n")
    prev_blank = True
    for n, line in enumerate(lines, 1):
        in_prose = line.strip() and not line.lstrip().startswith(("|", "-", "*", ">", "#", "["))
        if prev_blank and in_prose and BOLD_LEAD.match(line):
            problems.append("%s:%d: bold label used as a heading; make it a `###`" % (rel, n))
        long = in_prose and not line.lstrip()[:2].rstrip(".").isdigit() and len(line) > width
        if long and not URL.search(line):
            problems.append("%s:%d: prose line longer than %d characters" % (rel, n, width))
        prev_blank = not line.strip()
    if first_h2 is not None and h1:
        intro = [x for x in lines[h1[0][0] : first_h2 - 1] if x.strip()]
        if not intro:
            problems.append("%s: no intro paragraph between the H1 and section 1" % rel)
    return problems


def tokens(text: str, link_check) -> dict[str, set[str]]:
    """The facts a rewrite must keep: URLs, code spans, fenced lines, numbers, bold labels."""
    fenced: set[str] = set()
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence and line.strip():
            fenced.add(line.strip())
    prose = link_check.strip_fences(text)
    return {
        "url": {u.rstrip(".,;:") for u in URL.findall(prose)},
        "code span": set(CODE_SPAN.findall(prose)),
        "fenced line": fenced,
        "number": {m.group(0).strip() for m in NUMBER.finditer(prose)},
        "bold label": {b.strip().rstrip(".:") for b in BOLD.findall(prose)},
    }


def check_invariants(path: pathlib.Path, text: str, before: pathlib.Path, link_check) -> list[str]:
    kind = kind_of(path)
    if kind is None:
        return []
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    old_path = before / kind / path.name
    if not old_path.is_file():
        return ["%s: no pre-rewrite copy at %s" % (rel, old_path)]
    old = tokens(old_path.read_text(encoding="utf-8"), link_check)
    new = tokens(text, link_check)
    problems = []
    for kind_name in ("url", "code span", "fenced line", "number", "bold label"):
        for item in sorted(old[kind_name] - new[kind_name]):
            problems.append("%s: lost %s: %s" % (rel, kind_name, item))
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument(
        "--before", type=pathlib.Path, help="pre-rewrite copies, <DIR>/{collectors,analyzer}/"
    )
    ap.add_argument("--width", type=int, default=100, help="longest prose line allowed")
    ap.add_argument("files", nargs="*", type=lambda s: pathlib.Path(s).resolve())
    args = ap.parse_args()
    link_check = load_link_check()
    files = args.files or research_files()
    problems: list[str] = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        problems += check_structure(f, text, args.width, link_check)
        if args.before:
            problems += check_invariants(f, text, args.before.resolve(), link_check)
    for p in problems:
        print(p)
    print("%d files checked, %d problems" % (len(files), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
