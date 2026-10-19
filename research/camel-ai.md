# camel-ai

CAMEL is a multi-agent Python framework (package `camel-ai`) with toolkits for the terminal,
browser, Gmail and files. This document came out of the agent framework sweep for
[issue #64](https://github.com/seanthegeek/doubleagent/issues/64); see
[`collectors/research/frameworks.md`](frameworks.md) for the frameworks that got no catalog
line. There is no analyzer document: CAMEL keeps no transcripts under the home.

## 1. Source and evidence

[camel-ai/camel](https://github.com/camel-ai/camel), Apache-2.0, open source, commit
[`24fde60ad739b4be8f8f533fea9ba54256fbc4a2`](https://github.com/camel-ai/camel/commit/24fde60ad739b4be8f8f533fea9ba54256fbc4a2)
(2026-10-05), package `camel-ai` 0.2.91a7. All claims are from source.

CAMEL runs shell commands on the host: the terminal toolkit's `shell_exec`
uses `subprocess.Popen`
([terminal_toolkit.py:757](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/terminal_toolkit/terminal_toolkit.py#L757),
[838](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/terminal_toolkit/terminal_toolkit.py#L838)).

### Observed

- No real install: nothing was installed or run.

### Source reviews

- **Source review (2026-10-19)** at
  [`797296a`](https://github.com/camel-ai/camel/commit/797296a718ce856d9c9476e4bb69fedb71ab6382)
  (package version unchanged, 0.2.91a7), against `24fde60` above. One
  line per class:
  - Permission: none on disk. The terminal toolkit's `safe_mode`,
    `allowed_commands` and `require_approval` callback are constructor
    arguments of the calling program
    ([terminal_toolkit.py:143-148](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/toolkits/terminal_toolkit/terminal_toolkit.py#L143-L148),
    [200-206](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/toolkits/terminal_toolkit/terminal_toolkit.py#L200-L206)),
    and no decision is written anywhere.
  - Model: none on disk; the model is chosen in code, and model logs are
    opt-in (`CAMEL_MODEL_LOG_ENABLED`, `CAMEL_LOG_DIR` default
    `camel_logs` in the working directory,
    [base_model.py:287-295](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/models/base_model.py#L287-L295)).
  - Past use: none under the home. New since `24fde60`: `ChatAgent`
    takes a `tool_log_dir` that saves full tool outputs, a caller-chosen
    directory with no default
    ([chat_agent.py:640-644](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/agents/chat_agent.py#L640-L644));
    `save_memory(path)` and `JsonStorage` write where the caller says
    ([chat_agent.py:1780](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/agents/chat_agent.py#L1780),
    [json.py:72](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/storages/key_value_storages/json.py#L72)).
  - Sync, relay and origin: none (not found in `camel/` at `797296a`,
    grepped for `share_url`, `upload_trajectory` and `sync_to`). The
    Gmail token lets an agent read and send mail, which is a tool, not a
    relay of the session.
  - Scratch directories ([Scratch directories](#scratch-directories)): `./workspace`
    (terminal toolkit) and `./camel_working_dir` (file toolkits) in the working directory
    ([terminal_toolkit.py:185-195](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/toolkits/terminal_toolkit/terminal_toolkit.py#L185-L195),
    [file_toolkit.py:73](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/toolkits/file_toolkit.py#L73)),
    unrecorded and under no CAMEL-specific name, so no catalog line can
    find them.
  - Deletion: nothing to delete; the framework keeps no session.
  - Version drift: the home paths are unchanged
    (`.camel/gmail_token.json`,
    [gmail_toolkit.py:1316](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/toolkits/gmail_toolkit.py#L1316);
    `.camel/skills` and `.config/camel/skills`,
    [skill_toolkit.py:206-207](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/toolkits/skill_toolkit.py#L206-L207);
    `.camel/runtimes`,
    [runtime_utils.py:57](https://github.com/camel-ai/camel/blob/797296a718ce856d9c9476e4bb69fedb71ab6382/camel/toolkits/terminal_toolkit/runtime_utils.py#L57));
    line numbers moved.
  - Bad lines: no parser.

  The "nothing to parse" verdict stands.

## Collection

### 2. Per-user storage

| Path (home-relative, all OSes) | Holds | Default or opt-in |
| --- | --- | --- |
| `.camel/gmail_token.json` | Google OAuth token and refresh token, mode 0600 ([gmail_toolkit.py:1316](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/gmail_toolkit.py#L1316), [1390-1402](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/gmail_toolkit.py#L1390-L1402)) | default when `GmailToolkit` is used |
| `.camel/skills`, `.config/camel/skills` | user-scope skills, read ([skill_toolkit.py:201-209](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/skill_toolkit.py#L201-L209)) | read by default by `SkillToolkit` |
| `.camel/runtimes/{go,java}` | downloaded Go and JDK toolchains ([runtime_utils.py:57](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/terminal_toolkit/runtime_utils.py#L57), [terminal_toolkit.py:457-466](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/terminal_toolkit/terminal_toolkit.py#L457-L466)) | default when the terminal toolkit needs them; not collected |

Everything else is relative to the working directory: `./workspace` for
the terminal toolkit
([terminal_toolkit.py:188-195](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/terminal_toolkit/terminal_toolkit.py#L188-L195)),
`./camel_working_dir` for the file toolkits
([file_toolkit.py:69-73](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/toolkits/file_toolkit.py#L69-L73)),
`./chat_history.json` for `JsonStorage`
([json.py:71-73](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/storages/key_value_storages/json.py#L71-L73)),
and `camel_logs` model logs only with `CAMEL_MODEL_LOG_ENABLED`
([base_model.py:287-295](https://github.com/camel-ai/camel/blob/24fde60ad739b4be8f8f533fea9ba54256fbc4a2/camel/models/base_model.py#L287-L295)).
The browser `user_data_dir` is supplied by the caller.

#### Scratch directories

The terminal toolkit's `./workspace` and the file toolkits' `./camel_working_dir` are the
agent's own scratch space, created in the working directory, unrecorded and under no
CAMEL-specific name, so no catalog line can find them.

#### Name collision

Apache Camel JBang also uses `~/.camel`
(`CAMEL_DIR = ".camel"` resolved under the home,
[CommandLineHelper.java:44](https://github.com/apache/camel/blob/43fb0300bd10fa74ef37f3eca82d20678b6d3350/dsl/camel-jbang/camel-jbang-core/src/main/java/org/apache/camel/dsl/jbang/core/common/CommandLineHelper.java#L44),
[221-222](https://github.com/apache/camel/blob/43fb0300bd10fa74ef37f3eca82d20678b6d3350/dsl/camel-jbang/camel-jbang-core/src/main/java/org/apache/camel/dsl/jbang/core/common/CommandLineHelper.java#L221-L222)),
so a bare `.camel` entry would collect JBang's state as `camel-ai`. The
catalog names only `.camel/gmail_token.json` and `.camel/skills`, plus the
CAMEL-only `.config/camel`.

#### Docker

No compose file or named volume.

### 3. Credentials

- `.camel/gmail_token.json`: flagged.

### 4. Exclusions

`.camel/runtimes` would need one only if `.camel` were collected whole; it
is not, so none.

### 5. Project-local files

The working-directory files in [section 2](#2-per-user-storage) (`workspace/`,
`camel_working_dir/`, `chat_history.json`) are created wherever the
application runs, under no CAMEL-specific name, so they are not project
catalog entries.

### 6. Where the project path is recorded

Nowhere under the home.

## Parsing

The agent has no analyzer research document: nothing it writes is parsed, or
its parser is still in the backlog (see the agents page).
<!-- MERGE: write the one-paragraph parsing status -->

## 14. Confidence

High for every path (source). The catalog lines are of low value apart
from the OAuth token, which shows that a Google account was granted to a
CAMEL agent.
