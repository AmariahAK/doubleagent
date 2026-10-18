# Crush transcript schema

Catalog agent: `crush`. Crush began as an OpenCode fork
([opencode.md](opencode.md)) but shares no storage code with it any more:
Go, sqlc and goose migrations, one database per project. Paths cited are
relative to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/crush.md`](../../collectors/research/crush.md).

## 1. Source

[charmbracelet/crush](https://github.com/charmbracelet/crush) at [`ca6ae26ce016b980407ce32f012a467ec10c1e2f`](https://github.com/charmbracelet/crush/commit/ca6ae26ce016b980407ce32f012a467ec10c1e2f),
Functional Source License 1.1 with MIT future license ([`LICENSE.md`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/LICENSE.md)). Open
source.

Sync was checked at
[`12f96b4`](https://github.com/charmbracelet/crush/commit/12f96b4acd8f36312befbbf6fe7459da9ca07a72)
on 2026-10-17; the `Sync:` paragraph in
[section 8](#8-parser-plan) cites that commit.

## 2. Transcript stores

Per project: `<project>/.crush/crush.db` ([`internal/config/config.go:25`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/config/config.go#L25)
default `.crush`; [`internal/db/connect.go:93`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/connect.go#L93) `crush.db`). The data
directory is found by walking up from the cwd ([`internal/config/load.go:590-593`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/config/load.go#L590-L593))
and can be overridden by `data_directory` ([`config.go:470`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/config/config.go#L470)). The global
registry `~/.local/share/crush/projects.json` (Windows
`%LOCALAPPDATA%\crush\projects.json`; [`load.go:1259-1278`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/config/load.go#L1259-L1278),
[`internal/projects/projects.go:14`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/projects/projects.go#L14),[`31-33`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/projects/projects.go#L31-L33)) maps each project `path` to its
`data_dir`. One `messages` row per message; parts are a JSON array in the
`parts` column.

## 3. Record schema

[`internal/db/migrations/20250424200609_initial.sql`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/migrations/20250424200609_initial.sql).

`sessions` ([`:4-14`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/migrations/20250424200609_initial.sql#L4-L14) plus ALTERs): `id` (uuid; task sub-sessions use the tool
call id, [`internal/session/session.go:103`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/session/session.go#L103),[`117`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/session/session.go#L117)), `parent_session_id`,
`title`, `message_count`, `prompt_tokens`, `completion_tokens`, `cost`,
`updated_at`, `created_at` (epoch seconds, `strftime('%s','now')`,
[`internal/db/sql/sessions.sql:22-23`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/sql/sessions.sql#L22-L23)), `summary_message_id`, `todos` JSON,
`channel`.

`messages` ([`:47-57`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/migrations/20250424200609_initial.sql#L47-L57) plus ALTERs; [`internal/db/models.go:29-44`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/models.go#L29-L44)): `id`
uuid ([`internal/message/message.go:206`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/message.go#L206)), `session_id`, `role` in
`assistant|user|system|tool` ([`internal/message/content.go:20-27`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L20-L27)), `parts`
JSON, `model`, `provider` ([`20250627000000_add_provider_to_messages.sql`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/migrations/20250627000000_add_provider_to_messages.sql)),
`created_at`, `updated_at`, `finished_at` (seconds, copied from the `finish`
part's `time`, [`message.go:435-439`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/message.go#L435-L439)), `is_summary_message`, `prism_model_id`,
`prism_model_name`, `prism_*_savings`.

`parts` is `[{"type":...,"data":{...}}]` ([`message.go:613-629`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/message.go#L613-L629)). Types and
`data` keys ([`content.go`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go)): `text`: `text`, `hidden?` ([`:70-74`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L70-L74));
`reasoning`: `thinking`, `signature`, `thought_signature`, `tool_id`,
`responses_data`, `started_at`, `finished_at` (seconds; [`:55-63`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L55-L63));
`tool_call`: `id`, `name`, `input` (JSON string), `provider_executed`,
`finished` ([`:109-115`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L109-L115)); `tool_result`: `tool_call_id`, `name`, `content`,
`data` (base64 media), `mime_type`, `metadata`, `is_error` ([`:119-127`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L119-L127));
`finish`: `reason` in `end_turn|max_tokens|tool_use|canceled|error|content_filter|unknown`,
`time` (seconds), `message?`, `details?` ([`:33-49`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L33-L49),[`131-136`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L131-L136));
`shell_command`: `command`, `output`, `exit_code` ([`:142-146`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L142-L146)); `image_url`:
`url`, `detail`; `binary`: untagged Go fields `Path`, `MIMEType`, `Data`
([`:93-97`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/content.go#L93-L97)).

Other tables: `files` (session file snapshots: `path`, `content`,
`version`), `read_files`, `mcp_enabled_servers`, `mcp_disabled_servers`. No
project path, cwd or git branch column anywhere.

## 4. Joins

`messages.session_id → sessions.id`; `sessions.parent_session_id` for
sub-agents. `tool_call` parts live in the assistant message; the result is a
separate `role='tool'` message with a `tool_result` part
([`internal/agent/agent.go:1032-1038`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/agent/agent.go#L1032-L1038)), joined on
`tool_result.data.tool_call_id = tool_call.data.id`. Project path is the
parent directory of the `.crush` holding the database, or `projects.json`
`projects[].path` / `data_dir`.

## 5. SQLite specifics

`journal_mode=WAL` ([`connect.go:20`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/connect.go#L20)) with Go defaults (auto-checkpoint at
1000 pages), so a copy without `crush.db-wal` loses recent messages.
`secure_delete=ON` ([`connect.go:25`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/connect.go#L25)) zeroes deleted rows. Writes are
debounced about 33 ms ([`message.go:21`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/message/message.go#L21)) and serialised on one connection
([`connect.go:142`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/db/connect.go#L142)). No encryption or compression.

## 6. Format versions

Goose migrations only (12 files); no JSON era, no version field;
`goose_db_version` table.

## 7. Secrets

`crush.json` `providers.<name>.api_key` ([`config.go:102`](https://github.com/charmbracelet/crush/blob/ca6ae26ce016b980407ce32f012a467ec10c1e2f/internal/config/config.go#L102)) at
`~/.config/crush/`, `~/.local/share/crush/` and `<project>/.crush/`.
`reasoning.signature` and `thought_signature` are opaque provider blobs. Tool
input and output can contain pasted tokens.

## 8. Parser plan

Globs: `.local/share/crush/projects.json`,
`AppData/Local/crush/projects.json`, project-level `.crush/crush.db{,-wal,-shm}`.

Rows: one per part in `parts`.

| Column | Source |
| --- | --- |
| timestamp_utc | `messages.created_at` (s); tool_call and tool_result use `finished_at` or `finish.time` |
| session_id | `sessions.id` |
| project_path | directory containing `.crush`, or `projects.json` `path` |
| git_branch | empty |
| turn_type | `user`/`assistant` text; `reasoning` → thinking; `tool_call` → tool_use; `tool_result` → tool_result; role `system`, `finish`, `shell_command` → system |
| model | `provider`/`model` (or `prism_model_id`) |
| tool_name, tool_use_id | `data.name`, `data.id` or `data.tool_call_id` |
| text | text, input JSON, output |

Model rows. A `system` row `model: <model> provider=<provider>` precedes
the first message of a session whose `model` (else `prism_model_id`) is
set, and `model: <old> -> <new> provider=<provider>` every later message
of the session whose model or provider differs, with the message's
`created_at`; `tool` messages store an empty model and are skipped. The
research records no permission state for Crush (no approval, denial or
standing grant is named in [section 3](#3-record-schema)), so the parser
emits no permission rows.

Sync: Crush records no sync state. No command shares, exports, publishes
or uploads a session: the subcommands are `run`, `dirs`, `projects`,
`update-providers`, `logs`, `logout`, `schema`, `login`, `stats` and
`session` ([`internal/cmd/root.go:67-78`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/cmd/root.go#L67-L78)), plus `server` and `models`
registered in their own files, and `session` has only `list`, `show`,
`last`, `delete` and `rename` ([`internal/cmd/session.go:34-97`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/cmd/session.go#L34-L97)). No
migration adds a remote id, share URL, synced flag or sync time to any
table (the twelve files under
`internal/db/migrations/`; the newest
`sessions` column, `channel`, is
[`20260921000000_add_channel_to_sessions.sql:2`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/db/migrations/20260921000000_add_channel_to_sessions.sql#L2)).
Searched `share`, `publish`, `upload`, `cloud`, `sync`, `teleport`,
`backup`, `export`, `remote_id`, `share_url`, `synced` and `gist` over the
Go and SQL sources. What does leave the host, besides the model calls:

- Usage telemetry to PostHog (a hosted product-analytics service) at
  `https://data.charm.land` ([`internal/event/event.go:17`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/event/event.go#L17)), on by
  default and off when `CRUSH_DISABLE_METRICS` or `DO_NOT_TRACK` is true or
  `options.disable_metrics` is set in `crush.json`
  ([`internal/cmd/root.go:905-916`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/cmd/root.go#L905-L916),
  [`internal/config/config.go:475`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/config/config.go#L475)). The events are named actions
  (`session created`, `session deleted`, `prompt sent` and others,
  [`internal/event/all.go:24-83`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/event/all.go#L24-L83)); the prompt and token events carry
  the session id, provider, model, reasoning effort, thinking mode, yolo
  mode (the setting that skips permission prompts), token counts and cost,
  never prompt or reply text ([`internal/agent/event.go:26-50`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/agent/event.go#L26-L50)). The
  sender id is a hashed machine id recomputed at each start, not stored
  ([`internal/event/identifier.go:20-28`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/event/identifier.go#L20-L28)), and a Hyper login aliases
  it to the Hyper account's user id
  ([`internal/oauth/hyper/device.go:104-105`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/oauth/hyper/device.go#L104-L105)); a TUI crash or panic
  sends the error type and message ([`internal/event/event.go:100`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/event/event.go#L100),
  [`internal/log/log.go:68`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/log/log.go#L68)). Nothing on disk records what was sent.
- Hyper (Charm's hosted model gateway, `https://hyper.charm.land`,
  [`internal/agent/hyper/provider.go:45`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/agent/hyper/provider.go#L45)) is a model provider; its
  calls are model API calls, not a server copy of the session.
- Client-server mode (`crush server`, the TUI attached with `--host`)
  keeps the database with the server process, on a Unix socket or named
  pipe by default and TCP when asked ([`internal/server/server.go:72-86`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/server/server.go#L72-L86),
  [`internal/cmd/server.go:23`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/cmd/server.go#L23)); it is self-hosted, with no vendor
  service.
- MCP channels ([`internal/agent/tools/mcp/channel.go:20-36`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/agent/tools/mcp/channel.go#L20-L36)) push
  messages from an MCP server into a session; `sessions.channel` names that
  server. The flow is inbound, so it marks no upload.

A session deleted with `crush session delete` or from the TUI is removed
with its messages and file snapshots
([`internal/db/sql/sessions.sql:79-81`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/db/sql/sessions.sql#L79-L81),
[`20250424200609_initial.sql:32`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/db/migrations/20250424200609_initial.sql#L32),
[`20250424200609_initial.sql:56`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/db/migrations/20250424200609_initial.sql#L56)),
`secure_delete` zeroes the freed pages ([`internal/db/connect.go:25`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/db/connect.go#L25)),
and the only other trace is the `session deleted` telemetry event, which
carries no session id ([`internal/session/session.go:173`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/session/session.go#L173),
[`internal/event/all.go:28-30`](https://github.com/charmbracelet/crush/blob/12f96b4acd8f36312befbbf6fe7459da9ca07a72/internal/event/all.go#L28-L30)). The parser plan proposes no sync
row.

Fixture rows:

```sql
INSERT INTO sessions(id,title,message_count,prompt_tokens,completion_tokens,cost,updated_at,created_at) VALUES('6f1c0001','Fix bug',3,10,5,0.01,1760000005,1760000001);
INSERT INTO messages(id,session_id,role,parts,model,provider,created_at,updated_at,finished_at,is_summary_message) VALUES
('m1','6f1c0001','user','[{"type":"text","data":{"text":"list files"}},{"type":"finish","data":{"reason":"stop","time":0}}]','claude-sonnet-4','anthropic',1760000001,1760000001,NULL,0),
('m2','6f1c0001','assistant','[{"type":"tool_call","data":{"id":"call_x1","name":"bash","input":"{\"command\":\"ls\"}","provider_executed":false,"finished":true}},{"type":"finish","data":{"reason":"tool_use","time":1760000003}}]','claude-sonnet-4','anthropic',1760000002,1760000003,1760000003,0),
('m3','6f1c0001','tool','[{"type":"tool_result","data":{"tool_call_id":"call_x1","name":"bash","content":"a.txt","data":"","mime_type":"","metadata":"","is_error":false}},{"type":"finish","data":{"reason":"stop","time":0}}]','','',1760000003,1760000003,NULL,0);
```

`projects.json`: `{"projects":[{"path":"/home/u/repo","data_dir":"/home/u/repo/.crush","last_accessed":"2026-10-01T12:00:00Z"}]}`

Confidence. High: table columns, part JSON field names, timestamp units,
WAL, tool result as a separate message, absence of git branch. Not
determined: `binary` part key casing in shipped builds (inferred from an
untagged Go struct).
