# Record schema research

One document per catalog agent, named after the agent as it appears in
`collect-agent-artifacts.sh --list`, describing how that agent records
transcripts on disk and how a parser should read them. Each was written from
a shallow clone of the tool's source at the commit it names, with file and
line citations, or for a closed-source tool from the evidence named in its
first section (for Antigravity, the protobuf descriptors embedded in its
binary). Each ends with a parser plan mapped to the timeline columns and
synthetic sample records meant to become test fixtures. They are the
evidence behind each parser; the field names a parser depends on are
repeated in its module docstring under `doubleagent/parsers/`.

Forks of one codebase were often studied together, because the differences
are what matter, but each agent has its own document. Where two agents
share a lineage, each document says so and links to the other.

The first section of a document carries one **Observed** bullet per platform and
surface the agent has been run on, naming the build or version, the date,
what was exercised and what each surface wrote. That build is the version
the record shapes rest on: line types and key sets change between releases
(the rollouts of the ChatGPT desktop app's bundled Codex 0.163 carried
per-turn settings events, reviewer threads and turn triggers that the
document written from the 0.162 install did not list). Before
relying on a parser plan against an install, compare the install's build
with the latest Observed bullet for that platform and surface; when they
differ, or no bullet exists for the cell, the install gets a per-step round
([Real-install rounds in `AGENTS.md`](../../AGENTS.md#real-install-rounds))
and the shape tool's output is diffed against its storage and parser-plan sections before the
parser is changed.

| Agent | Document | Store | Parser |
| --- | --- | --- | --- |
| `agent-zero` | [agent-zero.md](agent-zero.md) | JSON per chat context, rewritten whole | yes |
| `aider` | [aider.md](aider.md) | markdown and readline-style text in the repository | yes |
| `antigravity` | [antigravity.md](antigravity.md) | SQLite of protobuf blobs per conversation, the same for the CLI (`.gemini/antigravity-cli`) and the desktop app (`.gemini/antigravity`); schema from the descriptors embedded in `agy` and the app's language server; verified on Linux (WSL: CLI; Ubuntu: CLI and app), macOS (CLI and app) and Windows (Windows 11 ARM64: CLI 1.3.5 and desktop app 2.23.1) installs | yes |
| `chatgpt-desktop` | [chatgpt-desktop.md](chatgpt-desktop.md) | no transcript: a ChatGPT conversation's text stays on the server; the app lists the account's conversations at sign-in as `chatgpt` rows of `~/.codex/sqlite/codex-dev.db` `local_thread_catalog` (WAL), while its Codex threads are `codex-cli` rollouts; closed source, from Windows and macOS installs | yes |
| `claude-code` | [claude-code.md](claude-code.md) | JSONL per session with `uuid`/`parentUuid` chains, subagent files beside it, prompt history | yes |
| `claude-desktop` | [claude-desktop.md](claude-desktop.md) | session records (JSON) and an HMAC-chained `audit.jsonl` per Cowork session around Claude Code JSONL transcripts; closed source, from the app bundle; verified on Windows, Linux and macOS installs | yes |
| `cline` | [cline.md](cline.md) | JSON arrays per task; SDK session files; SQLite indexes | yes |
| `codex-cli` | [codex-cli.md](codex-cli.md) | JSONL rollouts (`session_meta`, `response_item`, `event_msg`), optionally zstd-compressed | yes |
| `cody` | [cody.md](cody.md) | rows in the editor `state.vscdb`; JetBrains global-state JSON | yes |
| `continue` | [continue.md](continue.md) | JSON per session, session-level timestamps only | yes |
| `copilot-cli` | [copilot-cli.md](copilot-cli.md) | JSONL event log per session (`events.jsonl`) with a cross-session SQLite store (WAL) and a prompt history; closed source, from the shipped bundle's event schema and macOS and Linux installs, and on Windows a winget install and the CLI the Copilot Desktop app bundles | yes |
| `copilot-desktop` | [copilot-desktop.md](copilot-desktop.md) | SQLite app store `~/.copilot/data.db` (WAL) of accounts, projects, worktrees, workspaces, sessions, activity and schedules; the sessions themselves are Copilot CLI event logs; closed source, from the shipped binary and Linux and Windows installs | yes |
| `crush` | [crush.md](crush.md) | per-project SQLite (WAL), parts as a JSON array | yes |
| `gemini-cli` | [gemini-cli.md](gemini-cli.md) | JSONL with `$set`/`$patch`/`$rewindTo` operations | yes |
| `goose` | [goose.md](goose.md) | SQLite (WAL), `content_json` arrays | yes |
| `hermes` | [hermes.md](hermes.md) | SQLite (WAL) `state.db`, JSONL fallback transcripts | yes |
| `kilo-code` | [kilo-code.md](kilo-code.md) | OpenCode-style SQLite (`kilo.db`) | yes |
| `kiro` | [kiro.md](kiro.md) | Amazon Q CLI SQLite, one JSON blob per working directory; Kiro CLI unverified | yes, Amazon Q CLI only |
| `letta` | [letta.md](letta.md) | JSONL transcripts per agent and conversation, sessions index | yes |
| `little-coder` | [little-coder.md](little-coder.md) | pi session JSONL; prompt history as a JSON array | yes |
| `muse-code` | [muse-code.md](muse-code.md) | event-sourced JSONL per session and subagent; closed source, from the binary's strings, vendor skills and a real install | yes |
| `nanobot` | [nanobot.md](nanobot.md) | JSONL per session key under `sessions/<workspace-id>/` | yes |
| `ollama` | [ollama.md](ollama.md) | desktop-app SQLite (WAL) on macOS and Windows; REPL prompt history without times; no server-side transcripts | yes |
| `open-interpreter` | [open-interpreter.md](open-interpreter.md) | Codex rollout JSONL under `~/.openinterpreter` | yes, the Codex parser |
| `openclaw` | [openclaw.md](openclaw.md) | SQLite (WAL) per agent with JSON or zstd events, legacy JSONL | yes |
| `opencode` | [opencode.md](opencode.md) | SQLite (WAL) with JSON columns | yes |
| `openhands` | [openhands.md](openhands.md) | one JSON file per event per conversation, naive local timestamps | yes |
| `pearai` | [pearai.md](pearai.md) | Continue-fork session JSON, Roo-fork task files | yes |
| `pi` | [pi.md](pi.md) | JSONL session tree, header line with `cwd` | yes |
| `qwen-code` | [qwen-code.md](qwen-code.md) | JSONL, Claude-Code-like records with `cwd` and `gitBranch` | yes |
| `roo-code` | [roo-code.md](roo-code.md) | Cline task layout with Roo extensions | yes |
| `shellgpt` | [shellgpt.md](shellgpt.md) | one JSON message array per chat id in the temp dir | yes |
| `tabby` | [tabby.md](tabby.md) | server SQLite (WAL) `ee/db.sqlite`, event JSON logs | yes |
| `twinny` | [twinny.md](twinny.md) | rows in the editor `state.vscdb` | yes |
| `vscode` | [vscode.md](vscode.md) | VS Code chat sessions (Copilot Chat): JSONL mutation log, legacy JSON | yes |
| `zed` | [zed.md](zed.md) | SQLite with zstd-compressed JSON thread blobs | yes, needs `zstandard` |

The Parser column says whether `doubleagent/parsers/` has a parser for
the agent; the [agents page](../../docs/agents.md) lists the files each one
reads. `tools/check_research_links.py` at the repository root verifies the
citation links in these documents; see the
[collectors research index](../../collectors/research/README.md).

Findings that cut across agents:

- Only Claude Code, Codex CLI, Qwen Code, Antigravity, Hermes and Zed
  record a git branch, and Zed only at thread start. Every other store
  leaves `git_branch` empty.
- Per-message timestamps are missing in Continue sessions, Zed threads and
  Cline's legacy API history; those parsers inherit session-level times.
- OpenCode, Crush, Goose, Kilo, Antigravity and Zed's sidebar database run
  SQLite in WAL mode, so the `-wal` sidecar must be collected with the
  database. Amazon Q and Zed's `threads.db` use the rollback journal and copy
  cleanly alone.
- Credentials sit inside transcript databases for OpenCode, Kilo and Amazon
  Q; those files are collected unflagged and the keys to redact are listed
  under the "Secrets" heading (the seventh) of each document.

## Where transcripts live, and what survives

Each row says, for one agent, where its transcripts are stored and
whether they outlive deleting the project, which per-prompt history file
it keeps and what that file survives, where the working directory is
recorded, and what other copies of past use exist and what a delete
leaves. "Not stated" means the agent's document does not say, and the
link in each row opens that document's account of what survives. Parsed,
secondary and not parsed say whether the analyzer reads a file and as
what; [Secondary sources](../docs/output.md#secondary-sources) lists the
secondary sources per agent, and
[doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122)
is the design that shows each event once across them.

| Agent | Transcripts live in | Survives project deletion | Per-prompt history file | Working directory recorded | Second copy |
| --- | --- | --- | --- | --- | --- |
| `agent-zero` | install directory `usr/chats/<ctxid>/chat.json` | yes (projects are `usr/projects/<name>`, a separate place) | none | per chat `data.project` (a name) | The Telegram chat map (an entry with no chat marks a deleted chat), the shadow git of `usr` and the memory store outlive a delete; not parsed. [what survives](agent-zero.md#what-survives-a-delete) |
| `aider` | the project (git root): `.aider.chat.history.md` | no | `<repo>/.aider.input.history`: local time and text, no session; goes with the project; secondary. [what survives](aider.md#what-survives-a-delete) | implicit (the file's location) | `.aider.llm.history` (only with a flag), project-local like the transcript; secondary. [what survives](aider.md#what-survives-a-delete) |
| `antigravity` | home `~/.gemini/antigravity{,-cli}/conversations/<uuid>.db` | yes | CLI `history.jsonl`: prompt, time, workspace and conversation id (absent on a first prompt); secondary. [what survives](antigravity.md#what-survives-a-delete) | per conversation (workspace URIs) | The brain mirror `transcript_full.jsonl`, secondary; the summaries database, one row per conversation. [what survives](antigravity.md#what-survives-a-delete) |
| `chatgpt-desktop` | on OpenAI's servers only; the app's Codex-mode threads are `codex-cli` rollouts | not applicable: the conversations have no project, and their list is under the home | none | none (`cwd` is NULL on the `chatgpt` rows) | The account conversation list, the `chatgpt` rows of `codex-dev.db` `local_thread_catalog`; parsed. [what survives](chatgpt-desktop.md#what-survives) |
| `claude-code` | home `~/.claude/projects/<key>/<id>.jsonl` | yes | `~/.claude/history.jsonl`: text, time, project and session; usually outlives its transcript; secondary. [what survives](claude-code.md#what-survives-a-delete) | every record (`cwd`, `gitBranch`) | `jobs/<id>/parent-transcript.jsonl`, not parsed; imported copies in Hermes, Cline and CLAI outlive the transcript. [what survives](claude-code.md#what-survives-a-delete) |
| `claude-desktop` | app data `local-agent-mode-sessions/`; the Code tab uses `~/.claude/projects` | yes | none of its own; the Code tab uses Claude Code's | session record `cwd` and `userSelectedFolders`; JSONL `cwd` per record (a VM path in VM mode) | Per-session `audit.jsonl` (every message, permission events) and the record's `initialMessage`; secondary. [what survives](claude-desktop.md#what-survives-a-delete) |
| `cline` | VS Code `globalStorage` or `~/.cline/data/` | yes | CLI `cache/user_input_history.jsonl`: last 20 unique prompts, no session or cwd; survives a delete; secondary. [what survives](cline.md#what-survives-a-delete) | per task `cwdOnTaskInitialization`, manifest `cwd` | `session-search.db` until the hub next runs, secondary; `logs/hooks.jsonl` survives a delete, not parsed. [what survives](cline.md#what-survives-a-delete) |
| `codex-cli` | home `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | yes | `~/.codex/history.jsonl`: session, time and text; survives `thread/delete`; secondary. [what survives](codex-cli.md#what-survives-a-delete) | `session_meta.cwd`, updated per turn | `.codex-global-state.json` keeps a deleted thread's prompts and a deletion marker, secondary; memories and `db-backups/` not parsed. [what survives](codex-cli.md#what-survives-a-delete) |
| `cody` | the editor's `state.vscdb` or `Cody-nodejs/` | yes | none | none (inferred from `contextFiles`) | The JetBrains plugin's `<project>/.idea/cody_history.xml` outlives a delete or clear; not collected or parsed. [what survives](cody.md#what-survives-a-delete) |
| `continue` | `~/.continue/sessions/` | yes | CLI `input_history.json`: text and time, no session, up to 1000; survives a delete; not parsed. [what survives](continue.md#what-survives-a-delete) | per session `workspaceDirectory` | `dev_data/*.jsonl` events with the session id and `logs/cn.log` survive a delete; edit and feedback events not parsed. [what survives](continue.md#what-survives-a-delete) |
| `copilot-cli` | home `~/.copilot/session-state/<id>/events.jsonl` | yes | `command-history-state.json`: last 50 prompts, no time, session or cwd; survives a delete; secondary. [what survives](copilot-cli.md#what-survives-a-delete) | `session.start` `context.cwd` (updated by `session.context_changed`); `workspace.yaml` `cwd`; `session-store.db` `sessions.cwd` | `session-store.db` `turns` (prompt and final reply) survive `/session delete` and `/rewind`; secondary. [what survives](copilot-cli.md#what-survives-a-delete) |
| `copilot-desktop` | home `~/.copilot/session-state/<id>/events.jsonl`, written by the bundled Copilot CLI and parsed as `copilot-cli`; the app's own records in `~/.copilot/data.db` | not observed; the session logs and `data.db` live under the home | none of its own observed | `data.db` `projects.main_repo_path`; `worktrees.path`; `workspace.yaml` `cwd` | The CLI's `session-store.db`, `data.db` activity rows and the checkpoint refs survive a delete; parsed. [what survives](copilot-desktop.md#what-a-deleted-session-leaves) |
| `crush` | the project: `<project>/.crush/crush.db` | no | none | the database's location; `~/.local/share/crush/projects.json` | None of the transcript; `logs/crush.log` and `stats/index.html` outlive a delete, not parsed. [what survives](crush.md#what-survives-a-delete) |
| `gemini-cli` | home `~/.gemini/tmp/<slug>/chats/` | yes | `tmp/<slug>/logs.json`: prompts with session and time; untouched by delete and retention; secondary. [what survives](gemini-cli.md#what-survives-a-delete) | per project directory (`.project_root`) | `/chat save` checkpoints, the shadow git and `memory/` survive a delete and the 30-day retention; not parsed. [what survives](gemini-cli.md#what-survives-a-delete) |
| `goose` | home `~/.local/share/goose/sessions/sessions.db` | yes | `~/.local/state/goose/history.txt`: last 100 CLI inputs, text only; secondary. [what survives](goose.md#deletion-and-rewrites) | per session `working_dir` | `llm_request.<N>.jsonl` (last 10 provider calls) outlive `/clear`, a rewind and a delete; parsed. [what survives](goose.md#deletion-and-rewrites) |
| `hermes` | home `~/.hermes/state.db` | yes | `~/.hermes/.hermes_history`: prompts with time, no session; untouched by a delete; not parsed. [what survives](hermes.md#what-survives-a-delete) | per session `cwd` (updated) | `state-snapshots/` and `sessions/*.jsonl`, secondary; delete tombstones, `cron/output/` and `response_store.db` not parsed. [what survives](hermes.md#what-survives-a-delete) |
| `kilo-code` | home `~/.local/share/kilo/kilo.db` | yes | `~/.local/state/kilo/prompt-history.jsonl`: last 50 TUI prompts, no time, session or directory; survives a delete; not parsed. [what survives](kilo-code.md#what-survives-a-delete) | session `directory` and per message `path.cwd` | None separate; `retention/state.json` counts pruned sessions; not parsed. [what survives](kilo-code.md#what-survives-a-delete) |
| `kiro` | home `amazon-q/data.sqlite3`, the latest conversation per working directory only | yes | `~/.aws/amazonq/.cli_bash_history`: no time, session or directory; outlives `/clear`; not parsed. [what survives](kiro.md#copies-inside-the-conversation-blob-source-review-2026-10-19) | the row key and per message `env_context` | The blob's `transcript` array and checkpoint snapshots outlive `/clear` and a rewind; not parsed. [what survives](kiro.md#copies-inside-the-conversation-blob-source-review-2026-10-19) |
| `letta` | home `~/.letta/transcripts/` | yes | none | header `cwd` (local backend), else a heuristic | `transcript.jsonl` outlives an agent delete, secondary; `crons.json`, `runs/` and `listener-state/` not parsed. [what survives](letta.md#what-survives-a-delete) |
| `little-coder` | home `~/.pi/agent/sessions/` | yes | `little-coder-prompt-history.json`: last 100 prompts, no time or session; survives a delete; parsed. [what survives](little-coder.md#what-survives-a-delete) | header `cwd` | None of the transcript; the checkpoint directory outlives a delete; parsed. [what survives](little-coder.md#what-survives-a-delete) |
| `muse-code` | home `~/.local/share/muse/sessions/` | yes | `tui-history.jsonl`: prompt with session and workspace, no time; parsed. [what survives](muse-code.md#what-survives-a-delete) | session `workspace_root` | `.msp-view-v1` view and `session-index.db` (first prompt); what a delete leaves is not stated; not parsed. [what survives](muse-code.md#what-survives-a-delete) |
| `nanobot` | home `~/.nanobot/sessions/<workspace-id>/sessions.sqlite3`; the JSONL files beside it are imported once and then frozen | yes | `~/.nanobot/history/cli_history`: time and prompt, no session; never truncated; secondary. [what survives](nanobot.md#what-survives-a-delete) | a `.workspace` file per directory | WebUI transcript, frozen JSONL and `jsonl-backup/`, secondary; cron and trigger run records survive a delete, not parsed. [what survives](nanobot.md#what-survives-a-delete) |
| `ollama` | app data `db.sqlite` (desktop app) | yes | `~/.ollama/history`: last 100 REPL inputs, text only; parsed. [what survives](ollama.md#what-survives-a-delete) | none | A REPL `/save` lives on as a model blob, which the collector excludes with the weights. [what survives](ollama.md#what-survives-a-delete) |
| `open-interpreter` | home `~/.openinterpreter/sessions/` | yes | `~/.openinterpreter/history.jsonl`: session, time and text; survives `thread/delete`; secondary. [what survives](open-interpreter.md#what-survives-a-delete) | `session_meta` and per turn | `state_5.sqlite` and `thread_history_1.sqlite` as for Codex, secondary; memories and `db-backups/` not parsed. [what survives](open-interpreter.md#what-survives-a-delete) |
| `openclaw` | home `~/.openclaw/agents/<id>/agent/*.sqlite` | yes | none | header `cwd` | `.deleted` and `.reset` archives, compaction checkpoints and repair backups, secondary; the full-text index not parsed. [what survives](openclaw.md#what-survives-a-delete) |
| `opencode` | home `~/.local/share/opencode/opencode.db` | yes | `~/.local/state/opencode/prompt-history.jsonl`: last 50 TUI prompts, no time or session; survives a delete; not parsed. [what survives](opencode.md#what-survives-a-delete) | session `directory` and assistant `path.cwd` | Legacy V1 rows of a migrated database and `opencode-next.db`, secondary. [what survives](opencode.md#what-survives-a-delete) |
| `openhands` | home `~/.openhands/conversations/<hex>/` | yes | `projects/<sha256(cwd)>/prompt_history.json`: last 100 prompts per directory, local time; survives a delete; not parsed. [what survives](openhands.md#what-survives-a-delete) | per conversation `workspace.working_dir` | A fork, a full copy that survives its source's deletion, parsed as its own conversation. [what survives](openhands.md#what-survives-a-delete) |
| `pearai` | `~/.pearai/sessions/` and `globalStorage` tasks | yes | none | session `workspaceDirectory`; task `workspace` | The PearAI output channel log (every prompt and completion) and `dev_data/chat.jsonl` survive a delete; not parsed. [what survives](pearai.md#what-survives-a-delete) |
| `pi` | home `~/.pi/agent/sessions/--<cwd>--/` (or `--session-dir` anywhere) | yes | none | header `cwd` | User exports in project directories; `pi-debug.log` and `crashes.json` survive a delete, not parsed. [what survives](pi.md#what-survives-a-delete) |
| `qwen-code` | home `~/.qwen/projects/<cwd>/chats/` | yes | `~/.qwen/tmp/<sha256(cwd)>/logs.json`: prompts and model switches; untouched by a delete; secondary. [what survives](qwen-code.md#what-survives-a-delete) | every record (`cwd`) | `usage_record.jsonl` keeps a deleted session's id, project and times, no text; not parsed. [what survives](qwen-code.md#what-survives-a-delete) |
| `roo-code` | `globalStorage` `tasks/<id>/` or `~/.vscode-mock` | yes | CLI `~/.roo/cli-history.json`: newest 500 lines, text only; outlives a deleted task; secondary. [what survives](roo-code.md#what-survives-a-delete) | per task `workspace` | None. [what survives](roo-code.md#what-survives-a-delete) |
| `shellgpt` | the system temp directory `chat_cache/<id>` | yes, but lost to temp cleanup instead | none | none | The response cache: newest 100 answers, no prompt, time or session; outlives the chat; not parsed. [what survives](shellgpt.md#what-survives-a-delete) |
| `tabby` | home `~/.tabby/ee/db.sqlite` | yes | none | none (`git_url` only) | `db.backup-*.sqlite` copies and the `events/*.json` log, secondary; AI-written pages not parsed. [what survives](tabby.md#second-copies) |
| `twinny` | the editor's `state.vscdb` | yes | none | none in the chats; since 4.3.5 the `agent-changes/` records carry the workspace `root` | The `agent-changes/` records (newest 50) and the log channel survive a delete; not parsed. [what survives](twinny.md#what-survives-a-delete) |
| `vscode` | user data `workspaceStorage/<hash>/chatSessions/` | yes | none | `workspace.json` per hash; `workingDirectory` | `chatEditingSessions/`, Copilot Chat's `session-store.db`, hook transcripts and debug logs survive a delete; not parsed. [what survives](vscode.md#what-survives-a-delete) |
| `zed` | data directory `threads/threads.db` | yes | none | per thread `folder_paths` | `sidebar_threads` (metadata only); a thread's `created_git_worktrees` entry survives a delete, not parsed. [what survives](zed.md#what-survives-a-delete) |

What the table shows:

- Only Aider and Crush keep the transcript itself inside the project, so
  only for those two does deleting the project delete the evidence;
  ShellGPT's chats are lost to temp-directory cleanup instead. Pi's
  exports, Letta's session pointers, OpenHands' hooks file and the Muse
  and Claude Desktop worktrees are project-local too, but none is the
  primary transcript.
- Antigravity is the one agent whose history line is written before its
  session exists: the first prompt's line has no `conversationId`
  (Muse's `.session.jsonl.permission-init`, written before
  `session.jsonl`, is the nearest analogue). Claude Code's and Codex's
  history lines outlive their transcripts rather than precede them.
- Second copies that survive the loss of the primary store exist for
  Antigravity, Claude Desktop, Cline, Hermes, OpenClaw, Tabby, nanobot,
  Letta, Codex and Open Interpreter; the analyzer shows each event once
  across them
  ([doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122)).
- A transcript can also survive in another agent's store: Hermes Agent,
  Cline's SDK and CLAI import Claude Code and Codex sessions, and the
  copy outlives the original file
  ([claude-code.md](claude-code.md#2-transcript-files),
  [codex-cli.md](codex-cli.md#2-transcript-files)).
- Retention deletes old transcripts with no delete command in Claude
  Code (30 days), Gemini CLI (30 days by default) and Kilo Code (an
  opt-in pass); in each a prompt history outlives what retention
  removed.
