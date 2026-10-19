# chatgpt-desktop

OpenAI's ChatGPT desktop app. On Windows and macOS it now bundles Codex,
OpenAI's coding agent, whose state goes to `~/.codex` and is collected as
`codex-cli`; that half of the app is described in
[`codex-cli.md`](codex-cli.md), under
[Codex Desktop](codex-cli.md#codex-desktop-inside-the-chatgpt-app). On
the Windows and macOS installs checked the app keeps no local chat
transcript ([section 2](#2-per-user-storage)), and a reply to a ChatGPT
conversation from inside the app (build 26.1013.40934 on macOS,
2026-10-18) left none either. The one local trace of the account's
ChatGPT conversations, the `chatgpt` rows of `~/.codex/sqlite/codex-dev.db`
`local_thread_catalog`, and how the analyzer reads them are in
[`analyzer/research/chatgpt-desktop.md`](../../analyzer/research/chatgpt-desktop.md).

OpenAI's ChatGPT desktop app is a closed-source Electron app (Electron:
a desktop framework that runs a web user interface in a bundled
Chromium) that on Windows and macOS
bundles Codex, OpenAI's coding agent. The app's prompt box, the
composer, has a mode dropdown with two entries (build 26.1013.40934 on
macOS, 2026-10-18): **Codex** mode starts a local Codex thread, whose
rollout (Codex's JSONL transcript) goes to `~/.codex/sessions` and is
read by the `codex-cli` parser ([`codex-cli.md`](codex-cli.md)); the
**ChatGPT** entry lists the account's conversations on chatgpt.com,
OpenAI's web chat service. A ChatGPT-mode conversation keeps its text on
OpenAI's servers and leaves no transcript on disk. This document covers
the one local trace it does leave: a row in the app's own database,
`~/.codex/sqlite/codex-dev.db`, which the `chatgpt-desktop` parser
turns into timeline rows. Paths, credentials and exclusions are in
[`collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md).
[Issue 49](https://github.com/seanthegeek/doubleagent/issues/49) tracks
the parser.

<!-- MERGE: dedupe the intro paragraphs above into one -->

## 1. Source and evidence

Closed source. Windows and macOS evidence is a **real install** of each
(below); the former native macOS app and the previous Windows package
rest on **DFIR write-ups and press** (DFIR is digital forensics and
incident response), and Linux has no app. No official OpenAI
documentation of on-disk paths was found.

Closed source, so there are no commit links, and the app's client code is
not in the Codex repository: a search of the Codex source for
`codex-dev.db`, `local_thread_catalog`, `conversation_origin` and
`chatgpt_async_status` finds nothing
([section 13 of `codex-cli.md`](codex-cli.md#13-parser-plan)).
Every claim below is from a real install, read for file names, sizes,
table and column names, value types, enum values and row counts only;
no conversation title or id from an install is reproduced here.

<!-- MERGE: dedupe the section 1 prose above -->

### Observed

- macOS, 2026-10-18 (issues 49, 149, 160): ChatGPT `26.1013.40934`
  (bundle id `com.openai.codex`, `Codex Framework` `155.0.8059.80`) with
  the bundled Codex `0.163.0-alpha.10.2` (`originator` `Codex Desktop`),
  observed from 2026-10-18 18:15Z to 2026-10-19 00:43Z in the author's
  macOS lab VM of the 2026-10-15 round (macOS 26.6.2 build 25G83, arm64,
  64-bit Arm, one user, no Python and no Xcode Command Line Tools).
  Unlike the round of 2026-10-15, the user performed one step at a time
  and a listing of names, sizes and modification times was taken and
  diffed after each, so every bullet below says what that step wrote.
  The terms, as build 26.1013.40934 presents them on 2026-10-18:

  - The composer (the prompt box) has a mode dropdown with **Codex**,
    which runs a local Codex thread with a rollout (the Codex transcript
    file) under `~/.codex`, and **ChatGPT**, which lists the account's
    chatgpt.com conversations. Every thread of this round was started in
    Codex mode.
  - A **projectless output directory** is
    `~/Documents/Codex/<date>/<slug>/` with `work/` and `outputs/`: the
    working directory the app gives a thread that belongs to no project.
  - **Approve for me** is a permission mode in which a reviewer model,
    not the user, answers the agent's approval requests. The app stores
    it as the agent mode `guardian-approvals` and the reviewer
    `auto_review`, and each decision runs as a separate
    **guardian review** thread on the model `codex-auto-review` ("guardian" is the
    app's internal name for the reviewer).
  - **Full access** is the access level that turns the sandbox off
    (`approval_policy` `never`, sandbox `danger-full-access`).
  - A **heartbeat** is the kind of scheduled task the app creates: at
    each run the model carries out the prompt and decides whether to
    notify the user.
  - **Remote control** (Settings > Connections > Control this Mac or PC)
    lets a paired ChatGPT phone app drive the desktop's local threads
    through a relay at chatgpt.com
    ([Remote connections | ChatGPT Learn](https://learn.chatgpt.com/docs/remote-connections),
    read 2026-10-18).

  What each step wrote (times UTC):

  - Install and first launch, not signed in (the installer disk image,
    848,907 B, downloaded at 18:15:19Z; first launch 18:17:26Z; listing
    at 18:21:29Z): every `~/Library` entry of
    [section 2](#2-per-user-storage) and `~/.codex` existed before any
    sign-in. Under `Library/Application Support/Codex/` the Chromium
    profile (the directory a Chromium browser keeps one user's state in)
    already had a 20 KB `Cookies`,
    `artifact-sessions/runtime-generations/` held empty directories
    (collected), and `sentry/` held `scope_v3.json` (119 KB),
    `session.json` and `queue/`. The Chromium HTTP cache was under
    `Library/Caches/Codex/Default/`, not in the profile. `~/.codex` held
    `.codex-global-state.json` (1,282 B, no resume token), `config.toml`
    (2,114 B), `installation_id`, `ipc/ipc.sock`, `sqlite/codex-dev.db`,
    `state_5.sqlite`, `logs_2.sqlite` (1,000 rows before sign-in),
    `goals_1.sqlite`, `memories_1.sqlite`, `queue_1.sqlite` and the
    plugin trees, and no `auth.json`, `sessions/`, `history.jsonl`,
    `models_cache.json` or `version.json`. Outside both,
    `~/.cache/codex-runtimes/codex-primary-runtime/` (32,625 entries) is
    not collected. No launchd agent or daemon and no keychain item; the
    defaults domains (preference domains) are `com.openai.codex`,
    `com.openai.codex.installer` and `com.openai.sky.CUAService`.
  - Idle before sign-in (18:21Z to 18:31Z): Chromium component updates
    under `Library/Application Support/Codex/` (`WasmTtsEngine` 25 MB
    among them, none matched by a catalog line) and the update check of
    Sparkle (the macOS update framework) at 18:22:31Z
    (`Library/Caches/com.openai.codex/`,
    `Library/HTTPStorages/com.openai.codex` and its `.binarycookies`).
  - Sign-in (18:31:28Z to 18:32:34Z, listing at 18:33:09Z):
    `~/.codex/auth.json` (4,299 B), `models_cache.json` (399,712 B),
    `.sandbox_migration`, the first shell snapshot
    `shell_snapshots/<uuid>.<ns>.sh` (2,135 B, see
    [section 3](#3-credentials)), an `ambient-suggestions` file, and
    `cache/codex_apps_server_info/` and `cache/codex_apps_tools/`
    (825,347 B, under the excluded `.codex/cache`). The global state
    grew to 110,327 B and `config.toml` to 2,380 B. `codex-dev.db`
    `local_thread_catalog` gained three `source_kind` `chatgpt` rows
    before any chat in this VM: the account's conversations from the
    Windows round of 2026-10-15, so signing in lists the account's
    ChatGPT conversations locally. The storage partition (Chromium's
    isolated storage for an embedded web view)
    `codex-mcp-app-sandbox%3Ashared` was created at 18:32:05Z and
    `executor-plugins/codex-app-tools/` was filled in. Two sockets
    `/private/tmp/codex-browser-use/<uuid>.sock` appeared outside the
    home. Still no keychain item.
  - A plain question in a new chat, no tools (18:40:09Z to 18:40:31Z,
    listing at 18:40:59Z): a **local Codex thread**, unlike the plain
    chat of 2026-10-15: a rollout under `~/.codex/sessions/2026/10/18/`
    (190,766 B, 21 lines), a `session_index.jsonl` line, a new
    `thread_history_1.sqlite`, rows in `state_5.sqlite` and
    `codex-dev.db`, a thread lock, `computer-use/config.json` (152 B)
    and the projectless output directory
    `~/Documents/Codex/2026-10-18/w/`. No `history.jsonl` was written;
    the prompt is kept in the global state's `prompt-history`.
  - The project folder `~/Demo` added with the folder picker (18:48:52Z
    to 18:48:59Z) and a coding task in it (18:49:06Z to 18:50:51Z,
    listing at 18:58:11Z): `config.toml` gained a
    `[projects."<project path>"]` table with `trust_level` `trusted` (a
    standing trust grant for the folder), `state_5.sqlite` a `projects`
    and a `project_roots` row, the global state `local-projects`, and
    `Preferences/com.openai.codex.plist` grew from 328 to 1,088 B with
    `NSOSPLastRootDirectory` (the open panel's last directory, the
    folder picked). The task wrote three files into `~/Demo` at
    18:50:40Z and no project-local file (no `.codex`, `.git` or
    `AGENTS.md`); it left a second rollout (205,378 B, 39 lines), a
    second `ambient-suggestions` directory (one per project root) and
    `recent-workspace-files-v3` entries naming the three files.
  - Two approval requests in the `~/Demo` thread (19:03:50Z to
    19:05:03Z, listing at 19:06:30Z): a `curl` the user declined
    (19:04:01Z) and a write to `~/Desktop` the user approved
    (19:05:00Z). The approval dialog of build 26.1013.40934 offers no
    "always allow" choice. Neither decision is in the rollout; both are
    rows in `~/.codex/logs_2.sqlite`, and nothing else changed besides
    the rollout, the SQLite write-ahead logs and one global-state key.
  - A model switch (21:25:09Z), Approve for me (21:25:28Z) and a prompt
    to write a guide to the Desktop (21:26:40Z to 21:27:32Z, listing at
    21:33Z): the only new files were a third rollout (105,545 B, 17
    lines), the guardian review thread that approved the write, and its
    lock. The agent wrote `~/Documents/gpt-models-guide.md` (5,042 B),
    not the `~/Desktop` it was asked for. `config.toml` did not change:
    the mode is kept in the global state (`agent-mode-by-host-id`,
    `permission-selection-by-host-id:local`,
    `preferred-non-full-access-agent-mode-by-host-id`,
    `heartbeat-thread-permissions-by-id`) and the model in
    `composer-recent-model-configurations-v1` and `state_5.sqlite`
    `threads`.
  - Quit, relaunch (21:45:36Z) and the `~/Demo` thread resumed
    (21:46:06Z) with one prompt (21:47:36Z to 21:47:45Z, listing at
    21:49Z): the turn went into the same rollout, and the model and the
    mode survived the restart. Quit removed the locks of the threads not
    open and the old shell snapshots and checkpointed the SQLite stores;
    the relaunch wrote two new snapshots for the resumed thread,
    `cache/remote_plugin_catalog/<16 hex>.json` (38,747,166 B, under the
    excluded `.codex/cache`), `browser-sidebar-page-states.json`, and a
    lock for a prewarmed guardian session that never wrote a rollout
    (see
    [Codex Desktop inside the ChatGPT app in `codex-cli.md`](codex-cli.md#codex-desktop-inside-the-chatgpt-app)).
    Each launch makes new sockets under `/private/tmp/codex-app-tools/`
    and `/private/tmp/codex-browser-use/` and a
    `com.openai.codex.<6 chars>/` directory in the user's temporary
    directory under `/private/var/folders`.
  - Full access for one prompt (set at 21:52:30Z, turn 21:53:27Z to
    21:53:33Z, set back by the user at 21:53:38Z, listing at 21:56Z): no
    new file, and no file outside the rollout and `logs_2.sqlite` kept
    the full-access state once it was set back. The app does not revert
    full access on its own; it stays until the user changes it.
  - A reply, in ChatGPT mode, to an existing chatgpt.com conversation
    (about 22:02Z to 22:15Z, listing at 22:20Z): **nothing written
    locally** beyond a composer draft in the global state and
    model-cache and Chromium housekeeping. No rollout; the three
    `chatgpt` rows of `local_thread_catalog` kept their 2026-10-15
    update times, so that list is a snapshot taken at sign-in, not
    refreshed by use, and the profile's web storage has no chatgpt.com
    origin. The conversation exists only on the server.
  - chatgpt.com, checked by the user without a listing: the app's local
    threads do not appear among the account's Codex sessions, so local
    Codex threads are not uploaded in this build.
  - A scheduled task created in the sidebar's Scheduled view
    (23:18:38Z), run with Run now (23:19:26Z to 23:19:30Z, listing at
    23:22Z), and fired once on schedule (23:45:49Z to 23:45:53Z):
    `~/.codex/automations/.run-jitter-salt` (37 B),
    `automations/<slug>/automation.toml` (356 B), one `codex-dev.db`
    `automations` row, and a target thread in
    `~/Documents/Codex/2026-10-18/new-chat/` that both runs reported
    into. The user reported that scheduled tasks are not tied to a
    project and run only on an interval. The scheduled run decided not
    to notify the user and wrote no `automation_runs` or `inbox_items`
    row
    ([Scheduled tasks | ChatGPT Learn](https://learn.chatgpt.com/docs/automations)
    describes the feature, read 2026-10-18).
  - Remote control (2026-10-18 23:50:17Z to 2026-10-19 00:31Z, listings
    after each action): enabling it and pairing the ChatGPT iOS app
    wrote no file. It added one row to `~/.codex/state_5.sqlite`
    `remote_control_enrollments` (`websocket_url`, the relay on
    chatgpt.com; `account_id`; `app_server_client_name` `Codex Desktop`;
    `server_id`; `environment_id`; `server_name`, the Mac's host name;
    `updated_at`; `remote_control_enabled`) and two top-level
    global-state keys, `electron-local-remote-control-environment-id`
    and `codex-mobile-has-connected-device`. A prompt from the phone
    (23:59:14Z to 23:59:31Z) and one from a paired Android phone
    (00:29:14Z to 00:29:16Z) ran as turns of the existing local thread,
    marked only by their turn trigger (`remote_ios`, `remote_android`)
    and by the phones' connections in `logs_2.sqlite`, through which the
    phones also ran a command (`command/exec`) and read a file
    (`fs/readFile`) on the host outside any turn. Turning "Allow
    connections" off (00:05:42Z) and on (00:09:25Z) flipped
    `remote_control_enabled` in the same row; revoking the iPhone
    (00:14:36Z) and pairing the Android phone (00:23:10Z) left only
    `logs_2.sqlite` rows. The list of paired devices is on the server.
  - The first thread deleted with the app's own delete command
    (2026-10-19 00:36:02Z, listing at 00:40Z): a hard delete with no
    archive, which removed the rollout, its `session_index.jsonl` line
    and its rows in `state_5.sqlite`, `thread_history_1.sqlite` and
    `codex-dev.db`. The global state kept the thread's prompts,
    description, permissions and activity time and gained a deletion
    marker, `logs_2.sqlite` kept its rows, and the empty projectless
    output directory `~/Documents/Codex/2026-10-18/w/` remained. The
    delete dialog mentioned no remote copy.

  The sh collector 1.14.0 ran live in the VM as the user, not root, on
  2026-10-19 from 00:43:01Z to 00:43:21Z: 1 user with artifacts (47
  accounts listed), 2 projects (`~/Demo`, and
  `~/Documents/Codex/2026-10-18/new-chat`, the projectless output
  directory that project discovery took from the scheduled-task thread's
  rollout `cwd`; since collector 1.16.0 discovery drops it and the
  directory is collected as `codex-cli`, issue 149), 564 files and
  20,051,811 B collected, 28 `skipped_excluded`, none too large, 2
  `skipped_special` (`.codex/ipc/ipc.sock` and the group container's
  `IPC/computeruse.sock`), 1 `symlink`, 30 `error_read` rows for system
  accounts' homes under `/var` that a non-root run cannot list, exit 0,
  a 2,959,315 B archive. Manifest rows by agent: 537 `chatgpt-desktop`,
  58 `codex-cli` (every `~/.codex` file, the automations,
  `codex-dev.db`, `logs_2.sqlite` and the global state included, through
  the `codex-cli|.codex` line) and 30 with no agent (the `error_read`
  rows). The exclusions that fired are in [section 4](#4-exclusions);
  the largest files collected were the SQLite stores and the rollouts.
  Flagged `secret: true`: `.codex/auth.json`, `.codex/config.toml`, the
  global state and its `.bak`, the profile's and both partitions'
  `Cookies`, `Login Data` and `Login Data For Account` with their
  journals, and the two `.binarycookies`. Of the unflagged files whose
  names suggest a credential, only Chromium's `Trust Tokens` store
  remained, which is not one; the shell snapshots were collected
  unflagged, which collector 1.15.0 changes
  ([section 3](#3-credentials)).

- macOS, 2026-10-15 (issues 113, 121): ChatGPT `26.1007.71326`
  (`CFBundleShortVersionString`; `CFBundleVersion` `20398`), observed
  2026-10-15 (16:25Z to 17:05Z) in the author's macOS lab VM, macOS
  26.6.2 build 25G83, arm64 (64-bit Arm), one user, no Homebrew, Node.js
  or Python. `/Applications/ChatGPT.app` has the bundle identifier
  **`com.openai.codex`**, and its `Contents/Frameworks/` holds
  `Codex Framework.framework` (`com.openai.codex.framework`, version
  `155.0.8059.40`: the Electron framework under the app's own name, at
  the Chromium version of the Windows build) and `Sparkle.framework`
  2.9.1 (Sparkle is the macOS update framework). So the macOS app is the
  same Electron build as on Windows, not the native Swift app the 2024
  write-ups describe, and nothing under `~/Library` carries the old
  `com.openai.chat` identifier. Its version string is the `app_version`
  the Windows build's `codex-dev.db` records. `Contents/Resources/`
  holds `app.asar` (567,770,955 B), `codex-cli/` (the bundled Codex, run
  from `codex-cli/CodexCLI.app/Contents/MacOS/codex` according to the
  app log), `cua_node/`, `plugins/`, `skills/`, `rg`, `owl-app.ini`,
  `owl-electron-app.json` and `scripting.sdef`; a dock-tile plug-in
  `com.openai.codex.dock-tile-plugin` is under `Contents/PlugIns/`. The
  bundled Codex reports `originator` `Codex Desktop`, `cli_version`
  `0.162.0-alpha.17.2`, as on Windows. The user repeated the Windows
  rounds; no listing was taken between tasks:

  - Install and first launch (16:26Z):
    `~/Library/Application Support/Codex/` (the Chromium user-data
    directory), the other `~/Library` entries of
    [section 2](#2-per-user-storage), and `~/.codex`.
  - A plain chat and an image generation: no local transcript, as on
    Windows. `codex-dev.db` `local_thread_catalog` gained three
    `source_kind` `chatgpt` rows (one with `conversation_origin` `tpp`)
    and nothing else recorded them.
  - A task in the project folder `~/Demo` (16:39Z to 16:40Z) and a
    thread in the projectless output directory
    `~/Documents/Codex/2026-10-15/e` (16:50Z; which user action it was
    is not determined): one rollout each.
  - A scheduled automation (16:44Z):
    `~/.codex/automations/<slug>/automation.toml`, one `automations` row
    and its target thread in `~/Documents/Codex/2026-10-15/new-chat`.
    The `codex-browser-app` partition was created the same minute.
  - The standalone Codex CLI, installed with its shell installer and
    given one prompt in `~/demo2` (16:55Z to 16:56Z):
    `~/.codex/packages`, two `~/.local/bin` symlinks and a block in
    `~/.zprofile`; see
    [Codex Desktop](codex-cli.md#codex-desktop-inside-the-chatgpt-app).
  - No launchd agent or daemon, no `~/Applications` entry, and no item
    in the login keychain with an OpenAI, Codex or ChatGPT identifier
    (`security dump-keychain` listed 17 items; the old app's
    `com.openai.chat.conversations_v2_cache` item is absent).

  The sh collector from `main` (1.12.0 before the macOS lines) ran live
  as the user, not root, at 17:02Z: `users: 1`, 4 projects (`~/demo2`,
  `~/Demo` and the two output directories, since the sh `grep` reads
  rollouts the running app holds open), `codex-cli` 220 files (85.8 MiB,
  77 MB of it the computer-use app bundle), 9 excluded, 1 `symlink`, and
  30 `error_read` rows for system accounts' homes under `/var` that a
  non-root run cannot list (logged with "WARNING: not running as root").
  It collected nothing of the app outside `~/.codex` and
  `~/Library/Application Support/com.openai.codex`. A scratch copy with
  the macOS lines of the catalog, at 17:05Z: 497 collected, of which
  `chatgpt-desktop` 444 files and 4,990,271 B with 20 secret rows, 18
  excluded (among them `Codex Computer Use.app`, 76,967,936 B), 1
  `symlink` (the group container's `Application Scripts` link).

- Windows, 2026-10-15 (issues 113, 114, 115, 116): ChatGPT
  `26.1007.9446.0`, observed 2026-10-15 in the author's Parallels lab
  VM, Windows 11 ARM64 (ARM64 is the 64-bit Arm architecture; `ver`
  reports `10.0.26300.9550`), one user, no WSL (Windows Subsystem for
  Linux) distribution. The user downloaded `ChatGPT Installer.exe`
  (813,088 B) from the vendor, which installed the app from the
  Microsoft Store as an MSIX package (the Windows app package format;
  each package gets a per-user data directory under
  `%LOCALAPPDATA%\Packages\<package family name>`). The package is
  `OpenAI.Codex`, version `26.1007.9446.0`, package family name
  `OpenAI.Codex_2p2nqsd0c76g0`, display name `ChatGPT`, installed under
  `C:\Program Files\WindowsApps\OpenAI.Codex_26.1007.9446.0_arm64__2p2nqsd0c76g0`.
  The `OpenAI.ChatGPT-Desktop_*` package family the write-ups describe
  does not exist on this install, so the collector without the new lines
  found nothing of the app beyond `~\.codex`. Its `AppxManifest.xml`
  (the package's manifest) declares two applications, `App`
  (`app/ChatGPT.exe`) and `CodexCoreCommandRunner`
  (`app/resources/codex-command-runner.exe`), and the capabilities
  `runFullTrust`, `unvirtualizedResources`, `packagedServices`,
  `localSystemServices`, `internetClient`, `graphicsCaptureProgrammatic`
  and `graphicsCaptureWithoutBorder`.

  The app is a Chromium build, not Electron (Electron is the desktop
  framework built on Chromium and Node.js that most agent apps use):
  `app/` holds `ChatGPT.exe` (3.4 MB, product version `155.0.8059.40`),
  `chrome.dll` (311 MB, the same version), `chrome_elf.dll`,
  `chrome_proxy.exe`, `chrome_pwa_launcher.exe`,
  `elevation_service.exe`, `notification_helper.exe`, `Codex.exe` (20
  KB) and `owl-shell-runtime.json`; the resources also carry
  `owl-app.ini` and `owl-electron-app.json`, so the web layer is an
  Electron-style app hosted in that shell ("owl" is the shell's name in
  these file names; nothing more about it was determined).
  `app/resources/` holds `app.asar` (567 MB, the web app's archive), the
  bundled Codex as `codex.exe` (282,678,064 B) and a Linux `codex`
  binary, `codex-code-mode-host.exe`, `codex-command-runner.exe`,
  `codex-windows-sandbox-service.exe`,
  `codex-windows-sandbox-setup.exe`, `rg.exe` (ripgrep), and the
  directories `cua_node/`, `plugins/`, `skills/` and `tectonic/`. The
  bundled Codex reports itself in its transcripts as `originator`
  `Codex Desktop`, `cli_version` `0.162.0-alpha.17.2`.

  The user, in the app: asked a question in a plain chat, generated an
  image, and ran a coding task in a project folder; an attempt to create
  an automation failed with an unspecified error. After a first survey
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
    `~\.codex\.sandbox-secrets\sandbox_users.json`, the sandbox logs,
    and a 78-byte `Desktop\Note from ChatGPT.txt` written by the
    onboarding task the app's state names `desktop_note`.
  - Two local Codex threads, both rollouts under `~\.codex\sessions`:
    one at 14:26Z with its working directory in the app's default output
    directory `~\Documents\Codex\2026-10-15\d`, and one at 14:30Z to
    14:32Z in `~\Desktop\Demo`, which wrote eleven files into
    `Desktop\Demo\hello-worlds\`. The second is the project task. Which
    user action the first was is not determined from the files.
  - The plain chat and the image generation (the ChatGPT chat surface):
    **no local transcript**. The chat exists locally only as a thread
    binding and a resume token in `~\.codex\.codex-global-state.json`,
    one title-only row in `~\.codex\sqlite\codex-dev.db`, and whatever
    the profile's `app://` IndexedDB blob holds (not determined). The
    browser `History` databases of the profile and both partitions have
    no URL rows, and no generated image was written under the package or
    `~\.codex`. The `codex-mcp-app-sandbox%3Ashared` partition was
    created at 14:40:39Z, during this use.
  - The first automation attempt: nothing written (the `automations` and
    `automation_runs` tables of `codex-dev.db` stayed empty).
  - The Plus subscription (about 15:22Z): no file of its own.
    `auth.json` was rewritten with the same keys (the token refresh),
    and `models_cache.json` grew from 5 to 9 models.
  - The scheduled automation (15:25Z to 15:26Z): `~\.codex\automations\`
    with a `.run-jitter-salt` file and one `<slug>\automation.toml`, one
    row in `codex-dev.db` `automations` (status `ACTIVE`, kind
    `heartbeat`, a weekday `rrule`), and at once its target thread: a
    third rollout with its working directory in a new
    `~\Documents\Codex\2026-10-15\new-chat\` output directory, one user
    turn (the automation's prompt) and one assistant message, on a
    different model than the two earlier threads. The automation had not
    fired by the second survey (`automation_runs` empty). The same
    minute the app wrote
    `~\.codex\ambient-suggestions\<40 hex>\ambient-suggestions.json`. In
    the package only the `app://` IndexedDB (a second blob),
    `Local State`, `Network\Cookies` and a few network and Sentry files
    were rewritten.
  - The GitHub connection: **nothing written locally**. No `.gitconfig`,
    `.git-credentials`, `.ssh`, `gh` configuration or GitHub directory
    appeared, Windows Credential Manager (`cmdkey /list`) held no
    credential, and no other file changed: the connection is a connector
    on the ChatGPT account, server-side.
  - The standalone Codex CLI 0.162.1, installed beside the app at 15:38Z
    with OpenAI's PowerShell installer and given one prompt: it shares
    the app's `~\.codex` and the app's login (no new credential file),
    and adds its own binaries under `~\.codex\packages`; see
    [Standalone CLI on Windows](codex-cli.md#standalone-cli-on-windows).
  - Not exercised: a resumed thread, a denied tool call, an "allow
    always" grant, a model switch within a thread, remote control, an
    automation run.

  The collector was run live in the VM as the user (an administrator):
  collector 1.12.0 from `main` before these changes at 14:51Z (only
  `codex-cli`, 34 files, no project found, issue 114), then a scratch
  copy with the catalog lines of [section 2](#2-per-user-storage) at
  14:58Z, which collected 520 files as `chatgpt-desktop`, 23 excluded
  and 44 `error_copy` ([section 3](#3-credentials)). A third run,
  collector 1.12.0 from `main` at 15:31Z after the second round,
  collected 42 files of `~\.codex`, 4 `error_copy` (the three thread
  locks and `.sqlite-maintenance.lock`) and still no project. Besides
  files, the install created the registry key
  `HKLM\Software\OpenAI\Codex\WindowsSandboxService`, a `codex` protocol
  handler under `HKCU\Software\Classes`, a running service
  `CodexSandboxService.OpenAI.Codex` and two enabled local accounts
  `CodexSandboxOffline` and `CodexSandboxOnline`; services, accounts and
  processes are the EDR's job (the endpoint detection and response tool
  the responder already has) and are not collected.

- Former native macOS app (`com.openai.chat`): not observed; the
  evidence is write-ups
  ([Former native macOS app](#former-native-macos-app)).
- Previous Windows package (`OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0`): not
  observed; the evidence is a write-up
  ([Windows, previous package](#windows-previous-package)).
- Linux: no official app.

- macOS, ChatGPT 26.1013.40934, 2026-10-18: the author's macOS lab VM (macOS 26.6.2, build 25G83, arm64, one user), the app
  with its bundled Codex `0.163.0-alpha.10.2`, with a listing diff after
  every step; the full round is in
  [section 1 of `collectors/research/chatgpt-desktop.md`](#1-source-and-evidence)
  and [section 1 of `codex-cli.md`](codex-cli.md#1-source-and-evidence).
  What it showed of this table:
  - Before sign-in `codex-dev.db` already existed. Signing in
    (18:31:28Z to 18:32:34Z) wrote three `local_thread_catalog` rows with
    `source_kind` `chatgpt`, before any chat on that VM: the account's
    conversations, dated 2026-10-15, from the Windows round below, each
    with `display_title` set, `conversation_origin` empty twice and `tpp`
    once, `missing_candidate` 0, and `thread_source`, `model_provider`,
    `cwd`, `git_branch`, `project_id`, `trial_conversation_type` and
    `chatgpt_async_status` NULL. The conversations of the 2026-10-15
    macOS round below were not among them; why was not determined.
    `local_thread_catalog_hosts` gained two rows and
    `local_thread_catalog_sync_state` two
    ([section 10](#10-other-stores)).
  - A plain question in Codex mode (18:40:09Z to 18:40:31Z) added a row
    with `source_kind` `vscode`, `thread_source` `user` and the thread's
    `cwd`: the catalog lists the app's Codex threads too.
  - A reply, in ChatGPT mode, to one of the listed conversations (about
    22:02Z to 22:15Z) wrote nothing to the Codex stores: no rollout, no
    new row, and the three `chatgpt` rows kept their 2026-10-15
    `source_updated_at`. In that window `logs_2.sqlite`, the app server's
    log, held only `account/read`, `getAuthStatus`, `config/read` and
    `configRequirements/read` requests: the conversation never passed
    through the local app server (Codex's local service that owns the
    threads). The Chromium profile had no chatgpt.com origin directory.
  - Deleting the Codex-mode plain question with the app's own command
    (2026-10-19 00:36:02Z) removed that thread's `vscode` row with its
    rollout; the `chatgpt` rows stayed.
  - The user reported that the app's Codex-mode threads did not appear
    in the Codex area of chatgpt.com.
  - The sh collector 1.14.0, run live as the user (2026-10-19 00:43:01Z
    to 00:43:21Z), attributed `sqlite/codex-dev.db` to `codex-cli`.
- macOS, ChatGPT 26.1007.71326, 2026-10-15: the same VM, the earlier
  build with Codex `0.162.0-alpha.17.2`, no listing between tasks. A
  plain chat and an image generation left no transcript;
  `local_thread_catalog` held three `vscode` rows and three `chatgpt`
  rows, two with `conversation_origin` NULL and one `tpp`
  ([section 1 of `codex-cli.md`](codex-cli.md#1-source-and-evidence)).
- Windows, ChatGPT 26.1007.9446.0, 2026-10-15: the author's Windows 11
  ARM64 lab VM, the Microsoft Store package `OpenAI.Codex`. A plain chat
  and an image generation in the app left no local transcript; the chat
  left a `chatgpt` row with only its title set, at the same relative
  path `.codex/sqlite/codex-dev.db`, with a WAL sidecar (write-ahead
  log, where SQLite keeps recent writes until a checkpoint). By the end
  of the round the table held five rows: three `vscode` and two
  `chatgpt`, one with `conversation_origin` empty and one `tpp`
  ([section 10 of `codex-cli.md`](codex-cli.md#10-other-stores)).
- Not observed: a conversation deleted or renamed on chatgpt.com, a
  sign-out, and a second sign-in, so whether a later sign-in removes or
  updates a row is not determined; `conversation_origin` values other
  than empty, NULL and `tpp`; any `chatgpt_async_status` value; a
  `chatgpt` row with `cwd`, `model_provider` or `project_id` set. Linux
  has no ChatGPT desktop app.

<!-- MERGE: dedupe the Observed bullets above -->

### Source reviews

None.

None.

<!-- MERGE: dedupe the Source reviews above -->

## Collection

### 2. Per-user storage

No environment variable relocates the data on any platform.

#### Scratch directories

The app's own working and temporary directories, apart from the
profile and package directories of the subsections below:

- Windows: `~\Documents\Codex\<date>\<letter>\{outputs,work}\`, the
  default output directory of a thread with no project (empty on the
  install).
  Collected as `codex-cli` since collector 1.16.0 (issue 149; see
  [section 2 of `codex-cli.md`](codex-cli.md#2-per-user-storage)).
- Windows: `%LOCALAPPDATA%\Temp\` held 42 `.tmp<6 chars>` directories
  (the sandbox's and plugins' scratch), three `<uuid>.tmp.wav` and four
  `<uuid>.tmp` files; not collected ([section 4](#4-exclusions)).
- macOS, outside `~/Library` and `~/.codex` (ChatGPT 26.1013.40934,
  2026-10-18): the projectless output directories
  `~/Documents/Codex/<date>/<slug>/{work,outputs}`
  ([section 5](#5-project-local-files)), collected as `codex-cli` since
  collector 1.16.0 (issue 149; see
  [section 2 of `codex-cli.md`](codex-cli.md#2-per-user-storage)), and
  per-launch sockets under `/private/tmp/codex-app-tools/` and
  `/private/tmp/codex-browser-use/`, outside every home, so no catalog
  line can name them.

#### Windows, OpenAI.Codex package

Observed. The package's data directory is
`<pkg>` = `%LOCALAPPDATA%\Packages\OpenAI.Codex_2p2nqsd0c76g0`
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
[section 4](#4-exclusions); the output and temporary directories are
under [Scratch directories](#scratch-directories)):

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

#### Windows, previous package

Write-up, not observed. The `OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0`
package of 2024 and 2025, an Electron-style app whose data was under
`LocalCache\Roaming\ChatGPT\`
([garr3ttmjo/Digital-Forensic-Report-Writeups](https://github.com/garr3ttmjo/Digital-Forensic-Report-Writeups)
"ChatGPT Desktop Forensics", examined 2025-01-23;
[arXiv 2505.23938](https://arxiv.org/abs/2505.23938), October 2024
release, no exact paths). The full root is
`%LOCALAPPDATA%\Packages\OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0\LocalCache\Roaming\ChatGPT\`,
with chat history in `IndexedDB\https_chatgpt.com_0.indexeddb.leveldb\`
(persisting between sessions, removed on logout), session ids and
timestamps in `Local Storage\leveldb\`, and the standard Chromium
siblings (garr3ttmjo). The package's `LocalState\` may hold app
settings (MSIX convention, not cited). Its catalog lines stay for
installs that still have it.

#### macOS, com.openai.codex

Observed. Under `~/Library`:

| Path under `~/Library` | What it holds | Catalog |
| --- | --- | --- |
| `Application Support/Codex/Default/` | The Chromium profile, 742 files, 10.9 MB, with the Windows profile's entries except that the cookie store is `Cookies` and `Cookies-journal` directly in the profile, not under `Network/` (`Network Persistent State`, `TransportSecurity`, `Reporting and NEL`, `Trust Tokens` sit in the profile too); `IndexedDB/` with the single `app_-_0` origin (292 KB), `Local Storage/leveldb`, `Session Storage`, and the partitions `Partitions/codex-browser-app` and `Partitions/codex-mcp-app-sandbox%3Ashared` | collected |
| `Application Support/Codex/Local State`, `Last Version`, `statsig-state.json`, `.codex-tpp-local-executor-installation-id`, `browser-sidebar-page-states.json` | The files beside the profile. `Local State` (6,317 B) has the Windows keys except `os_crypt`: on macOS Chromium keeps the cookie key in the login keychain (not observed there), so the file is not flagged. `browser-sidebar-page-states.json` is 25 B (`pages`, `version`) | collected |
| `Application Support/Codex/executor-plugins/codex-app-tools/` | A bundled MCP server for the app's own tools: `.codex-plugin/plugin.json`, `.mcp.json`, `server.mjs` (949,032 B, excluded), `scripts/launch_codex_app_tools_mcp` | collected |
| `Application Support/Codex/artifact-sessions/runtime-generations/` | Empty on the install | collected |
| `Application Support/Codex/` other children | `component_crx_cache/` (58 MB), the twenty Chromium component directories of the Windows build, `BrowserMetrics-spare.pma` (4 MB), `GraphiteDawnCache/` (6 MB), `GPUPersistentCache/`, `Crashpad/`, `sentry/`, `ChromeFeatureState`, `OriginTrials/`, `Safe Browsing/`, `first_party_sets.db`, `segmentation_platform/`, and the `SingletonLock`, `SingletonSocket`, `SingletonCookie` and `RunningChromeVersion` symlinks (Chromium's single-instance lock) | not matched |
| `Application Support/com.openai.codex/production-appcast-bootstrap.json` | 30 B, `backendAppcastEnabled` (bool): the Sparkle appcast (update feed) switch. Collected as `codex-cli` before the macOS round, now as `chatgpt-desktop`, since the bundle id that owns it is the ChatGPT app | collected |
| `Application Support/com.openai.codex.installer/` | `attribution.json` (289 B: `created_at_ms`, `install_id`, `installed_version`, `installer_session_id`, `installer_stable_id`, `installer_version`, `schema_version`) and `attribution-acknowledgment.json` (137 B: `schema_version`, `install_id`, `app_version`, `acknowledged_at_ms`): install identifiers | collected |
| `Logs/com.openai.codex/<yyyy>/<mm>/<dd>/codex-desktop-<uuid>-<pid>-t<n>-i1-<hhmmss>-0.log` | The app's own log, the same `key=value` form as on Windows; three files, 1,593 lines in the largest; components include `[AppServerConnection]`, `[electron-message-handler]`, `[tpp-local-executor]`, `[mcp-app-sandbox]` and `[sparkle]` | collected |
| `Preferences/com.openai.codex.plist`, `com.openai.codex.installer.plist`, `com.openai.sky.CUAService.plist` | The app's preferences (`DockIconPreference`, `LastRunAppBundlePath`, `NSOSPLastRootDirectory`, the Sparkle `SU*` keys), the installer's `installer_stable_id`, and the computer-use service's status-item and Statsig stable id keys | collected |
| `HTTPStorages/com.openai.codex/`, `HTTPStorages/com.openai.sky.CUAService/` and the `.binarycookies` beside each | The macOS URL-session stores (`httpstorages.sqlite` with `-wal` and `-shm`) and their cookie files (461 B and 673 B) | collected; cookies secret |
| `Group Containers/2DC432GLL2.com.openai.sky.CUAService/` | The group container (a directory macOS shares between an app and its helpers) of the computer-use service: `IPC/computeruse.sock.lock`, `Library/Application Support/Software/Analytics.db` (one `distinct_id` row), a `Library/Application Scripts` symlink, empty `Caches` and `Preferences` | collected |
| `Caches/Codex/Default/` (`Cache`, `Code Cache`, `Partitions`; 6.2 MB), `Caches/com.openai.codex/`, `Caches/com.openai.sky.CUAService/` | The HTTP cache Electron keeps outside the profile on macOS, and the URL caches (`Cache.db`, `fsCachedData/`) | not matched |
| `Application Support/OpenAI/Codex/NativeMessagingHosts/` | Empty; the counterpart of the Windows `%LOCALAPPDATA%\OpenAI\Codex`, which here holds no binaries | not matched |

"sky" is OpenAI's internal name for the computer-use agent, read from
the bundle ids `com.openai.sky.CUAService` (an XPC service, a macOS
helper process) and the copy of `Codex Computer Use.app`
(`com.openai.sky.CUAService` 26.1005.1001425, 168 files, 76.6 MB) that
the app places in `~/.codex/computer-use/`. The `~/.codex` tree matches
Windows' with the differences listed in
[Codex Desktop](codex-cli.md#codex-desktop-inside-the-chatgpt-app).

On ChatGPT 26.1013.40934 (macOS, 2026-10-18) the layout was the same,
with these observations:

- `Application Support/Codex/sentry/scope_v3.json` (49 to 119 KB over
  the round; not matched by a catalog line) holds `scope.breadcrumbs`
  (200 entries, each `{category, data, level, message, timestamp,
  type}`), `scope.user` (`account_id`, `authMethod`, `id`), `scope.tags`
  (`buildFlavor`, `bundle`, `host`, `sessionId` and others) and
  `event.release`. After the first chat the breadcrumb categories were
  `console` 109, `electron.net` 62 (`data` `{method, status_code, url}`),
  `app_state` 10, `ui.click` 7, `child_process` 3 (`data` `{spawnfile}`),
  `fetch` 3 and `ui.input` 2: a rolling record of the URLs the app
  called, the user's clicks and the processes it spawned, beside the
  account identity. It holds no token. The catalog leaves it out, like
  the rest of the user-data directory's crash-reporting state.
- `Application Support/Codex/artifact-sessions/runtime-generations/`
  holds empty directories created at first launch; collected.
- The profile has no `Cache` directory: the HTTP cache is in
  `Caches/Codex/Default/`, so the
  `Library/Application Support/Codex/Default/Cache` exclusion matched
  nothing. `Caches/com.openai.sky.CUAService/Cache.db` and
  `Caches/com.apple.nsurlsessiond/Downloads/com.openai.codex/` are
  caches too; none is catalogued.
- `component_crx_cache/` (29 MB at first launch) and `GraphiteDawnCache/`
  (5.6 MB) beside the profile are not matched, like the other component
  directories.
- The profile's web storage is `IndexedDB/app_-_0.indexeddb.leveldb`
  (the `app://` origin), `Local Storage`, `Session Storage`,
  `Service Worker`, `Sync Data` and `shared_proto_db`; no directory is
  named after a chatgpt.com origin.

#### Former native macOS app

Write-ups, not observed. The native Swift app, bundle identifier
`com.openai.chat`, kept its data in
`~/Library/Application Support/com.openai.chat/`; conversations were
plain JSON in `conversations-{uuid}/` until 1.2024.171 and are encrypted
since, in `conversations-v2-{uuid}/`
([pvieito.com, ChatGPT unprotected conversations](https://pvieito.com/2024/07/chatgpt-unprotected-conversations);
[9to5mac.com, 2024-07-03 ChatGPT Mac app report](https://9to5mac.com/2024/07/03)).
Its catalog line stays for hosts that still have it.

### 3. Credentials

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
- macOS, `com.openai.codex` (observed): `Default/Cookies*` and
  `Default/Partitions/<partition>/Cookies*`, `Login Data*` in each, and
  `Library/HTTPStorages/com.openai.codex.binarycookies` and
  `com.openai.sky.CUAService.binarycookies` are flagged `secret: true`.
  The Chromium cookie key is not in `Local State` on macOS; the login
  keychain (the macOS credential store) held no item with an OpenAI,
  Codex or ChatGPT identifier, so where the key lives was not
  determined. The bundled Codex's `auth.json` and
  `.codex-global-state.json` are flagged as on Windows; there is no
  `.sandbox-secrets` on macOS.
- macOS, ChatGPT 26.1013.40934 (observed 2026-10-18): the bundled Codex
  writes `~/.codex/shell_snapshots/<thread uuid>.<unix ns>.sh`, the user's
  exported login-shell environment replayed for the sandbox, so any API
  key the shell exports is copied there; flagged from collector 1.15.0
  (details in [section 3 of `codex-cli.md`](codex-cli.md#3-credentials)).
  Collector 1.14.0 collected them unflagged.
- macOS, ChatGPT 26.1013.40934: the global state, already flagged, also
  carries the account's ids inside key names, not only in values:
  `chatgpt-work-models-v1/user-<account id>/<uuid>` and the keys of
  `new-task-execution-by-account-project`, which are JSON arrays holding
  `user-<account id>`.
- macOS, ChatGPT 26.1013.40934: remote control uses a server token,
  which the app refreshes when "Allow connections" is turned back on
  (`logs_2.sqlite` logs the refresh, without the token). Where it is
  stored was not found: `state_5.sqlite` `remote_control_enrollments` has
  no token column and its `websocket_url` has no query string,
  `auth.json` was not rewritten after sign-in, and a search of the login
  keychain for service or account names containing `openai`, `codex` or
  `chatgpt` was empty after every step. The enrollment row holds the
  account id and the Mac's host name but no secret, so it is not
  flagged.
- macOS, ChatGPT 26.1013.40934: `Trust Tokens` and `Trust Tokens-journal`
  (36,864 B, in `Default` and both partitions) are collected unflagged.
  They are Chromium's Private State Tokens store: anti-fraud tokens that
  websites issue to the browser, which sign no one in to anything, so
  they are not a credential.
- `sentry/scope_v3.json` carries the account id and user id
  (`scope.user`) but no token; it is not collected
  ([section 2](#2-per-user-storage)).
- Former native macOS app (write-up): the conversation encryption key
  is the Keychain item `com.openai.chat.conversations_v2_cache`
  (pvieito); absent on the 2026 install.
- No config file embeds an API key; the app uses account sign-in.
- Connecting a GitHub account (observed 2026-10-15) wrote no credential
  or configuration on the host: no `.git-credentials`, `.gitconfig`,
  `.ssh`, `gh` configuration or Credential Manager entry. The connection
  lives on the ChatGPT account, so the GitHub access the app had is not
  visible in a collection.

### 4. Exclusions

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

macOS, `com.openai.codex`: the same nine profile caches, in `Default`
and in every `Default/Partitions/<partition>`, as
`Library/Application Support/Codex/Default/...` exclusions;
`executor-plugins/*/server.mjs` (the bundled MCP server's 949 KB
script; its manifest and launcher are collected); and
`.codex/computer-use/*.app`, the 77 MB computer-use app bundle, whose
sibling `config.json` is collected. Not catalogued:

- `Library/Caches/Codex`, `Library/Caches/com.openai.codex` and
  `Library/Caches/com.openai.sky.CUAService`: HTTP and URL caches.
- `Library/Application Support/OpenAI`: empty on the install.
- The component directories, `component_crx_cache`, `sentry`,
  `Crashpad`, `BrowserMetrics-spare.pma` (a 4 MB metrics file) and the
  `Singleton*` symlinks under `Library/Application Support/Codex`: the
  catalog names only the profile and the files and directories beside
  it that the app writes.

The exclusions that fired in the live run on ChatGPT 26.1013.40934
(macOS, 2026-10-19, 28 `skipped_excluded` rows): `.codex/cache`
(39.6 MB, of which `remote_plugin_catalog/` 38.7 MB), `.codex/plugins/cache`
(67 MB), `.codex/plugins/.plugin-appserver` (341 MB),
`.codex/plugins/.remote-plugin-install-staging`, `.codex/.tmp` (123 MB),
`.codex/skills/.system`, `.codex/computer-use/Codex Computer Use.app`
(78 MB), `.codex/tmp`, `.codex/visualizations` (empty), and under
`Library/Application Support/Codex` the profile and partition caches
(`blob_storage`, `DawnGraphiteCache`, `DawnWebGPUCache`, `GPUCache`,
`Service Worker/ScriptCache`, `Extensions`) and
`executor-plugins/codex-app-tools/server.mjs` (950 KB). Nothing new and
large was collected. Not collected either, and not catalogued:
`~/.cache/codex-runtimes/codex-primary-runtime/` (32,625 entries),
`Library/Caches/Codex/Default/` (the HTTP cache) and the sockets under
`/private/tmp`.

Previous Windows package: `*/Roaming/ChatGPT/Cache`, `Code Cache`,
`GPUCache`, `DawnGraphiteCache`, `DawnWebGPUCache`. Former native macOS
app: `Library/Caches/com.openai.chat`, which no catalog line names.

### 5. Project-local files

The app writes none of its own into a project. The bundled Codex writes
what Codex writes (see [`codex-cli.md`](codex-cli.md)); the observed
project task wrote only the files it was asked for. Outside projects,
onboarding wrote `Desktop\Note from ChatGPT.txt`, and a thread with no
project gets `~\Documents\Codex\<date>\<letter>\`.

On macOS (ChatGPT 26.1013.40934, 2026-10-18) the coding task in `~/Demo`
again wrote only the three files it was asked for: no `.codex`, `.git`
or `AGENTS.md`. The projectless output directories were
`~/Documents/Codex/2026-10-18/w/` (the plain chat) and
`~/Documents/Codex/2026-10-18/new-chat/` (the scheduled task's thread),
each with `work/` and `outputs/`; the first stayed, empty, after its
thread was deleted. An approved write outside the project went to
`~/Desktop`, and the write Approve for me allowed went to `~/Documents`.

### 6. Where the project path is recorded

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

On macOS (ChatGPT 26.1013.40934, 2026-10-18) adding `~/Demo` as a project
also wrote it into `~/.codex/config.toml` as a `[projects."<path>"]`
table. The sh collector's live run found 2 projects from the rollouts:
`~/Demo` and the scheduled task's projectless output directory
`~/Documents/Codex/2026-10-18/new-chat`, which is the app's scratch
directory rather than a project the user chose (issue 149). The plain
chat's `~/Documents/Codex/2026-10-18/w` was not among them; its rollout
had been deleted before the run. Since collector 1.16.0 project
discovery drops a rollout `cwd` that is `<home>/Documents/Codex` or lies
under it, and the `codex-cli|Documents/Codex` catalog line collects the
directory whole, so its `outputs/` and `work/` files are in the archive.

## Parsing

### 7. Transcript stores

Relative to the home.

| Path | Content | Parse |
| --- | --- | --- |
| `.codex/sqlite/codex-dev.db` (+`-wal`, `-shm`) | the app's thread catalog and automation store; the `chatgpt` rows of `local_thread_catalog` are the account's conversations | yes, the `chatgpt` rows, by the `chatgpt-desktop` parser (the catalog attributes the file to `codex-cli`) |
| `.codex/sessions/**/rollout-*.jsonl` | the app's Codex-mode threads | yes, by the `codex-cli` parser |
| `.codex/.codex-global-state.json` | the app's UI and account state; on Windows it held a thread binding and a resume token for the ChatGPT chat ([section 2 of `collectors/research/chatgpt-desktop.md`](#2-per-user-storage)); on macOS no resume-token key had appeared by the end of sign-in | by the `codex-cli` parser for its Codex keys; not by this parser |
| the Chromium profile (`Library/Application Support/Codex` on macOS, the `OpenAI.Codex_*` package on Windows) | the web view's own storage, cookies and logs | no: no conversation text was found there on either install |

There is no ChatGPT-mode transcript on disk on any install checked.

#### What survives a delete

The `chatgpt` row is a sign-in snapshot that outlived a reply to its
conversation from inside the app with its times unchanged. A delete of a
Codex-mode thread removes only that thread's `vscode` row. What a
deletion of the conversation on chatgpt.com, or a sign-out, does to the
row was not exercised.

### 8. Record schema

`local_thread_catalog`, column names from `pragma table_info` on the
macOS install (build 26.1013.40934, 2026-10-18), in table order:
`host_id`, `thread_id`, `display_title`, `source_created_at`,
`source_updated_at`, `cwd`, `source_kind`, `source_detail`,
`model_provider`, `git_branch`, `observation_sequence`,
`missing_candidate`, `thread_source`, `source_recency_at`,
`pending_observed_title`, `project_id`, `conversation_origin`,
`trial_conversation_type`, `chatgpt_async_status`. The declared column
types were not recorded.

Values on the `chatgpt` rows (macOS, 2026-10-18):

| Column | Value |
| --- | --- |
| `host_id` | `chatgpt:<workspace uuid>:user-<account id>` (74 characters): the ChatGPT workspace and account; the `vscode` rows have `local` |
| `thread_id` | a UUID, the chatgpt.com conversation id |
| `display_title` | the conversation's title, set on every row seen |
| `source_created_at`, `source_updated_at`, `source_recency_at` | REAL epoch seconds with a fraction (not milliseconds) |
| `source_kind` | `chatgpt` (`vscode` for a Codex thread) |
| `conversation_origin` | empty or `tpp`; NULL on the 2026-10-15 macOS rows. What `tpp` stands for is not determined; the same token is in the app's `.codex-tpp-local-executor-installation-id` file name on both platforms and in the macOS app log's `[tpp-local-executor]` component ([section 2 of `collectors/research/chatgpt-desktop.md`](#2-per-user-storage)) |
| `missing_candidate` | 0 |
| `thread_source`, `model_provider`, `cwd`, `git_branch`, `project_id`, `trial_conversation_type`, `chatgpt_async_status` | NULL |
| `source_detail`, `observation_sequence`, `pending_observed_title` | not recorded |

### 9. Joins and timestamps

`thread_id` is the conversation's id on chatgpt.com and joins nothing
else on disk: no rollout, prompt history or log row carries it, because
the conversation never reaches the local app server
([section 1](#1-source-and-evidence)). It is the id to name in a request to OpenAI
for the conversation's content. `host_id` names the ChatGPT account the
list was taken from, as `local_thread_catalog_hosts` does.

The times are the server's times for the conversation as of the
snapshot: `source_created_at` when it was created and
`source_updated_at` when it last changed, both as of sign-in. A later
reply from inside the app did not move them ([section 1](#1-source-and-evidence)),
so `source_updated_at` is a lower bound on the conversation's last use,
not its last use. When the app wrote the row is the sign-in time, which
the row does not record.

### 10. Other stores

`codex-dev.db` (macOS, build 26.1013.40934, 2026-10-18; table and
column names only):

| Table | Columns | Rows seen |
| --- | --- | --- |
| `local_thread_catalog` | [section 8](#8-record-schema) | 3 `chatgpt` at sign-in, plus one `vscode` per Codex thread |
| `local_thread_catalog_hosts` | `host_id`, `host_kind` | 2: `local` / `local` and the account's `chatgpt:<uuid>:user-<id>` / `chatgpt` |
| `local_thread_catalog_sync_state` | `host_id`, `watermark_updated_at`, `initial_build_complete`, `observation_sequence`, `last_full_reconciled_at` | 2 (`initial_build_complete` 1; `observation_sequence` 5 and 1) |
| `local_thread_catalog_metadata` | `id`, `catalog_revision` | 1 |
| `local_thread_catalog_scan_checkpoints`, `local_thread_catalog_scan_entries` | not recorded | 0 |
| `automations`, `automation_runs`, `inbox_items` | the scheduled-task store ([section 10 of `codex-cli.md`](codex-cli.md#10-other-stores)) | `automations` 1 after a task was created; the `codex-cli` parser reads the task from `automation.toml` instead |
| `live_visualization_suggestions`, `local_app_server_feature_enablement`, `thread_timeline_ledger` | not read | 0, 1 and 0 |
| `codex_schema_migrations` | `app_version`, `build_flavor`, `build_commit` and more | 33 |

Only `local_thread_catalog` is read by the parser.

### 11. Format versions

`codex_schema_migrations` (33 rows on the 26.1013.40934 install)
carries the app version in `app_version`, with `build_flavor` `prod`
on the Windows install. The same table and the
same `chatgpt` row shape were seen on Windows build 26.1007.9446.0 and
macOS builds 26.1007.71326 and 26.1013.40934; the
`local_thread_catalog_metadata`, `_scan_checkpoints`, `_scan_entries`,
`_sync_state` and `thread_timeline_ledger` tables were recorded only on
the 26.1013.40934 install. The parser reads every column as possibly
absent or NULL, so an older table without a column still parses.

### 12. Secrets

`host_id` carries the ChatGPT workspace id and the account id, and
`display_title` the conversation's title, which is user content. No
token is stored in the table. The app's credentials are in
`~/.codex/auth.json`, flagged `secret: true` by the collector; see
[section 3 of `collectors/research/chatgpt-desktop.md`](#3-credentials).

### 13. Parser plan

`wants()` by `artifact.rel == ".codex/sqlite/codex-dev.db"`; the
analyzer offers the file, which the catalog attributes to `codex-cli`,
to this parser through `reads_agents = ("codex-cli",)`, the routing
Cody and Twinny use for an editor's `state.vscdb`. The `codex-cli`
parser does not want the file. The database is opened through
`sqlite_util.py`, which reads the WAL sidecar from a scratch copy. Rows
come only from `local_thread_catalog` rows whose `source_kind` is
`chatgpt`, in rowid order; the `vscode` rows are the Codex threads the
rollouts already give.

Per `chatgpt` row, three `system` rows, each with `session_id` the
`thread_id`, `project_path`, `model` and `git_branch` empty,
`source_line` 0, `source_file` the database, and `timestamp_utc` the
row's `source_updated_at` with milliseconds (its `source_created_at`
when that is NULL, none when both are). `-` stands for a NULL or empty
value:

1. `account conversation: <display_title> origin=<conversation_origin>
   created=<source_created_at, UTC> updated=<source_updated_at, UTC>
   host=<host_id> (from .codex/sqlite/codex-dev.db local_thread_catalog)`
2. `session origin: remote chatgpt.com conversation <thread_id> (listed
   at sign-in; its transcript is server-side)`
3. `session synced: chatgpt.com holds conversation <thread_id>, no local
   transcript`

#### Permission rows

None recorded for a ChatGPT-mode conversation; the app's Codex-mode
approvals are in the rollouts and `logs_2.sqlite`, read by the
`codex-cli` parser.

#### Model rows

None recorded; `model_provider` is NULL on every `chatgpt` row.

#### Past-use rows and secondary sources

None read beyond the primary store. The table is the only local record
of these conversations; the Windows global state's resume token for the
ChatGPT chat ([section 7](#7-transcript-stores)) is not read by this
parser. No secondary source.

#### Sync, relay and origin rows

The rows are themselves the sync marker, copied one way, account to app,
at sign-in; each gets the `session synced:` row. The app's Codex-mode
threads were not uploaded to the account on the macOS install
([section 1](#1-source-and-evidence)), and nothing in this table marks
one as uploaded.

The parser sets `records_origin` and `records_sync`, so `sessions.jsonl`
reads `origin` `remote` and `synced` `yes` for these sessions, and
`relayed` `""`. Their `user_turns`, `assistant_turns` and `tool_calls`
are 0, since the text is not on disk. Relay: none.

#### Scratch directory rows

Not stated.

#### Deletion rows

Not stated; what a delete leaves of the row is in
[What survives a delete](#what-survives-a-delete).

#### Bad-line rows

A file that is not SQLite is one `parser: not a SQLite database` row, a
SQLite error one `parser: SQLite error: <message>` row, and a database
without the table one `parser: no local_thread_catalog table` row.

#### Fixtures

Not stated.

## 14. Confidence

High (observed on Windows 11, ChatGPT 26.1007.9446.0): the package name
and layout, the catalog lines, exclusions and secret globs of
[section 2](#2-per-user-storage) to [section 4](#4-exclusions), that the
chat surface keeps no local transcript, and the locked-file failures.
High (observed on macOS 26.6.2, ChatGPT 26.1007.71326): the bundle id,
the `~/Library` layout and the macOS catalog lines, exclusions and
secret globs. High (observed on macOS 26.6.2, ChatGPT 26.1013.40934, one
step per listing): what each step of [section 1](#1-source-and-evidence)
wrote, that a ChatGPT-mode reply leaves nothing local, that remote
control leaves one enrollment row and log rows and no file, and that the
shell snapshots hold the exported environment. High (write-ups): the
former native app's `conversations-v2-*` encryption and the previous
Windows package's layout. Not determined: where the macOS app keeps its
Chromium cookie key; what the `app://` IndexedDB blob and
`Local Storage` hold; the bundled extension's purpose; what "tpp" and
"owl" stand for; the app's behaviour on x64 Windows (only ARM64 was
observed); which of the user's actions wrote the first Codex thread on
the 2026-10-15 installs; where the remote control server token is
stored; whether a heartbeat run that decides to notify the user writes
`automation_runs` or `inbox_items` rows (only a run that did not notify
was observed).
