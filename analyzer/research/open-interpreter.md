# Open Interpreter transcript schema

Catalog agent: `open-interpreter`. The current Open Interpreter is a Rust
fork of OpenAI Codex CLI that keeps Codex's protocol and file formats and
moves the home to `~/.openinterpreter` (see
[../../collectors/research/open-interpreter.md](../../collectors/research/open-interpreter.md)).
Transcripts are Codex rollouts, byte for byte, so the existing Codex parser
(`doubleagent/parsers/codex.py`) is the reference and this document
records only what was checked in the fork and what differs. Paths cited are
relative to `codex-rs/` in the clone.

## 1. Source

[openinterpreter/openinterpreter](https://github.com/openinterpreter/openinterpreter) at
[`2767e5f20d6927500b8f1938c773c61afb823245`](https://github.com/openinterpreter/openinterpreter/commit/2767e5f20d6927500b8f1938c773c61afb823245),
Apache-2.0, open source.

- **Source review (2026-10-19)**: [openinterpreter/openinterpreter](https://github.com/openinterpreter/openinterpreter)
  at [`ac1fcc8`](https://github.com/openinterpreter/openinterpreter/commit/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87),
  the head of `main` on 2026-10-19 (workspace version 0.0.56,
  [`codex-rs/Cargo.toml:163`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/Cargo.toml#L163)),
  compared file by file with
  [`2767e5f`](https://github.com/openinterpreter/openinterpreter/commit/2767e5f20d6927500b8f1938c773c61afb823245)
  (0.0.55), the commit cited below. Only four files differ: the Codex
  compatibility profile the fork announces to the model service moved
  from 0.156.1 to 0.159.0
  ([`codex-rs/product-info/src/lib.rs:12`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/product-info/src/lib.rs#L12)),
  with its tests and the version numbers. The fork has not taken
  Codex's changes after its snapshot, so the Codex findings of the same
  day ([section 1 of `codex-cli.md`](codex-cli.md#1-evidence)) apply
  only where noted. Source only. By class:
  - Permission state: found, not read, as in Codex: `rules/default.rules`
    ([`codex-rs/core/src/exec_policy.rs:54-56`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/core/src/exec_policy.rs#L54-L56)),
    `config.toml` project `trust_level`
    ([`codex-rs/core/src/config/mod.rs:2373`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/core/src/config/mod.rs#L2373))
    and tool `approval_mode`
    ([`codex-rs/core/src/mcp_tool_call.rs:2291`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/core/src/mcp_tool_call.rs#L2291),
    [`2334`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/core/src/mcp_tool_call.rs#L2334),
    [`2369`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/core/src/mcp_tool_call.rs#L2369)).
    Differs from Codex: the core logs a submission with its kind only,
    `operation=exec_approval`, never the decision
    ([`codex-rs/core/src/session/handlers.rs:421`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/core/src/session/handlers.rs#L421)),
    so the `op=ExecApproval` rows the shared reader turns into
    `permission decision:` rows cannot occur; the app server's
    `<- response:` line with the decision is still logged
    ([`codex-rs/app-server/src/outgoing_message.rs:481`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/app-server/src/outgoing_message.rs#L481)),
    and the fork has no `guardian_review_feedback` table (its state
    migrations stop at `0055_thread_attachments.sql`).
  - Model: covered; unchanged.
  - Past use: as in Codex, the memories files (off by default,
    [`codex-rs/features/src/lib.rs:1148-1150`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/features/src/lib.rs#L1148-L1150))
    and `db-backups/`
    ([`codex-rs/state/src/runtime/recovery.rs:12`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/state/src/runtime/recovery.rs#L12))
    exist and are not read; the import ledger is read.
  - Sync, relay and origin: covered; unchanged.
  - Scratch directories: found: thread worktrees in
    `.openinterpreter/worktrees` unless `[desktop] git-worktree-root`
    names another path
    ([`codex-rs/worktree/src/settings.rs:12`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/worktree/src/settings.rs#L12),
    [`44`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/worktree/src/settings.rs#L44)),
    classed by the analyzer's catalog rule.
  - Deletion: as in Codex: `thread/delete` removes the rollouts, the
    index lines and the thread's rows, `logs_2.sqlite` rows included
    ([`codex-rs/state/src/runtime/threads.rs:1153`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/state/src/runtime/threads.rs#L1153),
    [`codex-rs/thread-store/src/local/delete_thread.rs:262`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/thread-store/src/local/delete_thread.rs#L262)),
    and leaves `history.jsonl` and the import ledger.
  - Version drift: none in the record shapes; `turn_context` still has
    `network` here
    ([`codex-rs/protocol/src/protocol.rs:3318`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/protocol/src/protocol.rs#L3318)),
    unlike Codex at HEAD.
  - Bad lines: the shared reader's gap: a bad `thread_history_1.sqlite`
    `item_json` is counted, not shown
    ([section 8 of `codex-cli.md`](codex-cli.md#8-parser-plan-the-existing-parser)).

## 2. Transcript files

- `.openinterpreter/sessions/YYYY/MM/DD/rollout-<YYYY-MM-DDThh-mm-ss>-<thread uuid>.jsonl`,
  one file per thread, and the same under `.openinterpreter/archived_sessions/`
  ([`rollout/src/lib.rs:84-85`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/lib.rs#L84-L85),
  [`rollout/src/rollout_file_name.rs:64-67`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/rollout_file_name.rs#L64-L67)). The directory date and
  the file name time are local time
  ([`rollout/src/recorder.rs:1700-1712`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/recorder.rs#L1700-L1712)); record timestamps are UTC.
  A rollout may be stored as `.jsonl.zst`
  ([`rollout/src/compression.rs:25`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/compression.rs#L25),[`94`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/compression.rs#L94)).
- `.openinterpreter/history.jsonl`: one line per submitted prompt, all
  sessions ([`message-history/src/lib.rs:52`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/message-history/src/lib.rs#L52),[`86`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/message-history/src/lib.rs#L86)).
- `.openinterpreter/session_index.jsonl`: `{id, thread_name, updated_at}`
  per rename ([`rollout/src/session_index.rs:21-29`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/session_index.rs#L21-L29)).
- `.openinterpreter/external_agent_session_imports.json`: which rollouts
  were imported from Claude Code or Cursor ([section 4](#4-joins)).
- `.openinterpreter/.zcode/cli/artifacts/sess_<session id>/<call id>-tool-result-<uuid>.json`:
  full output of a tool call that was too long to inline under the zcode
  harness ([`core/src/tools/handlers/harness_aliases.rs:887-902`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/core/src/tools/handlers/harness_aliases.rs#L887-L902)).

## 3. Record schema

Each line is `RolloutLine`: `timestamp`, optional `ordinal`, and the
flattened item ([`history/src/lib.rs:277-284`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/history/src/lib.rs#L277-L284)), serialised as
`{"type": <snake_case variant>, "payload": {...}}` with an optional
`metadata` on `response_item`
([`history/src/rollout_payload.rs:22-62`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/history/src/rollout_payload.rs#L22-L62)). `timestamp` is UTC,
`YYYY-MM-DDThh:mm:ss.mmmZ` ([`rollout/src/recorder.rs:2054-2059`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/recorder.rs#L2054-L2059)).
Types: `session_meta`, `response_item`, `inter_agent_communication`,
`inter_agent_communication_metadata`, `compacted`, `turn_context`,
`token_usage_record`, `world_state`, `retained_context`,
`security_risk_score`, `event_msg`, `realtime_item`.

- `session_meta` payload ([`protocol/src/protocol.rs:3117-3154`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/protocol.rs#L3117-L3154)):
  `session_id`, `id` (thread), `forked_from_id?`, `parent_thread_id?`,
  `timestamp`, `cwd`, `runtime_workspace_roots?`, `originator`,
  `cli_version`, `source`, `agent_nickname?`, `agent_role?`, `agent_path?`,
  `model_provider`, `base_instructions`; plus `git` with `commit_hash`,
  `branch`, `repository_url` ([`protocol.rs:3222-3228`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/protocol.rs#L3222-L3228),
  [`3423-3437`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/protocol.rs#L3423-L3437)). `originator` defaults to `codex_cli_rs` in the
  fork too ([`login/src/auth/default_client.rs:42`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/login/src/auth/default_client.rs#L42),[`64-68`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/login/src/auth/default_client.rs#L64-L68)), so
  only the file's location tells Open Interpreter from Codex.
- `turn_context`: `turn_id`, `cwd`, `model`, `approval_policy`,
  `sandbox_policy`, `permission_profile`, `network`, `timezone`, `effort`
  and more, the same field names as Codex's `turn_context`
  ([`protocol.rs:3287-3343`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/protocol.rs#L3287-L3343)). The emulated harness
  (`claude-code`, `kimi-code`, `zcode` and others) is a `config.toml` key
  ([`config/src/config_toml.rs:166-170`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/config/src/config_toml.rs#L166-L170)) and is not recorded per turn.
- `response_item` payload, tagged by `type`
  ([`protocol/src/models.rs:1009-1011`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/models.rs#L1009-L1011)): `message` (`role`, `content`
  blocks, `phase?`; [`1020-1035`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/models.rs#L1020-L1035)), `reasoning` (`summary`,
  `content?`, `encrypted_content`; [`1047-1059`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/models.rs#L1047-L1059)), `local_shell_call`
  (`call_id`, `status`, `action`; [`1060-1072`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/models.rs#L1060-L1072)), `function_call`
  (`name`, `namespace?`, `arguments` JSON string, `call_id`;
  [`1073-1092`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/models.rs#L1073-L1092)), `function_call_output` (`call_id`, `name?`, `output`;
  [`1113-1132`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/models.rs#L1113-L1132)), `custom_tool_call`, `custom_tool_call_output`,
  `tool_search_call`, `tool_search_output`, `web_search_call`. The harness
  emulation renames tools (`Bash`, `Read`, `Grep` and so on in the
  claude-code harness, [`core/src/harness/claude_code.rs:1287`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/core/src/harness/claude_code.rs#L1287)), so `name` values are not the Codex set.
- `event_msg`: UI events (`task_started`, `task_complete`, `token_count`,
  ...), as in Codex.

`history.jsonl`: `{session_id, ts, text}`, `ts` epoch seconds
([`message-history/src/lib.rs:62-66`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/message-history/src/lib.rs#L62-L66),[`128-131`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/message-history/src/lib.rs#L128-L131)).

## 4. Joins

Session to project: `session_meta.payload.cwd`, updated per turn by
`turn_context.payload.cwd`. Tool call to result: `call_id`. Subagent to
parent: `session_meta.payload.parent_thread_id` and `forked_from_id`.
Imported chats: `external_agent_session_imports.json` `records[]` with
`source_path` (the original `~/.claude/projects/...` or `~/.cursor/...`
file), `content_sha256`, `imported_thread_id` (the rollout's thread id) and
`imported_at`, `source_modified_at` (epoch)
([`external-agent-sessions/src/ledger.rs:18-30`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/external-agent-sessions/src/ledger.rs#L18-L30)). A rollout whose thread id
is in that ledger was written by `/import`
([`external-agent-sessions/src/export.rs:58-73`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/external-agent-sessions/src/export.rs#L58-L73)), so its turns were
authored in another agent and their record timestamps are import time.

## 5. SQLite or binary stores

Same SQLite set as Codex (`state_5.sqlite`, `logs_2.sqlite`,
`thread_history_1.sqlite` and others;
[`state/src/sqlite.rs:29-34`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/src/sqlite.rs#L29-L34)); the rollouts are the primary record. zstd
for `.jsonl.zst` rollouts.

`state_5.sqlite` and `thread_history_1.sqlite` are parsed as secondary
sources by the shared Codex reader (issue 122); their record shapes, joins
and what they survive are in
[section 5 of `codex-cli.md`](codex-cli.md#5-other-files). The fork's
`threads` migrations that the parser reads match Codex's
([`state/migrations/0001_threads.sql:1-19`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/migrations/0001_threads.sql#L1-L19),
[`0007_threads_first_user_message.sql:1`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/migrations/0007_threads_first_user_message.sql#L1),
[`0025_thread_timestamps_millis.sql:1-2`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/migrations/0025_thread_timestamps_millis.sql#L1-L2)),
and the thread history migrations stop at 0006
([`state/thread_history_migrations/0006_thread_turn_ends.sql:1-3`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/thread_history_migrations/0006_thread_turn_ends.sql#L1-L3)):
there is no `started_at_ms` or `completed_at_ms` on `thread_items`, so
`created_at_ms`, the item's start or the rollout line's time
([`thread-store/src/local/thread_history.rs:431-438`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/thread-store/src/local/thread_history.rs#L431-L438)),
stamps every item row, and an `agentMessage` row precedes its rollout
twin by the time the message took to stream.

### What survives a delete

As in Codex, `thread/delete` removes the thread's rollouts, its index
lines and its rows in the SQLite stores, `logs_2.sqlite` included, and
with them the `session synced:` Sentry feedback marker
([`codex-rs/state/src/runtime/threads.rs:1153`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/state/src/runtime/threads.rs#L1153),
[`codex-rs/thread-store/src/local/delete_thread.rs:262`](https://github.com/openinterpreter/openinterpreter/blob/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87/codex-rs/thread-store/src/local/delete_thread.rs#L262)).
It leaves `history.jsonl`, one line per submitted prompt with its session
id and time, and the import ledger
`external_agent_session_imports.json`, which names the rollouts imported
from Claude Code or Cursor. The memories files (off by default) and
`db-backups/` exist as in Codex ([section 1](#1-source)); what a delete
does to them is not stated in this document. No deletion marker is
written. The analyzer reads `history.jsonl`, `state_5.sqlite` and
`thread_history_1.sqlite` as secondary sources and the import ledger to
mark imported rollouts ([section 8](#8-parser-plan)), and does not read
the memories files or `db-backups/` (see
[Secondary sources](../docs/output.md#secondary-sources)).

## 6. Format versions

Tracks upstream Codex; no fork-specific version marker in the records.
`cli_version` in `session_meta` is the fork's version.

## 7. Secrets

Not in rollouts by design, but tool arguments and outputs can carry pasted
keys. `reasoning.encrypted_content` is an opaque provider blob. The
credential files (`auth.json`, `credentials/kimi-code.json`, `.env`) are
listed in the [collector document](../../collectors/research/open-interpreter.md).

## 8. Parser plan

Reuse `CodexParser`, matching `.openinterpreter/sessions/` and
`.openinterpreter/archived_sessions/` rollouts and
`.openinterpreter/history.jsonl` with agent `open-interpreter`. The current
parser matches only `^\.codex/sessions/` and plain `.jsonl`; extending it to
`archived_sessions/` and `.jsonl.zst` would fix Codex as well. Mark rollouts
listed in the import ledger with a `system` row naming `source_path`.
The rollouts are the primary store; `history.jsonl`, `state_5.sqlite` and
`thread_history_1.sqlite` are secondary sources, read as for Codex
([section 8 of `codex-cli.md`](codex-cli.md#8-parser-plan-the-existing-parser)).

| Column | Source |
| --- | --- |
| timestamp_utc | line `timestamp`; history `ts` (s) |
| session_id | `session_meta.payload.id` |
| project_path | `turn_context.payload.cwd`, else `session_meta.payload.cwd` |
| git_branch | `session_meta.payload.git.branch` |
| turn_type | `message` by role; `function_call`, `custom_tool_call`, `local_shell_call`, `web_search_call` → tool_use; `*_output` → tool_result; `reasoning` → thinking; `task_started`/`task_complete` → system |
| model | `turn_context.payload.model` |
| model row | `system` `model: <model>` at the first `turn_context` that names one, `model: <old> -> <new>` at each change (the shared Codex reader) |
| permission mode row | `system` `permission mode: approval=<approval_policy> sandbox=<sandbox_policy> profile=<permission_profile> network=<network>` at the first `turn_context` with any of them and `permission mode: <old> -> <new>` on every change, `-` for a missing field |
| tool_name, tool_use_id | `name`, `call_id` |
| text | message text, `arguments`/`input`/`action.command`, `output` |

Sync: as for Codex (the `Sync:` paragraph of
[section 8 of `codex-cli.md`](codex-cli.md#8-parser-plan-the-existing-parser)),
the fork records no session sync and has the same exits, unchanged:
`/feedback` ("send logs to maintainers";
[`tui/src/slash_command.rs:93`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/tui/src/slash_command.rs#L93))
still reports to OpenAI's Sentry project, not to an Open Interpreter
one ([`feedback/src/lib.rs:56-57`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/feedback/src/lib.rs#L56-L57)),
attaches the thread's rollouts when the user agrees to upload logs
([`app-server/src/request_processors/feedback_processor.rs:200-215`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/app-server/src/request_processors/feedback_processor.rs#L200-L215)),
is on by default
([`core/src/config/mod.rs:4403-4407`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/core/src/config/mod.rs#L4403-L4407))
and logs `feedback event uploaded to Sentry` with the thread id
([`feedback/src/lib.rs:682-688`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/feedback/src/lib.rs#L682-L688))
into `.openinterpreter/logs_2.sqlite`
([`state/src/sqlite.rs:29`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/src/sqlite.rs#L29)), the
marker and the `session synced: feedback report uploaded to Sentry,
...` row Codex has, which the shared reader yields for the fork too
(fixture only), removed by
the fork's thread delete as in Codex
([`state/src/runtime/threads.rs:1153`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/src/runtime/threads.rs#L1153)).
`codex cloud` (here "Browse remote tasks";
[`cli/src/main.rs:239-241`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/cli/src/main.rs#L239-L241)) still
targets `https://chatgpt.com/backend-api/` by default
([`core/src/config/mod.rs:4341-4343`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/core/src/config/mod.rs#L4341-L4343))
and writes the same `error.log` line in its working directory
([`cloud-tasks-client/src/http.rs:377`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/cloud-tasks-client/src/http.rs#L377),
[`916`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/cloud-tasks-client/src/http.rs#L916)); remote control
keeps the `remote_control_enrollments` table
([`state/migrations/0024_remote_control_enrollments.sql:1-10`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/state/migrations/0024_remote_control_enrollments.sql#L1-L10));
the thread store is local only
([`core/src/config/mod.rs:597-603`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/core/src/config/mod.rs#L597-L603)).
The fork adds no share, sync or upload feature of its own (searched
`sync`, `share`, `upload`, `cloud`, `remote` in the crates absent
upstream: `acp-server`, `chat-wire-compat`, `external-agent-sessions`,
`product-info`, `mcp-server`, `execpolicy-legacy`).

There is no per-call decision row: the fork, like Codex, lists the
approval request events among the transient events the rollout never
stores ([`rollout/src/policy.rs:140-204`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/rollout/src/policy.rs#L140-L204)).

Source review of 2026-10-19 at
[`ac1fcc8`](https://github.com/openinterpreter/openinterpreter/commit/ac1fcc8fe57aba51fcc3c79afd57a0883237fe87),
by class (detail in [section 1](#1-source)):

- Permission: the standing grants of `rules/default.rules` and
  `config.toml` are not read, as in Codex; per-call decisions can come
  only from the app server's response lines, since the core does not log
  the decision.
- Model: covered.
- Past use: memories and `db-backups/` not read, as in Codex.
- Sync, relay and origin: covered; the fork records no relay or origin.
- Scratch directories: worktrees under `.openinterpreter/worktrees`,
  classed by the catalog rule; no row names them.
- Deletion: no marker; as in Codex.
- Drift: none since the cited commit. The paragraph above that says the
  parser matches only `^\.codex/sessions/` and plain `.jsonl` predates
  the shared `RolloutParser`, which reads `archived_sessions/` and
  `.jsonl.zst` for both agents.
- Bad lines: the shared `thread_history_1.sqlite` summary row.

Fixture (`.openinterpreter/sessions/2026/10/01/rollout-2026-10-01T12-00-00-0199a1b2-0000-7000-8000-000000000001.jsonl`):

```json
{"timestamp":"2026-10-01T10:00:00.000Z","type":"session_meta","payload":{"session_id":"0199a1b2-0000-7000-8000-000000000001","id":"0199a1b2-0000-7000-8000-000000000001","timestamp":"2026-10-01T10:00:00.000Z","cwd":"/home/alice/proj","originator":"codex_cli_rs","cli_version":"0.9.0","source":"cli","model_provider":"kimi-for-coding","git":{"branch":"main"}}}
{"timestamp":"2026-10-01T10:00:01.000Z","type":"turn_context","payload":{"turn_id":"t1","cwd":"/home/alice/proj","approval_policy":"on-request","sandbox_policy":{"type":"workspace-write"},"model":"kimi-k3"}}
{"timestamp":"2026-10-01T10:00:01.100Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"list the files"}]}}
{"timestamp":"2026-10-01T10:00:03.000Z","type":"response_item","payload":{"type":"function_call","name":"Bash","arguments":"{\"command\":\"ls\"}","call_id":"call_1"}}
{"timestamp":"2026-10-01T10:00:04.000Z","type":"response_item","payload":{"type":"function_call_output","call_id":"call_1","output":"README.md"}}
```

`external_agent_session_imports.json`:
`{"records":[{"source_path":"/home/alice/.claude/projects/-home-alice-proj/5b1c.jsonl","content_sha256":"ab12...","imported_thread_id":"0199a1b2-0000-7000-8000-000000000002","imported_at":1759312800}]}`

Confidence. High: file locations, line envelope, timestamp format, payload
field names (shared structs), the ledger's `records` key (no serde
rename on the struct), `input_text` content blocks ([`protocol/src/models.rs:876-880`](https://github.com/openinterpreter/openinterpreter/blob/2767e5f20d6927500b8f1938c773c61afb823245/codex-rs/protocol/src/models.rs#L876-L880)). Not determined: the exact tool names each emulated harness emits, which
vary by harness module.
