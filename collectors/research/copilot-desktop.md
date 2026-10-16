# copilot-desktop

Catalog agent: `copilot-desktop` (GitHub Copilot Desktop, the desktop app
GitHub ships as the dpkg package `github`). How its store is encoded and
how a parser reads it is in
[`analyzer/research/copilot-desktop.md`](../../analyzer/research/copilot-desktop.md).

The app runs its sessions through a bundled copy of Copilot CLI and
shares `~/.copilot` with it: the session logs under
`~/.copilot/session-state/` are Copilot CLI's format and stay with the
`copilot-cli` agent
([`copilot-cli.md`](copilot-cli.md)); nested catalog entries claim the
app's own files inside that directory. [Issue
147](https://github.com/seanthegeek/doubleagent/issues/147) tracks the app.

## 1. Source and evidence level

Closed source. GitHub Copilot Desktop is a Tauri app: Tauri is a desktop
framework that draws the user interface in the operating system's web
engine (on Linux WebKitGTK, the GTK port of the WebKit browser engine;
the package depends on `libwebkit2gtk-4.1-0`) and runs the backend as a
native Rust program. The app identifier is `com.github.githubapp`. Each
claim names its evidence level:

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
  `5e89734fe81b21dfa32c8b4473e7d055b38586804e23ed03a79353dc35ce32f1`. It was read with `strings` and `grep` only, never run by the
  research. Citations are written `github 1.1.29 linux-arm64
  /usr/bin/github` with the literal snippet, shortened after this
  paragraph to "binary" and the snippet; no byte offsets were recorded,
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
  `%APPDATA%` (`AppData/Roaming`) on Windows. The macOS and Windows paths
  in this document are derived from that behaviour and the app
  identifier, not observed.
- **Docs**: none fetched.
- **Observed (Linux)**: GitHub Copilot Desktop 1.1.29, the arm64 `.deb`
  installed at 21:59Z on 2026-10-16 on an Ubuntu 26.04.1 arm64 Parallels
  VM (home `/home/sean`, `/bin/sh` dash) that already held the Copilot CLI
  1.0.98 round's `~/.copilot`
  ([section 1 of `copilot-cli.md`](copilot-cli.md#1-source-and-evidence-level)),
  surveyed for names, sizes, modification times, key names and types only.
  Exercised: app start at 22:00:30Z; sign-in by device-code flow (a sign-in under OAuth, the open standard for delegated
  authorisation, in which the app shows a short code that the user enters on
  github.com in a browser; app log task `auth_device_code_flow`), after
  which `~/.local/share/keyrings/login.keyring` was modified at 22:01:14Z;
  one general chat (created 22:01:27Z, one prompt, no tool call, titled by
  the user); then the user added the GitHub repository
  `seanthegeek/doubleagent`, which the app cloned and checked out into a
  git worktree (a second working directory of the same repository on its
  own branch) at 22:03Z, and asked one question in a project session
  (created 22:03:11Z, four prompts, `bash` called twice and `create` once;
  the `create` call wrote a file on the user's desktop, outside the
  worktree). Every action ran before the first listing, so no per-action
  listing diff exists; the times above and the files' modification times
  are the only mapping from action to file. Not exercised: a scheduled
  task, a session automation, a session deleted from the app, a removed
  project, a denied tool call, a model switch, a remote session. Collector
  1.13.0, run as the user before the catalog had this agent: 770 files,
  24.7 MB, every one attributed to `copilot-cli` (262 of them the clone
  and the worktree), 2 `skipped_excluded`, 1 `secret: true`
  (`.copilot/config.json`), 5 `error_read` rows on system accounts;
  project discovery reported the chat directory and the worktree as
  projects ([section 6](#6-where-the-project-path-is-recorded)). macOS and
  Windows were not observed.

## 2. Per-user storage

Package files (shipped binary, real install (Linux)):
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

### Inside `~/.copilot`

The app resolves `~/.copilot` as Copilot CLI does, through `COPILOT_HOME`,
and an app-only override `COPILOT_HOME_OVERRIDE` (binary:
`github_app_desktop_services::platform::paths::COPILOT_HOME_OVERRIDE`; the
neighbouring string run lists the names it builds under it:
`copilot-worktreesdata.dbattachmentsmedia-cachesession.dbCOPILOT_HOMEchatscrash-reportsfilesplan.mdsession-state`).

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
[section 5 of `analyzer/research/copilot-desktop.md`](../../analyzer/research/copilot-desktop.md#5-sqlite-and-other-stores)),
`inuse.<pid>.hold` (0 bytes) and `inuse.<pid>.lock` (6 bytes). Two more
directories, `session-state/pending-session:<uuid>/files/` and
`session-state/pending-session:draft:<uuid>/files/`, were created empty
at 22:03Z. `extensions/` (empty) is also a CLI directory: the SDK guide
names "the user's copilot config extensions directory" (shipped binary,
`copilot-sdk/docs/extensions.md`), so it stays with `copilot-cli`.
`logs/process-<epoch ms>-<pid>.log` (six files) are the bundled CLI's
process logs and stay with `copilot-cli` too (lines such as "Starting CLI
in server mode (stdio)", `Created session: <uuid>`, "Installed N native
extension(s) for session", `Cleaning up session <uuid>: Session deleted via sessions.delete`). `~/.cache/copilot/` gained `tgrep-serve.lock`, and
`copilot-user-cache.json` grew to 6.5 KB.

App-only, all created at 22:00:30Z unless said (real install (Linux)):

| Path | Size | What it holds |
| --- | --- | --- |
| `data.db` | 1.3 MB | the app's own SQLite store (WAL mode, write-ahead log: new pages go to the `-wal` file until a checkpoint copies them into the main file; binary: `PRAGMA journal_mode=WAL;PRAGMA foreign_keys=ON;`): accounts, projects, worktrees, workspaces, sessions, activity, schedules; 110 tables |
| `data.db-wal`, `data.db-shm` | 1.67 MB, small | its WAL and shared-memory index; the WAL is larger than the main file, so both must be collected with it |
| `data.db.open-lock`, `data.db.startup-lock` | 0 bytes | lock files (binary: `db.open-lockdb.startup-lock`) |
| `repo-metadata-cache.db` (+`-wal`, `-shm`) | 4,096 (`-wal` 98,912) | GitHub metadata cache (binary: `repo-metadata-cache.db`); tables in [section 5 of the analyzer document](../../analyzer/research/copilot-desktop.md#5-sqlite-and-other-stores), all empty but one lifecycle row |
| `chats/<date>/<slug>-<first 8 of the session id>/` | empty | one working directory per general chat, the chat session's `cwd` (`chats/2026-10-16/automatic-barnacle-5d404e14`) |
| `repos/<name>/` | 20 MB | the clone of each added repository (remote `https://github.com/<login>/<name>.git`; its `.git/config` held no credential helper, and there was no `~/.gitconfig`) |
| `repos/copilot-worktrees/<name>/<branch>/` | in the 262 files above | the git worktree a project session runs in, on a new branch named `<login>-<adjective>-<noun>` |
| `run/single-instance.lock`, `run/single-instance.owner` | 0 and 5 bytes | the single-instance lock and the owning pid (binary: `single-instance.locksingle-instance.ownersingle-instance-pr.locksingle-instance-pr.owner`) |
| `run/ws.port`, `run/ws.release.port` | 11 bytes each | the port of the app's local WebSocket server |
| `run/ws.token`, `run/ws.release.token` | 49 bytes each | the WebSocket auth token ([section 3](#3-credentials)) |
| `media-cache/` | empty | media cache (binary: `"$HOME/.copilot/media-cache/**",`) |
| `canvas-catalog-probe/` | empty | canvas catalog probe (binary: `canvas-catalog-probe`) |
| `logs/github-app.<pid>.log` | 109 KB | the Tauri backend's tracing log: WebSocket server, session warm-up, the device-code sign-in, "wrote run file", "wrote WebSocket auth token", "Scheduler starting for workflows, session automations, and Scheduled tasks", git version detection, canvas catalog warm-up (each a literal in the binary) |

Named in the binary, not observed: `$HOME/.copilot/attachments/**` and
`$HOME/.copilot/workspaces/*/attachments/**` (binary: `"$HOME/.copilot/attachments/**",`,
`"$HOME/.copilot/workspaces/*/attachments/**",`), and `crash-reports`
(binary, in the string run above). They get no catalog line until an
install shows them: `attachments` under `~/.copilot` is collected with
`copilot-cli` meanwhile.

### Outside `~/.copilot`

| Path | Size | What it holds |
| --- | --- | --- |
| `~/.local/share/com.github.githubapp/` (Linux, observed); `~/Library/Application Support/com.github.githubapp` (macOS) and `AppData/Roaming/com.github.githubapp` (Windows), dirs crate | 4.6 MB | the Tauri data directory |
| `.../app-skills/` | 3.3 MB | skills bundled with the app, copied at first start (`af`, `agent-merge`, `agentfinder`, `connector-finder`, `create-canvas`, `factory-creator`, `impeccable` with hundreds of `.mjs` scripts, `latex`, `orchestrate`, `pr-stack`, each with `SKILL.md`), markers `.app-skills-bundled` and `.app-skills-version` (binary: `app-skillsapp-skills.new.app-skills-version`) |
| `.../localstorage/tauri_localhost_0.localstorage` (+`-wal`, `-shm`) | 4,096 (`-wal` 939,392) | the web view's local storage, SQLite `ItemTable(key, value BLOB)`; keys include `home-composer-draft:main` (192 bytes, the unsent composer draft), `inbox-cache` (2.5 KB) and tab lists ([section 2 of the analyzer document](../../analyzer/research/copilot-desktop.md#2-transcript-files)) |
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
  CLI. The store on macOS and Windows is not determined.
- `data.db` has two token columns, `accounts.access_token` and
  `settings.github_access_token` (with `github_token_type`, `github_scope`
  and `github_token_updated_at`); both were NULL on the install, the token
  being in the keyring. The binary also carries an older table's
  migration, `ALTER TABLE github_accounts ADD COLUMN access_token TEXT;`,
  and queries on `github_access_token IS NOT NULL`, so a file fallback
  exists; when it is used is not determined. `data.db` stays collected and
  unflagged, as Cursor's `state.vscdb` is, and those two columns are the
  ones to redact. `repo-metadata-cache.db` `github_metadata_account_lifecycle`
  holds a credential identity hash, which the schema comment says is
  "Hex SHA-256 of the credential identity in use. Comparison material
  only; ... never a token, and never enough to reconstruct one" (binary).
- `run/ws.token` and `run/ws.release.token` (49 bytes each, characters of
  the URL-safe base64 alphabet): the token the app's web view presents to
  the local WebSocket server (binary and app log: "wrote WebSocket auth
  token"). It is a live local credential while the app runs, so
  `.copilot/run/*.token` is a secret glob. `run/ws.port` is not a secret.
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

## 4. Exclusions

- `.copilot/repos`: the clones and worktrees of every added repository
  (262 files of the 770 on the install). Which repositories were added,
  where, and on which branch is in `data.db` `projects`, `worktrees` and
  `workspace_checkout_bindings`, which are collected.
- `.local/share/com.github.githubapp/app-skills`,
  `Library/Application Support/com.github.githubapp/app-skills` and
  `AppData/Roaming/com.github.githubapp/app-skills`: the skills shipped in
  the app, copied at first start; a skill the user added beside them is
  moved aside on a collision (binary: "a user-added app skill collides
  with a newly bundled one and was moved aside"), so the exclusion also
  prunes user-added skills there.
- `.local/share/com.github.githubapp/WebKitCache` and
  `.local/share/com.github.githubapp/CacheStorage`: WebKit's caches.
- Not collected, outside every entry: `~/.cache/github-copilot-sdk`
  (the 180 MB CLI binary), `~/.cache/github-copilot-git-<version>` (53 MB
  of git binaries) and `~/.cache/copilot-desktop-gh-<version>` (38 MB, the
  `gh` binary). Their version suffixes record which tool versions the app
  used, and a listing of `~/.cache` shows them without collecting them.
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
- `events.jsonl` `session.start` `data.context` carries `cwd`, and for a
  project session `branch`, `gitRoot`, `headCommit`, `hostType`
  (`github`), `repository` and `repositoryHost` (`github.com`).

## 7. Confidence

High: the app-only file set inside `~/.copilot`, its sizes and creation
times, the Tauri data directory on Linux, `~/.github-copilot-cli`, the
three `~/.cache` tool directories, the shared `session-state` format and
the `client_name` value (real install (Linux), with the path names
confirmed in the binary); the token in the keyring with NULL token
columns in `data.db` (real install (Linux) and binary); the run tokens
as live local credentials (binary and app log). Medium: the macOS and
Windows data directories (dirs crate, not observed); the macOS and
Windows token store. Not determined: when `data.db`'s token columns are
filled; how git reaches `git-credential-copilot`; what `ep/` holds; where
`attachments`, `workspaces/*/attachments` and `crash-reports` appear and
what they hold; whether Foundry Local model weights are downloaded
without the user asking.
