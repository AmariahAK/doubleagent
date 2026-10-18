"""Synthetic agent state in the shapes the parsers were validated against.
Content is invented; field names and nesting match real Claude Code and Codex
CLI files as of October 2026 (see the parser module docstrings)."""

from __future__ import annotations

import datetime
import json
import os
import sqlite3
from pathlib import Path

import zstandard

from doubleagent.parsers.antigravity import SCHEMA as AGY
from doubleagent.protobuf import encode

CLAUDE_SESSION = "11111111-2222-4333-8444-555555555555"
CLAUDE_WORK_SESSION = "11111111-2222-4333-8444-666666666666"
# A 2.1.295 session in the same project, and the session a Remote Control
# process in the registry fixture is bound to (no transcript).
CLAUDE_295_SESSION = "11111111-2222-4333-8444-777777777777"
CLAUDE_BRIDGE_SESSION = "11111111-2222-4333-8444-888888888888"
# A 2.1.296 session with permission mode and model changes (issue 93).
CLAUDE_296_SESSION = "11111111-2222-4333-8444-999999999999"
# Modification time given to the settings fixtures: 2026-10-01T09:00:00Z.
CLAUDE_SETTINGS_MTIME = 1790845200
CLAUDE_REGISTRY_KEY = "4242." + "ab" * 32 + ".key"
CODEX_SESSION = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
CODEX_SUBAGENT = "aaaaaaaa-bbbb-4ccc-8ddd-000000000002"
CODEX_FORK = "aaaaaaaa-bbbb-4ccc-8ddd-000000000003"
CODEX_LEGACY = "aaaaaaaa-bbbb-4ccc-8ddd-000000000004"
CODEX_REVERT_ROLLOUT = "aaaaaaaa-bbbb-4ccc-8ddd-000000000005"
# Synthetic ChatGPT ids of the shapes Codex Desktop writes in session_meta (#118):
# a 36-character uuid account id and a 29-character user id.
CODEX_ACCOUNT = "11111111-2222-4333-8444-555555555555"
CODEX_USER = "user-AbCdEfGhIjKlMnOpQrStUvWx"


def _jsonl(path: Path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


CLAUDE_TOOL_RESULT = "b1c2d3e4f.txt"
CLAUDE_PERSISTED = "line 1 of the full output\nline 2 of the full output"


def _claude_common(cwd, branch, **extra):
    return dict(
        sessionId=CLAUDE_SESSION,
        cwd=cwd,
        gitBranch=branch,
        version="2.1.289",
        userType="external",
        isSidechain=False,
        entrypoint="cli",
        **extra,
    )


def _claude_assistant(common, uuid, t, blocks, model="claude-fable-5-1", **extra):
    return dict(
        common,
        type="assistant",
        uuid=uuid,
        timestamp="2026-10-01T10:00:%s.000Z" % t,
        requestId="req_" + uuid,
        message={
            "model": model,
            "id": "msg_" + uuid,
            "type": "message",
            "role": "assistant",
            "content": blocks,
        },
        **extra,
    )


def _claude_user(common, uuid, t, content, **extra):
    return dict(
        common,
        type="user",
        uuid=uuid,
        timestamp="2026-10-01T10:00:%s.000Z" % t,
        message={"role": "user", "content": content},
        **extra,
    )


def _claude_attachment(common, uuid, t, attachment):
    return dict(
        common,
        type="attachment",
        uuid=uuid,
        timestamp="2026-10-01T10:00:%s.000Z" % t,
        attachment=attachment,
    )


def _claude_result(tool_use_id, content):
    return [{"tool_use_id": tool_use_id, "type": "tool_result", "content": content}]


def _claude_stub(name):
    return (
        "<persisted-output>\nOutput too large (32.8KB). Full output saved to: "
        "/home/alice/.claude/projects/-srv-proj/%s/tool-results/%s\n\n"
        "Preview (first 2KB):\nline 1 of the full output\n</persisted-output>"
    ) % (CLAUDE_SESSION, name)


def claude_session_records(cwd="/srv/proj", branch="main"):
    """Line numbers are what ClaudeCodeTests.test_rows asserts."""
    c = _claude_common(cwd, branch)
    sid = CLAUDE_SESSION
    return [
        dict(type="mode", mode="normal", sessionId=sid),  # 1
        _claude_user(
            c,
            "u1",
            "00",
            "delete the logs in /var/log please",
            parentUuid=None,
            origin={"kind": "human"},
            promptSource="typed",
        ),  # 2
        _claude_assistant(
            c, "a1", "01", [{"type": "thinking", "thinking": "private reasoning", "signature": "x"}]
        ),  # 3
        _claude_assistant(
            c, "a1b", "01", [{"type": "thinking", "thinking": "", "signature": "c2ln"}]
        ),  # 4: empty thinking, skipped
        _claude_assistant(
            c,
            "a2",
            "02",
            [
                {
                    "type": "tool_use",
                    "id": "toolu_01",
                    "name": "Bash",
                    "input": {"command": "rm -rf /var/log/*.log", "description": "Remove logs"},
                    "caller": {"type": "direct"},
                }
            ],
            wireToolInputs={
                "toolu_01": {
                    "command": "cd /srv/proj && rm -rf /var/log/*.log",
                    "description": "Remove logs",
                }
            },
            wireIngestContext={"toolu_01": {"cwd": "/srv/proj"}},
        ),  # 5
        _claude_user(
            c,
            "u2",
            "03",
            [
                {
                    "tool_use_id": "toolu_01",
                    "type": "tool_result",
                    "content": "removed 3 files",
                    "is_error": False,
                }
            ],
            toolUseResult={"stdout": "removed 3 files", "stderr": "", "interrupted": False},
            sourceToolAssistantUUID="a2",
        ),  # 6
        dict(
            type="queue-operation",
            operation="enqueue",
            timestamp="2026-10-01T10:00:03.500Z",
            sessionId=sid,
            content="also check /tmp",
        ),  # 7: delivered by the attachment on line 8
        _claude_attachment(
            c,
            "t1",
            "04",
            {
                "type": "queued_command",
                "prompt": "also check /tmp",
                "commandMode": "prompt",
                "origin": {"kind": "human"},
                "humanTurn": True,
                "source_uuid": "q1",
                "delivery_id": "d1",
                "timestamp": "2026-10-01T10:00:03.500Z",
            },
        ),  # 8
        _claude_attachment(
            c,
            "t2",
            "04",
            {
                "type": "edited_text_file",
                "filename": "/srv/proj/notes.md",
                "snippet": "1\tfile body",
            },
        ),  # 9
        _claude_attachment(
            c,
            "t3",
            "04",
            {
                "type": "hook_system_message",
                "hookName": "PostToolUse:Bash",
                "hookEvent": "PostToolUse",
                "toolUseID": "toolu_01",
                "content": "lint passed",
            },
        ),  # 10
        _claude_attachment(
            c, "t4", "04", {"type": "total_tokens_reminder", "text": "tokens used"}
        ),  # 11: skipped
        _claude_assistant(
            c, "a3", "04", [{"type": "text", "text": "Done. Three log files were removed."}]
        ),  # 12
        dict(
            c,
            type="system",
            uuid="s1",
            parentUuid="a3",
            timestamp="2026-10-01T10:00:05.000Z",
            subtype="turn_duration",
            durationMs=4000,
            messageCount=5,
            isMeta=False,
        ),  # 13
        _claude_user(
            c,
            "u3",
            "06",
            "<command-name>/model</command-name>\n<command-message>model</command-message>\n"
            "<command-args></command-args>",
        ),  # 14
        _claude_user(
            c, "u4", "06", "<local-command-stdout>Set model to Fable</local-command-stdout>"
        ),  # 15
        _claude_user(
            c,
            "u5",
            "07",
            "<task-notification>\n<task-id>b1</task-id>\n<status>completed</status>\n"
            "</task-notification>",
            origin={"kind": "task-notification"},
            promptSource="system",
        ),  # 16
        _claude_assistant(
            c,
            "a4",
            "08",
            [
                {
                    "type": "tool_use",
                    "id": "toolu_02",
                    "name": "ToolSearch",
                    "input": {"query": "select:WebFetch"},
                }
            ],
        ),  # 17
        _claude_user(
            c,
            "u6",
            "09",
            _claude_result("toolu_02", [{"type": "tool_reference", "tool_name": "WebFetch"}]),
        ),  # 18
        _claude_assistant(
            c,
            "a5",
            "10",
            [
                {
                    "type": "tool_use",
                    "id": "toolu_03",
                    "name": "Read",
                    "input": {"file_path": "/srv/proj/big.log"},
                }
            ],
        ),  # 19
        _claude_user(
            c, "u7", "11", _claude_result("toolu_03", _claude_stub(CLAUDE_TOOL_RESULT))
        ),  # 20: the stub's file exists
        _claude_assistant(
            c,
            "a6",
            "12",
            [
                {
                    "type": "tool_use",
                    "id": "toolu_04",
                    "name": "Read",
                    "input": {"file_path": "/srv/proj/gone.log"},
                }
            ],
        ),  # 21
        _claude_user(
            c, "u8", "13", _claude_result("toolu_04", _claude_stub("f0e1d2c3b.txt"))
        ),  # 22: the stub's file is missing
        _claude_assistant(
            c,
            "a7",
            "14",
            [{"type": "text", "text": "API Error: rate limited"}],
            model="<synthetic>",
            isApiErrorMessage=True,
            apiErrorStatus=429,
            error="rate_limit",
        ),  # 23
        dict(
            c,
            type="system",
            uuid="s2",
            timestamp="2026-10-01T10:00:15.000Z",
            subtype="api_error",
            level="error",
            retryInMs=500,
            retryAttempt=1,
            maxRetries=10,
            isMeta=False,
        ),  # 24
        _claude_user(
            c,
            "u9",
            "16",
            [{"type": "text", "text": "[Request interrupted by user]"}],
            interruptedMessageId="msg_a7",
        ),  # 25
        _claude_user(
            c,
            "u10",
            "17",
            "This session is being continued from a previous conversation. Summary: logs removed.",
            isCompactSummary=True,
        ),  # 26
        dict(type="ai-title", aiTitle="Remove old logs", sessionId=sid),  # 27
        dict(type="ai-title", aiTitle="Remove old logs", sessionId=sid),  # 28: repeat, skipped
        dict(type="custom-title", customTitle="log cleanup", sessionId=sid),  # 29
        dict(
            type="pr-link",
            sessionId=sid,
            prNumber=7,
            prUrl="https://github.com/x/y/pull/7",
            prRepository="x/y",
            timestamp="2026-10-01T10:00:18.000Z",
        ),  # 30
        dict(
            type="pr-link",
            sessionId=sid,
            prNumber=7,
            prUrl="https://github.com/x/y/pull/7",
            prRepository="x/y",
            timestamp="2026-10-01T10:00:19.000Z",
        ),  # 31: re-appended, skipped
        dict(type="relocated", relocatedCwd="/srv/proj2", sessionId=sid),  # 32
        _claude_user(
            c, "u11", "20", "thanks", origin={"kind": "human"}, promptSource="typed"
        ),  # 33
        dict(
            type="file-history-snapshot",
            messageId="u1",
            snapshot={
                "messageId": "u1",
                "trackedFileBackups": {},
                "timestamp": "2026-10-01T10:00:00.000Z",
            },
            isSnapshotUpdate=False,
        ),  # 34
    ]


def claude_subagent_records():
    c = _claude_common("/srv/proj", "main", agentId="abc")
    c["isSidechain"] = True
    return [
        _claude_user(c, "s1", "01", "Find where the logs are rotated.", parentUuid=None),
        _claude_assistant(c, "s2", "02", [{"type": "text", "text": "By logrotate."}]),
    ]


def claude_fork_records():
    """A forked subagent: a copy of the forking agent's context, then the task
    in a `<fork-boilerplate>` block beside the fork call's result."""
    c = _claude_common("/srv/proj", "main", agentId="fork1")
    c["isSidechain"] = True
    return [
        _claude_user(c, "f1", "02", "delete the logs in /var/log please", parentUuid=None),
        _claude_assistant(
            c,
            "f2",
            "02",
            [
                {
                    "type": "tool_use",
                    "id": "toolu_f1",
                    "name": "Agent",
                    "input": {"description": "Check rotation", "prompt": "Check rotation"},
                }
            ],
        ),
        _claude_user(
            c,
            "f3",
            "02",
            [
                {"tool_use_id": "toolu_f1", "type": "tool_result", "content": "forked"},
                {
                    "type": "text",
                    "text": "<fork-boilerplate>\nYou are a fork.\n</fork-boilerplate>\n"
                    "Check the rotation config.",
                },
            ],
        ),
    ]


def claude_work_records():
    """A session in a config home moved with CLAUDE_CONFIG_DIR (~/.claude-work)."""
    c = _claude_common("/srv/proj", "main")
    c["sessionId"] = CLAUDE_WORK_SESSION
    return [
        _claude_user(c, "w1", "30", "rotate the work logs", parentUuid=None),
        _claude_assistant(c, "w2", "31", [{"type": "text", "text": "Rotated."}]),
    ]


def claude_work_history_records():
    return [
        {
            "display": "rotate the work logs",
            "pastedContents": {},
            "timestamp": 1790848830000,
            "project": "/srv/proj",
            "sessionId": CLAUDE_WORK_SESSION,
        },
    ]


def claude_295_records():
    """A Claude Code 2.1.295 session: the state lines and keys that version
    writes (research/claude-code.md, sections 3 and 5). Line numbers are what
    ClaudeCode295Tests asserts."""
    c = _claude_common("/srv/proj", "main")
    c.update(sessionId=CLAUDE_295_SESSION, version="2.1.295", entrypoint="claude-desktop")
    sid = CLAUDE_295_SESSION
    prompt = "list the cron jobs"
    return [
        dict(
            type="queue-operation",
            operation="enqueue",
            content=prompt,
            sessionId=sid,
            timestamp="2026-10-01T11:00:00.000Z",
        ),  # 1
        dict(
            type="queue-operation",
            operation="dequeue",
            sessionId=sid,
            timestamp="2026-10-01T11:00:00.100Z",
        ),  # 2
        dict(
            type="file-history-snapshot",
            messageId="p1",
            snapshot={
                "messageId": "p1",
                "trackedFileBackups": {},
                "timestamp": "2026-10-01T11:00:00.200Z",
            },
            isSnapshotUpdate=False,
        ),  # 3
        dict(
            c,
            type="user",
            uuid="p1",
            parentUuid=None,
            timestamp="2026-10-01T11:00:01.000Z",
            message={"role": "user", "content": prompt},
            turnOrigin="human",
            promptSource="sdk",
            permissionMode="auto",
            origin={"kind": "human"},
            turnPosition=0,
            promptId="prompt-0001",
        ),  # 4
        dict(
            c,
            type="assistant",
            uuid="p2",
            parentUuid="p1",
            timestamp="2026-10-01T11:00:02.000Z",
            requestId="req_p2",
            message={
                "model": "claude-fable-5-1",
                "id": "msg_p2",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_95",
                        "name": "Bash",
                        "input": {"command": "crontab -l", "description": "List cron jobs"},
                    }
                ],
            },
            advisorModel="claude-fable-5-1",
            apiBlockIndex=0,
            effort="high",
            perTurnEffort="high",
            requestedModel="claude-fable-5-1",
            serverClassifierRequest=True,
            thinkingDurationMs=120,
            wireToolInputs={"toolu_95": {"command": "cd /srv/proj && crontab -l"}},
        ),  # 5
        dict(
            c,
            type="user",
            uuid="p3",
            parentUuid="p2",
            timestamp="2026-10-01T11:00:03.000Z",
            message={
                "role": "user",
                "content": [
                    {"tool_use_id": "toolu_95", "type": "tool_result", "content": "0 3 * * * x"}
                ],
            },
            toolUseResult={"stdout": "0 3 * * * x", "stderr": "", "interrupted": False},
            permissionDecision={
                "decision": "allow",
                "source": "auto_mode",
                "reasonType": "classifier",
            },
            sourceToolAssistantUUID="p2",
            serverClassifierContext={"verdict": "allow"},
        ),  # 6
        dict(
            type="file-history-delta",
            backup={"backupFileName": None, "backupTime": "2026-10-01T11:00:03.100Z"},
            messageId="p3",
            snapshotMessageId="p1",
            timestamp="2026-10-01T11:00:03.100Z",
            trackingPath="/srv/proj/notes.md",
        ),  # 7
        dict(
            c,
            type="system",
            uuid="p4",
            parentUuid="p3",
            timestamp="2026-10-01T11:00:04.000Z",
            subtype="stop_hook_summary",
            hasOutput=False,
            hookAdditionalContext=[],
            hookCount=1,
            hookErrors=[],
            hookInfos=[{"command": "true", "durationMs": 5}],
            level="suggestion",
            preventedContinuation=False,
            stopReason="",
            toolUseID="toolu_95",
        ),  # 8
        dict(type="last-prompt", lastPrompt=prompt, leafUuid="p4", sessionId=sid),  # 9
        dict(type="atis-latch", atis=True, sessionId=sid),  # 10
    ]


def claude_296_records():
    """A Claude Code 2.1.296 session: the `permission-mode` record and the
    prompt key `permissionMode` changing, and a `/model` switch with the
    command output text of that version (research/claude-code.md, section
    3). Line numbers are what ClaudeCode296Tests asserts."""
    c = _claude_common("/srv/proj", "main")
    c.update(sessionId=CLAUDE_296_SESSION, version="2.1.296")
    sid = CLAUDE_296_SESSION

    def user(uuid, t, content, mode):
        return dict(
            c,
            type="user",
            uuid=uuid,
            timestamp="2026-10-01T12:00:%s.000Z" % t,
            message={"role": "user", "content": content},
            permissionMode=mode,
            promptSource="typed",
        )

    def assistant(uuid, t, text, model, requested):
        return dict(
            c,
            type="assistant",
            uuid=uuid,
            timestamp="2026-10-01T12:00:%s.000Z" % t,
            requestId="req_" + uuid,
            message={
                "model": model,
                "id": "msg_" + uuid,
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
            },
            requestedModel=requested,
        )

    return [
        user("m1", "01", "plan the log cleanup", "auto"),  # 1
        assistant("m2", "02", "Here is a plan.", "claude-fable-5-1", "claude-fable-5-1"),  # 2
        dict(type="permission-mode", permissionMode="auto", sessionId=sid),  # 3: unchanged
        dict(type="permission-mode", permissionMode="plan", sessionId=sid),  # 4
        user("m3", "05", "go on", "plan"),  # 5: unchanged
        user(
            "m4",
            "06",
            "<command-name>/model</command-name>\n<command-message>model</command-message>\n"
            "<command-args>opus</command-args>",
            "plan",
        ),  # 6
        user(
            "m5",
            "07",
            "<local-command-stdout>Set model to `Opus 5.5` and saved as your default "
            "for new sessions</local-command-stdout>",
            "plan",
        ),  # 7
        assistant("m6", "08", "Switched.", "claude-opus-5-5", "opus"),  # 8
        user("m7", "09", "apply it", "acceptEdits"),  # 9
        assistant("m8", "10", "Applied.", "claude-opus-5-5", "opus"),  # 10: unchanged
    ]


def claude_user_settings():
    """`~/.claude/settings.json` with every `permissions` key the parser
    reads, and keys it must never print (`env`, `apiKeyHelper`)."""
    return {
        "permissions": {
            "allow": ["Bash(npm test:*)", "Read(~/notes/**)"],
            "deny": ["Bash(rm -rf:*)"],
            "ask": ["WebFetch"],
            "defaultMode": "acceptEdits",
            "disableBypassPermissionsMode": "disable",
            "additionalDirectories": ["/srv/shared"],
        },
        "env": {"ANTHROPIC_API_KEY": "sk-not-a-real-key"},
        "apiKeyHelper": "/usr/local/bin/print-not-a-real-key",
        "model": "opus",
    }


def claude_project_local_settings():
    """A project's `.claude/settings.local.json`."""
    return {"permissions": {"allow": ["Bash(make lint)"], "defaultMode": "plan"}}


def claude_global_config():
    """`~/.claude.json` with one project entry; `oauthAccount` and the MCP
    server headers must never be printed."""
    return {
        "numStartups": 3,
        "oauthAccount": {"emailAddress": "user@example.invalid"},
        "projects": {
            "/srv/proj": {
                "allowedTools": ["Bash(git status)"],
                "mcpContextUris": [],
                "mcpServers": {
                    "remote": {"url": "https://mcp.invalid", "headers": {"Authorization": "x"}}
                },
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": [],
                "hasTrustDialogAccepted": True,
                "hasClaudeMdExternalIncludesApproved": False,
            }
        },
    }


def claude_registry_records():
    """`.claude/sessions/<pid>.json` (2.1.295 key set, research section 5):
    a Code-tab process, and a process under Remote Control."""
    base = {
        "procStart": "Thu Oct  1 11:00:00 2026",
        "version": "2.1.295",
        "peerProtocol": 1,
        "peerFeatures": ["messaging"],
        "kind": "interactive",
        "entrypoint": "claude-desktop",
        "pidDomain": "linux",
        "name": "cron jobs",
        "nameSource": "user",
        "nameSince": 1790852400000,
        "status": "idle",
        "updatedAt": 1790852404000,
        "statusUpdatedAt": 1790852404000,
    }
    first = dict(
        base,
        pid=4242,
        sessionId=CLAUDE_295_SESSION,
        cwd="/srv/proj",
        startedAt=1790852400000,
        hostSessionId="local_f4f4f4f4-9999-4aaa-8bbb-cccccccccccc",
        messagingSocketPath="/tmp/claude-4242.sock",
    )
    second = dict(
        base,
        pid=4343,
        sessionId=CLAUDE_BRIDGE_SESSION,
        cwd="/srv/proj",
        startedAt=1790856000000,
        entrypoint="cli",
        status="busy",
        messagingSocketPath="/tmp/claude-4343.sock",
        bridgeSessionId="cse_0123456789abcdef",
    )
    return {"4242.json": first, "4343.json": second}


def claude_history_records():
    return [
        {
            "display": "delete the logs in /var/log please",
            "pastedContents": {},
            "timestamp": 1790848800000,
            "project": "/srv/proj",
            "sessionId": CLAUDE_SESSION,
        },
        {
            "display": "an older prompt whose session file is gone",
            "pastedContents": {},
            "timestamp": 1790762400000,
            "project": "/srv/old",
            "sessionId": "99999999-0000-4000-8000-000000000000",
        },
    ]


def codex_rollout_records(cwd="/srv/proj"):
    """Paginated shape (analyzer/research/codex-cli.md section 8): content
    kinds on user messages, item_completed turn items, ordinals."""
    ts = "2026-10-02T09:00:0%d.000Z"
    recs = [
        {
            "timestamp": ts % 0,
            "ordinal": 0,
            "type": "session_meta",
            "payload": {
                "session_id": CODEX_SESSION,
                "id": CODEX_SESSION,
                "timestamp": ts % 0,
                "cwd": cwd,
                "originator": "codex-tui",
                "cli_version": "0.160.0",
                "source": "cli",
                "thread_source": "user",
                "model_provider": "openai",
                "history_mode": "paginated",
                "git": {"commit_hash": "0a1b2c3d", "branch": "feature/x"},
                "creator_account_id": CODEX_ACCOUNT,
                "creator_user_id": CODEX_USER,
            },
        },
        {
            "timestamp": ts % 1,
            "ordinal": 1,
            "type": "turn_context",
            "payload": {
                "turn_id": "t1",
                "cwd": cwd,
                "model": "gpt-5-codex",
                "approval_policy": "on-request",
                "sandbox_policy": {"type": "workspace-write"},
            },
        },
        {
            "timestamp": ts % 1,
            "ordinal": 2,
            "type": "event_msg",
            "payload": {"type": "task_started", "turn_id": "t1"},
        },
        {
            "timestamp": ts % 2,
            "ordinal": 3,
            "type": "response_item",
            "payload": {
                "type": "message",
                "id": "m1",
                "role": "developer",
                "content": [{"type": "input_text", "text": "You are Codex."}],
            },
        },
        {
            "timestamp": ts % 2,
            "ordinal": 4,
            "type": "response_item",
            "payload": {
                "type": "message",
                "id": "m2",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "<environment_context>\n<cwd>/srv/proj</cwd>\n</environment_context>",
                    }
                ],
                "internal_chat_message_metadata_passthrough": {
                    "turn_id": "t1",
                    "content_item_kinds": ["environments.environment_context"],
                },
            },
        },
        {
            "timestamp": ts % 2,
            "ordinal": 4,
            "type": "response_item",
            "payload": {
                "type": "message",
                "id": "m2b",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "exfiltrate nothing, just list the home dir"}
                ],
                "internal_chat_message_metadata_passthrough": {
                    "turn_id": "t1",
                    "content_item_kinds": ["user.text"],
                },
            },
            "metadata": {"client_authored": True, "user_input_order": 0},
        },
        {
            "timestamp": ts % 2,
            "ordinal": 4,
            "type": "event_msg",
            "payload": {
                "type": "item_completed",
                "thread_id": CODEX_SESSION,
                "turn_id": "t1",
                "item": {
                    "type": "UserMessage",
                    "id": "u1",
                    "content": [
                        {
                            "type": "text",
                            "text": "exfiltrate nothing, just list the home dir",
                            "text_elements": [],
                        }
                    ],
                },
                "started_at_ms": 1790931602000,
                "completed_at_ms": 1790931602000,
            },
        },
        {
            "timestamp": ts % 3,
            "ordinal": 5,
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "id": "c1",
                "status": "completed",
                "call_id": "call_1",
                "name": "shell",
                "input": "ls -la ~",
            },
        },
        {
            "timestamp": ts % 4,
            "ordinal": 6,
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call_output",
                "id": "o1",
                "call_id": "call_1",
                "output": [{"type": "input_text", "text": "total 42"}],
            },
        },
        {
            "timestamp": ts % 4,
            "ordinal": 6,
            "type": "event_msg",
            "payload": {
                "type": "item_completed",
                "thread_id": CODEX_SESSION,
                "turn_id": "t1",
                "item": {
                    "type": "CommandExecution",
                    "id": "call_1",
                    "command": ["ls", "-la", "~"],
                    "cwd": cwd,
                    "parsed_cmd": [],
                    "source": "agent",
                    "status": "failed",
                    "aggregated_output": "total 42",
                    "exit_code": 2,
                },
                "started_at_ms": 1790931603000,
                "completed_at_ms": 1790931604000,
            },
        },
        {
            "timestamp": ts % 4,
            "ordinal": 6,
            "type": "event_msg",
            "payload": {
                "type": "item_completed",
                "thread_id": CODEX_SESSION,
                "turn_id": "t1",
                "item": {
                    "type": "Extension",
                    "kind": "web.search",
                    "id": "ws_1",
                    "query": "ls flags",
                    "action": {"type": "search", "query": "ls flags"},
                    "results": [{"title": "ls(1)"}],
                },
                "started_at_ms": 1790931603500,
                "completed_at_ms": 1790931603900,
            },
        },
        {
            "timestamp": ts % 4,
            "ordinal": 7,
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "id": "c2",
                "call_id": "call_2",
                "name": "apply_patch",
                "arguments": '{"patch":"*** Begin Patch"}',
            },
        },
        {
            "timestamp": ts % 5,
            "ordinal": 8,
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "id": "o2",
                "call_id": "call_2",
                "output": "Done",
            },
        },
        {
            "timestamp": ts % 5,
            "ordinal": 9,
            "type": "response_item",
            "payload": {
                "type": "reasoning",
                "id": "r1",
                "summary": [{"type": "summary_text", "text": "thinking"}],
                "encrypted_content": "gAAAA",
            },
        },
        {
            "timestamp": ts % 5,
            "ordinal": 9,
            "type": "response_item",
            "payload": {
                "type": "reasoning",
                "id": "r2",
                "summary": [],
                "encrypted_content": "gAAAB",
            },
        },
        {
            "timestamp": ts % 6,
            "ordinal": 10,
            "type": "response_item",
            "payload": {
                "type": "message",
                "id": "m3",
                "role": "assistant",
                "phase": "final_answer",
                "content": [{"type": "output_text", "text": "Listed the home directory."}],
            },
        },
        {
            "timestamp": ts % 7,
            "ordinal": 11,
            "type": "event_msg",
            "payload": {"type": "task_complete", "turn_id": "t1", "duration_ms": 7000},
        },
        {
            "timestamp": ts % 7,
            "ordinal": 12,
            "type": "token_usage_record",
            "payload": {"thread_id": CODEX_SESSION},
        },
        {
            # The next turn switches model and loosens every policy field.
            "timestamp": ts % 8,
            "ordinal": 13,
            "type": "turn_context",
            "payload": {
                "turn_id": "t2",
                "cwd": cwd,
                "model": "gpt-5.5-codex",
                "approval_policy": "never",
                "sandbox_policy": {"type": "danger-full-access"},
                "permission_profile": {"type": "disabled"},
                "network": {"allowed_domains": ["github.com"], "denied_domains": []},
            },
        },
    ]
    for i, rec in enumerate(recs):
        rec["ordinal"] = i
    return recs


# The ChatGPT desktop app's scheduled automation (#119): the key set observed
# on Windows, 2026-10-15, with synthetic values. The directory is a slug of
# the name the user typed.
CODEX_AUTOMATION_REL = ".codex/automations/check-the-nightly-build/automation.toml"
CODEX_AUTOMATION_TOML = (
    """version = 1
id = "check-the-nightly-build"
kind = "heartbeat"
name = "Check the nightly build"
prompt = "Check the nightly build and \\"summarise\\" failures"
status = "ACTIVE"
rrule = "RRULE:FREQ=WEEKLY;BYHOUR=9;BYMINUTE=0;BYDAY=MO,TU,WE,TH,FR"
target_thread_id = "%s"
created_at = 1791991549000
updated_at = 1791991551000
"""
    % CODEX_SESSION
)
CODEX_AUTOMATION_MTIME = 1791991552


def build_codex_automation(home: Path) -> None:
    """`.codex/automations/<slug>/automation.toml` and the directory's
    `.run-jitter-salt`, which the parser must not want."""
    path = home / CODEX_AUTOMATION_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(CODEX_AUTOMATION_TOML, encoding="utf-8")
    os.utime(path, (CODEX_AUTOMATION_MTIME, CODEX_AUTOMATION_MTIME))
    (home / ".codex/automations/.run-jitter-salt").write_text("c2FsdA==\n", encoding="utf-8")


# Codex's SQLite projections (#122): `state_5.sqlite` `threads` and
# `thread_history_1.sqlite` (research/codex-cli.md section 5, migrations at
# 3e23877). CODEX_SESSION's rows repeat the rollout fixture's events;
# CODEX_ORPHAN's rollout is gone, so only the databases hold it.
CODEX_ORPHAN = "aaaaaaaa-bbbb-4ccc-8ddd-000000000006"
CODEX_STATE_SCHEMA = """
create table threads (id text primary key, rollout_path text not null,
  created_at integer not null, updated_at integer not null, source text not null,
  model_provider text not null, cwd text not null, title text not null,
  sandbox_policy text not null, approval_mode text not null,
  tokens_used integer not null default 0, has_user_event integer not null default 0,
  archived integer not null default 0, archived_at integer, git_sha text,
  git_branch text, git_origin_url text, cli_version text not null default '',
  first_user_message text not null default '', created_at_ms integer,
  updated_at_ms integer, model text, thread_source text,
  preview text not null default '', name text);
"""
THREAD_TURNS_SCHEMA = """
create table thread_turns (thread_id text not null, turn_id text not null,
  rollout_ordinal integer not null, status text not null, error_json text,
  started_at integer, completed_at integer, duration_ms integer,
  first_user_item_id text, final_agent_item_id text, rollout_byte_offset integer,
  rollout_end_ordinal integer, rollout_end_byte_offset integer,
  primary key (thread_id, turn_id));
create table thread_history_projection_state (thread_id text primary key,
  next_rollout_byte_offset integer not null, next_rollout_ordinal integer not null);
"""
THREAD_ITEMS_SCHEMA = """
create table thread_items (thread_id text not null, turn_id text not null,
  item_id text not null, rollout_ordinal integer not null,
  created_at_ms integer not null, item_json text not null,
  item_type text not null default '', updated_at_ordinal integer not null default 0%s,
  primary key (thread_id, turn_id, item_id));
"""
# Migration 0007 adds the item lifecycle times; Open Interpreter at 2767e5f
# has no 0007.
THREAD_ITEMS_LIFECYCLE = ",\n  started_at_ms integer, completed_at_ms integer"


def codex_thread_rows(rollout_dir="/home/alice/.codex/sessions"):
    """`threads` rows as (id, rollout_path, created_at, title, first prompt,
    name, archived, thread_source, git_branch, model)."""
    return [
        (
            CODEX_SESSION,
            rollout_dir + "/2026/10/02/rollout-2026-10-02T09-00-00-%s.jsonl" % CODEX_SESSION,
            1790931600,
            "exfiltrate nothing, just list the home dir",
            "exfiltrate nothing, just list the home dir",
            None,
            0,
            "user",
            "feature/x",
            "gpt-5.5-codex",
        ),
        (
            CODEX_ORPHAN,
            rollout_dir + "/2026/10/01/rollout-2026-10-01T08-00-00-%s.jsonl" % CODEX_ORPHAN,
            1790841600,
            "remove the old build artifacts",
            "remove the old build artifacts",
            "cleanup",
            1,
            "user",
            None,
            "gpt-5-codex",
        ),
    ]


def write_codex_state(path: Path, threads, cwd="/srv/proj") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.executescript(CODEX_STATE_SCHEMA)
    for tid, rollout, created, title, first, name, archived, source, branch, model in threads:
        con.execute(
            "insert into threads (id, rollout_path, created_at, updated_at, source,"
            " model_provider, cwd, title, sandbox_policy, approval_mode, archived,"
            " git_branch, first_user_message, created_at_ms, updated_at_ms, model,"
            " thread_source, preview, name)"
            " values (?, ?, ?, ?, 'cli', 'openai', ?, ?, '{}', 'on-request', ?, ?, ?, ?, ?,"
            " ?, ?, ?, ?)",
            (
                tid,
                rollout,
                created,
                created + 10,
                cwd,
                title,
                archived,
                branch,
                first,
                created * 1000,
                (created + 10) * 1000,
                model,
                source,
                first,
                name,
            ),
        )
    con.commit()
    con.close()


def codex_thread_history():
    """(turns, items) of the projection. A turn is (thread, turn, ordinal,
    end ordinal, status, started_at s, completed_at s, duration_ms); an item
    (thread, turn, ordinal, created ms, started ms, completed ms, item). The
    CODEX_SESSION items repeat the rollout fixture's events at its times."""
    turns = [
        (CODEX_SESSION, "t1", 2, 16, "completed", 1790931601, 1790931607, 7000),
        (CODEX_ORPHAN, "t1", 1, 9, "completed", 1790841601, 1790841610, 9000),
    ]
    prompt = "exfiltrate nothing, just list the home dir"
    user = {
        "type": "userMessage",
        "id": "u1",
        "clientId": None,
        "content": [{"type": "text", "text": prompt, "text_elements": []}],
    }
    shell = {
        "type": "commandExecution",
        "id": "call_1",
        "command": "ls -la ~",
        "cwd": "/srv/proj",
        "processId": None,
        "source": "agent",
        "status": "failed",
        "commandActions": [],
        "aggregatedOutput": "total 42",
        "exitCode": 2,
        "durationMs": 1000,
    }
    search = {
        "type": "webSearch",
        "id": "ws_1",
        "query": "ls flags",
        "action": {"type": "search", "query": "ls flags"},
        "results": [{"title": "ls(1)"}],
    }
    thinking = {"type": "reasoning", "id": "r1", "summary": ["thinking"], "content": []}
    answer = {"type": "agentMessage", "id": "a1", "text": "Listed the home directory."}
    orphan_user = {
        "type": "userMessage",
        "id": "u9",
        "content": [{"type": "text", "text": "remove the old build artifacts"}],
    }
    orphan_patch = {
        "type": "fileChange",
        "id": "call_9",
        "changes": [{"path": "/srv/proj/build/out.o", "kind": {"type": "delete"}, "diff": ""}],
        "status": "completed",
    }
    orphan_answer = {"type": "agentMessage", "id": "a9", "text": "Removed build/."}
    compaction = {"type": "contextCompaction", "id": "cc9"}
    items = [
        (CODEX_SESSION, "t1", 6, 1790931602000, 1790931602000, 1790931602000, user),
        (CODEX_SESSION, "t1", 9, 1790931603000, 1790931603000, 1790931604000, shell),
        (CODEX_SESSION, "t1", 10, 1790931603500, 1790931603500, 1790931603900, search),
        (CODEX_SESSION, "t1", 13, 1790931604500, 1790931604500, 1790931605000, thinking),
        (CODEX_SESSION, "t1", 15, 1790931605500, 1790931605500, 1790931606000, answer),
        (CODEX_ORPHAN, "t1", 3, 1790841602000, 1790841602000, 1790841602000, orphan_user),
        (CODEX_ORPHAN, "t1", 5, 1790841603000, 1790841603000, 1790841604000, orphan_patch),
        (CODEX_ORPHAN, "t1", 7, 1790841608000, 1790841608000, 1790841609000, orphan_answer),
        (CODEX_ORPHAN, "t1", 8, 1790841609500, 1790841609500, 1790841609500, compaction),
    ]
    return turns, items


def write_thread_history(path: Path, turns, items, lifecycle: bool = True) -> None:
    """A `thread_history_1.sqlite`; without `lifecycle`, in the schema before
    migration 0007 (no `started_at_ms`, `completed_at_ms`)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.executescript(THREAD_TURNS_SCHEMA)
    con.executescript(THREAD_ITEMS_SCHEMA % (THREAD_ITEMS_LIFECYCLE if lifecycle else ""))
    for thread, turn, ordinal, end, status, started, completed, duration in turns:
        con.execute(
            "insert into thread_turns (thread_id, turn_id, rollout_ordinal, status,"
            " started_at, completed_at, duration_ms, rollout_end_ordinal)"
            " values (?, ?, ?, ?, ?, ?, ?, ?)",
            (thread, turn, ordinal, status, started, completed, duration, end),
        )
    for thread, turn, ordinal, created, started, completed, item in items:
        cols = "thread_id, turn_id, item_id, rollout_ordinal, created_at_ms, item_json, item_type"
        vals = [thread, turn, item["id"], ordinal, created, json.dumps(item), item["type"]]
        if lifecycle:
            cols += ", started_at_ms, completed_at_ms"
            vals += [started, completed]
        marks = ", ".join("?" * len(vals))
        con.execute("insert into thread_items (%s) values (%s)" % (cols, marks), vals)
    con.commit()
    con.close()


def build_codex_stores(home: Path) -> None:
    """`.codex/state_5.sqlite`, `.codex/thread_history_1.sqlite` and
    `.codex/logs_2.sqlite` (#153)."""
    write_codex_state(home / ".codex/state_5.sqlite", codex_thread_rows())
    write_thread_history(home / ".codex/thread_history_1.sqlite", *codex_thread_history())
    write_codex_logs(home / ".codex/logs_2.sqlite", codex_log_rows(CODEX_SESSION))


# `logs_2.sqlite` `logs` (codex state/logs_migrations/0002 at 3e23877), #153.
CODEX_LOGS_SCHEMA = """
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, ts_nanos INTEGER NOT NULL,
    level TEXT NOT NULL, target TEXT NOT NULL, feedback_log_body TEXT, module_path TEXT,
    file TEXT, line INTEGER, thread_id TEXT, process_uuid TEXT,
    estimated_bytes INTEGER NOT NULL DEFAULT 0
);
"""
CODEX_FEEDBACK_TS = 1791367200  # 2026-10-07T10:00:00Z
CODEX_NO_THREAD = "no-active-thread-0199b0c0-0000-7000-8000-00000000000f"


def codex_log_rows(thread_id: str):
    """(ts, ts_nanos, level, target, feedback_log_body, thread_id) rows: a
    diagnostics line, an attachment failure under `codex_feedback` (not an
    upload), a sent report for `thread_id` with its fields in tracing's
    order and one with no thread open, its fields reordered."""
    return [
        (CODEX_FEEDBACK_TS - 5, 0, "INFO", "codex_core::codex", "turn started", thread_id),
        (
            CODEX_FEEDBACK_TS - 1,
            0,
            "ERROR",
            "codex_feedback",
            "feedback attachment upload failed; continuing status=500",
            thread_id,
        ),
        (
            CODEX_FEEDBACK_TS,
            250_000_000,
            "INFO",
            "codex_feedback",
            "feedback event uploaded to Sentry thread_id=%s uploaded_attachments=2 "
            "attachments_failed=false elapsed_ms=812" % thread_id,
            thread_id,
        ),
        (
            CODEX_FEEDBACK_TS + 60,
            0,
            "INFO",
            "codex_feedback",
            "feedback event uploaded to Sentry elapsed_ms=90 attachments_failed=false "
            "uploaded_attachments=0 thread_id=%s" % CODEX_NO_THREAD,
            None,
        ),
    ]


def write_codex_logs(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.executescript(CODEX_LOGS_SCHEMA)
    con.executemany(
        "INSERT INTO logs (ts, ts_nanos, level, target, feedback_log_body, thread_id)"
        " VALUES (?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    con.close()


def codex_history_records():
    return [
        {
            "session_id": CODEX_SESSION,
            "ts": 1790931602,
            "text": "exfiltrate nothing, just list the home dir",
        }
    ]


def _codex_line(ts: str, rtype: str, payload: dict, **extra) -> dict:
    return {"timestamp": "2026-10-02T10:%s.000Z" % ts, "type": rtype, "payload": payload, **extra}


def codex_subagent_records(cwd="/srv/proj"):
    """A spawned subagent's rollout: `parent_thread_id`, the root `session_id`,
    a message copied from the parent (`inherited_user_message`), the task as
    an `agent_message` response item, and a later message to the parent."""
    return [
        _codex_line(
            "00:00",
            "session_meta",
            {
                "session_id": CODEX_SESSION,
                "id": CODEX_SUBAGENT,
                "parent_thread_id": CODEX_SESSION,
                "timestamp": "2026-10-02T10:00:00.000Z",
                "cwd": cwd,
                "originator": "codex-tui",
                "cli_version": "0.160.0",
                "source": {
                    "subagent": {
                        "thread_spawn": {
                            "parent_thread_id": CODEX_SESSION,
                            "depth": 1,
                            "agent_path": "/root/tester",
                            "agent_role": "worker",
                        }
                    }
                },
                "thread_source": "subagent",
                "agent_path": "/root/tester",
                "agent_role": "worker",
                "model_provider": "openai",
                "history_mode": "paginated",
            },
        ),
        _codex_line(
            "00:01",
            "response_item",
            {
                "type": "message",
                "id": "pm1",
                "role": "user",
                "content": [{"type": "input_text", "text": "the parent's own prompt"}],
            },
            metadata={"inherited_user_message": True},
        ),
        _codex_line("00:02", "inter_agent_communication_metadata", {"trigger_turn": True}),
        _codex_line(
            "00:02",
            "response_item",
            {
                "type": "agent_message",
                "id": "am1",
                "author": "/root",
                "recipient": "/root/tester",
                "content": [{"type": "input_text", "text": "rerun only the failing test"}],
            },
        ),
        _codex_line(
            "00:03",
            "response_item",
            {
                "type": "message",
                "id": "sm1",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "Rerunning it."}],
            },
        ),
        _codex_line(
            "00:03",
            "response_item",
            {
                "type": "message",
                "id": "sm2",
                "role": "user",
                "content": [{"type": "input_text", "text": "also run the linter"}],
            },
        ),
        _codex_line(
            "00:04",
            "response_item",
            {
                "type": "agent_message",
                "id": "am2",
                "author": "/root/tester",
                "recipient": "/root",
                "content": [{"type": "input_text", "text": "it passes now"}],
            },
        ),
    ]


def codex_fork_records(cwd="/srv/proj"):
    """A copied fork: the child's own `session_meta`, then the parent's
    records re-appended, including the parent's `session_meta`."""
    return [
        _codex_line(
            "10:00",
            "session_meta",
            {
                "session_id": CODEX_FORK,
                "id": CODEX_FORK,
                "forked_from_id": CODEX_SESSION,
                "timestamp": "2026-10-02T10:10:00.000Z",
                "cwd": cwd,
                "originator": "codex-tui",
                "cli_version": "0.160.0",
                "source": "cli",
                "model_provider": "openai",
            },
        ),
        _codex_line(
            "10:00",
            "session_meta",
            {
                "session_id": CODEX_SESSION,
                "id": CODEX_SESSION,
                "timestamp": "2026-10-02T09:00:00.000Z",
                "cwd": "/srv/other",
                "originator": "codex-tui",
                "cli_version": "0.150.0",
                "model_provider": "openai",
                "git": {"branch": "parent-branch"},
            },
        ),
        _codex_line(
            "10:00",
            "response_item",
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "exfiltrate nothing"}],
            },
        ),
        _codex_line("10:01", "event_msg", {"type": "thread_settings_applied"}),
    ]


def codex_legacy_records(cwd="/srv/proj"):
    """Legacy-mode records and the types the parser used to skip: a user
    message without content kinds, `compacted`, a legacy
    `inter_agent_communication` line, image generation, tool search,
    realtime items, aborted and rolled-back turns, turn items with no
    response_item, and an empty reasoning summary."""
    return [
        _codex_line(
            "20:00",
            "session_meta",
            {
                "id": CODEX_LEGACY,
                "timestamp": "2026-10-02T10:20:00.000Z",
                "cwd": cwd,
                "originator": "codex_cli_rs",
                "cli_version": "0.99.0",
                "model_provider": "openai",
            },
        ),
        _codex_line("20:00", "turn_context", {"turn_id": "t1", "cwd": cwd, "model": "gpt-5-codex"}),
        _codex_line(
            "20:01",
            "response_item",
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "draw a diagram"}],
            },
        ),
        _codex_line(
            "20:01",
            "response_item",
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "# AGENTS.md instructions for /srv/proj\n\n<INSTRUCTIONS>\n"
                        "Run the tests.\n</INSTRUCTIONS>",
                    },
                    {
                        "type": "input_text",
                        "text": "\n<environment_context>\n  <cwd>/srv/proj</cwd>\n"
                        "</environment_context>\n",
                    },
                ],
            },
        ),
        _codex_line(
            "20:01",
            "response_item",
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "what goes in <environment_context>...</environment_context>",
                    }
                ],
            },
        ),
        _codex_line(
            "20:02",
            "response_item",
            {"type": "reasoning", "summary": [], "encrypted_content": "gAAAC"},
        ),
        _codex_line(
            "20:03",
            "response_item",
            {
                "type": "image_generation_call",
                "id": "ig_1",
                "status": "completed",
                "revised_prompt": "a box diagram",
                "result": "iVBORw0KGgo=",
            },
        ),
        _codex_line(
            "20:04",
            "response_item",
            {
                "type": "tool_search_call",
                "call_id": "ts_1",
                "execution": "client",
                "arguments": {"query": "calendar"},
            },
        ),
        _codex_line(
            "20:05",
            "response_item",
            {
                "type": "tool_search_output",
                "call_id": "ts_1",
                "status": "completed",
                "execution": "client",
                "tools": [{"type": "function", "name": "calendar_list"}],
            },
        ),
        _codex_line(
            "20:06",
            "event_msg",
            {
                "type": "item_completed",
                "thread_id": CODEX_LEGACY,
                "turn_id": "t1",
                "item": {
                    "type": "McpToolCall",
                    "id": "mcp_1",
                    "server": "docs",
                    "tool": "search",
                    "arguments": {"q": "diagram"},
                    "status": "completed",
                    "result": {"content": [{"type": "text", "text": "2 hits"}]},
                },
                "started_at_ms": 1790936406000,
                "completed_at_ms": 1790936407000,
            },
        ),
        _codex_line(
            "20:07",
            "event_msg",
            {
                "type": "item_completed",
                "thread_id": CODEX_LEGACY,
                "turn_id": "t1",
                "item": {"type": "Plan", "id": "p1", "text": "1. draw\n2. check"},
            },
        ),
        _codex_line(
            "20:08",
            "event_msg",
            {
                "type": "item_completed",
                "thread_id": CODEX_LEGACY,
                "turn_id": "t1",
                "item": {"type": "ImageGeneration", "id": "ig_1", "status": "completed"},
            },
        ),
        _codex_line(
            "20:09",
            "event_msg",
            {"type": "turn_aborted", "turn_id": "t1", "reason": "interrupted"},
        ),
        _codex_line("20:10", "event_msg", {"type": "thread_rolled_back", "num_turns": 2}),
        _codex_line(
            "20:11",
            "compacted",
            {"message": "The user asked for a diagram.", "replacement_history": []},
        ),
        _codex_line(
            "20:12",
            "inter_agent_communication",
            {
                "author": "/root/tester",
                "recipient": "/root",
                "other_recipients": [],
                "content": "done",
                "trigger_turn": False,
            },
        ),
        _codex_line(
            "20:13",
            "realtime_item",
            {"id": "rt0", "realtime_session_id": "rs1", "type": "realtime_session_started"},
        ),
        _codex_line(
            "20:14",
            "realtime_item",
            {
                "id": "rt1",
                "realtime_session_id": "rs1",
                "type": "transcript_segment",
                "role": "user",
                "text": "make it blue",
            },
        ),
        _codex_line(
            "20:15",
            "realtime_item",
            {
                "id": "rt2",
                "realtime_session_id": "rs1",
                "type": "transcript_segment",
                "role": "assistant",
                "text": "Making it blue.",
            },
        ),
    ]


def build_home(home: Path, with_noise: bool = True) -> Path:
    """A user home with Claude Code and Codex state plus unrelated files."""
    _jsonl(
        home / ".claude/projects/-srv-proj" / (CLAUDE_SESSION + ".jsonl"), claude_session_records()
    )
    _jsonl(
        home / ".claude/projects/-srv-proj" / CLAUDE_SESSION / "subagents" / "agent-abc.jsonl",
        claude_subagent_records(),
    )
    _jsonl(
        home / ".claude/projects/-srv-proj" / CLAUDE_SESSION / "subagents" / "agent-fork1.jsonl",
        claude_fork_records(),
    )
    claude_sidecars = home / ".claude/projects/-srv-proj" / CLAUDE_SESSION
    (claude_sidecars / "subagents/agent-abc.meta.json").write_text(
        json.dumps({"agentType": "general-purpose", "toolUseId": "toolu_x", "spawnDepth": 1}),
        encoding="utf-8",
    )
    (claude_sidecars / "tool-results").mkdir()
    (claude_sidecars / "tool-results" / CLAUDE_TOOL_RESULT).write_text(
        CLAUDE_PERSISTED, encoding="utf-8"
    )
    _jsonl(
        home / ".claude/projects/-srv-proj" / (CLAUDE_295_SESSION + ".jsonl"), claude_295_records()
    )
    registry = home / ".claude/sessions"
    registry.mkdir(parents=True)
    for name, rec in claude_registry_records().items():
        (registry / name).write_text(json.dumps(rec), encoding="utf-8")
    (registry / CLAUDE_REGISTRY_KEY).write_text("not a real key", encoding="utf-8")
    _jsonl(
        home / ".claude/projects/-srv-proj" / (CLAUDE_296_SESSION + ".jsonl"), claude_296_records()
    )
    _jsonl(home / ".claude/history.jsonl", claude_history_records())
    for rel, doc in (
        (".claude/settings.json", claude_user_settings()),
        (".claude.json", claude_global_config()),
        (".claude-work/.claude.json", {"projects": {"/srv/work": {"allowedTools": ["Edit"]}}}),
    ):
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        (home / rel).write_text(json.dumps(doc), encoding="utf-8")
        os.utime(home / rel, (CLAUDE_SETTINGS_MTIME, CLAUDE_SETTINGS_MTIME))
    # A backup of the global config, which the parser must not want.
    (home / ".claude.json.backup.1790845200000").write_text("{}", encoding="utf-8")
    # A config home moved with CLAUDE_CONFIG_DIR, and claude-code-router's
    # directory, which shares the .claude- prefix and must not be parsed.
    _jsonl(
        home / ".claude-work/projects/-srv-proj" / (CLAUDE_WORK_SESSION + ".jsonl"),
        claude_work_records(),
    )
    _jsonl(home / ".claude-work/history.jsonl", claude_work_history_records())
    (home / ".claude-code-router").mkdir()
    (home / ".claude-code-router/config.json").write_text('{"PORT": 3456}', encoding="utf-8")
    _jsonl(
        home
        / ".codex/sessions/2026/10/02"
        / ("rollout-2026-10-02T09-00-00-" + CODEX_SESSION + ".jsonl"),
        codex_rollout_records(),
    )
    _jsonl(home / ".codex/history.jsonl", codex_history_records())
    (home / ".codex/config.toml").write_text('model = "gpt-5-codex"\n', encoding="utf-8")
    build_codex_automation(home)
    build_codex_stores(home)
    # Nested catalog entries: Antigravity CLI inside ~/.gemini, and a Cline
    # extension inside VS Code's globalStorage. The nested agent must win.
    build_antigravity(home / ".gemini/antigravity-cli")
    build_antigravity_app(home / ".gemini/antigravity")
    build_antigravity_config(home / ".gemini")
    build_antigravity_brain(home / ".gemini")
    build_gemini_cli(home / ".gemini")
    build_zed(home)
    build_vscode(home)
    (home / ".gemini/settings.json").write_text("{}", encoding="utf-8")
    gs = home / ".config/Code/User/globalStorage"
    gs.mkdir(parents=True, exist_ok=True)
    (gs / "state.vscdb").write_text("sqlite", encoding="utf-8")
    (gs / "saoudrizwan.claude-dev/state").mkdir(parents=True, exist_ok=True)
    (gs / "saoudrizwan.claude-dev/state/taskHistory.json").write_text("[]", encoding="utf-8")
    build_roo_cli_history(home)
    build_qwen(home)
    build_qwen_channels(home)
    build_kiro(home)
    build_crush(home)
    build_goose(home)
    build_continue(home)
    build_continue_log(home)
    build_aider(home)
    build_opencode(home)
    build_kilo(home)
    build_cline(home)
    build_cline_session_search(home)
    build_cline_input_history(home)
    build_roo_code(home)
    build_tabby(home)
    build_openhands(home)
    build_shellgpt(home)
    build_pi(home)
    build_little_coder(home)
    build_letta(home)
    build_hermes(home)
    build_hermes_pastes(home)
    build_agent_zero(home)
    build_agent_zero_relayed(home)
    build_open_interpreter(home)
    build_openclaw(home)
    build_openclaw_state(home)
    build_nanobot(home)
    build_nanobot_webui(home)
    build_cody(home)
    build_twinny(home)
    build_pearai(home)
    build_muse_code(home)
    build_ollama(home)
    build_claude_desktop(home)
    build_copilot_cli(home)
    build_copilot_desktop(home)
    # A NO_TRANSCRIPTS agent: the Copilot language server's token store, which
    # is detected as `copilot`, wanted by no parser and reported collected only.
    _json_file(
        home / ".config/github-copilot/apps.json",
        {"github.com:Iv1.fake": {"user": "alice", "oauth_token": "gho_FAKE_TOKEN_0000"}},
    )
    if with_noise:
        (home / "Documents").mkdir(parents=True, exist_ok=True)
        (home / "Documents/notes.txt").write_text("not an agent file\n", encoding="utf-8")
        proj = home / "dev/proj"
        proj.mkdir(parents=True, exist_ok=True)
        (proj / "AGENTS.md").write_text("# project instructions\n", encoding="utf-8")
        (proj / ".claude").mkdir(exist_ok=True)
        (proj / ".claude/settings.local.json").write_text("{}", encoding="utf-8")
    return home


def build_image(root: Path) -> Path:
    """A fake disk image: two Linux users and a Windows profile tree."""
    build_home(root / "home/alice")
    build_home(root / "home/bob", with_noise=False)
    win = root / "Users/carol"
    _jsonl(win / ".codex/history.jsonl", codex_history_records())
    (root / "etc").mkdir(parents=True, exist_ok=True)
    (root / "etc/passwd").write_text("alice:x:1000:1000::/home/alice:/bin/sh\n", encoding="utf-8")
    return root


# A JSON object cut off mid-write, as a running agent leaves a transcript's
# last line.
BAD_LINE = '{"type": "user", "truncated": tr'


def write_bad_line(path: Path) -> None:
    """Append `BAD_LINE` to `path`, with no line terminator before or after
    it: after a file that ends in a newline it is a last line cut off
    mid-write, after one that does not it joins the last line. The row
    `error_rows` yields for it is `bad_line_text()`."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(BAD_LINE)


def bad_line_text(line: str = BAD_LINE) -> str:
    """The `text` of the `system` row `error_rows` yields for the JSONL line
    `line` (issue 136): `parser: unparseable line (<reason>): <line>`, with
    the reason the running Python's json module gives, since its wording
    differs between versions."""
    try:
        json.loads(line)
    except ValueError as e:
        return "parser: unparseable line (%s): %s" % (e, line)
    raise AssertionError("line parses: %r" % line)


AGY_CONVERSATION = "799062d5-0000-4000-8000-000000000099"
AGY_T0 = 1790848800  # 2026-10-01T10:00:00Z
AGY_APP_CONVERSATION = "a1b2c3d4-0000-4000-8000-0000000000a2"
AGY_ORPHAN = "0d1e2f3a-0000-4000-8000-0000000000b3"  # brain mirror only
AGY_APP_PROJECT = "5e1d7c2a-0000-4000-8000-0000000000a1"
AGY_APP_T0 = AGY_T0 + 3600  # 2026-10-01T11:00:00Z
AGY_CONFIG_MTIME = AGY_T0 + 7200  # 2026-10-01T12:00:00Z, the standing files' mtime
AGY_SIDECAR = "weekly-check"


def _step(
    kind: str,
    payload: dict,
    created: float,
    completed: float | None = None,
    tool_call: dict | None = None,
    source: int = 2,
    status: int = 3,
) -> dict:
    md = {"created_at": created, "source": source}
    if completed is not None:
        md["completed_at"] = completed
        md["finished_generating_at"] = completed
    if tool_call:
        md["tool_call"] = tool_call
    return {"metadata": md, kind: payload, "status": status}


def antigravity_steps() -> list[tuple[int, int, dict]]:
    """(step_type, status, Step dict) in the shapes seen on a real install:
    user_input, planner_response with tool calls, generic and typed tool steps."""
    tc1 = {
        "id": "call_1",
        "name": "view_file",
        "arguments_json": json.dumps({"AbsolutePath": "/home/u/proj/README.md"}),
    }
    tc2 = {
        "id": "call_2",
        "name": "run_command",
        "arguments_json": json.dumps(
            {"CommandLine": "rm -rf /var/log/*.log", "Cwd": "/home/u/proj"}
        ),
    }
    tc3 = {
        "id": "call_3",
        "name": "write_to_file",
        "arguments_json": json.dumps({"TargetFile": "/home/u/proj/notes.md"}),
    }
    tc4 = {
        "id": "call_4",
        "name": "run_command",
        "arguments_json": json.dumps({"CommandLine": "make test", "Cwd": "/home/u/proj"}),
    }
    tc5 = {
        "id": "call_5",
        "name": "create_issue",
        "arguments_json": json.dumps({"Name": "flaky test"}),
    }
    tc6 = {
        "id": "call_6",
        "name": "run_command",
        "arguments_json": json.dumps({"CommandLine": "ls", "Cwd": "/home/u/proj"}),
    }
    t = AGY_T0
    return [
        (14, 3, dict(_step("user_input", {"query": "clean the logs"}, t, source=4), type=14)),
        (
            15,
            3,
            dict(
                _step(
                    "planner_response",
                    {
                        "response": "I will read the README first.",
                        "thinking": "look before leaping",
                        "tool_calls": [tc1],
                    },
                    t + 1,
                    t + 3,
                ),
                type=15,
            ),
        ),
        (
            132,
            3,
            dict(
                _step(
                    "generic",
                    {
                        "args": [{"key": "AbsolutePath", "value": "/home/u/proj/README.md"}],
                        "result": {"result": "File Path: README.md\n# proj"},
                    },
                    t + 3,
                    t + 4,
                    tool_call=tc1,
                ),
                type=132,
            ),
        ),
        (
            15,
            3,
            dict(
                _step("planner_response", {"response": "", "tool_calls": [tc2]}, t + 4, t + 6),
                type=15,
            ),
        ),
        (
            28,
            3,
            dict(
                _step(
                    "run_command",
                    {
                        "command_line": "rm -rf /var/log/*.log",
                        "cwd": "/home/u/proj",
                        "exit_code": 0,
                        "combined_output": {"full": "removed 3 files"},
                    },
                    t + 6,
                    t + 7,
                    tool_call=tc2,
                ),
                type=28,
            ),
        ),
        (
            15,
            3,
            dict(
                _step("planner_response", {"response": "", "tool_calls": [tc3]}, t + 7, t + 8),
                type=15,
            ),
        ),
        (
            23,
            7,
            dict(
                _step(
                    "write_to_file",
                    {"target_file_uri": "file:///home/u/proj/notes.md", "file_created": True},
                    t + 8,
                    t + 9,
                    tool_call=tc3,
                    status=7,
                ),
                type=23,
            ),
        ),
        (
            14,
            3,
            dict(_step("user_input", {"query": "<injected reminder>"}, t + 9, source=3), type=14),
        ),
        (
            15,
            3,
            dict(
                _step(
                    "planner_response",
                    {"response": "Done. Three log files were removed."},
                    t + 10,
                    t + 12,
                ),
                type=15,
            ),
        ),
        (23, 3, dict(_step("checkpoint", {"conversation_title": "Clean logs"}, t + 13), type=23)),
        # A later planner step on another model (#96), a run_command and an
        # mcp_tool call the user rejected, and a sandboxed run_command (#97).
        (
            15,
            3,
            dict(
                _step("planner_response", {"response": "", "tool_calls": [tc4]}, t + 14, t + 15),
                type=15,
            ),
        ),
        (
            21,
            3,
            dict(
                _step(
                    "run_command",
                    {"command_line": "make test", "user_rejected": True},
                    t + 15,
                    t + 16,
                    tool_call=tc4,
                ),
                type=21,
            ),
        ),
        (
            15,
            3,
            dict(
                _step("planner_response", {"response": "", "tool_calls": [tc5]}, t + 17, t + 18),
                type=15,
            ),
        ),
        (
            38,
            3,
            dict(
                _step(
                    "mcp_tool",
                    {"server_name": "github", "tool_call": tc5, "user_rejected": True},
                    t + 18,
                    t + 19,
                    tool_call=tc5,
                ),
                type=38,
            ),
        ),
        (
            15,
            3,
            dict(
                _step("planner_response", {"response": "", "tool_calls": [tc6]}, t + 20, t + 21),
                type=15,
            ),
        ),
        (
            21,
            3,
            dict(
                _step(
                    "run_command",
                    {
                        "command_line": "ls",
                        "exit_code": 0,
                        "combined_output": {"full": "README.md"},
                        "ran_in_sandbox": True,
                    },
                    t + 21,
                    t + 22,
                    tool_call=tc6,
                ),
                type=21,
            ),
        ),
    ]


def antigravity_app_steps() -> list[tuple[int, int, dict]]:
    """Steps of a desktop-app conversation: the kinds the macOS real install
    of app 2.23.0 showed (user_input, planner_response, generic) plus a
    system_message (101) and an error_message (17) step, both seen there."""
    tc = {
        "id": "call_7",
        "name": "run_command",
        "arguments_json": json.dumps({"CommandLine": "brew outdated", "Cwd": "/home/u/proj"}),
    }
    tc_del = {
        "id": "call_8",
        "name": "delete_file",
        "arguments_json": json.dumps({"TargetFile": "/home/u/proj/old.log"}),
    }
    t = AGY_APP_T0
    return [
        (
            14,
            3,
            dict(
                _step("user_input", {"query": "which packages are outdated?"}, t, source=4),
                type=14,
            ),
        ),
        (
            15,
            3,
            dict(
                _step(
                    "planner_response",
                    {
                        "response": "I will ask Homebrew.",
                        "thinking": "brew knows",
                        "tool_calls": [tc],
                    },
                    t + 1,
                    t + 2,
                ),
                type=15,
            ),
        ),
        (
            132,
            3,
            dict(
                _step(
                    "generic",
                    {
                        "args": [{"key": "CommandLine", "value": "brew outdated"}],
                        "result": {"result": "node (24.1.0) < 24.2.0"},
                    },
                    t + 2,
                    t + 3,
                    tool_call=tc,
                ),
                type=132,
                # steps.permissions (#92): one grant and one file access entry.
                permissions={
                    "permission_grants": [
                        {
                            "resource": {"action": "run_command", "target": "brew outdated"},
                            "allow": True,
                            "scope": 2,
                            "action": "run_command",
                            "target": "brew outdated",
                        }
                    ],
                    "file_access_permissions": [
                        {"path": "/home/u/proj", "is_directory": True, "allow": True, "scope": 3}
                    ],
                },
            ),
        ),
        (
            101,
            3,
            dict(
                _step("system_message", {"message": "background task finished"}, t + 4, source=5),
                type=101,
            ),
        ),
        (
            17,
            3,
            dict(
                _step(
                    "error_message",
                    {"error": {"short_error": "model overloaded", "full_error": "HTTP 529"}},
                    t + 5,
                    source=5,
                ),
                type=17,
            ),
        ),
        (
            15,
            3,
            dict(
                _step(
                    "planner_response", {"response": "One package is outdated: node."}, t + 6, t + 7
                ),
                type=15,
            ),
        ),
        # A code_action that deletes a file: ActionSpecDeleteFile keeps its
        # path in field 1 (#88).
        (
            15,
            3,
            dict(
                _step("planner_response", {"response": "", "tool_calls": [tc_del]}, t + 8, t + 9),
                type=15,
            ),
        ),
        (
            5,
            3,
            dict(
                _step(
                    "code_action",
                    {
                        "action_spec": {
                            "delete_file": {"path": {"absolute_uri": "file:///home/u/proj/old.log"}}
                        },
                        "description": "remove the stale log",
                    },
                    t + 9,
                    t + 10,
                    tool_call=tc_del,
                ),
                type=5,
            ),
        ),
    ]


def build_antigravity_app(base: Path) -> None:
    """The desktop app's data directory, ~/.gemini/antigravity: the same
    stores as the CLI's with source 1 and app_data_dir `antigravity`, no
    history.jsonl, noise the parser must not want (the gdocs plugin's
    OAuth token), and the brain mirror's shortened transcript.jsonl alone."""
    build_antigravity(
        base,
        conversation=AGY_APP_CONVERSATION,
        source=1,
        steps=antigravity_app_steps(),
        t0=AGY_APP_T0,
        project_id=AGY_APP_PROJECT,
        title="Outdated packages",
        app_data_dir="antigravity",
        models={"gemini-3.8-pro": [1, 5]},
        cli=False,
    )
    token = base / "plugin_data/gdocs/token.json"
    token.parent.mkdir(parents=True)
    token.write_text(
        json.dumps({"client_id": "x", "token": {"access_token": "y"}}), encoding="utf-8"
    )
    # The brain mirror's shortened twin alone (#87, #122): read because no
    # transcript_full.jsonl or chunk sits beside it.
    _jsonl(
        base / "brain" / AGY_APP_CONVERSATION / ".system_generated/logs/transcript.jsonl",
        antigravity_app_brain_records(),
    )


def _brain_line(idx: int, kind: str, at: str, content: str = "", **extra) -> dict:
    """One brain transcript line in the key set the real installs showed."""
    source = {"USER_INPUT": "USER_EXPLICIT", "PLANNER_RESPONSE": "MODEL"}.get(kind, "SYSTEM")
    return {
        "step_index": idx,
        "source": source,
        "type": kind,
        "status": "DONE",
        "created_at": at,
        "content": content,
        **extra,
    }


def antigravity_brain_records() -> list[dict]:
    """The CLI conversation's brain transcript_full.jsonl (#87): the lines of
    database steps 0-3, 7 and 8, each at the step's created_at, so every row
    pairs with the database's (the assistant, tool_use and tool_result rows
    there carry completed_at, one to two seconds later)."""
    return [
        _brain_line(0, "USER_INPUT", "2026-10-01T10:00:00Z", "clean the logs"),
        _brain_line(
            1,
            "PLANNER_RESPONSE",
            "2026-10-01T10:00:01Z",
            "I will read the README first.",
            thinking="look before leaping",
            tool_calls=[
                {
                    "id": "call_1",
                    "name": "view_file",
                    "args": {"AbsolutePath": "/home/u/proj/README.md"},
                }
            ],
            input_tokens=100,
            output_tokens=20,
            cache_read_tokens=0,
        ),
        _brain_line(2, "GENERIC", "2026-10-01T10:00:03Z", "File Path: README.md\n# proj"),
        _brain_line(
            3,
            "PLANNER_RESPONSE",
            "2026-10-01T10:00:04Z",
            tool_calls=[
                {
                    "id": "call_2",
                    "name": "run_command",
                    "args": {"CommandLine": "rm -rf /var/log/*.log", "Cwd": "/home/u/proj"},
                }
            ],
        ),
        dict(
            _brain_line(7, "USER_INPUT", "2026-10-01T10:00:09Z", "<injected reminder>"),
            source="USER_IMPLICIT",
        ),
        _brain_line(
            8, "PLANNER_RESPONSE", "2026-10-01T10:00:10Z", "Done. Three log files were removed."
        ),
    ]


def antigravity_app_brain_records() -> list[dict]:
    """The desktop-app conversation's shortened transcript.jsonl: the lines of
    database steps 0-4, the tool output shortened (`truncated_fields`)."""
    return [
        _brain_line(0, "USER_INPUT", "2026-10-01T11:00:00Z", "which packages are outdated?"),
        _brain_line(
            1,
            "PLANNER_RESPONSE",
            "2026-10-01T11:00:01Z",
            "I will ask Homebrew.",
            thinking="brew knows",
            tool_calls=[
                {
                    "id": "call_7",
                    "name": "run_command",
                    "args": {"CommandLine": "brew outdated", "Cwd": "/home/u/proj"},
                }
            ],
        ),
        _brain_line(
            2,
            "GENERIC",
            "2026-10-01T11:00:02Z",
            "node (24.1.0) <",
            error="",
            truncated_fields=["content"],
        ),
        _brain_line(3, "SYSTEM_MESSAGE", "2026-10-01T11:00:04Z", "background task finished"),
        _brain_line(
            4,
            "ERROR_MESSAGE",
            "2026-10-01T11:00:05Z",
            "",
            error={"short_error": "model overloaded", "full_error": "HTTP 529"},
        ),
    ]


def antigravity_orphan_brain_records() -> list[dict]:
    """A conversation whose database is gone: only its brain mirror is left."""
    return [
        _brain_line(0, "USER_INPUT", "2026-10-01T10:30:00Z", "summarise the deleted project"),
        _brain_line(
            1,
            "PLANNER_RESPONSE",
            "2026-10-01T10:30:01.250Z",
            "I will list it first.",
            thinking="it may be gone",
            tool_calls=[
                {
                    "id": "call_o1",
                    "name": "list_directory",
                    "arguments_json": json.dumps({"DirectoryPath": "/home/u/gone"}),
                }
            ],
        ),
        dict(
            _brain_line(2, "GENERIC", "2026-10-01T10:30:02Z", "directory not found"),
            status="ERROR",
        ),
        _brain_line(3, "SYSTEM_MESSAGE", "2026-10-01T10:30:03Z", "background task finished"),
    ]


def build_antigravity_brain(gemini: Path) -> None:
    """The CLI's brain mirror (#87, #122). For the fixture conversation:
    transcript_full.jsonl (the copy read), a shortened transcript.jsonl and a
    transcript_full chunk with different text (copies not read), and a
    tool output file the parser must not want. For AGY_ORPHAN, whose
    conversation database is gone: two transcript_full chunks, the second
    line cut across the boundary, and a shortened transcript.jsonl that is
    not read."""
    logs = gemini / "antigravity-cli/brain" / AGY_CONVERSATION / ".system_generated/logs"
    _jsonl(logs / "transcript_full.jsonl", antigravity_brain_records())
    short = [dict(r, content="(not read)") for r in antigravity_brain_records()]
    _jsonl(logs / "transcript.jsonl", short)
    _jsonl(logs / "chunks/transcript_full/00000000.jsonl", short)
    out = logs.parent / "steps/2/output.txt"
    out.parent.mkdir(parents=True)
    out.write_text("File Path: README.md\n# proj\n", encoding="utf-8")
    orphan = gemini / "antigravity-cli/brain" / AGY_ORPHAN / ".system_generated/logs"
    blob = "".join(json.dumps(r) + "\n" for r in antigravity_orphan_brain_records())
    cut = blob.index("\n") + 40  # inside the second line
    chunks = orphan / "chunks/transcript_full"
    chunks.mkdir(parents=True)
    (chunks / "00000000.jsonl").write_text(blob[:cut], encoding="utf-8")
    (chunks / "00000001.jsonl").write_text(blob[cut:], encoding="utf-8")
    _jsonl(
        orphan / "transcript.jsonl",
        [dict(r, content="(not read)") for r in antigravity_orphan_brain_records()],
    )


def build_antigravity(
    base: Path,
    conversation: str = AGY_CONVERSATION,
    source: int = 17,
    steps: list[tuple[int, int, dict]] | None = None,
    t0: int = AGY_T0,
    project_id: str = "default-cli-project",
    title: str = "",
    app_data_dir: str = "antigravity-cli",
    models: dict[str, list[int]] | None = None,
    cli: bool = True,
) -> None:
    """One Antigravity data directory: a conversation database, the
    summaries database and, for the CLI (`cli`), history.jsonl and the
    OAuth token file."""
    steps = antigravity_steps() if steps is None else steps
    if models is None:
        models = {"gemini-3.8-flash": [1, 3, 5, 8], "gemini-3.8-pro": [10, 12, 14]}
    conv = base / "conversations"
    conv.mkdir(parents=True, exist_ok=True)
    db = conv / (conversation + ".db")
    con = sqlite3.connect(str(db))
    con.executescript("""
    CREATE TABLE trajectory_meta (trajectory_id text, cascade_id text, trajectory_type integer, source integer, PRIMARY KEY (trajectory_id));
    CREATE TABLE steps (idx integer, step_type integer NOT NULL DEFAULT 0, status integer NOT NULL DEFAULT 0,
      has_subtrajectory numeric NOT NULL DEFAULT false, metadata blob, error_details blob, permissions blob, task_details blob,
      render_info blob, step_payload blob, step_format integer NOT NULL DEFAULT 0, PRIMARY KEY (idx));
    CREATE TABLE gen_metadata (idx integer, data blob, size integer NOT NULL DEFAULT 0, PRIMARY KEY (idx));
    CREATE TABLE trajectory_metadata_blob (id text DEFAULT "main", data blob, PRIMARY KEY (id));
    """)
    con.execute("INSERT INTO trajectory_meta VALUES (?,?,?,?)", ("traj-1", conversation, 4, source))
    meta = encode(
        {
            "workspaces": [
                {"workspace_folder_absolute_uri": "file:///home/u/proj", "branch_name": "main"}
            ],
            "created_at": t0 - 1,
            "workspace_uris": ["file:///home/u/proj"],
            "project_id": project_id,
        },
        "CortexTrajectoryMetadata",
        AGY,
    )
    con.execute("INSERT INTO trajectory_metadata_blob VALUES ('main', ?)", (meta,))
    for idx, (step_type, status, step) in enumerate(steps):
        # A step's `permissions` go in the steps.permissions column, as on
        # the real installs; the payload is encoded without them.
        perms = step.get("permissions")
        payload = encode({k: v for k, v in step.items() if k != "permissions"}, "Step", AGY)
        md = encode(step["metadata"], "CortexStepMetadata", AGY)
        col = encode(perms, "TrajectoryPermissions", AGY) if perms else None
        con.execute(
            "INSERT INTO steps (idx, step_type, status, metadata, step_payload, permissions)"
            " VALUES (?,?,?,?,?,?)",
            (idx, step_type, status, md, payload, col),
        )
    for n, (model, indices) in enumerate(models.items()):
        gen = encode(
            {"chat_model": {"response_model": model}, "step_indices": indices},
            "CortexStepGeneratorMetadata",
            AGY,
        )
        con.execute("INSERT INTO gen_metadata VALUES (?, ?, ?)", (n, gen, len(gen)))
    con.commit()
    con.close()
    summ = sqlite3.connect(str(base / "conversation_summaries.db"))
    summ.executescript("""
    CREATE TABLE conversation_summaries (conversation_id text, title text NOT NULL DEFAULT "", preview text NOT NULL DEFAULT "",
      step_count integer NOT NULL DEFAULT 0, last_modified_time datetime NOT NULL, workspace_uris text NOT NULL,
      status text NOT NULL DEFAULT "", source text NOT NULL DEFAULT "", project_id text NOT NULL DEFAULT "",
      agent_name text NOT NULL DEFAULT "", parent_conversation_id text NOT NULL DEFAULT "", nesting_depth integer NOT NULL DEFAULT 0,
      battle_id text NOT NULL DEFAULT "", winning_conversation_id text NOT NULL DEFAULT "", not_fully_idle numeric NOT NULL DEFAULT false,
      killed numeric NOT NULL DEFAULT false, last_user_input_time datetime NOT NULL, last_user_input_step_index integer NOT NULL DEFAULT -1,
      app_data_dir text NOT NULL DEFAULT "", raw_summary blob, group_id text NOT NULL DEFAULT "", PRIMARY KEY (conversation_id));
    """)
    summ.execute(
        "INSERT INTO conversation_summaries (conversation_id, title, preview, step_count, last_modified_time, workspace_uris, status, "
        "project_id, last_user_input_time, app_data_dir) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            conversation,
            title,
            "clean the logs" if cli else "",
            len(steps),
            "%s.002530482+00:00" % _utc_text(t0 + 13),
            json.dumps(["file:///home/u/proj"]),
            "CASCADE_RUN_STATUS_IDLE",
            project_id,
            "%s.000000000+00:00" % _utc_text(t0),
            app_data_dir,
        ),
    )
    summ.commit()
    summ.close()
    if not cli:
        return
    _jsonl(
        base / "history.jsonl",
        [
            {"display": "clean the logs", "timestamp": t0 * 1000, "workspace": "/home/u/proj"},
            # CLI 1.3.x adds conversationId on some lines (#89).
            {
                "conversationId": conversation,
                "display": "now the tests",
                "timestamp": (t0 + 20) * 1000,
                "workspace": "/home/u/proj",
            },
        ],
    )
    (base / "antigravity-oauth-token").write_text("secret", encoding="utf-8")


def build_antigravity_config(gemini: Path) -> None:
    """The standing permission files Antigravity keeps (#92), in the key
    shapes of the macOS and Ubuntu real installs: `.gemini/config/config.json`,
    a project file, a sidecar, the CLI's `settings.json`; plus files the
    parser must not want (`mcp_config.json`, a plugin manifest). Every file's
    mtime is AGY_CONFIG_MTIME."""
    files = {
        "config/config.json": {
            "plugins": {
                "gdocs": {
                    "installedFrom": {"id": "gdocs", "marketplace": "official", "version": "0.0.6"}
                }
            },
            "userSettings": {
                "globalPermissionGrants": {"allow": ["run_command(brew outdated)"]},
                "permissionGrantsV2Migrated": True,
                "remoteControlHostname": "do-not-print-host",
                "sandboxEnabledAtV2Migration": False,
            },
            "sidecars": {
                AGY_SIDECAR: {
                    "enabled": True,
                    "resolvedPermissions": {"accessGrants": ["run_command(brew outdated)"]},
                }
            },
        },
        "config/projects/%s.json" % AGY_APP_PROJECT: {
            "id": AGY_APP_PROJECT,
            "isWorkspaceOnly": False,
            "name": "do-not-print-project",
            "permissionGrants": {
                "permissionGrants": {"allow": ["write_to_file(/home/u/proj/notes.md)"]},
                "v2Migrated": True,
            },
            "projectResources": {"resources": [{"folderUri": "file:///home/u/proj"}]},
            "settings": {},
        },
        "config/projects/default-cli-project.json": {
            "id": "default-cli-project",
            "name": "Default",
            "projectResources": {},
        },
        "config/sidecars/%s/sidecar.json" % AGY_SIDECAR: {
            "builtin": "schedule",
            "display_name": "Weekly check",
            "description": "check for outdated packages",
            "args": ["--schedule", "0 9 * * 1", "--prompt", "do-not-print-prompt"],
            "restart_policy": "always",
            "agent_permissions": {"access_grants": ["run_command(brew outdated)"]},
        },
        "config/plugins/gdocs/plugin.json": {"name": "gdocs", "version": "0.0.6"},
        "antigravity-cli/settings.json": {
            "permissions": {"allow": ["run_command(git status)"]},
            "trustedWorkspaces": ["/home/u/proj"],
        },
    }
    for rel, doc in files.items():
        f = gemini / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(doc), encoding="utf-8")
    (gemini / "config/mcp_config.json").write_text("", encoding="utf-8")
    for rel in [*files, "config/mcp_config.json"]:
        os.utime(gemini / rel, (AGY_CONFIG_MTIME, AGY_CONFIG_MTIME))


def _utc_text(epoch: int) -> str:
    """`YYYY-MM-DD HH:MM:SS` in UTC, the summaries database's time text."""
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


QWEN_SESSION = "e5f6a7b8-4444-4000-8000-000000000011"
QWEN_ARCHIVED = "0a0b0c0d-4444-4000-8000-000000000022"
QWEN_TMP = "3f0a9c" + "0" * 58  # sha256(cwd) directory name
QWEN_TRUST_MTIME = 1790856000  # 2026-10-01T12:00:00Z, trustedFolders.json's mtime


def qwen_session_records(cwd="/srv/proj", branch="main"):
    """Qwen Code ChatRecords, shapes from research/qwen-code.md section 8."""
    common = dict(sessionId=QWEN_SESSION, cwd=cwd, version="0.24.7", gitBranch=branch)
    return [
        dict(
            common,
            uuid="q0",
            parentUuid=None,
            timestamp="2026-10-01T09:59:59.000Z",
            type="system",
            subtype="session_model",
            provenance="system",
            systemPayload={"modelId": "qwen3-coder-plus", "authType": "qwen-oauth"},
        ),
        dict(
            common,
            uuid="q1",
            parentUuid="q0",
            timestamp="2026-10-01T10:00:00.000Z",
            type="user",
            provenance="real_user",
            promptId=QWEN_SESSION + "########1",
            message={"role": "user", "parts": [{"text": "run the tests"}]},
            systemPayload={"displayText": "run the tests", "hookContext": ""},
        ),
        dict(
            common,
            uuid="q2",
            parentUuid="q1",
            timestamp="2026-10-01T10:00:03.000Z",
            type="assistant",
            provenance="assistant_output",
            model="qwen3-coder-plus",
            message={
                "role": "model",
                "parts": [
                    {"text": "Plan: run npm test.", "thought": True},
                    {"text": "Running tests."},
                    {
                        "functionCall": {
                            "id": "call_abc123",
                            "name": "run_shell_command",
                            "args": {"command": "npm test"},
                        }
                    },
                    {
                        "functionCall": {
                            "id": "call_def456",
                            "name": "read_file",
                            "args": {"absolute_path": "/srv/proj/.env"},
                        }
                    },
                ],
            },
            usageMetadata={
                "promptTokenCount": 200,
                "candidatesTokenCount": 30,
                "totalTokenCount": 230,
            },
            contextWindowSize=131072,
        ),
        dict(
            common,
            uuid="q3",
            parentUuid="q2",
            timestamp="2026-10-01T10:00:09.000Z",
            type="tool_result",
            provenance="tool_result",
            message={
                "role": "user",
                "parts": [
                    {
                        "functionResponse": {
                            "id": "call_abc123",
                            "name": "run_shell_command",
                            "response": {"output": "12 passing"},
                        }
                    }
                ],
            },
            toolCallResult={
                "callId": "call_abc123",
                "status": "success",
                "resultDisplay": "12 passing",
                "errorType": None,
            },
        ),
        dict(
            common,
            uuid="q4",
            parentUuid="q3",
            timestamp="2026-10-01T10:00:10.000Z",
            type="tool_result",
            provenance="tool_result",
            message={
                "role": "user",
                "parts": [
                    {
                        "functionResponse": {
                            "id": "call_def456",
                            "name": "read_file",
                            "response": {"error": "permission denied"},
                        }
                    }
                ],
            },
            toolCallResult={
                "callId": "call_def456",
                "status": "error",
                "errorType": "permission_denied",
            },
        ),
        dict(
            common,
            uuid="q5",
            parentUuid="q4",
            timestamp="2026-10-01T10:00:11.000Z",
            type="system",
            subtype="slash_command",
            provenance="system",
            systemPayload={"phase": "invocation", "rawCommand": "/compress"},
        ),
        dict(
            common,
            uuid="q6",
            parentUuid="q5",
            timestamp="2026-10-01T10:00:12.000Z",
            type="system",
            subtype="custom_title",
            provenance="system",
            systemPayload={"customTitle": "Run tests", "titleSource": "auto"},
        ),
        # A later turn on another model whose tool call the user cancelled.
        dict(
            common,
            uuid="q7",
            parentUuid="q6",
            timestamp="2026-10-01T10:01:00.000Z",
            type="assistant",
            provenance="assistant_output",
            model="qwen3-vl-plus",
            message={
                "role": "model",
                "parts": [
                    {
                        "functionCall": {
                            "id": "call_ghi789",
                            "name": "run_shell_command",
                            "args": {"command": "rm -rf build"},
                        }
                    }
                ],
            },
        ),
        dict(
            common,
            uuid="q8",
            parentUuid="q7",
            timestamp="2026-10-01T10:01:05.000Z",
            type="tool_result",
            provenance="tool_result",
            message={
                "role": "user",
                "parts": [
                    {
                        "functionResponse": {
                            "id": "call_ghi789",
                            "name": "run_shell_command",
                            "response": {"error": "cancelled by user"},
                        }
                    }
                ],
            },
            toolCallResult={"callId": "call_ghi789", "status": "cancelled"},
        ),
    ]


def qwen_logs_entries():
    """Gemini-legacy LogEntry array; model_switch carries a JSON string."""
    return [
        {
            "sessionId": QWEN_SESSION,
            "messageId": 0,
            "timestamp": "2026-10-01T10:00:00.000Z",
            "type": "user",
            "message": "run the tests",
        },
        {
            "sessionId": QWEN_SESSION,
            "messageId": 1,
            "timestamp": "2026-10-01T10:00:05.000Z",
            "type": "model_switch",
            "message": json.dumps(
                {
                    "fromModel": "qwen3-coder-plus",
                    "toModel": "qwen3-vl-plus",
                    "reason": "vision_auto_switch",
                }
            ),
        },
    ]


def build_qwen(home: Path) -> None:
    chats = home / ".qwen/projects/-srv-proj/chats"
    _jsonl(chats / (QWEN_SESSION + ".jsonl"), qwen_session_records())
    _jsonl(
        chats / "archive" / (QWEN_ARCHIVED + ".jsonl"),
        [dict(r, sessionId=QWEN_ARCHIVED) for r in qwen_session_records()[1:2]],
    )
    _jsonl(chats / (QWEN_SESSION + ".ledger.jsonl"), [{"promptId": "p1", "text": "run the tests"}])
    (chats / (QWEN_SESSION + ".runtime.json")).write_text(
        '{"session_id": "x", "started_at": 1790848800}', encoding="utf-8"
    )
    tmp = home / ".qwen/tmp" / QWEN_TMP
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "logs.json").write_text(json.dumps(qwen_logs_entries(), indent=2), encoding="utf-8")
    (home / ".qwen/settings.json").write_text("{}", encoding="utf-8")
    (home / ".qwen/oauth_creds.json").write_text('{"access_token": "secret"}', encoding="utf-8")
    # JSONC, as Qwen Code reads it: keys are folders, values TrustLevel strings.
    trust = home / ".qwen/trustedFolders.json"
    trust.write_text(
        '{\n  // trust dialog\n  "/srv/proj": "TRUST_FOLDER",\n  "/srv": "DO_NOT_TRUST"\n}\n',
        encoding="utf-8",
    )
    os.utime(trust, (QWEN_TRUST_MTIME, QWEN_TRUST_MTIME))


# Channel routes (#153), the `PersistedEntry` shape of
# packages/channels/base/src/SessionRouter.ts:25-36 at 2c591ecc:
# QWEN_SESSION was driven from a Telegram chat; QWEN_DAEMON_SESSION by the
# daemon from a GitHub thread, with no `startedAt`.
QWEN_DAEMON_SESSION = "e5f6a7b8-4444-4000-8000-000000000033"
QWEN_DAEMON_HASH = "9c1d" + "0" * 12
QWEN_ROUTES_MTIME = 1791367200  # 2026-10-07T10:00:00Z


def build_qwen_channels(home: Path) -> None:
    channels = home / ".qwen/channels"
    _json_file(
        channels / "sessions.json",
        {
            "telegram:-1001234": {
                "sessionId": QWEN_SESSION,
                "target": {"channelName": "telegram", "senderId": "42", "chatId": "-1001234"},
                "cwd": "/srv/proj",
                "turns": 3,
                "startedAt": 1790848800000,
            }
        },
    )
    routes = channels / "daemon" / QWEN_DAEMON_HASH / "routes.json"
    _json_file(
        routes,
        {
            "github:octo/proj#7": {
                "sessionId": QWEN_DAEMON_SESSION,
                "target": {
                    "channelName": "github",
                    "messageRoute": "issue_comment",
                    "senderId": "octocat",
                    "chatId": "octo/proj#7",
                    "threadId": "c-991",
                    "isGroup": True,
                },
                "cwd": "/srv/proj",
            }
        },
    )
    os.utime(routes, (QWEN_ROUTES_MTIME, QWEN_ROUTES_MTIME))
    # A half-written temporary file of the router, which the parser must not want.
    (channels / "1791367200000-4242-ab12.tmp").write_text("{", encoding="utf-8")


KIRO_SESSION = "3f2b8c1e-9d7a-4e6b-b1c2-0a9f8e7d6c5b"
KIRO_EXPORT_SESSION = "7c1d2e3f-4a5b-4c6d-8e7f-901234567890"
KIRO_SHELL_SESSION = "fig-shell-1"


def _kiro_user(content, timestamp=None, cwd="/srv/proj"):
    return {
        "additional_context": "",
        "env_context": {
            "env_state": {
                "operating_system": "linux",
                "current_working_directory": cwd,
                "environment_variables": [],
            }
        },
        "content": content,
        "timestamp": timestamp,
        "images": None,
    }


def _kiro_meta(n, start_ms, end_ms, kind="NotToolUse", tools=(), tags=()):
    return {
        "request_id": "req-%03d" % n,
        "message_id": "msg-%03d" % n,
        "request_start_timestamp_ms": start_ms,
        "stream_end_timestamp_ms": end_ms,
        "time_to_first_chunk": None,
        "time_between_chunks": [],
        "user_prompt_length": 0,
        "response_size": 0,
        "chat_conversation_type": kind,
        "tool_use_ids_and_names": [list(t) for t in tools],
        "model_id": "claude-sonnet-4",
        "message_meta_tags": list(tags),
    }


def kiro_conversation_records():
    """The ConversationState from analyzer/research/kiro.md section 8, with
    the project moved to /srv/proj. The research sample's user timestamp was
    six hours off its own request metadata; it is corrected here so the
    turns are in order."""
    return {
        "conversation_id": KIRO_SESSION,
        "next_message": None,
        "history": [
            {
                "user": _kiro_user(
                    {"Prompt": {"prompt": "list the files here"}},
                    "2026-04-23T20:17:15.123456789-07:00",
                ),
                "assistant": {
                    "ToolUse": {
                        "message_id": "msg-001",
                        "content": "I will list the directory.",
                        "tool_uses": [
                            {
                                "id": "tooluse_abc123",
                                "name": "execute_bash",
                                "orig_name": "execute_bash",
                                "args": {"command": "ls -la"},
                                "orig_args": {"command": "ls -la"},
                            }
                        ],
                    }
                },
                "request_metadata": _kiro_meta(
                    1, 1777000635200, 1777000636900, "ToolUse", [("tooluse_abc123", "execute_bash")]
                ),
            },
            {
                "user": _kiro_user(
                    {
                        "ToolUseResults": {
                            "tool_use_results": [
                                {
                                    "tool_use_id": "tooluse_abc123",
                                    "content": [{"Text": "total 8\nREADME.md"}],
                                    "status": "Success",
                                }
                            ]
                        }
                    }
                ),
                "assistant": {
                    "Response": {
                        "message_id": "msg-002",
                        "content": "The directory contains README.md.",
                    }
                },
                "request_metadata": dict(
                    _kiro_meta(2, 1777000637000, 1777000638100), model_id="claude-opus-4"
                ),
            },
        ],
        "valid_history_range": [0, 2],
        "transcript": ["> list the files here", "The directory contains README.md."],
        "tools": {"native___": []},
        "context_manager": None,
        "context_message_length": None,
        "latest_summary": None,
        "model_info": {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4"},
        "file_line_tracker": {},
        "checkpoint_manager": None,
        "mcp_enabled": True,
    }


def kiro_export_records():
    """A /save export exercising the less common variants: an MCP tool whose
    name differs from orig_name, a Json result, a cancelled tool use, a
    Compact tag, latest_summary, a pending next_message and the legacy
    `model` field instead of model_info."""
    return {
        "conversation_id": KIRO_EXPORT_SESSION,
        "next_message": _kiro_user(
            {"Prompt": {"prompt": "now push it"}}, "2026-04-24T08:00:00-07:00"
        ),
        "history": [
            {
                "user": _kiro_user(
                    {"Prompt": {"prompt": "open an issue"}}, "2026-04-24T07:00:00.000-07:00"
                ),
                "assistant": {
                    "ToolUse": {
                        "message_id": "msg-010",
                        "content": "",
                        "tool_uses": [
                            {
                                "id": "tooluse_mcp1",
                                "name": "github___create_issue",
                                "orig_name": "create_issue",
                                "args": {"title": "bug"},
                                "orig_args": {"title": "bug"},
                            }
                        ],
                    }
                },
                "request_metadata": dict(
                    _kiro_meta(10, 1777039201000, 1777039202000, "ToolUse"), model_id=None
                ),
            },
            {
                "user": _kiro_user(
                    {
                        "ToolUseResults": {
                            "tool_use_results": [
                                {
                                    "tool_use_id": "tooluse_mcp1",
                                    "content": [{"Json": {"number": 7}}],
                                    "status": "Error",
                                }
                            ]
                        }
                    }
                ),
                "assistant": {
                    "ToolUse": {
                        "message_id": "msg-011",
                        "content": "Retrying.",
                        "tool_uses": [
                            {
                                "id": "tooluse_bash2",
                                "name": "execute_bash",
                                "orig_name": "execute_bash",
                                "args": {"command": "rm -rf build"},
                                "orig_args": {"command": "rm -rf build"},
                            }
                        ],
                    }
                },
                "request_metadata": _kiro_meta(11, 1777039203000, 1777039204000, "ToolUse"),
            },
            {
                "user": _kiro_user(
                    {
                        "CancelledToolUses": {
                            "prompt": "stop, do not delete",
                            "tool_use_results": [
                                {
                                    "tool_use_id": "tooluse_bash2",
                                    "content": [{"Text": "Tool use was cancelled by the user"}],
                                    "status": "Error",
                                }
                            ],
                        }
                    },
                    "2026-04-24T07:00:10.000-07:00",
                ),
                "assistant": {"Response": {"message_id": "msg-012", "content": "Stopped."}},
                "request_metadata": _kiro_meta(12, 1777039211000, 1777039212000, tags=["Compact"]),
            },
        ],
        "valid_history_range": [0, 3],
        "transcript": [],
        "tools": {"native___": []},
        "latest_summary": [
            "User asked to open an issue and cancelled a delete.",
            _kiro_meta(13, 1777039213000, 1777039214000),
        ],
        "model": "claude-3.7-sonnet",
    }


def build_kiro(home: Path) -> None:
    base = home / ".local/share/amazon-q"
    base.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(base / "data.sqlite3"))
    con.executescript("""
    CREATE TABLE migrations (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, migration_time INTEGER NOT NULL);
    CREATE TABLE history (id INTEGER PRIMARY KEY, command TEXT, shell TEXT, pid INTEGER, session_id TEXT, cwd TEXT,
      start_time INTEGER, hostname TEXT, exit_code INTEGER, end_time INTEGER, duration INTEGER);
    CREATE TABLE state (key TEXT PRIMARY KEY, value BLOB);
    CREATE TABLE auth_kv (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE conversations (key TEXT PRIMARY KEY, value TEXT);
    """)
    con.execute(
        "INSERT INTO conversations (key, value) VALUES (?, ?)",
        ("/srv/proj", json.dumps(kiro_conversation_records())),
    )
    con.execute("INSERT INTO conversations (key, value) VALUES (?, ?)", ("/srv/broken", "not json"))
    con.execute(
        "INSERT INTO history (command, shell, pid, session_id, cwd, start_time, hostname, exit_code, end_time, "
        "duration) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "git status",
            "zsh",
            4242,
            KIRO_SHELL_SESSION,
            "/srv/proj",
            1776999600,
            "ws1",
            0,
            1776999601,
            1000,
        ),
    )
    con.execute(
        "INSERT INTO auth_kv VALUES ('codewhisperer:odic:token', '{\"access_token\":\"REDACT-ME\"}')"
    )
    con.commit()
    con.close()
    exports = home / ".aws/amazonq/exports"
    exports.mkdir(parents=True, exist_ok=True)
    text = json.dumps(kiro_export_records(), indent=2)
    (exports / "issue-chat.json").write_text(text, encoding="utf-8")
    # an export cut mid-write, inside the third history entry
    (exports / "issue-chat-cut.json").write_text(
        text[: text.index("stop, do not delete")], encoding="utf-8"
    )
    # noise the parser must not want: CLI settings, and a Kiro CLI session
    # file whose format is unverified even though it looks like an export
    (home / ".kiro/settings").mkdir(parents=True, exist_ok=True)
    (home / ".kiro/settings/cli.json").write_text('{"chat.defaultModel": "auto"}', encoding="utf-8")
    (home / ".kiro/sessions").mkdir(parents=True, exist_ok=True)
    (home / ".kiro/sessions/s1.json").write_text(
        json.dumps(
            {
                "conversation_id": "x",
                "history": [],
                "messages": [{"role": "user", "content": [{"text": "hi"}]}],
            }
        ),
        encoding="utf-8",
    )


GEMINI_SESSION = "a1b2c3d4-0000-4000-8000-000000000001"
GEMINI_RESUMED = "a1b2c3d4-0000-4000-8000-0000000000ff"
GEMINI_LEGACY = "b2c3d4e5-0000-4000-8000-000000000002"
GEMINI_SUBAGENT = "c3d4e5f6-0000-4000-8000-000000000003"
GEMINI_HASH = (
    "6b9af143446a411aefa3edb76e4693799bd7513e7ed8d919962d6713d3d3b972"  # sha256("/srv/proj")
)
GEMINI_REL = ".gemini/tmp/proj/chats/session-2026-10-01T09-00-a1b2c3d4.jsonl"


def gemini_session_records():
    """Session JSONL in the chatRecordingTypes.ts shapes: a re-appended
    message, $set, $rewindTo, $patch and a $set.sessionId from a resume."""
    ts = "2026-10-01T09:00:%s.000Z"
    ls_call = {
        "id": "list_directory-1759309207000",
        "name": "list_directory",
        "args": {"path": "/srv/proj/src"},
        "status": "executing",
        "timestamp": "2026-10-01T09:00:07.100Z",
        "displayName": "ReadFolder",
        "description": "Lists files",
    }
    ls_done = dict(
        ls_call,
        status="success",
        result=[
            {
                "functionResponse": {
                    "id": "list_directory-1759309207000",
                    "name": "list_directory",
                    "response": {"output": "main.ts\nutil.ts"},
                }
            }
        ],
    )
    g1 = {
        "id": "msg-g1",
        "timestamp": ts % "07",
        "type": "gemini",
        "content": "Listing now.",
        "thoughts": [
            {
                "subject": "Plan",
                "description": "Use the ls tool.",
                "timestamp": "2026-10-01T09:00:06.500Z",
            }
        ],
        "tokens": {"input": 120, "output": 12, "cached": 0, "thoughts": 8, "tool": 0, "total": 140},
        "model": "gemini-2.5-pro",
        "toolCalls": [ls_call],
    }
    rf = {
        "id": "read_file-1759309222000",
        "name": "read_file",
        "args": {"absolute_path": "/srv/proj/src/util.ts"},
        "status": "success",
        "timestamp": "2026-10-01T09:00:22.100Z",
        "displayName": "ReadFile",
        "result": [
            {
                "functionResponse": {
                    "id": "read_file-1759309222000",
                    "name": "read_file",
                    "response": {"output": "draft"},
                }
            }
        ],
    }
    return [
        {
            "sessionId": GEMINI_SESSION,
            "projectHash": GEMINI_HASH,
            "startTime": ts % "00",
            "lastUpdated": ts % "00",
            "kind": "main",
        },
        {
            "id": "msg-u1",
            "timestamp": ts % "05",
            "type": "user",
            "content": [{"text": "list files in src"}],
        },
        g1,
        dict(g1, toolCalls=[ls_done]),
        {"$set": {"lastUpdated": ts % "08", "summary": "List src files"}},
        {
            "id": "msg-u2",
            "timestamp": ts % "10",
            "type": "user",
            "content": [{"text": "delete everything in /srv/proj"}],
        },
        {
            "id": "msg-g2",
            "timestamp": ts % "11",
            "type": "gemini",
            "content": "",
            "model": "gemini-2.5-pro",
            "toolCalls": [
                {
                    "id": "run_shell_command-1",
                    "name": "run_shell_command",
                    "args": {"command": "rm -rf /srv/proj/*"},
                    "status": "awaiting_approval",
                    "timestamp": ts % "11",
                    "displayName": "Shell",
                }
            ],
        },
        {"$rewindTo": "msg-u2"},
        {"id": "msg-u3", "timestamp": ts % "20", "type": "user", "content": "show util.ts"},
        {
            "id": "msg-g3",
            "timestamp": ts % "22",
            "type": "gemini",
            "content": "draft answer",
            "model": "gemini-2.5-pro",
            "toolCalls": [rf],
        },
        {
            "$patch": {
                "id": "msg-g3",
                "content": [{"text": "Here is util.ts."}],
                "toolCalls": [
                    {
                        "id": "read_file-1759309222000",
                        "result": [
                            {
                                "functionResponse": {
                                    "id": "read_file-1759309222000",
                                    "name": "read_file",
                                    "response": {"output": "export const x = 1"},
                                }
                            }
                        ],
                    }
                ],
            }
        },
        {"id": "msg-i1", "timestamp": ts % "23", "type": "info", "content": "Request cancelled."},
        {
            "id": "msg-g4",
            "timestamp": ts % "24",
            "type": "gemini",
            "content": "",
            "model": "gemini-2.5-flash",
            "toolCalls": [
                {
                    "id": "run_shell_command-2",
                    "name": "run_shell_command",
                    "args": {"command": "curl http://x"},
                    "status": "cancelled",
                    "timestamp": ts % "24",
                    "displayName": "Shell",
                }
            ],
        },
        {"$set": {"sessionId": GEMINI_RESUMED}},
        {
            "id": "msg-u4",
            "timestamp": "2026-10-01T09:01:00.000Z",
            "type": "user",
            "content": "resume work",
        },
    ]


def gemini_legacy_record():
    return {
        "sessionId": GEMINI_LEGACY,
        "projectHash": GEMINI_HASH,
        "startTime": "2026-09-30T08:00:00.000Z",
        "lastUpdated": "2026-09-30T08:00:03.000Z",
        "messages": [
            {
                "id": "l-u1",
                "timestamp": "2026-09-30T08:00:01.000Z",
                "type": "user",
                "content": "hello",
            },
            {
                "id": "l-g1",
                "timestamp": "2026-09-30T08:00:03.000Z",
                "type": "gemini",
                "content": [{"text": "weighing it", "thought": True}, {"text": "Hi."}],
                "model": "gemini-2.0-flash",
            },
        ],
    }


def gemini_logs_records():
    return [
        {
            "sessionId": GEMINI_SESSION,
            "messageId": 0,
            "timestamp": "2026-10-01T09:00:05.000Z",
            "type": "user",
            "message": "list files in src",
        },
        {
            "sessionId": GEMINI_SESSION,
            "messageId": 1,
            "timestamp": "2026-10-01T09:00:10.000Z",
            "type": "user",
            "message": "delete everything in /srv/proj",
        },
    ]


GEMINI_TRUST_MTIME = 1790856000  # 2026-10-01T12:00:00Z, trustedFolders.json's mtime


def build_gemini_cli(base: Path) -> None:
    """~/.gemini with a slug directory (marker file), a legacy hash directory
    resolved through projects.json, a subagent session and noise."""
    slug = base / "tmp/proj"
    _jsonl(base / GEMINI_REL[len(".gemini/") :], gemini_session_records())
    _jsonl(
        slug / "chats" / GEMINI_SESSION / (GEMINI_SUBAGENT + ".jsonl"),
        [
            {
                "sessionId": GEMINI_SUBAGENT,
                "projectHash": GEMINI_HASH,
                "startTime": "2026-10-01T09:00:30.000Z",
                "kind": "subagent",
            },
            {
                "id": "s-u1",
                "timestamp": "2026-10-01T09:00:30.000Z",
                "type": "user",
                "content": "investigate",
            },
        ],
    )
    (slug / ".project_root").write_text("/srv/proj", encoding="utf-8")
    (slug / "logs.json").write_text(json.dumps(gemini_logs_records()), encoding="utf-8")
    (slug / "shell_history").write_text("ls\n", encoding="utf-8")
    legacy = base / "tmp" / GEMINI_HASH / "chats"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "session-2026-09-30T08-00-b2c3d4e5.json").write_text(
        json.dumps(gemini_legacy_record()), encoding="utf-8"
    )
    (base / "projects.json").write_text(
        json.dumps({"projects": {"/srv/proj": "proj"}}), encoding="utf-8"
    )
    (base / "oauth_creds.json").write_text('{"access_token": "secret"}', encoding="utf-8")
    trust = base / "trustedFolders.json"
    trust.write_text(
        json.dumps({"/srv/proj": "TRUST_FOLDER", "/srv/other": "TRUST_PARENT"}, indent=2),
        encoding="utf-8",
    )
    os.utime(trust, (GEMINI_TRUST_MTIME, GEMINI_TRUST_MTIME))


def _wal_db(path: Path, script: str, inserts) -> None:
    """Build a WAL-mode SQLite file whose schema is checkpointed into the main
    file and whose rows live only in the -wal sidecar, as on a host where the
    agent is still running. The files are copied out while the writer is
    still open, so closing it cannot checkpoint the copy."""
    import shutil
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="cac-fixture-"))
    try:
        src = tmp / path.name
        con = sqlite3.connect(str(src))
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA wal_autocheckpoint=0")
        con.executescript(script)
        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        for sql in inserts:
            con.execute(sql)
        con.commit()
        path.parent.mkdir(parents=True, exist_ok=True)
        for suffix in ("", "-wal", "-shm"):
            if Path(str(src) + suffix).exists():
                shutil.copyfile(str(src) + suffix, str(path) + suffix)
        con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


CRUSH_SESSION = "6f1c0001"

# Columns of internal/db/migrations at crush ca6ae26 that the parser reads.
CRUSH_SCHEMA = """
CREATE TABLE sessions (id TEXT PRIMARY KEY, parent_session_id TEXT, title TEXT NOT NULL,
  message_count INTEGER NOT NULL DEFAULT 0, prompt_tokens INTEGER NOT NULL DEFAULT 0,
  completion_tokens INTEGER NOT NULL DEFAULT 0, cost REAL NOT NULL DEFAULT 0.0,
  updated_at INTEGER NOT NULL, created_at INTEGER NOT NULL, summary_message_id TEXT, todos TEXT, channel TEXT);
CREATE TABLE messages (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL, parts TEXT NOT NULL DEFAULT '[]',
  model TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, finished_at INTEGER, provider TEXT,
  is_summary_message INTEGER DEFAULT 0 NOT NULL, prism_model_id TEXT, prism_model_name TEXT);
CREATE TABLE files (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, path TEXT NOT NULL, content TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
"""


def crush_records():
    """The INSERT statements of research/crush.md section 8, plus a final
    assistant message with reasoning, text and an abnormal finish, answered
    by another provider's model so the session has a model change."""
    return [
        "INSERT INTO sessions(id,title,message_count,prompt_tokens,completion_tokens,cost,updated_at,created_at) "
        "VALUES('6f1c0001','Fix bug',3,10,5,0.01,1760000005,1760000001)",
        "INSERT INTO messages(id,session_id,role,parts,model,provider,created_at,updated_at,finished_at,is_summary_message) VALUES "
        """('m1','6f1c0001','user','[{"type":"text","data":{"text":"list files"}},{"type":"finish","data":{"reason":"stop","time":0}}]','claude-sonnet-4','anthropic',1760000001,1760000001,NULL,0),"""
        """('m2','6f1c0001','assistant','[{"type":"tool_call","data":{"id":"call_x1","name":"bash","input":"{\\"command\\":\\"ls\\"}","provider_executed":false,"finished":true}},{"type":"finish","data":{"reason":"tool_use","time":1760000003}}]','claude-sonnet-4','anthropic',1760000002,1760000003,1760000003,0),"""
        """('m3','6f1c0001','tool','[{"type":"tool_result","data":{"tool_call_id":"call_x1","name":"bash","content":"a.txt","data":"","mime_type":"","metadata":"","is_error":false}},{"type":"finish","data":{"reason":"stop","time":0}}]','','',1760000003,1760000003,NULL,0)""",
        "INSERT INTO messages(id,session_id,role,parts,model,provider,created_at,updated_at,finished_at,is_summary_message) VALUES "
        """('m4','6f1c0001','assistant','[{"type":"reasoning","data":{"thinking":"one file only","signature":"sig","started_at":1760000004,"finished_at":1760000004}},{"type":"text","data":{"text":"There is one file, a.txt."}},{"type":"finish","data":{"reason":"max_tokens","time":1760000005}}]','gpt-5','openai',1760000004,1760000005,1760000005,0)""",
    ]


def build_crush(home: Path) -> None:
    """Crush run in the home directory, so its per-project store is
    ~/.crush/crush.db, plus the global project registry and config noise."""
    _wal_db(home / ".crush/crush.db", CRUSH_SCHEMA, crush_records())
    (home / ".crush/crush.json").write_text(
        '{"providers":{"anthropic":{"api_key":"sk-test"}}}', encoding="utf-8"
    )
    reg = home / ".local/share/crush"
    reg.mkdir(parents=True, exist_ok=True)
    (reg / "projects.json").write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "path": "/srv/proj",
                        "data_dir": "/srv/proj/.crush",
                        "last_accessed": "2026-10-01T12:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (home / ".config/crush").mkdir(parents=True, exist_ok=True)
    (home / ".config/crush/crush.json").write_text("{}", encoding="utf-8")


GOOSE_SESSION = "20260301_1"

# session_manager.rs at goose 591edd4, schema version 16 (research/goose.md section 3).
GOOSE_SCHEMA = """
CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE sessions (
  id TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
  user_set_name BOOLEAN DEFAULT FALSE, session_type TEXT NOT NULL DEFAULT 'user',
  working_dir TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, extension_data TEXT DEFAULT '{}',
  total_tokens INTEGER, input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER,
  cache_write_tokens INTEGER, accumulated_total_tokens INTEGER, accumulated_input_tokens INTEGER,
  accumulated_output_tokens INTEGER, accumulated_cache_read_tokens INTEGER,
  accumulated_cache_write_tokens INTEGER, accumulated_cost REAL, schedule_id TEXT, recipe_json TEXT,
  user_recipe_values_json TEXT, provider_name TEXT, model_config_json TEXT,
  goose_mode TEXT NOT NULL DEFAULT 'auto', archived_at TIMESTAMP, project_id TEXT, parent_session_id TEXT);
CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, message_id TEXT, session_id TEXT NOT NULL REFERENCES sessions(id),
  role TEXT NOT NULL, content_json TEXT NOT NULL, created_timestamp INTEGER NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tokens INTEGER, metadata_json TEXT);
CREATE TABLE usage_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  created_timestamp INTEGER NOT NULL, model TEXT, input_tokens INTEGER, output_tokens INTEGER,
  total_tokens INTEGER, cache_read_tokens INTEGER, cache_write_tokens INTEGER, cost REAL,
  cost_source TEXT, is_compaction INTEGER DEFAULT 0);
"""


def goose_records(cwd="/srv/proj"):
    """The INSERT statements of research/goose.md section 8, with the
    working directory moved to the shared project path."""
    return [
        "INSERT INTO schema_version(version) VALUES (16)",
        "INSERT INTO sessions(id,name,session_type,working_dir,created_at,updated_at,extension_data,provider_name,model_config_json,goose_mode) "
        "VALUES ('20260301_1','Fix flaky test','user','%s','2026-03-01 09:00:00','2026-03-01 09:01:05','{}','anthropic',"
        """'{"model_name":"claude-sonnet-4-5","temperature":null,"max_tokens":null,"toolshim":false,"toolshim_model":null}','auto')"""
        % cwd,
        "INSERT INTO messages(message_id,session_id,role,content_json,created_timestamp,metadata_json) VALUES "
        """('msg_20260301_1_a1','20260301_1','user','[{"type":"text","text":"run the tests"}]',1772355600,'{"userVisible":true,"agentVisible":true}'),"""
        """('msg_20260301_1_a2','20260301_1','assistant','[{"type":"toolRequest","id":"call_1","toolCall":{"status":"success","value":{"name":"developer__shell","arguments":{"command":"pytest -q"}}}}]',1772355601,"""
        """ '{"userVisible":true,"agentVisible":true,"inference":{"provider":"anthropic","requestedModel":"claude-sonnet-4-5"}}'),"""
        """('msg_20260301_1_a3','20260301_1','user','[{"type":"toolResponse","id":"call_1","toolResult":{"status":"success","value":{"content":[{"type":"text","text":"3 passed"}]}}}]',1772355603,'{"userVisible":true,"agentVisible":true}'),"""
        """('msg_20260301_1_a4','20260301_1','assistant','[{"type":"thinking","thinking":"all green","signature":"sig"},{"type":"text","text":"All 3 tests pass."}]',1772355605, '{"userVisible":true,"agentVisible":true,"inference":{"provider":"openai","requestedModel":"gpt-4.1","resolvedModel":"gpt-4.1-2025-04-14"}}')""",
        "INSERT INTO usage_ledger(session_id,created_timestamp,model,input_tokens,output_tokens,total_tokens) "
        "VALUES ('20260301_1',1772355605,'claude-sonnet-4-5',120,30,150)",
    ]


# Session sync (issue 153): a gateway session, created when a Telegram user
# pairs (crates/goose/src/gateway/handler.rs:304-326 at aaif-goose/goose
# bfcc6ee): name `<platform>/<display name or user id>`, working_dir
# `<config>/gateway/<platform>/<user_id>`. Kept out of build_home so the
# shared session's row order stays as the other tests expect.
GOOSE_GATEWAY_SESSION = "20261017_4"


def goose_gateway_records(display="alice"):
    return [
        "INSERT INTO sessions(id,name,session_type,working_dir,created_at,updated_at) VALUES "
        "('%s','telegram/%s','gateway','/home/alice/.config/goose/gateway/telegram/123456789',"
        "'2026-10-17 08:00:00','2026-10-17 08:05:00')" % (GOOSE_GATEWAY_SESSION, display),
        "INSERT INTO messages(message_id,session_id,role,content_json,created_timestamp,metadata_json)"
        " VALUES ('msg_gw_1','%s','user','[{\"type\":\"text\",\"text\":\"disk usage?\"}]',"
        "1792224060,'{\"userVisible\":true}')" % GOOSE_GATEWAY_SESSION,
    ]


def goose_legacy_records():
    return [
        {
            "description": "old chat",
            "working_dir": "/srv/old",
            "created_at": "2026-03-01T09:00:00Z",
            "updated_at": "2026-03-01T09:00:10Z",
            "extension_data": {},
            "message_count": 1,
        },
        {
            "id": "m1",
            "role": "user",
            "created": 1772355600,
            "content": [{"type": "text", "text": "hello"}],
        },
    ]


def goose_llm_request_records():
    return [
        {
            "model_config": {"model_name": "gpt-4.1"},
            "input": {"model": "gpt-4.1", "messages": [{"role": "user", "content": "hello"}]},
        },
        {
            "data": {
                "role": "assistant",
                "created": 1772355601,
                "content": [{"type": "text", "text": "hi"}],
            },
            "usage": {"input_tokens": 5, "output_tokens": 1},
        },
    ]


GOOSE_LEGACY_REL = ".local/share/goose/sessions/20260301_090000.jsonl"


def build_goose(home: Path) -> None:
    data = home / ".local/share/goose/sessions"
    _wal_db(data / "sessions.db", GOOSE_SCHEMA, goose_records())
    _jsonl(home / GOOSE_LEGACY_REL, goose_legacy_records())
    state = home / ".local/state/goose"
    _jsonl(state / "logs/llm_request.0.jsonl", goose_llm_request_records())
    (state / "history.txt").write_text(
        "#V2\nrun the tests\nline one\\nline two \\\\ done\n", encoding="utf-8"
    )
    (home / ".config/goose").mkdir(parents=True, exist_ok=True)
    (home / ".config/goose/config.yaml").write_text("GOOSE_PROVIDER: anthropic\n", encoding="utf-8")
    (home / ".config/goose/secrets.yaml").write_text(
        "ANTHROPIC_API_KEY: sk-test\n", encoding="utf-8"
    )


CONTINUE_SESSION = "0f1e"
CONTINUE_CREATED = (
    "1790935200000"  # 2026-10-02T10:00:00Z, a millisecond epoch string as sessions.json stores it
)


def continue_session():
    """A Continue session file in the shape of core/index.d.ts `Session`."""
    edit = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "edit_existing_file", "arguments": '{"filepath":"a.py"}'},
    }
    term = {
        "id": "call_2",
        "type": "function",
        "function": {"name": "run_terminal_command", "arguments": '{"command":"rm -rf build"}'},
    }
    return {
        "sessionId": CONTINUE_SESSION,
        "title": "Fix bug",
        "workspaceDirectory": "/srv/proj",
        "history": [
            {
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "rename foo"},
                        {"type": "imageUrl", "imageUrl": {"url": "data:image/png;base64,AA"}},
                    ],
                },
                "contextItems": [],
            },
            {
                "message": {"role": "thinking", "content": "consider the callers"},
                "contextItems": [],
            },
            {
                "message": {"role": "assistant", "content": "", "toolCalls": [edit]},
                "contextItems": [],
                "reasoning": {
                    "active": False,
                    "text": "find foo first",
                    "startAt": 1790935201000,
                    "endAt": 1790935202000,
                },
                "promptLogs": [
                    {
                        "modelTitle": "GPT-4o",
                        "modelProvider": "openai",
                        "prompt": "<long prompt>",
                        "completion": "",
                    }
                ],
                "toolCallStates": [
                    {
                        "toolCallId": "call_1",
                        "toolCall": edit,
                        "status": "done",
                        "parsedArgs": {"filepath": "a.py"},
                        "output": [{"name": "Edit", "description": "", "content": "ok"}],
                    }
                ],
            },
            {
                "message": {"role": "tool", "content": "ok", "toolCallId": "call_1"},
                "contextItems": [],
            },
            {
                "message": {
                    "role": "assistant",
                    "content": "Renamed. Cleaning the build too.",
                    "toolCalls": [term],
                },
                "contextItems": [],
                "promptLogs": [
                    {
                        "modelTitle": "Claude Sonnet 4.5",
                        "modelProvider": "anthropic",
                        "prompt": "<long prompt>",
                        "completion": "Renamed. Cleaning the build too.",
                    }
                ],
                "toolCallStates": [
                    {
                        "toolCallId": "call_2",
                        "toolCall": term,
                        "status": "canceled",
                        "parsedArgs": {"command": "rm -rf build"},
                    }
                ],
            },
        ],
        "mode": "agent",
        "chatModelTitle": "GPT-4o",
        "usage": {"promptTokens": 120, "completionTokens": 30, "totalCost": 0.01},
    }


def continue_index():
    return [
        {
            "sessionId": CONTINUE_SESSION,
            "title": "Fix bug",
            "dateCreated": CONTINUE_CREATED,
            "workspaceDirectory": "/srv/proj",
            "messageCount": 2,
        }
    ]


def continue_dev_data():
    base = {
        "schema": "0.2.0",
        "userId": "",
        "userAgent": "vscode/1.1 (Continue/1.0)",
        "selectedProfileId": "local",
    }
    chat = dict(
        base,
        eventName="chatInteraction",
        timestamp="2026-10-02T10:00:05.000Z",
        prompt="rename foo",
        completion="done",
        modelName="gpt-4o",
        modelTitle="GPT-4o",
        modelProvider="openai",
        sessionId=CONTINUE_SESSION,
    )
    tool = dict(
        base,
        eventName="toolUsage",
        timestamp="2026-10-02T10:00:03.000Z",
        toolCallId="call_1",
        functionName="edit_existing_file",
        functionParams={"filepath": "a.py"},
        toolCallArgs='{"filepath":"a.py"}',
        accepted=True,
        succeeded=True,
        output=[{"name": "Edit", "description": "", "content": "ok"}],
    )
    rejected = dict(
        base,
        eventName="toolUsage",
        timestamp="2026-10-02T10:00:06.000Z",
        toolCallId="call_2",
        functionName="run_terminal_command",
        functionParams={"command": "rm -rf build"},
        toolCallArgs='{"command":"rm -rf build"}',
        accepted=False,
        succeeded=False,
        output=[],
    )
    return [chat], [tool, rejected]


def build_continue(home: Path) -> None:
    sessions = home / ".continue/sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / (CONTINUE_SESSION + ".json")).write_text(
        json.dumps(continue_session(), indent=2), encoding="utf-8"
    )
    (sessions / "sessions.json").write_text(json.dumps(continue_index()), encoding="utf-8")
    chat, tool = continue_dev_data()
    _jsonl(home / ".continue/dev_data/0.2.0/chatInteraction.jsonl", chat)
    _jsonl(home / ".continue/dev_data/0.2.0/toolUsage.jsonl", tool)
    (home / ".continue/config.yaml").write_text("name: Local\nmodels: []\n", encoding="utf-8")


# The `cn` CLI's winston log in `cn serve --id` mode (#153), in the line
# format of extensions/cli/src/util/logger.ts:74-95 and the `[metadata]`
# lines of extensions/cli/src/util/metadata.ts:125-181 at 5522c6f. Two
# processes (a1b2c3d4, 0e0f1a2b) post for the same agent; the second's
# result comes after the first's second post, which never gets one.
CONTINUE_AGENT = "agt_7f3e"
CONTINUE_METADATA_URL = "https://api.continue.dev/agents/%s/metadata" % CONTINUE_AGENT
CONTINUE_CN_LOG = (
    "\n".join(
        [
            "2026-10-07 10:00:00.001 [a1b2c3d4] [info]: Starting server on port 8000",
            "2026-10-07 10:00:00.010 [a1b2c3d4] [warn]: Storage sync requested but no Continue API"
            " key is available; skipping uploads.",
            "2026-10-07 10:00:05.100 [a1b2c3d4] [info]: [metadata] POST %s"
            ' {"agentId":"%s","metadataKeys":["summary","isComplete"]}'
            % (CONTINUE_METADATA_URL, CONTINUE_AGENT),
            '2026-10-07 10:00:05.101 [a1b2c3d4] [info]: [metadata] Request body {"metadata":'
            '{"summary":"Renamed foo to bar","isComplete":false}}',
            "2026-10-07 10:00:05.200 [0e0f1a2b] [info]: [metadata] POST %s"
            ' {"agentId":"%s","metadataKeys":["additions"]}'
            % (CONTINUE_METADATA_URL, CONTINUE_AGENT),
            "2026-10-07 10:00:05.350 [a1b2c3d4] [info]: [metadata] Success: 200 (250ms) %s"
            % CONTINUE_METADATA_URL,
            "2026-10-07 10:00:06.000 [a1b2c3d4] [info]: [metadata] POST %s"
            ' {"agentId":"%s","metadataKeys":["isComplete"]}'
            % (CONTINUE_METADATA_URL, CONTINUE_AGENT),
            "2026-10-07 10:00:06.400 [0e0f1a2b] [warn]: [metadata] Failed: 502 Bad Gateway (1200ms) %s"
            ' {"response":"upstream"}' % CONTINUE_METADATA_URL,
            "2026-10-07 10:00:07.000 [a1b2c3d4] [error]: Unhandled error",
            "Error: boom",
            "    at main (index.js:1:1)",
        ]
    )
    + "\n"
)
CONTINUE_CN1_LOG = (
    "2026-10-06 09:00:00.000 [99aa88bb] [info]: [metadata] POST %s"
    ' {"agentId":"%s","metadataKeys":["summary"]}\n'
    "2026-10-06 09:00:00.500 [99aa88bb] [info]: [metadata] Auth required (skipping) (5ms) %s\n"
    % (CONTINUE_METADATA_URL, CONTINUE_AGENT, CONTINUE_METADATA_URL)
)


def build_continue_log(home: Path) -> None:
    logs = home / ".continue/logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "cn.log").write_text(CONTINUE_CN_LOG, encoding="utf-8")
    (logs / "cn1.log").write_text(CONTINUE_CN1_LOG, encoding="utf-8")
    # The extension's prompt log, which the parser does not read.
    (logs / "prompt.log").write_text("==========================\nprompt\n", encoding="utf-8")


# Written the way aider/io.py writes them: user and blockquote lines end in
# two spaces (markdown line breaks), assistant output is framed by blanks.
AIDER_CHAT = "".join(
    [
        "\n# aider chat started at 2026-10-02 12:00:00\n\n",
        "\n#### rename foo to bar  \n",
        "\nHere is the change:\n\na.py\n<<<<<<< SEARCH\nfoo\n=======\nbar\n>>>>>>> REPLACE\n\n",
        "> Applied edit to a.py  \n",
        "> Commit abc1234 refactor: rename foo to bar  \n",
        "\n# aider chat started at 2026-10-02 13:00:00\n\n",
        "\n#### /add b.py  \n",
        "> Added b.py to the chat  \n",
        "\n#### <blank>  \n",
    ]
)

# The last entry has no chat-history twin (a prompt whose chat line is gone),
# so it survives deduplication; the other two pair with the chat rows.
AIDER_INPUT = (
    "\n# 2026-10-02 12:00:05.123456\n+rename foo to bar\n\n# 2026-10-02 13:00:02.000000\n+/add b.py\n"
    "\n# 2026-10-02 13:05:00.000000\n+delete the migrations folder\n"
)

AIDER_LLM = (
    "TO LLM 2026-10-02T12:00:05\n-------\nSYSTEM Act as an expert\nSYSTEM software developer\n-------\n"
    "USER rename foo to bar\nLLM RESPONSE 2026-10-02T12:00:09\nASSISTANT Here is the change:\nASSISTANT \n"
    "ASSISTANT a.py\n"
)


def build_aider(base: Path) -> None:
    """Aider's history files in `base`, a home or a repository root."""
    base.mkdir(parents=True, exist_ok=True)
    (base / ".aider.chat.history.md").write_text(AIDER_CHAT, encoding="utf-8")
    (base / ".aider.input.history").write_text(AIDER_INPUT, encoding="utf-8")
    (base / ".aider.llm.history").write_text(AIDER_LLM, encoding="utf-8")
    (base / ".aider.conf.yml").write_text("model: gpt-4o\n", encoding="utf-8")


ZED_THREAD = "6f1c0b2e-1111-4bbb-8ccc-000000000001"
ZED_EXTERNAL = "ext-claude-code-sess-1"


def zed_thread_record(cwd="/srv/proj"):
    """A `threads.data` blob, version 0.3.0, as in analyzer/research/zed.md."""
    return {
        "version": "0.3.0",
        "title": "Fix flaky test",
        "updated_at": "2026-10-03T09:01:05Z",
        "initial_project_snapshot": {
            "worktree_snapshots": [
                {
                    "worktree_path": cwd,
                    "git_state": {
                        "remote_url": "git@github.com:alice/proj.git",
                        "head_sha": "abc123",
                        "current_branch": "main",
                        "diff": None,
                    },
                }
            ],
            "timestamp": "2026-10-03T09:00:00Z",
        },
        "model": {"provider": "anthropic", "model": "claude-sonnet-4-5"},
        "profile": "write",
        "sandbox_grants": {
            "write_paths": [
                cwd + "/build",
                {"requested": "/tmp/out", "resolved": "/private/tmp/out"},
            ],
            "network_hosts": ["*.npmjs.org"],
            "network_any_host": False,
            "allow_fs_write_all": False,
            "unsandboxed": True,
            "sandbox_fallback": False,
        },
        "messages": [
            {
                "User": {
                    "id": "9a7d6c5b-2222-4ddd-9eee-000000000002",
                    "content": [
                        {"Text": "run the tests"},
                        {"Mention": {"uri": "file://%s/README.md" % cwd, "content": ""}},
                    ],
                }
            },
            {
                "Agent": {
                    "content": [
                        {"Thinking": {"text": "use pytest", "signature": None}},
                        {
                            "ToolUse": {
                                "id": "toolu_01",
                                "name": "terminal",
                                "raw_input": '{"command":"pytest -q"}',
                                "input": {"type": "json", "value": {"command": "pytest -q"}},
                                "is_input_complete": True,
                                "thought_signature": None,
                            }
                        },
                        {"Text": "All 3 tests pass."},
                    ],
                    "tool_results": {
                        "toolu_01": {
                            "tool_use_id": "toolu_01",
                            "tool_name": "terminal",
                            "is_error": False,
                            "content": [{"Text": "3 passed"}],
                            "output": None,
                        }
                    },
                    "reasoning_details": None,
                }
            },
            "Resume",
            {"Compaction": {"Summary": "ran the tests"}},
        ],
    }


def zed_blob(record):
    """(data_type, data): zstd-compressed JSON, as Zed writes it."""
    raw = json.dumps(record).encode("utf-8")
    return "zstd", zstandard.ZstdCompressor(level=3).compress(raw)


def build_zed(home: Path) -> None:
    data = home / ".local/share/zed"
    (data / "threads").mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(data / "threads/threads.db"))
    con.executescript("""
    CREATE TABLE threads (id TEXT PRIMARY KEY, summary TEXT NOT NULL, updated_at TEXT NOT NULL,
      data_type TEXT NOT NULL, data BLOB NOT NULL);
    ALTER TABLE threads ADD COLUMN parent_id TEXT;
    ALTER TABLE threads ADD COLUMN folder_paths TEXT;
    ALTER TABLE threads ADD COLUMN folder_paths_order TEXT;
    ALTER TABLE threads ADD COLUMN created_at TEXT;
    """)
    dtype, blob = zed_blob(zed_thread_record())
    con.execute(
        "INSERT INTO threads(id,parent_id,folder_paths,folder_paths_order,summary,updated_at,data_type,data,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            ZED_THREAD,
            None,
            "/srv/proj",
            "0",
            "Fix flaky test",
            "2026-10-03T09:01:05.000000000+00:00",
            dtype,
            blob,
            "2026-10-03T09:00:00.000000000+00:00",
        ),
    )
    con.commit()
    con.close()
    (data / "db/0-stable").mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(data / "db/0-stable/db.sqlite"))
    con.executescript("""
    CREATE TABLE sidebar_threads(thread_id BLOB PRIMARY KEY, session_id TEXT, agent_id TEXT, title TEXT NOT NULL,
      updated_at TEXT NOT NULL, created_at TEXT, folder_paths TEXT, folder_paths_order TEXT, archived INTEGER DEFAULT 0,
      main_worktree_paths TEXT, main_worktree_paths_order TEXT, remote_connection TEXT);
    ALTER TABLE sidebar_threads ADD COLUMN interacted_at TEXT;
    ALTER TABLE sidebar_threads ADD COLUMN title_override TEXT;
    """)
    con.execute(
        "INSERT INTO sidebar_threads(thread_id,session_id,agent_id,title,updated_at,created_at,folder_paths,"
        "folder_paths_order,archived) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            os.urandom(16),
            ZED_THREAD,
            None,
            "Fix flaky test",
            "2026-10-03T09:01:05+00:00",
            "2026-10-03T09:00:00+00:00",
            "/srv/proj",
            "0",
            0,
        ),
    )
    con.execute(
        "INSERT INTO sidebar_threads(thread_id,session_id,agent_id,title,updated_at,folder_paths,folder_paths_order) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            os.urandom(16),
            ZED_EXTERNAL,
            "claude-code",
            "External thread",
            "2026-10-03T10:00:00+00:00",
            "/srv/proj",
            "0",
        ),
    )
    con.commit()
    con.close()
    (home / ".config/zed").mkdir(parents=True, exist_ok=True)
    (home / ".config/zed/settings.json").write_text(
        '{"agent": {"default_model": {}}}', encoding="utf-8"
    )


VSCODE_SESSION = "9ab0c1d2-0000-4000-8000-00000000c0de"
VSCODE_LEGACY_SESSION = "9ab0c1d2-0000-4000-8000-0000000001d0"
VSCODE_T0 = 1791025200000  # 2026-10-03T11:00:00Z, ms
VSCODE_WS = ".config/Code/User/workspaceStorage/abc123"


def vscode_log_records(cwd="/srv/proj"):
    """A `chatSessions/<id>.jsonl` mutation log, as in analyzer/research/vscode.md.
    The modelId, agent id and responder strings come from the closed Copilot
    extension and are invented."""
    t = VSCODE_T0
    return [
        {
            "kind": 0,
            "v": {
                "version": 3,
                "creationDate": t,
                "customTitle": None,
                "initialLocation": "panel",
                "responderUsername": "GitHub Copilot",
                "sessionId": VSCODE_SESSION,
                "requests": [
                    {
                        "requestId": "request_1",
                        "timestamp": t + 1000,
                        "message": {"text": "run tests", "parts": []},
                        "agent": {
                            "id": "github.copilot.default",
                            "name": "GitHub Copilot",
                            "extensionId": {"value": "GitHub.copilot-chat"},
                        },
                        "modelId": "copilot/gpt-4.1",
                        "modeInfo": {
                            "kind": "agent",
                            "telemetryModeId": "agent",
                            "isBuiltin": True,
                        },
                        "variableData": {
                            "variables": [
                                {
                                    "id": "file://%s/test_a.py" % cwd,
                                    "name": "test_a.py",
                                    "value": "...",
                                }
                            ]
                        },
                        "response": [
                            {"kind": "thinking", "value": "Need pytest", "id": "t1"},
                            {
                                "kind": "toolInvocationSerialized",
                                "toolCallId": "call_a",
                                "toolId": "run_in_terminal",
                                "invocationMessage": "Running command",
                                "isComplete": True,
                                # ConfirmedReason, ToolConfirmKind.UserAction = 4 (1.104+)
                                "isConfirmed": {"type": 4, "selectedButton": "Allow"},
                                "source": {"type": "internal", "label": "Built-In"},
                                "toolSpecificData": {
                                    "kind": "terminal",
                                    "commandLine": {"original": "pytest"},
                                },
                                "resultDetails": {
                                    "input": "pytest",
                                    "output": [{"type": "embed", "value": "3 passed"}],
                                },
                            },
                            {"value": "All tests pass in "},
                            {
                                "kind": "inlineReference",
                                "inlineReference": {"scheme": "file", "path": cwd + "/test_a.py"},
                                "name": "test_a.py",
                            },
                            {"value": "."},
                        ],
                        "responseId": "response_1",
                        "responseTimestamp": t + 2000,
                        "modelState": {"value": "complete"},
                    }
                ],
                "workingDirectory": "file://%s" % cwd,
            },
        },
        {
            "kind": 2,
            "k": ["requests"],
            "v": [
                {
                    "requestId": "request_2",
                    "timestamp": t + 10000,
                    "message": {"text": "thanks", "parts": []},
                    "variableData": {"variables": []},
                    "modelId": "copilot/gpt-4.1",
                    "response": [],
                }
            ],
        },
        {
            "kind": 2,
            "k": ["requests", 1, "response"],
            "v": [
                {"value": "You're welcome."},
                {
                    "kind": "confirmation",
                    "title": "Run npm install?",
                    "message": {"value": "This installs the packages."},
                    "data": {},
                    "buttons": ["Allow", "Dismiss"],
                    "isUsed": True,
                },
            ],
        },
        {"kind": 1, "k": ["requests", 1, "responseTimestamp"], "v": t + 11000},
        {"kind": 1, "k": ["customTitle"], "v": "Run tests"},
        {
            # The button click sends a request whose `confirmation` is its label;
            # the user also switched model and mode.
            "kind": 2,
            "k": ["requests"],
            "v": [
                {
                    "requestId": "request_3",
                    "timestamp": t + 20000,
                    "message": {"text": 'Allow: "Run npm install?"', "parts": []},
                    "variableData": {"variables": []},
                    "confirmation": "Allow",
                    "modelId": "copilot/claude-sonnet-4",
                    "modeInfo": {"kind": "ask", "telemetryModeId": "ask", "isBuiltin": True},
                    "response": [{"value": "Installed."}],
                    "responseTimestamp": t + 21000,
                }
            ],
        },
    ]


def vscode_legacy_session(cwd="/srv/proj"):
    """A pre-1.109 flat `.json` session from an empty window on a remote host."""
    t = VSCODE_T0 - 3600000
    return {
        "version": 3,
        "sessionId": VSCODE_LEGACY_SESSION,
        "creationDate": t,
        "initialLocation": "panel",
        "responderUsername": "GitHub Copilot",
        "workingDirectory": "file://%s" % cwd,
        "requests": [
            {
                "requestId": "request_1",
                "timestamp": t + 1000,
                "message": "where is the config?",
                "modelId": "copilot/gpt-4o",
                "response": ["It is in ", "config.toml."],
                "responseTimestamp": t + 2000,
                "result": {"errorDetails": {"message": "Rate limited"}},
            }
        ],
    }


def build_vscode(home: Path) -> None:
    ws = home / VSCODE_WS
    _jsonl(ws / "chatSessions" / (VSCODE_SESSION + ".jsonl"), vscode_log_records())
    (ws / "workspace.json").write_text(json.dumps({"folder": "file:///srv/proj"}), encoding="utf-8")
    (home / ".config/Code/User/settings.json").write_text(
        '{"chat.useLogSessionStorage": true}', encoding="utf-8"
    )
    legacy = home / ".vscode-server/data/User/globalStorage/emptyWindowChatSessions"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / (VSCODE_LEGACY_SESSION + ".json")).write_text(
        json.dumps(vscode_legacy_session(), indent=2), encoding="utf-8"
    )


# ---- OpenCode and Kilo Code ---------------------------------------------------------
# Shapes from analyzer/research/opencode.md and kilo-code.md (drizzle tables in
# packages/core/src/session/sql.ts, JSON in packages/schema/src/v1/session.ts).

OPENCODE_SESSION = "ses_01OC"
OPENCODE_V2_SESSION = "ses_02OCV2"
OPENCODE_LEGACY_SESSION = "ses_00LEGACY"
OPENCODE_T0 = 1791018000000  # 2026-10-03T09:00:00Z, ms
KILO_SESSION = "ses_01JAX"
KILO_TASK = "8f1c2b7e-1"
KILO_T0 = 1791021600000  # 2026-10-03T10:00:00Z, ms

OPENCODE_SCHEMA = """
CREATE TABLE project (id text PRIMARY KEY, worktree text NOT NULL, vcs text, name text, icon_url text, icon_color text,
  time_created integer NOT NULL, time_updated integer NOT NULL, time_initialized integer, sandboxes text NOT NULL);
CREATE TABLE session (id text PRIMARY KEY, project_id text NOT NULL, workspace_id text, parent_id text, slug text NOT NULL,
  directory text NOT NULL, path text, title text NOT NULL, version text NOT NULL, share_url text, summary_additions integer,
  summary_deletions integer, summary_files integer, summary_diffs text, metadata text, cost real, tokens_input integer,
  tokens_output integer, tokens_reasoning integer, tokens_cache_read integer, tokens_cache_write integer, revert text,
  permission text, agent text, model text, time_created integer NOT NULL, time_updated integer NOT NULL,
  time_compacting integer, time_archived integer);
CREATE TABLE message (id text PRIMARY KEY, session_id text NOT NULL, time_created integer NOT NULL,
  time_updated integer NOT NULL, data text NOT NULL);
CREATE TABLE part (id text PRIMARY KEY, message_id text NOT NULL, session_id text NOT NULL, time_created integer NOT NULL,
  time_updated integer NOT NULL, data text NOT NULL);
CREATE INDEX part_message_id_id_idx ON part (message_id, id);
CREATE TABLE session_message (id text PRIMARY KEY, session_id text NOT NULL, type text NOT NULL, seq integer NOT NULL,
  time_created integer NOT NULL, time_updated integer NOT NULL, data text NOT NULL);
CREATE TABLE credential (id text PRIMARY KEY, provider_id text, type text, name text, value text NOT NULL, account_id text,
  workspace_id text, active integer, time_created integer NOT NULL, time_updated integer NOT NULL);
"""


def _oc_session(con, sid, project_id, directory, title, t, parent=None, model=None):
    con.execute(
        "INSERT INTO session (id, project_id, parent_id, slug, directory, title, version, agent, model, "
        "time_created, time_updated) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            sid,
            project_id,
            parent,
            title.lower().replace(" ", "-"),
            directory,
            title,
            "1.2.0",
            "build",
            json.dumps(model) if model else None,
            t,
            t + 5000,
        ),
    )


def _oc_message(con, mid, sid, t, data):
    con.execute("INSERT INTO message VALUES (?,?,?,?,?)", (mid, sid, t, t, json.dumps(data)))


def _oc_part(con, pid, mid, sid, t, data):
    con.execute("INSERT INTO part VALUES (?,?,?,?,?,?)", (pid, mid, sid, t, t, json.dumps(data)))


def opencode_assistant(t, cwd="/srv/proj", model="claude-sonnet-4", **extra):
    d = {
        "role": "assistant",
        "time": {"created": t, "completed": t + 3000},
        "parentID": "msg_01",
        "modelID": model,
        "providerID": "anthropic",
        "mode": "build",
        "agent": "build",
        "path": {"cwd": cwd, "root": cwd},
        "cost": 0.01,
        "tokens": {"input": 10, "output": 5, "reasoning": 0, "cache": {"read": 0, "write": 0}},
    }
    d.update(extra)
    return d


def build_opencode_db(db: Path, t0: int = OPENCODE_T0) -> None:
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db))
    con.executescript(OPENCODE_SCHEMA)
    con.execute(
        "INSERT INTO project (id, worktree, vcs, time_created, time_updated, sandboxes) VALUES (?,?,?,?,?,?)",
        ("proj_a1", "/srv/proj", "git", t0, t0, "[]"),
    )
    _oc_session(con, OPENCODE_SESSION, "proj_a1", "/srv/proj", "Fix bug", t0)
    _oc_message(
        con,
        "msg_01",
        OPENCODE_SESSION,
        t0 + 1000,
        {
            "role": "user",
            "time": {"created": t0 + 1000},
            "agent": "build",
            "model": {"providerID": "anthropic", "modelID": "claude-sonnet-4"},
        },
    )
    _oc_part(
        con, "prt_01", "msg_01", OPENCODE_SESSION, t0 + 1000, {"type": "text", "text": "list files"}
    )
    _oc_part(
        con,
        "prt_01b",
        "msg_01",
        OPENCODE_SESSION,
        t0 + 1000,
        {"type": "text", "text": "<system-reminder>plan mode</system-reminder>", "synthetic": True},
    )
    _oc_message(con, "msg_02", OPENCODE_SESSION, t0 + 2000, opencode_assistant(t0 + 2000))
    _oc_part(
        con,
        "prt_02",
        "msg_02",
        OPENCODE_SESSION,
        t0 + 2000,
        {"type": "step-start", "snapshot": "abc123"},
    )
    _oc_part(
        con,
        "prt_03",
        "msg_02",
        OPENCODE_SESSION,
        t0 + 2100,
        {
            "type": "reasoning",
            "text": "user wants a listing",
            "time": {"start": t0 + 2100, "end": t0 + 2200},
        },
    )
    _oc_part(
        con,
        "prt_04",
        "msg_02",
        OPENCODE_SESSION,
        t0 + 2500,
        {
            "type": "tool",
            "callID": "call_x1",
            "tool": "bash",
            "state": {
                "status": "completed",
                "input": {"command": "ls"},
                "output": "a.txt",
                "title": "ls",
                "metadata": {},
                "time": {"start": t0 + 2500, "end": t0 + 3000},
            },
        },
    )
    _oc_part(
        con,
        "prt_05",
        "msg_02",
        OPENCODE_SESSION,
        t0 + 3500,
        {
            "type": "text",
            "text": "There is one file, a.txt.",
            "time": {"start": t0 + 3500, "end": t0 + 3600},
        },
    )
    _oc_part(
        con,
        "prt_06",
        "msg_02",
        OPENCODE_SESSION,
        t0 + 4000,
        {
            "type": "step-finish",
            "reason": "stop",
            "cost": 0.01,
            "tokens": {"input": 10, "output": 5, "reasoning": 0, "cache": {"read": 0, "write": 0}},
        },
    )
    # A session present only in the V2 session_message projection.
    _oc_session(con, OPENCODE_V2_SESSION, "proj_a1", "/srv/proj", "Run tests", t0 + 10000)
    con.execute(
        "INSERT INTO session_message VALUES (?,?,?,?,?,?,?)",
        (
            "msg_v2u",
            OPENCODE_V2_SESSION,
            "user",
            1,
            t0 + 11000,
            t0 + 11000,
            json.dumps({"id": "msg_v2u", "time": {"created": t0 + 11000}, "text": "run the tests"}),
        ),
    )
    con.execute(
        "INSERT INTO session_message VALUES (?,?,?,?,?,?,?)",
        (
            "msg_v2a",
            OPENCODE_V2_SESSION,
            "assistant",
            2,
            t0 + 12000,
            t0 + 14000,
            json.dumps(
                {
                    "id": "msg_v2a",
                    "agent": "build",
                    "model": {"id": "gpt-5", "providerID": "openai"},
                    "content": [
                        {"type": "text", "id": "c1", "text": "Running them."},
                        {
                            "type": "tool",
                            "id": "call_v2",
                            "name": "bash",
                            "state": {
                                "status": "completed",
                                "input": {"command": "pytest -q"},
                                "content": [{"type": "text", "text": "3 passed"}],
                                "structured": {},
                            },
                            "time": {"created": t0 + 12500, "completed": t0 + 13000},
                        },
                    ],
                    "time": {"created": t0 + 12000, "completed": t0 + 14000},
                }
            ),
        ),
    )
    # Switch records (packages/schema/src/session-message.ts AgentSwitched and
    # ModelSwitched at 907b3bc): `id` and `type` are columns, `data` keeps the rest.
    con.execute(
        "INSERT INTO session_message VALUES (?,?,?,?,?,?,?)",
        (
            "msg_v2s1",
            OPENCODE_V2_SESSION,
            "agent-switched",
            3,
            t0 + 15000,
            t0 + 15000,
            json.dumps({"time": {"created": t0 + 15000}, "agent": "plan"}),
        ),
    )
    con.execute(
        "INSERT INTO session_message VALUES (?,?,?,?,?,?,?)",
        (
            "msg_v2s2",
            OPENCODE_V2_SESSION,
            "model-switched",
            4,
            t0 + 16000,
            t0 + 16000,
            json.dumps(
                {
                    "time": {"created": t0 + 16000},
                    "model": {"id": "gpt-5-mini", "providerID": "openai"},
                }
            ),
        ),
    )
    con.execute(
        "INSERT INTO credential (id, provider_id, type, name, value, active, time_created, time_updated) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (
            "cred_01",
            "anthropic",
            "key",
            "my key",
            '{"type":"key","key":"sk-ant-REDACT"}',
            1,
            t0,
            t0,
        ),
    )
    con.commit()
    con.close()


def _json_file(path: Path, record) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def build_opencode_storage(storage: Path, t0: int = OPENCODE_T0 - 86400000) -> None:
    """The legacy JSON tree: ids inline, one file per record."""
    sid = OPENCODE_LEGACY_SESSION
    _json_file(
        storage / "project/proj_a1.json",
        {"id": "proj_a1", "vcs": "git", "worktree": "/srv/proj", "time": {"created": t0}},
    )
    _json_file(
        storage / "session/proj_a1" / (sid + ".json"),
        {
            "id": sid,
            "projectID": "proj_a1",
            "directory": "/srv/proj",
            "title": "Old session",
            "version": "0.9.0",
            "time": {"created": t0, "updated": t0 + 5000},
        },
    )
    _json_file(
        storage / "message" / sid / "msg_a.json",
        {
            "id": "msg_a",
            "sessionID": sid,
            "role": "user",
            "time": {"created": t0 + 1000},
            "agent": "build",
            "model": {"providerID": "anthropic", "modelID": "claude-sonnet-4"},
        },
    )
    _json_file(
        storage / "part/msg_a/prt_a1.json",
        {
            "id": "prt_a1",
            "sessionID": sid,
            "messageID": "msg_a",
            "type": "text",
            "text": "cat the secrets file",
        },
    )
    _json_file(
        storage / "message" / sid / "msg_b.json",
        dict(
            opencode_assistant(t0 + 2000),
            id="msg_b",
            sessionID=sid,
            error={"name": "APIError", "data": {"message": "overloaded"}},
        ),
    )
    _json_file(
        storage / "part/msg_b/prt_b1.json",
        {
            "id": "prt_b1",
            "sessionID": sid,
            "messageID": "msg_b",
            "type": "tool",
            "callID": "call_r1",
            "tool": "read",
            "state": {
                "status": "error",
                "input": {"filePath": "/srv/proj/.env"},
                "error": "permission denied",
                "time": {"start": t0 + 2500, "end": t0 + 2600},
            },
        },
    )
    _json_file(
        storage / "part/msg_b/prt_b2.json",
        {
            "id": "prt_b2",
            "sessionID": sid,
            "messageID": "msg_b",
            "type": "text",
            "text": "I could not read it.",
            "time": {"start": t0 + 2700},
        },
    )
    (storage / "migration").write_text("2", encoding="utf-8")


def build_opencode(home: Path) -> None:
    data = home / ".local/share/opencode"
    build_opencode_db(data / "opencode.db")
    build_opencode_storage(data / "storage")
    (data / "auth.json").write_text(
        '{"anthropic":{"type":"api","key":"sk-ant-REDACT"}}', encoding="utf-8"
    )
    _json_file(
        home / ".config/opencode/opencode.json", {"$schema": "https://opencode.ai/config.json"}
    )


def kilo_task_records(t0: int = KILO_T0 - 86400000):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "<task>fix tests</task>"},
                {
                    "type": "text",
                    "text": "<environment_details>cwd /srv/proj</environment_details>",
                },
            ],
            "ts": t0 + 1000,
        },
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Running the suite."},
                {
                    "type": "tool_use",
                    "id": "toolu_01A",
                    "name": "execute_command",
                    "input": {"command": "pytest -q"},
                },
            ],
            "ts": t0 + 2000,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01A",
                    "content": "3 passed",
                    "is_error": False,
                }
            ],
            "ts": t0 + 3000,
        },
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "tests pass"}],
            "ts": t0 + 3500,
        },
        {"role": "assistant", "content": "All three tests pass.", "ts": t0 + 4000},
    ]


def build_kilo(home: Path) -> None:
    data = home / ".local/share/kilo"
    db = data / "kilo.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db))
    con.executescript(OPENCODE_SCHEMA)
    t0 = KILO_T0
    con.execute(
        "INSERT INTO project (id, worktree, vcs, time_created, time_updated, sandboxes) VALUES (?,?,?,?,?,?)",
        ("prj_01JAX", "/srv/proj", "git", t0, t0, "[]"),
    )
    _oc_session(
        con,
        KILO_SESSION,
        "prj_01JAX",
        "/srv/proj",
        "fix tests",
        t0,
        model={"id": "claude-sonnet-4-5", "providerID": "anthropic"},
    )
    _oc_message(
        con,
        "msg_01JAXU",
        KILO_SESSION,
        t0 + 1000,
        {
            "role": "user",
            "time": {"created": t0 + 1000},
            "agent": "build",
            "model": {"providerID": "anthropic", "modelID": "claude-sonnet-4-5"},
        },
    )
    _oc_part(
        con,
        "prt_01JAXP",
        "msg_01JAXU",
        KILO_SESSION,
        t0 + 1000,
        {"type": "text", "text": "fix the tests"},
    )
    _oc_message(
        con,
        "msg_01JAXA",
        KILO_SESSION,
        t0 + 2000,
        dict(opencode_assistant(t0 + 2000, model="claude-sonnet-4-5"), parentID="msg_01JAXU"),
    )
    _oc_part(
        con,
        "prt_01JAXT",
        "msg_01JAXA",
        KILO_SESSION,
        t0 + 2500,
        {
            "type": "tool",
            "callID": "call_1",
            "tool": "bash",
            "state": {
                "status": "completed",
                "input": {"command": "pytest -q"},
                "output": "3 passed",
                "title": "pytest -q",
                "metadata": {},
                "time": {"start": t0 + 2500, "end": t0 + 3000},
            },
        },
    )
    # A later turn the user sent with another model and the plan agent.
    _oc_message(
        con,
        "msg_01JAXV",
        KILO_SESSION,
        t0 + 4000,
        {
            "role": "user",
            "time": {"created": t0 + 4000},
            "agent": "plan",
            "model": {"providerID": "openai", "modelID": "gpt-5"},
        },
    )
    _oc_part(
        con,
        "prt_01JAXQ",
        "msg_01JAXV",
        KILO_SESSION,
        t0 + 4000,
        {"type": "text", "text": "plan the next fix"},
    )
    # Kilo writes the V2 projection alongside V1; it must not duplicate the rows.
    con.execute(
        "INSERT INTO session_message VALUES (?,?,?,?,?,?,?)",
        (
            "msg_01JAXB",
            KILO_SESSION,
            "assistant",
            4,
            t0 + 2000,
            t0 + 3000,
            json.dumps(
                {
                    "agent": "build",
                    "model": {"providerID": "anthropic", "modelID": "claude-sonnet-4-5"},
                    "content": [
                        {
                            "type": "tool",
                            "id": "call_1",
                            "name": "bash",
                            "state": {
                                "status": "completed",
                                "input": {"command": "pytest -q"},
                                "content": [{"type": "text", "text": "3 passed"}],
                                "structured": {},
                            },
                            "time": {"created": t0 + 2500, "completed": t0 + 3000},
                        }
                    ],
                    "time": {"created": t0 + 2000, "completed": t0 + 3000},
                }
            ),
        ),
    )
    con.commit()
    con.close()
    (data / "auth.json").write_text('{"kilo":{"type":"oauth","access":"REDACT"}}', encoding="utf-8")
    tasks = home / ".config/Code/User/globalStorage/kilocode.kilo-code/tasks"
    task = tasks / KILO_TASK
    task.mkdir(parents=True, exist_ok=True)
    (task / "api_conversation_history.json").write_text(
        json.dumps(kilo_task_records()), encoding="utf-8"
    )
    (task / "ui_messages.json").write_text("[]", encoding="utf-8")
    _json_file(
        tasks / "_index.json",
        {
            "version": 1,
            "updatedAt": KILO_T0 - 86395000,
            "entries": [
                {
                    "id": KILO_TASK,
                    "number": 1,
                    "ts": KILO_T0 - 86400000,
                    "task": "fix tests",
                    "tokensIn": 1200,
                    "tokensOut": 80,
                    "totalCost": 0.0041,
                    "workspace": "/srv/proj",
                    "mode": "code",
                    "status": "completed",
                }
            ],
        },
    )


# ---- Cline and Roo Code (research/cline.md, research/roo-code.md) ----------------

CLINE_TASK = "1791021600000"  # 2026-10-03T10:00:00Z, a Date.now() id
CLINE_CLI_TASK = "1791021300000"  # API history only, no ui_messages.json
CLINE_SESSION = "1791021700000_k3x9q"
CLINE_OLD_SESSION = "1791000000000_old01"
ROO_TASK = "8f1c2b7e-0000-4000-8000-000000000001"
ROO_CLI_TASK = "8f1c2b7e-0000-4000-8000-000000000002"
ROO_GONE_TASK = "8f1c2b7e-0000-4000-8000-000000000003"
CLINE_T0 = 1791021600000


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def cline_ui_records(t0=CLINE_T0):
    model = {"modelId": "claude-sonnet-4-5", "providerId": "anthropic", "mode": "act"}
    return [
        {
            "ts": t0,
            "type": "say",
            "say": "task",
            "text": "fix tests",
            "images": ["data:image/png;base64,AAAA"],
        },
        {
            "ts": t0 + 1000,
            "type": "say",
            "say": "api_req_started",
            "text": json.dumps(
                {
                    "request": "<task>fix tests</task>",
                    "tokensIn": 1200,
                    "tokensOut": 80,
                    "cacheWrites": 0,
                    "cacheReads": 900,
                    "cost": 0.0041,
                }
            ),
        },
        {
            "ts": t0 + 1500,
            "type": "say",
            "say": "reasoning",
            "text": "read the test first",
            "partial": False,
        },
        {
            "ts": t0 + 2000,
            "type": "say",
            "say": "tool",
            "modelInfo": model,
            "text": json.dumps(
                {"tool": "readFile", "path": "src/app.py", "content": "/srv/proj/src/app.py"}
            ),
        },
        {
            "ts": t0 + 3000,
            "type": "say",
            "say": "text",
            "text": "Running the suite.",
            "modelInfo": model,
        },
        {"ts": t0 + 4000, "type": "ask", "ask": "command", "text": "pytest -q", "modelInfo": model},
        {"ts": t0 + 5000, "type": "say", "say": "command_output", "text": "3 passed"},
        {
            "ts": t0 + 6000,
            "type": "say",
            "say": "checkpoint_created",
            "lastCheckpointHash": "abc123",
        },
        {
            "ts": t0 + 7000,
            "type": "say",
            "say": "completion_result",
            "text": "All tests pass.",
            "modelInfo": model,
        },
        {"ts": t0 + 7001, "type": "ask", "ask": "completion_result", "text": ""},
    ]


def cline_api_records():
    return [
        {"role": "user", "content": [{"type": "text", "text": "<task>fix tests</task>"}]},
        {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "run the suite"},
                {
                    "type": "tool_use",
                    "id": "toolu_01A",
                    "name": "execute_command",
                    "input": {"command": "pytest -q"},
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01A",
                    "content": "3 passed",
                    "is_error": False,
                }
            ],
        },
    ]


def cline_task_metadata(t0=CLINE_T0):
    return {
        "files_in_context": [
            {
                "path": "src/app.py",
                "record_state": "active",
                "record_source": "read_tool",
                "cline_read_date": t0 + 2000,
                "cline_edit_date": None,
            },
        ],
        "model_usage": [
            {
                "ts": t0 + 300,
                "model_id": "claude-sonnet-4-5",
                "model_provider_id": "anthropic",
                "mode": "plan",
            },
            {
                "ts": t0 + 500,
                "model_id": "claude-sonnet-4-5",
                "model_provider_id": "anthropic",
                "mode": "act",
            },
            {
                "ts": t0 + 8000,
                "model_id": "claude-opus-4-5",
                "model_provider_id": "anthropic",
                "mode": "act",
            },
        ],
        "environment_history": [
            {
                "ts": t0 + 100,
                "os_name": "linux",
                "os_version": "6.6",
                "os_arch": "x64",
                "host_name": "Visual Studio Code",
                "host_version": "1.105.0",
                "cline_version": "3.40.0",
            }
        ],
    }


def cline_history_items():
    return [
        {
            "id": CLINE_TASK,
            "ulid": "01JAX3Q8M4",
            "ts": CLINE_T0 + 7001,
            "task": "fix tests",
            "tokensIn": 1200,
            "tokensOut": 80,
            "totalCost": 0.0041,
            "cwdOnTaskInitialization": "/srv/proj",
            "modelId": "claude-sonnet-4-5",
            "apiProvider": "anthropic",
        },
    ]


def cline_sdk_manifest():
    return {
        "version": 1,
        "session_id": CLINE_SESSION,
        "source": "cli",
        "pid": 4242,
        "started_at": "2026-10-03T10:01:40.000Z",
        "ended_at": "2026-10-03T10:01:50.000Z",
        "exit_code": 0,
        "status": "completed",
        "interactive": True,
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "cwd": "/srv/proj",
        "workspace_root": "/srv/proj",
        "enable_tools": True,
        "enable_spawn": False,
        "enable_teams": False,
        "prompt": "fix tests",
        "metadata": {"title": "fix tests"},
        "messages_path": "/home/u/.cline/data/sessions/%s/%s.messages.json"
        % (CLINE_SESSION, CLINE_SESSION),
    }


def cline_sdk_messages(t0=CLINE_T0 + 100000):
    return {
        "version": 1,
        "updated_at": "2026-10-03T10:01:50.000Z",
        "agent": "lead",
        "sessionId": CLINE_SESSION,
        "origin": {"source": "cli", "mode": "user", "sessionId": CLINE_SESSION},
        "system_prompt": "You are Cline.",
        "messages": [
            {"id": "m1", "role": "user", "content": "fix tests", "ts": t0},
            {
                "id": "m2",
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "run the suite"},
                    {
                        "type": "tool_use",
                        "id": "call_1",
                        "name": "bash",
                        "input": {"command": "pytest -q"},
                    },
                ],
                "modelInfo": {"id": "claude-sonnet-4-5", "provider": "anthropic"},
                "metrics": {"inputTokens": 1200, "outputTokens": 80, "cost": 0.0041},
                "ts": t0 + 2000,
            },
            {
                "id": "m3",
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "call_1",
                        "name": "bash",
                        "content": "3 passed",
                        "is_error": False,
                    }
                ],
                "ts": t0 + 3000,
            },
            {
                "id": "m4",
                "role": "assistant",
                "content": [{"type": "text", "text": "Fixed."}],
                "modelInfo": {"id": "claude-opus-4-5", "provider": "anthropic"},
            },
        ],
    }


def build_cline(home: Path) -> None:
    gs = home / ".config/Code/User/globalStorage/saoudrizwan.claude-dev"
    task = gs / "tasks" / CLINE_TASK
    _json(task / "ui_messages.json", cline_ui_records())
    _json(task / "api_conversation_history.json", cline_api_records())
    _json(task / "task_metadata.json", cline_task_metadata())
    _json(gs / "state/taskHistory.json", cline_history_items())
    _json(gs / "settings/cline_mcp_settings.json", {"mcpServers": {}})
    data = home / ".cline/data"
    _json(data / "tasks" / CLINE_CLI_TASK / "api_conversation_history.json", cline_api_records())
    _json(
        data / "state/taskHistory.json",
        [dict(cline_history_items()[0], id=CLINE_CLI_TASK, ts=1791021305000)],
    )
    _json(data / "secrets.json", {"apiKey": "sk-not-real"})
    sess = data / "sessions" / CLINE_SESSION
    _json(sess / (CLINE_SESSION + ".json"), cline_sdk_manifest())
    _json(sess / (CLINE_SESSION + ".messages.json"), cline_sdk_messages())
    _json(sess / (CLINE_SESSION + ".compaction.json"), {"version": 1})
    (data / "db").mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(data / "db/sessions.db"))
    con.execute(
        "CREATE TABLE sessions (session_id TEXT PRIMARY KEY, source TEXT, pid INTEGER, started_at TEXT, "
        "ended_at TEXT, exit_code INTEGER, status TEXT, interactive INTEGER, provider TEXT, model TEXT, "
        "cwd TEXT, workspace_root TEXT, prompt TEXT, metadata_json TEXT, is_subagent INTEGER, "
        "parent_session_id TEXT, updated_at TEXT)"
    )
    for sid, started, prompt in (
        (CLINE_SESSION, "2026-10-03T10:01:40.000Z", "fix tests"),
        (CLINE_OLD_SESSION, "2026-10-02T23:00:00.000Z", "an older deleted session"),
    ):
        con.execute(
            "INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                sid,
                "cli",
                4242,
                started,
                None,
                None,
                "completed",
                1,
                "anthropic",
                "claude-sonnet-4-5",
                "/srv/proj",
                "/srv/proj",
                prompt,
                json.dumps({"title": prompt}),
                0,
                None,
                started,
            ),
        )
    con.commit()
    con.close()


def cline_search_text(message: dict) -> str:
    """A message as session-search.db indexes it: every string value under
    `content`, skipping the `data`, `image`, `images`, `reasoning`,
    `thinking` and `metadata` keys, joined with line breaks
    (session-history-search.ts:54-95 at 39ff2359)."""
    parts: list[str] = []

    def walk(value) -> None:
        if isinstance(value, str):
            if value:
                parts.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                if key not in ("data", "image", "images", "reasoning", "thinking", "metadata"):
                    walk(item)

    walk(message.get("content", message))
    return "\n".join(parts).strip()


def cline_session_search_sessions():
    """(session id, started_at, workspace_root, title, prompt, messages) per
    indexed session: the fixture's SDK session, whose transcript is on disk,
    and the older session whose manifest and transcript are gone."""
    return [
        (
            CLINE_SESSION,
            "2026-10-03T10:01:40.000Z",
            "/srv/proj",
            "fix tests",
            "fix tests",
            cline_sdk_messages()["messages"],
        ),
        (
            CLINE_OLD_SESSION,
            "2026-10-02T23:00:00.000Z",
            "/srv/proj",
            "an older deleted session",
            "an older deleted session",
            [
                {"role": "user", "content": "prune the stale branches"},
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Deleted two branches."}],
                },
            ],
        ),
    ]


CLINE_SEARCH_FTS = (
    "CREATE VIRTUAL TABLE session_search USING fts5(session_id UNINDEXED, document_id "
    "UNINDEXED, ordinal UNINDEXED, role UNINDEXED, started_at UNINDEXED, workspace_root, "
    "title, content, tokenize='unicode61 remove_diacritics 2 tokenchars ''_-@''')"
)


def build_cline_session_search(home: Path) -> None:
    """`~/.cline/data/db/session-search.db` as the SDK hub writes it
    (session-history-search.ts:120-154 and 402-465 at 39ff2359), and
    `cron.db` beside it, which the parser must not want."""
    db = home / ".cline/data/db"
    db.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db / "session-search.db"))
    con.execute(
        "CREATE TABLE indexed_sessions (session_id TEXT PRIMARY KEY, source_revision TEXT NOT "
        "NULL, indexed_at TEXT NOT NULL, document_count INTEGER NOT NULL, index_version INTEGER "
        "NOT NULL, title TEXT NOT NULL DEFAULT '')"
    )
    con.execute(CLINE_SEARCH_FTS)
    insert = "INSERT INTO session_search VALUES (?,?,?,?,?,?,?,?)"
    for sid, started, workspace, title, prompt, messages in cline_session_search_sessions():
        con.execute(
            insert, (sid, sid + ":metadata", -1, "session", started, workspace, title, prompt)
        )
        count = 1
        for ordinal, message in enumerate(messages):
            content = cline_search_text(message)
            if not content:
                continue
            con.execute(
                insert,
                (
                    sid,
                    "%s:%d" % (sid, ordinal),
                    ordinal,
                    message.get("role") or "unknown",
                    started,
                    workspace,
                    "",
                    content,
                ),
            )
            count += 1
        con.execute(
            "INSERT INTO indexed_sessions VALUES (?,?,?,?,?,?)",
            (sid, started + ":1024:1791021710000", "2026-10-03T10:02:00.000Z", count, 2, title),
        )
    con.commit()
    con.close()
    con = sqlite3.connect(str(db / "cron.db"))
    con.execute("CREATE TABLE cron_jobs (id TEXT PRIMARY KEY, prompt TEXT)")
    con.commit()
    con.close()


def build_cline_input_history(home: Path) -> None:
    """The CLI's `~/.cline/data/cache/user_input_history.jsonl`
    (apps/cli/src/utils/input-history.ts:54-72 at 39ff2359): every line
    stamped with the last rewrite's time. "fix tests" repeats the SDK
    session's prompt; "list the open ports" has no transcript. A model
    cache beside it is noise the parser must not want."""
    cache = home / ".cline/data/cache"
    cache.mkdir(parents=True, exist_ok=True)
    rewrite = CLINE_T0 + 300000  # 2026-10-03T10:05:00Z
    lines = [{"prompt": p, "ts": rewrite} for p in ("fix tests", "list the open ports")]
    (cache / "user_input_history.jsonl").write_text(
        "".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8"
    )
    _json(cache / "openrouter_models.json", {"anthropic/claude-sonnet-4-5": {}})


# Enterprise prompt upload (#153): `metadata["enterprise.blobUpload"]`
# (sdk/packages/shared/src/remote-config/blob-storage.ts:56-57, 129-160 at
# 39ff2359). CLINE_BLOB_SESSION's manifest has the VS Code host's form, with
# `userDistinctId`; CLINE_BLOB_DELETED survives only as a sessions.db row
# with the CLI's form, without it. Not part of `build_home`: the tests that
# need them add them, so the session counts of the other Cline tests stay.
CLINE_BLOB_SESSION = "1791022000000_b10b5"
CLINE_BLOB_DELETED = "1791021900000_d31e7"


def cline_blob_upload(user: str = "usr_0f9e8d7c"):
    blob: dict = {
        "version": 1,
        "storage": {"adapterType": "s3", "bucket": "acme-cline-prompts", "region": "us-east-1"},
    }
    if user:
        blob["userDistinctId"] = user
    return blob


def build_cline_blob_upload(home: Path) -> None:
    data = home / ".cline/data"
    manifest = dict(
        cline_sdk_manifest(),
        session_id=CLINE_BLOB_SESSION,
        started_at="2026-10-03T10:06:40.000Z",
        ended_at=None,
        prompt="summarise the diff",
        metadata={"title": "summarise the diff", "enterprise.blobUpload": cline_blob_upload()},
    )
    _json(data / "sessions" / CLINE_BLOB_SESSION / (CLINE_BLOB_SESSION + ".json"), manifest)
    blob = dict(
        cline_blob_upload(""),
        storage={
            "adapterType": "r2",
            "bucket": "acme-r2",
            "endpoint": "https://acct.r2.cloudflarestorage.com",
            "accountId": "acct",
        },
    )
    con = sqlite3.connect(str(data / "db/sessions.db"))
    con.execute(
        "INSERT INTO sessions (session_id, source, started_at, status, provider, model, cwd,"
        " workspace_root, prompt, metadata_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            CLINE_BLOB_DELETED,
            "cli",
            "2026-10-03T10:05:00.000Z",
            "completed",
            "anthropic",
            "claude-sonnet-4-5",
            "/srv/proj",
            "/srv/proj",
            "a deleted uploaded session",
            json.dumps({"title": "uploaded", "enterprise.blobUpload": blob}),
        ),
    )
    con.commit()
    con.close()


# The VS Code extension's enterprise prompt upload queue (#153), the
# `SyncQueueItem` shape of apps/vscode/src/shared/services/worker/queue.ts:9-31
# at 39ff2359, one item of each status: CLINE_TASK's transcript uploaded,
# CLINE_QUEUE_PENDING's waiting and CLINE_QUEUE_FAILED's failing. The two
# queued-only tasks have no task directory.
CLINE_QUEUE_PENDING = "1791021700001"
CLINE_QUEUE_FAILED = "1791021700002"
CLINE_SYNC_QUEUE = ".config/Code/User/globalStorage/saoudrizwan.claude-dev/cache/sync-queue.json"
CLINE_SYNC_SECRET = "FULL TASK FILE CONTENT"


def build_cline_sync_queue(home: Path) -> None:
    items = {}
    for task, key, status, retries, ts, error in (
        (CLINE_TASK, "api_conversation_history.json", "synced", 0, CLINE_T0 + 5000, None),
        (CLINE_QUEUE_PENDING, "ui_messages.json", "pending", 0, CLINE_T0 + 5500, None),
        (CLINE_QUEUE_FAILED, "ui_messages.json", "failed", 3, CLINE_T0 + 6000, "403 Forbidden"),
    ):
        items[task + "/" + key] = {
            "id": task + "/" + key,
            "taskId": task,
            "key": key,
            "data": CLINE_SYNC_SECRET,
            "timestamp": ts,
            "status": status,
            "retryCount": retries,
            "lastError": error,
        }
    _json(home / CLINE_SYNC_QUEUE, {"items": items})


def roo_ui_records(t0=CLINE_T0 + 200000):
    return [
        {"ts": t0, "type": "say", "say": "text", "text": "rename the helper"},
        {
            "ts": t0 + 1000,
            "type": "say",
            "say": "api_req_started",
            "text": json.dumps(
                {
                    "request": "rename the helper",
                    "tokensIn": 900,
                    "tokensOut": 40,
                    "cost": 0.002,
                    "apiProtocol": "anthropic",
                }
            ),
        },
        {
            "ts": t0 + 2000,
            "type": "ask",
            "ask": "tool",
            "text": json.dumps(
                {"tool": "appliedDiff", "path": "src/util.py", "diff": "-old\n+new"}
            ),
        },
        {"ts": t0 + 3000, "type": "ask", "ask": "command", "text": "pytest -q"},
        {"ts": t0 + 4000, "type": "ask", "ask": "command_output", "text": "1 passed"},
        {
            "ts": t0 + 5000,
            "type": "say",
            "say": "condense_context",
            "partial": False,
            "contextCondense": {
                "cost": 0.001,
                "prevContextTokens": 9000,
                "newContextTokens": 1200,
                "summary": "Renamed helper; tests pass.",
                "condenseId": "c1",
            },
        },
        {
            "ts": t0 + 6000,
            "type": "ask",
            "ask": "followup",
            "text": json.dumps(
                {"question": "Commit now?", "suggest": [{"answer": "yes"}, {"answer": "no"}]}
            ),
        },
        {"ts": t0 + 7000, "type": "say", "say": "user_feedback", "text": "yes"},
        {
            "ts": t0 + 8000,
            "type": "say",
            "say": "completion_result",
            "text": "Renamed and committed.",
        },
    ]


def roo_api_records(t0=CLINE_T0 + 300000):
    return [
        {"role": "user", "content": [{"type": "text", "text": "<task>fix tests</task>"}], "ts": t0},
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "check the runner"}],
            "encrypted_content": "gAAAA",
            "ts": t0 + 1000,
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_01A",
                    "name": "execute_command",
                    "input": {"command": "pytest -q"},
                }
            ],
            "ts": t0 + 2000,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01A",
                    "content": "3 passed",
                    "is_error": False,
                }
            ],
            "ts": t0 + 3000,
        },
    ]


def roo_history_item(task_id, ts, task, workspace="/srv/proj"):
    return {
        "id": task_id,
        "number": 1,
        "ts": ts,
        "task": task,
        "tokensIn": 1200,
        "tokensOut": 80,
        "totalCost": 0.0041,
        "workspace": workspace,
        "mode": "code",
        "status": "completed",
    }


# The Roo CLI's input history (`.roo/cli-history.json`, issue 122): text
# only, so "rename the helper" and the follow-up "yes" pair with the task's
# own user rows on text alone (any task: the file names none); "/new" (a
# CLI command that never reaches a task) and "summarise the open issues"
# (its task directory is gone) are kept. The number and the blank entry are
# skipped, as the CLI's loadHistory skips them.
ROO_CLI_HISTORY_ENTRIES = [
    "rename the helper",
    "yes",
    "/new",
    42,
    "  ",
    "summarise the open issues",
]


def build_roo_cli_history(home: Path) -> None:
    roo = home / ".roo"
    _json(roo / "cli-history.json", {"version": 1, "entries": ROO_CLI_HISTORY_ENTRIES})
    _json(roo / "cli-settings.json", {"mode": "code", "provider": "anthropic"})


def build_roo_code(home: Path) -> None:
    gs = home / ".config/Code/User/globalStorage/rooveterinaryinc.roo-cline"
    task = gs / "tasks" / ROO_TASK
    _json(task / "ui_messages.json", roo_ui_records())
    _json(task / "api_conversation_history.json", roo_api_records())
    _json(
        task / "history_item.json",
        roo_history_item(ROO_TASK, CLINE_T0 + 208000, "rename the helper"),
    )
    _json(
        task / "task_metadata.json",
        {
            "files_in_context": [
                {
                    "path": "src/util.py",
                    "record_state": "active",
                    "record_source": "roo_edited",
                    "roo_read_date": CLINE_T0 + 202000,
                    "roo_edit_date": CLINE_T0 + 202500,
                    "user_edit_date": None,
                }
            ]
        },
    )
    _json(
        gs / "tasks/_index.json",
        {
            "version": 1,
            "updatedAt": CLINE_T0 + 208000,
            "entries": [
                roo_history_item(ROO_TASK, CLINE_T0 + 208000, "rename the helper"),
                roo_history_item(ROO_GONE_TASK, CLINE_T0 - 3600000, "a task deleted from disk"),
            ],
        },
    )
    mock = home / ".vscode-mock/global-storage"
    _json(mock / "tasks" / ROO_CLI_TASK / "api_conversation_history.json", roo_api_records())
    _json(
        mock / "tasks" / ROO_CLI_TASK / "history_item.json",
        roo_history_item(ROO_CLI_TASK, CLINE_T0 + 303000, "fix tests"),
    )
    _json(mock / "secrets.json", {"roo_cline_config_api_config": '{"apiKey":"sk-not-real"}'})


# Tabby: ee/tabby-db/schema/schema.sql at 21b2904 (research/tabby.md section 3),
# trimmed to the tables the parser reads plus every table that holds a secret,
# so the tests can prove those are never read.
TABBY_SCHEMA = """
CREATE TABLE registration_token(id INTEGER PRIMARY KEY AUTOINCREMENT, token VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT(DATETIME('now')), updated_at TIMESTAMP DEFAULT(DATETIME('now')));
CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, email VARCHAR(150) NOT NULL COLLATE NOCASE,
  is_admin BOOLEAN NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT(DATETIME('now')),
  updated_at TIMESTAMP DEFAULT(DATETIME('now')), auth_token VARCHAR(128) NOT NULL, active BOOLEAN NOT NULL DEFAULT 1,
  password_encrypted VARCHAR(128), avatar BLOB DEFAULT NULL, name VARCHAR(255));
CREATE TABLE refresh_tokens(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
  token VARCHAR(255) NOT NULL COLLATE NOCASE, expires_at TIMESTAMP NOT NULL, created_at TIMESTAMP DEFAULT(DATETIME('now')));
CREATE TABLE integrations(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, display_name TEXT NOT NULL,
  access_token TEXT NOT NULL, api_base TEXT, error TEXT, created_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')),
  updated_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')), synced BOOLEAN NOT NULL DEFAULT FALSE);
CREATE TABLE email_setting(id INTEGER PRIMARY KEY AUTOINCREMENT, smtp_username VARCHAR(255) NOT NULL,
  smtp_password VARCHAR(255) NOT NULL, smtp_server VARCHAR(255) NOT NULL, from_address VARCHAR(255) NOT NULL,
  encryption VARCHAR(255) NOT NULL DEFAULT 'ssltls', auth_method VARCHAR(255) NOT NULL DEFAULT 'plain',
  smtp_port INTEGER NOT NULL DEFAULT 25);
CREATE TABLE oauth_credential(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, provider TEXT NOT NULL,
  client_id VARCHAR(256) NOT NULL, client_secret VARCHAR(64) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')),
  updated_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')), config_url VARCHAR(256), config_scopes VARCHAR(256));
CREATE TABLE ldap_credential(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, host STRING NOT NULL,
  port INTEGER NOT NULL DEFAULT 389, bind_dn STRING NOT NULL, bind_password STRING NOT NULL, base_dn STRING NOT NULL,
  user_filter STRING NOT NULL, encryption STRING NOT NULL DEFAULT 'none', skip_tls_verify BOOLEAN NOT NULL DEFAULT FALSE,
  email_attribute STRING NOT NULL DEFAULT 'email', name_attribute STRING,
  created_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')), updated_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')));
CREATE TABLE user_events(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, kind TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')), payload BLOB NOT NULL);
CREATE TABLE threads(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, is_ephemeral BOOLEAN NOT NULL, user_id INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')), updated_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')),
  relevant_questions BLOB);
CREATE TABLE thread_messages(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, thread_id INTEGER NOT NULL, role TEXT NOT NULL,
  content TEXT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')),
  updated_at TIMESTAMP NOT NULL DEFAULT(DATETIME('now')), code_source_id VARCHAR(255), attachment BLOB NOT NULL DEFAULT '{}');
"""

# One distinct value per plaintext secret column; none may reach any output.
TABBY_SECRETS = (
    "auth_REDACT_tok",
    "pw_hash_REDACT",
    "regtok_REDACT",
    "refresh_REDACT",
    "ghp_REDACT_integration",
    "smtp_REDACT_pw",
    "oauth_REDACT_secret",
    "ldap_REDACT_bind",
)


def tabby_secret_records():
    s = TABBY_SECRETS
    return [
        "INSERT INTO users(id,email,is_admin,auth_token,active,name,password_encrypted) "
        "VALUES(1,'alice@example.com',1,'%s',1,'Alice','%s')" % (s[0], s[1]),
        "INSERT INTO registration_token(id,token) VALUES(1,'%s')" % s[2],
        "INSERT INTO refresh_tokens(user_id,token,expires_at) VALUES(1,'%s','2026-12-01 00:00:00')"
        % s[3],
        "INSERT INTO integrations(kind,display_name,access_token) VALUES('github','acme','%s')"
        % s[4],
        "INSERT INTO email_setting(smtp_username,smtp_password,smtp_server,from_address) "
        "VALUES('mailer','%s','smtp.example.com','tabby@example.com')" % s[5],
        "INSERT INTO oauth_credential(provider,client_id,client_secret) VALUES('github','cid','%s')"
        % s[6],
        "INSERT INTO ldap_credential(host,bind_dn,bind_password,base_dn,user_filter) "
        "VALUES('ldap.example.com','cn=admin','%s','dc=example','(uid=%%s)')" % s[7],
    ]


TABBY_SELECT_PAYLOAD = (
    '{\n  "select": {\n    "completion_id": "cmpl-7f3a",\n    "choice_index": 0,\n'
    '    "view_id": "view-1",\n    "elapsed": 1377\n  }\n}'
)


def tabby_records():
    """The INSERT statements of research/tabby.md section 8, with the
    research's single fixture token replaced by one per secret column, and a
    user_events row whose payload is the pretty JSON event_logger.rs writes."""
    return [
        *tabby_secret_records(),
        "INSERT INTO threads(id,is_ephemeral,user_id,created_at,updated_at,relevant_questions) "
        """VALUES(7,0,1,'2026-10-01 10:00:00','2026-10-01 10:00:09','["How is the cache invalidated?"]')""",
        "INSERT INTO thread_messages(id,thread_id,role,content,created_at,updated_at,attachment) VALUES "
        """(1,7,'user','Where is the cache cleared?','2026-10-01 10:00:00','2026-10-01 10:00:00','{"code":null,"client_code":[{"filepath":"src/cache.rs","start_line":10,"content":"fn clear()"}],"doc":null}'),"""
        """(2,7,'assistant','In `clear()` in src/cache.rs.','2026-10-01 10:00:02','2026-10-01 10:00:09','{"code":[{"git_url":"https://github.com/acme/app","commit":"abc123","language":"rust","filepath":"src/cache.rs","content":"fn clear() {}","start_line":10}],"client_code":null,"doc":null}')""",
        "INSERT INTO user_events(id,user_id,kind,created_at,payload) VALUES(1,1,'select','2026-10-01 10:00:01',"
        "'%s')" % TABBY_SELECT_PAYLOAD,
        # The event log's completion line as the database logger stores it
        # (event_logger.rs:79-109): `ts` truncated to the second (#122).
        "INSERT INTO user_events(id,user_id,kind,created_at,payload) "
        "VALUES(2,1,'completion','2025-10-01 10:00:00','%s')" % TABBY_COMPLETION_PAYLOAD,
    ]


# A pre-0.25 backup: deprecated per-kind attachment columns, no `attachment`,
# and an ephemeral thread the live database has since deleted.
TABBY_BACKUP_SCHEMA = TABBY_SCHEMA.replace(
    "code_source_id VARCHAR(255), attachment BLOB NOT NULL DEFAULT '{}'",
    "code_source_id VARCHAR(255), code_attachments BLOB, client_code_attachments BLOB, doc_attachments BLOB",
)
TABBY_REL = ".tabby/ee/db.sqlite"
TABBY_BACKUP_REL = ".tabby/ee/db.backup-20260915.sqlite"
TABBY_BACKUP2_REL = ".tabby/ee/db.backup-20261005.sqlite"
TABBY_EVENTS_REL = ".tabby/events/2025-10-01.json"


def tabby_backup_records():
    return [
        *tabby_secret_records(),
        "INSERT INTO threads(id,is_ephemeral,user_id,created_at,updated_at) "
        "VALUES(3,1,1,'2026-09-10 08:00:00','2026-09-10 08:00:04')",
        "INSERT INTO thread_messages(id,thread_id,role,content,created_at,updated_at,code_attachments) VALUES "
        "(1,3,'user','dump the users table','2026-09-10 08:00:00','2026-09-10 08:00:00',NULL),"
        """(2,3,'assistant','Run `select * from users`.','2026-09-10 08:00:04','2026-09-10 08:00:04','[{"git_url":"https://github.com/acme/ops","filepath":"db.sql","content":"select 1","language":"sql","start_line":null}]')""",
    ]


def tabby_event_records():
    """The two event log lines of research/tabby.md section 8 plus a
    chat_completion event, whose body is empty (routes/chat.rs:83)."""
    return [
        {
            "user": "1",
            "ts": 1759312800123,
            "event": {
                "completion": {
                    "completion_id": "cmpl-7f3a",
                    "language": "python",
                    "prompt": "def add(a, b):\n    ",
                    "segments": {
                        "prefix": "def add(a, b):\n    ",
                        "suffix": "\n",
                        "git_url": "https://github.com/acme/app",
                        "filepath": "app/math.py",
                    },
                    "choices": [{"index": 0, "text": "return a + b"}],
                    "user_agent": "tabby-agent/1.9",
                }
            },
        },
        {
            "user": "1",
            "ts": 1759312801500,
            "event": {
                "select": {
                    "completion_id": "cmpl-7f3a",
                    "choice_index": 0,
                    "view_id": "view-1",
                    "elapsed": 1377,
                }
            },
        },
        {"user": None, "ts": 1759312802000, "event": {"chat_completion": {}}},
    ]


TABBY_COMPLETION_PAYLOAD = json.dumps(tabby_event_records()[0]["event"], indent=2)


def tabby_backup2_records():
    """A later backup in the current schema (#122): the ephemeral thread of
    the first backup, copied again, and the live database's thread 7."""
    n = len(tabby_secret_records())
    return [
        *tabby_secret_records(),
        "INSERT INTO threads(id,is_ephemeral,user_id,created_at,updated_at) "
        "VALUES(3,1,1,'2026-09-10 08:00:00','2026-09-10 08:00:04')",
        "INSERT INTO thread_messages(id,thread_id,role,content,created_at,updated_at,attachment) VALUES "
        """(5,3,'user','dump the users table','2026-09-10 08:00:00','2026-09-10 08:00:00','{}'),"""
        """(6,3,'assistant','Run `select * from users`.','2026-09-10 08:00:04','2026-09-10 08:00:04','{"code":[{"git_url":"https://github.com/acme/ops","filepath":"db.sql","content":"select 1","language":"sql","start_line":null}]}')""",
        # Thread 7 and its messages, as the live database holds them.
        *tabby_records()[n : n + 2],
    ]


def build_tabby(home: Path) -> None:
    """A Tabby server's home: the live WAL database, a pre-migration backup
    and a later one holding copies of the same threads, one day of the event
    log, and the config file as noise."""
    _wal_db(home / TABBY_REL, TABBY_SCHEMA, tabby_records())
    for rel, schema, records in (
        (TABBY_BACKUP_REL, TABBY_BACKUP_SCHEMA, tabby_backup_records()),
        (TABBY_BACKUP2_REL, TABBY_SCHEMA, tabby_backup2_records()),
    ):
        con = sqlite3.connect(str(home / rel))
        con.executescript(schema)
        for sql in records:
            con.execute(sql)
        con.commit()
        con.close()
    _jsonl(home / TABBY_EVENTS_REL, tabby_event_records())
    (home / ".tabby/config.toml").write_text(
        '[model.chat.http]\napi_key = "sk-tabby-test"\n', encoding="utf-8"
    )


OPENHANDS_CONV = "0f0e0d0c111140008000000000000001"
OPENHANDS_CLI_CONV = "0f0e0d0c111140008000000000000002"
OPENHANDS_LEGACY = "legacy-sid-1"


def openhands_meta(cwd="/srv/proj"):
    return {
        "id": "0f0e0d0c-1111-4000-8000-000000000001",
        "title": "List files",
        "created_at": "2026-10-01T10:00:00Z",
        "updated_at": "2026-10-01T10:00:05Z",
        "workspace": {"kind": "LocalWorkspace", "working_dir": cwd},
        "secrets": {"GITHUB_TOKEN": "**********"},
    }


def openhands_base_state(conv_id, cwd="/srv/proj"):
    return {
        "id": conv_id,
        "execution_status": "finished",
        "agent": {
            "kind": "Agent",
            "llm": {"model": "litellm_proxy/claude-sonnet-4-5", "api_key": "**********"},
        },
        "workspace": {"kind": "LocalWorkspace", "working_dir": cwd},
    }


def openhands_events(prefix="6b1d5c2e-0000-4000-8000-00000000000", day="2026-10-01T12:00:"):
    return [
        {
            "kind": "SystemPromptEvent",
            "id": prefix + "0",
            "timestamp": day + "00.500000",
            "source": "agent",
            "system_prompt": {"type": "text", "text": "You are OpenHands agent."},
            "tools": [{"kind": "TerminalTool"}, {"kind": "FileEditorTool"}],
        },
        {
            "kind": "MessageEvent",
            "id": prefix + "1",
            "timestamp": day + "01.000000",
            "source": "user",
            "llm_message": {
                "role": "user",
                "content": [{"type": "text", "text": "list the files"}],
            },
            "activated_skills": [],
            "extended_content": [],
        },
        {
            "kind": "ActionEvent",
            "id": prefix + "2",
            "timestamp": day + "03.000000",
            "source": "agent",
            "thought": [{"type": "text", "text": "I will run ls."}],
            "action": {"kind": "TerminalAction", "command": "ls"},
            "tool_name": "terminal",
            "tool_call_id": "call_1",
            "tool_call": {
                "id": "call_1",
                "name": "terminal",
                "arguments": '{"command":"ls"}',
                "origin": "completion",
            },
            "llm_response_id": "resp_1",
            "security_risk": "LOW",
        },
        {
            "kind": "ObservationEvent",
            "id": prefix + "3",
            "timestamp": day + "04.000000",
            "source": "environment",
            "tool_name": "terminal",
            "tool_call_id": "call_1",
            "action_id": prefix + "2",
            "observation": {
                "kind": "TerminalObservation",
                "content": [{"type": "text", "text": "README.md"}],
                "is_error": False,
                "command": "ls",
                "exit_code": 0,
            },
        },
        {
            "kind": "ActionEvent",
            "id": prefix + "4",
            "timestamp": day + "05.000000",
            "source": "agent",
            "thought": [],
            "reasoning_content": "check the readme",
            "action": {
                "kind": "FileEditorAction",
                "command": "view",
                "path": "/srv/proj/README.md",
            },
            "tool_name": "file_editor",
            "tool_call_id": "call_2",
            "tool_call": {
                "id": "call_2",
                "name": "file_editor",
                "arguments": '{"command":"view","path":"/srv/proj/README.md"}',
                "origin": "completion",
            },
        },
        {
            "kind": "UserRejectObservation",
            "id": prefix + "5",
            "timestamp": day + "06.000000",
            "source": "user",
            "tool_name": "file_editor",
            "tool_call_id": "call_2",
            "action_id": prefix + "4",
            "rejection_reason": "not that file",
            "rejection_source": "user",
        },
        {
            "kind": "MessageEvent",
            "id": prefix + "6",
            "timestamp": day + "07.000000",
            "source": "agent",
            "llm_message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "The project has a README."}],
            },
            "activated_skills": [],
            "extended_content": [],
        },
    ]


def _openhands_conversation(cdir: Path, events) -> None:
    for n, ev in enumerate(events):
        path = cdir / "events" / ("event-%05d-%s.json" % (n, ev["id"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ev, separators=(",", ":")), encoding="utf-8")
    (cdir / "events" / (".eventlog-len-%d.marker" % len(events))).write_text("", encoding="utf-8")


def build_openhands(home: Path) -> None:
    oh = home / ".openhands"
    conv = oh / "agent-canvas/dev_conversations" / OPENHANDS_CONV
    _openhands_conversation(conv, openhands_events())
    _json_file(conv / "meta.json", openhands_meta())
    _json_file(conv / "base_state.json", openhands_base_state(OPENHANDS_CONV))
    # CLI conversation with no meta.json: naive times are emitted as if UTC.
    cli = oh / "conversations" / OPENHANDS_CLI_CONV
    _openhands_conversation(
        cli, openhands_events("7c2e6d3f-0000-4000-8000-00000000000", "2026-10-02T08:30:")[:4]
    )
    _json_file(cli / "base_state.json", openhands_base_state(OPENHANDS_CLI_CONV))
    legacy = oh / "sessions" / OPENHANDS_LEGACY / "events"
    for n in range(3):
        _json_file(
            legacy / ("%d.json" % n),
            {
                "id": n,
                "timestamp": "2026-03-01T09:00:0%d.000000" % n,
                "source": "user",
                "action": "message",
                "args": {"content": "hi"},
            },
        )
    _json_file(
        oh / "settings.json",
        {"llm_model": "anthropic/claude-sonnet-4-5", "llm_api_key": "sk-not-real"},
    )
    _json_file(oh / "secrets.json", {"custom_secrets": {"X": {"secret": "not-real"}}})


SHELLGPT_CHAT = "deploy-check"
SHELLGPT_LEGACY_CHAT = "old-functions"


def shellgpt_messages():
    return [
        {
            "role": "system",
            "content": "You are ShellGPT\nYou are programming and system administration assistant.",
        },
        {"role": "user", "content": "what is listening on port 8080"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_Q1w2e3r4",
                    "type": "function",
                    "function": {
                        "name": "execute_shell_command",
                        "arguments": '{"shell_command": "ss -ltnp | grep 8080"}',
                    },
                }
            ],
        },
        {
            "role": "tool",
            "content": 'Exit code: 0, Output:\nLISTEN 0 4096 0.0.0.0:8080 users:(("python3",pid=4242))\n',
            "tool_call_id": "call_Q1w2e3r4",
        },
        {
            "role": "assistant",
            "content": '\n> @FunctionCall `execute_shell_command(shell_command="ss -ltnp | grep 8080")` '
            "\n\nA python3 process (PID 4242) is listening on 8080.",
        },
    ]


def shellgpt_legacy_messages():
    return [
        {"role": "system", "content": "You are ShellGPT"},
        {"role": "user", "content": "how much disk is free"},
        {
            "role": "assistant",
            "content": "",
            "function_call": {
                "name": "execute_shell_command",
                "arguments": '{"shell_command": "df -h /"}',
            },
        },
        {
            "role": "function",
            "content": "Exit code: 0, Output:\n/dev/sda1 50G 20G 30G 40% /\n",
            "name": "execute_shell_command",
        },
        {"role": "assistant", "content": "30G is free on /."},
    ]


def build_shellgpt(home: Path) -> None:
    temp = home / "AppData/Local/Temp"
    (temp / "chat_cache").mkdir(parents=True, exist_ok=True)
    (temp / "chat_cache" / SHELLGPT_CHAT).write_text(
        json.dumps(shellgpt_messages()), encoding="utf-8"
    )
    (temp / "shell_gpt/chat_cache").mkdir(parents=True, exist_ok=True)
    (temp / "shell_gpt/chat_cache" / SHELLGPT_LEGACY_CHAT).write_text(
        json.dumps(shellgpt_legacy_messages()), encoding="utf-8"
    )
    (temp / "shell_gpt/cache").mkdir(parents=True, exist_ok=True)
    (temp / "shell_gpt/cache/0cc175b9c0f1b6a831c399e269772661").write_text(
        "a cached response", encoding="utf-8"
    )
    cfg = home / ".config/shell_gpt"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / ".sgptrc").write_text(
        "OPENAI_API_KEY=sk-not-real\nDEFAULT_MODEL=gpt-4o\n", encoding="utf-8"
    )


# ---- pi, little-coder, letta (pi session format) --------------------------------

PI_SESSION = "0199a1b2-7c3d-7e4f-8a5b-6c7d8e9f0a1b"
PI_FORK = "0199a1b2-7c3d-7e4f-8a5b-6c7d8e9f0a2c"
PI_DIR = ".pi/agent/sessions/--srv-proj--/"
PI_FILE = "2026-10-01T09-00-00-000Z_%s.jsonl" % PI_SESSION
PI_FORK_FILE = "2026-10-01T09-30-00-000Z_%s.jsonl" % PI_FORK
LC_SESSION = "0b9e2f4c-1111-4000-8000-000000000001"
LC_FILE = "2026-10-01T11-00-00-000Z_%s.jsonl" % LC_SESSION
PI_EXPERIMENTAL = "exp-session-1"
PI_TRUST = ".pi/agent/trust.json"
PI_TRUST_MTIME = 1790852000  # 2026-10-01T10:53:20Z
LETTA_LOCAL_CONV = "local-conv-1"
LETTA_LOCAL_DIR = "Y29udmVyc2F0aW9uOmxvY2FsLWNvbnYtMQ"  # base64url("conversation:local-conv-1")
LETTA_AGENT = "agent-1a2b"
LETTA_CONV = "conv-9f"


def pi_session_records(cwd="/srv/proj"):
    return [
        {
            "type": "session",
            "version": 3,
            "id": PI_SESSION,
            "timestamp": "2026-10-01T09:00:00.000Z",
            "cwd": cwd,
        },
        {
            "type": "model_change",
            "id": "1a2b3c4d",
            "parentId": None,
            "timestamp": "2026-10-01T09:00:00.100Z",
            "provider": "anthropic",
            "modelId": "claude-sonnet-4-5",
        },
        {
            "type": "message",
            "id": "2b3c4d5e",
            "parentId": "1a2b3c4d",
            "timestamp": "2026-10-01T09:00:01.000Z",
            "message": {
                "role": "user",
                "content": "fix the failing test",
                "timestamp": 1790845201000,
            },
        },
        {
            "type": "message",
            "id": "3c4d5e6f",
            "parentId": "2b3c4d5e",
            "timestamp": "2026-10-01T09:00:04.000Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "run the tests first"},
                    {
                        "type": "toolCall",
                        "id": "toolu_01",
                        "name": "bash",
                        "arguments": {"command": "npm test"},
                    },
                ],
                "api": "anthropic-messages",
                "provider": "anthropic",
                "model": "claude-sonnet-4-5",
                "usage": {
                    "input": 900,
                    "output": 40,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                    "totalTokens": 940,
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0},
                },
                "stopReason": "toolUse",
                "timestamp": 1790845204000,
            },
        },
        {
            "type": "message",
            "id": "4d5e6f70",
            "parentId": "3c4d5e6f",
            "timestamp": "2026-10-01T09:00:07.000Z",
            "message": {
                "role": "toolResult",
                "toolCallId": "toolu_01",
                "toolName": "bash",
                "content": [{"type": "text", "text": "1 failing"}],
                "isError": False,
                "timestamp": 1790845207000,
            },
        },
        {
            "type": "message",
            "id": "5e6f7081",
            "parentId": "4d5e6f70",
            "timestamp": "2026-10-01T09:00:09.000Z",
            "message": {
                "role": "bashExecution",
                "command": "git status",
                "output": "M src/a.ts",
                "exitCode": 0,
                "cancelled": False,
                "truncated": False,
                "timestamp": 1790845209000,
            },
        },
        {
            "type": "label",
            "id": "70819203",
            "parentId": "5e6f7081",
            "timestamp": "2026-10-01T09:00:09.500Z",
            "targetId": "2b3c4d5e",
            "label": "start",
        },
        {
            "type": "session_info",
            "id": "6f708192",
            "parentId": "5e6f7081",
            "timestamp": "2026-10-01T09:00:10.000Z",
            "name": "test fix",
        },
        {
            "type": "model_change",
            "id": "8192a3b5",
            "parentId": "6f708192",
            "timestamp": "2026-10-01T09:00:11.000Z",
            "provider": "openai",
            "modelId": "gpt-5",
        },
    ]


def pi_fork_records(parent_path):
    parent = pi_session_records()
    return [
        {
            "type": "session",
            "version": 3,
            "id": PI_FORK,
            "timestamp": "2026-10-01T09:30:00.000Z",
            "cwd": "/srv/proj",
            "parentSession": parent_path,
        },
        *parent[1:4],
        {
            "type": "message",
            "id": "8192a3b4",
            "parentId": "3c4d5e6f",
            "timestamp": "2026-10-01T09:30:05.000Z",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Trying another way."}],
                "provider": "anthropic",
                "model": "claude-sonnet-4-5",
                "stopReason": "stop",
                "timestamp": 1790847005000,
            },
        },
    ]


def little_coder_session_records(cwd="/srv/proj"):
    return [
        {
            "type": "session",
            "version": 3,
            "id": LC_SESSION,
            "timestamp": "2026-10-01T11:00:00.000Z",
            "cwd": cwd,
        },
        {
            "type": "custom_message",
            "id": "a1",
            "parentId": None,
            "timestamp": "2026-10-01T11:00:01.000Z",
            "customType": "lc-skills",
            "content": "## Skill: edit\nUse the edit tool.",
            "display": False,
        },
        {
            "type": "message",
            "id": "a2",
            "parentId": "a1",
            "timestamp": "2026-10-01T11:00:02.000Z",
            "message": {
                "role": "user",
                "content": "fix the failing test",
                "timestamp": 1790852402000,
            },
        },
        {
            "type": "message",
            "id": "a3",
            "parentId": "a2",
            "timestamp": "2026-10-01T11:00:05.000Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "run tests first"},
                    {
                        "type": "toolCall",
                        "id": "call_1",
                        "name": "bash",
                        "arguments": {"command": "npm test"},
                    },
                ],
                "api": "openai-completions",
                "provider": "llamacpp",
                "model": "qwen3.6-35b-a3b",
                "usage": {"input": 900, "output": 40, "cacheRead": 0, "cacheWrite": 0},
                "stopReason": "toolUse",
                "timestamp": 1790852405000,
            },
        },
        {
            "type": "message",
            "id": "a4",
            "parentId": "a3",
            "timestamp": "2026-10-01T11:00:09.000Z",
            "message": {
                "role": "toolResult",
                "toolCallId": "call_1",
                "toolName": "bash",
                "content": [{"type": "text", "text": "1 failing"}],
                "isError": False,
                "timestamp": 1790852409000,
            },
        },
        {
            "type": "message",
            "id": "a5",
            "parentId": "a4",
            "timestamp": "2026-10-01T11:00:12.000Z",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "One test fails."}],
                "api": "openai-completions",
                "provider": "llamacpp",
                "model": "qwen3.6-27b",
                "stopReason": "stop",
                "timestamp": 1790852412000,
            },
        },
    ]


def build_pi(home: Path) -> None:
    _jsonl(home / PI_DIR / PI_FILE, pi_session_records())
    _jsonl(home / PI_DIR / PI_FORK_FILE, pi_fork_records("/home/alice/" + PI_DIR + PI_FILE))
    _jsonl(home / PI_DIR / LC_FILE, little_coder_session_records())
    _json(
        home / ".pi/agent/experimental/sessions" / PI_EXPERIMENTAL / "meta.json",
        {"createdAt": 1790856000000, "cwd": "/srv/proj"},
    )
    _json(home / ".pi/agent/auth.json", {"anthropic": {"type": "api_key", "key": "sk-not-real"}})
    _json(home / ".pi/agent/settings.json", {"defaultProvider": "anthropic"})
    _json(home / PI_TRUST, {"/srv/proj": True, "/srv/untrusted": False})
    os.utime(home / PI_TRUST, (PI_TRUST_MTIME, PI_TRUST_MTIME))


def build_little_coder(home: Path) -> None:
    _json(
        home / ".pi/agent/little-coder-prompt-history.json",
        ["fix the failing test", "now run lint"],
    )
    ck = home / ".little-coder/checkpoints" / LC_FILE
    ck.mkdir(parents=True, exist_ok=True)
    (ck / "_srv_proj_src_a.ts").write_text("old contents\n", encoding="utf-8")
    (ck / "_srv_proj_src_new.ts.absent").write_text("", encoding="utf-8")
    os.utime(ck / "_srv_proj_src_a.ts", (1790852406, 1790852406))
    os.utime(ck / "_srv_proj_src_new.ts.absent", (1790852407, 1790852407))
    (home / ".config/little-coder").mkdir(parents=True, exist_ok=True)
    (home / ".config/little-coder/settings.json").write_text("{}", encoding="utf-8")


def letta_transcript_records():
    return [
        {
            "kind": "user",
            "text": "list the repo",
            "captured_at": "2026-10-01T12:00:05.120Z",
            "source_line_id": "ui-1",
        },
        {"kind": "reasoning", "text": "use ls", "captured_at": "2026-10-01T12:00:05.120Z"},
        {
            "kind": "tool_call",
            "name": "Bash",
            "argsText": '{"command":"ls"}',
            "resultText": "README.md",
            "resultOk": True,
            "captured_at": "2026-10-01T12:00:05.120Z",
            "source_line_id": "ui-2",
        },
        {
            "kind": "assistant",
            "text": "One file: README.md",
            "captured_at": "2026-10-01T12:00:05.120Z",
            "source_line_id": "ui-3",
            "source_message_id": "message-77",
        },
    ]


def letta_twin_transcript_records():
    """The local-backend conversation's transcript: the turn its
    messages.jsonl also holds, captured at the turn's end, then a turn
    messages.jsonl no longer has (issue 122)."""
    return [
        *letta_transcript_records(),
        {
            "kind": "user",
            "text": "now delete the build directory",
            "captured_at": "2026-10-01T12:00:40.500Z",
            "source_line_id": "ui-4",
        },
        {
            "kind": "assistant",
            "text": "Deleted build/",
            "captured_at": "2026-10-01T12:00:40.500Z",
            "source_line_id": "ui-5",
        },
    ]


def letta_local_records(cwd="/srv/proj"):
    asst = {
        "id": "letta-msg-2",
        "role": "assistant",
        "content": [
            {"type": "thinking", "thinking": "use ls"},
            {"type": "toolCall", "id": "call_1", "name": "Bash", "arguments": {"command": "ls"}},
        ],
        "api": "anthropic-messages",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "usage": {
            "input": 10,
            "output": 5,
            "cacheRead": 0,
            "cacheWrite": 0,
            "totalTokens": 15,
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0},
        },
        "stopReason": "toolUse",
        "timestamp": 1790856002000,
        "metadata": {"agent_id": LETTA_AGENT, "conversation_id": LETTA_LOCAL_CONV},
    }
    partial = dict(asst, content=[{"type": "thinking", "thinking": "use"}], stopReason="pending")
    return [
        {
            "type": "session",
            "version": 3,
            "id": LETTA_LOCAL_CONV,
            "timestamp": "2026-10-01T12:00:00.000Z",
            "cwd": cwd,
        },
        {
            "type": "message",
            "id": "a1b2c3d4",
            "parentId": None,
            "timestamp": "2026-10-01T12:00:01.000Z",
            "message": {
                "id": "letta-msg-1",
                "role": "user",
                "content": "list the repo",
                "timestamp": 1790856001000,
            },
        },
        {
            "type": "message",
            "id": "b2c3d4e4",
            "parentId": "a1b2c3d4",
            "timestamp": "2026-10-01T12:00:02.000Z",
            "message": partial,
        },
        {
            "type": "message",
            "id": "b2c3d4e5",
            "parentId": "a1b2c3d4",
            "timestamp": "2026-10-01T12:00:02.000Z",
            "message": asst,
        },
        {
            "type": "message",
            "id": "c3d4e5f6",
            "parentId": "b2c3d4e5",
            "timestamp": "2026-10-01T12:00:03.000Z",
            "message": {
                "id": "letta-msg-3",
                "role": "toolResult",
                "toolCallId": "call_1",
                "toolName": "Bash",
                "content": [{"type": "text", "text": "README.md"}],
                "isError": False,
                "timestamp": 1790856003000,
            },
        },
        {
            "type": "message",
            "id": "d4e5f6a7",
            "parentId": "c3d4e5f6",
            "timestamp": "2026-10-01T12:00:04.000Z",
            "message": {
                "id": "letta-msg-4",
                "role": "assistant",
                "content": [{"type": "text", "text": "One file: README.md"}],
                "provider": "anthropic",
                "model": "claude-haiku-4-5",
                "stopReason": "stop",
                "timestamp": 1790856004000,
            },
        },
    ]


def letta_sessions_records(project="/srv/proj"):
    usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "steps": 0,
    }
    start = {
        "agent_id": LETTA_AGENT,
        "session_id": "s-1",
        "timestamp": 1790856000000,
        "project": project,
        "model": "claude-sonnet-4-5",
        "provider": "anthropic",
        "usage": usage,
        "duration": {"api_ms": 0, "wall_ms": 0},
        "cost": {"type": "hosted"},
    }
    older = dict(start, session_id="s-0", timestamp=1790766000000, project="/srv/old")
    end = dict(
        start,
        timestamp=1790856060000,
        duration={"api_ms": 900, "wall_ms": 60000},
        message_count=4,
        tool_call_count=1,
        exit_reason="user_exit",
    )
    return [older, start, end]


def build_letta(home: Path) -> None:
    letta = home / ".letta"
    _jsonl(
        letta / "transcripts" / LETTA_AGENT / LETTA_CONV / "transcript.jsonl",
        letta_transcript_records(),
    )
    _jsonl(
        letta / "transcripts" / LETTA_AGENT / LETTA_LOCAL_CONV / "transcript.jsonl",
        letta_twin_transcript_records(),
    )
    _json(
        letta / "transcripts" / LETTA_AGENT / LETTA_CONV / "state.json",
        {"schema_version": "v3_assistant_steps"},
    )
    conv = letta / "lc-local-backend/conversations" / LETTA_LOCAL_DIR
    _jsonl(conv / "messages.jsonl", letta_local_records())
    _json(conv / "manifest.json", {"message_format": "pi-session-entry-jsonl", "schema_version": 2})
    _jsonl(letta / "sessions.jsonl", letta_sessions_records())
    _json(letta / "settings.json", {"env": {"LETTA_API_KEY": "sk-not-real"}})
    _json(letta / "transcripts" / LETTA_AGENT / LETTA_LOCAL_CONV / "payload-auto-a1b2c3.json", [])


HERMES_SESSION = "20261001_120000_a1b2c3d4"
HERMES_CHILD = "20261001_121500_e5f60708"
HERMES_DIVERTED = "20261001_130000_0badf00d"

# hermes_state_common.py:372-480 at hermes-agent 8b66a51, the columns
# research/hermes.md section 8 lists (schema version 31).
HERMES_SCHEMA = """
CREATE TABLE schema_version (version INTEGER NOT NULL);
CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT NOT NULL, model TEXT,
  parent_session_id TEXT, started_at REAL NOT NULL, ended_at REAL, end_reason TEXT,
  cwd TEXT, git_branch TEXT, git_repo_root TEXT, title TEXT);
CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
  role TEXT NOT NULL, content TEXT, tool_call_id TEXT, tool_calls TEXT, tool_name TEXT,
  timestamp REAL NOT NULL, finish_reason TEXT, reasoning TEXT, reasoning_content TEXT,
  active INTEGER NOT NULL DEFAULT 1, compacted INTEGER NOT NULL DEFAULT 0);
CREATE TABLE session_model_usage (session_id TEXT NOT NULL, model TEXT NOT NULL,
  billing_provider TEXT NOT NULL DEFAULT '', billing_base_url TEXT NOT NULL DEFAULT '',
  billing_mode TEXT NOT NULL DEFAULT '', task TEXT NOT NULL DEFAULT '',
  api_call_count INTEGER NOT NULL DEFAULT 0, first_seen REAL, last_seen REAL,
  PRIMARY KEY (session_id, model, billing_provider, billing_base_url, billing_mode, task));
"""


def hermes_records(cwd="/srv/proj"):
    """The INSERT statements of research/hermes.md section 8 with the shared
    project path, plus a rewound turn kept as active=0, a multimodal user
    message behind the NUL json prefix, and a subagent child session."""
    return [
        "INSERT INTO schema_version VALUES (31)",
        "INSERT INTO sessions VALUES ('%s','cli','anthropic/claude-sonnet-4',NULL,1790856000.0,NULL,NULL,"
        "'%s','main','%s','List files')" % (HERMES_SESSION, cwd, cwd),
        "INSERT INTO sessions VALUES ('%s','subagent','openai/gpt-5',"
        "'%s',1790856900.0,1790856910.0,'completed',NULL,NULL,'%s','Check disk')"
        % (HERMES_CHILD, HERMES_SESSION, cwd),
        "INSERT INTO messages (session_id,role,content,tool_call_id,tool_calls,tool_name,timestamp,finish_reason,reasoning) VALUES "
        "('%s','user','list files',NULL,NULL,NULL,1790856001.25,NULL,NULL),"
        % HERMES_SESSION
        + """('%s','assistant','',NULL,""" % HERMES_SESSION
        + """'[{"id":"call_1","call_id":"call_1","response_item_id":null,"type":"function","function":{"name":"terminal","arguments":"{\\"command\\":\\"ls\\"}"}}]',"""
        "NULL,1790856002.5,'tool_calls','User wants a listing.'),"
        "('%s','tool','a.txt' || char(10) || 'b.txt','call_1',NULL,'terminal',1790856003.0,NULL,NULL),"
        % HERMES_SESSION
        + "('%s','assistant','Two files: a.txt, b.txt.',NULL,NULL,NULL,1790856004.0,'stop',NULL)"
        % HERMES_SESSION,
        "INSERT INTO messages (session_id,role,content,timestamp,active,compacted) VALUES "
        "('%s','user','delete them instead',1790856005.0,0,1),"
        % HERMES_SESSION
        + """('%s','user',char(0) || 'json:[{"type":"text","text":"what is in this screenshot?"},"""
        """{"type":"image_url","image_url":{"url":"data:image/png;base64,AAAA"}}]',1790856006.0,1,0)"""
        % HERMES_SESSION,
        "INSERT INTO messages (session_id,role,content,timestamp) VALUES ('%s','user','df -h',1790856901.0)"
        % HERMES_CHILD,
        "INSERT INTO session_model_usage (session_id,model,billing_provider,task,api_call_count,"
        "first_seen,last_seen) VALUES "
        "('%s','anthropic/claude-sonnet-4','openrouter','',2,1790856002.5,1790856003.5),"
        "('%s','anthropic/claude-opus-4','openrouter','',1,1790856004.0,1790856004.0),"
        "('%s','google/gemini-flash','openrouter','title_generation',1,1790856001.5,1790856001.5)"
        % (HERMES_SESSION, HERMES_SESSION, HERMES_SESSION),
    ]


def hermes_diverted_records():
    """sessions/<id>.jsonl: message dicts appended while state.db was
    replaced under a running process (hermes_state.py:429-444)."""
    return [
        {"role": "user", "content": "show the env", "timestamp": 1790859600.0},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_9",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path":"/srv/proj/.env"}'},
                }
            ],
            "timestamp": 1790859601.0,
        },
        {
            "role": "tool",
            "content": "TOKEN=x",
            "tool_call_id": "call_9",
            "tool_name": "read_file",
            "timestamp": 1790859602.0,
        },
    ]


HERMES_DIVERTED_REL = ".hermes/sessions/%s.jsonl" % HERMES_DIVERTED


HERMES_PRUNED = "20260920_090000_deadbeef"
HERMES_SNAPSHOT_OLD = "20261001-110000"
HERMES_SNAPSHOT = "20261001-120004-pre-update"
HERMES_SNAPSHOT_REL = ".hermes/state-snapshots/%s/state.db" % HERMES_SNAPSHOT
HERMES_SNAPSHOT_OLD_REL = ".hermes/state-snapshots/%s/state.db" % HERMES_SNAPSHOT_OLD
HERMES_SESSION_JSONL_REL = ".hermes/sessions/%s.jsonl" % HERMES_SESSION


def hermes_pruned_records(cwd="/srv/proj"):
    """A session the live state.db no longer holds (pruned or deleted), as
    the quick snapshots keep it."""
    return [
        "INSERT INTO sessions VALUES ('%s','cli','anthropic/claude-sonnet-4',NULL,1789894800.0,"
        "1789894860.0,'user_exit','%s','main','%s','Audit logs')" % (HERMES_PRUNED, cwd, cwd),
        "INSERT INTO messages (session_id,role,content,timestamp) VALUES "
        "('%s','user','summarise the audit log',1789894801.0),"
        "('%s','assistant','The log shows three failed logins.',1789894802.0)"
        % (HERMES_PRUNED, HERMES_PRUNED),
    ]


def hermes_snapshot_records(cwd="/srv/proj"):
    """state-snapshots/<id>/state.db (hermes_cli/backup.py:1214-1420): the
    live database as it was at 12:00:04, the main session's first four
    messages and its first model, plus the pruned session."""
    live = hermes_records(cwd)
    return [
        live[0],
        live[1],
        live[3],
        "INSERT INTO session_model_usage (session_id,model,billing_provider,task,api_call_count,"
        "first_seen,last_seen) VALUES "
        "('%s','anthropic/claude-sonnet-4','openrouter','',2,1790856002.5,1790856003.5)"
        % HERMES_SESSION,
        *hermes_pruned_records(cwd),
    ]


def hermes_session_jsonl_records():
    """sessions/<main session>.jsonl: a divert of the main session, one
    message the live state.db also holds (list content, not the NUL json
    form) and one it lacks."""
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "what is in this screenshot?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
            ],
            "timestamp": 1790856006.0,
        },
        {"role": "user", "content": "and the hidden files?", "timestamp": 1790856007.0},
    ]


def _hermes_snapshot(path: Path, inserts) -> None:
    """A snapshot copy: SQLite's backup API leaves a plain database, no WAL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.executescript(HERMES_SCHEMA)
    for stmt in inserts:
        con.execute(stmt)
    con.commit()
    con.close()


def build_hermes(home: Path) -> None:
    hermes = home / ".hermes"
    _wal_db(hermes / "state.db", HERMES_SCHEMA, hermes_records())
    _jsonl(home / HERMES_DIVERTED_REL, hermes_diverted_records())
    _hermes_snapshot(
        home / HERMES_SNAPSHOT_OLD_REL,
        ["INSERT INTO schema_version VALUES (31)", *hermes_pruned_records()],
    )
    _hermes_snapshot(home / HERMES_SNAPSHOT_REL, hermes_snapshot_records())
    _json(
        hermes / "state-snapshots" / HERMES_SNAPSHOT / "manifest.json",
        {"id": HERMES_SNAPSHOT, "timestamp": "20261001-120004", "label": "pre-update"},
    )
    _jsonl(home / HERMES_SESSION_JSONL_REL, hermes_session_jsonl_records())
    (hermes / "config.yaml").write_text("model: anthropic/claude-sonnet-4\n", encoding="utf-8")
    (hermes / "auth.json").write_text(
        '{"providers": {"nous": {"access_token": "not-real"}}}', encoding="utf-8"
    )
    (hermes / "sessions/sessions.json").write_text("{}", encoding="utf-8")


AGENT_ZERO_CHAT = "AbCd1234"
AGENT_ZERO_REL = "agent-zero/usr/chats/%s/chat.json" % AGENT_ZERO_CHAT
AGENT_ZERO_LONG = "x" * 600


def _a0_message(mid, ai, content, metadata=None):
    return {
        "_cls": "Message",
        "id": mid,
        "ai": ai,
        "content": content,
        "metadata": metadata or {},
        "sequence": 0,
        "summary": "",
        "tokens": 5,
    }


# Session sync (issue 153): pastes/pending.json, the paste.rs links of
# `hermes debug share` uploads (hermes_cli/debug.py:38-39 at hermes-agent
# 8b66a51, research/hermes.md section 2): expire_at is upload + 21600 s.
HERMES_PASTES_REL = ".hermes/pastes/pending.json"


def hermes_pastes_records():
    return [
        {"url": "https://paste.rs/AbCdE", "expire_at": 1790875200.5},
        {"url": "https://paste.rs/FgHiJ", "expire_at": 1790875260.0},
    ]


def build_hermes_pastes(home: Path) -> None:
    path = home / HERMES_PASTES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(hermes_pastes_records()), encoding="utf-8")


def agent_zero_history():
    """Agent 0's history from research/agent-zero.md section 8, with the
    assistant message carrying the id of the `agent` log item that streamed
    it (agent.py:529-534) and its provider model, a second tool result
    long enough to be saved to messages/1.txt, and a later assistant message
    from another provider model (a model change)."""
    ai = json.dumps(
        {
            "thoughts": ["list"],
            "headline": "Listing",
            "tool_name": "code_execution_tool",
            "tool_args": {"runtime": "terminal", "code": "ls"},
        }
    )
    return {
        "_cls": "History",
        "counter": 5,
        "bulks": [],
        "topics": [],
        "current": {
            "_cls": "Topic",
            "summary": "",
            "messages": [
                _a0_message("u1", False, {"user_message": "list files"}),
                _a0_message(
                    "a1",
                    True,
                    ai,
                    {
                        "responses": {
                            "response_id": "resp_1",
                            "provider_model_key": "openrouter/anthropic/claude-sonnet-4",
                            "usage": {"input": 10, "output": 20},
                        }
                    },
                ),
                _a0_message(
                    "t1", False, {"tool_name": "code_execution_tool", "tool_result": "a.txt"}
                ),
                _a0_message(
                    "t2",
                    False,
                    {
                        "tool_name": "code_execution_tool",
                        "tool_result": AGENT_ZERO_LONG,
                        "file": "/a0/usr/chats/%s/messages/1.txt" % AGENT_ZERO_CHAT,
                    },
                ),
                _a0_message(
                    "a2",
                    True,
                    json.dumps({"thoughts": ["done"], "headline": "Checking again"}),
                    {
                        "responses": {
                            "response_id": "resp_2",
                            "provider_model_key": "openai/gpt-5",
                            "usage": {"input": 30, "output": 5},
                        }
                    },
                ),
            ],
        },
    }


def agent_zero_logs():
    return [
        {
            "no": 0,
            "id": "u1",
            "type": "user",
            "heading": "",
            "content": "list files",
            "kvps": {"attachments": []},
            "timestamp": 1790856001.0,
            "agentno": 0,
        },
        {
            "no": 1,
            "id": "a1",
            "type": "agent",
            "heading": "icon://network_intelligence A0: Listing",
            "content": "",
            "kvps": {
                "step": "Writing terminal command... (2)",
                "thoughts": ["list"],
                "headline": "Listing",
                "tool_name": "code_execution_tool",
                "tool_args": {"runtime": "terminal", "code": "ls"},
                "reasoning": "the user wants a listing",
            },
            "timestamp": 1790856002.0,
            "agentno": 0,
        },
        {
            "no": 2,
            "id": "t1",
            "type": "tool",
            "heading": "A0: Using tool 'code_execution_tool'",
            "content": "a.txt",
            "kvps": {"runtime": "terminal", "code": "ls", "_tool_name": "code_execution_tool"},
            "timestamp": 1790856003.0,
            "agentno": 0,
        },
        {
            "no": 3,
            "id": "t2",
            "type": "tool",
            "heading": "A0: Using tool 'code_execution_tool'",
            "content": AGENT_ZERO_LONG[:100] + "\n\n<< 500 Characters hidden >>\n\n",
            "kvps": {
                "runtime": "terminal",
                "code": "cat big.log",
                "_tool_name": "code_execution_tool",
            },
            "timestamp": 1790856004.0,
            "agentno": 0,
        },
        {
            "no": 4,
            "id": None,
            "type": "warning",
            "heading": "icon://warning Rate limit",
            "content": "retrying in 5s",
            "kvps": {},
            "timestamp": 1790856004.5,
            "agentno": 0,
        },
        {
            "no": 5,
            "id": "r1",
            "type": "response",
            "heading": "A0: Responding",
            "content": "There is one file, a.txt.",
            "kvps": {},
            "timestamp": 1790856005.0,
            "agentno": 0,
        },
        {
            "no": 6,
            "id": "a2",
            "type": "agent",
            "heading": "A0: Checking again",
            "content": "",
            "kvps": {"thoughts": ["done"], "headline": "Checking again"},
            "timestamp": 1790856006.0,
            "agentno": 0,
        },
    ]


def agent_zero_chat(logs=None, history=None):
    return {
        "id": AGENT_ZERO_CHAT,
        "name": "List files",
        "created_at": "2026-10-01T14:00:00+02:00",
        "type": "user",
        "last_message": "2026-10-01T14:00:05+02:00",
        "streaming_agent": 0,
        "agent_profile": "agent0",
        "data": {"project": "demo"},
        "output_data": {},
        "agents": [
            {
                "number": 0,
                "agent_profile": "agent0",
                "data": {},
                "history": json.dumps(
                    history if history is not None else agent_zero_history(), separators=(",", ":")
                ),
            }
        ],
        "log": {
            "guid": "6b0f0c1e-0000-4000-8000-000000000001",
            "progress": "",
            "progress_no": 5,
            "logs": logs if logs is not None else agent_zero_logs(),
        },
    }


def build_agent_zero(home: Path) -> None:
    """A docker-compose style install in ~/agent-zero, with the long tool
    result file, and settings and secrets noise."""
    usr = home / "agent-zero/usr"
    chat = usr / "chats" / AGENT_ZERO_CHAT
    chat.mkdir(parents=True, exist_ok=True)
    (chat / "chat.json").write_text(
        json.dumps(agent_zero_chat(), ensure_ascii=False), encoding="utf-8"
    )
    (chat / "messages").mkdir(exist_ok=True)
    (chat / "messages/1.txt").write_text(AGENT_ZERO_LONG + " (from file)", encoding="utf-8")
    (usr / "settings.json").write_text('{"chat_model_provider": "openrouter"}', encoding="utf-8")
    (usr / "secrets.env").write_text("API_KEY_OPENROUTER=not-real\n", encoding="utf-8")


# Session sync (issue 153): a Telegram chat whose main agent chained a turn
# on a provider-stored response, and a subordinate agent in local mode
# (ids recorded, nothing stored). Keys from research/agent-zero.md section 3
# (agent.py:1062-1082, plugins/_telegram_integration/helpers/constants.py:5-15
# at agent-zero e3051fb).
AGENT_ZERO_TG_CHAT = "TgChat01"
AGENT_ZERO_TG_REL = "agent-zero/usr/chats/%s/chat.json" % AGENT_ZERO_TG_CHAT
AGENT_ZERO_BOT_TOKEN = "123456:AA-FIXTURE-TELEGRAM-BOT-TOKEN"


def agent_zero_relayed_chat():
    chat = agent_zero_chat(
        logs=[
            {
                "no": 0,
                "id": "u1",
                "type": "user",
                "heading": "",
                "content": "status of the backups?",
                "kvps": {},
                "timestamp": 1790863200.0,
                "agentno": 0,
            },
            {
                "no": 1,
                "id": "r1",
                "type": "response",
                "heading": "",
                "content": "All backups ran.",
                "kvps": {},
                "timestamp": 1790863205.0,
                "agentno": 0,
            },
        ],
        history={"_cls": "History", "bulks": [], "topics": [], "current": {"messages": []}},
    )
    chat["id"] = AGENT_ZERO_TG_CHAT
    chat["name"] = "Telegram: @alice_ops"
    chat["data"] = {
        "project": "demo",
        "telegram_bot": "opsbot",
        "telegram_chat_id": 987654321,
        "telegram_chat_type": "private",
        "telegram_user_id": 123456789,
        "telegram_username": "alice_ops",
        "telegram_bot_cfg": {"name": "opsbot", "token": AGENT_ZERO_BOT_TOKEN},
    }
    chat["agents"][0]["data"] = {
        "responses_state": {
            "response_id": "resp_02",
            "previous_response_id": "resp_01",
            "provider_model_key": "openai/gpt-5",
            "history_counter": 4,
            "response_ids": ["resp_01", "resp_02"],
        }
    }
    sub = dict(chat["agents"][0])
    sub["number"] = 1
    sub["data"] = {
        "responses_state": {
            "response_id": "resp_l1",
            "previous_response_id": "",
            "provider_model_key": "codex/gpt-5-codex",
            "history_counter": 1,
            "response_ids": ["resp_l1"],
        }
    }
    chat["agents"].append(sub)
    return chat


def build_agent_zero_relayed(home: Path) -> None:
    path = home / AGENT_ZERO_TG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(agent_zero_relayed_chat()), encoding="utf-8")


OI_SESSION = "0199a1b2-0000-7000-8000-000000000001"
OI_IMPORTED = "0199a1b2-0000-7000-8000-000000000002"
OI_ROLLOUT = (
    ".openinterpreter/sessions/2026/10/01/rollout-2026-10-01T12-00-00-%s.jsonl" % OI_SESSION
)
OI_ARCHIVED = (
    ".openinterpreter/archived_sessions/2026/09/30/rollout-2026-09-30T08-00-00-%s.jsonl"
    % OI_IMPORTED
)


def open_interpreter_rollout_records(cwd="/srv/proj"):
    """research/open-interpreter.md section 8, with a reasoning item and a
    task_complete event added."""
    return [
        {
            "timestamp": "2026-10-01T10:00:00.000Z",
            "type": "session_meta",
            "payload": {
                "session_id": OI_SESSION,
                "id": OI_SESSION,
                "timestamp": "2026-10-01T10:00:00.000Z",
                "cwd": cwd,
                "originator": "codex_cli_rs",
                "cli_version": "0.9.0",
                "source": "cli",
                "model_provider": "kimi-for-coding",
                "git": {"branch": "main"},
            },
        },
        {
            "timestamp": "2026-10-01T10:00:01.000Z",
            "type": "turn_context",
            "payload": {
                "turn_id": "t1",
                "cwd": cwd,
                "approval_policy": "on-request",
                "sandbox_policy": {"type": "workspace-write"},
                "model": "kimi-k3",
            },
        },
        {
            "timestamp": "2026-10-01T10:00:01.100Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "list the files"}],
            },
        },
        {
            "timestamp": "2026-10-01T10:00:02.000Z",
            "type": "response_item",
            "payload": {
                "type": "reasoning",
                "summary": [{"type": "summary_text", "text": "run ls"}],
                "encrypted_content": "gAAA",
            },
        },
        {
            "timestamp": "2026-10-01T10:00:03.000Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "Bash",
                "arguments": '{"command":"ls"}',
                "call_id": "call_1",
            },
        },
        {
            "timestamp": "2026-10-01T10:00:04.000Z",
            "type": "response_item",
            "payload": {"type": "function_call_output", "call_id": "call_1", "output": "README.md"},
        },
        {
            "timestamp": "2026-10-01T10:00:05.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "One file: README.md"}],
            },
        },
        {
            "timestamp": "2026-10-01T10:00:05.000Z",
            "type": "event_msg",
            "payload": {"type": "task_complete", "turn_id": "t1", "duration_ms": 5000},
        },
        {
            # The next turn switches model and approval policy.
            "timestamp": "2026-10-01T10:00:06.000Z",
            "type": "turn_context",
            "payload": {
                "turn_id": "t2",
                "cwd": cwd,
                "approval_policy": "never",
                "sandbox_policy": {"type": "workspace-write"},
                "model": "kimi-k3-turbo",
            },
        },
    ]


def open_interpreter_imported_records(cwd="/srv/proj"):
    """A thread written by /import from a Claude Code transcript."""
    return [
        {
            "timestamp": "2026-09-30T08:00:00.000Z",
            "type": "session_meta",
            "payload": {
                "session_id": OI_IMPORTED,
                "id": OI_IMPORTED,
                "timestamp": "2026-09-30T08:00:00.000Z",
                "cwd": cwd,
                "originator": "codex_cli_rs",
                "cli_version": "0.9.0",
                "source": "cli",
                "model_provider": "openai",
            },
        },
        {
            "timestamp": "2026-09-30T08:00:00.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "imported prompt"}],
            },
        },
    ]


def open_interpreter_ledger():
    return {
        "records": [
            {
                "source_path": "/home/alice/.claude/projects/-home-alice-proj/5b1c.jsonl",
                "content_sha256": "ab12cd34",
                "imported_thread_id": OI_IMPORTED,
                "imported_at": 1790762400,
                "source_modified_at": 1790758800,
            },
        ]
    }


def build_open_interpreter(home: Path) -> None:
    oi = home / ".openinterpreter"
    _jsonl(home / OI_ROLLOUT, open_interpreter_rollout_records())
    _jsonl(home / OI_ARCHIVED, open_interpreter_imported_records())
    _jsonl(
        oi / "history.jsonl",
        [{"session_id": OI_SESSION, "ts": 1790848801, "text": "list the files"}],
    )
    _jsonl(
        oi / "session_index.jsonl",
        [{"id": OI_SESSION, "thread_name": "ls", "updated_at": "2026-10-01T10:00:05Z"}],
    )
    (oi / "external_agent_session_imports.json").write_text(
        json.dumps(open_interpreter_ledger()), encoding="utf-8"
    )
    (oi / "config.toml").write_text('harness = "claude-code"\n', encoding="utf-8")
    (oi / "auth.json").write_text('{"OPENAI_API_KEY": "sk-not-real"}', encoding="utf-8")
    build_open_interpreter_stores(home)


# The fork's SQLite set (#122): OI_SESSION's thread row repeats its first
# prompt; OI_ORPHAN's rollout is gone and only the projection, in the
# fork's schema without item lifecycle times, holds its turn.
OI_ORPHAN = "0199a1b2-0000-7000-8000-000000000003"


def build_open_interpreter_stores(home: Path) -> None:
    oi = home / ".openinterpreter"
    sessions = "/home/alice/.openinterpreter/sessions"
    write_codex_state(
        oi / "state_5.sqlite",
        [
            (
                OI_SESSION,
                sessions + "/2026/10/01/rollout-2026-10-01T12-00-00-%s.jsonl" % OI_SESSION,
                1790848800,
                "list the files",
                "list the files",
                None,
                0,
                "user",
                "main",
                "kimi-k3-turbo",
            ),
            (
                OI_ORPHAN,
                sessions + "/2026/09/29/rollout-2026-09-29T07-00-00-%s.jsonl" % OI_ORPHAN,
                1790665200,
                "summarise the README",
                "summarise the README",
                None,
                0,
                "user",
                None,
                "kimi-k3",
            ),
        ],
    )
    write_thread_history(
        oi / "thread_history_1.sqlite",
        [(OI_ORPHAN, "t1", 1, 6, "completed", 1790665201, 1790665206, 5000)],
        [
            (
                OI_ORPHAN,
                "t1",
                3,
                1790665202000,
                None,
                None,
                {
                    "type": "userMessage",
                    "id": "u1",
                    "content": [{"type": "text", "text": "summarise the README"}],
                },
            ),
            (
                OI_ORPHAN,
                "t1",
                5,
                1790665204000,
                None,
                None,
                {"type": "agentMessage", "id": "a1", "text": "It describes the project."},
            ),
        ],
        lifecycle=False,
    )
    # The fork's tracing log with a sent `/feedback` report for OI_SESSION (#153).
    write_codex_logs(oi / "logs_2.sqlite", codex_log_rows(OI_SESSION))


# -- OpenClaw (openclaw/openclaw at 3b16db7) ---------------------------------------
OPENCLAW_SESSION = "7d0c2a8e-1111-4000-8000-000000000001"
OPENCLAW_KEY = "agent:main:telegram:default:direct:123456789"
OPENCLAW_RESET_SESSION = "7d0c2a8e-1111-4000-8000-000000000002"
OPENCLAW_COLD_SESSION = "7d0c2a8e-1111-4000-8000-000000000003"
OPENCLAW_LEGACY = "7d0c2a8e-1111-4000-8000-0000000000aa"
OPENCLAW_DELETED = "7d0c2a8e-1111-4000-8000-0000000000dd"
OPENCLAW_TOKEN = "sk-ant-oat01-FIXTURE-OPENCLAW-TOKEN-0f9e8d"
OPENCLAW_AGENT = ".openclaw/agents/main"
OPENCLAW_CHECKPOINT = ".checkpoint.0b5e1c2d-3f4a-4b5c-8d6e-7f8091a2b3c4.jsonl"
OPENCLAW_REPAIR_BAK = ".jsonl.pre-doctor-branch-repair-2026-09-20T08-10-00-000Z.bak"

# Columns of src/state/openclaw-agent-schema.sql at 3b16db7 that the parser
# reads (CHECK constraints and unrelated columns left out).
OPENCLAW_SCHEMA = """
CREATE TABLE session_windows (session_id TEXT NOT NULL PRIMARY KEY, session_key TEXT NOT NULL,
  previous_session_id TEXT, reason TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
  started_at INTEGER, ended_at INTEGER, status TEXT, chat_type TEXT, channel TEXT, account_id TEXT,
  model_provider TEXT, model TEXT, parent_session_key TEXT, spawned_by TEXT, display_name TEXT);
CREATE TABLE transcript_events (session_id TEXT NOT NULL, seq INTEGER NOT NULL, event_json TEXT,
  created_at INTEGER NOT NULL, event_zstd BLOB, event_utf8_bytes INTEGER, navigation_json TEXT,
  PRIMARY KEY (session_id, seq));
CREATE TABLE session_transcript_archives (session_id TEXT NOT NULL, generation TEXT NOT NULL,
  session_key TEXT NOT NULL, reason TEXT NOT NULL, encoding TEXT NOT NULL, archive_blob BLOB NOT NULL,
  archive_sha256 TEXT NOT NULL, archive_name TEXT NOT NULL UNIQUE, created_at INTEGER NOT NULL,
  published_at INTEGER, PRIMARY KEY (session_id, generation));
CREATE TABLE session_transcript_cold_archives (session_id TEXT NOT NULL PRIMARY KEY, generation TEXT NOT NULL,
  archive_name TEXT NOT NULL UNIQUE, archive_sha256 TEXT NOT NULL, event_count INTEGER NOT NULL,
  raw_bytes INTEGER NOT NULL, archive_bytes INTEGER NOT NULL, last_seq INTEGER NOT NULL,
  archived_at INTEGER NOT NULL, storage TEXT NOT NULL, archive_blob BLOB);
CREATE TABLE auth_profile_store (store_key TEXT NOT NULL PRIMARY KEY, store_json TEXT NOT NULL,
  updated_at INTEGER NOT NULL);
"""


def openclaw_records(session_id=OPENCLAW_SESSION, cwd="/srv/proj"):
    """The research document's sample entries (section 8), cwd moved to /srv/proj."""
    return [
        {
            "type": "session",
            "version": 4,
            "id": session_id,
            "timestamp": "2026-10-01T09:00:00.000Z",
            "cwd": cwd,
        },
        {
            "type": "message",
            "id": "a1b2c3d4",
            "parentId": None,
            "timestamp": "2026-10-01T09:00:01.000Z",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "check disk space on the server"}],
                "timestamp": 1790845201000,
            },
        },
        {
            "type": "message",
            "id": "b2c3d4e5",
            "parentId": "a1b2c3d4",
            "timestamp": "2026-10-01T09:00:04.000Z",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "Use exec with df.",
                        "thinkingSignature": "sig-opaque",
                    },
                    {"type": "text", "text": "Checking."},
                    {
                        "type": "toolCall",
                        "id": "call_01",
                        "name": "exec",
                        "arguments": {"command": "df -h"},
                    },
                ],
                "api": "anthropic-messages",
                "provider": "anthropic",
                "model": "claude-sonnet-4-5",
                "usage": {
                    "input": 900,
                    "output": 40,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                    "totalTokens": 940,
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0},
                },
                "stopReason": "toolUse",
                "timestamp": 1790845204000,
            },
        },
        {
            "type": "message",
            "id": "c3d4e5f6",
            "parentId": "b2c3d4e5",
            "timestamp": "2026-10-01T09:00:05.000Z",
            "message": {
                "role": "toolResult",
                "toolCallId": "call_01",
                "toolName": "exec",
                "content": [{"type": "text", "text": "/dev/sda1  50G  20G  30G  40% /"}],
                "isError": False,
                "timestamp": 1790845205000,
            },
        },
        {
            "type": "model_change",
            "id": "d4e5f6a7",
            "parentId": "c3d4e5f6",
            "timestamp": "2026-10-01T09:01:00.000Z",
            "provider": "openai",
            "modelId": "gpt-5",
        },
    ]


def openclaw_legacy_records(session_id=OPENCLAW_LEGACY):
    return [
        {
            "type": "session",
            "version": 3,
            "id": session_id,
            "timestamp": "2026-09-20T08:00:00.000Z",
            "cwd": "/srv/proj",
        },
        {
            "type": "message",
            "id": "e1",
            "parentId": None,
            "timestamp": "2026-09-20T08:00:01.000Z",
            "message": {
                "role": "user",
                "content": "<runtime>channel=telegram</runtime>",
                "runtimeContext": {"retained": True},
                "timestamp": 1789891201000,
            },
        },
        {
            "type": "message",
            "id": "e2",
            "parentId": "e1",
            "timestamp": "2026-09-20T08:00:02.000Z",
            "message": {
                "role": "bashExecution",
                "command": "uptime",
                "output": "up 3 days",
                "exitCode": 0,
                "cancelled": False,
                "truncated": False,
                "timestamp": 1789891202000,
            },
        },
        {
            "type": "compaction",
            "id": "e3",
            "parentId": "e2",
            "timestamp": "2026-09-20T08:05:00.000Z",
            "summary": "checked uptime",
            "firstKeptEntryId": "e2",
            "tokensBefore": 5000,
        },
        {
            "type": "message",
            "id": "e4",
            "parentId": "e3",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "partial"}],
                "model": "gpt-5",
                "stopReason": "error",
                "errorMessage": "rate limited",
                "timestamp": 1789891510000,
            },
        },
    ]


# Session sync (issue 153): session_nodes (src/state/openclaw-agent-schema.sql:16-49
# at 3b16db7, the columns the parser reads) with a `publicShare` grant
# (src/config/sessions/types.ts:627-628) on the live session and none on the
# reset one, and state/openclaw.sqlite backup_runs
# (src/state/openclaw-state-schema.sql:1843-1849) with manifests shaped by
# src/state/backup-run-records.contract.ts:98-124.
OPENCLAW_SHARE_ID = "0a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f6071"
OPENCLAW_STATE_DB = ".openclaw/state/openclaw.sqlite"
OPENCLAW_BACKUP_KEY = "backups/main/2026-10-01T10-20-00Z-0a1b2c3d.tar.gz"
OPENCLAW_BACKUP_COMMIT = "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432"
OPENCLAW_NODES_SCHEMA = """
CREATE TABLE session_nodes (session_key TEXT NOT NULL PRIMARY KEY, current_session_id TEXT NOT NULL,
  entry_json TEXT NOT NULL, updated_at INTEGER NOT NULL, created_via TEXT, label TEXT);
"""
OPENCLAW_STATE_SCHEMA = """
CREATE TABLE backup_runs (id TEXT NOT NULL PRIMARY KEY, created_at INTEGER NOT NULL,
  archive_path TEXT NOT NULL, status TEXT NOT NULL, manifest_json TEXT NOT NULL) STRICT;
"""


def openclaw_node_inserts():
    """A published live session and an unpublished reset session."""
    shared = {
        "sessionId": OPENCLAW_SESSION,
        "updatedAt": 1790845260000,
        "publicShare": {
            "id": OPENCLAW_SHARE_ID,
            "sessionId": OPENCLAW_SESSION,
            "createdAt": 1790845320000,
        },
    }
    plain = {"sessionId": OPENCLAW_RESET_SESSION, "updatedAt": 1790847000000}
    return [
        "INSERT INTO session_nodes VALUES ('%s','%s','%s',1790845320000,'channel',NULL)"
        % (OPENCLAW_KEY, OPENCLAW_SESSION, json.dumps(shared)),
        "INSERT INTO session_nodes VALUES ('agent:main:main','%s','%s',1790847000000,'operator',NULL)"
        % (OPENCLAW_RESET_SESSION, json.dumps(plain)),
    ]


def openclaw_backup_runs():
    """(id, created_at, archive_path, status, manifest): an offsite archive
    upload and a pushed Git backup, which yield rows, and a Git backup whose
    push failed, a local archive and a failed upload, which do not."""
    location = {
        "name": "r2-offsite",
        "provider": "cloudflare-r2",
        "locationId": "loc-01",
        "key": OPENCLAW_BACKUP_KEY,
        "namespace": "main",
        "plaintextBytes": 81920,
        "storedBytes": 40960,
    }
    return [
        (
            "run-01",
            1790850000000,
            "/home/alice/.openclaw/backups/2026-10-01T10-20-00Z.tar.gz",
            "ok",
            {
                "kind": "archive",
                "target": "r2-offsite",
                "namespace": "main",
                "bytes": 81920,
                "location": location,
                "retention": {"kept": 1, "deleted": 0},
            },
        ),
        (
            "run-02",
            1790852400000,
            "/home/alice/openclaw-backup.git",
            "ok",
            {"kind": "git", "target": OPENCLAW_BACKUP_COMMIT, "namespace": "main"},
        ),
        (
            "run-03",
            1790856000000,
            "/home/alice/openclaw-backup.git",
            "ok",
            {"kind": "git", "target": "1" * 40, "namespace": "main", "pushFailed": True},
        ),
        (
            "run-04",
            1790859600000,
            "/home/alice/.openclaw/backups/local.tar.gz",
            "ok",
            {"kind": "archive", "namespace": "main"},
        ),
        (
            "run-05",
            1790863200000,
            "/home/alice/.openclaw/backups/failed.tar.gz",
            "failed",
            {"kind": "archive", "target": "r2-offsite", "error": "upload refused"},
        ),
    ]


def build_openclaw_state(home: Path) -> None:
    inserts = [
        "INSERT INTO backup_runs VALUES ('%s',%d,'%s','%s','%s')"
        % (rid, created, path, status, json.dumps(manifest))
        for rid, created, path, status, manifest in openclaw_backup_runs()
    ]
    _wal_db(home / OPENCLAW_STATE_DB, OPENCLAW_STATE_SCHEMA, inserts)


def _openclaw_zstd(raw: bytes) -> bytes:
    """zstd-compressed bytes, as OpenClaw writes them."""
    return zstandard.ZstdCompressor(level=1, write_checksum=True).compress(raw)


def _openclaw_jsonl(records) -> bytes:
    return "".join(json.dumps(r) + "\n" for r in records).encode("utf-8")


def build_openclaw(home: Path) -> None:
    agent = home / OPENCLAW_AGENT
    inserts = [
        "INSERT INTO session_windows VALUES ('%s','%s',NULL,'initial',1790845200000,1790845260000,1790845200000,"
        "NULL,'running','direct','telegram','default','anthropic','claude-sonnet-4-5',NULL,NULL,'Disk check')"
        % (OPENCLAW_SESSION, OPENCLAW_KEY),
        "INSERT INTO auth_profile_store VALUES ('anthropic:default','%s',1790845200000)"
        % json.dumps(
            {"type": "oauth", "access": OPENCLAW_TOKEN, "refresh": OPENCLAW_TOKEN + "-refresh"}
        ),
    ]
    for seq, rec in enumerate(openclaw_records()):
        raw = json.dumps(rec)
        z = _openclaw_zstd(raw.encode("utf-8")) if rec.get("id") == "b2c3d4e5" else None
        created = 1790845200000 + seq * 1000
        if z is not None:
            inserts.append(
                "INSERT INTO transcript_events VALUES ('%s',%d,NULL,%d,X'%s',%d,'{\"version\":1}')"
                % (OPENCLAW_SESSION, seq, created, z.hex(), len(raw))
            )
        else:
            inserts.append(
                "INSERT INTO transcript_events VALUES ('%s',%d,'%s',%d,NULL,NULL,NULL)"
                % (OPENCLAW_SESSION, seq, raw.replace("'", "''"), created)
            )
    reset = _openclaw_jsonl(
        [
            *openclaw_records(OPENCLAW_RESET_SESSION)[:2],
            {
                "type": "reset",
                "id": "r1",
                "parentId": "a1b2c3d4",
                "timestamp": "2026-10-01T09:30:00.000Z",
                "reason": "reset",
            },
        ]
    )
    inserts.append(
        "INSERT INTO session_transcript_archives VALUES ('%s','g1','%s','reset','identity',X'%s','%s',"
        "'%s.jsonl.reset.2026-10-01T09-30-00.000Z',1790847000000,NULL)"
        % (OPENCLAW_RESET_SESSION, OPENCLAW_KEY, reset.hex(), "0" * 64, OPENCLAW_RESET_SESSION)
    )
    # Published: the same zstd bytes are the .jsonl.deleted.*.zst file below.
    deleted = _openclaw_jsonl(openclaw_records(OPENCLAW_DELETED)[:2])
    inserts.append(
        "INSERT INTO session_transcript_archives VALUES ('%s','g2','%s','deleted','zstd',X'%s','%s',"
        "'%s.jsonl.deleted.2026-10-02T08-00-00.000Z.zst',1790928000000,1790928000500)"
        % (
            OPENCLAW_DELETED,
            OPENCLAW_KEY,
            _openclaw_zstd(deleted).hex(),
            "1" * 64,
            OPENCLAW_DELETED,
        )
    )
    cold = [
        {"kind": "header", "version": 1, "sessionId": OPENCLAW_COLD_SESSION, "generation": "g0"}
    ]
    for seq, rec in enumerate(openclaw_records(OPENCLAW_COLD_SESSION)[:2]):
        cold.append(
            {
                "kind": "event",
                "row": {"seq": seq, "event_json": json.dumps(rec), "created_at": 1790845200000},
            }
        )
        cold.append({"kind": "identity", "row": {"event_id": rec["id"], "seq": seq}})
    cold_raw = _openclaw_jsonl(cold)
    cold_blob = _openclaw_zstd(cold_raw)
    inserts.append(
        "INSERT INTO session_transcript_cold_archives VALUES ('%s','g0','%s.jsonl.zst','%s',2,%d,%d,1,"
        "1790850000000,'sqlite',X'%s')"
        % (
            OPENCLAW_COLD_SESSION,
            "c" * 64,
            "2" * 64,
            len(cold_raw),
            len(cold_blob),
            cold_blob.hex(),
        )
    )
    _wal_db(
        agent / "agent/openclaw-agent.sqlite",
        OPENCLAW_SCHEMA + OPENCLAW_NODES_SCHEMA,
        inserts + openclaw_node_inserts(),
    )
    sessions = agent / "sessions"
    _jsonl(sessions / (OPENCLAW_LEGACY + ".jsonl"), openclaw_legacy_records())
    (sessions / "sessions.json").write_text(
        json.dumps({OPENCLAW_KEY: {"sessionId": OPENCLAW_LEGACY, "updatedAt": 1789891510000}}),
        encoding="utf-8",
    )
    name = OPENCLAW_DELETED + ".jsonl.deleted.2026-10-02T08-00-00.000Z"
    (sessions / (name + ".zst")).write_bytes(_openclaw_zstd(deleted))
    # Secondary copies (issue 122): a pre-compaction checkpoint holds the
    # entries before the compaction; a pre-doctor branch-repair backup holds
    # the whole file before the repair, with an abandoned branch the
    # repaired file dropped.
    _jsonl(sessions / (OPENCLAW_LEGACY + OPENCLAW_CHECKPOINT), openclaw_legacy_records()[:3])
    _jsonl(
        sessions / (OPENCLAW_LEGACY + OPENCLAW_REPAIR_BAK),
        [
            *openclaw_legacy_records(),
            {
                "type": "message",
                "id": "e9",
                "parentId": "e1",
                "timestamp": "2026-09-20T08:00:30.000Z",
                "message": {
                    "role": "user",
                    "content": "abandoned branch prompt",
                    "timestamp": 1789891230000,
                },
            },
        ],
    )
    # Noise the parser must skip: a trajectory (another schema) and a
    # `.migrated` file (not confirmed as a transcript).
    _jsonl(sessions / (OPENCLAW_LEGACY + ".trajectory.jsonl"), [{"type": "trace"}])
    _jsonl(sessions / (OPENCLAW_LEGACY + ".jsonl.migrated"), openclaw_legacy_records())
    (agent / "agent/auth-profiles.json").write_text(
        json.dumps({"anthropic:default": {"key": OPENCLAW_TOKEN}}), encoding="utf-8"
    )
    (home / ".openclaw/openclaw.json").write_text('{"agents": {}}', encoding="utf-8")


# -- nanobot (HKUDS/nanobot at acdae3d) ------------------------------------------
NANOBOT_KEY = "telegram:123456789"
NANOBOT_WS = "0123456789abcdef0123456789abcdef"
NANOBOT_REL = ".nanobot/sessions/%s/dGVsZWdyYW06MTIzNDU2Nzg5.jsonl" % NANOBOT_WS
NANOBOT_LEGACY_REL = ".nanobot/sessions/cli_direct.jsonl"
NANOBOT_HISTORY_REL = ".nanobot/workspace/memory/history.jsonl"


def nanobot_records():
    """The research document's sample file (section 8), plus a hidden-history
    message and a provider_state line."""
    return [
        {
            "_type": "metadata",
            "key": NANOBOT_KEY,
            "created_at": "2026-10-01T10:15:00.000001",
            "updated_at": "2026-10-01T10:15:09.500000",
            "metadata": {"last_channel": NANOBOT_KEY},
            "last_archived": 0,
            "last_consolidated": 0,
        },
        {"_type": "provider_state", "state": {"opaque": "x"}},
        {
            "role": "user",
            "content": "[earlier conversation summarised]",
            "_hidden_history": True,
            "timestamp": "2026-10-01T10:15:00.500000",
        },
        {
            "role": "user",
            "content": "what is using port 8080?",
            "timestamp": "2026-10-01T10:15:01.200000",
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "exec",
                        "arguments": '{"command": "ss -ltnp | grep 8080"}',
                    },
                }
            ],
            "reasoning_content": "Check listening sockets.",
            "timestamp": "2026-10-01T10:15:04.000000",
        },
        {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "name": "exec",
            "content": 'LISTEN 0 128 *:8080 users:(("python3",pid=4242))',
            "timestamp": "2026-10-01T10:15:05.000000",
        },
        {
            "role": "assistant",
            "content": "python3 (pid 4242) is listening on 8080.",
            "timestamp": "2026-10-01T10:15:09.400000",
        },
    ]


def build_nanobot(home: Path) -> None:
    _jsonl(home / NANOBOT_REL, nanobot_records())
    (home / NANOBOT_REL).parent.joinpath(".workspace").write_text("/srv/proj\n", encoding="utf-8")
    (home / NANOBOT_REL).parent.joinpath("dGVsZWdyYW06MTIzNDU2Nzg5.checkpoint.json").write_text(
        "{}", encoding="utf-8"
    )
    _jsonl(
        home / NANOBOT_LEGACY_REL,
        [
            {
                "_type": "metadata",
                "key": "cli:direct",
                "created_at": "2026-09-01T08:00:00",
                "updated_at": "2026-09-01T08:00:05",
                "metadata": {"_nanobot_model_preset": "fast"},
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": "hello"}],
                "timestamp": "2026-09-01T08:00:01",
            },
            {"role": "assistant", "content": "hi"},
        ],
    )
    _jsonl(
        home / NANOBOT_HISTORY_REL,
        [
            {
                "cursor": 1,
                "timestamp": "2026-09-30 22:10",
                "content": "User asked about disk usage.",
                "session_key": NANOBOT_KEY,
            },
            {
                "cursor": 2,
                "timestamp": "2026-10-01 10:20",
                "content": "Found python3 on port 8080.",
            },
        ],
    )
    (home / ".nanobot/config.json").write_text(
        '{"providers": {"openai": {"apiKey": "sk-not-real"}}}', encoding="utf-8"
    )


# nanobot WebUI mirror and CLI history (issue 122). The host is taken to be
# at UTC+2: the session file's local times read two hours later than the
# WebUI's true-UTC created_at_ms.
NANOBOT_WEBUI_KEY = "websocket:chat-1"
NANOBOT_WEBUI_SESSION_REL = ".nanobot/sessions/%s/d2Vic29ja2V0OmNoYXQtMQ.jsonl" % NANOBOT_WS
NANOBOT_WEBUI_REL = ".nanobot/webui/websocket_chat-1.jsonl"
NANOBOT_WEBUI_SEGMENT_REL = ".nanobot/webui/websocket_chat-1.segments/000001.jsonl"
NANOBOT_CLI_HISTORY_REL = ".nanobot/history/cli_history"


def nanobot_webui_records():
    """The active WebUI file: one turn the session file also holds."""
    turn = {"chat_id": "chat-1", "turn_id": "t-2"}
    return [
        {"event": "user", **turn, "text": "show disk usage", "created_at_ms": 1790924400900},
        {
            "event": "reasoning_end",
            **turn,
            "text": "Run df.",
            "created_at_ms": 1790924401500,
        },
        {
            "event": "message",
            **turn,
            "kind": "tool_hint",
            "text": 'exec("df -h")',
            "tool_events": [
                {
                    "version": 1,
                    "phase": "start",
                    "call_id": "call_df1",
                    "name": "exec",
                    "arguments": {"command": "df -h"},
                    "result": None,
                }
            ],
            "created_at_ms": 1790924402000,
        },
        {
            "event": "message",
            **turn,
            "kind": "progress",
            "text": "",
            "tool_events": [
                {
                    "version": 1,
                    "phase": "end",
                    "call_id": "call_df1",
                    "name": "exec",
                    "arguments": {"command": "df -h"},
                    "result": "/dev/sda1 42%",
                }
            ],
            "created_at_ms": 1790924404000,
        },
        {
            "event": "file_edit",
            **turn,
            "edits": [
                {
                    "call_id": "call_w1",
                    "tool": "write_file",
                    "path": "notes.txt",
                    "absolute_path": "/srv/proj/notes.txt",
                    "phase": "end",
                    "status": "done",
                    "added": 1,
                    "deleted": 0,
                }
            ],
            "created_at_ms": 1790924404500,
        },
        {"event": "delta", **turn, "text": "The disk", "created_at_ms": 1790924405000},
        {
            "event": "stream_end",
            **turn,
            "text": "The disk is",
            "merge_next": True,
            "created_at_ms": 1790924405200,
        },
        {
            "event": "stream_end",
            **turn,
            "text": "The disk is 42% full.",
            "created_at_ms": 1790924405500,
        },
        {"event": "turn_end", **turn, "latency_ms": 5100, "created_at_ms": 1790924406000},
    ]


def build_nanobot_webui(home: Path) -> None:
    """A WebUI chat whose session file holds only the second turn (a `/new`
    emptied the first), its WebUI mirror (the first turn rotated into a
    segment), and the CLI history with one prompt of the legacy cli:direct
    session and one whose session is gone."""
    _jsonl(
        home / NANOBOT_WEBUI_SESSION_REL,
        [
            {
                "_type": "metadata",
                "key": NANOBOT_WEBUI_KEY,
                "created_at": "2026-10-02T09:00:00",
                "updated_at": "2026-10-02T09:00:06",
                "metadata": {"last_channel": NANOBOT_WEBUI_KEY},
            },
            {"role": "user", "content": "show disk usage", "timestamp": "2026-10-02T09:00:01"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_df1",
                        "type": "function",
                        "function": {"name": "exec", "arguments": '{"command": "df -h"}'},
                    }
                ],
                "timestamp": "2026-10-02T09:00:06",
            },
            {
                "role": "tool",
                "tool_call_id": "call_df1",
                "name": "exec",
                "content": "/dev/sda1 42%",
                "timestamp": "2026-10-02T09:00:06",
            },
            {
                "role": "assistant",
                "content": "The disk is 42% full.",
                "timestamp": "2026-10-02T09:00:06",
            },
        ],
    )
    _jsonl(home / NANOBOT_WEBUI_REL, nanobot_webui_records())
    old = {"chat_id": "chat-1", "turn_id": "t-1"}
    _jsonl(
        home / NANOBOT_WEBUI_SEGMENT_REL,
        [
            {"event": "user", **old, "text": "list the old logs", "created_at_ms": 1789905600000},
            {
                "event": "message",
                **old,
                "text": "There are 3 old logs.",
                "created_at_ms": 1789905603000,
            },
            {"event": "fork_marker", "chat_id": "chat-1", "created_at_ms": 1789905604000},
        ],
    )
    segments = (home / NANOBOT_WEBUI_SEGMENT_REL).parent
    (segments / "manifest.json").write_text(
        '{"version": 2, "segments": [{"id": "000001", "turn_count": 1}]}', encoding="utf-8"
    )
    (home / ".nanobot/webui/sidebar-state.json").write_text("{}", encoding="utf-8")
    (home / NANOBOT_CLI_HISTORY_REL).parent.mkdir(parents=True, exist_ok=True)
    (home / NANOBOT_CLI_HISTORY_REL).write_text(
        "\n# 2026-09-01 08:00:01.200000\n+hello\n"
        "\n# 2026-09-01 07:59:00.000000\n+first line\n+second line\n",
        encoding="utf-8",
    )


# ---- VS Code state.vscdb rows (Cody, Twinny) and PearAI ----------------------------
# Shapes from analyzer/research/cody.md, twinny.md and pearai.md.

VSCDB_SCHEMA = "CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB);"


def _vscdb(path: Path, items: dict) -> None:
    """Add `ItemTable` rows to a plain (non-WAL) state.vscdb."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.executescript(VSCDB_SCHEMA.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS"))
    for k, v in items.items():
        con.execute(
            "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
            (k, (v if isinstance(v, str) else json.dumps(v)).encode("utf-8")),
        )
    con.commit()
    con.close()


CODY_ACCOUNT = "https://sourcegraph.com/-alice"
CODY_CHAT = "Sat, 03 Oct 2026 10:00:00 GMT"
CODY_AGENTIC_CHAT = "Sat, 03 Oct 2026 10:30:00 GMT"
CODY_VSCODE_CHAT = "Sat, 03 Oct 2026 09:00:00 GMT"
CODY_MODEL = "anthropic::2024-10-22::claude-sonnet-4-latest"
CODY_MODEL_SWITCHED = "anthropic::2024-10-22::claude-3-5-haiku-latest"
CODY_JB_REL = ".local/share/Cody-nodejs/JetBrains-globalState/cody-local-chatHistory-v2"
CODY_VSCDB_REL = ".config/VSCodium/User/globalStorage/state.vscdb"
CODY_TOKEN = "sgp_cody_secret_not_real"


def cody_records():
    """The JetBrains AccountKeyedChatHistory: the research fixture chat and
    its agentic variant."""
    chat = {
        "id": CODY_CHAT,
        "chatTitle": "Fix flaky test",
        "lastInteractionTimestamp": CODY_CHAT,
        "interactions": [
            {
                "humanMessage": {
                    "speaker": "human",
                    "text": "why is test_login flaky?",
                    "intent": "chat",
                    "contextFiles": [
                        {
                            "type": "file",
                            "source": "user",
                            "uri": {
                                "$mid": 1,
                                "fsPath": "/srv/proj/tests/test_login.py",
                                "path": "/srv/proj/tests/test_login.py",
                                "scheme": "file",
                            },
                        }
                    ],
                },
                "assistantMessage": {
                    "speaker": "assistant",
                    "model": CODY_MODEL,
                    "text": "It depends on wall-clock time.",
                    "intent": "chat",
                },
            }
        ],
    }
    agentic = {
        "id": CODY_AGENTIC_CHAT,
        "chatTitle": "run the tests",
        "lastInteractionTimestamp": CODY_AGENTIC_CHAT,
        "interactions": [
            {
                "humanMessage": {"speaker": "human", "text": "run the tests", "intent": "agentic"},
                "assistantMessage": {
                    "speaker": "assistant",
                    "model": CODY_MODEL,
                    "text": "Running tests.",
                    "content": [
                        {"type": "text", "text": "Running tests."},
                        {
                            "type": "tool_call",
                            "tool_call": {
                                "id": "toolu_01",
                                "name": "run_terminal_command",
                                "arguments": '{"command":"pytest -q"}',
                            },
                        },
                    ],
                    "processes": [
                        {
                            "type": "confirmation",
                            "id": "toolu_01",
                            "title": "Run terminal command",
                            "description": "pytest -q",
                            "content": "Allow Cody to run this command?",
                            "state": "success",
                        },
                        {
                            "type": "tool",
                            "id": "toolu_01",
                            "title": "run_terminal_command",
                            "content": "pytest -q",
                            "state": "success",
                        },
                    ],
                },
            },
            {
                "humanMessage": {
                    "speaker": "human",
                    "text": "",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_result": {"id": "toolu_01", "content": "3 passed"},
                        }
                    ],
                },
                "assistantMessage": {
                    "speaker": "assistant",
                    "model": CODY_MODEL_SWITCHED,
                    "text": "All three pass.",
                    "error": {"name": "RateLimitError", "message": "rate limit exceeded"},
                },
            },
        ],
    }
    return {CODY_ACCOUNT: {"chat": {CODY_CHAT: chat, CODY_AGENTIC_CHAT: agentic}}}


def cody_vscode_state():
    """The `sourcegraph.cody-ai` global state value of a VS Code install."""
    return {
        "cody-local-chatHistory-v2": {
            CODY_ACCOUNT: {
                "chat": {
                    CODY_VSCODE_CHAT: {
                        "id": CODY_VSCODE_CHAT,
                        "lastInteractionTimestamp": CODY_VSCODE_CHAT,
                        "interactions": [
                            {
                                "humanMessage": {"speaker": "human", "text": "explain build.sh"},
                                "assistantMessage": {
                                    "speaker": "assistant",
                                    "model": CODY_MODEL,
                                    "text": "It runs make.",
                                },
                            }
                        ],
                    }
                }
            }
        },
        "cody-anonymous-user-id": "anon-1",
    }


def build_cody(home: Path) -> None:
    jb = home / CODY_JB_REL
    jb.parent.mkdir(parents=True, exist_ok=True)
    jb.write_text(json.dumps(cody_records()), encoding="utf-8")
    (home / ".local/share/Cody-nodejs/user-settings.json").write_text(
        '{"cody.serverEndpoint": "x"}', encoding="utf-8"
    )
    _vscdb(
        home / CODY_VSCDB_REL,
        {
            "sourcegraph.cody-ai": cody_vscode_state(),
            'secret://{"extensionId":"sourcegraph.cody-ai","key":"cody.access-token"}': CODY_TOKEN,
        },
    )


TWINNY_CONVERSATION = "7d1c2b3a-1111-4000-8000-000000000001"
TWINNY_ACTIVE = "7d1c2b3a-1111-4000-8000-000000000002"
TWINNY_API_KEY = "sk-twinny-fixture-not-real"
TWINNY_VSCDB_REL = ".vscode-server/data/User/globalStorage/state.vscdb"


def twinny_records():
    """The `rjmacarthy.twinny` global state value: the research fixture plus
    an unsaved active conversation, a failed tool step and provider keys."""
    return {
        "twinny.conversations": {
            TWINNY_CONVERSATION: {
                "id": TWINNY_CONVERSATION,
                "title": "List the tests",
                "updatedAt": 1791028805000,
                "messages": [
                    {"role": "user", "content": "which tests fail?"},
                    {
                        "role": "assistant",
                        "content": "<think>run the suite</think>Two tests fail.",
                        "meta": {
                            "model": "qwen2.5-coder:7b",
                            "provider": "Ollama",
                            "durationMs": 5200,
                            "withheld": [{"kind": "aws-key", "count": 1}],
                        },
                        "toolSteps": [
                            {
                                "id": "step-1",
                                "name": "run_command",
                                "summary": "ran `npm test`",
                                "args": {"command": "npm test"},
                                "output": "2 failing",
                                "status": "done",
                            },
                            {
                                "id": "step-2",
                                "name": "read_file",
                                "args": {"path": "src/a.ts"},
                                "output": "permission denied",
                                "status": "failed",
                            },
                        ],
                    },
                    {
                        # A switched model, a step saved while it waited for Run or
                        # Skip, and a skipped one (tool-steps.ts at 9339bd10).
                        "role": "assistant",
                        "content": "Cleaning the build.",
                        "meta": {"model": "qwen2.5-coder:14b", "provider": "Ollama"},
                        "toolSteps": [
                            {
                                "id": "step-3",
                                "name": "run_command",
                                "summary": "wants to run `rm -rf build`",
                                "args": {"command": "rm -rf build"},
                                "command": "rm -rf build",
                                "approval": "command",
                                "status": "waiting",
                            },
                            {
                                "id": "step-4",
                                "name": "delete_file",
                                "summary": "skipped",
                                "args": {"path": "dist"},
                                "output": "skipped by the user",
                                "status": "skipped",
                            },
                        ],
                    },
                ],
            }
        },
        "twinny.active-conversation": {
            "id": TWINNY_ACTIVE,
            "title": "draft",
            "updatedAt": 1791028900000,
            "messages": [{"role": "user", "content": "unsaved question"}],
        },
        "twinny.inference-providers": {
            "p1": {
                "id": "p1",
                "label": "Ollama",
                "provider": "ollama",
                "type": "chat",
                "modelName": "qwen2.5-coder:7b",
                "apiHostname": "localhost",
                "apiPort": 11434,
                "apiKey": TWINNY_API_KEY,
            }
        },
        "twinny.active-chat-provider": {"id": "p1", "apiKey": TWINNY_API_KEY},
    }


def build_twinny(home: Path) -> None:
    """Rows only in the -wal sidecar, as with the editor still running."""

    def lit(s):
        return "'" + s.replace("'", "''") + "'"

    _wal_db(
        home / TWINNY_VSCDB_REL,
        VSCDB_SCHEMA,
        [
            "INSERT INTO ItemTable VALUES ('rjmacarthy.twinny', CAST(%s AS BLOB))"
            % lit(json.dumps(twinny_records())),
            "INSERT INTO ItemTable VALUES (%s, %s)"
            % (
                lit('secret://{"extensionId":"rjmacarthy.twinny","key":"gateway"}'),
                lit(TWINNY_API_KEY),
            ),
        ],
    )
    tw = home / ".config/Code/User/globalStorage/rjmacarthy.twinny"
    tw.mkdir(parents=True, exist_ok=True)
    (tw / "twinny-providers.json").write_text(
        json.dumps({"apiKey": TWINNY_API_KEY}), encoding="utf-8"
    )


PEARAI_SESSION = "9b1c2d3e-0000-4000-8000-000000000001"
PEARAI_SEARCH_SESSION = "9b1c2d3e-0000-4000-8000-000000000002"
PEARAI_TASK = "1791036000000"
PEARAI_UI_TASK = "1791039600000"
PEARAI_GS = ".config/PearAI/User/globalStorage/"
PEARAI_ROO = PEARAI_GS + "pearai.pearai-roo-cline/"


def pearai_session():
    return {
        "history": [
            {
                "message": {"role": "user", "content": "why does build.sh fail"},
                "contextItems": [
                    {
                        "content": "set -e\nmake all",
                        "name": "build.sh",
                        "description": "/srv/proj/build.sh",
                        "id": {"providerTitle": "file", "itemId": "build.sh"},
                    }
                ],
            },
            {
                "message": {"role": "assistant", "content": "The make target is missing."},
                "contextItems": [],
                "promptLogs": [
                    {
                        "completionOptions": {"model": "pearai_model"},
                        "prompt": "<user>why does build.sh fail",
                        "completion": "The make target is missing.",
                    }
                ],
            },
            {"message": {"role": "user", "content": "add the target"}, "contextItems": []},
            {
                "message": {"role": "assistant", "content": "Added `all:` to the Makefile."},
                "contextItems": [],
                "promptLogs": [
                    {
                        "completionOptions": {"model": "pearai_model_2"},
                        "prompt": "<user>add the target",
                        "completion": "Added `all:` to the Makefile.",
                    }
                ],
            },
        ],
        "perplexityHistory": [],
        "title": "why does build.sh fail",
        "sessionId": PEARAI_SESSION,
        "workspaceDirectory": "/srv/proj",
    }


def pearai_search_session():
    return {
        "history": [],
        "perplexityHistory": [
            {
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "latest make release"}],
                },
                "contextItems": [],
            },
            {
                "message": {"role": "assistant", "content": "GNU make 4.4.1."},
                "contextItems": [],
                "citations": [{"url": "https://www.gnu.org/software/make/", "title": "GNU Make"}],
            },
        ],
        "title": "latest make release",
        "sessionId": PEARAI_SEARCH_SESSION,
        "workspaceDirectory": "/srv/proj",
    }


def pearai_index():
    return [
        {
            "sessionId": PEARAI_SESSION,
            "title": "why does build.sh fail",
            "dateCreated": "1791032400000",
            "workspaceDirectory": "/srv/proj",
            "integrationType": "continue",
        },
        {
            "sessionId": PEARAI_SEARCH_SESSION,
            "title": "latest make release",
            "dateCreated": "1791032500000",
            "workspaceDirectory": "/srv/proj",
            "integrationType": "perplexity",
        },
    ]


def pearai_api_records(t0=1791036000000):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "<task>\nrun the tests\n</task>"},
                {
                    "type": "text",
                    "text": "<environment_details>\n# Current Working Directory "
                    "(/srv/proj)\n</environment_details>",
                },
            ],
            "ts": t0,
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "<thinking>use npm</thinking>\nI will run them.\n<execute_command>\n<command>npm test</command>\n"
                    "</execute_command>",
                }
            ],
            "ts": t0 + 3000,
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "[execute_command for 'npm test'] Result:"},
                {"type": "text", "text": "12 passing"},
            ],
            "ts": t0 + 9000,
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "<attempt_completion>\n<result>All 12 tests pass.</result>\n</attempt_completion>",
                }
            ],
            "ts": t0 + 10000,
        },
    ]


def build_pearai(home: Path) -> None:
    sessions = home / ".pearai/sessions"
    _json(sessions / (PEARAI_SESSION + ".json"), pearai_session())
    _json(sessions / (PEARAI_SEARCH_SESSION + ".json"), pearai_search_session())
    _json(sessions / "sessions.json", pearai_index())
    (home / ".pearai/config.json").write_text('{"models": []}', encoding="utf-8")
    roo = home / PEARAI_ROO
    _json(roo / "tasks" / PEARAI_TASK / "api_conversation_history.json", pearai_api_records())
    _json(roo / "tasks" / PEARAI_TASK / "task_metadata.json", {"files_in_context": []})
    _json(roo / "tasks" / PEARAI_UI_TASK / "ui_messages.json", roo_ui_records(int(PEARAI_UI_TASK)))
    _json(
        roo / "tasks" / PEARAI_UI_TASK / "api_conversation_history.json",
        pearai_api_records(int(PEARAI_UI_TASK)),
    )
    _vscdb(
        home / PEARAI_GS / "state.vscdb",
        {
            "pearai.pearai-roo-cline": {
                "taskHistory": [
                    {
                        "id": PEARAI_TASK,
                        "number": 1,
                        "ts": 1791036010000,
                        "task": "run the tests",
                        "tokensIn": 900,
                        "tokensOut": 40,
                        "totalCost": 0.002,
                        "workspace": "/srv/proj",
                    }
                ]
            }
        },
    )


MUSE_SESSION = "01a0f000-0000-7000-8000-000000000001"
MUSE_CHILD = "0f3c2b1a-5d6e-4f70-8a9b-0c1d2e3f4a5b"
MUSE_RUN = "0b7e6f5a-4c3d-4e2f-9a1b-2c3d4e5f6a7b"
MUSE_MODEL = "muse-spark-1.3-contributor"
MUSE_MODEL_2 = "muse-spark-1.3-fast"
MUSE_TRUST_REL = ".config/muse/trust.json"
MUSE_DIR = ".local/share/muse/sessions/2026/10/01/%s/" % MUSE_SESSION
MUSE_REL = MUSE_DIR + "session.jsonl"
MUSE_CHILD_REL = MUSE_DIR + "subagent/%s/session.jsonl" % MUSE_CHILD
MUSE_HISTORY_REL = ".local/share/muse/tui-history.jsonl"
MUSE_T0 = 1790845200000000  # 2026-10-01T09:00:00Z in microseconds


def _muse_env(sid, seq, t_us, ptype, payload, version=1, cause=None, ns="8000"):
    return {
        "schema_version": 1,
        "id": "00000000-0000-4000-%s-%012d" % (ns, seq),
        "stream": {"kind": "session", "id": sid},
        "sequence": seq,
        "recorded_at": t_us,
        "record_type": "event",
        "durability": "durable",
        "causation_id": cause,
        "payload_type": ptype,
        "payload_schema_version": version,
        "payload": payload,
    }


def _muse_run(sid, seq, t_us, run_id, event, src_seq, ns="8000"):
    return _muse_env(
        sid,
        seq,
        t_us,
        "runtime.session",
        {
            "event": event,
            "kind": "run",
            "run_id": run_id,
            "source_run_record_id": "10000000-0000-4000-8000-%012d" % src_seq,
            "source_run_record_sequence": src_seq,
        },
        ns=ns,
    )


def _muse_frame(sid, n, ns="8000"):
    children = [
        _muse_env(
            sid,
            1,
            MUSE_T0,
            "runtime.session.permission_format_declared",
            {"format": "profile_v1", "schema_version": 1},
            ns=ns,
        ),
        _muse_env(
            sid,
            2,
            MUSE_T0,
            "runtime.session.permission_profile_committed",
            {
                "actor": {"id": None, "kind": "runtime"},
                "cause": "new_session_default",
                "permission_epoch": 1,
                "resolved_snapshot": {
                    "approval": "on_request",
                    "reviewer": "auto_review",
                    "schema_version": 1,
                },
                "schema_version": 1,
                "source": {"display_name": "Auto-review", "id": ":auto-review", "kind": "built_in"},
            },
            ns=ns,
        ),
    ]
    return {
        "retained_frame": "session_permission_transaction",
        "frame_schema_version": 1,
        "outer_log_ordinal": 1,
        "transaction_id": "a1b2c3d4-0000-4000-8000-%012d" % n,
        "children": [
            {"child_index": i, "record_json": json.dumps(c, separators=(",", ":"))}
            for i, c in enumerate(children)
        ],
        "content_sha256": "sha256:" + "0" * 64,
    }


def _muse_model(sid, seq, t_us, run_id, ns="8000"):
    return _muse_env(
        sid,
        seq,
        t_us,
        "run.model.configured",
        {
            "kind": "run_model",
            "record": {
                "command_id": run_id,
                "display_label": MUSE_MODEL,
                "model_id": MUSE_MODEL,
                "profile_id": "tbh",
                "provider_id": "meta",
                "run_stream": {"id": run_id, "kind": "run"},
                "source": "startup",
            },
        },
        ns=ns,
    )


def muse_session_records():
    """The main fixture of research/muse-code.md section 8, less the cut
    line (tests append one with `write_bad_line`), plus a
    `session.opened.observed` record with a `security_mode`, an automated
    review verdict between the approval request and its decision, and a
    `/model` change after the run (issues 96 and 97). The `security_mode`,
    `outcome`, `risk_level` and `user_authorization` values are synthetic:
    the research records the keys, not their values."""
    s, r, t = MUSE_SESSION, MUSE_RUN, MUSE_T0
    bash = {
        "chunk_id": "exec-1-1",
        "command": "npm test",
        "description": "Run the test suite",
        "exit_code": 1,
        "terminal_status": "completed",
        "output": "1 failing",
        "original_output_bytes": 9,
        "original_output_tokens": 3,
        "truncated": False,
    }
    effect = {
        "call_id": "call_01",
        "effect_id": "30000000-0000-7000-8000-000000000001",
        "model_call_index": 0,
        "task_id": "30000000-0000-7000-8000-000000000001",
        "task_stream": {"id": "30000000-0000-7000-8000-000000000001", "kind": "task"},
    }
    return [
        _muse_frame(s, 1),
        _muse_env(
            s,
            3,
            t + 100000,
            "runtime.session.metadata",
            {
                "kind": "metadata",
                "record": {
                    "build": {"semver": "1.4.2", "sha": "0123abcd45"},
                    "model_id": MUSE_MODEL,
                    "provider_id": "meta",
                    "tool_surface_version": "2",
                    "web_search_mode": "client",
                    "workspace_root": "/srv/proj",
                },
            },
        ),
        _muse_env(
            s,
            4,
            t + 200000,
            "session.workspace_branch.observed",
            {
                "kind": "workspace_branch",
                "record": {
                    "command_id": s,
                    "commit": "0123456789ab",
                    "reference": {"kind": "branch", "name": "main"},
                    "vcs": "git",
                    "workspace_root": "/srv/proj",
                },
            },
        ),
        _muse_env(
            s,
            5,
            t + 250000,
            "session.opened.observed",
            {
                "kind": "session_opened",
                "record": {
                    "resume": False,
                    "security_mode": "example_mode",
                    "session_id": s,
                    "workspace_kind": "git",
                },
            },
        ),
        _muse_env(
            s,
            5,
            t + 300000,
            "session.name.changed",
            {
                "authority_id": "d0d0d0d0-0000-4000-8000-000000000001",
                "new_name": "quiet-lyra",
                "operation_id": "e0e0e0e0-0000-4000-8000-000000000001",
                "previous_name": None,
                "session_id": s,
                "source": "automatic",
            },
            cause="f0f0f0f0-0000-4000-8000-000000000001",
        ),
        _muse_model(s, 6, t + 900000, r),
        _muse_env(
            s,
            7,
            t + 1000000,
            "runtime.user_intent.accepted",
            {
                "bindings": [],
                "delivery_policy": "session_current",
                "intent_id": r,
                "model_messages": [{"content": [{"kind": "text", "text": "fix the failing test"}]}],
                "refill_blocks": [{"kind": "text", "text": "fix the failing test"}],
                "semantic_kind": {"kind": "chat"},
                "source_session_id": s,
                "surface": "main",
                "wake_policy": "start_once",
            },
        ),
        _muse_run(s, 8, t + 1000000, r, {"kind": "started", "prompt": "fix the failing test"}, 1),
        _muse_run(
            s,
            9,
            t + 3000000,
            r,
            {
                "kind": "reasoning_summary_delta",
                "message_id": "20000000-0000-4000-8000-000000000001",
                "summary_index": 0,
                "text": "Running the tests first.",
            },
            5,
        ),
        _muse_run(
            s,
            10,
            t + 3100000,
            r,
            {
                "kind": "reasoning_summary_committed",
                "message_id": "20000000-0000-4000-8000-000000000001",
                "provider_item_id": "rs_0001:rs_0002",
                "response_id": "resp_0001",
                "text": "Running the tests first.",
            },
            6,
        ),
        _muse_run(
            s,
            11,
            t + 3200000,
            r,
            {
                "encrypted_content": "Q-AAAA",
                "kind": "reasoning_committed",
                "message_id": "20000000-0000-4000-8000-000000000002",
                "provider_item_id": "rs_0001:rs_0002",
                "response_id": "resp_0001",
                "text": "",
            },
            7,
        ),
        _muse_run(
            s,
            12,
            t + 3300000,
            r,
            {
                "duration_ms": 2300,
                "finish_reason": "tool_calls",
                "kind": "model_completed",
                "model": MUSE_MODEL,
                "usage": {
                    "cache_read_tokens": 0,
                    "cache_write_tokens": 0,
                    "cached_tokens": 0,
                    "input_tokens": 900,
                    "output_tokens": 40,
                    "reasoning_tokens": 12,
                },
            },
            8,
        ),
        _muse_run(
            s,
            13,
            t + 3400000,
            r,
            {
                "kind": "assistant_tool_calls_committed",
                "message_id": "20000000-0000-4000-8000-000000000003",
                "response_id": "resp_0001",
                "tool_calls": [
                    {
                        "args": json.dumps(
                            {"command": "npm test", "description": "Run the test suite"}
                        ),
                        "call_id": "call_01",
                        "id": "fc_01",
                        "name": "bash",
                    }
                ],
            },
            9,
        ),
        _muse_env(
            s,
            14,
            t + 3500000,
            "tool_batch.effect.started",
            {
                "kind": "tool_batch_effect",
                "record": dict(
                    effect,
                    kind="started",
                    parallel_profile={"kind": "ineligible"},
                    tool_name="bash",
                ),
                "run_id": r,
            },
        ),
        {
            "retained_marker": "omitted_live_only",
            "schema_version": 1,
            "stream": {"kind": "session", "id": s},
            "position": {"id": "40000000-0000-4000-8000-000000000015", "sequence": 15},
            "omitted_record": {
                "record_type": "status",
                "durability": "ephemeral",
                "payload_type": "runtime.session",
                "payload_schema_version": 1,
                "payload_kind": "task",
                "omission_class": "task_tool_delta_v1",
            },
        },
        _muse_env(
            s,
            16,
            t + 4400000,
            "tool_batch.effect.terminal",
            {
                "kind": "tool_batch_effect",
                "record": dict(
                    effect,
                    kind="terminal",
                    outcome={
                        "kind": "completed",
                        "output_ref_count": 0,
                        "task_completion": {"kind": "terminal", "terminal": {"kind": "completed"}},
                    },
                ),
                "run_id": r,
            },
        ),
        _muse_run(
            s,
            17,
            t + 4500000,
            r,
            {
                "batch_id": "20000000-0000-4000-8000-000000000003",
                "kind": "tool_result_batch_committed",
                "results": [
                    {"text": json.dumps(bash), "tool_call_id": "call_01", "tool_call_index": 0}
                ],
            },
            14,
        ),
        _muse_env(
            s,
            18,
            t + 5000000,
            "runtime.session",
            {
                "event": {
                    "approval_subject": {
                        "kind": "tool_action",
                        "network": {
                            "host": "registry.example.org",
                            "port": 443,
                            "protocol": "https",
                        },
                        "origin": {"kind": "url", "url": "https://registry.example.org/pkg"},
                        "tool_name": "network",
                    },
                    "kind": "requested",
                    "pending_action_id": "50000000-0000-7000-8000-000000000001",
                    "raw_args": "https registry.example.org:443",
                    "task_id": "30000000-0000-7000-8000-000000000002",
                    "tool_call_id": "call_02",
                    "tool_name": "network",
                },
                "kind": "approval",
                "run_id": r,
            },
            version=3,
        ),
        _muse_env(
            s,
            19,
            t + 5900000,
            "runtime.session",
            {
                "event": {
                    "assessment": {
                        "outcome": "allow",
                        "rationale": "Fetching a package index is low risk.",
                        "risk_level": "low",
                        "user_authorization": "not_required",
                    },
                    "completed_at_ms": 1790845205900,
                    "duration_ms": 900,
                    "kind": "automated_review_completed",
                    "status": "completed",
                    "usage": {},
                },
                "kind": "approval",
                "run_id": r,
            },
            version=3,
        ),
        _muse_env(
            s,
            19,
            t + 6000000,
            "runtime.session",
            {
                "event": {
                    "amendment": None,
                    "decision": "approved",
                    "decision_source": {
                        "kind": "llm_judge",
                        "review_id": "60000000-0000-4000-8000-000000000001",
                    },
                    "kind": "decision_applied",
                    "pending_action_id": "50000000-0000-7000-8000-000000000001",
                    "policy_result": "allow",
                    "session_stream": {"id": s, "kind": "session"},
                },
                "kind": "approval",
                "run_id": r,
            },
            version=3,
        ),
        _muse_run(
            s,
            20,
            t + 7000000,
            r,
            {
                "child_session_id": MUSE_CHILD,
                "child_session_log_path": "subagent/%s/session.jsonl" % MUSE_CHILD,
                "generation_id": 1,
                "kind": "memory_reminder_child_session_linked",
                "parent_run_id": r,
                "parent_session_id": s,
                "reminder_agent_id": "verify-reminder",
                "task_id": "30000000-0000-7000-8000-000000000003",
                "task_stream": {"id": "30000000-0000-7000-8000-000000000003", "kind": "task"},
            },
            20,
        ),
        _muse_run(
            s,
            21,
            t + 9000000,
            r,
            {
                "kind": "assistant_message_committed",
                "message_id": "20000000-0000-4000-8000-000000000004",
                "provider_item_id": "msg_0001",
                "response_id": "resp_0002",
                "text": "The test fails because the fixture date is stale.",
            },
            30,
        ),
        _muse_run(
            s,
            22,
            t + 9100000,
            r,
            {
                "eot_gate_ms": 3,
                "kind": "terminal",
                "reason": None,
                "terminal": "completed",
                "time_to_first_token_ms": 800,
                "turn_duration_ms": 8100,
            },
            31,
        ),
        _muse_env(
            s,
            23,
            t + 15000000,
            "runtime.model_reconfigure.completed",
            {
                "kind": "model_reconfigure",
                "record": {
                    "effective": {"model_id": MUSE_MODEL_2},
                    "previous": {"model_id": MUSE_MODEL},
                },
            },
        ),
        _muse_env(
            s,
            23,
            t + 20000000,
            "session.end",
            {
                "kind": "session_end",
                "record": {
                    "exit_reason": "clean",
                    "schema_version": 1,
                    "session_id": s,
                    "uptime_ms": 20000,
                },
            },
        ),
    ]


def muse_subagent_records():
    c, t, ns = MUSE_CHILD, MUSE_T0, "9000"
    return [
        _muse_frame(c, 2, ns=ns),
        _muse_env(
            c,
            3,
            t + 7100000,
            "runtime.session.metadata",
            {"kind": "metadata", "record": {"model_id": MUSE_MODEL, "provider_id": "meta"}},
            ns=ns,
        ),
        _muse_model(c, 4, t + 7100000, c, ns=ns),
        _muse_run(
            c,
            5,
            t + 7200000,
            c,
            {"kind": "started", "prompt": "You are a reminder observer for the main agent."},
            1,
            ns=ns,
        ),
        _muse_run(
            c,
            6,
            t + 8000000,
            c,
            {
                "kind": "assistant_tool_calls_committed",
                "message_id": "20000000-0000-4000-8000-000000000010",
                "response_id": "resp_0010",
                "tool_calls": [
                    {
                        "args": json.dumps(
                            {"decision": "none", "next_step": None, "reason": "Tests were run."}
                        ),
                        "call_id": "call_10",
                        "id": "fc_10",
                        "name": "submit_reminder_decision",
                    }
                ],
            },
            13,
            ns=ns,
        ),
        _muse_run(
            c,
            7,
            t + 8100000,
            c,
            {
                "batch_id": "20000000-0000-4000-8000-000000000010",
                "kind": "tool_result_batch_committed",
                "results": [
                    {
                        "text": "reminder decision recorded",
                        "tool_call_id": "call_10",
                        "tool_call_index": 0,
                    }
                ],
            },
            16,
            ns=ns,
        ),
        _muse_run(
            c,
            8,
            t + 8199999,
            c,
            {
                "kind": "terminal",
                "reason": None,
                "terminal": "completed",
                "time_to_first_token_ms": 500,
                "turn_duration_ms": 1000,
            },
            18,
            ns=ns,
        ),
    ]


def build_muse_code(home: Path) -> None:
    _jsonl(home / MUSE_REL, muse_session_records())
    _jsonl(home / MUSE_CHILD_REL, muse_subagent_records())
    _jsonl(
        home / MUSE_HISTORY_REL,
        ["fix the failing test", {"project": "/srv/proj", "session": MUSE_SESSION}],
    )
    # Noise the parser must not want: the automated approval reviewer's log
    # (same envelope, synthetic clock) and the settings file.
    review = _muse_run(
        "7a7a7a7a-0000-4000-8000-000000000001",
        1,
        1780531500000000,
        "7a7a7a7a-0000-4000-8000-000000000002",
        {"kind": "started", "prompt": '{"approval_review_context": {}}'},
        1,
    )
    review["stream"]["kind"] = "approval.review.runtime"
    _jsonl(home / MUSE_DIR / "approval-review/7a7a7a7a-0000-4000-8000-000000000001.jsonl", [review])
    (home / ".config/muse").mkdir(parents=True, exist_ok=True)
    (home / ".config/muse/settings.json").write_text("{}", encoding="utf-8")
    # Trusted projects (collectors/research/muse-code.md section 2).
    _json_file(
        home / MUSE_TRUST_REL,
        {
            "schema_version": 1,
            "projects": {
                "/srv/proj": {"decision": "trusted"},
                "/srv/other": {"decision": "trusted"},
            },
        },
    )


OLLAMA_CHAT = "0190a000-0000-7000-8000-00000000c001"
OLLAMA_DB_REL = "Library/Application Support/Ollama/db.sqlite"
OLLAMA_WIN_DB_REL = "AppData/Local/Ollama/db.sqlite"
OLLAMA_USER_NAME = "Alice Example"
OLLAMA_USER_EMAIL = "alice@example.invalid"
OLLAMA_ATTACHMENT = b"hello"
OLLAMA_MANIFEST_REL = ".ollama/models/manifests/registry.ollama.ai/library/gemma4/e4b"

# app/store/database.go at ollama v0.35.1 (b0c1ca4), schema version 19
# (research/ollama.md section 8). OLLAMA_SETTINGS_16 is the settings table
# before migrations 16 to 19 added onboarding_version, claude_desktop_used
# and codex_desktop_used; the transcript tables are the same in both.
OLLAMA_SETTINGS_19 = """
CREATE TABLE settings (id INTEGER PRIMARY KEY CHECK (id = 1), device_id TEXT NOT NULL DEFAULT '',
  working_dir TEXT NOT NULL DEFAULT '', selected_model TEXT NOT NULL DEFAULT '',
  onboarding_version INTEGER NOT NULL DEFAULT 0, claude_desktop_used BOOLEAN NOT NULL DEFAULT 0,
  codex_desktop_used BOOLEAN NOT NULL DEFAULT 0, schema_version INTEGER NOT NULL DEFAULT 19);
"""
OLLAMA_SETTINGS_16 = """
CREATE TABLE settings (id INTEGER PRIMARY KEY CHECK (id = 1), device_id TEXT NOT NULL DEFAULT '',
  working_dir TEXT NOT NULL DEFAULT '', selected_model TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 16);
"""
OLLAMA_SCHEMA = """
CREATE TABLE chats (id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, browser_state TEXT);
CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT NOT NULL, role TEXT NOT NULL,
  content TEXT NOT NULL DEFAULT '', thinking TEXT NOT NULL DEFAULT '', stream BOOLEAN NOT NULL DEFAULT 0,
  model_name TEXT, model_cloud BOOLEAN, model_ollama_host BOOLEAN,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  thinking_time_start TIMESTAMP, thinking_time_end TIMESTAMP, tool_result TEXT);
CREATE TABLE tool_calls (id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INTEGER NOT NULL, type TEXT NOT NULL,
  function_name TEXT NOT NULL, function_arguments TEXT NOT NULL, function_result TEXT);
CREATE TABLE attachments (id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INTEGER NOT NULL,
  filename TEXT NOT NULL, data BLOB NOT NULL);
CREATE TABLE users (name TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
  plan TEXT NOT NULL DEFAULT '', cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""


def ollama_records(schema_version: int = 19):
    """The INSERT statements of research/ollama.md section 8."""
    c = OLLAMA_CHAT
    return [
        "INSERT INTO settings (id, device_id, schema_version) "
        "VALUES (1, '0190a000-0000-7000-8000-00000000d001', %d)" % schema_version,
        "INSERT INTO users VALUES ('%s', '%s', 'free', '2026-03-01 08:59:00-08:00')"
        % (OLLAMA_USER_NAME, OLLAMA_USER_EMAIL),
        "INSERT INTO chats VALUES ('%s', 'Release notes', '2026-03-01 09:00:00.5-08:00', NULL)" % c,
        "INSERT INTO messages (id, chat_id, role, content, thinking, model_name, created_at, "
        "updated_at, tool_result) VALUES "
        "(1, '%s', 'user', 'summarise https://example.invalid/notes', '', NULL, "
        "'2026-03-01 09:00:00.5-08:00', '2026-03-01 09:00:00.5-08:00', NULL),"
        "(2, '%s', 'assistant', '', 'need to fetch the page', 'gemma4:e4b', "
        "'2026-03-01 09:00:01.25-08:00', '2026-03-01 09:00:02-08:00', NULL),"
        "(3, '%s', 'tool', 'Release 2.0 adds X.', '', NULL, "
        "'2026-03-01 09:00:03-08:00', '2026-03-01 09:00:03-08:00', "
        """'{"title":"Notes","content":"Release 2.0 adds X."}'),"""
        "(4, '%s', 'assistant', 'Release 2.0 adds X.', '', 'qwen3:8b', "
        "'2026-03-01 09:00:04.125-08:00', '2026-03-01 09:00:05-08:00', NULL)" % (c, c, c, c),
        "INSERT INTO tool_calls VALUES (1, 2, 'function', 'web_fetch', "
        """'{"url":"https://example.invalid/notes"}', NULL)""",
        "INSERT INTO attachments VALUES (1, 1, 'notes.txt', X'%s')" % OLLAMA_ATTACHMENT.hex(),
    ]


def write_ollama_db(path: Path, schema_version: int = 19) -> None:
    settings = OLLAMA_SETTINGS_19 if schema_version >= 19 else OLLAMA_SETTINGS_16
    _wal_db(path, settings + OLLAMA_SCHEMA, ollama_records(schema_version))


def build_ollama(home: Path) -> None:
    write_ollama_db(home / OLLAMA_DB_REL)
    write_ollama_db(home / OLLAMA_WIN_DB_REL, schema_version=16)
    ollama = home / ".ollama"
    ollama.mkdir(parents=True, exist_ok=True)
    (ollama / "history").write_text("why is the sky blue\n/set nohistory\n/bye\n", encoding="utf-8")
    # Noise the parser must not want: launch configuration, its backup, the
    # onboarding marker, the key pair, a server log and a model manifest,
    # which the collector collects once .ollama/models/blobs alone is excluded.
    (ollama / "config.json").write_text(
        '{"integrations":{"claude":{"models":["gemma4:e4b"]}},'
        '"last_model":"gemma4:e4b","last_selection":"claude"}',
        encoding="utf-8",
    )
    (ollama / "backup").mkdir(exist_ok=True)
    (ollama / "backup/config.json.1772355600").write_text(
        '{"integrations":{},"last_selection":"claude"}', encoding="utf-8"
    )
    (ollama / "onboarding-v1.completed").write_text("", encoding="utf-8")
    (ollama / "id_ed25519").write_text("not a real key\n", encoding="utf-8")
    (ollama / "logs").mkdir(exist_ok=True)
    (ollama / "logs/server.log").write_text(
        "[GIN] 2026/03/01 - 09:00:00 | 200 |\n", encoding="utf-8"
    )
    manifest = home / OLLAMA_MANIFEST_REL
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        '{"schemaVersion":2,"mediaType":"application/vnd.docker.distribution.manifest.v2+json"}',
        encoding="utf-8",
    )


# -- Claude Desktop (app bundle 2.31226.1) ------------------------------------------
CD_BASE = "Library/Application Support/Claude"
CD_ACCT = "aaaaaaaa-0000-4000-8000-000000000001"
CD_ORG = "bbbbbbbb-0000-4000-8000-000000000002"
CD_COWORK_ORG = "%s/local-agent-mode-sessions/%s/%s" % (CD_BASE, CD_ACCT, CD_ORG)
CD_CODE_ORG = "%s/claude-code-sessions/%s/%s" % (CD_BASE, CD_ACCT, CD_ORG)
CD_SESSION = "local_c0c0c0c0-1111-4222-8333-444444444444"
CD_CLI_SESSION = "d1d1d1d1-5555-4666-8777-888888888888"
CD_GUEST_CWD = "/sessions/quiet-river-1234"
CD_RECORD_REL = "%s/%s.json" % (CD_COWORK_ORG, CD_SESSION)
CD_TRANSCRIPT_REL = "%s/%s/.claude/projects/session/%s.jsonl" % (
    CD_COWORK_ORG,
    CD_SESSION,
    CD_CLI_SESSION,
)
CD_AUDIT_REL = "%s/%s/audit.jsonl" % (CD_COWORK_ORG, CD_SESSION)
# A session dir in the short (eight hex) form holding only an audit log.
CD_FALLBACK_DIR = "f3f3f3f3"
CD_FALLBACK_CLI = "d2d2d2d2-5555-4666-8777-888888888888"
CD_FALLBACK_REL = "%s/%s/audit.jsonl" % (CD_COWORK_ORG, CD_FALLBACK_DIR)
CD_CODE_SESSION = "local_e2e2e2e2-9999-4aaa-8bbb-cccccccccccc"
# Its own CLI id: a Code-tab record that joined the claude-code fixture
# session would put two agents under one session id in sessions.jsonl.
CD_CODE_CLI = "11111111-2222-4333-8444-555555555555"
CD_CODE_RECORD_REL = "%s/%s.json" % (CD_CODE_ORG, CD_CODE_SESSION)
# A Code-tab record with the persisted Remote Control state set (bundle
# serializer keys, research/claude-desktop.md section 3; fixture only).
CD_CODE_RC_SESSION = "local_e3e3e3e3-9999-4aaa-8bbb-cccccccccccc"
CD_CODE_RC_CLI = "e3e3e3e3-5555-4666-8777-888888888888"
CD_CODE_RC_RECORD_REL = "%s/%s.json" % (CD_CODE_ORG, CD_CODE_RC_SESSION)
CD_SCHED_REL = "%s/scheduled-tasks.json" % CD_COWORK_ORG
CD_WORKTREES_REL = "%s/git-worktrees.json" % CD_BASE
CD_SPACES_REL = "%s/remote-session-spaces.json" % CD_COWORK_ORG
CD_REMOTE_SESSION = "0123456789abcdef0123456789abcdef"
CD_SPACES_MTIME = 1790848800  # 2026-10-01T10:00:00Z


def claude_desktop_record():
    return {
        "sessionId": CD_SESSION,
        "processName": "quiet-river-1234",
        "cliSessionId": CD_CLI_SESSION,
        "cwd": CD_GUEST_CWD,
        "userSelectedFolders": ["/srv/proj"],
        "createdAt": 1790762400000,
        "lastActivityAt": 1790762460000,
        "model": "claude-fable-5-1",
        "permissionMode": "default",
        "isArchived": False,
        "title": "Summarise the test failures",
        "vmProcessName": "quiet-river-1234",
        "initialMessage": "why does the test fail?",
        "sessionType": "agent",
        "emailAddress": "user@example.invalid",
        # Cowork grants (issue 97): "arrays and objects" in the bundle, the
        # type of each key not determined; these values are fixture only.
        "approvedToolNames": ["Bash", "WebFetch"],
        "webFetchAllowedUrls": ["https://example.invalid/docs"],
        "egressAllowedDomains": ["example.invalid"],
        "userApprovedFileAccessPaths": ["/srv/proj/data"],
        "enabledMcpTools": {"github:create_issue": True},
        "fileDeleteApprovedMounts": [],
    }


def claude_desktop_transcript_records():
    """The claude-code fixture as the Cowork VM's CLI writes it: guest cwd,
    `entrypoint` local-agent and the record's `cliSessionId`."""
    out = []
    for r in claude_session_records(cwd=CD_GUEST_CWD):
        r = dict(r)
        if "sessionId" in r:
            r["sessionId"] = CD_CLI_SESSION
        if "entrypoint" in r:
            r["entrypoint"] = "local-agent"
        out.append(r)
    return out


def _cd_hmac(n: int) -> str:
    return "%064x" % n


def claude_desktop_audit_records():
    """Research section 8, verbatim (HMAC values and tool ids are
    placeholders). Line 1's prompt has no transcript twin; line 8's and the
    `init` model repeat the transcript's rows (issue 122). The `npm test`
    call is not the transcript's, so its id is not the transcript's
    `toolu_01`: tool rows pair on their id."""
    sid = CD_CLI_SESSION
    return [
        {
            "type": "user",
            "uuid": "00000000-0000-4000-8000-0000000000a1",
            "session_id": sid,
            "parent_tool_use_id": None,
            "client_platform": "desktop_app",
            "timestamp": "2026-10-01T10:00:00.000Z",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "why does the test fail?"}],
            },
            "_audit_timestamp": "2026-10-01T10:00:00.004Z",
            "_audit_hmac": _cd_hmac(1),
        },
        {
            "type": "system",
            "subtype": "init",
            "session_id": sid,
            "cwd": CD_GUEST_CWD,
            "model": "claude-fable-5-1",
            "_audit_timestamp": "2026-10-01T10:00:01.000Z",
            "_audit_hmac": _cd_hmac(2),
        },
        {
            "type": "assistant",
            "uuid": "00000000-0000-4000-8000-0000000000a2",
            "session_id": sid,
            "parent_tool_use_id": None,
            "message": {
                "model": "claude-fable-5-1",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_a1",
                        "name": "Bash",
                        "input": {"command": "npm test"},
                    }
                ],
            },
            "_audit_timestamp": "2026-10-01T10:00:03.000Z",
            "_audit_hmac": _cd_hmac(3),
        },
        {
            "type": "system",
            "subtype": "permission_request",
            "uuid": "00000000-0000-4000-8000-0000000000a3",
            "session_id": sid,
            "tool_name": "Bash",
            "tool_input": {"command": "npm test"},
            "_audit_timestamp": "2026-10-01T10:00:03.100Z",
            "_audit_hmac": _cd_hmac(4),
        },
        {
            "type": "system",
            "subtype": "permission_response",
            "uuid": "00000000-0000-4000-8000-0000000000a3",
            "session_id": sid,
            "tool_name": "Bash",
            "decision": "once",
            "granted": True,
            "_audit_timestamp": "2026-10-01T10:00:05.000Z",
            "_audit_hmac": _cd_hmac(5),
        },
        {
            "type": "user",
            "uuid": "00000000-0000-4000-8000-0000000000a4",
            "session_id": sid,
            "parent_tool_use_id": None,
            "message": {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_a1", "content": "1 failing"}
                ],
            },
            "_audit_timestamp": "2026-10-01T10:00:09.000Z",
            "_audit_hmac": _cd_hmac(6),
        },
        {
            "type": "result",
            "subtype": "success",
            "duration_ms": 9000,
            "duration_api_ms": 4000,
            "is_error": False,
            "num_turns": 2,
            "session_id": sid,
            "uuid": "00000000-0000-4000-8000-0000000000a5",
            "_audit_timestamp": "2026-10-01T10:00:12.000Z",
            "_audit_hmac": _cd_hmac(7),
        },
        # Issue 122: a prompt the transcript also records (its last user
        # line, "thanks" at 10:00:20), so the secondary row pairs with it.
        {
            "type": "user",
            "uuid": "00000000-0000-4000-8000-0000000000a6",
            "session_id": sid,
            "parent_tool_use_id": None,
            "client_platform": "desktop_app",
            "timestamp": "2026-10-01T10:00:20.000Z",
            "message": {"role": "user", "content": [{"type": "text", "text": "thanks"}]},
            "_audit_timestamp": "2026-10-01T10:00:20.003Z",
            "_audit_hmac": _cd_hmac(8),
        },
    ]


def claude_desktop_fallback_records():
    """An audit log whose session dir has no transcript: every line counts.
    Line numbers are what ClaudeDesktopTests.test_audit_fallback asserts."""
    sid = CD_FALLBACK_CLI

    def line(n, ts, **rec):
        rec.setdefault("session_id", sid)
        rec["_audit_timestamp"] = "2026-10-02T09:00:%s.000Z" % ts
        rec["_audit_hmac"] = _cd_hmac(100 + n)
        return rec

    return [
        line(
            1,
            "00",
            type="user",
            uuid="00000000-0000-4000-8000-0000000000b1",
            parent_tool_use_id=None,
            client_platform="desktop_app",
            timestamp="2026-10-02T08:59:59.500Z",
            message={"role": "user", "content": [{"type": "text", "text": "list the files"}]},
        ),  # 1
        line(2, "01", type="system", subtype="init", cwd=CD_GUEST_CWD, model="claude-fable-5-1"),
        line(
            3,
            "02",
            type="user",
            uuid="00000000-0000-4000-8000-0000000000b2",
            parent_tool_use_id=None,
            client_platform="desktop_app",
            isSynthetic=True,
            message={"role": "user", "content": [{"type": "text", "text": "folder mounted"}]},
        ),  # 3
        line(
            4,
            "03",
            type="assistant",
            uuid="00000000-0000-4000-8000-0000000000b3",
            parent_tool_use_id=None,
            message={
                "model": "claude-fable-5-1",
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "use ls", "signature": "x"},
                    {"type": "text", "text": "Listing."},
                    {
                        "type": "tool_use",
                        "id": "toolu_b1",
                        "name": "Bash",
                        "input": {"command": "ls"},
                    },
                ],
            },
        ),  # 4
        line(
            5,
            "04",
            type="system",
            subtype="permission_auto_approved",
            tool_name="Bash",
            source="always_allow",
        ),  # 5
        line(
            6,
            "05",
            type="user",
            uuid="00000000-0000-4000-8000-0000000000b4",
            parent_tool_use_id=None,
            message={
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_b1", "content": "README.md"}
                ],
            },
        ),  # 6
        line(
            7,
            "06",
            type="assistant",
            uuid="00000000-0000-4000-8000-0000000000b5",
            parent_tool_use_id=None,
            message={
                "model": "claude-fable-5-1",
                "role": "assistant",
                "content": [{"type": "text", "text": "One file: README.md"}],
            },
        ),  # 7
        line(8, "07", type="prompt_suggestion", suggestion="open it"),  # 8: skipped
        line(
            9,
            "08",
            type="result",
            subtype="success",
            duration_ms=8000,
            duration_api_ms=3000,
            is_error=False,
            num_turns=1,
            uuid="00000000-0000-4000-8000-0000000000b6",
        ),  # 9
        # The subtype is in the bundle, its fields are not recorded.
        line(
            10,
            "09",
            type="system",
            subtype="model_refusal_fallback",
            note="fields not recorded; fixture only",
        ),  # 10
        line(
            11,
            "10",
            type="assistant",
            uuid="00000000-0000-4000-8000-0000000000b7",
            parent_tool_use_id=None,
            message={
                "model": "claude-opus-5-5",
                "role": "assistant",
                "content": [{"type": "text", "text": "Answered by the fallback."}],
            },
        ),  # 11
    ]


def claude_desktop_code_record():
    return {
        "sessionId": CD_CODE_SESSION,
        "cliSessionId": CD_CODE_CLI,
        "cwd": "/srv/proj",
        "originCwd": "/srv/proj",
        "branch": "main",
        "createdAt": 1790762400000,
        "lastActivityAt": 1790762520000,
        "model": "claude-fable-5-1",
        "isArchived": False,
        "title": "Fix the failing test",
        "permissionMode": "default",
        # Per-session grants (issue 93): the entries' inner shape is not
        # determined (real installs showed both lists empty); fixture only.
        "effort": "high",
        "alwaysAllowedReasons": ["Bash(npm test)"],
        "sessionPermissionUpdates": [
            {
                "type": "addRules",
                "rules": [{"toolName": "Bash", "ruleContent": "npm test"}],
                "behavior": "allow",
                "destination": "session",
            }
        ],
        "chromePermissionMode": "ask",
        "chromeAllowedDomains": ["example.invalid"],
        "cuAllowedApps": ["Terminal"],
        "cuGrantFlags": {"clipboardRead": True},
        "cuFlagsGrantedAt": 1790762450000,
    }


def claude_desktop_code_rc_record():
    return {
        "sessionId": CD_CODE_RC_SESSION,
        "cliSessionId": CD_CODE_RC_CLI,
        "cwd": "/srv/proj",
        "originCwd": "/srv/proj",
        "branch": "main",
        "createdAt": 1790766000000,
        "lastActivityAt": 1790766600000,
        "model": "claude-fable-5-1",
        "isArchived": False,
        "title": "Driven from the phone",
        "permissionMode": "default",
        "remoteControlUserEnabled": True,
        "remoteControlUserRequested": True,
        "remoteControlUserToggled": True,
        "remoteControlAutoEligible": False,
        "bridgeSessionIds": ["cse_aaaa0001", "cse_aaaa0002"],
        "remoteControlSpawn": {
            "ccrSessionId": "cse_aaaa0001",
            "detachedAt": 1790766300000,
            "rcChild": True,
            "projectThreadChild": False,
        },
        "steeredByRemoteClient": True,
        "remoteControlLiveAtUpdateQuit": {
            "at": 1790766500000,
            "accountId": "aaaaaaaa-0000-4000-8000-000000000001",
        },
    }


def claude_desktop_scheduled_tasks():
    return {
        "scheduledTasks": [
            {
                "id": "daily-report",
                "cronExpression": "0 9 * * 1-5",
                "enabled": True,
                "filePath": "/home/user/Claude/Scheduled/daily-report/SKILL.md",
                "createdAt": 1790762400000,
                "cwd": "/srv/proj",
                "permissionMode": "default",
                "model": "claude-fable-5-1",
            }
        ],
        "recordedSkips": {},
        "sundayAliasBoundaryStamped": True,
        "dayFieldsOrBoundaryStamped": True,
    }


def claude_desktop_worktrees():
    return {
        "schemaVersion": 2,
        "worktrees": {
            "brave-otter": {
                "name": "brave-otter",
                "path": "/srv/proj/.claude/worktrees/brave-otter",
                "leasedBy": CD_CODE_SESSION,
                "baseRepo": "/srv/proj",
                "branch": "claude/brave-otter",
                "sourceBranch": "main",
                "createdAt": 1790762401000,
            }
        },
        "untrackedDirGc": {"cwds": {}, "roots": {}, "sightings": {}},
    }


def claude_desktop_remote_spaces():
    """Research section 3: `entries[]` with `sessionId` (32 hex) and
    `folders[]`; observed shape, fixture values."""
    return {"entries": [{"sessionId": CD_REMOTE_SESSION, "folders": ["/srv/proj", "/srv/docs"]}]}


def build_claude_desktop(home: Path) -> None:
    cowork = home / CD_COWORK_ORG
    cowork.mkdir(parents=True, exist_ok=True)
    (home / CD_RECORD_REL).write_text(
        json.dumps(claude_desktop_record(), indent=2), encoding="utf-8"
    )
    _jsonl(home / CD_TRANSCRIPT_REL, claude_desktop_transcript_records())
    _jsonl(home / CD_AUDIT_REL, claude_desktop_audit_records())
    _jsonl(home / CD_FALLBACK_REL, claude_desktop_fallback_records())
    code = home / CD_CODE_RECORD_REL
    code.parent.mkdir(parents=True, exist_ok=True)
    code.write_text(json.dumps(claude_desktop_code_record()), encoding="utf-8")
    (home / CD_CODE_RC_RECORD_REL).write_text(
        json.dumps(claude_desktop_code_rc_record()), encoding="utf-8"
    )
    (home / CD_SCHED_REL).write_text(json.dumps(claude_desktop_scheduled_tasks()), encoding="utf-8")
    (home / CD_WORKTREES_REL).write_text(json.dumps(claude_desktop_worktrees()), encoding="utf-8")
    (home / CD_SPACES_REL).write_text(json.dumps(claude_desktop_remote_spaces()), encoding="utf-8")
    os.utime(home / CD_SPACES_REL, (CD_SPACES_MTIME, CD_SPACES_MTIME))
    # Noise the parser must not want.
    (cowork / "spaces.json").write_text('{"spaces":[]}', encoding="utf-8")
    (cowork / "cowork_settings.json").write_text("{}", encoding="utf-8")
    (cowork / "rpm").mkdir(exist_ok=True)
    (cowork / "rpm/manifest.json").write_text(
        '{"lastUpdated":1790762400000,"plugins":[]}', encoding="utf-8"
    )
    (cowork / CD_SESSION / ".audit-key").write_bytes(b"not a real key")
    (home / CD_BASE / "claude_desktop_config.json").write_text(
        '{"mcpServers":{}}', encoding="utf-8"
    )


# GitHub Copilot CLI (issue 50): the sample records of
# research/copilot-cli.md section 8, verbatim, plus the `/model` switch to
# Auto of the Linux round (2026-10-16): a `model_picker` change and its two
# `session.info` lines (issue 133). The last line is cut mid-write, as a log
# whose session was still running.
COPILOT_SESSION = "5e55a0a1-0000-4000-8000-000000000001"
COPILOT_DIR = ".copilot/session-state/%s/" % COPILOT_SESSION
COPILOT_EVENTS_REL = COPILOT_DIR + "events.jsonl"
COPILOT_WORKSPACE_REL = COPILOT_DIR + "workspace.yaml"
COPILOT_SNAPSHOTS_REL = COPILOT_DIR + "rewind-file-snapshots/index.json"
COPILOT_STORE_REL = ".copilot/session-store.db"
COPILOT_HISTORY_REL = ".copilot/command-history-state.json"
COPILOT_PERMISSIONS_REL = ".copilot/permissions-config.json"
COPILOT_SETTINGS_REL = ".copilot/settings.json"
COPILOT_SIDEBAR_REL = (
    ".copilot/sidebar-sessions-state/"
    "6b9af143446a411aefa3edb76e4693799bd7513e7ed8d919962d6713d3d3b972.json"
)
COPILOT_LOG_REL = ".copilot/logs/process-1790845199000-4242.log"
COPILOT_SETTINGS_MTIME = 1790856000  # 2026-10-01T12:00:00Z

COPILOT_EVENT_LINES = [
    '{"id":"e0000000-0000-4000-8000-000000000001","parentId":null,"timestamp":"2026-10-01T09:00:00.000Z","type":"session.start","data":{"sessionId":"5e55a0a1-0000-4000-8000-000000000001","version":1,"producer":"copilot-agent","copilotVersion":"1.0.98","startTime":"2026-10-01T08:59:59.000Z","context":{"cwd":"/srv/proj","gitRoot":"/srv/proj","branch":"main"},"alreadyInUse":false,"remoteSteerable":false,"contextTier":null}}',
    '{"id":"e0000000-0000-4000-8000-000000000002","parentId":"e0000000-0000-4000-8000-000000000001","timestamp":"2026-10-01T09:00:00.100Z","type":"session.model_change","data":{"newModel":"gpt-6.1-sol","cause":"initial_resolution","source":"automatic","reasoningEffort":"medium","contextTier":null}}',
    '{"id":"e0000000-0000-4000-8000-000000000003","parentId":"e0000000-0000-4000-8000-000000000002","timestamp":"2026-10-01T09:00:01.000Z","type":"system.message","data":{"content":"You are the GitHub Copilot CLI.\\nFollow the user\'s instructions.","role":"system","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","metadata":{"variables":{"gitCommitTrailer":{"clientName":"copilot-cli","coauthorEnabled":true,"sessionId":"5e55a0a1-0000-4000-8000-000000000001"}}}}}',
    '{"id":"e0000000-0000-4000-8000-000000000004","parentId":"e0000000-0000-4000-8000-000000000003","timestamp":"2026-10-01T09:00:01.200Z","type":"user.message","data":{"content":"fix the failing test","transformedContent":"<current_datetime>2026-10-01T09:00:01Z</current_datetime>\\nfix the failing test","messageId":"2b2b2b2b-0000-4000-8000-000000000001","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","parentAgentTaskId":"3c3c3c3c-0000-4000-8000-000000000001","turnId":"0","delivery":"idle","responsesReasoning":{"effort":"medium","initialEffort":"medium","model":"gpt-6.1-sol"},"supportedNativeDocumentMimeTypes":[]}}',
    '{"id":"e0000000-0000-4000-8000-000000000005","parentId":"e0000000-0000-4000-8000-000000000004","timestamp":"2026-10-01T09:00:01.300Z","type":"assistant.turn_start","data":{"interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"0"}}',
    '{"id":"e0000000-0000-4000-8000-000000000006","parentId":null,"timestamp":"2026-10-01T09:00:01.400Z","type":"model.turn_started","data":{"kind":"turn_started","model":"gpt-4o-mini","modelInfo":{"id":"gpt-4o-mini","name":"GPT-4o mini","object":"model","version":"gpt-4o-mini-2024-07-18","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}},"timestampMs":1790845201400,"turn":0}}',
    '{"id":"e0000000-0000-4000-8000-000000000007","parentId":"e0000000-0000-4000-8000-000000000006","timestamp":"2026-10-01T09:00:01.410Z","type":"model.model_call_started","data":{"kind":"model_call_started","model":"gpt-4o-mini","modelInfo":{"id":"gpt-4o-mini","name":"GPT-4o mini","object":"model","version":"gpt-4o-mini-2024-07-18","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}},"timestampMs":1790845201410,"turn":0}}',
    '{"id":"e0000000-0000-4000-8000-000000000008","parentId":"e0000000-0000-4000-8000-000000000007","timestamp":"2026-10-01T09:00:01.420Z","type":"model.messages_snapshot","data":{"kind":"messages_snapshot","messages":[{"role":"system","content":"Generate a session title for this message."},{"role":"user","content":"fix the failing test"}]}}',
    '{"id":"e0000000-0000-4000-8000-000000000009","parentId":"e0000000-0000-4000-8000-000000000008","timestamp":"2026-10-01T09:00:01.430Z","type":"model.captured_assignment_context","data":{"kind":"captured_assignment_context","assignmentContext":"exp-a:1;exp-b:0;"}}',
    '{"id":"e0000000-0000-4000-8000-000000000010","parentId":"e0000000-0000-4000-8000-000000000009","timestamp":"2026-10-01T09:00:02.000Z","type":"model.message","data":{"callId":"4d4d4d4d-0000-4000-8000-000000000001","kind":"message","message":{"apiCallId":"chatcmpl-0001","content":"Fix failing test","outputTokens":4,"providerId":"copilot","refusal":null,"role":"assistant"},"modelCall":{"api_endpoint":"/chat/completions","api_id":"chatcmpl-0001","client_request_id":"req-0001","initiator":"agent","model":"gpt-4o-mini","request_id":"5f5f5f5f-0000-4000-8000-000000000001","rte":false,"service_request_id":"6a6a6a6a-0000-4000-8000-000000000001","transport":"http"},"turn":0}}',
    '{"id":"e0000000-0000-4000-8000-000000000011","parentId":"e0000000-0000-4000-8000-000000000010","timestamp":"2026-10-01T09:00:02.010Z","type":"model.response","data":{"callId":"4d4d4d4d-0000-4000-8000-000000000001","kind":"response","modelCall":{"api_id":"chatcmpl-0001","model":"gpt-4o-mini"},"response":{"content":"Fix failing test","providerId":"copilot","refusal":null,"role":"assistant"},"turn":0}}',
    '{"id":"e0000000-0000-4000-8000-000000000012","parentId":"e0000000-0000-4000-8000-000000000011","timestamp":"2026-10-01T09:00:02.020Z","type":"model.model_call_success","data":{"callId":"4d4d4d4d-0000-4000-8000-000000000001","kind":"model_call_success","modelCall":{"api_endpoint":"/chat/completions","api_id":"chatcmpl-0001","client_request_id":"req-0001","initiator":"agent","model":"gpt-4o-mini","request_id":"5f5f5f5f-0000-4000-8000-000000000001","rte":false,"service_request_id":"6a6a6a6a-0000-4000-8000-000000000001","transport":"http"},"modelCallDurationMs":590,"modelDisplayName":"GPT-4o mini","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}}}',
    '{"id":"e0000000-0000-4000-8000-000000000013","parentId":"e0000000-0000-4000-8000-000000000012","timestamp":"2026-10-01T09:00:02.030Z","type":"model.turn_ended","data":{"kind":"turn_ended","model":"gpt-4o-mini","modelInfo":{"id":"gpt-4o-mini","name":"GPT-4o mini","object":"model","version":"gpt-4o-mini-2024-07-18","provider":{"id":"copilot","kind":"copilot","label":"GitHub Copilot"}},"timestampMs":1790845202030,"turn":0}}',
    '{"id":"e0000000-0000-4000-8000-000000000014","parentId":"e0000000-0000-4000-8000-000000000013","timestamp":"2026-10-01T09:00:03.000Z","type":"assistant.message","data":{"content":"","messageId":"7b7b7b7b-0000-4000-8000-000000000001","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","originatingMessageId":"2b2b2b2b-0000-4000-8000-000000000001","model":"gpt-6.1-sol","providerId":"copilot","turnId":"0","reasoningText":"Run the tests first.","reasoningOpaque":"rs_AAAA","encryptedContent":"gAAAAA","reasoningBlocks":{"provider":"openai-responses","blocks":[{"type":"reasoning","id":"rs_AAAA","summary":[{"type":"summary_text","text":"Run the tests first."}],"encrypted_content":"gAAAAA"}]},"apiCallId":"resp_0001","rte":false,"serverTools":{"provider":"openai-responses"},"toolRequests":[{"type":"function","name":"bash","toolCallId":"call_01","toolTitle":"Run shell command","arguments":{"command":"npm test","description":"Run the test suite"},"intentionSummary":"Run the test suite"}]}}',
    '{"id":"e0000000-0000-4000-8000-000000000015","parentId":"e0000000-0000-4000-8000-000000000014","timestamp":"2026-10-01T09:00:03.100Z","type":"permission.requested","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000001","ownerSessionId":"5e55a0a1-0000-4000-8000-000000000001","agentMode":"interactive","permissionMode":"manual","permissionRequest":{"kind":"shell","toolCallId":"call_01","intention":"Run the test suite","fullCommandText":"npm test","shellType":"bash","commands":[{"identifier":"npm test","readOnly":false,"allowMatchIdentifier":"npm test"}],"commandSegments":[{"identifier":"npm test","fullCommandText":"npm test"}],"possiblePaths":[],"possibleUrls":[],"hasWriteFileRedirection":false,"canOfferSessionApproval":true},"promptRequest":{"kind":"commands","toolCallId":"call_01","intention":"Run the test suite","fullCommandText":"npm test","commandIdentifiers":["npm test"]}}}',
    '{"id":"e0000000-0000-4000-8000-000000000016","parentId":"e0000000-0000-4000-8000-000000000015","timestamp":"2026-10-01T09:00:06.000Z","type":"permission.completed","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000001","toolCallId":"call_01","decisionSource":"human_response","result":{"kind":"approved-for-location","locationKey":"/srv/proj","approval":{"kind":"commands","commandIdentifiers":["npm test"]}}}}',
    '{"id":"e0000000-0000-4000-8000-000000000017","parentId":"e0000000-0000-4000-8000-000000000016","timestamp":"2026-10-01T09:00:06.100Z","type":"tool.execution_start","data":{"toolCallId":"call_01","toolName":"bash","toolTitle":"Run shell command","arguments":{"command":"npm test","description":"Run the test suite"},"model":"gpt-6.1-sol","turnId":"0"}}',
    '{"id":"e0000000-0000-4000-8000-000000000018","parentId":"e0000000-0000-4000-8000-000000000017","timestamp":"2026-10-01T09:00:08.000Z","type":"tool.execution_complete","data":{"toolCallId":"call_01","success":false,"result":{"content":"1 failing","detailedContent":"1 failing\\n  date.test.js: expected 2026"},"error":{"code":"failure","message":"Command exited with code 1"},"shellExecution":{"exitCode":1},"toolTelemetry":{"metrics":{},"properties":{}},"model":"gpt-6.1-sol","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"0","rte":false}}',
    '{"id":"e0000000-0000-4000-8000-000000000019","parentId":"e0000000-0000-4000-8000-000000000018","timestamp":"2026-10-01T09:00:08.100Z","type":"assistant.turn_end","data":{"turnId":"0"}}',
    '{"id":"e0000000-0000-4000-8000-000000000020","parentId":"e0000000-0000-4000-8000-000000000019","timestamp":"2026-10-01T09:00:08.200Z","type":"assistant.turn_start","data":{"interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"1"}}',
    '{"id":"e0000000-0000-4000-8000-000000000021","parentId":"e0000000-0000-4000-8000-000000000020","timestamp":"2026-10-01T09:00:10.000Z","type":"assistant.message","data":{"content":"","messageId":"7b7b7b7b-0000-4000-8000-000000000002","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","originatingMessageId":"2b2b2b2b-0000-4000-8000-000000000001","model":"gpt-6.1-sol","providerId":"copilot","turnId":"1","apiCallId":"resp_0002","rte":false,"toolRequests":[{"type":"custom","name":"apply_patch","toolCallId":"custom_0000000000000000000000000001","toolTitle":"Apply patch","arguments":"*** Begin Patch\\n*** Update File: /srv/proj/date.test.js\\n-2025\\n+2026\\n*** End Patch\\n","intentionSummary":"Update the fixture year"}]}}',
    '{"id":"e0000000-0000-4000-8000-000000000022","parentId":"e0000000-0000-4000-8000-000000000021","timestamp":"2026-10-01T09:00:10.100Z","type":"permission.requested","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000002","ownerSessionId":"5e55a0a1-0000-4000-8000-000000000001","agentMode":"interactive","permissionMode":"manual","permissionRequest":{"kind":"write","toolCallId":"custom_0000000000000000000000000001","intention":"Update the fixture year","fileName":"/srv/proj/date.test.js","diff":"-2025\\n+2026\\n","canOfferSessionApproval":true},"promptRequest":{"kind":"write","toolCallId":"custom_0000000000000000000000000001","intention":"Update the fixture year","fileName":"/srv/proj/date.test.js"}}}',
    '{"id":"e0000000-0000-4000-8000-000000000023","parentId":"e0000000-0000-4000-8000-000000000022","timestamp":"2026-10-01T09:00:12.000Z","type":"permission.completed","data":{"requestId":"8c8c8c8c-0000-4000-8000-000000000002","toolCallId":"custom_0000000000000000000000000001","decisionSource":"human_response","result":{"kind":"approved"}}}',
    '{"id":"e0000000-0000-4000-8000-000000000024","parentId":"e0000000-0000-4000-8000-000000000023","timestamp":"2026-10-01T09:00:12.100Z","type":"tool.execution_start","data":{"toolCallId":"custom_0000000000000000000000000001","toolName":"apply_patch","toolTitle":"Apply patch","arguments":{"input":"*** Begin Patch\\n*** Update File: /srv/proj/date.test.js\\n-2025\\n+2026\\n*** End Patch\\n"},"model":"gpt-6.1-sol","turnId":"1"}}',
    '{"id":"e0000000-0000-4000-8000-000000000025","parentId":"e0000000-0000-4000-8000-000000000024","timestamp":"2026-10-01T09:00:12.500Z","type":"tool.execution_complete","data":{"toolCallId":"custom_0000000000000000000000000001","success":true,"result":{"content":"Modified 1 file: /srv/proj/date.test.js"},"toolTelemetry":{"metrics":{},"properties":{}},"model":"gpt-6.1-sol","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"1","rte":false}}',
    '{"id":"e0000000-0000-4000-8000-000000000026","parentId":"e0000000-0000-4000-8000-000000000025","timestamp":"2026-10-01T09:00:12.600Z","type":"assistant.turn_end","data":{"turnId":"1"}}',
    '{"id":"e0000000-0000-4000-8000-000000000027","parentId":"e0000000-0000-4000-8000-000000000026","timestamp":"2026-10-01T09:00:12.700Z","type":"assistant.turn_start","data":{"interactionId":"1a1a1a1a-0000-4000-8000-000000000001","turnId":"2"}}',
    '{"id":"e0000000-0000-4000-8000-000000000028","parentId":"e0000000-0000-4000-8000-000000000027","timestamp":"2026-10-01T09:00:15.000Z","type":"assistant.message","data":{"content":"The fixture year was stale; it now reads 2026.","messageId":"7b7b7b7b-0000-4000-8000-000000000003","interactionId":"1a1a1a1a-0000-4000-8000-000000000001","originatingMessageId":"2b2b2b2b-0000-4000-8000-000000000001","model":"gpt-6.1-sol","providerId":"copilot","turnId":"2","phase":"final_answer","apiCallId":"resp_0003","rte":false,"toolRequests":[]}}',
    '{"id":"e0000000-0000-4000-8000-000000000029","parentId":"e0000000-0000-4000-8000-000000000028","timestamp":"2026-10-01T09:00:15.100Z","type":"assistant.turn_end","data":{"turnId":"2"}}',
    '{"id":"e0000000-0000-4000-8000-000000000030","parentId":"e0000000-0000-4000-8000-000000000029","timestamp":"2026-10-01T09:00:15.200Z","type":"session.usage_record","data":{"usage":{"model":"gpt-6.1-sol","inputTokens":900,"outputTokens":40,"initiator":"agent","interactionType":"conversation-agent","apiEndpoint":"ws:/responses","transport":"websocket","isByok":false,"accounting":{"sequence":1,"sourceSessionId":"5e55a0a1-0000-4000-8000-000000000001","usageId":"u-0001"}}}}',
    '{"id":"e0000000-0000-4000-8000-000000000031","parentId":"e0000000-0000-4000-8000-000000000030","timestamp":"2026-10-01T09:00:20.000Z","type":"session.model_change","data":{"previousModel":"gpt-6.1-sol","newModel":"auto","previousReasoningEffort":"medium","reasoningEffort":null,"contextTier":null,"source":"model_picker"}}',
    '{"id":"e0000000-0000-4000-8000-000000000032","parentId":"e0000000-0000-4000-8000-000000000031","timestamp":"2026-10-01T09:00:20.395Z","type":"session.info","data":{"message":"Model changed from GitHub Copilot \u2022 GPT-6.1 Sol (medium) to GitHub Copilot \u2022 Auto for this session","infoType":"model"}}',
    '{"id":"e0000000-0000-4000-8000-000000000033","parentId":"e0000000-0000-4000-8000-000000000032","timestamp":"2026-10-01T09:00:20.396Z","type":"session.info","data":{"message":"Auto routing profile change to Balance requested.","infoType":"model"}}',
    '{"id":"e0000000-0000-4000-8000-000000000034","parentId":"e0000000-0000-4000-8000-000000000033","timestamp":"2026-10-01T09:00:30.000Z","type":"session.shutdown","data":{"shutdownType":"routine","sessionStartTime":1790845199000,"totalApiDurationMs":9000,"eventsFileSizeBytes":20000,"codeChanges":{"filesModified":["/srv/proj/date.test.js"],"linesAdded":1,"linesRemoved":1},"modelMetrics":{},"currentModel":"gpt-6.1-sol"}}',
    '{"id":"e0000000-0000-4000-8000-000000000035","parentId":"e0000000-0000-4000-8000-000000000034","timestamp":"2026-10-01T09:01:00.000Z","type":"user.message","data":{"content":"and run',
]

# session-store.db, schema version 38 as research/copilot-cli.md section 5
# lists its tables; only the columns named there.
COPILOT_STORE_SCHEMA = """
CREATE TABLE sessions (id TEXT PRIMARY KEY, cwd TEXT, repository TEXT, host_type TEXT,
  branch TEXT, summary TEXT, created_at TEXT, updated_at TEXT);
CREATE TABLE turns (session_id TEXT, turn_index INTEGER, user_message TEXT,
  assistant_response TEXT, timestamp TEXT, UNIQUE (session_id, turn_index));
CREATE TABLE session_files (session_id TEXT, file_path TEXT, tool_name TEXT,
  turn_index INTEGER, first_seen_at TEXT, UNIQUE (session_id, file_path));
CREATE TABLE session_refs (session_id TEXT, ref_type TEXT, ref_value TEXT,
  turn_index INTEGER, created_at TEXT);
CREATE TABLE checkpoints (session_id TEXT, checkpoint_number INTEGER, title TEXT,
  overview TEXT, history TEXT, work_done TEXT, technical_details TEXT, important_files TEXT,
  next_steps TEXT, created_at TEXT);
CREATE TABLE forge_trajectory_events (session_id TEXT, tool_call_id TEXT, turn_index INTEGER,
  event_type TEXT, command TEXT, output TEXT, exit_code INTEGER, event_key TEXT,
  event_value TEXT, created_at TEXT);
CREATE TABLE assistant_usage_events (session_id TEXT, model TEXT, total_nano_aiu INTEGER);
"""

COPILOT_STORE_ROWS = [
    "INSERT INTO sessions VALUES ('5e55a0a1-0000-4000-8000-000000000001', '/srv/proj', NULL,"
    " NULL, NULL, 'Fix failing test', '2026-10-01T09:00:00.000Z', '2026-10-01T09:00:30.000Z')",
    "INSERT INTO turns (session_id, turn_index, user_message, assistant_response, timestamp)"
    " VALUES ('5e55a0a1-0000-4000-8000-000000000001', 0, 'fix the failing test',"
    " 'The fixture year was stale; it now reads 2026.', '2026-10-01T09:00:15.200Z')",
    "INSERT INTO turns (session_id, turn_index, user_message, assistant_response, timestamp)"
    " VALUES ('5e55a0a1-0000-4000-8000-000000000001', 1, 'and run lint', NULL,"
    " '2026-10-01T09:01:05.000Z')",
    "INSERT INTO session_files (session_id, file_path, tool_name, turn_index, first_seen_at)"
    " VALUES ('5e55a0a1-0000-4000-8000-000000000001', '/srv/proj/date.test.js', 'apply_patch',"
    " 0, '2026-10-01T09:00:12.500Z')",
]

# The research document's sample, with the three `mc_` keys set as a
# resumed session synced to the account wrote them on Windows 1.0.98 (issue
# 151); the values are synthetic UUIDs. The file's mtime is the resume.
COPILOT_MC_TASK = "1c1c1c1c-0000-4000-8000-000000000001"
COPILOT_MC_SESSION = "2d2d2d2d-0000-4000-8000-000000000001"
COPILOT_MC_LAST_EVENT = "3e3e3e3e-0000-4000-8000-000000000001"
COPILOT_WORKSPACE_MTIME = 1790845290  # 2026-10-01T09:01:30Z
COPILOT_WORKSPACE_YAML = """\
id: 5e55a0a1-0000-4000-8000-000000000001
cwd: /srv/proj
client_name: copilot-cli
name: Fix failing test
user_named: false
summary_count: 0
fork_count: 0
created_at: 2026-10-01T09:00:00.000Z
updated_at: 2026-10-01T09:00:30.000Z
remote_steerable: false
mc_task_id: %s
mc_session_id: %s
mc_last_event_id: %s
""" % (COPILOT_MC_TASK, COPILOT_MC_SESSION, COPILOT_MC_LAST_EVENT)

COPILOT_SETTINGS = """\
{
  // user settings
  "allowedUrls": ["https://registry.example.org"]
}
"""

COPILOT_LOG = """\
2026-10-01T08:59:59.100Z [INFO] Starting Copilot CLI: 1.0.98
2026-10-01T08:59:59.400Z [INFO] Signed in to https://github.com as octo-user.
2026-10-01T08:59:59.900Z [INFO] Workspace initialized: 5e55a0a1-0000-4000-8000-000000000001
"""


def copilot_snapshot_index() -> dict:
    """`rewind-file-snapshots/index.json` with the snapshot taken before the
    first prompt (its `eventId` is that `user.message` line's `id`), in the
    key layout of research/copilot-cli.md section 5; the file key is a
    synthetic hex digest and the images are left out."""
    return {
        "schema": 1,
        "snapshots": [
            {
                "snapshotId": "9d9d9d9d-0000-4000-8000-000000000001",
                "eventId": "e0000000-0000-4000-8000-000000000004",
                "timestamp": "2026-10-01T09:00:01.150Z",
                "userMessage": "fix the failing test",
                "fileCount": 1,
                "linesAdded": 1,
                "linesRemoved": 1,
                "backupFiles": [],
                "files": {
                    "a1" * 8: {
                        "path": "/srv/proj/date.test.js",
                        "linesAdded": 1,
                        "linesRemoved": 1,
                        "preimage": None,
                        "postimage": None,
                    }
                },
            }
        ],
    }


def build_copilot_cli(home: Path) -> None:
    events = home / COPILOT_EVENTS_REL
    events.parent.mkdir(parents=True, exist_ok=True)
    events.write_text("\n".join(COPILOT_EVENT_LINES), encoding="utf-8")
    (home / COPILOT_WORKSPACE_REL).write_text(COPILOT_WORKSPACE_YAML, encoding="utf-8")
    os.utime(home / COPILOT_WORKSPACE_REL, (COPILOT_WORKSPACE_MTIME, COPILOT_WORKSPACE_MTIME))
    _json_file(home / COPILOT_SNAPSHOTS_REL, copilot_snapshot_index())
    _wal_db(home / COPILOT_STORE_REL, COPILOT_STORE_SCHEMA, COPILOT_STORE_ROWS)
    # Newest first; `/model` was typed between the two prompts.
    _json_file(
        home / COPILOT_HISTORY_REL,
        {"commandHistory": ["and run lint", "/model", "fix the failing test"]},
    )
    _json_file(
        home / COPILOT_PERMISSIONS_REL,
        {
            "locations": {
                "/srv/proj": {
                    "tool_approvals": [
                        {"kind": "write"},
                        {"kind": "commands", "commandIdentifiers": ["npm test"]},
                    ]
                }
            }
        },
    )
    (home / COPILOT_SETTINGS_REL).write_text(COPILOT_SETTINGS, encoding="utf-8")
    for rel in (COPILOT_PERMISSIONS_REL, COPILOT_SETTINGS_REL):
        os.utime(home / rel, (COPILOT_SETTINGS_MTIME, COPILOT_SETTINGS_MTIME))
    _json_file(
        home / COPILOT_SIDEBAR_REL,
        {"schemaVersion": 1, "cwd": "/srv/proj", "sessionIds": [COPILOT_SESSION]},
    )
    (home / COPILOT_LOG_REL).parent.mkdir(parents=True, exist_ok=True)
    (home / COPILOT_LOG_REL).write_text(COPILOT_LOG, encoding="utf-8")
    # Noise the parser must not want (research/copilot-cli.md section 8).
    (home / ".copilot/config.json").write_text("{}", encoding="utf-8")
    (home / ".copilot/open-sessions-state.json").write_text("{}", encoding="utf-8")
    _json_file(home / COPILOT_DIR / "rewind-file-snapshots/tracking.json", {"schema": 1})
    (home / COPILOT_DIR / "checkpoints").mkdir(parents=True, exist_ok=True)
    (home / COPILOT_DIR / "checkpoints/index.md").write_text(
        "| # | Title |\n| --- | --- |\n", encoding="utf-8"
    )


# GitHub Copilot Desktop (issue 147): the app's own store `.copilot/data.db`,
# with the table and column names of research/copilot-desktop.md section 3
# (a subset of each table's columns, names exact). The project session's id
# is the Copilot CLI fixture's session, since the app's sessions are the
# bundled CLI's session-state directories. The rows live only in the -wal
# sidecar, as on a host where the app is still running. The four scheduling
# tables and the deletion intent were empty on the real install: their rows
# are fixture only.
COPILOT_DESKTOP_DB_REL = ".copilot/data.db"
COPILOT_DESKTOP_CHAT = "5d404e14-0000-4000-8000-000000000001"
COPILOT_DESKTOP_FORK = "9f9f9f9f-0000-4000-8000-000000000001"
COPILOT_DESKTOP_WORKTREE = "/home/alice/.copilot/repos/copilot-worktrees/proj/octo-user-happy-otter"
COPILOT_DESKTOP_MTIME = 1790850600  # 2026-10-01T10:30:00Z
# Checkpoint refs in the app's clone of the project (issue 147): one well
# formed, at the project session's checkpoint, and one malformed.
COPILOT_DESKTOP_REF_DIR = ".copilot/repos/proj/.git/refs/copilot/checkpoints/" + COPILOT_SESSION
COPILOT_DESKTOP_REF_REL = (
    COPILOT_DESKTOP_REF_DIR + "/00000000000000000001/e0000000-0000-4000-8000-000000000004"
)
COPILOT_DESKTOP_REF_MTIME = 1790845201  # 2026-10-01T09:00:01Z
COPILOT_DESKTOP_BAD_REF_REL = (
    COPILOT_DESKTOP_REF_DIR + "/00000000000000000002/e0000000-0000-4000-8000-000000000020"
)
COPILOT_DESKTOP_BAD_REF_MTIME = 1790845230  # 2026-10-01T09:00:30Z
COPILOT_DESKTOP_HEAD_REF_REL = ".copilot/repos/proj/.git/refs/heads/main"

COPILOT_DESKTOP_SCHEMA = """
CREATE TABLE "accounts" (id TEXT PRIMARY KEY NOT NULL, login TEXT NOT NULL, name TEXT,
  is_default INTEGER NOT NULL DEFAULT 0, host TEXT NOT NULL DEFAULT 'github.com',
  token_updated_at TEXT, created_at TEXT, updated_at TEXT, access_token TEXT,
  kind TEXT NOT NULL DEFAULT 'github', settings_json TEXT NOT NULL DEFAULT '{}',
  parent_account_id TEXT REFERENCES accounts(id) ON DELETE CASCADE);
CREATE TABLE settings (id INTEGER PRIMARY KEY CHECK (id = 1), last_active_workspace_id TEXT,
  storage_location TEXT NOT NULL DEFAULT '', instructions TEXT NOT NULL DEFAULT '',
  github_access_token TEXT, github_token_type TEXT, github_scope TEXT,
  github_token_updated_at TEXT);
CREATE TABLE sessions (id TEXT PRIMARY KEY NOT NULL, title TEXT,
  session_type TEXT NOT NULL DEFAULT 'workspace', mode TEXT, model TEXT, reasoning_effort TEXT,
  is_running INTEGER NOT NULL DEFAULT 0, was_interrupted INTEGER NOT NULL DEFAULT 0,
  interruption_reason TEXT, created_at TEXT, updated_at TEXT,
  remote_control_enabled INTEGER NOT NULL DEFAULT 0, auto_approve INTEGER NOT NULL DEFAULT 1,
  enabled_experiments_json TEXT, forked_from_session_id TEXT, archived_at TEXT,
  permission_mode TEXT);
CREATE TABLE projects (id TEXT PRIMARY KEY NOT NULL, name TEXT NOT NULL,
  container_kind TEXT NOT NULL DEFAULT 'repository'
    CHECK (container_kind IN ('folder', 'repository', 'collection')),
  main_repo_path TEXT NOT NULL UNIQUE, default_branch TEXT NOT NULL DEFAULT 'main',
  github_owner TEXT, github_repo TEXT, github_account_id TEXT, tab_order INTEGER,
  created_at TEXT, last_opened_at TEXT);
CREATE TABLE worktrees (id TEXT PRIMARY KEY NOT NULL,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE, path TEXT NOT NULL,
  branch TEXT NOT NULL, base_branch TEXT, created_at TEXT);
CREATE TABLE workspaces (id TEXT PRIMARY KEY NOT NULL,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  worktree_id TEXT REFERENCES worktrees(id) ON DELETE SET NULL,
  workspace_type TEXT NOT NULL CHECK (workspace_type IN ('worktree', 'branch', 'folder', 'cloud')),
  branch TEXT NOT NULL, name TEXT NOT NULL, tab_order INTEGER NOT NULL DEFAULT 0,
  port INTEGER NOT NULL DEFAULT 0, created_at TEXT, updated_at TEXT,
  source_pr_repo_full_name TEXT, source_pr_number INTEGER, created_pr_repo_full_name TEXT,
  created_pr_number INTEGER);
CREATE TABLE workspace_session_aliases (session_id TEXT PRIMARY KEY NOT NULL,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, created_at TEXT);
CREATE TABLE activity_items (id TEXT PRIMARY KEY NOT NULL,
  workspace_id TEXT REFERENCES workspaces(id) ON DELETE CASCADE, session_id TEXT,
  activity_type TEXT NOT NULL, preview TEXT NOT NULL DEFAULT '',
  is_read INTEGER NOT NULL DEFAULT 0, created_at TEXT, updated_at TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE session_checkpoints (session_id TEXT NOT NULL, event_id TEXT NOT NULL,
  commit_sha TEXT NOT NULL, created_at TEXT, PRIMARY KEY (session_id, event_id));
CREATE TABLE "model_providers" (id TEXT PRIMARY KEY NOT NULL, name TEXT NOT NULL,
  created_at TEXT, updated_at TEXT, type TEXT NOT NULL DEFAULT 'openai',
  settings_json TEXT NOT NULL DEFAULT '{}', account_id TEXT);
CREATE TABLE app_state (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL, updated_at TEXT);
CREATE TABLE my_copilot_scheduled_tasks (id TEXT PRIMARY KEY NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1, title TEXT NOT NULL, prompt TEXT NOT NULL,
  enabled INTEGER NOT NULL, execution_mode TEXT NOT NULL,
  background_agent_type TEXT NOT NULL DEFAULT 'general-purpose', created_at TEXT,
  updated_at TEXT, archived_at TEXT);
CREATE TABLE my_copilot_scheduled_task_triggers (id TEXT PRIMARY KEY NOT NULL,
  task_id TEXT NOT NULL, kind TEXT NOT NULL, enabled INTEGER NOT NULL,
  config_version INTEGER NOT NULL DEFAULT 1, config_json TEXT NOT NULL,
  state_version INTEGER NOT NULL DEFAULT 1, state_json TEXT NOT NULL DEFAULT '{}',
  next_run_at TEXT, last_fired_at TEXT, created_at TEXT, updated_at TEXT, archived_at TEXT);
CREATE TABLE my_copilot_scheduled_task_invocations (id TEXT PRIMARY KEY NOT NULL,
  task_id TEXT NOT NULL, trigger_id TEXT, occurrence_key TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL, scheduled_for TEXT, task_revision INTEGER NOT NULL,
  task_title TEXT NOT NULL, prompt_snapshot TEXT NOT NULL, trigger_snapshot_json TEXT,
  execution_mode TEXT NOT NULL, parent_session_id TEXT, runtime_agent_id TEXT,
  status TEXT NOT NULL, claimed_at TEXT NOT NULL, dispatched_at TEXT);
CREATE TABLE "session_automations" (session_id TEXT PRIMARY KEY NOT NULL, prompt TEXT NOT NULL,
  interval TEXT NOT NULL CHECK (interval IN ('once', 'minutes', 'daily', 'weekly')),
  every_minutes INTEGER, schedule_hour INTEGER NOT NULL DEFAULT 9,
  schedule_day INTEGER NOT NULL DEFAULT 1, last_run_at TEXT, next_run_at TEXT, updated_at TEXT,
  name TEXT, owner_session_id TEXT, paused_at TEXT);
CREATE TABLE session_deletion_intents (session_id TEXT PRIMARY KEY NOT NULL, created_at TEXT);
"""


def copilot_desktop_records() -> list[str]:
    """The INSERTs of the fixture `data.db`, in the order the parser reads
    the tables; `build_copilot_desktop` writes them to the -wal sidecar."""
    s, chat, fork = COPILOT_SESSION, COPILOT_DESKTOP_CHAT, COPILOT_DESKTOP_FORK
    return [
        "INSERT INTO accounts VALUES ('acc1', 'octo-user', 'Octo User', 1, 'github.com',"
        " '2026-10-01T08:50:00.000Z', '2026-10-01T08:50:00.000Z', '2026-10-01T08:50:00.000Z',"
        " NULL, 'github', '{}', NULL)",
        "INSERT INTO settings VALUES (1, 'ws1', '/home/alice/.copilot/repos', '', NULL, NULL,"
        " NULL, NULL)",
        "INSERT INTO model_providers VALUES ('mp1', 'GitHub Copilot', '2026-10-01T08:50:01.000Z',"
        " '2026-10-01T08:50:01.000Z', 'github_copilot', '{}', 'acc1')",
        "INSERT INTO projects VALUES ('p1', 'proj', 'repository', '/srv/proj', 'main',"
        " 'octo-user', 'proj', 'acc1', 0, '2026-10-01T08:55:00.000Z', '2026-10-01T09:00:00.000Z')",
        "INSERT INTO worktrees VALUES ('wt1', 'p1', '%s', 'octo-user-happy-otter', 'main',"
        " '2026-10-01T08:56:00.000Z')" % COPILOT_DESKTOP_WORKTREE,
        "INSERT INTO workspaces VALUES ('ws1', 'p1', 'wt1', 'worktree', 'octo-user-happy-otter',"
        " 'happy-otter', 0, 3000, '2026-10-01T08:56:01.000Z', '2026-10-01T08:56:01.000Z',"
        " 'octo-user/proj', 12, NULL, NULL)",
        "INSERT INTO workspace_session_aliases VALUES ('%s', 'ws1', '2026-10-01T09:00:00.000Z')"
        % s,
        # The project session first by rowid, to show the rows follow created_at.
        "INSERT INTO sessions (id, title, session_type, model, created_at, updated_at,"
        " remote_control_enabled, auto_approve, forked_from_session_id, archived_at,"
        " permission_mode) VALUES ('%s', 'Fix failing test', 'project', 'gpt-6.1-sol',"
        " '2026-10-01T09:00:00.000Z', '2026-10-01T09:00:30.000Z', 0, 1, '%s', NULL, 'on')"
        % (s, fork),
        "INSERT INTO sessions (id, title, session_type, model, created_at, updated_at,"
        " remote_control_enabled, auto_approve, forked_from_session_id, archived_at,"
        " permission_mode) VALUES ('%s', 'Say hello', 'general_chat', 'claude-sonnet-5.5',"
        " '2026-10-01T08:51:00.000Z', '2026-10-01T08:51:05.000Z', 0, 1, NULL,"
        " '2026-10-01T10:00:00.000Z', NULL)" % chat,
        "INSERT INTO activity_items VALUES ('a1', 'ws1', '%s', 'agent_idle',"
        " 'The fixture year was stale', 0, '2026-10-01T09:00:15.500Z',"
        " '2026-10-01T09:00:15.500Z', '{}')" % s,
        "INSERT INTO activity_items VALUES ('a2', NULL, '%s', 'agent_idle',"
        " 'Hello! How can I help?', 1, '2026-10-01T08:51:05.000Z', '2026-10-01T08:51:05.000Z',"
        " '{}')" % chat,
        "INSERT INTO activity_items VALUES ('a3', 'ws1', NULL, 'workspace_ready',"
        " 'Workspace happy-otter is ready', 1, '2026-10-01T08:56:02.000Z',"
        " '2026-10-01T08:56:02.000Z', '{}')",
        "INSERT INTO session_checkpoints VALUES ('%s', 'e0000000-0000-4000-8000-000000000004',"
        " '0123456789abcdef0123456789abcdef01234567', '2026-10-01T09:00:01.200Z')" % s,
        "INSERT INTO app_state VALUES ('permission-mode-default-on', 'true',"
        " '2026-10-01T08:50:00.000Z')",
        "INSERT INTO my_copilot_scheduled_tasks VALUES ('t1', 1, 'Nightly lint',"
        " 'run the linter', 1, 'background', 'general-purpose', '2026-10-01T09:10:00.000Z',"
        " '2026-10-01T09:10:00.000Z', NULL)",
        "INSERT INTO my_copilot_scheduled_task_triggers VALUES ('tr1', 't1', 'cron', 1, 1,"
        " '{\"cron\":\"0 2 * * *\"}', 1, '{}', '2026-10-02T02:00:00.000Z', NULL,"
        " '2026-10-01T09:10:01.000Z', '2026-10-01T09:10:01.000Z', NULL)",
        "INSERT INTO my_copilot_scheduled_task_invocations VALUES ('inv1', 't1', 'tr1',"
        " 't1:2026-10-02T02:00', 'schedule', '2026-10-02T02:00:00.000Z', 1, 'Nightly lint',"
        " 'run the linter', NULL, 'background', '%s', NULL, 'completed',"
        " '2026-10-02T02:00:01.000Z', '2026-10-02T02:00:02.000Z')" % chat,
        "INSERT INTO session_automations VALUES ('%s', 'check CI', 'daily', NULL, 9, 1, NULL,"
        " '2026-10-02T09:00:00.000Z', '2026-10-01T09:20:00.000Z', 'CI check', NULL, NULL)" % s,
        "INSERT INTO session_deletion_intents VALUES ('%s', '2026-10-01T10:05:00.000Z')" % chat,
    ]


def build_copilot_desktop(home: Path) -> None:
    _wal_db(home / COPILOT_DESKTOP_DB_REL, COPILOT_DESKTOP_SCHEMA, copilot_desktop_records())
    db = home / COPILOT_DESKTOP_DB_REL
    os.utime(db, (COPILOT_DESKTOP_MTIME, COPILOT_DESKTOP_MTIME))
    # Noise the parser must not want: the WebSocket token and the web view's
    # local storage (research/copilot-desktop.md section 2).
    run = home / ".copilot/run"
    run.mkdir(parents=True, exist_ok=True)
    (run / "ws.token").write_text("A" * 49, encoding="utf-8")
    store = home / ".local/share/com.github.githubapp/localstorage/tauri_localhost_0.localstorage"
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_bytes(b"SQLite format 3\x00not a real store")
    # The checkpoint refs the parser reads, and a branch ref it must not want.
    for rel, content, mtime in (
        (
            COPILOT_DESKTOP_REF_REL,
            "0123456789abcdef0123456789abcdef01234567\n",
            COPILOT_DESKTOP_REF_MTIME,
        ),
        (COPILOT_DESKTOP_BAD_REF_REL, "not-a-hash\n", COPILOT_DESKTOP_BAD_REF_MTIME),
        (COPILOT_DESKTOP_HEAD_REF_REL, "fedcba9876543210fedcba9876543210fedcba98\n", None),
    ):
        ref = home / rel
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(content, encoding="utf-8")
        if mtime:
            os.utime(ref, (mtime, mtime))
