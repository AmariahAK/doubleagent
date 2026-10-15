# chatgpt-desktop

OpenAI's ChatGPT desktop app. On Windows it now bundles Codex, OpenAI's
coding agent, whose state goes to `~/.codex` and is collected as
`codex-cli`; that half of the app is described in
[`codex-cli.md`](codex-cli.md), under
[Codex Desktop](codex-cli.md#codex-desktop-inside-the-chatgpt-app). No
analyzer research document exists: on the Windows install checked the app
keeps no local chat transcript to parse
([section 2](#2-per-user-storage)).

## 1. Source and evidence level

Closed source. Windows evidence is a **real install** (below); macOS
evidence is **DFIR write-ups and press** (DFIR is digital forensics and
incident response), and Linux has no app. No official OpenAI
documentation of on-disk paths was found.

**Observed (Windows)** (issues 113, 114, 115, 116): ChatGPT
`26.1007.9446.0`, observed 2026-10-15 in the author's Parallels lab VM,
Windows 11 ARM64 (ARM64 is the 64-bit Arm architecture; `ver` reports
`10.0.26300.9550`), one user, no WSL (Windows Subsystem for Linux)
distribution. The user downloaded `ChatGPT Installer.exe` (813,088 B)
from the vendor, which installed the app from the Microsoft Store as an
MSIX package (the Windows app package format; each package gets a
per-user data directory under `%LOCALAPPDATA%\Packages\<package family
name>`). The package is `OpenAI.Codex`, version `26.1007.9446.0`, package
family name `OpenAI.Codex_2p2nqsd0c76g0`, display name `ChatGPT`,
installed under `C:\Program Files\WindowsApps\OpenAI.Codex_26.1007.9446.0_arm64__2p2nqsd0c76g0`.
The `OpenAI.ChatGPT-Desktop_*` package family the write-ups describe does
not exist on this install, so the collector without the new lines found nothing
of the app beyond `~\.codex`. Its `AppxManifest.xml` (the package's
manifest) declares two applications, `App` (`app/ChatGPT.exe`) and
`CodexCoreCommandRunner` (`app/resources/codex-command-runner.exe`), and
the capabilities `runFullTrust`, `unvirtualizedResources`,
`packagedServices`, `localSystemServices`, `internetClient`,
`graphicsCaptureProgrammatic` and `graphicsCaptureWithoutBorder`.

The app is a Chromium build, not Electron (Electron is the desktop
framework built on Chromium and Node.js that most agent apps use):
`app/` holds `ChatGPT.exe` (3.4 MB, product version `155.0.8059.40`),
`chrome.dll` (311 MB, the same version), `chrome_elf.dll`,
`chrome_proxy.exe`, `chrome_pwa_launcher.exe`, `elevation_service.exe`,
`notification_helper.exe`, `Codex.exe` (20 KB) and
`owl-shell-runtime.json`; the resources also carry `owl-app.ini` and
`owl-electron-app.json`, so the web layer is an Electron-style app hosted
in that shell ("owl" is the shell's name in these file names; nothing
more about it was determined). `app/resources/` holds `app.asar`
(567 MB, the web app's archive), the bundled Codex as `codex.exe`
(282,678,064 B) and a Linux `codex` binary, `codex-code-mode-host.exe`,
`codex-command-runner.exe`, `codex-windows-sandbox-service.exe`,
`codex-windows-sandbox-setup.exe`, `rg.exe` (ripgrep), and the
directories `cua_node/`, `plugins/`, `skills/` and `tectonic/`. The
bundled Codex reports itself in its transcripts as `originator`
`Codex Desktop`, `cli_version` `0.162.0-alpha.17.2`.

The user, in the app: asked a question in a plain chat, generated an
image, and ran a coding task in a project folder; an attempt to create an
automation failed with an unspecified error. After a first survey
(14:48Z) the user subscribed the account to ChatGPT Plus (the paid
plan), created a scheduled automation, which saved this time, and
connected a demo GitHub account with no repositories; a second survey
followed at 15:30Z. No listing was taken between the tasks of each
round, so which file each task wrote is by modification time only (all
times UTC):

- Install and first launch (14:09Z to 14:12Z): the package's data
  directory, `~\.codex`, the binaries under
  `%LOCALAPPDATA%\OpenAI\Codex` and the runtime under
  `~\.cache\codex-runtimes` ([section 2](#2-per-user-storage)).
- Onboarding (14:24Z to 14:26Z): the sandbox account passwords in
  `~\.codex\.sandbox-secrets\sandbox_users.json`, the sandbox logs, and a
  78-byte `Desktop\Note from ChatGPT.txt` written by the onboarding task
  the app's state names `desktop_note`.
- Two local Codex threads, both rollouts under `~\.codex\sessions`: one
  at 14:26Z with its working directory in the app's default output
  directory `~\Documents\Codex\2026-10-15\d`, and one at 14:30Z to
  14:32Z in `~\Desktop\Demo`, which wrote eleven files into
  `Desktop\Demo\hello-worlds\`. The second is the project task. Which
  user action the first was is not determined from the files.
- The plain chat and the image generation (the ChatGPT chat surface):
  **no local transcript**. The chat exists locally only as a thread
  binding and a resume token in `~\.codex\.codex-global-state.json`, one
  title-only row in `~\.codex\sqlite\codex-dev.db`, and whatever the
  profile's `app://` IndexedDB blob holds (not determined). The browser
  `History` databases of the profile and both partitions have no URL
  rows, and no generated image was written under the package or
  `~\.codex`. The `codex-mcp-app-sandbox%3Ashared` partition was created
  at 14:40:39Z, during this use.
- The first automation attempt: nothing written (the `automations` and
  `automation_runs` tables of `codex-dev.db` stayed empty).
- The Plus subscription (about 15:22Z): no file of its own. `auth.json`
  was rewritten with the same keys (the token refresh), and
  `models_cache.json` grew from 5 to 9 models.
- The scheduled automation (15:25Z to 15:26Z): `~\.codex\automations\`
  with a `.run-jitter-salt` file and one `<slug>\automation.toml`, one
  row in `codex-dev.db` `automations` (status `ACTIVE`, kind
  `heartbeat`, a weekday `rrule`), and at once its target thread: a
  third rollout with its working directory in a new
  `~\Documents\Codex\2026-10-15\new-chat\` output directory, one
  user turn (the automation's prompt) and one assistant message, on a
  different model than the two earlier threads. The automation had not
  fired by the second survey (`automation_runs` empty). The same minute
  the app wrote `~\.codex\ambient-suggestions\<40 hex>\ambient-suggestions.json`.
  In the package only the `app://` IndexedDB (a second blob), `Local State`,
  `Network\Cookies` and a few network and Sentry files were rewritten.
- The GitHub connection: **nothing written locally**. No `.gitconfig`,
  `.git-credentials`, `.ssh`, `gh` configuration or GitHub directory
  appeared, Windows Credential Manager (`cmdkey /list`) held no
  credential, and no other file changed: the connection is a connector
  on the ChatGPT account, server-side.
- Not exercised: a resumed thread, a denied tool call, an "allow always"
  grant, a model switch within a thread, remote control, an automation
  run.

The collector was run live in the VM as the user (an administrator): collector
1.12.0 from `main` before these changes at 14:51Z (only `codex-cli`, 34 files, no project
found, issue 114), then a scratch copy with the catalog lines of
[section 2](#2-per-user-storage) at 14:58Z, which collected 520 files as
`chatgpt-desktop`, 23 excluded and 44 `error_copy`
([section 3](#3-credentials)). A third run, collector 1.12.0 from `main`
at 15:31Z after the second round, collected 42 files of `~\.codex`, 4
`error_copy` (the three thread locks and `.sqlite-maintenance.lock`) and
still no project. Besides files, the install created the
registry key `HKLM\Software\OpenAI\Codex\WindowsSandboxService`, a
`codex` protocol handler under `HKCU\Software\Classes`, a running
service `CodexSandboxService.OpenAI.Codex` and two enabled local accounts
`CodexSandboxOffline` and `CodexSandboxOnline`; services, accounts and
processes are the EDR's job (the endpoint detection and response tool
the responder already has) and are not collected.

**macOS** (not observed on any real install): the native Swift app keeps
its data in `~/Library/Application Support/com.openai.chat/`;
conversations were plain JSON in `conversations-{uuid}/` until
1.2024.171 and are encrypted since, in `conversations-v2-{uuid}/`
([pvieito.com, ChatGPT unprotected conversations](https://pvieito.com/2024/07/chatgpt-unprotected-conversations);
[9to5mac.com, 2024-07-03 ChatGPT Mac app report](https://9to5mac.com/2024/07/03)).
Whether the 2026 macOS app also bundles Codex, and where it would keep
that state beyond `~/.codex`, is not determined. **Linux**: no official
app.

**Previous Windows package** (not observed): the
`OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0` package of 2024 and 2025, an
Electron-style app whose data was under `LocalCache\Roaming\ChatGPT\`
([garr3ttmjo/Digital-Forensic-Report-Writeups](https://github.com/garr3ttmjo/Digital-Forensic-Report-Writeups)
"ChatGPT Desktop Forensics", examined 2025-01-23;
[arXiv 2505.23938](https://arxiv.org/abs/2505.23938), October 2024
release, no exact paths). Its catalog lines stay for installs that still
have it.

## 2. Per-user storage

**Windows, `OpenAI.Codex` package** (observed). The package's data
directory is `<pkg>` = `%LOCALAPPDATA%\Packages\OpenAI.Codex_2p2nqsd0c76g0`
(`AppData/Local/Packages/OpenAI.Codex_*` in the catalog). The standard
MSIX subdirectories `AC\`, `AppData\`, `LocalState\`, `RoamingState\`
and `TempState\` are empty; `SystemAppData\Helium\` is Windows' own. The
app writes:

| Path under `<pkg>` | What it holds | Catalog |
| --- | --- | --- |
| `LocalCache\Roaming\Codex\web\Codex\Default\` | The Chromium profile (the directory a Chromium browser keeps one user's state in), 682 files, 4.3 MB: `Preferences`, `Secure Preferences`, `History` (no `urls` or `visits` rows), `Top Sites`, `Web Data`, `Login Data` and `Login Data For Account` (no rows), `Network\Cookies`, LevelDB stores (LevelDB is the key-value store Chromium keeps web storage in) under `Local Storage\leveldb`, `Session Storage`, `Sync Data\LevelDB` and others, and `IndexedDB\app_-_0.indexeddb.leveldb` (IndexedDB is the database a web page keeps structured data in) with a 264,598-byte blob: the only origin is `app://`, the scheme the app's UI is served from. No `https_chatgpt.com_0` origin exists, unlike the previous package | collected |
| `...\Default\Partitions\codex-browser-app\`, `...\Default\Partitions\codex-mcp-app-sandbox%3Ashared\` | Two storage partitions (Chromium's isolated storage for an embedded web view), each a full profile of the same shape: the in-app browser the agent drives, and the sandbox in which MCP apps' web pages run (MCP is the Model Context Protocol, through which an agent calls external tools) | collected |
| `LocalCache\Roaming\Codex\web\Codex\Local State` | The user-data directory's state (the user-data directory is the directory holding a Chromium browser's profiles): `os_crypt.encrypted_key`, the profile list, and `variations_google_groups` keyed by the three profile and partition names | collected, secret |
| `...\web\Codex\Last Version`, `statsig-state.json`, `.codex-tpp-local-executor-installation-id` | The Chromium version string; the Statsig stable id (Statsig is a feature-flag service); an installation id (what "tpp" stands for is not determined) | collected |
| `...\web\Codex\` other children | `sentry\` (Sentry, the crash and event reporting service: `scope_v3.json` with 200 breadcrumbs, `session.json`), `Crashpad\` (Chromium's crash reporter, empty), `component_crx_cache\` (59 MB), `DeferredBrowserMetrics\` (4 MB), shader and GPU caches, `first_party_sets.db`, `segmentation_platform\`, `Last Browser`, `lockfile`, and twenty Chromium component directories such as `CertificateRevocation`, `OptimizationHints`, `WasmTtsEngine` (23 MB) and `WidevineCdm` (20 MB): 1,066 files and 169 MB in all with `Default` | not matched |
| `LocalCache\Local\Codex\Logs\<yyyy>\<mm>\<dd>\codex-desktop-<uuid>-<pid>-t<n>-i1-<hhmmss>-0.log` | The app's own log, one line per event: `<ISO 8601 UTC time> <level> <event or [component]> key=value ...`; 1,551 lines on the install, mostly `[AppServerConnection]` and `[electron-message-handler]`, naming the Codex binary paths and the app-server connection | collected |
| `Settings\settings.dat` and its `.LOG1`, `.LOG2`, `roaming.lock` | The package's MSIX settings hive (a registry hive Windows keeps per package) | collected |

Elsewhere in the profile (observed, not collected,
[section 4](#4-exclusions)):

- `%LOCALAPPDATA%\OpenAI\Codex\` (2,371 files, 600 MB):
  `bin\<hash>\` copies of `codex.exe`, `codex-code-mode-host.exe`,
  `codex-command-runner.exe`, `codex-windows-sandbox-setup.exe` and
  `rg.exe` (the same bytes as in the package; the log's
  `copiedRuntimeLocation=true source=copied` says the app copies them
  out), and `runtimes\cua_node\<hash>\`, a Node.js runtime for the
  computer-use agent (CUA, the agent mode that drives the desktop).
- `~\.cache\codex-runtimes\codex-primary-runtime\` (22,306 files,
  1.27 GB): `dependencies\` with a Git for Windows tree, a PowerShell 7,
  Node.js with 201 packages and Python, `plugins\openai-primary-runtime\`
  (the documents, PDF, presentations, spreadsheets and template-creator
  plugins: manifests, `SKILL.md` files and assets) and `runtime.json`.
  The same plugin tree is under `~\.codex\plugins\cache`.
- `~\Documents\Codex\<date>\<letter>\{outputs,work}\`: the default
  output directory of a thread with no project (empty on the install).
- `%LOCALAPPDATA%\Temp\`: 42 `.tmp<6 chars>` directories (the sandbox's
  and plugins' scratch), three `<uuid>.tmp.wav` and four `<uuid>.tmp`
  files.
- No `AppData\Roaming\ChatGPT`, `AppData\Roaming\OpenAI`,
  `AppData\Local\ChatGPT`, `AppData\Local\Programs\ChatGPT`,
  `.config` or `.local` directory, and no reparse point (symlink or
  junction) under `.codex`, `.cache`, the package or
  `%LOCALAPPDATA%\OpenAI`.

`~\.codex`, 9,155 files on the install, is the bundled Codex's home; its
desktop-only files are in
[Codex Desktop](codex-cli.md#codex-desktop-inside-the-chatgpt-app),
among them `automations\<slug>\automation.toml`, one file per scheduled
automation (its kind, status, `rrule` recurrence rule, prompt and target
thread), and `ambient-suggestions\<40 hex>\ambient-suggestions.json`, the
app's suggested tasks for a project root. Both are collected as
`codex-cli`.

**Windows, previous package** (write-up, not observed): root
`%LOCALAPPDATA%\Packages\OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0\LocalCache\Roaming\ChatGPT\`,
chat history in `IndexedDB\https_chatgpt.com_0.indexeddb.leveldb\`
(persisting between sessions, removed on logout), session ids and
timestamps in `Local Storage\leveldb\`, and the standard Chromium
siblings (garr3ttmjo). The package's `LocalState\` may hold app
settings (MSIX convention, not cited).

**macOS** (write-ups, not observed): `~/Library/Application Support/com.openai.chat/`
with `conversations-v2-{uuid}/` (pvieito; 9to5mac). Expect also
`~/Library/Caches/com.openai.chat/`,
`~/Library/Preferences/com.openai.chat.plist` and
`~/Library/HTTPStorages/com.openai.chat/` (the standard layout of a
non-sandboxed app; not cited, medium).

No environment variable relocates the data on any platform.

## 3. Credentials

- Windows, `OpenAI.Codex` (observed): `Network\Cookies` and
  `Cookies-journal` in `Default` and in each partition (the Chromium
  cookie database), and `Login Data`, `Login Data For Account` (no rows
  on the install). They are encrypted with the key in the user-data
  directory's `Local State` `os_crypt.encrypted_key` (372 characters),
  itself wrapped with DPAPI, the Windows Data Protection API, which binds
  a secret to the user account. All are flagged `secret: true`. While
  the app runs, `Cookies` and `Cookies-journal` cannot be copied (the
  app holds a byte-range lock), nor can any LevelDB `LOCK` file or the
  `Settings\settings.dat*` hive: 44 `error_copy` rows on the install,
  the same classes the Antigravity desktop app shows. Close the app or
  collect from an image to get them.
- The bundled Codex's credentials are in `~\.codex`: `auth.json` (OAuth
  tokens), `.sandbox-secrets\sandbox_users.json` (the passwords of the
  two sandbox accounts) and `.codex-global-state.json` (ChatGPT
  conversation resume tokens and prompt history); see
  [section 3 of `codex-cli.md`](codex-cli.md#3-credentials).
- Windows, previous package (write-up): `Network\Cookies` with
  `Local State`; `Local Storage\leveldb` holds session identifiers. No
  plaintext token file reported.
- macOS (write-up): the conversation encryption key is the Keychain item
  `com.openai.chat.conversations_v2_cache` (the Keychain is the macOS
  credential store) (pvieito). Sign-in tokens are expected in the
  Keychain too (not cited).
- No config file embeds an API key; the app uses account sign-in.
- Connecting a GitHub account (observed 2026-10-15) wrote no credential
  or configuration on the host: no `.git-credentials`, `.gitconfig`,
  `.ssh`, `gh` configuration or Credential Manager entry. The connection
  lives on the ChatGPT account, so the GitHub access the app had is not
  visible in a collection.

## 4. Exclusions

Windows, `OpenAI.Codex`: in `Default` and in every
`Default\Partitions\<partition>`, the Chromium caches `Cache` (13.7 MB in
`Default`), `Code Cache`, `GPUCache` (5.8 MB), `DawnGraphiteCache`,
`DawnWebGPUCache`, `blob_storage` (4.6 MB, one long ASCII line),
`Service Worker\CacheStorage` and `Service Worker\ScriptCache`, and
`Extensions` (a bundled browser extension, 90 files and 400 KB, copied
into each profile; its purpose was not determined). Each is a
`*/Roaming/Codex/web/Codex/Default/...` exclusion and a
`.../Default/Partitions/*/...` one.

Not catalogued, so not collected and not listed in the manifest:

- The other children of `web\Codex\`: the Chromium component
  directories, `component_crx_cache`, `DeferredBrowserMetrics`, the
  shader and GPU caches, `sentry` and `Crashpad` (crash and event
  reporting state, the precedent being the Claude Desktop exclusion
  `*/Claude*/sentry`) and `Last Browser`. The catalog names `Default`
  and four files beside it instead of the whole directory, so these need
  no exclusion each; the scratch run that collected the whole directory
  with only the caches excluded took about 25 MB of them beside the
  4 MB profile.
- `%LOCALAPPDATA%\OpenAI\Codex`: binaries and a Node.js runtime only.
- `~\.cache\codex-runtimes`: the 1.27 GB runtime (Git, Node.js, Python,
  PowerShell) and plugin manifests also present under `~\.codex`.
- `%LOCALAPPDATA%\Temp` scratch directories and files: no stable name to
  catalogue.

Previous package: `*/Roaming/ChatGPT/Cache`, `Code Cache`, `GPUCache`,
`DawnGraphiteCache`, `DawnWebGPUCache`. macOS:
`Library/Caches/com.openai.chat`, which no catalog line names.

## 5. Project-local files

The app writes none of its own into a project. The bundled Codex writes
what Codex writes (see [`codex-cli.md`](codex-cli.md)); the observed
project task wrote only the files it was asked for. Outside projects,
onboarding wrote `Desktop\Note from ChatGPT.txt`, and a thread with no
project gets `~\Documents\Codex\<date>\<letter>\`.

## 6. Where the project path is recorded

Nothing under the package records a project path that the collector
reads. The bundled Codex records each thread's working directory in its
rollouts' `session_meta` `cwd`, which project discovery already reads
(Codex, "Session rollouts"); on the install both threads' directories
appear there. The desktop app also records projects in
`~\.codex\.codex-global-state.json` (`local-projects` `rootPaths`,
`thread-workspace-root-hints`, `thread-projectless-output-directories`)
and in `~\.codex\state_5.sqlite` `project_roots`; see
[section 6 of `codex-cli.md`](codex-cli.md#6-where-the-project-path-is-recorded).
The PowerShell collector's live run found no project because it could
not open the rollouts the running app held (issue 114, fixed in
collector 1.12.0).

## 7. Confidence

High (observed on Windows 11, ChatGPT 26.1007.9446.0): the package name
and layout, the catalog lines, exclusions and secret globs of
[section 2](#2-per-user-storage) to [section 4](#4-exclusions), that the
chat surface keeps no local transcript, and the locked-file failures.
High (write-ups): the macOS `conversations-v2-*` encryption and the
previous Windows package's layout. Medium: the macOS Caches, Preferences
and HTTPStorages directories (convention, uncited). Not determined: the
2026 macOS layout and whether the macOS app bundles Codex; what the
`app://` IndexedDB blob and `Local Storage` hold; the bundled
extension's purpose; what "tpp" and "owl" stand for; the app's behaviour
on x64 Windows (only ARM64 was observed); which of the user's actions
wrote the first Codex thread.
