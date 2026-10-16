import subprocess
import unittest
from pathlib import Path

from doubleagent import catalog
from doubleagent.parsers import NO_TRANSCRIPTS, by_agent

REPO = Path(__file__).resolve().parents[2]
COLLECTOR = REPO / "collectors" / "collect-agent-artifacts.sh"


class GlobTests(unittest.TestCase):
    def rx(self, pat):
        return catalog.glob_segment_to_regex(pat)

    def test_star_does_not_cross_slash(self):
        self.assertIsNotNone(self.rx("*.jsonl").fullmatch("a.jsonl"))
        self.assertIsNone(self.rx("*").fullmatch("a/b"))

    def test_question_and_class(self):
        self.assertIsNotNone(self.rx("rollout-?.jsonl").fullmatch("rollout-1.jsonl"))
        self.assertIsNotNone(self.rx("[Zz]ed").fullmatch("Zed"))
        self.assertIsNotNone(self.rx("[Zz]ed").fullmatch("zed"))
        self.assertIsNone(self.rx("[Zz]ed").fullmatch("Xed"))
        self.assertIsNotNone(self.rx("[!a]bc").fullmatch("xbc"))
        self.assertIsNone(self.rx("[!a]bc").fullmatch("abc"))

    def test_literal_dots_and_spaces(self):
        self.assertIsNotNone(self.rx("Application Support").fullmatch("Application Support"))
        self.assertIsNone(self.rx(".claude.json*").fullmatch("xclaudejson"))
        self.assertIsNotNone(self.rx(".claude.json*").fullmatch(".claude.json.backup"))


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.cat = catalog.load()

    def test_sections_parsed(self):
        self.assertGreater(len(self.cat.entries), 100)
        self.assertGreater(len(self.cat.project_entries), 30)
        self.assertGreater(len(self.cat.excludes), 50)
        self.assertGreater(len(self.cat.secrets), 50)
        self.assertIn("claude-code", self.cat.agents)
        self.assertIn("codex-cli", self.cat.agents)
        # Each project entry names a catalog agent, or `project` for a file
        # several agents read (AGENTS.md).
        agents = set(self.cat.agents) | {"project"}
        self.assertTrue(all(e.agent in agents for e in self.cat.project_entries))

    def test_every_entry_has_agent_and_glob(self):
        for e in self.cat.entries:
            self.assertTrue(e.agent and e.glob and e.segments, e)

    @unittest.skipUnless(COLLECTOR.exists(), "collector script not present")
    def test_bundled_copy_matches_collector_list(self):
        out = subprocess.run(
            ["sh", str(COLLECTOR), "--list"], capture_output=True, text=True, check=True
        ).stdout
        self.assertEqual(
            out,
            self.cat.text,
            "catalog.txt drifted; run: collectors/collect-agent-artifacts.sh --list > analyzer/doubleagent/catalog.txt",
        )


if __name__ == "__main__":
    unittest.main()


class NoTranscriptsTests(unittest.TestCase):
    """The `collected` rows of the agents table in docs/parsers.md and the
    NO_TRANSCRIPTS set the analyzer reports as collected only must agree."""

    def collected_rows(self) -> set[str]:
        text = (REPO / "analyzer" / "docs" / "parsers.md").read_text(encoding="utf-8")
        table = text.split("\n## Agents\n", 1)[1].split("\n## ", 1)[0]
        out = set()
        for line in table.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("| `") and len(cells) > 1 and cells[1] == "collected":
                out.add(cells[0].strip("`"))
        return out

    def test_table_matches_set(self):
        rows = self.collected_rows()
        self.assertTrue(rows)
        self.assertEqual(rows, set(NO_TRANSCRIPTS))

    def test_members_are_catalog_agents_without_parser(self):
        agents = set(catalog.load().agents)
        parsers = by_agent()
        for agent in NO_TRANSCRIPTS:
            self.assertIn(agent, agents)
            self.assertNotIn(agent, parsers)
