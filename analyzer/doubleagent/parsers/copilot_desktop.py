"""GitHub Copilot Desktop (Tauri app, dpkg package `github`) app store (issue 147).

Closed source. Validated against the shipped app (`github` 1.1.29
linux-arm64, `/usr/bin/github`) and a real install of GitHub Copilot
Desktop 1.1.29 on Ubuntu 26.04 arm64 (2026-10-16), with a synthetic
fixture; see `research/copilot-desktop.md`. The app runs its sessions
through a bundled Copilot CLI that writes them into
`.copilot/session-state/<id>/` in the CLI's own format, so those logs
belong to the catalog's `copilot-cli` entry and are read by the
`copilot-cli` parser (`workspace.yaml` `client_name` `github/autopilot`
marks them). This parser reads the app's own store only.

* `.copilot/data.db`, SQLite in WAL mode (opened through `sqlite_util`,
  which copies the `-wal` and `-shm` sidecars with it), the primary and
  only source: no `secondary()` file, since it repeats no event of the
  session logs. Every timestamp column is ISO 8601 UTC with milliseconds
  (`strftime('%Y-%m-%dT%H:%M:%fZ','now')`); every column is read as
  possibly NULL, and a table that is missing gives no rows. All rows are
  `system`, `source_line` 0, in this table order and then by the time
  column and rowid:
  - `accounts` (`login`, `host`, `kind`, `is_default`, `access_token`,
    `created_at`): `account: <login> host=<host> kind=<kind>
    default=<is_default> token_present=<true|false>`; the token itself is
    never written (it was NULL on the install, the token being in the
    GNOME keyring).
  - `settings` (`storage_location`, `instructions`, `github_access_token`,
    `github_token_type`), at the file's modification time: `desktop
    settings: storage_location=<s> instructions=<i or -> github_token_present=<b>
    github_token_type=<t or -> (from .copilot/data.db, file mtime)`.
  - `model_providers` (`name`, `type`, `created_at`): `model provider:
    <name> type=<type>`.
  - `projects` (`id`, `name`, `container_kind`, `main_repo_path`,
    `github_owner`, `github_repo`, `default_branch`, `created_at`):
    `project added: <name> kind=<k> path=<p> github=<owner>/<repo>
    default_branch=<b>`, ` github=` left out when both are NULL;
    `project_path` `main_repo_path`.
  - `worktrees` (`project_id`, `path`, `branch`, `base_branch`,
    `created_at`): `worktree: <path> branch=<b> base=<base or ->`.
  - `workspaces` (`id`, `project_id`, `name`, `workspace_type`, `branch`,
    `source_pr_repo_full_name`, `source_pr_number`,
    `created_pr_repo_full_name`, `created_pr_number`, `created_at`):
    `workspace: <name> type=<t> branch=<b>`, then ` source_pr=<repo>#<n>`
    and ` created_pr=<repo>#<n>` when set. Worktree and workspace rows
    take `project_path` from their project's `main_repo_path`.
  - `sessions` (`id`, `title`, `session_type`, `model`, `auto_approve`,
    `permission_mode`, `remote_control_enabled`, `archived_at`,
    `forked_from_session_id`, `created_at`): `desktop session: <title or
    -> type=<t> model=<m or -> auto_approve=<n> permission_mode=<p or ->
    remote_control=<n> archived=<true|false>`, and `forked from session
    <id>` when `forked_from_session_id` is set; `session_id` the id (the
    session-state directory name), `model` the model, `project_path`
    through `workspace_session_aliases` (`session_id`, `workspace_id`) ->
    `workspaces.project_id` -> `projects.main_repo_path`, empty for a
    general chat. `auto_approve` and `permission_mode` are the app's
    standing permission state: it records no per-call decision.
  - `activity_items` (`session_id`, `activity_type`, `preview`,
    `created_at`): `activity <type>: <preview>`.
  - `session_checkpoints` (`session_id`, `commit_sha`, `created_at`):
    `checkpoint commit <sha>`.
  - `my_copilot_scheduled_tasks` (`title`, `prompt`, `enabled`,
    `execution_mode`, `background_agent_type`, `created_at`):
    `scheduled task: <title> enabled=<n> mode=<m> agent=<a> prompt: <p>`.
  - `my_copilot_scheduled_task_triggers` (`task_id`, `kind`, `enabled`,
    `next_run_at`, `config_json`, `created_at`): `scheduled task trigger:
    task=<id> kind=<k> enabled=<n> next_run_at=<t or -> config: <json>`.
  - `my_copilot_scheduled_task_invocations` (`task_title`, `status`,
    `source`, `scheduled_for`, `prompt_snapshot`, `parent_session_id`,
    `claimed_at`), at `claimed_at`: `scheduled task run: <title>
    status=<s> source=<src> scheduled_for=<t or -> prompt: <p>`,
    `session_id` the parent session.
  - `session_automations` (`session_id`, `name`, `interval`,
    `every_minutes`, `next_run_at`, `prompt`, `updated_at`), at
    `updated_at`: `session automation: <name or -> interval=<i>
    every_minutes=<n or -> next_run_at=<t or -> prompt: <p>`.
  - `session_deletion_intents` (`session_id`, `created_at`): `session
    deletion requested`.
  The four scheduling tables and `session_deletion_intents` were empty on
  the install, so their rows are fixture only (columns from the schema).
  A file that is not SQLite, or a SQLite error, is one `parser:` row.

Model: `sessions.model` per session, on the `desktop session:` row and in
its `model` column; `data.db` keeps no per-switch history (the logs'
`session.model_change` events are the `copilot-cli` parser's `model:`
rows). Not read: `repo-metadata-cache.db`, the `localstorage` store (the
unsent composer draft), the `github-app.*.log` tracing log, `run/` and
the other `data.db` tables (empty on the install, or app bookkeeping).
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator

from ..inputs import Artifact
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import Options, Parser, compact_json, file_mtime

DB_RX = re.compile(r"^\.copilot/data\.db$")


def _str(v) -> str:
    if v is None:
        return ""
    return v if isinstance(v, str) else compact_json(v)


def _dash(v) -> str:
    return _str(v) or "-"


def _bool(v) -> str:
    return "false" if v in (None, "") else "true"


class CopilotDesktopParser(Parser):
    agent = "copilot-desktop"
    name = "copilot-desktop"

    def wants(self, artifact: Artifact) -> bool:
        return bool(DB_RX.match(artifact.rel))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            yield self._row(artifact, "parser: not a SQLite database")
            return
        try:
            with open_copy(artifact.disk_path) as con:
                rows = list(self._rows(artifact, con))
        except sqlite3.DatabaseError as e:
            yield self._row(artifact, "parser: SQLite error: %s" % e)
            return
        yield from rows

    def _row(self, artifact: Artifact, text: str, ts=None, **cols) -> Row:
        r = self.base_row(artifact)
        r.turn_type = "system"
        r.text = compact(text)
        r.timestamp_utc = to_utc(ts) if ts not in (None, "") else ""
        for k, v in cols.items():
            setattr(r, k, v or "")
        return r

    @staticmethod
    def _select(con: sqlite3.Connection, tables: set, table: str, order: str) -> list[dict]:
        if table not in tables:
            return []
        sql = "select rowid as _rowid, * from %s order by %s, rowid" % (table, order)
        return [dict(r) for r in con.execute(sql)]

    def _rows(self, artifact: Artifact, con: sqlite3.Connection) -> Iterator[Row]:
        tables = table_names(con)

        def select(table: str, order: str = "created_at") -> list[dict]:
            return self._select(con, tables, table, order)

        projects = {_str(p.get("id")): p for p in select("projects")}
        workspaces = select("workspaces")
        workspace_project = {_str(w.get("id")): _str(w.get("project_id")) for w in workspaces}
        aliases = {
            _str(a.get("session_id")): _str(a.get("workspace_id"))
            for a in select("workspace_session_aliases")
        }

        def project_path(project_id: str) -> str:
            return _str(projects.get(project_id, {}).get("main_repo_path"))

        for a in select("accounts"):
            yield self._row(
                artifact,
                "account: %s host=%s kind=%s default=%s token_present=%s"
                % (
                    _str(a.get("login")),
                    _str(a.get("host")),
                    _str(a.get("kind")),
                    _str(a.get("is_default")),
                    _bool(a.get("access_token")),
                ),
                a.get("created_at"),
            )
        mtime = file_mtime(artifact)
        for s in select("settings", "id"):
            yield self._row(
                artifact,
                "desktop settings: storage_location=%s instructions=%s"
                " github_token_present=%s github_token_type=%s (from %s, file mtime)"
                % (
                    _str(s.get("storage_location")),
                    _dash(s.get("instructions")),
                    _bool(s.get("github_access_token")),
                    _dash(s.get("github_token_type")),
                    artifact.rel,
                ),
                mtime,
            )
        for m in select("model_providers"):
            yield self._row(
                artifact,
                "model provider: %s type=%s" % (_str(m.get("name")), _str(m.get("type"))),
                m.get("created_at"),
            )
        for p in projects.values():
            text = "project added: %s kind=%s path=%s" % (
                _str(p.get("name")),
                _str(p.get("container_kind")),
                _str(p.get("main_repo_path")),
            )
            if p.get("github_owner") is not None or p.get("github_repo") is not None:
                text += " github=%s/%s" % (_str(p.get("github_owner")), _str(p.get("github_repo")))
            text += " default_branch=%s" % _str(p.get("default_branch"))
            yield self._row(
                artifact,
                text,
                p.get("created_at"),
                project_path=_str(p.get("main_repo_path")),
            )
        for w in select("worktrees"):
            yield self._row(
                artifact,
                "worktree: %s branch=%s base=%s"
                % (_str(w.get("path")), _str(w.get("branch")), _dash(w.get("base_branch"))),
                w.get("created_at"),
                project_path=project_path(_str(w.get("project_id"))),
            )
        for w in workspaces:
            text = "workspace: %s type=%s branch=%s" % (
                _str(w.get("name")),
                _str(w.get("workspace_type")),
                _str(w.get("branch")),
            )
            for prefix, label in (("source_pr", "source_pr"), ("created_pr", "created_pr")):
                repo, number = w.get(prefix + "_repo_full_name"), w.get(prefix + "_number")
                if repo is not None or number is not None:
                    text += " %s=%s#%s" % (label, _str(repo), _str(number))
            yield self._row(
                artifact,
                text,
                w.get("created_at"),
                project_path=project_path(_str(w.get("project_id"))),
            )
        yield from self._session_rows(artifact, select, aliases, workspace_project, project_path)
        yield from self._schedule_rows(artifact, select)

    def _session_rows(self, artifact, select, aliases, workspace_project, project_path):
        for s in select("sessions"):
            sid = _str(s.get("id"))
            cols = {
                "session_id": sid,
                "model": _str(s.get("model")),
                "project_path": project_path(workspace_project.get(aliases.get(sid, ""), "")),
            }
            yield self._row(
                artifact,
                "desktop session: %s type=%s model=%s auto_approve=%s permission_mode=%s"
                " remote_control=%s archived=%s"
                % (
                    _dash(s.get("title")),
                    _str(s.get("session_type")),
                    _dash(s.get("model")),
                    _str(s.get("auto_approve")),
                    _dash(s.get("permission_mode")),
                    _str(s.get("remote_control_enabled")),
                    _bool(s.get("archived_at")),
                ),
                s.get("created_at"),
                **cols,
            )
            if s.get("forked_from_session_id") not in (None, ""):
                yield self._row(
                    artifact,
                    "forked from session %s" % _str(s.get("forked_from_session_id")),
                    s.get("created_at"),
                    **cols,
                )
        for a in select("activity_items"):
            yield self._row(
                artifact,
                "activity %s: %s" % (_str(a.get("activity_type")), _str(a.get("preview"))),
                a.get("created_at"),
                session_id=_str(a.get("session_id")),
            )
        for c in select("session_checkpoints"):
            yield self._row(
                artifact,
                "checkpoint commit %s" % _str(c.get("commit_sha")),
                c.get("created_at"),
                session_id=_str(c.get("session_id")),
            )

    def _schedule_rows(self, artifact, select):
        for t in select("my_copilot_scheduled_tasks"):
            yield self._row(
                artifact,
                "scheduled task: %s enabled=%s mode=%s agent=%s prompt: %s"
                % (
                    _str(t.get("title")),
                    _str(t.get("enabled")),
                    _str(t.get("execution_mode")),
                    _str(t.get("background_agent_type")),
                    _str(t.get("prompt")),
                ),
                t.get("created_at"),
            )
        for t in select("my_copilot_scheduled_task_triggers"):
            yield self._row(
                artifact,
                "scheduled task trigger: task=%s kind=%s enabled=%s next_run_at=%s config: %s"
                % (
                    _str(t.get("task_id")),
                    _str(t.get("kind")),
                    _str(t.get("enabled")),
                    _dash(t.get("next_run_at")),
                    _str(t.get("config_json")),
                ),
                t.get("created_at"),
            )
        for i in select("my_copilot_scheduled_task_invocations", "claimed_at"):
            yield self._row(
                artifact,
                "scheduled task run: %s status=%s source=%s scheduled_for=%s prompt: %s"
                % (
                    _str(i.get("task_title")),
                    _str(i.get("status")),
                    _str(i.get("source")),
                    _dash(i.get("scheduled_for")),
                    _str(i.get("prompt_snapshot")),
                ),
                i.get("claimed_at"),
                session_id=_str(i.get("parent_session_id")),
            )
        for a in select("session_automations", "updated_at"):
            yield self._row(
                artifact,
                "session automation: %s interval=%s every_minutes=%s next_run_at=%s prompt: %s"
                % (
                    _dash(a.get("name")),
                    _str(a.get("interval")),
                    _dash(a.get("every_minutes")),
                    _dash(a.get("next_run_at")),
                    _str(a.get("prompt")),
                ),
                a.get("updated_at"),
                session_id=_str(a.get("session_id")),
            )
        for d in select("session_deletion_intents"):
            yield self._row(
                artifact,
                "session deletion requested",
                d.get("created_at"),
                session_id=_str(d.get("session_id")),
            )
