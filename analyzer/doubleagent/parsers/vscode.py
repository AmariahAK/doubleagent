"""VS Code chat sessions (GitHub Copilot Chat and other chat participants).

Validated against source, microsoft/vscode at d7622a529314 (see
`analyzer/research/vscode.md`), with a synthetic fixture; no real install
was checked. The store is VS Code's own, so the same parser covers every
editor data directory the catalog attributes to `vscode`: Code, Code -
Insiders, VSCodium, Positron and Trae under `.config`, `Library/Application
Support` or `AppData/Roaming`, and the remote-server layout
`.vscode-server*/data`, `.vscodium-server*/data`, `.positron-server/data`.
Files, relative to that directory's `User/`:

* `workspaceStorage/<hash>/chatSessions/<sessionId>.jsonl` (1.109 and
  later) or `.json` (earlier), with `workspaceStorage/<hash>/workspace.json`
  (`folder` or `workspace`, a file URI) beside it;
* `globalStorage/emptyWindowChatSessions/<sessionId>.jsonl` or `.json`;
* `globalStorage/transferredChatSessions/<sessionId>.json`.

`.jsonl` files are an object mutation log replayed in order: `{"kind": 0,
"v": <session>}` sets the whole object, `{"kind": 1, "k": [path], "v"}`
sets a value, `{"kind": 2, "k": [path], "v": [items], "i"?}` pushes items
(truncating to `i` first), `{"kind": 3, "k": [path]}` deletes. `.json`
files are the session object itself.

Session fields: `sessionId`, `creationDate` (ms), `responderUsername`,
`initialLocation`, `customTitle`, `workingDirectory` (URI), `requests[]`.
Request fields: `requestId`, `timestamp` (ms), `message` (`{text}` or a
string), `variableData.variables[].name`, `modelId`,
`isSystemInitiated`, `isCanceled`, `response[]`, `responseTimestamp` (ms),
`result.errorDetails.message`. Response parts: a bare `{value}` markdown
string (or `{kind: "markdownContent", content: {value}}`), `{kind:
"inlineReference", name?, inlineReference}`, `{kind: "thinking", value}`
(string or list), `{kind: "toolInvocationSerialized", toolCallId, toolId,
invocationMessage, pastTenseMessage, isComplete, toolSpecificData
(`commandLine.original` or `rawInput`), resultDetails (`{input, output:
[{value}], isError}` or a list of URIs), resultError}`, `{kind:
"textEditGroup", uri}`. Legacy `response` may be a string or a list of
strings. Other part kinds (progress, undo stops, code block URIs) are
skipped.

Model and permission rows, all `system`: the request `modelId` gives
`model: <id>` at the first request that names one and
`model: <old> -> <new>` on every later change, and the request
`modeInfo.telemetryModeId` (`ask`, `agent`, `edit`, `custom`) gives
`permission mode: <mode>` and `permission mode: <old> -> <new>` the same
way; both precede the request's user row and take its timestamp. A tool
invocation's `isConfirmed` (a boolean before 1.104, else a
`ConfirmedReason` object whose numeric `type` is a `ToolConfirmKind`,
printed `<Name>(<n>)`, with its `source`, `id`, `scope`, `selectedButton`,
`selectedButtonKind` or `reason` beside it) becomes
`permission decision: confirmed=<value> ...` after the `tool_result` row,
with the invocation's own `source.type` (where the tool came from:
`extension`, `mcp`, `user`, `internal`, `external`) as `tool_source=`. A
`{kind: "confirmation", title, message, buttons, isUsed}` response part
becomes `permission decision: confirmation isUsed=<bool> buttons=<list>
title=<title>` followed by its message, and a request whose
`confirmation` string is set (the label of the button the user clicked,
which also sent the request) gets `permission decision:
confirmation=<label>` after its user row.

The Copilot Chat extension is closed source, so `modelId` (the `model`
column) and `responderUsername` (in the session-start row) are passed
through as opaque strings; `agent.id` is not used. User rows carry
the request `timestamp`, response rows `responseTimestamp` (falling back to
the request time). Contiguous markdown and inline references become one
`assistant` row; each tool invocation becomes a `tool_use` and a
`tool_result` row sharing `toolCallId`. There is no git branch.
`source_line` is the log line that created the request (`.jsonl`) or 0
(`.json`).

The project path (issue 185) is the session's own `workingDirectory`
when it is set, else the `folder` of the sibling `workspace.json`, else
empty. A `workspace.json` `workspace` value is never the project: it names
a `.code-workspace` file, not a directory, and the Agents window opens
`User/agent-sessions.code-workspace` in the editor's own data directory
(microsoft/vscode at 4d22f4f, `environmentService.ts:280-281`), which the
inventory would class as a scratch directory and so hide the chat's real
project. The workspace file is named in the session-start row instead,
`workspace=<path>`. A `workspace.json` that cannot be read or is not a
JSON object gives one `parser: workspace.json not read (<reason>)` or
`parser: workspace.json is not a JSON object` row at the session's end.

Sync rows (issue 153), so `records_sync` is set; both sources are
written by the Copilot Chat extension:

* `globalStorage/github.copilot-chat/cloudSessions.json`, a JSON object
  `{<chat session id>: {cloudSessionId, cloudTaskId}}`, the sessions
  Copilot Chat's session sync uploaded to the user's GitHub account. The
  file is rewritten on each change and an entry may name a session no
  longer on disk, or one uploaded from another machine. One `system` row
  per entry at the file's modification time, `session_id` the key:
  `session synced: remote session <cloudSessionId> task <cloudTaskId>
  (from User/globalStorage/github.copilot-chat/cloudSessions.json, file
  mtime)`. A file that is not a JSON object is one `parser:` row.
* `globalStorage/state.vscdb`, read through `vscode_state.read_item`:
  the `ItemTable` row keyed `GitHub.copilot-chat` (the extension's global
  state) holds `github.copilot.cloudAgent.ownedTasks`, `{<taskId>:
  {recordedAt (ms), application?}}` or, in the older form, `{<taskId>:
  <recordedAt>}`, the cloud agent tasks this install started on GitHub's
  servers. One `system` row per task at `recordedAt`, `session_id`
  `copilot-cloud-agent:/task/<taskId>`: `session synced: cloud agent
  task <taskId> application=<application> (from state.vscdb
  GitHub.copilot-chat github.copilot.cloudAgent.ownedTasks, recordedAt)`.
  The task began on GitHub's servers rather than being uploaded from
  here, but GitHub holds its copy all the same, so it is a sync row and
  the task's session reads `synced` `yes`. Its origin is a second row at
  the same time and session: `session origin: remote GitHub cloud agent
  (from state.vscdb GitHub.copilot-chat
  github.copilot.cloudAgent.ownedTasks, recordedAt)`, so `records_origin`
  is set and the task's session reads `origin` `remote`, every other VS
  Code session `local`. A damaged database or a value that is not JSON is
  one `parser:` row; no other key is read.

An absent value prints `-` in both.

Errors (issue 136), after the session's other rows, each a `system` row
through `error_rows` in `base.py`: a `.jsonl` line that does not decode, or
that decodes but whose mutation cannot be applied, carries the line in full
with its line number, as `parser: unparseable line (<reason>): <line>` or
`parser: mutation not applied (<why>): <line>`; a `.json` file that does not
decode is `parser: file is not valid JSON (<reason>)`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

from ..inputs import Artifact
from ..model import Row, compact
from ..timeutil import to_utc
from ..vscode_state import read_item
from .antigravity import uri_to_path
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    file_mtime,
    line_text,
    setting_value,
    track_change,
)

USER_DIR = (
    r"^(?:(?:\.config|Library/Application Support|AppData/Roaming)/(?:Code[^/]*|VSCodium[^/]*|Positron|Trae[^/]*)"
    r"|\.vscode-server[^/]*/data|\.vscodium-server[^/]*/data|\.positron-server/data)/User/"
)
SESSION_RX = re.compile(
    USER_DIR + r"(?:workspaceStorage/[^/]+/chatSessions/[^/]+\.jsonl?"
    r"|globalStorage/emptyWindowChatSessions/[^/]+\.jsonl?"
    r"|globalStorage/transferredChatSessions/[^/]+\.json)$"
)

CLOUD_SESSIONS_RX = re.compile(
    USER_DIR + r"globalStorage/github\.copilot-chat/cloudSessions\.json$"
)
STATE_RX = re.compile(USER_DIR + r"globalStorage/state\.vscdb$")
COPILOT_STATE_KEY = "GitHub.copilot-chat"
OWNED_TASKS_KEY = "github.copilot.cloudAgent.ownedTasks"


class MutationError(ValueError):
    pass


def apply_mutation(state, rec: dict):
    """Apply one mutation-log record to `state` and return the new state."""
    kind = rec.get("kind")
    if kind == 0:
        return rec.get("v")
    path = rec.get("k")
    if not isinstance(path, list) or (not path and kind != 2):
        raise MutationError("bad path %r" % (path,))
    if kind == 2 and not path:
        target = state
    else:
        parent = _walk(state, path[:-1])
        key = path[-1]
        if kind == 1:
            _set(parent, key, rec.get("v"))
            return state
        if kind == 3:
            try:
                del parent[key]
            except (KeyError, IndexError, TypeError):
                pass
            return state
        if kind != 2:
            raise MutationError("unknown kind %r" % (kind,))
        try:
            target = parent[key]
        except (KeyError, IndexError, TypeError):
            target = None
        if target is None:
            target = []
            _set(parent, key, target)
    if not isinstance(target, list):
        raise MutationError("push to non-list at %r" % (path,))
    if isinstance(rec.get("i"), int):
        del target[rec["i"] :]
    items = rec.get("v")
    target.extend(items if isinstance(items, list) else [items])
    return state


def _walk(state, path):
    cur = state
    for k in path:
        try:
            cur = cur[k]
        except (KeyError, IndexError, TypeError):
            raise MutationError("path %r not found" % (path,)) from None
    return cur


def _set(parent, key, value):
    if isinstance(parent, list) and isinstance(key, int):
        if key == len(parent):
            parent.append(value)
        elif 0 <= key < len(parent):
            parent[key] = value
        else:
            raise MutationError("index %r out of range" % (key,))
    elif isinstance(parent, dict):
        parent[key] = value
    else:
        raise MutationError("cannot set %r" % (key,))


def md_text(v) -> str:
    """An IMarkdownString (`{value}`), a plain string or a list of either."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        val = v.get("value")
        return val if isinstance(val, str) else ""
    if isinstance(v, list):
        return "\n".join(md_text(x) for x in v)
    return str(v)


def uri_text(u) -> str:
    """A serialized URI (`{scheme, path, ...}` or `{$mid, fsPath}`), a URI
    string, or a location `{uri, range}`."""
    if isinstance(u, str):
        return uri_to_path(u)
    if isinstance(u, dict):
        if "uri" in u:
            return uri_text(u["uri"])
        for k in ("fsPath", "path", "external"):
            if isinstance(u.get(k), str):
                return u[k]
    return compact_json(u) if u is not None else ""


def tool_call_text(part: dict) -> str:
    tsd = part.get("toolSpecificData")
    if isinstance(tsd, dict):
        cl = tsd.get("commandLine")
        if isinstance(cl, dict) and (cl.get("userEdited") or cl.get("original")):
            return str(cl.get("userEdited") or cl.get("original"))
        if "rawInput" in tsd:
            raw = tsd["rawInput"]
            return raw if isinstance(raw, str) else compact_json(raw)
    rd = part.get("resultDetails")
    if isinstance(rd, dict) and isinstance(rd.get("input"), str) and rd["input"]:
        return rd["input"]
    return md_text(part.get("invocationMessage"))


# `ToolConfirmKind`, a const enum serialised as its number
# (chatService.ts:870-877 at d7622a529314).
TOOL_CONFIRM_KINDS = (
    "Denied",
    "ConfirmationNotNeeded",
    "Setting",
    "LmServicePerTool",
    "UserAction",
    "Skipped",
)


def confirmed_text(part: dict) -> str:
    """The `permission decision:` text for a tool invocation's `isConfirmed`,
    or "" when the invocation records none."""
    v = part.get("isConfirmed")
    if v is None:
        return ""
    if isinstance(v, dict):
        kind = v.get("type")
        if (
            isinstance(kind, int)
            and not isinstance(kind, bool)
            and 0 <= kind < len(TOOL_CONFIRM_KINDS)
        ):
            value = "%s(%d)" % (TOOL_CONFIRM_KINDS[kind], kind)
        else:
            value = setting_value(kind)
        pairs = [
            "%s=%s" % (k, setting_value(x))
            for k, x in v.items()
            if k not in ("type", "reason") and x is not None
        ]
        reason = md_text(v.get("reason"))
    else:
        value, pairs, reason = setting_value(v), [], ""
    src = part.get("source")
    if isinstance(src, dict) and src.get("type"):
        pairs.append("tool_source=%s" % setting_value(src["type"]))
    text = " ".join(["permission decision: confirmed=" + value, *pairs])
    return "%s reason=%s" % (text, reason) if reason else text


def confirmation_part_text(part: dict) -> str:
    """The `permission decision:` text for a `confirmation` response part."""
    pairs = ["permission decision: confirmation"]
    if "isUsed" in part:
        pairs.append("isUsed=%s" % setting_value(bool(part.get("isUsed"))))
    if isinstance(part.get("buttons"), list):
        pairs.append("buttons=%s" % compact_json(part["buttons"]))
    if part.get("title"):
        pairs.append("title=%s" % setting_value(part["title"]))
    msg = md_text(part.get("message"))
    return " ".join(pairs) + ("\n" + msg if msg else "")


def tool_result_text(part: dict) -> str:
    rd = part.get("resultDetails")
    text = ""
    is_error = bool(part.get("resultError"))
    if isinstance(rd, dict):
        out = rd.get("output")
        if isinstance(out, list):
            vals = []
            for o in out:
                if isinstance(o, dict):
                    v = o.get("value", o.get("text"))
                    vals.append(v if isinstance(v, str) else compact_json(v))
                elif isinstance(o, str):
                    vals.append(o)
            text = "\n".join(vals)
        elif out is not None:
            text = out if isinstance(out, str) else compact_json(out)
        is_error = is_error or bool(rd.get("isError"))
    elif isinstance(rd, list):
        text = "\n".join(uri_text(u) for u in rd)
    if part.get("resultError"):
        err = part["resultError"]
        text = "\n".join(x for x in (md_text(err) if not isinstance(err, bool) else "", text) if x)
    if not text:
        text = md_text(part.get("pastTenseMessage"))
    if not text and part.get("isComplete") is False:
        text = "[incomplete]"
    return ("[error] " + text) if is_error else text


class VsCodeParser(Parser):
    agent = "vscode"
    name = "vscode"
    records_sync = True
    records_origin = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return bool(SESSION_RX.match(rel) or CLOUD_SESSIONS_RX.match(rel) or STATE_RX.match(rel))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if CLOUD_SESSIONS_RX.match(artifact.rel):
            yield from self._parse_cloud_sessions(artifact)
            return
        if STATE_RX.match(artifact.rel):
            yield from self._parse_owned_tasks(artifact)
            return
        req_lines: dict[int, int] = {}
        errors: list = []
        if artifact.rel.endswith(".jsonl"):
            state = self._replay(artifact, req_lines, errors)
        else:
            try:
                with open(artifact.disk_path, "rb") as fh:
                    state = json.loads(fh.read().decode("utf-8", errors="replace"))
            except ValueError as e:
                state = None
                errors.append((0, "file is not valid JSON (%s)" % e, ""))
        if not isinstance(state, dict):
            state = {}
        session_id = str(state.get("sessionId") or Path(artifact.rel).name.rsplit(".", 1)[0])
        folder, workspace_file = self._workspace_folder(artifact, errors)
        project = uri_to_path(str(state.get("workingDirectory") or "")) or folder

        def base(turn_type: str, text: str, ts, line: int, model: str = "") -> Row:
            row = self.base_row(artifact)
            row.session_id = session_id
            row.project_path = project
            row.timestamp_utc = to_utc(ts)
            row.source_line = line
            row.model = model
            row.turn_type = turn_type
            row.text = compact(text)
            return row

        if state:
            yield base(
                "system",
                " ".join(
                    x
                    for x in (
                        "session start:",
                        "responder=%s" % state["responderUsername"]
                        if state.get("responderUsername")
                        else "",
                        "location=%s" % state["initialLocation"]
                        if state.get("initialLocation")
                        else "",
                        "title=%s" % state["customTitle"] if state.get("customTitle") else "",
                        "workspace=%s" % workspace_file if workspace_file else "",
                    )
                    if x
                ),
                state.get("creationDate"),
                req_lines.get(-1, 0),
            )
        requests = state.get("requests")
        if not isinstance(requests, list):
            requests = []
        seen: dict = {}
        for i, req in enumerate(requests):
            if isinstance(req, dict):
                yield from self._request_rows(req, req_lines.get(i, 0), base, opts, seen)
        yield from error_rows(self, artifact, errors, session_id, project)

    def _system_row(self, artifact: Artifact, session_id: str, ts: str, text: str) -> Row:
        row = self.base_row(artifact)
        row.session_id, row.timestamp_utc, row.turn_type = session_id, ts, "system"
        row.text = compact(text)
        return row

    def _parse_cloud_sessions(self, artifact: Artifact) -> Iterator[Row]:
        """`cloudSessions.json`: one sync row per entry at the file's
        modification time, or one `parser:` row when it is not a JSON
        object."""
        ts = file_mtime(artifact)
        try:
            with open(artifact.disk_path, "rb") as fh:
                doc = json.loads(fh.read().decode("utf-8", errors="replace"))
        except ValueError as e:
            doc = e
        if not isinstance(doc, dict):
            why = " (%s)" % doc if isinstance(doc, ValueError) else ""
            row = self._system_row(
                artifact, "", ts, "parser: cloudSessions.json is not a JSON object" + why
            )
            row.source_line = 1
            yield row
            return
        for key, entry in doc.items():
            entry = entry if isinstance(entry, dict) else {}
            row = self._system_row(
                artifact,
                str(key),
                ts,
                "session synced: remote session %s task %s (from "
                "User/globalStorage/github.copilot-chat/cloudSessions.json, file mtime)"
                % (entry.get("cloudSessionId") or "-", entry.get("cloudTaskId") or "-"),
            )
            row.source_line = 1
            yield row

    def _parse_owned_tasks(self, artifact: Artifact) -> Iterator[Row]:
        """`state.vscdb`: a `session synced:` and a `session origin: remote`
        row per cloud agent task in the Copilot Chat global state's
        `ownedTasks`, at `recordedAt`, then a `parser:` row per problem
        reading the database or the value."""
        state, problems = read_item(artifact.disk_path, COPILOT_STATE_KEY)
        tasks = state.get(OWNED_TASKS_KEY) if isinstance(state, dict) else None
        for task_id, entry in tasks.items() if isinstance(tasks, dict) else ():
            if isinstance(entry, dict):
                recorded, application = entry.get("recordedAt"), entry.get("application")
            else:
                recorded, application = entry, None
            session_id, ts = "copilot-cloud-agent:/task/%s" % task_id, to_utc(recorded)
            source = "(from state.vscdb %s %s, recordedAt)" % (COPILOT_STATE_KEY, OWNED_TASKS_KEY)
            yield self._system_row(
                artifact,
                session_id,
                ts,
                "session synced: cloud agent task %s application=%s %s"
                % (task_id, application or "-", source),
            )
            yield self._system_row(
                artifact, session_id, ts, "session origin: remote GitHub cloud agent " + source
            )
        for problem in problems:
            yield self._system_row(artifact, "", "", "parser: " + problem)

    def _replay(self, artifact: Artifact, req_lines: dict[int, int], errors: list):
        """Replay a `.jsonl` mutation log and return the session state. A
        line that does not decode, or whose mutation does not apply, is
        appended to `errors` as (line, reason, line text) and skipped;
        `iter_jsonl` is not used because a mutation error needs the line's
        text too."""
        state = None
        with open(artifact.disk_path, "rb") as fh:
            for n, raw in enumerate(fh, 1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    rec = json.loads(stripped.decode("utf-8", errors="replace"))
                except ValueError as e:
                    errors.append((n, "unparseable line (%s)" % e, line_text(raw)))
                    continue
                if not isinstance(rec, dict):
                    continue
                try:
                    state = apply_mutation(state, rec)
                except MutationError as e:
                    errors.append((n, "mutation not applied (%s)" % e, line_text(raw)))
                    continue
                self._track(rec, state, n, req_lines)
        return state

    @staticmethod
    def _track(rec: dict, state, n: int, req_lines: dict[int, int]) -> None:
        """Remember the log line that created each request."""
        kind, path = rec.get("kind"), rec.get("k") or []
        if kind == 0:
            req_lines.clear()
            req_lines[-1] = n
            reqs = state.get("requests") if isinstance(state, dict) else None
            for i in range(len(reqs) if isinstance(reqs, list) else 0):
                req_lines[i] = n
        elif path == ["requests"]:
            reqs = state.get("requests") if isinstance(state, dict) else None
            total = len(reqs) if isinstance(reqs, list) else 0
            start = 0
            if kind == 2:
                start = (
                    rec["i"] if isinstance(rec.get("i"), int) else total - len(rec.get("v") or [])
                )
            for i in list(req_lines):
                if i >= start:
                    del req_lines[i]
            for i in range(max(start, 0), total):
                req_lines[i] = n
        elif kind == 1 and len(path) == 2 and path[0] == "requests" and isinstance(path[1], int):
            req_lines[path[1]] = n

    @staticmethod
    def _workspace_folder(artifact: Artifact, errors: list) -> tuple[str, str]:
        """The sibling `workspace.json`'s `folder` and `workspace` as paths.

        Returns `(folder, workspace_file)`, either empty when absent; only
        the folder may become the project path (issue 185). A
        `workspace.json` that cannot be read or is not a JSON object adds
        one whole-file entry to `errors`.
        """
        parts = artifact.rel.split("/")
        if len(parts) < 4 or parts[-2] != "chatSessions" or parts[-4] != "workspaceStorage":
            return "", ""
        ws = artifact.disk_path.parent.parent / "workspace.json"
        try:
            if ws.is_symlink() or not ws.is_file():
                return "", ""
            with open(ws, "rb") as fh:
                data = json.loads(fh.read().decode("utf-8", errors="replace"))
        except (OSError, ValueError) as e:
            errors.append((0, "workspace.json not read (%s)" % e, ""))
            return "", ""
        if not isinstance(data, dict):
            errors.append((0, "workspace.json is not a JSON object", ""))
            return "", ""
        return (
            uri_to_path(str(data.get("folder") or "")),
            uri_to_path(str(data.get("workspace") or "")),
        )

    def _request_rows(self, req: dict, line: int, base, opts: Options, seen: dict) -> Iterator[Row]:
        model = str(req.get("modelId") or "")
        req_ts = req.get("timestamp")
        # One file is one session, so the tracked keys need no session id.
        t = track_change("model", seen, "model", model)
        if t:
            yield base("system", t, req_ts, line, model)
        mode_info = req.get("modeInfo")
        mode = mode_info.get("telemetryModeId") if isinstance(mode_info, dict) else None
        t = track_change("permission mode", seen, "mode", setting_value(mode) if mode else "")
        if t:
            yield base("system", t, req_ts, line, model)
        resp_ts = req.get("responseTimestamp") or req_ts
        msg = req.get("message")
        text = (
            msg
            if isinstance(msg, str)
            else (msg.get("text") if isinstance(msg, dict) else "") or ""
        )
        names = []
        vd = req.get("variableData")
        for v in (vd.get("variables") if isinstance(vd, dict) else None) or []:
            if isinstance(v, dict) and v.get("name"):
                names.append(str(v["name"]))
        if names:
            text = "%s\n[attached: %s]" % (text, ", ".join(names))
        if req.get("isSystemInitiated"):
            yield base("system", "system initiated: " + text, req_ts, line, model)
        else:
            yield base("user", text, req_ts, line, model)
        if isinstance(req.get("confirmation"), str) and req["confirmation"]:
            yield base(
                "system",
                "permission decision: confirmation=" + req["confirmation"],
                req_ts,
                line,
                model,
            )

        response = req.get("response")
        if isinstance(response, (str, dict)):
            response = [response]
        run: list[str] = []

        def flush():
            joined = "".join(run).strip()
            del run[:]
            if joined:
                return base("assistant", joined, resp_ts, line, model)
            return None

        for part in response or []:
            if isinstance(part, str):
                run.append(part)
                continue
            if not isinstance(part, dict):
                continue
            kind = part.get("kind")
            if kind is None and "value" in part:
                run.append(md_text(part))
                continue
            if kind == "markdownContent":
                run.append(md_text(part.get("content")))
                continue
            if kind == "inlineReference":
                run.append(str(part.get("name") or uri_text(part.get("inlineReference"))))
                continue
            row = flush()
            if row:
                yield row
            if kind == "thinking":
                if opts.include_thinking:
                    t = md_text(part.get("value"))
                    if t:
                        yield base("thinking", t, resp_ts, line, model)
            elif kind == "toolInvocationSerialized":
                tid = str(part.get("toolCallId") or "")
                tname = str(part.get("toolId") or "")
                use = base("tool_use", tool_call_text(part), resp_ts, line, model)
                use.tool_name, use.tool_use_id = tname, tid
                yield use
                res = base("tool_result", tool_result_text(part), resp_ts, line, model)
                res.tool_name, res.tool_use_id = tname, tid
                yield res
                decision = confirmed_text(part)
                if decision:
                    dec = base("system", decision, resp_ts, line, model)
                    dec.tool_name, dec.tool_use_id = tname, tid
                    yield dec
            elif kind == "confirmation":
                yield base("system", confirmation_part_text(part), resp_ts, line, model)
            elif kind == "textEditGroup":
                yield base("system", "edit: " + uri_text(part.get("uri")), resp_ts, line, model)
        row = flush()
        if row:
            yield row
        result = req.get("result")
        err = result.get("errorDetails") if isinstance(result, dict) else None
        if isinstance(err, dict) and err.get("message"):
            yield base("system", "error: %s" % err["message"], resp_ts, line, model)
        elif req.get("isCanceled"):
            yield base("system", "canceled", resp_ts, line, model)


__all__ = [
    "VsCodeParser",
    "apply_mutation",
    "confirmation_part_text",
    "confirmed_text",
    "tool_call_text",
    "tool_result_text",
]
