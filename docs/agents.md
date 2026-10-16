# Agents

Every agent in the collectors' catalog, in alphabetical order of its
catalog name, with what DoubleAgent does with its files: whether the
analyzer parses them, what the parser or the collector was validated
against, and where the research is. The status is one of three words:

- `parsed`: a parser reads the agent's files. Validated against gives
  the evidence class in a few words (source, bundle or real installs,
  with the platforms) and the agent's subsection under
  [Parser details](#parser-details) lists the files it reads and the full
  evidence its paths and record shapes were checked against, with the
  real installs (platform, version, date) on which they were seen.
- `backlog`: transcripts or other parseable records are collected and a
  parser is wanted. Cursor and Windsurf are blocked on format research:
  their record formats are not known well enough to write one.
- `collected`: the files are collected and detected, but hold nothing to
  parse: a token store, configuration only, or a surface that left no
  local transcript on the installs checked.

For a `backlog` or `collected` row, Validated against gives the
evidence level of the collector research, and the agent's subsection
under [Collected files](#collected-files) lists what the collector
gathers. Notes links the research documents and the open parser
issues, then gives the reason when the status needs one in a short
clause; where that clause was shortened, the subsection repeats it in
full. The agent name in each row links to its subsection.

The `collected` rows are the `NO_TRANSCRIPTS` set in
`analyzer/doubleagent/parsers/__init__.py`, which `timeline` reports as
`collected only` on its `agents:` line and in the `collected_only` key
of [`inventory.json`](../analyzer/docs/output.md#inventoryjson) rather
than as detected but not parsed; a test keeps the set and the table
equal.

| Agent | Status | Validated against | Notes |
| --- | --- | --- | --- |
| [`agent-zero`](#agent-zero) | parsed | source; fixture only | [collector research](../collectors/research/agent-zero.md); [analyzer research](../analyzer/research/agent-zero.md) |
| [`aider`](#aider) | parsed | source; fixture only | [collector research](../collectors/research/aider.md); [analyzer research](../analyzer/research/aider.md) |
| [`amp`](#amp) | backlog | Shipped binary strings, docs | [collector research](../collectors/research/amp.md); [issue 53](https://github.com/seanthegeek/doubleagent/issues/53); prompt history and thread logs; full threads are server-side |
| [`antigravity`](#antigravity) | parsed | real installs: WSL, macOS, Ubuntu, Windows (October 2026) | [collector research](../collectors/research/antigravity.md); [analyzer research](../analyzer/research/antigravity.md) |
| [`augment`](#augment) | backlog | Shipped bundle, docs | [collector research](../collectors/research/augment.md); [issue 55](https://github.com/seanthegeek/doubleagent/issues/55); full conversations in `.augment/sessions/*.json` and a prompt history |
| [`autogen-studio`](#autogen-studio) | backlog | Source | [collector research](../collectors/research/autogen-studio.md); [issue 69](https://github.com/seanthegeek/doubleagent/issues/69); SQLite `autogen04203.db` with the `message`, `session` and `run` tables |
| [`camel-ai`](#camel-ai) | collected | Source | [collector research](../collectors/research/camel-ai.md); no transcripts under the home; history is in the working directory |
| [`chatgpt-desktop`](#chatgpt-desktop) | collected | Write-ups and press; real installs on Windows and macOS, October 2026 | [collector research](../collectors/research/chatgpt-desktop.md); [issue 49](https://github.com/seanthegeek/doubleagent/issues/49); a chat left only an index entry; Codex threads parse as `codex-cli` |
| [`claude-code`](#claude-code) | parsed | real installs: Linux (WSL2), macOS (October 2026) | [collector research](../collectors/research/claude-code.md); [analyzer research](../analyzer/research/claude-code.md) |
| [`claude-desktop`](#claude-desktop) | parsed | real installs: Windows (MSIX), Linux, macOS (October 2026) | [collector research](../collectors/research/claude-desktop.md); [analyzer research](../analyzer/research/claude-desktop.md) |
| [`cline`](#cline) | parsed | source; fixture only | [collector research](../collectors/research/cline.md); [analyzer research](../analyzer/research/cline.md) |
| [`codex-cli`](#codex-cli) | parsed | real installs: Windows, macOS, Ubuntu (October 2026) | [collector research](../collectors/research/codex-cli.md); [analyzer research](../analyzer/research/codex-cli.md) |
| [`cody`](#cody) | parsed | source; fixture only | [collector research](../collectors/research/cody.md); [analyzer research](../analyzer/research/cody.md) |
| [`continue`](#continue) | parsed | source; fixture only | [collector research](../collectors/research/continue.md); [analyzer research](../analyzer/research/continue.md) |
| [`copilot`](#copilot) | collected | Source (the vendored language server) | [collector research](../collectors/research/copilot.md); an OAuth token store with no transcripts; Copilot Chat is parsed as `vscode` |
| [`copilot-cli`](#copilot-cli) | parsed | bundle and real install: macOS (October 2026) | [collector research](../collectors/research/copilot-cli.md); [analyzer research](../analyzer/research/copilot-cli.md); [issue 132](https://github.com/seanthegeek/doubleagent/issues/132); the legacy flat `session-state/<id>.jsonl` transcript is not parsed yet |
| [`crewai`](#crewai) | backlog | Source, appdirs source | [collector research](../collectors/research/crewai.md); [issue 140](https://github.com/seanthegeek/doubleagent/issues/140); `latest_kickoff_task_outputs.db` holds every task's output with its messages |
| [`crush`](#crush) | parsed | source; fixture only | [collector research](../collectors/research/crush.md); [analyzer research](../analyzer/research/crush.md) |
| [`cursor`](#cursor) | backlog | Shipped Agent CLI bundle, docs, forum, write-ups | [collector research](../collectors/research/cursor.md); [issue 51](https://github.com/seanthegeek/doubleagent/issues/51); blocked on format research: the `state.vscdb` key layout varies by version |
| [`dify`](#dify) | backlog | Source | [collector research](../collectors/research/dify.md); [issue 142](https://github.com/seanthegeek/doubleagent/issues/142); sandbox `shellctl.db` and job logs hold shell jobs; chats in PostgreSQL |
| [`factory-droid`](#factory-droid) | backlog | Shipped binary strings, docs | [collector research](../collectors/research/factory-droid.md); [issue 54](https://github.com/seanthegeek/doubleagent/issues/54); JSONL session transcripts under `.factory/sessions` and a prompt history |
| [`flowise`](#flowise) | backlog | Source | [collector research](../collectors/research/flowise.md); [issue 68](https://github.com/seanthegeek/doubleagent/issues/68); `database.sqlite` with `chat_message` (tool use and agent reasoning) and `execution` |
| [`gemini-cli`](#gemini-cli) | parsed | source; fixture only | [collector research](../collectors/research/gemini-cli.md); [analyzer research](../analyzer/research/gemini-cli.md) |
| [`goose`](#goose) | parsed | source; fixture only | [collector research](../collectors/research/goose.md); [analyzer research](../analyzer/research/goose.md) |
| [`hermes`](#hermes) | parsed | source; fixture only | [collector research](../collectors/research/hermes.md); [analyzer research](../analyzer/research/hermes.md) |
| [`kilo-code`](#kilo-code) | parsed | source; fixture only | [collector research](../collectors/research/kilo-code.md); [analyzer research](../analyzer/research/kilo-code.md) |
| [`kiro`](#kiro) | parsed | source; fixture only | [collector research](../collectors/research/kiro.md); [analyzer research](../analyzer/research/kiro.md) |
| [`langflow`](#langflow) | backlog | Source, platformdirs source; Desktop from docs only | [collector research](../collectors/research/langflow.md); [issue 141](https://github.com/seanthegeek/doubleagent/issues/141); Desktop's `database.db`; the server's `langflow.db` is not collected |
| [`letta`](#letta) | parsed | source; fixture only | [collector research](../collectors/research/letta.md); [analyzer research](../analyzer/research/letta.md) |
| [`little-coder`](#little-coder) | parsed | source; fixture only | [collector research](../collectors/research/little-coder.md); [analyzer research](../analyzer/research/little-coder.md) |
| [`local-deep-research`](#local-deep-research) | backlog | Source, platformdirs source | [collector research](../collectors/research/local-deep-research.md); [issue 56](https://github.com/seanthegeek/doubleagent/issues/56); history and chat in SQLCipher databases keyed from the login password |
| [`metagpt`](#metagpt) | collected | Source | [collector research](../collectors/research/metagpt.md); configuration only; its workspace and `team.json` are under the working directory |
| [`muse-code`](#muse-code) | parsed | binary strings and real install: Linux (October 2026) | [collector research](../collectors/research/muse-code.md); [analyzer research](../analyzer/research/muse-code.md) |
| [`n8n`](#n8n) | backlog | Source | [collector research](../collectors/research/n8n.md); [issue 67](https://github.com/seanthegeek/doubleagent/issues/67); `database.sqlite` executions and chats, and the gateway's tool-call log |
| [`nanobot`](#nanobot) | parsed | source; fixture only | [collector research](../collectors/research/nanobot.md); [analyzer research](../analyzer/research/nanobot.md) |
| [`ollama`](#ollama) | parsed | source; fixture only | [collector research](../collectors/research/ollama.md); [analyzer research](../analyzer/research/ollama.md) |
| [`open-interpreter`](#open-interpreter) | parsed | source; fixture only | [collector research](../collectors/research/open-interpreter.md); [analyzer research](../analyzer/research/open-interpreter.md); [issue 70](https://github.com/seanthegeek/doubleagent/issues/70); the legacy Python tool's `conversations/*.json` files are collected but not parsed yet |
| [`openclaw`](#openclaw) | parsed | source; fixture only | [collector research](../collectors/research/openclaw.md); [analyzer research](../analyzer/research/openclaw.md) |
| [`opencode`](#opencode) | parsed | source; fixture only | [collector research](../collectors/research/opencode.md); [analyzer research](../analyzer/research/opencode.md); [issue 139](https://github.com/seanthegeek/doubleagent/issues/139); undecodable message parts and records are counted, not carried in full |
| [`openhands`](#openhands) | parsed | source; fixture only | [collector research](../collectors/research/openhands.md); [analyzer research](../analyzer/research/openhands.md) |
| [`pearai`](#pearai) | parsed | source; fixture only | [collector research](../collectors/research/pearai.md); [analyzer research](../analyzer/research/pearai.md) |
| [`pi`](#pi) | parsed | source; fixture only | [collector research](../collectors/research/pi.md); [analyzer research](../analyzer/research/pi.md) |
| [`pydantic-clai`](#pydantic-clai) | backlog | Source, PyPI wheel | [collector research](../collectors/research/pydantic-clai.md); [issue 66](https://github.com/seanthegeek/doubleagent/issues/66); CLAI 2.0 `sessions.db` conversations and the prompt histories |
| [`qwen-code`](#qwen-code) | parsed | source; fixture only | [collector research](../collectors/research/qwen-code.md); [analyzer research](../analyzer/research/qwen-code.md) |
| [`roo-code`](#roo-code) | parsed | source; fixture only | [collector research](../collectors/research/roo-code.md); [analyzer research](../analyzer/research/roo-code.md) |
| [`shared`](#shared) | collected | Derived from the per-agent documents | [collector research](../collectors/research/shared.md); cross-agent instruction and skill directories with no transcripts |
| [`shellgpt`](#shellgpt) | parsed | source; fixture only | [collector research](../collectors/research/shellgpt.md); [analyzer research](../analyzer/research/shellgpt.md) |
| [`tabby`](#tabby) | parsed | source; fixture only | [collector research](../collectors/research/tabby.md); [analyzer research](../analyzer/research/tabby.md) |
| [`twinny`](#twinny) | parsed | source; fixture only | [collector research](../collectors/research/twinny.md); [analyzer research](../analyzer/research/twinny.md) |
| [`vscode`](#vscode) | parsed | source; fixture only | [collector research](../collectors/research/vscode.md); [analyzer research](../analyzer/research/vscode.md) |
| [`windsurf`](#windsurf) | backlog | Official docs, community write-ups | [collector research](../collectors/research/windsurf.md); [issue 52](https://github.com/seanthegeek/doubleagent/issues/52); blocked on format research: Cascade's `.pb` files have no published schema |
| [`zed`](#zed) | parsed | source; fixture only | [collector research](../collectors/research/zed.md); [analyzer research](../analyzer/research/zed.md) |

Files that are not transcripts, such as skills and configuration files,
are detected but not parsed.

## Parser details

One subsection per `parsed` agent, in alphabetical order: the files
the parser reads, and the evidence its paths and record shapes were
checked against, with the real installs (platform, version, date) on
which they were seen and "fixture only" for what rests on source or
a bundle alone.

### `agent-zero`

Files read: `usr/chats/<ctxid>/chat.json` (UI log for timestamps, each
agent's history for full text and model, `messages/<n>.txt` for long tool
results; history-only turns without timestamps when the log was trimmed at
1000 items) under `agent-zero`, `agent-zero/<instance>` or
`Desktop/agent-zero`, also the legacy `chats/<ctxid>.json` and
`tmp/chats`; project path is the container path `/a0/usr/projects/<name>`.

Validated against: Source at e3051fb, synthetic fixture.

### `aider`

Files read: `.aider.chat.history.md`, `.aider.input.history`,
`.aider.llm.history`, in a home or a repository (a project directory the
collector gathered); the input and LLM histories are secondary sources of
the chat history; times are host local time, emitted as if UTC.

Validated against: Source at 5dc9490, synthetic fixture.

### `antigravity`

Files read: `conversations/*.db` (SQLite of protobuf steps, with WAL
sidecars when present) and `conversation_summaries.db` under each of the
four data directories `.gemini/antigravity-cli` (the CLI),
`.gemini/antigravity` (the desktop app 2.x), `.gemini/antigravity-ide`
(the separately installed IDE) and `.gemini/antigravity-backup` (the app's
migration backup); `.gemini/antigravity-cli/history.jsonl` (CLI only; a
row's `session_id` is set when the line has `conversationId`, which CLI
1.3.x writes). The session start row names `source=<trajectory source>`
(`cli` for the CLI, `cascade_client` for the desktop app) and
`data_dir=<directory>`. Each grant in a step's `steps.permissions` blob is
a `system` row after the step's rows with its `tool_name` and
`tool_use_id`, `permission grant: action=<action> target=<target>
allow=<bool> scope=<scope>` (`<bool>` is `true` or `false`) or, for a file
access entry, `permission grant: path=<path> is_directory=<bool>
allow=<bool> scope=<scope>`. The standing permission files
`.gemini/config/config.json`, `.gemini/config/projects/*.json`,
`.gemini/config/sidecars/*/sidecar.json` and
`.gemini/antigravity-cli/settings.json` give one `permission setting:
<key>=<value> (from <file>, file mtime)` row per allow-list entry, sidecar
access grant, migration or sandbox flag and trusted workspace, at the
file's modification time; their other keys, `mcp_config.json` and plugin
`token.json` files are not read. The brain mirror under each data
directory, `brain/<uuid>/.system_generated/logs/` (one copy per
conversation: `transcript_full.jsonl`, else its
`chunks/transcript_full/*.jsonl` concatenated, else the shortened
`transcript.jsonl`, else its chunks), gives `user`, `assistant`,
`tool_use`, `tool_result`, `thinking` and `system` rows rendered as the
database's, with the line's `created_at`, the directory's `<uuid>` as
`session_id` and no `project_path`; a secondary source paired within 600
seconds, so a conversation whose database is gone is still in the
timeline. The brain directory's `steps/`, `messages/` and `tasks/` files,
`annotations/*.pbtxt` and the app's FTS5 search table are not read.

Validated against: Protobuf descriptors extracted from the shipped `agy`
binary (Linux x86-64) plus a real install (WSL), October 2026; a macOS
real install of CLI 1.2.16 and the desktop app 2.23.0, 2026-10-13, whose
embedded descriptors match the parser's tables; an Ubuntu 26.04.1
(aarch64) real install of CLI 1.3.4 and the desktop app 2.23.1,
2026-10-13; a Windows 11 ARM64 (build 26300) real install of CLI 1.3.5 and
the desktop app 2.23.1, 2026-10-14; the IDE and backup directories fixture
only (bundle-derived); the permission rows' file names and key names seen
on the macOS, Ubuntu and Windows installs, their values (scopes, actions,
grant patterns) fixture only; the brain mirror's file names and line keys
seen on the macOS, Ubuntu and Windows installs, its value forms from the
format description embedded in `agy` 1.3.6 (macOS arm64), the
`tool_calls[]` element shape fixture only.

### `claude-code`

Files read: `.claude/projects/<slug>/<session>.jsonl`, subagent
transcripts under the session directory (each opens with a `subagent <id>
of <session>` row), `tool-results/*.txt` in the session directory when a
result's `<persisted-output>` stub names it, `.claude/history.jsonl`, and
the per-process registry `.claude/sessions/<pid>.json` (one `system` row
per running process at `startedAt`: `claude-code process <pid> <kind>
status=<status> entrypoint=<entrypoint> bridge=<bridgeSessionId or none>
host_session=<hostSessionId or none>`, a `bridge=` value meaning the
process was under Remote Control when the collector ran; the
`<pid>.<sha256>.key` sibling is never read); a 2.1.295
`permissionDecision` on a tool-result line is a `system` row after its
`tool_result` rows, `permission decision: <decision> source=<source>
reason=<reasonType>`, joined on the first result's `tool_use_id`;
`permission mode: <mode>` at a session's first `permission-mode` record or
`permissionMode` prompt key and `permission mode: <old> -> <new>` on each
change, `model: <id>` at the first assistant reply and `model: <old> ->
<new>` on each change (with ` requested=<requestedModel>` when it
differs), each subagent file tracking its own; standing permission
settings, one `system` row per entry at the file's modification time,
`permission setting: <key>=<value> (from <file>, file mtime)`, from
`permissions.allow`, `deny`, `ask`, `additionalDirectories`, `defaultMode`
and `disableBypassPermissionsMode` in `.claude/settings.json` and
`.claude/settings.local.json` (the user's, and a discovered project's with
`project_path` the project) and from `projects.<path>.allowedTools`,
`hasTrustDialogAccepted` and `hasClaudeMdExternalIncludesApproved` in
`.claude.json`, no other key of either file being read; the same files
under a `.claude-<name>` config home moved with `CLAUDE_CONFIG_DIR` (such
as `.claude-work/projects/...`).

Validated against: Real installs, Claude Code 2.1.286 to 2.1.289 on Linux
(WSL2) and 2.1.295 on macOS (launched from the Claude Desktop Code tab),
and the shipped 2.1.289 package strings, October 2026; the
`sessions/<pid>.json` registry and `permissionDecision` on 2.1.295
installs on Linux and macOS (2026-10-11), with no `bridgeSessionId`
observed (the `bridge=` value is fixture only); the `permission-mode`
record, the `permissionMode` prompt key, `requestedModel` and the `/model`
output text on a 2.1.296 install on macOS (2026-10-13, key names and enum
values only), the settings `permissions` keys and mode names from the
2.1.296 darwin-arm64 binary's strings, the settings and `.claude.json`
rows fixture only.

### `claude-desktop`

Files read: Under the app-data directory (`Library/Application
Support/Claude`, `.config/Claude`, `AppData/Roaming/Claude`,
`AppData/Local/Claude`, each also `-3p`, `AppData/Local/Claude-Data` and
its package-family child, and, for the MSIX build (MSIX, the Windows
packaged-app format),
`AppData/Local/Packages/Claude_*/LocalCache/Roaming/Claude` or
`AppData/Local/Packages/AnthropicPBC.Claude_*/LocalCache/Roaming/Claude`):
Cowork and Code-tab transcripts
`{local-agent-mode-sessions,claude-code-sessions}/<acct>/<org>/[agent/]<session
dir>/.claude/projects/<slug>/<cliSessionId>.jsonl` and their subagent
files, read with the `claude-code` reader, with `project_path` from the
session record's `userSelectedFolders[0]` (the JSONL `cwd` is a VM guest
path); `claude-code-sessions/<acct>/<org>/imported-staging/*.jsonl`; each
Cowork session's `audit.jsonl`, a secondary source read in full on every
run whether or not the session dir holds a transcript (every turn, an
`init` row, and permission requests, responses and auto-decisions and
`result` lines as `system` rows; the turns the transcript repeats are
dropped); session records `local_<uuid>.json` (one `system` row at
`createdAt`, on a Code-tab record ending with the persisted Remote Control
state `remote_control=<bool> bridges=<n> spawned_remotely=<bool>
steered_remotely=<bool>` and followed by a `remote control live at update
quit` row when `remoteControlLiveAtUpdateQuit.at` is set, on either kind
ending with `permission_mode=<permissionMode> effort=<effort>` and
followed by one `permission grant:` row per `alwaysAllowedReasons` and
`sessionPermissionUpdates` entry and per `chromePermissionMode`,
`chromeAllowedDomains`, `cuAllowedApps`, `cuGrantFlags` and
`cuFlagsGrantedAt` value, at `lastActivityAt` (else `createdAt`), the
first prompt as a `user` row (on a Cowork record always, with no
timestamp, a secondary source that drops when the transcript or the audit
log has the prompt; on a Code-tab record only when its
`~/.claude/projects` transcript, a `claude-code` file, was not collected),
a `session error:` row, and one `permission grant:` row per entry of the
Cowork grants `approvedToolNames`, `webFetchAllowedUrls`,
`egressAllowedDomains`, `userApprovedFileAccessPaths`, `enabledMcpTools`
and `fileDeleteApprovedMounts`); the audit log's `init` model as a `model:
<id>` row, and `model_refusal_fallback` lines as a `system` row of their
fields; `scheduled-tasks.json` (each task row ending
`permission_mode=<permissionMode> model=<model>`); `git-worktrees.json`;
`local-agent-mode-sessions/<acct>/<org>/remote-session-spaces.json` (one
`permission setting: entries.<sessionId>.folders=<folder> (from <file>,
file mtime)` row per folder granted to a remote Cowork session).

Validated against: App bundle 2.31226.1 (`app.asar`, read, not run); real
installs of 2.31226.1 for the Code-tab record and its transcript: MSIX
build (2026-10-10), Linux `.deb` (2026-10-11) and macOS (2026-10-11),
where every Remote Control flag was `false` or absent, so the `true`
values, the bridge count and the update-quit row are fixture only; Cowork
transcripts, `audit.jsonl`, imported transcripts and scheduled tasks
fixture only; the `permission grant:` rows fixture only (real installs
showed both grant lists empty).

### `cline`

Files read: `<editor>/User/globalStorage/saoudrizwan.claude-dev/` and
`.cline/data/`: `tasks/<id>/ui_messages.json` (preferred),
`api_conversation_history.json` (a fallback, only when `ui_messages.json`
is absent, since its texts wrap the prompt in tags the UI messages lack
and could not be paired with them; inherits the task start time),
`task_metadata.json`, `state/taskHistory.json`; SDK
`.cline/data/sessions/<id>/<id>.json` and `*.messages.json`,
`.cline/data/db/sessions.db`; `.cline/data/db/session-search.db` (a
secondary source: one `system` row per indexed session at its start, then
one row per message with no timestamp); the CLI's
`.cline/data/cache/user_input_history.jsonl` (a secondary source: one
`user` row per prompt, no session or project, only the last line
timestamped, since every rewrite stamps every line with its own time).

Validated against: Source at 39ff2359, synthetic fixture.

### `codex-cli`

Files read: `.codex/sessions/**/rollout-*.jsonl` and `archived_sessions/`,
also as `.jsonl.zst` (needs `zstandard`), `.codex/history.jsonl`,
`.codex/automations/*/automation.toml`, and the rollouts' SQLite
projections `.codex/state_5.sqlite` (`threads`: a thread record and the
first prompt) and `.codex/thread_history_1.sqlite` (`thread_turns`,
`thread_items`), secondary sources.

Validated against: Real install, Codex CLI, October 2026; Codex Desktop
0.162.0-alpha.17.2 inside the ChatGPT desktop app, Windows 11, October
2026; Codex CLI 0.162.1 (standalone installer) on Windows 11, October
2026; Codex Desktop 0.162.0-alpha.17.2 inside ChatGPT 26.1007.71326 and
Codex CLI 0.162.1 on macOS 26.6.2, October 2026; Codex CLI 0.162.1
(standalone installer) on Ubuntu 26.04.1, October 2026; archived and
`.zst` rollouts, subagent and fork records from source at 3e23877,
synthetic fixture; the `state_5.sqlite` and `thread_history_1.sqlite`
table and column names seen on the Windows 11 install, their row shapes
from source at 3e23877, synthetic fixture. User-role context (environment,
AGENTS.md, skills) is `system` by its content kind; a subagent row links
each spawned thread to its parent; each automation of the ChatGPT desktop
app is a `scheduled task:` row; turn items that no response item carries
become rows.

### `cody`

Files read: The `sourcegraph.cody-ai` row of a VS Code or fork
`User/globalStorage/state.vscdb` (its `cody-local-chatHistory-v2` member)
and the JetBrains file
`Cody-nodejs/[Data/]JetBrains-globalState/cody-local-chatHistory-v2`.
Every row of a chat carries the chat's creation time (its id); no project
path is recorded.

Validated against: Source at 8e20ac6c, synthetic fixture.

### `continue`

Files read: `.continue/sessions/<sessionId>.json` (timestamped from
`sessions/sessions.json` `dateCreated`; messages have no time of their
own), `.continue/dev_data/<schema>/chatInteraction.jsonl` and
`toolUsage.jsonl`.

Validated against: Source at 5522c6f, synthetic fixture.

### `copilot-cli`

Files read: Under `.copilot` (or the pre-XDG `.local/state/.copilot` and
`.config/.copilot`): `session-state/<id>/events.jsonl` (the event log;
tool calls, results and the permission requests and decisions joined on
`toolCallId`; `model:` rows from `session.model_change`; the runtime's
utility-model calls as `utility model <id>:` rows),
`session-state/<id>/workspace.yaml` (session name and metadata),
`permissions-config.json` and `settings.json` (`allowedUrls`,
`deniedUrls`; one `permission setting: ... (from <file>, file mtime)` row
per entry at the file's modification time), `logs/process-*.log` (the
sign-in line), and `sidebar-sessions-state/*.json` (a project-path join,
no rows). Secondary sources: `session-store.db` (SQLite with WAL sidecars;
`sessions`, `turns`, `session_files`, `session_refs`, `checkpoints`,
`forge_trajectory_events`; one-hour window, since a turn is stamped when
it ends), `session-state/<id>/rewind-file-snapshots/index.json` (each
turn's prompt and changed files; one-hour window) and
`command-history-state.json` (prompts with no time, session or cwd).

Validated against: Shipped bundle 1.0.98 (darwin-arm64 event schema, CLI
and runtime strings) and a real install on macOS, Copilot CLI 1.0.98,
October 2026, synthetic fixture; `forge_trajectory_events`, checkpoints,
references, denials, resumes and subagents fixture only.

### `crush`

Files read: `<project>/.crush/crush.db` (SQLite with WAL sidecars; reached
as a project artifact, or under a home when Crush ran in `~`),
`.local/share/crush/projects.json`, `AppData/Local/crush/projects.json`.

Validated against: Source at ca6ae26, synthetic fixture.

### `gemini-cli`

Files read: `.gemini/tmp/<slug>/chats/**/*.jsonl` (with `$set`, `$patch`
and `$rewindTo` replayed), legacy `chats/**/*.json`,
`tmp/<slug>/logs.json`, also under `.cache/.gemini`; project path from
`.project_root` or `projects.json`; `.gemini/trustedFolders.json`, one
`permission setting: trustedFolders.<path>=<value> (from <file>, file
mtime)` row per folder at the file's modification time with `project_path`
the folder; a gemini message's `model` as `model: <id>` at a session's
first and `model: <old> -> <new>` on each change; a tool call with status
`cancelled` or `awaiting_approval` is followed by `permission decision:
<status>`.

Validated against: Source at fb972b2, synthetic fixture.

### `goose`

Files read: `.local/share/goose/sessions/sessions.db` (SQLite with WAL
sidecars), legacy `sessions/*.jsonl`,
`.local/state/goose/logs/llm_request.*.jsonl`, `history.txt` (a secondary
source, no timestamp: matches on text alone), and the
`AppData/Roaming/Block/goose/data` equivalents.

Validated against: Source at 591edd4, synthetic fixture.

### `hermes`

Files read: `state.db` (SQLite with WAL sidecars; `sessions`, `messages`
and `session_model_usage`, rewound or compacted `active = 0` rows kept
with a `[rewound]` prefix) and two secondary sources, the quick snapshots
`state-snapshots/<id>/state.db` (read like `state.db` after a `state
snapshot <id>` row; collected only with `--full`) and the
`sessions/<id>.jsonl` diverts written when `state.db` was replaced under a
running process, under `.hermes`, `.hermes_<suffix>`,
`AppData/Local/hermes` and their `profiles/<name>/` homes.

Validated against: Source at 8b66a51, synthetic fixture.

### `kilo-code`

Files read: `.local/share/kilo/kilo*.db` and `opencode-*.db` plus the same
JSON trees under `.local/share/kilo` (OpenCode parser, Kilo paths), and
pre-migration VS Code tasks
`<globalStorage>/kilocode.kilo-code/tasks/<id>/api_conversation_history.json`.

Validated against: Source at 76bcfd4, synthetic fixture.

### `kiro`

Files read: Amazon Q CLI `data.sqlite3` (`conversations` and legacy
`history` tables) under `amazon-q/` or `kiro-cli/` in `.local/share`,
`Library/Application Support` or `AppData/Local`; `/save` exports (`.json`
with `conversation_id` and `history`). Kiro CLI `.kiro/sessions/` files
are not parsed until their format is confirmed.

Validated against: Source at 15cc8f3, synthetic fixture.

### `letta`

Files read: Letta Code
`.letta/lc-local-backend/conversations/<key>/messages.jsonl` (pi session
format), `.letta/transcripts/<agent>/<conversation>/transcript.jsonl`
(project path from `sessions.jsonl` by time, a heuristic; a secondary
source, read beside the conversation's `messages.jsonl` with a one-hour
window because each line is stamped at the end of its turn),
`.letta/sessions.jsonl`.

Validated against: Source at 77faf36, synthetic fixture.

### `little-coder`

Files read: `.pi/agent/little-coder-prompt-history.json` (prompts without
timestamps or sessions) and `.little-coder/checkpoints/<session file>/`
(one `system` row per session's pre-edit copies); its transcripts are pi
sessions, parsed as `pi`.

Validated against: Source at 89d4fa0, synthetic fixture.

### `muse-code`

Files read: `.local/share/muse/sessions/YYYY/MM/DD/<id>/session.jsonl` and
each subagent's `subagent/<id>/session.jsonl` (event envelopes with
microsecond `recorded_at`; tool calls and results joined on `call_id`;
approval requests and decisions as `system` rows; a subagent takes its
project path and branch from the parent log),
`.local/share/muse/tui-history.jsonl` (prompts without timestamps),
`.config/muse/trust.json` (one `permission setting:` row per trusted
project, at the file's modification time). The approval reviewer's
`approval-review/*.jsonl` (synthetic clock), `tool-outputs/` and the
SQLite indexes are not read.

Validated against: Shipped binary 1.4.2 strings, vendor skills and a real
install (Linux), October 2026, synthetic fixture.

### `nanobot`

Files read: `.nanobot*/sessions/<workspace-id>/<key>.jsonl` (project path
from the sibling `.workspace`), legacy `sessions/*.jsonl` and
`.migration-conflicts/`, and `memory/history.jsonl`; times are host local
time, emitted as if UTC. Secondary sources: the WebUI transcript
`.nanobot*/webui/<key>.jsonl` and `<key>.segments/NNNNNN.jsonl` (true UTC
`created_at_ms`, 15-hour window) and `.nanobot/history/cli_history` (local
time, prompts only).

Validated against: Source at acdae3d, synthetic fixture.

### `ollama`

Files read: The desktop app's `Library/Application
Support/Ollama/db.sqlite` (macOS) and `AppData/Local/Ollama/db.sqlite`
(Windows), SQLite with WAL sidecars, schema versions 16 to 19: `messages`
with their `tool_calls` (no call id: the n-th `tool` message after an
assistant message pairs with its n-th call, `tool_use_id` is `<chat
id>:<tool_calls.id>`) and attachment names and sizes, never their bytes;
the `users` and `settings` tables are not read. `.ollama/history` (the
`ollama run` prompt history: no timestamp or session, so its rows sort
last and drop out of `--since`/`--until`; the last 100 entries only; a
pasted multi-line prompt becomes several rows; slash commands are `system`
rows). No project path is recorded. Model manifests, `config.json`,
`backup/`, `launch/` and `logs/` are not read.

Validated against: Source at v0.35.1 (b0c1ca4), synthetic fixture; no real
`db.sqlite`, since the desktop app does not exist on Linux.

### `open-interpreter`

Files read: Codex rollouts (Codex parser, Open Interpreter paths):
`.openinterpreter/sessions/**/rollout-*.jsonl` and `archived_sessions/`,
also as `.jsonl.zst`, `.openinterpreter/history.jsonl`,
`.openinterpreter/state_5.sqlite` and
`.openinterpreter/thread_history_1.sqlite` (secondary sources, read as for
Codex), and `external_agent_session_imports.json` (one `system` row per
`/import`ed thread, naming the Claude Code or Cursor source file; that
thread's record times are import time).

Validated against: Source at 2767e5f, synthetic fixture.

### `openclaw`

Files read: `agents/<id>/agent/openclaw-agent.sqlite` (SQLite with WAL
sidecars: `transcript_events`, zstd `event_zstd` rows need `zstandard`;
every reset/deleted archive blob, published or not, and SQLite cold
archives), legacy `agents/<id>/sessions/<id>.jsonl` and
`sessions/*.jsonl`, `sessions/cold/*.jsonl.zst`, and, as secondary
sources, the published reset and deleted archive files `*.jsonl.reset.*` /
`*.jsonl.deleted.*` (optionally `.zst`), compaction checkpoints
`*.checkpoint.<uuid>.jsonl` and pre-doctor repair backups
`*.jsonl.pre-doctor-*-repair-*.bak`, under `.openclaw`,
`.openclaw-<profile>`, `.clawdbot` or `.moltbot`. The session key (channel
and sender) is in each session's start row; `auth_profile_store` is never
read; `*.trajectory.jsonl` and `*.migrated*` are not read.

Validated against: Source at 3b16db7 (the checkpoint and backup writers,
since removed, at 6814525 and 6559e3f), synthetic fixture.

### `opencode`

Files read: `.local/share/opencode/opencode*.db` (SQLite with JSON
columns, WAL sidecars; V1 `message`/`part`, V2 `session_message` for
sessions without V1 rows), legacy JSON `storage/session/*/*.json` and
`storage/message/*/*.json` with their `part/` files, and the older
`project/<slug>/storage/session/` tree.

Validated against: Source at 907b3bc, synthetic fixture.

### `openhands`

Files read: `.openhands/agent-canvas/dev_conversations/<hex>/`,
`.openhands/agent-canvas/conversations/<hex>/` and
`.openhands/conversations/<hex>/`: one `events/event-<idx>-<id>.json` per
event, with the sibling `meta.json` (title, `created_at`, working dir) and
`base_state.json` (model). Event times are naive local time, corrected by
the offset `meta.json` `created_at` implies, else emitted as if UTC.
Legacy 0.x `sessions/<sid>/events/<n>.json` is reported as one `system`
row per session, not parsed.

Validated against: Source at b347047 (SDK), synthetic fixture.

### `pearai`

Files read: `.pearai/sessions/<sessionId>.json` (Continue fork, `history`
and `perplexityHistory`, timestamped from `sessions.json` `dateCreated`)
and `<editor>/User/globalStorage/pearai.pearai-roo-cline/tasks/<id>/` (Roo
Code 3.15 fork through the Cline task mapping; XML tool calls in
`api_conversation_history.json`; project from `taskHistory` in the sibling
`state.vscdb`).

Validated against: Source at 51eceef6 and 0b6df736, synthetic fixture.

### `pi`

Files read: `.pi/agent/sessions/<cwd>/<time>_<id>.jsonl` and legacy
`.pi/agent/*.jsonl` (session tree; fork entries copied from a collected
parent file are dropped; a session that looks driven by little-coder gets
a `system` row saying so),
`.pi/agent/experimental/sessions/<id>/meta.json` (the durable
`session.sqlite` beside it is not parsed), `.pi/agent/trust.json` (project
trust decisions, one `permission setting:` row per project).

Validated against: Source at 2003871, synthetic fixture.

### `qwen-code`

Files read: `.qwen/projects/<slug>/chats/<session>.jsonl` and
`chats/archive/`, `.qwen/tmp/<hash>/logs.json`;
`.qwen/trustedFolders.json`, one `permission setting:
trustedFolders.<path>=<value> (from <file>, file mtime)` row per folder at
the file's modification time with `project_path` the folder;
`session_model` as `model: <id> auth=<authType>`, an assistant record's
`model` as `model: <id>` when no earlier record named one and `model:
<old> -> <new>` on each change, the `logs.json` `model_switch` as `model:
<from> -> <to> reason=<reason>`; a tool result with status `cancelled` or
`awaiting_approval` is followed by `permission decision: <status>`.

Validated against: Source at 2c591ec, synthetic fixture.

### `roo-code`

Files read: `<editor>/User/globalStorage/rooveterinaryinc.roo-cline/` and
`.vscode-mock/global-storage/`: the Cline task files plus
`tasks/<id>/history_item.json` and `tasks/_index.json`; the CLI's input
history `.roo/cli-history.json` (a secondary source, text only).

Validated against: Source at b867ec91, synthetic fixture.

### `shellgpt`

Files read: Files directly under a `chat_cache/` directory:
`AppData/Local/Temp/chat_cache/<id>` and
`AppData/Local/Temp/shell_gpt/chat_cache/<id>`, or a copied Linux or macOS
temp directory given as loose input. One JSON array of OpenAI messages per
chat, `tool_calls` and the pre-1.5.0 `function_call` shape; no timestamp,
model or working directory is recorded, so those columns stay empty.

Validated against: Source at a082bd5, synthetic fixture.

### `tabby`

Files read: Server-side: `.tabby/ee/db.sqlite` or `dev-db.sqlite` (SQLite
with WAL sidecars; `threads`, `thread_messages`, `user_events`, thread
owner from `users.email`; secret columns never read), the pre-migration
backups `ee/db.backup-YYYYMMDD.sqlite` (may hold threads since deleted;
secondary), and the completion event log `.tabby/events/YYYY-MM-DD.json`
(full prompt and generated text; secondary, pairs with `user_events`).
Project is the attached repository URL; no local path is recorded.

Validated against: Source at 21b2904, synthetic fixture.

### `twinny`

Files read: The `rjmacarthy.twinny` row of a VS Code or fork
`User/globalStorage/state.vscdb` (`twinny.conversations`). Messages have
no time of their own: every row carries the conversation's `updatedAt`.
Provider `apiKey`s in the same value are never emitted.

Validated against: Source at 9339bd10, synthetic fixture.

### `vscode`

Files read: `User/workspaceStorage/<hash>/chatSessions/*.jsonl` and
`.json` (with the sibling `workspace.json` for the project),
`User/globalStorage/emptyWindowChatSessions/*`,
`User/globalStorage/transferredChatSessions/*.json`, for Code, Code -
Insiders, VSCodium, Positron, Trae and the `.vscode-server*/data` remote
layout. Covers Copilot Chat; its model and participant ids are opaque
strings.

Validated against: Source at d7622a5, synthetic fixture.

### `zed`

Files read: `threads/threads.db` (zstd-compressed JSON threads; needs
`zstandard`) and `db/0-<channel>/db.sqlite` `sidebar_threads`
(external-agent threads as `system` rows) under `.local/share/zed`,
`Library/Application Support/Zed`, `AppData/Local/Zed` or the Flatpak data
dir. No per-message timestamps: messages carry the thread's `updated_at`.

Validated against: Source at a846890, synthetic fixture.

## Collected files

One subsection per `backlog` or `collected` agent, in alphabetical
order: the files the collector gathers, and the evidence level of
the collector research.

### `amp`

Files collected: `.local/share/amp/history.jsonl` (prompt history with the
working directory), per-thread logs `.cache/amp/logs/threads/<T-id>.log`
and `cli.log`, the terminal tool's shell history
`.cache/amp/terminal/<threadId>/history`, `.amp/claude-diagnostics/`
(Claude Code session files copied when Amp drives Claude Code), settings
and `secrets.json`; full threads are stored server-side by ampcode.com.

Validated against: Shipped binary strings, docs.

Notes in full: prompt history, per-thread logs and the terminal tool's
shell history; full threads are server-side.

### `augment`

Files collected: `.augment/sessions/<conversationId>.json` (full
conversations), `prompt-history.jsonl`, `session.json` (the OAuth
session), `settings.json`, rules, commands, agents and plans.

Validated against: Shipped bundle, docs.

### `autogen-studio`

Files collected: `.autogenstudio/autogen04203.db` (SQLite with the tables
`team`, `message`, `session` and `run`), `files/`, `configs/`,
`temp_env_vars.env` and `.env`.

Validated against: Source.

### `camel-ai`

Files collected: `.camel/gmail_token.json` (the Gmail toolkit's Google
OAuth token), `.camel/skills` and `.config/camel`.

Validated against: Source.

Notes in full: no transcripts under the home; its `chat_history.json` is
relative to the working directory.

### `chatgpt-desktop`

Files collected: Windows: the `OpenAI.Codex_*` package's Chromium profile
(the directory Chromium keeps one user's state in), `Local State`, the
app's logs and the package settings hive; macOS: the `Library/Application
Support/Codex` profile, the `com.openai.codex` logs, preferences and
URL-session stores, and the group container (a directory macOS shares
between an app and its helpers) of the computer-use service, the agent
mode that drives the desktop; the former package and native macOS app
paths.

Validated against: Write-ups and press; real installs on Windows and
macOS, October 2026.

Notes in full: a chat left only an index entry on the installs checked;
its local Codex threads are parsed as `codex-cli`.

### `copilot`

Files collected: `.config/github-copilot` (`AppData/Local/github-copilot`
on Windows): `apps.json` and the legacy `hosts.json`, the OAuth token
store shared by the editor plugins that embed the Copilot language server
(Neovim, JetBrains, Xcode, Vim).

Validated against: Source (the vendored language server).

### `crewai`

Files collected: The run data directory, named after the project folder
(`.local/share/<project>`, `Library/Application Support/<project>`,
`AppData/Local/CrewAI/<project>`): `latest_kickoff_task_outputs.db` (every
task's output with its messages), `flow_states.db` and
`.crewai_user.json`; `.config/crewai/settings.json`, the
`crewai/credentials/` key and encrypted token, and `.crewai` skills.

Validated against: Source, appdirs source.

### `cursor`

Files collected: The editor's `User/` and `logs` directories, whose
`User/globalStorage/state.vscdb` holds the chats as `cursorDiskKV` rows
(`composerData:<id>`, `bubbleId:<composer>:<bubble>`); the Cursor Agent
CLI's `.cursor` (`projects/*/agent-transcripts/`, `chats/*/*/store.db`
with `meta.json`, `acp-sessions/`, `ai-tracking/`), `.config/cursor` and
`auth.json`.

Validated against: Shipped Agent CLI bundle, docs, forum, write-ups.

Notes in full: chats in `state.vscdb` and Agent CLI transcripts; blocked
on format research, the key layout changes between versions.

### `dify`

Files collected: The `difyctl` CLI client's `config.yml`, `login.yml` and
`tokens.yml` (`.config/difyctl`, `AppData/Roaming/difyctl`,
`AppData/Local/difyctl`), and the Docker volumes
`*dify_agent_local_sandbox_home` (the sandbox runtime shellctl's
`shellctl.db` and job output logs) and
`*dify_agent_local_sandbox_workspace`.

Validated against: Source.

Notes in full: the sandbox volume's `shellctl.db` and job logs hold the
shell jobs the agent ran; chats are in PostgreSQL.

### `factory-droid`

Files collected: `.factory/sessions/<projectKey>/<sessionId>.jsonl`
transcripts with their `.settings.json` sidecars,
`cache/session-index/index.db`, `state/history.json` (prompt history),
`missions/`, `logs/`, settings, `mcp.json` and `hooks.json`.

Validated against: Shipped binary strings, docs.

### `flowise`

Files collected: `.flowise/database.sqlite` (`chat_message` with
`usedTools` and `agentReasoning`, `execution`, the encrypted `credential`
table), `encryption.key` and the auth signing secrets, `storage` and
`uploads` (the `vectorstore` indexes are excluded).

Validated against: Source.

### `langflow`

Files collected: The config directory (`.cache/langflow`,
`Library/Caches/langflow`, `AppData/Local/langflow/langflow/Cache`) with
`secret_key` and uploaded files, `.langflow/fs_tool/fs_sandbox` (the
`.langflow/knowledge_bases` stores are excluded), Langflow Desktop's
`.langflow/data` (`database.db`, `.env`) and `com.LangflowDesktop`
directories (from the documentation only), and the Docker volume
`*langflow-data`; the open-source server's `langflow.db`, with the
`message` and `transaction` tables, sits in the installed package and is
not collected.

Validated against: Source, platformdirs source; Desktop from docs only.

Notes in full: Langflow Desktop's `database.db`; the server's
`langflow.db` sits in the installed package and is not collected.

### `local-deep-research`

Files collected: The data directory (`.local/share/local-deep-research`,
`Library/Application Support/local-deep-research`,
`AppData/Local/local-deep-research`): `ldr_auth.db` (the account list),
`encrypted_databases/ldr_user_*.db` (research history and chat), its
backups, the opt-in `research_outputs/` reports and logs, and the pre-1.0
unencrypted `ldr.db`; `Documents/LocalDeepResearch`; the Docker volume
`*ldr_data`.

Validated against: Source, platformdirs source.

Notes in full: research history and chat in per-user SQLCipher (encrypted
SQLite) databases keyed from the login password.

### `metagpt`

Files collected: `.metagpt/config2.yaml` (LLM configuration with
`api_key`) and `config2.bak`.

Validated against: Source.

### `n8n`

Files collected: `.n8n/database.sqlite` (`execution_entity`,
`execution_data`, `chat_hub_sessions`, `chat_hub_messages` and the
encrypted `credentials_entity`), `.n8n/config` (the encryption key), the
event log and crash journal, `.n8n-local-gateway/log` (every computer-use
tool call with its arguments; computer-use is n8n's local tool gateway for
its Assistant), `.n8n-gateway/settings.json`, and the Docker volumes
`*n8n_data` and `*n8n-data`.

Validated against: Source.

Notes in full: `database.sqlite` executions and chat messages, and the
computer-use gateway's log of every tool call.

### `pydantic-clai`

Files collected: `.pydantic-ai/prompt-history.txt` (`clai` v1) and
`.config/pydantic-clai2/` (CLAI 2.0): `sessions.db` (`conversations` with
the messages, `workspace` and `model`), `input-history`, `config.db`,
`credentials-*` and `mcp.json`; `sessions.db` can also hold Claude Code
and Codex sessions imported by `/resume`.

Validated against: Source, PyPI wheel.

### `shared`

Files collected: `.agents` and `.config/agents` (skills and agent
definitions in the cross-tool layout) and `.config/AGENTS.md` (user-level
instructions), read by several agents at once.

Validated against: Derived from the per-agent documents.

### `windsurf`

Files collected: `.codeium/windsurf/cascade/<uuid>.pb` (the history of
Cascade, Windsurf's agent, as protobuf), memories, workflows and
`mcp_config.json`; `.windsurf/transcripts/*.jsonl` (the transcripts
Cascade hands to hooks); the Windsurf and Devin editors' `User/` and
`logs` directories; the Devin CLI's `.config/devin` and
`.local/share/devin/credentials.toml`.

Validated against: Official docs, community write-ups.

Notes in full: Cascade history as protobuf and hook transcripts; blocked
on format research, the `.pb` files have no published schema.
