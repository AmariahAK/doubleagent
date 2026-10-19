# agent-zero

Agent Zero (catalog agent `agent-zero`) is agent0ai's open-source Python agent, usually run in a
Docker container whose install directory is `/a0`, with a web UI, messaging plugins (Telegram,
WhatsApp, email) and editor sessions; three companions put its data on the host: the A0 Install
scripts, the A0 Launcher (an Electron app that manages instances) and the A0 CLI connector (a
host-side client). Its Orchestrator plugin can drive other coding CLIs, Hermes among them. The
transcript schema is in [`analyzer/research/agent-zero.md`](../../analyzer/research/agent-zero.md).

## 1. Source and evidence

[agent0ai/agent-zero](https://github.com/agent0ai/agent-zero) at commit
[`e3051fb584b1a36be2b0a0c90606f1c2c2d356ec`](https://github.com/agent0ai/agent-zero/commit/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec).
The `LICENSE` file at that commit is plain MIT
([`LICENSE:1-4`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/LICENSE#L1-L4)), not a custom licence. Python, source public. Three companion
repositories decide where the data lands on the host and were also read:
[agent0ai/a0-install](https://github.com/agent0ai/a0-install) at [`c89b4026e9f16f53389e75537783411fefdd53f1`](https://github.com/agent0ai/a0-install/commit/c89b4026e9f16f53389e75537783411fefdd53f1)
(installer scripts), [agent0ai/a0-launcher](https://github.com/agent0ai/a0-launcher) at
[`b0333d80b5abf38d8481f55b667b0cf23d805bbb`](https://github.com/agent0ai/a0-launcher/commit/b0333d80b5abf38d8481f55b667b0cf23d805bbb) (Electron launcher, MIT,
[`LICENSE:1`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/LICENSE#L1)), and [agent0ai/a0-connector](https://github.com/agent0ai/a0-connector) at
[`76e834f20e50f6e47954c89ee39dd4c5b50d81b7`](https://github.com/agent0ai/a0-connector/commit/76e834f20e50f6e47954c89ee39dd4c5b50d81b7) (the host-side "A0 CLI", MIT,
[`LICENSE:1`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/LICENSE#L1)). All claims are from source or the in-repo docs.

### Observed

No real install. Nothing was installed or run, for the first research or the source review of
2026-10-19 (read only).

### Source reviews

- **Source review (2026-10-19).** agent0ai/agent-zero at
  [`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a)
  against
  [`e3051fb`](https://github.com/agent0ai/agent-zero/commit/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec)
  above; a0-install unchanged, HEAD is still
  [`c89b402`](https://github.com/agent0ai/a0-install/commit/c89b4026e9f16f53389e75537783411fefdd53f1);
  a0-launcher at
  [`a69403d`](https://github.com/agent0ai/a0-launcher/commit/a69403d9cc92009addb06fedb5585e60e09a3d2c)
  against
  [`b0333d8`](https://github.com/agent0ai/a0-launcher/commit/b0333d80b5abf38d8481f55b667b0cf23d805bbb);
  a0-connector at
  [`3741c88`](https://github.com/agent0ai/a0-connector/commit/3741c8809f1f99b4efee2ed1a24234a98bf896d4)
  against
  [`76e834f`](https://github.com/agent0ai/a0-connector/commit/76e834f20e50f6e47954c89ee39dd4c5b50d81b7).
  One line per requirement class; the
  record-level detail is in
  [Source reviews of `analyzer/research/agent-zero.md`](../../analyzer/research/agent-zero.md#source-reviews).
  - Permission state: found. Tool policy files
    `plugins/_tool_access/config.json` under agent profiles and
    projects, plugin switches `.toggle-0` and `.toggle-1`, and the
    Orchestrator plugin's bypass defaults, all inside `usr/` and so
    already collected ([section 2](#2-per-user-storage)).
  - Model: per-chat keys in `chat.json` and
    `usr/plugins/_model_config/presets.yaml`, already collected.
  - Past use beyond `chat.json`: the scheduler list (now `tasks.json`
    or `tasks.yaml`), Telegram's chat map and the memory store are
    collected; the time-travel shadow git, which records the chat id of
    every snapshot, is excluded ([section 4](#4-exclusions)).
  - Sync, relay and origin: no new channel at HEAD; the connector's
    `.env` points at a chat on another instance, already collected and
    flagged.
  - Scratch directories: found; `usr/workdir` is collected, the
    connector's screenshot directory under the system temp directory is
    not ([Scratch directories](#scratch-directories)).
  - Deletion: chat delete removes the chat folder and its scheduler
    tasks, reset keeps the folder
    ([`api/chat_remove.py:11-26`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/api/chat_remove.py#L11-L26),
    [`api/chat_reset.py:13-19`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/api/chat_reset.py#L13-L19)).
  - Version drift: the `usr/` layout is unchanged; the connector's
    path constants moved two lines (`_ENV_DIR` is now
    [`config.py:10-12`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/config.py#L10-L12));
    the launcher's Windows build can now run its own WSL distribution
    under `AppData/Local/agent-zero/wsl/Ubuntu`
    ([Host-side companions](#host-side-companions)). New credential directory:
    the WhatsApp bridge's `tmp/whatsapp/session/`, which the cited
    commit already had and which is collected unflagged
    ([section 3](#3-credentials)).
  - Bad lines: not a collector class; nothing to add.

## 2. Per-user storage

Agent Zero itself never resolves a home directory. Every path is relative
to the install directory, the parent of `helpers/`
([`helpers/files.py:23`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/files.py#L23),[`575-584`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/files.py#L575-L584)), shown to the agent as `/a0/...`
([`files.py:618-623`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/files.py#L618-L623)). In the container that is `/a0`; all user state is
under `/a0/usr` and `/a0/tmp`, both gitignored
([`.gitignore:26-39`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/.gitignore#L26-L39)). Where that lands on the host depends on how
it was started:

| Deployment | Host location of `/a0/usr` |
| --- | --- |
| A0 Install (`install.sh`, `install.ps1`) | `~/agent-zero/<container-name>/usr`, override `--data-dir` ([`install.sh:1630`](https://github.com/agent0ai/a0-install/blob/c89b4026e9f16f53389e75537783411fefdd53f1/install.sh#L1630),[`1650-1652`](https://github.com/agent0ai/a0-install/blob/c89b4026e9f16f53389e75537783411fefdd53f1/install.sh#L1650-L1652),[`1830`](https://github.com/agent0ai/a0-install/blob/c89b4026e9f16f53389e75537783411fefdd53f1/install.sh#L1830); [`install.ps1:30`](https://github.com/agent0ai/a0-install/blob/c89b4026e9f16f53389e75537783411fefdd53f1/install.ps1#L30),[`1856`](https://github.com/agent0ai/a0-install/blob/c89b4026e9f16f53389e75537783411fefdd53f1/install.ps1#L1856),[`1874`](https://github.com/agent0ai/a0-install/blob/c89b4026e9f16f53389e75537783411fefdd53f1/install.ps1#L1874)) |
| A0 Launcher, default "host directory" mode | `~/agent-zero/<instance>[-N]/usr` ([`state_store.js:144-149`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/shell/docker_manager/state_store.js#L144-L149), [`index.js:890-899`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/shell/docker_manager/index.js#L890-L899)) |
| A0 Launcher, "named volume" mode | Docker volume `a0-launcher-<slug>-usr` ([`index.js:948-951`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/shell/docker_manager/index.js#L948-L951)) |
| README `docker run` | Docker volume `a0_usr` ([`README.md:92`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/README.md#L92)) |
| `docker/run/docker-compose.yml` | `./agent-zero` beside the compose file, mounted as all of `/a0` ([`docker-compose.yml:5-6`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/docker/run/docker-compose.yml#L5-L6)) |
| Native ("development") run | the git clone, anywhere; the docs example is `~/Desktop/agent-zero` ([`docs/setup/dev-setup.md:34-37`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/docs/setup/dev-setup.md#L34-L37)); native means not `--dockerized` ([`helpers/runtime.py:59-64`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/runtime.py#L59-L64)) |

Named volumes live under the Docker data root (or inside the Docker Desktop
VM), outside any home, and are not reachable by a home-relative catalog;
since collector 1.5.0 the `DOCKER_VOLUMES` table collects `*a0_usr` and
`a0-launcher-*-usr` volumes with usr-relative exclusions and secret globs. Only
the native run has `usr/` and `tmp/` beside the source, a `.venv` or
`.conda`, and a legacy root `.env`.

### Scratch directories

`usr/workdir` is the working directory of a
chat with no project
([`helpers/settings.py:604`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/settings.py#L604)),
and `usr/projects/<name>` directories, clones included, belong to the
agent's own tree; both are collected under the `agent-zero` entries and
the volumes. Chats name them by container path (`/a0/usr/...`), which
the analyzer's catalog rule cannot match to a home path. The
connector's screenshot directory ([Host-side companions](#host-side-companions)) is the one
scratch location outside `usr/`, and it is not collected.

### Contents of usr/

- `chats/<ctxid>/chat.json`, one per chat or scheduled-task context, and
  `chats/<ctxid>/messages/<n>.txt` for tool results of 500 characters or
  more ([`helpers/persist_chat.py:17-19`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L17-L19),[`47-48`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L47-L48),
  [`extensions/python/hist_add_tool_result/_90_save_tool_call_file.py:23-40`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/extensions/python/hist_add_tool_result/_90_save_tool_call_file.py#L23-L40)).
- `settings.json` ([`helpers/settings.py:182`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/settings.py#L182)), `.env`
  ([`helpers/dotenv.py:17-18`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/dotenv.py#L17-L18)), `secrets.env`
  ([`helpers/secrets.py:19`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/secrets.py#L19)).
- `memory/<subdir>/`: LangChain FAISS store, `index.faiss`, `index.pkl`
  (pickled docstore holding the memory text), `embedding.json`,
  `knowledge_import.json` ([`plugins/_memory/helpers/memory.py:180`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_memory/helpers/memory.py#L180),[`197`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_memory/helpers/memory.py#L197),[`269`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_memory/helpers/memory.py#L269),[`550`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_memory/helpers/memory.py#L550),[`666-673`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_memory/helpers/memory.py#L666-L673)).
- `knowledge/` user knowledge files ([`memory.py:676-689`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_memory/helpers/memory.py#L676-L689)).
- `projects/<name>/` with metadata in `.a0proj/`: `project.json`,
  `mcp_servers.json`, `instructions/`, `knowledge/`, `skills/`, `memory/`,
  `secrets.env`, `variables.env`
  ([`helpers/projects.py:11-17`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/projects.py#L11-L17),[`77-86`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/projects.py#L77-L86),[`672-684`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/projects.py#L672-L684); [`secrets.py:554`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/secrets.py#L554)).
- `workdir/`, the agent's default working directory
  ([`settings.py:597`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/settings.py#L597)).
- `scheduler/tasks.json` ([`helpers/task_scheduler.py:29`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/task_scheduler.py#L29),[`521`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/task_scheduler.py#L521)).
- `agents/`, `skills/`, `plugins/` user extensions
  ([`helpers/subagents.py:12`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/subagents.py#L12), [`helpers/skills.py:91`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/skills.py#L91)).
- `uploads/`, `upload/`, `downloads/`, `email/`
  ([`helpers/migration.py:24-31`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/migration.py#L24-L31)).
- `.time_travel/workspaces/`: shadow git history of `usr` workspaces
  ([`plugins/_time_travel/helpers/time_travel.py:23-24`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_time_travel/helpers/time_travel.py#L23-L24)).

Older releases kept chats, scheduler, uploads, settings and secrets under
`tmp/`, memory under `memory/` and the `.env` at the install root; startup
moves them into `usr/` ([`migration.py:24-38`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/migration.py#L24-L38),[`95-107`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/migration.py#L95-L107)), so an
image of an un-upgraded install may hold them in the old places.

### More files under usr/ and tmp/

From the 2026-10-19 review at
[`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a),
all collected by the existing entries:

- `scheduler/tasks.yaml`, used instead of `tasks.json` when only the
  YAML file exists
  ([`helpers/task_scheduler.py:512-515`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/task_scheduler.py#L512-L515)).
- Tool policies, the per-profile and per-project permission lists:
  `usr/agents/<profile>/plugins/_tool_access/config.json`,
  `usr/projects/<name>/.a0proj/plugins/_tool_access/config.json` and
  `.a0proj/agents/<profile>/plugins/_tool_access/config.json`
  ([`plugins/_tool_access/README.md:4-9`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_tool_access/README.md#L4-L9)).
- Plugin switches: an empty `.toggle-0` (disabled) or `.toggle-1`
  (enabled) in a plugin's directory under `usr/plugins/`
  ([`helpers/plugins.py:60-61`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/plugins.py#L60-L61)).
- `plugins/_model_config/presets.yaml`, the model presets a chat can
  select
  ([`plugins/_model_config/helpers/model_config.py:10`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/helpers/model_config.py#L10),[`99-101`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/helpers/model_config.py#L99-L101)).
- `email/state.json` and `email/attachments/` of the email plugin
  ([`plugins/_email_integration/helpers/handler.py:38-39`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_email_integration/helpers/handler.py#L38-L39)),
  `whatsapp/media/` and, under the install's `tmp/`, `whatsapp/media/`
  and `whatsapp/session/` of the WhatsApp bridge
  ([`plugins/_whatsapp_integration/helpers/handler.py:31`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/helpers/handler.py#L31),
  [`plugins/_whatsapp_integration/helpers/storage_paths.py:6-11`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/helpers/storage_paths.py#L6-L11)).
  `tmp/` is beside `usr/` only in a native run or a whole-`/a0`
  mount; the installer, the launcher and the README volume mount
  `usr` alone, so `tmp/` stays inside the container.

### Host-side companions

These are home-relative:

- A0 CLI connector: `~/.agent-zero/.env` (instance URL, last chat id,
  remote-exec and computer-use flags) and `~/.agent-zero/session_cookies.json`
  ([`a0-connector config.py:8-10`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/src/agent_zero_cli/config.py#L8-L10),[`15-25`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/src/agent_zero_cli/config.py#L15-L25)), same path on every OS. Its
  managed browser profiles are under `~/.local/share/a0/browser-profiles`,
  `~/Library/Application Support/A0/Browser Profiles` or
  `%LOCALAPPDATA%\A0\Browser Profiles` ([`host_browser_common.py:476-487`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/src/agent_zero_cli/host_browser_common.py#L476-L487)).
- A0 Launcher: Electron `productName` "Agent Zero Launcher"
  ([`package.json:51`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/package.json#L51)), so `userData` is the Electron default directory of
  that name; it holds `docker_manager/state.json` and `docker_manager/cache`
  ([`state_store.js:13-23`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/shell/docker_manager/state_store.js#L13-L23)).
  The launcher's Windows installer treats `%APPDATA%\a0-launcher`
  (the package name, not the product name) as the launcher's settings
  directory and keeps it across a reinstall, renaming it to
  `a0-launcher-installer-backup` while it runs
  ([`packaging/platforms/windows/installer.nsh:55-62`](https://github.com/agent0ai/a0-launcher/blob/a69403d9cc92009addb06fedb5585e60e09a3d2c/packaging/platforms/windows/installer.nsh#L55-L62));
  which of the two names Electron uses at run time was not resolved
  from source (2026-10-19 review).
- A0 Launcher on Windows, new since the launcher commit first cited:
  on a host without Docker Desktop the launcher's setup can import its
  own WSL distribution named `Ubuntu`, with its own Docker engine, into
  `AppData/Local/agent-zero/wsl/Ubuntu`
  ([`shell/docker_adapter/impl/WindowsWslRuntime.mjs:23`](https://github.com/agent0ai/a0-launcher/blob/a69403d9cc92009addb06fedb5585e60e09a3d2c/shell/docker_adapter/impl/WindowsWslRuntime.mjs#L23),[`31`](https://github.com/agent0ai/a0-launcher/blob/a69403d9cc92009addb06fedb5585e60e09a3d2c/shell/docker_adapter/impl/WindowsWslRuntime.mjs#L31),[`353`](https://github.com/agent0ai/a0-launcher/blob/a69403d9cc92009addb06fedb5585e60e09a3d2c/shell/docker_adapter/impl/WindowsWslRuntime.mjs#L353)),
  whose virtual disk holds the Docker engine and the container data
  and is kept on uninstall
  ([`docs/runtime-troubleshooting.md:38-43`](https://github.com/agent0ai/a0-launcher/blob/a69403d9cc92009addb06fedb5585e60e09a3d2c/docs/runtime-troubleshooting.md#L38-L43)).
  A named volume of that engine is inside the virtual disk, out of
  reach of the collector's volume walk; no catalog line names the
  directory.
- A0 CLI connector, computer use: each screen capture the connector
  takes for the agent is written to
  `<system temp>/_a0_connector/computer_use/<ctxid>/<uuid>.png` and
  older captures are deleted as new ones arrive
  ([`computer_use.py:242-247`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/computer_use.py#L242-L247),[`1329-1340`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/computer_use.py#L1329-L1340),[`1348-1356`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/computer_use.py#L1348-L1356)),
  overridable with `A0_COMPUTER_USE_HOST_ARTIFACT_ROOT`
  ([`33`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/computer_use.py#L33)).
  The system temp directory is `/tmp` or `$TMPDIR` on Linux and macOS,
  outside the home, and `AppData/Local/Temp` on Windows, inside it; no
  catalog line names it.

## 3. Credentials

- `usr/.env`: provider keys as `API_KEY_<PROVIDER>`, `AUTH_LOGIN`,
  `AUTH_PASSWORD`, `RFC_PASSWORD`, `ROOT_PASSWORD`; settings strip these
  before writing `settings.json`
  ([`settings.py:540-570`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/settings.py#L540-L570)).
- `usr/secrets.env` and `usr/projects/*/.a0proj/secrets.env`: user secrets
  the agent references as `§§secret(KEY)`
  ([`secrets.py:17-19`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/secrets.py#L17-L19),[`535-556`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/secrets.py#L535-L556)).
- `usr/settings.json` keeps `mcp_servers`, a JSON string of MCP server
  definitions that can carry headers or env keys
  ([`settings.py:93`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/settings.py#L93)); `mcp_server_token` is blanked
  ([`settings.py:553`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/settings.py#L553)).
- Legacy: root `.env`, `tmp/secrets.env`, `tmp/settings.json`
  ([`migration.py:36-38`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/migration.py#L36-L38)); the VPS guide still mounts a root `.env`
  ([`docs/setup/vps-deployment.md:176`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/docs/setup/vps-deployment.md#L176)).
- The desktop plugin keeps a profile with `.ssh/` and `.gnupg/` under
  `usr/plugins/_desktop/profiles/agent-zero-desktop/` (paths from a grep of
  string literals; writer not traced).
- `usr/plugins/<plugin>/config.json` holds a plugin's settings, which
  for the Telegram integration are the bot `token` and, in webhook mode,
  `webhook_secret`, and probably the email integration's credentials
  ([`helpers/plugins.py:838-851`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/plugins.py#L838-L851));
  secret globs `agent-zero*/usr/plugins/*/config.json`,
  `Desktop/agent-zero*/usr/plugins/*/config.json` and the volume-relative
  `plugins/*/config.json` (the `a0_usr` volume's base is `usr` itself)
  and `usr/plugins/*/config.json` from collector 1.14.0. No other
  `DOCKER_VOLUMES` layout has a `plugins/<name>/config.json`. A
  per-project copy under `.a0proj/` or an agent profile's directory is
  not flagged. The same Telegram values sit in clear text in each
  Telegram chat's `chat.json`, under `data.telegram_bot_cfg` (keys
  `token` and `webhook_secret`); the transcript cannot be flagged, so
  those are the keys to redact before sharing a `chat.json`. Evidence in
  [section 7 of `analyzer/research/agent-zero.md`](../../analyzer/research/agent-zero.md#7-secrets).
- Host side: `~/.agent-zero/session_cookies.json` (login cookies per host,
  [`config.py:123-146`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/src/agent_zero_cli/config.py#L123-L146)); the launcher's `state.json` stores instance
  passwords encrypted with Electron `safeStorage`, i.e. the OS keychain
  ([`state_store.js:683-688`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/shell/docker_manager/state_store.js#L683-L688),[`753-761`](https://github.com/agent0ai/a0-launcher/blob/b0333d80b5abf38d8481f55b667b0cf23d805bbb/shell/docker_manager/state_store.js#L753-L761)).
- WhatsApp (2026-10-19 review): the bridge, a Node.js process that
  signs in as a linked WhatsApp device through the Baileys library,
  keeps that device's login state in `tmp/whatsapp/session/` with
  Baileys' `useMultiFileAuthState`
  ([`plugins/_whatsapp_integration/helpers/storage_paths.py:6-7`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/helpers/storage_paths.py#L6-L7),
  [`whatsapp-bridge/bridge.js:46`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/whatsapp-bridge/bridge.js#L46),[`108`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/whatsapp-bridge/bridge.js#L108)).
  Whoever holds those files can act as the account's linked device; the
  directory is collected where `tmp/` is on the host and no secret glob
  flags it.
- The connector's `.env` also holds `AGENT_ZERO_COMPUTER_USE_RESTORE_TOKEN`
  ([`config.py:22`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/config.py#L22)),
  already covered by the `.agent-zero/.env` glob.

## 4. Exclusions

`tmp/memory/embeddings` is an embedding cache ([`memory.py:145-147`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_memory/helpers/memory.py#L145-L147)),
`tmp/playwright` holds browser binaries
([`plugins/_browser/helpers/playwright.py:16`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_browser/helpers/playwright.py#L16)), `usr/.time_travel` is shadow git.
For native clones: `.venv`, `.conda`, `.git`. Python environments inside
`usr/workdir/*/.venv` occur (the code references one). The connector's and
launcher's Chromium directories are caches and cookie stores.

The `usr/.time_travel` exclusion drops more than file contents: every
snapshot commit of the shadow git ends with base64 JSON naming the
chat (`context_id`), the project, the trigger and the time
([`plugins/_time_travel/helpers/time_travel.py:1192-1194`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_time_travel/helpers/time_travel.py#L1192-L1194),[`1206-1220`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_time_travel/helpers/time_travel.py#L1206-L1220)),
so it is a record of which chat changed which files that outlives a
chat delete (2026-10-19 review). Its size was not measured. The
launcher's WSL directory on Windows is a whole Linux disk and is not a
candidate for collection by default.

## 5. Project-local files

Agent Zero "projects" are directories it owns under `usr/projects/<name>`
(git clones are made there, [`projects.py:121-151`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/projects.py#L121-L151)) with metadata in
`.a0proj/`; they are collected with `usr/`. Through the A0 CLI connector
the containerised agent reads and writes files and runs commands in the
host's current directory ([`acp.py:314`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/src/agent_zero_cli/acp.py#L314),
[`session.py:119`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/src/agent_zero_cli/session.py#L119)) but writes no Agent Zero state file there.

## 6. Where the project path is recorded

`usr/chats/<ctxid>/chat.json` key `data.project` holds the project name
([`projects.py:27`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/projects.py#L27),[`457`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/projects.py#L457)); the path is `usr/projects/<name>`.

Correction from the 2026-10-19 review: a host repository path is
recorded. A chat opened by an editor through ACP, the Agent Client
Protocol that the connector's `a0 acp` command serves, stores the
editor's workspace on the user's host as `data.acp_cwd` and any extra
folders as `data.acp_additional_directories` (a JSON list) in its
`chat.json`
([`plugins/_a0_acp/api/session.py:13-14`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_a0_acp/api/session.py#L13-L14),[`131-141`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_a0_acp/api/session.py#L131-L141)).
The keys were present at the commit first cited and were missed. The
`chat.json` is on the host only where `usr/` is (installer, launcher
host-directory mode, a native run) or in a collected volume, and the
path names a directory on whichever host ran the editor, which need not
be the host running Agent Zero. A plain A0 CLI chat records no host
path: the connector's working directory stays on the host side
([`a0-connector session.py:131`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/session.py#L131));
no key for it was found in agent-zero's `plugins/_a0_connector` at
[`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a)
(grepped for `workspace` and `cwd`).

## 7. Confidence

High: every path under the install directory and its `usr/` layout
(constants), the installer and launcher defaults, the connector files. Medium:
the Electron `userData` paths for the launcher (Electron default from
`productName`, no `setPath` found); `Desktop/agent-zero`, which is only the
docs example; whether `*agent-zero*` over-matches in real homes. Not
determined: where native installs are cloned in practice (the catalog cannot
find a clone outside the two listed paths, and a named Docker volume is never
under a home; both need a manual collection, or a separate issue for
collecting Docker volumes); the desktop plugin's credential files beyond the
literal paths found; whether plugin state such as
`usr/plugins/_telegram_integration/state.json` holds bot tokens.
