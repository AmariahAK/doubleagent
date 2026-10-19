# shellgpt

ShellGPT (`sgpt`, catalog name `shellgpt`) is an open-source Python command-line client for
OpenAI-compatible chat APIs. It stores a named chat or REPL session as the raw OpenAI `messages`
array it sends to the API, one JSON file per session, with no timestamps, model or working
directory. Paths cited are relative to the clone. Storage locations are in
[`collectors/research/shellgpt.md`](../../collectors/research/shellgpt.md).

## 1. Source and evidence

[TheR1D/shell_gpt](https://github.com/TheR1D/shell_gpt) at
[`a082bd5327ce0c4ef5a0284d9060e833be9444a6`](https://github.com/TheR1D/shell_gpt/commit/a082bd5327ce0c4ef5a0284d9060e833be9444a6)
(2026-07-02), version 1.5.1, MIT. Open source.

### Observed

No real install.

### Source reviews

- **Source review (2026-10-19).** HEAD of the default branch is still
  [`a082bd5`](https://github.com/TheR1D/shell_gpt/commit/a082bd5327ce0c4ef5a0284d9060e833be9444a6),
  the commit above, so nothing has drifted. The per-class detail, one line per requirement
  class, is in the subsections of [section 8](#8-parser-plan).
  - Permission state: found, not parsed. A function call the model
    asks for runs with no prompt at all; the standing switches are
    `.sgptrc` keys. The `--shell` `[E]xecute, [M]odify, [D]escribe,
    [A]bort` choice and the REPL's `e` are not recorded. Detail in
    [Permission state](#permission-state).
  - Model: found, not parsed: `DEFAULT_MODEL` in `.sgptrc` is the only
    record; a `--model` option leaves none.
  - Past use: found. The response cache holds the assistant text of
    chat turns as well as one-shot answers and outlives the chat file;
    not parsed, and not collected at its current Windows path.
  - Sync, relay and origin: already covered (none).
  - Scratch directories: none; sgpt runs in the caller's directory and
    records none.
  - Deletion: no delete command. The chat id `temp` is deleted at each
    use, a chat file keeps only its last 100 messages, the response
    cache its newest 100 files, and the operating system's temp cleanup
    removes the rest.
  - Version drift: none.
  - Bad lines: covered (a truncated array yields the messages before
    the cut and one `system` row).

## 2. Transcript stores

- `<CHAT_CACHE_PATH>/<chat id>`: one file per session started with `--chat <id>` or `--repl <id>`,
  named exactly as typed, no extension
  ([`sgpt/handlers/chat_handler.py:65-78`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L65-L78)).
  `CHAT_CACHE_PATH` defaults to `tempfile.gettempdir()/chat_cache`
  ([`sgpt/config.py:14`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L14),
  [`20`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L20));
  before 0.9.0 it was `gettempdir()/shell_gpt/chat_cache`, and `.sgptrc` keeps whichever value was
  written at first run. Home-relative globs the catalog can reach: `AppData/Local/Temp/chat_cache/*`
  and `AppData/Local/Temp/shell_gpt/chat_cache/*` (Windows). On Linux and macOS the files are under
  `/tmp` or `/var/folders/*/*/T` and arrive only as loose input.
- The id `temp` is invalidated at each start, so it holds only the most recent throwaway session
  ([`chat_handler.py:106-108`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L106-L108)).

### What survives a delete

ShellGPT has no delete command. What removes chat history is the `temp` chat id, invalidated at each
start; the cut on every write that keeps the system message and the last 100 other messages
([`chat_handler.py:75-77`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L75-L77));
and the operating system's cleanup of its temporary directory, where the chat files live by default.
A per-prompt history file is not stated. The response cache under `<CACHE_PATH>` keeps the answers
to chat turns that the cut dropped, and to one-shot prompts that never had a chat file, as text with
no prompt, time or session, the newest 100 files kept
([`cache.py:46-61`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/cache.py#L46-L61));
its Windows path since 0.9.0, `AppData/Local/Temp/cache`, is named by no catalog line. Deletion
markers are not stated. The analyzer reads the chat files and not the response cache, a secondary
source joined on text only (see [Secondary sources](../docs/output.md#secondary-sources)).

## 3. Record schema

The file is a single JSON array written by `json.dump` with default settings (one line,
ASCII-escaped)
([`chat_handler.py:72-78`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L72-L78)).
Each element is an OpenAI chat message:

- `{"role":"system","content":str}`: always element 0, written only when the session is new
  ([`chat_handler.py:165-170`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L165-L170)).
  The content is `"You are <role name>\n<role text>"`
  ([`sgpt/role.py:44`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/role.py#L44),
  [`role.py:150-153`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/role.py#L150-L153));
  sgpt itself parses the role name back from the first line
  ([`role.py:106-112`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/role.py#L106-L112)).
- `{"role":"user","content":str}`: the prompt. In REPL mode the first prompt is prefixed with any
  stdin or command-line prompt separated by three newlines
  ([`repl_handler.py:53-55`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/repl_handler.py#L53-L55)).
- `{"role":"assistant","content":null,"tool_calls":[{"id","type":"function","function":{"name","arguments"}}]}`:
  a function call; `arguments` is a JSON string
  ([`sgpt/handlers/handler.py:72-84`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L72-L84)).
  Only one call per turn (`parallel_tool_calls` is false;
  [`handler.py:118-121`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L118-L121)).
- `{"role":"tool","content":str,"tool_call_id":str}`: the function's return value
  ([`handler.py:98-100`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L98-L100)).
  For the bundled `execute_shell_command` it is `"Exit code: <n>, Output:\n<stdout+stderr>"`
  ([`llm_functions/common/execute_shell.py:18-25`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/llm_functions/common/execute_shell.py#L18-L25)).
- `{"role":"assistant","content":str}`: the full streamed response, appended after the call returns
  ([`chat_handler.py:56-61`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L56-L61)).
  When a function was called it also contains the marker line `` > @FunctionCall `name(k="v")` ``
  and, with `SHOW_FUNCTIONS_OUTPUT=true`, the output in a fenced block
  ([`handler.py:89-95`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L89-L95)).

So a turn with a function call is stored as user, assistant(tool_calls),
tool, assistant(content), in that order, because the handler mutates the
same list the session later writes.

Truncation: on every write the system message is kept and only the last `CHAT_CACHE_LENGTH` (default
100) other messages survive
([`chat_handler.py:75-77`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L75-L77);
[`config.py:22`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L22)).
Older turns of a long session are gone, and a cut can separate a `tool` message from its call.

## 4. Joins and timestamps

- Session to project: none recorded.
- Tool call to result: `tool_calls[0].id` equals the next `tool`
  message's `tool_call_id`.
- No subagents. Session id is the file name.

No timestamp, model, temperature or cwd is stored. The only time is the
file's mtime, which is the last write. The file is rewritten in full each
turn.

## 5. Other stores

No SQLite or binary store.

### Response cache

`<CACHE_PATH>/<md5>` files hold only a response string with no prompt
([`sgpt/cache.py:30-41`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/cache.py#L30-L41)).
Not a transcript; do not parse. `get_completion` of every handler, the chat handler included, is
wrapped by the cache decorator, which writes the full response text to
`<CACHE_PATH>/<md5 of the request>` unless it contains a function call
([`handler.py:102-110`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L102-L110);
[`sgpt/cache.py:30-44`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/cache.py#L30-L44)).
So the answers to chat turns that the 100-message cut dropped, and to one-shot prompts that have no
chat file, survive there as text with no prompt, time or session; they join on text only. The newest
100 files are kept
([`cache.py:46-61`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/cache.py#L46-L61)).
Its Windows path since 0.9.0 is `AppData/Local/Temp/cache`, which no catalog line names.

### Settings file and function store

`.sgptrc` keys `OPENAI_USE_FUNCTIONS` (default `true`: function calls allowed),
`DEFAULT_EXECUTE_SHELL_CMD` (default `false`; `true` makes Execute the default answer) and
`SHELL_INTERACTION` (default `true`; `false` skips the prompt)
([`sgpt/config.py:29`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L29),
[33](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L33),
[38](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L38);
read at
[`app.py:60-61`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/app.py#L60-L61),
[79-80](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/app.py#L79-L80),
[247](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/app.py#L247)).
The environment override of `SHELL_INTERACTION` reads the variable `"SHELL_INTERACTION "`, with a
trailing space, so only the file value takes effect in practice. The functions the model may call
are the `*.py` files in `~/.config/shell_gpt/functions/`, which `--install-functions` fills with
`execute_shell.py`
([`sgpt/llm_functions/init_functions.py:13-22`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/llm_functions/init_functions.py#L13-L22)).

`.sgptrc` `DEFAULT_MODEL` (default `gpt-5.4-mini`,
[`config.py:25`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L25))
is the model used when no `--model` was given; nothing records a per-call choice.

## 6. Format versions

No version field. Function calls arrived in 1.1.0
([`20ff0f2`](https://github.com/TheR1D/shell_gpt/commit/20ff0f2eeb26ee816bfd31d2fd0d67da6f1e861f))
using the legacy `functions` API: the call was stored as
`{"role":"assistant","content":"","function_call":{"name","arguments"}}` and the result as
`{"role":"function","content":str,"name":str}`, with no call id
([`handler.py:65-71`](https://github.com/TheR1D/shell_gpt/blob/6bd0bdebe1f321e397099e430e8ecd93beb965b6/sgpt/handlers/handler.py#L65-L71),
[`83`](https://github.com/TheR1D/shell_gpt/blob/6bd0bdebe1f321e397099e430e8ecd93beb965b6/sgpt/handlers/handler.py#L83)
at [`6bd0bde`](https://github.com/TheR1D/shell_gpt/commit/6bd0bdebe1f321e397099e430e8ecd93beb965b6),
the parent of the change below). 1.5.0 switched to `tool_calls` and `tool` messages
([`4ea2f83`](https://github.com/TheR1D/shell_gpt/commit/4ea2f834cff5dc020dabb25bb02030c630cd2062),
"Migrate to OpenAI v2"). A parser must accept both: pair a `function` message with the immediately
preceding `function_call` by position. Before 1.1.0 files hold only system, user and assistant
messages.

## 7. Secrets

The API key is never written into chat files; it is in `.sgptrc`
([`config.py:63-69`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L63-L69)).
Tool messages contain raw shell output and can contain anything the commands printed.

## 8. Parser plan

Detection: any regular file directly under a `chat_cache` directory whose
content parses as a JSON array of objects with `role`.

| Column | Source |
| --- | --- |
| timestamp_utc | empty; the manifest `mtime` may be given to the last row only |
| session_id | file name |
| project_path | empty |
| git_branch | empty |
| turn_type | `user` → user; `assistant` with `content` → assistant; each `tool_calls[]` → tool_use; `tool` → tool_result; `system` → system |
| model | empty |
| tool_name | `tool_calls[].function.name` |
| tool_use_id | `tool_calls[].id` / `tool_call_id` |
| text | `content`; for tool_use, `shell_command` from the parsed `arguments` when present, else `arguments` |
| source_line | 1 for every row (single-line file); the array index can go in the text or a later column |

### Permission state

Per call: none recorded, and none asked for function calls. `handle_function_call` appends the call,
runs `get_function(name)(**dict_args)` and appends the result with no confirmation
([`sgpt/handlers/handler.py:64-100`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L64-L100)),
so every `tool_use` row in a chat file is a command that ran. The `--shell` prompt
`[E]xecute, [M]odify, [D]escribe, [A]bort` runs the generated command with `run_command` after the
answer is written and records the choice nowhere
([`sgpt/app.py:243-260`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/app.py#L243-L260)),
nor does the REPL's `e` in the shell role
([`sgpt/handlers/repl_handler.py:56-59`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/repl_handler.py#L56-L59)).

Standing (proposed, not parsed): the `.sgptrc` switches and the function store described in
[Settings file and function store](#settings-file-and-function-store).
Proposed: one `permission setting: <key>=<value> (from .sgptrc, file
mtime)` row per key and one `permission setting: function <file name>
(from .config/shell_gpt/functions, file mtime)` row per installed
function, the API key never read. `.sgptrc` is a secret glob, so a
`--no-secrets` collection lacks it.

### Model

ShellGPT records no model in the chat cache, so the parser yields no
`model:` rows. The configured default is `DEFAULT_MODEL` in `.sgptrc`
([Settings file and function store](#settings-file-and-function-store)). Proposed: one
`model: <DEFAULT_MODEL> (configured default, from .sgptrc, file mtime)` row; not a per-session
model.

### Past use and secondary sources

The response cache (secondary, not parsed), described in [Response cache](#response-cache):
the answers to chat turns that the 100-message cut dropped and to one-shot prompts, as text that
joins on text only.

### Sync, relay and origin

The agent records none. ShellGPT records no sync state, because it has no feature that uploads a
session. Its only network client is the chat completion call: the OpenAI client pointed at
`API_BASE_URL`, or `litellm.completion` when `USE_LITELLM=true` (LiteLLM is a third-party library
that routes one call format to many model providers)
([`handler.py:15-33`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L15-L33)),
which sends the session's messages with each prompt and nothing else
([`handler.py:123-130`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L123-L130)).
The runtime dependencies are `openai`, `typer`, `click`, `rich`, `distro`, `pyreadline3` and
`prompt_toolkit`, with `litellm` optional
([`pyproject.toml:26-39`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/pyproject.toml#L26-L39));
no HTTP library, telemetry or crash reporter.

The command-line options for sessions are `--chat`, `--repl`, `--show-chat` and `--list-chats`, all
local
([`app.py:98-119`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/app.py#L98-L119)),
and the session store reads, writes, lists and deletes files in `CHAT_CACHE_PATH` only
([`chat_handler.py:65-95`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/chat_handler.py#L65-L95)).
No setting in `DEFAULT_CONFIG` names a sync, share or account
([`config.py:18-46`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/config.py#L18-L46)).
The terms `sync`, `share`, `upload`, `cloud`, `remote`, `publish`, `telemetry`, `analytics`,
`export`, `backup`, `team`, `account`, `login`, `requests`, `httpx`, `urllib`, `socket` and `sentry`
match nothing in `sgpt/`, and the only URLs in `sgpt/` and `pyproject.toml` are the project's own
GitHub links.

Two paths are outside this source: what LiteLLM itself sends when it is enabled (ShellGPT sets only
`suppress_debug_info` on it) and what a user-installed function under
`~/.config/shell_gpt/functions/` does, since each is arbitrary Python imported at start
([`function.py:31-36`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/function.py#L31-L36)).

### Scratch directories

None; sgpt runs in the caller's directory and records none.

### Deletion

No delete command; see [section 2](#2-transcript-stores) and
[What survives a delete](#what-survives-a-delete) for `temp`, and [section 3](#3-record-schema)
for the truncation. The parser yields no deletion rows.

### Bad lines

Covered: a truncated array yields the messages before the cut and one `system` row. The
response cache, if parsed, is one text per file with nothing to cut.

### Fixtures

Fixture (`chat_cache/deploy-check`, shown wrapped; the real file is one line):

```json
[{"role": "system", "content": "You are ShellGPT\nYou are programming and system administration assistant.\nYou are managing Linux/Ubuntu 24.04 LTS operating system with bash shell.\nAPPLY MARKDOWN formatting when possible."},
 {"role": "user", "content": "what is listening on port 8080"},
 {"role": "assistant", "content": null, "tool_calls": [{"id": "call_Q1w2e3r4", "type": "function", "function": {"name": "execute_shell_command", "arguments": "{\"shell_command\": \"ss -ltnp | grep 8080\"}"}}]},
 {"role": "tool", "content": "Exit code: 0, Output:\nLISTEN 0 4096 0.0.0.0:8080 0.0.0.0:* users:((\"python3\",pid=4242,fd=3))\n", "tool_call_id": "call_Q1w2e3r4"},
 {"role": "assistant", "content": "\n> @FunctionCall `execute_shell_command(shell_command=\"ss -ltnp | grep 8080\")` \n\nA python3 process (PID 4242) is listening on 8080."}]
```

### Confidence

High: file location, array shape, message keys, ordering, truncation (source), and the leading
`"\n"` before the marker, which is always emitted because the check runs right after the assistant
message is appended
([`handler.py:86-87`](https://github.com/TheR1D/shell_gpt/blob/a082bd5327ce0c4ef5a0284d9060e833be9444a6/sgpt/handlers/handler.py#L86-L87)).
Medium: the pre-1.5.0 shape, read from the parent of
[`4ea2f83`](https://github.com/TheR1D/shell_gpt/commit/4ea2f834cff5dc020dabb25bb02030c630cd2062) in
history rather than a released package.
