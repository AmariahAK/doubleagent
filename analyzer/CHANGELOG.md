# Changelog

All notable changes to the analyzer are recorded here. The version is
printed by `--version`. Changes to the `timeline.jsonl` and
`sessions.jsonl` fields (`timeline.csv` and `sessions.csv` columns up to
0.7.0) are called out, since they are interfaces.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.12.0] - 2026-10-13

### Added

- The bundled catalog copy detects the Antigravity CLI's file secret
  store `plugin-secrets.json` (`.config/antigravity`,
  `Library/Application Support/antigravity`, `AppData/Roaming/antigravity`)
  as `antigravity` ([#90]).
- The bundled catalog copy follows collector 1.12.0: the Antigravity
  desktop app's Electron user-data directory
  (`Library/Application Support/Antigravity`, `.config/Antigravity`,
  `AppData/Roaming/Antigravity`) and its macOS logs directory
  `Library/Logs/Antigravity` are detected as `antigravity` ([#83]).
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

### Changed

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

### Fixed

- `tools/proto_descriptors.py extract` no longer fails with a `TypeError`
  on Mach-O binaries such as the macOS builds of `agy` and the Antigravity
  desktop app's language server ([#86]).
- The `antigravity` parser reads the path of a `code_action` step that
  deletes a file: `ActionSpecDeleteFile` keeps the path in field 1, where
  the parser had read field 2, so the `tool_result` row lost the path or
  the step could not be decoded ([#88]).

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

[Unreleased]: https://github.com/seanthegeek/doubleagent/compare/analyzer-v0.12.0...HEAD
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
