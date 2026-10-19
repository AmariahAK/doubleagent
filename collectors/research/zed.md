# Zed: on-disk paths

## 1. Source and evidence level

[zed-industries/zed](https://github.com/zed-industries/zed), open source, commit [`a84689073d296dfd39987bc7dd478e43ef76d83a`](https://github.com/zed-industries/zed/commit/a84689073d296dfd39987bc7dd478e43ef76d83a) (blobless partial clone). Platform mapping verified against the `dirs` 6.0.0 crate (`scratchpad/crates/dirs/dirs-6.0.0`, version from `Cargo.lock`). Flatpak sandbox paths are Flatpak documentation level. Transcript schema is in [`analyzer/research/zed.md`](../../analyzer/research/zed.md).

- **Source review (2026-10-19)**: [zed-industries/zed](https://github.com/zed-industries/zed)
  at [`9cd14da`](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6)
  (the default branch on 2026-10-19), against
  [`a846890`](https://github.com/zed-industries/zed/commit/a84689073d296dfd39987bc7dd478e43ef76d83a)
  cited below. The paths in [section 2](#2-per-user-storage) are
  unchanged at HEAD (the data, config, logs and database directories,
  `threads/threads.db` and `db/0-<channel>/db.sqlite`); only line
  numbers moved by one or two. New for the collector, all from source:
  - Permission state: `settings.json` (already collected and flagged
    secret) now carries the standing tool rules `agent.tool_permissions`
    and the sandbox grants `agent.sandbox_permissions`, both written by
    Zed on an "Always allow" choice, and `db.sqlite` (collected) holds
    the trusted project list in table `trusted_worktrees`; details in
    [section 8 of `analyzer/research/zed.md`](../../analyzer/research/zed.md#8-parser-plan).
  - Past use: draft prompts, the created-worktree registry, archived
    worktrees and sidebar terminals are tables or key namespaces inside
    the collected `db.sqlite`; no new file
    ([section 2 of `analyzer/research/zed.md`](../../analyzer/research/zed.md#2-transcript-stores)).
  - Sync, relay and origin: none recorded on disk, as before.
  - Scratch directories: two, neither collected; see
    [section 2](#2-per-user-storage).
  - Deletion: a thread delete removes its rows and its macOS temp
    directory; no file records it.
  - Credentials, exclusions: nothing new.

## 2. Per-user storage

`APP_NAME` is `Zed`, lowercased for XDG paths ([`crates/paths/src/paths.rs:18-21`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L18-L21)).

- Config ([`paths.rs:122-139`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L122-L139)): Windows `dirs::config_dir()/Zed` = `%APPDATA%\Zed` ([`dirs/src/win.rs:8`](https://github.com/dirs-dev/dirs-rs/blob/00511bdc252f491a72ac89f6d6a2463406266fb2/src/win.rs#L8)); Linux/FreeBSD `$FLATPAK_XDG_CONFIG_HOME` or `$XDG_CONFIG_HOME`/`~/.config`, then `/zed` ([`dirs/src/lin.rs:9`](https://github.com/dirs-dev/dirs-rs/blob/00511bdc252f491a72ac89f6d6a2463406266fb2/src/lin.rs#L9)); macOS `~/.config/zed`.
- Data ([`paths.rs:144-165`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L144-L165)): macOS `~/Library/Application Support/Zed`; Linux `$FLATPAK_XDG_DATA_HOME` or `dirs::data_local_dir()` = `$XDG_DATA_HOME` or `~/.local/share`, then `/zed` ([`lin.rs:11-12`](https://github.com/dirs-dev/dirs-rs/blob/00511bdc252f491a72ac89f6d6a2463406266fb2/src/lin.rs#L11-L12)); Windows `dirs::data_local_dir()/Zed` = `%LOCALAPPDATA%\Zed` ([`win.rs:11`](https://github.com/dirs-dev/dirs-rs/blob/00511bdc252f491a72ac89f6d6a2463406266fb2/src/win.rs#L11)).
- State ([`paths.rs:169-190`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L169-L190)): macOS `~/.local/state/Zed` (capital Z), Linux `~/.local/state/zed`, Windows `%LOCALAPPDATA%\Zed`. No caller outside the paths crate uses it today.
- Temp/cache ([`paths.rs:193-218`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L193-L218)): macOS `~/Library/Caches/Zed`, Windows `%LOCALAPPDATA%\Zed`, Linux `~/.cache/zed`.
- Logs ([`paths.rs:228-255`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L228-L255)): macOS `~/Library/Logs/Zed`, elsewhere `<data>/logs`; files `Zed.log`, `Zed.log.old`. macOS crash reports in `~/Library/Logs/DiagnosticReports` ([`:264-268`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L264-L268)).
- `--user-data-dir <dir>` ([`crates/cli/src/main.rs:524`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/cli/src/main.rs#L524),[`969`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/cli/src/main.rs#L969)) makes `<dir>` the data dir and `<dir>/config` the config dir ([`paths.rs:103-125`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L103-L125)).
- Flatpak builds use `FLATPAK_XDG_*` ([`paths.rs:131`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L131),[`153`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L153),[`177`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L177),[`209`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L209)); app ids `dev.zed.Zed`, `dev.zed.ZedPreview`, `dev.zed.ZedNightly`, `dev.zed.ZedDev` ([`script/flatpak/bundle-flatpak:15-33`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/script/flatpak/bundle-flatpak#L15-L33)), so sandboxed state is `~/.var/app/dev.zed.Zed*/{config,data,cache}/zed`.

Config dir files: `settings.json`, `global_settings.json`, `settings_backup.json`, `keymap.json`, `keymap_backup.json`, `tasks.json`, `debug.json`, `AGENTS.md` ([`paths.rs:278-326`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L278-L326)), `themes/`, `snippets/` ([`:372-380`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L372-L380)), `development_credentials` ([`crates/zed_credentials_provider/src/zed_credentials_provider.rs:116`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/zed_credentials_provider/src/zed_credentials_provider.rs#L116)), `git/config`. On macOS only, `prompts/` (holding the LMDB `prompts-library-db.0.mdb`, [`crates/prompt_store/src/prompt_store.rs:28`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/prompt_store/src/prompt_store.rs#L28)), `prompt_overrides/` and `embeddings/` sit under config; elsewhere under data ([`paths.rs:386-433`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L386-L433)).

Data dir: `threads/threads.db` agent threads ([`crates/agent/src/db.rs:444-446`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L444-L446)); `db/0-<channel>/db.sqlite` where channel is `dev`, `nightly`, `preview`, `stable` or `global` ([`crates/db/src/db.rs:138`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/db/src/db.rs#L138),[`148-166`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/db/src/db.rs#L148-L166); [`crates/release_channel/src/lib.rs:218-221`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/release_channel/src/lib.rs#L218-L221)); `extensions/`, `remote_extensions/` (with `uploads/`), `languages/`, `debug_adapters/`, `external_agents/`, `copilot/`, `prettier/`, `remote_servers/`, `devcontainer/`, `hang_traces/`, `server_state/` ([`paths.rs:222-242`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L222-L242),[`348-483`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L348-L483)); `node/` runtime ([`crates/node_runtime/src/node_runtime.rs:637`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/node_runtime/src/node_runtime.rs#L637),[`1031`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/node_runtime/src/node_runtime.rs#L1031)); `build_timings/` ([`crates/zed/src/reliability.rs:465`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/zed/src/reliability.rs#L465)); `zed-<channel>.sock` ([`crates/zed/src/zed/open_listener.rs:413`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/zed/src/zed/open_listener.rs#L413)); `logs/` on Linux and Windows. No `conversations/` directory exists in current source.

At [`9cd14da`](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6)
(2026-10-19) `db.sqlite` also holds the tables `trusted_worktrees`,
`sidebar_terminal_threads`, `archived_git_worktrees` and the key-value
table `scoped_kv_store`, whose namespaces include `agent_draft_prompts`
and `created_git_worktrees`; every sqlez domain (Zed's name for one
group of tables with its migrations) opens the same file
([`crates/db/src/kvp.rs:20-41`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/db/src/kvp.rs#L20-L41);
[`crates/workspace/src/persistence.rs:986-991`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/workspace/src/persistence.rs#L986-L991)).
What each holds is in
[section 2 of `analyzer/research/zed.md`](../../analyzer/research/zed.md#2-transcript-stores).
Global agent skills are read from `~/.agents/skills/<skill>/SKILL.md`, a
directory shared with other agents and not created by Zed
([`crates/agent/src/agent.rs:616-638`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/agent.rs#L616-L638)).

Scratch directories. Zed has two, and the catalog collects neither:

- On macOS only, a thread whose terminal runs in the OS sandbox gets
  `tempfile`'s `$TMPDIR/zed-agent-terminal-<random>` (under
  `/var/folders`, outside the home), kept for the thread's life as its
  `TMPDIR` and removed when the thread is deleted; the thread blob in
  `threads.db` records it as `sandboxed_terminal_temp_dir`
  ([`crates/agent/src/thread.rs:1540-1566`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/thread.rs#L1540-L1566);
  [`crates/agent/src/db.rs:680-700`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent/src/db.rs#L680-L700)).
  Linux and Windows use the sandbox's private `/tmp` instead.
- A thread started in a new worktree runs in a linked git worktree (a
  second checkout made with `git worktree add`) that Zed creates under
  the `git.worktree_directory` setting, by default `../worktrees`
  relative to the repository, giving
  `<project parent>/worktrees/<worktree name>/<project>`; the setting
  must stay inside the project or its parent
  ([`crates/project/src/git_store.rs:6332-6349`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/project/src/git_store.rs#L6332-L6349),
  [`10845-10898`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/project/src/git_store.rs#L10845-L10898)).
  It is user project content beside the project, so no catalog line can
  name it; it is recorded in [section 6](#6-where-the-project-path-is-recorded).

## 3. Credentials

Production builds store credentials only in the OS keychain ([`zed_credentials_provider.rs:56-64`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/zed_credentials_provider/src/zed_credentials_provider.rs#L56-L64),[`69`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/zed_credentials_provider/src/zed_credentials_provider.rs#L69)). On the Dev channel, unless `ZED_DEVELOPMENT_USE_KEYCHAIN` is set, they go to `<config>/development_credentials` as JSON ([`:50-62`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/zed_credentials_provider/src/zed_credentials_provider.rs#L50-L62),[`116-120`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/zed_credentials_provider/src/zed_credentials_provider.rs#L116-L120)). `settings.json` (and its `settings_backup.json` copy and `global_settings.json`) can embed `api_key` and `custom_headers` for LM Studio style providers ([`crates/settings_content/src/language_model.rs:310-312`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/settings_content/src/language_model.rs#L310-L312)) and `agent_servers` environment. `db.sqlite` and `threads.db` hold no tokens.

At [`9cd14da`](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6)
(2026-10-19) no new credential file: the new `settings.json` keys
`agent.tool_permissions` and `agent.sandbox_permissions` hold rules and
paths, not secrets, and `scoped_kv_store` holds no token in the
namespaces read for this review.

## 4. Exclusions

Under either data root: `extensions`, `remote_extensions`, `node`, `languages`, `copilot`, `debug_adapters`, `external_agents`, `prettier`, `remote_servers`, `devcontainer`, `embeddings`, `server_state`, `hang_traces`, plus `build_timings`. `~/.cache/zed` and `~/Library/Caches/Zed` are temp. `prompts/*.mdb` is the user prompt library, small, keep.

## 5. Project-local files

`.zed/settings.json`, `.zed/tasks.json`, `.zed/debug.json` ([`paths.rs:487-531`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/paths/src/paths.rs#L487-L531)); rules files read by the agent: `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` ([`crates/prompt_store/src/prompts.rs:22-32`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/prompt_store/src/prompts.rs#L22-L32)). No per-project database.

## 6. Where the project path is recorded

- `threads.db` table `threads` columns `folder_paths`, `folder_paths_order` ([`crates/agent/src/db.rs:469-470`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L469-L470),[`545`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent/src/db.rs#L545)).
- `db.sqlite` table `sidebar_threads` columns `folder_paths`, `folder_paths_order` ([`crates/agent_ui/src/thread_metadata_store.rs:1375-1383`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/agent_ui/src/thread_metadata_store.rs#L1375-L1383)) and table `workspaces` columns `local_paths_array`, `local_paths_order_array` ([`crates/workspace/src/persistence.rs:731-733`](https://github.com/zed-industries/zed/blob/a84689073d296dfd39987bc7dd478e43ef76d83a/crates/workspace/src/persistence.rs#L731-L733)).
All SQLite, so left to the analyzer.

At [`9cd14da`](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6)
(2026-10-19), also in `db.sqlite`:

- `sidebar_threads.main_worktree_paths` and `main_worktree_paths_order`:
  the main repository of a thread whose `folder_paths` is a linked
  worktree ([`crates/agent_ui/src/thread_metadata_store.rs:1387-1388`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_metadata_store.rs#L1387-L1388)).
- `archived_git_worktrees` columns `worktree_path` and `main_repo_path`
  ([`thread_metadata_store.rs:1390-1398`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/thread_metadata_store.rs#L1390-L1398)).
- `scoped_kv_store` namespace `created_git_worktrees`, key `local`,
  a newline, then the worktree path: the worktrees Zed made, which are
  scratch rather than projects
  ([`crates/git_ui_core/src/created_worktrees.rs:34-50`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/git_ui_core/src/created_worktrees.rs#L34-L50)).
- `trusted_worktrees.absolute_path`: every project the user trusted
  ([`crates/workspace/src/persistence.rs:986-991`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/workspace/src/persistence.rs#L986-L991)).
- `sidebar_terminal_threads.working_directory` and `folder_paths`
  ([`crates/agent_ui/src/terminal_thread_metadata_store.rs:483-500`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_ui/src/terminal_thread_metadata_store.rs#L483-L500)).

## 7. Confidence

High: all paths from `paths.rs` and the `dirs` crate; credential provider behaviour. Medium: Flatpak `~/.var/app/<id>/{config,data}` layout (Flatpak convention; Zed only reads the `FLATPAK_XDG_*` variables the runtime sets). Not determined: the serialisation format of `folder_paths` (a `PathList`), and whether any legacy `conversations/` data survives on old installs.
