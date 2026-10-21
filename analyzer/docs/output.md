# Output

What `detect` prints, the files `timeline` writes, and the
`inventory.json`, `timeline.jsonl` and `sessions.jsonl` schemas.

## detect

`detect` prints the input, its kind (`archive`, `collected` for an extracted
collection, or `loose`), the host, any notes, and up to two tables: one
line per user, home and agent outside any project directory, and, when the
input holds project directories, one line per agent of each project. Both
give the number of files, their bytes (from the manifest `size`, or from
disk in loose mode), and whether a parser exists. The notes cover the
archive hash check, unreadable `collection.json`, manifest rows that do not
parse, and how a loose root was interpreted. One `problem:` line follows the
notes for each directory or file inside the input that could not be read
(see [Unreadable inputs](inputs.md#unreadable-inputs)). `no agent artifacts
found` is printed, with exit code `1`, only when both tables are empty.
`--files` adds one `user<TAB>agent<TAB>path` line per attributed file.
Collections made by collectors before 1.6.0 also hold a `live/` system
snapshot, which appears as agent `live` with no user, and `detect only`.

The first table has the columns `user`, `home` (cut to 32 characters),
`agent`, `files`, `bytes` and `parser` (`yes` or `detect only`), in the
order each user, home and agent's first file was met. Its homes are user
homes and Docker volumes, never a project directory.

Files the collector gathered from a project directory (a repository that
agent state referenced, or one given with `-p`) are listed in the second
table under the agent that owns them: a repository's `.claude/` under
`claude-code`, its `.aider.chat.history.md` under `aider`. Collectors
before 1.12.0 recorded every project file with agent `project`; for such a
collection the analyzer names the agent itself, from the project catalog
in its bundled catalog copy (the `# project artifacts` section of
`doubleagent catalog`): the most specific entry whose glob matches the
file's path relative to the project directory, so an old and a new
collection of the same host list the same agents. Nothing is printed about
the re-attribution.

Some project files belong to no single agent, because several agents read
the same file. These are the shared files: the collector records them
with agent `project`, and the tables count them on the project's
`(shared)` line. They are the `project` lines of the project catalog, and
[`research/shared.md`](../../research/shared.md)
and the per-agent research documents cite each reader:

- `AGENTS.md`, the repository instruction file read by Codex CLI, Copilot
  CLI, Amp, OpenCode, Crush, Factory Droid, Kilo Code, Zed and pi, and
  its variants `AGENTS.override.md` (Codex CLI, pi, Hermes) and
  `AGENT.md` (Amp, Zed).
- `.agents/`, the cross-tool skills directory that Codex CLI, Copilot
  CLI, Amp and Muse Code read.
- `.mcp.json`, the project's list of MCP (Model Context Protocol) servers,
  read by Claude Code, Copilot CLI and Muse Code.
- `.github/copilot-instructions.md`, `.github/git-commit-instructions.md`
  and `.github/instructions/`, the GitHub Copilot instruction files, read
  by the Copilot editor extensions, Copilot CLI, Crush and Zed.
- `SOUL.md` and `USER.md`, the persona and user-profile files of an
  OpenClaw or nanobot workspace; Hermes reads `SOUL.md` too.

A project file no project catalog entry matches is counted as shared as
well. `project` is not an agent, so it never appears as an agent in
either table, and a shared file cannot say which agent used it: a
repository holding only `AGENTS.md` shows that some agent was set up
there, not which one. The per-agent lines are the evidence of a
particular agent.

The project directories are the homes the analyzer marks as projects: the
paths in `collection.json` `projects` and, for a collection from a
collector before 1.12.0, the `home` of each collected row with agent
`project`. A loose input holds none, so the second table is not printed
there, nor for a collection without project files. The table follows the
first after a blank line, sorted by project path:

```text
project                                  users          agent                 files        bytes  parser
/srv/proj                                alice          claude-code               2         1800  yes
                                                        cursor                    3          920  yes
                                                        (shared)                  1          310
/srv/shared                              alice          (shared)                  1          120
```

Each project has one line per agent, sorted by agent, then a `(shared)`
line when it holds shared files, with an empty `parser` column. The path
(cut to 40 characters) and `users` (the users whose manifest rows name the
directory, sorted and joined by `,`) are printed on the project's first
line only.

### detect --json

With `--json`, `detect` prints the same data as one JSON object, indented
by two spaces, and exits `0` even when nothing was found. This example
is a real run on a test collection of host `ws01` with `--json --files`;
the `files` key appears only with `--files`:

```json
{
  "input": "/cases/ws01/ws01",
  "kind": "collected",
  "host": "ws01",
  "notes": [
    "1 manifest rows did not parse"
  ],
  "homes": [
    {
      "user": "alice",
      "home": "/home/alice",
      "inferred": false,
      "agents": [
        {
          "agent": "amp",
          "files": 1,
          "bytes": 2,
          "parser": false
        },
        {
          "agent": "claude-code",
          "files": 3,
          "bytes": 4343,
          "parser": true
        }
      ]
    },
    {
      "user": "bob",
      "home": "/home/bob",
      "inferred": false,
      "agents": [
        {
          "agent": "gemini-cli",
          "files": 1,
          "bytes": 2,
          "parser": true
        },
        {
          "agent": "ollama",
          "files": 1,
          "bytes": 25,
          "parser": true
        }
      ]
    }
  ],
  "projects": [
    {
      "path": "/srv/proj",
      "users": [
        "alice"
      ],
      "agents": [
        {
          "agent": "aider",
          "files": 1,
          "bytes": 41,
          "parser": true
        },
        {
          "agent": "cursor",
          "files": 1,
          "bytes": 9,
          "parser": true
        }
      ],
      "shared_files": 1,
      "shared_bytes": 9
    },
    {
      "path": "/srv/shared",
      "users": [
        "alice"
      ],
      "agents": [],
      "shared_files": 1,
      "shared_bytes": 9
    }
  ],
  "problems": [
    "/home/bob/.gemini/tmp/chats/gone.json: missing from the collection"
  ],
  "files": [
    {
      "user": "alice",
      "agent": "claude-code",
      "path": "/home/alice/.claude/history.jsonl"
    },
    {
      "user": "alice",
      "agent": "claude-code",
      "path": "/home/alice/.claude/projects/-srv-proj/11111111-2222-4333-8444-555555555555.jsonl"
    },
    {
      "user": "alice",
      "agent": "claude-code",
      "path": "/home/alice/.claude/projects/-/99999999-8888-4777-8666-555555555555.jsonl"
    },
    {
      "user": "bob",
      "agent": "ollama",
      "path": "/home/bob/.ollama/history"
    },
    {
      "user": "alice",
      "agent": "amp",
      "path": "/home/alice/.config/amp/settings.json"
    },
    {
      "user": "bob",
      "agent": "gemini-cli",
      "path": "/home/bob/.gemini/settings.json"
    },
    {
      "user": "alice",
      "agent": "aider",
      "path": "/srv/proj/.aider.input.history"
    },
    {
      "user": "alice",
      "agent": "cursor",
      "path": "/srv/proj/.cursor/rules/style.mdc"
    },
    {
      "user": "alice",
      "agent": "project",
      "path": "/srv/proj/AGENTS.md"
    },
    {
      "user": "alice",
      "agent": "project",
      "path": "/srv/shared/AGENTS.md"
    }
  ]
}
```

`inferred` is `true` only in loose mode, where `projects` is always `[]`,
so no single run shows both. `homes` holds the counts of the first table
of `detect`, which prints one line per user, home and agent in the order
each one's first file was met, while `homes` groups them by home and
sorts each home's agents: here alice's `amp` comes before `claude-code`,
which the first table prints first. Its keys, in order:

| Key | Type | Meaning |
| --- | --- | --- |
| `input` | string | The input path as given on the command line, as on the `input:` line. |
| `kind` | string | `archive` (an archive the analyzer extracted), `collected` (an extracted collection: `manifest.jsonl` and `fs/`) or `loose` (any other directory, or an archive that did not unpack to a collection). |
| `host` | string | `--host` when given, else `collection.json` `hostname`, else `""`. |
| `notes` | array of strings | The `note:` lines without their prefix, in the order they were made: the archive sha256 check (`archive sha256 verified against <name>`, or a line starting `WARNING`), `collection.json unreadable: <reason>`, `<n> manifest rows did not parse`, `fs/ found without manifest.jsonl; treating fs/ as the root`, `root is a <agent> directory; treating its parent as the home`. `[]` when there are none. |
| `homes` | array of objects | The first table, grouped by home: one per user home and Docker volume, in the order its first collected row was met; project directories are left out (they are `projects`). |
| `homes[].user` | string | The home's owner: the manifest `user`, or in loose mode the user inferred from the path; `--user` when neither names one; `""` when unknown. |
| `homes[].home` | string | The manifest `home`, the path on the source host: a user's home or a Docker volume's `_data`, never a project directory. In loose mode the home's path relative to the input root with a leading `/`, or `""` when the input root is the home or an agent directory; the text table prints the home's path on the analyst's disk there instead. |
| `homes[].inferred` | boolean | `true` in loose mode, where user and home come from the path; `false` when they come from a manifest. |
| `homes[].agents` | array of objects | One per agent with at least one file in this home, sorted by `agent`; `[]` when every file of the home is missing from the collection. Never holds `project`. |
| `homes[].agents[].agent` | string | Catalog agent name. |
| `homes[].agents[].files` | integer | Files attributed to this agent in this home: collected manifest rows of type `file` whose file is present under `fs/`, or files under a matched catalog path in loose mode. |
| `homes[].agents[].bytes` | integer | Their total size: the sum of the manifest `size` values, or of the sizes on disk in loose mode. |
| `homes[].agents[].parser` | boolean | `true` when the analyzer has a parser for this agent, `false` when it is detected only. |
| `projects` | array of objects | The second table: one per project directory the input holds (see [detect](#detect) for which they are), sorted by `path`. `[]` when there is none, always in loose mode. |
| `projects[].path` | string | The project directory as the manifest's `home` records it, the collector's path; in image mode it still starts with the `-r` root. |
| `projects[].users` | array of strings | The distinct users whose rows name the directory, sorted. |
| `projects[].agents` | array of objects | One per agent that owns at least one file in the directory, sorted by `agent`. Never holds `project`; `[]` when the directory holds only shared files, such as a repository with an `AGENTS.md` and nothing else. |
| `projects[].agents[].agent` | string | Catalog agent name. |
| `projects[].agents[].files` | integer | Files of this agent in the directory, counted as for `homes[].agents[].files`. |
| `projects[].agents[].bytes` | integer | Their total manifest `size`. |
| `projects[].agents[].parser` | boolean | `true` when the analyzer has a parser for this agent, `false` when it is detected only. |
| `projects[].shared_files` | integer | The shared files in the directory: files several agents read, which the manifest records with agent `project` rather than an owner (`AGENTS.md`, `.agents/`, `.mcp.json`, `.github/copilot-instructions.md`, `SOUL.md`; see [detect](#detect) for the full list and their readers). 0 when there is none. |
| `projects[].shared_bytes` | integer | The total manifest `size` of those shared files. |
| `problems` | array of strings | The `problem:` lines without their prefix, `<path>: <reason>`: each directory or file inside the input that could not be read while it was opened, and each collected manifest row whose file is missing from `fs/` (see [Unreadable inputs](inputs.md#unreadable-inputs)). `[]` when there are none. |
| `files` | array of objects | Only with `--files`: one per attributed file, in the order the manifest lists them (the walk order in loose mode). It mirrors the manifest file by file, so a shared file such as `AGENTS.md` appears here with agent `project`. |
| `files[].user` | string | As `homes[].user`. |
| `files[].agent` | string | The attributed agent: the manifest `agent`, re-attributed from the bundled project catalog for a project file of a collection before 1.12.0; `project` for a shared file (`AGENTS.md`, `.mcp.json`). |
| `files[].path` | string | The file's path on the source host, as the manifest records it. |

Before analyzer 0.12.0 the per-home counts were a flat array `agents`,
one object per user, home and agent with the keys `user`, `home`,
`agent`, `files`, `bytes`, `parser` and `inferred`, which also held the
project directories as rows whose `home` was the directory; `homes` had
no `agents` key and listed the project directories too.

## timeline

`timeline` writes three files into `-o`, creating the directory if needed,
overwriting files of the same name, and writes them even when no rows
were produced:

| File | What it holds | Schema |
| --- | --- | --- |
| `timeline.jsonl` | One record per turn, tool call, tool result or system event, sorted by time. | [timeline.jsonl](#timelinejsonl) |
| `sessions.jsonl` | One record per session, with its first and last timestamp, models and counts. | [sessions.jsonl](#sessionsjsonl) |
| `inventory.json` | What was detected and what was parsed: the input's kind, notes and problems; per home the files, bytes and whether a parser exists for each agent; row and session counts per project and outside any project, whether each project directory was collected and the files each agent left in it; and the lists of agents parsed and not parsed. | [inventory.json](#inventoryjson) |

On stdout it prints the input, host and notes, one `problem:` line per
directory or file that could not be read (see
[Unreadable inputs](inputs.md#unreadable-inputs)), and, when the timeline
is filtered, a `window:` line with the resolved UTC bounds, a `match:`
line with the patterns, and a `filtered:` line counting the rows dropped
outside the window, without a timestamp, and not matching. Then comes
the `dropped:` line, always printed, which counts the rows of secondary
sources left out because a primary store, or another secondary source,
records the same event (see
[Secondary sources](#secondary-sources)), with the agents that had any
in parentheses, sorted by name, and no parentheses when the count is 0:

```text
dropped:   3 duplicate rows from secondary sources (antigravity 2, claude-code 1)
dropped:   0 duplicate rows from secondary sources
```

Then come the `agents:` line, the row count with a breakdown by agent and
`turn_type`, and the session count. The breakdown counts the rows written. The
last three line groups name the three files, one each, in this order:

```text
rows:      214 in out/timeline.jsonl
           claude-code    assistant    40
           claude-code    user         50
sessions:  6 in out/sessions.jsonl
inventory: out/inventory.json (homes, projects, scratch directories, counts per agent, problems)
```

`rows:` is followed by one indented line per agent and `turn_type` with
its count, sorted by agent and type, and nothing when there are no rows.
When at least one record of `sessions.jsonl` has `synced` `yes`,
`relayed` `yes`, `origin` `remote` or `recovered` `yes` or `partial`,
the `sessions:` line ends with those counts in parentheses after the
path, in that order, each part present only when its count is greater
than 0 and the parts joined by a comma:
`sessions:  6 in out/sessions.jsonl (1 synced)`,
`sessions:  6 in out/sessions.jsonl (2 relayed)` or
`sessions:  6 in out/sessions.jsonl (1 synced, 2 relayed, 1 remote, 3 recovered)`.
With none it ends at the path, as above. The `synced` part is there
since analyzer 0.14.0, the `relayed`, `remote` and `recovered` parts
since 0.15.0.
The paths are `-o` joined with the file name, as given on the command
line. The exit code is `0` when at least one row was written and `1`
otherwise; the files are written either way. Before analyzer 0.12.0
`timeline` also wrote `detect.json`, named on a `detect:` line before the
`inventory:` line; its content is now in `inventory.json` (see
[inventory.json](#inventoryjson)).

The `agents:` line is always one line. When the input holds at least one
agent it lists them in two to four groups; otherwise it reads
`none were found`:

```text
agents:    parsed: antigravity, claude-code; detected but not parsed: amp
agents:    parsed: claude-code; detected but not parsed: none
agents:    parsed: none; detected but not parsed: amp
agents:    parsed: claude-code; detected but not parsed: none; parser found no rows: antigravity
agents:    parsed: claude-code; detected but not parsed: amp; collected only: copilot
agents:    none were found
```

`parsed` names the agents that produced rows before filtering. `detected but
not parsed` names the agents in the input that have no parser and whose files
hold records a parser is wanted for, the `backlog` rows of the [agents
page](../../docs/agents.md) (the agents `detect` shows without a parser, in
either table, so an agent whose only files are in a project directory counts).
`collected only` names the agents in the input that have no parser because
their files hold nothing to parse, a token store or configuration only: the
`collected` rows of that table. The group follows `detected but not parsed`
and appears only when it has an entry. Before analyzer 0.14.0 those agents
were listed under `detected but not parsed`. `parser found no rows` names the
agents in the input that have a parser which read their files and produced no
rows, such as a data directory holding only an empty database; the group
appears only when it has an entry, and with `--agent` it counts only the
agents selected. Shared files (agent `project`, see [detect](#detect)), which
every parser is offered, are never listed in any group. Each list is sorted
and comma-separated, and `parsed` or `detected but not parsed` reads `none`
when it is empty. `none were found` means the input holds no agent data, where
`detect` prints `no agent artifacts found`. Before analyzer 0.12.0 the line
read `parsed <list>; detected only <list>`, with `none` for an empty list.

## inventory.json

`inventory.json` is one JSON object, UTF-8 without a byte order mark,
indented by two spaces. It is the detection snapshot of the run as well
as its counts: `kind`, `notes`, `homes` and the problems met while the
input was opened are what [`detect --json`](#detect---json) prints for
the same input, so an analyst reads them here later instead of running
`detect` again. Its row and session counts follow what `timeline.jsonl`
and `sessions.jsonl` hold, so with `--since`, `--until` or `--match` they
count the rows and sessions left after filtering, and with `--agent` only
the agents selected. `homes`, `notes`, `problems` and the file counts
(`homes[].agents[].files` and `bytes`, and the project `files`, `bytes`
and `shared_files`) describe the whole input and do not follow the
filters, except that `--agent` changes the parser problems, which come
from the parsers that ran. This example is a real run of `timeline` on
the test collection of the [`detect --json`](#detect---json) example:

```json
{
  "doubleagent_version": "0.14.0",
  "input": "/cases/ws01/ws01",
  "kind": "collected",
  "host": "ws01",
  "notes": [
    "1 manifest rows did not parse"
  ],
  "problems": [
    "/home/bob/.gemini/tmp/chats/gone.json: missing from the collection"
  ],
  "rows": 18,
  "sessions": 2,
  "parsed": [
    "aider",
    "claude-code",
    "ollama"
  ],
  "detected_not_parsed": [
    "amp"
  ],
  "no_rows": [
    "cursor",
    "gemini-cli"
  ],
  "homes": [
    {
      "user": "alice",
      "home": "/home/alice",
      "inferred": false,
      "agents": [
        {
          "agent": "amp",
          "files": 1,
          "bytes": 2,
          "parser": false,
          "synced_sessions": 0,
          "relayed_sessions": 0,
          "remote_sessions": 0,
          "recovered_sessions": 0
        },
        {
          "agent": "claude-code",
          "files": 3,
          "bytes": 4343,
          "parser": true,
          "synced_sessions": 0,
          "relayed_sessions": 0,
          "remote_sessions": 0,
          "recovered_sessions": 0
        }
      ]
    },
    {
      "user": "bob",
      "home": "/home/bob",
      "inferred": false,
      "agents": [
        {
          "agent": "gemini-cli",
          "files": 1,
          "bytes": 2,
          "parser": true,
          "synced_sessions": 0,
          "relayed_sessions": 0,
          "remote_sessions": 0,
          "recovered_sessions": 0
        },
        {
          "agent": "ollama",
          "files": 1,
          "bytes": 25,
          "parser": true,
          "synced_sessions": 0,
          "relayed_sessions": 0,
          "remote_sessions": 0,
          "recovered_sessions": 0
        }
      ]
    }
  ],
  "projects": {
    "/srv/gone": {
      "status": "referenced",
      "rows": 1,
      "sessions": 0,
      "agents": {
        "claude-code": {
          "rows": 1,
          "sessions": 0,
          "turn_types": {
            "user": 1
          },
          "files": 0,
          "bytes": 0
        }
      },
      "shared_files": 0,
      "synced": "",
      "relayed": "",
      "origin": "",
      "recovered": ""
    },
    "/srv/proj": {
      "status": "collected",
      "rows": 8,
      "sessions": 1,
      "agents": {
        "aider": {
          "rows": 1,
          "sessions": 0,
          "turn_types": {
            "user": 1
          },
          "files": 1,
          "bytes": 41
        },
        "claude-code": {
          "rows": 7,
          "sessions": 1,
          "turn_types": {
            "assistant": 2,
            "system": 1,
            "tool_result": 1,
            "tool_use": 1,
            "user": 2
          },
          "files": 0,
          "bytes": 0
        },
        "cursor": {
          "rows": 0,
          "sessions": 0,
          "turn_types": {},
          "files": 1,
          "bytes": 9
        }
      },
      "shared_files": 1,
      "synced": "",
      "relayed": "",
      "origin": "",
      "recovered": "no"
    },
    "/srv/shared": {
      "status": "collected",
      "rows": 0,
      "sessions": 0,
      "agents": {},
      "shared_files": 1,
      "synced": "",
      "relayed": "",
      "origin": "",
      "recovered": ""
    }
  },
  "outside_projects": {
    "rows": 9,
    "sessions": 1,
    "agents": {
      "claude-code": {
        "rows": 7,
        "sessions": 1,
        "turn_types": {
          "assistant": 2,
          "system": 1,
          "tool_result": 1,
          "tool_use": 1,
          "user": 2
        }
      },
      "ollama": {
        "rows": 2,
        "sessions": 0,
        "turn_types": {
          "system": 1,
          "user": 1
        }
      }
    },
    "synced": "",
    "relayed": "",
    "origin": "",
    "recovered": "no"
  },
  "deduplicated": {},
  "collected_only": [],
  "synced_sessions": 0,
  "relayed_sessions": 0,
  "remote_sessions": 0,
  "recovered_sessions": 0,
  "scratch_directories": {}
}
```

`claude-code` is counted in three places. Under `/srv/proj` it has 7
rows and 1 session: one `history.jsonl` line and the six rows of a
session transcript whose working directory is `/srv/proj`; it has no
project files there, because its transcripts are in alice's home, where
`homes` counts its 3 files. Under `/srv/gone`, a `referenced` project, it
has one history line. Under
`outside_projects` it has the other 7 rows and 1 session: the history
line with no project and a session transcript that records no working
directory. `cursor` has a project file its parser does not read, and
`gemini-cli` a settings file, so both have a parser that found no rows;
`amp` has no parser. `deduplicated` is `{}`
because none of the three `history.jsonl` prompts is one a transcript
records, so every history line is kept, `collected_only` is `[]`
because no agent of the input is one with nothing to parse, and every
`synced_sessions`, `relayed_sessions` and `remote_sessions` is 0
because the parsers of the agents with sessions here record no sync,
relay or origin state (the `cursor` parser records origin, but `cursor`
has no session), so every project's `synced`, `relayed` and `origin` is
`""`.
Every `recovered_sessions` is 0 because the session under `/srv/proj`
and the one outside projects come from their transcripts alone (the
history lines that survive carry no session), so the `recovered` of
`/srv/proj` and of `outside_projects` is `no`, while `/srv/gone` and
`/srv/shared` have no session and read `""`. The run was made with
analyzer 0.14.0, before `relayed_sessions`, `remote_sessions`,
`recovered_sessions` and the project and `outside_projects` marks
existed; those keys are filled in by applying the 0.15.0 rules to the
agents and sessions the run shows, not by a run. `scratch_directories`
is `{}` the same way, by the 0.18.0 rules: none of the example's paths
lies under a home or project catalog entry, and none of its agents wrote
a `scratch directory:` row. Its keys, in order:

| Key | Type | Meaning |
| --- | --- | --- |
| `doubleagent_version` | string | The analyzer version that wrote the file, as `doubleagent --version` prints it, so the parser set and row conventions behind the counts can be looked up in the changelog. First key since 0.14.0. |
| `input` | string | The input path, as on the `input:` line. |
| `kind` | string | As in [`detect --json`](#detect---json): `archive`, `collected` or `loose`. |
| `host` | string | The host name, `""` when unknown. |
| `notes` | array of strings | As in [`detect --json`](#detect---json): the `note:` lines without their prefix, in the order they were made; `[]` when there are none. |
| `problems` | array of strings | The `problem:` lines of `timeline` without their prefix, `<path>: <reason>`: first the problems met while the input was opened, as in `detect --json`, then each file a parser could not read, by its path on the source host. Not changed by `--since`, `--until` or `--match`; with `--agent`, only the parsers that ran add theirs. `[]` when there are none. |
| `rows` | integer | The number of records in `timeline.jsonl`, after the filters. |
| `sessions` | integer | The number of records in `sessions.jsonl`, after the filters. |
| `parsed` | array of strings | The `parsed` group of the `agents:` line: the agents that produced rows before filtering, sorted. |
| `detected_not_parsed` | array of strings | The `detected but not parsed` group: the agents in the input, outside or inside a project directory, that have no parser, sorted. Since 0.14.0 it excludes the agents in `collected_only`. |
| `no_rows` | array of strings | The `parser found no rows` group, sorted; `[]` when it is empty. |
| `homes` | array of objects | The `homes` array of [`detect --json`](#detect---json) for the same input, element for element, with `synced_sessions`, `relayed_sessions`, `remote_sessions` and `recovered_sessions` added as the last four keys of each agent object: one per user home and Docker volume, in the order its first collected row was met, never a project directory. Not filtered. |
| `homes[].user` | string | As `homes[].user` in `detect --json`: the home's owner, `""` when unknown. |
| `homes[].home` | string | As `homes[].home` in `detect --json`: the manifest `home`, or in loose mode the path relative to the input root with a leading `/`. |
| `homes[].inferred` | boolean | `true` in loose mode, where user and home come from the path; `false` when they come from a manifest. |
| `homes[].agents` | array of objects | One per agent with files in this home, sorted by `agent`; `[]` when every file of the home is missing from the collection. |
| `homes[].agents[].agent` | string | Catalog agent name; never `project`. |
| `homes[].agents[].files` | integer | Files of this agent in this home, counted as in `detect --json`; not filtered. |
| `homes[].agents[].bytes` | integer | Their total size, the manifest `size` or the size on disk in loose mode; not filtered. |
| `homes[].agents[].parser` | boolean | `true` when the analyzer has a parser for this agent, `false` when it is detected only. |
| `homes[].agents[].synced_sessions` | integer | This user's sessions of this agent whose `synced` in `sessions.jsonl` is `yes`, after the filters; 0 when there is none, and always 0 for an agent whose parser records no sync state. Sessions are matched to the home by `user`. Last key of the object in 0.14.0. |
| `homes[].agents[].relayed_sessions` | integer | This user's sessions of this agent whose `relayed` in `sessions.jsonl` is `yes`, after the filters; 0 when there is none, and always 0 for an agent whose parser records no relay state. Sessions are matched to the home by `user`, as for `synced_sessions`. Added in 0.15.0. |
| `homes[].agents[].remote_sessions` | integer | This user's sessions of this agent whose `origin` in `sessions.jsonl` is `remote`, after the filters; 0 when there is none, and always 0 for an agent whose parser records no origin. Sessions are matched to the home by `user`, as for `synced_sessions`. Added in 0.15.0. |
| `homes[].agents[].recovered_sessions` | integer | This user's sessions of this agent whose `recovered` in `sessions.jsonl` is `yes` or `partial`, after the filters; 0 when there is none, and always 0 for an agent whose parser reads no secondary source. Sessions are matched to the home by `user`, as for `synced_sessions`. Last key of the object since 0.15.0. |
| `projects` | object | Keyed by project path, sorted: every distinct non-empty `project_path` of the rows, and every project directory the input holds, except the scratch directories, the agent's own working directories, which are under `scratch_directories` (since 0.18.0, see below), as the collector's path with the image root removed and Windows paths in the canonical form of [`timeline.jsonl`](#timelinejsonl) `project_path` (see below). Windows paths that differ only in case are one project, keyed by the collected directory's spelling when the project is one, else by the first spelling the rows record. `{}` when there is neither. |
| `projects.<path>.status` | string | `collected` when the path is a project directory the input holds, so its project files are in the collection; `referenced` when only rows name it, because the directory was deleted, was out of the collector's reach, was skipped with `--no-projects`, or is recorded in another form (see below). |
| `projects.<path>.rows` | integer | Rows with this `project_path`, or for a Windows path any spelling of it that differs only in case, after the filters. |
| `projects.<path>.sessions` | integer | Sessions whose `project_path` in `sessions.jsonl` is this one, compared as for `rows`, after the filters. |
| `projects.<path>.agents` | object | Keyed by agent name, sorted: every agent with rows in the project or files in its directory, so the keys are the agents used on the project. Never has the key `project`; `{}` for a project with neither. |
| `projects.<path>.agents.<agent>.rows` | integer | This agent's rows with this `project_path`, compared as for `rows`, after the filters; 0 for an agent with files and no rows. |
| `projects.<path>.agents.<agent>.sessions` | integer | This agent's sessions counted under this project, after the filters. |
| `projects.<path>.agents.<agent>.turn_types` | object | Keyed by `turn_type`, sorted: this agent's rows of each type in the project, after the filters, listing only the types that occur; `{}` with no rows. |
| `projects.<path>.agents.<agent>.files` | integer | The files the collection holds for this agent in this directory, not filtered; 0 for an agent with rows and no files there, and for every agent of a `referenced` project. |
| `projects.<path>.agents.<agent>.bytes` | integer | Their total manifest `size`, not filtered. |
| `projects.<path>.shared_files` | integer | The shared files the collection holds in the directory: files several agents read, which the manifest records with agent `project` rather than an owner (`AGENTS.md`, `.agents/`, `.mcp.json`, `.github/copilot-instructions.md`, `SOUL.md`; see [detect](#detect) for the full list and their readers). Not filtered; 0 for a `referenced` project. |
| `projects.<path>.synced` | string | `yes` when every session counted under the project has `synced` `yes`; `partial` when some do; `no` when none does and at least one agent of the project records sync state; `""` otherwise, and for a project with no session. Since 0.15.0. |
| `projects.<path>.relayed` | string | The same four values from `relayed`, with `no` when at least one agent of the project records relay state. Since 0.15.0. |
| `projects.<path>.origin` | string | `remote` when every session counted under the project has `origin` `remote`; `mixed` when some do; `local` when none does and at least one agent of the project records origin; `""` otherwise, and for a project with no session. Since 0.15.0. |
| `projects.<path>.recovered` | string | `yes` when every session counted under the project has `recovered` `yes`, so the project's primary transcripts are gone and only secondary sources remain; `partial` when some of its sessions are `yes` or `partial`; `no` when none is and at least one agent of the project reads a secondary source; `""` otherwise, and for a project with no session. A `referenced` project whose `recovered` is `yes` is one whose directory and whose agents' primary stores are both gone: what is left of it is the secondary sources. Last keys of the entry since 0.15.0: `synced`, `relayed`, `origin` and `recovered`, in that order. Counts of these sessions are kept only at the top level and per home agent. |
| `outside_projects` | object | The counts for the rows and sessions whose `project_path` is empty. It has no status and no file counts: files outside projects are counted per home under `homes`. |
| `outside_projects.rows` | integer | Rows with an empty `project_path`, after the filters. |
| `outside_projects.sessions` | integer | Sessions with an empty `project_path`, after the filters. |
| `outside_projects.agents` | object | Keyed by agent name, sorted: the agents with such rows or sessions; `{}` when there is none. |
| `outside_projects.agents.<agent>.rows` | integer | This agent's rows with an empty `project_path`, after the filters. |
| `outside_projects.agents.<agent>.sessions` | integer | This agent's sessions with an empty `project_path`, after the filters. |
| `outside_projects.agents.<agent>.turn_types` | object | Keyed by `turn_type`, sorted: this agent's rows of each type, listing only the types that occur. |
| `outside_projects.synced`, `relayed`, `origin`, `recovered` | string | As for a project, by the same rules and in the same order, over the sessions with an empty `project_path` and the agents with such rows or sessions; a Copilot cloud agent task, which records no project, is counted here. Last keys since 0.15.0. |
| `deduplicated` | object | Keyed by agent name, sorted: the agents with rows of a secondary source dropped because a primary store or another secondary source records the same event (see [Secondary sources](#secondary-sources)), the counts of the `dropped:` line. With `--agent`, only the agents selected; not changed by `--since`, `--until` or `--match`, which apply to the rows kept. `{}` when no row was dropped. |
| `deduplicated.<agent>` | integer | The number of this agent's secondary-source rows dropped, never 0. |
| `collected_only` | array of strings | The `collected only` group of the `agents:` line: the agents in the input, outside or inside a project directory, that have no parser because their files hold nothing to parse (the `collected` rows of the [agents page](../../docs/agents.md)), sorted; `[]` when it is empty. Since 0.14.0. |
| `synced_sessions` | integer | The number of records in `sessions.jsonl` whose `synced` is `yes`, after the filters, as for `sessions`; 0 when there is none. Last key in 0.14.0. |
| `relayed_sessions` | integer | The number of records in `sessions.jsonl` whose `relayed` is `yes`, after the filters, as for `sessions`; 0 when there is none. Added in 0.15.0. |
| `remote_sessions` | integer | The number of records in `sessions.jsonl` whose `origin` is `remote`, after the filters, as for `sessions`; 0 when there is none. Added in 0.15.0. |
| `recovered_sessions` | integer | The number of records in `sessions.jsonl` whose `recovered` is `yes` or `partial`, after the filters, as for `sessions`; 0 when there is none. Last key from 0.15.0 to 0.17.0. |
| `scratch_directories` | object | Keyed by path, sorted, and grouped as `projects` is: every `project_path` of the rows, and every project directory the input holds, that is a scratch directory (see below); `{}` when there is none. Last key since 0.18.0. |
| `scratch_directories.<path>.status` | string | As `projects.<path>.status`: `collected` when the collector gathered project files from the directory, `referenced` when only rows name it. Since 0.18.0. |
| `scratch_directories.<path>.rows`, `sessions`, `agents`, `shared_files` | integer, object | As for a project, over the rows and sessions with this `project_path` and the files in the directory; each agent object has the keys of `projects.<path>.agents.<agent>`. Since 0.18.0. |
| `scratch_directories.<path>.synced`, `relayed`, `origin`, `recovered` | string | As for a project, by the same rules and in the same order. Since 0.18.0. |

A row is counted under its own `project_path` and a session under the
session's, the first non-empty `project_path` among its rows, so a session
whose rows name two projects has rows under both and is counted once, under
the first. Rows with no `session_id` belong to no session. The `rows` of
`projects`, `scratch_directories` and `outside_projects` add up to the
top-level `rows`, and their `sessions` to the top-level `sessions`.
Nothing is counted twice: files per home are under `homes`, files per
project directory under `projects` or `scratch_directories`, and rows and
sessions under `projects`, `scratch_directories` and `outside_projects`.

A scratch directory is a working directory that belongs to the agent
rather than to the user: the directory an app creates for a chat that has
no project (the ChatGPT desktop app's `~/Documents/Codex/<date>/<slug>`,
with `work/` and `outputs/` inside), the agent's own state directory or a
clone or worktree it made inside it (Copilot Desktop's
`.copilot/chats/<id>`, `.copilot/repos/<name>` and
`.copilot/canvas-catalog-probe`), or the working directory of a session
the app pre-created and never prompted (Copilot Desktop's pool and probe
sessions, whose `cwd` on Windows is the app's install directory). A
project is a directory the user pointed the agent at. The two are kept
apart because a scratch directory says what the agent did on its own
account, which can still matter to the investigation. A path is a
scratch directory when any of these holds:

1. A parser says so: a `system` row whose `text` starts with
   `scratch directory:` names it in its own `project_path`. The
   `codex-cli` parser writes `scratch directory: <path> (projectless
   thread <id>) (from .codex/.codex-global-state.json
   thread-projectless-output-directories, file mtime)` for each entry of
   the desktop app's map of projectless output directories, and the
   `copilot-cli` parser writes `scratch directory: <cwd> (working
   directory of a session the app pre-created and never prompted: no
   events.jsonl)` for a session directory that holds a `workspace.yaml`
   with a `cwd` and no `events.jsonl`.
2. The catalog says so: the path is in or under a directory that a home
   entry of the bundled catalog names, in one of the input's homes. The
   path relative to the home is matched segment by segment against each
   entry's glob, so `/home/alice/.copilot/chats/<id>` is under the entry
   `.copilot` and `/home/alice/.config/Cursor/x` under
   `.config/[Cc]ursor`, while `/home/alice/.config/myproject` is under no
   entry. A Windows home is compared ignoring case. The rule needs the
   home's path on the source host, which a collection's manifest gives;
   in loose mode it applies only where the analyzer could infer the
   home's path from the tree, and not at all when the input is a home
   itself.
3. The project catalog says so: the path is under a directory that a
   project entry of one agent in the bundled catalog names, inside
   another directory, with at least one segment below the entry. This is
   the worktree an agent makes inside the user's project:
   `/srv/proj/.claude/worktrees/feat` is under the `claude-code` entry
   `.claude`, and `/srv/proj/.kilo/worktrees/k1`,
   `/srv/proj/.gemini/worktrees/g1`, `/srv/proj/.qwen/worktrees/q1` and
   `/srv/proj/.codex/worktrees/c1` under the `kilo-code`, `gemini-cli`,
   `qwen-code` and `codex-cli` entries, while `/srv/proj/.kilo` itself
   and `/srv/proj/src` are not scratch directories. The entries that
   belong to no single agent (`AGENTS.md`, `.agents`, the agent `project`
   in `--list`) do not count. A Windows path is compared ignoring case.
   The rule needs no home path, so it applies in loose mode as well.
   Since 0.20.1 ([issue 227](https://github.com/seanthegeek/doubleagent/issues/227)).

No rule looks at the collector's list of project directories, so a
scratch directory the collector gathered project files from is listed
under `scratch_directories` with `status` `collected`. A scratch
directory the collector gathers as the agent's own files (the Codex
output directory `Documents/Codex`, a `codex-cli` catalog entry since
collector 1.16.0) is not in `collection.json` `projects`, so it is
listed with `status` `referenced`: its files are counted under `homes`
for `codex-cli`, not as project files. The rows keep
their `project_path` in `timeline.jsonl` and `sessions.jsonl`, and
`detect` and `detect --json`, which read no rows, list every project
directory the input holds without applying either rule.

The project directories the input holds are the paths in `collection.json`
`projects` (the directories the collector gathered project files from,
discovered or given with `-p`) and, for a collection whose
`collection.json` is missing or has no `projects`, the `home` of each
collected manifest row with agent `project`. A loose input holds none:
the analyzer does not look for project directories in a loose tree, so
every key there is `referenced`. Each such directory is listed even when
no row names it, and even when the filters left no rows at all.

Paths are compared and counted as recorded, with two exceptions. First,
for a collection made in image mode (`collection.json` `mode` `image`),
the `root` given with `-r` is removed from the front of each project
directory, so `/mnt/image/srv/proj` in `collection.json` matches the
`/srv/proj` the transcripts on that host recorded; the file counts of two
directories that map to one path are added together. Second, a Windows
path (one that starts with a drive letter, or with `\\` for a network
share) is in the canonical form described under
[`timeline.jsonl`](#timelinejsonl) `project_path`, in the rows and in the
project directories alike, and is compared ignoring case, because Windows
file names are case-insensitive: `c:/Users/sean/demo`,
`C:\Users\sean\demo\` and `C:\USERS\sean\demo` are one project. Its
key is the spelling of the collected directory when the project is one,
so a collected project's rows, files and `status` `collected` stay under
the path `collection.json` names; otherwise it is the first spelling seen
in the rows in timeline order, then in the sessions. The case after the
drive is never changed, since the analyzer cannot know the folder's real
casing. Nothing else is normalised, so one repository recorded in two
forms has two keys: a trailing slash or a different case on a POSIX path,
or a Windows image collected on Linux or macOS, whose transcripts say
`C:\Users\alice\proj` while the collector's path, once the root is
removed, is `/Users/alice/proj`. The collector's form then has `status`
`collected` and the files, and the transcripts' form has the rows and
`status` `referenced`.

A jq query that lists projects by row count:

```sh
jq -r '.projects | to_entries | sort_by(-.value.rows)[] | "\(.value.rows)\t\(.key)"' out/inventory.json
```

The same for scratch directories:

```sh
jq -r '.scratch_directories | to_entries | sort_by(-.value.rows)[] | "\(.value.rows)\t\(.key)"' out/inventory.json
```

One that lists each project with the agents used on it:

```sh
jq -r '.projects | to_entries[] | "\(.key)\t\(.value.agents | keys | join(", "))"' out/inventory.json
```

And one that lists the agents that left files in a project but no rows:

```sh
jq -r '.projects | to_entries[] | .key as $p | .value.agents | to_entries[] | select(.value.rows == 0 and .value.files > 0) | "\($p)\t\(.key)"' out/inventory.json
```

Before analyzer 0.12.0 there was no `inventory.json`. The keys are an
interface like the JSONL fields: new ones are added at the end, the
existing ones keep their names, types and meaning. Analyzer 0.13.0 added
`deduplicated`. Analyzer 0.14.0 added `collected_only` and then
`synced_sessions`, the last key, and `synced_sessions` as the last key of
each `homes[].agents[]` object; from that version `detected_not_parsed`
no longer lists the agents with nothing to parse, which it had held since
0.12.0. Analyzer 0.15.0 added `relayed_sessions`, `remote_sessions`
and `recovered_sessions` after `synced_sessions`, in that order, as the
last keys of the file and of each `homes[].agents[]` object, and
`synced`, `relayed`, `origin` and `recovered` as the last keys of each
`projects.<path>` entry and of `outside_projects`. Analyzer 0.18.0
added `scratch_directories` as the last key of the file and moved the
scratch directories out of `projects` into it. The one key added at the front is `doubleagent_version`, in
analyzer 0.14.0, because a reader needs the version before the rest; the
file is one object read by key, not by position.

## JSONL encoding

Both JSONL files are UTF-8 without a byte order mark, one JSON object per
line, each line ended by LF, with no header line. Every object has every
field, in the order listed below. Fields with no value hold the empty string
`""`, never `null`, and every field is a string except the integers
`source_line`, `user_turns`, `assistant_turns` and `tool_calls` and the
array `models`. A line holds no literal line break: newlines inside
`text` are written as `\n`, and U+2028 and U+2029 as `\u2028` and
`\u2029`, because some line readers split on them. Other non-ASCII text is
written as UTF-8, not escaped, so a search for it matches as typed; the
exception is a record whose text holds a lone UTF-16 surrogate, which UTF-8
cannot encode, and which is written entirely with `\uXXXX` escapes.
There is no space after `:` or `,`, the same layout `jq -c` prints, so a
`grep` pattern such as `"agent":"codex-cli"` matches the file and jq output
alike. [searching.md](searching.md) has recipes.

## timeline.jsonl

`timeline.jsonl` fields, in order:

| Field | Type | Meaning |
| --- | --- | --- |
| `timestamp_utc` | string | ISO 8601 UTC with milliseconds, `2026-10-03T16:55:31.123Z`. Times recorded without a zone are taken as UTC. Epoch numbers above 10^11 are read as milliseconds, smaller ones as seconds. Empty when the record has none. |
| `host` | string | `--host` when given, else `collection.json` `hostname`. Empty for loose input without `--host`. |
| `user` | string | From the manifest, inferred from the path, or `--user`. |
| `agent` | string | Catalog agent name of the parser that produced the row. |
| `session_id` | string | The agent's own session or thread identifier. |
| `project_path` | string | Working directory recorded for the turn. A Windows path, one that starts with a drive letter and a separator or with `\\`, is written in one canonical form whichever store recorded it: upper-case drive letter, backslash separators, no repeated separators and no trailing separator except in a drive root (`C:\`), and the extended-length prefix `\\?\` removed (`\\?\UNC\server\share` becomes `\\server\share`), so `c:/Users/sean/demo/` is `C:\Users\sean\demo`. The case after the drive is kept as recorded. Any other path, POSIX paths included, is written as recorded. A `file:` URI is turned into a path by the parser that reads it. |
| `git_branch` | string | Branch recorded for the turn, where the agent logs one. |
| `turn_type` | string | `user`, `assistant`, `tool_use`, `tool_result`, `system`, or `thinking` with `--include-thinking`. |
| `model` | string | Model that produced the turn, where recorded. |
| `tool_name` | string | For `tool_use` rows: the tool. Codex shell calls are `shell`. |
| `tool_use_id` | string | Links a `tool_use` row to its `tool_result`. |
| `text` | string | The event's full text, with leading and trailing whitespace removed and inner line breaks and indentation kept: the prompt, the response, the tool output, or for a tool call its most identifying argument (the Bash command, the edited file, the search pattern, the fetched URL), else the arguments as JSON. It is never truncated, so the timeline is a complete transcript, one event per line. |
| `source_file` | string | Path of the record on the source host, as in the manifest. In loose mode it is the path relative to the input root with a leading `/`, or relative to the home when the input root is the home or an agent directory. |
| `source_line` | integer | Where the record is in that file, so the full record can be read. For line-oriented files (JSONL, Markdown, text) the 1-based line number. For SQLite stores it is the record's `rowid` (Tabby events: the event id), and for JSON documents an array index or `1`. Each parser's module docstring says which. `0` when no position applies. |
| `recovered` | string | `yes` when the row is an event (any `turn_type` but `system`) from a secondary source of its agent (see [Secondary sources](#secondary-sources)) that survived deduplication, so the agent's primary store does not hold the event; since 0.20.0 also the `user` and `assistant` rows the `cursor` parser takes from the `agentKv` prompt blobs of a conversation deleted in the editor, which the editor's database still holds although the conversation's own records are gone. `""` for every other row, including every `system` row of a secondary source (an index header, a thread record, a snapshot, a session-start or permission row, a `parser:` problem), which describes the source or the session rather than a turn the primary store lost. Since analyzer 0.15.0. |

The field names each parser relies on are listed in its module docstring
under `doubleagent/parsers/`. Thinking and reasoning blocks are left out
unless `--include-thinking` is passed.

### Row order and system rows

Rows are sorted by timestamp, then by source file and line. Rows without a
timestamp sort last. Injected context is typed `system`, not `user`, so
the `user` rows are what the person typed. In Claude Code that is
`isMeta` records, task notifications, slash commands and their output, a
subagent's task, compaction summaries and messages from other agents. In
Codex it is `developer` messages and user-role blocks whose content kind
names harness context rather than `user.*` input, or, in older rollouts
without content kinds, a block that is wholly a harness wrapper such as
`<environment_context>`. These `system` rows start with a lowercase label
naming the source, such as `subagent task:`, `task notification:`,
`slash command:`, `command output:` or `context: <kind>:`, followed by the
full text. Each line a parser cannot decode, such as a transcript's last
line cut off mid-write, is reported as its own `system` row whose
`source_line` is that line's number and whose `text` is
`parser: unparseable line (<reason>): <line>`: `<reason>` is the
decoder's message and `<line>` is the whole line as read (decoded as
UTF-8 with undecodable bytes replaced, less its line terminator), with
nothing repaired, extracted or shortened. The rest of the file is still
read. A line that is valid JSON but not an object, in a format whose
lines are objects, is reported the same way as `parser: unparseable line
(not a JSON object): <line>` (since 0.19.0). A database row or an array
element that does not decode is `parser: unparseable record <N>
(<reason>): <record>`: `<N>` is the row's `rowid` (or the id the table
keys it by), the element's position or its index, `<reason>` names the
table and column when the parser knows them (`(<table>.<column>:
<reason>)`, as in `goose`'s `messages.content_json` or `opencode`'s
`part.data`) and otherwise the decoder's message or `not a JSON object`,
and `<record>` is the stored value in full as text (a binary blob as
hex, as `zed` writes a `zstd` thread blob). Readers of JSON arrays use
the same form, with the record's text from its first character to the
end of the file, and a line that decodes but cannot be applied names what
failed, as VS Code's `parser: mutation not applied (<reason>): <line>`
does. An error that concerns the whole file rather than one line (the
file cannot be read, is not a JSON array, ends inside an array, is not a
SQLite database, or lacks the table the format keeps its records in) is
one `system` row `parser: <message>`, such as `parser: unterminated JSON
array`, `parser: not a SQLite database`, `parser: SQLite error:
<error>` or `parser: no <table> table in the session database`, with
the line number when the error has one and `0` otherwise.

Antigravity's permission state is also typed `system`. A grant recorded on
a step is `permission grant: action=<action> target=<target>
allow=<true|false> scope=<scope>`, or for a file access entry
`permission grant: path=<path> is_directory=<true|false>
allow=<true|false> scope=<scope>`; it follows the step's own rows and
carries the step's `tool_name` and `tool_use_id`, so it joins to the call
it governed. A standing grant from a settings file is
`permission setting: <key>=<value> (from <file>, file mtime)`: its
`timestamp_utc` is the file's modification time, not the time of the
grant, which no file records, and its `session_id` is empty, so it
appears in `timeline.jsonl` but in no `sessions.jsonl` record. The
[`antigravity` subsection of the agents page](../../docs/agents.md#antigravity) lists the
files.

Permission state and the model in use are `system` rows too. The
`claude-code` parser (and `claude-desktop` for the transcripts it reads
with the same reader) writes `permission mode: <mode>` at a session's
first permission mode and `permission mode: <old> -> <new>` on each
change, and `model: <id>` at the first assistant reply and
`model: <old> -> <new>` on each change, with ` requested=<id>` when the
model asked for differs from the one that answered; the `model` column of
a model row is the new model. Each subagent transcript tracks its own.
Standing permission settings are one row per entry, `permission setting:
<key>=<value> (from <file>, file mtime)`: `permissions.allow`, `deny`,
`ask`, `additionalDirectories`, `defaultMode` and
`disableBypassPermissionsMode` from `.claude/settings.json` and
`.claude/settings.local.json` (the user's, or a project's with
`project_path` the project), and `allowedTools`, `hasTrustDialogAccepted`
and `hasClaudeMdExternalIncludesApproved` per project from `.claude.json`
(with `project_path` the project key). Their `timestamp_utc` is the
file's modification time (the manifest `mtime` when there is a
manifest), not the time the entry was added, and their `session_id` is
empty. A Claude Desktop session record adds ` permission_mode=<mode>
effort=<effort>` to its row and one `permission grant: <key> <entry>` or
`permission grant: <key>=<value>` row per session grant, timestamped at
the record's `lastActivityAt` (else `createdAt`), which the text names as
`(as of <field>)`. A per-call decision stays `permission decision:`
(Claude Code) or `permission request:`, `permission response:`,
`permission auto-approved:` and `permission auto-denied:` (the Claude
Desktop audit log).

The `codex-cli` and `open-interpreter` parsers (one shared reader) write
`model: <id>` at the first record of a rollout that names a model and
`model: <old> -> <new>` at each later one whose model differs, and one
composite `permission mode: approval=<approval_policy>
sandbox=<sandbox_policy> profile=<permission_profile> network=<network>
reviewer=<approvals_reviewer> profile_id=<active_permission_profile.id>`
row at the first record with any of those fields and `permission mode:
<old> -> <new>` whenever the composite changes. The records are each
`turn_context` and each `thread_settings_applied` event, which the
ChatGPT desktop app writes the moment the user changes the model, the
reviewer or the access level, before any turn, so the row is dated when
the setting changed rather than at the next turn. A settings event
supplies only the thread-level fields, `approval`, `reviewer` and
`profile_id`; `sandbox` and `profile` are the turn's, so a row dated at
a settings event shows them as the last `turn_context` had them, or as
`-` when the access level (`profile_id`) changed, until the next
`turn_context` fills them in, and a settings event before the thread's
first `turn_context` is folded into that turn's row. A
missing field is `-` and an object field is compact JSON, so a value
reads `sandbox={"type":"workspace-write"}`. `reviewer` is `user` when
the user approves each escalated call, and `auto_review` in the desktop
app's "Approve for me" mode, where an automatic reviewer (a guardian
review thread) decides instead; `profile_id` is the desktop app's
access level, `:workspace` or `:danger-full-access` ("Full access", no
sandbox and no approvals), on Codex Desktop 0.163.0-alpha.10.2 inside
ChatGPT 26.1013.40934 (macOS, 2026-10-18). Both rows take the record's
timestamp, and the `model` column of both is the new model. The
`reviewer` and `profile_id` fields were added at the end of the
composite in analyzer 0.16.0, so every `permission mode:` row of these
parsers ends `reviewer=- profile_id=-` when the rollout records
neither.

Each turn of a rollout whose `task_started` record carries
`turn_attribution.turn_trigger` gets a row `turn trigger: <turn_trigger>
turn=<turn_id>` after its `task_started turn=<turn_id>` row. The values
seen with Codex Desktop 0.163.0-alpha.10.2 inside ChatGPT 26.1013.40934
(macOS, 2026-10-18 and 2026-10-19):

| `turn_trigger` | What started the turn |
| --- | --- |
| `composer` | A prompt typed in the desktop app. |
| `remote_ios` | A prompt sent from the ChatGPT iPhone app over remote control (Settings > Connections > Control this Mac or PC): the phone drives the desktop's thread, which stays local. |
| `remote_android` | The same from the ChatGPT Android app. |
| `guardian_review` | The automatic reviewer's turn, in a guardian review thread. |
| `scheduled_task_setup` | The first turn of a scheduled task's thread, when the task is created. |
| `automation_heartbeat_run_now` | A scheduled task run with Run now. |
| `automation_heartbeat_scheduled` | A scheduled task run at its scheduled time. |

Codex records no per-call approval in its rollouts. The desktop app's
are written to `logs_<N>.sqlite`: each user decision is one row
`permission decision: <decision> exec <item id> turn=<turn_id> (from
logs_<N>.sqlite logs, ts)` at the log row's time, with the thread as
`session_id` and the governed item's id as `tool_use_id`, which is the
`tool_use_id` of the call's `tool_use` row; `<decision>` is the log's
own word, `denied` or `approved` on this row. An app-server response to
an approval request (`Decline` or `Accept`) with no such row within two
seconds of it is `permission decision: <decision> request <request id>
(from logs_<N>.sqlite logs, ts)` with no session; on the install
observed those response rows had left the database before it was
collected, while the decision rows above remained. In the "Approve for me" mode the app spawns a guardian review
thread (a rollout with `thread_source` `guardian_review` and the user's
thread as `parent_thread_id`) whose final answer is the verdict: it is
one row `permission decision: <outcome> (auto_review
risk_level=<risk_level> user_authorization=<user_authorization>) exec
<item id> reviewer <review thread id>: <rationale>` at the review's
`task_complete` time, carrying the user's thread as `session_id`, an
empty `model` (the reviewer's model is not the thread's), and
the governed item's id as `tool_use_id` when the log names exactly one
call under review in that window (else `exec -` and an empty
`tool_use_id`); `allow` is the outcome seen. A log row of an approval
whose text the parser cannot read is a `parser: unreadable approval log
row (<target>): <text>` row.

From Codex source, with no real install yet to confirm them, and for
Open Interpreter's home as well where the fork keeps the code: an
`apply_patch` approval in `logs_<N>.sqlite` is `permission decision:
<decision> patch <item id> (from logs_<N>.sqlite logs, ts)`, with the
thread as `session_id` and the `FileChange` item's id as `tool_use_id`;
each record of the `guardian_review_feedback` table of `state_5.sqlite`,
an automatic review that did not allow the action, is a row at the
record's capture time with the reviewed thread as `session_id` and the
governed item as `tool_use_id`. A `denied` record whose decision is the
reviewer's JSON verdict reads exactly as the guardian review thread's
row, so the timeline keeps one of the two; any other reads
`permission decision: <status> (auto_review feedback model=<model>) exec
<item id> turn=<turn id> reviewer <review thread id>: <decision> action:
<reviewed command>`, `<status>` being `denied`, `invalid_decision`,
`missing_decision`, `failed`, `timed_out` or `aborted`. The standing
grants are one row each, `permission setting: <key>=<value> (from
.codex/config.toml, file mtime)` for `approval_policy`,
`approvals_reviewer`, `sandbox_mode`, `default_permissions`,
`projects.<path>.trust_level` (with `project_path` the path) and each MCP
or app tool's `approval_mode`, and `permission setting: <statement> (from
.codex/rules/<file>, file mtime)` for each statement of a rules file
(`prefix_rule(...)` for an "approve and remember" answer,
`network_rule(...)` for a network answer), at the file's modification
time with an empty `session_id`; a project's own `.codex/config.toml` and
`.codex/rules/` give the same rows with the project as `project_path`.
No other key of `config.toml` is shown. A `thread_goal_updated` event is
`thread goal: status=<status> turn=<turn id> objective: <objective>`, and
each `.codex/memories/rollout_summaries/<file>.md` is one row
`memory summary: thread <thread id> rollout=<path> (from <file>,
updated_at): <summary>` at the summary's `updated_at`, with the thread as
`session_id`; it repeats no event, so it is never dropped as a copy.

Each `/feedback` report recorded in `logs_<N>.sqlite`
is one row `session synced: feedback report uploaded to Sentry,
attachments <uploaded_attachments> failed <attachments_failed> (from
logs_<N>.sqlite logs, ts)` at the log row's time, with `-` for a field
the log line lacks and `session_id` the reported thread, empty when no
thread was open. Each row of the `remote_control_enrollments` table of
`state_5.sqlite`, the host's enrollment for remote control, is one row
`remote control: enabled=<0|1> server=<server_id>
environment=<environment_id> host=<server_name>
client=<app_server_client_name> account=<account_id>` at its
`updated_at`, with an empty `session_id`: remote control lets a paired
phone or desktop drive this host's threads, and turning it off keeps the
row with `enabled=0`. It is not a sync: the threads stay on the host.

The `codex-cli` parser also reads the desktop app's
`.codex/.codex-global-state.json`, a secondary source that keeps traces
of a thread the app deleted. Its prompt history gives `user` rows with
an empty `timestamp_utc` and the thread as `session_id`, which pair with
the rollout's prompts on text and are kept, and marked `recovered`, when
the rollout is gone. Its `system` rows are at the file's modification
time and end `(from .codex/.codex-global-state.json <key>, file mtime)`
or `(from .codex/.codex-global-state.json, file mtime)`:
`session deleted: <thread id>` for each thread the app deleted, `thread
description: <description> last_activity=<time>` per thread, `permission
mode (standing): approval=<approvalPolicy> sandbox=<sandboxPolicy>
reviewer=<approvalsReviewer> profile_id=<id>` per thread, `permission
setting: <key>.<host>=<value>` or `permission setting: <key>=<value>`
for the app's agent mode (`agent-mode-by-host-id`,
`preferred-non-full-access-agent-mode-by-host-id`,
`permission-selection-by-host-id:<host>`; `guardian-approvals` is the
"Approve for me" mode), and `remote control: mobile device
connected=<true|false> environment=<id>` when a phone was ever paired.
Since 0.18.0, each entry of the top-level
`thread-projectless-output-directories` map, the directory the app made
for a thread with no project, is also a `scratch directory: <path>
(projectless thread <thread id>)` row whose `project_path` is that
directory (see [`inventory.json`](#inventoryjson)).
A value the file lacks is `-`.

The `gemini-cli` and `qwen-code` parsers write `model: <id>` at a
session's first record that names a model and `model: <old> -> <new>`
on each change, tracked per session id: for Gemini CLI from each gemini
message's `model`, for Qwen Code from the `session_model` record, which
reads `model: <id> auth=<authType>`, and from each assistant record's
`model`; a Qwen Code `logs.json` `model_switch` entry reads
`model: <from> -> <to> reason=<reason>`. A tool call whose status is
`cancelled` or `awaiting_approval` keeps its `[<status>]` prefix on the
`tool_result` row and is followed by `permission decision: <status>`
with the call's `tool_name` and `tool_use_id` (after the `tool_use` row
when there is no result). Each folder in `.gemini/trustedFolders.json`
or `.qwen/trustedFolders.json` is one row
`permission setting: trustedFolders.<path>=<value> (from <file>, file mtime)`,
where `<value>` is the recorded trust level (`TRUST_FOLDER`,
`TRUST_PARENT` or `DO_NOT_TRUST`), with `project_path` the folder, the
file's modification time and an empty `session_id`. Each entry of Qwen
Code's `.qwen/channels/sessions.json` or
`.qwen/channels/daemon/<hash>/routes.json` is one row `session relayed:
channel <channelName> chat <chatId> sender <senderId> thread <threadId>
(from channels/sessions.json, startedAt)`, with `-` for an absent value,
the entry's `sessionId` as `session_id` and its `cwd` as
`project_path`, at `startedAt`, or at the file's modification time with
the text ending `file mtime)`; the daemon form names its `routes.json`.
Since 0.19.0 both parsers read a `trustedFolders.json` with a byte-order
mark, comments or trailing commas, as Qwen Code does. A Qwen Code `user`
record the user did not type is a `system` row `<subtype>
(provenance=<provenance> agent=<agentName> agentId=<agentId>): <text>`,
the parts the record lacks left out: a `cron` or `notification` record
(`cron (provenance=system): ...`), an `agent_message` or `agent_mention`
another workspace agent wrote (`provenance=external_agent`), and a
record of `goal_runtime` provenance; the user's own `agent_mention` stays a `user` row.

The `antigravity` parser writes `model: <id>` before the rows of a
conversation's first step that the `gen_metadata` table names a model for
(`chat_model.response_model`, else `model_display_name`) and
`model: <old> -> <new>` before the rows of each later step whose model
differs, at the step's `created_at`, with the new model in the `model`
column; the format has no switch record, so a change is seen only as a
different model on a later step. A `run_command` or `mcp_tool` call the
user rejected is followed, after its `tool_result` row (which keeps its
`[rejected by user]` marker), by `permission decision: user_rejected` with
the call's `tool_name`, `tool_use_id` and result time, and a
`run_command` result that ran in Antigravity's sandbox ends with
` sandbox=true`.

The `opencode` and `kilo-code` parsers write `model: <modelID>
provider=<providerID>` before the first message of a session that names a
model and `model: <old> -> <new> provider=<providerID>` before each later
message, or V2 `model-switched` record, whose model differs; the `model`
column of the row is the new `<providerID>/<modelID>`. They write
`permission mode: agent=<name>` and `permission mode: agent=<old> ->
agent=<new>` for the message's `agent` and for a V2 `agent-switched`
record, because an OpenCode or Kilo Code agent (`build`, `plan`, a custom
one) is a mode with its own permission ruleset. Both rows take the
message's timestamp and `source_line` and precede its other rows. Since
0.19.0 they read an OpenCode 2.0 database: session-start rows come from
`session_v2` and end with `fork=<id>` for a forked session, and the
`session_message` records of 2.0 add these rows: a `shell` record's
`tool_use` row (tool `shell`) and its `tool_result` row, whose text starts
`[timeout]`, `[killed]` or `[exit <code>]` when the command did not exit
0; `location switched: <old directory> -> <new directory>` with
` workspace=<id>` and ` subpath=<path>` when recorded (the session's
`project_path` stays its `directory`); `skill <name>: <text>`; `idle:
<outcome>` with the error after it when there is one; and `compaction
<reason> <status> <summary>`, all `system` but the shell rows. A session
that a 2.0 database holds only in the 1.x `session` table has a
session-start row ending `(only in the 1.x session table)`, and its rows
come from the 1.x `message` and `part` tables (see
[Secondary sources](#secondary-sources)). The
`crush` parser writes `model: <model> provider=<provider>` and `model:
<old> -> <new> provider=<provider>` the same way, from each message's
`model` and `provider`, where `<model>` is the model that served the
turn: Crush's `prism_model_id` for a Hyper Prism turn, else `model`.
Since 0.19.0 the row ends with ` requested=<model>` when the requested
`model` differs from the served one, and the `model` column reads
`<provider>/<served model>`, or the served model alone when no provider
is recorded. It writes no permission rows, because Crush
records no permission state the research names.
The `opencode` and `kilo-code` parsers write, after a database's
session-start rows, `session synced: share <id> url <url> (from
<database> session_share, time_created)` for each session published to
the share service, at the share's creation time; for a session with no
`session_share` row whose `session.updated.1` events record a share URL
(one shared and then unshared), `session synced: share url <url> (from
<database> event session.updated.1, info.time.updated)` at the first
event that names it and `session unshared (from <database> event
session.updated.1, info.time.updated)` at the first later event without
it, `<database>` being the file name (`opencode.db`, `kilo.db`). The
`kilo-code` parser also writes `session synced: kilo session <id> ingest
<ingestPath> share <url> (from storage/session_share/<sessionID>.json,
file mtime)` for each Kilo cloud session marker, at the file's
modification time, `-` for an absent value.

The pi session reader (the `pi` parser, the little-coder sessions in
pi's directory, which stay agent `pi`, and Letta's local-backend
`messages.jsonl`) and the `openclaw` parser write `model: <id>
provider=<provider>` at the first entry of a session that names a model
and `model: <old> -> <new> provider=<provider>` on each change, with
` requested=<model>` when an assistant message's `responseModel` (the
model the provider reported) differs from its `model` (the one asked
for); a `model_change` entry is one of those entries, and one that
names the model already in force, being the user's own switch, still
gets the plain `model: <id> provider=<provider>` row; for `openclaw`
the `session_windows` `model` and `model_provider` start the session at
its start time. `openclaw` writes `session synced: public share <id>
generation <sessionId> (from openclaw-agent.sqlite
session_nodes.entry_json, publicShare.createdAt)` after the start row of
a session published through the Gateway's public link, at the time
access was turned on, and one `backup uploaded: <kind> to <location or
archive path> key <object key or commit> namespace <namespace> (from
state/openclaw.sqlite backup_runs, created_at)` row, with an empty
`session_id`, per successful `openclaw backup` run that uploaded the
state directory to a storage location or committed it to a Git backup
repository whose push did not fail. The `letta` parser adds the same row
after the first
`.letta/sessions.jsonl` line of each CLI session and a change row when a
later line of the session names another model. The `pi` parser reads
`.pi/agent/trust.json`, the project trust decisions pi and little-coder
share, as one `permission setting: <path>=<true|false> (from
.pi/agent/trust.json, file mtime)` row per project, with `project_path`
the project, the file's modification time and an empty `session_id`.
For a `/bug` report recorded in a session, the `pi` parser writes
`session synced: bug report <id> uploaded to radius.pi.dev
transcript=<true|false> summary=<true|false> (from session entry
pi.bug-report, entry timestamp)` when it was uploaded and `bug report
exported: <id> path=<path> (from session entry pi.bug-report, entry
timestamp)` when it was written to a zip, at the entry's time.
The `letta` parser writes `session synced: server conversation
<conversation id> agent <agent id> server <server> (from
.letta/transcripts path, first captured_at)` before the first row of
each transcript whose agent id does not start `agent-local-`, at that
line's time, `<server>` the agent's `baseUrl` in `.letta/settings.json`,
`api.letta.com` when it has none and `-` when the file has no entry
for the agent; and `session synced: last session on <server> agent
<agentId> conversation <conversationId> (from <file>, file mtime)` for
each `sessionsByServer` entry of `.letta/settings.json` and of a
project's `.letta/settings.local.json` that is not the local backend's,
at the file's modification time, with the conversation as `session_id`.

The `cline`, `continue` and `pearai` parsers write the same `model:`
rows, with the `model` column the new model. Cline's SDK sessions write
`model: <id> provider=<provider>` after the session start (or
`sessions.db` index) row, from the manifest's `model` and `provider`, and
`model: <old> -> <new> provider=<provider>` before a message whose
`modelInfo.id` differs; its legacy tasks write `model: <model_id>
model_provider_id=<id> mode=<mode>` and `model: <old> -> <new> ...` from
the `model_usage` entries of `task_metadata.json` at each entry's time,
and `permission mode: <mode>` and `permission mode: <old> -> <new>` from
the same entries' `mode`. Continue writes `model: <chatModelTitle>` after
the session row and `model: <old> -> <new>` before a history item whose
`promptLogs[].modelTitle` differs; PearAI's chat sessions write
`model: <id>` and `model: <old> -> <new>` from each item's
`promptLogs[].completionOptions.model`. These rows inherit the session's
time like every other row of a Continue or PearAI session. Continue
also writes per-call decisions with the call's `tool_use_id` and
`tool_name`: `permission decision: accepted=<accepted>` after each
`dev_data` `toolUsage.jsonl` record's `tool_result` row, at the record's
time and with an empty `session_id` (the record names none), and
`permission decision: canceled reason=user` (the CLI's `Permission
denied by user`), `permission decision: canceled reason=policy`
(`Command blocked by security policy`) or `permission decision:
canceled` after a session tool call whose `toolCallStates[]` status is
`canceled`, and `permission decision: errored reason=policy` after an
`errored` one whose output is the extension's `Security Policy
Violation`, at the session time. A Continue session with a `mode`
writes `permission mode: <mode>` after its `model:` row, and one whose
`workspaceDirectory` ends in `cn-review-<digits>-<digits>` writes
`scratch directory: <workspaceDirectory> (cn review worktree)`, both
at the session time. Each rule of the CLI's `.continue/permissions.yaml`
is `permission setting: <list>=<rule> (from .continue/permissions.yaml,
file mtime)`, `<list>` being `allow`, `ask` or `exclude`, at the file's
modification time; a file in any other YAML layout is one `parser:
unsupported YAML at line <N> (only allow, ask and exclude lists of
strings are read)` row. Each `dev_data` `editOutcome.jsonl` line is
`permission decision: edit accepted=<accepted> file=<filepath> lines
<previousCodeLines> -> <newCodeLines>`, each `editInteraction.jsonl`
line `edit interaction: file=<filepath>` before its prompt (`user`) and
edited file (`assistant`), and each `chatFeedback.jsonl` line `chat
feedback: feedback=<true|false|-> model=<modelTitle>` after its prompt
and reply, all at the line's time and with `-` for an absent value. A
Cline
SDK session whose metadata has the `enterprise.blobUpload` key gets
`session synced: enterprise prompt upload to <adapterType> bucket
<bucket> object sessions/<userDistinctId or unknown>/<session_id>/messages.json
endpoint=<endpoint> region=<region> account=<accountId> (from
<session_id>.json metadata enterprise.blobUpload, started_at)` after its
`model:` row, at the session's start and with `-` for an absent value,
or the same row ending `(from sessions.db sessions.metadata_json
enterprise.blobUpload, started_at)` for a session known only from
`sessions.db`; each item of the VS Code extension's upload queue
`cache/sync-queue.json` is `enterprise prompt upload <status> key
<key> retries <retryCount> (from
saoudrizwan.claude-dev/cache/sync-queue.json, item timestamp)`, prefixed
`session synced: ` only when `<status>` is `synced` (a `pending` or
`failed` item has not reached the bucket), with the item's `taskId` as
`session_id`, at the item's time. A Cline SDK tool result for a call
the runtime did not run is followed by `permission decision: rejected
reason=<reason>` when the reason ends with the runtime's `-- NOT a tool
or system failure. Clarify with user before proceeding.` (written
without it), or `permission decision: blocked reason=<reason>` for
`Tool "<name>" is disabled by policy` and `Tool <name> was blocked by a
runtime hook`, with the result's `tool_use_id`, `tool_name` and time.
Cline's standing settings are one `permission setting: <key>=<value>
(from <file>, file mtime)` row each, at the file's modification time:
`autoApprovalSettings.enabled`, `.maxRequests`, `.favorites` (per entry)
and `.actions.<name>` and `mode` from `.cline/data/globalState.json`;
`toolAutoApprove`, `planActMode`, `disabledTools`, `disabledPlugins` and
`disabledAgentPlugins` (per entry) and `tools.<name>.enabled` from
`.cline/data/settings/global-settings.json`; and
`mcpServers.<name>.autoApprove` (per entry) and
`mcpServers.<name>.disabled` from `settings/cline_mcp_settings.json`.
Each Cline Cloud session in `globalState.json` `cloudSessionStatuses`
gets `session origin: remote cline-cloud session <id> status <status>
(from .cline/data/globalState.json cloudSessionStatuses, observedAt)`
and `session synced: cline-cloud holds session <id>, no local transcript
(from ...)` at its `observedAt`, with the id as `session_id`, and each
record of a `.cline/data/cloud-pending-starts/*.json` file the same pair,
the origin row reading `sandbox start pending account=<account>
endpoint=<endpoint>`, at the file's modification time, so such a session
has `origin` `remote` and `synced` `yes`; every other Cline session has
`origin` `local`. The `cloudTaskTarget` is `cloud task target:
target=<target> repository_id=<id> branch=<branch> (from
.cline/data/globalState.json, file mtime)`. A Cline session imported
from another agent names it on its start row: `imported_from=<tool>
imported_session=<id> imported_path=<path> imported_at=<time>
imported_provider=<provider> imported_model=<model>`. The hook audit log
`.cline/data/logs/hooks.jsonl` gives a `hook audit: <hookName> ...` row
for each `agent_start`, `agent_abort`, `agent_error` and
`session_shutdown` line, with `cline_version=`, `user=`, `agent=`,
`parent_agent=`, `reason=`, `pid=`, `source=` and `error=<name>:
<message>` when present. Continue's `.continue/logs/cn.log`, and the `cn<N>.log`
files it is rotated to, give `agent metadata posted: agent <agentId>
keys <metadataKeys> <status> (from logs/cn.log, log line time,
host-local)` for each metadata post of `cn serve --id`, `<status>`
being `Success`, `Unexpected response`, `Auth required`, `Failed`,
`Error` or `-` when no result line follows, and `storage upload
requested, skipped (from logs/cn.log, log line time, host-local)`, and
for each rule a "don't ask again" answer added to `permissions.yaml`
`permission decision: allow always rule=<rule> (from logs/cn.log, log
line time, host-local)`, all with an empty `session_id` and the log's
host-local time written as if it were UTC. `roo-code`,
`shellgpt` and `tabby` record no model and write no such row.

The `aider` parser reads the announcement lines Aider writes to
`.aider.chat.history.md` at startup and after each `/model`,
`/weak-model`, `/editor-model` or `/chat-mode` switch, and after the
`tool_result` row of the blockquote run that holds them writes
`model: <name>` at a session's first announcement and `model: <old> ->
<new>` on each later one that names another main model, the same text
followed by ` (editor model)` or ` (weak model)` for those two roles,
with the new model in the `model` column; a `Model:` line, which means
no separate weak model, sets the weak model to the main one without a
row unless it replaces a separate weak model. Each confirmation line
is `permission decision: <decision> (<question>) answer=<letter>
default=<default>` after the same kind of `tool_result` row, with
`<decision>` `yes`, `no`, `all`, `skip all` or `no, don't ask again`;
a `y` or `n` answer ends `; may be automatic (--yes-always)`, because
Aider writes the same line when `--yes-always` answers for the user.
Both take the run's time, a session header's or the last prompt's.

The `vscode`, `cody` and `twinny` parsers write the same `model: <id>`
and `model: <old> -> <new>` rows, from the request `modelId` (VS Code),
the assistant message `model` (Cody, per chat) and `meta.model` (Twinny,
per conversation), before the rows of the request or message that
names the model. VS Code also writes `permission mode: <mode>` and
`permission mode: <old> -> <new>` from the request's chat mode (`ask`,
`agent`, `edit`, `custom`). Per-call decisions are `permission
decision:` rows. In VS Code, a tool call's confirmation follows its
`tool_result` row with the call's `tool_use_id`: `permission decision:
confirmed=true` or `confirmed=false` (before VS Code 1.104), else
`confirmed=<kind>(<number>)`, one of `Denied(0)`,
`ConfirmationNotNeeded(1)`, `Setting(2)`, `LmServicePerTool(3)`,
`UserAction(4)` and `Skipped(5)`, followed by that record's `source`,
`id`, `scope`, `selectedButton` or `selectedButtonKind`, the tool's
origin as `tool_source=<type>` and any `reason` last. A question put to
the user in the chat is `permission decision: confirmation
isUsed=<true|false> buttons=<list> title=<title>` with its message on
the next line, and the request that answering it sent is followed by
`permission decision: confirmation=<button label>`. Cody's confirmation
steps are `permission decision: <decision> confirmation state=<state>
error=<message> title=<title>`, the parts the step lacks left out, with
the step's description and content on the next lines. Since 0.19.0
`<decision>` is `rejected` for a step the user refused (saved as state
`error` with the message `Command rejected`) and `approved or
unanswered` for a `pending` step, because Cody saves an approval and an
unanswered request the same way; any other step reads `permission
decision: confirmation state=<state> ...` with no separate decision
word. Cody's standing settings in the editor's `User/settings.json` are
`permission setting: <key>=<value> (from <file>, file mtime)` rows, one
per leaf of `cody.agentic.context.experimentalOptions` (such as
`cody.agentic.context.experimentalOptions.shell.allow=["git"]`), for
`cody.agentic.context.experimentalShell` and `cody.chat.agenticContext`,
and for `disabled` and `disabledTools` of each `cody.mcpServers.<server>`;
its model preferences are `model setting: <selected|defaults>.<usage>=<id>
endpoint=<endpoint> (from <file>, file mtime)`, from
`JetBrains-globalState/cody-model-preferences` or, ending `(from <file>
cody-model-preferences, file mtime)`, from the `state.vscdb` row, with
the `model` column the id. Both kinds have an empty `session_id` and the
file's modification time, not the time the setting was made. A JetBrains
project's legacy `.idea/cody_history.xml` gives, per chat, `chat:
<internalId> | account=<accountId> | messages=<n> (legacy JetBrains
history)`, `model: <id>` before the first assistant message, and the user
and assistant rows, with the chat's `updatedAt` as `session_id` and time
and the project as `project_path`. VS Code's session-start row ends with `workspace=<path>` when the
chat's workspace is a `.code-workspace` file (since 0.19.0); the
`project_path` is the session's `workingDirectory`, else the
workspace's folder, never that file. Twinny's tool steps saved while waiting for the user's Run or
Skip, or skipped, are `permission decision: waiting` and `permission
decision: skipped`, each with ` approval=<command|change>` when the
step records what was asked, after the step's `tool_result` row with
its `tool_use_id`.
The `vscode` parser writes `session synced: remote session
<cloudSessionId> task <cloudTaskId> (from
User/globalStorage/github.copilot-chat/cloudSessions.json, file mtime)`
for each chat session Copilot Chat's session sync uploaded to the
user's GitHub account, with the chat session id as `session_id` and the
file's modification time, and `session synced: cloud agent task
<taskId> application=<application> (from state.vscdb
GitHub.copilot-chat github.copilot.cloudAgent.ownedTasks, recordedAt)`
for each cloud agent task started from the editor, with `session_id`
`copilot-cloud-agent:/task/<taskId>`, at the time it was recorded; `-`
stands for an absent value. The task ran on GitHub's servers from the
start, but GitHub holds its copy as it does an uploaded session's, so
its session's `synced` in `sessions.jsonl` is `yes`. A second row at
the same time and session, `session origin: remote GitHub cloud agent
(from state.vscdb GitHub.copilot-chat
github.copilot.cloudAgent.ownedTasks, recordedAt)`, records where it
began, so its `origin` is `remote`.

The `chatgpt-desktop` parser reads the ChatGPT desktop app's list of
the account's ChatGPT conversations, the `chatgpt` rows of
`.codex/sqlite/codex-dev.db` `local_thread_catalog`, which the app
writes at sign-in; a conversation's text stays on OpenAI's servers and
is not on disk. Per conversation it writes three `system` rows with the
conversation id as `session_id`, at the row's `source_updated_at`:
`account conversation: <title> origin=<conversation_origin>
created=<UTC> updated=<UTC> host=<host_id> (from
.codex/sqlite/codex-dev.db local_thread_catalog)`, where `host_id` is
`chatgpt:<workspace uuid>:<user id>` and `-` stands for an
absent value; `session origin: remote chatgpt.com conversation <id>
(listed at sign-in; its transcript is server-side)`; and `session
synced: chatgpt.com holds conversation <id>, no local transcript`. Such
a session's `origin` is `remote`, its `synced` `yes`, and its turn
counts 0. The update time is the conversation's as of sign-in: a reply
from inside the app did not change it.

The `cursor` parser writes `session origin: remote cursor cloud agent`
for a Cursor cloud agent, which runs on Cursor's servers, with the
agent's `bc-<id>` as `session_id` and its repository
(`github.com/<owner>/<repo>`) as `project_path`: at the cached
conversation's `updated_at` when `conversation-search.db` holds one for
the agent, else at the agent's `createdAt` from the
`cloudAgentRepository.agents.<account>` list in `state.vscdb`. Beside it,
at the agent's `createdAt`, `session synced: cursor cloud agent <bcId>
(vendor copy; from state.vscdb cloudAgentRepository.agents)` records
that Cursor holds the conversation. The
session also has `model: <model>` (with ` requested=<id>` when the
requested model id differs), `source host: github.com <owner>/<repo>
(cloud agent)`, `cloud agent: <name> repo=<repoUrl> status=<status>
workflowStatus=<workflowStatus> archived=<isArchived> killed=<isKilled>
vmStarted=<hasStartedVm> (from state.vscdb cloudAgentRepository.agents,
rowUpdatedAtMs)` and, when the search index holds its text, `cached
conversation text (conversation-search.db, source=cloud-cache): <text>`,
one `system` row because the index runs the prompt and the reply
together; when the user answered the agent's request to authorise an
MCP server, the session also has `permission decision: <userDecision>
mcp auth for cloud agent <bcId> tool_call=<toolCallId> (from state.vscdb
cloudAgentRepository.mcpAuthResolution, file mtime)`, with the tool call
id as `tool_use_id`. Its `origin` is `remote` and its `synced` `yes`; every other
Cursor session's `synced` is `no`, since the editor records no sync of a
local conversation.

The `zed`, `goose`, `kiro`, `hermes` and `ollama` parsers write model rows
in the same form. `zed` writes `model: <model> provider=<provider>` once
per thread, after the thread-start row, since a thread blob keeps one
model. `goose` writes `model: <model_name> provider=<provider_name>` after
each session's start row and `model: <old> -> <new> provider=<provider>`
before a message whose recorded model differs, with
` requested=<requestedModel>` when the resolved model is another id.
`kiro` writes `model: <id>` and `model: <old> -> <new>` before the rows of
the history entry whose `request_metadata.model_id` names it, ending
` source=model_info` or ` source=model` when the entry had none and the
conversation-level field stood in. `hermes` writes them from the
`session_model_usage` table at each model's first use, with
` provider=<billing_provider>`, or one `model: <id>` from the session row
at its start. Since 0.19.0 a switch made in the Hermes TUI or desktop
app, stored as a message with `display_kind` `model_switch`, is also a
row `model: <old> -> <new> provider=<provider>` at the switch time,
`<old>` being the previous switch's model, else the last model the
`session_model_usage` table first saw before it; `model: <new>` when
neither is known, and `model_switch: <text>` when the stored message
does not parse. Such a switch can therefore appear twice, once from the
stored message and once from the usage table at the model's first use.
`ollama` writes them before the assistant message whose
`model_name` names the model. `goose` also writes
`permission mode: <goose_mode>` after each session's start row, and,
for a session the gateway relayed through its Telegram bot, `session
relayed: gateway <platform> user <user_id> display <display name> (from
sessions.db session_type gateway, created_at)`. `zed`
writes one `permission setting: <key>=<value> (thread blob, as of
updated_at)` row per grant the user gave for the rest of a thread
(`profile`, each `sandbox_grants.write_paths` and `network_hosts` entry,
and each `sandbox_grants` escape flag that is `true`): unlike the
settings-file rows these live in the thread blob, so their `session_id` is
the thread id and their `timestamp_utc` is the thread's `updated_at`, the
blob's last write rather than the time of the grant. `hermes` also
writes one `debug report uploaded: <url> (from pastes/pending.json,
expire_at minus 6 hours)` row per paste.rs link that `hermes debug
share` uploaded and that is still due for deletion, at the upload time,
with an empty `session_id`: the uploaded logs hold recent messages but
name no session.

OpenHands, Agent Zero, nanobot and Muse Code write the same kinds of row.
`openhands` writes `model: <id>` after each conversation's header row, at
the header's time, from `agent.llm.model` in `base_state.json`; a
rejected call's `tool_result` is followed by `permission decision:
rejected rejection_source=<source> <reason>` with the call's `tool_name`
and `tool_use_id`, and an action's `tool_use` text ends with
` security_risk=<value>` when the event has one. `agent-zero` writes
`model: <id>` before an agent's first reply and `model: <old> -> <new>`
on a change, tracked per chat and agent number, with ` agent=<n>` for a
subordinate agent. After the chat start row, at the file's modification
time, it also writes `session synced: provider response <response_id>
previous <previous_response_id> model <provider_model_key> (<n> response
ids) agent=<n> (from chat.json agents[].data.responses_state, file
mtime)` for each agent that chained a turn on a response the provider
stored, and for a chat carried by a messaging plugin `session relayed:
telegram bot <bot> chat <chat id> user <user id> @<username>`,
`session relayed: whatsapp chat <chat id> number <number>` or `session
relayed: email thread <thread id> from <sender>`, each ending `(from
chat.json data, file mtime)`. After those, at the file's modification
time and holding the latest value only, an editor (ACP) session gives
`permission mode: <acp_mode> (acp, as of file mtime)`, `model: requested
<acp_model_id> (acp, as of file mtime)` and `scratch directory:
<workdir_path> (acp container transport, from chat.json
data.workdir_path, as of file mtime)`, whose `project_path` is that
directory, while the chat's other rows carry the editor's workspace
`acp_cwd` as their `project_path`; a model chosen for the chat gives
`model: requested preset <name> (chat override, as of file mtime)`, or
`model: requested chat=<provider>/<name> utility=<provider>/<name> (chat
override, as of file mtime)` for a custom choice, never its API key. A
`warning` log item that records a permission decision is followed, at its
time, by `permission decision: blocked tool=<name> profile=<profile>`
(with `tool_name`), `permission decision: denied automatically (provider
MCP approval request)` or `permission decision: <clarify, passed or
terminated> (infection check)`. Standing settings are `permission
setting: tool_access.<key>=<value>`, `permission setting:
orchestrator.<cli>.<key>=<value>` and `permission setting:
<infection_check|orchestrator>=<enabled|disabled>`, each followed by
` profile=<profile>` and ` project=<name>` when the file is scoped and
ending `(from <file>, file mtime)`, with an empty `session_id`. The
scheduler's `tasks.json` gives `scheduled task: <name> type=<type>
state=<state>` at the task's `created_at` and, for a failed run,
`scheduled task failed: <error>` at `last_run`; the Telegram chat map
gives `session deleted: telegram bot <bot> chat <chat id> user <user id>
ctxid <ctxid> (from state.json, no chat.json in the input, file mtime)`
for a mapped chat whose `chat.json` is not in the input; and the A0 CLI
connector's `.agent-zero/.env` gives `session origin: remote agent-zero
instance <host> context <id> (from .agent-zero/.env, file mtime)` for
the last chat it used, so `agent-zero` sessions read `origin` `remote`
or `local`. `nanobot` writes `model: <preset> (preset)` after
the session start row: the value is a model preset of nanobot's
configuration, not a model id. `muse-code` writes, per session log,
`permission mode: approval=<approval> reviewer=<reviewer>
profile=<profile id>` followed by ` cause=<cause>` and
` format=<format>` from the log's permission frame,
`permission mode: security_mode=<value>`, and `permission mode: <old> ->
<new>` on a change of either; `model: <id> provider=<provider>` at the
first model a log names and `model: <old> -> <new>` on a change or a
`/model` command; `permission decision: <outcome>
kind=automated_review_completed risk_level=<r> user_authorization=<u>
status=<s> <rationale>` for the automated reviewer's verdict and
`permission decision: <decision> source=<source kind> policy_result=<p>
amendment=<a>` for the decision applied (`-` for a missing value), both
at the record's place in the log, before the call's `tool_result`, and
carrying the call's `tool_name` and `tool_use_id`; and one
`permission setting: projects.<path>.decision=<decision> (from
.config/muse/trust.json, file mtime)` row per trusted project, with
`project_path` the project, the file's modification time and an empty
`session_id`.

The `claude-code` decision row also ends with
` toolDenialKind=<value> userFeedback=<text>` when the same line records
either key, each printed as recorded and `userFeedback` last because it
is free text; a line with either key and no `permissionDecision` yields
`permission decision: - source=- reason=- toolDenialKind=<value>`. The
`claude-desktop` parser writes `model: <id>` from each audit log's
`system` `init` line and `model: <old> -> <new>` when an `assistant`
line's model changes, from every audit log whether or not the session's
transcript exists; a `model_refusal_fallback` line, whose fields are not
recorded, is `model_refusal_fallback: <compact JSON of its fields>`. A
Cowork session record adds one `permission grant: <key> <entry>`,
`permission grant: <key>.<member>=<value>` or `permission grant:
<key>=<value>` row, with the same `(as of <field>)` time, per entry of
`approvedToolNames`, `webFetchAllowedUrls`, `egressAllowedDomains`,
`userApprovedFileAccessPaths`, `enabledMcpTools` and
`fileDeleteApprovedMounts`. A scheduled task's row ends with
` permission_mode=<permissionMode> model=<model>` (`-` when absent) and
carries the task's model in the `model` column. Each folder in
`remote-session-spaces.json` is `permission setting:
entries.<sessionId>.folders=<folder> (from <file>, file mtime)`, with
`project_path` the folder and `session_id` empty, because the
`<sessionId>` there is the server-side id of a remote Cowork session.

### Secondary sources

Many agents keep a second copy of some of their events beside their
transcript store: a per-prompt history file, a mirror or projection of
the transcript, a full-text index, a backup or snapshot of the store, a
copy kept by a reset, a compaction or a repair. The table below names
them for each agent. The analyzer parses every source on every run,
even when the matching transcript exists, because a copy can survive
the transcript's deletion, and keeps each event once: a row from a
secondary source is dropped when a row from the agent's primary store has

- the same `host`, `user`, `agent`, `turn_type` and `text`; two
  `tool_use` or two `tool_result` rows that both carry a `tool_use_id`
  match on the same `tool_use_id` instead, and never on text when the
  ids differ, because a mirror can record a call in another form than
  the transcript does (Codex CLI's `thread_history_1.sqlite` holds the
  parsed command, the rollout the model's arguments) and a call id is
  unique within a session; a tool row without an id matches on text;
- the same `session_id`, when the secondary row has one; when it has
  none, the same `project_path` (whatever the primary row's
  `session_id`), when it has one; when it has neither, as a text-only
  prompt history does, any primary row of that host, user and agent;
- when the secondary row has a `timestamp_utc`, a `timestamp_utc` on the
  primary row too, at most the source's tolerance apart, the bound
  included; when the secondary row has none, no time constraint, so it
  matches on text and scope alone. A secondary row with a timestamp never
  matches a primary row without one.

The tolerance is per source: 2 seconds, except for the sources that
stamp an event later than the primary store does, whose wider window the
table below gives.

Matching is one-to-one. The secondary rows with a timestamp go first, in
timestamp order, each matched to the nearest primary row within its
tolerance that no earlier secondary row took, so a transcript cut after
three of five identical prompts keeps two of the five history lines.
Then the secondary rows with no timestamp go, those with a `session_id`
first, then those with only a `project_path`, then those with neither,
each group in input order, each matched to the earliest-timestamped
primary row still untaken (primary rows with no timestamp last, in input
order); taking them second keeps an undated row from claiming the
primary row a timestamped one pairs with, and taking the most specific
first lets a session's copy, not a text-only history line, take the
primary row. The primary row always survives, with its own `source_file`
and `source_line`.

Last, the secondary rows that no primary row took are matched against
the other secondary rows, one-to-one, under the same rule (the tolerance
of the row being tested), and a row that matches is dropped and counted
with the others. Its candidates are every secondary row a primary row
took, so a third copy of a primary event collapses onto the copy that
took it and only the primary row is left, and every secondary row tested
before it: the rows with a timestamp in timestamp order, then those with
none in input order. The copy kept of several is therefore the earliest
one with a timestamp, and a copy with no timestamp matches one with a
timestamp, with no time constraint, rather than the reverse. In this pass
only, a row that finds no candidate under its own scope tries the
broader ones, its `project_path` when it has one and then any scope, so
Antigravity's history line (a project, no session) and its brain mirror
line (a session, no project) of the same prompt meet; under a broader
scope a candidate whose `session_id` or `project_path` differs from one
the row records is never taken, so the same prompt typed in two sessions
stays two events. The copies of one event that several backups,
snapshots, archives or mirrors keep are thus shown once, even after the
primary store is gone. A row matches only a row from a different
`source_file`, so two identical prompts in one history file, with a
timestamp or without, are both kept as the two events the file records.
A `system` row whose text starts with `parser:` is never dropped and
never takes a copy, since it describes its own `source_file` (unreadable,
cut off, or holding an unparseable line), so a history file and a
transcript that fail with the same message are two problems, not one
event.

A secondary row with no match is kept, which recovers a prompt whose
transcript was deleted, excluded by size or truncated, and a prompt the
transcript no longer holds (a Gemini CLI rewind). The rule runs after
`--agent` and before `--since`, `--until` and `--match`, and the rows it
drops are counted per agent on the `dropped:` line of stdout and under
`deduplicated` in [inventory.json](#inventoryjson). Before analyzer
0.13.0 both rows were written. Since analyzer 0.15.0 every secondary
event row kept is marked `recovered` `yes` in `timeline.jsonl`; a
`system` row of a secondary source is not, since it describes the
source or the session rather than a lost turn. A parser whose primary
and secondary copies live in one file pairs them itself and marks the
event rows it took from the secondary copy `recovered` `yes` in the same
way: since 0.19.0 the `opencode` parser reads the 1.x
`message` and `part` tables of a database upgraded to OpenCode 2.0 only
for a session its `session_message` table does not hold, matched exactly
on the session id. [`sessions.jsonl`](#sessionsjsonl)
`recovered` says whether a session was rebuilt from such rows alone
(`yes`) or in part (`partial`):
`jq -c 'select(.recovered == "yes")' out/sessions.jsonl` lists the
sessions whose primary transcript is gone. Two cases read `partial` or
`yes` without anything lost. Deduplication matches on text, so a
secondary source that records an event in another form than the primary
store (an index that compresses a tool call into one line) keeps that
row, and its session reads `partial`: `partial` marks a session to
compare against its secondary sources, not proof that the transcript
was cut. And Letta's server backend keeps the store of record on the
server, so the local transcript is its mirror, a secondary source, and
a server-backend Letta session reads `yes` or `partial` by design,
beside its `session synced: server conversation` row.

| Agent | Secondary source | Primary store |
| --- | --- | --- |
| `agent-zero` | `usr/scheduler/tasks.json` of the install directory or volume (each task's prompt, with no timestamp, matches on text within the task's chat; its last result is stamped when the run ends: a 60-second window); the Telegram plugin's `usr/plugins/_telegram_integration/state.json` (only `system` rows, for a mapped chat that is gone) | `usr/chats/<ctxid>/chat.json` |
| `aider` | `.aider.input.history` and `.aider.llm.history`, in a home or a repository | `.aider.chat.history.md` beside them |
| `antigravity` | `.gemini/antigravity-cli/history.jsonl`; the brain mirror `.gemini/<dir>/brain/<uuid>/.system_generated/logs/transcript_full.jsonl`, else its chunks, else `transcript.jsonl`, else its chunks, `<dir>` each of `antigravity-cli`, `antigravity`, `antigravity-ide` and `antigravity-backup` (600 seconds: the mirror records a step's start, the database row its completion) | `.gemini/<dir>/conversations/<uuid>.db` |
| `claude-code` | `.claude/history.jsonl` (and `.claude-<name>/history.jsonl`) | `.claude/projects/<slug>/*.jsonl` and its subagent files |
| `claude-desktop` | each Cowork session's `local-agent-mode-sessions/<acct>/<org>/[agent/]<session dir>/audit.jsonl` under the app-data directory; the session records `local_<uuid>.json` beside the session dirs and under `claude-code-sessions/` (a Cowork record's first prompt has no timestamp: matches on text within the session) | the session dir's `.claude/projects/<slug>/*.jsonl` and its subagent files |
| `cline` | `.cline/data/db/session-search.db` (no timestamp per message: matches on text and session; a message of content blocks keeps their type names and tool ids, so only plain-string prompts match); `.cline/data/cache/user_input_history.jsonl` (only the last line timestamped: the others match on text alone); `.cline/data/logs/hooks.jsonl` (tolerance one hour; tool rows match on the call id) | `.cline/data/sessions/<id>/<id>.messages.json` |
| `cody` | a JetBrains project's `.idea/cody_history.xml`, the pre-agent plugin's history (the migration's chat id `updatedAt` as session and time; complete pairs match the migrated chat, an unpaired message is recovered) | the `sourcegraph.cody-ai` row of the editor's `state.vscdb` and `Cody-nodejs/[Data/]JetBrains-globalState/cody-local-chatHistory-v2` |
| `codex-cli` | `.codex/history.jsonl`; `.codex/state_5.sqlite` (first prompt with no timestamp: matches on text alone); `.codex/thread_history_1.sqlite`; `.codex/.codex-global-state.json` (the desktop app's prompt history, no timestamp: matches on text within the thread); `.codex/db-backups/<folder>/state_5.sqlite` (a copy Codex set aside as corrupt, read as `state_5.sqlite`) | the rollouts under `.codex/sessions/` and `.codex/archived_sessions/` |
| `continue` | `.continue/input_history.json` (the CLI's prompt history, no session or project: matches on text at any distance in time); `.continue/dev_data/<schema>/chatFeedback.jsonl` (a rated reply's prompt and completion, stamped at the click: matches within the session at any distance in time) | `.continue/sessions/<id>.json` and the `dev_data` `chatInteraction.jsonl` lines |
| `copilot-cli` | `.copilot/session-store.db` (`turns`, the prompt and the final reply of each turn, stamped when the turn ends: a one-hour window; its `sessions` name pairs with the `workspace.yaml` row; `session_files`, `session_refs`, `checkpoints` and `forge_trajectory_events` rows the log has no copy of are always kept); `.copilot/session-state/<id>/rewind-file-snapshots/index.json` (each turn's prompt, a one-hour window); `.copilot/command-history-state.json` (no timestamp, session or project: matches on text alone); each also under the pre-XDG `.local/state/.copilot` | `.copilot/session-state/<id>/events.jsonl` and `workspace.yaml` |
| `cursor` | `.cursor/projects/<project>/agent-transcripts/<composerId>/<composerId>.jsonl`, the agent worker's copy of each conversation (a prompt is stamped to the minute in local time with its UTC offset: a 60-second window; replies and tool calls have no timestamp and match on text within the conversation; the tool calls name the tools differently from the database, so they never pair) | the editor's `User/globalStorage/state.vscdb` `cursorDiskKV` composer and bubble rows |
| `gemini-cli` | `.gemini/tmp/<slug>/logs.json` (also under `.cache/.gemini`) | `.gemini/tmp/<slug>/chats/*.jsonl` |
| `goose` | `.local/state/goose/history.txt` and `.config/goose/history.txt` (`AppData/Roaming/Block/goose/data/history.txt` on Windows; no timestamp, session or project: matches on text alone) | `.local/share/goose/sessions/sessions.db` |
| `hermes` | `.hermes/state-snapshots/<id>/state.db` (copies of `state.db`; several snapshots collapse to one copy; collected only with `--full`) and `.hermes/sessions/<id>.jsonl` (no timestamp on some lines: those match on text within the session), also under `.hermes_<suffix>`, `AppData/Local/hermes`, `profiles/<name>/` and, since 0.19.0, the root of a Docker or Podman volume | `.hermes/state.db` |
| `letta` | `.letta/transcripts/<agent>/<conversation>/transcript.jsonl` (stamped at the end of the turn: a one-hour window) | `.letta/lc-local-backend/conversations/<key>/messages.jsonl` |
| `muse-code` | `.local/share/muse/tui-history.jsonl` (no timestamp: matches on text alone) | `.local/share/muse/sessions/.../session.jsonl` |
| `nanobot` | `.nanobot*/webui/<key>.jsonl` and `<key>.segments/NNNNNN.jsonl` (tolerance 15 hours: true UTC against the session file's local time, at most 14 hours apart, plus an hour of turn); `.nanobot*/history/cli_history` (no session or project: matches on text and time); when a `sessions.sqlite3` sits in the namespace directory, the namespace's `<key>.jsonl` files and their `jsonl-backup/` copies, which the database imported (since 0.19.0) | `.nanobot*/sessions/<workspace-id>/sessions.sqlite3`, else `.nanobot*/sessions/<workspace-id>/<key>.jsonl` |
| `open-interpreter` | `.openinterpreter/history.jsonl`; `.openinterpreter/state_5.sqlite` (first prompt with no timestamp); `.openinterpreter/thread_history_1.sqlite`; `.openinterpreter/db-backups/<folder>/state_5.sqlite` | the rollouts under `.openinterpreter/sessions/` and `.openinterpreter/archived_sessions/` |
| `openclaw` | `.openclaw/agents/<id>/sessions/` copies of a transcript: the published `*.jsonl.reset.*` / `*.jsonl.deleted.*` archive files, `*.checkpoint.<uuid>.jsonl` and `*.jsonl.pre-doctor-*-repair-*.bak` (each copy's session-start row names it and is kept) | `.openclaw/agents/<id>/agent/openclaw-agent.sqlite` (`transcript_events` and the `session_transcript_archives` blobs) and the legacy `sessions/<id>.jsonl` |
| `opencode` | `.local/share/opencode/opencode-next.db`, the pre-release 2.0 database that 2.0 imports and leaves in place; in a database upgraded to 2.0, the 1.x `message` and `part` tables, read only for a session `session_message` does not hold and paired by the parser itself (since 0.19.0) | `.local/share/opencode/opencode.db` (or `opencode-<channel>.db`): `session_v2` and `session_message` |
| `qwen-code` | `.qwen/tmp/<hash>/logs.json` | `.qwen/projects/<slug>/chats/*.jsonl` |
| `roo-code` | `.roo/cli-history.json` (no timestamp, task or project: matches on text alone) | the task files under `.vscode-mock/global-storage/tasks/` and the editor's `globalStorage/rooveterinaryinc.roo-cline/tasks/` |
| `tabby` | `.tabby/ee/db.backup-*.sqlite` and `dev-db.backup-*.sqlite` (copies of the live threads and events); `.tabby/events/YYYY-MM-DD.json` (its `user` and `assistant` rows pair with `user_events`; its `system` rows name the owner by encoded id, not email, and never pair) | `.tabby/ee/db.sqlite` or `dev-db.sqlite` |

The 2 seconds cover Codex's `history.jsonl`, which records whole seconds
beside the rollouts' milliseconds, and Antigravity's history line, under
a second from the database step. Qwen Code's `logs.json` rows have no
project path and match by `sessionId` only. A known miss: a prompt the
agent queued and sent later (Claude Code queues input typed while it
works) can be minutes from its transcript record, and is then shown
twice, the history row at the time it was typed. Hermes's quick
snapshots (`state-snapshots/`) are excluded by the collector unless it
runs with `--full`, so they appear only in a full collection or loose
input.

Some sources have a wider window, because they stamp an event later
than the primary store does or more coarsely. Cursor's agent transcript
stamps a prompt to the minute, so its rows match within 60 seconds. Antigravity's brain mirror records only
when a step started, while the database rows of a response or a tool
result carry its completion, so its rows match within 600 seconds.
Letta's `transcript.jsonl` stamps every line of a turn when the turn
ends, so its window is one hour; a turn longer than that leaves its
earlier lines shown twice. Copilot CLI's session store writes a turn
when it ends, so its `turns` rows and its rewind snapshots match within
one hour, and only against an identical event of the same session.
Cline's hook audit log `logs/hooks.jsonl` stamps a tool call when it
starts or ends and the transcript stamps the message when the turn is
written, so its rows match within one hour; its call rows match on the
call id.
nanobot's WebUI transcript stamps events in
true UTC while its session files record host local time, emitted as if
UTC, so its window is 15 hours (the largest UTC offset, 14 hours, plus
an hour of turn); a WebUI row kept because no session row matched
carries true UTC, unlike every other nanobot row. Continue's two
secondary sources have a window of ten years, in effect none: its
session rows carry the session's creation time rather than the
prompt's, so a prompt history entry is later by as long as the session
ran, and a `chatFeedback` line is stamped when the user rated the reply,
any time after its `chatInteraction` line; a history entry still never
matches a session row with no time, as a session the index lost has.

Several sources record no time for an event, and their rows match on
text and scope alone: Muse Code's `tui-history.jsonl`, Goose's
`history.txt` and Roo Code's `cli-history.json` record none at all;
Claude Desktop's Cowork session record keeps its first prompt with no
time of its own; Cline's `session-search.db` records none per message,
and its CLI `user_input_history.jsonl` only on its newest line, since
every rewrite stamps every line with the time of that rewrite; Codex
CLI's and Open Interpreter's `state_5.sqlite` hold a thread's first
prompt beside the thread's creation time, which can precede the prompt,
so the prompt row has none. A row with neither a session nor a project,
such as a Goose `history.txt` line, can match a primary row of any
session of the same user, so a prompt typed in two sessions is dropped
once, against the earliest database row.

Some secondary rows never match, because the primary store has no twin
for them or renders the event differently, and are always kept: Tabby's
event-log `system` rows, which name the server user by an encoded id
where the database gives an email; Cline's `session-search.db` messages
stored as content blocks, which the index keeps with their block type
names and tool ids; a nanobot WebUI prompt whose session copy has
runtime context appended (a quoted reply, an automation template);
Claude Desktop's permission requests, responses and auto-decisions,
`result` lines and `init: cwd=... model=...` rows, which the audit log
alone records (its `model: <id>` row does match the transcript's), and
the session records' `system` rows (the session, its grants, its error);
and the session-start row each OpenClaw copy begins with, which names
the copy.

Two sources that look like second copies are primary. Ollama's
`.ollama/history` is the `ollama run` REPL's readline history, while
its `db.sqlite` holds the desktop app's chats, a different surface, so
both are parsed as primary records. little-coder's prompt history rows
carry agent `little-coder`, while its transcripts are pi sessions under
agent `pi`; the rule pairs rows of one agent only, so it cannot pair
them, and both stay. Continue's `toolUsage.jsonl` is not a secondary
source either: its event rows carry their own time
but no session or project, and the session rows they repeat carry only
the session's creation time, so a match within 2 seconds would be
chance, and both are kept.

One fallback remains: Cline's `api_conversation_history.json` is read only
when the task's `ui_messages.json` is absent, because the two record different
texts for the same turn (the API history wraps the first prompt in `<task>`
tags, and its tool calls are content blocks where the UI messages have one
JSON record per tool), so the rule could not pair them and the task's turns
would be shown twice; see [Parser plan in
`research/cline.md`](../../research/cline.md#parser-plan).

## sessions.jsonl

`sessions.jsonl` has one record per distinct `host`, `user`, `agent` and
`session_id`, built from the records of `timeline.jsonl` that have a
non-empty `session_id`; records without one belong to no session. It is
built after filtering, so it summarises the rows written. It is sorted by
`first_timestamp_utc`, then `agent`, then `session_id`, so sessions with
no timestamp come first. Its fields, in order:

| Field | Type | Meaning |
| --- | --- | --- |
| `host` | string | The `host` of the session's timeline records. |
| `user` | string | The `user` of the session's timeline records. |
| `agent` | string | The `agent` of the session's timeline records. |
| `session_id` | string | The `session_id` of the session's timeline records, never empty. |
| `project_path` | string | The first non-empty `project_path` among the session's records in timeline order, so a Windows path is in the canonical form described under [`timeline.jsonl`](#timelinejsonl); `""` when none has one. `inventory.json` counts the session under this path. |
| `first_timestamp_utc` | string | The earliest non-empty `timestamp_utc` among the session's records, `""` when none has one. |
| `last_timestamp_utc` | string | The latest non-empty `timestamp_utc` among the session's records, `""` when none has one. |
| `models` | array of strings | Each distinct non-empty `model` of the session's records, in order of first use in the timeline; `[]` when none was recorded. |
| `user_turns` | integer | The number of the session's records with `turn_type` `user`. |
| `assistant_turns` | integer | The number with `turn_type` `assistant`. |
| `tool_calls` | integer | The number with `turn_type` `tool_use`. |
| `source_file` | string | The `source_file` that contributed the most of the session's records, the first met on a tie, so a transcript wins over a one-line-per-prompt history file; `""` when no record names one. |
| `synced` | string | Whether the session is synced to a remote account, from the agent's own record of it: `yes` when one of the session's records is a `system` row whose `text` starts with `session synced:` (written by the `agent-zero`, `chatgpt-desktop`, `cline`, `codex-cli`, `copilot-cli`, `cursor`, `kilo-code`, `letta`, `open-interpreter`, `openclaw`, `opencode`, `pi` and `vscode` parsers); `no` when the agent's parser records sync state and no record carries that row; `""` when the agent's parser records no sync state, so nothing is known. A string rather than a boolean, because `false` would say the agent can sync and did not. Since analyzer 0.14.0. |
| `relayed` | string | Whether the session was carried through a messaging platform (Telegram, WhatsApp, email, a GitHub thread), which keeps its own copy of the conversation, from the agent's own record of it: `yes` when one of the session's records is a `system` row whose `text` starts with `session relayed:` (written by the `agent-zero`, `goose` and `qwen-code` parsers); `no` when the agent's parser records relay state and no record carries that row; `""` when the agent's parser records no relay state, so nothing is known. A relay is not a sync: the copy is on the platform, not in the agent vendor's account, so a session can read `yes` in both fields (an Agent Zero Telegram chat chained on a stored provider response). Since analyzer 0.15.0. |
| `origin` | string | Where the session began, from the agent's own record of it: `remote` when one of the session's records is a `system` row whose `text` starts with `session origin: remote` (written by the `vscode` parser, for a Copilot cloud agent task that ran on GitHub's servers and is only listed in the editor, and by the `chatgpt-desktop` parser, for a ChatGPT conversation the app lists from the account; since analyzer 0.20.0 also by the `cursor` parser, for a conversation whose header names an agent location other than `local`, and since analyzer 0.20.1 for a Cursor cloud agent, `session origin: remote cursor cloud agent`); `local` when the agent's parser records origin and no record carries that row; `""` when the agent's parser records no origin, so nothing is known. A remote `vscode`, `chatgpt-desktop` or `cursor` session is also `synced` `yes`, since the vendor holds its copy; since analyzer 0.20.1 every other Cursor session's `synced` is `no`. Since analyzer 0.15.0. |
| `recovered` | string | Whether the session was rebuilt from secondary sources (see [Secondary sources](#secondary-sources)): `yes` when every one of its records in `timeline.jsonl` has `recovered` `yes`, so its primary transcript is gone and only secondary sources hold it; `partial` when some do, so the primary was cut or rewound and a secondary source kept turns it lost; `no` when none does and the agent's parser reads at least one secondary source; `""` when the agent's parser reads no secondary source, so nothing is known. Computed after the filters, over the session's event records only (`system` rows left out), so a secondary source's header, record or `parser:` row never makes a complete session `partial`, and a session with no event record reads `no` or `""`. Because deduplication matches on text, `partial` also results when a secondary source records an event in another form than the primary store does (an index that compresses a tool call into one line), so it marks a session to compare against its secondary sources, not proof of a cut; and a Letta session on the server backend, whose local transcript mirrors the server's store of record, reads `yes` or `partial` by design. Since analyzer 0.15.0. |

## Compatibility

The two JSONL layouts are a compatibility contract with the analysts and
tooling that consume them. A future version may append new fields after the
existing ones, but existing fields keep their names, order, type and
meaning.
