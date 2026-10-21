"""Open Interpreter transcripts.

The current Open Interpreter is a Rust fork of Codex CLI that keeps Codex's
rollout format and moves the home to `~/.openinterpreter`; checked against
openinterpreter/openinterpreter at 2767e5f (see
`research/open-interpreter.md`). Rollouts and history are read by the shared
`RolloutParser` in `codex.py`, so the field names listed there apply. Files:

* `.openinterpreter/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl`
  and the same under `.openinterpreter/archived_sessions/`, plain or
  `.jsonl.zst` (`rollout/src/lib.rs:84-85`, `rollout/src/compression.rs:25`).
  `session_meta.originator` is still `codex_cli_rs` in the fork, so only the
  file's location tells it from Codex. Tool names follow the emulated
  harness (`Bash`, `Read` under the claude-code harness), not the Codex set.
  `turn_context` keeps Codex's `model`, `approval_policy`,
  `sandbox_policy`, `permission_profile` and `network`
  (`protocol/src/protocol.rs:3287-3343`), so the shared reader's
  `model:` and `permission mode:` rows apply unchanged. The fork, like
  Codex, keeps approval requests out of the rollout
  (`rollout/src/policy.rs:140-204`), so there is no per-call decision row.
* `.openinterpreter/history.jsonl`: `{session_id, ts, text}`. A secondary
  source: the timeline drops a line whose event a rollout also records
  (`dedup.py`).
* `.openinterpreter/state_5.sqlite` and
  `.openinterpreter/thread_history_1.sqlite`: the fork keeps Codex's
  SQLite set under its own home (`state/src/sqlite.rs:29-34`), with the
  same `threads` columns and the thread history schema up to migration
  0006, without the item lifecycle times of Codex's 0007. Read by the
  shared reader in `codex_state.py` as secondary sources; every item row
  then takes `created_at_ms`.
* `.openinterpreter/logs_2.sqlite`: Codex's tracing log, kept by the fork
  with the same `logs` table and the same `/feedback` row
  (`feedback/src/lib.rs:682-688`), which still reports to OpenAI's Sentry
  project. Read by the shared reader in `codex_state.py`: one `session
  synced: feedback report uploaded to Sentry, ...` row per sent report,
  so `records_sync` is inherited and set.
* `.openinterpreter/config.toml`, `.openinterpreter/rules/*.rules`,
  `.openinterpreter/memories/rollout_summaries/*.md` and
  `.openinterpreter/db-backups/sqlite-*/state_5.sqlite`: the standing
  grants, memory summaries and database backups the fork keeps from Codex
  at ac1fcc8 (`core/src/exec_policy.rs:54-56`,
  `memories/write/src/storage.rs:110-136`,
  `state/src/runtime/recovery.rs:12`), read by the shared reader as for
  Codex (source-derived). The fork's core logs no approval decision and
  has no `guardian_review_feedback` table, so those rows cannot occur.
* `.openinterpreter/external_agent_session_imports.json`: the `/import`
  ledger, `records[]` with `source_path`, `content_sha256`,
  `imported_thread_id`, `imported_at` and optional `source_modified_at`
  (epoch seconds; `external-agent-sessions/src/ledger.rs:18-30`). Each
  record becomes one `system` row with the imported thread's id as
  `session_id`, so the analyst can see that the turns of that rollout were
  authored in another agent (Claude Code or Cursor) and that their record
  timestamps are import time.

Not parsed: `session_index.jsonl` (thread renames) and the zcode harness's
oversized tool results under `.zcode/cli/artifacts/`.
"""

from __future__ import annotations

from .codex import RolloutParser


class OpenInterpreterParser(RolloutParser):
    agent = "open-interpreter"
    name = "open-interpreter"
    home_prefix = ".openinterpreter"
    ledger_name = "external_agent_session_imports.json"
