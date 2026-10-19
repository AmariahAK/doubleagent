# kilo-code

Catalog agent: `kilo-code`. Kilo Code began as a Roo Code fork ([roo-code.md](roo-code.md), itself
a fork of Cline) but its current CLI, TUI (terminal UI) and server are an OpenCode fork, so the
SQLite schema in [opencode.md](opencode.md) applies; the VS Code extension only reads Roo-style
task directories for import
([`packages/kilo-vscode/src/legacy-migration/task-store.ts:6-7`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/src/legacy-migration/task-store.ts#L6-L7)).
Paths, credentials and the rest of the per-user state are in
[`collectors/research/kilo-code.md`](../../collectors/research/kilo-code.md).

## 1. Source and evidence

[Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode) at [`76bcfd40be616a72f4697b3041565f322245b462`](https://github.com/Kilo-Org/kilocode/commit/76bcfd40be616a72f4697b3041565f322245b462), MIT. Open
source. CLI, TUI and server in `packages/core`; VS Code extension
`kilocode.kilo-code` ([`packages/kilo-vscode/package.json:2`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/package.json#L2),[`11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/package.json#L11)).

Paths cited are relative to the clone.

### Observed

No real install.

- Not seen on a real install: the remote-control records of a session Kilo Cloud created
  ([Sync, relay and origin](#sync-relay-and-origin)).
- Fixture only: no real install has shown the `storage/session_share/<sessionID>.json` marker
  file ([Cloud session marker](#cloud-session-marker)).

### Source reviews

- **Source review (2026-10-19)**: [Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode)
  at [`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22), against [`76bcfd4`](https://github.com/Kilo-Org/kilocode/commit/76bcfd40be616a72f4697b3041565f322245b462), the commit the rest of
  this document cites. Kilo Code is no longer a Cline or Roo Code fork in
  any file the parser reads: its CLI, server and storage are OpenCode's
  ([opencode.md](opencode.md)), and only the VS Code extension's import of
  pre-migration Roo-style tasks remains of the Roo lineage. One line per
  requirement class:
  - Permission state: found, not read by the parser. Rejections and rule
    denials are tool part errors; "always" grants are written to the
    global config's `permission` key and to the `permission` table; the
    session `permission` column and the sandbox policy files under
    `~/.local/state` are further standing state. See
    [section 5](#5-other-stores) and [section 8](#8-parser-plan).
  - Model: already covered (V1 message model, V2 `model-switched`).
  - Past use beyond the primary store: found. The TUI's
    `prompt-history.jsonl` is not read; `retention/state.json` records
    automatic deletions.
  - Sync, relay and origin: found. Remote control from Kilo Cloud, and
    sessions it creates on the host, are recorded only in the log
    directory; a session cloned from a cloud session keeps no cloud id.
    Already covered: the ingest marker and share URL. No relay through a
    messaging platform was found.
  - Scratch directories: found. `<data>/worktree/<project id>/` is under
    a catalog entry; a project's `.kilo/worktrees/` is not, and remote
    attachments go to a temp root outside the home.
  - Deletion: found, the opt-in retention pass; already covered, the
    session delete and its remote delete.
  - Version drift: 9 of the 58 files cited by this document, the
    collector document and the parser changed, none moved or
    disappeared, and the schema, SQL and projector files the parser
    depends on are unchanged. The ingest queue's `session_status` item
    gained a transition record, which is sent to the server and not
    stored locally.
  - Bad lines: already covered for every file the parser reads.
    `prompt-history.jsonl` is JSON Lines and needs per-line handling when
    it is read.

## 2. Transcript stores

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

### What survives a delete

Deleting a session asks Kilo's service to delete the remote copy
(`DELETE /api/session/<id>`) and removes the
`storage/session_share/<sessionID>.json` marker only when the service
accepts; signed out, or on a network error or an error status, the
marker stays, with a `share remove failed` log line in the last two
cases
([`session/session.ts:728-733`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/session/session.ts#L728-L733),
[`packages/opencode/src/kilocode/session/index.ts:281-284`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session/index.ts#L281-L284),
[`kilo-sessions.ts:1687-1718`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1687-L1718)).
Which `kilo.db` rows the delete removes is not stated here; the session
code is OpenCode's ([opencode.md](opencode.md)). The opt-in retention
pass (`retention.enabled`, off by default) deletes sessions older than
`retention.maxAgeDays` (default 30) through the same delete, then
vacuums the database and truncates the WAL, which removes the deleted
rows' remnants, and records its counts, but no session id, in
`retention/state.json`. What remains is the TUI's prompt history
`prompt-history.jsonl`, the last 50 prompts and shell commands with no
time, session or directory, which survives a delete, the retention pass
and a removed project. The log files in `<data>/log/` hold the
`creating session`, `removing share` and `remote session started` lines;
whether a delete touches them is not stated. The analyzer reads
the `kilo.db` sessions and the marker files; it reads neither the prompt
history, the logs nor `retention/state.json`
([section 8](#8-parser-plan)).

### Remote control

Source review of 2026-10-19: `kilo remote`, `KILO_REMOTE=1` or
`"remote_control": true` in the config connects the host to Kilo Cloud,
Kilo's web service, so sessions can be driven, and created, from there
([`packages/core/src/v1/config/config.ts:121-123`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/v1/config/config.ts#L121-L123),
[`packages/opencode/src/kilo-sessions/kilo-sessions.ts:320`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L320),
[`:905`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L905)).
The only local record is in `<data>/log/<ISO time>.log`: `remote
connection enabled` and `remote connection disabled`
([`:1220`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1220),
[`:1259`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1259)),
and for each session the remote side creates on the host `remote session
started` with `sessionID`, `startedAt`, `model` (`<providerID>/<id>`) and
`directory`, then `remote session ended` with `sessionID`, `startedAt`,
`durationMs` and `reason`
([`packages/opencode/src/kilo-sessions/remote-session-log.ts:37-61`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/remote-session-log.ts#L37-L61),
[`remote-sender.ts:1176-1180`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/remote-sender.ts#L1176-L1180)).
The session itself is an ordinary row of `kilo.db` with nothing marking
its remote creation. Files the remote side attaches that are not text,
images or PDF are written to
`<system temp directory>/kilo/remote-attachments/<base64url session id>/`
and removed when the session's remote handling ends
([`packages/opencode/src/kilocode/remote-attachments.ts:8-16`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/remote-attachments.ts#L8-L16),
[`:272-287`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/remote-attachments.ts#L272-L287);
[`packages/core/src/global.ts:28`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/global.ts#L28)).

### Cloud session import

Source review of 2026-10-19: the VS Code extension lists the user's
Kilo Cloud sessions and clones one locally on its first message, and the
remote side can ask for the same clone
([`packages/kilo-vscode/src/kilo-provider/handlers/cloud-session.ts:1-6`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-vscode/src/kilo-provider/handlers/cloud-session.ts#L1-L6)).
The export is fetched from the ingest service
([`packages/kilo-gateway/src/cloud-sessions.ts:153-157`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L153-L157))
and stored as a new local session with a fresh id; the cloud session's
`parentID`, `share` and `permission` are dropped
([`:257`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L257),
[`:268`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L268),
[`:295-310`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L295-L310)),
and no log line names the cloud id (grepped `log.info` and `cloud` in
`packages/opencode/src/kilocode/server`). A cloned session therefore
cannot be told from a local one.

## 3. Record schema

### V1 messages and parts

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

### V2 session messages

V2 `session_message.data` ([`packages/schema/src/session-message.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts)): base
`{id, time{created}}` [`:24-27`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L24-L27); `type` in `agent-switched, model-switched,
user{text, files, agents}, synthetic{text}, system{text}, shell{callID,
command, output, time{created, completed}}, assistant{agent, model,
content[], snapshot{start, end, files}, finish, cost, tokens, error,
time{created, completed}}, compaction{reason, summary, recent}` [`:45-213`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L45-L213).
Assistant `content[]`: `text{id, text}`, `reasoning{id, text, time}`,
`tool{id, name, state{status, input, content[], structured, error, result},

time{created, ran,
completed}}` [`:122-158`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L122-L158). Times are millisecond epochs. The two switch records carry the common base `id`, `metadata?` and `time.created` ([`session-message.ts:24-28`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L24-L28)) plus `agent` (a string) for `agent-switched` ([`:30-35`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L30-L35)) and `model` for `model-switched` ([`:37-42`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L37-L42)), a `Model.Ref` `{id,
providerID,
variant?}` ([`packages/schema/src/model.ts:13-18`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/model.ts#L13-L18)). The projector stores `id` and `type` in their own columns and the rest of the record in `data` ([`packages/core/src/session/projector.ts:213-229`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L213-L229)), so `data` is `{time,
agent}` or `{time, model}`.

No git branch is recorded; `snapshot` holds commit hashes.

## 4. Joins and timestamps

`session.id` ← `message.session_id` ← `part.message_id`; `session.directory`
is the cwd and `session.project_id` → `project.worktree`
([`project/sql.ts:8`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/project/sql.ts#L8)). A V1 `tool` part carries both call and result in
`state`; V2 `assistant.content[].tool.id` likewise.

## 5. Other stores

### `kilo.db`

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

### Permission tables and columns

Source review of 2026-10-19: `session.permission` is a JSON
ruleset, `[{permission, pattern, action: "allow"|"deny"|"ask"}]`
([`packages/core/src/session/sql.ts:55`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/session/sql.ts#L55),
[`packages/schema/src/v1/permission.ts:16-25`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/v1/permission.ts#L16-L25)).
The `permission` table, `(id, project_id, action, resource,
time_created, time_updated)`, unique per project, action and resource
([`packages/core/src/permission/sql.ts:7-20`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/permission/sql.ts#L7-L20)),
holds the saved allow grants of a project that the newer permission
service reads
([`packages/core/src/permission.ts:116`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/permission.ts#L116),
[`:131-135`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/permission.ts#L131-L135)). Both were
present at [`76bcfd4`](https://github.com/Kilo-Org/kilocode/commit/76bcfd40be616a72f4697b3041565f322245b462).

### Cloud session marker

`<data>/storage/session_share/<sessionID>.json`, a
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

### TUI prompt history

Source review of 2026-10-19: the terminal UI keeps the prompts typed into
it in `~/.local/state/kilo/prompt-history.jsonl`, the state directory of
[section 2 of `collectors/research/kilo-code.md`](../../collectors/research/kilo-code.md#2-per-user-storage)
([`packages/tui/src/app.tsx:267-273`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/app.tsx#L267-L273),
[`packages/tui/src/prompt/history.tsx:53`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L53)).
Each line is `{input, mode?: "normal"|"shell", parts[]}`, the typed text,
whether it was a shell command (`!`), and the attached file and agent
parts; there is no time, session id or directory
([`:9-25`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L9-L25)). A prompt is
appended unless it repeats the last one, and the file is rewritten with
the last 50 (`MAX_HISTORY_ENTRIES`) whenever it grows past that and at
every start, which drops lines that do not parse
([`:27-42`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L27-L42),
[`:54-60`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L54-L60),
[`:83-108`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L83-L108)).
It was already present at [`76bcfd4`](https://github.com/Kilo-Org/kilocode/commit/76bcfd40be616a72f4697b3041565f322245b462).

### Retention

Source review of 2026-10-19: with `retention.enabled: true` in `kilo.json`
(off by default), a pass at most every 23 hours deletes sessions older
than `retention.maxAgeDays` (default 30) through the normal session
delete, then runs `VACUUM` and truncates the WAL when enough pages are
free, which also removes the deleted rows' remnants from the database
files
([`packages/opencode/src/kilocode/session/retention.ts:13-32`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L13-L32),
[`:163-167`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L163-L167),
[`:301-324`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L301-L324)).
It writes `<data>/retention/state.json`, `{at, scanned, deleted,
skippedActive, failed, durationMs, cancelled?, reclaimedBytes?}`, for the
last pass ([`:45-54`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L45-L54),
[`:326`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L326)),
and logs `retention pass complete` with the same counts
([`:472`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L472)).

## 6. Format versions

JSON `storage/` (two internal migrations, [`storage.ts:83-200`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L83-L200)) became SQLite
through drizzle migrations under `packages/core/src/database/migration/2026...`
(39 files); `opencode-*.db` was renamed `kilo-*.db`; `message`/`part` are
kept beside `session_message` ("legacy-writer-compat", migration
[`20260714141136`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/database/migration/20260714141136_session-message-legacy-writer-compat.ts)). Id prefixes: session `ses`, message `msg`/`msg_`, part
`prt` ([`schema/src/session-id.ts:5`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-id.ts#L5), [`v1/session.ts:17`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L17),[`23`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L23),
[`session-message.ts:12`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L12)). `.kilocodemodes` has no references in current
source and is legacy only.

OpenCode 2.0's `session_v2` table and how the parser reads it are under
[Bad lines](#bad-lines).

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

### Permission state

The message's `agent` (V1 user and assistant, V2 assistant, V2 `agent-switched` `agent`) is tracked
the same way as the model ([Model](#model)), as `permission mode: agent=<name>` and
`permission mode: agent=<old> -> agent=<new>`, because an agent (`build`, `plan` or a custom one) is
a mode that carries its own permission ruleset (the agent's `permission: PermissionV1.Ruleset`,
[`packages/opencode/src/agent/agent.ts:54`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/agent/agent.ts#L54)).
The session's `permission` JSON and the project's `sandboxes` array are named in
[section 5](#5-other-stores) without their shape, so the parser does not read them (issue 98), nor
are the `.kilo/` and `.kilocode/` permission configuration files that
[`collectors/research/kilo-code.md`](../../collectors/research/kilo-code.md) names; the research
records no per-call approval or denial, and whether a denied call shows as a tool `state.status` of
`error` is not researched.

From the source review of 2026-10-19 at [`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22); the
parser reads none of it yet; the code is OpenCode's with Kilo's changes,
so a reader belongs in the shared OpenCode parser:

- Per call: a request is `{id, sessionID, permission, patterns,
  metadata, always, tool?{messageID, callID}}` and a reply is `once`,
  `always` or `reject`
  ([`packages/schema/src/v1/permission.ts:27-38`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/v1/permission.ts#L27-L38)).
  The `permission.asked` and `permission.replied` events are not durable,
  so they never reach the `event` table
  ([`:66-70`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/v1/permission.ts#L66-L70);
  [`packages/schema/src/event.ts:42-52`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/event.ts#L42-L52)).
  What is stored is the tool part: a rejected call ends with
  `state.status` `error` and `state.error` `The user rejected permission
  to use this specific tool call.`, the same text followed by ` with the
  following feedback: <text>`, or, for a call a deny rule stopped, `The
  user has specified a rule which prevents you from using this specific
  tool call. Here are some of the relevant rules <JSON>`
  ([`packages/core/src/v1/permission.ts:7-27`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/v1/permission.ts#L7-L27);
  [`packages/opencode/src/permission/index.ts:314-333`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L314-L333)).
  A reject also rejects every other pending request of the session. An
  approval leaves no mark on the part. Matching these prefixes yields
  `permission decision: rejected`, `rejected with feedback` or `denied by
  rule` beside the tool's `tool_result` row, on its `callID`.
- Standing, written by the agent: an `always` reply adds `{<permission>:
  {<pattern>: "allow"}}` to the `permission` key of the first existing
  global config file among `kilo.jsonc`, `kilo.json`, `opencode.jsonc`,
  `opencode.json` and `config.json` in `~/.config/kilo`
  ([`packages/opencode/src/permission/index.ts:357-365`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L357-L365),
  [`packages/opencode/src/config/config.ts:206-215`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/config/config.ts#L206-L215),
  [`:1147-1153`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/config/config.ts#L1147-L1153)),
  and the extension's selective save writes `allow` and `deny` rules the
  same way ([`permission/index.ts:385-403`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L385-L403)).
  Protected configuration paths are downgraded to `once`
  ([`:338-340`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L338-L340)).
  The global config therefore records every standing grant the user gave,
  with the file's modification time as the only time.
- Standing, other: the `permission` table and `session.permission`
  column of [section 5](#5-other-stores); the sandbox policy files of
  [section 2 of `collectors/research/kilo-code.md`](../../collectors/research/kilo-code.md#2-per-user-storage);
  and project `kilo.json` and `.kilo/` permission keys.

Each standing entry can be one `permission setting: <key>=<value> (from
<file>, file mtime)` row; a `permission` table row has its own
`time_created`.

### Model

Model rows. A `system` row `model: <modelID> provider=<providerID>` precedes the first message of a
session that names a model (V1 user `model.{providerID, modelID}`, V1 assistant `providerID` and
`modelID`, V2 assistant `model.{id, providerID}`), and `model: <old> -> <new> provider=<providerID>`
precedes every later message, or stands for every V2 `model-switched` record, whose model differs.
Both these rows and the `permission mode:` rows of [Permission state](#permission-state) take the
message's timestamp. Kilo writes V1 and V2 for every event ([`kilo.db`](#kilodb)) and the parser
reads V2 only for a session with no V1 rows, so for Kilo sessions the change rows come from the V1
messages and the V2 switch records are read only when V1 is missing.

### Past use and secondary sources

Past use beyond the primary store (2026-10-19):
`~/.local/state/kilo/prompt-history.jsonl` ([TUI prompt history](#tui-prompt-history))
is a secondary source the parser does not read. Its lines carry no time,
session or directory, so each would be a `user` row with an empty
`timestamp_utc` that pairs with a transcript prompt on text alone; it
survives a deleted session, the retention pass and a removed project,
and holds shell commands (`mode` `shell`) typed in the TUI. A bad line
must become its own row before the next start drops it. The log
directory's `remote session started` lines and `retention/state.json`
are further records the parser does not read.

### Sync, relay and origin

Sync: the share code is OpenCode's
([opencode.md section 8](opencode.md#sync-relay-and-origin)), and Kilo changed what
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
([Cloud session marker](#cloud-session-marker)). The parser yields one `system` row per
file, `session synced: kilo session <id> ingest <ingestPath> share <url or
-> (from storage/session_share/<sessionID>.json, file mtime)`, timestamped
by the file's modification time, with the session id from the file name;
a file that is not a JSON object is one `parser:` row. The OpenCode
reader also yields the event rows of
[opencode.md section 8](opencode.md#sync-relay-and-origin) from `kilo.db`
(`session.share_url` itself is not read). These rows are fixture only: no
real install has shown the marker file. What a delete does to the file and the remote copy is in
[What survives a delete](#what-survives-a-delete).

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

Origin and remote control (source review of 2026-10-19): a session created by Kilo Cloud
over remote control can be marked from its `remote session started` log
line (`sessionID`, `startedAt`, `model`, `directory`), and remote
control itself from the `remote connection enabled` and `disabled`
lines. Each log line is `INFO  <UTC time to the second> +<ms>ms
service=<name> <key>=<value>... <message>`, written at the default level
`INFO`
([`packages/core/src/util/log.ts:27`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/util/log.ts#L27),
[`:162-189`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/util/log.ts#L162-L189)), so a reader
splits the key-value pairs off the message.
A session cloned from a cloud session records nothing of its origin.

### Scratch directories

Source review of 2026-10-19: `<data>/worktree/<project id>/`
([`packages/opencode/src/worktree/index.ts:210`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/worktree/index.ts#L210))
is under the catalog entry `.local/share/kilo`, so the analyzer's catalog
rule classes it. The agent manager's and the TUI's worktrees are
`<project>/.kilo/worktrees/<name>`
([`packages/opencode/src/kilocode/cli/cmd/tui-worktree.ts:14-17`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/cli/cmd/tui-worktree.ts#L14-L17)),
inside the user's project and under no home catalog entry, so the
analyzer counts each as a project of its own; `project_directory.type`
`git_worktree` and `project.sandboxes` name them
([`packages/core/src/project/sql.ts:16`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/project/sql.ts#L16),
[`:20-34`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/project/sql.ts#L20-L34)) and could
yield `scratch directory:` rows. Remote attachments go to a temp root
outside the home ([Remote control](#remote-control)).

### Deletion

Source review of 2026-10-19: the retention pass deletes old sessions in bulk
and vacuums the database ([Retention](#retention);
[What survives a delete](#what-survives-a-delete)); its
`state.json` can be one `system` row, `sessions deleted by retention:
deleted=<n> scanned=<n> failed=<n> (from retention/state.json, at)`, with
no `session_id`, since the file names no session.

### Bad lines

The source review of 2026-10-19 found bad lines already covered for every file the parser reads;
`prompt-history.jsonl` is JSON Lines and needs per-line handling when it is read
([Past use and secondary sources](#past-use-and-secondary-sources)).

The `kilo-code` parser subclasses the `opencode` parser, so two findings
of the OpenCode review of 2026-10-19 reach Kilo Code
([section 1 of `opencode.md`](opencode.md#source-reviews)). The OpenCode
parser counts undecodable database records, part files and events into
one `parser: <n> record(s) with undecodable data` row instead of one row
per record, and Kilo Code inherits that row. OpenCode 2.0 moved
sessions to a `session_v2` table that the parser does not read; no
`session_v2` table was found in Kilo Code's packages at [`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22), so
this applies only once Kilo Code takes that store. Both are fixed in the
OpenCode parser since analyzer 0.19.0 and apply to Kilo Code through the
subclass: each undecodable record, part file and event is its own
`parser: unparseable record <rowid> (<table>.data: <reason>): <data>` or
`parser: unparseable part <partID> (<reason>): <text>` row carrying it in
full (issue 139), and a database with `session_v2` is read from it, its
`session_message` transcript and the 1.x tables only for a session that
`session_message` lacks (issue 165).

### Fixtures

Fixtures:

```json
{"_table":"session","record":{"id":"ses_01JAX","project_id":"prj_01JAX","parent_id":null,"slug":"fix-tests","directory":"/home/u/proj","title":"fix tests","version":"1.0.0","agent":"build","model":"{\"id\":\"claude-sonnet-4-5\",\"providerID\":\"anthropic\"}","time_created":1760000000000,"time_updated":1760000005000}}
{"_table":"message","record":{"id":"msg_01JAXA","session_id":"ses_01JAX","time_created":1760000002000,"data":"{\"role\":\"assistant\",\"parentID\":\"msg_01JAXU\",\"modelID\":\"claude-sonnet-4-5\",\"providerID\":\"anthropic\",\"mode\":\"build\",\"agent\":\"build\",\"path\":{\"cwd\":\"/home/u/proj\",\"root\":\"/home/u/proj\"},\"cost\":0.0041,\"tokens\":{\"input\":1200,\"output\":80,\"reasoning\":0,\"cache\":{\"read\":900,\"write\":0}},\"time\":{\"created\":1760000002000,\"completed\":1760000003000}}"}}
{"_table":"part","record":{"id":"prt_01JAXT","message_id":"msg_01JAXA","session_id":"ses_01JAX","time_created":1760000002500,"data":"{\"type\":\"tool\",\"callID\":\"call_1\",\"tool\":\"bash\",\"state\":{\"status\":\"completed\",\"input\":{\"command\":\"pytest -q\"},\"output\":\"3 passed\",\"title\":\"pytest -q\",\"metadata\":{},\"time\":{\"start\":1760000002500,\"end\":1760000003000}}}"}}
{"_table":"session_message","record":{"id":"msg_01JAXB","session_id":"ses_01JAX","type":"assistant","seq":4,"time_created":1760000002000,"data":"{\"agent\":\"build\",\"model\":{\"providerID\":\"anthropic\",\"modelID\":\"claude-sonnet-4-5\"},\"content\":[{\"type\":\"tool\",\"id\":\"call_1\",\"name\":\"bash\",\"state\":{\"status\":\"completed\",\"input\":{\"command\":\"pytest -q\"},\"content\":[{\"type\":\"text\",\"text\":\"3 passed\"}],\"structured\":{}},\"time\":{\"created\":1760000002500,\"completed\":1760000003000}}],\"time\":{\"created\":1760000002000,\"completed\":1760000003000}}"}}
```

### Confidence

High: drizzle columns and V1/V2 struct fields (read from
source). Medium: V2 `session_message.data` serialised key order and the
`Model.Ref` shape. Not determined: the code path that imports legacy JSON
`storage/` into SQLite ([`packages/opencode/src/storage/db.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/db.ts), not traced).
