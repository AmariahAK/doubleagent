# Output

What `detect` prints, the files `timeline` writes, and the
`inventory.json`, `timeline.jsonl` and `sessions.jsonl` schemas. Back to
the [analyzer README](../README.md).

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
[`collectors/research/shared.md`](../../collectors/research/shared.md)
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
                                                        cursor                    3          920  detect only
                                                        (shared)                  1          310
/srv/shared                              alice          (shared)                  1          120
```

Each project has one line per agent, sorted by agent, then a `(shared)`
line when it holds shared files (the files several agents read, listed
above: `AGENTS.md`, `.mcp.json`, `.github/copilot-instructions.md`),
with an empty `parser` column because no one agent owns them. The path
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
          "agent": "claude-code",
          "files": 3,
          "bytes": 4343,
          "parser": true
        },
        {
          "agent": "copilot-cli",
          "files": 1,
          "bytes": 2,
          "parser": false
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
          "parser": false
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
      "agent": "copilot-cli",
      "path": "/home/alice/.copilot/config.json"
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
sorts each home's agents. Its keys, in order:

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
| `files` | array of objects | Only with `--files`: one per attributed file, in the order the manifest lists them (the walk order in loose mode). It mirrors the manifest file by file, so a shared file (one several agents read, such as `AGENTS.md`) appears here with agent `project`. |
| `files[].user` | string | As `homes[].user`. |
| `files[].agent` | string | The attributed agent: the manifest `agent`, re-attributed from the bundled project catalog for a project file of a collection before 1.12.0; `project` for a shared file, one several agents read (`AGENTS.md`, `.mcp.json`). |
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
sources left out because a primary store records the same event (see
[Secondary sources](#secondary-sources)), with the agents that had any
in parentheses, sorted by name, and no parentheses when the count is 0:

```text
dropped:   3 duplicate rows from secondary sources (antigravity 2, claude-code 1)
dropped:   0 duplicate rows from secondary sources
```

Then come the
`agents:` line, the row count with a breakdown by agent and `turn_type`,
and the session count. The breakdown counts the rows written. The last
three line groups name the three files, one each, in this order:

```text
rows:      214 in out/timeline.jsonl
           claude-code    assistant    40
           claude-code    user         50
sessions:  6 in out/sessions.jsonl
inventory: out/inventory.json (homes, projects, counts per agent, problems)
```

`rows:` is followed by one indented line per agent and `turn_type` with
its count, sorted by agent and type, and nothing when there are no rows.
The paths are `-o` joined with the file name, as given on the command
line. The exit code is `0` when at least one row was written and `1`
otherwise; the files are written either way. Before analyzer 0.12.0
`timeline` also wrote `detect.json`, named on a `detect:` line before the
`inventory:` line; its content is now in `inventory.json` (see
[inventory.json](#inventoryjson)).

The `agents:` line is always one line. When the input holds at least one
agent it lists them in two or three groups; otherwise it reads
`none were found`:

```text
agents:    parsed: antigravity, claude-code; detected but not parsed: copilot-cli
agents:    parsed: claude-code; detected but not parsed: none
agents:    parsed: none; detected but not parsed: copilot-cli
agents:    parsed: claude-code; detected but not parsed: none; parser found no rows: antigravity
agents:    none were found
```

`parsed` names the agents that produced rows before filtering. `detected
but not parsed` names the agents in the input that have no parser (the
agents `detect` shows without one, in either table, so an agent whose only
files are in a project directory counts). `parser found no rows` names the agents
in the input that have a parser which read their files and produced no
rows, such as a data directory holding only an empty database; the group
appears only when it has an entry, and with `--agent` it counts only the
agents selected. Files with agent `project` (a project file several agents
read, see [detect](#detect)), which every parser is offered, are never
listed in any group. Each list is sorted and
comma-separated, and `parsed` or `detected but not parsed` reads `none`
when it is empty. `none were found` means the input holds no agent data,
where `detect` prints `no agent artifacts found`. Before analyzer 0.12.0
the line read `parsed <list>; detected only <list>`, with `none` for an
empty list.

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
    "copilot-cli",
    "cursor"
  ],
  "no_rows": [
    "gemini-cli"
  ],
  "homes": [
    {
      "user": "alice",
      "home": "/home/alice",
      "inferred": false,
      "agents": [
        {
          "agent": "claude-code",
          "files": 3,
          "bytes": 4343,
          "parser": true
        },
        {
          "agent": "copilot-cli",
          "files": 1,
          "bytes": 2,
          "parser": false
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
      "shared_files": 0
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
      "shared_files": 1
    },
    "/srv/shared": {
      "status": "collected",
      "rows": 0,
      "sessions": 0,
      "agents": {},
      "shared_files": 1
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
    }
  },
  "deduplicated": {}
}
```

`claude-code` is counted in three places. Under `/srv/proj` it has 7
rows and 1 session: one `history.jsonl` line and the six rows of a
session transcript whose working directory is `/srv/proj`; it has no
project files there, because its transcripts are in alice's home, where
`homes` counts its 3 files. Under
`/srv/gone`, a `referenced` project, it has one history line. Under
`outside_projects` it has the other 7 rows and 1 session: the history
line with no project and a session transcript that records no working
directory. `cursor` has project files and no parser, so no rows;
`gemini-cli` has a parser that found no rows. `deduplicated` is `{}`
because none of the three `history.jsonl` prompts is one a transcript
records, so every history line is kept. Its keys, in order:

| Key | Type | Meaning |
| --- | --- | --- |
| `input` | string | The input path, as on the `input:` line. |
| `kind` | string | As in [`detect --json`](#detect---json): `archive`, `collected` or `loose`. |
| `host` | string | The host name, `""` when unknown. |
| `notes` | array of strings | As in [`detect --json`](#detect---json): the `note:` lines without their prefix, in the order they were made; `[]` when there are none. |
| `problems` | array of strings | The `problem:` lines of `timeline` without their prefix, `<path>: <reason>`: first the problems met while the input was opened, as in `detect --json`, then each file a parser could not read, by its path on the source host. Not changed by `--since`, `--until` or `--match`; with `--agent`, only the parsers that ran add theirs. `[]` when there are none. |
| `rows` | integer | The number of records in `timeline.jsonl`, after the filters. |
| `sessions` | integer | The number of records in `sessions.jsonl`, after the filters. |
| `parsed` | array of strings | The `parsed` group of the `agents:` line: the agents that produced rows before filtering, sorted. |
| `detected_not_parsed` | array of strings | The `detected but not parsed` group: the agents in the input, outside or inside a project directory, that have no parser, sorted. |
| `no_rows` | array of strings | The `parser found no rows` group, sorted; `[]` when it is empty. |
| `homes` | array of objects | The `homes` array of [`detect --json`](#detect---json) for the same input, element for element: one per user home and Docker volume, in the order its first collected row was met, never a project directory. Not filtered. |
| `homes[].user` | string | As `homes[].user` in `detect --json`: the home's owner, `""` when unknown. |
| `homes[].home` | string | As `homes[].home` in `detect --json`: the manifest `home`, or in loose mode the path relative to the input root with a leading `/`. |
| `homes[].inferred` | boolean | `true` in loose mode, where user and home come from the path; `false` when they come from a manifest. |
| `homes[].agents` | array of objects | One per agent with files in this home, sorted by `agent`; `[]` when every file of the home is missing from the collection. |
| `homes[].agents[].agent` | string | Catalog agent name; never `project`. |
| `homes[].agents[].files` | integer | Files of this agent in this home, counted as in `detect --json`; not filtered. |
| `homes[].agents[].bytes` | integer | Their total size, the manifest `size` or the size on disk in loose mode; not filtered. |
| `homes[].agents[].parser` | boolean | `true` when the analyzer has a parser for this agent, `false` when it is detected only. |
| `projects` | object | Keyed by project path, sorted: every distinct non-empty `project_path` of the rows, and every project directory the input holds, as the collector's path with the image root removed and Windows paths in the canonical form of [`timeline.jsonl`](#timelinejsonl) `project_path` (see below). Windows paths that differ only in case are one project, keyed by the collected directory's spelling when the project is one, else by the first spelling the rows record. `{}` when there is neither. |
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
| `outside_projects` | object | The counts for the rows and sessions whose `project_path` is empty. It has no status and no file counts: files outside projects are counted per home under `homes`. |
| `outside_projects.rows` | integer | Rows with an empty `project_path`, after the filters. |
| `outside_projects.sessions` | integer | Sessions with an empty `project_path`, after the filters. |
| `outside_projects.agents` | object | Keyed by agent name, sorted: the agents with such rows or sessions; `{}` when there is none. |
| `outside_projects.agents.<agent>.rows` | integer | This agent's rows with an empty `project_path`, after the filters. |
| `outside_projects.agents.<agent>.sessions` | integer | This agent's sessions with an empty `project_path`, after the filters. |
| `outside_projects.agents.<agent>.turn_types` | object | Keyed by `turn_type`, sorted: this agent's rows of each type, listing only the types that occur. |
| `deduplicated` | object | Keyed by agent name, sorted: the agents with rows of a secondary source dropped because a primary store records the same event (see [Secondary sources](#secondary-sources)), the counts of the `dropped:` line. With `--agent`, only the agents selected; not changed by `--since`, `--until` or `--match`, which apply to the rows kept. `{}` when no row was dropped. |
| `deduplicated.<agent>` | integer | The number of this agent's secondary-source rows dropped, never 0. |

A row is counted under its own `project_path` and a session under the
session's, the first non-empty `project_path` among its rows, so a session
whose rows name two projects has rows under both and is counted once, under
the first. Rows with no `session_id` belong to no session. The `rows` of
`projects` and `outside_projects` add up to the top-level `rows`, and their
`sessions` to the top-level `sessions`. Nothing is counted twice: files
per home are under `homes`, files per project directory under
`projects`, and rows and sessions under `projects` and
`outside_projects`.

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
existing ones keep their names, types and meaning. `deduplicated`, the
last key, was added in analyzer 0.13.0.

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
| `text` | string | The event's full text, with leading and trailing whitespace removed and inner line breaks and indentation kept: the prompt, the response, the tool output, or for a tool call its most identifying argument (the Bash command, the edited file, the search pattern, the fetched URL), else the arguments as JSON. |
| `source_file` | string | Path of the record on the source host, as in the manifest. In loose mode it is the path relative to the input root with a leading `/`, or relative to the home when the input root is the home or an agent directory. |
| `source_line` | integer | Where the record is in that file, so the full record can be read. For line-oriented files (JSONL, Markdown, text) the 1-based line number. For SQLite stores it is the record's `rowid` (Tabby events: the event id), and for JSON documents an array index or `1`. Each parser's module docstring says which. `0` when no position applies. |

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
full text. A line a parser cannot decode, such as a
transcript's last line cut off mid-write, is reported as a `system` row,
and the rest of the file is still read.

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
[`antigravity` row of the parser table](parsers.md#parser-table) lists the
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
`model: <id>` at the first `turn_context` record of a rollout that names
a model and `model: <old> -> <new>` at each later one whose model
differs, and one composite `permission mode: approval=<approval_policy>
sandbox=<sandbox_policy> profile=<permission_profile> network=<network>`
row at the first `turn_context` with any of those four fields and
`permission mode: <old> -> <new>` whenever the composite changes. A
missing field is `-` and an object field is compact JSON, so a value
reads `sandbox={"type":"workspace-write"}`. Both rows take the
`turn_context` line's timestamp and precede that turn's rows, and the
`model` column of both is the turn's model. Codex records no per-call
approval in its rollouts, so these parsers write no `permission
decision:` row.

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
file's modification time and an empty `session_id`.

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
message's timestamp and `source_line` and precede its other rows. The
`crush` parser writes `model: <model> provider=<provider>` and `model:
<old> -> <new> provider=<provider>` the same way, from each message's
`model` and `provider`; it writes no permission rows, because Crush
records no permission state the research names.

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
its start time. The `letta` parser adds the same row after the first
`.letta/sessions.jsonl` line of each CLI session and a change row when a
later line of the session names another model. The `pi` parser reads
`.pi/agent/trust.json`, the project trust decisions pi and little-coder
share, as one `permission setting: <path>=<true|false> (from
.pi/agent/trust.json, file mtime)` row per project, with `project_path`
the project, the file's modification time and an empty `session_id`.

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
`permission decision: canceled` after a session tool call whose
`toolCallStates[]` status is `canceled`, at the session time. `roo-code`,
`aider`, `shellgpt` and `tabby` record no model and write no such row.

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
steps are `permission decision: confirmation state=<state>
title=<title>` with the step's description and content on the next
lines. Twinny's tool steps saved while waiting for the user's Run or
Skip, or skipped, are `permission decision: waiting` and `permission
decision: skipped`, each with ` approval=<command|change>` when the
step records what was asked, after the step's `tool_result` row with
its `tool_use_id`.

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
at its start. `ollama` writes them before the assistant message whose
`model_name` names the model. `goose` also writes
`permission mode: <goose_mode>` after each session's start row. `zed`
writes one `permission setting: <key>=<value> (thread blob, as of
updated_at)` row per grant the user gave for the rest of a thread
(`profile`, each `sandbox_grants.write_paths` and `network_hosts` entry,
and each `sandbox_grants` escape flag that is `true`): unlike the
settings-file rows these live in the thread blob, so their `session_id` is
the thread id and their `timestamp_utc` is the thread's `updated_at`, the
blob's last write rather than the time of the grant.

OpenHands, Agent Zero, nanobot and Muse Code write the same kinds of row.
`openhands` writes `model: <id>` after each conversation's header row, at
the header's time, from `agent.llm.model` in `base_state.json`; a
rejected call's `tool_result` is followed by `permission decision:
rejected rejection_source=<source> <reason>` with the call's `tool_name`
and `tool_use_id`, and an action's `tool_use` text ends with
` security_risk=<value>` when the event has one. `agent-zero` writes
`model: <id>` before an agent's first reply and `model: <old> -> <new>`
on a change, tracked per chat and agent number, with ` agent=<n>` for a
subordinate agent. `nanobot` writes `model: <preset> (preset)` after
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

From issues 96 and 97, the `claude-code` decision row also ends with
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

Some agents keep a per-prompt history file beside their transcript store,
and the same prompt is then recorded in both. The analyzer parses every
source on every run, and keeps each event once: a row from a secondary
source is dropped when a row from the agent's primary store has

- the same `host`, `user`, `agent`, `turn_type` and `text`;
- the same `session_id`, when the secondary row has one; when it has
  none, the same `project_path` (whatever the primary row's
  `session_id`), when it has one; when it has neither, as a text-only
  prompt history does, any primary row of that host, user and agent;
- when the secondary row has a `timestamp_utc`, a `timestamp_utc` on the
  primary row too, at most the source's tolerance apart, the bound
  included; when the secondary row has none, no time constraint, so it
  matches on text and scope alone. A secondary row with a timestamp never
  matches a primary row without one.

The tolerance is per source: 2 seconds for every source in the table
below; a parser whose source stamps an event later than the primary store
does may widen it, and the table then says so.

Matching is one-to-one. The secondary rows with a timestamp go first, in
timestamp order, each matched to the nearest primary row within its
tolerance that no earlier secondary row took, so a transcript cut after
three of five identical prompts keeps two of the five history lines.
Then the secondary rows with no timestamp go, in input order, each
matched to the earliest-timestamped primary row still untaken (primary
rows with no timestamp last, in input order); taking them second keeps
an undated row from claiming the primary row a timestamped one pairs
with. The primary row always survives, with its own `source_file` and
`source_line`.

Last, the secondary rows that no primary row took are
matched among themselves in input order under the same rule (the
tolerance of the row being tested), one-to-one, and a row that pairs
with an earlier one is dropped and counted with the others, so the
copies of one event that several backups or snapshots keep after the
primary store is gone are shown once, as the first copy. A row pairs
only with an earlier row from a different `source_file`, so two
identical prompts in one history file, with a timestamp or without, are
both kept as the two events the file records.

A secondary row with no match is kept, which recovers a prompt whose
transcript was deleted, excluded by size or truncated, and a prompt the
transcript no longer holds (a Gemini CLI rewind). The rule runs after
`--agent` and before `--since`, `--until` and `--match`, and the rows it
drops are counted per agent on the `dropped:` line of stdout and under
`deduplicated` in [inventory.json](#inventoryjson). Before analyzer
0.13.0 both rows were written.

| Agent | Secondary source | Primary store |
| --- | --- | --- |
| `antigravity` | `.gemini/antigravity-cli/history.jsonl` | `.gemini/antigravity-cli/conversations/*.db` |
| `claude-code` | `.claude/history.jsonl` (and `.claude-<name>/history.jsonl`) | `.claude/projects/<slug>/*.jsonl` and its subagent files |
| `claude-desktop` | each Cowork session's `local-agent-mode-sessions/<acct>/<org>/[agent/]<session dir>/audit.jsonl` under the app-data directory | the session dir's `.claude/projects/<slug>/*.jsonl` and its subagent files |
| `codex-cli` | `.codex/history.jsonl` | the rollouts under `.codex/sessions/` and `.codex/archived_sessions/` |
| `gemini-cli` | `.gemini/tmp/<slug>/logs.json` (also under `.cache/.gemini`) | `.gemini/tmp/<slug>/chats/*.jsonl` |
| `muse-code` | `.local/share/muse/tui-history.jsonl` (no timestamp: matches on text alone) | `.local/share/muse/sessions/.../session.jsonl` |
| `open-interpreter` | `.openinterpreter/history.jsonl` | the rollouts under `.openinterpreter/sessions/` and `.openinterpreter/archived_sessions/` |
| `qwen-code` | `.qwen/tmp/<hash>/logs.json` | `.qwen/projects/<slug>/chats/*.jsonl` |

The 2 seconds cover Codex's `history.jsonl`, which records whole seconds
beside the rollouts' milliseconds, and Antigravity's history line, under
a second from the database step. Muse Code's `tui-history.jsonl` records
no time, so its rows match a session row of the same session on text
alone. Qwen Code's `logs.json` rows have no project path and match by `sessionId` only. A
known miss: a prompt the agent queued and sent later (Claude Code queues
input typed while it works) can be minutes from its transcript record,
and is then shown twice, the history row at the time it was typed.
Continue's `toolUsage.jsonl` is not a secondary source: its event rows
carry their own time but no session or project, and the session rows
they repeat carry only the session's creation time, so a match within 2
seconds would be chance, and both are kept.

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

## Compatibility

The two JSONL layouts are a compatibility contract with the analysts and
tooling that consume them. A future version may append new fields after the
existing ones, but existing fields keep their names, order, type and
meaning.
