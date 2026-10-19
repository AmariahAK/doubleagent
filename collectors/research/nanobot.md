# nanobot

nanobot is a small personal-assistant agent with a CLI, a WebUI and a gateway that connects chat
channels (Telegram, Discord, Feishu, WhatsApp, Matrix, QQ, WeChat and others under
`nanobot/channels/`); it is open source, written in Python, and not a fork of another agent.
This document covers where it keeps state on disk; the transcript schema is in
[`analyzer/research/nanobot.md`](../../analyzer/research/nanobot.md).

## 1. Source and evidence

[HKUDS/nanobot](https://github.com/HKUDS/nanobot), commit [`acdae3d0ae2714b6dde672428e921dbf705c096f`](https://github.com/HKUDS/nanobot/commit/acdae3d0ae2714b6dde672428e921dbf705c096f)
(2026-10-04, PyPI package `nanobot-ai` version `0.3.5`, [`pyproject.toml:2-3`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/pyproject.toml#L2-L3)), MIT
([`LICENSE`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/LICENSE)), open source, Python. Every claim is source-level unless it
cites `docs/` in the same checkout.

### Observed

- No real install.

### Source reviews

- **Source review (2026-10-19)** at
  [`909b277`](https://github.com/HKUDS/nanobot/commit/909b277e7a5a7ecd2aebdba9611e5febe86988d9)
  (2026-10-19, still `0.3.5` in `pyproject.toml`), against the
  [`acdae3d`](https://github.com/HKUDS/nanobot/commit/acdae3d0ae2714b6dde672428e921dbf705c096f)
  above; source only. Per class, with the detail in
  [section 2](#2-per-user-storage), [section 3](#3-credentials) and
  [section 6](#6-where-the-project-path-is-recorded), and the parser side
  in
  [section 1 of `analyzer/research/nanobot.md`](../../analyzer/research/nanobot.md#1-source-and-evidence):
  - Permission state: found; `config.json` `tools` and `allowFrom`
    settings, `pairing.json` (shape now traced) and the per-session
    `workspace_scope`; all under `.nanobot*`, so collected.
  - Model: covered (preset in session metadata; `llm_usage.sqlite3`).
  - Past use: drift. Sessions moved into
    `sessions/<workspace-id>/sessions.sqlite3`; also new
    `jsonl-backup/`, `.webui_session_index.json`, and workspace
    `cron/runs/` and `triggers/`. All under `.nanobot*` when the
    workspace is the default.
  - Sync, relay and origin: relay only, recorded in the session key and
    `metadata.last_channel`; nothing new for the collector.
  - Scratch directories: the default workspace and the Docker
    `api-workspace` are under `.nanobot`, collected; a `--home` instance
    root outside `.nanobot*` is not.
  - Deletion: covered in the analyzer document.
  - Version drift: found; SQLite session store, a `--home` option for
    the instance root, `.workspace-migration.lock` in the sessions root.
  - Bad lines: not a collector concern.

## 2. Per-user storage

All paths derive from `Path.home()`, so the layout is `~/.nanobot` on Linux and
macOS and `%USERPROFILE%\.nanobot` on Windows; there is no XDG, Library or
AppData branch. The config file is `~/.nanobot/config.json` unless
`--config` selects another ([`nanobot/config/loader.py:20-39`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/loader.py#L20-L39)), and the
instance data directory is the config file's parent
([`nanobot/config/paths.py:20-27`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L20-L27)). The documented multi-instance pattern
is `~/.nanobot-<name>/config.json` with its own workspace
([`docs/multiple-instances.md:13-20`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/docs/multiple-instances.md#L13-L20)). Settings can also come from
`NANOBOT_*` environment variables ([`config/schema.py:665-668`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L665-L668)).

Under the data directory:

- `config.json`: providers, channels, MCP servers, agent defaults ([section 3](#3-credentials)).
- `sessions/<workspace-id>/`: one directory per workspace, named by a 32-hex
  id, holding a `.workspace` marker file with the workspace path,
  `<base64url(session key)>.jsonl` transcripts, `<...>.checkpoint.json`
  runtime overlays, `.session-files.lock` and `.migration-conflicts/`
  ([`nanobot/session/manager.py:58-76`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L58-L76),[`448-477`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L448-L477),[`606-607`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L606-L607),[`777-779`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L777-L779),[`903-927`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L903-L927)).
- `webui/`: WebUI display transcripts `<key>.jsonl`, `<key>.segments/` with
  `manifest.json`, legacy `<key>.json`, plus `workspace-state.json`,
  `sidebar-state.json` ([`nanobot/webui/transcript.py:172-188`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/transcript.py#L172-L188); [`webui/workspaces.py:45`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/workspaces.py#L45); [`webui/sidebar_state.py:37`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/sidebar_state.py#L37)).
- `cron/jobs.json` (legacy location, [`nanobot/cli/runtime_config.py:195-196`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/runtime_config.py#L195-L196)), `logs/`,
  `media/<channel>/` received attachments ([`config/paths.py:30-48`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L30-L48)).
- `llm_usage.sqlite3`: table `llm_calls` with provider, model and UTC
  epoch-ms timestamps for every model call, WAL mode
  ([`nanobot/llm_usage/__init__.py:42`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/llm_usage/__init__.py#L42); [`llm_usage/store.py:190-222`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/llm_usage/store.py#L190-L222)).
- `pairing.json`: approved chat senders ([`nanobot/pairing/store.py:3`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/pairing/store.py#L3),[`33`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/pairing/store.py#L33)).
- `auth/xai.json`, `auth/mcp.json` ([section 3](#3-credentials)), `whatsapp-auth/neonize.db`,
  `matrix-store/`, `weixin/`, `mochat/`, `linear/state.sqlite3` channel state
  ([`channels/whatsapp/runtime.py:75`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/whatsapp/runtime.py#L75); [`channels/matrix/runtime.py:354`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/matrix/runtime.py#L354); [`channels/weixin/runtime.py:378`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/weixin/runtime.py#L378); [`channels/mochat/runtime.py:283`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/mochat/runtime.py#L283); [`channels/linear/state.py:44`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/linear/state.py#L44)).
- `mcp/<name>/` working directories for MCP presets ([`webui/mcp_presets_api.py:563`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/webui/mcp_presets_api.py#L563)),
  `cli-apps/` ([`apps/cli/service.py:428`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/apps/cli/service.py#L428)).
- `cache/tiktoken/`, `bin/tui/<version>/`, `run/executables/` ([section 4](#4-exclusions)).

Always under `~/.nanobot` regardless of `--config`: `history/cli_history`
(prompt_toolkit input history), legacy `sessions/<safe key>.jsonl`, the
default `workspace/`, and launchd logs `logs/<name>.launchd.log`
([`config/paths.py:51-71`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/paths.py#L51-L71); [`gateway/service.py:135-139`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/gateway/service.py#L135-L139)).

### Scratch directories

The default workspace (`~/.nanobot/workspace`, or
`<home>/workspace` under `--home`,
[`config/home.py:24-28`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/config/home.py#L24-L28)),
the compose file's `api-workspace`, the MCP preset directories `mcp/<name>/`
and `cli-apps/` are the agent's own working directories, not user
projects. All are under `.nanobot*`, so the catalog collects them and the
analyzer's catalog rule classes them as scratch directories. No temp root
outside the home holds session state: the only `tempfile` directories are
transient staging for skill deletes and marketplace installs and an SSH
control-socket directory (`nb-ssh-*`,
[`webui/remote_mux.py:29`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/remote_mux.py#L29)).

### Workspace

The **workspace** (default `~/.nanobot/workspace`, [`config/schema.py:117-120`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L117-L120))
holds the agent's instructions and memory: `AGENTS.md`, `SOUL.md`, `USER.md`
([`agent/context.py:92`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/context.py#L92),[`194-202`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/context.py#L194-L202)), `HEARTBEAT.md` (periodic tasks, [`cli/gateway_runtime.py:629`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/gateway_runtime.py#L629)),
`memory/MEMORY.md`, `memory/history.jsonl`, legacy `memory/HISTORY.md`, cursors
`memory/.cursor` and `.dream_cursor` ([`agent/memory.py:76-91`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/memory.py#L76-L91)), a dulwich git
repository versioning those files ([`agent/memory.py:89-91`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/memory.py#L89-L91); [`utils/gitstore.py:56`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/gitstore.py#L56)),
`skills/` ([`agent/skills.py:61`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/skills.py#L61)), `cron/jobs.json` ([`cli/gateway_runtime.py:469`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/gateway_runtime.py#L469)),
`.nanobot/workspace-id` ([`session/manager.py:529-534`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L529-L534)) and
`.nanobot/tool-results/` spilled tool output ([`utils/helpers.py:366-368`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/helpers.py#L366-L368),[`639`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/helpers.py#L639)). Older
releases kept `sessions/*.jsonl` inside the workspace; they are copied to the
data directory and removed ([`session/manager.py:806-855`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L806-L855)).

### Persistence

Persistence: systemd user unit `~/.config/systemd/user/nanobot-gateway.service`
or `~/Library/LaunchAgents/ai.nanobot.gateway.plist` ([`gateway/service.py:25`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/gateway/service.py#L25),[`86-87`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/gateway/service.py#L86-L87),[`135-136`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/gateway/service.py#L135-L136),[`227-236`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/gateway/service.py#L227-L236)). No Windows service.

### Changes at the 2026-10-19 commit

- A global `--home <dir>` option sets the instance root; without it the
  root is `~/.nanobot`, and `history/cli_history`, the legacy sessions
  directory and the default workspace now follow the chosen root instead
  of staying under `~/.nanobot`
  ([`config/home.py:19-28`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/config/home.py#L19-L28);
  [`config/paths.py:52-72`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/config/paths.py#L52-L72);
  [`cli/commands.py:115`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cli/commands.py#L115)).
  The documented form is `--home ~/.nanobot-<name>`
  ([`docs/multiple-instances.md:3`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/docs/multiple-instances.md#L3),[`12`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/docs/multiple-instances.md#L12)),
  which the `.nanobot*` entry covers; any other directory is missed.
- `sessions/<workspace-id>/sessions.sqlite3` with `-wal` and `-shm`
  sidecars is the session store (mode 0600); the namespace's `*.jsonl`
  files are imported once and left in place, unchanged afterwards
  ([`session/sqlite_store.py:95-96`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L95-L96),[`157-200`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/sqlite_store.py#L157-L200)).
  Beside it: `jsonl-backup/` (the workspace's older `sessions/*.jsonl`,
  moved out of the workspace,
  [`session/jsonl_migration.py:32`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/jsonl_migration.py#L32),[`235-291`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/jsonl_migration.py#L235-L291)),
  `.webui_session_index.json` (a WebUI sidebar cache,
  [`webui/session_list_index.py:39-40`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/session_list_index.py#L39-L40),[`172-173`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/session_list_index.py#L172-L173)),
  and `.workspace-migration.lock` in the `sessions/` root
  ([`session/location.py:45-48`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/session/location.py#L45-L48)).
  All are under the `.nanobot*` entry and collected; none is large by
  design.
- In the workspace: `cron/runs/<run id>.json` and `cron/action.jsonl`
  ([`cron/service.py:207-208`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/cron/service.py#L207-L208)),
  and `triggers/` with `triggers.json`, `inbox/`, `processing/`,
  `failed/` and `runs/`
  ([`triggers/local_store.py:45-50`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/triggers/local_store.py#L45-L50)).
  Run records hold the prompt and the reply of each scheduled or
  triggered run. Collected with the default workspace; a workspace
  elsewhere is a project path ([section 6](#6-where-the-project-path-is-recorded)).
- Docker: the compose file bind-mounts the host's `~/.nanobot` at
  `/home/nanobot/.nanobot` rather than using a named volume, and the API
  service's workspace is `~/.nanobot/api-workspace`
  ([`docker-compose.yml:13-14`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/docker-compose.yml#L13-L14),[`48-49`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/docker-compose.yml#L48-L49)),
  so the home entry collects both and no `DOCKER_VOLUMES` line is needed.

## 3. Credentials

- `config.json`: `providers.<name>.apiKey` ([`config/schema.py:194-202`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L194-L202)), the API
  server `apiKey` ([`:340`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L340)), MCP server `env` ([`:370`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L370)), and channel
  secrets such as Feishu `appSecret` and `verificationToken`
  ([`channels/feishu/config.py:18-20`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/feishu/config.py#L18-L20)) or Linear `clientSecret`
  ([`channels/linear/config.py:22-23`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/channels/linear/config.py#L22-L23)). Keys are camelCase via `to_camel`
  ([`config_base.py:9-15`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config_base.py#L9-L15)). `${VAR}` references are resolved from the
  environment ([`config/loader.py:196`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/loader.py#L196)).
- `auth/xai.json` (xAI OAuth, [`providers/xai_oauth.py:262`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/providers/xai_oauth.py#L262)) and `auth/mcp.json`
  (MCP OAuth, [`agent/tools/mcp_oauth.py:102`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/tools/mcp_oauth.py#L102)).
- `whatsapp-auth/neonize.db` is a linked-device WhatsApp session; `matrix-store/`
  holds Matrix session and encryption state.
- `webui/remote-pairing/<uuid>/identity` (an unencrypted OpenSSH private
  key) and `exchange` (a raw X25519 private key), the material of the
  remote WebUI pairing link; secret globs
  `.nanobot*/webui/remote-pairing/*/identity` and
  `.nanobot*/webui/remote-pairing/*/exchange` from collector 1.14.0. The
  `request`, `receipt` and `ssh_route` files beside them and
  `webui/remote-instances.json` stay unflagged.
  Evidence in
  [section 7 of `analyzer/research/nanobot.md`](../../analyzer/research/nanobot.md#7-secrets).
- No keychain use found.
- `pairing.json` at the 2026-10-19 commit is `{"approved": {<channel>:
  [<sender_id>...]}, "pending": {<code>: {channel, sender_id,
  created_at, expires_at, delivery_status}}}`, the code an
  `ABCD-EFGH` value that lives ten minutes and only lets an operator
  approve that sender
  ([`pairing/store.py:27-33`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/pairing/store.py#L27-L33),[`73-85`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/pairing/store.py#L73-L85),[`130-138`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/pairing/store.py#L130-L138)).
  It is permission evidence, not a credential, and stays unflagged.

## 4. Exclusions

`bin/tui` (downloaded TUI binaries, [`cli/tui_launcher.py:261`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/tui_launcher.py#L261)), `run/executables`
([`:248`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/cli/tui_launcher.py#L248)), `cache/tiktoken` ([`utils/token_encoding.py:20`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/utils/token_encoding.py#L20)). Nothing else is
large by design; `media/` can grow but is evidence.

## 5. Project-local files

A user can point `--workspace` at a repository, which then receives the
workspace files of [section 2](#2-per-user-storage), notably `.nanobot/` and `memory/`. `AGENTS.md`
is read from the active workspace, `SOUL.md` and `USER.md` from the configured
one ([`agent/context.py:194-202`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/agent/context.py#L194-L202)). No per-project database.

## 6. Where the project path is recorded

- `sessions/<workspace-id>/.workspace`: absolute workspace path, one line
  ([`session/manager.py:606-607`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/session/manager.py#L606-L607)).
- `config.json` `agents.defaults.workspace` ([`config/schema.py:117-120`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L117-L120),[`188-191`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L188-L191),[`428`](https://github.com/HKUDS/nanobot/blob/acdae3d0ae2714b6dde672428e921dbf705c096f/nanobot/config/schema.py#L428)).
- `webui/workspace-state.json` (WebUI workspace list; keys not traced).
- Per session, `metadata.workspace_scope.project_path` (with
  `access_mode` `restricted` or `full`): the project folder a WebUI chat
  was pointed at, which can differ from the workspace in `.workspace`
  ([`security/workspace_access.py:80-84`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/security/workspace_access.py#L80-L84);
  [`webui/inbound_commands.py:694`](https://github.com/HKUDS/nanobot/blob/909b277e7a5a7ecd2aebdba9611e5febe86988d9/nanobot/webui/inbound_commands.py#L694)).
  At the 2026-10-19 commit it sits in the `metadata` column of
  `sessions.sqlite3`, so `discover_projects` cannot read it; the
  analyzer can.

## 7. Confidence

High: every path in [section 2](#2-per-user-storage) to
[section 6](#6-where-the-project-path-is-recorded), read from constants in the cited files.
Medium: that `matrix-store/` holds credentials (inferred from its role; not
read); `.nanobot-*` as an instance naming convention comes from docs, and any
other `--config` location is missed. `nanobot|memory/...` lines assume the
collector's project globs accept a sub-path, as `.github/...` entries do. Not
determined: the contents of `webui/workspace-state.json`, `weixin/` and
`mochat/` state; whether the Docker image's `/root/.nanobot` differs.
