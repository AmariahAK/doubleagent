# Antigravity CLI and desktop app transcript schema

Catalog agent: `antigravity`. Google Antigravity ships two surfaces that
write transcripts: the Antigravity CLI (`agy`) and, since 2.0, the
Antigravity desktop app, an Electron app whose bundle calls the product
"AGY Hub" (its internal name for the agent-first app; the VS Code-fork
editor that carried the Antigravity name before 2.0 is now a separate
download, "Antigravity IDE"). Both run the same Go backend, which the app
calls the language server (the program that owns the conversation stores
and runs the agent), and both write
the same SQLite-of-protobuf conversation databases, each into its own data
directory under `~/.gemini`.

Evidence level: shipped binaries (protobuf descriptors extracted from `agy`
and from the app's `language_server`), confirmed against a real install on
the author's WSL workstation (CLI), on the author's Mac (CLI and desktop
app), in the author's Ubuntu lab VM (CLI and desktop app) and in the
author's Windows 11 lab VM (CLI and desktop app), October 2026. No public
source exists. Extraction:
`tools/proto_descriptors.py extract ~/.local/bin/agy descriptors.json`, then
`show` on the names below.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/antigravity.md`](../../collectors/research/antigravity.md).

## 1. Binary and version

- **Linux (WSL)**: `~/.local/bin/agy`, ELF x86-64, about 200 MB, Google
  Antigravity CLI, installed 2026-10-03. 1300 embedded `.proto`
  descriptors; the relevant packages are `gemini_coder`
  (`third_party/gemini_coder/proto/trajectory.proto`), `exa.cortex_pb`
  (`third_party/jetski/cortex_pb/cortex.proto`), `exa.codeium_common_pb`
  and `exa.jetski_cortex_pb`. The `jetski`, `cascade` and `codeium` names
  show the lineage from Windsurf's Cascade agent. The parser's tables were
  built from these descriptors.
- **Observed (macOS)**: the author's installs on macOS 26.4 (Darwin
  25.4.0), Apple silicon (arm64), 2026-10-13 (issue 83), read for file
  names, sizes, key names, value types and SQLite schemas only, with
  `analyzer/tools/shape.py`.
  - **CLI**: `~/.local/bin/agy`, Mach-O 64-bit arm64, 175,966,448 bytes,
    sha256
    `7dca095cfc1df2c057a385ed88a76c7ba98dc103258a80be87a8f42e484cb3aa`,
    installed 2026-10-04; `agy --version` prints `1.2.16`, while the
    embedded changelog's newest heading is still `## 1.2.15`. Two
    conversations in `~/.gemini/antigravity-cli/conversations/`, both
    `trajectory_meta.source` 17 (`cli`) and `trajectory_type` 4, of 12 and
    8 steps. A second look on 2026-10-15 with CLI 1.3.6 (`/Users/sean/.local/bin/agy`,
    183,407,440 bytes, sha256 `827ba22b4aa33557614a57aac2cc13f386e17db6b802febd3932226906ac05ab`): one
    conversation of 17 steps in a project directory the agent was then
    told to delete, which left the conversation database, its
    `brain/<uuid>/` mirror (16 `transcript_full.jsonl` lines), the
    `history.jsonl` lines and the summaries row in place, so the whole
    session parsed after the directory was gone; its four `history.jsonl`
    lines showed which ones carry `conversationId`
    ([section 5](#5-joins-and-gaps)).
  - **Desktop app**: `/Applications/Antigravity.app`,
    `CFBundleShortVersionString` and `CFBundleVersion` both `2.23.0`.
    `Contents/Resources/app.asar` is 4,486,221 bytes, sha256
    `4e99093662d797ecba823e92823d352413e3bf2ca721257df4a255c045df1598`;
    `Contents/Resources/bin/language_server` is a Mach-O arm64 binary of
    155,290,912 bytes, sha256
    `c1dd0c9940f712adf2185e756470752d5f5afee15441e32879e4a0f127e18273`.
    The app passes the language server `--subclient_type hub`,
    `--standalone` and `--app_data_dir` with the data-directory name
    (`app.asar:dist/languageServer.js@4241987` `'--subclient_type',`
    `'hub',`; `@4242293` `'--app_data_dir',`
    `(0, paths_1.getAppDataDirName)(),`), and the name is the app name
    lower-cased without spaces, `antigravity`
    (`app.asar:dist/paths.js@4312548`
    `return electron_1.app.getName().toLowerCase().replace(/\s+/g, '');`),
    under `~/.gemini` on every OS (`app.asar:dist/paths.js@4312621`
    `path_1.default.join(os_1.default.homedir(), '.gemini', getAppDataDirName())`).
    First launched 18:28 local time. The user exercised, in this order, a
    plain question-and-answer chat, a coding task, an automation (a
    scheduled task, which the app runs as a sidecar: a long-running helper
    process the language server supervises, enabled with
    `--enable_sidecars`, `app.asar:dist/languageServer.js@4242552`) and the
    Google Docs plugin (`gdocs`, installed from the official plugin
    marketplace). That wrote four conversations in
    `~/.gemini/antigravity/conversations/`, all `trajectory_meta.source` 1
    (`cascade_client`) and `trajectory_type` 4: 12 steps (modified 18:37),
    24 steps (18:43), 43 steps (18:50) and 31 steps (19:14), each with a
    `brain/<uuid>/` directory, an `annotations/<uuid>.pbtxt` and a row in
    `conversation_summaries.db` ([section 2](#2-stores-relative-to-home)).
    Which conversation belongs to which task was not recorded while it
    happened: no listing was taken between the tasks, so the order above
    is by modification time only. Where a scheduled run of
    the automation writes its transcript was not observed, because no run
    had fired.
  - **Descriptors**: `tools/proto_descriptors.py extract` (after the fix
    for issue 86) found 271 descriptor files in `agy` 1.2.16 and 484 in
    `language_server` 2.23.0; the difference from the Linux count above
    was not investigated. `exa.cortex_pb.CortexStepType` (118 values),
    `CortexStepStatus`, `CortexTrajectorySource`, `gemini_coder.Step`,
    `gemini_coder.Trajectory` and every message in the parser's `SCHEMA`
    were diffed against the parser's tables, which were built from the
    Linux descriptors: field numbers, names and types match in both macOS
    binaries, and the two define `CortexTrajectorySource` identically
    ([section 5](#5-joins-and-gaps)). Nothing the parser reads drifted.
    The diff did find one error in the tables themselves, the
    `delete_file` layout ([section 3](#3-conversation-database)).
- **Observed (Linux)**: the author's Ubuntu 26.04.1 LTS lab VM, aarch64, Linux
  7.0.0-38-generic, 2026-10-13 (times below in US Eastern daylight time; issue 83), read for file
  names, sizes, key names, value types, SQLite schemas and enum values
  only, with `find`, `ls`, `analyzer/tools/shape.py` and a read-only
  schema script, all Python run with `python3 -I`. The user installed both
  products and ran a few turns with each; no listing was taken between
  tasks, so, as on macOS, the mapping from task to file is by
  modification time only.
  - **CLI**: `~/.local/bin/agy`, ELF aarch64, 204,492,984 bytes, sha256
    `08d619ae3969c33b9cba5eac2a54f4566cbca1b5de68968167cb908ced5b4824`,
    installed 21:37 local time; `agy --version` prints `1.3.4`, while the
    embedded changelog's newest heading is `## 1.3.3`. One conversation in
    `~/.gemini/antigravity-cli/conversations/` (622,592 B, modified
    21:43), `trajectory_meta.source` 17 (`cli`) and `trajectory_type` 4,
    26 steps. New in 1.3.x: `history.jsonl` lines can carry
    `conversationId` (issue 89), and the CLI writes
    `annotations/<uuid>.pbtxt` as the app does
    ([section 2](#2-stores-relative-to-home)).
  - **Desktop app**: 2.23.1 (its `main.log` line
    `Starting app (v2.23.1) with dynamic port…`), downloaded as a
    `.tar.gz` and unpacked into the home; it is not an AppImage, as
    `main.log` itself says. The Electron binary `antigravity` is
    220,466,568 bytes, sha256
    `c543041069aa2e478235447cb636f9f09faab15003862029d226bb14b8dc655b`;
    `resources/app.asar` is 4,486,221 bytes (the size of the macOS 2.23.0
    asar, with a different hash), sha256
    `b8ec3628df2a12ee9deac5dc06367f238065af146bfe6298fdad6db5f9790d9c`;
    `resources/bin/language_server` is 181,358,800 bytes, sha256
    `310ee8e0cba4c4ee05504ac8021cbd3544a79c06cc01c790536361625c5fffb3`.
    First run 21:29. Four conversations in
    `~/.gemini/antigravity/conversations/` (655,360 to 1,114,112 B,
    modified 21:45, 21:51, 21:55 and 22:00), all `trajectory_meta.source`
    1 (`cascade_client`) and `trajectory_type` 4, of 14, 43, 30 and 38
    steps ([section 3](#3-conversation-database)), each with a
    `brain/<uuid>/` directory, an `annotations/<uuid>.pbtxt` and a
    summaries row. The user also scheduled an automation (a sidecar); its
    scheduler log is the first observed trace of a sidecar's own output
    ([section 2](#2-stores-relative-to-home)), but no scheduled run had
    fired, so what a run writes, and whether it becomes a conversation, is
    still not observed. The descriptors of the 1.3.4 and 2.23.1 binaries
    were not extracted in this round.
  - **Analyzer 0.12.0** over the collector 1.12.0 archive of this VM:
    the summary line read
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
- **Observed (Windows)**: the author's Windows 11 ARM64 lab VM, build 26300
  (`ver` prints `10.0.26300.9550`), 2026-10-14 (times below in UTC; the
  round ran in the evening US Eastern time, so they cross midnight into
  2026-10-15; issue 83), read for file names, sizes, key names, value
  types and log lines with ids redacted only. No WSL (Windows Subsystem for
  Linux) distribution was installed. The user installed the desktop app
  and the CLI and ran a few turns with each; as on macOS and Linux no
  listing was taken between tasks, so the mapping from task to file is by
  modification time only. `%LOCALAPPDATA%` below is the per-user
  `AppData\Local` folder and `%APPDATA%` the per-user `AppData\Roaming`
  folder.
  - **CLI**: `%LOCALAPPDATA%\agy\bin\agy.exe`, 184,062,616 bytes, sha256
    `223953a7d64ad199bbeaae3cf84d634b0ec3917979c7a60feac6ade05d50888b`,
    installed 23:56:21Z and on `PATH`; its `VersionInfo.ProductVersion` is
    empty, `agy --version` prints `1.3.5`, and the embedded changelog's
    newest heading is `## 1.3.4`. `~/.gemini/antigravity-cli/` was created
    at the first run, 00:22:29Z. The user started it from
    `C:\users\sean\demo2`, typed in lower case, and ran a coding task that
    wrote one source file per language into ten subdirectories and a
    `README.md` (00:25:07Z to 00:27:16Z). One conversation in
    `~/.gemini/antigravity-cli/conversations/` (983,040 B, modified
    00:28:12Z), 38 steps. Its `history.jsonl` had one line, without
    `conversationId`. New in 1.3.5 as observed here:
    `cache/conversation_metadata.json`, and a summaries database that
    mirrors the app's conversations
    ([section 2](#2-stores-relative-to-home),
    [section 4](#4-summaries-database)).
  - **Desktop app**: installed under
    `%LOCALAPPDATA%\Programs\antigravity\`. `Antigravity.exe` is
    226,382,336 bytes, sha256
    `16febcd47a2a6823fe9ec4847b60f2fc766a46c8c355643185326a2879668243`,
    `VersionInfo.ProductVersion` `2.23.1.0` and `FileVersion` `2.23.1`, and
    `main.log` reads `Starting app (v2.23.1) with dynamic port…`;
    `resources\app.asar` is 4,486,221 bytes, sha256
    `b8ec3628df2a12ee9deac5dc06367f238065af146bfe6298fdad6db5f9790d9c`,
    byte-identical to the Linux 2.23.1 asar;
    `resources\bin\language_server.exe` is 160,643,584 bytes, sha256
    `32d65353f033600274203137913207c02f636c214b8233c529a2afa0ee55ecf5`.
    First launch 23:56:11Z. The user ran a question with no file writes, a
    coding task in the project folder `C:\Users\sean\demo` (six files
    written 00:01:44Z to 00:03:20Z), a research task that wrote a Markdown
    document to the app's `scratch/` directory and started a background
    task, and a task that set up a scheduled automation (a sidecar) named
    `weekly-microsoft-security-bulletins`; the Google Docs plugin (`gdocs`
    0.0.6) was installed from the marketplace between 00:05:45Z and
    00:08:51Z. Four conversations in `~/.gemini/antigravity/conversations/`
    (622,592, 589,824, 1,441,792 and 6,258,688 B, modified 00:03:54Z,
    00:06:55Z, 00:13:30Z and 00:20:53Z) of 20, 10, 46 and 46 steps (the
    step counts are in the analyzer's session order, which was not matched
    to the file sizes), each with a `brain/<uuid>/` directory, an
    `annotations/<uuid>.pbtxt` and a summaries row. Neither the CLI's nor
    the app's conversation databases had a `-wal` or `-shm` sidecar when
    listed. No `sidecar_data/` directory appeared for the automation
    ([section 2](#2-stores-relative-to-home)). The descriptors of the 1.3.5
    and 2.23.1 Windows binaries were not extracted in this round.
  - **Analyzer 0.12.0** (at `main` commit [`4607cca`](https://github.com/seanthegeek/doubleagent/commit/4607ccaac18f9bcfcb1a01cefc9402939430b09d)) over the collector
    1.12.0 archive of this VM (PowerShell collector, 213 `collected`
    files): `detect` verified the archive's sha256 and listed the one user
    with `antigravity`, 213 files and 14,339,425 B, and its `detect.json`
    (a file `timeline` wrote until its content moved into
    [`inventory.json`](../docs/output.md#inventoryjson) later in 0.12.0)
    `problems` list was empty. `timeline --include-thinking` reported
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
    ([section 4](#4-summaries-database)) and 2 `system_message` steps (both
    `task_notification` events). Four session starts read
    `source=cascade_client` and `data_dir=antigravity`, one of them with
    the app project's `project_id` and three `outside-of-project`; the
    fifth read `source=cli`, `data_dir=antigravity-cli` and
    `project_id=default-cli-project`. Tool names: `run_command` 36,
    `write_to_file` 21, `view_file` 8, `search_web` 3, `ask_question` 3,
    `read_url_content` 1. The `history.jsonl` row had an empty
    `session_id`, since its line has no `conversationId`, and the
    lower-case `C:\users\sean\demo2` as `project_path`
    ([section 5](#5-joins-and-gaps)). No row reported an unreadable file
    or a decode failure.

## 2. Stores, relative to home

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
| `<dir>/conversation_summaries.db` | one row per conversation; the app's copy adds a full-text search table, and the CLI 1.3.5 copy on Windows also held a row for each of the app's conversations ([section 4](#4-summaries-database)) |
| `.gemini/antigravity-cli/history.jsonl` | `{display, timestamp (ms), workspace}` per prompt; CLI only, the app writes none (**observed**). CLI 1.3.4 (**observed**, Linux) adds `conversationId`, the conversation's UUID, on some lines: of its two lines one had `display`, `timestamp` and `workspace`, the other `conversationId` as well ([section 5](#5-joins-and-gaps)). CLI 1.3.5 (**observed**, Windows) wrote one line, with `display`, `timestamp` and `workspace` and no `conversationId` |
| `.gemini/antigravity-cli/cache/conversation_metadata.json` | CLI 1.3.5 (**observed**, Windows, 2,671 B; not seen on macOS with 1.2.16 or Linux with 1.3.4): `conversations` {`<uuid>`: {`is_internal` (bool), `last_modified_time` (ISO date), `summary` {`AgentName`, `AppDataDir`, `GroupID`, `ID` (UUID), `Internal` (bool), `Loaded` (bool), `NumSteps` (number), `Preview`, `ProjectID`, `Title`, `UpdatedAt` (ISO date), `WorkspaceURIs` (null)}}}; its four entries were the app's four conversations (`AppDataDir` of 11 characters, `antigravity`; `AgentName` and `GroupID` empty). The parser does not read it |
| `.gemini/antigravity-cli/cache/last_conversations.json` | {`<absolute path>`: `<uuid>`} (**observed**, Windows, 70 B): by its name, the last conversation per working folder; the parser does not read it |
| `.gemini/antigravity-cli/jetbox_summaries_proto.pb` | `jetbox_summaries_pb.SummariesState`, same summaries as the database; the app's counterpart is `.gemini/antigravity/agyhub_summaries_proto.pb` (1,436 B, **observed**; 1,417 B on Windows) |
| `<dir>/annotations/<uuid>.pbtxt` | seen in the app's directory (**observed**, 94-99 B each on macOS, 93-101 B on Linux, 93-96 B on Windows) and, from CLI 1.3.x, in the CLI's (**observed**, Linux, 37 B; Windows, 46 B): text-format protobuf (pbtxt, protobuf's human-readable text encoding, `field: value` lines) with a single `title:` field, the conversation title |
| `<dir>/brain/<uuid>/` | per-conversation artifacts and logs, below |
| `.gemini/antigravity-cli/antigravity-oauth-token` | credential, flagged secret by the collector; absent on the Windows install, where the CLI kept its token in the OS keyring ([section 6](#6-secrets)) |
| `.gemini/antigravity/plugin_data/<plugin>/token.json` | a plugin's OAuth credential ([section 6](#6-secrets)) |
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
([section 1](#1-binary-and-version)), so the mirror can lag the database by
a step. The token counts appear nowhere the parser reads.

The value forms come from a format description the backend embeds for its
own agent, which is told to read past conversations from these files
(`agy` 1.3.6 macOS arm64, the binary of [section 1](#1-binary-and-version),
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
  `completed_at` ([section 3](#3-conversation-database)); which of them
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
([section 5](#5-joins-and-gaps)); a planner step's calls are run as the
steps after it.

What the mirror survives: it sits under `brain/<uuid>/`, beside
`conversations/<uuid>.db` in the same data directory, so it survives what
the database survives (the deletion of the project directory, observed
2026-10-15) and is lost with the data directory. It is a second copy when
the database alone is lost, damaged or excluded: a database whose steps no
longer decode, a `-wal` sidecar the collection missed, a database file the
collector skipped for size, or a conversation the user deleted if the app
removes the database before the brain directory (not observed). The
chunked copies keep the transcript when `transcript_full.jsonl` itself was
skipped for size. Whether a compaction or a rewind rewrites the mirror was
not observed.

`messages/<uuid>.json` (**observed**): `content` (string), `id` (UUID),
`priority` (upper-case enum-like string), `recipient` (UUID),
`renderDetails` {`messageTitle`}, `sender` (a 43-44 character string
containing a UUID), `timestamp` (ISO date), and on two of three
`sourceMetadata` {`tool` {`conversationId` (UUID), `stepIndex` (number),
`toolCall` {`argumentsJson`, `id` (`call_` and digits), `name`
(`run_command`), `thinkingSignature`}}}. `messages/read.json` is
{`<uuid>`: bool} per message. On Linux the two messages had the same keys,
`sender` 44 characters.

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

**Permission configuration.** Besides the per-step grants in the
conversation databases ([section 3](#3-conversation-database)), Antigravity
keeps standing permission state in four JSON files, which together are its
permission configuration. A grant entry is a tool-call pattern: a tool name
followed by its argument in parentheses. The keys, with what was seen on the
2026-10-13 real installs (macOS: CLI 1.2.16 and app 2.23.0; Ubuntu: CLI
1.3.4 and app 2.23.1; key names and counts only, **observed** unless marked):

| File | Keys |
| --- | --- |
| `.gemini/config/config.json` (shared by the CLI and the app) | `userSettings.globalPermissionGrants.allow[]` (3 entries on macOS, 11 on Ubuntu, 14 on Windows), `userSettings.permissionGrantsV2Migrated` (bool), `userSettings.sandboxEnabledAtV2Migration` (bool); per automation (sidecar) `sidecars.<name>.enabled` and `sidecars.<name>.resolvedPermissions.accessGrants[]` (not in the macOS or the Windows file; the Windows file also had neither migration flag) |
| `.gemini/config/projects/<uuid>.json` | `permissionGrants.permissionGrants.allow[]` (seen on one Ubuntu project file), `permissionGrants.v2Migrated`; the project folder is `projectResources.resources[].folderUri` |
| `.gemini/config/sidecars/<name>/sidecar.json` | `agent_permissions.access_grants[]` (2 entries on macOS, 3 on Windows) |
| `.gemini/antigravity-cli/settings.json` | `permissions.allow[]` (CLI 1.3.x; one entry on Windows) and `trustedWorkspaces[]` (the folders the user trusted; a JSON tag in the binary, see [`collectors/research/antigravity.md`](../../collectors/research/antigravity.md)) |

The `antigravity` parser reads these keys and nothing else in the files
(not `plugins`, `remoteControlHostname`, a project's `name` or a sidecar's
`args`), and never wants `mcp_config.json`, which can embed MCP credentials,
or a plugin's `token.json`. Each list entry and each flag becomes one
`system` row, `permission setting: <key>=<value> (from <path relative to
the home>, file mtime)`, where `<key>` is the JSON path in the file and a
`trustedWorkspaces[]` entry is `trustedWorkspace=<path>`. The rows are
timestamped by the file's modification time (the manifest's `mtime`, or
the file's own without a manifest), since none of the entries records when
it was granted; their `session_id` is empty, and the project file's rows and
each trusted workspace's row carry the folder as `project_path`. A `deny[]`
list beside each `allow[]` is read the same way; none was seen, so it is
fixture only. On Windows (**observed**, CLI 1.3.5) the one
`trustedWorkspaces[]` entry was an absolute Windows path, not a `file://`
URI; the parser accepts both (issue 92).

### What survives a delete

What Antigravity's own delete of a conversation removes, in the CLI or
the app, is not stated: no real install has deleted one, and whether
the app removes the conversation database before the brain directory
is not observed. Deleting the project directory removes none of it: on
the macOS CLI 1.3.6 install of 2026-10-15 the conversation database,
its `brain/<uuid>/` mirror, the `history.jsonl` lines and the summaries
row stayed in place, and the whole session parsed after the directory
was gone ([section 1](#1-binary-and-version)). The per-prompt history
file, `.gemini/antigravity-cli/history.jsonl`, is the CLI's alone: each
line has the prompt, its time in milliseconds and the workspace, and
from CLI 1.3.x some lines also the conversation id. The second copies
are the brain mirror (`transcript_full.jsonl`, `transcript.jsonl` and
their chunks), which survives what the database survives and is lost
with the data directory; the summaries database with the app's
full-text search table; the protobuf summaries files; the title in
`annotations/<uuid>.pbtxt`; and, on the CLI 1.3.5 install, the CLI's
summary rows and `cache/conversation_metadata.json` entries for the
app's conversations ([section 4](#4-summaries-database)). Whether a
compaction or a rewind rewrites the mirror is not observed, and no
deletion marker is stated. The analyzer reads `history.jsonl` and the
brain mirror as secondary sources and each summaries row as its own
`conversation summary` row, and does not read the annotations, the
protobuf summaries, the full-text search table or the CLI's cache (see
[Secondary sources](../docs/output.md#secondary-sources)).

## 3. Conversation database

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
file name. `source` is a `CortexTrajectorySource` ([section 5](#5-joins-and-gaps));
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

The parser decodes the column, or Step field 133 of the payload when the
column is empty, and yields after the step's own rows one `system` row per
`permission_grants[]` entry, `permission grant: action=<action>
target=<target> allow=<true|false> scope=<scope>` (`action` and `target`
from fields 5 and 6, else from `resource`; with `deny_instruction=<text>`
appended when `user_deny_instruction` is set), and one per
`file_access_permissions[]` entry, `permission grant: path=<path>
is_directory=<true|false> allow=<true|false> scope=<scope>` (with
`from_current_step=true` appended when set). Each row carries the step's
`tool_name` and `tool_use_id`, so it sits beside the call it governed, and
the step's tool-result time; `<scope>` is the lower-case name without the
prefix, or the number for a value not in the enum. A blob that does not
decode is one `system` row, `parser: the permissions of step <idx> could
not be decoded`, and the step's other rows stand (issue 92).

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

Three tool-payload fields carry permission evidence (issue 97), all bool
and identical in the `agy` 1.2.16 and `language_server` 2.23.0
descriptors (macOS arm64): `CortexStepRunCommand` 14 `user_rejected` and
34 `ran_in_sandbox`, and `CortexStepMcpTool` 7 `user_rejected`. A step
with `user_rejected` set yields, right after its `tool_result` row (whose
text keeps `[rejected by user]`), a `system` row `permission decision:
user_rejected` with the step's `tool_name`, `tool_use_id` and result
time. `ran_in_sandbox` is not a decision: a `run_command` result with it
set ends with ` sandbox=true`. None of the three has been seen set in
real data, since every observed tool step was a `generic` step whose
typed payload sits in a `google.protobuf.Any` the parser does not unpack.

`trajectory_metadata_blob.data` is `CortexTrajectoryMetadata`: 1
`workspaces[]` (`CortexWorkspaceMetadata`: 1 `workspace_folder_absolute_uri`,
2 `git_root_absolute_uri`, 4 `branch_name`), 2 `created_at`, 5
`parent_conversation_id`, 6 `root_conversation_id`, 7 `workspace_uris[]`,
17 `nesting_depth`, 18 `project_id`.

## 4. Summaries database

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
([section 2](#2-stores-relative-to-home)), and its `cli.log` has a line
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

## 5. Joins and gaps

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

On Windows one folder can reach the parser under several spellings,
since the parser passes a plain path through unchanged and turns a
`file:` URI into a path with `uri_to_path`, which keeps the drive letter's
case and uses forward slashes. The Windows install (**observed**, Windows
11, CLI 1.3.5 and app 2.23.1, 2026-10-14) gave three: `c:/Users/sean/demo`, from the app's `file:///c%3A/Users/sean/demo`
URIs (a percent-encoded colon and a lower-case drive letter, as the
project file's `folderUri` records it); `C:/users/sean/demo2`, from the
`file:` URI in the CLI conversation's `conversation_summaries.workspace_uris`; and `C:\users\sean\demo2`,
the plain path of the `history.jsonl` `workspace`. The lower-case `users`
is how the user typed the CLI's working folder. `collection.json` listed
the two folders as `C:\Users\sean\demo` and `C:\users\sean\demo2`.
Up to analyzer 0.12.0 the rows carried the three spellings as recorded,
so `inventory.json` split one folder into two projects and neither
matched the collected folder's spelling. From analyzer 0.13.0
([doubleagent issue 112](https://github.com/seanthegeek/doubleagent/issues/112))
the timeline writes every Windows `project_path` in one canonical form
(upper-case drive letter, backslash separators, no trailing separator),
so the three become `C:\Users\sean\demo` and `C:\users\sean\demo2`,
and `inventory.json` groups spellings that differ only in case; the
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
own ([section 4](#4-summaries-database)); the parser does not put
`app_data_dir` in the row's text, but the row's `source_file` names the
database it came from. The parser puts
`source=<name>` and `data_dir=<directory>` in each conversation's session
start row. The conversation title is in `conversation_summaries.title` and
in `annotations/<uuid>.pbtxt` (`title:`); the parser reads the former.

Step kinds other than `user_input`, `planner_response`, `generic`,
`system_message` and `error_message` are decoded from the descriptors but
have not been seen in real data.

The brain mirror ([section 2](#2-stores-relative-to-home)) joins the
database by conversation id: the `<uuid>` of `brain/<uuid>/` is the
database's `cascade_id`, and the parser puts it in `session_id` for both.
A mirror line repeats one database step, and the timeline pairs the two
rows on `session_id`, `turn_type` and `text` within 600 seconds (see
[Secondary sources in `docs/output.md`](../docs/output.md#secondary-sources),
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

## 6. Secrets

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
[section 3 of `collectors/research/antigravity.md`](../../collectors/research/antigravity.md#3-credentials);
the parser reads neither.

## 7. Parser plan

Every source below is read on every run; a secondary source is one whose
rows the timeline drops when the primary store yields the same event
([Secondary sources in `docs/output.md`](../docs/output.md#secondary-sources)).

| Source | Role | Rows |
| --- | --- | --- |
| `<dir>/conversations/<uuid>.db` | primary: the store of record, every step with its payload, model, permissions and both times | session start, user, assistant, tool_use, tool_result, thinking, system, model and permission rows ([section 3](#3-conversation-database)) |
| `<dir>/conversation_summaries.db` | primary: a summary per conversation, not a copy of its events | one `conversation summary` `system` row per conversation ([section 4](#4-summaries-database)) |
| `.gemini/antigravity-cli/history.jsonl` | secondary (2 seconds): the prompts the database also records | one `user` row per line ([section 5](#5-joins-and-gaps)) |
| `<dir>/brain/<uuid>/.system_generated/logs/transcript_full.jsonl`, else `chunks/transcript_full/*.jsonl` concatenated, else `transcript.jsonl`, else `chunks/transcript/*.jsonl` | secondary (600 seconds): one copy of the database's steps, read in that order of preference, one copy per conversation | user, assistant, tool_use, tool_result, thinking and system rows, as the database reader renders the same step kinds ([section 2](#2-stores-relative-to-home)) |
| the standing permission files | primary: no other copy | `permission setting` rows ([section 2](#2-stores-relative-to-home)) |

The four mirror files are copies of one transcript, not four sources: the
shortened `transcript.jsonl` holds the same lines with long fields cut, and
the chunks are the same bytes split at 102,400 bytes. Not read:
`brain/<uuid>/.system_generated/steps/<idx>/output.txt` and `content.md`,
`messages/<uuid>.json` and `tasks/task-<idx>.log` (outputs and messages
the steps already carry, or not yet mapped to a step), `annotations/*.pbtxt`
(the title, also in the summaries database),
`cache/conversation_metadata.json`, `jetbox_summaries_proto.pb` and
`agyhub_summaries_proto.pb` (summaries again), and the app's FTS5 table.
