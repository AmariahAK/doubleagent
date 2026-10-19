# roo-code

Roo Code (catalog agent `roo-code`) is an open-source coding agent shipped as a VS Code extension
and a CLI (`roo`). It is a fork of Cline and keeps Cline's legacy task layout, so the record shapes
in [`cline.md`](cline.md) apply with the differences listed here; PearAI bundles an older fork of
it ([`pearai.md`](pearai.md)). The analyzer parses its tasks and CLI history, from source and
fixtures only.

## 1. Source and evidence

Open source. [RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code) at
[`b867ec9145750d0ae1ff7f02d35406e9bf2a0b16`](https://github.com/RooCodeInc/Roo-Code/commit/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16),
Apache-2.0 (clone `scratchpad/repos/roo`). All claims from source. It applies to the VS Code
extension, id `RooVeterinaryInc.roo-cline`
([`src/package.json:2`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L2),[`5`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L5)),
and the CLI, which is `apps/cli` on top of `packages/vscode-shim`. Paths cited are relative to the
clone.

### Observed

No real install.

### Source reviews

- **Source review (2026-10-19)**: [RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code) HEAD
  is still
  [`b867ec9`](https://github.com/RooCodeInc/Roo-Code/commit/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16)
  (2026-05-15, "Remove roocode.com web app"), the commit this document cites, so no path has moved
  and nothing has drifted. Roo Code is a fork of Cline's legacy task layout; its drift from
  [`cline.md`](cline.md) is listed in [section 8](#8-record-schema). One line per requirement class:
  - Paths: found the CLI's `--ephemeral` storage under the system temp directory and a fuller key
    list for `~/.roo/cli-settings.json` ([section 2](#2-per-user-storage)). No new credential
    file, exclusion or catalog line is needed.
  - Permission state: found, not read by the parser. Per call, an approved
    tool ask is marked `isAnswered` in `ui_messages.json` and a denial is a
    JSON `tool_result` in the API history; standing grants are the
    `alwaysAllow*`, `allowedCommands` and `deniedCommands` settings, MCP
    `alwaysAllow` lists, and the CLI's `requireApproval`.
    See [section 8](#8-record-schema) and [section 13](#13-parser-plan).
  - Model: already covered (no model per task). Found besides: the CLI's
    default `model` in `~/.roo/cli-settings.json`, and the provider
    profile named by `apiConfigName`, whose current model id is in the
    secret store.
  - Past use beyond the primary store: already covered
    (`~/.roo/cli-history.json`). Nothing else found.
  - Sync, relay and origin: already covered, none.
  - Scratch directories: found. The suggested worktree root
    `~/.roo/worktrees/` is under the catalog entry `.roo`; the CLI's
    `--ephemeral` storage is under the system temp directory and removed
    on exit ([section 7](#7-transcript-stores)).
  - Deletion: found ([section 13](#13-parser-plan);
    [What survives a delete](#what-survives-a-delete)).
  - Version drift: none; HEAD is the cited commit.
  - Bad lines: already covered; every file the parser reads is a JSON
    document or array.

## Collection

### 2. Per-user storage

The layouts differ by surface: the VS Code extension, the CLI's VS Code shim, and the
shared `~/.roo`.

#### Scratch directories

The worktree dialog's suggested root, `~/.roo/worktrees/<project>-<suffix>`
([`src/core/webview/worktree/handlers.ts:224-236`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/worktree/handlers.ts#L224-L236)),
is the only directory Roo Code chooses for itself as a working directory. It is under the catalog
line `roo-code|.roo` and in `EXCLUDES` (`.roo/worktrees`), so its contents are not collected and the
analyzer classes it as a scratch directory by its catalog rule.

#### VS Code extension

VS Code extension, globalStorage `rooveterinaryinc.roo-cline/` (same layout on every OS; root is
redirectable by the setting `roo-cline.customStoragePath`,
[`src/utils/storage.ts:14-48`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/utils/storage.ts#L14-L48),
[`src/package.json:334`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L334)):

- `tasks/<taskId>/api_conversation_history.json`, `ui_messages.json`, `task_metadata.json`,
  `history_item.json`; `tasks/_index.json`
  ([`src/shared/globalFileNames.ts:1-9`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/shared/globalFileNames.ts#L1-L9);
  [`src/core/task-persistence/TaskHistoryStore.ts:24-25`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/TaskHistoryStore.ts#L24-L25),[`561-570`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/TaskHistoryStore.ts#L561-L570)).
- `tasks/<taskId>/checkpoints/.git` shadow repo per task, or
  `checkpoints/<sha256[:8] of workspace>/` per workspace
  ([`src/services/checkpoints/ShadowCheckpointService.ts:125`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/checkpoints/ShadowCheckpointService.ts#L125),[`432-447`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/checkpoints/ShadowCheckpointService.ts#L432-L447);
  [`RepoPerTaskCheckpointService.ts:10`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/checkpoints/RepoPerTaskCheckpointService.ts#L10)).
- `settings/mcp_settings.json`, `settings/custom_modes.yaml`
  ([`src/utils/storage.ts:63-68`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/utils/storage.ts#L63-L68);
  [`src/services/mcp/McpHub.ts:494`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/mcp/McpHub.ts#L494);
  [`src/core/config/CustomModesManager.ts:251`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/config/CustomModesManager.ts#L251);
  the old name `cline_mcp_settings.json` is migrated,
  [`src/utils/migrateSettings.ts:26`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/utils/migrateSettings.ts#L26)).
- `cache/<provider>_models.json`
  ([`src/api/providers/fetchers/modelCache.ts:39-46`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/api/providers/fetchers/modelCache.ts#L39-L46)).
- `roo-index-cache-<sha256>.json` per workspace, codebase-index file hashes
  ([`src/services/code-index/cache-manager.ts:24-26`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/code-index/cache-manager.ts#L24-L26)).
  Vectors go to Qdrant, not disk.

#### CLI

CLI (`roo`), `~/.vscode-mock/` from `$HOME` or `%USERPROFILE%`
([`packages/vscode-shim/src/utils/paths.ts:8-16`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L8-L16),[`65-82`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L65-L82)):

- `global-storage/`: same `tasks/` tree as above, plus `global-state.json`, `configuration.json`,
  `secrets.json`
  ([`packages/vscode-shim/src/context/ExtensionContext.ts:102-111`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/context/ExtensionContext.ts#L102-L111);
  [`api/WorkspaceConfiguration.ts:87-88`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/api/WorkspaceConfiguration.ts#L87-L88);
  [`storage/SecretStorage.ts:47`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/storage/SecretStorage.ts#L47)).
- `workspace-storage/<hash>/workspace-state.json`, `configuration.json`; hash is a 32-bit string
  hash of the workspace path, not reversible
  ([`paths.ts:24-32`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L24-L32),[`72-75`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L72-L75)).
- `logs/`
  ([`paths.ts:80-82`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L80-L82)).

#### `~/.roo`

`~/.roo/`
([`src/services/roo-config/index.ts:26-28`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/roo-config/index.ts#L26-L28);
[`apps/cli/src/lib/storage/config-dir.ts:5`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/config-dir.ts#L5)):
`rules/`, `rules-<mode>/`
([`src/core/webview/webviewMessageHandler.ts:1908`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/webviewMessageHandler.ts#L1908)),
`commands/`
([`src/services/command/commands.ts:137`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/command/commands.ts#L137)),
`skills/`
([`src/services/skills/SkillsManager.ts:608`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/skills/SkillsManager.ts#L608)),
`worktrees/<project>-<suffix>`
([`src/core/webview/worktree/handlers.ts:229-230`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/worktree/handlers.ts#L229-L230)),
`cli-history.json`
([`apps/cli/src/lib/storage/history.ts:21`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L21),
entries are raw prompts), `cli-settings.json`
([`settings.ts:9`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/settings.ts#L9);
`onboardingProviderChoice`, `mode`, `provider`, `model`, `reasoningEffort`,
`consecutiveMistakeLimit`, `requireApproval`, the older `dangerouslySkipPermissions` and `oneshot`,
[`apps/cli/src/types/types.ts:55-73`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/types/types.ts#L55-L73);
`requireApproval` is permission state, see [Permission rows](#permission-rows)). `~/.agents/skills`
is also read
([`roo-config/index.ts:53-55`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/roo-config/index.ts#L53-L55);
[`SkillsManager.ts:594`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/skills/SkillsManager.ts#L594)).

#### Global MCP servers

Global MCP server install dir is platform-branched: Windows `AppData/Roaming/Roo-Code/MCP`, macOS
`Documents/Cline/MCP` (sic), Linux `.local/share/Roo-Code/MCP`, fallback `~/.roo-code/mcp`
([`src/core/webview/ClineProvider.ts:1547-1562`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/ClineProvider.ts#L1547-L1562)).
It holds cloned server code, not evidence of use. No XDG use elsewhere; no environment variable
relocates storage.

#### CLI ephemeral storage

`roo --ephemeral` keeps the whole CLI storage, tasks included, in
`<system temp directory>/roo-cli-<epoch ms>-<random>` and removes it on exit
([`apps/cli/src/lib/storage/ephemeral.ts:5-10`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/ephemeral.ts#L5-L10),
[`apps/cli/src/agent/extension-host.ts:598-601`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/agent/extension-host.ts#L598-L601)).
It is outside every home, so the collector cannot reach it with a catalog line; a responder who
finds a killed `roo --ephemeral` process collects the temp directory by hand.

### 3. Credentials

- Extension: provider profiles with API keys are stored in VS Code `context.secrets` under
  `roo_cline_config_api_config`
  ([`src/core/config/ProviderSettingsManager.ts:45`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/config/ProviderSettingsManager.ts#L45),[`657`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/config/ProviderSettingsManager.ts#L657));
  Codex OAuth credentials likewise
  ([`src/integrations/openai-codex/oauth.ts:451`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/integrations/openai-codex/oauth.ts#L451)).
  Those land in the editor's `state.vscdb`, collected by the vscode entries.
- CLI: the same keys serialised to `~/.vscode-mock/global-storage/secrets.json` (mode 0600,
  [`packages/vscode-shim/src/storage/SecretStorage.ts:10-47`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/storage/SecretStorage.ts#L10-L47)).
- `settings/mcp_settings.json` and project `.roo/mcp.json` can embed `env`
  and headers. No keychain use.

### 4. Exclusions

`*/rooveterinaryinc.roo-cline/tasks/*/checkpoints`,
`*/rooveterinaryinc.roo-cline/checkpoints`, `*/rooveterinaryinc.roo-cline/cache`,
`.vscode-mock/global-storage/tasks/*/checkpoints`,
`.vscode-mock/global-storage/checkpoints`, `.roo/worktrees`,
`.local/share/Roo-Code/MCP`, `AppData/Roaming/Roo-Code/MCP`, `.roo-code/mcp`.

### 5. Project-local files

`.roo/rules/`, `.roo/rules-<mode>/`, `.roo/commands/`, `.roo/mcp.json`, `.roo/skills/`
([`roo-config/index.ts:68-80`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/roo-config/index.ts#L68-L80);
[`webviewMessageHandler.ts:1901`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/webviewMessageHandler.ts#L1901);
[`commands.ts:141`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/command/commands.ts#L141);
[`McpHub.ts:379`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/mcp/McpHub.ts#L379);
[`SkillsManager.ts:379`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/skills/SkillsManager.ts#L379));
`.roomodes`, `.roorules*`, `.rooignore`, `.rooprotected`, legacy `.clinerules*`
([`src/core/protect/RooProtectedController.ts:17-23`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/protect/RooProtectedController.ts#L17-L23);
[`src/core/ignore/RooIgnoreController.ts:41`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/ignore/RooIgnoreController.ts#L41);
[`src/core/prompts/sections/custom-instructions.ts:229`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/prompts/sections/custom-instructions.ts#L229));
`.agents/skills`; `AGENTS.md`. No per-project database.

### 6. Where the project path is recorded

`tasks/_index.json[].workspace` and `tasks/<id>/history_item.json.workspace`
([`src/core/task-persistence/taskMetadata.ts:22`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/taskMetadata.ts#L22),[`37`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/taskMetadata.ts#L37),[`111`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/taskMetadata.ts#L111);
[`TaskHistoryStore.ts:146-149`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/TaskHistoryStore.ts#L146-L149)),
in both globalStorage and `~/.vscode-mock/global-storage`. `checkpoints/<hash>` is a truncated
sha256 and not reversible. A task run in a worktree records the worktree's path as its `workspace`,
so `~/.roo/worktrees/<project>-<suffix>` paths appear there.

## Parsing

### 7. Transcript stores

VS Code: `globalStorage/rooveterinaryinc.roo-cline/tasks/<taskId>/` with
`api_conversation_history.json`, `ui_messages.json`, `task_metadata.json`, `history_item.json`;
index `tasks/_index.json`
([`src/shared/globalFileNames.ts:1-9`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/shared/globalFileNames.ts#L1-L9)).
The root can be redirected by the setting `roo-cline.customStoragePath`
([`src/utils/storage.ts:14-48`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/utils/storage.ts#L14-L48)).
CLI root: `~/.vscode-mock/global-storage/`
([`apps/cli/src/lib/task-history/index.ts:8`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/task-history/index.ts#L8);
[`packages/vscode-shim/src/utils/paths.ts:8`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L8),[`65-66`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L65-L66)),
plus `~/.vscode-mock/workspace-storage/<hash>/`, `logs/`, and `global-storage/secrets.json`
([`vscode-shim/src/storage/SecretStorage.ts:47`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/storage/SecretStorage.ts#L47)).
`~/.roo` holds CLI config and global rules only
([`apps/cli/src/lib/storage/config-dir.ts:5`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/config-dir.ts#L5)).
The legacy transcript name `claude_messages.json` is read and then deleted on upgrade
([`src/core/task-persistence/apiMessages.ts:73-91`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/apiMessages.ts#L73-L91)).

#### What survives a delete

Deleting a task removes it and, by default, its subtasks from `tasks/_index.json`, deletes their
shadow checkpoint repositories or branches, and removes each task directory
([`src/core/webview/ClineProvider.ts:1737-1814`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/ClineProvider.ts#L1737-L1814)).
The CLI's `~/.roo/cli-history.json` is not touched: it holds the newest 500 submitted lines with no
time, task id or workspace, and outlives a deleted task directory, a removed workspace and the
extension's task-history pruning, so it is what is left of a deleted CLI task. A `roo --ephemeral`
task is removed with its temporary directory when the CLI exits and survives only a CLI killed
before its cleanup ran. Other second copies, project-local traces and deletion markers are not
stated. The analyzer reads `cli-history.json` as a secondary source whose lines are kept only when
no task has the same text (see [Secondary sources](../analyzer/docs/output.md#secondary-sources)).

#### Transcripts in CLI ephemeral storage

`roo --ephemeral` ("Run without persisting state",
[`apps/cli/src/index.ts:53`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/index.ts#L53))
points the whole extension storage, tasks included, at a new
`<system temp directory>/roo-cli-<epoch ms>-<random>` directory
([`apps/cli/src/lib/storage/ephemeral.ts:5-10`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/ephemeral.ts#L5-L10),
[`apps/cli/src/agent/extension-host.ts:378-381`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/agent/extension-host.ts#L378-L381))
and removes it when the CLI exits
([`:598-601`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/agent/extension-host.ts#L598-L601)).
Such a task is outside the home, so no catalog line reaches it, and it survives only a CLI that was
killed before its cleanup ran.

### 8. Record schema

#### Task files

`api_conversation_history.json` is the Anthropic `MessageParam[]` shape as in Cline
([`apiMessages.ts:12`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/apiMessages.ts#L12)),
extended with `ts` (ms), `isSummary`, `id`, `type:"reasoning"`, `summary`, `encrypted_content`,
`reasoning_details`, `reasoning_content`, `condenseId`, `condenseParent`, `truncationId`,
`truncationParent`, `isTruncationMarker`
([`apiMessages.ts:13-37`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/apiMessages.ts#L13-L37)).
Tool calls are mostly XML inside text blocks.

`ui_messages.json`
([`packages/types/src/message.ts:249-274`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/message.ts#L249-L274)):
`ts, type, ask, say, text, images, partial, reasoning, conversationHistoryIndex, checkpoint{}, progressStatus, contextCondense{cost, prevContextTokens, newContextTokens, summary, condenseId}, contextTruncation, isProtected, apiProtocol, isAnswered`.
Asks
[`:27-40`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/message.ts#L27-L40);
says
[`:144-174`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/message.ts#L144-L174)
add `subtask_result`, `checkpoint_saved`, `condense_context`, `codebase_search_result`,
`api_req_retried`. `ClineSayTool`
([`packages/types/src/vscode-extension-host.ts:693-760`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/vscode-extension-host.ts#L693-L760))
adds `appliedDiff`, `codebaseSearch`, `newTask`, `switchMode`, `finishTask`, `batchFiles[]`;
`ClineApiReqInfo`
([`:780-790`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/vscode-extension-host.ts#L780-L790))
adds `apiProtocol`. No model name appears anywhere in Roo transcripts; `HistoryItem.apiConfigName`
is a profile name.

`HistoryItem`
([`packages/types/src/history.ts:7-29`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/history.ts#L7-L29)):
`id, rootTaskId?, parentTaskId?, number, ts, task, tokensIn, tokensOut, totalCost, size?, workspace?, mode?, apiConfigName?, status?, delegatedToId?, childIds?, ...`.
`_index.json` is `{version:1, updatedAt, entries: HistoryItem[]}`
([`TaskHistoryStore.ts:14-18`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/TaskHistoryStore.ts#L14-L18)).
`task_metadata.json` holds only `files_in_context`
([`src/core/context-tracking/FileContextTracker.ts:117-135`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/context-tracking/FileContextTracker.ts#L117-L135)).

Timestamps are millisecond epochs. No git branch is recorded.

#### Permission records

Source review of 2026-10-19. Every approval goes through `ask`: the `ask` record is written first,
then `checkAutoApproval` decides `approve`, `deny`, `timeout` or `ask` from the settings
([`src/core/task/Task.ts:1313-1334`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L1313-L1334)).
An approval of a `tool` ask, by the user or automatically, sets `isAnswered: true` on that ask
record
([`:1489-1502`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L1489-L1502),
[`packages/types/src/message.ts:273`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/message.ts#L273));
an automatic approval is not told apart from a click. A denial reaches the model as a `tool_result`
in `api_conversation_history.json` whose text is JSON:
`{"status":"denied","message":"The user denied this operation."}`,
`{"status":"denied","feedback":...}`, or for an approval with a typed note
`{"status":"approved","feedback":...}`
([`src/core/prompts/responses.ts:8-24`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/prompts/responses.ts#L8-L24)).
`HistoryItem.mode` is the task's mode slug (`code`, `architect`, `ask`, `debug` or a custom mode),
which decides the tool groups the task may use, and `apiConfigName` names the provider profile
([`packages/types/src/history.ts:21-22`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/history.ts#L21-L22)).

### 9. Joins and timestamps

Directory name = `HistoryItem.id`; workspace = `workspace` in
`history_item.json` or `_index.json`; `rootTaskId` and `parentTaskId` link
subtasks. `ClineMessage.conversationHistoryIndex` indexes into the API
history.

A `cli-history.json` entry joins a task on text only. The first prompt of a task becomes the task's
first `say: "text"` record with the same text
([`src/core/task/Task.ts:1908`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L1908)),
and a later message or follow-up answer becomes a `say: "user_feedback"` record
([`Task.ts:2027-2029`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L2027-L2029));
both are `user` rows of the task. The API history wraps the first prompt in `<user_message>` tags
([`Task.ts:1935`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L1935)),
so a task that has only `api_conversation_history.json` left does not match on text. The file
outlives a deleted task directory, a removed workspace and the extension's task-history pruning,
since nothing but the 500-entry cap removes an entry; it does not record which task or workspace a
line went to.

### 10. Other stores

No SQLite store. The VS Code side keeps secrets in SecretStorage (`state.vscdb`).

#### CLI input history

The CLI also keeps an input history, `~/.roo/cli-history.json`: the file name is joined to
`getConfigDir()`
([`apps/cli/src/lib/storage/history.ts:20-22`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L20-L22)),
which is `~/.roo` on every platform
([`apps/cli/src/lib/storage/config-dir.ts:5-9`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/config-dir.ts#L5-L9)).
The catalog line `roo-code|.roo` collects it. It is the history the interactive prompt steps through
with the arrow keys, not a transcript.

`cli-history.json` is `{version: 1, entries: string[]}`
([`history.ts:9-15`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L9-L15)),
written pretty-printed with tabs and trimmed to the newest `MAX_HISTORY_ENTRIES` (500) on every save
([`history.ts:6-7`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L6-L7),
[`64-77`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L64-L77)).
`addToHistory` appends the trimmed line, skipping an empty one and one equal to the last entry
([`history.ts:90-108`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L90-L108));
`loadHistory` keeps only non-blank strings
([`history.ts:44-45`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L44-L45)).
Entries are oldest first and carry no time, task id or workspace. The input box adds every submitted
line before acting on it
([`apps/cli/src/ui/components/autocomplete/AutocompleteInput.tsx:180-198`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/ui/components/autocomplete/AutocompleteInput.tsx#L180-L198);
[`apps/cli/src/ui/hooks/useInputHistory.ts:83-97`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/ui/hooks/useInputHistory.ts#L83-L97)),
so it holds the first prompt of a task, the answers to follow-up questions and later messages, and
CLI commands such as `/new` that the CLI handles itself and never sends to a task
([`apps/cli/src/ui/hooks/useTaskSubmit.ts:56-132`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/ui/hooks/useTaskSubmit.ts#L56-L132)).
A prompt given on the command line rather than typed into the input box does not pass through it.

### 11. Format versions

`claude_messages.json` became `api_conversation_history.json` (deleted on read); globalState
`taskHistory` became `history_item.json` plus `_index.json` with `version: 1`
([`TaskHistoryStore.ts:320-360`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/TaskHistoryStore.ts#L320-L360)).
`.roo-code` has no references in current source and is legacy only.

### 12. Secrets

CLI `~/.vscode-mock/global-storage/secrets.json` holds provider profiles
with API keys and should be a collector `SECRET_GLOBS` entry (tracked in
issue 23). Transcripts carry file contents and command output.

### 13. Parser plan

Globs:
`<GS>/rooveterinaryinc.roo-cline/tasks/*/{api_conversation_history,ui_messages,history_item}.json`,
`<GS>/rooveterinaryinc.roo-cline/tasks/_index.json`,
`.vscode-mock/global-storage/tasks/**` (same files),
`.roo/cli-history.json`.

Rows and columns follow the Cline legacy mapping, with `ApiMessage.ts`
available as a fallback timestamp, `condense_context` typed `system`,
`session_id` the directory name, `project_path` from `history_item.workspace`,
and `model` always empty.

#### Permission rows

Permission state (2026-10-19; the parser reads none of it yet):

- Per call: the `isAnswered` mark and the denial and approval JSON of
  [section 8](#8-record-schema). A `tool_result` whose JSON `status` is
  `denied` or `approved` can yield `permission decision: <status>`
  (with ` feedback` when the key is present) beside the `tool_result`
  row, joined on `tool_use_id`.
- Standing: the global settings `autoApprovalEnabled`, `alwaysAllowReadOnly`,
  `alwaysAllowReadOnlyOutsideWorkspace`, `alwaysAllowWrite`, `alwaysAllowWriteOutsideWorkspace`,
  `alwaysAllowWriteProtected`, `alwaysAllowMcp`, `alwaysAllowModeSwitch`, `alwaysAllowSubtasks`,
  `alwaysAllowExecute`, `alwaysAllowFollowupQuestions`, `allowedCommands`, `deniedCommands`,
  `commandTimeoutAllowlist`, `allowedMaxRequests` and `allowedMaxCost`
  ([`packages/types/src/global-settings.ts:97-118`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/global-settings.ts#L97-L118)),
  kept in the extension's global state: the `state.vscdb` row of the extension in VS Code, and
  `~/.vscode-mock/global-storage/global-state.json` for the CLI
  ([`packages/vscode-shim/src/context/ExtensionContext.ts:104`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/context/ExtensionContext.ts#L104)).
  `roo-cline.allowedCommands` and `roo-cline.deniedCommands` are also VS Code settings in the user's
  `settings.json`
  ([`src/package.json:280`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L280),
  [`292`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L292)).
  Each MCP server in `settings/mcp_settings.json` or a project's `.roo/mcp.json` has an
  `alwaysAllow` list of tool names
  ([`src/services/mcp/McpHub.ts:70`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/mcp/McpHub.ts#L70)).
  Writes to Roo Code's own configuration files (`.roo/**`, `.roomodes`, `.rooignore`, `.roorules*`,
  `.clinerules*`, `.vscode/**`, `*.code-workspace`, `AGENTS.md`, `AGENT.md`) are never
  auto-approved; the list is fixed in code, and `.rooprotected` is in it only as a name reserved
  "for future use", not a file Roo Code reads
  ([`src/core/protect/RooProtectedController.ts:7-25`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/protect/RooProtectedController.ts#L7-L25)).
  The CLI runs every tool without asking unless `--require-approval` (`-a`,
  [`apps/cli/src/index.ts:36`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/index.ts#L36))
  or `requireApproval: true` (or the older `dangerouslySkipPermissions: false`) in
  `~/.roo/cli-settings.json` says otherwise
  ([`apps/cli/src/commands/cli/run.ts:125-128`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/commands/cli/run.ts#L125-L128)).
  Each entry can be one `permission setting:` row at the file's modification time.
- Mode: `HistoryItem.mode` can be one `permission mode: <mode>` row per
  task.

#### Model rows

Roo Code records no model in any of these files (`apiConfigName` is a
profile name, not a model id), so the parser yields no `model:` rows.

Model, found besides (2026-10-19): the provider profiles are stored as one secret,
`roo_cline_config_api_config`,
`{currentApiConfigName, apiConfigs: {<name>: {id, apiProvider, <provider>ModelId or apiModelId, ...}}, modeApiConfigs}`
([`src/core/config/ProviderSettingsManager.ts:45-61`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/config/ProviderSettingsManager.ts#L45-L61)),
in the editor's `state.vscdb` or the CLI's `secrets.json`, so a task's `apiConfigName` names a
profile whose model id is known only as it is now, not as it was when the task ran. The CLI's
`~/.roo/cli-settings.json` holds the default `model`, `provider`, `mode` and `reasoningEffort`
([`apps/cli/src/types/types.ts:55-73`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/types/types.ts#L55-L73)).
Neither is a per-task record; the parser yields no model row from them.

#### Past-use rows and secondary sources

The task files are the primary store. `cli-history.json` ([CLI input history](#cli-input-history))
is a secondary source (issue 122): one `user` row per entry, with empty `timestamp_utc`,
`session_id` and `project_path` because the file records none, so the timeline's deduplication pairs
it with a task's `user` row of the same text and keeps it only when no task has the text (a prompt
whose task directory was deleted, or a CLI command such as `/new`).

#### Sync, relay and origin rows

Sync: Roo Code records no sync state. Cline's enterprise prompt upload and its manifest marker
([Sync, relay and origin in `cline.md`](cline.md#sync-relay-and-origin-rows)) live in Cline's later
SDK, which Roo Code never took: its tasks keep the forked legacy layout, and its `HistoryItem` has
no share, sync or remote field
([`packages/types/src/history.ts:7-29`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/history.ts#L7-L29)).
At this commit (extension version 3.53.0,
[`src/package.json:6`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L6))
neither the extension nor the CLI holds a client for Roo Code Cloud, the vendor's hosted service
that earlier releases used for task sync and share links: there is no cloud package under
`packages/`; `CloudService`, `@roo-code/cloud`, `shareTask`, `shareUrl`, `posthog` and
`TelemetryService` have no code match in `src/`, `packages/`, `apps/` or `webview-ui/`, and `cloud`
matches only provider names and the documentation site, which redirects its removed Cloud pages,
`task-sync` and `task-sharing` among them
([`apps/docs/docusaurus.config.ts:278-290`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/docs/docusaurus.config.ts#L278-L290)).
What is left is a `// Cloud Sync Tracking` comment above the task's initial status
([`src/core/task/Task.ts:407-409`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L407-L409)),
`shareTaskSuccess` in a comment listing unhandled webview message types
([`src/core/webview/webviewMessageHandler.ts:3221`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/webviewMessageHandler.ts#L3221)),
and a CLI client for the vendor's tRPC (a TypeScript remote procedure call library) API that defines
only `auth.me` and has no caller
([`apps/cli/src/lib/sdk/client.ts:11-30`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/sdk/client.ts#L11-L30)).
`PRIVACY.md` still describes PostHog (a product-analytics service) usage telemetry that excludes
code and prompts
([`PRIVACY.md:13`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/PRIVACY.md#L13)),
but no telemetry code is in the tree. The releases that shipped Roo Code Cloud (the changelog's
Cloud Team entries,
[`CHANGELOG.md:312`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/CHANGELOG.md#L312),
[`486`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/CHANGELOG.md#L486))
were not reviewed, so an install of one of them may hold sync state this document does not describe.

#### Scratch directory rows

Source review of 2026-10-19: the worktree dialog suggests `~/.roo/worktrees/<project>-<suffix>`
([`src/core/webview/worktree/handlers.ts:224-236`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/worktree/handlers.ts#L224-L236)),
under the catalog entry `.roo`, so a task run there has its `workspace` classed by the analyzer's
catalog rule; a user-chosen path elsewhere is a project. No default directory for a task without a
workspace was found (grepped `homedir`, `tmpdir` and `worktrees` in `src/` and `apps/cli/src`).

#### Deletion rows

Not stated: what a task delete removes and what survives it is in
[What survives a delete](#what-survives-a-delete).

#### Bad-line rows

The source review of 2026-10-19 found bad lines already covered: every file the parser reads is a
JSON document or array.

#### Fixtures

Fixture:

```json
{"_file":"tasks/_index.json","record":{"version":1,"updatedAt":1760000005000,"entries":[{"id":"8f1c2b7e-1","number":1,"ts":1760000000000,"task":"fix tests","tokensIn":1200,"tokensOut":80,"totalCost":0.0041,"workspace":"/home/u/proj","mode":"code","status":"completed"}]}}
{"_file":"api_conversation_history.json","record":{"role":"assistant","content":[{"type":"tool_use","id":"toolu_01A","name":"execute_command","input":{"command":"pytest -q"}}],"ts":1760000002000}}
{"_file":"api_conversation_history.json","record":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_01A","content":"3 passed","is_error":false}],"ts":1760000003000}}
```

## 14. Confidence

Collection. High: all globalStorage and `~/.vscode-mock` paths, `_index.json.workspace`, secrets
locations. Medium: `.roo/worktrees` is only the suggested default offered to the user
([`handlers.ts:230`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/webview/worktree/handlers.ts#L230)),
so it may be elsewhere. Not determined: where the CLI stores cloud (Roo account) tokens beyond
`secrets.json`; `@roo-code/cloud` is an external package not in this clone.

Parsing. High: file names, layouts and type definitions (read from
source). Not determined: the `checkpoint` object keys.
