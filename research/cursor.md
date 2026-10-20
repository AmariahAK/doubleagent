# cursor

Cursor is a closed-source editor forked from VS Code (the Cursor IDE) with a command-line agent,
the Cursor Agent CLI (`agent`, `cursor-agent`), a copy of which the IDE embeds and runs as its
agent worker. The document uses Cursor's own names: a composer is one conversation, identified by
its `composerId` (a UUID); a bubble is one message, reasoning block or tool call inside a composer,
identified by its `bubbleId`; the Agents window is the IDE's window given over to agent
conversations, and the editor window is the VS Code-style window with its own chat pane and chat
history (on 3.26.13, 2026-10-20, only the editor window offered Export and Delete); `glass` is the
name the IDE's bundle and storage keys give that agent user interface (`workbench.glass.main.js`,
the `cursor/glass.*` keys); `agentKv` is the key prefix of a content-addressed blob store inside
the IDE's database; `yolo` is Cursor's internal name for auto-run, the setting that runs agent
tool calls without asking (`yoloCommandAllowlist`); and `toolFormer` is its internal name for a
tool call's record inside a bubble (`toolFormerData`). The analyzer parses the IDE's
conversations
([issue 51](https://github.com/seanthegeek/doubleagent/issues/51)); the Agent CLI's own stores
are not parsed.

## Source and evidence

Closed source. Evidence, strongest first; the real install is the evidence for the IDE, the
shipped bundle for the CLI:

- Real install: the Cursor IDE on macOS, builds 3.24.18, 3.25.9 and 3.26.13 (2026-10-19 and
  2026-10-20; [Observed](#observed)). Read for file names, sizes, key, table and column names,
  value types and enum values only; no value from the install is reproduced, and account ids are
  written `u<id>` and `auth0|user_<id>`.
- L1 shipped bundles. The IDE: Cursor 3.25.9 and 3.26.13 for macOS,
  `Cursor.app/Contents/Resources/app/out/vs/workbench/workbench.glass.main.js`, grepped for
  literal strings, cited below as `workbench.glass.main.js` with the snippet (byte offsets were
  not recorded). The CLI: Cursor Agent CLI `2026.10.01-e373342`, `agent-cli-package.tar.gz` from
  `downloads.cursor.com/lab/.../linux/x64/` (the URL is in the install script
  `https://cursor.com/install`, lines 78-131). Minified webpack chunks keep module names, so
  citations are `<chunk>.js` plus the original module path.
- L2 official docs: [Cursor CLI configuration](https://cursor.com/docs/cli/reference/configuration),
  [Cursor rules](https://cursor.com/docs/context/rules),
  [Cursor MCP](https://cursor.com/docs/context/mcp),
  [Cursor hooks](https://cursor.com/docs/agent/hooks),
  [Cursor ignore files](https://cursor.com/docs/context/ignore-files).
- L3 forum.cursor.com [thread 2825](https://forum.cursor.com/t/2825),
  [thread 167641](https://forum.cursor.com/t/167641),
  [thread 169582](https://forum.cursor.com/t/169582),
  [thread 172127](https://forum.cursor.com/t/172127),
  [How to delete a chat in Agent Window](https://forum.cursor.com/t/how-to-delete-a-chat-in-agent-window/163380/5)
  (fetched 2026-10-20).
- L4 write-ups and tools: [Callum-Ward/cursaves](https://github.com/Callum-Ward/cursaves)
  `docs/how-cursor-stores-chats.md`, extracurricular.ai (2026-09-09),
  [getagentseal/codeburn issue 986](https://github.com/getagentseal/codeburn/issues/986),
  [Cosmos-0118/AgentSweep](https://github.com/Cosmos-0118/AgentSweep) `rules/rules.toml`,
  [ShayGus/quota PR 20](https://github.com/ShayGus/quota/pull/20).
- The npm packages `cursor-agent` and `cursor-cli` are unrelated third-party projects (`npm view`),
  not Cursor's CLI.

### Observed

- macOS, Cursor IDE, 2026-10-19 and 2026-10-20
  ([issue 6](https://github.com/seanthegeek/doubleagent/issues/6) and
  [issue 51](https://github.com/seanthegeek/doubleagent/issues/51)): `Cursor.app`, bundle id
  `com.todesktop.230313mzl4w4u92`, 3.24.18 at first launch, 3.25.9 after an in-app update and
  3.26.13 after a second, in the author's macOS lab VM (macOS 26.6.2, Darwin 25.6.0, arm64), one
  user, one project (a git repository with one commit, `README.md` and `calc.py`), the agent pane
  of the Agents window and of the editor window. One step per listing, each diffed against the
  last (times UTC): the first launch, not signed in (2026-10-19 01:00Z), wrote the Electron
  profile of [Cursor IDE](#cursor-ide) and the `~/.cursor` entries of
  [`~/.cursor` as the IDE writes it](#cursor-as-the-ide-writes-it); sign-in (01:08Z) wrote the
  keys of [Credentials](#credentials), the built-in skills and the account's sync store
  ([AgentStores](#agentstores)); the in-app update to 3.25.9 (01:13Z) wrote the first
  [`update-supervisor`](#update-supervisor) directory; opening the project folder (01:16Z, with no
  workspace-trust prompt) wrote its workspace state, `~/.cursor/projects/<sanitized cwd>/`, the
  embedded Agent CLI ([Exclusions](#exclusions)) and a code index inside the repository's `.git`
  ([Project-local files](#project-local-files)); a question with no tool use (01:20Z) wrote the
  first composer ([Record schema](#record-schema)) and its JSONL copy
  ([Agent transcript JSONL](#agent-transcript-jsonl)); a code edit of `calc.py` (01:25Z), applied
  with no prompt, wrote tool bubbles, file-state rows, a retrieval checkpoint and tracking rows
  ([Other stores](#other-stores)); a shell command (01:31Z) ran with no prompt, because a new
  install defaults to the Auto-review run mode
  ([Run mode and standing lists](#run-mode-and-standing-lists)); switching the run mode to
  Allowlist (with Sandbox) (01:56Z) changed two settings; three `curl` commands under it were run
  (02:00Z), skipped (02:04Z) and allowed always (02:06Z), each recording its decision in its tool
  bubble ([Tool bubbles](#tool-bubbles)), the last adding two standing allowlist entries; a plan
  upgrade from free to Pro with an account merge (about 16:14Z to 16:38Z on 2026-10-20, two
  relaunches) and a model switch from `grok-4.6` to `grok-4.7` with no message sent (16:55Z) fell
  in one listing and were mapped by modification time; a question after the switch (17:39Z)
  recorded the new model on its user bubble ([Model rows](#model-rows)); a quit, two relaunches
  and the conversation reopened (17:44Z to 17:48Z) wrote nothing to the conversation
  ([Joins and timestamps](#joins-and-timestamps)); the update to 3.26.13 (17:57Z to 17:58Z) and
  a new conversation with one file read (created 17:56Z, answered 17:59Z) showed the layout of
  [Format versions](#format-versions); archiving the first conversation (18:09Z), exporting it
  to Markdown from the editor window (by 19:02Z), finding no Share there, and deleting it from
  the editor window (19:04Z) are in [What survives a delete](#what-survives-a-delete). The Agents
  window did not render the replies of 17:39Z and 17:59Z, which the store held whole and the
  editor window showed.
- Cursor Agent CLI, standalone (`agent`, `cursor-agent`, with its `~/.cursor/chats` and
  `acp-sessions` stores), any platform: not observed on any real install; bundle-derived
  ([Cursor Agent CLI](#cursor-agent-cli)).
- Cloud (background) agents and worktree agents, any platform: not observed on any real install.
- Windows and Linux, IDE and CLI: not observed on any real install; the IDE paths there are the
  macOS layout under the VS Code user-data-directory convention.

### Source reviews

- 2026-10-20: the IDE bundles 3.25.9 and 3.26.13 for macOS (`workbench.glass.main.js`, the run
  modes, the permission files and the delete commands) and the forum thread
  [How to delete a chat in Agent Window](https://forum.cursor.com/t/how-to-delete-a-chat-in-agent-window/163380/5).
  The document gained the run-mode table, the `permissions.json` and `sandbox.json` file names,
  and the delete surfaces, and the IDE's half was rewritten from the real install.

## Collection

### Per-user storage

Layout is identical on all OSes except the IDE app-data parent and the CLI `auth.json` location
([Credentials](#credentials)). The IDE layout below is the macOS install's
([Observed](#observed)); the Windows (`AppData/Roaming/Cursor`) and Linux (`.config/Cursor`)
parents follow the VS Code convention and were not observed.

#### Scratch directories

`~/.cursor/worktrees/<repo>/<name>`, the CLI's git worktrees (see
[Cursor Agent CLI](#cursor-agent-cli); excluded in [Exclusions](#exclusions)).

Outside the home, under `$TMPDIR` (`/private/var/folders/.../T/` on macOS), which no catalog line
reaches ([`collectors/docs/coverage.md`](../collectors/docs/coverage.md)):

- `cursor-agent-logs-<uid>/`: the IDE worker's logs, `session-<iso time>-<pid>-1.log` and a
  `latest.log` symlink. They were gone between 18:11Z and 19:02Z on 2026-10-20 with no user
  action, so they are not a durable source.
- `cursor-agent-worker-<hash>.sock`: the worker's socket.
- `<user>-cursor-zsh/`: copies of the user's `.zlogin`, `.zprofile`, `.zshenv` and `.zshrc`
  (0.6 to 10 KB each) for the IDE's zsh shell integration, seen on 2026-10-20.

#### Cursor IDE

IDE (VS Code fork; the generic layout is in
[User data directory of `research/vscode.md`](vscode.md#user-data-directory)):
`~/Library/Application Support/Cursor/User`, `%APPDATA%\Cursor\User`, `~/.config/Cursor/User` (forum
2825, 169582; cursaves; extracurricular). The chats live in `User/globalStorage/state.vscdb`
([Transcript stores](#transcript-stores)). The file is never vacuumed and reaches 30-125 GB
(forum 167641, 169582, 172127); `state.vscdb.backup` sits beside it.

What the macOS install held under `~/Library/Application Support/Cursor/`, with the catalog's
treatment:

| Path | Holds | Collected |
| --- | --- | --- |
| `User/globalStorage/state.vscdb` (+`-wal`, `-shm`) | the conversations, the settings and the tokens: tables `ItemTable`, `cursorDiskKV` and `composerHeaders` ([Record schema](#record-schema)); 2.9 MB before a quit checkpointed it to 2.2 MB | yes |
| `User/globalStorage/state.vscdb.backup` | a stale copy (forum) | excluded |
| `User/globalStorage/conversation-search.db` (+`-wal`, `-shm`) | the full-text index of the conversations ([`conversation-search.db`](#conversation-searchdb)) | yes |
| `User/globalStorage/storage.json` | VS Code window state (`windowsState`, `backupWorkspaces`, `lastKnownMenubarData`) and device ids; 12 KB, then 69 KB | yes |
| `User/globalStorage/anysphere.cursor-retrieval/checkpoints/<requestId>/` | shadow copies of the files an agent request edited ([Retrieval checkpoints](#retrieval-checkpoints)) | yes |
| `User/globalStorage/anysphere.cursor-agent-host/data.sqlite` | tables `ItemTable` and `cursorDiskKV`, empty throughout the round; first written by 3.25.9 | yes |
| `User/globalStorage/anysphere.cursor-agent-worker/agent-cli/` | the embedded Agent CLI, 608 MB in 453 files: `.local/share/cursor-agent/versions/2026.10.19-6bbf2c4/` (webpack chunks `NNNN.index.js` and binaries of 145-162 MB) and `.local/bin/cursor-agent`, a symlink into it | excluded |
| `User/globalStorage/anysphere.cursor-agent-worker/cursor-agent-worker-<hash10>.*` | the worker's control files: `owner.json` (`{ownerHash}`), `restart.json` (`{ownerHash, roots, version, workerId, workerName}`), `install` (23 bytes of text), `spec`, `<pid>.pid` and `log` | yes |
| `User/globalStorage/anysphere.cursor-agent-worker/worker-data/cursor-agent-worker-<hash>/` | the worker's own data directory in the CLI layout: `projects/<sanitized cwd>/{terminals,mcps}`, `logs/`, `worker.lock` (+`-journal`) | yes |
| `User/workspaceStorage/<id>/` | `workspace.json` and `state.vscdb` per opened folder, the directory name 32 hex digits (an md5 of the folder); `empty-window/` for a window with no folder ([Workspace `state.vscdb`](#workspace-statevscdb)) | yes |
| `User/History/<hex8>/entries.json` | VS Code's local file history | yes |
| `User/settings.json` | user settings (44 bytes) | yes |
| `logs/<launch stamp>/` | one directory per launch ([Logs](#logs)) | yes |
| `AgentStores/cursor_agent_stores/` | the account's and each composer's file-sync stores, 12.6 MB ([AgentStores](#agentstores)) | yes |
| `update-supervisor/<install uuid>/` | one directory per in-app update ([`update-supervisor`](#update-supervisor)); its `cursor-update-supervisor` is a 484 KB binary | yes, the binary excluded |
| `process-monitor/` | `<epoch ms>.log` every four hours (270-330 KB each, 1.4 MB in all) and `pending-uploads.json`: process logs | no: process state is the EDR's |
| `sentry/` | the crash reporter's scope with account and user context (44 KB) | no |
| `Cache`, `Code Cache`, `GPUCache`, `CachedData` (116 MB), `CachedProfilesData`, `CachedExtensionVSIXs` | Chromium and editor caches | no |
| `Cookies`, `DIPS`, `Local State`, `Preferences`, `Network Persistent State`, `Trust Tokens`, `SharedStorage`, `TransportSecurity`, `Crashpad`, `Backups`, `<version>-main.sock` (`3.24-main.sock`, `3.25-main.sock`) | the Chromium profile's state and the main process's socket | no |

Elsewhere under `~/Library`, none of it collected: the `defaults` domain
`com.todesktop.230313mzl4w4u92` (the bundle id); a `Preferences/ByHost/` property list and
`Caches/com.todesktop.230313mzl4w4u92.ShipIt/` (`ShipItState.plist` and logs) written by the
first in-app update, ShipIt being the updater component that `update-supervisor/events.jsonl` names
in its `shipit_*` event types; macOS's recent-documents list for the app,
`com.apple.LSSharedFileList.ApplicationRecentDocuments/<bundle id>.sfl4`, which named the
exported file ([Exported Markdown](#exported-markdown)); and a TCC (macOS's privacy permission
database) microphone grant to the bundle id.

#### `~/.cursor` as the IDE writes it

The IDE writes the CLI's data root (macOS install, 3.24.18 to 3.26.13; final sizes):

| Entry | Holds |
| --- | --- |
| `.gitignore` | a managed block, among its entries "Agent transcripts for citation" |
| `agents/`, `plugins/local/` | empty |
| `ai-tracking/ai-code-tracking.db` | lines of code the agent wrote and summaries per conversation, 72 KB ([`ai-code-tracking.db`](#ai-code-trackingdb)) |
| `argv.json` | Electron launch arguments, as in VS Code |
| `extensions/` | `anysphere.remote-ssh-1.1.16` and `extensions.json`, 1.3 MB; excluded |
| `projects/<sanitized cwd>/agent-transcripts/<composerId>/<composerId>.jsonl` | the worker's JSONL copy of each conversation ([Agent transcript JSONL](#agent-transcript-jsonl)) |
| `projects/<name>/mcps/<server>/{INSTRUCTIONS.md,SERVER_METADATA.json,tools/<tool>.json}` | the built-in MCP servers' tool manifests (`cursor-app-control`, `cursor-ide-browser`, `cursor-origin`, `cursor-subscriptions`), Cursor's own, rewritten at every launch, 44 KB |
| `projects/<name>/canvases/node_modules/` | type declarations (`@types/react`, `cursor/canvas`, `grok/canvas`), 226 KB per project; excluded |
| `projects/empty-window/` | the same for the window with no folder |
| `projects/.agent-data-cleanup-<date>` | an empty marker file |
| `skills-cursor/` | 26 built-in skills written at sign-in (automate, autopilot, canvas, create-hook, create-rule, create-skill, create-subagent, deploy-with-vercel, goal, loop, migrate-to-skills, new-repo, onboard, origin, rename-chat, review, review-bugbot, review-security, sdk, share, shell, split-to-prs, statusline, update-cli-config, update-cursor-settings, visualize), 392 KB |
| `statsig-cache.json` | a feature-flag cache from the server, 951 KB; excluded |
| `cli-config.json` | the CLI's settings, 837 bytes, written when the folder was opened ([`cli-config.json`, `permissions.json` and `sandbox.json`](#cli-configjson-permissionsjson-and-sandboxjson)) |
| `agent-cli-state.json` | `{version, workerIdsByDisplayName}`, the worker id per `<cwd> @ <hostname>` |
| `sandbox-policies/` | empty; created about 01:30Z on 2026-10-19 |

An IDE-run shell command left no `terminals/` capture under `projects/<sanitized cwd>/`, and
`~/.local/share/cursor-agent` and `~/.local/bin` stayed absent: the IDE's worker is its own copy
of the CLI.

#### Cursor Agent CLI

CLI data root `~/.cursor` (`CURSOR_DATA_DIR` override; `index.js` module
`../cursor-config/dist/paths.js`, function `c`). Config root for `cli-config.json` is
`CURSOR_CONFIG_DIR`, else `$XDG_CONFIG_HOME/cursor`, else `~/.cursor` (same module, function `a`;
docs cli/reference/configuration). Contents found in the bundle:

- `projects/<sanitized cwd>/` where the name is the path with every non-alphanumeric run replaced by
  `-` (`../utils/dist/workspace-paths.js` function `s`; `paths.js` function `d` truncates to 84
  chars plus a 7-hex sha256 suffix, falling back to `/tmp/.cursor` when the home path is too long).
  Inside: `agent-transcripts/` (`*.jsonl`, older `*.txt`), `terminals/` (terminal captures),
  `agent-tools/` (tool outputs over 51,380,224 bytes), `agent-notes/shared` and
  `agent-notes/<agent>`, `mcps/`, `mcp-auth.json`, `mcp-approvals.json`, `mcp-cache.json`,
  `.workspace-trusted` (`index.js` ignore list `!projects/*/...`; `./src/mcp/project-paths.ts`;
  `./src/workspace/approval.tsx`).
- `chats/<md5(resolved cwd)>/<sessionId>/store.db` plus `meta.json` (`7000.index.js`
  `./src/state/index.ts` functions `a`,`i`; `./src/state/chat-session-meta.ts` schema v1 with
  `createdAtMs`, `updatedAtMs`, `cwd`, `hasConversation`, `isSubagent`). `store.db` tables
  `meta(key,value)` and `blobs(id,data)` (codeburn 986).
- `acp-sessions/<id>/store.db` and `meta.json` (`6136.index.js`).
- `worktrees/<repo>/<name>` (`CURSOR_WORKTREES_ROOT`; `index.js` `./src/project/worktree.ts`),
  `plans/` (`1623.index.js`), `commands/`, `skills/`, `skills-cursor/`, `cloud-skills/`,
  `plugins/{local,marketplaces,local-marketplaces.json}` (`index.js`
  `../cursor-plugins/dist/index.js`), `sandbox-policies/` (`CURSOR_SANDBOX_POLICY_DIR`),
  `ide_state.json` (recently viewed files), `hooks.json`, `hooks/`,
  `managed/active-team-hooks/hooks.json` (`190.index.js`), `mcp.json` (docs),
  `ai-tracking/ai-code-tracking.db` (`2734.index.js`), `extensions/` and `argv.json` (dataFolderName
  convention; AgentSweep 859-872).
- Enterprise hooks: `/Library/Application Support/Cursor/hooks.json`, `/etc/cursor/hooks.json`,
  `C:\ProgramData\Cursor\hooks.json` (`190.index.js`; docs agent/hooks).
- CLI binaries: `~/.local/share/cursor-agent/versions/<ver>/`, symlinks
  `~/.local/bin/{agent,cursor-agent,cursor}` (install script lines 78-131; `2761.index.js`). Worker
  mode uses `/opt/cursor` or `~/.local/share/cursor-agent` as `--data-dir`.
- Remote SSH server `~/.cursor-server/` (serverDataFolderName convention; `2721.index.js` mentions
  downloading `cursor-server`); its `data/User` holds the remote side's editor state, as in
  [Remote server of `research/vscode.md`](vscode.md#remote-server).

### Credentials

- IDE: `User/globalStorage/state.vscdb` `ItemTable`, the same file as the chats, so it is
  collected unflagged and redacted by key
  ([ShayGus/quota PR 20](https://github.com/ShayGus/quota/pull/20), L4, confirmed on the macOS
  install, 3.24.18 to 3.26.13):
  - tokens: `cursorAuth/accessToken` and `cursorAuth/refreshToken`, 413 bytes each, plaintext
    JWT-shaped text (JSON Web Tokens, the signed bearer-token format); still plaintext on
    3.26.13, although the key `cursor.storage.authTokenEncryptionAtRest` (5 bytes) has existed since 3.25.9;
  - VS Code secret storage, one row per secret, keys beginning `secret://`:
    `secret://{"extensionId":"anysphere.cursor-agent-worker","key":"cursor-agent-worker.apiKey"}`
    (311 bytes, reissued at 323 bytes by the plan change), the matching `...apiKeyAuthId` row (207
    bytes), and `secret://{"extensionId":"vscode.git","key":"git-ipc-auth-token:<path>"}`, whose
    key holds the workspace-storage path; the values are encrypted with the Electron safeStorage
    key (Electron's keychain-held encryption key for app secrets), the login-keychain item
    `Cursor Safe Storage` / `Cursor Key`; redact every key with the prefix `secret://`;
  - account identity: `cursorAuth/cachedEmail`, `cursorAuth/cachedScopedProfile` (JSON
    `{authId, displayName}`), `cursorAuth/cachedSignUpType`, `cursorAuth/stripeMembershipAuthId`
    (37 bytes), `cursorAuth/stripeMembershipType` (plain text: `free`, then `premium` for the
    plan the UI calls Pro), `cursorAuth/stripeSubscriptionStatus` (`active`, from the upgrade) and
    `adminSettings.cachedAuthId`;
  - the account id `auth0|user_<id>`, URL-encoded `auth0%7Cuser_<id>`, is part of key names
    (`cloudAgentRepository.agents.*`, `cloudAgentRepository.serverPinnedBcIds.*`,
    `cursor/localLastActivityTimestampMs:*`,
    `agentData.cacheStorage.glass.cloudMcpServers.v1.personal.*`); the numeric account id is the
    `dashboardUserId` of the settings blob ([`ItemTable` keys](#itemtable-keys)) and the
    `u<id>` directory names of [AgentStores](#agentstores). The account merge at the plan change
    added a second numeric id and kept the `auth0|user_<id>` id.
- The IDE's sign-in on macOS added no keychain item.
- IDE device identifiers: `User/globalStorage/storage.json` `telemetry.devDeviceId` (a UUID),
  `telemetry.machineId` and `telemetry.macMachineId` (64 hex digits each).
- CLI (`index.js` `../cli-credentials/dist/index.js`, factory `d`): macOS uses the login keychain
  via `/usr/bin/security` (services `cursor-access-token`, `cursor-refresh-token`, `cursor-api-key`,
  `cursor-bedrock-*`, account `cursor-user`); every other OS, and macOS with
  `AGENT_CLI_CREDENTIAL_STORE=file`, writes `auth.json` (`accessToken`, `refreshToken`, `apiKey`,
  `bedrockCredentials`) at `$XDG_CONFIG_HOME/cursor/auth.json` or `~/.config/cursor/auth.json` on
  Linux, `~/.cursor/auth.json` on macOS, `%APPDATA%\Cursor\auth.json` on Windows (mode 0600). All
  three paths are flagged.
- MCP OAuth tokens per project: `~/.cursor/projects/<p>/mcp-auth.json` (`6136.index.js`,
  `8192.index.js`); flagged.
- `~/.cursor/mcp.json` and project `.cursor/mcp.json` carry server env blocks that often hold
  literal keys (docs recommend `${env:...}`); both are flagged, since the secret glob
  `.cursor/mcp.json` matches in the home and in a collected project.
- `~/.cursor_info` "holds a Cursor authentication token" (AgentSweep 904-910, L4 only, unverified).
- The zsh rc copies of [Scratch directories](#scratch-directories) can hold exported keys; they are
  outside the home and not collected.
- Not credentials, though their names suggest it (macOS install): `canvas-tokens.d.ts` and
  `tokens.d.ts` (TypeScript declarations of design tokens, under `canvases/node_modules` and
  `skills-cursor/canvas/sdk`), `browser_press_key.json` (an MCP tool manifest),
  `workbench.mcp.oauth.log` (MCP connection state changes, no token),
  `GitHub Authentication.*.log` ("Reading sessions from keychain", "Got 0 sessions") and
  `cursorAuthDebug.*.log` (0 bytes each).

### Exclusions

`.cursor/extensions` (extension payloads), `.cursor/worktrees` (git checkouts),
`.cursor/plugins/marketplaces` (cloned marketplaces),
`*/Cursor/User/globalStorage/state.vscdb.backup` (stale copy, up to 12 GB per forum 167641),
and `.cursor-server/bin` and `.cursor-server/extensions` (the remote server's binaries and
extensions, beside the collected `.cursor-server/data/User`). From the macOS install, copies of
what exists elsewhere:

- `*/User/globalStorage/anysphere.cursor-agent-worker/agent-cli`: the embedded Agent CLI, 608 MB
  of the install's 610 MB; the worker's control files and `worker-data/` beside it stay collected.
- `*/Cursor/update-supervisor/*/cursor-update-supervisor`: the 484 KB update helper binary.
- `.cursor/projects/*/canvases/node_modules`: type declarations, 226 KB per project.
- `.cursor/statsig-cache.json`: the server's feature flags, 951 KB.

`~/.local/share/cursor-agent` (557 MB per version) is not in the catalog. `projects/*/agent-tools`
holds only outputs over 49 MB; leave it to the size cap rather than exclude.

### Project-local files

`.cursor/rules/**/*.mdc`, `.cursorrules`, `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md` (`index.js`
`LocalCursorRulesService`; docs context/rules), `.cursor/mcp.json`, `.cursor/hooks.json`,
`.cursor/hooks/`, `.cursor/cli.json`, `.cursor/worktrees.json`, `.cursor/commands/`,
`.cursor/skills/`, `.cursor/skills-cursor/`, `.cursor/*.json` generally, `.cursorignore` (docs;
bundle). `.cursorindexingignore` appears in neither the bundle nor current docs.
`.cursor-plugin/marketplace.json` marks a plugin marketplace repo (docs). No per-project database.

The IDE bundle also reads `<root>/.cursor/permissions.json`, searched from the workspace root
down each path component, beside the user-level `~/.cursor/permissions.json` (`dataFolderName ??
".cursor"` + `permissions.json`, `workbench.glass.main.js`, 3.25.9), and the 3.25.9 renderer log
named `~/.cursor/sandbox.json` (absent; the log's error code `ENOPRO`); the install wrote none
of the three. Their fields are in [`cli-config.json`, `permissions.json` and
`sandbox.json`](#cli-configjson-permissionsjson-and-sandboxjson).

Opening the folder (3.25.9, 2026-10-19) wrote a code index inside the repository's git directory:
`.git/cursor/crepe/build.lock` and `.git/cursor/crepe/<HEAD sha>/{index.bin, metadata.json,
postings.bin}`, `metadata.json` holding `{git_revision, version}`. `.git/cursor` is not in
`PROJECT_CATALOG`.

### Where the project path is recorded

- `~/.cursor/chats/*/*/meta.json` key `cwd` (bundle `chat-session-meta.ts`);
  `~/.cursor/acp-sessions/*/meta.json` likewise.
- `~/.cursor/projects/<name>` is the sanitized cwd (lossy: `/home/u/a-b` and `/home/u/a_b` collide);
  the IDE names it the same way (`~/.cursor/projects/<sanitized cwd>/`, macOS install).
- IDE: `User/workspaceStorage/<md5>/workspace.json` `folder` (a `file://` URL).
- IDE, per conversation: `composerHeaders.value.workspaceIdentifier{id, uri{fsPath}}` and the
  same key in `composerData` (`id` is the `User/workspaceStorage/<id>/` directory name, checked on
  the 3.26.13 install), and `trackedGitRepos[].repoPath` in both
  ([`composerHeaders`](#composerheaders), [`composerData`](#composerdata)).
- IDE, per window: `ItemTable` `workspaceMetadata.entries` (`folderUri`, `paths[].uri`,
  `trackedGitRepos[].repoPath`, `workspaceId`) and `cursor/glass.additionalProjects`
  (`workspaceIdentifier.uri.fsPath`), and the path inside key names
  (`glass.localRepoBranchRecency.<abs path>`, `ofsContent:<composerId>:file://<path>`,
  `composer.autoAccept.lastSeenHeadSha` keys); the worker's `restart.json` `roots` and
  `agent-cli-state.json` display names (`<cwd> @ <hostname>`).

## Parsing

### Transcript stores

Relative to the home; the IDE's paths are given for macOS, with `.config/Cursor` and
`AppData/Roaming/Cursor` as the other platforms' parents.

| Store | Holds | Role |
| --- | --- | --- |
| `Library/Application Support/Cursor/User/globalStorage/state.vscdb` (+`-wal`) | every IDE conversation: `cursorDiskKV` rows per composer and per bubble, `composerHeaders` rows, and settings in `ItemTable` | primary |
| `.cursor/projects/<sanitized cwd>/agent-transcripts/<composerId>/<composerId>.jsonl` | the worker's copy of each conversation: user and assistant text and tool calls, no times, results or decisions | secondary |
| `.cursor/chats/<md5>/<sessionId>/store.db`, `.cursor/acp-sessions/<id>/store.db` | the standalone CLI's sessions | bundle-derived, not observed on any real install; not in this plan |

A conversation is a `composerData:<composerId>` row plus one `bubbleId:<composerId>:<bubbleId>`
row per bubble, ordered by the composer's header list
([`composerConvHeaders` and the header list](#composerconvheaders-and-the-header-list)); the
`composerHeaders` table holds one summary row per composer. Opening the app, a window or "new
chat" creates draft composers (`status` `none`, no headers), so composers outnumber
conversations: 11 `composerData` rows for 2 conversations by 3.26.13.

#### What survives a delete

Where delete lives. On 3.26.13 (2026-10-20) the Agents window's per-chat history menu holds Pin,
Rename, Edit Icon, Mark as Unread, Fork, Move to, Copy and Archive (or Unarchive), and its agent
pane's menu has no Delete, Export or Share; the editor window's chat history menu has Export and
Delete, and no Share. The forum says Delete "was intentionally replaced with Archive" in the
Agents window and "is still available in the chat history dropdown in the regular IDE editor
window"
([How to delete a chat in Agent Window](https://forum.cursor.com/t/how-to-delete-a-chat-in-agent-window/163380/5),
L3). The 3.26.13 bundle also has "Delete chat", the command `developer.deleteOldChats`
("Developer: Delete Old Chats...", prompting "Delete chats older than how many days?", logging
`[DeleteOldChats] Starting deletion of N chat(s) older than D days`, calling
`clearLegacyCheckpoints()` and then `deleteComposer`) and an account-level "Delete All Data"
("This will permanently delete all your data. This action cannot be undone."); none of these
three was exercised.

Archive (Agents window, 3.26.13, 2026-10-20) removes nothing: every bubble, checkpoint, `agentKv`
blob, transcript JSONL file and retrieval checkpoint stayed. It sets `composerHeaders.isArchived`
to 1 and `isArchived` true in the row's `value`, moves the row's `lastUpdatedAt` (column and
value) to the archive time, and sets `is_archived` 1 and `updated_at` to that time in
`conversation-search.db`; `composerData.isArchived` stays null. The rewrite also moved the
conversation's header list to the 3.26.13 layout ([Format versions](#format-versions)).

Delete (editor window, 3.26.13, 2026-10-20) acted at once, with no confirmation and no mention of
a server copy, and removed rows only, no file:

- removed: `composerData:<composerId>`, every `bubbleId:<composerId>:*` row (37), every
  `checkpointId:<composerId>:*` row (11), `composerConvHeaders:<composerId>:000000`,
  `ofsContent:<composerId>:file://...`, `composerRootWriterDiagnostic:<composerId>`, and the
  composer's `conversation-search.db` `conversations` row;
- left in `state.vscdb`: the `composerHeaders` row, with `isArchived` 1, `lastUpdatedAt` the delete
  time, `createdAt`, `agentLocation`, `workspaceIdentifier`, `totalLinesAdded`,
  `totalLinesRemoved`, `filesChangedCount` and `hasPendingPlan` intact and the `name` and
  `subtitle` keys dropped from `value`; `composerTranscriptHeightTail:<composerId>` (layout, no
  content); and 6 of the 163 `agentKv:blob:*` rows, whose JSON still names the composer id and
  holds the conversation's model messages ([`agentKv` blobs](#agentkv-blobs));
- left under `~/.cursor`: the conversation's transcript JSONL, all 28 lines, 4,276 bytes, with
  every user and assistant text and tool call; and its 2 `ai_code_hashes` rows in
  `ai-code-tracking.db`, which carry the composer id;
- left with no link to the conversation: its `AgentStores` store and `.control/<composerId>/`
  directory (names only, no content), and the code edit's retrieval checkpoint, whose join to the
  conversation was the deleted user bubble's `requestId`, so it remains unattributed shadow
  content;
- left wherever the user saved it: the exported Markdown ([Exported Markdown](#exported-markdown)).

The other conversation and its records were untouched. Deleting the project directory was not
exercised. The analyzer reads the surviving header, the transcript JSONL, the `agentKv` blobs
and `ai-code-tracking.db`
([Past-use rows and secondary sources](#past-use-rows-and-secondary-sources);
[Secondary sources](../analyzer/docs/output.md#secondary-sources)).

### Record schema

`state.vscdb` tables (3.24.18 to 3.26.13): `ItemTable(key, value)`, `cursorDiskKV(key, value)`
and `composerHeaders(composerId TEXT PRIMARY KEY, workspaceId TEXT, createdAt INTEGER,
lastUpdatedAt INTEGER, isArchived INTEGER, isSubagent INTEGER, recency INTEGER, checkpointAt
INTEGER, subagentTypeName TEXT, value TEXT)`, indexed on `(workspaceId, isSubagent, isArchived,
recency)` and `(recency, composerId)`. Values are JSON text unless a row says otherwise. The
`cursorDiskKV` key families:

| Key | Value |
| --- | --- |
| `composerData:<composerId>` | the composer ([`composerData`](#composerdata)); also `composerData:empty-state-draft` |
| `composerConvHeaders:<composerId>:<NNNNNN>` | a chunk of the header list, 3.26.13 ([`composerConvHeaders` and the header list](#composerconvheaders-and-the-header-list)) |
| `bubbleId:<composerId>:<bubbleId>` | a user bubble ([User bubbles](#user-bubbles)) |
| `bubbleId:<composerId>:<bubbleId>/s:<n>` | an assistant sub-bubble ([Assistant sub-bubbles](#assistant-sub-bubbles)) |
| `bubbleId:<composerId>:<bubbleId>/t:call-<uuid>-<n>` LF `fc_<uuid>_<n>` | a tool bubble; the key holds a literal line feed ([Tool bubbles](#tool-bubbles)) |
| `checkpointId:<composerId>:<checkpointId>`, `ofsContent:<composerId>:file://<path>`, `composer.content.<sha256>`, `inlineDiff:<workspaceId>:<uuid>`, `composer.autoAccept.lastSeenHeadSha`, `composer.autoAccept.lastSeenHeadTimestamp` | file state of an edit ([File-state rows](#file-state-rows)) |
| `agentKv:blob:<sha256>` | a content-addressed blob ([`agentKv` blobs](#agentkv-blobs)) |
| `composerDraft:<composerId>` | `{richText, text}`, an unsent draft (3.26.13; 35 characters on the install) |
| `composerRootWriterDiagnostic:<composerId>` | `{version, writerInstanceId, rendererRootBlobIdHex, previousRendererRootBlobIdHex, throughWriterSequence, writtenAtMs, writers, writersOmitted, predecessorVerified}`; `rendererRootBlobIdHex` (64 hex) names an `agentKv` blob |
| `composerTranscriptHeightTail:<composerId>`, `composerVirtualRowHeights:_recentIds`, `slashMenuItems/v7/local.glass.<workspace>`, `model-nudge.startup-trigger-session`, `model-nudge.startup-session`, `composer.composerHeaders.migratedToTable` | layout, menu and migration state, no conversation content |

#### `composerHeaders`

One row per composer, drafts included (5 rows by 3.26.13: two empty pre-login composers, the two
conversations and one composer the UI archived at once at 17:55:30Z, `status` `none`, no bubbles).
The columns duplicate the value's times; `workspaceId` is 32 hex digits, or `empty-window`.
`value` is JSON with the keys `type` (`head`), `composerId`, `name`, `subtitle`, `createdAt`,
`lastUpdatedAt`, `conversationCheckpointLastUpdatedAt`, `unifiedMode` (`agent`), `forceMode`
(`edit`), `hasUnreadMessages`, `contextUsagePercent`, `totalLinesAdded`, `totalLinesRemoved`,
`hasBlockingPendingActions`, `hasPendingPlan`, `isDraft`, `isWorktree`,
`worktreeStartedReadOnly`, `isSpec`, `isProject`, `isBestOfNSubcomposer`, `numSubComposers`,
`referencedPlans`, `trackedGitRepos[{repoPath, branches}]`, `workspaceIdentifier{id, uri}`,
`agentLocation{type, status, environment{id, uri{fsPath}}}` (`type` `local`, `status` `active`
on both conversations), `agentLocationHistory[{id, reason, timestamp, destination{type},
location}]` (`reason` `created`) and `isArchived`; a deleted conversation's row also had
`filesChangedCount`. The empty-window head has `isEphemeral`, a draft `draftTarget`,
`isArchived` and `hasBeenInSidebar`.

#### `composerData`

Keys seen (3.24.18 to 3.26.13): `_v`, `composerId`, `createdAt` and `lastUpdatedAt` (epoch ms
numbers), `lastReadAtMs`, `status` (`none` on a draft, `completed` after a turn), `name` (the
automatic title) and `subtitle`, `unifiedMode` (`agent`), `forceMode` (`edit`),
`conversationState` (an opaque string, 425 to 2,225 characters), `conversationMap` (`{}`: the
bubbles are rows of their own), `fullConversationHeadersOnly` (the header list, inline until
3.26.13), `modelConfig{modelName, maxMode, selectedModels[{modelId, parameters[{id, value}]}]}`
(parameters seen: `effort` `medium`, `context` `256k`), `latestChatGenerationUUID`,
`contextTokenLimit`, `contextTokensUsed`, `contextUsagePercent`,
`promptTokenBreakdown{categories[{id, label, characterCount, estimatedTokens}], maxTokens,
totalUsedTokens}`, `promptContextUsageTree{nodes[{id, parentId, categoryId, kind, label,
characterCount, estimatedTokens, contentAvailable}]}` (`kind` `tool_definition`),
`trackedGitRepos[{repoPath, branches}]`, `workspaceIdentifier{id, uri{fsPath}}`,
`conversationCheckpointLastUpdatedAt`, `blobEncryptionKey` and
`speculativeSummarizationEncryptionKey` (44-character strings), `isAgentic`, `isDraft`,
`isProject`, `isArchived` (null even when archived), `isBestOfNParent`, `isBestOfNSubcomposer`,
`isSpec`, `subComposerIds`, `subagentComposerIds`, `todos`, `queueItems`, `totalLinesAdded`,
`totalLinesRemoved`, `usageData`, `context`, `originalFileStates`, `newlyCreatedFiles` and
`capabilities[{type, data{bubbleDataMap}}]` (7 entries); a draft also has `draftTarget{environment
{id}, type}` (`existing`). A model switch rewrites `modelConfig` in place without moving
`lastUpdatedAt`.

#### `composerConvHeaders` and the header list

The header list is the ordered index of a composer's bubbles, one entry per bubble record:
`{bubbleId, type, grouping{isRenderable, hasText, isShortPlainText, hasThinking, capabilityType,
thinkingDurationMs, turnDurationMs, isKeptFinalAiVisibleOutsideWorkedForGroup,
toolDisplayComputed}, contentHeightHint, createdAt, startedAtMs, completedAtMs}`. `type` is 1 for
a user bubble and 2 for an assistant one; `bubbleId` is the bubble's id with its suffix, so
`<uuid>`, `<uuid>/s:<n>` or `<uuid>/t:call-<uuid>-<n>` LF `fc_<uuid>_<n>`, and is what follows
`bubbleId:<composerId>:` in the record's key. Up to 3.25.9 the list is
`composerData.fullConversationHeadersOnly`; on 3.26.13 it is a JSON array in
`composerConvHeaders:<composerId>:000000`, the six-digit suffix a chunk number (one chunk held 37
entries, 12,471 bytes, so a chunk's capacity is larger than any conversation seen), with
`fullConversationHeadersOnly` `[]`. On the install the list had one entry per bubble record (37
for 37).

#### User bubbles

`bubbleId:<composerId>:<bubbleId>` with `type` 1: `text` (what the user typed), `richText` (the
editor's structured form of the same text), `createdAt` (ISO 8601), `startedAtMs`,
`completedAtMs`, `requestId` (a UUID), `checkpointId` (a UUID), `modelInfo{modelName}`,
`agentMode` and `unifiedMode` (numbers), `tokenCount{inputTokens, outputTokens}`, `isAgentic`,
`isPlanExecution`, `context{...}`, `conversationState`, `contextWindowStatusAtCreation
{percentageRemaining, percentageRemainingFloat, tokenLimit, tokensUsed}` (from the second turn
on), and empty lists such as `toolResults`, `allThinkingBlocks`, `commits` and `deletedFiles`.
`modelInfo.modelName` is the model the turn was sent to (`grok-4.6` on the six turns before the
switch, `grok-4.7` after it).

#### Assistant sub-bubbles

One assistant turn is a `bubbleId` uuid whose records carry suffixes: `/s:<n>` for reasoning and
text, `/t:call-<uuid>-<n>` for tool calls, with one counter `n` across both, so the `/s:` indices
skip the slots taken by tool bubbles (`/s:0`, `/s:2`, `/s:3` beside `/t:call-<uuid>-1`). Every
assistant and tool bubble key carries a `/s:` or `/t:` suffix; only user bubbles have none
(3.26.13). A sub-bubble has `type` 2, its own `bubbleId`
(the uuid plus the suffix), `capabilityType`, `text`, `createdAt`, `startedAtMs`, `tokenCount
{inputTokens, outputTokens}`, `codeBlocks` and `requestId` (empty). A reasoning sub-bubble has
`capabilityType` 30, `thinking{text, signature}`, `thinkingDurationMs`, `thinkingStyle` and an
empty `text`; a text sub-bubble has `capabilityType` null, the reply in `text` and, on the last
of a turn, `turnDurationMs`. Assistant records have no `modelInfo`.

#### Tool bubbles

A tool bubble has `capabilityType` 15, `createdAt`, `startedAtMs`, `completedAtMs`, `tokenCount`
and `toolFormerData` with the keys `name`, `params` (a JSON string), `rawArgs` (a JSON string,
empty or absent on `edit_file_v2` and on a terminal command), `result` (a JSON string, 22 to 1,643
characters seen; an error object when the call was refused), `status` (`completed`, even for a
refused call), `tool` (a number), `toolCallId` (85 characters), `modelCallId` (85 characters, or
empty), `toolCallBinary` (base64), `toolIndex` and `additionalData`. Names seen:
`glob_file_search`, `get_mcp_tools`, `read_file_v2`, `edit_file_v2` and
`run_terminal_command_v2`. One bubble holds both the call and its result.

`additionalData` is absent on a call that ran with no review (a file read); a terminal command
that ran under auto-run has `{status, startedAtMs}`; a command the user was asked about has:

| Key | Values seen |
| --- | --- |
| `status` | `success` (ran), `rejected` (skipped) |
| `startedAtMs` | present when the command ran |
| `blockReason` | why it was held, e.g. `Not in allowlist: curl, head` |
| `reviewData.selectedOption` | `run` (Run), `skip` (Skip), `allowlistCommands` (Always run) |
| `reviewData.approvalType` | `user` |
| `reviewData.status` | `Done` |
| `reviewData.allowlistOptions` | `[{id, label, value, commandName, ancestorIds, tokens, tokenCount, indentLevel}]`, one per command in the line |
| `reviewData.candidatesForAllowlist`, `defaultAllowlistOptionIds`, `selectedAllowlistOptionIds` | the commands offered and preselected (`curl`, `head`) |
| `reviewData.appliedAllowlistOptionIds` | only after Always run: the entries added to the allowlist |
| `reviewData.hasClassifierSuggestions`, `reviewData.isShowingInput` | booleans |

The prompt the user answered offered Skip, Always run and Run (Allowlist (with Sandbox), 3.25.9,
2026-10-19).

#### File-state rows

An edit (3.25.9) wrote `checkpointId:<composerId>:<checkpointId>` (`{files[{uri{path},
isNewlyCreated, originalModelDiffWrtV0}], activeInlineDiffs, newlyCreatedFolders,
nonExistentFiles}`; a turn with no edit stores `{inlineDiffNewlyCreatedResources,
nonExistentFilesVersion}`), `ofsContent:<composerId>:file://<path>` (the file's text before the
edit, the path in the key), two `composer.content.<sha256>` rows (the file's text after and
before), `inlineDiff:<workspaceId>:<uuid>` (`{composerMetadata{composerId, composerGenerationID,
codeblockId, toolCallId}, diffId, generationUUID, originalTextLines, uri{path}}`) and
`composer.autoAccept.lastSeenHeadSha` (`{<repository path>: <commit sha>}`) with
`composer.autoAccept.lastSeenHeadTimestamp`.

#### `agentKv` blobs

`agentKv:blob:<sha256>` rows are the model calls' content, stored once per hash (11 after the
first question, 163 by the end: 44 JSON, 119 protobuf). The JSON ones are model messages,
`{role, content, providerOptions}` with `role` `system`, `user` or `assistant`, `content` a string
or an array of objects, and an
`id` (40 characters) on assistant messages: the user message is the whole prompt with its
context (30,511 bytes for a 37-character question) and the system message the system prompt
(4,441 bytes). The protobuf ones (first bytes `0A` or `1A`) are not decoded. No key names a
composer: a blob belongs to a conversation when the composer id occurs inside its `content` text,
that is, the prompt names it. Of the 6 rows that named the deleted conversation after its delete,
2 were JSON user messages (30,511 and 31,311 bytes) and 4 protobuf (615 to 653 bytes); 2 other
JSON blobs named the live conversation. They are plaintext, although the composer carries a
`blobEncryptionKey`.

#### `ItemTable` keys

Keys that hold conversation, permission and model evidence (macOS install):

- `src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser`:
  the settings blob, 493 KB of JSON; its keys are in
  [Run mode and standing lists](#run-mode-and-standing-lists), plus `aiSettings.modelConfig
  .<surface>{modelName, maxMode, selectedModels}` for the surfaces `composer`, `cmd-k`,
  `background-composer`, `plan-execution`, `quick-agent`, `spec`, `deep-search` and
  `composer-ensemble`; `aiSettings.modelLastUsedAt{<model id>: <ISO time>}` (9 ids, among them
  `grok-4.6` and `grok-4.7`, moved by a relaunch and by the switch);
  `availableDefaultModels2[{name, serverModelName, idAliases, supports*}]` (46);
  `cursorCreds{backendUrl, agentBackendUrl*, authClientId, authDomain}` (URLs and client ids, no
  secret); `dashboardUserId`; `membershipType` (`free`, then `premium`); `serverPrivacyMode`;
  `teamAdminSettings`; `teamBlocklist`; `mcpServers`; `mcpDisabledTools`;
  `cliDetectionStatus{agentStatus, claudeStatus, codexStatus}` (Cursor checks for other agents'
  CLIs); `authenticationSettings{githubLoggedIn}`; `backgroundComposerState`.
- `glass.agentConversationPanes.<id>` (`{activeTabId, tabAgentIds, version}`),
  `cursor/glass.selectedAgent`, `cursor/glass.lastRealAgent`,
  `glass/cursor.editorPanelVisibility.agent/<id>`, `cursor/glass.editorPanelFullscreen/<id>`:
  which conversation each pane shows.
- `glass.localRepoBranchRecency.<repository path>`: the branches used, `["main"]`.
- `cursor/localLastActivityTimestampMs`, `cursor/localLastActivityClientVersion` (also per
  account, `:auth0%7Cuser_<id>`).
- `cursor/glass.additionalProjects`, `cursor/glass.removedProjects`, `workspaceMetadata.entries`
  ([Where the project path is recorded](#where-the-project-path-is-recorded)).
- `cursorai/donotchange/{newPrivacyMode2, privacyMode, partnerDataShare,
  newPrivacyModeHoursRemainingInGracePeriod}` and `cursorai/serverConfig` (60 KB of server
  configuration); `adminSettings.cached` (792 bytes before sign-in).
- `cursor/agentAutorunBrandNewDefaultAttempted` (true, set before sign-in),
  `cursor/sandboxSupported`, `cursor/sandboxAutoRunSettingEnabled`.

#### Run mode and standing lists

The applicationUser blob's `composerState` holds the run mode per agent mode and the standing
lists. `modes4` has seven entries, `{id, autoRun, fullAutoRun, smartModeAutoRun, autoFix,
shouldAutoApplyIfNoEditTool, thinkingLevel, actionId, description, enabledMcpServers}`, with
`id` `agent`, `plan`, `chat`, `triage`, `spec`, `debug` and `multitask`; on the new install
`agent`, `triage` and `multitask` had `autoRun` true. No run-mode string is stored: the mode is
derived from the three flags and the `ItemTable` key `cursor/sandboxAutoRunSettingEnabled`
(true after the switch to Allowlist (with Sandbox); `cursor/sandboxSupported` true since the
folder opened):

| `autoRun` | `smartModeAutoRun` | `fullAutoRun` | sandbox key | Run mode (UI label) | Seen |
| --- | --- | --- | --- | --- | --- |
| false | any | false | any | Ask Every Time | bundle |
| true | false | false | absent or false | Allowlist | bundle |
| true | false | false | true | Allowlist (with Sandbox) | after the switch |
| true | true | false | absent or false | Auto-review | the new-install default |
| true | true | false | true | Auto-review (with Sandbox) | bundle |
| any | any | true | any | Run Everything | bundle |

The bundle (`workbench.glass.main.js`, 3.25.9) names the modes in two enums: `ASK_EVERY_TIME`
"Ask Every Time" ("Ask for permission before running each operation"), `USE_ALLOWLIST`
"Allowlist" / "Allowlist (with Sandbox)" ("Automatically run operations after you approve them
once"), `SMART_AUTO` "Auto-review" / "Auto-review (with Sandbox)" ("A classifier will run for
each action and decide whether it's safe to execute this command. Allowlists are still
respected.") and `RUN_EVERYTHING` "Run Everything" / "Run Everything (Unsandboxed)"
("Automatically run all operations without asking for permission"); and `ASK_EVERY_TIME`,
`YOLO`, `YOLO_WITH_SANDBOX`, `SMART_AUTO`, `SMART_AUTO_WITH_SANDBOX`, `FULL_YOLO`. The UI sets it
with the "Auto-Run" radio in settings, "Change run mode" in the agent pane, and the slash action
`/run-everything` ("Enable Run Everything for this agent"); an administrator can force it
(`defaultAgentRunMode`, e.g. `allowlist_without_sandbox`, `isAutoRunDisabledByAdmin`, refusals
"Run Everything is disabled by admin settings" and "... by permissions.json").

The standing lists and switches in `composerState`: `yoloCommandAllowlist` (`["curl", "head"]`
after Always run, `[]` before), `yoloCommandDenylist`, `smartAllowlistDenylist`,
`webFetchDomainAllowlist`, `autoApprovedModeTransitions` (all `[]`), and the booleans
`yoloEnableRunEverything` (false), `yoloDeleteFileDisabled` (false), `yoloMcpToolsDisabled`
(false), `yoloOutsideWorkspaceDisabled` (true), `autoApproveModeTransitions` (false),
`autoAcceptWebSearchTool` (false), `autoApplyFilesOutsideContext` (true),
`doNotShowYoloModeWarningAgain`, `doNotShowFullYoloModeWarningAgain`, `useLegacyTerminalTool`,
`playwrightProtection` and `mcpAuthBlocking`. Always run wrote only this list: no file changed.

#### Agent transcript JSONL

`~/.cursor/projects/<sanitized cwd>/agent-transcripts/<composerId>/<composerId>.jsonl`, written by
the worker beside each IDE turn (3.25.9 and 3.26.13). Line shapes:

- `{role: "user", message: {content: [{type: "text", text}]}}`; every user text block is the
  typed text in a fixed wrapper, `<timestamp>Monday, Oct NN, NNNN, N:NN PM
  (UTC-N)</timestamp>` LF `<user_query>Q</user_query>`: weekday name, abbreviated month, day,
  year, a 12-hour time with AM or PM and the UTC offset in parentheses, minute precision, in the
  local time zone (125 characters for a 37-character question); the query inside `<user_query>`
  is the user bubble's `text`;
- `{role: "assistant", message: {content: [...]}}` with blocks `{type: "text", text}` and
  `{type: "tool_use", name, input}`; `name` is a CamelCase tool name, not the snake_case
  `toolFormerData.name` (table below); `input` keys seen: `glob_pattern`;
  `namespace` and `toolName`; `path`; `path`, `old_string` and `new_string`; `command`,
  `description` and, for a command that needed a sandbox exception, `required_permissions`
  (`["full_network"]`);
- `{type: "turn_ended", status}` (`success`).

The user line's tag is the only time in the file; no line carries a model, tool result or
permission decision, so an approved and a skipped command have identical lines. The first
conversation's file grew from 3 to 28 lines over seven turns; the two conversations' files held
32 lines in all, 8 user, 16 assistant and 8 `turn_ended` (one per turn).

The transcript's tool names, matched to `toolFormerData.name` by their position in the round's
turns (one install, 3.25.9 and 3.26.13):

| Transcript `name` | `toolFormerData.name` |
| --- | --- |
| `GetDynamicTools` | `get_mcp_tools` |
| `Glob` | `glob_file_search` |
| `Read` | `read_file_v2` |
| `Shell` | `run_terminal_command_v2` |
| `StrReplace` | `edit_file_v2` |

### Joins and timestamps

The `composerId` joins `composerHeaders`, `composerData`, every `bubbleId:`,
`checkpointId:`, `ofsContent:`, `composerConvHeaders:`, `composerDraft:` and
`composerRootWriterDiagnostic:` key, the transcript JSONL's directory and file name,
`ai_code_hashes.conversationId`, the `conversation-search.db` `conversations.id`, the
`AgentStores` per-composer store and `.control/<composerId>/`. Bubble order is the header list's;
a tool call and its result are one bubble, keyed by `toolFormerData.toolCallId`; the
`inlineDiff` row names its `composerId` and `toolCallId`. A user bubble's `requestId` names the
retrieval checkpoint (`metadata.json` `agentRequestId`) and `ai_code_hashes.requestId`; its
`checkpointId` names the `checkpointId:` row. The transcript JSONL joins by composer id (its
directory and file name) and, within it, by text: no line has a bubble id or a tool-call id. A
user line's `<timestamp>` tag gives the turn's local time to the minute with its UTC offset, while
the user bubble's `createdAt` has milliseconds; assistant and `turn_ended` lines have no time.

Times: header entries and bubbles have `createdAt` (ISO 8601 with milliseconds) and `startedAtMs`
and `completedAtMs` (epoch ms); `composerData` and `composerHeaders` have `createdAt` and
`lastUpdatedAt` as epoch ms. `lastUpdatedAt` is the last time the composer was touched, not its
last message: an archive and a delete moved it, a model switch did not. The last message's time
is the last header entry's `startedAtMs` or `completedAtMs`. A resume writes nothing to the
conversation: after a quit, two relaunches and the conversation reopened, the bubbles,
`status`, `lastUpdatedAt` and headers were unchanged and `lastReadAtMs` stayed the last bubble's
`startedAtMs`; a relaunch shows only as a `logs/<launch stamp>/` directory and new drafts.

### Other stores

#### `conversation-search.db`

`User/globalStorage/conversation-search.db`: `conversations(fts_rowid, source, scope, id, title,
branches, updated_at, is_archived, root_fingerprint, cache_fingerprint)` with `source`
constrained to `local` or `cloud-cache` (only `local` seen), the FTS5 (SQLite's full-text search
module) table
`conversation_fts(title, body, branches)` with its shadow tables (`_idx`, `_config`, `_content`,
`_data`, `_docsize`), `conversation_search_candidates(id, updated_at)`,
`conversation_search_reconciliation(cursor, in_progress)` and
`conversation_search_settings(effective_conversation_cap)` (10000). One `conversations` row per
composer, drafts included (an empty title); `updated_at` is the composer's `lastUpdatedAt` in
epoch ms, refreshed at launch, and `is_archived` follows an archive. The FTS content holds the
conversation's text: title, the messages' text and the branches (42 characters of body in all
after the first question and its answer). A delete removes the row ([What survives a
delete](#what-survives-a-delete)).

#### `ai-code-tracking.db`

`~/.cursor/ai-tracking/ai-code-tracking.db`: `ai_code_hashes(hash, source, fileExtension,
fileName, requestId, conversationId, timestamp, model, createdAt)` (2 rows after the edit:
`source` `composer`, `conversationId` the composer id), `scored_commits(commitHash, branchName,
scoredAt INTEGER, linesAdded, linesDeleted, tabLinesAdded, tabLinesDeleted, composerLinesAdded,
composerLinesDeleted, humanLinesAdded, humanLinesDeleted, blankLinesAdded, blankLinesDeleted,
commitMessage, commitDate, v1AiPercentage, v2AiPercentage)` (the line counts INTEGER;
`commitMessage`, `commitDate` and the two percentages TEXT), `tracking_state(key, value)` (one
row, `trackingStartTime`),
`conversation_summaries(conversationId, title, tldr, overview, summaryBullets, model, mode,
updatedAt)`, `tracked_file_content(gitPath, content, conversationId, model, fileExtension,
createdAt)` and `ai_deleted_files(gitPath, composerId, conversationId, model, deletedAt)`. Only
`ai_code_hashes` and `tracking_state` had rows on the install. `ai_code_hashes.timestamp` is
epoch ms (a 13-digit integer); the unit of `createdAt` was not recorded.

#### Retrieval checkpoints

`User/globalStorage/anysphere.cursor-retrieval/checkpoints/<requestId>/`, one per agent request
that edited a file: `metadata.json` (`{agentRequestId, workspaceId,
startTrackingDateUnixMilliseconds, fileSizeBytes, requestFiles[{fileUuid, fsPath,
gitInfo{gitInfo{branch, commitHash, gitRoot}}}],
deduplicatedGitInfos}`), `files/<fileUuid>` (the file before the edit) and `diffs/<fileUuid>`
(`{fsPath, fileUuid, kind, numLines, fileSizeBytes, gitInfo, diffChanges[{original and modified
line ranges, addedLines, tokenizedAddedLines}]}`). The composer id is not in it.

#### Workspace `state.vscdb`

`User/workspaceStorage/<id>/state.vscdb` `ItemTable`, 12 to 18 keys: `aiService.prompts` and
`aiService.generations` (both `[]` throughout the round), `anysphere.cursor-retrieval`,
`cursor/agentLayout.sidebarLocation`, `cursor/sandboxSupported`,
`cursorAuth/workspaceOpenedDate`, `cursorHooks/lastDiskHooksLoadHadHooks`, `history.entries`,
`terminal.integrated.environmentVariableCollectionsV2`, `vscode.git`,
`workbench.view.remote.state` and
`workbench.customize.primitiveSourceSnapshot.{commands,rules,skills,subagents,mcps}.v3`.
`User/workspaceStorage/<id>/workspace.json` is `{folder}`.

#### `cli-config.json`, `permissions.json` and `sandbox.json`

`~/.cursor/cli-config.json`, the CLI's settings, written by the IDE and unchanged by the IDE's
run-mode switch and Always run: `approvalMode` (`allowlist`), `permissions{allow, deny}` (one
9-character entry, none), `sandbox{mode, networkAccess}` (`mode` `disabled`),
`attribution{attributeCommitsToAgent, attributePRsToAgent}`, `autoAcceptWebSearch`,
`display{mode}` (`zen`), `exploreSubagentModel` (`default`), `hasChangedDefaultModel`, `rewind`,
`steering` and `version`.

`permissions.json`, user and project level (bundle-derived, not observed on any real install;
`workbench.glass.main.js`, 3.25.9): `allowlists{mcp, terminal}`, `approvalMode`, and auto-run
instructions `{allowInstructions, blockInstructions}`; the bundle also names `terminalAllowlist`
and `approvalMode` as field sources. `sandbox.json`: name only, from the renderer log.

#### AgentStores

`AgentStores/cursor_agent_stores/` holds file-sync stores for agent assets such as skills, one per
account (`u<id>/`, from sign-in; a second after the account merge) and one per conversation
(`<composerId>/`, from the first edit): `.sync/index.sqlite`, `.sync/root-id` (36 bytes),
`.sync/root-id.lock`, `.sync/sync.lock` (`{acquiredAt, hostname, kind, pid, uid, windowId}`,
`kind` `ide`), `.sync/mount.json` on a conversation's store (`{kind, mountKey, readOnly,
version}`, `kind` `self`), `.sync/tmp/` and `files/` (`files/skills/` on the account's).
`index.sqlite` has `meta(key, value)` (`deletion_armed`, `files_root_birthtime_ms`,
`files_root_dev`, `files_root_ino`, `index_created_ms`, `last_complete_round_ms`,
`last_listing_applied_ms`, `remote_version`, `remote_version_listed_ms`, `root_id`,
`schema_version`, `tombstone_cursor_ms`, `tombstone_last_include_ms`,
`tombstone_rounds_since_include`), `files(rel_path, last_synced_sha, last_seen_etag, size,
last_synced_ms, direction, state, tombstone_etag, deleted_at_ms, stat_*)` (`direction` `pulled`
or `pushed`, `state` `live` or `tombstoned`), `pending_deletes` and `pending_rmdirs`. Every
`files` table stayed empty through the round.
`.control/<u<id> or composerId>/pins/<pid>-<uuid>.json`
(`{createdAtMs, hostname, pid, purpose, uid, version, windowId}`, `purpose` `foreground`) pins a
store per open window or conversation, and `.store-eviction-last-run` holds a number.

#### `update-supervisor`

`update-supervisor/<install uuid>/`, one per in-app update: `events.jsonl` (17 lines per update;
every line has `installationId`, `phase`, `recordedAt`, `schemaVersion` and `type`, which is one
of `supervisor_started{currentVersion, targetVersion, oldMainPid}`, `phase_changed{from, to,
reason}`, `shipit_state_changed`, `shipit_launchd_changed`, `shipit_install_started`,
`shipit_install_completed`, `shipit_relaunch_progress{line}`, `old_app_exited`,
`bundle_swapped{previousInode, currentInode, version}` and `new_app_ready`), `result.json`
(`{completedAt, details{currentVersion, elapsedMs}, finalPhase, installationId, schemaVersion,
status}`, `finalPhase` `confirmed`, `status` `success`), `app-ready.json` (`{currentVersion, pid,
readyAt}`) and the `cursor-update-supervisor` binary. Together they date each build the install
ran.

#### Exported Markdown

Export (editor window, 3.26.13, 2026-10-20) writes one Markdown file where the user saves it,
default name `export.md` (1,194 bytes and 89 lines for seven turns): `# <conversation title>`, a
line `_Exported on <M/D/YYYY at HH:MM:SS> <time zone> from Cursor (3.26.13)_`, then alternating
`**User**` and `**Cursor**` blocks separated by `---`. It has no per-turn time, tool call, tool
name, code fence, model or composer id: the prose only. Nothing in the app's stores records an
export; the app's recent-documents list names the file ([Cursor IDE](#cursor-ide)).

#### Logs

`logs/<launch stamp>/` (names only): `main.log`, `sharedprocess.log`, `composer.log`,
`conversationSearch.log`, `cursor-sentry-events.log`, `mcpprocess.log`,
`mcp-server-cursor-origin.log`, `cursorAuthDebug`, `cursor.requests`, and per window
`window<n>_wb<m>/`: `renderer.log`, `workbench.mcp.{allowlist,files,oauth}.log`,
`mcp-server-cursor-{origin,app-control,ide-browser,subscriptions}.workbench.log`,
`output_<stamp>/{cursor.hooks.workspaceId-<id>.log, cursor.requestTraces.log,
cursorAuthDebug.workspaceId-<id>.log, tasks.workspaceId-<id>.log}` and
`exthost/anysphere.cursor-{agent-exec,agent-worker,agent-host,always-local,mcp,retrieval,socket}/`
(`Cursor Agent Exec`, `Cursor Plugins`, `Mcp FileSystem Writer`, `Cursor Structured Logs`,
`Filesync`, `Cursor Indexing & Retrieval`, `MCP Logs`, and `Cursor Agent Host{, Network, Network
(debug), Storage}.workspaceId-<id>.<stamp>.log`).

### Format versions

- Before 3.0 (L4, cursaves; forum 2825, 167641): the composer list in `ItemTable`
  `composer.composerData` (<=2.6), then `composer.composerHeaders` (3.0+); the legacy chat in
  `ItemTable` `workbench.panel.aichat.view.aichat.chatdata`; `cursorDiskKV`
  `messageRequestContext:*` rows, not seen on the 3.24.18 to 3.26.13 install.
- 3.24.18 and 3.25.9 (observed): the headers in the `composerHeaders` table (`cursorDiskKV`
  `composer.composerHeaders.migratedToTable`, `ItemTable` `composer.composerHeaders.version`), the
  header list inline in `composerData.fullConversationHeadersOnly`. 3.25.9 added
  `anysphere.cursor-agent-host/data.sqlite` and `cursor.storage.authTokenEncryptionAtRest`.
- 3.26.13 (observed): a new conversation's header list is in
  `composerConvHeaders:<composerId>:<NNNNNN>` chunks, with `fullConversationHeadersOnly` `[]`; an
  older conversation keeps its inline list until the composer is rewritten, and archiving the
  first conversation moved its 37 entries into a chunk. Also new: `composerDraft:<composerId>` and
  `composerTranscriptHeightTail:<composerId>`. Tool names carry a `_v2` suffix on both 3.25.9 and
  3.26.13.
- `composerData._v` is 18 on every composer of the 3.26.13 install (12 rows);
  `composerRootWriterDiagnostic.version` carries a version whose value was not recorded.

### Secrets

The tokens, the secret-storage rows and the identity keys of `ItemTable` are listed in
[Credentials](#credentials). Inside the conversation stores: `composerData.blobEncryptionKey` and
`speculativeSummarizationEncryptionKey` (keys for blobs that were stored in plaintext anyway);
`cursorCreds` in the settings blob holds URLs and client ids, no secret; the hostname is in
`agent-cli-state.json` keys and in the `AgentStores` lock and pin files. User content beyond the
messages: the `agentKv` prompts with their context, the FTS index, the `ofsContent:` and
`composer.content.*` file texts, the retrieval checkpoints' file copies and
`tracked_file_content.content`.

### Parser plan

`wants()` by `artifact.rel`, with `(?:Library/Application Support|\.config|AppData/Roaming)/Cursor`
written `<ide>`:

```text
^<ide>/User/globalStorage/state\.vscdb$
^<ide>/User/globalStorage/conversation-search\.db$
^\.cursor/projects/[^/]+/agent-transcripts/[^/]+/[^/]+\.jsonl$
^\.cursor/ai-tracking/ai-code-tracking\.db$
^\.cursor/cli-config\.json$
^\.cursor/permissions\.json$
```

SQLite files are opened through `sqlite_util.py`. In `state.vscdb` the parser reads every
`composerData:` row; a composer with `status` `none` and an empty header list in both layouts is a
draft and yields nothing but its `composerDraft:` row. For the others it walks the header list
(`fullConversationHeadersOnly` when non-empty, else every `composerConvHeaders:<composerId>:*`
chunk in suffix order, concatenated) and reads `bubbleId:<composerId>:<entry bubbleId>` for each
entry.

| Record | `turn_type` and text |
| --- | --- |
| `composerHeaders` row or `composerData` with `name` | `system`, `session name: <name>` at `createdAt` |
| user bubble (`type` 1) | `user`, `text`, at `createdAt` |
| sub-bubble with `thinking.text` | `thinking`, `thinking.text` (only with `include_thinking`) |
| sub-bubble with non-empty `text` | `assistant`, `text`, at `createdAt` (else `startedAtMs`) |
| tool bubble | `tool_use`, `toolFormerData.params` (else `rawArgs`), at `startedAtMs`; then the permission row when `additionalData.reviewData` is present; then `tool_result`, `toolFormerData.result`, prefixed `[rejected] ` when `additionalData.status` is `rejected`, at `completedAtMs` |
| first user bubble with `modelInfo.modelName`; a later one with another | `system`, `model: <id>`; `model: <old> -> <new>` |
| `composerDraft:<composerId>` | `system`, `unsent draft: <text>` at the composer's `createdAt`, or with an empty `timestamp_utc` when it has none |
| `composerHeaders` `isArchived` 1 with its `composerData` present | `system`, `conversation archived` at `lastUpdatedAt` |
| `composerHeaders` row with no `composerData` and not a draft | `system`, `conversation deleted` at `lastUpdatedAt` ([Deletion rows](#deletion-rows)) |
| header entry with no bubble row | `system`, `parser: missing bubble <bubbleId>`, at the entry's `createdAt` |
| settings blob and `cli-config.json`, `permissions.json` | `system` permission and model rows ([Permission rows](#permission-rows), [Model rows](#model-rows)) |
| `ai-code-tracking.db`, `conversation-search.db`, transcript JSONL, `agentKv` blobs | [Past-use rows and secondary sources](#past-use-rows-and-secondary-sources) |

Columns:

| Column | Source |
| --- | --- |
| timestamp_utc | as in the table; epoch ms converted to UTC |
| session_id | the `composerId` |
| project_path | `composerHeaders.value.workspaceIdentifier.uri.fsPath`, else `composerData.workspaceIdentifier.uri.fsPath`, else the first `trackedGitRepos[].repoPath` |
| git_branch | the first entry of the matching `trackedGitRepos[].branches`, which was empty on the install; empty otherwise |
| model | the tracked `modelInfo.modelName` of the turn's user bubble |
| tool_name | `toolFormerData.name` |
| tool_use_id | `toolFormerData.toolCallId` |
| source_line | the `cursorDiskKV` rowid, or the 1-based line of a JSONL file, or the rowid of a table row |

#### Permission rows

Per call: a tool bubble whose `additionalData.reviewData` is present yields, after its `tool_use`
row, a `system` row `permission decision: <selectedOption> outcome=<additionalData.status>
approval=<approvalType> reason=<blockReason>`, then ` allowlisted=<entries>` when
`appliedAllowlistOptionIds` is present (the `commandName` of each matching `allowlistOptions`
entry, else the ids), with the call's `tool_use_id` and `tool_name`. A call that ran under
auto-run (`additionalData` without `reviewData`) or with no `additionalData` yields no permission
row; the run mode then in force is the standing row below. The record shapes are in
[Tool bubbles](#tool-bubbles).

Standing, at the modification time of the file, saying so in the text, with empty `session_id`:
from `state.vscdb`'s settings blob, one row per entry of `yoloCommandAllowlist`,
`yoloCommandDenylist`, `smartAllowlistDenylist`, `webFetchDomainAllowlist` and
`autoApprovedModeTransitions`, `permission setting: <list>=<entry> (from state.vscdb
composerState, file mtime)`; one per `modes4` entry, `permission setting: run mode <id>=<mode>
autoRun=<b> smartModeAutoRun=<b> fullAutoRun=<b> sandbox=<b>`, the mode derived as in
[Run mode and standing lists](#run-mode-and-standing-lists); and one per boolean switch of that
section. From `cli-config.json`: `approvalMode`, each `permissions.allow` and `permissions.deny`
entry and `sandbox.mode`. From `permissions.json` (bundle-derived, fixture only): each
`allowlists.mcp` and `allowlists.terminal` entry, `approvalMode`, and each `allowInstructions`
and `blockInstructions` entry.

#### Model rows

Per message the model is the user bubble's `modelInfo.modelName`: `model: <id>` at the first user
bubble that names one, `model: <old> -> <new>` at each later user bubble whose model differs;
assistant and tool rows take the tracked model. A switch in the UI writes no bubble, so it shows
only at the next message. `composerData.modelConfig` is the current selection with no history and
yields no row. The settings blob's `aiSettings.modelLastUsedAt` is the only dated record of a
switch: one `system` row per entry, `model last used: <id> (from state.vscdb
aiSettings.modelLastUsedAt)`, at its time, with empty `session_id`.

#### Past-use rows and secondary sources

- Transcript JSONL (secondary; `secondary()` true), `session_id` from the file name and
  `project_path` from the composer when the database has it. A user line yields a `user` row
  whose text is the query inside `<user_query>`, with the wrapper stripped, so it equals the user
  bubble's `text`, and whose `timestamp_utc` is the `<timestamp>` tag converted to UTC with its
  offset, at minute precision; a line whose wrapper does not parse keeps its whole text and an
  empty `timestamp_utc`. An assistant line yields an `assistant` row per text block and a
  `tool_use` row per tool block (`tool_name` the transcript's own CamelCase name, `text` the
  compact JSON of `input`), with an empty `timestamp_utc`, so they match on text alone; the
  mapping to the IDE's names in [Agent transcript JSONL](#agent-transcript-jsonl) was observed on
  one install and is not applied. `turn_ended` lines yield nothing. `secondary_tolerance()` is at
  least 60 seconds, because the tag has minute precision and the bubble's `createdAt` has
  milliseconds. The
  file survives a delete.
- `agentKv` blobs (secondary): a JSON blob whose `content` contains the id of a composer with a
  `composerHeaders` row but no `composerData` (a deleted conversation) yield `user` and
  `assistant` rows from
  `content` (a `system` message as `system prompt: <content>`), with an empty `timestamp_utc`
  and `source_line` the rowid. Blobs of a conversation still present are not yielded: their user
  text is the whole prompt with its context, which repeats the bubbles in a form deduplication
  cannot match. Protobuf blobs yield nothing.
- `ai-code-tracking.db` (not secondary: it repeats no event): `ai_code_hashes`, `system`, `ai
  code: <fileName> source=<source> model=<model> request=<requestId>` at `timestamp`;
  `conversation_summaries`, `system`, `conversation summary: <title>: <tldr>` at `updatedAt`;
  `ai_deleted_files`, `system`, `file deleted by agent: <gitPath> model=<model>` at
  `deletedAt`; `scored_commits`, `system`, `scored commit: <commitHash> branch=<branchName>
  +<linesAdded> -<linesDeleted>` at `scoredAt`; `session_id` the `conversationId`. Only
  `ai_code_hashes` was populated on the install.
- `conversation-search.db` (not secondary): one `system` row per `conversations` row with a
  title, `conversation index: <title> source=<source> archived=<is_archived>` at `updated_at`,
  `session_id` the `id`. A delete removes it, so it marks only conversations still present.
- The surviving `composerHeaders` row of a deleted conversation gives its `conversation deleted`
  row ([Deletion rows](#deletion-rows)).

The retrieval checkpoints, `AgentStores`, `update-supervisor`, the logs and an exported Markdown
file yield nothing: no times per turn, or no join to a conversation. The workspace
`aiService.prompts` key stayed `[]` and is not read.

#### Sync, relay and origin rows

The IDE recorded no sync of a local conversation (3.26.13, 2026-10-20): no Share or upload
surface, `agentLocation.type` `local` on both conversations, and every `AgentStores` `files` table
empty (those stores sync files such as skills, not transcripts). The parser yields `session
origin: remote <agentLocation.type>` when `agentLocation.type` is not `local` (bundle-derived:
only `local` was seen) and sets `records_origin`, so a local conversation's `origin` reads
`local`. `conversation-search.db` `source` `cloud-cache` (a cached cloud conversation,
bundle-derived) would mark a conversation held by the vendor; none was seen, and no sync row is
yielded. Relay: the agent records none.

#### Scratch directory rows

None under the home. The `$TMPDIR` directories of [Scratch directories](#scratch-directories) are
not collected.

#### Deletion rows

An archived conversation yields `conversation archived` at `lastUpdatedAt`. A `composerHeaders` row
whose `composerData` is gone, not a draft (it has an entry in `agentLocationHistory`, or
`isArchived` 1), yields `conversation deleted (header kept; time is the header's lastUpdatedAt)`
at `lastUpdatedAt`, with `project_path` from the header and `session_id` the composer id; the
archive time is lost, since the delete overwrote `lastUpdatedAt`. What survives a delete is in
[What survives a delete](#what-survives-a-delete).

#### Bad-line rows

The transcript JSONL is read with `iter_jsonl`, and each bad line becomes its own `system` row
through `error_rows`. A `cursorDiskKV` or `ItemTable` value that is not JSON (when it should be)
is appended to the errors list with its rowid and key, and a header entry with no bubble row has
its own row (table above). A database that is not SQLite is one `parser: not a SQLite database`
row, a SQLite error one `parser: SQLite error: <message>` row. `cli-config.json` or
`permissions.json` that is not JSON is one `parser:` row.

#### Fixtures

Synthetic records in the shapes above, invented values. `state.vscdb`, `cursorDiskKV`:

```json
{"key": "composerData:c1", "value": {"_v": 18, "composerId": "c1", "status": "completed", "name": "Add subtract", "createdAt": 1790000000000, "lastUpdatedAt": 1790000300000, "modelConfig": {"modelName": "grok-4.7", "maxMode": false, "selectedModels": [{"modelId": "grok-4.7", "parameters": [{"id": "context", "value": "256k"}]}]}, "workspaceIdentifier": {"id": "0123456789abcdef0123456789abcdef", "uri": {"fsPath": "/srv/proj"}}, "trackedGitRepos": [{"repoPath": "/srv/proj", "branches": []}], "fullConversationHeadersOnly": [{"bubbleId": "u1", "type": 1, "createdAt": "2026-10-01T10:00:00.000Z", "startedAtMs": 1790000000000, "completedAtMs": 1790000001000}, {"bubbleId": "a1/s:0", "type": 2, "createdAt": "2026-10-01T10:00:01.000Z"}, {"bubbleId": "a1/t:call-t1-1\nfc_t1_1", "type": 2, "createdAt": "2026-10-01T10:00:02.000Z"}, {"bubbleId": "a1/s:2", "type": 2, "createdAt": "2026-10-01T10:00:05.000Z"}, {"bubbleId": "u2", "type": 1, "createdAt": "2026-10-01T10:01:00.000Z"}, {"bubbleId": "a2/t:call-t2-0\nfc_t2_0", "type": 2, "createdAt": "2026-10-01T10:01:01.000Z"}, {"bubbleId": "a2/t:call-t3-1\nfc_t3_1", "type": 2, "createdAt": "2026-10-01T10:01:10.000Z"}, {"bubbleId": "a2/t:call-t4-2\nfc_t4_2", "type": 2, "createdAt": "2026-10-01T10:01:20.000Z"}]}}
{"key": "bubbleId:c1:u1", "value": {"type": 1, "text": "Add a subtract function", "createdAt": "2026-10-01T10:00:00.000Z", "requestId": "r1", "checkpointId": "k1", "modelInfo": {"modelName": "grok-4.6"}}}
{"key": "bubbleId:c1:a1/s:0", "value": {"type": 2, "bubbleId": "a1/s:0", "capabilityType": 30, "text": "", "thinking": {"text": "Read calc.py first.", "signature": "sig"}}}
{"key": "bubbleId:c1:a1/t:call-t1-1\nfc_t1_1", "value": {"type": 2, "capabilityType": 15, "startedAtMs": 1790000002000, "completedAtMs": 1790000002500, "toolFormerData": {"name": "read_file_v2", "params": "{\"path\":\"/srv/proj/calc.py\"}", "rawArgs": "{\"path\":\"calc.py\"}", "result": "{\"contents\":\"def add(a, b): ...\"}", "status": "completed", "tool": 40, "toolCallId": "tc1", "modelCallId": "mc1", "toolIndex": 0}}}
{"key": "bubbleId:c1:a1/s:2", "value": {"type": 2, "capabilityType": null, "text": "Added subtract().", "turnDurationMs": 5000}}
{"key": "bubbleId:c1:u2", "value": {"type": 1, "text": "Fetch the page with curl", "createdAt": "2026-10-01T10:01:00.000Z", "modelInfo": {"modelName": "grok-4.7"}}}
{"key": "bubbleId:c1:a2/t:call-t2-0\nfc_t2_0", "value": {"type": 2, "capabilityType": 15, "toolFormerData": {"name": "run_terminal_command_v2", "params": "{\"command\":\"curl -s example.test | head\"}", "rawArgs": "", "result": "{\"output\":\"ok\"}", "status": "completed", "toolCallId": "tc2", "additionalData": {"status": "success", "startedAtMs": 1790000061000, "blockReason": "Not in allowlist: curl, head", "reviewData": {"selectedOption": "run", "approvalType": "user", "status": "Done", "allowlistOptions": [{"id": "curl", "commandName": "curl"}, {"id": "head", "commandName": "head"}]}}}}}
{"key": "bubbleId:c1:a2/t:call-t3-1\nfc_t3_1", "value": {"type": 2, "capabilityType": 15, "toolFormerData": {"name": "run_terminal_command_v2", "params": "{\"command\":\"curl -s example.test | head\"}", "result": "{\"error\":\"skipped\"}", "status": "completed", "toolCallId": "tc3", "additionalData": {"status": "rejected", "blockReason": "Not in allowlist: curl, head", "reviewData": {"selectedOption": "skip", "approvalType": "user", "status": "Done"}}}}}
{"key": "bubbleId:c1:a2/t:call-t4-2\nfc_t4_2", "value": {"type": 2, "capabilityType": 15, "toolFormerData": {"name": "run_terminal_command_v2", "params": "{\"command\":\"curl -s example.test | head\"}", "result": "{\"output\":\"ok\"}", "status": "completed", "toolCallId": "tc4", "additionalData": {"status": "success", "startedAtMs": 1790000080000, "blockReason": "Not in allowlist: curl, head", "reviewData": {"selectedOption": "allowlistCommands", "approvalType": "user", "status": "Done", "allowlistOptions": [{"id": "curl", "commandName": "curl"}, {"id": "head", "commandName": "head"}], "appliedAllowlistOptionIds": ["curl", "head"]}}}}}
{"key": "composerData:c2", "value": {"composerId": "c2", "status": "completed", "name": "Read the README", "createdAt": 1790001000000, "fullConversationHeadersOnly": []}}
{"key": "composerConvHeaders:c2:000000", "value": [{"bubbleId": "u3", "type": 1, "createdAt": "2026-10-01T10:20:00.000Z"}, {"bubbleId": "a3/s:0", "type": 2, "createdAt": "2026-10-01T10:20:02.000Z"}]}
{"key": "bubbleId:c2:u3", "value": {"type": 1, "text": "What does the README say?", "modelInfo": {"modelName": "grok-4.7"}}}
{"key": "bubbleId:c2:a3/s:0", "value": {"type": 2, "text": "It describes calc.py."}}
{"key": "composerData:d1", "value": {"composerId": "d1", "status": "none", "fullConversationHeadersOnly": []}}
{"key": "composerDraft:d1", "value": {"richText": "{}", "text": "draft not sent"}}
{"key": "agentKv:blob:00ff", "value": {"role": "user", "content": "<context>conversation c3</context>\n<user_query>c3 deleted question</user_query>", "providerOptions": {}}}
{"key": "agentKv:blob:0a0b", "value": "<protobuf bytes, not JSON>"}
```

`composerHeaders` rows: `c1` (`isArchived` 0), `c2` (`isArchived` 1, `value.isArchived` true,
`lastUpdatedAt` 1790002000000) and the deleted `c3`, which has no `composerData:c3`:

```json
{"composerId": "c3", "workspaceId": "0123456789abcdef0123456789abcdef", "createdAt": 1789990000000, "lastUpdatedAt": 1790003000000, "isArchived": 1, "isSubagent": 0, "value": {"type": "head", "composerId": "c3", "createdAt": 1789990000000, "lastUpdatedAt": 1790003000000, "isArchived": true, "agentLocation": {"type": "local", "status": "active"}, "agentLocationHistory": [{"id": "l1", "reason": "created", "timestamp": 1789990000000}], "workspaceIdentifier": {"id": "0123456789abcdef0123456789abcdef", "uri": {"fsPath": "/srv/proj"}}, "totalLinesAdded": 0, "totalLinesRemoved": 0}}
```

`ItemTable` settings blob:

```json
{"composerState": {"modes4": [{"id": "agent", "autoRun": true, "smartModeAutoRun": false, "fullAutoRun": false}], "yoloCommandAllowlist": ["curl", "head"], "yoloCommandDenylist": [], "yoloOutsideWorkspaceDisabled": true}, "aiSettings": {"modelLastUsedAt": {"grok-4.7": "2026-10-01T09:59:00.000Z"}}}
```

with `cursor/sandboxAutoRunSettingEnabled` `true`.
`.cursor/projects/srv-proj/agent-transcripts/c1/c1.jsonl`, the live conversation's copy, whose
user lines match the bubbles `u1` and `u2` (10:00Z and 10:01Z, written at UTC-4):

```json
{"role": "user", "message": {"content": [{"type": "text", "text": "<timestamp>Thursday, Oct 1, 2026, 6:00 AM (UTC-4)</timestamp>\n<user_query>Add a subtract function</user_query>"}]}}
{"role": "assistant", "message": {"content": [{"type": "text", "text": "Added subtract()."}]}}
{"type": "turn_ended", "status": "success"}
{"role": "user", "message": {"content": [{"type": "text", "text": "<timestamp>Thursday, Oct 1, 2026, 6:01 AM (UTC-4)</timestamp>\n<user_query>Fetch the page with curl</user_query>"}]}}
{"role": "assistant", "message": {"content": [{"type": "tool_use", "name": "Shell", "input": {"command": "curl -s example.test | head", "description": "Fetch the page", "required_permissions": ["full_network"]}}]}}
{"type": "turn_ended", "status": "success"}
```

followed by a truncated line written with `write_bad_line`; and
`.cursor/projects/srv-proj/agent-transcripts/c3/c3.jsonl`, the deleted conversation's:

```json
{"role": "user", "message": {"content": [{"type": "text", "text": "<timestamp>Wednesday, Sep 30, 2026, 9:30 PM (UTC-4)</timestamp>\n<user_query>c3 deleted question</user_query>"}]}}
{"role": "assistant", "message": {"content": [{"type": "text", "text": "Answer kept only here."}]}}
{"type": "turn_ended", "status": "success"}
```

`ai-code-tracking.db` `ai_code_hashes`, two rows: (`hash` `h1`, `source` `composer`,
`fileExtension` `py`, `fileName` `/srv/proj/calc.py`, `requestId` `r1`, `conversationId` `c1`,
`timestamp` 1790000003000, `model` `grok-4.6`) and (`hash` `h2`, the same but `conversationId`
`c3`, `requestId` `r9`, `timestamp` 1789990060000), the second naming the deleted conversation.
Noise files
the parser must not want: `.cursor/statsig-cache.json` and
`.cursor/projects/srv-proj/mcps/cursor-ide-browser/SERVER_METADATA.json`. Expected: for `c1`, a
`session name:` row, `model: grok-4.6`, the user row, a thinking row only with `include_thinking`,
the read's `tool_use` and `tool_result` with no permission row, the assistant row, `model:
grok-4.6 -> grok-4.7`, and three commands each with `tool_use`, a `permission decision:` row
(`run`, `skip` with a `[rejected] ` result, `allowlistCommands` with `allowlisted=curl,head`)
and `tool_result`; for `c2`, rows from the chunk and `conversation archived`; for `c3`,
`conversation deleted`, the JSON blob's `user` row (the protobuf blob yields nothing), the
transcript's `user` row (`c3 deleted question` at 2026-10-01T01:30:00.000Z) and `assistant` row,
and its `ai code:` row; for `d1`, `unsent draft: draft not sent`;
standing rows for the two allowlist entries, the `agent` run mode `Allowlist (with Sandbox)` and
the switch; `model last used: grok-4.7`; `c1`'s `ai code:` row; and from `c1`'s transcript two
`user` rows (`Add a subtract function` at 10:00:00.000Z, `Fetch the page with curl` at
10:01:00.000Z) that deduplicate against `u1` and `u2`, an `assistant` row that matches the
bubble's text, a `tool_use` row with `tool_name` `Shell`, then the `parser:` row for the
truncated line.

## Confidence

- High, observed on macOS (Cursor IDE 3.24.18 to 3.26.13, one step per listing): the IDE's files
  and key families, the record shapes, the permission and model records, the archive and delete
  results, and the 3.26.13 header chunks.
- High (L1 bundle): the CLI's `~/.cursor` layout, `chats/` and `acp-sessions/` with `store.db`,
  the `projects/` name sanitization, worktrees, hooks, `ai-tracking`, and the CLI's `auth.json`
  and keychain logic; the IDE's run-mode names and delete commands.
- Medium: `.cursor-server` (convention plus L4); the Windows and Linux IDE paths (convention, not
  observed).
- Low: `~/.cursor_info` (a single L4 claim).
- Not determined: the standalone CLI's stores on a real install; whether `store.db` blobs are
  encrypted (`blobEncryptionKey` in `meta`, codeburn 986); whether the Windows CLI uses
  `%APPDATA%\Cursor\auth.json` or the IDE's directory of the same name; the status of
  `.cursorindexingignore`; the protobuf `agentKv` blobs; the transcript's tool-name mapping beyond
  the five names of one install; the form of a positive UTC offset in the transcript tag, and
  whether the tag truncates or rounds the seconds; whether `messageRequestContext:*` rows still
  appear on any 3.x build; the unit of `ai_code_hashes.createdAt`; subagent composers
  (`isSubagent`, `subagentComposerIds`), cloud
  and worktree agents, and a `cloud-cache` row in `conversation-search.db`; what the editor
  window's Delete does on a conversation that was not archived first, and what deleting the
  project directory leaves.
