"""The timeline's stdout summary: the `agents:` line reads naturally when
either of its lists is empty (issue 85)."""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from doubleagent import catalog, cli
from doubleagent.inputs import open_input
from doubleagent.parsers import ALL, Options, by_agent
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


# A synthetic catalog for the project tests, so they do not depend on which
# agent the bundled project catalog gives a file: `.pi/approved-plan.md`
# nests inside `.pi`, and `AGENTS.md` is left to `project`.
SYNTHETIC_CATALOG = """# home artifacts (relative to each home)
claude-code|.claude
pi|.pi

# project artifacts (relative to each discovered project)
claude-code|.claude
project|AGENTS.md
pi|.pi
pi-plans|.pi/approved-plan.md
aider|.aider.*
"""

CLAUDE_LOCAL_SETTINGS = {"permissions": {"allow": ["Bash(make lint)"]}}


class Collected:
    """An extracted collection written row by row: each file goes under
    fs/ and gets a collected manifest row."""

    def __init__(self, root: Path, projects: list[str] | None):
        self.root = root
        (root / "fs").mkdir(parents=True)
        summary: dict = {"hostname": "h1"}
        if projects is not None:
            summary["projects"] = projects
        (root / "collection.json").write_text(json.dumps(summary), encoding="utf-8")
        self.rows: list[dict] = []

    def add(self, user: str, home: str, agent: str, rel: str, text: str) -> None:
        path = home.rstrip("/") + "/" + rel
        disk = self.root / ("fs" + path)
        disk.parent.mkdir(parents=True, exist_ok=True)
        disk.write_text(text, encoding="utf-8")
        self.rows.append(
            {
                "user": user,
                "home": home,
                "agent": agent,
                "path": path,
                "archive_path": "fs" + path,
                "type": "file",
                "status": "collected",
                "size": len(text.encode("utf-8")),
            }
        )

    def write(self) -> Path:
        with open(self.root / "manifest.jsonl", "w", encoding="utf-8") as fh:
            for r in self.rows:
                fh.write(json.dumps(r) + "\n")
        return self.root


class ProjectAttributionTests(unittest.TestCase):
    """Project bases and the agent of their files (issue 104)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-proj-test-"))
        self.cat = catalog.parse(SYNTHETIC_CATALOG)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_project_agent_for(self):
        pa = self.cat.project_agent_for
        self.assertEqual(pa(".claude/settings.local.json"), "claude-code")
        self.assertEqual(pa("AGENTS.md"), "project")
        self.assertEqual(pa(".pi/settings.json"), "pi")
        self.assertEqual(pa(".pi/approved-plan.md"), "pi-plans")  # the nested entry wins
        self.assertEqual(pa(".aider.chat.history.md"), "aider")
        self.assertEqual(pa("README.md"), "")
        self.assertEqual(pa(".claude\\settings.json"), "claude-code")

    def test_marker_from_collection_json(self):
        c = Collected(self.tmp / "col", ["/srv/proj"])
        c.add("alice", "/home/alice", "claude-code", ".claude/history.jsonl", "")
        c.add("alice", "/srv/proj", "claude-code", ".claude/settings.local.json", "{}")
        c.add("alice", "/srv/proj", "project", "AGENTS.md", "# x\n")
        col = open_input(c.write(), self.cat)
        try:
            marks = {h.original: h.project for h in col.homes}
            agents = {a.original: a.agent for a in col.artifacts}
        finally:
            col.cleanup()
        self.assertEqual(marks, {"/home/alice": False, "/srv/proj": True})
        self.assertEqual(agents["/srv/proj/.claude/settings.local.json"], "claude-code")
        self.assertEqual(agents["/srv/proj/AGENTS.md"], "project")

    def test_old_collection_reattributed(self):
        # A collector before 1.12.0: every project row says `project`, and
        # collection.json has no `projects` key.
        c = Collected(self.tmp / "col", None)
        c.add("alice", "/home/alice", "pi", ".pi/agent/settings.json", "{}")
        for rel in (
            ".claude/settings.local.json",
            "AGENTS.md",
            ".pi/approved-plan.md",
            ".pi/notes.txt",
            ".aider.input.history",
            "unknown.txt",
        ):
            c.add("alice", "/srv/proj", "project", rel, "{}")
        col = open_input(c.write(), self.cat)
        try:
            marks = {h.original: h.project for h in col.homes}
            agents = {a.rel: a.agent for a in col.artifacts if a.home.original == "/srv/proj"}
            table = {(r["home"], r["agent"]): r["files"] for r in cli.detect_table(col)}
        finally:
            col.cleanup()
        self.assertEqual(marks, {"/home/alice": False, "/srv/proj": True})
        self.assertEqual(
            agents,
            {
                ".claude/settings.local.json": "claude-code",
                "AGENTS.md": "project",
                ".pi/approved-plan.md": "pi-plans",
                ".pi/notes.txt": "pi",
                ".aider.input.history": "aider",
                "unknown.txt": "project",
            },
        )
        self.assertEqual(
            table,
            {
                ("/home/alice", "pi"): 1,
                ("/srv/proj", "claude-code"): 1,
                ("/srv/proj", "project"): 2,
                ("/srv/proj", "pi-plans"): 1,
                ("/srv/proj", "pi"): 1,
                ("/srv/proj", "aider"): 1,
            },
        )

    def test_routing(self):
        c = Collected(self.tmp / "col", ["/srv/proj"])
        c.add(
            "alice",
            "/srv/proj",
            "claude-code",
            ".claude/settings.local.json",
            json.dumps(CLAUDE_LOCAL_SETTINGS),
        )
        c.add("alice", "/srv/proj", "project", "AGENTS.md", "# x\n")
        col = open_input(c.write(), self.cat)
        try:
            parsers = by_agent()
            routed = {a.rel: cli.parsers_for(a, parsers) for a in col.artifacts}
            rows, _, problems = cli.collect_rows(col, Options(), [])
        finally:
            col.cleanup()
        self.assertIs(routed["AGENTS.md"], ALL)
        self.assertEqual({p.agent for p in routed[".claude/settings.local.json"]}, {"claude-code"})
        self.assertEqual(problems, [])
        # The project-scoped settings row names the project, as it did when
        # the manifest said `project`.
        self.assertEqual(
            [(r.agent, r.project_path, r.turn_type) for r in rows],
            [("claude-code", "/srv/proj", "system")],
        )


class TimelineProjectStatusTests(unittest.TestCase):
    """`status` of each inventory.json project, and the stdout file lines."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-status-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self) -> Path:
        c = Collected(self.tmp / "col", ["/srv/proj", "/srv/empty"])
        history = [
            {"display": "in proj", "timestamp": 1790848800000, "project": "/srv/proj"},
            {"display": "gone", "timestamp": 1790848860000, "project": "/srv/gone"},
            {"display": "nowhere", "timestamp": 1790848920000},
        ]
        c.add(
            "alice",
            "/home/alice",
            "claude-code",
            ".claude/history.jsonl",
            "".join(json.dumps(x) + "\n" for x in history),
        )
        c.add("alice", "/srv/proj", "project", "AGENTS.md", "# x\n")
        c.add("alice", "/srv/empty", "project", "AGENTS.md", "# y\n")
        return c.write()

    def test_status_values(self):
        out = self.tmp / "out"
        rc, stdout = run_timeline(self.build(), out)
        self.assertEqual(rc, 0, stdout)
        inv = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
        projects = inv["projects"]
        self.assertEqual(list(projects), ["/srv/empty", "/srv/gone", "/srv/proj"])
        self.assertEqual(
            {k: v["status"] for k, v in projects.items()},
            {"/srv/empty": "collected", "/srv/gone": "referenced", "/srv/proj": "collected"},
        )
        # A collected project with no rows has zero counts; `status` is last.
        self.assertEqual(
            projects["/srv/empty"],
            {"rows": 0, "sessions": 0, "agents": {}, "status": "collected"},
        )
        self.assertEqual(projects["/srv/proj"]["rows"], 1)
        self.assertEqual(projects["/srv/gone"]["rows"], 1)
        self.assertEqual(list(projects["/srv/proj"]), ["rows", "sessions", "agents", "status"])
        self.assertNotIn("status", inv["no_project"])
        self.assertEqual(inv["no_project"]["rows"], 1)
        self.assertEqual(inv["rows"], 3)

    def test_stdout_names_every_file(self):
        out = self.tmp / "out"
        rc, stdout = run_timeline(self.build(), out)
        self.assertEqual(rc, 0, stdout)
        lines = stdout.splitlines()
        self.assertIn("rows:      3 in %s" % (out / "timeline.jsonl"), lines)
        self.assertIn("sessions:  0 in %s" % (out / "sessions.jsonl"), lines)
        self.assertIn(
            "detect:    %s (agents and files detected, problems)" % (out / "detect.json"), lines
        )
        self.assertIn(
            "inventory: %s (counts per project and agent)" % (out / "inventory.json"), lines
        )
        heads = [ln.split(":")[0] for ln in lines if not ln.startswith(" ")]
        self.assertEqual(heads[-4:], ["rows", "sessions", "detect", "inventory"])
        for name in ("timeline.jsonl", "sessions.jsonl", "detect.json", "inventory.json"):
            self.assertTrue((out / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
