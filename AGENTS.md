---
title: "Contributing"
nav_order: 5
---
# AGENTS.md

Guidance for AI coding agents and humans working in this repository.

## Purpose

`doubleagent` is a forensic analysis tool for AI agent use on a system,
for incident responders. It has two parts: collectors that gather the
on-disk artifacts of AI agents that run on the host (Claude Code, Gemini
CLI, Antigravity, Codex CLI, Copilot CLI, Cursor, VS Code chat extensions,
Windsurf, Aider, Ollama, Hermes, Agent Zero, OpenClaw, n8n, Flowise,
Langflow, and others), for every user on a host, into one archive with a
hashed manifest; and an analyzer, the `doubleagent` Python command, that
detects agent state in a collection or any loose directory tree and parses
transcripts into a JSONL timeline. The criterion for the catalog is an agent that executes tools or
shell commands on the host and leaves transcripts, configuration or
credentials on disk; it need not be an editor or coding tool. When a new
kind of agent is added, widen the wording in the [top-level README](README.md) in the
same commit.

The project supplements the EDR a responder already has during an incident
response investigation; it never duplicates EDR features. Process lists,
logged-on users, network connections, services, scheduled tasks and shell
histories are the EDR's job and are not collected. What the collector adds is what EDR does
not see: the agents' own transcripts, configuration, credentials and project
references on disk, and the catalog that says where to find them. A proposed
feature that an EDR console already provides is out of scope, however cheap
it looks to add.

The collectors must work in three situations:

1. Remotely through an EDR remote shell (CrowdStrike RTR, SentinelOne
   RemoteOps, Defender Live Response, Palo Alto Networks Cortex XDR Live
   Terminal).
2. Locally on the host by a responder.
3. Against a mounted disk image on an analyst workstation, including Windows
   images mounted on Linux or macOS.

The collectors run on the host, with sh and PowerShell 5.1 collectors. The
analyzer, under `analyzer/`, runs on the analyst's workstation and can be
installed and used without the collectors; the
[agents table](analyzer/docs/parsers.md#agents) lists every catalog agent
with its parse status. Parsing never happens on the host.

## Repository layout

```text
collectors/
  collect-agent-artifacts.sh   the macOS/Linux/BSD collector, single POSIX sh file
  Collect-AgentArtifacts.ps1   the Windows collector, single PowerShell 5.1 file
  PSScriptAnalyzerSettings.psd1  PSScriptAnalyzer rules, including the 5.1 compatibility
                               profiles
  README.md                    collector user documentation, keep in sync with behaviour
  docs/<topic>.md              detailed collector documentation: options, output and
                               manifest schema, coverage, Docker, privileges, inventory,
                               Windows, deployment, testing, internals
  CHANGELOG.md                 collector release history, one entry per VERSION
  tests/smoke.sh               end-to-end test of the sh collector (fake disk image)
  tests/smoke.ps1              end-to-end test of the PowerShell collector
  tests/catalog-sync.sh        fails if the catalog tables differ between the scripts
                               or from the analyzer's bundled copy
  research/<agent>.md          where each agent stores state: paths, credentials,
                               exclusions, project files, discovery; one per agent
analyzer/
  doubleagent/                 Python package: cli, inputs, catalog, model, parsers/
  doubleagent/catalog.txt      verbatim copy of collect-agent-artifacts.sh --list
  research/<agent>.md          how each agent records transcripts; one per agent
  README.md                    analyzer user documentation: quick start, commands, options
  docs/<topic>.md              detailed analyzer documentation: inputs, agents table,
                               output and JSONL schema, filtering, searching, inventory,
                               options, development
  CHANGELOG.md                 analyzer release history, one entry per VERSION
  tests/                       unittest suite with synthetic fixtures; tests/run.sh
  pyproject.toml               installable as the doubleagent command
  requirements.txt             third-party dependencies (python-dateutil;
                               zstandard, for compressed transcripts)
lab/                           Docker sandbox for running CLI agents against a scratch
                               home and exporting it for the collector; see lab/README.md
tools/check_research_links.py  verifies every citation link in the research documents
                               resolves to its file and line range at the cited commit
tools/check_doc_links.py       verifies every relative link and heading fragment in the
                               Markdown documents and that section and external
                               references are links
_config.yml                    the documentation site: Jekyll with the just-the-docs
                               theme, built from the documents where they are
_plugins/                      site build plugins: GitHub heading ids, code spans kramdown
                               reads differently, links to non-page files
Gemfile, Gemfile.lock          the site's Ruby dependencies
README.md                      project overview; points at the per-part READMEs
AGENTS.md                      this file
CLAUDE.md                      imports this file for Claude Code
LICENSE                        Apache 2.0
ruff.toml, pyrightconfig.json, .markdownlint-cli2.jsonc, .shellcheckrc
                               linter configuration; see "Quality gates"
.githooks/pre-commit           the catalog drift check
.github/                       CI workflow, the Pages workflow (workflows/pages.yml,
                               publishes the site) and Dependabot configuration
```

Nothing in `collectors/` may depend on `analyzer/`. Paths in this file are
relative to the repository root unless stated otherwise.

## Non-negotiable standards

**No dependencies on the host.** The collector uses only the base system: sh,
find, cp, tar, gzip, du, awk, grep, sed, sort, cut, tr, readlink, mkdir, rm,
and one of `sha256sum`, `shasum`, `sha256` or `openssl`. Never add Python,
Perl, jq, or anything that may be absent on a minimal host. macOS does not ship
Python 3; Alpine containers and BSD base systems do not ship bash. The Windows
collector, when written, is PowerShell 5.1 with no modules.

**POSIX sh, not bash.** The shebang is `#!/bin/sh` and the script must run
unchanged under bash 3.2 (macOS `/bin/sh`), dash, busybox ash, FreeBSD and
OpenBSD sh, posh (the pdksh lineage), and `zsh --emulate sh`. Concretely:

- No arrays, no `local`, no `[[ ]]`, no `read -d`, no `mapfile`, no
  `${var,,}`, no `${var:0:3}`, no `$'...'`, no `function` keyword, no
  `-print0 | read -d ''`, no process substitution.
- No GNU-only flags: no `sed -i`, `date -d`, `cp --parents`, `find -false`,
  `stat -c` without a BSD fallback, `xargs -0` without a fallback.
- Platform differences (`stat`, hashing, `ps`, user enumeration) go behind a
  small wrapper function with capability detection done once at startup.
- Shell functions cannot be inherited by `find -exec sh -c`, so shared helpers
  live in the `COMMON` string, which is `eval`'d in the main script and
  prepended to the worker programs.
- Globs with spaces are expanded with `IFS` set to newline only; see
  `expand_glob`. Pattern matching uses `case`.
- pdksh-derived shells end a `$(...)` at the first `)`, even a `case`
  pattern's inside a here-document. Write `case` patterns inside command
  substitutions as `(pattern)`, and read a here-document into a variable
  with `heredoc_var`, not `VAR=$(cat <<'EOF' ...)`.
- `shellcheck -s sh` with the repository's `.shellcheckrc` (every optional
  check on, four disabled with reasons), `checkbashisms -p` and a
  `shfmt -ln posix` parse must be clean on every sh file; see "Quality
  gates".

**Windows PowerShell 5.1, not PowerShell 7.** `Collect-AgentArtifacts.ps1`
must run under the PowerShell that ships with Windows 10, 11 and Server 2016+,
and also under PowerShell 7 on any OS so the test can run in Linux CI.
Concretely:

- No ternary operator, no `??`, no `-AsHashtable`, no three-argument
  `Join-Path`, no `[System.IO.Path]::GetRelativePath`, no `.NET Core`-only
  APIs. `Get-FileHash`, `ConvertTo-Json -Compress`, `[DateTimeOffset]` and
  `System.IO.Compression.FileSystem` are fine.
- Never name a variable after an automatic variable: `$home`, `$host`,
  `$args`, `$input`, `$error`, `$pid`, `$profile` are read-only or special
  and fail silently or loudly. Use `$homeDir`, `$HostName`, `$cargs`.
- Under `Set-StrictMode -Version 2` on 5.1 a scalar has no `.Count` and a
  missing property throws. Wrap anything that may be a single item in `@()`.
- Array splatting to a script file binds positionally; use a hashtable splat
  to pass named parameters.
- Hidden items (every dotfile under PowerShell 7 on Linux, `AppData` on
  Windows) need `-Force` on `Get-Item` and `Get-ChildItem`.
- Use `tar.exe` only when `$env:OS` is `Windows_NT`; under WSL, PowerShell 7
  on Linux can find the Windows `tar.exe` through interop and produce a
  broken archive. Fall back to `ZipFile` elsewhere.
- Write files through `StreamWriter` with UTF-8 and no BOM; `Add-Content` on
  5.1 defaults to ASCII and mangles non-ASCII paths.
- Open source files with `FileShare.ReadWrite | Delete` so stores locked by a
  running editor still copy.

**Single file, non-interactive.** No prompts, nothing read from stdin, all
output under `-o`, concise stdout, exit `0` when an archive was written even if
individual files failed. EDR consoles upload one file and run it once.

**Forensic soundness.**

- Never modify, move or delete anything outside the output directory.
- `lstat` every file before copying it so the manifest holds pre-copy times.
- Hash the staged copy, not the source, so the hash matches the archived bytes
  even when a running agent appends to the source mid-collection.
- Never follow symlinks; record them with their target and recreate them.
- Everything that is skipped (size exclusions, oversized files, secrets) is
  still recorded in the manifest with a status and size. Silence is a bug.
- Credential files are evidence of which account acted. Collect them by
  default, flag them `secret: true`, and honour `--no-secrets`.
- Never print secrets or file contents to stdout or the log.

**Catalog is data, not code.** Agent paths live in the `CATALOG`,
`PROJECT_CATALOG`, `EXCLUDES`, `SECRET_GLOBS` and `DOCKER_VOLUMES` tables at
the top of both scripts. `DOCKER_VOLUMES` maps a Docker or Podman named
volume name glob to an agent (`agent-zero|*a0_usr`); the first matching line
wins, a matched volume is collected whole with its `_data` directory as the
collection base, and an unmatched one gets a single
`skipped_unmatched_volume` row. Because the base is the volume root, a tool
deployed in a volume needs volume-relative forms of its exclusions and
secret globs (`tmp/playwright`, `secrets.env`) beside the home-relative ones;
keep them at the end of each table and check they do not collide with
another tool's volume layout (no bare `tmp` or `cache`). Adding a tool means adding the same lines to both, never new code
paths. Every entry is tried against every home directory so one table covers
macOS, Linux, Windows and disk images of each. The tables are byte-identical
between the sh single-quoted strings and the PowerShell `@'...'@`
here-strings; `collectors/tests/catalog-sync.sh` fails on any drift, and `--list` and
`-List` must print identical output. Glob semantics are shared: catalog
globs do not cross `/`, exclusion and secret globs do, and `[...]` and `[!...]` classes
work in both (the PowerShell side converts globs to regexes). Exclusion and secret globs are matched
relative to the collection base, a home directory, a discovered project
or a Docker volume's `_data` directory, so one pattern such as `.claude/worktrees` applies in both places; write them
without a leading `*/`. Anchor every glob on a path component: `.hermes*/auth.json`
and `agent-zero*/usr/.env`, never `*hermes*/auth.json`, which also matches
any project path containing the name. The one accepted leading `*` is the
editor data-directory form `*/User/globalStorage/...`. When an exclusion and
a secret glob both match, the exclusion wins: the subtree is pruned before
the secret test runs and its only manifest row is the directory's
`skipped_excluded`, so a credential inside an excluded tree needs the
exclusion narrowed (`hermes-agent/[!.]*` keeps `.env`). The PowerShell
match is case-insensitive, so a glob that differs from a sibling only by
case (`*/Hermes/Cache` beside `hermes/cache`) must name explicit bases
instead, and an exclusion whose last component is a common name
(`*/Claude*/Cache`) also prunes another tool's directory whose parent
differs only by case (Claude Code's `claude-cli-nodejs/Cache` on
Windows): that tool's catalog entry then names the directory's children
(`AppData/Local/claude-cli-nodejs/Cache/*`), never the directory, and
the PowerShell smoke test checks that a file under it is collected. An entry nested
inside another entry's match (`antigravity|.gemini/antigravity-cli` inside
`gemini-cli|.gemini`) claims its subtree: both collectors expand every entry
first and prune claimed paths from the enclosing walk, so each file is
collected once under the most specific agent, and the analyzer applies the
same rule in loose mode. Use a nested entry whenever one tool stores its state
inside another tool's directory.

**Manifest schema is an interface.** The analyzer and analysts depend on
`manifest.jsonl` and `collection.json`. Fields, status values
(`collected`, `symlink`, `skipped_excluded`, `skipped_size`, `skipped_secret`,
`skipped_special`, `error_copy`, `skipped_unmatched_volume`, `error_read`) and the
`fs/<original path>` archive layout are documented in
[`collectors/docs/output.md`](collectors/docs/output.md). Add fields if needed, but do not rename or remove them
without updating that page and noting it in the commit message.

### Readability

A responder reads a collector before running it as root, so both are
written to be audited (issue 99). The architecture and the function tables
are in [`collectors/docs/internals.md`](collectors/docs/internals.md).

- **One layout.** Both scripts have the same twelve sections, in this
  order and under these banner titles: Reader's guide, Data tables, Shared
  helpers, Manifest writer, Staging files, Catalog walk, Users, Docker and
  Podman volumes, Project discovery, Inventory output, Summary and archive,
  Main program. A section one script lacks keeps its banner and a line
  saying why. The reader's guide at the top of each file lists the
  sections, states the data flow in one paragraph and the naming rules;
  it changes with the flow. New code goes in the section that owns its
  step, and the main program stays a list of one call per step.
- **One comment per function**, directly above it: what it takes (in sh,
  also the globals it reads), what it returns, prints or writes (files,
  globals, `_ret_` variables), in sh its temporaries' prefix, and the shell
  or platform quirk it exists for, when there is one.
- **sh names.** Globals shared between functions are `UPPER_CASE`. A
  function's temporaries are `_<prefix>_<name>`, the prefix an abbreviation
  of the function's name (`_cp_` for `collect_path`), since sh has no
  `local`. A function that assigns its result instead of printing it sets
  `_ret_<what>` (`_ret_json`). A worker program is held in `<NAME>_WORKER`,
  read from the here-document `EOF_<NAME>_WORKER`, and its first line names
  its positional arguments; other here-document labels name what they
  feed (`EOF_USER_LIST`).
- **PowerShell names.** Script state is `$script:PascalCase`; parameters
  and locals are `$camelCase`. Functions use approved verbs, and a
  function that sets up or changes run state is named with `Initialize`,
  `Open`, `Close`, `Switch` or `Clear`, because PSScriptAnalyzer's
  `PSUseShouldProcessForStateChangingFunctions` rule wants `-WhatIf`
  support for `New`, `Set`, `Remove`, `Start`, `Stop` and `Update`.
- **Both.** No single-letter or cryptic names except a loop index whose
  scope is a few lines; a variable that fills a manifest field is named
  like the field (`mtime`, `archive_path`, `sha256`).
- **One name per job.** The sh and PowerShell functions for one step have
  matching names (`collect_path` and `Add-CollectedPath`) and one row in
  the pairs table in [`collectors/docs/internals.md`](collectors/docs/internals.md#function-pairs);
  a function added, renamed or removed on either side updates that page
  in the same commit.
- **Bounds.** A function body stays under 40 lines and never exceeds 60.
  Longer than 40 is allowed only for a per-item loop that a split would
  give an extra call per file or member (`Add-CollectedFile`,
  `Write-TarEntries`), a flat list of discovery sources
  (`Find-AgentSessionProjects`) or one literal (`Initialize-Summary`).
  Lines are at most 100 characters outside the data tables: break sh
  commands with `\` or a `set --` argument list, PowerShell ones with
  splatting or intermediate variables, never a backtick continuation. No
  new fork, pipeline or external command per file in the sh workers or in
  `Add-CollectedFile`.
- **Acceptance test for a refactor.** A change made for readability
  changes no behaviour: options, `--list`, manifest rows (every field,
  value and the row order), `collection.json`, the log lines and their
  order, stdout, stderr, exit codes, the archive's members, the tables
  byte for byte and the `COLLECTOR_SH` and `CAC_*` environment variables.
  The smoke tests passing is not enough, since they check selected rows.
  Run the collector before and after the change on the smoke test's fake
  image with the same arguments, for every collector run the smoke tests
  make, under every shell of the matrix and under PowerShell 7 and 5.1,
  and compare the manifests (every field but `atime`, which the first
  run's reads can move), `collection.json` (less `started`, `finished` and
  `archive`), the logs, stdout, stderr, exit codes and archive member
  lists, allowing only timestamps, the output directory and the archive's
  own size and hash to differ. A bug found on the way is filed and fixed
  in its own commit.

## Analyzer standards

The analyzer runs on the analyst's workstation, never on the host, so the
rules are different from the collectors'.

- **Python 3.10 or later, standard library first.** Third-party packages are
  allowed when a format needs them (protobuf, zstandard, a SQLite helper) and
  go in both `requirements.txt` and `pyproject.toml`. Avoid syntax newer
  than 3.10.
- **The catalog is shared, not copied by hand.** `doubleagent/catalog.txt`
  is generated from `collect-agent-artifacts.sh --list`; both
  `collectors/tests/catalog-sync.sh` and the analyzer tests fail when it is
  stale, the CI workflow in `.github/workflows/ci.yml` runs that check on
  every push and pull request, and `.githooks/pre-commit` refuses a commit
  that touches either collector or the copy while they differ (enable it
  once per clone with `git config core.hooksPath .githooks`). After any
  catalog edit, regenerate the copy before committing. Detection logic lives in `catalog.py` and reads that file. Never
  hard-code an agent path in a parser's detection; parsers select files by
  their path relative to the home (`artifact.rel`).
- **Attribution comes from the manifest when there is one.** Host, user, home
  and agent are read from `collection.json` and `manifest.jsonl`. Only loose
  input without a manifest infers them from paths, and the output says so.
  Never silently guess when the manifest is present.
- **Parsers are validated like catalog entries.** Confirm the record shape
  against source or a real install, write the evidence into
  `analyzer/research/<agent>.md` (one document per catalog agent, see the
  research process above), list the field names the parser depends on in
  the module docstring, and build the test fixture from those shapes.
  For a closed-source agent that stores protobuf, the shipped binary usually
  embeds its descriptors; `analyzer/tools/proto_descriptors.py` extracts
  them, and the parser's schema table cites the proto file they came from.
  Decode protobuf with `doubleagent/protobuf.py` and open SQLite through
  `doubleagent/sqlite_util.py` so WAL sidecars are read and the evidence
  copy is never opened directly.
  Bad lines are evidence, never fatal and never summarised away. A
  transcript cut mid-write by a running agent, a crash or a partial
  recovery still yields every turn before and after the cut, and each
  line that does not decode becomes its own `system` row carrying the
  line in full: `parser: unparseable line (<reason>): <line>`, the line
  as read with only its terminator removed, nothing repaired, extracted
  or shortened (issue 136); a JSON array reader says `unparseable record
  <N> (<reason>)` instead. An error about the whole file (unreadable,
  not a JSON array, cut inside an array) is one row `parser: <message>`.
  The row carries the `session_id` and `project_path` the reader knows
  for that file, an empty `timestamp_utc` (the line has none of its
  own) and `source_line` set to the line. This holds for every file a
  parser reads, not only the transcript: a history file, a secondary
  source or an index that loses lines says so in its own rows.
  Mechanically: a reader appends `(line, message, raw)` to an `errors`
  list (`iter_jsonl` and `line_text` in `parsers/base.py` do this for
  JSONL), the parser ends the file with
  `yield from error_rows(self, artifact, errors, session_id, project_path)`
  from `base.py`, and no parser formats a bad-line row of its own; only
  a whole-file row (an unreadable database, a document that is not
  JSON) is written in place. Every
  `errors` list a reader fills is reported, returned or passed on; a
  pre-scan that discards errors passes a literal `[]`, and only over a
  file the same parser also parses in full and reports on. Three history
  readers dropped bad lines silently (issues 125 and 134);
  `ErrorListsReportedTests` in `analyzer/tests/test_errors.py` fails on
  a list a parser fills and never reads again.
  The agent's subsection under
  [Parser details](analyzer/docs/parsers.md#parser-details), linked from
  its row in the [agents table](analyzer/docs/parsers.md#agents), names
  the real installs (platform, version, date) on which the parser's file
  paths and record shapes were seen, and says "fixture only" for a path
  that rests on source or a bundle alone, while the row's "Validated
  against" cell names the evidence class and platforms in a few words
  (`real installs: macOS, Windows (October 2026)`,
  `source; fixture only`); section 1 of the research document carries
  one **Observed** bullet per platform (see "Real-install rounds").
- **The outputs are interfaces.** The `timeline.jsonl` and `sessions.jsonl`
  fields, their order and their JSON types are documented in
  [`analyzer/docs/output.md`](analyzer/docs/output.md), and the `fleet-inventory.csv` columns in
  [`analyzer/docs/inventory.md`](analyzer/docs/inventory.md); add fields or columns at the end and never
  rename, retype or remove them without updating those pages and saying so
  in the commit. A JSONL record
  always has every field, with `""` rather than `null` for no value.
  Timestamps are always UTC ISO 8601 with milliseconds and a trailing Z.
- **Read-only, no surprises.** The analyzer writes only under `-o` and the
  archive work directory, never follows symlinks, and never materialises
  symlinks from an archive. The `text` field carries the full event text,
  line breaks included, and is never truncated; shortening it is the
  analyst's step afterwards, with jq or DuckDB.
- **Lint and types.** ruff (lint and format) and pyright in standard mode
  must be clean; see "Quality gates". Fix a finding rather than suppress
  it, and give any `# noqa` or `# pyright: ignore` a reason.
- **Tests.** `analyzer/tests/run.sh` must pass. Add a fixture and a test
  class for every parser, and a detection test for every new input shape.

## Adding a parser

The research is already done for every agent in the parser backlog: start
from `analyzer/research/<agent>.md`, whose section 8 is a parser plan mapped
to the timeline columns and whose sample records are meant to become the
fixture. Do not redo the research. The citations link to the commit that was
reviewed, so check the record shape at that link, not on the default branch,
and say in the module docstring if the shape has drifted since.

1. Create `doubleagent/parsers/<agent>.py` with a class that subclasses
   `Parser` from `parsers/base.py`. Its `agent` attribute must equal the
   catalog name. `wants()` selects by `artifact.rel` with a regex, and
   `secondary()` says, the same way, which of those files repeat the
   primary store's events (step 3, past use);
   `parse()` yields rows built from `base_row()`, which fills host, user,
   agent and `source_file`. Reuse `iter_jsonl`, `text_of` and
   `compact_json` from `base.py`, `compact` from `model.py` and `to_utc`
   from `timeutil.py` rather than writing new ones. List the field names
   the parser depends on in the module docstring, as the existing modules do.
   A parser that must read a file the catalog attributes to another agent
   (Cody and Twinny rows inside an editor's `state.vscdb`) lists that agent
   in its `reads_agents` attribute; nothing else routes files across agents.
   A wrapper over another agent's format reuses that agent's reader rather
   than copying it: little-coder and Letta Code sessions go through the pi
   parser's reader, and Open Interpreter subclasses Codex's `RolloutParser`.
2. Register an instance in the `ALL` list in `parsers/__init__.py`. Nothing
   else discovers parsers.
3. Row semantics the existing parsers share: `tool_use` rows carry
   `tool_name` and `tool_use_id`; `tool_result` rows join on
   `tool_use_id`; `thinking` rows are yielded only when
   `opts.include_thinking` is set; each bad line becomes its own `system`
   row carrying the line in full (`error_rows` in `base.py`), a
   whole-file error one `parser:` row, and the other turns are still
   yielded; `session_id` and `project_path` propagate from the session
   header to every row;
   `git_branch` stays empty when the format does not record it. Formats
   without per-message timestamps (Continue, Zed, Cline's legacy history)
   inherit the session timestamp; say so in the docstring.
   Permission state is evidence of what the user authorised, not
   configuration to skip. When the format records a per-call decision (an
   approval, a denial, an "allow always", an automatic decision), the
   parser yields a `system` row for it beside the call it governed,
   joined on `tool_use_id` when the format allows, in the form the
   `claude-code` parser uses (`permission decision: <decision> ...`).
   When the agent keeps standing allow or deny lists, trusted folders or
   sandbox settings in a file, the parser yields one `system` row per
   entry, timestamped by the file's modification time and saying so in
   the text, as the `claude-desktop` parser does for scheduled tasks. The
   research document names every file and field that holds either kind
   before the parser is written, and a parser plan with no permission
   line says the agent records none. Antigravity's per-step
   `TrajectoryPermissions` blob and its `globalPermissionGrants` list were
   collected for a week before anyone noticed the parser read neither
   (issue 92).
   The model is evidence of the same kind. Any agent that can use or
   switch between models gets a `system` row `model: <id>` at the first
   record of a session that names one and `model: <old> -> <new>` on
   every change, with the agent's own request or alias beside the
   resolved id when the format records both; filling the `model` column
   on each row is not enough, because an analyst filtering on `system`
   rows must see when the model changed. A model switch the user typed
   (a `/model` command and its output) keeps its own row as well. The
   research document names where the format records the model per
   message, per session and per switch, and a parser plan with no model
   line says the agent records none (issue 93).
   Past use is evidence of the same kind, and the transcript store is
   rarely its only record. A per-prompt history file, a mirror or
   projection of the transcript (a search index, a summaries database, a
   web interface's copy, a brain or memory directory), an archive of
   reset or deleted sessions, a backup and a text-only prompt history
   each outlive the transcript they repeat, and a session the user
   deleted is often recoverable from nothing else: an Antigravity session
   whose project directory the agent had deleted survived as a database,
   a brain mirror, four history lines and a summaries row (issue 122).
   Before the parser is written, the research document lists every file
   that records use beyond the primary store, says what each holds, what
   it survives (a deleted session, a rewind, a removed project, a
   compaction) and how its records join the primary store's (session id,
   project path, text and time), and its parser plan marks each source
   primary or secondary; a plan with no such line says the agent keeps
   none. The parser reads every one of them on every run, never as a
   fallback when the primary store is missing, and returns True from
   `secondary()` for the files that repeat the primary store's events, so
   `dedup.deduplicate` shows each event once and keeps what only the
   secondary source still holds (the rule is documented under
   [Secondary sources in `analyzer/docs/output.md`](analyzer/docs/output.md#secondary-sources)).
   A secondary source whose records carry no time of their own yields
   rows with an empty `timestamp_utc`, never an inherited session time,
   so the match is on text alone and the session's time stays on its own
   `system` row. A source that stamps events later than the primary store
   returns a wider window from `secondary_tolerance()` and says why in
   its docstring.
   The agent's row in the
   [survival table of `analyzer/research/README.md`](analyzer/research/README.md#where-transcripts-live-and-what-survives)
   is filled in the same commit.
4. SQLite stores are opened through `sqlite_util.py` so the WAL sidecar is
   read and the evidence copy is never opened directly. Protobuf blobs are
   decoded with `protobuf.py`. A new dependency such as `zstandard` for Zed
   goes in both `requirements.txt` and `pyproject.toml`.
5. Add a `<agent>_records()` builder to `tests/fixtures.py` and wire it into
   `build_home`, which the detection tests share. Use the same `/srv/proj`
   project path so the timeline tests see the rows, add a noise file the
   parser must not want (a config or credential file), and use
   `write_bad_line` for the truncation case.
6. Add a `<Agent>Tests(ParserBase)` class to `tests/test_parsers.py` with
   the same cases the existing classes have: rows, thinking opt-in, history,
   not-wanted, truncated line. The truncated-line case is repeated for
   every file the parser reads line by line, the history file and each
   secondary source as well as the transcript, and checks that the lines
   before and after the bad one are still yielded beside the `parser:` row.
7. Fill the agent's row in the [agents table](analyzer/docs/parsers.md#agents):
   set its status to `parsed`, its "Validated against" cell to the
   evidence class and platforms in a few words, and keep its Notes cell's
   shape: the research links, now with the analyzer research document,
   the open issue links, and a clause of about twelve words only when
   something is still unparsed. Move the agent's subsection from
   [Collected files](analyzer/docs/parsers.md#collected-files) to
   [Parser details](analyzer/docs/parsers.md#parser-details), in
   alphabetical order, and fill it with the files the parser reads
   ("Files read:") and the full evidence for the parser ("Validated
   against:", the platform, version and date of every real install).
   Grep the documents for the agent
   name and move it out of every example that shows it under `detected
   but not parsed`, `collected only` or `parser: false`. Also update the
   parsed-agent list in [`analyzer/README.md`](analyzer/README.md) and the [top-level README](README.md),
   bump `VERSION` in `doubleagent/__init__.py` (`pyproject.toml` reads it),
   and run `analyzer/tests/run.sh`.

Each parser is self-contained and fully specified by its research document
and this list, so one parser per agent, run in parallel, is the natural way
to delegate the backlog.

## Adding an agent to the catalog

Prefer reading the tool's source over installing it. Most agents are open
source even when their models are not, and the path constants are easy to
find. The validation for every current entry is recorded in the index table in
[`collectors/research/README.md`](collectors/research/README.md).

1. Shallow-clone the repository into the scratchpad and grep for `homedir`,
   `XDG`, `APPDATA`, `Application Support`, `.config/`, `.local/share`,
   `sessions`, `history`, `sqlite`, `auth`, `token`, `secrets`, `cache`,
   `cwd`, `workspace`. Read the paths module (`paths.ts`, `paths.rs`,
   `global.ts`, `storage.ts`, `home.go`) and cite file and line in the issue.
   For closed-source tools, grep the shipped npm bundle or binary for literal
   path strings (`npm pack`, `strings`), then fall back to official docs,
   vendor forums and published DFIR write-ups, and say which was used.
2. From that, identify transcripts, history, config, credentials, and
   anything large (binaries, model weights, caches, indexes, shadow git
   checkpoints, worktrees, git clones of marketplaces). Note which OSes share
   a layout: many tools use `~/.config` and `~/.local/share` on macOS and
   Windows too, and several keep credentials in the OS keychain with a file
   fallback that only appears on headless hosts.
3. Add `agent|path` lines to `CATALOG` in both scripts for every platform
   path the tool uses, including the Windows `AppData` location so images are
   covered. Regenerate `analyzer/doubleagent/catalog.txt` from `--list`,
   run `collectors/tests/catalog-sync.sh`, and add an `Added` line under
   `Unreleased` in [`analyzer/CHANGELOG.md`](analyzer/CHANGELOG.md), because the analyzer's detection
   changes with the catalog copy.
4. Add large or irrelevant subtrees to `EXCLUDES` and credential files to
   `SECRET_GLOBS`. If the tool's README, compose file or installer creates a
   named Docker volume, add its name pattern to `DOCKER_VOLUMES` with the
   source cited in the comment above it, and add volume-relative forms of
   its exclusions and secret globs (paths relative to the container mount
   point) at the end of `EXCLUDES` and `SECRET_GLOBS`.
5. If the tool records project paths, add extraction to the matching
   source group of `discover_projects` in the sh collector and
   `Find-Projects` in the PowerShell collector, at the same position on
   both sides (the groups are listed in
   [`collectors/docs/internals.md`](collectors/docs/internals.md#project-discovery)), and
   any per-project files to `PROJECT_CATALOG`. Process names are not
   listed anywhere: running processes are the EDR's job (see Purpose).
6. Add a fixture and assertions to `collectors/tests/smoke.sh` and
   `collectors/tests/smoke.ps1`. Both files have the same shape: the
   fake image is built first, in labelled fixture blocks (one per catalog
   revision, `# YYYY-MM-DD <topic> (#n)`) under the users' homes; then the
   default `run` and its `check "name" "expr"` lines; then the
   `--no-secrets`, `--full`, `-u` and other runs, each followed by its own
   checks. Put the new tool's files in a fixture block in the image-build
   section, its default-run checks after the default run's existing
   checks, and a check that depends on another run (a `skipped_secret`
   status needs `--no-secrets`) after that run's checks, repeating the
   same dated label at each place. A separate root and `run` (as the
   MSIX block does) is only for a layout the main image cannot
   hold. Add at least one check for every new secret glob, exclusion and
   discovery source, plus one for anything unusual in the layout
   (symlinks, SQLite sidecars, spaces in paths, drive-letter or
   `file:///` project references), and keep the check names identical in
   both files. Run the full shell matrix from "Validation and testing";
   every shell in it, including Windows PowerShell 5.1 through the WSL
   path, is available on the development host, so an untested shell is a
   gap to close, not a note to leave.
7. Write or update `collectors/research/<agent>.md` with the evidence
   (the eight sections in the research process below, less section 7), add
   a row to the index table in [`collectors/research/README.md`](collectors/research/README.md), mention the
   tool in [`collectors/docs/coverage.md`](collectors/docs/coverage.md) if it needs
   a note there, and close the matching GitHub issue. If the tool keeps
   transcripts worth parsing, also write `analyzer/research/<agent>.md` and
   its index row. Add the agent's row to the
   [agents table](analyzer/docs/parsers.md#agents) with status `backlog`
   (parseable records on disk, with a parser issue) or `collected`
   (nothing to parse, with the reason), its name linked to a new
   subsection under
   [Collected files](analyzer/docs/parsers.md#collected-files) that lists
   what the collector gathers; a `collected` row also adds the
   agent to `NO_TRANSCRIPTS` in `analyzer/doubleagent/parsers/__init__.py`,
   which the analyzer reports as `collected only` and a test keeps equal
   to the table. A parser issue filed for the agent later is linked in
   its row by the commit that files it, and an example that shows the
   agent list (the `agents:` line, `detected_not_parsed`,
   `collected_only`) is updated when the agent appears in the fixture.

Every catalog entry has been validated against source, a shipped bundle, or
official documentation. When a real-install check is wanted, run the tool in
the `lab/` sandbox and point the collector at the exported home rather than
installing it on the workstation (Linux layout only); `collectors/research/<agent>.md` records the evidence
for each agent and the index table in [`collectors/research/README.md`](collectors/research/README.md) summarises the level. Real-install checks
exist for Claude Code, Antigravity CLI, Codex CLI, Copilot CLI and Ollama.
Agents whose project paths live only in SQLite (Zed, Goose, OpenCode, Kilo
Code, Kiro CLI) are not covered by `discover_projects`; the analyzer reads them.

## Validating catalog entries from source

This is the process used for the v1.1 catalog, and the one to repeat when a
tool is added or a tool's layout is suspected to have changed. It replaces
installing the tool: source is authoritative, faster, and keeps the
workstation clean.

**1. Group the tools and fan out.** One researcher per platform group, run in
parallel. Group forks of the same codebase together (Gemini CLI with Qwen
Code; Cline with Roo Code and Kilo Code; OpenCode with Crush) because the
differences are what matter. Put closed-source tools in their own groups since
the evidence gathering is different.

**2. Give each researcher the same brief.** It should contain: the current
catalog lines for that tool (from `--list`), the repository to shallow-clone
into the scratchpad, the grep terms to start with, and the instruction to
cite file and line for every claim, as a link to that line at the reviewed
commit (`https://github.com/<owner>/<repo>/blob/<full sha>/<path>#L<n>`), and
never rely on memory. Grep terms that
find the paths module quickly:

```text
homedir  XDG  APPDATA  LOCALAPPDATA  "Application Support"  .config/  .local/share
.local/state  .cache  sessions  history  checkpoint  snapshot  worktree  sqlite  .db
auth  token  credential  secrets  keyring  keychain  cache  bin  node_modules
cwd  workspace  project  worktree  mcp  rules  AGENTS.md
```

Likely file names: `paths.ts`, `paths.rs`, `global.ts`, `storage.ts`,
`home.go`, `config/load.go`, `env.ts`, `directories.rs`.

**3. Require a fixed report structure.** Eight numbered sections, under
about a thousand words:

1. Repo, commit checked, open source or not.
2. Per-user storage for Linux, macOS and Windows: every directory and file
   under the home, what each holds, and whether the layout is shared across
   OSes. Flag tools that use XDG paths on macOS and Windows.
3. Credentials on disk, by exact file name, and whether the OS keychain is
   used with a file fallback. Note config files that can embed API keys.
4. Large or low-value subtrees to exclude, as exact path patterns: binaries,
   model weights, caches, embedding indexes, shadow git checkpoints,
   worktrees, marketplace clones, Electron caches.
5. Project-local files written or read inside repositories. Call out any
   per-project database, since those are easy to miss.
6. Where the project or workspace path is recorded, with file and JSON key or
   table and column, so `discover_projects` or the analyzer can use it.
7. Proposed lines in the collector's own formats: `agent|glob` for
   `CATALOG`, globs for `EXCLUDES` and `SECRET_GLOBS`, `project|glob` for
   `PROJECT_CATALOG`.
8. Confidence per item and what could not be determined.

**4. Evidence hierarchy for closed-source tools.** In order: the shipped npm
tarball or binary (`npm pack`, then grep or `strings`; minified bundles keep
literal path strings), official docs, vendor forums and issue trackers, then
published DFIR or reverse-engineering write-ups. The report must say which
level each claim came from, and the index table in
[`collectors/research/README.md`](collectors/research/README.md) records it. Two habits for minified
bundles and compiled binaries:

- Grep for the stable fragment of a message, never the whole sentence.
  Log lines are usually template literals
  (`${h?"Enabling":"Disabling"} remote control for session ${s}`), so a
  search for `Enabling remote control for session` misses a string that
  is there. "Not in the bundle" is unproven until a second fragment of
  the same message also misses.
- A compiled CLI (the Bun-built Claude Code binary, Go binaries) still
  carries its source strings, so `strings` and a regex over the bytes
  work, but offsets differ per platform build. Cite as
  `<tool> <version> <platform> @<byte offset>` with the literal snippet,
  and record the artifact's sha256 and where it came from, as
  [`analyzer/research/claude-code.md`](analyzer/research/claude-code.md) does for `claude 2.1.295 linux-arm64`.
  The `app.asar` form is `app.asar:<path>@<offset>` with the snippet;
  chunk names change every release, so the snippet is what a reader of
  another version greps for.

**5. Integrate in one commit.** Research agents write only their research
documents and never edit the scripts, the catalog copy or the tests; the
`CATALOG`, `PROJECT_CATALOG`, `EXCLUDES` and `SECRET_GLOBS` tables are
byte-identical here-strings in two scripts plus `catalog.txt`, so two
agents editing them in parallel conflict on every line. One integration
agent makes every table change after all reports are in, so the tables
change once. New lines go under the vendor's comment block in the table, or
a new comment block for a new vendor, never at the end. Then split every group report into one document per catalog agent,
named exactly as the agent appears in `--list`, keeping the numbered section
structure, the citations and the fixtures, but dropping section 7 once its
proposals are in the tables, so no committed document reviews a catalog
that has moved on (the collector documents number confidence as section 7
for that reason): path research (where state lives,
credentials, exclusions, project files, discovery) goes to
`collectors/research/<agent>.md`, record schema research (how transcripts
are encoded and how a parser reads them) goes to
`analyzer/research/<agent>.md`. A document covers one agent only, and
every agent that earns a catalog line gets its own, even when it came out
of a grouped sweep such as the framework sweep (issue 64): the sweep
document ([`collectors/research/frameworks.md`](collectors/research/frameworks.md)) keeps only the summary
table and the evidence for what got no catalog line. Where
agents share a lineage, each says so and links to the other rather than
repeating it. When an agent has both documents, each links to the other
with a Markdown link in a short paragraph before its first section, the
analyzer document to `../../collectors/research/<agent>.md` and the
collector document to `../../analyzer/research/<agent>.md`. A path to
another project document, or to one of its sections, is always a link,
never a bare code span (the link rule under "Conventions"). Each
directory has a README index that lists every document, sorted
alphabetically by agent name, and holds the cross-agent observations.
Grouped reports are never committed. Then: rewrite the five tables in both
scripts and regenerate
`analyzer/doubleagent/catalog.txt` from `--list`, extend
`discover_projects` in the sh collector and `Find-Projects` in the
PowerShell collector with every new grep-able source, add a fixture and
checks to `collectors/tests/smoke.sh` and `collectors/tests/smoke.ps1` for
each new secret pattern, exclusion and discovery source, run the full shell
matrix, run a live collection and read the `skipped_excluded` and
`secret: true` rows, update the research index tables, bump `VERSION`.

**6. Close the loop on GitHub.** Close each tool's issue with a comment that
names the evidence source and commit, the key findings, and the catalog
changes. Comment on the analyzer parser issue with any SQLite-only sources found.
File new issues for anything out of scope that the research surfaced, such
as sandboxed install paths or tokens stored inside chat databases.

**Running a round with subagents.** The split in [CLAUDE.md](CLAUDE.md) applies: the
main session writes one brief and a per-tool assignment, one research
subagent per tool runs in parallel, one integration subagent makes the
table, test and index changes, and the main session reviews. Research is
safe to delegate because each subagent writes only its own new document,
but the brief must set the safety envelope, which differs from code work:

- Fetching untrusted code is the job; executing it is not. Shallow clones,
  `npm pack` tarballs and binaries for `strings` go in the scratchpad and
  are only read. No `npm install`, no installers, no running the tool, no
  install on the workstation. A real-install run in `lab/` is a separate
  step that the user asks for explicitly.
- A blocked clone or download is reported, not worked around from memory.
  A research document written from memory is worse than none, because its
  citations look like evidence.
- A live collection against the workstation collects the author's own
  credentials. A subagent that runs one writes it under the scratchpad,
  deletes it afterwards, and never puts file contents or manifest rows
  from it into its report; or the main session runs it.
- Posting to GitHub (closing issues, commenting) is outward-facing, so the
  subagent reports what to post and the main session posts it after review.

The review gate for a research round is mechanical first: run
`tools/check_research_links.py` (with `--repos` pointing at the scratchpad
checkouts when they exist) and treat any link that does not resolve, and
any claim with no link, as unverified. Then the integration subagent's
test run is repeated by the main session: `collectors/tests/catalog-sync.sh`,
the full shell matrix and the analyzer tests.

Things the first run taught us, to check for explicitly next time:

- A library with no platform branching (`xdg-basedir`, `etcetera`,
  `home.Config()`) means `~/.config` and `~/.local/share` on macOS and
  Windows too. Do not assume Library or AppData.
- Exclusions must not swallow credential files. Continue's
  `index/globalContext.json` sits next to the embedding index it shares a
  directory with.
- Some tools store sessions inside the repository (Crush) or gitignore
  their own state directory, so the project list, not git, is the index.
- Auth tokens and chat history can share one SQLite file (Cursor, Windsurf);
  collect it unflagged and document the keys to redact.
- Forks drift: Kilo Code moved from the Roo layout to an OpenCode fork;
  Windsurf is rebranding to Devin. Check the current commit, not the name.

And from the October 2026 round:

- The named repository may no longer be the product. Letta's main branch is
  a landing page and the shipped tool is Letta Code in another repository;
  Open Interpreter is now a Rust fork of Codex CLI; two repositories had
  moved organisations. A researcher confirms what the repository ships
  before reading paths from it, and follows the move.
- A wrapper around another agent needs that agent in the catalog. little-coder
  writes its sessions into pi's directory and Letta Code uses pi's session
  format; neither was collectable until pi got its own entry. Researchers
  report every other agent whose state directory their tool reads or writes,
  and the round adds it.
- Entries that differ only by case (`.config/PearAI` and `.config/pearai`,
  `.config/goose` and `.config/Goose`) collect the same directory twice on
  macOS and Windows (issue 29). Add both only when they are distinct on
  Linux, and make the smoke check for them test attribution, not count.
- Counts in a brief are not evidence. The integration agent derives the
  number of agents from the documents in the tree, not from the brief, and
  says so when they differ.
- Claude Desktop has no separate Cowork button or Cowork tab since the
  2.31226 builds (October 2026): Chat and Cowork are one surface, and the
  app switches a chat into Cowork mode itself when the task needs the
  local agent. The remaining distinct surface is the Code tab. Do not
  describe a "Cowork mode" the user starts by hand, do not ask the user
  to "open Cowork", and do not expect a local `local_<uuid>.json` under
  `local-agent-mode-sessions/` for every chat: on the real installs
  checked (2.31226.1, MSIX build and Linux deb) a read-only
  chat left nothing there, and a chat that wrote files ran as a remote
  Cowork session whose only local traces were
  `remote-session-spaces.json` (the session id and the granted folders)
  and the files it committed; its transcript is server-side. Scheduled
  tasks set from a chat are account state on the server, not entries in
  the local `scheduled-tasks.json`, which stayed empty on both installs
  for an account that has one.
- Chat history outside the home (ShellGPT's temp directory) cannot become
  a catalog line. Record it in [`collectors/docs/coverage.md`](collectors/docs/coverage.md) as a manual step and
  file an issue, rather than stretching a glob. Docker and Podman named
  volumes are the exception since collector 1.5.0: they go in
  `DOCKER_VOLUMES`.

## Real-install rounds

Source and bundles say where an agent can write; a real install says what
it did write. A real-install round installs one agent in a clean VM (or
the `lab/` sandbox for Linux-only CLIs), exercises it, and compares the
result with the research documents, the catalog and the parser. The
Claude Desktop rounds of October 2026 (MSIX build, Linux deb,
macOS) are the pattern; each found something the bundle research had not:
an uncollected data directory, two unflagged keys, a feature that writes
nothing locally.

The round, in order:

1. **Survey names first.** List the agent's directories with names,
   sizes and mtimes only, before and after each action, and diff the
   listings. The diff is the evidence of what an action wrote.
2. **Read shapes, never values.** `analyzer/tools/shape.py` prints key
   names, value types and JSONL line types with UUIDs, hex ids and long
   tokens redacted, and never a value; copy it to the VM alone and run it
   with `python3 -I`. It is the only way to look inside an agent's files
   on a real install. Ad-hoc scripts that print values are not written,
   and nothing from a real install is pasted into the repository, an
   issue or a report beyond file names, key names, types, sizes, enum
   values and log lines with ids redacted.
3. **Exercise every surface separately** and record what each one wrote:
   a session with a tool call, a read-only chat, a chat that writes a
   file, a scheduled task, a resumed session, and one tool call approved
   and one denied, with an "allow always" or equivalent standing grant,
   and a model switch in the middle of a session, so the permission and
   model records are on disk for the shape tool to show; then a session
   deleted the way a user would (the agent's own delete or clear command,
   or the project directory removed), with a listing diff after it, so
   the round records which traces of past use survive and the parser
   reads them (step 3 of "Adding a parser"). A surface that writes
   nothing locally is a finding (Claude Desktop's merged Chat/Cowork
   surface runs server-side and leaves one index file), and so is a
   feature the VM cannot run (nested virtualisation); say which it was.
4. **Run the collector in the VM** as the user and pull the manifest, the
   summary and the log; read the error rows, the `skipped_excluded`
   rows and the unflagged-key list from "Validation and testing". Then
   pull the archive, run the analyzer over it, and check that every
   observed session yields rows and that no `system` row reports an
   unreadable file. A parser update starts the same way: run the shape
   tool over the new version's transcripts and diff the line types and
   key sets against the lists in the research document.
5. **Write it down the same day.** Section 1 of both research documents
   gets an **Observed** bullet per platform with the version, build,
   date, what was exercised and what each surface wrote; a layout the
   parser handles that no real install has shown is marked "not observed
   on any real install, bundle-derived"; every statement about a product
   surface (a tab, a button, a mode) carries the build and date, because
   surfaces change between releases and training-era knowledge of the UI
   is stale. Catalog, exclusion, secret-glob and parser changes follow
   the usual checklists, under the pending version.
6. **Clean up.** Delete the collections pulled to the analyst machine and
   every output left in the VM; revert the VM to its clean snapshot
   before the next agent.

Subagents do the integration from a brief that carries the evidence; they
never run the collector live against the VM or read its user's data
directories, and the main session posts anything that goes to GitHub.

A round covers every surface the agent ships, on every platform it ships
it for. An agent with a CLI and a desktop app (Antigravity, Claude), an
editor fork and an extension, or a packaged build and a direct download
shares directories between its surfaces but not formats, data-directory
names or feature sets: the Antigravity CLI and the Antigravity desktop
app both write SQLite-of-protobuf conversations under `~/.gemini`, in
`antigravity-cli/` and `antigravity/`, and the app's were collected and
never parsed until the app itself was exercised (October 2026), because
the CLI round had been taken as covering the agent. The matrix is
surfaces times platforms and each cell is its own round: install the
CLI and exercise it, install the app and exercise it, on macOS, Windows
and Linux, with one **Observed** bullet per cell in section 1 of both
research documents; a cell with no bullet is a gap to close, not a note
to leave. Within a surface, run every kind of task it offers, each one
on its own with a listing diff after it: a question with no tool use, a
coding task that writes files, a scheduled or automated task, a
third-party integration such as a plugin or an MCP server, a resumed
session. When every task was run before the first listing, the round
cannot say which task wrote which file; its document says so, gives
the modification times, and the mapping waits for the next round.

## Validation and testing

CI (`.github/workflows/ci.yml`) runs the catalog drift test, shellcheck, the
sh smoke test under sh, dash, bash, busybox ash, zsh and posh, the PowerShell
smoke test under PowerShell 7 on Linux and Windows PowerShell 5.1 on
Windows, the analyzer tests on Python 3.10, 3.11, 3.12, 3.13 and 3.14, and a lint job
with the quality gates below. A change that touches only Markdown files
and `.markdownlint-cli2.jsonc` is documentation only: the workflow's
first job classifies the push or pull request from the changed file
list, and when it is documentation only every other job is skipped and
the lint job runs just markdownlint and `tools/check_doc_links.py`.
Those two are also all a documentation-only change needs locally; the
smoke tests, the analyzer tests and the other linters are for changes to
code. A push whose previous commit GitHub cannot name (a new branch, a
force push) is treated as a code change. Run the same locally before
committing a change to the collector:

```sh
cd collectors
shellcheck -s sh -S warning collect-agent-artifacts.sh   # info-level notices are allowed
tests/smoke.sh            # /bin/sh
tests/smoke.sh dash
tests/smoke.sh bash
printf '#!/bin/sh\nexec busybox ash "$@"\n' > /tmp/ash && chmod +x /tmp/ash && tests/smoke.sh /tmp/ash  # busybox, as CI runs it
printf '#!/bin/sh\nexec zsh --emulate sh "$@"\n' > /tmp/zsh-sh && chmod +x /tmp/zsh-sh && tests/smoke.sh /tmp/zsh-sh
tests/smoke.sh posh
tests/catalog-sync.sh
pwsh -NoProfile -File tests/smoke.ps1
cd ../analyzer && tests/run.sh
cd ..
# quality gates, from the repository root (see "Quality gates")
uvx ruff@0.16.10 check . && uvx ruff@0.16.10 format --check .
uvx --from pyright==1.1.414 --with zstandard --with python-dateutil pyright
npx -y markdownlint-cli2@0.23.3 "**/*.md"
python3 tools/check_doc_links.py
shfmt -ln posix $(shfmt -f .) >/dev/null && shellcheck -s sh $(shfmt -f .) && checkbashisms -p $(shfmt -f .)
pwsh -NoProfile -Command '$r = @("collectors/Collect-AgentArtifacts.ps1","collectors/tests/smoke.ps1") | ForEach-Object { Invoke-ScriptAnalyzer -Path $_ -Settings collectors/PSScriptAnalyzerSettings.psd1 }; $r | Format-Table -AutoSize; exit @($r).Count'
```

For a change to the PowerShell collector, also run the test under real
Windows PowerShell 5.1. From this WSL checkout that is:

```sh
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -ExecutionPolicy Bypass \
  -File '\\wsl.localhost\Ubuntu\home\sean\dev\coding-agent-collector\collectors\tests\smoke.ps1' \
  -Collector '\\wsl.localhost\Ubuntu\home\sean\dev\coding-agent-collector\collectors\Collect-AgentArtifacts.ps1'
```

Symlink creation needs a privilege the test may not have on Windows; it
skips the symlink checks and says so. A pass under PowerShell 7 alone is not
enough: 5.1 is stricter about `.Count` on scalars and lacks several APIs.
A pass under 5.1 through the WSL path is still weaker than a pass on the
CI runner: the runner has longer temp paths, a different console width and
no symlink privilege, and two 5.1 failures so far appeared only there. A
change is done when the CI run for the pushed commit is green; check it
with `gh run watch` and fix what fails before moving on.

The smoke test builds a fake disk image under `$TMPDIR` with two users, a
service account, a `nobody` account to skip, awkward filenames (quotes,
spaces, backslashes), a symlink, credential files, excluded directories, an
oversized file and projects referenced from agent state. It runs the collector
in image mode with the given shell for both the script and the `find -exec`
workers (`COLLECTOR_SH`), then checks statuses, hashes, JSON validity,
archive contents, `--no-secrets`, `--full` and `-u`. All checks must pass under
every shell; a failure under one shell is a portability bug, not a test
problem.

On Debian and Ubuntu `/usr/bin/ash` is a link to dash, so `tests/smoke.sh
ash` does not test busybox; use the wrapper above. CI installs
`busybox-static`, whose `ash` runs busybox's own `tar`, `gzip` and other
applets before anything on `PATH`, while the non-static `busybox` package
honours `PATH`. A test that forces a code path with a `PATH` shim
therefore needs the static build to reproduce CI. Get it without
installing: `apt-get download busybox-static && dpkg-deb -x
busybox-static_*.deb bbs` in the scratchpad, then point the wrapper at
`bbs/usr/bin/busybox`.

Then run a live collection against your own host and read the summary:

```sh
collectors/collect-agent-artifacts.sh -o /tmp/live -q
powershell.exe -ExecutionPolicy Bypass -File collectors\Collect-AgentArtifacts.ps1 -OutputDir $env:TEMP\live -Quiet
```

Check the error count, look at the `skipped_excluded` rows for anything new
and large, and confirm the manifest parses as JSONL. Then list the
`collected` rows that are not `secret: true` and whose file name contains
`key`, `token`, `secret`, `cred`, `cookie` or `auth`, and account for each
one: either it is not a credential (say why in the research document) or
it needs a secret glob. Both keys the Linux round of October 2026 found
unflagged were visible this way. Delete the output afterwards; it contains
your own credentials.

The test uses `python3` only for JSON validation and the hash cross-check, and
skips those checks when it is absent. Never add a `python3` requirement to the
collector itself.

### Waiting for long-running checks

The smoke matrix, the PowerShell runs and the analyzer suite take
minutes, so agents often run them in the background. Wait on them in a
way that cannot hang:

- Wait on the process you started, never on a name search. Use `wait`
  in the same shell, or have each job write its exit code to a file
  (`...; echo "exit $?" >"$out.rc"`) and wait for every `.rc` file to
  exist. Never poll with `pgrep -f` or `ps | grep`: the waiting shell's
  own command line contains the pattern, so the loop matches itself and
  never ends.
- Give every wait an upper bound (`timeout 1800 ...`, or a loop that
  stops after N rounds) and report a timeout as a failure, not a pass.
- Read results from the output files, not from whether the watcher
  ended: a finished watcher can still mean a failed check, and a
  killed one says nothing about the checks it was waiting on.
- For CI, use `gh run watch <id> --exit-status`, which exits when the
  run ends.

### Quality gates

Every gate runs in the CI `lint` job, not in the pre-commit hook: the hook
is reserved for fast operations (see below).
The versions are pinned in the workflow's `env` block; change it and this
list together. Run the commands from the repository root before pushing;
for a documentation-only change, only markdownlint and
`tools/check_doc_links.py` (see the start of this section).

| Gate | Version | Local command | Configuration |
| --- | --- | --- | --- |
| ruff lint | 0.16.10 | `uvx ruff@0.16.10 check .` | `ruff.toml`; `analyzer/pyproject.toml` extends it |
| ruff format | 0.16.10 | `uvx ruff@0.16.10 format --check .` | `ruff.toml` (line length 100) |
| pyright, standard mode, Python 3.10 | 1.1.414 | `uvx --from pyright==1.1.414 --with zstandard --with python-dateutil pyright` | `pyrightconfig.json` |
| markdownlint | markdownlint-cli2 0.23.3 | `npx -y markdownlint-cli2@0.23.3 "**/*.md"` | `.markdownlint-cli2.jsonc` |
| shfmt POSIX parse | 3.14.1 | `shfmt -ln posix $(shfmt -f .) >/dev/null` | none; never pass `-w` |
| shellcheck | 0.11.0 | `shellcheck -s sh $(shfmt -f .)` | `.shellcheckrc` |
| checkbashisms | devscripts v2.26.13 | `checkbashisms -p $(shfmt -f .)` | none |
| PSScriptAnalyzer | 1.25.0 | the `pwsh` line in the block above | `collectors/PSScriptAnalyzerSettings.psd1` |
| document links | none | `python3 tools/check_doc_links.py` | none; see the link rule under "Conventions" |

- `shfmt -f .` lists the sh files by shebang as well as extension, so the
  hook script, `lab/lab.sh` and `analyzer/tests/run.sh` are checked too.
  `posh` (apt package `posh`) runs the smoke test in CI and in the block
  above.
- pyright runs with both analyzer dependencies installed, as CI runs it;
  `zstandard` and `python-dateutil` are ordinary top-level imports, never
  lazy imports with a fallback.
- shellcheck, shfmt and checkbashisms are not on PyPI or npm: install the
  release binaries (CI downloads them and checks their sha256), and
  checkbashisms as the single `scripts/checkbashisms.pl` from the devscripts
  tag, or `apt install devscripts`. PSScriptAnalyzer installs with
  `pwsh -NoProfile -Command 'Install-Module PSScriptAnalyzer -Scope CurrentUser -RequiredVersion 1.25.0 -Force'`.
- The tree was reformatted once with `ruff format` in a commit of its
  own, listed in `.git-blame-ignore-revs`; enable it locally with
  `git config blame.ignoreRevsFile .git-blame-ignore-revs`.
- The pre-commit hook (`.githooks/pre-commit`, enabled once per clone with
  `git config core.hooksPath .githooks`) holds only fast operations, today
  the catalog drift check. Linters, tests and network queries belong in CI
  or the release checklist, never in the hook; a slow hook gets bypassed.

## Conventions

- Commit messages: imperative subject under 70 characters, body explaining
  why, ending with the `Co-Authored-By` line when an AI agent wrote the code.
- Everything an AI agent writes to git or GitHub discloses that it was
  generated by AI and names the model: commits, issues, pull requests,
  comments, reviews and review replies. A commit carries a
  `Co-Authored-By: <model name> <noreply address>` trailer (for example
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`); an issue, pull
  request, comment, review or review reply ends with a line such as
  `Generated by AI (Claude Opus 5.5).` Name the model that wrote the text,
  as the tool reports it, not a family name or a guess; when a subagent
  wrote the change and the main session reviewed it, name both. This
  applies to text an agent posts on a person's behalf too.
- Work on `main` directly for now; branch when a change spans several commits.
- Outstanding work is tracked as GitHub issues. File one when you find
  something out of scope rather than widening a change, and label it by
  what it is: `bug` for behaviour that is wrong, broken or contradicts the
  documentation (a wrong exit status, a stale manifest value, a file
  collected twice, a promise the code does not keep), `enhancement` for a
  new feature, catalog entry or improvement to behaviour that already works
  as documented. A missing feature is an enhancement; a documented feature
  that misbehaves is a bug.
- Every bug fixed and every feature added has an issue, an existing one or
  one filed before the work is committed, even when the fix is found and
  made in the same session. Search open and closed issues first so the
  work lands on the existing one. The issue number is what ties the work
  together: each commit that implements it names it in the body
  (`Refs #<n>`), and each changelog line for it ends with `([#<n>])`, a
  reference link to the issue (see the changelog rule below). Use
  `Refs`, not `Fixes` or `Closes`, so the push does not close the issue
  before CI is green. GitHub closes an issue for any closing keyword
  (`close`, `fix`, `resolve` and their `-s` and `-d` forms) followed by
  `#<n>` anywhere in a commit message, prose included, so write "the fix
  for #29" or "#29 is fixed", never "fixes #29"; the issue is closed after the release is tagged,
  with a comment that explains the fix and names the commit and the
  release that contains it. Changes with no behaviour of their own
  (typos, formatting, a test-only refactor, these conventions) need no
  issue.
- Evidence lives in the research documents, not in issues. When an issue
  records file names, keys, values a field can take, or bundle and
  binary offsets, the commit that files or acts on it puts the same facts
  in `collectors/research/<agent>.md` or `analyzer/research/<agent>.md`
  with their citations; the issue keeps the proposal, the open questions
  and a pointer to the document. An issue is closed and forgotten; the
  document is what the next parser change reads.
- Documentation describes the code, not the intent. Every sentence that
  states an option, an output file, a field, a value a field can take, or a
  behaviour is checked against the code path that implements it before it
  is committed, and says where the two collectors or the platforms differ
  and what happens without root or Administrator. A feature is documented
  with specifics, an option table row, a file-by-file or field-by-field
  table, the list of values, never named in passing: a reader who has only
  the README must be able to say what each file in the output holds and
  which command produced it. A sentence that cannot be verified from the
  code is not written; "the analyzer reads X" is a claim about `cli.py`,
  not about what would be sensible. Before a `VERSION` bump, re-derive the
  option list, the output file list and the status or column list from the
  code and diff them against the README; the changelog entry then records
  what changed in those lists.
  The example output blocks and the key, field and column tables are
  part of the interface, for the collectors as much as for the analyzer:
  a change to anything a command prints or writes (a stdout line or
  group, a log line, a `manifest.jsonl` field or status value, a
  `collection.json` key, the `--list` and `-List` output, an option, a
  JSON key, a JSONL field, a CSV column, a row text convention) updates
  every example and table that shows it in the same commit, in
  `collectors/README.md` and `collectors/docs/` as in `analyzer/README.md`
  and `analyzer/docs/`, and an example marked as a real run is
  regenerated by running the command, the collector over the smoke
  test's fake image and the analyzer over the test fixtures, never
  edited by hand. Adding a parser or a catalog agent is such a change:
  an example that shows the agent under `detected but not parsed`,
  `collected only` or `parser: false` changes with it, and so does the
  agent's row in the [agents table](analyzer/docs/parsers.md#agents),
  which also gains a row for every new catalog agent and a link for
  every parser issue filed or closed, in the commit that adds the agent
  or acts on the issue. Grep the documents for the agent name, the key,
  the label or the heading before committing; nobody should have to ask
  for the examples or the table to be brought up to date.
  Behaviour changes without a README update are incomplete. The [top-level
  README](README.md) is an overview only.
  A new document page starts with the same front matter as its siblings
  (`title`, `parent`, `grand_parent` when three levels deep, `nav_order`,
  and `has_children` on a section page), so it takes its place in the
  navigation of the [documentation site](https://seanthegeek.github.io/doubleagent/);
  `tools/check_doc_links.py` stays the link check, and skips the front matter.
- Every term a document takes from a vendor, a bundle or a product
  surface is explained at its first use in that document: what it stands
  for, what it denotes here, and where the name comes from. This covers
  abbreviations (3p, 1p, MSIX, RTR, DPAPI), a vendor's internal names
  (`ccd`, `rpm`, `buddy-tokens`), and a directory or key whose name alone
  does not say what it holds. A reader who has only this document and
  the code must never need the vendor's documentation to decode a
  sentence; "3p" needed "the enterprise build that runs inference through
  the customer's own provider" beside it. Section 1 of a research
  document is the place when the term runs through the whole document,
  otherwise the first sentence that uses it. Before committing a
  document, list its capitalised and letter-digit short tokens and check
  that each is a code identifier the surrounding sentence explains or a
  term glossed earlier in the file.
- Every reference from one project document to another is a Markdown
  link, never a bare path or code span: a file is written
  ``[`collectors/docs/coverage.md`](collectors/docs/coverage.md)`` with
  the path relative to the citing file, and a section is written
  `[section 5](#5-project-local-files)` or, in another document,
  ``[section 2 of `analyzer/research/claude-desktop.md`](../../analyzer/research/claude-desktop.md#2-per-user-storage)``,
  with the fragment GitHub derives from the heading (lower case,
  punctuation other than hyphens removed, spaces to hyphens). A reference
  to several sections is one link per section. The exception is this
  file's references to the numbered sections of the research template
  (`<agent>.md`), which describe every research document at once and
  have no single target. A template path with a placeholder
  (`collectors/research/<agent>.md`) names a family of documents, not
  one, and stays a code span, as does a catalog path that happens to end
  in `.md` (an agent's `AGENTS.md` or `GEMINI.md` inside a project),
  which is data, not a document reference.
  An external source is linked the same way: the whole reference is
  one link whose text names what it is, a page title without quotes, an
  `owner/repo` README, `owner/repo issue 105`, `owner/repo pull request
  6`, and the target is the full URL with its scheme, so
  `[User identity and local data](https://claude.com/docs/third-party/claude-desktop/data-storage)`
  rather than a bare `claude.com/docs/...` with a title after it, and
  never a URL as the link text. A fetch date or a note stays outside
  the link text, in parentheses after it, and a second page on the same
  site is a second full link, never `and /settings`. Citations to a
  file at a commit keep their existing form (see "Validating catalog
  entries from source").
  `tools/check_doc_links.py`, run by the CI lint job, fails on a relative
  link whose file or heading does not exist, on a `section <n>` that is
  not link text, and on a URL or scheme-less host path (`github.com/...`)
  outside a link target; run it before pushing a documentation change.
- Bump `VERSION` in the script for any change to output format or options.
  For the analyzer, bump `VERSION` in `doubleagent/__init__.py`;
  `pyproject.toml` reads the version from it. Bump once per release: if
  `VERSION` is already ahead of the last release tag, later work before
  the tag goes into that version's changelog entry, with its date updated
  at tag time, and `VERSION` is not bumped again unless the user says so.
  A version that was never tagged is noise in the changelog. A change to
  documentation alone bumps nothing and needs no changelog line (see the
  tag rule below).
- Every `VERSION` bump comes with an entry in the matching changelog,
  [`collectors/CHANGELOG.md`](collectors/CHANGELOG.md) or [`analyzer/CHANGELOG.md`](analyzer/CHANGELOG.md), in Keep a Changelog
  form: a `## [x.y.z] - YYYY-MM-DD` heading with `Added`, `Changed`, `Fixed`
  and `Removed` subsections, one line per item, written for the responder
  or analyst who uses that part. Any change to the manifest, JSONL or CSV
  interfaces is called out in that entry. Work that lands between bumps
  goes under `## [Unreleased]` and moves into the next version's heading
  when it is bumped. An issue number in a changelog is a reference link,
  `([#<n>])`, never a bare `(#<n>)`, so it opens the issue when rendered.
  The definitions sit at the bottom of the file after the version
  comparison links, one `[#<n>]: https://github.com/seanthegeek/doubleagent/issues/<n>`
  per issue in descending order; add the definition with the first line
  that cites a new issue. markdownlint checks both ways: MD052, with
  `shortcut_syntax` on in `.markdownlint-cli2.jsonc`, fails on a
  reference with no definition, and MD053 on a definition nothing cites.
- A release requires zero open Dependabot alerts. Before tagging, check
  with `gh api "repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/dependabot/alerts?state=open" -q length`;
  if it is not 0, resolve or dismiss each alert (with a reason in the
  dismissal) before the tag. CI cannot enforce this, because the workflow
  token cannot read Dependabot alerts, so it is part of the release step.
  Dependabot itself is configured in `.github/dependabot.yml`.
- A tag marks a change to what the collector or the analyzer does. Once
  the bump commit is pushed and its CI run is green, tag it
  `collector-vX.Y.Z` or `analyzer-vX.Y.Z` with an annotated tag and push
  the tag. The prefix is what distinguishes the two version sequences;
  never use a bare `vX.Y.Z`. Add the version's comparison link at the
  bottom of the changelog. A change that touches only documentation,
  research documents, this file or the linter configuration gets no tag,
  for the same reason it gets no `VERSION` bump: the released scripts
  and package are unchanged, and the change is published by the push to
  `main`. Such a commit may follow a tagged commit without needing a
  tag of its own, and a pending tag may sit on it or on the last code
  commit, whichever the user prefers.

## Things to avoid

- Adding Python, jq or any interpreter to the on-host collector.
- Parsing transcripts on the host. That is the analyzer's job and it runs on
  the analyst side.
- Collecting model weights, editor caches or extension binaries by default.
- Reading files through symlinks or descending into symlinked directories.
- Writing to `/tmp` by default or anywhere other than `-o`.
- Interactive prompts, `sudo` calls, or anything that reads stdin.
- Bash-isms that happen to work on the developer's machine. Test under dash
  and busybox ash before assuming something is portable.
