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

    def test_earliest_copy_kept(self):
        # Time decides among timestamped copies, not input order: the
        # earlier copy is kept wherever it comes in the input.
        late = hist("2026-10-01T10:00:01.000Z", source_file=BACKUP_A)
        early = hist("2026-10-01T10:00:00.000Z", source_file=BACKUP_B)
        self.assertEqual(dedup([], [late, early])[0], [early])

    def test_copies_of_primary_event_collapse(self):
        # Three copies of one primary event in two files: the first takes
        # the primary row, the other two collapse onto it and onto each
        # other, and only the primary row is left.
        p = row()
        a = hist(source_file=BACKUP_A)
        b = hist("2026-10-01T10:00:00.500Z", source_file=BACKUP_B)
        c = hist("2026-10-01T10:00:01.000Z", source_file=BACKUP_A, source_line=2)
        kept, dropped = dedup([p], [a, b, c])
        self.assertEqual(kept, [p])
        self.assertEqual(dropped, Counter({"claude-code": 3}))
        # Undated copies the same way, in either input order.
        u1 = hist("", source_file=BACKUP_A)
        u2 = hist("", source_file=BACKUP_B)
        for secondary in ([u1, u2], [u2, u1]):
            kept, dropped = dedup([p], secondary)
            self.assertEqual(kept, [p])
            self.assertEqual(dropped, Counter({"claude-code": 2}))

    def test_undated_copy_of_dated_dropped(self):
        # An undated copy pairs with a dated one, whichever comes first in
        # the input, and the dated copy is the one kept.
        dated = hist("2026-10-01T10:00:00.000Z", source_file=BACKUP_A)
        undated = hist("", source_file=BACKUP_B)
        for secondary in ([dated, undated], [undated, dated]):
            kept, dropped = dedup([], secondary)
            self.assertEqual(kept, [dated])
            self.assertEqual(dropped, Counter({"claude-code": 1}))

    def test_most_specific_undated_copy_takes_primary(self):
        # Two undated copies of one event, an unscoped history line first in
        # the input and a session-scoped index row second, and the primary
        # row: the session-scoped copy takes the primary row, the unscoped
        # line collapses onto it, and both drop.
        p = row()
        loose = hist("", session_id="", project_path="", source_file=BACKUP_A)
        scoped = hist("", source_file=BACKUP_B)
        kept, dropped = dedup([p], [loose, scoped])
        self.assertEqual(kept, [p])
        self.assertEqual(dropped, Counter({"claude-code": 2}))

    def test_broader_scope_among_secondary(self):
        # A history line with a project and no session and a mirror line
        # with a session and no project, both copies of one primary event:
        # the history line takes the primary row (project scope), and the
        # mirror line, finding nothing under its session, meets it under its
        # identity alone.
        p = row()
        history = hist(session_id="", source_file=BACKUP_A)
        mirror = hist("2026-10-01T10:00:00.300Z", project_path="", source_file=BACKUP_B)
        kept, dropped = dedup([p], [history, mirror])
        self.assertEqual(kept, [p])
        self.assertEqual(dropped, Counter({"claude-code": 2}))
        # Under a broader scope a candidate of another session or project is
        # never taken: "yes" in two sessions of two backups is two events.
        other = "99999999-0000-4000-8000-000000000000"
        s1 = hist(text="yes", source_file=BACKUP_A)
        s2 = hist(text="yes", session_id=other, source_file=BACKUP_B)
        self.assertEqual(dedup([], [s1, s2])[0], [s1, s2])
        p1 = hist(text="yes", session_id="", source_file=BACKUP_A)
        p2 = hist(text="yes", project_path="/srv/other", source_file=BACKUP_B)
        self.assertEqual(dedup([], [p1, p2])[0], [p1, p2])
        # The primary pass stays strict: a row with a session never takes a
        # primary row of no session under a broader key.
        scoped = hist(session_id=other, project_path="")
        self.assertEqual(self.kept_secondary([row(session_id="")], [scoped]), [scoped])

    def test_tool_rows_pair_on_id(self):
        for turn_type in ("tool_use", "tool_result"):
            p = row(turn_type=turn_type, tool_use_id="call_1", text='{"cmd": ["ls", "-la"]}')
            same_id = hist(turn_type=turn_type, tool_use_id="call_1", text="ls -la")
            kept, dropped = dedup([p], [same_id])
            self.assertEqual(kept, [p], turn_type)
            self.assertEqual(dropped, Counter({"claude-code": 1}), turn_type)
            other_id = hist(turn_type=turn_type, tool_use_id="call_2", text=p.text)
            self.assertEqual(self.kept_secondary([p], [other_id]), [other_id], turn_type)
            # When either row has no id, text decides: a secondary row
            # without one pairs with the primary row with one.
            no_id = hist(turn_type=turn_type, text=p.text)
            self.assertEqual(self.kept_secondary([p], [no_id]), [], turn_type)
            other_text = hist(turn_type=turn_type, text="ls")
            self.assertEqual(self.kept_secondary([p], [other_text]), [other_text], turn_type)
            p_no_id = row(turn_type=turn_type, text="ls -la")
            self.assertEqual(
                self.kept_secondary([p_no_id], [hist(turn_type=turn_type, text="ls -la")]), []
            )
            # The id never stands in for a user row's text.
            u = hist(tool_use_id="call_1", text="other")
            self.assertEqual(self.kept_secondary([row(tool_use_id="call_1")], [u]), [u])
            # Copies among secondary rows pair on the id too.
            a = hist(turn_type=turn_type, tool_use_id="call_1", text="a", source_file=BACKUP_A)
            b = hist(turn_type=turn_type, tool_use_id="call_1", text="b", source_file=BACKUP_B)
            self.assertEqual(dedup([], [a, b])[0], [a], turn_type)

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
