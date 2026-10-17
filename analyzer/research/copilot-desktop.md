# GitHub Copilot Desktop store schema

Catalog agent: `copilot-desktop`. GitHub Copilot Desktop is GitHub's
closed-source desktop app (dpkg package `github` on Linux; on Windows an
NSIS installer, NSIS being the Nullsoft Scriptable Install System, an
installer framework), a Tauri app: Tauri is a desktop framework that
draws the user interface in the operating system's web engine
(WebKitGTK, the GTK port of the WebKit browser engine, on Linux;
WebView2, Microsoft Edge's embeddable Chromium, on Windows) and runs the backend as a native Rust program. The app
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
  `COPILOT_CLI_VERSION = "1.0.95-3"`. The Windows build was read the
  same way: `github.exe` 1.1.30 windows-arm64 (442,207,520 bytes, sha256
  `8e9b4162ee7c0d7c7212c3b34b05c7bd8809af24494ab4560f2fc2d4536288e5`,
  FileVersion 1.1.30), cited as `github 1.1.30 windows-arm64 github.exe`
  with the snippet; the SDK declarations in its install directory's
  `copilot-sdk\` say `COPILOT_CLI_VERSION = "1.0.99-2"`
  (`cliVersion.d.ts`) and `SDK_PROTOCOL_VERSION = 3`
  (`sdkProtocolVersion.d.ts`).
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
- **Observed (Windows)**: GitHub Copilot Desktop 1.1.30 on a Windows 11
  ARM64 Parallels VM (build 10.0.26300.9550, user `sean`, home
  `C:\Users\sean`), 2026-10-17, all times UTC, read for table names,
  column definitions, row counts, key names, types and enum values only,
  never values. The installer `GitHub-Copilot-windows-arm64-setup.exe`
  installs per user into `AppData\Local\Programs\GitHub Copilot\`; at
  first start the app downloaded the Copilot CLI it drives, 1.0.99-2, to
  `AppData\Local\github-copilot-sdk\cli\1.0.99-2\copilot.exe`.
  Exercised: first start at 19:53:23 (`data.db` created 19:53:24),
  sign-in by device-code flow at 19:54:27, three MCP servers added from
  the app's settings at 19:56 (MCP, the Model Context Protocol, is the
  plugin protocol for external tools; two of the three could not spawn,
  their commands not being installed), one general chat (`90825c78…`,
  created 19:59:11, three prompts, nine tool calls named `powershell` and
  `create`) in which the agent built and tested a small Node.js MCP
  server in the chat's working directory
  `.copilot\chats\2026-10-17\<slug>\`, running `npm install` there, then
  the GitHub repository `seanthegeek/doubleagent` added (cloned at
  20:04:42 into `.copilot\repos\doubleagent\`, worktree at 20:04:47) and
  one project session (`f60c7c7f…`, created 20:04:52, one prompt, one
  `powershell` call, one checkpoint). Node.js and the Visual Studio Build
  Tools, which the MCP work needed, were installed by the user beside the
  app. Every action ran before the first listing, so no per-action
  listing diff exists; the times above are the mapping, as on Linux. The
  app also created seven sessions of its own that were never prompted,
  pool and probe sessions (app log tasks `ws_session_warmup_loop`,
  `session_warmup_prepare`, `warm_canvas_catalogs`) whose
  `session-state/<uuid>/` directories hold a `workspace.yaml` and no
  `events.jsonl`: four with `cwd` the install directory, two with `cwd`
  `.copilot\canvas-catalog-probe` and one with `cwd` the clone. Analyzer
  0.14.0 over a collection taken before the deletion: 138 rows in 11
  sessions, no `parser:` row, `problems: []`, and 10 duplicate rows
  dropped from the `copilot-cli` secondary sources. The `copilot-desktop`
  parser wrote 15 `system` rows: `desktop settings:` (at the file's
  modification time), `account: <login> host=github.com kind=github
  default=1 token_present=false`, `model provider: GitHub Copilot
  type=github_copilot`, two `desktop session:` rows (`type=general_chat`
  and `type=project`, each `model=claude-sonnet-5.5 auto_approve=1
  permission_mode=on remote_control=0 archived=false`), four `activity
  agent_idle:` rows and one `activity workspace_ready:`, `project added:
  doubleagent kind=repository` with the clone's path,
  `github=seanthegeek/doubleagent default_branch=main`, one `worktree:`
  (`base=main`), one `workspace:` (`type=worktree`), one `checkpoint ref
  1:` and one `checkpoint commit`. The `copilot-cli` rows (`assistant` 7,
  `system` 92, `tool_result` 10, `tool_use` 10, `user` 4) are in
  [section 1 of `copilot-cli.md`](copilot-cli.md#1-evidence); each pool
  session is a session of one `session metadata: user_named=false ...
  client=github/autopilot` row whose `project_path` is its `cwd`. Not
  exercised: a scheduled task, a session automation, a denied tool call
  (allow-all stayed on), a model switch, a resumed session, a fork, a
  side chat, a remote session.
- **Observed (Windows), deletion and quit**: the same VM and app
  version. At 20:31 the user deleted the general chat with the app's own
  delete action (app log message kind `delete_session`) and took a
  listing diff, names and counts only; at 20:35 the user quit the app
  from the tray (the notification-area icon, which keeps the app
  running after its window is closed), leaving no `github.exe` or
  `copilot.exe` process, and took another. The delete removed the
  chat's `session-state/<uuid>/` directory entire, its `data.db`
  `sessions` row and the whole `.copilot\chats\2026-10-17\` tree, with
  the Node.js project the agent had built there; the quit checkpointed
  `data.db`'s WAL into the main file. What survived is in
  [What a deleted session leaves](#what-a-deleted-session-leaves). The
  analyzer run of the previous bullet predates the deletion; no run
  after it is recorded.

macOS was not observed.

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
| `.copilot/chats/<yyyy-mm-dd>/<slug>/` | a general chat's working directory and whatever the agent writes there (on the Windows install the Node.js project it built, `node_modules` included) | no; deleted with the session on Linux and Windows ([What a deleted session leaves](#what-a-deleted-session-leaves)) |
| `.local/share/com.github.githubapp/localstorage/tauri_localhost_0.localstorage` | Linux: the web view's local storage, SQLite `ItemTable(key, value BLOB)` | no: its values are UI state (tabs, caches, theme); the one user text, the unsent composer draft `home-composer-draft:main`, was never sent to the agent and has no time of its own; reading it is left for a later parser change |
| `AppData/Local/com.github.githubapp/EBWebView/Default/Local Storage/leveldb/` (`000003.log`, `CURRENT`, `LOCK`, `LOG`, `MANIFEST-000001`) | Windows: the web view's local storage inside the WebView2 user data folder (`EBWebView/`, a Chromium profile), in LevelDB, Google's key-value store format, whose `.log` file holds the newest writes; for the origin `http://tauri.localhost` it held the same keys as the Linux `ItemTable` | no, for the same reason as the Linux store; Chromium writes it lazily, so it held 30 bytes while the app ran and 6,174 bytes after the deletion |
| `.github-copilot-cli/logs/foundry.core<yyyymmdd>.log` | Foundry Local log (Foundry Local: Microsoft's runtime for local models) | no: model catalog fetches and a device id, no use of the agent; on Windows no device id file sat beside it, the Microsoft developer-tools device id being a registry value ([issue 148](https://github.com/seanthegeek/doubleagent/issues/148)) |

Desktop sessions in the event logs are told from CLI sessions by
`workspace.yaml` `client_name` `github/autopilot` (the CLI writes
`github/cli`); the `copilot-cli` parser writes it at the end of the
`session metadata:` row as ` client=<client_name>`.

## 3. Record schema

Every `created_at` and `updated_at` default is
`strftime('%Y-%m-%dT%H:%M:%fZ','now')`, ISO 8601 UTC with milliseconds
(real install (Linux)). `data.db` has 110 tables in 1.1.29 on Linux and
104 in 1.1.30 on Windows (`PRAGMA user_version` 194; not recorded on
Linux); the ones a parser reads, with the row counts observed on the
installs, are below. Columns marked "1.1.30" are in the Windows
install's definitions and not in the Linux list. Column
lists are as the survey printed the `CREATE TABLE` statement; where it
cut the statement, the list ends in "...".

| Table | Columns the parser reads (others named in the definition) | Observed |
| --- | --- | --- |
| `accounts` | `id`, `login`, `name`, `is_default`, `host` (default `github.com`), `token_updated_at`, `created_at`, `updated_at`, `access_token`, `kind` (default `github`), `settings_json`, `parent_account_id` | 1 row on each install: `kind` `github`, `host` `github.com`, `is_default` 1, `access_token` NULL; on Windows `settings_json` set and `parent_account_id` NULL |
| `settings` | `id` (always 1), `last_active_workspace_id`, `storage_location`, `instructions`, `github_access_token`, `github_token_type`, `github_scope`, `github_token_updated_at`; no timestamp column | 1 row on each install: `storage_location` the repos root under `~/.copilot`, `instructions` empty, token columns NULL |
| `model_providers` | `id`, `name`, `created_at`, `updated_at`, `type` (default `openai`), `settings_json`, `account_id` | 1 row: `type` `github_copilot`, `name` `GitHub Copilot` |
| `projects` | `id`, `name`, `container_kind` (`folder`, `repository` or `collection`), `main_repo_path` (unique), `default_branch`, `github_owner`, `github_repo`, `github_account_id`, `created_at`, `last_opened_at`; also `setup_script`, `run_script`, `instructions`, `auto_approve`, `trusted_config_sha256`, `trusted_config_accepted_at`, `branch_prefix`, `sandbox_enabled`, the `reusable_worktrees_*` settings, `checkout_is_managed`, `remote_control_enabled` and more; the definition ends `show_in_sidebar`, `provider_pr_binding_revision`, `agent_owner_session_id`, `copilot_account_id`, `copilot_account_source`, `github_account_source`, `remote_default_branch`, `default_branch_is_explicit` (1.1.30) | 1 row on each install: `container_kind` `repository`, `main_repo_path` under `~/.copilot/repos/`, owner and repository set, `default_branch` `main`; on Windows `checkout_is_managed` 1, `reusable_worktrees_enabled` 1, `auto_approve` 1, `sandbox_enabled` 0, `remote_control_enabled` 0 |
| `worktrees` | `id`, `project_id`, `path`, `branch`, `base_branch`, `created_at` | 1 row on each install: `path` under `~/.copilot/repos/copilot-worktrees/`, `base_branch` `main` |
| `workspaces` | `id`, `project_id`, `worktree_id`, `workspace_type` (`worktree`, `branch`, `folder` or `cloud`), `branch`, `name`, `created_at`, `source_pr_repo_full_name`, `source_pr_number`, `created_pr_repo_full_name`, `created_pr_number`; also `port`, the other `source_pr_*`, `source_issue_*` and `created_pr_*` columns, `last_diff_*`, token totals, `agent_merge_*`, `creator_session_id`, `archived_at`, `session_id`, `created_by`, and `host_id`, `name_source`, `explicitly_opened`, `coordinating_creator_session_id`, `provisional`, `provisional_base_ref`, `is_initialized`, `branch_session_create_scripts_started_at`, `lifecycle_generation`, `coordination_generation`, `initialization_generation`, `notification_recipient_session_id`, `session_bootstrap_config` (1.1.30) and more | 1 row on each install: `workspace_type` `worktree`, `port` 3000; on Windows `name_source` `auto`, `created_by` `user`, `is_initialized` 1 |
| `workspace_session_aliases` | `session_id` (primary key), `workspace_id`, `created_at` | 1 row on each install: the project session to its workspace |
| `workspace_checkout_bindings` | `workspace_id`, `repo_path`, `repo_full_name`, `display_name`, `checkout_kind` (`in_place` or `worktree`), `checkout_path`, `worktree_id` | 1 row on each install: `checkout_kind` `worktree`, `repo_path` the clone, `checkout_path` the worktree (not read by the parser; the worktree row carries the same path) |
| `sessions` | `id`, `title`, `session_type` (default `workspace`), `mode`, `model`, `reasoning_effort`, `created_at`, `remote_control_enabled`, `auto_approve` (default 1), `forked_from_session_id`, `archived_at`, `permission_mode`; also `is_running`, `was_interrupted`, `interruption_reason`, `updated_at`, `enabled_experiments_json`, token and context totals, `remote_session_mode`, `agent`, `provider_id`, `execution_location`, `context_tier`, `title_source`, `sandbox_enabled`, `agent_scope`, `provisional`, and `remote_availability`, `remote_availability_revision`, `remote_create_state`, `remote_prompt_delivery`, `recovered_empty_execution_event_id`, `empty_execution_failure_event_json`, `first_turn_context_delivery`, `lifecycle_generation`, `remote_lifecycle_owned` (1.1.30) and more | 2 rows on each install: `session_type` `general_chat` and `project`, `mode` NULL, `model` `claude-sonnet-5.5`, `auto_approve` 1, `remote_control_enabled` 0; `id` equals the `session-state` directory name; on Windows `reasoning_effort` NULL, `permission_mode` `on`, `title_source` `auto`, `remote_session_mode` `export`, `execution_location` `local`, `provisional` 0, `archived_at` NULL |
| `activity_items` | `id`, `workspace_id`, `session_id`, `activity_type`, `preview`, `is_read`, `created_at`, `updated_at`, `metadata_json` | Linux 6 rows: `agent_idle` ×5 with a `session_id` and a `preview` of 63 to 300 characters (the start of the reply), `workspace_ready` ×1 (31 characters, no session); Windows 5 rows: `agent_idle` ×4 with a `session_id`, `workspace_ready` ×1 without |
| `session_checkpoints` | `session_id`, `event_id`, `commit_sha`, `created_at` | Linux 4 rows for the project session, a 40-hex `commit_sha` each; the worktree's git log showed no new commit, so these are snapshot commits kept outside the branch; Windows 1 row for the project session |
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

On Windows (1.1.30, real install (Windows)) the other tables with rows
were `session_context_usage` (10 rows, `token_limit` 200000),
`app_state` (37 rows), `canvas_catalog_cache` (2 rows, `scope`
`project` and `user`), `project_checkouts` (1 row, `root_resource_uri`
a `file:` URI), `project_future_config_trust` (1 row, `project_id`,
`accepted_at`), `project_host_trust` (1 row), `project_trust_revisions`
(1 row), `reusable_worktree_pool` (1 row, `available`), `sqlite_sequence`
and `schema_migration_reversals`. The 37 `app_state` keys:
`activeWorkspaceId`, `canvas-store`, `catalogue-mcp-provenance`,
`cleared-background-tasks`, `copilot-available-models-v2` (23 KB),
`copilot-cloud-available-models-v2` (21 KB),
`copilot-cloud-workflow-metadata` (18 KB), `copilot-context-tier`,
`copilot-onboarding`, `copilot-reasoning-effort`,
`crash-reporting.tracking-id`, `enabled-experiments`,
`exp-assignment-cache`, `exp-first-launch-at`,
`feature-highlight-shown-today`, `feature-highlights`,
`github-read-outbox`, `home-discovery-dismissed`, `inbox-sections`,
`keep-awake-settings`, `lastRoutePath`, `main-content-tabs`,
`mock-connector-library`, `native-first-paint-theme-v1`,
`permission-mode-default-on`, `project-identity-host-revalidation-v1`,
`project-order`, `remote-control-feature-flag-split-v1`,
`remote-environments-legacy-import-completed`,
`remote-feature-flag-disables`, `right-panel`, `session-groups`,
`sidebar-project-groups`, `telemetry.machine_id`, `theme-settings-v2`,
`ui-zoom-level-v2`, `workspace-mru`. Empty: `agent_memory_bindings`,
`agent_memory_owners`, `agent_merge_delivery_origins`,
`agent_merge_permission_deliveries`, `agent_subscriptions`, `agents`,
`automation_group_contexts`, `builtin_agents`, `chat_parent_links`,
`collection_discovery`, `collection_members`,
`coordination_revocations`, `coordinator_agent_reports`,
`coordinator_assignments`, `coordinator_result_deliveries`,
`creator_notification_claims`, `factory_cloud_roles`,
`factory_creation_drafts`, `factory_cursors`, `factory_definitions`,
`factory_evaluations`, `factory_evidence_snapshots`,
`factory_job_settings`, `factory_jobs`, `factory_proposals`,
`factory_session_scopes`, `factory_targets`,
`factory_upgrade_receipts`, `inline_review_comments`,
`inline_review_replies`, `my_copilot_scheduled_task_invocations`,
`my_copilot_scheduled_task_triggers`, `my_copilot_scheduled_tasks`,
`plugin_marketplace_accounts`, `project_account_hints`,
`project_execution_scopes`, `project_host_catalogue_selections`,
`project_overview_summaries`, `project_repository_bindings`,
`project_sandbox_policies`, `project_trusted_config_hashes`,
`provider_models`, `pull_request_tours`, `remote_environment_metadata`,
`remote_environments`, `remote_session_adoption_suppressions`,
`review_thread_legacy_map`, `review_thread_messages`, `review_threads`,
`session_account_projects`, `session_automation_runs`,
`session_automation_runtime_reports`, `session_automations`,
`session_deletion_intents`, `session_managed_mcp_event_display_names`,
`session_mcp_event_sources`, `session_open_canvases`,
`session_side_chats`, `session_sources`, `software_factories`,
`software_factory_assessment_criteria`,
`software_factory_assessment_profiles`,
`software_factory_assessment_results`,
`software_factory_assessment_runs`, `software_factory_decisions`,
`workflow_runs`, `workflows`, `workspace_archive_preservation`,
`workspace_archive_preservation_attempt_worktrees`,
`workspace_archive_preservation_attempts`,
`workspace_archive_recoveries`, `workspace_changes_counts`,
`workspace_detach_notifications`, `workspace_diff_pins`,
`workspace_diff_snapshots`, `workspace_file_draft_sets`,
`workspace_file_drafts`, `workspace_file_edit_advisories`,
`workspace_file_save_journals`, `workspace_parent_links`,
`workspace_pull_request_links`, `workspace_repo_contexts`,
`workspace_side_chats`.

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

On Windows (real install (Windows), bundled CLI 1.0.99-2) the
differences above held, with these changes:

- `session.start` `producer` `copilot-agent`, `copilotVersion`
  `1.0.99-2`.
- `session.permissions_changed`, one per session, with the same
  `allowAll*` keys; the `copilot-cli` parser writes it as `permission
  mode: allow-all off -> on`. `session.model_change` came at the first
  prompt, `source` `startup`, `newModel` `claude-sonnet-5.5`.
- The general chat's 115 lines: 3 `user.message`, 8
  `assistant.message`, 9 `tool.execution_start` and
  `tool.execution_complete` pairs, 27 `hook.start` and `hook.end` pairs,
  1 `system.message`, 8 `session.usage_record`, 3
  `session.usage_checkpoint` and 1 `session.shutdown`. The project
  session's 30 lines held one prompt, one tool call and 7 hook pairs.
- Tool names `powershell` and `create` (the Linux sessions had `bash`).
  Three `create` calls failed with "Parent directory does not exist" and
  were retried. The first `powershell` call exited 1 because Windows
  PowerShell's execution policy refused to run `npm.ps1` ("running
  scripts is disabled on this system"), and the agent switched to
  `npm.cmd`; that is an ordinary failed tool result, not a permission
  decision: no `permission.requested` or `permission.completed` was
  written, and allow-all stayed on.
- `hookType` adds `postToolUseFailure`, the hook for a tool call that
  failed, to the Linux list.
- `session.shutdown` was written, unlike on Linux: at 20:13:47 for the
  chat, ten minutes after its last reply, and at 20:15:43 for the
  project session.
- No `pending-session:*` directory, no `rewind-file-snapshots/`, no
  `attachments` and no `crash-reports` were written.

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
  ([section 2](#2-transcript-files)). This is the Linux store; on
  Windows the web view is WebView2 and the same keys for the origin
  `http://tauri.localhost` were in the LevelDB store
  `AppData/Local/com.github.githubapp/EBWebView/Default/Local Storage/leveldb/`
  (14 records in `000003.log`, several keys rewritten more than once),
  also not parsed.

On Windows `data.db` was 1,347,584 bytes and unchanged while the app
ran, its WAL 1.8 MB at 20:08 and 1.9 MB at 20:32;
`repo-metadata-cache.db` had 12 tables and `PRAGMA user_version` 13
(real install (Windows)).

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

Real install (Windows), the deletion and quit bullets of
[section 1](#1-evidence): the app's delete of the general chat removed
its `session-state/<uuid>/` directory entire (`events.jsonl`,
`workspace.yaml`, `session.db`, `checkpoints/`, `files/`, `research/`,
`.workspace-fork.lock` and the `inuse.*` files), its `data.db`
`sessions` row and the whole `.copilot/chats/2026-10-17/` tree: the
chat's working directory, with the Node.js project the agent had built
there, `node_modules` included. The files an agent writes in a general
chat's directory do not outlive the chat. The project session's
`inuse.<pid>.hold` and `.lock` went too, its CLI process having ended at
the 20:15 shutdown. These survived:

- `data.db`: the chat's 3 `activity_items` rows (`agent_idle`, each with
  a reply preview and the deleted session's id);
  `session_deletion_intents` stayed at 0 rows; six `app_state` keys were
  rewritten at the deletion (`sidebar-project-groups`, `right-panel`,
  `cleared-background-tasks`, `session-groups`, `main-content-tabs`,
  `inbox-sections`).
- `data.db-wal`, until the app quit: 1,907,592 bytes, with 220
  occurrences of the chat's id against none in the main file. Quitting
  the app from the tray checkpointed the WAL (`data.db-wal` 0 bytes,
  `data.db` grown from 1,347,584 to 1,433,600 bytes), after which the id
  occurs 23 times in the main file, in the surviving `activity_items`
  rows and in freed pages. So the Linux finding that a deleted session's
  rows linger in `data.db-wal` holds only until the app next quits
  cleanly; after that the main file keeps the activity rows and whatever
  freed pages a later write has not reused.
- `session-store.db`, read by the `copilot-cli` parser: the chat's
  `sessions` row, all 3 `turns` with each prompt and reply in full
  (stamped 20:02:02, 20:02:49 and 20:13:48, the last at the shutdown), 3
  `session_files` rows naming the three files the agent created
  (`tool_name` `create`), 3 `search_index` rows and 8
  `assistant_usage_events` rows. Its WAL was not checkpointed at the
  quit (704,552 bytes, 220 mentions of the id). With the chat directory
  gone, the `turns` and `session_files` rows are what remains of the
  chat's work.
- `.copilot/session-state/.session-operation-locks/<uuid>.lock` (0
  bytes); the app log, with 41 lines naming the id, among them `session
  not found in memory during delete (already evicted) session_id=<uuid>`
  and `terminated agent processes owned by ending sessions
  scope="session_end" session_count=1 runtime_outcome="not_live" ...`
  under message kind `delete_session`; the CLI's process log, with one
  `Cleaning up session <uuid>: Session deleted via sessions.delete`
  line; `run/ws.port` and `run/ws.token`, rewritten at the deletion.
- The WebView2 local storage, whose tab-list keys were rewritten, as the
  Linux `side-chat-tabs` was.

The chat had no checkpoint, so no ref of it exists; the project
session's ref is intact. After the quit the six `run/` files, the seven
pool session directories, the 18 `.session-operation-locks` files, the
app log (193,758 bytes) and `repo-metadata-cache.db-wal` stayed on disk.

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

On Windows, 1.1.30 recorded 25 rows, `version` 170 to 194,
`recorded_by_app_version` `1.1.30`, with `PRAGMA user_version` 194 and
104 tables (real install (Windows)); the columns that differ from the
Linux list are marked in [section 3](#3-record-schema). Its bundled CLI
was 1.0.99-2 and its SDK protocol version 3 (SDK declarations of the
Windows build, `cliVersion.d.ts` and `sdkProtocolVersion.d.ts`).

## 7. Secrets

- `accounts.access_token` and `settings.github_access_token` (with
  `github_token_type`, `github_scope`) can hold a GitHub token; both were
  NULL on both installs, the token being in the GNOME keyring (the GNOME
  desktop's password store) on Linux and in Windows Credential Manager
  (the per-user credential vault Windows keeps) on Windows. The parser
  writes only whether each is present (`token_present=`,
  `github_token_present=`), never the value. On Windows the binary links
  the keyring library with its Windows store (`github 1.1.30
  windows-arm64 github.exe`: `keyring-core-1.0.0`,
  `windows-native-keyring-store`, `CredWriteW`), and the one credential
  file written that day under `AppData\Roaming\Microsoft\Credentials\`
  has the sign-in's modification time (19:54:27); the credential's
  target name is not determined.
- `accounts.login` and `projects.github_owner` name the account;
  `app_state` holds `telemetry.machine_id` and
  `crash-reporting.tracking-id` (not read).
- `activity_items.preview` is the start of an agent reply, and the
  scheduled-task and automation `prompt` columns are prompts the user
  wrote, kept verbatim.
- `run/ws.token` and `run/ws.release.token` (the local WebSocket auth
  tokens; 49 bytes on Linux, 48 on Windows, rewritten while the app runs
  and left on disk after it quits) are not read; the collector flags them
  `secret: true`.
- `.copilot/mcp-config.json`, the Copilot CLI's MCP server list, which
  the app writes when the user adds a server, can hold a token in a
  server's `env`: on the Windows install the `github` server's `env` held
  a GitHub personal access token in plain text. Not read; the collector
  flags the file `secret: true`
  ([section 3 of `collectors/research/copilot-cli.md`](../../collectors/research/copilot-cli.md#3-credentials)).
- On Windows the WebView2 `Local State` file's `os_crypt.encrypted_key`
  is the key Chromium encrypts cookie values and saved passwords with,
  wrapped by DPAPI (the Windows Data Protection API, which encrypts data
  to the user's logon credentials); the cookie and login stores were
  empty on the install. Not read; the collector flags `Local State`,
  the cookie store and `Login Data` `secret: true`. `Local State`
  `user_experience_metrics.client_id2` and `Preferences`
  `profile.edge_profile_id` are identifiers, not credentials.

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

MCP: the MCP servers the user adds from the app
(`.copilot/mcp-config.json`), their failed spawns (the CLI's
`logs/process-*.log`, `MCP server connection failed
{"server_name":"<name>","raw_error":"failed to spawn MCP server process:
program not found"}`) and the cached tool list of each connected server
(`AppData/Local/copilot/mcp-tools/<sha256>.json`,
[section 2 of `copilot-cli.md`](copilot-cli.md#2-transcript-files)) are
recorded on disk (Windows install) and not yet in the timeline
([issue 150](https://github.com/seanthegeek/doubleagent/issues/150)).
