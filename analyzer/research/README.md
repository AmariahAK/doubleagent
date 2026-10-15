# Record schema research

One document per catalog agent, named after the agent as it appears in
`collect-agent-artifacts.sh --list`, describing how that agent records
transcripts on disk and how a parser should read them. Each was written from
a shallow clone of the tool's source at the commit it names, with file and
line citations, or for a closed-source tool from the evidence named in its
first section (for Antigravity, the protobuf descriptors embedded in its
binary). Each ends with a parser plan mapped to the timeline columns and
synthetic sample records meant to become test fixtures. Treat them as the
evidence behind each parser; the field names a parser actually depends on
are repeated in its module docstring under `doubleagent/parsers/`.

The research itself may be done in groups (forks of one codebase are best
studied together, because the differences are what matter), but the
findings are split per agent before they land here. Where two agents share
a lineage, each document says so and links to the other instead of repeating
it.

| Agent | Document | Store | Parser |
| --- | --- | --- | --- |
| `agent-zero` | [agent-zero.md](agent-zero.md) | JSON per chat context, rewritten whole | yes |
| `aider` | [aider.md](aider.md) | markdown and readline-style text in the repository | yes |
| `antigravity` | [antigravity.md](antigravity.md) | SQLite of protobuf blobs per conversation, the same for the CLI (`.gemini/antigravity-cli`) and the desktop app (`.gemini/antigravity`); schema from the descriptors embedded in `agy` and the app's language server; verified on Linux (WSL: CLI; Ubuntu: CLI and app), macOS (CLI and app) and Windows (Windows 11 ARM64: CLI 1.3.5 and desktop app 2.23.1) installs | yes |
| `claude-code` | [claude-code.md](claude-code.md) | JSONL per session with `uuid`/`parentUuid` chains, subagent files beside it, prompt history | yes |
| `claude-desktop` | [claude-desktop.md](claude-desktop.md) | session records (JSON) and an HMAC-chained `audit.jsonl` per Cowork session around Claude Code JSONL transcripts; closed source, from the app bundle; verified on Windows, Linux and macOS installs | yes |
| `cline` | [cline.md](cline.md) | JSON arrays per task; SDK session files; SQLite indexes | yes |
| `codex-cli` | [codex-cli.md](codex-cli.md) | JSONL rollouts (`session_meta`, `response_item`, `event_msg`), optionally zstd-compressed | yes |
| `cody` | [cody.md](cody.md) | rows in the editor `state.vscdb`; JetBrains global-state JSON | yes |
| `continue` | [continue.md](continue.md) | JSON per session, session-level timestamps only | yes |
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
the agent; the parser table in [`docs/parsers.md`](../docs/parsers.md) lists the files each one
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

A sweep of the documents above on 2026-10-15, prompted by an Antigravity
session whose project directory the agent had deleted while every record
of the session stayed under the home. The table says, per agent, where
the transcripts are kept (a directory under the home survives deleting
the project; a store inside the project does not), whether a per-prompt
history file is written beside them and what each line holds, where the
working directory is recorded, and whether a second copy of the
transcript exists that would survive loss of the primary store. "Not
stated" means the document does not say. The unified-timeline design that
parses every source and shows each event once is
[doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122).

| Agent | Transcripts live in | Survives project deletion | Per-prompt history file | Working directory recorded | Second copy |
| --- | --- | --- | --- | --- | --- |
| `agent-zero` | install directory `usr/chats/<ctxid>/chat.json` | yes (projects are `usr/projects/<name>`, a separate place) | none | per chat `data.project` (a name) | none |
| `aider` | the project (git root): `.aider.chat.history.md` | no | `<repo>/.aider.input.history`: local timestamp and text, no session id | implicit (the file's location) | none outside the project; `.aider.input.history` and `.aider.llm.history` (only with a flag) beside the chat history are secondary sources and go with it |
| `antigravity` | home `~/.gemini/antigravity{,-cli}/conversations/<uuid>.db` | yes | `~/.gemini/antigravity-cli/history.jsonl`: `display`, `timestamp` (ms), `workspace`, `conversationId` (absent on a conversation's first prompt) | per conversation (workspace URIs) | brain `transcript{,_full}.jsonl` and chunks; the summaries database |
| `claude-code` | home `~/.claude/projects/<key>/<id>.jsonl` | yes | `~/.claude/history.jsonl`: `display`, `pastedContents`, `timestamp` (ms), `project`, `sessionId`; usually outlives its transcript, which retention deletes after 30 days | every record (`cwd`, `gitBranch`) | `jobs/<id>/parent-transcript.jsonl` (not observed) |
| `claude-desktop` | app data `local-agent-mode-sessions/`; the Code tab uses `~/.claude/projects` | yes | none of its own | session record `cwd` and `userSelectedFolders`; JSONL `cwd` per record (a VM path in VM mode) | per-session `audit.jsonl` (every SDK message) |
| `cline` | VS Code `globalStorage` or `~/.cline/data/` | yes | CLI `~/.cline/data/cache/user_input_history.jsonl` with `ts`; other fields not stated | per task `cwdOnTaskInitialization`, manifest `cwd` | `db/session-search.db`, a full-text copy of every transcript |
| `codex-cli` | home `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | yes | `~/.codex/history.jsonl`: `session_id`, `ts` (s), `text`; no cwd; can outlive the rollout | `session_meta.cwd`, updated per turn | `state_5.sqlite` (first prompt), `thread_history_1.sqlite` projection |
| `cody` | the editor's `state.vscdb` or `Cody-nodejs/` | yes | none | none (inferred from `contextFiles`) | none |
| `continue` | `~/.continue/sessions/` | yes | CLI `input_history.json`, fields not stated | per session `workspaceDirectory` | `dev_data/*.jsonl` events; `logs/prompt.log` (JetBrains only) |
| `crush` | the project: `<project>/.crush/crush.db` | no | none | the database's location; `~/.local/share/crush/projects.json` | none |
| `gemini-cli` | home `~/.gemini/tmp/<slug>/chats/` | yes | `~/.gemini/tmp/<slug>/logs.json`: `sessionId`, `messageId`, `timestamp`, `type`, `message` | per project directory (`.project_root`) | `/chat save` checkpoints, tool checkpoints, shadow git |
| `goose` | home `~/.local/share/goose/sessions/sessions.db` | yes | `~/.local/state/goose/history.txt`: text only | per session `working_dir` | `llm_request.<N>.jsonl` logs, per call |
| `hermes` | home `~/.hermes/state.db` | yes | none | per session `cwd` (updated) | `state-snapshots/*/state.db`, `sessions/*.jsonl` fallback, `/save` |
| `kilo-code` | home `~/.local/share/kilo/kilo.db` | yes | none | session `directory` and per message `path.cwd` | none separate (V1 and V2 tables in one database) |
| `kiro` | home `amazon-q/data.sqlite3`, the latest conversation per working directory only | yes | `~/.aws/amazonq/.cli_bash_history`, adjacent evidence, fields not stated | the row key and per message `env_context` | `/save <path>` only |
| `letta` | home `~/.letta/transcripts/` | yes | none (`sessions.jsonl` is per session: `agent_id`, `session_id`, `timestamp`, `project`) | header `cwd` (local backend), else a heuristic | local-backend `messages.jsonl`; chunk logs (truncated) |
| `little-coder` | home `~/.pi/agent/sessions/` | yes | `~/.pi/agent/little-coder-prompt-history.json`: strings only | header `cwd` | none |
| `muse-code` | home `~/.local/share/muse/sessions/` | yes | `tui-history.jsonl`: a prompt line then `{project, session}`; no timestamp | session `workspace_root` | `.msp-view-v1` journal; `session-index.db` (first prompt) |
| `nanobot` | home `~/.nanobot/sessions/<workspace-id>/` | yes | `~/.nanobot/history/cli_history`: prompts only | a `.workspace` file per directory | WebUI transcript mirror; `memory/history.jsonl` |
| `ollama` | app data `db.sqlite` (desktop app) | yes | `~/.ollama/history`: text only, last 100 | none | REPL `/save` into a model blob |
| `open-interpreter` | home `~/.openinterpreter/sessions/` | yes | `~/.openinterpreter/history.jsonl`: `session_id`, `ts`, `text` | `session_meta` and per turn | the Codex-style SQLite set |
| `openclaw` | home `~/.openclaw/agents/<id>/agent/*.sqlite` | yes | none | header `cwd` | `.reset` and `.deleted` archives, archive blobs, legacy JSONL |
| `opencode` | home `~/.local/share/opencode/opencode.db` | yes | none | session `directory` and assistant `path.cwd` | legacy `storage/` JSON tree |
| `openhands` | home `~/.openhands/conversations/<hex>/` | yes | `~/.openhands/projects/<sha256(cwd)>/prompt_history.json`, fields not stated | per conversation `workspace.working_dir` | not stated |
| `pearai` | `~/.pearai/sessions/` and `globalStorage` tasks | yes | none | session `workspaceDirectory`; task `workspace` | `dev_data/chat.jsonl` (only on feedback) |
| `pi` | home `~/.pi/agent/sessions/--<cwd>--/` (or `--session-dir` anywhere) | yes | none | header `cwd` | user exports `session-*.jsonl` and `.html`, written into project directories; forks copy entries |
| `qwen-code` | home `~/.qwen/projects/<cwd>/chats/` | yes | `~/.qwen/tmp/<sha256(cwd)>/logs.json`; per-session `<id>.ledger.jsonl` (fields not stated) | every record (`cwd`) | `logs.json`, checkpoints |
| `roo-code` | `globalStorage` `tasks/<id>/` or `~/.vscode-mock` | yes | CLI `cli-history.json`: raw prompts | per task `workspace` | none |
| `shellgpt` | the system temp directory `chat_cache/<id>` | yes, but lost to temp cleanup instead | none | none | none |
| `tabby` | home `~/.tabby/ee/db.sqlite` | yes | none | none (`git_url` only) | `db.backup-*.sqlite`, `events/*.json` |
| `twinny` | the editor's `state.vscdb` | yes | none | none | optional twinny-server recordings |
| `vscode` | user data `workspaceStorage/<hash>/chatSessions/` | yes | none | `workspace.json` per hash; `workingDirectory` | legacy `interactive.sessions` blob |
| `zed` | data directory `threads/threads.db` | yes | none | per thread `folder_paths` | `sidebar_threads` (metadata only) |

What the sweep shows:

- Only Aider and Crush keep the transcript itself inside the project, so
  only for those two does deleting the project delete the evidence.
  ShellGPT's chats are lost to temp-directory cleanup instead. Pi's user
  exports, Letta's `<project>/.letta/settings.local.json` session
  pointers, OpenHands' `<project>/.openhands/hooks.json` and the Muse
  and Claude Desktop worktrees are the other project-local traces, none
  of them the primary transcript.
- Antigravity is the one agent whose document says a history line is
  written before its session exists: the first prompt's line has no
  `conversationId`. Muse's `.session.jsonl.permission-init` file is the
  nearest analogue, written before `session.jsonl`. Claude Code's and
  Codex's history lines are said to outlive their transcripts (retention,
  deleted or ephemeral threads), not to precede them.
- Second copies that survive loss of the primary store exist for
  Antigravity, Claude Desktop, Cline, Hermes, OpenClaw, Tabby, nanobot,
  Letta, Codex and Open Interpreter; the analyzer reads only Claude
  Desktop's `audit.jsonl` (as a fallback) today. The others are listed in
  [doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122).
