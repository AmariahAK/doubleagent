# Goose transcript schema

Catalog agent: `goose`. Researched together with Zed ([zed.md](zed.md)); the
two share nothing but Rust and SQLite. Paths cited are relative to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/goose.md`](../../collectors/research/goose.md).

## 1. Source

[block/goose](https://github.com/block/goose) at [`591edd47cf2cfea4957d720c607cf2a4def8673d`](https://github.com/block/goose/commit/591edd47cf2cfea4957d720c607cf2a4def8673d), Apache-2.0. Open
source. Rust; sqlx 0.9.0, rmcp 3.4.1, etcetera 0.11.0, rustyline 18.0.1
([`Cargo.lock`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/Cargo.lock)). Third-party crate sources were read to verify serialisation.

The repository has since moved to
[aaif-goose/goose](https://github.com/aaif-goose/goose) (GitHub redirects
the old name). Sync was checked at
[`bfcc6ee`](https://github.com/aaif-goose/goose/commit/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc)
on 2026-10-17, where the `sessions` schema is at version 17
([`session_manager.rs:32`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/session/session_manager.rs#L32));
every other citation in this document remains at the earlier commit
unless it names the later one.

- **Source review (2026-10-19).** Reviewed
  [aaif-goose/goose](https://github.com/aaif-goose/goose) at HEAD
  [`fb9e3c8`](https://github.com/aaif-goose/goose/commit/fb9e3c89b2b4670a0eded99e7567e578ac6e502c)
  (committed 2026-10-19); the document previously cited
  [`591edd4`](https://github.com/block/goose/commit/591edd47cf2cfea4957d720c607cf2a4def8673d)
  and, for sync, [`bfcc6ee`](https://github.com/aaif-goose/goose/commit/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc).
  `github.com/block/goose` answers with a 301 redirect to
  `github.com/aaif-goose/goose`, so both names are one repository.
  Per requirement class:
  1. Permission state: found. Each answer to a tool confirmation is a
     persisted `actionRequired` block (`actionType`
     `toolConfirmationResponse`, `permission` in `allow_once`,
     `always_allow`, `deny_once`, `always_deny`, `cancel`), the request is
     an `actionRequired` block of `actionType` `toolConfirmation`, and the
     automatic verdict is `_meta` `goose.executable` on the `toolRequest`
     block; standing grants are `.config/goose/permission.yaml` and
     `roaming_trust.json`; see [section 3](#3-record-schema) and
     [Permission files](#permission-files). The parser reads none of
     them as permission rows; the old `permissions/tool_permissions.json`
     store has no caller at HEAD.
  2. Model: already covered (`metadata_json.inference.requestedModel`
     and `resolvedModel`, `model_config_json`, `usage_ledger.model`),
     unchanged at HEAD.
  3. Past use beyond the primary store: already covered for
     `history.txt`; new at HEAD are the project files
     `<data>/projects/<slug>.md` (no session content) and the scheduler's
     `schedule.json` (the job and its current session), neither read; the
     `llm_request` logs keep the last 10 provider calls, which outlive a
     `/clear`, a rewind and a delete; see
     [Deletion and rewrites](#deletion-and-rewrites).
  4. Sync, relay and origin: already covered (the Telegram gateway is
     still the only relay platform; no sync or share command; roaming
     peers leave no per-session mark).
  5. Scratch directories: found, already classed. A gateway session's
     working directory `.config/goose/gateway/<platform>/<user_id>` lies
     under the `.config/goose` catalog entry, so the analyzer's catalog
     rule lists it under `scratch_directories`; the desktop app's
     default working directory is the home itself, and a scheduled job
     runs in the scheduler process's current directory.
  6. Deletion: found; `goose session remove` and the desktop delete drop
     the rows, `/clear` and an edit replace the conversation, a rewind
     deletes the later messages, archive only sets `archived_at`; see
     [Deletion and rewrites](#deletion-and-rewrites).
  7. Version drift: schema version 17 at HEAD (16 at the cited commit,
     additive); every path and key the parser reads is still written;
     the provider crates have moved (`huggingface_auth.rs` now under
     `crates/goose-local-inference`); see [section 6](#6-format-versions).
  8. Bad lines: the legacy JSONL and the request logs go through
     `iter_jsonl` and `error_rows`; a `content_json`, `metadata_json` or
     `model_config_json` that does not parse is its own `parser:` row
     carrying the stored value in full since issue 183 (see
     [section 8](#8-parser-plan)); not observed on any real install,
     source-derived (block/goose at
     [`591edd4`](https://github.com/block/goose/commit/591edd47cf2cfea4957d720c607cf2a4def8673d)).

## 2. Transcript stores

Directories come from etcetera `choose_app_strategy`
([`crates/goose/src/config/paths.rs:22-32`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/config/paths.rs#L22-L32)), which is XDG on Linux and macOS
and the Windows strategy on Windows ([`etcetera-0.11.0/src/app_strategy.rs:151-163`](https://github.com/lunacookies/etcetera/blob/07b3f54999e4f3ff0f027de0144c9349d820ce80/src/app_strategy.rs#L151-L163)).
macOS therefore uses `~/.config/goose`, `~/.local/share/goose` and
`~/.local/state/goose`, not `Library/Application Support` (that catalog entry
covers only the Electron desktop shell). Windows: `AppData/Roaming/Block/goose/{config,data}`;
state has no Windows equivalent and falls back to data ([`paths.rs:32`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/config/paths.rs#L32);
[`etcetera/.../windows.rs:126-165`](https://github.com/lunacookies/etcetera/blob/07b3f54999e4f3ff0f027de0144c9349d820ce80/src/app_strategy/windows.rs#L126-L165)). `GOOSE_PATH_ROOT` overrides to
`$ROOT/{config,data,state}` ([`paths.rs:9-17`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/config/paths.rs#L9-L17)).

| Store | Linux and macOS | Windows | Unit |
| --- | --- | --- | --- |
| Sessions database | `.local/share/goose/sessions/sessions.db` (+`-wal`, `-shm`) | `AppData/Roaming/Block/goose/data/sessions/sessions.db` | `sessions` row = session; `messages` row = one message ([`session_manager.rs:29-30`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L29-L30),[`961-963`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L961-L963)) |
| Legacy sessions | `.local/share/goose/sessions/<YYYYMMDD_HHMMSS>.jsonl` | same directory | line 1 metadata, then one message per line ([`legacy.rs:62-100`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/legacy.rs#L62-L100),[`111`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/legacy.rs#L111)) |
| LLM request log | `.local/state/goose/logs/llm_request.<N>.jsonl` (rotated; temp `llm_request.<uuid>.jsonl`) | `AppData/Roaming/Block/goose/data/logs/` | one file per provider call ([`providers/utils.rs:86`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/providers/utils.rs#L86),[`121-131`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/providers/utils.rs#L121-L131)) |
| CLI history | `.local/state/goose/history.txt` (old `.config/goose/history.txt`) | `AppData/Roaming/Block/goose/data/history.txt` | rustyline V2: `#V2` header, one entry per line, `\n` and `\\` escaped ([`goose-cli/src/session/mod.rs:196-197`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-cli/src/session/mod.rs#L196-L197); [`rustyline-18.0.1/src/history.rs:463-465`](https://github.com/kkawakam/rustyline/blob/cc1aab036d62aff3dbdc681b08949076ec275030/src/history.rs#L463-L465)) |

## 3. Record schema

`sessions.db`, schema version 16 ([`session_manager.rs:28`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L28),[`1012-1098`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1012-L1098)):

```sql
CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE sessions (
  id TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
  user_set_name BOOLEAN DEFAULT FALSE, session_type TEXT NOT NULL DEFAULT 'user',
  working_dir TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, extension_data TEXT DEFAULT '{}',
  total_tokens INTEGER, input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER,
  cache_write_tokens INTEGER, accumulated_total_tokens INTEGER, accumulated_input_tokens INTEGER,
  accumulated_output_tokens INTEGER, accumulated_cache_read_tokens INTEGER,
  accumulated_cache_write_tokens INTEGER, accumulated_cost REAL, schedule_id TEXT, recipe_json TEXT,
  user_recipe_values_json TEXT, provider_name TEXT, model_config_json TEXT,
  goose_mode TEXT NOT NULL DEFAULT 'auto', archived_at TIMESTAMP, project_id TEXT, parent_session_id TEXT);
CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, message_id TEXT, session_id TEXT NOT NULL REFERENCES sessions(id),
  role TEXT NOT NULL, content_json TEXT NOT NULL, created_timestamp INTEGER NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tokens INTEGER, metadata_json TEXT);
CREATE TABLE usage_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  created_timestamp INTEGER NOT NULL, model TEXT, input_tokens INTEGER, output_tokens INTEGER,
  total_tokens INTEGER, cache_read_tokens INTEGER, cache_write_tokens INTEGER, cost REAL,
  cost_source TEXT, is_compaction INTEGER DEFAULT 0);
```

Migration v10 also creates `threads` and `thread_messages` ([`:1462-1487`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1462-L1487))
with no writer; treat as empty. v11 adds `provider_inventory_*` (model
lists, no secrets).

- Timestamp: `messages.created_timestamp` is epoch seconds (`Message::user()`
  uses `Utc::now().timestamp()`, [`goose-provider-types/src/conversation/message.rs:1035`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/message.rs#L1035));
  some clients write milliseconds, normalised with `> 10_000_000_000 → /1000`
  ([`session_manager.rs:31`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L31),[`729-741`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L729-L741)). `messages.timestamp` and
  `sessions.created_at`/`updated_at` are SQLite `CURRENT_TIMESTAMP` text
  `YYYY-MM-DD HH:MM:SS` UTC ([`:1958`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1958)); legacy-imported sessions bind chrono
  values, which sqlx writes as RFC 3339 ([`sqlx-sqlite-0.9.0/src/types/chrono.rs:69`](https://github.com/launchbadge/sqlx/blob/75bc0487eb661da811bb7a3c5d158f1bd463fef4/sqlx-sqlite/src/types/chrono.rs#L69)).
  Order within a second by `id` ([`:1887-1890`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1887-L1890)).
- Session id: `sessions.id` is `YYYYMMDD_<n>` ([`:1633-1647`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1633-L1647));
  `messages.message_id` is `msg_<session_id>_<uuid>` ([`:1941-1943`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1941-L1943)).
- Working directory: `sessions.working_dir`. Git branch: none.
- Model and provider: `sessions.provider_name`, `sessions.model_config_json`
  `{"model_name","temperature","max_tokens","toolshim","toolshim_model",
  "request_params"?,"reasoning"?,"supports_vision"?}`
  ([`goose-provider-types/src/model.rs:41-59`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/model.rs#L41-L59); `request_headers` is
  `#[serde(skip)]`); per message `metadata_json.inference.{provider,
  requestedModel, resolvedModel?, providerSessionId?}` ([`message.rs:768-775`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/message.rs#L768-L775));
  per request `usage_ledger.model`.
- Role: `messages.role` in `user`, `assistant` ([`:720-725`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L720-L725)). `session_type`
  in `user, scheduled, sub_agent, hidden, terminal, gateway, acp` ([`:46-57`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L46-L57)).
- `content_json`: JSON array, `"type"` tag in camelCase ([`message.rs:317-330`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/message.rs#L317-L330)):
  `text` `{"type":"text","text":"...","annotations"?,"_meta"?}` (rmcp
  [`content.rs:23-34`](https://github.com/modelcontextprotocol/rust-sdk/blob/9427a929959e665e0d12e9395f674026baf4bd48/crates/rmcp/src/model/content.rs#L23-L34)); `image` `{"data","mimeType"}`; `document` `{"data",
  "mimeType","name"?}`; `toolRequest` `{"id","toolCall":{"status":"success",
  "value":{"name","arguments":{...}}} | {"status":"error","error":"..."},
  "metadata"?,"_meta"?}` ([`message.rs:131-141`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/message.rs#L131-L141); [`tool_result_serde.rs:7-25`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/tool_result_serde.rs#L7-L25);
  rmcp [`model.rs:4142-4150`](https://github.com/modelcontextprotocol/rust-sdk/blob/9427a929959e665e0d12e9395f674026baf4bd48/crates/rmcp/src/model.rs#L4142-L4150)); `toolResponse` `{"id","toolResult":{"status":
  "success","value":{"content":[{"type":"text","text":..}|{"type":"image",..}|
  resource|resource_link|audio],"structuredContent"?,"isError"?}} |
  {"status":"error","error"}}` ([`message.rs:175-183`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/message.rs#L175-L183); rmcp [`model.rs:3886-3897`](https://github.com/modelcontextprotocol/rust-sdk/blob/9427a929959e665e0d12e9395f674026baf4bd48/crates/rmcp/src/model.rs#L3886-L3897),
  [`content.rs:256-264`](https://github.com/modelcontextprotocol/rust-sdk/blob/9427a929959e665e0d12e9395f674026baf4bd48/crates/rmcp/src/model/content.rs#L256-L264)), with older rows holding a bare content array in
  `value` ([`tool_result_serde.rs:142-145`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/tool_result_serde.rs#L142-L145)); `thinking` `{"thinking",
  "signature"}`; `redactedThinking` `{"data"}`; `toolConfirmationRequest`
  `{"id","toolName","arguments","prompt"}`; `actionRequired`
  `{"data":{"actionType":...}}`; `systemNotification` `{"notificationType",
  "msg","data"?}`; `error` `{"kind","message"}`.
- `metadata_json`: `{"userVisible","agentVisible","inference"?,
  "outputTokenLimitReached"?,"steer"?,"turnContext"?,"usage"?,"operations"?}`
  ([`message.rs:826-854`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/message.rs#L826-L854)).
- `actionRequired.data` (at HEAD
  [`fb9e3c8`](https://github.com/aaif-goose/goose/commit/fb9e3c89b2b4670a0eded99e7567e578ac6e502c),
  and already at the cited commit) is internally tagged on `actionType`
  with four variants
  ([`message.rs:194-219`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-provider-types/src/conversation/message.rs#L194-L219)):
  `toolConfirmation` `{"id","toolName","arguments","prompt"}`, the
  question put to the user before a tool runs; `toolConfirmationResponse`
  `{"id","permission"}`, the answer; `elicitation`
  `{"id","message","requestedSchema"}`, an MCP server's request for
  input (MCP elicitation: a server asks the user to fill a form), and
  `elicitationResponse` `{"id","userData","action"}`. `permission` is
  snake case: `always_allow`, `allow_once`, `cancel`, `deny_once`,
  `always_deny`
  ([`permission.rs:3-11`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-provider-types/src/permission.rs#L3-L11)).
  The request is written as an `assistant` message visible to the user
  only (`userVisible` true, `agentVisible` false)
  ([`ops_tool_approval.rs:116-127`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/ops_tool_approval.rs#L116-L127)),
  and the answer as a `user` message visible to neither, added to
  `messages` the moment the user answers
  ([`tool_confirmation.rs:108-116`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/tool_confirmation.rs#L108-L116)).
  `id` in both is the `toolRequest.id` it governs. A gateway user answers
  by typing `approve`, `approve always`, `deny` or `deny always` in the
  chat, which becomes the same record
  ([`gateway/handler.rs:215-223`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/gateway/handler.rs#L215-L223)).
- `toolRequest._meta` (`tool_meta`) carries `goose.executable`, `true` or
  `false`, the approval step's verdict on the call: `false` for a call
  the permission check denied or held for confirmation, then the value
  the user's answer allows (`allow_once` and `always_allow` give `true`)
  ([`message.rs:133-141`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-provider-types/src/conversation/message.rs#L133-L141);
  [`ops_tool_approval.rs:23`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/ops_tool_approval.rs#L23),
  [`57-76`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/ops_tool_approval.rs#L57-L76),
  [`103-112`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/ops_tool_approval.rs#L103-L112),
  [`271-289`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/ops_tool_approval.rs#L271-L289)).
  A call that runs with no question (mode `auto`, or a tool on an allow
  list) is not marked. A denied, cancelled or refused call is answered
  with a `toolResponse` holding the fixed text that begins `The user has
  declined to run this tool.`
  ([`tool_execution.rs:151`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/tool_execution.rs#L151);
  [`ops_toolcalling.rs:790-799`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/ops_toolcalling.rs#L790-L799)).
- `sessions.goose_mode` is one of `auto` (run every tool call), `approve`
  (ask before every call), `smart_approve` (ask only for calls judged
  sensitive) and `chat` (no tool calls)
  ([`goose_mode.rs:20-32`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-provider-types/src/goose_mode.rs#L20-L32)).
  A mode change rewrites the column in place
  ([`session_manager.rs:1897`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L1897)),
  so only the last mode survives. A scheduled job's session is created
  in `auto`
  ([`scheduler/full.rs:876-882`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/scheduler/full.rs#L876-L882)),
  so its tool calls ran without any confirmation.

## 4. Joins

`messages.session_id = sessions.id`; `usage_ledger.session_id` likewise.
Tool pairing: `toolRequest.id` (assistant row) with `toolResponse.id` (user
row). Project path: `sessions.working_dir`.

CLI history (`history.txt`) to `sessions.db`, on text alone (issue 122).
The CLI adds every input line that is not blank to the rustyline history,
slash commands included, before it decides what the line is
([`goose-cli/src/session/input.rs:193-195`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-cli/src/session/input.rs#L193-L195)),
and sends a prompt as the line with surrounding whitespace trimmed
([`input.rs:210`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-cli/src/session/input.rs#L210)).
The file is saved before the message is added to the session
([`session/mod.rs:786-787`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-cli/src/session/mod.rs#L786-L787)),
so a prompt's history line, stripped, equals the `text` block of its
`messages` row. The line records no time, session id or working directory,
so the only join is the text, against any session of the same user. A
saved history replaces `.config/goose/history.txt` with
`.local/state/goose/history.txt` and deletes the old file
([`session/mod.rs:225-230`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-cli/src/session/mod.rs#L225-L230)),
so both exist only when the save or that deletion failed. No other code at this
commit names `history.txt` (the `ui/` desktop app included), so the file
holds CLI prompts only.

What the history survives: `goose session remove` deletes the session's
`messages`, `usage_ledger` and `sessions` rows
([`commands/session.rs:44-46`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-cli/src/commands/session.rs#L44-L46);
[`session_manager.rs:2302-2315`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L2302-L2315))
and leaves `history.txt` alone, so the prompts of a removed session stay
in it. It does not survive many sessions: the editor is built without a
history size ([`session/mod.rs:648-660`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-cli/src/session/mod.rs#L648-L660)),
so rustyline's default of 100 entries applies and a consecutive repeat is
not added
([`rustyline-18.0.1/src/config.rs:248-251`](https://github.com/kkawakam/rustyline/blob/cc1aab036d62aff3dbdc681b08949076ec275030/src/config.rs#L248-L251);
[`history.rs:264-277`](https://github.com/kkawakam/rustyline/blob/cc1aab036d62aff3dbdc681b08949076ec275030/src/history.rs#L264-L277)).

Gateway pairings to `sessions.db`, on session id (at
[`bfcc6ee`](https://github.com/aaif-goose/goose/commit/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc)).
The gateway is Goose's chat-platform front end: `goose gateway start`
runs a bot (Telegram is the one platform implemented, through
`https://api.telegram.org`) that relays each message from a paired chat
user into a Goose session and sends the reply back to the chat
([`gateway/telegram.rs:13`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/telegram.rs#L13);
[`gateway/handler.rs:451-458`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/handler.rs#L451-L458)).
Pairing a chat user creates one session with `session_type` `gateway`,
`name` `<platform>/<display name or user id>` and `working_dir`
`.config/goose/gateway/<platform>/<user_id>`
([`handler.rs:304-326`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/handler.rs#L304-L326),
[`826-830`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/handler.rs#L826-L830);
[`session_manager.rs:50-61`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/session/session_manager.rs#L50-L61)),
then records the pairing under the `gateway_pairings` key of
`.config/goose/config.yaml`
([`handler.rs:355-363`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/handler.rs#L355-L363);
[`gateway/pairing.rs:11`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/pairing.rs#L11),
[`104-120`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/pairing.rs#L104-L120)).
Each list item is `{platform, user_id, display_name, state}` (strings,
`display_name` may be null), and `state` is internally tagged on its own
`state` key: `{state: unpaired}`, `{state: pending_code, code,
expires_at}` or `{state: paired, session_id, paired_at}`, with
`paired_at` in epoch seconds
([`pairing.rs:15-21`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/pairing.rs#L15-L21);
[`gateway/mod.rs:59-65`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/mod.rs#L59-L65);
[`handler.rs:355`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/handler.rs#L355)).
`state.session_id` equals `sessions.id`. A sample, with the platform id
and name invented:

```yaml
gateway_pairings:
- platform: telegram
  user_id: '123456789'
  display_name: alice
  state:
    state: paired
    session_id: 20261017_4
    paired_at: 1792224000
```

What the pairing survives: unpairing a user and removing a gateway
delete its entries from `gateway_pairings`
([`gateway/manager.rs:175-190`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/manager.rs#L175-L190),
[`331-343`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/manager.rs#L331-L343))
and leave the `gateway` session row, its name and its working directory;
`goose session remove` deletes the rows
([`session_manager.rs:2471-2498`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/session/session_manager.rs#L2471-L2498))
and leaves the `gateway_pairings` entry, which then names a session that
no longer exists. The working directory under `.config/goose/gateway/` is
never removed by either. No gateway code deletes chat messages on the
platform (no `deleteMessage` call in `crates/goose/src/gateway/`), so the
chat copy on Telegram outlives every local delete.

### Deletion and rewrites

At HEAD
[`fb9e3c8`](https://github.com/aaif-goose/goose/commit/fb9e3c89b2b4670a0eded99e7567e578ac6e502c)
the session store loses messages in five ways, and `history.txt` (CLI
prompts only, last 100) and the `llm_request` logs (the last 10 provider
calls, `LOGS_TO_KEEP`,
[`providers/utils.rs:50`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/providers/utils.rs#L50),
rotated at
[`67-75`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/providers/utils.rs#L67-L75))
are the only local copies left after each:

| Action | What it does to `sessions.db` |
| --- | --- |
| `goose session remove`, the desktop app's delete (an ACP `delete_session` request; ACP is the Agent Client Protocol the app speaks to its backend) | deletes the session's `messages`, `usage_ledger` and `sessions` rows ([`commands/session.rs:45`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-cli/src/commands/session.rs#L45); [`acp/server/manage_sessions.rs:88-105`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/acp/server/manage_sessions.rs#L88-L105); [`session_manager.rs:2477-2508`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L2477-L2508)) |
| `/clear` in the CLI | replaces the conversation with an empty one: every `messages` row of the session is deleted, the `sessions` row stays ([`goose-cli/src/session/mod.rs:1059-1077`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-cli/src/session/mod.rs#L1059-L1077); [`session_manager.rs:2149-2160`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L2149-L2160)) |
| `goose session --edit` | rewrites the conversation from an external editor the same way ([`goose-cli/src/cli.rs:2079-2088`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-cli/src/cli.rs#L2079-L2088)); `--fork` copies the session first and edits the copy ([`2069-2075`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-cli/src/cli.rs#L2069-L2075)) |
| a rewind (ACP `truncate_session_conversation`, and `goose term`) | deletes the session's messages from a timestamp or a message id on ([`manage_sessions.rs:168-183`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/acp/server/manage_sessions.rs#L168-L183); [`session_manager.rs:2816-2825`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L2816-L2825)) |
| archive (ACP `archive_session`) | sets `sessions.archived_at` and deletes nothing; unarchive clears it ([`manage_sessions.rs:223-252`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/acp/server/manage_sessions.rs#L223-L252)) |

Compaction is not a loss: it rewrites only the older messages'
`metadata_json` (their visibility) and inserts the summary, so the
compacted turns stay in `messages`
([`session_manager.rs:2198-2240`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L2198-L2240)).
No delete touches `permission.yaml`, `gateway_pairings`, `schedule.json`
or the gateway working directory. Source shows no local record of a
delete, so the analyzer cannot write a `session deleted:` row for Goose.

### Permission files

Standing grants at HEAD, none read by the parser:

| File | Shape | Meaning |
| --- | --- | --- |
| `.config/goose/permission.yaml` (`AppData/Roaming/Block/goose/config/permission.yaml` on Windows), with a `permission.yaml.lock` beside it | a YAML map from category to `{always_allow: [], ask_before: [], never_allow: []}`, each a list of tool names; the categories are `user` (the user's choices) and `smart_approve` (tools the `smart_approve` mode caches as needing a question) ([`config/permission.rs:13`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/config/permission.rs#L13), [`18-33`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/config/permission.rs#L18-L33), [`42-44`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/config/permission.rs#L42-L44), [`169-195`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/config/permission.rs#L169-L195)) | an `always_allow` answer adds the tool to `user.always_allow`, an `always_deny` answer to `user.never_allow` ([`ops_tool_approval.rs:57-70`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/agents/state_machine/ops_tool_approval.rs#L57-L70)); `goose configure` sets any level by hand ([`commands/configure.rs:1913`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-cli/src/commands/configure.rs#L1913)). The file keeps no time and no session, so its modification time is the last change |
| `.config/goose/roaming_trust.json` | JSON `{"allowed": [<peer key>], "revoked_keys": [<peer key>]}` ([`goose-roaming/src/trust.rs:19-26`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-roaming/src/trust.rs#L19-L26); [`commands/roam.rs:40-42`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-cli/src/commands/roam.rs#L40-L42)) | the peer keys allowed to drive this host's agent over roaming (`goose roam`), each with "goose's full ACP surface" ([`trust.rs:1-12`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-roaming/src/trust.rs#L1-L12)) |
| `gateway_configs[].allowed_user_ids` in `.config/goose/config.yaml` | list of chat user ids | the chat users allowed to pair with the gateway ([`gateway/handler.rs:64`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/gateway/handler.rs#L64), [`832-835`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/gateway/handler.rs#L832-L835)); `config.yaml` is a secret glob |

`.config/goose/permissions/tool_permissions.json`, the per-call store
named in
[`collectors/research/goose.md`](../../collectors/research/goose.md)
(records `{tool_name, allowed, context_hash, readable_context, timestamp,
expiry}` keyed `<tool>:<hash of the arguments>`,
[`permission/permission_store.rs:11-20`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/permission/permission_store.rs#L11-L20),
[`45-48`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/permission/permission_store.rs#L45-L48)),
has no writer at HEAD: `record_permission` and `ToolPermissionStore` are
not called outside their own module (grepped for `record_permission` and
`ToolPermissionStore` in `crates/` and `ui/`), so the file exists only
where an older release wrote it.

Other files that record use and are not read: `<data>/schedule.json`, a
JSON list of scheduled jobs `{id, source, cron, last_run,
currently_running, paused, current_session_id, process_start_time,
parameters, recipe_base_dir}`, whose `current_session_id` and
`sessions.schedule_id` join a job to its sessions
([`scheduler/common.rs:93-104`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/scheduler/common.rs#L93-L104),
[`167-187`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/scheduler/common.rs#L167-L187);
[`scheduler/full.rs:80-84`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/scheduler/full.rs#L80-L84));
and `<data>/projects/<slug>.md`, a Markdown file with YAML front matter
(`name`, `description`, and a `workingDirs` list) that groups working
directories under a project name, with no session content
([`sources.rs:69-75`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/sources.rs#L69-L75),
[`258-268`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/sources.rs#L258-L268)).
Neither repeats a transcript.

## 5. SQLite specifics

Opened with `journal_mode=WAL`, `busy_timeout` 30 s, directory mode 0700
([`session_manager.rs:945-955`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L945-L955)). Recent rows live in `sessions.db-wal` until
checkpoint; collect `sessions.db*`. No encryption.

## 6. Format versions

`schema_version` table, `CURRENT_SCHEMA_VERSION=16`; migrations 1-16 are
additive `ALTER TABLE ADD COLUMN` ([`session_manager.rs:1318-1613`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1318-L1613)), so older
databases lack `message_id`, `metadata_json`, `provider_name`,
`model_config_json`, `parent_session_id` and `usage_ledger`. Legacy JSONL
sessions are imported once when `schema_version` is absent
([`:982-989`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L982-L989),[`1145-1250`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/session_manager.rs#L1145-L1250)): line 1 `{"description","id"?,"created_at",
"updated_at","extension_data","message_count","working_dir"?, token fields}`,
then `{"id","role","created","content":[...],"metadata"?}`
([`legacy.rs:62-100`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/legacy.rs#L62-L100),[`128-130`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/legacy.rs#L128-L130)); the file name `YYYYMMDD_HHMMSS` gives the
created time ([`legacy.rs:111`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/legacy.rs#L111)). Imports from Claude Code, Codex and Pi JSONL
also land in `sessions.db` ([`import_formats/mod.rs:1-12`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/session/import_formats/mod.rs#L1-L12)). The catalog
entries `~/.goose` and `.config/Goose` were not found anywhere in the source
at this commit (issue 23).

At HEAD
[`fb9e3c8`](https://github.com/aaif-goose/goose/commit/fb9e3c89b2b4670a0eded99e7567e578ac6e502c)
(2026-10-19) `CURRENT_SCHEMA_VERSION` is 17, `sessions` is still
`sessions/sessions.db` in the data directory
([`session_manager.rs:32-34`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L32-L34)),
and the create statement adds only `system_prompt_override`,
`system_prompt_extras_json` and `container_id` to the columns of
[section 3](#3-record-schema), beside the `thread_id` column that
migration 10 adds
([`1559-1575`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L1559-L1575))
([`session_manager.rs:1141-1175`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L1141-L1175));
`messages` and `usage_ledger` are unchanged
([`1182-1215`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L1182-L1215)),
and `threads` and `thread_messages` still have no writer (no `INSERT INTO
threads` or `INSERT INTO thread_messages` in `crates/`). `session_type`
keeps the same seven values
([`session_manager.rs:52-61`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/session/session_manager.rs#L52-L61)),
the content block tags and `metadata_json.inference` keys are as in
[section 3](#3-record-schema)
([`message.rs:318-329`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-provider-types/src/conversation/message.rs#L318-L329),
[`766-775`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-provider-types/src/conversation/message.rs#L766-L775)),
the history paths are unchanged
([`goose-cli/src/session/mod.rs:197-198`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-cli/src/session/mod.rs#L197-L198)),
and the request logs are still `logs/llm_request.<N>.jsonl` in the state
directory, the last 10 kept. The provider code has been split into
crates of its own (`crates/goose-providers`,
`crates/goose-local-inference`): the Hugging Face token cache is now
written from
[`goose-local-inference/src/huggingface_auth.rs:33`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose-local-inference/src/huggingface_auth.rs#L33)
at the same path. Nothing the parser reads has moved or stopped being
written.

## 7. Secrets

`llm_request.*.jsonl` holds the entire provider request body (system prompt,
all messages, tool outputs) and responses ([`request_log.rs:81-86`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/request_log.rs#L81-L86),[`110-113`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/request_log.rs#L110-L113));
headers and keys are not logged (`ModelConfig.request_headers` is
`#[serde(skip)]`, [`model.rs:58-59`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/model.rs#L58-L59)). Credentials live in the keyring or
`.config/goose/secrets.yaml` ([`config/base.rs:89-91`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/config/base.rs#L89-L91),[`394`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose/src/config/base.rs#L394)). `recipe_json` and
`user_recipe_values_json` can carry user-entered parameters.

The gateway keeps its platform configuration, the Telegram bot token
included, as the secret `gateway_platform_config_<type>` (keyring or
`secrets.yaml`) and only `{gateway_type, max_sessions, allowed_user_ids}`
under `gateway_configs` in `config.yaml`
([`gateway/manager.rs:15-28`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/gateway/manager.rs#L15-L28)).
The `gateway_pairings` sync marker ([section 4](#4-joins)) also lives in
`config.yaml`, which the collector flags as a secret, so a `--no-secrets`
collection loses it. The Langfuse keys (`LANGFUSE_PUBLIC_KEY`,
`LANGFUSE_SECRET_KEY`) are read from the environment only
([`tracing/langfuse_layer.rs:154-172`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/tracing/langfuse_layer.rs#L154-L172)).

## 8. Parser plan

Globs: `.local/share/goose/sessions/sessions.db*`,
`.local/share/goose/sessions/*.jsonl`,
`.local/state/goose/logs/llm_request.*.jsonl`,
`.local/state/goose/history.txt`, `.config/goose/history.txt`,
`AppData/Roaming/Block/goose/data/sessions/sessions.db*`,
`AppData/Roaming/Block/goose/data/logs/llm_request.*.jsonl`,
`AppData/Roaming/Block/goose/data/history.txt`.

Rows: one per `content_json` block, plus one `system` row per session from
`sessions`.

Sources (issue 122): `sessions.db` is the primary store, and the legacy
JSONL sessions and the `llm_request` logs are read as primary records.
Both `history.txt` files are secondary sources: one `user` row per entry,
with an empty `timestamp_utc`, `session_id` and `project_path`, which
`dedup.deduplicate` drops when a database `user` row of the same user has
the same text and keeps otherwise (a removed session's prompt, a slash
command). See [section 4](#4-joins).

| Column | Source |
| --- | --- |
| timestamp_utc | `created_timestamp` (divide by 1000 if above 1e10) |
| session_id | `messages.session_id` |
| project_path | `sessions.working_dir` |
| git_branch | empty |
| turn_type | role `user` → user; `assistant` text → assistant; `toolRequest` → tool_use; `toolResponse` → tool_result; `thinking`/`redactedThinking` → thinking; `systemNotification`/`error`/`actionRequired` → system |
| model | `metadata_json.inference.requestedModel`, else `model_config_json.model_name` prefixed with `provider_name/` |
| tool_name | `toolCall.value.name` (responses look the name up by id) |
| tool_use_id | `toolRequest.id` / `toolResponse.id` |
| text | text, `arguments` JSON, result text |

Model and permission rows (issues 96 and 97), all `system`, from
`sessions.db`:

- `model: <model_config_json.model_name> provider=<provider_name>` after
  each session's start row, at `created_at`.
- `model: <old> -> <new> provider=<inference.provider>` before the rows of
  a message whose `metadata_json.inference.resolvedModel` (else
  `requestedModel`) differs from the session's current model, with
  ` requested=<requestedModel>` when the two differ. User messages carry no
  `inference` and change nothing.
- `permission mode: <goose_mode>` after each session's start row;
  `goose_mode` is one value per session row (default `auto`), so there is
  no change row.
- The answer to a tool confirmation is recorded (corrected by the
  source review of 2026-10-19, and already so at
  [`591edd4`](https://github.com/block/goose/commit/591edd47cf2cfea4957d720c607cf2a4def8673d)):
  an `actionRequired` block of `actionType` `toolConfirmationResponse`
  ([section 3](#3-record-schema)). The parser does not yet turn it into a
  `permission decision:` row; it writes the generic `action required:
  <compact JSON>` row with no `tool_use_id`, and the request keeps its
  `confirmation requested:` row (older `toolConfirmationRequest` blocks)
  or the same generic row (`actionType` `toolConfirmation`). The standing
  grants in `permission.yaml` and `roaming_trust.json` now have a
  recorded shape ([Permission files](#permission-files)) and are not
  read.
- The legacy JSONL sessions record no model and the request log has no
  session id, so neither yields model rows.

Sync: the one session that leaves the host with a local marker is a
gateway session, whose whole conversation is relayed through the
Telegram bot and stays in that chat on Telegram's servers. The marker is
the `gateway_pairings` entry in `.config/goose/config.yaml`
(`AppData/Roaming/Block/goose/config/config.yaml` on Windows), written once
when the chat user pairs and removed on unpair or gateway removal, plus
the session's own `session_type` `gateway`, which survives the unpair
([section 4](#4-joins)). A relayed chat is a copy on the messaging
platform, not a vendor sync, so the parser leaves `records_sync` off and
reads `sessions.db` rather than the pairing: one `system` row after each
`gateway` session's start row, at the session's `created_at`,
`session relayed: gateway <platform> user <user_id> display <display or
-> (from sessions.db session_type gateway, created_at)`, the platform
and user id taken from `working_dir`
(`.config/goose/gateway/<platform>/<user_id>`), the display from `name`
(`<platform>/<display name or user id>`, `-` when it is the user id).
The `gateway_pairings` entry repeats the platform and user id and adds
`paired_at`, but it is nested YAML, which the analyzer has no dependency
to read, inside `config.yaml`, which is a secret glob, so it is not read;
the session row survives an unpair, which deletes the entry, and is
present with `--no-secrets`. A session deleted with `goose session
remove` leaves only its pairing entry, naming a missing session id, and
so yields no row. Fixture only: no real install has shown a gateway
session. Nothing else at
[`bfcc6ee`](https://github.com/aaif-goose/goose/commit/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc)
uploads a session to a Goose or Block account; what was read:

- `goose session export` writes Markdown, JSON, YAML or HTML to a local
  file or stdout and records nothing
  ([`goose-cli/src/cli.rs:558-578`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose-cli/src/cli.rs#L558-L578);
  [`commands/session.rs:293-334`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose-cli/src/commands/session.rs#L293-L334)).
  No share, sync, cloud, upload or publish command exists in the CLI's
  command list, and the desktop app's former share feature is gone (no
  `shareUrl`, `share_url` or `BASE_URL_SHARE` in `crates/` or `ui/`).
- The `sessions` table at schema version 17 has no remote, share or sync
  column; its columns beyond those in [section 3](#3-record-schema) are
  local (`thread_id`, `system_prompt_override`, `system_prompt_extras_json`, and
  `container_id`, a local Docker container for extensions)
  ([`session_manager.rs:1140-1174`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/session/session_manager.rs#L1140-L1174),
  [`1560-1575`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/session/session_manager.rs#L1560-L1575),
  [`1728-1749`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/session/session_manager.rs#L1728-L1749)).
- Telemetry goes to PostHog (a product-analytics service) only after the
  user opts in (`GOOSE_TELEMETRY_ENABLED: true` in `config.yaml`;
  `GOOSE_TELEMETRY_OFF` forces it off) and carries counts, versions,
  provider, model, extension names and a pattern-redacted error message,
  never prompt or reply text
  ([`posthog.rs:16-52`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/posthog.rs#L16-L52),
  [`389-450`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/posthog.rs#L389-L450),
  [`530-536`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/posthog.rs#L530-L536));
  its only local file is `telemetry_installation.json` (an installation
  id, first-seen time and session count) in the state directory
  ([`posthog.rs:97-114`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/posthog.rs#L97-L114)).
  The desktop app's own analytics send nothing at this commit
  ([`ui/desktop/src/utils/analytics.ts:1-18`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/ui/desktop/src/utils/analytics.ts#L1-L18)),
  and its bug-report button opens a GitHub issue form with system details
  only
  ([`Diagnostics.tsx:185-191`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/ui/desktop/src/components/ui/Diagnostics.tsx#L185-L191)).
- Tracing uploads content with no local marker. Langfuse (an LLM tracing
  service, self-hosted or cloud) is enabled by `LANGFUSE_PUBLIC_KEY` and
  `LANGFUSE_SECRET_KEY` in the environment, default URL
  `http://localhost:3000`
  ([`langfuse_layer.rs:13`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/tracing/langfuse_layer.rs#L13),
  [`154-172`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/tracing/langfuse_layer.rs#L154-L172));
  OTLP (the OpenTelemetry protocol) export by `OTEL_EXPORTER_OTLP_ENDPOINT`
  or `otel_exporter_otlp_endpoint` in `config.yaml`, with the host and user
  name as resource attributes
  ([`otel/otlp.rs:224-283`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/otel/otlp.rs#L224-L283)).
  Both are off by default, and prompt, reply and message text enter the
  spans only when `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` is
  `true`
  ([`agents/gen_ai_telemetry.rs:9-14`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/agents/gen_ai_telemetry.rs#L9-L14);
  [`agents/agent.rs:988-994`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/agents/agent.rs#L988-L994);
  [`agents/reply_parts.rs:272-277`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/agents/reply_parts.rs#L272-L277)).
  An endpoint in `config.yaml` is the only trace on disk; the environment
  variables leave none. No row is proposed.
- Roaming (`goose roam`) is peer-to-peer remote control, not an upload:
  `roam share` serves this host's agent over ACP (the Agent Client
  Protocol) through iroh relays (a peer-to-peer QUIC library) to peers
  whose keys were accepted, and the sessions they drive stay in this
  host's `sessions.db`; `roam connect`, `delegate` and `bridge` drive a
  peer's agent, whose sessions stay on the peer
  ([`goose-roaming/src/lib.rs:1-24`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose-roaming/src/lib.rs#L1-L24);
  [`commands/roam.rs:157-197`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose-cli/src/commands/roam.rs#L157-L197)).
  The local record is `roaming_directory.json` in the state directory,
  one entry per peer with `endpoint_id`, `label`, `direction` (`inbound`
  or `outbound`), `agent_id`, `first_seen_ms`, `last_seen_ms` and
  `connected`, beside `roaming_peers.json` and `roaming_trust.json` in the
  config directory
  ([`roam.rs:36-46`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose-cli/src/commands/roam.rs#L36-L46);
  [`goose-roaming/src/directory.rs:17-44`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose-roaming/src/directory.rs#L17-L44)).
  It names no session id, so it is not a sync marker; a session hosted
  for a peer has `session_type` `acp` unless the client names itself
  ([`acp/server/new_session.rs:275-285`](https://github.com/aaif-goose/goose/blob/bfcc6ee6f1ee18d0c4c852a65c49b25f87ee40dc/crates/goose/src/acp/server/new_session.rs#L275-L285)).

Per requirement class, from the source review at
[`fb9e3c8`](https://github.com/aaif-goose/goose/commit/fb9e3c89b2b4670a0eded99e7567e578ac6e502c)
(2026-10-19); none of these rows is written yet:

- Permission, per call: a `system` row `permission decision: <permission>
  (toolConfirmationResponse)` for each `actionRequired` block of
  `actionType` `toolConfirmationResponse`, at the message's
  `created_timestamp`, `tool_use_id` the block's `id` and `tool_name`
  looked up from the `toolRequest` with that id; a `permission request:
  <toolName> <prompt> <arguments>` row for `actionType`
  `toolConfirmation` with the same join; and, for a `toolRequest` whose
  `_meta` holds `goose.executable` `false` with no answer in the
  session, `permission decision: not executable (goose.executable=false)`
  beside its `tool_use` row. Primary store.
- Permission, standing: one `permission setting: <category>.<level>=<tool>
  (from permission.yaml, file mtime)` row per entry of `permission.yaml`
  and `permission setting: roaming_trust.<allowed or revoked_keys>=<key>
  (from roaming_trust.json, file mtime)` per peer key, with an empty
  `session_id`. `permission.yaml` is plain YAML of lists of strings,
  which a small reader handles without a YAML dependency;
  `gateway_configs[].allowed_user_ids` stays unread with the rest of
  `config.yaml` (secret glob, nested YAML).
- Model: covered by the rows above; no change at HEAD.
- Past use: `history.txt` (secondary) covered; `schedule.json` would add
  one `system` row per job, `scheduled job: <id> cron <cron> source
  <source> paused=<paused> last_run=<last_run>` at the file's
  modification time, joined to its session by `current_session_id`
  (a configuration record, neither primary nor secondary);
  `projects/<slug>.md` holds no session content and needs no row.
- Sync, relay and origin: covered (`session relayed:` for `gateway`
  sessions); the agent records no sync and no origin (grepped for
  `shareUrl`, `share_url` and `BASE_URL_SHARE` in `crates/` and
  `ui/desktop/src`, and the Telegram factory is still the only gateway,
  [`gateway/mod.rs:95-100`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/crates/goose/src/gateway/mod.rs#L95-L100)).
- Scratch directories: no parser row needed; the gateway working
  directory is classed by the catalog rule, and the desktop app's
  default working directory is the home
  ([`ui/desktop/src/utils/workingDir.ts:55-59`](https://github.com/aaif-goose/goose/blob/fb9e3c89b2b4670a0eded99e7567e578ac6e502c/ui/desktop/src/utils/workingDir.ts#L55-L59)).
- Deletion: the agent records no delete, so there is no `session
  deleted:` row; `sessions.archived_at` is already on the session start
  row (`archived=`).
- Bad lines: the legacy JSONL and request logs are covered by
  `iter_jsonl` and `error_rows`; `history.txt` cannot fail to decode (each
  line is a row). In `sessions.db` (issue 183) a `content_json`,
  `metadata_json` or `model_config_json` that does not decode, or decodes
  to another type than Goose writes (an array for `content_json`
  ([`message.rs:317-330`](https://github.com/block/goose/blob/591edd47cf2cfea4957d720c607cf2a4def8673d/crates/goose-provider-types/src/conversation/message.rs#L317-L330)),
  an object for the other two), is one `system` row through
  `error_rows`: `parser: unparseable record <N> (<table>.<column>:
  <reason>): <stored value>`, the stored text in full, `<N>` the
  `messages.id` or the `sessions` rowid (also `source_line`), with the
  session's `session_id` and `working_dir` and an empty `timestamp_utc`.
  A NULL or empty `content_json` gives the row with reason `empty` and no
  value. The rest of the session is still yielded: a bad
  `model_config_json` row follows the session start row and the session
  has no `model:` row; a bad `metadata_json` row precedes the message's
  content rows, which keep the session's model and count as visible; a
  bad `content_json` row stands in for the message's rows. Not observed
  on any real install, source-derived (block/goose at
  [`591edd4`](https://github.com/block/goose/commit/591edd47cf2cfea4957d720c607cf2a4def8673d)).

Fixture:

```sql
INSERT INTO schema_version(version) VALUES (16);
INSERT INTO sessions(id,name,session_type,working_dir,created_at,updated_at,extension_data,provider_name,model_config_json,goose_mode)
VALUES ('20260301_1','Fix flaky test','user','/home/alice/proj','2026-03-01 09:00:00','2026-03-01 09:01:05','{}','anthropic',
 '{"model_name":"claude-sonnet-4-5","temperature":null,"max_tokens":null,"toolshim":false,"toolshim_model":null}','auto');
INSERT INTO messages(message_id,session_id,role,content_json,created_timestamp,metadata_json) VALUES
('msg_20260301_1_a1','20260301_1','user','[{"type":"text","text":"run the tests"}]',1772355600,'{"userVisible":true,"agentVisible":true}'),
('msg_20260301_1_a2','20260301_1','assistant','[{"type":"toolRequest","id":"call_1","toolCall":{"status":"success","value":{"name":"developer__shell","arguments":{"command":"pytest -q"}}}}]',1772355601,
 '{"userVisible":true,"agentVisible":true,"inference":{"provider":"anthropic","requestedModel":"claude-sonnet-4-5"}}'),
('msg_20260301_1_a3','20260301_1','user','[{"type":"toolResponse","id":"call_1","toolResult":{"status":"success","value":{"content":[{"type":"text","text":"3 passed"}]}}}]',1772355603,'{"userVisible":true,"agentVisible":true}'),
('msg_20260301_1_a4','20260301_1','assistant','[{"type":"thinking","thinking":"all green","signature":"sig"},{"type":"text","text":"All 3 tests pass."}]',1772355605,'{"userVisible":true,"agentVisible":true}');
INSERT INTO usage_ledger(session_id,created_timestamp,model,input_tokens,output_tokens,total_tokens) VALUES ('20260301_1',1772355605,'claude-sonnet-4-5',120,30,150);
```

Legacy `20260301_090000.jsonl`:

```jsonl
{"description":"old chat","working_dir":"/home/alice/old","created_at":"2026-03-01T09:00:00Z","updated_at":"2026-03-01T09:00:10Z","extension_data":{},"message_count":1}
{"id":"m1","role":"user","created":1772355600,"content":[{"type":"text","text":"hello"}]}
```

`llm_request.0.jsonl`: `{"model_config":{"model_name":"gpt-4.1"},"input":{"model":"gpt-4.1","messages":[{"role":"user","content":"hello"}]}}` then `{"data":{"role":"assistant","created":1772355601,"content":[{"type":"text","text":"hi"}]},"usage":{"input_tokens":5,"output_tokens":1}}`.

Confidence. High: DDL, content and metadata field names, path derivation,
WAL, version handling. `LOGS_TO_KEEP` is 10 at HEAD
([Deletion and rewrites](#deletion-and-rewrites)). Not determined: whether Goose desktop writes millisecond timestamps (only the
normaliser proves that some client does).
