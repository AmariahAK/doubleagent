# Hermes Agent transcript schema

Catalog agent: `hermes`. Hermes stores every conversation (CLI, TUI,
desktop, messaging gateway, cron, subagents) in one SQLite database per
profile home, in OpenAI chat-completions message shape. Paths in
[`collectors/research/hermes.md`](../../collectors/research/hermes.md).

## 1. Source

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) at [`8b66a51036c1e20920a17cdd049fdf55c968d683`](https://github.com/NousResearch/hermes-agent/commit/8b66a51036c1e20920a17cdd049fdf55c968d683),
MIT ([`LICENSE`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/LICENSE#L1-L3)). Open source, Python. Read only, not run.

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

## 6. Format versions

`schema_version.version`, currently 31
([`hermes_state_common.py:283`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L283)); migrations add columns in
place ([`hermes_state_schema.py:1018-1059`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_schema.py#L1018-L1059)), so a parser must select
columns that exist (`PRAGMA table_info`). Gateway metadata was in
`sessions/sessions.json` before v18 ([`hermes_state_schema.py:1308-1311`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_schema.py#L1308-L1311)).
The legacy `session_<id>.json` layout was not examined.

## 7. Secrets

Tool-call `arguments` are stored unredacted on purpose
([`agent/chat_completion_helpers.py:1641-1642`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/chat_completion_helpers.py#L1641-L1642)); tool results,
`api_content` and `system_prompts.prompt` (which embeds memory and context
files) can carry secrets. `request_dump_*` files are redacted before
writing ([`agent_runtime_helpers.py:1629-1633`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/agent_runtime_helpers.py#L1629-L1633)). `sessions.origin_json`
holds messaging user and chat identifiers.

## 8. Parser plan

Inputs, under any Hermes home, each marked for the timeline's
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

Permission: the pairing stores named in
[section 3 of `collectors/research/hermes.md`](../../collectors/research/hermes.md#3-credentials)
have no recorded shape and are not read, so there are no permission rows.

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
([section 3](#3-record-schema)). Proposed: no `session synced:` row. A
`system` row per `pastes/pending.json` entry, `debug report uploaded:
<url> (from pastes/pending.json, expire_at minus 6 hours)`, timestamped
`expire_at` minus 21600 seconds with an empty `session_id`, would show
that logs left the host in the last day; it marks no session.

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
