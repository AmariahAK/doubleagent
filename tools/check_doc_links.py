#!/usr/bin/env python3
"""Verify the links, section references and external references in the Markdown documents.

Every reference from one project document to another is a Markdown link with
a path relative to the citing file, and every reference to a section links to
its heading (the link rule under "Conventions" in AGENTS.md). This checks, in
every tracked Markdown file and every untracked one git does not ignore:

- each inline link `[text](target)` and reference definition `[label]: target`
  whose target has no URL scheme resolves to a file or directory that exists,
  relative to the citing file (an empty path is the citing file itself);
- when the target is a Markdown file and has a `#fragment`, the file has a
  heading whose GitHub anchor equals the fragment (lower case, characters
  other than letters, digits, spaces, hyphens and underscores removed, spaces
  to hyphens, `-1`, `-2` appended to repeated anchors);
- outside AGENTS.md, no `section <n>` or `sections <n>` appears except as
  link text, since a section reference must link to the heading;
- with link targets, reference definition targets and `<autolinks>` also
  ignored, no `http://` or `https://` URL and no scheme-less host path such as
  `github.com/owner/repo` is left in the text, and no inline link has a URL or
  host path as its text, since an external source is one link whose text
  names it and whose target is the full URL.

A YAML front matter block at the top of a file (the site's navigation, see
`_config.yml`), fenced code blocks and inline code spans are ignored before
matching.

Usage: tools/check_doc_links.py [FILE...]

With FILE arguments only those files are scanned. Every failure is printed as
`path:line: message`; the exit status is 1 when any check failed.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent

FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
CODE_SPAN = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
# Link text may hold one level of nested brackets; the target may be <...>
# and may be followed by a title.
INLINE_LINK = re.compile(
    r"\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(\s*(<[^>\n]*>|[^\s()]+(?:\([^\s()]*\)[^\s()]*)*)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
REF_DEF = re.compile(r"^ {0,3}\[[^\]]+\]:[ \t]*(<[^>\n]*>|\S+)", re.M)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
SECTION = re.compile(r"\bsections?\s+\d+", re.I)
ATX = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
HTML_ID = re.compile(r"<a\s[^>]*\b(?:id|name)=\"([^\"]+)\"", re.I)
URL = re.compile(r"\bhttps?://[^\s<>()\[\]]+", re.I)
HOST_PATH = re.compile(
    r"(?<![\w/@.-])(?:[a-z0-9-]+\.)+(?:com|io|org|net|dev|ai|co|google)/[^\s)\],;]+"
)
AUTOLINK = re.compile(r"<[A-Za-z][A-Za-z0-9+.-]*:[^\s<>]*>")
LINK_IN_HEADING = re.compile(r"!?\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\([^)]*\)")


def strip_front_matter(text: str) -> str:
    """Blank a leading `---` YAML front matter block, keeping line numbers.

    Without this the closing `---` would make the last key a setext heading.
    """
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        return text
    for end in range(1, len(lines)):
        if lines[end].rstrip() == "---":
            return "\n" * end + "\n".join(lines[end:]).replace("---", "", 1)
    return text


def strip_fences(text: str) -> str:
    """Blank front matter and every line of a fenced code block, keeping line numbers."""
    text = strip_front_matter(text)
    out = []
    fence = ""
    for line in text.split("\n"):
        m = FENCE.match(line)
        if fence:
            closing = m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence)
            if closing and not line.strip().lstrip(fence[0]):
                fence = ""
            out.append("")
        elif m:
            fence = m.group(1)
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def blank_code_spans(text: str) -> str:
    """Replace each inline code span with spaces, keeping offsets and newlines."""
    return CODE_SPAN.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def blank(text: str, spans: list[tuple[int, int]]) -> str:
    """Replace each span with spaces, keeping offsets and newlines."""
    chars = list(text)
    for lo, hi in spans:
        for i in range(lo, hi):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def anchor(heading: str) -> str:
    h = LINK_IN_HEADING.sub(r"\1", heading)
    h = h.replace("`", "").strip().lower()
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


def anchors_of(path: pathlib.Path, cache: dict[pathlib.Path, set[str]]) -> set[str]:
    if path in cache:
        return cache[path]
    text = strip_fences(path.read_text(encoding="utf-8"))
    lines = text.split("\n")
    seen: dict[str, int] = {}
    found: set[str] = set()
    for i, line in enumerate(lines):
        m = ATX.match(line)
        heading = None
        if m:
            heading = m.group(2)
        elif (
            i > 0
            and SETEXT.match(line)
            and lines[i - 1].strip()
            and not ATX.match(lines[i - 1])
            and not (
                line.strip().startswith("-") and lines[i - 1].lstrip().startswith(("-", "*", "|"))
            )
        ):
            heading = lines[i - 1]
        if heading is None:
            continue
        a = anchor(heading)
        n = seen.get(a, 0)
        seen[a] = n + 1
        found.add(a if n == 0 else "%s-%d" % (a, n))
    found.update(HTML_ID.findall(text))
    cache[path] = found
    return found


def markdown_files() -> list[pathlib.Path]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    files = {ROOT / p for p in out.split("\0") if p.endswith(".md")}
    return sorted(f for f in files if f.is_file())


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_target(src: pathlib.Path, target: str, cache: dict[pathlib.Path, set[str]]) -> str | None:
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if SCHEME.match(target):
        return None
    path_part, _, fragment = target.partition("#")
    path_part = urllib.parse.unquote(path_part)
    if not path_part:
        dest = src
    elif path_part.startswith("/"):
        dest = ROOT / path_part.lstrip("/")
    else:
        dest = src.parent / path_part
    if not dest.exists():
        return "link target does not exist: %s" % target
    if (
        fragment
        and dest.is_file()
        and dest.suffix.lower() == ".md"
        and urllib.parse.unquote(fragment) not in anchors_of(dest, cache)
    ):
        return "no heading for #%s in %s" % (fragment, display(dest))
    return None


def display(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("files", nargs="*", type=lambda s: pathlib.Path(s).resolve())
    args = ap.parse_args()
    files = args.files or markdown_files()
    cache: dict[pathlib.Path, set[str]] = {}
    links = bad = 0
    for f in files:
        rel = display(f)
        text = blank_code_spans(strip_fences(f.read_text(encoding="utf-8")))
        link_text: list[tuple[int, int]] = []
        targets: list[tuple[int, str]] = []
        hidden: list[tuple[int, int]] = []
        for m in INLINE_LINK.finditer(text):
            link_text.append((m.start(1), m.end(1)))
            targets.append((m.start(2), m.group(2)))
            hidden.append((m.start(1), m.end(1)))
            hidden.append((m.end(1), m.end(0)))
            label = " ".join(m.group(1).split())
            if URL.search(label) or HOST_PATH.search(label):
                print("%s:%d: link text is a URL: %s" % (rel, line_of(text, m.start(1)), label))
                bad += 1
        for m in REF_DEF.finditer(text):
            targets.append((m.start(1), m.group(1)))
            hidden.append((m.start(1), m.end(1)))
        for m in AUTOLINK.finditer(text):
            hidden.append((m.start(), m.end()))
        prose = blank(text, hidden)
        for pattern, what in ((URL, "URL"), (HOST_PATH, "host path")):
            for m in pattern.finditer(prose):
                print(
                    "%s:%d: %s is not a link: %s"
                    % (rel, line_of(prose, m.start()), what, m.group(0))
                )
                bad += 1
        for offset, target in sorted(targets):
            links += 1
            msg = check_target(f, target, cache)
            if msg:
                print("%s:%d: %s" % (rel, line_of(text, offset), msg))
                bad += 1
        if f.name == "AGENTS.md" and f.parent == ROOT:
            continue
        for m in SECTION.finditer(text):
            if any(lo <= m.start() and m.end() <= hi for lo, hi in link_text):
                continue
            words = " ".join(m.group(0).split())
            print(
                "%s:%d: section reference is not a link: %s"
                % (rel, line_of(text, m.start()), words)
            )
            bad += 1
    if bad:
        print("%d problems in %d links checked in %d files" % (bad, links, len(files)))
        return 1
    print("%d links checked in %d files" % (links, len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
