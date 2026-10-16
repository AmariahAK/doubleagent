# Parsers

What the parsers put in a row, how the analyzer routes files to them,
and how it reads protobuf and SQLite stores. Every catalog agent's parse
status, the files each parser reads and what it was validated against,
and the files collected for the agents not parsed are on the
[agents page](../../docs/agents.md).

## Row content

The field names each parser relies on are listed in its module docstring
under `doubleagent/parsers/`. Thinking and reasoning blocks are left out
unless `--include-thinking` is passed. The `text` field carries the full
text of each event, line breaks included, so the timeline is a complete
transcript, one event per line. The second copies an agent keeps beside
its transcript store (prompt histories, mirrors, indexes, backups and
snapshots, the secondary sources) are parsed even when the matching
transcript exists, because they can survive its deletion, and a row of
one is dropped when the transcript or another copy records the same
event (see [Secondary sources](output.md#secondary-sources)), so each
event appears once. One fallback remains: Cline's
`api_conversation_history.json` is read only when the task's
`ui_messages.json` is absent, because the two record different texts
for the same turn (the API history wraps the first prompt in `<task>`
tags, and its tool calls are content blocks where the UI messages have
one JSON record per tool), so the rule could not pair them and the
task's turns would be shown twice; see
[section 8 of `research/cline.md`](../research/cline.md#8-parser-plan).

## Routing files to parsers

Files the collector finds inside a project directory through its project
catalog have the project directory as their manifest `home`, which the
analyzer marks as a project base (from `collection.json` `projects`).
From collector 1.12.0 they carry the agent the project catalog names for
them, a repository's `.aider.chat.history.md` `aider` and its
`.crush/crush.db` `crush`, and go to that agent's parsers like any other
file, so `--agent aider` and `--agent crush` include them. Collectors
before 1.12.0 recorded every one as agent `project`; the analyzer
re-attributes those from its bundled project catalog (see
[detect in `output.md`](output.md#detect)). A file the catalog leaves to
agent `project`, because several agents read it (`AGENTS.md`), is
offered to every parser, and the rows of any parser that accepts it are
kept under that parser's agent. A parser that scopes a row to the
project, such as `claude-code` for a project's `.claude/settings.json`,
reads the project base marker, not the agent.

Every other file goes to the parsers of the agent the manifest (or, for loose
input, the catalog) attributes it to, plus any parser that names that agent
in its `reads_agents` attribute. Cody and Twinny keep their chats as rows of
the editor's own `state.vscdb`, which the catalog attributes to `vscode` or
to the fork whose `User/` directory holds it (`cursor`, `windsurf`, `pearai`,
`kiro`, `antigravity`); both parsers list all six editors in `reads_agents`,
so that file is offered to them too and the rows come out under `cody` or
`twinny`, and `--agent cody` selects them. `secret://` rows are never read.

## Protobuf and SQLite

Protobuf stores are decoded by `doubleagent/protobuf.py`, a small
schema-driven wire decoder, from field tables written into each parser. For
a closed-source agent the field names come from the descriptors embedded in
its binary. `tools/proto_descriptors.py extract BINARY OUT.json` extracts
them, and `show OUT.json MESSAGE...` and `find OUT.json TEXT` query them. SQLite
stores are copied together with their `-wal` and `-shm` sidecars into a
scratch directory before being opened, so the evidence copy is never touched
and rows still in the write-ahead log are not lost.

To read the key names and line types of an agent's files on a real install
without reading their values, use `tools/shape.py`; see
[Reading a real install](development.md#reading-a-real-install).
