# n8n

n8n is a workflow automation server with AI Agent nodes, plus `@n8n/computer-use`, a local
tool gateway for the n8n Assistant. Its agent surfaces are Instance AI (the n8n Assistant,
the built-in agent of the `instance-ai` module, which can drive the computer-use gateway) and
Chat Hub (n8n's chat front end to models and agent workflows). This document came out of the
agent framework sweep for [issue #64](https://github.com/seanthegeek/doubleagent/issues/64);
see [`collectors/research/frameworks.md`](frameworks.md) for the frameworks that got no
catalog line. There is no analyzer document yet.

## 1. Source and evidence

[n8n-io/n8n](https://github.com/n8n-io/n8n), commit
[`0e1c7549997f43053fda83534b597875b0310df6`](https://github.com/n8n-io/n8n/commit/0e1c7549997f43053fda83534b597875b0310df6).
Licence:
Sustainable Use License, with `.ee.` files under the enterprise licence
([LICENSE.md:1-14](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/LICENSE.md#L1-L14)).
All claims are from source unless marked inferred.

n8n executes tools and shell commands on the host:

- The Execute Command node runs `spawn(command, {shell: true})`
  ([ExecuteCommand.node.ts:48](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/nodes-base/nodes/ExecuteCommand/ExecuteCommand.node.ts#L48)).
  It is excluded by default through `NODES_EXCLUDE`
  ([nodes.config.ts:32-39](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/config/src/configs/nodes.config.ts#L32-L39)).
- The Code node runs through task runners in `internal` mode by default,
  which means child processes on the host
  ([runners.config.ts:16-17](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/config/src/configs/runners.config.ts#L16-L17)).
- computer-use exposes `shell_execute`, file and input tools to the agent;
  shell is denied by default
  ([computer-use README.md:21](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/computer-use/README.md#L21)).

### Observed

- No real install: nothing was installed or run.

### Source reviews

- **Source review (2026-10-19)**: HEAD
  [`9675910`](https://github.com/n8n-io/n8n/commit/967591041e508802f6cf77a1b1651ec48175f680)
  reviewed against the previously cited
  [`0e1c754`](https://github.com/n8n-io/n8n/commit/0e1c7549997f43053fda83534b597875b0310df6),
  from source only. Two surfaces matter here, Instance AI and Chat Hub. Both store in
  `database.sqlite`; detail in [Database and gateway detail](#database-and-gateway-detail).
  - Permission state: found. Per-call: Instance AI's
    `instance_ai_pending_confirmations` and its `confirmation-request`
    events, and the gateway log's denial errors. Standing:
    `instance_ai_thread_grants` ("always allow" within a thread) and
    `.n8n-gateway/settings.json` (`permissions` per tool group and
    `resourcePermissionsByOrigin` allow and deny lists).
  - Model: found: `chat_hub_messages.provider` and `model` per message,
    the same on `chat_hub_sessions`; Instance AI's model is instance
    configuration (`N8N_INSTANCE_AI_MODEL`).
  - Past use beyond the primary store: found: `instance_ai_events` is a
    sequenced event log of every Instance AI run; the gateway's `log`
    repeats each tool call with its arguments; `execution_entity` and
    `execution_data` keep the workflow runs a chat message started.
  - Sync: found: Instance AI's `run-start` events carry `langsmithRunId`
    and `langsmithTraceId` when the run is traced to LangSmith (LangChain's
    hosted tracing service) through n8n's AI proxy.
  - Scratch directories: none created by n8n; the gateway's working
    directory is the one the user picks ([Scratch directories](#scratch-directories)).
  - Deletion: found: deleting an Instance AI thread cascades to its
    messages, events, checkpoints, grants and pending confirmations, and
    one upgrade migration emptied the Instance AI tables; deleting a Chat
    Hub session leaves the workflow executions its messages point to.
  - Version drift: paths unchanged; the SQLite file name moved to
    [database.config.ts:127](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/config/src/configs/database.config.ts#L127);
    computer-use is unchanged apart from its `package.json`. Instance AI's
    tables existed at [`0e1c754`](https://github.com/n8n-io/n8n/commit/0e1c7549997f43053fda83534b597875b0310df6) and were not in this document.
  - Bad lines: `.n8n-local-gateway/log` and `.n8n/n8nEventLog*.log` are
    line-oriented; a parser must report a cut line.

## 2. Per-user storage

The n8n folder is `N8N_USER_FOLDER`, otherwise `HOME` (or `USERPROFILE`
on Windows), with `.n8n` appended: `~/.n8n` on every OS
([config/src/utils/utils.ts:7-11](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/config/src/utils/utils.ts#L7-L11)).

| Path | Holds | Default or opt-in |
| --- | --- | --- |
| `.n8n/database.sqlite` | tables `execution_entity`, `execution_data` (run data), `credentials_entity` (encrypted), `workflow_entity`, `chat_hub_sessions`, `chat_hub_messages` ([database.config.ts:123-125](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/config/src/configs/database.config.ts#L123-L125), [db-connection-options.ts:82](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/db/src/connection/db-connection-options.ts#L82), [SeparateExecutionData.ts:8](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/db/src/migrations/sqlite/1690000000010-SeparateExecutionData.ts#L8), [chat-hub-message.entity.ts:15](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/cli/src/modules/chat-hub/chat-hub-message.entity.ts#L15), [chat-hub-session.entity.ts:35](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/cli/src/modules/chat-hub/chat-hub-session.entity.ts#L35)) | default |
| `.n8n/config` | JSON holding `encryptionKey` ([instance-settings.ts:60](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/core/src/instance-settings/instance-settings.ts#L60), [355-357](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/core/src/instance-settings/instance-settings.ts#L355-L357)) | default |
| `.n8n/storage` (legacy `.n8n/binaryData`) | binary data from executions ([storage.config.ts:37](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/core/src/storage.config.ts#L37), [74-85](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/core/src/storage.config.ts#L74-L85)) | default |
| `.n8n/n8nEventLog*.log`, `.n8n/crash.journal` | audit event log, crash journal ([event-bus.config.ts:17](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/config/src/configs/event-bus.config.ts#L17), [log-writer.ts:87-92](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/cli/src/eventbus/message-event-bus-writer/message-event-bus-log-writer.ts#L87-L92), [crash-journal.ts:21](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/cli/src/crash-journal.ts#L21)) | default |
| `.n8n/nodes`, `.n8n/custom`, `.n8n/node-definitions`, `.n8n/n8n-sdk-templates` | community and custom nodes, generated definitions, template cache ([instance-settings.ts:52-58](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/core/src/instance-settings/instance-settings.ts#L52-L58), [instance-ai.adapter.service.ts:937](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/cli/src/modules/instance-ai/instance-ai.adapter.service.ts#L937)) | default |
| `.n8n/git`, `.n8n/ssh/key` | source-control checkout and SSH private key ([constants.ts:2](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/cli/src/modules/source-control.ee/constants.ts#L2), [29-30](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/cli/src/modules/source-control.ee/constants.ts#L29-L30)) | opt-in (enterprise source control) |
| `.cache/n8n/public` | static UI assets ([instance-settings.ts:49](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/core/src/instance-settings/instance-settings.ts#L49)) | default; noise, not collected |
| `.n8n-local-gateway/log` | computer-use log: every tool call with full arguments (`{tool, args}`), including `shell_execute` ([computer-use logger.ts:75-76](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/computer-use/src/logger.ts#L75-L76), [91-97](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/computer-use/src/logger.ts#L91-L97), [323-327](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/computer-use/src/logger.ts#L323-L327)) | default for computer-use users |
| `.n8n-gateway/settings.json` | computer-use permissions and resource grants ([config.ts:257-259](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/computer-use/src/config.ts#L257-L259), [settings-store.ts:104-117](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/computer-use/src/settings-store.ts#L104-L117)) | default for computer-use users |
| `Library/Application Support/n8n Gateway`, `AppData/Roaming/n8n Gateway` | tray app `settings.json`; inferred from Electron `userData` and `productName: 'n8n Gateway'`, macOS and Windows builds only ([local-gateway settings-store.ts:83](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/local-gateway/src/main/settings-store.ts#L83), [electron-builder.config.js:4](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/packages/@n8n/local-gateway/electron-builder.config.js#L4)) | inferred; no catalog line |

### Scratch directories

None. The gateway works in the directory set by
its configuration, the saved `filesystemDir`, or the directory it was
started from, in that order
([settings-store.ts:135](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/settings-store.ts#L135)):
a directory the user chose, not one the agent made.

### Docker

The named volume `n8n_data` is mounted at `/home/node/.n8n`
([README.md:29-30](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/README.md#L29-L30),
[docker/images/n8n/README.md:73](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/docker/images/n8n/README.md#L73)).
The `get-n8n.sh` installer uses `n8n-data`
([get-n8n-compose.yml:11-13](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/docker/get-n8n-compose.yml#L11-L13),
[88-89](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/docker/get-n8n-compose.yml#L88-L89))
with the project directory `./n8n`
([get-n8n.sh:23](https://github.com/n8n-io/n8n/blob/0e1c7549997f43053fda83534b597875b0310df6/docker/get-n8n.sh#L23)),
which gives the volume `n8n_n8n-data`. Both volumes hold the `.n8n`
layout at their root, so the `DOCKER_VOLUMES` lines are `*n8n_data` and
`*n8n-data`, with volume-relative exclusions and secret globs.

### Database and gateway detail

Detail from the 2026-10-19 review, at
[`9675910`](https://github.com/n8n-io/n8n/commit/967591041e508802f6cf77a1b1651ec48175f680),
for a future analyzer document:

- **Gateway permissions** (`.n8n-gateway/settings.json`). `permissions`
  maps each tool group (`filesystemRead`, `filesystemWrite`, `shell`,
  `computer`, `browser`; defaults `allow`, `ask`, `deny`, `deny`, `ask`)
  to a mode, `deny`, `ask` or `allow`
  ([config.ts:8-50](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/config.ts#L8-L50)).
  `resourcePermissionsByOrigin` holds, per connecting n8n instance and
  tool group, `allow` and `deny` lists of resources, and the older
  `resourcePermissions` the same without an origin; `filesystemDir` is
  the directory the user let the gateway work in
  ([settings-store.ts:25-61](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/settings-store.ts#L25-L61)).
  A prompt's answer is one of `allowOnce`, `allowForSession`,
  `alwaysAllow`, `denyOnce`, `alwaysDeny`; only the two `always` answers
  are written to the file
  ([tools/types.ts:55-60](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/tools/types.ts#L55-L60),
  [gateway-session.ts:7-12](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/gateway-session.ts#L7-L12)).
- **Gateway log** (`.n8n-local-gateway/log`). One line per message,
  `[<ISO time>] [<LEVEL>] <message> <meta JSON>`
  ([logger.ts:91-97](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/logger.ts#L91-L97)).
  A tool call logs `{tool, args}`, its end `{tool, durationMs}` or, on
  failure, `{tool, durationMs, error}`
  ([logger.ts:323-340](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/logger.ts#L323-L340)).
  A denied resource fails the call with `User denied access to <group>:
  <resource>` or `User permanently denied access to ...`, so denials
  reach the log as errors while approvals leave no line of their own
  ([gateway-client.ts:510-545](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/computer-use/src/gateway-client.ts#L510-L545)).
- **Instance AI tables.** `instance_ai_threads` (`title`, `projectId`,
  `metadata`), `instance_ai_messages` (`threadId`, `role`, `type`,
  `content`), `instance_ai_events` (`threadId`, `seq`, `runId`, `type`,
  `payload`), `instance_ai_checkpoints`, `instance_ai_thread_grants`
  (`threadId`, `userId`, `grantKey` such as `executions:run`) and
  `instance_ai_pending_confirmations` (`requestId`, `threadId`, `kind`
  `suspended` or `inline`, `runId`, `toolCallId`, `expiresAt`)
  ([instance-ai-thread.entity.ts:4-26](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/entities/instance-ai-thread.entity.ts#L4-L26),
  [instance-ai-message.entity.ts:4-24](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/entities/instance-ai-message.entity.ts#L4-L24),
  [instance-ai-event-log-entry.entity.ts:17-41](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/entities/instance-ai-event-log-entry.entity.ts#L17-L41),
  [instance-ai-thread-grant.entity.ts:7-39](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/entities/instance-ai-thread-grant.entity.ts#L7-L39),
  [instance-ai-pending-confirmation.entity.ts:7-70](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/entities/instance-ai-pending-confirmation.entity.ts#L7-L70)).
  Event types include `run-start`, `tool-call`, `tool-result`,
  `tool-error`, `confirmation-request`, `filesystem-request` and `error`
  ([instance-ai.schema.ts:224-247](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/api-types/src/schemas/instance-ai.schema.ts#L224-L247));
  an approval resumes the tool with `approved`, optional `userInput` and
  `scope` `once` or `session`
  ([instance-ai.schema.ts:284-296](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/api-types/src/schemas/instance-ai.schema.ts#L284-L296)).
  The model is `N8N_INSTANCE_AI_MODEL`, `anthropic/claude-opus-4-8` by
  default, from the environment, not the database
  ([instance-ai.config.ts:12-14](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/config/src/configs/instance-ai.config.ts#L12-L14)).
- **LangSmith ids.** `run-start` events keep `langsmithRunId` and
  `langsmithTraceId`, "so user feedback can annotate the trace after a
  restart", when the run was traced through the proxy's `/langsmith`
  endpoint
  ([instance-ai.schema.ts:413-430](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/api-types/src/schemas/instance-ai.schema.ts#L413-L430),
  [instance-ai.service.ts:1033-1039](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/instance-ai.service.ts#L1033-L1039),
  [4024-4041](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/instance-ai.service.ts#L4024-L4041)).
- **Chat Hub model.** `chat_hub_messages` has `provider` and `model` per
  message, and `executionId`, `previousMessageId`, `retryOfMessageId` and
  `revisionOfMessageId`; `chat_hub_sessions` has the session's `provider`
  and `model`
  ([chat-hub-message.entity.ts:55-114](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/chat-hub/chat-hub-message.entity.ts#L55-L114),
  [chat-hub-session.entity.ts:81-90](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/chat-hub/chat-hub-session.entity.ts#L81-L90)).
- **Deletion.** Deleting an Instance AI thread deletes it and its
  sub-agent threads, and the message, event, checkpoint, grant and
  pending confirmation rows go with it by `ON DELETE CASCADE`
  ([instance-ai-memory.service.ts:648-653](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/instance-ai-memory.service.ts#L648-L653),
  [typeorm-agent-memory.ts:388-390](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/storage/typeorm-agent-memory.ts#L388-L390),
  [CreateInstanceAiTables.ts:24-39](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/db/src/migrations/common/1775000000000-CreateInstanceAiTables.ts#L24-L39),
  [instance-ai-event-log-entry.entity.ts:20](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/instance-ai/entities/instance-ai-event-log-entry.entity.ts#L20)).
  One upgrade migration emptied the Instance AI checkpoint, message,
  resource and thread tables outright
  ([ResetInstanceAiNativePersistence.ts:3-19](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/@n8n/db/src/migrations/common/1784000000008-ResetInstanceAiNativePersistence.ts#L3-L19)),
  so an install upgraded past it holds no Instance AI thread from before
  the upgrade in those tables.
  Deleting a Chat Hub session deletes its attachments and the session
  ([chat-hub.service.ts:394-400](https://github.com/n8n-io/n8n/blob/967591041e508802f6cf77a1b1651ec48175f680/packages/cli/src/modules/chat-hub/chat-hub.service.ts#L394-L400));
  the workflow executions its messages started stay in
  `execution_entity`. The gateway log is never trimmed by n8n (not found
  in `logger.ts` at [`9675910`](https://github.com/n8n-io/n8n/commit/967591041e508802f6cf77a1b1651ec48175f680): grepped for `truncate` and `unlink`).

## 3. Credentials

- `.n8n/config` (`encryptionKey`) and `.n8n/ssh/*`: flagged, and in a
  volume the volume-relative `config` and `ssh/*`. The bare `config` glob
  matches only a file named `config` at the root of a collection base; the
  one other layout that has one is the retired Letta V1 server's
  `~/.letta/config` at the root of a `*letta*` volume
  ([`collectors/research/letta.md`](letta.md)), which is then also flagged. That is an accepted
  overmatch: flagging only adds `secret: true` and the `--no-secrets`
  skip.
- `database.sqlite` holds encrypted credentials and the history together,
  so it is collected unflagged; with `config` the `credentials_entity`
  rows can be decrypted.

## 4. Exclusions

`.n8n/nodes/node_modules`, `.n8n/custom/node_modules`,
`.n8n/node-definitions`, `.n8n/n8n-sdk-templates`, and the volume-relative
`nodes/node_modules`, `node-definitions` and `n8n-sdk-templates`.

## 5. Project-local files

None. Workflows are rows in the database.

## 6. Where the project path is recorded

Nowhere; n8n has no project concept on disk.

## 7. Confidence

High, apart from the Electron tray paths, which are inferred and have no
catalog line. Not determined: the tray app's Linux build (none is
configured).
