"""`gitmeta`: the remotes and HEAD of a collected project's repository
(issue 253)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from doubleagent import gitmeta
from doubleagent.inputs import Artifact, Home
from fixtures import PROJ_GIT_CONFIG, PROJ_GIT_HEAD, PROJ_GIT_REMOTES


class ParseRemotesTests(unittest.TestCase):
    def test_fixture_config(self):
        self.assertEqual(gitmeta.parse_remotes(PROJ_GIT_CONFIG), PROJ_GIT_REMOTES)

    def test_pushurl_is_what_the_file_says(self):
        # git falls back to `url` for pushes; the file has no pushurl, so none.
        got = gitmeta.parse_remotes('[remote "origin"]\n\turl = https://h/r.git\n')
        self.assertEqual(got, [{"name": "origin", "urls": ["https://h/r.git"], "pushurls": []}])

    def test_case_comments_quotes_and_continuation(self):
        text = (
            "# a comment\n"
            "; another\n"
            '[Remote "Fork"]\n'
            '  URL = "https://h/a;b#c.git"  # trailing comment\n'
            "  pushUrl = https://h/\\\n"
            "push.git\n"
            '[remote "second"]\n'
            "\turl = https://h/one.git\n"
            "\tpushurl = https://h/push-a.git\n"
            "\turl = https://h/two.git\n"
            "\tpushurl = https://h/push-b.git\n"
            "\turl =\n"
            "[remote.legacy]\n"
            "\turl = /srv/mirror.git\n"
            '[branch "main"]\n'
            "\turl = not-a-remote\n"
        )
        self.assertEqual(
            gitmeta.parse_remotes(text),
            [
                {
                    "name": "Fork",
                    "urls": ["https://h/a;b#c.git"],
                    "pushurls": ["https://h/push.git"],
                },
                {"name": "legacy", "urls": ["/srv/mirror.git"], "pushurls": []},
                # several url and pushurl lines: every value, in file order;
                # an empty value is skipped
                {
                    "name": "second",
                    "urls": ["https://h/one.git", "https://h/two.git"],
                    "pushurls": ["https://h/push-a.git", "https://h/push-b.git"],
                },
            ],
        )

    def test_malformed_lines_are_skipped(self):
        text = (
            '[remote "origin"]\n'
            "\tthis line has no equals sign\n"
            "\turl = https://h/origin.git\n"
            '[remote "broken"\n'  # unterminated header: its keys belong to no remote
            "\turl = https://h/broken.git\n"
            "= no key\n"
            '[remote "upstream"]\n'
            "\turl = https://h/upstream.git\n"
            "\x00\xff garbage\n"
        )
        self.assertEqual(
            gitmeta.parse_remotes(text),
            [
                {"name": "origin", "urls": ["https://h/origin.git"], "pushurls": []},
                {"name": "upstream", "urls": ["https://h/upstream.git"], "pushurls": []},
            ],
        )

    def test_empty_and_remote_without_url(self):
        self.assertEqual(gitmeta.parse_remotes(""), [])
        self.assertEqual(gitmeta.parse_remotes('[remote "x"]\n\tfetch = +refs/*\n'), [])
        # A section with only a push URL is listed.
        self.assertEqual(
            gitmeta.parse_remotes('[remote "p"]\n\tpushurl = https://h/p.git\n'),
            [{"name": "p", "urls": [], "pushurls": ["https://h/p.git"]}],
        )


class ParseHeadTests(unittest.TestCase):
    def test_branch(self):
        self.assertEqual(gitmeta.parse_head(PROJ_GIT_HEAD), "main")
        self.assertEqual(gitmeta.parse_head("ref: refs/heads/feature/x"), "feature/x")

    def test_detached(self):
        sha = "0123456789abcdef0123456789abcdef01234567"
        self.assertEqual(gitmeta.parse_head(sha + "\n"), sha)

    def test_other_ref_and_empty(self):
        self.assertEqual(
            gitmeta.parse_head("ref: refs/remotes/origin/main\n"), "refs/remotes/origin/main"
        )
        self.assertEqual(gitmeta.parse_head(""), "")
        self.assertEqual(gitmeta.parse_head("\n\n"), "")


class ProjectGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cac-gitmeta-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def artifact(self, home: Home, rel: str, text: str | None, agent: str = "project") -> Artifact:
        disk = self.tmp / home.original.strip("/") / rel
        disk.parent.mkdir(parents=True, exist_ok=True)
        if text is not None:
            disk.write_text(text, encoding="utf-8")
        return Artifact(disk, home.original + "/" + rel, rel, agent, home)

    def test_project_git(self):
        proj = Home(self.tmp / "srv/proj", "/srv/proj", "alice", project=True)
        bare = Home(self.tmp / "srv/bare", "/srv/bare", "alice", project=True)
        home = Home(self.tmp / "home/alice", "/home/alice", "alice")
        arts = [
            self.artifact(proj, ".git/config", PROJ_GIT_CONFIG),
            self.artifact(proj, ".git/HEAD", PROJ_GIT_HEAD),
            self.artifact(bare, "AGENTS.md", "# x\n"),
            # A home's .git is not a project's: never read.
            self.artifact(home, ".git/config", PROJ_GIT_CONFIG),
        ]
        self.assertEqual(
            gitmeta.project_git(arts),
            {"/srv/proj": {"remotes": PROJ_GIT_REMOTES, "head": "main"}},
        )

    def test_missing_unreadable_and_symlinked_files(self):
        proj = Home(self.tmp / "srv/proj", "/srv/proj", "alice", project=True)
        # A collected row whose file is gone reads as empty.
        missing = self.artifact(proj, ".git/HEAD", None)
        self.assertEqual(gitmeta.project_git([missing]), {"/srv/proj": {"remotes": [], "head": ""}})
        # A symlink is never followed.
        target = self.tmp / "elsewhere"
        target.write_text(PROJ_GIT_CONFIG, encoding="utf-8")
        link = self.tmp / "srv/proj/.git/config"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        config = Artifact(link, "/srv/proj/.git/config", ".git/config", "project", proj)
        self.assertEqual(gitmeta.read_text(link), "")
        self.assertEqual(gitmeta.project_git([config])["/srv/proj"]["remotes"], [])


if __name__ == "__main__":
    unittest.main()
