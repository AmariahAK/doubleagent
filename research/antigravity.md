# antigravity

Google Antigravity is three products under one catalog agent. The **CLI**, `agy`,
is a single Go binary. The **desktop app** (version 2.x, since 2.0) is an
Electron app, a desktop program built on Chromium and Node.js, whose bundle
calls the product "AGY Hub" (its internal name for the agent-first app, and
the `--subclient_type hub` argument it passes to its backend, below); it
describes itself to the user as "redesigned to put agents first". The
**IDE**, the VS Code fork that carried the Antigravity name before 2.0, is now
a separate download named "Antigravity IDE". The CLI and the desktop app run
the same Go backend, which the app calls the language server: it ships it as
`language_server`, the name it gives the process that serves its agent
conversations (the program that owns the conversation stores and runs the
agent), and starts it in standalone mode. Both write the same
SQLite-of-protobuf conversation databases, each into its own data directory
under `~/.gemini/`. The app runs a scheduled task (an automation) as a
sidecar, a long-running helper process the language server supervises. The
CLI and desktop app transcripts are parsed by the `antigravity` parser
([section 13](#13-parser-plan)).

## 1. Source and evidence

Closed source; no public source exists. Evidence levels, tagged per claim:

- **binary**: `~/.local/bin/agy` on the author's WSL (Windows Subsystem for
  Linux) workstation, the Google Antigravity CLI installed 2026-10-03, ELF
  x86-64 (the Linux executable format), 209,625,296 bytes (about 200 MB),
  sha256 `a759ce7c7a235d9b...`, `strings -n 8` saved to
  `scratchpad/agy_strings.txt` (552,251 lines). The embedded changelog's
  newest heading is `## 1.2.15` (`agy_strings.txt:310457`; oldest `## 1.0.0`
  at 311213). Cited as `str:<line>` or by quoted literal. It embeds 1300
  `.proto` descriptors; the relevant packages are `gemini_coder`
  (`third_party/gemini_coder/proto/trajectory.proto`), `exa.cortex_pb`
  (`third_party/jetski/cortex_pb/cortex.proto`), `exa.codeium_common_pb` and
  `exa.jetski_cortex_pb`. The `jetski`, `cascade` and `codeium` names show the
  lineage from Windsurf's Cascade agent. The parser's tables were built from
  these descriptors.
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
  [marioalbu08/antigravity-sync](https://github.com/marioalbu08/antigravity-sync),
  [SavFil/antigravity-convo-manager](https://github.com/SavFil/antigravity-convo-manager),
  [damadorPL/agent-memories](https://github.com/damadorPL/agent-memories) (google/antigravity.md),
  discuss.ai.google.dev thread 167445.

The transcript schema rests on the shipped binaries (protobuf descriptors
extracted from `agy` and from the app's `language_server`), confirmed against
a real install on the author's WSL workstation (CLI), on the author's Mac
(CLI and desktop app), in the author's Ubuntu lab VM (CLI and desktop app)
and in the author's Windows 11 lab VM (CLI and desktop app), October 2026.
Extraction:
`tools/proto_descriptors.py extract ~/.local/bin/agy descriptors.json`, then
`show` on the names below.

### Observed

- **macOS, CLI 1.3.6**: a second look on 2026-10-15 with CLI 1.3.6
  (`/Users/sean/.local/bin/agy`, 183,407,440 bytes, sha256
  `827ba22b4aa33557614a57aac2cc13f386e17db6b802febd3932226906ac05ab`): one
  conversation of 17 steps in a project directory the agent was then told to
  delete, which left the conversation database, its `brain/<uuid>/` mirror
  (16 `transcript_full.jsonl` lines), the `history.jsonl` lines and the
  summaries row in place, so the whole session parsed after the directory
  was gone; its four `history.jsonl` lines showed which ones carry
  `conversationId` ([section 9](#9-joins-and-timestamps)).

- **Windows, CLI** (issues 83, 89, 90): `agy` 1.3.5 (`agy --version`) at
  `%LOCALAPPDATA%\agy\bin\agy.exe`, on `PATH`, 184,062,616 B, sha256
  `223953a7d64ad199bbeaae3cf84d634b0ec3917979c7a60feac6ade05d50888b`,
  installed 2026-10-14T23:56:21Z in the author's Parallels lab VM, Windows
  11 ARM64 build 26300 (`ver` reports `10.0.26300.9550`; ARM64 is the 64-bit
  Arm architecture), and observed the same evening (US Eastern daylight
  time; the UTC times below cross into 2026-10-15), read for file names,
  sizes, key names, value types and log lines with ids redacted only.
  `%LOCALAPPDATA%` below is the per-user `AppData\Local` folder and
  `%APPDATA%` the per-user `AppData\Roaming` folder. The user installed the
  desktop app and the CLI and ran a few turns with each; as on macOS and
  Linux no listing was taken between tasks, so the mapping from task to
  file is by modification time only. The executable's version
  resource (`VersionInfo.ProductVersion`, the version Windows shows in the
  file's properties) is empty. The embedded changelog's newest heading is
  `## 1.3.4`, with `## 1.3.0` to `## 1.3.4` present, and an ASCII search
  over the file finds the literals `plugin-secrets.json`,
  `Using file-based secret storage`, `wincred` and `CredWrite`
  ([section 3](#3-credentials)). No WSL distribution is installed. The CLI
  created `~/.gemini/antigravity-cli/` at its first run, 00:22:29Z (`~` is
  `%USERPROFILE%`, `C:\Users\<user>`, here). The user started it from
  `<home>\demo2`, typed with a lower-case `users`
  (`C:\users\<user>\demo2`), and ran a coding task that wrote one source
  file per language into ten subdirectories and a `README.md` (00:25:07Z to
  00:27:16Z). That left one conversation, `conversations/<uuid>.db`
  (983,040 B, 00:28:12Z, 38 steps, `trajectory_meta.source` 17, no `-wal` or
  `-shm` sidecar when listed). Its `history.jsonl` had one line, without
  `conversationId`. Against 1.3.4 on Linux, the CLI also wrote
  `cache/conversation_metadata.json` and copied the desktop app's
  conversations into its own summaries database, new in 1.3.5 as observed
  here ([section 7](#7-transcript-stores),
  [Summaries database](#summaries-database)); its `cli.log` is a hard link
  rather than a symlink ([section 2](#2-per-user-storage)), and its OAuth
  token went to the Windows Credential Manager, not a file
  ([section 3](#3-credentials)). The descriptors of the 1.3.5 and 2.23.1
  Windows binaries were not extracted in this round.

- **Windows, desktop app** (issues 83, 84, 91): version 2.23.1
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
  `LICENSES.chromium.html`).

  It also made a Start Menu shortcut,
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
  in a project folder `<home>\demo` (`C:\Users\sean\demo`), which wrote six
  files there (a hello world in C, Go, JavaScript, Python and Rust, and a
  `README.md`, 00:01:44Z to 00:03:20Z); a research task that wrote a
  Markdown document to the app's `scratch/` directory (00:10:29Z) and
  started a background task; and a task that set up a scheduled automation
  (a sidecar, [section 2](#2-per-user-storage)) named
  `weekly-microsoft-security-bulletins` (`sidecar.json` 00:17:41Z to
  00:20:16Z). The Google Docs plugin `gdocs` 0.0.6 was installed from the
  marketplace between 00:05:45Z and 00:08:51Z, when its `token.json` was
  written. As on macOS and Linux no listing was taken between tasks, so the
  mapping from task to file is by modification time only: the four
  conversation databases under `~/.gemini/antigravity/conversations/` are
  00:03:54Z (622,592 B), 00:06:55Z (589,824 B), 00:13:30Z (1,441,792 B) and
  00:20:53Z (6,258,688 B), of 20, 10, 46 and 46 steps (the step counts are
  in the analyzer's session order, which was not matched to the file
  sizes), all `trajectory_meta.source` 1, each with a `brain/<uuid>/`
  directory, an `annotations/<uuid>.pbtxt` and a summaries row, and none
  with a `-wal` or `-shm` sidecar when listed (nor had the CLI's); the
  project file `~/.gemini/config/projects/<uuid>.json` is 23:59:53Z. No
  `sidecar_data/` directory appeared for the automation
  ([Sidecar logs](#sidecar-logs)).

  The surveys were taken after everything (00:29Z) and again after the
  collection (00:45Z); the second showed no new file, only the size
  refreshes described below. The app wrote `~/.gemini/antigravity/`, files
  in `~/.gemini/config/`, the Electron user-data directory
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
  [section 4](#4-exclusions); the only `secret: true` row was the plugin's
  `token.json`. The five `error_copy` rows were files the running app
  held: the last conversation's `.gemini\antigravity\presence\<uuid>.lock`
  (`The process cannot access the file because another process has locked a portion of the file.`),
  the `LOCK` files of `Local Storage\leveldb` and `Session Storage` (the
  same message), and `Network\Cookies` (20,480 B) and
  `Network\Cookies-journal` (`... because it is being used by another process.`).
  The three lock files are empty, so only their rows were lost; the cookie
  store is the one real loss, as on a live Claude Desktop host
  ([locked files in
  `collectors/docs/windows.md`](../collectors/docs/windows.md#locked-files-and-long-paths)).
  Collected unflagged with credential-like names were only `Trust Tokens`
  and its journal ([section 3](#3-credentials)).

  The manifest `size` was stale for files the app held open (issue 111):
  `logs\language_server.log` 0 against 218,747 B staged and archived,
  `DIPS-wal` 32 against 210,152, and the two `000003.log` files of the
  LevelDB stores (LevelDB is the key-value store format Chromium uses for
  web storage) 30 against 49 and 68 B. A `Get-ChildItem` listing before the
  run showed the same numbers and one after it the real ones: NTFS, the
  Windows file system, updates the length in a file's directory entry only
  when a handle on the file closes or the file is reopened, so the length
  read before the copy was stale and the collector's own open refreshed it.
  The `sha256` covered the real bytes.

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
  Windows paths ([section 6](#6-where-the-project-path-is-recorded)).

  Analyzer 0.12.0 (at `main` commit
  [`4607cca`](https://github.com/seanthegeek/doubleagent/commit/4607ccaac18f9bcfcb1a01cefc9402939430b09d))
  over the collector 1.12.0 archive of this VM, covering both surfaces
  (PowerShell collector, 213 `collected` files): `detect` verified the
  archive's sha256 and listed the one user with `antigravity`, 213 files
  and 14,339,425 B, and its `detect.json` (a file `timeline` wrote until its
  content moved into
  [`inventory.json`](../analyzer/docs/output.md#inventoryjson) later in
  0.12.0) `problems` list was empty. `timeline --include-thinking` reported
  `antigravity` parsed and nothing detected but not parsed, with 285
  rows (8 `user`, 10 `assistant`, 72 `tool_use`, 72 `tool_result`, 33
  `thinking`, 90 `system`) in 5 sessions. The `system` rows: 50
  `permission grant` (per-step grants, issue 92; three of them for
  PowerShell `Get-ChildItem` commands the agent ran over
  `~/.gemini/config`), 19 `permission setting` (14 from `config.json`
  `userSettings.globalPermissionGrants.allow`, 3 from `sidecar.json`
  `agent_permissions.access_grants` and 2 from the CLI's
  `settings.json`), 5 `model` (one per session, `gemini-3.8-flash-n` in
  every conversation), 5 session starts, 9 `conversation summary`
  ([Summaries database](#summaries-database)) and 2 `system_message` steps
  (both `task_notification` events). Four session starts read
  `source=cascade_client` and `data_dir=antigravity`, one of them with
  the app project's `project_id` and three `outside-of-project`; the
  fifth read `source=cli`, `data_dir=antigravity-cli` and
  `project_id=default-cli-project`. Tool names: `run_command` 36,
  `write_to_file` 21, `view_file` 8, `search_web` 3, `ask_question` 3,
  `read_url_content` 1. The `history.jsonl` row had an empty
  `session_id`, since its line has no `conversationId`, and the
  lower-case `C:\users\sean\demo2` as `project_path`
  ([section 9](#9-joins-and-timestamps)). No row reported an unreadable file
  or a decode failure.

- **Linux, CLI** (issues 83, 89, 90): `agy` 1.3.4 (`agy --version`) at
  `~/.local/bin/agy`, ELF aarch64, 204,492,984 bytes, sha256
  `08d619ae3969c33b9cba5eac2a54f4566cbca1b5de68968167cb908ced5b4824`, in the
  author's Ubuntu lab VM (Ubuntu 26.04.1 LTS, aarch64, Linux
  7.0.0-38-generic), installed 2026-10-13 21:37 local time (EDT, US Eastern
  daylight time) and observed the same day, read for file names, sizes, key
  names, value types, SQLite schemas and enum values only, with `find`,
  `ls`, `analyzer/tools/shape.py` and a read-only schema script, all Python
  run with `python3 -I`. The user installed both products and ran a few
  turns with each; no listing was taken between tasks, so, as on macOS, the
  mapping from task to file is by modification time only. The embedded
  changelog's newest heading is `## 1.3.3`. `~/.local/bin` is not on the
  non-interactive `PATH`. The user ran a few turns, which left one
  conversation (`~/.gemini/antigravity-cli/conversations/<uuid>.db`,
  622,592 B, modified 21:43, 26 steps, `trajectory_meta.source` 17 (`cli`)
  and `trajectory_type` 4) and a project folder the agent wrote files into.
  Against 1.2.x the CLI now also writes `annotations/<uuid>.pbtxt`, as the
  app does ([section 7](#7-transcript-stores)), `cache/marketplaces/`, a
  `conversationId` key in `history.jsonl` (issue 89) and a `permissions` key
  in `settings.json` ([section 2](#2-per-user-storage)), and its log names a
  file secret store it did not create ([section 3](#3-credentials)). The CLI
  left `~/.cache/antigravity/staging/` empty, as on macOS.

- **Linux, desktop app** (issues 83, 91): version 2.23.1
  (`main.log`: `Starting app (v2.23.1) with dynamic port…`), in the same VM,
  first run 2026-10-13 21:29 local time. It was downloaded as
  `~/Downloads/Antigravity.tar.gz` and unpacked by hand to `~/Antigravity/`
  (285 MB), a binary install that gets no catalog line: the Electron binary
  `antigravity` (220,466,568 B, sha256
  `c543041069aa2e478235447cb636f9f09faab15003862029d226bb14b8dc655b`), a
  setuid-root `chrome-sandbox`, the Chromium libraries and resource packs,
  `resources/app.asar` (4,486,221 B, the size of the macOS 2.23.0 asar,
  with a different hash, sha256
  `b8ec3628df2a12ee9deac5dc06367f238065af146bfe6298fdad6db5f9790d9c`),
  `resources/app-update.yml` (keys `provider`, `url`,
  `updaterCacheDirName`), `resources/bin/language_server` (181,358,800 B,
  sha256 `310ee8e0cba4c4ee05504ac8021cbd3544a79c06cc01c790536361625c5fffb3`)
  and `resources/bin/webm_encoder`. It is not an AppImage (a self-contained
  Linux application package): `main.log` warns
  `APPIMAGE env is not defined, current application is not an AppImage`.

  The user ran a few tasks, among them a coding task and a scheduled
  automation, with no listing between tasks, so the mapping from task to
  file is by modification time only, as on macOS: four conversations under
  `~/.gemini/antigravity/conversations/` (655,360 to 1,114,112 B, modified
  21:45, 21:51, 21:55 and 22:00, all `trajectory_meta.source` 1
  (`cascade_client`) and `trajectory_type` 4, of 14, 43, 30 and 38 steps,
  [Conversation database](#conversation-database)), each with a
  `brain/<uuid>/` directory, an `annotations/<uuid>.pbtxt` and a summaries
  row; a project folder `~/demo2/` (21:53 to 21:54) whose project file is
  21:47, the automation's `sidecar.json` (21:58 to 21:59) and its
  `sidecar_data/` (22:00), the Google Docs plugin's token (21:49), and a
  Markdown report the agent wrote at the home root (21:59). The
  automation's scheduler log is the first observed trace of a sidecar's own
  output ([Sidecar logs](#sidecar-logs)), but no scheduled run had fired,
  so what a run writes, and whether it becomes a conversation, is still not
  observed. The app wrote `~/.gemini/antigravity/` (56 MB), files in
  `~/.gemini/config/` (320 KB), and the Electron user-data directory
  `~/.config/Antigravity/` (8.9 MB) with its `logs/` inside it, as the
  bundle says. It created no `~/.config/antigravity` (lower case),
  `~/.antigravity`, `~/.antigravity-server`, `~/.gemini/antigravity-ide` or
  `~/.gemini/antigravity-backup`, no `~/.config/autostart` entry, no user
  systemd unit and no crontab entry for the schedule; `systemctl --user`
  showed only the running app's transient `app-antigravity-<pid>.scope`.
  The user also kept the CLI's project folder inside the install directory,
  `~/Antigravity/demo/`. The descriptors of the 1.3.4 and 2.23.1 binaries
  were not extracted in this round.

  Collector 1.12.0, run in the VM as the user (`-q -u <user>`,
  2026-10-14T02:04Z), collected 233 files (7,002,562 B) with 13
  `skipped_excluded` rows, 4 symlinks, 0 errors and dash as the worker
  shell. The excluded rows were the `cache/marketplaces` and `bin`
  directories of both `.gemini` data directories, the app's
  `plugin_data/gdocs/bin`, and the eight Chromium cache directories of
  `~/.config/Antigravity` ([section 4](#4-exclusions)); the only `secret: true`
  row was the plugin's `token.json`. Collected and unflagged with
  credential-like names were the Electron `Cookies` and `Trust Tokens`
  stores and their `-journal` files ([section 3](#3-credentials)). Three
  low-value directories were collected that the final 1.12.0 tables now
  exclude: `.gemini/antigravity/lib`, `.gemini/config/node_modules` and
  `.config/Antigravity/Dictionaries`. One project was discovered, the CLI's
  `~/Antigravity/demo`; the app's `~/demo2` was missed (issue 91,
  [section 6](#6-where-the-project-path-is-recorded)).

  Analyzer 0.12.0 over the collector 1.12.0 archive of this VM, covering
  both surfaces: the summary line read
  `agents:    parsed: antigravity; detected but not parsed: none`, with
  165 rows (9 `user`, 10 `assistant`, 67 `tool_use`, 67 `tool_result`,
  12 `system`) in 5 sessions, four with `source=cascade_client` and
  `data_dir=antigravity` and one with `source=cli` and
  `data_dir=antigravity-cli`. The `system` rows were the 5 session
  starts, the 5 conversation summaries and 2 `system_message` steps
  (both `task_notification` events); no row reported a decode failure.
  The two `history.jsonl` rows had `project_path` set and `session_id`
  empty, because analyzer 0.12.0 as run did not read `conversationId`;
  the parser reads it since (issue 89).

- **macOS, CLI** (issue 83): `agy` at `~/.local/bin/agy`, Mach-O 64-bit
  arm64 (the macOS executable format), 175,966,448 bytes, sha256
  `7dca095cfc1df2c057a385ed88a76c7ba98dc103258a80be87a8f42e484cb3aa`,
  installed 2026-10-04 on the author's Mac (macOS 26.4, Darwin 25.4.0, Apple
  silicon, arm64), observed 2026-10-13, read for file names, sizes, key
  names, value types and SQLite schemas only, with
  `analyzer/tools/shape.py`. `agy --version` prints `1.2.16`; the
  embedded changelog's newest heading is still `## 1.2.15`. Two
  conversations were on disk in `~/.gemini/antigravity-cli/conversations/`,
  each a `conversations/<uuid>.db` with `trajectory_meta.source` 17
  (`cli`, `CORTEX_TRAJECTORY_SOURCE_CLI` in the descriptor
  `exa.cortex_pb.CortexTrajectorySource`) and `trajectory_type` 4, of 12 and
  8 steps, with the `brain/<uuid>/` logs described in
  [section 2](#2-per-user-storage). The CLI left
  `~/.cache/antigravity/staging/` empty.

- **macOS, desktop app** (issue 83): `/Applications/Antigravity.app`,
  `CFBundleShortVersionString` and `CFBundleVersion` both `2.23.0`, Electron
  (`Contents/Frameworks/Electron`, 200,443,040 bytes), on the same Mac,
  first launched 2026-10-13 18:28 local time and observed the same day.
  `Contents/Resources/app.asar` is 4,486,221 bytes, sha256
  `4e99093662d797ecba823e92823d352413e3bf2ca721257df4a255c045df1598`. Its
  backend is `Contents/Resources/bin/language_server` (Mach-O arm64,
  155,290,912 bytes, sha256
  `c1dd0c9940f712adf2185e756470752d5f5afee15441e32879e4a0f127e18273`),
  beside `Contents/Resources/bin/webm_encoder`. The app passes the language
  server `--subclient_type hub`, `--standalone` and `--app_data_dir` with
  the data-directory name (`app.asar:dist/languageServer.js@4241987`
  `'--subclient_type',` `'hub',`; `@4242293` `'--app_data_dir',`
  `(0, paths_1.getAppDataDirName)(),`), and the name is the app name
  lower-cased without spaces, `antigravity`
  (`app.asar:dist/paths.js@4312548`
  `return electron_1.app.getName().toLowerCase().replace(/\s+/g, '');`),
  under `~/.gemini` on every OS (`app.asar:dist/paths.js@4312621`
  `path_1.default.join(os_1.default.homedir(), '.gemini', getAppDataDirName())`).

  The user ran, in this order, a plain question-and-answer chat with no
  tool use, a coding task, an automation (a scheduled task; the app runs it
  as a sidecar, [section 2](#2-per-user-storage), enabled with
  `--enable_sidecars`, `app.asar:dist/languageServer.js@4242552`) and the
  Google Docs plugin ("gdocs", installed from the official plugin
  marketplace). The directory listings were taken after all four, so which
  conversation belongs to which task is not known, and the order below is
  by modification time only: the four conversation databases under
  `~/.gemini/antigravity/conversations/`, all `trajectory_meta.source` 1
  (`CORTEX_TRAJECTORY_SOURCE_CASCADE_CLIENT`, `cascade_client`) and
  `trajectory_type` 4, are 12 steps (modified 18:37), 24 steps (18:43), 43
  steps (18:50) and 31 steps (19:14), each with a `brain/<uuid>/` directory,
  an `annotations/<uuid>.pbtxt` and a row in `conversation_summaries.db`
  ([section 7](#7-transcript-stores)); the automation's `sidecar.json` is
  18:41 to 18:42, the plugin's `token.json` 18:46 and the agent's scratch
  document 18:47; any mapping beyond those times waits for a round that
  lists after each task. Where a scheduled run of the automation writes its
  transcript was not observed, because no run had fired. The app wrote
  `~/.gemini/antigravity/` (49 MB), files in the shared `~/.gemini/config/`,
  the Electron user-data directory
  `~/Library/Application Support/Antigravity/` (5.3 MB) and
  `~/Library/Logs/Antigravity/`; it created no `~/.gemini/antigravity-ide`,
  `~/.gemini/antigravity-backup` or `~/.antigravity`, nothing under
  `~/Library/Caches`, and no LaunchAgent, launchd job or cron entry
  (`~/Library/LaunchAgents` has none). Collector 1.11.0 collected the
  `.gemini` directories but none of the Electron directories, since the
  catalog then named only the pre-2.0 `User` and `logs` subdirectories,
  which this build does not create.

### Source reviews

None.

## Collection

### 2. Per-user storage

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

#### Scratch directories

The desktop app's `~/.gemini/antigravity/scratch/<name>.md` holds a Markdown
document the agent wrote during a conversation, user-level, not per
conversation ([desktop app data directory](#desktop-app-data-directory));
each `brain/<uuid>/scratch/` was an empty directory on every install
([brain directories](#brain-directories)). Both are collected
([section 4](#4-exclusions)).

#### Windows install metadata

Install metadata (observed, Windows 11 ARM64 build 26300, 2026-10-14): the
app's program directory `%LOCALAPPDATA%\Programs\antigravity\`, its
installer in `%LOCALAPPDATA%\antigravity-updater\`, the Start Menu shortcut
and the `HKCU` uninstall entry ([section 1](#1-source-and-evidence)) are
binaries and install metadata, not state, and have no catalog line. The
catalog line `AppData/Local/antigravity` names a whole path component, so it
matches neither `antigravity-updater` nor `Programs\antigravity`.

#### Data directories under `~/.gemini`

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
  Before 2.0 the IDE used the same directory, `app.asar:dist/paths.js@4313608`,
  commented "User data dir for the old IDE (source for copy)":

  ```text
  exports.IDE_OLD_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity');
  ```

- `~/.gemini/antigravity-cli/` is the CLI's (binary, live, observed on
  macOS and Linux).
- `~/.gemini/antigravity-ide/` is the separately installed IDE's,
  `app.asar:dist/paths.js@4313784` ("User data dir for the separately
  installed IDE (destination for copy)"):

  ```text
  exports.IDE_NEW_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity-ide');
  ```

  The app's IDE install wizard copies pre-2.0 IDE data there when
  `antigravity-ide` does not exist and `antigravity` does
  (`app.asar:dist/ideInstall/constants.js@4160197`, `exports.WIZARD_SHOWN_KEY`
  and the comment "2. `~/.gemini/antigravity-ide` does NOT exist 3.
  `~/.gemini/antigravity` DOES exist"); on the observed install `main.log`
  records `[IDE Wizard] <path> not found — user was not migrated, skipping.`
- `~/.gemini/antigravity-backup/` is the backup taken during that copy,
  `app.asar:dist/paths.js@4313949`:

  ```text
  exports.IDE_BACKUP_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity-backup');
  ```

#### Desktop app data directory

`~/.gemini/antigravity/` (observed, macOS, app 2.23.0, 49 MB; the
Linux install of 2.23.1 had the same layout at 56 MB, with the additions
listed after the table):

| Path | Observed |
| --- | --- |
| `conversations/<uuid>.db` x4 (688,128 to 1,409,024 B, no sidecar files) | one SQLite database per conversation, the same schema as the CLI's ([section 8 of `analyzer/research/antigravity.md`](#8-record-schema)) |
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
  Code, not state, and excluded from 1.12.0 ([section 4](#4-exclusions)).
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

#### Brain directories

`brain/<uuid>/` (observed, app and CLI): `.system_generated/logs/transcript.jsonl`
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
[section 8 of `analyzer/research/antigravity.md`](#8-record-schema).

#### CLI data directory

`~/.gemini/antigravity-cli/` (live, observed on macOS, with binary
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
on the macOS install).

The rest of the directory: `cli.log` symlink to
`log/cli-<YYYYMMDD_HHMMSS>.log` (binary `cli.log`);
`conversation_summaries.db` (+`-wal`, `-shm`; binary
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
"wrote configurations to `~/.gemini/antigravity-cli/hooks.json` instead of
the shared `~/.gemini/config/hooks.json`").

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
  analyzer yields a summary row per app conversation from each database, see
  [section 10 of `analyzer/research/antigravity.md`](#10-other-stores).
  This was not seen on macOS (CLI 1.2.16) or Linux (1.3.4); whether it is
  new in 1.3.5 or needs the app to have run first is not determined.
- `cli.log` (41,122 B) is an NTFS hard link to
  `log/cli-20261014_202229.log`, not a symlink: `fsutil hardlink list`
  (`fsutil` is the Windows file-system utility) names both paths. A
  collection holds the bytes twice ([section 1](#1-source-and-evidence)).
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

#### Shared configuration directory

`~/.gemini/config/`, shared by the CLI and the app (binary changelog,
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
  The language server logged it (glog lines, digits and names redacted;
  repeat counts in brackets):

  ```text
  manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] is enabled   (x3)
  manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] starting
  manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] completed successfully in NN.NNNNms
  manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] already has status MIGRATION_STATUS_...   (x2)
  manager.go:NN] Migration [MIGRATION_ID_SIDECAR_USER_CONFIG_BYPASS] is disabled, skipping entirely   (x3)
  sidecar_manager.go:NNN] Config changed for sidecar <name>, updating...
  sidecar_sdk.go:NN] Using bundled agy-node
  ```

  Whether the sidecar ever started on Windows, and where its log would
  go, is not determined.
- `mcp_config.json` and `.migrated`, both empty (also on Windows).
- `node_modules/sidecar_sdk/` (observed, Linux, 5 files, 17,508 B): a copy
  of the sidecar SDK, excluded from 1.12.0. Absent on Windows.

#### Electron user-data directory

Electron keeps each app's own state, Chromium's storage included, in a
per-user directory that `app.getPath('userData')` returns, named after the
app under the per-OS application-data root. The root is
`~/Library/Application Support` on macOS and `%APPDATA%` on Windows
(`app.asar:node_modules/electron-log/src/node/NodeExternalApi.js@2235471`
`return path.join(home, 'Library/Application Support');` and @2235565
`return process.env.APPDATA || path.join(home, 'AppData/Roaming');`) and
`$XDG_CONFIG_HOME` or `~/.config` on Linux
([Electron app API](https://www.electronjs.org/docs/latest/api/app),
`app.getPath('appData')`, fetched 2026-10-13; the bundle snippets cover
macOS and Windows only). So the directory is
`~/Library/Application Support/Antigravity` (observed),
`~/.config/Antigravity` (observed on Linux, app 2.23.1) and
`%APPDATA%\Antigravity` (observed on Windows 11 ARM64 build 26300, app
2.23.1, 2026-10-14). The app stores UI state there
(`app.asar:dist/paths.js@4313059` `function getAppStoragePath() {` ...
`path_1.default.join(electron_1.app.getPath('userData'), 'app_storage.json')`,
"lightweight key-value store for UI state") and a Node wrapper for plugin
scripts (`app.asar:dist/utils.js@4399333` and @4399399):

```text
const binPath = path_1.default.join(userDataPath, 'bin');
const nodeWrapperPath = path_1.default.join(binPath, os === 'win32' ? 'agy-node.cmd' : 'agy-node');
```

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

#### Logs

Electron's logs directory is `~/Library/Logs/<name>` on macOS
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
Windows 11 ARM64 build 26300, app 2.23.1, 2026-10-14).

Observed on macOS: `main.log` (1,696 B; lines
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
AppImage warning ([section 1](#1-source-and-evidence)) and
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
[WSL](#wsl) below). The sidecar lines of `language_server.log` are under
`~/.gemini/config/` above.

#### macOS preferences file

`~/Library/Preferences/com.google.antigravity.plist` (916 B, observed)
holds only AppKit window and panel keys (`AppleTextDirection`,
`NSForceRightToLeftWritingDirection`, `NSNavPanelExpandedSizeForOpenMode`,
`NSOSPLastRootDirectory`, `NSTreatUnknownArgumentsAsOpen`) and has no
catalog line.

#### Antigravity IDE

The IDE (community, consistent across four sources):
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

#### WSL

On Windows the app can run its language server inside a WSL
(Windows Subsystem for Linux) distribution, installed at
`~/.antigravity-server/bin/<version>/` in the Linux home
(`app.asar:dist/wsl.js@4411665`
`` return `$HOME/.antigravity-server/bin/${version}`; ``; bundle-derived,
not observed on any real install). The directory holds the server binary;
where that server keeps conversations is not determined. The Windows
install (app 2.23.1, Windows 11 ARM64 build 26300, 2026-10-14, no WSL
distribution installed) shows the app listing WSL distributions at
start-up and for a "connect" menu: `main.log` has twice

```text
[error] Failed to list WSL distros: Error: wsl.exe --list --verbose failed: Command failed: C:\WINDOWS\System32\wsl.exe --list --verbose
```

with the OS text "The Windows Subsystem for Linux is not installed. You
can install by running 'wsl.exe --install'", from `dist\wsl.js`
(`execWsl`, `listWslDistros`), and once `[error] wsl:get-state failed: ...`
from `dist\menu.js` (`addWslConnectMenu`, `wslConnectMenuTemplate`) and
`dist\ipcHandlers.js`. The directory inside a distribution remains
unobserved.

#### System-level settings and environment variables

Enterprise `admin_settings.json` is system-level: `/etc/antigravity/`,
`/Library/Application Support/Antigravity/`, `...\Antigravity\` (binary).

Relocation env vars: none found for the home dir. `ANTIGRAVITY_EXECUTABLE_DATA_DIR`,
`AGY_ACCOUNT`, `AGY_ADC_AUTH`, `ANTIGRAVITY_PROJECT_ID`,
`ANTIGRAVITY_CONVERSATION_ID` exist (binary) but their effect on paths is
unknown.

### 3. Credentials

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
  lines (observed, home redacted)

  ```text
  I<MMDD HH:MM:SS.ffffff> <n> auth_store.go:136] Using file-based secret storage at ~/.config/antigravity/plugin-secrets.json
  ```

  and the binary carries the literal
  `plugin-secrets.json` beside `keychain get %s: %w` and
  `keychain set %s: %w` (observed, `agy` 1.3.4 linux-arm64, sha256 in
  [section 1](#1-source-and-evidence)). The file did not exist on
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
  `error_copy` rows ([section 1](#1-source-and-evidence)).
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
  treats Claude Desktop's `metadata_secret`, not as a secret glob.
  `app_storage.json` holds the signed-in account name
  (`jetski.onboarding.lastLoginUsername`), which identifies the user but
  is not a credential.
- IDE `state.vscdb` holds the conversation index
  (`antigravityUnifiedStateSync.trajectorySummaries`, Devilaiger) and, as a
  VS Code fork, probably auth state; collect unflagged.

### 4. Exclusions

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

### 5. Project-local files

`.agents/` workspace customizations (`.agents/agents/`, binary changelog;
damadorPL `<project-root>\.agents\`), `.antigravityignore` (binary),
`.antigravity-plugin` (binary), legacy `.antigravitycli/` (binary, removed
in favour of `cache/projects.json`). No per-project database.

### 6. Where the project path is recorded

- `history.jsonl`: `workspace` per prompt (CLI only; the app writes no
  `history.jsonl`), see
  [section 7 of `analyzer/research/antigravity.md`](#7-transcript-stores).
  On Windows it is the folder as the user typed it, with a lower-case
  `users` (`C:\users\<user>\demo2`, observed, CLI 1.3.5). The PowerShell
  collector compares project paths without regard to case
  (`Select-UniqueProjects`), so two spellings of one folder would not be
  collected twice; on that install they were two folders.
- `settings.json`: `trustedWorkspaces` array (binary json tag; docs/settings).
- `cache/projects.json`: workspace to project map (binary changelog).
- `history.jsonl` also carries `conversationId` from CLI 1.3.x (observed,
  Linux), which joins a prompt to its conversation; the analyzer uses it
  as the row's session id, see
  [section 9 of `analyzer/research/antigravity.md`](#9-joins-and-timestamps).
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
  collector keeps only `/`-rooted paths and `file://` URIs (see
  [which paths are used in `collectors/docs/coverage.md`](../collectors/docs/coverage.md#which-paths-are-used)),
  so in image mode over a Windows collection it discovers a project
  only from a `folderUri`: it found the app's `demo` and not the CLI's
  `demo2` (observed, [section 1](#1-source-and-evidence)).
- The analyzer carried the two Windows project folders under three
  `project_path` spellings: `c:/Users/<user>/demo` (from the
  percent-encoded `folderUri`), `C:/users/<user>/demo2` and
  `C:\users\<user>\demo2`; folding them is
  [doubleagent issue 112](https://github.com/seanthegeek/doubleagent/issues/112).
- `conversation_summaries.db` (`workspace_uris` column) and the
  per-conversation `*.db`: SQLite only, read by the analyzer.

## Parsing

### 7. Transcript stores

The four data directories under `~/.gemini` that can hold conversations:

| Directory | Written by |
| --- | --- |
| `.gemini/antigravity-cli/` | the CLI (**observed**, Linux, macOS and Windows) |
| `.gemini/antigravity/` | the desktop app 2.x (**observed**, macOS, Linux and Windows); before 2.0 the same directory was the VS Code-fork IDE's (`app.asar:dist/paths.js@4313608` `exports.IDE_OLD_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity');`) |
| `.gemini/antigravity-ide/` | the separately installed Antigravity IDE, after the app's install wizard copies the pre-2.0 IDE data out of `.gemini/antigravity` (`app.asar:dist/paths.js@4313784` `exports.IDE_NEW_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity-ide');`); bundle-derived, not observed on any real install |
| `.gemini/antigravity-backup/` | the backup taken during that copy (`app.asar:dist/paths.js@4313949` `exports.IDE_BACKUP_DATA_DIR = path_1.default.join(os_1.default.homedir(), '.gemini', 'antigravity-backup');`); bundle-derived, not observed on any real install |

The Linux install (**observed**, Ubuntu, CLI 1.3.4 and app 2.23.1) had the
same layout as the macOS one: `.gemini/antigravity/`,
`.gemini/antigravity-cli/` and `.gemini/config/`, and neither
`.gemini/antigravity-ide/` nor `.gemini/antigravity-backup/`. So did the
Windows install (**observed**, CLI 1.3.5 and app 2.23.1), under
`%USERPROFILE%\.gemini\` (the user's profile folder, the home on Windows),
with the same file names as on macOS and Linux.

Stores in each data directory (`<dir>` is one of the four above):

| Path | Content |
| --- | --- |
| `<dir>/conversations/<uuid>.db` (+`-wal`, `-shm`) | one SQLite database per conversation, WAL mode; the app's four had no sidecars when listed on macOS or Linux, nor did the app's four and the CLI's one on Windows (**observed**) |
| `<dir>/conversation_summaries.db` | one row per conversation; the app's copy adds a full-text search table, and the CLI 1.3.5 copy on Windows also held a row for each of the app's conversations ([Summaries database](#summaries-database)) |
| `.gemini/antigravity-cli/history.jsonl` | `{display, timestamp (ms), workspace}` per prompt; CLI only, the app writes none (**observed**). CLI 1.3.4 (**observed**, Linux) adds `conversationId`, the conversation's UUID, on some lines: of its two lines one had `display`, `timestamp` and `workspace`, the other `conversationId` as well ([section 9](#9-joins-and-timestamps)). CLI 1.3.5 (**observed**, Windows) wrote one line, with `display`, `timestamp` and `workspace` and no `conversationId` |
| `.gemini/antigravity-cli/cache/conversation_metadata.json` | CLI 1.3.5 (**observed**, Windows, 2,671 B; not seen on macOS with 1.2.16 or Linux with 1.3.4): `conversations` {`<uuid>`: {`is_internal` (bool), `last_modified_time` (ISO date), `summary` {`AgentName`, `AppDataDir`, `GroupID`, `ID` (UUID), `Internal` (bool), `Loaded` (bool), `NumSteps` (number), `Preview`, `ProjectID`, `Title`, `UpdatedAt` (ISO date), `WorkspaceURIs` (null)}}}; its four entries were the app's four conversations (`AppDataDir` of 11 characters, `antigravity`; `AgentName` and `GroupID` empty). The parser does not read it |
| `.gemini/antigravity-cli/cache/last_conversations.json` | {`<absolute path>`: `<uuid>`} (**observed**, Windows, 70 B): by its name, the last conversation per working folder; the parser does not read it |
| `.gemini/antigravity-cli/jetbox_summaries_proto.pb` | `jetbox_summaries_pb.SummariesState`, same summaries as the database; the app's counterpart is `.gemini/antigravity/agyhub_summaries_proto.pb` (1,436 B, **observed**; 1,417 B on Windows) |
| `<dir>/annotations/<uuid>.pbtxt` | seen in the app's directory (**observed**, 94-99 B each on macOS, 93-101 B on Linux, 93-96 B on Windows) and, from CLI 1.3.x, in the CLI's (**observed**, Linux, 37 B; Windows, 46 B): text-format protobuf (pbtxt, protobuf's human-readable text encoding, `field: value` lines) with a single `title:` field, the conversation title |
| `<dir>/brain/<uuid>/` | per-conversation artifacts and logs, below |
| `.gemini/antigravity-cli/antigravity-oauth-token` | credential, flagged secret by the collector; absent on the Windows install, where the CLI kept its token in the OS keyring ([section 12](#12-secrets)) |
| `.gemini/antigravity/plugin_data/<plugin>/token.json` | a plugin's OAuth credential ([section 12](#12-secrets)) |
| `<dir>/bin/` | binaries, excluded |
| `.gemini/antigravity/sidecar_data/<name>/logs/sidecar.log`, `sidecar_data/<name>/data/` | the scheduler log of the sidecar `<name>` and an empty `data/` directory (**observed**, Linux, 388 B, written when the automation was saved; absent on Windows), below |

The brain directory, `<dir>/brain/<uuid>/`, has the same layout for the CLI
and the app (**observed**, macOS, Linux and Windows):

| Path | Content |
| --- | --- |
| `.system_generated/logs/transcript.jsonl` | one JSON line per step, long fields shortened (17,832 to 155,131 B on the app; 12,720 to 56,481 B on Windows) |
| `.system_generated/logs/transcript_full.jsonl` | the same lines with nothing shortened |
| `.system_generated/logs/chunks/transcript/0000000N.jsonl`, `chunks/transcript_full/0000000N.jsonl` | the same lines split into chunks of about 100 KB; a line can be cut at a chunk boundary (one app conversation had two `transcript_full` chunks and `shape.py` counted one bad line in each). On Windows a 163,340 B `transcript_full.jsonl` was split into `chunks/transcript_full/00000000.jsonl` of 102,400 B (exactly 100 KiB) and `00000001.jsonl` of 60,940 B |
| `.system_generated/steps/<idx>/output.txt` | the output of each tool step (10 to 4,426 B on macOS, 9 to 8,248 B on Linux) |
| `.system_generated/steps/<idx>/content.md` | Markdown beside that step's `output.txt` (**observed**, Linux: one file of 24,820 B, step 20 of the 30-step app conversation; Windows: one of 2,682,163 B beside a 336 B `output.txt`, step 26 of the app conversation that, by modification time, set up the automation); not seen on macOS |
| `.system_generated/messages/<uuid>.json`, `messages/read.json` | app only, seen in a 43-step conversation on each platform: three messages addressed to the conversation on macOS, two of them tied to a `run_command` tool call; two on Linux, one of them tied to `run_command`; two on Windows (1,400 and 2,010 B, with an 89 B `read.json`), in the conversation that by modification time was the research task |
| `.system_generated/messages/undelivered/` | an empty directory in that Windows conversation (**observed**, Windows only); by its name, messages not yet delivered to the conversation |
| `.system_generated/tasks/task-<idx>.log` | app only, same conversations: plain-text output of a background task started by step `<idx>` (two on macOS; one on Linux, `task-10.log`, 996 B; one on Windows, `task-7.log`, 988 B) |
| `scratch/`, `.user_uploaded/` | empty directories on every install so far |

#### What survives a delete

What Antigravity's own delete of a conversation removes, in the CLI or the
app, is not stated: no real install has deleted one, and whether the app
removes the conversation database before the brain directory is not
observed. Deleting the project directory removes none of it: on the macOS
CLI 1.3.6 install of 2026-10-15 the conversation database, its
`brain/<uuid>/` mirror, the `history.jsonl` lines and the summaries row
stayed in place, and the whole session parsed after the directory was gone
([Observed](#observed)).

The per-prompt history file, `.gemini/antigravity-cli/history.jsonl`, is the
CLI's alone: each line has the prompt, its time in milliseconds and the
workspace, and from CLI 1.3.x some lines also the conversation id. The
second copies are the brain mirror (`transcript_full.jsonl`,
`transcript.jsonl` and their chunks), which survives what the database
survives and is lost with the data directory; the summaries database with
the app's full-text search table; the protobuf summaries files; the title in
`annotations/<uuid>.pbtxt`; and, on the CLI 1.3.5 install, the CLI's summary
rows and `cache/conversation_metadata.json` entries for the app's
conversations ([Summaries database](#summaries-database)). Whether a compaction or a
rewind rewrites the mirror is not observed, and no deletion marker is
stated. The analyzer reads `history.jsonl` and the brain mirror as secondary
sources and each summaries row as its own `conversation summary` row, and
does not read the annotations, the protobuf summaries, the full-text search
table or the CLI's cache (see
[Secondary sources](../analyzer/docs/output.md#secondary-sources)).

The mirror sits under `brain/<uuid>/`, beside `conversations/<uuid>.db` in
the same data directory. It is a second copy when the database alone is
lost, damaged or excluded: a database whose steps no longer decode, a
`-wal` sidecar the collection missed, a database file the collector skipped
for size, or a conversation the user deleted if the app removes the
database before the brain directory (not observed). The chunked copies
keep the transcript when `transcript_full.jsonl` itself was skipped for
size.

### 8. Record schema

#### Conversation database

```sql
CREATE TABLE trajectory_meta (trajectory_id text, cascade_id text, trajectory_type integer, source integer, PRIMARY KEY (trajectory_id));
CREATE TABLE steps (idx integer, step_type integer, status integer, has_subtrajectory numeric, metadata blob, error_details blob,
                    permissions blob, task_details blob, render_info blob, step_payload blob, step_format integer, PRIMARY KEY (idx));
CREATE TABLE gen_metadata (idx integer, data blob, size integer, PRIMARY KEY (idx));
CREATE TABLE executor_metadata (idx integer, data blob, PRIMARY KEY (idx));
CREATE TABLE parent_references (idx integer, data blob, PRIMARY KEY (idx));
CREATE TABLE trajectory_metadata_blob (id text DEFAULT "main", data blob, PRIMARY KEY (id));
CREATE TABLE battle_mode_infos (idx integer, data blob, PRIMARY KEY (idx));
```

The desktop app's databases have the identical schema (**observed**).
The tables mirror `gemini_coder.Trajectory`: `steps` (field 2),
`generator_metadata` (3), `trajectory_type` (4), `parent_references` (5),
`cascade_id` (6), `metadata` (7), `source` (8), `executor_metadatas` (9),
`battle_mode_infos` (10). `cascade_id` equals the conversation id and the
file name. `source` is a `CortexTrajectorySource` ([section 9](#9-joins-and-timestamps));
`trajectory_type` 4 is `CORTEX_TRAJECTORY_TYPE_CASCADE`.

`steps.step_payload` is a serialized `gemini_coder.Step`:

| Field | Name | Type |
| --- | --- | --- |
| 1 | `type` | `exa.cortex_pb.CortexStepType` (14 USER_INPUT, 15 PLANNER_RESPONSE, 132 GENERIC, 2 FINISH, 23 CHECKPOINT, 28 COMMAND_STATUS, 17 ERROR_MESSAGE, 101 SYSTEM_MESSAGE, ...) |
| 4 | `status` | `CortexStepStatus` (1 PENDING, 2 RUNNING, 3 DONE, 6 CANCELED, 7 ERROR, 9 WAITING, 12 INTERRUPTED) |
| 5 | `metadata` | `CortexStepMetadata` |
| 7..159 | oneof `step` | one message per step kind, field numbers in the parser's `SCHEMA["Step"]`; a protobuf oneof is a group of fields of which at most one is set, so the field present names the step kind |
| 133 | `permissions` | `exa.cortex_pb.TrajectoryPermissions`, also stored in the `steps.permissions` column |
| 148 | `task_details` | `gemini_coder.TaskDetails`, also stored in the `steps.task_details` column |

`steps.metadata` duplicates field 5. `CortexStepMetadata`: 1 `created_at`,
3 `source` (`CortexStepSource`: 2 MODEL, 3 USER_IMPLICIT, 4 USER_EXPLICIT,
5 SYSTEM), 4 `tool_call` (`ChatToolCall`: 1 `id`, 2 `name`, 3
`arguments_json`, 9 `original_name`), 7 `finished_generating_at`, 8
`completed_at`, 11 `generator_model` (enum), 12 `execution_id`, 20
`source_trajectory_step_info`, 26 `internal_metadata.status_transitions`,
30 `tool_summary`, 31 `tool_action`, 32 `started_at`. All timestamps are
`google.protobuf.Timestamp` (seconds, nanos).

Step kinds seen on a real install: `user_input` (19: 1 `query`, 2
`user_response`, 12 `user_config`), `planner_response` (20: 1 `response`,
3 `thinking`, 6 `message_id`, 7 `tool_calls[]`, 12 `stop_reason`, 16
`raw_thinking`) and `generic` (140: 1 `args[]` key/value, 2 `result`
with 1 `result` text and 6 `payload` as `google.protobuf.Any` holding the
typed tool step, here `view_file`). The desktop app's conversations
(**observed**, macOS) also have `system_message` (step type 101, payload
field 114: 1 `message`, 3 `event_type`) and `error_message` (step type 17,
payload field 24: 3 `error` as `CortexErrorDetails` with 1
`user_error_message`, 2 `short_error`, 3 `full_error`). Counts across the
app's four conversations (110 steps): 7 `user_input` (14), 51
`planner_response` (15), 44 `generic` (132), 3 `system_message` (101, all
in the 43-step conversation) and 5 `error_message` (17, all in the 31-step
conversation). Every step had `status` 3 (DONE), `has_subtrajectory` 0 and
`step_format` 0. `steps.permissions` was set on 10 tool steps (52 to 1,174
B) and `steps.task_details` on 2 (239 and 764 B); `error_details` and
`render_info` were empty.

Step kinds other than `user_input`, `planner_response`, `generic`,
`system_message` and `error_message` are decoded from the descriptors but
have not been seen in real data.

The Linux installs (**observed**, CLI 1.3.4 and app 2.23.1) showed the
same three common kinds and `system_message`, and no `error_message`. The
app's four conversations (125 steps): 14 steps (2 `user_input`, 7
`planner_response`, 6 `generic`; `permissions` on none), 43 steps (1, 21,
19 and 2 `system_message`; `permissions` on 6, `task_details` on 1), 30
steps (1, 15, 13; `permissions` on 4) and 38 steps (1, 19, 18;
`permissions` on 9). The CLI's one conversation: 26 steps (2, 13, 11),
`permissions` on 9. In all five, `gen_metadata` had one row per planner
step (7, 21, 15, 19 and 13). The parser reads `permissions` (below) and not
`task_details`.

`steps.permissions` holds an `exa.cortex_pb.TrajectoryPermissions`, the
same message as `gemini_coder.Step` field 133, recording what the user
allowed or denied for that step's tool call. Its fields, from the
descriptors (`third_party/jetski/cortex_pb/cortex.proto`, identical in
`agy` 1.2.16 and `language_server` 2.23.0, macOS arm64):

| Message | Field | Name | Type |
| --- | --- | --- | --- |
| `TrajectoryPermissions` | 1 | `file_access_permissions[]` | `FileAccessPermission` |
| `TrajectoryPermissions` | 2 | `permission_grants[]` | `PermissionGrant` |
| `PermissionGrant` | 1 | `resource` | `PermissionResource` (1 `action`, 2 `target`, both string) |
| `PermissionGrant` | 2 | `allow` | bool |
| `PermissionGrant` | 3 | `scope` | `PermissionScope` |
| `PermissionGrant` | 4 | `user_deny_instruction` | string |
| `PermissionGrant` | 5 | `action` | string |
| `PermissionGrant` | 6 | `target` | string |
| `FileAccessPermission` | 1 | `path` | string |
| `FileAccessPermission` | 2 | `is_directory` | bool |
| `FileAccessPermission` | 3 | `allow` | bool |
| `FileAccessPermission` | 4 | `scope` | `PermissionScope` |
| `FileAccessPermission` | 5 | `from_current_step` | bool |

`exa.cortex_pb.PermissionScope`, how long a grant holds (each name prefixed
`PERMISSION_SCOPE_`): 0 `UNSPECIFIED`, 1 `ONCE`, 2 `CONVERSATION`, 3
`WORKSPACE`, 4 `GLOBAL`, 5 `PROJECT`. Protobuf 3 does not write a false
bool or a zero enum, so a grant with no `allow` is a denial and one with
no `scope` is `UNSPECIFIED`. The column was set on 10 tool steps of the
macOS app's conversations (52 to 1,174 B) and on 28 Ubuntu steps (0, 6, 4
and 9 in the app's four conversations, 9 in the CLI's one; **observed**);
which scope values and which `action` strings occur was not read. On
Windows (**observed**, CLI 1.3.5 and app 2.23.1) the parser yielded 50
`permission grant` rows across the five conversations, three of them for
PowerShell `Get-ChildItem` commands; their scopes were not recorded.

The tool executed by a step is in its `metadata.tool_call`; its `id`
matches the `tool_calls[].id` proposed by the preceding planner step. Tool
payload messages the parser understands: `run_command` (1 `command`, 2
`cwd`, 6 `exit_code`, 21 `combined_output`, 23 `command_line`, 14
`user_rejected`), `command_status`, `shell_exec`, `view_file` (1
`absolute_path_uri`), `list_directory`, `grep_search`, `find`,
`write_to_file` (1 `target_file_uri`, 4 `file_created`), `file_change`,
`code_action` (1 `action_spec` with `command.file`, `create_file.path`,
`delete_file.path`, `sed.path` as `PathScopeItem` 5 `absolute_uri`),
`read_url_content`, `search_web`, `mcp_tool` (1 `server_name`, 2
`tool_call`, 3 `result_string`), `agency_tool_call`, `invoke_subagent` (5
`conversation_id`, 10 `results[].conversation_id`), `ask_question`,
`checkpoint`, `system_message`, `ephemeral_message`, `task_boundary`,
`notify_user`, `error_message`, `finish`, `memory`, `directory_rules`,
`conversation_history`, `send_command_input`.

The paths inside `action_spec` sit at different field numbers per action:
`ActionSpecCommand` 4 `file`, `ActionSpecCreateFile` 2 `path`,
`ActionSpecDeleteFile` 1 `path` and `ActionSpecSed` 3 `path`, each a
`PathScopeItem` (descriptors of `agy` 1.2.16 and `language_server` 2.23.0,
macOS arm64). Up to analyzer 0.11.0 the parser read `delete_file` with
the `create_file` layout, `path` at field 2, so a delete action lost its
path or its step failed to decode; the 2026-10-13 descriptor diff found
it and analyzer 0.12.0 reads field 1 (issue 88). No `code_action` step
has been seen in real data.

`gen_metadata.data` is `CortexStepGeneratorMetadata`: 1 `chat_model`
(`ChatModelMetadata`: 19 `response_model` such as `gemini-3.8-flash`, 21
`model_display_name`, 1 `system_prompt`, 2 `message_prompts[]`), 2
`step_indices[]` (packed). This is the only place the model name appears.
The app's databases have one `gen_metadata` row per planner step
(**observed**); `executor_metadata` had 1-3 rows, `parent_references` and
`battle_mode_infos` none, and `trajectory_metadata_blob` one row of 618-698
B.

Three tool-payload fields carry permission evidence (issue 97), all bool and
identical in the `agy` 1.2.16 and `language_server` 2.23.0 descriptors
(macOS arm64): `CortexStepRunCommand` 14 `user_rejected` and 34
`ran_in_sandbox`, and `CortexStepMcpTool` 7 `user_rejected`. None of the
three has been seen set in real data, since every observed tool step was a
`generic` step whose typed payload sits in a `google.protobuf.Any` the
parser does not unpack.

`trajectory_metadata_blob.data` is `CortexTrajectoryMetadata`: 1
`workspaces[]` (`CortexWorkspaceMetadata`: 1 `workspace_folder_absolute_uri`,
2 `git_root_absolute_uri`, 4 `branch_name`), 2 `created_at`, 5
`parent_conversation_id`, 6 `root_conversation_id`, 7 `workspace_uris[]`,
17 `nesting_depth`, 18 `project_id`.

#### Brain mirror lines

Brain JSONL line shapes (both `transcript.jsonl` and
`transcript_full.jsonl`, app and CLI, **observed**): every line has
`content`, `created_at`, `source`, `status`, `step_index` and `type`, where
`type` is `USER_INPUT`, `PLANNER_RESPONSE`, `GENERIC`, `SYSTEM_MESSAGE` or
`ERROR_MESSAGE`. `PLANNER_RESPONSE` lines add `thinking`, `tool_calls`,
`input_tokens`, `output_tokens` and `cache_read_tokens`; `ERROR_MESSAGE`
lines add `error`; in `transcript.jsonl` (not `_full`) long `GENERIC` and
`PLANNER_RESPONSE` lines add `truncated_fields`. On Linux (CLI 1.3.4 and app
2.23.1, **observed**) every `GENERIC` line also has an `error` key, which on
macOS appeared only on `ERROR_MESSAGE` lines. The line count equals the
conversation database's step count; the Linux app's four transcripts had
14, 30, 38 and 43 lines and no bad line; the macOS CLI 1.3.6 conversation of
2026-10-15 had 16 `transcript_full.jsonl` lines for 17 database steps
([Observed](#observed)), so the mirror can lag the database by
a step. The token counts appear nowhere the parser reads.

The value forms come from a format description the backend embeds for its
own agent, which is told to read past conversations from these files
(`agy` 1.3.6 macOS arm64, the binary of [Observed](#observed),
sha256 `827ba22b4aa33557614a57aac2cc13f386e17db6b802febd3932226906ac05ab`,
read with `strings` and `grep -b`, never run):

- `agy 1.3.6 darwin-arm64 @54350700` `Transcripts are in JSON Lines (JSONL)
  format.`, one JSON object per step.
- `@54350936` `` `source`: The source of the action (e.g., `USER_EXPLICIT`,
  `MODEL`, `SYSTEM`). ``: the names of `exa.cortex_pb.CortexStepSource`
  without the `CORTEX_STEP_SOURCE_` prefix. The enum also has
  `CORTEX_STEP_SOURCE_USER_IMPLICIT` (`@52896931`), the source of a prompt
  the backend injected rather than one the user typed, which the database
  reader turns into a `system` row; that a mirror line spells it
  `USER_IMPLICIT` is inferred from the other three names, not observed.
- `@54351208` `` `status`: The status of the step (e.g., `DONE`, `ERROR`). ``:
  `CortexStepStatus` names without their prefix, the database's
  `STEP_STATUS` values upper-cased.
- `@54351268` `` `created_at`: The ISO 8601 timestamp of when the step
  occurred. ``: one time per line. The database step has `created_at` and
  `completed_at` ([Conversation database](#conversation-database)); which of them
  the line repeats was not compared on a real install, and the parser
  takes it as `created_at`.
- `@54351541` `` `tool_calls`: An array of tool calls made in this step,
  including their arguments. ``: the element's keys are not given, and
  no real install has recorded them; the parser reads `id`, `name` and
  the arguments as `arguments_json`, `args` or `arguments`, the first
  present, an object or a JSON string (fixture only).
- `@54351847` `` `truncated_fields`: An array of field names that were
  truncated ``, followed by the examples `["content"]`, `["thinking"]`,
  `["tool_calls"]`, and the statement that the key is never in
  `transcript_full.jsonl`.
- `@53937489` `` `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript_full.jsonl` ``:
  `<appDataDir>` is the data directory (`antigravity-cli`, `antigravity`,
  and so on), the same name the app passes the language server.

A `GENERIC` line carries no tool name or call id: its `content` is the
tool's output. The database's tool steps on every real install so far were
`generic` steps whose `metadata.tool_call` names the call
([section 9](#9-joins-and-timestamps)); a planner step's calls are run as the
steps after it.

#### Brain message files

`messages/<uuid>.json` (**observed**): `content` (string), `id` (UUID),
`priority` (upper-case enum-like string), `recipient` (UUID),
`renderDetails` {`messageTitle`}, `sender` (a 43-44 character string
containing a UUID), `timestamp` (ISO date), and on two of three
`sourceMetadata` {`tool` {`conversationId` (UUID), `stepIndex` (number),
`toolCall` {`argumentsJson`, `id` (`call_` and digits), `name`
(`run_command`), `thinkingSignature`}}}. `messages/read.json` is
{`<uuid>`: bool} per message. On Linux the two messages had the same keys,
`sender` 44 characters.

### 9. Joins and timestamps

Conversation id = `cascade_id` = file name = `conversation_summaries.
conversation_id` = the `brain/<uuid>/` and `annotations/<uuid>.pbtxt`
names. Subagent conversations are separate databases linked by
`parent_conversation_id` and by `invoke_subagent.results[].conversation_id`.
Git branch is available only when the trajectory metadata records a
workspace `branch_name`; the sample run from a non-git directory left it
empty. Up to CLI 1.2.x `history.jsonl` has no conversation id, so its rows
carry only the workspace. From CLI 1.3.x a line can carry `conversationId`
(**observed**, CLI 1.3.4 Linux, one of two lines), which is the
conversation id above; the parser puts it in the history row's
`session_id` (issue 89), so the prompt joins to its conversation's rows,
and a line without it keeps `session_id` empty. A macOS session with CLI
1.3.6 (**observed**, 2026-10-15) shows which lines get it: of four lines
for one conversation, the first prompt, written before the conversation
existed, had no `conversationId`, and the three prompts typed into the
running conversation all carried it. The two earlier observations fit
that pattern (one of two lines on Linux; the single first-prompt line on
Windows, CLI 1.3.5, had none), so a history row with an empty
`session_id` is a conversation's opening prompt, attributed to the
workspace only, and its conversation is the database whose first
`USER_INPUT` step has the same text and a timestamp within a second.

On Windows one folder can reach the parser under several spellings, since
the parser passes a plain path through unchanged and turns a `file:` URI
into a path with `uri_to_path`, which keeps the drive letter's case and uses
forward slashes. The Windows install (**observed**, Windows 11, CLI 1.3.5
and app 2.23.1, 2026-10-14) gave three: `c:/Users/sean/demo`, from the app's
`file:///c%3A/Users/sean/demo` URIs (a percent-encoded colon and a
lower-case drive letter, as the project file's `folderUri` records it);
`C:/users/sean/demo2`, from the `file:` URI in the CLI conversation's
`conversation_summaries.workspace_uris`; and `C:\users\sean\demo2`, the
plain path of the `history.jsonl` `workspace`. The lower-case `users` is how
the user typed the CLI's working folder. `collection.json` listed the two
folders as `C:\Users\sean\demo` and `C:\users\sean\demo2`. Up to analyzer
0.12.0 the rows carried the three spellings as recorded, so `inventory.json`
split one folder into two projects and neither matched the collected
folder's spelling. From analyzer 0.13.0
([doubleagent issue 112](https://github.com/seanthegeek/doubleagent/issues/112))
the timeline writes every Windows `project_path` in one canonical form
(upper-case drive letter, backslash separators, no trailing separator), so
the three become `C:\Users\sean\demo` and `C:\users\sean\demo2`, and
`inventory.json` groups spellings that differ only in case; the
canonicalisation is applied to every parser's rows in `collect_rows` in
`cli.py`, and the parser itself is unchanged.

Which surface wrote a conversation is recorded twice: the data directory
the database sits in, and `trajectory_meta.source`, an
`exa.cortex_pb.CortexTrajectorySource` (each name prefixed
`CORTEX_TRAJECTORY_SOURCE_`; identical in `agy` 1.2.16 and
`language_server` 2.23.0):

```text
0 UNSPECIFIED, 1 CASCADE_CLIENT, 2 EXPLAIN_PROBLEM, 3 REFACTOR_FUNCTION,
4 EVAL, 5 EVAL_TASK, 6 ASYNC_PRR, 7 ASYNC_CF, 8 ASYNC_SL, 9 ASYNC_PRD,
10 ASYNC_CM, 12 INTERACTIVE_CASCADE, 13 REPLAY, 15 SDK, 16 SUBAGENT,
17 CLI, 18 JETBOX, 19 AGENT_API, 20 CIDER, 21 GEMINI_APP, 22 VSCODE,
23 VISUAL_STUDIO
```

The CLI writes 17 (`CLI`) and the desktop app 1 (`CASCADE_CLIENT`)
(**observed**, macOS and Linux). The summaries table's `app_data_dir` column holds
the data-directory name the app passes the language server (`antigravity`
on the app, `antigravity-cli` on the CLI). It also tells a summary row
the CLI 1.3.5 database mirrors from the app (`antigravity`) from the CLI's
own ([Summaries database](#summaries-database)); the parser does not put
`app_data_dir` in the row's text, but the row's `source_file` names the
database it came from. The parser puts
`source=<name>` and `data_dir=<directory>` in each conversation's session
start row. The conversation title is in `conversation_summaries.title` and
in `annotations/<uuid>.pbtxt` (`title:`); the parser reads the former.

The brain mirror ([section 7](#7-transcript-stores)) joins the
database by conversation id: the `<uuid>` of `brain/<uuid>/` is the
database's `cascade_id`, and the parser puts it in `session_id` for both.
A mirror line repeats one database step, and the timeline pairs the two
rows on `session_id`, `turn_type` and `text` within 600 seconds (see
[Secondary sources in `docs/output.md`](../analyzer/docs/output.md#secondary-sources),
the analyzer's rule for second copies). The mirror records no workspace,
so its rows have no `project_path`; they need none to pair, since the
session id scopes the match. The text joins because the parser renders a
mirror line as the database reader renders the step of the same kind. The
time is the weak part: the line has one `created_at`, while the database
reader stamps an `assistant`, `tool_use` or `tool_result` row with the
step's `completed_at`, so the mirror's row comes first by the time the
model or the tool took, which is what the 600 seconds cover. Rows that do
not pair, and so appear twice when both stores survive: a
`SYSTEM_MESSAGE` whose database step has an `event_type` (the
`task_notification` events of every real install; the database row reads
`task_notification: <message>`, and the line records no event type), a
queued prompt (the database row starts `[queued] `), a field shortened in
`transcript.jsonl` on a row with no `tool_use_id` (a shortened tool call
or result pairs on the id the parser infers for it, since analyzer
0.13.0 pairs tool rows on their ids), a step that ran longer than ten
minutes, and a `GENERIC` line whose `content` differs from the database
step's `generic.result.result` and that has no inferred id, which no
install has compared. A conversation's opening prompt is in
`history.jsonl` without `conversationId`, in the mirror and in the
database; the history line, matched by workspace, can take the database
row first, and the mirror's row, matched by session, then finds the
history row under the broader scope `dedup.deduplicate` tries among
secondary rows, so the prompt is shown once.

### 10. Other stores

#### Summaries database

```sql
CREATE TABLE conversation_summaries (conversation_id text PRIMARY KEY, title text, preview text, step_count integer,
  last_modified_time datetime, workspace_uris text, status text, source text, project_id text, agent_name text,
  parent_conversation_id text, nesting_depth integer, battle_id text, winning_conversation_id text, not_fully_idle numeric,
  killed numeric, last_user_input_time datetime, last_user_input_step_index integer, app_data_dir text, raw_summary blob, group_id text);
```

Times are text like `2026-10-03 16:43:44.002530482+00:00`. `workspace_uris`
is a JSON array of `file://` URIs. `status` is a `CascadeRunStatus` name.
`raw_summary` is `exa.jetski_cortex_pb.CascadeTrajectorySummary` (1
`summary`, 2 `step_count`, 3 `last_modified_time`, 7 `created_time`, 9
`workspaces[]`, 10 `last_user_input_time`, 17 `trajectory_metadata`, 22
`trajectory_type`, 24 `fork_parent_conversation_id`).

The desktop app's `conversation_summaries.db` (**observed**, macOS; 131,072
B with a 32,768 B `-shm` and an empty `-wal`) has the same
`conversation_summaries` table and two more:

- `search_schema_version(version)`, one row, value 3.
- `conversations_fts`, an FTS5 virtual table (FTS5 is SQLite's full-text
  search extension; a virtual table whose rows live in the shadow tables
  `conversations_fts_data`, `_idx`, `_content`, `_docsize` and `_config`;
  the Linux listing showed `conversations_fts_config`, which the macOS
  listing did not record) with the
  columns `conversation_id`, `chunk_index`, `chunk_first_step`,
  `chunk_last_step`, `last_modified_time`, `step_count`,
  `last_step_created_at`, `archived`, `user_step_byte_offsets`,
  `agent_step_byte_offsets`, `title`, `workspace`, `project`, `user_body`
  and `agent_body`, tokenizer `unicode61 remove_diacritics 2`, prefix
  indexes `1 2 3`; 8 rows for 4 conversations. By their names,
  `user_body` and `agent_body` hold the user's and the agent's text of a
  chunk of steps (the values were not read); the parser does not read
  the table.

Its four `conversation_summaries` rows had `status`
`CASCADE_RUN_STATUS_IDLE`, `source` and `agent_name` empty,
`nesting_depth` 0, `parent_conversation_id` and `group_id` empty, `killed`
0, `project_id` and `title` set, `app_data_dir` `antigravity`,
`raw_summary` of 285-395 B and `workspace_uris` as text. The CLI's
summaries database has only `conversation_summaries`.

On Linux (**observed**, app 2.23.1) the app's database was 167,936 B with a
32,768 B `-shm` and an empty `-wal`, the same schema with
`search_schema_version` 3, and four rows like the macOS ones, `raw_summary`
278-390 B. The CLI 1.3.4 summaries database was 20,480 B with only
`conversation_summaries` and one row (`app_data_dir` `antigravity-cli`,
`raw_summary` 386 B).

On Windows (**observed**, CLI 1.3.5 and app 2.23.1) neither summaries
database had a `-wal` or `-shm` sidecar: the app's was 159,744 B, the
CLI's 40,960 B. The CLI's held five rows, its own conversation's and one
for each of the app's four, which carry `app_data_dir` `antigravity`; the
CLI's `cache/conversation_metadata.json` lists the same four
([section 7](#7-transcript-stores)), and its `cli.log` has a line
from `reconcile_summaries.go` and one from `project_uris_migration.go`.
The parser reads every row of both databases, so each app conversation
yields two `conversation summary` rows, one from each database (9 for 5
conversations on this install). The mirrored row has no run status: the
app's own row reads
`conversation summary | <title> | CASCADE_RUN_STATUS_IDLE | 20 steps` and
the CLI's copy `conversation summary | <title> | 20 steps`. Neither macOS
(CLI 1.2.16) nor Linux (CLI 1.3.4) showed the mirroring; whether it is new
in 1.3.5 or needs the app to have run first on the same profile is not
determined.

#### Permission configuration files

Besides the per-step grants in the conversation databases
([Conversation database](#conversation-database)), Antigravity keeps standing permission
state in four JSON files, which together are its permission configuration. A
grant entry is a tool-call pattern: a tool name followed by its argument in
parentheses. The keys, with what was seen on the 2026-10-13 real installs
(macOS: CLI 1.2.16 and app 2.23.0; Ubuntu: CLI 1.3.4 and app 2.23.1; key
names and counts only, **observed** unless marked):

| File | Keys |
| --- | --- |
| `.gemini/config/config.json` (shared by the CLI and the app) | `userSettings.globalPermissionGrants.allow[]` (3 entries on macOS, 11 on Ubuntu, 14 on Windows), `userSettings.permissionGrantsV2Migrated` (bool), `userSettings.sandboxEnabledAtV2Migration` (bool); per automation (sidecar) `sidecars.<name>.enabled` and `sidecars.<name>.resolvedPermissions.accessGrants[]` (not in the macOS or the Windows file; the Windows file also had neither migration flag) |
| `.gemini/config/projects/<uuid>.json` | `permissionGrants.permissionGrants.allow[]` (seen on one Ubuntu project file), `permissionGrants.v2Migrated`; the project folder is `projectResources.resources[].folderUri` |
| `.gemini/config/sidecars/<name>/sidecar.json` | `agent_permissions.access_grants[]` (2 entries on macOS, 3 on Windows) |
| `.gemini/antigravity-cli/settings.json` | `permissions.allow[]` (CLI 1.3.x; one entry on Windows) and `trustedWorkspaces[]` (the folders the user trusted; a JSON tag in the binary, see [CLI data directory](#cli-data-directory)) |

#### Sidecar logs

`sidecar_data/<name>/logs/sidecar.log` (**observed**, Linux): the plain-text
log of the sidecar named `<name>` (the automation's name, the same as its
directory under `.gemini/config/sidecars/`). With digits and names
redacted, its lines were:

```text
=== sidecar "<name>" started at <timestamp> ===
<date> <time> [schedule] Scheduler started for schedule: "CRON_TZ=America/New_York N N * * *"
<date> <time> [schedule] Calculated jitter: NmNN.NNNNNNNNs
<date> <time> [schedule] Next execution scheduled in NNhNNmNNs (at <UTC time>), will run by ...
```

So a scheduled automation's own output lands under
`sidecar_data/<name>/logs/`. The schedule is a cron expression with a time
zone prefix (`CRON_TZ=`). The parser does not read the log.

On Windows (**observed**, app 2.23.1) the automation was saved
(`.gemini/config/sidecars/<name>/sidecar.json`, written 00:17:41Z to
00:20:16Z), but no `sidecar_data/` directory existed 25 minutes later and
`config.json` had no `sidecars` key, both of which the Linux install had
within a minute of saving. The language server's log,
`%APPDATA%\Antigravity\logs\language_server.log`, has these lines about it
(digits and names redacted; repeat counts in brackets):

```text
manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] is enabled   (x3)
manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] starting
manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] completed successfully in NN.NNNNms
manager.go:NN] Migration [MIGRATION_ID_BUILTIN_SIDECARS_TO_PLUGINS] already has status MIGRATION_STATUS_...   (x2)
manager.go:NN] Migration [MIGRATION_ID_SIDECAR_USER_CONFIG_BYPASS] is disabled, skipping entirely   (x3)
sidecar_manager.go:NNN] Config changed for sidecar <name>, updating...
sidecar_sdk.go:NN] Using bundled agy-node
```

Whether the sidecar ever started on Windows, and where its log would go
there, is not determined.

### 11. Format versions

The builds observed differ in which files and keys they write; the
protobuf schemas were compared only between the Linux (WSL) build and the
macOS CLI 1.2.16 and app 2.23.0, and the descriptors of the later builds
were not extracted ([Observed](#observed)).

- `history.jsonl`: up to CLI 1.2.x a line has no conversation id; from CLI
  1.3.x a prompt typed into a running conversation carries
  `conversationId` and a conversation's opening prompt does not (CLI
  1.3.4 on Linux, 1.3.5 on Windows, 1.3.6 on macOS;
  [section 9](#9-joins-and-timestamps)).
- `annotations/<uuid>.pbtxt` appears in the CLI's directory from CLI
  1.3.x, as in the app's ([section 7](#7-transcript-stores)), and the
  CLI's `settings.json` has `permissions.allow[]` from CLI 1.3.x
  ([Permission configuration files](#permission-configuration-files)).
- CLI 1.3.5 on Windows wrote `cache/conversation_metadata.json` and a
  summary row for each of the app's conversations, which neither CLI
  1.2.16 on macOS nor 1.3.4 on Linux showed; whether that is new in 1.3.5
  or needs the app to have run first is not determined
  ([Summaries database](#summaries-database)).
- Brain mirror lines: on Linux (CLI 1.3.4 and app 2.23.1) every `GENERIC`
  line has an `error` key, which on macOS appeared only on
  `ERROR_MESSAGE` lines ([Brain mirror lines](#brain-mirror-lines)).
- Before 2.0 the VS Code-fork IDE wrote `.gemini/antigravity/`, the
  directory the desktop app 2.x now uses; the separately installed IDE's
  directory is `.gemini/antigravity-ide/` ([section 7](#7-transcript-stores)).

The descriptor comparison: `tools/proto_descriptors.py extract` (after the
fix for issue 86) found 271 descriptor files in `agy` 1.2.16 and 484 in
`language_server` 2.23.0; the difference from the Linux count in
[section 1](#1-source-and-evidence) was not investigated.
`exa.cortex_pb.CortexStepType` (118 values), `CortexStepStatus`,
`CortexTrajectorySource`, `gemini_coder.Step`, `gemini_coder.Trajectory` and
every message in the parser's `SCHEMA` were diffed against the parser's
tables, which were built from the Linux descriptors: field numbers, names
and types match in both macOS binaries, and the two define
`CortexTrajectorySource` identically ([section 9](#9-joins-and-timestamps)).
Nothing the parser reads drifted. The diff did find one error in the tables
themselves, the `delete_file` layout ([Conversation database](#conversation-database)).

### 12. Secrets

`antigravity-oauth-token` (collector secret glob).
`plugin_data/<plugin>/token.json` under the desktop app's data directory
(**observed**, macOS: `plugin_data/gdocs/token.json`, 1,119 B, mode 0600)
is the Google Docs plugin's OAuth credential: keys `client_id`,
`client_secret`, `email`, `scopes` (8 URLs), `token` {`access_token`,
`expiry` (ISO date), `refresh_token`, `token_type`} and `updated_at`. The
collector flags it `secret: true` from collector 1.12.0 (issue 84); the
parser never reads it. `ChatModelMetadata.system_prompt` and
`message_prompts` in `gen_metadata` hold the full prompt including file
contents; the parser does not read them. Tool outputs in `generic.result`
and `run_command`, the brain directory's `steps/<idx>/output.txt` and
`tasks/*.log` contain whatever the agent read, and so, presumably, do the
FTS5 table's `user_body` and `agent_body`.

On Windows (**observed**, CLI 1.3.5) the CLI kept its OAuth token in the
OS keyring, the Windows Credential Manager, and wrote no
`antigravity-oauth-token` or `plugin-secrets.json` file; the desktop app's
`Local State` file there holds key material. Both are described in
[section 3 of `collectors/research/antigravity.md`](#3-credentials);
the parser reads neither.

### 13. Parser plan

Every source below is read on every run; a secondary source is one whose
rows the timeline drops when the primary store yields the same event
([Secondary sources in `docs/output.md`](../analyzer/docs/output.md#secondary-sources)).

| Source | Role | Rows |
| --- | --- | --- |
| `<dir>/conversations/<uuid>.db` | primary: the store of record, every step with its payload, model, permissions and both times | session start, user, assistant, tool_use, tool_result, thinking, system, model and permission rows ([Conversation database](#conversation-database)) |
| `<dir>/conversation_summaries.db` | primary: a summary per conversation, not a copy of its events | one `conversation summary` `system` row per conversation ([Summaries database](#summaries-database)) |
| `.gemini/antigravity-cli/history.jsonl` | secondary (2 seconds): the prompts the database also records | one `user` row per line ([section 9](#9-joins-and-timestamps)) |
| `<dir>/brain/<uuid>/.system_generated/logs/transcript_full.jsonl`, else `chunks/transcript_full/*.jsonl` concatenated, else `transcript.jsonl`, else `chunks/transcript/*.jsonl` | secondary (600 seconds): one copy of the database's steps, read in that order of preference, one copy per conversation | user, assistant, tool_use, tool_result, thinking and system rows, as the database reader renders the same step kinds ([section 7](#7-transcript-stores)) |
| the standing permission files | primary: no other copy | `permission setting` rows ([Permission configuration files](#permission-configuration-files)) |

The four mirror files are copies of one transcript, not four sources: the
shortened `transcript.jsonl` holds the same lines with long fields cut, and
the chunks are the same bytes split at 102,400 bytes. Not read:
`brain/<uuid>/.system_generated/steps/<idx>/output.txt` and `content.md`,
`messages/<uuid>.json` and `tasks/task-<idx>.log` (outputs and messages
the steps already carry, or not yet mapped to a step), `annotations/*.pbtxt`
(the title, also in the summaries database),
`cache/conversation_metadata.json`, `jetbox_summaries_proto.pb` and
`agyhub_summaries_proto.pb` (summaries again), and the app's FTS5 table.

#### Permission rows

The parser decodes the `steps.permissions` column
([Conversation database](#conversation-database)), or Step field 133 of the payload when
the column is empty, and yields after the step's own rows one `system` row
per `permission_grants[]` entry,
`permission grant: action=<action> target=<target> allow=<true|false> scope=<scope>`
(`action` and `target` from fields 5 and 6, else from `resource`; with
`deny_instruction=<text>` appended when `user_deny_instruction` is set), and
one per `file_access_permissions[]` entry,
`permission grant: path=<path> is_directory=<true|false> allow=<true|false> scope=<scope>`
(with `from_current_step=true` appended when set). Each row carries the
step's `tool_name` and `tool_use_id`, so it sits beside the call it
governed, and the step's tool-result time; `<scope>` is the lower-case name
without the prefix, or the number for a value not in the enum.

A step with `user_rejected` set (the three tool-payload fields of
[Conversation database](#conversation-database)) yields, right after its `tool_result`
row (whose text keeps `[rejected by user]`), a `system` row
`permission decision: user_rejected` with the step's `tool_name`,
`tool_use_id` and result time. `ran_in_sandbox` is not a decision: a
`run_command` result with it set ends with ` sandbox=true`.

The `antigravity` parser reads the keys of the
[permission configuration files](#permission-configuration-files) and
nothing else in the files (not `plugins`, `remoteControlHostname`, a
project's `name` or a sidecar's `args`), and never wants `mcp_config.json`,
which can embed MCP credentials, or a plugin's `token.json`. Each list entry
and each flag becomes one `system` row,
`permission setting: <key>=<value> (from <path relative to the home>, file mtime)`,
where `<key>` is the JSON path in the file and a `trustedWorkspaces[]` entry
is `trustedWorkspace=<path>`. The rows are timestamped by the file's
modification time (the manifest's `mtime`, or the file's own without a
manifest), since none of the entries records when it was granted; their
`session_id` is empty, and the project file's rows and each trusted
workspace's row carry the folder as `project_path`. A `deny[]` list beside
each `allow[]` is read the same way; none was seen, so it is fixture only.
On Windows (**observed**, CLI 1.3.5) the one `trustedWorkspaces[]` entry was
an absolute Windows path, not a `file://` URI; the parser accepts both
(issue 92).

#### Model rows

The parser yields the model as a `system` row (issue 96): `model: <id>`
before the rows of the conversation's first step that a `gen_metadata`
row lists in `step_indices`, and `model: <old> -> <new>` before the rows
of each later step whose model differs, at the step's
`metadata.created_at`, with the new id in the `model` column. The id is
`chat_model.response_model`, else `model_display_name`. No step kind in
the parser's `SCHEMA` records a model switch. The macOS and Linux rounds
did not record the `response_model` values per conversation; on Windows
(**observed**, CLI 1.3.5 and app 2.23.1) each of the five conversations
yielded one `model` row and no change, with `gemini-3.8-flash-n` in every
one. So a model change within a conversation has not been observed; it
would show only as a different `response_model` on a later planner step.

#### Past-use rows and secondary sources

The conversation database is the store of record. `history.jsonl` (2
seconds) and the brain mirror (600 seconds, one copy per conversation in
the order of preference in the table) are secondary sources; each
summaries row is a `conversation summary` row of its own, so an app
conversation that CLI 1.3.5 also summarises yields two
([Summaries database](#summaries-database)). What each copy survives is in
[What survives a delete](#what-survives-a-delete); how history and mirror
rows pair with the database's, and which rows do not pair, is in
[section 9](#9-joins-and-timestamps).

#### Sync, relay and origin rows

Not stated.

#### Scratch directory rows

Not stated.

#### Deletion rows

Not stated.

#### Bad-line rows

A `steps.permissions` blob that does not decode is one `system` row,
`parser: the permissions of step <idx> could not be decoded`, and the
step's other rows stand (issue 92). A brain chunk can cut a line at a
chunk boundary ([section 7](#7-transcript-stores)).

#### Fixtures

Not stated.

## 14. Confidence

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
`~/.config/antigravity/plugin-secrets.json` on Linux (observed).

Medium:
the macOS and
Windows paths of `plugin-secrets.json` (inferred from Go's
`os.UserConfigDir()`, not observed; the Windows install used the
Credential Manager instead) and its contents (never observed); `antigravity-ide/conversations` and
`brain` (four community sources, no real install); the `Antigravity IDE`
app-dir name on macOS (inferred from the Windows and Linux names);
`knowledge/` sub-layout (one source); `.cache/antigravity` purpose.

Not determined: which of the observed app conversations belongs to which
task, on either install (modification times only,
[section 1](#1-source-and-evidence)); what a fired scheduled run
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
