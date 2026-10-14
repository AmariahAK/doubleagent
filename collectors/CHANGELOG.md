# Changelog

All notable changes to the collectors are recorded here. The sh and
PowerShell collectors share one version, printed by `--version` and
`-Version` and recorded in `collection.json`. Changes to the manifest
(`manifest.jsonl` fields and status values) and to `collection.json` are
called out, since analysts and the analyzer depend on them.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.12.0] - 2026-10-13

### Added

- The Antigravity desktop app's Electron user-data directory is collected
  whole as `antigravity`: `Library/Application Support/Antigravity`,
  `.config/Antigravity` and `AppData/Roaming/Antigravity`, which replace
  the pre-2.0 `User` and `logs` lines for the same directories. The 2.x
  app (2.23.0, macOS, checked on a real install) has neither
  subdirectory; on Linux and Windows its logs are in the `logs/` child,
  which the whole-directory line still covers ([#83]).
- `Library/Logs/Antigravity`, the desktop app's macOS logs directory
  (`main.log`, `language_server.log`), is collected as `antigravity`
  ([#83]).
- Antigravity plugin OAuth credentials,
  `.gemini/antigravity*/plugin_data/<plugin>/token.json` (the Google Docs
  plugin writes one), are flagged `secret: true` ([#84]).
- The Antigravity CLI's file secret store `plugin-secrets.json`, which
  CLI 1.3.4 uses for plugin credentials when no OS keychain is available,
  is collected as `antigravity` and flagged `secret: true`:
  `.config/antigravity/plugin-secrets.json` (named in the CLI's own log
  on Linux), `Library/Application Support/antigravity/plugin-secrets.json`
  and `AppData/Roaming/antigravity/plugin-secrets.json`. The secret globs
  accept `Antigravity` as well, since on a case-insensitive filesystem
  the file shares the desktop app's Electron user-data directory
  ([#90]).

### Changed

- The Antigravity `bin/` exclusion covers every `.gemini` data directory
  (`antigravity`, `antigravity-cli`, `antigravity-ide`,
  `antigravity-backup`), not only the CLI's, so the desktop app's
  binaries in `.gemini/antigravity/bin` get one `skipped_excluded` row
  ([#83]).
- Plugin binaries under `.gemini/antigravity*/plugin_data/<plugin>/bin`
  and the plugin marketplace cache `.gemini/antigravity*/cache/marketplaces`
  are excluded; the rest of `cache/` is still collected ([#83]).
- The Chromium caches in the Antigravity Electron user-data directory are
  excluded: `Cache` (named under each of the three locations, since the
  PowerShell match ignores case and `*/Antigravity/Cache` would also prune
  `.gemini/antigravity/cache`), `Code Cache`, `GPUCache`,
  `DawnGraphiteCache`, `DawnWebGPUCache`, `blob_storage`,
  `Shared Dictionary`, `CachedData` and `Crashpad` ([#83]).
- The Antigravity Electron user-data directory's `Dictionaries`
  (Chromium's spell-check dictionary, 452 KB on Linux), the sidecar SDK
  the desktop app installs under `.gemini/antigravity*/lib/node_modules`,
  and its copy under `.gemini/config/node_modules` are excluded ([#83]).
- Manifest change: files collected from a project directory now carry the
  agent that owns them in the manifest `agent` field (`claude-code` for a
  project's `.claude/` and `CLAUDE.md`, `cursor` for `.cursor/`, `aider`
  for `.aider.chat.history.md`, `little-coder` for `.pi/approved-plan.md`
  inside pi's `.pi/`), taken from the `PROJECT_CATALOG` table that
  `--list` prints. Files several agents read (`AGENTS.md`,
  `AGENTS.override.md`, `AGENT.md`, `.agents/`, `.mcp.json`,
  `.github/copilot-instructions.md`, `.github/git-commit-instructions.md`,
  `.github/instructions/`, `SOUL.md`, `USER.md`) keep the agent
  `project`, which until now every project row had ([#104]).
- Both collectors are reorganised for readability: the same twelve
  sections in the same order, a reader's guide at the top, a comment on
  every function, the long functions split by step, and matching names
  for the sh and PowerShell functions that do the same step (listed in
  [docs/internals.md](docs/internals.md)). Options, `--list` output,
  the manifest, `collection.json`, the log, stdout, the archive and the
  exit codes are unchanged ([#99]).

### Fixed

- Project discovery in the sh collector now matches `file://` URIs.
  From 1.3.0 the pattern required a slash after `file:///`, so no URI
  ever matched: the Antigravity desktop app's project folders in
  `.gemini/config/projects/*.json` (`folderUri`) were never discovered,
  nor was a `file://` URI in the other files read the same way (the
  Antigravity CLI's `settings.json` and `cache/projects.json`, Kiro's
  `session.json`, Goose's `recent-dirs.json` and Twinny's embedding
  manifests); plain absolute paths in them were unaffected. A Windows
  URI (`file:///C:/x`, also `file:///c%3A/x`) now yields the
  drive-relative `/x`, which image mode prefixes with the root, as the
  PowerShell collector already did ([#91]).
- The sh collector's home patterns (`home/*`, `Users/*`, `usr/home/*`,
  `export/home/*`) are expanded under the root only. Since 1.0.0 the shell
  expanded them against the current directory first, so in image mode,
  run from a directory with a `home` or `Users` subdirectory (`/` on
  macOS), the homes found only by those patterns were lost: a Windows
  image yielded no users, and a Linux image only those in its
  `etc/passwd` ([#105]).
- The sh collector clears its list of claimed paths (`NESTED_CLAIMS`, the
  subtrees that nested catalog entries collect) at startup. The Docker
  and Podman volume walks read it without setting it, so a value in the
  environment the collector was started with pruned the paths it named
  from every matched volume, with no manifest row ([#106]).
- The sh collector tests a catalog match that is a file, not only a
  directory, against the exclusions: an excluded file match now gets one
  `skipped_excluded` row with its size instead of being collected, and
  `--inventory` no longer counts it, as in the PowerShell collector. A
  file named `.local/bin/.muse-update.<suffix>`, matched by the Muse Code
  catalog line `.local/bin/.muse-*` and by the exclusion
  `.local/bin/.muse-update.*`, was collected whole. `--full` still
  collects it ([#107]).
- The PowerShell collector reports an `-OutputDir` that is a file, or lies
  under one, as `Cannot create output dir: <dir>` and exits 2, as the sh
  collector does. `New-Item` neither fails nor creates the directory
  there, so a path under a file went on to print a `Resolve-Path` error,
  a `ProviderPath` error from strict mode and then
  `Output dir not writable: <dir>`, and a path that is a file printed the
  last message alone ([#108]).

## [1.11.0] - 2026-10-12

### Added

- Claude Desktop installed as an MSIX package on Windows (Anthropic's
  Windows download, not a Microsoft Store app) is collected as
  `claude-desktop`: its data directory under
  `AppData/Local/Packages/Claude_*/LocalCache/Roaming/Claude` (and the
  `AnthropicPBC.Claude_*` family), where MSIX virtualisation stores what
  the app reports as `AppData/Roaming/Claude` ([#73]).
- `AppData/Local/Claude` (the MSIX build's logs) and
  `AppData/Local/Claude-Data` (an alternative Windows data directory) are
  collected as `claude-desktop` ([#73]).
- The MSIX build's `config.json` (OAuth token cache), `Cookies*`,
  `host-creds-*.json` and `ccd-session-secrets/*` are flagged
  `secret: true` under both package families ([#73]).
- Claude Desktop's space-link signing key,
  `spaces-present/<acct>/<org>/link-key` under the data directory, is
  flagged `secret: true` (`*/Claude*/spaces-present/*/link-key`) ([#73]).
- Claude Code's per-process session key,
  `.claude/sessions/<pid>.<hash>.key` (and the same under a relocated
  `.claude-*` home), is flagged `secret: true`; the `<pid>.json` beside it
  stays unflagged ([#76]).
- The official Linux `.deb` of Claude Desktop (2.31226.1) was checked
  against the catalog on a real install: the data directory and its logs
  are under `.config/Claude`, already collected as `claude-desktop`, and
  the CLI the app downloads under `claude-code/<version>/<hash>/` is
  excluded by `*/Claude*/claude-code` ([#73]).
- Claude Code's CLI cache directory, which holds per-project MCP server
  logs (`<project slug>/mcp-logs-<server>/<timestamp>.jsonl`), is
  collected as `claude-code` from `Library/Caches/claude-cli-nodejs`
  (macOS), `.cache/claude-cli-nodejs` (Linux) and
  `AppData/Local/claude-cli-nodejs/Cache/*` (Windows). The Windows entry
  names the children of `Cache/` because the PowerShell collector's
  case-insensitive exclusion `*/Claude*/Cache` would otherwise prune the
  directory itself ([#81]).
- The macOS standard build of Claude Desktop (2.31226.1) was checked
  against the catalog on a real install: the data directory, the logs,
  `Partitions/`, `claude-code-vm` (the Linux CLI build the Cowork VM runs)
  and `vm_bundles` behave as documented and nothing new needed collecting;
  the Touch ID WebAuthn metadata secret in `Preferences`, collected
  unflagged, is documented as a key to redact ([#73]).

### Fixed

- The PowerShell collector collects paths longer than 260 characters under
  Windows PowerShell 5.1 without `LongPathsEnabled` on the host: every
  file system call uses the extended-length form (`\\?\`), so a deep source
  file is enumerated and its staged copy is written, where before the copy
  failed as `error_copy` and a source tree past 260 characters was not
  listed. Manifest paths and the archive layout are unchanged ([#77]).
- In the PowerShell collector, a directory that a wildcard catalog segment
  cannot list gets an `error_read` row instead of being skipped silently
  ([#77]).
- `tests/smoke.sh` passes on a macOS host: it strips the trailing slash
  from `$TMPDIR` and resolves the work directory before building the fake
  image, and hashes the backslash-named file from an extracted copy of the
  archive, because bsdtar reads a backslash in a member name as an escape
  ([#78]).
- On macOS and the BSDs, a catalog match directory that cannot be listed or
  entered (an agent's state directory with no read permission) left no row
  in the manifest, only a `find` line in the log; it now gets one
  `error_read` row with the OS error, as on Linux ([#82]).

## [1.10.3] - 2026-10-07

### Added

- The PowerShell collector has its own tar writer, used when `tar.exe` is
  missing or fails: it writes the same `.tar.gz` layout with pax headers
  for non-ASCII and long names, and keeps the staged symlinks.
  `collection.json` `capabilities.archiver` has a new value,
  `PowerShell tar writer`, for an archive it wrote ([#72]).
- `CAC_ARCHIVER`, a test hook for the PowerShell collector, sets the
  archivers to try (`tar`, `writer`, `zip`) ([#72]).

### Fixed

- On Windows, a collection with a file name outside the ANSI code page
  (CJK, Cyrillic) no longer falls back to a zip without saying why:
  some `tar.exe` builds crash on such names, and the collector now logs its exit
  code (`tar.exe failed: exit code 0xC0000005`), adds a `notes` entry to
  `collection.json` for each fallback, and writes the `.tar.gz` with its
  own tar writer ([#72]).
- The PowerShell collector's zip, now the last resort, stores entry names
  with `/` instead of `\` under Windows PowerShell 5.1, so it extracts
  into the `fs/<original path>` layout on Linux and macOS ([#72]).

## [1.10.2] - 2026-10-07

### Changed

- The PowerShell collector's per-file work is faster: the exclusion and
  credential tables are each tested with one regular expression instead of
  a loop over every glob, the staged copy is hashed through the handle that
  wrote it with one SHA-256 object for the run (reopening a file just
  written waited for the antivirus scan on Windows), the owner lookup reads
  only the owner and translates each SID once, staging directories are
  remembered, and the source is no longer read a second time for its
  timestamps. A 5,000-file collection takes about a third of the time under
  Windows PowerShell 5.1 and about half under PowerShell 7 ([#71]).
- The PowerShell collector writes manifest rows itself instead of through
  `ConvertTo-Json`. The rows parse to the same values with the same keys,
  order and types, byte for byte as PowerShell 7 wrote them; under Windows
  PowerShell 5.1, `<`, `>`, `&` and `'` are now written as themselves rather
  than as `\u` escapes ([#71]).
- `collection.json` from the PowerShell collector reports
  `capabilities.hash_tool` as `System.Security.Cryptography.SHA256` instead
  of `Get-FileHash` ([#71]).

## [1.10.1] - 2026-10-07

### Changed

- The sh collector's per-file work forks far fewer processes: manifest rows
  are built without subshells, and files are lstat'ed, copied and hashed in
  chunks of up to 256 with one `stat`, one hasher call and one `cp -p` per
  directory, falling back to per-file calls for a chunk or file the batch
  cannot handle. The manifest is unchanged, rows in the same order; a
  5,000-file collection takes about a tenth of the time it did, and the
  `shasum` path (macOS) about a twentieth ([#71]).
- The sh collector's `find -exec` workers run under `dash` when it is on
  `PATH` and `COLLECTOR_SH` is unset, instead of `sh`; on macOS, whose `sh`
  is bash, this roughly halves the remaining time ([#71]).
- `--inventory` stats each batch of files with one `stat` call ([#71]).

## [1.10.0] - 2026-10-06

### Added

- Catalog agent `autogen-studio`: `~/.autogenstudio`, with `.env` and
  `temp_env_vars.env` flagged as credentials ([#64]).
- Catalog agent `crewai`: `~/.config/crewai`, `~/.crewai`, the `crewai`
  data directory, and CrewAI's run databases (`latest_kickoff_task_outputs.db*`,
  `flow_states.db*`) and `.crewai_user.json` inside the data directory named
  after the project folder (`.local/share/*/...`,
  `Library/Application Support/*/...`), plus `AppData/Local/[Cc]rew[Aa][Ii]`;
  `settings.json` and the `credentials/` token files flagged ([#64]).
- Catalog agent `camel-ai`: `.camel/gmail_token.json` (flagged),
  `.camel/skills` and `.config/camel`, leaving the rest of `~/.camel`,
  which Apache Camel JBang shares, uncollected ([#64]).
- Catalog agent `dify`: the `difyctl` config directories, with `tokens.yml`
  flagged, and the Docker volumes `*dify_agent_local_sandbox_home` and
  `*dify_agent_local_sandbox_workspace` ([#64]).
- Catalog agent `flowise`: `~/.flowise`, with `encryption.key` and
  `*_secret.key` flagged and `vectorstore` excluded ([#64]).
- Catalog agent `langflow`: the config directory (`.cache/langflow`,
  `Library/Caches/langflow`, `AppData/Local/langflow/langflow/Cache`),
  `~/.langflow` and the Langflow Desktop directories; `secret_key`,
  `cache_secret_key` and the Desktop `data/.env` flagged; knowledge bases,
  Desktop virtual environments and caches, and `profile_pictures`
  excluded; the Docker volume `*langflow-data` ([#64]).
- Catalog agent `metagpt`: `~/.metagpt`, with `config2.yaml` and
  `config2.bak` flagged ([#64]).
- Catalog agent `n8n`: `~/.n8n`, `~/.n8n-local-gateway` and
  `~/.n8n-gateway`; `.n8n/config` and `.n8n/ssh/*` flagged; node modules,
  node definitions and SDK templates excluded; the Docker volumes
  `*n8n_data` and `*n8n-data` ([#64]).
- Catalog agent `pydantic-clai`: `~/.pydantic-ai` and
  `~/.config/pydantic-clai2` (CLAI 2.0), with `credentials-*` and the
  Logfire credentials flagged, and the project entry `.clai` ([#64]).
- `open-interpreter`: the legacy Python tool's platformdirs
  `open-interpreter` directories, the older `Open Interpreter*` directories
  and `.cache/open-interpreter`, with `profiles/*` and `config.yaml`
  flagged and the downloaded `models/` excluded ([#64]).
- Volume-relative exclusions `profile_pictures`, `nodes/node_modules`,
  `node-definitions` and `n8n-sdk-templates`, and secret globs
  `secret_key`, `cache_secret_key`, `config` and `ssh/*`, at the end of
  `EXCLUDES` and `SECRET_GLOBS` ([#64]).

## [1.9.0] - 2026-10-06

### Changed

- The Ollama exclusion `.ollama/models` is narrowed to `.ollama/models/blobs`,
  so the model manifests under `.ollama/models/manifests` (an inventory of
  pulled models, with pull times) and the per-blob `models/metadata` files
  are collected; the weights stay `skipped_excluded`. The volume-relative
  `models` exclusion is unchanged, so a Docker Ollama volume's manifests are
  still not collected ([#44]).

### Removed

- The credential pattern `.claude-*/.device-keys.json`, which could never
  match: no catalog line collects that file from a `.claude-<name>` config
  home, and Claude Code keeps it in `~/.claude` whatever `CLAUDE_CONFIG_DIR`
  says. `.claude/.device-keys.json` is still collected and flagged ([#41]).

## [1.8.1] - 2026-10-05

### Fixed

- sh collector: a `tar` that fails inside the `tar | gzip` fallback is now
  detected, logged as `tar | gzip: tar exited N`, and the collector falls
  through to the plain `.tar`, instead of hashing and reporting a truncated
  `.tar.gz` as success ([#40]).

## [1.8.0] - 2026-10-05

Interface changes: the manifest has a new status value, `error_read`;
`collection.json` has new fields `options.no_projects`, `options.projects`
and `counts.error_read`, and the sh collector now writes
`capabilities.archiver`; the PowerShell collector now sets `archive_path`
(and, when the link is not in the archive, `error`) on `symlink` rows; the
stdout `errors:` line now reads `errors:     N (X error_copy, Y error_read)`.

### Added

- `collection.json` `options.no_projects` (boolean) and `options.projects`
  (the `-p`/`--project` or `-Project` values, resolved to absolute paths
  and de-duplicated), and, in the sh collector, `capabilities.archiver`
  (`tar -z`, `tar | gzip` or `tar`) ([#31]).
- Manifest status `error_read`: one `dir` row, with the reason in `error`,
  for a home, project directory or directory inside a walk that cannot be
  listed or entered, and for a `-p`/`-Project` value that is not a
  directory. `collection.json` `counts.error_read` counts them ([#32], [#39]).

### Fixed

- On a case-insensitive filesystem (macOS, Windows), catalog entries that
  differ only by case (`.config/goose` and `.config/Goose`,
  `.config/PearAI/User` and `.config/pearai/User`, `.config/Cursor/User`
  inside `.config/cursor`) no longer collect the same files twice: the first
  catalog line keeps the directory and the later one is logged and skipped,
  also with `--inventory`. On Linux both directories are still collected.
  The sh collector compares device and inode; the PowerShell collector
  compares on-disk names and records paths in their on-disk spelling ([#29]).
- `collection.json` `archive` and `capabilities.archiver` name the archive
  and archiver actually used. Both collectors rewrite the summary and its
  archived copy before each fallback, so they no longer say `.tar.gz` after
  the sh collector's plain `.tar` fallback or `.tar.gz` and `tar.exe` after
  the PowerShell collector's `.zip` fallback ([#31]).
- The PowerShell collector recreates symlinks and other reparse points in
  the archive, with the target string as stored, and sets their
  `archive_path`, as the sh collector does ([#30]). Windows PowerShell 5.1
  makes the link with `cmd.exe`'s `mklink` and skips a link path or target
  containing `%` or `"`, which `cmd.exe` cannot take verbatim; PowerShell
  7 uses .NET. Where Windows refuses to
  create a link (no Administrator or Developer Mode) or the archive is a
  `.zip`, which cannot hold links, the `symlink` row keeps an empty
  `archive_path`, its `error` field says why, and `collection.json`
  `notes` counts them; a late fall back from `tar.exe` to zip removes the
  staged links first and rewrites their manifest rows, so a zip never
  holds a link target's bytes. Manifest change: `error` is now set on such
  `symlink` rows, and `archive_path` on recreated ones.
- A home or a directory inside a home that the collector could not read
  was silent (sh) or only logged; it now has an `error_read` row and a
  `read failed:` log line ([#32]).
- The stdout `errors:` line counts `error_copy` and `error_read` rows
  together and shows each in parentheses, `errors:     3 (1 error_copy,
  2 error_read)`; it counted only `error_copy` before ([#32]).
- The PowerShell collector checks that the output directory is writable
  (a probe file created and removed) and exits 2 with
  `Output dir not writable: <dir>` before collecting, as the sh collector
  does ([#38]).
- A `-p`/`-Project` directory that does not exist was dropped silently; it
  is now logged and gets an `error_read` row. A relative `-p` was ignored
  by the sh collector; both collectors now resolve it against the current
  directory, in image mode too ([#39]).

## [1.7.0] - 2026-10-04

### Added

- Meta's Muse Code CLI as catalog agent `muse-code`, with an evidence
  document under `research/`: `~/.config/muse` and `~/.local/share/muse`
  (the same paths on Windows), `~/.muse`, the launcher's dot files in
  `~/.local/bin/.muse-*`, the Windows install directory
  `AppData/Local/Programs/muse` and the per-session shell sandbox
  `AppData/LocalLow/muse-shell-sandbox-*`. `auth.json` and `settings.json`
  under `.config/muse` are flagged secret. The bundled plugin and skill
  copies, marketplace clones, update staging directories, the Windows
  `muse-bin-*.exe` binary and `.muse/worktrees` are excluded. Projects are
  discovered from `trust.json` and session logs' `workspace_root`, and a
  project's `.muse` directory is collected.
- Claude Code config homes moved with `CLAUDE_CONFIG_DIR` to a
  `~/.claude-<name>` directory such as `~/.claude-work`: `projects/`,
  `file-history/`, `history.jsonl`, `.claude.json*` and the credential
  files inside it are collected as `claude-code`, the credential files and
  `.claude.json` are flagged secret, and its `.claude.json` and
  `history.jsonl` are project discovery sources. The entries name
  Claude-only files, so `~/.claude-code-router`, `~/.claude-mem` and
  `~/.claude-squad` are not collected.
- `collection.json` field `users_with_artifacts`: the users whose home
  produced at least one manifest row. `users` and `homes` still list
  every home scanned.

### Changed

- The stdout `users:` line counts only homes that produced at least one
  manifest row, and the `User` progress line is written only for a home
  with a catalog match.
- The stdout `size:` and `collected:` lines add the size in binary units
  after the byte count, such as `74779093 (71.3 MiB)`.
- The sh collector's final progress line on stderr is `done`; the archive
  path, size and sha256 stay in the log file's `done:` line and on stdout.
  The PowerShell collector now prints the same `done` line.
- PowerShell collector: the internal logging function is renamed from
  `Write-Log` to `Write-CollectorLog` so it no longer shadows a Windows
  built-in command name; output and behaviour are unchanged. Found by
  PSScriptAnalyzer 1.25.0 with `collectors/PSScriptAnalyzerSettings.psd1`.

### Fixed

- sh collector: failed to parse under posh and other pdksh-derived shells,
  which stop a `$(...)` at the `)` of a case pattern. The two such `case`
  statements use the `(pattern)` form, and the shared helper and worker
  programs are read from here-documents without `$(cat <<...)`; the
  programs are byte-identical. The smoke test now passes under posh.

### Removed

- Shell history collection: the `shell-history` catalog agent and its ten
  entries (`.bash_history`, `.zsh_history`, `.zsh_sessions`, `.sh_history`,
  `.history`, `.bash_sessions`, both fish `fish_history` paths and both
  PSReadLine `ConsoleHost_history.txt` paths). Shell history is the EDR's
  job, like process lists and logons. Manifests no longer hold
  `shell-history` rows, and `--list` and `-List` no longer print them.
- General-purpose `.env` files: the `shared|.env` entry for `~/.env` and
  the `project|.env` entry for a `.env` at a discovered project's root.
  They hold whatever secrets the user or project keeps, not only AI keys,
  and are left to the EDR. An agent's own `.env` inside its state
  directory (`~/.codex/.env`, `~/.gemini/.env`, `~/.hermes/.env`, the
  Agent Zero `usr/.env` and the others in `SECRET_GLOBS`) is still
  collected and flagged secret.

## [1.6.0] - 2026-10-04

### Added

- Inventory mode, `--inventory` / `-Inventory`, for fleet audits through
  an EDR console: the collection walk (catalog, exclusions, nested claims,
  Docker volumes, `-u`, `-r`, `--full`, `--no-docker`) with `lstat` only.
  It writes nothing, not even a log; `-o` is ignored with a stderr note.
  Exit code `0` once the walk has run.
- Inventory output on stdout, JSON Lines: one `host` line (`type`, `host`,
  `collector`, `mode`, `at`, `users_scanned`, `users_unreadable`,
  `docker_volumes`).
- Then one `agent` line per user and agent with at least one file after
  exclusions and nested claims (`type`, `host`, `user`,
  `agent`, `files`, `bytes`, `first`, `last`, `projects`, `evidence`);
  `projects` is the user's discovered project count, repeated on each of
  the user's lines, and Docker volumes appear as user `docker`.
- Inventory never opens a credential file: project discovery skips sources
  that match `SECRET_GLOBS`.

### Changed

- PowerShell: the `profile not accessible (skipped)` log line is written
  only for profiles selected by `-Users`.

### Removed

- The live system snapshot. Both collectors no longer write the `live/`
  directory (`system.txt`, `users.txt`, `logins.txt`, `processes.txt`,
  `agent-processes.txt`, `network.txt`, `services.txt`,
  `scheduled-tasks.txt`, and the sh collector's `live/environ/<pid>.txt`
  process environments). The collectors supplement an EDR, which already
  records processes, logins, network connections and services.
- Manifest: the `live` agent name and the `live/<file>` archive paths are
  gone; no row has an empty `path` any more.
- The `--no-live` / `-NoLive` option. Passing it is now a usage error.
- `collection.json`: the `options.no_live` field. The host name stays in
  `hostname`.

## [1.5.0] - 2026-10-04

### Added

- Docker and Podman named volumes are collected (issue 28). Both
  collectors enumerate `var/lib/docker/volumes`,
  `var/lib/containers/storage/volumes` and `ProgramData/Docker/volumes`
  under the root, and the rootless `.local/share/docker/volumes` and
  `.local/share/containers/storage/volumes` under each home, from the
  filesystem only. A volume whose name matches the new `DOCKER_VOLUMES`
  table is collected whole with `user` `docker` and its `_data` directory
  as `home`; exclusion and secret globs apply relative to `_data`.
- New catalog table `DOCKER_VOLUMES` (Agent Zero, Local Deep Research,
  Ollama from source; Tabby, OpenHands, Letta, Hermes, OpenClaw and nanobot
  by inferred name), printed last by `--list` and `-List` under the new
  heading `# docker volumes (agent|volume name glob)`. Consumers of the
  `--list` output that do not know the heading should stop reading there.
- Volume-relative forms of the Agent Zero, Tabby, Ollama, Local Deep
  Research, OpenHands, Hermes, OpenClaw, nanobot and Letta exclusions and
  secret globs, at the end of `EXCLUDES` and `SECRET_GLOBS`.
- `--no-docker` / `-NoDocker` skips the enumeration.
- Manifest: new status value `skipped_unmatched_volume`, one `dir` row
  with its size for each volume that matches no `DOCKER_VOLUMES` line.
- `collection.json`: `options.no_docker`, `counts.skipped_unmatched_volume`,
  a `docker` object (`volumes_found`, `volumes_collected`, `unreadable`,
  `docker_desktop`) and a `notes` list. An unreadable volume directory or a
  volume that cannot be walked is noted there and in a `docker:` line of
  the stdout summary; collection continues and the exit code is unchanged.
  Docker Desktop data (whose Linux volumes are inside a VM disk) is only
  noted.

## [1.4.0] - 2026-10-04

### Added

- Fifteen catalog agents from the October 2026 backlog, each with an
  evidence document under `research/`: `pearai`, `cody`, `twinny`, `tabby`,
  `open-interpreter`, `openhands`, `pi`, `little-coder`, `letta`, `hermes`,
  `openclaw`, `nanobot`, `agent-zero`, `shellgpt` and `local-deep-research`.
  Several of them are general-purpose or chat-channel agents rather than
  coding agents. Sourcegraph Cody and Twinny have nested entries inside
  every VS Code family editor's globalStorage, like Cline and Continue, and
  little-coder's prompt history is a nested entry inside pi's `~/.pi`.
- 82 home catalog entries, 33 project catalog entries, 151 exclusions and
  150 secret globs, among them Codex CLI's `.codex/.env`, which was not
  flagged before.
- Twenty-one more project discovery sources in both collectors: Hermes
  checkpoint project records; Letta's session index and local-backend
  transcripts; pi session headers (also little-coder's), misplaced
  sessions, trusted folders, crash log and experimental session metadata;
  Open Interpreter live and archived rollouts; OpenHands workspaces, Agent
  Canvas conversation metadata and CLI conversation state; PearAI
  sessions; OpenClaw `workspace` and `agentDir` from its JSON5 config,
  legacy `clawdbot.json` included; nanobot workspace markers and instance
  config; Tabby `file://` repositories; and the common directory of the
  files in each Twinny embeddings manifest.
- `[!...]` negated classes in exclusion and secret globs now work in the
  PowerShell collector as they do in the sh collector.

### Fixed

- The PowerShell collector dropped `file:///` URIs of POSIX paths found in
  agent state; they now map to the path.

## [1.3.0] - 2026-10-03

### Added

- 60 home catalog entries, among them the remote server data directories of
  VS Code, Cursor, Windsurf, Devin and Kiro (with their agent extensions
  attributed to the extension), Antigravity IDE and `.gemini/config`, the
  Copilot CLI XDG directories and caches, Windsurf transcripts, the Ollama
  desktop app and Zed under Flatpak.
- 33 project catalog entries, 55 exclusions and 80 secret globs, including
  the Cursor and Windsurf credential files, now flagged `secret: true`.
- Ten more project discovery sources in both collectors.
- `collectors/research/` holds one evidence document per catalog agent.

### Fixed

- Exclusions that hid evidence: Factory Droid's cache exclusion now covers
  only its sounds, Kiro's `powers` directory is collected again, the Kilo
  Code worktree exclusions match the real paths, and Codex database backups
  and Goose apps are collected.

## [1.2.0] - 2026-10-03

### Changed

- A catalog entry nested inside another entry's directory now claims its
  subtree: each file is collected once, under the most specific agent.
  Manifest rows for Antigravity CLI files under `~/.gemini/antigravity-cli`
  now have `agent` `antigravity` instead of `gemini-cli`.

### Added

- Nested entries for the Cline, Roo Code, Kilo Code and Continue extensions
  inside the globalStorage of every VS Code family editor (VS Code, VSCodium,
  Cursor, Windsurf, Antigravity IDE, Kiro), on all three platforms, so their
  files are attributed to the extension rather than the editor.

## [1.1.0] - 2026-10-03

### Added

- `Collect-AgentArtifacts.ps1`, the Windows PowerShell 5.1 collector, with
  the same catalog, manifest and archive layout as the sh collector. It reads
  profiles from the registry and `C:\Users`, copies files held open by
  running editors, takes a CIM live snapshot, and writes a `tar.gz` through
  `tar.exe` or a `.zip` on older hosts.
- Manifest rows written by the Windows collector carry two extra fields,
  `owner` and `attributes`, and record `uid`, `gid`, `ctime` as `0` and
  `mode` as `""`.
- Catalog agents `roo-code`, `kilo-code`, `copilot` (the GitHub Copilot
  editor plugin's `github-copilot` directory) and `shared` (`~/.agents`,
  `~/.env` and `AGENTS.md` shared between agents).
- Nine more project discovery sources, and Crush's per-project `.crush`
  session database.
- Exclusions for embedding indexes, shadow git checkpoints, worktrees,
  daemon binaries and Electron caches.
- Secret flags for the Gemini CLI and Goose credential files that replace
  the OS keychain when it is unavailable.

### Changed

- Catalog entries for Cursor, Windsurf, Continue, Amp, Goose, Zed, Kiro,
  Qwen Code, Cline, Augment, Factory Droid, Crush, OpenCode, ChatGPT Desktop,
  Claude Desktop, Gemini CLI, Codex CLI and Aider were rebuilt from each
  tool's source, shipped bundle or official documentation.
- Zed, Goose, OpenCode, Crush, Kilo Code and Amp are looked for under
  `~/.config` and `~/.local/share` on macOS and Windows images too.

### Fixed

- Continue's `index/globalContext.json` is collected; only the embedding
  index beside it is excluded.

## [1.0.0] - 2026-10-03

### Added

- `collect-agent-artifacts.sh`, a single POSIX sh collector with no
  dependencies beyond the base system, for live macOS, Linux and BSD hosts
  and for mounted disk images (`-r`).
- Collection of Claude Code, Claude Desktop, Gemini CLI, Antigravity, Codex
  CLI, Copilot CLI, Cursor, VS Code, Windsurf, Aider, Ollama and other agent
  state, plus shell histories, for every user, and project files from
  repositories referenced in agent state.
- `manifest.jsonl` with one row per path: `user`, `home`, `agent`, `path`,
  `archive_path`, `type`, `size`, `mtime`, `atime`, `ctime`, `btime`, `uid`,
  `gid`, `mode`, `sha256`, `secret`, `status`, `target`, `error`. Status
  values: `collected`, `symlink`, `skipped_excluded`, `skipped_size`,
  `skipped_secret`, `error_copy`.
- `collection.json` run summary, a `fs/<original path>` archive layout, a
  live system snapshot, and a SHA-256 of the archive.
- Options `-o`, `-r`, `-u`, `-p`, `--full`, `--no-secrets`, `--no-live`,
  `--no-projects`, `--max-file-size`, `-k`, `--list`, `-q`, `-V`, `-h`.
- Default size exclusions for model weights, caches and extension binaries,
  overridden by `--full`; credential files collected and flagged
  `secret: true` by default.

[Unreleased]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.12.0...HEAD
[1.12.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.11.0...collector-v1.12.0
[1.11.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.10.3...collector-v1.11.0
[1.10.3]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.10.2...collector-v1.10.3
[1.10.2]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.10.1...collector-v1.10.2
[1.10.1]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.10.0...collector-v1.10.1
[1.10.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.9.0...collector-v1.10.0
[1.9.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.8.1...collector-v1.9.0
[1.8.1]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.8.0...collector-v1.8.1
[1.8.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.7.0...collector-v1.8.0
[1.7.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.6.0...collector-v1.7.0
[1.6.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.5.0...collector-v1.6.0
[1.5.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.4.0...collector-v1.5.0
[1.4.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.3.0...collector-v1.4.0
[1.3.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.2.0...collector-v1.3.0
[1.2.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.1.0...collector-v1.2.0
[1.1.0]: https://github.com/seanthegeek/doubleagent/compare/collector-v1.0.0...collector-v1.1.0
[1.0.0]: https://github.com/seanthegeek/doubleagent/releases/tag/collector-v1.0.0

[#108]: https://github.com/seanthegeek/doubleagent/issues/108
[#107]: https://github.com/seanthegeek/doubleagent/issues/107
[#106]: https://github.com/seanthegeek/doubleagent/issues/106
[#105]: https://github.com/seanthegeek/doubleagent/issues/105
[#104]: https://github.com/seanthegeek/doubleagent/issues/104
[#99]: https://github.com/seanthegeek/doubleagent/issues/99
[#91]: https://github.com/seanthegeek/doubleagent/issues/91
[#90]: https://github.com/seanthegeek/doubleagent/issues/90
[#84]: https://github.com/seanthegeek/doubleagent/issues/84
[#83]: https://github.com/seanthegeek/doubleagent/issues/83
[#82]: https://github.com/seanthegeek/doubleagent/issues/82
[#81]: https://github.com/seanthegeek/doubleagent/issues/81
[#78]: https://github.com/seanthegeek/doubleagent/issues/78
[#77]: https://github.com/seanthegeek/doubleagent/issues/77
[#76]: https://github.com/seanthegeek/doubleagent/issues/76
[#73]: https://github.com/seanthegeek/doubleagent/issues/73
[#72]: https://github.com/seanthegeek/doubleagent/issues/72
[#71]: https://github.com/seanthegeek/doubleagent/issues/71
[#64]: https://github.com/seanthegeek/doubleagent/issues/64
[#44]: https://github.com/seanthegeek/doubleagent/issues/44
[#41]: https://github.com/seanthegeek/doubleagent/issues/41
[#40]: https://github.com/seanthegeek/doubleagent/issues/40
[#39]: https://github.com/seanthegeek/doubleagent/issues/39
[#38]: https://github.com/seanthegeek/doubleagent/issues/38
[#32]: https://github.com/seanthegeek/doubleagent/issues/32
[#31]: https://github.com/seanthegeek/doubleagent/issues/31
[#30]: https://github.com/seanthegeek/doubleagent/issues/30
[#29]: https://github.com/seanthegeek/doubleagent/issues/29
