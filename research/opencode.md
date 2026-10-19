# opencode

OpenCode (catalog agent `opencode`) is an open-source coding agent with a terminal UI, a background
server and, on the 2.0 line, an Electron desktop app; its repository moved from `sst/opencode` to
`anomalyco/opencode` ([section 1](#1-source-and-evidence)). It was researched together with Crush,
which began as an OpenCode fork but no longer shares any storage code ([`crush.md`](crush.md)); Kilo
Code's current store is an OpenCode fork and shares this schema ([`kilo-code.md`](kilo-code.md)),
and Kilo Code's parser subclasses this one, so the per-record error rows and the `session_v2`
reading apply to Kilo Code's database too, should Kilo Code take OpenCode's 2.0 store. Letta Code
(at
[`2a46615`](https://github.com/letta-ai/letta-code/commit/2a46615d16babb06cf5450b8e57ecb9bdbf2f436))
can drive OpenCode as an external coding agent, starting `opencode serve` in its working directory
([src/agent/subagents/index.ts:123-159](https://github.com/letta-ai/letta-code/blob/2a46615d16babb06cf5450b8e57ecb9bdbf2f436/src/agent/subagents/index.ts#L123-L159),
[src/tools/impl/opencode-server.ts:51-66](https://github.com/letta-ai/letta-code/blob/2a46615d16babb06cf5450b8e57ecb9bdbf2f436/src/tools/impl/opencode-server.ts#L51-L66)),
so a session Letta Code started lands in this store like any other OpenCode session
([section 1 of `letta.md`](letta.md#1-source-and-evidence)). The analyzer parses the 1.x and 2.0
database layouts, from source and fixtures only.

## 1. Source and evidence

[sst/opencode](https://github.com/sst/opencode), open source, at
[`907b3bc518fa48e90e8ec24dd327d13eee71c36c`](https://github.com/sst/opencode/commit/907b3bc518fa48e90e8ec24dd327d13eee71c36c),
MIT. Every claim is from source. Platform mapping verified against the `xdg-basedir` 5.1.0 tarball
(`scratchpad/crates/xdg/package/index.js`), the version pinned in
[`packages/core/package.json:127`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/package.json#L127).
The schema has moved out of `packages/opencode` into `packages/core` (tables) and `packages/schema`
(JSON shapes). Paths cited are relative to the clone.

Session sharing was checked at this commit on 2026-10-17. On the default branch at
[`797d2af`](https://github.com/sst/opencode/commit/797d2afdbf8f0b4f189748373ff1a69bde9e0ff7) the
`share/` modules are gone and the share and unshare keybindings read "Deprecated: session sharing
was removed"
([`packages/tui/src/config/v1/keybind.ts:101-102`](https://github.com/sst/opencode/blob/797d2afdbf8f0b4f189748373ff1a69bde9e0ff7/packages/tui/src/config/v1/keybind.ts#L101-L102));
no migration in that tree drops `session_share`, so a database created by an earlier release can
still hold the share rows in [Share records](#share-records).

### Observed

No real install.

- The 2.0 layout the parser reads since issue 165 (`session_v2` and the 2.0 `session_message` types)
  is not observed on any real install, source-derived
  ([anomalyco/opencode](https://github.com/anomalyco/opencode) at
  [`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e)),
  and the real-install round of 2.0 is still to run.
- No real install has shown a `session_share` row or a shared session's events, so the
  `session synced:` rows are fixture only
  ([Sync, relay and origin](#sync-relay-and-origin-rows)).

### Source reviews

- **Source review (2026-10-19)**: the repository has moved to
  [anomalyco/opencode](https://github.com/anomalyco/opencode) (`sst/opencode` redirects to it;
  default branch `dev`). Reviewed at the `dev` head
  [`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e),
  whose CLI package is version 2.0.32
  ([`packages/cli/package.json:4`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/package.json#L4));
  the document previously cited
  [`907b3bc`](https://github.com/sst/opencode/commit/907b3bc518fa48e90e8ec24dd327d13eee71c36c),
  which is 4742 commits behind it. The newest tagged release, v1.19.3 of 2026-10-16, is not on
  `dev`: it is 52 commits after `907b3bc` on another branch and still keeps the 1.x layout (its
  `session` table is `session`, beside the `message` and `part` tables this document describes),
  while `dev` is the 2.0 line that npm publishes under the `dev` tag only. So the paths in
  [section 2](#2-per-user-storage), [section 3](#3-credentials), [section 4](#4-exclusions),
  [section 5](#5-project-local-files) and [section 6](#6-where-the-project-path-is-recorded), and
  the record sections, describe the shipped 1.x release; the additions in those sections and in
  [section 11](#11-format-versions) are what the 2.0 line changes or adds. Per class:
  - Permission state: found, not read. A `permission` table in the database, which existed at
    `907b3bc` too, holds the per-project "always" grants
    ([section 6](#6-where-the-project-path-is-recorded)); the config `permissions` rule list is
    the other standing state. Per-call outcomes are in the tool
    part's error text (1.x) or the tool item's `error.type` (2.0)
    ([Permission records](#permission-records), [section 7](#7-transcript-stores)).
  - Model: covered (`model:` rows); nothing new on disk except `model.json`
    ([section 2](#2-per-user-storage)). 2.0 adds `previous` to
    `model-switched` and a `variant` the parser does not show; no alias
    beside a resolved id.
  - Past use beyond the primary store: found.
    `prompt-history.jsonl`, `prompt-stash.jsonl`, `frecency.jsonl` and `session.json` under
    `~/.local/state/opencode` (all present at `907b3bc` too, missed then), the
    legacy V1 tables that survive a 2.0 delete, `opencode-next.db`, the
    full tool outputs and the desktop app's `drafts.sqlite`
    ([section 2](#2-per-user-storage), [section 7](#7-transcript-stores)). The state files are
    collected by the existing `.local/state/opencode` entry; the desktop app's directory is not.
    The parser reads the legacy V1
    tables of a 2.0 database and `opencode-next.db` (issue 165); the
    others are not read.
  - Sync, relay and origin: covered for 1.x shares; none at `dev`, where sharing is removed
    ([`packages/tui/src/config/keybind.ts:125-127`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/config/keybind.ts#L125-L127))
    and the CLI keeps no event payloads, so the event-based share rows can no longer appear. A
    session imported from a URL keeps no mark of its origin
    ([Sync, relay and origin](#sync-relay-and-origin-rows)). New: remote access through a public
    tunnel, configured in `service.json` ([section 3](#3-credentials)).
  - Scratch directories: found, the temp root `<os.tmpdir()>/opencode`, outside the home,
    and the agent-made worktrees ([section 2](#2-per-user-storage),
    [section 11](#11-format-versions)).
  - Deletion: found, nothing on the collection side; 2.0 deletes the `session_v2` row and its
    messages but not the legacy V1 rows of a migrated session; archiving sets
    `time_archived`, which the parser does not show.
  - Version drift: found. The 2.0 line moves the code from `packages/opencode` to `packages/core`,
    `packages/cli`, `packages/tui` and `packages/util`, and the global paths to
    [`packages/util/src/global.ts:12-27`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/util/src/global.ts#L12-L27)
    and
    [`packages/util/src/global-roots.ts:4-19`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/util/src/global-roots.ts#L4-L19),
    which keep the same XDG directories (no platform branch) and add a `tmp` root. The database name
    rule moved to
    [`packages/cli/src/database-path.ts:4-13`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/database-path.ts#L4-L13)
    (`dev` now also maps to `opencode.db`). A new surface, the OpenCode desktop app, has its own
    data directory the catalog lacks. Sessions move to `session_v2`, and a new database has no
    `session`, `message`, `part` or `session_share` table. The parser read session headers and
    project paths only from `session` until issue 165; it now reads `session_v2` and the 2.0
    `session_message` types ([Version drift](#version-drift)); the layout is not observed on any
    real install ([Observed](#observed)).
  - Bad lines: found; the parser counted undecodable database records,
    part files and events into one summary row instead of one row per
    record, until issue 139; each is now its own row
    ([Bad lines](#bad-line-rows)).

## Collection

### 2. Per-user storage

[`packages/core/src/global.ts:3`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L3),[`10-15`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L10-L15)
builds data, cache, config and state as `xdg*/opencode`.
[`xdg-basedir/index.js:7-16`](https://github.com/sindresorhus/xdg-basedir/blob/8cceade858e4da18cb971bf1844f086e9e213563/index.js#L7-L16)
has no platform branch: `XDG_DATA_HOME` or `~/.local/share`, `XDG_CONFIG_HOME` or `~/.config`,
`XDG_STATE_HOME` or `~/.local/state`, `XDG_CACHE_HOME` or `~/.cache`. So the layout is identical on
Linux, macOS and Windows (`%USERPROFILE%\.local\share\opencode` etc.). Home itself comes from
`OPENCODE_TEST_HOME` or `os.homedir()`
([`global.ts:19`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L19)).

#### Scratch directories

OpenCode 2.0 creates `<os.tmpdir()>/opencode` at start and tells the model in its environment block
to prefer it over `/tmp`, as a directory "pre-created and approved for external access"
([`packages/util/src/global-roots.ts:17`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/util/src/global-roots.ts#L17),
[`packages/util/src/global.ts:66-72`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/util/src/global.ts#L66-L72),
[`packages/core/src/instructions/builtins.ts:43`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/instructions/builtins.ts#L43)).
It is `/tmp/opencode` on Linux, under `/var/folders` on macOS and `%TEMP%\opencode`
(`AppData\Local\Temp\opencode`) on Windows, so outside the home on Linux and macOS, where no catalog
line can reach it, and under the home but unclaimed by any catalog line on Windows; the same gap as
Claude Code's temp root (issue 163). The worktrees OpenCode makes for a project are scratch
directories inside the data directory
([`packages/core/src/worktree/strategies.ts:51`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/worktree/strategies.ts#L51));
the catalog excludes their contents (`.local/share/opencode/worktree`), and since
`.local/share/opencode` is a catalog entry the analyzer's catalog rule already lists a session
working there as a scratch directory rather than a project.

#### Data directory

`~/.local/share/opencode` (data):

- `opencode.db` with `-wal`/`-shm` (WAL at
  [`packages/core/src/database/database.ts:27`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L27)).
  Name is `opencode.db` on the latest/beta/prod channels or when `OPENCODE_DISABLE_CHANNEL_DB` is
  set, otherwise `opencode-<channel>.db`
  ([`database.ts:48-54`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L48-L54)).
  `OPENCODE_DB` relocates it; a relative value is joined to the data dir
  ([`database.ts:44-46`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L44-L46)).
- `storage/` legacy JSON tree: `project/<id>.json`, `session/<projectID>/`, `message/<sessionID>/`,
  `part/<messageID>/`, `session_diff/`, plus a `migration` marker
  ([`packages/opencode/src/storage/storage.ts:122`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L122),[`143`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L143),[`154`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L154),[`169`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L169),[`192`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L192),[`224-225`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L224-L225)).
- `auth.json`
  ([`packages/opencode/src/auth/index.ts:10`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L10)),
  `mcp-auth.json`
  ([`packages/opencode/src/mcp/auth.ts:37`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/mcp/auth.ts#L37)).
- `snapshot/<projectID>/<hash>` bare git dirs for file checkpoints
  ([`packages/opencode/src/snapshot/index.ts:71`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/snapshot/index.ts#L71),
  [`packages/core/src/snapshot.ts:98`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/snapshot.ts#L98)).
- `worktree/<projectID>/` git worktrees
  ([`packages/opencode/src/worktree/index.ts:208`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/worktree/index.ts#L208)).
- `repos/`
  ([`global.ts:24`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L24)),
  `tool-output/` truncated tool output, pruned unless `OPENCODE_DISABLE_PRUNE`
  ([`packages/opencode/src/tool/truncation-dir.ts:4`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/tool/truncation-dir.ts#L4),
  [`config.ts:596`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L596)).
- `log/opencode.log` and `log/direct/<stamp>-<pid>.jsonl` run traces
  ([`packages/core/src/observability/logging.ts:49`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/observability/logging.ts#L49),
  [`packages/opencode/src/cli/cmd/run/trace.ts:32`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/run/trace.ts#L32)).

#### Config directories

`~/.config/opencode` (config, overridable with `OPENCODE_CONFIG_DIR`,
[`global.ts:64`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L64)):
`opencode.jsonc`, `opencode.json`, `config.json`, legacy `config` migrated to `config.json`
([`packages/opencode/src/config/config.ts:141-142`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L141-L142),[`272-285`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L272-L285));
`tui.json(c)`
([`config/tui.ts:184`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/tui.ts#L184));
`AGENTS.md`
([`session/instruction.ts:61`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/instruction.ts#L61));
`agents/`, `themes/`, `plugins/`, `skills/`; a `.gitignore` plus `package.json` and `node_modules`
created by the background `@opencode-ai/plugin` install in every config dir
([`config.ts:309-317`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L309-L317),[`450-460`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L450-L460)).

`~/.opencode`: a second config directory discovered with `afs.up` from home to home
([`packages/opencode/src/config/paths.ts:34-38`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/paths.ts#L34-L38)),
read for `opencode.json(c)` because it ends in `.opencode`
([`config.ts:439-441`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L439-L441));
also gets the `node_modules` install. `~/.opencode/bin/opencode` is the curl installer target
([`install:68`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/install#L68),
recognised at
[`installation/index.ts:175`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/installation/index.ts#L175)).

#### State directory

`~/.local/state/opencode`: `plugin-meta.json`
([`plugin/meta.ts:49`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/plugin/meta.ts#L49)),
`model.json` last-used model
([`cli/cmd/run/variant.shared.ts:19`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/run/variant.shared.ts#L19)),
file locks
([`global.ts:33`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L33)).

#### Cache directory

`~/.cache/opencode`: `bin/` LSP and tool binaries
([`global.ts:22`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L22),
[`lsp/server.ts:835`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/lsp/server.ts#L835),[`964`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/lsp/server.ts#L964),[`1049`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/lsp/server.ts#L1049)),
`packages/` npm installs
([`packages/core/src/npm.ts:87`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/npm.ts#L87)),
`skills/` clones
([`skill/discovery.ts:35`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/skill/discovery.ts#L35)),
`models.json` models.dev cache
([`packages/core/src/models-dev.ts:160-164`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/models-dev.ts#L160-L164)).

#### Additions on the 2.0 line

Additions from the source review of 2026-10-19 (`dev` at
[`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e)
unless a line names `907b3bc`):

- `~/.local/state/opencode/prompt-history.jsonl`: the TUI's last 50 prompts, one JSON object per
  line with `text`, `files`, `agents`, `skills`, `pasted` and an optional `mode` (`normal` or
  `shell`), and no session id, project or time
  ([`packages/tui/src/prompt/history.tsx:20-23`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L20-L23),
  [`:60`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L60),
  [`:93`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L93),
  [`:139`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L139)).
  Present at `907b3bc` as well
  ([`packages/tui/src/prompt/history.tsx:53`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/tui/src/prompt/history.tsx#L53)).
- `~/.local/state/opencode/prompt-stash.jsonl`: up to 50 prompts the user set aside unsent, each
  `{prompt, timestamp}` with the time in epoch milliseconds
  ([`packages/tui/src/prompt/stash.tsx:9-14`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/stash.tsx#L9-L14),
  [`:40`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/stash.tsx#L40)).
- `~/.local/state/opencode/frecency.jsonl`: one line per file the user attached to a prompt,
  `{path, frequency, lastOpen}`, `path` absolute (resolved against the TUI's working directory) and
  `lastOpen` in epoch milliseconds, up to 1000 paths
  ([`packages/tui/src/prompt/frecency.tsx:8-10`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/frecency.tsx#L8-L10),
  [`:42`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/frecency.tsx#L42),
  [`:61`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/frecency.tsx#L61)).
- `~/.local/state/opencode/session.json`: `{pinned: [<session id>...]}`, the sessions the user
  pinned in the TUI
  ([`packages/tui/src/context/local.tsx:517-530`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/context/local.tsx#L517-L530));
  `model.json` now holds `recent`, `favorite` and `variant`
  ([`packages/tui/src/model-preference.ts:12-16`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/model-preference.ts#L12-L16),
  [`packages/tui/src/context/local.tsx:157`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/context/local.tsx#L157)).
- `~/.local/state/opencode/service.json` (or `service-<channel>.json`): the background server's
  registration, `{id, version, url, pid, password}`
  ([`packages/cli/src/services/service-config.ts:39-42`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/services/service-config.ts#L39-L42),
  [`:115-130`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/services/service-config.ts#L115-L130);
  [`packages/client/src/effect/service.ts:142-148`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/client/src/effect/service.ts#L142-L148)),
  and `~/.config/opencode/service.json` its settings ([section 3](#3-credentials)).
- `~/.local/share/opencode/opencode-next.db`: the database of the pre-release 2.0 builds. The 2.0
  migration imports its sessions into `opencode.db` opening it read-only and leaves the file in
  place
  ([`packages/core/src/database/v1-migration.bun.ts:702-706`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L702-L706));
  the existing `opencode*.db*` secret glob already flags it.
- `~/.local/share/opencode/log/opencode.log`, or `opencode-<channel>.log` for a local build
  ([`packages/util/src/observability/logging.ts:59-62`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/util/src/observability/logging.ts#L59-L62)).
  `tool-output/tool_<id>` files keep the full text of a tool result the transcript cut at 2000 lines
  or 50 KiB, for seven days; the transcript keeps the path in its marker
  `[showing lines 1-<n> of <m>; full output saved to <file>]`
  ([`packages/core/src/tool-output.ts:13-18`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/tool-output.ts#L13-L18),
  [`:86-90`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/tool-output.ts#L86-L90)).
  The catalog excludes the directory.
- Snapshots stay at `snapshot/<projectID>/<hash of worktree>`
  ([`packages/core/src/snapshot.ts:96`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/snapshot.ts#L96));
  worktrees move to `worktree/<first six characters of projectID>/<name>`
  ([`packages/core/src/worktree/strategies.ts:51`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/worktree/strategies.ts#L51)).

#### OpenCode desktop app

The OpenCode desktop app (Electron, `packages/desktop`) keeps its own data in Electron's `userData`,
set to `<appData>/<app id>` with the id `ai.opencode.desktop`, `ai.opencode.desktop.beta` or
`ai.opencode.desktop.dev`
([`packages/desktop/src/main/constants.ts:17-26`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/desktop/src/main/constants.ts#L17-L26),
[`packages/desktop/src/main/lifecycle/configure.ts:33`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/desktop/src/main/lifecycle/configure.ts#L33)):
`~/Library/Application Support/ai.opencode.desktop` on macOS, `%APPDATA%\ai.opencode.desktop` on
Windows and `~/.config/ai.opencode.desktop` on Linux. It holds `drafts.sqlite`, whose `document`
table keeps prompt drafts and history and whose `state` table keeps what the renderer persists
([`packages/desktop/src/main/storage/index.ts:22-24`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/desktop/src/main/storage/index.ts#L22-L24),
[`packages/desktop/src/main/storage/schema.ts:3-29`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/desktop/src/main/storage/schema.ts#L3-L29)),
and a `compile-cache` directory
([`configure.ts:42`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/desktop/src/main/lifecycle/configure.ts#L42)).
No catalog line names it. Whether the app's sidecar server writes the same
`~/.local/share/opencode/opencode.db` was not determined.

#### System-wide managed config

System-wide managed config, outside home: `/Library/Application Support/opencode`,
`%ProgramData%\opencode`, `/etc/opencode`
([`config/managed.ts:23-27`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/managed.ts#L23-L27)).

### 3. Credentials

- `~/.local/share/opencode/auth.json`, mode 0600: per provider
  `{type:"oauth",refresh,access,expires}` or `{type:"api",key}` or `{type:"wellknown",key,token}`
  ([`auth/index.ts:14-33`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L14-L33),[`79`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L79)).
  `OPENCODE_AUTH_CONTENT` can replace it
  ([`:59`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L59)).
- `~/.local/share/opencode/mcp-auth.json` MCP OAuth tokens
  ([`mcp/auth.ts:37`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/mcp/auth.ts#L37)).
- `opencode*.db*`: table `credential` with JSON `value` column
  ([`packages/core/src/credential/sql.ts:5-14`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/credential/sql.ts#L5-L14)),
  so the transcript database is also a secret store.
- `opencode.json(c)` / `config.json` in both config dirs can carry `provider.<id>.options.apiKey`
  ([`packages/opencode/src/provider/provider.ts:229`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/provider/provider.ts#L229),[`352`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/provider/provider.ts#L352)).
- No keychain use found.
- Added 2026-10-19 (`dev` at
  [`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e)):
  `~/.config/opencode/service.json` (or `service-<channel>.json`), written mode 0600, holds the
  background server's `password` (32 random bytes, base64url, kept across restarts), its `hostname`,
  `port`, `cors` and `env`, and, when remote access is on, `remote.route`, the random
  16-hex-character subdomain that is the only secret in the public URL of the server
  ([`packages/cli/src/services/service-config.ts:14-26`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/services/service-config.ts#L14-L26),
  [`:164-175`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/services/service-config.ts#L164-L175),
  [`:177-186`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/services/service-config.ts#L177-L186)).
  The registration copy `~/.local/state/opencode/service.json` carries the same `password`
  ([section 2](#2-per-user-storage)). Neither file matches a secret glob today. Remote access
  exposes the server through an OpenTunnel tunnel (a third-party tunnelling client library,
  `@opentunnel/client`) at `https://<route>.<tunnel hostname>`, turned on with
  `opencode service set remote true` or `opencode pair --remote`
  ([`packages/cli/src/services/remote-tunnel.ts:14-27`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/services/remote-tunnel.ts#L14-L27),
  [`packages/cli/src/commands/handlers/pair.ts:21-25`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/commands/handlers/pair.ts#L21-L25));
  the tunnel identity is kept by that library under an XDG path this repository does not name
  ([`remote-tunnel.ts:66-70`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/services/remote-tunnel.ts#L66-L70)),
  not determined.
- `auth.json` is imported into the `credential` table by a 2.0 migration and left in place
  ([`packages/core/src/database/migration/20260805200742_import_legacy_credentials.ts:39`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260805200742_import_legacy_credentials.ts#L39),
  [`:46-50`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260805200742_import_legacy_credentials.ts#L46-L50)),
  so both copies stay on disk.

### 4. Exclusions

Relative to the home:

`.local/share/opencode/snapshot`, `.local/share/opencode/worktree`, `.local/share/opencode/repos`,
`.local/share/opencode/tool-output`, `.config/opencode/node_modules`, `.opencode/node_modules`,
`.opencode/bin`, `.cache/opencode` (entire dir is binaries, package installs and skill clones;
`models.json` is public data).

Source review of 2026-10-19: the 2.0 line adds no excludable subtree under the catalog's existing
OpenCode entries; `worktree` and `snapshot` stay where the exclusions point. The desktop app's
`compile-cache` directory ([section 2](#2-per-user-storage)) is low-value and would need an
exclusion if the app's data directory gets a catalog line.

### 5. Project-local files

`.opencode/` directories from cwd up to the worktree root
([`config/paths.ts:26-31`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/paths.ts#L26-L31))
holding `opencode.json(c)`, `agents/`, `plugins/`, `themes/`, `skills/`, and the generated
`.gitignore`, `package.json`, `node_modules`; `opencode.jsonc` / `opencode.json` found by walking up
([`paths.ts:17-19`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/paths.ts#L17-L19));
`AGENTS.md`, `CLAUDE.md`, deprecated `CONTEXT.md`
([`session/instruction.ts:65-67`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/instruction.ts#L65-L67)).
No per-project database; sessions live in the home DB.

### 6. Where the project path is recorded

- SQLite table `project`: `worktree` (absolute), `sandboxes` (array), and table `project_directory`
  `directory` with `type` main/root/git_worktree
  ([`packages/core/src/project/sql.ts:7-34`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/project/sql.ts#L7-L34)).
- Added 2026-10-19 for the 2.0 line (`dev` at
  [`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e)),
  all in SQLite and so for the analyzer, not `discover_projects`: `session_v2.directory` and `path`
  (the session's working directory and its path under the project,
  [`packages/core/src/session/sql.ts:22-37`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/sql.ts#L22-L37));
  `project.time_archived` for a project the user archived
  ([`packages/core/src/project/sql.ts:12-29`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/project/sql.ts#L12-L29));
  the `worktree` table, `project_id`, `directory` (absolute), `strategy` and `time_created`, one row
  per worktree OpenCode made, which replaces the deprecated `project_directory`
  ([`packages/core/src/worktree/sql.ts:6-20`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/worktree/sql.ts#L6-L20),
  [`project/sql.ts:31-47`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/project/sql.ts#L31-L47));
  and the `permission` table's `project_id`, which ties standing grants to a project. Outside
  SQLite, `~/.local/state/opencode/frecency.jsonl` lists absolute paths of files attached to prompts
  ([section 2](#2-per-user-storage)); their directories point at projects but are file paths, not
  project roots.
- Legacy `storage/project/<id>.json` key `worktree`
  ([`storage.ts:122-132`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L122-L132)).

## Parsing

### 7. Transcript stores

One SQLite file for all projects: `~/.local/share/opencode/opencode.db`
([`packages/core/src/global.ts:3`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L3),[`11`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L11)
uses `xdg-basedir` with no platform branching, so the same path on macOS and Windows;
[`packages/core/src/database/database.ts:49-54`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L49-L54)).
Non-release channels use `opencode-<channel>.db` in the same directory
([`database.ts:54`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L54));
`OPENCODE_DB` can relocate it
([`:43-47`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L43-L47)).
One `message` row per message, one `part` row per content part. A legacy JSON tree
`~/.local/share/opencode/storage/`
([`packages/opencode/src/storage/storage.ts:224`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L224))
still exists ([section 11](#11-format-versions)).

`journal_mode=WAL`
([`database.ts:27`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L27),
also at open
[`sqlite.bun.ts:164`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/sqlite.bun.ts#L164));
`wal_checkpoint(PASSIVE)` runs at startup only
([`database.ts:32`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/database.ts#L32)).
Rows written since the last checkpoint live only in `opencode.db-wal`, so a copy without the sidecar
loses recent messages. No encryption or compression.

Other records of use, beside this store, are in [section 10](#10-other-stores), under
[Other records of use](#other-records-of-use).

#### What survives a delete

In 2.0, deleting a session publishes the durable `session.deleted` and removes the session's events
and sequence
([`packages/core/src/session.ts:378-388`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session.ts#L378-L388);
[`packages/core/src/bus.ts:702-714`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L702-L714));
the projector deletes the `session_v2` row
([`projector.ts:552-554`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L552-L554)),
which cascades to `session_message`, `session_pending`, `session_inbox` and the instruction tables
([`packages/core/src/session/sql.ts:79-160`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/sql.ts#L79-L160)),
child sessions first. Nothing deletes the legacy `session`, `message` and `part` rows the upgrade
copied from, and no record of the deletion is left. Archiving sets `time_archived` and unarchiving
clears it
([`projector.ts:615-627`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L615-L627)).

In 1.x a delete removes the `session` row with its `session_share` and `event` rows
([`session/session.ts:606-623`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/session.ts#L606-L623),
[`projector.ts:257-259`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L257-L259),
[`event.ts:514-521`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/event.ts#L514-L521)),
and ShareNext's `session.deleted` subscriber asks the share service to delete the public copy
([`share-next.ts:200`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L200));
whether that request still finds the share row before the cascade removes it is not determined from
source, and no local file records that the remote copy was deleted. What remains: the legacy
`session`, `message` and `part` rows of a database migrated to 2.0, which nothing deletes;
`prompt-history.jsonl`, the last 50 TUI prompts with no session, project or time; unsent prompts in
`prompt-stash.jsonl`; a pinned session id in `session.json`; full tool outputs under `tool-output/`
for seven days; and, for a 1.x share, the `creating share` and `removing share` lines in
`log/opencode.log`. No record of the deletion is left. The analyzer reads the legacy V1 tables, for
a session `session_message` does not hold, and `opencode-next.db` as secondary sources, and does not
read the three `~/.local/state/opencode` files, the log or `tool-output/`, which the collector
excludes (see [Secondary sources](../analyzer/docs/output.md#secondary-sources)).

### 8. Record schema

Git branch is not recorded anywhere. Role: `message.data.role`. Project
path: `project.worktree`; cwd: `session.directory` or assistant
`data.path.cwd`.

Drizzle tables in
[`packages/core/src/session/sql.ts`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts).

#### `session` and `project`

`session`
([`:22-66`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L22-L66)):
`id` (`ses_...`), `project_id` → `project.id`, `workspace_id`, `parent_id`, `slug`, `directory`
(cwd, stored with `/` on Windows,
[`database/path.ts:5-8`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/path.ts#L5-L8)),
`path`, `title`, `version` (OpenCode version), `share_url`, `summary_*`, `metadata` JSON, `cost`,
`tokens_*`, `revert` JSON, `permission` JSON, `agent`, `model` JSON `{id, providerID, variant?}`
([`:52-56`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L52-L56)),
`time_created`, `time_updated` (epoch milliseconds,
[`database/schema.sql.ts:3-10`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/schema.sql.ts#L3-L10)
uses `Date.now()`), `time_compacting`, `time_archived`.

`project`
([`project/sql.ts:6-18`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/project/sql.ts#L6-L18)):
`id`, `worktree` (absolute repository root), `vcs`, `name`, `time_*`, `sandboxes` JSON array.

#### `message` and `part`

`message`
([`sql.ts:68-80`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L68-L80);
CREATE in
[`database/migration/20260127222353_familiar_lady_ursula.ts:22-31`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L22-L31)):
`id` (`msg_...`), `session_id`, `time_created`, `time_updated` (ms), `data` JSON = the V1 message
minus `id` and `sessionID`
([`session/projector.ts:77-82`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L77-L82)).
`data`
([`packages/schema/src/v1/session.ts`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts)):
user
([`:332-354`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L332-L354))
`role:"user"`, `time.created` (ms), `agent`, `model:{providerID, modelID, variant?}`, `format?`,
`summary?`, `system?`, `tools?`; assistant
([`:453-485`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L453-L485))
`role:"assistant"`, `time.{created, completed?}`, `parentID` (the user message), `modelID`,
`providerID`, `mode`, `agent`, `path.{cwd, root}`, `cost`,
`tokens.{input, output, reasoning, cache.{read, write}}`, `error?` (`{name, data}`), `finish?`,
`variant?`.

`part`
([`sql.ts:82-98`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L82-L98);
CREATE
[`...ursula.ts:33-42`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L33-L42)):
`id` (`prt_...`), `message_id`, `session_id`, `time_created`, `time_updated`, `data` JSON = the part
minus `id`, `messageID` and `sessionID`
([`projector.ts:84-87`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L84-L87)).
`data.type` discriminator
([`v1/session.ts:357-370`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L357-L370)):
`text`
([`:102-115`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L102-L115):
`text`, `synthetic?`, `ignored?`, `time.{start,end?}`); `reasoning`
([`:118-127`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L118-L127):
`text`, `time.{start,end?}`); `tool`
([`:315-322`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L315-L322):
`callID`, `tool` (name), `state.status` in `pending|running|completed|error`
([`:259-302`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L259-L302)),
`state.input` on all, `completed` adds `output`, `title`, `metadata`, `time.{start,end}`, `error`
adds `error`, `time.{start,end}`); the tool call and its result are the same part, mutated in place;
`step-start`
([`:233-237`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L233-L237),
`snapshot?`), `step-finish`
([`:240-256`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L240-L256),
`reason`, `cost`, `tokens`), `subtask`
([`:204-217`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L204-L217),
`prompt`, `description`, `agent`), `compaction`
([`:195-201`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L195-L201)),
`snapshot`, `patch`, `file`, `agent`, `retry`.

#### `session_message`

Newer V2 projection in the same database: `session_message`
([`sql.ts:119-138`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/sql.ts#L119-L138)):
`id`, `session_id`, `type` in
`agent-switched|model-switched|user|synthetic|system|shell|assistant|compaction`
([`packages/schema/src/session-message.ts:200-213`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L200-L213)),
`seq`, `time_created` (ms,
[`projector.ts:203`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L203)),
`data` JSON. Assistant `data`
([`session-message.ts:165-189`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L165-L189)):
`agent`, `model.{id, providerID}`, `content[]` with `type` in `text|reasoning|tool`
([`:122-157`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L122-L157));
tool items carry `id`, `name`, `state.status`, `state.input`, `state.content[]`
(`{type:"text",text}`), `state.error.message`, `time.{created, ran?, completed?}`. User `data`:
`text`, `files?`, `agents?`
([`:44-51`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L44-L51)).
Migration
[`20260622170816_reset_v2_session_state.ts:8-14`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260622170816_reset_v2_session_state.ts#L8-L14)
wipes `session_message`, `session_input` and `event` on upgrade, so `message`/`part` are the durable
transcript; treat `session_message` as supplementary. The two switch records carry the common base
`id`, `metadata?` and `time.created`
([`session-message.ts:24-28`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L24-L28))
plus `agent` (a string) for `agent-switched`
([`:30-35`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L30-L35))
and `model` for `model-switched`
([`:37-42`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/session-message.ts#L37-L42)),
a `Model.Ref` `{id, providerID, variant?}`
([`packages/schema/src/model.ts:13-18`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/model.ts#L13-L18)).
The projector stores `id` and `type` in their own columns and the rest of the record in `data`
([`packages/core/src/session/projector.ts:192-208`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/session/projector.ts#L192-L208)),
so `data` is `{time, agent}` or `{time, model}`.

#### `event`

`event`
([`core/src/event/sql.ts:10-25`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/event/sql.ts#L10-L25)):
`aggregate_id` = session id, `seq`, `type` such as `message.updated.1` and `message.part.updated.1`
([`schema/src/event.ts:94-96`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/event.ts#L94-L96)),
`data` JSON with full message or part copies
([`core/src/event.ts:336-348`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/event.ts#L336-L348)).
Also wiped by the reset migration.

### 9. Joins and timestamps

`session.project_id → project.id` (worktree); `message.session_id → session.id`;
`part.message_id → message.id` (`part.session_id` is denormalised). Order parts by `part.id` (ids
are time-ordered,
[`v1/session.ts:17-27`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/v1/session.ts#L17-L27))
or `time_created`. Tool call and result are one `part` row; assistant → user through
`data.parentID`. `session_message` joins on `session_id`, ordered by `seq`. Times are epoch
milliseconds ([section 8](#8-record-schema)).

### 10. Other stores

#### Other records of use

Other records of use, from the source review of 2026-10-19 (`dev` at
[`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e);
the three TUI files are at the same paths at `907b3bc`, for example
[`packages/tui/src/prompt/history.tsx:53`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/tui/src/prompt/history.tsx#L53)).
The parser reads the legacy tables of a 2.0 database and `opencode-next.db`; it reads none of the
others.

| Source | Holds | Survives | Joins on | Plan |
| --- | --- | --- | --- | --- |
| `~/.local/state/opencode/prompt-history.jsonl` ([`packages/tui/src/prompt/history.tsx:20-23`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L20-L23), [`:60-75`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L60-L75), [`:93-100`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L93-L100), [`:139`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/history.tsx#L139)) | the last 50 TUI prompts, `{text, files, agents, skills, pasted, mode?}`; no session id, project or time | session delete, project removal; trimmed to 50 and rewritten at each start, dropping lines that do not parse | text only | not read; secondary when read, empty `timestamp_utc` |
| `~/.local/state/opencode/prompt-stash.jsonl` ([`packages/tui/src/prompt/stash.tsx:9-14`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/stash.tsx#L9-L14), [`:40`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/prompt/stash.tsx#L40)) | up to 50 prompts set aside unsent, `{prompt, timestamp}` (epoch ms) | everything; a stashed prompt may never reach a transcript | none (text and time when it was later sent) | not read; primary for what it holds (unsent prompts), `system` rows |
| `~/.local/state/opencode/session.json` ([`packages/tui/src/context/local.tsx:517-530`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/context/local.tsx#L517-L530)) | `pinned`, ids of sessions the user pinned | session delete (the id stays until the user unpins it) | session id | not read; secondary: a pinned id with no session left is a trace of a deleted session |
| Legacy `session`, `message`, `part` tables in a database migrated to 2.0 ([section 11](#11-format-versions)) | the 1.x transcript, copied into `session_message` by the migration | deletion of the session in 2.0, which removes only the `session_v2` row and what cascades from it | session id, message id (the copy keeps the V1 ids, [`v1-migration.bun.ts:353`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L353), [`:404`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L404)) | secondary: read only for a session `session_message` does not hold, its event rows marked `recovered` by the parser |
| `~/.local/share/opencode/opencode-next.db` ([`packages/core/src/database/v1-migration.bun.ts:702-706`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L702-L706), [`:846`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L846)) | a pre-release 2.0 database (`project`, `session`, `session_message`), imported read-only and left in place | everything after the import | session id | secondary (`secondary()`), so a session it shares with `opencode.db` is shown once |
| `~/.local/share/opencode/tool-output/tool_<id>` ([`packages/core/src/tool-output.ts:13-18`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/tool-output.ts#L13-L18), [`:86-90`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/tool-output.ts#L86-L90)) | full text of a tool result the transcript cut, kept seven days | session delete within the seven days | the path in the transcript marker `full output saved to <file>` | secondary; not collected (catalog exclusion) |
| desktop app `drafts.sqlite` in `<appData>/ai.opencode.desktop*` ([`packages/desktop/src/main/storage/schema.ts:3-29`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/desktop/src/main/storage/schema.ts#L3-L29)) | prompt drafts and history, `document(key, value)` | not determined | not determined | not collected; needs a real-install round |

The 2.0 runtime keeps no other mirror: the `event` table holds payloads
only on the hosted (workerd) server, never in the CLI
([Event payloads in 2.0](#event-payloads-in-20)).

#### Share records

A session published to OpenCode's web share service (the `/share` command,
[Sync, relay and origin](#sync-relay-and-origin-rows)) has one `session_share` row
([`packages/core/src/share/sql.ts:5-13`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/share/sql.ts#L5-L13);
CREATE in
[`...ursula.ts:89-97`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L89-L97)):
`session_id` (primary key, references `session.id` with `ON DELETE CASCADE`), `id` (the share id;
the hosted service makes it the last eight characters of the session id,
[`packages/enterprise/src/core/share.ts:117-122`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/enterprise/src/core/share.ts#L117-L122)),
`secret` (a random UUID the service returns and the client sends back with every sync and delete, so
a credential for the public copy), `url` (the public page) and `time_created`, `time_updated` (epoch
ms,
[`database/schema.sql.ts:3-10`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/schema.sql.ts#L3-L10)).
`ShareNext.create` writes it once the service has answered the create request, as an upsert when the
session is shared again
([`packages/opencode/src/share/share-next.ts:310-336`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L310-L336)),
and `ShareNext.remove` deletes it after the service accepts the delete
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
whose `data.info.share.url` holds the URL and `data.info.time.updated` the time of the change
([`session/session.ts:734-746`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/session.ts#L734-L746)),
so the `event` table still holds the URL after an unshare. A session never shared has no
`session_share` row, a NULL `share_url` and no `share` key in its events. Deleting a session removes
its `session_share` row with it ([What survives a delete](#what-survives-a-delete)); the upgrade
migration
[`20260622170816_reset_v2_session_state.ts:11`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration/20260622170816_reset_v2_session_state.ts#L11)
emptied `event` once.

#### Permission records

From the source review of 2026-10-19: OpenCode asks before a tool call when the rules say `ask`; the
user answers `once`, `always` or `reject` (`Permission.Reply`,
[`packages/schema/src/permission.ts:42-54`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/permission.ts#L42-L54)).
The `permission.asked` and `permission.replied` events are ephemeral, so the answer itself is never
stored; what lands on disk is:

- Standing grants. The `permission` table, `id` (`per_...`), `project_id` (references `project.id`,
  `ON DELETE CASCADE`), `action` (the tool's permission name), `resource` (the pattern granted) and
  `time_created`, `time_updated` (epoch ms), one row per pattern of an `always` reply
  ([`packages/core/src/permission/sql.ts:7-20`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/permission/sql.ts#L7-L20);
  [`packages/core/src/permission.ts:299-306`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/permission.ts#L299-L306)).
  Saved rows are applied as `allow` rules for every later session of the project
  ([`:147-156`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/permission.ts#L147-L156)).
  The table exists at `907b3bc` with the same columns
  ([`packages/core/src/permission/sql.ts:7-19`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/permission/sql.ts#L7-L19)),
  but the 1.x CLI there keeps `always` answers in memory only
  ([`packages/opencode/src/permission/index.ts:143-150`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/permission/index.ts#L143-L150)),
  so on a 1.x install the table is written only by the 2.0 runtime it bundles. An older shape,
  `permission(project_id, data)`, was created by the first migration and dropped by
  [`20260601202201_amazing_prowler.ts:8`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260601202201_amazing_prowler.ts#L8)
  ([`20260127222353_familiar_lady_ursula.ts:44-51`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260127222353_familiar_lady_ursula.ts#L44-L51)).
- The session's rule list. `session.permission` (`session_v2.permission` in 2.0) is a
  `Permission.Ruleset`, a JSON array of `{action, resource, effect}` with `effect` in
  `allow|deny|ask`
  ([`packages/schema/src/permission.ts:56-67`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/permission.ts#L56-L67)),
  set at creation and by the durable `session.permissions` event
  ([`packages/schema/src/session-event.ts:121-129`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-event.ts#L121-L129);
  [`packages/core/src/session/projector.ts:593-596`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L593-L596)).
  The 2.0 upgrade copies 1.x sessions with `permission` NULL
  ([`packages/core/src/database/v1-migration.bun.ts:611-628`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L611-L628))
  and a later migration clears the column for every session
  ([`20260910120000_clear_v1_session_permission.ts:8`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260910120000_clear_v1_session_permission.ts#L8)),
  so it holds only rules set after that. The configured rules are the config's `permissions` list
  and each agent's
  ([`packages/schema/src/config.ts:55`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/config.ts#L55),
  [`packages/schema/src/config/agent.ts:21`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/config/agent.ts#L21)).
- Per-call outcomes, in the transcript. In 1.x a refused call is a tool part with `state.status`
  `error` and `state.error` the refusal's text
  ([`packages/opencode/src/session/processor.ts:185-203`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/processor.ts#L185-L203)):
  "The user rejected permission to use this specific tool call.", the same followed by "with the
  following feedback: " and the user's text, or "The user has specified a rule which prevents you
  from using this specific tool call. ..." for a `deny` rule
  ([`packages/core/src/v1/permission.ts:7-25`](https://github.com/anomalyco/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/v1/permission.ts#L7-L25)).
  In 2.0 the assistant's tool item gets `state.status` `error` with `error.type` `aborted` and
  message "The user declined this tool call" for a plain rejection
  ([`packages/core/src/session/runner/step.ts:207-215`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/runner/step.ts#L207-L215)),
  and `error.type` `permission.rejected` for a `deny` rule or a rejection with feedback
  ([`packages/core/src/session/to-session-error.ts:61-62`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/to-session-error.ts#L61-L62)).
  An approval leaves no per-call record in either version.

#### Event payloads in 2.0

The `event` table keeps payloads only when the bus is configured to persist them, which the hosted
(workerd) server does and the CLI does not
([`packages/core/src/bus.ts:178-179`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L178-L179),
[`:203`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L203),
[`:908`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/bus.ts#L908);
[`packages/server/src/workerd.ts:64-69`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/server/src/workerd.ts#L64-L69)),
and the 2.0 upgrade deletes every existing `event` row
([`v1-migration.bun.ts:549-566`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L549-L566)).

### 11. Format versions

Legacy JSON under `~/.local/share/opencode/storage/`, one file per key: `project/<projectID>.json`
(`{id, vcs, worktree, time}`), `session/<projectID>/<sessionID>.json`,
`message/<sessionID>/<msgID>.json`, `part/<msgID>/<partID>.json`, `session_diff/<sessionID>.json`,
marker `storage/migration` (integer)
([`storage.ts:63-65`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L63-L65),[`81-211`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L81-L211),[`224-225`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L224-L225)).
Before that, per-project
`~/.local/share/opencode/project/<slug>/storage/session/{info,message,part}/...`
([`storage.ts:97`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L97),[`139`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L139),[`150`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L150),[`165`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/storage/storage.ts#L165);
[`packages/web/src/content/docs/troubleshooting.mdx:35-36`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/web/src/content/docs/troubleshooting.mdx#L35-L36)).
JSON records carry `id`, `sessionID` and `messageID` inline (the database `data` column strips
them). The SQLite `migration` table
([`database/migration.ts:30`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/database/migration.ts#L30))
lists applied schema migrations; `data_migration` tracks data moves. At this commit no code imports
`storage/` JSON into SQLite; `storage/` is still written for `session_diff`
([`session/revert.ts:77`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/session/revert.ts#L77)),
so both trees coexist. `opencode import`
([`cli/cmd/import.ts:196-225`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/import.ts#L196-L225))
loads exported JSON into `message`/`part`.

OpenCode 2.0 (the `dev` branch at
[`cb07c55`](https://github.com/anomalyco/opencode/commit/cb07c555d4d1ca34430b7857b52f104c3d95e09e),
source review of 2026-10-19; not in a tagged release yet). The code moved to `packages/core`,
`packages/cli`, `packages/tui` and `packages/util`; the database is still `opencode.db` (or
`opencode-<channel>.db`) under the same XDG data directory
([`packages/cli/src/database-path.ts:4-13`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/database-path.ts#L4-L13)).
What changes for the parser:

- Sessions live in `session_v2`, same columns as `session` plus `fork_session_id`, `fork_boundary`,
  `time_idle`, `time_viewed`, `idle_outcome`, `resume_attempts`
  ([`packages/core/src/session/sql.ts:22-68`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/sql.ts#L22-L68)).
  A database created by 2.0 is bootstrapped from the current schema
  ([`packages/core/src/database/migration.ts:26-36`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration.ts#L26-L36);
  [`schema.gen.ts:184`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/schema.gen.ts#L184)),
  which has no `session`, `message`, `part`, `session_share` or `todo` table. A database upgraded
  from 1.x gets `session_v2` beside the old tables and the upgrade copies each 1.x session into it
  and its `message`/`part` rows into `session_message`, leaving the old rows in place
  ([`packages/core/src/database/migration/20260804233008_loose_psylocke.ts:90`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260804233008_loose_psylocke.ts#L90),
  [`:139-140`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260804233008_loose_psylocke.ts#L139-L140);
  [`v1-migration.bun.ts:534-700`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/v1-migration.bun.ts#L534-L700)).
  A database from a pre-release 2.0 build has its `session` renamed to `session_v2`
  ([`loose_psylocke.ts:13-38`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/database/migration/20260804233008_loose_psylocke.ts#L13-L38)).
- `session_message` is the only transcript for new sessions. Its `type` adds `location-switched`
  (`location.{directory, workspaceID}`, `projectID`, `subpath`, `previous`), `skill` (`skill`,
  `name`, `text`) and `idle` (`outcome` in `succeeded|failed|interrupted`, `error`) to the types in
  [section 8](#8-record-schema); `agent-switched` and `model-switched` gain `previous`; `shell` is
  now `shellID`, `command`, `status` (`running|exited|timeout|killed`), `exit` and `output`, an
  object `{output, cursor, size, truncated}`; tool items gain `executed` and the `streaming` status;
  assistant gains `snapshot`, `finish`, `retry`, `time.streamed`
  ([`packages/schema/src/session-message.ts:45-125`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-message.ts#L45-L125),
  [`:213-237`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-message.ts#L213-L237),
  [`:290-309`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/session-message.ts#L290-L309);
  [`packages/schema/src/shell.ts:25`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/shell.ts#L25),
  [`:77-84`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/schema/src/shell.ts#L77-L84)).
  Model and agent changes are also projected onto `session_v2.model` and `agent`
  ([`projector.ts:555-571`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/projector.ts#L555-L571)).
- Session sharing is removed
  ([`packages/tui/src/config/keybind.ts:125-127`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/tui/src/config/keybind.ts#L125-L127));
  `session_v2.share_url` remains as a column and is copied from 1.x sessions.
- New tables: `permission` ([Permission records](#permission-records)), `worktree` (`project_id`,
  `directory`, `strategy`, `time_created`, one row per worktree OpenCode made under
  `~/.local/share/opencode/worktree/<first six characters of the project id>/`;
  [`packages/core/src/worktree/sql.ts:6-20`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/worktree/sql.ts#L6-L20),
  [`packages/core/src/worktree/strategies.ts:51`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/worktree/strategies.ts#L51)),
  `kv`, `session_pending`, `session_inbox`, `instruction_*`, and `project.time_archived`.
- Scratch directories. 2.0 creates `<os.tmpdir()>/opencode` and tells the model to prefer it to
  `/tmp`, "pre-created and approved for external access"
  ([`packages/util/src/global-roots.ts:17`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/util/src/global-roots.ts#L17),
  [`packages/core/src/instructions/builtins.ts:43`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/instructions/builtins.ts#L43)).
  It is outside the home on Linux and macOS and so never collected. The instruction is about where
  the model writes temporary files, so the path shows in tool inputs; whether a session's
  `directory` can be it was not determined. A session working in an OpenCode worktree has its
  `directory` under the data directory, which the analyzer's catalog rule already lists as a scratch
  directory.
- A session imported with `opencode session import <file or URL>` is written as a new session with
  the local version and the import time as `time_updated`, and no field records where it came from
  ([`packages/cli/src/commands/handlers/session/import.ts:15-22`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/cli/src/commands/handlers/session/import.ts#L15-L22);
  [`packages/core/src/session/transfer.ts:64-126`](https://github.com/anomalyco/opencode/blob/cb07c555d4d1ca34430b7857b52f104c3d95e09e/packages/core/src/session/transfer.ts#L64-L126)).

### 12. Secrets

`credential.value` JSON (`{type:"oauth", access, refresh}` or `{type:"key", key}`,
[`schema/src/credential.ts:16-34`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/schema/src/credential.ts#L16-L34)),
`account.access_token` and `refresh_token`, `control_account.*`, `session_share.secret` (the share
service's per-share secret that authorises sync to and deletion of the public copy,
[Share records](#share-records)), plus the legacy files `~/.local/share/opencode/auth.json`
([`auth/index.ts:10`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L10),[`14-35`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/auth/index.ts#L14-L35))
and `mcp-auth.json`. Tool `input` and `output` text can contain pasted tokens.

### 13. Parser plan

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

The subsections below give the plan per requirement class from the source review of
2026-10-19 (detail in [section 7](#7-transcript-stores), [section 10](#10-other-stores)
and [section 11](#11-format-versions)), after what the parser does today.

#### Permission rows

The message's `agent` (V1 user and assistant, V2 assistant, V2 `agent-switched` `agent`) is tracked
the same way as `permission mode: agent=<name>` and `permission mode: agent=<old> -> agent=<new>`,
because an agent (`build`, `plan` or a custom one) is a mode that carries its own permission ruleset
(the agent's `permission: PermissionV1.Ruleset`,
[`packages/opencode/src/agent/agent.ts:44`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/agent/agent.ts#L44)).
Both rows take the message's timestamp. The parser reads nothing else of the permission state (issue
98): not the session's `permission` JSON, not the project's `sandboxes` array, and not the per-call
outcomes and standing grants in [Permission records](#permission-records). Before the source review
of 2026-10-19 this document said the session JSON and the `sandboxes` array were named in
[section 8](#8-record-schema) without their shape, that no per-call approval or denial was recorded,
and that whether a denied call shows as a tool `state.status` of `error` was not researched; the
review found both the per-call outcomes and the standing grants. Planned, not read today: per call,
a tool result whose 1.x `state.error` starts "The user rejected permission" or "The user has
specified a rule which prevents you", or whose 2.0 `error.type` is `permission.rejected` or is
`aborted` with "The user declined this tool call", gets `permission decision: rejected` (with
` feedback` or ` rule` as the text shows) after its `tool_result` row, joined on `tool_use_id`; no
approval is recorded. Standing: one
`permission setting: <action> <resource>=allow (from <database> permission, time_created)` row per
`permission` table row at its `time_created`, `project_path` the project's `worktree`; and the
session's `permission` rule list as `permission setting: session <action> <resource>=<effect>` rows
at the session's `time_updated`. Not read today.

#### Model rows

Model and mode rows. A `system` row `model: <modelID> provider=<providerID>`
precedes the first message of a session that names a model (V1 user
`model.{providerID, modelID}`, V1 assistant `providerID` and `modelID`, V2
assistant `model.{id, providerID}`), and `model: <old> -> <new>
provider=<providerID>` precedes every later message, or stands for every V2
`model-switched` record, whose model differs; mode rows are under
[Permission state](#permission-rows).
Plan from the source review: add the 2.0 `variant` beside `provider=` when present. No alias
beside a resolved id exists.

#### Past-use rows and secondary sources

`prompt-history.jsonl` (secondary, empty `timestamp_utc`, text
match), `prompt-stash.jsonl` (primary for unsent prompts, `system`
rows at `timestamp`), `session.json` (`system` row per pinned id that
has no session, at the file's modification time), the legacy V1 tables
of a migrated database (secondary to `session_message`), and
`opencode-next.db` (secondary to `opencode.db`). Read: the legacy V1
tables (a session `session_message` does not hold, its event rows
marked `recovered` "yes" by the parser, since both stores are one
file) and `opencode-next.db` (`secondary()`, deduplicated against the
database it was imported into); `has_secondary` is set. The three
`~/.local/state/opencode` files are not read.
The sources and their joins are under [Other records of use](#other-records-of-use).

#### Sync, relay and origin rows

Sync: OpenCode uploads a session only when it is shared. Sharing starts from `/share` in the TUI,
which asks once and remembers the answer as `share_consent` in `~/.local/state/opencode/kv.json`
([`packages/tui/src/routes/session/index.tsx:465-497`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/tui/src/routes/session/index.tsx#L465-L497),
[`packages/tui/src/context/kv.tsx:15`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/tui/src/context/kv.tsx#L15)),
from `opencode run --share`
([`packages/opencode/src/cli/cmd/run.ts:161-164`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/run.ts#L161-L164),
[`:535-547`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/cli/cmd/run.ts#L535-L547)),
or for every new top-level session when the config sets `share: "auto"` (or the deprecated
`autoshare: true`) or `OPENCODE_AUTO_SHARE` is set
([`packages/core/src/v1/config/config.ts:57-63`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/v1/config/config.ts#L57-L63),
[`config/config.ts:589-591`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/config/config.ts#L589-L591),
[`effect/runtime-flags.ts:17`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/effect/runtime-flags.ts#L17),
[`share/session.ts:39-46`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/session.ts#L39-L46)).
With `share` unset sharing is manual; `share: "disabled"` or `OPENCODE_DISABLE_SHARE` blocks it
([`share/session.ts:28`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/session.ts#L28),
[`share-next.ts:23`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L23)).
Once shared, a full copy and then every session, message, part, diff and model update is posted with
the share secret to `<base>/api/share/<id>/sync`
([`share-next.ts:179-199`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L179-L199),
[`:247-299`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L247-L299)),
where the base is `https://opncd.ai` or the config's `enterprise.url`, or, for a user signed in to
an OpenCode console account with an active organisation (the `account` table), the account's URL
under `/api/shares` with its bearer token and an `x-org-id` header
([`:206-222`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L206-L222)).
OpenCode Zen, OpenCode's hosted model gateway, is a model provider, so its calls are model API calls
and not sync; trace and log export over OTLP (OpenTelemetry's wire protocol) goes only to an
endpoint the user sets in `OTEL_EXPORTER_OTLP_ENDPOINT`
([`core/src/flag/flag.ts:16-17`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/flag/flag.ts#L16-L17)).
The parser yields one `system` row per `session_share` row,
`session synced: share <id> url <url> (from opencode.db session_share, time_created)`, timestamped
by `time_created`, never with `secret`; for a session with no `session_share` row whose
`session.updated.1` events carry `info.share.url`,
`session synced: share url <url> (from opencode.db event session.updated.1, info.time.updated)` at
that event's `info.time.updated`, and
`session unshared (from opencode.db event session.updated.1, info.time.updated)` at the first later
event without `share`; the database name in the text is the file's own (`opencode-<channel>.db` for
a channel database). These rows are fixture only ([Observed](#observed)). shown a `session_share`
row or a shared session's events. Deleting a Deleting a shared session is under
[What survives a delete](#what-survives-a-delete). What survives it is the log: `creating share` and
`removing share` lines with the `sessionID` go to `~/.local/share/opencode/log/opencode.log` at the
default INFO level
([`share-next.ts:312`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L312),
[`:340`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/share/share-next.ts#L340);
[`core/src/observability/logging.ts:49-52`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/observability/logging.ts#L49-L52),
[`:59-65`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/observability/logging.ts#L59-L65);
[`core/src/global.ts:23`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/global.ts#L23)).
Separately, a session can be moved to a workspace (the control plane's `workspace` table) served by
another OpenCode instance (`Workspace.sessionWarp`,
[`control-plane/workspace.ts:559`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/control-plane/workspace.ts#L559)),
recorded as `session.workspace_id` and a `workspace` row
([`core/src/control-plane/workspace.sql.ts:6-18`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/core/src/control-plane/workspace.sql.ts#L6-L18));
the one built-in adapter targets a local worktree
([`control-plane/adapters/worktree.ts:92`](https://github.com/sst/opencode/blob/907b3bc518fa48e90e8ec24dd327d13eee71c36c/packages/opencode/src/control-plane/adapters/worktree.ts#L92)),
so a remote target comes from a plugin, and none was researched.

Sync: 1.x shares covered; none at `dev`. Relay: none (no messaging
integration; not found in `packages/core`, `packages/cli`,
`packages/server` or `packages/tui` at `cb07c55`, grepped for
`telegram`, `whatsapp` and `slack`). Origin: none; an imported session
carries no source.

#### Scratch directory rows

A session whose directory is under
`~/.local/share/opencode/worktree/` is already classed by the catalog
rule; the parser could add `scratch directory: <directory> (worktree,
from <database> worktree)` rows from the `worktree` table. The temp root
is not collectable.

#### Deletion rows

No local record of a deleted 2.0 session other than the
legacy V1 rows and a pinned id; `time_archived` should become a
`session archived (from <database> session_v2, time_archived)` row.

#### Bad-line rows

Done (issue 139). Each `message`, `part`, `session_message`
or `event` row whose `data` is not a JSON object is its own `parser:
unparseable record <rowid> (<table>.data: <reason>): <data>` row
carrying the stored value in full, with its row's session and project,
an empty timestamp and `source_line` the rowid; each part file of the
JSON trees that does not decode is `parser: unparseable part <partID>
(<reason>): <file text>`, `source_file` the part file. A message or
session file that does not decode stays one whole-file `parser:`
row.

#### Fixtures

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

#### Version drift

Done (issue 165), from source alone; the real-install
round of 2.0 is still to run, and its line types and key sets are to be
compared with this plan. Session headers and `directory` come from
`session_v2`, else `session`; the session-start row adds
`fork=<fork_session_id>`, and a session a 2.0 database holds only in
the 1.x `session` table ends `(only in the 1.x session table)`. In a
database with `session_v2`, `session_message` is the transcript and
the 1.x `message` and `part` rows are read only for a session it does
not hold. The 2.0 `shell` record (`shellID`, `status`, `exit`,
`output.output`) is a `tool_use` row and a `tool_result` row starting
`[timeout]`, `[killed]` or `[exit <code>]` when it did not exit 0;
`location-switched` is a `system` row `location switched: <previous
directory> -> <directory>` (with `workspace=` and `subpath=` when
set; `project_path` stays the session's `directory`), `skill` is
`skill <name>: <text>`, `idle` is `idle: <outcome>` with the error
text, and a compaction row adds its `status` and error. A 2.0 tool
error shows its `error.type` before the message (`[error] aborted The
user declined this tool call`).

## 14. Confidence

Collection. High: every path above (source). Medium: whether the collector's project-level exclusion
syntax matches `<project>/.opencode/node_modules`; test it. Not determined: whether older releases
wrote `bin/` under the data dir (the current catalog exclusion suggests they did).

Parsing. High: table columns, JSON field names, timestamp units, part
types, WAL, paths, absence of git branch. Medium: which table is
authoritative over time (`session_message` is new and was reset once;
`message`/`part` have been stable since the first migration). Not
determined: exact byte layout of `session_message.data` for all types in a
real install; whether an intermediate release had a startup JSON to SQLite
importer.
