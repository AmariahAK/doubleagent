# little-coder

little-coder is a launcher plus a fixed set of extensions for the [pi](pi.md) coding agent: a
terminal CLI that spawns pi's own CLI and writes its sessions into pi's directory, `~/.pi/agent`,
beside a few files of its own. The retired v0.0.x releases were a separate Python
implementation with their own state in `~/.little-coder`. The record schema is in
[`analyzer/research/little-coder.md`](../../analyzer/research/little-coder.md).

Catalog agent: `little-coder`. little-coder is a launcher and extension set
for the pi coding agent, so its transcripts are pi session files written by
pi itself. This document covers what little-coder adds and how to tell its
sessions from plain pi sessions; the full pi record schema is in [`pi.md`](pi.md). Paths are in
[`collectors/research/little-coder.md`](../../collectors/research/little-coder.md).

<!-- MERGE: dedupe the intro paragraphs above into one -->

## 1. Source and evidence

[itayinbarr/little-coder](https://github.com/itayinbarr/little-coder) at [`89d4fa0af864230527ab75d12604ed0eb320e6df`](https://github.com/itayinbarr/little-coder/commit/89d4fa0af864230527ab75d12604ed0eb320e6df),
version 1.20.0, Apache-2.0 ([package.json:3](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/package.json#L3), [10](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/package.json#L10)). Open source,
TypeScript and Node. All claims from source. little-coder depends on the pi coding agent
(`@earendil-works/pi-coding-agent` `^0.83.0`, [package.json:41](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/package.json#L41)); it spawns
pi's own CLI from its `node_modules` ([bin/little-coder.mjs:98-136](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L98-L136),
[505-509](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L505-L509)). pi's storage was therefore read at [earendil-works/pi](https://github.com/earendil-works/pi) tag
`v0.83.0`, [`845d6ff1f6643aba440341cce877ce1c43ebbc39`](https://github.com/earendil-works/pi/commit/845d6ff1f6643aba440341cce877ce1c43ebbc39).

[itayinbarr/little-coder](https://github.com/itayinbarr/little-coder) at [`89d4fa0af864230527ab75d12604ed0eb320e6df`](https://github.com/itayinbarr/little-coder/commit/89d4fa0af864230527ab75d12604ed0eb320e6df),
Apache-2.0. It depends on `@earendil-works/pi-coding-agent` `^0.83.0`
([package.json:41](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/package.json#L41)), read at [earendil-works/pi](https://github.com/earendil-works/pi) `v0.83.0`,
[`845d6ff1f6643aba440341cce877ce1c43ebbc39`](https://github.com/earendil-works/pi/commit/845d6ff1f6643aba440341cce877ce1c43ebbc39).

The retired v0.0.x Python implementation, which kept its own state in
`~/.little-coder` and had a Gist sync command, was read at tag `v0.0.5`,
[`424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03`](https://github.com/itayinbarr/little-coder/commit/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03),
for sync only (2026-10-17).

Confidence. High: file locations, header and entry fields, message roles,
`lc-*` custom types, sub-agents unsaved (source). Medium: that every
little-coder session contains an `lc-` entry; with injection set to
`system` mode and no plan, bg-shell or research use, a session may carry
none, and then only `provider: "llamacpp"` hints at it. Not determined:
the exact `usage` sub-fields beyond those shown ([types.ts:368-380](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/ai/src/types.ts#L368-L380)).

<!-- MERGE: dedupe the section 1 prose above -->

### Observed

- No real install.

- No real install.

<!-- MERGE: dedupe the Observed bullets above -->

### Source reviews

- 2026-10-19: `main` of [itayinbarr/little-coder](https://github.com/itayinbarr/little-coder) is still [`89d4fa0`](https://github.com/itayinbarr/little-coder/commit/89d4fa0af864230527ab75d12604ed0eb320e6df) and still pins pi `^0.83.0`, so every path here holds. By class:
  - Permission state: the `permission-gate` extension's mode and allow list are the
    environment variables `LITTLE_CODER_PERMISSION_MODE` and `LITTLE_CODER_BASH_ALLOW`, not
    files; its refusals are in the session files
    ([Source reviews](#source-reviews) of the analyzer
    document).
  - Model, past use, sync: no new file.
  - Scratch directories: none under the home ([Scratch directories](#scratch-directories)).
  - Deletion: `/clear` starts a new pi session and deletes nothing.
  - Version drift: none.
  - Bad lines: not a collector concern.

- 2026-10-19: the head of
  [itayinbarr/little-coder](https://github.com/itayinbarr/little-coder)
  `main` on 2026-10-19 is still
  [`89d4fa0`](https://github.com/itayinbarr/little-coder/commit/89d4fa0af864230527ab75d12604ed0eb320e6df),
  the commit cited throughout, and it still pins pi `^0.83.0`
  ([package.json:41](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/package.json#L41)),
  so there is no drift; the review read it again for the requirement
  classes. Source only. By class:
  - Permission state: found, not read as decisions. The
    `permission-gate` extension decides each shell and edit call by the
    mode in `LITTLE_CODER_PERMISSION_MODE` (`auto`, the default,
    `accept-all` or `manual`) and the extra allowed prefixes in
    `LITTLE_CODER_BASH_ALLOW`
    ([.pi/extensions/permission-gate/index.ts:5-19](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/index.ts#L5-L19),
    [268-272](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/index.ts#L268-L272));
    both are environment variables, so no file holds the standing
    state. In `manual` mode the user is asked per call: edits offer
    Apply, Deny and "Apply all (this session)", the last kept in memory
    ([permission-gate/manual-edit-confirm.ts:5-37](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/manual-edit-confirm.ts#L5-L37)),
    shell commands a yes or no. A refusal blocks the call with a reason,
    `edit cancelled by user`, `command cancelled by user`, or in `auto`
    mode a text starting `shell whitelist:`
    ([index.ts:288](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/index.ts#L288),
    [303](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/index.ts#L303),
    [315](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/index.ts#L315),
    [330](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/index.ts#L330),
    [354](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/permission-gate/index.ts#L354)),
    and pi 0.83.0 records a blocked call as a `toolResult` with that
    reason as its text and `isError` true
    ([packages/agent/src/agent-loop.ts:636-642](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/agent/src/agent-loop.ts#L636-L642),
    [756-761](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/agent/src/agent-loop.ts#L756-L761)).
    An approval leaves no record beyond the call's normal result. The
    pi parser shows the refusal as an ordinary `tool_result` row.
  - Model: covered. The `phase-model` extension switches the model at
    plan and implementation phases through `pi.setModel`
    ([.pi/extensions/phase-model/index.ts:169](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/phase-model/index.ts#L169)),
    and pi 0.83.0's `setModel` appends a `model_change` entry
    ([packages/coding-agent/src/core/agent-session.ts:1578-1586](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/agent-session.ts#L1578-L1586)),
    which pi's reader turns into a `model:` row.
  - Past use: covered (the prompt history and the checkpoints); no
    other store found.
  - Sync, relay and origin: covered; none in the current releases.
  - Scratch directories: `/deep-research` runs its research agents in
    a fresh `<tmpdir>/deep-research-*` directory and removes it when
    done
    ([.pi/extensions/deep-research/index.ts:167-176](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/deep-research/index.ts#L167-L176),
    [257](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/deep-research/index.ts#L257));
    those agents run with `--no-session`, so no record names it. None
    under the home.
  - Deletion: `/clear` is an alias for pi's new-session command and
    deletes nothing
    ([.pi/extensions/clear-command/index.ts:18-23](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/clear-command/index.ts#L18-L23));
    a session file goes only through pi's own picker
    ([What survives a delete in `pi.md`](pi.md#what-survives-a-delete)), which leaves the checkpoint
    directory and the prompt history behind.
  - Version drift: none.
  - Bad lines: covered; the prompt history reader reports a bad record.

<!-- MERGE: dedupe the Source reviews above -->

## Collection

### 2. Per-user storage

#### Shared with pi: `~/.pi/agent`

The launcher and pi both use
`PI_CODING_AGENT_DIR` (with `~` expansion) or `homedir()/.pi/agent` on every
OS ([little-coder.mjs:24-35](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L24-L35); pi
[packages/coding-agent/src/config.ts:491-496](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/config.ts#L491-L496), [515-521](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/config.ts#L515-L521)). In it pi
keeps `settings.json`, `auth.json`, `models.json`,
`themes/`, `tools/`, `bin/` (fd, rg), `prompts/`, `pi-debug.log` and
`sessions/` ([config.ts:523-566](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/config.ts#L523-L566)). Sessions are
`sessions/--<cwd with / \ : replaced by ->--/<ISO timestamp>_<uuid>.jsonl`
([packages/coding-agent/src/core/session-manager.ts:476-481](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L476-L481), [950-953](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L950-L953)),
overridable by `PI_CODING_AGENT_SESSION_DIR` ([config.ts:495-496](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/config.ts#L495-L496)).
little-coder sessions and plain pi sessions share this directory and
cannot be told apart by path. little-coder itself writes:

- `settings.json`: merges `quietStartup: true` and `lastChangelogVersion`
  on each interactive launch ([little-coder.mjs:400-466](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L400-L466)); a v1.9.0
  keybinding is removed from `keybindings.json` ([:468-490](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L468-L490)).
- `little-coder-prompt-history.json`: a JSON array of the last 100 prompts
  typed, no timestamps ([.pi/extensions/prompt-history/index.ts:23-26](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/prompt-history/index.ts#L23-L26), [38-40](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/prompt-history/index.ts#L38-L40), [52-57](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/prompt-history/index.ts#L52-L57)).

#### Checkpoints: `~/.little-coder/checkpoints/<session file name>/`

Before a `write` or
`edit` tool call, the first time per session, a copy of the target file's
previous contents is saved under a name derived from its path (non
`[A-Za-z0-9._-]` characters become `_`, last 200 characters), or an empty
`<name>.absent` if it did not exist
([.pi/extensions/checkpoint/index.ts:6-9](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/checkpoint/index.ts#L6-L9), [25-58](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/checkpoint/index.ts#L25-L58)). The directory is the session
file's basename, so it matches a `sessions/` JSONL file
([:63-65](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/checkpoint/index.ts#L63-L65)). `homedir()` on every OS.

#### Configuration: `~/.config/little-coder/`

`~/.config/little-coder/`, or `$XDG_CONFIG_HOME/little-coder`, using
`HOME` or `USERPROFILE`, so `~/.config` on macOS and Windows too:

- `models.json`, the user's provider override (`LITTLE_CODER_MODELS_FILE`
  wins) ([little-coder.mjs:46-56](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L46-L56); [.pi/extensions/llama-cpp-provider/config.ts:75-82](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/llama-cpp-provider/config.ts#L75-L82)).
- `extensions/`, user extensions loaded on every launch
  (`LITTLE_CODER_EXTENSIONS_DIR` wins) ([bin/user-extensions.mjs:17-22](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/user-extensions.mjs#L17-L22), [37-51](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/user-extensions.mjs#L37-L51)).

#### Update check: `~/.cache/little-coder/version-check.json`

`~/.cache/little-coder/version-check.json` (or `$XDG_CACHE_HOME`):
update check timestamp and latest version ([bin/update-check.mjs:33-37](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/update-check.mjs#L33-L37)).

#### Package install

The package itself (`.pi/extensions/`, `AGENTS.md` used as the system
prompt, `skills/`, bundled `models.json`) lives in the global npm or bun
install, not the home ([little-coder.mjs:163](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L163), [314](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L314)).

#### Scratch directories

None known under the home. little-coder works in the user's cwd. Its one directory of its own, `/deep-research`'s `<tmpdir>/deep-research-*`, is in the system temporary directory and removed when the research ends ([.pi/extensions/deep-research/index.ts:167-176](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/deep-research/index.ts#L167-L176), [257](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/deep-research/index.ts#L257)); no catalog line can hold it and nothing records it. `~/.little-coder/checkpoints/` holds copies of project files, not a working directory.

#### Deletion

What a delete leaves (the checkpoints and the prompt history) is in
[What survives a delete](#what-survives-a-delete).

### 3. Credentials

- `~/.pi/agent/auth.json`, pi's credential store, mode 0600
  ([packages/coding-agent/src/core/auth-storage.ts:21](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/auth-storage.ts#L21), [31](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/auth-storage.ts#L31)). Belongs to pi.
- `~/.config/little-coder/models.json`: `providers.<name>.apiKey` is meant
  to name an environment variable, but a value that names none is used as a
  literal key ([config.ts:4-14](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/llama-cpp-provider/config.ts#L4-L14), [294-300](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/llama-cpp-provider/config.ts#L294-L300)). Flag it.
- `~/.little-coder/config.json` of the v0.0.x Python releases holds
  `gist_token`, a GitHub personal access token with the `gist` scope;
  secret glob `.little-coder/config.json` from collector 1.14.0. Evidence
  in
  [section 12 of `analyzer/research/little-coder.md`](#12-secrets).
- No keychain use.

### 4. Exclusions

None. Checkpoints are copies of project files and can be large on a busy
host, but they are pre-edit evidence; keep them.

### 5. Project-local files

- `.pi/approved-plan.md`, written by the plan mode in the session's cwd
  ([.pi/extensions/plan-mode/index.ts:20](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/plan-mode/index.ts#L20), [740-742](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/plan-mode/index.ts#L740-L742)).
- Reads `AGENTS.md`, then `CLAUDE.md`, from the project
  ([.pi/extensions/project-context/discover.ts:21-27](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/project-context/discover.ts#L21-L27)); pi's own project
  context loading is turned off with `--no-context-files`, and project
  `.pi/extensions` load only with `--with-pi-extensions`
  ([little-coder.mjs:222-228](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L222-L228), [365-372](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/little-coder.mjs#L365-L372)).
- `/deep-research` writes its report into the cwd
  ([.pi/extensions/deep-research/index.ts:366-367](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/deep-research/index.ts#L366-L367)).

### 6. Where the project path is recorded

The pi session header line: `{"type":"session",...,"cwd":...}`
([session-manager.ts:32-39](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L32-L39), [936-944](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L936-L944)), and the encoded
session directory name. Checkpoint file names encode absolute paths, but
lossily (`/` becomes `_`).

## Parsing

### 7. Transcript stores

- `.pi/agent/sessions/--<encoded cwd>--/<ISO timestamp with - for : and .>_<uuid>.jsonl`,
  one file per session, appended per entry
  ([packages/coding-agent/src/core/session-manager.ts:476-481](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L476-L481), [950-953](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L950-L953)).
  Shared with plain pi.
- `.pi/agent/little-coder-prompt-history.json`: JSON array of up to 100
  prompt strings, oldest first, no timestamps or session ids
  ([.pi/extensions/prompt-history/index.ts:26](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/prompt-history/index.ts#L26), [38-40](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/prompt-history/index.ts#L38-L40), [52-57](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/prompt-history/index.ts#L52-L57)).
- `.little-coder/checkpoints/<session file name>/<mangled path>`: pre-edit
  file copies, not transcripts, but they join to a session by name
  ([.pi/extensions/checkpoint/index.ts:25-29](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/checkpoint/index.ts#L25-L29), [63-65](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/checkpoint/index.ts#L63-L65)).

Sub-agents run pi with `--no-session`, so they leave no file
([.pi/extensions/subagent/spawn.ts:14](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/subagent/spawn.ts#L14), [318-322](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/subagent/spawn.ts#L318-L322)).

#### What survives a delete

little-coder has no delete of its own: `/clear` is an alias for pi's
new-session command and deletes nothing
([.pi/extensions/clear-command/index.ts:18-23](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/clear-command/index.ts#L18-L23)).
A session file is removed only through pi's own session picker
([What survives a delete in `pi.md`](pi.md#what-survives-a-delete)), which leaves two things
behind: the session's checkpoint directory
`.little-coder/checkpoints/<session file name>/`, whose name still joins
its pre-edit file copies to the session, and the prompt history
`little-coder-prompt-history.json`, the last 100 prompts with no time and
no session id
([.pi/extensions/prompt-history/index.ts:26](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/prompt-history/index.ts#L26)).
No deletion marker is written. The analyzer reads both: the prompt
history as `user` rows with no timestamp and no session
([Past use and secondary sources](#past-use-rows-and-secondary-sources)), and the checkpoints, which
[Source reviews](#source-reviews) counts as covered past use.

### 8. Record schema

pi session format version 3
([session-manager.ts:30](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L30)). Line 1 is the header
`{type:"session", version, id, timestamp (ISO), cwd, parentSession?}`
([:32-39](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L32-L39)). Every other line has `type`, `id`, `parentId`, `timestamp`
(ISO) ([:46-51](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L46-L51)) and is one of `message`, `thinking_level_change`,
`model_change` (`provider`, `modelId`), `compaction`, `branch_summary`,
`custom`, `custom_message`, `label`, `session_info` ([:53-153](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L53-L153)).

`message.message` ([packages/ai/src/types.ts:393-431](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/ai/src/types.ts#L393-L431)):

- `user`: `content` string or `text`/`image` parts, `timestamp` (Unix ms).
- `assistant`: `content[]` of `text`, `thinking` (`thinking`), `toolCall`
  (`id`, `name`, `arguments` object) ([:338-366](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/ai/src/types.ts#L338-L366)); `provider`, `model`,
  `usage`, `stopReason` (`stop|length|toolUse|error|aborted`, [:391](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/ai/src/types.ts#L391)),
  `errorMessage`, `timestamp` (ms).
- `toolResult`: `toolCallId`, `toolName`, `content[]`, `isError`, `timestamp`.
- pi's own roles `bashExecution` (`command`, `output`, `exitCode`),
  `custom`, `branchSummary`, `compactionSummary`
  ([packages/coding-agent/src/core/messages.ts:29-67](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/messages.ts#L29-L67)).

Extension messages become `custom_message` entries with `customType`,
`content`, `display`, `details` ([session-manager.ts:135-141](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L135-L141);
[packages/coding-agent/src/core/agent-session.ts:624-633](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/agent-session.ts#L624-L633)).

#### little-coder markers

Its extensions tag what they inject:
`lc-skills`, `lc-knowledge`, `lc-project-context`
([.pi/extensions/_shared/inject.ts:49-64](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/_shared/inject.ts#L49-L64); [skill-inject/index.ts:393](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/skill-inject/index.ts#L393);
[knowledge-inject/index.ts:169](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/knowledge-inject/index.ts#L169); [project-context/index.ts:96](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/project-context/index.ts#L96)),
`lc-bg-shell` with `details.id` ([bg-shell/index.ts:134-135](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/bg-shell/index.ts#L134-L135)), `lc-plan`,
`lc-approved-plan` ([plan-mode/index.ts:394](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/plan-mode/index.ts#L394), [817](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/plan-mode/index.ts#L817)), `lc-research`
([deep-research/index.ts:334](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/deep-research/index.ts#L334)). Injection can instead go into the
system prompt (`injectMode` `system`), which leaves no entry
([inject.ts:60-62](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/_shared/inject.ts#L60-L62)). Assistant `provider` is commonly `llamacpp`,
little-coder's local provider ([.pi/extensions/llama-cpp-provider/index.ts:172](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/llama-cpp-provider/index.ts#L172);
[models.json:2-4](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/models.json#L2-L4)).

### 9. Joins and timestamps

Session id: header `id`, also in the file name. Tree: `parentId` → `id`.
Tool use to result: `toolCall.id` = `toolResult.toolCallId`. Project path:
header `cwd`. Forked sessions: header `parentSession`. Checkpoint directory
name = session file basename.

### 10. Other stores

None besides the prompt history and the checkpoints of [section 7](#7-transcript-stores): no
SQLite or binary store. Images are base64 inside `image` parts ([types.ts:354-358](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/ai/src/types.ts#L354-L358)).

### 11. Format versions

pi header `version` (absent in v1 files, 3 now,
[session-manager.ts:30-35](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/core/session-manager.ts#L30-L35)). little-coder pins pi 0.83.x; a release that moves
to pi 1.x should be re-checked against pi's research.

### 12. Secrets

Session files store tool inputs and outputs verbatim; `thinkingSignature`
and `thoughtSignature` are opaque provider blobs ([types.ts:344-366](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/ai/src/types.ts#L344-L366)).
Credentials are in `auth.json`, not in sessions.

The v0.0.x Python releases kept a GitHub personal access token with the
`gist` scope as `gist_token` in `~/.little-coder/config.json`
([cloudsave.py:9-12](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/cloudsave.py#L9-L12),
[little_coder.py:1371-1384](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/little_coder.py#L1371-L1384),
[config.py:6-7](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/config.py#L6-L7)).

### 13. Parser plan

Use the pi parser for `.pi/agent/sessions/*/*.jsonl` and label a session
`little-coder` when it contains any `custom_message` whose `customType`
starts with `lc-`; otherwise leave it `pi`. Parse
`little-coder-prompt-history.json` as `user` rows with no timestamp and no
session.

| Column | Source |
| --- | --- |
| timestamp_utc | entry `timestamp` (ISO); `message.timestamp` (ms) as fallback |
| session_id | header `id` |
| project_path | header `cwd` |
| git_branch | empty |
| turn_type | `user`, `assistant`; `toolCall` → tool_use; `toolResult` → tool_result; `thinking` → thinking; `custom_message`, `model_change`, `compaction`, `bashExecution` → system |
| model | assistant `provider`/`model`; a `model: <id> provider=<provider>` `system` row at the first assistant message that names a model and `model: <old> -> <new> provider=<provider>` on each change, from pi's reader ([Model in `pi.md`](pi.md#model-rows)) |
| tool_name, tool_use_id | `toolCall.name`/`id`; `toolResult.toolName`/`toolCallId` |
| text | text parts; tool_use: `arguments.command` or `path`, else JSON; tool_result: text parts |

#### Permission rows

Permission decisions of the `permission-gate`
extension are on disk as error `toolResult` rows whose text is
`edit cancelled by user`, `command cancelled by user` or starts
`shell whitelist:` ([Source reviews](#source-reviews)); a `permission decision: denied (<reason>)`
row joined on the `toolCallId` would show them as decisions. The pi parser shows the refusal as an
ordinary `tool_result` row today. There is no standing state on disk to read: the mode and the
allow list are environment variables.

#### Model rows

Covered through pi's `model_change` rows: the `phase-model` extension's switches become
`model_change` entries, which pi's reader turns into `model:` rows
([Model in `pi.md`](pi.md#model-rows)).

#### Past-use rows and secondary sources

The prompt history is read on every run, as above, and is the one secondary source. The
checkpoints of [section 7](#7-transcript-stores) are covered past use. No other store found.

#### Sync, relay and origin rows

On the pi it pins (0.83.x) little-coder inherits pi's `/share`,
which uploads a session as a secret GitHub gist through `gh` and leaves
no local marker; pi's `/bug` upload and its `pi.bug-report` entry
arrived after 0.83.0
([0.83.0 interactive-mode.ts:5523-5608](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/src/modes/interactive/interactive-mode.ts#L5523-L5608);
[Sync, relay and origin in `pi.md`](pi.md#sync-relay-and-origin-rows)).
little-coder's own extensions add no upload: a search of `bin/` and
`.pi/extensions/` for `gist`, `upload`, `share`, `telemetry` and
`fetch(` finds only the npm update check
([bin/update-check.mjs:106](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/bin/update-check.mjs#L106))
and the research and browser tools. The v0.0.x Python releases had
`/cloudsave`, opt-in: `/cloudsave setup <token>` stores the token,
`/cloudsave` or `/cloudsave push [desc]` uploads the conversation as a
private gist described `[little-coder] <desc or time>` holding
`little-coder_session_<time>.json`, and `/cloudsave auto on` uploads at
`/exit` ([cloudsave.py:73-101](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/cloudsave.py#L73-L101),
[little_coder.py:1386-1400](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/little_coder.py#L1386-L1400),
[1443-1459](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/little_coder.py#L1443-L1459),
[1471-1486](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/little_coder.py#L1471-L1486)). Each upload records only
the newest gist id, `cloudsave_last_gist_id` in
`~/.little-coder/config.json`, and later pushes update that same gist in
place, so the key names one gist for every upload since the first
([little_coder.py:1451-1457](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/little_coder.py#L1451-L1457)); the
uploaded `session_id` is a fresh random 8-hex value that matches no
local session file
([little_coder.py:1331-1336](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/little_coder.py#L1331-L1336)). The
automatic path passes `existing_gist_id=`, a keyword
`upload_session` does not take, so it fails with a `TypeError` before
any upload ([little_coder.py:1477-1480](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/little_coder.py#L1477-L1480),
[cloudsave.py:73-78](https://github.com/itayinbarr/little-coder/blob/424f7a4b9f9214a36a6bcb69e1f3435ca3e68d03/cloudsave.py#L73-L78)). The current parser does
not read the v0.0.x layout; when it does, the row is one `system` row
`session synced: gist <cloudsave_last_gist_id> (from
.little-coder/config.json, file mtime)`, at the file's modification time,
with an empty session id.

The current releases sync nothing of their own, and no session is relayed or of remote origin.

#### Scratch directory rows

None in the home. `/deep-research`'s `<tmpdir>/deep-research-*` directory is removed when done
and no record names it ([Source reviews](#source-reviews)).

#### Deletion rows

No marker; see [What survives a delete](#what-survives-a-delete).

#### Bad-line rows

Covered: the session files go through pi's reader
([Bad lines in `pi.md`](pi.md#bad-line-rows)), and the prompt history reader reports a bad record.

#### Fixtures

Fixture:

```json
{"type":"session","version":3,"id":"0b9e2f4c-1111-4000-8000-000000000001","timestamp":"2026-10-01T09:00:00.000Z","cwd":"/home/alice/proj"}
{"type":"custom_message","id":"a1","parentId":null,"timestamp":"2026-10-01T09:00:01.000Z","customType":"lc-skills","content":"## Skill: edit\nUse the edit tool.","display":false}
{"type":"message","id":"a2","parentId":"a1","timestamp":"2026-10-01T09:00:02.000Z","message":{"role":"user","content":"fix the failing test","timestamp":1759309202000}}
{"type":"message","id":"a3","parentId":"a2","timestamp":"2026-10-01T09:00:05.000Z","message":{"role":"assistant","content":[{"type":"thinking","thinking":"run tests first"},{"type":"toolCall","id":"call_1","name":"bash","arguments":{"command":"npm test"}}],"api":"openai-completions","provider":"llamacpp","model":"qwen3.6-35b-a3b","usage":{"input":900,"output":40,"cacheRead":0,"cacheWrite":0},"stopReason":"toolUse","timestamp":1759309205000}}
{"type":"message","id":"a4","parentId":"a3","timestamp":"2026-10-01T09:00:09.000Z","message":{"role":"toolResult","toolCallId":"call_1","toolName":"bash","content":[{"type":"text","text":"1 failing"}],"isError":false,"timestamp":1759309209000}}
```

`little-coder-prompt-history.json`: `["fix the failing test","now run lint"]`

## 14. Confidence

High: every path above, the env overrides, the checkpoint naming, the
prompt history format, that sessions are pi's (source). High for pi paths
at v0.83.0 (source at the tag); a later little-coder that moves to pi 1.x
may differ. Medium: on Windows the checkpoint directory name, since the
extension splits the session path on `/` only
([checkpoint/index.ts:64](https://github.com/itayinbarr/little-coder/blob/89d4fa0af864230527ab75d12604ed0eb320e6df/.pi/extensions/checkpoint/index.ts#L64)) and a backslash path would not be
split. Not determined: real sizes of `checkpoints/`; whether pi project
files beyond `.pi/approved-plan.md` are written when `--with-pi-extensions`
is used (that is pi's behaviour, covered by pi's own research).
