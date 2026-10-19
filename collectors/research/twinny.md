# Twinny: on-disk paths

## 1. Source and evidence level

[twinnydotdev/twinny](https://github.com/twinnydotdev/twinny) at [`9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6`](https://github.com/twinnydotdev/twinny/commit/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6),
version 4.3.5, MIT ([package.json:32](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/package.json#L32)). Open source,
TypeScript. All claims from source. How VS Code stores an extension's
`globalState` was checked against [microsoft/vscode](https://github.com/microsoft/vscode) at the commit used by
[vscode.md](vscode.md). The repository holds three programs: the VS Code
extension, the `twinny-node` peer-to-peer GPU sharing CLI
([package.json:61-63](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/package.json#L61-L63)) and the `twinny-server` team
gateway ([packages/twinny-server/package.json:28-30](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/packages/twinny-server/package.json#L28-L30)).
Record schema: [`analyzer/research/twinny.md`](../../analyzer/research/twinny.md).

- **Source review (2026-10-19)**: [twinnydotdev/twinny](https://github.com/twinnydotdev/twinny) at
  [`0337b26`](https://github.com/twinnydotdev/twinny/commit/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a)
  (version 4.3.15, today's HEAD), against
  [`9339bd1`](https://github.com/twinnydotdev/twinny/commit/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6)
  (4.3.5), which the citations below name unless they say otherwise;
  VS Code paths from [microsoft/vscode](https://github.com/microsoft/vscode) at
  [`4d22f4f`](https://github.com/microsoft/vscode/commit/4d22f4f922eb012217ac65672ccce02f59d63706).
  Permission state: found, standing grants in `globalState` and settings
  ([section 2](#2-per-user-storage)). Model: already covered (per reply,
  in the conversation). Past use: found, a new `agent-changes/` directory
  of per-reply file copies in the workspace's extension storage and the
  Twinny log channel ([section 2](#2-per-user-storage)). Sync, relay and
  origin: already covered, none (the analyzer document checked it at
  this commit). Scratch directories: none
  ([section 2](#2-per-user-storage)). Deletion: a conversation delete
  touches only `globalState`, leaving `agent-changes/` and the log.
  Version drift: found, new credential and account keys for the ChatGPT
  plan sign-in ([section 3](#3-credentials)) and the change records
  above; every path in this document is still used at HEAD. Bad lines:
  not applicable to the collector.

## 2. Per-user storage

Extension id `rjmacarthy.twinny` (publisher `rjmacarthy`, name `twinny`,
[package.json:2](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/package.json#L2), [33](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/package.json#L33);
[src/protocol/types.ts:118](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/protocol/types.ts#L118)). The editor's
`User/globalStorage/rjmacarthy.twinny/` directory is already collected under
`vscode`; what Twinny actually keeps is split three ways.

**VS Code `globalState`, not files.** Chat history, the provider list and the
active providers are `context.globalState` keys
([src/common/constants/storage.ts:1-21](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/storage.ts#L1-L21)):
`twinny.conversations` (every conversation, keyed by id),
`twinny.active-conversation`, `twinny.inference-providers`,
`twinny.active-chat-provider`, `-fim-provider`, `-embeddings-provider`,
P2P device and trusted-peer lists, team share state
([src/extension/chat/conversation-history.ts:80-104](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/conversation-history.ts#L80-L104);
[src/extension/providers/store.ts:47-64](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/providers/store.ts#L47-L64)).
VS Code persists an extension's global state as one JSON string in the
profile `state.vscdb` `ItemTable`, keyed by the extension id
([extHostMemento.ts:118](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/api/common/extHostMemento.ts#L118);
[extensionStorage.ts:159-176](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/extensionManagement/common/extensionStorage.ts#L159-L176)).
So Twinny's chats live in `User/globalStorage/state.vscdb`, row
`key = 'rjmacarthy.twinny'`, which the `vscode` entry collects. Per-workspace
UI state (`chatMessage` draft, `contextItems`, `selection`,
`embeddingsUpdatedAt`, [storage.ts:35-47](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/storage.ts#L35-L47); [src/extension/webview/base.ts:301-322](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/webview/base.ts#L301-L322))
goes to `workspaceStorage/<id>/state.vscdb` under the same key.

**`globalStorage/rjmacarthy.twinny/`** holds only:

- `twinny-providers.json`, the provider list including `apiKey`, written only
  when the setting `twinny.providerStorageLocation` is `file` (default
  `globalState`) ([store.ts:37-41](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/providers/store.ts#L37-L41), [141-171](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/providers/store.ts#L141-L171);
  [src/common/constants/misc.ts:29](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/misc.ts#L29);
  [package.json:699-708](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/package.json#L699-L708)).
- `p2p-host.lock` and `team-share.lock`, `{pid, since}` window locks
  ([src/extension/p2p/host.ts:40](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/p2p/host.ts#L40), [83-88](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/p2p/host.ts#L83-L88);
  [src/extension/team/share.ts:28](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/team/share.ts#L28), [86-90](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/team/share.ts#L86-L90);
  [src/extension/utils/window-lock.ts:26-52](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/utils/window-lock.ts#L26-L52)).

No chat, embedding or symmetry data is written there, except
`agent-changes/` when no folder is open (below).

**Since 4.3.5, at
[`0337b26`](https://github.com/twinnydotdev/twinny/commit/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a):**

- `workspaceStorage/<id>/rjmacarthy.twinny/agent-changes/<uuid>.json`, one
  record per agent-mode reply that changed files: the absolute workspace
  root, each changed file's relative path and status, and the whole text
  of each file (up to 1 MiB) as it was before the reply, the newest 50
  kept ([src/extension/chat/index.ts:210-221](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L210-L221);
  [src/extension/chat/reply-changes.ts:25-47](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L25-L47),
  [211-259](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L211-L259)). With no
  folder open it goes to `globalStorage/rjmacarthy.twinny/agent-changes/`
  instead (VS Code's workspace storage is then undefined,
  [extHostStoragePaths.ts:82-91](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/api/common/extHostStoragePaths.ts#L82-L91)).
  The workspace copy is collected only inside the editor's `User`
  directory, attributed to the editor (`vscode` or the fork); no
  `twinny` catalog line names `workspaceStorage`.
- Standing permission grants, as keys of the extension's `globalState`
  value (the `rjmacarthy.twinny` row of `globalStorage/state.vscdb`),
  each prefixed `twinny-global-context-`: `alwaysRunCommands`,
  `alwaysRunMcpTools`, `autoRunCommands`, `agentMode`, and the current
  `twinny.selectedModel`
  ([src/common/constants/storage.ts:25-35](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/constants/storage.ts#L25-L35);
  [src/extension/chat/index.ts:162-192](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L162-L192),
  [466-491](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L466-L491)); the editor
  settings `twinny.chatTools`, `twinny.chatToolsCommands`,
  `twinny.chatToolsEdits` and `twinny.chatToolsMcpServers` in the
  user `settings.json`
  ([package.json:645-720](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/package.json#L645-L720)). Both files are
  collected as agent `vscode`.
- The ChatGPT plan sign-in's profile, `twinny.chatgpt-plan.profile`
  (`clientId`, `subject`, `email`, `name` of the signed-in OpenAI
  account) and `twinny.chatgpt-plan.host-id`, also in the `globalState`
  value ([src/extension/chatgpt-plan/session.ts:11-13](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chatgpt-plan/session.ts#L11-L13),
  [52-57](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chatgpt-plan/session.ts#L52-L57),
  [397-402](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chatgpt-plan/session.ts#L397-L402)).
- The **Twinny** log channel, `<editor logs>/<session>/window<n>/exthost/rjmacarthy.twinny/Twinny.log`
  ([src/common/logger.ts:93-97](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/logger.ts#L93-L97);
  [extHostOutput.ts:148-150](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/api/common/extHostOutput.ts#L148-L150)),
  one line per chat request naming the model, and the prompts and
  replies at Debug level; collected as agent `vscode` under the editor's
  `logs` entries.

**Scratch directories.** Twinny has none. Agent mode works in the first
workspace folder only
([src/extension/chat/index.ts:494-497](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L494-L497)),
and its one temporary file, a copy of the repository's index named
`twinny-index-<uuid>` in the system temporary directory, is deleted as
soon as the tree is snapshotted
([src/extension/chat/command-snapshot.ts:62-80](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/command-snapshot.ts#L62-L80));
nothing for the catalog to collect or for discovery to drop.

**`~/.twinny`** from `os.homedir()` on every OS (no platform branching):

- `templates/*.hbs`: editable prompt templates, defaults copied in on first
  run ([src/index.ts:186](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/index.ts#L186);
  [src/extension/templates/provider.ts:18](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/templates/provider.ts#L18), [68-80](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/templates/provider.ts#L68-L80), [157](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/templates/provider.ts#L157)).
- `embeddings/<workspace name>/`: a LanceDB table `chunks` plus
  `manifest.json` per workspace; the name is `vscode.workspace.name` with
  characters outside `[A-Za-z0-9_.-]` replaced by `_`
  ([src/extension/embeddings/index.ts:85-91](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/embeddings/index.ts#L85-L91);
  [database.ts:9-11](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/embeddings/database.ts#L9-L11), [102-104](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/embeddings/database.ts#L102-L104);
  [src/extension/utils.ts:369-376](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/utils.ts#L369-L376)).
- `node/identity.json` (P2P key seed, mode 0600) and
  `node/trusted-peers.json`, written by `twinny-node`
  ([src/node/config.ts:1-24](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/node/config.ts#L1-L24), [51-55](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/node/config.ts#L51-L55)).
- `server/`, the `twinny-server` data directory
  ([src/gateway/config.ts:209-222](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/config.ts#L209-L222)): `format.json`,
  `keys.json`, `license`, `invites.json`, `plugins.json`, `usage/`,
  `recordings/`, `audit/`, `plugins/` ([src/gateway/data-format.ts:18-21](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/data-format.ts#L18-L21)).
  `usage/YYYY-MM-DD.jsonl` per-request records
  ([usage.ts:41](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/usage.ts#L41), [83](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/usage.ts#L83)); `audit/YYYY-MM.jsonl` admin actions
  ([audit.ts:3](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/audit.ts#L3), [101-102](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/audit.ts#L101-L102); [serve.ts:354](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/serve.ts#L354));
  `recordings/recordings.sqlite` or `recordings/jsonl/YYYY-MM-DD.jsonl`,
  full prompts and replies, off by default
  ([src/gateway/recording/store.ts:1-11](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/recording/store.ts#L1-L11), [553-556](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/recording/store.ts#L553-L556);
  [config.ts:216-222](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/config.ts#L216-L222)); `plugins/<id>/` plugin state
  ([plugins/host.ts:492-494](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/plugins/host.ts#L492-L494)). The server's own
  configuration is `twinny.gateway.json` in the directory it was started
  from ([src/gateway/init.ts:19](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/init.ts#L19), [150](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/init.ts#L150)).

Layout is the same on Linux, macOS and Windows; only the editor's
`User` directory moves (see [vscode.md](vscode.md)). No environment overrides
for `~/.twinny` in the extension; the server's paths can be changed in its
config (`auth.keysFile`, `auth.licenseFile`, `usage.dir`, `recording.dir`,
[config.ts:312-330](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/config.ts#L312-L330)).

## 3. Credentials

- Provider API keys: `apiKey` on each provider
  ([src/common/types.ts:255-272](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L255-L272)), in `state.vscdb`
  (`rjmacarthy.twinny` → `twinny.inference-providers`) or in
  `globalStorage/rjmacarthy.twinny/twinny-providers.json`. Plain text.
- Team gateway tokens: VS Code secret storage, `twinny.gateway-token.<providerId>`
  ([src/extension/providers/credentials.ts:14](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/providers/credentials.ts#L14), [59-61](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/providers/credentials.ts#L59-L61));
  P2P identity and host seeds also secret storage
  ([storage.ts:11-13](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/storage.ts#L11-L13); [src/extension/p2p/runtime.ts:261-265](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/p2p/runtime.ts#L261-L265);
  [host.ts:336-340](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/p2p/host.ts#L336-L340)). These are encrypted `secret://` rows in
  `state.vscdb` (see [vscode.md](vscode.md)).
- `twinny.githubToken` setting, a GitHub PAT, in the editor `settings.json`
  ([package.json:693-698](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/package.json#L693-L698)).
- `~/.twinny/node/identity.json`: the `twinny-node` key seed.
- ChatGPT plan sign-in (new since 4.3.5): access, refresh and id tokens
  in VS Code secret storage under `twinny.chatgpt-plan.credentials`, an
  encrypted `secret://` row; the account's email and subject in plain
  `globalState`
  ([src/extension/chatgpt-plan/session.ts:11-13](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chatgpt-plan/session.ts#L11-L13),
  [59-66](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chatgpt-plan/session.ts#L59-L66),
  [484](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chatgpt-plan/session.ts#L484)).
- `twinny.chatToolsMcpServers` in the user `settings.json` can carry
  tokens in each server's `env` (the setting's own example is a
  `GITHUB_TOKEN`, [package.json:684-720](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/package.json#L684-L720)).
- Exported provider lists: the "Export providers" command writes the
  providers, `apiKey` included, to a file the user picks, named
  `twinny-providers.json` by default
  ([src/extension/providers/manager.ts:690-704](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/providers/manager.ts#L690-L704));
  only the copy in `globalStorage/rjmacarthy.twinny/` is in a known
  place.
- `twinny-server`: `license` (a licence token), `keys.json` (SHA-256 of
  client keys, not the keys, [src/gateway/keys.ts:4-7](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/keys.ts#L4-L7)),
  `plugins/<id>/settings.json` with git clone tokens for the context plugin
  ([src/gateway/plugins/context.ts:59-60](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/plugins/context.ts#L59-L60), [214](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/plugins/context.ts#L214), [236-241](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/plugins/context.ts#L236-L241)).
  Backend API keys are read from environment variables named in the config
  (`apiKeyEnv`, [config.ts:58](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/config.ts#L58), [237](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/config.ts#L237)).

## 4. Exclusions

- `~/.twinny/embeddings/*/chunks.lance`: the LanceDB vector table of source
  chunks; size grows with the indexed workspace. Keep `manifest.json`.
- `~/.twinny/server/plugins/*/repos/*/checkout` (shallow git clones) and
  `.../index` (`manifest.json`, `chunks.json`, `vectors.bin`)
  ([context.ts:271-273](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/plugins/context.ts#L271-L273), [290-295](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/plugins/context.ts#L290-L295), [336-338](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/plugins/context.ts#L336-L338)).

## 5. Project-local files

None written. Twinny reads each workspace's `.gitignore` to filter files
([src/extension/embeddings/indexer.ts:85-94](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/embeddings/indexer.ts#L85-L94)) and has no rules or
instructions file of its own.

## 6. Where the project path is recorded

- `~/.twinny/embeddings/<workspace>/manifest.json`: `files` is keyed by the
  absolute path of every indexed file ([database.ts:45-51](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/embeddings/database.ts#L45-L51);
  [indexer.ts:123-133](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/embeddings/indexer.ts#L123-L133), [313](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/embeddings/indexer.ts#L313)). The workspace
  root is a common prefix of those keys, not a field.
- `workspaceStorage/<id>/rjmacarthy.twinny/agent-changes/*.json` (since
  4.3.5): key `root`, the absolute workspace root agent mode worked in
  ([src/extension/chat/reply-changes.ts:42-47](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L42-L47),
  [161](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L161)); a grep-able
  `"root":"<path>"` in one-line JSON.
- Conversations carry no workspace path. The workspace link is the
  `workspaceStorage/<id>/workspace.json` that holds Twinny's per-workspace
  state.

## 7. Confidence

High: extension id, `globalState` keys, the provider file name and
setting, `~/.twinny` subpaths, gateway data directory layout, secret storage
keys (all source). High: `globalState` stored in `state.vscdb` under the
extension id (VS Code source). Medium: `chunks.lance` as the on-disk name of
the LanceDB table (LanceDB's naming convention, not visible in Twinny's
source). Not determined: sizes of a real index; whether `invites.json`
holds reusable secrets; how the JetBrains or other editors (Twinny is VS
Code only at this commit) would differ.
