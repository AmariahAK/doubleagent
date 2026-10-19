# OpenHands: on-disk paths

## 1. Source and evidence level

OpenHands is now split across several MIT-licensed repositories, all open
source; `All-Hands-AI/OpenHands` redirects to `OpenHands/OpenHands`.

- [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) at [`a6bba78ffd5a8b31620770f52383b1a2c0477fcd`](https://github.com/OpenHands/OpenHands/commit/a6bba78ffd5a8b31620770f52383b1a2c0477fcd)
  (2026-10-03): now only Agent Canvas, the React frontend plus the local-stack
  launcher; backend, conversations and events belong to the SDK
  ([`AGENTS.md:31-35`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/AGENTS.md#L31-L35)).
- [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) at [`b347047e2dcdd8f4b2be810aa8bc6632bc756d41`](https://github.com/OpenHands/software-agent-sdk/commit/b347047e2dcdd8f4b2be810aa8bc6632bc756d41):
  the SDK and the Agent Server, which owns every file under `~/.openhands`
  that matters.
- [OpenHands/OpenHands-CLI](https://github.com/OpenHands/OpenHands-CLI) at [`954f2ba646e8d749261a8f2b2b7e3031fa39be9f`](https://github.com/OpenHands/OpenHands-CLI/commit/954f2ba646e8d749261a8f2b2b7e3031fa39be9f):
  the `openhands` terminal CLI, "no longer actively maintained"
  ([`README.md:31-35`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/README.md#L31-L35)) but still installed in the field.
- The pre-Canvas Python app, read at tags `1.11.0`
  ([`11ca68ab2e15dcd85c21e4d7d3409e7a259369ac`](https://github.com/OpenHands/OpenHands/commit/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac))
  and `0.62.0` ([`7fbb48c40679afd674970966b96185657d92a487`](https://github.com/OpenHands/OpenHands/commit/7fbb48c40679afd674970966b96185657d92a487)),
  for legacy layouts that share `~/.openhands`.

All claims are from source. Transcript schema is in
[`analyzer/research/openhands.md`](../../analyzer/research/openhands.md).

- **Source review (2026-10-19)**: OpenHands at
  [`8d39305`](https://github.com/OpenHands/OpenHands/commit/8d39305538c1d17a30cbe477e57a0e18fcee7d95)
  (previously [`a6bba78`](https://github.com/OpenHands/OpenHands/commit/a6bba78ffd5a8b31620770f52383b1a2c0477fcd)), software-agent-sdk at
  [`33d8aa2`](https://github.com/OpenHands/software-agent-sdk/commit/33d8aa29c3078d074799e2fbf5e847aeb2d71360)
  (previously [`b347047`](https://github.com/OpenHands/software-agent-sdk/commit/b347047e2dcdd8f4b2be810aa8bc6632bc756d41)), OpenHands-CLI at
  [`0403f1a`](https://github.com/OpenHands/OpenHands-CLI/commit/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2)
  (previously [`954f2ba`](https://github.com/OpenHands/OpenHands-CLI/commit/954f2ba646e8d749261a8f2b2b7e3031fa39be9f); no commit since 2026-10-09). From source only.
  - Permission state: the per-conversation `confirmation_policy`,
    `security_analyzer` and `blocked_actions` in `base_state.json`, and
    the server default in `settings.json`; both files are collected.
    Detail in the [analyzer document](../../analyzer/research/openhands.md#3-record-schema).
  - Model: in `base_state.json` and event files; nothing new to collect.
  - Past use beyond the primary store: the CLI's
    `projects/<sha256>/prompt_history.json` (already collected) and the
    Canvas app's `Local Storage` (already collected, under the Electron
    user data directory).
  - Sync, relay and origin: Canvas now also connects to DigitalOcean
    Managed Agents sessions; their only local files are a credential store
    and `Local Storage` entries ([section 2](#2-per-user-storage),
    [section 3](#3-credentials)). No relay.
  - Scratch directories: found; see "Scratch directories" in
    [section 2](#2-per-user-storage). `~/.openhands/workspaces` (automation
    runs) is collected whole, unlike `agent-canvas/workspaces`.
  - Deletion: an Agent Server delete removes the conversation directory
    and the worktree under `/tmp`, and keeps the workspace and branches.
  - Version drift: every path in this document is unchanged at the new
    commits; new is `mars-credentials.json`.
  - Bad lines: analyzer-side only; see the
    [analyzer document](../../analyzer/research/openhands.md#8-parser-plan).

## 2. Per-user storage

One root, `~/.openhands`, on every OS: Python `Path.home() / ".openhands"`
([`openhands-sdk/openhands/sdk/utils/path.py:32-59`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/utils/path.py#L32-L59)) and Node
`homedir()` ([`scripts/dev-safe.mjs:80-102`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L80-L102)), so
`%USERPROFILE%\.openhands` on Windows. `OH_PERSISTENCE_DIR` replaces it
(SDK); the CLI uses `OPENHANDS_PERSISTENCE_DIR` and
`OPENHANDS_CONVERSATIONS_DIR` ([`openhands_cli/locations.py:5-23`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/locations.py#L5-L23));
the 1.x app also honoured `FILE_STORE_PATH`
([`openhands/app_server/config.py:75-89`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/config.py#L75-L89)).

**Agent Canvas** (`agent-canvas`, `npm install -g @openhands/agent-canvas`,
or the Electron app) runs the Agent Server with
`OH_PERSISTENCE_DIR=~/.openhands` and its own state in
`~/.openhands/agent-canvas` (`OH_CANVAS_SAFE_STATE_DIR`)
([`scripts/dev-safe.mjs:643-703`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L643-L703), [`817-821`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L817-L821);
[`bin/agent-canvas.mjs:157-166`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/bin/agent-canvas.mjs#L157-L166)):

- `agent-canvas/dev_conversations/<conversation hex>/` when run natively,
  `agent-canvas/conversations/<hex>/` when Canvas runs in its Docker image
  ([`docker/entrypoint.sh:174-178`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/docker/entrypoint.sh#L174-L178);
  [`config/defaults.json:23-26`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/config/defaults.json#L23-L26)). Each holds
  `meta.json`, `base_state.json`, `events/event-NNNNN-<id>.json` and
  `bash_events/` ([section 6](#6-where-the-project-path-is-recorded), and the [analyzer document](../../analyzer/research/openhands.md)).
- `agent-canvas/bash_events/`: commands typed in the Canvas terminal, one
  file per event named `<YYYYMMDDHHMMSSffffff>_<kind>_...`
  ([`openhands-agent-server/openhands/agent_server/bash_service.py:61-72`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/bash_service.py#L61-L72)).
- `agent-canvas/workspaces/<conversation hex>/`: default working directory
  for conversations not opened on a project, and automation run workspaces
  ([`dev-safe.mjs:649`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L649),[`703`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L703);
  [`scripts/dev-with-automation.mjs:1064-1069`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-with-automation.mjs#L1064-L1069);
  [`src/api/agent-server-config.ts:203-211`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/src/api/agent-server-config.ts#L203-L211)).
- `agent-canvas/logs/agent-canvas.%DATE%.log` ([`scripts/logger.mjs:23-26`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/logger.mjs#L23-L26),[`64`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/logger.mjs#L64));
  `agent-canvas/storage/` ([`dev-with-automation.mjs:600-608`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-with-automation.mjs#L600-L608));
  `agent-canvas/tmux/` sockets ([`dev-safe.mjs:682-698`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L682-L698)).
- `automation/automations.db`, SQLite, the automation service's schedules
  and run history ([`config/defaults.json:26`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/config/defaults.json#L26);
  [`dev-with-automation.mjs:1047-1048`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-with-automation.mjs#L1047-L1048)).

**Agent Server stores** directly under `~/.openhands`
([`openhands-agent-server/openhands/agent_server/persistence/store.py:802-822`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/persistence/store.py#L802-L822)):
`settings.json` ([`store.py:306-314`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/persistence/store.py#L306-L314)),
`secrets.json` ([`444-450`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/persistence/store.py#L444-L450)),
`workspaces.json` ([`725-742`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/persistence/store.py#L725-L742)),
`provider-connections/provider_connections.json` ([`895-913`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/persistence/store.py#L895-L913);
[`openhands-sdk/openhands/sdk/llm/provider_connection_store.py:49-50`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/provider_connection_store.py#L49-L50)),
`profiles/<name>.json` LLM profiles ([`openhands-sdk/openhands/sdk/llm/llm_profile_store.py:28`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/llm_profile_store.py#L28)),
`agent-profiles/` ([`openhands-sdk/openhands/sdk/profiles/agent_profile_store.py:29`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/profiles/agent_profile_store.py#L29)),
`auth/` ([`openhands-sdk/openhands/sdk/llm/auth/credentials.py:21-28`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/auth/credentials.py#L21-L28)),
`memory/MEMORY.md` ([`openhands-sdk/openhands/sdk/context/memory.py:23`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/context/memory.py#L23)),
`skills/`, `skills/installed/`, `microagents/` ([`openhands-agent-server/openhands/agent_server/skills_service.py:6-10`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/skills_service.py#L6-L10)),
`plugins/installed/` ([`openhands-sdk/openhands/sdk/plugin/installed.py:23`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/plugin/installed.py#L23)),
`cache/skills/`, `cache/plugins/` ([`openhands-sdk/openhands/sdk/skills/fetch.py:20`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/skills/fetch.py#L20);
[`openhands-sdk/openhands/sdk/plugin/fetch.py:20`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/plugin/fetch.py#L20)).

**Docker runtime** (`OH_CONVERSATION_RUNTIME=docker`, one container per
conversation, [`README.md:107-117`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/README.md#L107-L117)) keeps
`runtime-control/<hex>.json` (per-conversation identity) and
`runtime-data/<hex>/persistence/` under `~/.openhands`
([`openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py:54-68`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py#L54-L68)).
The container gets the host conversation directory, that persistence
directory (as its `HOME`) and the host workspace as bind mounts
([`docker_runtime/registry.py:40-42`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/docker_runtime/registry.py#L40-L42),[`354-404`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/docker_runtime/registry.py#L354-L404)),
so transcripts and the container user's dotfiles land on the host. Only
what the agent writes outside those mounts (container `/tmp`, packages it
installs) stays in the container and is lost with it. Canvas-in-Docker
likewise bind-mounts host `~/.openhands` to `/home/openhands/.openhands`
([`README.md:93-101`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/README.md#L93-L101)). Git worktrees go to
`/tmp/conversation-worktrees` by default
([`openhands-agent-server/openhands/agent_server/config.py:256-281`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/config.py#L256-L281)),
outside the home.

**Electron app**: product name `OpenHands Agent Canvas`
([`electron/package.json:3`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/electron/package.json#L3)), so Electron's
default user data directory (`~/Library/Application Support/OpenHands Agent Canvas`,
`~/.config/OpenHands Agent Canvas`, `%APPDATA%\OpenHands Agent Canvas`)
holds the frontend's localStorage; the backend state is the same
`~/.openhands`. Since the 2026-10-19 review (Canvas at
[`8d39305`](https://github.com/OpenHands/OpenHands/commit/8d39305538c1d17a30cbe477e57a0e18fcee7d95))
it also holds `mars-credentials.json`, the store of DigitalOcean
connections for Managed Agents sessions (MARS, DigitalOcean's name for
its hosted agent sandboxes: a microVM that runs its own Agent Server, so
those conversations stay on DigitalOcean)
([`scripts/mars-credentials.mjs:18`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/mars-credentials.mjs#L18),
[`77-88`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/mars-credentials.mjs#L77-L88);
[`electron/main.mjs:773-777`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/electron/main.mjs#L773-L777);
[`src/api/mars/AGENTS.md:3`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/mars/AGENTS.md#L3)).
The localStorage keys that matter (`openhands-backends`,
`openhands-last-conversation-by-backend`,
`openhands-agent-server-conversation-metadata`,
`archived-conversations`) are listed in
[section 5 of the analyzer document](../../analyzer/research/openhands.md#5-sqlite-or-binary-stores).

**Automation workspaces.** The automation service unpacks each run into
`AUTOMATION_WORKSPACE_BASE`: `~/.openhands/workspaces` under
Canvas-in-Docker, `~/.openhands/agent-canvas/workspaces` natively
([`docker/entrypoint.sh:334-336`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/docker/entrypoint.sh#L334-L336);
[`scripts/dev-with-automation.mjs:1066-1075`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/dev-with-automation.mjs#L1066-L1075)).
The Docker path was already there at `a6bba78` and was missed.

**Scratch directories.** OpenHands has three, all chosen by the agent
rather than the user:

- `~/.openhands/agent-canvas/workspaces/<conversation hex>/`, the working
  directory of a Canvas conversation opened on no project
  ([`scripts/dev-safe.mjs:648-649`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/dev-safe.mjs#L648-L649),
  [`703`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/dev-safe.mjs#L703)).
  Under the home, excluded by default
  ([section 4](#4-exclusions)), collected with `--full`.
- `~/.openhands/workspaces/<run>/`, automation runs under
  Canvas-in-Docker (above). Under the home and collected whole today.
- `/tmp/conversation-worktrees/<dir>/`, the git worktree the Agent
  Server makes for a conversation started with worktree isolation
  ([`openhands-agent-server/openhands/agent_server/config.py:286-293`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/config.py#L286-L293)).
  Outside the home, so no catalog line can collect it; the conversation's
  `meta.json` and `base_state.json` record it as
  `workspace.working_dir`, and Canvas records the choice as
  `workspace_mode` `new_worktree` in its localStorage.

The first two are under the `.openhands` catalog entry, so the analyzer's
catalog rule classes them as scratch directories; the third is not.

**CLI** ([`openhands_cli/locations.py:5-54`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/locations.py#L5-L54)):
`conversations/<hex>/` (SDK layout, plus `TASKS.json`,
[`tui/panels/plan_side_panel.py:107`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/tui/panels/plan_side_panel.py#L107)),
`projects/<sha256 of cwd>/prompt_history.json`, `agent_settings.json`,
`mcp.json`, `cli_config.json` ([`stores/cli_settings.py:60-63`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/stores/cli_settings.py#L60-L63)),
`cloud/api_key.txt`, `cache/acp/` ([`acp_impl/utils/resources.py:43`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/acp_impl/utils/resources.py#L43)),
`hooks.json` ([`acp_impl/agent/local_agent.py:180`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/acp_impl/agent/local_agent.py#L180)). `openhands serve` runs the legacy app image with
`~/.openhands` mounted at `/.openhands`
([`gui_launcher.py:125-140`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/gui_launcher.py#L125-L140)).

**Legacy app, same root.** 1.x: `openhands.db` SQLite
([`openhands/app_server/services/db_session_injector.py:192`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/services/db_session_injector.py#L192)),
`[<user_id>/]v1_conversations/<hex>/<event hex>.json`
([`conversation_paths.py:12`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/conversation_paths.py#L12),[`38-55`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/conversation_paths.py#L38-L55);
[`event/event_service_base.py:89`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/event/event_service_base.py#L89)), `settings.json`, `secrets.json`
([`settings/file_settings_store.py:15`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/settings/file_settings_store.py#L15); [`secrets/file_secrets_store.py:15`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/secrets/file_secrets_store.py#L15)),
`analytics_id.txt` ([`analytics/oss_install_id.py:21`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/analytics/oss_install_id.py#L21)). 0.x:
`sessions/<sid>/` with `events/<n>.json`, `event_cache/<start>-<end>.json`,
`metadata.json`, `init.json`, `agent_state.pkl`, `conversation_stats.pkl`,
`llm_registry.json`, or `users/<id>/conversations/<sid>/`
([`openhands/storage/locations.py:1-42`](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/storage/locations.py#L1-L42);
[`openhands/events/event_store.py:159`](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/events/event_store.py#L159)); default root
`~/.openhands` ([`openhands/core/config/openhands_config.py:73`](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/core/config/openhands_config.py#L73)).

Paths inside the sandbox and not on the host: in the 0.x app, the runtime
container's `/workspace` unless `SANDBOX_VOLUMES` mounted a host directory
([`gui_launcher.py:161-170`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/gui_launcher.py#L161-L170)); in Canvas-in-Docker, everything
except `~/.openhands` and `PROJECTS_PATH`.

## 3. Credentials

- `~/.openhands/agent-canvas/secret-key.txt`: `OH_SECRET_KEY`, the master key
  ([`dev-safe.mjs:90-102`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L90-L102); [`docker/entrypoint.sh:185-196`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/docker/entrypoint.sh#L185-L196)).
  Secret fields in `settings.json`, `secrets.json`, `profiles/*.json`,
  `meta.json` and `base_state.json` are Fernet tokens keyed by
  SHA-256 of it ([`openhands-sdk/openhands/sdk/utils/cipher.py:73-80`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/utils/cipher.py#L73-L80);
  [`pydantic_secrets.py:48-78`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/utils/pydantic_secrets.py#L48-L78)), and are written in
  plaintext when no key is configured ([`store.py:372-383`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/persistence/store.py#L372-L383)). Collecting
  the key with the stores makes every secret readable.
- `~/.openhands/agent-canvas/api-key.txt`: the local backend session key
  ([`dev-safe.mjs:80-85`](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/scripts/dev-safe.mjs#L80-L85)).
- `settings.json`, `secrets.json`, `profiles/*.json`,
  `provider-connections/*`, `auth/<vendor>_oauth.json`
  ([`credentials.py:73-75`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/auth/credentials.py#L73-L75)).
- `runtime-control/<hex>.json`: per-conversation `api_key` and
  `encryption_key`, themselves encrypted with the master key
  ([`provisioning.py:22-45`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py#L22-L45)).
- CLI: `agent_settings.json` saved with `expose_secrets: True`, so the LLM
  API key is plaintext ([`stores/agent_store.py:474-476`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/stores/agent_store.py#L474-L476));
  `cloud/api_key.txt` ([`auth/token_storage.py:19-25`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/auth/token_storage.py#L19-L25)); `mcp.json`
  holds MCP server definitions, which may embed keys.
- Legacy: `.jwt_secret` and `.keys` in the root
  ([`openhands/app_server/utils/encryption_key.py:51-57`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/utils/encryption_key.py#L51-L57);
  [`openhands/core/config/utils.py:35`](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/core/config/utils.py#L35)).
- A conversation driving Codex through ACP reads `~/.codex/auth.json`
  ([`openhands-sdk/openhands/sdk/agent/acp_file_credentials.py:32`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/agent/acp_file_credentials.py#L32),[`65-68`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/agent/acp_file_credentials.py#L65-L68)); older
  conversations may hold `acp/codex/auth.json` in their own directory
  ([`event_service.py:338-339`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/event_service.py#L338-L339)).

- Agent Canvas Electron app (2026-10-19 review):
  `<user data directory>/mars-credentials.json`, the DigitalOcean
  connections (`connections[]` with `kind` `oauth` or `pat`, `label`,
  `teamName`, `expiresAt` and the token, and a `deviceId`); only the token
  is encrypted, with Electron `safeStorage` (the OS keychain), and is
  written as `null` when the keychain is unavailable, so the connection
  then lasts only for the session; the file is mode 0600
  ([`scripts/mars-credentials.mjs:42-49`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/mars-credentials.mjs#L42-L49),
  [`77-88`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/mars-credentials.mjs#L77-L88),
  [`118-135`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/mars-credentials.mjs#L118-L135),
  [`195-210`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/scripts/mars-credentials.mjs#L195-L210)).
  No secret glob flags it yet.
- The Canvas `Local Storage` key `openhands-backends` stores each
  backend's `apiKey` in plain JSON, an OpenHands Cloud key for a cloud
  backend ([`src/api/backend-registry/types.ts:4-22`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/backend-registry/types.ts#L4-L22);
  [`storage.ts:95-101`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/backend-registry/storage.ts#L95-L101)).
  It shares the LevelDB files with the conversation metadata, so it is
  collected unflagged and the key is the one to redact.

No keychain use found, apart from the `safeStorage` encryption above.

## 4. Exclusions

`.openhands/cache` (git clones of skill and plugin sources), and
`.openhands/agent-canvas/workspaces`, which can hold whole repositories the
agent cloned. It is also the agent's work product for scratch
conversations, so it is excluded by default like `.claude/worktrees` and
`.codex/worktrees`, recorded as `skipped_excluded` with its size, and
collected with `--full`.
`.openhands/agent-canvas/tmux` holds sockets only. Keep `bash_events`,
`runtime-data` (container `HOME`, may hold shell history) and `logs`.

`.openhands/workspaces` (automation run workspaces under
Canvas-in-Docker, [section 2](#2-per-user-storage)) holds the same kind
of content as `agent-canvas/workspaces` and is not excluded today; an
exclusion like the native one would treat both alike (2026-10-19 review).

## 5. Project-local files

`<project>/.openhands/`: `hooks.json`
([`openhands-agent-server/openhands/agent_server/hooks_service.py:36`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/hooks_service.py#L36)), `skills/`,
`microagents/`, `memory/MEMORY.md`, `setup.sh`, `pre-commit.sh`
([`skills_service.py:6-10`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/skills_service.py#L6-L10); [`memory.py:23`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/context/memory.py#L23);
[`openhands/app_server/app_conversation/app_conversation_service_base.py:66-74`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/app_conversation/app_conversation_service_base.py#L66-L74)).
Also read: `.agents/skills/` ([`app_conversation_router.py:1364`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/app_conversation/app_conversation_router.py#L1364)), `AGENTS.md`, `.cursorrules` (skills service, above). No per-project
database.

## 6. Where the project path is recorded

- `workspaces.json` `workspaces[].path` and `workspaceParents[].path`
  ([`openhands-agent-server/openhands/agent_server/persistence/models.py:615-636`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/persistence/models.py#L615-L636)).
- Each conversation's `meta.json` and `base_state.json`:
  `workspace.working_dir` ([`openhands-sdk/openhands/sdk/conversation/request.py:105`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/request.py#L105);
  [`openhands-sdk/openhands/sdk/workspace/base.py:43`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/workspace/base.py#L43)).
  Under Canvas-in-Docker these are container paths (`/projects/<name>`),
  not host paths.
- CLI `projects/<sha256>/` names are hashes of the path
  ([`locations.py:34-42`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/locations.py#L34-L42)); not reversible, but checkable
  against a candidate path.
- Agent Canvas `localStorage` (Electron `Local Storage`)
  `openhands-agent-server-conversation-metadata`: per conversation id,
  `selected_workspace` (the folder the user attached),
  `selected_repository`, `selected_branch` and `workspace_mode`
  (`local_repo` or `new_worktree`)
  ([`src/api/conversation-metadata-store.ts:4-56`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/conversation-metadata-store.ts#L4-L56)).
  LevelDB, so not grep-able by `discover_projects`.
- A worktree conversation's `workspace.working_dir` is under
  `/tmp/conversation-worktrees/` by default, a scratch directory
  ([section 2](#2-per-user-storage)), not the user's project
  (2026-10-19 review). Whether the conversation files also name the
  repository the worktree was made from was not traced.

## 7. Confidence

High: every path in [section 2](#2-per-user-storage) and [section 3](#3-credentials) under `~/.openhands` (constants and env
defaults in the cited files), the Fernet scheme, the Docker-runtime bind
mounts, the CLI and legacy layouts at the cited commits. Medium: the
Electron user data directory (Electron convention from `productName`; the
app does not set it explicitly); `agent-canvas/storage` contents (created
for the automation file store, not traced); whether `secrets.json` in the
legacy root used the same field names. Not determined: Agent Server file
logs (`LOG_DIR` defaults to a relative `logs`, so the cwd of the server);
the automation service's tarballs under `storage/`; whether a Canvas
install leaves a uv tool environment worth collecting (uv caches are
outside this tool's directories).
