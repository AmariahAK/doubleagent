"""The timeline's stdout summary: the `agents:` line reads naturally when
either of its lists is empty (issue 85)."""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from doubleagent import cli
from fixtures import build_home


def run_timeline(root: Path, out: Path) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc = cli.main(["timeline", str(root), "-o", str(out), "--host", "h1"])
    return rc, buf.getvalue()


def agents_line(stdout: str) -> str:
    lines = [line for line in stdout.splitlines() if line.startswith("agents:")]
    assert len(lines) == 1, stdout
    return lines[0]


class AgentsSummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-cli-test-"))
        self.home = self.tmp / "home" / "alice"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, text: str) -> None:
        p = self.home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def claude_history(self) -> None:
        self.write(
            ".claude/history.jsonl",
            json.dumps({"display": "hello", "timestamp": 1790848800000, "project": "/srv/proj"})
            + "\n",
        )

    def copilot_state(self) -> None:
        self.write(".copilot/config.json", "{}")

    def test_text(self):
        summary = cli.agents_summary
        self.assertEqual(
            summary(True, ["claude-code", "antigravity"], ["copilot-cli", "copilot-cli"], []),
            "parsed: antigravity, claude-code; detected but not parsed: copilot-cli",
        )
        self.assertEqual(
            summary(True, ["claude-code"], [], []),
            "parsed: claude-code; detected but not parsed: none",
        )
        self.assertEqual(
            summary(True, [], ["cursor"], []),
            "parsed: none; detected but not parsed: cursor",
        )
        self.assertEqual(
            summary(True, [], [], ["antigravity"]),
            "parsed: none; detected but not parsed: none; parser found no rows: antigravity",
        )
        self.assertEqual(summary(False, [], [], []), "none were found")

    def test_both_lists(self):
        self.claude_history()
        self.copilot_state()
        rc, out = run_timeline(self.tmp / "home", self.tmp / "out")
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            agents_line(out),
            "agents:    parsed: claude-code; detected but not parsed: copilot-cli",
        )

    def test_nothing_unparsed(self):
        self.claude_history()
        rc, out = run_timeline(self.tmp / "home", self.tmp / "out")
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            agents_line(out),
            "agents:    parsed: claude-code; detected but not parsed: none",
        )
        self.assertNotIn("only none", out)

    def test_nothing_parsed(self):
        self.copilot_state()
        rc, out = run_timeline(self.tmp / "home", self.tmp / "out")
        self.assertEqual(rc, 1, out)  # no rows
        self.assertEqual(
            agents_line(out),
            "agents:    parsed: none; detected but not parsed: copilot-cli",
        )

    def test_parser_found_no_rows(self):
        # The agent is detected and has a parser, but its files hold nothing:
        # an empty summaries database and an empty conversations directory.
        self.write(".gemini/antigravity-cli/conversation_summaries.db", "")
        (self.home / ".gemini/antigravity-cli/conversations").mkdir()
        self.copilot_state()
        rc, out = run_timeline(self.tmp / "home", self.tmp / "out")
        self.assertEqual(rc, 1, out)  # no rows
        self.assertEqual(
            agents_line(out),
            "agents:    parsed: none; detected but not parsed: copilot-cli;"
            " parser found no rows: antigravity",
        )
        self.assertNotIn("none were found", out)

    def test_agent_left_out_by_filter_is_not_no_rows(self):
        self.claude_history()
        self.write(".gemini/antigravity-cli/conversation_summaries.db", "")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            rc = cli.main(
                [
                    "timeline",
                    str(self.tmp / "home"),
                    "-o",
                    str(self.tmp / "out"),
                    "--agent",
                    "claude-code",
                ]
            )
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertEqual(
            agents_line(buf.getvalue()),
            "agents:    parsed: claude-code; detected but not parsed: none",
        )

    def test_no_agent_data(self):
        self.write("Documents/notes.txt", "not an agent file\n")
        rc, out = run_timeline(self.tmp / "home", self.tmp / "out")
        self.assertEqual(rc, 1, out)  # no rows
        self.assertEqual(agents_line(out), "agents:    none were found")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class InventoryJsonTests(unittest.TestCase):
    """inventory.json: counts per project and outside any project, and the
    agent lists, written by `timeline` (issue 103)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-inv-json-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def timeline(self, root: Path, *extra: str) -> tuple[int, str, Path]:
        out = self.tmp / "out"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            rc = cli.main(["timeline", str(root), "-o", str(out), "--host", "h1", *extra])
        return rc, buf.getvalue(), out

    def check_totals(self, out: Path) -> dict:
        inv = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
        rows = read_jsonl(out / "timeline.jsonl")
        sessions = read_jsonl(out / "sessions.jsonl")
        self.assertEqual(inv["rows"], len(rows))
        self.assertEqual(inv["sessions"], len(sessions))
        groups = dict(inv["projects"])
        self.assertNotIn("", groups)
        groups[""] = inv["no_project"]
        # Every row and session lands in exactly one group, and each
        # group's totals are the sum of its agents'.
        self.assertEqual(sum(g["rows"] for g in groups.values()), len(rows))
        self.assertEqual(sum(g["sessions"] for g in groups.values()), len(sessions))
        for path, g in groups.items():
            self.assertEqual(sum(a["rows"] for a in g["agents"].values()), g["rows"], path)
            self.assertEqual(sum(a["sessions"] for a in g["agents"].values()), g["sessions"])
            for agent, a in g["agents"].items():
                want = [r for r in rows if r["project_path"] == path and r["agent"] == agent]
                self.assertEqual(sum(a["turn_types"].values()), len(want), (path, agent))
                for tt, n in a["turn_types"].items():
                    self.assertEqual(n, sum(1 for r in want if r["turn_type"] == tt))
        return inv

    def test_full_fixture(self):
        home = self.tmp / "home" / "alice"
        build_home(home)
        (home / ".copilot").mkdir(exist_ok=True)
        (home / ".copilot/config.json").write_text("{}", encoding="utf-8")
        rc, out, path = self.timeline(self.tmp / "home")
        self.assertEqual(rc, 0, out)
        inv = self.check_totals(path)
        self.assertIn("/srv/proj", inv["projects"])
        self.assertIn("claude-code", inv["projects"]["/srv/proj"]["agents"])
        self.assertIn("claude-code", inv["parsed"])
        self.assertIn("copilot-cli", inv["detected_not_parsed"])
        self.assertEqual(inv["detected_not_parsed"], sorted(inv["detected_not_parsed"]))
        self.assertEqual(list(inv["projects"]), sorted(inv["projects"]))

    def test_with_and_without_project(self):
        home = self.tmp / "home" / "alice"
        (home / ".claude").mkdir(parents=True)
        lines = [
            {"display": "in a project", "timestamp": 1790848800000, "project": "/srv/proj"},
            {"display": "no project", "timestamp": 1790848860000},
        ]
        (home / ".claude/history.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8"
        )
        rc, out, path = self.timeline(self.tmp / "home")
        self.assertEqual(rc, 0, out)
        inv = self.check_totals(path)
        self.assertEqual(list(inv["projects"]), ["/srv/proj"])
        self.assertEqual(inv["projects"]["/srv/proj"]["rows"], 1)
        self.assertEqual(inv["no_project"]["rows"], 1)
        self.assertEqual(inv["no_project"]["agents"]["claude-code"]["turn_types"], {"user": 1})
        self.assertEqual(inv["detected_not_parsed"], [])
        self.assertEqual(inv["no_rows"], [])

    def test_filtered(self):
        home = self.tmp / "home" / "alice"
        build_home(home)
        rc, out, path = self.timeline(self.tmp / "home", "--match", "zzz-no-such-text")
        self.assertEqual(rc, 1, out)  # no rows
        inv = self.check_totals(path)
        self.assertEqual(inv["rows"], 0)
        self.assertEqual(inv["projects"], {})
        self.assertEqual(inv["no_project"], {"rows": 0, "sessions": 0, "agents": {}})
        # `parsed` names the agents with rows before filtering, as stdout does.
        self.assertIn("claude-code", inv["parsed"])


if __name__ == "__main__":
    unittest.main()
