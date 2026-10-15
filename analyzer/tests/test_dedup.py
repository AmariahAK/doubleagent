"""dedup.deduplicate: secondary-source rows dropped when a primary store
yields the same event (issue 122)."""

import unittest
from collections import Counter

from doubleagent.dedup import TOLERANCE_SECONDS, deduplicate
from doubleagent.model import Row

SID = "11111111-2222-4333-8444-555555555555"


def row(ts="2026-10-01T10:00:00.000Z", **kw) -> Row:
    r = Row(
        timestamp_utc=ts,
        host="h1",
        user="alice",
        agent="claude-code",
        session_id=SID,
        project_path="/srv/proj",
        turn_type="user",
        text="delete the logs",
        source_file="/home/alice/.claude/projects/-srv-proj/%s.jsonl" % SID,
        source_line=2,
    )
    for k, v in kw.items():
        setattr(r, k, v)
    return r


def hist(ts="2026-10-01T10:00:00.000Z", **kw) -> Row:
    kw.setdefault("source_file", "/home/alice/.claude/history.jsonl")
    kw.setdefault("source_line", 1)
    return row(ts, **kw)


class DeduplicateTests(unittest.TestCase):
    def kept_secondary(self, primary, secondary):
        kept, _ = deduplicate(primary, secondary)
        return kept[len(primary) :]

    def test_match_by_session(self):
        p = row()
        kept, dropped = deduplicate([p], [hist(project_path="/elsewhere")])
        self.assertEqual(kept, [p])
        self.assertEqual(dropped, Counter({"claude-code": 1}))

    def test_match_by_project_without_session(self):
        p = row()
        kept, dropped = deduplicate([p], [hist(session_id="")])
        self.assertEqual(kept, [p])
        self.assertEqual(dropped["claude-code"], 1)

    def test_no_match_by_project_without_session_other_project(self):
        h = hist(session_id="", project_path="/srv/other")
        self.assertEqual(self.kept_secondary([row()], [h]), [h])

    def test_session_differs_project_same(self):
        h = hist(session_id="99999999-0000-4000-8000-000000000000")
        self.assertEqual(self.kept_secondary([row()], [h]), [h])

    def test_one_to_one_nearest(self):
        # A transcript cut after three of five identical prompts keeps two
        # of the five history lines, and each primary row takes the history
        # line nearest to it.
        primary = [
            row("2026-10-01T10:00:%02d.500Z" % s, text="continue", source_line=s)
            for s in (10, 20, 30)
        ]
        secondary = [
            hist("2026-10-01T10:00:%02d.000Z" % s, text="continue", source_line=s)
            for s in (50, 10, 20, 30, 40)
        ]
        kept, dropped = deduplicate(primary, secondary)
        self.assertEqual(kept[:3], primary)
        self.assertEqual([r.source_line for r in kept[3:]], [50, 40])
        self.assertEqual(dropped, Counter({"claude-code": 3}))

    def test_nearest_candidate_wins(self):
        # Secondary rows go in timestamp order, each to the nearest unused
        # primary row: the first line takes the row 0.3 s away, not the one
        # 1.5 s away, which leaves the second line (3.5 s from it) unmatched.
        primary = [row("2026-10-01T10:00:00.000Z"), row("2026-10-01T10:00:01.800Z")]
        first = hist("2026-10-01T10:00:01.500Z", source_line=1)
        second = hist("2026-10-01T10:00:03.500Z", source_line=2)
        self.assertEqual(self.kept_secondary(primary, [second, first]), [second])

    def test_tolerance_boundary(self):
        self.assertEqual(TOLERANCE_SECONDS, 2.0)
        p = row("2026-10-01T10:00:00.000Z")
        self.assertEqual(self.kept_secondary([p], [hist("2026-10-01T10:00:02.000Z")]), [])
        self.assertEqual(self.kept_secondary([p], [hist("2026-10-01T09:59:58.000Z")]), [])
        late = hist("2026-10-01T10:00:02.001Z")
        self.assertEqual(self.kept_secondary([p], [late]), [late])
        early = hist("2026-10-01T09:59:57.999Z")
        self.assertEqual(self.kept_secondary([p], [early]), [early])

    def test_empty_timestamp_never_matches(self):
        h = hist("")
        self.assertEqual(self.kept_secondary([row()], [h]), [h])
        h = hist()
        self.assertEqual(self.kept_secondary([row("")], [h]), [h])
        h = hist("")
        self.assertEqual(self.kept_secondary([row("")], [h]), [h])

    def test_other_fields_never_match(self):
        for field, value in (
            ("turn_type", "system"),
            ("text", "delete the logs!"),
            ("user", "bob"),
            ("host", "h2"),
            ("agent", "codex-cli"),
        ):
            h = hist(**{field: value})
            self.assertEqual(self.kept_secondary([row()], [h]), [h], field)

    def test_primary_never_dropped(self):
        # Two identical primary rows stay, with their own source lines.
        a = row(source_line=2)
        b = row(source_line=9)
        kept, dropped = deduplicate([a, b], [hist()])
        self.assertEqual(kept, [a, b])
        self.assertEqual(sum(dropped.values()), 1)
        kept, dropped = deduplicate([a, b], [])
        self.assertEqual(kept, [a, b])
        self.assertEqual(dropped, Counter())

    def test_counter_per_agent(self):
        primary = [row(), row(agent="antigravity"), row(agent="codex-cli")]
        secondary = [hist(), hist(agent="antigravity"), hist(agent="codex-cli", text="x")]
        _, dropped = deduplicate(primary, secondary)
        self.assertEqual(dropped, Counter({"claude-code": 1, "antigravity": 1}))

    def test_result_order(self):
        # Every primary row in input order, then the unmatched secondary
        # rows in input order, not timestamp order.
        p1 = row("2026-10-01T10:00:05.000Z", text="b")
        p2 = row("2026-10-01T10:00:00.000Z", text="a")
        s1 = hist("2026-10-01T11:00:00.000Z", text="late")
        s2 = hist("2026-10-01T10:00:00.000Z", text="a")
        s3 = hist("2026-10-01T09:00:00.000Z", text="early")
        kept, _ = deduplicate([p1, p2], [s1, s2, s3])
        self.assertEqual(kept, [p1, p2, s1, s3])


if __name__ == "__main__":
    unittest.main()
