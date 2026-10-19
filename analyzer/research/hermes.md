# Hermes Agent transcript schema

Catalog agent: `hermes`. Hermes stores every conversation (CLI, TUI,
desktop, messaging gateway, cron, subagents) in one SQLite database per
profile home, in OpenAI chat-completions message shape. Paths in
[`collectors/research/hermes.md`](../../collectors/research/hermes.md).

## 1. Source

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) at [`8b66a51036c1e20920a17cdd049fdf55c968d683`](https://github.com/NousResearch/hermes-agent/commit/8b66a51036c1e20920a17cdd049fdf55c968d683),
MIT ([`LICENSE`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/LICENSE#L1-L3)). Open source, Python. Read only, not run.

- **Source review (2026-10-19)** at
  [`86fa9e6ca1de7ee71132d2be0103f3e37d1fa872`](https://github.com/NousResearch/hermes-agent/commit/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872)
  (HEAD of 2026-10-19), against the
  [`8b66a51036c1e20920a17cdd049fdf55c968d683`](https://github.com/NousResearch/hermes-agent/commit/8b66a51036c1e20920a17cdd049fdf55c968d683)
  (2026-10-04) cited above. Nothing installed or run; no real install of
  Hermes has been observed. Per requirement class:
  - Permission state: found, not parsed. Per-call outcomes are written
    into the `terminal` tool result (`approval` note, `status`
    `blocked` or `pending_approval`), and standing grants live in
    `config.yaml` (`command_allowlist`, `approvals.*`), in
    `sessions.model_config.yolo_mode` and in the gateway pairing files
    ([section 3](#3-record-schema), [section 8](#8-parser-plan)).
  - Model: covered. `session_model_usage` and `sessions.model` are
    read, and since issue 180 the durable model-switch marker rows
    (`display_kind = 'model_switch'`) are `model:` `system` rows rather
    than user prompts ([section 3](#3-record-schema),
    [section 8](#8-parser-plan)).
  - Past use beyond `state.db`: found, not read. The prompt history
    `.hermes_history`, the cron run archive `cron/output/`,
    `response_store.db`, trajectory files, the Bot Mode room log and
    sessions imported from Claude Code and Codex CLI
    ([section 2](#2-transcript-files)).
  - Sync, relay and origin: found. Gateway sessions are relays through a
    messaging platform and the parser writes no `session relayed:` row;
    `hermes sessions export --format trace --upload` uploads a session to
    a Hugging Face dataset and leaves no local mark; the desktop app lists
    sessions of remote, SSH and Hermes Cloud backends
    ([section 8](#8-parser-plan)).
  - Scratch directories: found. `cache/scratch/` and `sandboxes/` under
    the Hermes home, and git worktrees under `<repo>/.worktrees/`, which
    `sessions.cwd` records ([section 2](#2-transcript-files)).
  - Deletion: found, changed since the cited commit. A delete now leaves
    a tombstone per session id in `state.db` `state_meta`, and automatic
    pruning is now off by default ([section 5](#5-sqlite-specifics)).
  - Version drift: schema version 31 to 32, three new `sessions`
    columns and four new tables, a new `local-<sha256>` session id form;
    every path, table and column the parser reads is unchanged
    ([section 6](#6-format-versions)).
  - Bad lines: covered. The divert reader goes through `iter_jsonl`, and
    since issue 182 a `tool_calls` value that does not decode is a
    `parser:` row carrying the value ([section 8](#8-parser-plan)).
  - Layouts the parser handles that no install has shown: the
    model-switch marker rows, a malformed `tool_calls` value and a Hermes
    home in a Docker or Podman named volume are not observed on any real
    install, source-derived (NousResearch/hermes-agent at
    [`86fa9e6`](https://github.com/NousResearch/hermes-agent/commit/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872)
    for the markers,
    [`8b66a51`](https://github.com/NousResearch/hermes-agent/commit/8b66a51036c1e20920a17cdd049fdf55c968d683)
    for the volume mount point).

## 2. Transcript files

Globs relative to the user home:

- `.hermes/state.db` (+ `-wal`, `-shm`), and the same under
  `.hermes/profiles/*/` and `AppData/Local/hermes/`
  ([`hermes_state.py:176`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state.py#L176); home resolution in
  [`hermes_constants.py:51-58`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_constants.py#L51-L58)). One database holds all sessions; it
  is canonical for the gateway too
  ([`gateway/session_transcript.py:573-575`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/gateway/session_transcript.py#L573-L575)).
- `.hermes/sessions/<session_id>.jsonl`: written only when `state.db` was
  replaced under a running process; one JSON message dict per line
  ([`hermes_state.py:429-444`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state.py#L429-L444)).
  Hermes calls this a divert: the batch of messages a live agent or the
  gateway could not write because its database handle was replaced or
  quarantined is appended here instead ([`agent/session_persistence.py:392-397`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/session_persistence.py#L392-L397), [`gateway/session_transcript.py:153-177`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/gateway/session_transcript.py#L153-L177)). An agent's line has the
  keys of a `messages` row in that order, `role`, `content`, `tool_name`,
  `tool_calls` (a list), `tool_call_id`, the reasoning keys, `timestamp`
  and others ([`agent/session_persistence.py:224-236`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/session_persistence.py#L224-L236)); a gateway line is the pending transcript message as the
  gateway queued it. No `session_id` field (it is the file name), no `cwd`,
  no model.
- `.hermes/state-snapshots/<id>/state.db`: quick snapshots. `/snapshot
  [label]`, `hermes backup --quick`, `hermes update` (label `pre-update`)
  and the profile repair (label `repair-profiles`) copy `state.db` and the
  other critical state files ([`hermes_cli/backup.py:1057-1076`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1057-L1076)) into `state-snapshots/<id>/`
  ([`hermes_cli/backup.py:57`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L57), [`hermes_cli/cli_commands_mixin.py:826-828`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/cli_commands_mixin.py#L826-L828), [`hermes_cli/backup.py:2190-2193`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L2190-L2193), [`hermes_cli/update_cmd_maint.py:686-691`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/update_cmd_maint.py#L686-L691), [`hermes_cli/sessions_repair_profiles.py:485`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/sessions_repair_profiles.py#L485)). `<id>` is the UTC time `%Y%m%d-%H%M%S`, then
  `-<label>` when one was given, then `-2`, `-3` on a collision ([`hermes_cli/backup.py:1263-1270`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1263-L1270)); the
  files are staged under `.<id>.<pid>.partial` and renamed into place
  ([`hermes_cli/backup.py:1271`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1271), [`hermes_cli/backup.py:1420`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1420)), and a `manifest.json` records `id`, `timestamp`, `label`,
  `file_count`, `total_size`, `files`, `failed_dbs` and
  `oversized_skipped` ([`hermes_cli/backup.py:1393-1402`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1393-L1402)). A database is copied with SQLite's backup API,
  so the copy is a consistent, complete database with no WAL of its own
  ([`hermes_cli/backup_sqlite.py:31-35`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup_sqlite.py#L31-L35), [`hermes_cli/backup_sqlite.py:68`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup_sqlite.py#L68)). By default 20 snapshots are kept, older ones pruned (the `hermes update` caller passes its own count), except when a
  database failed to copy or was skipped as too large ([`hermes_cli/backup.py:1079`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1079), [`hermes_cli/backup.py:1422-1430`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1422-L1430)); `hermes
  update` passes a file-size cap, so a large `state.db` can be missing from
  its snapshot ([`hermes_cli/update_cmd_maint.py:690-691`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/update_cmd_maint.py#L690-L691)). Collected only with `--full`: the catalog excludes
  `state-snapshots`
  ([section 4 of `collectors/research/hermes.md`](../../collectors/research/hermes.md#4-exclusions)).
- `.hermes/backups/pre-update-*.zip` and `pre-migration-*.zip`: full zip
  backups of the home, 5 of each ([`hermes_cli/backup.py:1120-1124`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1120-L1124)); not parsed.
- `.hermes/sessions/<id>.json`, `session_<id>.json` (legacy snapshots) and
  `request_dump_<id>_<ts>.json` (redacted API request on error)
  ([`hermes_state_sessions.py:1573-1585`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_sessions.py#L1573-L1585),
  [`agent/agent_runtime_helpers.py:1628-1633`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/agent_runtime_helpers.py#L1628-L1633)).
  Nothing at the checked commit writes the two legacy snapshot names; the
  only code that names them is `_remove_session_files`, which deletes them
  with a session (an evaluation script checks that the old
  `write_json_snapshots` setting no longer produces any,
  [`evals/session_snapshot_removal.py:12-29`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/evals/session_snapshot_removal.py#L12-L29)),
  so their shape cannot be read from this source and the parser does not
  read them.
- `.hermes/sessions/saved/hermes_conversation_<YYYYmmdd_HHMMSS>.json`
  (`{id, model, started_at, messages}`) from `/save`
  ([`hermes_cli/cli_session_mixin.py:669-689`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/cli_session_mixin.py#L669-L689)).
- `.hermes/response_store.db`: API-server response store
  ([`gateway/platforms/api_server.py:732`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/gateway/platforms/api_server.py#L732)); schema not examined.
- `.hermes/pastes/pending.json`: the paste.rs links (paste.rs is a
  public, anonymous paste service) that `hermes debug share`, the gateway's
  `/debug` and the dashboard's debug-share endpoint uploaded and that are
  still due for deletion
  ([`hermes_cli/debug.py:38-39`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L38-L39)).
  A JSON list of `{"url": <string>, "expire_at": <epoch seconds, float>}`,
  `expire_at` the upload time plus 21600 seconds (6 hours), merged by URL
  keeping the later time
  ([`hermes_cli/debug.py:156-166`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L156-L166),
  [`hermes_cli/debug.py:31`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L31)).
  An entry is dropped once its paste is deleted, or 24 hours after
  `expire_at` when the delete keeps failing
  ([`hermes_cli/debug.py:59-89`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L59-L89));
  the gateway sweeps it hourly and every `hermes debug` call sweeps it
  first ([`gateway/run.py:4666-4670`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/gateway/run.py#L4666-L4670),
  [`hermes_cli/debug.py:639-641`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L639-L641)).
  The file is missing or `[]` when nothing was shared in the last 6 to 30
  hours. Links to dpaste.com (the fallback paste service) are never
  written, since dpaste.com has no anonymous delete
  ([`hermes_cli/debug.py:158-160`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L158-L160)).
- `.hermes/retaindb_queue.db`: the write-behind queue of the RetainDB
  memory provider (a paid cloud memory service), present only when
  `memory.provider` is `retaindb`
  ([`plugins/memory/retaindb/__init__.py:343-345`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/plugins/memory/retaindb/__init__.py#L343-L345)).
  Table `pending` (`id`, `user_id`, `session_id`, `messages_json` holding
  the turn's user and assistant text, `created_at` ISO 8601 UTC,
  `last_error`); a row is deleted as soon as its upload succeeds, so the
  table holds only turns not yet uploaded
  ([`plugins/memory/retaindb/__init__.py:194-198`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/plugins/memory/retaindb/__init__.py#L194-L198),
  [`plugins/memory/retaindb/__init__.py:226-241`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/plugins/memory/retaindb/__init__.py#L226-L241)).
  Not read by the parser.

Session ids are `<YYYYmmdd_HHMMSS>_<hex>` from local time
([`hermes_state_ids.py:56-60`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_ids.py#L56-L60)).
At the 2026-10-19 HEAD a session created through the unified runtime
(Hermes' newer single owner of session creation for the local front ends
and cron) is instead `local-` followed by the SHA-256 of its profile,
principal and request ids, and a cron run's request id is
`cron:<job>:<execution>`; runs from before it were
`cron_<job>_<YYYYmmdd_HHMMSS>`
([`hermes_state_keys.py:11-17`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_keys.py#L11-L17),
[`hermes_state_keys.py:71-74`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_keys.py#L71-L74)).
The parser treats the id as an opaque string, so both forms work.

Sources of past use beyond `state.db` that the parser does not read, at
the 2026-10-19 HEAD (none of them is new since the cited commit unless
it says so):

- `.hermes/.hermes_history`: the prompt history of the classic CLI and
  of the TUI (the terminal interface), shared by both
  ([`hermes_cli/cli_init_mixin.py:389`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/cli_init_mixin.py#L389),
  [`hermes_cli/cli_tui_mixin.py:2208`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/cli_tui_mixin.py#L2208),
  [`ui-tui/src/lib/history.ts:6-7`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/ui-tui/src/lib/history.ts#L6-L7)).
  prompt_toolkit's `FileHistory` format: per entry a blank line, a
  `# <timestamp>` line and the entry's lines each prefixed `+`; the TUI
  writes the timestamp as UTC `YYYY-MM-DD HH:MM:SS.mmm` and keeps the
  last 1000 entries in memory only
  ([`ui-tui/src/lib/history.ts:71-78`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/ui-tui/src/lib/history.ts#L71-L78)),
  while prompt_toolkit writes local time. Every typed line, slash
  commands included (`/model`, `/yolo`, `/snapshot`), with no session id
  or project. Nothing that deletes a session touches it, so it survives
  a delete, a prune, a rewind and a removed project. Joins on text and
  time only. Secondary.
- `cron/output/<job id>/<YYYY-mm-dd_HH-MM-SS>.md`: one Markdown file per
  cron run, local time in the name, with a `# Cron Job: <id>` header and
  `## Prompt` and `## Response` sections, pruned per job to a configured
  count
  ([`cron/jobs.py:114`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/cron/jobs.py#L114),
  [`cron/jobs.py:3384-3395`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/cron/jobs.py#L3384-L3395),
  [`cron/scheduler_prompt.py:72-73`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/cron/scheduler_prompt.py#L72-L73)).
  Survives the prune or delete of the run's `source='cron'` session.
  Joins on the job id and time, not on a session id. Secondary.
- `response_store.db`: the API server's store for the OpenAI Responses
  API (`previous_response_id` chaining). Table `responses`
  (`response_id`, `data`, `accessed_at`), whose `data` is JSON
  `{response, conversation_history, instructions, session_id}`, the full
  cumulative history at that response; table `conversations` (`name`,
  `response_id`); it keeps the 100 most recently used responses
  ([`gateway/platforms/api_server_response_store.py:14`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/platforms/api_server_response_store.py#L14),
  [`gateway/platforms/api_server_response_store.py:21-24`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/platforms/api_server_response_store.py#L21-L24),
  [`gateway/platforms/api_server_response_store.py:58-61`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/platforms/api_server_response_store.py#L58-L61),
  [`gateway/platforms/api_server_openai_routes.py:354-358`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/platforms/api_server_openai_routes.py#L354-L358)).
  No session delete path names it (grepped `response_store` and
  `ResponseStore` in `hermes_state*.py` and `hermes_cli/sessions*.py`:
  only the WAL helper), so it outlives a deleted `api_server` session.
  Joins on `session_id`. Secondary.
- `trajectory_samples.jsonl` and `failed_trajectories.jsonl` in the
  working directory (project files, collected by the project catalog):
  one line per run in the ShareGPT format (a common layout for conversation training data), `{conversations, timestamp, model,
  completed}`, `timestamp` local ISO 8601 without a zone, no session id
  ([`agent/trajectory.py:37-41`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/trajectory.py#L37-L41)).
  Written only with `--save-trajectories`; survives everything. Joins on
  text and time within a project. Secondary.
- Sessions imported from other agents. `hermes_cli/foreign_sessions.py`
  reads Claude Code `~/.claude/projects/*/*.jsonl` and Codex CLI
  `~/.codex/sessions/**/rollout-*.jsonl` and copies their user and
  assistant turns into `state.db` as a new session with `source`
  `claude-code` or `codex-cli`, `origin_json`
  `{"imported_from": {"tool", "path", "foreign_session_id"}}` and the
  title `Imported from <tool>: <first line>`
  ([`hermes_cli/foreign_sessions.py:26-27`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/foreign_sessions.py#L26-L27),
  [`hermes_cli/foreign_sessions.py:173-178`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/foreign_sessions.py#L173-L178),
  [`hermes_cli/foreign_sessions.py:254-260`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/foreign_sessions.py#L254-L260)).
  The messages are appended at import time, so their `timestamp` is the
  import's, not the original turn's. The parser reads these rows as
  Hermes sessions (they are in `state.db`), and its start row shows
  `source=claude-code` but not the origin path; such a session is a
  copy of another agent's transcript that outlives the original file.
- Bot Mode group chats (Bot Mode is the desktop app's roster of
  profiles as named bots that share group chats): tables `hosted_rooms`
  and `hosted_room_events` (`room_id`, `seq`, `event_id`, `kind`,
  `actor_json`, `payload_json`, `created_at`), an append-only room log in
  the gateway's root `state.db`
  ([`gateway/hosted_rooms.py:1-5`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/hosted_rooms.py#L1-L5),
  [`gateway/hosted_rooms.py:88-117`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/hosted_rooms.py#L88-L117)).
  The event kinds and payload shapes were not examined; whether a room
  message also becomes a `messages` row was not determined. Secondary
  until shown otherwise.
- `conversation_generations` (`source`, `session_key`, `generation`) in
  `state.db`: one row per messaging routing peer, deliberately never
  deleted, so it names every platform chat (`session_key` is
  `agent:<profile>:<platform>:...`) that ever had a conversation after
  its sessions are gone
  ([`hermes_state_common.py:642-669`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_common.py#L642-L669)).
  No time column. Secondary, with no text to join on; a record of
  relay use, not of turns.

Scratch directories, at the 2026-10-19 HEAD: `cache/scratch/<entry>`
under the Hermes home, the `TMPDIR` of the agent's child processes,
reaped when idle
([`hermes_constants.py:957`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_constants.py#L957),
[`hermes_constants_scratch.py:1-6`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_constants_scratch.py#L1-L6));
`sandboxes/` under the Hermes home, the container backends' persistent
bind mounts (`TERMINAL_SANDBOX_DIR` overrides it)
([`tools/environments/base.py:189-191`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/environments/base.py#L189-L191),
[`tools/environments/docker.py:856`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/environments/docker.py#L856));
and git worktrees the agent creates inside the user's repository,
`<repo>/.worktrees/<name>` on branch `hermes/<name>` for `hermes -w`,
`.worktrees/subagent-<id>` on `hermes-subagent/<name>` for delegated
subagents, and `.worktrees/<child id>` for kanban children
([`hermes_cli/worktree_ops.py:435-441`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/worktree_ops.py#L435-L441),
[`tools/subagent_worktree.py:81-96`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/subagent_worktree.py#L81-L96),
[`hermes_cli/kanban_db_graph.py:181`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/kanban_db_graph.py#L181)).
A `-w` session runs with its working directory in the worktree
([`hermes_cli/cli_commands_mixin.py:1189-1197`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/cli_commands_mixin.py#L1189-L1197)),
so `sessions.cwd` holds the worktree path
([`hermes_cli/worktree_ops.py:822-825`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/worktree_ops.py#L822-L825)),
and a retained TUI worktree is locked with the reason
`hermes session=<id> db=<path>`
([`hermes_cli/worktree_ops.py:805-815`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/worktree_ops.py#L805-L815)).
The analyzer's catalog rule already classes any path under the Hermes
home as a scratch directory; a `.worktrees/<name>` path is not under a
home entry, so it is listed as a project.

## 3. Record schema

Schema in [`hermes_state_common.py:372-480`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L372-L480).

`sessions` ([`382-447`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L382-L447)): `id`, `source` (`cli`, `cron`, `kanban`,
`acp`, `api_server`, `subagent`, `tool`, `recovered` or a messaging
platform; [`hermes_state.py:471-473`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state.py#L471-L473)), `user_id`, `session_key`,
`chat_id`, `chat_type`, `thread_id`, `display_name`, `origin_json`, `model`,
`model_config`, `system_prompt_hash` (joins `system_prompts.hash`),
`parent_session_id`, `started_at`, `ended_at` (REAL epoch seconds),
`end_reason`, token and cost counters, `cwd`, `git_branch`,
`git_repo_root`, `title`, `profile_name`, `archived`, `hidden`,
`tool_names`. `cwd` and `git_branch` are set at creation and updated by
`update_session_cwd` ([`hermes_state_sessions.py:326`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_sessions.py#L326),[`558-566`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_sessions.py#L558-L566)).

`messages` ([`449-480`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L449-L480)), one row per OpenAI message:

| Column | Meaning |
| --- | --- |
| `id` | INTEGER autoincrement, order of writing |
| `session_id` | `sessions.id` |
| `role` | `user`, `assistant`, `tool`, `system` ([`hermes_state_messages.py:644`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_messages.py#L644)) |
| `content` | TEXT; list or dict content (multimodal parts) is stored as `"\x00json:"` + JSON ([`hermes_state_messages.py:138-147`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_messages.py#L138-L147), prefix at [`hermes_state.py:1612`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state.py#L1612)) |
| `tool_calls` | JSON list on assistant rows ([`hermes_state_messages.py:266`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_messages.py#L266)); each `{id, call_id, response_item_id, type, function: {name, arguments}}` with `arguments` a JSON string ([`agent/chat_completion_helpers.py:1642-1644`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/chat_completion_helpers.py#L1642-L1644)) |
| `tool_call_id`, `tool_name` | on `role='tool'` result rows ([`agent/turn_tool_round.py:115-118`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/turn_tool_round.py#L115-L118)) |
| `timestamp` | REAL, `time.time()` epoch seconds, UTC ([`hermes_state_messages.py:399`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_messages.py#L399)) |
| `reasoning`, `reasoning_content` | thinking text; `reasoning_details`, `codex_reasoning_items`, `codex_message_items` are JSON ([`hermes_state_messages.py:278-280`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_messages.py#L278-L280)) |
| `finish_reason`, `token_count` | provider values |
| `active`, `compacted` | rewind and compaction set `active=0, compacted=1` instead of deleting ([`hermes_state_messages.py:70`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_messages.py#L70)) |
| `api_content` | exact string sent to the API when it differed from `content` ([`hermes_state_messages.py:390-392`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_messages.py#L390-L392)) |
| `platform_message_id`, `display_kind`, `display_metadata`, `message_uid`, `tool_call_uid(s)` | gateway and UI bookkeeping |

Model per message is not stored; use `sessions.model`, or
`session_model_usage.model` ([`hermes_state_common.py:482-502`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L482-L502)) when a
session switched models. `session_model_usage` has one row per
(`session_id`, `model`, `billing_provider`, `billing_base_url`,
`billing_mode`, `task`), upserted with the token delta of each API call
that reports usage;
`first_seen` and `last_seen` are `time.time()` epoch seconds, `task` is
empty for the main agent loop and names the work (`vision`, `compression`,
`title_generation`) for auxiliary calls
([`hermes_state_usage.py:337-365`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_usage.py#L337-L365)).
`sessions.model` is overwritten by a mid-session `/model` switch
([`hermes_state_sessions.py:708-735`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_sessions.py#L708-L735)),
so it holds the latest model, not the first.

Model switches made in the TUI, the desktop app or another front end of
the TUI gateway are also durable message rows, at the 2026-10-19 HEAD and
at the cited commit alike: a `role = 'user'` row with
`display_kind = 'model_switch'` and the content `[System: The active
model for this chat has changed to <model> via provider <provider>. From
this point forward, ...]`, timestamped at the switch
([`tui_gateway/server.py:1274`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tui_gateway/server.py#L1274),
[`tui_gateway/server.py:1291-1331`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tui_gateway/server.py#L1291-L1331)).
Each switch first deactivates the earlier marker rows of the session
(`active = 0`), which are kept, never deleted
([`hermes_state_messages.py:1064-1070`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_messages.py#L1064-L1070)),
so every switch survives as one row with the model, the provider and
the time; the classic CLI's `/model` writes no row and only updates
`sessions.model`. Other `display_kind` values mark rows that are not
typed input either: `hidden`, `steer`, `internal_notification`,
`async_delegation_complete`, `process_complete` and `failed_turn`
([`hermes_state_detached_results.py:29`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_detached_results.py#L29),
[`agent/prompt_builder.py:586`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/prompt_builder.py#L586),
[`agent/turn_failure_copy.py:55`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/turn_failure_copy.py#L55),
[`gateway/response_filters.py:33`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/response_filters.py#L33),
[`tools/process_registry_notifications.py:349`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/process_registry_notifications.py#L349)).

Permission outcomes are in the `terminal` tool's result row, whose
`content` is JSON. A command that needed approval and got it carries
`"approval": "Command required approval (<description>) and was approved
by the user."` or `"Command was flagged (<description>) and
auto-approved by smart approval."` (smart approval is Hermes' guardian
model that judges a flagged command)
([`tools/terminal_tool.py:1081-1087`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/terminal_tool.py#L1081-L1087),
[`tools/terminal_tool_result.py:268`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/terminal_tool_result.py#L268),
[`tools/terminal_tool_background.py:187-188`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/terminal_tool_background.py#L187-L188));
a refused one is `{"output": "", "exit_code": -1, "error": <message>,
"status": "blocked"}` with `user_summary` when a person was asked, and
one waiting for a gateway `/approve` is `"status": "pending_approval"`
with `command`, `description`, `pattern_key`, `smart_denied` and
`allow_permanent`
([`tools/terminal_tool.py:1062-1079`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/terminal_tool.py#L1062-L1079)).
The refusal message names the outcome: `BLOCKED by smart approval`, a
user denial with the user's `/deny` reason, a timeout ("Silence is not
consent"), or a withdrawn prompt; the outcome enum is `denied`,
`timeout`, `notify_failed`, `cancelled`, `blocked`
([`tools/approval.py:528`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval.py#L528),
[`tools/approval.py:790`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval.py#L790),
[`tools/approval.py:884-890`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval.py#L884-L890)).
The `outcome` key itself is not written to the result. An "always"
answer appends the command's pattern to `command_allowlist` in the
profile's `config.yaml`
([`tools/approval.py:401-414`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval.py#L401-L414),
[`tools/approval.py:470-495`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval.py#L470-L495)),
and a session's `/yolo` bypass (all approvals off for that session) is
kept as `yolo_mode: true` in `sessions.model_config` for the CLI, TUI
and desktop and in the gateway's routing entry for messaging sessions
([`tools/approval_yolo.py:1-8`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval_yolo.py#L1-L8),
[`agent/agent_init.py:1206-1216`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/agent_init.py#L1206-L1216)).
The other standing settings are in `config.yaml`: `approvals.mode`
(`manual`, `smart` or `off`, default `smart`), `approvals.cron_mode`,
`single_query_mode` and `unattended_mode` (`deny` or `approve`),
`approvals.deny` (globs that block even under `/yolo`) and
`command_allowlist`
([`hermes_cli/config_defaults.py:1680-1718`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/config_defaults.py#L1680-L1718),
[`tools/approval_context.py:263-280`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval_context.py#L263-L280));
the environment variable `HERMES_YOLO_MODE` turns every check off for
the process
([`tools/approval.py:46`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/approval.py#L46)).
The messaging gateway's pairing store, the standing list of platform
users allowed to drive the agent, is `pairing/<platform>-approved.json`,
a JSON object keyed by user id with `{user_name, approved_at}`
(`approved_at` epoch seconds), beside `<platform>-pending.json`
([`gateway/pairing.py:1-7`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/pairing.py#L1-L7),
[`gateway/pairing.py:353-356`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/pairing.py#L353-L356),
[`gateway/pairing.py:431-437`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/pairing.py#L431-L437)).
All of these existed at the cited commit; none was examined then.

A messaging session's row names the platform and the people:
`sessions.source` is the platform (`telegram`, `discord`, `whatsapp`,
`whatsapp_cloud`, `slack`, `signal`, `mattermost`, `matrix`, `email`,
`sms`, `dingtalk`, `feishu`, `wecom`, `wecom_callback`, `weixin`,
`bluebubbles`, `qqbot`, `yuanbao`, `webhook`, `msgraph_webhook`, or a
plugin platform; `api_server` and `local` are not messaging platforms)
([`gateway/config.py:217-242`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/config.py#L217-L242)),
`user_id`, `chat_id`, `chat_type` (`dm`, `group`, `channel`, `thread`),
`thread_id`, `display_name` (the chat name) and `origin_json`, the
serialized source `{platform, chat_id, chat_name, chat_type, user_id,
user_name, thread_id, chat_topic, ...}`
([`gateway/session.py:68-80`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/session.py#L68-L80),
[`gateway/session.py:128-131`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/session.py#L128-L131),
[`gateway/session_recovery.py:336-345`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/session_recovery.py#L336-L345),
[`hermes_state_gateway.py:236-292`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_gateway.py#L236-L292),
[`run_agent.py:57-75`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/run_agent.py#L57-L75)).
A message that came through the experimental connector relay (a
generic adapter fed by a separate connector service) records the
underlying platform, not `relay`
([`gateway/session.py:99-102`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/session.py#L99-L102)).

## 4. Joins

- Message to session: `messages.session_id = sessions.id`; project path is
  `sessions.cwd` (or `git_repo_root`), branch `sessions.git_branch`.
- Tool use to result: `messages.tool_calls[].id` (or `call_id`) equals a
  later `role='tool'` row's `tool_call_id`. Hermes pairs on `call_id` then
  `id`, splitting at `|` ([`agent/message_sanitization.py:520-528`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/message_sanitization.py#L520-L528)).
- Parent to child: `sessions.parent_session_id`. A parent whose
  `end_reason='compression'` continues in its child; `'branched'` marks a
  `/branch` fork ([`hermes_state_common.py:169-174`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L169-L174)); `source='subagent'`
  rows are delegated tasks.
- System prompt: `sessions.system_prompt_hash = system_prompts.hash`.

## 5. SQLite specifics

WAL by default with a DELETE fallback on filesystems that refuse it
([`hermes_state_wal.py:254-262`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_wal.py#L254-L262)); read `state.db-wal` with the main file.
FTS5 tables `messages_fts` and `messages_fts_trigram`
([`hermes_state_common.py:785`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L785),[`905`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L905)) are indexes; skip them. Ended sessions
idle 90 days are pruned and the file may be VACUUMed
([`hermes_cli/config_defaults.py:2276-2285`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/config_defaults.py#L2276-L2285),
[`hermes_state_maintenance.py:421-445`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_maintenance.py#L421-L445)); older copies live in
`state-snapshots/*/state.db` ([section 2](#2-transcript-files)). No
compression or encryption.

What the copies survive and how they join. A snapshot is the whole
database at the snapshot time, so it outlives a session pruned after 90
idle days, a session deleted with `hermes sessions delete` (which removes
the rows and the session's files under `sessions/`), a VACUUM, and a
`state.db` replaced, rebuilt or quarantined; it does not see anything
written after it. Its rows join the live database's exactly: the same
`sessions.id`, the same `cwd` and `git_repo_root`, the same
`messages.timestamp` (the backup API copies the pages, not a re-encoding).
Two things make a snapshot row differ from its live twin: a message rewound
or compacted after the snapshot (live `active = 0`, so the parser's
`[rewound]` prefix), and a session whose `end_reason`, `title` or later
model was set after it (the session start row's text). Those rows are kept
from both. A divert holds messages the replaced database never received, so most
of its lines have no twin in the live database; a line does have one when
the same messages also reached a database the parser reads (a snapshot,
or a new `state.db` that a later flush wrote them to), and then it carries
the same session id and, when the line has one, the same `timestamp`.
Whether Hermes replays a divert into a new database was not determined;
the session-row heal of
[`agent/session_persistence.py:354-375`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/session_persistence.py#L354-L375)
replays the in-memory transcript only when a session row was deleted, a
different failure.

Deletion at the 2026-10-19 HEAD. Automatic pruning is off by default
since the cited commit: `sessions.auto_prune` was `true` at
[`hermes_cli/config_defaults.py:2276`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/config_defaults.py#L2276)
and is `false` now, with `retention_days` still 90 and the user asked
once when the disk runs low
([`hermes_cli/config_defaults.py:2279-2289`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/config_defaults.py#L2279-L2289)),
so on a current install old sessions stay in `state.db` unless the user
opted in or ran `hermes sessions prune`. `hermes sessions delete` (and
the dashboard and desktop deletes) removes the session, its whole local
reset or compression lineage when it has one, its delegate children,
their `messages` rows and the files under `sessions/` named after the id
(`<id>.json`, `<id>.jsonl`, `session_<id>.json`,
`request_dump_<id>_*.json`)
([`hermes_state_sessions.py:1628-1648`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_sessions.py#L1628-L1648),
[`hermes_state_sessions.py:1701-1770`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_sessions.py#L1701-L1770)).
New since the cited commit, every delete path, the prune sweep
included, first writes deletion fences into `state.db` `state_meta`
(a key and JSON value table) that outlive the rows
([`hermes_state_mutation_retirement.py:148-163`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_mutation_retirement.py#L148-L163)):
the key `gateway.retired_session.v1.<session id>` with
`{"retired_at": <epoch seconds>, "own": true}`, plus `"expires": true`
when a sweep rather than a delete removed it
([`hermes_state_mutation_retirement.py:9`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_mutation_retirement.py#L9),
[`hermes_state_mutation_retirement.py:286-300`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_mutation_retirement.py#L286-L300),
[`hermes_state_mutation_retirement.py:307-317`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_mutation_retirement.py#L307-L317)),
and, for each request the session had admitted, a
`gateway.terminal_admission.v1.<admission id>` row with the principal,
request id and digests and the payload emptied
([`hermes_state_mutation_retirement.py:100-140`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_mutation_retirement.py#L100-L140)).
The marker is the only record of when a session was deleted and of its
id; it holds no text. A deleted session's gateway routing entry is
dropped, but its `conversation_generations` row stays
([section 2](#2-transcript-files)). Archiving (`hermes sessions
archive`, the sidebar, the idle sweep `sessions.auto_archive`, off by
default) only sets `archived = 1` (and `auto_archived` for the sweep)
and keeps the messages
([`hermes_state_sessions.py:937-942`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_sessions.py#L937-L942),
[`hermes_state_sessions.py:1968-1980`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_sessions.py#L1968-L1980)).
None of these touches `.hermes_history`, `cron/output/`,
`response_store.db`, the snapshots or a memory provider's copy.

## 6. Format versions

`schema_version.version`, currently 31
([`hermes_state_common.py:283`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L283)); migrations add columns in
place ([`hermes_state_schema.py:1018-1059`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_schema.py#L1018-L1059)), so a parser must select
columns that exist (`PRAGMA table_info`). Gateway metadata was in
`sessions/sessions.json` before v18 ([`hermes_state_schema.py:1308-1311`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_schema.py#L1308-L1311)).
The legacy `session_<id>.json` layout was not examined.

Drift to the 2026-10-19 HEAD: `SCHEMA_VERSION` is 32
([`hermes_state_common.py:289`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_common.py#L289)).
`sessions` gained `runtime_revision`, `runtime_generation` and
`transcript_revision`
([`hermes_state_common.py:445-513`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_common.py#L445-L513)),
`messages` and `session_model_usage` are unchanged
([`hermes_state_common.py:515-568`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_common.py#L515-L568)),
and four tables of the unified runtime are new: `runtime_epoch`,
`session_admissions` (each queued, steered or redirected request against
a session, with `payload_json` and `status`), `worker_executions` and
`worker_receipts`
([`hermes_state_common.py:570-622`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state_common.py#L570-L622)).
Every file, table, column and constant the parser depends on was checked
at HEAD and is unchanged: `state.db`
([`hermes_state.py:180`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state.py#L180)),
the `\x00json:` prefix
([`hermes_state.py:1627`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state.py#L1627)),
the divert `sessions/<id>.jsonl`
([`hermes_state.py:434-441`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_state.py#L434-L441)),
`state-snapshots`
([`hermes_cli/backup.py:58`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/backup.py#L58))
and `pastes/pending.json` with its 21600-second lifetime
([`hermes_cli/debug.py:32`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/debug.py#L32),
[`hermes_cli/debug.py:43`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/debug.py#L43)).
The parser reads `select *`, so the new columns do not affect it. The
behaviour changes are the deletion fences and the prune default
([section 5](#5-sqlite-specifics)) and the `local-` session ids
([section 2](#2-transcript-files)).

## 7. Secrets

Tool-call `arguments` are stored unredacted on purpose
([`agent/chat_completion_helpers.py:1641-1642`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/chat_completion_helpers.py#L1641-L1642)); tool results,
`api_content` and `system_prompts.prompt` (which embeds memory and context
files) can carry secrets. `request_dump_*` files are redacted before
writing ([`agent_runtime_helpers.py:1629-1633`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/agent_runtime_helpers.py#L1629-L1633)). `sessions.origin_json`
holds messaging user and chat identifiers.

## 8. Parser plan

Inputs, under any Hermes home (a home's `.hermes`,
`.hermes_<suffix>`, `AppData/Local/hermes[_<suffix>]`, any of them
followed by `profiles/<name>`, or the root of a Docker or Podman named
volume's `_data`, which holds the Hermes home itself, as the next
paragraph but one says), each marked for the timeline's
deduplication (issue 122, see
[Secondary sources in `docs/output.md`](../docs/output.md#secondary-sources)):

| Source | Kind | Why |
| --- | --- | --- |
| `state.db` (via `sqlite_util`, so the WAL is read) | primary | the store of record for every front end |
| `state-snapshots/<id>/state.db` | secondary | an older copy of `state.db`; read with the same reader after one `system` row `state snapshot <id>: older copy of state.db`, timestamped from the id's UTC time when the id starts with one, else empty; rows pair with the live rows exactly, and the copies several snapshots keep of a pruned session collapse to the first |
| `sessions/<id>.jsonl` | secondary | a divert of messages `state.db` did not take; `session_id` from the file name, no project path (the match is by session id), each line's own `timestamp` or none |
| `sessions/<id>.json`, `session_<id>.json` | not read | no writer at the checked commit, shape unknown |
| `backups/*.zip`, `sessions/saved/*.json`, `response_store.db` | not read | archives and exports; `response_store.db` schema not examined |

Both secondary sources keep the default 2-second tolerance: their times
are copies of the live ones, not later stamps. Rows: one per message; an assistant row
with N `tool_calls` yields one `assistant` row (when `content` is non-empty),
one `thinking` row (when `reasoning`/`reasoning_content` is set), and N
`tool_use` rows. Order by `timestamp, id`. Include `active=0` rows: they are
evidence of rewound or compacted turns.

| Column | Source |
| --- | --- |
| timestamp_utc | `messages.timestamp` (epoch s) |
| session_id | `messages.session_id` |
| project_path | `sessions.cwd`, else `git_repo_root` |
| git_branch | `sessions.git_branch` |
| turn_type | `role`: `user` → user, `assistant` → assistant, `tool` → tool_result, `system` → system; `tool_calls[]` → tool_use; reasoning → thinking |
| model | `sessions.model` |
| tool_name | `tool_calls[].function.name`, or `messages.tool_name` |
| tool_use_id | `tool_calls[].id` / `messages.tool_call_id` |
| text | `content` (strip `\x00json:` and join text parts); for tool_use the `command`/`path` key of `arguments`, else the arguments |
| source_line | `messages.id` |

Model rows (issue 96), `system`, after each session's start row: the
session's `session_model_usage` rows with `task` empty, ordered by
`first_seen`, give `model: <model>` for the first and
`model: <old> -> <new>` for each later one, at `first_seen`, with
` provider=<billing_provider>` when it is set; auxiliary task rows are
skipped. The table aggregates per model, so a switch back to a model
already used is not visible. A session with no such rows gets one
`model: <sessions.model>` row at `started_at`. The `model` column of the
other rows stays `sessions.model`.

Model-switch markers (issue 180), `system`, in message order: each
`messages` row with `display_kind = 'model_switch'` is one row
`model: <old> -> <model> provider=<provider>` at the row's `timestamp`,
with `model` set to the new model and `source_line` to `messages.id`,
parsed from the marker text `[System: The active model for this chat
has changed to <model> via provider <provider>. From this point
forward, ...]` (the provider part only when one was set). The marker
names only the new model: `<old>` is the session's previous marker's
model, else the last main-loop `session_model_usage` model whose
`first_seen` is before the marker; with neither, or when it is the new
model, the row is `model: <model>` with the provider suffix. A later
switch sets the marker's `active` to 0, which is no rewind, so the row
has no `[rewound]` prefix, and a marker is never a `user` row. A marker
whose text has another form is a `system` row `model_switch: <text>`.
These rows sit beside the `session_model_usage` rows above, which show
the first API call on each model rather than the switch.

Malformed `tool_calls` (issue 182): a value that is not valid JSON, is
not a list (a lone object is read as a one-call list) or holds an entry
that is not an object gives one row through `error_rows`, after the
message's other rows, `parser: unparseable record <messages.id>
(tool_calls is not valid JSON: <reason>)`, `(tool_calls is not a
list)` or `(tool_calls entry is not an object)`, followed by `: ` and
the value as stored, with the message's `session_id` and project path
and an empty `timestamp_utc`; the entries that are objects still give
`tool_use` rows. A divert line uses the same rule, with `<N>` the line
number and the value written as compact JSON when it is not a string.

Volume homes (issue 181): the catalog's `hermes|*hermes*` volume line
collects a named volume whole with its `_data` directory as the base.
The container's Hermes home is `/opt/data`
([`docker-compose.yml:36-37`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/docker-compose.yml#L36-L37)),
so a named volume mounted there holds the Hermes home itself and the
files arrive as `state.db`, `sessions/<id>.jsonl`,
`state-snapshots/<id>/state.db`, `pastes/pending.json` and
`profiles/<name>/...` with no prefix. `wants()` accepts these as it
accepts the home forms, and the rows carry the manifest's `docker` user.

Permission: the pairing stores named in
[section 3 of `collectors/research/hermes.md`](../../collectors/research/hermes.md#3-credentials)
have no recorded shape and are not read, so there are no permission rows.

Per-class plan from the source review of 2026-10-19 (HEAD
[`86fa9e6`](https://github.com/NousResearch/hermes-agent/commit/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872));
the model-switch rows, the volume homes and the `tool_calls` rows are
implemented (issues 180, 181 and 182, above); the rest is not, and every
line rests on source alone, so each change starts with a per-step
real-install round:

- Permission (gap): the shape of the pairing store is now known
  ([section 3](#3-record-schema)). Proposed rows: after a `terminal`
  `tool_result` whose JSON has `approval`, `permission decision:
  approved (<approval note>)`; with `status` `blocked`, `permission
  decision: blocked <error>`; with `status` `pending_approval`,
  `permission decision: pending pattern=<pattern_key>
  smart_denied=<smart_denied>`, each with the call's `tool_name` and
  `tool_use_id`. One `permission setting: yolo_mode=true (from
  state.db sessions.model_config, started_at)` row per session whose
  `model_config` has it. From `config.yaml`, one `permission setting:
  <key>=<value> (from config.yaml, file mtime)` row per
  `command_allowlist` entry, `approvals.deny` entry and `approvals.mode`,
  `cron_mode`, `single_query_mode` and `unattended_mode`; from
  `pairing/<platform>-approved.json`, one `permission setting:
  pairing.<platform>.<user_id> user_name=<user_name> (from
  pairing/<platform>-approved.json, approved_at)` row per user at
  `approved_at`. Both files are collected (the pairing files flagged
  secret).
- Model (partly done): the `display_kind = 'model_switch'` rows are
  `model:` rows (issue 180, above). Still proposed: every other
  non-empty `display_kind` on a `user` row becomes a `system` row
  prefixed with the kind, so injected notices are not counted as typed
  prompts.
- Past use (gap): `.hermes_history` (secondary, `user` rows with the
  entry's time and no session; a slash command keeps its own row),
  `cron/output/*/*.md` (secondary, `user` from `## Prompt` and
  `assistant` from `## Response` at the file name's local time, no
  session id), `response_store.db` (secondary, `conversation_history`
  joined on `data.session_id`), the trajectory files (secondary, no
  session), and the `hosted_room_events` log (to be examined in the
  round). The `imported_from` object of `origin_json` should go on the
  session start row (`imported from <tool> <path> session
  <foreign_session_id>`), since the turns carry the import's time.
  `conversation_generations` gives no text; one `system` row per row,
  `relay peer: <source> <session_key> generation <n>`, with an empty
  `timestamp_utc`, would show chats whose sessions are gone.
- Sync, relay, origin (gap): relay. A session whose `source` is a
  messaging platform (every gateway platform but `local` and
  `api_server`) gets `session relayed: <source> chat <chat_id>
  (<chat_type>) user <user_id> <user_name from origin_json> display
  <display_name> (from state.db sessions, started_at)` after its start
  row, and the parser sets `records_relay`. Sync: `hermes sessions export
  --format trace --upload [--public]` converts a session to Claude Code
  JSONL and uploads it to the user's Hugging Face dataset
  `<user>/hermes-traces` as `sessions/<session id>.jsonl`, private unless
  `--public`, and writes nothing locally on success
  ([`agent/trace_upload.py:1-5`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/trace_upload.py#L1-L5),
  [`agent/trace_upload.py:209-221`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/trace_upload.py#L209-L221),
  [`hermes_cli/sessions_cmd.py:463-482`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/sessions_cmd.py#L463-L482));
  the only local traces are the command in the shell's own history and
  `HF_TOKEN` in `.env`, so no `session synced:` row is possible (the
  file existed at the cited commit; the earlier grep missed it).
  Origin: the desktop app's `connections.json` registry lists `local`,
  `remote` (a `hermes serve` the user runs), `ssh` and `cloud` (Hermes
  Cloud, Nous Research's hosted Hermes) connections; a session on a
  remote, SSH or cloud backend lives in that host's `state.db`, and
  whether the desktop keeps any local copy was not determined
  ([`apps/desktop/electron/main.ts:1349-1354`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/apps/desktop/electron/main.ts#L1349-L1354),
  [`apps/desktop/electron/connection-registry.ts:1-10`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/apps/desktop/electron/connection-registry.ts#L1-L10),
  [`apps/desktop/electron/connection-registry.ts:44-47`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/apps/desktop/electron/connection-registry.ts#L44-L47)).
  The parser does not read the desktop's `userData`; a `system` row per
  non-local connection (`session origin:` needs a session, so a plain
  `remote backend: <kind> <label> <url> (from connections.json, file
  mtime)`) is the proposal, after the round shows the file.
- Scratch directories (partial): `cache/scratch` and `sandboxes` are
  under the catalog's Hermes home, so the analyzer's catalog rule
  already classes them. A session whose `cwd` is a
  `<repo>/.worktrees/<name>` the agent made is listed as a project;
  proposed: a `scratch directory: <cwd> (git worktree the agent created
  under <repo>/.worktrees)` row when `cwd` has that shape and
  `git_branch` starts with `hermes/` or `hermes-subagent/`.
- Deletion (gap, new since the cited commit): one `session deleted:
  <id> (from state.db state_meta gateway.retired_session.v1, retired_at)`
  row per marker, at `retired_at`, with ` sweep` when it has `expires`;
  `archived=1` on the session start row.
- Version drift: none affects the parser
  ([section 6](#6-format-versions)). A Hermes home collected from a
  Docker or Podman named volume has its files at the volume root
  (`state.db`, not `.hermes/state.db`); `wants()` accepts that form
  since issue 181 (above).
- Bad lines: `sessions/<id>.jsonl` goes through `iter_jsonl` and
  `error_rows` and `pastes/pending.json` reports each bad entry. A
  `tool_calls` value that does not decode is an `error_rows` entry
  carrying the stored value since issue 182 (above); before it, a value
  that was not valid JSON was dropped with no row and one that parsed to
  something other than a list got a row of the parser's own without the
  value.

Sync: Hermes records no sync state for a session. Nothing uploads a
session, a transcript or a title to the Nous account: the Nous Portal
(Nous Research's account and billing site, `portal.nousresearch.com`)
is used for sign-in, inference and the tool gateway
([`hermes_cli/portal_cli.py:10-20`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/portal_cli.py#L10-L20)),
and a grep of the tree for session upload, sync, share and cloud-session
names found nothing beyond the paths below. `hermes sessions delete`
removes the rows and the session's files and calls nothing remote
([`hermes_state_sessions.py:1606-1650`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_sessions.py#L1606-L1650)).
Content does leave the host on these opt-in paths, none of which marks a
session:

- `hermes debug share` (CLI), `/debug` (gateway) and the dashboard's
  `POST /api/ops/debug-share` upload a report and the logs, whose own
  notice says they hold "Verbatim content of your recent messages", to
  paste.rs, falling back to dpaste.com
  ([`hermes_cli/debug.py:96-113`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L96-L113),
  [`hermes_cli/debug.py:442-479`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L442-L479),
  [`gateway/slash_commands.py:1213-1243`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/gateway/slash_commands.py#L1213-L1243),
  [`hermes_cli/web_routers/status.py:792-803`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/web_routers/status.py#L792-L803)).
  The CLI asks first unless `--yes` is given. The paste.rs links stay in
  `pastes/pending.json` for 6 to 30 hours
  ([section 2](#2-transcript-files)), and with redaction on (the default)
  `agent.log` gets the line `hermes debug share: applied force-mode
  redaction to log snapshots before upload`
  ([`hermes_cli/debug.py:451-453`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L451-L453)).
  `hermes debug share --nous` sends the same bundle to Nous's private
  diagnostics storage (an S3 bucket behind `portal.nousresearch.com`,
  kept 14 days) and only prints the view URL; its local trace is the log
  line `hermes debug share --nous: applied force-mode redaction before
  upload`
  ([`hermes_cli/diagnostics_upload.py:1-13`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/diagnostics_upload.py#L1-L13),
  [`hermes_cli/debug.py:578-605`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L578-L605)).
  `hermes debug delete <url>` deletes a paste.rs paste and does not
  touch `pending.json`
  ([`hermes_cli/debug.py:616-636`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/debug.py#L616-L636)).
- An external memory provider, set in `config.yaml` `memory.provider`
  (empty by default;
  [`hermes_cli/config_defaults.py:1325-1328`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/config_defaults.py#L1325-L1328)),
  receives every completed turn's user and assistant text with the
  session id
  ([`agent/memory_manager.py:535-557`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/memory_manager.py#L535-L557)):
  Mem0 (a hosted memory service, or self-hosted) at
  [`plugins/memory/mem0/__init__.py:302-313`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/plugins/memory/mem0/__init__.py#L302-L313),
  RetainDB through `retaindb_queue.db`
  ([`plugins/memory/retaindb/__init__.py:405-412`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/plugins/memory/retaindb/__init__.py#L405-L412),
  [section 2](#2-transcript-files)), ByteRover and OpenViking (local
  servers with an optional cloud), and the catalog-installed Honcho,
  Hindsight and Supermemory, whose code is not in this repository. The
  local traces are the provider name in `config.yaml`, its settings
  (`mem0.json`, `honcho.json`) and its key in `.env`; no file records
  which turns were sent, and deleting a session does not delete the
  provider's copy.
- The Langfuse plugin (Langfuse is an LLM tracing service, hosted or
  self-hosted), off unless enabled in `plugins.enabled` with keys in
  `.env`, exports prompts, replies and tool payloads, redacted and
  truncated by default, and writes no local file
  ([`plugins/observability/langfuse/__init__.py:1-7`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/plugins/observability/langfuse/__init__.py#L1-L7)).
- Shared metrics (`config.yaml` `telemetry.shared_metrics.enabled` and
  `.send`, both off by default) are counters only, "Never prompts,
  files, paths", kept in `telemetry/shared_metrics/` and sent daily to
  `telemetry.nousresearch.com` when `send` is on
  ([`hermes_cli/config_defaults.py:2337-2349`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/config_defaults.py#L2337-L2349),
  [`hermes_cli/observability/shared_metrics_consent.py:29-36`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/observability/shared_metrics_consent.py#L29-L36),
  [`hermes_cli/observability/shared_metrics.py:191-193`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/observability/shared_metrics.py#L191-L193)).

A gateway session's messages also live on the messaging platform, which
is the channel the user typed in, not a sync; `sessions.chat_id`,
`origin_json` and `messages.platform_message_id` name them there
([section 3](#3-record-schema)). The parser yields no `session synced:`
row and leaves `records_sync` off. It reads `pastes/pending.json` and
yields one `system` row per entry, `debug report uploaded: <url> (from
pastes/pending.json, expire_at minus 6 hours)`, timestamped `expire_at`
minus 21600 seconds with an empty `session_id`, which shows that logs
left the host in the last day and marks no session; a file that is not a
JSON list is one `parser:` row. Fixture only: no real install has shown
the file.

Fixture:

```sql
CREATE TABLE schema_version (version INTEGER NOT NULL);
INSERT INTO schema_version VALUES (31);
CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT NOT NULL, model TEXT,
  parent_session_id TEXT, started_at REAL NOT NULL, ended_at REAL, end_reason TEXT,
  cwd TEXT, git_branch TEXT, git_repo_root TEXT, title TEXT);
CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
  role TEXT NOT NULL, content TEXT, tool_call_id TEXT, tool_calls TEXT, tool_name TEXT,
  timestamp REAL NOT NULL, finish_reason TEXT, reasoning TEXT, reasoning_content TEXT,
  active INTEGER NOT NULL DEFAULT 1, compacted INTEGER NOT NULL DEFAULT 0);
INSERT INTO sessions VALUES ('20261001_120000_a1b2c3d4','cli','anthropic/claude-sonnet-4',NULL,
  1759320000.0,NULL,NULL,'/home/u/repo','main','/home/u/repo','List files');
INSERT INTO messages (session_id,role,content,tool_call_id,tool_calls,tool_name,timestamp,finish_reason,reasoning) VALUES
 ('20261001_120000_a1b2c3d4','user','list files',NULL,NULL,NULL,1759320001.25,NULL,NULL),
 ('20261001_120000_a1b2c3d4','assistant','',NULL,
  '[{"id":"call_1","call_id":"call_1","response_item_id":null,"type":"function","function":{"name":"terminal","arguments":"{\"command\":\"ls\"}"}}]',
  NULL,1759320002.5,'tool_calls','User wants a listing.'),
 ('20261001_120000_a1b2c3d4','tool','a.txt\nb.txt','call_1',NULL,'terminal',1759320003.0,NULL,NULL),
 ('20261001_120000_a1b2c3d4','assistant','Two files: a.txt, b.txt.',NULL,NULL,NULL,1759320004.0,'stop',NULL);
```

Confidence. High: table and column names, timestamp unit, content prefix,
tool-call shape, joins, WAL. Medium: the full set of `role` values (only the
four above seen in queries) and `source` values beyond the stale-open list.
The shell tool is registered as `terminal`
([`tools/terminal_tool.py:1634`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/tools/terminal_tool.py#L1634)). Not determined: `response_store.db` and legacy
`session_<id>.json` schemas.
