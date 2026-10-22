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
  escapes, keeps the whitespace quotes or an escape protect while the bare
  whitespace around it is trimmed, ends at a `#` or `;` outside quotes,
  and continues on the next
  line after a backslash at the end of the line that is part of the value:
  a backslash that ends a comment, a header line or a blank line continues
  nothing, as in git, so a comment such as `# C:\\git\\` never swallows the
  header after it. A pair may follow its header on the same line
  (`[remote "origin"] url = ...`), as git allows. A line that is not a
  section header or a `key = value` pair, and the keys after an
  unterminated section header, are skipped, and a value git rejects, a
  quoted one the file ends inside or one with an escape git does not
  define, is dropped and reported, since a config cut mid-URL or edited
  by hand must not yield a destination git would not read; the deprecated
  dotted form lower-cases its subsection, as git does;
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
from .model import is_windows_path

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


# The whitespace git trims around a value and a ref: ASCII only, since
# `str.strip()` would also take U+00A0 and its kind, which git keeps.
_ASCII_SPACE = " \t\r\f\v"


def _physical_lines(text: str) -> list[str]:
    """`text` split at line feeds only, a carriage return before one
    removed, and an initial byte-order mark dropped: git ends a line at LF
    or CRLF alone and accepts a UTF-8 BOM at the start of a config, while
    `str.splitlines()` would also split at U+2028, U+0085 and the ASCII
    separators, cutting a path that holds one."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [ln[:-1] if ln.endswith("\r") else ln for ln in lines]


def _parse_value(lines: list[str], i: int, text: str) -> tuple[str, int, str]:
    """The value that starts with `text` on line `i` of `lines`, with quotes
    and escapes resolved, a trailing comment removed and only the bare
    whitespace around it trimmed, the index of the last line it used, and
    `""` or the reason git would reject the line (an unterminated quote, an
    escape other than `\\\\`, `\\"`, `\\n`, `\\t` and `\\b`), in which case
    the value is `""`: a backslash at the end of the line, outside a
    comment, continues the value on the next line (a comment ends the line
    and never continues it, as in git). A lone backslash at the end of the
    file is dropped."""
    # Each character with whether quotes or an escape protect it: only bare
    # whitespace around the value is trimmed, as git trims it, so a quoted
    # path that ends in a space keeps its space.
    out: list[tuple[str, bool]] = []
    quoted = False
    while True:
        j = 0
        continued = False
        while j < len(text):
            c = text[j]
            if c == "\\":
                if j + 1 < len(text):
                    if text[j + 1] not in _ESCAPES:
                        # git rejects the line; the value is not evidence.
                        return "", i, "unsupported escape \\" + text[j + 1]
                    out.append((_ESCAPES[text[j + 1]], True))
                    j += 2
                    continue
                continued = True
                break
            if c == '"':
                quoted = not quoted
            elif c in "#;" and not quoted:
                break
            else:
                out.append((c, quoted))
            j += 1
        if continued and i + 1 < len(lines):
            i += 1
            text = lines[i]
            continue
        while out and out[0][0] in _ASCII_SPACE and not out[0][1]:
            out.pop(0)
        while out and out[-1][0] in _ASCII_SPACE and not out[-1][1]:
            out.pop()
        # A quote still open at the end is a value the file ends inside: git
        # rejects the line, and the text so far is not the destination.
        return "".join(c for c, _ in out), i, "unterminated quoted value" if quoted else ""


def _entries(text: str, errors: list[str]) -> Iterable[tuple[str, str | None]]:
    """The config's entries in order: `("[", header)` for a section header
    and `(key, value)` for a pair, the key lower-cased and the value
    resolved by `_parse_value`. A pair may follow its header on the same
    line (`[remote "origin"] url = ...`), as git allows. Comment, blank and
    unparseable lines are skipped; only a value continues across lines. A
    pair git would reject, a quoted value the file ends inside or an
    escape git does not define, is dropped and described in `errors`
    (`line <n>: unterminated quoted value`, `line <n>: unsupported escape
    \\q`), since its text is not the value git would have read."""
    lines = _physical_lines(text)
    i = 0
    while i < len(lines):
        # Only leading whitespace is dropped here: a value's trailing
        # whitespace is _parse_value's to judge, since `\ ` at the end of a
        # line is an escaped space, not a continuation.
        line = lines[i].lstrip(_ASCII_SPACE)
        if line.startswith("["):
            m = _HEADER_RX.match(line)
            if m is None:
                yield "[", line.rstrip(_ASCII_SPACE)  # unterminated or malformed
                i += 1
                continue
            yield "[", m.group(0)
            line = line[m.end() :].lstrip(_ASCII_SPACE)
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
        start = i + 1
        value, i, error = _parse_value(lines, i, m.group(2))
        if error:
            errors.append("line %d: %s" % (start, error))
        else:
            yield m.group(1).lower(), value
        i += 1


def parse_remotes(text: str, errors: list[str] | None = None) -> list[dict]:
    """The remotes of a `.git/config` text: one `{"name", "urls",
    "pushurls"}` per `[remote "<name>"]` section that sets a non-empty `url`
    or `pushurl`, sorted by name. `urls` and `pushurls` hold every value of
    the key in file order, `[]` when the section sets none: `pushurls` is
    what the file says, not git's fallback to `urls`. A value the file ends
    inside (an unterminated quote) is left out and, when `errors` is given,
    described in it as `_entries` does."""
    remotes: dict[str, dict] = {}
    current: str | None = None
    for key, value in _entries(text, [] if errors is None else errors):
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
                # git lower-cases the dotted form's subsection, so
                # [remote.Origin] and [remote "origin"] are one remote.
                current = section[len("remote.") :]
            continue
        if current is None or key not in ("url", "pushurl") or not value:
            continue
        remote = remotes.setdefault(current, {"name": current, "urls": [], "pushurls": []})
        remote[key + "s"].append(value)
    return [r for _, r in sorted(remotes.items())]


def parse_head(text: str) -> str:
    """The branch a `.git/HEAD` text names (`ref: refs/heads/<branch>`), the
    full ref for any other symbolic ref, else the detached commit hash; ""
    for an empty text. The first line ends at a line feed, and only ASCII
    whitespace is trimmed, since a ref may hold other whitespace."""
    lines = [ln.strip(_ASCII_SPACE) for ln in _physical_lines(text)]
    first = next((ln for ln in lines if ln), "")
    if first.startswith("ref:"):
        ref = first[len("ref:") :].strip(_ASCII_SPACE)
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
    given, as `<original path>: <reason>` (once per path). Under a Windows
    project path the file names are matched without regard to case, since
    the PowerShell collector matches the catalog that way and keeps the
    on-disk spelling (`.GIT/CONFIG`); elsewhere the match is exact."""
    out: dict[str, dict] = {}
    for a in artifacts:
        if not a.home.project or a.agent != PROJECT_AGENT:
            continue
        path = a.home.original or str(a.home.disk_path)
        windows = is_windows_path(path)
        rel = a.rel.lower() if windows else a.rel
        if rel == CONFIG_REL:
            field = "remotes"
        elif rel == (HEAD_REL.lower() if windows else HEAD_REL):
            field = "head"
        else:
            continue
        entry = out.setdefault(path, {"remotes": None, "head": None})
        if entry[field] is not None:
            continue
        text, error = read_text(a.disk_path)
        if error:
            line = "%s: %s" % (a.original, error)
            if problems is not None and line not in problems:
                problems.append(line)
            continue
        if field == "head":
            entry[field] = parse_head(text)
            continue
        errors: list[str] = []
        entry[field] = parse_remotes(text, errors)
        for e in errors:
            line = "%s: %s" % (a.original, e)
            if problems is not None and line not in problems:
                problems.append(line)
    return {
        path: {"remotes": e["remotes"] or [], "head": e["head"] or ""} for path, e in out.items()
    }
