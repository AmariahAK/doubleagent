# CrewAI: on-disk paths

This document came out of the agent framework sweep for issue #64; see
[frameworks.md](frameworks.md) for the frameworks that got no catalog line.
There is no analyzer document yet.

## 1. Source and evidence level

[crewAIInc/crewAI](https://github.com/crewAIInc/crewAI), MIT, open source, commit
[`e836a191cfe524feb519c6952a458c9f1e1ff0ef`](https://github.com/crewAIInc/crewAI/commit/e836a191cfe524feb519c6952a458c9f1e1ff0ef).
The repository ships the `crewai` library, `crewai-core`, the `crewai` CLI
(`lib/cli`) and `crewai-tools`. All claims are from source; nothing was
installed or run.

Path resolution uses `appdirs~=1.4.4`
([lib/crewai-core/pyproject.toml:11](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/pyproject.toml#L11)),
not platformdirs, read in [ActiveState/appdirs](https://github.com/ActiveState/appdirs) at
[`8734277956c1df3b85385e6b308e954910533884`](https://github.com/ActiveState/appdirs/commit/8734277956c1df3b85385e6b308e954910533884).
`user_data_dir(appname, appauthor)` is `$XDG_DATA_HOME/<appname>` or
`~/.local/share/<appname>` on Linux, `~/Library/Application Support/<appname>`
on macOS, and `%LOCALAPPDATA%\<appauthor>\<appname>` on Windows, where
`appauthor` defaults to `appname` and is ignored on Linux and macOS
([appdirs.py:76-93](https://github.com/ActiveState/appdirs/blob/8734277956c1df3b85385e6b308e954910533884/appdirs.py#L76-L93)).
`user_cache_dir` is `~/.cache/<appname>`, `~/Library/Caches/<appname>` and
`%LOCALAPPDATA%\<appauthor>\<appname>\Cache`
([appdirs.py:297-315](https://github.com/ActiveState/appdirs/blob/8734277956c1df3b85385e6b308e954910533884/appdirs.py#L297-L315)).

CrewAI runs on the host: agents run arbitrary user-defined Python tools,
`FileWriterTool` writes host files
([file_writer_tool.py:165](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-tools/src/crewai_tools/tools/file_writer_tool/file_writer_tool.py#L165)),
and MCP stdio servers are spawned
([mcp/transports/stdio.py:83-97](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/mcp/transports/stdio.py#L83-L97)).
The built-in CodeInterpreterTool is gone
([agent/core.py:293-297](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/agent/core.py#L293-L297)).

- **Source review (2026-10-19)**: HEAD
  [`65cdd70`](https://github.com/crewAIInc/crewAI/commit/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2)
  reviewed against the previously cited
  [`e836a19`](https://github.com/crewAIInc/crewAI/commit/e836a191cfe524feb519c6952a458c9f1e1ff0ef),
  from source only. AMP (Agent Management Platform) is CrewAI's hosted
  service, and Wharf is the trace intake that the source names as the
  place a run's spans are sent
  ([last_run.py:1-7](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/telemetry/tracing/last_run.py#L1-L7)).
  - Permission state: found. Paused Flow reviews are rows of
    `pending_feedback` in the opt-in `flow_states.db`, and the trace consent
    is a standing setting in `.crewai_user.json`
    ([section 2](#2-per-user-storage)). No per-tool approval exists: a task's
    `human_input` review is asked on the console and its answer becomes a
    user message in the task's `messages`
    ([human_input.py:46](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/core/providers/human_input.py#L46)).
  - Model: none in the run database. `latest_kickoff_task_outputs` keeps the
    agent's role (`agent`), not its model; the only stored model string is
    the `llm` of a pending Flow review
    ([async_feedback/types.py:38](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/flow/async_feedback/types.py#L38)).
    Not found in `kickoff_task_outputs_storage.py` or `last_run.py` at
    [`65cdd70`](https://github.com/crewAIInc/crewAI/commit/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2) (grepped for `model` and `llm`).
  - Past use beyond the primary store: found, and the run database is not
    a history: every kickoff empties `latest_kickoff_task_outputs` before
    its first task
    ([crews/utils.py:339](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/crews/utils.py#L339),
    [task_output_storage_handler.py:79-81](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/utilities/task_output_storage_handler.py#L79-L81)),
    so it holds the last run only. Opt-in checkpoints in the project's
    `.checkpoints/` and the project's `.crewai/last_run.json` outlive it
    ([section 5](#5-project-local-files)).
  - Sync: found. A traced run is uploaded to AMP, and the project's
    `.crewai/last_run.json` records its execution id, trace tier and AMP
    trace URL ([section 5](#5-project-local-files)).
  - Scratch directories: none; CrewAI runs in the user's working directory.
  - Deletion: found. `crewai reset-memories -k` (or `-a`) empties the run
    table
    ([cli.py:478-482](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/cli.py#L478-L482),
    [crew.py:2486-2490](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/crew.py#L2486-L2490));
    it leaves `last_run.json`, the checkpoints and the remote trace.
  - Version drift: the paths and tables below are unchanged apart from
    line shifts in `flow/persistence/sqlite.py`; the eval-awaiting markers
    are now JSON files and their directory is derived from the account's
    home rather than `appdirs` on Linux and macOS
    ([crew_run_tui.py:357-376](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/crew_run_tui.py#L357-L376)),
    the same path as before; `crewai eval export` is new
    ([section 5](#5-project-local-files)).
  - Bad lines: no line-oriented file; every store is SQLite or a JSON
    document.

## 2. Per-user storage

The run data directory comes from `db_storage_path()`:
`appdirs.user_data_dir(<CREWAI_STORAGE_DIR or the basename of the working directory>, "CrewAI")`
([crewai_core/paths.py:11-26](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/paths.py#L11-L26)).
The directory is therefore named after the project folder:
`~/.local/share/<project>`, `~/Library/Application Support/<project>` and
`%LOCALAPPDATA%\CrewAI\<project>`. Only Windows has a fixed `CrewAI`
component, which is why the Linux and macOS catalog lines are anchored on
CrewAI's own file names below a `*` segment.

| Path (`<data>` = the run data directory) | Holds | Default or opt-in |
| --- | --- | --- |
| `<data>/latest_kickoff_task_outputs.db` (+ WAL) | table `latest_kickoff_task_outputs`: task_id, task_key, expected_output, output JSON (raw, pydantic, agent, messages), inputs, timestamp ([crew.py:224-225](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/crew.py#L224-L225), [task_output_storage_handler.py:25-27](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/utilities/task_output_storage_handler.py#L25-L27), [crew.py:1510-1520](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/crew.py#L1510-L1520), [kickoff_task_outputs_storage.py:25-60](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/memory/storage/kickoff_task_outputs_storage.py#L25-L60)) | default: every `Crew` creates it and every task writes a row |
| `<data>/.crewai_user.json` | trace consent, first-execution flag ([user_data.py:23-26](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/user_data.py#L23-L26)) | default (tracing check) |
| `<data>/memory/` (LanceDB), `memory/qdrant-edge` | agent memory ([crew.py:256-269](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/crew.py#L256-L269), [lancedb_storage.py:69-75](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/memory/storage/lancedb_storage.py#L69-L75), [qdrant_edge_storage.py:104-110](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/memory/storage/qdrant_edge_storage.py#L104-L110)) | opt-in (`memory=True`; default `False`) |
| `<data>/flow_states.db` | Flow state snapshots ([flow/persistence/sqlite.py:71](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/flow/persistence/sqlite.py#L71)) | opt-in (`@persist`) |
| `<data>/` Chroma files, `qdrant/` | knowledge and RAG stores ([rag/chromadb/constants.py:11](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/rag/chromadb/constants.py#L11), [rag/qdrant/constants.py:12](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/rag/qdrant/constants.py#L12)) | opt-in (knowledge sources) |
| `.config/crewai/settings.json` on every OS (falls back to the temp dir, then the working directory) | CLI settings: enterprise URL, org, OAuth2 config, `tool_repository_username` and `password` ([settings.py:26](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/settings.py#L26), [85-89](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/settings.py#L85-L89), [166-171](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/settings.py#L166-L171), [246-259](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/settings.py#L246-L259)) | written by CLI login and config |
| `.local/share/crewai/credentials/`, `Library/Application Support/crewai/credentials/`, `AppData/Local/crewai/credentials/` | `secret.key` (Fernet key), `tokens.enc` (encrypted access token and expiry) ([token_manager.py:22-34](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/token_manager.py#L22-L34), [87-97](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/token_manager.py#L87-L97)) | written by `crewai login` |
| `user_data_dir("crewai", "CrewAI")/eval-awaiting` | CLI TUI eval markers ([crew_run_tui.py:320-323](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/cli/src/crewai_cli/crew_run_tui.py#L320-L323)) | CLI |
| `.crewai/skills/<org>/<name>`, `.crewai/model_catalog_cache.json`, `.crewai/provider_cache.json` | downloaded skills, model lists ([skills/cache.py:24](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai/src/crewai/skills/cache.py#L24), [model_catalog.py:594-599](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/cli/src/crewai_cli/model_catalog.py#L594-L599), [provider.py:215-217](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/cli/src/crewai_cli/provider.py#L215-L217)) | CLI and skills |
| `user_cache_dir("crewai")/version_cache.json` | update check ([version.py:44](https://github.com/crewAIInc/crewAI/blob/e836a191cfe524feb519c6952a458c9f1e1ff0ef/lib/crewai-core/src/crewai_core/version.py#L44)) | cache only, not collected |

On Windows `%LOCALAPPDATA%\crewai\credentials` and
`%LOCALAPPDATA%\CrewAI\<project>` share one parent (NTFS is
case-insensitive), and the token directory looks like a project named
`credentials`. A Windows image mounted on Linux can hold either spelling,
so the catalog line is the class `AppData/Local/[Cc]rew[Aa][Ii]` rather
than two lines that differ only by case (issue 29).

Detail from the 2026-10-19 review, at
[`65cdd70`](https://github.com/crewAIInc/crewAI/commit/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2):

- `.crewai_user.json` holds `first_execution_done` and `trace_consent`,
  the standing answer to "share traces with AMP": the run's first-run
  prompt writes both
  ([ephemeral.py:144](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/telemetry/tracing/ephemeral.py#L144)),
  and so do `crewai traces enable` and `crewai traces disable`
  ([cli.py:1327](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/cli.py#L1327),
  [1348](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/cli.py#L1348)).
  `CREWAI_TRACING_ENABLED=true` in the environment or the project's `.env`
  overrides a recorded refusal
  ([user_data.py:77-91](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai-core/src/crewai_core/user_data.py#L77-L91)).
  The file sits in the run data directory, so the consent is per project
  folder name.
- `flow_states.db` has two tables: `flow_states` (`flow_uuid`,
  `method_name`, `timestamp`, `state_json`), one row per persisted step,
  and `pending_feedback` (`flow_uuid`, `context_json`, `state_json`,
  `created_at`), a Flow paused for a human review; the row is removed when
  the Flow resumes
  ([sqlite.py:74-76](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/flow/persistence/sqlite.py#L74-L76),
  [113-139](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/flow/persistence/sqlite.py#L113-L139),
  [332](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/flow/persistence/sqlite.py#L332)).
- `latest_kickoff_task_outputs` (columns `task_id`, `task_key`,
  `expected_output`, `output`, `task_index`, `inputs`, `was_replayed`,
  `timestamp`) is emptied at the start of every kickoff
  ([kickoff_task_outputs_storage.py:49-58](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/memory/storage/kickoff_task_outputs_storage.py#L49-L58),
  [crews/utils.py:339](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/crews/utils.py#L339)),
  so it shows the latest run of each project folder name and nothing
  earlier.
- The `eval-awaiting/<token>` files are JSON (`trusted_amp_origins`,
  `tracing_turned_on`) that live while `crewai eval` waits for a run
  ([crew_run_tui.py:409-420](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/crew_run_tui.py#L409-L420)).

**Scratch directories.** None. CrewAI creates no working directory of its
own; tools and checkpoints write relative to the directory the crew was
started from, which is the user's project.

**Memory gap.** On Linux and macOS the opt-in `memory/`, Chroma and Qdrant
stores under `<data>/` have no CrewAI-specific name to anchor a glob on, so
the catalog collects the run database, the flow database and
`.crewai_user.json` but not the memory stores beside them. A responder who
finds a run database should copy its sibling directory by hand; see
[coverage.md](../docs/coverage.md). On Windows the whole `CrewAI`
directory is collected.

Docker: no compose file or named volume.

## 3. Credentials

- `credentials/secret.key` and `credentials/tokens.enc`: the key decrypts
  the token, so both are flagged.
- `.config/crewai/settings.json`: flagged; it can hold
  `tool_repository_password` in plaintext.

## 4. Exclusions

None at default. The opt-in Chroma and LanceDB stores can be large, but
they are agent memory, and on Linux and macOS they are not collected
anyway ([section 2](#2-per-user-storage)).

## 5. Project-local files

A CrewAI project is ordinary Python code, and the run directory is per
project but lives under the home ([section 2](#2-per-user-storage)). The
2026-10-19 review at
[`65cdd70`](https://github.com/crewAIInc/crewAI/commit/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2)
found these files that CrewAI writes inside the project directory (the
working directory of the run); none is in `PROJECT_CATALOG`:

- `.crewai/last_run.json`: the last traced run whose spans reached AMP:
  `execution_id`, `tier` (`ephemeral` without a login, `authenticated`
  with one), `started_at`, `finished_at`, `recorded_at`, `amp_base_url`
  and, when AMP granted one, `trace_url`. It is written for every traced
  run, not only for `crewai eval`, and it is the local mark that the run's
  trace is on the vendor's servers
  ([last_run.py:35-36](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/telemetry/tracing/last_run.py#L35-L36),
  [56-57](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/telemetry/tracing/last_run.py#L56-L57),
  [86-98](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/telemetry/tracing/last_run.py#L86-L98),
  [grants.py:208](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/telemetry/tracing/grants.py#L208)).
- `.crewai/last_eval.json`: `execution_id` and `at` of the run the
  `crewai eval` app evaluated
  ([eval_crew.py:466-495](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/experimental/eval_crew.py#L466-L495)).
- `.crewai/eval_project_state.json`: the `execution_id` of the evaluated
  run and `files`, every project file by relative path with its
  modification time in nanoseconds and size (the `.env` included, other
  dotfiles left out): a listing of the project as it was when the run was
  sent for grading
  ([eval_crew.py:805-866](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/experimental/eval_crew.py#L805-L866)).
- `eval.jsonc`: the user's evaluation criteria, uploaded to AMP with the
  evaluation
  ([eval_crew.py:410-425](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/experimental/eval_crew.py#L410-L425)).
- `.env`: `crewai eval` writes `CREWAI_TRACING_ENABLED=true` into it when
  the user agrees to tracing
  ([eval_crew.py:205-224](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/experimental/eval_crew.py#L205-L224)).
- `crewai-eval-<id>/`: `crewai eval export <id>` downloads an evaluation
  from AMP (report, outputs, judge verdicts and the traces) with a
  `.gitignore` of `*`
  ([cli.py:794-807](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/cli.py#L794-L807),
  [eval_crew.py:2028](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/experimental/eval_crew.py#L2028)).
- `.checkpoints/` (opt-in, `checkpoint=True` on a Crew, Flow or Agent):
  one JSON file per checkpoint, named `{ts}_{uuid8}_p-{parent}.json`, or
  `.checkpoints.db` with the SQLite provider; written on `task_completed`
  by default and kept without limit unless `max_checkpoints` is set
  ([checkpoint_config.py:160-193](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/state/checkpoint_config.py#L160-L193),
  [json_provider.py:116](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/crewai/src/crewai/state/provider/json_provider.py#L116)).
  Unlike the run table, checkpoints survive the next kickoff. The
  directory name is generic, so a project-catalog line for it would also
  match other tools' checkpoints.

The `crewai create` template excludes `.crewai/` from the first commit
([git.py:8-9](https://github.com/crewAIInc/crewAI/blob/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2/lib/cli/src/crewai_cli/git.py#L8-L9)),
so git is no index of these files.

## 6. Where the project path is recorded

Only indirectly: the run data directory is named after the project
folder's basename, not its full path. Nothing records the full path, so
`discover_projects` has nothing to read. The project-local files in
[section 5](#5-project-local-files) hold no path either; the 2026-10-19
review found none in `last_run.py` or `eval_crew.py` at
[`65cdd70`](https://github.com/crewAIInc/crewAI/commit/65cdd70ac0fc0ba93c553fa30d3dd13a498559e2)
(grepped for `cwd` and `project_dir`: the working directory is used only
to locate the files, and `eval_project_state.json` keeps paths relative
to it).

## 7. Confidence

High for the paths and the default or opt-in status of each store
(source). Medium for the Windows class line covering both spellings, which
follows from appdirs and NTFS rather than a Windows run. Not determined:
whether `CREWAI_STORAGE_DIR` is commonly set in deployments, which would
rename the run directory.
