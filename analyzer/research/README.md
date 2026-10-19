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

A sweep of the documents above on 2026-10-15, prompted by an Antigravity
session whose project directory the agent had deleted while every record
of the session stayed under the home. A transcript directory under the
home survives deleting the project; a store inside the project does not.
The history and second-copy cells also say which files the analyzer parses
as secondary sources, since analyzer 0.13.0 (see
[Secondary sources](../docs/output.md#secondary-sources)). "Not stated"
means the document does not say. The unified-timeline design that
parses every source and shows each event once is
[doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122).

| Agent | Transcripts live in | Survives project deletion | Per-prompt history file | Working directory recorded | Second copy |
| --- | --- | --- | --- | --- | --- |
| `agent-zero` | install directory `usr/chats/<ctxid>/chat.json` | yes (projects are `usr/projects/<name>`, a separate place) | none | per chat `data.project` (a name) | none |
| `aider` | the project (git root): `.aider.chat.history.md` | no | `<repo>/.aider.input.history`: local timestamp and text, no session id | implicit (the file's location) | none outside the project; `.aider.input.history` and `.aider.llm.history` (only with a flag) beside the chat history are secondary sources and go with it |
| `antigravity` | home `~/.gemini/antigravity{,-cli}/conversations/<uuid>.db` | yes | `~/.gemini/antigravity-cli/history.jsonl`: `display`, `timestamp` (ms), `workspace`, `conversationId` (absent on a conversation's first prompt) | per conversation (workspace URIs) | brain `transcript_full.jsonl` (else its chunks, else the shortened `transcript.jsonl`), every step, no workspace; parsed as a secondary source since analyzer 0.13.0. The summaries database holds a summary per conversation, not its events |
| `chatgpt-desktop` | on OpenAI's servers only; the app's Codex-mode threads are `codex-cli` rollouts | not applicable: the conversations have no project, and their list is under the home | none | none (`cwd` is NULL on the `chatgpt` rows) | the `chatgpt` rows of `~/.codex/sqlite/codex-dev.db` `local_thread_catalog`, parsed since analyzer 0.17.0: a sign-in snapshot of the account's conversation list (title, creation and update times, account) that kept its times when a conversation was continued in the app (macOS, 2026-10-18); deleting a Codex-mode thread removed only that thread's `vscode` row; what a delete on chatgpt.com or a sign-out does to the row was not exercised |
| `claude-code` | home `~/.claude/projects/<key>/<id>.jsonl` | yes | `~/.claude/history.jsonl`: `display`, `pastedContents`, `timestamp` (ms), `project`, `sessionId`; usually outlives its transcript, which retention deletes after 30 days | every record (`cwd`, `gitBranch`) | `jobs/<id>/parent-transcript.jsonl` (not observed) |
| `claude-desktop` | app data `local-agent-mode-sessions/`; the Code tab uses `~/.claude/projects` | yes | none of its own | session record `cwd` and `userSelectedFolders`; JSONL `cwd` per record (a VM path in VM mode) | per-session `audit.jsonl` (every SDK message but stream deltas, plus permission events; append-only), a secondary source since analyzer 0.13.0 |
| `cline` | VS Code `globalStorage` or `~/.cline/data/` | yes | CLI `~/.cline/data/cache/user_input_history.jsonl`: `prompt`, `ts` (ms, the last rewrite's time on every line), last 20 unique prompts, no session or cwd; read as a secondary source | per task `cwdOnTaskInitialization`, manifest `cwd` | `db/session-search.db`, a full-text copy of every SDK lead transcript with no per-message time, read as a secondary source; the hub drops a session when it next reconciles after the session is deleted. The VS Code extension's upload queue `cache/sync-queue.json` holds in each item's `data` a full copy of the queued task file, which outlives a deleted task until the queue's seven-day cleanup; the parser does not read `data` |
| `codex-cli` | home `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | yes | `~/.codex/history.jsonl`: `session_id`, `ts` (s), `text`; no cwd; can outlive the rollout. Codex Desktop writes none: its prompts are in `.codex-global-state.json` `prompt-history`, per thread id, with no time | `session_meta.cwd`, updated per turn | `state_5.sqlite` `threads` (thread record, first prompt with no time) and `thread_history_1.sqlite` (projection of the turn events and turn items), both parsed as secondary sources; they outlive a rollout removed outside Codex, not a Codex thread delete. A delete in the ChatGPT app (macOS, build 26.1013.40934, 2026-10-18) removes the rollout, the `session_index.jsonl` line, the `state_5.sqlite` and `thread_history_1.sqlite` rows and the `codex-dev.db` catalog row; `.codex-global-state.json` keeps the thread's prompts, description, last activity time, standing permissions and a deletion marker `codex-writing-block-deleted-thread-v1:<id>`, parsed as a secondary source, and `logs_2.sqlite` keeps rows with the thread id |
| `cody` | the editor's `state.vscdb` or `Cody-nodejs/` | yes | none | none (inferred from `contextFiles`) | none |
| `continue` | `~/.continue/sessions/` | yes | CLI `input_history.json`, fields not stated | per session `workspaceDirectory` | `dev_data/*.jsonl` events; `logs/prompt.log` (JetBrains only) |
| `copilot-cli` | home `~/.copilot/session-state/<id>/events.jsonl` | yes | `~/.copilot/command-history-state.json`: prompts only, newest first, at most 50, no time, session or cwd; read as a secondary source matched on text alone | `session.start` `context.cwd` (updated by `session.context_changed`); `workspace.yaml` `cwd`; `session-store.db` `sessions.cwd` | `session-store.db` `turns` (prompt and final reply per turn, stamped at turn end) with `session_files`, `session_refs` and `checkpoints`; the bundle never deletes these rows, so they outlive a `/rewind` (which truncates `events.jsonl`) and a deleted session directory; `rewind-file-snapshots/index.json` keeps each turn's prompt until a rewind prunes it; both parsed as secondary sources since analyzer 0.14.0, with a one-hour window; a project directory removed with `rm -r` leaves every source intact, and the session was reconstructed in full (Linux install, 2026-10-16); on Windows (bundled CLI 1.0.99-2, 2026-10-17) a general chat deleted from the Copilot Desktop app kept its `turns`, `session_files` and `search_index` rows, and the store's WAL was not checkpointed when the app quit; a session deleted with the standalone CLI's own `/session delete <id> --yes --remote`, locally and from the account (Windows winget install, 1.0.98, 2026-10-17), lost its directory and with it the `workspace.yaml` sync marker, and was rebuilt from the store alone, which had kept only its last three of six turns |
| `copilot-desktop` | home `~/.copilot/session-state/<id>/events.jsonl`, written by the bundled Copilot CLI and parsed as `copilot-cli`; the app's own records in `~/.copilot/data.db` | not observed (no project was removed); the session logs and `data.db` live under the home, and `data.db` `projects` keeps the repository's name, owner and clone path | none of its own observed | `data.db` `projects.main_repo_path` through `workspace_session_aliases` and `workspaces`; `worktrees.path`; `workspace.yaml` `cwd` (the chat directory or the worktree) | `data.db` `activity_items.preview` (the start of each reply) and `session_checkpoints` (snapshot commits); the clone's `.git/refs/copilot/checkpoints/<session>/<seq>/<event id>` refs, parsed since analyzer 0.14.0; the CLI's `session-store.db` holds every prompt and final reply. A session deleted from the app (Linux install, 2026-10-16) loses its `session-state` directory, worktree and `data.db` workspace rows, but its `session-store.db` rows, the project session's `data.db` `sessions`, activity and checkpoint rows, the deleted rows' pages in `data.db-wal` and the checkpoint refs survive, and the analyzer rebuilt both sessions from them; `session_deletion_intents` stayed empty. On Windows (2026-10-17) the delete also removed the chat's working directory under `~/.copilot/chats/` with the project the agent had built there, the chat's `activity_items` rows survived, and quitting the app checkpointed `data.db-wal` into the main file, so the deleted session's id moves from the WAL into the main file's surviving rows and freed pages |
| `crush` | the project: `<project>/.crush/crush.db` | no | none | the database's location; `~/.local/share/crush/projects.json` | none |
| `gemini-cli` | home `~/.gemini/tmp/<slug>/chats/` | yes | `~/.gemini/tmp/<slug>/logs.json`: `sessionId`, `messageId`, `timestamp`, `type`, `message` | per project directory (`.project_root`) | `/chat save` checkpoints, tool checkpoints, shadow git |
| `goose` | home `~/.local/share/goose/sessions/sessions.db` | yes | `~/.local/state/goose/history.txt`: text only, the last 100 CLI inputs; a secondary source matched on text alone | per session `working_dir` | `llm_request.<N>.jsonl` logs, per call (parsed, not marked secondary) |
| `hermes` | home `~/.hermes/state.db` | yes | none | per session `cwd` (updated) | `state-snapshots/*/state.db` (up to 20 copies, collected only with `--full`) and `sessions/*.jsonl` diverts, both parsed as secondary sources; `backups/*.zip` and `/save` exports, not parsed |
| `kilo-code` | home `~/.local/share/kilo/kilo.db` | yes | none | session `directory` and per message `path.cwd` | none separate (V1 and V2 tables in one database) |
| `kiro` | home `amazon-q/data.sqlite3`, the latest conversation per working directory only | yes | `~/.aws/amazonq/.cli_bash_history`, adjacent evidence, fields not stated | the row key and per message `env_context` | `/save <path>` only |
| `letta` | home `~/.letta/transcripts/` | yes | none (`sessions.jsonl` is per session: `agent_id`, `session_id`, `timestamp`, `project`) | header `cwd` (local backend), else a heuristic | `transcripts/<agent>/<conversation>/transcript.jsonl`, a copy of each completed turn of the local-backend `messages.jsonl` (secondary; it outlives an agent's deletion); chunk logs (truncated) |
| `little-coder` | home `~/.pi/agent/sessions/` | yes | `~/.pi/agent/little-coder-prompt-history.json`: strings only | header `cwd` | none |
| `muse-code` | home `~/.local/share/muse/sessions/` | yes | `tui-history.jsonl`: a prompt line then `{project, session}`; no timestamp | session `workspace_root` | `.msp-view-v1` journal; `session-index.db` (first prompt) |
| `nanobot` | home `~/.nanobot/sessions/<workspace-id>/` | yes | `~/.nanobot/history/cli_history`: local timestamp and prompt text, no session or workspace | a `.workspace` file per directory | WebUI transcript `webui/<key>.jsonl` and `.segments/` (WebUI chats; survives `/new`); `memory/history.jsonl` holds summaries, not copies |
| `ollama` | app data `db.sqlite` (desktop app) | yes | `~/.ollama/history`: text only, last 100 | none | REPL `/save` into a model blob |
| `open-interpreter` | home `~/.openinterpreter/sessions/` | yes | `~/.openinterpreter/history.jsonl`: `session_id`, `ts`, `text` | `session_meta` and per turn | `state_5.sqlite` and `thread_history_1.sqlite` as for Codex (no item lifecycle times), parsed as secondary sources |
| `openclaw` | home `~/.openclaw/agents/<id>/agent/*.sqlite` | yes | none | header `cwd` | `.reset` and `.deleted` archive files (copies of the archive blobs), compaction checkpoints and pre-doctor repair backups, all parsed as secondary sources; legacy JSONL |
| `opencode` | home `~/.local/share/opencode/opencode.db` | yes | none | session `directory` and assistant `path.cwd` | legacy `storage/` JSON tree |
| `openhands` | home `~/.openhands/conversations/<hex>/` | yes | `~/.openhands/projects/<sha256(cwd)>/prompt_history.json`, fields not stated | per conversation `workspace.working_dir` | not stated |
| `pearai` | `~/.pearai/sessions/` and `globalStorage` tasks | yes | none | session `workspaceDirectory`; task `workspace` | `dev_data/chat.jsonl` (only on feedback) |
| `pi` | home `~/.pi/agent/sessions/--<cwd>--/` (or `--session-dir` anywhere) | yes | none | header `cwd` | user exports `session-*.jsonl` and `.html`, written into project directories; forks copy entries |
| `qwen-code` | home `~/.qwen/projects/<cwd>/chats/` | yes | `~/.qwen/tmp/<sha256(cwd)>/logs.json`; per-session `<id>.ledger.jsonl` (fields not stated) | every record (`cwd`) | `logs.json`, checkpoints |
| `roo-code` | `globalStorage` `tasks/<id>/` or `~/.vscode-mock` | yes | CLI `~/.roo/cli-history.json`: text only, every submitted line, the newest 500 | per task `workspace` | none |
| `shellgpt` | the system temp directory `chat_cache/<id>` | yes, but lost to temp cleanup instead | none | none | none |
| `tabby` | home `~/.tabby/ee/db.sqlite` | yes | none | none (`git_url` only) | `db.backup-*.sqlite` (pre-migration copies of threads and events); `events/*.json` (every event, `user_events` keeps only those with a user, for three months) |
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
  Letta, Codex and Open Interpreter; the table says which of them the
  analyzer parses as secondary sources. The design is
  [doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122).
