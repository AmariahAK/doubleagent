"""Drop rows from secondary sources that a primary store also records
(issue 122).

A secondary source is a file a parser reads beside the agent's own
transcript store and that repeats some of its events: a per-prompt history
file, a mirror or a projection (`Parser.secondary`). Every source is parsed
on every run; this module then keeps each event once. A secondary row is
dropped when a primary row has the same `host`, `user`, `agent`,
`turn_type` and `text`, the same `session_id` (or, when the secondary row
has none, the same `project_path`), and a `timestamp_utc` at most
`TOLERANCE_SECONDS` away. Matching is one-to-one, the primary row always
survives, and a secondary row with no match is kept, so a session whose
transcript was deleted, excluded by size or truncated is still recovered
from its history lines.

Why two seconds: Codex writes `history.jsonl` `ts` in whole seconds beside
the millisecond timestamps of its rollouts; an Antigravity history line and
the database step for the same prompt differ by under a second; Claude
Code writes its history entry when the prompt is submitted, as the
transcript's user record is. Known miss: a prompt an agent queued and sent
later (Claude Code queues input typed while it works) can be minutes from
its transcript record, and is then shown twice, the history line's time
being when it was typed.

Rows with an empty `timestamp_utc` on either side never match, so Muse
Code's `tui-history.jsonl`, which records no time, is always kept.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter

from .model import Row
from .timeutil import epoch_ms

TOLERANCE_SECONDS = 2.0
_TOLERANCE_MS = int(TOLERANCE_SECONDS * 1000)

_Bucket = list[tuple[int, int]]  # (epoch ms, index into primary), sorted


def _identity(r: Row) -> tuple[str, str, str, str, str]:
    return (r.host, r.user, r.agent, r.turn_type, r.text)


def _index(primary: list[Row]) -> tuple[dict[tuple, _Bucket], dict[tuple, _Bucket]]:
    """The primary rows with a timestamp, by session and by project."""
    by_session: dict[tuple, _Bucket] = {}
    by_project: dict[tuple, _Bucket] = {}
    for i, r in enumerate(primary):
        ms = epoch_ms(r.timestamp_utc)
        if ms is None:
            continue
        ident = _identity(r)
        by_session.setdefault((*ident, r.session_id), []).append((ms, i))
        by_project.setdefault((*ident, r.project_path), []).append((ms, i))
    for bucket in (*by_session.values(), *by_project.values()):
        bucket.sort()
    return by_session, by_project


def _nearest(bucket: _Bucket, ms: int, used: set[int]) -> int | None:
    """The index of the unused primary row in `bucket` nearest to `ms` and
    within the tolerance, the earlier one on a tie; None when there is none."""
    best: tuple[int, int] | None = None
    k = bisect_left(bucket, (ms - _TOLERANCE_MS, -1))
    while k < len(bucket) and bucket[k][0] <= ms + _TOLERANCE_MS:
        t, i = bucket[k]
        k += 1
        if i in used:
            continue
        if best is None or abs(t - ms) < best[0]:
            best = (abs(t - ms), i)
    return best[1] if best else None


def deduplicate(primary: list[Row], secondary: list[Row]) -> tuple[list[Row], Counter[str]]:
    """The rows to keep (every primary row, then the secondary rows with no
    primary match, in the order given) and the dropped rows per agent."""
    by_session, by_project = _index(primary)
    used: set[int] = set()
    dropped: set[int] = set()
    counts: Counter[str] = Counter()
    stamped = [(epoch_ms(r.timestamp_utc), j) for j, r in enumerate(secondary)]
    for ms, j in sorted((ms, j) for ms, j in stamped if ms is not None):
        r = secondary[j]
        if r.session_id:
            bucket = by_session.get((*_identity(r), r.session_id))
        else:
            bucket = by_project.get((*_identity(r), r.project_path))
        i = _nearest(bucket, ms, used) if bucket else None
        if i is None:
            continue
        used.add(i)
        dropped.add(j)
        counts[r.agent] += 1
    kept = list(primary) + [r for j, r in enumerate(secondary) if j not in dropped]
    return kept, counts
