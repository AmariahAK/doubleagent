# GitHub Copilot Desktop store schema

Catalog agent: `copilot-desktop`. GitHub Copilot Desktop is GitHub's
closed-source desktop app (dpkg package `github`), a Tauri app: Tauri is a
desktop framework that draws the user interface in the operating
system's web engine (WebKitGTK, the GTK port of the WebKit browser
engine, on Linux) and runs the backend as a native Rust program. The app
runs its sessions through a bundled Copilot CLI, whose event logs land in
`~/.copilot/session-state/` and are read by the `copilot-cli` parser
([`copilot-cli.md`](copilot-cli.md)); this document covers the app's own
SQLite store, `~/.copilot/data.db`, which records the accounts,
repositories, worktrees, workspaces, sessions, activity and schedules
around those logs. Paths, credentials and exclusions are in
[`collectors/research/copilot-desktop.md`](../../collectors/research/copilot-desktop.md).
[Issue 147](https://github.com/seanthegeek/doubleagent/issues/147) tracks
the app.

## 1. Evidence

Closed source, so there are no commit links. Each claim names its
evidence level:

- **Shipped binary**: dpkg package `github` 1.1.29 (arm64 `.deb`),
  `/usr/bin/github`, a 1,388,701,168-byte ELF aarch64 executable with
  debug information (BuildID
  `337d94e3f5709ec9c61ece90f86958a5d141a9e3`, sha256
  `9f6259e76190ef3fd89561e594a0a6fad0967bddc2faf3b119c8bafa3097ec27`), read
  with `strings` and `grep`, never run by the research. Citations are
  `github 1.1.29 linux-arm64 /usr/bin/github` with a literal snippet,
  shortened after this paragraph to "binary" and the snippet; no offsets
  were recorded. The package also ships the SDK's TypeScript declarations
  (SDK, software development kit: GitHub's library that embeds and drives
  the Copilot CLI) under `/usr/lib/GitHub Copilot/copilot-sdk/`, cited as
  "SDK declarations" with the file and the declaration;
  `cliVersion.d.ts` names the CLI it drives,
  `COPILOT_CLI_VERSION = "1.0.95-3"`.
- **Docs**: none fetched.
- **Observed (Linux)**: GitHub Copilot Desktop 1.1.29, installed at 21:59Z
  on 2026-10-16 on an Ubuntu 26.04.1 arm64 Parallels VM (home
  `/home/sean`) that already held the Copilot CLI 1.0.98 round's
  `~/.copilot` ([section 1 of `copilot-cli.md`](copilot-cli.md#1-evidence)),
  read for table names, column definitions, row counts, key names, types
  and enum values only, never values. Exercised: app start at
  22:00:30Z, sign-in by device-code flow (a sign-in in which the app shows
  a short code that the user enters on github.com in a browser), one
  general chat (session `5d404e14…`, created 22:01:27Z, one prompt, no
  tool call, titled by the user), then the GitHub repository
  `seanthegeek/doubleagent` added (cloned and checked out into a git
  worktree, a second working directory of the same repository on its own
  branch, at 22:03Z) and one project session (`79255eab…`, created
  22:03:11Z, four prompts, tools `bash` 2 and `create` 1; the `create`
  call wrote a file outside the worktree, recorded in the CLI's
  `session-store.db` `session_files`). Every action ran before the first
  listing, so no per-action listing diff exists; the times above are the
  mapping. The existing `copilot-cli` parser read both session logs (86
  rows, no `parser:` row) but wrote `permission mode: - -> -` for the
  permission change and the hook events as `hook.start: {...}` with the
  whole payload ([section 3](#3-record-schema)). Not exercised: a
  scheduled task, a session automation, a removed project, a denied tool
  call, a model switch, a fork, a side chat, a remote session (a deleted
  session is the next bullet).
- **Observed (Linux), deletion**: the same VM and app version, at 02:05Z
  on 2026-10-17 (22:05 on 2026-10-16 in the VM's local time; the app log
  stamps `delete_workspace` 02:05:17Z and `delete_session` 02:05:31Z).
  The user restarted the app and deleted both sessions above
  with the app's own delete action (app log operations `delete_session`
  and `delete_workspace`; the app sends the bundled CLI
  `sessions.delete`), then took a listing diff, names and counts only.
  Both `session-state/<uuid>/` directories, the chat directory, the
  worktree with its branch, the general chat's `data.db` `sessions` row
  and every `workspaces`, `worktrees`, `workspace_session_aliases` and
  `workspace_checkout_bindings` row were removed;
  `session_deletion_intents` stayed empty, 0 rows before and after. What
  survived is in [What a deleted session leaves](#what-a-deleted-session-leaves).
  The analyzer over a fresh collection listed both deleted sessions in
  `sessions.jsonl` and reconstructed them from the Copilot CLI store's
  `turns` (kept as secondary rows with no primary left) and from
  `data.db` (the checkpoint, activity and session rows), with no
  `parser:` row; it also listed the app's own directories as projects
  ([issue 149](https://github.com/seanthegeek/doubleagent/issues/149)).
  Two more sessions existed by then, `83277a7e…` and `4c088c7e…`
  (`client_name` `github/autopilot`, `user_named` false, no
  `events.jsonl`, `cwd` under `.copilot/`), and the app created an empty
  general chat, `4e347d3e…`, at the restart; none of the three was
  exercised.

macOS and Windows were not observed.

## 2. Transcript files

Relative to the home.

| Path | Content | Parse |
| --- | --- | --- |
| `.copilot/data.db` (+`-wal`, `-shm`) | the app's store: accounts, settings, projects, worktrees, workspaces, sessions, activity, checkpoints, schedules | yes, primary, by the `copilot-desktop` parser |
| `.copilot/repos/<name>/.git/refs/copilot/checkpoints/<session id>/<seq>/<event id>` | one loose ref per session checkpoint (a loose ref is a ref kept as its own file under `.git/refs/`, holding a commit hash, rather than a line of `.git/packed-refs`): `<seq>` 20 digits, zero-padded, `<event id>` an event id of the session's `events.jsonl`; outlives the session ([What a deleted session leaves](#what-a-deleted-session-leaves)) | yes, by the `copilot-desktop` parser, one `checkpoint ref` row each |
| `.copilot/repos/<name>/.git/logs/` | the clone's reflog (git's log of each change to where a ref points) | no: on the install it held only the clone, `remote set-head`, the pre-created worktree's checkout and reset entries, and no checkpoint ref |
| `.copilot/session-state/<uuid>/events.jsonl`, `workspace.yaml` | each app session's event log and metadata, Copilot CLI's format | yes, by the `copilot-cli` parser ([section 2 of `copilot-cli.md`](copilot-cli.md#2-transcript-files)) |
| `.copilot/session-state/<uuid>/session.db` | per-session workflow and factory store ([section 5](#5-sqlite-and-other-stores)) | no; its tables were empty but two |
| `.copilot/repo-metadata-cache.db` (+`-wal`, `-shm`) | GitHub metadata cache | no; empty but one lifecycle row |
| `.copilot/logs/github-app.<pid>.log` | the Tauri backend's tracing log | no: it records the app's own start-up, sign-in and scheduler steps, while the sessions, prompts and tool calls it would date are in the event logs and `data.db` |
| `.local/share/com.github.githubapp/localstorage/tauri_localhost_0.localstorage` | the web view's local storage, SQLite `ItemTable(key, value BLOB)` | no: its values are UI state (tabs, caches, theme); the one user text, the unsent composer draft `home-composer-draft:main`, was never sent to the agent and has no time of its own; reading it is left for a later parser change |
| `.github-copilot-cli/logs/foundry.core<yyyymmdd>.log` | Foundry Local log (Foundry Local: Microsoft's runtime for local models) | no: model catalog fetches and a device id, no use of the agent |

Desktop sessions in the event logs are told from CLI sessions by
`workspace.yaml` `client_name` `github/autopilot` (the CLI writes
`github/cli`); the `copilot-cli` parser writes it at the end of the
`session metadata:` row as ` client=<client_name>`.

## 3. Record schema

Every `created_at` and `updated_at` default is
`strftime('%Y-%m-%dT%H:%M:%fZ','now')`, ISO 8601 UTC with milliseconds
(real install (Linux)). `data.db` has 110 tables; the ones a parser
reads, with the row counts observed on the install, are below. Column
lists are as the survey printed the `CREATE TABLE` statement; where it
cut the statement, the list ends in "...".

| Table | Columns the parser reads (others named in the definition) | Observed |
| --- | --- | --- |
| `accounts` | `id`, `login`, `name`, `is_default`, `host` (default `github.com`), `token_updated_at`, `created_at`, `updated_at`, `access_token`, `kind` (default `github`), `settings_json`, `parent_account_id` | 1 row: `kind` `github`, `host` `github.com`, `is_default` 1, `access_token` NULL |
| `settings` | `id` (always 1), `last_active_workspace_id`, `storage_location`, `instructions`, `github_access_token`, `github_token_type`, `github_scope`, `github_token_updated_at`; no timestamp column | 1 row: `storage_location` the repos root under `~/.copilot`, `instructions` empty, token columns NULL |
| `model_providers` | `id`, `name`, `created_at`, `updated_at`, `type` (default `openai`), `settings_json`, `account_id` | 1 row: `type` `github_copilot`, `name` `GitHub Copilot` |
| `projects` | `id`, `name`, `container_kind` (`folder`, `repository` or `collection`), `main_repo_path` (unique), `default_branch`, `github_owner`, `github_repo`, `github_account_id`, `created_at`, `last_opened_at`; also `setup_script`, `run_script`, `instructions`, `auto_approve`, `trusted_config_sha256`, `trusted_config_accepted_at`, `branch_prefix`, `sandbox_enabled`, the `reusable_worktrees_*` settings and more | 1 row: `container_kind` `repository`, `main_repo_path` under `~/.copilot/repos/`, owner and repository set, `default_branch` `main` |
| `worktrees` | `id`, `project_id`, `path`, `branch`, `base_branch`, `created_at` | 1 row: `path` under `~/.copilot/repos/copilot-worktrees/`, `base_branch` `main` |
| `workspaces` | `id`, `project_id`, `worktree_id`, `workspace_type` (`worktree`, `branch`, `folder` or `cloud`), `branch`, `name`, `created_at`, `source_pr_repo_full_name`, `source_pr_number`, `created_pr_repo_full_name`, `created_pr_number`; also `port`, the other `source_pr_*`, `source_issue_*` and `created_pr_*` columns, `last_diff_*`, token totals, `agent_merge_*`, `creator_session_id`, `archived_at`, `session_id` and more | 1 row: `workspace_type` `worktree`, `port` 3000 |
| `workspace_session_aliases` | `session_id` (primary key), `workspace_id`, `created_at` | 1 row: the project session to its workspace |
| `workspace_checkout_bindings` | `workspace_id`, `repo_path`, `repo_full_name`, `display_name`, `checkout_kind` (`in_place` or `worktree`), `checkout_path`, `worktree_id` | 1 row: `checkout_kind` `worktree`, `repo_path` the clone, `checkout_path` the worktree (not read by the parser; the worktree row carries the same path) |
| `sessions` | `id`, `title`, `session_type` (default `workspace`), `mode`, `model`, `reasoning_effort`, `created_at`, `remote_control_enabled`, `auto_approve` (default 1), `forked_from_session_id`, `archived_at`, `permission_mode`; also `is_running`, `was_interrupted`, `interruption_reason`, `updated_at`, `enabled_experiments_json`, token and context totals, `remote_session_mode`, `agent`, `provider_id`, `execution_location`, `context_tier`, `title_source`, `sandbox_enabled`, `agent_scope` and more | 2 rows: `session_type` `general_chat` and `project`, `mode` NULL, `model` `claude-sonnet-5.5`, `auto_approve` 1, `remote_control_enabled` 0; `id` equals the `session-state` directory name |
| `activity_items` | `id`, `workspace_id`, `session_id`, `activity_type`, `preview`, `is_read`, `created_at`, `updated_at`, `metadata_json` | 6 rows: `agent_idle` ×5 with a `session_id` and a `preview` of 63 to 300 characters (the start of the reply), `workspace_ready` ×1 (31 characters, no session) |
| `session_checkpoints` | `session_id`, `event_id`, `commit_sha`, `created_at` | 4 rows for the project session, a 40-hex `commit_sha` each; the worktree's git log showed no new commit, so these are snapshot commits kept outside the branch |
| `my_copilot_scheduled_tasks` | `id`, `revision`, `title`, `prompt`, `enabled`, `execution_mode`, `background_agent_type` (default `general-purpose`), `created_at`, `updated_at`, `archived_at` | 0 rows |
| `my_copilot_scheduled_task_triggers` | `id`, `task_id`, `kind`, `enabled`, `config_version`, `config_json`, `state_version`, `state_json`, `next_run_at`, `last_fired_at`, `created_at`, `updated_at`, `archived_at` | 0 rows |
| `my_copilot_scheduled_task_invocations` | `id`, `task_id`, `trigger_id`, `occurrence_key`, `source`, `scheduled_for`, `task_revision`, `task_title`, `prompt_snapshot`, `trigger_snapshot_json`, `execution_mode`, `parent_session_id`, `runtime_agent_id`, `status`, `claimed_at`, `dispatched_at`, `completed_at`, ... (the survey cut the definition there) | 0 rows |
| `session_automations` | `session_id`, `prompt`, `interval` (`once`, `minutes`, `daily` or `weekly`), `every_minutes`, `schedule_hour`, `schedule_day`, `last_run_at`, `next_run_at`, `updated_at`, `name`, `owner_session_id`, `paused_at`; no `created_at` | 0 rows |
| `session_deletion_intents` | `session_id`, `created_at` | 0 rows; the binary inserts a row (binary: `INSERT OR IGNORE INTO session_deletion_intents (session_id) VALUES (?1)`) and leaves sessions that have one out of its queries (binary: `AND NOT EXISTS (SELECT 1 FROM session_deletion_intents`) |

Other tables observed, not read: `session_context_usage` (8 rows,
`ts_ms`, `current_tokens`, `token_limit` 200000), `app_state` (34
key-value rows; keys include `activeWorkspaceId`,
`copilot-available-models-v2`, `permission-mode-default-on`,
`session-groups`, `telemetry.machine_id`, `crash-reporting.tracking-id`,
`workspace-mru`), `schema_migration_reversals`
([section 6](#6-format-versions)), `session_sources` (files and folders
attached to a session, with `onedrive` and `gdrive` providers),
`session_side_chats`, `chat_parent_links`, `remote_environments`, all
empty; and, by name only and empty unless said: `agent_memory_*`,
`agent_merge_*`, `agents`, `builtin_agents`, `canvas_catalog_cache` (1
row), `coordinator_*`, `factory_*`, `inline_review_*`,
`project_checkouts` (1 row), `project_host_trust` (1 row, a 64-hex
`trusted_config_sha256`), `project_trust_revisions` (1 row),
`reusable_worktree_pool` (1 row), `review_thread_*`, `workflow_runs`,
`workflows`, `workspace_archive_*`, `workspace_diff_*`, `workspace_file_*`,
`workspace_pull_request_links` and the rest of the 110.

### The session logs the app's CLI writes

These are Copilot CLI event logs ([section 3 of
`copilot-cli.md`](copilot-cli.md#3-record-schema)), with these
differences on the install (real install (Linux)):

- `session.start` `producer` `copilot-agent`, `copilotVersion` `1.0.95-3`;
  `context` holds `cwd` only for the general chat, and `branch`, `cwd`,
  `gitRoot`, `headCommit`, `hostType` (`github`), `repository` and
  `repositoryHost` (`github.com`) for the project session.
- `session.model_change`, one per session: `source` `startup`,
  `previousModel` null, `newModel` `claude-sonnet-5.5`, and the reasoning
  and tier keys all null.
- `session.permissions_changed`, one per session, with the keys
  `previousAllowAllPermissions` false, `allowAllPermissions` true,
  `previousAllowAllPermissionMode` `off` and `allowAllPermissionMode`
  `on`, not the schema's `previousMode` and `mode`. The SDK declarations
  shipped with the app name only the schema keys (SDK declarations,
  `generated/session-events.d.ts`: `export interface PermissionsChangedData`
  with `assistedApprovalModel?`, `mode?`, `previousMode?`), and the 1.0.98
  schema does not name the `allowAll*` keys either.
- `user.message` keys `content`, `delivery` (`idle`), `interactionId`,
  `messageId`, `parentAgentTaskId`, `supportedNativeDocumentMimeTypes`,
  `transformedContent`, `turnId`; no `source`, no `agentMode`.
- `tool.execution_start` keys `arguments`, `model`, `shellToolInfo` (new,
  on `bash`), `toolCallId`, `toolName`, `toolTitle`, `turnId`.
- `hook.start` and `hook.end` pairs, 5 in the general chat and 23 in the
  project session (SDK declarations: `HookStartData` `hookInvocationId`,
  `hookType`, `input?`, `parentToolCallId?`; `HookEndData` `error?`,
  `hookInvocationId`, `hookType`, `output?`, `parentToolCallId?`,
  `success`). `hookType` values and their `input` keys: `sessionStart`
  (`cwd`, `initialPrompt`, `sessionId`, `source`, `timestamp`),
  `userPromptSubmitted` (`cwd`, `prompt`, `sessionId`, `timestamp`),
  `userPromptTransformed` (the same plus `transformedPrompt`),
  `preToolUse` and `postToolUse` (keys not recorded; a `postToolUse`
  payload reached 4 KB), `agentStop` (`cwd`, `sessionId`, `stopReason`,
  `stop_hook_active`, `timestamp`, `transcriptPath`), `sessionEnd` (`cwd`,
  `reason`, `sessionId`, `timestamp`). `hook.end` carried
  `hookInvocationId`, `hookType`, `success` and, for all but the tool
  hooks, `output` `{}`.
- No `permission.requested` or `permission.completed` (the app approves
  automatically), no `session.shutdown`, no `session.info`.

## 4. Joins and timestamps

- Session: `sessions.id` = the `session-state/<uuid>/` directory name =
  `session.start` `sessionId` = `workspace_session_aliases.session_id` =
  `activity_items.session_id` = `session_checkpoints.session_id`
  (real install (Linux)). The `copilot-desktop` and `copilot-cli` rows of
  one session therefore share `session_id`.
- Project: `workspace_session_aliases.workspace_id` → `workspaces.id`;
  `workspaces.project_id` → `projects.id`, whose `main_repo_path` is the
  `project_path` of the session's rows; `workspaces.worktree_id` →
  `worktrees.id`, and `worktrees.project_id` → `projects.id`. A general
  chat has no alias row and no project. The `copilot-cli` rows of a
  project session carry the worktree path from `workspace.yaml` `cwd`,
  not `main_repo_path`, so the two parsers' `project_path` differ for the
  same session; the join is `session_id`.
- Checkpoint: `session_checkpoints.event_id` names an event of the
  session's log (format not checked against the log's `id`s). Each
  checkpoint ref's path carries the session id and an event id that is
  an `events.jsonl` event id of the session, and its commit is dated at
  the matching `session_checkpoints` time (real install (Linux)). On the
  install each ref's commit hash equalled the row's `commit_sha` and its
  event id the row's `event_id`, for all four checkpoints, so the ref,
  the row and the log event are one record under three names.
- Fork: `sessions.forked_from_session_id` → `sessions.id` (not observed).
- Scheduled task: `my_copilot_scheduled_task_triggers.task_id` and
  `my_copilot_scheduled_task_invocations.task_id` → `my_copilot_scheduled_tasks.id`;
  `invocations.trigger_id` → `triggers.id`; `invocations.parent_session_id`
  → `sessions.id` (schema; not observed).
- Times: every `*_at` column is ISO 8601 UTC with milliseconds and `Z`;
  `session_context_usage.ts_ms` is epoch milliseconds. `settings` has no
  time column, so its row is timestamped by the file's modification time.

## 5. SQLite and other stores

Three SQLite files belong to the app (real install (Linux)):

- `~/.copilot/data.db`, WAL mode (write-ahead log: new pages go to the
  `-wal` file until a checkpoint copies them into the main file; binary:
  `PRAGMA journal_mode=WAL;PRAGMA foreign_keys=ON;`) with
  `data.db.open-lock` and `data.db.startup-lock` beside it. On the install
  the WAL (1.67 MB) was larger than the main file (1.3 MB), so the parser
  must read the evidence copy with its sidecars, through
  `doubleagent/sqlite_util.py`. Schema in [section 3](#3-record-schema).
- `~/.copilot/repo-metadata-cache.db` (+`-wal`, `-shm`; binary:
  `repo-metadata-cache.db`): `github_metadata_account_lifecycle` (1 row;
  its schema comment says the credential column is "Hex SHA-256 of the
  credential identity in use ... never a token"), `github_metadata_items`,
  `_lists`, `_list_pages`, `_org_items`, `_org_lists`, `_org_lifecycle`,
  `_repo_lifecycle`, `_repo_backoffs`, `_org_backoffs`,
  `_cleanup_obligations`, all empty. Not parsed.
- `~/.local/share/com.github.githubapp/localstorage/tauri_localhost_0.localstorage`
  (+`-wal`, `-shm`): WebKit's local storage for the app's page, one table
  `ItemTable(key, value BLOB)`, keys `copilot.first-paint-theme.v1`,
  `backend-instance-id`, `detail-cache`, `agent-tabs`,
  `chat-agent-tabs-source-v1`, `chat-agent-tabs-partition-v1`,
  `home-composer-draft:main` (192 bytes), `general-chat-tabs`,
  `inbox-cache` (2.5 KB), `side-chat-tabs`, `workspace-tabs`. Not parsed
  ([section 2](#2-transcript-files)).

### What a deleted session leaves

Real install (Linux), the deletion round of [section 1](#1-evidence):
the app's delete removed each session's `session-state/<uuid>/` directory
entire (`events.jsonl`, `workspace.yaml`, `session.db`, `checkpoints/`,
`rewind-file-snapshots/`, `files/`, `research/`), so the `copilot-cli`
parser has no primary store left for either session. These survived:

- `session-store.db`, the Copilot CLI's cross-session store, which the
  CLI calls its chronicle, read by the `copilot-cli` parser as a
  secondary source ([section 5 of `copilot-cli.md`](copilot-cli.md#5-sqlite-and-other-stores)):
  the `sessions` rows of both sessions (`summary` the session name, `cwd`
  under `.copilot/`, the project session with `repository` and `branch`),
  5 `turns` rows holding every prompt and final reply in full (the general
  chat's one turn written at 22:12:15Z, ten minutes after its reply; the
  project session's four at 22:04:43Z, 22:06:30Z, 22:06:50Z and
  22:17:00Z), 1 `session_files` row (the `create` of the file the agent
  wrote), 8 `assistant_usage_events` rows and 5 `search_index` rows. The
  CLI's research prediction that the bundle never deletes these rows held.
- `data.db`: the project session's `sessions` row (title, `session_type`
  `project`, `archived_at` null, `is_running` 0), one `activity_items`
  row for the general chat (`agent_idle`, a 300-character preview of the
  reply, `session_id` set although its session row is gone), all 4
  `session_checkpoints` rows (commit hashes and times), 7
  `session_context_usage` rows, the `projects` row and the
  `reusable_worktree_pool` row (state `available`, the worktree the pool
  pre-creates). Removed: the general chat's `sessions` row and every
  `workspaces`, `worktrees`, `workspace_session_aliases` and
  `workspace_checkout_bindings` row, so the project session's rows lose
  their `project_path` join ([section 4](#4-joins-and-timestamps)).
- `data.db-wal`: the deleted rows' pages. The two session ids occur 63
  and 105 times in the WAL and never in `data.db`, whose main file had
  not changed since the app first started.
- The clone's checkpoint refs: four files
  `.git/refs/copilot/checkpoints/79255eab…/0000000000000000000N/<event id>`
  (N 1 to 4), each holding a commit hash. Each commit has author and
  committer `Copilot`, subject `copilot checkpoint: <session id> @ <event
  id>`, an empty body and one parent, and is dated at the
  `session_checkpoints` times. Their trees were identical to `main`,
  because the session's only write went outside the worktree; in a
  session that edits files they are per-turn snapshots of the worktree.
  The refs appear in no reflog. The worktree that remains is the pool's
  `copilot-prewarm-<adjective>-<noun>` on a detached HEAD (a checkout of
  a commit, here `main`'s, rather than of a branch).
- `logs/github-app.<pid>.log` (160 KB): `deleted local branch ref on hard
  delete workspace_id=<uuid> branch=<branch> repo=<path>`, `permanently
  deleted workspace workspace_id=<uuid>`, `archived workspace
  workspace_id=<uuid>`, `not parking worktree; removing it instead
  project_id=<uuid> error=reusable worktree pool is full for project
  <uuid>`, `session not found in memory during delete (already evicted)
  session_id=<uuid>` twice and `terminated agent processes owned by
  ending sessions scope="session_end" ...`, with 22 and 129 mentions of
  the two ids; not parsed ([section 2](#2-transcript-files)).
- The CLI's `logs/process-<epoch ms>-<pid>.log`, untouched, with
  `Cleaning up session <uuid>: Session deleted via sessions.delete` once
  per deletion (three lines in all, one from an earlier delete); the two
  0-byte `.session-operation-locks/<id>.lock` files; the file the agent
  wrote.
- `localstorage`: the `side-chat-tabs` value still keys its
  `openSessionIdsByWorkspace` object by both deleted ids (empty lists)
  and the pending-session id; `home-composer-draft:main` is `{state:
  {promptText, selectedProjectId, projectExplicitlySelected}, version}`,
  empty here. The ids occur nowhere else in it, WAL included.

Also present: each session directory's `session.db` (192 KB), written by
the bundled CLI, with the tables `factory_agents`,
`factory_credit_charges`, `factory_journal`, `factory_phases`,
`factory_progress`, `factory_runs`, `workflow_agents`,
`workflow_credit_charges`, `workflow_journal`, `workflow_phases`,
`workflow_progress`, `workflow_runs`, `workflow_store_schema` (1 row) and
`github_metadata_*` (the account lifecycle 1 row, the rest empty); and
WebKit's `hsts-storage.sqlite` in the Tauri data directory. Neither is
parsed.

## 6. Format versions

`schema_migration_reversals` records the reversible migrations: 18 rows,
the highest `version` 187, `recorded_by_app_version` `1.1.29`
(real install (Linux)). It is the only version marker in `data.db`, so a
parser change for a later app version starts by comparing the highest
`version` and the table definitions with [section 3](#3-record-schema).
The binary carries older migrations (binary:
`ALTER TABLE github_accounts ADD COLUMN access_token TEXT;`), so earlier
builds had other table names; their shapes are not determined. The
bundled CLI was 1.0.95-3 (SDK declarations, `cliVersion.d.ts`), older
than the 1.0.98 the `copilot-cli` research reads, and its logs carry the
differences listed in [section 3](#the-session-logs-the-apps-cli-writes).

## 7. Secrets

- `accounts.access_token` and `settings.github_access_token` (with
  `github_token_type`, `github_scope`) can hold a GitHub token; both were
  NULL on the install, the token being in the GNOME keyring (the GNOME
  desktop's password store). The parser writes only whether each is
  present (`token_present=`, `github_token_present=`), never the value.
- `accounts.login` and `projects.github_owner` name the account;
  `app_state` holds `telemetry.machine_id` and
  `crash-reporting.tracking-id` (not read).
- `activity_items.preview` is the start of an agent reply, and the
  scheduled-task and automation `prompt` columns are prompts the user
  wrote, kept verbatim.
- `run/ws.token` and `run/ws.release.token` (the local WebSocket auth
  tokens) are not read; the collector flags them `secret: true`.

## 8. Parser plan

`wants()` by `artifact.rel`: `^\.copilot/data\.db$`, opened through
`sqlite_util.py`, which reads the WAL sidecar from the evidence copy, and
the checkpoint refs (below). No secondary source. Rows from `data.db`,
each `system`, with `source_file` the database and `source_line` empty,
timestamps converted with `to_utc`:

| Table | Row |
| --- | --- |
| `accounts` | at `created_at`: `account: <login> host=<host> kind=<kind> default=<is_default> token_present=<true if access_token not null>` |
| `settings` | at the file's mtime (say so in the text): `desktop settings: storage_location=<storage_location> instructions=<instructions or -> github_token_present=<bool> github_token_type=<github_token_type or ->` |
| `model_providers` | at `created_at`: `model provider: <name> type=<type>` |
| `projects` | at `created_at`, `project_path` = `main_repo_path`: `project added: <name> kind=<container_kind> path=<main_repo_path> github=<github_owner>/<github_repo> default_branch=<default_branch>` (omit ` github=` when both null) |
| `worktrees` | at `created_at`, `project_path` = the project's `main_repo_path`: `worktree: <path> branch=<branch> base=<base_branch or ->` |
| `workspaces` | at `created_at`, `project_path` as above: `workspace: <name> type=<workspace_type> branch=<branch>` plus ` source_pr=<source_pr_repo_full_name>#<source_pr_number>` and ` created_pr=<created_pr_repo_full_name>#<created_pr_number>` when set |
| `sessions` | at `created_at`, `session_id` = `id`, `model` = `model`, `project_path` via `workspace_session_aliases` -> `workspaces` -> `projects.main_repo_path` (empty for a general chat): `desktop session: <title or -> type=<session_type> model=<model or -> auto_approve=<auto_approve> permission_mode=<permission_mode or -> remote_control=<remote_control_enabled> archived=<true if archived_at>`; and when `forked_from_session_id` is set a second row `forked from session <id>` |
| `activity_items` | at `created_at`, `session_id` when set: `activity <activity_type>: <preview>` |
| `session_checkpoints` | at `created_at`, `session_id`: `checkpoint commit <commit_sha>` |
| `my_copilot_scheduled_tasks` | at `created_at`: `scheduled task: <title> enabled=<enabled> mode=<execution_mode> agent=<background_agent_type> prompt: <prompt>` |
| `my_copilot_scheduled_task_triggers` | at `created_at`: `scheduled task trigger: task=<task_id> kind=<kind> enabled=<enabled> next_run_at=<next_run_at or -> config: <config_json>` |
| `my_copilot_scheduled_task_invocations` | at `claimed_at`, `session_id` = `parent_session_id` when set: `scheduled task run: <task_title> status=<status> source=<source> scheduled_for=<scheduled_for or -> prompt: <prompt_snapshot>` |
| `session_automations` | at `updated_at`, `session_id`: `session automation: <name or -> interval=<interval> every_minutes=<every_minutes or -> next_run_at=<next_run_at or -> prompt: <prompt>` |
| `session_deletion_intents` | at `created_at`, `session_id`: `session deletion requested` |

Every column is read as possibly NULL. A database that cannot be opened
gives one `parser: <message>` row. Rows follow the table order above,
then `created_at`.

Checkpoint refs: `wants()` also takes
`^\.copilot/repos/[^/]+/\.git/refs/copilot/checkpoints/([0-9a-f-]{36})/(\d+)/([0-9a-f-]{36})$`
and yields one `system` row per ref file:
`checkpoint ref <seq as an integer>: commit <file content, stripped> event <event id> (file mtime)`,
with `session_id` the first group, `timestamp_utc` the file's
modification time (`file_mtime` from `parsers/base.py`), `project_path`
empty and `source_file` the ref file. A ref file that is empty or not a
40-hex hash still yields the row with its content as read, stripped,
nothing repaired. No secondary. These rows are what remains of a
deleted session's checkpoints in the clone
([What a deleted session leaves](#what-a-deleted-session-leaves)).

Permission: the app records no per-call decision in `data.db`; its
standing permission state is `sessions.auto_approve` and
`sessions.permission_mode` (and `projects.auto_approve`, not read), on
the `desktop session:` row. In the session logs it is the
`session.permissions_changed` event with the `allowAll*` keys, which the
`copilot-cli` parser writes as `permission mode: allow-all <previous> ->
<new>`; no `permission.requested` or `permission.completed` was written,
since the app approved every call automatically.

Model: `sessions.model` (and `reasoning_effort`, not read) per session,
on the `desktop session:` row and in its `model` column; the switches are
the logs' `session.model_change` events, which the `copilot-cli` parser
writes as `model:` rows. `data.db` records no per-switch history.

Schedules: `my_copilot_scheduled_tasks`, their triggers and invocations,
and `session_automations` are the evidence of scheduled and recurring
work (binary: "Scheduler starting for workflows, session automations, and
Scheduled tasks"); all four were empty on the install, so their rows are
fixture only.

Past use beyond the primary store: `data.db` is a primary source for the
app's own records and repeats no event of the session logs, so no
`secondary()` file. `activity_items.preview` overlaps the start of an
assistant reply in the log but is shorter text at a different time, so
it stays its own row. `session_deletion_intents` would outlive a session
the app is deleting, but it stayed empty through the observed deletion.
What a deletion leaves is in
[What a deleted session leaves](#what-a-deleted-session-leaves): the
Copilot CLI's `session-store.db` rows (secondary sources of the
`copilot-cli` parser, which then have no primary left and are kept),
the `data.db` rows above that the delete did not remove, and the
checkpoint refs, a primary source of their own. The logs' `hook.*` events, which
the `copilot-cli` parser writes as `hook <hookType> start:` and `hook
<hookType> end:` rows, repeat each prompt (`userPromptSubmitted`
`prompt`) and the transcript path (`agentStop` `transcriptPath`).
