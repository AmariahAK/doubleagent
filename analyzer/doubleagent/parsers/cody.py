"""Sourcegraph Cody chat history.

Validated against source, sourcegraph/cody-public-snapshot at 8e20ac6c (see
`research/cody.md`), with a synthetic fixture; no real install was
checked. Every chat of every account lives in one JSON object,
`AccountKeyedChatHistory`, stored in two places:

* VS Code and its forks: the `ItemTable` row `key = 'sourcegraph.cody-ai'`
  of `<editor User dir>/globalStorage/state.vscdb`, whose JSON value is the
  extension's whole global state; the history is its
  `cody-local-chatHistory-v2` member. The catalog attributes that file to
  `vscode`, or to the fork (Cursor, Windsurf, PearAI, Kiro, Antigravity)
  whose `User/` directory it sits in, so this parser lists all of them,
  `vscode_state.EDITOR_AGENTS`, in `reads_agents`.
* The JetBrains plugin (Cody agent): the file
  `Cody-nodejs/[Data/]JetBrains-globalState/cody-local-chatHistory-v2`,
  whose whole content is the JSON history.

Shape: `{"<endpoint>-<username>": {"chat": {"<chatID>": transcript}}}`.
Transcript fields: `id`, `chatTitle`, `lastInteractionTimestamp`,
`interactions[]` of `{humanMessage, assistantMessage}`. Message fields:
`speaker` (`human`, `assistant`, `system`), `text`, `model`, `intent`,
`contextFiles[].uri.fsPath` (or `.path`), `error.message`, `content[]`
parts (`{type: "tool_call", tool_call: {id, name, arguments}}` on the
assistant, `{type: "tool_result", tool_result: {id, content}}` on the
human), and `processes[]` (`{type, id, title, description, content,
state, error.message}`, `type` one of `tool`, `confirmation`, `step`).

Model and permission rows, all `system`: the assistant message `model`
gives `model: <id>` at the first assistant message of a chat that names
one and `model: <old> -> <new>` on every later change, before that
message's rows. A `processes[]` entry of type `confirmation` (a step
that prompted the user; Deep Cody's terminal tool adds one per command,
on the human message) becomes `permission decision: <decision>
confirmation state=<state> error=<error.message> title=<title>` with its
`description` and `content` on the following lines, `tool_use_id` the
entry's `id`. A refusal completes the step with `Error('Command
rejected')`, so `state` `error` with `error.message` `Command rejected` is
`rejected`; an approval never completes the step, so `pending` is
`approved or unanswered`, which the format cannot tell apart. Any other
state keeps the plain `permission decision: confirmation state=<state>`,
with `error=` whenever the step carries an `error.message`.

There is no per-message timestamp. The chat id is the chat's creation time
as `Date.toUTCString()` (`Fri, 03 Oct 2026 10:00:00 GMT`), and every row of
the chat inherits it; a non-date id (pre-migration UUIDs) falls back to
`lastInteractionTimestamp`, which is the same creation time. `session_id`
is the chat id, prefixed with `<account>/` only when the same id occurs
under two accounts of one store. No project path is recorded with a chat;
`project_path` stays empty and the user row lists the context files, since
the parent of one context file is not the project. `processes[]` tool
steps are emitted only when no `tool_call` part has the same id, so an
agentic call is not counted twice. `source_line` is 1 for the JetBrains
file (one JSON value) and 0 for the SQLite row. A history that does not
parse is walked chat by chat, and every interaction decoded before the
damage is still yielded, followed by one `system` row. No git branch.

Settings, model preferences and the legacy JetBrains history were added
from the same commit in the 2026-10-21 source review; every row below is
source-derived and not observed on any real install:

* The editor's `User/settings.json` (JSONC, read with `parse_jsonc` from
  the Gemini CLI parser; the catalog attributes it to the editor, which
  `reads_agents` covers): one `permission setting: <key>=<value> (from
  <file>, file mtime)` row per leaf of the flat keys
  `cody.agentic.context.experimentalOptions` (`shell.allow`,
  `shell.block`), `cody.agentic.context.experimentalShell` and
  `cody.chat.agenticContext`, and per `disabled` and `disabledTools` of
  each `cody.mcpServers.<server>`; an MCP server's `headers`, `env`,
  `url`, `command` and `args` are never read. A settings file that does
  not decode is reported only when its text names a `cody.` key, since
  the file belongs to the editor.
* `cody-model-preferences`, the global-state key in the
  `sourcegraph.cody-ai` row and the file of that name under
  `JetBrains-globalState/`: `{<endpoint>: {defaults: {<usage>: <id>},
  selected: {<usage>: <id>}}}`, one `model setting:
  <selected|defaults>.<usage>=<id> endpoint=<endpoint> (from <file>,
  file mtime)` row per entry (`<file>` followed by ` cody-model-preferences`
  for the database row), the `model` column the id. It records the
  current choice, not when it was made.
* `<project>/.idea/cody_history.xml`, the pre-agent plugin's
  `HistoryService` component, a secondary source (`secondary()`): the
  IntelliJ serialisation of `HistoryState`, `accountData/list/AccountData`
  with `accountId@value` and `chats/list/chat`, or the deprecated top-level
  `chats/list/chat`; each `chat` has `internalId@value`, `updatedAt@value`,
  `accountId@value` (deprecated), `model@value` (deprecated), an `llm`
  element whose `model@value` is the chat's model, and
  `messages/list/message` with `speaker@value` (`HUMAN`, `ASSISTANT`) and
  `text@value`. The migration into the agent store used `updatedAt` as the
  chat id and `llm.model` as every message's model, so the rows take
  `updatedAt` as `session_id` (else `internalId`) and as the time, read as
  UTC like the same string in the agent store: a chat row `chat:
  <internalId> | account=<accountId> | messages=<n> (legacy JetBrains
  history)`, then `model: <id>` before the first assistant message, and
  the user and assistant rows, with `project_path` the project the file
  sits in. The file is read with `xml.etree.ElementTree.iterparse`, so the
  chats before a cut or damaged part are still yielded, followed by one
  `parser:` row; expat resolves no external entity.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from email.utils import parsedate_to_datetime

from ..inputs import Artifact
from ..model import Row, compact
from ..timeutil import to_utc
from ..vscode_state import EDITOR_AGENTS, STATE_DB_RX, read_item
from .base import (
    Options,
    Parser,
    compact_json,
    file_mtime,
    setting_value,
    text_of,
    track_change,
)
from .cline_legacy import iter_array_at, read_text
from .gemini_cli import parse_jsonc

JETBRAINS_RX = re.compile(
    r"(?:^|/)Cody-nodejs/(?:[^/]+/)?JetBrains-globalState/cody-local-chatHistory-v2$"
)
JETBRAINS_PREFS_RX = re.compile(
    r"(?:^|/)Cody-nodejs/(?:[^/]+/)?JetBrains-globalState/cody-model-preferences$"
)
SETTINGS_RX = re.compile(r"(?:^|/)User/settings\.json$")
LEGACY_RX = re.compile(r"(?:^|/)\.idea/cody_history\.xml$")
ITEM_KEY = "sourcegraph.cody-ai"
HISTORY_KEY = "cody-local-chatHistory-v2"
PREFS_KEY = "cody-model-preferences"
# Flat `settings.json` keys whose leaves are permission settings.
PERMISSION_KEYS = (
    "cody.agentic.context.experimentalOptions",
    "cody.agentic.context.experimentalShell",
    "cody.chat.agenticContext",
)
MCP_KEY = "cody.mcpServers"
MCP_FIELDS = ("disabled", "disabledTools")
REJECTED = "Command rejected"

_DATE_KEY = (
    r'"((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2} GMT)"\s*:\s*\{'
)
_ACCOUNT_KEY = r'"([^"\\]+)"\s*:\s*\{\s*"chat"\s*:\s*\{'


def chat_time(chat_id: str, fallback) -> str:
    """UTC timestamp of a `toUTCString()` chat id, else of `fallback`."""
    for v in (chat_id, fallback):
        if isinstance(v, str) and v:
            try:
                return to_utc(parsedate_to_datetime(v).isoformat())
            except (TypeError, ValueError, IndexError):
                pass
            ts = to_utc(v)
            if ts:
                return ts
    return ""


def recover_history(text: str) -> tuple[dict, str]:
    """Rebuild what can be read from a damaged history text: each chat whose
    key is a `toUTCString()` date, with the interactions that decode."""
    out: dict[str, dict] = {}
    marks = [(m.start(), "account", m.group(1)) for m in re.finditer(_ACCOUNT_KEY, text)]
    marks += [(m.end(), "chat", m.group(1)) for m in re.finditer(_DATE_KEY, text)]
    marks.sort()
    account = ""
    chats = 0
    for i, (pos, kind, name) in enumerate(marks):
        if kind == "account":
            account = name
            continue
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        m = re.compile(r'"interactions"\s*:\s*').search(text, pos, end)
        interactions = []
        if m:
            errs: list = []
            interactions = [v for _, v in iter_array_at(text, m.end(), errs) if isinstance(v, dict)]
        title = re.compile(r'"chatTitle"\s*:\s*("(?:[^"\\]|\\.)*")').search(text, pos, end)
        chat = {"id": name, "interactions": interactions}
        if title:
            try:
                chat["chatTitle"] = json.loads(title.group(1))
            except ValueError:
                pass
        out.setdefault(account, {"chat": {}})["chat"][name] = chat
        chats += 1
    return out, "chat history did not parse; recovered %d chat(s)" % chats


def _fs_path(uri) -> str:
    if isinstance(uri, str):
        return uri
    if isinstance(uri, dict):
        for k in ("fsPath", "path", "external"):
            if isinstance(uri.get(k), str) and uri[k]:
                return uri[k]
    return ""


def _confirmation_head(proc: dict) -> str:
    """First line of the permission row for a `confirmation` process step.

    A refusal completes the step with `Error('Command rejected')`, so it is
    saved as `state` `error` with that `error.message`; an approval never
    completes the step, so `pending` is an approval or an unanswered request.
    """
    state = proc.get("state")
    err = proc.get("error")
    message = err.get("message") if isinstance(err, dict) else err
    message = setting_value(message) if message else ""
    if state == "error" and message == REJECTED:
        decision = "rejected"
    elif state == "pending":
        decision = "approved or unanswered"
    else:
        decision = "confirmation"
    head = "permission decision: %s" % decision
    if decision != "confirmation":
        head += " confirmation"
    if state:
        head += " state=%s" % setting_value(state)
    if message:
        head += " error=%s" % message
    if proc.get("title"):
        head += " title=%s" % setting_value(proc["title"])
    return head


def _leaves(prefix: str, value) -> list[tuple[str, object]]:
    """(dotted key, value) for each leaf of a settings value; an empty
    object is a leaf of its own."""
    if isinstance(value, dict) and value:
        out: list[tuple[str, object]] = []
        for k, v in value.items():
            out.extend(_leaves("%s.%s" % (prefix, k), v))
        return out
    return [(prefix, value)]


def settings_entries(doc: dict) -> list[tuple[str, object]]:
    """The permission entries of an editor `settings.json`: every leaf of
    `PERMISSION_KEYS`, and `disabled` and `disabledTools` of each MCP server
    (never its headers, env, url or command)."""
    out: list[tuple[str, object]] = []
    for key in PERMISSION_KEYS:
        if key in doc:
            out.extend(_leaves(key, doc[key]))
    servers = doc.get(MCP_KEY)
    for name, conf in servers.items() if isinstance(servers, dict) else ():
        if isinstance(conf, dict):
            for field in MCP_FIELDS:
                if field in conf:
                    out.append(("%s.%s.%s" % (MCP_KEY, name, field), conf[field]))
    return out


def pref_entries(prefs) -> list[tuple[str, str, str, str]]:
    """(kind, usage, model id, endpoint) for each entry of a
    `cody-model-preferences` value, the user's `selected` before the
    server's `defaults`."""
    out: list[tuple[str, str, str, str]] = []
    for endpoint, entry in prefs.items() if isinstance(prefs, dict) else ():
        if not isinstance(entry, dict):
            continue
        for kind in ("selected", "defaults"):
            usages = entry.get(kind)
            for usage, model in usages.items() if isinstance(usages, dict) else ():
                if isinstance(model, str) and model:
                    out.append((kind, str(usage), model, str(endpoint)))
    return out


def _value(elem, tag: str) -> str:
    """The `value` attribute of `elem`'s direct child `tag`, or ""."""
    child = elem.find(tag)
    return (child.get("value") or "") if child is not None else ""


class CodyParser(Parser):
    agent = "cody"
    name = "cody"
    reads_agents = EDITOR_AGENTS
    has_secondary = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return any(
            rx.search(rel)
            for rx in (STATE_DB_RX, JETBRAINS_RX, JETBRAINS_PREFS_RX, SETTINGS_RX, LEGACY_RX)
        )

    def secondary(self, artifact: Artifact) -> bool:
        return bool(LEGACY_RX.search(artifact.rel))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if SETTINGS_RX.search(artifact.rel):
            yield from self._settings_rows(artifact)
            return
        if JETBRAINS_PREFS_RX.search(artifact.rel):
            yield from self._prefs_file_rows(artifact)
            return
        if LEGACY_RX.search(artifact.rel):
            yield from self._legacy_rows(artifact)
            return
        problems: list[str] = []
        state = None
        if JETBRAINS_RX.search(artifact.rel):
            line = 1
            text = read_text(artifact.disk_path)
            if text is None:
                yield self._system(artifact, "parser: unreadable history file", line)
                return
            history = self._decode(text, problems)
        else:
            line = 0
            state, problems = read_item(artifact.disk_path, ITEM_KEY)
            if state is None:
                for p in problems:
                    yield self._system(artifact, "parser: " + p, line)
                return
            if isinstance(state, str):  # value did not parse; read_item noted it
                history = recover_history(state)[0]
            else:
                history = state.get(HISTORY_KEY) if isinstance(state, dict) else None
                if isinstance(history, str):
                    history = self._decode(history, problems)
        if isinstance(history, dict):
            yield from self._history_rows(artifact, history, line, opts)
        if isinstance(state, dict):
            source = "%s %s" % (artifact.rel, PREFS_KEY)
            yield from self._prefs_rows(artifact, state.get(PREFS_KEY), source, line)
        for p in problems:
            yield self._system(artifact, "parser: " + p, line)

    def _settings_rows(self, artifact: Artifact) -> Iterator[Row]:
        """`permission setting:` rows from an editor's `User/settings.json`."""
        try:
            raw = artifact.disk_path.read_bytes()
        except OSError:
            return
        try:
            doc = parse_jsonc(raw)
        except ValueError:
            doc = None
        if not isinstance(doc, dict):
            # The file is the editor's; it concerns Cody only if it names Cody.
            if b'"cody.' in raw:
                yield self._system(artifact, "parser: settings.json is not a JSON object", 1)
            return
        ts = file_mtime(artifact)
        for key, value in settings_entries(doc):
            row = self._system(
                artifact,
                compact(
                    "permission setting: %s=%s (from %s, file mtime)"
                    % (key, setting_value(value), artifact.rel)
                ),
                1,
            )
            row.timestamp_utc = ts
            yield row

    def _prefs_file_rows(self, artifact: Artifact) -> Iterator[Row]:
        """`model setting:` rows from `JetBrains-globalState/cody-model-preferences`."""
        text = read_text(artifact.disk_path)
        try:
            prefs = json.loads(text) if text is not None else None
        except ValueError:
            prefs = None
        if not isinstance(prefs, dict):
            yield self._system(artifact, "parser: %s is not a JSON object" % PREFS_KEY, 1)
            return
        yield from self._prefs_rows(artifact, prefs, artifact.rel, 1)

    def _prefs_rows(self, artifact: Artifact, prefs, source: str, line: int) -> Iterator[Row]:
        ts = file_mtime(artifact)
        for kind, usage, model, endpoint in pref_entries(prefs):
            row = self._system(
                artifact,
                "model setting: %s.%s=%s endpoint=%s (from %s, file mtime)"
                % (kind, usage, model, endpoint, source),
                line,
            )
            row.timestamp_utc = ts
            row.model = model
            yield row

    def _legacy_rows(self, artifact: Artifact) -> Iterator[Row]:
        """Rows from a JetBrains project's `.idea/cody_history.xml`, read
        incrementally so the chats before a damaged part survive it."""
        project = artifact.home.original if artifact.home.project else ""
        stack: list[str] = []
        account = ""
        chats = 0
        try:
            with open(artifact.disk_path, "rb") as fh:
                for event, elem in ET.iterparse(fh, events=("start", "end")):
                    if event == "start":
                        stack.append(elem.tag)
                        if elem.tag == "AccountData":
                            account = ""
                        continue
                    stack.pop()
                    if elem.tag == "accountId" and stack and stack[-1] == "AccountData":
                        account = elem.get("value") or ""
                    elif elem.tag == "AccountData":
                        account = ""
                    elif elem.tag == "chat":
                        chats += 1
                        yield from self._legacy_chat(artifact, elem, account, project)
                        elem.clear()
        except (OSError, ET.ParseError) as e:
            row = self._system(
                artifact,
                "parser: cody_history.xml did not parse; read %d chat(s) (%s)" % (chats, e),
                0,
            )
            row.project_path = project
            yield row

    def _legacy_chat(self, artifact: Artifact, chat, account: str, project: str) -> Iterator[Row]:
        internal = _value(chat, "internalId")
        updated = _value(chat, "updatedAt")
        account = account or _value(chat, "accountId")
        model = ""
        llm = chat.find("llm")
        for m in llm.iter("model") if llm is not None else ():
            if m.get("value"):
                model = m.get("value") or ""
                break
        model = model or _value(chat, "model")
        holder = chat.find("messages")
        messages = list(holder.iter("message")) if holder is not None else []
        ts = chat_time(updated, None)

        def row(turn: str, text: str, model_id: str = "") -> Row:
            r = self.base_row(artifact)
            r.timestamp_utc = ts
            r.session_id = updated or internal
            r.project_path = project
            r.source_line = 0
            r.turn_type = turn
            r.model = model_id
            r.text = compact(text)
            return r

        yield row(
            "system",
            "chat: %s | account=%s | messages=%d (legacy JetBrains history)"
            % (internal, account or "-", len(messages)),
        )
        model_shown = False
        for m in messages:
            speaker, text = _value(m, "speaker"), _value(m, "text")
            if speaker == "ASSISTANT":
                if model and not model_shown:
                    model_shown = True
                    yield row("system", "model: " + model, model)
                if text:
                    yield row("assistant", text, model)
            elif speaker == "HUMAN":
                if text:
                    yield row("user", text)
            elif text:
                yield row("system", "message speaker=%s: %s" % (speaker or "-", text))

    @staticmethod
    def _decode(text: str, problems: list[str]):
        try:
            return json.loads(text)
        except ValueError as e:
            history, problem = recover_history(text)
            problems.append("%s (%s)" % (problem, e))
            return history

    def _system(self, artifact: Artifact, text: str, line: int) -> Row:
        row = self.base_row(artifact)
        row.turn_type = "system"
        row.source_line = line
        row.text = text
        return row

    def _history_rows(
        self, artifact: Artifact, history: dict, line: int, opts: Options
    ) -> Iterator[Row]:
        seen: dict[str, int] = {}
        for acct in history.values():
            chats = acct.get("chat") if isinstance(acct, dict) else None
            for cid in chats if isinstance(chats, dict) else {}:
                seen[cid] = seen.get(cid, 0) + 1
        for account, acct in history.items():
            chats = acct.get("chat") if isinstance(acct, dict) else None
            if not isinstance(chats, dict):
                continue
            for cid, chat in chats.items():
                if not isinstance(chat, dict):
                    continue
                sid = str(chat.get("id") or cid)
                if seen.get(cid, 0) > 1:
                    sid = "%s/%s" % (account, sid)
                yield from self._chat_rows(artifact, account, sid, chat, line, opts)

    def _chat_rows(
        self, artifact: Artifact, account: str, sid: str, chat: dict, line: int, opts: Options
    ) -> Iterator[Row]:
        ts = chat_time(str(chat.get("id") or ""), chat.get("lastInteractionTimestamp"))
        interactions = chat.get("interactions")
        interactions = (
            [i for i in interactions if isinstance(i, dict)]
            if isinstance(interactions, list)
            else []
        )

        def row(turn: str, text, model: str = "", name: str = "", tid: str = "") -> Row:
            r = self.base_row(artifact)
            r.timestamp_utc = ts
            r.session_id = sid
            r.source_line = line
            r.turn_type = turn
            r.model = model
            r.tool_name = name
            r.tool_use_id = tid
            r.text = compact(text)
            return r

        yield row(
            "system",
            "chat: %s | account=%s | interactions=%d"
            % (chat.get("chatTitle") or "", account, len(interactions)),
        )
        names: dict[str, str] = {}
        seen: dict = {}
        for it in interactions:
            for key in ("humanMessage", "assistantMessage"):
                msg = it.get(key)
                if isinstance(msg, dict):
                    yield from self._message_rows(msg, row, names, seen)

    def _message_rows(self, msg: dict, row, names: dict[str, str], seen: dict) -> Iterator[Row]:
        speaker = msg.get("speaker")
        model = str(msg.get("model") or "") if speaker == "assistant" else ""
        # `seen` is per chat, so the tracked key needs no session id.
        t = track_change("model", seen, "model", model)
        if t:
            yield row("system", t, model)
        text = msg.get("text")
        text = text if isinstance(text, str) else text_of(text)
        parts = msg.get("content")
        if not isinstance(parts, list):
            parts = []
        if not text:
            text = "\n".join(
                str(p.get("text"))
                for p in parts
                if isinstance(p, dict) and p.get("type") == "text" and p.get("text")
            )
        if speaker == "human":
            files = [
                _fs_path(f.get("uri")) for f in msg.get("contextFiles") or [] if isinstance(f, dict)
            ]
            files = [f for f in files if f]
            if files:
                text = "%s\n[context: %s]" % (text, ", ".join(files))
            if text:
                yield row("user", text)
        elif text:
            yield row("assistant" if speaker == "assistant" else "system", text, model)
        call_ids = set()
        for p in parts:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "tool_call" and isinstance(p.get("tool_call"), dict):
                tc = p["tool_call"]
                tid, name = str(tc.get("id") or ""), str(tc.get("name") or "")
                call_ids.add(tid)
                names[tid] = name
                args = tc.get("arguments")
                yield row(
                    "tool_use",
                    args if isinstance(args, str) else compact_json(args),
                    model,
                    name,
                    tid,
                )
            elif p.get("type") == "tool_result" and isinstance(p.get("tool_result"), dict):
                tr = p["tool_result"]
                tid = str(tr.get("id") or "")
                c = tr.get("content")
                yield row(
                    "tool_result",
                    c
                    if isinstance(c, str)
                    else text_of(c)
                    if isinstance(c, list)
                    else compact_json(c),
                    model,
                    names.get(tid, ""),
                    tid,
                )
        for proc in msg.get("processes") or []:
            if isinstance(proc, dict) and proc.get("type") == "confirmation":
                tid = str(proc.get("id") or "")
                lines = [_confirmation_head(proc)] + [
                    setting_value(proc[k]) for k in ("description", "content") if proc.get(k)
                ]
                yield row("system", "\n".join(lines), model, names.get(tid, ""), tid)
                continue
            if not isinstance(proc, dict) or proc.get("type") != "tool":
                continue
            tid = str(proc.get("id") or "")
            if tid and tid in call_ids:
                continue
            name = str(proc.get("title") or "")
            names[tid] = name
            body = proc.get("content")
            body = body if isinstance(body, str) else compact_json(body) if body is not None else ""
            if proc.get("state") and proc.get("state") != "success":
                body = "[%s] %s" % (proc["state"], body)
            yield row("tool_use", body, model, name, tid)
        err = msg.get("error")
        if isinstance(err, dict) and err.get("message"):
            yield row("system", "error: %s" % err["message"], model)


__all__ = ["CodyParser", "chat_time", "recover_history"]
