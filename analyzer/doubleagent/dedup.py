"""Drop rows from secondary sources that a primary store also records
(issue 122).

A secondary source is a file a parser reads beside the agent's own
transcript store and that repeats some of its events: a per-prompt history
file, a mirror or a projection (`Parser.secondary`). Every source is parsed
on every run; this module then keeps each event once. A secondary row is
dropped when a primary row has

- the same `host`, `user`, `agent`, `turn_type` and `text`;
- the same `session_id` when the secondary row has one; otherwise the same
  `project_path` when the secondary row has one; otherwise any primary row
  of that host, user and agent, since a text-only history records neither;
- when the secondary row has a `timestamp_utc`, a `timestamp_utc` at most
  the source's tolerance away (`Parser.secondary_tolerance`, by default
  `TOLERANCE_SECONDS`), the bound included; when it has none, any time or
  none.

Matching is one-to-one, the primary row always survives, and a secondary
row with no match is kept, so a session whose transcript was deleted,
excluded by size or truncated is still recovered from its history lines.
The timestamped secondary rows go first, in time order, each to the
nearest unused primary row within its tolerance; then the rows with no
timestamp, in input order, each to the earliest-timestamped unused
candidate, the undated candidates last in input order. Taking the
timestamped rows first keeps an undated row from claiming the primary row
a timestamped one would pair with. Then the secondary rows no primary row
took are matched among themselves in input order under the same rule (the
tolerance of the row being tested), one-to-one, and a row that pairs with an
earlier one is dropped and counted like the others, so the several copies
of one event that backups, snapshots and archives keep after the primary
store is gone are shown once, as the first copy. A row pairs only with an
earlier row from a different `source_file`, since two identical lines in
one file are two events that file records.

Why two seconds: Codex writes `history.jsonl` `ts` in whole seconds beside
the millisecond timestamps of its rollouts; an Antigravity history line and
the database step for the same prompt differ by under a second; Claude
Code writes its history entry when the prompt is submitted, as the
transcript's user record is. Known miss: a prompt an agent queued and sent
later (Claude Code queues input typed while it works) can be minutes from
its transcript record, and is then shown twice, the history line's time
being when it was typed.

Two cases the fixed window does not fit. A text-only prompt history with no
time of its own (Muse Code's `tui-history.jsonl`) yields rows with an empty
`timestamp_utc`, and those match on text and scope alone. A mirror that
stamps an event later than the primary store does (a transcript captured
at the end of a turn) gets a wider window from its parser's
`secondary_tolerance()`. A timestamped secondary row never matches a
primary row with no timestamp.
"""

from __future__ import annotations

from bisect import bisect_left, insort
from collections import Counter
from collections.abc import Container

from .model import Row
from .timeutil import epoch_ms

TOLERANCE_SECONDS = 2.0

_Dated = list[tuple[int, int]]  # (epoch ms, row index), sorted


class _Bucket:
    """The candidate rows of one match key: those with a timestamp, sorted
    by time, and those without, in input order."""

    __slots__ = ("dated", "undated")

    def __init__(self) -> None:
        self.dated: _Dated = []
        self.undated: list[int] = []


def _identity(r: Row) -> tuple[str, str, str, str, str]:
    return (r.host, r.user, r.agent, r.turn_type, r.text)


def _key(r: Row) -> tuple:
    """The match key of a secondary row: its identity and scope."""
    if r.session_id:
        return (*_identity(r), "session", r.session_id)
    if r.project_path:
        return (*_identity(r), "project", r.project_path)
    return (*_identity(r), "any")


def _add(buckets: dict[tuple, _Bucket], r: Row, i: int, ms: int | None) -> None:
    """File candidate `r`, row index `i`, under its session, its project and
    its identity alone, keeping each bucket's timestamps sorted."""
    ident = _identity(r)
    for key in (
        (*ident, "session", r.session_id),
        (*ident, "project", r.project_path),
        (*ident, "any"),
    ):
        bucket = buckets.setdefault(key, _Bucket())
        if ms is None:
            bucket.undated.append(i)
        else:
            insort(bucket.dated, (ms, i))


def _nearest(dated: _Dated, ms: int, tolerance_ms: int, used: Container[int]) -> int | None:
    """The index of the unused row in `dated` nearest to `ms` and within
    `tolerance_ms`, the earlier one on a tie; None when there is none."""
    best: tuple[int, int] | None = None
    k = bisect_left(dated, (ms - tolerance_ms, -1))
    while k < len(dated) and dated[k][0] <= ms + tolerance_ms:
        t, i = dated[k]
        k += 1
        if i in used:
            continue
        if best is None or abs(t - ms) < best[0]:
            best = (abs(t - ms), i)
    return best[1] if best else None


def _earliest(bucket: _Bucket, used: Container[int]) -> int | None:
    """The index of the earliest-timestamped unused row in `bucket`, the
    undated ones last in input order; None when every one is used."""
    for _, i in bucket.dated:
        if i not in used:
            return i
    for i in bucket.undated:
        if i not in used:
            return i
    return None


def _pair(bucket: _Bucket | None, r: Row, tolerance: float, used: Container[int]) -> int | None:
    """The candidate in `bucket` not in `used` that secondary row `r` pairs
    with under the time rule, or None."""
    if bucket is None:
        return None
    ms = epoch_ms(r.timestamp_utc)
    if ms is None:
        return _earliest(bucket, used)
    return _nearest(bucket.dated, ms, int(tolerance * 1000), used)


def _against_primary(primary: list[Row], secondary: list[tuple[Row, float]]) -> list[int]:
    """The indices of the secondary rows that pair with a primary row: the
    timestamped ones first, in time order, then the undated ones in input
    order."""
    buckets: dict[tuple, _Bucket] = {}
    for i, r in enumerate(primary):
        _add(buckets, r, i, epoch_ms(r.timestamp_utc))
    stamped = []
    undated = []
    for j, (r, _) in enumerate(secondary):
        ms = epoch_ms(r.timestamp_utc)
        if ms is None:
            undated.append(j)
        else:
            stamped.append((ms, j))
    used: set[int] = set()
    matched: list[int] = []
    for j in [j for _, j in sorted(stamped)] + undated:
        r, tolerance = secondary[j]
        i = _pair(buckets.get(_key(r)), r, tolerance, used)
        if i is not None:
            used.add(i)
            matched.append(j)
    return matched


class _Unavailable:
    """The earlier secondary rows a row may not pair with: those already
    taken, and those from its own `source_file`, which records them as
    separate events."""

    def __init__(self, used: set[int], same_file: set[int]) -> None:
        self.used = used
        self.same_file = same_file

    def __contains__(self, i: object) -> bool:
        return i in self.used or i in self.same_file


def _among_secondary(secondary: list[tuple[Row, float]], matched: set[int]) -> list[int]:
    """The indices of the secondary rows, of those no primary row took, that
    pair with an earlier one from another `source_file`, in input order,
    each earlier row taken once."""
    buckets: dict[tuple, _Bucket] = {}
    used: set[int] = set()
    by_file: dict[str, set[int]] = {}
    copies: list[int] = []
    for j, (r, tolerance) in enumerate(secondary):
        if j in matched:
            continue
        same_file = by_file.setdefault(r.source_file, set())
        i = _pair(buckets.get(_key(r)), r, tolerance, _Unavailable(used, same_file))
        if i is not None:
            used.add(i)
            copies.append(j)
        _add(buckets, r, j, epoch_ms(r.timestamp_utc))
        same_file.add(j)
    return copies


def deduplicate(
    primary: list[Row], secondary: list[tuple[Row, float]]
) -> tuple[list[Row], Counter[str]]:
    """The rows to keep (every primary row, then the secondary rows with no
    primary match and no earlier copy, in the order given) and the dropped
    rows per agent. Each secondary row comes with its tolerance in seconds."""
    matched = set(_against_primary(primary, secondary))
    dropped = matched | set(_among_secondary(secondary, matched))
    counts: Counter[str] = Counter(secondary[j][0].agent for j in dropped)
    kept = list(primary) + [r for j, (r, _) in enumerate(secondary) if j not in dropped]
    return kept, counts
