# Output

What `detect` prints, the files `timeline` writes, and the
`timeline.jsonl` and `sessions.jsonl` schemas. Back to the
[analyzer README](../README.md).

## detect

`detect` prints the input, its kind (`archive`, `collected` for an extracted
collection, or `loose`), the host, any notes, and one line per user, home
and agent with the number of files, their bytes (from the manifest `size`,
or from disk in loose mode), and whether a parser exists. The notes cover the
archive hash check, unreadable `collection.json`, manifest rows that do not
parse, and how a loose root was interpreted. One `problem:` line follows the
notes for each directory or file inside the input that could not be read
(see [Unreadable inputs](inputs.md#unreadable-inputs)). `--files` adds one
`user<TAB>agent<TAB>path` line per attributed file. With `--json` the same
data is printed as one object with the keys `input`, `kind`, `host`,
`notes`, `homes` (`user`, `home`, `inferred`), `agents` (`user`, `home`,
`agent`, `files`, `bytes`, `parser`, `inferred`), `problems` (an array of
the problem line texts, without the `problem:` prefix), and with `--files`
also `files` (`user`, `agent`, `path`). Collections made by collectors before
1.6.0 also hold a `live/` system snapshot, which appears as agent `live`
with no user, and `detect only`.

## timeline

`timeline` writes three files into `-o`, creating the directory if needed,
and writes them even when no rows were produced:

```text
timeline.jsonl  one record per turn, tool call, tool result or system event
sessions.jsonl  one record per session with first and last timestamp and counts
detect.json     the detect --json object without its homes and files keys; its
                problems also hold the files a parser could not read
```

On stdout it prints the input, host and notes, one `problem:` line per
directory or file that could not be read (see
[Unreadable inputs](inputs.md#unreadable-inputs)), and, when the timeline
is filtered, a `window:` line with the resolved UTC bounds, a `match:`
line with the patterns, and a `filtered:` line counting the rows dropped
outside the window, without a timestamp, and not matching. Then come the
`agents:` line, the row count with a breakdown by agent and `turn_type`,
and the session count. The breakdown counts the rows written.

The `agents:` line is always one line. When the input holds at least one
agent it lists them in two or three groups; otherwise it reads
`none were found`:

```text
agents:    parsed: antigravity, claude-code; detected but not parsed: copilot-cli
agents:    parsed: claude-code; detected but not parsed: none
agents:    parsed: none; detected but not parsed: copilot-cli
agents:    parsed: claude-code; detected but not parsed: none; parser found no rows: antigravity
agents:    none were found
```

`parsed` names the agents that produced rows before filtering. `detected
but not parsed` names the agents in the input that have no parser (the
agents `detect` shows without one). `parser found no rows` names the agents
in the input that have a parser which read their files and produced no
rows, such as a data directory holding only an empty database; the group
appears only when it has an entry, and with `--agent` it counts only the
agents selected. Files tagged `project`, which every parser is offered, are
never listed in the last two groups. Each list is sorted and
comma-separated, and `parsed` or `detected but not parsed` reads `none`
when it is empty. `none were found` means the input holds no agent data,
where `detect` prints `no agent artifacts found`. Before analyzer 0.12.0
the line read `parsed <list>; detected only <list>`, with `none` for an
empty list.

## JSONL encoding

Both JSONL files are UTF-8 without a byte order mark, one JSON object per
line, each line ended by LF, with no header line. Every object has every
field, in the order listed below. Fields with no value hold the empty string
`""`, never `null`, and every field is a string except the integers
`source_line`, `user_turns`, `assistant_turns` and `tool_calls` and the
array `models`. A line holds no literal line break: newlines inside
`text` are written as `\n`, and U+2028 and U+2029 as `\u2028` and
`\u2029`, because some line readers split on them. Other non-ASCII text is
written as UTF-8, not escaped, so a search for it matches as typed; the
exception is a record whose text holds a lone UTF-16 surrogate, which UTF-8
cannot encode, and which is written entirely with `\uXXXX` escapes.
There is no space after `:` or `,`, the same layout `jq -c` prints, so a
`grep` pattern such as `"agent":"codex-cli"` matches the file and jq output
alike. [searching.md](searching.md) has recipes.

## timeline.jsonl

`timeline.jsonl` fields, in order:

| Field | Meaning |
| --- | --- |
| `timestamp_utc` | ISO 8601 UTC with milliseconds, `2026-10-03T16:55:31.123Z`. Times recorded without a zone are taken as UTC. Epoch numbers above 10^11 are read as milliseconds, smaller ones as seconds. Empty when the record has none. |
| `host` | From `collection.json`, or `--host`. Empty for loose input without `--host`. |
| `user` | From the manifest, inferred from the path, or `--user`. |
| `agent` | Catalog agent name of the parser that produced the row. |
| `session_id` | The agent's own session or thread identifier. |
| `project_path` | Working directory recorded for the turn. |
| `git_branch` | Branch recorded for the turn, where the agent logs one. |
| `turn_type` | `user`, `assistant`, `tool_use`, `tool_result`, `system`, or `thinking` with `--include-thinking`. |
| `model` | Model that produced the turn, where recorded. |
| `tool_name` | For `tool_use` rows: the tool. Codex shell calls are `shell`. |
| `tool_use_id` | Links a `tool_use` row to its `tool_result`. |
| `text` | The event's full text, with leading and trailing whitespace removed and inner line breaks and indentation kept: the prompt, the response, the tool output, or for a tool call its most identifying argument (the Bash command, the edited file, the search pattern, the fetched URL), else the arguments as JSON. |
| `source_file` | Path of the record on the source host, as in the manifest. In loose mode it is the path relative to the input root with a leading `/`, or relative to the home when the input root is the home or an agent directory. |
| `source_line` | Integer. Where the record is in that file, so the full record can be read. For line-oriented files (JSONL, Markdown, text) the 1-based line number. For SQLite stores it is the record's `rowid` (Tabby events: the event id), and for JSON documents an array index or `1`. Each parser's module docstring says which. `0` when no position applies. |

### Row order and system rows

Rows are sorted by timestamp, then by source file and line. Rows without a
timestamp sort last. Injected context is typed `system`, not `user`, so
the `user` rows are what the person typed. In Claude Code that is
`isMeta` records, task notifications, slash commands and their output, a
subagent's task, compaction summaries and messages from other agents. In
Codex it is `developer` messages and user-role blocks whose content kind
names harness context rather than `user.*` input, or, in older rollouts
without content kinds, a block that is wholly a harness wrapper such as
`<environment_context>`. These `system` rows start with a lowercase label
naming the source, such as `subagent task:`, `task notification:`,
`slash command:`, `command output:` or `context: <kind>:`, followed by the
full text. A line a parser cannot decode, such as a
transcript's last line cut off mid-write, is reported as a `system` row,
and the rest of the file is still read.

Antigravity's permission state is also typed `system`. A grant recorded on
a step is `permission grant: action=<action> target=<target>
allow=<true|false> scope=<scope>`, or for a file access entry
`permission grant: path=<path> is_directory=<true|false>
allow=<true|false> scope=<scope>`; it follows the step's own rows and
carries the step's `tool_name` and `tool_use_id`, so it joins to the call
it governed. A standing grant from a settings file is
`permission setting: <key>=<value> (from <file>, file mtime)`: its
`timestamp_utc` is the file's modification time, not the time of the
grant, which no file records, and its `session_id` is empty, so it
appears in `timeline.jsonl` but in no `sessions.jsonl` record. The
[`antigravity` row of the parser table](parsers.md#parser-table) lists the
files.

Permission state and the model in use are `system` rows too. The
`claude-code` parser (and `claude-desktop` for the transcripts it reads
with the same reader) writes `permission mode: <mode>` at a session's
first permission mode and `permission mode: <old> -> <new>` on each
change, and `model: <id>` at the first assistant reply and
`model: <old> -> <new>` on each change, with ` requested=<id>` when the
model asked for differs from the one that answered; the `model` column of
a model row is the new model. Each subagent transcript tracks its own.
Standing permission settings are one row per entry, `permission setting:
<key>=<value> (from <file>, file mtime)`: `permissions.allow`, `deny`,
`ask`, `additionalDirectories`, `defaultMode` and
`disableBypassPermissionsMode` from `.claude/settings.json` and
`.claude/settings.local.json` (the user's, or a project's with
`project_path` the project), and `allowedTools`, `hasTrustDialogAccepted`
and `hasClaudeMdExternalIncludesApproved` per project from `.claude.json`
(with `project_path` the project key). Their `timestamp_utc` is the
file's modification time (the manifest `mtime` when there is a
manifest), not the time the entry was added, and their `session_id` is
empty. A Claude Desktop session record adds ` permission_mode=<mode>
effort=<effort>` to its row and one `permission grant: <key> <entry>` or
`permission grant: <key>=<value>` row per session grant, timestamped at
the record's `lastActivityAt` (else `createdAt`), which the text names as
`(as of <field>)`. A per-call decision stays `permission decision:`
(Claude Code) or `permission request:`, `permission response:`,
`permission auto-approved:` and `permission auto-denied:` (the Claude
Desktop audit log).

The `codex-cli` and `open-interpreter` parsers (one shared reader) write
`model: <id>` at the first `turn_context` record of a rollout that names
a model and `model: <old> -> <new>` at each later one whose model
differs, and one composite `permission mode: approval=<approval_policy>
sandbox=<sandbox_policy> profile=<permission_profile> network=<network>`
row at the first `turn_context` with any of those four fields and
`permission mode: <old> -> <new>` whenever the composite changes. A
missing field is `-` and an object field is compact JSON, so a value
reads `sandbox={"type":"workspace-write"}`. Both rows take the
`turn_context` line's timestamp and precede that turn's rows, and the
`model` column of both is the turn's model. Codex records no per-call
approval in its rollouts, so these parsers write no `permission
decision:` row.

The `gemini-cli` and `qwen-code` parsers write `model: <id>` at a
session's first record that names a model and `model: <old> -> <new>`
on each change, tracked per session id: for Gemini CLI from each gemini
message's `model`, for Qwen Code from the `session_model` record, which
reads `model: <id> auth=<authType>`, and from each assistant record's
`model`; a Qwen Code `logs.json` `model_switch` entry reads
`model: <from> -> <to> reason=<reason>`. A tool call whose status is
`cancelled` or `awaiting_approval` keeps its `[<status>]` prefix on the
`tool_result` row and is followed by `permission decision: <status>`
with the call's `tool_name` and `tool_use_id` (after the `tool_use` row
when there is no result). Each folder in `.gemini/trustedFolders.json`
or `.qwen/trustedFolders.json` is one row
`permission setting: trustedFolders.<path>=<value> (from <file>, file mtime)`,
where `<value>` is the recorded trust level (`TRUST_FOLDER`,
`TRUST_PARENT` or `DO_NOT_TRUST`), with `project_path` the folder, the
file's modification time and an empty `session_id`.

The `antigravity` parser writes `model: <id>` before the rows of a
conversation's first step that the `gen_metadata` table names a model for
(`chat_model.response_model`, else `model_display_name`) and
`model: <old> -> <new>` before the rows of each later step whose model
differs, at the step's `created_at`, with the new model in the `model`
column; the format has no switch record, so a change is seen only as a
different model on a later step. A `run_command` or `mcp_tool` call the
user rejected is followed, after its `tool_result` row (which keeps its
`[rejected by user]` marker), by `permission decision: user_rejected` with
the call's `tool_name`, `tool_use_id` and result time, and a
`run_command` result that ran in Antigravity's sandbox ends with
` sandbox=true`.

The `opencode` and `kilo-code` parsers write `model: <modelID>
provider=<providerID>` before the first message of a session that names a
model and `model: <old> -> <new> provider=<providerID>` before each later
message, or V2 `model-switched` record, whose model differs; the `model`
column of the row is the new `<providerID>/<modelID>`. They write
`permission mode: agent=<name>` and `permission mode: agent=<old> ->
agent=<new>` for the message's `agent` and for a V2 `agent-switched`
record, because an OpenCode or Kilo Code agent (`build`, `plan`, a custom
one) is a mode with its own permission ruleset. Both rows take the
message's timestamp and `source_line` and precede its other rows. The
`crush` parser writes `model: <model> provider=<provider>` and `model:
<old> -> <new> provider=<provider>` the same way, from each message's
`model` and `provider`; it writes no permission rows, because Crush
records no permission state the research names.

The pi session reader (the `pi` parser, the little-coder sessions in
pi's directory, which stay agent `pi`, and Letta's local-backend
`messages.jsonl`) and the `openclaw` parser write `model: <id>
provider=<provider>` at the first entry of a session that names a model
and `model: <old> -> <new> provider=<provider>` on each change, with
` requested=<model>` when an assistant message's `responseModel` (the
model the provider reported) differs from its `model` (the one asked
for); a `model_change` entry is one of those entries, and one that
names the model already in force, being the user's own switch, still
gets the plain `model: <id> provider=<provider>` row; for `openclaw`
the `session_windows` `model` and `model_provider` start the session at
its start time. The `letta` parser adds the same row after the first
`.letta/sessions.jsonl` line of each CLI session and a change row when a
later line of the session names another model. The `pi` parser reads
`.pi/agent/trust.json`, the project trust decisions pi and little-coder
share, as one `permission setting: <path>=<true|false> (from
.pi/agent/trust.json, file mtime)` row per project, with `project_path`
the project, the file's modification time and an empty `session_id`.

The `cline`, `continue` and `pearai` parsers write the same `model:`
rows, with the `model` column the new model. Cline's SDK sessions write
`model: <id> provider=<provider>` after the session start (or
`sessions.db` index) row, from the manifest's `model` and `provider`, and
`model: <old> -> <new> provider=<provider>` before a message whose
`modelInfo.id` differs; its legacy tasks write `model: <model_id>
model_provider_id=<id> mode=<mode>` and `model: <old> -> <new> ...` from
the `model_usage` entries of `task_metadata.json` at each entry's time,
and `permission mode: <mode>` and `permission mode: <old> -> <new>` from
the same entries' `mode`. Continue writes `model: <chatModelTitle>` after
the session row and `model: <old> -> <new>` before a history item whose
`promptLogs[].modelTitle` differs; PearAI's chat sessions write
`model: <id>` and `model: <old> -> <new>` from each item's
`promptLogs[].completionOptions.model`. These rows inherit the session's
time like every other row of a Continue or PearAI session. Continue
also writes per-call decisions with the call's `tool_use_id` and
`tool_name`: `permission decision: accepted=<accepted>` after each
`dev_data` `toolUsage.jsonl` record's `tool_result` row, at the record's
time and with an empty `session_id` (the record names none), and
`permission decision: canceled` after a session tool call whose
`toolCallStates[]` status is `canceled`, at the session time. `roo-code`,
`aider`, `shellgpt` and `tabby` record no model and write no such row.

The `vscode`, `cody` and `twinny` parsers write the same `model: <id>`
and `model: <old> -> <new>` rows, from the request `modelId` (VS Code),
the assistant message `model` (Cody, per chat) and `meta.model` (Twinny,
per conversation), before the rows of the request or message that
names the model. VS Code also writes `permission mode: <mode>` and
`permission mode: <old> -> <new>` from the request's chat mode (`ask`,
`agent`, `edit`, `custom`). Per-call decisions are `permission
decision:` rows. In VS Code, a tool call's confirmation follows its
`tool_result` row with the call's `tool_use_id`: `permission decision:
confirmed=true` or `confirmed=false` (before VS Code 1.104), else
`confirmed=<kind>(<number>)`, one of `Denied(0)`,
`ConfirmationNotNeeded(1)`, `Setting(2)`, `LmServicePerTool(3)`,
`UserAction(4)` and `Skipped(5)`, followed by that record's `source`,
`id`, `scope`, `selectedButton` or `selectedButtonKind`, the tool's
origin as `tool_source=<type>` and any `reason` last. A question put to
the user in the chat is `permission decision: confirmation
isUsed=<true|false> buttons=<list> title=<title>` with its message on
the next line, and the request that answering it sent is followed by
`permission decision: confirmation=<button label>`. Cody's confirmation
steps are `permission decision: confirmation state=<state>
title=<title>` with the step's description and content on the next
lines. Twinny's tool steps saved while waiting for the user's Run or
Skip, or skipped, are `permission decision: waiting` and `permission
decision: skipped`, each with ` approval=<command|change>` when the
step records what was asked, after the step's `tool_result` row with
its `tool_use_id`.

The `zed`, `goose`, `kiro`, `hermes` and `ollama` parsers write model rows
in the same form. `zed` writes `model: <model> provider=<provider>` once
per thread, after the thread-start row, since a thread blob keeps one
model. `goose` writes `model: <model_name> provider=<provider_name>` after
each session's start row and `model: <old> -> <new> provider=<provider>`
before a message whose recorded model differs, with
` requested=<requestedModel>` when the resolved model is another id.
`kiro` writes `model: <id>` and `model: <old> -> <new>` before the rows of
the history entry whose `request_metadata.model_id` names it, ending
` source=model_info` or ` source=model` when the entry had none and the
conversation-level field stood in. `hermes` writes them from the
`session_model_usage` table at each model's first use, with
` provider=<billing_provider>`, or one `model: <id>` from the session row
at its start. `ollama` writes them before the assistant message whose
`model_name` names the model. `goose` also writes
`permission mode: <goose_mode>` after each session's start row. `zed`
writes one `permission setting: <key>=<value> (thread blob, as of
updated_at)` row per grant the user gave for the rest of a thread
(`profile`, each `sandbox_grants.write_paths` and `network_hosts` entry,
and each `sandbox_grants` escape flag that is `true`): unlike the
settings-file rows these live in the thread blob, so their `session_id` is
the thread id and their `timestamp_utc` is the thread's `updated_at`, the
blob's last write rather than the time of the grant.

OpenHands, Agent Zero, nanobot and Muse Code write the same kinds of row.
`openhands` writes `model: <id>` after each conversation's header row, at
the header's time, from `agent.llm.model` in `base_state.json`; a
rejected call's `tool_result` is followed by `permission decision:
rejected rejection_source=<source> <reason>` with the call's `tool_name`
and `tool_use_id`, and an action's `tool_use` text ends with
` security_risk=<value>` when the event has one. `agent-zero` writes
`model: <id>` before an agent's first reply and `model: <old> -> <new>`
on a change, tracked per chat and agent number, with ` agent=<n>` for a
subordinate agent. `nanobot` writes `model: <preset> (preset)` after
the session start row: the value is a model preset of nanobot's
configuration, not a model id. `muse-code` writes, per session log,
`permission mode: approval=<approval> reviewer=<reviewer>
profile=<profile id>` followed by ` cause=<cause>` and
` format=<format>` from the log's permission frame,
`permission mode: security_mode=<value>`, and `permission mode: <old> ->
<new>` on a change of either; `model: <id> provider=<provider>` at the
first model a log names and `model: <old> -> <new>` on a change or a
`/model` command; `permission decision: <outcome>
kind=automated_review_completed risk_level=<r> user_authorization=<u>
status=<s> <rationale>` for the automated reviewer's verdict and
`permission decision: <decision> source=<source kind> policy_result=<p>
amendment=<a>` for the decision applied (`-` for a missing value), both
at the record's place in the log, before the call's `tool_result`, and
carrying the call's `tool_name` and `tool_use_id`; and one
`permission setting: projects.<path>.decision=<decision> (from
.config/muse/trust.json, file mtime)` row per trusted project, with
`project_path` the project, the file's modification time and an empty
`session_id`.

## sessions.jsonl

`sessions.jsonl` has one record per `host`, `user`, `agent` and
`session_id`, built from the timeline records that have a session id. Its
fields, in order: `host`, `user`, `agent`, `session_id`, `project_path`
(the first non-empty one), `first_timestamp_utc`, `last_timestamp_utc`,
`models` (an array of strings, in order of first use, empty when none was
recorded), `user_turns` and `assistant_turns` (integers, timeline records
of those types), `tool_calls` (integer, `tool_use` records), and
`source_file` (the file that contributed the most records). It is sorted by
first timestamp, so sessions with no timestamp come first.

## Compatibility

The two JSONL layouts are a compatibility contract with the analysts and
tooling that consume them. A future version may append new fields after the
existing ones, but existing fields keep their names, order, type and
meaning.
