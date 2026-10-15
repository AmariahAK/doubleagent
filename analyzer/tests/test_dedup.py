"""dedup.deduplicate: secondary-source rows dropped when a primary store
yields the same event (issue 122)."""

import unittest
from collections import Counter

from doubleagent.dedup import TOLERANCE_SECONDS, deduplicate
from doubleagent.model import Row

SID = "11111111-2222-4333-8444-555555555555"
BACKUP_A = "/home/alice/.app/backups/1/history.jsonl"
BACKUP_B = "/home/alice/.app/backups/2/history.jsonl"
BACKUP_C = "/home/alice/.app/backups/3/history.jsonl"


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


def dedup(primary, secondary, tolerance=TOLERANCE_SECONDS):
    """`deduplicate` with every secondary row at the same tolerance."""
    return deduplicate(primary, [(r, tolerance) for r in secondary])


class DeduplicateTests(unittest.TestCase):
    def kept_secondary(self, primary, secondary, tolerance=TOLERANCE_SECONDS):
        kept, _ = dedup(primary, secondary, tolerance)
        return kept[len(primary) :]

    def test_match_by_session(self):
        p = row()
        kept, dropped = dedup([p], [hist(project_path="/elsewhere")])
        self.assertEqual(kept, [p])
        self.assertEqual(dropped, Counter({"claude-code": 1}))

    def test_match_by_project_without_session(self):
        p = row()
        kept, dropped = dedup([p], [hist(session_id="")])
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
        kept, dropped = dedup(primary, secondary)
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

    def test_timestamped_never_matches_undated_primary(self):
        h = hist()
        self.assertEqual(self.kept_secondary([row("")], [h]), [h])
        self.assertEqual(self.kept_secondary([row("")], [h], 3600.0), [h])

    def test_undated_matches_by_session(self):
        p = row()
        kept, dropped = dedup([p], [hist("", project_path="/elsewhere")])
        self.assertEqual(kept, [p])
        self.assertEqual(dropped, Counter({"claude-code": 1}))
        h = hist("", session_id="99999999-0000-4000-8000-000000000000")
        self.assertEqual(self.kept_secondary([p], [h]), [h])

    def test_undated_matches_by_project(self):
        p = row()
        self.assertEqual(self.kept_secondary([p], [hist("", session_id="")]), [])
        h = hist("", session_id="", project_path="/srv/other")
        self.assertEqual(self.kept_secondary([p], [h]), [h])

    def test_undated_without_session_or_project_matches_any(self):
        # A text-only history records neither: any primary row of that
        # host, user and agent with the text pairs with it.
        p = row(project_path="/srv/other")
        self.assertEqual(self.kept_secondary([p], [hist("", session_id="", project_path="")]), [])
        h = hist("", session_id="", project_path="", user="bob")
        self.assertEqual(self.kept_secondary([p], [h]), [h])

    def test_undated_text_differs(self):
        h = hist("", text="delete the logs!")
        self.assertEqual(self.kept_secondary([row()], [h]), [h])

    def test_undated_both_sides(self):
        self.assertEqual(self.kept_secondary([row("")], [hist("")]), [])

    def test_undated_one_to_one(self):
        # Three undated history lines and two primary rows: two drop, the
        # last in input order is kept; the dated primary row is taken first.
        primary = [row("", source_line=5), row("2026-10-01T10:00:00.000Z", source_line=3)]
        secondary = [hist("", source_line=n) for n in (1, 2, 3)]
        kept, dropped = dedup(primary, secondary)
        self.assertEqual(kept[:2], primary)
        self.assertEqual([r.source_line for r in kept[2:]], [3])
        self.assertEqual(dropped, Counter({"claude-code": 2}))

    def test_undated_takes_earliest(self):
        # The undated row takes the earliest-timestamped unused candidate.
        late = row("2026-10-01T11:00:00.000Z", source_line=9)
        early = row("2026-10-01T09:00:00.000Z", source_line=4)
        dated = hist("2026-10-01T11:00:01.000Z", source_line=2)
        undated = hist("", source_line=1)
        # The dated line pairs with `late`, so the undated one takes `early`;
        # with only `late` there, the undated line is kept.
        self.assertEqual(self.kept_secondary([late, early], [undated, dated]), [])
        self.assertEqual(self.kept_secondary([late], [undated, dated]), [undated])

    def test_timestamped_before_undated(self):
        # The undated row comes first in input order but must not steal the
        # only candidate the timestamped row pairs with.
        p = row()
        undated = hist("", source_line=1)
        dated = hist("2026-10-01T10:00:01.000Z", source_line=2)
        self.assertEqual(self.kept_secondary([p], [undated, dated]), [undated])

    def test_per_row_tolerance(self):
        p = row("2026-10-01T10:00:00.000Z")
        h = hist("2026-10-01T10:05:00.000Z")
        self.assertEqual(self.kept_secondary([p], [h], 600.0), [])
        self.assertEqual(self.kept_secondary([p], [h]), [h])
        # Two rows in one call, each with its own window.
        wide = hist("2026-10-01T10:05:00.000Z", source_line=1)
        narrow = hist("2026-10-01T10:05:00.000Z", source_line=2, text="x")
        primary = [p, row("2026-10-01T10:00:00.000Z", text="x")]
        kept, dropped = deduplicate(primary, [(wide, 600.0), (narrow, 2.0)])
        self.assertEqual(kept[2:], [narrow])
        self.assertEqual(dropped, Counter({"claude-code": 1}))

    def test_undated_copies_collapse(self):
        # Two backups of one history, no primary store: the first copy stays.
        a = hist("", source_line=1, source_file=BACKUP_A)
        b = hist("", source_line=1, source_file=BACKUP_B)
        kept, dropped = dedup([], [a, b])
        self.assertEqual(kept, [a])
        self.assertEqual(dropped, Counter({"claude-code": 1}))

    def test_timestamped_copies_within_tolerance(self):
        a = hist("2026-10-01T10:00:00.000Z", source_file=BACKUP_A)
        b = hist("2026-10-01T10:00:01.500Z", source_file=BACKUP_B)
        self.assertEqual(dedup([], [a, b])[0], [a])
        far = hist("2026-10-01T10:00:02.001Z", source_file=BACKUP_B)
        self.assertEqual(dedup([], [a, far])[0], [a, far])
        # The tolerance is that of the row being tested.
        self.assertEqual(deduplicate([], [(a, 2.0), (far, 600.0)])[0], [a])

    def test_earlier_copy_kept(self):
        # Input order decides, not time: the later row in the input goes.
        late = hist("2026-10-01T10:00:01.000Z", source_file=BACKUP_A)
        early = hist("2026-10-01T10:00:00.000Z", source_file=BACKUP_B)
        self.assertEqual(dedup([], [late, early])[0], [late])

    def test_copy_matched_to_primary_not_reused(self):
        # The first copy pairs with the primary row and is dropped; the
        # second cannot pair with it, so it is kept: one primary row and
        # one history line for two recorded events.
        p = row()
        a = hist(source_file=BACKUP_A)
        b = hist(source_file=BACKUP_B)
        kept, dropped = dedup([p], [a, b])
        self.assertEqual(kept, [p, b])
        self.assertEqual(dropped, Counter({"claude-code": 1}))

    def test_copies_one_to_one_and_chained(self):
        # Two backups each holding "continue" twice, a minute apart, keep
        # two rows; three copies of one event keep one.
        t1, t2 = "2026-10-01T10:00:00.000Z", "2026-10-01T10:01:00.000Z"
        a1, a2, b1, b2 = (
            hist(t, text="continue", source_line=n, source_file=f)
            for n, t, f in (
                (1, t1, BACKUP_A),
                (2, t2, BACKUP_A),
                (1, t1, BACKUP_B),
                (2, t2, BACKUP_B),
            )
        )
        self.assertEqual(dedup([], [a1, a2, b1, b2])[0], [a1, a2])
        c1, c2, c3 = (hist("", source_file=f) for f in (BACKUP_A, BACKUP_B, BACKUP_C))
        kept, dropped = dedup([], [c1, c2, c3])
        self.assertEqual(kept, [c1])
        self.assertEqual(dropped, Counter({"claude-code": 2}))

    def test_repeats_in_one_source_kept(self):
        # Two "yes" lines in one undated history with no primary store are
        # two events the file records: both stay. The same two lines in two
        # files are one event: the first stays.
        a = hist("", text="yes", source_line=1, source_file=BACKUP_A)
        b = hist("", text="yes", source_line=3, source_file=BACKUP_A)
        kept, dropped = dedup([], [a, b])
        self.assertEqual(kept, [a, b])
        self.assertEqual(dropped, Counter())
        c = hist("", text="yes", source_line=1, source_file=BACKUP_B)
        self.assertEqual(dedup([], [a, c])[0], [a])
        stamped = [
            hist("2026-10-01T10:00:00.000Z", text="yes", source_line=n, source_file=BACKUP_A)
            for n in (1, 2)
        ]
        self.assertEqual(dedup([], stamped)[0], stamped)

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
        kept, dropped = dedup([a, b], [hist()])
        self.assertEqual(kept, [a, b])
        self.assertEqual(sum(dropped.values()), 1)
        kept, dropped = dedup([a, b], [])
        self.assertEqual(kept, [a, b])
        self.assertEqual(dropped, Counter())

    def test_counter_per_agent(self):
        primary = [row(), row(agent="antigravity"), row(agent="codex-cli")]
        secondary = [hist(), hist(agent="antigravity"), hist(agent="codex-cli", text="x")]
        _, dropped = dedup(primary, secondary)
        self.assertEqual(dropped, Counter({"claude-code": 1, "antigravity": 1}))

    def test_result_order(self):
        # Every primary row in input order, then the unmatched secondary
        # rows in input order, not timestamp order.
        p1 = row("2026-10-01T10:00:05.000Z", text="b")
        p2 = row("2026-10-01T10:00:00.000Z", text="a")
        s1 = hist("2026-10-01T11:00:00.000Z", text="late")
        s2 = hist("2026-10-01T10:00:00.000Z", text="a")
        s3 = hist("2026-10-01T09:00:00.000Z", text="early")
        kept, _ = dedup([p1, p2], [s1, s2, s3])
        self.assertEqual(kept, [p1, p2, s1, s3])


if __name__ == "__main__":
    unittest.main()
