"""Roo Code transcripts.

Validated against source (RooCodeInc/Roo-Code at b867ec91, see
`analyzer/research/roo-code.md`) with a synthetic fixture; no real install.

Roo Code forked Cline and keeps its per-task layout, so the transcript files
are read by the shared mapping in `cline_legacy.py`, whose docstring lists
the fields. Roots: the extension's
`<editor>/User/globalStorage/rooveterinaryinc.roo-cline/` and the CLI's
`~/.vscode-mock/global-storage/`. A root moved with the
`roo-cline.customStoragePath` setting is not found.

* `tasks/<taskId>/ui_messages.json`, `api_conversation_history.json` (or
  the pre-rename `claude_messages.json`) and `task_metadata.json`, as in
  Cline. Roo's differences: the task prompt is the first `say: "text"`
  record (there is no `say: "task"`), `condense_context` carries
  `contextCondense {summary, prevContextTokens, newContextTokens, cost}`,
  API history records carry their own `ts`, and `task_metadata.json` holds
  only `files_in_context` with `roo_read_date` and `roo_edit_date`. The task
  id is a UUID, so API history records without `ts` inherit the
  `HistoryItem.ts`.
* `tasks/<taskId>/history_item.json`: one `HistoryItem {id, ts, task,
  tokensIn, tokensOut, totalCost, size, workspace, mode, status,
  apiConfigName, parentTaskId, rootTaskId}`. One `system` row; `workspace`
  is the task's project path.
* `tasks/_index.json`: `{version, updatedAt, entries: HistoryItem[]}`. A
  `system` row only for entries whose `history_item.json` is not on disk,
  so a deleted task still shows without doubling the others.
* `.roo/cli-history.json`, the Roo CLI's input history (the `.roo` directory
  is `getConfigDir()`): `{version: 1, entries: string[]}`, every line
  submitted in the interactive CLI (a task prompt, a follow-up answer, a
  slash command such as `/new`), trimmed, oldest first, consecutive
  duplicates and empty lines skipped, capped at the newest 500. One `user`
  row per string entry in file order, `source_line` the 1-based entry
  index; non-string and blank entries are skipped as the CLI's own
  `loadHistory` skips them. A file cut mid-write yields the entries before
  the cut and one `system` row for the cut (issue 136): the entry that
  does not decode, `parser: unparseable record <N> (<reason>): <raw>` with
  the text from its first character to the end of the file, or `parser: array cut off after record N` when the cut falls
  between entries; a file with no `entries` array is one `system` row. The file records no time, no task id
  and no workspace, so the rows have an empty `timestamp_utc`,
  `session_id` and `project_path`. A secondary source (`dedup.py`): each
  row matches a task's `user` row (the prompt's `say: "text"` or a
  `user_feedback`) on text alone, any task, and is kept only when no task
  has the text, which recovers a prompt whose task directory was deleted.

No model name is recorded anywhere in Roo transcripts (`apiConfigName` is a
profile name), so `model` is always empty. No git branch is recorded.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ..inputs import Artifact
from ..model import Row
from .base import Options, error_rows
from .cline_legacy import LegacyTaskParser, iter_array_at, load_json, read_text

ROOT = r"(?:(?:.*/)?User/globalStorage/rooveterinaryinc\.roo-cline|\.vscode-mock/global-storage)"
ITEM_RX = re.compile(r"^%s/tasks/[^/]+/history_item\.json$" % ROOT, re.I)
INDEX_RX = re.compile(r"^%s/tasks/_index\.json$" % ROOT, re.I)
CLI_HISTORY_REL = ".roo/cli-history.json"
ENTRIES_KEY_RX = re.compile(r'"entries"\s*:\s*(?=\[)')
ITEM_FILE = "history_item.json"


class RooCodeParser(LegacyTaskParser):
    agent = "roo-code"
    name = "roo-code"
    ROOT = ROOT
    PROJECT_KEY = "workspace"

    def wants(self, artifact: Artifact) -> bool:
        return bool(
            self.task_match(artifact)
            or ITEM_RX.match(artifact.rel)
            or INDEX_RX.match(artifact.rel)
            or artifact.rel == CLI_HISTORY_REL
        )

    def secondary(self, artifact: Artifact) -> bool:
        return artifact.rel == CLI_HISTORY_REL

    def history_item(self, task_dir: Path, root: Path, task_id: str) -> dict | None:
        item = load_json(task_dir / ITEM_FILE)
        if isinstance(item, dict):
            return item
        index = self.cached_json(root / "tasks" / "_index.json")
        entries = index.get("entries") if isinstance(index, dict) else None
        if isinstance(entries, list):
            for e in entries:
                if isinstance(e, dict) and str(e.get("id")) == task_id:
                    return e
        return None

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if self.task_match(artifact):
            yield from self.parse_task_file(artifact, opts)
        elif ITEM_RX.match(artifact.rel):
            item = load_json(artifact.disk_path)
            if isinstance(item, dict):
                yield self.history_row(artifact, item, 1, opts)
            else:
                yield from error_rows(
                    self,
                    artifact,
                    [(0, "history_item.json is not a JSON object", "")],
                    artifact.disk_path.parent.name,
                )
        elif INDEX_RX.match(artifact.rel):
            yield from self._parse_index(artifact, opts)
        elif artifact.rel == CLI_HISTORY_REL:
            yield from self._parse_cli_history(artifact)

    def _parse_cli_history(self, artifact: Artifact) -> Iterator[Row]:
        errors: list = []
        data = load_json(artifact.disk_path)
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            entries = enumerate(data["entries"], 1)
        else:
            # Cut mid-write (the CLI rewrites the whole file per prompt): walk
            # the entries array as far as it parses.
            s = read_text(artifact.disk_path) if data is None else None
            m = ENTRIES_KEY_RX.search(s) if s is not None else None
            if m and s is not None:
                entries = iter_array_at(s, m.end(), errors)
            else:
                errors.append((0, "cli-history.json has no entries array", ""))
                entries = iter(())
        for n, entry in entries:
            if not isinstance(entry, str) or not entry.strip():
                continue
            row = self.base_row(artifact)
            row.source_line = n
            row.turn_type = "user"
            row.text = entry
            yield row
        if data is None and not errors:
            errors.append((0, "cli-history.json unparseable after its entries array", ""))
        yield from error_rows(self, artifact, errors)

    def _parse_index(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        index = load_json(artifact.disk_path)
        if not isinstance(index, dict) or not isinstance(index.get("entries"), list):
            yield from error_rows(self, artifact, [(0, "_index.json has no entries array", "")])
            return
        tasks = artifact.disk_path.parent
        for n, e in enumerate(index["entries"], 1):
            if not isinstance(e, dict):
                continue
            tid = str(e.get("id") or "")
            if tid and (tasks / tid / ITEM_FILE).is_file():
                continue
            yield self.history_row(artifact, e, n, opts)
