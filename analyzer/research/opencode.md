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
The planned form is one `system` row per `session_share` row,
`session synced: share <id> url <url> (from opencode.db session_share,
time_created)`, timestamped by `time_created`, never with `secret`; for a
session with no `session_share` row whose `session.updated.1` events carry
`info.share.url`, `session synced: share url <url> (from opencode.db event
session.updated.1, info.time.updated)` at that event's `info.time.updated`,
and `session unshared (from opencode.db event session.updated.1,
info.time.updated)` at the first later event without `share`. Deleting a
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
