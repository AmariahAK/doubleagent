# chatgpt-desktop

OpenAI's ChatGPT desktop app is a closed-source Electron app (Electron:
a desktop framework that runs a web user interface in a bundled
Chromium) that on Windows and macOS
bundles Codex, OpenAI's coding agent. The app's prompt box, the
composer, has a mode dropdown with two entries (build 26.1013.40934 on
macOS, 2026-10-18): **Codex** mode starts a local Codex thread, whose
rollout (Codex's JSONL transcript) goes to `~/.codex/sessions` and is
read by the `codex-cli` parser ([`codex-cli.md`](codex-cli.md)); the
**ChatGPT** entry lists the account's conversations on chatgpt.com,
OpenAI's web chat service. A ChatGPT-mode conversation keeps its text on
OpenAI's servers and leaves no transcript on disk. This document covers
the one local trace it does leave: a row in the app's own database,
`~/.codex/sqlite/codex-dev.db`, which the `chatgpt-desktop` parser
turns into timeline rows. Paths, credentials and exclusions are in
[`collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md).
[Issue 49](https://github.com/seanthegeek/doubleagent/issues/49) tracks
the parser.

## 1. Source and evidence

Closed source, so there are no commit links, and the app's client code is
not in the Codex repository: a search of the Codex source for
`codex-dev.db`, `local_thread_catalog`, `conversation_origin` and
`chatgpt_async_status` finds nothing
([section 8 of `codex-cli.md`](codex-cli.md#8-parser-plan)).
Every claim below is from a real install, read for file names, sizes,
table and column names, value types, enum values and row counts only;
no conversation title or id from an install is reproduced here.

### Observed

- macOS, ChatGPT 26.1013.40934, 2026-10-18: the author's macOS lab VM (macOS 26.6.2, build 25G83, arm64, one user), the app
  with its bundled Codex `0.163.0-alpha.10.2`, with a listing diff after
  every step; the full round is in
  [section 1 of `collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md#1-source-and-evidence)
  and [section 1 of `codex-cli.md`](codex-cli.md#1-source-and-evidence).
  What it showed of this table:
  - Before sign-in `codex-dev.db` already existed. Signing in
    (18:31:28Z to 18:32:34Z) wrote three `local_thread_catalog` rows with
    `source_kind` `chatgpt`, before any chat on that VM: the account's
    conversations, dated 2026-10-15, from the Windows round below, each
    with `display_title` set, `conversation_origin` empty twice and `tpp`
    once, `missing_candidate` 0, and `thread_source`, `model_provider`,
    `cwd`, `git_branch`, `project_id`, `trial_conversation_type` and
    `chatgpt_async_status` NULL. The conversations of the 2026-10-15
    macOS round below were not among them; why was not determined.
    `local_thread_catalog_hosts` gained two rows and
    `local_thread_catalog_sync_state` two
    ([section 5](#5-other-stores)).
  - A plain question in Codex mode (18:40:09Z to 18:40:31Z) added a row
    with `source_kind` `vscode`, `thread_source` `user` and the thread's
    `cwd`: the catalog lists the app's Codex threads too.
  - A reply, in ChatGPT mode, to one of the listed conversations (about
    22:02Z to 22:15Z) wrote nothing to the Codex stores: no rollout, no
    new row, and the three `chatgpt` rows kept their 2026-10-15
    `source_updated_at`. In that window `logs_2.sqlite`, the app server's
    log, held only `account/read`, `getAuthStatus`, `config/read` and
    `configRequirements/read` requests: the conversation never passed
    through the local app server (Codex's local service that owns the
    threads). The Chromium profile had no chatgpt.com origin directory.
  - Deleting the Codex-mode plain question with the app's own command
    (2026-10-19 00:36:02Z) removed that thread's `vscode` row with its
    rollout; the `chatgpt` rows stayed.
  - The user reported that the app's Codex-mode threads did not appear
    in the Codex area of chatgpt.com.
  - The sh collector 1.14.0, run live as the user (2026-10-19 00:43:01Z
    to 00:43:21Z), attributed `sqlite/codex-dev.db` to `codex-cli`.
- macOS, ChatGPT 26.1007.71326, 2026-10-15: the same VM, the earlier
  build with Codex `0.162.0-alpha.17.2`, no listing between tasks. A
  plain chat and an image generation left no transcript;
  `local_thread_catalog` held three `vscode` rows and three `chatgpt`
  rows, two with `conversation_origin` NULL and one `tpp`
  ([section 1 of `codex-cli.md`](codex-cli.md#1-source-and-evidence)).
- Windows, ChatGPT 26.1007.9446.0, 2026-10-15: the author's Windows 11
  ARM64 lab VM, the Microsoft Store package `OpenAI.Codex`. A plain chat
  and an image generation in the app left no local transcript; the chat
  left a `chatgpt` row with only its title set, at the same relative
  path `.codex/sqlite/codex-dev.db`, with a WAL sidecar (write-ahead
  log, where SQLite keeps recent writes until a checkpoint). By the end
  of the round the table held five rows: three `vscode` and two
  `chatgpt`, one with `conversation_origin` empty and one `tpp`
  ([section 5 of `codex-cli.md`](codex-cli.md#5-other-stores)).
- Not observed: a conversation deleted or renamed on chatgpt.com, a
  sign-out, and a second sign-in, so whether a later sign-in removes or
  updates a row is not determined; `conversation_origin` values other
  than empty, NULL and `tpp`; any `chatgpt_async_status` value; a
  `chatgpt` row with `cwd`, `model_provider` or `project_id` set. Linux
  has no ChatGPT desktop app.

### Source reviews

None.

## 2. Transcript stores

Relative to the home.

| Path | Content | Parse |
| --- | --- | --- |
| `.codex/sqlite/codex-dev.db` (+`-wal`, `-shm`) | the app's thread catalog and automation store; the `chatgpt` rows of `local_thread_catalog` are the account's conversations | yes, the `chatgpt` rows, by the `chatgpt-desktop` parser (the catalog attributes the file to `codex-cli`) |
| `.codex/sessions/**/rollout-*.jsonl` | the app's Codex-mode threads | yes, by the `codex-cli` parser |
| `.codex/.codex-global-state.json` | the app's UI and account state; on Windows it held a thread binding and a resume token for the ChatGPT chat ([section 2 of `collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md#2-per-user-storage)); on macOS no resume-token key had appeared by the end of sign-in | by the `codex-cli` parser for its Codex keys; not by this parser |
| the Chromium profile (`Library/Application Support/Codex` on macOS, the `OpenAI.Codex_*` package on Windows) | the web view's own storage, cookies and logs | no: no conversation text was found there on either install |

There is no ChatGPT-mode transcript on disk on any install checked.

### What survives a delete

The `chatgpt` row is a sign-in snapshot that outlived a reply to its
conversation from inside the app with its times unchanged. A delete of a
Codex-mode thread removes only that thread's `vscode` row. What a
deletion of the conversation on chatgpt.com, or a sign-out, does to the
row was not exercised.

## 3. Record schema

`local_thread_catalog`, column names from `pragma table_info` on the
macOS install (build 26.1013.40934, 2026-10-18), in table order:
`host_id`, `thread_id`, `display_title`, `source_created_at`,
`source_updated_at`, `cwd`, `source_kind`, `source_detail`,
`model_provider`, `git_branch`, `observation_sequence`,
`missing_candidate`, `thread_source`, `source_recency_at`,
`pending_observed_title`, `project_id`, `conversation_origin`,
`trial_conversation_type`, `chatgpt_async_status`. The declared column
types were not recorded.

Values on the `chatgpt` rows (macOS, 2026-10-18):

| Column | Value |
| --- | --- |
| `host_id` | `chatgpt:<workspace uuid>:user-<account id>` (74 characters): the ChatGPT workspace and account; the `vscode` rows have `local` |
| `thread_id` | a UUID, the chatgpt.com conversation id |
| `display_title` | the conversation's title, set on every row seen |
| `source_created_at`, `source_updated_at`, `source_recency_at` | REAL epoch seconds with a fraction (not milliseconds) |
| `source_kind` | `chatgpt` (`vscode` for a Codex thread) |
| `conversation_origin` | empty or `tpp`; NULL on the 2026-10-15 macOS rows. What `tpp` stands for is not determined; the same token is in the app's `.codex-tpp-local-executor-installation-id` file name on both platforms and in the macOS app log's `[tpp-local-executor]` component ([section 2 of `collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md#2-per-user-storage)) |
| `missing_candidate` | 0 |
| `thread_source`, `model_provider`, `cwd`, `git_branch`, `project_id`, `trial_conversation_type`, `chatgpt_async_status` | NULL |
| `source_detail`, `observation_sequence`, `pending_observed_title` | not recorded |

## 4. Joins and timestamps

`thread_id` is the conversation's id on chatgpt.com and joins nothing
else on disk: no rollout, prompt history or log row carries it, because
the conversation never reaches the local app server
([section 1](#1-source-and-evidence)). It is the id to name in a request to OpenAI
for the conversation's content. `host_id` names the ChatGPT account the
list was taken from, as `local_thread_catalog_hosts` does.

The times are the server's times for the conversation as of the
snapshot: `source_created_at` when it was created and
`source_updated_at` when it last changed, both as of sign-in. A later
reply from inside the app did not move them ([section 1](#1-source-and-evidence)),
so `source_updated_at` is a lower bound on the conversation's last use,
not its last use. When the app wrote the row is the sign-in time, which
the row does not record.

## 5. Other stores

`codex-dev.db` (macOS, build 26.1013.40934, 2026-10-18; table and
column names only):

| Table | Columns | Rows seen |
| --- | --- | --- |
| `local_thread_catalog` | [section 3](#3-record-schema) | 3 `chatgpt` at sign-in, plus one `vscode` per Codex thread |
| `local_thread_catalog_hosts` | `host_id`, `host_kind` | 2: `local` / `local` and the account's `chatgpt:<uuid>:user-<id>` / `chatgpt` |
| `local_thread_catalog_sync_state` | `host_id`, `watermark_updated_at`, `initial_build_complete`, `observation_sequence`, `last_full_reconciled_at` | 2 (`initial_build_complete` 1; `observation_sequence` 5 and 1) |
| `local_thread_catalog_metadata` | `id`, `catalog_revision` | 1 |
| `local_thread_catalog_scan_checkpoints`, `local_thread_catalog_scan_entries` | not recorded | 0 |
| `automations`, `automation_runs`, `inbox_items` | the scheduled-task store ([section 5 of `codex-cli.md`](codex-cli.md#5-other-stores)) | `automations` 1 after a task was created; the `codex-cli` parser reads the task from `automation.toml` instead |
| `live_visualization_suggestions`, `local_app_server_feature_enablement`, `thread_timeline_ledger` | not read | 0, 1 and 0 |
| `codex_schema_migrations` | `app_version`, `build_flavor`, `build_commit` and more | 33 |

Only `local_thread_catalog` is read by the parser.

## 6. Format versions

`codex_schema_migrations` (33 rows on the 26.1013.40934 install)
carries the app version in `app_version`, with `build_flavor` `prod`
on the Windows install. The same table and the
same `chatgpt` row shape were seen on Windows build 26.1007.9446.0 and
macOS builds 26.1007.71326 and 26.1013.40934; the
`local_thread_catalog_metadata`, `_scan_checkpoints`, `_scan_entries`,
`_sync_state` and `thread_timeline_ledger` tables were recorded only on
the 26.1013.40934 install. The parser reads every column as possibly
absent or NULL, so an older table without a column still parses.

## 7. Secrets

`host_id` carries the ChatGPT workspace id and the account id, and
`display_title` the conversation's title, which is user content. No
token is stored in the table. The app's credentials are in
`~/.codex/auth.json`, flagged `secret: true` by the collector; see
[section 3 of `collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md#3-credentials).

## 8. Parser plan

`wants()` by `artifact.rel == ".codex/sqlite/codex-dev.db"`; the
analyzer offers the file, which the catalog attributes to `codex-cli`,
to this parser through `reads_agents = ("codex-cli",)`, the routing
Cody and Twinny use for an editor's `state.vscdb`. The `codex-cli`
parser does not want the file. The database is opened through
`sqlite_util.py`, which reads the WAL sidecar from a scratch copy. Rows
come only from `local_thread_catalog` rows whose `source_kind` is
`chatgpt`, in rowid order; the `vscode` rows are the Codex threads the
rollouts already give.

Per `chatgpt` row, three `system` rows, each with `session_id` the
`thread_id`, `project_path`, `model` and `git_branch` empty,
`source_line` 0, `source_file` the database, and `timestamp_utc` the
row's `source_updated_at` with milliseconds (its `source_created_at`
when that is NULL, none when both are). `-` stands for a NULL or empty
value:

1. `account conversation: <display_title> origin=<conversation_origin>
   created=<source_created_at, UTC> updated=<source_updated_at, UTC>
   host=<host_id> (from .codex/sqlite/codex-dev.db local_thread_catalog)`
2. `session origin: remote chatgpt.com conversation <thread_id> (listed
   at sign-in; its transcript is server-side)`
3. `session synced: chatgpt.com holds conversation <thread_id>, no local
   transcript`

### Permission state

None recorded for a ChatGPT-mode conversation; the app's Codex-mode
approvals are in the rollouts and `logs_2.sqlite`, read by the
`codex-cli` parser.

### Model

None recorded; `model_provider` is NULL on every `chatgpt` row.

### Past use and secondary sources

None read beyond the primary store. The table is the only local record
of these conversations; the Windows global state's resume token for the
ChatGPT chat ([section 2](#2-transcript-stores)) is not read by this
parser. No secondary source.

### Sync, relay and origin

The rows are themselves the sync marker, copied one way, account to app,
at sign-in; each gets the `session synced:` row. The app's Codex-mode
threads were not uploaded to the account on the macOS install
([section 1](#1-source-and-evidence)), and nothing in this table marks
one as uploaded.

The parser sets `records_origin` and `records_sync`, so `sessions.jsonl`
reads `origin` `remote` and `synced` `yes` for these sessions, and
`relayed` `""`. Their `user_turns`, `assistant_turns` and `tool_calls`
are 0, since the text is not on disk. Relay: none.

### Scratch directories

Not stated.

### Deletion

Not stated; what a delete leaves of the row is in
[What survives a delete](#what-survives-a-delete).

### Bad lines

A file that is not SQLite is one `parser: not a SQLite database` row, a
SQLite error one `parser: SQLite error: <message>` row, and a database
without the table one `parser: no local_thread_catalog table` row.

### Fixtures

Not stated.
