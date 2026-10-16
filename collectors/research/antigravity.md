---
title: "antigravity: on-disk paths (CLI agy, the desktop app and the IDE)"
parent: "Collector research"
grand_parent: "Collectors"
nav_order: 4
---
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
- **observed**: the macOS, Ubuntu and Windows real installs below, read
  for file names, sizes, key names, value types, counts and log-line
  templates with ids redacted only.
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

**Observed (Windows, CLI)** (issues 83, 89, 90): `agy` 1.3.5
(`agy --version`) at `%LOCALAPPDATA%\agy\bin\agy.exe`, on `PATH`,
184,062,616 B, sha256
`223953a7d64ad199bbeaae3cf84d634b0ec3917979c7a60feac6ade05d50888b`,
installed 2026-10-14T23:56:21Z in the author's Parallels lab VM, Windows
11 ARM64 build 26300 (`ver` reports `10.0.26300.9550`; ARM64 is the
64-bit Arm architecture), and observed the same evening (US Eastern
daylight time; the UTC times below cross into 2026-10-15). The
executable's version resource (`VersionInfo.ProductVersion`, the version
Windows shows in the file's properties) is empty. The embedded
changelog's newest heading is `## 1.3.4`, with `## 1.3.0` to `## 1.3.4`
present, and an ASCII search over the file finds the literals
`plugin-secrets.json`, `Using file-based secret storage`, `wincred` and
`CredWrite` ([section 3](#3-credentials)). No WSL (Windows Subsystem for
Linux) distribution is installed. The CLI created
`~/.gemini/antigravity-cli/` at 00:22:29Z (`~` is `%USERPROFILE%`,
`C:\Users\<user>`, here). The user started it from `<home>\demo2`,
typed with a lower-case `users` (`C:\users\<user>\demo2`), and ran a
coding task that wrote one source file per language into ten
subdirectories and a `README.md` (00:25:07Z to 00:27:16Z). That left one
conversation, `conversations/<uuid>.db` (983,040 B, 00:28:12Z, 38 steps,
`trajectory_meta.source` 17, no `-wal` or `-shm` sidecar when listed).
Against 1.3.4 on Linux, the CLI also wrote
`cache/conversation_metadata.json` and copied the desktop app's
conversations into its own summaries database, its `cli.log` is a hard
link rather than a symlink ([section 2](#2-per-user-storage)), and its
OAuth token went to the Windows Credential Manager, not a file
([section 3](#3-credentials)).

**Observed (Windows, desktop app)** (issues 83, 84, 91): version 2.23.1
(`main.log`: `Starting app (v2.23.1) with dynamic port…`; the version
resource of `Antigravity.exe` has `ProductVersion` `2.23.1.0` and
`FileVersion` `2.23.1`), in the same VM, first launched
2026-10-14T23:56:11Z. The per-user installer was left at
`%LOCALAPPDATA%\antigravity-updater\installer.exe` (155,215,064 B, sha256
`428ad29354a12654db8be066cbce1fb307dca538b51176a584c1009cb59c3fbc`,
23:55:21Z) and installed the app to `%LOCALAPPDATA%\Programs\antigravity\`
(424 files, 574,823,898 B, 23:56:09Z): `Antigravity.exe` (226,382,336 B,
sha256 `16febcd47a2a6823fe9ec4847b60f2fc766a46c8c355643185326a2879668243`),
`Uninstall Antigravity.exe`, `resources\app.asar` (4,486,221 B, sha256
`b8ec3628df2a12ee9deac5dc06367f238065af146bfe6298fdad6db5f9790d9c`,
byte-identical to the Linux 2.23.1 asar), `resources\app.asar.unpacked\`
(Node modules, among them `chrome-devtools-mcp`),
`resources\app-update.yml` (144 B), `resources\elevate.exe` (107,520 B),
`resources\bin\language_server.exe` (160,643,584 B, sha256
`32d65353f033600274203137913207c02f636c214b8233c529a2afa0ee55ecf5`),
`resources\bin\webm_encoder.exe` (12,472,320 B, sha256
`e78f6cd6292baeb2d322cba9a5e66f2e42aed5589cba175fe4aa5dd6daea90fd`) and
the usual Electron and Chromium files (`locales\`, `*.pak`, `icudtl.dat`,
`ffmpeg.dll`, `vulkan-1.dll`, `d3dcompiler_47.dll`,
`LICENSES.chromium.html`). It also made a Start Menu shortcut,
`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Antigravity.lnk`, and
an uninstall entry under
`HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall` (HKCU is
`HKEY_CURRENT_USER`, the per-user registry hive) with `DisplayName`
`Antigravity`, `DisplayVersion` `2.23.1` and no `InstallLocation`. There
was no `Run` key entry, no scheduled task and nothing in the Startup
folder, so, as on macOS and Linux, the schedule runs only while the app
runs. While the app ran, six `Antigravity.exe` processes and one
`language_server.exe` were running: the same backend as on the other
platforms.

The user ran, in the app: a question with no file writes; a coding task
in a project folder `<home>\demo`, which wrote six files there (a hello
world in C, Go, JavaScript, Python and Rust, and a `README.md`, 00:01:44Z
to 00:03:20Z); a research task that wrote a Markdown document to the
app's `scratch/` (00:10:29Z) and started a background task; and a task
that set up a scheduled automation (a sidecar,
[section 2](#2-per-user-storage)) named
`weekly-microsoft-security-bulletins` (`sidecar.json` 00:17:41Z to
00:20:16Z). The Google Docs plugin `gdocs` 0.0.6 was installed from the
marketplace between 00:05:45Z and 00:08:51Z, when its `token.json` was
written. As on macOS and Linux no listing was taken between tasks, so the
mapping from task to file is by modification time only: the four
conversation databases under `~/.gemini/antigravity/conversations/` are
00:03:54Z (622,592 B, 20 steps), 00:06:55Z (589,824 B, 10 steps),
00:13:30Z (1,441,792 B, 46 steps) and 00:20:53Z (6,258,688 B, 46 steps),
all `trajectory_meta.source` 1 and none with a `-wal` or `-shm` sidecar
when listed; the project file `~/.gemini/config/projects/<uuid>.json` is
23:59:53Z. The surveys were taken after everything (00:29Z) and again
after the collection (00:45Z); the second showed no new file, only the
size refreshes described below. The app wrote `~/.gemini/antigravity/`,
files in `~/.gemini/config/`, the Electron user-data directory
`%APPDATA%\Antigravity\` with its `logs\`, and an empty
`%LOCALAPPDATA%\antigravity\staging\` (23:56:15Z, before the CLI's first
run). It created no `~/.gemini/antigravity-ide`,
`~/.gemini/antigravity-backup`, `~/.antigravity`, `~/.config`, `~/.cache`
or `~/.antigravity-server` under the profile, and no
`%APPDATA%\Antigravity IDE`.

Collector 1.12.0 under Windows PowerShell 5.1 (`collection.json`
`platform`: `Windows 10.0.26300.0 ARM64 PowerShell 5.1.26100.9549`), run
as administrator in live mode with `-Quiet` from 2026-10-15T00:34:27Z to
00:34:30Z, while the app and its language server were running, found 1
user (the three service profiles were scanned and empty) and 2 projects,
and wrote 213 `collected` rows (14,339,425 B by the manifest), 12
`skipped_excluded`, 5 `error_copy` and no `skipped_size`,
`skipped_secret`, `symlink` or `error_read` row; `tar.exe` wrote the
archive (2,248,759 B). The excluded rows, with their sizes, are in
[section 4](#4-exclude); the only `secret: true` row was the plugin's
`token.json`. The five `error_copy` rows were files the running app
held: the last conversation's `.gemini\antigravity\presence\<uuid>.lock`
(`The process cannot access the file because another process has locked a portion of the file.`),
the `LOCK` files of `Local Storage\leveldb` and `Session Storage` (the
same message), and `Network\Cookies` (20,480 B) and
`Network\Cookies-journal` (`... because it is being used by another process.`).
The three lock files are empty, so only their rows were lost; the cookie
store is the one real loss, as on a live Claude Desktop host
([locked files in `collectors/docs/windows.md`](../docs/windows.md#locked-files-and-long-paths)).
Collected unflagged with credential-like names were only `Trust Tokens`
and its journal ([section 3](#3-credentials)). The manifest `size` was
stale for files the app held open (issue 111): `logs\language_server.log`
0 against 218,747 B staged and archived, `DIPS-wal` 32 against 210,152,
and the two `000003.log` files of the LevelDB stores (LevelDB is the
key-value store format Chromium uses for web storage) 30 against 49 and
68 B. A
`Get-ChildItem` listing before the run showed the same numbers and one
after it the real ones: NTFS, the Windows file system, updates the length
in a file's directory entry only when a handle on the file closes or the
file is reopened, so the length read before the copy was stale and the
collector's own open refreshed it. The `sha256` covered the real bytes.
From 1.12.0 the PowerShell collector records the copied byte count for a
`collected` row. `cli.log` and the log file it is hard-linked to were
collected as two regular files with the same bytes, since the PowerShell
collector has no hard-link handling. The two projects were `<home>\demo`,
from the project file's `folderUri`, and `C:\users\<user>\demo2`, from
`history.jsonl` `workspace`.

The sh collector 1.12.0 in image mode over the archive's `fs/C` tree
(bash 3.2 on macOS), with the empty `demo` directory recreated because
the archive does not hold it (the project had no project-level
artifact), recorded the real sizes (14,768,349 B for the same 213 files),
discovered `demo` from the percent-encoded `file:///c%3A/...` URI (the
issue 91 fix) and, as documented, not `demo2`, whose only references are
Windows paths ([section 6](#6-where-the-workspace-path-is-recorded)).

## 2. Per-user storage

Everything the CLI and the app keep per user sits under `~/.gemini/`; the
Go binary resolves it via `os.UserHomeDir` (binary) so Windows is
`%USERPROFILE%\.gemini` (community: Devilaiger, discuss 167445 quote
`%USERPROFILE%\.gemini\antigravity-cli\brain`). The app's main process
builds the same path from Node's `os.homedir()` (bundle, below).
`os.UserConfigDir`/`os.UserCacheDir`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`,
`APPDATA`, `LOCALAPPDATA` also appear (binary), consistent with the
`~/.cache/antigravity/staging` dir (live, observed; empty) used as the
plugin "marketplace cache ... staging directories" (str changelog). On
Windows the same directory is `%LOCALAPPDATA%\antigravity\staging`
(observed, Windows 11 ARM64 build 26300, 2026-10-14; empty), since Go's
`os.UserCacheDir()` is `%LOCALAPPDATA%` there; the desktop app 2.23.1
created it during its first launch, before the CLI's first run. From
collector 1.12.0 `antigravity|AppData/Local/antigravity` collects it.
Windows CLI install dir is `%LOCALAPPDATA%\agy\bin` (docs/cli/install;
observed with CLI 1.3.5).

**Windows install metadata** (observed, Windows 11 ARM64 build 26300,
2026-10-14): the app's program directory
`%LOCALAPPDATA%\Programs\antigravity\`, its installer in
`%LOCALAPPDATA%\antigravity-updater\`, the Start Menu shortcut and the
`HKCU` uninstall entry ([section 1](#1-source-and-evidence-level)) are
binaries and install metadata, not state, and have no catalog line. The
catalog line `AppData/Local/antigravity` names a whole path component, so
it matches neither `antigravity-updater` nor `Programs\antigravity`.

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

On Windows (observed, app 2.23.1, Windows 11 ARM64 build 26300,
2026-10-14) the layout is the same, with these differences:

- `bin/` holds `agentapi.bat` (107 B), `webm_encoder.exe` (12,472,320 B)
  and `gdocs.cmd` (128 B), a `.cmd` launcher where macOS and Linux have
  the `bin/gdocs` symlink.
- No `sidecar_data/` (see the sidecar bullet under `~/.gemini/config/`
  below) and no `lib/`.
- `conversations/<uuid>.db` x4 (589,824 to 6,258,688 B) and
  `conversation_summaries.db` (159,744 B), none with a `-wal` or `-shm`
  sidecar when listed.
- In the research task's conversation,
  `brain/<uuid>/.system_generated/messages/` holds `<uuid>.json` x2
  (1,400 and 2,010 B), `read.json` (89 B, an object of two message UUIDs
  to booleans) and an empty `undelivered/` directory, not seen on another
  install; `tasks/task-7.log` (988 B) sits beside it.
- One `transcript_full.jsonl` (163,340 B) is also split into
  `chunks/transcript_full/00000000.jsonl` (102,400 B) and
  `00000001.jsonl` (60,940 B): the chunks are cut at 102,400 B (a
  macOS conversation had two chunks too, with sizes not recorded). The four conversations'
  `transcript.jsonl` and `transcript_full.jsonl` are 12,720 and 12,357 B,
  17,119 and 17,053 B, 56,481 and 163,340 B, and 55,052 and 63,094 B.
- In the automation task's conversation, `steps/26/content.md` is
  2,682,163 B beside a 336 B `output.txt`, against the 24,820 B
  `content.md` on Linux.
- Other sizes: `agyhub_summaries_proto.pb` 1,417 B,
  `annotations/<uuid>.pbtxt` x4 93 to 96 B, `antigravity_state.pbtxt`
  812 B, `builtin/.checksum` 72 B, `installation_id` 36 B,
  `scratch/<name>.md` 23,305 B, `plugin_data/gdocs/token.json` 1,122 B,
  `plugin_data/gdocs/bin/` 31,200,920 B,
  `cache/marketplaces/antigravity-plugins-official/` 207,829 B
  (`marketplace.json` 17,664 B, `meta.json` 48 B and
  `plugins/gdocs/0.0.6/`), and `crashes/crash_<pid>_<uuid>.log` and
  `presence/<uuid>.lock` x4 at 0 B.

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

Observed on Windows (CLI 1.3.5, Windows 11 ARM64 build 26300,
2026-10-14), against 1.3.4 on Linux:

- `cache/conversation_metadata.json` (2,671 B), new: `conversations`
  {`<uuid>` x4: {`is_internal` (bool), `last_modified_time` (ISO 8601
  date), `summary` {`AgentName` (empty string), `AppDataDir` (11
  characters), `GroupID` (empty string), `ID` (UUID), `Internal` (bool),
  `Loaded` (bool), `NumSteps` (number), `Preview` (string), `ProjectID`
  (18 characters), `Title` (string), `UpdatedAt` (ISO 8601 date),
  `WorkspaceURIs` (null)}}}. The four entries are the desktop app's four
  conversations; an 11-character `AppDataDir` is `antigravity`, the
  app's data directory.
- `conversation_summaries.db` (40,960 B, no sidecars) holds five rows:
  the CLI's own conversation and one for each of the app's four, with
  `app_data_dir` `antigravity`. `cli.log` has one line from
  `reconcile_summaries.go` and one from `project_uris_migration.go`. So
  CLI 1.3.5 copies the app's conversation index into its own; the
  analyzer yields a summary row per app conversation from each database
  ([section 4 of `analyzer/research/antigravity.md`](../../analyzer/research/antigravity.md#4-summaries-database)).
  This was not seen on macOS (CLI 1.2.16) or Linux (1.3.4); whether it is
  new in 1.3.5 or needs the app to have run first is not determined.
- `cli.log` (41,122 B) is an NTFS hard link to
  `log/cli-20261014_202229.log`, not a symlink: `fsutil hardlink list`
  (`fsutil` is the Windows file-system utility) names both paths. A
  collection holds the bytes twice ([section 1](#1-source-and-evidence-level)).
- `updater/update.lock` (0 B) and `updater/update_status.json` (59 B;
  `message` string, `success` bool).
- `plugin_data/gdocs/`, an empty directory; the plugin's `token.json` is
  in the app's directory.
- `history.jsonl` (230 B) has one line with `display`, `timestamp` and
  `workspace` and no `conversationId`.
- `settings.json` (172 B): `permissions` {`allow`, one string} and
  `trustedWorkspaces` (one absolute Windows path).
- Other files: `annotations/<uuid>.pbtxt` (46 B), `bin/agentapi.bat`
  (68 B), `bin/webm_encoder.exe` (12,472,320 B),
  `cache/default_project_id.txt` (19 B), `cache/last_conversations.json`
  (70 B, one absolute path to a UUID), `cache/marketplaces/` (17,712 B),
  `cache/onboarding.json` (111 B; `consumerOnboardingComplete`,
  `enterpriseOnboardingComplete`, `onboardingComplete`, booleans),
  `implicit/<uuid>.pb` (226 B), `installation_id` (36 B),
  `jetbox_summaries_proto.pb` (430 B), `jetski_state.pbtxt` (503 B),
  `last_check.timestamp` (0 B), `presence/<uuid>.lock` (0 B), an empty
  `crashes/`, and the same `builtin/` skills. There is no
  `antigravity-oauth-token` ([section 3](#3-credentials)).

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
  one entry per scheduled automation. On Windows (3,332 B, app 2.23.1) it
  has `plugins` as on macOS and `userSettings` {`globalPermissionGrants`
  {`allow`, an array of 14 strings}, `remoteControlHostname`}: no
  `sidecars` key although an automation was saved, and neither
  `permissionGrantsV2Migrated` nor `sandboxEnabledAtV2Migration`.
- `plugins/gdocs/`: the installed plugin, `plugin.json`, `README.md`,
  `skills/gdocs/SKILL.md`, nine reference documents and the launcher
  scripts `skills/gdocs/scripts/gdocs` (shell) and `gdocs.cmd`. On
  Windows: `plugin.json` 429 B, `README.md` 154 B, `SKILL.md` 41,701 B,
  `scripts/gdocs` 2,102 B and `scripts/gdocs.cmd` 1,756 B.
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
  `config.json` `sidecars` entry has a `projectId`). On Windows (243 B,
  app 2.23.1) the project file has `id`, `isWorkspaceOnly`, `name`,
  `projectResources` and an empty `settings`, with no `permissionGrants`,
  and its `folderUri` is `file:///c%3A/Users/<user>/demo`: a lower-case
  drive letter and a percent-encoded colon. `default-cli-project.json`
  (84 B) is as on macOS, and there is no folder-less automation project.
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
  On Windows (app 2.23.1) `sidecars/weekly-microsoft-security-bulletins/sidecar.json`
  (1,005 B) has the same keys, with `access_grants` an array of 3
  strings, but 25 minutes after it was saved there was no
  `~/.gemini/antigravity/sidecar_data/` and no `sidecars` entry in
  `config.json`, both of which the Linux install had within a minute.
  The language server logged it (glog lines, digits and names redacted):
  `manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] is enabled`
  (three times), the same migration `starting`,
  `completed successfully in NN.NNNNms` and twice
  `already has status MIGRATION_STATUS_...`;
  `manager.go:NN] Migration [MIGRATION_ID_SIDECAR_USER_CONFIG_BYPASS] is disabled, skipping entirely`
  (three times); one
  `sidecar_manager.go:NNN] Config changed for sidecar <name>, updating...`
  and one `sidecar_sdk.go:NN] Using bundled agy-node`. Whether the
  sidecar ever started on Windows, and where its log would go, is not
  determined.
- `mcp_config.json` and `.migrated`, both empty (also on Windows).
- `node_modules/sidecar_sdk/` (observed, Linux, 5 files, 17,508 B): a copy
  of the sidecar SDK, excluded from 1.12.0. Absent on Windows.

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
`%APPDATA%\Antigravity` (observed on Windows 11 ARM64 build 26300, app
2.23.1, 2026-10-14). The app stores UI state there
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

Observed on Windows (`%APPDATA%\Antigravity\`, created 23:56:11Z, app
2.23.1, Windows 11 ARM64 build 26300, 2026-10-14): `app_storage.json`
(1,545 B; the macOS key set, without the two Linux additions),
`bin\agy-node.cmd` (107 B, the Windows name the bundle predicts),
`.updaterId` (36 B), `DevToolsActivePort` (60 B), `Preferences` (132 B;
`electron.media.device_id_salt`, `spellcheck.dictionaries` (one string),
`spellcheck.dictionary`), `Local State` (490 B; `os_crypt`
{`audit_enabled` (bool), `encrypted_key` (a 380-character string)} and
`uninstall_metrics` {`installation_date2`}, see
[section 3](#3-credentials)), `logs\main.log` (4,751 B, 51 lines) and
`logs\language_server.log` (218,747 B), `Network\Cookies` (20,480 B) and
`Cookies-journal`, `Network Persistent State` (472 B),
`NetworkDataMigrated` (0 B), `Network\Trust Tokens` (36,864 B)
and its `-journal`, `DIPS` (4,096 B) and `DIPS-wal` (210,152 B),
`declarative_performance_observer.db` (32,768 B) and its `-journal`,
`Local Storage\leveldb\` (`000003.log` 49 B, `CURRENT`, `LOCK`, `LOG`
251 B, `MANIFEST-000001`), `Session Storage\` (`000003.log` 68 B and the
other LevelDB files), `lockfile` (0 B, the Windows form of the
`Singleton*` symlinks, which do not exist here), and the caches
`Cache\Cache_Data` and `Cache\No_Vary_Search` (9,368,215 B in all),
`Code Cache` (22,862 B), `DawnGraphiteCache`, `DawnWebGPUCache` and
`GPUCache` (557,424 B each), `Shared Dictionary` (45,128 B) and an empty
`blob_storage\<uuid>\`. There is no `Crashpad\`, no `Dictionaries\`, no
`CachedData` and no `User\`.
`%APPDATA%\antigravity` (lower case) is the same directory, as expected
on a case-insensitive filesystem, and there is no
`%APPDATA%\Antigravity IDE`.

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
(observed on Linux) and `%APPDATA%\Antigravity\logs` (observed on
Windows 11 ARM64 build 26300, app 2.23.1, 2026-10-14). Observed on macOS: `main.log` (1,696 B; lines
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
Observed on Windows: `main.log` (51 lines) has the
`Starting app (v2.23.1) with dynamic port…` line and, beyond the
templates above (digits and ids redacted):
`Generated new staging user ID: <uuid>`,
`Host bridge server listening on http://127.0.0.1:<port>`,
`[Auto-Restart] Port changed! Reloading all windows with URL: https://127.0.0.1:<port>/`,
`Local: https://127.0.0.1:<port>/`,
`LS Logs: <home>\AppData\Roaming\Antigravity\logs\language_server.log`,
`Electron Logs: <home>\AppData\Roaming\Antigravity\logs\main.log`,
`[IDE Wizard] <home>\.gemini\antigravity not found — user was not migrated, skipping.`,
`Update for version 2.23.1 is not available (latest version: 2.23.1, downgrade is allowed).`,
`[AutoUpdater] Up to date (2.23.1)`, and three WSL errors (see
**WSL** below). The sidecar lines of `language_server.log` are under
`~/.gemini/config/` above.

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
where that server keeps conversations is not determined. The Windows
install (app 2.23.1, Windows 11 ARM64 build 26300, 2026-10-14, no WSL
distribution installed) shows the app listing WSL distributions at
start-up and for a "connect" menu: `main.log` has twice
`[error] Failed to list WSL distros: Error: wsl.exe --list --verbose failed: Command failed: C:\WINDOWS\System32\wsl.exe --list --verbose`
with the OS text "The Windows Subsystem for Linux is not installed. You
can install by running 'wsl.exe --install'", from `dist\wsl.js`
(`execWsl`, `listWslDistros`), and once `[error] wsl:get-state failed: ...`
from `dist\menu.js` (`addWslConnectMenu`, `wslConnectMenuTemplate`) and
`dist\ipcHandlers.js`. The directory inside a distribution remains
unobserved.

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
- On Windows the keyring is the Windows Credential Manager (observed, CLI
  1.3.5, Windows 11 ARM64 build 26300, 2026-10-14). `cli.log` has
  `auth.go:NNN] ChainedAuth: authenticated via keyring (effective: keyring)`
  and `keyring.go:NN] keyringAuth: loaded token, expiry=<date> expired=false`,
  and no `Using file-based secret storage` line; there is no
  `antigravity-oauth-token` file and no `plugin-secrets.json` anywhere
  under the profile (searched by name). The binary carries the `wincred`
  and `CredWrite` literals, the Go keyring's Windows backend and the
  Windows API call that writes a credential. `cmdkey /list` (the Windows
  command that lists Credential Manager entries), run from an SSH (remote
  shell) session, which is a different logon session, listed no entries, so the
  entry's name is not determined.
- `plugin_data/<plugin>/token.json` under a `.gemini` data directory:
  the Google Docs plugin's OAuth credential (observed,
  `~/.gemini/antigravity/plugin_data/gdocs/token.json`, 1,119 B, mode
  0600), keys `client_id`, `client_secret`, `email`, `scopes` (an array of 8 URLs),
  `token` {`access_token`, `expiry`, `refresh_token`, `token_type`} and
  `updated_at`. Collector 1.11.0 collected it unflagged (issue 84); from
  1.12.0 `*.gemini/antigravity*/plugin_data/*/token.json` flags it in
  every `.gemini/antigravity*` directory. On Windows (1,122 B, app
  2.23.1) collector 1.12.0 flagged it `secret: true`, the only such row.
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
  `os.UserConfigDir()`, not observed; the Windows install of CLI 1.3.5
  used the Credential Manager and wrote no such file, though its binary
  carries the literal. On those case-insensitive
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
  macOS install, 20,480 B on Linux and Windows, where it is
  `Network\Cookies`), `Trust Tokens` (Chromium's store for
  the Private State Tokens web API, 36,864 B on Linux and Windows) with their
  `-journal` files, and `Local Storage/leveldb/` (16 KB on macOS, 628 B on
  Linux, contents not read) are collected unflagged; whether any of them
  can hold a credential is not determined. On a live Windows host the
  running app holds `Network\Cookies` and its journal, so they get
  `error_copy` rows ([section 1](#1-source-and-evidence-level)).
- `Local State` on Windows (490 B) has `os_crypt.encrypted_key`, a
  380-character string: Chromium's key for the cookie store, wrapped with
  DPAPI (the Windows Data Protection API, the per-user encryption the OS
  provides). macOS keeps that key in the Keychain and Linux in the
  Secret Service, so `Local State` holds key material on Windows only
  (the Linux file is 57 B with only `uninstall_metrics`). It
  is collected unflagged: the rest of the file is install metadata, and
  the key is useless without the user's DPAPI context. Treat
  `encrypted_key` as a key to redact before sharing, as
  [section 3 of `collectors/research/claude-desktop.md`](claude-desktop.md#3-credentials)
  treats Claude Desktop's `metadata_secret`, not as a secret glob. `app_storage.json` holds the signed-in account
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
  recorded them; on the Windows install of CLI 1.3.5 and app 2.23.1,
  12,472,388 B and 12,472,555 B). One line per directory rather
  than `.gemini/antigravity*/bin`, because `*` in an exclusion crosses
  `/` and that form would also prune any `bin` directory the agent writes
  under `brain/<uuid>/`.
- `.gemini/antigravity*/plugin_data/*/bin`: plugin binaries (the Google
  Docs plugin's, 31,938,752 B; 36,327,424 B on Linux; 31,200,920 B on
  Windows). The plugin's
  `token.json` beside it stays collected.
- `.gemini/antigravity*/cache/marketplaces`: the plugin marketplace cache
  (16 files, 207,829 B; on Linux 282,624 B in the app's directory and
  32,768 B in the CLI's, which has one from 1.3.x; on Windows 207,829 B
  and 17,712 B), a copy of the
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
  `crashes` or `bin`. On Windows (observed, app 2.23.1) the set is
  `Cache` 9,368,215 B, `Code Cache` 22,862 B, `DawnGraphiteCache`,
  `DawnWebGPUCache` and `GPUCache` 557,424 B each, `Shared Dictionary`
  45,128 B and `blob_storage` 0 B, all `skipped_excluded`; there is no
  `Crashpad`, `Dictionaries` or `CachedData`.
- `AppData/Local/agy` (CLI install; `bin\agy.exe` 184,062,616 B on
  Windows) and `.antigravity/extensions`. `.cache/antigravity` (the
  marketplace staging directory) and, from 1.12.0, its Windows form
  `AppData/Local/antigravity` are collected; they were empty on every
  install checked.
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
  On Windows it is the folder as the user typed it, with a lower-case
  `users` (`C:\users\<user>\demo2`, observed, CLI 1.3.5). The PowerShell
  collector compares project paths without regard to case
  (`Select-UniqueProjects`), so two spellings of one folder would not be
  collected twice; on that install they were two folders.
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
- On Windows `trustedWorkspaces`, the `history.jsonl` `workspace` and the
  `last_conversations.json` keys are Windows paths (`C:\...`). The sh
  collector keeps only `/`-rooted paths and `file://` URIs
  ([which paths are used in `collectors/docs/coverage.md`](../docs/coverage.md#which-paths-are-used)),
  so in image mode over a Windows collection it discovers a project
  only from a `folderUri`: it found the app's `demo` and not the CLI's
  `demo2` (observed, [section 1](#1-source-and-evidence-level)).
- The analyzer carried the two Windows project folders under three
  `project_path` spellings: `c:/Users/<user>/demo` (from the
  percent-encoded `folderUri`), `C:/users/<user>/demo2` and
  `C:\users\<user>\demo2`; folding them is
  [doubleagent issue 112](https://github.com/seanthegeek/doubleagent/issues/112).
- `conversation_summaries.db` (`workspace_uris` column) and the
  per-conversation `*.db`: SQLite only, read by the analyzer.

## 7. Confidence

High: the CLI layout (live, observed and binary literals); the desktop
app's data directory `~/.gemini/antigravity` and its contents (bundle and
observed); the Electron user-data directory name `Antigravity` and the
macOS logs directory (bundle and observed); the Linux Electron
user-data directory `~/.config/Antigravity` and its `logs/` (bundle and
observed, app 2.23.1); the Windows Electron user-data directory
`%APPDATA%\Antigravity` and its `logs\`, and the Windows staging
directory `%LOCALAPPDATA%\antigravity\staging` (observed, app 2.23.1 and
CLI 1.3.5, Windows 11 ARM64 build 26300, 2026-10-14); the Credential
Manager as the CLI's keyring on Windows (observed log lines); the roles of
`antigravity-ide` and `antigravity-backup` (bundle); the plugin token's
location and keys (observed); the keyring service and file fallback;
`~/.gemini/config` contents, including `projects/<uuid>.json` and
`sidecars/<name>/sidecar.json` (observed); the CLI's log line naming
`~/.config/antigravity/plugin-secrets.json` on Linux (observed). Medium:
the macOS and
Windows paths of `plugin-secrets.json` (inferred from Go's
`os.UserConfigDir()`, not observed; the Windows install used the
Credential Manager instead) and its contents (never observed); `antigravity-ide/conversations` and
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
semantics; whether `~/.antigravity` is still written by any build;
whether the scheduled automation's sidecar ever started on Windows, and
where its log would go there (no `sidecar_data/` appeared); the name of
the CLI's Credential Manager entry on Windows; whether CLI 1.3.5 copies
the app's conversation summaries on every platform, or only once the
app has run.
