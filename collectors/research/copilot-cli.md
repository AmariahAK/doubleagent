# copilot-cli

Catalog agent: `copilot-cli` (GitHub Copilot CLI). How the transcripts are encoded and how a parser
reads them is in [`analyzer/research/copilot-cli.md`](../../analyzer/research/copilot-cli.md). The
GitHub Copilot Desktop app runs its sessions through a bundled Copilot CLI and writes them into the
same `~/.copilot/session-state/` directory, in this format, with `workspace.yaml` `client_name`
`github/autopilot` where the CLI writes `github/cli`; those sessions stay `copilot-cli`, and the
app's own files are the `copilot-desktop` agent's ([`copilot-desktop.md`](copilot-desktop.md) and
[`analyzer/research/copilot-desktop.md`](../../analyzer/research/copilot-desktop.md)).

## 1. Source and evidence

Closed source (`github/copilot-cli` repo is issues only). Evidence is the **shipped bundle**:
`npm pack @github/copilot` 1.0.91 (5 KB loader, `buildMetadata.gitCommit 216810c5`) →
`npm pack @github/copilot-linux-x64@1.0.91`, a 178 MB Node single-executable (`copilot`). Its SEA
(Node single executable application) blob (magic 0x143da20 at 0x67a01b8) holds `sea-loader.js`
(122 KB, `scratchpad/npm/cp-sea-loader.js`) and one asset `copilot.tgz` (69.7 MB,
`scratchpad/npm/cp-asset-copilot.tgz`), extracted to `scratchpad/npm/cp-pkg/package/`: `app.js`
(7.6 MB JS), `prebuilds/linux-x64/cli-native.node` (8 MB) and `runtime.node` (122 MB, Rust).
Citations: "app.js" with the surrounding identifiers, "sea-loader" (same code appears in cc-loader),
"native"/"runtime" for byte-string hits. **Docs**: [Copilot CLI configuration directory
reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference).
**Local**: names-only listing of `~/.copilot` and `~/.cache/copilot`.

The 1.0.98 bundle (`@github/copilot-darwin-arm64`, loader `buildMetadata.gitCommit` `45ef16251c8`,
`copilot` sha256 `b1a76d9eec3c88e8545ee96834189ab08c3d75ef65500a60925187fa6c33fdf1`) has the same
SEA layout with one extra byte after the blob flags (magic at `0x5888000`, `copilot.tgz` at
`0x58a6877`); `app.js` is now a 42 KB bootstrap and the CLI code is `cli-main.js` (sha256
`151c2e2a37ddb2514fc5cdbd5c473f9aeeb1a74d59e5062f3921a46d12a8f1c2`), with the state paths in the
Rust addon `prebuilds/darwin-arm64/runtime.node`. Citations to it are written
`cli-main.js@<byte offset>` or `runtime.node@<byte offset>` with a snippet; the extraction is
described in [section 1 of
`analyzer/research/copilot-cli.md`](../../analyzer/research/copilot-cli.md#1-source-and-evidence).

### Observed

- **Observed (Windows, winget)**: the standalone Copilot CLI 1.0.98 installed with
  `winget install GitHub.Copilot` (winget is the Windows Package Manager; `GitHub.Copilot` is the
  package id), on the same Windows 11 ARM64 Parallels VM (build 10.0.26300.9550, user `sean`, home
  `C:\Users\sean`) reverted to its clean snapshot, which has no Python, git, `gh` or Node and had
  never run Copilot Desktop, 2026-10-17, all times UTC, surveyed for names, sizes, key names and
  types only. This is the first round with a names-only listing after every action, so each action's
  writes below come from a listing diff. The install (listing 21:44Z) wrote
  `AppData\Local\Microsoft\WinGet\Packages\GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe\`
  with `copilot.exe` (154,351,392 bytes, file date 2026-10-14, version 1.0.98) and a 16 KB winget
  database `GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe.db` beside it, a user `PATH` entry
  for that directory, the HKCU uninstall key `GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe`
  (DisplayName `Copilot CLI`, DisplayVersion `v1.0.98`, InstallLocation that directory) and the
  installer download under `AppData\Local\Temp\WinGet\GitHub.Copilot.v1.0.98`; no `.copilot`, no
  `AppData\Local\copilot`, no credential file and no `DeveloperTools` registry key yet ([section
  2](#2-per-user-storage)). The first start, `copilot` in `C:\Users\sean\demo` at 21:46:48 (listing
  21:48Z), wrote the extracted package `AppData\Local\copilot\pkg\win32-arm64\1.0.98\`
  (181,983,762 bytes), `AppData\Local\copilot\marketplaces\.auto-update.lock` and `.copilot\` with
  the Linux layout: `config.json`, `command-history-state.json` (43 bytes),
  `open-sessions-state.json` (188 bytes), an empty `installed-plugins.lock`, empty `ide\`,
  `servers\` and `installed-plugins\`, `sidebar-sessions-state\<sha256 of cwd>.json` (125 bytes),
  `logs\.copilot-log.lock`, `logs\process-1792273608752-2868.log`, and `session-state\` with
  `.session-operation-locks\<uuid>.lock` and the session directory (`workspace.yaml` 212 bytes with
  the keys `id`, `cwd`, `client_name`, `user_named`, `summary_count`, `fork_count`, `created_at`,
  `updated_at`; `.workspace-fork.lock`; `checkpoints\index.md` 172 bytes; empty `files\` and
  `research\`; `inuse.2868.hold` 0 bytes and `inuse.2868.lock` 5 bytes, the process's in-use
  markers). The user logged in from inside the session (`/login`, the device-code flow, in which the
  user types a one-time code into github.com in a browser), completing at 21:48:02. While the code
  was pending the CLI wrote about 280,000 log lines in 74 seconds: the process log rotated at 10 MB
  four times (`process-1792273608752-2868.1.log` to `.4.log`, 10,472,282 to 10,483,404 bytes and
  65,093 to 65,615 lines each, seven message kinds) and the live log was 3,068,006 bytes at
  21:48:02. Each rotated file holds about 9,700 each of `[WARNING] [rust:copilot_runtime::auth::gh]`
  lines saying the CLI failed to run `gh auth token` (`"error":"program path has no file name"`; no
  `gh` on the VM), three `[managedSettings]` lines (`effective policy resolved: source=none`,
  `device MDM: no policy present on this device`,
  `server policy fetch skipped: no authenticated GitHub host available`; MDM is mobile device
  management, an organisation's policy push), `[INFO] Remote session access disabled` and
  `[rust:lsp::session_service] Resolved LSP telemetry consent` with
  `"telemetry_level":"off","source":"auth_change"` (LSP is the Language Server Protocol), and about
  7,500 `[INFO] [rust:otel] OTel session policy applied` (OTel is OpenTelemetry, the telemetry
  framework): a pending login re-resolves the auth state in a tight loop on Windows 1.0.98. After
  the login the live log grew by 3 KB in fifteen minutes; the Linux and macOS 1.0.98 logs were
  105 bytes to 47 KB. The login (21:48:02) rewrote `config.json` (418 bytes, JSONC, the five keys of
  [section 3](#3-credentials)), wrote two Windows Credential Manager files under
  `AppData\Roaming\Microsoft\Credentials\` (634 and 666 bytes, the only ones in the profile besides
  one of 2026-10-10 under `AppData\Local\Microsoft\Credentials\`), created the registry value
  `HKCU\SOFTWARE\Microsoft\DeveloperTools\deviceid` (`REG_SZ`, 36 characters; no file), and wrote in
  `AppData\Local\copilot\` `copilot-user-cache.json` (3,309 bytes), `exp-cache.json` (10,904 bytes),
  `memory-enablement-cache-config.json` (351 bytes), `managed-settings.<sha256>.order.json`
  (36 bytes) and `managed-settings.<sha256>.fence` (36 bytes, a file not seen before, contents not
  read), each with a `.lock`, and an empty `managed-settings\` directory. The first prompt
  (21:50:55, listing 22:02Z) created `events.jsonl` (1,216,194 bytes by 22:01:14; the session read
  web pages, so the tool results were large), `session-store.db` (4,096 bytes) with `-wal`
  (1,268,992 bytes) and `-shm`, and `rewind-file-snapshots\tracking.json` (29 bytes; no `index.json`
  yet), grew `command-history-state.json` to 114 bytes and `workspace.yaml` to 251 bytes (the `name`
  key added); the process log grew by 3 KB. One tool call denied and one approved with "allow
  always" (listing 22:06Z; the two steps share a diff) created `permissions-config.json` at 22:06:06
  (142 bytes, `{locations: {"<cwd>": {tool_approvals: {kind: "write"}}}}`, the standing grant for
  file writes in `demo` written by the "allow always"; the denial wrote no standing rule), grew
  `events.jsonl` by 750 KB, the WAL to 1,590,352 bytes and `command-history-state.json` to
  190 bytes, and the approved `apply_patch` call wrote `demo\ai-coding-tools-review.md`. A `/model`
  switch to Auto (listing 22:08Z) grew `events.jsonl` by 870 bytes and `command-history-state.json`
  by 14 bytes and rewrote `exp-cache.json` at the same size, nothing else. Quitting at 22:08:31
  wrote `rewind-file-snapshots\index.json` (1,204 bytes), grew `events.jsonl` by 8 KB and removed
  the `inuse.2868` pair. Resuming at 22:08:50 (`copilot` again, the session picked from the resume
  picker; listing 22:09Z) wrote a new process log `process-1792274929863-4428.log` (36 KB, no flood)
  and rewrote `workspace.yaml` from 251 to 376 bytes with `updated_at` unchanged, adding
  `remote_steerable` (false), `mc_task_id`, `mc_session_id` and `mc_last_event_id` (UUIDs), the sync
  marker of [section 6](#6-where-the-project-path-is-recorded); `open-sessions-state.json` became
  373 bytes (keys `schemaVersion`, `openedAt`, `refreshedAt`, `working`); the sidebar file became
  169 bytes with two `sessionIds`, the resumed session and a new id that got an operation lock and a
  sidebar entry but never a directory (the picker appears to start a fresh session before switching
  to the chosen one); `config.json` was touched at the same size; and the cache gained
  `managed-settings\<sha256>.json` (252 bytes), with `managed-settings.<sha256>.order.json` at
  101 bytes and `memory-enablement-cache-config.json` at 532. The resumed process logged
  `Remote session access enabled` (the first process had logged `disabled` throughout the flood) and
  `Using default model: gpt-6.1-sol`; the sync itself is logged nowhere. At 22:11:04 the user
  started `copilot` again in `demo` (a new session whose directory held `workspace.yaml` of
  212 bytes and a 1,162-byte `events.jsonl` with `session.start`, `session.model_change` and
  `session.shutdown` only, and no `session.db` or `rewind-file-snapshots`) and deleted the first
  session from it with `/session delete <id> --yes --remote`, after trying `/session`,
  `/session delete-all`, `/session delete <id>` and `/session delete copilot <id>`; the CLI asked
  whether to delete the synced copy too ("has been synced to your account. Would you also like to
  delete the synced session data"), the user said yes, and quit at 22:16:32 (listing 22:17Z). The
  delete removed the whole session directory and the id from the sidebar file (rewritten at
  22:16:32, same 169 bytes, now the new session and the never-created one), and
  `open-sessions-state.json` became `{}`. It left `session-store.db` (WAL unchanged since 22:06)
  with the session's rows, the 0-byte `.session-operation-locks\<id>.lock` (three locks in all), the
  seven slash commands among the ten entries of `command-history-state.json` (450 bytes), the five
  process logs, `permissions-config.json` and the file the approved call wrote; what the analyzer
  rebuilt from them is in [section 1 of
  `analyzer/research/copilot-cli.md`](../../analyzer/research/copilot-cli.md#1-source-and-evidence).
  The process logs record nothing about the deletion (no `sessions.delete` line, unlike the desktop
  app's bundled CLI), and `mcp-config.json` was never written. Collector 1.13.0, run as the user at
  22:17:18 from an administrator SSH session, no Copilot Desktop on this snapshot: 34 files,
  46,680,889 bytes, all `copilot-cli`, the five logs 44.4 MB of them; 3 `skipped_excluded`
  (`.copilot\installed-plugins`, 0 bytes; `AppData\Local\copilot\marketplaces`, 0 bytes beyond its
  lock; `AppData\Local\copilot\pkg`, 181,983,762 bytes); 0 errors; 1 `secret: true` row
  (`.copilot\config.json`); project discovery found `C:\Users\sean\demo` from the two session
  directories' `workspace.yaml`, both with an `events.jsonl`. An npm install of the standalone CLI
  on Windows is still not observed ([issue
  133](https://github.com/seanthegeek/doubleagent/issues/133)).
- **Observed (Windows, through Copilot Desktop)**: Copilot CLI 1.0.99-2 as the bundled CLI of GitHub
  Copilot Desktop 1.1.30 (`copilot-sdk/cliVersion.d.ts` `COPILOT_CLI_VERSION = "1.0.99-2"`,
  `COPILOT_CLI_USE_NPM_PACKAGE = false`), downloaded by the app to
  `AppData\Local\github-copilot-sdk\cli\1.0.99-2\copilot.exe` (158,577,952 bytes, sha256
  `b7bc340acf1c82228de2e3504444847f8e18beec1f07f72f260f1bbeb4c3a9b2`), on a Windows 11 ARM64
  Parallels VM (build 10.0.26300.9550, home `C:\Users\sean`), 2026-10-17, surveyed for names, sizes,
  key names and types only; the round is in [section 1 of
  `copilot-desktop.md`](copilot-desktop.md#1-source-and-evidence). `copilot.exe` carries the strings
  `COPILOT_HOME`, `USERPROFILE` and the named pipe prefix `\\.\pipe\copilot-taskbar-`, and no
  keyring strings. `.copilot` sat at the top of the profile (`C:\Users\sean\.copilot`, the
  `COPILOT_HOME` default under `USERPROFILE`) with the Linux layout: `config.json` (131 bytes,
  JSONC, one key `firstLaunchAt`), `session-store.db` (4096 bytes, `-wal` 609,792 then
  704,552 bytes, `-shm`), `logs/.copilot-log.lock` and 17 `logs/process-<epoch ms>-<pid>.log`
  (1.7 KB to 47 KB), `session-state/`, empty `extensions/` and empty `installed-plugins/`. Adding
  three MCP servers (Model Context Protocol servers, programs that offer the agent extra tools) from
  the app wrote `mcp-config.json` (725 bytes, shape
  `mcpServers{<name>{type: "local", command, args[], tools[], env{}}}`; one server's `env` held a
  GitHub personal access token, [section 3](#3-credentials)), `.mcp-writer.binding` (157 bytes JSON,
  `lock{file_index, platform: "windows", volume}` and `root{...}`) and `.mcp-writer.lock` (0 bytes);
  the process logs say `MCP server connection failed {"server_name":"<name>","raw_error":"failed to
  spawn MCP server process: program not found"}` for the two servers whose commands were not
  installed. The cache directory was `AppData\Local\copilot` ([section 2](#2-per-user-storage)):
  `copilot-user-cache.json` (3,309 bytes, JSONC, the Linux shape, no token; its `response` also
  named `analytics_tracking_id`, `assigned_date`, `can_signup_for_limited`, `copilotignore_enabled`,
  `restricted_telemetry`, `enterprise_usage_telemetry`, `is_staff`, `te`, `token_based_billing`,
  `can_upgrade_plan` and `quota_reset_date_utc`, which the Linux list in [section
  2](#2-per-user-storage) does not name) with `.lock`, `managed-settings/<sha256>.json` (252 bytes,
  the Linux shape, `response` null) with its `.order.json` and `.lock`, `tgrep-serve.lock`,
  `mcp-tools/<sha256>.json` (two files of 20 KB), `marketplaces/` (4,560 files, 263,616,505 bytes:
  `freshness.json`, `github-awesome-copilot.lock` and the clone `github-awesome-copilot/`; the logs
  say `Best-effort plugin preparation skipped 1 item.` three times) and `pkg/win32-arm64/1.0.99-2/`
  (255 files, 191,966,761 bytes, `.extraction-complete`, `cli-main.js` and the `inuse.<pid>.hold`
  and `.lock` pairs of five processes). No `AppData\Local\Microsoft\DeveloperTools` or `~/.cache`
  was written; the Microsoft developer-tools device id ([issue
  148](https://github.com/seanthegeek/doubleagent/issues/148)) is the registry value
  `HKCU\SOFTWARE\Microsoft\DeveloperTools\deviceid` (HKCU is `HKEY_CURRENT_USER`, the registry hive
  of the signed-in user; a string value, type `REG_SZ`, of 36 characters) on Windows, outside the
  collector's scope. Collector 1.13.0 as first written, run as the user: `copilot-cli` 4,641 files
  and 265,398,349 bytes, 4,560 files and 263,616,505 bytes of them the marketplace clone, now
  excluded ([section 4](#4-exclusions)); `.copilot/config.json` and `.copilot/mcp-config.json`
  flagged `secret: true`; `AppData/Local/copilot/pkg` and `.copilot/installed-plugins`
  `skipped_excluded`. The standalone CLI on Windows is the bullet above.
- **Observed (Linux)**: Copilot CLI 1.0.98 installed with `sudo npm install -g @github/copilot`, an
  Ubuntu 26.04.1 arm64 Parallels VM (kernel 7.0.0-38-generic, `/bin/sh` dash, home `/home/sean`),
  2026-10-16, surveyed for names, sizes, key names and types only. Exercised: `copilot login`, then
  two interactive sessions, the first in `~/demo` (created 21:01:19Z, shut down 21:16:01Z, UTC) and
  the second in `~/secret` (21:16:26Z to 21:19:27Z), after which the user removed the project with
  `rm -r secret/`. Every action ran before the first listing, so no per-action listing diff exists;
  the times above and the files' modification times are the only mapping from action to file.
  `~/.copilot` held the macOS set above except `settings.json`, which was not written: three
  `logs/process-*.log` (105 bytes for `copilot login`, 16 KB and 15 KB for the sessions),
  `session-store.db` (4096 bytes) with a 1.37 MB `-wal` and `-shm`, and two
  `sidebar-sessions-state/` files, one for the removed `~/secret`. No `~/.config/.copilot` or
  `~/.local/state/.copilot`. `~/.cache/copilot` held the names macOS keeps in
  `~/Library/Caches/copilot`, with the package under `pkg/linux-arm64/1.0.98/`
  (`.extraction-complete`, `cli-main.js`, `prebuilds/linux-arm64/runtime.node`, `schemas/`). The
  login put the GitHub token in the GNOME keyring (the GNOME desktop's password store, which the
  runtime reaches through its vendored Secret Service client), not in `config.json` ([section
  3](#3-credentials)); the first session start wrote one file outside the catalog ([section
  2](#2-per-user-storage)). The x64 GitHub Copilot Desktop AppImage, launched by mistake on the
  arm64 VM, failed to start and wrote nothing under `~/.copilot` ([issue
  147](https://github.com/seanthegeek/doubleagent/issues/147) tracks the desktop app). Collector
  1.13.0, run as the user (not root): 38 files collected, 2 `skipped_excluded`
  (`.copilot/installed-plugins`, `.cache/copilot/pkg`), 1 `secret: true` (`.copilot/config.json`), 0
  `skipped_secret`, and 5 `error_read` rows on other accounts' homes (permission denied, expected
  without root); project discovery found `/home/sean/demo` from `workspace.yaml`. Windows on 1.0.98
  is the winget bullet above.
- **Observed (macOS)**: Copilot CLI 1.0.98 installed with Homebrew's npm, the author's workstation,
  2026-10-15, surveyed for names, sizes, key names and types only (three interactive sessions).
  `~/.copilot` held `command-history-state.json`, `config.json` (JSONC, JSON with comments: one or
  two `//` comment lines before plain JSON, so a strict JSON parser refuses it; [section
  2](#2-per-user-storage)), empty `ide/`, `installed-plugins/`, `servers/` and an empty
  `installed-plugins.lock`, `logs/process-<epoch ms>-<pid>.log` and `.copilot-log.lock`,
  `open-sessions-state.json` (`{}`), `permissions-config.json`, `session-state/`
  (`.session-operation-locks/<uuid>.lock` and one directory per session), `session-store.db` with
  `-wal` (1.7 MB) and `-shm` (the main file 4 KB), `settings.json` and
  `sidebar-sessions-state/<sha256 of cwd>.json`. Each session directory held `events.jsonl`,
  `workspace.yaml`, `.workspace-fork.lock`, `checkpoints/index.md`, empty `files/` and `research/`,
  and `rewind-file-snapshots/` (`index.json`, `tracking.json`). No `~/.config/.copilot`,
  `~/.local/state/.copilot` or `~/.cache/copilot`. `~/Library/Caches/copilot` held
  `copilot-user-cache.json` and `exp-cache.json` (both JSONC) with `.lock` files,
  `managed-settings/<hex>.json` with `managed-settings.<hex>.order.json` and a lock,
  `marketplaces/.auto-update.lock`, `memory-enablement-cache-config.json`, and the extracted package
  `pkg/darwin-arm64/1.0.98/` (with `.extraction-complete`).

### Source reviews

- 2026-10-19: microsoft/vscode at
  [`4d22f4f`](https://github.com/microsoft/vscode/commit/4d22f4f922eb012217ac65672ccce02f59d63706),
  for the Copilot CLI sessions that VS Code's Copilot Chat extension runs in a git worktree;
  findings in [Scratch directories](#scratch-directories).

## 2. Per-user storage

Config home: `configDir ?? process.env.COPILOT_HOME ?? join(homedir(), ".copilot")` (app.js
`function dot(e)`, `dQe`; native: "Set the configuration directory (default: ~/.copilot).
Deprecated: use COPILOT_HOME env var instead"). Same on all OSes; docs confirm `~/.copilot` and
`COPILOT_HOME`.

XDG handling: on start the CLI *migrates* state out of XDG dirs into `~/.copilot` (app.js
`function CEn(e,t)`): from `$XDG_STATE_HOME/.copilot/` the entries `session-state`,
`session-store.db`, `command-history-state`, `command-history-state.json`, `installed-plugins`; from
`$XDG_CONFIG_HOME/.copilot/` the entries `config.json`, `config`, `mcp-config`, `lsp-config`,
`permissions-config`, `copilot-instructions.md`, `mcp-oauth-config`, `hooks`. So older installs with
XDG set may still have `$XDG_STATE_HOME/.copilot` and `$XDG_CONFIG_HOME/.copilot` (default
`~/.local/state/.copilot`, `~/.config/.copilot`), and symlinks are left behind (`symlinkSync` in the
same function).

### Scratch directories

VS Code's Copilot Chat extension can run a Copilot CLI session in a git worktree it creates at
`<repo parent>/<repo>.worktrees/<branch>`, unless the git extension's global state holds a
`worktreeRoot:<repo>` root
([`extensions/git/src/repository.ts:1952-1970`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/git/src/repository.ts#L1952-L1970),
[`chatSessionWorktreeServiceImpl.ts:113`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorktreeServiceImpl.ts#L113)),
and records it in `session-state/<id>/vscode.metadata.json`, whose entries carry `workspaceFolder`,
`worktreeProperties` and `additionalWorkspaces`
([`chatSessionMetadataStoreImpl.ts:170-186`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chatSessions/copilotcli/vscode-node/chatSessionMetadataStoreImpl.ts#L170-L186);
source review of microsoft/vscode at
[`4d22f4f`](https://github.com/microsoft/vscode/commit/4d22f4f922eb012217ac65672ccce02f59d63706),
2026-10-19; not seen on a real install). Such a worktree is a scratch directory of the agent, not
the user's project. It sits beside the user's repository, outside every catalog line, so it is not
collected, and `discover_projects` and `Find-Projects` do not read `vscode.metadata.json`; see
[`vscode.md`](vscode.md).

### Inside `~/.copilot`

The docs table plus the bundle:

- `session-state/<sessionId>/` session history: `events.jsonl` (runtime: "Computes the absolute path
  to a session's persisted events.jsonl file"; app.js crash report copies `e.sessionFilePath` as
  `events.jsonl`), `workspace.yaml` (app.js `loadSessionFsWorkspace`, keys `id`, `created_at`,
  `updated_at`, `name`, `user_named`, `summary_count`; `workspaceLoadPersistedSessionCwd` reads cwd
  from it), `plan.md`, `autopilot-objective.json` (app.js `copySessionFsOptionalFile`), checkpoints
  and files subdirs (`/session checkpoints|files|plan` commands). Observed at 1.0.98 (macOS and
  Linux): `checkpoints/index.md` (a Markdown table of compaction checkpoints), `files/` ("Persistent
  storage for session artifacts", `runtime.node@82945561`), `research/`,
  `rewind-file-snapshots/index.json` and `tracking.json` (file snapshots for `/rewind`,
  `runtime.node@82575983` `rewind-file-snapshotstracking.json`), `.workspace-fork.lock`; beside the
  session directories `.session-operation-locks/<uuid>.lock` (`runtime.node@82828676`). The bundle
  also names `session-state/<id>/session.db`, a per-session SQLite of the agent's todo tables
  (`cli-main.js@149653` `this.join(this.sessionStatePath,"session.db")`; not observed), and the
  legacy flat transcript `session-state/<id>.jsonl` that 1.0.98 no longer reads
  (`cli-main.js@1654639` `Rwr=".jsonl"`).
- `session-store.db` SQLite "cross-session data such as checkpoint indexing and search" (docs;
  runtime SQL `FROM checkpoints ... session_id, checkpoint_number`), in WAL mode
  (`runtime.node@80402520` `PRAGMA journal_mode = WAL`): on the 1.0.98 install the rows were in the
  `-wal` sidecar, so the sidecars must be collected with it. Tables and their writers are in
  [section 5 of
  `analyzer/research/copilot-cli.md`](../../analyzer/research/copilot-cli.md#5-other-stores).
- `command-history-state.json` `{commandHistory: [...]}`, the Ctrl+R prompt history, newest first,
  at most 50 by default (observed at 1.0.98; the docs still name a `command-history-state/`
  directory). `open-sessions-state.json` open-session tracker (`runtime.node@79300674`
  `open-sessions`). `sidebar-sessions-state/<sha256 of cwd>.json` `{schemaVersion, cwd, sessionIds}`
  (real install; the file name is the sha256 of `cwd`, verified; `runtime.node@87698768`
  `sidebar-sessions`). `servers/` and `installed-plugins.lock` (observed, empty).
- Docs-only at 1.0.98 (not observed): `extensions/`, `mcp-secrets/` ("Local fallback storage and
  index for MCP secret placeholders"; `cli-main.js@5455460` `huo="mcp-secrets"`), `plugin-data/`
  (`cli-main.js@1688706`), `providers.json` (the BYOK, bring-your-own-key, provider and model
  registry; `cli-main.js@4314272` `jwr="providers.json"`, overridable with
  `COPILOT_PROVIDERS_CONFIG`).
- `logs/` process logs (native: "Set log file directory (default: ~/.copilot/logs/)"); local
  `logs/process-<epoch>-<pid>.log`. The process log rotates at 10 MB to
  `process-<epoch>-<pid>.<n>.log` (`.1.log` to `.4.log` observed on Windows 1.0.98). A login left
  pending loops on Windows 1.0.98: the winget install wrote about 280,000 lines in 74 seconds while
  a device code waited, four rotated files of 10 MB and a 3 MB live log ([section
  1](#1-source-and-evidence)), so a collection can carry 45 MB of login-loop log. The logs stay
  collected and are not excluded ([section 4](#4-exclusions)), because the sign-in lines that name
  the account are in them. `ide/<uuid>.lock` IDE discovery lock files (app.js `QB` scans
  `Gi(e,"state")/ide` for `.lock`; local `ide/`). `state/` for the session store default path
  (app.js `sessionStoreDefaultPath(Gi(e,"state"))`).
- `config.json` "automatically managed application state (authentication, installed plugins...)"
  (docs), `settings.json` user settings (docs; runtime "Settings migration ... between config.json
  and settings.json"; written on the macOS install, absent on the Linux one), `mcp-config.json`
  (native help text; observed on Windows with `.mcp-writer.binding` and `.mcp-writer.lock` beside
  it, the writer's lock and its binding to the file's volume and file index), `mcp-oauth-config`
  (app.js `JDn="mcp-oauth-config"`), `permissions-config.json`, `lsp-config`,
  `command-history-state/`, `installed-plugins/<marketplace>/<plugin>` (docs; runtime
  "installed-plugins root"), `copilot-instructions.md`, `instructions/*.instructions.md`,
  `agents/*.agent.md`, `skills/<name>/SKILL.md`, `hooks/` (docs; app.js help list
  `$HOME/.copilot/copilot-instructions.md`, `$HOME/.copilot/instructions/**/*.instructions.md`).

### Package and cache directory

- Package cache for auto-update (sea-loader `Xi()`): `$COPILOT_PKG_CACHE_HOME/pkg`,
  `$COPILOT_CACHE_HOME/pkg`, `~/Library/Caches/copilot/pkg` (macOS), `%LOCALAPPDATA%\copilot\pkg`
  (Windows), `$XDG_CACHE_HOME/copilot/pkg` or `~/.cache/copilot/pkg` (Linux), `$COPILOT_HOME/pkg`,
  `~/.copilot/pkg`; extraction marker `.extraction-complete`. Local
  `~/.cache/copilot/copilot-user-cache.json` (runtime literal `copilot-user-cache`). On macOS 1.0.98
  `~/Library/Caches/copilot`, and on Linux 1.0.98 `~/.cache/copilot` with the same names, also held
  `exp-cache.json` (the ExP experiment-assignment cache; ExP is Microsoft's experimentation
  service), `managed-settings/` ("cache for enterprise managed settings, safe to delete",
  `runtime.node@79814215`; on the Windows winget install also `managed-settings.<sha256>.fence`,
  36 bytes, beside the `.order.json` and `.lock`, contents not read),
  `memory-enablement-cache-config.json` and `marketplaces/`, each with `.lock` files.
- Five of these files are JSONC, not JSON (Linux install): `config.json`, `copilot-user-cache.json`,
  `exp-cache.json`, `memory-enablement-cache-config.json` and `managed-settings/<hex>.json` start
  with one or two `//` comment lines ("Disposable cache for ..., safe to delete. Managed
  automatically." and "User settings belong in settings.json.") and then hold plain JSON, which is
  why the macOS survey could not parse them. Shapes observed on Linux: `copilot-user-cache.json` is
  `copilotUserCache{<key>: {schemaVersion, generation, retrievedAt, response}}`, where `response` is
  the Copilot user entitlement response (`login`, `copilot_plan`, `access_type_sku`,
  `organization_login_list`, `organization_list`, `enterprise_list`,
  `endpoints{api, origin-tracker, proxy, telemetry, exp}`,
  `quota_snapshots{chat, completions, premium_interactions}` with entitlement and remaining counts,
  `quota_reset_date`, and feature flags such as `chat_enabled`, `is_mcp_enabled`,
  `codex_agent_enabled`, `cloud_session_storage_enabled`, `cli_remote_control_enabled`);
  `exp-cache.json` is
  `expAssignmentsCache{"v3:<hex>": {schemaVersion, retrievedAt, response{Features[...], ...}}}`
  (feature names such as `anthropic_tool_search_enabled`, `openai_toolsearch_enabled`,
  `gpt-default`); `managed-settings/<hex>.json` is
  `{schemaVersion, retrievedAtMs, account, response, ignoredPaths[]}` (`response` null), beside
  `managed-settings.<hex>.order.json` `{lastAppliedOrder, nextOrder}`;
  `memory-enablement-cache-config.json` is
  `memoryEnablementCache{"v1:<hex>": {schemaVersion, retrievedAt, enabled}}`.
- `marketplaces/.auto-update.lock` was the only file in `marketplaces/` on macOS and Linux. On
  Windows (CLI 1.0.99-2, bundled with Copilot Desktop) the same directory held `freshness.json`
  (98 bytes), `github-awesome-copilot.lock` (0 bytes) and `github-awesome-copilot/`, a shallow git
  clone of the awesome-copilot plugin marketplace (4,533 files and 160 MB outside its `.git`),
  263 MB in all; it is excluded from collector 1.13.0 ([section 4](#4-exclusions), [issue
  131](https://github.com/seanthegeek/doubleagent/issues/131)).
- Also on Windows: `mcp-tools/<sha256>.json`, one file per MCP server that connected in a session
  (two files of 20,383 and 20,384 bytes, written at 19:59:20Z and 20:04:57Z by the two sessions that
  connected, both naming `playwright`), shape `{schemaVersion, serverName, tools: [{name,
  description, annotations{destructiveHint, openWorldHint, readOnlyHint, title}, inputSchema{...}}],
  updatedAt}`, the cached tool list of a connected MCP server (25 tools); collected.

### Outside the catalog

- Outside `~/.copilot` and the cache, not in the catalog: the first session start on Linux wrote
  `~/.cache/Microsoft/DeveloperTools/deviceid` (36 bytes, a UUID), the device id Microsoft's
  developer tools share ([issue 148](https://github.com/seanthegeek/doubleagent/issues/148)); on
  Windows the login of the winget install created the registry value
  `HKCU\SOFTWARE\Microsoft\DeveloperTools\deviceid` instead, as Copilot Desktop's did, and no file.
  The winget install puts the executable in
  `AppData/Local/Microsoft/WinGet/Packages/GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe/`
  (`copilot.exe` and winget's own `.db`), outside every catalog entry, like the npm global directory
  on Linux; the program holds no user state.
- System policy: `/etc/github-copilot/managed-settings.json`, `/etc/github-copilot/policy.d`
  (runtime).

## 3. Credentials

- GitHub token: OS keyring by default (runtime vendors `keyring-core` and
  `zbus-secret-service-keyring-store`; env `COPILOT_DISABLE_KEYTAR`), with `storeTokenPlaintext`
  setting "Store auth token in plaintext (less secure)" (runtime settings schema) which puts it in
  `config.json` ("authentication" per docs). On the Linux install `copilot login` wrote the token to
  the GNOME keyring (`~/.local/share/keyrings/login.keyring`, modified at the minute of the login),
  as the runtime's keyring-store strings predict, and `config.json` held no token: its keys were
  `loggedInUsers[{host, login, kind}]`, `lastLoggedInUser{host, login}`, `firstLaunchAt`,
  `appTipShown` and a fifth key of 20 or more characters whose name was not recorded; the Windows
  winget install named it: `reasoningSummariesCleanupDone` (418-byte `config.json` after the login,
  the same five keys). On that install the login wrote two Windows Credential Manager files
  (Credential Manager is Windows' per-user credential store) under
  `AppData/Roaming/Microsoft/Credentials/` (634 and 666 bytes) in the same second, so the token went
  to Credential Manager as Copilot Desktop's did; the target name was not determined (unreadable
  from the SSH session), and `config.json` held no token. Keep `config.json` a secret glob for the
  plaintext fallback.
- `copilot-user-cache.json` holds no token (Linux install; shape in [section
  2](#2-per-user-storage)): it names the login, plan, organizations and quotas, and stays collected
  and unflagged, which answers [issue 130](https://github.com/seanthegeek/doubleagent/issues/130)
  for that file. The process log names the login twice, in the sign-in line and in the
  managed-settings fetch line.
- Env precedence `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`; falls back to `gh auth token`
  (app.js `Lgo`, runtime "`gh auth token` stdout collection"), so `~/.config/gh/hosts.yml` is a
  related credential.
- `mcp-oauth-config` MCP OAuth store (`copilot-mcp-oauth-store-key-v1`); `mcp-config.json` can embed
  headers/tokens, and on the Windows install it did: the `github` server's `env` held
  `GITHUB_PERSONAL_ACCESS_TOKEN`, a 33-character GitHub personal access token in plain text, written
  when the user added the server from Copilot Desktop's settings; the secret glob
  `.copilot/mcp-config.json` flagged it. `settings.json`
  `sandbox.userPolicy.network.proxy.password`.
- The CLI does not use `~/.config/github-copilot/{hosts,apps}.json` (no hit in app.js, native or
  runtime).

## 4. Exclusions

`.copilot/pkg`, `.cache/copilot/pkg`, `Library/Caches/copilot/pkg`, `AppData/Local/copilot/pkg`
(extracted ~180 MB packages per version; 192 MB for `win32-arm64/1.0.99-2`),
`.copilot/installed-plugins` (marketplace copies; keep manifests if desired). Keep `logs/`,
`session-state/`, `session-store.db`.

From collector 1.13.0 also `.cache/copilot/marketplaces`, `Library/Caches/copilot/marketplaces` and
`AppData/Local/copilot/marketplaces`: the git clone of each plugin marketplace the CLI reads (263 MB
and 4,560 files on the Windows install, where walking it took 2 min 6 s of a 3 min 29 s collection;
[issue 131](https://github.com/seanthegeek/doubleagent/issues/131)). The `skipped_excluded` row
keeps the directory's size, but which marketplaces were cloned, and when, is inside it and is lost;
`--full` collects it.

## 5. Project-local files

`.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`,
`.github/git-commit-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.claude/rules/**/*.md`
(read; app.js help list), `.github/copilot/settings.json`, `.github/copilot/settings.local.json`
(app.js `LO`), `.mcp.json`, `.github/mcp.json` (native help), `.github/lsp.json`, `.github/hooks/`,
`.github/skills/`, `.github/agents/` (app.js). No per-project database.

## 6. Where the project path is recorded

`session-state/<id>/workspace.yaml` persisted session cwd (app.js
`workspaceLoadPersistedSessionCwd(FP(Wp(e,t),"workspace.yaml"))`); key name not visible in the JS
(handled natively), grep for an absolute path. Observed at 1.0.98: `workspace.yaml` keys, in order,
`id`, `cwd`, `client_name`, `name`, `user_named`, `summary_count`, `fork_count`, `created_at`,
`updated_at`, `remote_steerable`, `mc_task_id`, `mc_session_id`, `mc_last_event_id` (the `mc_` keys
are Mission Control ids, GitHub's remote session mirror); `remote_steerable` and the three `mc_`
keys mark a session synced to the account: the winget install's `workspace.yaml` gained them when
the session was resumed, and every Copilot Desktop session carries them. They live only in
`workspace.yaml`, so a session deleted locally and remotely leaves no local record that it was ever
synced. The analyzer yields no row for them yet ([issue
151](https://github.com/seanthegeek/doubleagent/issues/151)). `cwd` is the project path;
`client_name` was `github/cli` on both Linux sessions.

`permissions-config.json` is "organized by project location" (docs):
`{locations: {<abs path>: {tool_approvals: [{kind, ...}], allowed_directories: [...]}}}`, keyed by
git root or cwd (docs; observed two locations with `write` approvals on macOS, and on Linux one
location, `~/demo`, with one `write` approval and no `allowed_directories` key;
`runtime.node@82849229` `tool_approvalsallowed_directories`).

`settings.json` `allowedUrls` and `deniedUrls` hold URL rules (`runtime.node@79085397`; observed
four `allowedUrls` on macOS); the docs say it is JSON with comments.

`sidebar-sessions-state/*.json` `cwd` maps a project path to its session ids, and outlives the
project: the removed `~/secret` kept its file on Linux. `events.jsonl` `session.start`
`data.context.cwd` and `session-store.db` `sessions.cwd` carry it too. `session-store.db` rows carry
`session_id` and checkpoints (analyzer).

## 7. Confidence

High: config home and `COPILOT_HOME`, directory names (docs plus bundle), XDG migration list, pkg
cache locations (`~/Library/Caches/copilot` on macOS, `~/.cache/copilot` on Linux and
`AppData/Local/copilot` on Windows observed, the last through Copilot Desktop's bundled CLI 1.0.99-2
and the winget install of 1.0.98), log dir, keyring/plaintext token model (token in the GNOME
keyring observed on Linux); the `session-state/<id>/` file set, the `workspace.yaml` keys (cwd in
`cwd`), the `session-store.db` schema and the `permissions-config.json` shape (real installs on
macOS and Linux at 1.0.98 plus bundle; the file set and `workspace.yaml` keys also on Windows at
1.0.99-2); `mcp-config.json` holding a plain-text token under a server's `env`, the
`mcp-tools/<sha256>.json` shape and the marketplace clone's size (real install on Windows);
`config.json` is JSONC with account keys and no token on a keyring install, and
`copilot-user-cache.json` is the entitlement response with no token (Linux install). Medium:
`state/ide` vs `ide/` (both installs show `ide/` at top level, code joins through a "state"
resolver); `session.db`, `plan.md` and `mcp-secrets/` (bundle or docs, not observed); the
`config.json` token field name under `storeTokenPlaintext` (not observed). High since the Windows
winget round (1.0.98, 2026-10-17): the standalone CLI's Windows layout under
`%USERPROFILE%\.copilot` and `AppData\Local\copilot`, the fifth `config.json` key, the token going
to Windows Credential Manager, the registry device id and the `mc_` keys added at a resume. Not
determined: why `session-store.db` reported `schema_version` 8 on Linux and 38 on macOS for the same
1.0.98; the Credential Manager target name; what the `managed-settings.<sha256>.fence` file holds;
the layout of an npm-installed CLI on Windows ([issue
133](https://github.com/seanthegeek/doubleagent/issues/133)).
