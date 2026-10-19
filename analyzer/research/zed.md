# Zed agent thread schema

Catalog agent: `zed`. Covers Zed's built-in agent panel threads. Researched
together with Goose ([goose.md](goose.md)). Paths cited are relative to the
clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/zed.md`](../../collectors/research/zed.md).

## 1. Source

[zed-industries/zed](https://github.com/zed-industries/zed) at [`a84689073d296dfd39987bc7dd478e43ef76d83a`](https://github.com/zed-industries/zed/commit/a84689073d296dfd39987bc7dd478e43ef76d83a); agent
crates GPL-3.0-or-later ([`crates/agent/Cargo.toml:6`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/Cargo.toml#L6),
[`crates/agent_ui/Cargo.toml:6`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/Cargo.toml#L6)). Rust; sqlez (Zed's own SQLite wrapper),
zstd crate, agent-client-protocol-schema 1.9.1.

Sync was checked at [`56934ec`](https://github.com/zed-industries/zed/commit/56934ec0560bce8929025497411de7f5322fb6ca)
on 2026-10-17; the citations in the Sync paragraph of
[section 8](#8-parser-plan) and the clipboard sentence in
[section 6](#6-format-versions) are to that commit.

- **Source review (2026-10-19)**: [zed-industries/zed](https://github.com/zed-industries/zed)
  at [`9cd14da`](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6)
  (the default branch on 2026-10-19), against the schema research at
  [`a846890`](https://github.com/zed-industries/zed/commit/a84689073d296dfd39987bc7dd478e43ef76d83a)
  and the sync check at
  [`56934ec`](https://github.com/zed-industries/zed/commit/56934ec0560bce8929025497411de7f5322fb6ca).
  ACP below is the Agent Client Protocol, the JSON-RPC protocol Zed uses
  to drive an external agent (Claude Agent, Gemini CLI, Codex) as a
  child process. One line per requirement:
  - Permission state: found, mostly not parsed. The thread blob's
    `sandbox_grants` and `profile` are read, as before. Not read: the
    standing rules in `settings.json` under `agent.tool_permissions` and
    `agent.sandbox_permissions`, which Zed itself writes when the user
    picks "Always allow" or "Always deny" on a prompt; the per-project
    trust list in the `trusted_worktrees` table of `db.sqlite`; and each
    external agent's `agent_servers.<id>.default_mode`. Per call, only a
    denial leaves a trace, as an `is_error` tool result whose text names
    the reason; an approval leaves none
    ([section 8](#8-parser-plan)).
  - Model: already covered. The blob still holds one `model`
    (`provider`, `model`) per thread, overwritten on a switch, and no
    message records a model ([section 3](#3-record-schema)).
  - Past use beyond the primary store: found. `db.sqlite` also holds
    unsent draft prompts, the registry of git worktrees Zed created,
    sidebar terminal tabs and, for a thread archived from such a
    worktree, `archived_git_worktrees` rows whose WIP (work in progress)
    commits stay reachable in the main repository under
    `refs/archived-worktrees/<id>`. None is read
    ([section 2](#2-transcript-stores)).
  - Sync, relay and origin: no change from `56934ec`; rating a thread is
    still the only path that sends one, and nothing local records it.
    No other upload at HEAD: not found in zed-industries/zed at
    `9cd14da` (grepped for `share_thread`, `ShareThread`, `sync_thread`,
    `upload_thread` and `cloud_thread`). No relay, no origin.
  - Scratch directories: found, two. On macOS a sandboxed thread gets
    `$TMPDIR/zed-agent-terminal-<random>` (outside the home, recorded in
    the blob as `sandboxed_terminal_temp_dir`), and a thread started in
    a new worktree runs in a linked git worktree (a second checkout made
    with `git worktree add`) that Zed creates beside the project, by
    default `<project parent>/worktrees/<worktree name>/<project>`,
    recorded as the thread's `folder_paths`, with the real project in
    `sidebar_threads.main_worktree_paths`. Neither is marked as scratch
    ([section 8](#8-parser-plan)).
  - Deletion: found ([section 8](#8-parser-plan)). Deleting a thread
    removes its `threads` row and every subagent row under it, its macOS
    temp directory, its `sidebar_threads` row, its draft prompt, and any
    archived-worktree ref nothing else references; an external agent's
    thread is deleted by the agent itself over ACP when it supports that.
  - Version drift: none in the shapes the parser reads. The `threads`
    DDL, blob `version` `0.3.0`, `DbThread`, `DbSandboxGrants`, the
    message enums, `LanguageModelToolUse`, `LanguageModelToolResult` and
    the `sidebar_threads` migrations are unchanged at HEAD; only line
    numbers moved, by one or two. The external agent ids the confidence
    note left open are `gemini`, `claude-acp` and `codex-acp`
    ([section 2](#2-transcript-stores)).
  - Bad lines: no file is read line by line, but three paths stay
    silent: a file that is not SQLite yields nothing, a blob that does
    not decode yields a row not prefixed `parser:`, and a message or
    content item of an unknown variant is skipped
    ([section 8](#8-parser-plan)).

## 2. Transcript stores

`data_dir` is `Library/Application Support/Zed` (macOS), `.local/share/zed`
(Linux), `AppData/Local/Zed` (Windows) ([`crates/paths/src/paths.rs:144-166`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L144-L166)).

| Store | Path | Unit |
| --- | --- | --- |
| Threads database | `<data>/threads/threads.db` | `threads` row = one thread; `data` BLOB = zstd(JSON) of the whole thread including all messages ([`crates/agent/src/db.rs:444-457`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L444-L457),[`535`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L535)) |
| Sidebar metadata | `<data>/db/0-{stable,preview,nightly,dev}/db.sqlite`, table `sidebar_threads` | one row per thread, including external-agent threads ([`crates/db/src/db.rs:138`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/db/src/db.rs#L138),[`166`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/db/src/db.rs#L166); [`release_channel/src/lib.rs:216-223`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/release_channel/src/lib.rs#L216-L223); [`agent_ui/src/thread_metadata_store.rs:1375-1465`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1375-L1465)) |

No separate text-thread or `contexts/*.json` store exists at this commit.

Other per-user stores at
[`9cd14da`](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6),
all in the same `db/0-<channel>/db.sqlite`, since every sqlez domain
(Zed's name for one group of tables with its migrations) opens that file
([`crates/db/src/db.rs:138`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/db/src/db.rs#L138),
[`166`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/db/src/db.rs#L166);
[`crates/db/src/kvp.rs:41`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/db/src/kvp.rs#L41);
[`crates/agent_ui/src/thread_metadata_store.rs:1469`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_metadata_store.rs#L1469);
[`crates/workspace/src/persistence.rs:1078`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/workspace/src/persistence.rs#L1078)).
The parser reads none of them.

| Source | Table and key | What it holds | Survives | Joins on | Plan |
| --- | --- | --- | --- | --- | --- |
| Draft prompts | `scoped_kv_store(namespace, key, value)`, namespace `agent_draft_prompts`, key the sidebar `thread_id` ([`kvp.rs:31-36`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/db/src/kvp.rs#L31-L36); [`agent_ui/src/draft_prompt_store.rs:25-58`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/draft_prompt_store.rs#L25-L58)) | the unsent prompt of a draft thread, a JSON array of ACP content blocks; a draft is a `sidebar_threads` row with `session_id` NULL ([`draft_prompt_store.rs:1-5`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/draft_prompt_store.rs#L1-L5)) | nothing: deleted with the sidebar row ([`thread_metadata_store.rs:1141-1164`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_metadata_store.rs#L1141-L1164)) | `key` to `sidebar_threads.thread_id` | primary: text no other store holds |
| Zed-created worktrees | `scoped_kv_store` namespace `created_git_worktrees`, key `<host>` newline `<worktree path>` (`local` for this machine), value `{created_at_seconds, created_at_subsec_nanos}` ([`git_ui_core/src/created_worktrees.rs:34-73`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/git_ui_core/src/created_worktrees.rs#L34-L73)) | each linked git worktree Zed made for a thread, with its creation time | the thread's deletion; removed only by `forget_created_worktree` ([`created_worktrees.rs:142`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/git_ui_core/src/created_worktrees.rs#L142)) | worktree path to `sidebar_threads.folder_paths` | primary: the scratch marker |
| Archived worktrees | `archived_git_worktrees`, `thread_archived_worktrees` ([section 3](#3-record-schema)) | for a thread archived from a Zed-created worktree: the worktree and main repository paths, the branch, and the staged, unstaged and original commit ids; the worktree directory is removed and the WIP commits stay in the main repository under `refs/archived-worktrees/<id>` ([`agent_ui/src/thread_worktree_archive.rs:77-79`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_worktree_archive.rs#L77-L79), [`499-607`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_worktree_archive.rs#L499-L607)) | the worktree's removal; dropped with the ref when the last thread linked to it is deleted ([`thread_worktree_archive.rs:823-912`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_worktree_archive.rs#L823-L912)) | `thread_archived_worktrees.thread_id` to `sidebar_threads.thread_id` | primary |
| Sidebar terminals | `sidebar_terminal_threads(terminal_id, title, custom_title, created_at, working_directory, folder_paths, folder_paths_order, main_worktree_paths, main_worktree_paths_order, remote_connection)` ([`agent_ui/src/terminal_thread_metadata_store.rs:483-500`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/terminal_thread_metadata_store.rs#L483-L500)) | a terminal tab opened in the threads sidebar: title, start time and working directory, no output | not determined | `folder_paths` | primary, metadata only |
| Native sidebar rows | `sidebar_threads` rows with `agent_id` NULL ([section 3](#3-record-schema)) | title, `title_override`, `archived`, `interacted_at` and `main_worktree_paths` of a native thread | deleted with the thread | `session_id` to `threads.id` | secondary; skipped today, so `archived`, `interacted_at` and `main_worktree_paths` are never shown |

The `trusted_worktrees(trust_id, absolute_path, user_name, host_name)`
table of the same file is permission state, not past use
([section 8](#8-parser-plan)). An external agent's transcript is in no
Zed store: Zed asks the agent to replay it over the ACP `session/load`
request
([`agent_servers/src/acp/v2.rs:1173`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_servers/src/acp/v2.rs#L1173)),
so it lives wherever that agent keeps its sessions. The ids of the three
built-in external agents, the `sidebar_threads.agent_id` values, are
`gemini`, `claude-acp` and `codex-acp`
([`agent_servers/src/custom.rs:17-19`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_servers/src/custom.rs#L17-L19)).

## 3. Record schema

`threads.db` ([`crates/agent/src/db.rs:450-485`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L450-L485)):

```sql
CREATE TABLE threads (id TEXT PRIMARY KEY, summary TEXT NOT NULL, updated_at TEXT NOT NULL,
  data_type TEXT NOT NULL, data BLOB NOT NULL);
ALTER TABLE threads ADD COLUMN parent_id TEXT;
ALTER TABLE threads ADD COLUMN folder_paths TEXT; ALTER TABLE threads ADD COLUMN folder_paths_order TEXT;
ALTER TABLE threads ADD COLUMN created_at TEXT;
```

`id` is the ACP session id, a UUID v4 string ([`thread.rs:1430`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/thread.rs#L1430);
`#[serde(transparent)]` newtype, [`agent-client-protocol-schema-1.9.1/src/v1/mod.rs:48-51`](https://github.com/agentclientprotocol/agent-client-protocol/blob/7e87dc205a7325bd07d0249fd20bb7486ee6ba95/agent-client-protocol-schema/src/v1/mod.rs#L48-L51)).
`parent_id` is the subagent parent ([`db.rs:514-517`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L514-L517)). `summary` is the
title. `updated_at` and `created_at` are `to_rfc3339()`, for example
`2026-01-02T03:04:05.123456789+00:00` ([`db.rs:513`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L513),[`542`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L542)). `folder_paths` is
sorted paths joined by `\n`; `folder_paths_order` is comma-separated display
indices ([`crates/util/src/path_list.rs:130-146`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/util/src/path_list.rs#L130-L146)). `data_type` is `zstd` or
`json` ([`db.rs:363-367`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L363-L367)).

Blob JSON is `DbThread` flattened plus `"version":"0.3.0"`
([`db.rs:53-89`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L53-L89),[`189`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L189),[`505-510`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L505-L510)): `title, messages[], updated_at (RFC 3339 "Z"),
detailed_summary, initial_project_snapshot{worktree_snapshots:[{worktree_path,
git_state:{remote_url, head_sha, current_branch, diff}}], timestamp},
cumulative_token_usage, request_token_usage{<user_msg_id>:{input_tokens,
output_tokens, cache_creation_input_tokens, cache_read_input_tokens}},
model{provider, model}, profile, subagent_context{parent_thread_id, depth},
speed, thinking_enabled, thinking_effort, draft_prompt, ui_scroll_position,
sandboxed_terminal_temp_dir, sandbox_grants{write_paths, network_hosts, ...}`
([`agent.rs:89-93`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/agent.rs#L89-L93); [`project/src/telemetry_snapshot.rs:33-45`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/project/src/telemetry_snapshot.rs#L33-L45);
[`legacy_thread.rs:45-49`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/legacy_thread.rs#L45-L49); [`language_model_core.rs:525-535`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/language_model_core/src/language_model_core.rs#L525-L535)).

`sandbox_grants` is `DbSandboxGrants`, the sandbox escalations the user
approved "for the rest of this thread" (the "Allow for this thread" prompt
option): `write_paths` (granted write paths, each covering its subtree),
`network_hosts` (host patterns such as `*.npmjs.org`), and the booleans
`network_any_host`, `allow_fs_write_all`, `unsandboxed` and
`sandbox_fallback` (commands allowed to run unsandboxed because the OS
sandbox could not be created), all `#[serde(default)]`
([`db.rs:84-122`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L84-L122)). A `write_paths`
entry is a bare path string when no canonical target was resolved (and in
legacy rows), else an object `{requested, resolved, on_windows_fs?}`
([`granted_write_path.rs:64-87`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/settings/src/granted_write_path.rs#L64-L87)).
`profile` is the agent profile id the thread ran under
([`db.rs:69`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L69)).

There are no per-message timestamps, only the thread's `updated_at` and
`created_at` and `initial_project_snapshot.timestamp`. Git branch is
`initial_project_snapshot.worktree_snapshots[].git_state.current_branch`,
captured at thread start.

`messages[]` are externally tagged serde enums with no renames
([`thread.rs:202-208`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/thread.rs#L202-L208),[`287-301`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/thread.rs#L287-L301),[`743-759`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/thread.rs#L743-L759)):

- `{"User":{"id":"<uuid>","content":[{"Text":"..."},{"Mention":{"uri":...,"content":"..."}},{"Image":{"source":"<base64 png>"}}]}}`
- `{"Agent":{"content":[{"Text":"..."},{"Thinking":{"text":"...","signature":null}},{"RedactedThinking":"..."},{"ToolUse":{"id":"toolu_1","name":"terminal","raw_input":"{...}","input":{"type":"json","value":{...}},"is_input_complete":true,"thought_signature":null}}],"tool_results":{"toolu_1":{"tool_use_id":"toolu_1","tool_name":"terminal","is_error":false,"content":[{"Text":"..."}],"output":{...}}},"reasoning_details":null}}`
  ([`language_model_core.rs:592-629`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/language_model_core/src/language_model_core.rs#L592-L629); [`request.rs:67-76`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/language_model_core/src/request.rs#L67-L76),[`148-152`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/language_model_core/src/request.rs#L148-L152); a legacy
  single-value `content` is accepted, [`request.rs:104-145`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/language_model_core/src/request.rs#L104-L145))
- `"Resume"`, `{"Compaction":{"Summary":"..."}}` or `{"Compaction":{"ProviderNative":{...}}}`.

`db.sqlite` → `sidebar_threads` (final shape,
[`thread_metadata_store.rs:1424-1437`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1424-L1437),[`1459-1464`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1459-L1464)):

```sql
CREATE TABLE sidebar_threads(thread_id BLOB PRIMARY KEY, session_id TEXT, agent_id TEXT, title TEXT NOT NULL,
  updated_at TEXT NOT NULL, created_at TEXT, folder_paths TEXT, folder_paths_order TEXT, archived INTEGER DEFAULT 0,
  main_worktree_paths TEXT, main_worktree_paths_order TEXT, remote_connection TEXT) STRICT;
ALTER TABLE sidebar_threads ADD COLUMN interacted_at TEXT; ALTER TABLE sidebar_threads ADD COLUMN title_override TEXT;
CREATE TABLE archived_git_worktrees(id INTEGER PRIMARY KEY, worktree_path TEXT NOT NULL, main_repo_path TEXT NOT NULL,
  branch_name TEXT, staged_commit_hash TEXT, unstaged_commit_hash TEXT, original_commit_hash TEXT) STRICT;
CREATE TABLE thread_archived_worktrees(thread_id BLOB NOT NULL, archived_worktree_id INTEGER NOT NULL
  REFERENCES archived_git_worktrees(id), PRIMARY KEY (thread_id, archived_worktree_id)) STRICT;
```

`thread_id` is 16 raw UUID bytes ([`sqlez/src/bindable.rs:360-370`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/sqlez/src/bindable.rs#L360-L370));
`session_id` equals `threads.id`; `agent_id` NULL means the native Zed Agent,
otherwise an external ACP agent whose transcript is not in `threads.db`
([`thread_metadata_store.rs:1499-1500`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1499-L1500),[`1725-1727`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1725-L1727); [`agent.rs:2742`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/agent.rs#L2742)); times are RFC 3339
([`:1729-1740`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1729-L1740)); `remote_connection` is JSON; `interacted_at` is the last user
send.

## 4. Joins

`sidebar_threads.session_id = threads.id` (plus `threads.parent_id` for
subagents). Tool pairing inside one `Agent` message: `content[].ToolUse.id`
with the `tool_results` key or `tool_use_id`. Project path:
`threads.folder_paths` split on `\n`, fallback
`initial_project_snapshot.worktree_snapshots[].worktree_path`; branch from
`git_state.current_branch` or `archived_git_worktrees.branch_name` through
`thread_archived_worktrees`.

## 5. SQLite and compression

`db.sqlite`: `PRAGMA journal_mode=WAL; synchronous=NORMAL`
([`crates/db/src/db.rs:129-133`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/db/src/db.rs#L129-L133); [`sqlez/src/thread_safe_connection.rs:61-62`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/sqlez/src/thread_safe_connection.rs#L61-L62)),
so collect the `-wal` sidecar. `threads.db` is opened with plain
`Connection::open_file` and no journal pragma ([`sqlez/src/connection.rs:65`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/sqlez/src/connection.rs#L65)),
so it uses the default rollback journal and a `threads.db-journal` may exist
mid-write. Blobs are `zstd::encode_all(json, 3)` / `decode_all`
([`db.rs:178-184`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L178-L184),[`535`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L535),[`660`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L660)): standard zstd frames, no dictionary, content size
present. In Python, `zstandard.ZstdDecompressor().decompress(blob)`, falling
back to `stream_reader` if the size header is missing. Rows with
`data_type='json'` are raw UTF-8. No encryption.

## 6. Format versions

Blob `version` `"0.3.0"` is current ([`db.rs:189`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L189)); `"0.2.0"` and `"0.1.0"`
are `SerializedThread {version, summary, updated_at, messages:[{id:int,
role, segments:[{type:"text",text}|{type:"thinking",text,signature?}|
{type:"RedactedThinking",data}], tool_uses:[{id,name,input}],
tool_results:[{tool_use_id,is_error,content,output}], context, creases,
is_hidden}], initial_project_snapshot, cumulative_token_usage,
request_token_usage:[...], detailed_summary_state, model{provider,model},
profile}` ([`legacy_thread.rs:23-164`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/legacy_thread.rs#L23-L164)); no `version` key means
`LegacySerializedThread` with `messages[].text` ([`:166-205`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/legacy_thread.rs#L166-L205)). Upgrade logic
[`db.rs:195-330`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L195-L330). Shared and exported threads use `SharedThread` version
`"1.0.0"` ([`db.rs:130-141`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L130-L141)). `sidebar_threads` is migrated in place
([`thread_metadata_store.rs:1373-1465`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1373-L1465)); cross-channel import copies rows
between `0-<channel>` databases ([`thread_import.rs`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_import.rs)).

`SharedThread` is used only by the agent panel's two debugging actions,
`CopyThreadToClipboard` (the thread as base64 JSON on the clipboard) and
`LoadThreadFromClipboard` ([`agent_ui.rs:332-335`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/agent_ui.rs#L332-L335);
[`agent_panel.rs:3792-3826`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/agent_panel.rs#L3792-L3826),
[`3852-3929`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/agent_panel.rs#L3852-L3929)); nothing is sent over
the network. A thread loaded that way is saved to `threads.db` under a new
UUID session id ([`agent_panel.rs:3894`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/agent_panel.rs#L3894)), its title
prefixed `🔗 ` and with no `initial_project_snapshot`, `profile` or
`sandbox_grants` ([`db.rs:153-172`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent/src/db.rs#L153-L172)), so the prefix marks a
thread pasted in from elsewhere rather than run on this host.

## 7. Secrets

Blob fields `sandbox_grants.write_paths`/`network_hosts`, `draft_prompt`,
`Mention.content` (inlined file contents), `initial_project_snapshot.git_state.diff`
(full diff), and `remote_connection` (host and user) in `sidebar_threads`. No
API keys were found in thread storage; the collector flags `settings.json`
separately.

## 8. Parser plan

Globs: `{Library/Application Support/Zed,.local/share/zed,AppData/Local/Zed}/threads/threads.db*`
and `.../db/0-*/db.sqlite*`. Requires the `zstandard` package.

Rows: one per message content item and per `tool_results` entry; one
`system` row per `sidebar_threads` entry with `agent_id` set (external agent,
no transcript).

| Column | Source |
| --- | --- |
| timestamp_utc | thread `updated_at` for all messages (approximate); `initial_project_snapshot.timestamp` for the thread-start row |
| session_id | `threads.id` |
| project_path | first of `folder_paths.split("\n")` |
| git_branch | `git_state.current_branch` |
| turn_type | `User.Text/Mention/Image` → user; `Agent.Text` → assistant; `Thinking`/`RedactedThinking` → thinking; `ToolUse` → tool_use; `tool_results[*]` → tool_result; `Resume`/`Compaction` → system |
| model | `model.provider/model.model` |
| tool_name, tool_use_id | `ToolUse.name` / `tool_name`, `ToolUse.id` / `tool_use_id` |
| text | text, `arguments` JSON, result text; `Mention.uri` for mentions |

Model and permission rows (issues 96 and 97), all `system`, after the
thread-start row and before the first message:

- `model: <model.model> provider=<model.provider>` once per thread at the
  thread-start time, from the blob's `model`. The blob holds one `model`
  per thread, so a switch inside a thread is not recorded and there is no
  change row.
- `permission setting: <key>=<value> (thread blob, as of updated_at)`, one
  row per `profile`, per `sandbox_grants.write_paths[]` entry (a string, or
  the object printed as compact JSON), per `sandbox_grants.network_hosts[]`
  entry, and per `sandbox_grants` boolean (`network_any_host`,
  `allow_fs_write_all`, `unsandboxed`, `sandbox_fallback`) that is `true`.
  The grants live in the thread blob, so `session_id` is the thread id and
  `timestamp_utc` the thread's `updated_at` (the blob's last write; the
  moment of the grant is not recorded).

Sync: Zed records no sync state; no thread is synced to the account,
shared by link or kept on a server as a copy of `threads.db`. Thread text
does leave the host in one place beyond the model call: rating a thread.
A thumbs-up or thumbs-down on a native Zed Agent thread (the buttons, or
the `/helpful` and `/not-helpful` commands in the message box,
[`completion_provider.rs:205-210`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/completion_provider.rs#L205-L210)) posts the whole
thread, the `DbThread` that `threads.db` stores, serialised as JSON, with
the session id, parent session id, rating and organisation id to
`/client/feedback/agent_thread`; the comment box that follows a
thumbs-down posts the thread again with the comment to
`/client/feedback/agent_thread_comments` ([`thread_view.rs:69-123`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/conversation_view/thread_view.rs#L69-L123),
[`125-165`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/conversation_view/thread_view.rs#L125-L165); [`cloud_api_client.rs:272-297`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/cloud_api_client/src/cloud_api_client.rs#L272-L297);
[`cloud_api_types.rs:107-123`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/cloud_api_types/src/cloud_api_types.rs#L107-L123); the payload is
[`agent.rs:3552-3567`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent/src/agent.rs#L3552-L3567)). The tooltip says
so: "Rating the thread sends all of your current conversation to the Zed
team" ([`thread_view.rs:7560`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/conversation_view/thread_view.rs#L7560)). It needs a signed-in Zed account
([`cloud_api_client.rs:182-194`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/cloud_api_client/src/cloud_api_client.rs#L182-L194)), happens only on a click, and is
offered while the `agent.enable_feedback` setting is `true`, its default
([`agent.rs:352-355`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/settings_content/src/agent.rs#L352-L355); [`default.json:1294-1295`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/assets/settings/default.json#L1294-L1295)),
unless the organisation's configuration sets
`is_agent_thread_feedback_enabled` false ([`thread_view.rs:7650-7663`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/conversation_view/thread_view.rs#L7650-L7663)).
External ACP agents' threads cannot be rated: only the native connection
implements the `AgentTelemetry` hook that supplies the thread
([`agent.rs:3450-3452`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent/src/agent.rs#L3450-L3452)). Nothing on disk records that a thread was
rated: the rating is held in the view's memory
([`thread_view.rs:63-66`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/conversation_view/thread_view.rs#L63-L66)), `DbThread` has no field for it
([`db.rs:53-89`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent/src/db.rs#L53-L89)), and the request bypasses the telemetry queue, so
it is not in `telemetry.log`. So this is an upload with no local marker,
and no row is proposed. Telemetry (`telemetry.metrics`, default `true`,
[`settings_content.rs:610-633`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/settings_content/src/settings_content.rs#L610-L633)) sends events to
`/telemetry/events` and appends each one to `telemetry.log` in the logs
directory (`Library/Logs/Zed` or `<data>/logs`, recreated empty at every
launch, [`telemetry.rs:214-223`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/client/src/telemetry.rs#L214-L223),
[`284-286`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/client/src/telemetry.rs#L284-L286), [`637-680`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/client/src/telemetry.rs#L637-L680)). The agent panel's
events carry ids, model, status and token counts, not text, for example
`Agent Thread Completion` ([`thread.rs:3039-3049`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent/src/thread.rs#L3039-L3049)); the
inline assistant's `Inline Assistant Rated` event, sent on its thumbs
buttons, carries the prompt, the completion and the selected text
([`inline_prompt_editor.rs:640-651`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/inline_prompt_editor.rs#L640-L651)), so a `telemetry.log` from the
current launch can hold inline-assistant text, never panel-thread text.
`telemetry.diagnostics` (default `true`) uploads crash minidumps (a
process memory snapshot, `*.dmp` beside a `*.json` metadata file in the
logs directory) to Sentry, the crash service, and deletes both once the
upload succeeds ([`reliability.rs:51-54`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/zed/src/reliability.rs#L51-L54),
[`259-295`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/zed/src/reliability.rs#L259-L295)); no thread file is attached, though
the memory image may hold whatever the panel had loaded. The Zed-hosted
model provider receives the thread id with each request
([`thread.rs:4124`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent/src/thread.rs#L4124); [`cloud_llm_client.rs:220-228`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/cloud_llm_client/src/cloud_llm_client.rs#L220-L228)),
which is the model call, not sync. The collaboration server has a
`SharedThreadId` type that nothing uses
([`ids.rs:96-106`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/collab/src/db/ids.rs#L96-L106)), the collaboration protocol has
no thread message (`crates/proto/proto/ai.proto` carries only agent and
context-server commands), and the `remote_connection` column of
`sidebar_threads` is the SSH, WSL or Docker remote-development target
([`remote_client.rs:1361-1367`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/remote/src/remote_client.rs#L1361-L1367)), not a cloud id. Deleting a
thread removes its `threads` row ([`db.rs:703-754`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent/src/db.rs#L703-L754)) and its
`sidebar_threads` row
([`thread_metadata_store.rs:1577`](https://github.com/zed-industries/zed/blob/56934ec0560bce8929025497411de7f5322fb6ca/crates/agent_ui/src/thread_metadata_store.rs#L1577)); a copy
already sent with a rating stays with Zed, and nothing local says so.

Plan lines from the source review of 2026-10-19, at
[`9cd14da`](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6),
one per requirement; none is implemented yet, and every new row rests on
source alone (fixture only):

- **Permission, standing rules (not read).** The user's `settings.json`
  (and a project's `.zed/settings.json`; patterns from every layer add
  up) holds `agent.tool_permissions.default` and, per tool name
  (`terminal`, `edit_file`, `fetch`, `mcp:<server>:<tool>` and so on),
  `tools.<tool>.default` and the regex lists `always_allow`,
  `always_deny` and `always_confirm` of `{pattern, case_sensitive}`,
  with the modes `allow`, `deny` and `confirm`
  ([`crates/settings_content/src/agent.rs:397-412`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/settings_content/src/agent.rs#L397-L412),
  [`1067-1140`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/settings_content/src/agent.rs#L1067-L1140);
  [`assets/settings/default.json:1235-1275`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/assets/settings/default.json#L1235-L1275)),
  and `agent.sandbox_permissions` holds `allow_all_hosts`,
  `network_hosts[]`, `allow_fs_write_all`, `allow_unsandboxed` and
  `write_paths[]` (a path or `{requested, resolved}`)
  ([`agent.rs:1013-1065`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/settings_content/src/agent.rs#L1013-L1065)).
  Zed writes these itself: an "Always allow" or "Always deny" choice on
  a tool prompt (option ids `always_allow:<tool>`, `always_deny:<tool>`,
  `always_allow_mcp:<tool>`, `always_deny_mcp:<tool>`) appends the
  command's sub-patterns to `always_allow` or `always_deny`, or sets the
  tool's `default`
  ([`crates/agent/src/thread.rs:6899-7005`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L6899-L7005)),
  and "Allow always" on a sandbox escalation writes
  `sandbox_permissions`
  ([`thread.rs:6368-6440`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L6368-L6440),
  [`6658-6673`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L6658-L6673)).
  The older boolean `agent.always_allow_tool_actions` is migrated to
  `tool_permissions.default: "allow"` and no longer read
  ([`crates/migrator/src/migrations/m_2026_02_04/settings.rs:7`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/migrator/src/migrations/m_2026_02_04/settings.rs#L7)).
  An external agent's own mode (Claude Agent's permission mode, for
  one) is `agent_servers.<id>.default_mode`
  ([`agent.rs:854-859`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/settings_content/src/agent.rs#L854-L859)).
  Project trust, which gates a project's settings, its language and MCP
  servers and its `.agents/skills`, is one `trusted_worktrees` row per
  trusted path, with `user_name` and `host_name` for a remote host, in
  `db.sqlite`, rewritten whole on every change
  ([`crates/workspace/src/persistence.rs:986-991`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/workspace/src/persistence.rs#L986-L991),
  [`2590-2632`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/workspace/src/persistence.rs#L2590-L2632);
  [`crates/agent/src/agent.rs:1309-1317`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/agent.rs#L1309-L1317)),
  and `session.trust_all_worktrees` (default `false`) skips the check
  ([`crates/settings_content/src/project.rs:498-503`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/settings_content/src/project.rs#L498-L503)).
  Plan: one `permission setting: <key>=<value> (from <file>, file
  mtime)` row per entry of `agent.tool_permissions`,
  `agent.sandbox_permissions`, `agent_servers.<id>.default_mode` and
  `session.trust_all_worktrees`, read from the settings files the
  catalog collects, and one `permission setting:
  trusted_worktrees.<path>=true (from db.sqlite trusted_worktrees, file
  mtime)` row per trusted path, `project_path` the path.
- **Permission, per call (not read).** An approval leaves no record in
  the thread. A denial fails the tool, and the error text becomes the
  `tool_results` entry with `is_error` true
  ([`thread.rs:3958`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L3958),
  [`5501-5512`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L5501-L5512)):
  `Permission to run tool denied by user` for the user's denial
  ([`thread.rs:6905`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L6905)),
  and for an automatic denial by the rules `Blocked by global default:
  deny`, `Command blocked by security rule for <tool> tool`, `<tool>
  tool is disabled` or the built-in `Blocked by built-in security rule`
  ([`crates/agent/src/tool_permissions.rs:12-13`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/tool_permissions.rs#L12-L13),
  [`292-298`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/tool_permissions.rs#L292-L298),
  [`396-430`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/tool_permissions.rs#L396-L430));
  a call cut off by the user is `Tool canceled by user`
  ([`thread.rs:72`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L72)).
  Plan: after such a `tool_result` row, a `permission decision:
  denied` or `permission decision: auto_denied reason=<text>` row with
  the call's `tool_name` and `tool_use_id`, matched on those message
  fragments.
- **Model.** Covered: one `model` per thread, no per-message model and
  no switch record ([section 3](#3-record-schema)).
- **Past use.** The draft prompts, the created-worktree registry, the
  archived worktrees and the sidebar terminals in
  [section 2](#2-transcript-stores) are primary sources the parser does
  not read: a `user` row `draft prompt (unsent): <text>` per draft, at
  the sidebar row's `updated_at`, and the archived-worktree branch and
  commit ids as a `system` row. The native `sidebar_threads` rows are
  secondary; reading them would show `archived` and `interacted_at`.
- **Sync, relay and origin.** No change from the paragraph above: the
  rating upload is the only one and leaves no local mark; the agent
  records no relay and no origin.
- **Scratch directories.** Two, both unmarked today. The macOS
  `$TMPDIR/zed-agent-terminal-<random>` directory, which is the
  terminal's `TMPDIR` and a writable path in the Seatbelt sandbox
  (macOS's per-process sandbox profiles); Linux uses bubblewrap's
  private `/tmp` and Windows the WSL sandbox's, so neither gets one
  ([`thread.rs:1540-1566`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L1540-L1566);
  [`agent.rs:3851-3870`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/agent.rs#L3851-L3870)).
  It sits outside the home, so no catalog line collects it; the blob
  key `sandboxed_terminal_temp_dir` names it. And the Zed-created
  linked worktree: `git.worktree_directory` (default `../worktrees`,
  relative to the repository) plus the worktree name and the project's
  directory name
  ([`crates/project/src/git_store.rs:6332-6349`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/project/src/git_store.rs#L6332-L6349),
  [`10845-10898`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/project/src/git_store.rs#L10845-L10898);
  [`assets/settings/default.json:1885-1901`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/assets/settings/default.json#L1885-L1901)),
  which becomes the thread's `folder_paths`, so the parser reports the
  worktree as the project. Plan: `scratch directory:
  <sandboxed_terminal_temp_dir> (sandbox temp directory)` per thread
  blob that names one, and `scratch directory: <worktree path>
  (Zed-created git worktree of <main_worktree_paths>)` for a thread
  whose `folder_paths` has a `created_git_worktrees` entry, with
  `project_path` the main repository from `main_worktree_paths`.
- **Deletion.** The thread's delete (the archive view's delete, or the
  native connection's `delete_session`) removes the `threads` row, every
  subagent row whose `parent_id` chain leads to it, and the macOS temp
  directory the blob names
  ([`crates/agent/src/db.rs:680-754`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/db.rs#L680-L754);
  [`agent.rs:3613-3625`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/agent.rs#L3613-L3625)),
  then the `sidebar_threads` row and the draft prompt, then the
  archived-worktree rows and their `refs/archived-worktrees/<id>` ref
  once no other thread links to them, and asks an external agent to
  delete its own copy over ACP `session/delete` when the agent offers it
  ([`crates/agent_ui/src/threads_archive_view.rs:814-854`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/threads_archive_view.rs#L814-L854);
  [`crates/agent_servers/src/acp/v1.rs:285-300`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_servers/src/acp/v1.rs#L285-L300)).
  "Delete all" empties `threads`
  ([`db.rs:756-789`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/db.rs#L756-L789)).
  Archiving only sets `sidebar_threads.archived`; for a thread in a
  Zed-created worktree it also removes the worktree directory after
  saving its state as commits
  ([`crates/agent_ui/src/thread_metadata_store.rs:859-878`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_metadata_store.rs#L859-L878)).
  Nothing local records a deletion. Whether the sidebar row of a thread
  removed by "Delete all" outlives it was not determined.
- **Version drift.** None in the shapes read: the `threads` DDL
  ([`db.rs:446-487`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/db.rs#L446-L487)),
  `DbThread` and `DbSandboxGrants`
  ([`db.rs:53-122`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/db.rs#L53-L122)),
  `version` `0.3.0`
  ([`db.rs:189`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/db.rs#L189)),
  the message enums
  ([`thread.rs:202-217`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L202-L217),
  [`287-301`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L287-L301),
  [`743-759`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L743-L759)),
  the tool use and result
  ([`crates/language_model_core/src/language_model_core.rs:593-602`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/language_model_core/src/language_model_core.rs#L593-L602);
  [`crates/language_model_core/src/request.rs:68-76`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/language_model_core/src/request.rs#L68-L76))
  and the `sidebar_threads` migrations
  ([`thread_metadata_store.rs:1372-1465`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_metadata_store.rs#L1372-L1465))
  read as at `a846890`, with line numbers moved by one or two.
- **Bad lines.** The parser reads no file line by line. Three silent
  paths remain: `parse()` returns nothing for a file that is not SQLite
  (the `goose` parser writes `parser: not a SQLite database`); a blob
  that does not decode yields `thread <id> could not be decoded
  (<reason>)`, not a row prefixed `parser:`; and a `messages[]` item, or
  an `Agent` content item, of an unknown variant is skipped without a
  row.

Fixtures. `threads.db` (`data` is the zstd of the JSON below,
`data_type='zstd'`):

```sql
INSERT INTO threads(id,parent_id,folder_paths,folder_paths_order,summary,updated_at,data_type,data,created_at)
VALUES ('6f1c0b2e-1111-4bbb-8ccc-000000000001',NULL,'/home/alice/proj','0','Fix flaky test','2026-03-01T09:01:05.000000000+00:00','zstd',X'<zstd>','2026-03-01T09:00:00.000000000+00:00');
```

```json
{"version":"0.3.0","title":"Fix flaky test","updated_at":"2026-03-01T09:01:05Z",
 "initial_project_snapshot":{"worktree_snapshots":[{"worktree_path":"/home/alice/proj","git_state":{"remote_url":"git@github.com:alice/proj.git","head_sha":"abc123","current_branch":"main","diff":null}}],"timestamp":"2026-03-01T09:00:00Z"},
 "model":{"provider":"anthropic","model":"claude-sonnet-4-5"},
 "messages":[
  {"User":{"id":"9a7d6c5b-2222-4ddd-9eee-000000000002","content":[{"Text":"run the tests"},{"Mention":{"uri":"file:///home/alice/proj/README.md","content":""}}]}},
  {"Agent":{"content":[{"Thinking":{"text":"use pytest","signature":null}},{"ToolUse":{"id":"toolu_01","name":"terminal","raw_input":"{\"command\":\"pytest -q\"}","input":{"type":"json","value":{"command":"pytest -q"}},"is_input_complete":true,"thought_signature":null}},{"Text":"All 3 tests pass."}],
   "tool_results":{"toolu_01":{"tool_use_id":"toolu_01","tool_name":"terminal","is_error":false,"content":[{"Text":"3 passed"}],"output":null}},"reasoning_details":null}},
  "Resume"]}
```

`db.sqlite`:

```sql
INSERT INTO sidebar_threads(thread_id,session_id,agent_id,title,updated_at,created_at,folder_paths,folder_paths_order,archived)
VALUES (randomblob(16),'6f1c0b2e-1111-4bbb-8ccc-000000000001',NULL,'Fix flaky test','2026-03-01T09:01:05+00:00','2026-03-01T09:00:00+00:00','/home/alice/proj','0',0);
INSERT INTO sidebar_threads(thread_id,session_id,agent_id,title,updated_at,folder_paths,folder_paths_order)
VALUES (randomblob(16),'ext-claude-code-sess-1','claude-code','External thread','2026-03-01T10:00:00+00:00','/home/alice/proj','0');
```

Confidence. High: DDL, blob and enum shapes, zstd framing, path derivation,
WAL settings, version handling. Medium: exact `agent_id` strings for
external agents; `MentionUri` variant encoding; legacy `Role` spelling in
0.2.0 blobs.
