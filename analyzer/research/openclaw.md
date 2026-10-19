# openclaw

OpenClaw (catalog agent `openclaw`, previously Clawdbot and then Moltbot) is a self-hosted agent
whose Gateway (the long-running `openclaw gateway` server process that owns every session) takes
messages from chat channels and runs agents; the Control UI (its web front end), the TUI and the
mobile and desktop apps are clients of that Gateway, not copies of its store, and OpenClaw has no
vendor account. Its transcript record shape (`type:
"session"` header, then `message`, `model_change`, `compaction` and other
entries linked by `id`/`parentId`) is the tree-structured session format of
its agent core; since mid-2026 the records live as rows in a per-agent SQLite
database rather than in `.jsonl` files, which remain only as legacy import
sources and archives. Path research is in
[`collectors/research/openclaw.md`](../../collectors/research/openclaw.md).

## 1. Source and evidence

[openclaw/openclaw](https://github.com/openclaw/openclaw) at [`3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9`](https://github.com/openclaw/openclaw/commit/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9)
(2026-10-04, version `2026.9.8`, agent schema version 24 per
[`package.json:5-9`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/package.json#L5-L9)), MIT, open source.
Session sharing, backup upload and remote execution were checked at the same
commit on 2026-10-17.

### Observed

- No real install of OpenClaw has been surveyed; the source review of 2026-10-19 was source
  only.
- The bad-line rows of issue 177 (the legacy `sessions.json` index and JSON lines that are not
  objects) are not observed on any real install, source-derived
  ([openclaw/openclaw](https://github.com/openclaw/openclaw) at
  [`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b)).
- The public-share and backup-upload rows are fixture only
  ([Sync, relay and origin](#sync-relay-and-origin)).

### Source reviews

- **Source review (2026-10-19).** [openclaw/openclaw](https://github.com/openclaw/openclaw)
  at [`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b)
  (2026-10-19, version `2026.10.5`,
  [`package.json:3`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/package.json#L3);
  shared-state schema 28 and agent schema 31,
  [`package.json:17-20`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/package.json#L17-L20)),
  against [`3b16db7`](https://github.com/openclaw/openclaw/commit/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9),
  which the rest of this document cites (state 20, agent 24). Per requirement class (the
  parser work each class leads to is under [section 8](#8-parser-plan)):
  - Permission state: found, not parsed. Per-call decisions are rows of
    `operator_approvals` and standing settings rows of `exec_approvals_config`
    and `operator_approval_standing_grants` in `state/openclaw.sqlite`, all
    present at both commits; columns and values in
    [Permission records](#permission-records).
  - Model: covered for the transcript (`model_change`, `responseModel`,
    `session_windows.model`); found and not parsed, the session's own
    override in `session_nodes.entry_json` (`modelOverride`,
    `providerOverride`, `modelOverrideSource`), in
    [Model override](#model-override).
  - Past use beyond the primary store: found, not parsed: the transcript
    search index, queued and cancelled prompts, the memory index's session
    chunks and the raw inbound channel messages, in
    [Other records of past use](#other-records-of-past-use).
  - Sync, relay and origin: sync already covered (public share, backup
    upload). Relay found and not parsed: every channel session's
    `session_windows`, `conversations` and `session_nodes.entry_json`
    `delivery` name the platform, account and peer
    ([section 4](#4-joins-and-timestamps)). Origin: none (no session starts on a vendor
    server; grepped `origin` and `remote` in `src/config/sessions/`). New
    since the last review: the experimental PostgreSQL engine, which leaves
    only an anchor in `openclaw-agent.sqlite` ([PostgreSQL engine](#postgresql-engine)).
  - Scratch directories: found; the default workspace, managed worktrees,
    Gateway clones and sandbox workspaces are under the state directory,
    so the analyzer's catalog rule classes them; see
    [Scratch directories in `collectors/research/openclaw.md`](../../collectors/research/openclaw.md#scratch-directories).
  - Deletion: found: archive (`archivedAt`, `archiveReason`), delete (a
    `.jsonl.deleted.*` archive unless incognito) and memory forget
    (`memory_session_tombstones`); no `session deleted:` row is written
    today ([Deletion](#deletion)).
  - Version drift: the transcript entry shape, header version 4 and every
    column the parser reads are unchanged; the file-name patterns moved from
    `artifacts.ts` to `transcript-file-names.ts` unchanged; agent schemas 25
    to 31 add navigation and outbox columns the parser does not read
    ([section 6](#6-format-versions)). The PostgreSQL engine is the one
    change that leaves the parser with nothing to read.
  - Bad lines: two gaps in the parser, the legacy `sessions.json` index and
    JSON lines that are not objects, both dropped without a row; both now
    yield a `parser:` row ([Bad lines](#bad-lines), issue 177).

## 2. Transcript stores

Home-relative, with `.openclaw` replaceable by `.openclaw-<profile>` or the
legacy `.clawdbot`:

- `.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite` with `-wal`/`-shm`:
  the live store. One database per agent; one `session_windows` row per
  transcript generation; one `transcript_events` row per record
  ([`src/state/openclaw-agent-schema.sql:159-188`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L159-L188),[`566-604`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L566-L604)). `agentDir` can be
  moved by config ([`agents/agent-scope-config.ts:577-588`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/agents/agent-scope-config.ts#L577-L588)).
- `.openclaw/agents/<agentId>/sessions/<sessionId>.jsonl`: legacy one-file-per-session
  transcripts, imported into SQLite by `openclaw doctor --fix` and then
  removed ([`docs/cli/doctor/state-migrations.md:60`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/cli/doctor/state-migrations.md#L60)); a host that never ran
  doctor after upgrading still has them. `sessions/` at the state root is
  the older single-agent equivalent ([`docs/openclaw-agent-runtime.md:58-59`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/openclaw-agent-runtime.md#L58-L59)).
- Same directory, archives of reset or deleted sessions:
  `<sessionId>.jsonl.reset.<YYYY-MM-DDTHH-MM-SS[.mmm]Z>[.<32 hex generation>][.zst]`
  and `.jsonl.deleted.<...>` ([`config/sessions/artifacts.ts:10-32`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/artifacts.ts#L10-L32); naming
  [`session-accessor.sqlite-archive-artifact.ts:47`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-archive-artifact.ts#L47),[`70`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-archive-artifact.ts#L70)). `.zst` files are a
  single zstd frame of the JSONL ([`config/sessions/archive-compression.ts:11-30`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/archive-compression.ts#L11-L30)). The
  canonical copy of each archive is also a blob in `session_transcript_archives`
  ([`openclaw-agent-schema.sql:606-624`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L606-L624)). Deleting a session keeps a `.deleted`
  archive unless it was incognito ([`docs/cli/sessions.md:212-217`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/cli/sessions.md#L212-L217)).
- Also there: `<id>.checkpoint.<uuid>.jsonl` compaction checkpoints,
  `<id>.trajectory.jsonl` runtime trajectories, `*.migrated[.N]` and
  `*.pre-doctor-*-repair-*.bak` rollback copies (which of them are copies
  of a transcript is in [Past use and secondary sources](#past-use-and-secondary-sources))
  ([`artifacts.ts:13-17`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/artifacts.ts#L13-L17),[`96-116`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/artifacts.ts#L96-L116)),
  and a legacy `sessions.json` index.

The agent database uses a WAL journal ([`infra/sqlite-wal.ts:169`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/infra/sqlite-wal.ts#L169)), read through
`sqlite_util.py` with sidecars. Payloads of 1 KiB to 4 MiB that shrink by at
least 10% are stored as `event_zstd` (one zstd frame, level 1, checksum,
no dictionary) with `event_json` NULL and the original length in
`event_utf8_bytes`; others stay in `event_json`
([`config/sessions/transcript-payload.ts:22-24`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/transcript-payload.ts#L22-L24),[`215-272`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/transcript-payload.ts#L215-L272); [`infra/zstd-codec.ts:22-37`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/infra/zstd-codec.ts#L22-L37)).
The parser needs `zstandard`. Cold storage moves old generations into
`session_transcript_cold_archives` (blob, or a file in the sessions directory
when `storage='file'`, [`:633-648`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L633-L648)); `archive_blob` in both archive tables
is JSONL, zstd when `encoding='zstd'`.

### What survives a delete

`openclaw sessions archive` keeps the transcript and only sets
`archivedAt`, `archivedBy` and `archiveReason`
(`manual|active-session-cap|age-retention|stale-dashboard|restart-recovery`)
in `entry_json`, mirrored in `session_nodes.archived_at`
([`docs/cli/sessions.md:181-196`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/cli/sessions.md#L181-L196);
[`src/config/sessions/types.ts:300-305`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/types.ts#L300-L305);
[`gateway-protocol/src/schema/sessions-row.ts:48-54`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/packages/gateway-protocol/src/schema/sessions-row.ts#L48-L54)).
`openclaw sessions delete` removes the session row, its generations and bindings and keeps
a `.jsonl.deleted.<ts>` archive with its `session_transcript_archives`
blob (`reason` `deleted`) unless the session was incognito, as a reset keeps a
`.jsonl.reset.<ts>` one
([`docs/cli/sessions.md:222-233`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/cli/sessions.md#L222-L233)).

The memory index keeps the session's `memory_index_chunks` until
`openclaw memory forget`, which writes one `memory_session_tombstones`
row (`session_id`, `agent_id`, `reason`, default `forgotten`, `created_at`) per forgotten
session
([`openclaw-agent-schema.sql:699-704`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L699-L704);
[`extensions/memory-core/src/memory-session-tombstones.ts:89-106`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/extensions/memory-core/src/memory-session-tombstones.ts#L89-L106));
inbound channel messages in
`channel_ingress_events` are pruned by age and count, not by deletion,
`conversation_deliveries` rows go only with their conversation, and an
uploaded backup keeps the session. Pending inputs cascade away with the
session, whether the full-text index rows go is not determined, and a
public share grant is lost with the session row
([Other records of past use](#other-records-of-past-use),
[Sync, relay and origin](#sync-relay-and-origin)). There is no prompt-history file.

The analyzer reads the archive blobs as primary and the published
`.jsonl.deleted.*` and `.jsonl.reset.*` files as secondary, shows a
deleted archive only as an `archive=deleted.<ts>` session-start row and
the backups as `backup uploaded:` rows, and does not read the memory
index, the tombstones, the full-text index or the channel tables (see
[Secondary sources](../docs/output.md#secondary-sources) and [Deletion](#deletion)).

## 3. Record schema

### Transcript entries

Each `transcript_events.event_json` (or decompressed `event_zstd`) and each
legacy JSONL line is one entry ([`agents/sessions/session-manager-types.ts:9-119`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/agents/sessions/session-manager-types.ts#L9-L119)):

- Header: `{type:"session", version, id, timestamp, cwd, parentSession?}`,
  always the first record ([`config/sessions/transcript-header.ts:20-29`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/transcript-header.ts#L20-L29);
  [`session-accessor.sqlite-transcript-header.ts:7-35`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-transcript-header.ts#L7-L35)). `cwd` defaults to the
  process cwd when the caller gives none.
- Every other entry: `type`, `id`, `parentId` (null at the root), `timestamp`
  (ISO 8601 string, UTC from `toISOString()`), optional `appendMode:"side"`.
  Types: `message`, `thinking_level_change {thinkingLevel}`,
  `model_change {provider, modelId}`, `compaction {summary, firstKeptEntryId,
  tokensBefore, tokensAfter?, details?, fromHook?}`, `reset {reason:
  new|reset|idle|daily|cron-stale}`, `branch_summary {fromId, summary}`,
  `custom {customType, data}`, `custom_message {customType, content, display}`,
  `label {targetId, label}`, `session_info {name}`. Unknown records with
  `id`/`parentId` (for example `leaf`) are preserved opaquely
  ([`config/sessions/session-entry-codec.ts:181-221`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-entry-codec.ts#L181-L221)).
- `message.message` is an `AgentMessage`
  ([`packages/agent-core/src/types.ts:467-479`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/agent-core/src/types.ts#L467-L479)), discriminated by `role`
  ([`packages/llm-core/src/types.ts:369-390`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/llm-core/src/types.ts#L369-L390),[`516-561`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/llm-core/src/types.ts#L516-L561)):
  - `user`: `content` string or blocks, `timestamp` (epoch ms).
    `runtimeContext` marks injected runtime context, not human input.
  - `assistant`: `content` blocks, `api`, `provider`, `model`,
    `responseModel?`, `responseId?`, `turnId?`, `usage {input, output,
    cacheRead, cacheWrite, totalTokens, cost{...}}`, `stopReason`
    (`stop|length|toolUse|error|aborted`, [`:357`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/llm-core/src/types.ts#L357)), `errorMessage?`,
    `errorBody?`, `providerReplay?`, `timestamp` ms.
  - `toolResult`: `toolCallId`, `toolName`, `content` (text/image blocks),
    `details?`, `isError`, `timestamp` ms.
  - `bashExecution`: `command`, `output`, `exitCode`, `cancelled`,
    `truncated`, `fullOutputPath?`, `timestamp` ms (user-run `!` commands,
    [`agent-core/src/types.ts:397-416`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/agent-core/src/types.ts#L397-L416)).
  - `custom {customType, content, display, details?}`, `branchSummary
    {summary, fromId}`, `compactionSummary {summary, tokensBefore}` (its
    `timestamp` may be a string, [`:418-461`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/agent-core/src/types.ts#L418-L461)).
- Content blocks ([`llm-core/src/types.ts:264-313`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/llm-core/src/types.ts#L264-L313)): `text {text}`, `thinking
  {thinking, thinkingSignature?, redacted?}`, `image {data (base64),
  mimeType}`, `toolCall {id, name, arguments (object)}`.

### Row metadata

`transcript_events.created_at` is epoch ms, taken from the
record's timestamp or `Date.now()`
([`session-accessor.sqlite-transcript-store.ts:173`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-transcript-store.ts#L173)); `seq` orders a session from 0.
`session_windows`: `session_key`, `previous_session_id`, `reason`
(`initial|reset|rollover|fork|rewind|switch|recovery|compaction`), `channel`,
`account_id`, `chat_type`, `model_provider`, `model`, `started_at`,
`ended_at`, `status`, `parent_session_key`, `spawned_by`, `display_name`.
`session_nodes` ([`:16-49`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L16-L49)): `session_key`, `current_session_id`,
`entry_json` (session metadata), `created_via`
(`operator|spawn|channel|cron|...`), `created_actor_type/id`, `label`.

### Permission records

From the 2026-10-19 review; tables unchanged between the two
commits, line numbers at [`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b),
all in `state/openclaw.sqlite`:

- `operator_approvals`, one row per approval request the Gateway raised
  for an `exec` (shell) call, a plugin action or a system agent: `kind`
  (`exec|plugin|system-agent`), `status`
  (`pending|allowed|denied|expired|cancelled`), `decision`
  (`allow-once|allow-always|deny`), `terminal_reason`
  (`user|timeout|malformed-verdict|no-route|run-aborted|gateway-restart|storage-corrupt`),
  `resolver_kind` (`device|channel|runtime|system`: the paired device, the
  chat channel, the runtime's automatic reviewer or the system), `resolver_id`,
  `presentation_json` (what the reviewer was shown),
  `requested_by_device_id`, `source_agent_id`, `source_session_key`,
  `source_session_id`, `source_run_id`, `source_tool_call_id`,
  `source_tool_name`, `created_at_ms`, `resolved_at_ms`, `consumed_at_ms`
  ([`openclaw-state-schema.sql:370-475`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-state-schema.sql#L370-L475)).
  `source_session_id` and `source_tool_call_id` join it to the transcript's
  `toolCall.id`.
- `exec_approvals_config`, the standing exec policy, migrated from the
  legacy `~/.openclaw/exec-approvals.json`
  ([`infra/exec-approvals-config.ts:95-101`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/infra/exec-approvals-config.ts#L95-L101)):
  `raw_json` (the whole file: `defaults` and per-agent `agents.<id>` with
  `security` `deny|allowlist|full`, `ask` `off|on-miss|always`,
  `askFallback`, `autoAllowSkills`, an `allowlist` and `mcpTools` grants,
  and `socket.token`, a credential), plus `default_security`,
  `default_ask`, `default_ask_fallback`, `auto_allow_skills`,
  `allowlist_count`, `updated_at_ms`
  ([`openclaw-state-schema.sql:356-368`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-state-schema.sql#L356-L368);
  [`infra/exec-approvals-core.ts:12-15`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/infra/exec-approvals-core.ts#L12-L15),
  [`:226-234`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/infra/exec-approvals-core.ts#L226-L234)).
  The exec mode `auto` is `allowlist` with `on-miss` and the automatic
  reviewer on ([`:96-115`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/infra/exec-approvals-core.ts#L96-L115)).
- `operator_approval_standing_grants`: an `allow-always` decision on a
  scheduled (cron) job mints a grant, `grant_id`, `minted_by_approval_id`,
  `agent_id`, `cron_job_id`, `operation_binding`, `created_at_ms`,
  `expires_at_ms`, `revoked_at_ms`, `last_used_at_ms`, `use_count`
  ([`:512-529`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-state-schema.sql#L512-L529)).
- `channel_pairing_allow_entries` (`channel_key`, `account_id`, `entry`,
  `updated_at`): the chat senders allowed to talk to the agent per channel
  account ([`:794-801`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-state-schema.sql#L794-L801)).
- `audit_events` carries `tool_call_id`, `tool_name`, `action`, `status`,
  `reason_code` and `actor_type`/`actor_id` per action
  ([`:100-132`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-state-schema.sql#L100-L132));
  its `kind` and `action` values were not enumerated.
- Per session, in `session_nodes.entry_json`: `elevatedLevel`, `execHost`,
  `execNode`, `execCwd`, `toolOverrides` (`mcpServers` on or off,
  `mcpToolsDeny`) and `sendPolicy` (`allow|deny`)
  ([`src/config/sessions/types.ts:481-500`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/types.ts#L481-L500),
  [`:532`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/types.ts#L532)).

### Model override

From the 2026-10-19 review: `session_nodes.entry_json` keeps the
session's chosen model apart from the transcript, `providerOverride`,
`modelOverride`, `modelOverrideSource` (`auto` for a temporary runtime
fallback, `user` for `/model` or `sessions.patch`, `default`), and
`modelOverrideFallbackOriginProvider`/`Model` (the model the user had
picked when a fallback replaced it)
([`src/config/sessions/types.ts:502-516`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/types.ts#L502-L516)).
The assistant message's `responseModel` beside `model` is the resolved id
beside the request, as before
([`packages/llm-core/src/types.ts:535`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/packages/llm-core/src/types.ts#L535)).

## 4. Joins and timestamps

- Session: `transcript_events.session_id = session_windows.session_id`; the
  header `id` equals it. Generations of one conversation share
  `session_key` and chain through `previous_session_id`.
- Session key encodes the origin: `agent:<agentId>:<channel>:<accountId>:direct:<peerId>`,
  `agent:<agentId>:<channel>:<peerKind>:<peerId>`, or `agent:<agentId>:main`-style
  keys ([`routing/session-key.ts:206-261`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/routing/session-key.ts#L206-L261)). This is how a responder ties a
  transcript to a Telegram chat or WhatsApp number.
- Relay (2026-10-19 review, unchanged between the two commits). A session
  carried through a messaging platform is recorded three ways besides its
  key, each naming the platform's copy of the conversation:
  `session_windows` `channel`, `account_id`, `chat_type`
  (`direct|group|channel`), `primary_conversation_id` and
  `hook_external_content_source` (`gmail|webhook`, a session started by a
  Gmail or webhook hook)
  ([`openclaw-agent-schema.sql:140-171`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L140-L171));
  `conversations` (`conversation_id`, `channel`, `account_id`, `kind`,
  `peer_id`, `delivery_target`, `thread_id`, `native_channel_id`,
  `native_direct_user_id`, `label`, `created_at`;
  [`:192-207`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L192-L207)),
  joined to a generation by `session_conversations` (`session_id`,
  `conversation_id`, `role` `primary|participant|related`, `first_seen_at`,
  `last_seen_at`;
  [`:257-267`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L257-L267));
  and `session_nodes.entry_json` `delivery`, `{kind:"none"}`,
  `{kind:"internal"}` or `{kind:"external", route, context, origin}`, whose
  `origin` holds `provider`, `surface`, `chatType`, `from`, `to`,
  `accountId`, `threadId`, `nativeChannelId` and `nativeDirectUserId`
  ([`src/config/sessions/types.ts:60-83`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/types.ts#L60-L83),
  [`:606`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/types.ts#L606)),
  with `session_nodes.created_via` `channel` for a session a channel message
  created ([`openclaw-agent-schema.sql:28`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L28)).
  The channel `webchat` is the Control UI itself, not a platform
  ([`utils/message-channel-constants.ts:3`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/utils/message-channel-constants.ts#L3)).
- Tool call to result: `toolCall.id` in an assistant message equals
  `toolResult.toolCallId` in a later `message` entry.
- Tree: `parentId → id`; `transcript_event_identities` indexes it
  ([`openclaw-agent-schema.sql:684-694`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L684-L694)).
- Subagents: `session_nodes.parent_session_key`/`spawned_by`, and
  `fork_source_session_id`/`fork_source_entry_id` for forks; header
  `parentSession`.
- Project: header `cwd`. No git branch is recorded.
- Times: entry `timestamp` is an ISO 8601 UTC string, message `timestamp` and
  `transcript_events.created_at` are epoch ms ([section 3](#3-record-schema)); how copies
  join the database rows is under
  [Past use and secondary sources](#past-use-and-secondary-sources).

## 5. Other stores

### Audit, ingress and debug logs

Not transcripts but useful: `state/openclaw.sqlite` `audit_events`
([`openclaw-state-schema.sql:149-171`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-state-schema.sql#L149-L171)) and `channel_ingress_events.payload_json`
(raw inbound chat messages, [`:1301-1323`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-state-schema.sql#L1301-L1323)); `logs/raw-stream.jsonl`,
`logs/anthropic-payload.jsonl`, `logs/cache-trace.jsonl` debug traces.

### Other records of past use

From the 2026-10-19 review at
[`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b)
(all present at [`3b16db7`](https://github.com/openclaw/openclaw/commit/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9)
too; none read by the parser):

| Source | Holds | Survives | Joins on | Plan |
| --- | --- | --- | --- | --- |
| `openclaw-agent.sqlite` `session_transcript_fts` (FTS5, the SQLite full-text index; content in its `_content` shadow table) and `session_transcript_fts_rows` ([`openclaw-agent-schema.sql:809-823`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L809-L823)) | user and assistant text with `session_id`, `message_id`, `role`, `timestamp`, the index behind the `sessions_search` tool ([`docs/concepts/session-search.md:10-13`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/concepts/session-search.md#L10-L13)) | rows are deleted explicitly when a generation moves to cold storage ([`session-cold-storage-worker.ts:519-521`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/session-cold-storage-worker.ts#L519-L521)); `session_transcript_fts_rows` has no foreign key to `session_windows`, so whether a session delete removes them was not determined | `session_id`, entry `id` (`message_id`), text, time | secondary |
| `openclaw-agent.sqlite` `session_pending_inputs` ([`:848-864`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L848-L864)) and `session_input_completions` | each accepted prompt as `message_json` with `state` `queued`, `interrupted` or `cancelled` and `accepted_at`, kept "outside the active transcript until its exact turn owns execution" | a cancelled or interrupted prompt never reaches the transcript; the rows cascade away with the session | `session_id`, `session_key`, `consumed_event_id` (the transcript entry once consumed) | primary for rows never consumed, secondary otherwise |
| `openclaw-agent.sqlite` `memory_index_chunks` with `source` `sessions` ([`:658-670`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L658-L670); the two sources are `memory` and `sessions`, [`memory-host-sdk/src/host/types.ts:5`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/packages/memory-host-sdk/src/host/types.ts#L5)) | chunks of transcript text with `path`, line range and `updated_at` | a session delete: "retained deleted-session archives can remain eligible for memory search" until `openclaw memory forget` ([`docs/cli/sessions.md:222-233`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/cli/sessions.md#L222-L233)) | `path` and text; no session id column | secondary; the chunk `path` form was not determined |
| `state/openclaw.sqlite` `channel_ingress_events` ([`openclaw-state-schema.sql:1273-1294`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-state-schema.sql#L1273-L1294)) | each inbound channel message as `payload_json`, with `channel_id`, `account_id`, `status`, `received_at` | pruned by age and count per status (`pending`, `completed`, `failed`), not by session deletion ([`channels/message/ingress-queue.kernel.ts:494-512`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/channels/message/ingress-queue.kernel.ts#L494-L512)) | text and time; the payload shape per channel was not determined | secondary |
| `openclaw-agent.sqlite` `conversation_deliveries` ([`:225-248`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L225-L248)) | each outbound send or turn to a platform conversation: `status`, `platform_message_id`, `reply_text`, `reply_timestamp`, `source_session_key` | cascades with the `conversations` row, not with the session | `source_session_key`, time | secondary |

No prompt-history file exists: not found in openclaw/openclaw at
[`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b)
(grepped `history.jsonl`, `input-history`, `prompt-history` and
`historyFile` in `src/`).

### Sharing and upload state

All in SQLite:

- `session_nodes.entry_json` key `publicShare`, an object
  `{id, sessionId, createdAt}`: `id` 48 lower-case hex characters,
  `sessionId` the transcript generation it publishes, `createdAt` epoch ms
  ([`src/config/sessions/types.ts:627-628`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/types.ts#L627-L628),
  [`src/config/sessions/session-public-share.ts:7-24`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-public-share.ts#L7-L24);
  `entry_json` is the session-metadata column,
  [`src/state/openclaw-agent-schema.sql:16-19`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L16-L19)). It is written when the
  session's creator or a Gateway admin turns on **Public access** in the
  Control UI (the `session.publicShare.set` Gateway method, a fresh random
  `id` and `Date.now()`), and removed when it is turned off
  ([`src/gateway/server-methods/sessions-sharing.ts:351-373`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/gateway/server-methods/sessions-sharing.ts#L351-L373)). The key
  is absent on a session never published, and is dropped when the entry
  moves to a new `sessionId` (a reset or fork) or is incognito
  ([`src/config/sessions/session-accessor.sqlite-entry-store.ts:518-533`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-entry-store.ts#L518-L533)).
  The public URL is `<control UI base>/share/session?token=<opaque>`, served
  by the Gateway itself; the token is an encrypted form of the grant and is
  not stored ([`docs/web/urls.md:223-268`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/web/urls.md#L223-L268)).
- `state/openclaw.sqlite` `backup_runs` (`id`, `created_at` epoch ms,
  `archive_path`, `status` `ok|failed`, `manifest_json`)
  ([`src/state/openclaw-state-schema.sql:1843-1849`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-state-schema.sql#L1843-L1849)): one row per
  `openclaw backup` attempt. `manifest_json` holds `kind`
  (`archive|sqlite-snapshot|git|external`), `target` (the storage location
  name for an offsite archive, the commit sha for a Git backup), `namespace`,
  `error`, `pushFailed`, `bytes`, and for an upload `location {name,
  provider, locationId, key, namespace, plaintextBytes, storedBytes}` and
  `retention {kept, deleted}`
  ([`src/state/backup-run-records.contract.ts:98-124`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/backup-run-records.contract.ts#L98-L124);
  writers [`src/commands/backup.ts:57-70`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/commands/backup.ts#L57-L70),
  [`src/commands/backup-git.ts:140-151`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/commands/backup-git.ts#L140-L151)). The table is pruned to the
  newest 200 rows plus the newest attempt and newest success per target
  ([`src/state/backup-run-records.kernel.ts:22-48`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/backup-run-records.kernel.ts#L22-L48)).
- `state/openclaw.sqlite` `worker_session_placements`, one row per session
  whose turns run on a paired device or a cloud worker: `session_id`,
  `session_key`, `execution_mode` (`worker-turn|remote-exec`), `state`
  (`local` to `failed`), `environment_id`, `remote_workspace_dir`,
  `last_transcript_ack_cursor`, `created_at_ms`, `updated_at_ms`
  ([`src/state/openclaw-state-schema.sql:2142-2170`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-state-schema.sql#L2142-L2170)). The row is
  deleted when the placement is retired
  ([`src/gateway/worker-environments/placement-store.ts:261-279`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/gateway/worker-environments/placement-store.ts#L261-L279)).

### PostgreSQL engine

New since [`3b16db7`](https://github.com/openclaw/openclaw/commit/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9),
which has no PostgreSQL source file; experimental at
[`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b).
`database.engine: "postgres"` in `openclaw.json`, or
`database.families.agent.engine`, moves the agent databases, transcripts
included, to a PostgreSQL server named by `database.postgres.connection`
(a DSN string or a SecretRef)
([`docs/reference/database-engines.md:68-73`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/reference/database-engines.md#L68-L73),
[`:96-116`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/reference/database-engines.md#L96-L116)).
The local `openclaw-agent.sqlite` then is "a small SQLite anchor" holding one
table, `openclaw_engine_anchor (store_id, engine, schema)` with `engine`
`postgres` and `schema` the server namespace
`<schemaPrefix>_<store>_<uuid-prefix>`
([`:591-595`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/reference/database-engines.md#L591-L595);
[`src/infra/database-engine/open.ts:149`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/infra/database-engine/open.ts#L149)).
The transcript is then on the database server, wherever the operator runs
it, and no local file holds it; transcript payloads are plain JSON there,
never zstd. The parser opens the anchor, finds none of its tables and
yields nothing, with no row saying where the store went.

## 6. Format versions

Header `version`: current 4, minimum readable 3; versions 1-2 need doctor
import and may lack `id`/`parentId`; the old `hookMessage` role becomes
`custom` with `customType:"hook"` ([`config/sessions/version.ts:1-4`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/version.ts#L1-L4); [`session-entry-codec.ts:154-179`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-entry-codec.ts#L154-L179)).
Database schema version is in `schema_meta.schema_version`
([`openclaw-agent-schema.sql:6-14`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L6-L14)). Test fixtures for schema v1, v14, v15, v19,
v21 and v22 are in `test/fixtures/sqlite/`.

At [`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b)
(2026-10-19) the agent schema is 31; the history lists 25 to 31 as
unreleased changes to session-writer validation, transcript navigation
columns, the context-engine outbox, index sizes, Brotli-compressed
trajectory payloads and memory-index revisions
([`docs/reference/database-schemas/agent-schema-history.md:43-50`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/docs/reference/database-schemas/agent-schema-history.md#L43-L50)).
`transcript_events` gained `navigation_*` and `message_role` columns but keeps
`session_id`, `seq`, `event_json`, `event_zstd`, `event_utf8_bytes` and
`created_at` with the same zstd rule
([`openclaw-agent-schema.sql:437-482`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/state/openclaw-agent-schema.sql#L437-L482));
the archive tables and `session_windows` keep every column the parser
reads; the header version is still 4
([`config/sessions/version.ts:2`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/version.ts#L2)).
The archive and checkpoint file-name patterns moved, unchanged, to
[`config/sessions/transcript-file-names.ts:12-16`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/config/sessions/transcript-file-names.ts#L12-L16);
the `exec` tool name cited in [section 8](#8-parser-plan) now comes from
[`agents/lazy-exec-tool.ts:63`](https://github.com/openclaw/openclaw/blob/146284a289f98a2cf3babbc55cc3bd16c28e604b/src/agents/lazy-exec-tool.ts#L63),
`core-tool-factory-descriptors.ts` being gone. No other drift changes what the parser reads; the
one change that defeats the parser is the PostgreSQL engine
([PostgreSQL engine](#postgresql-engine)).

## 7. Secrets

In the same database as the transcripts: `auth_profile_store.store_json`,
`auth_profile_state.state_json` and `session_suggestions`
([`state/secret-state-tables.ts:31-35`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/secret-state-tables.ts#L31-L35)); do not emit them. In records:
`thinkingSignature` and `providerReplay.data` are opaque provider state;
`image.data` is base64 media; `toolResult.content` and `bashExecution.output`
are raw tool output and may contain anything the agent read, including
`.env` files.

The key that encrypts public share tokens is derived from the Gateway's
device identity, the `device_identities` row of `state/openclaw.sqlite`
([`src/gateway/control-ui-public-session-token.ts:196-217`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/gateway/control-ui-public-session-token.ts#L196-L217)); whoever
holds that database can mint working share URLs for every `publicShare`
grant. Offsite backup credentials (`accessKeyId`, `secretAccessKey`) and the
encryption passphrase are configured under `storage.locations` in the config
file as SecretRefs (references to a value held in the environment or a
secret store, not the value itself)
([`docs/concepts/storage-locations.md:79-91`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/concepts/storage-locations.md#L79-L91)).

## 8. Parser plan

Selection: `*/agent/openclaw-agent.sqlite` under an `openclaw` artifact
(plus `-wal`); `*/sessions/*.jsonl`, `*.jsonl.reset.*`, `*.jsonl.deleted.*`
(decompress `.zst`), `*.checkpoint.<uuid>.jsonl` and
`*.jsonl.pre-doctor-*-repair-*.bak`. Skip `*.trajectory.jsonl` and
`*.migrated*` (see [Past use and secondary sources](#past-use-and-secondary-sources)). SQL:
`SELECT e.rowid, e.session_id, e.seq,
e.event_json, e.event_zstd, e.created_at, w.model, w.channel, w.session_key
FROM transcript_events e LEFT JOIN session_windows w USING (session_id) ORDER
BY e.session_id, e.seq`. Then archive blobs.

| Column | Source |
| --- | --- |
| timestamp_utc | entry `timestamp`; else `message.timestamp` (ms); else `created_at` (ms) |
| session_id | `session_id` / header `id` |
| project_path | header `cwd` of the session |
| git_branch | empty |
| turn_type | role `user` → user; `assistant` text → assistant, `toolCall` block → tool_use, `thinking` block → thinking; `toolResult` → tool_result; `bashExecution` → tool_use (tool `bash`); other entry types and roles → system |
| model | assistant `responseModel` or `model`; `model_change.modelId` |
| tool_name | `toolCall.name` / `toolResult.toolName` |
| tool_use_id | `toolCall.id` / `toolResult.toolCallId` |
| text | text blocks; `toolCall.arguments.command`/`path`/`url` else JSON; tool result text; `summary` for compaction; `reason` for reset |
| source_line | `transcript_events.rowid`, or the JSONL line number |

Put `session_key` (channel and peer) into the system row for each session.
The shell tool is named `exec` ([`agents/core-tool-factory-descriptors.ts:20`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/agents/core-tool-factory-descriptors.ts#L20)); `api` values include
`anthropic-messages` ([`llm-core/src/types.ts:23`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/llm-core/src/types.ts#L23)).

The proposals below come from the source review of 2026-10-19 at
[`146284a`](https://github.com/openclaw/openclaw/commit/146284a289f98a2cf3babbc55cc3bd16c28e604b).
Every proposal here rests on source alone; [AGENTS.md](../../AGENTS.md#real-install-rounds)
requires a per-step real-install round before the parser changes, and OpenClaw has none.

### Permission state

No transcript entry records a per-call permission
decision; `bashExecution.cancelled` stays on the bash `tool_result` row. The
`exec_approvals_config`, `operator_approvals` and `audit_events` tables of
`state/openclaw.sqlite`
([`collectors/research/openclaw.md`](../../collectors/research/openclaw.md))
hold approvals; their columns were recorded on 2026-10-19
([Permission records](#permission-records)) and the parser does not read them
yet.

Proposed: one `permission decision: <decision or status>
kind=<kind> resolver=<resolver_kind> reason=<terminal_reason>` row per
`operator_approvals` row at `resolved_at_ms` (else `created_at_ms`), with
`session_id` `source_session_id`, `tool_name` `source_tool_name` and
`tool_use_id` `source_tool_call_id`, so it sits beside the call it
governed; one `permission setting: <key>=<value> (from
state/openclaw.sqlite exec_approvals_config, updated_at_ms)` row per
default and per-agent `security`, `ask`, `askFallback`,
`autoAllowSkills` and allowlist entry of `raw_json` (never `socket.token`),
one per `operator_approval_standing_grants` and
`channel_pairing_allow_entries` row, and one per session-level
`elevatedLevel`, `execHost`, `toolOverrides` and `sendPolicy` from
`entry_json`. Not parsed today.

### Model

`system` row `model: <id> provider=<provider>` at the first
model a session names and `model: <old> -> <new> provider=<provider>` on
every later entry whose model differs, with the `model` column set to the
new id. Sources, in order: the `session_windows` `model` and
`model_provider` (the row follows the session-start row, at its time),
`model_change` `modelId` and `provider`, and the assistant `responseModel`,
else `model`, with `provider`; when `responseModel` differs from `model`
the row ends ` requested=<model>`. `responseModel` is the concrete model the
stream reported "when different from the requested `model`"
([`llm-core/src/types.ts:533`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/packages/llm-core/src/types.ts#L533)).
A `model_change` entry naming the model already in force still yields the
plain `model: <id> provider=<provider>` row, since it records a switch;
an assistant message that repeats the current model yields none.

Proposed: one `model: <old> -> <modelOverride>
provider=<providerOverride> source=<modelOverrideSource>` row from
`entry_json` at the node's `updated_at` ([Model override](#model-override)), which records a
`/model` the user typed even when no turn followed. Not parsed today.

### Past use and secondary sources

Every source is parsed on
every run, and a row of a secondary source is dropped when a primary
store's row records the same event (issue 122; see
[Secondary sources in `analyzer/docs/output.md`](../docs/output.md#secondary-sources)).

- Primary: `openclaw-agent.sqlite`, all of it: `transcript_events`, the
  cold archives and every `session_transcript_archives` blob, whether or
  not its `published_at` is set (the time the blob was also written to the
  sessions directory as a file). The schema calls that table the
  "canonical cold-tier owner for reclaimed transcript generations", from
  which "the derived .deleted/.reset file may be recreated"
  ([`openclaw-agent-schema.sql:606-607`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L606-L607)); the file is
  published from the blob's exact bytes, hash-checked
  ([`session-accessor.sqlite-archive-artifact.ts:177-216`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-archive-artifact.ts#L177-L216)).
  `openclaw doctor` (the CLI's repair and migration command) "repairs
  canonical blobs before their reconstructible files", rewriting a
  published file from its row
  ([`state-migrations.transcript-directives-archives.ts:327-379`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/infra/state-migrations.transcript-directives-archives.ts#L327-L379)),
  so the table, not the file, is the store of record. The legacy plain
  `<sessionId>.jsonl` is primary too: before doctor imports it, it is the
  only copy.
- Secondary, the published `.jsonl.reset.*` / `.jsonl.deleted.*` file:
  the same entries as the blob. It survives the database being lost or
  excluded; otherwise the blob outlives it, since retention deletes a
  published row only once its file is gone
  ([`session-history-archive-pruning.worker.ts:105-127`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-history-archive-pruning.worker.ts#L105-L127)).
- Secondary, `<name>.checkpoint.<uuid>.jsonl`: a pre-compaction snapshot,
  a byte copy of the session file taken before compaction
  ([`src/gateway/session-compaction-checkpoints.ts:383-389`](https://github.com/openclaw/openclaw/blob/68145258676f1401a2e42cbaffe6564c2a6213c6/src/gateway/session-compaction-checkpoints.ts#L383-L389) at
  [`6814525`](https://github.com/openclaw/openclaw/commit/68145258676f1401a2e42cbaffe6564c2a6213c6), the parent of the commit that stopped copying,
  [`c59635a`](https://github.com/openclaw/openclaw/commit/c59635ae970cb70171c72fa422b15dc38319414f)). At [`3b16db7`](https://github.com/openclaw/openclaw/commit/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9) no runtime writes new ones; the session store
  keeps only the references
  ([`legacy-compaction-history.ts:3-7`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/legacy-compaction-history.ts#L3-L7)), so the files exist on
  hosts that ran an older release. A checkpoint holds the entries a
  compaction later summarised, which survive in the legacy file or, after
  import, in `transcript_events`; it survives a compaction of the live
  transcript but is a copy of nothing the primary store lost unless that
  store is gone. `<name>` is the session file's name, `<sessionId>` or,
  for a session forked from a checkpoint, `<ts>_<sessionId>`
  ([`session-compaction-checkpoints.ts:320-332`](https://github.com/openclaw/openclaw/blob/68145258676f1401a2e42cbaffe6564c2a6213c6/src/gateway/session-compaction-checkpoints.ts#L320-L332) at [`6814525`](https://github.com/openclaw/openclaw/commit/68145258676f1401a2e42cbaffe6564c2a6213c6)).
- Secondary, `<sessionId>.jsonl.pre-doctor-(branch|openai-codex)-repair-<ts>.bak`:
  a byte copy of a legacy transcript taken before `openclaw doctor`
  rewrote it
  ([`src/commands/doctor-session-transcripts.ts:249-292`](https://github.com/openclaw/openclaw/blob/6559e3f3b94c54e2b1aa06d1fca712c5360455ff/src/commands/doctor-session-transcripts.ts#L249-L292) at
  [`6559e3f`](https://github.com/openclaw/openclaw/commit/6559e3f3b94c54e2b1aa06d1fca712c5360455ff), the parent of [`4273ca9`](https://github.com/openclaw/openclaw/commit/4273ca9dbd9b3e3172f34a7231d41bcd8b5d200c), which removed the file-era
  runtime; the name pattern is still classified at
  [`artifacts.ts:13-14`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/artifacts.ts#L13-L14)). A branch repair keeps only the active
  branch, so the backup also holds the abandoned branches, which no other
  store has, and its rows for them are kept.
- Not read: `<id>.trajectory.jsonl`, the trajectory flight recorder (a
  per-run log of runtime events: prompt submitted, tool call, model
  completed), a different schema marked `openclaw-trajectory`
  ([`docs/tools/trajectory.md:76-102`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/tools/trajectory.md#L76-L102)), not a transcript copy;
  `*.migrated[.N]` ([`artifacts.ts:15`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/artifacts.ts#L15)), for which no writer of a
  session transcript was found at [`3b16db7`](https://github.com/openclaw/openclaw/commit/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9) or [`6559e3f`](https://github.com/openclaw/openclaw/commit/6559e3f3b94c54e2b1aa06d1fca712c5360455ff) (the suffix is
  used there for migrated cron logs, pairing stores and audit logs); and
  `<id>.jsonl.bak.<ts>`, the legacy compact backups
  ([`artifacts.ts:43-50`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/artifacts.ts#L43-L50)), whose content is not recorded.

Joins: the copies are byte copies, so their entries carry the same `id`,
`timestamp` and header `cwd` as the primary store's rows, and the parser
takes the session id of every JSONL file from its header `id` (the name
before the suffix only when there is no header), the id
`transcript_events.session_id` and the archive table carry. An archive
whose session id is over 96 bytes is named `session-<sha256>`
([`session-accessor.sqlite-archive-artifact.ts:24-29`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-archive-artifact.ts#L24-L29)), which the header id
overrides. Every entry row of a copy therefore pairs with its primary
twin at the same time (a 2-second tolerance is not needed but is the
default). The session-start row does not: a copy's names the file
(`archive=<reason>.<ts>` or `copy=<suffix>`) where the database's carries
the `session_windows` and archive columns, so each copy keeps one row
showing it exists.

Covered: the archive blobs and their files, checkpoints and pre-doctor copies. Proposed:
`session_pending_inputs` as a source of
`user` rows (primary for `queued`, `interrupted` or `cancelled` rows with
no `consumed_event_id`, secondary otherwise), and
`session_transcript_fts`, `channel_ingress_events` and
`conversation_deliveries` as secondary sources
([Other records of past use](#other-records-of-past-use)). `memory_index_chunks` waits until
the form of its `path` for a session is known.

### Sync, relay and origin

Sync: OpenClaw keeps no copy of a session on a vendor service. Session
content leaves the Gateway host in three ways, all operator actions; the
first two leave a local record ([Sharing and upload state](#sharing-and-upload-state)).
Both are covered (`session synced: public share`, `backup uploaded:`).

- Public link: `session_nodes.entry_json` `publicShare` marks a session
  whose user messages and final answers anyone with the URL can read,
  served by the Gateway (opt-in per session, off by default,
  [`docs/concepts/multi-user.md:21-36`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/concepts/multi-user.md#L21-L36)). The parser yields one `system`
  row after the generation's session-start row: `session synced: public
  share <publicShare.id> generation <publicShare.sessionId> (from
  openclaw-agent.sqlite session_nodes.entry_json, publicShare.createdAt)`,
  timestamped by `createdAt`, with `session_id` the generation, and sets
  `records_sync`; a grant whose generation has no transcript rows in the
  database still yields its row. Fixture only: no real install has shown
  the key. Turning access off removes the key, and
  deleting the session deletes its `session_nodes` row
  ([`src/config/sessions/session-accessor.sqlite-entry-store.ts:271-274`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/config/sessions/session-accessor.sqlite-entry-store.ts#L271-L274));
  the `.jsonl.deleted.*` archive and its `session_transcript_archives`
  blob keep the transcript but have no column for the grant
  ([`src/state/openclaw-agent-schema.sql:608-624`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/state/openclaw-agent-schema.sql#L608-L624)), so no local
  file says a deleted or unpublished session was ever public.
- Backup upload: `openclaw backup create --to <location>` uploads the whole
  state directory, every agent database included, to a configured storage
  location (a mounted disk, or Cloudflare R2, the Cloudflare object store,
  through a plugin) under `backups/<namespace>/<UTC ts>-<8 hex>.tar.gz`,
  and `openclaw backup git create --push` pushes per-table JSONL dumps to a
  Git remote; both are opt-in and can be scheduled with `openclaw backup
  enable` ([`docs/cli/backup.md:86-96`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/cli/backup.md#L86-L96),
  [`docs/cli/backup.md:318-321`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/cli/backup.md#L318-L321), [`docs/cli/backup.md:364`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/cli/backup.md#L364)).
  The marker is host-wide, not per session: each `backup_runs` row says
  every session in the uploaded databases at `created_at` left the host.
  The parser yields one `system` row per `backup_runs` row with `status`
  `ok` and either a `location` or a Git `target` without `pushFailed`,
  with an empty `session_id`, in the agent's own term rather than
  `session synced:` because it marks no one session: `backup uploaded:
  <kind> to <location.name or archive_path> key <location.key or target>
  namespace <location.namespace or namespace or -> (from
  state/openclaw.sqlite backup_runs, created_at)`, timestamped by
  `created_at`. A Git backup run without `--push` records the same
  manifest as a pushed one, `target` the commit and no `pushFailed`
  ([`src/commands/backup-git.ts:140-151`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/src/commands/backup-git.ts#L140-L151)),
  so a Git row says a commit was made and may have been pushed. Fixture
  only. Deleting a session does not touch `backup_runs`, and the
  uploaded archives keep the session; retention prunes the table
  ([`docs/cli/backup.md:486-499`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/cli/backup.md#L486-L499)).
- Remote execution: a session placed on a paired device or a Crabbox cloud
  worker (a machine OpenClaw rents from AWS, Hetzner or another backend
  for the session) sends its workspace and turn context to that machine
  while the Gateway keeps the canonical transcript
  ([`docs/gateway/cloud-sessions.md:10-20`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/gateway/cloud-sessions.md#L10-L20)). This is execution, not
  a copy kept elsewhere, and no row is proposed; `worker_session_placements`
  names the environment while the placement lives.

Not sync: the daily update check and the opt-in anonymous statistics carry
no prompt or reply text, only a session-creation count
([`docs/gateway/telemetry.md:11-24`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/gateway/telemetry.md#L11-L24)); OpenTelemetry export sends
message text only when `diagnostics.otel.captureContent` is `true`, to the
operator's own collector
([`docs/gateway/opentelemetry/privacy-and-trace-context.md:47-56`](https://github.com/openclaw/openclaw/blob/3b16db73c0b5209aad2ee7c3fb5ddfb12fb208f9/docs/gateway/opentelemetry/privacy-and-trace-context.md#L47-L56)).
Searched `share`, `publicShare`, `sync`, `upload`, `cloud`, `remote`,
`backup`, `telemetry`, `export` and `publish` in `src/` and `docs/`.

Relay: the parser puts `channel`, `account_id` and `chat_type` on the
session-start row but writes no `session relayed:` row and does not set
`records_relay` (the records are under [section 4](#4-joins-and-timestamps)). Proposed: one
`session relayed: <channel> account <account_id>
<chat_type> peer <peer_id> thread <thread_id> (from openclaw-agent.sqlite
conversations, created_at)` row per `session_conversations` link (else
from `session_windows.channel` or `entry_json.delivery.origin`) for any
channel other than `webchat`, and `records_relay` set; a
`hook_external_content_source` of `gmail` is an email relay of the same
kind.

Origin: the agent records none (no session is created on a vendor
server; grepped `origin` and `remote` in `src/config/sessions/`). A
PostgreSQL anchor ([PostgreSQL engine](#postgresql-engine)) should yield
one whole-file row, `parser: agent database is a PostgreSQL anchor
(store <store_id>, schema <schema>): transcripts are on the database
server`, so the gap is visible.

### Scratch directories

The default workspace (`.openclaw/workspace`,
`workspace-<agentId>`), `worktrees/`, Gateway clones under `projects/`
and `sandboxes/` are under the state directory, which the analyzer's
catalog rule already classes as scratch; proposed, a `scratch directory:`
row per `state/openclaw.sqlite` `projects` row whose `source` is `cloned`
and per `worktrees` row, so a state directory moved by
`OPENCLAW_STATE_DIR` is classed too.

### Deletion

Today a deleted archive shows only as an
`archive=deleted.<ts>` session-start row ([What survives a delete](#what-survives-a-delete)).
Proposed: `session deleted: <session_id> (from
openclaw-agent.sqlite session_transcript_archives reason deleted,
created_at)` for each deleted archive, `session archived: <archiveReason>
by <archivedBy>` from `entry_json` at `archivedAt`, and `session
forgotten from memory: <session_id> reason=<reason>` per
`memory_session_tombstones` row.

### Bad lines

Issue 177: a legacy `sessions.json` that cannot be read,
does not decode or is not a JSON object yields one whole-file `system`
row in each transcript beside it, after that transcript's line rows,
with `source_line` 0 and the transcript's `session_id` and `cwd`:
`parser: sessions.json unreadable (<reason>)`, `parser: sessions.json
unparseable (<reason>)` or `parser: sessions.json is not a JSON object`;
the transcript's own rows are still yielded, without the session key.
A line that is valid JSON but not an object (an array, a string, a
number, `null`), in a JSONL file or an archive blob, is its own row like
any other bad line, `parser: unparseable line (not a JSON object):
<line>` (prefixed `archive <name> line <n>: ` inside a blob), and the
lines around it are still yielded.

### Fixtures

JSONL form; the SQLite form stores the same strings in `event_json`:

```json
{"type":"session","version":4,"id":"7d0c2a8e-1111-4000-8000-000000000001","timestamp":"2026-10-01T09:00:00.000Z","cwd":"/home/alice/.openclaw/workspace"}
{"type":"message","id":"a1b2c3d4","parentId":null,"timestamp":"2026-10-01T09:00:01.000Z","message":{"role":"user","content":[{"type":"text","text":"check disk space on the server"}],"timestamp":1759309201000}}
{"type":"message","id":"b2c3d4e5","parentId":"a1b2c3d4","timestamp":"2026-10-01T09:00:04.000Z","message":{"role":"assistant","content":[{"type":"thinking","thinking":"Use exec with df."},{"type":"text","text":"Checking."},{"type":"toolCall","id":"call_01","name":"exec","arguments":{"command":"df -h"}}],"api":"anthropic-messages","provider":"anthropic","model":"claude-sonnet-4-5","usage":{"input":900,"output":40,"cacheRead":0,"cacheWrite":0,"totalTokens":940,"cost":{"input":0,"output":0,"cacheRead":0,"cacheWrite":0,"total":0}},"stopReason":"toolUse","timestamp":1759309204000}}
{"type":"message","id":"c3d4e5f6","parentId":"b2c3d4e5","timestamp":"2026-10-01T09:00:05.000Z","message":{"role":"toolResult","toolCallId":"call_01","toolName":"exec","content":[{"type":"text","text":"/dev/sda1  50G  20G  30G  40% /"}],"isError":false,"timestamp":1759309205000}}
{"type":"model_change","id":"d4e5f6a7","parentId":"c3d4e5f6","timestamp":"2026-10-01T09:01:00.000Z","provider":"openai","modelId":"gpt-5"}
```

### Confidence

High: table and column names, entry and message field names,
compression rule, archive naming, version constants. Medium: that legacy
`.jsonl` files are removed after import on every path; `cwd` meaning the
workspace. Not
determined: the shapes of `trajectory_runtime_events`,
`acp_parent_stream_events` and `custom.data` per `customType`; whether
cold-archived generations keep any `transcript_events` rows.
