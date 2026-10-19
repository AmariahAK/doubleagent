# copilot-desktop

Catalog agent: `copilot-desktop` (GitHub Copilot Desktop, the desktop app
GitHub ships as the dpkg package `github` on Linux and as the per-user
installer `GitHub-Copilot-windows-<arch>-setup.exe` on Windows). The app
runs its sessions through a bundled copy of Copilot CLI and shares
`~/.copilot` with it: the session logs under `~/.copilot/session-state/`
are Copilot CLI's format and stay with the `copilot-cli` agent
([`copilot-cli.md`](copilot-cli.md)); nested catalog entries claim the
app's own files inside that directory. How its store is encoded and how a
parser reads it is in
[`analyzer/research/copilot-desktop.md`](../../analyzer/research/copilot-desktop.md).
[Issue 147](https://github.com/seanthegeek/doubleagent/issues/147) tracks the app.

## 1. Source and evidence

Closed source. GitHub Copilot Desktop is a Tauri app: Tauri is a desktop
framework that draws the user interface in the operating system's web
engine (on Linux WebKitGTK, the GTK port of the WebKit browser engine;
the package depends on `libwebkit2gtk-4.1-0`) and runs the backend as a
native Rust program; on Windows the web engine is WebView2, Microsoft
Edge's Chromium engine packaged for embedding in other applications. The
app identifier is `com.github.githubapp`. Each claim names its evidence
level:

- **Shipped binary**: `GitHub-Copilot-linux-arm64.deb` (464 MB), dpkg
  package `github` 1.1.29, maintainer "you", description "Tauri Copilot
  Application", installed size 1,609,955 KB. `/usr/bin/github` is a
  1,388,701,168-byte ELF aarch64 executable with debug information, not
  stripped (`file`: BuildID
  `337d94e3f5709ec9c61ece90f86958a5d141a9e3`), sha256
  `9f6259e76190ef3fd89561e594a0a6fad0967bddc2faf3b119c8bafa3097ec27`;
  the `.deb` is
  `51117b94e5e278e609d9f568857c86d7b45cbc98d8d09b20497134377c33351b` and
  `/usr/bin/git-credential-copilot` (4,342,424 bytes)
  `5e89734fe81b21dfa32c8b4473e7d055b38586804e23ed03a79353dc35ce32f1`.
  It was read with `strings` and `grep` only, never run by the research.
  Citations are written `github 1.1.29 linux-arm64 /usr/bin/github` with
  the literal snippet, shortened after this paragraph to "binary" and the
  snippet; no byte offsets were recorded,
  so grep for the snippet. Its Rust crates include `github_app`,
  `github_app_desktop_services`, `github_app_storage`,
  `github_app_database`, `github_copilot_sdk` and
  `github_app_git_native`; the paths module is
  `crates/desktop-services/src/platform/paths.rs` (binary). The package's
  TypeScript declarations under `/usr/lib/GitHub Copilot/copilot-sdk/`
  were read with `grep` and `sed`.
- **Dirs crate**: the binary links the Rust `dirs` crate (binary:
  `index.crates.io-1949cf8c6b5b557f/dirs-6.0.0`, with `dirs-5.0.1` and
  `dirs-4.0.0` beside it), whose data directory is
  `~/.local/share` on Linux, `~/Library/Application Support` on macOS and
  `%APPDATA%` (`AppData/Roaming`) on Windows, and whose cache directory is
  `~/.cache` on Linux and `%LOCALAPPDATA%` (`AppData/Local`) on Windows.
  The Windows install confirmed both Windows directories (the data
  directory held only `app-skills/`, and the three tool downloads went to
  `AppData/Local`); the Windows binary carries no `dirs-<version>` string,
  so the crate is inferred there from the paths, not read. The macOS paths
  in this document are derived from the crate's behaviour and the app
  identifier, not observed.
- **Shipped binary (Windows)**: `GitHub-Copilot-windows-arm64-setup.exe`
  (297,454,576 bytes, sha256
  `d63b70c36d61a090a4a455dc8b67c538374328304846035e44b2740781e2a4dd`,
  version resource 1.1.30, product name "GitHub Copilot"), an NSIS
  installer (Nullsoft Scriptable Install System, an installer framework;
  the install directory holds its `uninstall.exe` and the icons directory
  its `nsis-header.bmp` and `nsis-sidebar.bmp`). It installs per user
  into `AppData/Local/Programs/GitHub Copilot/` (312 files, 520 MB):
  `github.exe` (442,207,520 bytes, sha256
  `8e9b4162ee7c0d7c7212c3b34b05c7bd8809af24494ab4560f2fc2d4536288e5`,
  FileVersion 1.1.30, CompanyName "GitHub Inc.") and
  `git-credential-copilot.exe` (289,568 bytes, sha256
  `d538676354421560ede7e3490f0661c24ef8698fbbcd62f6b9ea15ea533d3af6`),
  read on the VM with a string search only. Citations are written
  `github 1.1.30 windows-arm64 github.exe` with the literal snippet; no
  byte offsets were recorded.
- **Docs**: none fetched.

### Observed

- **Observed (Windows), deletion and quit**: the VM and app of the next
  bullet. At
  20:31Z the user deleted the general chat with the app's own delete
  action and a listing diff was taken; at 20:35Z the user quit the app from
  the system tray (no `github.exe` or `copilot.exe` process was left) and
  a second listing was taken. The deletion removed the chat's
  `session-state/<uuid>/` directory entire and its working directory under
  `chats/`, including the project the agent had built there and its
  `node_modules`; what survived is in [section 2](#deletion). Quitting
  checkpointed `data.db`: its `-wal` went to 0 bytes and the main file grew from
  1,347,584 to 1,433,600 bytes.
- **Observed (Windows)**: GitHub Copilot Desktop 1.1.30, the arm64 NSIS
  installer above, installed per user at 19:48Z on 2026-10-17 on a
  Windows 11 ARM64 Parallels VM (build 10.0.26300.9550, Windows
  PowerShell 5.1.26100.9549, user `sean`, home `C:\Users\sean`),
  surveyed over SSH for names, sizes, modification times, key names and
  types only; all times are UTC. Exercised: first start at 19:53:23Z;
  sign-in by device-code flow (a sign-in under OAuth, the open standard
  for delegated authorisation, in which the app shows a short code that
  the user enters on github.com in a browser) at 19:54:27Z; three MCP
  servers (Model
  Context Protocol servers, programs that offer the agent extra tools)
  added from the app's settings at 19:56Z, two of which could not start
  because their commands were not installed; a general chat (created
  19:59:11Z, three prompts at 20:00:04Z, 20:02:02Z and 20:02:49Z) in
  which the agent built and tested a small Node.js MCP server in the
  chat's working directory, running `npm install` there; the GitHub
  repository `seanthegeek/doubleagent` added at 20:04:45Z, cloned and
  checked out into a git worktree (a second working directory of the
  same repository on its own branch), and one prompt in a project session
  (20:05:27Z, one `powershell` call, one checkpoint at 20:05:40Z). The
  user had installed Node.js 24.22.0 and the Visual Studio Build Tools
  beside the app for the MCP work; `AppData/Local/npm-cache` is theirs.
  What each surface wrote: the app's own files inside `.copilot` and
  outside it ([section 2](#2-per-user-storage)), the WebView2 user data
  folder `AppData/Local/com.github.githubapp/EBWebView/`, three tool
  downloads under `AppData/Local`, and, through the bundled Copilot CLI
  1.0.99-2, the session directories, `session-store.db`, `mcp-config.json`
  and the CLI cache `AppData/Local/copilot`
  ([section 1 of `copilot-cli.md`](copilot-cli.md#1-source-and-evidence)).
  The app also pre-created seven pool and probe sessions that were never
  prompted (no `events.jsonl`). Every action ran before the first
  listing, so no per-action listing diff exists for them; the times above
  and the files' modification times are the only mapping from action to
  file, as on Linux. Not exercised: a scheduled task, a session
  automation, a denied tool call (allow-all stayed on), a model switch, a
  resumed session, a fork, a side chat, a remote session. Collector 1.13.0
  as first written, run as the user in an administrator SSH session while
  the app ran: 8,111 files collected (283,808,459 bytes), 6
  `skipped_excluded`, 1 `error_copy` (`.copilot/run/single-instance.lock`,
  "The process cannot access the file because another process has locked
  a portion of the file"), 0 `error_read`; `copilot-cli` 4,641 files and
  265,398,349 bytes (4,560 files and 263,616,505 bytes of them the
  marketplace clone in `AppData/Local/copilot/marketplaces`),
  `copilot-desktop` 3,470 files and 18,410,110 bytes (3,415 files and
  14,781,620 bytes of them `.copilot/chats`, nearly all the chat project's
  `node_modules`); 3 min 29 s, 2 min 6 s of it in
  `AppData/Local/copilot`. Secret rows, all collected:
  `.copilot/config.json`, `.copilot/mcp-config.json`, `.copilot/run/ws.token`,
  `.copilot/run/ws.release.token`. The WebView2 folder was not collected
  (no catalog entry), and project discovery reported the app's install
  directory as a project ([section 6](#6-where-the-project-path-is-recorded)).
  Both led to catalog changes in the same version ([section 4](#4-exclusions)).
- **Observed (Linux), deletion**: the VM and app of the next bullet
  (GitHub Copilot Desktop 1.1.29), at 02:05Z on 2026-10-17 (22:05 on 2026-10-16 in the
  VM's local time; the app log stamps `delete_workspace` 02:05:17Z and
  `delete_session` 02:05:31Z). The user restarted the app and
  deleted both sessions of the first round, the general chat
  (`5d404e14…`) and the project session (`79255eab…`), with the app's own
  delete action; the app log calls the two operations `delete_session`
  and `delete_workspace`, and the app sends the bundled CLI
  `sessions.delete`. A listing diff (names and counts only) was taken
  afterwards. Removed: both `session-state/<uuid>/` directories entire,
  the chat directory, the worktree and its branch, and in `data.db` the
  general chat's `sessions` row and every `workspaces`, `worktrees`,
  `workspace_session_aliases` and `workspace_checkout_bindings` row;
  `session_deletion_intents` stayed empty (0 rows before and after).
  Survived: the Copilot CLI store `session-store.db` with both sessions'
  prompts and replies, the project session's `data.db` `sessions` row and
  checkpoints, the deleted rows' pages in `data.db-wal`, four checkpoint
  refs in the clone's `.git`, the app log's deletion lines and the file
  the agent wrote ([section 2](#deletion) lists each).
  The `.copilot/repos` exclusion of collector 1.13.0 as first written
  dropped those refs with the clone, so each clone's `.git` became a
  nested catalog entry of its own ([section 4](#4-exclusions)). Two more
  sessions existed by then,
  `83277a7e…` (created 22:15Z) and `4c088c7e…` (created 23:01Z), both
  with `client_name` `github/autopilot`, `user_named` false, no
  `events.jsonl` and a `cwd` under `.copilot/` (a `canvas-catalog-probe`
  `cwd` belongs to one of them), and the app created an empty general
  chat, `4e347d3e…` (`chats/2026-10-16/symmetrical-telegram-4e347d3e/`),
  at the restart. None of the three was exercised.
- **Observed (Linux)**: GitHub Copilot Desktop 1.1.29, the arm64 `.deb`
  installed at 21:59Z on 2026-10-16 on an Ubuntu 26.04.1 arm64 Parallels
  VM (home `/home/sean`, `/bin/sh` dash) that already held the Copilot CLI
  1.0.98 round's `~/.copilot`
  ([section 1 of `copilot-cli.md`](copilot-cli.md#1-source-and-evidence)),
  surveyed for names, sizes, modification times, key names and types only.
  Exercised: app start at 22:00:30Z; sign-in by device-code flow (app
  log task `auth_device_code_flow`), after
  which `~/.local/share/keyrings/login.keyring` was modified at 22:01:14Z;
  one general chat (created 22:01:27Z, one prompt, no tool call, titled by
  the user); then the user added the GitHub repository
  `seanthegeek/doubleagent`, which the app cloned and checked out into a
  git worktree at 22:03Z, and asked one question in a project session
  (created 22:03:11Z, four prompts, `bash` called twice and `create` once;
  the `create` call wrote a file on the user's desktop, outside the
  worktree). Every action ran before the first listing, so no per-action
  listing diff exists; the times above and the files' modification times
  are the only mapping from action to file. Not exercised: a scheduled
  task, a session automation, a removed project, a denied tool call, a
  model switch, a remote session (a session deleted from the app is the
  bullet above). Collector
  1.13.0, run as the user before the catalog had this agent: 770 files,
  24.7 MB, every one attributed to `copilot-cli` (262 of them the clone
  and the worktree), 2 `skipped_excluded`, 1 `secret: true`
  (`.copilot/config.json`), 5 `error_read` rows on system accounts;
  project discovery reported the chat directory and the worktree as
  projects ([section 6](#6-where-the-project-path-is-recorded)).
- macOS was not observed.

### Source reviews

None.

## 2. Per-user storage

### Scratch directories

The app's own working directories, which are not projects the user works in
([section 6](#6-where-the-project-path-is-recorded)): a general chat's
`~/.copilot/chats/<date>/<slug>-<id8>/`, a project session's worktree under
`~/.copilot/repos/copilot-worktrees/`, the clone under `~/.copilot/repos/`,
`~/.copilot/canvas-catalog-probe/` and, on Windows, the install directory
`AppData/Local/Programs/GitHub Copilot`; the last three were the `cwd` of the pool
and probe sessions the app pre-creates ([Inside `~/.copilot`](#inside-copilot)).

### Package files

Linux (shipped binary, real install (Linux)):
`/usr/bin/github`, `/usr/bin/git-credential-copilot` (4,342,424 bytes,
the git credential helper, [section 3](#3-credentials)), and
`/usr/lib/GitHub Copilot/` (244 MB): `Microsoft.AI.Foundry.Local.Core.so`,
`libonnxruntime.so`, `libonnxruntime-genai.so` and
`libonnxruntime_providers_shared.so` (Foundry Local, Microsoft's runtime
for running models on the local machine, built on ONNX Runtime,
Microsoft's inference engine for models in the ONNX format, Open Neural
Network Exchange), `app-extensions/` (`README.md`, `catalog.json`,
`azure-devops/`), `copilot-extension-host/`, `copilot-sdk/` (TypeScript
declarations, `extension.js` and four Markdown guides under `docs/`; SDK,
software development kit, here GitHub's library that embeds and drives
the Copilot CLI), `icons/`, `native-plugins/`
(`libgithub_app_linux_pulse_plugin.so`), `plugins/` (empty), `sounds/`,
`terminal-integration/` (shell integration scripts for bash, zsh, fish
and PowerShell). Desktop entries `/usr/share/applications/GitHub
Copilot.desktop` (`Exec=github %u`, `StartupWMClass=github`, URL schemes
`github-app`, `ghapp` and `gh`) and, written by the app at first start,
`~/.local/share/applications/com.github.githubapp.desktop` (138 bytes;
not collected, outside every entry).

Windows (shipped binary, real install (Windows)): the per-user
install directory `AppData/Local/Programs/GitHub Copilot/` holds
`github.exe`, `git-credential-copilot.exe`,
`Microsoft.AI.Foundry.Local.Core.dll` (24 MB), `onnxruntime.dll`,
`onnxruntime-genai.dll`, `onnxruntime_providers_shared.dll`,
`uninstall.exe`, and the directories `app-extensions/` (`catalog.json`,
`README.md`, `azure-devops/`), `copilot-extension-host/preloads/`,
`copilot-sdk/` (TypeScript declarations, `index.js`, `extension.js`;
`cliVersion.d.ts` sets `COPILOT_CLI_VERSION = "1.0.99-2"` and
`COPILOT_CLI_USE_NPM_PACKAGE = false`, `sdkProtocolVersion.d.ts` sets
`SDK_PROTOCOL_VERSION = 3`), `icons/`, `plugins/`, `sounds/` and
`terminal-integration/` (the Linux scripts plus `shellIntegration.ps1`).

Unlike the Linux package's empty `plugins/`, the Windows one holds three
built-in plugins: `computer-use/` (`computer-use-mcp.exe`,
`CopilotComputerUse.exe`, `mcp.json`, `plugin.json`,
`github-app-integrity.json`), and `excel-agent/` and `word-agent/` (each
`plugin.json`, `github-app-integrity.json`, two skills under `skills/`
and `com.github.copilot/extensions/`). The install directory is outside
every catalog entry.

The installer registers, under HKCU
(`HKEY_CURRENT_USER`, the registry hive of the signed-in user), the
uninstall key
`HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\GitHub Copilot`
(DisplayName "GitHub Copilot", DisplayVersion 1.1.30, Publisher "GitHub
Inc.", InstallLocation the directory above, EstimatedSize 508107 KB) and
the URL protocol handlers `HKCU\Software\Classes\github-app`, `ghapp` and
`gh` (each `shell\open\command` runs `github.exe "%1"`), with no Run
(autostart) entry, and the shortcuts `AppData/Roaming/Microsoft/Windows/Start
Menu/Programs/GitHub Copilot.lnk` and `Desktop/GitHub Copilot.lnk`. The
registry is outside the collector's scope.

### Inside `~/.copilot`

The app resolves `~/.copilot` as Copilot CLI does, through `COPILOT_HOME`,
and an app-only override `COPILOT_HOME_OVERRIDE` (binary:
`github_app_desktop_services::platform::paths::COPILOT_HOME_OVERRIDE`). The
neighbouring string run in the binary lists the names it builds under it:

```text
copilot-worktreesdata.dbattachmentsmedia-cachesession.dbCOPILOT_HOMEchatscrash-reportsfilesplan.mdsession-state
```

Shared with Copilot CLI (real install (Linux)): `session-state/<uuid>/`
holds each app session in Copilot CLI's format (`events.jsonl`,
`workspace.yaml`, `checkpoints/index.md`, `files/`, `research/`,
`.workspace-fork.lock`), written by the bundled CLI; the directory name is
the session id in `data.db` `sessions.id`. A desktop session differs from a
CLI session in `workspace.yaml` `client_name` (`github/autopilot`, where
the CLI writes `github/cli`), `user_named` true, and, for a project
session, `git_root`, `repository`, `host_type` and `branch` after `cwd`;
neither had `mc_last_event_id`. Each directory also held `session.db`
(192 KB SQLite, the per-session workflow and factory store that
[section 2 of `copilot-cli.md`](copilot-cli.md#2-per-user-storage) names
from the bundle; its tables are in
[section 5 of `analyzer/research/copilot-desktop.md`](../../analyzer/research/copilot-desktop.md#sessiondb-and-hsts-storagesqlite)),
`inuse.<pid>.hold` (0 bytes) and `inuse.<pid>.lock` (6 bytes). Two more
directories, `session-state/pending-session:<uuid>/files/` and
`session-state/pending-session:draft:<uuid>/files/`, were created empty
at 22:03Z.

`extensions/` (empty) is also a CLI directory: the SDK guide names "the
user's copilot config extensions directory" (shipped binary,
`copilot-sdk/docs/extensions.md`), so it stays with `copilot-cli`.
`logs/process-<epoch ms>-<pid>.log` (six files) are the bundled CLI's
process logs and stay with `copilot-cli` too (lines such as "Starting CLI
in server mode (stdio)", `Created session: <uuid>`, "Installed N native
extension(s) for session",
`Cleaning up session <uuid>: Session deleted via sessions.delete`).
`~/.cache/copilot/` gained `tgrep-serve.lock`, and
`copilot-user-cache.json` grew to 6.5 KB.

On Windows (real install, CLI 1.0.99-2) `.copilot` sits at the top of the
profile (`C:\Users\sean\.copilot`, the `COPILOT_HOME` default under
`USERPROFILE`; `github.exe` and the CLI's `copilot.exe` both carry the
strings `COPILOT_HOME`, and `copilot.exe` also `USERPROFILE`) with the
same layout. The bundled CLI wrote `config.json`, `session-store.db`, 17
process logs, `session-state/`, `extensions/` (empty) and
`installed-plugins/` (empty).

Adding MCP servers from the app's settings
(app log message kind `add_mcp_config_server`) wrote the CLI's
`mcp-config.json` (725 bytes; shape
`mcpServers{<name>{type: "local", command, args[], tools[], env{}}}`; one
server's `env` held a GitHub personal access token in plain text,
[section 3](#3-credentials)), `.mcp-writer.binding` (157 bytes JSON,
`lock{file_index, platform: "windows", volume}` and `root{...}`) and
`.mcp-writer.lock` (0 bytes), all collected as `copilot-cli`; the CLI's
cache gained `mcp-tools/<sha256>.json`, the cached tool list of each MCP
server that connected
([section 2 of `copilot-cli.md`](copilot-cli.md#2-per-user-storage)).

`session-state/` held 18 `.session-operation-locks/<uuid>.lock` files but
only 9 session directories: the CLI logs say `Created session` 18 times
and `Session deleted via sessions.delete` 9 times, so the app creates and
deletes sessions of its own. Seven of the nine were pool and probe
sessions the app pre-created and never prompted (app log tasks
`ws_session_warmup_loop`, `session_warmup_prepare`, `warm_cli_acquire`,
`warm_canvas_catalogs`): each held only `workspace.yaml`,
`.workspace-fork.lock`, `checkpoints/index.md` and empty `files/` and
`research/`, with no `events.jsonl` and no `session.db`, and
`workspace.yaml` `client_name` `github/autopilot`, `user_named` false.
Their `cwd` was the app's install directory
`C:\Users\sean\AppData\Local\Programs\GitHub Copilot` (four sessions),
`.copilot/canvas-catalog-probe` (two) or the clone
`.copilot/repos/doubleagent` (one, created after the project session,
with `git_root`, `repository`, `host_type` and `branch`). The two
exercised sessions had `events.jsonl`, `session.db` and, while running,
`inuse.<pid>.hold` and `.lock`, and their `workspace.yaml` the extra keys
`name`, `user_named: true`, `remote_steerable` and the `mc_` keys. No
`pending-session:*` directory, `rewind-file-snapshots/`, `attachments` or
`crash-reports` appeared.

App-only, all created at 22:00:30Z unless said (real install (Linux)):

| Path | Size | What it holds |
| --- | --- | --- |
| `data.db` | 1.3 MB | the app's own SQLite store (WAL mode, write-ahead log: new pages go to the `-wal` file until a checkpoint copies them into the main file; binary: `PRAGMA journal_mode=WAL;PRAGMA foreign_keys=ON;`): accounts, projects, worktrees, workspaces, sessions, activity, schedules; 110 tables |
| `data.db-wal`, `data.db-shm` | 1.67 MB, small | its WAL and shared-memory index; the WAL is larger than the main file, so both must be collected with it |
| `data.db.open-lock`, `data.db.startup-lock` | 0 bytes | lock files (binary: `db.open-lockdb.startup-lock`) |
| `repo-metadata-cache.db` (+`-wal`, `-shm`) | 4,096 (`-wal` 98,912) | GitHub metadata cache (binary: `repo-metadata-cache.db`); tables in [section 5 of the analyzer document](../../analyzer/research/copilot-desktop.md#repo-metadata-cachedb), all empty but one lifecycle row |
| `chats/<date>/<slug>-<first 8 of the session id>/` | empty | one working directory per general chat, the chat session's `cwd` (`chats/2026-10-16/automatic-barnacle-5d404e14`); on Windows the agent built a Node.js project in one (`chats/2026-10-17/refactored-barnacle-90825c78/weather-mcp/` with `package.json`, `package-lock.json`, `test-client.js`, `src/index.js` and `node_modules/`, 3,415 files and 14.8 MB in all, 4 files and 45,644 bytes without `node_modules`) |
| `repos/<name>/` | 20 MB | the clone of each added repository (remote `https://github.com/<login>/<name>.git`; its `.git/config` held no credential helper, and there was no `~/.gitconfig`); its `.git/refs/copilot/checkpoints/` holds the session checkpoint refs ([below](#deletion)) |
| `repos/copilot-worktrees/<name>/<branch>/` | in the 262 files above | the git worktree a project session runs in, on a new branch named `<login>-<adjective>-<noun>`; after the deletion round, the pool's pre-created worktree `copilot-prewarm-<adjective>-<noun>` instead |
| `run/single-instance.lock`, `run/single-instance.owner` | 0 and 5 bytes | the single-instance lock and the owning pid (binary: `single-instance.locksingle-instance.ownersingle-instance-pr.locksingle-instance-pr.owner`) |
| `run/ws.port`, `run/ws.release.port` | 11 bytes each (10 on Windows) | the port of the app's local WebSocket server |
| `run/ws.token`, `run/ws.release.token` | 49 bytes each (48 on Windows) | the WebSocket auth token ([section 3](#3-credentials)) |
| `media-cache/` | empty | media cache (binary: `"$HOME/.copilot/media-cache/**",`) |
| `canvas-catalog-probe/` | empty | canvas catalog probe (binary: `canvas-catalog-probe`) |
| `logs/github-app.<pid>.log` | 109 KB | the Tauri backend's tracing log: WebSocket server, session warm-up, the device-code sign-in, "wrote run file", "wrote WebSocket auth token", "Scheduler starting for workflows, session automations, and Scheduled tasks", git version detection, canvas catalog warm-up (each a literal in the binary) |

Named in the binary, not observed: `$HOME/.copilot/attachments/**` and
`$HOME/.copilot/workspaces/*/attachments/**` (binary: `"$HOME/.copilot/attachments/**",`,
`"$HOME/.copilot/workspaces/*/attachments/**",`), and `crash-reports`
(binary, in the string run above; also in
`github 1.1.30 windows-arm64 github.exe`: `attachments`,
`crash-reports`). They get no catalog line until an install shows them,
and the Windows install did not: `attachments` under `~/.copilot` is
collected with `copilot-cli` meanwhile.

On Windows the same app-only set was written, with these differences:
`data.db` 1,347,584 bytes (`-wal` 1,796,352 at 20:08Z, 1,907,592 at
20:32Z); the `run/` files rewritten when the app restarted its WebSocket
server (`ws.port` and `ws.token` at 20:02:41Z and 20:31:33Z), all six
still on disk after the app quit; the collector's copy of
`run/single-instance.lock` failed while the app ran, because the app
holds a byte-range lock on it (`error_copy`); `repos/<name>/.git/` held
`refs/copilot/checkpoints/<session id>/<seq>/<event id>` for the project
session's one checkpoint and `worktrees/<branch>/` for the session's
worktree and the pool's `copilot-prewarm-<adjective>-<noun>` worktree;
the app log `logs/github-app.5688.log` (193,758 bytes after quit) has the
start line `GitHub Copilot app started pid=N version=N.N.N commit=<hex>
platform=windows arch=aarch64 ...`, `opening database
db_path="C:\\Users\\sean\\.copilot\\data.db"`, `embedded git installed
path=<path>`, `Prepared executable built-in plugin plugin_name=...`
(three times) and `Executable built-in plugin is not bundled for this
platform` (once).

### Outside `~/.copilot`

| Path | Size | What it holds |
| --- | --- | --- |
| `~/.local/share/com.github.githubapp/` (Linux, observed); `AppData/Roaming/com.github.githubapp` (Windows, observed); `~/Library/Application Support/com.github.githubapp` (macOS, dirs crate, not observed) | 4.6 MB (Linux), 3.0 MB (Windows) | the Tauri data directory; on Windows it held only `app-skills/`, the web view's storage being in the WebView2 folder below |
| `.../app-skills/` | 3.3 MB (Linux), 3.0 MB and 145 files (Windows) | skills bundled with the app, copied at first start (`af`, `agent-merge`, `agentfinder`, `connector-finder`, `create-canvas`, `factory-creator`, `impeccable` with hundreds of `.mjs` scripts, `latex`, `orchestrate`, `pr-stack`, each with `SKILL.md`; 1.1.30 on Windows adds `automation-group-creator`), markers `.app-skills-bundled` and `.app-skills-version` (binary: `app-skillsapp-skills.new.app-skills-version`) |
| `.../localstorage/tauri_localhost_0.localstorage` (+`-wal`, `-shm`) | 4,096 (`-wal` 939,392) | the web view's local storage, SQLite `ItemTable(key, value BLOB)`; keys include `home-composer-draft:main` (192 bytes, the unsent composer draft), `inbox-cache` (2.5 KB) and tab lists ([section 2 of the analyzer document](../../analyzer/research/copilot-desktop.md#2-transcript-stores)) |
| `.../WebKitCache/Version 17/` | 280 KB | WebKit's HTTP cache (`Blobs`, `Records`, `salt`) |
| `.../CacheStorage/salt`, `.../storage/salt`, `.../mediakeys/v1/salt` | 8 bytes each | WebKit's per-origin salts |
| `.../hsts-storage.sqlite` | 12,288 | WebKit's HSTS store (HTTP Strict Transport Security: the hosts that must be reached over HTTPS) |
| `~/.github-copilot-cli/` | 96 KB | Foundry Local's directory, named after the app's Foundry app name `github-copilot-cli` (binary: `Skipping Foundry Local init: rate-limit cool-down recorded by a concurrent attemptgithub-copilot-cli`) |
| `~/.github-copilot-cli/cache/models/foundry.modelinfo.json` | 71 KB | the local-model catalog (44 models); downloaded weights would land under `cache/models/` (none downloaded) |
| `~/.github-copilot-cli/ep/` | empty | not determined |
| `~/.github-copilot-cli/logs/foundry.core<yyyymmdd>.log` | 3,660 | Foundry Local log: `Telemetry initialized for app 'github-copilot-cli' with Device ID: <hex>`, "Found N locally cached models", "Got N models from Azure Foundry catalog" |
| `~/Microsoft/DeveloperTools/.onnxruntime/deviceid` | 36 bytes | a UUID in a directory named `.onnxruntime`, different from the `~/.cache/Microsoft/DeveloperTools/deviceid` of [issue 148](https://github.com/seanthegeek/doubleagent/issues/148); not collected |
| `~/.cache/github-copilot-sdk/cli/1.0.95-3/copilot` | 180 MB (180,095,744 bytes, sha256 `42cf5d50353862c2a04108ae2556df8a32810ee4de8890c472600bd0abd94407`) | the Copilot CLI that runs the app's sessions, downloaded at first start, with the marker `.copilot-cli.ok` (9 bytes; binary: `.copilot-cli.ok`, `github-copilot-sdk`) |
| `~/.cache/github-copilot-git-2.53.0-4/` | 53 MB | a private git build (`bin/`, `etc/`, `libexec/`, `share/`, `ssl/`); the app log says `embedded_git_in_use=true` (binary: `github-copilot-git-`) |
| `~/.cache/copilot-desktop-gh-2.102.0/` | 38 MB | GitHub's `gh` CLI (binary: `copilot-desktop-gh-`) |
| `~/.local/share/keyrings/login.keyring` | not recorded | the GNOME keyring, modified at sign-in ([section 3](#3-credentials)) |

No `~/.config` entry was written. The layout of `~/.copilot` is the same
on every OS, as Copilot CLI's is; the Tauri data directory moves with
the dirs crate.

On Windows (real install, 1.1.30) these were written outside `.copilot`:

| Path | Size | What it holds |
| --- | --- | --- |
| `AppData/Local/com.github.githubapp/EBWebView/` | 611 files, 72,614,047 bytes | the WebView2 user data folder (binary: `EBWebView`; `Last Version` says runtime 155.0.4283.62), a Chromium profile; collected as `copilot-desktop` from collector 1.13.0, less its caches ([section 4](#4-exclusions)); itemised below |
| `AppData/Local/github-copilot-sdk/cli/1.0.99-2/copilot.exe` | 158,577,952 bytes, sha256 `b7bc340acf1c82228de2e3504444847f8e18beec1f07f72f260f1bbeb4c3a9b2` | the Copilot CLI that runs the app's sessions, with `.copilot-cli.ok` (9 bytes), downloaded 19:53:31Z to 19:53:51Z; not collected |
| `AppData/Local/github-copilot-git-2.53.0-4/` | 517 files, 114 MB | the embedded git in the MinGW layout (Minimalist GNU for Windows, the GNU toolchain port Git for Windows is built with): `clangarm64/`, `cmd/git.exe`, `etc/`, `usr/`, `LICENSE.txt` and an `.integrity-<sha256>` marker; not collected |
| `AppData/Local/copilot-desktop-gh-2.102.0/gh.exe` | 39,351,608 bytes | GitHub's `gh` CLI; not collected |
| `.github-copilot-cli/` | | Foundry Local's directory, as on Linux: `cache/models/foundry.modelinfo.json` (72,935 bytes, 44 models), empty `ep/`, `logs/foundry.core20261017.log` (3,887 bytes; its cache line names `C:\Users\sean/.github-copilot-cli/cache/models` with mixed separators, and it says "Model ... is not supported on Arm64 currently"); no device id file beside it |
| `AppData/Roaming/Microsoft/Credentials/<32 hex>` | 666 bytes | a file of Credential Manager, the per-user credential vault of Windows, written at the sign-in minute ([section 3](#3-credentials)); outside the catalog |

The three downloads under `AppData/Local` have the names Linux keeps
under `~/.cache`. No `AppData/Local/Microsoft/DeveloperTools/`,
`~/Microsoft/`, `~/.cache/`, `.onnxruntime` directory or file named
`deviceid` was in the profile to depth 6; the Microsoft developer-tools
device id of [issue 148](https://github.com/seanthegeek/doubleagent/issues/148)
is the registry value `HKCU\SOFTWARE\Microsoft\DeveloperTools\deviceid`
(a string value, type `REG_SZ`, of 36 characters) on Windows, with a
`HardwareCache` subkey.

The WebView2 folder, per directory (files, bytes), with what collector
1.13.0 excludes marked:

| Path under `EBWebView/` | Files, bytes | What it holds |
| --- | --- | --- |
| `Local State` | 1, 10,079 | Chromium's browser-wide state, JSON: `os_crypt{encrypted_key}` (the profile key, wrapped with DPAPI, the Windows Data Protection API, [section 3](#3-credentials)), `profile`, `user_experience_metrics{client_id2, machine_id, ...}`, `variations_*`, `updateclientdata` |
| `Default/Local Storage/leveldb/` | `000003.log`, `CURRENT`, `LOCK`, `LOG`, `MANIFEST-000001` | the web view's local storage, a leveldb database (Google's key-value store library, which Chromium uses for DOM storage): for the origin `http://tauri.localhost` the same keys as the Linux WebKit `localstorage` table (`home-composer-draft:main`, `inbox-cache`, `agent-tabs`, `general-chat-tabs`, `side-chat-tabs`, `workspace-tabs`, `chat-agent-tabs-partition-v1`, `chat-agent-tabs-source-v1`, `detail-cache`, `backend-instance-id`, `copilot.first-paint-theme.v1`). `000003.log` was 30 bytes while the app ran, because Chromium writes DOM storage lazily, and 6,174 bytes after the deletion |
| `Default/Session Storage/` | `000003.log` 30, then 234 | session storage, leveldb |
| `Default/Network/` | `Cookies` 20,480 and `Cookies-journal`, `TransportSecurity` 189, `Network Persistent State`, `Reporting and NEL`, `Trust Tokens`, `Device Bound Sessions`, `Sdch Dictionaries`, `SCT Auditing Pending Reports`, `NetworkDataMigrated` | the network stores; `Cookies` had 0 rows after the app quit (it cannot be opened while any `github.exe` runs, Windows error 32, a sharing violation) |
| `Default/History` | 249,856 | browsing history, SQLite: 7 `urls` rows, all `http://tauri.localhost` (the app's own pages), 16 `visits` |
| `Default/Login Data`, `Login Data For Account` | 43,008 each | saved passwords; 0 `logins` rows |
| `Default/Web Data` | 227,328 | autofill: 1 `autofill` row, 13 `autofill_edge_field_values`, 0 `token_service` |
| `Default/Vpn Tokens` | 28,672 | 0 `vpn_token_config` rows |
| `Default/Preferences`, `Default/Secure Preferences` | 8,516 and 9,856 | profile preferences (`profile{name, edge_profile_id, created_by_version, ...}`, `extensions`, `password_manager`, `edge`, `autofill`) and their integrity checks (`protection{macs, super_mac}`, message authentication codes over the settings) |
| `Default/` others | small | `Favicons`, `Top Sites`, `settings_diagnostic.log` (38 KB), `favorites_diagnostic.log`, `DashTrackerDatabase`, `DIPS`, `ServerCertificate`, `shared_proto_db/`, `Extension Rules`, `Extension Scripts`, `Extension State`, `Site Characteristics Database`, `Sync Data/LevelDB`, `EdgeSessions/SessionRestoreLog`, `Sessions/` (empty), `README` |
| `Crashpad/` | 4, 308 | crash reporter state (`metadata`, `settings.dat`, `throttle_store.dat`, `watson_metadata`; empty `attachments/` and `reports/`) |
| `TrustTokenKeyCommitments/`, `OriginTrials/`, `AutoLaunchProtocolsComponent/` | 4, 7,093; 1, 43; 2, 3,807 | downloaded component data |
| `Default/Cache` (excluded) | 30, 7,061,265 | HTTP cache |
| `Default/Code Cache` (excluded) | 322, 92,526 | compiled JavaScript and WebAssembly |
| `Default/GPUCache` (excluded) | 5, 5,837,168 | GPU shader cache |
| `Default/DawnGraphiteCache`, `Default/DawnWebGPUCache` (excluded) | 5 and 557,424 each | WebGPU caches |
| `Default/blob_storage`, `Default/Shared Dictionary` (excluded) | not recorded | blob store and shared compression dictionaries |
| `GrShaderCache`, `ShaderCache`, `GPUPersistentCache` (excluded) | 5, 557,424; 5, 557,424; 3, 0 | shader caches |
| `component_crx_cache`, `extensions_crx_cache` (excluded) | 9, 20,720,619; 1, 13 | downloaded component and extension packages |
| `WidevineCdm` (excluded) | 6, 20,278,481 | the Widevine module (Google's digital-rights-management component for protected media) |
| `Subresource Filter` (excluded) | 15, 11,814,930 | the ad-filter list |
| `hyphen-data`, `PKIMetadata`, `CertificateRevocation` (excluded) | 54, 1,769,902; 4, 266,347; 2, 23,236 | hyphenation dictionaries, certificate metadata and revocation lists |
| `BrowserMetrics-spare.pma` (excluded) | 1,310,720 | metrics scratch file |

Top-level `Last Version`, `lockfile`, `Variations*` and the empty
`MEIPreload/` and `Trust Protection Lists/` are collected too.

### Deletion

Real install (Linux), the deletion round of
[section 1](#1-source-and-evidence); names, counts and key names
only. The app's delete removed each session's `session-state/<uuid>/`
directory entire (`events.jsonl`, `workspace.yaml`, `session.db`,
`checkpoints/`, `rewind-file-snapshots/`, `files/`, `research/`, the
`inuse.*` files), the general chat's directory under `chats/`, the project
session's worktree and its branch (app log: `deleted local branch ref on
hard delete workspace_id=<uuid> branch=<login>-improved-happiness
repo=<path>`, `permanently deleted workspace workspace_id=<uuid>`,
`archived workspace workspace_id=<uuid>`, `not parking worktree; removing
it instead project_id=<uuid> error=reusable worktree pool is full for
project <uuid>`), and in `data.db` the general chat's `sessions` row and
every `workspaces`, `worktrees`, `workspace_session_aliases` and
`workspace_checkout_bindings` row. These survived:

| Path | What survived |
| --- | --- |
| `session-store.db` (Copilot CLI's cross-session store, collected as `copilot-cli`) | the `sessions` rows of both sessions (`summary` the session name, `cwd` under `.copilot/`, `repository` and `branch` for the project session), 5 `turns` rows holding every prompt and final reply in full, 1 `session_files` row (the `create` of the file the agent wrote), 8 `assistant_usage_events` rows and 5 `search_index` rows ([section 5 of `analyzer/research/copilot-desktop.md`](../../analyzer/research/copilot-desktop.md#what-survives-a-delete)) |
| `data.db` | the project session's `sessions` row (`archived_at` null, `is_running` 0), the general chat's `activity_items` row (its `session_id` set although the session row is gone), all 4 `session_checkpoints` rows, 7 `session_context_usage` rows, the `projects` row and the `reusable_worktree_pool` row |
| `data.db-wal` | the deleted rows' pages: the two session ids occur 63 and 105 times in the WAL and never in `data.db`, whose main file had not changed since the app first started |
| `repos/<name>/.git/refs/copilot/checkpoints/<session id>/<seq>/<event id>` | four loose refs of the deleted project session, one per checkpoint (a loose ref is a ref stored as its own file under `.git/refs/`, holding a commit hash, rather than a line of `.git/packed-refs`); `<seq>` is a 20-digit zero-padded sequence number (1 to 4) and `<event id>` a 36-character UUID that is an event id of the session's deleted `events.jsonl`. Each names a commit with author and committer `Copilot`, subject `copilot checkpoint: <session id> @ <event id>`, an empty body and one parent, dated at the `session_checkpoints` times. Their trees were identical to `main`, because the session's only write went outside the worktree; in a session that edits files they would be per-turn snapshots of the worktree. The refs appear in no reflog (git's log, under `.git/logs/`, of each change to where a ref points): the reflog held only the clone, `remote set-head`, the pre-created worktree's checkout and reset entries |
| `repos/copilot-worktrees/<name>/copilot-prewarm-<adjective>-<noun>/` | the worktree the reusable-worktree pool pre-creates, on a detached HEAD (a checkout of a commit, here `main`'s, rather than of a branch); it replaced the deleted session's worktree |
| `logs/github-app.<pid>.log` | 160 KB after the round: the deletion lines above, `session not found in memory during delete (already evicted) session_id=<uuid>` twice and `terminated agent processes owned by ending sessions scope="session_end" ...`; 22 and 129 mentions of the two session ids |
| `logs/process-<epoch ms>-<pid>.log` (collected as `copilot-cli`) | untouched; the CLI server log says `Cleaning up session <uuid>: Session deleted via sessions.delete` once per deletion (three lines in all, one from an earlier delete) |
| `.session-operation-locks/<session id>.lock` (collected as `copilot-cli`) | one 0-byte file per deleted session |
| the file the agent created | still on the user's desktop, outside every catalog entry |
| `.local/share/com.github.githubapp/localstorage/tauri_localhost_0.localstorage` | the `side-chat-tabs` value still keys its `openSessionIdsByWorkspace` object by both deleted ids (empty lists) and the pending-session id; `home-composer-draft:main` is `{state: {promptText, selectedProjectId, projectExplicitlySelected}, version}`, empty here; neither session id occurs anywhere else in it, WAL included |

On Windows (real install, 1.1.30, the deletion and quit round of
[section 1](#1-source-and-evidence)) the app's delete of the general
chat removed its `session-state/<uuid>/` directory entire (`events.jsonl`,
`workspace.yaml`, `session.db`, `checkpoints/`, `files/`, `research/`,
`.workspace-fork.lock`, the `inuse.*` files) and `chats/2026-10-17/`
entire, with the project the agent had built there (`weather-mcp/`, its
`node_modules` included): files an agent writes in a chat's working
directory are deleted with the chat. In `data.db` the chat's `sessions`
row went. The project session's `inuse.<pid>.hold` and `.lock` went too,
its CLI process having ended at its 20:15Z shutdown. The chat had no
checkpoint, so no `.git` ref of it existed; the project session's ref
stayed. These survived, and differ from Linux as noted:

| Path | What survived |
| --- | --- |
| `data.db` | the chat's 3 `activity_items` rows (`agent_idle`, with reply previews); `session_deletion_intents` still empty; six `app_state` keys rewritten at deletion time (`sidebar-project-groups`, `right-panel`, `cleared-background-tasks`, `session-groups`, `main-content-tabs`, `inbox-sections`) |
| `data.db-wal`, then `data.db` | before the quit the WAL (1,907,592 bytes) held 220 occurrences of the chat's id and the main file none. Quitting the app checkpointed the WAL: `data.db-wal` went to 0 bytes, `data.db` grew from 1,347,584 to 1,433,600 bytes, and the id then occurred 23 times in the main file (the surviving `activity_items` rows and freed pages). So the Linux finding that a deleted session's pages stay in `data.db-wal` holds only until the app next quits cleanly; after that the main file keeps the activity rows and whatever freed pages a later write has not reused |
| `session-store.db` (`copilot-cli`) | the chat's `sessions` row, all 3 `turns` with prompt and reply, 3 `session_files` rows naming the files the agent created, 3 `search_index` rows and 8 `assistant_usage_events`; its `-wal` (704,552 bytes, 220 mentions of the id) was not checkpointed at the quit |
| `session-state/.session-operation-locks/<uuid>.lock` (`copilot-cli`) | 0 bytes, as on Linux |
| `logs/github-app.5688.log` | 41 lines naming the id, among them `github_app::session::manager::lifecycle: session not found in memory during delete (already evicted) session_id=<uuid>` and `github_app::session::manager::process_teardown: terminated agent processes owned by ending sessions scope="session_end" session_count=1 runtime_outcome="not_live" ...` under message kind `delete_session` |
| `logs/process-<epoch ms>-<pid>.log` (`copilot-cli`) | one `Cleaning up session <uuid>: Session deleted via sessions.delete` line |
| `run/ws.port`, `run/ws.token` | rewritten at 20:31:33Z; all six `run/` files stay on disk after the quit |
| `AppData/Local/com.github.githubapp/EBWebView/Default/Local Storage/leveldb/` | the tab-list keys rewritten, as the Linux `side-chat-tabs` was |

After the quit the seven pool session directories, the 18 operation
locks, the app log and `repo-metadata-cache.db-wal` (98,912 bytes) were
still on disk.

## 3. Credentials

- GitHub token: the OS keyring. The binary links `keyring_core` and
  `dbus_secret_service_keyring_store` (binary:
  `index.crates.io-1949cf8c6b5b557f/keyring-core-1.0.0`), the client for
  the Secret Service, the freedesktop.org interface over D-Bus (the Linux desktop's
  inter-process message bus) that the GNOME
  keyring (the GNOME desktop's password store) implements. On the Linux
  install `~/.local/share/keyrings/login.keyring` was modified at
  22:01:14Z, during the sign-in, and no token was found in any file the
  survey read. The keyring is outside the catalog, as it is for Copilot
  CLI. On Windows the token goes to Credential Manager (the per-user
  credential vault of Windows, whose entries are files under
  `AppData/Roaming/Microsoft/Credentials/` encrypted with DPAPI, the Data
  Protection API that ties a key to the user's logon): `github.exe` links
  the same crate with the Windows store (`github 1.1.30 windows-arm64
  github.exe`: `keyring-core-1.0.0`, `keyring-store-1.1.0`,
  `windows-native-keyring-store`, and the imports `CredWriteW`,
  `CredReadW`, `CredDeleteW`, `CredEnumerateW`), and the one credential
  file written that day, `AppData/Roaming/Microsoft/Credentials/<32 hex>`
  (666 bytes), has the sign-in minute, 19:54:27Z (`data.db`
  `accounts.created_at` 19:54:27.147Z, app log task
  `auth_device_code_flow`). The credential's target name is not
  determined: `CredEnumerateW` from the SSH session failed with error 1312
  (no logon session; a key-based SSH logon has no credential vault), and
  `cmdkey /list` printed nothing there. The Credentials directory is
  outside the catalog. The binary has no `storeTokenPlaintext` string. The
  store on macOS is not determined.
- `data.db` has two token columns, `accounts.access_token` and
  `settings.github_access_token` (with `github_token_type`, `github_scope`
  and `github_token_updated_at`); both were NULL on the Linux and Windows installs, the token
  being in the keyring. The binary also carries an older table's
  migration, `ALTER TABLE github_accounts ADD COLUMN access_token TEXT;`,
  and queries on `github_access_token IS NOT NULL`, so a file fallback
  exists; when it is used is not determined. `data.db` stays collected and
  unflagged, as Cursor's `state.vscdb` is, and those two columns are the
  ones to redact. `repo-metadata-cache.db` `github_metadata_account_lifecycle`
  holds a credential identity hash, which the schema comment says is
  "Hex SHA-256 of the credential identity in use. Comparison material
  only; ... never a token, and never enough to reconstruct one" (binary).
- `run/ws.token` and `run/ws.release.token` (49 bytes each on Linux, 48
  on Windows, characters of the URL-safe base64 alphabet): the token the app's web view presents to
  the local WebSocket server (binary and app log: "wrote WebSocket auth
  token"). It is a live local credential while the app runs, so
  `.copilot/run/*.token` is a secret glob. `run/ws.port` is not a secret.
  On Windows both were rewritten while the app ran and stayed on disk
  after it quit.
- The storage crate sets mode 0600 on a token file (binary:
  `crates/storage/src/permissions.rs` "Failed to set 0600 on token file");
  the two run tokens were mode 0600 on the install (`-rw-------`), the
  port files too; which other files it covers is not determined.
- `/usr/bin/git-credential-copilot` is a git credential helper (binary
  manifest: `"binaries/git-credential-copilot"`; build note: "`cargo build
  -p git-credential-copilot`) and set $COPILOT_TRAMPOLINE_BIN_DIR"). Its
  strings show a Unix-domain socket client (`std::os::unix::net::UnixStream`),
  which suggests it asks the running app for the credential rather than
  reading a file; not confirmed. The clone's `.git/config` named no
  helper on the install, so how git is pointed at it is not determined.
- The WebKit salts (`CacheStorage/salt`, `storage/salt`,
  `mediakeys/v1/salt`, `WebKitCache/Version 17/salt`) key WebKit's
  per-origin storage names; they are not credentials and stay unflagged.
- `~/.copilot/config.json` stays the Copilot CLI secret glob; the app did
  not change its role.
- `~/.copilot/mcp-config.json`, written by the bundled CLI when MCP
  servers are added from the app, held a GitHub personal access token in
  plain text on Windows (the `github` server's `env`
  `GITHUB_PERSONAL_ACCESS_TOKEN`, 33 characters); it is the Copilot CLI
  secret glob `.copilot/mcp-config.json`, and the Windows run flagged it.
- The WebView2 `Local State` `os_crypt.encrypted_key` (396 characters) is
  the key Chromium encrypts cookie values and saved passwords with,
  wrapped with DPAPI so only the user's logon can unwrap it. It is not a
  credential by itself, and the stores it protects were empty on the
  install (`Network/Cookies` 0 rows after the quit, since the device-code
  sign-in runs in the system browser and leaves no github.com cookie in
  the app's web view; `Login Data` 0 `logins` rows; `Web Data`
  `token_service` 0 rows; `Vpn Tokens` 0 rows). They are flagged
  `secret: true` all the same, by the globs
  `AppData/Local/com.github.githubapp/EBWebView/Local State`,
  `.../Default/Network/Cookies*` and `.../Default/Login Data*`, as the
  same Chromium stores of ChatGPT Desktop are, because a cookie store, a
  saved-password store and the key that encrypts them hold credentials
  whenever the web view signs in. `user_experience_metrics.client_id2` in `Local State` and
  `profile.edge_profile_id` in `Preferences` are identifiers, not
  credentials. The run's check of unflagged file names that look like
  credentials found only the WebView2 files `Vpn Tokens`, `Trust Tokens`,
  `Cookies` (now flagged) and `TrustTokenKeyCommitments/keys.json` (the last holds the
  public key commitments of Chromium's Trust Tokens component), none a
  credential.
- `git-credential-copilot.exe` on Windows carries none of the keyring
  strings; `github.exe` has the named pipe prefix `\\.\pipe\copilot-ssh-`
  (a Windows named pipe, a local inter-process channel); what uses it,
  and how the helper reaches the app on Windows, are not determined.

## 4. Exclusions

- `.copilot/repos`, with each clone's `.git` carved out by a nested
  catalog entry: `.copilot/repos` is excluded whole (the clones' working
  trees and the worktrees under `copilot-worktrees`; the 262 files of the
  770 on the install were the clone and the worktree), and the catalog
  line `copilot-desktop|.copilot/repos/*/.git` claims each clone's
  top-level `.git` as its own walk, less the exclusions
  `.copilot/repos/*/.git/objects` (the object store) and
  `.copilot/repos/*/.git/index`. Exclusions can only remove, and their
  globs cross `/`, so no exclusion set could keep a working tree out and
  its `.git` in; the nested entry does it with data alone. Collected as
  `copilot-desktop`: `.git/refs` (the checkpoint refs), `.git/packed-refs`,
  `.git/logs` (the reflog), `.git/HEAD`, `.git/config` and
  `.git/worktrees`; the working tree, dot entries included, gets no row of
  its own beyond the `skipped_excluded` row of `repos`, and `--full`
  collects it. Which repositories were added, where, and on which branch
  is in `data.db` `projects`, `worktrees` and
  `workspace_checkout_bindings`, which are collected. Collector 1.13.0 as
  first written excluded `.copilot/repos` whole, `.git` included; the
  deletion round ([section 2](#deletion)) found the
  checkpoint refs of a deleted session there, outliving the session, so
  the `.git` entry was added.
- `.local/share/com.github.githubapp/app-skills`,
  `Library/Application Support/com.github.githubapp/app-skills` and
  `AppData/Roaming/com.github.githubapp/app-skills`: the skills shipped in
  the app, copied at first start; a skill the user added beside them is
  moved aside on a collision (binary: "a user-added app skill collides
  with a newly bundled one and was moved aside"), so the exclusion also
  prunes user-added skills there.
- `.local/share/com.github.githubapp/WebKitCache` and
  `.local/share/com.github.githubapp/CacheStorage`: WebKit's caches.
- The WebView2 user data folder `AppData/Local/com.github.githubapp`
  (Windows), a catalog entry from collector 1.13.0 because it holds the
  web view's Local Storage (the composer draft and tab lists that Linux
  keeps in the WebKit `localstorage` table), less its Chromium caches and
  downloaded components, each with one `skipped_excluded` row:
  `EBWebView/Default/Cache` (7.1 MB on the install), `Default/Code Cache`
  (93 KB), `Default/GPUCache` (5.8 MB), `Default/DawnGraphiteCache` and
  `Default/DawnWebGPUCache` (557 KB each), `Default/blob_storage` and
  `Default/Shared Dictionary` (sizes not recorded), `GrShaderCache` and
  `ShaderCache` (557 KB each), `GPUPersistentCache` (empty),
  `component_crx_cache` (20.7 MB), `extensions_crx_cache` (13 bytes),
  `WidevineCdm` (20.3 MB), `Subresource Filter` (11.8 MB), `hyphen-data`
  (1.8 MB), `PKIMetadata` (266 KB), `CertificateRevocation` (23 KB) and
  `BrowserMetrics-spare.pma` (1.3 MB), all under
  `AppData/Local/com.github.githubapp/EBWebView/`. Of the folder's 611
  files and 72.6 MB, that leaves about 140 files and at most 1.2 MB
  collected, by the survey's per-directory sizes: `Local State`,
  `Preferences`, `Secure Preferences`, Local and Session Storage, the
  `Network/` stores, `History`, `Favicons`, `Top Sites`, `Login Data`,
  `Web Data`, the diagnostic logs, `Crashpad` and the leveldb bookkeeping
  files. None of the globs differs from another only by case, which the
  PowerShell collector's case-insensitive match would merge.
- `.copilot/chats/*/node_modules`: the dependency tree of a project the
  agent builds in a chat's working directory (exclusion globs cross `/`,
  so it reaches `chats/<date>/<slug>/<project>/node_modules`). On the
  Windows install it was 3,411 of the chat directory's 3,415 files and
  14.7 of its 14.8 MB; the four files the agent wrote stay collected.
- The Copilot CLI's marketplace clone under its cache directory,
  `AppData/Local/copilot/marketplaces` (4,560 files, 263,616,505 bytes on
  the Windows install, a shallow git clone of the awesome-copilot
  marketplace, cloned 19:55:19Z to 19:55:34Z, two minutes after the app's
  first start), with `.cache/copilot/marketplaces` and
  `Library/Caches/copilot/marketplaces` beside it; see
  [section 4 of `copilot-cli.md`](copilot-cli.md#4-exclusions) and
  [issue 131](https://github.com/seanthegeek/doubleagent/issues/131).
- Not collected, outside every entry: `~/.cache/github-copilot-sdk`
  (the 180 MB CLI binary), `~/.cache/github-copilot-git-<version>` (53 MB
  of git binaries) and `~/.cache/copilot-desktop-gh-<version>` (38 MB, the
  `gh` binary). Their version suffixes record which tool versions the app
  used, and a listing of `~/.cache` shows them without collecting them.
  On Windows the same three are `AppData/Local/github-copilot-sdk`
  (158.6 MB), `AppData/Local/github-copilot-git-<version>` (114 MB) and
  `AppData/Local/copilot-desktop-gh-<version>` (39.4 MB), also outside
  every entry, as is the install directory
  `AppData/Local/Programs/GitHub Copilot` (520 MB).
- Foundry Local model weights would land under
  `.github-copilot-cli/cache/models/`; none were downloaded on the
  install, so no exclusion was added. A host where a local model was
  downloaded would need one.

## 5. Project-local files

None observed. The app writes inside the clone and worktree it manages
under `~/.copilot/repos/`, not inside the user's own repositories. The
SDK guide names `.github/extensions/` as the project extensions
directory (shipped binary, `copilot-sdk/docs/extensions.md`: "The CLI
scans `.github/extensions/` (project)"), a Copilot CLI convention, not
an app file.

## 6. Where the project path is recorded

- `data.db` `projects.main_repo_path` (the clone under
  `~/.copilot/repos/`), with `github_owner` and `github_repo`;
  `worktrees.path` and `branch`; `workspace_checkout_bindings.repo_path`,
  `checkout_path` and `repo_full_name`; `settings.storage_location`
  (`/home/sean/.copilot/repos` on the install, the root under which the app
  clones). SQLite only, so discovery does not read them; the analyzer
  does.
- `session-state/<uuid>/workspace.yaml` `cwd`, as for Copilot CLI: a
  general chat's `cwd` is its empty `~/.copilot/chats/<date>/<slug>-<id8>`
  directory, and a project session's is its worktree under
  `~/.copilot/repos/copilot-worktrees/`. Neither is a project the user
  works in, and collector 1.13.0 reported both as projects and collected
  the worktree's `AGENTS.md` and `CLAUDE.md` as project files. Project
  discovery now skips a `workspace.yaml` `cwd` that lies under the same
  home's `.copilot/` directory, in both collectors; the repository the
  user added is identified by `data.db` `projects` and by the project
  session's `workspace.yaml` `repository` key instead.
- On Windows the app pre-created seven pool and probe sessions that were
  never prompted ([section 2](#inside-copilot)); four had the app's install
  directory `C:\Users\sean\AppData\Local\Programs\GitHub Copilot` as
  their `cwd`, and collector 1.13.0 as first written reported that
  directory as a project (no project file was collected there; the other
  three `cwd`s were under `.copilot/` and already skipped). Project
  discovery now also skips the `cwd` of a session directory that has no
  `events.jsonl`, in both collectors: every prompted session on the Linux
  and Windows installs had one, and none of the pool or probe sessions
  did. Whether a standalone Copilot CLI session that exits before its
  first prompt writes `events.jsonl` is not determined; if it does not,
  its `cwd` is no longer discovered either.
- `events.jsonl` `session.start` `data.context` carries `cwd`, and for a
  project session `branch`, `gitRoot`, `headCommit`, `hostType`
  (`github`), `repository` and `repositoryHost` (`github.com`).
- After a session is deleted ([section 2](#deletion)),
  `session-state/<uuid>/` and the `data.db` `worktrees`, `workspaces` and
  `workspace_checkout_bindings` rows are gone; the `data.db` `projects`
  row and `session-store.db` `sessions` (`cwd`, `repository`, `branch`)
  still name the repository, and the checkpoint refs under the clone's
  `.git/refs/copilot/checkpoints/` still name the session id. The
  analyzer's inventory lists the app's own directories (the chat
  directories, `canvas-catalog-probe`, the clone and the worktree) as
  projects, [issue 149](https://github.com/seanthegeek/doubleagent/issues/149).

## 7. Confidence

High: the app-only file set inside `~/.copilot`, its sizes and creation
times, the Tauri data directory on Linux and Windows, `~/.github-copilot-cli`, the
three tool download directories (`~/.cache` on Linux, `AppData/Local` on
Windows), the shared `session-state` format and
the `client_name` value (real installs (Linux, Windows), with the path names
confirmed in the binary); the WebView2 user data folder and its contents
(real install (Windows) and binary); the pool and probe sessions without
`events.jsonl` (real installs (Linux, Windows) and app log); the token in
the keyring with NULL token columns in `data.db` (real install (Linux) and
binary); the run tokens as live local credentials (binary and app log);
what a session deleted from the app removes and leaves, the checkpoint
refs' layout and the WAL checkpoint at quit (real installs (Linux,
Windows)).

Medium: the token in Windows Credential Manager (binary
imports and the credential file's modification time, target name not
read); the macOS data directory (dirs crate, not observed); the macOS
token store.

Not determined: when `data.db`'s token columns are
filled; how git reaches `git-credential-copilot`; what `ep/` holds; where
`attachments`, `workspaces/*/attachments` and `crash-reports` appear and
what they hold; whether Foundry Local model weights are downloaded
without the user asking; whether a CLI session that is never prompted
writes `events.jsonl`; the sizes of the WebView2 `blob_storage` and
`Shared Dictionary` directories.
