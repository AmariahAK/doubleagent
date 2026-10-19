# OpenCode transcript schema

Catalog agent: `opencode`. Researched together with Crush, which began as
an OpenCode fork but no longer shares any storage code
([crush.md](crush.md)); Kilo Code's current store is an OpenCode fork and
shares this schema ([kilo-code.md](kilo-code.md)). Paths cited are relative
to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/opencode.md`](../../collectors/research/opencode.md).

## 1. Source

[sst/opencode](https://github.com/sst/opencode) at [`907b3bc518fa48e90e8ec24dd327d13eee71c36c`](https://github.com/sst/opencode/commit/907b3bc518fa48e90e8ec24dd327d13eee71c36c), MIT. Open
source. The schema has moved out of `packages/opencode` into
`packages/core` (tables) and `packages/schema` (JSON shapes).

Session sharing was checked at this commit on 2026-10-17. On the default
branch at [`797d2af`](https://github.com/sst/opencode/commit/797d2afdbf8f0b4f189748373ff1a69bde9e0ff7)
the `share/` modules are gone and the share and unshare keybindings read
"Deprecated: session sharing was removed"
([`packages/tui/src/config/v1/keybind.ts:101-102`](https://github.com/sst/opencode/blob/797d2afdbf8f0b4f189748373ff1a69bde9e0ff7/packages/tui/src/config/v1/keybind.ts#L101-L102));
no migration in that tree drops `session_share`, so a database created by an
earlier release can still hold the share rows in
[section 5](#5-sqlite-specifics).

- **Source review (2026-10-19)**: the repository has moved to
  [anomalyco/opencode](https://github.com/anomalyco/opencode) (default
  branch `dev`). Reviewed at the `dev` head
  [`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e),
  CLI version 2.0.32
  ([`packages/cli/package.json:4`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/package.json#L4));
  the document previously cited
  [`907b3bc`](https://github.com/sst/opencode/commit/907b3bc518fa48e90e8ec24dd327d13eee71c36c),
  4742 commits behind it. The newest tagged release, v1.19.3 of
  2026-10-16, is 52 commits after `907b3bc` on another branch and keeps
  the `session`, `message` and `part` tables this document describes; the
  2.0 line is published on npm under the `dev` tag only. The sections
  below describe 1.x; the 2.0 changes are in
  [section 6](#6-format-versions). Per class:
  - Permission state: found, not read. Per-call outcomes are in the tool
    part's error text (1.x) or the tool item's `error.type` (2.0), and
    standing "always" grants in the `permission` table, which existed at
    `907b3bc` too ([section 5](#5-sqlite-specifics)).
  - Model: covered (`model:` rows). 2.0 adds `previous` to
    `model-switched` and a `variant` the parser does not show; no alias
    beside a resolved id.
  - Past use beyond the primary store: found, none read.
    `prompt-history.jsonl`, `prompt-stash.jsonl`, `session.json`, the
    legacy V1 tables that survive a 2.0 delete, `opencode-next.db`, the
    full tool outputs and the desktop app's `drafts.sqlite`
    ([section 2](#2-transcript-stores)).
  - Sync, relay and origin: covered for 1.x shares; none at `dev`, where
    sharing is removed and the CLI keeps no event payloads, so the
    event-based share rows can no longer appear. A session imported from
    a URL keeps no mark of its origin
    ([section 8](#8-parser-plan)).
  - Scratch directories: found, the temp root `<os.tmpdir()>/opencode`
    and the agent's worktrees ([section 6](#6-format-versions)).
  - Deletion: found; 2.0 deletes the `session_v2` row and its messages
    but not the legacy V1 rows of a migrated session; archiving sets
    `time_archived`, which the parser does not show.
  - Version drift: found, and a parser bug once 2.0 ships: sessions move
    to `session_v2`, a new database has no `session`, `message`, `part`
    or `session_share` table, and the parser reads session headers and
    project paths only from `session`.
  - Bad lines: found; the parser counts undecodable database records,
    part files and events into one summary row instead of one row per
    record.

## 2. Transcript stores

One SQLite file for all projects: `~/.local/share/opencode/opencode.db`
([`packages/core/src/global.ts:3`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L3),[`11`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L11) uses `xdg-basedir` with no platform
branching, so the same path on macOS and Windows;
[`packages/core/src/database/database.ts:49-54`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L49-L54)). Non-release channels use
`opencode-<channel>.db` in the same directory ([`database.ts:54`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L54));
`OPENCODE_DB` can relocate it ([`:43-47`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L43-L47)). One `message` row per message, one
`part` row per content part. A legacy JSON tree
`~/.local/share/opencode/storage/` ([`packages/opencode/src/storage/storage.ts:224`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L224))
still exists ([section 6](#6-format-versions)).

Other records of use, from the source review of 2026-10-19 (`dev` at
[`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e);
the three TUI files are at the same paths at `907b3bc`, for example
[`packages/tui/src/prompt/history.tsx:53`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/tui/src/prompt/history.tsx#L53)).
None is read by the parser today.

| Source | Holds | Survives | Joins on | Plan |
| --- | --- | --- | --- | --- |
| `~/.local/state/opencode/prompt-history.jsonl` ([`packages/tui/src/prompt/history.tsx:20-23`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L20-L23), [`:60-75`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L60-L75), [`:93-100`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L93-L100), [`:139`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L139)) | the last 50 TUI prompts, `{text, files, agents, skills, pasted, mode?}`; no session id, project or time | session delete, project removal; trimmed to 50 and rewritten at each start, dropping lines that do not parse | text only | secondary, empty `timestamp_utc` |
| `~/.local/state/opencode/prompt-stash.jsonl` ([`packages/tui/src/prompt/stash.tsx:9-14`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/stash.tsx#L9-L14), [`:40`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/stash.tsx#L40)) | up to 50 prompts set aside unsent, `{prompt, timestamp}` (epoch ms) | everything; a stashed prompt may never reach a transcript | none (text and time when it was later sent) | primary for what it holds (unsent prompts), `system` rows |
| `~/.local/state/opencode/session.json` ([`packages/tui/src/context/local.tsx:517-530`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/context/local.tsx#L517-L530)) | `pinned`, ids of sessions the user pinned | session delete (the id stays until the user unpins it) | session id | secondary: a pinned id with no session left is a trace of a deleted session |
| Legacy `session`, `message`, `part` tables in a database migrated to 2.0 ([section 6](#6-format-versions)) | the 1.x transcript, copied into `session_message` by the migration | deletion of the session in 2.0, which removes only the `session_v2` row and what cascades from it | session id, message id (the copy keeps the V1 ids, [`v1-migration.bun.ts:353`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L353), [`:404`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L404)) | secondary once the parser reads `session_message` for migrated sessions; today it reads them as primary |
| `~/.local/share/opencode/opencode-next.db` ([`packages/core/src/database/v1-migration.bun.ts:702-706`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L702-L706), [`:846`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L846)) | a pre-release 2.0 database (`project`, `session`, `session_message`), imported read-only and left in place | everything after the import | session id | secondary; the parser's database pattern already reads it as a channel database, so its sessions appear twice today |
| `~/.local/share/opencode/tool-output/tool_<id>` ([`packages/core/src/tool-output.ts:13-18`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/tool-output.ts#L13-L18), [`:86-90`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/tool-output.ts#L86-L90)) | full text of a tool result the transcript cut, kept seven days | session delete within the seven days | the path in the transcript marker `full output saved to <file>` | secondary; not collected (catalog exclusion) |
| desktop app `drafts.sqlite` in `<appData>/ai.opencode.desktop*` ([`packages/desktop/src/main/storage/schema.ts:3-29`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/desktop/src/main/storage/schema.ts#L3-L29)) | prompt drafts and history, `document(key, value)` | not determined | not determined | not collected; needs a real-install round |

The 2.0 runtime keeps no other mirror: the `event` table holds payloads
only on the hosted (workerd) server, never in the CLI
([section 5](#5-sqlite-specifics)).

## 3. Record schema

Drizzle tables in [`packages/core/src/session/sql.ts`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts).

`session` ([`:22-66`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L22-L66)): `id` (`ses_...`), `project_id` → `project.id`,
`workspace_id`, `parent_id`, `slug`, `directory` (cwd, stored with `/` on
Windows, [`database/path.ts:5-8`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/path.ts#L5-L8)), `path`, `title`, `version` (OpenCode
version), `share_url`, `summary_*`, `metadata` JSON, `cost`, `tokens_*`,
`revert` JSON, `permission` JSON, `agent`, `model` JSON `{id, providerID,
variant?}` ([`:52-56`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L52-L56)), `time_created`, `time_updated` (epoch milliseconds,
[`database/schema.sql.ts:3-10`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/schema.sql.ts#L3-L10) uses `Date.now()`), `time_compacting`,
`time_archived`.

`project` ([`project/sql.ts:6-18`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/project/sql.ts#L6-L18)): `id`, `worktree` (absolute repository
root), `vcs`, `name`, `time_*`, `sandboxes` JSON array.

`message` ([`sql.ts:68-80`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L68-L80); CREATE in
[`database/migration/20260127222353_familiar_lady_ursula.ts:22-31`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L22-L31)): `id`
(`msg_...`), `session_id`, `time_created`, `time_updated` (ms), `data` JSON =
the V1 message minus `id` and `sessionID` ([`session/projector.ts:77-82`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L77-L82)).
`data` ([`packages/schema/src/v1/session.ts`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts)): user ([`:332-354`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L332-L354))
`role:"user"`, `time.created` (ms), `agent`, `model:{providerID, modelID,
variant?}`, `format?`, `summary?`, `system?`, `tools?`; assistant
([`:453-485`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L453-L485)) `role:"assistant"`, `time.{created, completed?}`, `parentID`
(the user message), `modelID`, `providerID`, `mode`, `agent`, `path.{cwd,
root}`, `cost`, `tokens.{input, output, reasoning, cache.{read, write}}`,
`error?` (`{name, data}`), `finish?`, `variant?`.

`part` ([`sql.ts:82-98`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L82-L98); CREATE [`...ursula.ts:33-42`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L33-L42)): `id` (`prt_...`),
`message_id`, `session_id`, `time_created`, `time_updated`, `data` JSON = the
part minus `id`, `messageID` and `sessionID` ([`projector.ts:84-87`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L84-L87)).
`data.type` discriminator ([`v1/session.ts:357-370`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L357-L370)): `text` ([`:102-115`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L102-L115):
`text`, `synthetic?`, `ignored?`, `time.{start,end?}`); `reasoning`
([`:118-127`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L118-L127): `text`, `time.{start,end?}`); `tool` ([`:315-322`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L315-L322): `callID`,
`tool` (name), `state.status` in `pending|running|completed|error`
([`:259-302`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L259-L302)), `state.input` on all, `completed` adds `output`, `title`,
`metadata`, `time.{start,end}`, `error` adds `error`, `time.{start,end}`);
the tool call and its result are the same part, mutated in place;
`step-start` ([`:233-237`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L233-L237), `snapshot?`), `step-finish` ([`:240-256`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L240-L256), `reason`,
`cost`, `tokens`), `subtask` ([`:204-217`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L204-L217), `prompt`, `description`, `agent`),
`compaction` ([`:195-201`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L195-L201)), `snapshot`, `patch`, `file`, `agent`, `retry`.

Newer V2 projection in the same database: `session_message`
([`sql.ts:119-138`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L119-L138)): `id`, `session_id`, `type` in
`agent-switched|model-switched|user|synthetic|system|shell|assistant|compaction`
([`packages/schema/src/session-message.ts:200-213`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L200-L213)), `seq`, `time_created`
(ms, [`projector.ts:203`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L203)), `data` JSON. Assistant `data`
([`session-message.ts:165-189`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L165-L189)): `agent`, `model.{id, providerID}`,
`content[]` with `type` in `text|reasoning|tool` ([`:122-157`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L122-L157)); tool items
carry `id`, `name`, `state.status`, `state.input`, `state.content[]`
(`{type:"text",text}`), `state.error.message`, `time.{created, ran?,
completed?}`. User `data`: `text`, `files?`, `agents?` ([`:44-51`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L44-L51)). Migration
[`20260622170816_reset_v2_session_state.ts:8-14`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260622170816_reset_v2_session_state.ts#L8-L14) wipes `session_message`,
`session_input` and `event` on upgrade, so `message`/`part` are the durable
transcript; treat `session_message` as supplementary. The two switch records carry the common base `id`, `metadata?` and `time.created` ([`session-message.ts:24-28`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L24-L28)) plus `agent` (a string) for `agent-switched` ([`:30-35`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L30-L35)) and `model` for `model-switched` ([`:37-42`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L37-L42)), a `Model.Ref` `{id, providerID, variant?}` ([`packages/schema/src/model.ts:13-18`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/model.ts#L13-L18)). The projector stores `id` and `type` in their own columns and the rest of the record in `data` ([`packages/core/src/session/projector.ts:192-208`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L192-L208)), so `data` is `{time, agent}` or `{time, model}`.

`event` ([`core/src/event/sql.ts:10-25`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/event/sql.ts#L10-L25)): `aggregate_id` = session id, `seq`,
`type` such as `message.updated.1` and `message.part.updated.1`
([`schema/src/event.ts:94-96`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/event.ts#L94-L96)), `data` JSON with full message or part copies
([`core/src/event.ts:336-348`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/event.ts#L336-L348)). Also wiped by the reset migration.

Git branch is not recorded anywhere. Role: `message.data.role`. Project
path: `project.worktree`; cwd: `session.directory` or assistant
`data.path.cwd`.

## 4. Joins

`session.project_id → project.id` (worktree); `message.session_id →
session.id`; `part.message_id → message.id` (`part.session_id` is
denormalised). Order parts by `part.id` (ids are time-ordered,
[`v1/session.ts:17-27`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L17-L27)) or `time_created`. Tool call and result are one `part`
row; assistant → user through `data.parentID`. `session_message` joins on
`session_id`, ordered by `seq`.

## 5. SQLite specifics

`journal_mode=WAL` ([`database.ts:27`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L27), also at open [`sqlite.bun.ts:164`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/sqlite.bun.ts#L164));
`wal_checkpoint(PASSIVE)` runs at startup only ([`database.ts:32`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L32)). Rows
written since the last checkpoint live only in `opencode.db-wal`, so a copy
without the sidecar loses recent messages. No encryption or compression.

Share records. A session published to OpenCode's web share service (the
`/share` command, [section 8](#8-parser-plan)) has one `session_share` row
([`packages/core/src/share/sql.ts:5-13`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/share/sql.ts#L5-L13); CREATE in
[`...ursula.ts:89-97`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L89-L97)):
`session_id` (primary key, references `session.id` with `ON DELETE
CASCADE`), `id` (the share id; the hosted service makes it the last eight
characters of the session id,
[`packages/enterprise/src/core/share.ts:117-122`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/enterprise/src/core/share.ts#L117-L122)),
`secret` (a random UUID the service returns and the client sends back with
every sync and delete, so a credential for the public copy), `url` (the
public page) and `time_created`, `time_updated` (epoch ms,
[`database/schema.sql.ts:3-10`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/schema.sql.ts#L3-L10)).
`ShareNext.create` writes it once the service has answered the create
request, as an upsert when the session is shared again
([`packages/opencode/src/share/share-next.ts:310-336`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L310-L336)), and
`ShareNext.remove` deletes it after the service accepts the delete
([`:338-359`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L338-L359)).
The same URL goes into `session.share_url`
([`packages/opencode/src/share/session.ts:26-32`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/session.ts#L26-L32),
[`packages/opencode/src/session/session.ts:810-812`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/session.ts#L810-L812),
[`core/src/session/projector.ts:56`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L56)),
which `/unshare` sets back to NULL
([`share/session.ts:34-37`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/session.ts#L34-L37)).
Each of these changes is also a durable `session.updated.1` event
([`schema/src/v1/session.ts:502-506`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L502-L506),
[`:580-587`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L580-L587);
[`core/src/event.ts:336-347`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/event.ts#L336-L347))
whose `data.info.share.url` holds the URL and `data.info.time.updated` the
time of the change
([`session/session.ts:734-746`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/session.ts#L734-L746)),
so the `event` table still holds the URL after an unshare. A session never
shared has no `session_share` row, a NULL `share_url` and no `share` key in
its events. Deleting a session removes its `session` row, its
`session_share` row with it, and its `event` rows
([`session/session.ts:606-623`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/session.ts#L606-L623),
[`projector.ts:257-259`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L257-L259),
[`event.ts:514-521`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/event.ts#L514-L521)); the upgrade
migration
[`20260622170816_reset_v2_session_state.ts:11`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260622170816_reset_v2_session_state.ts#L11)
emptied `event` once.

Permission records (source review of 2026-10-19). OpenCode asks before a
tool call when the rules say `ask`; the user answers `once`, `always` or
`reject` (`Permission.Reply`,
[`packages/schema/src/permission.ts:42-54`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/permission.ts#L42-L54)).
The `permission.asked` and `permission.replied` events are ephemeral, so
the answer itself is never stored; what lands on disk is:

- Standing grants. The `permission` table, `id` (`per_...`), `project_id`
  (references `project.id`, `ON DELETE CASCADE`), `action` (the tool's
  permission name), `resource` (the pattern granted) and `time_created`,
  `time_updated` (epoch ms), one row per pattern of an `always` reply
  ([`packages/core/src/permission/sql.ts:7-20`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/permission/sql.ts#L7-L20);
  [`packages/core/src/permission.ts:299-306`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/permission.ts#L299-L306)).
  Saved rows are applied as `allow` rules for every later session of the
  project ([`:147-156`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/permission.ts#L147-L156)).
  The table exists at `907b3bc` with the same columns
  ([`packages/core/src/permission/sql.ts:7-19`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/permission/sql.ts#L7-L19)),
  but the 1.x CLI there keeps `always` answers in memory only
  ([`packages/opencode/src/permission/index.ts:143-150`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/permission/index.ts#L143-L150)),
  so on a 1.x install the table is written only by the 2.0 runtime it
  bundles. An older shape, `permission(project_id, data)`, was created by
  the first migration and dropped by
  [`20260601202201_amazing_prowler.ts:8`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260601202201_amazing_prowler.ts#L8)
  ([`20260127222353_familiar_lady_ursula.ts:44-51`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L44-L51)).
- The session's rule list. `session.permission` (`session_v2.permission`
  in 2.0) is a `Permission.Ruleset`, a JSON array of `{action, resource,
  effect}` with `effect` in `allow|deny|ask`
  ([`packages/schema/src/permission.ts:56-67`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/permission.ts#L56-L67)),
  set at creation and by the durable `session.permissions` event
  ([`packages/schema/src/session-event.ts:121-129`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-event.ts#L121-L129);
  [`packages/core/src/session/projector.ts:593-596`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L593-L596)).
  The 2.0 upgrade copies 1.x sessions with `permission` NULL
  ([`packages/core/src/database/v1-migration.bun.ts:611-628`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L611-L628))
  and a later migration clears the column for every session
  ([`20260910120000_clear_v1_session_permission.ts:8`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260910120000_clear_v1_session_permission.ts#L8)),
  so it holds only rules set after that. The configured rules are the
  config's `permissions` list and each agent's
  ([`packages/schema/src/config.ts:55`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/config.ts#L55),
  [`packages/schema/src/config/agent.ts:21`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/config/agent.ts#L21)).
- Per-call outcomes, in the transcript. In 1.x a refused call is a tool
  part with `state.status` `error` and `state.error` the refusal's text
  ([`packages/opencode/src/session/processor.ts:185-203`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/processor.ts#L185-L203)):
  "The user rejected permission to use this specific tool call.", the
  same followed by "with the following feedback: " and the user's text, or "The user
  has specified a rule which prevents you from using this specific tool
  call. ..." for a `deny` rule
  ([`packages/core/src/v1/permission.ts:7-25`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/v1/permission.ts#L7-L25)).
  In 2.0 the assistant's tool item gets `state.status` `error` with
  `error.type` `aborted` and message "The user declined this tool call"
  for a plain rejection
  ([`packages/core/src/session/runner/step.ts:207-215`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/runner/step.ts#L207-L215)),
  and `error.type` `permission.rejected` for a `deny` rule or a rejection
  with feedback
  ([`packages/core/src/session/to-session-error.ts:61-62`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/to-session-error.ts#L61-L62)).
  An approval leaves no per-call record in either version.

Events and deletion in 2.0. The `event` table keeps payloads only when
the bus is configured to persist them, which the hosted (workerd) server
does and the CLI does not
([`packages/core/src/bus.ts:178-179`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L178-L179),
[`:203`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L203),
[`:908`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L908);
[`packages/server/src/workerd.ts:64-69`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/server/src/workerd.ts#L64-L69)),
and the 2.0 upgrade deletes every existing `event` row
([`v1-migration.bun.ts:549-566`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L549-L566)).
Deleting a session publishes the durable `session.deleted` and removes
the session's events and sequence
([`packages/core/src/session.ts:378-388`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session.ts#L378-L388);
[`packages/core/src/bus.ts:702-714`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L702-L714));
the projector deletes the `session_v2` row
([`projector.ts:552-554`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L552-L554)),
which cascades to `session_message`, `session_pending`, `session_inbox`
and the instruction tables
([`packages/core/src/session/sql.ts:79-160`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/sql.ts#L79-L160)),
child sessions first. Nothing deletes the legacy `session`, `message` and
`part` rows the upgrade copied from, and no record of the deletion is
left. Archiving sets `time_archived` and unarchiving clears it
([`projector.ts:615-627`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L615-L627)).

## 6. Format versions

Legacy JSON under `~/.local/share/opencode/storage/`, one file per key:
`project/<projectID>.json` (`{id, vcs, worktree, time}`),
`session/<projectID>/<sessionID>.json`, `message/<sessionID>/<msgID>.json`,
`part/<msgID>/<partID>.json`, `session_diff/<sessionID>.json`, marker
`storage/migration` (integer) ([`storage.ts:63-65`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L63-L65),[`81-211`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L81-L211),[`224-225`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L224-L225)). Before
that, per-project `~/.local/share/opencode/project/<slug>/storage/session/{info,message,part}/...`
([`storage.ts:97`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L97),[`139`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L139),[`150`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L150),[`165`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L165); [`packages/web/src/content/docs/troubleshooting.mdx:35-36`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/web/src/content/docs/troubleshooting.mdx#L35-L36)).
JSON records carry `id`, `sessionID` and `messageID` inline (the database
`data` column strips them). The SQLite `migration` table
([`database/migration.ts:30`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration.ts#L30)) lists applied schema migrations;
`data_migration` tracks data moves. At this commit no code imports
`storage/` JSON into SQLite; `storage/` is still written for `session_diff`
([`session/revert.ts:77`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/revert.ts#L77)), so both trees coexist. `opencode import`
([`cli/cmd/import.ts:196-225`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/import.ts#L196-L225)) loads exported JSON into `message`/`part`.

OpenCode 2.0 (the `dev` branch at
[`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e),
source review of 2026-10-19; not in a tagged release yet). The code moved
to `packages/core`, `packages/cli`, `packages/tui` and `packages/util`;
the database is still `opencode.db` (or `opencode-<channel>.db`) under the
same XDG data directory
([`packages/cli/src/database-path.ts:4-13`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/database-path.ts#L4-L13)).
What changes for the parser:

- Sessions live in `session_v2`, same columns as `session` plus
  `fork_session_id`, `fork_boundary`, `time_idle`, `time_viewed`,
  `idle_outcome`, `resume_attempts`
  ([`packages/core/src/session/sql.ts:22-68`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/sql.ts#L22-L68)).
  A database created by 2.0 is bootstrapped from the current schema
  ([`packages/core/src/database/migration.ts:26-36`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration.ts#L26-L36);
  [`schema.gen.ts:184`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/schema.gen.ts#L184)),
  which has no `session`, `message`, `part`, `session_share` or `todo`
  table. A database upgraded from 1.x gets `session_v2` beside the old
  tables and the upgrade copies each 1.x session into it and its
  `message`/`part` rows into `session_message`, leaving the old rows in
  place ([`packages/core/src/database/migration/20260804233008_loose_psylocke.ts:90`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260804233008_loose_psylocke.ts#L90),
  [`:139-140`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260804233008_loose_psylocke.ts#L139-L140);
  [`v1-migration.bun.ts:534-700`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L534-L700)).
  A database from a pre-release 2.0 build has its `session` renamed to
  `session_v2` ([`loose_psylocke.ts:13-38`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260804233008_loose_psylocke.ts#L13-L38)).
- `session_message` is the only transcript for new sessions. Its `type`
  adds `location-switched` (`location.{directory, workspaceID}`,
  `projectID`, `subpath`, `previous`), `skill` (`skill`, `name`, `text`)
  and `idle` (`outcome` in `succeeded|failed|interrupted`, `error`) to the
  types in [section 3](#3-record-schema); `agent-switched` and
  `model-switched` gain `previous`; `shell` is now `shellID`, `command`,
  `status` (`running|exited|timeout|killed`), `exit` and `output`, an
  object `{output, cursor, size, truncated}`; tool items gain `executed`
  and the `streaming` status; assistant gains `snapshot`, `finish`,
  `retry`, `time.streamed`
  ([`packages/schema/src/session-message.ts:45-125`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-message.ts#L45-L125),
  [`:213-237`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-message.ts#L213-L237),
  [`:290-309`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-message.ts#L290-L309);
  [`packages/schema/src/shell.ts:25`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/shell.ts#L25),
  [`:77-84`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/shell.ts#L77-L84)).
  Model and agent changes are also projected onto `session_v2.model` and
  `agent` ([`projector.ts:555-571`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L555-L571)).
- Session sharing is removed ([`packages/tui/src/config/keybind.ts:125-127`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/config/keybind.ts#L125-L127));
  `session_v2.share_url` remains as a column and is copied from 1.x
  sessions.
- New tables: `permission` ([section 5](#5-sqlite-specifics)), `worktree`
  (`project_id`, `directory`, `strategy`, `time_created`, one row per
  worktree OpenCode made under
  `~/.local/share/opencode/worktree/<first six characters of the project
  id>/`;
  [`packages/core/src/worktree/sql.ts:6-20`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/worktree/sql.ts#L6-L20),
  [`packages/core/src/worktree/strategies.ts:51`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/worktree/strategies.ts#L51)),
  `kv`, `session_pending`, `session_inbox`, `instruction_*`, and
  `project.time_archived`.
- Scratch directories. 2.0 creates `<os.tmpdir()>/opencode` and tells the
  model to prefer it to `/tmp`, "pre-created and approved for external
  access"
  ([`packages/util/src/global-roots.ts:17`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/util/src/global-roots.ts#L17),
  [`packages/core/src/instructions/builtins.ts:43`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/instructions/builtins.ts#L43)).
  It is outside the home on Linux and macOS and so never collected. The
  instruction is about where the model writes temporary files, so the
  path shows in tool inputs; whether a session's `directory` can be it
  was not determined. A session working in an
  OpenCode worktree has its `directory` under the data directory, which
  the analyzer's catalog rule already lists as a scratch directory.
- A session imported with `opencode session import <file or URL>` is
  written as a new session with the local version and the import time as
  `time_updated`, and no field records where it came from
  ([`packages/cli/src/commands/handlers/session/import.ts:15-22`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/commands/handlers/session/import.ts#L15-L22);
  [`packages/core/src/session/transfer.ts:64-126`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/transfer.ts#L64-L126)).

## 7. Secrets

`credential.value` JSON (`{type:"oauth", access, refresh}` or `{type:"key",
key}`, [`schema/src/credential.ts:16-34`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/credential.ts#L16-L34)), `account.access_token` and
`refresh_token`, `control_account.*`, `session_share.secret` (the share
service's per-share secret that authorises sync to and deletion of the
public copy, [section 5](#5-sqlite-specifics)), plus the legacy
files `~/.local/share/opencode/auth.json` ([`auth/index.ts:10`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L10),[`14-35`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L14-L35)) and
`mcp-auth.json`. Tool `input` and `output` text can contain pasted tokens.

## 8. Parser plan

Globs: `.local/share/opencode/opencode*.db{,-wal,-shm}`,
`.local/share/opencode/storage/{session,message,part,project}/**/*.json`,
`.local/share/opencode/project/*/storage/session/**/*.json`.

Rows: one per `part`, plus a `user` row per user message.

| Column | Source |
| --- | --- |
| timestamp_utc | part `data.time.start`, else `part.time_created` (ms) |
| session_id | `session.id` |
| project_path | `project.worktree`, fallback `session.directory` |
| git_branch | empty |
| turn_type | user message → user; `text` → assistant; `reasoning` → thinking; `tool` pending/running → tool_use; `tool` completed/error → tool_use plus tool_result; `step-*` → system |
| model | `data.providerID/modelID` |
| tool_name, tool_use_id | `data.tool`, `data.callID` |
| text | text, input JSON, output or error |

Model and mode rows. A `system` row `model: <modelID> provider=<providerID>`
precedes the first message of a session that names a model (V1 user
`model.{providerID, modelID}`, V1 assistant `providerID` and `modelID`, V2
assistant `model.{id, providerID}`), and `model: <old> -> <new>
provider=<providerID>` precedes every later message, or stands for every V2
`model-switched` record, whose model differs. The message's `agent` (V1 user
and assistant, V2 assistant, V2 `agent-switched` `agent`) is tracked the
same way as `permission mode: agent=<name>` and `permission mode:
agent=<old> -> agent=<new>`, because an agent (`build`, `plan` or a custom
one) is a mode that carries its own permission ruleset (the agent's `permission: PermissionV1.Ruleset`, [`packages/opencode/src/agent/agent.ts:44`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/agent/agent.ts#L44)). Both rows take the
message's timestamp. The session's `permission` JSON and the project's
`sandboxes` array are named in [section 3](#3-record-schema) without their
shape, so the parser does not read them (issue 98); the research records
no per-call approval or denial, and whether a denied call shows as a tool
`state.status` of `error` is not researched.

Sync: OpenCode uploads a session only when it is shared. Sharing starts
from `/share` in the TUI, which asks once and remembers the answer as
`share_consent` in `~/.local/state/opencode/kv.json`
([`packages/tui/src/routes/session/index.tsx:465-497`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/tui/src/routes/session/index.tsx#L465-L497),
[`packages/tui/src/context/kv.tsx:15`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/tui/src/context/kv.tsx#L15)),
from `opencode run --share`
([`packages/opencode/src/cli/cmd/run.ts:161-164`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/run.ts#L161-L164),
[`:535-547`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/run.ts#L535-L547)), or
for every new top-level session when the config sets `share: "auto"` (or
the deprecated `autoshare: true`) or `OPENCODE_AUTO_SHARE` is set
([`packages/core/src/v1/config/config.ts:57-63`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/v1/config/config.ts#L57-L63),
[`config/config.ts:589-591`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L589-L591),
[`effect/runtime-flags.ts:17`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/effect/runtime-flags.ts#L17),
[`share/session.ts:39-46`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/session.ts#L39-L46)).
With `share` unset sharing is manual; `share: "disabled"` or
`OPENCODE_DISABLE_SHARE` blocks it
([`share/session.ts:28`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/session.ts#L28),
[`share-next.ts:23`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L23)).
Once shared, a full copy and then every session, message, part, diff and
model update is posted with the share secret to `<base>/api/share/<id>/sync`
([`share-next.ts:179-199`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L179-L199),
[`:247-299`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L247-L299)),
where the base is `https://opncd.ai` or the config's `enterprise.url`, or,
for a user signed in to an OpenCode console account with an active
organisation (the `account` table), the account's URL under `/api/shares`
with its bearer token and an `x-org-id` header
([`:206-222`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L206-L222)).
OpenCode Zen, OpenCode's hosted model gateway, is a model provider, so its
calls are model API calls and not sync; trace and log export over OTLP
(OpenTelemetry's wire protocol) goes only to an endpoint the user sets in
`OTEL_EXPORTER_OTLP_ENDPOINT`
([`core/src/flag/flag.ts:16-17`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/flag/flag.ts#L16-L17)).
The parser yields one `system` row per `session_share` row,
`session synced: share <id> url <url> (from opencode.db session_share,
time_created)`, timestamped by `time_created`, never with `secret`; for a
session with no `session_share` row whose `session.updated.1` events carry
`info.share.url`, `session synced: share url <url> (from opencode.db event
session.updated.1, info.time.updated)` at that event's `info.time.updated`,
and `session unshared (from opencode.db event session.updated.1,
info.time.updated)` at the first later event without `share`; the
database name in the text is the file's own (`opencode-<channel>.db` for
a channel database). These rows are fixture only: no real install has
shown a `session_share` row or a shared session's events. Deleting a
session through OpenCode removes the `session`, `session_share` and `event`
rows ([section 5](#5-sqlite-specifics)), and ShareNext's `session.deleted`
subscriber asks the service to delete the public copy
([`share-next.ts:200`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L200));
whether that request still finds the share row before the cascade removes
it is not determined from source, and no local file records that the remote
copy was deleted. What survives is the log: `creating share` and `removing
share` lines with the `sessionID` go to
`~/.local/share/opencode/log/opencode.log` at the default INFO level
([`share-next.ts:312`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L312),
[`:340`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L340);
[`core/src/observability/logging.ts:49-52`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/observability/logging.ts#L49-L52),
[`:59-65`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/observability/logging.ts#L59-L65);
[`core/src/global.ts:23`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L23)).
Separately, a session can be moved to a workspace (the control plane's
`workspace` table) served by another OpenCode instance
(`Workspace.sessionWarp`,
[`control-plane/workspace.ts:559`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/control-plane/workspace.ts#L559)),
recorded as `session.workspace_id` and a `workspace` row
([`core/src/control-plane/workspace.sql.ts:6-18`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/control-plane/workspace.sql.ts#L6-L18));
the one built-in adapter targets a local worktree
([`control-plane/adapters/worktree.ts:92`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/control-plane/adapters/worktree.ts#L92)),
so a remote target comes from a plugin, and none was researched.

Plan by requirement class, from the source review of 2026-10-19 (detail
in [section 2](#2-transcript-stores), [section 5](#5-sqlite-specifics)
and [section 6](#6-format-versions)):

- Permission: per call, a tool result whose 1.x `state.error` starts "The
  user rejected permission" or "The user has specified a rule which
  prevents you", or whose 2.0 `error.type` is `permission.rejected` or is
  `aborted` with "The user declined this tool call", gets `permission
  decision: rejected` (with ` feedback` or ` rule` as the text shows)
  after its `tool_result` row, joined on `tool_use_id`; no approval is
  recorded. Standing: one `permission setting: <action> <resource>=allow
  (from <database> permission, time_created)` row per `permission` table
  row at its `time_created`, `project_path` the project's `worktree`;
  and the session's `permission` rule list as `permission setting:
  session <action> <resource>=<effect>` rows at the session's
  `time_updated`. Not read today.
- Model: covered; add the 2.0 `variant` beside `provider=` when present.
  No alias beside a resolved id exists.
- Past use: `prompt-history.jsonl` (secondary, empty `timestamp_utc`, text
  match), `prompt-stash.jsonl` (primary for unsent prompts, `system`
  rows at `timestamp`), `session.json` (`system` row per pinned id that
  has no session, at the file's modification time), the legacy V1 tables
  of a migrated database (secondary to `session_message`), and
  `opencode-next.db` (secondary to `opencode.db`). None is read today;
  `has_secondary` would be needed.
- Sync: 1.x shares covered; none at `dev`. Relay: none (no messaging
  integration; not found in `packages/core`, `packages/cli`,
  `packages/server` or `packages/tui` at `cb07c55`, grepped for
  `telegram`, `whatsapp` and `slack`). Origin: none; an imported session
  carries no source.
- Scratch directories: a session whose directory is under
  `~/.local/share/opencode/worktree/` is already classed by the catalog
  rule; the parser could add `scratch directory: <directory> (worktree,
  from <database> worktree)` rows from the `worktree` table. The temp root
  is not collectable.
- Deletion: no local record of a deleted 2.0 session other than the
  legacy V1 rows and a pinned id; `time_archived` should become a
  `session archived (from <database> session_v2, time_archived)` row.
- Version drift: read `session_v2` as well as `session` for session
  headers and `directory`; read the 2.0 `shell` shape (`shellID`,
  `output.output`) and the `location-switched`, `skill` and `idle` types.
  This needs a real-install round of 2.0 first (a newer version).
- Bad lines: each undecodable `message`, `part`, `session_message` or
  `event` `data`, and each undecodable part file of the JSON tree,
  should be its own `parser: unparseable record <rowid> (<reason>)` row
  carrying the value, not a count in one `parser: <n> record(s) with
  undecodable data` row.

Fixture rows:

```sql
INSERT INTO project(id,worktree,vcs,time_created,time_updated,sandboxes) VALUES('proj_a1','/home/u/repo','git',1760000000000,1760000000000,'[]');
INSERT INTO session(id,project_id,slug,directory,title,version,cost,tokens_input,tokens_output,tokens_reasoning,tokens_cache_read,tokens_cache_write,time_created,time_updated) VALUES('ses_01','proj_a1','fix-bug','/home/u/repo','Fix bug','1.2.0',0,0,0,0,0,0,1760000001000,1760000005000);
INSERT INTO message VALUES('msg_01','ses_01',1760000001000,1760000001000,'{"role":"user","time":{"created":1760000001000},"agent":"build","model":{"providerID":"anthropic","modelID":"claude-sonnet-4"}}');
INSERT INTO part VALUES('prt_01','msg_01','ses_01',1760000001000,1760000001000,'{"type":"text","text":"list files"}');
INSERT INTO message VALUES('msg_02','ses_01',1760000002000,1760000005000,'{"role":"assistant","time":{"created":1760000002000,"completed":1760000005000},"parentID":"msg_01","modelID":"claude-sonnet-4","providerID":"anthropic","mode":"build","agent":"build","path":{"cwd":"/home/u/repo","root":"/home/u/repo"},"cost":0.01,"tokens":{"input":10,"output":5,"reasoning":0,"cache":{"read":0,"write":0}}}');
INSERT INTO part VALUES('prt_02','msg_02','ses_01',1760000002000,1760000003000,'{"type":"tool","callID":"call_x1","tool":"bash","state":{"status":"completed","input":{"command":"ls"},"output":"a.txt","title":"ls","metadata":{},"time":{"start":1760000002500,"end":1760000003000}}}');
INSERT INTO credential VALUES('cred_01','anthropic','key','my key','{"type":"key","key":"sk-ant-REDACT"}',NULL,NULL,1,1760000000000,1760000000000);
```

Confidence. High: table columns, JSON field names, timestamp units, part
types, WAL, paths, absence of git branch. Medium: which table is
authoritative over time (`session_message` is new and was reset once;
`message`/`part` have been stable since the first migration). Not
determined: exact byte layout of `session_message.data` for all types in a
real install; whether an intermediate release had a startup JSON to SQLite
importer.
