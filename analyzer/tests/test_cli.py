"""The timeline's stdout summary: the `agents:` line reads naturally when
either of its lists is empty (issue 85)."""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
        groups[""] = inv["outside_projects"]
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
        self.assertEqual(inv["outside_projects"]["rows"], 1)
        self.assertEqual(
            inv["outside_projects"]["agents"]["claude-code"]["turn_types"], {"user": 1}
        )
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
        self.assertEqual(inv["outside_projects"], {"rows": 0, "sessions": 0, "agents": {}})
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
        # A collected project with no rows has zero counts; `status` comes
        # first and the shared files last (issue 104).
        self.assertEqual(
            projects["/srv/empty"],
            {"status": "collected", "rows": 0, "sessions": 0, "agents": {}, "shared_files": 1},
        )
        self.assertEqual(projects["/srv/proj"]["rows"], 1)
        self.assertEqual(projects["/srv/gone"]["rows"], 1)
        self.assertEqual(
            list(projects["/srv/proj"]),
            ["status", "rows", "sessions", "agents", "shared_files"],
        )
        self.assertNotIn("status", inv["outside_projects"])
        self.assertEqual(inv["outside_projects"]["rows"], 1)
        self.assertEqual(inv["rows"], 3)
        # The home's files are under `homes`, never under outside_projects.
        home = inv["homes"][0]
        self.assertEqual((home["user"], home["home"]), ("alice", "/home/alice"))
        self.assertEqual([(a["agent"], a["files"]) for a in home["agents"]], [("claude-code", 1)])
        self.assertNotIn("files", inv["outside_projects"]["agents"]["claude-code"])

    def test_image_root_removed(self):
        # In image mode collection.json names `<root>/srv/proj`, while the
        # host's transcripts say `/srv/proj`: both are one project.
        strip = cli.strip_image_root
        image = {"mode": "image", "root": "/mnt/image/"}
        self.assertEqual(strip("/mnt/image/srv/proj", image), "/srv/proj")
        self.assertEqual(strip("/mnt/imagex/srv/proj", image), "/mnt/imagex/srv/proj")
        self.assertEqual(strip("/srv/proj", image), "/srv/proj")
        self.assertEqual(
            strip("/mnt/image/srv/proj", {"mode": "live", "root": "/mnt/image"}),
            "/mnt/image/srv/proj",
        )
        self.assertEqual(strip("/srv/proj", {"mode": "live", "root": "/"}), "/srv/proj")

    def test_stdout_names_every_file(self):
        out = self.tmp / "out"
        rc, stdout = run_timeline(self.build(), out)
        self.assertEqual(rc, 0, stdout)
        lines = stdout.splitlines()
        self.assertIn("rows:      3 in %s" % (out / "timeline.jsonl"), lines)
        self.assertIn("sessions:  0 in %s" % (out / "sessions.jsonl"), lines)
        self.assertIn(
            "inventory: %s (homes, projects, counts per agent, problems)"
            % (out / "inventory.json"),
            lines,
        )
        heads = [ln.split(":")[0] for ln in lines if not ln.startswith(" ")]
        self.assertEqual(heads[-3:], ["rows", "sessions", "inventory"])
        self.assertNotIn("detect", heads)
        self.assertEqual(
            sorted(p.name for p in out.iterdir()),
            ["inventory.json", "sessions.jsonl", "timeline.jsonl"],
        )


def run_detect(root: Path, *extra: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc = cli.main(["detect", str(root), *extra])
    return rc, buf.getvalue()


AIDER_HISTORY = "# 2026-10-01\n+ hi\n"

# project_agents() for ProjectAgentsTests.build, new or old style.
PROJECT_AGENTS = {
    "/srv/proj": {
        "users": ["alice"],
        "agents": {
            "aider": {"files": 1, "bytes": len(AIDER_HISTORY)},
            "claude-code": {"files": 1, "bytes": 2},
        },
        "shared_files": 1,
        "shared_bytes": 4,
    },
    "/srv/shared": {"users": ["alice"], "agents": {}, "shared_files": 1, "shared_bytes": 9},
}


class ProjectAgentsTests(unittest.TestCase):
    """The agents used on each home and collected project, in `detect`,
    `detect --json` and inventory.json; `project` is never shown as an
    agent (issue 104)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-projagents-test-"))
        self.cat = catalog.parse(SYNTHETIC_CATALOG)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, new: bool, name: str = "col") -> Path:
        # new: collector 1.12.0, collection.json `projects` and agent-named
        # rows; old: no `projects` key and every project row `project`.
        c = Collected(self.tmp / name, ["/srv/proj", "/srv/shared"] if new else None)
        c.add("alice", "/home/alice", "claude-code", ".claude/settings.json", "{}")
        files = [
            ("/srv/proj", "claude-code", ".claude/settings.local.json", "{}"),
            ("/srv/proj", "aider", ".aider.input.history", AIDER_HISTORY),
            ("/srv/proj", "project", "AGENTS.md", "# x\n"),
            ("/srv/shared", "project", "AGENTS.md", "# shared\n"),
        ]
        for home, agent, rel, text in files:
            c.add("alice", home, agent if new else "project", rel, text)
        return c.write()

    def agents_of(self, root: Path) -> dict[str, dict]:
        col = open_input(root, self.cat)
        try:
            return cli.project_agents(col)
        finally:
            col.cleanup()

    def test_project_agents(self):
        self.assertEqual(self.agents_of(self.build(True)), PROJECT_AGENTS)

    def test_old_collection_agrees(self):
        self.assertEqual(self.agents_of(self.build(False, "old")), PROJECT_AGENTS)

    def test_detect_json(self):
        rc, out = run_detect(self.build(True), "--json")
        self.assertEqual(rc, 0, out)
        doc = json.loads(out)
        self.assertEqual(
            list(doc),
            [
                "input",
                "kind",
                "host",
                "notes",
                "homes",
                "projects",
                "problems",
            ],
        )
        self.assertEqual(
            doc["homes"],
            [
                {
                    "user": "alice",
                    "home": "/home/alice",
                    "inferred": False,
                    "agents": [{"agent": "claude-code", "files": 1, "bytes": 2, "parser": True}],
                }
            ],
        )
        self.assertEqual(
            doc["projects"],
            [
                {
                    "path": "/srv/proj",
                    "users": ["alice"],
                    "agents": [
                        {"agent": "aider", "files": 1, "bytes": 18, "parser": True},
                        {"agent": "claude-code", "files": 1, "bytes": 2, "parser": True},
                    ],
                    "shared_files": 1,
                    "shared_bytes": 4,
                },
                {
                    "path": "/srv/shared",
                    "users": ["alice"],
                    "agents": [],
                    "shared_files": 1,
                    "shared_bytes": 9,
                },
            ],
        )
        # --files still names every file with its attributed agent.
        rc, out = run_detect(self.build(True, "col2"), "--json", "--files")
        doc = json.loads(out)
        self.assertEqual(list(doc)[-1], "files")
        self.assertIn(
            {"user": "alice", "agent": "project", "path": "/srv/shared/AGENTS.md"}, doc["files"]
        )

    def test_detect_text(self):
        root = self.build(True)
        rc, out = run_detect(root)
        self.assertEqual(rc, 0, out)
        lines = out.splitlines()
        # The header lines and the first table, as before 0.12.0 (issue 104).
        homes_fmt = "%-14s %-32s %-18s %8s %12s  %s"
        self.assertEqual(
            lines[:7],
            [
                "input:   %s" % root,
                "kind:    collected",
                "host:    h1",
                "",
                homes_fmt % ("user", "home", "agent", "files", "bytes", "parser"),
                homes_fmt % ("alice", "/home/alice", "claude-code", 1, 2, "yes"),
                "",
            ],
        )
        fmt = "%-40s %-14s %-18s %8s %12s  %s"
        head = fmt % ("project", "users", "agent", "files", "bytes", "parser")
        self.assertIn(head, lines)
        at = lines.index(head)
        self.assertEqual(lines[at - 1], "")
        self.assertEqual(
            lines[at + 1 : at + 5],
            [
                fmt % ("/srv/proj", "alice", "aider", 1, 18, "yes"),
                fmt % ("", "", "claude-code", 1, 2, "yes"),
                (fmt % ("", "", "(shared)", 1, 4, "")).rstrip(),
                (fmt % ("/srv/shared", "alice", "(shared)", 1, 9, "")).rstrip(),
            ],
        )
        self.assertEqual(len(lines), at + 5)
        # The first table holds the user home only; `project` is no agent.
        self.assertNotIn("/srv/", "\n".join(lines[:at]))
        self.assertNotIn(" project ", out)

    def test_detect_text_first_table(self):
        # The first table keeps its 0.11.0 layout: one line per user, home
        # and agent in the order the first file was met, which is not the
        # sorted order of homes[].agents (issue 104).
        c = Collected(self.tmp / "col", ["/srv/proj"])
        c.add("alice", "/home/alice", "codex-cli", ".codex/config.toml", "x=1\n")
        c.add("bob", "/home/bob", "claude-code", ".claude/settings.json", "{}")
        c.add("alice", "/srv/proj", "project", "AGENTS.md", "# x\n")
        c.add("alice", "/home/alice", "aider", ".aider.conf.yml", "x\n")
        root = c.write()
        rc, out = run_detect(root)
        self.assertEqual(rc, 0, out)
        fmt = "%-14s %-32s %-18s %8s %12s  %s"
        lines = out.splitlines()
        at = lines.index(fmt % ("user", "home", "agent", "files", "bytes", "parser"))
        self.assertEqual(lines[at - 1], "")
        self.assertEqual(
            lines[at + 1 : at + 5],
            [
                fmt % ("alice", "/home/alice", "codex-cli", 1, 4, "yes"),
                fmt % ("bob", "/home/bob", "claude-code", 1, 2, "yes"),
                fmt % ("alice", "/home/alice", "aider", 1, 2, "yes"),
                "",
            ],
        )
        rc, js = run_detect(root, "--json")
        homes = json.loads(js)["homes"]
        self.assertEqual([h["user"] for h in homes], ["alice", "bob"])
        self.assertEqual([a["agent"] for a in homes[0]["agents"]], ["aider", "codex-cli"])

    def test_detect_text_without_projects(self):
        c = Collected(self.tmp / "col", [])
        c.add("alice", "/home/alice", "claude-code", ".claude/settings.json", "{}")
        rc, out = run_detect(c.write())
        self.assertEqual(rc, 0, out)
        self.assertNotIn("project", out)

    def test_detect_json_matches_inventory(self):
        root = self.build(True)
        # A file missing from fs/ is a problem met while opening the input;
        # an aider history the parser cannot read is a parser problem.
        manifest = root / "manifest.jsonl"
        gone = {
            "user": "alice",
            "home": "/home/alice",
            "agent": "claude-code",
            "path": "/home/alice/.claude/gone.json",
            "archive_path": "fs/home/alice/.claude/gone.json",
            "type": "file",
            "status": "collected",
            "size": 1,
        }
        with open(manifest, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(gone) + "\n")
        rc, out = run_detect(root, "--json")
        self.assertEqual(rc, 0, out)
        doc = json.loads(out)
        aider = by_agent()["aider"][0]
        denied = PermissionError(13, "Permission denied")
        with mock.patch.object(aider, "parse", side_effect=denied):
            rc, stdout = run_timeline(root, self.tmp / "out")
        self.assertEqual(rc, 1, stdout)  # no rows; inventory.json is written anyway
        inv = json.loads((self.tmp / "out" / "inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(
            list(inv),
            [
                "input",
                "kind",
                "host",
                "notes",
                "problems",
                "rows",
                "sessions",
                "parsed",
                "detected_not_parsed",
                "no_rows",
                "homes",
                "projects",
                "outside_projects",
            ],
        )
        for key in ("input", "kind", "host", "notes", "homes"):
            self.assertEqual(inv[key], doc[key], key)
        self.assertEqual(inv["kind"], "collected")
        self.assertEqual(
            doc["problems"], ["/home/alice/.claude/gone.json: missing from the collection"]
        )
        self.assertEqual(
            inv["problems"],
            doc["problems"] + ["/srv/proj/.aider.input.history: permission denied"],
        )
        self.assertFalse((self.tmp / "out" / "detect.json").exists())

    def timeline_inventory(self, root: Path, want_rc: int = 0) -> dict:
        out = self.tmp / "out"
        rc, stdout = run_timeline(root, out)
        self.assertEqual(rc, want_rc, stdout)
        return json.loads((out / "inventory.json").read_text(encoding="utf-8"))

    def test_inventory(self):
        c = Collected(self.tmp / "col", ["/srv/proj", "/srv/shared"])
        history = [
            {"display": "in proj", "timestamp": 1790848800000, "project": "/srv/proj"},
            {"display": "gone", "timestamp": 1790848860000, "project": "/srv/gone"},
        ]
        c.add(
            "alice",
            "/home/alice",
            "claude-code",
            ".claude/history.jsonl",
            "".join(json.dumps(x) + "\n" for x in history),
        )
        c.add("alice", "/srv/proj", "cursor", ".cursor/rules/x.mdc", "x\n")
        c.add("alice", "/srv/proj", "project", "AGENTS.md", "# x\n")
        c.add("alice", "/srv/shared", "project", "AGENTS.md", "# y\n")
        inv = self.timeline_inventory(c.write())
        self.assertEqual(
            list(inv),
            [
                "input",
                "kind",
                "host",
                "notes",
                "problems",
                "rows",
                "sessions",
                "parsed",
                "detected_not_parsed",
                "no_rows",
                "homes",
                "projects",
                "outside_projects",
            ],
        )
        self.assertEqual(inv["problems"], [])
        projects = inv["projects"]
        for path, entry in projects.items():
            self.assertEqual(
                list(entry), ["status", "rows", "sessions", "agents", "shared_files"], path
            )
        proj = projects["/srv/proj"]
        # Rows and no files; files and no rows.
        self.assertEqual(
            proj["agents"]["claude-code"],
            {"rows": 1, "sessions": 0, "turn_types": {"user": 1}, "files": 0, "bytes": 0},
        )
        self.assertEqual(
            proj["agents"]["cursor"],
            {"rows": 0, "sessions": 0, "turn_types": {}, "files": 1, "bytes": 2},
        )
        self.assertEqual(proj["shared_files"], 1)
        self.assertEqual(
            projects["/srv/gone"],
            {
                "status": "referenced",
                "rows": 1,
                "sessions": 0,
                "agents": {
                    "claude-code": {
                        "rows": 1,
                        "sessions": 0,
                        "turn_types": {"user": 1},
                        "files": 0,
                        "bytes": 0,
                    }
                },
                "shared_files": 0,
            },
        )
        self.assertEqual(
            projects["/srv/shared"],
            {"status": "collected", "rows": 0, "sessions": 0, "agents": {}, "shared_files": 1},
        )
        self.assertEqual(inv["outside_projects"], {"rows": 0, "sessions": 0, "agents": {}})
        # cursor is in no home, only in a project: still detected.
        self.assertEqual(inv["detected_not_parsed"], ["cursor"])

    def test_outside_projects_has_no_file_counts(self):
        c = Collected(self.tmp / "col", [])
        history = [{"display": "nowhere", "timestamp": 1790848920000}]
        c.add(
            "alice",
            "/home/alice",
            "claude-code",
            ".claude/history.jsonl",
            "".join(json.dumps(x) + "\n" for x in history),
        )
        inv = self.timeline_inventory(c.write())
        self.assertEqual(inv["projects"], {})
        self.assertEqual(
            inv["outside_projects"]["agents"]["claude-code"],
            {"rows": 1, "sessions": 0, "turn_types": {"user": 1}},
        )

    def test_inventory_image_root(self):
        c = Collected(self.tmp / "col", ["/mnt/image/srv/proj"])
        summary = {
            "hostname": "h1",
            "mode": "image",
            "root": "/mnt/image",
            "projects": ["/mnt/image/srv/proj"],
        }
        (c.root / "collection.json").write_text(json.dumps(summary), encoding="utf-8")
        c.add("alice", "/mnt/image/srv/proj", "cursor", ".cursor/rules/x.mdc", "x\n")
        inv = self.timeline_inventory(c.write(), want_rc=1)  # no rows
        self.assertEqual(list(inv["projects"]), ["/srv/proj"])
        self.assertEqual(
            inv["projects"]["/srv/proj"]["agents"]["cursor"],
            {"rows": 0, "sessions": 0, "turn_types": {}, "files": 1, "bytes": 2},
        )

    def test_loose_has_none(self):
        home = self.tmp / "home" / "alice"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude/settings.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.agents_of(self.tmp / "home"), {})
        rc, out = run_detect(self.tmp / "home", "--json")
        self.assertEqual(rc, 0, out)
        self.assertEqual(json.loads(out)["projects"], [])


if __name__ == "__main__":
    unittest.main()
