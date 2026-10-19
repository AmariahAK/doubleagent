# gemini-cli

Gemini CLI (catalog agent `gemini-cli`) is Google's open-source command-line agent. It was
researched together with Qwen Code, which forked Gemini CLI; see [`qwen-code.md`](qwen-code.md)
for how far the fork has drifted. Zed's agent panel can also drive it
([Driven from Zed](#driven-from-zed)). Paths cited are relative to the repository clone. Paths,
credentials and the rest of the per-user state are in
[`collectors/research/gemini-cli.md`](../../collectors/research/gemini-cli.md).

## 1. Source and evidence

[google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) at [`fb972b2f87fe7d5b06d37eac711490162d98de2c`](https://github.com/google-gemini/gemini-cli/commit/fb972b2f87fe7d5b06d37eac711490162d98de2c)
(2026-10-02), version 0.64.0-nightly.20260929, Apache-2.0. Open source.

### Observed

- No real install.

### Source reviews

- **Source review (2026-10-19).** HEAD
  [`3be3d44`](https://github.com/google-gemini/gemini-cli/commit/3be3d4424b3c8a760d793ae1bea6cb5180adf27d)
  (2026-10-19, version 0.66.0-nightly.20261013) against the commit
  above, for the requirement classes of the October 2026 sweep. Every
  citation in this document still resolves at the old commit; the lines
  below cite HEAD.
  - Permission state: found. The per-call `status` is already read; the
    standing grants are not: the "Allow for all future sessions" policy
    file `policies/auto-saved.toml`, in the home and in each project,
    the approval-mode and tool-list settings in `settings.json`, and
    `trusted_hooks.json` and `acknowledgments/agents.json`. Shapes in
    [section 5](#5-other-stores), rows in [Permission state](#permission-state).
  - Model: already covered (one `model` per gemini message). A
    `/model set` switch is an `info` message `Model set to <name>`,
    which the parser already yields as a `system` row.
  - Past use: found. `shell_history`, the `/chat save` checkpoints, the
    tool checkpoints, the auto-memory directory and the optional
    activity log are not parsed; `logs.json` is. Detail in
    [section 5](#5-other-stores).
  - Sync, relay and origin: already covered; nothing changed at HEAD.
  - Scratch directories: found. `--worktree` sessions run in
    `<project>/.gemini/worktrees/<name>`, which no rule classes as
    scratch.
  - Deletion: found. Besides the delete command, every start deletes
    sessions older than 30 days by default, sessions it cannot read,
    and the whole tool-checkpoint directory.
  - Version drift: none that the parser depends on. Between the two
    commits `chatRecordingService.ts` changed only resume and
    exit-cleanup logic, `chatRecordingTypes.ts`, `storage.ts`,
    `projectRegistry.ts`, `logger.ts`, `trust.ts` and
    `sessionOperations.ts` did not change, and the policy engine
    changed only how it decides, not what it stores.
  - Bad lines: covered for the session file, `logs.json` and
    `trustedFolders.json`; the shared `trustedFolders.json` reader also
    accepts the trailing commas and byte-order mark Qwen Code allows
    (see [Permission state](#permission-state)). The sources proposed in
    [section 8](#8-parser-plan) need the same treatment when they are
    parsed.

## 2. Transcript stores

Base directory `~/.gemini` ([`packages/core/src/config/storage.ts:54-60`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L54-L60));
under the macOS `SANDBOX=sandbox-exec` sandbox it is `~/.cache/.gemini`
([storage.ts:97-101](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L97-L101)). The project identifier is now a slug, not a hash:
`~/.gemini/projects.json` maps `{ "projects": { "<abs path>": "<slug>" } }`
([storage.ts:289-299](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L289-L299); [`projectRegistry.ts:16-18`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/projectRegistry.ts#L16-L18),[`304-316`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/projectRegistry.ts#L304-L316),[`414-421`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/projectRegistry.ts#L414-L421); slug is the
lower-cased basename with non-alphanumeric runs replaced by `-`, suffixed
`-1`, `-2` on collision). Each slug directory carries a marker
`~/.gemini/tmp/<slug>/.project_root` whose content is the absolute project
path ([projectRegistry.ts:24](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/projectRegistry.ts#L24),[372-412](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/projectRegistry.ts#L372-L412)). Legacy `tmp/<sha256(projectRoot)>`
directories are copied to the slug directory on first run and left in place
([storage.ts:310-324](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L310-L324); [`storageMigration.ts:20-52`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storageMigration.ts#L20-L52); [`utils/paths.ts:318-320`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/paths.ts#L318-L320)),
so both may exist.

- Session: `~/.gemini/tmp/<slug>/chats/session-<YYYY-MM-DDTHH-MM>-<shortId8>.jsonl`,
  one file per session ([`services/chatRecordingService.ts:757-799`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L757-L799); prefix
  [`chatRecordingTypes.ts:12`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L12)). Collisions insert `-1-`, `-2-` before the
  short id ([795-797](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L795-L797)). Subagent sessions: `chats/<parentSessionId>/<sessionId>.jsonl`
  ([763-791](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L763-L791)).
- Legacy session: same name with `.json`, one JSON object
  (`ConversationRecord`) ([1566-1616](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L1566-L1616)); on resume it is re-emitted into a
  sibling `.jsonl` ([708-735](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L708-L735)).
- Prompt history: `~/.gemini/tmp/<slug>/logs.json`, JSON array of `LogEntry`
  ([`core/logger.ts:15`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L15),[`21-27`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L21-L27),[`148-149`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L148-L149),[`229-233`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L229-L233)).
- `/chat save` checkpoints: `tmp/<slug>/checkpoint-<encodeURIComponent(tag)>.json`
  ([logger.ts:285-295](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L285-L295),[329-343](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L329-L343); [`cli/.../chatCommand.ts:142`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/ui/commands/chatCommand.ts#L142)).
- Tool checkpoints: `tmp/<slug>/checkpoints/<ISO ts with : and . replaced>-<basename>-<tool>.json`
  ([`utils/checkpointUtils.ts:59-66`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/checkpointUtils.ts#L59-L66),[`130-141`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/checkpointUtils.ts#L130-L141); [storage.ts:364-366](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L364-L366)), backed by a
  shadow git repository at `~/.gemini/history/<slug>` ([storage.ts:326-330](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L326-L330);
  [`gitService.ts:74-75`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/gitService.ts#L74-L75)).
- Optional activity log: `tmp/<slug>/logs/session-<sessionId>.jsonl`
  ([`cli/src/utils/activityLogger.ts:693-699`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/utils/activityLogger.ts#L693-L699)). Schema not examined.
- Externalised large tool output: `tmp/<slug>/tool-outputs/`
  ([`utils/fileUtils.ts:799`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/fileUtils.ts#L799),[`814`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/fileUtils.ts#L814)); shell history `tmp/<slug>/shell_history`
  ([storage.ts:480-482](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L480-L482)).

The past-use stores beside the session file (`logs.json`, `shell_history`, the checkpoints,
`memory/`, the activity log and the `/bug` files) are described in
[section 5](#5-other-stores).

### What survives a delete

The CLI's delete command removes a session's chat file, its activity
log and its tool outputs
([`core/src/utils/sessionOperations.ts:59-116`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/utils/sessionOperations.ts#L59-L116);
at the first commit
[`core/src/utils/sessionOperations.ts:59-83`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/sessionOperations.ts#L59-L83)).
There is no remote copy to offer to delete.

Retention removes more without being asked, at
[`3be3d44`](https://github.com/google-gemini/gemini-cli/commit/3be3d4424b3c8a760d793ae1bea6cb5180adf27d):

- Every start runs `cleanupExpiredSessions`
  ([`cli/src/gemini.tsx:786`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/gemini.tsx#L786)).
  `general.sessionRetention.enabled` defaults to true and `maxAge` to
  `30d`, with an optional `maxCount`
  ([`settingsSchema.ts:389-430`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L389-L430)),
  so a default install keeps about a month of sessions per project. The
  cleanup also deletes every `session-*` file it cannot read, that
  lacks a `sessionId` or that has no resumable content
  ([`sessionCleanup.ts:302-311`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/sessionCleanup.ts#L302-L311);
  [`cli/src/utils/sessionUtils.ts:266-303`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/sessionUtils.ts#L266-L303)),
  and with each file the session's activity log, tool outputs and
  subagent sessions
  ([`sessionCleanup.ts:216-222`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/sessionCleanup.ts#L216-L222)).
  A session file truncated badly enough to fail loading is therefore
  removed by the next start.
- On exit a session with no resumable content (no real prompt, reply or
  tool activity) deletes its own file
  ([`chatRecordingService.ts:1327-1370`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/services/chatRecordingService.ts#L1327-L1370)).
- Background shell logs, `tmp/background-processes/background-<pid>.log`,
  are deleted after seven days
  ([`core/src/services/shellExecutionService.ts:390-392`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/services/shellExecutionService.ts#L390-L392);
  [`cli/src/utils/logCleanup.ts:11-43`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/logCleanup.ts#L11-L43)).
- Every start also deletes the whole tool-checkpoint directory
  ([Tool checkpoints](#tool-checkpoints)).

What remains of a deleted or expired session is the per-project prompt
history `logs.json`, which neither the delete command nor the retention
cleanup touches; `shell_history`, the last 100 shell-mode commands with
no time or session id; the `/chat save` checkpoints, removed only by
`/chat delete <tag>`; the shadow git repository under `history/<slug>`;
`memory/`; and the `bug-report-history-*.json` files from `/bug`. The
agent writes no deletion marker, and the requests already sent to Code Assist and Clearcut
under the session's `sessionId` are server-side records held by Google, which a responder can
only ask Google for ([Sync, relay and origin](#sync-relay-and-origin)). The analyzer reads
`logs.json` as a secondary source (see
[Secondary sources](../docs/output.md#secondary-sources)) and none of the
others ([section 8](#8-parser-plan)).

### Worktree sessions

With `experimental.worktrees` on (off by default),
`gemini --worktree [name]` creates a git worktree at
`<project>/.gemini/worktrees/<name>` on branch `worktree-<name>` and
changes into it before the configuration is loaded
([`core/src/services/worktreeService.ts:117-134`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/services/worktreeService.ts#L117-L134);
[`cli/src/utils/worktreeSetup.ts:28-35`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/worktreeSetup.ts#L28-L35);
[`gemini.tsx:496-505`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/gemini.tsx#L496-L505);
[`settingsSchema.ts:2234-2243`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L2234-L2243)).
The session's `.project_root` is then the worktree path. It lies under
a project, not under a home catalog entry, so the analyzer's catalog
rule does not class it as a scratch directory. There is no default
working directory for a session without a project: the CLI runs in the
directory it was started in.

### Driven from Zed

Zed's agent panel can run Gemini CLI as an external agent over ACP (the
Agent Client Protocol, the JSON-RPC protocol Zed uses to drive another
agent); its threads sidebar then lists the session in `sidebar_threads`
with `agent_id` `gemini` and the ACP session id in `session_id`, while
the transcript stays in Gemini CLI's own store
([`agent_servers/src/custom.rs:17-19`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_servers/src/custom.rs#L17-L19);
[section 2 of `zed.md`](zed.md#2-transcript-stores)). Whether that id
equals Gemini CLI's session id was not determined (Zed source review of
2026-10-19).

## 3. Record schema

### Session JSONL

Session JSONL ([`services/chatRecordingTypes.ts`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts)). Line 1 is
`PartialMetadataRecord` ([156-165](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L156-L165)): `sessionId`, `projectHash` (sha256 of the
project path), `startTime`, `lastUpdated` (ISO 8601), `summary?`,
`directories?: string[]`, `kind?: 'main'|'subagent'`. Later lines are one of
(discriminated at [`chatRecordingService.ts:79-95`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L79-L95)):

- `MessageRecord` = `BaseMessageRecord & ConversationRecordExtra` ([44-87](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L44-L87)):
  `id` (UUID), `timestamp` (ISO 8601 via `toISOString`,
  [chatRecordingService.ts:1022](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L1022)), `content: PartListUnion` (string, Part or
  Part[]), `displayContent?`, `type: 'user'|'info'|'error'|'warning'|'gemini'`.
  For `type:'gemini'` also `toolCalls?: ToolCallRecord[]`, `thoughts?:
  {subject, description, timestamp}[]` ([`utils/thoughtUtils.ts:7-10`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/thoughtUtils.ts#L7-L10)),
  `tokens?: {input, output, cached, thoughts?, tool?, total}` ([19-26](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L19-L26)),
  `model?: string`.
- `ToolCallRecord` ([54-67](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L54-L67)): `id`, `name`, `args: object`, `result?:
  PartListUnion|null`, `status` from `CoreToolCallStatus` =
  `validating|scheduled|error|success|executing|cancelled|awaiting_approval`
  ([`scheduler/types.ts:26-34`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/scheduler/types.ts#L26-L34)), `timestamp`, `agentId?`, `displayName?`,
  `description?`, `resultDisplay?` (string or `FileDiff{fileDiff, fileName,
  filePath, originalContent, newContent}`, [`tools/tools.ts:935-966`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/tools/tools.ts#L935-L966)),
  `renderOutputAsMarkdown?`.
- `{ "$set": {...metadata fields..., "memoryScratchpad"?, legacy "messages"?} }`
  ([149-154](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L149-L154)); `{ "$patch": { id?, content?, toolCalls?:[{id,result}], updates?,
  removeIds?, orderIds? } }` ([138-147](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L138-L147)); `{ "$rewindTo": "<message id>" }`
  ([123-125](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L123-L125)) drops that message and everything after it
  ([chatRecordingService.ts:305-335](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L305-L335)).

Current code records model text only as `content` ([geminiChat.ts:1652-1656](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/geminiChat.ts#L1652-L1656))
with tool calls in `toolCalls`; the reader also accepts `functionCall` and
`thought: true` parts inside `content` ("modern session",
[`utils/sessionUtils.ts:138-144`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/sessionUtils.ts#L138-L144)). No cwd and no git branch are stored in the
session file.

### logs.json

`logs.json` `LogEntry`: `sessionId`, `messageId` (per-session counter),
`timestamp` (ISO), `type: 'user'`, `message` ([logger.ts:17-27](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L17-L27)). User prompts
only.

### Checkpoints

`checkpoint-<tag>.json`: `{ "history": Content[], "authType"?: string }`
([logger.ts:29-32](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L29-L32)). `checkpoints/*.json` `ToolCallData`: `history?`,
`clientHistory?: Content[]`, `commitHash?`, `toolCall: {name, args}`,
`messageId?` (equals `prompt_id`) ([checkpointUtils.ts:15-24](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/checkpointUtils.ts#L15-L24),[130-139](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/checkpointUtils.ts#L130-L139)).

## 4. Joins and timestamps

Session = file; `sessionId` from line 1, overridden by any later
`$set.sessionId`, which is rewritten on resume ([chatRecordingService.ts:737](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L737)).
A tool call and its result are the same `toolCalls[]` element (`id`,
`result`, `status`); the whole gemini message is re-appended whenever its
tool calls change ([1118-1187](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L1118-L1187), [989-1005](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingService.ts#L989-L1005)), so a parser must keep the last
record per `id` and apply `$patch` and `$rewindTo`. Project path: the
`tmp/<slug>/.project_root` content or a `projects.json` reverse lookup;
legacy hash directories have no reverse map (compare sha256 of known cwds).
`kind` plus directory nesting links a subagent session to its parent.

## 5. Other stores

No SQLite store. `~/.gemini/history/<slug>` is a shadow git repository; treat it as
binary.

Past use beyond the session file, at
[`3be3d44`](https://github.com/google-gemini/gemini-cli/commit/3be3d4424b3c8a760d793ae1bea6cb5180adf27d)
(source review of 2026-10-19). Each is collected under `.gemini`; only
`logs.json` is parsed.

### logs.json

`logs.json` (secondary, parsed): user prompts. Neither the delete
command nor the retention cleanup ([What survives a delete](#what-survives-a-delete))
touches it (`logs.json` and
`LOG_FILE_NAME` do not occur in
[`core/src/utils/sessionOperations.ts`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/utils/sessionOperations.ts)
or
[`cli/src/utils/sessionCleanup.ts`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/sessionCleanup.ts)),
so it is the only prompt record of an expired or deleted session.

### shell_history

`shell_history` (secondary, not parsed): the commands the user ran
in shell mode (`!`), plain text, oldest first, one command per line
with a trailing `\` joining a continued line, deduplicated and capped
at 100, no time and no session id
([`cli/src/ui/hooks/useShellHistory.ts:12`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/ui/hooks/useShellHistory.ts#L12),
[31-71](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/ui/hooks/useShellHistory.ts#L31-L71),
[89-100](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/ui/hooks/useShellHistory.ts#L89-L100)).
The session file repeats each command inside a synthetic user message
`I ran the following shell command: ...`
([`cli/src/ui/hooks/useExecutionLifecycle.ts:44-69`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/ui/hooks/useExecutionLifecycle.ts#L44-L69);
[`core/src/core/geminiChat.ts:1304-1316`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/core/geminiChat.ts#L1304-L1316)),
so it joins on text only. It survives deletion and retention, since
it is per project, not per session.

### /chat save checkpoints

`checkpoint-<tag>.json` from `/chat save` (secondary, not parsed): a
full `history` array with no time or session id
([section 3](#3-record-schema)). Removed only by `/chat delete <tag>`
([`core/src/core/logger.ts:393`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/core/logger.ts#L393)),
so it survives the session's deletion and expiry; joins on text.

### Tool checkpoints

`checkpoints/*.json` tool checkpoints (secondary, not parsed): the
`clientHistory` before each file-changing tool call. The CLI deletes
the whole directory at every start
([`cli/src/utils/cleanup.ts:187-197`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/cleanup.ts#L187-L197);
called from
[`cli/src/gemini.tsx:507-512`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/gemini.tsx#L507-L512)),
so only the checkpoints of the last run in each project exist. The
shadow git repository under `history/<slug>` is not cleaned.

### memory/

`tmp/<slug>/memory/` (a projection, not parsed): `MEMORY.md` and
skills the memory tool writes, and, under `experimental.autoMemory`
(off by default), `.inbox/<kind>/*.patch` files that a background
agent extracts "from past sessions"
([`core/src/config/storage.ts:332-342`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/config/storage.ts#L332-L342);
[`core/src/tools/memoryTool.ts:12`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/tools/memoryTool.ts#L12);
[`cli/src/config/settingsSchema.ts:2432-2441`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L2432-L2441)).
No session id or time; it outlives the sessions it was drawn from.

### Activity log

`logs/session-<sessionId>.jsonl`, the activity log (secondary, not
parsed): one JSON object per line, `{type: "console"|"network",
payload, sessionId, timestamp}` with `timestamp` in epoch
milliseconds; a `network` payload carries request and response
bodies, so the model calls themselves
([`cli/src/utils/activityLogger.ts:101-118`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/activityLogger.ts#L101-L118),
[688-730](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/activityLogger.ts#L688-L730)).
Written only in interactive mode with `general.devtools` on (off by
default), to `GEMINI_CLI_ACTIVITY_LOG_TARGET` when that is set
([`cli/src/gemini.tsx:757-762`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/gemini.tsx#L757-L762);
[`cli/src/utils/devtoolsService.ts:121-132`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/utils/devtoolsService.ts#L121-L132);
[`settingsSchema.ts:247-255`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L247-L255)).
The delete command removes it with the session
([`sessionOperations.ts:59-116`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/utils/sessionOperations.ts#L59-L116)).

### Bug reports

`bug-report-history-<epoch ms>.json` from `/bug` (secondary, not parsed) and
`bug-memory-<epoch ms>.heapsnapshot` from `/bug-memory`.
`/bug` opens a GitHub new-issue URL carrying the CLI version and the
session id, and, when the history is longer than the initial context,
writes the history to `~/.gemini/tmp/<slug>/bug-report-history-<epoch
ms>.json` and asks the user to attach it by hand
([`cli/src/ui/commands/bugCommand.ts:63-125`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/ui/commands/bugCommand.ts#L63-L125)).
That file is a copy of the conversation in the
`exportHistoryToFile` JSON form and outlives a deleted session; it
says nothing about whether it was uploaded. `/bug-memory` writes a V8
heap snapshot, `bug-memory-<epoch ms>.heapsnapshot`, to the same
directory
([`cli/src/ui/commands/bugMemoryCommand.ts:26-41`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/ui/commands/bugMemoryCommand.ts#L26-L41)).
The heap snapshot is a dump of the CLI process's memory; the collector flags it as a secret
([section 3 of
`collectors/research/gemini-cli.md`](../../collectors/research/gemini-cli.md#3-credentials)).

### Standing permission files

Shapes from the source review of 2026-10-19, at [`3be3d44`](https://github.com/google-gemini/gemini-cli/commit/3be3d4424b3c8a760d793ae1bea6cb5180adf27d); none is parsed yet
([Permission state](#permission-state)).

`policies/auto-saved.toml`, in `~/.gemini/policies/` for a grant
the user saved for every project and in `<project>/.gemini/policies/`
for one saved for the workspace
([`core/src/config/storage.ts:28`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/config/storage.ts#L28),
[150-152](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/config/storage.ts#L150-L152),
[236-249](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/config/storage.ts#L236-L249)).
Written when the user picks "Allow for all future sessions": a TOML
document whose `rule` array holds one table per grant with
`decision = "allow"`, `priority`, `toolName`, and optionally
`mcpName`, `commandPrefix` (string or array), `argsPattern`,
`allowRedirection` and `modes` (approval modes)
([`core/src/policy/config.ts:646-657`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/policy/config.ts#L646-L657),
[684-710](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/policy/config.ts#L684-L710),
[795-880](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/policy/config.ts#L795-L880)).
An unparseable file is copied to `auto-saved.toml.bak` and replaced
by a fresh one ([824](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/policy/config.ts#L824)),
so the `.bak` holds the grants from before.

`settings.json` (home and project): `general.defaultApprovalMode`
(`default`, `auto_edit` or `plan`; YOLO only from the command line)
([`cli/src/config/settingsSchema.ts:228-245`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L228-L245);
the runtime enum `default`, `autoEdit`, `yolo`, `plan` is at
[`core/src/policy/types.ts:48-53`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/policy/types.ts#L48-L53)),
`tools.allowed`, `tools.confirmationRequired` and `tools.exclude`
([1682-1719](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L1682-L1719)),
`security.disableYoloMode`, `security.disableAlwaysAllow`,
`security.enablePermanentToolApproval`,
`security.autoAddToPolicyByDefault` and
`security.folderTrust.enabled`
([1845-1925](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L1845-L1925)).

`trusted_hooks.json`: `{"<project path>": ["<hook name>:<command>",
...]}`, the project hooks the user trusted
([`core/src/hooks/trustedHooks.ts:72`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/hooks/trustedHooks.ts#L72),
[103-119](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/hooks/trustedHooks.ts#L103-L119);
key form at
[`core/src/hooks/types.ts:121-125`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/hooks/types.ts#L121-L125)).
`acknowledgments/agents.json`: `{"<project path>": {"<agent name>":
"<agent hash>"}}`, the project subagents the user acknowledged
([`core/src/agents/acknowledgedAgents.ts:13-18`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/agents/acknowledgedAgents.ts#L13-L18)).

## 6. Format versions

Hash directories became slug directories (copied, both remain); single-object
`session-*.json` became `.jsonl`; `$set.messages` full-history checkpoints are
deprecated ([chatRecordingTypes.ts:150-153](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/chatRecordingTypes.ts#L150-L153)); `checkpoint-<tag>` moved from a
raw array to `{history, authType}` ([logger.ts:359-372](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L359-L372)); legacy un-encoded
`checkpoint-<tag>.json` names ([logger.ts:312-313](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/core/logger.ts#L312-L313)). No explicit version field.

## 7. Secrets

`~/.gemini/oauth_creds.json` ([storage.ts:22](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L22),[255-257](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L255-L257)), `mcp-oauth-tokens.json`,
`a2a-oauth-tokens.json` ([70-76](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/storage.ts#L70-L76)), `gemini-credentials.json`
([`services/fileKeychain.ts:20`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/services/fileKeychain.ts#L20)), `google_accounts.json`. Checkpoints
(`clientHistory`) and `toolCalls[].result` embed full tool output.

## 8. Parser plan

Globs (home-relative): `.gemini/tmp/*/chats/**/*.jsonl`,
`.gemini/tmp/*/chats/**/*.json`, `.gemini/tmp/*/logs.json`,
`.gemini/tmp/*/checkpoints/*.json`, `.cache/.gemini/tmp/*/chats/**/*.jsonl`.

Rows: one per user, info, error or warning message; one `assistant` row per
gemini message plus one `thinking` row per `thoughts[]` entry; one `tool_use`
per `toolCalls[]` element and one `tool_result` when `result` is non-null,
sharing the `tool_use_id`; `logs.json` entries as `user` rows when no session
file covers that `sessionId`.

| Column | Source |
| --- | --- |
| timestamp_utc | `timestamp` (ISO); `toolCalls[].timestamp`, `thoughts[].timestamp` |
| session_id | line-1 `sessionId`, overridden by later `$set.sessionId` |
| project_path | `.project_root` or `projects.json`; else `projectHash` |
| git_branch | empty |
| turn_type | user → user; gemini → assistant; info/error/warning → system; toolCalls → tool_use/tool_result; thoughts → thinking |
| model | `model` |
| tool_name, tool_use_id | `toolCalls[].name`, `toolCalls[].id` |
| text | `content` text; for tool_use `displayName` plus args; `summary` on `$set` |

### Permission state

Permission rows (issues 96 and 97), added with the model rows in [Model](#model):

- `permission decision: <status>` (`system`, the call's `tool_name` and
  `tool_use_id`) after the `tool_result` row of a `toolCalls[]` element
  whose `status` is `cancelled` or `awaiting_approval`, or after its
  `tool_use` row when it has no result. The `[cancelled]` (and
  `[error]`) prefix on the result row stays. No other approval record is
  written to the session file.
- `permission setting: trustedFolders.<path>=<value> (from <file>, file
  mtime)` (`system`, `project_path` the folder, no session id, the
  file's modification time, line 1), one per key of
  `~/.gemini/trustedFolders.json`. The file is a JSON object read with
  comments stripped ([`utils/trust.ts:106`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/trust.ts#L106)) whose
  keys are folder paths and whose values are a `TrustLevel`:
  `TRUST_FOLDER`, `TRUST_PARENT` or `DO_NOT_TRUST`
  ([`utils/trust.ts:18-22`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/trust.ts#L18-L22),
  [95-96](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/trust.ts#L95-L96)); the CLI writes it with
  `JSON.stringify` ([342](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/utils/trust.ts#L342)). The value is printed as
  recorded. The same reader serves Qwen Code's `~/.qwen/trustedFolders.json`,
  which Qwen now reads as JSONC (JSON with comments) with trailing commas
  allowed and a leading byte-order mark dropped
  ([`jsonc-editor.ts:24`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/utils/jsonc-editor.ts#L24),
  [92-107](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/utils/jsonc-editor.ts#L92-L107)),
  so the parser drops a byte-order mark, strips comments and drops a
  comma that only whitespace separates from a closing `}` or `]`, outside
  strings, before decoding; a Gemini CLI file reads as before. This
  form is not observed on any real install, source-derived
  (QwenLM/qwen-code at
  [`5dcf7c7`](https://github.com/QwenLM/qwen-code/commit/5dcf7c7cb162e825d95d531081f67ee60da3c0e1)).
  A file that still does not decode, or is not a JSON object, is one
  `parser: <file> is not a JSON object` row.
- Not read: `policies/auto-saved.toml` (the saved "always allow"
  policies), `policy_integrity.json`, `trusted_hooks.json` and
  `acknowledgments/agents.json`; their shapes were not recorded at the first
  review (nor in
  [`collectors/research/gemini-cli.md`](../../collectors/research/gemini-cli.md)) and are now in
  [Standing permission files](#standing-permission-files).

Proposed rows for the standing grants (source review of 2026-10-19, not yet parsed):

- `policies/auto-saved.toml`:
  `permission setting: policy allow <toolName> [mcp=<mcpName>]
  [prefix=<commandPrefix>|args=<argsPattern>] [modes=<modes>] (from
  <file>, file mtime)`, one per `rule` entry, `project_path` the
  project for the workspace file. Reading it needs a TOML reader
  (Python 3.11's `tomllib`; the analyzer supports 3.10).
- `settings.json`: one `permission setting: <key>=<value> (from <file>, file
  mtime)` row per key present.
- `trusted_hooks.json` and `acknowledgments/agents.json`: one `permission setting:` row per
  entry, `project_path` the key.
- Per-call decisions: unchanged. The session file records the call's
  `status` only; which button the user pressed is not recorded.

### Model

- `model: <id>` (`system`, `model` column set) before the first gemini
  message of a session whose `model` is set, and `model: <old> -> <new>`
  before each later gemini message whose `model` differs, tracked per
  `sessionId` in replay order, with the message's timestamp and line.
  The format keeps one `model` per message and no separate switch record.
- Covered, at the source review of 2026-10-19. Each gemini message's `model` is the resolved model
  after routing; the alias the user chose is `model.name` in
  `settings.json`
  ([`settingsSchema.ts:1062-1075`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/config/settingsSchema.ts#L1062-L1075)),
  and `/model set <name> [--persist]` adds the `info` message `Model set
  to <name>` ([`cli/src/ui/commands/modelCommand.ts:18-47`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/ui/commands/modelCommand.ts#L18-L47)),
  recorded because `info` items are written to the session
  ([`cli/src/ui/hooks/useHistoryManager.ts:91-123`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/cli/src/ui/hooks/useHistoryManager.ts#L91-L123)).
  User and info messages carry no `model`
  ([`chatRecordingService.ts:1079-1105`](https://github.com/google-gemini/gemini-cli/blob/3be3d4424b3c8a760d793ae1bea6cb5180adf27d/packages/core/src/services/chatRecordingService.ts#L1079-L1105)).

### Past use and secondary sources

`logs.json` is read as a secondary source: its entries become `user` rows when no session file
covers that `sessionId` (see [Secondary sources](../docs/output.md#secondary-sources)).

From the source review of 2026-10-19: `shell_history`, `checkpoint-<tag>.json` and
`checkpoints/*.json` are secondary sources to add, rows with an empty
`timestamp_utc` matched on text; `memory/` and the activity log are
candidates after a real-install round shows them
([section 5](#5-other-stores)).

### Sync, relay and origin

Sync: Gemini CLI records no sync state. No command uploads a session,
and nothing under `~/.gemini` holds a remote id, share URL or synced
flag. What was searched, at the commit in [section 1](#1-source-and-evidence):

- `/chat share` (also `/resume share`) writes the conversation to a
  local `.md` or `.json` file, by default
  `gemini-conversation-<epoch ms>.json` in the working directory
  ([`cli/src/ui/commands/chatCommand.ts:282-331`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/ui/commands/chatCommand.ts#L282-L331);
  [`cli/src/ui/utils/historyExportUtils.ts:61-81`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/ui/utils/historyExportUtils.ts#L61-L81)),
  and `/export-session <path>` writes the session record as JSON to the
  path given
  ([`cli/src/ui/commands/exportSessionCommand.ts:18-76`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/ui/commands/exportSessionCommand.ts#L18-L76)).
  Neither sends anything over the network.
- `/bug` and `/bug-memory` write local files only; see [Bug reports](#bug-reports).
- Code Assist (Google's `cloudcode-pa.googleapis.com` backend, used
  when the user signs in with a Google account,
  [`core/src/code_assist/server.ts:73-74`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/code_assist/server.ts#L73-L74))
  receives the local `sessionId` as `session_id` in every model request
  ([`core/src/code_assist/converter.ts:163-177`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/code_assist/converter.ts#L163-L177)),
  so the transcript's `sessionId` is also the key of the server's
  request records; that is the model API call, not sync. Its metrics
  calls, `recordConversationOffered` and
  `recordConversationInteraction`, carry a trace id, counts, latencies
  and an accept or reject status, no text
  ([`core/src/code_assist/types.ts:311-336`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/code_assist/types.ts#L311-L336);
  [`server.ts:376-412`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/code_assist/server.ts#L376-L412)).
  The free-tier "allow Google to use my data" choice in `/privacy` is a
  server-side user setting, `freeTierDataCollectionOptin`, read and
  written through the API and not stored locally
  ([`cli/src/ui/hooks/usePrivacySettings.ts:153-193`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/ui/hooks/usePrivacySettings.ts#L153-L193)).
  The server's `traceId` becomes the in-memory `responseId`
  ([`converter.ts:145-150`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/code_assist/converter.ts#L145-L150))
  and is not written to the session file: `responseId`, `traceId`,
  `remote`, `cloud` and `upload` do not occur in
  `core/src/services/chatRecordingService.ts` or
  `chatRecordingTypes.ts`.
- Clearcut, Google's event-logging endpoint
  `play.googleapis.com/log`, receives usage statistics when
  `privacy.usageStatisticsEnabled` in `settings.json` is on, which is
  the default
  ([`core/src/telemetry/clearcut-logger/clearcut-logger.ts:244`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/clearcut-logger/clearcut-logger.ts#L244),
  [340-342](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/clearcut-logger/clearcut-logger.ts#L340-L342);
  [`cli/src/config/settingsSchema.ts:970-976`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/config/settingsSchema.ts#L970-L976)).
  Each event carries the session id and the signed-in Google account's
  email, or the `installation_id` when there is none
  ([clearcut-logger.ts:496-501](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/clearcut-logger/clearcut-logger.ts#L496-L501),
  [1157-1162](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/clearcut-logger/clearcut-logger.ts#L1157-L1162)).
  The prompt event sends the prompt's length, not its text
  ([743-751](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/clearcut-logger/clearcut-logger.ts#L743-L751)).
  The one exception is Conseca, the context-aware security checker
  that has a model write a tool policy from the prompt
  (`security.enableConseca`, off by default,
  [`settingsSchema.ts:2007-2014`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/cli/src/config/settingsSchema.ts#L2007-L2014)):
  with it on, its Clearcut events carry the user prompt, the trusted
  content, the generated policy and the verdict rationale whenever
  `telemetry.logPrompts` is on, which is its default
  ([`core/src/telemetry/conseca-logger.ts:33-46`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/conseca-logger.ts#L33-L46),
  [85-98](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/conseca-logger.ts#L85-L98);
  [`core/src/config/config.ts:2913-2915`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/config.ts#L2913-L2915)).
  Prompt text then leaves the host with no local record that it did.
- OpenTelemetry export (`telemetry.enabled`, off by default; target
  `local` by default or `gcp`, the user's own Google Cloud project,
  [`config.ts:1094-1100`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/config/config.ts#L1094-L1100);
  [`core/src/telemetry/index.ts:7-12`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/index.ts#L7-L12))
  puts the prompt text in the `user_prompt` log record when
  `telemetry.logPrompts` is on
  ([`core/src/telemetry/types.ts:222-224`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/telemetry/types.ts#L222-L224)).
  It goes to a collector the user configures, not to a vendor account;
  a `telemetry.outfile` path in `settings.json` is a local copy of
  those records wherever the user put it.
- Remote subagents over A2A (the Agent2Agent protocol, a remote agent
  the user configures by URL) keep the remote `contextId` and `taskId`
  in a static in-memory map only
  ([`core/src/agents/remote-session-invocation.ts:43-57`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/agents/remote-session-invocation.ts#L43-L57),
  [242-247](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/core/src/agents/remote-session-invocation.ts#L242-L247)).
  The `a2a-server` package, a server the user deploys and not part of
  the CLI, stores tasks in a Google Cloud Storage bucket when
  `GCS_BUCKET_NAME` is set
  ([`a2a-server/src/http/app.ts:250-256`](https://github.com/google-gemini/gemini-cli/blob/fb972b2f87fe7d5b06d37eac711490162d98de2c/packages/a2a-server/src/http/app.ts#L250-L256)).
- A session deleted through the CLI leaves no remote copy to delete; see
  [What survives a delete](#what-survives-a-delete).

No row is proposed; the agent records none.

### Scratch directories

A session whose `.project_root` lies under
`<project>/.gemini/worktrees/` should yield `scratch directory: <path>
(gemini --worktree <name>)`. The worktree facts are in [Worktree sessions](#worktree-sessions).

### Deletion

No row; a deletion leaves no marker to read. The agents
page should tell the analyst that a default install deletes sessions
older than 30 days at each start and that `logs.json`,
`shell_history` and the `/chat save` checkpoints are what remains
([What survives a delete](#what-survives-a-delete)).

### Bad lines

The parser covers the session file, `logs.json` and `trustedFolders.json`
([Source reviews](#source-reviews)); the sources proposed in this section need the same
treatment when they are parsed.
`shell_history` has no structure to break, but a line that
is not valid UTF-8 must still become a row carrying the line.

### Fixtures

Fixture (one JSON object per line):

```json
{"sessionId":"a1b2c3d4-0000-4000-8000-000000000001","projectHash":"9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08","startTime":"2026-10-01T09:00:00.000Z","lastUpdated":"2026-10-01T09:00:00.000Z","kind":"main"}
{"id":"6a0e3e5a-1111-4000-8000-000000000002","timestamp":"2026-10-01T09:00:05.000Z","type":"user","content":[{"text":"list files in src"}]}
{"id":"7b1f4f6b-2222-4000-8000-000000000003","timestamp":"2026-10-01T09:00:07.000Z","type":"gemini","content":"Listing now.","thoughts":[{"subject":"Plan","description":"Use the ls tool.","timestamp":"2026-10-01T09:00:06.500Z"}],"tokens":{"input":120,"output":12,"cached":0,"thoughts":8,"tool":0,"total":140},"model":"gemini-2.5-pro","toolCalls":[{"id":"list_directory-1759309207000","name":"list_directory","args":{"path":"/home/alice/proj/src"},"status":"success","timestamp":"2026-10-01T09:00:07.100Z","result":[{"functionResponse":{"id":"list_directory-1759309207000","name":"list_directory","response":{"output":"main.ts\nutil.ts"}}}],"displayName":"ReadFolder","description":"Lists files"}]}
{"$set":{"lastUpdated":"2026-10-01T09:00:08.000Z","summary":"List src files"}}
{"$patch":{"id":"7b1f4f6b-2222-4000-8000-000000000003","toolCalls":[{"id":"list_directory-1759309207000","result":null}]}}
{"$rewindTo":"7b1f4f6b-2222-4000-8000-000000000003"}
```

`logs.json`:

```json
[{"sessionId":"a1b2c3d4-0000-4000-8000-000000000001","messageId":0,"timestamp":"2026-10-01T09:00:05.000Z","type":"user","message":"list files in src"}]
```

### Confidence

High (type definitions and writers): record field names, file
paths, status values, ISO timestamps, slug registry and `.project_root`.
Medium: whether current Gemini ever writes `functionCall` parts into
`content` (the reader supports it, the examined writer does not). Not
determined: the `activityLogger` JSONL schema and whether it is on by
default (the source review of 2026-10-19 later recorded both; see
[Activity log](#activity-log)); the `a2a-server` and `sdk` packages' separate storage.
