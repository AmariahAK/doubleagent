# Continue: on-disk paths

## 1. Source and evidence level

Open source. [continuedev/continue](https://github.com/continuedev/continue) at [`5522c6f44ca0ac3528b37244818fbfa39b5af470`](https://github.com/continuedev/continue/commit/5522c6f44ca0ac3528b37244818fbfa39b5af470)
(clone `scratchpad/repos/continue`). All claims from source. Covers the VS Code
extension `continue.continue`, the JetBrains plugin (same core via
`binary/`) and the `cn` CLI (`extensions/cli`). Record schemas:
[`analyzer/research/continue.md`](../../analyzer/research/continue.md).

- **Source review (2026-10-19)**: reviewed
  [continuedev/continue](https://github.com/continuedev/continue) at
  [`5522c6f`](https://github.com/continuedev/continue/commit/5522c6f44ca0ac3528b37244818fbfa39b5af470), the commit this document already cited: the default
  branch `main` has not moved since 2026-07-20, and its README says the
  repository "is no longer actively maintained and is read-only for all
  users" after a final 2.0.0 release of the VS Code extension, the CLI
  and the JetBrains plugin ([`README.md:19`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/README.md#L19), [`README.md:27-29`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/README.md#L27-L29)).
  Whether development continues anywhere else cannot be told from the
  clone. Per requirement class: permission state, found (the CLI's
  `permissions.yaml` shape and its "don't ask again" writer; the
  extension's tool policies live in the editor's webview storage,
  [section 2](#2-per-user-storage)); model, found (the selected models
  in `index/globalContext.json`); past use, found (`input_history.json`,
  the CLI's prompt history, collected with `.continue`); sync, relay and
  origin, already covered in
  [section 8 of `analyzer/research/continue.md`](../../analyzer/research/continue.md#8-parser-plan);
  scratch directories, found (`cn review` worktrees in the system temp
  directory, [section 6](#6-project-path)); deletion, found (in the
  analyzer document); version drift, none (same commit); bad lines, in
  the analyzer document.

## 2. Per-user storage

One global dir on every OS, `~/.continue`, from `os.homedir()`; env
`CONTINUE_GLOBAL_DIR` relocates it (relative values resolve against cwd)
([`core/util/paths.ts:27-35`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L27-L35); [`extensions/cli/src/env.ts:10-11`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/env.ts#L10-L11)). No XDG,
Library or AppData paths.

Under `~/.continue`:

- `sessions/<sessionId>.json`, `sessions/sessions.json` ([`paths.ts:78-112`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L78-L112);
  [`core/util/history.ts:112-120`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L112-L120)); the CLI writes the same dir
  ([`extensions/cli/src/session.ts:50-67`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/session.ts#L50-L67)).
- `config.yaml`, `config.json`, `config.ts`, `tsconfig.json`,
  `package.json`, `types/core/index.d.ts`, `out/config.js`
  ([`paths.ts:114-177`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L114-L177)), `.continuerc.json` ([`paths.ts:210-225`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L210-L225)),
  `.continueignore` ([`paths.ts:58-67`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L58-L67)), `sharedConfig.json` ([`paths.ts:98-100`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L98-L100)),
  `.env` ([`paths.ts:377-378`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L377-L378)), `.local`/`.staging` environment markers
  ([`paths.ts:462-468`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L462-L468)).
- `.configs/<hostname>/config.json`, `config.js` for remote configs
  ([`paths.ts:342-375`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L342-L375)).
- `index/index.sqlite`, `index/lancedb/`, `index/autocompleteCache.sqlite`,
  `index/docs.sqlite`, `index/globalContext.json` ([`paths.ts:86-95`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L86-L95),[`326-340`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L326-L340)).
- `dev_data/devdata.sqlite`, `dev_data/<schema>/<event>.jsonl` with events
  `chatInteraction`, `chatFeedback`, `toolUsage`, `tokensGenerated`,
  `autocomplete`, `editInteraction`, `quickEdit`, `editOutcome`,
  `nextEditOutcome` ([`paths.ts:228-249`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L228-L249);
  [`packages/config-yaml/src/schemas/data/index.ts`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/data/index.ts)); legacy `dev_data/*.jsonl`
  ([`paths.ts:440-461`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L440-L461)).
- `logs/core.log`, `logs/prompt.log` ([`paths.ts:385-399`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L385-L399)); CLI logs in
  `logs/` too ([`extensions/cli/src/util/logger.ts:17`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/logger.ts#L17)).
- `.utils/.chromium-browser-snapshots`, `.utils/esbuild`, `.utils/repo_map.txt`
  ([`paths.ts:46-56`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L46-L56),[`433-438`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L433-L438)), `.diffs/` ([`paths.ts:470-477`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L470-L477)),
  `.migrations/<id>` markers ([`paths.ts:293-310`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L293-L310)), `node_modules/`.
- Blocks folders shared by IDE and CLI: `rules/`, `prompts/`, `agents/`,
  `mcpServers/`, `skills/`, plus any `<name>/` read by
  `getGlobalFolderWithName` ([`paths.ts:401-406`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L401-L406);
  [`core/config/loadLocalAssistants.ts:108-121`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/loadLocalAssistants.ts#L108-L121);
  [`core/context/mcp/json/loadJsonMcpConfigs.ts:43`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/context/mcp/json/loadJsonMcpConfigs.ts#L43);
  [`extensions/cli/src/util/loadMarkdownSkills.ts:98`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/loadMarkdownSkills.ts#L98);
  [`extensions/cli/src/systemMessage.ts:93`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/systemMessage.ts#L93)).
- CLI only: `auth.json`, `input_history.json`, `permissions.yaml`,
  `.onboarding_complete` ([`extensions/cli/src/auth/authEnv.ts:5`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/auth/authEnv.ts#L5);
  [`util/inputHistory.ts:6`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/inputHistory.ts#L6); [`permissions/permissionsYamlLoader.ts:12`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/permissions/permissionsYamlLoader.ts#L12);
  [`onboarding.ts:108`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/onboarding.ts#L108)).
- `permissions.yaml` (CLI) holds standing tool grants: three optional
  lists, `allow`, `ask` and `exclude`, of tool patterns written `Tool`
  or `Tool(<argument pattern>)` such as `Bash(npm*)`, and no other key
  ([`permissionsYamlLoader.ts:15-19`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/permissions/permissionsYamlLoader.ts#L15-L19),
  [`77-117`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/permissions/permissionsYamlLoader.ts#L77-L117)).
  `cn` creates it with three empty lists
  ([`permissionsYamlLoader.ts:152-179`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/permissions/permissionsYamlLoader.ts#L152-L179))
  and appends a rule to `allow` when the user answers a tool prompt
  with "Continue + don't ask again": `Bash(<first word of the
  command>*)` for a shell command, the tool name otherwise
  ([`policyWriter.ts:18-76`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/permissions/policyWriter.ts#L18-L76);
  [`extensions/cli/src/ui/components/ToolPermissionSelector.tsx:37-55`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/ui/components/ToolPermissionSelector.tsx#L37-L55);
  [`extensions/cli/src/ui/hooks/useChat.ts:789-823`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/ui/hooks/useChat.ts#L789-L823)).
  It holds no secret.
- `input_history.json` (CLI) is the TUI's prompt history: a JSON array
  of `{text, timestamp}` (epoch milliseconds), newest first, at most
  1000 entries, a repeated prompt moved to the front instead of added
  twice; every prompt and slash command typed in the TUI goes in
  ([`util/inputHistory.ts:6-12`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/inputHistory.ts#L6-L12),
  [`53-72`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/inputHistory.ts#L53-L72);
  [`extensions/cli/src/ui/UserInput.tsx:477`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/ui/UserInput.tsx#L477),
  [`585`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/ui/UserInput.tsx#L585)).
- `index/globalContext.json` also holds the selected models,
  `selectedModelsByProfileId.<profile id>.<role>` for the extension and
  `cliSelectedModel` for the CLI, and `lastSelectedProfileForWorkspace`
  keyed by workspace
  ([`core/util/GlobalContext.ts:18-33`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/GlobalContext.ts#L18-L33);
  [`extensions/cli/src/util/modelPersistence.ts:7-19`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/modelPersistence.ts#L7-L19)).

VS Code `globalStorage/continue.continue/`: `<key>.bin` AES-GCM blobs
written by the extension's own secret store, key material in VS Code
`context.secrets` ([`extensions/vscode/src/stubs/SecretStorage.ts:7-23`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/vscode/src/stubs/SecretStorage.ts#L7-L23),[`41-58`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/vscode/src/stubs/SecretStorage.ts#L41-L58),[`100`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/vscode/src/stubs/SecretStorage.ts#L100)).

The extension's tool policies are not under `~/.continue`. Its webview
keeps `toolSettings` (tool name to `allowedWithPermission`, the default,
`allowedWithoutPermission` or `disabled`), `toolGroupSettings` (`include`
or `exclude`), `ruleSettings` and `reasoningSettings` with redux-persist
(a library that saves the webview's state store) in the webview's
`localStorage`, under the key `persist:root`, one JSON string per slice
([`gui/src/redux/store.ts:36-60`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/gui/src/redux/store.ts#L36-L60), [`92-99`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/gui/src/redux/store.ts#L92-L99);
[`gui/src/redux/slices/uiSlice.ts:27-34`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/gui/src/redux/slices/uiSlice.ts#L27-L34);
[`gui/src/util/migrateLocalStorage.ts:32-36`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/gui/src/util/migrateLocalStorage.ts#L32-L36)).
Where VS Code or a JetBrains IDE keeps a webview's local storage on disk
is outside this source and not determined; the catalog's
`globalStorage/continue.continue` lines do not cover it.

## 3. Credentials

- `~/.continue/auth.json` (CLI): `userId`, `userEmail`, `accessToken`,
  `refreshToken`, `expiresAt`, `organizationId`
  ([`extensions/cli/src/auth/workos.ts:28-40`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/auth/workos.ts#L28-L40)).
- `config.yaml` / `config.json` / `config.ts` / `.configs/*/config.js*` embed
  provider `apiKey` values; `.env` holds the `${{ secrets.X }}` inputs
  ([`paths.ts:377-383`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L377-L383)).
- `index/globalContext.json` key `mcpOauthStorage[server].tokens` and
  `clientInformation` ([`core/util/GlobalContext.ts:50-53`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/GlobalContext.ts#L50-L53)); it shares the
  `index/` dir with the embedding store.
- `mcpServers/*.yaml|json` can embed headers and env.
- VS Code: hub session token in `globalStorage/continue.continue/*.bin`,
  decryptable only with the key in the editor's `state.vscdb`.
- No OS keychain use by the core.

## 4. Exclude

`.continue/index/lancedb`, `.continue/index/*.sqlite`, `.continue/.utils`,
`.continue/node_modules`, `.continue/out`, `.continue/types`,
`.continue/.diffs`, `.continue/.migrations`, `.continue/dev_data/devdata.sqlite`.
Keep `dev_data/**/*.jsonl` (prompts, tool usage), `logs/prompt.log`,
`index/globalContext.json`.

## 5. Project-local

`.continue/<subdir>/*.yaml|md` for `rules`, `prompts`, `agents`,
`mcpServers`, `skills`, `models`, `context`, `docs`, `data`
([`loadLocalAssistants.ts:22-23`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/loadLocalAssistants.ts#L22-L23),[`112-115`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/loadLocalAssistants.ts#L112-L115); [`extensions/vscode/src/activation/activate.ts:42`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/vscode/src/activation/activate.ts#L42);
[`createNewAssistantFile.ts:55`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/createNewAssistantFile.ts#L55); [`promptFiles/index.ts:4`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/promptFiles/index.ts#L4);
[`tools/definitions/createRuleBlock.ts:65`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/tools/definitions/createRuleBlock.ts#L65)); `.continuerc.json`
([`core/config/json/loadRcConfigs.ts:18`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/json/loadRcConfigs.ts#L18); [`loadLocalAssistants.ts:18`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/loadLocalAssistants.ts#L18));
`.continueignore` ([`core/core.ts:1287`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/core.ts#L1287)). No per-project database.

## 6. Project path

`sessions/sessions.json[].workspaceDirectory` and
`sessions/<id>.json.workspaceDirectory` ([`history.ts:105-120`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L105-L120),[`160-172`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L160-L172)).
Empty string for sessions created without a workspace.

Scratch directories. `cn review` makes one detached git worktree per
review agent at `<system temp directory>/cn-review-<epoch ms>-<n>`, runs
a headless agent in it in the `auto` permission mode, and removes it in
a `finally` block with `git worktree remove --force`
([`extensions/cli/src/commands/review/worktree.ts:15-20`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/commands/review/worktree.ts#L15-L20),
[`99-115`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/commands/review/worktree.ts#L99-L115);
[`extensions/cli/src/commands/review/reviewWorker.ts:116-129`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/commands/review/reviewWorker.ts#L116-L129);
[`extensions/cli/src/commands/review.ts:341`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/commands/review.ts#L341),
[`389-392`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/commands/review.ts#L389-L392)).
The worker changes into the worktree before it starts its services or
adds the first message, and a CLI session takes `process.cwd()` as its
`workspaceDirectory` when it is created
([`extensions/cli/src/session.ts:92-106`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/session.ts#L92-L106)), so the review session's
file and `sessions.json` entry name the temp path, and
`discover_projects` lists it as a project. The system temp directory is
outside the home on Linux and macOS and is `AppData/Local/Temp` on
Windows; no catalog line collects it, and the worktree is normally gone
before collection. Nothing in the path or the session marks it as the
agent's own; the basename `cn-review-<digits>-<digits>` is the only
sign. The extension has no scratch directory: a terminal command with no
workspace runs in the home directory
([`core/tools/implementations/runTerminalCommand.ts:81-87`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/tools/implementations/runTerminalCommand.ts#L81-L87)).

## 7. Confidence

High: every `~/.continue` path, `auth.json` fields, `workspaceDirectory`,
`.bin` secret blobs. Medium: list of project `.continue/<subdir>` names (the
loader accepts any subdir passed by callers). Not determined: whether the
JetBrains plugin writes anything outside `~/.continue` (its `binary/` uses
the same [`core/util/paths.ts`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts)).
