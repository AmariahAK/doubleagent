# nanobot transcript schema

Catalog agent: `nanobot`. nanobot stores each conversation as a JSONL file of
OpenAI chat-completions messages behind one metadata line, rewritten whole on
every save. Path research is in
[../../collectors/research/nanobot.md](../../collectors/research/nanobot.md).

## 1. Source

[HKUDS/nanobot](https://github.com/HKUDS/nanobot) at [`acdae3d0ae2714b6dde672428e921dbf705c096f`](https://github.com/HKUDS/nanobot/commit/acdae3d0ae2714b6dde672428e921dbf705c096f) (2026-10-04,
`nanobot-ai` 0.3.5), MIT, open source.

## 2. Transcript files

Home-relative; `.nanobot` may be `.nanobot-<instance>` when `--config` points
elsewhere ([`nanobot/config/paths.py:20-27`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L20-L27)).

- `.nanobot/sessions/<workspace-id>/<stem>.jsonl`: one file per session key.
  `<workspace-id>` is 32 hex characters; `<stem>` is the URL-safe base64 of the
  session key without padding ([`nanobot/session/manager.py:74`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L74),[`903-924`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L903-L924)), so
  `cli:direct` is `Y2xpOmRpcmVjdA.jsonl`. The sibling `.workspace` file gives
  the workspace path ([`:606-607`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L606-L607)).
- Sidecar `<stem>.checkpoint.json`: volatile mid-turn checkpoint, deleted on
  the next full save ([`:60`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L60),[`926-927`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L926-L927),[`1233-1235`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L1233-L1235)). Not a transcript.
- Legacy: `.nanobot/sessions/<key with ":" → "_">.jsonl` (global, before
  per-workspace namespaces) and `<workspace>/sessions/*.jsonl` (older still),
  both migrated into the namespaced directory ([`config/paths.py:69-71`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L69-L71);
  [`session/manager.py:806-855`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L806-L855),[`929-933`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L929-L933)). Same record format. Conflicting copies
  are kept in `.migration-conflicts/` ([`:777-779`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L777-L779)).
- `<workspace>/memory/history.jsonl`: compressed long-term journal, lines
  `{cursor, timestamp: "YYYY-MM-DD HH:MM", content, session_key?}`
  ([`agent/memory.py:311-322`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/memory.py#L311-L322)); legacy `memory/HISTORY.md`.
- `.nanobot/webui/<safe key>.jsonl` and `<safe key>.segments/NNNNNN.jsonl`:
  WebUI display transcript, schema version 3, a rendering mirror of the
  session ([`webui/transcript.py:1`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1),[`31-39`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L31-L39),[`172-188`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L172-L188)). The
  directory is the instance's data directory, so `.nanobot-<instance>/webui/`
  for an instance ([`config/paths.py:20-27`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L20-L27),[`46-48`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L46-L48)). Parsed since analyzer
  0.13.0 as a secondary source; record shape in
  [section 3](#3-record-schema). The legacy `<safe key>.json` snapshot beside
  it ([`webui/transcript.py:186-188`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L186-L188)) is not read: its shape was not traced.
- `.nanobot/history/cli_history`: prompt_toolkit input history, user prompts
  only ([`config/paths.py:64-66`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L64-L66)), always under `~/.nanobot` whatever instance
  runs. Parsed since analyzer 0.13.0 as a secondary source.

## 3. Record schema

Line 1 is metadata ([`session/manager.py:1207-1220`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L1207-L1220)): `{"_type":"metadata", key,
created_at, updated_at, metadata, last_archived, last_consolidated}`. An
optional line 2 is `{"_type":"provider_state", state}` ([`:1221-1226`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L1221-L1226)).
Every other line is one message dict ([`:1227-1228`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L1227-L1228); loader treats any line
without a known `_type` as a message, [`:961-987`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L961-L987)):

- `role`: `user`, `assistant`, `tool` (and `system` if a caller adds one).
- `content`: string, or a list of OpenAI content blocks (`{type:"text",
  text}`; inline images are replaced on save, [`agent/loop.py:2409-2427`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/loop.py#L2409-L2427)).
- `timestamp`: `datetime.now().isoformat()`, **naive local time with no
  zone**, for example `2026-10-01T10:15:02.123456`
  ([`session/manager.py:208-217`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L208-L217); [`agent/loop.py:2430`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/loop.py#L2430)). `created_at` and
  `updated_at` in the metadata line are the same form ([`:177-178`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L177-L178)).
- assistant: `tool_calls: [{id, type:"function", function:{name, arguments
  (JSON string)}, extra_content?, provider_specific_fields?}]`
  ([`providers/base.py:94-112`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/providers/base.py#L94-L112)), `reasoning_content` (thinking text),
  `thinking_blocks` ([`utils/helpers.py:753-771`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/helpers.py#L753-L771)). Empty assistant messages
  are dropped ([`loop.py:2391-2392`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/loop.py#L2391-L2392)).
- tool: `tool_call_id`, `name`, `content` ([`agent/runner.py:541-550`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/runner.py#L541-L550)).
- Flags: `_hidden_history: true` marks the synthetic user message that stands
  in for summarised history ([`session/history_visibility.py:10`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/history_visibility.py#L10);
  [`session/manager.py:219-238`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L219-L238)); `_runtime_context` marks injected runtime
  context on a user message ([`runtime_context.py:14`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/runtime_context.py#L14); [`loop.py:2428-2429`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/loop.py#L2428-L2429)).

No model is recorded per message. The session's model preset is
`metadata._nanobot_model_preset` ([`session/model_selection.py:9`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/model_selection.py#L9)); the
summary is `metadata._last_summary {text, last_active}` and the last
delivery route `metadata.last_channel` ([`session/keys.py:10`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/keys.py#L10),[`38`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/keys.py#L38)).

### WebUI display transcript

The WebUI is nanobot's browser chat interface, served by its gateway over a
WebSocket channel; its chats are sessions with the key `websocket:<chat_id>`
([`webui/session_identity.py:8`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/session_identity.py#L8),[`17-19`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/session_identity.py#L17-L19)). Every transcript append goes
through `webui_session_key(chat_id)` ([`webui/transcript.py:1274-1281`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1274-L1281)), so
only WebUI chats have one. The file stem is `SessionManager.safe_key`, the
key with `:` replaced by `_` and unsafe characters by `_`
([`session/manager.py:899-900`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L899-L900); [`utils/helpers.py:372-374`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/helpers.py#L372-L374)), so
`websocket:chat-1` is `websocket_chat-1.jsonl`, unlike the base64 stem of
the session file ([`:903-904`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L903-L904)).

Layout. Records are appended to the active `<safe key>.jsonl`
([`webui/transcript.py:1075-1086`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1075-L1086),[`1118-1127`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1118-L1127)). After a `turn_end`, when the
file passes 2 MiB, the older turns move into the next numbered
`<safe key>.segments/NNNNNN.jsonl` and the active file is rewritten with the
recent turns only ([`:35-36`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L35-L36),[`629-668`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L629-L668),[`671-711`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L671-L711)); `segments/manifest.json`
indexes the segments. The files hold disjoint turns, not copies of each
other: nanobot reads the segments in order, then the active file
([`:1058-1065`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1058-L1065)).

Records. One JSON object per line, `event` naming it, `chat_id`, the turn
annotations `turn_id`, `turn_phase` and `turn_seq`
([`:1289-1305`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1289-L1305)), and `created_at_ms`, set to `time.time()` in epoch
milliseconds when the record is appended, unless the caller gave one
([`:1089-1106`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1089-L1106)). This is true UTC, unlike every other nanobot time.

- `user`: `text`, optional `media_paths[]`, `cli_apps[]`, `mcp_presets[]`,
  `session_mentions[]` ([`:1494-1530`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1494-L1530)), appended when the WebUI channel accepts
  the message, before the agent turn ([`webui/inbound_commands.py:658-669`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/inbound_commands.py#L658-L669)).
- `message`: `text`, optional `kind` (`tool_hint`, `progress`, `reasoning`),
  `tool_events[]`, `media[]`, `latency_ms`
  ([`channels/websocket/runtime.py:1185-1227`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/websocket/runtime.py#L1185-L1227); [`webui/transcript.py:2245-2278`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L2245-L2278)). No
  `kind` is an assistant reply; `tool_hint` and `progress` are breadcrumbs.
  A tool event is `{version, phase, call_id, name, arguments (an object),
  result, error, files, embeds}`, `phase` `start` when the call is made and
  `end` or `error` when it returns ([`utils/progress_events.py:91-102`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/progress_events.py#L91-L102),[`116-143`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/progress_events.py#L116-L143)).
- `stream_end` and `reasoning_end`: the completed text of a streamed answer
  or reasoning segment in `text`. A `stream_end` with `merge_next` keeps its
  buffer, so the next `stream_end` repeats its text
  ([`channels/websocket/runtime.py:1273-1297`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/websocket/runtime.py#L1273-L1297),[`1338-1377`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/websocket/runtime.py#L1338-L1377)). `delta` and
  `reasoning_delta` chunks are not written ([`webui/transcript.py:1229-1247`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1229-L1247));
  older files may hold them, folded into the end record at `turn_end`
  ([`:325-362`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L325-L362)).
- `file_edit`: `edits[]` of `{version, call_id, tool, path, absolute_path,
  phase, added, deleted, approximate, status, binary?, operation?}`
  ([`channels/websocket/runtime.py:1304-1321`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/websocket/runtime.py#L1304-L1321); [`utils/file_edit_events.py:531-558`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/file_edit_events.py#L531-L558)).
- `turn_end` (`latency_ms`, `usage`, `round_usages`,
  `context_window_tokens`), `context_compaction` (`compaction_id`,
  `phase`), and `fork_marker`, the boundary where a forked chat starts
  ([`webui/transcript.py:2289-2326`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L2289-L2326),[`1361-1369`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1361-L1369)).

A fork writes the target's transcript from the source's rows or from the
truncated session messages, `user` and `message` only, every record then
stamped at the fork ([`:1319-1358`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1319-L1358),[`1372-1407`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L1372-L1407)).

### CLI input history

`nanobot agent` reads input through a prompt_toolkit `PromptSession` with a
`FileHistory` on `~/.nanobot/history/cli_history`
([`cli/terminal.py:86-95`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/terminal.py#L86-L95),[`182-188`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/terminal.py#L182-L188)). The format is the one Aider's input history
uses ([`aider.md`](aider.md)): an entry is a `# <local timestamp>` line
followed by one `+<line>` per input line. The timestamp is naive host local
time, the same convention as the session files. No session key or
workspace is written, and the file is shared by every CLI session.

### Memory journal

`memory/history.jsonl` is not a copy of session events. An entry is a
summary the model wrote of archived messages
([`agent/memory.py:1006-1007`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/memory.py#L1006-L1007)) or, when summarising fails, a `[RAW] <n>
messages` block of several formatted messages
([`:627-647`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/memory.py#L627-L647),[`649-672`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/memory.py#L649-L672)), stamped to the minute
([`:311-324`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/memory.py#L311-L324)).

## 4. Joins

- Session: file = metadata `key`. Keys are `<channel>:<chat_id>`, or
  `unified:default`, `heartbeat`, `cli:direct` ([`session/keys.py:8-9`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/keys.py#L8-L9),[`23-27`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/keys.py#L23-L27);
  [`cli/agent.py:146`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/agent.py#L146)). The channel and chat id identify the external sender.
- Project: `.workspace` in the same directory.
- Tool call to result: `tool_calls[].id` = `tool_call_id`.
- Model: by time, against `.nanobot/llm_usage.sqlite3` `llm_calls.started_at_ms`
  (UTC epoch ms, [`providers/base.py:1283`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/providers/base.py#L1283); [`llm_usage/store.py:196-218`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/llm_usage/store.py#L196-L218)), which also
  gives the host's clock offset.
- Subagents: not persisted as separate session files as far as traced.
- WebUI transcript to session file: session key `websocket:` + `chat_id`
  = the session file's metadata `key`; its file is
  `sessions/<workspace-id>/<base64 of the key>.jsonl`, whose `.workspace`
  gives the project. Tool calls join on `call_id` = `tool_calls[].id`.
  Text: the WebUI `user` text is the typed message, while the session's
  copy has any runtime context (a quoted reply, an automation template)
  appended ([`runtime_context.py:120-145`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/runtime_context.py#L120-L145); [`agent/loop.py:693-699`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/loop.py#L693-L699)), so
  those two differ. Time: the session user message is stamped when it is
  persisted at the start of the turn ([`agent/loop.py:663-705`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/loop.py#L663-L705);
  [`session/manager.py:208-217`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L208-L217)), its assistant and tool messages when the turn
  is saved at its end ([`agent/loop.py:2430`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/loop.py#L2430)), all in host local time; the
  WebUI stamps each record in true UTC as it streams. The two differ by
  the host's UTC offset (at most 14 hours) plus up to the turn's length.
- CLI history to session file: text and time only; the CLI's session key
  is `cli:direct` unless `--session` names another ([`cli/agent.py:146`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/agent.py#L146)),
  and the file records neither. The entry is written when the prompt is
  submitted and the session user message at the start of the turn, both
  in local time.
- What each survives. `/new` empties the session file and leaves the WebUI
  transcript ([`command/builtin.py:314-346`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/command/builtin.py#L314-L346)), so the WebUI turns
  before it survive only there and in the memory journal's summary.
  Deleting a WebUI chat deletes the session file and the transcript
  together ([`webui/ws_http.py:1250-1251`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/ws_http.py#L1250-L1251); [`webui/thread_disk.py:19-31`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/thread_disk.py#L19-L31)). The
  CLI history survives `/new` and any session deletion; nothing in the
  traced source truncates it.

## 5. SQLite or binary stores

None for transcripts. `llm_usage.sqlite3` (WAL, [`store.py:190`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/llm_usage/store.py#L190)) holds only
call metadata.

## 6. Format versions

No version field in session files. The metadata line writes both
`last_archived` and the older `last_consolidated` for downgrade
compatibility ([`session/manager.py:1215-1218`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L1215-L1218)). Legacy file names differ ([section 2](#2-transcript-files)).
`Session.clear()` empties the messages and the next save rewrites the file
([`:374-380`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L374-L380)), so a `/new` in a chat erases the previous transcript; only
`memory/history.jsonl` and the WebUI mirror keep a trace.

## 7. Secrets

`provider_state.state` is opaque provider conversation state. Tool `content`
holds raw tool output. `tool_calls[].function.arguments` can contain whatever
the agent passed to a shell. Credentials themselves are not in session files.

## 8. Parser plan

Globs (home-relative): `.nanobot*/sessions/*/*.jsonl`,
`.nanobot*/sessions/*.jsonl`, `.nanobot*/sessions/*/.migration-conflicts/*.jsonl`.
Skip `*.checkpoint.json`. Read `.workspace` from the same directory.

**Timestamps are host local time.** The collector does not record the host
zone, so follow the aider parser's documented convention (local time emitted
as if UTC, stated in its [subsection of the agents page](../../docs/agents.md#aider)) and let the analyst correct it;
`llm_usage.sqlite3` gives true UTC for the same calls to derive the offset.

| Column | Source |
| --- | --- |
| timestamp_utc | message `timestamp` (naive local; see above) |
| session_id | metadata `key` |
| project_path | `.workspace` file content |
| git_branch | empty |
| turn_type | `user` → user (`_hidden_history` → system); `assistant` → assistant, plus tool_use per `tool_calls[]`, thinking from `reasoning_content`; `tool` → tool_result |
| model | empty, or `metadata._nanobot_model_preset` |
| tool_name | `tool_calls[].function.name` / tool `name` |
| tool_use_id | `tool_calls[].id` / `tool_call_id` |
| text | `content` text; for tool_use the `command`/`path`/`url` key of the parsed `arguments`, else the arguments string |
| source_line | line number |

Model and permission rows (issues 96 and 97): when the metadata line has
`metadata._nanobot_model_preset`, a `system` row `model: <preset>
(preset)` follows the session start row at its time; the value names a
model preset of nanobot's configuration, not a model id, and the row says
so. A session file has one metadata line, so it names one preset and no
`model: <old> -> <new>` row is written; per-call models are in
`llm_usage.sqlite3` `llm_calls`, which the parser does not read. No
permission state is read: `pairing.json`, the chat senders the operator
approved
([`collectors/research/nanobot.md`](../../collectors/research/nanobot.md)),
is named in the research without its shape, so the file is not read.

Sources, primary or secondary (issue 122; every one read on every run):

| File | Role | Rows |
| --- | --- | --- |
| `sessions/<workspace-id>/<stem>.jsonl`, legacy and `.migration-conflicts/` copies | primary | as above |
| `<workspace>/memory/history.jsonl` | primary: summaries, not copies of events | one `system` row per entry, `memory history #<cursor>: <content>` |
| `webui/<safe key>.jsonl`, `webui/<safe key>.segments/NNNNNN.jsonl` | secondary, tolerance 15 hours | `user`; `assistant` (`message` with no `kind`, `stream_end` without `merge_next`); `tool_use` and `tool_result` per tool event; `thinking` (opt-in); `system` for breadcrumbs without tool events, finished file edits, `fork_marker`, `context_compaction` and unknown events; nothing for `delta`, `reasoning_delta`, `turn_end` |
| `.nanobot/history/cli_history` | secondary, tolerance 2 seconds | one `user` row per entry at its own time, no session or project |

The WebUI rows carry `created_at_ms` as true UTC, the session file's rows
local time as if UTC; the 15-hour window is the largest UTC offset (14
hours) plus an hour of turn, for the assistant and tool messages the
session stamps at the turn's end. Known misses, each shown twice: a turn
longer than that hour, a forked chat's transcript (every record stamped at
the fork), and a user message whose session copy carries appended runtime
context. A kept WebUI row keeps its true-UTC time.

Fixture, file `.nanobot/sessions/0123456789abcdef0123456789abcdef/dGVsZWdyYW06MTIzNDU2Nzg5.jsonl`,
with `.workspace` containing `/home/alice/.nanobot/workspace`:

```json
{"_type":"metadata","key":"telegram:123456789","created_at":"2026-10-01T10:15:00.000001","updated_at":"2026-10-01T10:15:09.500000","metadata":{"last_channel":"telegram:123456789"},"last_archived":0,"last_consolidated":0}
{"role":"user","content":"what is using port 8080?","timestamp":"2026-10-01T10:15:01.200000"}
{"role":"assistant","content":"","tool_calls":[{"id":"call_abc123","type":"function","function":{"name":"exec","arguments":"{\"command\": \"ss -ltnp | grep 8080\"}"}}],"reasoning_content":"Check listening sockets.","timestamp":"2026-10-01T10:15:04.000000"}
{"role":"tool","tool_call_id":"call_abc123","name":"exec","content":"LISTEN 0 128 *:8080 users:((\"python3\",pid=4242))","timestamp":"2026-10-01T10:15:05.000000"}
{"role":"assistant","content":"python3 (pid 4242) is listening on 8080.","timestamp":"2026-10-01T10:15:09.400000"}
```

Confidence. High: file naming, metadata and message field names, naive
local timestamps, tool call shape. The shell tool is
named `exec` ([`agent/tools/shell.py:247-248`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/tools/shell.py#L247-L248)). Medium: `thinking_blocks` element
shape is provider-defined. High, from source: the WebUI transcript record
shape and layout; medium: that the fixture's pairing holds on a real
install, since no WebUI or CLI history was observed. Not determined: whether
subagent runs are persisted anywhere; the legacy WebUI `<safe key>.json`
snapshot shape.
