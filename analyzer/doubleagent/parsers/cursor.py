"""Cursor IDE agent conversations (issue 51).

Closed source. Validated against real installs of the Cursor IDE on macOS
(3.24.18, 3.25.9 and 3.26.13), Linux (3.25.9) and Windows (3.26.13),
October 2026, one step per listing, and the 3.25.9 and 3.26.13 bundles (`workbench.glass.main.js`) for the run modes;
see `research/cursor.md`, whose Parsing part this module follows (Record
schema, Joins and timestamps, Parser plan). The standalone Cursor Agent
CLI's `~/.cursor/chats` and `acp-sessions` stores are not read: no real
install has shown them. The IDE's paths are under `<ide>`, which is
`Library/Application Support/Cursor`, `.config/Cursor` or
`AppData/Roaming/Cursor`. Cursor's names: a composer is one conversation
(`composerId`), a bubble one message, reasoning block or tool call in it
(`bubbleId`), `toolFormer` a tool call's record, `yolo` auto-run.

* `<ide>/User/globalStorage/state.vscdb`, the primary store, opened through
  `sqlite_util` with its `-wal`:
  - `cursorDiskKV` `composerData:<composerId>` (`status`, `name`,
    `createdAt`, `lastUpdatedAt`, `isArchived`, `workspaceIdentifier.uri
    .fsPath`, `trackedGitRepos[].repoPath` and `.branches`,
    `fullConversationHeadersOnly[]`). A composer with `status` `none` and
    an empty header list in both layouts is a draft and yields only its
    `composerDraft:<composerId>` row (`text`): `unsent draft: <text>` at the
    composer's `createdAt`. The header list is `fullConversationHeadersOnly`
    (3.25.9) when not empty, else every `composerConvHeaders:<composerId>:
    <NNNNNN>` chunk (3.26.13, a JSON array) in suffix order, concatenated;
    each entry has `bubbleId` (with its `/s:<n>` or `/t:call-...` LF
    `fc_...` suffix), `type` and `createdAt`, and names the row
    `bubbleId:<composerId>:<bubbleId>`. A conversation's rows:
    `session name: <name>` at `createdAt`; then per entry, in list order,
    the bubble's rows; an entry with no bubble row is `parser: missing
    bubble <bubbleId>` at the entry's `createdAt`.
  - User bubble (`type` 1: `text`, `createdAt`, `modelInfo.modelName`):
    a `model: <id>` row the first time a user bubble names a model and
    `model: <old> -> <new>` when a later one names another, then the `user`
    row at `createdAt`. A user bubble without `modelInfo` (the turns the
    app injects) gives no `model:` row. Every row of the turn carries that model in
    `model`; assistant records name none. `composerData.modelConfig` is
    the current selection with no history and is not read.
  - Assistant sub-bubble (`type` 2, no `toolFormerData`: `thinking.text`,
    `text`, `createdAt`, `startedAtMs`): a `thinking` row with
    `opts.include_thinking`, then an `assistant` row when `text` is not
    empty, at `createdAt`, else `startedAtMs`, else the entry's
    `createdAt`.
  - Tool bubble (`toolFormerData`: `name`, `params`, `rawArgs`, `result`,
    `toolCallId`, `additionalData.status`, `.startedAtMs`, `.blockReason`,
    `.reviewData.selectedOption`, `.approvalType`, `.allowlistOptions[]
    {id, commandName}`, `.appliedAllowlistOptionIds`; the bubble's
    `startedAtMs` and `completedAtMs`; `.reviewData.status` and
    `toolFormerData.status`): a `tool_use` row, `params`, else `rawArgs`,
    at `startedAtMs`; when `reviewData` is present and answered
    (`reviewData.status` `Done` and `toolFormerData.status` not
    `loading`) a `system` row `permission decision: <selectedOption>
    outcome=<status> approval=<approvalType> reason=<blockReason>`, with `
    allowlisted=<the commandName of each applied option, else its id>`
    when `appliedAllowlistOptionIds` is not empty, whatever
    `selectedOption` says (the macOS 3.25.9 Agents window's "Always run"
    writes `allowlistCommands`, the Linux 3.25.9 editor window's "add ...
    to the allow list" writes `run`) (`-` for a missing value); when
    `reviewData` is present but unanswered (any other `reviewData.status`,
    `Requested` seen on 3.25.9 Linux, or `toolFormerData.status`
    `loading`), the prompt was still open when the store was copied and
    `selectedOption` holds a preset (`rejectAndTellWhatToDoDifferently`),
    so the row is `permission prompt pending: <tool_name>
    reason=<blockReason> options=<allowlistOptions ids>` instead; then a
    `tool_result` row, `result`, prefixed `[rejected] ` when
    `additionalData.status` is `rejected` and the prompt was answered, at
    `completedAtMs`, and none for a pending call with no `result`. A
    call in flight when the user stopped the turn (Windows 3.26.13) has
    `reviewData.status` the string `None`, `additionalData.status`
    `rejected` and the preset `selectedOption`: its row is `permission
    decision: stopped by the user (reviewData.status None,
    additionalData.status rejected)`, and its result keeps the
    `[rejected] ` prefix; the calls queued after it have
    `toolFormerData.status` `cancelled` and an empty `additionalData`,
    and yield their `tool_use` row and no permission row.
    `tool_name` is `toolFormerData.name` and `tool_use_id` `toolCallId` on
    all three. A call that ran under auto-run or a standing allowlist
    entry has no `reviewData` and gets no permission row; the run mode and
    the list in force are standing rows. An MCP tool call is an ordinary
    tool bubble (Windows 3.26.13): `toolFormerData.name`
    `mcp-<server>-<tool>` (`tool` 19) and the manifest fetch
    `get_mcp_tools` (`tool` 63), with `params` and `rawArgs` as for any
    tool and `additionalData` holding only `status`. A prompt for an MCP
    call answered Run under Allowlist leaves no `reviewData`,
    `selectedOption` or `blockReason`, so no per-call decision row exists
    for MCP calls; the switches in force (`yoloMcpToolsDisabled`,
    `mcpAuthBlocking`) are standing rows. `toolFormerData.toolCallBinary`
    (a serialized copy of the call) and `modelCallId` are not read.
  - `composerHeaders` table (`composerId`, `createdAt`, `lastUpdatedAt`,
    `isArchived`, and `value`: `name`, `isArchived`,
    `workspaceIdentifier.uri.fsPath`, `trackedGitRepos[]`,
    `agentLocation.type`, `agentLocationHistory[]`). `project_path` is the
    header's `workspaceIdentifier.uri.fsPath`, else the composer's, else
    the first `trackedGitRepos[].repoPath`; `git_branch` the first entry
    of that repository's `branches`. A conversation whose header is
    archived (`isArchived` 1 or `value.isArchived` true; the composer's own
    `isArchived` stays null) gets `conversation archived` at the header's
    `lastUpdatedAt`. A header with no `composerData` that is not a draft
    (it has an `agentLocationHistory` entry or is archived) is a deleted
    conversation: `conversation deleted (header kept; time is the header's
    lastUpdatedAt)` at `lastUpdatedAt`, followed by ` (isArchived is set by
    the delete)` when the header is archived, since the delete sets the
    flag on a conversation that was never archived (Windows 3.26.13); such
    a header gets no `conversation archived` row. An `agentLocation.type`
    other than `local` gives `session origin: remote <type>`
    (bundle-derived: only `local` has been seen). `agentLocation` and
    `agentLocationHistory` are optional per conversation: on Windows
    3.26.13 one header had neither and a later one of the same install
    both.
  - `agentKv:blob:<sha256>` rows, read only for deleted conversations: a
    JSON blob (`role`, `content`) whose `content` contains the id of a
    deleted composer yields a `user` or `assistant` row from `content`
    (`system prompt: <content>` for `role` `system`, `<role> message:
    <content>` for another role), with an empty `timestamp_utc`, the
    composer's session and project, and `recovered` "yes", since nothing
    else in the store holds the event. Blobs of a conversation still
    present are not read: their user text is the whole prompt with its
    context, which repeats the bubbles in a form deduplication cannot
    match. Protobuf blobs yield nothing. The plan calls these blobs
    secondary; `secondary()` decides per file and the database is the
    primary store, so the parser sets `recovered` on these rows itself.
  - Standing settings, at the file's modification time with an empty
    `session_id`, from `ItemTable`
    `src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl
    .persistentStorage.applicationUser` and
    `cursor/sandboxAutoRunSettingEnabled`: `permission setting:
    <list>=<entry> (from state.vscdb composerState, file mtime, written
    late by the app)` per entry
    of `composerState.yoloCommandAllowlist`, `yoloCommandDenylist`,
    `smartAllowlistDenylist`, `webFetchDomainAllowlist` and
    `autoApprovedModeTransitions`; `permission setting: run mode <id>=<mode>
    autoRun=<b> smartModeAutoRun=<b> fullAutoRun=<b> sandbox=<b> (from ...)`
    per `composerState.modes4` entry, the mode derived from the flags and
    the sandbox key (`RUN_MODES`); `permission setting: <switch>=<value>
    (from ...)` per boolean switch in `SWITCHES`; and `model last used:
    <id> (from state.vscdb aiSettings.modelLastUsedAt, written late by the
    app)` per entry of `aiSettings.modelLastUsedAt`, at its own time. The
    app flushes this blob late (3.25.9 Linux: a list entry added from a
    prompt was not written by the next quit, and a switched model's entry
    appeared only at its next use), so neither time is the event's.
  - Source-host and remote-host rows from `ItemTable`, with an empty
    `session_id` (3.25.9 Linux, 2026-10-20): the editor's own GitHub
    sign-in writes `github-<login>` (a JSON list of `{id, name,
    allowed}`, the extensions allowed to use the account) and
    `github-<login>-usages` (`[{extensionId, extensionName, lastUsed,
    scopes[]}]`), which give `source host: github account <login>
    scopes=<the usages' scopes, deduplicated, else -> (from state.vscdb
    key github-<login>)` at the latest `lastUsed` (epoch ms), else the
    file's modification time; a `github-` key whose value is not a list
    is another extension's and is skipped. Cursor's own GitHub app
    connection names no account locally. `remoteAgentHost.enrolled.
    <account>` true gives `remote agent host enrolled: <displayName>
    (from state.vscdb remoteAgentHost.enrolled.<account>, file mtime)`,
    `<displayName>` from `remoteAgentHost.displayName.<account>` (JSON or
    plain text), else `-`; the row text ends `file mtime; on by default, a
    paired device leaves no local record)`, since the enrolment is on
    from sign-in and pairing a phone wrote nothing locally (Windows
    3.26.13). Only the `github-` and `remoteAgentHost.` keys
    are selected: the `secret://` values beside them (the GitHub token,
    `remoteAgentHost.computerKey.<account>`) are never read. Nothing
    marks a local session synced: a local session reads `synced` `no`.
  - Cloud agents (Windows 3.26.13, 2026-10-21). A cloud agent (`bc-<uuid>`,
    "background composer") runs on Cursor's servers and has no composer
    rows locally. Each element of an `ItemTable`
    `cloudAgentRepository.agents.<account>` list (selected by the prefix,
    so the account id may be URL-encoded; a value that is not a JSON list
    is skipped) with `bcId`, `name`, `repoUrl` (`github.com/<owner>/
    <repo>`), `status`, `workflowStatus`, `isArchived`, `isKilled`,
    `hasStartedVm`, `createdAt`, `rowUpdatedAtMs`, `modelDetails.modelName`
    and `requestedModel.modelId` gives, with `session_id` the `bcId`,
    `project_path` the `repoUrl` and `model` the model on every row:
    `session origin: remote cursor cloud agent` at `createdAt`, unless the
    `conversation-search.db` beside the file has a `cloud-cache` row for
    the agent, whose parse yields it; `session synced: cursor cloud agent
    <bcId> (vendor copy; from state.vscdb cloudAgentRepository.agents)`
    at `createdAt`, since the vendor holds the conversation, so
    `records_sync` is set; `model: <modelName>` (with `
    requested=<modelId>` when the two differ) at `createdAt`; `source host:
    github.com <owner>/<repo> (cloud agent)` at `createdAt` when the host
    of `repoUrl` (parsed, with or without a scheme) is `github.com`; and
    `cloud agent: <name> repo=<repoUrl>
    status=<status> workflowStatus=<workflowStatus> archived=<isArchived>
    killed=<isKilled> vmStarted=<hasStartedVm> (from state.vscdb
    cloudAgentRepository.agents, rowUpdatedAtMs)` at `rowUpdatedAtMs`.
    An agent the Agents window started as a new project
    (`startedAsNewProject`, with `branchName`) has a `repoUrl` in Cursor
    Origin, `origin.cursor.com/git/<namespace>/tmp-<hex>`, and no
    `source host:` row. `cloudAgentRepository.mcpAuthResolution`
    (`agentId`, `toolCallId`, `userDecision`; also `authId`, `nonce`,
    `queryId` and `version`, not read), the user's answer to a cloud
    agent's request to authorise an MCP server, gives `permission
    decision: <userDecision> mcp auth for cloud agent <agentId>
    tool_call=<toolCallId> (from state.vscdb
    cloudAgentRepository.mcpAuthResolution, file mtime)` in the agent's
    session with `tool_use_id` the `toolCallId`; the grant itself is held
    server-side.
    Each element of `cloudEnvironmentTemplate.githubRepos` (`url`, `name`,
    `type`), the repositories the account may reach through Origin,
    gives `source host repository: <url, else name> type=<type> (from
    state.vscdb cloudEnvironmentTemplate.githubRepos, file mtime)` with
    no session. `cursorDiskKV` `bcCachedDetails:<bcId>`, written when a
    cloud conversation is reopened, is protobuf with no schema yet and is
    not read; the `secret://` connection tokens beside the list are never
    read.
  - MCP servers and plugins (Windows 3.26.13), from `ItemTable`, with an
    empty `session_id`. A key `mcpOAuth.global.<b64>` or
    `mcpOAuth.secret.<b64>` names URL-safe base64 (unpadded) of `[<scope>]
    <field>`, the scope `plugin-<plugin>-<server>::mcpScope:profile:<b64
    profile>` or `oauth-attempt:<uuid>`. Per server scope with the global
    field `mcp_server_url`: `mcp server: <scope before ::> url=<url> (from
    state.vscdb mcpOAuth.global, mcp_oauth_updated_at_ms)` at the scope's
    `mcp_oauth_updated_at_ms` (`file mtime` in the text and the file's
    time when it is absent), ending ` tokens=stored (ciphertext, not
    read)` when a `mcpOAuth.secret.` key of the scope names `mcp_tokens`.
    Only the key names of `mcpOAuth.secret.` rows are selected: their
    values (`mcp_tokens`, `mcp_code_verifier`,
    `mcp_oauth_attempt_client_secret`, `mcp_client_information`) are
    safeStorage ciphertext and credentials. The `oauth-attempt:` scopes,
    the migration flags and `mcpOAuth.extensionMigrationComplete` yield
    nothing. Each entry (`id`, `sources[]`) of a
    `cursor.plugins.installedIds.<team>|<scope>` list gives `plugin
    installed: id=<id> sources=<sources> scope=<scope> (from state.vscdb
    cursor.plugins.installedIds, file mtime)`, the scope `no-workspace` or
    a folder's `file://` URI, whose path (a Windows drive URI in the
    `c:\\...` form `fsPath` writes) is the row's `project_path`.
* `.cursor/projects/<sanitized cwd>/agent-transcripts/<composerId>/
  <composerId>.jsonl`, the agent worker's copy, a secondary source
  (`secondary()`): `{role, message{content[{type text|tool_use, text,
  name, input}]}}` and `{type: turn_ended}` lines. A user text block is
  `<timestamp>Thursday, Oct 1, 2026, 6:00 AM (UTC-4)</timestamp>` LF
  `<user_query>Q</user_query>`; the row's text is Q and its time the tag
  converted to UTC with its offset, at minute precision. A block whose
  wrapper does not parse keeps its whole text and an empty time. Assistant
  text blocks are `assistant` rows and tool blocks `tool_use` rows
  (`tool_name` the transcript's CamelCase name, `text` the compact JSON of
  `input`), with an empty time, so they pair on text alone; the
  transcript's tool names differ from `toolFormerData.name` (an MCP
  call is `GetDynamicTools` or `CallDynamicTool` there) and are not
  mapped, so a live conversation's transcript `tool_use` rows do not pair
  with the bubbles' and are kept beside them. `turn_ended` lines and lines
  of any other shape yield nothing. `session_id` is the file name and
  `project_path` the composer's in the home's `state.vscdb`.
  `secondary_tolerance()` is 60 seconds: the tag has minute precision and
  the bubble's `createdAt` milliseconds.
* `.cursor/ai-tracking/ai-code-tracking.db` (not secondary: it repeats no
  event), each table read when present: `ai_code_hashes` (`fileName`,
  `source`, `model`, `requestId`, `conversationId`, `timestamp`) as `ai
  code: <fileName> source=<source> model=<model> request=<requestId>` at
  `timestamp`; `conversation_summaries` (`conversationId`, `title`,
  `tldr`, `model`, `updatedAt`) as `conversation summary: <title>: <tldr>`
  at `updatedAt`; `ai_deleted_files` (`gitPath`, `composerId`,
  `conversationId`, `model`, `deletedAt`) as `file deleted by agent:
  <gitPath> model=<model>` at `deletedAt`; `scored_commits`
  (`commitHash`, `branchName`, `linesAdded`, `linesDeleted`, `scoredAt`)
  as `scored commit: <commitHash> branch=<branchName> +<linesAdded>
  -<linesDeleted>` at `scoredAt`, with no session. Only `ai_code_hashes`
  has been seen populated; the other three are fixture only.
* `<ide>/User/globalStorage/conversation-search.db` (not secondary):
  `conversations` (`fts_rowid`, `id`, `title`, `source`, `is_archived`,
  `updated_at`) and the FTS5 shadow table `conversation_fts_content`
  (`id`, `c0` the title, `c1` the body), read as a plain table joined on
  `fts_rowid` = `id`, never through the fts5 virtual table. Per row, at
  `updated_at`: `session origin: remote cursor cloud agent` when `source`
  is `cloud-cache` (a cloud agent's cached conversation, `id` its
  `bc-<uuid>`); `conversation index: <title> source=<source>
  archived=<is_archived>` when it has a title; and `cached conversation
  text (conversation-search.db, source=<source>): <c1>` when the body is
  not empty. The body runs the prompt and the reply together with no turn
  boundary, so it is one `system` row, never `user` or `assistant`, with
  `source=local` for a local row. Some local rows have no body: on
  Windows 3.26.13 conversations with text had bodies of 252 and 806
  characters and the deleted and short ones none, as on macOS (42
  characters); the `cloud-cache` rows held the cloud conversations'
  text. A cloud agent's project and model come from the agent list in
  the home's `state.vscdb`.
* `<ide>/User/globalStorage/mcp-oauth-attempts/<uuid>.json` (Windows
  3.26.13), the dynamic client registration of an MCP OAuth attempt, one
  file per server at a time, rewritten when the server reconnects
  (`serverUrl`, `clientInformation.client_id`, `owner.workspaceId`,
  `createdAtMs`; plaintext, no secret): `mcp oauth attempt:
  server=<serverUrl> client_id=<client_id> workspace=<workspaceId> (from
  mcp-oauth-attempts/<file>)` at `createdAtMs`, else the file's
  modification time with `, file mtime` in the parenthesis; a file that
  is not a JSON object is one `parser:` row.
* `.cursor/cli-config.json` (`approvalMode`, `permissions.allow[]`,
  `permissions.deny[]`, `sandbox.mode`) and `.cursor/permissions.json` in
  the home or a project (`approvalMode`, `allowlists.mcp[]`,
  `allowlists.terminal[]`, and top-level `allowInstructions[]` and
  `blockInstructions[]`; bundle-derived, fixture only): `permission
  setting: <key>=<value> (from <path>, file mtime)` per value or entry.

The project path, the session and the model of an ai-tracking,
conversation-search or transcript row come from the home's `state.vscdb`
when it is there (`composerHeaders` and `composerData` by composer id).
Bad lines of the transcript are `error_rows` rows. A `cursorDiskKV`,
`composerHeaders` or `ItemTable` value that should be JSON and is not is
an error entry `unparseable record <rowid> (<key>: <reason>)` with the value
as stored, reported per composer with its session and project. A database
that is not SQLite is one `parser: not a SQLite database` row, a SQLite
error one `parser: SQLite error: <message>` row, and a JSON settings file
that does not decode one `parser:` row.
"""

from __future__ import annotations

import base64
import json
import re
import sqlite3
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from ..inputs import Artifact, error_reason
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import format_utc, to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    file_mtime,
    iter_jsonl,
    setting_value,
    text_of,
    track_change,
)

IDE = r"(?:Library/Application Support|\.config|AppData/Roaming)/Cursor"
IDE_PARENTS = ("Library/Application Support/Cursor", ".config/Cursor", "AppData/Roaming/Cursor")
STATE_RX = re.compile(r"^%s/User/globalStorage/state\.vscdb$" % IDE)
SEARCH_RX = re.compile(r"^%s/User/globalStorage/conversation-search\.db$" % IDE)
TRANSCRIPT_RX = re.compile(r"^\.cursor/projects/[^/]+/agent-transcripts/[^/]+/([^/]+)\.jsonl$")
TRACKING_RX = re.compile(r"^\.cursor/ai-tracking/ai-code-tracking\.db$")
CLI_CONFIG_RX = re.compile(r"^\.cursor/cli-config\.json$")
PERMISSIONS_RX = re.compile(r"^\.cursor/permissions\.json$")
ATTEMPT_RX = re.compile(r"^%s/User/globalStorage/mcp-oauth-attempts/([^/]+\.json)$" % IDE)

SETTINGS_KEY = (
    "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl"
    ".persistentStorage.applicationUser"
)
SANDBOX_KEY = "cursor/sandboxAutoRunSettingEnabled"
# The editor's enrolment of this machine as a remote agent host for an
# account; `secret://remoteAgentHost.computerKey.<account>` beside them is
# its credential and is never read.
ENROLLED_PREFIX = "remoteAgentHost.enrolled."
DISPLAY_PREFIX = "remoteAgentHost.displayName."
STANDING_LISTS = (
    "yoloCommandAllowlist",
    "yoloCommandDenylist",
    "smartAllowlistDenylist",
    "webFetchDomainAllowlist",
    "autoApprovedModeTransitions",
)
SWITCHES = (
    "yoloEnableRunEverything",
    "yoloDeleteFileDisabled",
    "yoloMcpToolsDisabled",
    "yoloOutsideWorkspaceDisabled",
    "autoApproveModeTransitions",
    "autoAcceptWebSearchTool",
    "autoApplyFilesOutsideContext",
    "doNotShowYoloModeWarningAgain",
    "doNotShowFullYoloModeWarningAgain",
    "useLegacyTerminalTool",
    "playwrightProtection",
    "mcpAuthBlocking",
)
# The settings blob is flushed late by the app, so its rows say so.
COMPOSER_SOURCE = "(from state.vscdb composerState, file mtime, written late by the app)"
MODEL_USED_SOURCE = "(from state.vscdb aiSettings.modelLastUsedAt, written late by the app)"
STOPPED_TEXT = (
    "permission decision: stopped by the user (reviewData.status None,"
    " additionalData.status rejected)"
)
DELETED_TEXT = "conversation deleted (header kept; time is the header's lastUpdatedAt)"
# The delete sets the header's `isArchived`, so a deleted header reads
# archived although the conversation never was (Windows 3.26.13).
ARCHIVED_BY_DELETE = " (isArchived is set by the delete)"
# The cloud agent list, one `ItemTable` key per Cursor account (the suffix
# is the account id, `auth0|user_<id>` or URL-encoded `auth0%7Cuser_<id>`),
# and the repositories a cloud agent may use (Windows 3.26.13).
CLOUD_AGENTS_PREFIX = "cloudAgentRepository.agents."
GITHUB_REPOS_KEY = "cloudEnvironmentTemplate.githubRepos"
CLOUD_ORIGIN = "session origin: remote cursor cloud agent"
CLOUD_SOURCE = "(from state.vscdb cloudAgentRepository.agents, rowUpdatedAtMs)"
CLOUD_SYNCED = (
    "session synced: cursor cloud agent %s (vendor copy; from state.vscdb"
    " cloudAgentRepository.agents)"
)
REPOS_SOURCE = "(from state.vscdb cloudEnvironmentTemplate.githubRepos, file mtime)"
CLOUD_CACHE = "cloud-cache"
# The cloud agent's request to authorise an MCP server, answered by the
# user (Windows 3.26.13).
MCP_AUTH_KEY = "cloudAgentRepository.mcpAuthResolution"
MCP_AUTH_SOURCE = "(from state.vscdb cloudAgentRepository.mcpAuthResolution, file mtime)"
# MCP OAuth state, one `ItemTable` key per scope and field: the suffix is
# URL-safe base64 of `[<scope>] <field>`. The `mcpOAuth.secret.` values are
# safeStorage ciphertext and are never read: only their key names are
# selected.
MCP_GLOBAL_PREFIX = "mcpOAuth.global."
MCP_SECRET_PREFIX = "mcpOAuth.secret."
MCP_KEY_RX = re.compile(r"^\[(.+)\] (\S+)$")
MCP_TOKENS = " tokens=stored (ciphertext, not read)"
PLUGINS_PREFIX = "cursor.plugins.installedIds."
PLUGINS_SOURCE = "(from state.vscdb cursor.plugins.installedIds, file mtime)"

# `<timestamp>Thursday, Oct 1, 2026, 6:00 AM (UTC-4)</timestamp>` LF
# `<user_query>Q</user_query>`, the worker's wrapper of a user text block.
WRAPPER_RX = re.compile(
    r"^<timestamp>([^<]*)</timestamp>\s*<user_query>(.*)</user_query>\s*$", re.DOTALL
)
TAG_RX = re.compile(
    r"^\s*[A-Za-z]+,\s+([A-Za-z]{3})[A-Za-z]*\.?\s+(\d{1,2}),\s+(\d{4}),\s+(\d{1,2}):(\d{2})"
    r"\s*([AaPp][Mm])\s*\(UTC(?:([+-])(\d{1,2})(?::?(\d{2}))?)?\)\s*$"
)
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")

TRACKING_TABLES = {
    "ai_code_hashes": (
        "fileName",
        "source",
        "model",
        "requestId",
        "conversationId",
        "timestamp",
    ),
    "conversation_summaries": ("conversationId", "title", "tldr", "model", "updatedAt"),
    "ai_deleted_files": ("gitPath", "composerId", "conversationId", "model", "deletedAt"),
    "scored_commits": ("commitHash", "branchName", "linesAdded", "linesDeleted", "scoredAt"),
}
SEARCH_COLUMNS = ("fts_rowid", "id", "title", "source", "is_archived", "updated_at")


def run_mode(mode: dict, sandbox: bool) -> str:
    """The UI label of a `modes4` entry's run mode, derived from its
    `autoRun`, `smartModeAutoRun` and `fullAutoRun` flags and the sandbox
    key (research/cursor.md, Run mode and standing lists); no run-mode
    string is stored."""
    if mode.get("fullAutoRun") is True:
        return "Run Everything"
    if mode.get("autoRun") is not True:
        return "Ask Every Time"
    label = "Auto-review" if mode.get("smartModeAutoRun") is True else "Allowlist"
    return label + " (with Sandbox)" if sandbox else label


def tag_time(tag: str) -> str:
    """The transcript's `<timestamp>` tag as a UTC timeline timestamp, or ""
    when it does not parse. The tag is local time to the minute with its
    UTC offset in parentheses."""
    m = TAG_RX.match(tag)
    if not m:
        return ""
    mon, day, year, hour, minute, ampm, sign, off_h, off_m = m.groups()
    if mon.lower() not in MONTHS:
        return ""
    hour_n = int(hour) % 12 + (12 if ampm.lower() == "pm" else 0)
    try:
        local = datetime(int(year), MONTHS.index(mon.lower()) + 1, int(day), hour_n, int(minute))
    except ValueError:
        return ""
    offset = timedelta(hours=int(off_h or 0), minutes=int(off_m or 0))
    if sign == "-":
        offset = -offset
    return format_utc((local - offset).replace(tzinfo=timezone.utc))


def unwrap_query(text: str) -> tuple[str, str]:
    """(query, timestamp) of a transcript user text block: the text inside
    `<user_query>` and the tag's time, or the whole text and "" when the
    wrapper or its tag does not parse."""
    m = WRAPPER_RX.match(text)
    if m:
        when = tag_time(m.group(1))
        if when:
            return m.group(2), when
    return text, ""


def _as_text(value) -> str:
    """A database value as text: bytes decoded as UTF-8 with replacement."""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", errors="replace")
    return "" if value is None else str(value)


def _object(value) -> dict:
    return value if isinstance(value, dict) else {}


def _decode(rowid: int, key: str, value, errors: list):
    """The JSON value of a row, or None, appending an error entry when it
    does not decode."""
    text = _as_text(value)
    try:
        return json.loads(text)
    except ValueError as e:
        errors.append((rowid, "unparseable record %d (%s: %s)" % (rowid, key, e), text))
        return None


def _prefixed(con: sqlite3.Connection, prefix: str) -> list[tuple[int, str, object]]:
    """The `cursorDiskKV` rows whose key starts with `prefix`, in key order,
    by a range over the key so the table's index is used."""
    end = prefix[:-1] + chr(ord(prefix[-1]) + 1)
    sql = "select rowid, key, value from cursorDiskKV where key >= ? and key < ? order by key"
    return [(int(r[0]), _as_text(r[1]), r[2]) for r in con.execute(sql, (prefix, end))]


def _one(con: sqlite3.Connection, key: str) -> tuple[int, object] | None:
    row = con.execute("select rowid, value from cursorDiskKV where key = ?", (key,)).fetchone()
    return (int(row[0]), row[1]) if row else None


def _select(con: sqlite3.Connection, table: str, wanted: tuple[str, ...]) -> list[dict]:
    """Every row of `table` as a dict of the `wanted` columns it has, plus
    `_rowid`, in rowid order."""
    have = {r[1] for r in con.execute("pragma table_info(%s)" % table)}
    cols = [c for c in wanted if c in have]
    if not cols:
        return []
    sql = 'select rowid as _rowid, %s from "%s" order by rowid' % (
        ", ".join('"%s"' % c for c in cols),
        table,
    )
    return [dict(r) for r in con.execute(sql)]


def _project(*docs: dict) -> tuple[str, str]:
    """(project_path, git_branch) of a composer from its header value and
    its `composerData`, in that order of preference."""
    path = ""
    for doc in docs:
        path = str(_object(_object(doc.get("workspaceIdentifier")).get("uri")).get("fsPath") or "")
        if path:
            break
    repos = [r for doc in docs for r in doc.get("trackedGitRepos") or [] if isinstance(r, dict)]
    if not path and repos:
        path = str(repos[0].get("repoPath") or "")
    for repo in repos:
        if str(repo.get("repoPath") or "") == path:
            branches = repo.get("branches") or []
            if branches and isinstance(branches[0], str):
                return path, branches[0]
            break
    return path, ""


class _Composer:
    """What the store holds about one composer: its `composerData` (or
    None), its header row and the header's `value`."""

    def __init__(self, cid: str) -> None:
        self.cid = cid
        self.data: dict | None = None
        self.data_rowid = 0
        self.header: dict | None = None
        self.head: dict = {}
        self.errors: list = []

    @property
    def project(self) -> tuple[str, str]:
        return _project(self.head, self.data or {})

    def created(self):
        for doc in (self.data or {}, self.head, self.header or {}):
            if doc.get("createdAt") not in (None, ""):
                return doc.get("createdAt")
        return None

    def header_updated(self):
        h = self.header or {}
        value = h.get("lastUpdatedAt")
        return value if value not in (None, "") else self.head.get("lastUpdatedAt")

    def archived(self) -> bool:
        h = self.header or {}
        return (
            bool(h.get("isArchived"))
            or self.head.get("isArchived") is True
            or ((self.data or {}).get("isArchived") is True)
        )


def _read_headers(con: sqlite3.Connection, composers: dict) -> None:
    """Attach each `composerHeaders` row and its decoded `value` to its
    composer; a value that does not decode is an error of that composer."""
    if "composerHeaders" not in table_names(con):
        return
    wanted = ("composerId", "createdAt", "lastUpdatedAt", "isArchived", "value")
    for rec in _select(con, "composerHeaders", wanted):
        cid = str(rec.get("composerId") or "")
        if not cid:
            continue
        c = composers.setdefault(cid, _Composer(cid))
        c.header = rec
        if rec.get("value") is not None:
            label = "composerHeaders " + cid
            c.head = _object(_decode(int(rec["_rowid"]), label, rec["value"], c.errors))


def read_composers(con: sqlite3.Connection) -> dict[str, _Composer]:
    """Every composer of the store by id, `composerData` rows in rowid
    order first, then the header-only ones."""
    composers: dict[str, _Composer] = {}
    if "cursorDiskKV" in table_names(con):
        rows = sorted(_prefixed(con, "composerData:"))
        for rowid, key, value in rows:
            cid = key[len("composerData:") :]
            c = composers.setdefault(cid, _Composer(cid))
            c.data = _object(_decode(rowid, key, value, c.errors))
            c.data_rowid = rowid
    _read_headers(con, composers)
    return composers


def read_cloud_agents(con: sqlite3.Connection, errors: list) -> list[tuple[int, dict]]:
    """(rowid, agent) of every element with a `bcId` of the `ItemTable`
    lists `cloudAgentRepository.agents.<account>`, in key order. The
    prefix alone selects them, so either spelling of the account id
    matches; a value that is not a JSON list is skipped, and one that
    starts as a list and does not decode is an error entry."""
    if "ItemTable" not in table_names(con):
        return []
    sql = "select rowid, key, value from ItemTable where substr(key, 1, ?) = ? order by key"
    found: list[tuple[int, dict]] = []
    for rowid, key, value in con.execute(sql, (len(CLOUD_AGENTS_PREFIX), CLOUD_AGENTS_PREFIX)):
        agents = None
        if _as_text(value).lstrip().startswith("["):
            agents = _decode(int(rowid), _as_text(key), value, errors)
        for agent in agents if isinstance(agents, list) else []:
            if isinstance(agent, dict) and agent.get("bcId"):
                found.append((int(rowid), agent))
    return found


def cloud_model(agent: dict) -> tuple[str, str]:
    """(model, requested) of a cloud agent: `modelDetails.modelName`, else
    `requestedModel.modelId`, and that `modelId`."""
    requested = _as_text(_object(agent.get("requestedModel")).get("modelId"))
    model = _as_text(_object(agent.get("modelDetails")).get("modelName")) or requested
    return model, requested


def project_map(path: Path) -> dict[str, tuple[str, str]]:
    """composerId, and a cloud agent's `bcId`, -> (project_path,
    git_branch) from the `state.vscdb` at `path`; {} when it is missing or
    unreadable."""
    return _state_index(path)[0]


def model_map(path: Path) -> dict[str, str]:
    """A cloud agent's `bcId` -> its model, from the `state.vscdb` at
    `path`; {} when it is missing or unreadable."""
    return _state_index(path)[1]


def _state_index(path: Path) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """(project_map, model_map) of the `state.vscdb` at `path`. A cloud
    agent's project is its `repoUrl`. Cached by the file's and its
    sidecar's size and mtime, since every transcript and side database of
    a home asks for the same file."""
    key = [str(path)]
    for p in (path, Path(str(path) + "-wal")):
        try:
            st = p.stat()
            key += [st.st_size, st.st_mtime_ns]
        except OSError:
            key += [None, None]
    cache_key = tuple(key)
    if cache_key in _PROJECT_CACHE:
        return _PROJECT_CACHE[cache_key]
    found: dict[str, tuple[str, str]] = {}
    models: dict[str, str] = {}
    if is_sqlite(path):
        try:
            with open_copy(path) as con:
                # A pre-scan: the file's own parse reports its errors.
                found = {cid: c.project for cid, c in read_composers(con).items()}
                for _rowid, agent in read_cloud_agents(con, []):
                    bc_id = str(agent["bcId"])
                    found.setdefault(bc_id, (_as_text(agent.get("repoUrl")), ""))
                    models.setdefault(bc_id, cloud_model(agent)[0])
        except sqlite3.DatabaseError:
            found, models = {}, {}
    _PROJECT_CACHE.clear()
    _PROJECT_CACHE[cache_key] = (found, models)
    return found, models


_PROJECT_CACHE: dict[tuple, tuple[dict[str, tuple[str, str]], dict[str, str]]] = {}


def _home_state(artifact: Artifact) -> Path | None:
    """The IDE `state.vscdb` in the artifact's home, the first of the
    platform parents that has one."""
    for parent in IDE_PARENTS:
        path = artifact.home.disk_path / parent / "User/globalStorage/state.vscdb"
        if path.is_file():
            return path
    return None


def home_projects(artifact: Artifact) -> dict[str, tuple[str, str]]:
    """The composer and cloud agent projects of the home's IDE
    `state.vscdb`."""
    path = _home_state(artifact)
    return project_map(path) if path else {}


def home_models(artifact: Artifact) -> dict[str, str]:
    """The cloud agent models of the home's IDE `state.vscdb`."""
    path = _home_state(artifact)
    return model_map(path) if path else {}


def cloud_cached_ids(state: Path) -> set[str]:
    """The ids of the `cloud-cache` rows of the `conversation-search.db`
    beside the `state.vscdb` at `state`, whose parse yields their origin
    row; an empty set when it is missing or unreadable."""
    path = state.parent / "conversation-search.db"
    if not is_sqlite(path):
        return set()
    try:
        with open_copy(path) as con:
            if "conversations" not in table_names(con):
                return set()
            sql = "select id from conversations where source = ?"
            return {_as_text(r[0]) for r in con.execute(sql, (CLOUD_CACHE,))}
    except sqlite3.DatabaseError:
        return set()


class CursorParser(Parser):
    agent = "cursor"
    name = "cursor"
    records_origin = True
    records_sync = True
    has_secondary = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return any(
            rx.match(rel)
            for rx in (
                STATE_RX,
                SEARCH_RX,
                TRANSCRIPT_RX,
                TRACKING_RX,
                CLI_CONFIG_RX,
                PERMISSIONS_RX,
                ATTEMPT_RX,
            )
        )

    def secondary(self, artifact: Artifact) -> bool:
        return bool(TRANSCRIPT_RX.match(artifact.rel))

    def secondary_tolerance(self, artifact: Artifact) -> float:
        """60 seconds: the transcript's `<timestamp>` tag has minute
        precision, the user bubble's `createdAt` milliseconds."""
        return 60.0

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        if STATE_RX.match(rel):
            yield from self._database(artifact, self._state, opts)
        elif SEARCH_RX.match(rel):
            yield from self._database(artifact, self._search, opts)
        elif TRACKING_RX.match(rel):
            yield from self._database(artifact, self._tracking, opts)
        elif TRANSCRIPT_RX.match(rel):
            yield from self._transcript(artifact)
        elif ATTEMPT_RX.match(rel):
            yield from self._attempt(artifact)
        else:
            yield from self._settings_file(artifact)

    # -- shared -----------------------------------------------------------

    def _row(
        self, artifact: Artifact, turn_type: str, text: str, when: object = "", line: int = 0
    ) -> Row:
        row = self.base_row(artifact)
        row.turn_type = turn_type
        row.text = text
        row.timestamp_utc = to_utc(when) if when not in (None, "") else ""
        row.source_line = line
        return row

    def _database(self, artifact: Artifact, reader, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            yield self._row(artifact, "system", "parser: not a SQLite database")
            return
        try:
            with open_copy(artifact.disk_path) as con:
                rows = list(reader(artifact, con, opts))
        except sqlite3.DatabaseError as e:
            yield self._row(artifact, "system", "parser: SQLite error: %s" % e)
            return
        yield from rows

    # -- state.vscdb ------------------------------------------------------

    def _state(self, artifact: Artifact, con: sqlite3.Connection, opts: Options) -> Iterator[Row]:
        errors: list = []
        composers = read_composers(con)
        kv = "cursorDiskKV" in table_names(con)
        drafts = {
            key[len("composerDraft:") :]: (rowid, key, value)
            for rowid, key, value in (_prefixed(con, "composerDraft:") if kv else [])
        }
        for cid in drafts:
            composers.setdefault(cid, _Composer(cid))
        deleted: list[_Composer] = []
        for c in composers.values():
            stamp = self._stamper(artifact, c)
            if c.data is not None:
                entries = self._entries(con, c, kv)
                # A draft: never sent, no header list in either layout.
                if entries or c.data.get("status") != "none":
                    yield from self._conversation(con, c, entries, stamp, opts)
            elif self._was_conversation(c):
                deleted.append(c)
                yield from self._deleted(c, stamp)
            if c.cid in drafts:
                yield from self._draft(c, drafts[c.cid], stamp)
            yield from error_rows(self, artifact, c.errors, c.cid, c.project[0])
        if deleted and kv:
            yield from self._blobs(artifact, con, deleted)
        yield from self._standing(artifact, con, errors)
        yield from self._integrations(artifact, con, errors)
        yield from self._cloud(artifact, con, errors)
        yield from self._mcp(artifact, con)
        yield from self._plugins(artifact, con, errors)
        yield from error_rows(self, artifact, errors)

    def _stamper(self, artifact: Artifact, c: _Composer):
        path, branch = c.project

        def stamp(turn_type: str, text: str, when="", line=0, model="") -> Row:
            row = self._row(artifact, turn_type, text, when, line)
            row.session_id = c.cid
            row.project_path = path
            row.git_branch = branch
            row.model = model
            return row

        return stamp

    @staticmethod
    def _was_conversation(c: _Composer) -> bool:
        """A header with no `composerData` is a deleted conversation when it
        is not a draft: it has an `agentLocationHistory` entry or is
        archived."""
        return bool(c.head.get("agentLocationHistory")) or c.archived()

    def _entries(self, con: sqlite3.Connection, c: _Composer, kv: bool) -> list[dict]:
        inline = (c.data or {}).get("fullConversationHeadersOnly")
        if isinstance(inline, list) and inline:
            return [e for e in inline if isinstance(e, dict)]
        if not kv:
            return []
        entries: list[dict] = []
        for rowid, key, value in _prefixed(con, "composerConvHeaders:%s:" % c.cid):
            chunk = _decode(rowid, key, value, c.errors)
            if isinstance(chunk, list):
                entries += [e for e in chunk if isinstance(e, dict)]
        return entries

    def _conversation(
        self, con: sqlite3.Connection, c: _Composer, entries: list[dict], stamp, opts: Options
    ) -> Iterator[Row]:
        data = c.data or {}
        name = compact(data.get("name") or c.head.get("name"))
        if name:
            yield stamp("system", "session name: " + name, c.created(), c.data_rowid)
        yield from self._origin(c, stamp)
        seen: dict = {}
        model = ""
        for entry in entries:
            bid = str(entry.get("bubbleId") or "")
            key = "bubbleId:%s:%s" % (c.cid, bid)
            found = _one(con, key) if bid else None
            if found is None:
                yield stamp("system", "parser: missing bubble " + bid, entry.get("createdAt"))
                continue
            rowid, value = found
            bubble = _object(_decode(rowid, key, value, c.errors))
            if not bubble:
                continue
            if (bubble.get("type") or entry.get("type")) == 1:
                change = track_change(
                    "model",
                    seen,
                    c.cid,
                    str(_object(bubble.get("modelInfo")).get("modelName") or ""),
                )
                model = seen.get(c.cid, "")
                when = bubble.get("createdAt") or entry.get("createdAt")
                if change:
                    yield stamp("system", change, when, rowid, model)
                text = compact(bubble.get("text"))
                if text:
                    yield stamp("user", text, when, rowid, model)
            elif isinstance(bubble.get("toolFormerData"), dict):
                yield from self._tool(bubble, entry, rowid, stamp, model)
            else:
                when = (
                    bubble.get("createdAt") or bubble.get("startedAtMs") or entry.get("createdAt")
                )
                thinking = compact(_object(bubble.get("thinking")).get("text"))
                if thinking and opts.include_thinking:
                    yield stamp("thinking", thinking, when, rowid, model)
                text = compact(bubble.get("text"))
                if text:
                    yield stamp("assistant", text, when, rowid, model)
        if c.archived():
            yield stamp("system", "conversation archived", c.header_updated(), c.data_rowid, model)

    def _origin(self, c: _Composer, stamp) -> Iterator[Row]:
        kind = str(_object(c.head.get("agentLocation")).get("type") or "")
        if kind and kind != "local":
            yield stamp("system", "session origin: remote " + kind, c.created())

    def _tool(self, bubble: dict, entry: dict, rowid: int, stamp, model: str) -> Iterator[Row]:
        tool = bubble["toolFormerData"]
        extra = _object(tool.get("additionalData"))
        name = str(tool.get("name") or "")
        call_id = str(tool.get("toolCallId") or "")
        started = (
            bubble.get("startedAtMs")
            or extra.get("startedAtMs")
            or bubble.get("createdAt")
            or entry.get("createdAt")
        )
        args = tool.get("params") or tool.get("rawArgs")
        args_text = args if isinstance(args, str) else compact_json(args) if args else ""

        def row(turn_type: str, text: str, when) -> Row:
            r = stamp(turn_type, text, when, rowid, model)
            r.tool_name, r.tool_use_id = name, call_id
            return r

        yield row("tool_use", compact(args_text), started)
        review = extra.get("reviewData")
        pending = False
        if isinstance(review, dict):
            if review.get("status") == "None" and extra.get("status") == "rejected":
                # A turn the user stopped: `selectedOption` is a preset.
                text = STOPPED_TEXT
            else:
                pending = review.get("status") != "Done" or tool.get("status") == "loading"
                text = (
                    pending_text(name, extra, review) if pending else permission_text(extra, review)
                )
            yield row("system", text, started)
        result = tool.get("result")
        result_text = ""
        if result not in (None, ""):
            result_text = compact(result if isinstance(result, str) else compact_json(result))
        rejected = extra.get("status") == "rejected" and not pending
        if result_text or rejected:
            text = ("[rejected] " if rejected else "") + result_text
            yield row("tool_result", compact(text), bubble.get("completedAtMs") or started)

    def _deleted(self, c: _Composer, stamp) -> Iterator[Row]:
        line = int((c.header or {}).get("_rowid") or 0)
        name = compact(c.head.get("name"))
        if name:
            yield stamp("system", "session name: " + name, c.created(), line)
        yield from self._origin(c, stamp)
        # The delete sets `isArchived`: no `conversation archived` row.
        text = DELETED_TEXT + (ARCHIVED_BY_DELETE if c.archived() else "")
        yield stamp("system", text, c.header_updated(), line)

    def _draft(self, c: _Composer, found, stamp) -> Iterator[Row]:
        rowid, key, value = found
        draft = _object(_decode(rowid, key, value, c.errors))
        text = compact(draft.get("text"))
        if text:
            yield stamp("system", "unsent draft: " + text, c.created(), rowid)

    def _blobs(
        self, artifact: Artifact, con: sqlite3.Connection, deleted: list[_Composer]
    ) -> Iterator[Row]:
        """User and assistant rows from the JSON `agentKv` blobs that name a
        deleted composer. A blob that is not JSON is protobuf, not an
        error."""
        for rowid, _key, value in _prefixed(con, "agentKv:blob:"):
            try:
                blob = json.loads(_as_text(value))
            except ValueError:
                continue
            if not isinstance(blob, dict) or "content" not in blob:
                continue
            content = blob.get("content")
            haystack = content if isinstance(content, str) else compact_json(content)
            for c in deleted:
                if c.cid not in haystack:
                    continue
                stamp = self._stamper(artifact, c)
                role = str(blob.get("role") or "")
                text = compact(text_of(content))
                if role in ("user", "assistant"):
                    row = stamp(role, text, "", rowid)
                    row.recovered = "yes"
                else:
                    row = stamp("system", "%s: %s" % (_role_label(role), text), "", rowid)
                yield row

    def _standing(self, artifact: Artifact, con: sqlite3.Connection, errors: list) -> Iterator[Row]:
        if "ItemTable" not in table_names(con):
            return
        items = {}
        sql = "select rowid, key, value from ItemTable where key in (?, ?)"
        for rowid, key, value in con.execute(sql, (SETTINGS_KEY, SANDBOX_KEY)):
            items[_as_text(key)] = (int(rowid), value)
        if SETTINGS_KEY not in items:
            return
        rowid, value = items[SETTINGS_KEY]
        settings = _object(_decode(rowid, SETTINGS_KEY, value, errors))
        sandbox = False
        if SANDBOX_KEY in items:
            sandbox = _decode(items[SANDBOX_KEY][0], SANDBOX_KEY, items[SANDBOX_KEY][1], []) is True
        mtime = file_mtime(artifact)
        for text in standing_texts(_object(settings.get("composerState")), sandbox):
            yield self._row(artifact, "system", text, mtime, rowid)
        used = _object(_object(settings.get("aiSettings")).get("modelLastUsedAt"))
        for model_id, when in used.items():
            text = "model last used: %s %s" % (model_id, MODEL_USED_SOURCE)
            yield self._row(artifact, "system", text, when, rowid)

    def _integrations(
        self, artifact: Artifact, con: sqlite3.Connection, errors: list
    ) -> Iterator[Row]:
        """`source host:` rows from the editor's own GitHub sign-in and
        `remote agent host enrolled:` rows. Only the `github-*` and
        `remoteAgentHost.*` keys are selected, so no `secret://` value is
        ever read."""
        if "ItemTable" not in table_names(con):
            return
        sql = (
            "select rowid, key, value from ItemTable"
            " where substr(key, 1, 7) = 'github-' or substr(key, 1, 16) = 'remoteAgentHost.'"
        )
        items = {_as_text(key): (int(rowid), value) for rowid, key, value in con.execute(sql)}
        mtime = file_mtime(artifact)
        for key in sorted(items):
            rowid, value = items[key]
            if key.startswith("github-") and not key.endswith("-usages"):
                login = key[len("github-") :]
                # Another extension's `github-` key that is not the account
                # list is skipped; a cut account list is a bad record.
                if not login or not isinstance(_plain(value), list):
                    if _as_text(value).startswith("["):
                        _decode(rowid, key, value, errors)
                    continue
                usages = []
                if key + "-usages" in items:
                    u_rowid, u_value = items[key + "-usages"]
                    found = _decode(u_rowid, key + "-usages", u_value, errors)
                    usages = (
                        [u for u in found if isinstance(u, dict)] if isinstance(found, list) else []
                    )
                yield self._row(
                    artifact,
                    "system",
                    github_text(login, key, usages),
                    last_used(usages) or mtime,
                    rowid,
                )
            elif key.startswith(ENROLLED_PREFIX) and _plain(value) is True:
                account = key[len(ENROLLED_PREFIX) :]
                raw = items.get(DISPLAY_PREFIX + account, (0, None))[1]
                name = _plain(raw)
                name = compact(name if isinstance(name, str) else _as_text(raw)) or "-"
                text = (
                    "remote agent host enrolled: %s (from state.vscdb %s, file mtime;"
                    " on by default, a paired device leaves no local record)" % (name, key)
                )
                yield self._row(artifact, "system", text, mtime, rowid)

    def _cloud(self, artifact: Artifact, con: sqlite3.Connection, errors: list) -> Iterator[Row]:
        """Rows of the cloud agent lists and of the repository list. The
        origin row of an agent is left to `conversation-search.db` when it
        has a `cloud-cache` row for the agent. `bcCachedDetails:<bcId>` is
        protobuf with no schema and is not read."""
        if "ItemTable" not in table_names(con):
            return
        cached = cloud_cached_ids(artifact.disk_path)
        agents = read_cloud_agents(con, errors)
        for rowid, agent in agents:
            yield from self._cloud_agent(artifact, rowid, agent, cached)
        yield from self._mcp_auth(artifact, con, agents, errors)
        found = con.execute(
            "select rowid, value from ItemTable where key = ?", (GITHUB_REPOS_KEY,)
        ).fetchone()
        if found is None:
            return
        repos = _decode(int(found[0]), GITHUB_REPOS_KEY, found[1], errors)
        mtime = file_mtime(artifact)
        for repo in repos if isinstance(repos, list) else []:
            if isinstance(repo, dict):
                yield self._row(artifact, "system", repository_text(repo), mtime, int(found[0]))

    def _cloud_agent(
        self, artifact: Artifact, rowid: int, agent: dict, cached: set[str]
    ) -> Iterator[Row]:
        """`session origin:`, `model:`, `source host:` and `cloud agent:`
        rows of one element of a cloud agent list, in its session."""
        bc_id = str(agent["bcId"])
        repo = _as_text(agent.get("repoUrl"))
        model, requested = cloud_model(agent)
        created = agent.get("createdAt") or agent.get("rowUpdatedAtMs")

        def row(text: str, when) -> Row:
            r = self._row(artifact, "system", text, when, rowid)
            r.session_id, r.project_path, r.model = bc_id, repo, model
            return r

        if bc_id not in cached:
            yield row(CLOUD_ORIGIN, created)
        yield row(CLOUD_SYNCED % bc_id, created)
        if model:
            extra = " requested=" + requested if requested and requested != model else ""
            yield row("model: " + model + extra, created)
        github_repo = github_repository(repo)
        if github_repo:
            yield row("source host: github.com %s (cloud agent)" % github_repo, created)
        yield row(cloud_text(agent), agent.get("rowUpdatedAtMs") or created)

    def _mcp_auth(
        self, artifact: Artifact, con: sqlite3.Connection, agents: list, errors: list
    ) -> Iterator[Row]:
        """`permission decision: <userDecision> mcp auth for cloud agent
        <agentId> ...` from `cloudAgentRepository.mcpAuthResolution`, in
        the agent's session and joined on its `toolCallId`, at the file's
        modification time; project and model from the agent list."""
        found = con.execute(
            "select rowid, value from ItemTable where key = ?", (MCP_AUTH_KEY,)
        ).fetchone()
        if found is None:
            return
        doc = _decode(int(found[0]), MCP_AUTH_KEY, found[1], errors)
        known = {str(a["bcId"]): a for _rowid, a in agents}
        mtime = file_mtime(artifact)
        for res in doc if isinstance(doc, list) else [doc]:
            if not isinstance(res, dict):
                continue
            agent_id, call_id = _as_text(res.get("agentId")), _as_text(res.get("toolCallId"))
            text = "permission decision: %s mcp auth for cloud agent %s tool_call=%s %s" % (
                _field(res.get("userDecision")),
                _field(agent_id),
                _field(call_id),
                MCP_AUTH_SOURCE,
            )
            row = self._row(artifact, "system", text, mtime, int(found[0]))
            row.session_id, row.tool_use_id = agent_id, call_id
            if agent_id in known:
                row.project_path = _as_text(known[agent_id].get("repoUrl"))
                row.model = cloud_model(known[agent_id])[0]
            yield row

    def _mcp(self, artifact: Artifact, con: sqlite3.Connection) -> Iterator[Row]:
        """`mcp server: <server> url=<url> (from ...)` per MCP OAuth scope
        with an `mcp_server_url`, at its `mcp_oauth_updated_at_ms`, else the
        file's modification time, with ` tokens=stored (ciphertext, not
        read)` when an `mcpOAuth.secret.` key names `mcp_tokens` for the
        scope. Only the key names of the secret rows are selected. The
        `oauth-attempt:` scopes and keys whose name does not decode to
        `[<scope>] <field>` are skipped."""
        if "ItemTable" not in table_names(con):
            return
        sql = "select key from ItemTable where substr(key, 1, ?) = ?"
        tokens = set()
        for (key,) in con.execute(sql, (len(MCP_SECRET_PREFIX), MCP_SECRET_PREFIX)):
            name = mcp_key_name(_as_text(key), MCP_SECRET_PREFIX)
            if name and name[1] == "mcp_tokens":
                tokens.add(name[0])
        sql = "select rowid, key, value from ItemTable where substr(key, 1, ?) = ? order by key"
        scopes: dict[str, dict[str, tuple[int, object]]] = {}
        for rowid, key, value in con.execute(sql, (len(MCP_GLOBAL_PREFIX), MCP_GLOBAL_PREFIX)):
            name = mcp_key_name(_as_text(key), MCP_GLOBAL_PREFIX)
            if name and not name[0].startswith("oauth-attempt:"):
                scopes.setdefault(name[0], {})[name[1]] = (int(rowid), value)
        mtime = file_mtime(artifact)
        for scope in sorted(scopes):
            fields = scopes[scope]
            if "mcp_server_url" not in fields:
                continue
            rowid, raw = fields["mcp_server_url"]
            url = _plain(raw)
            url = url if isinstance(url, str) else _as_text(raw)
            updated = _plain(fields.get("mcp_oauth_updated_at_ms", (0, None))[1])
            has_time = isinstance(updated, (int, float)) and not isinstance(updated, bool)
            text = "mcp server: %s url=%s (from state.vscdb mcpOAuth.global, %s)" % (
                scope.split("::", 1)[0],
                _field(compact(url)),
                "mcp_oauth_updated_at_ms" if has_time else "file mtime",
            )
            if scope in tokens:
                text += MCP_TOKENS
            yield self._row(artifact, "system", text, updated if has_time else mtime, rowid)

    def _plugins(self, artifact: Artifact, con: sqlite3.Connection, errors: list) -> Iterator[Row]:
        """`plugin installed: id=<id> sources=<sources> scope=<scope> (from
        ...)` per entry of each `cursor.plugins.installedIds.<team>|<scope>`
        list, at the file's modification time; a `file://` scope is the
        row's `project_path`. A value that is not a JSON list is skipped,
        one that starts as a list and does not decode is an error entry."""
        if "ItemTable" not in table_names(con):
            return
        sql = "select rowid, key, value from ItemTable where substr(key, 1, ?) = ? order by key"
        mtime = file_mtime(artifact)
        for rowid, key, value in con.execute(sql, (len(PLUGINS_PREFIX), PLUGINS_PREFIX)):
            key = _as_text(key)
            scope = key[len(PLUGINS_PREFIX) :].rsplit("|", 1)[-1]
            entries = None
            if _as_text(value).lstrip().startswith("["):
                entries = _decode(int(rowid), key, value, errors)
            for entry in entries if isinstance(entries, list) else []:
                if not isinstance(entry, dict):
                    continue
                sources = entry.get("sources")
                names = ",".join(str(s) for s in sources) if isinstance(sources, list) else ""
                text = "plugin installed: id=%s sources=%s scope=%s %s" % (
                    _value(entry.get("id")),
                    names or "-",
                    _field(scope),
                    PLUGINS_SOURCE,
                )
                row = self._row(artifact, "system", text, mtime, int(rowid))
                row.project_path = uri_path(scope) if scope.startswith("file:") else ""
                yield row

    # -- side databases --------------------------------------------------

    def _search(self, artifact: Artifact, con: sqlite3.Connection, opts: Options) -> Iterator[Row]:
        if "conversations" not in table_names(con):
            return
        projects, models = home_projects(artifact), home_models(artifact)
        bodies = fts_bodies(con)
        for rec in _select(con, "conversations", SEARCH_COLUMNS):
            sid = _as_text(rec.get("id"))

            def row(text: str, rec=rec, sid=sid) -> Row:
                r = self._row(artifact, "system", text, rec.get("updated_at"), int(rec["_rowid"]))
                self._join(r, sid, projects)
                r.model = models.get(sid, "")
                return r

            source = _as_text(rec.get("source"))
            if source == CLOUD_CACHE:
                yield row(CLOUD_ORIGIN)
            title = compact(_as_text(rec.get("title")))
            if title:
                yield row(
                    "conversation index: %s source=%s archived=%s"
                    % (title, _field(source), _field(rec.get("is_archived")))
                )
            body = compact(_as_text(bodies.get(rec.get("fts_rowid"))))
            if body:
                yield row(
                    "cached conversation text (conversation-search.db, source=%s): %s"
                    % (_field(source), body)
                )

    def _tracking(
        self, artifact: Artifact, con: sqlite3.Connection, opts: Options
    ) -> Iterator[Row]:
        tables = table_names(con)
        projects = home_projects(artifact)
        for table, columns in TRACKING_TABLES.items():
            if table not in tables:
                continue
            for rec in _select(con, table, columns):
                text, when, sid = tracking_text(table, rec)
                row = self._row(artifact, "system", text, when, int(rec["_rowid"]))
                self._join(row, sid, projects)
                row.model = _as_text(rec.get("model"))
                if table == "scored_commits":
                    row.git_branch = _as_text(rec.get("branchName"))
                yield row

    @staticmethod
    def _join(row: Row, sid: str, projects: dict) -> None:
        row.session_id = sid
        if sid in projects:
            row.project_path, row.git_branch = projects[sid]

    # -- transcript JSONL -------------------------------------------------

    def _transcript(self, artifact: Artifact) -> Iterator[Row]:
        m = TRANSCRIPT_RX.match(artifact.rel)
        sid = m.group(1) if m else ""
        path, branch = home_projects(artifact).get(sid, ("", ""))
        errors: list = []

        def row(turn_type: str, text: str, when: str, line: int) -> Row:
            r = self._row(artifact, turn_type, text, "", line)
            r.timestamp_utc = when
            r.session_id, r.project_path, r.git_branch = sid, path, branch
            return r

        for n, rec in iter_jsonl(artifact.disk_path, errors):
            role = rec.get("role")
            if role not in ("user", "assistant"):
                continue
            content = _object(rec.get("message")).get("content")
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    if role == "user":
                        query, when = unwrap_query(block["text"])
                        text = compact(query)
                        if text:
                            yield row("user", text, when, n)
                    elif compact(block["text"]):
                        yield row("assistant", compact(block["text"]), "", n)
                elif block.get("type") == "tool_use":
                    r = row("tool_use", compact_json(block.get("input")), "", n)
                    r.tool_name = str(block.get("name") or "")
                    yield r
        yield from error_rows(self, artifact, errors, sid, path)

    # -- MCP OAuth attempt files ------------------------------------------

    def _attempt(self, artifact: Artifact) -> Iterator[Row]:
        """`mcp oauth attempt: server=<serverUrl> client_id=<client_id>
        workspace=<workspaceId> (from mcp-oauth-attempts/<file>)` at
        `createdAtMs`, else the file's modification time (and the text
        says so). The client id is an identifier, not a secret."""
        rel = artifact.rel
        try:
            with open(artifact.disk_path, "rb") as fh:
                doc = json.loads(fh.read().decode("utf-8", errors="replace"))
        except (OSError, ValueError) as e:
            yield self._row(
                artifact, "system", "parser: unreadable %s: %s" % (rel, error_reason(e))
            )
            return
        if not isinstance(doc, dict):
            yield self._row(artifact, "system", "parser: %s is not a JSON object" % rel)
            return
        m = ATTEMPT_RX.match(rel)
        source = "mcp-oauth-attempts/" + (m.group(1) if m else "")
        created = doc.get("createdAtMs")
        if created in (None, ""):
            created, source = file_mtime(artifact), source + ", file mtime"
        text = "mcp oauth attempt: server=%s client_id=%s workspace=%s (from %s)" % (
            _field(doc.get("serverUrl")),
            _field(_object(doc.get("clientInformation")).get("client_id")),
            _field(_object(doc.get("owner")).get("workspaceId")),
            source,
        )
        yield self._row(artifact, "system", text, created, 1)

    # -- settings files ---------------------------------------------------

    def _settings_file(self, artifact: Artifact) -> Iterator[Row]:
        rel = artifact.rel
        try:
            with open(artifact.disk_path, "rb") as fh:
                doc = json.loads(fh.read().decode("utf-8", errors="replace"))
        except (OSError, ValueError) as e:
            yield self._row(
                artifact, "system", "parser: unreadable %s: %s" % (rel, error_reason(e))
            )
            return
        if not isinstance(doc, dict):
            yield self._row(artifact, "system", "parser: %s is not a JSON object" % rel)
            return
        if CLI_CONFIG_RX.match(rel):
            settings = cli_config_settings(doc)
        else:
            settings = permissions_settings(doc)
        mtime = file_mtime(artifact)
        project = artifact.home.original if artifact.home.project else ""
        for setting in settings:
            row = self._row(
                artifact,
                "system",
                compact("permission setting: %s (from %s, file mtime)" % (setting, rel)),
                mtime,
                1,
            )
            row.project_path = project
            yield row


def _field(value) -> str:
    text = _as_text(value)
    return text if text != "" else "-"


def _role_label(role: str) -> str:
    return "system prompt" if role == "system" else "%s message" % (role or "-")


def _value(value) -> str:
    """A cloud agent field as row text: `-` when absent or empty, else as
    `setting_value` writes it."""
    return "-" if value in (None, "") else setting_value(value)


def mcp_key_name(key: str, prefix: str) -> tuple[str, str] | None:
    """(scope, field) of an `mcpOAuth.global.` or `mcpOAuth.secret.` key,
    whose suffix is URL-safe base64 (unpadded) of `[<scope>] <field>`; None
    when it does not decode to that form. Only the key name is read."""
    suffix = key[len(prefix) :]
    try:
        name = base64.urlsafe_b64decode(suffix + "=" * (-len(suffix) % 4)).decode("utf-8")
    except ValueError:
        return None
    m = MCP_KEY_RX.match(name)
    return (m.group(1), m.group(2)) if m else None


def uri_path(uri: str) -> str:
    """The path of a `file://` URI, percent-decoded; a Windows drive path
    (`file:///c%3A/Users/...`) in the drive form `c:\\Users\\...` that
    `fsPath` writes."""
    path = unquote(urlparse(uri).path)
    if re.match(r"^/[A-Za-z]:", path):
        return path[1:].replace("/", "\\")
    return path


def fts_bodies(con: sqlite3.Connection) -> dict:
    """`conversation_fts_content` `id` -> `c1` (the body; `c0` is the
    title), read from the FTS5 shadow table as a plain table, so the fts5
    module is never needed; {} when the table or a column is missing."""
    if "conversation_fts_content" not in table_names(con):
        return {}
    have = {r[1] for r in con.execute("pragma table_info(conversation_fts_content)")}
    if not {"id", "c1"} <= have:
        return {}
    return {r[0]: r[1] for r in con.execute("select id, c1 from conversation_fts_content")}


def github_repository(url: str) -> str:
    """`<owner>/<repo>` when the host of `url` is `github.com`, else `""`.
    Cursor writes `repoUrl` without a scheme (`github.com/<owner>/<repo>`),
    so a scheme-less value is parsed as a network path; the host is
    compared after parsing, never as a prefix of the string, so a path or
    a longer host that merely contains `github.com` does not match."""
    parsed = urlparse(url if "://" in url else "//" + url)
    if parsed.hostname != "github.com":
        return ""
    return parsed.path.strip("/")


def cloud_text(agent: dict) -> str:
    """`cloud agent: <name> repo=<repoUrl> status=<status> workflowStatus=
    <workflowStatus> archived=<isArchived> killed=<isKilled>
    vmStarted=<hasStartedVm> (from ...)`, `-` for an absent value."""
    return (
        "cloud agent: %s repo=%s status=%s workflowStatus=%s archived=%s killed=%s vmStarted=%s %s"
        % (
            compact(agent.get("name")) or "-",
            _value(agent.get("repoUrl")),
            _value(agent.get("status")),
            _value(agent.get("workflowStatus")),
            _value(agent.get("isArchived")),
            _value(agent.get("isKilled")),
            _value(agent.get("hasStartedVm")),
            CLOUD_SOURCE,
        )
    )


def repository_text(repo: dict) -> str:
    """`source host repository: <url, else name> type=<type> (from ...)`
    for one element of `cloudEnvironmentTemplate.githubRepos`."""
    target = _as_text(repo.get("url")) or _as_text(repo.get("name")) or "-"
    return "source host repository: %s type=%s %s" % (
        target,
        _value(repo.get("type")),
        REPOS_SOURCE,
    )


def pending_text(name: str, extra: dict, review: dict) -> str:
    """`permission prompt pending: <tool_name> reason=<blockReason>
    options=<allowlistOptions ids>` for a prompt still open when the store
    was copied; its `selectedOption` is a preset, not a decision."""
    ids = [
        _as_text(option.get("id"))
        for option in review.get("allowlistOptions") or []
        if isinstance(option, dict) and option.get("id") is not None
    ]
    return "permission prompt pending: %s reason=%s options=%s" % (
        _field(name),
        _field(extra.get("blockReason")),
        ",".join(ids) or "-",
    )


def permission_text(extra: dict, review: dict) -> str:
    """`permission decision: <selectedOption> outcome=<status>
    approval=<approvalType> reason=<blockReason>`, then ` allowlisted=` with
    the applied allowlist entries when there are any, which marks an
    allow-always decision whatever `selectedOption` says."""
    text = "permission decision: %s outcome=%s approval=%s reason=%s" % (
        _field(review.get("selectedOption")),
        _field(extra.get("status")),
        _field(review.get("approvalType")),
        _field(extra.get("blockReason")),
    )
    applied = review.get("appliedAllowlistOptionIds")
    if isinstance(applied, list) and applied:
        names = {}
        for option in review.get("allowlistOptions") or []:
            if isinstance(option, dict) and option.get("id") is not None:
                names[str(option["id"])] = str(option.get("commandName") or option["id"])
        text += " allowlisted=" + ",".join(names.get(str(i), str(i)) for i in applied)
    return text


def standing_texts(state: dict, sandbox: bool) -> Iterator[str]:
    """The `permission setting:` texts of the settings blob's
    `composerState`: one per standing-list entry, one per `modes4` entry
    and one per boolean switch."""
    for key in STANDING_LISTS:
        for entry in state.get(key) or [] if isinstance(state.get(key), list) else []:
            yield "permission setting: %s=%s %s" % (key, setting_value(entry), COMPOSER_SOURCE)
    for mode in state.get("modes4") or [] if isinstance(state.get("modes4"), list) else []:
        if not isinstance(mode, dict):
            continue
        flags = " ".join(
            "%s=%s" % (flag, setting_value(mode[flag]) if flag in mode else "-")
            for flag in ("autoRun", "smartModeAutoRun", "fullAutoRun")
        )
        yield "permission setting: run mode %s=%s %s sandbox=%s %s" % (
            _field(mode.get("id")),
            run_mode(mode, sandbox),
            flags,
            setting_value(sandbox),
            COMPOSER_SOURCE,
        )
    for key in SWITCHES:
        if key in state:
            yield "permission setting: %s=%s %s" % (key, setting_value(state[key]), COMPOSER_SOURCE)


def _plain(value):
    """A short ItemTable value: its JSON value when it decodes, else its
    text (`remoteAgentHost.displayName.<account>` may be either)."""
    text = _as_text(value)
    try:
        return json.loads(text)
    except ValueError:
        return text


def last_used(usages: list[dict]):
    """The latest `lastUsed` (epoch ms) of a `github-<login>-usages` list,
    or None."""
    times = [u["lastUsed"] for u in usages if isinstance(u.get("lastUsed"), (int, float))]
    return max(times) if times else None


def github_text(login: str, key: str, usages: list[dict]) -> str:
    """`source host: github account <login> scopes=<scopes> (from state.vscdb
    key <key>)`, the scopes deduplicated from the usages' `scopes` lists."""
    scopes: list[str] = []
    for usage in usages:
        for scope in usage.get("scopes") or [] if isinstance(usage.get("scopes"), list) else []:
            if str(scope) not in scopes:
                scopes.append(str(scope))
    return "source host: github account %s scopes=%s (from state.vscdb key %s)" % (
        login,
        ",".join(scopes) or "-",
        key,
    )


def _entries(value) -> list:
    return value if isinstance(value, list) else []


def cli_config_settings(doc: dict) -> Iterator[str]:
    """`<key>=<value>` per setting of `.cursor/cli-config.json` that
    governs permissions."""
    if "approvalMode" in doc:
        yield "approvalMode=%s" % setting_value(doc["approvalMode"])
    permissions = _object(doc.get("permissions"))
    for key in ("allow", "deny"):
        for entry in _entries(permissions.get(key)):
            yield "permissions.%s=%s" % (key, setting_value(entry))
    sandbox = _object(doc.get("sandbox"))
    if "mode" in sandbox:
        yield "sandbox.mode=%s" % setting_value(sandbox["mode"])


def permissions_settings(doc: dict) -> Iterator[str]:
    """`<key>=<value>` per entry of a `permissions.json`."""
    allowlists = _object(doc.get("allowlists"))
    for key in ("mcp", "terminal"):
        for entry in _entries(allowlists.get(key)):
            yield "allowlists.%s=%s" % (key, setting_value(entry))
    if "approvalMode" in doc:
        yield "approvalMode=%s" % setting_value(doc["approvalMode"])
    for key in ("allowInstructions", "blockInstructions"):
        for entry in _entries(doc.get(key)):
            yield "%s=%s" % (key, setting_value(entry))


def tracking_text(table: str, rec: dict) -> tuple[str, object, str]:
    """(text, time, session id) of an `ai-code-tracking.db` row."""
    f = {k: _field(v) for k, v in rec.items()}
    sid = _as_text(rec.get("conversationId") or rec.get("composerId"))
    if table == "ai_code_hashes":
        text = "ai code: %s source=%s model=%s request=%s" % (
            f.get("fileName", "-"),
            f.get("source", "-"),
            f.get("model", "-"),
            f.get("requestId", "-"),
        )
        return text, rec.get("timestamp"), sid
    if table == "conversation_summaries":
        text = "conversation summary: %s: %s" % (f.get("title", "-"), f.get("tldr", "-"))
        return text, rec.get("updatedAt"), sid
    if table == "ai_deleted_files":
        text = "file deleted by agent: %s model=%s" % (f.get("gitPath", "-"), f.get("model", "-"))
        return text, rec.get("deletedAt"), sid
    text = "scored commit: %s branch=%s +%s -%s" % (
        f.get("commitHash", "-"),
        f.get("branchName", "-"),
        f.get("linesAdded", "-"),
        f.get("linesDeleted", "-"),
    )
    return text, rec.get("scoredAt"), ""
