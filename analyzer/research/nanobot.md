# nanobot transcript schema

Catalog agent: `nanobot`. nanobot stores each conversation as a JSONL file of
OpenAI chat-completions messages behind one metadata line, rewritten whole on
every save. Path research is in
[../../collectors/research/nanobot.md](../../collectors/research/nanobot.md).

## 1. Source

[HKUDS/nanobot](https://github.com/HKUDS/nanobot) at [`acdae3d0ae2714b6dde672428e921dbf705c096f`](https://github.com/HKUDS/nanobot/commit/acdae3d0ae2714b6dde672428e921dbf705c096f) (2026-10-04,
`nanobot-ai` 0.3.5), MIT, open source.

- **Source review (2026-10-19)** at
  [`909b277`](https://github.com/HKUDS/nanobot/commit/909b277e7a5a7ecd2aebdba9611e5febe86988d9)
  (2026-10-19; `pyproject.toml` still reads 0.3.5, and the session
  database below is marked as introduced in 0.3.6,
  [`session/jsonl_migration.py:1-6`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/jsonl_migration.py#L1-L6)),
  against the
  [`acdae3d`](https://github.com/HKUDS/nanobot/commit/acdae3d0ae2714b6dde672428e921dbf705c096f)
  this document cited. Source only; nothing was installed or run. One
  line per requirement class, detail in [section 2](#2-transcript-files),
  [section 5](#5-sqlite-or-binary-stores) and
  [section 8](#8-parser-plan):
  - Permission state: found, not read. Standing settings only: the
    `tools` block of `config.json` (`restrictToWorkspace`, the exec tool's
    `sandbox`, `allowPatterns` and `denyPatterns`), each channel's
    `allowFrom` list, `pairing.json` (approved chat senders, shape now
    traced) and each WebUI chat's `workspace_scope.access_mode`
    (`restricted` or `full`) in the session metadata. No per-call approval
    exists: the exec tool refuses a command by pattern and says so in the
    tool result.
  - Model: covered in part. The session's model preset is one metadata
    key (covered); a `/model <preset>` switch is kept in the transcript as
    a user and assistant message pair flagged `_command`, whose reply
    names the resolved model, and the parser shows it as two plain rows
    with no `model: <old> -> <new>` row.
  - Past use beyond the primary store: drift and found. Sessions now live
    in `sessions/<workspace-id>/sessions.sqlite3`, which the parser does
    not read; the JSONL files it reads become frozen import sources. New
    unread sources: `jsonl-backup/`, the WebUI sidebar cache, and the
    cron and trigger run records. Memory journal, WebUI transcript and CLI
    history: covered.
  - Sync, relay and origin: relay found and not written. A session whose
    key is `<channel>:<chat_id>` for a messaging channel (Telegram,
    WhatsApp, Discord, Slack, Feishu, email and the others) was carried
    through that platform, and `metadata.last_channel` names the last
    route; the parser puts both in its session start row but writes no
    `session relayed:` row. Sync: none (Langfuse tracing stays opt-in and
    is now wired into the Codex provider too). Origin: none.
  - Scratch directories: found, already classed. The default workspace
    `~/.nanobot/workspace` (and the Docker compose file's
    `~/.nanobot/api-workspace`) is under the `.nanobot*` catalog entry, so
    the analyzer's catalog rule lists it under `scratch_directories`; an
    instance root chosen with the new `--home` option outside `~/.nanobot*`
    is not.
  - Deletion: found. Deleting a WebUI chat removes the session's rows and
    its child sessions' rows from the database, its WebUI transcript and,
    when the user confirms, its scheduled jobs; it leaves the memory
    journal, the CLI history, the cron and trigger run records, the usage
    database and any frozen JSONL copy.
  - Version drift: found. Session store moved from JSONL to SQLite;
    `.migration-conflicts/` and the import of the global pre-namespace
    `sessions/*.jsonl` are gone; `--home` moves `history/cli_history` into
    the chosen instance root. Message, metadata and WebUI record shapes
    are unchanged.
  - Bad lines: covered for every file the parser reads (`iter_jsonl` and
    `read_input_history` report each bad line). The database's
    `messages.record` JSON text needs the same per-record rule when it is
    read.

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
  runs. Parsed since analyzer 0.13.0 as a secondary source. At the
  2026-10-19 commit a global `--home <dir>` option selects the instance
  root, and the history file, the default workspace and the legacy
  sessions directory follow it
  ([`config/home.py:19-28`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/config/home.py#L19-L28);
  [`config/paths.py:52-72`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/config/paths.py#L52-L72);
  [`docs/multiple-instances.md:3`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/docs/multiple-instances.md#L3),[`12`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/docs/multiple-instances.md#L12)),
  so an instance run as `--home ~/.nanobot-work` writes
  `.nanobot-work/history/cli_history`, which the parser's fixed
  `.nanobot/history/cli_history` path does not select.

Found in the source review of 2026-10-19 (not read by the parser yet):

- `.nanobot/sessions/<workspace-id>/sessions.sqlite3`, with its `-wal`
  and `-shm` sidecars: the session store of record at that commit
  ([`session/location.py:31-35`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/location.py#L31-L35),[`56`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/location.py#L56);
  [`session/sqlite_store.py:95-96`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L95-L96);
  [`session/manager.py:422-437`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/manager.py#L422-L437)).
  Primary. Schema in [section 5](#5-sqlite-or-binary-stores). On first
  start, every `sessions/<workspace-id>/*.jsonl` and
  `<workspace>/sessions/*.jsonl` is imported in one transaction
  ([`session/sqlite_store.py:185-200`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L185-L200);
  [`session/jsonl_migration.py:155-197`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/jsonl_migration.py#L155-L197)).
  The namespace's own JSONL files are left where they were and are never
  written again, so after the import they are frozen copies of the
  sessions as they stood that day; every later turn is only in the
  database. The global pre-namespace `.nanobot/sessions/*.jsonl` files
  and `.migration-conflicts/` are no longer read by nanobot at all
  (`get_legacy_sessions_dir` is only exported, and `migration-conflicts`
  is not found in nanobot at `909b277`; grepped for
  `get_legacy_sessions_dir` and `migration-conflicts`).
- `.nanobot/sessions/<workspace-id>/jsonl-backup/<name>.jsonl` and
  `<name>.checkpoint.json`: the older `<workspace>/sessions/` files,
  copied byte for byte with their modification time kept and then
  removed from the workspace
  ([`session/jsonl_migration.py:32`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/jsonl_migration.py#L32),[`221-232`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/jsonl_migration.py#L221-L232),[`235-291`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/jsonl_migration.py#L235-L291)).
  Same record format as the session JSONL; secondary once the database
  is read, since every one was imported into it.
- `.nanobot/sessions/<workspace-id>/.webui_session_index.json`: a
  rebuildable cache of the WebUI sidebar, `{"version": 8, "sessions":
  [...]}` with one row per WebUI transcript (title, preview, model
  preset, workspace scope)
  ([`webui/session_list_index.py:1-6`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/session_list_index.py#L1-L6),[`39-40`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/session_list_index.py#L39-L40),[`172-204`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/session_list_index.py#L172-L204)).
  Secondary; it holds a preview, not turns, and a row can outlive the
  transcript until the cache is rebuilt.
- `<workspace>/cron/runs/<run id>.json`: one audit record per scheduled
  run, `job_id`, `job_name`, `session_key`, `rendered_prompt`,
  `status`, `response` or `error`, `run_id`, `updated_at_ms` (UTC epoch
  milliseconds)
  ([`cron/service.py:207-208`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cron/service.py#L207-L208),[`472-474`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cron/service.py#L472-L474);
  [`cron/bound_runner.py:98-146`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cron/bound_runner.py#L98-L146);
  [`utils/run_records.py:19-29`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/utils/run_records.py#L19-L29)),
  beside `cron/jobs.json`, whose `state.runHistory[]` keeps `runAtMs`,
  `status`, `runId` and `sessionKey`
  ([`cron/service.py:445-454`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cron/service.py#L445-L454)),
  and `cron/action.jsonl`, a queue of `{action, params}` lines
  ([`:673-674`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cron/service.py#L673-L674)).
  Secondary: the prompt and the reply are also turns of the bound
  session, and the run record survives the session's deletion.
- `<workspace>/triggers/`: local triggers (`triggers.json`, each bound
  to a `channel`, `chat_id` and `session_key`), the delivery queue
  (`inbox/`, `processing/`, `failed/`, each delivery `{id, triggerId,
  content, createdAtMs, attempts, lastError}`) and `runs/<delivery
  id>.json` audit records with the content and the `response`
  ([`triggers/local_store.py:45-50`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/triggers/local_store.py#L45-L50),[`53-90`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/triggers/local_store.py#L53-L90),[`292-310`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/triggers/local_store.py#L292-L310);
  [`triggers/local_types.py:121-158`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/triggers/local_types.py#L121-L158)).
  Secondary, as for the cron runs; this directory was already in the
  cited commit and was not traced then.

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

None for transcripts at the [section 1](#1-source) commit. `llm_usage.sqlite3` (WAL, [`store.py:190`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/llm_usage/store.py#L190)) holds only
call metadata: `llm_calls` has `started_at_ms`, `provider`, `model` and
`source` per call and no session key
([`llm_usage/store.py:196-218`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/llm_usage/store.py#L196-L218)
at the 2026-10-19 commit), so a call joins a session on time alone.

At the 2026-10-19 commit the transcripts are in SQLite.
`sessions/<workspace-id>/sessions.sqlite3` is opened in WAL mode (the
write-ahead log, a `-wal` sidecar that holds committed pages not yet
copied into the main file) with `PRAGMA user_version` 1
([`session/sqlite_store.py:44-73`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L44-L73),[`174`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L174)):

| Table | Columns | Holds |
| --- | --- | --- |
| `sessions` | `key` (primary), `created_at`, `updated_at`, `metadata` (JSON text), `provider_state`, `last_archived`, `revision`, `generation`, `title`, `preview`, `visible_updated_at` | the old metadata line, one row per session key; times are `datetime.isoformat()` of naive local time, as in the JSONL |
| `messages` | `session_key`, `position`, `record` (JSON text) | one message per row in order; `record` is exactly the old JSONL message line (`role`, `content`, `timestamp`, `tool_calls`, flags) |
| `checkpoints` | `session_key`, `record` | the mid-turn runtime checkpoint, formerly `<stem>.checkpoint.json` |
| `pending_inputs` | `session_key`, `kind`, `position`, `record` | follow-up messages queued while a turn runs (`kind` `pending_user_followups`) |
| `storage_meta` | `key`, `value` | `jsonl_import` = `complete` after the import, and the pending workspace-source list |

Writes upsert each changed `messages` row and delete rows past the new
length, so a `/new` or a rewind removes rows rather than rewriting a file
([`:281-335`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L281-L335)).
Deleting a session is one `DELETE FROM sessions`, and the foreign keys
cascade to its messages, checkpoint and pending inputs
([`:53-66`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L53-L66),[`394-396`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L394-L396)).
No `VACUUM`, `auto_vacuum` or `secure_delete` is set (not found in
`nanobot/session` or `nanobot/llm_usage` at `909b277`; grepped for
`VACUUM`, `auto_vacuum` and `secure_delete`), so a deleted session's
pages stay in the file's free list or the WAL until reused. A child
session (a subagent or a fork) names its parent in
`metadata.parent_session_key`
([`session/types.py:8-9`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/types.py#L8-L9);
[`session/sqlite_store.py:404-413`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L404-L413)).

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

Remote WebUI pairing, nanobot's SSH-based link from a local WebUI to a
nanobot gateway on another host the user runs (no vendor relay,
[`webui/remote_pairing.py:1-5`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_pairing.py#L1-L5)),
keeps its material under the instance's `webui/` directory
([`webui/ws_http.py:392-394`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/ws_http.py#L392-L394)):
`remote-pairing/<uuid>/identity` (an unencrypted OpenSSH private key),
`exchange` (a raw X25519 private key), `request`, `receipt` and
`ssh_route`
([`:208-210`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_pairing.py#L208-L210),[`249-251`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_pairing.py#L249-L251),[`290-299`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_pairing.py#L290-L299)).
`remote-instances.json` lists the saved remote servers by UUID with
`name`, `host` (`user@host`), `port`, `ssh_config`, `identity_file`,
`config_path`, `runtime_user`, `local_port` and `pair_id`
([`webui/remote_instances.py:28-34`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_instances.py#L28-L34),[`52-53`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_instances.py#L52-L53),[`98-103`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_instances.py#L98-L103);
[`webui/remote_ssh.py:32-41`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_ssh.py#L32-L41)),
beside `remote-origin-ports.json` and per-server pinned host keys in
`remote-hosts/<uuid>`
([`remote_instances.py:70-71`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_instances.py#L70-L71),[`105-125`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_instances.py#L105-L125)).
The catalog collects all of them under `.nanobot*`, and no secret glob
matches the two private keys.

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
is named in the research without its shape, so the file is not read
(its shape is traced in the requirement-class list below).

Sync: nanobot records no sync state, because it uploads no session to a
vendor or share service. The session, the WebUI transcript, the memory
journal and the CLI history are written only under the home and the
workspace ([section 2](#2-transcript-files)), and the project's own
privacy notes say chat history is stored locally and that the model
provider sees the prompts
([`SECURITY.md:208-212`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/SECURITY.md#L208-L212)).
A channel (Telegram, Slack and the other chat services nanobot answers
through) keeps its own copy of the messages it carried, on the channel's
servers, as the model provider sees the prompts; neither is sync. Searched
at the [section 1](#1-source) commit: `sync`, `share`, `upload`, `cloud`,
`telemetry`, `analytics`, `backup`, `export`, `remote`, every
`https://` host outside the provider and channel modules, and the WebUI
and TUI front ends for analytics libraries (none). The paths found and
read, none of which carries session content to a vendor:

- Langfuse tracing, an LLM-observability service, is opt-in: with the
  `langfuse` extra installed (`nanobot plugins enable langfuse`) and
  `LANGFUSE_SECRET_KEY` set in the environment, the OpenAI-compatible
  provider's client is swapped for Langfuse's wrapper, which sends each
  model call's prompt and reply to `LANGFUSE_BASE_URL` (default
  `https://cloud.langfuse.com`)
  ([`providers/openai_compat_provider.py:624-632`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/providers/openai_compat_provider.py#L624-L632);
  [`webui/settings_capabilities.py:197-205`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/settings_capabilities.py#L197-L205);
  [`pyproject.toml:85-86`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/pyproject.toml#L85-L86);
  [`docs/provider-cookbook.md:529-557`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/docs/provider-cookbook.md#L529-L557)).
  The setting lives only in the process environment, not in
  `config.json`, and the gateway's systemd unit sets no such variable
  ([`gateway/service.py:268-273`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/gateway/service.py#L268-L273)),
  so nothing collected says a session was traced; a responder who finds
  the `langfuse` package in nanobot's Python environment asks the
  Langfuse project for the traces.
- Remote WebUI pairing connects the local WebUI over SSH to a nanobot
  gateway on another host the user runs; that host's sessions stay on it,
  in its own `.nanobot`, and the local side keeps only the server list
  and the pairing keys ([section 7](#7-secrets)). "Forget" removes a
  pairing's files
  ([`webui/remote_pairing.py:330-339`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_pairing.py#L330-L339))
  and leaves the append-only `remote-origin-ports.json` ledger
  ([`webui/remote_instances.py:105-125`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/remote_instances.py#L105-L125)).
  The parser does not read these files; they point the responder at the
  other host to collect.
- The update check is a GET of the PyPI release record on request
  ([`webui/version_check.py:1-3`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/version_check.py#L1-L3),[`19`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/version_check.py#L19)),
  the GitHub star invitation is local state only
  ([`webui/star_prompt.py:1`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/star_prompt.py#L1)),
  and the skills marketplace runs `npx skills add` with
  `DISABLE_TELEMETRY=1`
  ([`webui/skills_marketplace.py:382-388`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/skills_marketplace.py#L382-L388)).
- A WebUI Temporary Chat runs on a non-persistent session and writes no
  session file or WebUI transcript
  ([`webui/temporary_chats.py:40-44`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/temporary_chats.py#L40-L44),[`84-98`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/temporary_chats.py#L84-L98);
  [`session/manager.py:1634-1642`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L1634-L1642)),
  so such a chat leaves no transcript on disk at all.

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

Requirement classes at the 2026-10-19 commit (see the review bullet in
[section 1](#1-source)); none of this is in the parser yet:

- Primary store: read `sessions/<workspace-id>/sessions.sqlite3` through
  `sqlite_util.py` ([section 5](#5-sqlite-or-binary-stores)): one session
  per `sessions` row, `metadata` as the old metadata line, `messages`
  ordered by `position` with `record` mapped as the JSONL message lines
  are now, and each `record` that does not decode its own
  `parser: unparseable record <position> (<reason>)` row. The
  namespace's `*.jsonl` files and `jsonl-backup/*.jsonl` then become
  secondary (`secondary()` true, default 2-second window: the same
  `timestamp` strings), since the import copied every one of them.
- Permission: one `system` row per standing setting at the file's
  modification time, `permission setting: <key>=<value> (from
  config.json, file mtime)`, for `tools.restrictToWorkspace`,
  `tools.exec.enable`, `tools.exec.sandbox`, each
  `tools.exec.allowPatterns`, `denyPatterns`, `sandboxRoBinds`,
  `sandboxRwBinds` and `allowedEnvKeys` entry, `tools.ssrfWhitelist`,
  `tools.webuiAllowLocalServiceAccess`,
  `tools.webuiAllowRemotePackageInstall` and each
  `channels.<name>.allowFrom` entry
  ([`config/schema.py:428-458`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/config/schema.py#L428-L458);
  [`agent/tools/shell_config.py:11-28`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/agent/tools/shell_config.py#L11-L28);
  [`channels/base.py:244-257`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/channels/base.py#L244-L257));
  one per `pairing.json` `approved.<channel>[]` sender, `permission
  setting: pairing.approved.<channel>=<sender_id> (from pairing.json,
  file mtime)`, and per `pending.<code>` entry at its `created_at`
  (epoch seconds), with `channel`, `sender_id`, `expires_at` and
  `delivery_status`
  ([`pairing/store.py:1-5`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/pairing/store.py#L1-L5),[`32-33`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/pairing/store.py#L32-L33),[`73-85`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/pairing/store.py#L73-L85),[`133-138`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/pairing/store.py#L133-L138));
  and after the session start row, `permission mode:
  access_mode=<restricted|full> project=<project_path>` from
  `metadata.workspace_scope`, which the WebUI writes on every message it
  accepts
  ([`security/workspace_access.py:11-12`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/security/workspace_access.py#L11-L12),[`80-84`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/security/workspace_access.py#L80-L84),[`212-213`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/security/workspace_access.py#L212-L213);
  [`webui/inbound_commands.py:694`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/inbound_commands.py#L694)).
  The key was already written at the [section 1](#1-source) commit.
  Per-call decisions: the agent records none. The exec tool's refusals
  are tool results such as `Error: Command blocked by deny pattern
  filter`
  ([`agent/tools/shell.py:825-835`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/agent/tools/shell.py#L825-L835)),
  already `tool_result` rows; no approval prompt exists (not found at
  `909b277`; grepped for `approv` in `nanobot/agent` and for
  `ask_user`, `confirm` and `permission` there, which find only the
  in-memory goal permission of `agent/goal_permission.py`).
- Model: keep `model: <preset> (preset)`, and add `model: <old> -> <new>
  (preset)` when a `_command` user message reads `/model <name>` and its
  `_command` assistant reply starts `Switched model preset to`, with
  ` requested=<name>` and the resolved id from the reply's `- Model:`
  line
  ([`command/builtin.py:405-448`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/command/builtin.py#L405-L448);
  [`agent/loop.py:2143-2155`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/agent/loop.py#L2143-L2155)).
  The metadata keeps only the last preset, so the first preset of a
  switched session is not recorded anywhere.
- Past use: add the cron and trigger run records as secondary sources
  (`user` from `rendered_prompt` or `content`, `assistant` from
  `response`, at `updated_at_ms`, `session_id` from `session_key` or the
  trigger's), and the WebUI sidebar cache as a secondary source of one
  `system` row per entry naming the title and preview; see
  [section 2](#2-transcript-files).
- Relay: after the session start row, for a key whose channel is a
  messaging platform, `session relayed: <channel> chat <chat_id> (from
  session key)`, and `... last route <channel>:<chat_id> (from
  metadata.last_channel)` when the last route differs, as the
  `agent-zero` and `goose` parsers do; set `records_relay`. The channel
  prefixes at `909b277` are `dingtalk`, `discord`, `email`, `feishu`,
  `linear`, `matrix`, `mattermost`, `mochat`, `msteams`, `napcat`, `qq`,
  `signal`, `slack`, `telegram`, `wecom`, `weixin`, `whatsapp` and
  `whatsapp_agent` (each channel's `name`, for example
  [`channels/telegram/runtime.py:589`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/channels/telegram/runtime.py#L589));
  `websocket` (the WebUI), `cli`, `api`
  ([`api/server.py:361`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/api/server.py#L361)),
  `heartbeat`, `dream:` and `unified:default` are local, though
  `unified:default` with a messaging `last_channel` was relayed
  ([`session/keys.py:8-38`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/keys.py#L8-L38)).
  Sync: the agent records none; the [sync paragraph](#8-parser-plan)
  above still holds, and Langfuse is now also called from the Codex
  provider
  ([`providers/openai_codex_provider.py:59`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/providers/openai_codex_provider.py#L59);
  [`providers/openai_compat_provider.py:595-601`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/providers/openai_compat_provider.py#L595-L601)).
  Origin: the agent records none; `nanobot remote` pairs a server with a
  local WebUI over SSH, "No public WebUI or relay"
  ([`cli/remote.py:1`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cli/remote.py#L1),[`20`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cli/remote.py#L20)).
- Scratch directories: no row needed. The default workspace
  `<instance>/workspace`
  ([`config/home.py:24-28`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/config/home.py#L24-L28))
  and the compose file's `api-workspace`
  ([`docker-compose.yml:48-49`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/docker-compose.yml#L48-L49))
  are under `.nanobot*`, which the catalog rule already classes; a
  `--home` outside the home's `.nanobot*` is neither collected nor
  classed.
- Deletion: no row; the session's rows are gone from the database
  ([`webui/ws_http.py:1363-1378`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/ws_http.py#L1363-L1378);
  [`session/manager.py:555-574`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/manager.py#L555-L574)),
  and what survives is the secondary sources above.
- CLI history: select `.nanobot*/history/cli_history`, since `--home`
  moves it.

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
