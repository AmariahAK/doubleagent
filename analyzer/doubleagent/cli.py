"""Command line: detect agents in an input, or write the JSONL timeline."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

from . import VERSION, gitmeta
from . import catalog as catalog_mod
from . import inventory as inventory_mod
from .dedup import deduplicate
from .filters import FORMS_HELP, RowFilter, parse_bound
from .inputs import PROJECT_AGENT, Collection, describe_error, error_reason, open_input
from .model import (
    GIT_REMOTE_PREFIX,
    SCRATCH_PREFIX,
    Row,
    SessionSummary,
    canonical_project_path,
    is_windows_path,
    project_key,
    summarise,
)
from .parsers import ALL, NO_TRANSCRIPTS, Options, by_agent

PROG = "doubleagent"
# The agents whose parser reads at least one secondary source
# (`Parser.has_secondary`), and the `recovered` values of a session that
# secondary sources kept rows of.
SECONDARY_AGENTS = frozenset(p.agent for p in ALL if p.has_secondary)
RECOVERED = ("yes", "partial")
# The agents whose parser records sync, relay and origin state
# (`Parser.records_sync`, `records_relay`, `records_origin`).
SYNC_AGENTS = frozenset(p.agent for p in ALL if p.records_sync)
RELAY_AGENTS = frozenset(p.agent for p in ALL if p.records_relay)
ORIGIN_AGENTS = frozenset(p.agent for p in ALL if p.records_origin)
# The session marks summarised per project, in key order: the key, which
# is also the `SessionSummary` attribute, the value every session must have
# for the full label, the values a session counts with, the full, some and
# none labels, and the agents whose parser records the mark.
PROJECT_MARKS = (
    ("synced", "yes", ("yes",), ("yes", "partial", "no"), SYNC_AGENTS),
    ("relayed", "yes", ("yes",), ("yes", "partial", "no"), RELAY_AGENTS),
    ("origin", "remote", ("remote",), ("remote", "mixed", "local"), ORIGIN_AGENTS),
    ("recovered", "yes", RECOVERED, ("yes", "partial", "no"), SECONDARY_AGENTS),
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Detect AI agent state in a collection and parse it into a JSONL timeline.",
    )
    ap.add_argument("--version", action="version", version="%s %s" % (PROG, VERSION))
    sub = ap.add_subparsers(dest="command", required=True)

    def add_input(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "input",
            type=Path,
            help="collector archive (.tar.gz or .zip), extracted collection, or any directory",
        )
        p.add_argument(
            "--host", default="", help="host name to record when the input has no collection.json"
        )
        p.add_argument(
            "--user",
            default="",
            help="user name to record for a home whose owner cannot be inferred",
        )
        p.add_argument(
            "--work-dir",
            type=Path,
            default=None,
            help="where to extract an archive (default: a temporary directory removed afterwards)",
        )
        p.add_argument(
            "--keep-extracted", action="store_true", help="do not delete the extracted archive"
        )

    d = sub.add_parser("detect", help="list the homes, users and agents found in the input")
    add_input(d)
    d.add_argument("--json", action="store_true", help="machine-readable output")
    d.add_argument("--files", action="store_true", help="list every attributed file")

    t = sub.add_parser("timeline", help="parse transcripts into timeline.jsonl and sessions.jsonl")
    add_input(t)
    t.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    t.add_argument(
        "--include-thinking",
        action="store_true",
        help="emit thinking and reasoning blocks as rows of type thinking",
    )
    t.add_argument(
        "--agent",
        action="append",
        default=[],
        help="only parse this agent (repeatable); default is every agent with a parser",
    )
    t.add_argument(
        "--since",
        metavar="WHEN",
        default="",
        help="keep rows at or after WHEN; see --until for the forms",
    )
    t.add_argument(
        "--until",
        metavar="WHEN",
        default="",
        help="keep rows at or before WHEN. UTC unless an offset is given; a value without a "
        "time of day (2026-10-01, 2026-10, today) covers that whole period. " + FORMS_HELP,
    )
    t.add_argument(
        "--keep-undated",
        action="store_true",
        help="with --since or --until, also keep rows that have no timestamp",
    )
    t.add_argument(
        "--match",
        metavar="REGEX",
        action="append",
        default=[],
        help="keep rows whose text matches this Python regular expression (repeatable, any may "
        "match); a matched tool call keeps its result and a matched result its call",
    )
    t.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="make --match case-insensitive",
    )

    i = sub.add_parser("inventory", help="merge collector --inventory outputs into one fleet CSV")
    i.add_argument(
        "input",
        type=Path,
        nargs="+",
        help="a saved stdout of collect-agent-artifacts --inventory, or a directory of them",
    )
    i.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(inventory_mod.DEFAULT_NAME),
        help="CSV to write (default: %s in the current directory)" % inventory_mod.DEFAULT_NAME,
    )

    c = sub.add_parser("catalog", help="print the bundled artifact catalog")
    c.add_argument(
        "--agents", action="store_true", help="print agent names and whether a parser exists"
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "catalog":
        return cmd_catalog(args)
    if args.command == "inventory":
        return cmd_inventory(args)
    if args.command == "timeline":
        # Checked before an archive is extracted, so a typo fails at once.
        try:
            args.row_filter = build_filter(args)
        except ValueError as e:
            print("error: %s" % e, file=sys.stderr)
            return 2
    cat = catalog_mod.load()
    try:
        col = open_input(args.input, cat, work_dir=args.work_dir, host=args.host)
    except OSError as e:
        print("error: %s" % describe_error(args.input, e), file=sys.stderr)
        return 2
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    try:
        if args.user:
            for h in col.homes:
                if not h.user:
                    h.user = args.user
        if args.command == "detect":
            return cmd_detect(args, col)
        return cmd_timeline(args, col)
    finally:
        if not args.keep_extracted:
            col.cleanup()
        elif col._tmp:
            print("extracted to: %s" % col._tmp, file=sys.stderr)


# ---- catalog --------------------------------------------------------------------


def cmd_catalog(args: argparse.Namespace) -> int:
    cat = catalog_mod.load()
    if not args.agents:
        sys.stdout.write(cat.text)
        return 0
    parsers = by_agent()
    for agent in cat.agents:
        print("%-20s %s" % (agent, "parser" if agent in parsers else "detect only"))
    return 0


# ---- inventory ------------------------------------------------------------------


def cmd_inventory(args: argparse.Namespace) -> int:
    try:
        files = inventory_mod.input_files(args.input)
    except OSError as e:
        print("error: %s" % describe_error("", e), file=sys.stderr)
        return 2
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    rows: list[list[str]] = []
    for f in files:
        try:
            got, junk = inventory_mod.read_file(f)
        except OSError as e:
            print("error: %s" % describe_error(f, e), file=sys.stderr)
            return 2
        if junk:
            print(
                "skipped %d non-inventory line%s in %s" % (junk, "" if junk == 1 else "s", f),
                file=sys.stderr,
            )
        rows.extend(got)
    if args.output.parent != Path(""):
        args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(inventory_mod.INVENTORY_COLUMNS)
        w.writerows(rows)
    hosts = {r[0] for r in rows}
    print(
        "rows:   %d from %d host%s in %s"
        % (len(rows), len(hosts), "" if len(hosts) == 1 else "s", args.output)
    )
    roll = inventory_mod.rollup(rows)
    if roll:
        print()
        print("%-22s %6s %6s  %s" % ("agent", "hosts", "users", "latest"))
        for agent, nh, nu, last in roll:
            print("%-22s %6d %6d  %s" % (agent, nh, nu, last))
    return 0 if rows else 1


# ---- detect ---------------------------------------------------------------------


def detect_table(col: Collection, include_projects: bool = True) -> list[dict]:
    """One row per user, home and agent, in the order the first file was
    met: `user`, `home`, `agent`, `files`, `bytes` (manifest `size`, or the
    size on disk in loose mode), `parser`, `inferred`. With
    `include_projects` false, artifacts in a project directory (a home
    marked `project`) are left out: that is the first table of `detect`,
    whose rows keep this order rather than the per-home grouping of
    `home_agents`."""
    parsers = by_agent()
    rows: dict[tuple[str, str, str], dict] = OrderedDict()
    for a in col.artifacts:
        if a.home.project and not include_projects:
            continue
        key = (a.home.user, a.home.original, a.agent)
        r = rows.get(key)
        if r is None:
            r = rows[key] = {
                "user": a.home.user,
                "home": a.home.original or str(a.home.disk_path),
                "agent": a.agent,
                "files": 0,
                "bytes": 0,
                "parser": a.agent in parsers,
                "inferred": a.home.inferred,
            }
        r["files"] += 1
        r["bytes"] += artifact_bytes(a)
    return list(rows.values())


def artifact_bytes(a) -> int:
    """The size of one artifact: the manifest `size` when the input has a
    manifest, else the file's `lstat` size (0 when it cannot be read)."""
    if a.manifest is not None:
        return int(a.manifest.get("size") or 0)
    try:
        return a.disk_path.lstat().st_size
    except OSError:
        return 0


def home_agents(col: Collection) -> list[dict]:
    """The `homes` array of `detect --json` and inventory.json: one object
    per user home or Docker volume (a home not marked `project`), in the
    order its first collected row was met, with the keys `user`, `home`
    (`home.original`: the manifest `home`, or in loose mode the path
    relative to the input root with a leading `/`, `""` when the root is
    the home), `inferred` and `agents`. `agents` is sorted by agent, one
    object of `agent`, `files`, `bytes` (as in `detect_table`) and
    `parser` per agent with files in that home; a home whose files were
    all missing from the collection has an empty array."""
    parsers = by_agent()
    counts: dict[int, dict[str, dict]] = {}
    for a in col.artifacts:
        if a.home.project:
            continue
        c = counts.setdefault(id(a.home), {}).setdefault(a.agent, {"files": 0, "bytes": 0})
        c["files"] += 1
        c["bytes"] += artifact_bytes(a)
    return [
        {
            "user": h.user,
            "home": h.original,
            "inferred": h.inferred,
            "agents": [
                {"agent": agent, **c, "parser": agent in parsers}
                for agent, c in sorted(counts.get(id(h), {}).items())
            ],
        }
        for h in col.homes
        if not h.project
    ]


def project_agents(col: Collection) -> dict[str, dict]:
    """The agents used on each project directory the input holds, keyed by
    the directory's path on the source host (`home.original`, which in image
    mode still carries the `-r` root) and sorted by it. Only artifacts whose
    home is marked `project` count, so loose input yields an empty dict.

    Each value has `users` (sorted distinct users whose rows name the
    directory), `agents` (keyed by agent, sorted: `files` and `bytes` of
    that agent's files in the directory), and `shared_files` and
    `shared_bytes`, the files with agent `project` (those no single agent
    owns, such as AGENTS.md), which is not an agent and so never a key of
    `agents`. Bytes are the manifest `size`, as in `detect_table`."""
    groups: dict[str, dict] = {}
    for a in col.artifacts:
        if not a.home.project:
            continue
        path = a.home.original or str(a.home.disk_path)
        g = groups.setdefault(
            path, {"users": set(), "agents": {}, "shared_files": 0, "shared_bytes": 0}
        )
        if a.home.user:
            g["users"].add(a.home.user)
        size = artifact_bytes(a)
        if a.agent == PROJECT_AGENT:
            g["shared_files"] += 1
            g["shared_bytes"] += size
        else:
            counts = g["agents"].setdefault(a.agent, {"files": 0, "bytes": 0})
            counts["files"] += 1
            counts["bytes"] += size
    return {
        path: {
            "users": sorted(g["users"]),
            "agents": dict(sorted(g["agents"].items())),
            "shared_files": g["shared_files"],
            "shared_bytes": g["shared_bytes"],
        }
        for path, g in sorted(groups.items())
    }


def detect_object(col: Collection) -> dict:
    """The keys `detect --json` and inventory.json share, in order: `input`,
    `kind`, `host`, `notes`, `homes` (`home_agents`) and `projects` (one
    object per project directory from `project_agents`, its `agents` an
    array of `agent`, `files`, `bytes`, `parser`, as in `homes`, and its
    last two keys `remotes` and `head` from `gitmeta.project_git`, `[]`
    and `""` without the repository files). The callers add `problems`,
    and `detect --json --files` adds `files`."""
    parsers = by_agent()
    git = gitmeta.project_git(col.artifacts)
    projects = [
        {
            "path": path,
            "users": p["users"],
            "agents": [
                {"agent": agent, **counts, "parser": agent in parsers}
                for agent, counts in p["agents"].items()
            ],
            "shared_files": p["shared_files"],
            "shared_bytes": p["shared_bytes"],
            "remotes": git.get(path, {}).get("remotes", []),
            "head": git.get(path, {}).get("head", ""),
        }
        for path, p in project_agents(col).items()
    ]
    return {
        "input": str(col.source),
        "kind": col.kind,
        "host": col.host,
        "notes": col.notes,
        "homes": home_agents(col),
        "projects": projects,
    }


def print_project_table(projects: list[dict]) -> None:
    """The second table of `detect`: one line per agent of each project,
    then a `(shared)` line when the project holds shared files, then a
    `remotes:` line (`remotes_text`) when its repository has remotes; the
    path and users appear on the project's first line only."""
    line = "%-40s %-14s %-18s %8s %12s  %s"
    print(line % ("project", "users", "agent", "files", "bytes", "parser"))
    for p in projects:
        lines = [
            (a["agent"], a["files"], a["bytes"], "yes" if a["parser"] else "detect only")
            for a in p["agents"]
        ]
        if p["shared_files"]:
            lines.append(("(shared)", p["shared_files"], p["shared_bytes"], ""))
        first = (p["path"][:40], ",".join(p["users"]) or "?")
        for i, (agent, files, size, parser) in enumerate(lines):
            path, users = first if i == 0 else ("", "")
            print((line % (path, users, agent, files, size, parser)).rstrip())
        if p["remotes"]:
            print("  remotes: " + remotes_text(p["remotes"]))


def remotes_text(remotes: list[dict]) -> str:
    """`<name> <url> ...` per remote, its `urls` joined by a space, then
    ` (push <pushurl> ...)` when it sets `pushurls`; remotes joined with
    `, `."""
    parts = []
    for r in remotes:
        text = " ".join([r["name"], *r["urls"]])
        if r["pushurls"]:
            text += " (push %s)" % " ".join(r["pushurls"])
        parts.append(text)
    return ", ".join(parts)


def cmd_detect(args: argparse.Namespace, col: Collection) -> int:
    det = detect_object(col)
    if args.json:
        out = {**det, "problems": col.problems}
        if args.files:
            out["files"] = [
                {"user": a.home.user, "agent": a.agent, "path": a.original} for a in col.artifacts
            ]
        json.dump(out, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    print("input:   %s" % col.source)
    print(
        "kind:    %s%s"
        % (
            col.kind,
            "" if col.kind != "loose" else " (no manifest; user and home inferred from paths)",
        )
    )
    print("host:    %s" % (col.host or "(unknown)"))
    for n in col.notes:
        print("note:    %s" % n)
    for p in col.problems:
        print("problem: %s" % p)
    table, projects = detect_table(col, include_projects=False), det["projects"]
    if not table and not projects:
        print("no agent artifacts found")
        return 1
    if table:
        print()
        print(
            "%-14s %-32s %-18s %8s %12s  %s" % ("user", "home", "agent", "files", "bytes", "parser")
        )
    for r in table:
        print(
            "%-14s %-32s %-18s %8d %12d  %s"
            % (
                r["user"] or "?",
                r["home"][:32],
                r["agent"],
                r["files"],
                r["bytes"],
                "yes" if r["parser"] else "detect only",
            )
        )
    if projects:
        print()
        print_project_table(projects)
    if args.files:
        print()
        for a in col.artifacts:
            print("%s\t%s\t%s" % (a.home.user, a.agent, a.original))
    return 0


# ---- timeline -------------------------------------------------------------------


def parsers_for(artifact, parsers: dict[str, list]) -> list:
    # A file in a project directory that the catalog leaves to no single
    # agent (agent `project`, inputs.PROJECT_AGENT) may be read by any of
    # them, so it is offered to every parser.
    if artifact.agent == PROJECT_AGENT:
        return ALL
    own = parsers.get(artifact.agent, [])
    # Parsers that read another agent's files (Cody and Twinny rows inside
    # the state.vscdb of `vscode` or a fork) say so in `reads_agents`.
    return own + [p for p in ALL if artifact.agent in p.reads_agents and p not in own]


def collect_rows(
    col: Collection, opts: Options, agents: list[str]
) -> tuple[list[Row], Counter, list[str], Counter]:
    """Parse every artifact into timeline rows. Returns the rows, sorted;
    their counts per (agent, turn_type); the problems; and the rows dropped
    per agent because a secondary source repeated a primary store's event
    (`dedup.deduplicate`, issue 122)."""
    parsers = by_agent()
    primary: list[Row] = []
    secondary: list[tuple[Row, float]] = []
    problems: list[str] = list(col.problems)
    for a in col.artifacts:
        for p in parsers_for(a, parsers):
            # Filter on the parser's agent, so --agent aider also takes the
            # repository-level Aider files the manifest calls `project`.
            if agents and p.agent not in agents:
                continue
            if not p.wants(a):
                continue
            tolerance = p.secondary_tolerance(a) if p.secondary(a) else None
            try:
                for row in p.parse(a, opts):
                    # One spelling per Windows folder, whichever parser and
                    # store the path came from (issue 112).
                    row.project_path = canonical_project_path(row.project_path)
                    if tolerance is None:
                        primary.append(row)
                    else:
                        secondary.append((row, tolerance))
            except OSError as e:
                problems.append("%s: %s" % (a.original, error_reason(e)))
    rows, deduplicated = deduplicate(primary, secondary)
    counts: Counter = Counter((r.agent, r.turn_type) for r in rows)
    rows.sort(key=lambda r: (r.timestamp_utc == "", r.timestamp_utc, r.source_file, r.source_line))
    return rows, counts, problems, deduplicated


# No spaces after separators: the same layout as `jq -c`, so a grep pattern
# such as '"agent":"codex-cli"' matches both the file and jq's output.
JSONL_SEPARATORS = (",", ":")


def jsonl_line(record: dict) -> str:
    """One JSON object on one line, keys in schema order. Non-ASCII text is
    written as UTF-8 rather than escaped, so grep finds it as typed. U+2028
    and U+2029 are escaped because some line readers (Python's
    str.splitlines among them) split on them, and a record holding a lone
    surrogate, which UTF-8 cannot encode, falls back to ASCII escapes."""
    s = json.dumps(record, ensure_ascii=False, separators=JSONL_SEPARATORS)
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        return json.dumps(record, separators=JSONL_SEPARATORS)
    return s.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def write_jsonl(path: Path, rows) -> None:
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        for r in rows:
            fh.write(jsonl_line(r.as_dict()))
            fh.write("\n")


def build_filter(args: argparse.Namespace) -> RowFilter:
    """The row filter from --since, --until, --keep-undated and --match.
    Raises ValueError with a message for the user on a bad value."""
    since = parse_bound(args.since) if args.since else ""
    until = parse_bound(args.until, end=True) if args.until else ""
    if since and until and since > until:
        raise ValueError("--since %s is after --until %s" % (since, until))
    flags = re.IGNORECASE if args.ignore_case else 0
    patterns = []
    for m in args.match:
        try:
            patterns.append(re.compile(m, flags))
        except re.error as e:
            raise ValueError("--match %r: %s" % (m, e)) from None
    return RowFilter(since, until, args.keep_undated, patterns)


def dropped_summary(deduplicated: Counter) -> str:
    """The text of the timeline's `dropped:` line: the secondary-source rows
    `dedup.deduplicate` dropped, with the agents that had any, by name."""
    total = sum(deduplicated.values())
    text = "%d duplicate rows from secondary sources" % total
    if total:
        text += " (%s)" % ", ".join(
            "%s %d" % (a, deduplicated[a]) for a in sorted(deduplicated) if deduplicated[a]
        )
    return text


def agents_summary(
    detected: bool,
    parsed: list[str],
    unparsed: list[str],
    no_rows: list[str],
    collected_only: list[str] | None = None,
) -> str:
    """The text of the timeline's `agents:` line. `detected` says whether the
    input held any agent at all; `parsed` are the agents that produced rows,
    `unparsed` the detected agents with no parser that are a parser backlog,
    `collected_only` the detected agents with no parser whose files hold
    nothing to parse (`parsers.NO_TRANSCRIPTS`), and `no_rows` the detected
    agents whose parser ran and produced no rows. Each list is sorted and
    reads `none` when empty; `collected_only` and `no_rows` are shown only
    when they have an entry."""

    def names(agents: list[str]) -> str:
        return ", ".join(sorted(set(agents))) or "none"

    if not detected and not parsed:
        return "none were found"
    text = "parsed: %s; detected but not parsed: %s" % (names(parsed), names(unparsed))
    if collected_only:
        text += "; collected only: %s" % names(collected_only)
    if no_rows:
        text += "; parser found no rows: %s" % names(no_rows)
    return text


def project_inventory(
    rows: list[Row],
    sessions: list[SessionSummary],
    collected: list[str] | None = None,
    files: dict[str, dict] | None = None,
) -> dict[str, dict]:
    """Counts per project, the empty path included: rows and sessions in
    total, and per agent the rows, sessions and rows by `turn_type`. A
    session is counted under its summary's project, the first non-empty
    `project_path` among its rows.

    Paths are grouped by `project_key`, so the spellings of one Windows
    folder that differ only in case are one project; any other path is
    compared exactly as recorded. A group is keyed by the spelling of the
    collected project it matches, else by the first spelling seen, in the
    rows (timeline order), then the sessions, then `files`; the output is
    sorted by that key.

    Each non-empty key is a project entry with the keys `status`, `rows`,
    `sessions`, `agents`, `shared_files`, then the four marks of
    `PROJECT_MARKS` (`synced`, `relayed`, `origin`, `recovered`), in that
    order. `status` is
    `collected` when the group matches one of `collected` (the project
    directories the input holds), else `referenced` (named only by rows); a
    collected project no row names is listed with zero counts. `files` maps
    a project path to `project_files` output, looked up through
    `project_key` (the counts of paths with one key are added); each agent
    of a project entry gets `files` and `bytes` after `turn_types` from it
    (0 when absent), an agent with files and no rows is listed with zero
    counts, and `shared_files` is the project's files with agent `project`.
    Each mark is `project_mark` of the project's sessions. After the marks
    come `remotes` and `head`, the repository's (`files` entry, `[]` and
    `""` when it has none, so always for a `referenced` project), and
    `recorded_remotes`, the sorted distinct URLs of the `git remote:` rows
    (`GIT_REMOTE_PREFIX`) among `rows`: a row of a session is counted under
    the session's project, a row without a session under its own
    `project_path`. The empty path's entry (`outside_projects`) has no
    `status`, no `shared_files`, no file counts and none of the three
    repository keys: `rows`, `sessions`, `agents`, then the same marks over
    its sessions."""
    groups: dict[str, dict] = {}
    names: dict[str, str] = {}

    def group(path: str) -> dict:
        key = project_key(path)
        names.setdefault(key, path)
        return groups.setdefault(key, {"rows": 0, "sessions": 0, "agents": {}})

    marks: dict[str, list[SessionSummary]] = {}

    def agent_of(path: str, agent: str) -> tuple[dict, dict]:
        g = group(path)
        a = g["agents"].setdefault(agent, {"rows": 0, "sessions": 0, "turn_types": {}})
        return g, a

    # Collected spellings first, so they name their groups.
    for path in collected or []:
        if path:
            group(path)
    collected_keys = set(groups)
    on_disk_by_key: dict[str, dict] = {}
    for path, f in (files or {}).items():
        m = on_disk_by_key.setdefault(
            project_key(path), {"agents": {}, "shared_files": 0, "remotes": [], "head": ""}
        )
        m["shared_files"] += f["shared_files"]
        m["remotes"] = m["remotes"] or f.get("remotes", [])
        m["head"] = m["head"] or f.get("head", "")
        for agent, counts in f["agents"].items():
            c = m["agents"].setdefault(agent, {"files": 0, "bytes": 0})
            c["files"] += counts["files"]
            c["bytes"] += counts["bytes"]
    for r in rows:
        g, a = agent_of(r.project_path, r.agent)
        g["rows"] += 1
        a["rows"] += 1
        a["turn_types"][r.turn_type] = a["turn_types"].get(r.turn_type, 0) + 1
    for s in sessions:
        g, a = agent_of(s.project_path, s.agent)
        g["sessions"] += 1
        a["sessions"] += 1
        marks.setdefault(project_key(s.project_path), []).append(s)
    for path, f in (files or {}).items():
        if path:
            for agent in f["agents"]:
                agent_of(path, agent)
    recorded = recorded_remotes(rows, sessions)
    out: dict[str, dict] = {}
    for key in sorted(groups, key=names.__getitem__):
        g, path = groups[key], names[key]
        empty_disk = {"agents": {}, "shared_files": 0, "remotes": [], "head": ""}
        on_disk = on_disk_by_key.get(key, empty_disk) if path else None
        agents = {}
        for name in sorted(g["agents"]):
            a = g["agents"][name]
            a["turn_types"] = dict(sorted(a["turn_types"].items()))
            if on_disk is not None:
                counts = on_disk["agents"].get(name, {"files": 0, "bytes": 0})
                a["files"], a["bytes"] = counts["files"], counts["bytes"]
            agents[name] = a
        if on_disk is None:
            out[path] = {"rows": g["rows"], "sessions": g["sessions"], "agents": agents}
        else:
            out[path] = {
                "status": "collected" if key in collected_keys else "referenced",
                "rows": g["rows"],
                "sessions": g["sessions"],
                "agents": agents,
                "shared_files": on_disk["shared_files"],
            }
        for m in PROJECT_MARKS:
            out[path][m[0]] = project_mark(marks.get(key, []), m, set(agents))
        if on_disk is not None:
            out[path]["remotes"] = on_disk["remotes"] if key in collected_keys else []
            out[path]["head"] = on_disk["head"] if key in collected_keys else ""
            out[path]["recorded_remotes"] = sorted(recorded.get(key, ()))
    return out


def recorded_remotes(rows: list[Row], sessions: list[SessionSummary]) -> dict[str, set[str]]:
    """The URLs of the `git remote:` rows of `rows` by `project_key`: a row
    with a session id under its session's project (the summary's
    `project_path`, which `sessions` holds), a row without one, or of a
    session `sessions` does not hold, under its own `project_path`."""
    projects = {(s.host, s.user, s.agent, s.session_id): s.project_path for s in sessions}
    out: dict[str, set[str]] = {}
    for r in rows:
        if r.turn_type != "system" or not r.text.startswith(GIT_REMOTE_PREFIX):
            continue
        url = r.text[len(GIT_REMOTE_PREFIX) :]
        if not url:
            continue
        path = projects.get((r.host, r.user, r.agent, r.session_id), r.project_path)
        out.setdefault(project_key(path), set()).add(url)
    return out


def project_mark(sessions: list[SessionSummary], mark: tuple, agents: set[str]) -> str:
    """A project's mark (`PROJECT_MARKS` row `mark`) from its `sessions`:
    the full label ("yes", or "remote" for origin) when every session has
    the full value, the some label ("partial", "mixed") when some have a
    counted value, the none label ("no", "local") when none has and one of
    the project's `agents` records the mark, "" otherwise and for a project
    with no session."""
    attr, full, hits, labels, mark_agents = mark
    values = [getattr(s, attr) for s in sessions]
    if not values:
        return ""
    if all(v == full for v in values):
        return labels[0]
    if any(v in hits for v in values):
        return labels[1]
    return labels[2] if mark_agents & agents else ""


def collected_projects(col: Collection) -> list[str]:
    """The project directories the input holds, as their paths on the source
    host: collection.json `projects`, even one none of whose files were
    collected, and the homes marked `project` (which adds the bases of rows
    with agent `project` in a collection whose collection.json is missing),
    each in `canonical_project_path` form, sorted and de-duplicated."""
    summary = col.summary or {}
    listed = summary.get("projects")
    paths = {str(p) for p in (listed if isinstance(listed, list) else []) if p}
    paths.update(h.original for h in col.homes if h.project and h.original)
    return sorted({canonical_project_path(strip_image_root(p, summary)) for p in paths})


def scratch_keys(
    col: Collection, rows: list[Row], cat: catalog_mod.Catalog | None = None
) -> set[str]:
    """The `project_key` of every path inventory.json would list as a
    project that is a scratch directory, a working directory that belongs
    to the agent rather than to the user (issue 149); inventory.json lists
    these under `scratch_directories` instead of `projects`. A path is one
    when either holds:

    1. A parser says so: a `system` row whose text starts with
       `SCRATCH_PREFIX` (`scratch directory:`) names it in its own
       `project_path`.
    2. The catalog says so: the path, a `project_path` of `rows` or a
       project directory the input holds (`collected_projects`), is in
       or under a directory that a home catalog entry (of `cat`, the
       bundled catalog when None) names, in one of the input's homes that
       is not a project directory and has a known path on the source host
       (`home_scratch_key`), or it is under a directory that one agent's
       project catalog entry names inside another directory, as an
       agent's own worktree `<project>/.claude/worktrees/<name>` is
       (`project_scratch_key`, issue 227).

    The collector's project list only adds paths to test: a scratch
    directory the collector collected project files from stays one."""
    keys = {
        project_key(r.project_path)
        for r in rows
        if r.turn_type == "system" and r.project_path and r.text.startswith(SCRATCH_PREFIX)
    }
    cat = cat or catalog_mod.load()
    summary = col.summary or {}
    homes = {
        strip_image_root(h.original, summary) for h in col.homes if h.original and not h.project
    }
    paths = [r.project_path for r in rows] + collected_projects(col)
    for key in {project_key(p) for p in paths if p} - keys:
        if project_scratch_key(key, cat) or any(home_scratch_key(key, home, cat) for home in homes):
            keys.add(key)
    return keys


def project_scratch_key(key: str, cat: catalog_mod.Catalog) -> bool:
    r"""Whether `key`, a `project_key`, lies under a directory that a
    project catalog entry of one agent names inside a project:
    `<project>/<entry>/<more>`, with at least one segment before the entry
    (the project) and at least one after it, so `/srv/p/.kilo/worktrees/x`
    is under the `kilo-code` entry `.kilo` of the project `/srv/p`, while
    `/srv/p/.kilo` itself and `/srv/p/src` are not. The entries of the
    pseudo-agent `project` (`AGENTS.md`, `.agents`), which belong to no
    single agent, are skipped. Unlike `home_scratch_key` this needs no
    home path, so it applies in loose mode too. A Windows path is split on
    backslashes and its segments are matched without regard to case."""
    windows = is_windows_path(key)
    flags = re.IGNORECASE if windows else 0
    parts = [p for p in key.split("\\" if windows else "/") if p]
    for e in cat.project_entries:
        if e.agent == PROJECT_AGENT:
            continue
        n = len(e.segments)
        for i in range(1, len(parts) - n):
            pairs = zip(e.regexes, parts[i : i + n], strict=True)
            if all(re.fullmatch(rx.pattern, p, flags) for rx, p in pairs):
                return True
    return False


def home_scratch_key(key: str, home: str, cat: catalog_mod.Catalog) -> bool:
    r"""Whether `key`, a `project_key`, lies in or under a directory that a
    home catalog entry names in `home`, a home's path on the source host:
    `key` must be the home or start with it and a separator, and
    `Catalog.claims_home_path` must claim the rest. A Windows home
    (`C:\Users\a`) is compared in `project_key` form, lower case with
    backslashes, and its segments are matched without regard to case; any
    other home is compared exactly."""
    windows = is_windows_path(home)
    sep = "\\" if windows else "/"
    home_key = project_key(home)
    prefix = home_key if home_key.endswith(sep) else home_key + sep
    if key != home_key and not key.startswith(prefix):
        return False
    return bool(cat.claims_home_path(key[len(home_key) :], windows))


def project_files(col: Collection) -> dict[str, dict]:
    """`project_agents` keyed as `collected_projects` keys its paths, with
    the image root stripped and in `canonical_project_path` form, and summed
    when two directories map to one path: per path `agents` (agent to
    `files` and `bytes`), `shared_files`, and the `remotes` and `head` of
    `gitmeta.project_git` (the first directory's that has them)."""
    summary = col.summary or {}
    git = gitmeta.project_git(col.artifacts)
    merged: dict[str, dict] = {}
    for path, p in project_agents(col).items():
        key = canonical_project_path(strip_image_root(path, summary))
        m = merged.setdefault(key, {"agents": {}, "shared_files": 0, "remotes": [], "head": ""})
        m["shared_files"] += p["shared_files"]
        repo = git.get(path, {})
        m["remotes"] = m["remotes"] or repo.get("remotes", [])
        m["head"] = m["head"] or repo.get("head", "")
        for agent, counts in p["agents"].items():
            c = m["agents"].setdefault(agent, {"files": 0, "bytes": 0})
            c["files"] += counts["files"]
            c["bytes"] += counts["bytes"]
    return merged


def strip_image_root(path: str, summary: dict) -> str:
    """A collected path as the imaged host saw it: in image mode the
    collector records `-r <root>/srv/proj`, while the transcripts on that
    host say `/srv/proj`. Paths outside the root are returned unchanged."""
    root = str(summary.get("root") or "")
    if summary.get("mode") != "image" or root in ("", "/", "\\"):
        return path
    root = root.rstrip("/\\")
    if path.startswith(root) and path[len(root) : len(root) + 1] in ("/", "\\"):
        return path[len(root) :]
    return path


def synced_homes(homes: list[dict], sessions: list[SessionSummary]) -> list[dict]:
    """The `homes` array of inventory.json: `homes` (`home_agents`) with four
    last keys in each agent object, `synced_sessions`, `relayed_sessions`,
    `remote_sessions` and `recovered_sessions`, the number of the sessions
    of that user and agent whose `synced` (issue 151) or `relayed` (issue
    153) is "yes", whose `origin` is "remote" (issue 153), or whose
    `recovered` is "yes" or "partial"."""
    synced = Counter((s.user, s.agent) for s in sessions if s.synced == "yes")
    relayed = Counter((s.user, s.agent) for s in sessions if s.relayed == "yes")
    remote = Counter((s.user, s.agent) for s in sessions if s.origin == "remote")
    recovered = Counter((s.user, s.agent) for s in sessions if s.recovered in RECOVERED)
    return [
        {
            **h,
            "agents": [
                {
                    **a,
                    "synced_sessions": synced[(h["user"], a["agent"])],
                    "relayed_sessions": relayed[(h["user"], a["agent"])],
                    "remote_sessions": remote[(h["user"], a["agent"])],
                    "recovered_sessions": recovered[(h["user"], a["agent"])],
                }
                for a in h["agents"]
            ],
        }
        for h in homes
    ]


def cmd_timeline(args: argparse.Namespace, col: Collection) -> int:
    opts = Options(include_thinking=args.include_thinking)
    rf: RowFilter = args.row_filter
    args.output.mkdir(parents=True, exist_ok=True)
    rows, counts, problems, deduplicated = collect_rows(col, opts, args.agent)
    parsed_agents = sorted({a for a, _ in counts})
    if rf.active:
        rows = rf.apply(rows)
        counts = Counter((r.agent, r.turn_type) for r in rows)
    sessions = summarise(rows, SYNC_AGENTS, RELAY_AGENTS, ORIGIN_AGENTS, SECONDARY_AGENTS)
    timeline = args.output / "timeline.jsonl"
    sess = args.output / "sessions.jsonl"
    write_jsonl(timeline, rows)
    write_jsonl(sess, sessions)
    detect = detect_object(col)
    print("input:     %s (%s)" % (col.source, col.kind))
    print("host:      %s" % (col.host or "(unknown)"))
    for n in col.notes:
        print("note:      %s" % n)
    for p in problems:
        print("problem:   %s" % p)
    if rf.since or rf.until:
        print(
            "window:    %s to %s%s"
            % (
                rf.since or "(start)",
                rf.until or "(end)",
                ", undated rows kept" if rf.keep_undated else "",
            )
        )
    if rf.patterns:
        print(
            "match:     %s%s"
            % (
                " | ".join(p.pattern for p in rf.patterns),
                " (ignore case)" if args.ignore_case else "",
            )
        )
    if rf.active:
        print(
            "filtered:  %d outside the window, %d without a timestamp, %d not matching"
            % (rf.dropped_window, rf.dropped_undated, rf.dropped_match)
        )
    print("dropped:   " + dropped_summary(deduplicated))
    # The agents outside and inside project directories. Shared project
    # files (agent `project`) are routed to every parser, so they are never
    # "detected but not parsed" in their own right.
    agents = [a for h in detect["homes"] for a in h["agents"] if a["agent"] != PROJECT_AGENT]
    agents += [a for p in detect["projects"] for a in p["agents"]]
    # Agents with no parser are a parser backlog, unless their files hold
    # nothing to parse (NO_TRANSCRIPTS), which are collected only.
    unparsed = [r["agent"] for r in agents if not r["parser"] and r["agent"] not in NO_TRANSCRIPTS]
    collected_only = [
        r["agent"] for r in agents if not r["parser"] and r["agent"] in NO_TRANSCRIPTS
    ]
    # An agent left out by --agent was not parsed, so it did not come up empty.
    no_rows = [
        r["agent"]
        for r in agents
        if r["parser"]
        and r["agent"] not in parsed_agents
        and (not args.agent or r["agent"] in args.agent)
    ]
    groups = project_inventory(rows, sessions, collected_projects(col), project_files(col))
    scratch = scratch_keys(col, rows)
    synced = sum(1 for s in sessions if s.synced == "yes")
    relayed = sum(1 for s in sessions if s.relayed == "yes")
    remote = sum(1 for s in sessions if s.origin == "remote")
    recovered = sum(1 for s in sessions if s.recovered in RECOVERED)
    empty: dict = {"rows": 0, "sessions": 0, "agents": {}}
    empty.update({m[0]: "" for m in PROJECT_MARKS})
    inventory_path = args.output / "inventory.json"
    with open(inventory_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "doubleagent_version": VERSION,
                **{k: detect[k] for k in ("input", "kind", "host", "notes")},
                "problems": problems,
                "rows": len(rows),
                "sessions": len(sessions),
                "parsed": parsed_agents,
                "detected_not_parsed": sorted(set(unparsed)),
                "no_rows": sorted(set(no_rows)),
                "homes": synced_homes(detect["homes"], sessions),
                "projects": {
                    k: v for k, v in groups.items() if k and project_key(k) not in scratch
                },
                "outside_projects": groups.get("", empty),
                "deduplicated": {
                    k: deduplicated[k] for k in sorted(deduplicated) if deduplicated[k]
                },
                "collected_only": sorted(set(collected_only)),
                "synced_sessions": synced,
                "relayed_sessions": relayed,
                "remote_sessions": remote,
                "recovered_sessions": recovered,
                "scratch_directories": {
                    k: v for k, v in groups.items() if k and project_key(k) in scratch
                },
            },
            fh,
            indent=2,
        )
    print(
        "agents:    "
        + agents_summary(
            bool(agents), parsed_agents, unparsed, sorted(set(no_rows)), collected_only
        )
    )
    print("rows:      %d in %s" % (len(rows), timeline))
    for (agent, tt), n in sorted(counts.items()):
        print("           %-14s %-12s %d" % (agent, tt, n))
    marks = ["%d synced" % synced] if synced else []
    marks += ["%d relayed" % relayed] if relayed else []
    marks += ["%d remote" % remote] if remote else []
    marks += ["%d recovered" % recovered] if recovered else []
    print(
        "sessions:  %d in %s%s" % (len(sessions), sess, " (%s)" % ", ".join(marks) if marks else "")
    )
    print(
        "inventory: %s (homes, projects, scratch directories, counts per agent, problems)"
        % inventory_path
    )
    return 0 if rows else 1
