# tabby

Tabby (catalog agent `tabby`) is a self-hosted completion and chat server; transcripts
live on the server host, in its SQLite database and a daily event log.
Editor clients keep none. Paths are in
[`collectors/research/tabby.md`](../../collectors/research/tabby.md).

## 1. Source and evidence

[TabbyML/tabby](https://github.com/TabbyML/tabby) at [`21b29048d7bcf6b94f9f482f2d0fd05efadfd19f`](https://github.com/TabbyML/tabby/commit/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f).
Apache-2.0 outside `ee/`, Tabby Enterprise licence inside; source public.

### Observed

- No real install.

### Source reviews

- **Source review (2026-10-19)**: the repository's HEAD is still
  [`21b2904`](https://github.com/TabbyML/tabby/commit/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f),
  the commit this document cites, so every citation holds. One line per
  requirement class:
  - Permission: none. Tabby's chat and answer engine run no tools on the
    host, so there is no per-call decision or standing grant: `tool_calls`
    and `ToolCall` occur in `crates/` and `ee/` only in a test helper
    (`ee/tabby-webserver/src/service/answer/testutils/mod.rs`), and
    `approv` matches no Rust file.
  - Model: found, not recorded per message. A thread run names its model
    in the request and nothing stores it; the server's `config.toml`
    names the configured models ([Model](#model)).
  - Past use: backups and the event log already covered; found three
    sources the parser does not read: AI-written pages, the IntelliJ
    inline-chat command history and the VS Code inline-edit command
    history ([section 5](#5-other-stores)).
  - Sync, relay and origin: already covered (no upload; share stays on the
    server).
  - Scratch directories: found, `.tabby/repositories/` clones, already
    excluded ([Scratch directories](#scratch-directories)).
  - Deletion: thread delete and the 7-day ephemeral cleanup already
    covered; found the delete of one question and answer pair
    ([What survives a delete](#what-survives-a-delete)).
  - Version drift: none (HEAD is the cited commit).
  - Bad lines: already covered; the event log is read through
    `iter_jsonl` and its errors through `error_rows`.

## 2. Transcript stores

- `.tabby/ee/db.sqlite` (`-wal`, `-shm`), and `.tabby/ee/db.backup-YYYYMMDD.sqlite`
  copies made before each migration
  ([ee/tabby-webserver/src/path.rs:9-15](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/path.rs#L9-L15); [ee/tabby-db/src/lib.rs:189-221](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/lib.rs#L189-L221)).
  Chat threads (`threads`, `thread_messages`), AI-written pages
  (`pages`, `page_sections`), and per-user completion events
  (`user_events`, `user_completions`). Source builds without the `prod`
  feature use `dev-db.sqlite`.
- `.tabby/events/YYYY-MM-DD.json`: JSON Lines, one `LogEntry` per line, a new
  file per UTC day ([crates/tabby/src/services/event.rs:68-93](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby/src/services/event.rs#L68-L93)), no
  retention. Written whether or not the database is in use
  ([ee/tabby-webserver/src/webserver.rs:34-46](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/webserver.rs#L34-L46); [crates/tabby/src/serve.rs:139-152](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby/src/serve.rs#L139-L152)).

### What survives a delete

Deleting a thread (`deleteThread`,
[mod.rs:1529-1540](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/schema/mod.rs#L1529-L1540)) removes the row
([threads.rs:385-391](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L385-L391)) and its messages by cascade
([ee/tabby-db/schema/schema.sql:189](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L189)); a pre-migration backup
taken before the delete keeps the row and its `is_ephemeral` flag
([Shared threads](#shared-threads)). Ephemeral threads untouched for 7 days are
deleted by a background job ([threads.rs:393-430](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L393-L430);
[background_job/db.rs:33-35](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/background_job/db.rs#L33-L35)), so the pre-migration backups and
the event log can hold chats and completions the live database no longer
has.

From the source review of 2026-10-19:

`deleteThreadMessagePair`
([ee/tabby-schema/src/schema/mod.rs:1508](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/schema/mod.rs#L1508))
removes one user message and the assistant answer after it
([ee/tabby-db/src/threads.rs:339-382](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L339-L382)),
leaving the thread; only a pre-migration backup keeps the pair. No writer
deletes a user row (`DELETE FROM users` and `delete_user` grepped in
`ee/tabby-db/src`), although `threads.user_id` cascades
([schema.sql:177](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L177)).
An AI-written page outlives the thread it came from ([Pages](#pages)).

Two files repeat what the live database records; [doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122)
is the rule that parses both and drops the repeats.

The backups: `backup_db` copies the database file byte for byte, named
`db.backup-<UTC date>.sqlite` (`dev-db.backup-` for source builds), only
when a migration is pending
([ee/tabby-db/src/lib.rs:189-221](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/lib.rs#L189-L221)). A backup therefore holds the same
thread ids, message texts, attachments and times as the live database
had on that day, in the schema of the release before the migration (a
pre-0.25 backup keeps its attachments in the old per-kind columns, which
the parser renders the same way). It survives the 7-day deletion of
ephemeral threads and the three-month pruning of `user_events` below;
several backups hold the same threads when nothing deleted them in
between. They join the live database on thread id (`session_id`) and on
text and time exactly.

The event log against `user_events`: the server hands every event to two
loggers through `ComposedLogger`
([crates/tabby-common/src/api/event.rs:133-149](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/api/event.rs#L133-L149);
[ee/tabby-webserver/src/webserver.rs:45-46](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/webserver.rs#L45-L46)): the file
logger, which appends the serialised `LogEntry` to the day's file
([crates/tabby/src/services/event.rs:104-117](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby/src/services/event.rs#L104-L117)), and the database
logger, which writes the same `entry.event`, pretty-printed, to
`user_events` with `entry.ts` as `created_at`
([ee/tabby-webserver/src/service/event_logger.rs:20-127](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/event_logger.rs#L20-L127)). So a
`user_events` row is the same event as a log line, with:

- `created_at` truncated to the second: the millisecond `ts` becomes a
  `%F %X` string
  ([ee/tabby-db/src/user_events.rs:20-42](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/user_events.rs#L20-L42);
  [lib.rs:307-310](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/lib.rs#L307-L310)), under a second from the log line;
- a row only when the log line's `user` decodes to a user row id; the
  `user` field is the id Tabby's GraphQL API (served with the juniper
  library) hands out, the row id encoded with Hashids (a
  reversible integer-to-string encoding, salt `tabby-id-serializer`,
  minimum length 6), and an event with no user is not stored
  ([event_logger.rs:16-18](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/event_logger.rs#L16-L18);
  [ee/tabby-schema/src/dao.rs:556-575](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/dao.rs#L556-L575));
- rows older than three months deleted by the database background job
  ([user_events.rs:77-95](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/user_events.rs#L77-L95);
  [ee/tabby-webserver/src/service/background_job/db.rs:88](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/background_job/db.rs#L88)),
  while the log has no retention.

The log is the fuller record, but the database is the store Tabby reads
back: its user-event service (`UserEventService::list`) queries `user_events`
([ee/tabby-webserver/src/service/user_event.rs:23-37](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/user_event.rs#L23-L37)), and nothing but the
writer opens the events directory
([crates/tabby-common/src/path.rs:52](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/path.rs#L52);
[event.rs:21](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby/src/services/event.rs#L21)). The analyzer also marks whole files, and
the database file holds the threads as well, so the database is primary
and the log secondary. Nothing is lost by it: a log line with no
`user_events` twin (no user, a server run without the database, pruned
after three months) is kept. The rows join on `completion_id`
(`session_id`), `segments.git_url` (`project_path`), the prompt and
choice texts and a time within a second. The `system` rows do not join:
the parser names the owner by the log's encoded id in one and by the
account's email in the other, and the encoded id cannot be resolved to an
email without the database, so both copies of a completion's `system`
row and of a view, select, dismiss or chat-completion event are kept.

The analyzer reads the live database as primary and the backups and the event log as secondary
sources ([Past use and secondary sources](#past-use-and-secondary-sources); see
[Secondary sources](../docs/output.md#secondary-sources)).

## 3. Record schema

### threads

`threads` ([ee/tabby-db/schema/schema.sql:167-178](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L167-L178)): `id` integer,
`is_ephemeral` (sidebar chats start ephemeral,
[ee/tabby-webserver/src/service/thread.rs:123](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/thread.rs#L123)), `user_id`, `created_at`,
`updated_at`, `relevant_questions` (JSON array of strings).

### thread_messages

`thread_messages` ([schema.sql:179-190](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L179-L190)): `id`, `thread_id`, `role`
(`user` or `assistant`, [ee/tabby-schema/src/dao.rs:719-734](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/dao.rs#L719-L734)), `content`
(Markdown; assistant content is appended while streaming,
[ee/tabby-db/src/threads.rs:274](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L274)), `code_source_id`, `attachment` JSON
(`code[]`, `client_code[]`, `doc[]`, `code_file_list`,
[ee/tabby-db/src/attachment.rs:5-10](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/attachment.rs#L5-L10)), `created_at`, `updated_at`. `code[]`
items: `git_url`, `commit`, `language`, `filepath`, `content`,
`start_line`; `client_code[]`: `filepath`, `start_line`, `content`
([attachment.rs:84-100](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/attachment.rs#L84-L100)). Messages alternate roles; two in a row
with the same role are rejected ([threads.rs:150-153](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L150-L153)). No model,
tool calls or thinking are stored.

### user_events

`user_events` ([schema.sql:116-123](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L116-L123)): `user_id`, `kind` in
`completion|chat_completion|select|view|dismiss`
([dao.rs:597-606](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/dao.rs#L597-L606)), `created_at`, `payload` (pretty JSON of the
`Event`, [ee/tabby-webserver/src/service/event_logger.rs:21-25](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/event_logger.rs#L21-L25)).

### Event log line

`LogEntry` ([crates/tabby-common/src/api/event.rs:106-111](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/api/event.rs#L106-L111)):
`user` (server user id or null), `ts` (Unix ms, [:113-120](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/api/event.rs#L113-L120)), `event`, an
externally tagged snake_case enum ([:32-73](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/api/event.rs#L32-L73)): `{"completion":{...}}`
with `completion_id`, `language`, `prompt` (the full prompt sent to the
model), `segments` (`prefix`, `suffix`, `clipboard`, `git_url`,
`declarations[]`, `filepath`, [:81-98](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/api/event.rs#L81-L98)), `choices[]` (`index`, `text`),
`user_agent`; `view`, `select`, `dismiss` with `completion_id`,
`choice_index`, `view_id`, `elapsed`; `chat_completion` is empty
([crates/tabby/src/routes/chat.rs:83](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby/src/routes/chat.rs#L83)).

### Shared threads

Sharing a thread does not upload it anywhere: the
thread stays in this server's database and the share turns it from
ephemeral into persisted. Every thread is created with `is_ephemeral`
true ([ee/tabby-webserver/src/service/thread.rs:120-127](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/thread.rs#L120-L127)),
and the only writer that clears it is the `setThreadPersisted` GraphQL
mutation ([ee/tabby-schema/src/schema/mod.rs:1542-1555](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/schema/mod.rs#L1542-L1555);
[thread.rs:138-143](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/thread.rs#L138-L143)), which runs
`UPDATE threads SET is_ephemeral = ?, updated_at = DATETIME('now')`
([ee/tabby-db/src/threads.rs:125-131](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L125-L131)). The web UI calls it
from the Share button of the answer-engine page and of the chat panel
(the page the IDE extensions embed), then copies a link of the form
`<server>/search/<title slug>-<thread id>` to the clipboard
([ee/tabby-ui/app/search/components/search.tsx:1098-1137](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-ui/app/search/components/search.tsx#L1098-L1137);
[:266-275](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-ui/app/search/components/search.tsx#L266-L275);
[ee/tabby-ui/components/chat/chat-panel.tsx:115-134](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-ui/components/chat/chat-panel.tsx#L115-L134)).
So `is_ephemeral = 0` means the owner shared the thread. A persisted
thread is readable by every user of the server, not only its owner
([ee/tabby-schema/src/policy.rs:31-45](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/policy.rs#L31-L45)), is listed in the home
page's all-threads feed
([ee/tabby-ui/app/(home)/components/thread-feeds/all-threads.tsx:35-42](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-ui/app/%28home%29/components/thread-feeds/all-threads.tsx#L35-L42)),
and is exempt from the 7-day cleanup
([What survives a delete](#what-survives-a-delete)). No column records the
share time or who opened the link: `updated_at` is set at the share and
again whenever `relevant_questions` is rewritten
([threads.rs:108-120](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L108-L120)), so the share happened at or
before it. Nothing unshares a thread: no caller sets `is_ephemeral`
back to true ([thread.rs:140](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/thread.rs#L140) is the only call of
`update_thread_ephemeral`). Deleting a thread is in
[What survives a delete](#what-survives-a-delete).

## 4. Joins and timestamps

`thread_messages.thread_id → threads.id`; `threads.user_id → users.id`
(`users.email`, `users.name` attribute the chat,
[schema.sql:17-30](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L17-L30)). `user_events.payload.completion.completion_id`
joins `user_completions.completion_id` and the `view`/`select`/`dismiss`
events of the same completion. Project identity is the `git_url` and
`filepath` in attachments or `segments`; no local cwd is recorded.
`page_sections.page_id → pages.id` for pages.

Timestamps: SQLite columns are `DATETIME('now')` defaults or
`%F %X` strings, both UTC without zone, `YYYY-MM-DD HH:MM:SS`
([ee/tabby-db/src/lib.rs:307-310](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/lib.rs#L307-L310); [user_events.rs:27-31](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/user_events.rs#L27-L31)).

## 5. Other stores

### SQLite specifics

WAL journal ([lib.rs:165-176](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/lib.rs#L165-L176)); collect `-wal` or lose recent rows.
`thread_messages.attachment` is TEXT JSON written with `JSON_OBJECT`
([threads.rs:159-166](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L159-L166)).
Migrations are sqlx (`_sqlx_migrations`). The 7-day cleanup of ephemeral threads is in
[What survives a delete](#what-survives-a-delete).

### Pages

`pages` and `page_sections`
([schema.sql:267-288](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L267-L288))
are AI-written documents: `pages(author_id, title, content, created_at,
updated_at, code_source_id)` and `page_sections(page_id, title, content,
position, attachment)`. A page is generated from a thread's messages
(`convertThreadToPage`) or from a title prompt the user typed
(`createPageRun`)
([ee/tabby-webserver/src/service/page.rs:92-133](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/page.rs#L92-L133),
[:135-150](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/page.rs#L135-L150)),
and is a row of its own, so it outlives the thread it came from; it is
removed only by `delete_page`
([ee/tabby-db/src/pages.rs:123-124](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/pages.rs#L123-L124)).
It records no thread id, so it joins a thread on `author_id`, text and
time only.

### Editor command histories

Two editor clients keep the user's recent inline-edit instructions,
without times:

- IntelliJ: `intellij-tabby-command-history.xml`, state
  `CommandHistoryState.history`, a list of up to 30 strings, newest first
  ([clients/intellij/.../inlineChat/CommandHistory.kt:5-31](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/intellij/src/main/kotlin/com/tabbyml/intellijtabby/inlineChat/CommandHistory.kt#L5-L31)).
  The service is requested per project
  ([InlineChatIntentionAction.kt:97](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/intellij/src/main/kotlin/com/tabbyml/intellijtabby/inlineChat/InlineChatIntentionAction.kt#L97))
  while its `@Service` annotation names no level, so whether the IDE
  writes the file to its `options/` directory, where the catalog looks,
  or to the project's `.idea/` was not determined from this source.
- VS Code: `edit.recentlyCommand` in the extension's global state, the
  `TabbyML.vscode-tabby` row of `state.vscdb`, a list of JSON-encoded
  commands, newest first, capped by the `chatEdit.history` advanced
  setting (default 20)
  ([clients/vscode/src/Config.ts:115-118](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/vscode/src/Config.ts#L115-L118),
  [:139-145](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/vscode/src/Config.ts#L139-L145),
  [clients/vscode/src/inline-edit/quickPick.ts:344-351](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/vscode/src/inline-edit/quickPick.ts#L344-L351)).
  The catalog attributes `state.vscdb` to `vscode`, so a Tabby reader of
  it needs `reads_agents`.

## 6. Format versions

Migrations under `ee/tabby-db/migrations/`; `thread_messages` arrived in
`0035` ([0035_add-thread-message-table.up.sql](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/migrations/0035_add-thread-message-table.up.sql)), and the separate
`code_attachments`, `client_code_attachments`, `doc_attachments` columns
were deprecated in 0.25 in favour of `attachment`
([threads.rs:34-38](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/src/threads.rs#L34-L38)) and are absent from the current schema. A backup
from before 0.25 can carry attachments only in the old columns. Event log lines have no version.

## 7. Secrets

The database also holds `users.auth_token`, `registration_token.token`,
`refresh_tokens.token`, `integrations.access_token`,
`email_setting.smtp_password`, `oauth_credential.client_secret`,
`ldap_credential.bind_password` (see collectors research,
[section 3](../../collectors/research/tabby.md#3-credentials)).
Redact those columns. Completion prompts and `clipboard` segments can carry
pasted secrets.

## 8. Parser plan

Globs: `.tabby/ee/db.sqlite`, `.tabby/ee/db.backup-*.sqlite`,
`.tabby/ee/dev-db.sqlite`, `.tabby/events/*.json`.

| Column | Source |
| --- | --- |
| timestamp_utc | `thread_messages.created_at`; event log `ts` (ms) |
| session_id | `threads.id`; for completions `completion_id` |
| project_path | `attachment.code[0].git_url` or `segments.git_url`, else empty |
| git_branch | empty |
| turn_type | `role`; completion `prompt` → user, `choices[].text` → assistant; view/select/dismiss → system |
| model | empty (not recorded) |
| tool_name, tool_use_id | empty |
| text | `content`; completion `prompt` and choice text; others the event kind |

Add the thread owner's `users.email` to `text` or a note, since one
server serves many people.

### Permission state

The agent records none (no tool execution; see [Source reviews](#source-reviews)).

### Model

Tabby records no model in the thread or event stores, so the parser yields
no `model:` rows.

From the source review of 2026-10-19: a thread run's `ThreadRunOptionsInput.model_name`
([ee/tabby-schema/src/schema/thread/inputs.rs:73-76](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-schema/src/schema/thread/inputs.rs#L73-L76))
is passed to the chat request
([ee/tabby-webserver/src/service/answer.rs:210](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-webserver/src/service/answer.rs#L210))
and not stored: `thread_messages` has no model column
([schema.sql:179-190](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L179-L190)).
The configured models are in `.tabby/config.toml`: `[model.completion]`,
`[model.chat]` and `[model.embedding]`, each `http` with `model_name`
and `supported_models` or `local` with `model_id`
([crates/tabby-common/src/config.rs:259-263](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/config.rs#L259-L263),
[:302-342](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/config.rs#L302-L342)).
A `system` row per configured model, `model configured: <kind>
<model_name or model_id>`, at the file's modification time and saying
so, is the most the files support; it says which models the server
could use, not which one answered.

### Past use and secondary sources

Sources, primary or secondary (see [What survives a delete](#what-survives-a-delete)):

| File | Role | Time rule |
| --- | --- | --- |
| `.tabby/ee/db.sqlite`, `dev-db.sqlite` | primary | own `created_at` |
| `.tabby/ee/db.backup-*.sqlite`, `dev-db.backup-*.sqlite` | secondary, one leading `system` row naming the file | own `created_at`, identical to the live copy; default 2-second window |
| `.tabby/events/YYYY-MM-DD.json` | secondary | own `ts` in milliseconds, under a second after `user_events.created_at`; default 2-second window |

From the source review of 2026-10-19: `pages` and `page_sections` primary (their own
`created_at`, `session_id` `page:<id>`), and the two command histories secondary with
an empty timestamp (see [section 5](#5-other-stores)).

### Sync, relay and origin

Tabby records no sync state, because it uploads no session to the
vendor; the server is the only store and the share feature stays on it.
A shared thread is marked by `threads.is_ephemeral = 0` (see
[Shared threads](#shared-threads)), which the `thread start` row
already carries by omission (it says `ephemeral` only for an unshared
thread); a row of the form `thread shared: visible to all users of this
server (from db.sqlite, threads.updated_at upper bound)` would make it
explicit, timestamped by nothing of its own, so empty, with the upper
bound in the text. What leaves the host besides model API calls is
usage telemetry, which carries no prompt, reply or thread text:

- The server posts a `ServeHealth` event every 3000 seconds to
  `https://app.tabbyml.com/api/usage`, with the anonymous UUID from
  `.tabby/usage_anonymous_id` as `distinct_id` and the `HealthState`
  (model names, device, CPU, version, webserver flag) as properties; on
  by default, off when `TABBY_DISABLE_USAGE_COLLECTION` is set
  ([crates/tabby-common/src/usage.rs:13-82](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/usage.rs#L13-L82);
  [crates/tabby/src/serve.rs:362-377](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby/src/serve.rs#L362-L377);
  [crates/tabby/src/services/health.rs:12-33](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby/src/services/health.rs#L12-L33)).
- `tabby-agent`, the editor clients' language server, posts
  `AgentInitialized`, `AgentConnected` and `AgentStats` (completion
  counts and latency percentiles) to the same `/usage` endpoint with the
  `anonymousId` from `.tabby-client/agent/data.json`
  ([clients/tabby-agent/src/telemetry.ts:40-121](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/tabby-agent/src/telemetry.ts#L40-L121);
  [clients/tabby-agent/src/codeCompletion/statistics.ts:59-84](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/tabby-agent/src/codeCompletion/statistics.ts#L59-L84)).
  On by default (`anonymousUsageTracking.disable` false,
  [clients/tabby-agent/src/config/default.ts:125-127](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/tabby-agent/src/config/default.ts#L125-L127)), off through
  `[anonymousUsageTracking] disable = true` in the client `config.toml`,
  the editor setting, or the server's security setting
  `disable_client_side_telemetry`
  ([clients/tabby-agent/src/config/index.ts:57-63](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/tabby-agent/src/config/index.ts#L57-L63)), stored in
  `server_setting.security_disable_client_side_telemetry`
  ([schema.sql:64](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L64)). The client logs each send only at
  trace level, and the log level defaults to `silent`
  ([default.ts:119-121](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/tabby-agent/src/config/default.ts#L119-L121)).

No client keeps a server thread id on disk. The VS Code chat webview
keeps the panel's `SessionState` (`threadId`, `qaPairs`, input, context)
in an in-memory `Map` keyed by server endpoint
([clients/vscode/src/chat/webview.ts:91-92](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/vscode/src/chat/webview.ts#L91-L92);
[:529-553](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/clients/vscode/src/chat/webview.ts#L529-L553);
[ee/tabby-ui/lib/types/chat.ts:228-234](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-ui/lib/types/chat.ts#L228-L234)), and the web UI's
persisted `tabby-chat-storage` local-storage entry holds the selected
model and repository but excludes `activeChatId`
([ee/tabby-ui/lib/stores/chat-store.ts:8-48](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-ui/lib/stores/chat-store.ts#L8-L48)). The IntelliJ
plugin does not implement the session-state calls. Searched `share`,
`sync`, `upload`, `cloud`, `export`, `telemetry`, `usage`, `threadId`,
`localStorage`, `globalState` and `https://` in `crates/`, `ee/` and
`clients/`.

No change at the source review of 2026-10-19.

### Scratch directories

`.tabby/repositories/<sanitised git url>/` holds
the clones Tabby makes of remote repositories it indexes
([crates/tabby-common/src/config.rs:198-218](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/crates/tabby-common/src/config.rs#L198-L218)),
excluded by the catalog. The parser's `project_path` is a repository
URL, never a local directory, so no scratch directory can appear as a
project.

### Deletion

No deletion row. A pair deleted with `deleteThreadMessagePair` survives only
in a backup; the backups are already read. See [What survives a delete](#what-survives-a-delete).

### Bad lines

Covered: the event log is read through `iter_jsonl` and its errors through `error_rows`. No
change at the source review of 2026-10-19.

### Fixtures

```sql
INSERT INTO users(id,email,is_admin,auth_token,active,name) VALUES(1,'alice@example.com',1,'auth_REDACT',1,'Alice');
INSERT INTO threads(id,is_ephemeral,user_id,created_at,updated_at,relevant_questions) VALUES(7,0,1,'2026-10-01 10:00:00','2026-10-01 10:00:09','["How is the cache invalidated?"]');
INSERT INTO thread_messages(id,thread_id,role,content,created_at,updated_at,attachment) VALUES
(1,7,'user','Where is the cache cleared?','2026-10-01 10:00:00','2026-10-01 10:00:00','{"code":null,"client_code":[{"filepath":"src/cache.rs","start_line":10,"content":"fn clear()"}],"doc":null}'),
(2,7,'assistant','In `clear()` in src/cache.rs.','2026-10-01 10:00:02','2026-10-01 10:00:09','{"code":[{"git_url":"https://github.com/acme/app","commit":"abc123","language":"rust","filepath":"src/cache.rs","content":"fn clear() {}","start_line":10}],"client_code":null,"doc":null}');
```

```json
{"user":"1","ts":1759312800123,"event":{"completion":{"completion_id":"cmpl-7f3a","language":"python","prompt":"def add(a, b):\n    ","segments":{"prefix":"def add(a, b):\n    ","suffix":"\n","git_url":"https://github.com/acme/app","filepath":"app/math.py"},"choices":[{"index":0,"text":"return a + b"}],"user_agent":"tabby-agent/1.9"}}}
{"user":"1","ts":1759312801500,"event":{"select":{"completion_id":"cmpl-7f3a","choice_index":0,"view_id":"view-1","elapsed":1377}}}
```

### Confidence

High: table and column names, role values, event JSON shape
and `ts` unit, WAL, backups, ephemeral cleanup (source). Medium: the exact
form of `user` in the event log (the Hashids-encoded user row id the database logger decodes, see
[What survives a delete](#what-survives-a-delete); how a request's user reaches the entry was
not traced through the auth middleware). Not determined: `pages` and `page_sections`
content shape beyond `title`/`content` ([schema.sql:267-288](https://github.com/TabbyML/tabby/blob/21b29048d7bcf6b94f9f482f2d0fd05efadfd19f/ee/tabby-db/schema/schema.sql#L267-L288)).
