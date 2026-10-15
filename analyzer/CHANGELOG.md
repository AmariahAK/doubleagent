# Changelog

All notable changes to the analyzer are recorded here. The version is
printed by `--version`. Changes to the `timeline.jsonl` and
`sessions.jsonl` fields (`timeline.csv` and `sessions.csv` columns up to
0.7.0) are called out, since they are interfaces.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed

- Codex and Open Interpreter history files now report malformed JSONL rows
  in a `system` row while preserving valid prompts ([#125]).

## [0.13.0] - 2026-10-15

### Added

- A `dropped:` line on the `timeline` stdout, always printed before
  `agents:`, counting the rows of secondary sources dropped because a
  primary store, or another secondary source, records the same event,
  with the agents that had any ([#122]).
- `inventory.json` key `deduplicated`, the new last key: the dropped
  rows per agent, `{}` when none ([#122]).
- The `hermes` parser reads the quick snapshots
  `state-snapshots/<id>/state.db` (collected with `--full`) like
  `state.db`, after one `system` row naming the snapshot, as a secondary
  source, so a session pruned or deleted from the live database is
  recovered once however many snapshots hold it ([#122]).
- Cline's `~/.cline/data/db/session-search.db`, the SDK's full-text index
  of each session, is read as a secondary source: one `system` row per
  indexed session at its start, then a `user` or `assistant` row per
  message with no timestamp, so a session whose transcript is gone still
  shows its turns ([#122]).
- Cline's CLI prompt history `~/.cline/data/cache/user_input_history.jsonl`
  is read as a secondary source: one `user` row per prompt, the last one
  at its `ts` and the others with no timestamp, since the CLI restamps
  every line each time it rewrites the file ([#122]).
- OpenClaw: compaction checkpoints (`*.checkpoint.<uuid>.jsonl`) and
  pre-doctor repair backups (`*.jsonl.pre-doctor-*-repair-*.bak`) in the
  sessions directory are parsed as secondary sources; a backup keeps the
  abandoned branches a doctor repair removed ([#122]).
- The `nanobot` parser reads the WebUI display transcript
  (`.nanobot*/webui/<key>.jsonl` and its `.segments/NNNNNN.jsonl`) as a
  secondary source: `user`, `assistant`, `tool_use`, `tool_result`,
  opt-in `thinking` and `system` rows (file edits, fork markers, context
  compactions) at the record's `created_at_ms`, which is true UTC unlike
  the session files' local time, so they pair with session rows within
  15 hours; a WebUI turn whose session file a `/new` emptied is now in
  the timeline ([#122]).
- The `nanobot` parser reads `~/.nanobot/history/cli_history`, the CLI's
  prompt history, as a secondary source: one `user` row per prompt at
  its own local time, with no session or project ([#122]).
- The `codex-cli` and `open-interpreter` parsers read `state_5.sqlite`
  (a `thread record:` system row per thread and its first prompt, with
  no timestamp) and `thread_history_1.sqlite` (the turns and turn items
  Codex projects from a rollout) as secondary sources, so a thread whose
  rollout was removed outside Codex, excluded by size or truncated is
  still in the timeline ([#122]).
- Roo Code: the CLI's input history `~/.roo/cli-history.json` is read,
  one `user` row per entry with no timestamp, task or project, as a
  secondary source that matches the task rows on text alone ([#122]).
- The `antigravity` parser reads the brain mirror of each conversation,
  `brain/<uuid>/.system_generated/logs/transcript_full.jsonl` (else its
  chunks, else the shortened `transcript.jsonl`, else its chunks) under
  every data directory, as a secondary source paired with the
  conversation database within 600 seconds, so a conversation whose
  database is gone or unreadable is still in the timeline ([#122]).

### Changed

- Interface change: the `timeline.jsonl` and `sessions.jsonl`
  `project_path` of a Windows path (a drive letter or a `\\` network
  share) is written in one canonical form, whichever agent and store
  recorded it: upper-case drive letter, backslash separators, no repeated
  or trailing separator (except in a drive root such as `C:\`), and the
  extended-length prefix `\\?\` removed. Antigravity's
  `c:/Users/sean/demo` (from a `file:` URI) and `C:/users/sean/demo2`
  are now `C:\Users\sean\demo` and `C:\users\sean\demo2`. The case
  after the drive is kept as recorded; POSIX paths are unchanged
  ([#112]).
- Interface change: `inventory.json` `projects` groups Windows paths that
  differ only in case into one project, keyed by the spelling of the
  collected project directory when it is one, so its `status` is
  `collected` and its rows, sessions and files are under one key; a
  project the input does not hold is keyed by the first spelling the rows
  record. Project directories from `collection.json` are in the same
  canonical form ([#112]).
- Interface change: `timeline.jsonl` no longer holds a row of a second
  copy that repeats a transcript row or another copy. The secondary
  sources are Aider's `.aider.input.history` and `.aider.llm.history`;
  Antigravity's CLI `history.jsonl` and brain mirror; Claude Code's
  `history.jsonl`; Claude Desktop's Cowork `audit.jsonl`; Cline's
  `session-search.db` and CLI `user_input_history.jsonl`; Codex CLI's
  and Open Interpreter's `history.jsonl`, `state_5.sqlite` and
  `thread_history_1.sqlite`; Gemini CLI's and Qwen Code's `logs.json`;
  Goose's `history.txt`; Hermes's `state-snapshots/<id>/state.db` and
  `sessions/<id>.jsonl` diverts; Letta's `transcript.jsonl`; Muse Code's
  `tui-history.jsonl`; nanobot's WebUI transcript and `cli_history`;
  OpenClaw's reset and deleted archive files, compaction checkpoints and
  pre-doctor repair backups; Roo Code's `cli-history.json`; and Tabby's
  database backups and `events/` log. One of their rows is
  dropped when a primary-store row of the same host, user and agent has
  the same `turn_type` and `text` (two `tool_use` or two `tool_result`
  rows that both carry a `tool_use_id`: the same `tool_use_id` instead),
  the same `session_id` (or, without one, the same `project_path`, or,
  without either, any session or project) and, when the secondary row
  has a `timestamp_utc`, one at most 2 seconds away (a wider window
  where the parser table says so); a row with no timestamp, such as Muse
  Code's, matches on text alone, the session-scoped ones first, so the
  most specific copy takes the primary row. Secondary rows that no
  primary row took are then matched against the copies a primary row
  took and against each other the same way, the timestamped rows first
  in time order and the undated ones after, and looking under a broader
  scope too (the project, then any) when a candidate's session and
  project do not differ from the row's; so three copies of a primary
  event leave only the primary row, copies of one event kept by several
  backups appear once, as the earliest timestamped copy, and of an
  undated and a timestamped copy the timestamped one is kept. A row pairs only with one from a
  different file, so two identical lines in one file both stay.
  Secondary rows with no match are kept, so a prompt whose transcript is
  gone is still in the timeline ([#122]).
- Goose's CLI `history.txt` (both locations) is a secondary source: a
  history row is dropped when a `sessions.db` user row has the same text,
  and kept when none does, such as a prompt of a removed session ([#122]).
- Aider's `.aider.input.history` and `.aider.llm.history` are secondary
  sources of `.aider.chat.history.md`: an input-history prompt the chat
  history records is dropped, since the chat row takes its time from it,
  and one the chat history lacks is kept ([#122]).
- Claude Desktop: each Cowork session's `audit.jsonl` is read in full on
  every run, its prompts, replies and tool calls too, not only when the
  session dir holds no transcript, and is a secondary source of that
  transcript; the audit rows without a session record take the `init`
  line's `cwd` as `project_path`, as the transcript's rows take the
  JSONL `cwd`. The Cowork session record `local_<uuid>.json` is a
  secondary source too, and its `initialMessage` is now always a `user`
  row, with no timestamp, instead of only when neither a transcript nor
  an audit log was collected; a Code-tab record's stays a fallback,
  since its transcript belongs to agent `claude-code` ([#122]).
- The `letta` parser reads `.letta/transcripts/<agent>/<conversation>/transcript.jsonl`
  always, also when the conversation's local-backend `messages.jsonl` was
  collected (it gave one `system` row pointing at it before), as a
  secondary source paired with `messages.jsonl` within one hour, since
  Letta stamps each line at the end of its turn; its `tool_use` text is
  now the command, path or query, as the `messages.jsonl` row shows it,
  instead of the arguments JSON ([#122]).
- The `hermes` parser's `sessions/<id>.jsonl` diverts are a secondary
  source: a message the live `state.db` also holds for that session is
  shown once ([#122]).
- Tabby's pre-migration backups `db.backup-*.sqlite` and the event log
  `events/YYYY-MM-DD.json` are secondary sources: a backup's thread and
  event rows that the live database (or an earlier backup) also holds,
  and an event log prompt or choice that `user_events` also holds, are
  dropped. The backup's leading `system` row now names the backup file
  ([#122]).
- OpenClaw: a published reset or deleted archive blob in
  `session_transcript_archives` is parsed in full instead of one `system`
  row naming its file, and the `.jsonl.reset.*` / `.jsonl.deleted.*` file
  is a secondary source; the session id of a legacy JSONL file is now its
  header `id` ([#122]).

## [0.12.0] - 2026-10-15

### Added

- `timeline` writes `inventory.json` beside `timeline.jsonl` and
  `sessions.jsonl`: the input's `kind`, `notes` and `problems` (the
  problems met while opening the input, then each file a parser could
  not read), the files, bytes and parser of each agent in each user home
  and Docker volume (`homes`, the same array `detect --json` prints), row
  and session counts per project (`projects`) and outside any project
  (`outside_projects`), each split by agent and `turn_type`, and the
  lists of agents parsed, detected but not parsed, and whose parser found
  no rows. The row and session counts follow the filters, as the stdout
  breakdown does; `homes`, `notes`, `problems` and the file counts do not
  ([#103], [#104]).
- Each `inventory.json` project starts with `status`: `collected` when
  the path is a project directory the collection holds
  (`collection.json` `projects`), `referenced` when only timeline rows
  name it. A collected project that no row names is listed with zero
  counts ([#104]).
- Each `inventory.json` project counts the files the collection holds in
  its directory: every agent gains `files` and `bytes`, an agent with
  project files and no rows (a `.cursor/` directory, an agent with no
  parser) is listed with zero rows, so the keys of `agents` are every
  agent used on the project, and `shared_files` counts the files no
  single agent owns (`AGENTS.md`, `.mcp.json`). These counts do not
  follow the filters ([#104]).
- `detect` prints project directories in a table of their own after the
  table of homes: one line per agent of each project with its files,
  bytes and parser, and a `(shared)` line for files such as `AGENTS.md`.
  `detect --json` holds them as `projects` (`path`, `users`, `agents`
  with `agent`, `files`, `bytes`, `parser`, `shared_files`,
  `shared_bytes`). `project` never appears as an agent.
  Collections from collectors before and after 1.12.0 give the same
  lists, and loose input lists no project ([#104]).
- An agent whose only files are in a project directory counts as
  detected on the timeline's `agents:` line and in `inventory.json`
  ([#104]).
- `timeline` prints a line for `inventory.json` after the `sessions:`
  line: `inventory: <path> (homes, projects, counts per agent,
  problems)`. The `rows:` and `sessions:` lines are unchanged ([#103],
  [#104]).
- `docs/output.md` documents every key of `detect --json` and
  `inventory.json` and every field of `sessions.jsonl` in a table with
  its type, and the `timeline.jsonl` table gains a type column ([#103],
  [#104]).
- The bundled catalog copy detects the Antigravity CLI's file secret
  store `plugin-secrets.json` (`.config/antigravity`,
  `Library/Application Support/antigravity`, `AppData/Roaming/antigravity`)
  as `antigravity` ([#90]).
- The bundled catalog copy follows collector 1.12.0: the Antigravity
  desktop app's Electron user-data directory
  (`Library/Application Support/Antigravity`, `.config/Antigravity`,
  `AppData/Roaming/Antigravity`) and its macOS logs directory
  `Library/Logs/Antigravity` are detected as `antigravity` ([#83]).
- The bundled catalog copy detects `AppData/Local/antigravity`, the
  Windows staging directory of the Antigravity desktop app and CLI, as
  `antigravity`, following collector 1.12.0 ([#83]).
- The `antigravity` parser reads the Antigravity desktop app's
  conversations: `conversations/*.db` and `conversation_summaries.db`
  under `.gemini/antigravity` (the desktop app 2.x), and under
  `.gemini/antigravity-ide` and `.gemini/antigravity-backup` (the
  separately installed IDE and the app's migration backup) as well as
  `.gemini/antigravity-cli`. Before, only the CLI's conversations produced
  rows and the app's were collected but silently skipped. Each
  conversation's session start row now names the surface that wrote it,
  `source=<trajectory source>` (`cli` for the CLI, `cascade_client` for the
  desktop app, the number for a value not in the table) and
  `data_dir=<the .gemini subdirectory>` ([#83]).
- Rows from the Antigravity CLI's `history.jsonl` carry the
  conversation's id in `session_id` when the line has `conversationId`,
  which CLI 1.3.x writes; older lines have none and keep `session_id`
  empty. A prompt in the history can now be joined to its conversation
  database ([#89]).
- The `antigravity` parser turns Antigravity's permission state into
  `system` rows. Each grant in a step's `steps.permissions` blob is a
  `permission grant: action=<action> target=<target> allow=<true|false>
  scope=<scope>` row, and each file access entry a `permission grant:
  path=<path> is_directory=<true|false> allow=<true|false> scope=<scope>`
  row, after the step's rows and with its `tool_name` and `tool_use_id`.
  The standing grants in `.gemini/config/config.json`,
  `.gemini/config/projects/*.json`, `.gemini/config/sidecars/*/sidecar.json`
  and the CLI's `.gemini/antigravity-cli/settings.json` (allow lists,
  sidecar access grants, the migration and sandbox flags, trusted
  workspaces) are one `permission setting: <key>=<value> (from <file>,
  file mtime)` row per entry, timestamped by the file's modification time
  ([#92]).
- The `claude-code` parser records the permission mode and the model as
  events: `permission mode: <mode>` at a session's first
  `permission-mode` record or `permissionMode` prompt key and
  `permission mode: <old> -> <new>` on each change, and `model: <id>` at
  the first assistant reply and `model: <old> -> <new>` on each change,
  with ` requested=<requestedModel>` when the requested model differs.
  The `claude-desktop` transcripts, read with the same reader, gain the
  same rows ([#93]).
- The `claude-code` parser reads the standing permission settings: one
  `system` row per `permissions.allow`, `deny`, `ask` and
  `additionalDirectories` entry and one for `defaultMode` and
  `disableBypassPermissionsMode` in `.claude/settings.json` and
  `.claude/settings.local.json` (the user's and, from a collection, a
  discovered project's), and one per `allowedTools` entry and for
  `hasTrustDialogAccepted` and `hasClaudeMdExternalIncludesApproved` of
  each project in `.claude.json`, timestamped by the file's modification
  time and saying so. These files were not read before; no other key in
  them is read ([#93]).
- The `claude-desktop` session-record row ends with
  `permission_mode=<mode> effort=<effort>`, and each per-session grant in
  the record (`alwaysAllowedReasons` and `sessionPermissionUpdates`
  entries, `chromePermissionMode`, `chromeAllowedDomains`,
  `cuAllowedApps`, `cuGrantFlags`, `cuFlagsGrantedAt`) is a
  `permission grant:` row at the record's `lastActivityAt` ([#93]).
- The `codex-cli` and `open-interpreter` parsers record the model and
  the permission policy of each turn as events: `model: <id>` at the
  first `turn_context` that names a model and `model: <old> -> <new>` on
  each change, and `permission mode: approval=<approval_policy>
  sandbox=<sandbox_policy> profile=<permission_profile> network=<network>`
  at the first `turn_context` with a policy and `permission mode: <old> ->
  <new>` on each change (`-` for a missing field). Codex writes no
  per-call approval to its rollouts, so there is no decision row
  ([#96], [#97]).
- The `gemini-cli` and `qwen-code` parsers read `trustedFolders.json`
  (`.gemini/trustedFolders.json`, `.qwen/trustedFolders.json`): one
  `permission setting: trustedFolders.<path>=<TrustLevel> (from <file>,
  file mtime)` row per folder, with `project_path` the folder and the
  file's modification time. A tool call whose status is `cancelled` or
  `awaiting_approval` is followed by a `permission decision: <status>`
  row with its `tool_use_id`; the `[cancelled]` prefix on the result row
  stays. `gemini-cli` writes `model: <id>` at a session's first gemini
  message that names a model and `model: <old> -> <new>` on each change,
  and `qwen-code` writes `model: <id>` from the first assistant record
  when no `session_model` record named one, and a change row when an
  assistant record's model differs ([#96], [#97]).
- The `antigravity` parser writes `model: <id>` before the rows of a
  conversation's first step that `gen_metadata` names a model for and
  `model: <old> -> <new>` before those of every later step on another
  model, and a `permission decision: user_rejected` row after the result
  of a `run_command` or `mcp_tool` call the user rejected, with the call's
  `tool_use_id`; a `run_command` result that ran in the sandbox ends with
  `sandbox=true` ([#96], [#97]).
- The `opencode` and `kilo-code` parsers record the model and the agent
  as events: `model: <modelID> provider=<providerID>` before the first
  message of a session that names a model and `model: <old> -> <new>
  provider=<providerID>` before each message that changes it, and
  `permission mode: agent=<name>` and `permission mode: agent=<old> ->
  agent=<new>` for the message's `agent`, since an OpenCode agent carries
  its own permission ruleset. In a session that only the V2
  `session_message` table holds, the `model-switched` and
  `agent-switched` records, which were printed as raw JSON before, become
  the change rows ([#96], [#97]).
- The `crush` parser records the model as events: `model: <model>
  provider=<provider>` before the first message of a session that names
  one and `model: <old> -> <new> provider=<provider>` before each message
  that changes it ([#96]).
- The `pi` parser reads `.pi/agent/trust.json`, the project trust
  decisions in the agent directory pi and little-coder share: one
  `permission setting: <path>=<true|false> (from .pi/agent/trust.json,
  file mtime)` row per project, with `project_path` the project and
  `timestamp_utc` the file's modification time, not the time of the
  decision. The file was not read before ([#97]).
- The `letta` parser adds a `model: <id> provider=<provider>` row after
  the first `.letta/sessions.jsonl` line of each CLI session that names a
  model, and `model: <old> -> <new> provider=<provider>` when a later
  line of the session names another ([#96]).
- The `continue` and `pearai` chat-session parsers yield a `system` row
  `model: <id>` at a session's first model and `model: <old> -> <new>`
  ahead of a later history item that names a different one: Continue
  starts from `chatModelTitle` (else the first `promptLogs[].modelTitle`)
  and compares each item's `promptLogs[].modelTitle`, PearAI compares each
  item's `promptLogs[].completionOptions.model`. The `continue` parser
  also yields `permission decision: accepted=<value>` after each
  `toolUsage.jsonl` record's `tool_result` row and
  `permission decision: canceled` for a session tool call whose state is
  `canceled` ([#96], [#97]).
- The `vscode` parser writes `model: <id>` and `model: <old> -> <new>`
  rows from the request `modelId`, and `permission mode: <mode>` and
  `permission mode: <old> -> <new>` rows from the request
  `modeInfo.telemetryModeId` (`ask`, `agent`, `edit`, `custom`). A tool
  invocation's `isConfirmed` becomes a `permission decision:
  confirmed=<value>` row after its result (`true` or `false` before VS
  Code 1.104, else the confirmation kind such as `UserAction(4)` or
  `Denied(0)` with its `source`, `scope`, `id`, `selectedButton` or
  `reason`, and `tool_source=<type>`), a `confirmation` response part a
  `permission decision: confirmation isUsed=<bool> buttons=<list>
  title=<title>` row, and a request sent by a confirmation button a
  `permission decision: confirmation=<label>` row ([#96], [#97]).
- The `cody` parser writes `model: <id>` and `model: <old> -> <new>`
  rows from the assistant message `model`, per chat, and turns each
  `processes[]` entry of type `confirmation`, dropped before, into a
  `permission decision: confirmation state=<state> title=<title>` row
  ([#96], [#97]).
- The `twinny` parser writes `model: <id>` and `model: <old> -> <new>`
  rows from `meta.model`, per conversation, and a `permission decision:
  waiting` or `permission decision: skipped` row (with
  ` approval=<command|change>` when recorded) after the result of a tool
  step saved while it waited for the user's Run or Skip, or after the
  user skipped it ([#96], [#97]).
- The `zed` parser yields `model: <model> provider=<provider>` once per
  thread after the thread-start row, and one `permission setting:
  <key>=<value> (thread blob, as of updated_at)` row per thread-scoped
  grant in the thread blob: `profile`, each `sandbox_grants.write_paths`
  and `sandbox_grants.network_hosts` entry, and each of the
  `network_any_host`, `allow_fs_write_all`, `unsandboxed` and
  `sandbox_fallback` flags that is set, with the thread id as
  `session_id` and the thread's `updated_at` as the time ([#96], [#97]).
- The `goose` parser yields `model: <model_name> provider=<provider_name>`
  and `permission mode: <goose_mode>` after each session's start row, and
  `model: <old> -> <new> provider=<provider>` (with
  ` requested=<requestedModel>` when the resolved model differs) before a
  message whose `metadata_json.inference` names another model ([#96],
  [#97]).
- The `kiro` parser yields `model: <id>` before a conversation's first
  history entry and `model: <old> -> <new>` before each entry whose
  `request_metadata.model_id` differs; an entry without one falls back to
  `model_info.model_id` (or the legacy `model`) and the row ends
  ` source=model_info` (or ` source=model`) ([#96]).
- The `hermes` parser yields `model: <id>` and
  `model: <old> -> <new>` rows from the main-loop rows of the
  `session_model_usage` table, at each model's `first_seen` and with
  ` provider=<billing_provider>`, or one `model: <sessions.model>` row at
  `started_at` when the session has none ([#96]).
- The `ollama` parser yields `model: <model_name>` before a chat's first
  assistant message that names a model and `model: <old> -> <new>` before
  each assistant message whose `model_name` differs ([#96]).
- The `openhands`, `agent-zero` and `nanobot` parsers record the model
  as an event: `openhands` writes `model: <agent.llm.model>` after each
  conversation's header row; `agent-zero` writes `model: <id>` before an
  agent's first reply and `model: <old> -> <new>` when
  `metadata.responses.provider_model_key` changes, ending ` agent=<n>`
  for a subordinate agent; `nanobot` writes `model: <preset> (preset)`
  after the session start row, since the session records a model preset
  of its configuration, not a model id ([#96]).
- The `openhands` parser follows a rejected call's `tool_result` with a
  `system` row `permission decision: rejected
  rejection_source=<source> <reason>`, and ends an action's `tool_use`
  text with ` security_risk=<value>`, the security analyzer's rating
  ([#97]).
- The `muse-code` parser records the starting permission profile and
  security mode as `permission mode: approval=<a> reviewer=<r>
  profile=<id>` (with its `cause` and declared `format`) and
  `permission mode: security_mode=<value>`, the automated reviewer's
  verdict as `permission decision: <outcome>
  kind=automated_review_completed ...` with its rationale, the model as
  `model: <id> provider=<provider>` at the first model a session log
  names and `model: <old> -> <new>` on each change, and each trusted
  project in `.config/muse/trust.json`, not read before, as a
  `permission setting: projects.<path>.decision=<decision> (from
  .config/muse/trust.json, file mtime)` row ([#96], [#97]).
- The `claude-code` `permission decision:` row ends with
  `toolDenialKind=<value> userFeedback=<text>` when the line records
  either key, and a line with either key but no `permissionDecision`
  gets the row too ([#97]).
- The `claude-desktop` parser writes `model: <id>` from each audit log's
  `init` line even when the transcript exists, `model: <old> -> <new>`
  in the full audit fallback, and a `model_refusal_fallback:` row; adds
  one `permission grant:` row per entry of `approvedToolNames`,
  `webFetchAllowedUrls`, `egressAllowedDomains`,
  `userApprovedFileAccessPaths`, `enabledMcpTools` and
  `fileDeleteApprovedMounts` in a session record; ends each scheduled
  task row with `permission_mode=<mode> model=<model>`; and reads
  `remote-session-spaces.json`, not read before, as one
  `permission setting:` row per folder granted to a remote Cowork
  session, at the file's modification time ([#96], [#97]).
- The catalog copy detects the ChatGPT desktop app's renamed Windows
  package, `OpenAI.Codex` (its Chromium profile, log directory and
  settings hive), as `chatgpt-desktop` ([#113]).
- The `codex-cli` and `open-interpreter` session start row ends with
  `account=<creator_account_id> user=<creator_user_id>` when the
  rollout's `session_meta` names the ChatGPT account and user that
  created the thread, as Codex Desktop inside the ChatGPT desktop app
  writes them; a rollout without them keeps the old text ([#118]).
- The `codex-cli` parser reads the ChatGPT desktop app's scheduled
  automations, `.codex/automations/<slug>/automation.toml`, not read
  before: one `system` row per file, `scheduled task: <id> name=<name>
  kind=<kind> status=<status> rrule=<rrule> target_thread=<thread id>
  created=<UTC> updated=<UTC> (from <file>, file mtime) prompt:
  <prompt>`, at the file's modification time, with `session_id` the
  thread the automation runs in ([#119]).
- The catalog copy detects the ChatGPT desktop app on macOS (its
  `Library/Application Support/Codex` profile, logs, preferences,
  `HTTPStorages` and computer-use group container) as `chatgpt-desktop`,
  and attributes `Library/Application Support/com.openai.codex` to
  `chatgpt-desktop` instead of `codex-cli` ([#121]).

### Changed

- The bundled catalog copy follows collector 1.12.0's project catalog: a
  project-directory file is detected as the agent that owns it
  (`claude-code` for `.claude/` and `CLAUDE.md`, `cursor` for `.cursor/`,
  `aider` for `.aider.chat.history.md`), and only files several agents
  read (`AGENTS.md`, `AGENTS.override.md`, `AGENT.md`, `.agents/`,
  `.mcp.json`, the shared GitHub Copilot instruction files, `SOUL.md`,
  `USER.md`) stay `project` ([#104]).
- Files from a project directory are attributed to the agent that owns
  them in `detect` and `inventory.json`, not to `project`:
  a repository's `.claude/` is `claude-code`, its
  `.aider.chat.history.md` `aider`. A manifest row with agent `project`,
  as collectors before 1.12.0 wrote for every project file, is
  re-attributed from the bundled project catalog; a file several agents
  read (`AGENTS.md`) stays `project` and is counted as a shared file of
  its project. Project directories are recognised
  from `collection.json` `projects` (or a row with agent `project`), not
  from the agent, so the `claude-code` parser still gives a project's
  settings rows the project's `project_path` ([#104]).
- `detect --json`: the flat key `agents`, one object per user, home and
  agent, is replaced by `homes[].agents`, each home's agents sorted by
  name with `agent`, `files`, `bytes` and `parser` (0.11.0's `homes` had
  no `agents` key); `homes` lists user homes and Docker volumes only,
  since project directories moved to `projects`. Nothing in the object
  is named `outside_projects`. The first table `detect` prints leaves out
  project directories the same way. A script that read `.agents` reads
  `.homes[].agents`, plus `.projects[].agents` for project files
  ([#104]).
- The `agents:` line `timeline` prints reads
  `parsed: <list>; detected but not parsed: <list>`, with `none` for an
  empty list, followed by `; parser found no rows: <list>` when a
  detected agent's parser produced no rows, and `none were found` for an
  input with no agent data. It used to read
  `parsed <list>; detected only <list>`, which said `detected only none`
  when every detected agent was parsed, `parsed none; detected only none`
  for an empty input, and nothing about agents whose parser found no
  rows ([#85]).
- The `qwen-code` model rows take the common form: a `session_model`
  record reads `model: <id> auth=<authType>` (was
  `session_model: <id> auth=<authType>`), and a `logs.json`
  `model_switch` entry reads `model: <from> -> <to> reason=<reason>`
  (was `model_switch: <from> -> <to> (<reason>)`) ([#96]).
- The pi session reader, which parses `pi` sessions, the little-coder
  sessions in pi's directory and Letta's local-backend `messages.jsonl`,
  writes `model: <id> provider=<provider>` at the first entry that names
  a model (a `model_change` or an assistant message) and
  `model: <old> -> <new> provider=<provider>` on each change, with
  ` requested=<model>` when the assistant's `responseModel` differs from
  the `model` asked for. A `model_change` entry that names the model
  already in force, a switch the user made, still gets the plain
  `model: <id> provider=<provider>` row. It replaces
  `model_change: <provider>/<id>`, which appeared only for a
  `model_change` entry, so a session whose model was named only on
  assistant messages had no model row. The `model` column is now
  `responseModel` when the message has one ([#96]).
- The `openclaw` parser writes `model: <id> provider=<provider>` at a
  session's first model (the `session_windows` `model`, else the first
  `model_change` or assistant message) and `model: <old> -> <new>
  provider=<provider>` on each change, with ` requested=<model>` and the
  repeated `model_change` row as above, in place of
  `model change: <provider>/<id>` ([#96]).
- The `cline` parser's model rows take the `model: <id>` and
  `model: <old> -> <new>` form. An SDK session's start row no longer ends
  with `model=<id>`; a `model: <id> provider=<provider>` row follows it
  (also for a `sessions.db` index row), and a message whose
  `modelInfo.id` differs yields `model: <old> -> <new>
  provider=<provider>`. The legacy `model_usage: model_id=...` rows from
  `task_metadata.json` become `model: <id> model_provider_id=<p>
  mode=<m>` at the first entry and on a change of `model_id`, and
  `permission mode: <mode>` and `permission mode: <old> -> <new>` rows
  carry the entry's `mode`; an entry that changes neither has no row
  ([#96], [#97]).
- The `muse-code` approval decision row reads `permission decision:
  <decision> source=<decision_source.kind> policy_result=<p>
  amendment=<a>`, where it read `approval <decision> by <source>`; and the
  `/model` row reads `model: <old> -> <new>`, preceded by `model:
  <previous>` when the log named no model before it, where it read
  `model: <new>` ([#96], [#97]).

### Fixed

- `tools/proto_descriptors.py extract` no longer fails with a `TypeError`
  on Mach-O binaries such as the macOS builds of `agy` and the Antigravity
  desktop app's language server ([#86]).
- The `antigravity` parser reads the path of a `code_action` step that
  deletes a file: `ActionSpecDeleteFile` keeps the path in field 1, where
  the parser had read field 2, so the `tool_result` row lost the path or
  the step could not be decoded ([#88]).
- `tools/shape.py` redacts OpenAI user and organisation ids (`user-` or
  `org-` and 20 or more letters and digits) as `<user-id>` and
  `<org-id>` in keys and paths, a `win32:/...` path key and an absolute
  path after a `<prefix>:` in a key (`local:C:\...`) as `<abs-path>`,
  and the elements of a key that is a JSON-encoded array, which it
  printed whole before: Codex Desktop's `.codex-global-state.json` keys
  state by arrays holding the user id and absolute file paths ([#117]).

### Removed

- `timeline` no longer writes `detect.json`; its `kind`, `notes`,
  `problems` and per-home agent table are in `inventory.json` as `kind`,
  `notes`, `problems` and `homes` ([#104]).

## [0.11.0] - 2026-10-12

### Added

- The bundled catalog copy follows collector 1.11.0: Claude Desktop's
  MSIX data directories under `AppData/Local/Packages`, and
  `AppData/Local/Claude` and `AppData/Local/Claude-Data`, are detected as
  `claude-desktop` ([#73]).
- The bundled catalog copy follows collector 1.11.0: the Claude Code CLI
  cache directory (`Library/Caches/claude-cli-nodejs`,
  `.cache/claude-cli-nodejs`, `AppData/Local/claude-cli-nodejs/Cache/*`), which
  holds per-project MCP server logs, is detected as `claude-code` ([#81]).

- A `claude-desktop` parser: Claude Desktop's Cowork and Code-tab
  transcripts (Claude Code JSONL under the app-data directory, with the
  project path taken from the session record), each Cowork session's
  `audit.jsonl` (permission requests, responses and automatic decisions,
  and every turn when the transcript is missing), session records,
  scheduled tasks and Code-tab worktrees. The rows come out under agent
  `claude-desktop` ([#48]).
- The bundled catalog copy follows collector 1.10.0: the agents
  `autogen-studio`, `camel-ai`, `crewai`, `dify`, `flowise`, `langflow`,
  `metagpt`, `n8n` and `pydantic-clai`, the project entry `.clai`, the
  legacy Open Interpreter directories under `open-interpreter`, and the
  Dify, Langflow and n8n Docker volume patterns are detected; none is
  parsed yet ([#64]).
- Claude Code 2.1.295 permission decisions: a tool-result line that
  records how the call was allowed or denied gets a `system` row after
  its result, `permission decision: <decision> source=<source>
  reason=<reasonType>`, carrying the call's `tool_use_id` ([#76]).
- Claude Code's per-process registry `~/.claude/sessions/<pid>.json` is
  read: one `system` row per process at its start time, `claude-code
  process <pid> <kind> status=<status> entrypoint=<entrypoint>
  bridge=<id or none> host_session=<id or none>`, joined to the session.
  A `bridge=` id means the process was under Remote Control when the
  collection ran; check it against the EDR's process list, since a
  crashed process can leave its file behind ([#80]).
- Claude Desktop Code-tab session rows end with the session's persisted
  Remote Control state, `remote_control=<bool> bridges=<n>
  spawned_remotely=<bool> steered_remotely=<bool>`, and a session that
  was under Remote Control when the app quit to update gets a `remote
  control live at update quit` row at that time ([#80]).

### Fixed

- The detection test for the framework agents passes on a case-insensitive
  filesystem (macOS): the two spellings of CrewAI's Windows directory are
  built in separate homes instead of one ([#75]).

## [0.10.0] - 2026-10-06

### Changed

- The analyzer is now `doubleagent`: `pip install .` installs the
  distribution `doubleagent` (was `coding-agent-analyzer`) with the
  command `doubleagent` (was `analyze-agent-artifacts`), and the Python
  package is `doubleagent` (was `agent_analyzer`), so `python3 -m
  doubleagent` runs it from a checkout. `--version` prints
  `doubleagent <version>`. The output files and their fields are
  unchanged ([#47]).
- `zstandard` is a required dependency, imported at start-up like
  `python-dateutil`. The `system` row that said "zstandard package not
  installed" for each compressed Zed thread, Codex or Open Interpreter
  rollout and OpenClaw row is gone ([#47]).
- `pyproject.toml` reads the version from `doubleagent.VERSION`, so it is
  set in one place ([#47]).

## [0.9.0] - 2026-10-06

### Added

- An `ollama` parser for the Ollama desktop app's chat database
  (`Library/Application Support/Ollama/db.sqlite` on macOS,
  `AppData/Local/Ollama/db.sqlite` on Windows, schema versions 16 to 19)
  and the `ollama run` prompt history `.ollama/history`. Tool calls and
  results are paired by position, with `tool_use_id` set to
  `<chat id>:<tool_calls.id>`; attachments appear as their name and size
  only, and the account and settings tables are not read. History rows
  have no timestamp or session, so they sort last and are dropped by
  `--since` and `--until` unless `--keep-undated` is given ([#43]).

### Changed

- The bundled catalog copy follows the collector: the Ollama exclusion is
  now `.ollama/models/blobs`, so `.ollama/models/manifests` and
  `models/metadata` files appear in collections ([#44]).

### Fixed

- Timestamps with a fraction of one, two, four or five digits, such as
  go-sqlite3's `2026-03-01 09:00:00.5-08:00`, are converted on Python 3.10
  as well; before, they gave an empty `timestamp_utc` there ([#45]).
- `tests/run.sh` runs only the named tests when given a module, class or
  method name (`tests/run.sh test_catalog`,
  `tests/run.sh test_parsers.ClaudeCodeTests.test_rows`); before, it passed
  the name to `unittest discover`, which ignored it and ran the whole suite.
  With no names it still runs discover with the options given, and with
  names it refuses the discover-only options `-p`, `-s` and `-t` ([#34]).

### Removed

- The bundled catalog copy drops the collectors' unused credential pattern
  `.claude-*/.device-keys.json`; detection is unchanged ([#41]).

## [0.8.1] - 2026-10-05

### Added

- `detect` prints `problem:` lines too, and `detect --json` and
  `detect.json` have a new last key `problems`, an array of the problem
  texts; in `detect.json` it also holds the files a parser could not read ([#37]).

### Fixed

- An input that cannot be opened, including a missing path, an archive
  that is not readable, an archive inside a directory that cannot be
  traversed, an input directory that cannot be listed and an unreadable
  `manifest.jsonl`, now prints `error: <path>: <reason>` with the OS
  reason in lower case (`no such file or directory`, `permission denied`)
  and exits 2 under `detect`, `timeline` and `inventory`. Before, it
  printed only the path, or a Python traceback for permission errors. A
  corrupt or truncated archive prints `error: <path>: cannot extract:
  <reason>` instead of a traceback, and the extracted work directory is
  removed on every such error ([#37]).
- A directory inside a loose tree that cannot be listed is now a
  `problem:` line instead of being skipped silently ([#37]).
- A manifest row whose file is absent from the extracted collection is now
  one `problem:` line, `<original path>: missing from the collection` ([#37]).
- Problem lines and the `collection.json unreadable` note name the path
  once: `<path>: permission denied` instead of
  `<path>: [Errno 13] Permission denied: '<path>'`. The Continue and Codex
  `parser: unreadable ...` system rows carry only the reason, since
  `source_file` names the file ([#37]).

## [0.8.0] - 2026-10-04

### Added

- `timeline --since WHEN` and `--until WHEN` keep only the rows inside a
  UTC time window, `--keep-undated` also keeps rows without a timestamp,
  and `--match REGEX` (repeatable, `-i` for case-insensitive) keeps rows
  whose `text` matches, with the paired tool call or result. `WHEN` is an
  ISO 8601 date or time (a space may replace the `T`, and an offset may
  follow after a space), a year or month, an epoch number, `today`,
  `yesterday`, `now`, or a relative time such as `45m`, `36h`, `3d`, `2w`,
  `6mo`, `1y`. A value names a period to its last written unit, so
  `--since 2026-10-01 --until 2026-10-01` is that whole day. The resolved
  window and the dropped-row counts are printed. `sessions.jsonl` is
  summarised from the kept rows.
- `python-dateutil` is a new required dependency, used for `--since` and
  `--until`; reinstall with `pip install -r requirements.txt`.
- The [analyzer README](README.md) has recipes for filtering a written timeline by time
  with jq, DuckDB, Python and PowerShell.

### Changed

- `timeline` writes `timeline.jsonl` and `sessions.jsonl` instead of
  `timeline.csv` and `sessions.csv`: one JSON object per line, UTF-8, LF
  line ends, every field present in the old column order, `""` for no
  value. Interface change: `source_line`, `user_turns`, `assistant_turns`
  and `tool_calls` are JSON integers, and `models` is an array of strings
  instead of a space-separated string. Field names are unchanged.
- The `text` field keeps the event's line breaks and indentation, so tool
  output, diffs and multi-line prompts read as they were written; only
  leading and trailing whitespace is removed. Before, whitespace runs were
  collapsed to one space.
- The [analyzer README](README.md) has a section on reading and searching large JSONL
  timelines with jq, grep, DuckDB, Python and PowerShell.

### Removed

- `--max-text-length`. `text` is always written in full; cut it while
  reading, for example with `.text[0:200]` in jq.
- The `shell-history` catalog agent, following collector 1.7.0, which no
  longer collects shell history. Loose input no longer attributes
  `.bash_history`, `.zsh_history` and the other shell history files to an
  agent.
- The `shared|.env` and `project|.env` catalog entries, following collector
  1.7.0. Loose input no longer attributes a home or project `.env` file to
  `shared` or `project`.

## [0.7.0] - 2026-10-04

### Added

- Claude Code: sessions and `history.jsonl` in a config home moved with
  `CLAUDE_CONFIG_DIR` to a `.claude-<name>` directory (such as
  `~/.claude-work`) are parsed, and the bundled catalog copy detects
  them; `~/.claude-code-router` and other `.claude-` tools are not.
- Claude Code: a tool result stored as a `<persisted-output>` stub now
  carries the full output from the session's `tool-results/*.txt` file;
  when the file is missing, the stub is kept with a
  `[persisted output not found: ...]` note.
- Claude Code: each subagent transcript opens with a `system` row
  `subagent <agent id> of <session id>`.
- Claude Code: `session title:` rows for `ai-title`, `custom-title` and
  `agent-name` records, `cwd changed:` rows for `relocated` records (later
  rows take the new `project_path`), `hook:` rows for hook system messages
  and `edited file:` rows for `edited_text_file` attachments (the path
  only, not the snippet).

### Changed

- Claude Code: the Bash `tool_use` text is the command the model sent,
  with its `cd <dir> &&` prefix, instead of the normalised one.
- Claude Code: other injected context (`isMeta` records) starts with
  `context:`, and `system` records without `content` (`api_error`,
  `memory_saved`, ...) show their fields as JSON after the subtype.
- Open Interpreter rollouts are read by the same code as Codex CLI's, so
  every Codex CLI change below applies to them too.
- Codex CLI: a rollout that holds an ancestor's `session_meta` (a copied
  fork) keeps the file's own session id, project and branch; the ancestor's
  record is a `system` row `copied from ancestor: ...`, and a fork gets a
  `forked from <id>` row.
- Codex CLI: a non-zero exit code from a command's `item_completed` record
  prefixes that call's `tool_result` text as `[exit N]`.
- Codex CLI: a subagent rollout starts with a `system` row
  `subagent <id> of <parent id>` (with its agent path and role), and its
  first prompt, the task from the parent, is a `system` row
  `subagent task: ...` instead of `user`. Messages copied from the parent
  (`inherited_user_message`) are no longer repeated in the subagent's rows.

### Fixed

- Claude Code: prompts typed while a turn was running and delivered as
  `queued_command` attachments are now `user` rows; they were missing.
  The `enqueue` that repeated a delivered prompt's text is now
  `prompt queued: delivered at line N`, keeping the time it was typed;
  an `enqueue` with no delivery in the file is still
  `queue enqueue: <prompt>`.
- Claude Code: a subagent's task, task notifications, slash commands and
  their output, peer and coordinator messages, interruption markers and
  compaction summaries were `user` rows; they are now `system` rows with
  a label (`subagent task:`, `task notification:`, `slash command:`,
  `command output:`, `peer message:`, `coordinator message:`,
  `interrupted:`, `compaction summary:`).
- Claude Code: local API errors (model `<synthetic>`) were `assistant`
  rows; they are now `system` rows `api error: <status> <error>: <text>`.
- Claude Code: empty thinking blocks (signature only) no longer produce
  `[redacted]` thinking rows; only `redacted_thinking` blocks do.
- Claude Code: `pr-link` rows, re-written on every metadata flush, appear
  once per session and URL, and with the session's project and branch,
  like the queue rows.
- Claude Code: tool results that list tools (`tool_reference` blocks) show
  the tool names instead of empty text.
- Codex CLI: user-role messages the harness injects (environment context,
  AGENTS.md and skill instructions, subagent notifications, user shell
  commands) were `user` rows; they are now `system` rows
  `context: <kind>: ...`, by content kind where the rollout records one
  (current releases) and otherwise by the harness's own wrapper around the
  block (`<environment_context>`, `# AGENTS.md instructions`, `<skill>`
  and others), so `user` rows and `user_turns` count only what the person
  typed. A tag typed inside a prompt does not change its type.
- Codex CLI: compaction summaries, messages between agents
  (`inter_agent_communication`, `agent_message`), image generation
  prompts, tool searches, realtime voice transcripts, aborted and
  rolled-back turns, and `item_completed` turn items that no other record
  carries (web searches inside code-mode calls, MCP and dynamic tool calls,
  plans) were dropped; they now produce rows.
- Codex CLI: a reverted thread's rollout
  (`rollout-<time>-<thread id>_<rollout id>.jsonl`) cut before its
  `session_meta` took the rollout id as session id; it now takes the
  thread id.
- Codex CLI: a reasoning item with no summary text was a `thinking` row
  with empty text under `--include-thinking`; it is now skipped.

## [0.6.0] - 2026-10-04

### Added

- Muse Code parser (`muse-code`): session logs under
  `.local/share/muse/sessions/` and their subagent logs (user prompts,
  assistant replies, tool calls and results, approval requests and
  decisions, failed runs; reasoning summaries with `--include-thinking`),
  and the `tui-history.jsonl` prompt history.
- The catalog copy detects `muse-code` (Meta's Muse Code CLI).

### Changed

- Minimum Python raised from 3.9 to 3.10.

### Fixed

- OpenClaw: a `transcript_events` row whose `event_json` is valid JSON
  but not an object (such as `null`) no longer stops the parser with
  `UnboundLocalError`; it becomes a `system` row, "event seq N
  unreadable: not a JSON object", and the session's later events are
  still read.

## [0.5.0] - 2026-10-04

### Added

- `inventory` command: merges the saved stdout of collector 1.6.0
  `--inventory` / `-Inventory` runs (files, or directories of files) into
  one CSV, `fleet-inventory.csv` unless `-o FILE` is given.
- New CSV interface, `fleet-inventory.csv`, columns `host`, `collector`,
  `mode`, `at`, `user`, `agent`, `files`, `bytes`, `first`, `last`,
  `projects`, `evidence`; times normalised to UTC with milliseconds. A host
  with no agents gives one row with the agent columns empty.
- Console junk lines in a capture are skipped and counted on stderr.
- A per-agent rollup on stdout after the CSV: hosts, users and latest
  `last`.
- The catalog copy carries collector 1.5.0's `DOCKER_VOLUMES` table; the
  reader keeps those lines in their own list instead of the secret list.

### Changed

- The [README](README.md) says the `live` pseudo-agent appears only in collections made
  by collectors before 1.6.0, which removed the live snapshot.

## [0.4.0] - 2026-10-04

### Added

- Transcript parsers for fourteen more agents: `tabby`, `openhands`,
  `shellgpt`, `pi`, `little-coder`, `letta`, `hermes`, `agent-zero`,
  `open-interpreter`, `openclaw`, `nanobot`, `cody`, `twinny` and `pearai`,
  for thirty parsed agents in all. little-coder and Letta Code sessions are
  read with the pi parser's reader, and Open Interpreter rollouts with the
  Codex one.
- `reads_agents` routing: a parser can name other catalog agents whose files
  it is also offered. Cody and Twinny use it to read their rows of the
  `state.vscdb` that the catalog attributes to `vscode` or to a fork
  (`cursor`, `windsurf`, `pearai`, `kiro`, `antigravity`); the rows come out
  under `cody` or `twinny`, and `--agent cody` selects them.
- `agent_analyzer/vscode_state.py`, a helper that reads one extension's
  global state out of a VS Code family `state.vscdb` through
  `sqlite_util`, never reading `secret://` rows.
- Detection of the fifteen agents added in collector 1.4.0: `pearai`,
  `cody`, `twinny`, `tabby`, `open-interpreter`, `openhands`, `pi`,
  `little-coder`, `letta`, `hermes`, `openclaw`, `nanobot`, `agent-zero`,
  `shellgpt` and `local-deep-research`, from the regenerated catalog copy.

### Changed

- The Codex parser now also reads archived rollouts under
  `archived_sessions/` and zstd-compressed `.jsonl.zst` rollouts (needs
  `zstandard`; without it each compressed rollout is one `system` row). Its
  rollout reader is now the reusable `RolloutParser` base class.

## [0.3.1] - 2026-10-04

### Fixed

- The `timeline` summary no longer lists `project` among the agents that
  were detected but not parsed.

## [0.3.0] - 2026-10-03

### Added

- Transcript parsers for Gemini CLI, Qwen Code, Kiro (Amazon Q Developer CLI
  conversations), Crush, Goose, Zed, VS Code chat sessions, Continue, Aider,
  OpenCode, Kilo Code, Cline and Roo Code, for sixteen parsed agents in all.
- Dependency on the `zstandard` package for Zed threads; without it each Zed
  thread becomes one undecodable `system` row and everything else runs.

### Changed

- Files the collector found inside a discovered repository (agent `project`
  in the manifest) are offered to every parser, so a repository's
  `.crush/crush.db` and `.aider.*` files are parsed and their rows carry the
  real agent. `--agent` filters on that agent, so `--agent aider` includes
  repository-level Aider files.
- `detect` no longer reports `project` as a parsed agent.

## [0.2.0] - 2026-10-03

### Added

- Antigravity CLI parser for its SQLite conversation databases, decoded from
  the protobuf schemas embedded in the shipped binary. SQLite stores are read
  from a copy taken with their WAL and SHM sidecars, so the evidence copy is
  never opened and uncheckpointed rows are kept.
- Detection of the catalog entries added in collectors 1.2.0 and 1.3.0.

### Changed

- `timeline.csv`: the `summary` column is renamed `text`, in the same
  position, and holds the event's full text by default.
- `--max-text-length N` replaces `--summary-length N` and defaults to `0`,
  no cut; the old default cut at 400 characters.
- In loose mode a nested catalog entry claims its subtree, as in the
  collectors, so Antigravity CLI files under `~/.gemini` are attributed to
  `antigravity`.

## [0.1.0] - 2026-10-03

### Added

- `detect`, `timeline` and `catalog` commands, reading a collector archive,
  an extracted collection, or a loose directory such as a mounted image, a
  copied home or a single agent directory.
- Detection of every agent in the collectors' catalog. Host, user and agent
  come from the manifest when present; for loose input they are inferred
  from paths and marked as inferred.
- Parsers for Claude Code (session transcripts, subagent transcripts,
  `history.jsonl`) and Codex CLI (rollouts, `history.jsonl`).
- `timeline.csv` columns: `timestamp_utc`, `host`, `user`, `agent`,
  `session_id`, `project_path`, `git_branch`, `turn_type`, `model`,
  `tool_name`, `tool_use_id`, `summary`, `source_file`, `source_line`.
- `sessions.csv` columns: `host`, `user`, `agent`, `session_id`,
  `project_path`, `first_timestamp_utc`, `last_timestamp_utc`, `models`,
  `user_turns`, `assistant_turns`, `tool_calls`, `source_file`.
- Options `--host`, `--user`, `--work-dir`, `--keep-extracted`,
  `--summary-length` (default 400), `--include-thinking` and `--agent`;
  `detect --json` and `--files`; `catalog --agents`.

[Unreleased]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.13.0...HEAD
[0.13.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.12.0...analyzer-v0.13.0
[0.12.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.11.0...analyzer-v0.12.0
[0.11.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.10.0...analyzer-v0.11.0
[0.10.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.9.0...analyzer-v0.10.0
[0.9.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.8.1...analyzer-v0.9.0
[0.8.1]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.8.0...analyzer-v0.8.1
[0.8.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.7.0...analyzer-v0.8.0
[0.7.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.6.0...analyzer-v0.7.0
[0.6.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.5.0...analyzer-v0.6.0
[0.5.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.4.0...analyzer-v0.5.0
[0.4.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.3.1...analyzer-v0.4.0
[0.3.1]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.3.0...analyzer-v0.3.1
[0.3.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.2.0...analyzer-v0.3.0
[0.2.0]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.1.0...analyzer-v0.2.0
[0.1.0]: https://github.com/seanthegeek/doubleagent/releases/tag/analyzer-v0.1.0

[#122]: https://github.com/seanthegeek/doubleagent/issues/122
[#125]: https://github.com/seanthegeek/doubleagent/issues/125
[#121]: https://github.com/seanthegeek/doubleagent/issues/121
[#119]: https://github.com/seanthegeek/doubleagent/issues/119
[#118]: https://github.com/seanthegeek/doubleagent/issues/118
[#117]: https://github.com/seanthegeek/doubleagent/issues/117
[#113]: https://github.com/seanthegeek/doubleagent/issues/113
[#112]: https://github.com/seanthegeek/doubleagent/issues/112
[#104]: https://github.com/seanthegeek/doubleagent/issues/104
[#103]: https://github.com/seanthegeek/doubleagent/issues/103
[#97]: https://github.com/seanthegeek/doubleagent/issues/97
[#96]: https://github.com/seanthegeek/doubleagent/issues/96
[#93]: https://github.com/seanthegeek/doubleagent/issues/93
[#92]: https://github.com/seanthegeek/doubleagent/issues/92
[#90]: https://github.com/seanthegeek/doubleagent/issues/90
[#89]: https://github.com/seanthegeek/doubleagent/issues/89
[#88]: https://github.com/seanthegeek/doubleagent/issues/88
[#86]: https://github.com/seanthegeek/doubleagent/issues/86
[#85]: https://github.com/seanthegeek/doubleagent/issues/85
[#83]: https://github.com/seanthegeek/doubleagent/issues/83
[#81]: https://github.com/seanthegeek/doubleagent/issues/81
[#80]: https://github.com/seanthegeek/doubleagent/issues/80
[#76]: https://github.com/seanthegeek/doubleagent/issues/76
[#75]: https://github.com/seanthegeek/doubleagent/issues/75
[#73]: https://github.com/seanthegeek/doubleagent/issues/73
[#64]: https://github.com/seanthegeek/doubleagent/issues/64
[#48]: https://github.com/seanthegeek/doubleagent/issues/48
[#47]: https://github.com/seanthegeek/doubleagent/issues/47
[#45]: https://github.com/seanthegeek/doubleagent/issues/45
[#44]: https://github.com/seanthegeek/doubleagent/issues/44
[#43]: https://github.com/seanthegeek/doubleagent/issues/43
[#41]: https://github.com/seanthegeek/doubleagent/issues/41
[#37]: https://github.com/seanthegeek/doubleagent/issues/37
[#34]: https://github.com/seanthegeek/doubleagent/issues/34
