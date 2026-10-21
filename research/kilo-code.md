# kilo-code

Kilo Code (catalog agent `kilo-code`) is an open-source coding agent: a CLI, terminal UI (TUI) and
server that are an OpenCode fork, so the SQLite schema in [`opencode.md`](opencode.md) applies, and
a VS Code extension that is a thin client of that server. It began as a fork of Roo Code
([`roo-code.md`](roo-code.md)), itself a fork of Cline, and its extension still reads the Roo-style
task directories that pre-fork installs left, for import
([`packages/kilo-vscode/src/legacy-migration/task-store.ts:6-7`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/src/legacy-migration/task-store.ts#L6-L7)).
The analyzer parses its `kilo.db` sessions and the cloud session marker, from source and fixtures
only.

## Source and evidence

Open source. [Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode) at
[`76bcfd40be616a72f4697b3041565f322245b462`](https://github.com/Kilo-Org/kilocode/commit/76bcfd40be616a72f4697b3041565f322245b462),
MIT (clone `scratchpad/repos/kilo`). The CLI, TUI and server are an OpenCode fork in `packages/core`
and `packages/opencode`; the VS Code extension `kilocode.kilo-code`
([`packages/kilo-vscode/package.json:2`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/package.json#L2),[`11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/package.json#L11))
is a thin client of that server. All claims from source. Paths cited are relative to the clone.
Citations to the later commit
[`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22)
are of files that were present at the cited commit too.

### Observed

No real install.

### Source reviews

- 2026-10-21: Kilo-Org/kilocode at
  [87cc35c](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22):
  the parser plan's permission, past-use, remote control, scratch directory and deletion items are
  now read from source alone, the sandbox directories got catalog lines, the TUI prompt stash and
  the session pull request links were added, and the source-host integration was reviewed
  ([Source host rows](#source-host-rows)).
- 2026-10-19:
  [`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22)
  against
  [`76bcfd4`](https://github.com/Kilo-Org/kilocode/commit/76bcfd40be616a72f4697b3041565f322245b462).
  Added the sandbox policy and preference files, the TUI prompt history, the retention pass,
  remote control, cloud session import, the permission records and the project worktrees
  ([Per-user storage](#per-user-storage),
  [Where the project path is recorded](#where-the-project-path-is-recorded),
  [Transcript stores](#transcript-stores), [Other stores](#other-stores),
  [Parser plan](#parser-plan)). Of the 58 files the document and the parser cite, 9 changed and none
  moved or disappeared; the schema, SQL and projector files the parser depends on are unchanged.

## Collection

### Per-user storage

`xdg-basedir` with no platform branching
([`packages/core/src/global.ts:3`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L3),[`12`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L12),[`22-26`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L22-L26)),
so the same paths on Linux, macOS and Windows; `XDG_DATA_HOME`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`,
`XDG_STATE_HOME` relocate them. `KILO_TEST_HOME` overrides home
([`global.ts:32`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L32)).
Newlines are stripped from `$HOME`
([`global.ts:21`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L21)).
All three roots are tagged no-index for Spotlight
([`global.ts:58`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L58)).

#### Scratch directories

- `~/.local/share/kilo/worktree/<project id>/`, the agent's worktrees
  ([`packages/opencode/src/worktree/index.ts:210`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/worktree/index.ts#L210)),
  is under the catalog line `kilo-code|.local/share/kilo` and in `EXCLUDES`, and the analyzer's
  catalog rule classes it.
- `<project>/.kilo/worktrees/<name>`, the agent manager's and the TUI's worktrees
  ([`packages/opencode/src/kilocode/cli/cmd/tui-worktree.ts:14-17`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/cli/cmd/tui-worktree.ts#L14-L17);
  [Project-local files](#project-local-files)), is the agent's own worktree inside the user's project; it
  is in `EXCLUDES` but under no home catalog entry, so the analyzer counts each as a project of
  its own. [Where the project path is recorded](#where-the-project-path-is-recorded) says which
  `kilo.db` rows name them.
- `<system temp directory>/kilo/remote-attachments/<base64url session id>/`, files sent from Kilo
  Cloud over remote control, removed when the session's remote handling ends
  ([`packages/opencode/src/kilocode/remote-attachments.ts:272-287`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/remote-attachments.ts#L272-L287);
  [`packages/core/src/global.ts:28`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/global.ts#L28);
  [Remote control](#remote-control)). Outside the home, so no catalog line reaches it; the
  collector documentation names it as a manual step.

#### `~/.local/share/kilo`

`~/.local/share/kilo` (data):

- `kilo.db` (SQLite, WAL) on release builds; `kilo-<channel>.db` or a pre-existing
  `opencode-<channel>.db` otherwise; `KILO_DB` overrides
  ([`packages/core/src/database/database.ts:32`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/database/database.ts#L32),[`52-66`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/database/database.ts#L52-L66);
  [`packages/core/src/flag/flag.ts:111`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/flag/flag.ts#L111)).
  Holds sessions, messages, parts, projects.
- `auth.json`
  ([`packages/opencode/src/auth/index.ts:11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/auth/index.ts#L11)),
  `mcp-auth.json`
  ([`mcp/auth.ts:37`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/mcp/auth.ts#L37)).
- `storage/` legacy JSON store
  ([`storage/storage.ts:234`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L234);
  [`kilocode/storage/json-migration.ts:78`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/storage/json-migration.ts#L78)).
- `snapshot/<projectID>/<hash>` bare git dirs for checkpoints
  ([`snapshot/index.ts:108`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/snapshot/index.ts#L108)),
  `worktree/<projectID>/` agent worktrees
  ([`worktree/index.ts:210`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/worktree/index.ts#L210)),
  `tool-output/` truncated tool results
  ([`tool/truncation-dir.ts:4`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/tool/truncation-dir.ts#L4)),
  `repos/`
  ([`global.ts:37`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L37)),
  `log/`
  ([`global.ts:36`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L36)),
  `plans/*.md`
  ([`session/session.ts:416`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/session/session.ts#L416)),
  `retention/state.json`, the counts of the last automatic deletion pass
  ([`kilocode/session/retention.ts:326`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session/retention.ts#L326);
  [Retention](#retention)),
  `session-export.db`, `session-export-workspace.json`
  ([`kilocode/bootstrap.ts:83-88`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/bootstrap.ts#L83-L88)).
- `state/` fallback for the state dir when `XDG_STATE_HOME` is unset and `~/.local/state/kilo` is
  unusable
  ([`global.ts:26`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L26);
  [`kilocode/global.ts:38-72`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/kilocode/global.ts#L38-L72)).

#### `~/.local/state/kilo`

`~/.local/state/kilo` (state): `indexing/` codebase index
([`kilocode/indexing.ts:298`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/indexing.ts#L298)),
`model.json`, `plugin-meta.json`, `background-process/`, and `prompt-history.jsonl`, the last 50
prompts typed into the terminal UI, shell commands included
([`packages/tui/src/prompt/history.tsx:27`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L27),
[`:53`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L53); shape in
[TUI prompt history](#tui-prompt-history)), and `prompt-stash.jsonl`, up to 50 prompts set aside
unsent
([`packages/tui/src/prompt/stash.tsx:15`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/stash.tsx#L15),
[`:36`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/stash.tsx#L36)),
collected by `kilo-code|.local/state/kilo`.

Beside it, in the parent of the state directory (`path.dirname(Global.Path.state)`):

- `~/.local/state/kilo-sandbox-policy/<sha256 of session id>/<sha256 of directory>.json`, one per
  session and directory,
  `{enabled, mode: "allow"|"deny"|"proxy", allowedHosts[], writablePaths[], version}`: the
  confinement Kilo's sandbox applied to that session's commands (network mode, allowed hosts and
  writable paths)
  ([`packages/opencode/src/kilocode/sandbox/store.ts:10-31`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/sandbox/store.ts#L10-L31)).
- `~/.local/state/kilo-sandbox-preference/<sha256 of directory>.json`, `true` or `false`,
  whether the sandbox is on for a directory
  ([`preference.ts:7-34`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/sandbox/preference.ts#L7-L34)).

On the default layout both are siblings of `~/.local/state/kilo`, collected by the catalog lines
`kilo-code|.local/state/kilo-sandbox-policy` and `kilo-code|.local/state/kilo-sandbox-preference`
(from source alone); with the fallback state directory `<data>/state` they land in
`~/.local/share/kilo` and are collected with it. The names are hashes, so a file is tied to a
session or project only by hashing a known id or path.

#### `~/.config/kilo`

`~/.config/kilo` (config, `KILO_CONFIG_DIR` overrides,
[`flag.ts:140-141`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/flag/flag.ts#L140-L141)):
`kilo.jsonc`, `kilo.json`, `opencode.jsonc`, `opencode.json`, `config.json`, legacy `config/` dir
([`packages/opencode/src/config/config.ts:206-208`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/config/config.ts#L206-L208),[`458-488`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/config/config.ts#L458-L488)),
`agents/`
([`kilocode/marketplace/paths.ts:76`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/marketplace/paths.ts#L76)),
`tui.jsonc`, `themes/`, `marketplace/`. The `permission` key of the global config files is
rewritten by an "always" approval ([Permission rows](#permission-rows)). `KILO_CONFIG` points at
an extra config file,
`KILO_CONFIG_CONTENT` inlines one
([`config.ts:762-777`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/config/config.ts#L762-L777),[`897-903`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/config/config.ts#L897-L903)).

#### `~/.cache/kilo`

`~/.cache/kilo`: `bin/`
([`global.ts:35`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/global.ts#L35),
LSP servers such as clangd, zls), `skills/`, `packages/git/`, `commands/`
([`kilocode/skill-remove.ts:25`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/skill-remove.ts#L25);
[`kilocode/plugin/git-source.ts:158`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/plugin/git-source.ts#L158);
[`kilocode/command-files.ts:118`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/command-files.ts#L118)).

#### `~/.kilo` and `~/.kilocode`

`~/.kilo`: `bin/kilo` installer target
([`install:70`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/install#L70)),
`skills/`
([`marketplace/paths.ts:81`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/marketplace/paths.ts#L81)),
`rules/`
([`kilocode/rules-migrator.ts:12`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/rules-migrator.ts#L12));
it and `~/.kilocode` are extra config roots
([`kilocode/config/overlay.ts:244`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/config/overlay.ts#L244)).
`~/.kilocode`: legacy `rules/`, `cli/config.json`, `cli/global/settings/custom_modes.yaml`
([`kilocode/modes-migrator.ts:170`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/modes-migrator.ts#L170));
`~/.kilocodemodes`
([`modes-migrator.ts:174`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/modes-migrator.ts#L174)).
`~/.agents` is read for skills
([`kilocode/config/claude-migration.ts:641`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/config/claude-migration.ts#L641)).

#### VS Code extension

VS Code `globalStorage/kilocode.kilo-code/`: the current extension keeps only `globalState` keys
([`packages/kilo-vscode/src/KiloProvider.ts:1652-1663`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/src/KiloProvider.ts#L1652-L1663))
and reads legacy Roo-style `tasks/_index.json` for import
([`packages/kilo-vscode/src/legacy-migration/task-store.ts:136`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-vscode/src/legacy-migration/task-store.ts#L136)).
Pre-fork installs leave `tasks/`, `checkpoints/`, `cache/` there.

### Credentials

- `~/.local/share/kilo/auth.json`, mode 0600: per provider `{type:"api", key}` or
  `{type:"oauth", refresh, access, accountId?, enterpriseUrl?, baseURL?}`
  ([`auth/index.ts:15-27`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/auth/index.ts#L15-L27),[`81-90`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/auth/index.ts#L81-L90)).
- `~/.local/share/kilo/mcp-auth.json`: MCP OAuth tokens
  ([`mcp/auth.ts:37`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/mcp/auth.ts#L37)).
- `~/.kilocode/cli/config.json`: legacy Kilo token, migrated into `auth.json`
  ([`packages/kilo-gateway/src/auth/legacy-migration.ts:5-11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-gateway/src/auth/legacy-migration.ts#L5-L11)).
- `kilo.db` holds credentials in its `credential` and `account` tables
  ([`kilo.db`](#kilodb); the fields in [Secrets](#secrets)).
- `kilo.json*` and `config.json` can embed `{env:...}` provider keys and MCP headers.
- No keychain use. `KILO_SERVER_PASSWORD` is env only
  ([`flag.ts:68`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/flag/flag.ts#L68)).

### Exclusions

`.local/share/kilo/snapshot`, `/worktree`, `/repos`, `/tool-output`,
`.local/state/kilo/indexing`, `.local/share/kilo/state/indexing`,
`.cache/kilo` (binaries, package clones), `.kilo/bin`, project
`.kilo/worktrees`. Keep `plans/`, `retention/`, `session-export*`, and `log/`: it is bounded and
holds the only local record of a session deletion whose remote delete failed
([Logs](#logs), [What survives a delete](#what-survives-a-delete)).

### Project-local files

`.kilo/` and legacy `.kilocode/` at any depth
([`kilocode/permission/config-paths.ts:9-11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/permission/config-paths.ts#L9-L11);
[`config.ts:808`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/config/config.ts#L808))
with `rules/`, `workflows/`, `agent/`, `agents/`, `skills/`, `worktrees/`
([`rules-migrator.ts:11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/rules-migrator.ts#L11);
[`workflows-migrator.ts:14`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/workflows-migrator.ts#L14);
[`kilocode/agent/builder.ts:77`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/agent/builder.ts#L77);
[`marketplace/paths.ts:77`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/marketplace/paths.ts#L77),[`82`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/marketplace/paths.ts#L82);
[`kilocode/cli/cmd/tui-worktree.ts:17`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/cli/cmd/tui-worktree.ts#L17),
added to `.git/info/exclude`); `kilo.json`, `kilo.jsonc`, `opencode.json(c)`
([`cli/cmd/mcp.ts:399-402`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/cli/cmd/mcp.ts#L399-L402));
`.kilocodeignore`
([`kilocode/ignore-migrator.ts:10`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/ignore-migrator.ts#L10)),
`.kilocodemodes`
([`modes-migrator.ts:187`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/modes-migrator.ts#L187)),
`.kilocoderules`
([`rules-migrator.ts:7`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/rules-migrator.ts#L7)),
`AGENTS.md`. No per-project database.

### Where the project path is recorded

`kilo.db` table `project`: `worktree` (absolute), `vcs`, `name`, `sandboxes[]`; table
`project_directory`: `directory`, `type` (`main|root|git_worktree`)
([`packages/core/src/project/sql.ts:6-34`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/project/sql.ts#L6-L34)).
Legacy `storage/project/<id>.json` `worktree`. SQLite only; left to the analyzer.

A worktree the agent created is a `project_directory` row of type `git_worktree` and an entry of
`project.sandboxes`, and a session run in it has the worktree as `session.directory`
([`packages/core/src/project/sql.ts:16`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/project/sql.ts#L16),
[`:20-34`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/project/sql.ts#L20-L34)
at
[`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22)).

## Parsing

### Transcript stores

`<data>` below is `~/.local/share/kilo` ([Per-user storage](#per-user-storage)). Transcripts are
SQLite, `<data>/kilo.db` or one of the channel names of
[`~/.local/share/kilo`](#localsharekilo) (tables in [`kilo.db`](#kilodb)).
Legacy JSON store `<data>/storage/session/<projectID>/<sesID>.json`,
`storage/message/<sesID>/<msgID>.json`, `storage/part/<msgID>/<prtID>.json`, older
`storage/session/info/*.json` and `storage/session/message/<ses>/*.json`, marker `storage/migration`
([`packages/opencode/src/storage/storage.ts:65`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L65),[`140-170`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L140-L170),[`193-197`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L193-L197),[`234-236`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L234-L236)).
The VS Code globalStorage `kilocode.kilo-code/tasks/<id>/` holds only pre-migration Roo-style files.

#### What survives a delete

Deleting a session asks Kilo's service to delete the remote copy (`DELETE /api/session/<id>`) and
removes the `storage/session_share/<sessionID>.json` marker only when the service accepts; signed
out, or on a network error or an error status, the marker stays, with a `share remove failed` log
line in the last two cases
([`session/session.ts:728-733`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/session/session.ts#L728-L733),
[`packages/opencode/src/kilocode/session/index.ts:281-284`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session/index.ts#L281-L284),
[`kilo-sessions.ts:1687-1718`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1687-L1718)).
Which `kilo.db` rows the delete removes is not stated here; the session code is OpenCode's
([What survives a delete in `opencode.md`](opencode.md#what-survives-a-delete)). The opt-in
retention pass ([Retention](#retention)) deletes old sessions through the same delete, then
vacuums the database, which removes the deleted rows' remnants, and records its counts, but no
session id, in `retention/state.json`. What remains is the TUI's prompt history
`prompt-history.jsonl` ([TUI prompt history](#tui-prompt-history)), which carries no time, session
or directory and survives a delete, the retention pass and a removed project. The log files
([Logs](#logs)) hold the `creating session`, `removing share` and `remote session started` lines;
whether a delete touches them is not stated. The analyzer reads the `kilo.db` sessions, the marker
files, the prompt history as a secondary source, the remote control lines of the logs and
`retention/state.json` ([Parser plan](#parser-plan),
[Secondary sources](../analyzer/docs/output.md#secondary-sources)).

#### Remote control

`kilo remote`, `KILO_REMOTE=1` or `"remote_control": true` in the
config connects the host to Kilo Cloud, Kilo's web service, so sessions can be driven, and created,
from there
([`packages/core/src/v1/config/config.ts:121-123`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/v1/config/config.ts#L121-L123),
[`packages/opencode/src/kilo-sessions/kilo-sessions.ts:320`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L320),
[`:905`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L905)).
The only local record is in the logs ([Logs](#logs)): `remote connection enabled` and
`remote connection disabled`
([`:1220`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1220),
[`:1259`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1259)),
and for each session the remote side creates on the host `remote session started` with `sessionID`,
`startedAt`, `model` (`<providerID>/<id>`) and `directory`, then `remote session ended` with
`sessionID`, `startedAt`, `durationMs` and `reason`
([`packages/opencode/src/kilo-sessions/remote-session-log.ts:37-61`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/remote-session-log.ts#L37-L61),
[`remote-sender.ts:1176-1180`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/remote-sender.ts#L1176-L1180)).
The session itself is an ordinary row of `kilo.db` with nothing marking its remote creation. Files
the remote side attaches that are not text, images or PDF are written to
`<system temp directory>/kilo/remote-attachments/<base64url session id>/` and removed when the
session's remote handling ends
([`packages/opencode/src/kilocode/remote-attachments.ts:8-16`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/remote-attachments.ts#L8-L16),
[`:272-287`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/remote-attachments.ts#L272-L287);
[`packages/core/src/global.ts:28`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/global.ts#L28)).

#### Cloud session import

The VS Code extension lists the user's Kilo Cloud sessions and clones
one locally on its first message, and the remote side can ask for the same clone
([`packages/kilo-vscode/src/kilo-provider/handlers/cloud-session.ts:1-6`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-vscode/src/kilo-provider/handlers/cloud-session.ts#L1-L6)).
The export is fetched from the ingest service
([`packages/kilo-gateway/src/cloud-sessions.ts:153-157`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L153-L157))
and stored as a new local session with a fresh id; the cloud session's `parentID`, `share` and
`permission` are dropped
([`:257`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L257),
[`:268`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L268),
[`:295-310`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/kilo-gateway/src/cloud-sessions.ts#L295-L310)),
and no log line names the cloud id (grepped `log.info` and `cloud` in
`packages/opencode/src/kilocode/server`). A cloned session therefore cannot be told from a local
one.

### Record schema

#### V1 messages and parts

V1 `message.data` and `part.data`
([`packages/schema/src/v1/session.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts)):
user
[`:374-400`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L374-L400)
`{role:"user", time{created}, agent, model{providerID, modelID, variant?}, system?, tools?, editorContext?, summary?}`;
assistant
[`:499-535`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L499-L535)
`{role:"assistant", time{created, completed?}, parentID, modelID, providerID, mode, agent, path{cwd, root}, cost, tokens{input, output, reasoning, cache{read, write}}, error?, finish?}`.
Parts (all with `id, sessionID, messageID`
[`:80-86`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L80-L86)):
`text{text, synthetic?, time{start,end}}`
[`:102`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L102),
`reasoning{text, time}`
[`:118`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L118),
`tool{callID, tool, state{status: pending|running|completed|error, input, output?, title?, error?, time{start,end}}}`
[`:289-362`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L289-L362),
`step-start`, `step-finish{reason, snapshot (git hash), model, cost, tokens}`
[`:241-288`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L241-L288),
`file`, `agent`, `subtask`, `compaction`, `retry`, `patch`, `snapshot`.

#### V2 session messages

V2 `session_message.data`
([`packages/schema/src/session-message.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts)):
base `{id, time{created}}`
[`:24-27`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L24-L27);
`type` in
`agent-switched, model-switched, user{text, files, agents}, synthetic{text}, system{text}, shell{callID, command, output, time{created, completed}}, assistant{agent, model, content[], snapshot{start, end, files}, finish, cost, tokens, error, time{created, completed}}, compaction{reason, summary, recent}`
[`:45-213`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L45-L213).
Assistant `content[]`: `text{id, text}`, `reasoning{id, text, time}`,
`tool{id, name, state{status, input, content[], structured, error, result}, time{created, ran, completed}}`
[`:122-158`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L122-L158).
Times are millisecond epochs. The two switch records carry the common base `id`, `metadata?` and
`time.created`
([`session-message.ts:24-28`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L24-L28))
plus `agent` (a string) for `agent-switched`
([`:30-35`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L30-L35))
and `model` for `model-switched`
([`:37-42`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L37-L42)),
a `Model.Ref` `{id, providerID, variant?}`
([`packages/schema/src/model.ts:13-18`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/model.ts#L13-L18)).
The projector stores `id` and `type` in their own columns and the rest of the record in `data`
([`packages/core/src/session/projector.ts:213-229`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L213-L229)),
so `data` is `{time, agent}` or `{time, model}`.

No git branch is recorded; `snapshot` holds commit hashes.

### Joins and timestamps

`session.id` ← `message.session_id` ← `part.message_id`; `session.directory` is the cwd and
`session.project_id` → `project.worktree`
([`project/sql.ts:8`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/project/sql.ts#L8)).
A V1 `tool` part carries both call and result in `state`; V2 `assistant.content[].tool.id` likewise.

### Other stores

#### `kilo.db`

`kilo.db`
([`packages/core/src/session/sql.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts)):
`session(id, project_id, workspace_id, parent_id, slug, directory, path, title, version, share_url, summary_*, metadata JSON, cost, tokens_*, revert JSON, permission JSON, agent, model JSON{id, providerID, variant}, time_created, time_updated, time_compacting, time_archived)`
[`:24-71`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L24-L71);
`message(id, session_id, time_created, time_updated, data JSON)`
[`:73-90`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L73-L90);
`part(id, message_id, session_id, time_*, data JSON)`
[`:92-114`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L92-L114);
`session_message(id, session_id, type, seq, time_*, data JSON)`
[`:135-154`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/sql.ts#L135-L154);
`session_input(prompt JSON)`, `session_context_epoch(snapshot JSON)`, `todo`;
`project(id, worktree, vcs, name, sandboxes)`; `credential(value JSON)`
([`credential/sql.ts:5-14`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/credential/sql.ts#L5-L14));
`account(access_token, refresh_token)` and legacy `control_account`
([`account/sql.ts:6-39`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/account/sql.ts#L6-L39)).
The projector writes V2 `session_message` and V1 `message`/`part` for every event
([`session/projector.ts:213-230`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L213-L230),[`285-300`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L285-L300),[`335-345`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/session/projector.ts#L335-L345)),
so either set is complete. WAL mode as in OpenCode; collect the `-wal` sidecar.

#### Permission tables and columns

`session.permission` is a JSON ruleset,
`[{permission, pattern, action: "allow"|"deny"|"ask"}]`
([`packages/core/src/session/sql.ts:55`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/session/sql.ts#L55),
[`packages/schema/src/v1/permission.ts:16-25`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/v1/permission.ts#L16-L25)).
The `permission` table, `(id, project_id, action, resource, time_created, time_updated)`, unique per
project, action and resource
([`packages/core/src/permission/sql.ts:7-20`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/permission/sql.ts#L7-L20)),
holds the saved allow grants of a project that the newer permission service reads
([`packages/core/src/permission.ts:116`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/permission.ts#L116),
[`:131-135`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/permission.ts#L131-L135)).

#### Cloud session marker

`<data>/storage/session_share/<sessionID>.json`, a storage key written as a JSON file
([`storage.ts:64-66`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L64-L66)),
holds `{id, ingestPath, url?}`
([`packages/opencode/src/kilo-sessions/kilo-sessions.ts:1549-1558`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1549-L1558)).
`id` and `ingestPath` (the path on Kilo's session ingest service that receives the session's events)
are written when the ingest service registers the session, at session creation for a user signed in
to Kilo
([`:1432-1466`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1432-L1466));
`url`, `https://app.kilo.ai/s/<share_token>`, is added by a share
([`:1468-1511`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1468-L1511))
and removed by an unshare, which keeps the file
([`:1513-1547`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1513-L1547)).
A session created while signed out, or with `KILO_DISABLE_SESSION_INGEST` set, has no file. The file
carries no time of its own.

#### TUI prompt history

The terminal UI keeps the prompts typed into it in `~/.local/state/kilo/prompt-history.jsonl`, the
state directory of [Per-user storage](#per-user-storage)
([`packages/tui/src/app.tsx:267-273`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/app.tsx#L267-L273),
[`packages/tui/src/prompt/history.tsx:53`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L53)).
Each line is `{input, mode?: "normal"|"shell", parts[]}`, the typed text, whether it was a shell
command (`!`), and the attached file and agent parts; there is no time, session id or directory
([`:9-25`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L9-L25)).
A prompt is appended unless it repeats the last one, and the file is rewritten with the last 50
(`MAX_HISTORY_ENTRIES`) whenever it grows past that and at every start, which drops lines that do
not parse
([`:27-42`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L27-L42),
[`:54-60`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L54-L60),
[`:83-108`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/history.tsx#L83-L108)).
`prompt-stash.jsonl` beside it holds one `{input, parts, timestamp}` line per prompt set aside
unsent, `timestamp` in epoch milliseconds, rewritten at each start the same way
([`packages/tui/src/prompt/stash.tsx:9-13`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/stash.tsx#L9-L13),
[`:17-30`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/prompt/stash.tsx#L17-L30)).
Unlike OpenCode's terminal UI, Kilo's keeps no `session.json` of pinned sessions (no `pinned` key
in `packages/tui/src` at `87cc35c`).

#### Retention

With `retention.enabled: true` in `kilo.json` (off by default), a pass
at most every 23 hours deletes sessions older than `retention.maxAgeDays` (default 30) through the
normal session delete, then runs `VACUUM` and truncates the WAL when enough pages are free, which
also removes the deleted rows' remnants from the database files
([`packages/opencode/src/kilocode/session/retention.ts:13-32`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L13-L32),
[`:163-167`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L163-L167),
[`:301-324`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L301-L324)).
It writes `<data>/retention/state.json`,
`{at, scanned, deleted, skippedActive, failed, durationMs, cancelled?, reclaimedBytes?}`, for the
last pass
([`:45-54`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L45-L54),
[`:326`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L326)),
and logs `retention pass complete` with the same counts
([`:472`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/session/retention.ts#L472)).

#### Logs

`<data>/log/<ISO time>.log`, bounded: the ten newest `????-??-??T??????.log` files are kept and
each rotates at 50 MB
([`packages/core/src/util/log.ts:24`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/util/log.ts#L24),
[`70-96`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/util/log.ts#L70-L96),
[`127-141`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/util/log.ts#L127-L141)).
Each line is `INFO <UTC time to the second> +<ms>ms service=<name> <key>=<value>... <message>`,
written at the default level `INFO`
([`packages/core/src/util/log.ts:27`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/util/log.ts#L27),
[`:162-189`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/util/log.ts#L162-L189)),
so a reader splits the key-value pairs off the message. The session service writes `creating
session`, `sharing`, `unsharing` and `removing share`
([`kilo-sessions.ts:1444`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1444),
[`:1487`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1487),
[`:1527`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1527),
[`:1691`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L1691);
[`packages/core/src/util/log.ts:84-85`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/util/log.ts#L84-L85)),
remote control writes the lines of [Remote control](#remote-control), and the retention pass
writes `retention pass complete` ([Retention](#retention)).

### Format versions

JSON `storage/` (two internal migrations,
[`storage.ts:83-200`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/storage.ts#L83-L200))
became SQLite through drizzle migrations under `packages/core/src/database/migration/2026...` (39
files); `opencode-*.db` was renamed `kilo-*.db`; `message`/`part` are kept beside `session_message`
("legacy-writer-compat", migration
[`20260714141136`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/core/src/database/migration/20260714141136_session-message-legacy-writer-compat.ts)).
Id prefixes: session `ses`, message `msg`/`msg_`, part `prt`
([`schema/src/session-id.ts:5`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-id.ts#L5),
[`v1/session.ts:17`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L17),[`23`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/v1/session.ts#L23),
[`session-message.ts:12`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/schema/src/session-message.ts#L12)).
`.kilocodemodes` has no references in current source and is legacy only.

OpenCode 2.0 moved sessions to a `session_v2` table; no `session_v2` table was found in Kilo Code's
packages at [`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22), so OpenCode's reading of it
([Format versions in `opencode.md`](opencode.md#format-versions)) applies only once Kilo Code takes
that store.

### Secrets

`auth.json`
([`packages/opencode/src/auth/index.ts:11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/auth/index.ts#L11)),
`credential.value`, `account.access_token`/`refresh_token`, `control_account`, and
`session.share_url`. The `storage/session_share/*.json` files hold no credential: the ingest service
authenticates with the Kilo token from `auth.json` ([Parser plan](#parser-plan)). The database is
collected unflagged like Cursor's `state.vscdb`; the tables above are the redaction targets
([issue 23](https://github.com/seanthegeek/doubleagent/issues/23)).

### Parser plan

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

#### Permission rows

The message's `agent` (V1 user and assistant, V2 assistant, V2 `agent-switched` `agent`) is tracked
the same way as the model ([Model](#model-rows)), as `permission mode: agent=<name>` and
`permission mode: agent=<old> -> agent=<new>`, because an agent (`build`, `plan` or a custom one) is
a mode that carries its own permission ruleset (the agent's `permission: PermissionV1.Ruleset`,
[`packages/opencode/src/agent/agent.ts:54`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/agent/agent.ts#L54)).
It does not read the project's `sandboxes` array ([Other stores](#other-stores)) or the `.kilo/`
and `.kilocode/` permission configuration files of a project
([Project-local files](#project-local-files);
[issue 98](https://github.com/seanthegeek/doubleagent/issues/98)).

Since the source review of 2026-10-21 it reads the records below, source-derived; not observed on
any real install. The code is OpenCode's with Kilo's changes, so the per-call, table and column
readers are the shared OpenCode parser's
([Permission rows of `opencode.md`](opencode.md#permission-rows)):

- Per call: a request is
  `{id, sessionID, permission, patterns, metadata, always, tool?{messageID, callID}}` and a reply is
  `once`, `always` or `reject`
  ([`packages/schema/src/v1/permission.ts:27-38`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/v1/permission.ts#L27-L38)).
  The `permission.asked` and `permission.replied` events are not durable, so they never reach the
  `event` table
  ([`:66-70`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/v1/permission.ts#L66-L70);
  [`packages/schema/src/event.ts:42-52`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/schema/src/event.ts#L42-L52)).
  What is stored is the tool part: a rejected call ends with `state.status` `error` and
  `state.error` `The user rejected permission to use this specific tool call.`, the same text
  followed by ` with the following feedback: <text>`, or, for a call a deny rule stopped,
  `The user has specified a rule which prevents you from using this specific tool call. Here are some of the relevant rules <JSON>`
  ([`packages/core/src/v1/permission.ts:7-27`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/v1/permission.ts#L7-L27);
  [`packages/opencode/src/permission/index.ts:314-333`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L314-L333)).
  The part's `state.error` is the error's message
  ([`packages/opencode/src/session/processor.ts:299-312`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/session/processor.ts#L299-L312),
  [`packages/tui/src/util/error.ts:125-133`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/tui/src/util/error.ts#L125-L133)).
  A reject also rejects every other pending request of the session. An approval leaves no mark on
  the part. The parser matches these prefixes and writes `permission decision: rejected`,
  `permission decision: rejected with feedback` or `permission decision: denied by rule` after the
  tool's `tool_result` row, with its `tool_name`, `callID` as `tool_use_id` and the result's time.
- Standing, written by the agent: an `always` reply adds `{<permission>: {<pattern>: "allow"}}` to
  the `permission` key of the first existing global config file among `kilo.jsonc`, `kilo.json`,
  `opencode.jsonc`, `opencode.json` and `config.json` in `~/.config/kilo`
  ([`packages/opencode/src/permission/index.ts:357-365`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L357-L365),
  [`packages/opencode/src/config/config.ts:206-215`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/config/config.ts#L206-L215),
  [`:1147-1153`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/config/config.ts#L1147-L1153)),
  and the extension's selective save writes `allow` and `deny` rules the same way
  ([`permission/index.ts:385-403`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L385-L403)).
  Protected configuration paths are downgraded to `once`
  ([`:338-340`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L338-L340)).
  The global config therefore records every standing grant the user gave, with the file's
  modification time as the only time. The `permission` key is one action or an object of
  permission names, each one action or an object of patterns to actions, `null` being Kilo's
  delete sentinel
  ([`packages/core/src/v1/config/permission.ts:5-56`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/core/src/v1/config/permission.ts#L5-L56);
  [`packages/opencode/src/permission/index.ts:522-543`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/permission/index.ts#L522-L543)).
  The parser reads each of the five files as JSONC and writes one `permission setting:
  permission.<permission>.<pattern>=<action> (from .config/kilo/<file>, file mtime)` row per rule,
  `permission.<permission>=<action>` for a rule given as one action and `permission=<action>` for a
  key that is one action, at the file's modification time with no session.
- Standing, the `permission` table and `session.permission` column of
  [Permission tables and columns](#permission-tables-and-columns): through the OpenCode reader,
  `permission setting: <action> <resource>=allow (from kilo.db permission, time_created)` per row
  and `permission setting: session <permission> <pattern>=<effect> (from kilo.db
  session.permission, time_updated)` per rule.
- Standing, the sandbox: each key of a policy file of [Per-user storage](#per-user-storage) is one
  `permission setting: sandbox.<key>=<value> (from <file>, file mtime)` row, and a preference file
  one `permission setting: sandbox.enabled=<true|false> (from <file>, file mtime)` row, with no
  session, since the file names are hashes. A file that is not the expected JSON is one `parser:`
  row.
- Not read: project `kilo.json` and `.kilo/` permission keys.

#### Model rows

A `system` row `model: <modelID> provider=<providerID>` precedes the first message of a
session that names a model (V1 user `model.{providerID, modelID}`, V1 assistant `providerID` and
`modelID`, V2 assistant `model.{id, providerID}`), and `model: <old> -> <new> provider=<providerID>`
precedes every later message, or stands for every V2 `model-switched` record, whose model differs.
Both these rows and the `permission mode:` rows of [Permission state](#permission-rows) take the
message's timestamp. Kilo writes V1 and V2 for every event ([`kilo.db`](#kilodb)) and the parser
reads V2 only for a session with no V1 rows, so for Kilo sessions the change rows come from the V1
messages and the V2 switch records are read only when V1 is missing.

#### Past-use rows and secondary sources

Since 2026-10-21, source-derived; not observed on any real install, the OpenCode reader takes
`~/.local/state/kilo/prompt-history.jsonl` ([TUI prompt history](#tui-prompt-history)) as a
secondary source (`secondary()`, `has_secondary` set): its lines carry no time, session or
directory, so each is a `user` row with an empty `timestamp_utc` that pairs with a transcript
prompt on text alone, and a shell command (`mode` `shell`) is a `tool_use` row with tool `shell`
and no id; what it survives is in [What survives a delete](#what-survives-a-delete). Its
`prompt-stash.jsonl` is a primary record of unsent prompts, one `system` row per line at its
`timestamp`, `prompt stashed (unsent): <text> (from .local/state/kilo/prompt-stash.jsonl,
timestamp)`. The remote control lines of the logs are under
[Sync, relay and origin rows](#sync-relay-and-origin-rows), `retention/state.json` under
[Deletion rows](#deletion-rows).

#### Sync, relay and origin rows

Sync: the share code is OpenCode's
([Sync, relay and origin rows of `opencode.md`](opencode.md#sync-relay-and-origin-rows)), and Kilo
changed what it calls.
Kilo replaced OpenCode's share service with its own cloud sessions: for a user signed in to Kilo (a
`kilo` entry in `auth.json`, or `KILO_API_KEY`,
[`packages/opencode/src/kilo-sessions/kilo-sessions.ts:199-210`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L199-L210)),
every new session is registered with `POST /api/session` on `https://ingest.kilosessions.ai`
(`KILO_SESSION_INGEST_URL` overrides) at creation
([`:245-272`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L245-L272),
[`:676-681`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L676-L681)),
and from then on every message, part, model and diff is posted to its `ingestPath`
([`:771-779`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L771-L779);
[`ingest-queue.ts:281-295`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/ingest-queue.ts#L281-L295)).
At [`87cc35c`](https://github.com/Kilo-Org/kilocode/commit/87cc35ce6904465a0eed507a8c75c79185863a22) the ingest queue's `session_status` item also carries a transition record, which
is sent to the server and not stored locally.
This is on by default once signed in; only `KILO_DISABLE_SESSION_INGEST` turns it off, and
`KILO_DISABLE_SHARE` blocks only the public link
([`:275-278`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilo-sessions/kilo-sessions.ts#L275-L278)).
`/share` and `/unshare` reach Kilo's service instead of OpenCode's
([`packages/opencode/src/share/session.ts:25-36`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/share/session.ts#L25-L36)),
whose `ShareNext` initialisation Kilo commented out
([`packages/opencode/src/project/bootstrap.ts:9-11`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/project/bootstrap.ts#L9-L11)),
so the upstream `session_share` table stays empty; `session.share_url` and the `session.updated.1`
events still record the public URL as upstream
([`packages/opencode/src/session/session.ts:1014-1016`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/session/session.ts#L1014-L1016)).

The marker is the `storage/session_share/<sessionID>.json` file
([Cloud session marker](#cloud-session-marker)). The parser yields one `system` row per
file, `session synced: kilo session <id> ingest <ingestPath> share <url or
-> (from storage/session_share/<sessionID>.json, file mtime)`, timestamped
by the file's modification time, with the session id from the file name;
a file that is not a JSON object is one `parser:` row. The OpenCode
reader also yields the event rows of
[Sync, relay and origin rows of `opencode.md`](opencode.md#sync-relay-and-origin-rows) from `kilo.db`
(`session.share_url` itself is not read). These rows are fixture only: no
real install has shown the marker file. What a delete does to the file and the remote copy is in
[What survives a delete](#what-survives-a-delete).

The service's `creating session`, `sharing`, `unsharing` and `removing share` lines are in the
logs ([Logs](#logs)); the parser does not read them.

A second uploader, session export to
`https://supermassive-black-hole.kiloapps.io/v1/session-export/batch` for personal accounts on free
Kilo gateway models, is compiled in but switched off (`enabled = false`) at this commit
([`kilocode/session-export/session-export.ts:35`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session-export/session-export.ts#L35),
[`worker/endpoint.ts:1`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session-export/worker/endpoint.ts#L1),
[`eligibility.ts:16-22`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/session-export/eligibility.ts#L16-L22));
its `session-export.db` and `session-export-workspace.json` sit in `<data>`
([`kilocode/bootstrap.ts:71-89`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/kilocode/bootstrap.ts#L71-L89)).

Telemetry goes to PostHog, a product analytics service
([`packages/kilo-telemetry/src/client.ts:9`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-telemetry/src/client.ts#L9),
level set by `KILO_TELEMETRY_LEVEL`,
[`telemetry.ts:89-91`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/kilo-telemetry/src/telemetry.ts#L89-L91));
a search of its event definitions for `prompt`, `text`, `content` and `message` found counts and
ids, not prompt text.

Origin and remote control: since 2026-10-21, source-derived; not observed on any real install, the
parser reads the remote control lines of `log/<time>.log` ([Remote control](#remote-control), in
the format of [Logs](#logs)) as `system` rows ending `(from log/<file>, <time basis>)`: `remote
control: connection enabled connected=<true|false>` and `remote control: connection disabled` at
the line's time; `remote control: session started model=<model> directory=<directory>` at the
line's `startedAt`, with `sessionID` as `session_id` and the directory as `project_path`; and
`remote control: session ended reason=<reason> durationMs=<n> startedAt=<time>` at the line's
time with the session. A line that ends with one of the four messages without its fields is a
`parser: unparseable line` row; every other log line is not read. These are neither sync nor relay
nor origin rows: remote control is a live control channel through which Kilo Cloud sends prompts
and receives the session's events for display
([`packages/opencode/src/kilo-sessions/remote-sender.ts:590-660`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/remote-sender.ts#L590-L660)),
the session it creates runs on the host and is stored in `kilo.db` like any other, and the copy
Kilo keeps is the ingest upload the session marker above records, so `records_relay` and
`records_origin` stay unset, as for Codex's remote control. A session cloned from a cloud session
records nothing of its origin ([Cloud session import](#cloud-session-import)).

#### Scratch directory rows

The agent's worktrees ([Scratch directories](#scratch-directories)) are named by the
`project_directory` rows of type `git_worktree` and by `project.sandboxes`
([Where the project path is recorded](#where-the-project-path-is-recorded)). Since 2026-10-21,
source-derived; not observed on any real install, the OpenCode reader writes one `system` row
`scratch directory: <directory> (git worktree of <project worktree> strategy=<strategy>) (from
kilo.db project_directory, time_created)` per `project_directory` row of type `git_worktree`, with
the directory as `project_path` and no session
([Scratch directory rows of `opencode.md`](opencode.md#scratch-directory-rows)). Remote attachments
go to a temp root outside the home and give no row.

#### Deletion rows

The retention pass deletes old sessions in bulk and vacuums the database ([Retention](#retention);
[What survives a delete](#what-survives-a-delete)). Since 2026-10-21, source-derived; not observed
on any real install, its `state.json` is one `system` row at its `at`, `sessions deleted by
retention: deleted=<n> scanned=<n> skippedActive=<n> failed=<n> durationMs=<n> (from
retention/state.json, at)`, with ` cancelled=true` and ` reclaimedBytes=<n>` before the source
when the file has them and `-` for an absent count, and no `session_id`, since the file names no
session. An archived session (`session.time_archived`) is a `session archived (from kilo.db
session, time_archived)` row through the OpenCode reader.

#### Bad-line rows

Every file the parser reads is covered. Each line of `prompt-history.jsonl` and
`prompt-stash.jsonl` that does not decode is its own `parser: unparseable line (<reason>): <line>`
row, read before Kilo's next start drops it; a log line that names a remote control message
without its fields is `parser: unparseable line (<message> without its fields): <line>`; a config,
sandbox or retention file that does not decode is one `parser:` row.

The `kilo-code` parser subclasses the `opencode` parser
([Bad-line rows of `opencode.md`](opencode.md#bad-line-rows)). Before analyzer 0.19.0 the OpenCode
parser counted undecodable database records, part files and events into one
`parser: <n> record(s) with undecodable data` row; since 0.19.0 each undecodable record, part file
and event is its own `parser: unparseable record <rowid> (<table>.data: <reason>): <data>` or
`parser: unparseable part <partID> (<reason>): <text>` row carrying it in full
([issue 139](https://github.com/seanthegeek/doubleagent/issues/139)), and a database with
`session_v2` ([Format versions](#format-versions)) is read from it, its `session_message` transcript
and the 1.x tables only for a session that `session_message` lacks
([issue 165](https://github.com/seanthegeek/doubleagent/issues/165)). Both reach Kilo Code through
the subclass.

#### Fixtures

```json
{"_table":"session","record":{"id":"ses_01JAX","project_id":"prj_01JAX","parent_id":null,"slug":"fix-tests","directory":"/home/u/proj","title":"fix tests","version":"1.0.0","agent":"build","model":"{\"id\":\"claude-sonnet-4-5\",\"providerID\":\"anthropic\"}","time_created":1760000000000,"time_updated":1760000005000}}
{"_table":"message","record":{"id":"msg_01JAXA","session_id":"ses_01JAX","time_created":1760000002000,"data":"{\"role\":\"assistant\",\"parentID\":\"msg_01JAXU\",\"modelID\":\"claude-sonnet-4-5\",\"providerID\":\"anthropic\",\"mode\":\"build\",\"agent\":\"build\",\"path\":{\"cwd\":\"/home/u/proj\",\"root\":\"/home/u/proj\"},\"cost\":0.0041,\"tokens\":{\"input\":1200,\"output\":80,\"reasoning\":0,\"cache\":{\"read\":900,\"write\":0}},\"time\":{\"created\":1760000002000,\"completed\":1760000003000}}"}}
{"_table":"part","record":{"id":"prt_01JAXT","message_id":"msg_01JAXA","session_id":"ses_01JAX","time_created":1760000002500,"data":"{\"type\":\"tool\",\"callID\":\"call_1\",\"tool\":\"bash\",\"state\":{\"status\":\"completed\",\"input\":{\"command\":\"pytest -q\"},\"output\":\"3 passed\",\"title\":\"pytest -q\",\"metadata\":{},\"time\":{\"start\":1760000002500,\"end\":1760000003000}}}"}}
{"_table":"session_message","record":{"id":"msg_01JAXB","session_id":"ses_01JAX","type":"assistant","seq":4,"time_created":1760000002000,"data":"{\"agent\":\"build\",\"model\":{\"providerID\":\"anthropic\",\"modelID\":\"claude-sonnet-4-5\"},\"content\":[{\"type\":\"tool\",\"id\":\"call_1\",\"name\":\"bash\",\"state\":{\"status\":\"completed\",\"input\":{\"command\":\"pytest -q\"},\"content\":[{\"type\":\"text\",\"text\":\"3 passed\"}],\"structured\":{}},\"time\":{\"created\":1760000002500,\"completed\":1760000003000}}],\"time\":{\"created\":1760000002000,\"completed\":1760000003000}}"}}
```

State files, one record each (prompt history, prompt stash, global config, sandbox policy,
retention state):

```json
{"input":"fix the tests","parts":[]}
{"input":"stashed idea","parts":[],"timestamp":1760000009000}
{"permission":{"bash":{"git status":"allow","rm *":"deny"},"webfetch":"ask"}}
{"enabled":true,"mode":"proxy","allowedHosts":["registry.npmjs.org"],"writablePaths":["/home/u/proj"],"version":3}
{"at":1760007200000,"scanned":40,"deleted":12,"skippedActive":1,"failed":0,"durationMs":830}
```

Log lines, in the format of [Logs](#logs):

```text
INFO  2026-10-03T10:00:05 +12ms service=kilo-sessions connected=true remote connection enabled
INFO  2026-10-03T10:00:09 +40ms service=kilo-sessions sessionID=ses_01JAX startedAt=2026-10-03T10:00:09.250Z model=anthropic/claude-sonnet-4-5 directory=/home/u/proj remote session started
```

#### Source host rows

The agent's source-host integrations are server-side, and the parser yields no `source host:`
row. Kilo Cloud Agents run a remote task on a GitHub, GitLab or plain git repository
(`kilo cloud start --repo <repo> --repo-type github|gitlab|git`,
[`packages/opencode/src/kilocode/cli/cmd/cloud.ts:12-45`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/cli/cmd/cloud.ts#L12-L45);
[`packages/opencode/src/kilocode/cloud/repository.ts:4-25`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilocode/cloud/repository.ts#L4-L25)):
the repository access and its grant belong to the Kilo account on the server, and the cloud
commands write no local file (grepped `packages/opencode/src/kilocode/cloud` for writes and
storage calls at `87cc35c`), so the remote conversation is fetched each time. The GitHub Copilot
model provider's device flow asks for `read:user` and keeps its token in `auth.json` under
`github-copilot`
([`packages/opencode/src/plugin/github-copilot/copilot.ts:94-95`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/plugin/github-copilot/copilot.ts#L94-L95),
[`:243`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/plugin/github-copilot/copilot.ts#L243));
GitLab sign-in comes from the third-party `opencode-gitlab-auth` package
([`packages/opencode/src/plugin/index.ts:17`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/plugin/index.ts#L17)),
whose storage this repository does not show. Neither records the account's login. For the CLI,
Kilo also records the pull request a session owns, from a `gh pr create` or push the session made
or a `kilo pr link <url>`, in `<data>/storage/session_pr_link_session/<sessionID>.json`,
`{link: {platform, prUrl, prNumber}, headRef?, headSha?, evidence}` with `evidence` in
`pr_create|push|user`
([`packages/opencode/src/kilo-sessions/pr-link.ts:14-41`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/pr-link.ts#L14-L41),
[`:363-373`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/kilo-sessions/pr-link.ts#L363-L373);
[`packages/opencode/src/cli/cmd/pr.ts:205`](https://github.com/Kilo-Org/kilocode/blob/87cc35ce6904465a0eed507a8c75c79185863a22/packages/opencode/src/cli/cmd/pr.ts#L205));
the file is collected with `~/.local/share/kilo` and not parsed.

## Confidence

- High: XDG roots, db names, auth files, project table columns, project dotfiles; drizzle columns
  and V1/V2 struct fields (read from source).
- Medium: V2 `session_message.data` serialised key order and the `Model.Ref` shape.
- Low: contents of `globalStorage/kilocode.kilo-code` on current installs beyond `globalState`;
  nothing in `kilo-vscode` writes files there.
- Not determined: which permission service the shipped CLI uses, the 1.x one that writes "always"
  grants into the global config and refusal texts into `state.error`, or the newer one that saves
  grants in the `permission` table; the parser reads both ([Permission rows](#permission-rows)).
- Not determined: where the `opencode-gitlab-auth` package keeps a GitLab sign-in.
- Not determined: the code path that imports legacy JSON `storage/` into SQLite
  ([`packages/opencode/src/storage/db.ts`](https://github.com/Kilo-Org/kilocode/blob/76bcfd40be616a72f4697b3041565f322245b462/packages/opencode/src/storage/db.ts),
  not traced).
