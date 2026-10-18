# Kilo Code transcript schema

Catalog agent: `kilo-code`. Kilo Code began as a Roo Code fork but its
current CLI, TUI and server are an OpenCode fork, so the SQLite schema in
[opencode.md](opencode.md) applies; the VS Code extension only reads
Roo-style task directories for import
([`packages/kilo-vscode/src/legacy-migration/task-store.ts:6-7`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/src/legacy-migration/task-store.ts#L6-L7)). Paths cited
are relative to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/kilo-code.md`](../../collectors/research/kilo-code.md).

## 1. Source

[Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode) at [`76bcfd40be616a72f4697b3041565f322245b462`](https://github.com/Kilo-Org/kilocode/commit/76bcfd40be616a72f4697b3041565f322245b462), MIT. Open
source. CLI, TUI and server in `packages/core`; VS Code extension
`kilocode.kilo-code` ([`packages/kilo-vscode/package.json:2`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/package.json#L2),[`11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/package.json#L11)).

## 2. Transcript files

XDG with no platform branching ([`packages/core/src/global.ts:3`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L3),[`12`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L12),[`22-26`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L22-L26)):
data `~/.local/share/kilo`, config `~/.config/kilo`, cache `~/.cache/kilo`,
state `~/.local/state/kilo` (fallback `<data>/state`, [`:26`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L26)). Transcripts
are SQLite: `<data>/kilo.db` on release channels, else `kilo-<channel>.db`
or a pre-existing `opencode-<channel>.db`; `KILO_DB` overrides
([`packages/core/src/database/database.ts:52-66`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/database/database.ts#L52-L66)). Legacy JSON store
`<data>/storage/session/<projectID>/<sesID>.json`,
`storage/message/<sesID>/<msgID>.json`, `storage/part/<msgID>/<prtID>.json`,
older `storage/session/info/*.json` and `storage/session/message/<ses>/*.json`,
marker `storage/migration` ([`packages/opencode/src/storage/storage.ts:65`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L65),[`140-170`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L140-L170),[`193-197`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L193-L197),[`234-236`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L234-L236)).
The VS Code globalStorage `kilocode.kilo-code/tasks/<id>/` holds only
pre-migration Roo-style files.

Cloud session marker: `<data>/storage/session_share/<sessionID>.json`, a
storage key written as a JSON file
([`storage.ts:64-66`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L64-L66)),
holds `{id, ingestPath, url?}`
([`packages/opencode/src/kilo-sessions/kilo-sessions.ts:1549-1558`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1549-L1558)). `id` and `ingestPath`
(the path on Kilo's session ingest service that receives the session's
events) are written when the ingest service registers the session, at
session creation for a user signed in to Kilo
([`:1432-1466`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1432-L1466)); `url`,
`https://app.kilo.ai/s/<share_token>`, is added by a share
([`:1468-1511`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1468-L1511)) and removed by
an unshare, which keeps the file
([`:1513-1547`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1513-L1547)). A session
created while signed out, or with `KILO_DISABLE_SESSION_INGEST` set, has no
file. The file carries no time of its own.

## 3. Record schema

V1 `message.data` and `part.data` ([`packages/schema/src/v1/session.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts)):
user [`:374-400`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L374-L400) `{role:"user", time{created}, agent, model{providerID,
modelID, variant?}, system?, tools?, editorContext?, summary?}`; assistant
[`:499-535`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L499-L535) `{role:"assistant", time{created, completed?}, parentID,
modelID, providerID, mode, agent, path{cwd, root}, cost, tokens{input,
output, reasoning, cache{read, write}}, error?, finish?}`. Parts (all with
`id, sessionID, messageID` [`:80-86`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L80-L86)): `text{text, synthetic?,
time{start,end}}` [`:102`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L102), `reasoning{text, time}` [`:118`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L118), `tool{callID, tool,
state{status: pending|running|completed|error, input, output?, title?,
error?, time{start,end}}}` [`:289-362`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L289-L362), `step-start`, `step-finish{reason,
snapshot (git hash), model, cost, tokens}` [`:241-288`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L241-L288), `file`, `agent`,
`subtask`, `compaction`, `retry`, `patch`, `snapshot`.

V2 `session_message.data` ([`packages/schema/src/session-message.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts)): base
`{id, time{created}}` [`:24-27`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L24-L27); `type` in `agent-switched, model-switched,
user{text, files, agents}, synthetic{text}, system{text}, shell{callID,
command, output, time{created, completed}}, assistant{agent, model,
content[], snapshot{start, end, files}, finish, cost, tokens, error,
time{created, completed}}, compaction{reason, summary, recent}` [`:45-213`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L45-L213).
Assistant `content[]`: `text{id, text}`, `reasoning{id, text, time}`,
`tool{id, name, state{status, input, content[], structured, error, result},
time{created, ran, completed}}` [`:122-158`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L122-L158). Times are millisecond epochs. The two switch records carry the common base `id`, `metadata?` and `time.created` ([`session-message.ts:24-28`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L24-L28)) plus `agent` (a string) for `agent-switched` ([`:30-35`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L30-L35)) and `model` for `model-switched` ([`:37-42`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L37-L42)), a `Model.Ref` `{id, providerID, variant?}` ([`packages/schema/src/model.ts:13-18`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/model.ts#L13-L18)). The projector stores `id` and `type` in their own columns and the rest of the record in `data` ([`packages/core/src/session/projector.ts:213-229`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L213-L229)), so `data` is `{time, agent}` or `{time, model}`.

No git branch is recorded; `snapshot` holds commit hashes.

## 4. Joins

`session.id` ← `message.session_id` ← `part.message_id`; `session.directory`
is the cwd and `session.project_id` → `project.worktree`
([`project/sql.ts:8`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/project/sql.ts#L8)). A V1 `tool` part carries both call and result in
`state`; V2 `assistant.content[].tool.id` likewise.

## 5. SQLite stores

`kilo.db` ([`packages/core/src/session/sql.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts)): `session(id, project_id,
workspace_id, parent_id, slug, directory, path, title, version, share_url,
summary_*, metadata JSON, cost, tokens_*, revert JSON, permission JSON,
agent, model JSON{id, providerID, variant}, time_created, time_updated,
time_compacting, time_archived)` [`:24-71`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L24-L71); `message(id, session_id,
time_created, time_updated, data JSON)` [`:73-90`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L73-L90); `part(id, message_id,
session_id, time_*, data JSON)` [`:92-114`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L92-L114); `session_message(id, session_id,
type, seq, time_*, data JSON)` [`:135-154`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L135-L154); `session_input(prompt JSON)`,
`session_context_epoch(snapshot JSON)`, `todo`; `project(id, worktree, vcs,
name, sandboxes)`; `credential(value JSON)` ([`credential/sql.ts:5-14`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/credential/sql.ts#L5-L14));
`account(access_token, refresh_token)` and legacy `control_account`
([`account/sql.ts:6-39`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/account/sql.ts#L6-L39)). The projector writes V2 `session_message` and V1
`message`/`part` for every event ([`session/projector.ts:213-230`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L213-L230),[`285-300`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L285-L300),[`335-345`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L335-L345)),
so either set is complete. WAL mode as in OpenCode; collect the `-wal`
sidecar.

## 6. Format versions

JSON `storage/` (two internal migrations, [`storage.ts:83-200`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L83-L200)) became SQLite
through drizzle migrations under `packages/core/src/database/migration/2026...`
(39 files); `opencode-*.db` was renamed `kilo-*.db`; `message`/`part` are
kept beside `session_message` ("legacy-writer-compat", migration
[`20260714141136`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/database/migration/20260714141136_session-message-legacy-writer-compat.ts)). Id prefixes: session `ses`, message `msg`/`msg_`, part
`prt` ([`schema/src/session-id.ts:5`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-id.ts#L5), [`v1/session.ts:17`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L17),[`23`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L23),
[`session-message.ts:12`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L12)). `.kilocodemodes` has no references in current
source and is legacy only.

## 7. Secrets

`auth.json` ([`packages/opencode/src/auth/index.ts:11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/auth/index.ts#L11)), `credential.value`,
`account.access_token`/`refresh_token`, `control_account`, and
`session.share_url`. The `storage/session_share/*.json` files hold no
credential: the ingest service authenticates with the Kilo token from
`auth.json` ([section 8](#8-parser-plan)). The database is collected unflagged like Cursor's
`state.vscdb`; the tables above are the redaction targets (issue 23).

## 8. Parser plan

Globs: `.local/share/kilo/kilo*.db`, `.local/share/kilo/opencode-*.db`,
`.local/share/kilo/storage/{session,message,part}/**/*.json`; also
`<GS>/kilocode.kilo-code/tasks/**` for pre-migration tasks, parsed with the
Roo mapping.

Rows: one per V1 `part`, or per V2 `session_message` content item.

| Column | V1 |
| --- | --- |
| timestamp_utc | `part.data.time.start` or `message.time_created` |
| session_id | `session_id` (`parent_id` for subtasks) |
| project_path | `session.directory` or `project.worktree` |
| git_branch | empty |
| turn_type | text → by role; reasoning → thinking; tool → tool_use plus tool_result; step-*/compaction → system |
| model | `assistant.modelID` |
| tool_name, tool_use_id | `part.data.tool`, `callID` |
| text | `text` or `state.title` |

Model and mode rows. A `system` row `model: <modelID> provider=<providerID>`
precedes the first message of a session that names a model (V1 user
`model.{providerID, modelID}`, V1 assistant `providerID` and `modelID`, V2
assistant `model.{id, providerID}`), and `model: <old> -> <new>
provider=<providerID>` precedes every later message, or stands for every V2
`model-switched` record, whose model differs. The message's `agent` (V1 user
and assistant, V2 assistant, V2 `agent-switched` `agent`) is tracked the
same way as `permission mode: agent=<name>` and `permission mode:
agent=<old> -> agent=<new>`, because an agent (`build`, `plan` or a custom
one) is a mode that carries its own permission ruleset (the agent's `permission: PermissionV1.Ruleset`, [`packages/opencode/src/agent/agent.ts:54`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/agent/agent.ts#L54)). Both rows take the
message's timestamp. Kilo writes V1 and V2 for every event ([section 5](#5-sqlite-stores)) and the parser reads V2 only for a session with no V1 rows, so for Kilo sessions the change rows come from the V1 messages and the V2 switch records are read only when V1 is missing. The session's `permission` JSON and the project's
`sandboxes` array are named in [section 5](#5-sqlite-stores) without their
shape, so the parser does not read them (issue 98), nor are the `.kilo/` and `.kilocode/` permission configuration files that [`collectors/research/kilo-code.md`](../../collectors/research/kilo-code.md) names; the research records
no per-call approval or denial, and whether a denied call shows as a tool
`state.status` of `error` is not researched.

Sync: the share code is OpenCode's
([opencode.md section 8](opencode.md#8-parser-plan)), and Kilo changed what
it calls. Kilo replaced OpenCode's share service with its own cloud
sessions: for a user signed in to Kilo (a `kilo` entry in `auth.json`, or
`KILO_API_KEY`, [`packages/opencode/src/kilo-sessions/kilo-sessions.ts:199-210`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L199-L210)),
every new session is registered with `POST /api/session` on
`https://ingest.kilosessions.ai` (`KILO_SESSION_INGEST_URL` overrides) at
creation ([`:245-272`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L245-L272),
[`:676-681`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L676-L681)), and from then
on every message, part, model and diff is posted to its `ingestPath`
([`:771-779`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L771-L779);
[`ingest-queue.ts:281-295`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/ingest-queue.ts#L281-L295)).
This is on by default once signed in; only `KILO_DISABLE_SESSION_INGEST`
turns it off, and `KILO_DISABLE_SHARE` blocks only the public link
([`:275-278`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L275-L278)). `/share` and
`/unshare` reach Kilo's service instead of OpenCode's
([`packages/opencode/src/share/session.ts:25-36`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/share/session.ts#L25-L36)),
whose `ShareNext` initialisation Kilo commented out
([`packages/opencode/src/project/bootstrap.ts:9-11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/project/bootstrap.ts#L9-L11)),
so the upstream `session_share` table stays empty; `session.share_url` and
the `session.updated.1` events still record the public URL as upstream
([`packages/opencode/src/session/session.ts:1014-1016`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/session/session.ts#L1014-L1016)).
The marker is the `storage/session_share/<sessionID>.json` file
([section 2](#2-transcript-files)). The parser yields one `system` row per
file, `session synced: kilo session <id> ingest <ingestPath> share <url or
-> (from storage/session_share/<sessionID>.json, file mtime)`, timestamped
by the file's modification time, with the session id from the file name;
a file that is not a JSON object is one `parser:` row. The OpenCode
reader also yields the event rows of
[opencode.md section 8](opencode.md#8-parser-plan) from `kilo.db`
(`session.share_url` itself is not read). These rows are fixture only: no
real install has shown the marker file. Deleting a session asks the service to delete the
remote copy (`DELETE /api/session/<id>`) and removes the file only when the
service accepts; signed out, or on a network error or an error status, the
file stays, with a `share remove failed` log line in the second and third
cases ([`session/session.ts:728-733`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/session/session.ts#L728-L733),
[`packages/opencode/src/kilocode/session/index.ts:281-284`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session/index.ts#L281-L284),
[`kilo-sessions.ts:1687-1718`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1687-L1718)).
The service's `creating session`, `sharing`, `unsharing` and `removing
share` lines go to `<data>/log/<ISO time>.log`
([`kilo-sessions.ts:1444`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1444),
[`:1487`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1487), [`:1527`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1527),
[`:1691`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1691);
[`packages/core/src/util/log.ts:84-85`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/util/log.ts#L84-L85)).
A second uploader, session export to
`https://supermassive-black-hole.kiloapps.io/v1/session-export/batch` for
personal accounts on free Kilo gateway models, is compiled in but switched
off (`enabled = false`) at this commit
([`kilocode/session-export/session-export.ts:35`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session-export/session-export.ts#L35),
[`worker/endpoint.ts:1`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session-export/worker/endpoint.ts#L1),
[`eligibility.ts:16-22`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session-export/eligibility.ts#L16-L22));
its `session-export.db` and `session-export-workspace.json` sit in `<data>`
([`kilocode/bootstrap.ts:71-89`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/bootstrap.ts#L71-L89)).
Telemetry goes to PostHog, a product analytics service
([`packages/kilo-telemetry/src/client.ts:9`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-telemetry/src/client.ts#L9),
level set by `KILO_TELEMETRY_LEVEL`,
[`telemetry.ts:89-91`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-telemetry/src/telemetry.ts#L89-L91));
a search of its event definitions for `prompt`, `text`, `content` and
`message` found counts and ids, not prompt text.

Fixtures:

```json
{"_table":"session","record":{"id":"ses_01JAX","project_id":"prj_01JAX","parent_id":null,"slug":"fix-tests","directory":"/home/u/proj","title":"fix tests","version":"1.0.0","agent":"build","model":"{\"id\":\"claude-sonnet-4-5\",\"providerID\":\"anthropic\"}","time_created":1760000000000,"time_updated":1760000005000}}
{"_table":"message","record":{"id":"msg_01JAXA","session_id":"ses_01JAX","time_created":1760000002000,"data":"{\"role\":\"assistant\",\"parentID\":\"msg_01JAXU\",\"modelID\":\"claude-sonnet-4-5\",\"providerID\":\"anthropic\",\"mode\":\"build\",\"agent\":\"build\",\"path\":{\"cwd\":\"/home/u/proj\",\"root\":\"/home/u/proj\"},\"cost\":0.0041,\"tokens\":{\"input\":1200,\"output\":80,\"reasoning\":0,\"cache\":{\"read\":900,\"write\":0}},\"time\":{\"created\":1760000002000,\"completed\":1760000003000}}"}}
{"_table":"part","record":{"id":"prt_01JAXT","message_id":"msg_01JAXA","session_id":"ses_01JAX","time_created":1760000002500,"data":"{\"type\":\"tool\",\"callID\":\"call_1\",\"tool\":\"bash\",\"state\":{\"status\":\"completed\",\"input\":{\"command\":\"pytest -q\"},\"output\":\"3 passed\",\"title\":\"pytest -q\",\"metadata\":{},\"time\":{\"start\":1760000002500,\"end\":1760000003000}}}"}}
{"_table":"session_message","record":{"id":"msg_01JAXB","session_id":"ses_01JAX","type":"assistant","seq":4,"time_created":1760000002000,"data":"{\"agent\":\"build\",\"model\":{\"providerID\":\"anthropic\",\"modelID\":\"claude-sonnet-4-5\"},\"content\":[{\"type\":\"tool\",\"id\":\"call_1\",\"name\":\"bash\",\"state\":{\"status\":\"completed\",\"input\":{\"command\":\"pytest -q\"},\"content\":[{\"type\":\"text\",\"text\":\"3 passed\"}],\"structured\":{}},\"time\":{\"created\":1760000002500,\"completed\":1760000003000}}],\"time\":{\"created\":1760000002000,\"completed\":1760000003000}}"}}
```

Confidence. High: drizzle columns and V1/V2 struct fields (read from
source). Medium: V2 `session_message.data` serialised key order and the
`Model.Ref` shape. Not determined: the code path that imports legacy JSON
`storage/` into SQLite ([`packages/opencode/src/storage/db.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/db.ts), not traced).
