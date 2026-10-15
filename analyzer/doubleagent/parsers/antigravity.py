"""Antigravity CLI (`agy`) and Antigravity desktop app conversations.

Antigravity stores each conversation as a SQLite database of protobuf blobs.
There is no public schema, so the message definitions below were taken from
the protobuf file descriptors embedded in the shipped `agy` binary (Google
Antigravity CLI, Linux x86-64, October 2026): `third_party/gemini_coder/proto/
trajectory.proto`, `third_party/jetski/cortex_pb/cortex.proto`,
`third_party/jetski/codeium_common_pb/codeium_common.proto` and
`third_party/jetski/jetski_cortex_pb/jetski_cortex.proto`. They were checked
against a real install. `analyzer/tools/proto_descriptors.py` re-extracts them
from a binary when a new release changes the format.

Descriptor drift check (2026-10-13): `exa.cortex_pb.CortexStepType`,
`CortexStepStatus`, `CortexTrajectorySource`, `gemini_coder.Step` and every
message in `SCHEMA` were diffed against the descriptors of `agy` 1.2.16
(macOS arm64) and of the desktop app's `language_server` 2.23.0 (macOS
arm64). Field numbers, names and types match in both, and `STEP_TYPES` lists
the same 118 values; nothing drifted from the Linux x86-64 descriptors the
tables were built from. The diff did find one error in the tables
themselves: `ActionSpecDeleteFile` keeps its `path` in field 1, and the
parser had read it with the `ActionSpecCreateFile` layout (field 2); it has
its own entry since analyzer 0.12.0 (issue 88). The new real data has steps
with `permissions` (`gemini_coder.Step` field 133, read since analyzer 0.12.0,
issue 92) and `task_details` (148, not read).

The CLI and the desktop app run the same Go backend (the app calls it the
language server) and write the same stores, each into its own data
directory under `~/.gemini`:

* `antigravity-cli/`: the CLI's (`trajectory_meta.source` 17, `cli`).
* `antigravity/`: the desktop app 2.x's (`source` 1, `cascade_client`); the
  app passes the name to the backend as `--app_data_dir`, and its summaries
  rows carry it in `app_data_dir`.
* `antigravity-ide/`: the separately installed Antigravity IDE's, after the
  app's install wizard migrates pre-2.0 IDE data out of `antigravity/`.
* `antigravity-backup/`: the backup the app takes during that migration.

Files, relative to the home directory, under each of those directories
(`<dir>`):

* `.gemini/<dir>/conversations/<conversation id>.db`, with `-wal`
  and `-shm` sidecars (WAL mode, so the sidecars hold the newest steps):
  - `trajectory_meta(trajectory_id, cascade_id, trajectory_type, source)`:
    `cascade_id` is the conversation id; `source` is a
    `CortexTrajectorySource` (`TRAJECTORY_SOURCES`).
  - `trajectory_metadata_blob(id, data)`: `exa.cortex_pb.CortexTrajectoryMetadata`
    with `workspaces[].workspace_folder_absolute_uri` and `branch_name`,
    `created_at`, `parent_conversation_id`, `project_id`.
  - `steps(idx, step_type, status, metadata, step_payload, ...)`: one row
    per step. `step_payload` is a `gemini_coder.Step` whose `metadata`
    (`exa.cortex_pb.CortexStepMetadata`) carries `created_at`,
    `completed_at`, `source` and the `tool_call` the step executed
    (`exa.codeium_common_pb.ChatToolCall`: `id`, `name`, `arguments_json`).
    The payload oneof names the step kind: `user_input.query`,
    `planner_response.response` with `thinking` and `tool_calls[]`, and one
    message per tool (`run_command`, `view_file`, `write_to_file`,
    `code_action`, `mcp_tool`, `generic`, ...), plus `system_message`
    (`message`, `event_type`; step type 101) and `error_message`
    (`error.short_error`, `user_error_message`, `full_error`; step type 17),
    both seen in the desktop app's real data and yielded as `system` rows.
  - `gen_metadata(idx, data)`: `exa.cortex_pb.CortexStepGeneratorMetadata`
    with `step_indices[]` and `chat_model.response_model`, the only place
    the model name is recorded.
  - `steps.permissions`: an `exa.cortex_pb.TrajectoryPermissions`, the same
    message as `gemini_coder.Step` field 133 (read from the payload when the
    column is empty): `permission_grants[]` (`PermissionGrant`: 1
    `resource` {1 `action`, 2 `target`}, 2 `allow`, 3 `scope`, 4
    `user_deny_instruction`, 5 `action`, 6 `target`) and
    `file_access_permissions[]` (`FileAccessPermission`: 1 `path`, 2
    `is_directory`, 3 `allow`, 4 `scope`, 5 `from_current_step`); `scope` is
    an `exa.cortex_pb.PermissionScope` (`PERMISSION_SCOPES`). Proto3 omits a
    false bool and a zero enum, so a missing `allow` reads `false` and a
    missing `scope` `unspecified`.
* `.gemini/<dir>/conversation_summaries.db`, table
  `conversation_summaries`: one row per conversation with `title`,
  `preview`, `step_count`, `last_modified_time`, `workspace_uris` (JSON
  array), `status`, `agent_name`, `parent_conversation_id`, `project_id`.
  The app's copy also has an FTS5 table `conversations_fts` and
  `search_schema_version`, which are not read.
* `.gemini/antigravity-cli/history.jsonl` (CLI only; the app writes none):
  `{display, timestamp, workspace}` per prompt, `timestamp` in epoch
  milliseconds; from CLI 1.3.x a line may also carry `conversationId`, the
  conversation's UUID, which becomes the row's `session_id` (older lines
  have none and keep it empty). A secondary source: the timeline drops a
  line whose event a conversation database also records (`dedup.py`).
* `.gemini/<dir>/brain/<conversation id>/.system_generated/logs/`, the brain
  mirror (issue 87): one JSON line per step, written by the backend beside
  the database, in four copies of one transcript: `transcript_full.jsonl`;
  `transcript.jsonl`, the same lines with long fields shortened and the
  shortened field names in `truncated_fields`; and each split into chunks
  of 100 KiB, `chunks/transcript_full/<n>.jsonl` and
  `chunks/transcript/<n>.jsonl` (`<n>` eight digits from 00000000), cut
  mid-line at the boundary. One copy is read per conversation, the most
  complete present: `transcript_full.jsonl`, else its chunks concatenated
  in order (which makes the cut line whole), else `transcript.jsonl`, else
  its chunks; the other copies yield nothing. Fields read: `type`
  (`USER_INPUT`, `PLANNER_RESPONSE`, `GENERIC`, `SYSTEM_MESSAGE`,
  `ERROR_MESSAGE`), `source` (`USER_EXPLICIT`, `USER_IMPLICIT`, `MODEL`,
  `SYSTEM`), `status` (`DONE`, `ERROR`, ...), `created_at` (ISO 8601),
  `content`, `thinking`, `tool_calls[]` (`id`, `name` and the arguments as
  `arguments_json`, `args` or `arguments`, an object or a JSON string;
  the element shape is not recorded from a real install, so the parser
  takes the first of the three it finds), `error` (an object with
  `short_error`, `user_error_message`, `full_error`, or a string) and
  `truncated_fields`. The key names are from the real installs
  (`analyzer/research/antigravity.md` section 2); the value forms of
  `source`, `status`, `created_at` and `truncated_fields` are from the
  format description embedded in `agy` 1.3.6 (macOS arm64). Not read:
  `step_index`, `media`, the token counts, and the brain directory's
  `steps/<idx>/output.txt`, `steps/<idx>/content.md`,
  `messages/<uuid>.json` and `tasks/task-<idx>.log`.
  Rows, rendered as the database reader renders the step of the same
  kind so the timeline can pair them: `USER_INPUT` a `user` row (`system`
  when `source` is `USER_IMPLICIT`); `PLANNER_RESPONSE` a `thinking` row
  (`--include-thinking` only), an `assistant` row when `content` is not
  empty and one `tool_use` row per `tool_calls[]` entry, its text the
  argument `tool_args_summary` picks; `GENERIC` a `tool_result` row,
  `content` as text, with the `tool_name` and `tool_use_id` of the next
  unused call of the last `PLANNER_RESPONSE` (the line itself names no
  call; the database runs a planner step's calls as the steps after it,
  so the n-th `GENERIC` line after it is taken as the n-th call), a
  `system` row when no call is pending; `SYSTEM_MESSAGE` a `system` row
  `system_message: <content>`; `ERROR_MESSAGE` a `system` row
  `error: <error>`; any other type a `tool_result` or `system` row as for
  `GENERIC`. `GENERIC`, `SYSTEM_MESSAGE`, `ERROR_MESSAGE` and other rows
  get `[<status>] ` in front when `status` is not `DONE`, as the database
  rows do. A row whose field is in `truncated_fields` ends with
  ` [truncated: <field>]`. Every row has the line's `created_at`,
  `session_id` the `<conversation id>` of the directory (the database's
  `cascade_id`), `source_line` the line number (in the concatenated chunks
  for a chunked copy, whose `source_file` is the first chunk), and empty
  `project_path`, `git_branch` and `model`, which the mirror does not
  record; no model or permission rows, for the same reason. A bad line is
  one `system` row after the others.
  A secondary source of the conversation database: the timeline drops a
  row the database also yields. Its time rule: the mirror records only a
  step's `created_at`, while the database reader stamps `assistant`,
  `tool_use` and `tool_result` rows with the step's `completed_at`, so the
  mirror's row comes before the database's by the time the model took to
  generate the response or the tool took to run. `secondary_tolerance` is
  therefore 600 seconds; a step that ran longer than ten minutes is shown
  twice. Known misses, kept as two rows: a `SYSTEM_MESSAGE` whose database
  step has an `event_type` (the database row reads `<event_type>:
  <message>`, and the mirror records no event type), a queued prompt
  (the database row starts `[queued] `), a shortened field of a row
  without a `tool_use_id` (a shortened tool call or result pairs on its
  id), and a `GENERIC` line whose `content` differs from the database
  step's `generic.result.result` with no tool id inferred for it, which
  no install has compared. A conversation's opening prompt that
  `history.jsonl` records without `conversationId` is matched once: the
  history row, matched by workspace, can take the database row first, and
  the mirror's row then pairs with the history row under the broader
  scope of `dedup.deduplicate`.

Standing permission files (issue 92), read only for the keys named here;
every other key in them (`plugins`, `remoteControlHostname`, a project's
`name`, a sidecar's `args`) is left unread, and `plugin_data/*/token.json`
and `.gemini/config/mcp_config.json` are never wanted:

* `.gemini/config/config.json` (shared by the CLI and the app):
  `userSettings.globalPermissionGrants.allow[]` (tool-call patterns, a tool
  name with its argument in parentheses), `.deny[]` when present (not
  observed), `userSettings.permissionGrantsV2Migrated`,
  `userSettings.sandboxEnabledAtV2Migration`, and per automation
  `sidecars.<name>.enabled` and `sidecars.<name>.resolvedPermissions.accessGrants[]`.
* `.gemini/config/projects/<id>.json`: `permissionGrants.permissionGrants.allow[]`
  (and `.deny[]` when present, not observed) and `permissionGrants.v2Migrated`;
  `project_path` is the first `projectResources.resources[].folderUri`.
* `.gemini/config/sidecars/<name>/sidecar.json`: `agent_permissions.access_grants[]`.
* `.gemini/antigravity-cli/settings.json`: `permissions.allow[]` (and
  `.deny[]` when present, not observed) and `trustedWorkspaces[]`, each
  trusted workspace a row whose `project_path` is the workspace.

Rows: one `user` row per user_input step (`system` when the source is
USER_IMPLICIT); for each planner_response step an `assistant` row, one
`tool_use` row per proposed tool call, and a `thinking` row with
`--include-thinking`; one `tool_result` row per executed tool step, keyed by
the planner's call id; `system` rows for the session start, checkpoints,
system messages, errors and the conversation summary. The session start
row's text names `source=<trajectory source>` (the number when it is not in
`TRAJECTORY_SOURCES`) and `data_dir=<the .gemini subdirectory>`, so a CLI
conversation and a desktop-app one can be told apart. Step timestamps come
from the step metadata; tool results use `completed_at`.

Permission rows (issue 92), all `system`: after a step's own rows, one
`permission grant: action=<action> target=<target> allow=<true|false>
scope=<scope>` row per `permission_grants[]` entry (` deny_instruction=<text>`
appended when the user gave one) and one `permission grant: path=<path>
is_directory=<true|false> allow=<true|false> scope=<scope>` row per
`file_access_permissions[]` entry (` from_current_step=true` appended when
set), with the step's `tool_name` and `tool_use_id`, the step's index as
`source_line` and the step's tool-result time. From each standing file, one
`permission setting: <key>=<value> (from <path relative to the home>, file
mtime)` row per list entry and per flag, `<key>` the JSON path in the file
(`trustedWorkspace` for a `trustedWorkspaces[]` entry), timestamped by the
file's modification time (the manifest's `mtime`, or the file's own when
there is no manifest), `session_id` empty, `source_line` the entry's
1-based position among the file's rows.

Model rows (issue 96), `system`: `model: <id>` before the rows of the
conversation's first step that `gen_metadata` names a model for, and
`model: <old> -> <new>` before the rows of every later step whose model
differs, with the step's `created_at`, its index as `source_line` and the
new id in the `model` column. The id is `chat_model.response_model`, else
`model_display_name`; the descriptors give no separate switch record, so a
change is seen only as a different model on a later step.

Per-call rows (issue 97): a `run_command` step with `user_rejected` (field
14) or an `mcp_tool` step with `user_rejected` (field 7) yields, right
after its `tool_result` row (which keeps its `[rejected by user]` marker),
a `system` row `permission decision: user_rejected` with the step's
`tool_name`, `tool_use_id` and result time. A `run_command` step with
`ran_in_sandbox` (field 34) gets ` sandbox=true` at the end of its result
row's text.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlparse

from ..inputs import Artifact
from ..model import Row, compact
from ..protobuf import Schema, decode
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    file_mtime,
    iter_jsonl,
    setting_value,
    text_of,
    track_change,
)

BASE = ".gemini/antigravity-cli/"
# The four data directories under ~/.gemini that hold the same stores: the
# CLI's, the desktop app's, the separately installed IDE's and the backup the
# app takes when it migrates pre-2.0 IDE data. Group 1 is the directory name.
DATA_DIR = r"^\.gemini/(antigravity(?:-cli|-ide|-backup)?)/"
CONV_RX = re.compile(DATA_DIR + r"conversations/[^/]+\.db$")
SUMMARIES_RX = re.compile(DATA_DIR + r"conversation_summaries\.db$")
HISTORY_REL = BASE + "history.jsonl"
# The brain mirror (issue 87): per conversation, the step transcript in its
# complete form, its shortened twin, or either split into numbered chunks.
# Group 2 is the conversation id; group 3 the file form, or groups 4 and 5
# the chunked form and the chunk number.
BRAIN_RX = re.compile(
    DATA_DIR + r"brain/([^/]+)/\.system_generated/logs/"
    r"(?:(transcript(?:_full)?)\.jsonl|chunks/(transcript(?:_full)?)/(\d+)\.jsonl)$"
)
FULL = "transcript_full"
SHORT = "transcript"
# How far a brain row's time may be from the database row's for the timeline
# to pair them: the mirror records only `created_at`, the database reader
# stamps assistant, tool_use and tool_result rows with `completed_at`.
BRAIN_TOLERANCE_SECONDS = 600.0
# Standing permission files (issue 92).
CONFIG_REL = ".gemini/config/config.json"
PROJECT_RX = re.compile(r"^\.gemini/config/projects/[^/]+\.json$")
SIDECAR_RX = re.compile(r"^\.gemini/config/sidecars/[^/]+/sidecar\.json$")
CLI_SETTINGS_REL = BASE + "settings.json"

# exa.cortex_pb.PermissionScope, lower-cased without the PERMISSION_SCOPE_
# prefix: how long a permission grant holds.
PERMISSION_SCOPES = {
    0: "unspecified",
    1: "once",
    2: "conversation",
    3: "workspace",
    4: "global",
    5: "project",
}

# exa.cortex_pb.CortexTrajectorySource, lower-cased without the prefix: the
# surface that started the conversation (trajectory_meta.source).
TRAJECTORY_SOURCES = {
    0: "unspecified",
    1: "cascade_client",
    2: "explain_problem",
    3: "refactor_function",
    4: "eval",
    5: "eval_task",
    6: "async_prr",
    7: "async_cf",
    8: "async_sl",
    9: "async_prd",
    10: "async_cm",
    12: "interactive_cascade",
    13: "replay",
    15: "sdk",
    16: "subagent",
    17: "cli",
    18: "jetbox",
    19: "agent_api",
    20: "cider",
    21: "gemini_app",
    22: "vscode",
    23: "visual_studio",
}

# exa.cortex_pb.CortexStepType, lower-cased without the prefix.
STEP_TYPES = {
    0: "unspecified",
    1: "dummy",
    2: "finish",
    3: "plan_input",
    4: "mquery",
    5: "code_action",
    6: "git_commit",
    7: "grep_search",
    8: "view_file",
    9: "list_directory",
    10: "compile",
    13: "view_code_item",
    14: "user_input",
    15: "planner_response",
    17: "error_message",
    21: "run_command",
    23: "checkpoint",
    24: "propose_code",
    25: "find",
    27: "suggested_responses",
    28: "command_status",
    29: "memory",
    31: "read_url_content",
    32: "view_content_chunk",
    33: "search_web",
    34: "retrieve_memory",
    38: "mcp_tool",
    39: "manager_feedback",
    40: "tool_call_proposal",
    41: "tool_call_choice",
    42: "trajectory_choice",
    45: "clipboard",
    47: "view_file_outline",
    49: "post_pr_review",
    51: "list_resources",
    52: "read_resource",
    53: "lint_diff",
    54: "find_all_references",
    55: "brain_update",
    56: "open_browser_url",
    57: "run_extension_code",
    59: "proposal_feedback",
    60: "trajectory_search",
    61: "execute_browser_javascript",
    62: "list_browser_pages",
    63: "capture_browser_screenshot",
    64: "click_browser_pixel",
    65: "read_terminal",
    66: "capture_browser_console_logs",
    67: "read_browser_page",
    68: "browser_get_dom",
    73: "code_search",
    74: "browser_input",
    75: "browser_move_mouse",
    76: "browser_select_option",
    77: "browser_scroll_up",
    78: "browser_scroll_down",
    79: "browser_click_element",
    80: "browser_press_key",
    81: "task_boundary",
    82: "notify_user",
    83: "code_acknowledgement",
    84: "internal_search",
    85: "browser_subagent",
    86: "file_change",
    87: "move",
    88: "browser_scroll",
    89: "knowledge_generation",
    90: "ephemeral_message",
    91: "generate_image",
    92: "delete_directory",
    93: "compile_applet",
    94: "install_applet_dependencies",
    95: "install_applet_package",
    96: "browser_resize_window",
    97: "browser_drag_pixel_to_pixel",
    98: "conversation_history",
    99: "knowledge_artifacts",
    100: "send_command_input",
    101: "system_message",
    102: "wait",
    103: "agency_tool_call",
    104: "cider_agent_dummy",
    105: "build_cleaner",
    106: "blaze_build_targets",
    107: "blaze_test_targets",
    108: "set_up_firebase",
    109: "moma",
    110: "restart_dev_server",
    111: "deploy_firebase",
    112: "shell_exec",
    113: "browser_mouse_wheel",
    114: "lint_applet",
    116: "ki_insertion",
    117: "retrieve_content",
    118: "critique",
    119: "findings",
    120: "browser_mouse_up",
    121: "browser_mouse_down",
    122: "workspace_api",
    123: "browser_list_network_requests",
    124: "browser_get_network_request",
    125: "browser_refresh_page",
    126: "edit_notebook",
    127: "invoke_subagent",
    128: "write_blob",
    129: "read_notebook",
    130: "propose_ai_comments",
    131: "start_code_review",
    132: "generic",
    133: "set_up_cloud_sql",
    134: "execute_notebook",
    135: "cloud_sql_update_schema",
    136: "rpc_action",
    137: "cloud_sql_execute_sql",
    138: "ask_question",
    139: "directory_rules",
    140: "tool_search",
}

# exa.cortex_pb.CortexStepStatus
STEP_STATUS = {
    0: "unspecified",
    1: "pending",
    2: "running",
    3: "done",
    4: "invalid",
    5: "cleared",
    6: "canceled",
    7: "error",
    8: "generating",
    9: "waiting",
    11: "queued",
    12: "interrupted",
}

STEP_SOURCE_USER_IMPLICIT = 3  # exa.cortex_pb.CortexStepSource

# Field numbers from the embedded descriptors; only the fields the parser reads.
SCHEMA: Schema = {
    "Step": {
        1: ("type", "int"),
        4: ("status", "int"),
        5: ("metadata", "CortexStepMetadata"),
        10: ("code_action", "CortexStepCodeAction"),
        12: ("finish", "CortexStepFinish"),
        13: ("grep_search", "CortexStepGrepSearch"),
        14: ("view_file", "CortexStepViewFile"),
        15: ("list_directory", "CortexStepListDirectory"),
        19: ("user_input", "CortexStepUserInput"),
        20: ("planner_response", "CortexStepPlannerResponse"),
        23: ("write_to_file", "CortexStepWriteToFile"),
        24: ("error_message", "CortexStepErrorMessage"),
        28: ("run_command", "CortexStepRunCommand"),
        30: ("checkpoint", "CortexStepCheckpoint"),
        31: ("error", "CortexErrorDetails"),
        34: ("find", "CortexStepFind"),
        37: ("command_status", "CortexStepCommandStatus"),
        38: ("memory", "CortexStepMemory"),
        40: ("read_url_content", "CortexStepReadUrlContent"),
        42: ("search_web", "CortexStepSearchWeb"),
        47: ("mcp_tool", "CortexStepMcpTool"),
        93: ("task_boundary", "CortexStepTaskBoundary"),
        94: ("notify_user", "CortexStepNotifyUser"),
        98: ("file_change", "CortexStepFileChange"),
        103: ("ephemeral_message", "CortexStepEphemeralMessage"),
        111: ("conversation_history", "CortexStepConversationHistory"),
        113: ("send_command_input", "CortexStepSendCommandInput"),
        114: ("system_message", "CortexStepSystemMessage"),
        116: ("agency_tool_call", "CortexStepAgencyToolCall"),
        127: ("shell_exec", "CortexStepShellExec"),
        133: ("permissions", "TrajectoryPermissions"),
        140: ("generic", "CortexStepGeneric"),
        143: ("invoke_subagent", "CortexStepInvokeSubagent"),
        154: ("ask_question", "CortexStepAskQuestion"),
        156: ("directory_rules", "CortexStepDirectoryRules"),
    },
    "CortexStepMetadata": {
        1: ("created_at", "ts"),
        3: ("source", "int"),
        4: ("tool_call", "ChatToolCall"),
        7: ("finished_generating_at", "ts"),
        8: ("completed_at", "ts"),
        12: ("execution_id", "str"),
        30: ("tool_summary", "str"),
        31: ("tool_action", "str"),
        32: ("started_at", "ts"),
    },
    "ChatToolCall": {
        1: ("id", "str"),
        2: ("name", "str"),
        3: ("arguments_json", "str"),
        9: ("original_name", "str"),
    },
    "CortexStepUserInput": {
        1: ("query", "str"),
        2: ("user_response", "str"),
        6: ("is_queued_message", "bool"),
    },
    "CortexStepPlannerResponse": {
        1: ("response", "str"),
        3: ("thinking", "str"),
        6: ("message_id", "str"),
        7: ("+tool_calls", "ChatToolCall"),
        8: ("modified_response", "str"),
        16: ("raw_thinking", "str"),
    },
    "CortexStepGeneric": {1: ("+args", "KV"), 2: ("result", "GenericStepResult")},
    "KV": {1: ("key", "str"), 2: ("value", "str")},
    "GenericStepResult": {1: ("result", "str"), 7: ("full_output_uri", "str")},
    "CortexStepRunCommand": {
        1: ("command", "str"),
        2: ("cwd", "str"),
        4: ("stdout", "str"),
        5: ("stderr", "str"),
        6: ("exit_code", "int"),
        14: ("user_rejected", "bool"),
        21: ("combined_output", "RunCommandOutput"),
        23: ("command_line", "str"),
        34: ("ran_in_sandbox", "bool"),
        37: ("timed_out", "bool"),
    },
    "RunCommandOutput": {1: ("full", "str"), 2: ("truncated", "str")},
    "CortexStepCommandStatus": {
        1: ("command_id", "str"),
        3: ("stdout", "str"),
        4: ("stderr", "str"),
        5: ("exit_code", "int"),
        9: ("combined", "str"),
    },
    "CortexStepShellExec": {
        1: ("command", "str"),
        2: ("exit_code", "int"),
        3: ("output", "str"),
        4: ("error_message", "str"),
    },
    "CortexStepSendCommandInput": {
        1: ("command_id", "str"),
        2: ("input", "str"),
        6: ("terminate", "bool"),
    },
    "CortexStepViewFile": {
        1: ("absolute_path_uri", "str"),
        2: ("start_line", "int"),
        3: ("end_line", "int"),
        17: ("is_skill_file", "bool"),
    },
    "CortexStepListDirectory": {1: ("directory_path_uri", "str")},
    "CortexStepGrepSearch": {
        1: ("query", "str"),
        10: ("command_run", "str"),
        11: ("search_path_uri", "str"),
    },
    "CortexStepFind": {
        1: ("pattern", "str"),
        9: ("command_run", "str"),
        10: ("search_directory", "str"),
    },
    "CortexStepWriteToFile": {1: ("target_file_uri", "str"), 4: ("file_created", "bool")},
    "CortexStepFileChange": {
        1: ("absolute_path_uri", "str"),
        2: ("file_change_type", "int"),
        5: ("instruction", "str"),
    },
    "CortexStepCodeAction": {
        1: ("action_spec", "ActionSpec"),
        8: ("code_instruction", "str"),
        26: ("description", "str"),
    },
    "ActionSpec": {
        1: ("command", "ActionSpecCommand"),
        2: ("create_file", "ActionSpecPath"),
        4: ("delete_file", "ActionSpecDeleteFile"),
        5: ("sed", "ActionSpecSed"),
    },
    "ActionSpecCommand": {1: ("instruction", "str"), 4: ("file", "PathScopeItem")},
    "ActionSpecPath": {1: ("instruction", "str"), 2: ("path", "PathScopeItem")},
    "ActionSpecDeleteFile": {1: ("path", "PathScopeItem")},
    "ActionSpecSed": {3: ("path", "PathScopeItem")},
    "PathScopeItem": {1: ("absolute_path_migrate_me_to_uri", "str"), 5: ("absolute_uri", "str")},
    "CortexStepReadUrlContent": {1: ("url", "str"), 3: ("resolved_url", "str")},
    "CortexStepSearchWeb": {1: ("query", "str"), 5: ("summary", "str")},
    "CortexStepMcpTool": {
        1: ("server_name", "str"),
        2: ("tool_call", "ChatToolCall"),
        3: ("result_string", "str"),
        7: ("user_rejected", "bool"),
    },
    "CortexStepAgencyToolCall": {1: ("agent_name", "str"), 2: ("function_name", "str")},
    "CortexStepInvokeSubagent": {
        1: ("subagent_name", "str"),
        2: ("prompt", "str"),
        5: ("conversation_id", "str"),
        10: ("+results", "SubagentResult"),
    },
    "SubagentResult": {1: ("conversation_id", "str")},
    "CortexStepAskQuestion": {1: ("+questions", "AskQuestionEntry")},
    "AskQuestionEntry": {
        1: ("question", "str"),
        4: ("+selected_option_ids", "str"),
        5: ("write_in_response", "str"),
        6: ("skipped", "bool"),
    },
    "CortexStepCheckpoint": {
        4: ("user_intent", "str"),
        5: ("session_summary", "str"),
        10: ("conversation_title", "str"),
    },
    "CortexStepMemory": {1: ("memory_id", "str"), 3: ("action", "int")},
    "CortexStepFinish": {2: ("output_string", "str")},
    "CortexStepErrorMessage": {3: ("error", "CortexErrorDetails")},
    "CortexErrorDetails": {
        1: ("user_error_message", "str"),
        2: ("short_error", "str"),
        3: ("full_error", "str"),
    },
    "CortexStepSystemMessage": {1: ("message", "str"), 3: ("event_type", "str")},
    "CortexStepEphemeralMessage": {1: ("content", "str")},
    "CortexStepTaskBoundary": {
        1: ("task_name", "str"),
        2: ("task_status", "str"),
        3: ("task_summary", "str"),
    },
    "CortexStepNotifyUser": {2: ("notification_content", "str")},
    "CortexStepDirectoryRules": {2: ("+rule_file_uris", "str")},
    "CortexStepConversationHistory": {1: ("content", "str")},
    "TrajectoryPermissions": {
        1: ("+file_access_permissions", "FileAccessPermission"),
        2: ("+permission_grants", "PermissionGrant"),
    },
    "PermissionGrant": {
        1: ("resource", "PermissionResource"),
        2: ("allow", "bool"),
        3: ("scope", "int"),
        4: ("user_deny_instruction", "str"),
        5: ("action", "str"),
        6: ("target", "str"),
    },
    "PermissionResource": {1: ("action", "str"), 2: ("target", "str")},
    "FileAccessPermission": {
        1: ("path", "str"),
        2: ("is_directory", "bool"),
        3: ("allow", "bool"),
        4: ("scope", "int"),
        5: ("from_current_step", "bool"),
    },
    "CortexTrajectoryMetadata": {
        1: ("+workspaces", "CortexWorkspaceMetadata"),
        2: ("created_at", "ts"),
        5: ("parent_conversation_id", "str"),
        6: ("root_conversation_id", "str"),
        7: ("+workspace_uris", "str"),
        17: ("nesting_depth", "int"),
        18: ("project_id", "str"),
    },
    "CortexWorkspaceMetadata": {
        1: ("workspace_folder_absolute_uri", "str"),
        2: ("git_root_absolute_uri", "str"),
        4: ("branch_name", "str"),
    },
    "CortexStepGeneratorMetadata": {
        1: ("chat_model", "ChatModelMetadata"),
        2: ("+step_indices", "int"),
    },
    "ChatModelMetadata": {
        19: ("response_model", "str"),
        21: ("model_display_name", "str"),
        22: ("response_model_full", "str"),
    },
}

# The oneof step kinds: every Step field but the scalars, the metadata and
# the permissions that sit beside the step kind.
PAYLOAD_KINDS = [
    name
    for num, (name, kind) in SCHEMA["Step"].items()
    if kind not in ("int", "CortexStepMetadata", "TrajectoryPermissions")
]

# Which JSON argument best identifies a proposed tool call, tried in order.
ARG_KEYS = (
    "CommandLine",
    "Command",
    "AbsolutePath",
    "TargetFile",
    "AbsolutePathUri",
    "Path",
    "DirectoryPath",
    "Url",
    "Query",
    "SearchPath",
    "Pattern",
    "Prompt",
    "Instruction",
    "TaskName",
    "Name",
)


def uri_to_path(uri: str) -> str:
    if not uri:
        return ""
    if not uri.startswith("file:"):
        return uri
    p = unquote(urlparse(uri).path)
    if re.match(r"^/[A-Za-z]:", p):
        p = p[1:]
    return p


def tool_args_summary(arguments_json: str) -> str:
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except ValueError:
        return arguments_json
    if isinstance(args, dict):
        for k in ARG_KEYS:
            v = args.get(k)
            if v not in (None, "", [], {}):
                return v if isinstance(v, str) else compact_json(v)
    return compact_json(args)


def _path_of(scope: dict | None) -> str:
    if not scope:
        return ""
    return uri_to_path(
        scope.get("absolute_uri") or scope.get("absolute_path_migrate_me_to_uri") or ""
    )


def _output(p: dict) -> str:
    combined = p.get("combined_output") or {}
    return (
        combined.get("full")
        or combined.get("truncated")
        or p.get("combined")
        or p.get("stdout")
        or p.get("stderr")
        or p.get("output")
        or ""
    )


def _join(*parts: str) -> str:
    return " | ".join(x for x in parts if x)


def _bool(v: object) -> str:
    return "true" if v else "false"


def _list(v: object) -> list:
    return v if isinstance(v, list) else []


def _dict(v: object) -> dict:
    return v if isinstance(v, dict) else {}


def _read_json(artifact: Artifact) -> object:
    """The parsed file, or None when it cannot be read or parsed."""
    try:
        return json.loads(artifact.disk_path.read_bytes().decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


def _regular(path: Path) -> bool:
    """True for a regular file, never through a symlink."""
    return path.is_file() and not path.is_symlink()


def _chunks(logs: Path, form: str) -> list[Path]:
    """The chunk files of `form` under `logs/chunks`, in chunk order."""
    d = logs / "chunks" / form
    try:
        names = [p for p in d.iterdir() if p.suffix == ".jsonl" and p.stem.isdigit()]
    except OSError:
        return []
    return sorted((p for p in names if _regular(p)), key=lambda p: int(p.stem))


def brain_copy(path: Path, form: str, chunk_form: str) -> bytes | None:
    """The bytes of the brain transcript that `path` stands for, or None when
    another copy of the same transcript is the one read. The copies, in order
    of preference: `transcript_full.jsonl`; its chunks, concatenated (a line
    cut at a chunk boundary is whole again); the shortened `transcript.jsonl`;
    its chunks. A chunked form is read through its first chunk present."""
    logs = path.parent if form else path.parent.parent.parent
    full = logs / (FULL + ".jsonl")
    if form == FULL:
        return path.read_bytes()
    if form == SHORT:
        if _regular(full) or _chunks(logs, FULL):
            return None
        return path.read_bytes()
    chunks = _chunks(logs, chunk_form)
    if not chunks or chunks[0].name != path.name:
        return None
    if _regular(full):
        return None
    if chunk_form == SHORT and (_chunks(logs, FULL) or _regular(logs / (SHORT + ".jsonl"))):
        return None
    return b"".join(p.read_bytes() for p in chunks)


def _brain_args(tc: dict) -> str:
    """A brain tool call's arguments as a JSON string: `arguments_json` as the
    database records it, else `args` or `arguments`, an object or a string."""
    for key in ("arguments_json", "args", "arguments"):
        v = tc.get(key)
        if isinstance(v, str) and v:
            return v
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
    return ""


def permission_texts(perms: dict) -> list[str]:
    """One `permission grant:` text per entry of a TrajectoryPermissions."""
    out = []
    for g in perms.get("permission_grants", []):
        res = g.get("resource") or {}
        scope = g.get("scope", 0)
        text = "permission grant: action=%s target=%s allow=%s scope=%s" % (
            g.get("action") or res.get("action", ""),
            g.get("target") or res.get("target", ""),
            _bool(g.get("allow")),
            PERMISSION_SCOPES.get(scope, str(scope)),
        )
        if g.get("user_deny_instruction"):
            text += " deny_instruction=" + g["user_deny_instruction"]
        out.append(text)
    for f in perms.get("file_access_permissions", []):
        scope = f.get("scope", 0)
        text = "permission grant: path=%s is_directory=%s allow=%s scope=%s" % (
            uri_to_path(f.get("path", "")),
            _bool(f.get("is_directory")),
            _bool(f.get("allow")),
            PERMISSION_SCOPES.get(scope, str(scope)),
        )
        if f.get("from_current_step"):
            text += " from_current_step=true"
        out.append(text)
    return out


def standing_entries(rel: str, doc: dict) -> list[tuple[str, object, str]]:
    """(key, value, project_path) for each permission entry of a standing
    file, reading only the keys the module docstring names."""
    out: list[tuple[str, object, str]] = []
    if rel == CONFIG_REL:
        us = _dict(doc.get("userSettings"))
        grants = _dict(us.get("globalPermissionGrants"))
        for lst in ("allow", "deny"):
            for v in _list(grants.get(lst)):
                out.append(("userSettings.globalPermissionGrants." + lst, v, ""))
        for k in ("permissionGrantsV2Migrated", "sandboxEnabledAtV2Migration"):
            if k in us:
                out.append(("userSettings." + k, us[k], ""))
        for name, sc in _dict(doc.get("sidecars")).items():
            sc = _dict(sc)
            if "enabled" in sc:
                out.append(("sidecars.%s.enabled" % name, sc["enabled"], ""))
            for v in _list(_dict(sc.get("resolvedPermissions")).get("accessGrants")):
                out.append(("sidecars.%s.resolvedPermissions.accessGrants" % name, v, ""))
    elif PROJECT_RX.match(rel):
        folder = ""
        for r in _list(_dict(doc.get("projectResources")).get("resources")):
            uri = _dict(r).get("folderUri")
            if isinstance(uri, str) and uri:
                folder = uri_to_path(uri)
                break
        pg = _dict(doc.get("permissionGrants"))
        inner = _dict(pg.get("permissionGrants"))
        for lst in ("allow", "deny"):
            for v in _list(inner.get(lst)):
                out.append(("permissionGrants.permissionGrants." + lst, v, folder))
        if "v2Migrated" in pg:
            out.append(("permissionGrants.v2Migrated", pg["v2Migrated"], folder))
    elif SIDECAR_RX.match(rel):
        for v in _list(_dict(doc.get("agent_permissions")).get("access_grants")):
            out.append(("agent_permissions.access_grants", v, ""))
    elif rel == CLI_SETTINGS_REL:
        perms = _dict(doc.get("permissions"))
        for lst in ("allow", "deny"):
            for v in _list(perms.get(lst)):
                out.append(("permissions." + lst, v, ""))
        for v in _list(doc.get("trustedWorkspaces")):
            path = uri_to_path(v) if isinstance(v, str) else ""
            out.append(("trustedWorkspace", path or v, path))
    return out


def describe_payload(kind: str, p: dict) -> str:
    """One line describing a tool step's result or a system event."""
    if kind == "run_command":
        return _join(
            p.get("command_line") or p.get("command") or "",
            "[rejected by user]" if p.get("user_rejected") else "",
            "[timed out]" if p.get("timed_out") else "",
            "exit=%s" % p["exit_code"] if "exit_code" in p else "",
            _output(p),
        )
    if kind in ("command_status", "shell_exec"):
        return _join(
            p.get("command", ""),
            "exit=%s" % p["exit_code"] if "exit_code" in p else "",
            _output(p) or p.get("error_message", ""),
        )
    if kind == "send_command_input":
        return "input to %s: %s%s" % (
            p.get("command_id", ""),
            p.get("input", ""),
            " [terminate]" if p.get("terminate") else "",
        )
    if kind == "view_file":
        rng = ""
        if p.get("start_line") or p.get("end_line"):
            rng = ":%s-%s" % (p.get("start_line", ""), p.get("end_line", ""))
        return uri_to_path(p.get("absolute_path_uri", "")) + rng
    if kind == "list_directory":
        return uri_to_path(p.get("directory_path_uri", ""))
    if kind == "grep_search":
        return _join(
            p.get("query", ""), uri_to_path(p.get("search_path_uri", "")), p.get("command_run", "")
        )
    if kind == "find":
        return _join(p.get("pattern", ""), p.get("search_directory", ""), p.get("command_run", ""))
    if kind == "write_to_file":
        return uri_to_path(p.get("target_file_uri", "")) + (
            " [created]" if p.get("file_created") else ""
        )
    if kind == "file_change":
        return _join(uri_to_path(p.get("absolute_path_uri", "")), p.get("instruction", ""))
    if kind == "code_action":
        spec = p.get("action_spec") or {}
        kindname = path = ""
        for key in ("command", "create_file", "delete_file", "sed"):
            sub = spec.get(key)
            if sub:
                kindname, path = key, _path_of(sub.get("file") or sub.get("path"))
                break
        return _join(kindname, path, p.get("description") or p.get("code_instruction", ""))
    if kind == "read_url_content":
        return p.get("resolved_url") or p.get("url", "")
    if kind == "search_web":
        return p.get("query", "")
    if kind == "mcp_tool":
        tc = p.get("tool_call") or {}
        return _join(
            "%s/%s" % (p.get("server_name", ""), tc.get("name", "")),
            "[rejected by user]" if p.get("user_rejected") else "",
            p.get("result_string", ""),
        )
    if kind == "agency_tool_call":
        return "%s.%s" % (p.get("agent_name", ""), p.get("function_name", ""))
    if kind == "invoke_subagent":
        children = " ".join(
            r.get("conversation_id", "") for r in p.get("results", []) if r.get("conversation_id")
        )
        return _join(
            p.get("subagent_name", ""),
            p.get("prompt", ""),
            "children: " + children if children else "",
        )
    if kind == "ask_question":
        qs = []
        for q in p.get("questions", []):
            ans = (
                q.get("write_in_response")
                or " ".join(q.get("selected_option_ids", []))
                or ("skipped" if q.get("skipped") else "")
            )
            qs.append(q.get("question", "") + (" -> " + ans if ans else ""))
        return "; ".join(qs)
    if kind == "generic":
        return (p.get("result") or {}).get("result", "")
    if kind == "checkpoint":
        return "checkpoint: " + (
            p.get("conversation_title") or p.get("session_summary") or p.get("user_intent", "")
        )
    if kind == "system_message":
        return "%s: %s" % (p.get("event_type") or "system_message", p.get("message", ""))
    if kind == "ephemeral_message":
        return "ephemeral: " + p.get("content", "")
    if kind == "task_boundary":
        return "task %s [%s]: %s" % (
            p.get("task_name", ""),
            p.get("task_status", ""),
            p.get("task_summary", ""),
        )
    if kind == "notify_user":
        return "notify user: " + p.get("notification_content", "")
    if kind in ("error", "error_message"):
        e = p.get("error", {}) if kind == "error_message" else p
        return "error: " + (
            e.get("short_error") or e.get("user_error_message") or e.get("full_error", "")
        )
    if kind == "finish":
        return "finish: " + p.get("output_string", "")
    if kind == "memory":
        return "memory %s action=%s" % (p.get("memory_id", ""), p.get("action", ""))
    if kind == "directory_rules":
        return "directory rules: " + " ".join(uri_to_path(u) for u in p.get("rule_file_uris", []))
    if kind == "conversation_history":
        return "conversation history injected (%d chars)" % len(p.get("content", ""))
    return compact_json(p)


class AntigravityParser(Parser):
    agent = "antigravity"
    name = "antigravity"

    def wants(self, artifact: Artifact) -> bool:
        return (
            artifact.rel == HISTORY_REL
            or bool(BRAIN_RX.match(artifact.rel))
            or bool(SUMMARIES_RX.match(artifact.rel))
            or bool(CONV_RX.match(artifact.rel))
            or self._standing(artifact.rel)
        )

    @staticmethod
    def _standing(rel: str) -> bool:
        return (
            rel in (CONFIG_REL, CLI_SETTINGS_REL)
            or bool(PROJECT_RX.match(rel))
            or bool(SIDECAR_RX.match(rel))
        )

    def secondary(self, artifact: Artifact) -> bool:
        return artifact.rel == HISTORY_REL or bool(BRAIN_RX.match(artifact.rel))

    def secondary_tolerance(self, artifact: Artifact) -> float:
        if BRAIN_RX.match(artifact.rel):
            return BRAIN_TOLERANCE_SECONDS
        return super().secondary_tolerance(artifact)

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if artifact.rel == HISTORY_REL:
            yield from self._parse_history(artifact, opts)
        elif BRAIN_RX.match(artifact.rel):
            yield from self._parse_brain(artifact, opts)
        elif self._standing(artifact.rel):
            yield from self._parse_standing(artifact)
        elif SUMMARIES_RX.match(artifact.rel):
            yield from self._parse_summaries(artifact, opts)
        else:
            yield from self._parse_conversation(artifact, opts)

    # -- history.jsonl ------------------------------------------------------------
    def _parse_history(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            row = self.base_row(artifact)
            row.source_line = n
            row.timestamp_utc = to_utc(rec.get("timestamp"))
            row.project_path = uri_to_path(str(rec.get("workspace") or ""))
            row.session_id = str(rec.get("conversationId") or "")
            row.turn_type = "user"
            row.text = compact(rec.get("display"))
            yield row

    # -- brain/<uuid>/.system_generated/logs ------------------------------------
    def _parse_brain(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        m = BRAIN_RX.match(artifact.rel)
        if not m:
            return
        blob = brain_copy(artifact.disk_path, m.group(3) or "", m.group(4) or "")
        if blob is None:
            return
        session_id = m.group(2)
        errors: list[int] = []
        calls: list[dict] = []
        for n, raw in enumerate(blob.split(b"\n"), 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw.decode("utf-8", errors="replace"))
            except ValueError:
                errors.append(n)
                continue
            if isinstance(rec, dict):
                yield from self._brain_rows(artifact, n, rec, session_id, calls, opts)
        if errors:
            row = self.base_row(artifact)
            row.session_id = session_id
            row.source_line = errors[0]
            row.turn_type = "system"
            row.text = "parser: %d unparseable line(s), first at line %d" % (
                len(errors),
                errors[0],
            )
            yield row

    def _brain_rows(
        self,
        artifact: Artifact,
        n: int,
        rec: dict,
        session_id: str,
        calls: list[dict],
        opts: Options,
    ) -> Iterator[Row]:
        """The rows of one brain line, rendered as `_step_rows` renders the
        database step of the same kind. `calls` holds the tool calls of the
        last PLANNER_RESPONSE not yet matched to a GENERIC line."""
        kind = str(rec.get("type") or "")
        status = str(rec.get("status") or "").lower()
        content = text_of(rec.get("content"))
        truncated = [str(f) for f in _list(rec.get("truncated_fields"))]

        def base(turn_type: str, text: str, field: str = "content") -> Row:
            row = self.base_row(artifact)
            row.source_line = n
            row.session_id = session_id
            row.timestamp_utc = to_utc(rec.get("created_at"))
            row.turn_type = turn_type
            if field in truncated:
                text += " [truncated: %s]" % field
            row.text = compact(text)
            return row

        if kind == "USER_INPUT":
            implicit = rec.get("source") == "USER_IMPLICIT"
            calls.clear()
            yield base("system" if implicit else "user", content)
            return
        if kind == "PLANNER_RESPONSE":
            thinking = text_of(rec.get("thinking"))
            if thinking and opts.include_thinking:
                yield base("thinking", thinking, "thinking")
            if content:
                yield base("assistant", content)
            calls[:] = [_dict(tc) for tc in _list(rec.get("tool_calls"))]
            for tc in calls:
                row = base("tool_use", tool_args_summary(_brain_args(tc)), "tool_calls")
                row.tool_name = str(tc.get("name") or "")
                row.tool_use_id = str(tc.get("id") or "")
                yield row
            return
        if kind == "SYSTEM_MESSAGE":
            text = "system_message: " + content
        elif kind == "ERROR_MESSAGE":
            err = rec.get("error")
            if isinstance(err, dict):
                err = (
                    err.get("short_error") or err.get("user_error_message") or err.get("full_error")
                )
            text = "error: " + (err if isinstance(err, str) and err else content)
        else:
            text = content or "step %s" % kind.lower()
        if status and status != "done":
            text = "[%s] %s" % (status, text)
        if kind in ("SYSTEM_MESSAGE", "ERROR_MESSAGE") or not calls:
            yield base("system", text)
            return
        tc = calls.pop(0)
        row = base("tool_result", text)
        row.tool_name = str(tc.get("name") or "")
        row.tool_use_id = str(tc.get("id") or "")
        yield row

    # -- standing permission files ----------------------------------------------
    def _parse_standing(self, artifact: Artifact) -> Iterator[Row]:
        doc = _read_json(artifact)
        mtime = file_mtime(artifact)
        if not isinstance(doc, dict):
            row = self.base_row(artifact)
            row.source_line = 1
            row.timestamp_utc = mtime
            row.turn_type = "system"
            row.text = "parser: unreadable %s" % artifact.rel
            yield row
            return
        for n, (key, value, project) in enumerate(standing_entries(artifact.rel, doc), 1):
            row = self.base_row(artifact)
            row.source_line = n
            row.timestamp_utc = mtime
            row.project_path = project
            row.turn_type = "system"
            row.text = compact(
                "permission setting: %s=%s (from %s, file mtime)"
                % (key, setting_value(value), artifact.rel)
            )
            yield row

    # -- conversation_summaries.db ----------------------------------------------
    def _parse_summaries(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            return
        with open_copy(artifact.disk_path) as con:
            if "conversation_summaries" not in table_names(con):
                return
            for n, r in enumerate(
                con.execute("select * from conversation_summaries order by last_modified_time"), 1
            ):
                r = dict(r)
                row = self.base_row(artifact)
                row.source_line = n
                row.session_id = str(r.get("conversation_id") or "")
                row.timestamp_utc = to_utc(r.get("last_modified_time"))
                try:
                    uris = json.loads(r.get("workspace_uris") or "[]")
                except ValueError:
                    uris = []
                row.project_path = uri_to_path(uris[0]) if uris else ""
                row.turn_type = "system"
                row.text = compact(
                    _join(
                        "conversation summary",
                        r.get("title") or r.get("preview") or "",
                        str(r.get("status") or ""),
                        "%s steps" % r.get("step_count", 0),
                        "agent=%s" % r["agent_name"] if r.get("agent_name") else "",
                        "parent=%s" % r["parent_conversation_id"]
                        if r.get("parent_conversation_id")
                        else "",
                    ),
                )
                yield row

    # -- conversations/<id>.db -----------------------------------------------------
    def _parse_conversation(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            return
        with open_copy(artifact.disk_path) as con:
            tables = table_names(con)
            if "steps" not in tables:
                return
            session_id = artifact.disk_path.name[:-3]
            project_path = branch = source = ""
            m = CONV_RX.match(artifact.rel)
            data_dir = m.group(1) if m else ""
            if "trajectory_meta" in tables:
                tm = con.execute("select * from trajectory_meta limit 1").fetchone()
                if tm:
                    session_id = tm["cascade_id"] or session_id
                    if tm["source"] is not None:
                        source = TRAJECTORY_SOURCES.get(tm["source"], str(tm["source"]))
            if "trajectory_metadata_blob" in tables:
                blob = con.execute("select data from trajectory_metadata_blob limit 1").fetchone()
                if blob and blob[0]:
                    try:
                        meta = decode(blob[0], "CortexTrajectoryMetadata", SCHEMA)
                    except ValueError:
                        meta = {}
                    ws = (meta.get("workspaces") or [{}])[0]
                    project_path = uri_to_path(
                        ws.get("workspace_folder_absolute_uri")
                        or (meta.get("workspace_uris") or [""])[0]
                    )
                    branch = ws.get("branch_name", "")
                    if meta.get("created_at"):
                        row = self._row(artifact, 0, session_id, project_path, branch)
                        row.timestamp_utc = meta["created_at"]
                        row.turn_type = "system"
                        row.text = compact(
                            _join(
                                "session start",
                                "source=%s" % source if source else "",
                                "data_dir=%s" % data_dir if data_dir else "",
                                "project_id=%s" % meta["project_id"]
                                if meta.get("project_id")
                                else "",
                                "parent=%s" % meta["parent_conversation_id"]
                                if meta.get("parent_conversation_id")
                                else "",
                            ),
                        )
                        yield row
            models: dict[int, str] = {}
            if "gen_metadata" in tables:
                for (data,) in con.execute("select data from gen_metadata"):
                    try:
                        gm = decode(data or b"", "CortexStepGeneratorMetadata", SCHEMA)
                    except ValueError:
                        continue
                    cm = gm.get("chat_model") or {}
                    model = cm.get("response_model") or cm.get("model_display_name") or ""
                    for idx in gm.get("step_indices", []):
                        models[idx] = model
            seen_models: dict = {}
            bad = 0
            cols = {r[1] for r in con.execute("pragma table_info(steps)")}
            perm_col = "permissions" if "permissions" in cols else "NULL AS permissions"
            for srow in con.execute(
                "select idx, step_type, status, metadata, step_payload, %s from steps order by idx"
                % perm_col
            ):
                idx = srow["idx"]
                try:
                    step = (
                        decode(srow["step_payload"], "Step", SCHEMA) if srow["step_payload"] else {}
                    )
                    if "metadata" not in step and srow["metadata"]:
                        step["metadata"] = decode(srow["metadata"], "CortexStepMetadata", SCHEMA)
                except ValueError:
                    bad += 1
                    continue
                model = models.get(idx, "")
                change = track_change("model", seen_models, session_id, model)
                if change:
                    # The model at the conversation's first generated step and
                    # on every change, before that step's own rows (#96).
                    md = step.get("metadata") or {}
                    row = self._row(artifact, idx, session_id, project_path, branch)
                    row.timestamp_utc = md.get("created_at") or md.get("completed_at", "")
                    row.turn_type = "system"
                    row.model = model
                    row.text = change
                    yield row
                yield from self._step_rows(
                    artifact,
                    idx,
                    srow["step_type"],
                    srow["status"],
                    step,
                    session_id,
                    project_path,
                    branch,
                    model,
                    opts,
                )
                yield from self._permission_rows(
                    artifact, idx, step, srow["permissions"], session_id, project_path, branch
                )
            if bad:
                row = self._row(artifact, 0, session_id, project_path, branch)
                row.turn_type = "system"
                row.text = "parser: %d step(s) could not be decoded" % bad
                yield row

    def _row(
        self, artifact: Artifact, idx: int, session_id: str, project_path: str, branch: str
    ) -> Row:
        row = self.base_row(artifact)
        row.source_line = idx
        row.session_id = session_id
        row.project_path = project_path
        row.git_branch = branch
        return row

    def _permission_rows(
        self,
        artifact: Artifact,
        idx: int,
        step: dict,
        column: bytes | None,
        session_id: str,
        project_path: str,
        branch: str,
    ) -> Iterator[Row]:
        """One `system` row per grant in the step's permissions: the
        `steps.permissions` column, else Step field 133 of the payload."""
        perms = step.get("permissions") or {}
        if column:
            try:
                perms = decode(column, "TrajectoryPermissions", SCHEMA)
            except ValueError:
                row = self._row(artifact, idx, session_id, project_path, branch)
                row.turn_type = "system"
                row.text = "parser: the permissions of step %d could not be decoded" % idx
                yield row
                return
        texts = permission_texts(perms)
        if not texts:
            return
        md = step.get("metadata") or {}
        tc = md.get("tool_call") or {}
        ts = md.get("completed_at") or md.get("finished_generating_at") or md.get("created_at", "")
        for text in texts:
            row = self._row(artifact, idx, session_id, project_path, branch)
            row.timestamp_utc = ts
            row.turn_type = "system"
            row.tool_name = tc.get("name") or tc.get("original_name", "")
            row.tool_use_id = tc.get("id", "")
            row.text = compact(text)
            yield row

    def _step_rows(
        self,
        artifact: Artifact,
        idx: int,
        step_type: int,
        status: int,
        step: dict,
        session_id: str,
        project_path: str,
        branch: str,
        model: str,
        opts: Options,
    ) -> Iterator[Row]:
        md = step.get("metadata") or {}
        created = md.get("created_at", "")
        completed = md.get("completed_at") or md.get("finished_generating_at") or created
        kind = next((k for k in PAYLOAD_KINDS if k in step), "")
        payload = step.get(kind) or {}
        status_name = STEP_STATUS.get(status, str(status))
        type_name = STEP_TYPES.get(step_type, str(step_type))

        def base(ts: str) -> Row:
            row = self._row(artifact, idx, session_id, project_path, branch)
            row.timestamp_utc = ts
            row.model = model
            return row

        if kind == "user_input":
            row = base(created)
            row.turn_type = "system" if md.get("source") == STEP_SOURCE_USER_IMPLICIT else "user"
            text = payload.get("query") or payload.get("user_response") or ""
            if payload.get("is_queued_message"):
                text = "[queued] " + text
            row.text = compact(text)
            yield row
            return

        if kind == "planner_response":
            thinking = payload.get("raw_thinking") or payload.get("thinking")
            if thinking and opts.include_thinking:
                row = base(created)
                row.turn_type = "thinking"
                row.text = compact(thinking)
                yield row
            text = payload.get("modified_response") or payload.get("response")
            if text:
                row = base(completed)
                row.turn_type = "assistant"
                row.text = compact(text)
                yield row
            for tc in payload.get("tool_calls", []):
                row = base(completed)
                row.turn_type = "tool_use"
                row.tool_name = tc.get("name") or tc.get("original_name", "")
                row.tool_use_id = tc.get("id", "")
                row.text = compact(tool_args_summary(tc.get("arguments_json", "")))
                yield row
            return

        tc = md.get("tool_call")
        text = describe_payload(kind, payload) if kind else "step %s" % type_name
        if status_name != "done":
            text = "[%s] %s" % (status_name, text)
        if kind == "run_command" and payload.get("ran_in_sandbox"):
            text += " sandbox=true"
        if tc:
            row = base(completed)
            row.turn_type = "tool_result"
            row.tool_name = tc.get("name") or tc.get("original_name", "")
            row.tool_use_id = tc.get("id", "")
        else:
            row = base(created)
            row.turn_type = "system"
        row.text = compact(text)
        yield row
        if kind in ("run_command", "mcp_tool") and payload.get("user_rejected"):
            # The user's rejection of the call as its own row, beside the
            # result that also carries `[rejected by user]` (#97).
            decision = base(row.timestamp_utc)
            decision.turn_type = "system"
            decision.tool_name = row.tool_name or (payload.get("tool_call") or {}).get("name", "")
            decision.tool_use_id = row.tool_use_id
            decision.text = "permission decision: user_rejected"
            yield decision
