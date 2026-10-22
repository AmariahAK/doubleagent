"""The remotes and checked-out branch of a collected project's repository.

The collectors gather a project's `.git/HEAD`, `.git/config`,
`.git/FETCH_HEAD`, `.git/packed-refs`, `.git/refs`, `.git/logs` and
`.git/worktrees` with agent `project` (the project catalog's `project|.git/...`
lines, collector 1.19.0, issue 253). This module reads two of them:

* `.git/config`, git's INI-like configuration: a `[remote "<name>"]` section
  per remote, with `url` (where fetches come from, and pushes when there is
  no `pushurl`) and `pushurl` (where pushes go). Section and key names are
  matched without regard to case, as git does; the subsection (the remote's
  name) is kept as written. The deprecated `[remote.<name>]` form is read
  too. A value may be quoted, may hold `\\`, `\\"`, `\\n`, `\\t` and `\\b`
  escapes, ends at a `#` or `;` outside quotes, and continues on the next
  line after a backslash at the end of the line that is part of the value:
  a backslash that ends a comment, a header line or a blank line continues
  nothing, as in git, so a comment such as `# C:\\git\\` never swallows the
  header after it. A pair may follow its header on the same line
  (`[remote "origin"] url = ...`), as git allows. A line that is not a
  section header or a `key = value` pair, and the keys after an
  unterminated section header, are skipped;
  the rest of the file is still read. A remote may have several `url` and
  `pushurl` lines (git fetches from the first `url` and pushes to every
  `pushurl`, or to every `url` when there is none), so every value of each
  is kept, in file order.
* `.git/HEAD`: `ref: refs/heads/<branch>` while a branch is checked out,
  else the commit hash of a detached HEAD.

Files are read whole from the evidence copy, opened read-only and only when
`lstat` says they are regular files, so a symlink is never followed. A file
that cannot be read (missing, not a regular file, a permission or I/O
error) gives no remotes and no head, and `project_git` reports it as a
problem, `<path>: <reason>`, so an unreadable file is never mistaken for a
repository without remotes.
"""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Iterable
from pathlib import Path

from .inputs import PROJECT_AGENT, Artifact

CONFIG_REL = ".git/config"
HEAD_REL = ".git/HEAD"

_HEADER_RX = re.compile(r'\[\s*([A-Za-z0-9.-]+)(?:\s+"((?:[^"\\]|\\.)*)")?\s*\]')
_KEY_RX = re.compile(r"([A-Za-z][A-Za-z0-9-]*)\s*(?:=(.*))?$")
_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "t": "\t", "b": "\b"}


def read_text(path: Path) -> tuple[str, str]:
    """`(text, error)`: the whole file at `path` as text (UTF-8, undecodable
    bytes replaced) and `""`, or `""` and the reason when it is missing,
    unreadable or not a regular file. Never follows a symlink."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return "", "not a regular file"
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as fh:
            data = fh.read()
    except OSError as e:
        return "", e.strerror or type(e).__name__
    return data.decode("utf-8", errors="replace"), ""


def _parse_value(lines: list[str], i: int, text: str) -> tuple[str, int]:
    """The value that starts with `text` on line `i` of `lines`, with quotes
    and escapes resolved and a trailing comment removed, and the index of
    the last line it used: a backslash at the end of the line, outside a
    comment, continues the value on the next line (a comment ends the line
    and never continues it, as in git). A lone backslash at the end of the
    file is dropped."""
    out: list[str] = []
    quoted = False
    while True:
        j = 0
        continued = False
        while j < len(text):
            c = text[j]
            if c == "\\":
                if j + 1 < len(text):
                    out.append(_ESCAPES.get(text[j + 1], text[j + 1]))
                    j += 2
                    continue
                continued = True
                break
            if c == '"':
                quoted = not quoted
            elif c in "#;" and not quoted:
                break
            else:
                out.append(c)
            j += 1
        if continued and i + 1 < len(lines):
            i += 1
            text = lines[i]
            continue
        return "".join(out).strip(), i


def _entries(text: str) -> Iterable[tuple[str, str | None]]:
    """The config's entries in order: `("[", header)` for a section header
    and `(key, value)` for a pair, the key lower-cased and the value
    resolved by `_parse_value`. A pair may follow its header on the same
    line (`[remote "origin"] url = ...`), as git allows. Comment, blank and
    unparseable lines are skipped; only a value continues across lines."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("["):
            m = _HEADER_RX.match(line)
            if m is None:
                yield "[", line  # unterminated or malformed
                i += 1
                continue
            yield "[", m.group(0)
            line = line[m.end() :].strip()
        if not line or line[0] in "#;":
            i += 1
            continue
        m = _KEY_RX.match(line)
        if m is None:
            i += 1
            continue
        if m.group(2) is None:
            yield m.group(1).lower(), None
            i += 1
            continue
        value, i = _parse_value(lines, i, m.group(2))
        yield m.group(1).lower(), value
        i += 1


def parse_remotes(text: str) -> list[dict]:
    """The remotes of a `.git/config` text: one `{"name", "urls",
    "pushurls"}` per `[remote "<name>"]` section that sets a non-empty `url`
    or `pushurl`, sorted by name. `urls` and `pushurls` hold every value of
    the key in file order, `[]` when the section sets none: `pushurls` is
    what the file says, not git's fallback to `urls`."""
    remotes: dict[str, dict] = {}
    current: str | None = None
    for key, value in _entries(text):
        if key == "[":
            m = _HEADER_RX.match(value or "")
            current = None
            if m is None:
                continue  # unterminated or malformed: its keys belong to no section
            section, sub = m.group(1).lower(), m.group(2)
            if sub is not None:
                if section == "remote":
                    current = re.sub(r"\\(.)", r"\1", sub)
            elif section.startswith("remote.") and len(section) > len("remote."):
                current = m.group(1)[len("remote.") :]
            continue
        if current is None or key not in ("url", "pushurl") or not value:
            continue
        remote = remotes.setdefault(current, {"name": current, "urls": [], "pushurls": []})
        remote[key + "s"].append(value)
    return [r for _, r in sorted(remotes.items())]


def parse_head(text: str) -> str:
    """The branch a `.git/HEAD` text names (`ref: refs/heads/<branch>`), the
    full ref for any other symbolic ref, else the detached commit hash; ""
    for an empty text."""
    first = text.strip().splitlines()[0].strip() if text.strip() else ""
    if first.startswith("ref:"):
        ref = first[len("ref:") :].strip()
        return ref[len("refs/heads/") :] if ref.startswith("refs/heads/") else ref
    return first


def project_git(
    artifacts: Iterable[Artifact], problems: list[str] | None = None
) -> dict[str, dict]:
    """`{"remotes": [...], "head": str}` per project directory among the
    `artifacts`, keyed as `cli.project_agents` keys it (`home.original`, or
    the disk path when that is empty), from its `.git/config` and
    `.git/HEAD` files with agent `project`. A project without them is
    absent; the first file met wins when a path has two copies. A file that
    cannot be read counts as absent and is appended to `problems`, when
    given, as `<original path>: <reason>` (once per path)."""
    out: dict[str, dict] = {}
    for a in artifacts:
        if not a.home.project or a.agent != PROJECT_AGENT or a.rel not in (CONFIG_REL, HEAD_REL):
            continue
        path = a.home.original or str(a.home.disk_path)
        entry = out.setdefault(path, {"remotes": None, "head": None})
        field = "remotes" if a.rel == CONFIG_REL else "head"
        if entry[field] is not None:
            continue
        text, error = read_text(a.disk_path)
        if error:
            line = "%s: %s" % (a.original, error)
            if problems is not None and line not in problems:
                problems.append(line)
            continue
        entry[field] = parse_remotes(text) if field == "remotes" else parse_head(text)
    return {
        path: {"remotes": e["remotes"] or [], "head": e["head"] or ""} for path, e in out.items()
    }
