# kiro

The catalog agent `kiro` covers the Kiro CLI (formerly the open-source Amazon Q Developer CLI)
and the Kiro IDE, a VS Code fork. Evidence levels below are L1 (source or shipped binary), L2
(kiro.dev documentation), L3 (vendor issue tracker) and L4 (community source). How the
transcripts are encoded and how the parser reads them is in
[`analyzer/research/kiro.md`](../../analyzer/research/kiro.md).

## 1. Source and evidence

- L1 source: [aws/amazon-q-developer-cli](https://github.com/aws/amazon-q-developer-cli) at [`15cc8f3cd18c4272925ce1c7053268eedff1ea0a`](https://github.com/aws/amazon-q-developer-cli/commit/15cc8f3cd18c4272925ce1c7053268eedff1ea0a) (2026-04-23), [`crates/chat-cli/src/util/paths.rs`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs), [`database/mod.rs`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/mod.rs), [`database/sqlite_migrations/`](https://github.com/aws/amazon-q-developer-cli/tree/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/sqlite_migrations), [`cli/chat/conversation.rs`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/conversation.rs). Cited as `Q paths.rs:N`.
- L1 binary strings: Kiro CLI 2.27.1, `kirocli-x86_64-linux.zip` from
  `desktop-release.q.us-east-1.amazonaws.com/latest/` (BUILD_HASH 7c1a246f, 2026-10-02), extracted
  to `scratchpad/npm/kiro/kirocli/`. `bin/kiro-cli-chat` is the agent (crate `chat-cli-v2`);
  `bin/kiro-cli` is the autocomplete shell wrapper. Strings in
  `scratchpad/npm/kiro/chat-strings.txt`.
- L2 kiro.dev docs: `reference/settings`, `configuration`, `permissions`,
  `cli/chat/session-management`, `cli/v3/new-features`, `mcp/configuration`,
  `custom-agents/configuration-reference`, `steering`, `hooks`, `powers`,
  `upgrade-guides/migrating-from-q`, `getting-started/authentication`.
- L3 [kirodotdev/Kiro](https://github.com/kirodotdev/Kiro) issues [11282](https://github.com/kirodotdev/Kiro/issues/11282), [5727](https://github.com/kirodotdev/Kiro/issues/5727), [9977](https://github.com/kirodotdev/Kiro/issues/9977), [6780](https://github.com/kirodotdev/Kiro/issues/6780), PR [5755](https://github.com/kirodotdev/Kiro/pull/5755).
- L4 community source: [junhoyeo/tokscale](https://github.com/junhoyeo/tokscale) `sessions/kiro.rs`, [getagentseal/codeburn](https://github.com/getagentseal/codeburn) `docs/providers/kiro.md`, wakatime-cli `pkg/ai/kiro.go`, [hnewcity/KiroaaS](https://github.com/hnewcity/KiroaaS) `main.rs`, Kiro IDE `product.json` copy in [Bad3r/dotfiles](https://github.com/Bad3r/dotfiles).

### Observed

No real install.

### Source reviews

- **Source review (2026-10-19)**: HEAD of aws/amazon-q-developer-cli is still [`15cc8f3`](https://github.com/aws/amazon-q-developer-cli/commit/15cc8f3cd18c4272925ce1c7053268eedff1ea0a), the commit cited here, so the open-source paths have not moved; every Kiro CLI path still rests on the 2.27.1 binary and the kiro.dev documentation. One line per class, detail in [section 3 of `analyzer/research/kiro.md`](../../analyzer/research/kiro.md#3-record-schema) and [section 8 of `analyzer/research/kiro.md`](../../analyzer/research/kiro.md#8-parser-plan):
  - Permission: found. Standing grants in `.aws/amazonq/cli-agents/*.json` and
    `.amazonq/cli-agents/*.json` (`allowedTools`, `toolsSettings`), both collected
    ([section 2](#2-per-user-storage)).
  - Model: `model` in the same agent files and `chat.defaultModel` in the data directory's
    `settings.json`, both collected.
  - Past use: found. `.aws/amazonq/.cli_bash_history` is the chat prompt history;
    `.amazonq/.subagents/<agent>.json` records delegated background tasks; both collected
    ([section 2](#2-per-user-storage), [section 5](#5-project-local-files)).
  - Sync, relay and origin: none in the open-source CLI.
  - Scratch directories: found, `.aws/amazonq/cli-checkouts/<conversation_id>`, already excluded
    ([section 2](#2-per-user-storage)).
  - Deletion: `/clear` and the per-directory row replacement leave the prompt history; the shadow
    repository is deleted when the session ends.
  - Version drift: none in the open-source code; not assessable for the Kiro CLI without a newer
    binary.
  - Bad lines: not a collector concern.

## 2. Per-user storage

Layout is the same on Linux, macOS and Windows except the platform data dir.

### Scratch directories

`.aws/amazonq/cli-checkouts/<conversation_id>` is a bare git repository the CLI makes as the checkpoint store for the user's working directory, only when checkpoints are on, and deletes when the session ends ([`crates/chat-cli/src/cli/chat/mod.rs:225-226`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/mod.rs#L225-L226), [`crates/chat-cli/src/cli/chat/checkpoint.rs:349-364`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/checkpoint.rs#L349-L364)). It is excluded ([section 4](#4-exclusions)) and never recorded as a project; the CLI has no working directory of its own.

### Kiro CLI

Kiro CLI home `~/.kiro` (override `KIRO_HOME`, docs reference/settings; binary help "Defaults to
KIRO_HOME/.kiro/sessions"):

- `settings/cli.json`, `settings/permissions.yaml`, `settings/mcp.json`, `settings/lsp.json` (docs;
  binary), `settings.json` mentioned in the binary's prompt text.
- `agents/*.json` (legacy 2.x profiles as `*.json.bak`), `prompts/`, `steering/` with
  `steering/AGENTS.md`, `skills/`, `hooks/`, `workflows/`,
  `powers/installed/<name>/{plugin.json,skills/,mcp.json}` (docs configuration, custom-agents,
  powers, permissions).
- `sessions/cli/<id>.json` header with `session_id`, `cwd` plus `<id>.jsonl` conversation (tokscale
  `:4, 13, 134-135`); `sessions/<workspace-hash>/sess_<uuid>/session.json` (`workspacePaths`,
  `modelId`, `createdAt`) and `messages.jsonl`, written by the IDE and the CLI's v3 session store
  (tokscale `:8-9, 171-179, 569-590`; codeburn; binary `sess_<uuid>`); `session-index/<hash>.jsonl`;
  `workspace-roots/<hash(root)>/.trust-migration.json` with key `root` and `permissions.yaml` (issue
  11282; docs permissions).
- State stores: `memories/` (memory database), `sandbox-state/`, `web-session/`, `cloud-cache/`,
  `sandbox-curl/` (docs permissions). `.default` config marker in `install.sh`.
- Legacy Amazon Q: `~/.aws/amazonq/{cli-agents,prompts,mcp.json,cli-checkouts,.cli_bash_history,global_context.json,profiles,knowledge_bases}` (Q [`paths.rs:59-66`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L59-L66)); the 2.27.1 binary still carries these names and `.aws/amazonq`.
- Platform data dir via `dirs::data_local_dir()`: Linux `~/.local/share/<app>/`, macOS `~/Library/Application Support/<app>/`, Windows `%LOCALAPPDATA%\<app>\`, holding `settings.json` and `data.sqlite3` (Q [`paths.rs:307-331`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L307-L331)). `<app>` is `amazon-q` in the Q source; `kiro-cli` per community tools (KiroaaS `:523-526`, tokscale `:6`). The binary contains `data.sqlite3` and `KIRO_TEST_SETTINGS_PATH` in `chat-cli-v2/src/util/paths.rs` but the directory literal is not visible; docs say only "SQLite database in `~/.kiro/`" (session-management).
- Logs: `$TMPDIR/kiro-log/kiro-chat.log` (binary; docs migrating-from-q), legacy `$TMPDIR/qlog` (Q [`paths.rs:143-151`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L143-L151)), Windows `%TEMP%\amazon-q\logs`. Outside home.
- Binaries: `~/.local/bin/{kiro-cli,kiro-cli-chat,kiro-cli-term,q,qchat}` (install.sh), Kiro Crew
  via `download.crew.kiro.dev/cli.sh` (binary).
- From the source review of 2026-10-19, Amazon Q source only: `.aws/amazonq/.cli_bash_history` is the chat prompt's rustyline history, every prompt line except `y`, `n`, `t` and lines starting with a space, without times ([`crates/chat-cli/src/cli/chat/prompt.rs:575-595`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/prompt.rs#L575-L595), [`input_source.rs:112-140`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/input_source.rs#L112-L140)). `.aws/amazonq/cli-agents/<name>.json` holds `allowedTools`, `toolsSettings` and `model` ([`crates/chat-cli/src/cli/agent/mod.rs:130-179`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/agent/mod.rs#L130-L179)). The data directory's `settings.json` holds `chat.defaultModel` and the feature switches such as `chat.enableCheckpoint` ([`crates/chat-cli/src/database/settings.rs:126-134`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/settings.rs#L126-L134)).

### Kiro IDE

Kiro IDE (VS Code fork, `nameShort` Kiro, `dataFolderName` `.kiro`, `serverDataFolderName`
`.kiro-server`, L4 product.json): `~/Library/Application Support/Kiro/User`, `~/.config/Kiro/User`
(`$XDG_CONFIG_HOME`), `%APPDATA%\Kiro\User`; remote `~/.kiro-server/data/User` (codeburn; wakatime
`:505-513`). Chat state in `User/globalStorage/kiro.kiroagent/`: `<workspace-hash>/<execution>.chat`
legacy, extensionless `<workspace-hash>/<session>/<execution>` (post Feb 2026),
`workspace-sessions/<base64url(path)>/<uuid>.json` v1 records, `index/` code-search index,
`config.json`, `profile.json`, `.migrations/`, a LanceDB vector index (codeburn; PR 5755; issue
6780: 4.8 GB sessions plus 564 MB LanceDB; issue 9977: 25 GB across 31 hash dirs). Extensions in
`~/.kiro/extensions` share the CLI's home.

### Environment variables

Env: `KIRO_HOME`, `KIRO_API_KEY`, `KIRO_LOG_LEVEL`, `KIRO_ACP_RECORD_PATH` (JSONL ACP wire
recording, docs reference/settings), `KIRO_TEST_SESSIONS_DIR`, `KIRO_TEST_SETTINGS_PATH` (binary).

## 3. Credentials

- `data.sqlite3` table `auth_kv(key, value)` holds Builder ID / IAM Identity Center tokens, deliberately separate from `state` (Q [`database/sqlite_migrations/005_auth_table.sql`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/sqlite_migrations/005_auth_table.sql); [`mod.rs:163`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/mod.rs#L163),[`172`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/mod.rs#L172); identical migration text in the 2.27.1 binary). Journal files `data.sqlite3-journal`/`-wal` may exist. Flag the whole file.
- MCP OAuth tokens in `~/.aws/sso/cache/*.json` (Q [`paths.rs:314-316`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L314-L316); binary `~/.aws/sso/cache`); KiroaaS also probes `~/.aws/sso/cache/kiro-auth-token.json` (L4).
- `KIRO_API_KEY` (`ksk_...`) env var for headless use (docs authentication); no file store
  documented.
- Files that embed keys: `~/.kiro/settings/mcp.json`, `.kiro/settings/mcp.json`,
  `~/.kiro/powers/installed/*/mcp.json`, agent JSON `mcpServers` blocks (docs mcp/configuration,
  permissions). `~/.kiro/web-session/` by name holds browser session state (docs permissions).
  Binary string `secrets.json` in `owner_only_sweep.rs` suggests an owner-only
  `~/.kiro/secrets.json`; unverified.

## 4. Exclusions

`.aws/amazonq/cli-checkouts` (shadow repos, Q [`paths.rs:62`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L62)), `.aws/amazonq/knowledge_bases` (Q [`paths.rs:66`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L66)), `.kiro/cloud-cache`, `.kiro/sandbox-state`, `.kiro/sandbox-curl` (names only, docs permissions), `*/User/globalStorage/kiro.kiroagent/index` and `*lance*` (PR 5755; issue 6780), `.kiro/extensions` (IDE extension payloads). `.kiro/powers` should not be excluded wholesale: powers are skills, `mcp.json` and knowledge files (docs powers), and `powers/installed/*/mcp.json` can carry credentials.

## 5. Project-local files

`.kiro/settings/mcp.json`, `.kiro/settings/lsp.json`, `.kiro/agents/`, `.kiro/steering/*.md`, `.kiro/skills/*/SKILL.md`, `.kiro/hooks/<id>.json`, `.kiro/specs/`, `.kiro/workflows/`, `.kiro/prompts/`, `.kiroignore`, `AGENTS.md` at root and in subdirectories (docs configuration, steering, hooks, permissions); legacy `.amazonq/{cli-agents,prompts,mcp.json,cli-todo-lists,.subagents,rules/**/*.md}` (Q [`paths.rs:46-51`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L46-L51)) and `AmazonQ.md` (Q [`conversation.rs:1285`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/conversation.rs#L1285), [`paths.rs:54`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/util/paths.rs#L54)). No per-project database. `.amazonq/.subagents/<agent>.json` records the last background task the `delegate` tool ran for each agent (task, status, launch and completion times, output, summary, `cwd`), and a task for the default agent runs with `--trust-all-tools` ([`crates/chat-cli/src/cli/chat/tools/delegate.rs:248-291`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/tools/delegate.rs#L248-L291), [`:337-345`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/cli/chat/tools/delegate.rs#L337-L345)); collected through the `.amazonq` project entry (source review 2026-10-19).

## 6. Where the project path is recorded

- `~/.kiro/workspace-roots/<hash>/.trust-migration.json` key `root` (issue 11282).
- `~/.kiro/sessions/*/sess_*/session.json` key `workspacePaths` (array) (tokscale `:178-179`);
  `~/.kiro/sessions/cli/*.json` key `cwd` (tokscale `:135`).
- `data.sqlite3` table `conversations(key, value)` keyed by cwd (Q [`mod.rs:402-410`](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/mod.rs#L402-L410), [migration 007](https://github.com/aws/amazon-q-developer-cli/blob/15cc8f3cd18c4272925ce1c7053268eedff1ea0a/crates/chat-cli/src/database/sqlite_migrations/007_conversations_table.sql)); 2.27.1 adds `conversations_v2(key, conversation_id, value, created_at, updated_at)` (binary migration `008_multiple_conversations_per_path`), still keyed by path. SQLite, so left to the analyzer.
- IDE `kiro.kiroagent/workspace-sessions/<base64url(path)>/` directory name decodes to the workspace
  path (codeburn; wakatime glob `*/workspace-sessions/*/*.json`). Grep-able without SQLite.

## 7. Confidence

High: `~/.kiro` subdirectories, `KIRO_HOME`, legacy `~/.aws/amazonq` and `~/.aws/sso/cache`,
`auth_kv` and `conversations` tables, `amazon-q` data dir, `$TMPDIR/kiro-log`, project `.kiro`
files, Kiro IDE app dirs and `kiro.kiroagent`. Medium: `kiro-cli` as the current data-dir name,
`sessions/<hash>/sess_*` and `session-index` layouts (L3/L4, binary confirms `sess_<uuid>` only),
LanceDB directory name, `.kiro-server`. Low: `~/.kiro/secrets.json`, `kiro-auth-token.json`. Not
determined: whether the v3 CLI still writes `data.sqlite3` or only `~/.kiro/sessions` ("SQLite
database in `~/.kiro/`" per docs vs `data.sqlite3` string in the binary), the hash function for
`workspace-roots` and `sessions` buckets, Windows `KIRO_HOME` default, and the `.chat` file schema.
