# antigravity: on-disk paths (CLI `agy`, the desktop app and the IDE)

How the transcripts are encoded and how the parser reads them is in
[`analyzer/research/antigravity.md`](../../analyzer/research/antigravity.md).

Antigravity is three products under one catalog agent. The **CLI**, `agy`,
is a single Go binary. The **desktop app** (version 2.x) is an Electron
app, a desktop program built on Chromium and Node.js, whose bundle calls
the product "AGY Hub" (the `--subclient_type hub` argument it passes to its
backend, below); it describes itself to the user as "redesigned to put
agents first". The **IDE**, the VS Code fork that carried the Antigravity
name before 2.0, is now a separate download named "Antigravity IDE". The
CLI and the desktop app run the same Go backend: the app ships it as
`language_server`, the name it gives the process that serves its agent
conversations, and starts it in standalone mode. Both keep their state
under `~/.gemini/`, in different subdirectories.

## 1. Source and evidence level

Closed source. Evidence levels, tagged per claim:

- **binary**: `~/.local/bin/agy`, ELF x86-64 (the Linux executable
  format), 209,625,296 bytes, sha256 `a759ce7c7a235d9b...`, `strings -n 8`
  saved to `scratchpad/agy_strings.txt` (552,251 lines). The embedded
  changelog's newest heading is `## 1.2.15` (`agy_strings.txt:310457`;
  oldest `## 1.0.0` at 311213). Cited as `str:<line>` or by quoted literal.
- **descriptors**: the protobuf descriptors embedded in `agy` 1.2.16
  macOS arm64 (271 descriptor files) and in the desktop app's
  `language_server` 2.23.0 (484), extracted with
  `analyzer/tools/proto_descriptors.py extract` and cited by message or
  enum name.
- **bundle**: the desktop app's `Contents/Resources/app.asar` (asar is
  Electron's archive format for an app's code), version 2.23.0, 4,486,221
  bytes, sha256
  `4e99093662d797ecba823e92823d352413e3bf2ca721257df4a255c045df1598`, 738
  packed files with the main-process code under `dist/`. Cited as
  `app.asar:<path>@<byte offset into the asar file>` followed by a literal
  snippet; a reader of another version should grep for the snippet. Nothing
  from the bundle was executed.
- **live**: names and sizes only under `~/.gemini/antigravity-cli`,
  `~/.gemini/config` and `~/.cache/antigravity` on the Linux workstation
  where the ELF binary above was read.
- **observed**: the macOS real install below, read for file names, sizes,
  key names, value types and counts only.
- **docs**: [Antigravity CLI install](https://antigravity.google/docs/cli/install/),
  [Antigravity settings](https://antigravity.google/docs/settings/),
  [Antigravity CLI hands-on codelab](https://codelabs.developers.google.com/antigravity-cli-hands-on); **community**:
  jazzyalex.github.io agent-sessions guide, dev.to ndondadaniel2020 restore
  write-up, [Devilaiger/antigravity-chat-history-fix](https://github.com/Devilaiger/antigravity-chat-history-fix),
  [marioalbu08/antigravity-sync](https://github.com/marioalbu08/antigravity-sync), [SavFil/antigravity-convo-manager](https://github.com/SavFil/antigravity-convo-manager),
  [damadorPL/agent-memories](https://github.com/damadorPL/agent-memories) (google/antigravity.md),
  discuss.ai.google.dev thread 167445.

**Observed (macOS, CLI)** (issue 83): `agy` at `~/.local/bin/agy`, Mach-O
64-bit arm64 (the macOS executable format), 175,966,448 bytes, sha256
`7dca095cfc1df2c057a385ed88a76c7ba98dc103258a80be87a8f42e484cb3aa`,
installed 2026-10-04 on the author's Mac (macOS 26.4, Darwin 25.4.0,
Apple silicon), observed 2026-10-13. `agy --version` prints `1.2.16`; the
embedded changelog's newest heading is still `## 1.2.15`. Two
conversations were on disk, each a `conversations/<uuid>.db` with
`trajectory_meta.source` 17 (`CORTEX_TRAJECTORY_SOURCE_CLI` in the
descriptor `exa.cortex_pb.CortexTrajectorySource`) and 12 and 8 steps,
with the `brain/<uuid>/` logs described in
[section 2](#2-per-user-storage). The CLI left `~/.cache/antigravity/staging/`
empty.

**Observed (macOS, desktop app)** (issue 83): `/Applications/Antigravity.app`,
`CFBundleShortVersionString` and `CFBundleVersion` both `2.23.0`, Electron
(`Contents/Frameworks/Electron`, 200,443,040 bytes), on the same Mac,
first launched 2026-10-13 18:28 local time and observed the same day. Its
backend is `Contents/Resources/bin/language_server` (Mach-O arm64,
155,290,912 bytes, sha256
`c1dd0c9940f712adf2185e756470752d5f5afee15441e32879e4a0f127e18273`),
beside `Contents/Resources/bin/webm_encoder`. The user ran, in this order,
a question with no tool use, a coding task, an automation (a scheduled
task; the app calls it a sidecar, [section 2](#2-per-user-storage)) and the Google Docs
plugin ("gdocs", installed from the official plugin marketplace). The
directory listings were taken after all four, so which conversation
belongs to which task is not known: the four conversation databases under
`~/.gemini/antigravity/conversations/` have modification times 18:37,
18:43, 18:50 and 19:14, the automation's `sidecar.json` 18:41 to 18:42,
the plugin's `token.json` 18:46 and the agent's scratch document 18:47;
any mapping beyond those times waits for a round that lists after each
task. All four conversations have `trajectory_meta.source` 1
(`CORTEX_TRAJECTORY_SOURCE_CASCADE_CLIENT`). The app wrote
`~/.gemini/antigravity/` (49 MB), files in the shared `~/.gemini/config/`,
the Electron user-data directory `~/Library/Application Support/Antigravity/`
(5.3 MB) and `~/Library/Logs/Antigravity/`; it created no
`~/.gemini/antigravity-ide`, `~/.gemini/antigravity-backup` or
`~/.antigravity`, nothing under `~/Library/Caches`, and no LaunchAgent,
launchd job or cron entry (`~/Library/LaunchAgents` has none). Collector
1.11.0 collected the `.gemini` directories but none of the Electron
directories, since the catalog then named only the pre-2.0 `User` and
`logs` subdirectories, which this build does not create.

## 2. Per-user storage

Everything the CLI and the app keep per user sits under `~/.gemini/`; the
Go binary resolves it via `os.UserHomeDir` (binary) so Windows is
`%USERPROFILE%\.gemini` (community: Devilaiger, discuss 167445 quote
`%USERPROFILE%\.gemini\antigravity-cli\brain`). The app's main process
builds the same path from Node's `os.homedir()` (bundle, below).
`os.UserConfigDir`/`os.UserCacheDir`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`,
`APPDATA`, `LOCALAPPDATA` also appear (binary), consistent with the
`~/.cache/antigravity/staging` dir (live, observed; empty) used as the
plugin "marketplace cache ... staging directories" (str changelog).
Windows CLI install dir is `%LOCALAPPDATA%\agy\bin` (docs/cli/install).

**The four data directories under `~/.gemini`.**

- `~/.gemini/antigravity/` is the desktop app's data directory on every
  OS. The name is the app name lower-cased without spaces
  (`app.asar:dist/paths.js@4312548`
  `return electron_1.app.getName().toLowerCase().replace(/\s+/g, '');`,
  inside `function getAppDataDirName() {` at @4312439; `antigravity-dev`
  when the app runs unpackaged), joined to the home
  (`app.asar:dist/paths.js@4312621` `function getAppDataDir() {` ...
  `path_1.default.join(os_1.default.homedir(), '.gemini', getAppDataDirName())`).
  The app passes the name to its backend
  (`app.asar:dist/languageServer.js@4242293` `'--app_data_dir',`
  `(0, paths_1.getAppDataDirName)(),`), which owns the directory, and
  starts the backend as subclient "hub"
  (`app.asar:dist/languageServer.js@4241987` `'--subclient_type',` `'hub',`,
  beside `'--override_ide_name', 'antigravity'` and `'--standalone'`).
  Before 2.0 the IDE used the same directory:
  `app.asar:dist/paths.js@4313608`
  `exports.IDE_OLD_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity');`,
  commented "User data dir for the old IDE (source for copy)".
- `~/.gemini/antigravity-cli/` is the CLI's (binary, live, observed).
- `~/.gemini/antigravity-ide/` is the separately installed IDE's:
  `app.asar:dist/paths.js@4313784`
  `exports.IDE_NEW_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity-ide');`
  ("User data dir for the separately installed IDE (destination for
  copy)"). The app's IDE install wizard copies pre-2.0 IDE data there when
  `antigravity-ide` does not exist and `antigravity` does
  (`app.asar:dist/ideInstall/constants.js@4160197`, `exports.WIZARD_SHOWN_KEY`
  and the comment "2. `~/.gemini/antigravity-ide` does NOT exist 3.
  `~/.gemini/antigravity` DOES exist"); on the observed install `main.log`
  records `[IDE Wizard] <path> not found — user was not migrated, skipping.`
- `~/.gemini/antigravity-backup/` is the backup taken during that copy:
  `app.asar:dist/paths.js@4313949`
  `exports.IDE_BACKUP_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity-backup');`.

**`~/.gemini/antigravity/`** (observed, macOS, app 2.23.0, 49 MB):

| Path | Observed |
| --- | --- |
| `conversations/<uuid>.db` x4 (688,128 to 1,409,024 B, no sidecar files) | one SQLite database per conversation, the same schema as the CLI's ([section 3 of `analyzer/research/antigravity.md`](../../analyzer/research/antigravity.md#3-conversation-database)) |
| `conversation_summaries.db` (131,072 B; `-shm` 32,768 B, `-wal` 0 B) | the conversation index: the CLI's `conversation_summaries` table plus `search_schema_version` and `conversations_fts`, an FTS5 table (SQLite's full-text search module) over titles, workspaces and message bodies |
| `brain/<uuid>/` x4 | per-conversation logs and tool output, below |
| `annotations/<uuid>.pbtxt` x4 (94 to 99 B) | pbtxt is the protobuf text format, a human-readable serialisation of a protobuf message; each holds one `title:` field, the conversation title |
| `scratch/<name>.md` (24,280 B) | a Markdown document the agent wrote during a conversation; user-level, not per conversation |
| `plugin_data/gdocs/token.json` (1,119 B, mode 0600) | the Google Docs plugin's OAuth credential ([section 3](#3-credentials)) |
| `plugin_data/gdocs/bin/gdocs-<digits>` (31,938,752 B) | the plugin's binary |
| `bin/webm_encoder` (12,699,266 B), `bin/agentapi` (100 B), `bin/gdocs` | binaries; `bin/gdocs` is a symlink to `~/.gemini/config/plugins/gdocs/skills/gdocs/scripts/gdocs` |
| `cache/marketplaces/antigravity-plugins-official/` (207,829 B) | the plugin marketplace cache: `marketplace.json` (17 plugins, each with a name, version and archive URL and sha256), `meta.json` and `plugins/gdocs/0.0.6/`, a copy of the plugin the user installed |
| `builtin/skills/<name>/SKILL.md` x8, `builtin/.checksum`, `builtin/keep.txt` | bundled skills, the same set as `antigravity-cli/builtin/` |
| `agyhub_summaries_proto.pb` (1,436 B) | the app's counterpart of the CLI's `jetbox_summaries_proto.pb` |
| `antigravity_state.pbtxt` (850 B) | install and onboarding state (keys `installation_uuid`, `post_onboarding`, `agent_onboarding_completed`, `seen_nuxs` (by its name, the new-user-experience tips already shown), `migrate_convos_into_projects`, `migrate_retroactive_projects`, `migrations`); the CLI's counterpart is `jetski_state.pbtxt` |
| `installation_id` (36 B), `presence/<uuid>.lock` x4 (0 B), `crashes/crash_<pid>_<uuid>.log` (0 B) | as in the CLI directory |

Jetski and Jetbox are internal names that appear in the CLI's file names
and keyring service; the binary does not explain them.

**`brain/<uuid>/`** (observed, app and CLI): `.system_generated/logs/transcript.jsonl`
and `transcript_full.jsonl` (17,832 to 155,131 B in the app), one JSON line
per conversation step; the same lines split into files of about 100 KB
under `.system_generated/logs/chunks/transcript/0000000N.jsonl` and
`chunks/transcript_full/0000000N.jsonl`; `.system_generated/steps/<idx>/output.txt`,
the output of each tool step (10 to 4,426 B); and the empty directories
`scratch/` and `.user_uploaded/`. One app conversation also has
`.system_generated/messages/<uuid>.json` x3 (records with `sender`,
`recipient`, `content` and `timestamp`, two of them naming the
`run_command` tool call they came from), `messages/read.json` (a
read flag per message) and
`.system_generated/tasks/task-<idx>.log` x2 (the plain-text output of a
background task started by step `<idx>`); the CLI's brain directories
have no `messages/` or `tasks/`. The binary also names
`.system_generated/worktrees` and `.system_generated/subagents` (binary).
The line shapes are in
[section 2 of `analyzer/research/antigravity.md`](../../analyzer/research/antigravity.md#2-stores-relative-to-home).

**`~/.gemini/antigravity-cli/`** (live, observed on macOS, with binary
literal where noted): `antigravity-oauth-token` (1,670 B, see
[section 3](#3-credentials)); `bin/webm_encoder` (17 MB on Linux);
`brain/<uuid>/` as above (binary: `.system_generated/logs/transcript.jsonl`,
`transcript_full.jsonl`); `builtin/skills/<name>/`, `builtin/.checksum`,
`keep.txt` (bundled skills; binary also names
`~/.gemini/<app-name>/builtin/sidecars/<id>/` and
`builtin/plugins/<plugin>/sidecars/`); `cache/` with
`default_project_id.txt` (19 B, base64 text), `last_conversations.json`
(an object mapping an absolute workspace path to a conversation UUID) and
`onboarding.json` (three onboarding booleans) (observed), plus
`cache/projects.json` (binary: "stores workspace-to-project mappings in a
centralized `~/.gemini/antigravity-cli/cache/projects.json`"; not present
on the macOS install); `cli.log` symlink to `log/cli-<YYYYMMDD_HHMMSS>.log`
(binary `cli.log`); `conversation_summaries.db` (+`-wal`, `-shm`; binary
`conversation_summaries.db`, `ALTER TABLE conversation_summaries ...`),
which has only the `conversation_summaries` table; `conversations/<uuid>.db`
(+wal/shm); `crashes/` (empty); `history.jsonl` (binary);
`implicit/<uuid>.pb`; `installation_id` (binary);
`jetbox_summaries_proto.pb` (binary `jetbox_summaries_pb.SummariesState`);
`jetski_state.pbtxt` (binary; keys `installation_uuid`, `post_onboarding`,
`migrations`, observed); `last_check.timestamp`; `presence/<uuid>.lock`;
`settings.json` (docs: `~/.gemini/antigravity-cli/settings.json`; binary
`trustedWorkspaces` tag); `keybindings.json` (docs/settings);
`updater/{update.lock, update_status.json}`; legacy `hooks.json` (binary:
"wrote configurations to `~/.gemini/antigravity-cli/hooks.json` instead
of the shared `~/.gemini/config/hooks.json`").

**`~/.gemini/config/`**, shared by the CLI and the app (binary changelog,
live names, observed 232 KB on macOS): `mcp_config.json`, `hooks.json`,
`config.json`, `projects/<uuid>.json`, `skills/<name>/SKILL.md`,
`plugins/<name>/`, `rules/*.md`, `workflows/`, `global_workflows/`,
`sidecars/`, `GEMINI.md`, `AGENTS.md`, `skills.json`, `rules.json`,
`plugins.json`, `agents.json`, `workflows.json`, `.migrated`. The binary
also reads `~/.gemini/GEMINI.md` and `~/.gemini/AGENTS.md`, and names
legacy `~/.gemini/jetski/brain` and per-repo `.antigravitycli` workspace
dirs (both superseded). Observed on macOS:

- `config.json` (657 B): `plugins` {`gdocs` {`installedFrom` {`id`,
  `marketplace`, `version`}}} and `userSettings` {`globalPermissionGrants`
  {`allow`, an array of 3 strings}, `permissionGrantsV2Migrated`,
  `remoteControlHostname`, `sandboxEnabledAtV2Migration`}.
- `plugins/gdocs/`: the installed plugin, `plugin.json`, `README.md`,
  `skills/gdocs/SKILL.md`, nine reference documents and the launcher
  scripts `skills/gdocs/scripts/gdocs` (shell) and `gdocs.cmd`.
- `projects/<uuid>.json` (283 B), written by the app when a project is
  created: `id`, `isWorkspaceOnly`, `name`, `permissionGrants`,
  `projectResources` {`resources`, an array of objects whose `folderUri` is a `file://` URL},
  `settings`; and `projects/default-cli-project.json` (84 B, from the CLI)
  with an empty `projectResources`.
- `sidecars/<name>/sidecar.json` (725 B), the automation the user
  scheduled. A sidecar is the app's name for a long-running helper
  process that its language server supervises; the app starts the server
  with `--enable_sidecars` (`app.asar:dist/languageServer.js@4242552`
  `'--enable_sidecars',`). The file's keys are `builtin` ("schedule", the
  built-in sidecar that runs an agent task on a schedule),
  `display_name`, `description`, `args` (an array of 5 strings), `restart_policy`
  ("always") and `agent_permissions` {`access_grants`, an array of 2 strings}. No
  launchd job or cron entry was created, so the schedule runs only while
  the app's language server runs. Where a scheduled run's transcript
  lands was not observed: no run had fired.
- `mcp_config.json` and `.migrated`, both empty.

**The desktop app's Electron user-data directory.** Electron keeps each
app's own state, Chromium's storage included, in a per-user directory
that `app.getPath('userData')` returns, named after the app under the
per-OS application-data root. The root is `~/Library/Application Support`
on macOS and `%APPDATA%` on Windows
(`app.asar:node_modules/electron-log/src/node/NodeExternalApi.js@2235471`
`return path.join(home, 'Library/Application Support');` and @2235565
`return process.env.APPDATA || path.join(home, 'AppData/Roaming');`) and
`$XDG_CONFIG_HOME` or `~/.config` on Linux ([Electron app API](https://www.electronjs.org/docs/latest/api/app),
`app.getPath('appData')`, fetched 2026-10-13; the bundle snippets cover
macOS and Windows only).
So the directory is `~/Library/Application Support/Antigravity`
(observed), `~/.config/Antigravity` (Linux) and `%APPDATA%\Antigravity`
(Windows); the Linux and Windows paths are bundle-derived, not observed
on any real install. The app stores UI state there
(`app.asar:dist/paths.js@4313059` `function getAppStoragePath() {` ...
`path_1.default.join(electron_1.app.getPath('userData'), 'app_storage.json')`,
"lightweight key-value store for UI state") and a Node wrapper for plugin
scripts (`app.asar:dist/utils.js@4399333`
`const binPath = path_1.default.join(userDataPath, 'bin');` and @4399399
`const nodeWrapperPath = path_1.default.join(binPath, os === 'win32' ? 'agy-node.cmd' : 'agy-node');`).
Observed on macOS (5.3 MB, created 18:28): `app_storage.json` (1,528 B;
string values under the keys `antigravity-multi-conversation-layout-v3-<uuid>`
x4 and `-index`, `aux-pane-session`, `comments`,
`didAskForNotificationPermission`, `ide-install-wizard-shown`,
`jetski.onboarding.lastLoginIsGcpTos`, `jetski.onboarding.lastLoginUsername`
(the signed-in account name), `lastCreatedProjectId`,
`new-convo-last-selected-project`, `new-convo-magic-workspace-selected`,
`projectsOrder`), `bin/agy-node` (a 152 B `#!/bin/sh` wrapper that runs
the bundled `Antigravity Helper` with `ELECTRON_RUN_AS_NODE=1`),
`Preferences`, `Local State`, `Network Persistent State`, `.updaterId`,
`DevToolsActivePort`, `Cookies` (SQLite, 0 rows), `Local Storage/leveldb/`
(16 KB), `Session Storage/` (16 KB), `DIPS` + `DIPS-wal` (260 KB),
`Trust Tokens`, `declarative_performance_observer.db`, the symlinks
`SingletonCookie`, `SingletonLock`, `SingletonSocket`, and the Chromium
caches `Cache` (3.2 MB), `Code Cache` (52 KB), `GPUCache`,
`DawnGraphiteCache`, `DawnWebGPUCache` (548 KB each), `Shared Dictionary`
(52 KB) and `blob_storage`. There is no `User/` and no `logs/`, the
subdirectories the pre-2.0 catalog lines named.

**Logs.** Electron's logs directory is `~/Library/Logs/<name>` on macOS
and `<userData>/logs` elsewhere
(`app.asar:node_modules/electron-log/src/main/ElectronExternalApi.js@2216282`
`return this.getPath('logs') || super.getElectronLogPath();` and
`app.asar:node_modules/electron-log/src/node/NodeExternalApi.js@2233256`
`return path.join(this.getAppUserDataPath(appName), 'logs');`), and the
backend's log goes there too (`app.asar:dist/paths.js@4313430`
`function getLsLogPath() {` ...
`path_1.default.join(electron_1.app.getPath('logs'), constants_1.LS_LOG_FILE_NAME)`;
`app.asar:dist/constants.js@4136120`
`exports.LS_LOG_FILE_NAME = 'language_server.log';`). So the logs are in
`~/Library/Logs/Antigravity` (observed), `~/.config/Antigravity/logs` and
`%APPDATA%\Antigravity\logs` (bundle-derived, not observed on any real
install). Observed on macOS: `main.log` (1,696 B; lines
`[YYYY-MM-DD HH:MM:SS.mmm] [info]  <message>`, among them
`Starting app (v2.23.0) with dynamic port…`,
`Host bridge server listening on http://127.0.0.1:<port>`,
`LS Logs:     <path>`, `Electron Logs: <path>`, the IDE wizard line above,
`[AutoUpdater] ...` and an hourly `Checking for update`) and
`language_server.log` (160,403 B; lines in the format of glog, Google's
logging library: `ERROR: logging before google.Init: I|E|W<MMDD HH:MM:SS.ffffff> ...`).
The server log names `~/.gemini/config/projects/outside-of-project.json`
174 times (the file does not exist),
`~/.gemini/antigravity-cli/conversations/<uuid>.pb` twice, and the plugin
script, the scratch document and the two `bin/` entries once each.

`~/Library/Preferences/com.google.antigravity.plist` (916 B, observed)
holds only AppKit window and panel keys (`AppleTextDirection`,
`NSForceRightToLeftWritingDirection`, `NSNavPanelExpandedSizeForOpenMode`,
`NSOSPLastRootDirectory`, `NSTreatUnknownArgumentsAsOpen`) and has no
catalog line.

**The IDE** (community, consistent across four sources):
`~/.gemini/antigravity-ide/` with `conversations/<uuid>.db`,
`brain/<uuid>/` (Markdown artifacts `task.md`, `implementation_plan.md`,
`walkthrough.md`, each with `.metadata.json`, plus
`.system_generated/logs/transcript.jsonl`),
`knowledge/<ki-id>/{metadata.json, artifacts/}`, `knowledge.lock`
(damadorPL); docs/settings calls `~/.gemini/antigravity-ide/` the "local
app data directory". The upgrade leftover `~/.gemini/antigravity-backup/brain`
is reported by jazzyalex, and matches the bundle's backup directory. The
IDE's VS Code-fork app directory is named `Antigravity IDE`:
`%APPDATA%\Antigravity IDE\User\globalStorage\state.vscdb` (Devilaiger,
marioalbu08), `~/.config/Antigravity IDE/User/globalStorage/state.vscdb`
(dev.to); macOS by convention `~/Library/Application Support/Antigravity IDE`.
The IDE installs its program to `/Applications/Antigravity IDE.app`,
`%LOCALAPPDATA%\Programs\Antigravity IDE\` and
`~/.local/share/antigravity-ide` (`app.asar:dist/ideInstall/constants.js@4162112`
`function getIdeInstallPath() {` with `'/Applications/Antigravity IDE.app'`,
`'Programs', 'Antigravity IDE', 'Antigravity IDE.exe'` and
`path.join(os.homedir(), '.local', 'share', 'antigravity-ide')`); those are
binaries, not state, and have no catalog line.

**WSL.** On Windows the app can run its language server inside a WSL
(Windows Subsystem for Linux) distribution, installed at
`~/.antigravity-server/bin/<version>/` in the Linux home
(`app.asar:dist/wsl.js@4411665`
`` return `$HOME/.antigravity-server/bin/${version}`; ``; bundle-derived,
not observed on any real install). The directory holds the server binary;
where that server keeps conversations is not determined.

Enterprise `admin_settings.json` is system-level: `/etc/antigravity/`,
`/Library/Application Support/Antigravity/`, `...\Antigravity\` (binary).

Relocation env vars: none found for the home dir. `ANTIGRAVITY_EXECUTABLE_DATA_DIR`,
`AGY_ACCOUNT`, `AGY_ADC_AUTH`, `ANTIGRAVITY_PROJECT_ID`,
`ANTIGRAVITY_CONVERSATION_ID` exist (binary) but their effect on paths is
unknown.

## 3. Credentials

- Keyring first: `zalando/go-keyring` with Secret Service, service name
  `jetski-standalone-oauth-token` (binary); docs/cli/install: Apple
  Keychain, Linux Secret Service, Windows Credential Manager. File fallback
  when the keyring is "bypassed or unreachable" (binary changelog) is
  `~/.gemini/antigravity-cli/antigravity-oauth-token` (live, 1,670 B; the
  whole literal is not in the strings, so the name is assembled at runtime).
  Flagged by `*.gemini/antigravity-cli/antigravity-oauth-token`. The
  app's `~/.gemini/antigravity/` held no token file on the macOS install
  (observed).
- `plugin_data/<plugin>/token.json` under a `.gemini` data directory:
  the Google Docs plugin's OAuth credential (observed,
  `~/.gemini/antigravity/plugin_data/gdocs/token.json`, 1,119 B, mode
  0600), keys `client_id`, `client_secret`, `email`, `scopes` (an array of 8 URLs),
  `token` {`access_token`, `expiry`, `refresh_token`, `token_type`} and
  `updated_at`. Collector 1.11.0 collected it unflagged (issue 84); from
  1.12.0 `*.gemini/antigravity*/plugin_data/*/token.json` flags it in
  every `.gemini/antigravity*` directory.
- `GEMINI_API_KEY` with `modelProvider: "gemini"` in `settings.json`
  (binary changelog; docs/cli/install); the key is env-only.
- `~/.gemini/config/mcp_config.json` can embed MCP `env` and `headers`
  (binary `McpStdioTransport.EnvEntry`, `McpHttpTransport.HeadersEntry`).
- The Electron user-data directory's `Cookies` (SQLite, 0 rows on the
  observed install) and `Local Storage/leveldb/` (16 KB, contents not
  read) are collected unflagged; whether either can hold a credential
  is not determined. `app_storage.json` holds the signed-in account
  name (`jetski.onboarding.lastLoginUsername`), which identifies the user
  but is not a credential.
- IDE `state.vscdb` holds the conversation index
  (`antigravityUnifiedStateSync.trajectorySummaries`, Devilaiger) and, as a
  VS Code fork, probably auth state; collect unflagged.

## 4. Exclude

Sizes are from the macOS install (observed) unless noted.

- `.gemini/antigravity/bin`, `.gemini/antigravity-cli/bin`,
  `.gemini/antigravity-ide/bin`, `.gemini/antigravity-backup/bin`: the
  encoder and launcher binaries (app 12,699,366 B in 2 files; CLI
  12,787,712 B on macOS, 17 MB on Linux). One line per directory rather
  than `.gemini/antigravity*/bin`, because `*` in an exclusion crosses
  `/` and that form would also prune any `bin` directory the agent writes
  under `brain/<uuid>/`.
- `.gemini/antigravity*/plugin_data/*/bin`: plugin binaries (the Google
  Docs plugin's, 31,938,752 B). The plugin's `token.json` beside it stays
  collected.
- `.gemini/antigravity*/cache/marketplaces`: the plugin marketplace cache
  (16 files, 207,829 B), a copy of the marketplace index and of each
  downloaded plugin; the installed copy is in `~/.gemini/config/plugins/`.
  The rest of `cache/` is collected.
- `.gemini/antigravity*/brain/*/.system_generated/worktrees` (git
  worktrees of the project, binary).
- The Chromium caches in the Electron user-data directory:
  `*/Antigravity/Code Cache`, `*/Antigravity/GPUCache`,
  `*/Antigravity/DawnGraphiteCache`, `*/Antigravity/DawnWebGPUCache`,
  `*/Antigravity/blob_storage`, `*/Antigravity/Shared Dictionary`,
  `*/Antigravity/CachedData`, `*/Antigravity/Crashpad` (observed:
  `Code Cache` 52 KB, `GPUCache`, `DawnGraphiteCache` and
  `DawnWebGPUCache` 548 KB each, `Shared Dictionary` 52 KB; `CachedData`
  and `Crashpad` did not exist), and `Cache` (3.2 MB) as
  `.config/Antigravity/Cache`, `Library/Application Support/Antigravity/Cache`
  and `AppData/Roaming/Antigravity/Cache`. `Cache` is named under each base
  because the PowerShell collector matches without regard to case, and
  `*/Antigravity/Cache` would also prune `.gemini/antigravity/cache`. None
  of the other patterns matches the data directories' lower-case `cache`,
  `crashes` or `bin`.
- `AppData/Local/agy` (CLI install) and `.antigravity/extensions`.
  `.cache/antigravity` (the marketplace staging directory) is collected;
  it was empty on both installs.
- `Antigravity IDE` Electron caches (`Cache`, `CachedData`, `GPUCache`,
  `Code Cache`, by VS Code convention) are outside the collected `User`
  and `logs` subdirectories.

Kept: `.system_generated/subagents` (sub-conversation data), `scratch/`,
`builtin/` (bundled skills, 176 KB in the CLI directory) and the Electron
`Local Storage/`, `Session Storage/` and `DIPS`.

## 5. Project-local files

`.agents/` workspace customizations (`.agents/agents/`, binary changelog;
damadorPL `<project-root>\.agents\`), `.antigravityignore` (binary),
`.antigravity-plugin` (binary), legacy `.antigravitycli/` (binary, removed
in favour of `cache/projects.json`). No per-project database.

## 6. Where the workspace path is recorded

- `history.jsonl`: `workspace` per prompt (CLI only; the app writes no
  `history.jsonl`) ([section 2 of `analyzer/research/antigravity.md`](../../analyzer/research/antigravity.md#2-stores-relative-to-home)).
- `settings.json`: `trustedWorkspaces` array (binary json tag; docs/settings).
- `cache/projects.json`: workspace to project map (binary changelog).
- `config/projects/<uuid>.json`: `projectResources.resources[].folderUri`,
  a `file://` URL of the project folder (observed on macOS, written by
  the app). `discover_projects` and `Find-Projects` read `file:///` URLs
  from `.gemini/config/projects/*.json`, and a collection of the macOS
  install discovered the folder. JSON tags present in the binary:
  `workspace_uris`, `workspace_paths`, `workspace_uri`, `project_id`,
  `display_name`, `cwd`.
- `antigravity-cli/cache/last_conversations.json`: an object whose keys
  are absolute workspace paths (observed). Not read by the collectors.
- `conversation_summaries.db` (`workspace_uris` column) and the
  per-conversation `*.db`: SQLite only, read by the analyzer.

## 7. Confidence

High: the CLI layout (live, observed and binary literals); the desktop
app's data directory `~/.gemini/antigravity` and its contents (bundle and
observed); the Electron user-data directory name `Antigravity` and the
macOS logs directory (bundle and observed); the roles of
`antigravity-ide` and `antigravity-backup` (bundle); the plugin token's
location and keys (observed); the keyring service and file fallback;
`~/.gemini/config` contents, including `projects/<uuid>.json` and
`sidecars/<name>/sidecar.json` (observed). Medium: the Linux and Windows
paths of the Electron user-data directory and logs (bundle-derived, not
observed on any real install); `antigravity-ide/conversations` and
`brain` (four community sources, no real install); the `Antigravity IDE`
app-dir name on macOS (inferred from the Windows and Linux names);
`knowledge/` sub-layout (one source); `.cache/antigravity` purpose.
Not determined: which of the four observed app conversations belongs to
which task (modification times only, [section 1](#1-source-and-evidence-level));
where a scheduled sidecar run writes its transcript; whether the Electron
`Cookies` or `Local Storage/` can hold a credential; where the WSL
language server keeps state; the `implicit/*.pb` and `presence/`
semantics; whether `~/.antigravity` is still written by any build.
