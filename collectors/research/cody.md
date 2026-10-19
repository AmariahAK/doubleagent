# Sourcegraph Cody: on-disk paths

Catalog agent: `cody`. Cody is Sourcegraph's coding assistant, shipped as
a VS Code extension (`sourcegraph.cody-ai`), a JetBrains plugin and a
`cody` CLI; the last two run the same TypeScript "agent" in a Node
process. **In VS Code, chat history and the access token are not files:
they are rows in the editor's `User/globalStorage/state.vscdb`**, which
the `vscode` entries already collect. The extension's own
`globalStorage` folder holds only a local search index. The JetBrains
plugin keeps the same chat history as files under an `env-paths`
directory named `Cody-nodejs` (the CLI keeps it in memory). Transcript schema is in
[`analyzer/research/cody.md`](../../analyzer/research/cody.md).

## 1. Source and evidence level

[sourcegraph/cody-public-snapshot](https://github.com/sourcegraph/cody-public-snapshot), commit
[`8e20ac6c1460c08b0db581c0204658112a246eda`](https://github.com/sourcegraph/cody-public-snapshot/commit/8e20ac6c1460c08b0db581c0204658112a246eda)
(2025-08-01), VS Code extension version 1.116.0
([`vscode/package.json:3-7`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/package.json#L3-L7)). **The source
is frozen.** Sourcegraph moved Cody to a private repository and this is the
copy taken just before
([`README.md:1-5`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/README.md#L1-L5)); the README names
[`d7fc674`](https://github.com/sourcegraph/cody-public-snapshot/commit/d7fc6741e7893e3f6e29efe58043f1afe08d505f)
as the last Apache-2.0 commit, while the `LICENSE` file at HEAD is still
Apache-2.0 text. The shipped extension may have moved on; every claim
below is about the extension as of August 2025. Home-directory resolution
of `env-paths` is cited from its source at the locked version 2.2.1
(`pnpm-lock.yaml`). VS Code storage mechanics are cited from the PearAI
fork of VS Code 1.96.4, the only VS Code checkout read in this round; see
[vscode.md](vscode.md) for upstream.

- **Source review (2026-10-19)**: the repository's HEAD on 2026-10-19 is
  still
  [`8e20ac6`](https://github.com/sourcegraph/cody-public-snapshot/commit/8e20ac6c1460c08b0db581c0204658112a246eda),
  committed 2025-08-01 and the commit this document already cited; the
  public source has been frozen since August 2025, so nothing later can
  be reviewed. Per class (the record-level detail is in
  [section 1 of `analyzer/research/cody.md`](../../analyzer/research/cody.md#1-source)):
  - Permission state: found. Standing settings live in the editor's user
    `settings.json` (`cody.agentic.context.experimentalOptions`,
    `cody.mcpServers`), already collected with the editor, and for the
    JetBrains plugin in the IDE's `options/cody.xml`, which is not
    collected ([section 2](#2-per-user-storage)).
  - Model: found `cody-model-preferences`, a key inside files already
    collected (the `state.vscdb` row, `JetBrains-globalState/`).
  - Past use beyond the primary store: found the JetBrains plugin's
    pre-agent `<project>/.idea/cody_history.xml`, never deleted after
    migration and not collected ([section 5](#5-project-local-files)).
  - Sync, relay and origin: none recorded on disk (already covered in
    the analyzer document).
  - Scratch directories: none ([section 2](#2-per-user-storage)).
  - Deletion: clear and delete rewrite the history value in place; no
    file is removed
    ([section 8 of `analyzer/research/cody.md`](../../analyzer/research/cody.md#8-parser-plan)).
  - Version drift: none; the snapshot is HEAD.
  - Bad lines: not a collector concern; the analyzer reads each history
    as one JSON value.
  - Correction: the `cody chat` CLI keeps global state, chat history
    included, in memory and writes no `Cody-nodejs/<name>-globalState`
    directory
    ([`agent/src/cli/command-chat.ts:141-158`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/cli/command-chat.ts#L141-L158);
    [`agent/src/global-state/AgentGlobalState.ts:23-33`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/global-state/AgentGlobalState.ts#L23-L33)).

## 2. Per-user storage

**VS Code extension.**

- Global state: `localStorage.setStorage(context.globalState)`
  ([`vscode/src/main.ts:133-136`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/main.ts#L133-L136)). VS
  Code stores an extension's global state as one JSON value under the
  extension id in `ItemTable` of `User/globalStorage/state.vscdb`
  ([PearAI `extensionStorage.ts:159-161`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/platform/extensionManagement/common/extensionStorage.ts#L159-L161),
  [`170-175`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/platform/extensionManagement/common/extensionStorage.ts#L170-L175)).
  So the row key is `sourcegraph.cody-ai` and its value is a JSON object
  whose keys include `cody-local-chatHistory-v2` (all chat history),
  `SOURCEGRAPH_CODY_ENDPOINT` (last server), `SOURCEGRAPH_CODY_ENDPOINT_HISTORY`,
  `sourcegraphAnonymousUid`, `cody-model-preferences`,
  `cody-github-repo-metadata`
  ([`vscode/src/services/LocalStorageProvider.ts:29-39`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L29-L39)).
  History is keyed by `<endpoint>-<username>`
  ([`LocalStorageProvider.ts:393-397`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L393-L397)),
  so one row can hold several accounts' chats.
- `User/globalStorage/sourcegraph.cody-ai/symf/`: the downloaded `symf`
  search binary `symf-<version>-<arch>-<platform>`
  ([`vscode/src/local-context/download-symf.ts:53-56`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/local-context/download-symf.ts#L53-L56),
  [`118`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/local-context/download-symf.ts#L118)) and
  `symf/indexroot/<absolute workspace path>/`, one index per indexed
  folder; on Windows the drive colon is dropped
  ([`vscode/src/local-context/symf.ts:74`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/local-context/symf.ts#L74),
  [`396-411`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/local-context/symf.ts#L396-L411)), plus
  `.tmp/`, `.trash/` and `.failed/<path with / as __>` sentinels
  ([`symf.ts:339`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/local-context/symf.ts#L339),
  [`514-517`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/local-context/symf.ts#L514-L517)). Enabled by
  default (`cody.experimental.symf.enabled`;
  [`vscode/src/extension.node.ts:33-35`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/extension.node.ts#L33-L35)).
- `~/.vscode/cody.json`: user custom commands, in the home, not the
  user data directory
  ([`vscode/src/commands/services/custom-commands.ts:20`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/services/custom-commands.ts#L20),
  [`46-48`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/services/custom-commands.ts#L46-L48);
  [`vscode/src/commands/types.ts:9-15`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/types.ts#L9-L15)).
  The `vscode` entries do not collect it today.
- Output channel logs go to the editor's `logs/` tree, already collected.

**JetBrains plugin and CLI (agent).** Paths come from
`envPaths('Cody')` ([`lib/shared/src/codyPaths.ts:3`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/codyPaths.ts#L3)),
which appends `-nodejs` by default
([env-paths `index.js:54-59`](https://github.com/sindresorhus/env-paths/blob/62d4ec8cd42f1a419e00856fab949ca8286773f6/index.js#L54-L59)):

| | data | config | log |
| --- | --- | --- | --- |
| Linux | `~/.local/share/Cody-nodejs` | `~/.config/Cody-nodejs` | `~/.local/state/Cody-nodejs` |
| macOS | `~/Library/Application Support/Cody-nodejs` | `~/Library/Preferences/Cody-nodejs` | `~/Library/Logs/Cody-nodejs` |
| Windows | `%LOCALAPPDATA%\Cody-nodejs\Data` | `%APPDATA%\Cody-nodejs\Config` | `%LOCALAPPDATA%\Cody-nodejs\Log` |

([env-paths `index.js:9-47`](https://github.com/sindresorhus/env-paths/blob/62d4ec8cd42f1a419e00856fab949ca8286773f6/index.js#L9-L47); XDG variables honoured
on Linux only.) The agent sets `globalStorageUri` and `storageUri` to
data, `logUri` to log, and copies extension resources into
`<config>/dist` ([`agent/src/agent.ts:120-137`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/agent.ts#L120-L137),
[`159-161`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/agent.ts#L159-L161),
[`180-189`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/agent.ts#L180-L189)).

- `<data>/JetBrains-globalState/`: the JetBrains plugin asks for
  server-managed global state
  ([`jetbrains/.../CodyAgentService.kt:203`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/agent/CodyAgentService.kt#L203)),
  with client name `JetBrains`
  ([`CodyAgent.kt:136-137`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/agent/CodyAgent.kt#L136-L137)),
  so the agent opens `<data>/<name>-globalState` with `node-localstorage`
  ([`agent/src/agent.ts:1470-1476`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/agent.ts#L1470-L1476);
  [`agent/src/global-state/AgentGlobalState.ts:115-121`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/global-state/AgentGlobalState.ts#L115-L121)).
  Each key is one file named by its URL-encoded key, holding the JSON value
  ([`AgentGlobalState.ts:134-140`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/global-state/AgentGlobalState.ts#L134-L140);
  [node-localstorage 3.0.5 `LocalStorage.js`](https://unpkg.com/node-localstorage@3.0.5/LocalStorage.js)
  `setItem`). The chat history is the file
  `JetBrains-globalState/cody-local-chatHistory-v2`, quota 256 MB.
- `<data>/symf/`: same binary and index as above.
- `<config>/user-settings.json`: CLI accounts
  ([`agent/src/cli/command-auth/settings.ts:6-36`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/cli/command-auth/settings.ts#L6-L36)).
- `~/.cody/commands.json`: custom commands for agent clients
  ([`types.ts:13-14`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/types.ts#L13-L14);
  [`custom-commands.ts:46-47`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/services/custom-commands.ts#L46-L47)).

**JetBrains IDE settings (source review of 2026-10-19).** The plugin
also persists application-level components in the IDE's `options/`
directory (`~/.config/JetBrains/<product>`,
`~/Library/Application Support/JetBrains/<product>`,
`%APPDATA%\JetBrains\<product>`, per
[Directories used by the IDE to store settings, caches, plugins and logs](https://www.jetbrains.com/help/idea/directories-used-by-the-ide-to-store-settings-caches-plugins-and-logs.html)),
none of which the catalog collects:

- `cody.xml`: `GlobalCodySettings.jsonConfig`, a global `cody.*`
  settings document
  ([`jetbrains/.../config/GlobalCodySettings.kt:10-24`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/config/GlobalCodySettings.kt#L10-L24)).
  The plugin passes the agent the per-project file
  `<project>/.idea/.sourcegraph/cody_settings.json`, or
  `~/.sourcegraph/cody_settings.json` when the project has no base path,
  with this document as the fallback
  ([`ConfigUtil.kt:152-162`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/config/ConfigUtil.kt#L152-L162),
  [`184-199`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/config/ConfigUtil.kt#L184-L199)),
  so a JetBrains user's `cody.agentic.context.experimentalOptions` and
  `cody.mcpServers` are in one of those three; neither
  `~/.sourcegraph/` nor `.idea/.sourcegraph/` is a catalog line (the
  project table's `.sourcegraph` names the project root's directory).
- `cody_application_settings.xml`: feature toggles, `anonymousUserId`
  and `shouldAcceptNonTrustedCertificatesAutomatically`
  ([`CodyApplicationSettings.kt:9-25`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/config/CodyApplicationSettings.kt#L9-L25)).
- `cody_accounts_settings.xml`: the pre-agent account list
  ([`auth/deprecated/DeprecatedCodyAccountManager.kt:44-47`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/auth/deprecated/DeprecatedCodyAccountManager.kt#L44-L47)).

The project-level files are in [section 5](#5-project-local-files).

**Scratch directories.** None. Deep Cody's terminal tool and the agentic
chat's `run_terminal_command` both run in the first workspace folder
([`vscode/src/commands/context/shell.ts:37`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/context/shell.ts#L37);
[`vscode/src/chat/chat-view/tools/shell.ts:52-69`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/shell.ts#L52-L69)),
and no clone, worktree or per-chat directory is created outside the
internal `cody bench` evaluation command, whose `cody-bench-` worktree
sits in the system temp directory
([`agent/src/cli/command-bench/testTypecheck.ts:49-55`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/cli/command-bench/testTypecheck.ts#L49-L55)).
The `symf/indexroot/<path>` directories are indexes named after real
workspaces, not working directories.

## 3. Credentials

- VS Code: the access token is stored in SecretStorage three times, under
  the endpoint URL, under `cody.access-token`, and the token source under
  `<endpoint>cody.access-token.source`
  ([`vscode/src/services/SecretStorageProvider.ts:5-6`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/SecretStorageProvider.ts#L5-L6),
  [`97-112`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/SecretStorageProvider.ts#L97-L112)).
  These are encrypted `secret://{"extensionId":"sourcegraph.cody-ai","key":...}`
  rows in `state.vscdb`
  ([PearAI `mainThreadSecretState.ts:76-78`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/workbench/api/browser/mainThreadSecretState.ts#L76-L78)).
- `cody.experimental.localTokenPath`: a setting that points at a JSON file
  with a `token` key, read instead of SecretStorage
  ([`SecretStorageProvider.ts:48-57`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/SecretStorageProvider.ts#L48-L57),
  [`225-235`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/SecretStorageProvider.ts#L225-L235)).
  Its location is arbitrary; read `settings.json` for it.
- JetBrains: secrets are client-managed
  ([`CodyAgentService.kt:204`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/agent/CodyAgentService.kt#L204)),
  that is, in the IDE's own password store, not in `Cody-nodejs`.
- CLI: the OS keychain via `security`, Windows Credential Manager or
  `secret-tool`, no file fallback
  ([`agent/src/cli/command-auth/secrets.ts:8-14`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/cli/command-auth/secrets.ts#L8-L14),
  [`204-213`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/cli/command-auth/secrets.ts#L204-L213)).
  `user-settings.json` holds `serverEndpoint`, `username` and
  `customHeaders`, which may carry proxy auth.
- `cody.mcpServers.<server>` entries (VS Code `settings.json`, the
  JetBrains `cody_settings.json` files and `cody.xml`) take `headers`
  for an SSE (server-sent events, the HTTP transport) server and `env` for a stdio one, where MCP (Model Context Protocol) servers usually
  receive their tokens
  ([`vscode/src/chat/chat-view/tools/MCPManager.ts:31-43`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/MCPManager.ts#L31-L43));
  source review of 2026-10-19.

## 4. Exclusions

- The `symf-*` binary in each `symf/` directory.
- `<config>/dist`: copied extension resources.
- `symf/indexroot` index content was not sized; its directory names are
  the indexed workspace paths, which is evidence, so it is not proposed for
  exclusion until a live collection shows it is large.

## 5. Project-local files

`.vscode/cody.json` (VS Code) and `.cody/commands.json` (agent clients)
at the first workspace folder ([`custom-commands.ts:36-39`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/services/custom-commands.ts#L36-L39));
`.sourcegraph/*.rule.md` rules
([`vscode/src/rules/fs-rule-provider.ts:20-26`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/rules/fs-rule-provider.ts#L20-L26)).
No per-project database.

JetBrains project files (source review of 2026-10-19), neither in the
project table:

- `.idea/cody_history.xml`: the plugin's pre-agent chat history, a
  project-level component (`HistoryService`), with every chat's
  messages, `updatedAt` and model
  ([`jetbrains/.../history/HistoryService.kt:13-15`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/history/HistoryService.kt#L13-L15)).
  The run-once migration copies it into the agent store and leaves it in
  place
  ([`ChatHistoryMigration.kt:17-28`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/config/migration/ChatHistoryMigration.kt#L17-L28)),
  so it is the copy a chat deleted in the plugin still has. The `.idea/`
  location is the IntelliJ Platform's rule for project-level
  components, not re-read from platform source here. Its schema is in
  [section 2 of `analyzer/research/cody.md`](../../analyzer/research/cody.md#2-transcript-files).
- `.idea/.sourcegraph/cody_settings.json`: the per-project `cody.*`
  settings, permission settings and MCP servers included
  ([section 2](#2-per-user-storage)).

## 6. Where the project path is recorded

- Chat transcripts carry no workspace field; context items carry file URIs
  (`contextFiles[].uri`), from which the project can be inferred.
- `symf/indexroot/<path>` directory names are indexed workspace roots.
- VS Code `workspaceStorage/*/workspace.json` as usual.
- A JetBrains `.idea/cody_history.xml` or `.idea/.sourcegraph/` names its
  project by where it sits; nothing inside records the path.

## 7. Confidence

High (frozen source): storage keys and row layout, symf paths, custom
command files, agent `Cody-nodejs` layout, JetBrains global-state
directory, CLI keychain use. Medium: that current shipped builds still
use these keys and paths; the source stops in August 2025. Medium: the
`*/Cody-nodejs/...` exclusion and secret forms assume exclusion globs match
under `AppData/Local` and `Library/Preferences` the same way. Not
determined: the size of a symf index; whether the JetBrains plugin passes a
`globalStateDir` from the Kotlin side in builds after the snapshot (it does
not at this commit); where the Eclipse and Visual Studio clients, which are
not in this repository, keep state.
