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
  escapes, may continue on the next line after a trailing backslash, and
  ends at a `#` or `;` outside quotes. A line that is not a section header
  or a `key = value` pair, and the keys after an unterminated section
  header, are skipped; the rest of the file is still read. A remote may
  have several `url` and `pushurl` lines (git fetches from the first `url`
  and pushes to every `pushurl`, or to every `url` when there is none), so
  every value of each is kept, in file order.
* `.git/HEAD`: `ref: refs/heads/<branch>` while a branch is checked out,
  else the commit hash of a detached HEAD.

Files are read from the evidence copy, opened read-only and only when
`lstat` says they are regular files, so a symlink is never followed. An
unreadable file reads as empty: no remotes, no head.
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
# Larger than any repository configuration; a file past it is read up to it.
MAX_BYTES = 1 << 20

_HEADER_RX = re.compile(r'\[\s*([A-Za-z0-9.-]+)(?:\s+"((?:[^"\\]|\\.)*)")?\s*\]')
_KEY_RX = re.compile(r"([A-Za-z][A-Za-z0-9-]*)\s*(?:=(.*))?$")
_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "t": "\t", "b": "\b"}


def read_text(path: Path) -> str:
    """The file at `path` as text (UTF-8, undecodable bytes replaced), at
    most `MAX_BYTES`; "" when it is missing, unreadable or not a regular
    file. Never follows a symlink."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return ""
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as fh:
            data = fh.read(MAX_BYTES)
    except OSError:
        return ""
    return data.decode("utf-8", errors="replace")


def _value(text: str) -> str:
    """A config value with quotes and escapes resolved and a trailing
    comment removed. A lone backslash at the end (a continuation with no
    next line) is dropped."""
    out: list[str] = []
    quoted = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            if i + 1 < len(text):
                out.append(_ESCAPES.get(text[i + 1], text[i + 1]))
            i += 2
            continue
        if c == '"':
            quoted = not quoted
        elif c in "#;" and not quoted:
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).strip()


def _continues(line: str) -> bool:
    """Whether `line` ends in a continuation backslash: an odd number of
    trailing backslashes, since `\\\\` is an escaped backslash."""
    return (len(line) - len(line.rstrip("\\"))) % 2 == 1


def _logical_lines(text: str) -> Iterable[str]:
    """The lines of `text`, a line that ends in a continuation backslash
    joined to the next one."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        while _continues(line) and i + 1 < len(lines):
            i += 1
            line = line[:-1] + lines[i]
        yield line
        i += 1


def parse_remotes(text: str) -> list[dict]:
    """The remotes of a `.git/config` text: one `{"name", "urls",
    "pushurls"}` per `[remote "<name>"]` section that sets a non-empty `url`
    or `pushurl`, sorted by name. `urls` and `pushurls` hold every value of
    the key in file order, `[]` when the section sets none: `pushurls` is
    what the file says, not git's fallback to `urls`."""
    remotes: dict[str, dict] = {}
    current: str | None = None
    for raw in _logical_lines(text):
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("["):
            m = _HEADER_RX.match(line)
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
        if current is None:
            continue
        m = _KEY_RX.match(line)
        if m is None or m.group(2) is None:
            continue
        key = m.group(1).lower()
        if key not in ("url", "pushurl"):
            continue
        value = _value(m.group(2))
        if not value:
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


def project_git(artifacts: Iterable[Artifact]) -> dict[str, dict]:
    """`{"remotes": [...], "head": str}` per project directory among the
    `artifacts`, keyed as `cli.project_agents` keys it (`home.original`, or
    the disk path when that is empty), from its `.git/config` and
    `.git/HEAD` files with agent `project`. A project without them is
    absent; the first file met wins when a path has two copies."""
    out: dict[str, dict] = {}
    for a in artifacts:
        if not a.home.project or a.agent != PROJECT_AGENT or a.rel not in (CONFIG_REL, HEAD_REL):
            continue
        path = a.home.original or str(a.home.disk_path)
        entry = out.setdefault(path, {"remotes": None, "head": None})
        if a.rel == CONFIG_REL and entry["remotes"] is None:
            entry["remotes"] = parse_remotes(read_text(a.disk_path))
        elif a.rel == HEAD_REL and entry["head"] is None:
            entry["head"] = parse_head(read_text(a.disk_path))
    return {
        path: {"remotes": e["remotes"] or [], "head": e["head"] or ""} for path, e in out.items()
    }
