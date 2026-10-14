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
        self.assertEqual(
            cli.agents_summary(["claude-code", "antigravity"], ["copilot-cli", "copilot-cli"]),
            "parsed: antigravity, claude-code; detected but not parsed: copilot-cli",
        )
        self.assertEqual(
            cli.agents_summary(["claude-code"], []),
            "parsed: claude-code; detected but not parsed: none",
        )
        self.assertEqual(
            cli.agents_summary([], ["cursor"]),
            "parsed: none; detected but not parsed: cursor",
        )

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

    def test_no_agent_data(self):
        self.assertEqual(cli.agents_summary([], []), "none were found")
        self.write("Documents/notes.txt", "not an agent file\n")
        rc, out = run_timeline(self.tmp / "home", self.tmp / "out")
        self.assertEqual(rc, 1, out)  # no rows
        self.assertEqual(agents_line(out), "agents:    none were found")


if __name__ == "__main__":
    unittest.main()
