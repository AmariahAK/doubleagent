# claude-code

Claude Code (catalog agent `claude-code`) is Anthropic's closed-source coding agent CLI; Claude
Desktop's Code tab launches the same CLI ([`claude-desktop.md`](claude-desktop.md)), and the VS Code
extension runs it too and writes into the same `~/.claude` tree, so the extension is a surface of
this agent and not a catalog agent of its own ([VS Code extension files](#vs-code-extension-files)).
It writes one append-only JSONL transcript per session, a tree of records linked by
`uuid`/`parentUuid`, with each subagent in its own JSONL file under the session directory, plus a
global prompt history. On 2.1.309 a session can be handed to the session daemon, a background
`claude` supervisor process that keeps sessions running after the console that started them exits,
and run by one of its workers, the `claude` processes the daemon starts to hold those sessions
([Session daemon files](#session-daemon-files)). MCP (Model Context Protocol) servers are the tool
servers the CLI starts or connects to; a connector is an MCP server attached to the claude.ai
account rather than configured on the host. A slug is a path or name with every character other
than a letter or digit replaced by `-`, the scheme of the `projects/` keys. No other agent in the
catalog shares this format; Claude Desktop's Code sessions point back at the same `projects/` files
([Where the project path is recorded](#where-the-project-path-is-recorded)). The agent is parsed by
the `claude-code` parser ([Parser plan](#parser-plan)).

## Source and evidence

Closed source. The public repository
[anthropics/claude-code](https://github.com/anthropics/claude-code), at
[1132b8a](https://github.com/anthropics/claude-code/commit/1132b8a98e93300bb3822197fb7eee12ce4fb906)
(2026-10-21), is published under Anthropic's Commercial Terms of Service and ships the README,
the changelog, example plugins, the TypeScript of four built-in mods (`sec-default`, `diff`,
`telemetry`, `agents-md`) and the plugin API's type declarations, not the CLI, so the claims
about the CLI below have no commit links. No binary below was ever
executed. Each claim names its evidence level, best first:

- **Bundle 2.1.288**, the evidence for the Collection part ([Per-user storage](#per-user-storage) to
  [Where the project path is recorded](#where-the-project-path-is-recorded)): `npm pack @anthropic-ai/claude-code` gives
  2.1.288, a 28 KB shim whose `package.json` lists `optionalDependencies` on eight platform packages
  (`scratchpad/npm/cc/package/package.json`, `scratchpad/` being the working directory of the
  research session that read the package). `npm pack @anthropic-ai/claude-code-linux-x64@2.1.288`
  gives a single 245 MB Bun-compiled binary `claude` (Bun is the JavaScript runtime that packs the
  CLI's code and itself into one executable); `strings -n 6` of it is
  `scratchpad/npm/cc.strings`, and every "cc:NNN" in the Collection part is a line in that file.
  Evidence level per claim there: **bundle** unless marked **docs** or **local**.
- **Bundle 2.1.289**, the evidence for the Parsing part ([Transcript stores](#transcript-stores) to
  [Parser plan](#parser-plan)): `npm pack @anthropic-ai/claude-code@2.1.289` (shim, sha256
  `d72b0a94b84e51fbe5686577f322488a89f844c275985e8054e16951c6dd3e64`) and
  `npm pack @anthropic-ai/claude-code-linux-x64@2.1.289` (sha256
  `50a6eb433422febcfa7b7ac1e78ba795cdf79f1fe58f017fb1d9aeb9491b337d`), whose single Bun-compiled
  binary `package/claude` (246,107,320 bytes, sha256
  `a186b99e4a9c88366cd49df2f7dad56c61fc306ef0140b19ee64b7c42a8d1348`) was read with `strings -n 6`.
  Every `cc:NNN` in the Parsing part is a 1-based line in that strings file (531,386 lines); the
  minified JavaScript keeps record type literals and object shapes. 2.1.289 was chosen because it is
  the newest `version` in the local transcripts. The two strings files are numbered differently, so
  a `cc:` line in the Collection part does not match one in the Parsing part.
- **Docs**: [Claude Code settings](https://code.claude.com/docs/en/settings),
  [Claude Code IAM](https://code.claude.com/docs/en/iam),
  [Claude Code managed settings](https://code.claude.com/docs/en/managed-settings);
  [Claude Desktop data storage](https://claude.com/docs/third-party/claude-desktop/data-storage);
  for the retention sweep and the session scratchpad,
  [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory.md#cleaned-up-automatically),
  [Settings reference, `cleanupPeriodDays`](https://code.claude.com/docs/en/settings-reference#cleanupperioddays)
  and
  [Monitoring usage, Retention sweep event](https://code.claude.com/docs/en/monitoring-usage#retention-sweep-event)
  (read 2026-10-26).
- **Local**: the author's host ([Observed](#observed)). A shape the Parsing part marks observed
  was seen on the WSL2 install; one marked bundle rests on the binary only.
- **Windows 2.1.309**: the clean-VM round of 2026-10-23 ([Observed](#observed)). A claim marked
  "on Windows 2.1.309" rests on that round's listings and the shape tool's key names, types and
  enum values; no value was read.
- **Linux 2.1.310**: the clean-VM round of 2026-10-25 and 2026-10-26 ([Observed](#observed)). A
  claim marked "on Linux 2.1.310" rests on that round's listings, file modes and the shape tool's
  key names, types and enum values, in the same way.
- **Vendor text in the bundle**: the built-in "Fewer Permission Prompts" prompt describes the
  transcript layout for the model itself (2.1.289 strings file, cc:489602: "Session transcripts
  live at `~/.claude/projects/<sanitized-cwd>/*.jsonl`. Each line is a JSON object. Tool calls
  appear as `assistant` messages with `message.content[]` entries of `type: "tool_use"`").
- **Binary 2.1.296** ([issue 93](https://github.com/seanthegeek/doubleagent/issues/93)): the
  author's installed CLI, `~/.local/share/claude/versions/2.1.296`, a Bun-compiled Mach-O arm64
  executable of 240,664,432 bytes, sha256
  `c9b5341637becbd423ddffc5b254afb645682a3868cb708bbc6cc0e7bb419937`, searched for byte strings.
  Citations are `claude 2.1.296 darwin-arm64 @<byte offset>` with the literal snippet, as for the
  2.1.295 Linux build below; the offsets are only valid for this build.
- **Binary 2.1.295**: the Linux arm64 build of CLI 2.1.295 that Claude Desktop downloads
  (`https://downloads.claude.ai/claude-code-releases/2.1.295/linux-arm64/claude.zst`, decompressed
  255,516,664 bytes, sha256 `cfb9dc1332fb6f92a683f835823e91b3179a803398ca7852cd2381a3cb1dea3b`);
  citations are written `claude 2.1.295 linux-arm64 @<byte offset>` with a literal snippet, because
  the `cc:` line numbers belong to 2.1.288 and 2.1.289. It is the evidence for the
  [CLI cache directory](#cli-cache-directory) and [Remote Control](#remote-control).

### Observed

- Windows 11 arm64 (build 10.0.26300), CLI 2.1.309 win32-arm64 from the native installer, a clean
  virtual machine (VM), 2026-10-23 ([issue 256](https://github.com/seanthegeek/doubleagent/issues/256)), one listing
  diff per step, file names, sizes, key names and enum values only: the install
  ([Native installer](#native-installer)); the first launch, browser sign-in and trust dialog
  ([Credentials](#credentials), [`.claude.json`](#claudejson),
  [Where the project path is recorded](#where-the-project-path-is-recorded)); an `/exit` with no
  prompt and a question the model answered with a shell call in `auto` mode
  ([Transcript stores](#transcript-stores), [Record schema](#record-schema)); a reboot with that
  session open, after which the next start's session was handed to the session daemon
  ([Session daemon files](#session-daemon-files),
  [Session daemon records](#session-daemon-records));
  the Shift+Tab mode cycle, a one-time approval, a denial with a typed reason and an allow-always
  grant ([Permission decisions](#permission-decisions),
  [Permission configuration](#permission-configuration)); a file edit
  ([File-history records](#file-history-records)); accept-edits and plan mode, with the plan file
  ([Files that hold evidence](#files-that-hold-evidence)); a `/model` switch saved as the default
  ([Joins and timestamps](#joins-and-timestamps)); a subagent, a large output persisted to a file,
  a pasted text, a prompt typed while a turn ran, `/compact`, `/rename` and `/exit`
  ([Record schema](#record-schema), [`history.jsonl`](#historyjsonl)); `claude --resume`, a refused
  `claude --continue` and `claude agents` ([Joins and timestamps](#joins-and-timestamps)); a
  local-scope MCP server ([CLI cache directory](#cli-cache-directory),
  [MCP state](#mcp-state)); `/install-github-app` and a read-only pull-request question
  ([Source-host integration](#source-host-integration)); Remote Control from the Claude iPhone app
  ([Remote Control](#remote-control)); a cloud session, which the CLI did not offer this account;
  `/loop` and `/schedule` ([Scheduled tasks](#scheduled-tasks)); the VS Code extension
  ([VS Code extension files](#vs-code-extension-files),
  [VS Code extension sessions](#vs-code-extension-sessions)); then `/clear`, a `cleanupPeriodDays`
  setting, the project directory removed and a reboot
  ([What survives a delete](#what-survives-a-delete), [Scratch directories](#scratch-directories)).
- Ubuntu 26.04.1 LTS arm64, CLI 2.1.310 linux-arm64 from the native installer, a clean VM,
  2026-10-25 and 2026-10-26 ([issue 256](https://github.com/seanthegeek/doubleagent/issues/256)),
  one listing diff per step, file names, sizes, modes, key names and enum values only: the install
  ([Native installer](#native-installer)); the first launch, browser sign-in and trust dialog
  ([Credentials](#credentials), [`.claude.json`](#claudejson),
  [CLI cache directory](#cli-cache-directory), [Scratch directories](#scratch-directories),
  [Where the project path is recorded](#where-the-project-path-is-recorded)); an `/exit` with no
  prompt, then a question answered with no tool call and one answered with a `Read` in `auto` mode
  ([Transcript stores](#transcript-stores), [Record schema](#record-schema)); the Shift+Tab mode
  cycle, two one-time approvals, a denial with a typed reason and an allow-always grant
  ([Permission decisions](#permission-decisions),
  [Permission configuration](#permission-configuration)); a file edit and a prompt on a detached
  head ([File-history records](#file-history-records),
  [Joins and timestamps](#joins-and-timestamps)); accept-edits and plan mode, once with a question and once with a task that wrote a plan file
  ([Files that hold evidence](#files-that-hold-evidence)); a `/model` switch
  ([Joins and timestamps](#joins-and-timestamps)); a subagent, a large output persisted to a file,
  a short and a long paste, a prompt typed while a turn ran, `/compact`, `/rename` and `/exit`
  ([Record schema](#record-schema), [`history.jsonl`](#historyjsonl)); `claude --resume`,
  `claude --continue` and `claude agents` ([Joins and timestamps](#joins-and-timestamps),
  [Session daemon files](#session-daemon-files)); a local-scope MCP server
  ([MCP state](#mcp-state)); `gh auth login`, `/install-github-app` and a read-only pull-request
  question ([Source-host integration](#source-host-integration)); Remote Control from the Claude
  phone app ([Remote Control](#remote-control)); a cloud session, which the CLI did not offer this
  account; `/loop` and `/schedule` ([Scheduled tasks](#scheduled-tasks)); the VS Code extension
  ([VS Code extension files](#vs-code-extension-files),
  [VS Code extension sessions](#vs-code-extension-sessions)); `/clear`, a `cleanupPeriodDays`
  setting with a backdated transcript, short and idle sessions and a `--debug` session left open
  overnight, the project directory removed and a reboot
  ([What survives a delete](#what-survives-a-delete), [Scratch directories](#scratch-directories),
  [Files that hold evidence](#files-that-hold-evidence)).
- macOS, CLI 2.1.296, the author's install, 2026-10-13
  ([issue 93](https://github.com/seanthegeek/doubleagent/issues/93)), key names, enum values and
  counts only: 308 `permission-mode` records across four session files, every one `permissionMode`
  `auto` ([Record schema](#record-schema)); `permissionMode` on every `user` prompt line;
  `message.model` and `requestedModel` on every `assistant` line, equal on every line seen; a
  `/model` switch written as a `user` line `<command-name>/model</command-name>` followed by a
  `user` line holding the command output ([Joins and timestamps](#joins-and-timestamps)); summary
  lines with `modelUsage.<model id>.{inputTokens, outputTokens, ...}`. The permission configuration
  keys of [Permission configuration](#permission-configuration) were seen in `~/.claude.json` and
  the settings files of the same install, by name only.
- macOS, CLI 2.1.295 launched by the Claude Desktop Code tab, 2026-10-11: the CLI cache directory
  `~/Library/Caches/claude-cli-nodejs/` ([CLI cache directory](#cli-cache-directory)) with its
  `claude-cli-nodejs` MCP logs ([Transcript stores](#transcript-stores)), and
  `sessions/<pid>.<sha256>.key` ([Credentials](#credentials)) beside the `sessions/<pid>.json`
  registry ([Remote Control](#remote-control)); in the transcripts
  `requestedModel`, the `stop_hook_summary` keys and `renderedBesideToolResult`
  ([Record schema](#record-schema)).
- Linux, the Ubuntu lab install of 2026-10-11, CLI 2.1.295 launched from the Claude Desktop Code
  tab: `sessions/<pid>.<sha256>.key` beside `sessions/<pid>.json` ([Credentials](#credentials)), and
  the registry's key names and value types only ([Remote Control](#remote-control)).
- Linux (WSL2), the author's host, October 2026, versions 2.1.286 to 2.1.289 (the native install was
  2.1.288 when the layout was checked): the layout was confirmed names-only against `~/.claude`, and
  claims marked **local** rest on it. 95 transcript files (15 session files, 80 subagent files),
  31,116 lines, 0 unparseable, plus 80 subagent `.meta.json` files, 37 persisted tool outputs,
  `history.jsonl` (162 lines) and `sessions/*.json` (3), read by key path and value type only
  ([Record schema](#record-schema) to [Other stores](#other-stores)).

### Source reviews

- 2026-10-26: three of Anthropic's Claude Code documentation pages,
  [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory.md#cleaned-up-automatically),
  [Settings reference, `cleanupPeriodDays`](https://code.claude.com/docs/en/settings-reference#cleanupperioddays)
  and
  [Monitoring usage, Retention sweep event](https://code.claude.com/docs/en/monitoring-usage#retention-sweep-event):
  [What survives a delete](#what-survives-a-delete) now states what the retention sweep removes and
  keeps and names `claude purge`, and [Scratch directories](#scratch-directories) the conditions
  under which a session gets a scratchpad.
- 2026-10-21: [anthropics/claude-code](https://github.com/anthropics/claude-code) at
  [1132b8a](https://github.com/anthropics/claude-code/commit/1132b8a98e93300bb3822197fb7eee12ce4fb906):
  the public repository was checked for the CLI's source and does not ship it; the opening of
  [Source and evidence](#source-and-evidence) says what it holds, and
  [Project-local files](#project-local-files) gains the `AGENTS.md` instruction files the
  `agents-md` mod reads.
- 2026-10-19: the agents that read, drive, copy or index Claude Code state, at Crush
  [7f799fb](https://github.com/charmbracelet/crush/commit/7f799fbc1fdaf0a931a4ff73e6539bafee59d3da),
  Agent Zero
  [ff2a5b9](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a),
  Hermes Agent
  [86fa9e6](https://github.com/NousResearch/hermes-agent/commit/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872),
  Cline [41e75ef](https://github.com/cline/cline/commit/41e75efc53e7abbcb76564b89e6de57f78659b33),
  Pydantic AI
  [0ba01f9](https://github.com/pydantic/pydantic-ai/commit/0ba01f92be3fc361f89970502cd6e7dd3611aec3)
  and Zed
  [9cd14da](https://github.com/zed-industries/zed/commit/9cd14daad768fbfaeeac8789f515f9a5f67669a6).
  Added [Used by other agents](#used-by-other-agents) and the copies and the Zed index under
  [What survives a delete](#what-survives-a-delete).

## Collection

### Per-user storage

Config home = `process.env.CLAUDE_CONFIG_DIR ?? join(homedir(), ".claude")`, NFC-normalised
(cc:472945 `o()??u(R(),".claude")`, cc:497291). Same on Linux, macOS and Windows
(`%USERPROFILE%\.claude`, docs settings page; observed on Windows 2.1.309). No Library or AppData
paths for user state, apart from the cache directory below and, on Windows, the temp root
([Scratch directories](#scratch-directories)); the native installer's `~/.local` and `~/.cache`
directories are used on Windows as well ([Native installer](#native-installer)), and Claude Code
appends to the user's global git excludes file `~/.config/git/ignore`, creating it when absent
([Files that hold evidence](#files-that-hold-evidence)). `CLAUDE_CONFIG_DIR` relocates everything
including
`.credentials.json` and the keychain entry name (docs /iam "Credential management"); separate
account dirs such as `~/.claude-work` are documented practice (docs /iam "multiple accounts").

Known top-level directories inside the config home, from the literal set at cc:482244:
`agent-memory`, `agent-memory-local`, `agent-memory-project`, `api-dumps`, `backups`, `cache`,
`chrome`, `cowork_plugins`, `daemon`, `debug`, `downloads`, `dump-prompts`, `feedback`,
`feedback-bundles`, `file-history`, `file-transfers`, `ide`, `image-cache`, `jobs`, `local`,
`local-settings`, `logs`, `mcp-discovery-cache`, `mcp-skill-archives`, `paste-cache`, `plans`,
`plugins`, `project-settings`, `projects`, `remote`, `scratch`, `seed-admin`, `session-env`,
`sessions`, `shares`, `shell-snapshots`, `startup-perf`, `state`, `statsig`, `storage-v2`,
`systemd`, `tasks`, `teams`, `telemetry`, `todos`, `traces`, `uploads`, `usage-data`. User-config
subdirs also include `commands`, `agents`, `output-styles`, `skills`, `workflows`, `routines`,
`themes`, `rules` (cc:473782). Known top-level files (cc:483303): `.claude.json`,
`.claude.json.backup`, `.credentials.json`, `history.jsonl`, `.session_ingress_token`,
`policy-limits.json`, `remote-settings.json`, `hfi-auth.json`, `stats-cache.json`,
`mcp-needs-auth-cache.json`, `gh-pr-status-cache.json`, `antproto.json`, `active-time.json`,
`loop.md`, `server-sessions.json`, `computer-use.lock`, `server.lock`; plus `settings.json`,
`settings.local.json` (cc:436317-8), `.device-keys.json` and `.config.json` (cc:477075). On Windows
2.1.309 the round saw `backups`, `cache`, `daemon`, `downloads`, `file-history`, `ide`, `jobs`,
`paste-cache`, `plans`, `plugins`, `projects`, `session-env`, `sessions`, `shell-snapshots`,
`skills` and `state` written, and the files `.credentials.json`, `history.jsonl`, `settings.json`,
`.last-cleanup`, `daemon.lock`, `daemon.log` and `daemon.status.json`; `debug`, `statsig`, `todos`
and `.device-keys.json` were never written. On Linux 2.1.310 the round saw the same directories,
plus `debug` (written only by a `claude --debug` session), and the same files except `daemon.lock`
and `daemon.status.json`; `statsig`, `todos`, `startup-perf` and `.device-keys.json` were never
written. `sessions/`, `daemon/` and `ide/` are mode 0700 there, and the files holding keys or
tokens 0600 ([Credentials](#credentials)).

#### Scratch directories

On Windows the temp root is under the home: `%LOCALAPPDATA%\Temp\claude\`
(`AppData/Local/Temp/claude`), created empty at the first launch, not the `claude-<uid>` form of
Linux. Observed on Windows 2.1.309, each session id gets `<slug>\<session id>\scratchpad\` and
`<slug>\<session id>\tasks\`, `<slug>` being the project key of
[Transcript stores](#transcript-stores) (`C--Users-sean-lab-proj` for the lab project,
`C--Users-sean` for the home). A directory appears for every session id the CLI starts, including
ids that never get a transcript: a start refused by a settings error, a probe session the VS Code
extension opens beside its own, and the replacement workers the session daemon starts at each
`/exit` ([Session daemon files](#session-daemon-files)). `tasks\` is filled at the session's first
tool run: `tasks\<agent id>.output` (0 B) for a subagent, `tasks\<9 base-36 chars>.output` holding
the output of a command Claude Code moved to the background (22 B), and short-lived task files
created and removed during a long command. The temp root survives a reboot (Windows does not clear
`%TEMP%` at boot). The housekeeping sweep that writes `.last-cleanup` removed the session
directories of earlier sessions, an open session's included, while the `<slug>` directories stayed;
the tree of a session whose process died in a reboot was gone after the next start. The catalog
collects it since this round (`claude-code|AppData/Local/Temp/claude`). The session's scratchpad is
also named by the `environment` attachment's `snapshot.scratchpadDirectory` key
([`attachment` records](#attachment-records)).

The vendor's
[Explore the .claude directory](https://code.claude.com/docs/en/claude-directory.md#cleaned-up-automatically)
names the session scratchpad, a per-session working directory Claude Code gives the model for
temporary files: `/tmp/claude-<uid>/<project>/<session-id>/scratchpad/` on Linux (under `$TMPDIR`
when it is set), `/private/tmp/claude-<uid>/...` on macOS and `%TEMP%\claude\...` on Windows,
movable with `CLAUDE_CODE_TMPDIR`; a session gets one only when it is signed in with a claude.ai
account, on the Anthropic API, with `enableArtifact` not set to false. The page says the
scratchpad lasts as long as the session's transcript, the retention sweep deleting the directory
with the transcript, and that `claude purge` does not touch the temp directory
([What survives a delete](#what-survives-a-delete)).

Observed on Linux 2.1.310 (2026-10-25 and 2026-10-26), the temp root is `/tmp/claude-<uid>`
(`/tmp/claude-1000/`), outside the home, and holds one directory per *process*, not per session:
`<slug>/<uuid>/scratchpad/`, every level mode 0700, created empty at the process start. A new
session's directory is named by its session id; a `claude --resume`, a `claude --continue`, the
`claude agents` console and its supervisor, and even `claude mcp add`, which runs no session, each
got a directory of their own under a uuid that is not the resumed session's, so by the end of the
round the temp root held sixteen such directories under two slugs, the project's and `-home-sean`
from one start in the home. `<slug>/<uuid>/tasks/` (mode 0775) appears at the session's first shell
call:
`tasks/<agent id>.output` is a symlink to the subagent's transcript,
`projects/<slug>/<session id>/subagents/agent-<agent id>.jsonl` (on Windows a 0 B file), and
`tasks/<9 base-36 chars>.output` (22 B, mode 0664) holds the output of a command Claude Code moved
to the background. Beside the slugs, `bash-edit-diff/<19 digits>-<19 digits>-<16 hex>/` (mode 0700)
is a snapshot of the project's working tree taken at a shell call, so that Claude Code can diff
what the command changed (the `bash_edit_diff` feature, behind the `tengu_agile_glade` flag): a
non-bare git repository with `HEAD`, `refs/heads/main`, a `config` of four keys
(`core.repositoryformatversion`, `core.bare`, `core.logallrefupdates`, `core.untrackedcache`), an
empty `config.global` (a `GIT_CONFIG_GLOBAL` override), an `index` (659 B, two entries),
`info/attributes`, `info/exclude`, loose objects and `objects/info/alternates`, git's list of other
object directories a repository borrows from, which names the project's `.git/objects`. Its one
commit, holding `.gitignore`, `README.md` and `calc.py`, is its own and not the project's `HEAD`;
nothing under the project's `.git` changed. A second, empty `<ids>/` directory sat beside it. Both
were removed at the session's exit, the empty `bash-edit-diff/` parent staying, so the snapshots are
on disk only for a live session or one whose process died. Six seconds after the first launch the
Bun runtime of the binary also wrote `/tmp/.bun-<uid>-<16 hex>.node` (976,328 B, mode 0600), a
native module it extracts to `/tmp`, which no console process had mapped when it was checked.

The tree outlives `/exit`. The retention sweep deleted the scratchpad directory of the transcript it
deleted ([What survives a delete](#what-survives-a-delete)), so the temp root is bounded by
`cleanupPeriodDays` like the transcripts. `/tmp` on Ubuntu 26.04 is tmpfs, a file system held in
memory and emptied at every boot, so the reboot removed the whole temp root, both project slugs,
the `tasks/` files and symlink, `bash-edit-diff/` and the Bun module, while on Windows the temp root
survived a reboot. A collection taken on Linux after a reboot finds none of it. The Claude Desktop
Code tab's use of the same root is in [Where the project path is recorded in
`claude-desktop.md`](claude-desktop.md#where-the-project-path-is-recorded); on Linux and macOS the
temp root is not collected
([issue 163](https://github.com/seanthegeek/doubleagent/issues/163)).

#### Files that hold evidence

- `projects/<key>/<sessionId>.jsonl`: transcripts, with `<key>` derived from the cwd (cc:473017,
  cc:473728); `projects/<key>/<sessionId>/subagents/agent-<id>.jsonl`: subagent transcripts
  (cc:476679); `projects/<key>/memory/*.md`: per-project memory (cc:489631). The naming and the
  sidecars are in [Transcript stores](#transcript-stores). Local shows `-home-sean-dev-...` dirs
  holding `<uuid>.jsonl`, `<uuid>/`, `memory/`; Windows 2.1.309 shows `C--Users-sean-lab-proj`
  holding `<uuid>.jsonl`, `<uuid>/` with `subagents/`, `tool-results/` and `custom-title.json`,
  and an empty `memory/` created at the first prompt; Linux 2.1.310 shows the same under
  `-home-sean-lab-proj` ([Transcript stores](#transcript-stores)).
- `history.jsonl`: prompt history, with retention pruning (cc:338013-15, 478233); the vendor page
  says the retention sweep keeps it ([What survives a delete](#what-survives-a-delete)).
- `paste-cache/<16 hex>.txt`: the text of a long paste, named by the hash `history.jsonl` records
  ([`history.jsonl`](#historyjsonl)); created at the first such paste (6,604 B on Windows 2.1.309;
  15,108 B, mode 0600, on Linux 2.1.310).
- `debug/<sessionId>.txt`: per-session debug logs (cc:472977); `debug/latest` symlink (local). On
  Linux 2.1.310 only a session started with `claude --debug` wrote them: the log (31 KB after the
  start, 48.3 KB when the session exited 10 h 52 min later) and `debug/latest`, a symlink to it,
  both kept after the exit. Each line carries a component tag: `[STARTUP]`, `[FileIndex]`, `[init]`,
  `[uds-messaging]`, `[servedCatalog]`, `[keybindings]`, `[MCP]`, `[Bootstrap]`, `[skills]`,
  `[sessionRegistry]`, `[plugins-scope]`, `[engine]`, `[claudeai-mcp]`, `[plugins]`,
  `[mcp-registry]`, `[jobStateNameSync]`, `[event-loop-stall]`, `[cc-plugin-telemetry]`,
  `[auto-mode]`, `[ScheduledTasks]` and `[Perfetto]`. The vendor page lists `debug/` among the paths
  the retention sweep removes ([What survives a delete](#what-survives-a-delete)).
- `file-history/<sessionId>/`: pre-edit file backups (cc:482923), one `<16 hex>@v<n>` file per
  tracked path and version on Windows 2.1.309 ([File-history records](#file-history-records));
  `session-env/<sessionId>/` (cc:480109), an empty directory created at the session's first tool
  run on Windows 2.1.309 and at its first shell call on Linux 2.1.310, kept after the exit;
  `shell-snapshots/snapshot-<shell>-<epoch>-<rand>.sh` (shell function
  dumps, cc:480528 region, local name confirms), on Windows a 2.3 KB `snapshot-bash-*` of Git Bash
  (the bash that Git for Windows installs), on Linux 2.1.310 a 7.5 KB
  `snapshot-bash-<epoch ms>-<6 chars>.sh`, written at a session's first Bash call and removed when
  the console exits; `todos/`, `tasks/<sessionId>/`, `plans/*.md` (cc:476220; on Windows 2.1.309
  `plans/<adjective-adjective-noun>.md`, a 1.3 KB Markdown plan under a random three-word name,
  written with the `Write` tool in plan mode; on Linux 2.1.310 the same form, 1,010 B, written when
  the plan-mode prompt was a task and not when it was a question, so `plans/` is not written for
  every plan-mode session), `teams/`,
  `jobs/<id>/parent-transcript.jsonl` (cc "jobs" ctx), `dump-prompts/*.jsonl` (full outgoing
  prompts, cc "dump-prompts" ctx), `api-dumps`, `traces/*.json`,
  `usage-data/{facets,session-meta}/*.json` and `report-*.html` (cc:492127),
  `feedback-bundles/*.zip`, `shares/*.zip`, `uploads/<sessionId>/`, `ide/<port>.lock` (local
  `13502.lock`; Windows/WSL also probes `%USERPROFILE%\.claude\ide`, cc "ide" ctx; on Windows
  2.1.309 `ide/` was created when the VS Code extension activated and the lock removed when VS Code
  closed, and on Linux 2.1.310 the same, `ide/` being mode 0700), `backups/` (`.claude.json`
  snapshots; docs: `~/.claude/backups/.claude.json.corrupted.<ts>`).
- `backups/.claude.json.backup.<epoch ms>` on Windows 2.1.309: a dated full copy of `.claude.json`
  written at every start and exit, the first (84 B, `firstStartTime` and `firstStartVersion`) by
  the installer; the housekeeping sweep prunes the oldest, and four to five were kept through the
  round. Each copy carries the sign-in details of `.claude.json` ([Credentials](#credentials)). On
  Linux 2.1.310 copies were also written mid-session and at the first launch, the changelog fetch
  and the sign-in (84, 517, 558 and 2,290 B), and the set was capped at the five newest with no
  sweep involved: each new copy removed the oldest, as the vendor's
  [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory.md#cleaned-up-automatically)
  says ("keeps the five newest, plus a copy of any version it couldn't parse").
- `.last-cleanup`: a 24-byte printable marker, not JSON, rewritten when the housekeeping sweep runs;
  on Windows 2.1.309 that was at a start, at a turn and on a timer while idle, and the sweep pruned
  `backups/` and the temp root ([Scratch directories](#scratch-directories)). On Linux 2.1.310 it
  was first written 30 minutes into the second session, by the retention sweep, whose timing is
  under [What survives a delete](#what-survives-a-delete); that sweep also removed the session
  daemon's empty `daemon/auth/` directory.
- `skills/synced/<org uuid>_<account uuid>/`: copies of the claude.ai account's skills, written at
  the first prompt after sign-in (286 entries, 3.9 MB on Windows 2.1.309: `manifest.json`,
  `.last-complete-round`, a transient `.staging/`, one directory per skill) and refreshed on a
  timer, with an empty `skills/synced/.bucket-<org uuid>_<account uuid>` beside it. The directory
  name says which account and organisation the skills came from; collected. On Linux 2.1.310 it
  was written at the second start (307 entries with `plugins/synced/`, 7.2 MB; the skills 4.7 MB:
  `manifest.json` 11.5 KB, `.last-complete-round` 40 B, an empty `.staging/`, 14 skill directories
  such as `docx/`, `pdf/`, `deep-research/` and `computer-use/`), and `.last-complete-round` was
  rewritten at most starts and on a timer while a session ran (42 minutes after the first sync,
  then at intervals of hours overnight).
- `state/mcp-discover-verdicts.json`: one entry per MCP server the CLI probed
  ([MCP state](#mcp-state)).
- `~/.config/git/ignore`, outside the config home: the user's global git excludes file. Claude Code
  appends `**/.claude/settings.local.json` to it, creating it when absent: on Windows 2.1.309 it
  created the file (31 B, the length of that pattern and a newline) in the same second it wrote a
  project's `settings.local.json`, and on Linux 2.1.310 the same (31 B, creating `~/.config/git/`).
  The collector does not take it, because the file exists on hosts
  that never ran Claude Code and a catalog line would mark them as Claude Code homes; a responder
  checks it by hand.
- `.claude.json` sits in `$HOME`, or inside the config home when `CLAUDE_CONFIG_DIR` is set: its
  path is ``join(process.env.CLAUDE_CONFIG_DIR || homedir(), `.claude${suffix}.json`)`` (cc:473059
  `mar()`, cc:473896 `configPath`; variants `.claude${suffix}.json`, cc:477075); docs: "holds your
  sign-in session, MCP server configurations, per-project state such as trust decisions, and the
  global config keys" (settings page). Its `projects` object is keyed by project path
  ([Where the project path is recorded](#where-the-project-path-is-recorded)); the keys seen on
  Windows 2.1.309 are under [`.claude.json`](#claudejson).
- `settings.json`, `settings.local.json` and, per project, `.claude/settings.json` and
  `.claude/settings.local.json`: settings, including the standing permission grants, which with
  the `projects.<path>` grants in `.claude.json` are the evidence of what the person authorised
  ([issue 93](https://github.com/seanthegeek/doubleagent/issues/93)). They are collected with the
  config home and the project catalog's `.claude` entry; their keys are under
  [Permission configuration](#permission-configuration). The user `settings.json` on Windows
  2.1.309 held `autoUpdatesChannel` (written by the installer), `theme` (first launch), `model`
  (the alias picked when `/model` was saved as the default), `agentPushNotifEnabled` (written when
  Remote Control started) and `cleanupPeriodDays` (set by hand). On Linux 2.1.310 it held the same
  keys but `autoUpdatesChannel`: `theme` written at the first launch (22 B), not by the installer,
  then `model` (`opus`), `agentPushNotifEnabled` and `cleanupPeriodDays` (99 B).
- `plugins/`: `installed_plugins.json`, `known_marketplaces.json`, `marketplaces/<name>/` git
  clones, `cache/` zip cache (cc plugins ctx); local also `blocklist.json`,
  `plugin-directory-cache-v2.json`, `synced/`. On Windows 2.1.309 the first sign-in auto-installed
  the official marketplace: `known_marketplaces.json` (283 B,
  `claude-plugins-official{installLocation, lastUpdated, source{source, repo}}` with `source`
  `github`) and the clone `marketplaces/claude-plugins-official/` (818 entries, 13.7 MB, with
  `.git`); `plugin-directory-cache-v2.json` (2.6 MB, a download of the plugin directory,
  refreshed on a timer); and `synced/<org uuid>_<account uuid>/` with `.marketplaces.json`
  (`etag, parserVersion, rows[{id, name, display_name, scope, source{source}, updated_at}]`,
  `scope` `default`, `source` `claudeai`: the account's marketplaces) and `.last-complete-round`,
  plus a `.bucket-` file like the skills one. On Linux 2.1.310 the first launch wrote
  `known_marketplaces.json` (274 B) and the clone (819 entries, 16.2 MB), and the second start the
  `synced/` files (`.marketplaces.json` 392 B, `.last-complete-round` 37 B, rewritten at every
  start) and, during its second turn, `plugin-directory-cache-v2.json` (2.7 MB); the directory
  cache and `known_marketplaces.json` were refreshed again on timers, once two minutes after a
  prompt with `Plugin autoupdate: checking installed plugins` in the `--debug` log.
- `cache/changelog.md` (1.0 MB, written by the installer) and
  `cache/model-catalog/<org uuid>-<12 hex>-cc.json` (14 KB, `catalog, fetchedAt, staleAt, version`,
  refreshed at starts and at a `/model` change), on Windows 2.1.309. On Linux 2.1.310 the installer
  fetched nothing: the first launch wrote `changelog.md` (with `changelogLastFetched` in
  `.claude.json`), and the second start the model catalog (14.4 KB), whose
  `catalog{config{id, models, provider_alias_targets, settings_vocabulary}, state{id, model,
  selection_source, thinking, thinking_by_model}, surface}` records where the default model came
  from ([Joins and timestamps](#joins-and-timestamps)).
- Writes with no user action, on Linux 2.1.310 in a `--debug` session left open overnight: the
  OAuth access token was refreshed (OAuth being the authorisation protocol of the claude.ai
  sign-in), rewriting `.credentials.json` ([Credentials](#credentials)); `.claude.json` was
  rewritten with a backup about five hours after the last prompt; the skills sync ran seven hours
  after the previous one; and the debug log shows a native-installer update check every 30 minutes
  (`Checking for native installer update to version 2.1.310`, then
  `Found 2.1.310 at ~/.local/bin/claude, skipping install`), the skills poll moving to a 30-second
  idle interval, and an `[event-loop-stall]` warning (`likely sleep/wake`). A 24-minute idle with
  no prompt wrote nothing beyond the start's files.
- `statsig/` feature-flag cache, `cache/gateway-models.json`, `cache/model-capabilities.json`,
  `telemetry/`, `telemetry/runs/`, `chrome/chrome-native-host[.bat]`, `local/` (npm-local install),
  `remote/` (cloud sessions: `/home/claude/.claude/remote/.oauth_token`, `.api_key`,
  `.session_ingress_token`, cc `.session_ingress_token` ctx).
- The session daemon's files and `jobs/`: [Session daemon files](#session-daemon-files).

#### Native installer

Native installer binaries: `$XDG_DATA_HOME/claude/versions/<ver>` (default
`~/.local/share/claude/versions`) and symlink `~/.local/bin/claude` (cc "versions" ctx
`o(wje(e),"claude","versions")`, `o(n,".local","bin")`; local confirms three ~245 MB versions).
Windows: `winget Anthropic.ClaudeCode` (cc:296086), or the native installer
`irm https://claude.ai/install.ps1 | iex`. On Windows 11 arm64 the native installer of 2.1.309
(2026-10-23) wrote `~\.local\share\claude\versions\2.1.309` (282,697,888 bytes, a win32-arm64 PE
executable, PE being the Windows executable format) and `~\.local\bin\claude.exe`, a full second
copy of the same bytes, not a symlink, hard link or junction; `~\.local\state\claude\locks\` and
`~\.cache\claude\staging\`, both empty; and in the config home the first `backups/` copy,
`cache/changelog.md`, empty `downloads/` and `sessions/`, `settings.json` and `~\.claude.json`. It
added no `PATH` entry to the user environment (it printed the instruction instead) and wrote nothing
under `%LOCALAPPDATA%`, `%APPDATA%`, `%TEMP%`, `Program Files` or the registry policy keys. Neither
binary is collected: the versions directory is excluded ([Exclusions](#exclusions)) and the launcher
copy has no catalog line.

On Ubuntu 26.04.1 arm64 the native installer of 2.1.310 (2026-10-25) runs as
`curl -fsSL https://claude.ai/install.sh | bash`: the script is `#!/bin/bash` and uses `[[ ]]` and
`=~`, and piped to `sh`, which is dash on Ubuntu (a smaller POSIX shell), it stops with
`sh: 9: Syntax error: "(" unexpected (expecting "then")` (exit 2) before writing anything. In
15 seconds it printed `Installing Claude Code native build latest...`,
`Setting up launcher and shell integration...`, a note that `~/.local/bin` is not in `PATH` with the
line to append to `~/.bashrc`, `Version: 2.1.310` and `Location: ~/.local/bin/claude`, and wrote
`~/.local/share/claude/versions/2.1.310` (291,496,120 bytes, an ELF aarch64 executable, ELF being
the Linux executable format, dynamically linked) with `~/.local/bin/claude` a symlink to it (47 B),
not the copy of Windows; the empty `~/.local/state/claude/locks` and `~/.cache/claude/staging`
directories; and in the config home the first `backups/` copy, empty `downloads/` and `sessions/`,
and `~/.claude.json` (517 B, 12 keys). Unlike the Windows installer it fetched nothing: no
`cache/changelog.md`, `settings.json` or `changelogLastFetched` key until the first launch. It
changed no shell profile; Ubuntu's `.profile` already adds `~/.local/bin` at login when it exists.

`~/.local/state/claude/locks/<version>.lock` (138 B, mode 0644, JSON `acquiredAt, execPath, pid,
version`) is a per-version lock held by a running `claude` process: on Linux 2.1.310 it was written
at each start and removed at each exit, so it exists only while a session runs and names that
process's executable and pid. `~/.cache/claude/staging/` stayed empty whenever listed, on Windows
and Linux alike. Both directories are collected since this round (`claude-code|.local/state/claude`
and `claude-code|.cache/claude`).

#### Session daemon files

Observed on Windows 2.1.309, after a reboot killed an open session and the next start handed its
session to the daemon (the records are under [Session daemon records](#session-daemon-records)):

- `daemon.lock` (431 B JSON), `daemon.status.json` (121 B) and `daemon.log` (0 B until the daemon
  ended, then 1,370 B of text) in the config home: the supervisor's lock, status and log.
- `daemon/roster.json` (3.3 KB with three workers, 88 B with none): the workers and how to reach
  them, with two auth tokens per worker ([Credentials](#credentials)); `daemon/control.key`
  (32 B) and `daemon/pipe.key` (16 B), raw keys for the daemon's local IPC (inter-process
  communication); `daemon/dispatch/` (empty), `daemon/pty-pids/<short>.pid` (4 B
  each, one per worker; a PTY is the pseudo-terminal a worker runs in) and
  `daemon/attach-journal/<uuid>.json` (316 B, one per attach of a console to a worker).
- `jobs/pins.json` (`[]`), `jobs/.draft-<8 hex>` (42 B, an unsent prompt draft written at exit),
  and per worker `jobs/<short>/` with `state.json` (905 B to 1.1 KB), `timeline.jsonl` (the job's
  state changes, 445 B to 4.8 KB) and an empty `tmp/`; `<short>` is the worker's eight-hex short id.
- `sessions/<pid>.json` and its `.key` for each worker beside the console's
  ([Remote Control](#remote-control)).

The daemon is not a login item: after a reboot no `claude.exe` ran and nothing restarted it, and its
files stayed as they were left. `/exit` in a console attached to a worker does not stop the worker,
and at each exit new worker session directories and MCP logs appeared, the daemon starting
replacement workers. On the round the daemon ended (2026-10-23 15:11:45Z) while an ordinary console
session of the same project was running, removing `daemon.lock`, `daemon.status.json`, the
`pty-pids` file and the worker's registry files and leaving `roster.json` with no workers; what
ended it is not known.

On Linux 2.1.310 no session was handed to the daemon: no `claude` process remained after any
`/exit`, a 90-minute session's included, none started at login after the reboot, and
`claude --continue` resumed the last session in place
([Joins and timestamps](#joins-and-timestamps)).
`claude agents` started the daemon even with no session to attach to, writing `daemon/` (mode
0700) with `control.key` (32 B of hex, mode 0600), `roster.json` (89 B, mode 0600, no workers) and
the empty `auth/` and `dispatch/`, and `jobs/pins.json` (`[]`); when the console was quit the
supervisor, having no worker, exited and wrote `daemon.log` (809 B, ten lines of text, mode 0664).
No `daemon.lock`, `daemon.status.json`, `daemon/pipe.key`, `daemon/pty-pids/`,
`daemon/attach-journal/`, `jobs/<short>/` or `jobs/.draft-*` was written, and the files stayed as
left through the reboot, except `daemon/auth/`, which a later sweep removed
([Files that hold evidence](#files-that-hold-evidence)).

#### VS Code extension files

The Claude Code extension for VS Code (2.1.309 on Windows, installed from the marketplace on
2026-10-23) lives in `~\.vscode\extensions\anthropic.claude-code-2.1.309-win32-arm64\` (281.6 MB,
58 entries: `extension.js`, `webview\index.js`, `claude-code-settings.schema.json`,
`.vsixmanifest`, `package.json` and a `resources\` tree holding the CLI binary), which is a copy of
a published package and not collected (the `vscode` catalog entry takes `extensions.json` only). It
keeps no VS Code storage of its own: no `globalStorage\anthropic.claude-code*` directory existed.
Its log is `AppData\Roaming\Code\logs\<start>\window1\exthost\Anthropic.claude-code\Claude
VSCode.log` (text; exthost is VS Code's extension host process), which the `vscode` catalog entry
collects under that agent. In the config home it creates `ide/` with a `<port>.lock` while VS Code
runs and removes the lock when VS Code closes; its sessions go to the CLI's `projects/` tree
([VS Code extension sessions](#vs-code-extension-sessions)). The VS Code agent-host and chat files
written at VS Code's own launch are VS Code's ([`vscode.md`](vscode.md)).

On Linux the extension (2.1.310 linux-arm64 in VS Code 1.143.1, installed from the marketplace on
2026-10-26) is `~/.vscode/extensions/anthropic.claude-code-2.1.310-linux-arm64/` (297 MB:
`resources/native-binary/claude`, 291,496,120 B, the size of the installed CLI binary,
`extension.js` 3.7 MB, `webview/index.js` 6.0 MB, `claude-code-settings.schema.json`,
`.vsixmanifest`, `package.json`, `README.md` and images), again with no
`globalStorage/anthropic.claude-code*` directory. Its log is
`~/.config/Code/logs/<start>/window1/exthost/Anthropic.claude-code/Claude VSCode.log` (53 KB, 579
lines). Its start wrote one connector MCP log per server and a skills sync, its session went to the
CLI's `projects/` tree, and `ide/` was empty again after VS Code closed. VS Code 1.143 itself wrote
`~/.copilot/logs/` at its first start, before the extension was installed
([Per-user storage in `copilot-cli.md`](copilot-cli.md#per-user-storage)).

#### CLI cache directory

The CLI cache directory ([issue 81](https://github.com/seanthegeek/doubleagent/issues/81)) comes
from the env-paths code bundled in the CLI with app name `claude-cli` and suffix `nodejs`:
`~/Library/Caches/claude-cli-nodejs/` on macOS (observed with CLI 2.1.295 launched by the Claude
Desktop Code tab, 2026-10-11), `$XDG_CACHE_HOME/claude-cli-nodejs/` else
`~/.cache/claude-cli-nodejs/` on Linux (observed on Linux 2.1.310), and
`%LOCALAPPDATA%\claude-cli-nodejs\Cache\` on Windows (observed on Windows 2.1.309). Under it,
`<project slug>/mcp-logs-<server>/<timestamp>.jsonl`: the slug is the cwd with every
non-alphanumeric character replaced by `-` (the `projects/` key scheme), the server is the MCP
server name slugged the same way, and the file name is an ISO timestamp with `:` and `.` replaced by
`-` (`2026-10-12T02-23-51-709Z.jsonl`).

Each line is `{cwd, debug, sessionId, timestamp}`, or `{cwd, error, sessionId, timestamp}` for an
error (seen on Windows 2.1.309). The bundle also names `<project slug>/errors/` (not observed).
`CLAUDE_CONFIG_DIR` does not move it. Observed on Windows 2.1.309: every process start (each
console, worker, resume and VS Code extension session) wrote one new file for each of the account's
two claude.ai connectors, `mcp-logs-claude-ai-Claude-Docs\` and `mcp-logs-claude-artifacts\` under
`C--Users-sean-lab-proj\` (9 to 12 lines each, two of them `error` lines in the second), from the
first sign-in on, so the connector logs are account state on every surface; a local-scope stdio
server added with `claude mcp add` logged to `mcp-logs-fs\`, one file of 0.9 to 2.0 KB per server
start. Observed on macOS: the Code tab's CLI wrote
`mcp-logs-ccd-host/` and `mcp-logs-terminal/` (the desktop's own two MCP servers) under the
project's slug at session start, one line of about 200 bytes each, and ordinary CLI sessions on
another project wrote `mcp-logs-<connector name>/` files of 7-9 lines (1.5-2.2 KB); the whole
directory was 16 KB. Observed on Linux 2.1.310: from the first sign-in on, every start (each
console, resume, `--continue`, the VS Code extension) wrote one file per claude.ai connector of the
account under `~/.cache/claude-cli-nodejs/-home-sean-lab-proj/` (`mcp-logs-claude-ai-Claude-Docs/`
9 lines, `mcp-logs-claude-ai-Monarch/` 8, `mcp-logs-claude-artifacts/` 12 with two `error` lines),
and the local-scope stdio server `fs` logged to `mcp-logs-fs/` (2,302 B, 10 lines, one of them an
`error`); no `errors/` directory appeared. Evidence, `claude 2.1.295 linux-arm64` (the binary
recorded in
[Source and evidence](#source-and-evidence)):

- `@206335642`, env-paths with the three platform branches: `F=(t)=>{let e=n.join(d,"Library");return{data:n.join(e,"Application Support",t),config:n.join(e,"Preferences",t),cache:n.join(e,"Caches",t),log:n.join(e,"Logs",t),temp:n.join(_,t)}}`, `P=(t)=>{let e=g.APPDATA||n.join(d,"AppData","Roaming"),r=g.LOCALAPPDATA||n.join(d,"AppData","Local");return{data:n.join(r,t,"Data"),config:n.join(e,t,"Config"),cache:n.join(r,t,"Cache"),log:n.join(r,t,"Log"),temp:n.join(_,t)}}` and, at `@206336051`, `G=(t)=>{...cache:n.join(g.XDG_CACHE_HOME||n.join(d,".cache"),t),log:n.join(g.XDG_STATE_HOME||n.join(d,".local","state"),t)...}`.
- `@206336334`: ``function f(t,{suffix:e="nodejs"}={}){...if(e)t+=`-${e}`;if(E.platform==="darwin")return F(t);if(E.platform==="win32")return P(t);return G(t)}import{join as h}from"path";var k=f("claude-cli"),O=200;function N(t){let e=t.replace(/[^a-zA-Z0-9]/g,"-");if(e.length<=O)return e;return`${e.slice(0,O)}-${Math.abs(yse(t)).toString(36)}`}``.
- `@206336793`: ``function y(){return h(k.cache,N(n2n()))}var yut={baseLogs:()=>y(),errors:()=>h(y(),"errors"),mcpLogs:(t)=>h(y(),`mcp-logs-${N(t)}`)}``.

#### Managed policy

System-wide managed policy (outside the home): `/Library/Application Support/ClaudeCode/`,
`/etc/claude-code/`, `C:\Program Files\ClaudeCode\` holding `managed-settings.json`,
`managed-settings.d/`, `managed-mcp.json` (cc:412717-9; docs /managed-settings). MDM plist domain
`com.anthropic.claudecode`; registry `HKLM|HKCU\SOFTWARE\Policies\ClaudeCode\Settings` (docs).

#### Relocated config homes (`CLAUDE_CONFIG_DIR`)

With `CLAUDE_CONFIG_DIR` set, every file above moves into that directory, `.claude.json` included
(cc:473059, cc:473896); the one exception is `.device-keys.json`, which stays at
`~/.claude/.device-keys.json` (cc:477075 `E9n()` joins `homedir()`, `".claude"`). Third-party tools
that read Claude Code state resolve `.claude.json` the same way
([claude-mem `observed-billing.ts`](https://github.com/thedotmack/claude-mem/blob/c91e30491ce078a6dfe73296cd96f9b3b9578a32/src/shared/observed-billing.ts#L46-L48)).
The catalog covers a relocated home only when it is a `.claude-<name>` directory in the home, such
as `~/.claude-work`, and only through the Claude-specific names inside it: `.claude-*/projects`,
`.claude-*/file-history`, `.claude-*/history.jsonl`, `.claude-*/.claude.json*`,
`.claude-*/.credentials.json`, `.claude-*/hfi-auth.json`, `.claude-*/.session_ingress_token`,
`.claude-*/remote/.oauth_token`, `.claude-*/remote/.api_key`, `.claude-*/sessions/*.*.key` (the
`<pid>.<sha256>.key` shape), `.claude-*/daemon/control.key`, `.claude-*/daemon/pipe.key`,
`.claude-*/daemon/roster.json` and `.claude-*/backups/.claude.json.*`. A bare `.claude-*` entry
would claim other tools' directories that share the prefix:

- claude-code-router: `~/.claude-code-router` on macOS and Linux, `%APPDATA%\claude-code-router` on
  Windows
  ([`app-paths.ts`](https://github.com/musistudio/claude-code-router/blob/f2e01bfe0c01e0c7ea7a37077747473f69869048/packages/core/src/runtime/app-paths.ts#L35-L42);
  [`packages/cli/README.md`](https://github.com/musistudio/claude-code-router/blob/f2e01bfe0c01e0c7ea7a37077747473f69869048/packages/cli/README.md#L115-L128)).
  Top level: `config.sqlite`, `app-data/`, `service.json`, `gateway.config.json`, `profiles/`,
  `bin/`, plus `config.json`, `app-cache`, `bot-gateway`, `grok-media` and a few state JSON files;
  no `projects/`, `history.jsonl`, `file-history/`, `.claude.json` or `.credentials.json` at its
  root. It does run Claude Code with `CLAUDE_CONFIG_DIR` set to
  `~/.claude-code-router/profiles/<slug>[/custom]/claude`
  ([`launch-core.ts`](https://github.com/musistudio/claude-code-router/blob/f2e01bfe0c01e0c7ea7a37077747473f69869048/packages/core/src/profiles/launch-core.ts#L257-L266),
  [env](https://github.com/musistudio/claude-code-router/blob/f2e01bfe0c01e0c7ea7a37077747473f69869048/packages/core/src/profiles/launch-core.ts#L320-L326));
  those homes are three levels down and are not matched by the `.claude-*/` lines.
- claude-mem: `~/.claude-mem`
  ([`paths.ts`](https://github.com/thedotmack/claude-mem/blob/c91e30491ce078a6dfe73296cd96f9b3b9578a32/src/shared/paths.ts#L26))
  holds `settings.json`
  ([`paths.ts`](https://github.com/thedotmack/claude-mem/blob/c91e30491ce078a6dfe73296cd96f9b3b9578a32/src/shared/paths.ts#L56)),
  which can carry provider API keys
  ([`OpenAICompatProvider.ts`](https://github.com/thedotmack/claude-mem/blob/c91e30491ce078a6dfe73296cd96f9b3b9578a32/src/services/worker/OpenAICompatProvider.ts#L450)),
  plus `claude-mem.db`, `logs/`, `chroma/` and `.env`. Its `settings.json` is why
  `.claude-*/settings.json` is not a catalog line; it has no `projects/` or `history.jsonl`.
- claude-squad: `~/.claude-squad`
  ([`config.go`](https://github.com/smtg-ai/claude-squad/blob/ce1ffb4392b01f38e2c4599c7c84d2a93973b138/config/config.go#L26))
  holds `config.json`, `state.json` and `instances.json`
  ([`config.go`](https://github.com/smtg-ai/claude-squad/blob/ce1ffb4392b01f38e2c4599c7c84d2a93973b138/config/config.go#L16),
  [`state.go`](https://github.com/smtg-ai/claude-squad/blob/ce1ffb4392b01f38e2c4599c7c84d2a93973b138/config/state.go#L12-L13)).

Not collected from a relocated home: `settings.json`, `settings.local.json`, the `<pid>.json`
registry files of `sessions/` (its `*.key` files are), `todos/`, `plans/`, `tasks/`,
`session-env/`, `shell-snapshots/`, `debug/` and the other subdirectories, and any config home
outside the home directory or not named `.claude-<name>`.

#### Used by other agents

Other agents read this agent's config home or drive the CLI (from source; none seen on a real
install):

- Crush reads `~/.claude/skills` as one of its global skills directories, beside
  `~/.agents/skills`, and a project's `.claude/skills` as a project one
  ([`internal/config/load.go:1312-1322`](https://github.com/charmbracelet/crush/blob/7f799fbc1fdaf0a931a4ff73e6539bafee59d3da/internal/config/load.go#L1312-L1322),
  [`1345-1350`](https://github.com/charmbracelet/crush/blob/7f799fbc1fdaf0a931a4ff73e6539bafee59d3da/internal/config/load.go#L1345-L1350)),
  so a skill in the config home or the project may have been loaded by Crush as well as by Claude
  Code ([`crush.md`](crush.md)).
- Agent Zero's Orchestrator plugin, which tells that agent how to drive other coding CLIs on the
  host or in its container, defaults Claude Code to `permission_mode: bypassPermissions` and, when
  not running as root, runs
  `claude -p "$TASK" --output-format json --permission-mode bypassPermissions --allowedTools Bash,Read,Edit`
  ([`plugins/_orchestrator/default_config.yaml:7-37`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_orchestrator/default_config.yaml#L7-L37),
  [`plugins/_orchestrator/README.md:96`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_orchestrator/README.md#L96)).
  Such a session is an ordinary transcript under `projects/`, started by another agent with
  approvals bypassed; the plugin's permission settings are in
  [Parser plan in `agent-zero.md`](agent-zero.md#parser-plan).
- Hermes Agent, Cline, Pydantic AI's CLAI (its command-line chat client) and Zed copy or index the
  transcripts ([What survives a delete](#what-survives-a-delete)).

### Credentials

- macOS: Keychain generic password, account = OS user, service = `"Claude Code"` + `"-credentials"`
  (keyed to the config dir when non-default), read with
  `security find-generic-password -a <user> -w -s <service>` (cc:473906, cc:494949,
  `HAn="-credentials"` chunk near cc:473906). Fallback and Linux/Windows:
  `<config>/.credentials.json` mode 0600 (docs /iam). Local file present. On Windows 2.1.309 it was
  written at the browser sign-in (559 B) and rewritten at each token refresh; its fields are in
  [Secrets](#secrets). On Linux 2.1.310 it was written at the sign-in (559 B, mode 0600, the
  Windows key set) and rewritten overnight in an idle session when the access token was refreshed,
  at the same size: the file's modification time is not the sign-in time, and only its hash shows
  that it changed.
- `~/.claude/.device-keys.json` (device key store, file fallback to keychain, cc:477075,
  cc:337890-900). Not moved by `CLAUDE_CONFIG_DIR`. Not written by the sign-in or at any later step
  on Windows 2.1.309.
- `.claude.json` holds the sign-in session and MCP server definitions (docs; cc:406053 "refusing
  to write to avoid wiping ~/.claude.json" auth) and is flagged `secret: true`; its credential
  fields are in [Secrets](#secrets).
- `hfi-auth.json`, `.session_ingress_token`, `remote/.oauth_token`, `remote/.api_key` (cloud/host
  handoff), `CLAUDE_CODE_HOST_CREDS_FILE` path (cc:272494, 276584 region), Claude Desktop
  `host-creds-*.json` (see claude-desktop).
- `<config>/sessions/<pid>.<sha256>.key` (139 bytes on Linux, 108 bytes on macOS) beside the
  per-process `sessions/<pid>.json`, observed on real installs with CLI 2.1.295 launched from the
  Claude Desktop Code tab on Linux and on macOS, 2026-10-11 (see
  [issue 76](https://github.com/seanthegeek/doubleagent/issues/76) and
  [`claude-desktop.md`](claude-desktop.md)); flagged `secret: true` (`.claude/sessions/*.key`,
  `.claude-*/sessions/*.key`). On Windows 2.1.309 it is 118 B, a JSON object whose fields are in
  [Secrets](#secrets), and is removed with its `<pid>.json` when the process exits. On Linux 2.1.310
  it is 138 or 139 B, mode 0600, in a `sessions/` of mode 0700, a JSON object with a different third
  key ([Secrets](#secrets)), removed at the exit in the same way. The `<pid>.json` itself is not
  flagged ([Remote Control](#remote-control)).
- The session daemon's `daemon/control.key`, `daemon/pipe.key` and `daemon/roster.json`
  ([Session daemon files](#session-daemon-files)): the first two are raw keys, the roster holds two
  auth tokens per worker. Flagged `secret: true` since this round (`.claude/daemon/control.key`,
  `.claude/daemon/pipe.key`, `.claude/daemon/roster.json` and their `.claude-*/` forms).
- `backups/.claude.json.backup.<epoch ms>` ([Files that hold evidence](#files-that-hold-evidence)):
  each a full copy of `.claude.json` with its sign-in details, flagged `secret: true` since this
  round (`.claude/backups/.claude.json.*` and the `.claude-*/` form, which also takes the
  `.claude.json.corrupted.<ts>` copy of [Per-user storage](#per-user-storage)). The home-level
  `.claude.json.backup*` files of the older layout, beside `~/.claude.json`, are flagged with them.
- The GitHub account Claude Code acts through, and its token, are in the `gh` tool's store, not in
  Claude Code's files ([Source-host integration](#source-host-integration)).
- Config files that can embed keys: `settings.json` / `settings.local.json`, `.mcp.json`,
  `managed-mcp.json` (the fields are in [Secrets](#secrets)). Env: `ANTHROPIC_API_KEY`,
  `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN` (docs /iam precedence list). Anthropic profiles
  live outside: `~/.config/anthropic` / `%APPDATA%\Anthropic` (docs /iam).

### Exclusions

Patterns are relative to the home: `.claude/plugins/marketplaces` (git clones, 13.7 MB for the
official marketplace on Windows 2.1.309), `.claude/plugins/cache`,
`.claude/plugins/plugin-directory-cache*` (the 2.6 MB download of the plugin directory, excluded
since this round), `.claude/plugins/*/node_modules`, `.claude/local/node_modules`,
`.claude/image-cache`, `.claude/chrome`, `.claude/cache` (the changelog and the model catalog),
`.claude/statsig` (flag cache, optional), `.local/share/claude/versions` (~245 MB per version, 282.7
MB for 2.1.309 win32-arm64). `.claude/paste-cache` is collected since this round: `history.jsonl`
names a long paste by its hash alone, so once the transcript is gone the paste cache holds the only
copy of the text ([`history.jsonl`](#historyjsonl)). `skills/synced/` is a copy of account state
and is collected, as the list of skills the agent could use on the host. Project-side:
`*/.claude/worktrees`, `*/.claude/checkpoints` (gitignore template cc "claude-code-runtime").
`downloads/`, `uploads/`, `file-transfers/` may be large but are user content; cap by size rather
than exclude. The [CLI cache directory](#cli-cache-directory) is small and nothing in it, its
`errors/` subdirectory included, is excluded. On Windows the catalog names the cache directory's
children (`AppData/Local/claude-cli-nodejs/Cache/*`) rather than the directory, so that the Claude
Desktop exclusion `*/Claude*/Cache` does not prune it
([`collectors/docs/coverage.md`](../collectors/docs/coverage.md) says why). The VS Code
extension's copy of the CLI binary
(`.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude`, 291 MB on Linux
2.1.310, [VS Code extension files](#vs-code-extension-files)) needs no exclusion: the `vscode`
catalog entry takes `extensions.json` only.

### Project-local files

`.claude/settings.json`, `.claude/settings.local.json`,
`.claude/{skills,commands,agents,hooks,rules}/` (cc "agents"/"settings.json" ctx), `.mcp.json`
(cc:273219), `CLAUDE.md`, `CLAUDE.local.md` (cc:19360, 299964), `.claude/scheduled_tasks.json`,
`.claude/scheduled_tasks.lock`, `.claude/routines/.state/`, `.claude/worktrees/`,
`.claude/checkpoints/`, `.claude/mailbox/`, `.claude/agent-registry.json`,
`.claude/agent-memory-local`, `.claude/first-run`, `.claude/assistant-daemon-state.json` (gitignore
template, cc "claude-code-runtime" ctx). The built-in `agents-md` mod also reads `AGENTS.md`
and `.claude/AGENTS.md` as project instructions, by default where a project has no `CLAUDE.md`
([`mods/agents-md/hooks/names/agents-names.ts:5`](https://github.com/anthropics/claude-code/blob/1132b8a98e93300bb3822197fb7eee12ce4fb906/mods/agents-md/hooks/names/agents-names.ts#L5));
the collector gathers them through the shared `project|AGENTS.md` entry and `claude-code|.claude`.
No per-project database.

Observed on Windows 2.1.309:

- `.claude/settings.local.json` was created by the first allow-always answer (87 B, one
  `permissions.allow` rule, [Permission configuration](#permission-configuration)), and in the same
  second Claude Code created the user's `~/.config/git/ignore` to keep that file out of commits
  ([Files that hold evidence](#files-that-hold-evidence)).
- `.claude/scheduled_tasks.lock` (123 B JSON, `acquiredAt, pid, procStart, sessionId`) was written by
  `/loop`; no `scheduled_tasks.json` was left beside it after the task was deleted
  ([Scheduled tasks](#scheduled-tasks)).
- `.git/info/exclude` was rewritten in the same second as the lock: git's six-line default template
  plus eleven exclude patterns that name `claude` (541 B, 17 lines). It is git metadata and is
  collected with the project's other `.git/` files since this round (`project|.git/info/exclude`).
- Removing the project directory removes these files and nothing in the home
  ([What survives a delete](#what-survives-a-delete)).

Observed on Linux 2.1.310: the allow-always answer created `.claude/` and
`.claude/settings.local.json` (72 B, mode 0664, one rule,
[Permission configuration](#permission-configuration)), with `~/.config/git/ignore` in the same
second; `/loop` wrote `.claude/scheduled_tasks.lock` (112 B, the same four keys), which was left
behind after the loop was stopped, with no `scheduled_tasks.json` beside it
([Scheduled tasks](#scheduled-tasks)). Removing the project (52 entries) removed these files and
nothing in the home.

### Where the project path is recorded

- `~/.claude.json` → `projects` object, keys are absolute cwd paths (cc:474276 `e.projects`; docs
  "per-project state such as trust decisions"). In a relocated home it is
  `<config home>/.claude.json`; `discover_projects` and `Find-Projects` read
  `~/.claude-*/.claude.json` and `~/.claude-*/history.jsonl` as well as the default paths. On
  Windows 2.1.309 the key is the native path with backslashes and the drive letter
  (`C:\Users\sean\lab\proj`), written at the trust dialog of the first launch, and the transcript
  directory for it is `projects/C--Users-sean-lab-proj/`
  ([issue 112](https://github.com/seanthegeek/doubleagent/issues/112)); a start in the home that
  stopped at the trust prompt added no key. On Linux 2.1.310 the key is the plain absolute path
  (`/home/sean/lab/proj`), written at the trust dialog, with the transcript directory
  `projects/-home-sean-lab-proj/`; a start in the home that stopped at the trust prompt added no
  key, no `projects/-home-sean/` directory and no history line. `projects.<path>.lastSessionId`
  names the last session run there ([`.claude.json`](#claudejson)). The `environment` attachment's
  `snapshot.scratchpadDirectory` spelled the same project's slug two ways across sessions on
  Windows 2.1.309, `C--Users-sean-lab-proj` and `c--Users-sean-lab-proj` (the drive letter's case
  differs), so a project's scratch directories can differ only by case
  ([issue 112](https://github.com/seanthegeek/doubleagent/issues/112)).
- `~/.claude.json` → `githubRepoPaths`, `{"<owner>/<repo>": ["<local path>", ...]}`: every GitHub
  repository the CLI has seen as a checkout's `origin` remote, with the local checkouts of it. On
  Windows 2.1.309 it was filled at the first launch in the lab checkout, with no GitHub sign-in, and
  still listed the path after the checkout was removed; Linux 2.1.310 did the same.
- `history.jsonl` → `project` on every line ([`history.jsonl`](#historyjsonl)).
- Transcript records: every `projects/<key>/<id>.jsonl` record carries `"cwd"` (cc:482870 parser;
  the envelope is in [Record schema](#record-schema)). The directory key is lossy (dashes), so read
  `cwd` rather than decode the key.
- [CLI cache directory](#cli-cache-directory): every `mcp-logs-*/<timestamp>.jsonl` line
  carries `cwd`, a project path, and the slug directory above it is the lossy key of the same path.
  `discover_projects` and `Find-Projects` do not read it.
- Claude Desktop `claude-code-sessions/` records each Code session's working folder (docs
  data-storage) and points back to `~/.claude/projects/`.

## Parsing

### Transcript stores

The config home is `$CLAUDE_CONFIG_DIR`, else `~/.claude`, on every OS
([Per-user storage](#per-user-storage)). Relative to the home:

| Path | Content | Parse |
| --- | --- | --- |
| `.claude/projects/<key>/<session id>.jsonl` | the session transcript; `<key>` is the cwd with every `[^a-zA-Z0-9]` replaced by `-`, cut at 200 characters plus `-` and a base-36 hash when longer (cc:473717, cc:474429); the session id is a UUID (cc:477784 `${q()}.jsonl`) | yes |
| `.claude/projects/<key>/<session id>/subagents/agent-<agent id>.jsonl` | one transcript per subagent, same record format; an optional extra directory level sits between `subagents/` and the file when the agent has a transcript subdirectory (cc:477784 `agentTranscriptSubdirs`, cc:484031 parses `subagents/<dirs...>/agent-(.+).jsonl`) | yes |
| `.claude/projects/<key>/<session id>/subagents/agent-<agent id>.meta.json` | one JSON object per subagent: `agentType`, `description`, `toolUseId`, `model`, `spawnDepth`, `requestShape`, `requestNonInteractive`, and for some `isFork`, `parentAgentId`, `spawnedWithWorktree`, `worktreePath`, `worktreeBranch` (observed, 80 of 80; cc:484010 maps `.meta.json` to `.jsonl`); on Windows 2.1.309 `agentType, description, finished, launchedWithDefaults, requestNonInteractive, requestShape, spawnDepth, toolUseId`, with no `model` (226 B); on Linux 2.1.310 the same plus `isBuiltIn` (243 B, `requestShape` `background`) | no, [Joins and timestamps](#joins-and-timestamps) |
| `.claude/projects/<key>/<session id>/tool-results/<name>.txt` | full output of a tool result too large to keep inline (`tool-results` constant, cc:474483); the inline result holds a `<persisted-output>` stub (cc:382991); on Windows 2.1.309 `<name>` is nine base-36 characters (1.2 MB for a 20,000-line listing; on Linux 2.1.310 191,741 B for 20,000 lines of a word list) | yes, [Persisted output files](#persisted-output-files) |
| `.claude/projects/<key>/<session id>/custom-title.json` | `{customTitle}`, the name given with `/rename` (27 B on Windows 2.1.309), beside the transcript's `custom-title` line | no; the line is read |
| `.claude/jobs/<short>/state.json`, `.claude/jobs/<short>/timeline.jsonl` | a daemon worker's job state and its state changes ([Session daemon records](#session-daemon-records)) | no |
| `.claude/projects/<key>/<session id>/remote-agents/remote-agent-<id>.meta.json`, `.../mcp-tasks/mcp-task-<id>.meta.json` | sidecars for remote agents and MCP tasks (cc:484010, cc:488428) | no; not observed |
| `.claude/projects/<key>/memory/*.md` | per-project memory files (observed) | no |
| `.claude/history.jsonl` | prompt history across sessions, [Other stores](#other-stores) | yes, as history |
| `.claude/sessions/<pid>.json` | live-process registry, one file per running CLI process; its keys are under [Remote Control](#remote-control) | yes, one `system` row per file, [Parser plan](#parser-plan) |
| `.claude/jobs/<id>/parent-transcript.jsonl` | a copy of the parent transcript handed to a background job (cc:474968) | no; not observed |
| `.claude/dump-prompts/<session id>.jsonl` | full outgoing prompts, when that debug option is on (cc:487015) | no; not observed |
| `<CLI cache directory>/<key>/mcp-logs-<server>/<timestamp>.jsonl` | MCP server log of the CLI, outside the config home; paths per platform and line shape under [CLI cache directory](#cli-cache-directory) ([issue 81](https://github.com/seanthegeek/doubleagent/issues/81)) | no; a possible source of `system` rows ([Parser plan](#parser-plan)) |

The parser selects `projects/[^/]+/.*\.jsonl$` and `history.jsonl` under `.claude` or a
`.claude-<name>` home, so it reads main and subagent transcripts at any depth, ignores the
`.meta.json` sidecars, and reads a `.txt` sidecar only when a stub names it
([Parser plan](#parser-plan) gives every glob). A config home moved with `CLAUDE_CONFIG_DIR` to a
`.claude-<name>` directory in the home (for example `~/.claude-work`) is matched by the parser as
far as it is collected ([Relocated config homes](#relocated-config-homes-claude_config_dir)); a
config home elsewhere or under another name is neither collected nor parsed.

One file is one session id. Observed on Windows 2.1.309: a start and `/exit` with no prompt still
writes a six-line transcript (`mode`, `permission-mode`, three `user` lines of the `/exit` command,
a `file-history-snapshot`) and a `history.jsonl` line; `/clear` starts a new file in the same
process; `claude --resume` appends to the chosen session's file under the same `sessionId`; a
session handed to a daemon worker continues in the worker's file, and the console's file ends with
a `continued-in` line ([Session daemon records](#session-daemon-records)). After a reboot killed an
open session its file stayed as it was and the next start opened a new session, with nothing on
screen about the old one. Observed on Linux 2.1.310 the same, with no daemon: the empty session
writes the same six lines (2,060 B) and history line; `/clear` starts a new file in the same
process; a resumed or continued session stays in its own file
([Joins and timestamps](#joins-and-timestamps)). The transcript and subagent files
are mode 0600, the `.meta.json` and `tool-results/` files 0664. `/rename` wrote `custom-title.json`
(27 B) and a `custom-title` and an `agent-name` line.

#### VS Code extension sessions

A session started from the VS Code extension's panel (2.1.309 on Windows, 2026-10-23) is an
ordinary transcript in the same `projects/<key>/` directory as the CLI's, so one catalog agent
covers both. Every line carries `entrypoint` `claude-vscode` where the CLI's carry `cli`, and its
`user` prompt lines `promptSource` `sdk` with `origin.kind` `human` and `turnOrigin` `human`. It has
no `system`, `mode`, `permission-mode` or `continued-in` line (not even `turn_duration`); its
`environment` attachment has `changes` beside `snapshot`, its `deferred_tools_delta` adds
`needsAuthMcpServers`, and its shell tool call was `Bash` where the CLI session on the same host
used `PowerShell`. It took the permission mode and the default model the CLI had left in
`settings.json` (`auto`, so no approval was asked). The extension also started a second session id
in the same second, with a temp directory and no transcript
([Scratch directories](#scratch-directories)), and the session's connector MCP logs are the same as
a CLI session's ([CLI cache directory](#cli-cache-directory)). `.claude.json`
`clientDataCacheSlots` gained an entry whose `entrypoint` is `claude-vscode`
([`.claude.json`](#claudejson)). On Linux 2.1.310 (2026-10-26) the extension's session file
(335,769 B, 43 lines) again carried `entrypoint` `claude-vscode` on every envelope line,
`promptSource` `sdk` on the prompt and no `mode` or `permission-mode` line; it held a `cost-state`
line, `queue-operation` lines without `content`
([`queue-operation` records](#queue-operation-records)), and its `Bash` call was allowed by the
classifier in `auto` mode. Its prompt is not a `history.jsonl` line
([`history.jsonl`](#historyjsonl)).

#### What survives a delete

The retention setting `cleanupPeriodDays` (default 30, minimum 1; cc:474049 setting description,
cc:490770 `cleanupPeriodDays??`) drives a sweep that deletes old session data. The vendor's
[Explore the .claude directory](https://code.claude.com/docs/en/claude-directory.md#cleaned-up-automatically)
lists what it deletes once older than the period: `projects/<project>/<session>.jsonl` with its
`.orphaned-*` and `.superseded-*` copies, the session's `subagents/` (with the parent),
`tool-results/` and `mcp-tasks/`, `file-history/<session>/` (keeping the 100 most recent
checkpoints and each file's first snapshot), `plans/`, `debug/`, `paste-cache/`,
`image-cache/<session>/` (2.1.274 and earlier; later builds keep images under the temp directory's
per-session `images/`), `uploads/<session>/` (Remote Control attachments), `dev-mods/<session>/`,
`session-env/`, `tasks/`, `shell-snapshots/` (removed at a clean exit; the sweep clears what a
crash left), `backups/` (the five newest kept), `feedback-bundles/`, `feedback/drafts/`,
`usage-data/`, `skills/.trash/`, `plugins/.trash/`, `plugins/installed_plugins.set-aside.*` and
`.unreadable.*`, and the legacy `todos/`, `statsig/` and `logs/`. Its own rules: `sessions/` loses
each file when its session exits and a crash's leftovers at the next launch; the auto memory
`projects/<project>/memory/` is kept, the directory removed only when it stayed empty for the whole
period (before 2.1.228 the sweep could delete files beneath it); Claude Desktop and Cowork
transcripts are kept at any age unless `desktopSessionCleanupPeriodDays` (2.1.248 and later),
managed settings or the HIPAA configuration (the setup for health data under the United States
HIPAA rules) say otherwise; and a session's scratchpad goes with its transcript
([Scratch directories](#scratch-directories)). The page keeps until the user deletes them
`history.jsonl` (older entries are removed only under the HIPAA configuration),
`stats-cache.json`, `remote-settings.json` (deleted at logout), `cache/changelog.md` and
`policy-limits.json`, and names as state files to keep `.credentials.json`, `agent-memory/`,
`jobs/` and `daemon/`. The sweep is skipped in `--bare` mode and paused when the period cannot be
determined (`/status` warns).
[Settings reference, `cleanupPeriodDays`](https://code.claude.com/docs/en/settings-reference#cleanupperioddays)
says Claude Code "runs the deletion as a background sweep after a session starts" and "deletes
transcripts without showing a message";
[Monitoring usage, Retention sweep event](https://code.claude.com/docs/en/monitoring-usage#retention-sweep-event)
says it runs at most once per session, that a sweep not finished when the session exits emits
nothing, and that from 2.1.227 it emits the OpenTelemetry event `claude_code.retention_sweep`
(OpenTelemetry being the telemetry export standard of Claude Code's monitoring) with `result`
(`complete` or `skipped`), `skip_reason` (`user_source_disabled`, `settings_unknowable`,
`settings_invalid_key_set`), `period_days`, `used_default`, `transcripts_deleted`,
`transcripts_exempted_desktop`, `session_files_deleted`, `artifacts_deleted`,
`files_retained_fresh`, `files_past_cutoff` and `error_count`.

The user's own delete is `claude purge <project>` (`claude project purge` before 2.1.288, on the
same page): it deletes the project's `projects/` tree and auto memory, the per-session `tasks/`,
`debug/` and `file-history/`, the matching `history.jsonl` lines and the project's `~/.claude.json`
entry, and leaves `shell-snapshots/`, `backups/`, the temp directory and `.heapsnapshot` files.
Neither round ran it.

Observed on Linux 2.1.310 (2026-10-25 and 2026-10-26), with `cleanupPeriodDays` set to 1 and the
empty transcript of the first session backdated three days: the sweep ran at 03:34:43Z, in a
`claude --debug` session started at 02:37:33Z whose one prompt was at 03:14:31Z. It deleted that
transcript and its session's scratchpad directory under the temp root, rewrote `.last-cleanup` and
kept the session's `history.jsonl` line; nothing else was old enough to go. The debug log's only
trace of it is one line at 03:34:43.431Z,
`settings.read: the engine's merge is not raised again (a retention sweep starts): neither the loaded plugins nor the settings changed.`
Over the round the sweep ran in three sessions, each 10 to 20 minutes after that session's last
prompt (23:15:06Z to 23:25:46Z, 01:21:28Z to 01:32:08Z, 03:14:31Z to 03:34:43Z), and in none of the
four sessions that had no prompt: two that exited within a minute, the second after `.last-cleanup`
had been rewritten by hand to a week earlier, one left idle for 24 minutes, and the first 37
minutes of the `--debug` session, whose log has no retention, cleanup or housekeeping line in that
time. The vendor's "after a session starts" is the claim; the condition observed on 2.1.310 Linux
is a session with at least one prompt.

Since 2.1.309 the setting cannot be 0:
on Windows (2026-10-23) a `settings.json` with `"cleanupPeriodDays": 0` stopped the start with a
Settings Error screen reading `cleanupPeriodDays: Number must be greater than or equal to 0`, then
`cleanupPeriodDays must be at least 1. To keep transcripts for a long time, set a large number (e.g.
3650 for ~10 years). To disable transcript writes entirely, remove this setting and use the
--no-session-persistence CLI flag or the SDK persistSession:false option instead. (0 is rejected
because it previously silently disabled all transcript writes, which users setting it to mean
"never clean up" did not expect.)` and `Files with errors are skipped entirely, not just the invalid
settings.`, with the choices `Fix with Claude`, `Exit and fix manually` and
`Continue without these settings`. The refused start still left a temp directory for a session id
with no transcript, a `backups/` copy and a model-catalog refresh. With `1` the start ran, but the
sweep did not: `.last-cleanup` kept its earlier content and nothing under `projects/`,
`file-history/`, `history.jsonl` or the temp root was removed, since a one-day period cannot reach
files written that day. The Windows round therefore did not observe what the retention sweep
removes; the only sweep seen there is the housekeeping one that pruned `backups/` and the temp root
([Scratch directories](#scratch-directories)).

Observed on Windows 2.1.309 and Linux 2.1.310 for the user's other ways to end a session:

- `/clear` is not a delete: it starts a new transcript file with the full session preamble, the old
  file keeps every turn and gains only a `cost-state` line, no marker, and `history.jsonl` keeps the
  old session's lines and records the next prompt under the new id. On Linux the old file gained a
  `system` line beside the `cost-state` line, and the `/clear` command's lines were in the new file.
- `/exit` removes the process's `sessions/<pid>.json` and `.key` and its shell snapshot, and nothing
  of the transcript; with the daemon running, the worker holding the session and its registry file
  stay ([Session daemon files](#session-daemon-files)). On Linux it also removed the version lock
  ([Native installer](#native-installer)) and the session's `bash-edit-diff/` snapshots, and kept
  `session-env/<session id>/` and the temp root ([Scratch directories](#scratch-directories)).
- Removing the project directory (`Remove-Item -Recurse -Force`) removed only the project's files
  ([Project-local files](#project-local-files)). Every trace in the home stayed: the
  `projects/<key>/` directory with all eight transcripts, `subagents/`, `tool-results/` and
  `custom-title.json`; `file-history/<session id>/`; `plans/`; every `history.jsonl` line, each
  naming the project in `project`; the `.claude.json` `projects.<path>` entry and
  `githubRepoPaths`; the CLI cache directory's `<slug>/mcp-logs-*`; and the temp root's `<slug>`
  directory. A later start in the home that stopped at the trust prompt wrote only a temp directory
  under the home's slug and a refresh of `plugins/synced/` and `skills/synced/`. On Linux
  (`rm -rf`) the same held: `projects/-home-sean-lab-proj/` kept its 12 entries, `.claude.json`
  kept `projects."/home/sean/lab/proj"` and `githubRepoPaths`, all 43 `history.jsonl` lines named
  the path, and the CLI cache and the temp root kept the project's slug, `bash-edit-diff/`
  included.
- A reboot removed nothing on Windows; on Linux it cleared the temp root and changed nothing in the
  home ([Scratch directories](#scratch-directories)).

The per-prompt history ([`history.jsonl`](#historyjsonl)) usually outlives its transcript and is
then the only record of the prompt, except a prompt sent through `claude agents` or from the VS Code
extension's panel, which it does not record; the retention sweep keeps it, so a session found only
in `history.jsonl` is what a swept session leaves. Long pasted text is in `paste-cache/`, collected
since this round, and a short paste is inline in the history line. Beside it in the config
home sit the backups of files the agent edited (`file-history/<session id>/`), the dated copies of
`.claude.json` in `backups/`, the live-process records of `sessions/<pid>.json`, a background job's
copy of its parent transcript (`jobs/<id>/parent-transcript.jsonl`, not observed), the daemon's job
files and the project paths in `.claude.json`; the vendor's list above says which of them the
sweep removes and which it keeps, and a project's `.claude.json` entry goes with `claude purge`,
which the list does not name for the sweep. Inside
the transcript each `api-request-blob` line repeats a full request message, the prompt text
included ([Record schema](#record-schema)). Hermes Agent's `state.db`, a Cline session made by the
SDK's import and Pydantic AI's CLAI `sessions.db` hold copies that outlive the original file
(below). No deletion marker is stated or was seen. The analyzer reads `history.jsonl` as a secondary
source and the session records and `.claude.json` for their own rows, not `file-history/`,
`paste-cache/`, `backups/` or `jobs/`; it lists a removed project that the collected files still
name with the `referenced` status; the other agents' copies are read, if at all, under those agents
(see [Secondary sources](../analyzer/docs/output.md#secondary-sources)).

- **Copies held by other agents.** Three agents copy these transcripts into stores of their own,
  where the copy outlives the original file (from source; none seen on a real install):
  - Hermes Agent's `hermes_cli/foreign_sessions.py` reads Claude Code's
    `~/.claude/projects/*/*.jsonl` and appends their user and assistant turns to its `state.db` as a
    new session whose `origin_json.imported_from` names the tool, the source path and the foreign
    session id, stamped with the import time
    ([`hermes_cli/foreign_sessions.py:254-260`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/foreign_sessions.py#L254-L260);
    [Imported sessions in `hermes.md`](hermes.md#imported-sessions)).
  - Cline's SDK session import makes an ordinary Cline session with a new id and
    `metadata.importedFrom{tool, sourceSessionId, sourcePath, importedAt, sourceProvider, sourceModel}`;
    at the reviewed commit only Cline's example desktop app calls it
    ([`sdk/packages/core/src/services/session-import/service.ts:349-366`](https://github.com/cline/cline/blob/41e75efc53e7abbcb76564b89e6de57f78659b33/sdk/packages/core/src/services/session-import/service.ts#L349-L366);
    [Transcript stores in `cline.md`](cline.md#transcript-stores)).
  - Pydantic AI's CLAI 2.0 (its command-line chat client) `/resume` copies them into its
    `sessions.db`
    ([`claude_code_sessions.py:41-43`](https://github.com/pydantic/pydantic-ai/blob/0ba01f92be3fc361f89970502cd6e7dd3611aec3/src/pydantic_clai2/pydantic_clai2/runtime/claude_code_sessions.py#L41-L43);
    [Other agents' sessions in `pydantic-clai.md`](pydantic-clai.md#other-agents-sessions)).
- **Indexed by Zed.** Zed's agent panel can run this agent as an external agent over ACP (the Agent
  Client Protocol, the JSON-RPC protocol Zed uses to drive another agent); its threads sidebar then
  lists the session in `sidebar_threads` with `agent_id` `claude-acp` and the ACP session id in
  `session_id`, while the transcript stays in this agent's own store
  ([`agent_servers/src/custom.rs:17-19`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_servers/src/custom.rs#L17-L19);
  [Transcript stores in `zed.md`](zed.md#transcript-stores)). Whether that id equals the session id this
  agent records was not determined.

### Record schema

Every line is one JSON object with a `type`. The loader's own type table (cc:484009, `nxr`) lists
every type 2.1.289 reads, with how it merges repeats; a second table (cc:484010, `rss`) says which
survive a session copy. The Observed column counts lines on the WSL2 install; the Windows column
says whether the type was written on Windows 2.1.309:

| `type` | Loader class | Observed | Windows 2.1.309 | Holds |
| --- | --- | --- | --- | --- |
| `user` | transcript | 6,008 | yes | a user turn: prompt, tool results, injected text |
| `assistant` | transcript | 9,911 | yes | one content block of a model response |
| `system` | transcript | 318 | yes | runtime notices, by `subtype` |
| `attachment` | transcript | 10,794 | yes | context injected into the next request, by `attachment.type` |
| `progress` | boundary-cleared | 0 | no | streamed tool, hook and forked-agent progress (bundle: cc:482374, cc:482655, cc:483757, cc:482596) |
| `file-history-snapshot`, `file-history-delta` | boundary-cleared | 172, 25 | yes | which files were backed up before edits, and the backup names ([File-history records](#file-history-records)) |
| `last-prompt` | boundary-cleared | 602 | yes | `lastPrompt` (text of the latest prompt), `leafUuid` |
| `continued-in` | boundary-cleared | 0 | yes | `continuedInSessionId`, `sessionId`, `timestamp` (cc:480715): the session continued in another session's file ([Session daemon records](#session-daemon-records)) |
| `content-replacement` | accumulate | 0 | no | `replacements`, optional `agentId` (cc:484029, cc:494705) |
| `api-request-shape`, `api-request-blob`, `api-request` | boundary-cleared | 0 | yes | request capture, written by default on 2.1.309: `api-request-shape` `{shape, shapeHash, timestamp, version, sessionId}`, the shape that `api-request` lines name by `shapeHash`, with a new line when the tool set changed (105,657 B for the first); `api-request` `{base, cacheControl, id, keep, params, querySource, requestDigest, shapeHash, tail, timestamp, version}` per request, `params` `{betas, context_management, max_tokens, model, output_config, thinking}`; `api-request-blob` `{hash, message}`, `message` `{clear_at, content, output_config, role}`, a full request message, so the prompt text is stored a second time in the file (a subagent's lacks `clear_at`) |
| `fork-context-ref`, `frame-link` | accumulate | 0 | no | fork reference (cc:484031); artifact link `path`, `frameUrl`, `title`, `artifactCount`, `timestamp` (cc:504346) |
| `summary` | last-wins | 0 | no | legacy session summary `summary`, `leafUuid` (cc:484055) |
| `custom-title`, `ai-title` | last-wins | 0, 548 | yes | `customTitle` (user-set name, `{customTitle, sessionId, type}`, written by `/rename` with `custom-title.json` beside it), `aiTitle` (generated name) |
| `tag`, `relocated` | last-wins | 0 | no | `tag`; `relocatedCwd`, written when the session's cwd moves (cc:484038) |
| `ended-by-model` | last-wins | 0 | no | `timestamp` only (cc:484055) |
| `agent-name`, `agent-color`, `agent-setting` | last-wins | 129, 0, 0 | `agent-name` only | `agentName`, `agentColor`, `agentSetting`; `agent-name` is `{agentName, sessionId, type}` and was re-written each time the session was renamed |
| `pr-link` | last-wins | 221 | no (no pull request was made) | `prNumber`, `prUrl`, `prRepository`, `timestamp` |
| `mode`, `permission-mode` | last-wins | 608, 410 | yes | `mode` (`normal` observed); `permissionMode` (`auto`, `plan` observed; `auto` in all 308 records on the 2.1.296 install; `auto`, `default`, `acceptEdits` and `plan` on Windows 2.1.309, where the status line calls `default` "manual" and Shift+Tab cycles auto, manual, accept edits, plan). The permission mode is how tool calls are approved: `default` prompts, `acceptEdits` allows file edits, `plan` only plans, `bypassPermissions` allows everything, `dontAsk` denies what would prompt, `auto` lets a classifier decide (`claude 2.1.296 darwin-arm64 @187461122` `var CH=["acceptEdits","auto","bypassPermissions","default","dontAsk","plan"]`, with `manual` read as an alias for `default`; `@188412753` `if(e==="auto")return"classify";if(e==="bypassPermissions"\|\|_V(e,n))return"allow";if(e==="dontAsk")return"deny";return"ask"`). The record is `{type, permissionMode, sessionId}` with no `timestamp` (`@199803784` `type:"permission-mode",permissionMode:this.currentSessionPermissionMode,sessionId:y`). A fresh install starts in `auto` |
| `bridge-session` | last-wins | 256 | yes | `bridgeSessionId`, `lastSequenceNum`, `ownerAccountUuid`, `ownerOrganizationUuid`, `sessionId`; `bridgeSessionId` null on the line written at the disconnect ([Remote Control](#remote-control)) |
| `atis-latch`, `cost-state`, `queue-operation` | last-wins | 607, 25, 488 | yes | an opaque token; cumulative cost and per-model token usage, `{hasUnknownModelCost, modelUsage, sessionId, startTime, totalAPIDuration, totalAPIDurationWithoutRetries, totalCostUSD, totalDuration, totalLinesAdded, totalLinesRemoved, totalToolDuration, type}` on 2.1.309, written when a session's process stops writing to the file (an exit, a `/clear`, the daemon handover); prompt queue changes |
| `isolation-latch`, `dev-mods`, `memory-mode`, `worktree-state`, `history-suppression`, `attribution-snapshot`, `artifact-comment-monitor`, `artifact-autoreact-ledger`, `observer-ref` | various | 0 | no | session state (cc:484021, cc:484022) |

Session-state records (`last-prompt`, titles, `agent-name`, `mode`, `permission-mode`, `atis-latch`,
`worktree-state`, `pr-link`, `frame-link`, `bridge-session`) are re-appended as a block whenever the
session's metadata is flushed (cc:484021, cc:484022); on Windows 2.1.309 a `/compact` re-emitted
five of each. They carry `sessionId` and of the non-transcript types only `pr-link`, `frame-link`,
`queue-operation`, `continued-in` and the `api-request*` lines carry a `timestamp`, which for
`pr-link` is the time of the flush (`timestamp:new Date().toISOString()` in the re-append), not of
the pull request. Observed: one file holds 105 `pr-link` lines for a single URL.

On Linux 2.1.310 one `/compact` took `ai-title` from 6 to 16 lines, `atis-latch` from 8 to 18,
`mode` and `permission-mode` from 8 to 18, `last-prompt` from 8 to 17 and `file-history-snapshot`
from 10 to 21, so counts of these types are not turn counts. The `permission-mode` record is also
written lazily there: a Shift+Tab to `default` appeared as a `permission-mode` line only at the
next prompt, and a switch to `acceptEdits` never got one, while every prompt line carried its
`permissionMode`, which is therefore the per-turn evidence of the mode.

Byte shares on Windows 2.1.309, for the daemon worker's session file after the resume step
(1,271,056 B, 436 lines): `attachment` 91 lines and 531,967 B, `api-request-blob` 63 and 116,591 B,
`assistant` 49 and 105,885 B, `user` 51 and 98,449 B, `api-request` 36 and 64,636 B, `system` 25
and 13,389 B, `file-history-snapshot` 21 and 9,818 B; the three `api-request-shape` lines after the
`/compact` were 317 KB. Context and request capture, not the conversation, are most of the file.

On Linux 2.1.310 (2026-10-25 and 2026-10-26) every line type and key set of a two-turn session
equalled Windows 2.1.309's for the `cli` entrypoint, and a session that ran every step reached
1,202,662 B and 449 lines; a compaction took one file from 800 KB to 1,173,652 B, the context being
re-attached after the boundary. The key-set differences the round found are in the subsections
below.

#### Transcript envelope

The envelope of `user`, `assistant`, `system` and `attachment` records (observed on every one unless
noted): `type`, `uuid` (UUID), `parentUuid` (UUID, or null on a chain root: observed on the first
transcript record of every file and on one `system` record), `timestamp` (ISO 8601 UTC,
milliseconds, `Z`; 27,061 of 27,061), `sessionId` (UUID), `cwd`, `gitBranch`, `version` (`2.1.NNN`),
`isSidechain` (false in session files, true in subagent files, 18,429 of 18,429), `userType`
(`external`), `entrypoint` (`cli` observed; `claude-vscode` on every line of a VS Code extension
session on Windows 2.1.309, [VS Code extension sessions](#vs-code-extension-sessions)), optional
`slug` (plan name), `agentId` (subagent files only: equals the file's `agent-<id>`), and on some
`user`, `assistant` and `attachment` records a snake-case `session_id`
([Joins and timestamps](#joins-and-timestamps)). On Windows 2.1.309 the lines of a daemon worker's
file and of a subagent file also carry `sessionKind` (`bg` on every type) and `slug`. On Linux
2.1.310, with no daemon, no line carried `sessionKind`; `slug` appeared on every type once the
session had a title; subagent lines carry `agentId` on every type; and on a detached head
`gitBranch` is `HEAD` ([Joins and timestamps](#joins-and-timestamps)).

#### `assistant` records

An `assistant` record adds `message` (the Messages API response object: `id`, `type:"message"`,
`role`, `model`, `content`, `stop_reason`, `stop_sequence`, `usage`, `container`,
`context_management`, `stop_details`, `diagnostics`, `input_transformations`), `requestId`,
`apiBlockIndex`, `effort`, `perTurnEffort`, `advisorModel`, `serverClassifierRequest`, optional
`thinkingDurationMs`, `requestedModel` (observed on macOS with CLI 2.1.295, 2026-10-11),
`attributionAgent`, `attributionSkill`, and per tool call `wireToolInputs` and `wireIngestContext`
([Wire inputs](#wire-inputs)) (observed; built at cc:482605). API failures are `assistant` records
with `isApiErrorMessage:true`, `error`, `apiErrorStatus`, `message.model` `<synthetic>` and one text
block holding the error (observed 10; cc:477488). On Windows 2.1.309 the key set adds `requestRef`,
`session_id`, `thinkingDisplay` and `thinkingDurationMs` (with `thinking` blocks), and
`attributionMcpServer`, `attributionMcpTool` and `attributionSkill` on the turn a skill ran
(`/schedule`); `attributionAgent` is on a subagent's lines. `message.usage` holds
`cache_creation, cache_creation_input_tokens, cache_miss_reason, cache_read_input_tokens,
fallback_credit, inference_geo, input_tokens, iterations, output_tokens, output_tokens_details,
server_tool_use, service_tier, speed`. On Linux 2.1.310 the 22-key `assistant` set was identical
to Windows 2.1.309's; `wireIngestContext` was on the Remote Control turn's lines,
`attributionAgent` on a subagent's, and the `claude-sonnet-5-5` turns carried no `thinking` block
while the `claude-opus-5-5` ones did.

#### `user` records

A `user` record adds `message` (`role:"user"`, `content` string or block list), `promptId` (UUID),
and as applicable `isMeta`, `origin{kind, ...}`, `promptSource`, `turnOrigin`, `turnPosition`,
`permissionMode`, `toolUseResult`, `sourceToolAssistantUUID`, `serverClassifierContext`,
`isCompactSummary`, `isVisibleInTranscriptOnly`, `summarizeMetadata`, `interruptedMessageId`,
`toolDenialKind`, `userFeedback`, `queueSkipAttachments`, `queueTranscriptOnly` (the factory at
cc:483772 lists them; observed except the compaction fields, which Windows 2.1.309 showed). Windows
2.1.309 adds `sandboxed` (false), `session_id`, `permissionDecision`
([Permission decisions](#permission-decisions)), `mcpMeta` (on the `/install-github-app` command's
lines), `queueSkipSlashCommands` (the Remote Control prompt), and on the prompt a `/loop` fired
`scheduledFireId`, `scheduledTaskId`, `wakeupSource`, `turnCompanion` and `queuePriority`. Values
seen there: `promptSource` `typed`, `system` (a task notification or a `/loop` firing),
`suggestion_accepted` (a prompt Claude suggested and the person accepted), `queued` (the Remote
Control prompt) and `sdk` (the VS Code extension); `turnOrigin` `human`, `task_notification` and
`scheduled`; `origin.kind` `human` and `task-notification`, with `origin` keys
`kind, producer, runId` on the latter; `isMeta` on the lines of a slash command. On Linux 2.1.310
the same keys and values, with these placements: `sandboxed` (false) only on the result line of an
executed shell call, absent from a denied call's and from other tools' lines;
`serverClassifierContext` absent while every call was approved by hand and present once a shell
call was allowed by configuration; `mcpMeta` on an MCP tool's result line; `queueSkipAttachments`
(true) on a prompt typed while a turn ran; `queueSkipSlashCommands` on the Remote Control prompt;
`promptSource` `suggestion_accepted` on the prompt the `/schedule` flow left; and `permissionMode`
`default` on a prompt typed in the mode the status line calls manual.

#### Permission decisions

`permissionDecision` sits on the `user` line that carries the tool's `tool_result` (2.1.295 and
later). On Windows 2.1.309 and Linux 2.1.310 its keys were `decision`, `source`, `reasonType`,
`grantScope` and `reasonCode`, each only when it applies; a `reasonCode` cell names the Windows
values first and the Linux ones after the semicolon:

| How the call was allowed or refused | `decision` | `source` | `reasonType` | `grantScope` | `reasonCode` | Other keys on the line |
| --- | --- | --- | --- | --- | --- | --- |
| the `auto` mode classifier allowed it; on Linux also an `Agent` call in `default` mode | `accept` | `config` | `classifier` | - | - | - |
| the mode allows it without asking (a `Read` in `default`, an `Edit` in `acceptEdits`, a `Grep`) | `accept` | `config` | `mode` | - | - | - |
| a shell command allowed without a prompt in `default` mode (a `sleep` and a `cat`, Linux) | `accept` | `config` | `subcommandResults` | - | - | - |
| the person answered Yes once | `accept` | `user_temporary` | - | `once` | `other`, `unknown` or `subcommandResults` (a piped command approved as a whole); `bashMiss:no-rule-match` (a shell command no allow rule matched) or `unknown` (an `Edit`, a plain `head`) | - |
| an allow-always rule the person had granted (Windows), or the allow-always answer itself (Linux) | `accept` | `user_permanent` | - | - | `other`; `bashMiss:no-rule-match` | - |
| the person refused, typing a reason | `reject` | `user_reject` | - | - | `other`; `bashMiss:no-rule-match` | `toolDenialKind` `user-rejected`, `userFeedback` (the typed reason) |
| the person declined a plan ("tell Claude what to do instead") | `reject` | `user_reject` | - | - | `unknown` | `toolDenialKind` `user-rejected`, on the `ExitPlanMode` call |

One accept with `reasonType` `other` was also seen in plan mode, on both platforms. A file edit is
approved like a command. The shape of the denial is the one of
[issue 97](https://github.com/seanthegeek/doubleagent/issues/97).

#### `system` records

A `system` record adds `subtype`, `isMeta` (false on every builder, cc:483998, and on 318 of 318
observed), `level`, `content` and subtype fields. Observed subtypes: `turn_duration` (`durationMs`,
`messageCount`, `pendingBackgroundAgentCount`, no `content`), `away_summary` (`content`, a
model-written recap), `local_command` (`content`, `level:"info"`, optional
`commandRun{command, args}`, `usageReport`), `bridge_status` (`content`, `url`), `informational`
(`content`, `level:"notice"`). The builders at cc:483998 add `compact_boundary`
(`content:"Conversation compacted"`,
`compactMetadata{trigger, preTokens, userContext, messagesSummarized, ...}`, `logicalParentUuid`),
`api_error` (`level: "error"`, `error`, `retryInMs`, `retryAttempt`, `maxRetries`, no `content`),
`memory_saved` (`writtenPaths`), `agents_killed`, `stop_hook_summary`, `permission_retry`,
`scheduled_task_fire`, `cloud_session_status`; cc:487124 adds `model_refusal_fallback` and others.
Observed on macOS with CLI 2.1.295 (2026-10-11), a `stop_hook_summary` record carries `hasOutput`,
`hookAdditionalContext`, `hookCount`, `hookErrors`, `hookInfos`, `level`, `preventedContinuation`,
`stopReason` and `toolUseID` beside the envelope. Many `subtype` literals in the bundle (`init`,
`status`, `task_*`, `hook_*`, `ui_*`) belong to the SDK stream, not the transcript.

Observed on Windows 2.1.309: `turn_duration`; `away_summary`, a recap written for a person who was
away, with `content` and the envelope; `local_command` with `commandRun` for `/rename`, `/exit`,
`/clear` and the Remote Control start and stop, the `/clear` one written in the new session's file;
`compact_boundary` with `compactMetadata`, `content`, `level` and `logicalParentUuid`;
`bridge_status` with `url`, the pairing URL; and `scheduled_task_fire` with `cron`, `prompt` and
`taskId`. `pendingBackgroundAgentCount` was on the `system` lines of the session that ran a
subagent.

Observed on Linux 2.1.310, the same subtypes. `local_command` lines (keys `commandRun, content, cwd,
entrypoint, gitBranch, isMeta, isSidechain, level, parentUuid, sessionId, slug, subtype,
timestamp, type, userType, uuid, version`) were written for `/rename`, `/exit`, `/clear` and the
Remote Control start and stop, and not for `/model`, `/compact`, `/install-github-app`, `/loop` or
`/schedule`, which left only their `user` command lines, nor for an `/exit` after a resume.
`compact_boundary` carries `compactMetadata{cumulativeDroppedTokens, durationMs, postTokens,
preCompactDiscoveredTools, preTokens, preservedMessages{allUuids, anchorUuid, headUuid, tailUuid,
uuids}, preservedSegment, trigger}` beside `content`, `level` and `logicalParentUuid`, and an
`away_summary` written for an idle gap carries the branch of the time it was computed.
`pendingBackgroundAgentCount` appeared on the `system` lines from the first backgrounded command.

#### `attachment` records

An `attachment` record adds `attachment{type, ...}` and, on most, `rendered` and `renderedRole` (the
text the model saw), and on some `renderedBesideToolResult` (observed on macOS with CLI 2.1.295,
2026-10-11). Observed `attachment.type` values: `total_tokens_reminder`, `batching_reminder_sent`,
`deferred_tools_record`, `deferred_tools_delta`, `bash_output_audience_note`, `prompt_snapshot` (the
system prompt and tool list), `environment`
(`snapshot{workingDirectory, platform, shell, osVersion, isGitRepo, isWorktree, ...}`),
`skill_listing`, `queued_command`, `remote_session_change`, `date`, `model`
(`identity{modelId, marketingName, knowledgeCutoff}`), `agent_listing_delta`,
`mcp_instructions_delta`, `auto_mode`, `session_context` (`context{userEmail, gitStatus}`),
`credential_org` (`organizationUuid`), `edited_text_file` (`filename`, `snippet`), `instructions`
(`files`), `silent_turn_reminder`, `command_permissions`, `plan_mode`, `plan_mode_exit`,
`plan_mode_reentry`, `hook_system_message` (`hookName`, `hookEvent`, `content`), `thinking_drop`,
`read_truncation_notice`. `queued_command` carries `prompt`, `origin{kind}`, `commandMode`,
`source_uuid`, `delivery_id`, `timestamp`: a prompt that arrived while a turn was running.

Key sets on Windows 2.1.309, where the shape tool gave them (none was read for a value):

| `attachment.type` | Keys |
| --- | --- |
| `auto_mode` | `autoModeConsentFlow, bashFirst, bashFirstSteer, bypass, finishExposedWork, steerOnly`: the auto-mode configuration of the turn, not a decision ([issue 98](https://github.com/seanthegeek/doubleagent/issues/98)) |
| `auto_mode_exit` | new type: written when the Shift+Tab cycle left `auto` |
| `plan_mode` | `isSubAgent, planExists, planFilePath, reminderType, type` |
| `plan_mode_exit` | `planExists, planFilePath, type`; also written when the cycle passed through plan mode |
| `plan_file_reference`, `file` | new types: the plan and the files a `/compact` carried over |
| `environment` | `snapshot` in the CLI, `changes` and `snapshot` in the VS Code extension; `snapshot` holds `additionalWorkingDirectories, isGitRepo, isWorktree, osVersion, platform, scratchpadDirectory, shell, workingDirectory` |
| `model` | `identity, text`; a second one after a `/model` switch |
| `session_context` | `context` |
| `credential_org` | `organizationUuid` |
| `prompt_snapshot` | `cliPrefix, contextRendering, echoWireToolInputs, inlineTools, keptReminders, reminderFold, systemPrompt, systemTurns, toolChangeHeader, tools` |
| `deferred_tools_delta` | `addedLines, addedNames, failedMcpServers, pendingMcpServers, readdedNames, removedNames, surfacedDefinitions, surfacedNames, wireHiddenNames`, plus `needsAuthMcpServers` in the extension; it lists the connector servers |
| `skill_listing` | `content, digests, isInitial, names, skillCount` |
| `agent_listing_delta` | `addedLines, addedTypes, builtInPluginTypes, builtInTypes, isInitial, removedTypes, showConcurrencyNote` |
| `remote_session_change` | `commit, managedCommit, managedPr, pr, url, sendUserFileHint`: a link to a claude.ai session or a pull request when there is one; present in plain local sessions |
| `session_cron_carry` | `tasks, type`; by its name, the scheduled tasks carried into a new session |
| `task_reminder` | `content, itemCount, type` |
| `command_permissions` | `allowedTools, type`, on the `/schedule` skill's turn |

Also written there: `total_tokens_reminder`, `batching_reminder_sent`, `bash_output_audience_note`,
`date`, `mcp_instructions_delta` and `deferred_tools_record`. `queued_command` and
`edited_text_file` were not written: a prompt typed during a turn became an ordinary `user` line
([User-record kinds](#user-record-kinds)).

On Linux 2.1.310 the key sets above held, `plan_mode` with `planExists` false when the plan file
was not yet written, and the round added:

| `attachment.type` | Keys |
| --- | --- |
| `plan_mode_reentry` | `planFilePath, type`, at the next plan-mode turn after a plan was written ([issue 98](https://github.com/seanthegeek/doubleagent/issues/98)) |
| `compact_file_reference` | `displayPath, filename`, after a `/compact` |
| `plan_file_reference` | `planContent, planFilePath`: the plan re-injected after a `/compact` |
| `file` | `content{file, type}, displayPath, filename`: an edited file re-injected after a `/compact` |
| `deferred_tools_delta` | `needsAuthMcpServers` in the VS Code extension, as on Windows |
| `session_context` | in a subagent file, `context` with `userEmail` only (no `gitStatus`) |

A turn in `auto` mode that ran only a `Read` wrote no `auto_mode`, `bash_output_audience_note` or
`batching_reminder_sent`, which on Windows came with a shell call; a later `auto` session that used
an MCP tool wrote `auto_mode`. No `auto_mode_exit` was written when the Shift+Tab cycle left
`auto`.

#### `queue-operation` records

A `queue-operation` record has `operation` (`enqueue`, `dequeue`, `remove`), `timestamp`,
`sessionId`, and on `enqueue` and `remove` the queued `content`; optional `commandUuid`,
`deliveryId`, `reason` (observed). On Windows 2.1.309 the keys were `content, operation, sessionId,
timestamp, type`: an `enqueue` and `dequeue` pair for a prompt typed while a turn ran, for the
Remote Control prompt, for a `/loop` firing and for a subagent's completion notice. On Linux
2.1.310 the CLI's lines had the same keys, and the VS Code extension's session wrote
`operation, sessionId, timestamp, type`, with no `content`.

#### Completeness and streaming

One API response becomes one `assistant` record per content block: all 9,911 observed `assistant`
records hold exactly one block, consecutive records share `message.id` and `requestId`, and only the
last carries a non-null `stop_reason` (observed; `apiBlockIndex` numbers them). There are no
streaming deltas to reassemble. The transcript is complete except for persisted tool output
([Persisted output](#persisted-output)), pasted text in history ([Other stores](#other-stores)),
and file backups (`file-history/`).

#### Message content, tool calls and results

`message.content` blocks (observed counts):

| Record | Block `type` | Fields |
| --- | --- | --- |
| `assistant` | `text` (886) | `text` |
| `assistant` | `thinking` (3,525) | `thinking`, `signature`; `thinking` is `""` in 3,165, text present in 360 |
| `assistant` | `tool_use` (5,513) | `id` (`toolu_...`), `name`, `input` (object), `caller{type:"direct"}` |
| `assistant` | `redacted_thinking`, `server_tool_use`, others | not observed |
| `user` | string content (474) | the prompt or injected text |
| `user` | `text` (35) | `text` |
| `user` | `tool_result` (5,512) | `tool_use_id`, `content` (string in 5,327; list of `{type:"text", text}` in 167 or `{type:"tool_reference", tool_name}` in 18), `is_error` (true 183, false 4,632, absent 749) |
| `user` | `image` | not observed; `text_of` renders it `[image]` |

#### Tool call join

`tool_use.id` = `tool_result.tool_use_id` (observed). Each result's `user` record also carries
`sourceToolAssistantUUID`, the `uuid` of the `assistant` record holding the call, and
`toolUseResult`, the tool's structured result: for Bash `stdout`, `stderr`, `interrupted`,
`isImage`, `noOutputExpected`, optional `returnCodeInterpretation`, `persistedOutputPath`,
`persistedOutputSize`, `bashEditDiff`; for file tools `filePath`,
`file{filePath, content, numLines, startLine, totalLines}`, `oldString`, `newString`,
`structuredPatch`, `originalFile`, `userModified`; for web tools `url`, `code`, `codeText`, `bytes`,
`result`, `durationMs`, `query`, `results`; for Agent `agentId`, `status`, `prompt`,
`resolvedModel`, `outputFile`. Windows 2.1.309 adds: for `PowerShell` the Bash keys; for Read
`file` and `type` (`text`); for Write `type` `create`; for Agent `canContinueAgent`,
`canReadOutputFile`, `description`, `isAsync`; for ToolSearch `content`, `matches`, `query`,
`total_deferred_tools`, `failed_mcp_servers`; for Grep `content`, `filenames`, `mode`, `numFiles`,
`numLines`, `totalLines`; for CronCreate and CronDelete `annotations`, `durable`, `humanSchedule`,
`id`, `nextFireAt`, `recurring`; for AskUserQuestion `answers`, keyed by the question; and
`backgroundTaskId` when Claude Code moved a long command to the background, whose output then went
to the temp root's `tasks/<id>.output` ([Scratch directories](#scratch-directories)) and whose end
came back as a `task-notification` turn. Linux 2.1.310 showed the same keys, Agent adding
`resolvedModel` with the session's model, Bash `{interrupted, isImage, noOutputExpected, stderr,
stdout, type}`, and ToolSearch, which the model called to load a deferred tool (an MCP tool, a
cron tool) before using it, `matches`, `query` and `total_deferred_tools`. On an error it is the
error string (183 observed, all with
`is_error:true`). The model-visible text is the `tool_result.content`; `toolUseResult` repeats or
extends it.

#### Wire inputs

`assistant.wireToolInputs` maps each `tool_use.id` to the input exactly as the model sent it;
`tool_use.input` is the normalised input Claude Code ran (cc:482605 attaches both; cc:481832 and
cc:482596 compare and strip them). Observed: 1,607 of 5,513 differ. For 1,498 of 1,501 differing
Bash calls the wire `command` is the stored `command` with a leading `cd <dir> && ` that the stored
input lacks, and `wireIngestContext[<id>].cwd` holds that directory; Edit adds `replace_all`,
ExitPlanMode and SendMessage add fields the model did not send.

#### Persisted output

When a result is too large, its full text goes to `<session id>/tool-results/<name>.txt` and the
`tool_result.content` holds a `<persisted-output>` stub with the path and a preview (cc:382991,
cc:474483); `toolUseResult.persistedOutputPath` names the file (37 observed) and
`persistedOutputSize` its size. On Windows 2.1.309 both keys were on the result line of a
20,000-line PowerShell listing and of a `gh` output, the files being
`<session id>/tool-results/<9 base-36 chars>.txt` (1.2 MB and 49.6 KB); the stub kept in the
transcript was about 38 KB. A 3,000-line listing the model only counted was not persisted. On Linux
2.1.310 the same two keys named `tool-results/<9 base-36 chars>.txt` for a 20,000-line `head` of a
word list and a `gh` output, and the stub was again about 37 KB.

#### Tool names

Tool names observed: `Bash`, `Read`, `Write`, `Edit`, `WebFetch`, `WebSearch`, `Agent`,
`SendMessage`, `SubagentHandback`, `ToolSearch`, `EnterPlanMode`, `ExitPlanMode`; MCP tools are
`mcp__<server>__<tool>` (cc:489602; `mcp__fs__list_directory` on Windows 2.1.309). On Windows
2.1.309 the shell tool is `PowerShell`, and `Bash`, which runs Git Bash there, was used too (by the
model for `ls` and `gh`, and by the VS Code extension's session); also seen `Read`, `Write`, `Edit`,
`Grep`, `Agent`, `ToolSearch`, `ExitPlanMode`, `AskUserQuestion`, `CronCreate` and `CronDelete`.
On Linux 2.1.310 the shell tool is `Bash`, and a question about a file the Windows model answered
with a shell `cat` was answered with `Read`; also seen `Write`, `Edit`, `Agent`, `ToolSearch`,
`ExitPlanMode`, `AskUserQuestion`, `CronCreate`, `CronDelete`, `Skill` (for `/loop` and
`/schedule`) and `mcp__fs__list_directory`. Input keys observed: `command`, `description`,
`timeout`, `run_in_background` (Bash); `file_path`, `offset`, `limit` (Read); `file_path`,
`content` (Write); `file_path`, `old_string`, `new_string` (Edit); `url`, `prompt` (WebFetch);
`query` (WebSearch); `description`, `prompt`, `subagent_type`, `model`, `isolation` (Agent).

#### User-record kinds

A `user` record is not always typed by the person:

| Signal | Meaning | Observed |
| --- | --- | --- |
| `origin.kind:"human"`, `promptSource` `typed`, `queued` or `suggestion_accepted` | a prompt the person submitted | 165 |
| `origin.kind:"human"`, `promptSource` `sdk` | a prompt typed in the VS Code extension's panel | Windows 2.1.309 |
| `turnOrigin:"scheduled"`, `promptSource:"system"`, with `scheduledTaskId` | the prompt of a `/loop` firing, after a `scheduled_task_fire` system line | Windows 2.1.309 |
| no `origin`, `parentUuid` null, first line of a subagent file | the task the parent agent gave the subagent | 80 of 80 subagent files |
| `origin.kind:"task-notification"`, content `<task-notification>...` | a background task's completion notice; `isMeta` absent in 62 of 66; on Windows 2.1.309 with `promptSource` `system` and `turnOrigin` `task_notification`, for a subagent's end and a backgrounded command's | 66 |
| `origin.kind` `peer`, `coordinator`, `auto-continuation` | messages from other sessions or the runtime; `isMeta:true` | 65 |
| `isMeta:true`, `<system-reminder>` or `<local-command-caveat>` | injected context | 87 strings, 27 blocks |
| `<command-name>`, `<command-message>`, `<local-command-stdout>` | a slash command and its output; `isMeta` absent; the 27 `<command-message>` records also carry `origin.kind:"human"` and are counted above | 38 |
| `isCompactSummary:true` | the summary that replaces history after compaction, text starting "This session is being continued from a previous conversation" (cc:482588); built through the user-message factory without `isMeta` (cc:482593, cc:482597, cc:482598); with `isVisibleInTranscriptOnly` on Windows 2.1.309 | Windows 2.1.309 |
| `tool_result` blocks | tool output | 5,512 |

A prompt typed while a turn runs is first a `queue-operation` `enqueue` with its `content`, then
either a `queued_command` attachment (delivered inside the running turn) or a later `user` record
with `promptSource:"queued"`. Observed: 11 `queued_command` attachments with `origin.kind:"human"`
whose text is in no `user` record of the file. On Windows 2.1.309 a prompt typed while a command ran
was an `enqueue` and `dequeue` pair and then an ordinary `user` line with `promptSource` `typed`,
with no `queued_command` attachment; the Remote Control prompt from the phone was the line with
`promptSource` `queued` ([Remote Control](#remote-control)). Linux 2.1.310 confirmed both forms
and the task-notification turns, one per backgrounded command ([`user` records](#user-records)).

### Joins and timestamps

- **Timestamps**: per record `timestamp`, ISO 8601 UTC with milliseconds and `Z` (observed 27,061 of
  27,061; `new Date().toISOString()` in every builder). Not monotonic in file order: in 52 of 95
  files a record is older than an earlier line, mostly by under a second (assistant blocks and
  attachments written after the fact), 19 by a minute or more. Session-state records have no
  timestamp.
- **Session id**: `sessionId` equals the file name in all session-file records (12,526 of 12,526).
  In a subagent file `sessionId` is the **parent** session's id (18,429 of 18,429) and `agentId`
  names the subagent. The snake-case `session_id` on some records equals `sessionId` in 12 session
  files and in 3 names an earlier session whose file exists while none of those records' `uuid`s are
  in it; consistent with a resumed or forked session, purpose not determined. On Windows 2.1.309
  `claude --resume` appended to the chosen session's own file under the same `sessionId` (no new
  file and no copy), while the daemon handover copied the console session's turns into the worker's
  new file, so the worker's file holds lines first written under the console's session; whether
  those copies are the records whose `session_id` names an earlier session was not determined
  (values were not compared). On Linux 2.1.310, with no daemon, `claude --resume` and
  `claude --continue` both appended to the session's own file, and their prompts to
  `history.jsonl`, under the same `sessionId`, with no `continued-in` line; each resuming process
  got its own temp-root directory under a new uuid ([Scratch directories](#scratch-directories)).
- **Daemon handover**: the console file's `continued-in` `continuedInSessionId` is the worker's
  session id, the worker's `jobs/<short>/state.json` `resumeSessionId` is the console's, and the
  console's `sessions/<pid>.json` carries the job as `parkedJobId`
  ([Session daemon records](#session-daemon-records)). Later turns, an attach through
  `claude agents` and a `--resume` all land in the worker's file. While a worker holds the last
  session, `claude --continue` is refused with
  ``Your most recent conversation is running in the background (session <uuid>). Use `claude agents` to find and attach to it, or `claude --resume` to pick another session.``
  On Linux 2.1.310 no worker held a session and `--continue` resumed the latest one in place, so
  the refusal is the daemon's behaviour, not a rule of `--continue`.
- **`/clear`**: a new session id and file in the same process; the old file is not linked to the
  new one by any record seen (its last line is a `cost-state`).
- **Project path**: `cwd` on every transcript record; can change within a session (4 of 15 session
  files had more than one) and `relocated` records it (cc:484038); the directory `<key>` is lossy
  ([Where the project path is recorded](#where-the-project-path-is-recorded)).
- **Branch**: `gitBranch` on every transcript record (never empty observed); changes within a
  session (2 files). On a detached head it is the literal string `HEAD`, never empty and never a
  commit hash (Linux 2.1.310, a `git checkout --detach` before one prompt: four of the turn's five
  envelope lines carried `HEAD`, and the fifth, an `away_summary` computed before the checkout,
  `main`).
- **Model**: `message.model` on `assistant` records (`claude-<family>-N-N` observed, `<synthetic>`
  for local errors); `requestedModel`, the model the request asked for
  (`claude 2.1.296 darwin-arm64 @198072824` `requestedModel:X.model`), equal to `message.model` on
  every 2.1.296 line observed; `model` attachment `identity.modelId`; `cost-state.modelUsage` keys.
  A `/model` switch is a `user` line `<command-name>/model</command-name>` followed by a `user`
  line with the command output, built from `@199593943`
  `var fle="Set model to ",gne=" and saved as your default for new sessions"`; observed on 2.1.296
  as
  ``<local-command-stdout>Set model to `<display name>` and saved as your default for new sessions</local-command-stdout>``.
  The parser keeps it as `command output:` and marks the change itself from `message.model`. On
  Windows 2.1.309 a `/model` switch to Sonnet saved as the default left `message.model` and
  `requestedModel` both the resolved id (`claude-sonnet-5-5`) on the following lines, the earlier
  ones staying `claude-fable-5-1`; the alias the person picked is in no transcript line, only in
  `settings.json` `model` (`sonnet`), and a second `model` attachment followed. A subagent inherited
  the session's model, and later sessions, the VS Code extension's included, started on the saved
  default. On Linux 2.1.310 the default before any switch was `claude-sonnet-5-5`, where the
  Windows cell's was `claude-fable-5-1`: the model catalog's `state.selection_source` was
  `user_setting`, so the default is account state, not a property of the build. Picking Opus with
  `/model` saved the alias `opus` to `settings.json` `model` at once, with no option to decline
  (2.1.309 asked), and left two `user` lines (the command and a `<local-command-stdout>` with
  `Set model to`); the next `assistant` lines carried `claude-opus-5-5` in both `message.model` and
  `requestedModel`, with a second `model` attachment (`identity{knowledgeCutoff, marketingName,
  modelId}, text`). A subagent again inherited the session's model.
- **Subagents**: the parent's `Agent` `tool_use.id` equals the subagent's `.meta.json` `toolUseId`,
  and the parent's `toolUseResult.agentId` equals the file's agent id (76 of 76 non-fork subagents).
  Forked agents (`agentType:"fork"`, 4) have a `toolUseId` that is not in the parent transcript.
  Confirmed on Windows 2.1.309 and Linux 2.1.310, where every subagent line carries `agentId`.
- **Tool results**: `sourceToolAssistantUUID` on the result line is the `uuid` of the `assistant`
  line with the call (observed on Windows 2.1.309 as on WSL2). A backgrounded command's result
  carries `toolUseResult.backgroundTaskId`; its output went to a temp-root `tasks/<id>.output` file
  and its end came back as a `task-notification` turn (whether the id is the file's name was not
  compared).
- **Turn**: `promptId` groups a prompt's records; `turnPosition{ promptIndex, turnIndex}` on some
  `user` records.

### Other stores

`sessions/<pid>.json` and the `.meta.json` sidecars: [Transcript stores](#transcript-stores). No
SQLite store holds transcript content. `.claude.json` `projects` keys are project paths
([Where the project path is recorded](#where-the-project-path-is-recorded)).

#### `history.jsonl`

`.claude/history.jsonl` (observed 162 of 162):
`{display, pastedContents, timestamp, project, sessionId}`, `timestamp` epoch **milliseconds**
(integer), `project` the cwd. Written by `addEntry` (cc:479374) and read with the schema at
cc:479372. `pastedContents` maps a paste number to `{id, type, content, mediaType, filename}` when
the paste is at most 1,024 characters, else to `{id, type, contentHash, mediaType, filename}` with
the text stored in `paste-cache/` under its hash (cc:479369 `z8=1024`, cc:479374
`registerPastedTextForRecall`, cc:479360 `paste-cache`); `display` holds the `[Pasted text #N]`
placeholder. Every `pastedContents` on the WSL2 install was empty. On Windows 2.1.309 a pasted
text of about 40 lines (shown as `[Pasted text #1 +N lines]`) gave `pastedContents`
`{"1": {contentHash, id, type}}`, with no `content`, `mediaType` or `filename`, and the text went to
`paste-cache/<contentHash>.txt` (6,604 B); the transcript's `user` line holds the paste inline, so
the cache is a second copy while the transcript exists and the only one after. `paste-cache/` is
collected since this round ([Exclusions](#exclusions)); what the history outlives is under
[What survives a delete](#what-survives-a-delete).

On Linux 2.1.310 both forms were written to one file. A short multi-line paste (shown as
`[Pasted text #1 +N lines]`) gave `pastedContents` `{"1": {content, id, type}}`, the text itself
in `content` and no `paste-cache/` file, so the history line holds the paste and outlives the
transcript with it; a long one (300 lines of a manual page) gave `{"2": {contentHash, id, type}}`
and `paste-cache/<contentHash>.txt`. The key is the paste's number within the session, not always
`1`.

On Windows 2.1.309 every typed prompt and slash command was a line (`/model`, `/compact`,
`/rename`, `/exit`, `/install-github-app`), a mistyped subcommand (`claude ls`) became a prompt
and a line, a session with no prompt left one line, and a refused or trust-prompt start left none.
A prompt sent through a console attached with `claude agents` was not recorded, so the transcript
is its only record. On Linux 2.1.310 the same held except that `/model` was not a line, while
`/compact`, `/rename`, `/exit`, `/clear` and the prompts after `--resume` and `--continue` were; a
prompt sent from the VS Code extension's panel was not a line either, and the retention sweep left
the line of the session whose transcript it deleted.

#### File-history records

`file-history-snapshot` and `file-history-delta` records name the files backed up before each edit
(`snapshot.trackedFileBackups` keyed by path,
`backup{backupFileName, backupTime, version, realParentDir}`); the bytes are in
`.claude/file-history/<session id>/`. The paths in `trackedFileBackups` are files the agent edited,
which no other record lists in one place.

On Windows 2.1.309 a `file-history-delta` line has `backup, messageId, snapshotMessageId, timestamp,
trackingPath, type`. The backups are `file-history/<session id>/<16 hex>@v<n>`, one `<16 hex>` per
tracked path and a new `@v<n>` per version: the first edit wrote `@v1`, the pre-edit copy, whose
modification time was the source file's own; a later edit wrote `@v2`; and the next prompt after an
edit wrote the post-edit copy as `@v3`, so a snapshot is taken at the next prompt too. The plan
file the `Write` tool wrote in plan mode was tracked the same way. The empty directory is created
at the session's start.

On Linux 2.1.310 the directory was created at the first edit, and the pre-edit `@v1` copy's
modification time was the time of the backup, not the source file's, so whether a backup keeps
the source's time differs between the platforms. A new `@v<n>` was written at every prompt while a
file was tracked, a prompt that edited nothing included, while the transcript held one
`file-history-delta` line per tracked file. The plan file written in plan mode was tracked from the
next prompt, its first copy `@v2` with no `@v1`, since the `Write` that created it had no earlier
content.

#### Permission configuration

- Key names come from the 2.1.296 binary and were observed by name on the 2.1.296 install, values
  never read ([issue 93](https://github.com/seanthegeek/doubleagent/issues/93)).
- Settings files: `<config home>/settings.json` and `<config home>/settings.local.json` for the
  user, and `<project>/.claude/settings.json` (shared, committed) and
  `<project>/.claude/settings.local.json` (personal, gitignored) per project (`@188743274`
  `case"projectSettings":return Se(".claude","settings.json");case"localSettings":return Se(".claude","settings.local.json")`;
  with `CLAUDE_CONFIG_DIR` set both the global config and the user settings move into it,
  `@212229478`
  `globalConfig:it(e||zt(),".claude.json"),userSettings:it(e||it(zt(),".claude"),"settings.json")`).
- Their `permissions` object, `@188532304`
  `function ia(e){return u({allow:A(Gi()).optional().describe("List of permission rules for allowed operations"),deny:A(Fo()).optional()...,ask:A(Fo()).optional()...,defaultMode:pa(rh,U([...CH,...Ho(e)])).optional()...,disableBypassPermissionsMode:U(["disable"]).optional()...,blockReadsOutsideWorkingDirectories:H().optional()...,additionalDirectories:A(o()).optional()`,
  holds `allow`, `deny` and `ask` (rule strings, a tool name with an optional argument pattern in
  parentheses, such as `Bash(npm test:*)`), `defaultMode` (a mode name of the `permission-mode` row
  in [Record schema](#record-schema)),
  `disableBypassPermissionsMode` (only `"disable"`; also a managed-settings key, `@188373224`
  `{path:["permissions","disableBypassPermissionsMode"],restrictive:"disable"}`),
  `blockReadsOutsideWorkingDirectories` (boolean) and `additionalDirectories` (paths outside the
  working directory the agent may use). "Always allow" answers to a prompt are persisted into these
  lists and a mode chosen to keep into `defaultMode` (`@191956974`
  `permissions:{defaultMode:e.mode}`). The same files hold keys that can carry credentials, which
  the parser never reads ([Secrets](#secrets)).
- In `~/.claude.json` (the global config, a credential file, [Credentials](#credentials)) each
  `projects.<path>` object starts from `@189922165`
  `var bue={allowedTools:[],mcpContextUris:[],mcpServers:{},enabledMcpjsonServers:[],disabledMcpjsonServers:[],hasTrustDialogAccepted:!1,hasClaudeMdExternalIncludesApproved:!1,`:
  `allowedTools` (tools allowed for that project), `hasTrustDialogAccepted` (the person accepted the
  folder trust prompt), `hasClaudeMdExternalIncludesApproved` (the person approved `CLAUDE.md`
  imports from outside the project), `enabledMcpjsonServers` and `disabledMcpjsonServers` (approval
  of the project's `.mcp.json` servers) and `mcpServers` (project-scoped server definitions, which
  can carry headers). The parser reads the rows of [Permission rows](#permission-rows); the MCP
  lists and definitions are not read.
- Observed on Windows 2.1.309: the allow-always answer, worded "Yes, and don't ask again for :
  python calc.py 1 1" (the prefix slot was empty, so the grant was the exact command), wrote the
  project's `.claude/settings.local.json` with `permissions.allow` holding one rule,
  `PowerShell(python calc.py 1 1)`, the rule form naming the Windows shell tool where the Linux one
  names `Bash(...)`. It did not write the user `settings.local.json` or
  `projects.<path>.allowedTools`, which stayed empty. Its next use is recorded as
  `source` `user_permanent` ([Permission decisions](#permission-decisions)). No mode was kept as a
  default in the round, so `defaultMode` was not written; the `/model` default went to the user
  `settings.json` `model` ([Files that hold evidence](#files-that-hold-evidence)).
- Observed on Linux 2.1.310: the allow-always option offered a wildcard prefix rule, worded
  "Always allow python3 *", for the command `python3 calc.py 1 1`, and wrote the project's
  `.claude/settings.local.json` with `permissions.allow` holding one 15-character rule, the length
  of `Bash(python3 *)` (the value was not read). It did not write the user `settings.local.json`,
  the user `settings.json` or `projects.<path>.allowedTools`, and the answer's own result line was
  recorded as `source` `user_permanent` ([Permission decisions](#permission-decisions)). Again no
  mode was kept as a default.

#### `.claude.json`

The keys seen on Windows 2.1.309, by name and type (the round read no value). After the installer
(558 B): `autoUpdates`, `autoUpdatesProtectedForNative`, `changelogLastFetched`, `firstStartTime`,
`firstStartVersion`, `hasResetAutoModeOptInForDefaultOffer`, `installMethod` (`native`),
`machineID` (64 hex), `migrationVersion`, `opusProMigrationComplete`, `seenNotifications`,
`sonnet1m45MigrationComplete`, `userID` (64 hex). After the sign-in (63,377 B): `oauthAccount`
([Secrets](#secrets)), `projects`, `githubRepoPaths`
([Where the project path is recorded](#where-the-project-path-is-recorded)),
`claudeAiMcpEverConnected` (one entry), `pluginUsage.<plugin>@builtin{lastUsedAt, usageCount,
lastUsedNumStartups}`, `cachedExperimentData`, `cachedGrowthBookFeatures` (about 50 KB of
feature-flag cache), `clientDataCacheSlots.bi1-<16 hex>{at, data, entrypoint, model, org}` (the
default model and the surface, `cli` or `claude-vscode`, before any prompt), `numStartups`,
`hasCompletedOnboarding` and `officialMarketplaceAutoInstalled`. Later starts added `agentLastUsed`,
`announcementImpressions`, `cachedArtifactRoster{accountUuid, capabilities, fetchedAt,
organizationUuid, version}`, `fullscreenUpsellSeenCount`, `hasOpenedAgentsView`, `lastPlanModeUse`,
`remoteControlUpsellSeenCount`, `tipLifetimeShownCounts`, `tipsHistory`, the Remote Control keys of
[Remote Control](#remote-control) and `skillUsage.<skill>{lastUsedAt, usageCount}` (`loop` and
`schedule` after those skills ran).

Each `projects.<path>` object had, beside the keys of
[Permission configuration](#permission-configuration), `hasClaudeMdExternalIncludesWarningShown`,
`hasUnseenTeamArtifacts`, `lastGracefulShutdown`, `lastVersionBase`, an `mcpServers` entry per
local-scope MCP server ([MCP state](#mcp-state)), and after the first turn the last session's
metrics: `lastAPIDuration`, `lastAPIDurationWithoutRetries`, `lastCost`, `lastDuration`,
`lastLinesAdded`, `lastLinesRemoved`, `lastModelUsage`, `lastSessionId`, `lastSessionMetrics`,
`lastStartTime`, `lastToolDuration`, `lastTotalCacheCreationInputTokens`,
`lastTotalCacheReadInputTokens`, `lastTotalInputTokens`, `lastTotalOutputTokens` and
`lastTotalWebSearchRequests`. The file is rewritten at every start and exit, with a dated copy in
`backups/` ([Files that hold evidence](#files-that-hold-evidence)), and keeps a removed project's
entry ([What survives a delete](#what-survives-a-delete)).

On Linux 2.1.310 the installer wrote 517 B with twelve keys, the Windows set less
`changelogLastFetched`, which the first launch added. After the sign-in the file was 65,833 B with
43 top-level keys, all within the Windows set; `oauthAccount` had 20 keys
([Secrets](#secrets)), `cachedGrowthBookFeatures` was about 60 KB, `cachedExperimentData` held 15
`tengu_*` experiments, `pluginUsage` four `@builtin` plugins, and `clientDataCacheSlots`
`data{cedar_basin, cedar_lagoon{claude-fable, claude-mythos}}`; also present were
`passesEligibilityCache.<uuid>`, `groveConfigCache.<uuid>`, `penguinModeOrgEnabled` and
`hasSeenAutoDefaultNotice`. Later starts added `apiCreditLinkStatusCache`, `promptQueueUseCount`,
`feedbackSurveyState{lastShownTime}`, `tipsHistoryByCommand.<command>{numStartups, tipId}`,
`tipLifetimeShownCounts.<tip>` (14 tips, among them `install-github-app`, `install-slack-app` and
`prompt-queue`) and `githubWebConnectionStatusCache`
([Source-host integration](#source-host-integration)), 55 top-level keys by the end. A project
entry's metrics added `lastFpsAverage`, `lastFpsLow1Pct` and, in `lastSessionMetrics`,
`frame_duration_ms_{avg,count,max,min,p50,p95,p99}`. The file was also rewritten, with a backup,
in a session left idle overnight ([Files that hold evidence](#files-that-hold-evidence)).

#### Session daemon records

The files are listed under [Session daemon files](#session-daemon-files). Key sets on Windows
2.1.309:

- `daemon.lock`: `jsonPath, launchTarget, logPath, origin, pid, procStartFt, processWrapper,
  spawnedBy{cwd, label, pid}, startedAt, version`. `daemon.status.json`: `supervisorPid,
  supervisorProcStart, workers{}, writtenAt`.
- `daemon/roster.json`: `proto, supervisorPid, updatedAt, workers{<short>: {attempt, cliVersion,
  cwd, decModes, dispatch, firedInteractiveMarks, pid, procStart, ptyAuth, ptySock,
  rendezvousSock, rvAuth, sessionId, startedAt}}`, where `dispatch` holds `agent`, `cols`,
  `createdAt`, `cwd`, `env{CLAUDE_BG_ISOLATION}`, `isolation`, `launch{args or flagArgs, fork,
  mode, restoresTranscript, sessionId}`, `nonce`, `proto`, `respawnFlags`, `rows`, `seed{intent}`,
  `sessionId`, `short` and `source`; `ptyAuth` and `rvAuth` are 32-hex tokens. On Linux 2.1.310,
  with no worker, `proto, supervisorPid, updatedAt, workers{}`.
- `daemon/attach-journal/<uuid>.json`: `attachCold, attachMs, attempt, gestureId,
  interactiveReached, marksExpected, msgsInJsonl, msgsLoaded, msgsRenderedAtFirstPaint, pid,
  procStart, startedAtEpochMs, surface, via`, one per attach, removed when the console exits.
- `jobs/<short>/state.json`: `backend, bgIsolation, children, cliVersion, createdAt, cwd,
  daemonShort, detail, firstTerminalAt, inFlight{drainableMonitors, kinds, queued, tasks}, intent,
  interactiveLineage, lastTerminalAt, linkScanOffset, linkScanPath, name, nameSource, needs,
  output{result}, providerEnv, respawnFlags, resumeSessionId, sessionId, state, template, tempo,
  tokens, updatedAt`; `name` follows `/rename`, and `resumeSessionId` names the console session the
  job took over. `jobs/<short>/timeline.jsonl` lines are `{at, detail, state, text}`.
- `jobs/.draft-<8 hex>`: `{collapsed, q, ts}`.
- `sessions/<pid>.json` of the console gained `parkedJobId`, and each worker's has `jobId` and a
  two-character `kind` in place of `interactive`; the idle spare worker's has `spare` (removed the
  moment a prompt was sent), and one had `agent`. After `/rename` the worker's `name` changed and a
  `formerNames` list of objects appeared.

The handover itself is in the transcripts: 36 seconds after the start, the console's file got a
`continued-in` line and a closing `cost-state`, and the worker's new file started with an
`agent-name` and an `ai-title` line, then received the console's turns and every later one, its
lines carrying `sessionKind` `bg` ([Transcript envelope](#transcript-envelope)). The request
capture lines are per process and were not copied. What triggered the handover is not known: the
only actions before it were one prompt and the Shift+Tab mode cycle. The console's file was still
rewritten at its exit, with the same turns.

#### MCP state

On Windows 2.1.309 `claude mcp add --scope local` put the server under
`.claude.json` `projects.<path>.mcpServers.<name>{args, command, env, type}`, not in the top-level
`mcpServers`; the first start that used it wrote `state/mcp-discover-verdicts.json`
(`{"stdio:<hex>": {modernProtocolVersion, observedAt}}`, one key per stdio server probed), and each
server start wrote a log file in the [CLI cache directory](#cli-cache-directory). Its tool calls are
`mcp__<server>__<tool>` ([Tool names](#tool-names)). Whether `claude mcp add` wrote
`.claude.json` before the session started was not separated there. The account's claude.ai
connectors need no local configuration and log on every start.

On Linux 2.1.310 `claude mcp add --scope local fs -- npx -y @modelcontextprotocol/server-filesystem
<project>` wrote `.claude.json` itself, before any session, and said so:
`Added stdio MCP server fs with command: ... to local config` and
`File modified: /home/sean/.claude.json [project: /home/sean/lab/proj]`. The server went to
`projects.<path>.mcpServers.fs{args, command, env, type}` (`command` `npx`, `type` `stdio`, an
empty `env{}`), with no top-level `mcpServers` and no `.mcp.json`. In the next session the model
loaded the server's tool with `ToolSearch` and called `mcp__fs__list_directory`, both allowed by
configuration in `auto` mode, the result line carrying `mcpMeta`. `state/mcp-discover-verdicts.json`
(101 B, mode 0600) had been written at the second start, before any local server existed, with one
key of the form `mcpsrv_<24 chars>` (`{modernProtocolVersion, observedAt}`), the claude.ai
connectors' id form, and gained no key for the stdio server.

#### Scheduled tasks

On Windows 2.1.309 `/loop 1m <prompt>` is run through tools: a `CronCreate` call starts it and a
`CronDelete` call stops it (their result keys are under [Tool call join](#tool-call-join)), each
firing is a `system` `scheduled_task_fire` line followed by a `user` prompt with `turnOrigin`
`scheduled` ([User-record kinds](#user-record-kinds)), and the project gets
`.claude/scheduled_tasks.lock` and a rewritten `.git/info/exclude`
([Project-local files](#project-local-files)); `.claude.json` counts the skill in `skillUsage`.
`/schedule`, for cloud routines, ran as a skill that asked with `AskUserQuestion` and, cancelled,
created nothing locally: no `routines/` directory in the project or the config home, no `jobs/` or
`systemd/` entry.

On Linux 2.1.310 the record set was the same: `CronCreate` and `CronDelete` calls (both loaded with
`ToolSearch`), two `scheduled_task_fire` lines and two `user` prompts with `turnOrigin`
`scheduled`, `promptSource` `system` and the scheduled-fire keys, `Skill` tool calls for both
commands, no `local_command` line, and `skillUsage.loop` and `skillUsage.schedule` in
`.claude.json`. The project's `.claude/scheduled_tasks.lock` was written at the loop's start and
left behind after the stop ([Project-local files](#project-local-files)). The cancelled
`/schedule` again created no routine, and its `AskUserQuestion` left a prompt line with
`promptSource` `suggestion_accepted`.

#### Source-host integration

Observed on Windows 2.1.309, with the GitHub CLI `gh` installed and no GitHub sign-in at first:

- `githubRepoPaths` in `.claude.json` maps every GitHub repository the CLI has seen as a
  checkout's `origin` remote to its local checkouts, filled at the first launch from the git
  remote alone ([Where the project path is recorded](#where-the-project-path-is-recorded)); it is
  the list of repositories the host has worked on, not of what an account may reach.
- `/install-github-app` asked for `gh auth login` first, then installed the Claude GitHub app; the
  repositories the app may reach are chosen on GitHub's website (all by default) and live on
  GitHub. Claude Code's own state recorded nothing of it: no `gh-pr-status-cache.json`, no new
  `.claude.json` key, no new file under `~/.claude`; the transcript gained the command's lines.
- The connected account is in `gh`'s own store, `%APPDATA%\GitHub CLI\config.yml` and
  `hosts.yml` (which names the user), with the token in the Windows Credential Manager. These are
  `gh`'s files, not in the catalog; a responder reads `hosts.yml` for the account.
- A read-only question about the repository's pull requests ran `gh` through the `Bash` tool; the
  only trace beyond the transcript was one persisted `gh` output in `tool-results/`
  ([Persisted output](#persisted-output)). No `pr-link` line was written, since no pull request was
  made, and no repository-bound remote conversation is stored locally.

Observed on Linux 2.1.310, with `gh` 2.46.0 installed and signed in as a throwaway account before
Claude Code was asked:

- `gh auth login` (the browser flow) wrote only `gh`'s own store: `~/.config/gh/config.yml`
  (902 B, mode 0600) and `hosts.yml` (94 B, mode 0600), which names the account but holds no token;
  `gh auth status` reported the token in the keyring, and the GNOME keyring file (the Ubuntu
  desktop's encrypted password store) `~/.local/share/keyrings/login.keyring` (719 B, mode 0600)
  was rewritten in the same second. It
  also created `~/.gitconfig` with `gh`'s git credential helper lines; the scopes were `gist`,
  `read:org`, `repo` and `workflow`. Nothing under a Claude Code root changed. A headless host,
  with no keyring, would have the token in `hosts.yml` (not observed).
- `/install-github-app` found the app already installed on the account and said so. Unlike
  2.1.309, `.claude.json` then gained `githubWebConnectionStatusCache{accountUuid, orgUuid, status}`
  with `status` `connected`, naming the connected claude.ai account and organisation, beside
  `tipsHistoryByCommand.install-github-app`. There was still no `gh-pr-status-cache.json` and no
  `pr-link` line, the command was two `user` lines, and the repository list is still only
  `githubRepoPaths`.
- The read-only pull-request question ran three `Bash` calls of `gh`, allowed by the classifier in
  `auto` mode, one output persisted to `tool-results/` (49.6 KB); the first shell call also
  snapshotted the working tree under the temp root's `bash-edit-diff/`
  ([Scratch directories](#scratch-directories)).

#### Remote Control

Remote Control lets another device (claude.ai or the mobile app) drive a local Claude Code process
through a bridge, the relay through Anthropic's servers that carries the other device's prompts to
the local process and its output back. The evidence is the 2.1.295 Linux binary of
[Source and evidence](#source-and-evidence), the Ubuntu lab install of 2026-10-11, the Windows
2.1.309 round and the Linux 2.1.310 round ([Observed](#observed)).

- **Live at collection time.** `.claude/sessions/<pid>.json` is the per-process registry (collector
  [issue 76](https://github.com/seanthegeek/doubleagent/issues/76)). Observed keys on Linux 2.1.295:
  `pid`, `sessionId`, `cwd`, `startedAt`, `procStart`, `version`, `peerProtocol`, `peerFeatures`,
  `kind`, `entrypoint`, `hostSessionId`, `pidDomain`, `messagingSocketPath`, `name`, `nameSource`,
  `nameSince`, `status`, `updatedAt`, `statusUpdatedAt`, with a sibling `<pid>.<sha256>.key`;
  evidence `claude 2.1.295 linux-arm64 @209019746`
  `pid:process.pid,sessionId:V(),cwd:we(),startedAt:Date.now(),procStart:await Fl(process.pid)`,
  then `@209020296`
  `peerProtocol:Akr,peerFeatures:HU(),kind:s,entrypoint:a.CLAUDE_CODE_ENTRYPOINT,hostSessionId:Okr(),pidDomain:await BT()`.
  `kind` was `interactive`, `status` `idle`, and `hostSessionId` the Claude Desktop `local_<uuid>`;
  `messagingSocketPath` is the local peer socket, not the bridge. On macOS (2026-10-11, CLI 2.1.295
  launched from the Code tab) the 612-byte file had the same key set, with `entrypoint`
  `claude-desktop`, `kind` `interactive`, `status` `idle`, `nameSource` `user`, `pidDomain` `darwin`
  and `hostSessionId` a 42-character `local_<uuid>`; the sibling `.key` is in
  [Credentials](#credentials). On the WSL2 install (2.1.286 to 2.1.289) some files lacked `name`
  and `status`. While Remote Control is attached the CLI patches `bridgeSessionId` into the same
  file
  (`@209023561` `async function mHn(e,n){await bn({bridgeSessionId:e},n)}`, the helper that also
  patches `messagingSocketPath`), and the session picker pairs local sessions with the bridge by it
  (`@208451566` `if(s.bridgeSessionId!==void 0)`). So a registry file with `bridgeSessionId` set at
  collection time means that process was under Remote Control when the collector ran. A record can
  outlive a crashed process until the housekeeping sweep (`.last-cleanup`), or, as the vendor's
  table under [What survives a delete](#what-survives-a-delete) puts it, until the next launch
  clears a crash's leftovers (a 2.1.310 `--debug` log shows
  `[sessionRegistry] sweep permitted (domain linux:<hex>:pid:[...])` at the start), so pair the
  claim with the EDR's process list. On Linux 2.1.310 a session's registry file was 560 or 561 B
  with 18 keys of the set above (`kind` `interactive`, `entrypoint` `cli`, `name` derived as
  `proj-<2 hex>`, three `peerFeatures`), rewritten at status changes and removed at the exit.
- **Transcript lines.** `turnOrigin` takes one of `@215584535`
  `var zLt=["human","sdk","scheduled","task_notification","auto_continuation","peer","host_synthetic","system","unknown"]`;
  no value names Remote Control, and a `remote-restart-auto-resume` wake-up maps to
  `auto_continuation` (`@215585139`
  `case"remote-restart-auto-resume":case"ci-monitor":return"auto_continuation"`). The CLI derives
  `{kind:"bridge"}` for a human prompt sent over the bridge (`@214818778`
  `function Ioe(e,n){switch(e.kind){case"human":return n===!0?{kind:"bridge"}:{kind:"composer"}`),
  but that value was seen only feeding the hook path; the observed transcript lines carry
  `origin:{kind:"human"}`. On Windows 2.1.309 the prompt sent from the phone was a `user` line with
  `origin.kind` `human`, `turnOrigin` `human` and `promptSource` `queued`, with
  `queueSkipSlashCommands` and a `queue-operation` pair, between `bridge-session` lines: the bridge
  prompt is told apart by `queued` and the surrounding `bridge-session` lines, not by its origin.
- **Windows 2.1.309.** `/remote-control` in an open session, paired with the Claude iPhone app,
  wrote three `bridge-session` lines (the last, at the disconnect, with `bridgeSessionId` null), a
  `system` `bridge_status` line with `url`, `local_command` lines for the start and stop, and
  `bridgeSessionId` in the process's `sessions/<pid>.json` (null after the disconnect). Starting it
  added `agentPushNotifEnabled` to `settings.json`, the phone push-notification opt-in, and
  `.claude.json` later held `hasRemoteEnvironment`, `hasUsedRemoteControl`,
  `remoteControlReadyPushCount`, `remoteControlReadyPushKey`, `remoteControlSurfacesSeen` (one
  string), `remoteDialogSeen`, `replBridgePlaceholders`, `seenNotifications.rc-active-badge` and
  two push-notification counters. The tool call the phone asked for ran with no approval prompt,
  the session being in `auto` mode.
- **Linux 2.1.310.** The same records, paired with the Claude phone app: three `bridge-session`
  lines, none with a null `bridgeSessionId`, a `bridge_status` line with `url`, `local_command`
  lines for the start and stop, a `queue-operation` pair, and the phone's prompt as the round's
  only `user` line with `promptSource` `queued` (with `origin.kind` and `turnOrigin` `human` and
  `queueSkipSlashCommands`); the turn's `assistant` lines carried `wireIngestContext`. The registry
  file grew to 584 B with `bridgeSessionId`, which was set to null at the disconnect and kept, not
  removed. `settings.json` gained `agentPushNotifEnabled`, and `.claude.json`
  `hasUsedRemoteControl`, `remoteControlSurfacesSeen` (`mobile`), `remoteDialogSeen`,
  `replBridgePlaceholders{}` and `seenNotifications.rc-active-badge`. After the disconnect no local
  file said whether the session was still visible on claude.ai: the `bridge-session` lines, the
  nulled registry key and `hasUsedRemoteControl` are the only marks.
- **Historical.** `~/.claude.json` keys `hasUsedRemoteControl`, `remoteControlUpsellSeenCount`,
  `remoteControlSurfacesSeen` and `remoteDialogSeen` (`@224457799`
  `return!e.hasUsedRemoteControl&&!ore()&&(e.remoteControlUpsellSeenCount??0)<c`, `@224460306`
  `remoteControlSurfacesSeen:[...t,n]`, `@224188242` in the global-config key list
  `"remoteDialogSeen"`; observed on a macOS install that has used the feature) say the account used
  Remote Control on this host at some time.
- **Not Remote Control.** `.session_ingress_token`, `remote/.oauth_token` and
  `CLAUDE_CODE_REMOTE_SESSION_ID` belong to cloud-hosted sessions, where the CLI itself runs
  remotely, as `@206668216`
  `setHasRemoteSessionOrContainerId(Boolean(a.CLAUDE_CODE_REMOTE_SESSION_ID||a.CLAUDE_CODE_CONTAINER_ID))`
  shows; a different feature, whose files are in [Credentials](#credentials).

[Sync, relay and origin rows](#sync-relay-and-origin-rows) says which rows the parser makes of
these fields ([issue 80](https://github.com/seanthegeek/doubleagent/issues/80)).

### Format versions

- Versions 2.1.286 to 2.1.289 observed with the same shapes. The parser docstring says "Claude Code
  2.x"; nothing older was available.
- `summary` (`{type, summary, leafUuid}`) and `progress` records are still read by 2.1.289
  (cc:484009, cc:484055) and `progress` can still be written by forked agents (cc:482596); neither
  was observed. The summary type is the legacy form of session titles, now `ai-title` and
  `custom-title`.
- `thinking` blocks are mostly empty strings with a `signature` (3,165 of 3,525): the thinking text
  was not returned, not redacted; `redacted_thinking` is a separate block type.
- Compaction (`compact_boundary` plus a `user` record with `isCompactSummary`) was not observed
  before 2.1.309; `relocated` was never observed.
- 2.1.309 (Windows 11 arm64, 2026-10-23), against 2.1.289: the request capture lines
  `api-request-shape`, `api-request` and `api-request-blob` are written by default and hold more of
  the file than the conversation ([Record schema](#record-schema)); `permissionDecision` gains
  `grantScope` and `reasonCode`, and `source` the values `user_temporary`, `user_permanent` and
  `user_reject` ([Permission decisions](#permission-decisions)); worker and subagent lines carry
  `sessionKind` and `slug` ([Transcript envelope](#transcript-envelope)); `continued-in` and
  `cost-state` lines mark the session daemon's handover, which writes the worker's own transcript
  file ([Session daemon records](#session-daemon-records)); `assistant` lines add `requestRef`,
  `thinkingDisplay` and the `attributionMcp*` keys and `user` lines `sandboxed`, `mcpMeta`,
  `queueSkipSlashCommands` and the scheduled-task keys
  ([`assistant` records](#assistant-records), [`user` records](#user-records)); the attachment
  types `auto_mode_exit`, `session_cron_carry`, `task_reminder`, `plan_file_reference` and `file`
  are new ([`attachment` records](#attachment-records)); `compact_boundary` and `isCompactSummary`
  are observed; `history.jsonl` `pastedContents` carries `{contentHash, id, type}`
  ([`history.jsonl`](#historyjsonl)); `custom-title.json` is written beside the session file; the
  session daemon, `jobs/`, `skills/synced/`, `plugins/synced/` and `state/` directories are written
  ([Per-user storage](#per-user-storage)); the setting `cleanupPeriodDays` must be at least 1
  ([What survives a delete](#what-survives-a-delete)); and a prompt typed during a turn is no longer
  a `queued_command` attachment ([User-record kinds](#user-record-kinds)). The record types of
  2.1.289 that 2.1.309 still writes kept their keys, with the additions named here.
- 2.1.310 (Ubuntu 26.04.1 arm64, 2026-10-25 and 2026-10-26), against 2.1.309: every line type and
  key set of the transcript is unchanged; `/model` saves the pick as the default for new sessions
  without asking ([Joins and timestamps](#joins-and-timestamps)); the allow-always option offers a
  wildcard prefix rule ("Always allow python3 *") rather than the exact command
  ([Permission configuration](#permission-configuration)); `.claude.json` records a GitHub
  connection in `githubWebConnectionStatusCache`
  ([Source-host integration](#source-host-integration)); `permissionDecision.reasonCode` takes
  the value `bashMiss:no-rule-match`, and `reasonType` `subcommandResults` appears on a `config`
  accept ([Permission decisions](#permission-decisions)); `promptSource` `suggestion_accepted`
  was seen on the `/schedule` flow's prompt line ([`user` records](#user-records)); `.meta.json`
  adds `isBuiltIn` ([Transcript stores](#transcript-stores)); a project entry in `.claude.json`
  adds `lastFpsAverage` and `lastFpsLow1Pct` ([`.claude.json`](#claudejson)); and a shell call
  snapshots the working tree under the temp root's `bash-edit-diff/`
  ([Scratch directories](#scratch-directories)). Some differences from the Windows cell are the
  platform's, not the version's: the `.key` file's `procStart` for `procStartFt`, the symlink
  launcher, the `file-history` backup's modification time.
- No compressed or archived transcript form exists; deletion by `cleanupPeriodDays` is the only
  rotation.

### Secrets

- `~/.claude.json`, the global config: `oauthAccount` (the sign-in session) and the MCP server
  definitions' `env` blocks and headers, globally and under `projects.<path>.mcpServers`. The
  parser reads only its permission keys ([Permission configuration](#permission-configuration)).
  On Windows 2.1.309 `oauthAccount` held `accountUuid`, `emailAddress`, `fullName`, `displayName`,
  `organizationUuid`, `organizationName`, `organizationRole`, `organizationType`, `billingType`,
  `accountCreatedAt` and `subscriptionCreatedAt` among others; `machineID` and `userID` (64 hex
  each) identify the install, `cachedArtifactRoster` and `clientDataCacheSlots` name the account
  and organisation again, and `githubRepoPaths` names the GitHub repositories
  ([`.claude.json`](#claudejson)). Every `backups/.claude.json.backup.<epoch ms>` holds the same.
  On Linux 2.1.310 `oauthAccount` had 20 keys, `hasExtraUsageEnabled`, `seatTier` and
  `workspaceRole` among them, and `githubWebConnectionStatusCache` names the account and
  organisation of the GitHub connection by `accountUuid` and `orgUuid`.
- `.credentials.json` on Windows 2.1.309 and Linux 2.1.310:
  `claudeAiOauth{accessToken, refreshToken, expiresAt, refreshTokenExpiresAt, scopes,
  subscriptionType, subscriptionTypeSource, rateLimitTier}`, `scopes` six strings.
- `sessions/<pid>.<sha256>.key` on Windows 2.1.309: `{peerToken, pidDomain, procStartFt}`,
  `peerToken` 32 hex; on Linux 2.1.310 `{peerToken, pidDomain, procStart}`, `procStart` a decimal
  string, the process's start tick. `daemon/control.key` (32 B of hex on Linux) and
  `daemon/pipe.key` are raw key bytes, and
  `daemon/roster.json` carries `ptyAuth` and `rvAuth` per worker
  ([Session daemon records](#session-daemon-records)).
- Account and organisation ids in names: `skills/synced/<org uuid>_<account uuid>/`,
  `plugins/synced/<org uuid>_<account uuid>/` and `cache/model-catalog/<org uuid>-...`.
- The settings files: `env` (such as `env.ANTHROPIC_API_KEY`), `apiKeyHelper`, hooks and MCP server
  settings and headers; the parser never reads them.
- Identity inside the transcript: the `session_context` attachment carries
  `context{userEmail, gitStatus}`, `credential_org` an `organizationUuid`, and `bridge-session`
  records `ownerAccountUuid` and `ownerOrganizationUuid` ([Record schema](#record-schema)); the
  `bridge_status` line's `url` is the Remote Control pairing URL, and every `api-request-blob`
  repeats a request message with the prompt text.
- The credential files of the config home are in [Credentials](#credentials).

### Parser plan

`doubleagent/parsers/claude_code.py`, class `ClaudeCodeParser`. `wants()`:

```text
^\.claude(?:-[^/]+)?/projects/[^/]+/.*\.jsonl$
^\.claude(?:-[^/]+)?/history\.jsonl$
^\.claude(?:-[^/]+)?/sessions/\d+\.json$
^\.claude(?:-[^/]+)?/settings(?:\.local)?\.json$
^(?:\.claude-[^/]+/)?\.claude\.json$
```

The `.claude-<name>` form is a config home moved with `CLAUDE_CONFIG_DIR`; what the catalog
collects from one is under [Relocated config homes](#relocated-config-homes-claude_config_dir). A
project's `.claude/settings.json` and `.claude/settings.local.json` reach the parser as `project`
artifacts (the collector's project catalog has `project|.claude`), with the project directory as
their home.

Lines are read with `iter_jsonl`; each bad line becomes the row described under [Bad
lines](#bad-line-rows). Each session file is read twice: a first pass collects the prompts that
`queued_command` attachments and `user` records deliver and the lines that deliver them, whether the
file holds a `<fork-boilerplate>` block, and the first `cwd` and `gitBranch`.

Coverage. A label is the start of a `system` row's text, `<label>: ` and then the full text:

| Record | `turn_type` |
| --- | --- |
| subagent file, first transcript record | an extra `system` row first, `subagent <agentId> of <sessionId>` (`agentId` from the record, else from the file name) |
| `user`, first one in a subagent file that is not a fork | `system`, label `subagent task` |
| `user`, `isCompactSummary` | `system`, label `compaction summary` |
| `user`, `interruptedMessageId` | `system`, label `interrupted` |
| `user` text starting `<task-notification>` | `system`, label `task notification` |
| `user` text starting `<command-name>` or `<command-message>` | `system`, label `slash command` |
| `user` text starting `<local-command-stdout>` | `system`, label `command output` |
| `user` text starting `<local-command-caveat>` or `<system-reminder>` | `system`, label `context` |
| `user` text starting `<fork-boilerplate>` | `system`, label `subagent task` |
| `user`, `origin.kind` `task-notification`, `peer`, `coordinator`, `auto-continuation` | `system`, label `task notification`, `peer message`, `coordinator message`, `auto-continuation` |
| `user`, other `isMeta` | `system`, label `context` |
| `user`, any other string, `text` or `image` block | `user` (one row per block); the rules above are tried in this order, the record-level ones for every block |
| `user`, `tool_result` block | `tool_result`; `tool_reference` blocks as their `tool_name`; a `<persisted-output>` stub replaced by its `tool-results/` file, named by `toolUseResult.persistedOutputPath` when that key is set and the line has one `tool_result` block, else by the stub's text (below); text prefixed `[error]` when `is_error` |
| `user`, `permissionDecision` (2.1.295) | one `system` row after the line's `tool_result` rows, `permission decision: <decision> source=<source> reason=<reasonType>` (`-` for a missing key), then a space and the object's compact JSON when it has other keys (`grantScope` and `reasonCode` on 2.1.309, [Permission decisions](#permission-decisions)); `tool_use_id` of the line's first `tool_result` block, `tool_name` empty as on `tool_result` rows |
| `user`, `toolDenialKind`, `userFeedback` (factory key list, [Record schema](#record-schema)) | appended to that line's `permission decision:` row as ` toolDenialKind=<value> userFeedback=<value>`, in that order, each only when set, printed as recorded (no value set is recorded; `userFeedback` is free text, so it comes last); a line with either key and no `permissionDecision` gets the row with `-` for `decision`, `source` and `reasonType` ([issue 97](https://github.com/seanthegeek/doubleagent/issues/97)) |
| `attachment` `plan_mode`, `plan_mode_exit`, `plan_mode_reentry`, `auto_mode`, `auto_mode_exit` | skip: their keys are now recorded ([`attachment` records](#attachment-records)); `auto_mode` is the turn's auto-mode configuration, not a decision, and every mode change they mark is also a `permissionMode` value or a `permission-mode` record, which the `permission mode:` rows read |
| first record of a transcript file that carries `entrypoint` | before its rows, a `system` row `session surface: <entrypoint>` (values `cli`, `claude-vscode`, `claude-desktop` for the Code tab), and `session surface: <old> -> <new>` on a change; a subagent file gets its own row |
| `user` record with `promptSource` set and not `typed`, or `turnOrigin` set and not `human` | after the record's rows, a `system` row `prompt trigger: promptSource=<promptSource> turnOrigin=<turnOrigin>`, `-` for a missing key; the pairs seen on Windows 2.1.309 are `promptSource=suggestion_accepted turnOrigin=human`, `promptSource=system turnOrigin=task_notification` (a subagent's or a background command's end), `promptSource=queued turnOrigin=human` (the Remote Control phone), `promptSource=system turnOrigin=scheduled` (a `/loop` firing) and `promptSource=sdk turnOrigin=human` (the VS Code extension); `origin.kind` still picks the label above |
| `continued-in` | `system`, `session continued in: <continuedInSessionId>`, at the record's `timestamp` |
| `bridge-session` | `system`, `remote control: bridge session <bridgeSessionId or none> lastSequenceNum=<lastSequenceNum or ->`, written when the (id, sequence) pair changes, `none` being the detach; the owner uuids are never printed. At the first record naming an id, once per session and bridge id, `session synced: remote control bridge <bridgeSessionId> url <url>` ([Sync, relay and origin rows](#sync-relay-and-origin-rows)) |
| `attachment` `environment` with `snapshot.scratchpadDirectory` | `system`, `scratch directory: <path> (session scratchpad, from the environment attachment)`, once per session and path, `project_path` the scratchpad path ([Scratch directory rows](#scratch-directory-rows)) |
| `user` `permissionMode`, `permission-mode` record | one tracker per session id in the file: the first value is a `system` row `permission mode: <mode>`, a later different value `permission mode: <old> -> <new>`, before the line's other rows; a `user` line's row takes its timestamp, a `permission-mode` record (no timestamp) the latest one seen; an unchanged value, such as a re-appended state record, yields nothing; a subagent file has its own tracker |
| `assistant` `message.model` (not `<synthetic>`, not an API error) | before the line's rows, `model: <id>` at the session's first one and `model: <old> -> <new>` on each change, with ` requested=<requestedModel>` when that key is set and differs; `model` column the new model; a subagent file has its own tracker |
| `assistant`, `isApiErrorMessage` or model `<synthetic>` | `system`, `api error: <apiErrorStatus> <error>: <text>`, no model |
| `assistant`, `text` block | `assistant` (empty text skipped) |
| `assistant`, `tool_use` block | `tool_use` |
| `assistant`, `thinking` | `thinking` with `include_thinking`; an empty `thinking` (signature only) is skipped |
| `assistant`, `redacted_thinking` | `thinking` with `include_thinking`, text `[redacted]` |
| `assistant`, other block types | skip |
| `system` | `system`, text `<subtype>: <content>`; `turn_duration` as `<durationMs> ms, <messageCount> messages`; without `content`, `<subtype>: ` and the compact JSON of the fields other than the envelope (`api_error`: `level`, `retryInMs`, `retryAttempt`, `maxRetries`, `error`) |
| `attachment` `queued_command`, `origin.kind` `human` | `user`, text `prompt` (a text marker above still makes it `system`) |
| `attachment` `queued_command`, other origin | `system`, the marker or origin label, else `queued command` |
| `attachment` `hook_system_message` | `system`, `hook: <hookName>: <content>` |
| `attachment` `edited_text_file` | `system`, `edited file: <filename>` (the `snippet` is not shown) |
| `attachment`, other types | skip: model context (system prompt, tool lists, reminders, environment and model snapshots, skill and agent listings); `remote_session_change` (the session's PR and commit) is skipped too |
| `ai-title`, `custom-title`, `agent-name` | `system`, `session title: <value>`, once per distinct value per session |
| `relocated` | `system`, `cwd changed: <relocatedCwd>`; every later row of the file takes it as `project_path` |
| `pr-link` | `system`, `pr-link: <prUrl or prNumber>`, once per session and URL (the first record wins) |
| `queue-operation` | `system`, `queue <operation>: <content>`; an `enqueue` whose `content` a `queued_command` attachment or a `user` record of the file delivers is `prompt queued: delivered at line N` at the enqueue's own timestamp, N being the first delivering line after it (else the first), so the typing time is kept and the prompt text appears once, on the delivering row |
| every other type ([Record schema](#record-schema) table) | skip |
| `history.jsonl` line | `user` |
| `sessions/<pid>.json` | one `system` row at `startedAt` (epoch ms), `claude-code process <pid> <kind> status=<status> entrypoint=<entrypoint> bridge=<bridgeSessionId or none> host_session=<hostSessionId or none>` (`-` for a missing `kind`, `status` or `entrypoint`), `session_id` `sessionId`, `project_path` `cwd`, `source_line` 1; a file that is not a JSON object is one `system` row `parser: session registry file is not a JSON object`. A `bridge=` value means the process was under Remote Control when the collector ran ([Remote Control](#remote-control)), and the file then gives a second `system` row, `session synced: remote control bridge <bridgeSessionId> url - (from <path>, file mtime)`, at the file's modification time ([Sync, relay and origin rows](#sync-relay-and-origin-rows)) |
| `settings.json`, `settings.local.json` (user, `.claude-<name>`, or a project's) | one `system` row per `permissions.allow`, `deny`, `ask` and `additionalDirectories` entry, then one for `permissions.defaultMode` and `permissions.disableBypassPermissionsMode` when set: `permission setting: permissions.<key>=<value> (from <path relative to the home or project>, file mtime)`, a non-string value as compact JSON; `timestamp_utc` the manifest `mtime`, else the file's own; `session_id` empty; `project_path` the project directory for a `project` artifact, else empty; `source_line` 1; beside them, when `cleanupPeriodDays` is set, one `system` row `retention setting: cleanupPeriodDays=<n> (from settings.json, file mtime)` at the same time, since the value decides what the retention sweep removes ([What survives a delete](#what-survives-a-delete)); no other key read; a file that is not a JSON object is one `system` row `parser: settings file is not a JSON object` |
| `.claude.json`, `.claude-<name>/.claude.json` | per `projects.<path>`: one row per `allowedTools` entry, then one each for `hasTrustDialogAccepted` and `hasClaudeMdExternalIncludesApproved` when present, `permission setting: <key>=<value> (from .claude.json, file mtime)`, `project_path` the `<path>` key, times as above; when `githubWebConnectionStatusCache` is present (2.1.310), one `system` row `source host: github status=<status> (from .claude.json, file mtime)` at the file's modification time, its `accountUuid` and `orgUuid` never printed ([Sync, relay and origin rows](#sync-relay-and-origin-rows)); nothing else in the file is read (it holds the account's OAuth details); `.claude.json.backup*` is not wanted |

Columns:

| Column | Source |
| --- | --- |
| timestamp_utc | record `timestamp`; records without one (titles, `relocated`) take the latest timestamp seen in the file; history: `timestamp` (ms) |
| session_id | latest `sessionId` (or `session_id`) seen in the file; history: `sessionId` |
| project_path | the `relocatedCwd` of an earlier `relocated` record, else the latest `cwd` seen in the file, else the file's first `cwd`; history: `project` |
| git_branch | the latest `gitBranch` seen in the file, else the file's first |
| turn_type | coverage table |
| model | `message.model` on `assistant` and `thinking` rows |
| tool_name | `tool_use.name`; empty on `tool_result` rows |
| tool_use_id | `tool_use.id` / `tool_result.tool_use_id` |
| text | user/assistant/thinking text; `tool_use`: for Bash the `command` of `wireToolInputs[<id>]` when present (it keeps the `cd <dir> &&` prefix), else per-tool key from `input` (`command`, `file_path`, `notebook_path`, `pattern`+`path`, `url`, `query`, `description`+`prompt`, `skill`+`args`, `path`), else the first of `command`, `file_path`, `path`, `pattern`, `url`, `query`, `description`, else compact JSON; `tool_result`: the block text as above |
| source_line | 1-based line number; the subagent header row takes its first record's line |

Not read: `.meta.json` sidecars, the `sessions/<pid>.<sha256>.key` files (secrets), `paste-cache/`,
the other `sessions/<pid>.json` keys (`procStart`, `version`, `peerProtocol`, `peerFeatures`,
`pidDomain`, `messagingSocketPath`, `name`, `nameSource`, `nameSince`, `updatedAt`,
`statusUpdatedAt`), the 2.1.295 assistant keys (`advisorModel`, `apiBlockIndex`, `effort`,
`perTurnEffort`, `serverClassifierRequest`, `thinkingDurationMs`; `requestedModel` is read only for
the model row and `wireToolInputs` only for Bash), `sourceToolAssistantUUID` and
`serverClassifierContext`, the 2.1.309 request capture lines (`api-request-shape`, `api-request`,
`api-request-blob`), `cost-state`, `mode`, `atis-latch`, `custom-title.json` (the `custom-title`
line is read), the session daemon's files (`daemon.log`, `roster.json`) and `jobs/`,
`backups/`, `file-history/`, `plans/`, `state/mcp-discover-verdicts.json`, `skills/synced/`,
`plugins/synced/`, the registry keys `formerNames`, `parkedJobId` and `jobId`, `sessionKind` (kept
in the row's envelope, not printed), `githubRepoPaths`, the `debug/` logs written by
`claude --debug`, which are not a store the parser reads, and the `claude-cli-nodejs` MCP logs
([CLI cache directory](#cli-cache-directory)), whose lines name the session, the project and a
time, so each `debug` message could become a `system` row joined to the session.

#### Permission rows

Per-call decisions are the `permission decision:` rows of `permissionDecision`, `toolDenialKind`
and `userFeedback` ([issue 97](https://github.com/seanthegeek/doubleagent/issues/97)), the mode the
`permission mode:` rows, and the standing grants the `permission setting:` rows of the settings
files and `.claude.json` ([issue 93](https://github.com/seanthegeek/doubleagent/issues/93)); the
coverage table has the exact texts, [Record schema](#record-schema) and
[Permission configuration](#permission-configuration) the records. On 2.1.309 and 2.1.310 the
decision row covers every form of [Permission decisions](#permission-decisions): the classifier's
and the mode's automatic accepts (`source=config reason=classifier` or `reason=mode`, and on
2.1.310 `reason=subcommandResults`), the one-time approval (`source=user_temporary`, `grantScope`
`once` in the JSON suffix), the allow-always rule's use (`source=user_permanent`), the denial
(`source=user_reject` with `toolDenialKind` and `userFeedback`) and the declined plan (a rejected
`ExitPlanMode`); the `reasonCode` values, `bashMiss:no-rule-match` on 2.1.310 among them, are in
the JSON suffix. The allow-always grant itself is a
`permission setting: permissions.allow=PowerShell(...)` row from the project's
`settings.local.json` on Windows, and a `Bash(...)` one on Linux. The `plan_mode`,
`plan_mode_exit`, `plan_mode_reentry`, `auto_mode` and `auto_mode_exit` attachments are not read;
the mode changes they mark are `permission mode:` rows.

#### Model rows

The `model:` rows come from `message.model` and `requestedModel` (the `assistant` row of the
coverage table). A `/model` switch keeps its own `slash command` and `command output` rows
([Joins and timestamps](#joins-and-timestamps)). The `model` attachment and `cost-state` records are
not read. Confirmed on Windows 2.1.309 and Linux 2.1.310: the lines carry the resolved id only, so
the change row is the evidence of a switch, and the alias the person picked is in `settings.json`
`model`, which the parser does not read.

#### Past-use rows and secondary sources

`.claude/history.jsonl` is read on every run as a secondary source of the transcripts, one `user`
row per line ([`history.jsonl`](#historyjsonl)); it usually outlives its transcript ([What survives
a delete](#what-survives-a-delete)), the retention sweep keeping it when it deletes the transcript,
so a session found only in `history.jsonl` is the expected trace of a swept session. The
`sessions/<pid>.json` registry and the permission settings yield rows of their own. A prompt sent
through `claude agents` or from the VS Code extension's panel is in the transcript only
([`history.jsonl`](#historyjsonl)). Not read: `file-history/` and the `file-history-*` records,
`paste-cache/` (collected; the paste is inline in the transcript, and `history.jsonl` names it by
hash), `backups/` (dated copies of `.claude.json`), `jobs/` and the daemon's files, the
`.meta.json` sidecars and the `claude-cli-nodejs` MCP logs, which each name the session, the
project and a time and so could become rows of their own.

#### Sync, relay and origin rows

The agent records sync through Remote Control. A `bridge-session` line becomes a
`remote control: bridge session <bridgeSessionId or none> lastSequenceNum=<lastSequenceNum or ->`
row whenever its id and sequence pair changes, `none` marking the detach. At the first
`bridge-session` line that names an id, once per session and bridge id, the parser also yields
`session synced: remote control bridge <bridgeSessionId> url <url>`, the `url` being that of the
`bridge_status` system line that belongs to the bridge: among the status lines between the
previous and the next `bridge-session` line of another id (a detach counts), the first at or
after it, else the nearest before it, else `-`, so a second bridge in one file never takes the
first bridge's URL, and it sets
`records_sync`, so `sessions.jsonl` `synced` reads `yes` or `no` for this agent's sessions. The
row rests on the `bridge_status` URL (`https://claude.ai/code/session_<id>`) naming the session on
claude.ai while the bridge is up; whether claude.ai keeps the transcript after the detach was not
determined. A `sessions/<pid>.json` registry file that names a `bridgeSessionId` gives the same
marker, `session synced: remote control bridge <bridgeSessionId> url - (from <path>, file mtime)`,
at the file's modification time, because the id says the process was under Remote Control when
the collector ran ([Remote Control](#remote-control)); it is the marker that is left when the
transcript is gone, and a session with both keeps both rows, which `sessions.jsonl` counts once
as `synced` `yes`. The daemon handover is local and is a `session continued in:`
row, not a sync row. The agent records no relay, and the parser sets neither `records_relay` nor
`records_origin`: a cloud session could not be started from the CLI on the Windows or the Linux
round, and the files the bundle names for one (`.session_ingress_token`, `remote/`,
`server-sessions.json`, `remote-settings.json`) were never written; the `remote_session_change`
attachment, present in plain local sessions with nothing to link, is skipped. The source host is
a row since 2.1.310: `.claude.json` `githubWebConnectionStatusCache` gives one `system` row
`source host: github status=<status> (from .claude.json, file mtime)` at the file's modification
time, the account and organisation uuids not printed
([Source-host integration](#source-host-integration)); 2.1.309 wrote no such key, so its homes
have no such row. The GitHub account's login and token stay in `gh`'s store, which is not
collected, and `githubRepoPaths` is not read.

#### Scratch directory rows

The `environment` attachment's `snapshot.scratchpadDirectory` becomes a `system` row
`scratch directory: <path> (session scratchpad, from the environment attachment)`, once per session
and path, whose `project_path` is the scratchpad path, so `inventory.json` lists it under
`scratch_directories`. On Windows the path
is under the collected temp root `AppData/Local/Temp/claude/<slug>/<session id>/scratchpad`
([Scratch directories](#scratch-directories)); on Linux and macOS the temp root is outside the home
and not collected ([issue 163](https://github.com/seanthegeek/doubleagent/issues/163)), so the row
names a directory the collection lacks. On Linux the temp root also holds one directory per
process, so a resume, a `--continue`, `claude agents` or `claude mcp add` leaves directories that a
session's row may not name, and the whole tree is gone after a reboot or when the retention sweep
deletes the session's transcript. The files under the temp root's `tasks/` and `bash-edit-diff/`
are not read.

#### Deletion rows

The agent records none: no deletion marker is stated or was seen on Windows 2.1.309 or Linux
2.1.310 ([What survives a delete](#what-survives-a-delete)). A `/clear` is a `local_command` row,
`local_command: ` and the command, in the new session's file, with nothing in the old one. A removed
project is not a row: the analyzer's inventory lists it with the `referenced` status, a project the
collected files still name with no files of its own. The retention sweep deletes silently, so the
setting that drives it is the row: `cleanupPeriodDays` in a settings file gives
`retention setting: cleanupPeriodDays=<n> (from settings.json, file mtime)` (coverage table), and a
session whose transcript the sweep removed remains as its `history.jsonl` rows
([Past-use rows and secondary sources](#past-use-rows-and-secondary-sources)).

#### Bad-line rows

Each bad line becomes its own `system` row at the end of the file's rows, `source_line` its line
number and text `parser: unparseable line (<decoder message>): <the line in full>`
([issue 136](https://github.com/seanthegeek/doubleagent/issues/136)); the rows before and after it
are kept. The session sample under [Fixtures](#fixtures) ends with a cut line for this case.

#### Fixtures

Sample records, `.claude/projects/-srv-proj/11111111-2222-4333-8444-555555555555.jsonl` (state
record, typed prompt, empty-thinking block, Bash call with a wire input, its result, a prompt queued
mid-turn and its attachment, reply, turn duration, title, last prompt, PR link, backup snapshot,
then a cut line):

```json
{"type":"mode","mode":"normal","sessionId":"11111111-2222-4333-8444-555555555555"}
{"parentUuid":null,"isSidechain":false,"promptId":"0c0c0c0c-0000-4000-8000-000000000001","type":"user","message":{"role":"user","content":"why does the test fail?"},"uuid":"00000000-0000-4000-8000-000000000001","timestamp":"2026-10-01T10:00:00.000Z","permissionMode":"auto","origin":{"kind":"human"},"promptSource":"typed","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"parentUuid":"00000000-0000-4000-8000-000000000001","isSidechain":false,"message":{"model":"claude-fable-5-1","id":"msg_01","type":"message","role":"assistant","content":[{"type":"thinking","thinking":"","signature":"c2lnbmF0dXJl"}],"stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":900,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":40}},"requestId":"req_01","apiBlockIndex":0,"type":"assistant","uuid":"00000000-0000-4000-8000-000000000002","timestamp":"2026-10-01T10:00:02.000Z","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"parentUuid":"00000000-0000-4000-8000-000000000002","isSidechain":false,"message":{"model":"claude-fable-5-1","id":"msg_01","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_01","name":"Bash","input":{"command":"npm test","description":"Run the tests"},"caller":{"type":"direct"}}],"stop_reason":"tool_use","stop_sequence":null,"usage":{"input_tokens":900,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":60}},"requestId":"req_01","apiBlockIndex":1,"wireToolInputs":{"toolu_01":{"command":"cd /srv/proj && npm test","description":"Run the tests"}},"wireIngestContext":{"toolu_01":{"cwd":"/srv/proj"}},"type":"assistant","uuid":"00000000-0000-4000-8000-000000000003","timestamp":"2026-10-01T10:00:03.000Z","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"parentUuid":"00000000-0000-4000-8000-000000000003","isSidechain":false,"promptId":"0c0c0c0c-0000-4000-8000-000000000001","type":"user","message":{"role":"user","content":[{"tool_use_id":"toolu_01","type":"tool_result","content":"1 failing","is_error":false}]},"uuid":"00000000-0000-4000-8000-000000000004","timestamp":"2026-10-01T10:00:05.000Z","toolUseResult":{"stdout":"1 failing","stderr":"","interrupted":false,"isImage":false,"noOutputExpected":false},"sourceToolAssistantUUID":"00000000-0000-4000-8000-000000000003","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"type":"queue-operation","operation":"enqueue","timestamp":"2026-10-01T10:00:05.500Z","sessionId":"11111111-2222-4333-8444-555555555555","content":"also check the linter"}
{"parentUuid":"00000000-0000-4000-8000-000000000004","isSidechain":false,"attachment":{"type":"queued_command","prompt":"also check the linter","commandMode":"prompt","origin":{"kind":"human"},"source_uuid":"00000000-0000-4000-8000-0000000000a1","delivery_id":"0d0d0d0d-0000-4000-8000-000000000001","timestamp":"2026-10-01T10:00:05.500Z"},"type":"attachment","uuid":"00000000-0000-4000-8000-000000000005","timestamp":"2026-10-01T10:00:06.000Z","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"parentUuid":"00000000-0000-4000-8000-000000000005","isSidechain":false,"message":{"model":"claude-fable-5-1","id":"msg_02","type":"message","role":"assistant","content":[{"type":"text","text":"The fixture date is stale; the linter is clean."}],"stop_reason":"end_turn","stop_sequence":null,"usage":{"input_tokens":950,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":20}},"requestId":"req_02","apiBlockIndex":0,"type":"assistant","uuid":"00000000-0000-4000-8000-000000000006","timestamp":"2026-10-01T10:00:08.000Z","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"parentUuid":"00000000-0000-4000-8000-000000000006","isSidechain":false,"type":"system","subtype":"turn_duration","durationMs":8000,"messageCount":7,"pendingBackgroundAgentCount":0,"timestamp":"2026-10-01T10:00:08.100Z","uuid":"00000000-0000-4000-8000-000000000007","isMeta":false,"userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"type":"ai-title","aiTitle":"Fix stale fixture date","sessionId":"11111111-2222-4333-8444-555555555555"}
{"type":"last-prompt","lastPrompt":"why does the test fail?","leafUuid":"00000000-0000-4000-8000-000000000007","sessionId":"11111111-2222-4333-8444-555555555555"}
{"type":"pr-link","sessionId":"11111111-2222-4333-8444-555555555555","prNumber":7,"prUrl":"https://github.com/example/proj/pull/7","prRepository":"example/proj","timestamp":"2026-10-01T10:00:09.000Z"}
{"type":"file-history-snapshot","messageId":"00000000-0000-4000-8000-000000000001","snapshot":{"messageId":"00000000-0000-4000-8000-000000000001","trackedFileBackups":{},"timestamp":"2026-10-01T10:00:00.000Z"},"isSnapshotUpdate":false}
{"parentUuid":"00000000-0000-4000-8000-000000000007","isSidechain":false,"type":"user","message":{"role":"user","content":"thanks"
```

Subagent, and its sidecar `agent-a0b1c2d3e4f5a6b7c.meta.json`:

- `.claude/projects/-srv-proj/11111111-2222-4333-8444-555555555555/subagents/agent-a0b1c2d3e4f5a6b7c.jsonl`

```json
{"parentUuid":null,"isSidechain":true,"agentId":"a0b1c2d3e4f5a6b7c","promptId":"0c0c0c0c-0000-4000-8000-000000000001","type":"user","message":{"role":"user","content":"Find where the fixture date is set."},"uuid":"00000000-0000-4000-9000-000000000001","timestamp":"2026-10-01T10:00:04.000Z","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555","version":"2.1.289","gitBranch":"main"}
{"agentType":"general-purpose","description":"Find the fixture date","toolUseId":"toolu_02","model":"claude-fable-5-1","spawnDepth":1,"requestShape":"agent","requestNonInteractive":false}
```

History `.claude/history.jsonl`:

```json
{"display":"why does the test fail? [Pasted text #1 +3 lines]","pastedContents":{"1":{"id":1,"type":"text","contentHash":"0123456789abcdef"}},"timestamp":1790848800000,"project":"/srv/proj","sessionId":"11111111-2222-4333-8444-555555555555"}
```

Expected rows from the session sample with the parser: `user` (line 2); nothing for the empty
thinking block (line 3, even with `include_thinking`); `tool_use` `Bash` `toolu_01` text
`cd /srv/proj && npm test` (line 4, from `wireToolInputs`); `tool_result` `toolu_01` text
`1 failing` (line 5); `system` `prompt queued: delivered at line 7` (line 6, at 10:00:05.500);
`user` `also check the linter` (line 7); `assistant` (line 8); `system`
`turn_duration: 8000 ms, 7 messages` (line 9); `system` `session title: Fix stale fixture date`
(line 10, timestamp of line 9); `system` `pr-link: https://...` (line 12); and the bad-line `system`
row (line 14). All have `session_id` `11111111-...`; all but the bad-line row have `project_path`
`/srv/proj` and `git_branch` `main` (checked by running the parser on this sample). The subagent
sample yields two `system` rows on line 1, `subagent a0b1c2d3e4f5a6b7c of 11111111-...` and
`subagent task: Find where the fixture date is set.`, with the parent's `session_id`. Noise the
parser must not want: `.claude/settings.json`, the `.meta.json` sidecar, `tool-results/*.txt` (read
only through a stub).

Records in the 2.1.309 shapes of the Windows round, values synthetic (a VS Code extension prompt
with its environment snapshot, a one-time approval, a Remote Control bridge line and its status, a
daemon handover):

```json
{"parentUuid":null,"isSidechain":false,"type":"attachment","attachment":{"type":"environment","changes":{},"snapshot":{"workingDirectory":"/srv/proj","platform":"linux","shell":"bash","osVersion":"6.8","isGitRepo":true,"isWorktree":false,"additionalWorkingDirectories":[],"scratchpadDirectory":"/tmp/claude-1000/-srv-proj/22222222-3333-4444-8555-666666666666/scratchpad"}},"uuid":"00000000-0000-4000-a000-000000000001","timestamp":"2026-10-23T16:03:24.000Z","userType":"external","entrypoint":"claude-vscode","cwd":"/srv/proj","sessionId":"22222222-3333-4444-8555-666666666666","version":"2.1.309","gitBranch":"main"}
{"parentUuid":"00000000-0000-4000-a000-000000000001","isSidechain":false,"type":"user","message":{"role":"user","content":"run the tests"},"uuid":"00000000-0000-4000-a000-000000000002","timestamp":"2026-10-23T17:00:55.000Z","permissionMode":"auto","origin":{"kind":"human"},"promptSource":"sdk","turnOrigin":"human","sandboxed":false,"userType":"external","entrypoint":"claude-vscode","cwd":"/srv/proj","sessionId":"22222222-3333-4444-8555-666666666666","version":"2.1.309","gitBranch":"main"}
{"parentUuid":"00000000-0000-4000-a000-000000000003","isSidechain":false,"type":"user","message":{"role":"user","content":[{"tool_use_id":"toolu_11","type":"tool_result","content":"ok","is_error":false}]},"uuid":"00000000-0000-4000-a000-000000000004","timestamp":"2026-10-23T17:01:10.000Z","permissionDecision":{"decision":"accept","source":"user_temporary","grantScope":"once","reasonCode":"other"},"toolUseResult":{"stdout":"ok","stderr":"","interrupted":false,"isImage":false,"noOutputExpected":false},"sourceToolAssistantUUID":"00000000-0000-4000-a000-000000000003","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"22222222-3333-4444-8555-666666666666","version":"2.1.309","gitBranch":"main"}
{"type":"bridge-session","bridgeSessionId":"cse_0123456789abcdef","lastSequenceNum":3,"ownerAccountUuid":"00000000-0000-4000-b000-000000000001","ownerOrganizationUuid":"00000000-0000-4000-b000-000000000002","sessionId":"22222222-3333-4444-8555-666666666666"}
{"parentUuid":"00000000-0000-4000-a000-000000000004","isSidechain":false,"type":"system","subtype":"bridge_status","content":"Remote Control connected","url":"https://claude.ai/code/session_0123456789abcdef","isMeta":false,"level":"info","uuid":"00000000-0000-4000-a000-000000000005","timestamp":"2026-10-23T17:02:00.000Z","userType":"external","entrypoint":"cli","cwd":"/srv/proj","sessionId":"22222222-3333-4444-8555-666666666666","version":"2.1.309","gitBranch":"main"}
{"type":"continued-in","continuedInSessionId":"33333333-4444-4555-8666-777777777777","sessionId":"22222222-3333-4444-8555-666666666666","timestamp":"2026-10-23T17:03:00.000Z"}
```

They yield, in the forms of the coverage table: `session surface: claude-vscode` (line 1) and
`session surface: claude-vscode -> cli` (line 3 carries another value);
`scratch directory: /tmp/claude-1000/-srv-proj/22222222-.../scratchpad (session scratchpad, from the
environment attachment)` (line 1); the `user` row and then
`prompt trigger: promptSource=sdk turnOrigin=human` (line 2); the `tool_result` row and
`permission decision: accept source=user_temporary reason=- {"decision":"accept","grantScope":"once","reasonCode":"other","source":"user_temporary"}`
(line 3); `remote control: bridge session cse_0123456789abcdef lastSequenceNum=3` and
`session synced: remote control bridge cse_0123456789abcdef url https://claude.ai/code/session_0123456789abcdef`
(line 4; no `bridge_status` line precedes it, so the file's first, line 5, gives the url); the
`bridge_status` `system` row (line 5); and
`session continued in: 33333333-4444-4555-8666-777777777777` (line 6). The surface change is a
fixture device, not something a real file was seen to do.

#### Forked subagents

A forked subagent's file begins with a copy of the forking agent's context (observed in the 4 fork
files: the records before the `<fork-boilerplate>` one have new `uuid`s, and their tool ids are in
no session file), so no boundary ties those records to their source; their rows are kept, the first
`user` record stays `user`, and the `<fork-boilerplate>` block is the `subagent task` row.

#### Persisted output files

When a `tool_result` text starts with `<persisted-output>`, the parser takes the path from the
line's `toolUseResult.persistedOutputPath` when that key is set (2.1.309), else the path after
`Full output saved to: `, keeps its last component and requires the component before `tool-results`
to equal the transcript's session directory (`<session id>/` beside a session file, the directory
above `subagents/` for a subagent file). It reads `<session dir>/tool-results/<name>` when neither
the file, `tool-results/` nor the session directory is a symlink, and otherwise keeps the stub
followed by `[persisted output not found: tool-results/<name>]`. On the observed install every stub
resolved.

## Confidence

- High (bundle literals plus docs, layout confirmed locally and on Windows 2.1.309): config-dir
  resolution, directory and file name sets, the `projects/` key scheme and transcript naming,
  keychain service construction, `.credentials.json`, managed paths, native installer paths.
- High (bundle, corroborated by claude-mem source): `.claude.json` inside a relocated config home;
  and that claude-code-router, claude-mem and claude-squad keep nothing at their roots that the
  `.claude-*/` lines collect (source at the linked commits).
- High (observed and consistent with the bundle): the record type list, the transcript envelope,
  one block per `assistant` record, the `tool_use`/`tool_result` join, `toolUseResult`,
  `sourceToolAssistantUUID`, `wireToolInputs`/`wireIngestContext` and the stripped `cd` prefix,
  `user`-record origins and the subagent first-line prompt, the subagent join through `.meta.json`,
  millisecond ISO timestamps, epoch-millisecond history, empty thinking with signature, `pr-link`
  re-append, `queued_command` prompts before 2.1.309.
- High (observed on macOS and Linux with 2.1.295 and 2.1.296, and on Windows with 2.1.309): the
  `sessions/<pid>.json` registry keys, `requestedModel`, and the `permission-mode` records; the
  permission configuration key names (observed by name only).
- High (observed on Windows 2.1.309, key names and enum values only, one install): the request
  capture lines, the `permissionDecision` forms, compaction, the session daemon's handover and
  files, the Remote Control records, the VS Code extension's sessions, the Windows temp root and
  CLI cache directory, and what a `/clear` or a removed project leaves.
- High (observed on Linux 2.1.310, key names, enum values and file modes only, one install): the
  native installer's layout and the version lock, the Linux CLI cache directory and temp root,
  the transcript record set, the `permissionDecision` forms, the detached-head `gitBranch`, the
  two `pastedContents` forms, the GitHub connection key, and what the retention sweep removed and
  kept in its one observed run.
- Medium: the exact keychain service string (built from `"Claude Code"` + `"-credentials"`; not seen
  as one literal); contents of `storage-v2`, `seed-admin`, `remote`, `systemd` (names only), and of
  `~/.cache/claude/staging` beyond its being empty whenever listed.
- Medium (bundle only, not exercised): `api_error`, `memory_saved`, `relocated`, `ended-by-model`,
  `content-replacement`, `frame-link`, `summary`, `progress`, nested subagent subdirectories; a
  cloud session's files and an origin row for it, which neither the Windows nor the Linux round
  could start from the CLI.
- Medium (vendor documentation only, not exercised): what `claude purge` deletes and leaves, and
  the sweep's rules for `file-history/` checkpoints, auto memory and Claude Desktop transcripts.
- Not determined: how common config-home names other than `.claude-<name>` are; other `.claude-`
  prefixed tools beyond the three checked; whether `.claude.json` suffix variants
  (`.claude<suffix>.json`) appear on normal installs; size of `dump-prompts` in practice.
- Not determined: the meaning of a `session_id` that differs from `sessionId`, and whether it marks
  the lines the daemon handover copies; the shape of `fork-context-ref`,
  `content-replacement.replacements[]` and `history-suppression`; whether `redacted_thinking`,
  `server_tool_use` or `image` blocks still appear in 2.1.x transcripts; `gitBranch` outside a
  repository; the layout before 2.1.286.
- Not determined on Windows 2.1.309: what triggered the daemon handover and
  what ended the daemon; whether a prompt sent through `claude agents` was answered, since no
  `assistant` line followed it; whether claude.ai keeps a Remote Control session's transcript after
  the detach, which the `session synced:` row assumes only for while the bridge is up; the meaning
  of the two-character `kind` of a worker's registry file; `defaultMode` for
  a mode kept as the default, which no step chose.
- Not determined on Linux 2.1.310: the exact trigger of the retention sweep (the observed
  condition, a session with at least one prompt, is under
  [What survives a delete](#what-survives-a-delete)), and so whether a host whose sessions are all
  short or promptless ever sweeps; whether the Linux build ever hands a session to the session
  daemon, which no step of the round did; which part of the CLI owns the Bun module
  `/tmp/.bun-<uid>-<hex>.node` and whether it is reused across starts; whether the `bash-edit-diff/`
  snapshots of a session whose process died stay until a reboot or the sweep; whether the
  `file-history` backup's modification time differs from Windows by platform or by version; why
  `/model` was a `history.jsonl` line on Windows 2.1.309 and not on Linux 2.1.310; and where `gh`
  keeps the token on a headless Linux host.
