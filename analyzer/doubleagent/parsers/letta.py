"""Letta Code transcripts.

Validated against source, letta-ai/letta-code at 77faf36e (October 2026),
with a synthetic fixture; see `research/letta.md`. Letta keeps
conversations on the Letta server by default; three local stores are
parsed:

* `~/.letta/lc-local-backend/conversations/<base64url key>/messages.jsonl`
  (local backend only; the key is `conversation:<id>` or
  `default:<agent id>`). `manifest.json` `message_format`
  `pi-session-entry-jsonl` (schema 2): pi's session format, read with
  `pi.read_session` and `pi.entry_rows`. Header `id` (conversation id,
  falling back to the decoded directory name) and `cwd`; entries `message`
  and `compaction`. `message.id` starts `letta-msg-` and a message may be
  re-appended with the same `id` as a replacement snapshot, so only the
  last copy of each `message.id` is kept. Schema 1 files
  (`pi-ai-message-jsonl`, one bare message per line, no header) are read
  too, timed by `message.metadata.created_at` or `message.timestamp`.
* `~/.letta/transcripts/<agent>/<conversation>/transcript.jsonl` (both
  backends, appended after each turn): `kind` user, assistant, reasoning
  (a `thinking` row, opt-in) or error (system) with `text`; or
  `kind: "tool_call"` with `name`, `argsText`, `resultText`, `resultOk`,
  emitted as a tool_use and a tool_result with no tool id. `argsText` is
  the streamed arguments JSON; when it parses, the tool_use text is
  `pi.args_summary` of it (the command, path or query), as the
  `messages.jsonl` row for the same call renders it, else the raw text.
  Every line has `captured_at` (ISO 8601 Z, shared by a turn's lines). No
  model and no cwd: the session id is the conversation directory name
  (the conversation id, `local-conv-<n>` or `default`, which the directory
  sanitisation leaves unchanged, so it equals the `messages.jsonl` header
  `id`) and the project path is the `project` of the `sessions.jsonl` line
  with the same `agent_id` and the latest `timestamp` at or before
  `captured_at`, a heuristic.

  A secondary source (`secondary()`, issue 122): in local-backend mode it
  repeats the turns of the conversation's `messages.jsonl`, the store of
  record, and it is read always, whether or not that file was collected,
  so a conversation whose local-backend directory was deleted (deleting an
  agent removes its conversation directories, not its transcripts) or a
  server-backend conversation (no local store at all) is still recovered.
  Letta stamps `captured_at` once per turn, when the turn ends
  (`new Date()` in `appendTranscriptDeltaJsonl`, called after the turn's
  `end_turn` stop reason), so every line of a turn is later than its
  `messages.jsonl` twin by up to the turn's duration, the user prompt by
  all of it. `secondary_tolerance()` is therefore `TURN_TOLERANCE_SECONDS`
  (one hour) instead of the default 2 seconds; a turn longer than that
  (a long unattended run, an approval left waiting) leaves its earlier
  lines unpaired, shown twice. The pairing is confined to one
  conversation and one text, so the wide window can only pair a line with
  an identical event of the same conversation. Turns that end in an
  error or an interrupt are never appended, so the transcript lacks them.
* `~/.letta/sessions.jsonl`: per CLI session, a start line and an exit
  line with `agent_id`, `session_id`, `timestamp` (ms), `project`,
  `model`, `provider`, and on exit `message_count`, `tool_call_count`,
  `exit_reason`, `duration.wall_ms`. One system row per line, followed by
  `model: <model> provider=<provider>` on the first line of a
  `session_id` that names a model and `model: <old> -> <new>
  provider=<provider>` when a later line of it names another.

Model rows in `messages.jsonl` come from the pi reader (`pi.model_text`):
`model: <id> provider=<provider>` at the first assistant `message.model`
(or `responseModel`) of a conversation and `model: <old> -> <new> ...` on
each change. The reflection transcript records no model. No permission
state is read: a project's `.letta/settings.local.json` holds its
permissions, but the research does not record their shape.

Not parsed: `logs/chunk-logs/` (stream chunks cut to 200 characters) and
the retired Letta server's `sqlite.db` (column encodings unverified).
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from collections.abc import Iterator

from ..inputs import Artifact
from ..model import Row, compact
from ..timeutil import to_utc
from .base import Options, Parser, iter_jsonl
from .pi import SessionFile, args_summary, entry_rows, error_row, model_text, read_session

TRANSCRIPT_RX = re.compile(r"^\.letta/transcripts/([^/]+)/([^/]+)/transcript\.jsonl$")
LOCAL_RX = re.compile(r"^\.letta/lc-local-backend/conversations/([^/]+)/messages\.jsonl$")
SESSIONS_REL = ".letta/sessions.jsonl"
# The window a transcript line may lag its messages.jsonl twin: a turn's
# whole duration, since captured_at is stamped at the turn's end.
TURN_TOLERANCE_SECONDS = 3600.0


def decode_key(name: str) -> str:
    """`conversation:<id>` or `default:<agent id>` from a base64url
    directory name, or empty."""
    try:
        return base64.urlsafe_b64decode(name + "=" * (-len(name) % 4)).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return ""


def sanitize(segment: str) -> str:
    """The transcript directory name Letta derives from an id."""
    s = re.sub(r"[^a-zA-Z0-9._-]", "_", segment).strip()
    return s or "unknown"


def _args_text(args) -> str:
    """A transcript `argsText` as the pi reader renders the same call's
    arguments: `args_summary` of the parsed JSON, else the text itself."""
    if not isinstance(args, str):
        return args_summary(args)
    try:
        return args_summary(json.loads(args))
    except ValueError:
        return args


def _bare_messages(session: SessionFile) -> SessionFile:
    """Schema 1: every line a bare pi-ai message. Wrapped as entries."""
    out = SessionFile()
    out.errors = session.errors
    for n, rec in session.entries:
        meta = rec.get("metadata")
        if not isinstance(meta, dict):
            meta = {}
        out.entries.append(
            (n, {"type": "message", "timestamp": meta.get("created_at"), "message": rec})
        )
    return out


def _last_snapshots(session: SessionFile) -> SessionFile:
    """Keep only the last entry for each `message.id`."""
    last: dict[str, int] = {}
    for i, (_, rec) in enumerate(session.entries):
        msg = rec.get("message")
        if isinstance(msg, dict) and msg.get("id"):
            last[str(msg.get("id"))] = i
    out = SessionFile()
    out.header, out.header_line, out.errors = session.header, session.header_line, session.errors
    for i, (n, rec) in enumerate(session.entries):
        msg = rec.get("message")
        if isinstance(msg, dict) and msg.get("id") and last[str(msg.get("id"))] != i:
            continue
        out.entries.append((n, rec))
    return out


class LettaParser(Parser):
    agent = "letta"
    name = "letta"

    def wants(self, artifact: Artifact) -> bool:
        return (
            artifact.rel == SESSIONS_REL
            or bool(TRANSCRIPT_RX.match(artifact.rel))
            or bool(LOCAL_RX.match(artifact.rel))
        )

    def secondary(self, artifact: Artifact) -> bool:
        return bool(TRANSCRIPT_RX.match(artifact.rel))

    def secondary_tolerance(self, artifact: Artifact) -> float:
        return TURN_TOLERANCE_SECONDS

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if artifact.rel == SESSIONS_REL:
            yield from self._parse_sessions(artifact, opts)
            return
        m = LOCAL_RX.match(artifact.rel)
        if m:
            yield from self._parse_local(artifact, m.group(1), opts)
            return
        m = TRANSCRIPT_RX.match(artifact.rel)
        assert m is not None  # wants() accepted only matching paths
        yield from self._parse_transcript(artifact, m.group(1), m.group(2), opts)

    # -- local backend ----------------------------------------------------

    def _parse_local(self, artifact: Artifact, dirname: str, opts: Options) -> Iterator[Row]:
        session = read_session(artifact.disk_path)
        key = decode_key(dirname)
        sid = str(session.header.get("id") or key.partition(":")[2])
        cwd = str(session.header.get("cwd") or "")
        if (
            not session.header
            and session.entries
            and all("role" in rec and rec.get("type") != "message" for _, rec in session.entries)
        ):
            session = _bare_messages(session)
        else:
            session = _last_snapshots(session)
        if session.header:
            row = self.base_row(artifact)
            row.source_line = session.header_line
            row.timestamp_utc = to_utc(session.header.get("timestamp"))
            row.session_id, row.project_path, row.turn_type = sid, cwd, "system"
            row.text = compact(
                "letta local-backend conversation start: %s cwd=%s" % (key or sid, cwd),
            )
            yield row
        yield from entry_rows(self, artifact, session, opts, sid, cwd)
        if session.errors:
            yield error_row(self, artifact, session.errors, sid, cwd)

    # -- reflection transcript ------------------------------------------

    def _sessions(self, artifact: Artifact, agent_dir: str) -> list[tuple[str, str]]:
        """(timestamp, project) of the sessions.jsonl lines for this agent,
        sorted by time."""
        f = artifact.home.disk_path / SESSIONS_REL
        if f.is_symlink() or not f.is_file() or (artifact.home.disk_path / ".letta").is_symlink():
            return []
        out = []
        for _, rec in iter_jsonl(f, []):
            if sanitize(str(rec.get("agent_id") or "")) == agent_dir and rec.get("project"):
                ts = to_utc(rec.get("timestamp"))
                if ts:
                    out.append((ts, str(rec.get("project"))))
        return sorted(out)

    def _parse_transcript(
        self, artifact: Artifact, agent_dir: str, conv_dir: str, opts: Options
    ) -> Iterator[Row]:
        sessions = self._sessions(artifact, agent_dir)
        errors: list = []
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            ts = to_utc(rec.get("captured_at"))
            project = ""
            for sts, sproj in sessions:
                if ts and sts <= ts:
                    project = sproj
                elif ts:
                    break

            def base() -> Row:
                row = self.base_row(artifact)
                row.source_line = n
                row.timestamp_utc = ts
                row.session_id = conv_dir
                row.project_path = project
                return row

            kind = rec.get("kind")
            text = str(rec.get("text") or "")
            if kind in ("user", "assistant"):
                row = base()
                row.turn_type = kind
                row.text = compact(text)
                yield row
            elif kind == "reasoning":
                if opts.include_thinking:
                    row = base()
                    row.turn_type = "thinking"
                    row.text = compact(text)
                    yield row
            elif kind == "error":
                row = base()
                row.turn_type = "system"
                row.text = compact("error: " + text)
                yield row
            elif kind == "tool_call":
                name = str(rec.get("name") or "")
                row = base()
                row.turn_type, row.tool_name = "tool_use", name
                row.text = compact(_args_text(rec.get("argsText")))
                yield row
                if "resultText" in rec or "resultOk" in rec:
                    result = str(rec.get("resultText") or "")
                    if rec.get("resultOk") is False:
                        result = "[error] " + result
                    row = base()
                    row.turn_type, row.tool_name = "tool_result", name
                    row.text = compact(result)
                    yield row
        if errors:
            yield error_row(self, artifact, errors, conv_dir)

    # -- sessions.jsonl --------------------------------------------------

    def _parse_sessions(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        seen: dict = {}  # the model per CLI session, for the `model:` rows
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            row = self.base_row(artifact)
            row.source_line = n
            row.timestamp_utc = to_utc(rec.get("timestamp"))
            row.session_id = str(rec.get("session_id") or "")
            row.project_path = str(rec.get("project") or "")
            row.model = str(rec.get("model") or "")
            row.turn_type = "system"
            dur = rec.get("duration")
            if not isinstance(dur, dict):
                dur = {}
            if "exit_reason" in rec or "message_count" in rec:
                text = (
                    "letta session end: agent=%s exit_reason=%s messages=%s tool_calls=%s wall_ms=%s"
                    % (
                        rec.get("agent_id") or "",
                        rec.get("exit_reason") or "",
                        rec.get("message_count", ""),
                        rec.get("tool_call_count", ""),
                        dur.get("wall_ms", ""),
                    )
                )
            else:
                text = "letta session start: agent=%s provider=%s model=%s project=%s" % (
                    rec.get("agent_id") or "",
                    rec.get("provider") or "",
                    row.model,
                    row.project_path,
                )
            row.text = compact(text)
            yield row
            mtext = model_text(seen, row.session_id, row.model, str(rec.get("provider") or ""))
            if mtext:
                mrow = self.base_row(artifact)
                mrow.source_line, mrow.turn_type = n, "system"
                mrow.timestamp_utc, mrow.session_id = row.timestamp_utc, row.session_id
                mrow.project_path, mrow.model = row.project_path, row.model
                mrow.text = compact(mtext)
                yield mrow
        if errors:
            yield error_row(self, artifact, errors)
