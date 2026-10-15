"""Parser interface. A parser owns one agent name from the catalog, says which
of that agent's artifacts it reads, and yields timeline rows from each."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from ..dedup import TOLERANCE_SECONDS
from ..inputs import Artifact
from ..model import Row
from ..timeutil import to_utc


@dataclass
class Options:
    include_thinking: bool = False


class Parser:
    agent: str = ""
    name: str = ""
    # Other catalog agents whose artifacts this parser is also offered: an
    # extension whose chats are rows of the editor's own state.vscdb, which
    # the catalog attributes to `vscode` or to a fork such as `cursor`, lists
    # those editors here (`vscode_state.EDITOR_AGENTS`).
    reads_agents: tuple[str, ...] = ()

    def wants(self, artifact: Artifact) -> bool:
        raise NotImplementedError

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        raise NotImplementedError

    def secondary(self, artifact: Artifact) -> bool:
        """True when `artifact` is a secondary source of this parser: a
        per-prompt history file, a mirror or a projection of a store the
        parser also reads. Its rows are kept in the timeline unless the
        primary store yields the same event (`dedup.deduplicate`), so a
        session whose primary store is gone is still recovered from it."""
        return False

    def secondary_tolerance(self, artifact: Artifact) -> float:
        """Seconds a secondary row's `timestamp_utc` may differ from the primary
        row's for `dedup.deduplicate` to pair them. The default suits a history
        line written when the prompt was submitted; a parser whose secondary
        source stamps an event later than the primary store does (a transcript
        captured at the end of a turn) returns a wider window and says why in
        its docstring."""
        return TOLERANCE_SECONDS

    def base_row(self, artifact: Artifact) -> Row:
        return Row(
            host=artifact.home.host,
            user=artifact.home.user,
            agent=self.agent,
            source_file=artifact.original,
        )


def iter_jsonl(path, errors: list) -> Iterator[tuple[int, dict]]:
    """Yield (line_number, record) for each JSON object line. Bad lines are
    counted in `errors` as (line_number, message) and skipped: a transcript
    truncated mid-write by a running agent must not lose its earlier turns."""
    with open(path, "rb") as fh:
        for n, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw.decode("utf-8", errors="replace"))
            except ValueError as e:
                errors.append((n, str(e)))
                continue
            if isinstance(rec, dict):
                yield n, rec


def text_of(content) -> str:
    """Flatten the content field of a chat message: a string, or a list of
    typed blocks whose text lives under `text`."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, str):
                parts.append(b)
            elif isinstance(b, dict):
                t = b.get("text")
                if isinstance(t, str):
                    parts.append(t)
                elif b.get("type") == "image":
                    parts.append("[image]")
        return "\n".join(parts)
    if isinstance(content, dict):
        t = content.get("text")
        return t if isinstance(t, str) else json.dumps(content, ensure_ascii=False)
    return str(content)


def compact_json(value) -> str:
    try:
        s = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    except (TypeError, ValueError):
        s = str(value)
    return s


def file_mtime(artifact: Artifact) -> str:
    """The file's modification time as a timeline timestamp: the manifest's
    pre-copy `mtime` when the collection has a manifest, else the file's
    own. Standing settings rows (`permission setting: ... (from <file>,
    file mtime)`) are timestamped with this."""
    t = (artifact.manifest or {}).get("mtime")
    if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0:
        return to_utc(t)
    try:
        return to_utc(artifact.disk_path.lstat().st_mtime)
    except OSError:
        return ""


def setting_value(v) -> str:
    """A setting as row text: a bool as `true`/`false`, a string as it is,
    anything else as compact JSON."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return v
    return compact_json(v)


def track_change(label: str, seen: dict, key, value: str) -> str:
    """The `system` row text for a tracked state (`model`, `permission mode`)
    when `value` is new for `key` (a session or thread id): `<label>: <value>`
    the first time, `<label>: <old> -> <new>` on a change, and `""` when it
    is unchanged or empty. `seen` is the parser's per-file dict."""
    if not value:
        return ""
    old = seen.get(key)
    if old == value:
        return ""
    seen[key] = value
    return "%s: %s -> %s" % (label, old, value) if old else "%s: %s" % (label, value)
