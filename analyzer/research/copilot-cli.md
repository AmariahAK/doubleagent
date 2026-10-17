# GitHub Copilot CLI transcript schema

Catalog agent: `copilot-cli`. GitHub Copilot CLI (`copilot`) is GitHub's
closed-source terminal coding agent. It writes one event log per session,
`events.jsonl`, under `~/.copilot/session-state/<session id>/`, and keeps
copies of the conversation in a cross-session SQLite database and a prompt
history file. Paths, credentials and exclusions are in
[`collectors/research/copilot-cli.md`](../../collectors/research/copilot-cli.md).
It shares no format with the VS Code Copilot Chat extension
([`vscode.md`](vscode.md)) or the `copilot` catalog agent.

The GitHub Copilot Desktop app runs its sessions through a bundled
Copilot CLI and writes them into the same `~/.copilot/session-state/`
directory, in this format, with `workspace.yaml` `client_name`
`github/autopilot` where the CLI writes `github/cli`; this parser reads
them. The app's own store is in
[`copilot-desktop.md`](copilot-desktop.md), and its paths in
[`collectors/research/copilot-desktop.md`](../../collectors/research/copilot-desktop.md).

## 1. Evidence

Closed source: `github/copilot-cli` holds issues and a changelog only, so
there are no commit links. Each claim names its evidence level:

- **Bundle**: `@github/copilot-darwin-arm64` 1.0.98 (loader package
  `@github/copilot` 1.0.98, `buildMetadata.gitCommit` `45ef16251c8`), the
  `copilot` executable, sha256
  `b1a76d9eec3c88e8545ee96834189ab08c3d75ef65500a60925187fa6c33fdf1`,
  167,681,584 bytes, copied from a Homebrew npm install on 2026-10-15. It
  is a Node.js single executable application (SEA: a Node binary with a
  script and assets appended in a `__NODE_SEA` blob). The blob magic
  `0x0143da20` is at file offset `0x5888000`; flags `0x19` (no warning,
  assets, exec arguments); `sea-loader.js` (124,974 bytes, sha256
  `a9bc83c428713c66388718e554df0be3f9aa92f3e79df17fe47dbadb2e9e7eaf`); one
  asset `copilot.tgz` at `0x58a6877` (70,377,164 bytes, sha256
  `26c6165cb45bce1b37a3a8d6bbcd484e2d938cf513d5970cbdf9ef0da8b92a70`); six
  Node exec arguments (`--no-warnings`, `--expose-gc`, ...). Unlike 1.0.91,
  the blob carries a one-byte field after the flags, and `app.js` is now a
  42 KB bootstrap (sha256
  `c5f37d9040e5d866e01e4266c83d87d08ff3ab0804d6a0a0dc863b4414196a7b`) that
  imports `cli-main.js` (8,193,186 bytes, sha256
  `151c2e2a37ddb2514fc5cdbd5c473f9aeeb1a74d59e5062f3921a46d12a8f1c2`), the
  minified CLI. The event store and the session database are written by
  `prebuilds/darwin-arm64/runtime.node`, a Rust Node addon (97,100,816
  bytes, sha256
  `e5bb26efbdff6cc21a607d3fee0fb9efa933ebeb3d7fe97332ee1a7f0793a02e`). The
  package also ships the event schema as JSON Schema,
  `schemas/session-events.schema.json` (990,556 bytes, sha256
  `81c4a1eb9f0f3bd21a68219f30aaa774fd7c041eafa76c62ff691ac53efae1ed`, 159
  event types with a description per field) and as TypeScript,
  `copilot-sdk/generated/session-events.d.ts` (sha256
  `a2f3897149e0ec1aee24c23dbed3632b44916971d06f5c82768ead98981eaa37`).
  Citations are `copilot 1.0.98 darwin-arm64 <file>@<byte offset>` with a
  literal snippet, shortened after this paragraph to `cli-main.js@<n>`,
  `runtime.node@<n>` and `schema@<n>` (the schema file, at the definition's
  `"title"`). Offsets change with every build; grep for the snippet. The
  binary was read with `strings`, `grep` and Python, never executed.
- **Docs**: [GitHub Copilot CLI configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference)
  (fetched 2026-10-15) for the directory layout and `permissions-config.json`.
- **Observed (macOS)**: Copilot CLI 1.0.98, Homebrew npm install, the
  author's workstation, 2026-10-15, read with `analyzer/tools/shape.py`
  and a schema dump only (key names, types, enum values, counts; no
  values). Three interactive sessions in `manual` permission mode (52, 168
  and 64 lines, none bad), with `bash`, `view`, `apply_patch`, `web_fetch`,
  `web_search` (an MCP tool), `ask_user` and
  `fetch_copilot_cli_documentation` calls; 17 permission prompts approved
  once (`approved`) or for the project (`approved-for-location`, a command
  and a write approval); one automatic model resolution per session; three
  normal shutdowns; one session whose `turns` rows were re-indexed
  ([section 5](#5-sqlite-and-other-stores)). Not exercised: a denial, a
  model switch the user typed, a resumed session, a rewind, a deleted
  session, a subagent, a compaction.
- **Observed (Linux)**: Copilot CLI 1.0.98, installed with `sudo npm
  install -g @github/copilot` on an Ubuntu 26.04.1 arm64 Parallels VM
  (kernel 7.0.0-38-generic, home `/home/sean`), 2026-10-16, read with
  `analyzer/tools/shape.py` only (key names, types, enum values, counts;
  no values). Exercised: `copilot login`, then two interactive sessions.
  Session 1, in `~/demo` (created 21:01:19.518Z, prompts at 21:02:40Z and
  21:05:34.923Z, shutdown 21:16:01Z, all UTC; 194 lines), called `bash` 2
  times, `apply_patch` 2 (11 files, then 1), `view` 3, `glob` 1,
  `web_fetch` 18, `web_search` 7 and `fetch_copilot_cli_documentation` 1,
  with 20 permission requests (`kind` `shell` 2, `url` 17, `write` 1,
  each carrying `permissionMode` `manual` and `agentMode` `interactive`):
  19 `approved` and one `approved-for-location` for the write, all
  `decisionSource` `human_response`, and one automatic model resolution.
  Session 2, in `~/secret` (created 21:16:26.715Z, one prompt at
  21:17:18Z, shutdown 21:19:27Z; 35 lines), had one `write` request
  approved and a model switch the user typed: `/model`, choosing Auto, at
  21:19:20Z, which wrote a `session.model_change` and two `session.info`
  lines ([section 3](#event-types)). The user then removed the project
  with `rm -r secret/`. Every action ran before the first listing, so no
  per-action listing diff exists; the times above are the mapping. Each
  surface wrote: the login a 105-byte process log and the token in the
  GNOME keyring (the GNOME desktop's password store; `config.json` held
  no token; [section 3 of
  `collectors/research/copilot-cli.md`](../../collectors/research/copilot-cli.md#3-credentials));
  each session its `session-state/<uuid>/` directory, a process log (16
  KB and 15 KB), `session-store.db` rows (in a 1.37 MB WAL beside a
  4096-byte main file), a `sidebar-sessions-state` file and its prompts in
  `command-history-state.json`; the `write` approval for the location
  the one `permissions-config.json` entry. No `settings.json` was
  written. Analyzer 0.14.0 over the collection: 2 sessions, 160 rows
  (`system` 79, `tool_use` 35, `tool_result` 35, `assistant` 7, `user`
  4), no `parser:` row, 17 secondary rows deduplicated. The removed
  `~/secret` session was reconstructed in full from `events.jsonl`,
  `session-store.db`, `rewind-file-snapshots/index.json` and
  `command-history-state.json`, which survive the project directory's
  removal, and the inventory reports `/home/sean/secret` as
  `referenced`. Not exercised: a denial, a resume, a rewind, a session
  deleted with the CLI's own command, a subagent, a compaction, plan or
  autopilot mode, a scheduled task.
- **Observed (Windows, through Copilot Desktop)**: Copilot CLI 1.0.99-2
  as the bundled CLI of GitHub Copilot Desktop 1.1.30, which downloads it
  to `AppData\Local\github-copilot-sdk\cli\1.0.99-2\copilot.exe`
  (158,577,952 bytes, sha256
  `b7bc340acf1c82228de2e3504444847f8e18beec1f07f72f260f1bbeb4c3a9b2`),
  on a Windows 11 ARM64 Parallels VM (build 10.0.26300.9550, home
  `C:\Users\sean`), 2026-10-17, all times UTC, names, key names, types,
  enum values and counts only; the exercise is in
  [section 1 of `copilot-desktop.md`](copilot-desktop.md#1-evidence).
  The CLI wrote the Linux layout under `%USERPROFILE%\.copilot\` (the
  executable carries `COPILOT_HOME` and `USERPROFILE`). The general chat's
  `events.jsonl` (115 lines): `session.start` (`producer`
  `copilot-agent`, `copilotVersion` `1.0.99-2`),
  `session.permissions_changed` with the same `allowAll*` keys as the
  Linux app sessions, `session.model_change` (`source` `startup`) at the
  first prompt, 3 `user.message`, 8 `assistant.message`, 9
  `tool.execution_start` and `tool.execution_complete` pairs with tool
  names `powershell` and `create`, 27 `hook.start` and `hook.end` pairs
  with `hookType` `sessionStart`, `userPromptSubmitted`,
  `userPromptTransformed`, `preToolUse`, `postToolUse`,
  `postToolUseFailure` (not seen on Linux), `agentStop` and
  `sessionEnd`, 1 `system.message`, 8 `session.usage_record`, 3
  `session.usage_checkpoint` and 1 `session.shutdown`, written at
  20:13:47, ten minutes after the last reply (the Linux app sessions
  wrote none). The project session's (30 lines): one prompt, one
  `powershell` call, 7 hook pairs and a `session.shutdown`. Three
  `create` calls failed ("Parent directory does not exist") and the
  first `powershell` call exited 1 because Windows PowerShell's
  execution policy refused `npm.ps1`; both are ordinary failed tool
  results, and no `permission.requested` or `permission.completed` was
  written (allow-all stayed on). `session-store.db`: 17 tables,
  `schema_version` 8, `sessions` 2, `turns` 4 (3 for the chat, each with
  its reply, so no null-response duplicate row this time, and 1 for the
  project session), `session_files` 3 (`tool_name` `create`),
  `search_index` 4 (`source_type` `turn`), `assistant_usage_events` 10
  (`model` `claude-sonnet-5.5`, `initiator` `user` and `agent`,
  `api_endpoint` `/v1/messages`, `reasoning_effort` `medium`,
  `finish_reason` `stop` and `tool_calls`), and `checkpoints`,
  `dynamic_context_items`, `forge_skill_proposals`,
  `forge_trajectory_events` and `session_refs` empty. The app also
  created seven sessions that were never prompted, each a directory with
  only `workspace.yaml` (`client_name` `github/autopilot`, `user_named`
  false), `.workspace-fork.lock`, an empty `checkpoints/index.md` table
  and empty `files/` and `research/`, and no `events.jsonl` or
  `session.db`. MCP: the three servers the user added from the app went
  into `mcp-config.json`, two of them never spawned (the CLI log's `MCP
  server connection failed {"server_name":"<name>","raw_error":"failed
  to spawn MCP server process: program not found"}`, six and five
  times), and the one that connected left one tool cache per session in
  `AppData\Local\copilot\mcp-tools\` ([section 2](#2-transcript-files)).
  Analyzer 0.14.0 over the collection: `copilot-cli` rows `assistant` 7,
  `system` 92, `tool_result` 10, `tool_use` 10, `user` 4, 10 duplicate
  secondary rows dropped, no `parser:` row; among them `session start:
  copilot 1.0.99-2 producer=copilot-agent cwd=...`, `permission mode:
  allow-all off -> on`, `model: claude-sonnet-5.5 source=startup`, the
  `hook <hookType> start:` and `end:` rows, `file changed: <path>
  tool=create` and `session end: routine files modified: <paths>`, and
  one `session metadata: user_named=false ... client=github/autopilot`
  row for each of the seven unprompted sessions. The standalone CLI on
  Windows is the next bullet.
- **Observed (Windows, winget)**: the standalone Copilot CLI 1.0.98
  installed with `winget install GitHub.Copilot` (winget is the Windows
  Package Manager) on the same Windows 11 ARM64 Parallels VM (build
  10.0.26300.9550, home `C:\Users\sean`), reverted to a clean snapshot
  that had never run Copilot Desktop, 2026-10-17, all times UTC, names,
  key names, types, enum values and counts only. The first round with a
  names-only listing after every action; the per-action writes are in
  [section 1 of
  `collectors/research/copilot-cli.md`](../../collectors/research/copilot-cli.md#1-source-and-evidence-level).
  Exercised in `C:\Users\sean\demo`: a first start with `/login` from
  inside the session (21:46:48 to 21:48:02), a session that read web pages
  from its first prompt at 21:50:55, one tool call denied and one approved
  with "allow always" (a `write` grant for `demo`), a `/model` switch to
  Auto, a quit at 22:08:31, a resume from the resume picker at 22:08:50,
  and a delete with the CLI's own command from a new session started at
  22:11:04. The session's `events.jsonl` at the quit (1,973,737 bytes)
  held `assistant.message` 55, `assistant.turn_start` 55,
  `assistant.turn_end` 55, `session.usage_record` 55,
  `tool.execution_start` and `tool.execution_complete` 109 each,
  `permission.requested` and `permission.completed` 79 each,
  `user.message` 6, `session.model_change` 4, `session.usage_checkpoint`
  4, `session.info` 3, `system.message` 3, `session.start` 1,
  `session.shutdown` 1, 12 each of the eight `model.*` types
  (`captured_assignment_context`, `message`, `messages_snapshot`,
  `model_call_started`, `model_call_success`, `response`, `turn_ended`,
  `turn_started`), and 2 each of `subagent.configured`,
  `subagent.selected`, `subagent.started` and `subagent.completed`, which
  came from the session's web-reading task and were seen on no other
  install. `session.start` `data` keys: `sessionId`, `version`,
  `producer`, `copilotVersion`, `startTime`, `contextTier`,
  `context{cwd}`, `alreadyInUse`, `remoteSteerable`. `system.message`:
  `role`, `content`, `metadata{variables{gitCommitTrailer, sessionId,
  clientName, coauthorEnabled}}`, `interactionId`. `permission.requested`
  `permissionRequest` key sets: 72 of the `url` form (`kind`,
  `toolCallId`, `intention`, `url`, `requestSandboxBypass`,
  `requestSandboxBypassReason`, then `promptRequest`; the web fetches), 2
  of the shell form (`fullCommandText`, `shellType`, `intention`,
  `commands`, with `identifier` and `readOnly`, ...), 2 of the write form
  (`fileName`, `diff`, `newFileContents`, `canOfferSessionApproval`,
  `fileEdits`) and 3 with a key beginning `redirecte` (the rest of its
  name was cut in the listing; not determined). `permission.completed`
  was listed as `{requestId, toolCallId, result{kind, decisionSource},
  agentId}`, `agentId` on some records only: `decisionSource` inside
  `result`, where the Linux records and the parser have it beside
  `result` ([section 3](#event-types)); not determined whether this is
  the shape or the listing's nesting, and no row of it reached the
  analyzer, since the session was deleted before the collection. The
  `result.kind` of the denial was not recorded. `model.model_call_success`
  carried `turn`, `callId`, `modelCallDurationMs`, `ttftMs`,
  `outputTtftMs`, `interTokenLatencyMs` and `modelCall{model, api_id,
  api_endpoint, request_id, client_request_id, service...}`. The resume
  rewrote `workspace.yaml` with `updated_at` unchanged, adding
  `remote_steerable` (false), `mc_task_id`, `mc_session_id` and
  `mc_last_event_id` (UUIDs), the keys every Copilot Desktop session
  carries; the resumed process logged `Remote session access enabled`
  and `Using default model: gpt-6.1-sol`, and the sync itself is logged
  nowhere. The delete, `/session delete <id> --yes --remote` after four
  other forms (`/session`, `/session delete-all`, `/session delete <id>`,
  `/session delete copilot <id>`), asked whether to delete the synced
  copy too ("has been synced to your account. Would you also like to
  delete the synced session data"); the user said yes. It removed the
  session directory whole (`events.jsonl`, `workspace.yaml` with the
  `mc_` keys, both `rewind-file-snapshots` files, `checkpoints/`,
  `files/`, `research/`) and the id from the sidebar file, and left: in
  `session-store.db` (the WAL unchanged since 22:06) the `sessions` row
  (`cwd` set, `repository` null, a 32-character `summary`), 3 `turns`
  (prompts of 63, 18 and 42 characters, replies of 4,346, 1,704 and 30,
  stamped 22:03:42, 22:04:58 and 22:05:54), 1 `session_files` row
  (`apply_patch`), 3 `search_index` rows and 55
  `assistant_usage_events` (`model` `claude-sonnet-5`, `api_endpoint`
  `/v1/messages`; the new session's `gpt-6.1-sol` rows use
  `ws:/responses`), with `session_refs`, `checkpoints` and
  `forge_trajectory_events` empty; the session's 0-byte operation lock;
  the seven slash commands among the ten entries of
  `command-history-state.json`; the five process logs, which record
  nothing about the delete (no `sessions.delete` line, unlike the desktop
  app's bundled CLI); `permissions-config.json`; and the file the approved
  call wrote. The `events.jsonl` held 6 `user.message` and the store kept
  3 `turns`, the last three; why is not determined. With the remote copy
  deleted too, no local file says the session was ever synced: the `mc_`
  keys lived only in the deleted `workspace.yaml`. Analyzer 0.14.0 over
  the collection (collector 1.13.0, 34 files): 24 rows (`assistant` 3,
  `system` 11, `user` 10), 2 sessions, 3 duplicate secondary rows
  dropped, no `parser:` row, `problems: []`, `demo` the one project. The
  deleted session was rebuilt from `session-store.db` alone: `session
  name:` at 21:46:48 (`created_at`), the three `turns` as `user` and
  `assistant` pairs (the last reply, 30 characters, the agent reporting
  the denied write) and `file changed: <path> tool=apply_patch` at
  22:06:06. The other rows: `signed in: https://github.com as <login>`
  once per process log (21:48:02, 22:08:50, 22:08:51, 22:11:05),
  `permission setting: locations.<cwd>.tool_approvals={"kind":"write"}
  (from .copilot/permissions-config.json, file mtime)` at 22:06:06, the
  new session's `session metadata: user_named=false forks=0
  compactions=0 client=github/cli`, `session start: copilot 1.0.98
  producer=copilot-agent cwd=<demo>`, `model: gpt-6.1-sol
  cause=initial_resolution source=automatic effort=medium` and `session
  end: routine files modified: none`, and the seven slash commands as
  undated `user` rows from the command history, the three `/session
  delete` forms among them. The deletion lost from the timeline the
  session's 109 tool calls and their permission decisions, the denial,
  the `/model` switch's `session.info` output, the resume, and every
  event of its first three prompts. A first `/login` left pending also
  wrote about 280,000 process-log lines (45 MB in five files) on this
  install; the sign-in line the parser reads is among them; the npm-installed CLI on Windows is still not observed
  ([issue 133](https://github.com/seanthegeek/doubleagent/issues/133)).

## 2. Transcript files

Relative to the home; `~/.copilot` unless `COPILOT_HOME` moves it.
Installs that predate the XDG migration keep the same names under
`.local/state/.copilot` (session state, store, history) and
`.config/.copilot` (config, permissions)
([`collectors/research/copilot-cli.md`](../../collectors/research/copilot-cli.md)).

| Path | Content | Parse |
| --- | --- | --- |
| `.copilot/session-state/<uuid>/events.jsonl` | the session event log | yes, primary |
| `.copilot/session-state/<uuid>/workspace.yaml` | session metadata: name, cwd, counts | yes |
| `.copilot/session-state/<uuid>/rewind-file-snapshots/index.json` | per-turn file snapshots for `/rewind`, with the prompt | yes, secondary |
| `.copilot/session-state/<uuid>/rewind-file-snapshots/tracking.json` | `{schema, tracking}` | no |
| `.copilot/session-state/<uuid>/checkpoints/index.md` | Markdown table of compaction checkpoints | no |
| `.copilot/session-state/<uuid>/session.db` | per-session SQLite of the agent's own todo tables (bundle; not observed) | no |
| `.copilot/session-state/<uuid>/files/`, `research/`, `plan.md` | agent artifacts (empty on the install) | no |
| `.copilot/session-state/<uuid>.jsonl` | legacy flat transcript, refused by 1.0.98 | no, [section 6](#6-format-versions) |
| `.copilot/session-store.db` (+`-wal`, `-shm`) | cross-session SQLite ("chronicle" store) | yes, secondary |
| `.copilot/command-history-state.json` | prompt history for Ctrl+R | yes, secondary |
| `.copilot/permissions-config.json` | standing approvals per project | yes |
| `.copilot/settings.json` | user settings, JSON with comments (written on macOS, absent on the Linux install) | yes, `allowedUrls`/`deniedUrls` |
| `.copilot/sidebar-sessions-state/<sha256 of cwd>.json` | `{schemaVersion, cwd, sessionIds}` | yes, as a join |
| `.copilot/logs/process-<epoch ms>-<pid>.log` | process log | yes, sign-in line only |
| `.copilot/open-sessions-state.json` | open-session tracker (`{}` observed) | no |
| `.copilot/mcp-config.json` | MCP server configuration, `mcpServers{<name>{type, command, args[], tools[], env{}}}`; `env` can hold a token in plain text (a GitHub personal access token on the Windows install) | no ([section 8](#8-parser-plan)) |
| `.copilot/.mcp-writer.binding`, `.copilot/.mcp-writer.lock` | the lock of the writer of `mcp-config.json`: `lock{file_index, platform, volume}`, `root{...}` (Windows install) | no |
| `AppData/Local/copilot/mcp-tools/<sha256>.json` | the cached tool list of a connected MCP server, `{schemaVersion, serverName, tools[{name, description, annotations{destructiveHint, openWorldHint, readOnlyHint, title}, inputSchema}], updatedAt}`, one per session that connected (Windows install; not observed on macOS or Linux) | no ([section 8](#8-parser-plan)) |

`session-state/<uuid>/` is created at session start (`runtime.node@83194924`
`Workspace initialized`); `files/` is "Persistent storage for session
artifacts" (`runtime.node@82945561`); `session.db` is the per-session SQL
database (`cli-main.js@149653`
`this.join(this.sessionStatePath,"session.db")`).

## 3. Record schema

### Envelope

Every line is `{id, parentId, timestamp, type, data}` (observed, 284 of
284 on macOS and every line on Linux; `schema@1133`). `id` is a UUID v4; `timestamp` is ISO 8601 UTC with
milliseconds and `Z`; `type` names the event; `data` is its payload. Two
optional envelope keys are in the schema and were not observed: `agentId`,
set on events from a subagent ("Absent for events from the root/main
agent", `schema@1503`), and `ephemeral`, which marks events that are "not
persisted to the session event log on disk" (`schema@1331`): 83 of the 159
types are ephemeral (streaming deltas, `session.idle`,
`session.title_changed`, `assistant.usage`, `session.snapshot_rewind`, the
`model.call_*` family) and never reach the file. A parser skips unknown
types.

`parentId` is "the chronologically preceding event in the session ... Null
for the first event" (`schema@1133`). Observed: the previous line on 258
lines, `null` on `session.start` and on `model.turn_started`, and on 3 of
9 `model.model_call_started` an id absent from the file. The dangling ids
are ephemeral events, which take a place in the chain but are not
written; the `model.*` events come from the Rust runtime's own publisher
(`runtime.node@80033248` `Failed to publish native model event`) and start
a chain of their own. A rewind truncates the file instead of branching it
([section 4](#4-joins-and-timestamps)), so the chain carries no tree and a
parser ignores it.

### Event types

Observed types with the keys a parser reads (all named in the schema
unless marked):

| `type` | `data` keys | Schema |
| --- | --- | --- |
| `session.start` | `sessionId` (= directory name), `version` (1), `producer` (`copilot-agent`), `copilotVersion`, `startTime` (session creation, not the line time), `selectedModel`, `context{cwd, gitRoot, repository, hostType, branch, headCommit}` (`cwd` alone on Linux, outside a git repository), `alreadyInUse`, `remoteSteerable`, `contextTier` | `@801015` `StartData`; `@987057` `WorkingDirectoryContext` |
| `session.model_change` | `previousModel`, `newModel`, `cause` (`initial_resolution` observed; `rate_limit_auto_switch` per the schema), `source` (`automatic` observed; `model_picker` observed on Linux for a typed `/model` choosing Auto, with `previousModel`, `newModel` `auto`, `previousReasoningEffort` `medium`, `reasoningEffort` and `contextTier` null; also `model_command`, `settings_command`, `config_command`, `startup`, `agent`, `plan_mode`, `managed_settings`, `repo_settings`, `sdk`, ...), `reasoningEffort`, `previousReasoningEffort`, `providerId` | `@460110` `ModelChangeData`, `@462830` `ModelChangeSource` |
| `session.info` | `infoType` ("Category of informational message": `model`, `fork`, `remote`, `tip`, `warning`, `managed_plugins`, `managed_plugins_complete`, `relay_attachments_dropped`, `canvas`, `hook_progress_transient` in `cli-main.js`, offset not recorded), `message` ("Human-readable informational message for display in the timeline"), `url` and `tip` (optional). Emitted persisted (`this.emit("session.info", ...)`) and ephemeral (`emitEphemeral`) in `cli-main.js` of the 1.0.98 linux-arm64 package (offset not recorded). Observed on Linux right after the `model_picker` change: `infoType` `model`, `Model changed from GitHub Copilot • GPT-6.1 Sol (medium) to GitHub Copilot • Auto for this session` and `Auto routing profile change to Balance requested.` | `schema` `InfoEvent` / `InfoData` of the 1.0.98 linux-arm64 package, offset not recorded ("Informational message for timeline display with categorization"; `additionalProperties: false`) |
| `system.message` | `content` (the full system prompt, 36 KB observed), `role` (`system`, `developer`), `interactionId`, `metadata.variables` (`gitCommitTrailer{clientName, coauthorEnabled, sessionId}` real install and `runtime.node@81992124`) | `@829319` |
| `user.message` | `content` (the prompt as typed), `transformedContent` (the prompt with injected context), `messageId`, `interactionId`, `turnId`, `delivery` (`idle`, `steering`, `queued`), `agentMode` (`interactive`, `plan`, `autopilot`, `shell`), `source` (absent or `user` for typed input; `skill-<name>`, `agent-<id>`, `command-`, `schedule-`, `autopilot-` prefixes), `isAutopilotContinuation`, `attachments`, `responsesReasoning` | `@959453` |
| `assistant.turn_start` / `assistant.turn_end` | `turnId` ("typically a stringified turn number"), `interactionId`, `model`, `parentToolCallId` | `@63598` |
| `assistant.message` | `messageId`, `originatingMessageId` (= the prompt's `messageId`), `content` (empty when the message only calls tools), `model`, `providerId`, `turnId`, `phase` (`final_answer` observed), `reasoningText` (readable reasoning summary), `reasoningOpaque` and `encryptedContent` (opaque provider blobs), `reasoningBlocks{provider, blocks[{type, id, summary[{type, text}], encrypted_content}]}`, `toolRequests[]`, `apiCallId`, `serverTools`, `rte`, `chunkIndex`/`chunkCount`, `parentToolCallId` | `@29947` |
| `toolRequests[]` | `toolCallId` (`call_...`; `custom_...` for grammar tools such as `apply_patch`), `name`, `arguments` (object, or a string for `type` `custom`), `type` (`function`, `custom`), `toolTitle`, `intentionSummary`, `mcpServerName`, `mcpToolName` | `@41785` |
| `tool.execution_start` | `toolCallId`, `toolName`, `toolTitle`, `arguments`, `model`, `turnId`, `mcpServerName`, `mcpToolName`, `parentToolCallId` | `@899827` |
| `tool.execution_complete` | `toolCallId`, `success`, `result{content, detailedContent, structuredContent, contents}`, `error{code, message}`, `shellExecution{exitCode}`, `isUserRequested`, `toolTelemetry`, `model`, `turnId`, `interactionId`, `rte` | `@873844` |
| `permission.requested` | `requestId`, `permissionRequest{kind, toolCallId, intention, ...}`, `promptRequest{kind, ...}` (the prompt shown), `permissionMode` (`manual`, `assisted`, `allow-all`), `agentMode`, `ownerSessionId`, `resolvedByHook` | `@565075`, `@561612` `PermissionRequest`, `@520733` `PermissionMode` |
| `permission.completed` | `requestId`, `toolCallId`, `decisionSource` (`human_response` observed; `assisted_approval`, `host_policy`, `unattended_fallback`, `authorization_carry_forward`), `result{kind, ...}` | `@596459` `PermissionResult`, `@504557` |
| `session.usage_record` | `usage{model, inputTokens, outputTokens, reasoningTokens, cacheReadTokens, cost, duration, finishReason, initiator, interactionType, apiEndpoint, transport, provider, isByok, isAuto, accounting{sequence, sourceSessionId, usageId}, apiCallId}` | `@81773` `AssistantUsageData` |
| `session.usage_checkpoint`, `session.shutdown` | `accountingSnapshot`, `shutdownType` (`routine`, `error`), `errorReason`, `sessionStartTime` (epoch ms), `codeChanges{filesModified, linesAdded, linesRemoved}`, `modelMetrics`, `currentModel`, `eventsFileSizeBytes` | `@765167`, `@771298` |
| `model.turn_started`, `model.model_call_started`, `model.turn_ended` | `kind`, `model`, `modelInfo{...}`, `timestampMs`, `turn` | not in the schema; `cli-main.js@1147661` |
| `model.messages_snapshot` | `kind`, `messages[{role, content}]` (the utility prompt) | not in the schema |
| `model.captured_assignment_context` | `kind`, `assignmentContext` (string) | not in the schema |
| `model.message`, `model.response` | `callId`, `kind`, `message{role, content, apiCallId, outputTokens, refusal}` / `response{...}`, `modelCall{model, api_endpoint, initiator, transport, request_id, ...}`, `turn` | not in the schema |
| `model.model_call_success` | `callId`, `modelCall`, `copilotUsage{token_details, total_nano_aiu}`, `quotaSnapshots`, `provider`, `modelCallDurationMs`; on the Windows winget install (1.0.98) also `turn`, `ttftMs`, `outputTtftMs`, `interTokenLatencyMs` and `modelCall{model, api_id, api_endpoint, request_id, client_request_id, service...}` | not in the schema |
| `subagent.configured`, `subagent.selected`, `subagent.started`, `subagent.completed` | keys not recorded; 2 of each on the Windows winget install (1.0.98), from a session's web-reading task, seen on no other install | `subagent.started` and `.completed` are in the schema (list below); the other two not checked |

Glosses: CAPI is the Copilot API, the GitHub endpoint that serves the
models; `interactionId` is its id for one prompt's run. `rte` is the
"treatment/eligibility signal returned by the Copilot API in the
`X-GitHub-Copilot-Request-TE` response header" (`schema@29947`). A nano AIU
is a billing unit ("nano-AI units cost", `ShutdownData`); BYOK is "bring
your own key", a user-supplied model provider. MCP is the Model Context
Protocol, the plugin protocol for external tools.

`permissionRequest.kind` values: `shell` (`fullCommandText`, `commands[{identifier,
readOnly}]` plus `allowMatchIdentifier` (real install and
`runtime.node@87055448`), `commandSegments`, `possiblePaths`,
`possibleUrls`, `hasWriteFileRedirection`, `canOfferSessionApproval`,
`shellType` (real install and `runtime.node@87056164`)), `write` (`fileName`, `diff`,
`newFileContents`, and `fileEdits` and `canOfferSessionApproval` on the Linux install), `read` (`path`), `url` (`url`, and
`requestSandboxBypass` and `requestSandboxBypassReason` on the Linux install), `mcp` (`serverName`,
`toolName`, `args`), `memory`, `custom-tool`, `hook`, `workflow`,
`extension-management`, `extension-permission-access`,
`extension-env-access` (`schema@583572`, `@594037`, `@587312`).
`promptRequest.kind` adds `commands` (in place of `shell`) and `path`.

`result.kind` values (`schema@596459`): `approved`;
`approved-for-session` and `approved-for-location` (with `approval{kind,
commandIdentifiers | serverName, toolName | toolName | operation |
extensionName}`, and `locationKey`, the git root or cwd, for the location
form, `@485843`); `approved-read-only-for-session` (`directories`);
`cancelled` (`reason`); `denied-by-rules` (`rules[{kind, argument}]`);
`denied-no-approval-rule-and-could-not-request-from-user`;
`denied-interactively-by-user` (`feedback`, `forceReject`);
`denied-by-content-exclusion-policy` (`path`, `message`);
`denied-by-permission-request-hook` (`message`, `interrupt`). Only the
first and the location form were observed; on Linux the location form
carried `approval{kind: write}` and the project path as `locationKey`.

The eight `model.*` types are the runtime's native model events, listed in
`cli-main.js@1147861` (`captured_assignment_context:!0,...,turn_started:!0`)
and kept out of the CLI's own timeline (`cli-main.js@1158330`
`if(!($M(c)||Ree(c)))return t(c)`). Each set is one call to a utility
model, not the session model. Observed: three sets per session, one to
`gpt-4o-mini` and two to `gpt-5.4-nano` or `gpt-5.6-luna-utility`. The
first is the session-name generator: the CLI calls
`modelGenerateSessionName` with the first prompt, stores the answer as the
session's name and logs it (`cli-main.js@7310874`
``await e.name.setAuto({summary:O.value}),s.info(`Session named: "${O.value}"`)``;
prompt `runtime.node@90556512` `Generate a session title for this
message:`). The other two are the task-analytics classifier, a telemetry
feature that labels each turn (`runtime.node@83390256`
`judgeModelPreferredgpt-5.6-luna-utility`, `@83388829` `gpt-5.4-nano`,
`@83390335` `copilot_cli_task_analytics`). `assignmentContext` is the ExP
assignment string (ExP is Microsoft's experimentation service; the string
names the experiment treatments the client is in, `runtime.node@79937841`
`ExP assignment response AssignmentContext must be a string`).

Schema types a parser should handle although none was observed:
`session.resume` (`resumeTime`, `selectedModel`, `context`),
`session.error` (`errorType`, `message`, `statusCode`), `abort`
(`reason`: `user_initiated`, `remote_command`, `user_abort`,
`autopilot_credit_limit`), `session.compaction_complete` (`summaryContent`,
`checkpointNumber`, `checkpointPath`), `session.context_changed`
(`WorkingDirectoryContext`), `session.permissions_changed`
(`previousMode`, `mode`), `session.mode_changed` (`previousMode`,
`newMode`), `session.auto_mode_resolved` (`chosenModel`,
`routingMethod`; Auto is the model setting that lets the service choose), `session.task_complete` (`summary`), `session.handoff`,
`session.schedule_created` (`prompt`, `cron`, `at`), `system.notification`
(`content`, `kind`), `assistant.reasoning` (`reasoningId`, `content`),
`tool.user_requested` (`toolCallId`, `toolName`, `arguments`; a tool the
user ran), `permission.carriedForward`, `human_response.recorded`,
`subagent.failed` (`toolCallId`, `agentName`, `model`, the keys the schema
gives `.started` and `.completed` too, which were observed on Windows),
`skill.invoked` (`name`, `path`), `hook.start` / `hook.end`.

## 4. Joins and timestamps

- Session: `session.start.data.sessionId` = the directory name = `turns`,
  `sessions.id`, `sidebar-sessions-state` `sessionIds[]` and
  `workspace.yaml` `id`.
- Tool call: `toolRequests[].toolCallId` = `tool.execution_start` and
  `tool.execution_complete` `toolCallId` = `permissionRequest.toolCallId`
  = `permission.completed.toolCallId`. `requestId` joins the two
  permission events.
- Prompt to reply: `user.message.messageId` =
  `assistant.message.originatingMessageId`; `interactionId` groups the
  prompt, its turns and its tools. `turnId` counts agent-loop turns
  (22 observed for 7 prompts) and is not `turns.turn_index`, which counts
  prompts.
- Utility call: `model.*` `callId` joins message, response and success.
- Rewind: a snapshot's `eventId` is the id of the `user.message` it
  precedes (real install, equality not checked). `/rewind` truncates
  `events.jsonl` at that event ("Truncates persisted session history to a
  specific event", `runtime.node@83147234`; restore and truncation are
  "Not crash-atomic", `@83147760`), so discarded turns are gone from the
  log and survive only in the stores of
  [section 5](#5-sqlite-and-other-stores).
- Project: `session.start.data.context.cwd`, updated by
  `session.context_changed` and `session.resume`; `workspace.yaml` `cwd`;
  `sessions.cwd`; `sidebar-sessions-state` `cwd`, whose file name is the
  sha256 of the cwd (real install, verified).

On the Windows winget install (1.0.98) one session held 12 of each
`model.*` type beside its 55 `assistant.message`, so that session made 12
utility calls, not the three per session seen on macOS; what each was for
was not determined.

Every timestamp in the log is UTC with `Z`. `session.shutdown.sessionStartTime`
is epoch milliseconds; `timestampMs` on native model events likewise.

## 5. SQLite and other stores

`session-store.db` runs in WAL mode (`runtime.node@80402520` `PRAGMA
journal_mode = WAL`); on the install the data was in the 1.7 MB WAL and
the main file was 4 KB (1.37 MB and 4096 bytes on Linux), so the WAL
must be read. `schema_version` 38 observed on macOS and 8 on Linux, both
on 1.0.98, and 8 on Windows with the Copilot Desktop app's bundled
1.0.99-2 ([section 6](#6-format-versions)). The runtime writes it as each turn ends and rebuilds it from
`events.jsonl` with `/chronicle reindex` ("chronicle" is the CLI's name
for its session-history commands: `standup`, `reindex`, `skills`, `tips`;
`runtime.node@80541016` `src/runtime/src/session/store_reindex.rs`). Column
meanings come from the runtime's own description for its SQL tool
(`runtime.node@80212161`):

| Table | Written by | Meaning |
| --- | --- | --- |
| `sessions(id, cwd, repository, host_type, branch, summary, created_at, updated_at)` | `@80389716` `INSERT INTO sessions ... ON CONFLICT(id) DO UPDATE SET cwd = COALESCE(excluded.cwd, cwd)` | one row per session; `summary` a 27 to 39 character title (observed) |
| `turns(session_id, turn_index, user_message, assistant_response, timestamp)` | `@80389302` `INSERT INTO turns ... ON CONFLICT(session_id, turn_index) DO UPDATE SET user_message = COALESCE(...)`; next index from `SELECT MAX(turn_index)` | one row per prompt: the typed prompt and the final reply |
| `session_files(session_id, file_path, tool_name, turn_index, first_seen_at)` | `@80389148` `INSERT OR IGNORE INTO session_files` | files changed, `tool_name` `edit`, `create` or `apply_patch` |
| `session_refs(session_id, ref_type, ref_value, turn_index, created_at)` | `@80388999` `INSERT OR IGNORE INTO session_refs` | `ref_type` `commit`, `pr` or `issue` (`@80212254`) |
| `checkpoints(session_id, checkpoint_number, title, overview, history, work_done, technical_details, important_files, next_steps, created_at)` | `@80390542` | compaction checkpoints |
| `search_index` (FTS5, SQLite's full-text index) | `@80390397` | `source_type` `turn`, `checkpoint_*` or `workspace_artifact`; `source_id` `<session>:turn:<n>`; `content` = prompt, newline, reply (observed) |
| `assistant_usage_events` | `@80401153` | one row per model call: model, tokens, `total_nano_aiu`, `initiator`, `finish_reason`, `token_details_json`; on Linux 28 rows with `model` `gpt-6.1-sol`, `copilot_usage_model` null, `initiator` `agent` or `user`, `api_endpoint` `ws:/responses` or `/responses`, `reasoning_effort` `medium`, `finish_reason` `stop` or `tool_calls` |
| `forge_trajectory_events(session_id, tool_call_id, turn_index, event_type, command, output, exit_code, event_key, event_value, created_at)` | `@80402086` | tool commands and outputs collected for Forge, the feature that proposes skills from repeated workflows (`/chronicle skills create`); `event_type` values not found as literals |
| `forge_skill_proposals`, `dynamic_context_items` | | skill proposals and per-repository context; no session content (both present and empty on Linux, beside `search_index` and its five FTS5 shadow tables) |

Observed: `turns` 9 rows on macOS, `user_message` equal to a
`user.message` `content` and `assistant_response` equal to an
`assistant.message` `content` or null; `timestamp` 4 to 293 seconds after
the matching `user.message` line. On one macOS session the first two
prompts appear again at `turn_index` 2 and 3 after a turn whose response
is null. The Linux round explains the repeat from the timestamps (6
`turns` rows; prompt lengths 111 and 114 characters in session 1, 90 in
session 2). Session 1 has `(0, p1, r1)` at 21:05:34.927Z, `(1, p2, null)`
at 21:08:11.565Z, `(2, p1, r1)` at 21:08:12.119Z and `(3, p2, r2)` at
21:16:01.831Z; session 2 has `(0, p1, null)` at 21:18:16.638Z and `(1, p1,
r1)` at 21:19:27.956Z. So the complete row of a turn is written when the
next prompt arrives (21:05:34.927Z is 4 ms after prompt 2) or at shutdown
(21:16:01.831Z, 21:19:27.956Z), under `MAX(turn_index) + 1`; a
prompt-only row with a null response is written mid-turn, 58 to 157
seconds after the prompt, during a model call and aligned with no
transcript event; and the row written on the next prompt repeats the
previous turn under a new index when a prompt-only row sits between
them. No delete, rewind or reindex was involved. The parser's secondary
deduplication drops both kinds of copy (17 rows on the Linux collection).
The Windows install (bundled 1.0.99-2) wrote no prompt-only row: one
complete row per prompt, 3 for the general chat and 1 for the project
session, the chat's last stamped at its shutdown.
The string `duplicate_turn` sits beside the reindex messages
(`runtime.node@80355318`); a reindex, which derives turns from the log and
merges with `COALESCE`, was not run. Other Linux rows: `sessions` 2
(`cwd` set; `repository`, `host_type` and `branch` null, since neither
directory was a git repository; `summary` the generated session name),
`session_files` 13 (`tool_name` `apply_patch`), `session_refs`,
`checkpoints` and `forge_trajectory_events` 0, `search_index` 6
(`source_type` `turn`, `source_id` `<session>:turn:<n>`, `content` the
prompt, a newline and the reply, or the prompt alone when the reply is
null). The bundle holds no `DELETE` for `sessions`,
`turns`, `session_files`, `session_refs` or `checkpoints` (only for
`search_index` rows it rewrites and `dynamic_context_items`), so these
rows outlive a rewind and a deleted session directory. A session deleted
from the GitHub Copilot Desktop app is a `sessions.delete` call to the
CLI the app bundles, which removes the session directory and leaves these
rows: observed on the Linux install of 2026-10-16, where two deleted app
sessions kept their `sessions`, `turns`, `session_files`,
`assistant_usage_events` and `search_index` rows, and on the Windows
install of 2026-10-17, where the deleted general chat kept its
`sessions` row, 3 `turns`, 3 `session_files`, 3 `search_index` and 8
`assistant_usage_events` rows, and the WAL holding them was not
checkpointed when the app quit
([What a deleted session leaves in `copilot-desktop.md`](copilot-desktop.md#what-a-deleted-session-leaves)).
A session deleted with the standalone CLI's own command, `/session delete
<id> --yes --remote`, locally and from the account (Windows winget
install, 1.0.98, 2026-10-17), likewise kept its `sessions` row, 3
`turns`, 1 `session_files` row, 3 `search_index` rows and 55
`assistant_usage_events` rows (`model` `claude-sonnet-5`, `api_endpoint`
`/v1/messages`); the WAL's size and time were unchanged since 22:06,
before the delete. Its `events.jsonl` had held 6 `user.message` lines,
and the store kept only 3 turns, the last three (stamped 22:03:42,
22:04:58 and 22:05:54); why the first three are missing is not
determined. The analyzer rebuilt the deleted session from these rows
alone ([section 1](#1-evidence)).

Other stores:

- `command-history-state.json` `{commandHistory: [...]}`: prompts, newest
  first, a repeat moved to the front, slash commands included (the
  Linux file held 4 entries, `/model` newest, then the three prompts), at
  most `commandHistoryMaxSize` (50
  by default, 1 to 1000) (`cli-main.js@1109188`
  `this.commandHistory.unshift(t),this.commandHistory=this.commandHistory.slice(0,this.maxSize)`;
  `@1108158` `yNt=50,Dze=1e3`). No time, session or cwd. The docs name a
  `command-history-state/` directory instead; 1.0.98 wrote the file.
- `workspace.yaml` (real install key order): `id`, `cwd`, `client_name`,
  `name` (the generated or `/rename` name), `user_named`, `summary_count`
  (compactions), `fork_count`, `created_at`, `updated_at`,
  `remote_steerable`, `mc_task_id`, `mc_session_id`, `mc_last_event_id`;
  on Linux `client_name` was `github/cli` on both sessions, `user_named`
  false, `summary_count` and `fork_count` 0, `remote_steerable` false. On
  the Windows winget install (1.0.98) the file was written at session
  start without `name` and the last four keys (212 bytes), gained `name`
  at the first prompt and `remote_steerable` and the `mc_` keys at a
  resume, with `updated_at` unchanged; the `mc_` keys are the sync marker
  of [section 8](#8-parser-plan).
  The struct has 19 fields (`runtime.node@82945317` `struct WorkspaceMetadata
  with 19 elements`); `repository`, `host_type`, `branch`,
  `mc_environment_id` and `chronicle_sync_dismissed` are among the rest
  (`runtime.node@87588572`). The `mc_` keys are Mission Control ids;
  Mission Control is GitHub's service that mirrors a session's events for
  remote viewing and steering (`runtime.node@79041460` `enroll published
  application sessions in Mission Control`).
- `rewind-file-snapshots/index.json` `{schema, snapshots[{snapshotId,
  eventId, timestamp, userMessage, fileCount, linesAdded, linesRemoved,
  backupFiles, files{<hex>: {path, linesAdded, linesRemoved, preimage,
  postimage}}}]}`, with `preimage{kind}` and `postimage{kind,
  contentHash (sha256 hex), encodedPath{data, encoding}, resolvedPath}`
  (real installs; the removed `~/secret` project's snapshot still names
  its file under `/home/sean/secret`; `runtime.node@82575983`
  `rewind-file-snapshotstracking.json`). A rewind prunes the discarded
  turns' snapshots (`runtime.node@82545128` `Failed to prune a
  withdrawn turn's file snapshot`).
- `permissions-config.json` `{locations: {<abs path>: {tool_approvals:
  [{kind, ...}], allowed_directories: [...]}}}`; `kind` `commands`
  (`commandIdentifiers`), `read`, `write`, `mcp` (`serverName`,
  `toolName`), `mcp-sampling`, `memory`, `custom-tool`,
  `extension-management`, `workflow`, `extension-permission-access`,
  `extension-env-access` (docs; `runtime.node@82849044`; observed two
  locations with `write` entries on macOS, and one, `~/demo`, with one
  `write` entry and no `allowed_directories` key on Linux).
- `settings.json`: `allowedUrls` and `deniedUrls`, "URLs or domains allowed
  without prompting" (`runtime.node@79085397`); observed four
  `allowedUrls` on macOS; not written on the Linux install. JSON with
  comments (docs).
- `logs/process-*.log`: `<ISO ms Z> [LEVEL] <message>`. `Signed in to
  <host> as <login>.` (`cli-main.js@7556306`) names the account; `Session
  named: "<name>"`, `Starting Copilot CLI: <version>`
  (`cli-main.js@8163060`), `Workspace initialized: <uuid>`. Also seen on
  Linux (ids redacted): `Node.js version: v<n>`, `Login status unknown`,
  `Workspace initialized: <uuid> (checkpoints: 0)`, `Registering
  foreground session: <uuid>` and `Unregistering ...`, `Remote session
  access enabled`, `Session indexing debug: SESSION_INDEXING=true,
  repository=undefined`, `[rust:model_bindings::api_resolver] Using
  default model: gpt-6.1-sol`, `[managedSettings] device MDM: no policy
  present on this device` (MDM is mobile device management, an
  organisation's policy push), `[managedSettings] self-fetch starting for
  account https://github.com/<login>`, `[rust:rmcp::service] Service
  initialized as client` for the `github-mcp-server` remote MCP server,
  `Memory enablement check: enabled` and `Starting graceful shutdown of
  CLI server`. The login appears twice, in the sign-in line and the
  managed-settings line. On the Windows winget install (1.0.98) also
  `Remote session access disabled` (before the login) and `enabled` (a
  resumed process), `Unregistering foreground session: <uuid>`, `Closing
  session <uuid>`, `Closed interrupted sub-agent records on resume
  {"closed":0,"dangling":0}`, `Destroying 0 active sessions` and
  `[rust:rmcp::service] Service initialized as client` with no MCP server
  configured; no line records a session deleted with `/session delete`.
  A log rotates at 10 MB to `process-<epoch ms>-<pid>.<n>.log` (`.1` to
  `.4` observed there, while a pending login looped; [section 1 of
  `collectors/research/copilot-cli.md`](../../collectors/research/copilot-cli.md#1-source-and-evidence-level)).
  The parser's pattern (`process-\d+-\d+\.log`, [section 8](#8-parser-plan))
  does not select the rotated files, so a sign-in line that rotated out
  would not be read ([issue 152](https://github.com/seanthegeek/doubleagent/issues/152));
  on that install the four `signed in:` rows came from the unrotated
  logs.

## 6. Format versions

`session.start.data.version` 1 and `producer` `copilot-agent` on every
observed log. Several fields are "Absent on historical events"
(`permissionMode`, `ownerSessionId`) or absent "on completions recorded
before this field existed" (`decisionSource`, `schema@504557`), so older
logs lack them. Earlier builds wrote a flat `session-state/<session
id>.jsonl`; 1.0.98 refuses to resume one (`cli-main.js@1698895` `uses a
legacy flat JSONL transcript format that is no longer supported`;
`cli-main.js@1654639` `Rwr=".jsonl"`) and the reindex skips it. Its
record shape is not in this bundle. The schema allows no extra keys
(`additionalProperties: false`), yet the install carried `shellType` and
`allowMatchIdentifier`, so the file is a superset of the published
schema. `session-store.db` migrates through `schema_version`: 38 on
the macOS install and 8 on the Linux install, both 1.0.98 and both with
the tables of [section 5](#5-sqlite-and-other-stores); neither number is
explained (the Windows install's bundled 1.0.99-2 also had 8);
`rewind-file-snapshots` and `sidebar-sessions-state` carry
their own `schema` and `schemaVersion` numbers.

## 7. Secrets

`system.message.content` is the full system prompt with the user's custom
instructions; `transformedContent` repeats each prompt with injected
context. Tool arguments and results are verbatim (shell output, fetched
pages), and a `write` permission request carries the `diff` and
`newFileContents` of the file. `encryptedContent`, `reasoningOpaque` and
`reasoningBlocks[].encrypted_content` are opaque provider blobs
("Session-bound and stripped on resume", `schema@29947`); `apiCallId` (500
characters observed) is the provider's response id, and `usageId`,
`request_id` and `service_request_id` are request ids, none a credential.
`model_call_success.quotaSnapshots` records the account's plan
entitlements. The log's sign-in line names the GitHub login. No token was
seen in a session file; the token is in the OS keychain (the GNOME
keyring on the Linux install) or, with the plaintext fallback, in
`config.json` (JSONC, JSON after `//` comment lines; on Linux it held only
account keys; already a secret glob). `mcp-config.json` can hold a
token in plain text in a server's `env`: on the Windows install the
`github` server's `env` held a GitHub personal access token; the file is
not parsed and the collector flags it `secret: true`. `/chronicle reindex`
also uploads the sessions to the account (docs: "Reindexing also syncs
your session data to your account").

## 8. Parser plan

`wants()` by `artifact.rel`, with `(?:\.copilot|\.local/state/\.copilot|\.config/\.copilot)`
written `<home>`:

```text
^<home>/session-state/[0-9a-f-]{36}/events\.jsonl$
^<home>/session-state/[0-9a-f-]{36}/workspace\.yaml$
^<home>/session-state/[0-9a-f-]{36}/rewind-file-snapshots/index\.json$
^<home>/session-store\.db$
^<home>/command-history-state\.json$
^<home>/permissions-config\.json$
^<home>/settings\.json$
^<home>/sidebar-sessions-state/[0-9a-f]{64}\.json$
^<home>/logs/process-\d+-\d+\.log$
```

`secondary()` is true for `session-store.db`, `command-history-state.json`
and `rewind-file-snapshots/index.json`. `secondary_tolerance()` is 3600
seconds for the first and the last: `turns.timestamp` is written at the end
of the turn (4 to 293 seconds after the prompt observed, and a turn with
many tools can run longer), and the snapshot time was not measured against
the prompt's, so both get the one-hour window `letta` uses.

`events.jsonl` is read with `iter_jsonl`; each bad line is its own
`system` row, `parser: unparseable line (<reason>): <line>` with the line
in full (issue 136), and reading continues. Rows follow the log order, timestamped by the
line's `timestamp`.

| Record | `turn_type` and text |
| --- | --- |
| `session.start` | `system`, `session start: copilot <copilotVersion> producer=<producer> cwd=<context.cwd>`; fills `session_id`, `project_path`, `git_branch` (`context.branch`) |
| `session.resume` | `system`, `session resumed`; updates cwd and branch from `context` |
| `session.context_changed` | no row; updates `project_path` and `git_branch` |
| `system.message` | `system`, `system prompt: <content>` (`role` `developer`: `developer message:`), never shortened |
| `user.message`, no `agentId`, `source` absent or `user`, not `isAutopilotContinuation` | `user`, `content` |
| `user.message`, other | `system`, `<label>: <content>`: `auto-continuation` for `isAutopilotContinuation`, `subagent task` with `agentId`, otherwise the `source` value |
| `assistant.message` | `assistant` with `content` when non-empty; then `thinking` with `reasoningText` (only with `include_thinking`; else the summaries joined from `reasoningBlocks.blocks[].summary[].text`); then one `tool_use` per `toolRequests[]` |
| `assistant.reasoning` | `thinking`, `content` (only with `include_thinking`) |
| `tool.execution_start` | no row when an earlier `toolRequests[]` had the `toolCallId`; otherwise `tool_use` (a user-requested or subagent call) |
| `tool.user_requested` | `tool_use`, prefixed `user requested: ` |
| `tool.execution_complete` | `tool_result`: the longer of `result.detailedContent` and `result.content`, `detailedContent` on a tie (it is the complete text, but a successful skill invocation puts the concise text there: one observed record had 25 characters in `detailedContent` beside 8091 in `content`); prefixed `[exit N] ` when `shellExecution.exitCode` is non-zero; `error.message` appended on a new line when `success` is false |
| `permission.requested` | `system`, `permission request: <permissionRequest.kind> <fullCommandText, url, fileName, path or serverName/toolName> intention=<intention>`, `tool_use_id` `permissionRequest.toolCallId`; first `permissionMode` and `agentMode` give `permission mode: <permissionMode> agent=<agentMode>`, a change gives `permission mode: <old> -> <new>` |
| `permission.completed` | `system`, `permission decision: <result.kind> source=<decisionSource or ->`, then ` location=<locationKey>`, ` approval=<compact JSON of approval>`, ` directories=...`, ` feedback=<feedback>`, ` rules=<compact JSON>`, ` reason=<reason>`, ` path=<path>`, ` message=<message>` when present; `tool_use_id` `toolCallId` |
| `permission.carriedForward` | `system`, `permission decision: carried-forward source=<decisionSource>` |
| `session.permissions_changed` / `session.mode_changed` | `system`, `permission mode: <previousMode> -> <mode>` / `agent mode: <previousMode> -> <newMode>`; the Copilot Desktop app's form (`previousAllowAllPermissions`, `allowAllPermissions`, `previousAllowAllPermissionMode`, `allowAllPermissionMode`, no `mode` and no `previousMode`; real installs, Linux, bundled CLI 1.0.95-3, and Windows, 1.0.99-2) is `permission mode: allow-all <previousAllowAllPermissionMode or -> -> <allowAllPermissionMode or ->`, and the tracked mode becomes `allow-all <allowAllPermissionMode>` |
| `session.model_change` | `system`, `model: <newModel>` at the first, `model: <old> -> <newModel>` on a change, kept when equal; followed by ` cause=<cause> source=<source> effort=<reasoningEffort>` for the keys present |
| `session.auto_mode_resolved` | `system`, `model: <old> -> <chosenModel> (auto, <routingMethod>)` |
| `session.info` | `system`, `session.info <infoType>: <message>`, then ` url=<url>` and ` tip=<tip>` for the keys present, at the line's `timestamp`; `model` the tracked model, `tool_name` and `tool_use_id` empty |
| `model.message` | `system`, `utility model <modelCall.model>: <message.content>`, `model` that model; never changes the session model |
| other `model.*` | skip (the prompt snapshot, the ExP string and call bookkeeping) |
| `session.compaction_complete` | `system`, `compaction summary: <summaryContent>` |
| `abort`, `session.error`, `session.warning` | `system`, `<type>: <reason or message>` |
| `session.task_complete`, `system.notification`, `session.schedule_created`, `skill.invoked`, `subagent.*`, `session.handoff` | `system`, `<type>: ` and the main text field, else compact JSON |
| `hook.start` / `hook.end` | `system`, `hook <hookType> start: <compact JSON of input, or {}>` / `hook <hookType> end: success=<true or false> output=<compact JSON of output, or {}>`, then ` error=<compact JSON>` when `error` is present; `-` for a missing `hookType` or a non-boolean `success`; `tool_use_id` `parentToolCallId` when present, `tool_name` empty; never shortened |
| `session.shutdown` | `system`, `session end: <shutdownType> <errorReason> files modified: <codeChanges.filesModified>` |
| `assistant.turn_*`, `session.usage_record`, `session.usage_checkpoint`, unknown types | skip |

The `model` column is `assistant.message.model` or the tool event's
`model`, else the model tracked from `session.model_change`.

A `/model` command the user types is not a `user.message`: the log keeps
only its `session.model_change` and `session.info` lines, and the command
itself survives only as an entry of `command-history-state.json`, which
no other source repeats, so deduplication keeps it as an undated `user`
row (Linux install).

Other files:

| File | Rows |
| --- | --- |
| `session-store.db` `turns` | `user` from `user_message` and `assistant` from `assistant_response` when not null; `timestamp`, `session_id`, `project_path` and `git_branch` from `sessions`; `source_line` the rowid |
| `session-store.db` `sessions` | `system`, `session name: <summary>` at `created_at` |
| `session-store.db` `session_files` / `session_refs` | `system`, `file changed: <file_path> tool=<tool_name>` at `first_seen_at` / `reference: <ref_type> <ref_value>` at `created_at` |
| `session-store.db` `checkpoints` | `system`, `checkpoint <n>: <title>` and each non-null column on its own line, at `created_at` |
| `session-store.db` `forge_trajectory_events` | `tool_use` (`command`) and `tool_result` (`output`, `[exit N]`) joined on `tool_call_id` (empty table observed; unverified) |
| `search_index`, `assistant_usage_events`, `forge_skill_proposals`, `dynamic_context_items` | none: concatenated copies, accounting, or no session |
| `command-history-state.json` | `user` per entry, empty `timestamp_utc`, `session_id` and `project_path`; `source_line` the 1-based index (newest first) |
| `rewind-file-snapshots/index.json` | `user` from `userMessage` at `timestamp`; and `system`, `rewind snapshot: <fileCount> files +<linesAdded> -<linesRemoved>: <path>, ...` |
| `workspace.yaml` | `system`, `session name: <name>` and `session metadata: user_named=<user_named> forks=<fork_count> compactions=<summary_count> client=<client_name>` at `created_at` (`client=` empty when the key is absent; `github/cli` for the CLI, `github/autopilot` for the Copilot Desktop app); `cwd` is the session's project fallback |
| `permissions-config.json` | one `system` row per `tool_approvals` and `allowed_directories` entry: `permission setting: locations.<path>.tool_approvals=<compact JSON> (from .copilot/permissions-config.json, file mtime)`, `project_path` the location, timestamp the file's mtime, empty `session_id` |
| `settings.json` | one `system` row per `allowedUrls` and `deniedUrls` entry, `permission setting: allowedUrls=<url> (from .copilot/settings.json, file mtime)`; strip comments before parsing |
| `sidebar-sessions-state/*.json` | none; `cwd` per `sessionIds[]` fills `project_path` of database and snapshot rows that lack one |
| `logs/process-*.log` | `system`, `signed in: <host> as <login>` at the line's time; `session_id` from `Workspace initialized: <uuid>` when the file names exactly one |

Sync: `workspace.yaml` `remote_steerable` and the three `mc_` keys
(`mc_task_id`, `mc_session_id`, `mc_last_event_id`) mark a session
synced to the account through Mission Control: added at a resume on the
Windows winget install (1.0.98) and present in every Copilot Desktop
session (Linux 1.1.29, Windows 1.1.30). The parser does not yield a row
for them yet ([issue 151](https://github.com/seanthegeek/doubleagent/issues/151)).
The planned form is one `system` row after the `session metadata:` row,
`session synced: remote session <mc_session_id> task <mc_task_id or ->
last event <mc_last_event_id or -> remote_steerable=<remote_steerable or
-> (from workspace.yaml, file mtime)`, timestamped by the file's
modification time, a key present with an empty value printed `-`; a
`synced` field last in each `sessions.jsonl` record, a string with three
values: `yes` when the session has that row, `no` when the agent's parser
records sync state (`copilot-cli`, whose rows include the Copilot Desktop
sessions) and the session has none, and empty when the agent's parser
records no sync state, so nothing is known; and a `synced_sessions`
count in `inventory.json`, at the top level and in each
`homes[].agents[]` entry. A session deleted locally and remotely leaves
no marker anywhere on disk: the keys live only in its `workspace.yaml`.

MCP: the configured servers (`mcp-config.json`), their failed spawns
(the process log's `MCP server connection failed` lines) and the cached
tool lists (`AppData/Local/copilot/mcp-tools/<sha256>.json`) are recorded
on disk (Windows install) and not yet in the timeline ([issue 150](https://github.com/seanthegeek/doubleagent/issues/150)).

The `sessions` row and the `workspace.yaml` row share the `session name:`
form so the database copy drops when the two agree; the metadata is a row
of its own so that the name rows can match. The `workspace.yaml` rows are
not secondary.

Columns:

| Column | Source |
| --- | --- |
| timestamp_utc | line `timestamp`; database columns as stored |
| session_id | the directory name (= `session.start.sessionId`); `session_id` columns |
| project_path | latest `context.cwd`, else `workspace.yaml` `cwd`, else `sessions.cwd`, else `sidebar-sessions-state` |
| git_branch | latest `context.branch`, else `sessions.branch`; empty when neither is set |
| model | as above |
| tool_name | `toolRequests[].name` or `toolName`; on results and permission rows, the name remembered for the `toolCallId` |
| tool_use_id | `toolCallId` |
| text | coverage tables; a `tool_use` text is the `arguments` string, else `command`, `url`, `query`, `path` or `input`, else compact JSON |
| source_line | 1-based line, or array index, or rowid |

Sample fixture
`.copilot/session-state/5e55a0a1-0000-4000-8000-000000000001/events.jsonl`
(synthetic; start, model, system prompt, prompt, utility call, reasoning
and a `bash` request, a location approval, a failed run, an `apply_patch`
request approved once, a final reply, usage, the Linux round's `/model`
switch to Auto with its two `session.info` lines, shutdown, then a cut
line):

```json
{"id":"e0000000-0000-4000-8000-000000000001","parentId":null,"timestamp":"2026-10-01T09:00:00.000Z","type":"session.start","data":{"sessionId":"5e55a0a1-0000-4000-8000-000000000001","version":1,"producer":"copilot-agent","copilotVersion":"1.0.98","startTime":"2026-10-01T08:59:59.000Z","context":{"cwd":"/srv/proj","gitRoot":"/srv/proj","branch":"main"},"alreadyInUse":false,"remoteSteerable":false,"contextTier":null}}
{"id":"e0000000-0000-4000-8000-000000000002","parentId":"e0000000-0000-4000-8000-000000000001","timestamp":"2026-10-01T09:00:00.100Z","type":"session.model_change","data":{"newModel":"gpt-6.1-sol","cause":"initial_resolution","source":"automatic","reasoningEffort":"medium","contextTier":null}}
{"id":"e0000000-0000-4000-8000-000000000003","parentId":"e0000000-0000-4000-8000-000000000002","timestamp":"2026-10-01T09:00:01.000Z","type":"system.message","data":{"content":"You are the GitHub Copilot CLI.\nFollow the user's instructions.","role":"system","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","metadata":{"variables":{"gitCommitTrailer":{"clientName":"copilot-cli","coauthorEnabled":true,"sessionId":"5e55a0a1-0000-4000-8000-000000000001"}}}}}
{"id":"e0000000-0000-4000-8000-000000000004","parentId":"e0000000-0000-4000-8000-000000000003","timestamp":"2026-10-01T09:00:01.200Z","type":"user.message","data":{"content":"fix the failing test","transformedContent":"<current_datetime>2026-10-01T09:00:01Z</current_datetime>\nfix the failing test","messageId":"2b2b2b2b-0000-4000-8000-000000000001","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","parentAgentTaskId":"3c3c3c3c-0000-4000-8000-000000000001","turnId":"0","delivery":"idle","responsesReasoning":{"effort":"medium","initialEffort":"medium","model":"gpt-6.1-sol"},"supportedNativeDocumentMimeTypes":[]}}
{"id":"e0000000-0000-4000-8000-000000000005","parentId":"e0000000-0000-4000-8000-000000000004","timestamp":"2026-10-01T09:00:01.300Z","type":"assistant.turn_start","data":{"interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"0"}}
{"id":"e0000000-0000-4000-8000-000000000006","parentId":null,"timestamp":"2026-10-01T09:00:01.400Z","type":"model.turn_started","data":{"kind":"turn_started","model":"gpt-4o-mini","modelInfo":{"id":"gpt-4o-mini","name":"GPT-4o mini","object":"model","version":"gpt-4o-mini-2024-07-18","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}},"timestampMs":1790845201400,"turn":0}}
{"id":"e0000000-0000-4000-8000-000000000007","parentId":"e0000000-0000-4000-8000-000000000006","timestamp":"2026-10-01T09:00:01.410Z","type":"model.model_call_started","data":{"kind":"model_call_started","model":"gpt-4o-mini","modelInfo":{"id":"gpt-4o-mini","name":"GPT-4o mini","object":"model","version":"gpt-4o-mini-2024-07-18","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}},"timestampMs":1790845201410,"turn":0}}
{"id":"e0000000-0000-4000-8000-000000000008","parentId":"e0000000-0000-4000-8000-000000000007","timestamp":"2026-10-01T09:00:01.420Z","type":"model.messages_snapshot","data":{"kind":"messages_snapshot","messages":[{"role":"system","content":"Generate a session title for this message."},{"role":"user","content":"fix the failing test"}]}}
{"id":"e0000000-0000-4000-8000-000000000009","parentId":"e0000000-0000-4000-8000-000000000008","timestamp":"2026-10-01T09:00:01.430Z","type":"model.captured_assignment_context","data":{"kind":"captured_assignment_context","assignmentContext":"exp-a:1;exp-b:0;"}}
{"id":"e0000000-0000-4000-8000-000000000010","parentId":"e0000000-0000-4000-8000-000000000009","timestamp":"2026-10-01T09:00:02.000Z","type":"model.message","data":{"callId":"4d4d4d4d-0000-4000-8000-000000000001","kind":"message","message":{"apiCallId":"chatcmpl-0001","content":"Fix failing test","outputTokens":4,"providerId":"copilot","refusal":null,"role":"assistant"},"modelCall":{"api_endpoint":"/chat/completions","api_id":"chatcmpl-0001","client_request_id":"req-0001","initiator":"agent","model":"gpt-4o-mini","request_id":"5f5f5f5f-0000-4000-8000-000000000001","rte":false,"service_request_id":"6a6a6a6a-0000-4000-8000-000000000001","transport":"http"},"turn":0}}
{"id":"e0000000-0000-4000-8000-000000000011","parentId":"e0000000-0000-4000-8000-000000000010","timestamp":"2026-10-01T09:00:02.010Z","type":"model.response","data":{"callId":"4d4d4d4d-0000-4000-8000-000000000001","kind":"response","modelCall":{"api_id":"chatcmpl-0001","model":"gpt-4o-mini"},"response":{"content":"Fix failing test","providerId":"copilot","refusal":null,"role":"assistant"},"turn":0}}
{"id":"e0000000-0000-4000-8000-000000000012","parentId":"e0000000-0000-4000-8000-000000000011","timestamp":"2026-10-01T09:00:02.020Z","type":"model.model_call_success","data":{"callId":"4d4d4d4d-0000-4000-8000-000000000001","kind":"model_call_success","modelCall":{"api_endpoint":"/chat/completions","api_id":"chatcmpl-0001","client_request_id":"req-0001","initiator":"agent","model":"gpt-4o-mini","request_id":"5f5f5f5f-0000-4000-8000-000000000001","rte":false,"service_request_id":"6a6a6a6a-0000-4000-8000-000000000001","transport":"http"},"modelCallDurationMs":590,"modelDisplayName":"GPT-4o mini","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}}}
{"id":"e0000000-0000-4000-8000-000000000013","parentId":"e0000000-0000-4000-8000-000000000012","timestamp":"2026-10-01T09:00:02.030Z","type":"model.turn_ended","data":{"kind":"turn_ended","model":"gpt-4o-mini","modelInfo":{"id":"gpt-4o-mini","name":"GPT-4o mini","object":"model","version":"gpt-4o-mini-2024-07-18","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}},"timestampMs":1790845202030,"turn":0}}
{"id":"e0000000-0000-4000-8000-000000000014","parentId":"e0000000-0000-4000-8000-000000000013","timestamp":"2026-10-01T09:00:03.000Z","type":"assistant.message","data":{"content":"","messageId":"7b7b7b7b-0000-4000-8000-000000000001","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","originatingMessageId":"2b2b2b2b-0000-4000-8000-000000000001","model":"gpt-6.1-sol","providerId":"copilot","turnId":"0","reasoningText":"Run the tests first.","reasoningOpaque":"rs_AAAA","encryptedContent":"gAAAAA","reasoningBlocks":{"provider":"openai-responses","blocks":[{"type":"reasoning","id":"rs_AAAA","summary":[{"type":"summary_text","text":"Run the tests first."}],"encrypted_content":"gAAAAA"}]},"apiCallId":"resp_0001","rte":false,"serverTools":{"provider":"openai-responses"},"toolRequests":[{"type":"function","name":"bash","toolCallId":"call_01","toolTitle":"Run shell command","arguments":{"command":"npm test","description":"Run the test suite"},"intentionSummary":"Run the test suite"}]}}
{"id":"e0000000-0000-4000-8000-000000000015","parentId":"e0000000-0000-4000-8000-000000000014","timestamp":"2026-10-01T09:00:03.100Z","type":"permission.requested","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000001","ownerSessionId":"5e55a0a1-0000-4000-8000-000000000001","agentMode":"interactive","permissionMode":"manual","permissionRequest":{"kind":"shell","toolCallId":"call_01","intention":"Run the test suite","fullCommandText":"npm test","shellType":"bash","commands":[{"identifier":"npm test","readOnly":false,"allowMatchIdentifier":"npm test"}],"commandSegments":[{"identifier":"npm test","fullCommandText":"npm test"}],"possiblePaths":[],"possibleUrls":[],"hasWriteFileRedirection":false,"canOfferSessionApproval":true},"promptRequest":{"kind":"commands","toolCallId":"call_01","intention":"Run the test suite","fullCommandText":"npm test","commandIdentifiers":["npm test"]}}}
{"id":"e0000000-0000-4000-8000-000000000016","parentId":"e0000000-0000-4000-8000-000000000015","timestamp":"2026-10-01T09:00:06.000Z","type":"permission.completed","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000001","toolCallId":"call_01","decisionSource":"human_response","result":{"kind":"approved-for-location","locationKey":"/srv/proj","approval":{"kind":"commands","commandIdentifiers":["npm test"]}}}}
{"id":"e0000000-0000-4000-8000-000000000017","parentId":"e0000000-0000-4000-8000-000000000016","timestamp":"2026-10-01T09:00:06.100Z","type":"tool.execution_start","data":{"toolCallId":"call_01","toolName":"bash","toolTitle":"Run shell command","arguments":{"command":"npm test","description":"Run the test suite"},"model":"gpt-6.1-sol","turnId":"0"}}
{"id":"e0000000-0000-4000-8000-000000000018","parentId":"e0000000-0000-4000-8000-000000000017","timestamp":"2026-10-01T09:00:08.000Z","type":"tool.execution_complete","data":{"toolCallId":"call_01","success":false,"result":{"content":"1 failing","detailedContent":"1 failing\n  date.test.js: expected 2026"},"error":{"code":"failure","message":"Command exited with code 1"},"shellExecution":{"exitCode":1},"toolTelemetry":{"metrics":{},"properties":{}},"model":"gpt-6.1-sol","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"0","rte":false}}
{"id":"e0000000-0000-4000-8000-000000000019","parentId":"e0000000-0000-4000-8000-000000000018","timestamp":"2026-10-01T09:00:08.100Z","type":"assistant.turn_end","data":{"turnId":"0"}}
{"id":"e0000000-0000-4000-8000-000000000020","parentId":"e0000000-0000-4000-8000-000000000019","timestamp":"2026-10-01T09:00:08.200Z","type":"assistant.turn_start","data":{"interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"1"}}
{"id":"e0000000-0000-4000-8000-000000000021","parentId":"e0000000-0000-4000-8000-000000000020","timestamp":"2026-10-01T09:00:10.000Z","type":"assistant.message","data":{"content":"","messageId":"7b7b7b7b-0000-4000-8000-000000000002","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","originatingMessageId":"2b2b2b2b-0000-4000-8000-000000000001","model":"gpt-6.1-sol","providerId":"copilot","turnId":"1","apiCallId":"resp_0002","rte":false,"toolRequests":[{"type":"custom","name":"apply_patch","toolCallId":"custom_0000000000000000000000000001","toolTitle":"Apply patch","arguments":"*** Begin Patch\n*** Update File: /srv/proj/date.test.js\n-2025\n+2026\n*** End Patch\n","intentionSummary":"Update the fixture year"}]}}
{"id":"e0000000-0000-4000-8000-000000000022","parentId":"e0000000-0000-4000-8000-000000000021","timestamp":"2026-10-01T09:00:10.100Z","type":"permission.requested","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000002","ownerSessionId":"5e55a0a1-0000-4000-8000-000000000001","agentMode":"interactive","permissionMode":"manual","permissionRequest":{"kind":"write","toolCallId":"custom_0000000000000000000000000001","intention":"Update the fixture year","fileName":"/srv/proj/date.test.js","diff":"-2025\n+2026\n","canOfferSessionApproval":true},"promptRequest":{"kind":"write","toolCallId":"custom_0000000000000000000000000001","intention":"Update the fixture year","fileName":"/srv/proj/date.test.js"}}}
{"id":"e0000000-0000-4000-8000-000000000023","parentId":"e0000000-0000-4000-8000-000000000022","timestamp":"2026-10-01T09:00:12.000Z","type":"permission.completed","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000002","toolCallId":"custom_0000000000000000000000000001","decisionSource":"human_response","result":{"kind":"approved"}}}
{"id":"e0000000-0000-4000-8000-000000000024","parentId":"e0000000-0000-4000-8000-000000000023","timestamp":"2026-10-01T09:00:12.100Z","type":"tool.execution_start","data":{"toolCallId":"custom_0000000000000000000000000001","toolName":"apply_patch","toolTitle":"Apply patch","arguments":{"input":"*** Begin Patch\n*** Update File: /srv/proj/date.test.js\n-2025\n+2026\n*** End Patch\n"},"model":"gpt-6.1-sol","turnId":"1"}}
{"id":"e0000000-0000-4000-8000-000000000025","parentId":"e0000000-0000-4000-8000-000000000024","timestamp":"2026-10-01T09:00:12.500Z","type":"tool.execution_complete","data":{"toolCallId":"custom_0000000000000000000000000001","success":true,"result":{"content":"Modified 1 file: /srv/proj/date.test.js"},"toolTelemetry":{"metrics":{},"properties":{}},"model":"gpt-6.1-sol","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"1","rte":false}}
{"id":"e0000000-0000-4000-8000-000000000026","parentId":"e0000000-0000-4000-8000-000000000025","timestamp":"2026-10-01T09:00:12.600Z","type":"assistant.turn_end","data":{"turnId":"1"}}
{"id":"e0000000-0000-4000-8000-000000000027","parentId":"e0000000-0000-4000-8000-000000000026","timestamp":"2026-10-01T09:00:12.700Z","type":"assistant.turn_start","data":{"interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"2"}}
{"id":"e0000000-0000-4000-8000-000000000028","parentId":"e0000000-0000-4000-8000-000000000027","timestamp":"2026-10-01T09:00:15.000Z","type":"assistant.message","data":{"content":"The fixture year was stale; it now reads 2026.","messageId":"7b7b7b7b-0000-4000-8000-000000000003","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","originatingMessageId":"2b2b2b2b-0000-4000-8000-000000000001","model":"gpt-6.1-sol","providerId":"copilot","turnId":"2","phase":"final_answer","apiCallId":"resp_0003","rte":false,"toolRequests":[]}}
{"id":"e0000000-0000-4000-8000-000000000029","parentId":"e0000000-0000-4000-8000-000000000028","timestamp":"2026-10-01T09:00:15.100Z","type":"assistant.turn_end","data":{"turnId":"2"}}
{"id":"e0000000-0000-4000-8000-000000000030","parentId":"e0000000-0000-4000-8000-000000000029","timestamp":"2026-10-01T09:00:15.200Z","type":"session.usage_record","data":{"usage":{"model":"gpt-6.1-sol","inputTokens":900,"outputTokens":40,"initiator":"agent","interactionType":"conversation-agent","apiEndpoint":"ws:/responses","transport":"websocket","isByok":false,"accounting":{"sequence":1,"sourceSessionId":"5e55a0a1-0000-4000-8000-000000000001","usageId":"u-0001"}}}}
{"id":"e0000000-0000-4000-8000-000000000031","parentId":"e0000000-0000-4000-8000-000000000030","timestamp":"2026-10-01T09:00:20.000Z","type":"session.model_change","data":{"previousModel":"gpt-6.1-sol","newModel":"auto","previousReasoningEffort":"medium","reasoningEffort":null,"contextTier":null,"source":"model_picker"}}
{"id":"e0000000-0000-4000-8000-000000000032","parentId":"e0000000-0000-4000-8000-000000000031","timestamp":"2026-10-01T09:00:20.395Z","type":"session.info","data":{"message":"Model changed from GitHub Copilot • GPT-6.1 Sol (medium) to GitHub Copilot • Auto for this session","infoType":"model"}}
{"id":"e0000000-0000-4000-8000-000000000033","parentId":"e0000000-0000-4000-8000-000000000032","timestamp":"2026-10-01T09:00:20.396Z","type":"session.info","data":{"message":"Auto routing profile change to Balance requested.","infoType":"model"}}
{"id":"e0000000-0000-4000-8000-000000000034","parentId":"e0000000-0000-4000-8000-000000000033","timestamp":"2026-10-01T09:00:30.000Z","type":"session.shutdown","data":{"shutdownType":"routine","sessionStartTime":1790845199000,"totalApiDurationMs":9000,"eventsFileSizeBytes":20000,"codeChanges":{"filesModified":["/srv/proj/date.test.js"],"linesAdded":1,"linesRemoved":1},"modelMetrics":{},"currentModel":"gpt-6.1-sol"}}
{"id":"e0000000-0000-4000-8000-000000000035","parentId":"e0000000-0000-4000-8000-000000000034","timestamp":"2026-10-01T09:01:00.000Z","type":"user.message","data":{"content":"and run
```

`session-store.db`:

```sql
INSERT INTO sessions VALUES ('5e55a0a1-0000-4000-8000-000000000001', '/srv/proj', NULL, NULL, NULL, 'Fix failing test', '2026-10-01T09:00:00.000Z', '2026-10-01T09:00:30.000Z');
INSERT INTO turns (session_id, turn_index, user_message, assistant_response, timestamp) VALUES ('5e55a0a1-0000-4000-8000-000000000001', 0, 'fix the failing test', 'The fixture year was stale; it now reads 2026.', '2026-10-01T09:00:15.200Z');
INSERT INTO turns (session_id, turn_index, user_message, assistant_response, timestamp) VALUES ('5e55a0a1-0000-4000-8000-000000000001', 1, 'and run lint', NULL, '2026-10-01T09:01:05.000Z');
INSERT INTO session_files (session_id, file_path, tool_name, turn_index, first_seen_at) VALUES ('5e55a0a1-0000-4000-8000-000000000001', '/srv/proj/date.test.js', 'apply_patch', 0, '2026-10-01T09:00:12.500Z');
```

`.copilot/session-state/5e55a0a1-0000-4000-8000-000000000001/workspace.yaml`:

```yaml
id: 5e55a0a1-0000-4000-8000-000000000001
cwd: /srv/proj
client_name: copilot-cli
name: Fix failing test
user_named: false
summary_count: 0
fork_count: 0
created_at: 2026-10-01T09:00:00.000Z
updated_at: 2026-10-01T09:00:30.000Z
remote_steerable: false
mc_task_id: null
mc_session_id: null
mc_last_event_id: null
```

`.copilot/command-history-state.json`:

```json
{"commandHistory":["and run lint","/model","fix the failing test"]}
```

`.copilot/permissions-config.json`:

```json
{"locations":{"/srv/proj":{"tool_approvals":[{"kind":"write"},{"kind":"commands","commandIdentifiers":["npm test"]}]}}}
```

`.copilot/settings.json`:

```json
{
  // user settings
  "allowedUrls": ["https://registry.example.org"]
}
```

`.copilot/session-state/5e55a0a1-0000-4000-8000-000000000001/rewind-file-snapshots/index.json`
(the snapshot taken before the first prompt, whose `eventId` is line 4's
`id`; the file key is a synthetic digest and the images are left out):

```json
{"schema":1,"snapshots":[{"snapshotId":"9d9d9d9d-0000-4000-8000-000000000001","eventId":"e0000000-0000-4000-8000-000000000004","timestamp":"2026-10-01T09:00:01.150Z","userMessage":"fix the failing test","fileCount":1,"linesAdded":1,"linesRemoved":1,"backupFiles":[],"files":{"a1a1a1a1a1a1a1a1":{"path":"/srv/proj/date.test.js","linesAdded":1,"linesRemoved":1,"preimage":null,"postimage":null}}}]}
```

`.copilot/sidebar-sessions-state/6b9af143446a411aefa3edb76e4693799bd7513e7ed8d919962d6713d3d3b972.json`
(the sha256 of `/srv/proj`):

```json
{"schemaVersion":1,"cwd":"/srv/proj","sessionIds":["5e55a0a1-0000-4000-8000-000000000001"]}
```

`.copilot/logs/process-1790845199000-4242.log`:

```text
2026-10-01T08:59:59.100Z [INFO] Starting Copilot CLI: 1.0.98
2026-10-01T08:59:59.400Z [INFO] Signed in to https://github.com as octo-user.
2026-10-01T08:59:59.900Z [INFO] Workspace initialized: 5e55a0a1-0000-4000-8000-000000000001
```

Noise the parser must not want: `.copilot/config.json`,
`.copilot/session-state/5e55a0a1-0000-4000-8000-000000000001/rewind-file-snapshots/tracking.json`
and `.copilot/session-state/5e55a0a1-0000-4000-8000-000000000001/checkpoints/index.md`.

Expected rows from `events.jsonl`: `system` session start (line 1, with
`project_path` `/srv/proj` and `git_branch` `main`); `system` `model:
gpt-6.1-sol cause=initial_resolution source=automatic effort=medium`
(line 2); `system` system prompt (line 3); `user` `fix the failing test`
(line 4); `system` `utility model gpt-4o-mini: Fix failing test` (line
10); `thinking` `Run the tests first.` with `include_thinking` (line 14);
`tool_use` `bash` `call_01` text `npm test` (line 14); `system`
`permission request: shell npm test intention=Run the test suite` and
`permission mode: manual agent=interactive` (line 15); `system`
`permission decision: approved-for-location source=human_response
location=/srv/proj approval={"commandIdentifiers":["npm test"],"kind":"commands"}`
(line 16); `tool_result` `call_01` text `[exit 1] 1 failing` and the
detail, then `Command exited with code 1` (line 18); `tool_use`
`apply_patch` (line 21); the write request and `permission decision:
approved source=human_response` (lines 22, 23); `tool_result` (line 25);
`assistant` reply (line 28); `system` `model: gpt-6.1-sol -> auto
source=model_picker` (line 31); `system` `session.info model: Model
changed from GitHub Copilot • GPT-6.1 Sol (medium) to GitHub Copilot •
Auto for this session` and `session.info model: Auto routing profile
change to Balance requested.` (lines 32, 33, `model` `auto`); `system`
session end (line 34); the bad-line `system` row (line 35). Six secondary rows drop: the snapshot's
prompt pairs with line 4 (the nearest in time), and the `turns` row 0
prompt, which loses that one-to-one match, collapses onto the snapshot's
copy; the row 0 reply pairs with line 28; the `sessions` row's `session
name: Fix failing test` pairs with the `workspace.yaml` row; the history's
`fix the failing test` pairs with line 4, and its `and run lint` collapses
onto the `turns` row 1, the only other copy of a prompt the cut log lost.
Kept: `turns` row 1 (`and run lint`), the history's `/model` (an undated
`user` row, in no other source), `file changed:
/srv/proj/date.test.js tool=apply_patch` and `rewind snapshot: 1 files +1
-1: /srv/proj/date.test.js`.

Confidence. High (schema and real install agree): the envelope, the
observed event types and keys, the permission result kinds, the
`toolCallId` join, the session-store schema and its SQL, the history
file's order, the WAL, the utility-call purposes. Medium (bundle only):
the unobserved event types, the denial and session-approval shapes,
subagent events in the same file, `forge_trajectory_events`, the
snapshot's timing. High since the Linux round: the `turns` write
pattern behind the repeated rows (complete row at the next prompt or at
shutdown, prompt-only row mid-turn), the `session.info` shape, the
`model_picker` change, and the Linux layout, which matches macOS.
`sessions.summary` holds the generated session name (Linux install).
Not determined: why `schema_version` is 8 on Linux and 38 on macOS on the same 1.0.98; the
legacy flat transcript's shape. The Windows layout was observed through
the Copilot Desktop app's bundled 1.0.99-2 and the winget install of
1.0.98 (2026-10-17), and matched Linux under `%USERPROFILE%` in both;
the winget round also exercised a denial, a resume, a session deleted
with the CLI's own command and subagent events, seen as listings and key
shapes only, since the delete took the session's `events.jsonl` before
the analyzer ran. Not determined: why the store kept 3 of 6 turns;
whether `permission.completed` nests `decisionSource` in `result` on
Windows. The npm-installed CLI on Windows is not observed
([issue 133](https://github.com/seanthegeek/doubleagent/issues/133)).
