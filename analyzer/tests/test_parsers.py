import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar, cast

from doubleagent import catalog, cli, protobuf, sqlite_util
from doubleagent.inputs import Artifact, Home, open_input
from doubleagent.model import compact, summarise
from doubleagent.parsers import Options, by_agent
from doubleagent.parsers.antigravity import (
    AntigravityParser,
    file_mtime,
    permission_texts,
    tool_args_summary,
    uri_to_path,
)
from doubleagent.parsers.claude_code import ClaudeCodeParser, tool_summary
from doubleagent.parsers.codex import CodexParser, flat_toml
from doubleagent.parsers.crush import CrushParser, project_of
from doubleagent.parsers.gemini_cli import GeminiCliParser, resolve_project
from doubleagent.parsers.goose import GooseParser, unescape_history
from doubleagent.timeutil import to_utc
from fixtures import (
    AGY,
    AGY_APP_CONVERSATION,
    AGY_APP_PROJECT,
    AGY_CONVERSATION,
    CLAUDE_295_SESSION,
    CLAUDE_296_SESSION,
    CLAUDE_BRIDGE_SESSION,
    CLAUDE_REGISTRY_KEY,
    CLAUDE_SESSION,
    CLAUDE_SETTINGS_MTIME,
    CLAUDE_WORK_SESSION,
    CODEX_ACCOUNT,
    CODEX_AUTOMATION_MTIME,
    CODEX_AUTOMATION_REL,
    CODEX_AUTOMATION_TOML,
    CODEX_FORK,
    CODEX_LEGACY,
    CODEX_REVERT_ROLLOUT,
    CODEX_SESSION,
    CODEX_SUBAGENT,
    CODEX_USER,
    CRUSH_SESSION,
    GEMINI_HASH,
    GEMINI_LEGACY,
    GEMINI_REL,
    GEMINI_RESUMED,
    GEMINI_SESSION,
    GEMINI_SUBAGENT,
    GOOSE_LEGACY_REL,
    GOOSE_SESSION,
    build_home,
    claude_project_local_settings,
    codex_fork_records,
    codex_legacy_records,
    codex_rollout_records,
    codex_subagent_records,
    write_bad_line,
)


class TimeTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(to_utc("2026-10-01T10:00:00.000Z"), "2026-10-01T10:00:00.000Z")
        self.assertEqual(to_utc("2026-10-01T12:00:00+02:00"), "2026-10-01T10:00:00.000Z")
        self.assertEqual(to_utc(1790848800000), "2026-10-01T10:00:00.000Z")  # ms
        self.assertEqual(to_utc(1790848800), "2026-10-01T10:00:00.000Z")  # s
        self.assertEqual(to_utc("1790848800"), "2026-10-01T10:00:00.000Z")
        # go-sqlite3 trims trailing fraction zeros; Go keeps nanoseconds.
        self.assertEqual(to_utc("2026-03-01 09:00:00.5-08:00"), "2026-03-01T17:00:00.500Z")
        self.assertEqual(to_utc("2026-03-01 09:00:01.25-08:00"), "2026-03-01T17:00:01.250Z")
        self.assertEqual(to_utc("2026-03-01T09:00:00.123456789Z"), "2026-03-01T09:00:00.123Z")
        self.assertEqual(to_utc(None), "")
        self.assertEqual(to_utc("garbage"), "")


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return [json.loads(line) for line in fh]


class JsonlOutputTests(unittest.TestCase):
    def test_text_keeps_inner_whitespace(self):
        self.assertEqual(compact("  line one\n    indented\n"), "line one\n    indented")
        self.assertEqual(compact(None), "")

    def test_one_record_per_line(self):
        for text in ("a\nb\r\nc", "a\u2028b\u2029c", "lone \ud800 surrogate", "caf\u00e9"):
            line = cli.jsonl_line({"text": text})
            self.assertEqual(len(line.splitlines()), 1, repr(text))
            self.assertEqual(json.loads(line), {"text": text})
        self.assertIn("caf\u00e9", cli.jsonl_line({"text": "caf\u00e9"}))


class ParserBase(unittest.TestCase):
    def setUp(self):
        self.cat = catalog.load()
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-analyzer-test-"))
        self.home = build_home(self.tmp / "home" / "alice")
        self.col = open_input(self.tmp / "home", self.cat, host="h1")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def artifact(self, rel):
        return next(a for a in self.col.artifacts if a.rel == rel)

    def rows_for(self, parser, rel, **kw):
        return list(parser.parse(self.artifact(rel), Options(**kw)))


class ClaudeCodeTests(ParserBase):
    REL = ".claude/projects/-srv-proj/%s.jsonl" % CLAUDE_SESSION
    SUB = ".claude/projects/-srv-proj/%s/subagents/agent-abc.jsonl" % CLAUDE_SESSION
    FORK = ".claude/projects/-srv-proj/%s/subagents/agent-fork1.jsonl" % CLAUDE_SESSION

    # (source_line, turn_type, text) for every row of the fixture session;
    # an empty text is checked in its own test.
    EXPECTED: ClassVar[list[tuple[int, str, str]]] = [
        (2, "user", "delete the logs in /var/log please"),
        (3, "system", "model: claude-fable-5-1"),
        (5, "tool_use", "cd /srv/proj && rm -rf /var/log/*.log"),
        (6, "tool_result", "removed 3 files"),
        (7, "system", "prompt queued: delivered at line 8"),
        (8, "user", "also check /tmp"),
        (9, "system", "edited file: /srv/proj/notes.md"),
        (10, "system", "hook: PostToolUse:Bash: lint passed"),
        (12, "assistant", "Done. Three log files were removed."),
        (13, "system", "turn_duration: 4000 ms, 5 messages"),
        (
            14,
            "system",
            "slash command: <command-name>/model</command-name>\n"
            "<command-message>model</command-message>\n<command-args></command-args>",
        ),
        (
            15,
            "system",
            "command output: <local-command-stdout>Set model to Fable</local-command-stdout>",
        ),
        (
            16,
            "system",
            "task notification: <task-notification>\n<task-id>b1</task-id>\n"
            "<status>completed</status>\n</task-notification>",
        ),
        (17, "tool_use", "select:WebFetch"),
        (18, "tool_result", "WebFetch"),
        (19, "tool_use", "/srv/proj/big.log"),
        (20, "tool_result", "line 1 of the full output\nline 2 of the full output"),
        (21, "tool_use", "/srv/proj/gone.log"),
        (22, "tool_result", ""),
        (23, "system", "api error: 429 rate_limit: API Error: rate limited"),
        (
            24,
            "system",
            'api_error: {"level":"error","maxRetries":10,"retryAttempt":1,"retryInMs":500}',
        ),
        (25, "system", "interrupted: [Request interrupted by user]"),
        (
            26,
            "system",
            "compaction summary: This session is being continued from a previous "
            "conversation. Summary: logs removed.",
        ),
        (27, "system", "session title: Remove old logs"),
        (29, "system", "session title: log cleanup"),
        (30, "system", "pr-link: https://github.com/x/y/pull/7"),
        (32, "system", "cwd changed: /srv/proj2"),
        (33, "user", "thanks"),
    ]

    def test_secondary(self):
        # The history file is a secondary source, the transcript is not (#122).
        p = ClaudeCodeParser()
        self.assertTrue(p.secondary(self.artifact(".claude/history.jsonl")))
        self.assertFalse(p.secondary(self.artifact(self.REL)))

    def test_rows(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual(
            [(r.source_line, r.turn_type) for r in rows], [(n, t) for n, t, _ in self.EXPECTED]
        )
        for r, (_n, _t, text) in zip(rows, self.EXPECTED, strict=True):
            if text:
                self.assertEqual(r.text, text)
        for r in rows:
            self.assertEqual((r.host, r.user, r.agent), ("h1", "alice", "claude-code"))
            self.assertEqual(r.session_id, CLAUDE_SESSION)
            self.assertEqual(r.source_file, "/alice/" + self.REL)  # relative to the input root
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
            self.assertEqual(r.git_branch, "main", r)
        by_line = {r.source_line: r for r in rows}
        use = by_line[5]
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.model), ("Bash", "toolu_01", "claude-fable-5-1")
        )
        self.assertEqual(by_line[6].tool_use_id, "toolu_01")
        self.assertEqual(
            (by_line[18].tool_use_id, by_line[20].tool_use_id), ("toolu_02", "toolu_03")
        )
        self.assertEqual(by_line[23].model, "")

    def test_state_rows_take_session_project_and_time(self):
        rows = {r.source_line: r for r in self.rows_for(ClaudeCodeParser(), self.REL)}
        for n in (27, 29, 30):
            self.assertEqual(rows[n].project_path, "/srv/proj")
        # Title records have no timestamp: the latest one seen is used.
        self.assertEqual(rows[27].timestamp_utc, "2026-10-01T10:00:17.000Z")
        # After `relocated`, rows take the new cwd.
        self.assertEqual(rows[32].project_path, "/srv/proj2")
        self.assertEqual(rows[33].project_path, "/srv/proj2")
        self.assertEqual(rows[2].project_path, "/srv/proj")

    def test_duplicates_dropped(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        texts = [r.text for r in rows]
        self.assertEqual(texts.count("pr-link: https://github.com/x/y/pull/7"), 1)
        self.assertEqual(texts.count("session title: Remove old logs"), 1)
        # The enqueue on line 7 is delivered by the attachment on line 8: the
        # prompt text appears once, and the enqueue keeps its own time.
        self.assertEqual(sum("also check /tmp" in t for t in texts), 1)
        queued = next(r for r in rows if r.source_line == 7)
        self.assertEqual(queued.timestamp_utc, "2026-10-01T10:00:03.500Z")
        self.assertEqual(queued.project_path, "/srv/proj")

    def test_undelivered_enqueue_keeps_its_text(self):
        path = self.home / self.REL
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(
                '{"type":"queue-operation","operation":"enqueue",'
                '"timestamp":"2026-10-01T10:00:30.000Z","sessionId":"%s",'
                '"content":"never delivered"}\n' % CLAUDE_SESSION
            )
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual(rows[-1].text, "queue enqueue: never delivered")
        self.assertEqual(rows[-1].source_line, 35)

    def test_persisted_output(self):
        rows = {r.source_line: r for r in self.rows_for(ClaudeCodeParser(), self.REL)}
        self.assertEqual(rows[20].text, "line 1 of the full output\nline 2 of the full output")
        missing = rows[22].text
        self.assertTrue(missing.startswith("<persisted-output>"), missing)
        self.assertTrue(
            missing.endswith("[persisted output not found: tool-results/f0e1d2c3b.txt]"), missing
        )

    def test_persisted_output_not_through_symlink(self):
        tr = self.home / ".claude/projects/-srv-proj" / CLAUDE_SESSION / "tool-results"
        stored = tr / "b1c2d3e4f.txt"
        target = self.tmp / "outside.txt"
        target.write_text("outside", encoding="utf-8")
        stored.unlink()
        try:
            stored.symlink_to(target)
        except OSError:
            self.skipTest("symlinks not available")
        rows = {r.source_line: r for r in self.rows_for(ClaudeCodeParser(), self.REL)}
        self.assertIn("[persisted output not found", rows[20].text)
        self.assertNotIn("outside", rows[20].text)

    def test_thinking_opt_in(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL, include_thinking=True)
        thinking = [r for r in rows if r.turn_type == "thinking"]
        # The empty block on line 4 (signature only) is skipped.
        self.assertEqual([(r.source_line, r.text) for r in thinking], [(3, "private reasoning")])

    def test_history(self):
        rows = self.rows_for(ClaudeCodeParser(), ".claude/history.jsonl")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].timestamp_utc, "2026-10-01T10:00:00.000Z")
        self.assertEqual(rows[0].project_path, "/srv/proj")
        self.assertEqual(rows[1].project_path, "/srv/old")
        self.assertTrue(all(r.turn_type == "user" for r in rows))

    def test_subagent_file(self):
        rows = self.rows_for(ClaudeCodeParser(), self.SUB)
        self.assertEqual(
            [(r.source_line, r.turn_type, r.text) for r in rows],
            [
                (1, "system", "subagent abc of %s" % CLAUDE_SESSION),
                (1, "system", "subagent task: Find where the logs are rotated."),
                (2, "system", "model: claude-fable-5-1"),
                (2, "assistant", "By logrotate."),
            ],
        )
        self.assertTrue(all(r.session_id == CLAUDE_SESSION for r in rows))

    def test_fork_subagent_file(self):
        rows = self.rows_for(ClaudeCodeParser(), self.FORK)
        self.assertEqual(
            [(r.source_line, r.turn_type) for r in rows],
            [
                (1, "system"),
                (1, "user"),
                (2, "system"),
                (2, "tool_use"),
                (3, "tool_result"),
                (3, "system"),
            ],
        )
        self.assertEqual(rows[0].text, "subagent fork1 of %s" % CLAUDE_SESSION)
        # The copied context keeps its rows; the boilerplate block is the task.
        self.assertEqual(rows[1].text, "delete the logs in /var/log please")
        # The fork tracks its own model.
        self.assertEqual(rows[2].text, "model: claude-fable-5-1")
        self.assertTrue(rows[5].text.startswith("subagent task: <fork-boilerplate>"), rows[5].text)

    def test_sidecars_not_wanted(self):
        base = ".claude/projects/-srv-proj/%s/" % CLAUDE_SESSION
        for rel in (
            base + "subagents/agent-abc.meta.json",
            base + "tool-results/b1c2d3e4f.txt",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(ClaudeCodeParser().wants(art), rel)

    def test_relocated_config_home(self):
        # CLAUDE_CONFIG_DIR=~/.claude-work: the session and history are parsed.
        rel = ".claude-work/projects/-srv-proj/%s.jsonl" % CLAUDE_WORK_SESSION
        art = next(a for a in self.col.artifacts if a.rel == rel)
        self.assertEqual(art.agent, "claude-code")
        rows = self.rows_for(ClaudeCodeParser(), rel)
        self.assertEqual(
            [(r.source_line, r.turn_type, r.text) for r in rows],
            [
                (1, "user", "rotate the work logs"),
                (2, "system", "model: claude-fable-5-1"),
                (2, "assistant", "Rotated."),
            ],
        )
        self.assertTrue(all(r.session_id == CLAUDE_WORK_SESSION for r in rows))
        self.assertTrue(all(r.project_path == "/srv/proj" for r in rows))
        rows = self.rows_for(ClaudeCodeParser(), ".claude-work/history.jsonl")
        self.assertEqual(
            [(r.turn_type, r.session_id) for r in rows], [("user", CLAUDE_WORK_SESSION)]
        )

    def test_claude_code_router_not_wanted(self):
        # .claude-code-router shares the prefix but is not a Claude Code home:
        # the catalog does not claim it and the parser would not want it.
        self.assertFalse(any(".claude-code-router" in a.rel for a in self.col.artifacts))
        home = self.col.artifacts[0].home
        for rel in (".claude-code-router/config.json", ".claude-code-router/history.json"):
            art = Artifact(self.home / rel, rel, rel, "claude-code", home)
            self.assertFalse(ClaudeCodeParser().wants(art), rel)

    def test_tool_summary_shapes(self):
        self.assertEqual(
            tool_summary("Edit", {"file_path": "/a", "old_string": "x", "new_string": "y"}), "/a"
        )
        self.assertEqual(tool_summary("Grep", {"pattern": "foo", "path": "/src"}), "foo | /src")
        self.assertEqual(tool_summary("Unknown", {"z": 1, "a": 2}), '{"a":2,"z":1}')
        self.assertEqual(tool_summary("Unknown", "raw"), '"raw"')

    def test_truncated_last_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual(len(rows), len(self.EXPECTED) + 1)
        self.assertIn("1 unparseable line", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 35)


class ClaudeCode295Tests(ParserBase):
    """Claude Code 2.1.295: permission decisions, the state lines that
    version writes, and the per-process registry `sessions/<pid>.json`."""

    REL = ".claude/projects/-srv-proj/%s.jsonl" % CLAUDE_295_SESSION
    REG = ".claude/sessions/4242.json"
    BRIDGE = ".claude/sessions/4343.json"

    EXPECTED: ClassVar[list[tuple[int, str, str]]] = [
        (1, "system", "prompt queued: delivered at line 4"),
        (2, "system", "queue dequeue:"),
        (4, "system", "permission mode: auto"),
        (4, "user", "list the cron jobs"),
        (5, "system", "model: claude-fable-5-1"),
        (5, "tool_use", "cd /srv/proj && crontab -l"),
        (6, "tool_result", "0 3 * * * x"),
        (6, "system", "permission decision: allow source=auto_mode reason=classifier"),
        (
            8,
            "system",
            'stop_hook_summary: {"hasOutput":false,"hookAdditionalContext":[],"hookCount":1,'
            '"hookErrors":[],"hookInfos":[{"command":"true","durationMs":5}],'
            '"level":"suggestion","preventedContinuation":false,"stopReason":"",'
            '"toolUseID":"toolu_95"}',
        ),
    ]

    def test_rows(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual([(r.source_line, r.turn_type, r.text) for r in rows], self.EXPECTED)
        for r in rows:
            self.assertEqual(r.session_id, CLAUDE_295_SESSION)
            self.assertEqual(r.project_path, "/srv/proj")
            self.assertEqual(r.git_branch, "main")
        # The state lines (snapshot, delta, last-prompt, atis-latch) yield
        # nothing, and no line is reported unreadable.
        self.assertFalse(any(r.text.startswith("parser:") for r in rows))

    def test_permission_decision_row(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        i = next(i for i, r in enumerate(rows) if r.text.startswith("permission decision:"))
        result, perm = rows[i - 1], rows[i]
        self.assertEqual(result.turn_type, "tool_result")
        self.assertEqual(
            (perm.turn_type, perm.tool_use_id, perm.tool_name, perm.timestamp_utc, perm.model),
            ("system", "toolu_95", "", "2026-10-01T11:00:03.000Z", ""),
        )

    def test_permission_decision_extra_and_missing_keys(self):
        path = self.home / self.REL
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "type": "user",
                        "sessionId": CLAUDE_295_SESSION,
                        "timestamp": "2026-10-01T11:00:09.000Z",
                        "message": {
                            "role": "user",
                            "content": [
                                {"type": "tool_result", "tool_use_id": "toolu_96", "content": "x"},
                                {"type": "tool_result", "tool_use_id": "toolu_97", "content": "y"},
                            ],
                        },
                        "permissionDecision": {"decision": "deny", "ruleId": "r1"},
                    }
                )
                + "\n"
            )
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.tool_use_id) for r in rows[-3:]],
            [("tool_result", "toolu_96"), ("tool_result", "toolu_97"), ("system", "toolu_96")],
        )
        self.assertEqual(
            rows[-1].text,
            'permission decision: deny source=- reason=- {"decision":"deny","ruleId":"r1"}',
        )

    def _append_result(self, tool_use_id: str, **keys):
        rec = {
            "type": "user",
            "sessionId": CLAUDE_295_SESSION,
            "timestamp": "2026-10-01T11:00:10.000Z",
            "message": {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": "no"}],
            },
        }
        rec.update(keys)
        with open(self.home / self.REL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")

    def test_denial_kind_and_feedback(self):
        # Issue 97: `toolDenialKind` and `userFeedback` on the same line are
        # appended to the decision row, printed as recorded (no value set is
        # in the research; these values are fixture only).
        self._append_result(
            "toolu_95",
            permissionDecision={"decision": "deny", "source": "user", "reasonType": "rule"},
            toolDenialKind="user_rejected",
            userFeedback="use the read-only listing instead",
        )
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        # Every earlier row is unchanged.
        self.assertEqual(
            [(r.source_line, r.turn_type, r.text) for r in rows[: len(self.EXPECTED)]],
            self.EXPECTED,
        )
        perm = rows[-1]
        self.assertEqual(
            (perm.turn_type, perm.tool_use_id, perm.timestamp_utc, perm.text),
            (
                "system",
                "toolu_95",
                "2026-10-01T11:00:10.000Z",
                "permission decision: deny source=user reason=rule "
                "toolDenialKind=user_rejected userFeedback=use the read-only listing instead",
            ),
        )

    def test_denial_keys_without_decision(self):
        self._append_result("toolu_95", toolDenialKind="user_rejected")
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.tool_use_id, r.text) for r in rows[-2:]],
            [
                ("tool_result", "toolu_95", "no"),
                (
                    "system",
                    "toolu_95",
                    "permission decision: - source=- reason=- toolDenialKind=user_rejected",
                ),
            ],
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL, include_thinking=True)
        self.assertEqual([r for r in rows if r.turn_type == "thinking"], [])
        self.assertEqual(len(rows), len(self.EXPECTED))

    def test_registry_rows(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REG)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(
            (
                r.turn_type,
                r.text,
                r.timestamp_utc,
                r.session_id,
                r.project_path,
                r.model,
                r.source_line,
            ),
            (
                "system",
                "claude-code process 4242 interactive status=idle entrypoint=claude-desktop "
                "bridge=none host_session=local_f4f4f4f4-9999-4aaa-8bbb-cccccccccccc",
                "2026-10-01T11:00:00.000Z",
                CLAUDE_295_SESSION,
                "/srv/proj",
                "",
                1,
            ),
        )
        self.assertEqual(r.source_file, "/alice/" + self.REG)
        # The registry row joins the session's transcript rows.
        sessions = {x.session_id for x in self.rows_for(ClaudeCodeParser(), self.REL)}
        self.assertEqual(sessions, {r.session_id})
        rows = self.rows_for(ClaudeCodeParser(), self.BRIDGE)
        self.assertEqual(
            [(x.text, x.session_id, x.timestamp_utc) for x in rows],
            [
                (
                    "claude-code process 4343 interactive status=busy entrypoint=cli "
                    "bridge=cse_0123456789abcdef host_session=none",
                    CLAUDE_BRIDGE_SESSION,
                    "2026-10-01T12:00:00.000Z",
                )
            ],
        )

    def test_registry_missing_keys(self):
        (self.home / self.REG).write_text('{"pid": 4242}', encoding="utf-8")
        rows = self.rows_for(ClaudeCodeParser(), self.REG)
        self.assertEqual(
            [(r.text, r.timestamp_utc, r.session_id) for r in rows],
            [
                (
                    "claude-code process 4242 - status=- entrypoint=- bridge=none "
                    "host_session=none",
                    "",
                    "",
                )
            ],
        )

    def test_not_wanted(self):
        rel = ".claude/sessions/" + CLAUDE_REGISTRY_KEY
        art = next(a for a in self.col.artifacts if a.rel == rel)
        self.assertEqual(art.agent, "claude-code")
        self.assertFalse(ClaudeCodeParser().wants(art))

    def test_registry_not_json_object(self):
        for body in ('{"pid": 42', "[1, 2]"):
            (self.home / self.REG).write_text(body, encoding="utf-8")
            rows = self.rows_for(ClaudeCodeParser(), self.REG)
            self.assertEqual(
                [(r.turn_type, r.source_line, r.text) for r in rows],
                [("system", 1, "parser: session registry file is not a JSON object")],
            )

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual(len(rows), len(self.EXPECTED) + 1)
        self.assertEqual(rows[-1].text, "parser: 1 unparseable line(s), first at line 11")


class ClaudeCode296Tests(ParserBase):
    """Permission mode and model as events, and the standing permission
    settings in settings.json, settings.local.json and .claude.json (issue
    93)."""

    REL = ".claude/projects/-srv-proj/%s.jsonl" % CLAUDE_296_SESSION
    SETTINGS_TS = "2026-10-01T09:00:00.000Z"

    EXPECTED: ClassVar[list[tuple[int, str, str]]] = [
        (1, "system", "permission mode: auto"),
        (1, "user", "plan the log cleanup"),
        (2, "system", "model: claude-fable-5-1"),
        (2, "assistant", "Here is a plan."),
        (4, "system", "permission mode: auto -> plan"),
        (5, "user", "go on"),
        (
            6,
            "system",
            "slash command: <command-name>/model</command-name>\n"
            "<command-message>model</command-message>\n<command-args>opus</command-args>",
        ),
        (
            7,
            "system",
            "command output: <local-command-stdout>Set model to `Opus 5.5` and saved as "
            "your default for new sessions</local-command-stdout>",
        ),
        (8, "system", "model: claude-fable-5-1 -> claude-opus-5-5 requested=opus"),
        (8, "assistant", "Switched."),
        (9, "system", "permission mode: plan -> acceptEdits"),
        (9, "user", "apply it"),
        (10, "assistant", "Applied."),
    ]

    def test_rows(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual([(r.source_line, r.turn_type, r.text) for r in rows], self.EXPECTED)
        for r in rows:
            self.assertEqual((r.session_id, r.project_path), (CLAUDE_296_SESSION, "/srv/proj"))

    def test_mode_and_model_columns_and_times(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        by = {(r.source_line, r.text.split(":")[0]): r for r in rows if r.turn_type == "system"}
        # A user line's mode row takes the line's time; a permission-mode
        # record has none and takes the latest seen.
        self.assertEqual(by[1, "permission mode"].timestamp_utc, "2026-10-01T12:00:01.000Z")
        self.assertEqual(by[4, "permission mode"].timestamp_utc, "2026-10-01T12:00:02.000Z")
        self.assertEqual(by[1, "permission mode"].model, "")
        self.assertEqual(by[2, "model"].model, "claude-fable-5-1")
        self.assertEqual(by[8, "model"].model, "claude-opus-5-5")
        self.assertEqual(by[8, "model"].timestamp_utc, "2026-10-01T12:00:08.000Z")

    def test_subagent_tracks_its_own_mode(self):
        # A subagent file of the session starts its own tracker.
        rel = ".claude/projects/-srv-proj/%s/subagents/agent-m1.jsonl" % CLAUDE_296_SESSION
        path = self.home / rel
        path.parent.mkdir(parents=True)
        lines = [
            {
                "type": "user",
                "sessionId": CLAUDE_296_SESSION,
                "agentId": "m1",
                "timestamp": "2026-10-01T12:00:20.000Z",
                "message": {"role": "user", "content": "check it"},
                "permissionMode": "acceptEdits",
            },
            {
                "type": "assistant",
                "sessionId": CLAUDE_296_SESSION,
                "agentId": "m1",
                "timestamp": "2026-10-01T12:00:21.000Z",
                "message": {
                    "model": "claude-opus-5-5",
                    "content": [{"type": "text", "text": "ok"}],
                },
            },
        ]
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        self.col = open_input(self.tmp / "home", self.cat, host="h1")
        rows = self.rows_for(ClaudeCodeParser(), rel)
        self.assertEqual(
            [r.text for r in rows],
            [
                "subagent m1 of %s" % CLAUDE_296_SESSION,
                "permission mode: acceptEdits",
                "subagent task: check it",
                "model: claude-opus-5-5",
                "ok",
            ],
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(ClaudeCodeParser(), self.REL, include_thinking=True)
        self.assertEqual(len(rows), len(self.EXPECTED))

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(ClaudeCodeParser(), self.REL)
        self.assertEqual(len(rows), len(self.EXPECTED) + 1)
        self.assertEqual(rows[-1].text, "parser: 1 unparseable line(s), first at line 11")

    def test_user_settings_rows(self):
        rows = self.rows_for(ClaudeCodeParser(), ".claude/settings.json")
        src = "(from .claude/settings.json, file mtime)"
        self.assertEqual(
            [r.text for r in rows],
            [
                "permission setting: permissions.allow=Bash(npm test:*) " + src,
                "permission setting: permissions.allow=Read(~/notes/**) " + src,
                "permission setting: permissions.deny=Bash(rm -rf:*) " + src,
                "permission setting: permissions.ask=WebFetch " + src,
                "permission setting: permissions.additionalDirectories=/srv/shared " + src,
                "permission setting: permissions.defaultMode=acceptEdits " + src,
                "permission setting: permissions.disableBypassPermissionsMode=disable " + src,
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.turn_type, r.timestamp_utc, r.session_id, r.project_path, r.agent),
                ("system", self.SETTINGS_TS, "", "", "claude-code"),
            )
            # env and apiKeyHelper are never read.
            self.assertNotIn("not-a-real-key", r.text)

    def test_global_config_rows(self):
        rows = self.rows_for(ClaudeCodeParser(), ".claude.json")
        src = "(from .claude.json, file mtime)"
        self.assertEqual(
            [(r.text, r.project_path, r.timestamp_utc) for r in rows],
            [
                (
                    "permission setting: allowedTools=Bash(git status) " + src,
                    "/srv/proj",
                    self.SETTINGS_TS,
                ),
                (
                    "permission setting: hasTrustDialogAccepted=true " + src,
                    "/srv/proj",
                    self.SETTINGS_TS,
                ),
                (
                    "permission setting: hasClaudeMdExternalIncludesApproved=false " + src,
                    "/srv/proj",
                    self.SETTINGS_TS,
                ),
            ],
        )
        for r in rows:
            self.assertNotIn("example.invalid", r.text)
            self.assertNotIn("Authorization", r.text)
        rows = self.rows_for(ClaudeCodeParser(), ".claude-work/.claude.json")
        self.assertEqual(
            [(r.text, r.project_path) for r in rows],
            [
                (
                    "permission setting: allowedTools=Edit "
                    "(from .claude-work/.claude.json, file mtime)",
                    "/srv/work",
                )
            ],
        )

    def test_manifest_mtime_wins(self):
        art = next(a for a in self.col.artifacts if a.rel == ".claude/settings.json")
        art.manifest = {"mtime": CLAUDE_SETTINGS_MTIME + 3600}
        rows = list(ClaudeCodeParser().parse(art, Options()))
        self.assertEqual({r.timestamp_utc for r in rows}, {"2026-10-01T10:00:00.000Z"})

    def test_project_local_settings(self):
        # A file the collector found in a discovered project: agent
        # `project`, home the project directory.
        proj = self.tmp / "srv" / "proj"
        path = proj / ".claude/settings.local.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(claude_project_local_settings()), encoding="utf-8")
        rel = ".claude/settings.local.json"
        home = Home(disk_path=proj, original="/srv/proj", user="alice", host="h1", project=True)
        art = Artifact(path, "/srv/proj/" + rel, rel, "project", home)
        self.assertIn(ClaudeCodeParser, [type(x) for x in cli.parsers_for(art, {})])
        self.assertTrue(ClaudeCodeParser().wants(art))
        rows = list(ClaudeCodeParser().parse(art, Options()))
        # A collector from 1.12.0 names the agent; the rows are the same.
        own = Artifact(path, "/srv/proj/" + rel, rel, "claude-code", home)
        self.assertIn(ClaudeCodeParser, [type(x) for x in cli.parsers_for(own, by_agent())])
        self.assertEqual(
            [r.as_dict() for r in ClaudeCodeParser().parse(own, Options())],
            [r.as_dict() for r in rows],
        )
        src = "(from .claude/settings.local.json, file mtime)"
        self.assertEqual(
            [(r.text, r.project_path, r.source_file) for r in rows],
            [
                (
                    "permission setting: permissions.allow=Bash(make lint) " + src,
                    "/srv/proj",
                    "/srv/proj/" + rel,
                ),
                (
                    "permission setting: permissions.defaultMode=plan " + src,
                    "/srv/proj",
                    "/srv/proj/" + rel,
                ),
            ],
        )

    def test_settings_without_permissions_and_unreadable(self):
        path = self.home / ".claude/settings.json"
        path.write_text('{"model": "opus", "env": {"X": "y"}}', encoding="utf-8")
        self.assertEqual(self.rows_for(ClaudeCodeParser(), ".claude/settings.json"), [])
        for body in ("[1]", "{not json"):
            path.write_text(body, encoding="utf-8")
            rows = self.rows_for(ClaudeCodeParser(), ".claude/settings.json")
            self.assertEqual(
                [(r.turn_type, r.text) for r in rows],
                [("system", "parser: settings file is not a JSON object")],
            )

    def test_backups_and_other_files_not_wanted(self):
        for rel in (".claude.json.backup.1790845200000",):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(ClaudeCodeParser().wants(art), rel)
        home = self.col.artifacts[0].home
        for rel in (
            ".claude/settings.json.bak",
            ".claude/cowork_settings.json",
            ".claude/.credentials.json",
            "proj/.claude/settings.json",
        ):
            art = Artifact(self.home / rel, rel, rel, "claude-code", home)
            self.assertFalse(ClaudeCodeParser().wants(art), rel)


class CodexTests(ParserBase):
    REL = ".codex/sessions/2026/10/02/rollout-2026-10-02T09-00-00-%s.jsonl" % CODEX_SESSION
    TYPES: ClassVar[list[str]] = [
        "system",  # session start
        "system",  # model: (first turn_context)
        "system",  # permission mode: (first turn_context)
        "system",  # task_started
        "system",  # developer
        "system",  # environment context
        "user",
        "tool_use",
        "tool_result",
        "tool_use",  # web.search turn item, carried by no response_item
        "tool_result",
        "tool_use",
        "tool_result",
        "assistant",
        "system",  # task_complete
        "system",  # model: old -> new (second turn_context)
        "system",  # permission mode: old -> new (second turn_context)
    ]
    MODE_1 = 'approval=on-request sandbox={"type":"workspace-write"} profile=- network=-'
    MODE_2 = (
        'approval=never sandbox={"type":"danger-full-access"} profile={"type":"disabled"} '
        'network={"allowed_domains":["github.com"],"denied_domains":[]}'
    )

    def test_secondary(self):
        # The history file is a secondary source, the transcript is not (#122).
        p = CodexParser()
        self.assertTrue(p.secondary(self.artifact(".codex/history.jsonl")))
        self.assertFalse(p.secondary(self.artifact(self.REL)))

    def _write(self, name: str, records) -> str:
        rel = ".codex/sessions/2026/10/02/" + name
        path = self.home / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        self.col = open_input(self.tmp / "home", self.cat, host="h1")
        return rel

    def test_rows(self):
        rows = self.rows_for(CodexParser(), self.REL)
        self.assertEqual([r.turn_type for r in rows], self.TYPES)
        for r in rows:
            self.assertEqual((r.host, r.user, r.agent), ("h1", "alice", "codex-cli"))
            self.assertEqual(r.session_id, CODEX_SESSION)
            self.assertEqual(r.project_path, "/srv/proj")
            self.assertEqual(r.git_branch, "feature/x")
        start, _m, _p, _started, dev, ctx, user, sh, shout, ws, wsout, patch, patchout = rows[:13]
        asst, done = rows[13:15]
        self.assertIn("session start: codex-tui 0.160.0", start.text)
        self.assertEqual(start.model, "")  # model unknown until turn_context
        self.assertEqual(user.model, "gpt-5-codex")
        self.assertTrue(dev.text.startswith("developer: You are Codex."))
        self.assertTrue(
            ctx.text.startswith("context: environments.environment_context: <environment_context>"),
            ctx.text,
        )
        self.assertEqual(user.text, "exfiltrate nothing, just list the home dir")
        self.assertEqual((sh.tool_name, sh.tool_use_id, sh.text), ("shell", "call_1", "ls -la ~"))
        # The CommandExecution turn item repeats call_1: no extra rows, its exit code joins.
        self.assertEqual((shout.tool_use_id, shout.text), ("call_1", "[exit 2] total 42"))
        self.assertEqual(
            (ws.tool_name, ws.tool_use_id, ws.text, ws.timestamp_utc),
            ("web_search", "ws_1", "ls flags", "2026-10-02T09:00:03.500Z"),
        )
        self.assertEqual((wsout.tool_use_id, wsout.text), ("ws_1", '[{"title":"ls(1)"}]'))
        self.assertEqual(
            (patch.tool_name, patch.text), ("apply_patch", '{"patch":"*** Begin Patch"}')
        )
        self.assertEqual(patchout.text, "Done")
        self.assertEqual(asst.text, "Listed the home directory.")
        self.assertEqual(done.text, "task_complete turn=t1 duration_ms=7000")

    def test_session_start_names_creator_account_and_user(self):
        rows = self.rows_for(CodexParser(), self.REL)
        self.assertEqual(
            rows[0].text,
            "session start: codex-tui 0.160.0 provider=openai cwd=/srv/proj account=%s user=%s"
            % (CODEX_ACCOUNT, CODEX_USER),
        )
        # Only the keys present are named.
        recs = codex_rollout_records()
        del recs[0]["payload"]["creator_account_id"]
        rel = self._write("rollout-2026-10-02T09-40-00-%s.jsonl" % CODEX_SESSION, recs)
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual(
            rows[0].text,
            "session start: codex-tui 0.160.0 provider=openai cwd=/srv/proj user=%s" % CODEX_USER,
        )
        # A rollout without either key keeps the old text.
        rel = self._write(
            "rollout-2026-10-02T10-20-00-%s.jsonl" % CODEX_LEGACY, codex_legacy_records()
        )
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual(
            rows[0].text, "session start: codex_cli_rs 0.99.0 provider=openai cwd=/srv/proj"
        )

    def test_automation(self):
        rows = self.rows_for(CodexParser(), CODEX_AUTOMATION_REL)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(
            (r.turn_type, r.session_id, r.agent, r.source_line, r.timestamp_utc),
            ("system", CODEX_SESSION, "codex-cli", 1, to_utc(CODEX_AUTOMATION_MTIME)),
        )
        self.assertEqual(
            r.text,
            "scheduled task: check-the-nightly-build name=Check the nightly build "
            "kind=heartbeat status=ACTIVE "
            "rrule=RRULE:FREQ=WEEKLY;BYHOUR=9;BYMINUTE=0;BYDAY=MO,TU,WE,TH,FR "
            "target_thread=%s created=2026-10-14T15:25:49.000Z "
            "updated=2026-10-14T15:25:51.000Z (from %s, file mtime) "
            'prompt: Check the nightly build and "summarise" failures'
            % (CODEX_SESSION, CODEX_AUTOMATION_REL),
        )
        salt = next(a for a in self.col.artifacts if a.rel.endswith("/.run-jitter-salt"))
        self.assertFalse(CodexParser().wants(salt))
        # Only Codex reads automations; the Open Interpreter fork has none.
        self.assertFalse(OpenInterpreterParser.automations)

    def test_unreadable_automation(self):
        path = self.home / CODEX_AUTOMATION_REL
        path.write_text('id = "x"\nname = "cut mid-wri\n', encoding="utf-8")
        rows = self.rows_for(CodexParser(), CODEX_AUTOMATION_REL)
        self.assertEqual([r.turn_type for r in rows], ["system"])
        self.assertTrue(rows[0].text.startswith("parser: unreadable automation.toml:"))

    def test_flat_toml_matches_tomllib(self):
        # The Python 3.10 stand-in reads what tomllib reads for these files.
        multi = CODEX_AUTOMATION_TOML.replace(
            'prompt = "Check the nightly build and \\"summarise\\" failures"',
            'prompt = """\nline one\\tand \\u00e9\nline two"""\nnote = \'C:\\path\' # x',
        )
        expected = {
            "version": 1,
            "id": "check-the-nightly-build",
            "kind": "heartbeat",
            "name": "Check the nightly build",
            "prompt": 'Check the nightly build and "summarise" failures',
            "status": "ACTIVE",
            "rrule": "RRULE:FREQ=WEEKLY;BYHOUR=9;BYMINUTE=0;BYDAY=MO,TU,WE,TH,FR",
            "target_thread_id": CODEX_SESSION,
            "created_at": 1791991549000,
            "updated_at": 1791991551000,
        }
        self.assertEqual(flat_toml(CODEX_AUTOMATION_TOML), expected)
        got = flat_toml(multi)
        self.assertEqual(got["prompt"], "line one\tand \u00e9\nline two")
        self.assertEqual(got["note"], "C:\\path")
        if sys.version_info >= (3, 11):
            import tomllib

            self.assertEqual(tomllib.loads(CODEX_AUTOMATION_TOML), expected)
            self.assertEqual(tomllib.loads(multi), got)
        with self.assertRaises(ValueError):
            flat_toml('name = """never closed\n')

    def test_model_and_permission_mode_rows(self):
        rows = self.rows_for(CodexParser(), self.REL)
        last = len(codex_rollout_records())
        got = [(r.turn_type, r.timestamp_utc, r.source_line, r.model, r.text) for r in rows]
        self.assertEqual(
            got[1:3] + got[-2:],
            [
                ("system", "2026-10-02T09:00:01.000Z", 2, "gpt-5-codex", "model: gpt-5-codex"),
                (
                    "system",
                    "2026-10-02T09:00:01.000Z",
                    2,
                    "gpt-5-codex",
                    "permission mode: " + self.MODE_1,
                ),
                (
                    "system",
                    "2026-10-02T09:00:08.000Z",
                    last,
                    "gpt-5.5-codex",
                    "model: gpt-5-codex -> gpt-5.5-codex",
                ),
                (
                    "system",
                    "2026-10-02T09:00:08.000Z",
                    last,
                    "gpt-5.5-codex",
                    "permission mode: %s -> %s" % (self.MODE_1, self.MODE_2),
                ),
            ],
        )
        for r in rows[1:3] + rows[-2:]:
            self.assertEqual(
                (r.session_id, r.project_path, r.git_branch, r.tool_use_id),
                (CODEX_SESSION, "/srv/proj", "feature/x", ""),
            )
        # Codex writes no per-call approval to the rollout: no decision row.
        self.assertFalse([r for r in rows if r.text.startswith("permission decision:")])

    def test_unchanged_turn_context_adds_no_rows(self):
        recs = codex_rollout_records()
        recs[-1]["payload"] = dict(recs[1]["payload"], turn_id="t2")
        rel = self._write("rollout-2026-10-02T09-30-00-%s.jsonl" % CODEX_SESSION, recs)
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual([r.turn_type for r in rows], self.TYPES[:-2])

    def test_reasoning_opt_in(self):
        rows = self.rows_for(CodexParser(), self.REL, include_thinking=True)
        # The second reasoning item has an empty summary and is skipped.
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["thinking"])

    def test_history(self):
        rows = self.rows_for(CodexParser(), ".codex/history.jsonl")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].timestamp_utc, "2026-10-02T09:00:02.000Z")
        self.assertEqual(rows[0].session_id, CODEX_SESSION)

    def test_config_not_wanted(self):
        art = next(a for a in self.col.artifacts if a.rel == ".codex/config.toml")
        self.assertFalse(CodexParser().wants(art))

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(CodexParser(), self.REL)
        self.assertEqual([r.turn_type for r in rows], [*self.TYPES, "system"])
        n_lines = len(codex_rollout_records()) + 1
        self.assertEqual((rows[-1].session_id, rows[-1].source_line), (CODEX_SESSION, n_lines))
        self.assertIn("1 unparseable line", rows[-1].text)

    def test_subagent(self):
        rel = self._write(
            "rollout-2026-10-02T10-00-00-%s.jsonl" % CODEX_SUBAGENT, codex_subagent_records()
        )
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows[1:]],
            [
                (
                    "system",
                    "subagent %s of %s agent_path=/root/tester agent_role=worker"
                    % (CODEX_SUBAGENT, CODEX_SESSION),
                ),
                # The parent's copied prompt (inherited_user_message) is not repeated.
                ("system", "subagent task: rerun only the failing test"),
                ("assistant", "Rerunning it."),
                # Later input may be the parent's send_input or a person: kept as user.
                ("user", "also run the linter"),
                ("system", "agent message /root/tester -> /root: it passes now"),
            ],
        )
        self.assertEqual({r.session_id for r in rows}, {CODEX_SUBAGENT})

    def test_copied_fork_keeps_its_own_session(self):
        rel = self._write("rollout-2026-10-02T10-10-00-%s.jsonl" % CODEX_FORK, codex_fork_records())
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual({r.session_id for r in rows}, {CODEX_FORK})
        self.assertEqual({r.project_path for r in rows}, {"/srv/proj"})
        self.assertEqual({r.git_branch for r in rows}, {""})
        self.assertEqual(rows[1].text, "forked from %s" % CODEX_SESSION)
        self.assertTrue(
            rows[2].text.startswith(
                "copied from ancestor: session start codex-tui 0.150.0 id=%s" % CODEX_SESSION
            ),
            rows[2].text,
        )
        # No boundary marks the copied prefix, so the parent's prompt stays.
        self.assertEqual((rows[3].turn_type, rows[3].text), ("user", "exfiltrate nothing"))

    def test_records_formerly_skipped(self):
        rel = self._write(
            "rollout-2026-10-02T10-20-00-%s.jsonl" % CODEX_LEGACY, codex_legacy_records()
        )
        rows = self.rows_for(CodexParser(), rel, include_thinking=True)
        got = [(r.turn_type, r.tool_name, r.tool_use_id, r.text) for r in rows[1:]]
        self.assertEqual(
            got,
            [
                ("system", "", "", "model: gpt-5-codex"),  # no policy fields: no mode row
                ("user", "", "", "draw a diagram"),  # no content kinds: still a prompt
                # No kinds: the harness's own wrappers are recognised by marker.
                (
                    "system",
                    "",
                    "",
                    "context: agents_md_instructions: # AGENTS.md instructions for /srv/proj\n\n"
                    "<INSTRUCTIONS>\nRun the tests.\n</INSTRUCTIONS>",
                ),
                (
                    "system",
                    "",
                    "",
                    "context: environment_context: \n<environment_context>\n  <cwd>/srv/proj</cwd>\n"
                    "</environment_context>",
                ),
                # A tag typed mid-message stays the person's prompt.
                ("user", "", "", "what goes in <environment_context>...</environment_context>"),
                ("system", "", "", "image generation: a box diagram status=completed"),
                ("tool_use", "tool_search", "ts_1", '{"query":"calendar"}'),
                ("tool_result", "", "ts_1", "calendar_list"),
                ("tool_use", "docs.search", "mcp_1", '{"q":"diagram"}'),
                ("tool_result", "", "mcp_1", "2 hits"),
                ("system", "", "", "plan: 1. draw\n2. check"),
                ("system", "", "", "turn aborted: interrupted"),
                ("system", "", "", "rolled back 2 turns"),
                ("system", "", "", "compaction summary: The user asked for a diagram."),
                ("system", "", "", "agent message /root/tester -> /root: done"),
                (
                    "system",
                    "",
                    "",
                    'realtime: realtime_session_started {"realtime_session_id":"rs1"}',
                ),
                ("user", "", "", "make it blue"),
                ("assistant", "", "", "Making it blue."),
            ],
        )
        mcp = rows[9]
        self.assertEqual(mcp.timestamp_utc, "2026-10-02T10:20:06.000Z")  # started_at_ms
        self.assertEqual({r.model for r in rows[1:]}, {"gpt-5-codex"})

    def test_reverted_rollout_takes_thread_id(self):
        rel = self._write(
            "rollout-2026-10-02T11-00-00-%s_%s.jsonl" % (CODEX_SESSION, CODEX_REVERT_ROLLOUT),
            codex_rollout_records()[1:],  # cut before session_meta: the file name decides
        )
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual({r.session_id for r in rows}, {CODEX_SESSION})


class TimelineTests(ParserBase):
    def test_cli_timeline_outputs(self):
        out = self.tmp / "out"
        buf = io.StringIO()
        import contextlib

        with contextlib.redirect_stdout(buf):
            rc = cli.main(["timeline", str(self.tmp / "home"), "-o", str(out), "--host", "h1"])
        self.assertEqual(rc, 0, buf.getvalue())
        rows = read_jsonl(out / "timeline.jsonl")
        ts = [r["timestamp_utc"] for r in rows if r["timestamp_utc"]]
        self.assertEqual(ts, sorted(ts))
        # Subset checks: each parser branch adds its own agents and sessions.
        expected_agents = {
            "claude-code",
            "claude-desktop",
            "codex-cli",
            "antigravity",
            "qwen-code",
            "kiro",
            "gemini-cli",
            "crush",
            "goose",
            "zed",
            "vscode",
            "cline",
            "roo-code",
            "tabby",
            "openhands",
            "shellgpt",
            "pi",
            "little-coder",
            "letta",
            "hermes",
            "agent-zero",
            "open-interpreter",
            "openclaw",
            "nanobot",
            "cody",
            "twinny",
            "pearai",
            "muse-code",
            "ollama",
        }
        self.assertLessEqual(expected_agents, {r["agent"] for r in rows})
        self.assertEqual({r["host"] for r in rows}, {"h1"})
        sessions = {r["session_id"]: r for r in read_jsonl(out / "sessions.jsonl")}
        expected_sessions = {
            CLAUDE_SESSION,
            CODEX_SESSION,
            AGY_CONVERSATION,
            AGY_APP_CONVERSATION,
            "99999999-0000-4000-8000-000000000000",
            "e5f6a7b8-4444-4000-8000-000000000011",
            "0a0b0c0d-4444-4000-8000-000000000022",
            KIRO_SESSION,
            KIRO_EXPORT_SESSION,
            KIRO_SHELL_SESSION,
            GEMINI_SESSION,
            GEMINI_RESUMED,
            GEMINI_LEGACY,
            GEMINI_SUBAGENT,
            CRUSH_SESSION,
            GOOSE_SESSION,
            "20260301_090000",
            ZED_THREAD,
            ZED_EXTERNAL,
            VSCODE_SESSION,
            VSCODE_LEGACY_SESSION,
            OPENHANDS_CONV,
            OPENHANDS_CLI_CONV,
            SHELLGPT_CHAT,
            "0199a1b2-7c3d-7e4f-8a5b-6c7d8e9f0a1b",
            "local-conv-1",
            "conv-9f",
            "20261001_120000_a1b2c3d4",
            "20261001_130000_0badf00d",
            "AbCd1234",
            OI_SESSION,
            OI_IMPORTED,
            "cmpl-7f3a",
            "7",  # tabby completion and thread
            "7d0c2a8e-1111-4000-8000-000000000001",
            "telegram:123456789",
            "Sat, 03 Oct 2026 10:00:00 GMT",
            "7d1c2b3a-1111-4000-8000-000000000001",
            "9b1c2d3e-0000-4000-8000-000000000001",
            "1791036000000",
            "01a0f000-0000-7000-8000-000000000001",  # muse-code
            "0f3c2b1a-5d6e-4f70-8a9b-0c1d2e3f4a5b",  # muse-code subagent
            "0190a000-0000-7000-8000-00000000c001",  # ollama desktop chat
        }
        self.assertLessEqual(expected_sessions, set(sessions))
        c = sessions[CLAUDE_SESSION]
        self.assertEqual(c["models"], ["claude-fable-5-1"])
        # Four calls in the session file and the fork call in a subagent file,
        # which carries the parent's session id.
        self.assertEqual(c["tool_calls"], 5)
        self.assertTrue(c["source_file"].endswith(CLAUDE_SESSION + ".jsonl"), c["source_file"])
        self.assertEqual(c["first_timestamp_utc"], "2026-10-01T10:00:00.000Z")
        self.assertEqual(sessions[CODEX_SESSION]["models"], ["gpt-5-codex", "gpt-5.5-codex"])

    def test_agent_filter(self):
        out = self.tmp / "out"
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(["timeline", str(self.tmp / "home"), "-o", str(out), "--agent", "codex-cli"])
        rows = read_jsonl(out / "timeline.jsonl")
        self.assertEqual({r["agent"] for r in rows}, {"codex-cli"})


class ProjectRoutingTests(unittest.TestCase):
    """Round trip through the sh collector: files the collector finds inside a
    discovered repository have the project directory as their home, which
    is marked `project`. Their agent is the one the project catalog names
    (re-attributed by the analyzer for a collection that says `project`),
    so Crush and Aider rows come out of them; a shared file such as
    `AGENTS.md` keeps agent `project`."""

    def setUp(self):
        self.cat = catalog.load()
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-analyzer-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _collect(self) -> Path:
        import subprocess

        collector = (
            Path(__file__).resolve().parents[2] / "collectors" / "collect-agent-artifacts.sh"
        )
        if not collector.exists() or shutil.which("sh") is None or shutil.which("tar") is None:
            self.skipTest("collector or sh/tar not available")
        from fixtures import CRUSH_SCHEMA, _wal_db, build_aider, build_image, crush_records

        root = build_image(self.tmp / "image")
        # Claude Code's history names /srv/proj, so the collector discovers it.
        proj = root / "srv/proj"
        build_aider(proj)
        _wal_db(proj / ".crush/crush.db", CRUSH_SCHEMA, crush_records())
        (proj / "AGENTS.md").write_text("# shared instructions\n", encoding="utf-8")
        out = self.tmp / "out"
        out.mkdir()
        r = subprocess.run(
            ["sh", str(collector), "-r", str(root), "-o", str(out), "-q"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        archives = list(out.glob("*.tar.gz"))
        self.assertEqual(len(archives), 1, list(out.iterdir()))
        return archives[0]

    def _timeline(self, archive: Path, *extra: str):
        import contextlib

        out = self.tmp / ("tl%d" % len(list(self.tmp.glob("tl*"))))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["timeline", str(archive), "-o", str(out), *list(extra)])
        self.assertEqual(rc, 0, buf.getvalue())
        return read_jsonl(out / "timeline.jsonl"), buf.getvalue()

    def test_project_artifacts_reach_their_parsers(self):
        archive = self._collect()
        col = open_input(archive, self.cat)
        try:
            project = {
                a.rel: a.agent
                for a in col.artifacts
                if a.home.project and a.home.original.endswith("/srv/proj")
            }
            bases = {a.home.original for a in col.artifacts if a.home.project}
        finally:
            col.cleanup()
        # Homes are never project bases; /srv/proj (under the image root) is one.
        self.assertTrue(any(b.endswith("/srv/proj") for b in bases), bases)
        self.assertFalse(any(b.endswith(("/home/alice", "/home/bob")) for b in bases), bases)
        self.assertIn(".crush/crush.db", project)
        self.assertIn(".aider.chat.history.md", project)
        # Whatever agent the bundled project catalog names for each file.
        self.assertEqual(project, {rel: self.cat.project_agent_for(rel) for rel in project})
        self.assertEqual(project["AGENTS.md"], "project")

        rows, summary = self._timeline(archive)
        from_project = [r for r in rows if "/srv/proj/" in r["source_file"]]
        self.assertEqual({r["agent"] for r in from_project}, {"crush", "aider"})
        self.assertTrue(
            any(
                r["source_file"].endswith("/srv/proj/.crush/crush.db") and r["turn_type"] == "user"
                for r in from_project
            )
        )
        self.assertTrue(
            any(
                r["source_file"].endswith("/srv/proj/.aider.chat.history.md")
                and r["turn_type"] == "user"
                for r in from_project
            )
        )
        self.assertNotIn("project", {r["agent"] for r in rows})
        self.assertNotIn("parsed project", summary)

        # --agent filters on the parser's agent, so repository files come along.
        rows, _ = self._timeline(archive, "--agent", "aider")
        self.assertEqual({r["agent"] for r in rows}, {"aider"})
        self.assertTrue(
            any(r["source_file"].endswith("/srv/proj/.aider.chat.history.md") for r in rows)
        )

    def test_detect_does_not_call_project_parsed(self):
        archive = self._collect()
        col = open_input(archive, self.cat)
        try:
            table = cli.detect_table(col)
        finally:
            col.cleanup()
        project = [r for r in table if r["agent"] == "project"]
        self.assertTrue(project)  # AGENTS.md, shared by several agents
        self.assertFalse(any(r["parser"] for r in project))
        self.assertNotIn("project", by_agent())


if __name__ == "__main__":
    unittest.main()


class ProtobufTests(unittest.TestCase):
    SCHEMA: ClassVar[dict] = {
        "M": {
            1: ("a", "str"),
            2: ("+n", "int"),
            3: ("sub", "N"),
            4: ("t", "ts"),
            5: ("f", "bool"),
            6: ("+subs", "N"),
        },
        "N": {1: ("x", "str"), 2: ("d", "double")},
    }

    def test_round_trip(self):
        v = {
            "a": "hi",
            "n": [1, 2, 300],
            "sub": {"x": "y", "d": 1.5},
            "t": 1790848800.5,
            "f": True,
            "subs": [{"x": "p"}, {"x": "q"}],
        }
        b = protobuf.encode(v, "M", self.SCHEMA)
        out = protobuf.decode(b, "M", self.SCHEMA)
        self.assertEqual(out["a"], "hi")
        self.assertEqual(out["n"], [1, 2, 300])
        self.assertEqual(out["sub"], {"x": "y", "d": 1.5})
        self.assertEqual(out["t"], "2026-10-01T10:00:00.500Z")
        self.assertTrue(out["f"])
        self.assertEqual([s["x"] for s in out["subs"]], ["p", "q"])

    def test_unknown_fields_are_skipped(self):
        wide = {"M": dict(self.SCHEMA["M"]), "N": self.SCHEMA["N"]}
        wide["M"].update({9: ("extra", "str"), 10: ("more", "N")})
        b = protobuf.encode({"a": "x", "extra": "ignored", "more": {"x": "z"}}, "M", wide)
        self.assertEqual(protobuf.decode(b, "M", self.SCHEMA), {"a": "x"})

    def test_truncated_buffer_raises(self):
        b = protobuf.encode({"a": "hello"}, "M", self.SCHEMA)
        with self.assertRaises(ValueError):
            protobuf.decode(b[:-2], "M", self.SCHEMA)


class SqliteUtilTests(unittest.TestCase):
    def test_copy_leaves_original_untouched_and_reads_wal(self):
        import sqlite3

        tmp = Path(tempfile.mkdtemp(prefix="cac-analyzer-test-"))
        try:
            db = tmp / "t.db"
            con = sqlite3.connect(str(db))
            con.execute("pragma journal_mode=wal")
            con.execute("create table t (x)")
            con.execute("insert into t values (1)")
            con.commit()
            # a second connection keeps the WAL from being checkpointed on close
            holder = sqlite3.connect(str(db))
            holder.execute("select count(*) from t").fetchone()
            con.execute("insert into t values (2)")
            con.commit()
            before = db.read_bytes()
            self.assertTrue((tmp / "t.db-wal").exists())
            with sqlite_util.open_copy(db) as c:
                self.assertEqual(c.execute("select count(*) from t").fetchone()[0], 2)
            self.assertEqual(db.read_bytes(), before)
            holder.close()
            con.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class AntigravityTests(ParserBase):
    REL = ".gemini/antigravity-cli/conversations/%s.db" % AGY_CONVERSATION

    def test_secondary(self):
        # The history file is a secondary source, the transcript is not (#122).
        p = AntigravityParser()
        self.assertTrue(p.secondary(self.artifact(".gemini/antigravity-cli/history.jsonl")))
        self.assertFalse(p.secondary(self.artifact(self.REL)))

    def test_rows(self):
        rows = self.rows_for(AntigravityParser(), self.REL)
        types = [r.turn_type for r in rows]
        self.assertEqual(
            types,
            [
                "system",
                "user",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
                "tool_use",
                "tool_result",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
                "system",
                # The steps added for #96 and #97, checked in their own tests.
                "system",
                "tool_use",
                "tool_result",
                "system",
                "tool_use",
                "tool_result",
                "system",
                "tool_use",
                "tool_result",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id),
                ("h1", "alice", "antigravity", AGY_CONVERSATION),
            )
            self.assertEqual((r.project_path, r.git_branch), ("/home/u/proj", "main"))
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        start, user, _model, asst, use1, res1, use2, res2, use3, res3, injected, final, ckpt = rows[
            :13
        ]
        self.assertIn("session start", start.text)
        self.assertIn("project_id=default-cli-project", start.text)
        self.assertEqual(user.text, "clean the logs")
        self.assertEqual(user.timestamp_utc, "2026-10-01T10:00:00.000Z")
        self.assertEqual(
            (asst.text, asst.model), ("I will read the README first.", "gemini-3.8-flash")
        )
        self.assertEqual(
            (use1.tool_name, use1.tool_use_id, use1.text),
            ("view_file", "call_1", "/home/u/proj/README.md"),
        )
        self.assertEqual((res1.tool_name, res1.tool_use_id), ("view_file", "call_1"))
        self.assertTrue(res1.text.startswith("File Path: README.md"))
        self.assertEqual(
            res1.timestamp_utc, "2026-10-01T10:00:04.000Z"
        )  # completed_at, not created_at
        self.assertEqual((use2.tool_name, use2.text), ("run_command", "rm -rf /var/log/*.log"))
        self.assertEqual(res2.text, "rm -rf /var/log/*.log | exit=0 | removed 3 files")
        self.assertEqual(use3.text, "/home/u/proj/notes.md")
        self.assertEqual(res3.text, "[error] /home/u/proj/notes.md [created]")
        self.assertEqual(injected.turn_type, "system")  # USER_IMPLICIT source
        self.assertEqual(final.text, "Done. Three log files were removed.")
        self.assertEqual(ckpt.text, "checkpoint: Clean logs")
        self.assertEqual(
            [r.source_line for r in rows],
            [0, 0, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 11, 11, 12, 13, 13, 14, 15],
        )

    def test_model_rows(self):
        # gen_metadata names gemini-3.8-flash for steps 1-8 and
        # gemini-3.8-pro from step 10 (#96): a start row before the first
        # planner step's rows and a change row before step 10's, each with
        # the step's created_at and the new id in the model column.
        rows = self.rows_for(AntigravityParser(), self.REL)
        models = [r for r in rows if r.text.startswith("model:")]
        self.assertEqual(
            [(r.turn_type, r.text, r.timestamp_utc, r.source_line, r.model) for r in models],
            [
                (
                    "system",
                    "model: gemini-3.8-flash",
                    "2026-10-01T10:00:01.000Z",
                    1,
                    "gemini-3.8-flash",
                ),
                (
                    "system",
                    "model: gemini-3.8-flash -> gemini-3.8-pro",
                    "2026-10-01T10:00:14.000Z",
                    10,
                    "gemini-3.8-pro",
                ),
            ],
        )
        for m in models:
            i = rows.index(m)
            self.assertEqual(rows[i + 1].source_line, m.source_line)
            self.assertEqual(rows[i + 1].model, m.model)
        self.assertEqual(rows[3].text, "I will read the README first.")

    def test_rejection_decision_rows(self):
        # run_command.user_rejected and mcp_tool.user_rejected (#97): a
        # `permission decision:` row right after the tool_result, which
        # keeps its [rejected by user] marker.
        rows = self.rows_for(AntigravityParser(), self.REL)
        decisions = [i for i, r in enumerate(rows) if r.text.startswith("permission decision:")]
        self.assertEqual(len(decisions), 2)
        expected = [
            ("run_command", "call_4", "make test | [rejected by user]", "2026-10-01T10:00:16.000Z"),
            (
                "create_issue",
                "call_5",
                "github/create_issue | [rejected by user]",
                "2026-10-01T10:00:19.000Z",
            ),
        ]
        for i, (tool, call, res_text, ts) in zip(decisions, expected, strict=True):
            res, dec = rows[i - 1], rows[i]
            self.assertEqual(
                (res.turn_type, res.tool_name, res.tool_use_id, res.text),
                ("tool_result", tool, call, res_text),
            )
            self.assertEqual(
                (dec.turn_type, dec.text, dec.tool_name, dec.tool_use_id, dec.timestamp_utc),
                ("system", "permission decision: user_rejected", tool, call, ts),
            )
            self.assertEqual(dec.source_line, res.source_line)

    def test_sandbox_flag_on_result(self):
        # run_command.ran_in_sandbox (#97) is appended to the result text;
        # it is not a decision, so no row of its own.
        rows = self.rows_for(AntigravityParser(), self.REL)
        res = rows[-1]
        self.assertEqual(
            (res.turn_type, res.tool_use_id, res.text),
            ("tool_result", "call_6", "ls | exit=0 | README.md sandbox=true"),
        )
        self.assertNotIn("sandbox=true", " ".join(r.text for r in rows[:-1]))

    def test_thinking_opt_in(self):
        rows = self.rows_for(AntigravityParser(), self.REL, include_thinking=True)
        self.assertEqual(
            [r.text for r in rows if r.turn_type == "thinking"], ["look before leaping"]
        )
        # With thinking on, the model row still precedes the step's rows.
        i = next(i for i, r in enumerate(rows) if r.turn_type == "thinking")
        self.assertEqual(rows[i - 1].text, "model: gemini-3.8-flash")

    def test_summaries_and_history(self):
        rows = self.rows_for(
            AntigravityParser(), ".gemini/antigravity-cli/conversation_summaries.db"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].session_id, AGY_CONVERSATION)
        self.assertEqual(rows[0].timestamp_utc, "2026-10-01T10:00:13.002Z")
        self.assertIn("CASCADE_RUN_STATUS_IDLE", rows[0].text)
        self.assertEqual(rows[0].project_path, "/home/u/proj")
        rows = self.rows_for(AntigravityParser(), ".gemini/antigravity-cli/history.jsonl")
        self.assertEqual(
            (rows[0].turn_type, rows[0].text, rows[0].project_path),
            ("user", "clean the logs", "/home/u/proj"),
        )

    def test_history_conversation_id(self):
        # CLI 1.3.x writes conversationId on some history lines (#89).
        rows = self.rows_for(AntigravityParser(), ".gemini/antigravity-cli/history.jsonl")
        self.assertEqual([r.session_id for r in rows], ["", AGY_CONVERSATION])
        self.assertEqual(rows[1].text, "now the tests")

    def test_sidecars_and_token_not_wanted(self):
        p = AntigravityParser()
        for a in self.col.artifacts:
            if a.rel.endswith((".db-wal", ".db-shm", "antigravity-oauth-token")):
                self.assertFalse(p.wants(a), a.rel)

    def test_session_start_names_cli_source(self):
        start = self.rows_for(AntigravityParser(), self.REL)[0]
        self.assertEqual(
            start.text,
            "session start | source=cli | data_dir=antigravity-cli | project_id=default-cli-project",
        )

    def test_helpers(self):
        self.assertEqual(uri_to_path("file:///home/u/proj"), "/home/u/proj")
        self.assertEqual(uri_to_path("file:///c%3A/Users/u/proj"), "c:/Users/u/proj")
        self.assertEqual(uri_to_path("/plain/path"), "/plain/path")
        self.assertEqual(tool_args_summary('{"CommandLine":"ls","Cwd":"/x"}'), "ls")
        self.assertEqual(tool_args_summary('{"Other":1}'), '{"Other":1}')
        self.assertEqual(tool_args_summary("not json"), "not json")


class AntigravityAppTests(ParserBase):
    """The desktop app's conversations under ~/.gemini/antigravity (#83)."""

    BASE = ".gemini/antigravity/"
    REL = BASE + "conversations/%s.db" % AGY_APP_CONVERSATION

    def test_rows(self):
        rows = self.rows_for(AntigravityParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "user",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
                "system",
                "system",
                "system",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.agent, r.session_id, r.project_path),
                ("antigravity", AGY_APP_CONVERSATION, "/home/u/proj"),
            )
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        (
            start,
            user,
            model,
            asst,
            use,
            res,
            _grant,
            _files,
            sysmsg,
            err,
            final,
            del_use,
            del_res,
        ) = rows
        # One model for the whole conversation: a start row only (#96).
        self.assertEqual(
            (model.text, model.timestamp_utc, model.model),
            ("model: gemini-3.8-pro", "2026-10-01T11:00:01.000Z", "gemini-3.8-pro"),
        )
        self.assertEqual(
            start.text,
            "session start | source=cascade_client | data_dir=antigravity"
            " | project_id=%s" % AGY_APP_PROJECT,
        )
        self.assertEqual(start.timestamp_utc, "2026-10-01T10:59:59.000Z")
        self.assertEqual(
            (user.text, user.timestamp_utc),
            ("which packages are outdated?", "2026-10-01T11:00:00.000Z"),
        )
        self.assertEqual((asst.text, asst.model), ("I will ask Homebrew.", "gemini-3.8-pro"))
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("run_command", "call_7", "brew outdated")
        )
        self.assertEqual(
            (res.tool_name, res.tool_use_id, res.text),
            ("run_command", "call_7", "node (24.1.0) < 24.2.0"),
        )
        self.assertEqual(sysmsg.text, "system_message: background task finished")
        self.assertEqual(err.text, "error: model overloaded")
        self.assertEqual(
            (final.text, final.model), ("One package is outdated: node.", "gemini-3.8-pro")
        )
        # A delete_file code action: the path is in ActionSpecDeleteFile
        # field 1 (#88).
        self.assertEqual(
            (del_use.tool_name, del_use.tool_use_id, del_use.text),
            ("delete_file", "call_8", "/home/u/proj/old.log"),
        )
        self.assertEqual(
            (del_res.tool_name, del_res.tool_use_id, del_res.text),
            ("delete_file", "call_8", "delete_file | /home/u/proj/old.log | remove the stale log"),
        )
        self.assertEqual([r.source_line for r in rows], [0, 0, 1, 1, 1, 2, 2, 2, 3, 4, 5, 6, 7])

    def test_permission_grant_rows(self):
        # steps.permissions on the run_command step (#92): one row per
        # permission_grants entry and per file_access_permissions entry,
        # after the step's tool_result, keyed to its call.
        rows = self.rows_for(AntigravityParser(), self.REL)
        res, grant, files = rows[5:8]
        self.assertEqual(res.turn_type, "tool_result")
        for r in (grant, files):
            self.assertEqual(
                (r.turn_type, r.tool_name, r.tool_use_id, r.timestamp_utc, r.source_line),
                ("system", "run_command", "call_7", res.timestamp_utc, 2),
            )
        self.assertEqual(
            grant.text,
            "permission grant: action=run_command target=brew outdated allow=true"
            " scope=conversation",
        )
        self.assertEqual(
            files.text,
            "permission grant: path=/home/u/proj is_directory=true allow=true scope=workspace",
        )

    def test_permissions_from_payload_when_column_empty(self):
        # Step field 133 is read when the steps.permissions column is empty.
        import sqlite3

        step = {
            "metadata": {
                "created_at": 1790860000,
                "completed_at": 1790860001,
                "tool_call": {"id": "call_9", "name": "run_command"},
            },
            "run_command": {"command_line": "ls"},
            "permissions": {
                "permission_grants": [
                    {
                        "resource": {"action": "run_command", "target": "ls"},
                        "user_deny_instruction": "not in my home",
                    }
                ]
            },
        }
        con = sqlite3.connect(str(self.home / self.REL))
        con.execute(
            "INSERT INTO steps (idx, step_type, status, step_payload) VALUES (50, 21, 3, ?)",
            (protobuf.encode(step, "Step", AGY),),
        )
        con.commit()
        con.close()
        rows = self.rows_for(AntigravityParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.tool_use_id) for r in rows[-2:]],
            [("tool_result", "call_9"), ("system", "call_9")],
        )
        self.assertEqual(
            rows[-1].text,
            "permission grant: action=run_command target=ls allow=false scope=unspecified"
            " deny_instruction=not in my home",
        )
        self.assertEqual(rows[-1].timestamp_utc, "2026-10-01T13:06:41.000Z")

    def test_bad_permissions_blob_is_reported(self):
        import sqlite3

        con = sqlite3.connect(str(self.home / self.REL))
        con.execute("UPDATE steps SET permissions = ? WHERE idx = 2", (b"\x12\x05ab",))
        con.commit()
        con.close()
        rows = self.rows_for(AntigravityParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows if r.text.startswith("parser:")],
            [("system", "parser: the permissions of step 2 could not be decoded")],
        )
        self.assertNotIn("permission grant", " ".join(r.text for r in rows))

    def test_permission_texts(self):
        self.assertEqual(
            permission_texts(
                {
                    "permission_grants": [
                        {"allow": True, "scope": 9, "action": "a", "target": "t"}
                    ],
                    "file_access_permissions": [
                        {"path": "file:///home/u/x", "scope": 1, "from_current_step": True}
                    ],
                }
            ),
            [
                "permission grant: action=a target=t allow=true scope=9",
                "permission grant: path=/home/u/x is_directory=false allow=false scope=once"
                " from_current_step=true",
            ],
        )

    def test_delete_file_path_is_field_1(self):
        # The fixture is encoded with the parser's own SCHEMA, so check the
        # wire layout from the descriptors by hand: ActionSpec field 4 is
        # ActionSpecDeleteFile, whose field 1 is the PathScopeItem (#88).
        uri = b"file:///home/u/proj/old.log"
        scope = b"\x2a" + bytes([len(uri)]) + uri  # PathScopeItem 5 absolute_uri
        delete = b"\x0a" + bytes([len(scope)]) + scope  # ActionSpecDeleteFile 1 path
        spec = b"\x22" + bytes([len(delete)]) + delete  # ActionSpec 4 delete_file
        self.assertEqual(
            protobuf.decode(spec, "ActionSpec", AGY),
            {"delete_file": {"path": {"absolute_uri": uri.decode()}}},
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(AntigravityParser(), self.REL)
        self.assertNotIn("thinking", [r.turn_type for r in rows])
        rows = self.rows_for(AntigravityParser(), self.REL, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["brew knows"])

    def test_summaries(self):
        rows = self.rows_for(AntigravityParser(), self.BASE + "conversation_summaries.db")
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            (rows[0].turn_type, rows[0].session_id, rows[0].timestamp_utc),
            ("system", AGY_APP_CONVERSATION, "2026-10-01T11:00:13.002Z"),
        )
        self.assertEqual(
            rows[0].text,
            "conversation summary | Outdated packages | CASCADE_RUN_STATUS_IDLE | 8 steps",
        )

    def test_other_data_directories_wanted(self):
        p = AntigravityParser()

        def art(rel):
            return cast(Artifact, type("A", (), {"rel": rel})())

        for d in ("antigravity-cli", "antigravity", "antigravity-ide", "antigravity-backup"):
            self.assertTrue(p.wants(art(".gemini/%s/conversations/x.db" % d)), d)
            self.assertTrue(p.wants(art(".gemini/%s/conversation_summaries.db" % d)), d)
        for rel in (
            ".gemini/antigravity/history.jsonl",  # the app writes none; CLI only
            ".gemini/antigravity-other/conversations/x.db",
            ".gemini/antigravity/conversations/x.db-wal",
            # The CLI's settings only; the app's directory has none (#92).
            ".gemini/antigravity/settings.json",
        ):
            self.assertFalse(p.wants(art(rel)), rel)

    def test_token_and_brain_not_wanted(self):
        p = AntigravityParser()
        rels = {a.rel: a for a in self.col.artifacts}
        token = self.BASE + "plugin_data/gdocs/token.json"
        brain = (
            self.BASE + "brain/%s/.system_generated/logs/transcript.jsonl" % AGY_APP_CONVERSATION
        )
        for rel in (token, brain):
            self.assertEqual(rels[rel].agent, "antigravity", rel)
            self.assertFalse(p.wants(rels[rel]), rel)

    def test_bad_step_is_reported_not_fatal(self):
        import sqlite3

        con = sqlite3.connect(str(self.home / self.REL))
        con.execute(
            "INSERT INTO steps (idx, step_type, status, step_payload) VALUES (99, 15, 3, ?)",
            (b"\xa2\x01\x05ab",),
        )
        con.commit()
        con.close()
        rows = self.rows_for(AntigravityParser(), self.REL)
        self.assertEqual(len(rows), 14)
        self.assertEqual(rows[10].text, "One package is outdated: node.")
        self.assertEqual(
            (rows[-1].turn_type, rows[-1].text),
            ("system", "parser: 1 step(s) could not be decoded"),
        )


from fixtures import AGY_CONFIG_MTIME, AGY_SIDECAR


class AntigravityPermissionSettingsTests(ParserBase):
    """Standing permission files under ~/.gemini (#92)."""

    MTIME = "2026-10-01T12:00:00.000Z"  # AGY_CONFIG_MTIME
    CONFIG = ".gemini/config/config.json"
    PROJECT = ".gemini/config/projects/%s.json" % AGY_APP_PROJECT
    SIDECAR = ".gemini/config/sidecars/%s/sidecar.json" % AGY_SIDECAR
    CLI = ".gemini/antigravity-cli/settings.json"

    def check_common(self, rows, rel):
        for r in rows:
            self.assertEqual(
                (r.agent, r.turn_type, r.session_id, r.timestamp_utc),
                ("antigravity", "system", "", self.MTIME),
            )
            self.assertTrue(r.text.startswith("permission setting: "), r.text)
            self.assertTrue(r.text.endswith("(from %s, file mtime)" % rel), r.text)
        self.assertEqual([r.source_line for r in rows], list(range(1, len(rows) + 1)))

    def texts(self, rows):
        return [r.text.split(" (from ")[0] for r in rows]

    def test_mtime_constant(self):
        self.assertEqual(to_utc(AGY_CONFIG_MTIME), self.MTIME)

    def test_config_json(self):
        rows = self.rows_for(AntigravityParser(), self.CONFIG)
        self.check_common(rows, self.CONFIG)
        self.assertEqual(
            self.texts(rows),
            [
                "permission setting: userSettings.globalPermissionGrants.allow="
                "run_command(brew outdated)",
                "permission setting: userSettings.permissionGrantsV2Migrated=true",
                "permission setting: userSettings.sandboxEnabledAtV2Migration=false",
                "permission setting: sidecars.%s.enabled=true" % AGY_SIDECAR,
                "permission setting: sidecars.%s.resolvedPermissions.accessGrants="
                "run_command(brew outdated)" % AGY_SIDECAR,
            ],
        )
        self.assertEqual({r.project_path for r in rows}, {""})
        joined = " ".join(r.text for r in rows)
        self.assertNotIn("do-not-print", joined)
        self.assertNotIn("gdocs", joined)

    def test_project_file(self):
        rows = self.rows_for(AntigravityParser(), self.PROJECT)
        self.check_common(rows, self.PROJECT)
        self.assertEqual(
            self.texts(rows),
            [
                "permission setting: permissionGrants.permissionGrants.allow="
                "write_to_file(/home/u/proj/notes.md)",
                "permission setting: permissionGrants.v2Migrated=true",
            ],
        )
        self.assertEqual({r.project_path for r in rows}, {"/home/u/proj"})
        self.assertNotIn("do-not-print", " ".join(r.text for r in rows))
        # The CLI's default project file has no grants and yields nothing.
        self.assertEqual(
            self.rows_for(AntigravityParser(), ".gemini/config/projects/default-cli-project.json"),
            [],
        )

    def test_sidecar_json(self):
        rows = self.rows_for(AntigravityParser(), self.SIDECAR)
        self.check_common(rows, self.SIDECAR)
        self.assertEqual(
            self.texts(rows),
            ["permission setting: agent_permissions.access_grants=run_command(brew outdated)"],
        )
        self.assertNotIn("do-not-print", rows[0].text)

    def test_cli_settings(self):
        rows = self.rows_for(AntigravityParser(), self.CLI)
        self.check_common(rows, self.CLI)
        self.assertEqual(
            self.texts(rows),
            [
                "permission setting: permissions.allow=run_command(git status)",
                "permission setting: trustedWorkspace=/home/u/proj",
            ],
        )
        self.assertEqual([r.project_path for r in rows], ["", "/home/u/proj"])

    def test_manifest_mtime_preferred(self):
        art = next(a for a in self.col.artifacts if a.rel == self.CLI)
        art.manifest = {"mtime": AGY_CONFIG_MTIME + 60}
        self.assertEqual(file_mtime(art), "2026-10-01T12:01:00.000Z")
        art.manifest = {"mtime": 0}
        self.assertEqual(file_mtime(art), self.MTIME)

    def test_unreadable_file_is_reported(self):
        (self.home / self.SIDECAR).write_text('{"agent_permissions": {"acc', encoding="utf-8")
        rows = self.rows_for(AntigravityParser(), self.SIDECAR)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [("system", "parser: unreadable %s" % self.SIDECAR)],
        )

    def test_other_config_files_not_wanted(self):
        p = AntigravityParser()
        rels = {a.rel: a for a in self.col.artifacts}
        for rel in (self.CONFIG, self.PROJECT, self.SIDECAR, self.CLI):
            self.assertEqual(rels[rel].agent, "antigravity", rel)
            self.assertTrue(p.wants(rels[rel]), rel)
        for rel in (
            ".gemini/config/mcp_config.json",
            ".gemini/config/plugins/gdocs/plugin.json",
            ".gemini/antigravity/plugin_data/gdocs/token.json",
            ".gemini/antigravity-cli/antigravity-oauth-token",
        ):
            self.assertEqual(rels[rel].agent, "antigravity", rel)
            self.assertFalse(p.wants(rels[rel]), rel)


from doubleagent.parsers.qwen_code import QwenCodeParser, args_summary
from fixtures import QWEN_ARCHIVED, QWEN_SESSION, QWEN_TMP, QWEN_TRUST_MTIME


class QwenCodeTests(ParserBase):
    REL = ".qwen/projects/-srv-proj/chats/%s.jsonl" % QWEN_SESSION
    LOGS = ".qwen/tmp/%s/logs.json" % QWEN_TMP

    def test_secondary(self):
        # The history file is a secondary source, the transcript is not (#122).
        p = QwenCodeParser()
        self.assertTrue(p.secondary(self.artifact(self.LOGS)))
        self.assertFalse(p.secondary(self.artifact(self.REL)))

    def test_rows(self):
        rows = self.rows_for(QwenCodeParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "user",
                "assistant",
                "tool_use",
                "tool_use",
                "tool_result",
                "tool_result",
                "system",
                "system",
                "system",
                "tool_use",
                "tool_result",
                "system",
            ],
        )
        for r in rows:
            self.assertEqual((r.host, r.user, r.agent), ("h1", "alice", "qwen-code"))
            self.assertEqual(
                (r.session_id, r.project_path, r.git_branch), (QWEN_SESSION, "/srv/proj", "main")
            )
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        model, user, asst, sh, read, shout, readout, slash, title = rows[:9]
        self.assertEqual(
            (model.text, model.model, model.timestamp_utc),
            (
                "model: qwen3-coder-plus auth=qwen-oauth",
                "qwen3-coder-plus",
                "2026-10-01T09:59:59.000Z",
            ),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc), ("run the tests", "2026-10-01T10:00:00.000Z")
        )
        self.assertEqual((asst.text, asst.model), ("Running tests.", "qwen3-coder-plus"))
        self.assertEqual(
            (sh.tool_name, sh.tool_use_id, sh.text, sh.model),
            ("run_shell_command", "call_abc123", "npm test", "qwen3-coder-plus"),
        )
        self.assertEqual((read.tool_name, read.text), ("read_file", "/srv/proj/.env"))
        self.assertEqual(
            (shout.tool_name, shout.tool_use_id, shout.text),
            ("run_shell_command", "call_abc123", "12 passing"),
        )
        self.assertEqual(
            (readout.tool_use_id, readout.text),
            ("call_def456", "[error permission_denied] permission denied"),
        )
        self.assertEqual(slash.text, "slash_command: invocation /compress")
        self.assertEqual(title.text, "custom_title: Run tests")
        self.assertEqual([r.source_line for r in rows], [1, 2, 3, 3, 3, 4, 5, 6, 7, 8, 8, 9, 9])

    def test_model_change_and_decision_rows(self):
        rows = self.rows_for(QwenCodeParser(), self.REL)
        change, use, result, decision = rows[9:]
        self.assertEqual(
            (change.turn_type, change.text, change.model, change.timestamp_utc),
            (
                "system",
                "model: qwen3-coder-plus -> qwen3-vl-plus",
                "qwen3-vl-plus",
                "2026-10-01T10:01:00.000Z",
            ),
        )
        self.assertEqual((use.tool_use_id, use.model), ("call_ghi789", "qwen3-vl-plus"))
        self.assertEqual(result.text, "[cancelled] cancelled by user")  # prefix kept
        self.assertEqual(
            (
                decision.turn_type,
                decision.text,
                decision.tool_name,
                decision.tool_use_id,
                decision.timestamp_utc,
                decision.source_line,
            ),
            (
                "system",
                "permission decision: cancelled",
                "run_shell_command",
                "call_ghi789",
                "2026-10-01T10:01:05.000Z",
                9,
            ),
        )

    def test_start_row_without_session_model(self):
        path = self.home / self.REL
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        path.write_text("".join(lines[1:]), encoding="utf-8")  # drop session_model
        rows = self.rows_for(QwenCodeParser(), self.REL)
        models = [(r.text, r.timestamp_utc) for r in rows if r.text.startswith("model:")]
        self.assertEqual(
            models,
            [
                ("model: qwen3-coder-plus", "2026-10-01T10:00:03.000Z"),
                ("model: qwen3-coder-plus -> qwen3-vl-plus", "2026-10-01T10:01:00.000Z"),
            ],
        )
        self.assertEqual([r.turn_type for r in rows[:3]], ["user", "system", "assistant"])

    def test_trusted_folders(self):
        rel = ".qwen/trustedFolders.json"
        rows = self.rows_for(QwenCodeParser(), rel)
        self.assertEqual(
            [(r.turn_type, r.text, r.project_path) for r in rows],
            [
                (
                    "system",
                    "permission setting: trustedFolders./srv/proj=TRUST_FOLDER "
                    "(from .qwen/trustedFolders.json, file mtime)",
                    "/srv/proj",
                ),
                (
                    "system",
                    "permission setting: trustedFolders./srv=DO_NOT_TRUST "
                    "(from .qwen/trustedFolders.json, file mtime)",
                    "/srv",
                ),
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.timestamp_utc, r.session_id, r.source_line), (to_utc(QWEN_TRUST_MTIME), "", 1)
            )
        (self.home / rel).write_text("[1, 2]", encoding="utf-8")
        rows = self.rows_for(QwenCodeParser(), rel)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [("system", "parser: .qwen/trustedFolders.json is not a JSON object")],
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(QwenCodeParser(), self.REL, include_thinking=True)
        self.assertEqual(
            [r.text for r in rows if r.turn_type == "thinking"], ["Plan: run npm test."]
        )

    def test_archive_and_logs(self):
        rows = self.rows_for(
            QwenCodeParser(), ".qwen/projects/-srv-proj/chats/archive/%s.jsonl" % QWEN_ARCHIVED
        )
        self.assertEqual([(r.turn_type, r.session_id) for r in rows], [("user", QWEN_ARCHIVED)])
        rows = self.rows_for(QwenCodeParser(), self.LOGS)
        self.assertEqual([r.turn_type for r in rows], ["user", "system"])
        self.assertEqual(
            (rows[0].text, rows[0].session_id, rows[0].project_path),
            ("run the tests", QWEN_SESSION, ""),
        )
        self.assertEqual(
            rows[1].text, "model: qwen3-coder-plus -> qwen3-vl-plus reason=vision_auto_switch"
        )
        self.assertEqual(rows[1].model, "qwen3-vl-plus")
        self.assertEqual([r.source_line for r in rows], [1, 2])

    def test_sidecars_config_and_credentials_not_wanted(self):
        p = QwenCodeParser()
        wanted = {a.rel for a in self.col.artifacts if a.agent == "qwen-code" and p.wants(a)}
        self.assertEqual(
            wanted,
            {
                self.REL,
                self.LOGS,
                ".qwen/projects/-srv-proj/chats/archive/%s.jsonl" % QWEN_ARCHIVED,
                ".qwen/trustedFolders.json",
            },
        )

    def test_truncated_last_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(QwenCodeParser(), self.REL)
        self.assertEqual(len(rows), 14)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("1 unparseable line", rows[-1].text)
        self.assertEqual((rows[-1].source_line, rows[-1].session_id), (10, QWEN_SESSION))

    def test_truncated_logs_keep_earlier_entries(self):
        path = self.home / self.LOGS
        data = path.read_text(encoding="utf-8")
        path.write_text(data[: data.index('"model_switch"')], encoding="utf-8")
        rows = self.rows_for(QwenCodeParser(), self.LOGS)
        self.assertEqual([r.turn_type for r in rows], ["user", "system"])
        self.assertEqual(rows[0].text, "run the tests")
        self.assertIn("1 unparseable entry", rows[1].text)

    def test_args_summary(self):
        self.assertEqual(args_summary({"command": "ls"}), "ls")
        self.assertEqual(args_summary({"other": 1}), '{"other":1}')
        self.assertEqual(args_summary(None), "")


from doubleagent.parsers.kiro import KiroParser, salvage
from fixtures import KIRO_EXPORT_SESSION, KIRO_SESSION, KIRO_SHELL_SESSION


class KiroTests(ParserBase):
    DB = ".local/share/amazon-q/data.sqlite3"
    EXPORT = ".aws/amazonq/exports/issue-chat.json"

    def test_rows(self):
        rows = self.rows_for(KiroParser(), self.DB)
        conv = [r for r in rows if r.session_id == KIRO_SESSION and not model_or_permission_row(r)]
        self.assertEqual(
            [r.turn_type for r in conv],
            ["user", "assistant", "tool_use", "tool_result", "assistant"],
        )
        for r in conv:
            self.assertEqual((r.host, r.user, r.agent), ("h1", "alice", "kiro"))
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", ""))
            self.assertEqual(r.source_line, 1)
        # the second request was answered by another model
        self.assertEqual([r.model for r in conv], ["claude-sonnet-4"] * 3 + ["claude-opus-4"] * 2)
        user, asst, use, res, final = conv
        self.assertEqual(
            (user.text, user.timestamp_utc), ("list the files here", "2026-04-24T03:17:15.123Z")
        )
        self.assertEqual(
            (asst.text, asst.timestamp_utc),
            ("I will list the directory.", "2026-04-24T03:17:16.900Z"),
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("execute_bash", "tooluse_abc123", '{"command":"ls -la"}'),
        )
        # null user.timestamp falls back to the entry's request start
        self.assertEqual(
            (res.tool_name, res.tool_use_id, res.timestamp_utc),
            ("execute_bash", "tooluse_abc123", "2026-04-24T03:17:17.000Z"),
        )
        self.assertEqual(res.text, "total 8\nREADME.md [Success]")
        self.assertEqual(final.timestamp_utc, "2026-04-24T03:17:18.100Z")

    def test_export_variants(self):
        rows = [
            r for r in self.rows_for(KiroParser(), self.EXPORT) if not model_or_permission_row(r)
        ]
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "user",
                "tool_use",
                "tool_result",
                "assistant",
                "tool_use",
                "user",
                "tool_result",
                "assistant",
                "system",
                "system",
                "system",
            ],
        )
        self.assertTrue(
            all(r.session_id == KIRO_EXPORT_SESSION and r.project_path == "/srv/proj" for r in rows)
        )
        user, mcp, mcpres, _, _, stop, cancelled, _, compact_, summary, pending = rows
        self.assertEqual(
            (user.timestamp_utc, user.model), ("2026-04-24T14:00:00.000Z", "claude-3.7-sonnet")
        )  # legacy model
        self.assertEqual(
            (mcp.tool_name, mcp.text),
            ("github___create_issue", 'orig_name=create_issue {"title":"bug"}'),
        )
        self.assertEqual(
            (mcpres.tool_name, mcpres.text), ("github___create_issue", '{"number":7} [Error]')
        )
        self.assertEqual(stop.text, "stop, do not delete")
        self.assertEqual(
            (cancelled.tool_use_id, cancelled.text),
            ("tooluse_bash2", "cancelled Tool use was cancelled by the user [Error]"),
        )
        self.assertTrue(compact_.text.startswith("compact:"))
        self.assertEqual(
            summary.text, "summary: User asked to open an issue and cancelled a delete."
        )
        self.assertEqual(pending.text, "pending message (not sent): now push it")

    def test_model_rows(self):
        rows = [r for r in self.rows_for(KiroParser(), self.DB) if r.session_id == KIRO_SESSION]
        state = [(i, r) for i, r in enumerate(rows) if model_or_permission_row(r)]
        self.assertEqual(
            [(i, r.text, r.timestamp_utc, r.model) for i, r in state],
            [
                (0, "model: claude-sonnet-4", "2026-04-24T03:17:15.123Z", "claude-sonnet-4"),
                # before the second entry's rows; its user timestamp is null,
                # so the request start
                (
                    4,
                    "model: claude-sonnet-4 -> claude-opus-4",
                    "2026-04-24T03:17:17.000Z",
                    "claude-opus-4",
                ),
            ],
        )
        for _, r in state:
            self.assertEqual(
                (r.turn_type, r.project_path, r.source_line), ("system", "/srv/proj", 1)
            )
        # an entry without model_id falls back to the conversation's model and says so
        rows = self.rows_for(KiroParser(), self.EXPORT)
        self.assertEqual(
            [r.text for r in rows if model_or_permission_row(r)],
            [
                "model: claude-3.7-sonnet source=model",
                "model: claude-3.7-sonnet -> claude-sonnet-4",
            ],
        )
        self.assertEqual(rows[0].timestamp_utc, "2026-04-24T14:00:00.000Z")

    def test_thinking_opt_in(self):
        # the format records no reasoning, so the option changes nothing
        for rel in (self.DB, self.EXPORT):
            with_thinking = self.rows_for(KiroParser(), rel, include_thinking=True)
            self.assertEqual(len(self.rows_for(KiroParser(), rel)), len(with_thinking))
            self.assertFalse([r for r in with_thinking if r.turn_type == "thinking"])

    def test_shell_history_and_bad_blob(self):
        rows = self.rows_for(KiroParser(), self.DB)
        shell = [r for r in rows if r.session_id == KIRO_SHELL_SESSION]
        self.assertEqual(len(shell), 1)
        self.assertEqual(
            (shell[0].turn_type, shell[0].timestamp_utc, shell[0].project_path),
            ("system", "2026-04-24T03:00:00.000Z", "/srv/proj"),
        )
        self.assertTrue(shell[0].text.startswith("shell history: git status"))
        bad = [r for r in rows if r.project_path == "/srv/broken"]
        self.assertEqual(len(bad), 1)
        self.assertEqual((bad[0].turn_type, bad[0].source_line), ("system", 2))
        self.assertIn("unparseable", bad[0].text)
        self.assertNotIn("REDACT-ME", " ".join(r.text for r in rows))

    def test_not_wanted(self):
        p = KiroParser()
        for rel in (".kiro/settings/cli.json", ".kiro/sessions/s1.json"):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertEqual(art.agent, "kiro")
            self.assertFalse(p.wants(art), rel)

    def test_truncated_export_is_reported_not_fatal(self):
        rows = self.rows_for(KiroParser(), ".aws/amazonq/exports/issue-chat-cut.json")
        self.assertEqual(
            [r.turn_type for r in rows if not model_or_permission_row(r)],
            ["user", "tool_use", "tool_result", "assistant", "tool_use", "system"],
        )
        self.assertEqual(rows[0].session_id, KIRO_EXPORT_SESSION)
        self.assertIn("2 history entries recovered", rows[-1].text)

    def test_salvage(self):
        self.assertEqual(salvage('{"a": 1}'), ({"a": 1}, ""))
        state, err = salvage('{"conversation_id": "c\\"1", "history": [{"x": 1}, {"y": ')
        self.assertEqual(state, {"conversation_id": 'c"1', "history": [{"x": 1}]})
        self.assertTrue(err)
        self.assertEqual(salvage("garbage")[0], None)


from fixtures import GEMINI_TRUST_MTIME


class GeminiCliTests(ParserBase):
    REL = GEMINI_REL
    LEGACY = ".gemini/tmp/%s/chats/session-2026-09-30T08-00-b2c3d4e5.json" % GEMINI_HASH

    def test_secondary(self):
        # The history file is a secondary source, the transcript is not (#122).
        p = GeminiCliParser()
        self.assertTrue(p.secondary(self.artifact(".gemini/tmp/proj/logs.json")))
        self.assertFalse(p.secondary(self.artifact(self.REL)))

    def test_rows(self):
        rows = self.rows_for(GeminiCliParser(), self.REL)
        types = [r.turn_type for r in rows]
        self.assertEqual(
            types,
            [
                "system",
                "user",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
                "user",
                "assistant",
                "tool_use",
                "tool_result",
                "system",
                "system",
                "tool_use",
                "tool_result",
                "system",
                "user",
                "system",
                "system",
            ],
        )
        for r in rows:
            self.assertEqual((r.host, r.user, r.agent), ("h1", "alice", "gemini-cli"))
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", ""))
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        (
            start,
            u1,
            m1,
            g1,
            ls,
            lsout,
            _u3,
            g3,
            rf,
            rfout,
            info,
            m2,
            sh,
            shout,
            dec,
            u4,
            summ,
            rewind,
        ) = rows
        self.assertEqual(
            (m1.text, m1.model, m1.timestamp_utc, m1.session_id, m1.source_line),
            (
                "model: gemini-2.5-pro",
                "gemini-2.5-pro",
                "2026-10-01T09:00:07.000Z",
                GEMINI_SESSION,
                4,
            ),
        )
        self.assertEqual(
            (m2.text, m2.model, m2.timestamp_utc, m2.source_line),
            (
                "model: gemini-2.5-pro -> gemini-2.5-flash",
                "gemini-2.5-flash",
                "2026-10-01T09:00:24.000Z",
                13,
            ),
        )
        self.assertEqual(
            (dec.text, dec.tool_name, dec.tool_use_id, dec.timestamp_utc),
            (
                "permission decision: cancelled",
                "run_shell_command",
                "run_shell_command-2",
                "2026-10-01T09:00:24.000Z",
            ),
        )
        self.assertIn("session start: kind=main", start.text)
        self.assertEqual((u1.text, u1.session_id), ("list files in src", GEMINI_SESSION))
        self.assertEqual(
            (g1.text, g1.model, g1.source_line), ("Listing now.", "gemini-2.5-pro", 4)
        )  # re-appended record
        self.assertEqual(
            (ls.tool_name, ls.tool_use_id), ("list_directory", "list_directory-1759309207000")
        )
        self.assertEqual(ls.text, 'ReadFolder: {"path":"/srv/proj/src"}')
        self.assertEqual(ls.timestamp_utc, "2026-10-01T09:00:07.100Z")
        self.assertEqual(
            (lsout.tool_use_id, lsout.text), ("list_directory-1759309207000", "main.ts\nutil.ts")
        )
        self.assertNotIn("delete everything", " ".join(r.text for r in rows))  # rewound
        self.assertEqual(g3.text, "Here is util.ts.")  # $patch content
        self.assertEqual(rfout.text, "export const x = 1")  # $patch toolCalls result
        self.assertEqual(info.text, "info: Request cancelled.")
        self.assertEqual(
            (sh.text, sh.model), ('Shell: {"command":"curl http://x"}', "gemini-2.5-flash")
        )
        self.assertEqual(shout.text, "[cancelled]")
        self.assertEqual(u4.session_id, GEMINI_RESUMED)  # $set.sessionId on resume
        self.assertEqual(rf.session_id, GEMINI_SESSION)
        self.assertEqual(
            (summ.text, summ.timestamp_utc, summ.source_line),
            ("summary: List src files", "2026-10-01T09:00:08.000Z", 5),
        )
        self.assertEqual(
            (rewind.text, rewind.source_line), ("rewind to msg-u2: 2 message(s) dropped", 8)
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(GeminiCliParser(), self.REL, include_thinking=True)
        think = [r for r in rows if r.turn_type == "thinking"]
        self.assertEqual(
            [(r.text, r.timestamp_utc) for r in think],
            [("Plan: Use the ls tool.", "2026-10-01T09:00:06.500Z")],
        )

    def test_legacy_json_and_hash_directory(self):
        rows = self.rows_for(GeminiCliParser(), self.LEGACY)
        self.assertEqual([r.turn_type for r in rows], ["system", "user", "system", "assistant"])
        self.assertTrue(all(r.session_id == GEMINI_LEGACY for r in rows))
        self.assertTrue(
            all(r.project_path == "/srv/proj" for r in rows)
        )  # sha256 match in projects.json
        self.assertEqual(rows[2].text, "model: gemini-2.0-flash")
        self.assertEqual((rows[3].text, rows[3].model), ("Hi.", "gemini-2.0-flash"))
        rows = self.rows_for(GeminiCliParser(), self.LEGACY, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["weighing it"])

    def test_subagent_session(self):
        rel = ".gemini/tmp/proj/chats/%s/%s.jsonl" % (GEMINI_SESSION, GEMINI_SUBAGENT)
        rows = self.rows_for(GeminiCliParser(), rel)
        self.assertEqual([r.turn_type for r in rows], ["system", "user"])
        self.assertIn("kind=subagent", rows[0].text)
        self.assertEqual(rows[1].session_id, GEMINI_SUBAGENT)

    def test_awaiting_approval_without_result(self):
        rel = ".gemini/tmp/proj/chats/%s/%s.jsonl" % (GEMINI_SESSION, GEMINI_SUBAGENT)
        call = {
            "id": "run_shell_command-9",
            "name": "run_shell_command",
            "args": {"command": "make deploy"},
            "status": "awaiting_approval",
            "timestamp": "2026-10-01T09:00:32.000Z",
        }
        msg = {
            "id": "s-g1",
            "timestamp": "2026-10-01T09:00:31.000Z",
            "type": "gemini",
            "content": "",
            "model": "gemini-2.5-pro",
            "toolCalls": [call],
        }
        with open(self.home / rel, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(msg) + "\n")
        rows = self.rows_for(GeminiCliParser(), rel)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows[2:]],
            [
                ("system", "model: gemini-2.5-pro"),
                ("tool_use", '{"command":"make deploy"}'),
                ("system", "permission decision: awaiting_approval"),
            ],
        )
        dec = rows[-1]
        self.assertEqual(
            (dec.tool_name, dec.tool_use_id, dec.timestamp_utc, dec.session_id),
            (
                "run_shell_command",
                "run_shell_command-9",
                "2026-10-01T09:00:32.000Z",
                GEMINI_SUBAGENT,
            ),
        )

    def test_trusted_folders(self):
        rel = ".gemini/trustedFolders.json"
        rows = self.rows_for(GeminiCliParser(), rel)
        self.assertEqual(
            [(r.turn_type, r.text, r.project_path) for r in rows],
            [
                (
                    "system",
                    "permission setting: trustedFolders./srv/proj=TRUST_FOLDER "
                    "(from .gemini/trustedFolders.json, file mtime)",
                    "/srv/proj",
                ),
                (
                    "system",
                    "permission setting: trustedFolders./srv/other=TRUST_PARENT "
                    "(from .gemini/trustedFolders.json, file mtime)",
                    "/srv/other",
                ),
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.timestamp_utc, r.session_id, r.source_line, r.agent),
                (to_utc(GEMINI_TRUST_MTIME), "", 1, "gemini-cli"),
            )
        (self.home / rel).write_text('{"/srv/proj": ', encoding="utf-8")
        rows = self.rows_for(GeminiCliParser(), rel)
        self.assertEqual(
            [(r.turn_type, r.text, r.timestamp_utc) for r in rows],
            [
                (
                    "system",
                    "parser: .gemini/trustedFolders.json is not a JSON object",
                    rows[0].timestamp_utc,
                )
            ],
        )
        # The session file still yields every row.
        self.assertEqual(len(self.rows_for(GeminiCliParser(), self.REL)), 18)

    def test_history(self):
        rows = self.rows_for(GeminiCliParser(), ".gemini/tmp/proj/logs.json")
        self.assertEqual([r.turn_type for r in rows], ["user", "user"])
        self.assertEqual(rows[1].text, "delete everything in /srv/proj")  # kept although rewound
        self.assertEqual((rows[0].session_id, rows[0].project_path), (GEMINI_SESSION, "/srv/proj"))
        self.assertEqual(rows[0].timestamp_utc, "2026-10-01T09:00:05.000Z")

    def test_project_fallbacks(self):
        base = self.home / ".gemini"
        self.assertEqual(resolve_project(base, "proj"), "/srv/proj")  # .project_root
        (base / "tmp/proj/.project_root").unlink()
        self.assertEqual(resolve_project(base, "proj"), "/srv/proj")  # projects.json slug
        self.assertEqual(resolve_project(base, "other", GEMINI_HASH), "/srv/proj")
        self.assertEqual(resolve_project(base, "other", "f" * 64), "f" * 64)  # unresolved hash

    def test_noise_not_wanted(self):
        p = GeminiCliParser()
        for rel in (
            ".gemini/oauth_creds.json",
            ".gemini/settings.json",
            ".gemini/projects.json",
            ".gemini/tmp/proj/.project_root",
            ".gemini/tmp/proj/shell_history",
            ".gemini/antigravity-cli/history.jsonl",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(p.wants(art), rel)

    def test_truncated_last_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(GeminiCliParser(), self.REL)
        self.assertEqual(len(rows), 19)
        self.assertIn("1 unparseable line", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 16)
        (self.home / self.LEGACY).write_text('{"sessionId": "x", "messages": [', encoding="utf-8")
        rows = self.rows_for(GeminiCliParser(), self.LEGACY)
        self.assertEqual(len(rows), 1)
        self.assertIn("unparseable", rows[0].text)


class CrushTests(ParserBase):
    REL = ".crush/crush.db"

    def test_rows(self):
        rows = self.rows_for(CrushParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
                "system",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "crush", CRUSH_SESSION)
            )
            self.assertEqual(
                (r.project_path, r.git_branch), ("/alice", "")
            )  # the directory holding .crush
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        start, model, user, use, result, switch, asst, finish = rows
        self.assertEqual(
            start.text, "session start | Fix bug | 3 messages | tokens in=10 out=5 | cost=0.01"
        )
        self.assertEqual(
            (model.text, model.model, model.timestamp_utc, model.source_line),
            (
                "model: claude-sonnet-4 provider=anthropic",
                "anthropic/claude-sonnet-4",
                "2025-10-09T08:53:21.000Z",
                1,
            ),
        )
        # The tool message (m3) names no model and is not a change.
        self.assertEqual(
            (switch.text, switch.model, switch.timestamp_utc, switch.source_line),
            (
                "model: claude-sonnet-4 -> gpt-5 provider=openai",
                "openai/gpt-5",
                "2025-10-09T08:53:24.000Z",
                4,
            ),
        )
        self.assertEqual(asst.model, "openai/gpt-5")
        self.assertEqual(
            (user.text, user.model, user.timestamp_utc),
            ("list files", "anthropic/claude-sonnet-4", "2025-10-09T08:53:21.000Z"),
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("bash", "call_x1", '{"command":"ls"}')
        )
        self.assertEqual(
            use.timestamp_utc, "2025-10-09T08:53:23.000Z"
        )  # finished_at, not created_at
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text), ("bash", "call_x1", "a.txt")
        )
        self.assertEqual(asst.text, "There is one file, a.txt.")
        self.assertEqual(
            (finish.text, finish.timestamp_utc), ("finish: max_tokens", "2025-10-09T08:53:25.000Z")
        )

    def test_rows_live_only_in_the_wal(self):
        art = next(a for a in self.col.artifacts if a.rel == self.REL)
        import sqlite3

        con = sqlite3.connect("file:%s?immutable=1" % art.disk_path.as_posix(), uri=True)
        try:
            self.assertEqual(con.execute("select count(*) from messages").fetchone()[0], 0)
        finally:
            con.close()
        self.assertTrue(Path(str(art.disk_path) + "-wal").is_file())

    def test_thinking_opt_in(self):
        rows = self.rows_for(CrushParser(), self.REL, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["one file only"])

    def test_projects_registry(self):
        rows = self.rows_for(CrushParser(), ".local/share/crush/projects.json")
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            (rows[0].turn_type, rows[0].project_path, rows[0].timestamp_utc),
            ("system", "/srv/proj", "2026-10-01T12:00:00.000Z"),
        )
        self.assertIn("data_dir=/srv/proj/.crush", rows[0].text)

    def test_project_path_from_original(self):
        self.assertEqual(project_of("/srv/proj/.crush/crush.db"), "/srv/proj")
        self.assertEqual(project_of("C:\\Users\\a\\repo\\.crush\\crush.db"), "C:\\Users\\a\\repo")
        self.assertEqual(project_of(".crush/crush.db"), "")

    def test_config_and_sidecars_not_wanted(self):
        p = CrushParser()
        for a in self.col.artifacts:
            if a.agent == "crush" and a.rel.endswith(("crush.json", "-wal", "-shm")):
                self.assertFalse(p.wants(a), a.rel)

    def test_bad_parts_is_reported_not_fatal(self):
        import sqlite3

        db = self.home / self.REL
        con = sqlite3.connect(str(db))
        con.execute(
            "INSERT INTO messages(id,session_id,role,parts,model,provider,created_at,updated_at) "
            "VALUES ('m5','6f1c0001','assistant','[{\"type\":\"text\",\"data\":{\"text\":\"cut','m','p',1760000006,1760000006)"
        )
        con.commit()
        con.close()
        rows = self.rows_for(CrushParser(), self.REL)
        # m5 names model "m" from provider "p", so its parse error follows a model row.
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[-2].text, "model: gpt-5 -> m provider=p")
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("m5 parts did not parse", rows[-1].text)
        self.assertEqual(rows[2].text, "list files")

    def test_not_sqlite_is_reported(self):
        (self.home / self.REL).write_bytes(b"not a database")
        rows = self.rows_for(CrushParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows], [("system", "parser: not a SQLite database")]
        )


class GooseTests(ParserBase):
    REL = ".local/share/goose/sessions/sessions.db"

    def test_rows(self):
        rows = [r for r in self.rows_for(GooseParser(), self.REL) if not model_or_permission_row(r)]
        self.assertEqual(
            [r.turn_type for r in rows], ["system", "user", "tool_use", "tool_result", "assistant"]
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "goose", GOOSE_SESSION)
            )
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", ""))
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        # the last assistant message names its own provider and model
        self.assertEqual(
            [r.model for r in rows],
            ["anthropic/claude-sonnet-4-5"] * 4 + ["openai/gpt-4.1-2025-04-14"],
        )
        start, user, use, result, asst = rows
        self.assertEqual(
            (start.text, start.timestamp_utc),
            ("session start | Fix flaky test | type=user", "2026-03-01T09:00:00.000Z"),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc), ("run the tests", "2026-03-01T09:00:00.000Z")
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("developer__shell", "call_1", '{"command":"pytest -q"}'),
        )
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text),
            ("developer__shell", "call_1", "3 passed"),
        )
        self.assertEqual(
            (asst.text, asst.timestamp_utc), ("All 3 tests pass.", "2026-03-01T09:00:05.000Z")
        )
        self.assertEqual([r.source_line for r in rows], [1, 1, 2, 3, 4])

    def test_thinking_opt_in(self):
        rows = self.rows_for(GooseParser(), self.REL, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["all green"])

    def test_legacy_request_log_and_history(self):
        rows = self.rows_for(GooseParser(), GOOSE_LEGACY_REL)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [("system", "session start (legacy) | old chat | 1 messages"), ("user", "hello")],
        )
        self.assertEqual(
            {(r.session_id, r.project_path) for r in rows}, {("20260301_090000", "/srv/old")}
        )
        rows = self.rows_for(GooseParser(), ".local/state/goose/logs/llm_request.0.jsonl")
        self.assertEqual(
            [(r.turn_type, r.model, r.text) for r in rows],
            [
                ("system", "gpt-4.1", "llm request | 1 messages | last user: hello"),
                ("assistant", "gpt-4.1", "hi"),
            ],
        )
        self.assertEqual({r.timestamp_utc for r in rows}, {"2026-03-01T09:00:01.000Z"})
        rows = self.rows_for(GooseParser(), ".local/state/goose/history.txt")
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [("user", "run the tests"), ("user", "line one\nline two \\ done")],
        )
        self.assertEqual(unescape_history("a\\nb\\\\c"), "a\nb\\c")

    def test_millisecond_timestamps(self):
        from doubleagent.parsers.goose import epoch

        self.assertEqual(epoch(1772355600000), "2026-03-01T09:00:00.000Z")
        self.assertEqual(
            epoch(17723556000), to_utc(17723556)
        )  # Goose divides above 1e10, to_utc only above 1e11

    def test_config_secrets_and_sidecars_not_wanted(self):
        p = GooseParser()
        for a in self.col.artifacts:
            if a.agent == "goose" and a.rel.endswith((".yaml", "-wal", "-shm")):
                self.assertFalse(p.wants(a), a.rel)

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / GOOSE_LEGACY_REL)
        rows = self.rows_for(GooseParser(), GOOSE_LEGACY_REL)
        self.assertEqual([r.turn_type for r in rows], ["system", "user", "system"])
        self.assertEqual(rows[-1].text, "parser: 1 unparseable line(s), first at line 3")
        self.assertEqual(rows[-1].session_id, "20260301_090000")

    def test_bad_content_json_is_reported_not_fatal(self):
        import sqlite3

        con = sqlite3.connect(str(self.home / self.REL))
        con.execute(
            "INSERT INTO messages(session_id,role,content_json,created_timestamp) "
            "VALUES ('20260301_1','assistant','[{\"type\":\"text\",\"te',1772355606)"
        )
        con.commit()
        con.close()
        rows = [r for r in self.rows_for(GooseParser(), self.REL) if not model_or_permission_row(r)]
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "tool_use", "tool_result", "assistant", "system"],
        )
        self.assertIn("content_json did not parse", rows[-1].text)

    def test_model_and_mode_rows(self):
        rows = self.rows_for(GooseParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows[:4]],
            [
                ("system", "session start | Fix flaky test | type=user"),
                ("system", "model: claude-sonnet-4-5 provider=anthropic"),
                ("system", "permission mode: auto"),
                ("user", "run the tests"),
            ],
        )
        for r in rows[1:3]:
            self.assertEqual(
                (r.timestamp_utc, r.session_id, r.project_path, r.model, r.source_line),
                (
                    "2026-03-01T09:00:00.000Z",
                    GOOSE_SESSION,
                    "/srv/proj",
                    "anthropic/claude-sonnet-4-5",
                    1,
                ),
            )
        # message 2 requests the session's model: no row; message 4 switches
        change = [r for r in rows if r.text.startswith("model: ") and "->" in r.text]
        self.assertEqual(len(change), 1)
        c = change[0]
        self.assertEqual(
            c.text,
            "model: claude-sonnet-4-5 -> gpt-4.1-2025-04-14 provider=openai requested=gpt-4.1",
        )
        self.assertEqual(
            (c.turn_type, c.timestamp_utc, c.session_id, c.model, c.source_line),
            ("system", "2026-03-01T09:00:05.000Z", GOOSE_SESSION, "openai/gpt-4.1-2025-04-14", 4),
        )
        self.assertEqual(rows[rows.index(c) + 1].text, "All 3 tests pass.")

    def test_legacy_and_request_log_have_no_model_rows(self):
        for rel in (GOOSE_LEGACY_REL, ".local/state/goose/logs/llm_request.0.jsonl"):
            self.assertFalse(
                [r for r in self.rows_for(GooseParser(), rel) if model_or_permission_row(r)]
            )


from doubleagent.parsers.aider import AiderParser
from doubleagent.parsers.continue_dev import ContinueParser, load_session
from fixtures import CONTINUE_SESSION, build_aider


class ContinueTests(ParserBase):
    REL = ".continue/sessions/%s.json" % CONTINUE_SESSION

    def test_rows(self):
        rows = self.rows_for(ContinueParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
                "system",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id),
                ("h1", "alice", "continue", CONTINUE_SESSION),
            )
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", ""))
            # no per-message time: every row inherits sessions.json dateCreated
            self.assertEqual(r.timestamp_utc, "2026-10-02T10:00:00.000Z")
        start, model, user, use1, res1, switch, asst, _use2, res2, canceled = rows
        self.assertIn("session start: Fix bug mode=agent items=5", start.text)
        # chatModelTitle starts the session; item 5's promptLogs switch it
        self.assertEqual(
            (model.text, model.model, model.source_line), ("model: GPT-4o", "GPT-4o", 0)
        )
        self.assertEqual(
            (switch.text, switch.model, switch.source_line),
            ("model: GPT-4o -> Claude Sonnet 4.5", "Claude Sonnet 4.5", 5),
        )
        self.assertEqual(user.text, "rename foo\n[image]")
        self.assertEqual(
            (use1.tool_name, use1.tool_use_id, use1.text, use1.model),
            ("edit_existing_file", "call_1", '{"filepath":"a.py"}', "GPT-4o"),
        )
        self.assertEqual(
            (res1.tool_name, res1.tool_use_id, res1.text), ("edit_existing_file", "call_1", "ok")
        )
        self.assertEqual(asst.text, "Renamed. Cleaning the build too.")
        # a call with no tool message keeps its outcome in toolCallStates
        self.assertEqual((res2.tool_use_id, res2.text), ("call_2", "[canceled]"))
        # the canceled state is a per-call decision, after its result row
        self.assertEqual(
            (canceled.text, canceled.tool_use_id, canceled.tool_name, canceled.timestamp_utc),
            (
                "permission decision: canceled",
                "call_2",
                "run_terminal_command",
                "2026-10-02T10:00:00.000Z",
            ),
        )
        self.assertEqual([r.source_line for r in rows], [0, 0, 1, 3, 4, 5, 5, 5, 5, 5])

    def test_thinking_opt_in(self):
        rows = self.rows_for(ContinueParser(), self.REL, include_thinking=True)
        thinking = [r for r in rows if r.turn_type == "thinking"]
        self.assertEqual([r.text for r in thinking], ["consider the callers", "find foo first"])
        self.assertEqual(thinking[1].timestamp_utc, "2026-10-02T10:00:01.000Z")  # reasoning.startAt

    def test_dev_data(self):
        rows = self.rows_for(ContinueParser(), ".continue/dev_data/0.2.0/chatInteraction.jsonl")
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows], [("user", "rename foo"), ("assistant", "done")]
        )
        self.assertTrue(all(r.timestamp_utc == "2026-10-02T10:00:05.000Z" for r in rows))
        self.assertEqual(
            (rows[1].session_id, rows[1].project_path, rows[1].model),
            (CONTINUE_SESSION, "/srv/proj", "GPT-4o"),
        )
        rows = self.rows_for(ContinueParser(), ".continue/dev_data/0.2.0/toolUsage.jsonl")
        self.assertEqual(
            [(r.turn_type, r.tool_name, r.tool_use_id) for r in rows],
            [
                ("tool_use", "edit_existing_file", "call_1"),
                ("tool_result", "edit_existing_file", "call_1"),
                ("system", "edit_existing_file", "call_1"),
                ("tool_use", "run_terminal_command", "call_2"),
                ("tool_result", "run_terminal_command", "call_2"),
                ("system", "run_terminal_command", "call_2"),
            ],
        )
        self.assertEqual(rows[1].text, "accepted=true succeeded=true ok")
        self.assertEqual(
            (rows[2].text, rows[2].timestamp_utc, rows[2].session_id),
            ("permission decision: accepted=true", "2026-10-02T10:00:03.000Z", ""),
        )
        self.assertEqual(rows[4].text, "accepted=false succeeded=false")
        self.assertEqual(
            (rows[5].text, rows[5].timestamp_utc, rows[5].source_line),
            ("permission decision: accepted=false", "2026-10-02T10:00:06.000Z", 2),
        )

    def test_index_and_config_not_wanted(self):
        p = ContinueParser()
        for rel in (".continue/sessions/sessions.json", ".continue/config.yaml"):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(p.wants(art), rel)

    def test_truncated_session_keeps_earlier_turns(self):
        path = self.home / self.REL
        raw = path.read_text(encoding="utf-8")
        path.write_text(raw[: raw.index('"toolCallId": "call_2"')], encoding="utf-8")
        rows = self.rows_for(ContinueParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "system", "tool_use", "tool_result", "system"],
        )
        # chatModelTitle sits after the cut, so the first promptLogs title starts it
        self.assertEqual((rows[2].text, rows[2].source_line), ("model: GPT-4o", 3))
        self.assertIn("recovered 4 history item(s)", rows[-1].text)
        self.assertEqual(rows[1].session_id, CONTINUE_SESSION)

    def test_truncated_dev_data_line(self):
        rel = ".continue/dev_data/0.2.0/chatInteraction.jsonl"
        write_bad_line(self.home / rel)
        rows = self.rows_for(ContinueParser(), rel)
        self.assertEqual([r.turn_type for r in rows], ["user", "assistant", "system"])
        self.assertIn("1 unparseable line", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 2)

    def test_load_session_trailing_data(self):
        obj, problem = load_session('{"sessionId": "x", "history": []}\n{"junk"')
        self.assertEqual(obj["sessionId"], "x")
        self.assertIn("trailing data", problem)


class AiderTests(ParserBase):
    CHAT = ".aider.chat.history.md"
    S1 = "/alice/.aider.chat.history.md#2026-10-02 12:00:00"
    S2 = "/alice/.aider.chat.history.md#2026-10-02 13:00:00"

    def test_rows(self):
        rows = self.rows_for(AiderParser(), self.CHAT)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "assistant", "tool_result", "system", "user", "tool_result", "user"],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.project_path), ("h1", "alice", "aider", "/alice")
            )
            self.assertEqual((r.model, r.git_branch, r.tool_use_id), ("", "", ""))
        start, user, asst, tool, _start2, add, added, blank = rows
        self.assertEqual([r.session_id for r in rows], [self.S1] * 4 + [self.S2] * 4)
        self.assertEqual(start.timestamp_utc, "2026-10-02T12:00:00.000Z")
        # the prompt takes its time from the matching input-history entry, and later rows inherit it
        self.assertEqual(
            (user.text, user.timestamp_utc), ("rename foo to bar", "2026-10-02T12:00:05.123Z")
        )
        self.assertEqual(asst.timestamp_utc, "2026-10-02T12:00:05.123Z")
        self.assertTrue(asst.text.startswith("Here is the change:\n\na.py\n<<<<<<< SEARCH"))
        self.assertTrue(asst.text.endswith(">>>>>>> REPLACE"))
        self.assertEqual(
            tool.text, "Applied edit to a.py\nCommit abc1234 refactor: rename foo to bar"
        )
        self.assertEqual((add.text, add.timestamp_utc), ("/add b.py", "2026-10-02T13:00:02.000Z"))
        self.assertEqual(added.text, "Added b.py to the chat")
        self.assertEqual(blank.text, "<blank>")
        self.assertEqual([r.source_line for r in rows], [2, 5, 7, 16, 19, 22, 23, 25])

    def test_thinking_opt_in(self):
        # Aider records no reasoning; the flag must not change the rows.
        self.assertEqual(
            len(self.rows_for(AiderParser(), self.CHAT, include_thinking=True)),
            len(self.rows_for(AiderParser(), self.CHAT)),
        )

    def test_input_and_llm_history(self):
        rows = self.rows_for(AiderParser(), ".aider.input.history")
        self.assertEqual(
            [(r.turn_type, r.text, r.timestamp_utc, r.session_id) for r in rows],
            [
                ("user", "rename foo to bar", "2026-10-02T12:00:05.123Z", self.S1),
                ("user", "/add b.py", "2026-10-02T13:00:02.000Z", self.S2),
            ],
        )
        rows = self.rows_for(AiderParser(), ".aider.llm.history")
        self.assertEqual([r.turn_type for r in rows], ["system", "assistant"])
        self.assertEqual(
            rows[0].text,
            "TO LLM: 2 message(s) (SYSTEM 1, USER 1); last user message: rename foo to bar",
        )
        self.assertEqual(
            (rows[1].text, rows[1].timestamp_utc),
            ("Here is the change:\n\na.py", "2026-10-02T12:00:09.000Z"),
        )
        self.assertTrue(all(r.session_id == self.S1 for r in rows))

    def test_config_not_wanted(self):
        art = next(a for a in self.col.artifacts if a.rel == ".aider.conf.yml")
        self.assertFalse(AiderParser().wants(art))

    def test_truncated_line(self):
        write_bad_line(self.home / ".aider.input.history")
        rows = self.rows_for(AiderParser(), ".aider.input.history")
        self.assertEqual([r.turn_type for r in rows], ["user", "user", "system"])
        self.assertIn("1 unparseable line", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 7)

    def test_project_artifacts_from_manifest(self):
        """The collector attributes repository files to agent `project` with
        the project as the home; the rows still say aider."""
        import json as _json

        root = self.tmp / "collected"
        build_aider(root / "fs/srv/proj")
        (root / "collection.json").write_text(_json.dumps({"hostname": "h2"}), encoding="utf-8")
        with open(root / "manifest.jsonl", "w", encoding="utf-8") as fh:
            for name in (
                ".aider.chat.history.md",
                ".aider.input.history",
                ".aider.llm.history",
                ".aider.conf.yml",
            ):
                fh.write(
                    _json.dumps(
                        {
                            "user": "alice",
                            "home": "/srv/proj",
                            "agent": "project",
                            "path": "/srv/proj/" + name,
                            "archive_path": "fs/srv/proj/" + name,
                            "type": "file",
                            "status": "collected",
                            "secret": name.endswith(".yml"),
                        }
                    )
                    + "\n"
                )
        col = open_input(root, self.cat)
        self.assertEqual(col.kind, "collected")
        # Agent `project` rows are re-attributed from the bundled project
        # catalog, and their base is marked as a project.
        self.assertEqual(
            {a.rel: a.agent for a in col.artifacts if a.home.project},
            {
                rel: self.cat.project_agent_for(rel) or "project"
                for rel in (
                    ".aider.chat.history.md",
                    ".aider.input.history",
                    ".aider.llm.history",
                    ".aider.conf.yml",
                )
            },
        )
        rows, _, problems, _ = cli.collect_rows(col, Options(), [])
        self.assertEqual(problems, [])
        self.assertEqual(len(rows), 8 + 2 + 2)
        self.assertEqual(
            {(r.host, r.user, r.agent, r.project_path) for r in rows},
            {("h2", "alice", "aider", "/srv/proj")},
        )
        self.assertEqual(
            {r.session_id for r in rows},
            {
                "/srv/proj/.aider.chat.history.md#2026-10-02 12:00:00",
                "/srv/proj/.aider.chat.history.md#2026-10-02 13:00:00",
            },
        )
        self.assertFalse(
            AiderParser().wants(next(a for a in col.artifacts if a.rel == ".aider.conf.yml"))
        )


import sqlite3
from types import SimpleNamespace

import zstandard

from doubleagent.parsers.vscode import VsCodeParser, apply_mutation
from doubleagent.parsers.vscode import confirmed_text as vscode_confirmed_text
from doubleagent.parsers.zed import ZedParser
from fixtures import (
    VSCODE_LEGACY_SESSION,
    VSCODE_SESSION,
    VSCODE_WS,
    ZED_EXTERNAL,
    ZED_THREAD,
)


def rel_only(rel: str) -> Artifact:
    """A stand-in artifact carrying only `rel`, the one attribute wants() reads."""
    return cast(Artifact, SimpleNamespace(rel=rel))


def model_or_permission_row(r) -> bool:
    """A `model:` or `permission ...:` system row (issues 96 and 97)."""
    return r.turn_type == "system" and r.text.startswith(("model: ", "permission "))


class ZedTests(ParserBase):
    REL = ".local/share/zed/threads/threads.db"
    SIDEBAR = ".local/share/zed/db/0-stable/db.sqlite"

    def _insert(self, thread_id, data_type, data, updated="2026-10-03T12:00:00+00:00"):
        con = sqlite3.connect(str(self.home / self.REL))
        con.execute(
            "INSERT INTO threads(id,summary,updated_at,data_type,data,folder_paths) VALUES (?,?,?,?,?,?)",
            (thread_id, "extra", updated, data_type, data, "/srv/other"),
        )
        con.commit()
        con.close()

    def test_rows(self):
        rows = [r for r in self.rows_for(ZedParser(), self.REL) if not model_or_permission_row(r)]
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "tool_use", "tool_result", "assistant", "system", "system"],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "zed", ZED_THREAD)
            )
            self.assertEqual(
                (r.project_path, r.git_branch, r.model),
                ("/srv/proj", "main", "anthropic/claude-sonnet-4-5"),
            )
            self.assertEqual(r.source_line, 1)
        start, user, use, result, asst, resume, compaction = rows
        self.assertEqual(start.timestamp_utc, "2026-10-03T09:00:00.000Z")  # project snapshot time
        self.assertEqual(start.text, "thread start: Fix flaky test version=0.3.0")
        self.assertEqual(
            user.timestamp_utc, "2026-10-03T09:01:05.000Z"
        )  # thread updated_at, approximate
        self.assertEqual(user.text, "run the tests\n[mention] file:///srv/proj/README.md")
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("terminal", "toolu_01", '{"command":"pytest -q"}'),
        )
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text),
            ("terminal", "toolu_01", "3 passed"),
        )
        self.assertEqual(asst.text, "All 3 tests pass.")
        self.assertEqual((resume.text, compaction.text), ("resume", "compaction: ran the tests"))

    def test_thinking_opt_in(self):
        rows = self.rows_for(ZedParser(), self.REL, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["use pytest"])

    def test_sidebar_external_threads(self):
        rows = self.rows_for(ZedParser(), self.SIDEBAR)
        self.assertEqual(len(rows), 1)  # the native thread is skipped
        r = rows[0]
        self.assertEqual(
            (r.turn_type, r.session_id, r.project_path), ("system", ZED_EXTERNAL, "/srv/proj")
        )
        self.assertEqual(r.timestamp_utc, "2026-10-03T10:00:00.000Z")
        self.assertIn("agent=claude-code", r.text)

    def test_settings_not_wanted(self):
        art = next(a for a in self.col.artifacts if a.rel == ".config/zed/settings.json")
        self.assertFalse(ZedParser().wants(art))
        for rel in (
            "AppData/Local/Zed/threads/threads.db",
            "Library/Application Support/Zed/db/0-preview/db.sqlite",
            ".var/app/dev.zed.Zed/data/zed/threads/threads.db",
        ):
            self.assertTrue(ZedParser().wants(rel_only(rel)), rel)
        for rel in (self.REL + "-journal", self.SIDEBAR + "-wal"):
            self.assertFalse(ZedParser().wants(rel_only(rel)), rel)

    def test_corrupt_blob_is_reported_not_fatal(self):
        blob = zstandard.ZstdCompressor().compress(b'{"version":"0.3.0","messages":[]}' * 50)
        self._insert("bad-thread", "zstd", blob[: len(blob) // 2])
        rows = self.rows_for(ZedParser(), self.REL)
        self.assertEqual(len([r for r in rows if r.session_id == ZED_THREAD]), 13)
        bad = [r for r in rows if r.session_id == "bad-thread"]
        self.assertEqual(len(bad), 1)
        self.assertEqual(
            (bad[0].turn_type, bad[0].project_path, bad[0].source_line), ("system", "/srv/other", 2)
        )
        self.assertIn("could not be decoded", bad[0].text)

    def test_json_and_legacy_versions(self):
        legacy = {
            "version": "0.2.0",
            "summary": "old",
            "updated_at": "2026-01-01T00:00:00Z",
            "messages": [
                {
                    "id": 0,
                    "role": "user",
                    "segments": [{"type": "text", "text": "hello"}],
                    "tool_uses": [],
                    "tool_results": [],
                },
                {
                    "id": 1,
                    "role": "assistant",
                    "segments": [
                        {"type": "thinking", "text": "hmm"},
                        {"type": "text", "text": "hi"},
                    ],
                    "tool_uses": [{"id": "t1", "name": "grep", "input": {"regex": "x"}}],
                    "tool_results": [
                        {"tool_use_id": "t1", "is_error": True, "content": "no match"}
                    ],
                },
            ],
        }
        self._insert("legacy-thread", "json", json.dumps(legacy).encode("utf-8"))
        rows = [r for r in self.rows_for(ZedParser(), self.REL) if r.session_id == "legacy-thread"]
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [
                ("system", "thread start: extra version=0.2.0"),
                ("user", "hello"),
                ("assistant", "hi"),
                ("tool_use", '{"regex":"x"}'),
                ("tool_result", "[error] no match"),
            ],
        )
        self.assertEqual(rows[1].timestamp_utc, "2026-10-03T12:00:00.000Z")

    def test_model_and_thread_grant_rows(self):
        rows = self.rows_for(ZedParser(), self.REL)
        state = [r for r in rows if model_or_permission_row(r)]
        self.assertEqual(
            [r.text for r in state],
            [
                "model: claude-sonnet-4-5 provider=anthropic",
                "permission setting: profile=write (thread blob, as of updated_at)",
                "permission setting: sandbox_grants.write_paths=/srv/proj/build"
                " (thread blob, as of updated_at)",
                'permission setting: sandbox_grants.write_paths={"requested":"/tmp/out",'
                '"resolved":"/private/tmp/out"} (thread blob, as of updated_at)',
                "permission setting: sandbox_grants.network_hosts=*.npmjs.org"
                " (thread blob, as of updated_at)",
                "permission setting: sandbox_grants.unsandboxed=true"
                " (thread blob, as of updated_at)",
            ],
        )
        # the model row follows the thread-start row at its time; the grants
        # carry the thread id and the thread's updated_at, and come before
        # the first message
        self.assertEqual(rows[1], state[0])
        self.assertEqual(state[0].timestamp_utc, "2026-10-03T09:00:00.000Z")
        for r in state:
            self.assertEqual(
                (r.turn_type, r.session_id, r.project_path, r.source_line),
                ("system", ZED_THREAD, "/srv/proj", 1),
            )
            self.assertEqual(r.model, "anthropic/claude-sonnet-4-5")
        for r in state[1:]:
            self.assertEqual(r.timestamp_utc, "2026-10-03T09:01:05.000Z")
        self.assertEqual(rows[len(state) + 1].turn_type, "user")

    def test_thread_without_model_or_grants_has_no_state_rows(self):
        self._insert("bare", "json", b'{"version":"0.3.0","messages":[]}')
        rows = [r for r in self.rows_for(ZedParser(), self.REL) if r.session_id == "bare"]
        self.assertEqual([r.text for r in rows], ["thread start: extra version=0.3.0"])


class VsCodeTests(ParserBase):
    REL = VSCODE_WS + "/chatSessions/%s.jsonl" % VSCODE_SESSION
    LEGACY = (
        ".vscode-server/data/User/globalStorage/emptyWindowChatSessions/%s.json"
        % VSCODE_LEGACY_SESSION
    )

    def test_rows(self):
        rows = self.rows_for(VsCodeParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
                "user",
                "assistant",
                "system",
                "system",
                "system",
                "user",
                "system",
                "assistant",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "vscode", VSCODE_SESSION)
            )
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", ""))
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        self.assertEqual([r.source_line for r in rows], [1] * 8 + [2, 2, 2] + [6] * 5)
        start, model, mode, user, use, result, decision, asst, user2, asst2 = rows[:10]
        self.assertEqual(
            (model.text, model.model, model.timestamp_utc),
            ("model: copilot/gpt-4.1", "copilot/gpt-4.1", "2026-10-03T11:00:01.000Z"),
        )
        self.assertEqual(
            (mode.text, mode.timestamp_utc),
            ("permission mode: agent", "2026-10-03T11:00:01.000Z"),
        )
        self.assertEqual(
            (decision.text, decision.tool_use_id, decision.tool_name, decision.timestamp_utc),
            (
                "permission decision: confirmed=UserAction(4) selectedButton=Allow"
                " tool_source=internal",
                "call_a",
                "run_in_terminal",
                "2026-10-03T11:00:02.000Z",
            ),
        )
        confirm, model2, mode2, user3, chosen, asst3 = rows[10:]
        self.assertEqual(
            (confirm.text, confirm.timestamp_utc),
            (
                'permission decision: confirmation isUsed=true buttons=["Allow","Dismiss"]'
                " title=Run npm install?\nThis installs the packages.",
                "2026-10-03T11:00:11.000Z",
            ),
        )
        self.assertEqual(
            (model2.text, model2.model, model2.timestamp_utc),
            (
                "model: copilot/gpt-4.1 -> copilot/claude-sonnet-4",
                "copilot/claude-sonnet-4",
                "2026-10-03T11:00:20.000Z",
            ),
        )
        self.assertEqual(mode2.text, "permission mode: agent -> ask")
        self.assertEqual(user3.text, 'Allow: "Run npm install?"')
        self.assertEqual(
            (chosen.text, chosen.timestamp_utc),
            ("permission decision: confirmation=Allow", "2026-10-03T11:00:20.000Z"),
        )
        self.assertEqual(asst3.text, "Installed.")
        self.assertEqual(
            start.text, "session start: responder=GitHub Copilot location=panel title=Run tests"
        )
        self.assertEqual(start.timestamp_utc, "2026-10-03T11:00:00.000Z")
        self.assertEqual(
            (user.text, user.model, user.timestamp_utc),
            ("run tests\n[attached: test_a.py]", "copilot/gpt-4.1", "2026-10-03T11:00:01.000Z"),
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("run_in_terminal", "call_a", "pytest")
        )
        self.assertEqual(
            (result.tool_use_id, result.text, result.timestamp_utc),
            ("call_a", "3 passed", "2026-10-03T11:00:02.000Z"),
        )
        self.assertEqual(
            asst.text, "All tests pass in test_a.py."
        )  # markdown run with an inline reference
        self.assertEqual(
            (user2.text, user2.source_line), ("thanks", 2)
        )  # pushed by the second log line
        self.assertEqual(
            (asst2.text, asst2.timestamp_utc), ("You're welcome.", "2026-10-03T11:00:11.000Z")
        )

    def test_confirmed_forms(self):
        # A pre-1.104 boolean, a denial with its source, and a reason.
        self.assertEqual(
            vscode_confirmed_text({"isConfirmed": False}), "permission decision: confirmed=false"
        )
        self.assertEqual(
            vscode_confirmed_text(
                {"isConfirmed": {"type": 0, "source": "user"}, "source": {"type": "mcp"}}
            ),
            "permission decision: confirmed=Denied(0) source=user tool_source=mcp",
        )
        self.assertEqual(
            vscode_confirmed_text({"isConfirmed": {"type": 1, "reason": {"value": "read only"}}}),
            "permission decision: confirmed=ConfirmationNotNeeded(1) reason=read only",
        )
        self.assertEqual(vscode_confirmed_text({"isConfirmed": None}), "")
        self.assertEqual(vscode_confirmed_text({}), "")

    def test_thinking_opt_in(self):
        rows = self.rows_for(VsCodeParser(), self.REL, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["Need pytest"])

    def test_legacy_json_session(self):
        rows = self.rows_for(VsCodeParser(), self.LEGACY)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [
                ("system", "session start: responder=GitHub Copilot location=panel"),
                ("system", "model: copilot/gpt-4o"),
                ("user", "where is the config?"),
                ("assistant", "It is in config.toml."),
                ("system", "error: Rate limited"),
            ],
        )
        self.assertTrue(
            all(
                r.session_id == VSCODE_LEGACY_SESSION and r.project_path == "/srv/proj"
                for r in rows
            )
        )
        self.assertEqual(rows[2].model, "copilot/gpt-4o")

    def test_not_wanted(self):
        for rel in (VSCODE_WS + "/workspace.json", ".config/Code/User/settings.json"):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(VsCodeParser().wants(art), rel)
        for rel in (
            "Library/Application Support/Code - Insiders/User/workspaceStorage/x/chatSessions/s.json",
            "AppData/Roaming/VSCodium/User/globalStorage/transferredChatSessions/s.json",
            ".config/Positron/User/globalStorage/emptyWindowChatSessions/s.jsonl",
            ".config/Trae CN/User/workspaceStorage/x/chatSessions/s.jsonl",
            ".vscodium-server-insiders/data/User/workspaceStorage/x/chatSessions/s.jsonl",
            ".positron-server/data/User/globalStorage/emptyWindowChatSessions/s.json",
        ):
            self.assertTrue(VsCodeParser().wants(rel_only(rel)), rel)
        for rel in (
            ".config/Cursor/User/workspaceStorage/x/chatSessions/s.jsonl",
            ".config/Code/User/globalStorage/transferredChatSessions/s.jsonl",
        ):
            self.assertFalse(VsCodeParser().wants(rel_only(rel)), rel)

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(VsCodeParser(), self.REL)
        self.assertEqual(len(rows), 17)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("1 unparseable line", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 7)

    def test_mutation_log(self):
        s = apply_mutation(None, {"kind": 0, "v": {"a": [1, 2, 3], "b": {"c": 1}}})
        s = apply_mutation(s, {"kind": 2, "k": ["a"], "v": [9], "i": 1})
        s = apply_mutation(s, {"kind": 1, "k": ["b", "c"], "v": 2})
        s = apply_mutation(s, {"kind": 3, "k": ["b"]})
        s = apply_mutation(s, {"kind": 2, "k": ["new"], "v": [1]})
        self.assertEqual(s, {"a": [1, 9], "new": [1]})
        with self.assertRaises(ValueError):
            apply_mutation(s, {"kind": 1, "k": ["missing", "x"], "v": 1})


from doubleagent.parsers.kilo_code import KiloCodeParser
from doubleagent.parsers.kilo_code import iter_json_array as kilo_iter_json_array
from doubleagent.parsers.opencode import OpenCodeParser
from doubleagent.parsers.opencode import tool_summary as opencode_tool_summary
from fixtures import (
    KILO_SESSION,
    KILO_TASK,
    OPENCODE_LEGACY_SESSION,
    OPENCODE_SESSION,
    OPENCODE_V2_SESSION,
)


class OpenCodeTests(ParserBase):
    DB = ".local/share/opencode/opencode.db"
    STORAGE = ".local/share/opencode/storage/"

    def test_rows(self):
        rows = self.rows_for(OpenCodeParser(), self.DB)
        self.assertEqual(
            [(r.session_id, r.turn_type) for r in rows],
            [
                (OPENCODE_SESSION, "system"),
                (OPENCODE_V2_SESSION, "system"),
                (OPENCODE_SESSION, "system"),
                (OPENCODE_SESSION, "system"),
                (OPENCODE_SESSION, "user"),
                (OPENCODE_SESSION, "system"),
                (OPENCODE_SESSION, "tool_use"),
                (OPENCODE_SESSION, "tool_result"),
                (OPENCODE_SESSION, "assistant"),
                (OPENCODE_SESSION, "system"),
                (OPENCODE_V2_SESSION, "user"),
                (OPENCODE_V2_SESSION, "system"),
                (OPENCODE_V2_SESSION, "system"),
                (OPENCODE_V2_SESSION, "assistant"),
                (OPENCODE_V2_SESSION, "tool_use"),
                (OPENCODE_V2_SESSION, "tool_result"),
                (OPENCODE_V2_SESSION, "system"),
                (OPENCODE_V2_SESSION, "system"),
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.project_path, r.git_branch),
                ("h1", "alice", "opencode", "/srv/proj", ""),
            )
            self.assertEqual(r.source_file, "/alice/" + self.DB)
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        (
            start,
            _,
            model,
            mode,
            user,
            synth,
            use,
            res,
            asst,
            finish,
            v2user,
            v2model,
            v2mode,
            v2asst,
            v2use,
            v2res,
            v2agent_switch,
            v2model_switch,
        ) = rows
        self.assertIn("session start: Fix bug", start.text)
        # The assistant message names the same model and agent, so no change row.
        self.assertEqual(
            [(r.text, r.timestamp_utc, r.source_line, r.model) for r in (model, mode)],
            [
                (
                    "model: claude-sonnet-4 provider=anthropic",
                    "2026-10-03T09:00:01.000Z",
                    1,
                    "anthropic/claude-sonnet-4",
                ),
                (
                    "permission mode: agent=build",
                    "2026-10-03T09:00:01.000Z",
                    1,
                    "anthropic/claude-sonnet-4",
                ),
            ],
        )
        self.assertEqual(
            [(r.text, r.timestamp_utc) for r in (v2model, v2mode)],
            [
                ("model: gpt-5 provider=openai", "2026-10-03T09:00:12.000Z"),
                ("permission mode: agent=build", "2026-10-03T09:00:12.000Z"),
            ],
        )
        self.assertEqual(
            (v2agent_switch.text, v2agent_switch.timestamp_utc, v2agent_switch.source_line),
            ("permission mode: agent=build -> agent=plan", "2026-10-03T09:00:15.000Z", 3),
        )
        self.assertEqual(
            (
                v2model_switch.text,
                v2model_switch.timestamp_utc,
                v2model_switch.source_line,
                v2model_switch.model,
            ),
            (
                "model: gpt-5 -> gpt-5-mini provider=openai",
                "2026-10-03T09:00:16.000Z",
                4,
                "openai/gpt-5-mini",
            ),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc, user.model),
            ("list files", "2026-10-03T09:00:01.000Z", "anthropic/claude-sonnet-4"),
        )
        self.assertTrue(synth.text.startswith("synthetic: <system-reminder>"))
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text, use.timestamp_utc),
            ("bash", "call_x1", "ls", "2026-10-03T09:00:02.500Z"),
        )
        self.assertEqual(
            (res.tool_name, res.tool_use_id, res.text, res.timestamp_utc),
            ("bash", "call_x1", "a.txt", "2026-10-03T09:00:03.000Z"),
        )
        self.assertEqual(asst.text, "There is one file, a.txt.")
        self.assertEqual(finish.text, "step-finish reason=stop cost=0.01 tokens_in=10 tokens_out=5")
        self.assertEqual(v2user.text, "run the tests")
        self.assertEqual((v2asst.text, v2asst.model), ("Running them.", "openai/gpt-5"))
        self.assertEqual(
            (v2use.tool_use_id, v2use.text, v2res.text), ("call_v2", "pytest -q", "3 passed")
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(OpenCodeParser(), self.DB, include_thinking=True)
        self.assertEqual(
            [r.text for r in rows if r.turn_type == "thinking"], ["user wants a listing"]
        )

    def test_legacy_json_tree(self):
        p = OpenCodeParser()
        rows = self.rows_for(p, self.STORAGE + "session/proj_a1/%s.json" % OPENCODE_LEGACY_SESSION)
        self.assertEqual(
            [(r.turn_type, r.session_id, r.project_path) for r in rows],
            [("system", OPENCODE_LEGACY_SESSION, "/srv/proj")],
        )
        self.assertIn("Old session", rows[0].text)
        rows = self.rows_for(p, self.STORAGE + "message/%s/msg_a.json" % OPENCODE_LEGACY_SESSION)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [
                ("system", "model: claude-sonnet-4 provider=anthropic"),
                ("system", "permission mode: agent=build"),
                ("user", "cat the secrets file"),
            ],
        )
        self.assertEqual(
            rows[0].source_file,
            "/alice/" + self.STORAGE + "message/%s/msg_a.json" % OPENCODE_LEGACY_SESSION,
        )
        self.assertEqual(rows[2].source_file, "/alice/" + self.STORAGE + "part/msg_a/prt_a1.json")
        self.assertEqual({r.timestamp_utc for r in rows}, {"2026-10-02T09:00:01.000Z"})
        # msg_b names the model and agent msg_a did, the message before it in
        # the session directory, so its file yields no model or mode row.
        rows = self.rows_for(p, self.STORAGE + "message/%s/msg_b.json" % OPENCODE_LEGACY_SESSION)
        self.assertEqual(
            [r.turn_type for r in rows], ["tool_use", "tool_result", "assistant", "system"]
        )
        use, res, _asst, err = rows
        self.assertEqual((use.tool_name, use.text), ("read", "/srv/proj/.env"))
        self.assertEqual(res.text, "[error] permission denied")
        self.assertEqual(err.text, "error: APIError overloaded")
        self.assertEqual(
            err.source_file,
            "/alice/" + self.STORAGE + "message/%s/msg_b.json" % OPENCODE_LEGACY_SESSION,
        )
        self.assertTrue(all(r.session_id == OPENCODE_LEGACY_SESSION for r in rows))

    def test_old_per_project_layout(self):
        base = self.home / ".local/share/opencode/project/srv-proj/storage/session"
        (base / "info").mkdir(parents=True)
        (base / "info/ses_old.json").write_text(
            '{"id":"ses_old","title":"Older","time":{"created":1790000000000}}'
        )
        (base / "message/ses_old").mkdir(parents=True)
        (base / "message/ses_old/msg_o.json").write_text(
            '{"id":"msg_o","sessionID":"ses_old","role":"user","time":{"created":1790000001000},'
            '"path":{"cwd":"/srv/proj","root":"/srv/proj"}}'
        )
        (base / "part/ses_old/msg_o").mkdir(parents=True)
        (base / "part/ses_old/msg_o/prt_o.json").write_text(
            '{"id":"prt_o","type":"text","text":"hello"}'
        )
        self.col = open_input(self.tmp / "home", self.cat, host="h1")
        rows = self.rows_for(
            OpenCodeParser(),
            ".local/share/opencode/project/srv-proj/storage/session/message/ses_old/msg_o.json",
        )
        self.assertEqual(
            [(r.turn_type, r.text, r.session_id, r.project_path) for r in rows],
            [("user", "hello", "ses_old", "/srv/proj")],
        )
        rows = self.rows_for(
            OpenCodeParser(),
            ".local/share/opencode/project/srv-proj/storage/session/info/ses_old.json",
        )
        self.assertEqual([r.turn_type for r in rows], ["system"])

    def test_config_parts_and_credentials_not_wanted(self):
        p = OpenCodeParser()
        wanted = sorted(a.rel for a in self.col.artifacts if a.agent == "opencode" and p.wants(a))
        self.assertEqual(
            wanted,
            [
                self.DB,
                self.STORAGE + "message/%s/msg_a.json" % OPENCODE_LEGACY_SESSION,
                self.STORAGE + "message/%s/msg_b.json" % OPENCODE_LEGACY_SESSION,
                self.STORAGE + "session/proj_a1/%s.json" % OPENCODE_LEGACY_SESSION,
            ],
        )

    def test_truncated_part_is_reported_not_fatal(self):
        write_bad_line(self.home / self.STORAGE / "part/msg_b/prt_b2.json")
        rows = self.rows_for(
            OpenCodeParser(), self.STORAGE + "message/%s/msg_b.json" % OPENCODE_LEGACY_SESSION
        )
        self.assertEqual(
            [r.turn_type for r in rows], ["tool_use", "tool_result", "system", "system"]
        )
        self.assertIn("1 part(s) of message msg_b could not be decoded", rows[-1].text)

    def test_truncated_message_file(self):
        write_bad_line(
            self.home / self.STORAGE / "message" / OPENCODE_LEGACY_SESSION / "msg_a.json"
        )
        rows = self.rows_for(
            OpenCodeParser(), self.STORAGE + "message/%s/msg_a.json" % OPENCODE_LEGACY_SESSION
        )
        self.assertEqual(
            [(r.turn_type, r.session_id) for r in rows], [("system", OPENCODE_LEGACY_SESSION)]
        )
        self.assertIn("could not be decoded", rows[0].text)

    def test_bad_data_column_is_reported_not_fatal(self):
        import sqlite3

        con = sqlite3.connect(str(self.home / self.DB))
        con.execute(
            "INSERT INTO part VALUES ('prt_09','msg_02',?,1791018005000,1791018005000,'{\"type\":\"te')",
            (OPENCODE_SESSION,),
        )
        con.execute(
            "INSERT INTO message VALUES ('msg_09',?,1791018006000,1791018006000,'{bad')",
            (OPENCODE_SESSION,),
        )
        con.commit()
        con.close()
        rows = self.rows_for(OpenCodeParser(), self.DB)
        self.assertEqual(len([r for r in rows if r.turn_type == "tool_use"]), 2)
        texts = [r.text for r in rows if r.text.startswith("parser:")]
        self.assertEqual(
            texts,
            [
                "parser: 1 part(s) of message msg_02 could not be decoded",
                "parser: 1 record(s) with undecodable data",
            ],
        )

    def test_tool_summary(self):
        self.assertEqual(opencode_tool_summary({"command": "ls", "description": "list"}), "ls")
        self.assertEqual(opencode_tool_summary({"filePath": "/a"}), "/a")
        self.assertEqual(opencode_tool_summary({"pattern": "foo", "path": "/src"}), "foo | /src")
        self.assertEqual(opencode_tool_summary({"z": 1, "a": 2}), '{"a":2,"z":1}')
        self.assertEqual(opencode_tool_summary(None), "")

    def test_timeline_includes_opencode_and_kilo(self):
        out = self.tmp / "out"
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(
                [
                    "timeline",
                    str(self.tmp / "home"),
                    "-o",
                    str(out),
                    "--agent",
                    "opencode",
                    "--agent",
                    "kilo-code",
                ]
            )
        sessions = {r["session_id"]: r for r in read_jsonl(out / "sessions.jsonl")}
        self.assertEqual(
            set(sessions),
            {
                OPENCODE_SESSION,
                OPENCODE_V2_SESSION,
                OPENCODE_LEGACY_SESSION,
                KILO_SESSION,
                KILO_TASK,
            },
        )
        self.assertEqual(sessions[OPENCODE_SESSION]["models"], ["anthropic/claude-sonnet-4"])
        self.assertEqual(sessions[OPENCODE_SESSION]["tool_calls"], 1)
        self.assertEqual(sessions[KILO_SESSION]["agent"], "kilo-code")
        self.assertEqual({s["project_path"] for s in sessions.values()}, {"/srv/proj"})


class KiloCodeTests(ParserBase):
    DB = ".local/share/kilo/kilo.db"
    TASK = (
        ".config/Code/User/globalStorage/kilocode.kilo-code/tasks/%s/api_conversation_history.json"
        % KILO_TASK
    )

    def test_rows(self):
        rows = self.rows_for(KiloCodeParser(), self.DB)
        # The V2 session_message copy of the tool call is not repeated.
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "system",
                "system",
                "user",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id, r.project_path),
                ("h1", "alice", "kilo-code", KILO_SESSION, "/srv/proj"),
            )
        start, model, mode, user, use, res, switch, mode_switch, user2 = rows
        self.assertEqual(
            [(r.text, r.timestamp_utc) for r in (model, mode)],
            [
                ("model: claude-sonnet-4-5 provider=anthropic", "2026-10-03T10:00:01.000Z"),
                ("permission mode: agent=build", "2026-10-03T10:00:01.000Z"),
            ],
        )
        # The later user message changes model and agent (from the V1 message,
        # since V2 switch records are read only for sessions with no V1 rows).
        self.assertEqual(
            [(r.text, r.timestamp_utc, r.model) for r in (switch, mode_switch)],
            [
                (
                    "model: claude-sonnet-4-5 -> gpt-5 provider=openai",
                    "2026-10-03T10:00:04.000Z",
                    "openai/gpt-5",
                ),
                (
                    "permission mode: agent=build -> agent=plan",
                    "2026-10-03T10:00:04.000Z",
                    "openai/gpt-5",
                ),
            ],
        )
        self.assertEqual(user2.text, "plan the next fix")
        self.assertIn("session start: fix tests", start.text)
        self.assertEqual((user.text, user.model), ("fix the tests", "anthropic/claude-sonnet-4-5"))
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("bash", "call_1", "pytest -q")
        )
        self.assertEqual(
            (res.tool_use_id, res.text, res.timestamp_utc),
            ("call_1", "3 passed", "2026-10-03T10:00:03.000Z"),
        )

    def test_legacy_task(self):
        rows = self.rows_for(KiloCodeParser(), self.TASK)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "system", "assistant", "tool_use", "tool_result", "assistant"],
        )
        for r in rows:
            self.assertEqual(
                (r.agent, r.session_id, r.project_path, r.model),
                ("kilo-code", KILO_TASK, "/srv/proj", ""),
            )
        start, user, env, asst, use, res, final = rows
        self.assertEqual(start.text, "task: fix tests mode=code status=completed")
        self.assertEqual(
            (user.text, user.timestamp_utc, user.source_line),
            ("<task>fix tests</task>", "2026-10-02T10:00:01.000Z", 1),
        )
        self.assertTrue(env.text.startswith("<environment_details>"))
        self.assertEqual(asst.text, "Running the suite.")
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("execute_command", "toolu_01A", "pytest -q"),
        )
        self.assertEqual((res.tool_use_id, res.text), ("toolu_01A", "3 passed"))
        self.assertEqual((final.text, final.source_line), ("All three tests pass.", 5))

    def test_thinking_opt_in(self):
        rows = self.rows_for(KiloCodeParser(), self.TASK, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["tests pass"])

    def test_history_item_preferred_over_index(self):
        task_dir = (self.home / self.TASK).parent
        (task_dir / "history_item.json").write_text(
            '{"id":"%s","task":"from item","workspace":"/srv/other","ts":1}' % KILO_TASK
        )
        rows = self.rows_for(KiloCodeParser(), self.TASK)
        self.assertEqual(rows[0].text, "task: from item")
        self.assertEqual({r.project_path for r in rows}, {"/srv/other"})

    def test_credentials_and_ui_messages_not_wanted(self):
        p = KiloCodeParser()
        wanted = sorted(a.rel for a in self.col.artifacts if a.agent == "kilo-code" and p.wants(a))
        self.assertEqual(wanted, [self.TASK, self.DB])

    def test_truncated_task_file_keeps_earlier_records(self):
        path = self.home / self.TASK
        raw = path.read_bytes()
        path.write_bytes(raw[: raw.index(b'{"type": "reasoning"') + 10])
        rows = self.rows_for(KiloCodeParser(), self.TASK)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "system", "assistant", "tool_use", "tool_result", "system"],
        )
        self.assertIn("record 4", rows[-1].text)
        self.assertIn("3 earlier record(s) kept", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 4)

    def test_bad_line_appended(self):
        write_bad_line(self.home / self.TASK)
        rows = self.rows_for(KiloCodeParser(), self.TASK)
        self.assertEqual(len(rows), 8)
        self.assertIn("unexpected data after the array", rows[-1].text)

    def test_iter_json_array(self):
        self.assertEqual(kilo_iter_json_array('[1, {"a": 2} ,3]'), ([1, {"a": 2}, 3], None))
        self.assertEqual(kilo_iter_json_array("[]"), ([], None))
        self.assertEqual(kilo_iter_json_array('[1, {"a"')[0], [1])
        self.assertEqual(kilo_iter_json_array("[1, 2")[1], "record 3: unexpected end of file")
        self.assertEqual(kilo_iter_json_array('{"a":1}'), ([], "not a JSON array"))


from doubleagent.parsers.cline import ClineParser
from doubleagent.parsers.cline_legacy import iter_json_array
from doubleagent.parsers.roo_code import RooCodeParser
from fixtures import (
    CLINE_CLI_TASK,
    CLINE_OLD_SESSION,
    CLINE_SESSION,
    CLINE_TASK,
    ROO_CLI_TASK,
    ROO_GONE_TASK,
    ROO_TASK,
)

CLINE_GS = ".config/Code/User/globalStorage/saoudrizwan.claude-dev/"
ROO_GS = ".config/Code/User/globalStorage/rooveterinaryinc.roo-cline/"


class ClineTests(ParserBase):
    UI = CLINE_GS + "tasks/%s/ui_messages.json" % CLINE_TASK
    SDK = ".cline/data/sessions/%s/%s" % (CLINE_SESSION, CLINE_SESSION)

    def test_rows(self):
        rows = self.rows_for(ClineParser(), self.UI)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "user",
                "system",
                "tool_use",
                "assistant",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "cline", CLINE_TASK)
            )
            self.assertEqual(
                (r.project_path, r.git_branch, r.model), ("/srv/proj", "", "claude-sonnet-4-5")
            )
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        user, api, read, _text, cmd, out, ckpt, done = rows
        self.assertEqual(
            (user.text, user.timestamp_utc),
            ("fix tests | [1 image(s)]", "2026-10-03T10:00:00.000Z"),
        )
        self.assertEqual(
            api.text,
            "api_req_started: tokensIn=1200 tokensOut=80 cacheWrites=0 cacheReads=900 cost=0.0041",
        )
        self.assertEqual(
            (read.tool_name, read.tool_use_id, read.text),
            ("readFile", "1791021602000", "src/app.py | /srv/proj/src/app.py"),
        )
        self.assertEqual(
            (cmd.tool_name, cmd.tool_use_id, cmd.text),
            ("execute_command", "1791021604000", "pytest -q"),
        )
        self.assertEqual((out.tool_use_id, out.text), ("1791021604000", "3 passed"))
        self.assertEqual(ckpt.text, "checkpoint_created: abc123")
        self.assertEqual(done.text, "All tests pass.")
        self.assertEqual(
            [r.source_line for r in rows], [1, 2, 4, 5, 6, 7, 8, 9]
        )  # empty ask at 10 skipped

    def test_thinking_opt_in(self):
        rows = self.rows_for(ClineParser(), self.UI, include_thinking=True)
        self.assertEqual(
            [r.text for r in rows if r.turn_type == "thinking"], ["read the test first"]
        )
        rows = self.rows_for(ClineParser(), self.SDK + ".messages.json", include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["run the suite"])

    def test_api_history_only_without_ui_messages(self):
        self.assertEqual(
            self.rows_for(
                ClineParser(), CLINE_GS + "tasks/%s/api_conversation_history.json" % CLINE_TASK
            ),
            [],
        )
        rows = self.rows_for(
            ClineParser(), ".cline/data/tasks/%s/api_conversation_history.json" % CLINE_CLI_TASK
        )
        self.assertEqual([r.turn_type for r in rows], ["user", "tool_use", "tool_result"])
        # No per-message timestamps: every row inherits the task id's time.
        self.assertEqual({r.timestamp_utc for r in rows}, {"2026-10-03T09:55:00.000Z"})
        self.assertEqual({r.project_path for r in rows}, {"/srv/proj"})
        use, res = rows[1], rows[2]
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("execute_command", "toolu_01A", "pytest -q"),
        )
        self.assertEqual((res.tool_use_id, res.text), ("toolu_01A", "3 passed"))

    def test_history_and_metadata(self):
        rows = self.rows_for(ClineParser(), CLINE_GS + "state/taskHistory.json")
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            (rows[0].turn_type, rows[0].session_id, rows[0].project_path),
            ("system", CLINE_TASK, "/srv/proj"),
        )
        self.assertTrue(rows[0].text.startswith("task: fix tests | tokensIn=1200"))
        rows = self.rows_for(ClineParser(), CLINE_GS + "tasks/%s/task_metadata.json" % CLINE_TASK)
        self.assertEqual(
            [r.text.split(":")[0] for r in rows],
            [
                "environment",
                "model",
                "permission mode",
                "permission mode",
                "file cline_read",
                "model",
            ],
        )
        self.assertEqual(rows[4].timestamp_utc, "2026-10-03T10:00:02.000Z")
        self.assertIn("src/app.py", rows[4].text)

    def test_model_and_mode_rows_from_model_usage(self):
        rows = self.rows_for(ClineParser(), CLINE_GS + "tasks/%s/task_metadata.json" % CLINE_TASK)
        got = [
            (r.turn_type, r.text, r.timestamp_utc, r.model, r.session_id, r.source_line)
            for r in rows
            if r.text.startswith(("model", "permission"))
        ]
        self.assertEqual(
            got,
            [
                (
                    "system",
                    "model: claude-sonnet-4-5 model_provider_id=anthropic mode=plan",
                    "2026-10-03T10:00:00.300Z",
                    "claude-sonnet-4-5",
                    CLINE_TASK,
                    1,
                ),
                (
                    "system",
                    "permission mode: plan",
                    "2026-10-03T10:00:00.300Z",
                    "claude-sonnet-4-5",
                    CLINE_TASK,
                    1,
                ),
                # the second entry changes only the mode
                (
                    "system",
                    "permission mode: plan -> act",
                    "2026-10-03T10:00:00.500Z",
                    "claude-sonnet-4-5",
                    CLINE_TASK,
                    2,
                ),
                (
                    "system",
                    "model: claude-sonnet-4-5 -> claude-opus-4-5 model_provider_id=anthropic "
                    "mode=act",
                    "2026-10-03T10:00:08.000Z",
                    "claude-opus-4-5",
                    CLINE_TASK,
                    3,
                ),
            ],
        )
        self.assertEqual({r.project_path for r in rows}, {"/srv/proj"})

    def test_sdk_session(self):
        rows = self.rows_for(ClineParser(), self.SDK + ".json")
        self.assertEqual(
            [r.text.split(":")[0] for r in rows], ["session start", "model", "session end"]
        )
        self.assertEqual(
            (rows[0].session_id, rows[0].project_path, rows[0].timestamp_utc),
            (CLINE_SESSION, "/srv/proj", "2026-10-03T10:01:40.000Z"),
        )
        self.assertIn("title=fix tests", rows[0].text)
        self.assertNotIn("model=", rows[0].text)  # the model has its own row
        self.assertEqual(
            (rows[1].turn_type, rows[1].text, rows[1].model, rows[1].timestamp_utc),
            (
                "system",
                "model: claude-sonnet-4-5 provider=anthropic",
                "claude-sonnet-4-5",
                "2026-10-03T10:01:40.000Z",
            ),
        )
        self.assertEqual((rows[1].session_id, rows[1].project_path), (CLINE_SESSION, "/srv/proj"))
        rows = self.rows_for(ClineParser(), self.SDK + ".messages.json")
        self.assertEqual(
            [r.turn_type for r in rows], ["user", "tool_use", "tool_result", "system", "assistant"]
        )
        _user, use, res, switch, asst = rows
        # m2 names the manifest's model, so no row; m4 switches
        self.assertEqual(
            (switch.text, switch.model, switch.timestamp_utc, switch.source_line),
            (
                "model: claude-sonnet-4-5 -> claude-opus-4-5 provider=anthropic",
                "claude-opus-4-5",
                res.timestamp_utc,
                4,
            ),
        )
        self.assertEqual(asst.model, "claude-opus-4-5")
        self.assertEqual({r.session_id for r in rows}, {CLINE_SESSION})
        self.assertEqual({r.project_path for r in rows}, {"/srv/proj"})
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("bash", "call_1", "pytest -q")
        )
        self.assertEqual((res.tool_name, res.tool_use_id, res.text), ("bash", "call_1", "3 passed"))
        self.assertEqual(asst.timestamp_utc, res.timestamp_utc)  # no ts: previous message's time
        self.assertEqual([r.source_line for r in rows], [1, 2, 3, 4, 4])

    def test_sdk_messages_without_manifest_start_from_first_model(self):
        (self.home / (self.SDK + ".json")).unlink()
        rows = self.rows_for(ClineParser(), self.SDK + ".messages.json")
        models = [(r.text, r.source_line) for r in rows if r.text.startswith("model:")]
        self.assertEqual(
            models,
            [
                ("model: claude-sonnet-4-5 provider=anthropic", 2),
                ("model: claude-sonnet-4-5 -> claude-opus-4-5 provider=anthropic", 4),
            ],
        )

    def test_sessions_db_only_lists_sessions_without_manifest(self):
        rows = self.rows_for(ClineParser(), ".cline/data/db/sessions.db")
        self.assertEqual([r.session_id for r in rows], [CLINE_OLD_SESSION] * 2)
        self.assertEqual(rows[0].timestamp_utc, "2026-10-02T23:00:00.000Z")
        self.assertIn("an older deleted session", rows[0].text)
        self.assertEqual(
            (rows[1].text, rows[1].timestamp_utc),
            ("model: claude-sonnet-4-5 provider=anthropic", "2026-10-02T23:00:00.000Z"),
        )

    def test_config_and_secrets_not_wanted(self):
        p = ClineParser()
        for rel in (
            CLINE_GS + "settings/cline_mcp_settings.json",
            ".cline/data/secrets.json",
            self.SDK + ".compaction.json",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(p.wants(art), rel)

    def test_wants_any_editor_prefix(self):
        p = ClineParser()
        art = next(a for a in self.col.artifacts if a.rel == self.UI)
        for prefix in (
            "Library/Application Support/Cursor/User/globalStorage/",
            "AppData/Roaming/Code - Insiders/User/globalStorage/",
            ".vscode-server/data/User/globalStorage/",
        ):
            art.rel = prefix + "saoudrizwan.claude-dev/tasks/1/ui_messages.json"
            self.assertTrue(p.wants(art), art.rel)
        art.rel = ".config/Code/User/globalStorage/other.ext/tasks/1/ui_messages.json"
        self.assertFalse(p.wants(art))

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.UI)
        rows = self.rows_for(ClineParser(), self.UI)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("after the JSON array", rows[-1].text)

    def test_array_cut_mid_write_keeps_earlier_records(self):
        path = self.home / self.UI
        data = path.read_text(encoding="utf-8")
        path.write_text(data[: data.index('"say": "command_output"') - 30], encoding="utf-8")
        rows = self.rows_for(ClineParser(), self.UI)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["user", "system", "tool_use", "assistant", "tool_use", "system"],
        )
        self.assertEqual(rows[-1].source_line, 7)
        self.assertIn("record 7", rows[-1].text)
        sdk = self.home / (self.SDK + ".messages.json")
        data = sdk.read_text(encoding="utf-8")
        sdk.write_text(data[: data.index('"id": "m3"') - 2], encoding="utf-8")
        rows = self.rows_for(ClineParser(), self.SDK + ".messages.json")
        self.assertEqual([r.turn_type for r in rows], ["user", "tool_use", "system"])
        self.assertEqual(rows[0].timestamp_utc, "2026-10-03T10:01:40.000Z")

    def test_sessions_summary(self):
        rows = []
        for parser in (ClineParser(), RooCodeParser()):
            for a in self.col.artifacts_for(parser.agent):
                if parser.wants(a):
                    rows.extend(parser.parse(a, Options()))
        sessions = {s.session_id: s for s in summarise(rows)}
        self.assertEqual(
            set(sessions),
            {
                CLINE_TASK,
                CLINE_CLI_TASK,
                CLINE_SESSION,
                CLINE_OLD_SESSION,
                ROO_TASK,
                ROO_CLI_TASK,
                ROO_GONE_TASK,
            },
        )
        s = sessions[CLINE_TASK]
        # task_metadata.json's model_usage records the later switch to Opus
        self.assertEqual(
            (s.models, s.user_turns, s.assistant_turns, s.tool_calls),
            ({"claude-sonnet-4-5": None, "claude-opus-4-5": None}, 1, 2, 2),
        )
        self.assertTrue(s.source_file.endswith("ui_messages.json"), s.source_file)
        self.assertEqual(sessions[CLINE_SESSION].first_timestamp_utc, "2026-10-03T10:01:40.000Z")
        self.assertEqual(sessions[ROO_TASK].project_path, "/srv/proj")

    def test_json_array_reader(self):
        p = self.tmp / "a.json"
        for text, items, nerr in (
            ("[]", [], 0),
            ('[{"a":1}, {"b":2}]', [{"a": 1}, {"b": 2}], 0),
            ('[{"a":1}, {"b":', [{"a": 1}], 1),
            ('{"a":1}', [], 1),
        ):
            p.write_text(text, encoding="utf-8")
            errors = []
            self.assertEqual([v for _, v in iter_json_array(p, errors)], items, text)
            self.assertEqual(len(errors), nerr, text)


class RooCodeTests(ParserBase):
    UI = ROO_GS + "tasks/%s/ui_messages.json" % ROO_TASK
    CLI_API = ".vscode-mock/global-storage/tasks/%s/api_conversation_history.json" % ROO_CLI_TASK

    def test_rows(self):
        rows = self.rows_for(RooCodeParser(), self.UI)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "user",
                "system",
                "tool_use",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
                "user",
                "assistant",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "roo-code", ROO_TASK)
            )
            self.assertEqual((r.project_path, r.git_branch, r.model), ("/srv/proj", "", ""))
        user, api, diff, cmd, out, condense, ask, feedback, _done = rows
        self.assertEqual(
            (user.text, user.timestamp_utc), ("rename the helper", "2026-10-03T10:03:20.000Z")
        )
        self.assertIn("apiProtocol=anthropic", api.text)
        self.assertEqual((diff.tool_name, diff.text), ("appliedDiff", "src/util.py | -old\n+new"))
        self.assertEqual((out.tool_use_id, out.text), (cmd.tool_use_id, "1 passed"))
        self.assertTrue(condense.text.startswith("condense_context: prevContextTokens=9000"))
        self.assertIn("Renamed helper; tests pass.", condense.text)
        self.assertEqual(ask.text, "Commit now? | yes; no")
        self.assertEqual(feedback.text, "yes")

    def test_thinking_opt_in(self):
        rows = self.rows_for(RooCodeParser(), self.CLI_API)
        self.assertNotIn("thinking", [r.turn_type for r in rows])
        rows = self.rows_for(RooCodeParser(), self.CLI_API, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["check the runner"])

    def test_api_history_only_without_ui_messages(self):
        self.assertEqual(
            self.rows_for(
                RooCodeParser(), ROO_GS + "tasks/%s/api_conversation_history.json" % ROO_TASK
            ),
            [],
        )
        rows = self.rows_for(RooCodeParser(), self.CLI_API)
        self.assertEqual([r.turn_type for r in rows], ["user", "tool_use", "tool_result"])
        self.assertEqual(
            [r.timestamp_utc for r in rows],  # Roo records carry their own ts
            ["2026-10-03T10:05:00.000Z", "2026-10-03T10:05:02.000Z", "2026-10-03T10:05:03.000Z"],
        )
        self.assertEqual(
            {(r.session_id, r.project_path) for r in rows}, {(ROO_CLI_TASK, "/srv/proj")}
        )
        self.assertEqual((rows[1].tool_use_id, rows[2].tool_use_id), ("toolu_01A", "toolu_01A"))

    def test_history_item_and_index(self):
        rows = self.rows_for(RooCodeParser(), ROO_GS + "tasks/%s/history_item.json" % ROO_TASK)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].text.startswith("task: rename the helper"))
        self.assertIn("mode=code", rows[0].text)
        rows = self.rows_for(RooCodeParser(), ROO_GS + "tasks/_index.json")
        self.assertEqual(
            [r.session_id for r in rows], [ROO_GONE_TASK]
        )  # tasks on disk are not repeated
        rows = self.rows_for(RooCodeParser(), ROO_GS + "tasks/%s/task_metadata.json" % ROO_TASK)
        self.assertEqual([r.text.split(":")[0] for r in rows], ["file roo_read", "file roo_edit"])

    def test_secrets_not_wanted(self):
        art = next(
            a for a in self.col.artifacts if a.rel == ".vscode-mock/global-storage/secrets.json"
        )
        self.assertFalse(RooCodeParser().wants(art))
        self.assertFalse(ClineParser().wants(art))

    CLI_HISTORY = ".roo/cli-history.json"

    def test_secondary(self):
        p = RooCodeParser()
        self.assertTrue(p.secondary(self.artifact(self.CLI_HISTORY)))
        for rel in (self.UI, self.CLI_API, ROO_GS + "tasks/_index.json"):
            self.assertFalse(p.secondary(self.artifact(rel)), rel)
        self.assertEqual(p.secondary_tolerance(self.artifact(self.CLI_HISTORY)), 2.0)

    def test_cli_history_rows(self):
        p = RooCodeParser()
        self.assertTrue(p.wants(self.artifact(self.CLI_HISTORY)))
        rows = self.rows_for(p, self.CLI_HISTORY)
        self.assertEqual(
            [(r.source_line, r.turn_type, r.text) for r in rows],
            [
                (1, "user", "rename the helper"),
                (2, "user", "yes"),
                (3, "user", "/new"),
                (6, "user", "summarise the open issues"),
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id, r.project_path, r.timestamp_utc),
                ("h1", "alice", "roo-code", "", "", ""),
            )
            self.assertTrue(r.source_file.endswith(self.CLI_HISTORY), r.source_file)
        # The settings file beside it is configuration, not history.
        self.assertFalse(p.wants(self.artifact(".roo/cli-settings.json")))

    def test_cli_history_truncated(self):
        write_bad_line(self.home / self.CLI_HISTORY)
        rows = self.rows_for(RooCodeParser(), self.CLI_HISTORY)
        self.assertEqual([r.turn_type for r in rows], ["user"] * 4 + ["system"])
        self.assertEqual(
            rows[-1].text, "parser: cli-history.json unparseable after its entries array"
        )

    def test_cli_history_malformed(self):
        path = self.home / self.CLI_HISTORY
        path.write_text('{"version": 1, "entries": ["rename the helper", "ye', encoding="utf-8")
        rows = self.rows_for(RooCodeParser(), self.CLI_HISTORY)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [("user", "rename the helper"), ("system", rows[1].text)],
        )
        self.assertTrue(rows[1].text.startswith("parser: record 2 unparseable"), rows[1].text)
        path.write_text('{"version": 1}', encoding="utf-8")
        rows = self.rows_for(RooCodeParser(), self.CLI_HISTORY)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [("system", "parser: cli-history.json has no entries array")],
        )

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.UI)
        rows = self.rows_for(RooCodeParser(), self.UI)
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("parser:", rows[-1].text)


from doubleagent.parsers.tabby import TabbyParser
from fixtures import TABBY_BACKUP_REL, TABBY_EVENTS_REL, TABBY_REL, TABBY_SECRETS


class TabbyTests(ParserBase):
    def test_rows(self):
        rows = self.rows_for(TabbyParser(), TABBY_REL)
        self.assertEqual([r.turn_type for r in rows], ["system", "user", "assistant", "system"])
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.git_branch, r.model), ("h1", "alice", "tabby", "", "")
            )
            self.assertTrue(r.source_file.endswith(TABBY_REL), r.source_file)
        start, user, asst, select = rows
        for r in (start, user, asst):
            self.assertEqual((r.session_id, r.project_path), ("7", "https://github.com/acme/app"))
        self.assertEqual(
            (start.timestamp_utc, start.text),
            (
                "2026-10-01T10:00:00.000Z",
                "thread start | owner alice@example.com (Alice) | relevant questions: How is the cache invalidated?",
            ),
        )
        self.assertEqual(
            (user.text, user.source_line),
            ("Where is the cache cleared? [attachments: client_code src/cache.rs:10]", 1),
        )
        self.assertEqual(
            (asst.timestamp_utc, asst.text),
            (
                "2026-10-01T10:00:02.000Z",
                "In `clear()` in src/cache.rs. [attachments: code https://github.com/acme/app@abc123 src/cache.rs:10]",
            ),
        )
        self.assertEqual(
            (select.session_id, select.timestamp_utc, select.text),
            (
                "cmpl-7f3a",
                "2026-10-01T10:00:01.000Z",
                "select choice 0 | user=alice@example.com (Alice) | view=view-1 | elapsed=1377ms",
            ),
        )

    def test_thinking_opt_in(self):
        # Tabby stores no reasoning; the flag must not invent rows.
        self.assertEqual(
            len(self.rows_for(TabbyParser(), TABBY_REL, include_thinking=True)),
            len(self.rows_for(TabbyParser(), TABBY_REL)),
        )

    def test_backup_and_event_log(self):
        rows = self.rows_for(TabbyParser(), TABBY_BACKUP_REL)
        self.assertEqual([r.turn_type for r in rows], ["system", "system", "user", "assistant"])
        self.assertIn("backup database", rows[0].text)
        self.assertTrue(all(r.source_file.endswith(TABBY_BACKUP_REL) for r in rows))
        self.assertEqual(
            {(r.session_id, r.project_path) for r in rows[1:]},
            {("3", "https://github.com/acme/ops")},
        )
        self.assertIn("ephemeral", rows[1].text)
        self.assertEqual(
            rows[3].text,
            "Run `select * from users`. [attachments: code https://github.com/acme/ops db.sql]",
        )
        rows = self.rows_for(TabbyParser(), TABBY_EVENTS_REL)
        self.assertEqual(
            [(r.turn_type, r.session_id) for r in rows],
            [
                ("system", "cmpl-7f3a"),
                ("user", "cmpl-7f3a"),
                ("assistant", "cmpl-7f3a"),
                ("system", "cmpl-7f3a"),
                ("system", ""),
            ],
        )
        self.assertEqual(
            rows[0].text,
            "completion | user=1 | language=python | file=app/math.py | client=tabby-agent/1.9",
        )
        self.assertEqual(
            (rows[1].text, rows[1].timestamp_utc, rows[1].project_path),
            ("def add(a, b):", "2025-10-01T10:00:00.123Z", "https://github.com/acme/app"),
        )
        self.assertEqual(rows[2].text, "return a + b")
        self.assertEqual(
            (rows[3].text, rows[3].timestamp_utc),
            ("select choice 0 | user=1 | view=view-1 | elapsed=1377ms", "2025-10-01T10:00:01.500Z"),
        )
        self.assertEqual(rows[4].text, "chat_completion")

    def test_config_and_sidecars_not_wanted(self):
        p = TabbyParser()
        seen = set()
        for a in self.col.artifacts:
            if a.agent == "tabby":
                seen.add(a.rel)
                self.assertEqual(
                    p.wants(a), a.rel in (TABBY_REL, TABBY_BACKUP_REL, TABBY_EVENTS_REL), a.rel
                )
        self.assertIn(".tabby/config.toml", seen)

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / TABBY_EVENTS_REL)
        rows = self.rows_for(TabbyParser(), TABBY_EVENTS_REL)
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            (rows[-1].turn_type, rows[-1].text),
            ("system", "parser: 1 unparseable line(s), first at line 4"),
        )

    def test_bad_payload_is_reported_not_fatal(self):
        import sqlite3

        con = sqlite3.connect(str(self.home / TABBY_REL))
        con.execute(
            "INSERT INTO user_events(user_id,kind,created_at,payload) VALUES(1,'view','2026-10-01 10:00:05','{\"view\":')"
        )
        con.commit()
        con.close()
        rows = self.rows_for(TabbyParser(), TABBY_REL)
        self.assertEqual(
            [r.turn_type for r in rows], ["system", "user", "assistant", "system", "system"]
        )
        self.assertIn("payload did not parse", rows[-1].text)

    def test_secret_columns_never_reach_output(self):
        for rel in (TABBY_REL, TABBY_BACKUP_REL):
            for r in self.rows_for(TabbyParser(), rel):
                for value in r.as_dict().values():
                    for secret in TABBY_SECRETS:
                        self.assertNotIn(secret, str(value))
        out = self.tmp / "out"
        buf = io.StringIO()
        import contextlib

        with contextlib.redirect_stdout(buf):
            rc = cli.main(
                [
                    "timeline",
                    str(self.tmp / "home"),
                    "-o",
                    str(out),
                    "--host",
                    "h1",
                    "--agent",
                    "tabby",
                ]
            )
        self.assertEqual(rc, 0, buf.getvalue())
        produced = [p for p in out.rglob("*") if p.is_file()]
        self.assertTrue(produced)
        for p in produced:
            data = p.read_bytes()
            for secret in TABBY_SECRETS:
                self.assertNotIn(secret.encode(), data, p)
        for secret in TABBY_SECRETS:
            self.assertNotIn(secret, buf.getvalue())


from doubleagent.parsers.openhands import OpenHandsParser
from doubleagent.parsers.shellgpt import ShellGptParser, load_messages
from fixtures import (
    OPENHANDS_CLI_CONV,
    OPENHANDS_CONV,
    OPENHANDS_LEGACY,
    SHELLGPT_CHAT,
    SHELLGPT_LEGACY_CHAT,
)


class OpenHandsTests(ParserBase):
    CANVAS = ".openhands/agent-canvas/dev_conversations/%s/events/" % OPENHANDS_CONV
    CLI = ".openhands/conversations/%s/events/" % OPENHANDS_CLI_CONV

    def event(self, base, n):
        return next(a.rel for a in self.col.artifacts if a.rel.startswith(base + "event-%05d-" % n))

    def conversation(self, base, **kw):
        rows = []
        for a in sorted(self.col.artifacts, key=lambda a: a.rel):
            if a.rel.startswith(base) and OpenHandsParser().wants(a):
                rows.extend(OpenHandsParser().parse(a, Options(**kw)))
        return rows

    def test_rows(self):
        rows = self.conversation(self.CANVAS)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id),
                ("h1", "alice", "openhands", OPENHANDS_CONV),
            )
            self.assertEqual(
                (r.project_path, r.git_branch, r.model),
                ("/srv/proj", "", "litellm_proxy/claude-sonnet-4-5"),
            )
            self.assertEqual(r.source_line, 1)
        header, model, prompt, user, ls, out, view, reject, decision, asst = rows
        self.assertTrue(header.text.startswith("conversation start | List files"), header.text)
        self.assertEqual(
            (model.text, model.timestamp_utc),
            ("model: litellm_proxy/claude-sonnet-4-5", "2026-10-01T10:00:00.000Z"),
        )
        self.assertIn("corrected by UTC+02:00", header.text)
        self.assertEqual(header.timestamp_utc, "2026-10-01T10:00:00.000Z")
        self.assertEqual(prompt.text, "system prompt, 2 tools: You are OpenHands agent.")
        # Naive local 12:00:01 anchored by meta.json created_at 10:00:00Z.
        self.assertEqual(
            (user.text, user.timestamp_utc), ("list the files", "2026-10-01T10:00:01.000Z")
        )
        self.assertEqual(
            (ls.tool_name, ls.tool_use_id, ls.text),
            ("terminal", "call_1", "ls security_risk=LOW"),
        )
        self.assertEqual(
            (out.tool_use_id, out.text, out.timestamp_utc),
            ("call_1", "README.md", "2026-10-01T10:00:04.000Z"),
        )
        self.assertEqual((view.tool_name, view.text), ("file_editor", "view /srv/proj/README.md"))
        self.assertEqual(
            (reject.tool_use_id, reject.text), ("call_2", "[rejected by user] not that file")
        )
        self.assertEqual(
            (decision.tool_name, decision.tool_use_id, decision.text, decision.timestamp_utc),
            (
                "file_editor",
                "call_2",
                "permission decision: rejected rejection_source=user not that file",
                reject.timestamp_utc,
            ),
        )
        self.assertEqual(rows.index(decision), rows.index(reject) + 1)
        self.assertEqual(asst.text, "The project has a README.")
        self.assertTrue(asst.source_file.endswith(".json"))

    def test_no_meta_emits_naive_time_as_utc(self):
        rows = self.conversation(self.CLI)
        self.assertEqual(rows[0].turn_type, "system")
        self.assertIn("emitted as if UTC", rows[0].text)
        self.assertEqual(rows[1].text, "model: litellm_proxy/claude-sonnet-4-5")
        self.assertEqual(rows[3].timestamp_utc, "2026-10-02T08:30:01.000Z")
        self.assertEqual({r.session_id for r in rows}, {OPENHANDS_CLI_CONV})

    def test_thinking_opt_in(self):
        self.assertNotIn("thinking", [r.turn_type for r in self.conversation(self.CANVAS)])
        rows = self.conversation(self.CANVAS, include_thinking=True)
        self.assertEqual(
            [r.text for r in rows if r.turn_type == "thinking"],
            ["I will run ls.", "check the readme"],
        )

    def test_legacy_session_reported_once(self):
        rows = [
            r
            for a in self.col.artifacts
            if OpenHandsParser().wants(a) and "/sessions/" in a.rel
            for r in OpenHandsParser().parse(a, Options())
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].session_id, rows[0].turn_type), (OPENHANDS_LEGACY, "system"))
        self.assertIn("3 event files, not parsed", rows[0].text)

    def test_secrets_not_wanted(self):
        for rel in (
            ".openhands/settings.json",
            ".openhands/secrets.json",
            ".openhands/agent-canvas/dev_conversations/%s/meta.json" % OPENHANDS_CONV,
            ".openhands/agent-canvas/dev_conversations/%s/base_state.json" % OPENHANDS_CONV,
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(OpenHandsParser().wants(art), rel)

    def test_truncated_line_is_reported_not_fatal(self):
        rel = self.event(self.CANVAS, 6)
        write_bad_line(self.home / rel)
        rows = self.rows_for(OpenHandsParser(), rel)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].turn_type, "system")
        self.assertIn("parser:", rows[0].text)
        self.assertEqual(len(self.conversation(self.CANVAS)), 10)  # the other events still parse


class ShellGptTests(ParserBase):
    CHAT = "AppData/Local/Temp/chat_cache/" + SHELLGPT_CHAT
    LEGACY = "AppData/Local/Temp/shell_gpt/chat_cache/" + SHELLGPT_LEGACY_CHAT

    def test_rows(self):
        rows = self.rows_for(ShellGptParser(), self.CHAT)
        self.assertEqual(
            [r.turn_type for r in rows], ["system", "user", "tool_use", "tool_result", "assistant"]
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "shellgpt", SHELLGPT_CHAT)
            )
            self.assertEqual(
                (r.timestamp_utc, r.project_path, r.git_branch, r.model, r.source_line),
                ("", "", "", "", 1),
            )
        system, user, use, result, asst = rows
        self.assertTrue(system.text.startswith("You are ShellGPT"))
        self.assertEqual(user.text, "what is listening on port 8080")
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("execute_shell_command", "call_Q1w2e3r4", "ss -ltnp | grep 8080"),
        )
        self.assertEqual(
            (result.tool_name, result.tool_use_id), ("execute_shell_command", "call_Q1w2e3r4")
        )
        self.assertTrue(result.text.startswith("Exit code: 0, Output:\nLISTEN"))
        self.assertTrue(asst.text.endswith("is listening on 8080."))

    def test_legacy_function_call(self):
        rows = self.rows_for(ShellGptParser(), self.LEGACY)
        self.assertEqual(
            [r.turn_type for r in rows], ["system", "user", "tool_use", "tool_result", "assistant"]
        )
        use, result = rows[2], rows[3]
        self.assertEqual((use.tool_use_id, use.text), ("function_call_2", "df -h /"))
        self.assertEqual(
            (result.tool_use_id, result.tool_name), ("function_call_2", "execute_shell_command")
        )

    def test_thinking_opt_in(self):
        # ShellGPT stores no reasoning; the option changes nothing.
        self.assertEqual(
            [
                r.turn_type
                for r in self.rows_for(ShellGptParser(), self.CHAT, include_thinking=True)
            ],
            [r.turn_type for r in self.rows_for(ShellGptParser(), self.CHAT)],
        )

    def test_not_wanted(self):
        for rel in (
            ".config/shell_gpt/.sgptrc",
            "AppData/Local/Temp/shell_gpt/cache/0cc175b9c0f1b6a831c399e269772661",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(ShellGptParser().wants(art), rel)

    def test_loose_temp_directory_is_wanted(self):
        art = next(a for a in self.col.artifacts if a.rel == self.CHAT)
        art.rel = "tmp/chat_cache/" + SHELLGPT_CHAT
        self.assertTrue(ShellGptParser().wants(art))

    def test_truncated_line_is_reported_not_fatal(self):
        path = self.home / self.CHAT
        raw = path.read_text(encoding="utf-8")
        path.write_text(raw[: raw.index('{"role": "tool"') + 20], encoding="utf-8")
        rows = self.rows_for(ShellGptParser(), self.CHAT)
        self.assertEqual([r.turn_type for r in rows], ["system", "user", "tool_use", "system"])
        self.assertIn("parser: truncated after 3 message(s)", rows[-1].text)
        msgs, err = load_messages("not json")
        self.assertEqual(msgs, [])
        self.assertTrue(err)


from doubleagent.parsers.letta import LettaParser, decode_key
from doubleagent.parsers.little_coder import LittleCoderParser
from doubleagent.parsers.pi import PiParser
from doubleagent.parsers.pi import args_summary as pi_args_summary
from fixtures import (
    LC_FILE,
    LC_SESSION,
    LETTA_AGENT,
    LETTA_CONV,
    LETTA_LOCAL_CONV,
    LETTA_LOCAL_DIR,
    PI_DIR,
    PI_EXPERIMENTAL,
    PI_FILE,
    PI_FORK,
    PI_FORK_FILE,
    PI_SESSION,
    PI_TRUST,
    _jsonl,
    pi_session_records,
)


class PiTests(ParserBase):
    REL = PI_DIR + PI_FILE
    FORK = PI_DIR + PI_FORK_FILE
    LC = PI_DIR + LC_FILE

    def test_rows(self):
        rows = self.rows_for(PiParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "tool_use",
                "tool_result",
                "system",
                "system",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "pi", PI_SESSION)
            )
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", ""))
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        start, mc, user, use, result, bash, bash_out, info, change = rows
        self.assertEqual(
            (start.text, start.timestamp_utc),
            ("session start: version=3 cwd=/srv/proj", "2026-10-01T09:00:00.000Z"),
        )
        # The model_change entry starts the model; the assistant message on
        # line 4 names the same model and adds no row.
        self.assertEqual(
            (mc.model, mc.text, mc.timestamp_utc),
            (
                "claude-sonnet-4-5",
                "model: claude-sonnet-4-5 provider=anthropic",
                "2026-10-01T09:00:00.100Z",
            ),
        )
        self.assertEqual(
            (change.model, change.text, change.timestamp_utc),
            (
                "gpt-5",
                "model: claude-sonnet-4-5 -> gpt-5 provider=openai",
                "2026-10-01T09:00:11.000Z",
            ),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc), ("fix the failing test", "2026-10-01T09:00:01.000Z")
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.model, use.text),
            ("bash", "toolu_01", "claude-sonnet-4-5", "npm test"),
        )
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text), ("bash", "toolu_01", "1 failing")
        )
        self.assertEqual(
            (bash.tool_name, bash.tool_use_id, bash.text), ("bash", "5e6f7081", "git status")
        )
        self.assertEqual((bash_out.tool_use_id, bash_out.text), ("5e6f7081", "M src/a.ts"))
        self.assertEqual(info.text, "session_info: name=test fix")
        self.assertEqual(
            [r.source_line for r in rows], [1, 2, 3, 4, 5, 6, 6, 8, 9]
        )  # the label on line 7 is skipped
        self.assertEqual(
            pi_args_summary({"edits": [{"oldText": "a", "newText": "b"}], "path": "src/a.ts"}),
            "src/a.ts",
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(PiParser(), self.REL, include_thinking=True)
        thinking = [r for r in rows if r.turn_type == "thinking"]
        self.assertEqual(
            [(r.text, r.model) for r in thinking], [("run the tests first", "claude-sonnet-4-5")]
        )

    def test_fork_drops_entries_copied_from_parent(self):
        rows = self.rows_for(PiParser(), self.FORK)
        self.assertEqual([r.turn_type for r in rows], ["system", "system", "system", "assistant"])
        self.assertIn("parentSession=/home/alice/" + self.REL, rows[0].text)
        self.assertTrue(
            rows[1].text.startswith("fork: 3 entries copied from the parent session"), rows[1].text
        )
        # The copied model_change is dropped, so the fork's own first
        # assistant message starts its model.
        self.assertEqual(rows[2].text, "model: claude-sonnet-4-5 provider=anthropic")
        self.assertEqual((rows[3].session_id, rows[3].text), (PI_FORK, "Trying another way."))

    def test_fork_kept_whole_without_parent(self):
        (self.home / self.REL).unlink()
        rows = self.rows_for(PiParser(), self.FORK)
        self.assertEqual(
            [r.turn_type for r in rows], ["system", "system", "user", "tool_use", "assistant"]
        )
        self.assertEqual({r.session_id for r in rows}, {PI_FORK})

    def test_little_coder_session_is_flagged(self):
        rows = self.rows_for(PiParser(), self.LC)
        self.assertEqual({r.agent for r in rows}, {"pi"})
        last = rows[-1]
        self.assertEqual((last.turn_type, last.session_id), ("system", LC_SESSION))
        self.assertTrue(last.text.startswith("session driven by little-coder"), last.text)
        for why in ("lc-skills", "llamacpp", "checkpoints"):
            self.assertIn(why, last.text)
        self.assertIn(
            "custom_message lc-skills: ## Skill: edit\nUse the edit tool.", [r.text for r in rows]
        )
        plain = self.rows_for(PiParser(), self.REL)
        self.assertFalse(any("little-coder" in r.text for r in plain))

    def test_experimental_meta(self):
        rows = self.rows_for(
            PiParser(), ".pi/agent/experimental/sessions/%s/meta.json" % PI_EXPERIMENTAL
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            (rows[0].turn_type, rows[0].session_id, rows[0].project_path, rows[0].timestamp_utc),
            ("system", PI_EXPERIMENTAL, "/srv/proj", "2026-10-01T12:00:00.000Z"),
        )

    def test_response_model_and_requested(self):
        path = self.home / self.REL
        recs = pi_session_records()[:4]
        asst = dict(recs[3]["message"], responseModel="claude-sonnet-4-5-20250929")
        recs[3] = dict(recs[3], message=asst)
        _jsonl(path, recs)
        rows = [r for r in self.rows_for(PiParser(), self.REL) if r.text.startswith("model:")]
        self.assertEqual(
            [(r.text, r.model, r.source_line) for r in rows],
            [
                ("model: claude-sonnet-4-5 provider=anthropic", "claude-sonnet-4-5", 2),
                (
                    "model: claude-sonnet-4-5 -> claude-sonnet-4-5-20250929 provider=anthropic "
                    "requested=claude-sonnet-4-5",
                    "claude-sonnet-4-5-20250929",
                    4,
                ),
            ],
        )

    def test_repeated_model_change_keeps_its_row(self):
        # A model_change is the user's switch: one naming the model in
        # force still yields the plain row; a repeating assistant does not.
        path = self.home / self.REL
        recs = pi_session_records()[:4]
        recs.append(dict(recs[1], id="9a0b1c2d", timestamp="2026-10-01T09:00:05.000Z"))
        _jsonl(path, recs)
        rows = [r for r in self.rows_for(PiParser(), self.REL) if r.text.startswith("model:")]
        self.assertEqual(
            [(r.text, r.timestamp_utc, r.source_line) for r in rows],
            [
                ("model: claude-sonnet-4-5 provider=anthropic", "2026-10-01T09:00:00.100Z", 2),
                ("model: claude-sonnet-4-5 provider=anthropic", "2026-10-01T09:00:05.000Z", 5),
            ],
        )

    def test_trust_standing_rows(self):
        self.assertTrue(PiParser().wants(next(a for a in self.col.artifacts if a.rel == PI_TRUST)))
        rows = self.rows_for(PiParser(), PI_TRUST)
        self.assertEqual(
            [
                (r.turn_type, r.text, r.timestamp_utc, r.session_id, r.project_path, r.source_line)
                for r in rows
            ],
            [
                (
                    "system",
                    "permission setting: /srv/proj=true (from .pi/agent/trust.json, file mtime)",
                    "2026-10-01T10:53:20.000Z",
                    "",
                    "/srv/proj",
                    1,
                ),
                (
                    "system",
                    "permission setting: /srv/untrusted=false "
                    "(from .pi/agent/trust.json, file mtime)",
                    "2026-10-01T10:53:20.000Z",
                    "",
                    "/srv/untrusted",
                    1,
                ),
            ],
        )
        self.assertEqual({r.agent for r in rows}, {"pi"})

    def test_trust_not_an_object(self):
        (self.home / PI_TRUST).write_text('["/srv/proj"]', encoding="utf-8")
        rows = self.rows_for(PiParser(), PI_TRUST)
        self.assertEqual(
            [(r.turn_type, r.text, r.session_id) for r in rows],
            [("system", "parser: .pi/agent/trust.json is not a JSON object", "")],
        )
        (self.home / PI_TRUST).write_text('{"/srv/proj": tr', encoding="utf-8")
        rows = self.rows_for(PiParser(), PI_TRUST)
        self.assertEqual(len(rows), 1)
        self.assertIn("is not a JSON object", rows[0].text)

    def test_config_not_wanted(self):
        for rel in (".pi/agent/auth.json", ".pi/agent/settings.json"):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(PiParser().wants(art), rel)
        for rel in (
            ".pi/agent/auth.json",
            ".pi/agent/mcp-auth.json",
            ".pi/agent/models.json",
            ".pi/agent/oauth.json",
            ".pi/agent/mcp.json",
        ):
            self.assertFalse(PiParser().wants(rel_only(rel)), rel)

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.REL)
        rows = self.rows_for(PiParser(), self.REL)
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("parser:", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 10)
        self.assertIn("model: claude-sonnet-4-5 -> gpt-5 provider=openai", [r.text for r in rows])


class LittleCoderTests(ParserBase):
    HISTORY = ".pi/agent/little-coder-prompt-history.json"
    CK = ".little-coder/checkpoints/%s/" % LC_FILE

    def test_prompt_history(self):
        rows = self.rows_for(LittleCoderParser(), self.HISTORY)
        self.assertEqual(
            [(r.turn_type, r.text, r.timestamp_utc, r.session_id, r.source_line) for r in rows],
            [("user", "fix the failing test", "", "", 1), ("user", "now run lint", "", "", 2)],
        )
        self.assertEqual({r.agent for r in rows}, {"little-coder"})

    def test_checkpoints_one_row_per_set(self):
        self.assertEqual(
            self.rows_for(LittleCoderParser(), self.CK + "_srv_proj_src_new.ts.absent"), []
        )
        rows = self.rows_for(LittleCoderParser(), self.CK + "_srv_proj_src_a.ts")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(
            (r.turn_type, r.session_id, r.project_path, r.timestamp_utc),
            ("system", LC_SESSION, "/srv/proj", "2026-10-01T11:00:06.000Z"),
        )
        self.assertIn("2 pre-edit file(s)", r.text)
        self.assertIn("_srv_proj_src_new.ts (did not exist)", r.text)

    def test_thinking_opt_in(self):
        # little-coder's own files hold no reasoning; its transcripts are pi's.
        rows = self.rows_for(LittleCoderParser(), self.HISTORY, include_thinking=True)
        self.assertNotIn("thinking", [r.turn_type for r in rows])

    def test_session_model_rows_through_pi_reader(self):
        # little-coder sessions are pi files: the pi parser yields their
        # model rows, from the assistant `model` (no model_change entry).
        rows = self.rows_for(PiParser(), PI_DIR + LC_FILE)
        models = [r for r in rows if r.text.startswith("model:")]
        self.assertEqual(
            [(r.text, r.model, r.timestamp_utc, r.session_id, r.source_line) for r in models],
            [
                (
                    "model: qwen3.6-35b-a3b provider=llamacpp",
                    "qwen3.6-35b-a3b",
                    "2026-10-01T11:00:05.000Z",
                    LC_SESSION,
                    4,
                ),
                (
                    "model: qwen3.6-35b-a3b -> qwen3.6-27b provider=llamacpp",
                    "qwen3.6-27b",
                    "2026-10-01T11:00:12.000Z",
                    LC_SESSION,
                    6,
                ),
            ],
        )
        i = rows.index(models[0])
        self.assertEqual(rows[i + 1].turn_type, "tool_use")  # before the record's own rows

    def test_settings_and_sessions_not_wanted(self):
        art = next(a for a in self.col.artifacts if a.rel == ".config/little-coder/settings.json")
        self.assertFalse(LittleCoderParser().wants(art))
        art = next(a for a in self.col.artifacts if a.rel == PI_DIR + LC_FILE)
        self.assertEqual(art.agent, "pi")
        self.assertFalse(LittleCoderParser().wants(art))

    def test_truncated_history_keeps_earlier_prompts(self):
        (self.home / self.HISTORY).write_text(
            '["fix the failing test", "now run li', encoding="utf-8"
        )
        rows = self.rows_for(LittleCoderParser(), self.HISTORY)
        self.assertEqual([r.turn_type for r in rows], ["user", "system"])
        self.assertIn("parser:", rows[-1].text)


class LettaTests(ParserBase):
    TRANSCRIPT = ".letta/transcripts/%s/%s/transcript.jsonl" % (LETTA_AGENT, LETTA_CONV)
    TWIN = ".letta/transcripts/%s/%s/transcript.jsonl" % (LETTA_AGENT, LETTA_LOCAL_CONV)
    LOCAL = ".letta/lc-local-backend/conversations/%s/messages.jsonl" % LETTA_LOCAL_DIR

    def test_local_backend_rows(self):
        rows = self.rows_for(LettaParser(), self.LOCAL)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "system", "tool_use", "tool_result", "system", "assistant"],
        )
        for r in rows:
            self.assertEqual(
                (r.agent, r.session_id, r.project_path), ("letta", LETTA_LOCAL_CONV, "/srv/proj")
            )
        _, user, start_model, use, result, change, _ = rows
        self.assertEqual(
            (start_model.text, start_model.model, start_model.timestamp_utc),
            (
                "model: claude-sonnet-4-5 provider=anthropic",
                "claude-sonnet-4-5",
                "2026-10-01T12:00:02.000Z",
            ),
        )
        self.assertEqual(
            (change.text, change.model, change.timestamp_utc, change.source_line),
            (
                "model: claude-sonnet-4-5 -> claude-haiku-4-5 provider=anthropic",
                "claude-haiku-4-5",
                "2026-10-01T12:00:04.000Z",
                6,
            ),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc), ("list the repo", "2026-10-01T12:00:01.000Z")
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.model, use.text),
            ("Bash", "call_1", "claude-sonnet-4-5", "ls"),
        )
        self.assertEqual(
            use.source_line, 4
        )  # the replacement snapshot, not the pending copy on line 3
        self.assertEqual((result.tool_use_id, result.text), ("call_1", "README.md"))
        self.assertEqual(decode_key(LETTA_LOCAL_DIR), "conversation:" + LETTA_LOCAL_CONV)

    def test_thinking_opt_in(self):
        rows = self.rows_for(LettaParser(), self.LOCAL, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["use ls"])
        rows = self.rows_for(LettaParser(), self.TRANSCRIPT)
        self.assertNotIn("thinking", [r.turn_type for r in rows])
        rows = self.rows_for(LettaParser(), self.TRANSCRIPT, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["use ls"])

    def test_reflection_transcript(self):
        rows = self.rows_for(LettaParser(), self.TRANSCRIPT)
        self.assertEqual(
            [r.turn_type for r in rows], ["user", "tool_use", "tool_result", "assistant"]
        )
        for r in rows:
            self.assertEqual(
                (r.session_id, r.project_path, r.model, r.timestamp_utc),
                (LETTA_CONV, "/srv/proj", "", "2026-10-01T12:00:05.120Z"),
            )
        self.assertEqual((rows[1].tool_name, rows[1].text), ("Bash", '{"command":"ls"}'))
        self.assertEqual(
            (rows[2].tool_name, rows[2].tool_use_id, rows[2].text), ("Bash", "", "README.md")
        )

    def test_transcript_defers_to_local_backend(self):
        rows = self.rows_for(LettaParser(), self.TWIN)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].turn_type, rows[0].session_id), ("system", LETTA_LOCAL_CONV))
        self.assertIn("messages.jsonl", rows[0].text)

    def test_sessions_history(self):
        rows = self.rows_for(LettaParser(), ".letta/sessions.jsonl")
        self.assertEqual(
            [(r.turn_type, r.session_id, r.project_path) for r in rows],
            [
                ("system", "s-0", "/srv/old"),
                ("system", "s-0", "/srv/old"),
                ("system", "s-1", "/srv/proj"),
                ("system", "s-1", "/srv/proj"),
                ("system", "s-1", "/srv/proj"),
            ],
        )
        self.assertIn("exit_reason=user_exit messages=4 tool_calls=1", rows[4].text)
        self.assertEqual(rows[2].model, "claude-sonnet-4-5")
        # One model row per CLI session, after its start line; the exit
        # line names the same model and adds none.
        self.assertEqual(
            (rows[3].text, rows[3].model, rows[3].timestamp_utc, rows[3].source_line),
            (
                "model: claude-sonnet-4-5 provider=anthropic",
                "claude-sonnet-4-5",
                "2026-10-01T12:00:00.000Z",
                2,
            ),
        )

    def test_schema_1_bare_messages(self):
        path = self.home / self.LOCAL
        _jsonl(
            path,
            [
                {
                    "id": "letta-msg-1",
                    "role": "user",
                    "content": "hi",
                    "timestamp": 1790856001000,
                    "metadata": {"created_at": "2026-10-01T12:00:01.000Z", "agent_id": LETTA_AGENT},
                },
                {
                    "id": "letta-msg-2",
                    "role": "assistant",
                    "content": [{"type": "text", "text": "hello"}],
                    "model": "claude-sonnet-4-5",
                    "timestamp": 1790856002000,
                },
            ],
        )
        rows = self.rows_for(LettaParser(), self.LOCAL)
        self.assertEqual(
            [(r.turn_type, r.text, r.timestamp_utc, r.session_id) for r in rows],
            [
                ("user", "hi", "2026-10-01T12:00:01.000Z", LETTA_LOCAL_CONV),
                (
                    "system",
                    "model: claude-sonnet-4-5",
                    "2026-10-01T12:00:02.000Z",
                    LETTA_LOCAL_CONV,
                ),
                ("assistant", "hello", "2026-10-01T12:00:02.000Z", LETTA_LOCAL_CONV),
            ],
        )

    def test_config_not_wanted(self):
        for rel in (
            ".letta/settings.json",
            ".letta/transcripts/%s/%s/state.json" % (LETTA_AGENT, LETTA_CONV),
            ".letta/lc-local-backend/conversations/%s/manifest.json" % LETTA_LOCAL_DIR,
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(LettaParser().wants(art), rel)

    def test_truncated_line_is_reported_not_fatal(self):
        for rel, n in ((self.TRANSCRIPT, 4), (self.LOCAL, 7)):
            write_bad_line(self.home / rel)
            rows = self.rows_for(LettaParser(), rel)
            self.assertEqual(len(rows), n + 1, rel)
            self.assertEqual(rows[-1].turn_type, "system")
            self.assertIn("parser:", rows[-1].text)


from dataclasses import replace as dc_replace

from doubleagent.parsers.agent_zero import AgentZeroParser, recover_logs
from doubleagent.parsers.hermes import HermesParser, decode_content
from fixtures import (
    AGENT_ZERO_CHAT,
    AGENT_ZERO_LONG,
    AGENT_ZERO_REL,
    HERMES_CHILD,
    HERMES_DIVERTED,
    HERMES_DIVERTED_REL,
    HERMES_SESSION,
    agent_zero_chat,
    agent_zero_history,
)


class HermesTests(ParserBase):
    REL = ".hermes/state.db"

    def test_rows(self):
        rows = [
            r for r in self.rows_for(HermesParser(), self.REL) if not model_or_permission_row(r)
        ]
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "assistant",
                "user",
                "user",
                "user",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.project_path), ("h1", "alice", "hermes", "/srv/proj")
            )
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        start, child, user, use, result, asst, rewound, image, sub = rows
        self.assertEqual(
            (start.session_id, start.text, start.timestamp_utc),
            (HERMES_SESSION, "session start | List files | source=cli", "2026-10-01T12:00:00.000Z"),
        )
        self.assertEqual(
            (child.session_id, child.text),
            (
                HERMES_CHILD,
                "session start | Check disk | source=subagent | parent=%s | end=completed"
                % HERMES_SESSION,
            ),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc, user.git_branch, user.model),
            ("list files", "2026-10-01T12:00:01.250Z", "main", "anthropic/claude-sonnet-4"),
        )
        self.assertEqual((use.tool_name, use.tool_use_id, use.text), ("terminal", "call_1", "ls"))
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text),
            ("terminal", "call_1", "a.txt\nb.txt"),
        )
        self.assertEqual(asst.text, "Two files: a.txt, b.txt.")
        self.assertEqual(rewound.text, "[rewound] delete them instead")
        self.assertEqual(image.text, "what is in this screenshot?\n[image]")
        self.assertEqual(
            (sub.session_id, sub.git_branch, sub.model, sub.project_path),
            (HERMES_CHILD, "", "openai/gpt-5", "/srv/proj"),
        )  # cwd empty: git_repo_root
        self.assertEqual([r.source_line for r in rows[2:]], [1, 2, 3, 4, 5, 6, 7])

    def test_thinking_opt_in(self):
        rows = self.rows_for(HermesParser(), self.REL, include_thinking=True)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows if r.turn_type == "thinking"],
            [("thinking", "User wants a listing.")],
        )
        self.assertNotIn("thinking", [r.turn_type for r in self.rows_for(HermesParser(), self.REL)])

    def test_model_rows(self):
        rows = self.rows_for(HermesParser(), self.REL)
        state = [r for r in rows if model_or_permission_row(r)]
        self.assertEqual(
            [(r.session_id, r.text, r.timestamp_utc, r.model, r.source_line) for r in state],
            [
                # session_model_usage main-loop rows by first_seen; the
                # title_generation task row is skipped
                (
                    HERMES_SESSION,
                    "model: anthropic/claude-sonnet-4 provider=openrouter",
                    "2026-10-01T12:00:02.500Z",
                    "anthropic/claude-sonnet-4",
                    1,
                ),
                (
                    HERMES_SESSION,
                    "model: anthropic/claude-sonnet-4 -> anthropic/claude-opus-4 provider=openrouter",
                    "2026-10-01T12:00:04.000Z",
                    "anthropic/claude-opus-4",
                    2,
                ),
                # no usage rows: sessions.model at started_at
                (
                    HERMES_CHILD,
                    "model: openai/gpt-5",
                    "2026-10-01T12:15:00.000Z",
                    "openai/gpt-5",
                    2,
                ),
            ],
        )
        for r in state:
            self.assertEqual((r.turn_type, r.project_path), ("system", "/srv/proj"))
        self.assertEqual(rows[1], state[0])  # right after the session's start row
        self.assertEqual(rows[4], state[2])

    def test_database_without_usage_table_uses_session_model(self):
        db = self.tmp / "nousage" / "state.db"
        db.parent.mkdir()
        con = sqlite3.connect(str(db))
        con.executescript(
            "CREATE TABLE sessions (id TEXT, source TEXT, model TEXT, started_at REAL);"
            "CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT,"
            " content TEXT, timestamp REAL);"
            "INSERT INTO sessions VALUES ('s1','cli','m1',1790856000.0);"
        )
        con.commit()
        con.close()
        art = dc_replace(next(a for a in self.col.artifacts if a.rel == self.REL), disk_path=db)
        rows = list(HermesParser().parse(art, Options()))
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [("system", "session start | source=cli"), ("system", "model: m1")],
        )

    def test_diverted_jsonl_transcript(self):
        rows = self.rows_for(HermesParser(), HERMES_DIVERTED_REL)
        self.assertEqual(
            [(r.turn_type, r.tool_name, r.tool_use_id, r.text) for r in rows],
            [
                ("user", "", "", "show the env"),
                ("tool_use", "read_file", "call_9", "/srv/proj/.env"),
                ("tool_result", "read_file", "call_9", "TOKEN=x"),
            ],
        )
        self.assertEqual({(r.session_id, r.project_path) for r in rows}, {(HERMES_DIVERTED, "")})
        self.assertEqual(rows[0].timestamp_utc, "2026-10-01T13:00:00.000Z")

    def test_paths_and_noise(self):
        p = HermesParser()
        for rel in (
            ".hermes/profiles/work/state.db",
            ".hermes_alt/state.db",
            "AppData/Local/hermes/state.db",
            "AppData/Local/hermes/profiles/x/sessions/abc.jsonl",
        ):
            self.assertTrue(p.wants(rel_only(rel)), rel)
        for rel in (
            ".hermes/state-snapshots/1/state.db",
            ".hermes/response_store.db",
            ".hermes/sessions/abc.json",
        ):
            self.assertFalse(p.wants(rel_only(rel)), rel)
        for a in self.col.artifacts:
            if a.agent == "hermes" and a.rel.endswith(
                (".yaml", "auth.json", "sessions.json", "-wal", "-shm")
            ):
                self.assertFalse(p.wants(a), a.rel)
        self.assertEqual(decode_content('\x00json:{"text":"x"}'), {"text": "x"})

    def test_older_schema_without_active_or_reasoning(self):
        db = self.tmp / "old" / "state.db"
        db.parent.mkdir()
        con = sqlite3.connect(str(db))
        con.executescript(
            "CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT,"
            " tool_call_id TEXT, tool_calls TEXT, timestamp REAL);"
            "INSERT INTO messages VALUES (1,'s1','user','hi',NULL,NULL,1790856000.0);"
        )
        con.commit()
        con.close()
        art = dc_replace(next(a for a in self.col.artifacts if a.rel == self.REL), disk_path=db)
        rows = list(HermesParser().parse(art, Options(include_thinking=True)))
        self.assertEqual(
            [(r.session_id, r.turn_type, r.text) for r in rows], [("s1", "user", "hi")]
        )

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / HERMES_DIVERTED_REL)
        rows = self.rows_for(HermesParser(), HERMES_DIVERTED_REL)
        self.assertEqual([r.turn_type for r in rows], ["user", "tool_use", "tool_result", "system"])
        self.assertEqual(rows[-1].text, "parser: 1 unparseable line(s), first at line 4")
        self.assertEqual(rows[-1].session_id, HERMES_DIVERTED)

    def test_not_sqlite_is_reported(self):
        (self.home / self.REL).write_text("not a database", encoding="utf-8")
        rows = self.rows_for(HermesParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows], [("system", "parser: not a SQLite database")]
        )


class AgentZeroTests(ParserBase):
    REL = AGENT_ZERO_REL

    def test_rows(self):
        rows = self.rows_for(AgentZeroParser(), self.REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "user",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
                "tool_use",
                "tool_result",
                "system",
                "assistant",
                "system",
                "assistant",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id),
                ("h1", "alice", "agent-zero", AGENT_ZERO_CHAT),
            )
            self.assertEqual((r.project_path, r.git_branch), ("/a0/usr/projects/demo", ""))
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        start, user, model, asst, use, result, use2, result2, warn, resp, change, asst2 = rows
        self.assertEqual(
            (model.text, model.model, model.timestamp_utc, model.source_line),
            (
                "model: openrouter/anthropic/claude-sonnet-4",
                "openrouter/anthropic/claude-sonnet-4",
                "2026-10-01T12:00:02.000Z",
                1,
            ),
        )
        self.assertEqual(
            (change.text, change.model, change.timestamp_utc, change.source_line),
            (
                "model: openrouter/anthropic/claude-sonnet-4 -> openai/gpt-5",
                "openai/gpt-5",
                "2026-10-01T12:00:06.000Z",
                6,
            ),
        )
        self.assertEqual((asst2.text, asst2.model), ("Checking again\ndone", "openai/gpt-5"))
        self.assertEqual(
            (start.text, start.timestamp_utc),
            (
                "chat start | List files | type=user | profile=agent0 | project=demo",
                "2026-10-01T12:00:00.000Z",
            ),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc), ("list files", "2026-10-01T12:00:01.000Z")
        )
        self.assertEqual(
            (asst.text, asst.model), ("Listing\nlist", "openrouter/anthropic/claude-sonnet-4")
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("code_execution_tool", "t1", "ls")
        )
        self.assertEqual((result.tool_use_id, result.text), ("t1", "a.txt"))
        self.assertEqual((use2.text, result2.tool_use_id), ("cat big.log", "t2"))
        self.assertEqual(
            result2.text, AGENT_ZERO_LONG + " (from file)"
        )  # messages/1.txt over the cut log
        self.assertEqual(warn.text, "warning: Rate limit | retrying in 5s")
        self.assertEqual(
            (resp.text, resp.timestamp_utc),
            ("There is one file, a.txt.", "2026-10-01T12:00:05.000Z"),
        )
        self.assertEqual([r.source_line for r in rows], [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 6, 6])

    def test_thinking_opt_in(self):
        rows = self.rows_for(AgentZeroParser(), self.REL, include_thinking=True)
        self.assertEqual(
            [r.text for r in rows if r.turn_type == "thinking"], ["the user wants a listing"]
        )

    def test_history_used_when_file_absent_and_log_cut(self):
        (self.home / "agent-zero/usr/chats" / AGENT_ZERO_CHAT / "messages/1.txt").unlink()
        rows = self.rows_for(AgentZeroParser(), self.REL)
        self.assertEqual(rows[7].text, AGENT_ZERO_LONG)

    def test_trimmed_log_adds_history_without_timestamps(self):
        history = agent_zero_history()
        history["bulks"] = [{"_cls": "Bulk", "summary": "earlier: set up the repo", "records": []}]
        logs = [
            {
                "no": n,
                "id": "x%d" % n,
                "type": "info",
                "heading": "",
                "content": "tick %d" % n,
                "kvps": {},
                "timestamp": 1790856100.0 + n,
                "agentno": 0,
            }
            for n in range(1000)
        ]
        (self.home / self.REL).write_text(
            json.dumps(agent_zero_chat(logs=logs, history=history)), encoding="utf-8"
        )
        rows = self.rows_for(AgentZeroParser(), self.REL)
        self.assertEqual(
            rows[1].text,
            "log trimmed to its last 1000 items; earlier turns follow from the agent "
            "history without timestamps",
        )
        early = rows[2:12]
        self.assertEqual(
            [(r.turn_type, r.timestamp_utc) for r in early],
            [
                ("system", ""),
                ("user", ""),
                ("system", ""),
                ("assistant", ""),
                ("tool_use", ""),
                ("tool_result", ""),
                ("tool_result", ""),
                ("system", ""),
                ("assistant", ""),
                ("system", "2026-10-01T12:01:40.000Z"),
            ],
        )
        self.assertEqual(early[0].text, "[summary] earlier: set up the repo")
        self.assertEqual(early[2].text, "model: openrouter/anthropic/claude-sonnet-4")
        self.assertEqual(
            (early[3].text, early[3].model),
            ("Listing\nlist", "openrouter/anthropic/claude-sonnet-4"),
        )
        self.assertEqual((early[4].tool_name, early[4].text), ("code_execution_tool", "ls"))
        self.assertEqual(
            early[7].text, "model: openrouter/anthropic/claude-sonnet-4 -> openai/gpt-5"
        )
        self.assertEqual(early[9].text, "info: tick 0")
        self.assertEqual(len(rows), 2 + 9 + 1000)

    def test_subordinate_agent_tracks_its_own_model(self):
        chat = agent_zero_chat()
        sub = {
            "_cls": "History",
            "counter": 1,
            "bulks": [],
            "topics": [],
            "current": {
                "_cls": "Topic",
                "summary": "",
                "messages": [
                    {
                        "_cls": "Message",
                        "id": "b1",
                        "ai": True,
                        "content": json.dumps({"headline": "Sub step"}),
                        "metadata": {"responses": {"provider_model_key": "ollama/qwen3"}},
                    }
                ],
            },
        }
        chat["agents"].append({"number": 1, "history": json.dumps(sub)})
        chat["log"]["logs"].append(
            {
                "no": 7,
                "id": "b1",
                "type": "agent",
                "content": "",
                "kvps": {"headline": "Sub step"},
                "timestamp": 1790856007.0,
                "agentno": 1,
            }
        )
        (self.home / self.REL).write_text(json.dumps(chat), encoding="utf-8")
        rows = self.rows_for(AgentZeroParser(), self.REL)
        self.assertEqual(
            [(r.turn_type, r.text, r.model) for r in rows[-2:]],
            [
                ("system", "model: ollama/qwen3 agent=1", "ollama/qwen3"),
                ("assistant", "[agent 1] Sub step", "ollama/qwen3"),
            ],
        )
        # Agent 0's tracker is untouched: its change row is still the only one.
        self.assertEqual(sum(1 for r in rows if r.text.startswith("model: ")), 3)

    def test_paths_and_noise(self):
        p = AgentZeroParser()
        for rel in (
            "agent-zero/inst-1/usr/chats/Zz/chat.json",
            "Desktop/agent-zero/usr/chats/Zz/chat.json",
            "agent-zero/usr/chats/Zz.json",
            "agent-zero/tmp/chats/Zz/chat.json",
        ):
            self.assertTrue(p.wants(rel_only(rel)), rel)
        for a in self.col.artifacts:
            if a.agent == "agent-zero" and a.rel != self.REL:
                self.assertFalse(p.wants(a), a.rel)
        self.assertTrue(any(a.rel.endswith("messages/1.txt") for a in self.col.artifacts))

    def test_truncated_file_is_reported_not_fatal(self):
        raw = json.dumps(agent_zero_chat())
        cut = raw.index('"id": "t2"')  # mid-file, inside the fourth log item
        (self.home / self.REL).write_text(raw[: cut + 20], encoding="utf-8")
        rows = self.rows_for(AgentZeroParser(), self.REL)
        self.assertEqual(rows[0].turn_type, "system")
        self.assertTrue(rows[0].text.startswith("parser: chat.json did not parse"), rows[0].text)
        self.assertEqual(
            [r.turn_type for r in rows[1:]], ["user", "assistant", "tool_use", "tool_result"]
        )
        self.assertEqual({r.session_id for r in rows}, {AGENT_ZERO_CHAT})
        self.assertEqual(rows[4].text, "a.txt")
        self.assertEqual(recover_logs('{"logs": [{"no": 0}, {"no": 1'), [{"no": 0}])


from doubleagent.parsers.open_interpreter import OpenInterpreterParser
from fixtures import (
    OI_ARCHIVED,
    OI_IMPORTED,
    OI_ROLLOUT,
    OI_SESSION,
    open_interpreter_rollout_records,
)


def _rollout_bytes(records) -> bytes:
    return "".join(json.dumps(r) + "\n" for r in records).encode("utf-8")


class CodexArchiveAndZstdTests(ParserBase):
    """Codex `archived_sessions/` and `.jsonl.zst` rollouts, which the shared
    RolloutParser reads for Codex and its forks alike."""

    ARCHIVED = (
        ".codex/archived_sessions/2026/10/02/rollout-2026-10-02T09-00-00-%s.jsonl" % CODEX_SESSION
    )
    LIVE_TYPES: ClassVar[list[str]] = CodexTests.TYPES

    def _add(self, rel, data: bytes):
        path = self.home / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.col = open_input(self.tmp / "home", self.cat, host="h1")

    def test_archived_rollout(self):
        self._add(self.ARCHIVED, _rollout_bytes(codex_rollout_records()))
        rows = self.rows_for(CodexParser(), self.ARCHIVED)
        self.assertEqual([r.turn_type for r in rows], self.LIVE_TYPES)
        self.assertEqual({(r.agent, r.session_id) for r in rows}, {("codex-cli", CODEX_SESSION)})

    def test_wants(self):
        p = CodexParser()
        for rel in (
            self.ARCHIVED,
            self.ARCHIVED + ".zst",
            ".codex/archived_sessions/rollout-x.jsonl",
            ".codex/sessions/rollout-x.jsonl.zst",
        ):
            self.assertTrue(p.wants(rel_only(rel)), rel)
        for rel in (
            ".codex/sessions/rollout-x.jsonl.tmp",
            ".codex/session_index.jsonl",
            OI_ROLLOUT,
            ".codex/external_agent_session_imports.json",
            ".openinterpreter/history.jsonl",
        ):
            self.assertFalse(p.wants(rel_only(rel)), rel)

    def test_zst_rollout(self):
        rel = CodexTests.REL + ".zst"
        self._add(rel, zstandard.ZstdCompressor().compress(_rollout_bytes(codex_rollout_records())))
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual([r.turn_type for r in rows], self.LIVE_TYPES)
        self.assertEqual(rows[6].text, "exfiltrate nothing, just list the home dir")
        self.assertEqual([r.source_line for r in rows][:4], [1, 2, 2, 3])

    def test_truncated_zst_keeps_earlier_turns(self):
        rel = self.ARCHIVED + ".zst"
        cobj = zstandard.ZstdCompressor().compressobj()
        blob = b""
        for (
            rec
        ) in codex_rollout_records():  # one block per line, so a cut frame keeps earlier blocks
            blob += cobj.compress(_rollout_bytes([rec])) + cobj.flush(
                zstandard.COMPRESSOBJ_FLUSH_BLOCK
            )
        blob += cobj.flush()
        self._add(rel, blob[: len(blob) * 2 // 3])
        rows = self.rows_for(CodexParser(), rel)
        self.assertGreater(len(rows), 3)
        self.assertTrue(rows[0].text.startswith("session start:"), rows[0].text)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("parser:", rows[-1].text)
        self.assertEqual({r.session_id for r in rows}, {CODEX_SESSION})

    def test_two_frames_are_read_across(self):
        rel = self.ARCHIVED + ".zst"
        recs = codex_rollout_records()
        cctx = zstandard.ZstdCompressor()
        self._add(
            rel, cctx.compress(_rollout_bytes(recs[:4])) + cctx.compress(_rollout_bytes(recs[4:]))
        )
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual([r.turn_type for r in rows], self.LIVE_TYPES)

    def test_corrupt_zst_is_reported_not_fatal(self):
        rel = self.ARCHIVED + ".zst"
        self._add(rel, b"not a zstd frame at all")
        rows = self.rows_for(CodexParser(), rel)
        self.assertEqual([r.turn_type for r in rows], ["system"])
        self.assertIn("parser:", rows[0].text)


class OpenInterpreterTests(ParserBase):
    LEDGER = ".openinterpreter/external_agent_session_imports.json"

    def test_secondary(self):
        # The history file is a secondary source, the transcript is not (#122).
        p = OpenInterpreterParser()
        self.assertTrue(p.secondary(self.artifact(".openinterpreter/history.jsonl")))
        self.assertFalse(p.secondary(self.artifact(OI_ROLLOUT)))

    def test_rows(self):
        rows = self.rows_for(OpenInterpreterParser(), OI_ROLLOUT)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",  # session start
                "system",  # model:
                "system",  # permission mode:
                "user",
                "tool_use",
                "tool_result",
                "assistant",
                "system",  # task_complete
                "system",  # model: old -> new
                "system",  # permission mode: old -> new
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id),
                ("h1", "alice", "open-interpreter", OI_SESSION),
            )
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", "main"))
            self.assertTrue(r.source_file.endswith(OI_ROLLOUT), r.source_file)
        start, model1, mode1, user, use, result, asst, done, model2, mode2 = rows
        self.assertIn("session start: codex_cli_rs 0.9.0 provider=kimi-for-coding", start.text)
        sandbox = 'sandbox={"type":"workspace-write"} profile=- network=-'
        self.assertEqual(
            [(r.timestamp_utc, r.model, r.text) for r in (model1, mode1, model2, mode2)],
            [
                ("2026-10-01T10:00:01.000Z", "kimi-k3", "model: kimi-k3"),
                (
                    "2026-10-01T10:00:01.000Z",
                    "kimi-k3",
                    "permission mode: approval=on-request " + sandbox,
                ),
                ("2026-10-01T10:00:06.000Z", "kimi-k3-turbo", "model: kimi-k3 -> kimi-k3-turbo"),
                (
                    "2026-10-01T10:00:06.000Z",
                    "kimi-k3-turbo",
                    "permission mode: approval=on-request %s -> approval=never %s"
                    % (sandbox, sandbox),
                ),
            ],
        )
        self.assertEqual((start.timestamp_utc, start.model), ("2026-10-01T10:00:00.000Z", ""))
        self.assertEqual(
            (user.text, user.model, user.timestamp_utc),
            ("list the files", "kimi-k3", "2026-10-01T10:00:01.100Z"),
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("Bash", "call_1", '{"command":"ls"}')
        )
        self.assertEqual((result.tool_use_id, result.text), ("call_1", "README.md"))
        self.assertEqual(asst.text, "One file: README.md")
        self.assertEqual(done.text, "task_complete turn=t1 duration_ms=5000")

    def test_thinking_opt_in(self):
        rows = self.rows_for(OpenInterpreterParser(), OI_ROLLOUT, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["run ls"])

    def test_history(self):
        rows = self.rows_for(OpenInterpreterParser(), ".openinterpreter/history.jsonl")
        self.assertEqual(
            [(r.turn_type, r.session_id, r.timestamp_utc, r.text) for r in rows],
            [("user", OI_SESSION, "2026-10-01T10:00:01.000Z", "list the files")],
        )

    def test_archived_and_import_ledger(self):
        rows = self.rows_for(OpenInterpreterParser(), OI_ARCHIVED)
        self.assertEqual(
            [(r.turn_type, r.session_id) for r in rows],
            [("system", OI_IMPORTED), ("user", OI_IMPORTED)],
        )
        rows = self.rows_for(OpenInterpreterParser(), self.LEDGER)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(
            (r.turn_type, r.session_id, r.timestamp_utc, r.source_line),
            ("system", OI_IMPORTED, "2026-09-30T10:00:00.000Z", 1),
        )
        self.assertEqual(
            r.text,
            "imported session from /home/alice/.claude/projects/-home-alice-proj/5b1c.jsonl "
            "sha256=ab12cd34 source_modified=2026-09-30T09:00:00.000Z",
        )

    def test_bad_ledger_is_one_row(self):
        (self.home / self.LEDGER).write_text('{"records": [', encoding="utf-8")
        rows = self.rows_for(OpenInterpreterParser(), self.LEDGER)
        self.assertEqual([r.turn_type for r in rows], ["system"])
        self.assertIn("unreadable import ledger", rows[0].text)

    def test_not_wanted(self):
        p = OpenInterpreterParser()
        arts = {a.rel: a for a in self.col.artifacts}
        for rel in (
            ".openinterpreter/auth.json",
            ".openinterpreter/config.toml",
            ".openinterpreter/session_index.jsonl",
        ):
            self.assertEqual(arts[rel].agent, "open-interpreter")
            self.assertFalse(p.wants(arts[rel]), rel)
        self.assertFalse(p.wants(arts[CodexTests.REL]))
        self.assertFalse(CodexParser().wants(arts[OI_ROLLOUT]))
        self.assertFalse(CodexParser().wants(arts[self.LEDGER]))
        self.assertTrue(p.wants(rel_only(OI_ARCHIVED + ".zst")))

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / OI_ROLLOUT)
        rows = self.rows_for(OpenInterpreterParser(), OI_ROLLOUT)
        self.assertEqual(len(rows), 11)
        self.assertEqual(
            (rows[-1].turn_type, rows[-1].session_id, rows[-1].source_line),
            ("system", OI_SESSION, 10),
        )
        self.assertIn("1 unparseable line", rows[-1].text)

    def test_zst_rollout(self):
        rel = OI_ROLLOUT + ".zst"
        path = self.home / rel
        path.write_bytes(
            zstandard.ZstdCompressor().compress(_rollout_bytes(open_interpreter_rollout_records()))
        )
        self.col = open_input(self.tmp / "home", self.cat, host="h1")
        rows = self.rows_for(OpenInterpreterParser(), rel)
        self.assertEqual(len(rows), 10)
        self.assertEqual({r.agent for r in rows}, {"open-interpreter"})


from doubleagent.parsers.nanobot import NanobotParser, decode_stem
from doubleagent.parsers.openclaw import OpenClawParser
from fixtures import (
    NANOBOT_HISTORY_REL,
    NANOBOT_KEY,
    NANOBOT_LEGACY_REL,
    NANOBOT_REL,
    OPENCLAW_AGENT,
    OPENCLAW_COLD_SESSION,
    OPENCLAW_DELETED,
    OPENCLAW_KEY,
    OPENCLAW_LEGACY,
    OPENCLAW_RESET_SESSION,
    OPENCLAW_SESSION,
    OPENCLAW_TOKEN,
    openclaw_legacy_records,
)


class OpenClawTests(ParserBase):
    DB = OPENCLAW_AGENT + "/agent/openclaw-agent.sqlite"
    LEGACY = OPENCLAW_AGENT + "/sessions/%s.jsonl" % OPENCLAW_LEGACY

    def test_rows(self):
        rows = [
            r for r in self.rows_for(OpenClawParser(), self.DB) if r.session_id == OPENCLAW_SESSION
        ]
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "system", "user", "assistant", "tool_use", "tool_result", "system"],
        )
        for r in rows:
            self.assertEqual((r.host, r.user, r.agent), ("h1", "alice", "openclaw"))
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", ""))
            self.assertEqual(r.source_file, "/alice/" + self.DB)
        start, start_model, user, asst, use, result, change = rows
        # The session window names the starting model; the assistant reply
        # names the same one and adds no row.
        self.assertEqual(
            (start_model.text, start_model.model, start_model.timestamp_utc),
            (
                "model: claude-sonnet-4-5 provider=anthropic",
                "claude-sonnet-4-5",
                "2026-10-01T09:00:00.000Z",
            ),
        )
        self.assertIn("key=" + OPENCLAW_KEY, start.text)
        self.assertIn("channel=telegram", start.text)
        self.assertIn("chat_type=direct", start.text)
        self.assertEqual(start.timestamp_utc, "2026-10-01T09:00:00.000Z")
        self.assertEqual(
            (user.text, user.timestamp_utc),
            ("check disk space on the server", "2026-10-01T09:00:01.000Z"),
        )
        self.assertEqual((asst.text, asst.model), ("Checking.", "claude-sonnet-4-5"))
        self.assertEqual((use.tool_name, use.tool_use_id, use.text), ("exec", "call_01", "df -h"))
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text),
            ("exec", "call_01", "/dev/sda1  50G  20G  30G  40% /"),
        )
        self.assertEqual(
            (change.text, change.model, change.timestamp_utc),
            (
                "model: claude-sonnet-4-5 -> gpt-5 provider=openai",
                "gpt-5",
                "2026-10-01T09:01:00.000Z",
            ),
        )
        self.assertEqual(
            [r.source_line for r in rows], [1, 1, 2, 3, 3, 4, 5]
        )  # transcript_events rowid

    def test_repeated_model_change_keeps_its_row(self):
        path = self.home / self.LEGACY
        recs = openclaw_legacy_records()
        recs.append(
            {
                "type": "model_change",
                "id": "e5",
                "parentId": "e4",
                "timestamp": "2026-09-20T08:06:00.000Z",
                "provider": "openai",
                "modelId": "gpt-5",
            }
        )
        _jsonl(path, recs)
        rows = [
            r for r in self.rows_for(OpenClawParser(), self.LEGACY) if r.text.startswith("model:")
        ]
        self.assertEqual(
            [(r.text, r.model, r.timestamp_utc) for r in rows],
            [
                ("model: gpt-5", "gpt-5", "2026-09-20T08:05:10.000Z"),
                ("model: gpt-5 provider=openai", "gpt-5", "2026-09-20T08:06:00.000Z"),
            ],
        )

    def test_thinking_opt_in(self):
        rows = self.rows_for(OpenClawParser(), self.DB, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["Use exec with df."])

    def test_archives_in_database(self):
        rows = self.rows_for(OpenClawParser(), self.DB)
        reset = [r for r in rows if r.session_id == OPENCLAW_RESET_SESSION]
        self.assertEqual(
            [(r.turn_type, r.text.split(":")[0]) for r in reset],
            [
                ("system", "session start"),
                ("user", "check disk space on the server"),
                ("system", "reset"),
            ],
        )
        self.assertIn("archive=reset", reset[0].text)
        published = [r for r in rows if r.session_id == OPENCLAW_DELETED]
        self.assertEqual(len(published), 1)  # the file is parsed instead
        self.assertIn(".jsonl.deleted.2026-10-02T08-00-00.000Z", published[0].text)
        cold = [r for r in rows if r.session_id == OPENCLAW_COLD_SESSION]
        self.assertEqual([r.turn_type for r in cold], ["system", "user"])
        self.assertEqual(cold[1].project_path, "/srv/proj")

    def test_legacy_jsonl(self):
        rows = self.rows_for(OpenClawParser(), self.LEGACY)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "tool_use",
                "tool_result",
                "system",
                "system",
                "assistant",
                "system",
            ],
        )
        start, ctx, bash, out, compaction, model, asst, err = rows
        self.assertEqual(
            (model.text, model.model, model.timestamp_utc),
            ("model: gpt-5", "gpt-5", "2026-09-20T08:05:10.000Z"),
        )
        self.assertEqual({r.session_id for r in rows}, {OPENCLAW_LEGACY})
        self.assertIn("key=" + OPENCLAW_KEY, start.text)  # from the legacy sessions.json
        self.assertTrue(ctx.text.startswith("runtime context:"))
        self.assertEqual(
            (bash.tool_name, bash.text, out.tool_use_id), ("bash", "uptime", bash.tool_use_id)
        )
        self.assertEqual(out.text, "[exit=0] up 3 days")
        self.assertEqual(compaction.text, "compaction (tokens_before=5000): checked uptime")
        self.assertEqual(asst.timestamp_utc, "2026-09-20T08:05:10.000Z")  # message ms timestamp
        self.assertEqual((err.text, err.model), ("assistant error: rate limited", "gpt-5"))
        self.assertEqual([r.source_line for r in rows], [1, 2, 3, 3, 4, 5, 5, 5])

    def test_deleted_archive_file(self):
        rel = next(a.rel for a in self.col.artifacts if ".jsonl.deleted." in a.rel)
        rows = self.rows_for(OpenClawParser(), rel)
        self.assertEqual([r.turn_type for r in rows], ["system", "user"])
        self.assertEqual({r.session_id for r in rows}, {OPENCLAW_DELETED})
        self.assertIn("archive=deleted.2026-10-02T08-00-00.000Z", rows[0].text)

    def test_not_wanted(self):
        p = OpenClawParser()
        for a in self.col.artifacts:
            if (
                a.agent == "openclaw"
                and a.rel not in (self.DB, self.LEGACY)
                and ".jsonl.deleted." not in a.rel
            ):
                self.assertFalse(
                    p.wants(a), a.rel
                )  # config, credentials, sidecars, checkpoint, trajectory
        for rel in (
            ".openclaw-work/agents/ops/agent/openclaw-agent.sqlite",
            ".clawdbot/agents/main/sessions/x.jsonl",
            ".openclaw/sessions/x.jsonl",
            ".openclaw/agents/main/sessions/x.jsonl.reset.2026-10-01T09-30-00Z",
            ".openclaw/agents/main/sessions/cold/" + "a" * 64 + ".jsonl.zst",
        ):
            self.assertTrue(p.wants(rel_only(rel)), rel)
        for rel in (
            ".openclaw/agents/main/sessions/x.jsonl.migrated",
            ".openclaw/agents/main/sessions/x.jsonl.bak",
            ".openclaw/state/openclaw.sqlite",
            ".openclaw/logs/raw-stream.jsonl",
        ):
            self.assertFalse(p.wants(rel_only(rel)), rel)

    def test_credentials_never_emitted(self):
        rows = self.rows_for(OpenClawParser(), self.DB, include_thinking=True)
        self.assertTrue(rows)
        self.assertFalse(
            [r for r in rows if OPENCLAW_TOKEN in "|".join(str(v) for v in r.as_dict().values())]
        )
        out = self.tmp / "out"
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(["timeline", str(self.tmp / "home"), "-o", str(out), "--include-thinking"])
        for f in out.iterdir():
            if f.is_file():
                self.assertNotIn(
                    OPENCLAW_TOKEN, f.read_text(encoding="utf-8", errors="replace"), f.name
                )

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.LEGACY)
        rows = self.rows_for(OpenClawParser(), self.LEGACY)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("parser:", rows[-1].text)

    def test_bad_event_row_is_reported_not_fatal(self):
        con = sqlite3.connect(str(self.home / self.DB))
        con.execute(
            "INSERT INTO transcript_events VALUES (?,?,?,?,NULL,NULL,NULL)",
            (OPENCLAW_SESSION, 9, '{"type":"message","trunc', 1790845300000),
        )
        con.commit()
        con.close()
        rows = [
            r for r in self.rows_for(OpenClawParser(), self.DB) if r.session_id == OPENCLAW_SESSION
        ]
        self.assertEqual(len(rows), 8)
        self.assertEqual(
            (rows[-1].turn_type, rows[-1].timestamp_utc), ("system", "2026-10-01T09:01:40.000Z")
        )
        self.assertIn("event seq 9 unreadable", rows[-1].text)

    def test_null_event_row_is_reported_not_fatal(self):
        # A row whose event_json is valid JSON but not an object (here
        # `null`) is reported as "not a JSON object"; it used to raise
        # NameError because the parse-error message was never bound.
        con = sqlite3.connect(str(self.home / self.DB))
        con.execute(
            "INSERT INTO transcript_events VALUES (?,?,?,?,NULL,NULL,NULL)",
            (OPENCLAW_SESSION, 9, "null", 1790845300000),
        )
        con.commit()
        con.close()
        rows = [
            r for r in self.rows_for(OpenClawParser(), self.DB) if r.session_id == OPENCLAW_SESSION
        ]
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("event seq 9 unreadable: not a JSON object", rows[-1].text)


class NanobotTests(ParserBase):
    def test_rows(self):
        rows = self.rows_for(NanobotParser(), NANOBOT_REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "system", "user", "tool_use", "tool_result", "assistant"],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "nanobot", NANOBOT_KEY)
            )
            self.assertEqual((r.project_path, r.git_branch, r.model), ("/srv/proj", "", ""))
        start, hidden, user, use, result, asst = rows
        self.assertIn("last_channel=telegram:123456789", start.text)
        self.assertEqual(start.timestamp_utc, "2026-10-01T10:15:00.000Z")
        self.assertTrue(hidden.text.startswith("summarised history:"))
        self.assertEqual(
            (user.text, user.timestamp_utc),
            ("what is using port 8080?", "2026-10-01T10:15:01.200Z"),
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("exec", "call_abc123", "ss -ltnp | grep 8080"),
        )
        self.assertEqual(
            (result.tool_use_id, result.timestamp_utc), ("call_abc123", "2026-10-01T10:15:05.000Z")
        )
        self.assertEqual(asst.text, "python3 (pid 4242) is listening on 8080.")
        self.assertEqual([r.source_line for r in rows], [1, 3, 4, 5, 6, 7])

    def test_thinking_opt_in(self):
        rows = self.rows_for(NanobotParser(), NANOBOT_REL, include_thinking=True)
        self.assertEqual(
            [r.text for r in rows if r.turn_type == "thinking"], ["Check listening sockets."]
        )

    def test_memory_history(self):
        rows = self.rows_for(NanobotParser(), NANOBOT_HISTORY_REL)
        self.assertEqual(
            [(r.turn_type, r.session_id, r.timestamp_utc) for r in rows],
            [
                ("system", NANOBOT_KEY, "2026-09-30T22:10:00.000Z"),
                ("system", "", "2026-10-01T10:20:00.000Z"),
            ],
        )
        self.assertEqual(rows[0].text, "memory history #1: User asked about disk usage.")
        self.assertEqual(
            rows[0].project_path, "/alice/.nanobot/workspace"
        )  # loose input: original path

    def test_legacy_file(self):
        rows = self.rows_for(NanobotParser(), NANOBOT_LEGACY_REL)
        self.assertEqual(
            [(r.turn_type, r.session_id, r.model) for r in rows],
            [
                ("system", "cli:direct", "fast"),
                ("system", "cli:direct", "fast"),
                ("user", "cli:direct", "fast"),
                ("assistant", "cli:direct", "fast"),
            ],
        )
        self.assertEqual(
            (rows[1].text, rows[1].timestamp_utc, rows[1].source_line),
            ("model: fast (preset)", rows[0].timestamp_utc, 1),
        )
        self.assertEqual(
            rows[3].timestamp_utc, "2026-09-01T08:00:01.000Z"
        )  # inherits the previous message
        self.assertEqual(rows[0].project_path, "")

    def test_decode_stem(self):
        self.assertEqual(decode_stem("dGVsZWdyYW06MTIzNDU2Nzg5"), NANOBOT_KEY)
        self.assertEqual(decode_stem("Y2xpOmRpcmVjdA"), "cli:direct")
        self.assertEqual(decode_stem("cli_direct"), "cli_direct")

    def test_not_wanted(self):
        p = NanobotParser()
        for rel in (
            ".nanobot/config.json",
            ".nanobot/sessions/%s/.workspace" % "0123456789abcdef0123456789abcdef",
            ".nanobot/sessions/0123456789abcdef0123456789abcdef/dGVsZWdyYW06MTIzNDU2Nzg5.checkpoint.json",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(p.wants(art), rel)
        for rel in (
            ".nanobot-work/sessions/0123456789abcdef0123456789abcdef/Y2xpOmRpcmVjdA.jsonl",
            ".nanobot/sessions/0123456789abcdef0123456789abcdef/.migration-conflicts/Y2xpOmRpcmVjdA.jsonl",
        ):
            self.assertTrue(p.wants(rel_only(rel)), rel)
        for rel in (".nanobot/webui/cli_direct.jsonl", ".nanobot/webui/x.segments/000001.jsonl"):
            self.assertFalse(p.wants(rel_only(rel)), rel)

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / NANOBOT_REL)
        rows = self.rows_for(NanobotParser(), NANOBOT_REL)
        self.assertEqual(len(rows), 7)
        self.assertEqual((rows[-1].turn_type, rows[-1].session_id), ("system", NANOBOT_KEY))
        self.assertIn("parser:", rows[-1].text)


from doubleagent import vscode_state
from doubleagent.parsers.cody import CodyParser, chat_time
from doubleagent.parsers.pearai import PearAiParser
from doubleagent.parsers.twinny import TwinnyParser
from fixtures import (
    CODY_ACCOUNT,
    CODY_AGENTIC_CHAT,
    CODY_CHAT,
    CODY_JB_REL,
    CODY_MODEL,
    CODY_MODEL_SWITCHED,
    CODY_TOKEN,
    CODY_VSCDB_REL,
    CODY_VSCODE_CHAT,
    PEARAI_GS,
    PEARAI_ROO,
    PEARAI_SEARCH_SESSION,
    PEARAI_SESSION,
    PEARAI_TASK,
    PEARAI_UI_TASK,
    TWINNY_ACTIVE,
    TWINNY_API_KEY,
    TWINNY_CONVERSATION,
    TWINNY_VSCDB_REL,
    _vscdb,
    cody_vscode_state,
)


class ReadsAgentsRoutingTests(ParserBase):
    """`reads_agents` offers a `vscode` state.vscdb to the Cody and Twinny
    parsers as well as to the VS Code parser, and nothing else to them."""

    def test_state_vscdb_offered_to_extension_parsers(self):
        parsers = by_agent()
        art = next(a for a in self.col.artifacts if a.rel == CODY_VSCDB_REL)
        self.assertEqual(art.agent, "vscode")
        offered = cli.parsers_for(art, parsers)
        self.assertEqual({p.agent for p in offered}, {"vscode", "cody", "twinny"})
        self.assertEqual(len(offered), len(set(map(id, offered))))
        self.assertFalse(any(p.wants(art) for p in offered if p.agent == "vscode"))
        other = next(a for a in self.col.artifacts if a.agent == "codex-cli")
        self.assertEqual({p.agent for p in cli.parsers_for(other, parsers)}, {"codex-cli"})

    def test_cli_attributes_rows_to_the_extension(self):
        rows, _counts, problems, _ = cli.collect_rows(self.col, Options(), [])
        self.assertEqual(problems, [])
        from_vscdb = {
            r.agent for r in rows if r.source_file.endswith("/User/globalStorage/state.vscdb")
        }
        self.assertEqual(from_vscdb, {"cody", "twinny"})
        rows, _, _, _ = cli.collect_rows(self.col, Options(), ["twinny"])
        self.assertEqual({r.agent for r in rows}, {"twinny"})

    def test_fork_state_vscdb_reaches_cody(self):
        # Cody installed in Cursor writes to Cursor's state.vscdb, which the
        # catalog attributes to `cursor`, not `vscode`.
        rel = ".config/Cursor/User/globalStorage/state.vscdb"
        _vscdb(self.home / rel, {"sourcegraph.cody-ai": cody_vscode_state()})
        col = open_input(self.tmp / "home", self.cat, host="h1")
        art = next(a for a in col.artifacts if a.rel == rel)
        self.assertEqual(art.agent, "cursor")
        self.assertIn("cody", {p.agent for p in cli.parsers_for(art, by_agent())})
        rows, _, problems, _ = cli.collect_rows(col, Options(), ["cody"])
        self.assertEqual(problems, [])
        from_cursor = [r for r in rows if r.source_file.endswith(rel)]
        self.assertTrue(from_cursor)
        self.assertEqual({r.agent for r in from_cursor}, {"cody"})
        self.assertIn(CODY_VSCODE_CHAT, {r.session_id for r in from_cursor})


class CodyTests(ParserBase):
    def test_rows(self):
        rows = self.rows_for(CodyParser(), CODY_JB_REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "user",
                "system",
                "assistant",
                "system",
                "user",
                "system",
                "assistant",
                "tool_use",
                "system",
                "tool_result",
                "system",
                "assistant",
                "system",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.source_line, r.git_branch),
                ("h1", "alice", "cody", 1, ""),
            )
        first, user, model, asst = rows[:4]
        self.assertEqual({r.session_id for r in rows[:4]}, {CODY_CHAT})
        self.assertEqual({r.timestamp_utc for r in rows[:4]}, {"2026-10-03T10:00:00.000Z"})
        self.assertEqual({r.timestamp_utc for r in rows[4:]}, {"2026-10-03T10:30:00.000Z"})
        self.assertEqual((model.text, model.model), ("model: " + CODY_MODEL, CODY_MODEL))
        # Each chat tracks its own model, so the agentic chat starts again.
        self.assertEqual(rows[6].text, "model: " + CODY_MODEL)
        self.assertEqual(rows[6].session_id, CODY_AGENTIC_CHAT)
        decision = rows[9]
        self.assertEqual(
            (decision.text, decision.tool_use_id, decision.tool_name),
            (
                "permission decision: confirmation state=success title=Run terminal command"
                "\npytest -q\nAllow Cody to run this command?",
                "toolu_01",
                "run_terminal_command",
            ),
        )
        self.assertEqual(
            (rows[11].text, rows[11].model),
            ("model: %s -> %s" % (CODY_MODEL, CODY_MODEL_SWITCHED), CODY_MODEL_SWITCHED),
        )
        self.assertEqual(
            first.text, "chat: Fix flaky test | account=%s | interactions=1" % CODY_ACCOUNT
        )
        self.assertEqual(
            user.text, "why is test_login flaky?\n[context: /srv/proj/tests/test_login.py]"
        )
        self.assertEqual((user.model, user.project_path), ("", ""))
        self.assertEqual(
            (asst.text, asst.model),
            ("It depends on wall-clock time.", "anthropic::2024-10-22::claude-sonnet-4-latest"),
        )
        use, result = rows[8], rows[10]
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text),
            ("run_terminal_command", "toolu_01", '{"command":"pytest -q"}'),
        )
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text, result.session_id),
            ("run_terminal_command", "toolu_01", "3 passed", CODY_AGENTIC_CHAT),
        )
        self.assertEqual(rows[-1].text, "error: rate limit exceeded")

    def test_vscode_state_row(self):
        rows = self.rows_for(CodyParser(), CODY_VSCDB_REL)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows],
            [
                ("system", "chat:  | account=%s | interactions=1" % CODY_ACCOUNT),
                ("user", "explain build.sh"),
                ("system", "model: anthropic::2024-10-22::claude-sonnet-4-latest"),
                ("assistant", "It runs make."),
            ],
        )
        self.assertEqual(
            {(r.agent, r.session_id, r.source_line, r.timestamp_utc) for r in rows},
            {("cody", CODY_VSCODE_CHAT, 0, "2026-10-03T09:00:00.000Z")},
        )
        self.assertNotIn(CODY_TOKEN, " ".join(r.text for r in rows))

    def test_thinking_opt_in(self):
        # Cody records no reasoning; the option must not invent rows.
        plain = self.rows_for(CodyParser(), CODY_JB_REL)
        self.assertEqual(self.rows_for(CodyParser(), CODY_JB_REL, include_thinking=True), plain)

    def test_chat_time_and_account_collision(self):
        self.assertEqual(
            chat_time("Sat, 03 Oct 2026 10:00:00 GMT", None), "2026-10-03T10:00:00.000Z"
        )
        self.assertEqual(
            chat_time("0f0e-uuid", "Sat, 03 Oct 2026 11:00:00 GMT"), "2026-10-03T11:00:00.000Z"
        )
        self.assertEqual(chat_time("0f0e-uuid", None), "")
        hist = json.loads((self.home / CODY_JB_REL).read_text(encoding="utf-8"))
        hist["https://example.org/-bob"] = {
            "chat": {CODY_CHAT: hist[CODY_ACCOUNT]["chat"][CODY_CHAT]}
        }
        (self.home / CODY_JB_REL).write_text(json.dumps(hist), encoding="utf-8")
        sids = {r.session_id for r in self.rows_for(CodyParser(), CODY_JB_REL)}
        self.assertEqual(
            sids,
            {
                CODY_ACCOUNT + "/" + CODY_CHAT,
                "https://example.org/-bob/" + CODY_CHAT,
                CODY_AGENTIC_CHAT,
            },
        )

    def test_not_wanted(self):
        for rel in (
            ".local/share/Cody-nodejs/user-settings.json",
            ".config/Code/User/globalStorage/rjmacarthy.twinny/twinny-providers.json",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertFalse(CodyParser().wants(art), rel)
        # A state.vscdb that is not SQLite (or has no Cody row) yields nothing.
        self.assertEqual(
            self.rows_for(CodyParser(), ".config/Code/User/globalStorage/state.vscdb"), []
        )
        self.assertEqual(self.rows_for(CodyParser(), TWINNY_VSCDB_REL), [])

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / CODY_JB_REL)
        rows = self.rows_for(CodyParser(), CODY_JB_REL)
        self.assertEqual(len(rows), 15)
        self.assertEqual([r.turn_type for r in rows[:4]], ["system", "user", "system", "assistant"])
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("parser: chat history did not parse; recovered 2 chat(s)", rows[-1].text)

    def test_cut_mid_chat_keeps_earlier_interactions(self):
        text = (self.home / CODY_JB_REL).read_text(encoding="utf-8")
        cut = text.index('"All three pass.')
        (self.home / CODY_JB_REL).write_text(text[:cut], encoding="utf-8")
        rows = self.rows_for(CodyParser(), CODY_JB_REL)
        texts = [r.text for r in rows]
        self.assertIn("It depends on wall-clock time.", texts)
        self.assertIn("Running tests.", texts)
        self.assertNotIn("All three pass.", texts)
        self.assertEqual(rows[-1].turn_type, "system")


class TwinnyTests(ParserBase):
    def test_rows(self):
        # The rows live only in the -wal sidecar: read through sqlite_util.
        self.assertTrue((self.home / (TWINNY_VSCDB_REL + "-wal")).is_file())
        rows = self.rows_for(TwinnyParser(), TWINNY_VSCDB_REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "user",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
                "tool_use",
                "tool_result",
                "system",
                "system",
                "assistant",
                "tool_use",
                "tool_result",
                "system",
                "tool_use",
                "tool_result",
                "system",
                "system",
                "user",
            ],
        )
        for r in rows[:17]:
            self.assertEqual(
                (r.agent, r.session_id, r.timestamp_utc, r.source_line, r.project_path),
                ("twinny", TWINNY_CONVERSATION, "2026-10-03T12:00:05.000Z", 0, ""),
            )
        self.assertEqual(rows[0].text, "conversation: List the tests | messages=3")
        self.assertEqual(
            (rows[2].text, rows[2].model), ("model: qwen2.5-coder:7b", "qwen2.5-coder:7b")
        )
        self.assertEqual((rows[3].text, rows[3].model), ("Two tests fail.", "qwen2.5-coder:7b"))
        self.assertEqual(
            (rows[4].tool_name, rows[4].tool_use_id, rows[4].text),
            ("run_command", "step-1", '{"command":"npm test"}'),
        )
        self.assertEqual((rows[5].tool_use_id, rows[5].text), ("step-1", "2 failing"))
        self.assertEqual(rows[7].text, "[failed] permission denied")
        self.assertEqual(rows[8].text, 'secret shield withheld: [{"count":1,"kind":"aws-key"}]')
        self.assertEqual(
            (rows[9].text, rows[9].model),
            ("model: qwen2.5-coder:7b -> qwen2.5-coder:14b", "qwen2.5-coder:14b"),
        )
        self.assertEqual((rows[11].text, rows[12].text), ("rm -rf build", "[waiting]"))
        self.assertEqual(
            (rows[13].text, rows[13].tool_use_id, rows[13].tool_name),
            ("permission decision: waiting approval=command", "step-3", "run_command"),
        )
        self.assertEqual(rows[15].text, "[skipped] skipped by the user")
        self.assertEqual(
            (rows[16].text, rows[16].tool_use_id, rows[16].tool_name),
            ("permission decision: skipped", "step-4", "delete_file"),
        )
        self.assertEqual(
            {r.session_id for r in rows[17:]}, {TWINNY_ACTIVE}
        )  # unsaved active conversation
        self.assertEqual(rows[18].text, "unsaved question")

    def test_thinking_opt_in(self):
        rows = self.rows_for(TwinnyParser(), TWINNY_VSCDB_REL, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["run the suite"])
        self.assertEqual(
            rows[rows.index(next(r for r in rows if r.turn_type == "thinking")) + 1].text,
            "Two tests fail.",
        )

    def test_api_key_never_emitted(self):
        out = self.tmp / "out"
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                cli.main(["timeline", str(self.tmp / "home"), "-o", str(out), "--host", "h1"]), 0
            )
        for name in ("timeline.jsonl", "sessions.jsonl"):
            text = (out / name).read_text(encoding="utf-8")
            self.assertNotIn(TWINNY_API_KEY, text, name)
            self.assertNotIn(CODY_TOKEN, text, name)
        self.assertIn(TWINNY_CONVERSATION, (out / "sessions.jsonl").read_text(encoding="utf-8"))
        # Nor from a value the parser cannot decode.
        db = self.home / ".config/Code - Insiders/User/globalStorage/state.vscdb"
        _vscdb(
            db,
            {"rjmacarthy.twinny": '{"twinny.inference-providers":{"apiKey":"%s"' % TWINNY_API_KEY},
        )
        col = open_input(self.tmp / "home", self.cat, host="h1")
        art = next(
            a
            for a in col.artifacts
            if a.rel == ".config/Code - Insiders/User/globalStorage/state.vscdb"
        )
        rows = list(TwinnyParser().parse(art, Options()))
        self.assertEqual([r.turn_type for r in rows], ["system"])
        self.assertTrue(
            rows[0].text.startswith(
                "parser: ItemTable value for rjmacarthy.twinny is not valid JSON"
            )
        )
        self.assertNotIn(TWINNY_API_KEY, rows[0].text)

    def test_secret_rows_never_read(self):
        db = self.home / TWINNY_VSCDB_REL
        key = 'secret://{"extensionId":"rjmacarthy.twinny","key":"gateway"}'
        self.assertEqual(vscode_state.read_item(db, key), (None, []))
        values, _ = vscode_state.read_items(db, [key, "rjmacarthy.twinny"])
        self.assertEqual(list(values), ["rjmacarthy.twinny"])

    def test_not_wanted(self):
        art = next(
            a
            for a in self.col.artifacts
            if a.rel == ".config/Code/User/globalStorage/rjmacarthy.twinny/twinny-providers.json"
        )
        self.assertEqual(art.agent, "twinny")
        self.assertFalse(TwinnyParser().wants(art))
        self.assertEqual(
            self.rows_for(TwinnyParser(), ".config/Code/User/globalStorage/state.vscdb"), []
        )
        self.assertEqual(self.rows_for(TwinnyParser(), CODY_VSCDB_REL), [])

    def test_truncated_line_is_reported_not_fatal(self):
        # A damaged SQLite file is one system row, not an exception.
        db = self.home / CODY_VSCDB_REL
        data = db.read_bytes()
        db.write_bytes(data[:100] + b"\x00" * (len(data) - 100))
        rows = self.rows_for(TwinnyParser(), CODY_VSCDB_REL)
        self.assertEqual([r.turn_type for r in rows], ["system"])
        self.assertIn("parser: state.vscdb unreadable", rows[0].text)


class PearAiTests(ParserBase):
    SESSION = ".pearai/sessions/%s.json" % PEARAI_SESSION
    API = PEARAI_ROO + "tasks/%s/api_conversation_history.json" % PEARAI_TASK

    def test_rows(self):
        rows = self.rows_for(PearAiParser(), self.SESSION)
        self.assertEqual(
            [(r.turn_type, r.source_line) for r in rows],
            [
                ("system", 0),
                ("user", 1),
                ("system", 2),
                ("assistant", 2),
                ("user", 3),
                ("system", 4),
                ("assistant", 4),
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.agent, r.session_id, r.project_path, r.timestamp_utc),
                ("pearai", PEARAI_SESSION, "/srv/proj", "2026-10-03T13:00:00.000Z"),
            )
        self.assertEqual(
            rows[0].text,
            "session start: why does build.sh fail | integration=continue | "
            "history=4 perplexityHistory=0",
        )
        self.assertEqual(rows[1].text, "why does build.sh fail\n[context: /srv/proj/build.sh]")
        self.assertEqual(
            (rows[3].text, rows[3].model), ("The make target is missing.", "pearai_model")
        )
        # promptLogs[].completionOptions.model: the first one starts, a new one switches
        self.assertEqual(
            [(r.text, r.model) for r in (rows[2], rows[5])],
            [
                ("model: pearai_model", "pearai_model"),
                ("model: pearai_model -> pearai_model_2", "pearai_model_2"),
            ],
        )
        rows = self.rows_for(PearAiParser(), ".pearai/sessions/%s.json" % PEARAI_SEARCH_SESSION)
        self.assertEqual(
            [(r.turn_type, r.source_line, r.text) for r in rows][1:],
            [
                ("user", 1, "latest make release"),
                (
                    "assistant",
                    2,
                    "GNU make 4.4.1.\n[citations: https://www.gnu.org/software/make/]",
                ),
            ],
        )
        self.assertIn("integration=perplexity", rows[0].text)

    def test_task_xml_tool_calls(self):
        rows = self.rows_for(PearAiParser(), self.API)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["user", "system", "assistant", "tool_use", "tool_result", "tool_use"],
        )
        self.assertEqual(
            {(r.agent, r.session_id, r.project_path, r.model) for r in rows},
            {("pearai", PEARAI_TASK, "/srv/proj", "")},
        )  # project from state.vscdb taskHistory
        user, env, asst, use, result, done = rows
        self.assertEqual(
            (user.text, user.timestamp_utc), ("run the tests", "2026-10-03T14:00:00.000Z")
        )
        self.assertTrue(env.text.startswith("<environment_details>"))
        self.assertEqual(asst.text, "I will run them.")
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text, use.source_line),
            ("execute_command", "2", "npm test", 2),
        )
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text, result.timestamp_utc),
            ("execute_command", "2", "12 passing", "2026-10-03T14:00:09.000Z"),
        )
        self.assertEqual(
            (done.tool_name, done.tool_use_id, done.text),
            ("attempt_completion", "4", "All 12 tests pass."),
        )

    def test_thinking_opt_in(self):
        self.assertNotIn("thinking", [r.turn_type for r in self.rows_for(PearAiParser(), self.API)])
        rows = self.rows_for(PearAiParser(), self.API, include_thinking=True)
        self.assertEqual([r.text for r in rows if r.turn_type == "thinking"], ["use npm"])

    def test_ui_messages_preferred(self):
        task = PEARAI_ROO + "tasks/%s/" % PEARAI_UI_TASK
        self.assertEqual(self.rows_for(PearAiParser(), task + "api_conversation_history.json"), [])
        rows = self.rows_for(PearAiParser(), task + "ui_messages.json")
        self.assertEqual(rows[0].turn_type, "user")
        self.assertEqual({r.session_id for r in rows}, {PEARAI_UI_TASK})
        self.assertIn("tool_result", [r.turn_type for r in rows])

    def test_not_wanted(self):
        for rel in (
            ".pearai/config.json",
            ".pearai/sessions/sessions.json",
            PEARAI_GS + "state.vscdb",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertEqual(art.agent, "pearai")
            self.assertFalse(PearAiParser().wants(art), rel)

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / self.SESSION)
        rows = self.rows_for(PearAiParser(), self.SESSION)
        self.assertEqual(
            [r.turn_type for r in rows],
            ["system", "user", "system", "assistant", "user", "system", "assistant", "system"],
        )
        self.assertIn("parser:", rows[-1].text)
        write_bad_line(self.home / self.API)
        rows = self.rows_for(PearAiParser(), self.API)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("parser:", rows[-1].text)


from doubleagent.parsers.muse_code import MuseCodeParser, micros_to_utc, result_text
from doubleagent.parsers.muse_code import args_summary as muse_args_summary
from fixtures import (
    MUSE_CHILD,
    MUSE_CHILD_REL,
    MUSE_DIR,
    MUSE_HISTORY_REL,
    MUSE_MODEL,
    MUSE_MODEL_2,
    MUSE_REL,
    MUSE_RUN,
    MUSE_SESSION,
    MUSE_T0,
    MUSE_TRUST_REL,
    _muse_env,
    _muse_run,
)


class MuseCodeTests(ParserBase):
    def test_secondary(self):
        # The history file is a secondary source, the transcript is not (#122).
        p = MuseCodeParser()
        self.assertTrue(p.secondary(self.artifact(MUSE_HISTORY_REL)))
        self.assertFalse(p.secondary(self.artifact(MUSE_REL)))

    def append(self, rel, *records):
        with open(self.home / rel, "a", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")

    def test_rows(self):
        rows = self.rows_for(MuseCodeParser(), MUSE_REL)
        self.assertEqual(
            [r.turn_type for r in rows],
            [
                "system",
                "system",
                "system",
                "system",
                "user",
                "tool_use",
                "tool_result",
                "system",
                "system",
                "system",
                "assistant",
                "system",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "muse-code", MUSE_SESSION)
            )
            self.assertEqual((r.project_path, r.git_branch), ("/srv/proj", "main"))
            self.assertTrue(r.timestamp_utc.endswith("Z"), r)
        mode, model, security, name, user, use, result, req, review, dec, asst, change = rows
        self.assertEqual({r.model for r in rows[:-1]}, {MUSE_MODEL})
        self.assertEqual(
            (mode.text, mode.timestamp_utc),
            (
                "permission mode: approval=on_request reviewer=auto_review profile=:auto-review"
                " cause=new_session_default format=profile_v1",
                "2026-10-01T09:00:00.000Z",
            ),
        )
        self.assertEqual(
            (model.text, model.timestamp_utc),
            ("model: muse-spark-1.3-contributor provider=meta", "2026-10-01T09:00:00.100Z"),
        )
        self.assertEqual(
            (security.text, security.timestamp_utc),
            ("permission mode: security_mode=example_mode", "2026-10-01T09:00:00.250Z"),
        )
        self.assertEqual(
            (review.tool_name, review.tool_use_id, review.text, review.timestamp_utc),
            (
                "network",
                "call_02",
                "permission decision: allow kind=automated_review_completed risk_level=low"
                " user_authorization=not_required status=completed"
                " Fetching a package index is low risk.",
                "2026-10-01T09:00:05.900Z",
            ),
        )
        self.assertEqual(
            (change.text, change.model, change.timestamp_utc),
            (
                "model: muse-spark-1.3-contributor -> muse-spark-1.3-fast",
                MUSE_MODEL_2,
                "2026-10-01T09:00:15.000Z",
            ),
        )
        self.assertEqual(
            (name.text, name.timestamp_utc),
            ("session name: quiet-lyra", "2026-10-01T09:00:00.300Z"),
        )
        self.assertEqual(
            (user.text, user.timestamp_utc), ("fix the failing test", "2026-10-01T09:00:01.000Z")
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text), ("bash", "call_01", "npm test")
        )
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text),
            ("bash", "call_01", "[exit 1] 1 failing"),
        )
        self.assertEqual(
            (req.tool_name, req.tool_use_id, req.text),
            ("network", "call_02", "approval requested: https registry.example.org:443"),
        )
        self.assertEqual(
            (dec.tool_name, dec.tool_use_id, dec.text),
            (
                "network",
                "call_02",
                "permission decision: approved source=llm_judge policy_result=allow amendment=-",
            ),
        )
        self.assertEqual(asst.text, "The test fails because the fixture date is stale.")
        self.assertEqual([r.source_line for r in rows], [1, 2, 4, 5, 8, 13, 17, 18, 19, 20, 22, 24])

    def test_thinking_opt_in(self):
        rows = self.rows_for(MuseCodeParser(), MUSE_REL, include_thinking=True)
        thinking = [r for r in rows if r.turn_type == "thinking"]
        # The delta repeats the committed summary; the encrypted reasoning
        # record has empty text. One row.
        self.assertEqual(
            [(r.text, r.source_line, r.model) for r in thinking],
            [("Running the tests first.", 10, MUSE_MODEL)],
        )

    def test_subagent_takes_parent_project(self):
        rows = self.rows_for(MuseCodeParser(), MUSE_CHILD_REL)
        self.assertEqual(
            [r.turn_type for r in rows], ["system", "system", "system", "tool_use", "tool_result"]
        )
        self.assertEqual({r.session_id for r in rows}, {MUSE_CHILD})
        self.assertEqual({(r.project_path, r.git_branch) for r in rows}, {("/srv/proj", "main")})
        # Each subagent log tracks its own permission mode and model.
        self.assertTrue(rows[0].text.startswith("permission mode: approval=on_request"))
        self.assertEqual(rows[1].text, "model: muse-spark-1.3-contributor provider=meta")
        rows = rows[2:]
        self.assertEqual(
            rows[0].text, "subagent task: You are a reminder observer for the main agent."
        )
        self.assertEqual(
            (rows[1].tool_name, rows[1].tool_use_id), ("submit_reminder_decision", "call_10")
        )
        self.assertEqual(
            (rows[2].tool_name, rows[2].tool_use_id, rows[2].text),
            ("submit_reminder_decision", "call_10", "reminder decision recorded"),
        )

    def test_subagent_without_parent(self):
        (self.home / MUSE_REL).unlink()
        rows = self.rows_for(MuseCodeParser(), MUSE_CHILD_REL)
        self.assertEqual(len(rows), 5)
        self.assertEqual({(r.project_path, r.git_branch) for r in rows}, {("", "")})

    def test_history(self):
        rows = self.rows_for(MuseCodeParser(), MUSE_HISTORY_REL)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(
            (r.turn_type, r.text, r.session_id, r.project_path, r.timestamp_utc, r.source_line),
            ("user", "fix the failing test", MUSE_SESSION, "/srv/proj", "", 1),
        )

    def test_cut_log_and_other_run_events(self):
        s, r, t = MUSE_SESSION, MUSE_RUN, MUSE_T0
        self.append(
            MUSE_REL,
            _muse_run(
                s,
                24,
                t + 30000000,
                r,
                {
                    "kind": "inbox_item_queued",
                    "source": {"source": "user_steer"},
                    "payload": {"prompt": "also check the linter"},
                },
                40,
            ),
            _muse_run(
                s,
                25,
                t + 31000000,
                r,
                {"kind": "reasoning_summary_delta", "message_id": "m9", "text": "First."},
                41,
            ),
            _muse_run(
                s,
                26,
                t + 31100000,
                r,
                {"kind": "reasoning_summary_delta", "message_id": "m9", "text": "Second."},
                42,
            ),
            _muse_run(
                s,
                27,
                t + 32000000,
                r,
                {"kind": "terminal", "terminal": "failed", "reason": "402 Payment Required"},
                43,
            ),
            _muse_env(
                s,
                28,
                t + 33000000,
                "user_shell.command",
                {"record": {"command_id": "sh1", "command_text": "ls"}},
            ),
            _muse_env(
                s,
                29,
                t + 33100000,
                "user_shell.result",
                {"record": {"exit_code": 2, "visible_output": "no such file"}},
            ),
            _muse_env(s, 30, t + 34000000, "some.future.type", {"kind": "x"}),
        )
        rows = self.rows_for(MuseCodeParser(), MUSE_REL, include_thinking=True)[-5:]
        self.assertEqual(
            [(r.turn_type, r.text, r.source_line) for r in rows],
            [
                ("user", "also check the linter", 26),
                ("thinking", "First.\n\nSecond.", 28),
                ("system", "run failed: 402 Payment Required", 29),
                ("tool_use", "ls", 30),
                ("tool_result", "[exit 2] no such file", 31),
            ],
        )
        self.assertEqual({(r.tool_name, r.tool_use_id) for r in rows[3:]}, {("user_shell", "sh1")})

    def test_helpers(self):
        self.assertEqual(micros_to_utc(MUSE_T0), "2026-10-01T09:00:00.000Z")
        self.assertEqual(micros_to_utc(None), "")
        self.assertEqual(muse_args_summary('{"url": "https://example.org"}'), "https://example.org")
        self.assertEqual(muse_args_summary({"cmd": "make"}), "make")
        self.assertEqual(muse_args_summary("not json"), "not json")
        self.assertEqual(result_text('{"output": "ok", "exit_code": 0}'), "ok")
        self.assertEqual(result_text("tool failed: 403"), "tool failed: 403")

    def test_not_wanted(self):
        for rel in (
            ".config/muse/settings.json",
            MUSE_DIR + "approval-review/7a7a7a7a-0000-4000-8000-000000000001.jsonl",
        ):
            art = next(a for a in self.col.artifacts if a.rel == rel)
            self.assertEqual(art.agent, "muse-code")
            self.assertFalse(MuseCodeParser().wants(art), rel)

    def test_not_muse_file_gives_no_rows(self):
        with open(self.home / MUSE_REL, "w", encoding="utf-8") as fh:
            fh.write('{"type": "user", "content": "x"}\n')
        self.assertEqual(self.rows_for(MuseCodeParser(), MUSE_REL), [])

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / MUSE_REL)
        rows = self.rows_for(MuseCodeParser(), MUSE_REL)
        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[-1].turn_type, "system")
        self.assertIn("parser:", rows[-1].text)
        self.assertEqual((rows[-1].source_line, rows[-1].session_id), (26, MUSE_SESSION))

    def test_reconfigure_without_earlier_model_uses_previous(self):
        rel = (
            MUSE_DIR.replace(MUSE_SESSION, "01a0f000-0000-7000-8000-0000000000ff") + "session.jsonl"
        )
        _jsonl(
            self.home / rel,
            [
                _muse_env(
                    "s2",
                    1,
                    MUSE_T0,
                    "runtime.model_reconfigure.completed",
                    {
                        "record": {
                            "effective": {"model_id": MUSE_MODEL_2},
                            "previous": {"model_id": MUSE_MODEL},
                            "apply_outcome": "applied",
                        }
                    },
                ),
                _muse_env(
                    "s2",
                    2,
                    MUSE_T0 + 1000000,
                    "runtime.model_reconfigure.completed",
                    {"record": {"effective": {"model_id": MUSE_MODEL_2}}},
                ),
            ],
        )
        self.col = open_input(self.tmp / "home", self.cat, host="h1")
        rows = self.rows_for(MuseCodeParser(), rel)
        self.assertEqual(
            [(r.text, r.model, r.source_line) for r in rows],
            [
                ("model: %s" % MUSE_MODEL, MUSE_MODEL, 1),
                (
                    "model: %s -> %s apply_outcome=applied" % (MUSE_MODEL, MUSE_MODEL_2),
                    MUSE_MODEL_2,
                    1,
                ),
                # A `/model` to the same model keeps its row.
                ("model: %s -> %s" % (MUSE_MODEL_2, MUSE_MODEL_2), MUSE_MODEL_2, 2),
            ],
        )

    def test_trusted_projects(self):
        art = next(a for a in self.col.artifacts if a.rel == MUSE_TRUST_REL)
        rows = list(MuseCodeParser().parse(art, Options()))
        mtime = file_mtime(art)
        self.assertTrue(mtime)
        self.assertEqual(
            [(r.turn_type, r.text, r.project_path) for r in rows],
            [
                (
                    "system",
                    "permission setting: projects./srv/proj.decision=trusted"
                    " (from .config/muse/trust.json, file mtime)",
                    "/srv/proj",
                ),
                (
                    "system",
                    "permission setting: projects./srv/other.decision=trusted"
                    " (from .config/muse/trust.json, file mtime)",
                    "/srv/other",
                ),
            ],
        )
        for r in rows:
            self.assertEqual((r.timestamp_utc, r.session_id, r.source_line), (mtime, "", 1))

    def test_unreadable_trust_file(self):
        (self.home / MUSE_TRUST_REL).write_text("[1, 2", encoding="utf-8")
        rows = self.rows_for(MuseCodeParser(), MUSE_TRUST_REL)
        self.assertEqual(
            [(r.turn_type, r.text, r.session_id) for r in rows],
            [("system", "parser: trust.json is not a JSON object", "")],
        )
        self.assertTrue(rows[0].timestamp_utc)
        # The session log still yields every row.
        self.assertEqual(len(self.rows_for(MuseCodeParser(), MUSE_REL)), 12)


from doubleagent.parsers.ollama import OllamaParser, call_text
from fixtures import (
    OLLAMA_ATTACHMENT,
    OLLAMA_CHAT,
    OLLAMA_DB_REL,
    OLLAMA_MANIFEST_REL,
    OLLAMA_USER_EMAIL,
    OLLAMA_USER_NAME,
    OLLAMA_WIN_DB_REL,
)


class OllamaTests(ParserBase):
    HISTORY_REL = ".ollama/history"
    CALL_ID = OLLAMA_CHAT + ":1"

    def run_timeline(self, name, *extra):
        import contextlib

        out = self.tmp / name
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(
                ["timeline", str(self.tmp / "home"), "-o", str(out), "--agent", "ollama", *extra]
            )
        self.assertEqual(rc, 0)
        return out

    def test_rows(self):
        rows = [
            r
            for r in self.rows_for(OllamaParser(), OLLAMA_DB_REL)
            if not model_or_permission_row(r)
        ]
        self.assertEqual(
            [r.turn_type for r in rows], ["user", "tool_use", "tool_result", "assistant"]
        )
        for r in rows:
            self.assertEqual(
                (r.host, r.user, r.agent, r.session_id), ("h1", "alice", "ollama", OLLAMA_CHAT)
            )
            self.assertEqual((r.project_path, r.git_branch), ("", ""))
        user, use, result, asst = rows
        self.assertEqual(
            (user.text, user.timestamp_utc, user.model, user.source_line),
            (
                "summarise https://example.invalid/notes\n[attachment: notes.txt, 5 bytes]",
                "2026-03-01T17:00:00.500Z",
                "",
                1,
            ),
        )
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.text, use.model, use.timestamp_utc),
            (
                "web_fetch",
                self.CALL_ID,
                "https://example.invalid/notes",
                "gemma4:e4b",
                "2026-03-01T17:00:01.250Z",
            ),
        )
        self.assertEqual(use.source_line, 1)  # tool_calls.id
        self.assertEqual(
            (result.tool_name, result.tool_use_id, result.text, result.timestamp_utc),
            ("web_fetch", self.CALL_ID, "Release 2.0 adds X.", "2026-03-01T17:00:03.000Z"),
        )
        self.assertEqual(
            (asst.text, asst.model, asst.timestamp_utc, asst.source_line),
            ("Release 2.0 adds X.", "qwen3:8b", "2026-03-01T17:00:04.125Z", 4),
        )

    def test_model_rows(self):
        for thinking in (False, True):
            rows = self.rows_for(OllamaParser(), OLLAMA_DB_REL, include_thinking=thinking)
            state = [r for r in rows if model_or_permission_row(r)]
            self.assertEqual(
                [(r.text, r.timestamp_utc, r.model, r.source_line, r.session_id) for r in state],
                [
                    ("model: gemma4:e4b", "2026-03-01T17:00:01.250Z", "gemma4:e4b", 2, OLLAMA_CHAT),
                    (
                        "model: gemma4:e4b -> qwen3:8b",
                        "2026-03-01T17:00:04.125Z",
                        "qwen3:8b",
                        4,
                        OLLAMA_CHAT,
                    ),
                ],
            )
            # each sits immediately before its message's first row
            self.assertEqual(rows[rows.index(state[0]) + 1].source_line, 2 if thinking else 1)
            self.assertEqual(rows[rows.index(state[1]) + 1].text, "Release 2.0 adds X.")

    def test_thinking_opt_in(self):
        rows = self.rows_for(OllamaParser(), OLLAMA_DB_REL, include_thinking=True)
        rows = [r for r in rows if not model_or_permission_row(r)]
        self.assertEqual(
            [r.turn_type for r in rows],
            ["user", "thinking", "tool_use", "tool_result", "assistant"],
        )
        t = rows[1]
        self.assertEqual(
            (t.text, t.model, t.timestamp_utc, t.source_line),
            ("need to fetch the page", "gemma4:e4b", "2026-03-01T17:00:01.250Z", 2),
        )

    def test_schema_version_16_gives_the_same_rows(self):
        def strip(rows):
            return [{k: v for k, v in r.as_dict().items() if k != "source_file"} for r in rows]

        for thinking in (False, True):
            mac = self.rows_for(OllamaParser(), OLLAMA_DB_REL, include_thinking=thinking)
            win = self.rows_for(OllamaParser(), OLLAMA_WIN_DB_REL, include_thinking=thinking)
            self.assertTrue(mac)
            self.assertEqual(strip(win), strip(mac))
            self.assertTrue(all(r.source_file.endswith(OLLAMA_WIN_DB_REL) for r in win))

    def test_account_and_attachment_bytes_never_emitted(self):
        out = self.run_timeline("out", "--include-thinking")
        self.assertTrue(read_jsonl(out / "timeline.jsonl"))
        forbidden = (
            OLLAMA_USER_NAME,
            OLLAMA_USER_EMAIL,
            '"free"',
            "0190a000-0000-7000-8000-00000000d001",  # settings.device_id
            OLLAMA_ATTACHMENT.decode(),
            OLLAMA_ATTACHMENT.hex(),
        )
        for name in ("timeline.jsonl", "sessions.jsonl"):
            text = (out / name).read_text(encoding="utf-8")
            for f in forbidden:
                self.assertNotIn(f, text, (name, f))

    def test_history_and_slash_commands(self):
        rows = self.rows_for(OllamaParser(), self.HISTORY_REL)
        self.assertEqual(
            [(r.turn_type, r.text, r.source_line) for r in rows],
            [
                ("user", "why is the sky blue", 1),
                ("system", "slash command: /set nohistory", 2),
                ("system", "slash command: /bye", 3),
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.timestamp_utc, r.session_id, r.model, r.agent), ("", "", "", "ollama")
            )

    def test_undated_history_in_timeline_and_sessions(self):
        # cli.collect_rows sorts on (timestamp_utc == "", ...), so undated
        # rows come last; filters.RowFilter.in_window drops them under
        # --since unless --keep-undated; model.summarise skips rows with no
        # session_id, so the history adds no session.
        out = self.run_timeline("all")
        rows = read_jsonl(out / "timeline.jsonl")
        sessions = read_jsonl(out / "sessions.jsonl")
        hist = [r for r in rows if r["source_file"].endswith("/.ollama/history")]
        self.assertEqual(len(hist), 3)
        self.assertEqual(rows[-3:], hist)
        self.assertTrue(all(r["timestamp_utc"] for r in rows[:-3]))
        self.assertEqual({s["session_id"] for s in sessions}, {OLLAMA_CHAT})
        for s in sessions:
            self.assertEqual(
                (s["first_timestamp_utc"], s["last_timestamp_utc"], s["models"]),
                (
                    "2026-03-01T17:00:00.500Z",
                    "2026-03-01T17:00:04.125Z",
                    ["gemma4:e4b", "qwen3:8b"],
                ),
            )
        rows = read_jsonl(self.run_timeline("since", "--since", "2026-03-01") / "timeline.jsonl")
        self.assertTrue(rows)
        self.assertFalse([r for r in rows if not r["timestamp_utc"]])
        out = self.run_timeline("undated", "--since", "2026-03-01", "--keep-undated")
        rows = read_jsonl(out / "timeline.jsonl")
        self.assertEqual(len([r for r in rows if not r["timestamp_utc"]]), 3)

    def test_tool_pairing_and_placeholder(self):
        import sqlite3

        c = OLLAMA_CHAT
        con = sqlite3.connect(str(self.home / OLLAMA_DB_REL))
        con.executescript(
            "INSERT INTO messages (id, chat_id, role, content, model_name, created_at) VALUES"
            " (5, '%(c)s', 'user', 'search twice', NULL, '2026-03-01 09:01:00-08:00'),"
            " (6, '%(c)s', 'assistant', 'Searching.', 'gemma4:e4b', '2026-03-01 09:01:01-08:00'),"
            " (7, '%(c)s', 'tool', '', NULL, '2026-03-01 09:01:02-08:00'),"
            " (8, '%(c)s', 'tool', 'second', NULL, '2026-03-01 09:01:03-08:00'),"
            " (9, '%(c)s', 'tool', 'extra', NULL, '2026-03-01 09:01:04-08:00'),"
            " (10, '%(c)s', 'assistant', '', 'gemma4:e4b', '2026-03-01 09:01:05-08:00');"
            "UPDATE messages SET tool_result = '{\"results\":[1]}' WHERE id = 7;"
            "INSERT INTO tool_calls VALUES (2, 6, 'function', 'web_search',"
            ' \'{"query":"ollama","max_results":3}\', NULL),'
            " (3, 6, 'function', 'browser.find', '{\"pattern\":\"x\"}', NULL);" % {"c": c}
        )
        con.commit()
        con.close()
        rows = self.rows_for(OllamaParser(), OLLAMA_DB_REL)
        # message 6 switches back to gemma4; the placeholder 10 yields nothing
        self.assertEqual(
            [r.text for r in rows if model_or_permission_row(r)][2:],
            ["model: qwen3:8b -> gemma4:e4b"],
        )
        rows = [r for r in rows if not model_or_permission_row(r)][4:]
        self.assertEqual(
            [(r.turn_type, r.tool_name, r.tool_use_id, r.text, r.source_line) for r in rows],
            [
                ("user", "", "", "search twice", 5),
                ("assistant", "", "", "Searching.", 6),
                ("tool_use", "web_search", c + ":2", "ollama", 2),
                ("tool_use", "browser.find", c + ":3", '{"pattern":"x"}', 3),
                ("tool_result", "web_search", c + ":2", '{"results":[1]}', 7),
                ("tool_result", "browser.find", c + ":3", "second", 8),
                ("tool_result", "browser.find", "", "extra", 9),
            ],
        )
        self.assertEqual(call_text("not json"), "not json")
        self.assertEqual(call_text('{"url":""}'), '{"url":""}')

    def test_other_files_not_wanted(self):
        p = OllamaParser()
        wanted = {OLLAMA_DB_REL, OLLAMA_WIN_DB_REL, self.HISTORY_REL}
        rels = {a.rel for a in self.col.artifacts if a.agent == "ollama"}
        for rel in (
            OLLAMA_MANIFEST_REL,
            OLLAMA_DB_REL + "-wal",
            OLLAMA_WIN_DB_REL + "-shm",
            ".ollama/config.json",
            ".ollama/backup/config.json.1772355600",
            ".ollama/onboarding-v1.completed",
            ".ollama/id_ed25519",
            ".ollama/logs/server.log",
        ):
            self.assertIn(rel, rels)
        for a in self.col.artifacts:
            if a.agent == "ollama":
                self.assertEqual(p.wants(a), a.rel in wanted, a.rel)
        self.assertEqual(wanted, {a.rel for a in self.col.artifacts if p.wants(a)})

    def test_not_a_database_is_one_system_row(self):
        db = self.home / OLLAMA_DB_REL
        for suffix in ("-wal", "-shm"):
            Path(str(db) + suffix).unlink()
        db.write_text("not a database\n", encoding="utf-8")
        rows = self.rows_for(OllamaParser(), OLLAMA_DB_REL)
        self.assertEqual(
            [(r.turn_type, r.text) for r in rows], [("system", "parser: not a SQLite database")]
        )

    def test_truncated_database_is_reported_not_fatal(self):
        db = self.home / OLLAMA_DB_REL
        for suffix in ("-wal", "-shm"):
            Path(str(db) + suffix).unlink()
        db.write_bytes(db.read_bytes()[:200])
        rows = self.rows_for(OllamaParser(), OLLAMA_DB_REL)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].turn_type, "system")
        self.assertIn("parser: SQLite error", rows[0].text)

    def test_truncated_history_line_still_yields_earlier_lines(self):
        with open(self.home / self.HISTORY_REL, "ab") as fh:
            fh.write(b"half a pro\xe2")
        rows = self.rows_for(OllamaParser(), self.HISTORY_REL)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[-1].text, "half a pro�")


from doubleagent.parsers.claude_desktop import ClaudeDesktopParser
from fixtures import (
    CD_AUDIT_REL,
    CD_CLI_SESSION,
    CD_CODE_CLI,
    CD_CODE_RC_CLI,
    CD_CODE_RC_RECORD_REL,
    CD_CODE_RECORD_REL,
    CD_COWORK_ORG,
    CD_FALLBACK_CLI,
    CD_FALLBACK_DIR,
    CD_FALLBACK_REL,
    CD_RECORD_REL,
    CD_REMOTE_SESSION,
    CD_SCHED_REL,
    CD_SESSION,
    CD_SPACES_REL,
    CD_TRANSCRIPT_REL,
    CD_WORKTREES_REL,
    claude_subagent_records,
)


class ClaudeDesktopTests(ParserBase):
    def test_transcript_rows(self):
        arts = {a.rel: a for a in self.col.artifacts}
        self.assertEqual(arts[CD_TRANSCRIPT_REL].agent, "claude-desktop")
        rows = self.rows_for(ClaudeDesktopParser(), CD_TRANSCRIPT_REL)
        # The claude-code reader's rows, line for line.
        self.assertEqual(
            [(r.source_line, r.turn_type) for r in rows],
            [(n, t) for n, t, _ in ClaudeCodeTests.EXPECTED],
        )
        for r in rows:
            self.assertEqual((r.host, r.user, r.agent), ("h1", "alice", "claude-desktop"))
            self.assertEqual(r.session_id, CD_CLI_SESSION)
            # From the record's userSelectedFolders, not the guest cwd.
            self.assertEqual(r.project_path, "/srv/proj", r)
            self.assertEqual(r.source_file, "/alice/" + CD_TRANSCRIPT_REL)
        self.assertEqual(rows[0].text, "delete the logs in /var/log please")

    def test_transcript_without_record_keeps_jsonl_cwd(self):
        (self.home / CD_RECORD_REL).unlink()
        rows = self.rows_for(ClaudeDesktopParser(), CD_TRANSCRIPT_REL)
        self.assertEqual(rows[0].project_path, "/sessions/quiet-river-1234")

    def test_record_not_read_through_symlink(self):
        record = self.home / CD_RECORD_REL
        target = self.tmp / "outside.json"
        target.write_bytes(record.read_bytes())
        record.unlink()
        try:
            record.symlink_to(target)
        except OSError:
            self.skipTest("symlinks not available")
        rows = self.rows_for(ClaudeDesktopParser(), CD_TRANSCRIPT_REL)
        self.assertEqual(rows[0].project_path, "/sessions/quiet-river-1234")

    def test_subagent_transcript(self):
        rel = CD_TRANSCRIPT_REL[: -len(".jsonl")] + "/subagents/agent-abc.jsonl"
        path = self.home / rel
        path.parent.mkdir(parents=True)
        lines = [json.dumps(r) for r in claude_subagent_records()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.col = open_input(self.tmp / "home", self.cat, host="h1")
        rows = self.rows_for(ClaudeDesktopParser(), rel)
        self.assertEqual(rows[0].text, "subagent abc of %s" % CLAUDE_SESSION)
        self.assertEqual({r.project_path for r in rows}, {"/srv/proj"})
        self.assertEqual({r.agent for r in rows}, {"claude-desktop"})

    def test_audit_with_transcript(self):
        # The transcript holds the turns: only the init model, permission
        # and result rows.
        rows = self.rows_for(ClaudeDesktopParser(), CD_AUDIT_REL)
        self.assertEqual(
            [(r.source_line, r.turn_type, r.tool_name, r.timestamp_utc, r.text) for r in rows],
            [
                (
                    2,
                    "system",
                    "",
                    "2026-10-01T10:00:01.000Z",
                    "model: claude-fable-5-1",
                ),
                (
                    4,
                    "system",
                    "Bash",
                    "2026-10-01T10:00:03.100Z",
                    "permission request: Bash npm test",
                ),
                (
                    5,
                    "system",
                    "Bash",
                    "2026-10-01T10:00:05.000Z",
                    "permission response: Bash once granted=true",
                ),
                (
                    7,
                    "system",
                    "",
                    "2026-10-01T10:00:12.000Z",
                    "result: success turns=2 error=false",
                ),
            ],
        )
        for r in rows:
            self.assertEqual((r.agent, r.session_id), ("claude-desktop", CD_CLI_SESSION))
            self.assertEqual(r.project_path, "/srv/proj")
        self.assertEqual(rows[0].model, "claude-fable-5-1")

    def test_audit_fallback(self):
        rows = self.rows_for(ClaudeDesktopParser(), CD_FALLBACK_REL)
        self.assertEqual(
            [(r.source_line, r.turn_type, r.text) for r in rows],
            [
                (1, "user", "list the files"),
                (2, "system", "model: claude-fable-5-1"),
                (2, "system", "init: cwd=/sessions/quiet-river-1234 model=claude-fable-5-1"),
                (3, "system", "context: notification: folder mounted"),
                (4, "assistant", "Listing."),
                (4, "tool_use", "ls"),
                (5, "system", "permission auto-approved: Bash (always_allow)"),
                (6, "tool_result", "README.md"),
                (7, "assistant", "One file: README.md"),
                (9, "system", "result: success turns=1 error=false"),
                (
                    10,
                    "system",
                    'model_refusal_fallback: {"note":"fields not recorded; fixture only"}',
                ),
                (11, "system", "model: claude-fable-5-1 -> claude-opus-5-5"),
                (11, "assistant", "Answered by the fallback."),
            ],
        )
        change = rows[-2]
        self.assertEqual(
            (change.timestamp_utc, change.model, change.session_id),
            ("2026-10-02T09:00:10.000Z", "claude-opus-5-5", CD_FALLBACK_CLI),
        )
        by = {(r.source_line, r.turn_type): r for r in rows}
        # The prompt's own timestamp wins over the audit write time.
        self.assertEqual(by[1, "user"].timestamp_utc, "2026-10-02T08:59:59.500Z")
        self.assertEqual(by[2, "system"].timestamp_utc, "2026-10-02T09:00:01.000Z")
        use = by[4, "tool_use"]
        self.assertEqual(
            (use.tool_name, use.tool_use_id, use.model), ("Bash", "toolu_b1", "claude-fable-5-1")
        )
        self.assertEqual(by[6, "tool_result"].tool_use_id, "toolu_b1")
        # No session record: the line's session id, no project.
        self.assertEqual({r.session_id for r in rows}, {CD_FALLBACK_CLI})
        self.assertEqual({r.project_path for r in rows}, {""})

    def test_audit_short_dir_joins_record(self):
        # A record under agent/ whose UUID starts with the short dir name.
        rec = (
            self.home
            / CD_COWORK_ORG
            / "agent"
            / ("local_%s-aaaa-4bbb-8ccc-dddddddddddd.json" % CD_FALLBACK_DIR)
        )
        rec.parent.mkdir()
        rec.write_text(
            json.dumps(
                {
                    "sessionId": "local_%s-aaaa-4bbb-8ccc-dddddddddddd" % CD_FALLBACK_DIR,
                    "cliSessionId": "cafecafe-0000-4000-8000-000000000001",
                    "userSelectedFolders": ["/srv/other"],
                    "createdAt": 1790762400000,
                    "lastActivityAt": 1790762400000,
                }
            ),
            encoding="utf-8",
        )
        rows = self.rows_for(ClaudeDesktopParser(), CD_FALLBACK_REL)
        self.assertEqual({r.session_id for r in rows}, {"cafecafe-0000-4000-8000-000000000001"})
        self.assertEqual({r.project_path for r in rows}, {"/srv/other"})

    def test_cowork_record(self):
        rows = self.rows_for(ClaudeDesktopParser(), CD_RECORD_REL)
        # The transcript and audit log exist, so initialMessage is not
        # repeated; the grant rows follow (test_cowork_record_grants).
        self.assertEqual(
            [
                (r.source_line, r.turn_type, r.text)
                for r in rows
                if not r.text.startswith("permission grant:")
            ],
            [
                (
                    1,
                    "system",
                    'desktop session: agent "Summarise the test failures" '
                    "permission_mode=default effort=-",
                )
            ],
        )
        r = rows[0]
        self.assertEqual(
            (r.timestamp_utc, r.session_id, r.project_path, r.git_branch, r.model),
            ("2026-09-30T10:00:00.000Z", CD_CLI_SESSION, "/srv/proj", "", "claude-fable-5-1"),
        )

    def test_cowork_record_grants(self):
        # Issue 97: one row per list entry and object member of the Cowork
        # tool, network and folder grants, at lastActivityAt; an empty list
        # (fileDeleteApprovedMounts) yields nothing.
        rows = self.rows_for(ClaudeDesktopParser(), CD_RECORD_REL)[1:]
        self.assertEqual(
            [r.text for r in rows],
            [
                "permission grant: approvedToolNames Bash (as of lastActivityAt)",
                "permission grant: approvedToolNames WebFetch (as of lastActivityAt)",
                "permission grant: webFetchAllowedUrls https://example.invalid/docs "
                "(as of lastActivityAt)",
                "permission grant: egressAllowedDomains example.invalid (as of lastActivityAt)",
                "permission grant: userApprovedFileAccessPaths /srv/proj/data "
                "(as of lastActivityAt)",
                "permission grant: enabledMcpTools.github:create_issue=true (as of lastActivityAt)",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.turn_type, r.timestamp_utc, r.session_id, r.project_path, r.source_line),
                ("system", "2026-09-30T10:01:00.000Z", CD_CLI_SESSION, "/srv/proj", 1),
            )

    def test_cowork_grant_scalar_value(self):
        path = self.home / CD_RECORD_REL
        rec = json.loads(path.read_text(encoding="utf-8"))
        for key in (
            "approvedToolNames",
            "webFetchAllowedUrls",
            "egressAllowedDomains",
            "userApprovedFileAccessPaths",
            "enabledMcpTools",
        ):
            rec.pop(key)
        rec["fileDeleteApprovedMounts"] = "proj"
        path.write_text(json.dumps(rec), encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_RECORD_REL)
        self.assertEqual(
            [r.text for r in rows[1:]],
            ["permission grant: fileDeleteApprovedMounts=proj (as of lastActivityAt)"],
        )

    def test_record_without_session_and_with_error(self):
        shutil.rmtree(self.home / CD_COWORK_ORG / CD_SESSION)
        path = self.home / CD_RECORD_REL
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec.update(error="VM failed to start", errorCategory="vm", errorAt=1790762430000)
        path.write_text(json.dumps(rec), encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_RECORD_REL)
        self.assertEqual(
            [
                (r.turn_type, r.timestamp_utc, r.text)
                for r in rows
                if not r.text.startswith("permission grant:")
            ],
            [
                (
                    "system",
                    "2026-09-30T10:00:00.000Z",
                    'desktop session: agent "Summarise the test failures" '
                    "permission_mode=default effort=-",
                ),
                ("user", "2026-09-30T10:00:00.000Z", "why does the test fail?"),
                ("system", "2026-09-30T10:00:30.000Z", "session error: vm: VM failed to start"),
            ],
        )

    def test_code_record(self):
        rows = self.rows_for(ClaudeDesktopParser(), CD_CODE_RECORD_REL)
        r = rows[0]
        self.assertEqual(
            (r.turn_type, r.text, r.timestamp_utc, r.session_id, r.project_path, r.git_branch),
            (
                "system",
                'desktop code session: "Fix the failing test" remote_control=false bridges=0 '
                "spawned_remotely=false steered_remotely=false permission_mode=default "
                "effort=high",
                "2026-09-30T10:00:00.000Z",
                CD_CODE_CLI,
                "/srv/proj",
                "main",
            ),
        )

    def test_code_record_grants(self):
        # One row per list entry and per grant key with a value, at
        # lastActivityAt, joined to the session like the record row.
        rows = self.rows_for(ClaudeDesktopParser(), CD_CODE_RECORD_REL)[1:]
        self.assertEqual(
            [r.text for r in rows],
            [
                "permission grant: alwaysAllowedReasons Bash(npm test) (as of lastActivityAt)",
                "permission grant: sessionPermissionUpdates "
                '{"behavior":"allow","destination":"session",'
                '"rules":[{"ruleContent":"npm test","toolName":"Bash"}],"type":"addRules"} '
                "(as of lastActivityAt)",
                "permission grant: chromePermissionMode=ask (as of lastActivityAt)",
                'permission grant: chromeAllowedDomains=["example.invalid"] (as of lastActivityAt)',
                'permission grant: cuAllowedApps=["Terminal"] (as of lastActivityAt)',
                'permission grant: cuGrantFlags={"clipboardRead":true} (as of lastActivityAt)',
                "permission grant: cuFlagsGrantedAt=1790762450000 (as of lastActivityAt)",
            ],
        )
        for r in rows:
            self.assertEqual(
                (r.turn_type, r.timestamp_utc, r.session_id, r.project_path, r.tool_use_id),
                ("system", "2026-09-30T10:02:00.000Z", CD_CODE_CLI, "/srv/proj", ""),
            )

    def test_record_grants_fall_back_to_created_and_skip_empty(self):
        path = self.home / CD_CODE_RECORD_REL
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec.pop("lastActivityAt")
        rec.pop("effort")
        rec.update(alwaysAllowedReasons=[], chromeAllowedDomains=[], cuGrantFlags={})
        rec.update(sessionPermissionUpdates=None, cuAllowedApps="", cuFlagsGrantedAt=None)
        path.write_text(json.dumps(rec), encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_CODE_RECORD_REL)
        self.assertTrue(rows[0].text.endswith("permission_mode=default effort=-"), rows[0].text)
        self.assertEqual(
            [(r.text, r.timestamp_utc) for r in rows[1:]],
            [
                (
                    "permission grant: chromePermissionMode=ask (as of createdAt)",
                    "2026-09-30T10:00:00.000Z",
                )
            ],
        )

    def test_code_record_remote_control(self):
        rows = self.rows_for(ClaudeDesktopParser(), CD_CODE_RC_RECORD_REL)
        self.assertEqual(
            [
                (r.turn_type, r.text, r.timestamp_utc, r.session_id, r.project_path, r.source_line)
                for r in rows
            ],
            [
                (
                    "system",
                    'desktop code session: "Driven from the phone" remote_control=true '
                    "bridges=2 spawned_remotely=true steered_remotely=true "
                    "permission_mode=default effort=-",
                    "2026-09-30T11:00:00.000Z",
                    CD_CODE_RC_CLI,
                    "/srv/proj",
                    1,
                ),
                (
                    "system",
                    "remote control live at update quit",
                    "2026-09-30T11:08:20.000Z",
                    CD_CODE_RC_CLI,
                    "/srv/proj",
                    1,
                ),
            ],
        )

    def test_code_record_remote_control_edge_values(self):
        # An empty spawn object is not a remote spawn; an update-quit object
        # without a numeric `at` yields no second row.
        path = self.home / CD_CODE_RC_RECORD_REL
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec.update(
            remoteControlSpawn={},
            bridgeSessionIds=None,
            remoteControlLiveAtUpdateQuit={"accountId": "x", "at": "soon"},
        )
        path.write_text(json.dumps(rec), encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_CODE_RC_RECORD_REL)
        self.assertEqual(
            [r.text for r in rows],
            [
                'desktop code session: "Driven from the phone" remote_control=true '
                "bridges=0 spawned_remotely=false steered_remotely=true "
                "permission_mode=default effort=-"
            ],
        )

    def test_code_record_joins_home_transcript(self):
        # The Code tab's transcript is claude-code's ~/.claude/projects file:
        # when it is in the input, the first prompt is not repeated.
        path = self.home / CD_CODE_RECORD_REL
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec.update(cliSessionId=CLAUDE_SESSION, initialMessage="fix the test")
        path.write_text(json.dumps(rec), encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_CODE_RECORD_REL)
        self.assertEqual(
            [(r.turn_type, r.session_id) for r in rows if "permission grant" not in r.text],
            [("system", CLAUDE_SESSION)],
        )
        shutil.rmtree(self.home / ".claude/projects")
        rows = self.rows_for(ClaudeDesktopParser(), CD_CODE_RECORD_REL)
        rows = [r for r in rows if "permission grant" not in r.text]
        self.assertEqual([r.turn_type for r in rows], ["system", "user"])
        self.assertEqual(rows[1].text, "fix the test")

    def test_empty_index_files_yield_nothing(self):
        # A fresh install writes the markers before any task or worktree
        # exists (observed on Windows: `{"schemaVersion": 2}`); only a
        # non-object file is reported.
        (self.home / CD_WORKTREES_REL).write_text('{"schemaVersion": 2}', encoding="utf-8")
        (self.home / CD_SCHED_REL).write_text('{"recordedSkips": {}}', encoding="utf-8")
        self.assertEqual(self.rows_for(ClaudeDesktopParser(), CD_WORKTREES_REL), [])
        self.assertEqual(self.rows_for(ClaudeDesktopParser(), CD_SCHED_REL), [])
        (self.home / CD_WORKTREES_REL).write_text("[]", encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_WORKTREES_REL)
        self.assertEqual([r.turn_type for r in rows], ["system"])
        self.assertIn("unreadable", rows[0].text)

    def test_bad_record_is_one_row(self):
        (self.home / CD_RECORD_REL).write_text("[1, 2]", encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_RECORD_REL)
        self.assertEqual([r.turn_type for r in rows], ["system"])
        self.assertIn("not a JSON object", rows[0].text)

    def test_scheduled_tasks_and_worktrees(self):
        rows = self.rows_for(ClaudeDesktopParser(), CD_SCHED_REL)
        self.assertEqual(
            [(r.source_line, r.turn_type, r.timestamp_utc, r.project_path, r.text) for r in rows],
            [
                (
                    1,
                    "system",
                    "2026-09-30T10:00:00.000Z",
                    "/srv/proj",
                    "scheduled task: daily-report 0 9 * * 1-5 enabled=true "
                    "permission_mode=default model=claude-fable-5-1",
                )
            ],
        )
        self.assertEqual(rows[0].model, "claude-fable-5-1")
        rows = self.rows_for(ClaudeDesktopParser(), CD_WORKTREES_REL)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(
            (r.turn_type, r.timestamp_utc, r.project_path, r.git_branch, r.session_id),
            ("system", "2026-09-30T10:00:01.000Z", "/srv/proj", "claude/brave-otter", ""),
        )
        self.assertEqual(
            r.text,
            "worktree created: /srv/proj/.claude/worktrees/brave-otter "
            "branch=claude/brave-otter from=main leased by "
            "local_e2e2e2e2-9999-4aaa-8bbb-cccccccccccc",
        )

    def test_scheduled_task_without_mode_or_model(self):
        doc = json.loads((self.home / CD_SCHED_REL).read_text(encoding="utf-8"))
        del doc["scheduledTasks"][0]["permissionMode"], doc["scheduledTasks"][0]["model"]
        (self.home / CD_SCHED_REL).write_text(json.dumps(doc), encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_SCHED_REL)
        self.assertEqual(
            [(r.text, r.model) for r in rows],
            [
                (
                    "scheduled task: daily-report 0 9 * * 1-5 enabled=true "
                    "permission_mode=- model=-",
                    "",
                )
            ],
        )

    def test_remote_session_spaces(self):
        # Issue 97: one standing row per granted folder, at the file mtime,
        # with the folder as project_path and no session id.
        rows = self.rows_for(ClaudeDesktopParser(), CD_SPACES_REL)
        key = "entries.%s.folders" % CD_REMOTE_SESSION
        self.assertEqual(
            [
                (r.turn_type, r.text, r.timestamp_utc, r.session_id, r.project_path, r.source_line)
                for r in rows
            ],
            [
                (
                    "system",
                    "permission setting: %s=%s (from %s, file mtime)"
                    % (key, folder, CD_SPACES_REL),
                    "2026-10-01T10:00:00.000Z",
                    "",
                    folder,
                    1,
                )
                for folder in ("/srv/proj", "/srv/docs")
            ],
        )

    def test_remote_session_spaces_not_object(self):
        (self.home / CD_SPACES_REL).write_text("[1]", encoding="utf-8")
        rows = self.rows_for(ClaudeDesktopParser(), CD_SPACES_REL)
        self.assertEqual(
            [(r.turn_type, r.source_line, r.text) for r in rows],
            [("system", 1, "parser: remote-session-spaces.json is not a JSON object")],
        )
        (self.home / CD_SPACES_REL).write_text(
            '{"entries": [{"folders": ["/x"]}, 3]}', encoding="utf-8"
        )
        rows = self.rows_for(ClaudeDesktopParser(), CD_SPACES_REL)
        self.assertEqual(
            [r.text for r in rows],
            ["permission setting: entries.folders=/x (from %s, file mtime)" % CD_SPACES_REL],
        )

    def test_thinking_opt_in(self):
        p = ClaudeDesktopParser()
        rows = self.rows_for(p, CD_TRANSCRIPT_REL)
        self.assertFalse(any(r.turn_type == "thinking" for r in rows))
        rows = self.rows_for(p, CD_TRANSCRIPT_REL, include_thinking=True)
        self.assertEqual(
            [(r.source_line, r.text) for r in rows if r.turn_type == "thinking"],
            [(3, "private reasoning")],
        )
        rows = self.rows_for(p, CD_FALLBACK_REL, include_thinking=True)
        self.assertEqual(
            [(r.source_line, r.text) for r in rows if r.turn_type == "thinking"], [(4, "use ls")]
        )

    def test_not_wanted(self):
        p = ClaudeDesktopParser()
        arts = {a.rel: a for a in self.col.artifacts}
        base = "Library/Application Support/Claude/"
        for rel in (
            CD_COWORK_ORG + "/spaces.json",
            CD_COWORK_ORG + "/cowork_settings.json",
            CD_COWORK_ORG + "/rpm/manifest.json",
            CD_COWORK_ORG + "/%s/.audit-key" % CD_SESSION,
            base + "claude_desktop_config.json",
        ):
            self.assertEqual(arts[rel].agent, "claude-desktop", rel)
            self.assertFalse(p.wants(arts[rel]), rel)
        # Each parser reads only its own tree.
        self.assertFalse(ClaudeCodeParser().wants(arts[CD_TRANSCRIPT_REL]))
        self.assertFalse(p.wants(arts[ClaudeCodeTests.REL]))
        self.assertFalse(p.wants(arts[".claude/history.jsonl"]))
        # The other catalog bases, and the staged import tree.
        tail = CD_TRANSCRIPT_REL[len(base) :]
        for root in (
            ".config/Claude-3p/",
            "AppData/Roaming/Claude/",
            "AppData/Local/Claude-3p/",
            "AppData/Local/Claude/",
            "AppData/Local/Claude-Data/",
            "AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/",
            "AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/Claude/",
            "AppData/Local/Packages/AnthropicPBC.Claude_fnn82j28hfe8t/LocalCache/Roaming/Claude/",
        ):
            self.assertTrue(p.wants(rel_only(root + tail)), root)
        self.assertFalse(
            p.wants(rel_only("AppData/Local/Packages/Other_x/LocalCache/Roaming/Claude/" + tail))
        )
        self.assertFalse(p.wants(rel_only("Claude/" + tail)))
        self.assertTrue(
            p.wants(rel_only(base + "claude-code-sessions/a/b/imported-staging/x.jsonl"))
        )

    def test_truncated_line_is_reported_not_fatal(self):
        write_bad_line(self.home / CD_AUDIT_REL)
        rows = self.rows_for(ClaudeDesktopParser(), CD_AUDIT_REL)
        self.assertEqual(len(rows), 5)
        self.assertEqual(
            (rows[-1].turn_type, rows[-1].session_id, rows[-1].source_line),
            ("system", CD_CLI_SESSION, 8),
        )
        self.assertIn("1 unparseable line", rows[-1].text)
        write_bad_line(self.home / CD_TRANSCRIPT_REL)
        rows = self.rows_for(ClaudeDesktopParser(), CD_TRANSCRIPT_REL)
        self.assertEqual(len(rows), len(ClaudeCodeTests.EXPECTED) + 1)
        self.assertIn("1 unparseable line", rows[-1].text)
        self.assertEqual(rows[-1].source_line, 35)
