# langflow

Langflow is a Python visual agent builder (`langflow` and the `lfx` package), served as an
open-source (OSS) server and as Langflow Desktop, a closed-source desktop build. It came into
the catalog from the agent framework sweep for
[issue #64](https://github.com/seanthegeek/doubleagent/issues/64); see
[`research/frameworks.md`](frameworks.md) for the frameworks that got no catalog line. Its
parser is in the backlog ([issue 141](https://github.com/seanthegeek/doubleagent/issues/141)).

## 1. Source and evidence

[langflow-ai/langflow](https://github.com/langflow-ai/langflow), MIT
([LICENSE:1-3](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/LICENSE#L1-L3)),
commit
[`504c02fc47e76087b82b0e7cbe4186e9cdd916d4`](https://github.com/langflow-ai/langflow/commit/504c02fc47e76087b82b0e7cbe4186e9cdd916d4).
The OSS paths are from source. **Langflow Desktop is closed source; its paths rest on the
documentation in this repository only.** Platform directory resolution is cited from
[tox-dev/platformdirs](https://github.com/tox-dev/platformdirs) at
[`960ff632eb575deb6f0d5bf49519d5a2ee2098b6`](https://github.com/tox-dev/platformdirs/commit/960ff632eb575deb6f0d5bf49519d5a2ee2098b6).

Langflow executes code on the host: custom component code is `exec`'d in the server process
([validate.py:692](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/custom/validate.py#L692)),
there is a Python Interpreter component
([python_repl_core.py:13-14](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/components/utilities/python_repl_core.py#L13-L14)),
and MCP stdio servers are spawned on the host
([mcp/util.py:2166](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/base/mcp/util.py#L2166)).

### Observed

- No real install: nothing was installed or run.

### Source reviews

- **Source review (2026-10-19)**: HEAD
  [`972d56c`](https://github.com/langflow-ai/langflow/commit/972d56c47d3830d17060ee85cfaad152df823041)
  reviewed against the previously cited
  [`504c02f`](https://github.com/langflow-ai/langflow/commit/504c02fc47e76087b82b0e7cbe4186e9cdd916d4),
  from source only; the open-source schema is the one the server's
  `langflow.db` uses, and that Langflow Desktop's `database.db` uses it
  too is an inference, since Desktop is closed source. Detail in
  [Database detail](#database-detail).
  - Permission state: none recorded per call. The Langflow Assistant's
    canvas edits are proposals the user approves in a UI card, and the
    approval is not stored
    ([router.py:435-438](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/agentic/api/router.py#L435-L438));
    standing governance is in `policy_bundle_revision` and
    `model_provider_policy` (approved providers, blocked components and
    models), and `audit_events` logs actions on resources.
  - Model: found: `span` rows of the native tracer, on by default, carry
    the model of each LLM call.
  - Past use beyond the primary store: found: `trace` and `span`,
    `transaction` (now with `session_id`), `vertex_build`, `flow_version`
    and `audit_events` all outlive a session delete, which removes only
    `message` rows.
  - Sync: found for flows, not sessions: `deployment` rows record a flow
    pushed to an external provider account under a remote `resource_key`;
    third-party tracers (LangSmith, Langfuse, LangWatch and others) send
    runs out when their environment variables are set, with no local
    marker.
  - Scratch directories: found ([Scratch directories](#scratch-directories)):
    `.langflow/fs_tool/fs_sandbox`, the
    Assistant's file sandbox, already collected by `langflow|.langflow`.
  - Deletion: found: a session delete removes its `message` rows; a flow
    delete removes messages, transactions, vertex builds, versions and
    traces.
  - Version drift: paths unchanged; `paths.py` lines moved (the config directory validator is now at
    [paths.py:67-76](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/lfx/src/lfx/services/settings/groups/paths.py#L67-L76)),
    `AUTO_LOGIN` now defaults to `False` in release packages, and the tables `audit_events`,
    `trigger` (with `trigger_event`) and `data_subject_request` are new since
    [`504c02f`](https://github.com/langflow-ai/langflow/commit/504c02fc47e76087b82b0e7cbe4186e9cdd916d4).
  - Bad lines: no line-oriented file is collected apart from logs; every
    store is SQLite.

## Collection

### 2. Per-user storage

The config directory is `LANGFLOW_CONFIG_DIR`, otherwise
`platformdirs.user_cache_dir("langflow", "langflow")`
([paths.py:55-62](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/services/settings/groups/paths.py#L55-L62)):

- Linux: `~/.cache/langflow`, or under `XDG_CACHE_HOME`
  ([unix.py:58-60](https://github.com/tox-dev/platformdirs/blob/960ff632eb575deb6f0d5bf49519d5a2ee2098b6/src/platformdirs/unix.py#L58-L60),
  [_xdg.py:55-56](https://github.com/tox-dev/platformdirs/blob/960ff632eb575deb6f0d5bf49519d5a2ee2098b6/src/platformdirs/_xdg.py#L55-L56)).
- macOS: `~/Library/Caches/langflow`
  ([macos.py:49-51](https://github.com/tox-dev/platformdirs/blob/960ff632eb575deb6f0d5bf49519d5a2ee2098b6/src/platformdirs/macos.py#L49-L51)).
- Windows: `%LOCALAPPDATA%\langflow\langflow\Cache`
  ([windows.py:37-51](https://github.com/tox-dev/platformdirs/blob/960ff632eb575deb6f0d5bf49519d5a2ee2098b6/src/platformdirs/windows.py#L37-L51),
  [70-73](https://github.com/tox-dev/platformdirs/blob/960ff632eb575deb6f0d5bf49519d5a2ee2098b6/src/platformdirs/windows.py#L70-L73)).
  The author segment is doubled even where the code omits `appauthor`
  (`user_cache_dir("langflow")` in
  [logger.py:1217](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/log/logger.py#L1217)).

| Path | Holds | Default or opt-in |
| --- | --- | --- |
| `.cache/langflow`; `Library/Caches/langflow`; `AppData/Local/langflow/langflow/Cache` | `secret_key` (Fernet key for `variable`), `cache_secret_key`, `<user_id>/` uploaded files and `_mcp_servers_<id>.json`, `profile_pictures` (copied assets), and `langflow.db` only when opted in ([auth.py:352-361](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/services/settings/auth.py#L352-L361), [cache/service.py:35](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/services/cache/service.py#L35), [services/utils.py:316-317](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/services/utils.py#L316-L317), [setup.py:690-691](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/initial_setup/setup.py#L690-L691)) | default |
| `.langflow/knowledge_bases` | Chroma knowledge and memory bases ([paths.py:13](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/services/settings/groups/paths.py#L13)) | default |
| `.langflow/fs_tool/fs_sandbox` | files the Langflow Assistant's FileSystem tool reads and writes ([assistant_workspace.py:34](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/agentic/helpers/assistant_workspace.py#L34), [64](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/agentic/helpers/assistant_workspace.py#L64)) | default when the Assistant runs |
| Desktop, macOS: `.langflow/data` (`database.db`, `.env`), `Library/Application Support/com.LangflowDesktop` (venv), `Library/Logs/com.LangflowDesktop`, `Library/Caches/com.LangflowDesktop` | Desktop database, environment, logs ([memory.mdx:15-17](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Develop/memory.mdx#L15-L17), [environment-variables.mdx:329](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Develop/environment-variables.mdx#L329), [logging.mdx:18-21](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Develop/logging.mdx#L18-L21), [troubleshooting.mdx:142](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Support/troubleshooting.mdx#L142), [315-319](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Support/troubleshooting.mdx#L315-L319)) | default (docs) |
| Desktop, Windows: `AppData/Roaming/com.LangflowDesktop` (`data/database.db`, `data/.env`, `knowledge_bases`), `AppData/Local/com.LangflowDesktop` (venv, `logs`, `cache`) | as above ([memory.mdx:18](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Develop/memory.mdx#L18), [environment-variables.mdx:345](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Develop/environment-variables.mdx#L345), [logging.mdx:21](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Develop/logging.mdx#L21), [troubleshooting.mdx:331](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Support/troubleshooting.mdx#L331)) | default (docs) |

`Library/Caches/com.LangflowDesktop` is a cache and has no catalog line.
The docs disagree with the code on the OSS knowledge bases:
[memory-bases.mdx:173-179](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docs/docs/Develop/memory-bases.mdx#L173-L179)
places them in `site-packages`, but the code default is
`~/.langflow/knowledge_bases`. The code wins.

#### Scratch directories

`.langflow/fs_tool/fs_sandbox` is the Langflow
Assistant's own file workspace (in the table above); the
`langflow|.langflow` catalog line collects it, so the
analyzer's home-catalog rule would class it as a scratch directory if a
parser ever named it as a project. Nothing else is a working directory.

#### OSS database

The OSS database is not under the home: `langflow.db` defaults to the installed package directory
(`site-packages/langflow/`), because `save_db_in_config_dir` is `False`
([database.py:18](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/services/settings/groups/database.py#L18),
[110-121](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/lfx/src/lfx/services/settings/groups/database.py#L110-L121)).
It holds the tables `message`, `transaction` (run history) and `vertex_build`
([message/model.py:183](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/services/database/models/message/model.py#L183),
[transactions/model.py:158](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/services/database/models/transactions/model.py#L158),
[vertex_builds/model.py:70](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/src/backend/base/langflow/services/database/models/vertex_builds/model.py#L70)),
plus `variable` (encrypted credentials). A virtual environment has no fixed home path, so the
database is a manual step in [`collectors/docs/coverage.md`](../collectors/docs/coverage.md). A
`uv tool` install would put it under `.local/share/uv/tools/langflow/...`, but uv was not cited, so
that line was not added.

#### Docker

The named volume `langflow-data` is mounted at `/app/langflow`,
which is the config directory (`LANGFLOW_CONFIG_DIR=/app/langflow`), so its
root holds `secret_key`, `cache_secret_key` and `profile_pictures`.
PostgreSQL uses the volume `langflow-postgres`
([docker_example/docker-compose.yml:13-15](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docker_example/docker-compose.yml#L13-L15),
[30-34](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docker_example/docker-compose.yml#L30-L34)),
which is a whole PostgreSQL cluster the analyzer cannot read and is left
unmatched. The image home is `/app/data`
([build_and_push.Dockerfile:209](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docker/build_and_push.Dockerfile#L209),
[226](https://github.com/langflow-ai/langflow/blob/504c02fc47e76087b82b0e7cbe4186e9cdd916d4/docker/build_and_push.Dockerfile#L226)).

#### Database detail

Detail from the 2026-10-19 review, at
[`972d56c`](https://github.com/langflow-ai/langflow/commit/972d56c47d3830d17060ee85cfaad152df823041),
for a future parser over Desktop's `database.db` (or a
server `langflow.db` collected by hand):

- **Model.** The native tracer is on unless `LANGFLOW_NATIVE_TRACING` is
  `false`
  ([native.py:110-115](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/tracing/native.py#L110-L115)).
  It writes a `trace` row per run (name, status, times, `total_tokens`,
  `flow_id`, `session_id`) and a `span` row per component and LangChain
  call, named `{operation} {model}`, with `inputs`, `outputs` and
  `attributes`; the model name is kept per LLM span and read back from
  the `gen_ai.response.model` attribute
  ([traces/model.py:134-160](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/traces/model.py#L134-L160),
  [284-330](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/traces/model.py#L284-L330),
  [native.py:442](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/tracing/native.py#L442),
  [formatting.py:124](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/tracing/formatting.py#L124)).
  `message` has no model column
  ([message/model.py:30-45](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/message/model.py#L30-L45)).
- **Other run records.** `transaction` now carries `user_id` and
  `session_id`
  ([transactions/model.py:122-123](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/transactions/model.py#L122-L123)),
  so a component run joins its chat session; `vertex_build` and
  `flow_version` (saved versions of a flow) are per flow; `audit_events`
  (new) records `action`, `operation`, `event_type`, `result`, the actor
  and the resource with a `timestamp` and `details` JSON
  ([audit_event/model.py:68-120](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/audit_event/model.py#L68-L120));
  `trigger` and `trigger_event` (new) hold scheduled and event-driven flow
  runs
  ([trigger/model.py:54-57](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/trigger/model.py#L54-L57),
  [142-145](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/trigger/model.py#L142-L145)).
- **Standing policy.** `policy_bundle_revision` keeps every revision of
  the deployment policy (`approved_provider_ids`,
  `blocked_component_keys`, `blocked_model_keys`,
  `approved_integration_provider_ids` and others) with `created_by`
  ([policy_bundle/model.py:20-60](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/policy_bundle/model.py#L20-L60)),
  beside `model_provider_policy`
  ([model_provider_policy/model.py:8-11](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/model_provider_policy/model.py#L8-L11)).
- **Flows pushed out.** `deployment` rows name a flow deployed to an
  external provider account (`deployment_provider_account`) under the
  provider's `resource_key`, with the display name synced from the
  provider
  ([deployment/model.py:21-55](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/deployment/model.py#L21-L55)).
  LangSmith, Langfuse, LangWatch, Arize Phoenix, Opik, Openlayer and
  Traceloop tracers are enabled by their own environment variables (for
  example `LANGCHAIN_API_KEY`, `LANGFUSE_SECRET_KEY`) and keep no local
  row
  ([langsmith.py:128](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/tracing/langsmith.py#L128),
  [langfuse.py:610-612](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/tracing/langfuse.py#L610-L612)).
- **Deletion.** Deleting a session removes its `message` rows and its
  memory-base data, nothing else
  ([monitor.py:533-557](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/api/v1/monitor.py#L533-L557),
  [message/crud.py:71-84](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/services/database/models/message/crud.py#L71-L84)),
  so the session's `transaction`, `trace` and `span` rows survive it.
  Deleting a flow removes its triggers, messages, transactions, vertex
  builds, versions, traces and spans
  ([flow_utils.py:124-185](https://github.com/langflow-ai/langflow/blob/972d56c47d3830d17060ee85cfaad152df823041/src/backend/base/langflow/api/utils/flow_utils.py#L124-L185)).

### 3. Credentials

- `secret_key` and `cache_secret_key` in the config directory, in each
  OS's location and at the root of a `*langflow-data` volume: flagged.
- The Desktop `data/.env` (macOS `.langflow/data/.env`, Windows
  `AppData/Roaming/com.LangflowDesktop/data/.env`): flagged.
- `_mcp_servers_*.json` may embed environment values for MCP servers; not
  flagged.

### 4. Exclusions

`.langflow/knowledge_bases`, the Desktop `knowledge_bases`, `venv`,
`python_env` and `cache` directories, and `profile_pictures` in the config
directory (home-relative in each OS's location, and volume-relative).

### 5. Project-local files

None. Flows are rows in the database.

### 6. Where the project path is recorded

Nowhere; Langflow has no project concept.

## Parsing

Langflow is `backlog`: its parser is
[issue 141](https://github.com/seanthegeek/doubleagent/issues/141), and nothing it writes is
parsed yet. A parser would read Langflow Desktop's `database.db` (or a server `langflow.db`
collected by hand, since the server's database is not under the home and is not collected,
[OSS database](#oss-database)): `message` rows for the chat, `transaction` (which joins a
component run to its chat session), `vertex_build` and `flow_version`, the native tracer's
`trace` and `span` rows for the model of each LLM call, `audit_events`, `trigger` and
`trigger_event`, `policy_bundle_revision` and `model_provider_policy` for standing policy, and
`deployment` rows for flows pushed out ([Database detail](#database-detail)). That Desktop's
`database.db` uses the open-source schema is an inference, since Desktop is closed source.

## 14. Confidence

High for the OSS paths (source). Medium for Desktop, which rests on docs
only. Not determined: where Desktop keeps its `secret_key`, and the Desktop
Linux layout, which the docs do not give.
