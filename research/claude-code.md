# claude-code

Claude Code (catalog agent `claude-code`) is Anthropic's closed-source coding agent CLI; Claude
Desktop's Code tab launches the same CLI ([`claude-desktop.md`](claude-desktop.md)). It writes one
append-only JSONL transcript per session, a tree of records linked by `uuid`/`parentUuid`, with each
subagent in its own JSONL file under the session directory, plus a global prompt history. No other
agent in the catalog shares this format; Claude Desktop's Code sessions point back at the same
`projects/` files ([Where the project path is recorded](#where-the-project-path-is-recorded)). The
agent is parsed by the `claude-code` parser ([Parser plan](#parser-plan)).

## Source and evidence

Closed source; no public repository, so there are no commit links. No binary below was ever
executed. Each claim names its evidence level, best first:

- **Bundle 2.1.288**, the evidence for the Collection part ([Per-user storage](#per-user-storage) to
  [Where the project path is recorded](#where-the-project-path-is-recorded)): `npm pack @anthropic-ai/claude-code` gives
  2.1.288, a 28 KB shim whose `package.json` lists `optionalDependencies` on eight platform packages
  (`scratchpad/npm/cc/package/package.json`). `npm pack @anthropic-ai/claude-code-linux-x64@2.1.288`
  gives a single 245 MB Bun-compiled binary `claude`; `strings -n 6` of it is
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
  [Claude Desktop data storage](https://claude.com/docs/third-party/claude-desktop/data-storage).
- **Local**: the author's host ([Observed](#observed)). A shape the Parsing part marks observed
  was seen on the WSL2 install; one marked bundle rests on the binary only.
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
- Windows (native): no real install.

### Source reviews

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
(`%USERPROFILE%\.claude`, docs settings page). No XDG or Library/AppData paths for user state, apart
from the cache directory below. `CLAUDE_CONFIG_DIR` relocates everything including
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
`settings.local.json` (cc:436317-8), `.device-keys.json` and `.config.json` (cc:477075).

#### Scratch directories

None known under the home; the Claude Code CLI temp roots outside it (`/tmp/claude-<uid>` on Linux)
are described in [Where the project path is recorded in
`claude-desktop.md`](claude-desktop.md#where-the-project-path-is-recorded).

#### Files that hold evidence

- `projects/<key>/<sessionId>.jsonl`: transcripts, with `<key>` derived from the cwd (cc:473017,
  cc:473728); `projects/<key>/<sessionId>/subagents/agent-<id>.jsonl`: subagent transcripts
  (cc:476679); `projects/<key>/memory/*.md`: per-project memory (cc:489631). The naming and the
  sidecars are in [Transcript stores](#transcript-stores). Local shows `-home-sean-dev-...` dirs
  holding `<uuid>.jsonl`, `<uuid>/`, `memory/`.
- `history.jsonl`: prompt history, with retention pruning (cc:338013-15, 478233).
- `debug/<sessionId>.txt`: per-session debug logs (cc:472977); `debug/latest` symlink (local).
- `file-history/<sessionId>/`: pre-edit file backups (cc:482923); `session-env/<sessionId>/`
  (cc:480109); `shell-snapshots/snapshot-<shell>-<epoch>-<rand>.sh` (shell function dumps, cc:480528
  region, local name confirms); `todos/`, `tasks/<sessionId>/`, `plans/*.md` (cc:476220), `teams/`,
  `jobs/<id>/parent-transcript.jsonl` (cc "jobs" ctx), `dump-prompts/*.jsonl` (full outgoing
  prompts, cc "dump-prompts" ctx), `api-dumps`, `traces/*.json`,
  `usage-data/{facets,session-meta}/*.json` and `report-*.html` (cc:492127),
  `feedback-bundles/*.zip`, `shares/*.zip`, `uploads/<sessionId>/`, `ide/<port>.lock` (local
  `13502.lock`; Windows/WSL also probes `%USERPROFILE%\.claude\ide`, cc "ide" ctx), `backups/`
  (`.claude.json` snapshots; docs: `~/.claude/backups/.claude.json.corrupted.<ts>`).
- `.claude.json` sits in `$HOME`, or inside the config home when `CLAUDE_CONFIG_DIR` is set: its
  path is ``join(process.env.CLAUDE_CONFIG_DIR || homedir(), `.claude${suffix}.json`)`` (cc:473059
  `mar()`, cc:473896 `configPath`; variants `.claude${suffix}.json`, cc:477075); docs: "holds your
  sign-in session, MCP server configurations, per-project state such as trust decisions, and the
  global config keys" (settings page). Its `projects` object is keyed by project path
  ([Where the project path is recorded](#where-the-project-path-is-recorded)).
- `settings.json`, `settings.local.json` and, per project, `.claude/settings.json` and
  `.claude/settings.local.json`: settings, including the standing permission grants, which with
  the `projects.<path>` grants in `.claude.json` are the evidence of what the person authorised
  ([issue 93](https://github.com/seanthegeek/doubleagent/issues/93)). They are collected with the
  config home and the project catalog's `.claude` entry; their keys are under
  [Permission configuration](#permission-configuration).
- `plugins/`: `installed_plugins.json`, `known_marketplaces.json`, `marketplaces/<name>/` git
  clones, `cache/` zip cache (cc plugins ctx); local also `blocklist.json`,
  `plugin-directory-cache-v2.json`, `synced/`.
- `statsig/` feature-flag cache, `cache/gateway-models.json`, `cache/model-capabilities.json`,
  `telemetry/`, `telemetry/runs/`, `chrome/chrome-native-host[.bat]`, `local/` (npm-local install),
  `remote/` (cloud sessions: `/home/claude/.claude/remote/.oauth_token`, `.api_key`,
  `.session_ingress_token`, cc `.session_ingress_token` ctx).
- Native installer binaries: `$XDG_DATA_HOME/claude/versions/<ver>` (default
  `~/.local/share/claude/versions`) and symlink `~/.local/bin/claude` (cc "versions" ctx
  `o(wje(e),"claude","versions")`, `o(n,".local","bin")`; local confirms three ~245 MB versions).
  Windows: `winget Anthropic.ClaudeCode` (cc:296086).

#### CLI cache directory

The CLI cache directory ([issue 81](https://github.com/seanthegeek/doubleagent/issues/81)) comes
from the env-paths code bundled in the CLI with app name `claude-cli` and suffix `nodejs`:
`~/Library/Caches/claude-cli-nodejs/` on macOS (observed with CLI 2.1.295 launched by the Claude
Desktop Code tab, 2026-10-11), `$XDG_CACHE_HOME/claude-cli-nodejs/` else
`~/.cache/claude-cli-nodejs/` on Linux, and `%LOCALAPPDATA%\claude-cli-nodejs\Cache\` on Windows
(both bundle-derived, not observed on a real install). Under it,
`<project slug>/mcp-logs-<server>/<timestamp>.jsonl`: the slug is the cwd with every
non-alphanumeric character replaced by `-` (the `projects/` key scheme), the server is the MCP
server name slugged the same way, and the file name is an ISO timestamp with `:` and `.` replaced by
`-` (`2026-10-12T02-23-51-709Z.jsonl`).

Each line is `{cwd, debug, sessionId, timestamp}`. The bundle also names `<project slug>/errors/`
(not observed). `CLAUDE_CONFIG_DIR` does not move it. Observed on macOS: the Code tab's CLI wrote
`mcp-logs-ccd-host/` and `mcp-logs-terminal/` (the desktop's own two MCP servers) under the
project's slug at session start, one line of about 200 bytes each, and ordinary CLI sessions on
another project wrote `mcp-logs-<connector name>/` files of 7-9 lines (1.5-2.2 KB); the whole
directory was 16 KB. Evidence, `claude 2.1.295 linux-arm64` (the binary recorded in
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
`.claude-*/remote/.oauth_token` and `.claude-*/remote/.api_key`. A bare `.claude-*` entry would
claim other tools' directories that share the prefix:

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

Not collected from a relocated home: `settings.json`, `settings.local.json`, `sessions/`, `todos/`,
`plans/`, `tasks/`, `session-env/`, `shell-snapshots/`, `debug/` and the other subdirectories, and
any config home outside the home directory or not named `.claude-<name>`.

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
  `<config>/.credentials.json` mode 0600 (docs /iam). Local file present.
- `~/.claude/.device-keys.json` (device key store, file fallback to keychain, cc:477075,
  cc:337890-900). Not moved by `CLAUDE_CONFIG_DIR`.
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
  `.claude-*/sessions/*.key`). The `<pid>.json` itself is not flagged
  ([Remote Control](#remote-control)).
- Config files that can embed keys: `settings.json` / `settings.local.json`, `.mcp.json`,
  `managed-mcp.json` (the fields are in [Secrets](#secrets)). Env: `ANTHROPIC_API_KEY`,
  `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN` (docs /iam precedence list). Anthropic profiles
  live outside: `~/.config/anthropic` / `%APPDATA%\Anthropic` (docs /iam).

### Exclusions

Patterns are relative to the home: `.claude/plugins/marketplaces` (git clones),
`.claude/plugins/cache`, `.claude/plugins/*/node_modules`, `.claude/local/node_modules`,
`.claude/image-cache`, `.claude/paste-cache`, `.claude/chrome`, `.claude/cache`, `.claude/statsig`
(flag cache, optional), `.local/share/claude/versions` (~245 MB per version). Project-side:
`*/.claude/worktrees`, `*/.claude/checkpoints` (gitignore template cc "claude-code-runtime").
`downloads/`, `uploads/`, `file-transfers/` may be large but are user content; cap by size rather
than exclude. The [CLI cache directory](#cli-cache-directory) is small and nothing in it, its
`errors/` subdirectory included, is excluded. On Windows the catalog names the cache directory's
children (`AppData/Local/claude-cli-nodejs/Cache/*`) rather than the directory, so that the Claude
Desktop exclusion `*/Claude*/Cache` does not prune it
([`collectors/docs/coverage.md`](../collectors/docs/coverage.md) says why).

### Project-local files

`.claude/settings.json`, `.claude/settings.local.json`,
`.claude/{skills,commands,agents,hooks,rules}/` (cc "agents"/"settings.json" ctx), `.mcp.json`
(cc:273219), `CLAUDE.md`, `CLAUDE.local.md` (cc:19360, 299964), `.claude/scheduled_tasks.json`,
`.claude/scheduled_tasks.lock`, `.claude/routines/.state/`, `.claude/worktrees/`,
`.claude/checkpoints/`, `.claude/mailbox/`, `.claude/agent-registry.json`,
`.claude/agent-memory-local`, `.claude/first-run`, `.claude/assistant-daemon-state.json` (gitignore
template, cc "claude-code-runtime" ctx). No per-project database.

### Where the project path is recorded

- `~/.claude.json` → `projects` object, keys are absolute cwd paths (cc:474276 `e.projects`; docs
  "per-project state such as trust decisions"). In a relocated home it is
  `<config home>/.claude.json`; `discover_projects` and `Find-Projects` read
  `~/.claude-*/.claude.json` and `~/.claude-*/history.jsonl` as well as the default paths.
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
| `.claude/projects/<key>/<session id>/subagents/agent-<agent id>.meta.json` | one JSON object per subagent: `agentType`, `description`, `toolUseId`, `model`, `spawnDepth`, `requestShape`, `requestNonInteractive`, and for some `isFork`, `parentAgentId`, `spawnedWithWorktree`, `worktreePath`, `worktreeBranch` (observed, 80 of 80; cc:484010 maps `.meta.json` to `.jsonl`) | no, [Joins and timestamps](#joins-and-timestamps) |
| `.claude/projects/<key>/<session id>/tool-results/<name>.txt` | full output of a tool result too large to keep inline (`tool-results` constant, cc:474483); the inline result holds a `<persisted-output>` stub (cc:382991) | through the stub, [Parser plan](#parser-plan) |
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

#### What survives a delete

Claude Code deletes transcripts older than `cleanupPeriodDays` (default 30) at startup and prunes
`.claude/history.jsonl` by the same retention (cc:474049 setting description, cc:490770
`cleanupPeriodDays??`); no other delete command is stated. The per-prompt history
([`history.jsonl`](#historyjsonl)) usually outlives its transcript and is then the only record of
the prompt; long pasted text is in `paste-cache/`, which the collector excludes. Beside it in the
config home sit the backups of files the agent edited (`file-history/<session id>/`), the
live-process records of `sessions/<pid>.json`, a background job's copy of its parent transcript
(`jobs/<id>/parent-transcript.jsonl`, not observed) and the project paths in `.claude.json`; whether
retention prunes them is not stated. Hermes Agent's `state.db`, a Cline session made by the SDK's
import and Pydantic AI's CLAI `sessions.db` hold copies that outlive the original file (below). No
deletion marker is stated. The analyzer reads `history.jsonl` as a secondary source and the session
records and `.claude.json` for their own rows, not `file-history/`, `paste-cache/` or `jobs/`; the
other agents' copies are read, if at all, under those agents (see [Secondary
sources](../analyzer/docs/output.md#secondary-sources)).

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
survive a session copy. Counts are observed lines:

| `type` | Loader class | Observed | Holds |
| --- | --- | --- | --- |
| `user` | transcript | 6,008 | a user turn: prompt, tool results, injected text |
| `assistant` | transcript | 9,911 | one content block of a model response |
| `system` | transcript | 318 | runtime notices, by `subtype` |
| `attachment` | transcript | 10,794 | context injected into the next request, by `attachment.type` |
| `progress` | boundary-cleared | 0 | streamed tool, hook and forked-agent progress (bundle: cc:482374, cc:482655, cc:483757, cc:482596) |
| `file-history-snapshot`, `file-history-delta` | boundary-cleared | 172, 25 | which files were backed up before edits, and the backup names |
| `last-prompt` | boundary-cleared | 602 | `lastPrompt` (text of the latest prompt), `leafUuid` |
| `continued-in` | boundary-cleared | 0 | `continuedInSessionId`, `timestamp` (cc:480715) |
| `content-replacement` | accumulate | 0 | `replacements`, optional `agentId` (cc:484029, cc:494705) |
| `api-request-shape`, `api-request-blob`, `api-request` | boundary-cleared | 0 | request capture; shape not determined |
| `fork-context-ref`, `frame-link` | accumulate | 0 | fork reference (cc:484031); artifact link `path`, `frameUrl`, `title`, `artifactCount`, `timestamp` (cc:504346) |
| `summary` | last-wins | 0 | legacy session summary `summary`, `leafUuid` (cc:484055) |
| `custom-title`, `ai-title` | last-wins | 0, 548 | `customTitle` (user-set name), `aiTitle` (generated name) |
| `tag`, `relocated` | last-wins | 0 | `tag`; `relocatedCwd`, written when the session's cwd moves (cc:484038) |
| `ended-by-model` | last-wins | 0 | `timestamp` only (cc:484055) |
| `agent-name`, `agent-color`, `agent-setting` | last-wins | 129, 0, 0 | `agentName`, `agentColor`, `agentSetting` |
| `pr-link` | last-wins | 221 | `prNumber`, `prUrl`, `prRepository`, `timestamp` |
| `mode`, `permission-mode` | last-wins | 608, 410 | `mode` (`normal` observed); `permissionMode` (`auto`, `plan` observed; `auto` in all 308 records on the 2.1.296 install). The permission mode is how tool calls are approved: `default` prompts, `acceptEdits` allows file edits, `plan` only plans, `bypassPermissions` allows everything, `dontAsk` denies what would prompt, `auto` lets a classifier decide (`claude 2.1.296 darwin-arm64 @187461122` `var CH=["acceptEdits","auto","bypassPermissions","default","dontAsk","plan"]`, with `manual` read as an alias for `default`; `@188412753` `if(e==="auto")return"classify";if(e==="bypassPermissions"\|\|_V(e,n))return"allow";if(e==="dontAsk")return"deny";return"ask"`). The record is `{type, permissionMode, sessionId}` with no `timestamp` (`@199803784` `type:"permission-mode",permissionMode:this.currentSessionPermissionMode,sessionId:y`) |
| `bridge-session` | last-wins | 256 | `bridgeSessionId`, `lastSequenceNum`, `ownerAccountUuid`, `ownerOrganizationUuid` |
| `atis-latch`, `cost-state`, `queue-operation` | last-wins | 607, 25, 488 | an opaque token; cumulative cost and per-model token usage; prompt queue changes |
| `isolation-latch`, `dev-mods`, `memory-mode`, `worktree-state`, `history-suppression`, `attribution-snapshot`, `artifact-comment-monitor`, `artifact-autoreact-ledger`, `observer-ref` | various | 0 | session state (cc:484021, cc:484022) |

Session-state records (`last-prompt`, titles, `agent-name`, `mode`, `permission-mode`, `atis-latch`,
`worktree-state`, `pr-link`, `frame-link`, `bridge-session`) are re-appended as a block whenever the
session's metadata is flushed (cc:484021, cc:484022). They carry `sessionId` and only `pr-link`,
`frame-link` and `queue-operation` carry a `timestamp`, which for `pr-link` is the time of the flush
(`timestamp:new Date().toISOString()` in the re-append), not of the pull request. Observed: one file
holds 105 `pr-link` lines for a single URL.

#### Transcript envelope

The envelope of `user`, `assistant`, `system` and `attachment` records (observed on every one unless
noted): `type`, `uuid` (UUID), `parentUuid` (UUID, or null on a chain root: observed on the first
transcript record of every file and on one `system` record), `timestamp` (ISO 8601 UTC,
milliseconds, `Z`; 27,061 of 27,061), `sessionId` (UUID), `cwd`, `gitBranch`, `version` (`2.1.NNN`),
`isSidechain` (false in session files, true in subagent files, 18,429 of 18,429), `userType`
(`external`), `entrypoint` (`cli` observed), optional `slug` (plan name), `agentId` (subagent files
only: equals the file's `agent-<id>`), and on some `user`, `assistant` and `attachment` records a
snake-case `session_id` ([Joins and timestamps](#joins-and-timestamps)).

#### `assistant` records

An `assistant` record adds `message` (the Messages API response object: `id`, `type:"message"`,
`role`, `model`, `content`, `stop_reason`, `stop_sequence`, `usage`, `container`,
`context_management`, `stop_details`, `diagnostics`, `input_transformations`), `requestId`,
`apiBlockIndex`, `effort`, `perTurnEffort`, `advisorModel`, `serverClassifierRequest`, optional
`thinkingDurationMs`, `requestedModel` (observed on macOS with CLI 2.1.295, 2026-10-11),
`attributionAgent`, `attributionSkill`, and per tool call `wireToolInputs` and `wireIngestContext`
([Wire inputs](#wire-inputs)) (observed; built at cc:482605). API failures are `assistant` records
with `isApiErrorMessage:true`, `error`, `apiErrorStatus`, `message.model` `<synthetic>` and one text
block holding the error (observed 10; cc:477488).

#### `user` records

A `user` record adds `message` (`role:"user"`, `content` string or block list), `promptId` (UUID),
and as applicable `isMeta`, `origin{kind, ...}`, `promptSource`, `turnOrigin`, `turnPosition`,
`permissionMode`, `toolUseResult`, `sourceToolAssistantUUID`, `serverClassifierContext`,
`isCompactSummary`, `isVisibleInTranscriptOnly`, `summarizeMetadata`, `interruptedMessageId`,
`toolDenialKind`, `userFeedback`, `queueSkipAttachments`, `queueTranscriptOnly` (the factory at
cc:483772 lists them; observed except the compaction fields).

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

#### `queue-operation` records

A `queue-operation` record has `operation` (`enqueue`, `dequeue`, `remove`), `timestamp`,
`sessionId`, and on `enqueue` and `remove` the queued `content`; optional `commandUuid`,
`deliveryId`, `reason` (observed).

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
`resolvedModel`, `outputFile`. On an error it is the error string (183 observed, all with
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
cc:474483); `toolUseResult.persistedOutputPath` names the file (37 observed).

#### Tool names

Tool names observed: `Bash`, `Read`, `Write`, `Edit`, `WebFetch`, `WebSearch`, `Agent`,
`SendMessage`, `SubagentHandback`, `ToolSearch`, `EnterPlanMode`, `ExitPlanMode`; MCP tools are
`mcp__<server>__<tool>` (cc:489602). Input keys observed: `command`, `description`, `timeout`,
`run_in_background` (Bash); `file_path`, `offset`, `limit` (Read); `file_path`, `content` (Write);
`file_path`, `old_string`, `new_string` (Edit); `url`, `prompt` (WebFetch); `query` (WebSearch);
`description`, `prompt`, `subagent_type`, `model`, `isolation` (Agent).

#### User-record kinds

A `user` record is not always typed by the person:

| Signal | Meaning | Observed |
| --- | --- | --- |
| `origin.kind:"human"`, `promptSource` `typed`, `queued` or `suggestion_accepted` | a prompt the person submitted | 165 |
| no `origin`, `parentUuid` null, first line of a subagent file | the task the parent agent gave the subagent | 80 of 80 subagent files |
| `origin.kind:"task-notification"`, content `<task-notification>...` | a background task's completion notice; `isMeta` absent in 62 of 66 | 66 |
| `origin.kind` `peer`, `coordinator`, `auto-continuation` | messages from other sessions or the runtime; `isMeta:true` | 65 |
| `isMeta:true`, `<system-reminder>` or `<local-command-caveat>` | injected context | 87 strings, 27 blocks |
| `<command-name>`, `<command-message>`, `<local-command-stdout>` | a slash command and its output; `isMeta` absent; the 27 `<command-message>` records also carry `origin.kind:"human"` and are counted above | 38 |
| `isCompactSummary:true` | the summary that replaces history after compaction, text starting "This session is being continued from a previous conversation" (cc:482588); built through the user-message factory without `isMeta` (cc:482593, cc:482597, cc:482598) | bundle |
| `tool_result` blocks | tool output | 5,512 |

A prompt typed while a turn runs is first a `queue-operation` `enqueue` with its `content`, then
either a `queued_command` attachment (delivered inside the running turn) or a later `user` record
with `promptSource:"queued"`. Observed: 11 `queued_command` attachments with `origin.kind:"human"`
whose text is in no `user` record of the file.

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
  in it; consistent with a resumed or forked session, purpose not determined.
- **Project path**: `cwd` on every transcript record; can change within a session (4 of 15 session
  files had more than one) and `relocated` records it (cc:484038); the directory `<key>` is lossy
  ([Where the project path is recorded](#where-the-project-path-is-recorded)).
- **Branch**: `gitBranch` on every transcript record (never empty observed; `HEAD` when detached is
  not determined); changes within a session (2 files).
- **Model**: `message.model` on `assistant` records (`claude-<family>-N-N` observed, `<synthetic>`
  for local errors); `requestedModel`, the model the request asked for
  (`claude 2.1.296 darwin-arm64 @198072824` `requestedModel:X.model`), equal to `message.model` on
  every 2.1.296 line observed; `model` attachment `identity.modelId`; `cost-state.modelUsage` keys.
  A `/model` switch is a `user` line `<command-name>/model</command-name>` followed by a `user`
  line with the command output, built from `@199593943`
  `var fle="Set model to ",gne=" and saved as your default for new sessions"`; observed on 2.1.296
  as
  ``<local-command-stdout>Set model to `<display name>` and saved as your default for new sessions</local-command-stdout>``.
  The parser keeps it as `command output:` and marks the change itself from `message.model`.
- **Subagents**: the parent's `Agent` `tool_use.id` equals the subagent's `.meta.json` `toolUseId`,
  and the parent's `toolUseResult.agentId` equals the file's agent id (76 of 76 non-fork subagents).
  Forked agents (`agentType:"fork"`, 4) have a `toolUseId` that is not in the parent transcript.
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
placeholder. Every observed `pastedContents` was empty. `paste-cache/` is excluded
([Exclusions](#exclusions)); what the history outlives is under
[What survives a delete](#what-survives-a-delete).

#### File-history records

`file-history-snapshot` and `file-history-delta` records name the files backed up before each edit
(`snapshot.trackedFileBackups` keyed by path,
`backup{backupFileName, backupTime, version, realParentDir}`); the bytes are in
`.claude/file-history/<session id>/`. The paths in `trackedFileBackups` are files the agent edited,
which no other record lists in one place.

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

#### Remote Control

Remote Control lets another device (claude.ai or the mobile app) drive a local Claude Code process
through a bridge. The evidence is the 2.1.295 Linux binary of
[Source and evidence](#source-and-evidence) and the Ubuntu lab install of 2026-10-11
([Observed](#observed)).

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
  outlive a crashed process until the housekeeping sweep (`.last-cleanup`), so pair the claim with
  the EDR's process list.
- **Transcript lines.** `turnOrigin` takes one of `@215584535`
  `var zLt=["human","sdk","scheduled","task_notification","auto_continuation","peer","host_synthetic","system","unknown"]`;
  no value names Remote Control, and a `remote-restart-auto-resume` wake-up maps to
  `auto_continuation` (`@215585139`
  `case"remote-restart-auto-resume":case"ci-monitor":return"auto_continuation"`). The CLI derives
  `{kind:"bridge"}` for a human prompt sent over the bridge (`@214818778`
  `function Ioe(e,n){switch(e.kind){case"human":return n===!0?{kind:"bridge"}:{kind:"composer"}`),
  but that value was seen only feeding the hook path; the observed transcript lines carry
  `origin:{kind:"human"}`. Whether a bridge prompt is marked on the transcript line is not
  determined.
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
- Compaction (`compact_boundary` plus a `user` record with `isCompactSummary`) and `relocated` were
  not observed.
- No compressed or archived transcript form exists; deletion by `cleanupPeriodDays` is the only
  rotation.

### Secrets

- `~/.claude.json`, the global config: `oauthAccount` (the sign-in session) and the MCP server
  definitions' `env` blocks and headers, globally and under `projects.<path>.mcpServers`. The
  parser reads only its permission keys ([Permission configuration](#permission-configuration)).
- The settings files: `env` (such as `env.ANTHROPIC_API_KEY`), `apiKeyHelper`, hooks and MCP server
  settings and headers; the parser never reads them.
- Identity inside the transcript: the `session_context` attachment carries
  `context{userEmail, gitStatus}`, `credential_org` an `organizationUuid`, and `bridge-session`
  records `ownerAccountUuid` and `ownerOrganizationUuid` ([Record schema](#record-schema)).
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
| `user`, `tool_result` block | `tool_result`; `tool_reference` blocks as their `tool_name`; a `<persisted-output>` stub replaced by its `tool-results/` file (below); text prefixed `[error]` when `is_error` |
| `user`, `permissionDecision` (2.1.295) | one `system` row after the line's `tool_result` rows, `permission decision: <decision> source=<source> reason=<reasonType>` (`-` for a missing key), then a space and the object's compact JSON when it has other keys; `tool_use_id` of the line's first `tool_result` block, `tool_name` empty as on `tool_result` rows |
| `user`, `toolDenialKind`, `userFeedback` (factory key list, [Record schema](#record-schema)) | appended to that line's `permission decision:` row as ` toolDenialKind=<value> userFeedback=<value>`, in that order, each only when set, printed as recorded (no value set is recorded; `userFeedback` is free text, so it comes last); a line with either key and no `permissionDecision` gets the row with `-` for `decision`, `source` and `reasonType` ([issue 97](https://github.com/seanthegeek/doubleagent/issues/97)) |
| `attachment` `plan_mode`, `plan_mode_exit`, `plan_mode_reentry`, `auto_mode` | skip: they are timestamped mode changes, but their field shapes are not recorded in this document, so the parser does not read them |
| `user`, `turnOrigin`, `promptSource`, `origin` (2.1.295 prompt keys) | no row; `origin.kind` still picks the label above, the others change nothing |
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
| `sessions/<pid>.json` | one `system` row at `startedAt` (epoch ms), `claude-code process <pid> <kind> status=<status> entrypoint=<entrypoint> bridge=<bridgeSessionId or none> host_session=<hostSessionId or none>` (`-` for a missing `kind`, `status` or `entrypoint`), `session_id` `sessionId`, `project_path` `cwd`, `source_line` 1; a file that is not a JSON object is one `system` row `parser: session registry file is not a JSON object`. A `bridge=` value means the process was under Remote Control when the collector ran ([Remote Control](#remote-control)) |
| `settings.json`, `settings.local.json` (user, `.claude-<name>`, or a project's) | one `system` row per `permissions.allow`, `deny`, `ask` and `additionalDirectories` entry, then one for `permissions.defaultMode` and `permissions.disableBypassPermissionsMode` when set: `permission setting: permissions.<key>=<value> (from <path relative to the home or project>, file mtime)`, a non-string value as compact JSON; `timestamp_utc` the manifest `mtime`, else the file's own; `session_id` empty; `project_path` the project directory for a `project` artifact, else empty; `source_line` 1; no other key read; a file that is not a JSON object is one `system` row `parser: settings file is not a JSON object` |
| `.claude.json`, `.claude-<name>/.claude.json` | per `projects.<path>`: one row per `allowedTools` entry, then one each for `hasTrustDialogAccepted` and `hasClaudeMdExternalIncludesApproved` when present, `permission setting: <key>=<value> (from .claude.json, file mtime)`, `project_path` the `<path>` key, times as above; nothing else in the file is read (it holds the account's OAuth details); `.claude.json.backup*` is not wanted |

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
`serverClassifierContext`, and the `claude-cli-nodejs` MCP logs
([CLI cache directory](#cli-cache-directory)), whose lines name the session, the project and a
time, so each `debug` message could become a `system` row joined to the session.

#### Permission rows

Per-call decisions are the `permission decision:` rows of `permissionDecision`, `toolDenialKind`
and `userFeedback` ([issue 97](https://github.com/seanthegeek/doubleagent/issues/97)), the mode the
`permission mode:` rows, and the standing grants the `permission setting:` rows of the settings
files and `.claude.json` ([issue 93](https://github.com/seanthegeek/doubleagent/issues/93)); the
coverage table has the exact texts, [Record schema](#record-schema) and
[Permission configuration](#permission-configuration) the records. The `plan_mode`,
`plan_mode_exit`, `plan_mode_reentry` and `auto_mode` attachments are not read.

#### Model rows

The `model:` rows come from `message.model` and `requestedModel` (the `assistant` row of the
coverage table). A `/model` switch keeps its own `slash command` and `command output` rows
([Joins and timestamps](#joins-and-timestamps)). The `model` attachment and `cost-state` records are
not read.

#### Past-use rows and secondary sources

`.claude/history.jsonl` is read on every run as a secondary source of the transcripts, one `user`
row per line ([`history.jsonl`](#historyjsonl)); it usually outlives its transcript ([What survives
a delete](#what-survives-a-delete)). The `sessions/<pid>.json` registry and the permission settings
yield rows of their own. Not read: `file-history/`, `paste-cache/`, `jobs/`, the `.meta.json`
sidecars and the `claude-cli-nodejs` MCP logs.

#### Sync, relay and origin rows

Not stated. The `bridge=` value of a `sessions/<pid>.json` row says the process was under Remote
Control, another device driving it, when the collector ran ([Remote Control](#remote-control));
`bridge-session` records are not read.

#### Scratch directory rows

Not stated.

#### Deletion rows

Not stated; no deletion marker is stated ([What survives a delete](#what-survives-a-delete)).

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

#### Forked subagents

A forked subagent's file begins with a copy of the forking agent's context (observed in the 4 fork
files: the records before the `<fork-boilerplate>` one have new `uuid`s, and their tool ids are in
no session file), so no boundary ties those records to their source; their rows are kept, the first
`user` record stays `user`, and the `<fork-boilerplate>` block is the `subagent task` row.

#### Persisted output files

When a `tool_result` text starts with `<persisted-output>`, the parser takes the path after
`Full output saved to: `, keeps its last component and requires the component before `tool-results`
to equal the transcript's session directory (`<session id>/` beside a session file, the directory
above `subagents/` for a subagent file). It reads `<session dir>/tool-results/<name>` when neither
the file, `tool-results/` nor the session directory is a symlink, and otherwise keeps the stub
followed by `[persisted output not found: tool-results/<name>]`. On the observed install every stub
resolved.

## Confidence

- High (bundle literals plus docs, layout confirmed locally): config-dir resolution, directory and
  file name sets, the `projects/` key scheme and transcript naming, keychain service construction,
  `.credentials.json`, managed paths, native installer paths.
- High (bundle, corroborated by claude-mem source): `.claude.json` inside a relocated config home;
  and that claude-code-router, claude-mem and claude-squad keep nothing at their roots that the
  `.claude-*/` lines collect (source at the linked commits).
- High (observed and consistent with the bundle): the record type list, the transcript envelope,
  one block per `assistant` record, the `tool_use`/`tool_result` join, `toolUseResult`,
  `sourceToolAssistantUUID`, `wireToolInputs`/`wireIngestContext` and the stripped `cd` prefix,
  `user`-record origins and the subagent first-line prompt, the subagent join through `.meta.json`,
  millisecond ISO timestamps, epoch-millisecond history, empty thinking with signature, `pr-link`
  re-append, `queued_command` prompts.
- High (observed on macOS and Linux with 2.1.295 and 2.1.296): the `sessions/<pid>.json` registry
  keys, `requestedModel`, and the `permission-mode` records; the permission configuration key
  names (observed by name only).
- Medium: the exact keychain service string (built from `"Claude Code"` + `"-credentials"`; not seen
  as one literal); contents of `storage-v2`, `seed-admin`, `remote`, `systemd`, `daemon` (names
  only).
- Medium (bundle only, not exercised): `compact_boundary` and `isCompactSummary` shapes,
  `api_error`, `memory_saved`, `relocated`, `continued-in`, `ended-by-model`,
  `content-replacement`, `frame-link`, `summary`, `progress`, nested subagent subdirectories,
  `paste-cache` storage of pasted text; the CLI cache directory on Linux and Windows.
- Not determined: how common config-home names other than `.claude-<name>` are; other `.claude-`
  prefixed tools beyond the three checked; whether `.claude.json` suffix variants
  (`.claude<suffix>.json`) appear on normal installs; Windows-only paths beyond
  `%USERPROFILE%\.claude` (none found); size of `dump-prompts` in practice.
- Not determined: the meaning of a `session_id` that differs from `sessionId`; the shape of
  `api-request*`, `fork-context-ref`, `content-replacement.replacements[]` and
  `history-suppression`; whether `redacted_thinking`, `server_tool_use` or `image` blocks still
  appear in 2.1.x transcripts; `gitBranch` for a detached head or outside a repository; the layout
  before 2.1.286; the Windows transcripts, which rest on the bundle and docs alone; whether a prompt
  sent over Remote Control is marked on its transcript line ([Remote Control](#remote-control)).
