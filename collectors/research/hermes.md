# Hermes Agent: on-disk paths

Catalog agent: `hermes`. Transcript schema is in
[`analyzer/research/hermes.md`](../../analyzer/research/hermes.md).

## 1. Source and evidence level

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), MIT ([`LICENSE`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/LICENSE#L1-L3)), open source, Python with an Electron desktop app,
commit [`8b66a51036c1e20920a17cdd049fdf55c968d683`](https://github.com/NousResearch/hermes-agent/commit/8b66a51036c1e20920a17cdd049fdf55c968d683).
All claims are from source; the documented home layout in
[`website/docs/user-guide/configuration.md:22-31`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/website/docs/user-guide/configuration.md#L22-L31)
agrees with it. Nothing was installed or run.

- **Source review (2026-10-19)** at
  [`86fa9e6ca1de7ee71132d2be0103f3e37d1fa872`](https://github.com/NousResearch/hermes-agent/commit/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872)
  (HEAD of 2026-10-19), against the
  [`8b66a51036c1e20920a17cdd049fdf55c968d683`](https://github.com/NousResearch/hermes-agent/commit/8b66a51036c1e20920a17cdd049fdf55c968d683)
  (2026-10-04) cited above. Nothing installed or run; no real install has
  been observed. Collector-side findings: the prompt history
  `.hermes_history` and the cron run archive `cron/output/` are under the
  home and collected ([section 2](#2-per-user-storage)); the pairing
  files' shape is known and they are the gateway's standing grants
  ([section 3](#3-credentials)); the scratch directories are
  `cache/scratch/` (collected) and `sandboxes/` (excluded) under the home
  and `.worktrees/<name>` inside a project, recorded in `sessions.cwd`
  ([section 2](#2-per-user-storage),
  [section 6](#6-where-the-project-path-is-recorded)); every path the
  catalog names is unchanged at HEAD. Permission, model, sync, relay,
  deletion, drift and bad-line findings for the parser are in
  [section 1 of `analyzer/research/hermes.md`](../../analyzer/research/hermes.md#1-source).

## 2. Per-user storage

**Home resolution.** Context override, then `HERMES_HOME`, then the platform
default ([`hermes_constants.py:111-118`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_constants.py#L111-L118)): `~/.hermes` on Linux and macOS,
`%LOCALAPPDATA%\hermes` (fallback `~/AppData/Local/hermes`) on Windows, each
with an optional `HERMES_DATA_DIR_SUFFIX` appended
([`hermes_constants.py:51-58`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_constants.py#L51-L58)). The Windows desktop app keeps using a
legacy `~/.hermes` when `%LOCALAPPDATA%\hermes` does not exist
([`apps/desktop/electron/data-paths.mjs:26-33`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/apps/desktop/electron/data-paths.mjs#L26-L33),[`56-65`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/apps/desktop/electron/data-paths.mjs#L56-L65)), so both
forms occur on Windows. No XDG paths.

**Profiles.** Named profiles are complete homes under `<root>/profiles/<name>/`
([`hermes_cli/profiles.py:287-297`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/profiles.py#L287-L297)); every path below can also appear one
level down under `profiles/*/`.

**Docker.** The compose file bind-mounts the host `~/.hermes` to
`/opt/data` ([`docker-compose.yml:36-37`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/docker-compose.yml#L36-L37)), so container
deployments still leave state in the host home.

**Contents of the home** (relative to it):

- `state.db` with `-wal`/`-shm`: the session and message store, canonical for
  CLI, gateway and desktop ([`hermes_state.py:176`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state.py#L176)).
- `sessions/`: `sessions.json` gateway routing index
  ([`hermes_state_schema.py:1311`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_schema.py#L1311)); `<id>.jsonl` fallback
  transcripts written when `state.db` was replaced under a live process
  ([`hermes_state.py:429-444`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state.py#L429-L444)); legacy `<id>.json` and
  `session_<id>.json` snapshots, and `request_dump_<id>_*.json` API error
  dumps ([`hermes_state_sessions.py:1573-1585`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_sessions.py#L1573-L1585),
  [`agent/agent_runtime_helpers.py:1628`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/agent_runtime_helpers.py#L1628)); `saved/hermes_conversation_<ts>.{json,md,html}`
  from `/save` ([`hermes_cli/cli_session_mixin.py:677-689`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/cli_session_mixin.py#L677-L689)).
- `session-exports/`: default output of `hermes sessions export`
  ([`hermes_cli/sessions_cmd.py:74-76`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/sessions_cmd.py#L74-L76)).
- `config.yaml`, `.env`, `SOUL.md` (agent identity), `skills/`
  ([`hermes_constants.py:1190-1202`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_constants.py#L1190-L1202)); `memories/MEMORY.md` and
  `memories/USER.md` ([`tools/memory_tool.py:38-40`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/tools/memory_tool.py#L38-L40),
  [`tools/memory_tool_store.py:212`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/tools/memory_tool_store.py#L212)).
- `logs/agent.log`, `errors.log`, `gateway.log`
  ([`AGENTS.md:247-248`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/AGENTS.md#L247-L248)).
- Other SQLite stores the backup code treats as user data: `cron/jobs.json`,
  `cron/executions.db`, `projects.db`, `response_store.db` (API-server
  conversation history and tool payloads), `memory_store.db`,
  `verification_evidence.db`, `kanban.db`, `kanban/boards`
  ([`hermes_cli/backup.py:1061-1072`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1061-L1072)); cron output under `cron/output`
  ([`cron/jobs.py:110`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/cron/jobs.py#L110)).
- `checkpoints/`: one shared shadow git store; `store/projects/<hash16>.json`
  records `workdir` ([`tools/checkpoint_manager.py:13-25`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/tools/checkpoint_manager.py#L13-L25),[`74`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/tools/checkpoint_manager.py#L74)).
- `state-snapshots/<id>/` (up to 20 copies of `state.db`, `.env`, `auth.json`
  and the other stores) and `backups/` (pre-update and pre-migration zips, 5
  each) ([`hermes_cli/backup.py:1061-1062`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1061-L1062),[`1079-1084`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1079-L1084),[`1120-1124`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L1120-L1124)).
- `cache/terminal` (spilled tool results, background-process logs) and
  `cache/scratch` (`TMPDIR` of every child process)
  ([`configuration.md:240-256`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/website/docs/user-guide/configuration.md#L240-L256)).
- `hermes-agent/`: the installer's git checkout and venv
  ([`scripts/install.sh:79`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/scripts/install.sh#L79),
  [`scripts/install.ps1:23-24`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/scripts/install.ps1#L23-L24)).
- `.hermes_history`: the prompt history of the CLI and the TUI, every
  typed line with a timestamp (2026-10-19 HEAD,
  [`hermes_cli/cli_init_mixin.py:389`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/cli_init_mixin.py#L389),
  [`ui-tui/src/lib/history.ts:6-7`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/ui-tui/src/lib/history.ts#L6-L7)). Collected; the
  profile export leaves it out, with `state.db` and `response_store.db`
  ([`hermes_cli/profiles.py:241`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/profiles.py#L241)).
- `cron/output/<job id>/<YYYY-mm-dd_HH-MM-SS>.md`: one Markdown file per
  cron run with the prompt and the response
  ([`cron/jobs.py:3384-3395`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/cron/jobs.py#L3384-L3395)). Collected.
- `pairing/<platform>-approved.json` and `-pending.json`: the messaging
  gateway's approved and pending users
  ([`gateway/pairing.py:353-356`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/pairing.py#L353-L356)), see
  [section 3](#3-credentials).

**Scratch directories** (2026-10-19 HEAD). `cache/scratch/<entry>` is
the `TMPDIR` of every child process, reaped when idle
([`hermes_constants.py:957`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_constants.py#L957),
[`hermes_constants_scratch.py:1-6`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_constants_scratch.py#L1-L6)); it is under the
catalog's `.hermes` entry and collected. `sandboxes/` (or
`TERMINAL_SANDBOX_DIR`) holds the container backends' persistent bind
mounts, `sandboxes/docker/<task>` for Docker
([`tools/environments/base.py:189-191`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/environments/base.py#L189-L191),
[`tools/environments/docker.py:856`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/environments/docker.py#L856)); it is excluded
([section 4](#4-exclusions)). The worktrees the agent creates are inside
the user's repository, not the home
([section 6](#6-where-the-project-path-is-recorded)). The analyzer's
catalog rule classes any path under the Hermes home as a scratch
directory.

**Started by another agent** (Agent Zero source review of 2026-10-19, at [`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a)). Agent Zero's Orchestrator plugin, which tells that agent how to drive other coding CLIs on the host or in its container, defaults Hermes to `yolo: true` and runs `hermes chat --quiet --source tool -q <task> --yolo`, which bypasses every dangerous-command approval prompt for the run ([`hermes_cli/_parser.py:307-308`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/_parser.py#L307-L308); [`plugins/_orchestrator/default_config.yaml:7-37`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_orchestrator/default_config.yaml#L7-L37), [`plugins/_orchestrator/skills/orchestrator/references/hermes.md:16`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_orchestrator/skills/orchestrator/references/hermes.md#L16)). Such a session is an ordinary session in this home's `state.db`, started by another agent with approvals bypassed; the plugin's permission settings are in [section 8 of `analyzer/research/agent-zero.md`](../../analyzer/research/agent-zero.md#8-parser-plan).

**Desktop app.** Electron `productName` is `Hermes`
([`apps/desktop/package.json:3`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/apps/desktop/package.json#L3)), so its `userData` is the Electron default
`Hermes` directory, overridable by `HERMES_DESKTOP_USER_DATA_DIR`
([`data-paths.mjs:35-39`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/apps/desktop/electron/data-paths.mjs#L35-L39)). It holds `connection.json`, `connections.json`,
`active-profile.json` and window state
([`apps/desktop/electron/main.ts:1222`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/apps/desktop/electron/main.ts#L1222),[`1331-1341`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/apps/desktop/electron/main.ts#L1331-L1341)); conversations stay in `state.db`.

## 3. Credentials

Hermes keeps its own authoritative list, `PROFILE_CREDENTIAL_PATHS`
([`hermes_cli/profiles.py:155-188`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/profiles.py#L155-L188)), relative to each profile home:
`auth.json` (OAuth provider credentials and credential pool), `.env` (API
keys, platform bot tokens), `auth/google_oauth.json`, `.op.env` (1Password
service-account token), `npmrc`, `.anthropic_oauth.json`,
`google_token.json`, `google_client_secret.json`,
`google_oauth_pending.json`, `google_chat_user_tokens/`,
`google_chat_user_*.json`, `slack_tokens.json`, `honcho.json`, `mem0.json`,
`webhook_subscriptions.json` (HMAC secrets), `teams_pipeline_store.json`,
`mcp-tokens/`, `vault/` (`vault.key` beside `vault.json.enc`), browser
profiles (`browser-profile`, `browser_auth`, `bot-desktop`,
`browser-profiles`, `browser_profiles`, `chrome-debug`), pairing stores,
`whatsapp/session`, `matrix/store` (both also under `platforms/`),
`cache/bws_cache*.json` (Bitwarden plaintext cache), `weixin/accounts`,
`.copilot_jwt.json`, `runtime/photon-sidecar.json`, `proxy/` (CA key),
`home/` (the subprocess `HOME` in containers: gh, git, ssh, npm credentials,
[`hermes_constants.py:695-718`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_constants.py#L695-L718)), and `backups`, `state-snapshots`. Copies
named `auth.json.*` and `.env.bak*` are also credential stores
([`profiles.py:189-195`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/profiles.py#L189-L195)).

The pairing files are also standing permission state: at the 2026-10-19
HEAD `pairing/<platform>-approved.json` is a JSON object keyed by the
platform user id, each `{user_name, approved_at}` (epoch seconds), the
users the bot owner approved to drive the agent from that platform
([`gateway/pairing.py:1-7`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/pairing.py#L1-L7),
[`gateway/pairing.py:431-437`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/gateway/pairing.py#L431-L437)); the shape is the same
at the cited commit. They stay flagged secret, since a pending file
holds live pairing codes. `hermes sessions export --format trace
--upload` takes a Hugging Face token from `HF_TOKEN` or three alternate
variable names in the environment
([`agent/trace_upload.py:36`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/trace_upload.py#L36),
[`agent/trace_upload.py:170-172`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/agent/trace_upload.py#L170-L172)), which the setup
message tells the user to put in `.env`; `.env` is already flagged.

The installer checkout's own `hermes-agent/.env` is loaded as a fallback
([`cli.py:337-338`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/cli.py#L337-L338), [`hermes_cli/env_loader.py:455-462`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/env_loader.py#L455-L462)), so it can hold keys
inside an otherwise excluded tree. `config.yaml` is for non-secret settings
and `.env` is required for secrets
([`configuration.md:62-63`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/website/docs/user-guide/configuration.md#L62-L63)). No OS keychain for Hermes' own
secrets; secret managers (1Password, command sources) are pluggable.

Tool-call arguments are deliberately not redacted before they reach
`state.db` ([`agent/chat_completion_helpers.py:1640-1649`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/chat_completion_helpers.py#L1640-L1649)), so the session
database can contain credentials typed into commands. Collect it unflagged.

## 4. Exclusions

Hermes' own backup exclusions are the best guide
([`hermes_cli/backup.py:72-92`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L72-L92),[`94`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L94),[`99`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/backup.py#L99)):
`hermes-agent` (code checkout), `models`, `runtimes`, `node` (GGUF models,
llama.cpp, Node, "tens to hundreds of GB",
[`hermes_constants.py:205-209`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_constants.py#L205-L209)), `installs` and `tools`
([`hermes_cli/home_data_layout.py:5-6`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/home_data_layout.py#L5-L6)), `checkpoints` (shadow git), live
Chromium profiles, `node_modules`, `.venv`, `site-packages`, `sandboxes`
([`tools/environments/base.py:191`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/tools/environments/base.py#L191)). Keep `checkpoints/store/projects/*.json`
for discovery.

`state-snapshots/` and `backups/` are large but hold older copies of
`state.db`. Sessions are pruned after 90 days of inactivity by default
([`hermes_cli/config_defaults.py:2276-2285`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/config_defaults.py#L2276-L2285)), so these copies may be the only
record of deleted sessions. The catalog excludes them by default; use
`--full` when deletion is suspected. They also contain `.env` and
`auth.json`. `cache/` is not excluded: `cache/terminal` holds tool output.

At the 2026-10-19 HEAD automatic pruning is off by default
([`hermes_cli/config_defaults.py:2279-2289`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/config_defaults.py#L2279-L2289)), so on a
current install a session is gone from `state.db` only when the user
deleted or pruned it, and a deleted session leaves a tombstone in
`state.db` itself (see
[section 5 of `analyzer/research/hermes.md`](../../analyzer/research/hermes.md#5-sqlite-specifics)).
`sandboxes/` stays excluded: a container backend's persistent workspace
can hold whole repositories, and the commands that ran there are in
`state.db`.

The installer checkout is excluded entry by entry rather than as one
directory (`hermes-agent/[!.]*` and `hermes-agent/.[!e]*`), because an
exclusion wins over a secret glob: pruning the whole tree would lose
`hermes-agent/.env`, which is collected and flagged. The exclusion and
secret globs are anchored to `.hermes*/` and `AppData/Local/hermes*/`, so
they cover profiles and suffixed homes without matching unrelated paths.

## 5. Project-local files

- `.hermes.md` or `HERMES.md`, nearest from cwd up to the git root
  ([`agent/prompt_builder.py:140-149`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/prompt_builder.py#L140-L149)); also reads `AGENTS.override.md`,
  `AGENTS.md`, `agents.md`, `CLAUDE.md`, `claude.md`, `.cursorrules`,
  `.cursor/rules/*.mdc` ([`prompt_builder.py:1676`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/prompt_builder.py#L1676),[`1691`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/prompt_builder.py#L1691),[`1700-1706`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/prompt_builder.py#L1700-L1706)).
- `.hermes/`: `skills/` ([`agent/skill_utils.py:496`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/skill_utils.py#L496)), `plugins/`
  ([`hermes_cli/plugins_discovery.py:213`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/plugins_discovery.py#L213)), `plans/<date>-<slug>.md`
  ([`agent/plan_prompt.py:21`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/plan_prompt.py#L21)), `environment.json`
  ([`agent/verify/environment.py:17`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/verify/environment.py#L17)); `.agents/skills` is also read.
- `trajectory_samples.jsonl` and `failed_trajectories.jsonl` in the cwd when
  `--save-trajectories` is given ([`agent/trajectory.py:37-44`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/trajectory.py#L37-L44),
  [`agent/legacy_cli.py:50`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/agent/legacy_cli.py#L50)). No per-project database.

## 6. Where the project path is recorded

- `checkpoints/store/projects/<hash16>.json`, key `workdir`
  ([`tools/checkpoint_manager.py:615-619`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/tools/checkpoint_manager.py#L615-L619)). Grep-able JSON; only present when
  checkpoints are enabled.
- `state.db` table `sessions`, columns `cwd`, `git_repo_root`, `git_branch`
  ([`hermes_state_common.py:409-411`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_state_common.py#L409-L411)). SQLite only.
- `projects.db` tables `projects.primary_path` and `project_folders.path`
  ([`hermes_cli/projects_db.py:29-49`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/hermes_cli/projects_db.py#L29-L49)). SQLite only.
- Worktrees the agent creates (2026-10-19 HEAD):
  `<repo>/.worktrees/<name>` on branch `hermes/<name>` for `hermes -w`,
  and `.worktrees/subagent-<id>` on `hermes-subagent/<name>` for
  delegated subagents
  ([`hermes_cli/worktree_ops.py:435-441`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/worktree_ops.py#L435-L441),
  [`tools/subagent_worktree.py:81-96`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/tools/subagent_worktree.py#L81-L96)). The session
  runs in the worktree, so `sessions.cwd` is the worktree path
  ([`hermes_cli/worktree_ops.py:822-825`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/worktree_ops.py#L822-L825)), and a
  retained TUI worktree is locked with the reason
  `hermes session=<id> db=<path>`
  ([`hermes_cli/worktree_ops.py:805-815`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/worktree_ops.py#L805-L815)). These are
  scratch directories inside a project: the project catalog collects the
  repository's `.hermes/` files, not `.worktrees/`.

## 7. Confidence

High: home resolution, profile layout, `state.db` and every file named in
[section 2](#2-per-user-storage) and [section 3](#3-credentials) (source constants). High: backup exclusion list as a guide to
size. Medium: the desktop `userData` path, which follows the Electron default
from `productName` rather than an explicit `setPath` for stable builds
([`apps/desktop/electron/product-identity.ts:26-47`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/apps/desktop/electron/product-identity.ts#L26-L47)). The `*hermes*`
prefixes first proposed for the exclusion and secret globs were tightened to
`.hermes*/` and `AppData/Local/hermes*/` at integration. Not
determined: the exact sizes of `state-snapshots` and `cache/scratch` on a
real install; the format of `auth.json` beyond "OAuth provider credentials"
([`configuration.md:25`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/website/docs/user-guide/configuration.md#L25)); Termux installs, which come from APT
([`scripts/install.sh:340`](https://github.com/NousResearch/hermes-agent/blob/8b66a51036c1e20920a17cdd049fdf55c968d683/scripts/install.sh#L340)) and were not checked.
