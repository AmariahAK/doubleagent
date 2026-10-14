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
- **observed**: the macOS and Ubuntu real installs below, read for file
  names, sizes, key names, value types, counts and log-line templates with
  ids redacted only.
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

**Observed (Linux, CLI)** (issues 83, 89, 90): `agy` 1.3.4 (`agy --version`)
at `~/.local/bin/agy`, ELF aarch64, 204,492,984 bytes, sha256
`08d619ae3969c33b9cba5eac2a54f4566cbca1b5de68968167cb908ced5b4824`, in
the author's Ubuntu lab VM (Ubuntu 26.04.1 LTS, aarch64, Linux
7.0.0-38-generic), installed 2026-10-13 21:37 local time (EDT) and
observed the same day; the embedded changelog's newest heading is
`## 1.3.3`. `~/.local/bin` is not on the non-interactive `PATH`. The user
ran a few turns, which left one conversation
(`~/.gemini/antigravity-cli/conversations/<uuid>.db`, 26 steps,
`trajectory_meta.source` 17) and a project folder the agent wrote files
into. Against 1.2.x the CLI now also writes `annotations/<uuid>.pbtxt`,
`cache/marketplaces/`, a `conversationId` key in `history.jsonl` and a
`permissions` key in `settings.json` ([section 2](#2-per-user-storage)),
and its log names a file secret store it did not create
([section 3](#3-credentials)). The CLI left `~/.cache/antigravity/staging/`
empty, as on macOS.

**Observed (Linux, desktop app)** (issues 83, 91): version 2.23.1
(`main.log`: `Starting app (v2.23.1) with dynamic port…`), in the same VM,
first run 2026-10-13 21:29 local time. It was downloaded as
`~/Downloads/Antigravity.tar.gz` and unpacked by hand to `~/Antigravity/`
(285 MB), a binary install that gets no catalog line: the Electron binary
`antigravity` (220,466,568 B, sha256
`c543041069aa2e478235447cb636f9f09faab15003862029d226bb14b8dc655b`), a
setuid-root `chrome-sandbox`, the Chromium libraries and resource packs,
`resources/app.asar` (4,486,221 B, the size of the macOS 2.23.0 asar,
sha256 `b8ec3628df2a12ee9deac5dc06367f238065af146bfe6298fdad6db5f9790d9c`),
`resources/app-update.yml` (keys `provider`, `url`,
`updaterCacheDirName`), `resources/bin/language_server` (181,358,800 B,
sha256 `310ee8e0cba4c4ee05504ac8021cbd3544a79c06cc01c790536361625c5fffb3`)
and `resources/bin/webm_encoder`. It is not an AppImage (a self-contained
Linux application package): `main.log` warns
`APPIMAGE env is not defined, current application is not an AppImage`.
The user ran a few tasks, among them a coding task and a scheduled
automation, with no listing between tasks, so the mapping from task to
file is by modification time only, as on macOS: four conversations under
`~/.gemini/antigravity/conversations/` (21:45, 21:51, 21:55, 22:00, all
`trajectory_meta.source` 1), a project folder `~/demo2/` (21:53 to 21:54)
whose project file is 21:47, the automation's `sidecar.json` (21:58 to
21:59) and its `sidecar_data/` (22:00), the Google Docs plugin's token
(21:49), and a Markdown report the agent wrote at the home root (21:59).
The app wrote `~/.gemini/antigravity/` (56 MB), files in
`~/.gemini/config/` (320 KB), and the Electron user-data directory
`~/.config/Antigravity/` (8.9 MB) with its `logs/` inside it, as the
bundle says. It created no `~/.config/antigravity` (lower case),
`~/.antigravity`, `~/.antigravity-server`, `~/.gemini/antigravity-ide` or
`~/.gemini/antigravity-backup`, no `~/.config/autostart` entry, no user
systemd unit and no crontab entry for the schedule; `systemctl --user`
showed only the running app's transient `app-antigravity-<pid>.scope`.
The user also kept the CLI's project folder inside the install directory,
`~/Antigravity/demo/`.

Collector 1.12.0, run in the VM as the user (`-q -u <user>`,
2026-10-14T02:04Z), collected 233 files (7,002,562 B) with 13
`skipped_excluded` rows, 4 symlinks, 0 errors and dash as the worker
shell. The excluded rows were the `cache/marketplaces` and `bin`
directories of both `.gemini` data directories, the app's
`plugin_data/gdocs/bin`, and the eight Chromium cache directories of
`~/.config/Antigravity` ([section 4](#4-exclude)); the only `secret: true`
row was the plugin's `token.json`. Collected and unflagged with
credential-like names were the Electron `Cookies` and `Trust Tokens`
stores and their `-journal` files ([section 3](#3-credentials)). Three
low-value directories were collected that the final 1.12.0 tables now
exclude: `.gemini/antigravity/lib`, `.gemini/config/node_modules` and
`.config/Antigravity/Dictionaries`. One project was discovered, the CLI's
`~/Antigravity/demo`; the app's `~/demo2` was missed (issue 91,
[section 6](#6-where-the-workspace-path-is-recorded)).

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
- `~/.gemini/antigravity-cli/` is the CLI's (binary, live, observed on
  macOS and Linux).
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

**`~/.gemini/antigravity/`** (observed, macOS, app 2.23.0, 49 MB; the
Linux install of 2.23.1 had the same layout at 56 MB, with the additions
listed after the table):

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

Added on Linux (observed, app 2.23.1):

- `sidecar_data/<name>/` (22:00): `logs/sidecar.log` (388 B) and an
  empty `data/`, written by the scheduled automation named `<name>`. The
  log's lines, digits redacted:
  `=== sidecar "<name>" started at <timestamp> ===`, then
  `<date> <time> [schedule] Scheduler started for schedule: "CRON_TZ=<zone> N N * * *"`,
  `[schedule] Calculated jitter: NmNN.NNNNNNNNs` and
  `[schedule] Next execution scheduled in NNhNNmNNs (at <UTC time>), will run by ...`.
  So a scheduled run's own output lands under `sidecar_data/<name>/logs/`;
  no run had fired, and what a run writes, and whether it becomes a
  conversation, is still not observed.
- `lib/node_modules/sidecar_sdk/` (5 files, 17,508 B: `package.json`,
  `index.mjs`, `preload.js`, `esm_resolver.js`, `register_loader.js`):
  the sidecar SDK, the JavaScript library the app installs for sidecar
  code; the same five files are in `~/.gemini/config/node_modules/sidecar_sdk/`.
  Code, not state, and excluded from 1.12.0 ([section 4](#4-exclude)).
- `brain/<uuid>/.system_generated/steps/<idx>/content.md` (24,820 B,
  Markdown) beside that step's `output.txt`, in one conversation.
- `conversation_summaries.db` (167,936 B) with the macOS schema; the FTS5
  shadow tables listed are `conversations_fts_config`, `_content`,
  `_data`, `_docsize` and `_idx`.
- `scratch/<name>.md` (675 B), `plugin_data/gdocs/token.json` (1,126 B,
  mode 0600) and `plugin_data/gdocs/bin/gdocs-<digits>` (36,320,890 B),
  `bin/webm_encoder` (15,860,003 B), `bin/agentapi` (84 B), the `bin/gdocs`
  symlink and `cache/marketplaces/antigravity-plugins-official/`
  (282,624 B) as on macOS.

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

New in CLI 1.3.x (observed, Linux, 1.3.4): `annotations/<uuid>.pbtxt`
(37 B, one `title:` field, as in the app's directory);
`cache/marketplaces/antigravity-plugins-official/` (`marketplace.json`
and `meta.json`, 32,768 B, excluded); a `conversationId` key on
`history.jsonl` lines beside `display`, `timestamp` and `workspace` (one
of the two lines had it); and `settings.json` (156 B) with `permissions`
{`allow`, an array of 2 strings} beside `trustedWorkspaces` (an array of
1 absolute path). The log directory holds `log/cli-<YYYYMMDD_HHMMSS>.log`
files (22,498 and 45,442 B) in glog format (glog is Google's logging
library) with `cli.log` linking to the
newest; besides the secret-store line in [section 3](#3-credentials),
they name `~/.gemini/config/config.json`, `~/.gemini/extensions` (Gemini
CLI's extension directory, absent on this install) and the workspace
paths.

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
  `remoteControlHostname`, `sandboxEnabledAtV2Migration`}. On Linux
  (1,356 B, 22:00) it also has `sidecars` {`<name>` {`argumentValues`
  (null), `enabled` (bool), `projectId` (UUID), `resolvedPermissions`
  {`accessGrants`, an array of 2 strings}, `schemaVersion` (number)}},
  one entry per scheduled automation.
- `plugins/gdocs/`: the installed plugin, `plugin.json`, `README.md`,
  `skills/gdocs/SKILL.md`, nine reference documents and the launcher
  scripts `skills/gdocs/scripts/gdocs` (shell) and `gdocs.cmd`.
- `projects/<uuid>.json` (283 B), written by the app when a project is
  created: `id`, `isWorkspaceOnly`, `name`, `permissionGrants`,
  `projectResources` {`resources`, an array of objects whose `folderUri` is a `file://` URL},
  `settings`; and `projects/default-cli-project.json` (84 B, from the CLI)
  with an empty `projectResources`. The file is pretty-printed: on Linux
  (293 B) the `folderUri` key is followed by a colon, two spaces and the
  quoted `file:///` URL. Linux also had a second shape (382 B, 22:00) with
  no folder: `id`, `name`, `permissionGrants` {`permissionGrants`
  {`allow`, an array of 2 strings}, `v2Migrated`}, an empty
  `projectResources` and `settings` {`artifactReviewMode`}; by its time
  and its grants, the project the scheduled automation runs under (the
  `config.json` `sidecars` entry has a `projectId`).
- `sidecars/<name>/sidecar.json` (725 B), the automation the user
  scheduled. A sidecar is the app's name for a long-running helper
  process that its language server supervises; the app starts the server
  with `--enable_sidecars` (`app.asar:dist/languageServer.js@4242552`
  `'--enable_sidecars',`). The file's keys are `builtin` ("schedule", the
  built-in sidecar that runs an agent task on a schedule),
  `display_name`, `description`, `args` (an array of 5 strings), `restart_policy`
  ("always") and `agent_permissions` {`access_grants`, an array of 2 strings}. No
  launchd job or cron entry was created on macOS, and no autostart entry,
  user systemd unit or crontab entry on Linux, so the schedule runs only
  while the app's language server runs. The Linux `sidecar.json` (791 B)
  has the same keys. The scheduler's log is
  `~/.gemini/antigravity/sidecar_data/<name>/logs/sidecar.log` (observed,
  Linux); where a fired run's transcript lands was not observed: no run
  had fired on either install.
- `mcp_config.json` and `.migrated`, both empty.
- `node_modules/sidecar_sdk/` (observed, Linux, 5 files, 17,508 B): a copy
  of the sidecar SDK, excluded from 1.12.0.

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
(observed), `~/.config/Antigravity` (observed on Linux, app 2.23.1) and
`%APPDATA%\Antigravity` (Windows, bundle-derived, not observed on any
real install). The app stores UI state there
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

Observed on Linux (`~/.config/Antigravity/`, 8.9 MB, created 21:29):
`app_storage.json` (1,681 B; the macOS keys plus `aux-pane-v2-session`
and `sidebar_collapsed_sections`), `bin/agy-node` (80 B), `logs/main.log`
(2,128 B) and `logs/language_server.log` (135,703 B), `Cookies`
(20,480 B), `Local Storage/leveldb/` (6 files, 628 B), `Session Storage/`
(6 files, 642 B), `DIPS` (36,864 B) and `DIPS-wal` (115,392 B),
`Trust Tokens` (36,864 B), `declarative_performance_observer.db`
(32,768 B), `DevToolsActivePort`, `Local State` (57 B;
`uninstall_metrics.installation_date2`), `Network Persistent State`
(944 B), `Preferences` (132 B; `electron.media.device_id_salt`,
`spellcheck.dictionaries`, `spellcheck.dictionary`), the `Singleton*`
symlinks, and the caches `Cache` (6,959,104 B), `Code Cache`
(114,688 B), `GPUCache` (614,400 B), `DawnGraphiteCache` and
`DawnWebGPUCache` (307,200 B each), `Shared Dictionary` (65,536 B),
`blob_storage` (8,192 B) and `Crashpad/` (8,192 B; a 36 B `client_id`,
Crashpad being Chromium's crash reporter). New against macOS:
`Dictionaries/en-US-10-1.bdic` (451,968 B), the spell-check dictionary
Chromium downloads in its binary `.bdic` format, excluded from 1.12.0.

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
`~/Library/Logs/Antigravity` (observed), `~/.config/Antigravity/logs`
(observed on Linux) and `%APPDATA%\Antigravity\logs` (bundle-derived, not
observed on any real install). Observed on macOS: `main.log` (1,696 B; lines
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
Observed on Linux: `main.log` has the macOS lines with `v2.23.1`, plus the
AppImage warning ([section 1](#1-source-and-evidence-level)) and
`Shutting down language server…`; `language_server.log` names
`~/.gemini/config/projects/outside-of-project.json` 194 times (absent)
and `~/.gemini/antigravity-cli/conversations/<uuid>.pb` once.

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
- `plugin-secrets.json`, the CLI's file store for plugin secrets when no
  OS keychain is usable (issue 90). Each CLI 1.3.4 log on Linux has two
  lines
  `I<MMDD HH:MM:SS.ffffff> <n> auth_store.go:136] Using file-based secret storage at ~/.config/antigravity/plugin-secrets.json`
  (observed, home redacted), and the binary carries the literal
  `plugin-secrets.json` beside `keychain get %s: %w` and
  `keychain set %s: %w` (observed, `agy` 1.3.4 linux-arm64, sha256 in
  [section 1](#1-source-and-evidence-level)). The file did not exist on
  the install, since nothing was authorised from the CLI, and neither did
  `~/.config/antigravity`. The lower-case directory under `~/.config` is
  Go's `os.UserConfigDir()` on Linux; the macOS and Windows paths,
  `~/Library/Application Support/antigravity/plugin-secrets.json` and
  `%APPDATA%\antigravity\plugin-secrets.json`, are inferred from
  `os.UserConfigDir()`, not observed. On those case-insensitive
  filesystems the directory is the app's Electron user-data directory
  when that exists. From 1.12.0 the three paths are catalog entries and
  `.config/[Aa]ntigravity/plugin-secrets.json`,
  `Library/Application Support/[Aa]ntigravity/plugin-secrets.json` and
  `AppData/Roaming/[Aa]ntigravity/plugin-secrets.json` flag them. The
  class accepts either case because whichever product creates the
  directory first fixes its spelling, and the sh collector records a file
  inside a case variant of a matched directory under that directory's
  spelling (a Linux image read from a case-insensitive filesystem
  included).
- `GEMINI_API_KEY` with `modelProvider: "gemini"` in `settings.json`
  (binary changelog; docs/cli/install); the key is env-only.
- `~/.gemini/config/mcp_config.json` can embed MCP `env` and `headers`
  (binary `McpStdioTransport.EnvEntry`, `McpHttpTransport.HeadersEntry`).
- The Electron user-data directory's `Cookies` (SQLite, 0 rows on the
  macOS install, 20,480 B on Linux), `Trust Tokens` (Chromium's store for
  the Private State Tokens web API, 36,864 B on Linux) with their
  `-journal` files, and `Local Storage/leveldb/` (16 KB on macOS, 628 B on
  Linux, contents not read) are collected unflagged; whether any of them
  can hold a credential is not determined. `app_storage.json` holds the signed-in account
  name (`jetski.onboarding.lastLoginUsername`), which identifies the user
  but is not a credential.
- IDE `state.vscdb` holds the conversation index
  (`antigravityUnifiedStateSync.trajectorySummaries`, Devilaiger) and, as a
  VS Code fork, probably auth state; collect unflagged.

## 4. Exclude

Sizes are from the macOS install (observed) unless noted; the Linux
install's are given where they were recorded.

- `.gemini/antigravity/bin`, `.gemini/antigravity-cli/bin`,
  `.gemini/antigravity-ide/bin`, `.gemini/antigravity-backup/bin`: the
  encoder and launcher binaries (app 12,699,366 B in 2 files; CLI
  12,787,712 B on macOS, 17 MB on Linux; on the Linux install of CLI
  1.3.4 and app 2.23.1, 15,872,000 B and 15,876,096 B as the manifest
  recorded them). One line per directory rather
  than `.gemini/antigravity*/bin`, because `*` in an exclusion crosses
  `/` and that form would also prune any `bin` directory the agent writes
  under `brain/<uuid>/`.
- `.gemini/antigravity*/plugin_data/*/bin`: plugin binaries (the Google
  Docs plugin's, 31,938,752 B; 36,327,424 B on Linux). The plugin's
  `token.json` beside it stays collected.
- `.gemini/antigravity*/cache/marketplaces`: the plugin marketplace cache
  (16 files, 207,829 B; on Linux 282,624 B in the app's directory and
  32,768 B in the CLI's, which has one from 1.3.x), a copy of the
  marketplace index and of each downloaded plugin; the installed copy is
  in `~/.gemini/config/plugins/`. The rest of `cache/` is collected.
- `.gemini/antigravity*/brain/*/.system_generated/worktrees` (git
  worktrees of the project, binary).
- `.gemini/antigravity*/lib/node_modules` and `.gemini/config/node_modules`:
  the sidecar SDK the app installs twice (observed on Linux, 5 files and
  17,508 B in each), code rather than state. The `*` crosses `/`, so the
  first also prunes a `lib/node_modules` an agent writes under `brain/`,
  which is a dependency tree as well.
- The Chromium caches in the Electron user-data directory:
  `*/Antigravity/Code Cache`, `*/Antigravity/GPUCache`,
  `*/Antigravity/DawnGraphiteCache`, `*/Antigravity/DawnWebGPUCache`,
  `*/Antigravity/blob_storage`, `*/Antigravity/Shared Dictionary`,
  `*/Antigravity/CachedData`, `*/Antigravity/Crashpad` (observed:
  `Code Cache` 52 KB, `GPUCache`, `DawnGraphiteCache` and
  `DawnWebGPUCache` 548 KB each, `Shared Dictionary` 52 KB; `CachedData`
  and `Crashpad` did not exist on macOS; on Linux `Code Cache` 114,688 B,
  `GPUCache` 614,400 B, `DawnGraphiteCache` and `DawnWebGPUCache`
  307,200 B each, `Shared Dictionary` 65,536 B, `blob_storage` 8,192 B,
  `Crashpad` 8,192 B), `*/Antigravity/Dictionaries` (the spell-check
  dictionary, 451,968 B on Linux), and `Cache` (3.2 MB; 6,959,104 B on
  Linux) as
  `.config/Antigravity/Cache`, `Library/Application Support/Antigravity/Cache`
  and `AppData/Roaming/Antigravity/Cache`. `Cache` is named under each base
  because the PowerShell collector matches without regard to case, and
  `*/Antigravity/Cache` would also prune `.gemini/antigravity/cache`. None
  of the other patterns matches the data directories' lower-case `cache`,
  `crashes` or `bin`.
- `AppData/Local/agy` (CLI install) and `.antigravity/extensions`.
  `.cache/antigravity` (the marketplace staging directory) is collected;
  it was empty on every install checked.
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
- `history.jsonl` also carries `conversationId` from CLI 1.3.x (observed,
  Linux), which joins a prompt to its conversation; the analyzer uses it
  as the row's session id ([section 2 of `analyzer/research/antigravity.md`](../../analyzer/research/antigravity.md#2-stores-relative-to-home)).
  The collectors read only `workspace`.
- `config/projects/<uuid>.json`: `projectResources.resources[].folderUri`,
  a `file://` URL of the project folder (observed on macOS and Linux,
  written by the app; the folder-less shape in
  [section 2](#2-per-user-storage) has none). `Find-Projects` in the
  PowerShell collector reads these URLs. `discover_projects` in the sh
  collector did not before 1.12.0 (issue 91): from 1.3.0 its pattern
  required a slash after `file:///`, so no `file://` URI matched, and the
  Linux collection missed the app's project folder. The earlier statement
  here that a collection of the macOS install discovered the folder was
  wrong; that folder was found from other sources. From 1.12.0
  `abs_strings` matches `file://` followed by the path's own `/`, and a
  Windows URI (`file:///C:/x`, or `file:///c%3A/x`) yields the
  drive-relative `/x` that image mode prefixes with the root. JSON tags
  present in the binary: `workspace_uris`, `workspace_paths`,
  `workspace_uri`, `project_id`, `display_name`, `cwd`.
- `antigravity-cli/cache/last_conversations.json`: an object whose keys
  are absolute workspace paths (observed). Not read by the collectors.
- `conversation_summaries.db` (`workspace_uris` column) and the
  per-conversation `*.db`: SQLite only, read by the analyzer.

## 7. Confidence

High: the CLI layout (live, observed and binary literals); the desktop
app's data directory `~/.gemini/antigravity` and its contents (bundle and
observed); the Electron user-data directory name `Antigravity` and the
macOS logs directory (bundle and observed); the Linux Electron
user-data directory `~/.config/Antigravity` and its `logs/` (bundle and
observed, app 2.23.1); the roles of
`antigravity-ide` and `antigravity-backup` (bundle); the plugin token's
location and keys (observed); the keyring service and file fallback;
`~/.gemini/config` contents, including `projects/<uuid>.json` and
`sidecars/<name>/sidecar.json` (observed); the CLI's log line naming
`~/.config/antigravity/plugin-secrets.json` on Linux (observed). Medium:
the Windows path of the Electron user-data directory and logs
(bundle-derived, not observed on any real install); the macOS and
Windows paths of `plugin-secrets.json` (inferred from Go's
`os.UserConfigDir()`, not observed) and its contents (never observed); `antigravity-ide/conversations` and
`brain` (four community sources, no real install); the `Antigravity IDE`
app-dir name on macOS (inferred from the Windows and Linux names);
`knowledge/` sub-layout (one source); `.cache/antigravity` purpose.
Not determined: which of the observed app conversations belongs to which
task, on either install (modification times only,
[section 1](#1-source-and-evidence-level)); what a fired scheduled run
writes and whether it becomes a conversation (the scheduler's own log is
`sidecar_data/<name>/logs/sidecar.log`, observed on Linux, but no run
fired); whether the Electron
`Cookies` or `Local Storage/` can hold a credential; where the WSL
language server keeps state; the `implicit/*.pb` and `presence/`
semantics; whether `~/.antigravity` is still written by any build.
