# aider

Aider (catalog agent `aider`) is a terminal pair-programming CLI that works inside a git
repository (or the current directory) and keeps its chat and prompt history there as plain-text
files, with a few optional files under the home, so most of its evidence is project-level. It
shares no storage or format with another agent. Paths cited are relative to the clone. The agent
is parsed: the `aider` parser reads the chat history as the primary store and the input and LLM
histories as secondary sources ([section 13](#13-parser-plan)).

## 1. Source and evidence

[Aider-AI/aider](https://github.com/Aider-AI/aider), open source, commit
[`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`](https://github.com/Aider-AI/aider/commit/5dc9490bb35f9729ef2c95d00a19ccd30c26339c),
Apache-2.0
([`LICENSE.txt`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/LICENSE.txt)).
All claims from source; the config-key example is from the shipped docs in the same tree. The input
history format comes from the upstream prompt_toolkit `history.py`, which is not vendored.

### Observed

- No real install.

### Source reviews

- **Source review (2026-10-19).** The head of
  [Aider-AI/aider](https://github.com/Aider-AI/aider) `main` on
  2026-10-19 is still
  [`5dc9490`](https://github.com/Aider-AI/aider/commit/5dc9490bb35f9729ef2c95d00a19ccd30c26339c),
  the commit cited throughout, so every path here holds and there is no drift; the review read the
  writers again for each requirement class. Source only. By class:
  - Permission state: found, not read as decisions. Every confirmation
    is written to the chat history as a blockquote line holding the
    question, its options and the answer
    ([section 8](#8-record-schema)); the standing grant is `yes-always`
    in an `.aider.conf.yml` ([section 2](#2-per-user-storage)) or `--yes-always`, under which the
    answer is
    written as if typed. "Don't ask again" lasts the run only.
  - Model: found, not read. The startup announcements written to the
    chat history name the main, weak and editor models
    ([section 8](#8-record-schema)), and each `/model`, `/weak-model`
    or `/editor-model` switch writes them again; there is no separate file. The earlier statement
    that the files record no model was wrong.
  - Past use: covered (the input and LLM histories); no other store
    found and no new file.
  - Sync, relay and origin: covered; none, and no new file.
  - Scratch directories: none ([Scratch directories](#scratch-directories)). Aider works in the git
    root or cwd; the only directory it makes is a system temporary directory for an image pasted
    with `/paste`
    ([`commands.py:1295-1298`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L1295-L1298)).
  - Deletion: covered; `/clear` and `/reset` empty the in-memory chat and leave every file
    ([`commands.py:439-443`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L439-L443)).
  - Version drift: none.
  - Bad lines: not a collector concern; covered by the parser.

## Collection

### 2. Per-user storage

Aider has no platform branching; everything is `Path.home()` (`%USERPROFILE%` on Windows), so the
layout is identical on Linux, macOS and Windows. No `XDG` use.

Home-level files, all optional:

- `~/.aider.conf.yml`: the config search is cwd, git root, home
  ([`aider/main.py:464-477`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L464-L477);
  [`aider/args.py:790-796`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L790-L796)),
  or `--config`.
- `~/.aider.model.settings.yml` and `~/.aider.model.metadata.json`: `generate_search_path_list`
  tries home, git root, then cwd or the `--model-settings-file`/`--model-metadata-file` value
  ([`main.py:305-310`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L305-L310),[`336-338`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L336-L338),[`397-399`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L397-L399);
  defaults
  [`args.py:121-131`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L121-L131)).
- `~/.env`: `load_dotenv_files` loads `~/.env`, `<git root>/.env`, then `.env` in cwd or
  `--env-file`
  ([`main.py:361-385`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L361-L385);
  [`args.py:31-32`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L31-L32),[`801-804`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L801-L804)).
  This is a shared dotfile, not aider-owned.
- `~/.aider/oauth-keys.env`: loaded first
  ([`main.py:370-374`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L370-L374)),
  written by the OpenRouter OAuth flow
  ([`aider/onboarding.py:363-367`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/onboarding.py#L363-L367)).
- `~/.aider/analytics.json`: anonymous `uuid` and disable flag
  ([`aider/analytics.py:139-152`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L139-L152)).
  `--analytics-log <file>` writes JSONL events wherever the user says
  ([`args.py:575-578`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L575-L578)).
- `~/.aider/caches/`: `model_prices_and_context_window.json`
  ([`aider/models.py:169-170`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/models.py#L169-L170)),
  `openrouter_models.json`
  ([`aider/openrouter.py:34-35`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/openrouter.py#L34-L35)),
  `versioncheck`
  ([`aider/versioncheck.py:12`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/versioncheck.py#L12)),
  `help.<version>/` llama-index embedding store
  ([`aider/help.py:93`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/help.py#L93)).
- History files default to the git root ([section 5](#5-project-local-files)); when aider runs
  outside a repository they land in the cwd
  ([`args.py:271-276`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L271-L276)),
  so `~/.aider.chat.history.md` and friends exist only for sessions started in the home directory.
- At [`5dc9490`](https://github.com/Aider-AI/aider/commit/5dc9490bb35f9729ef2c95d00a19ccd30c26339c)
  (source review of 2026-10-19): `.aider.conf.yml` at any level can set `yes-always: true`, which
  answers yes to every confirmation without asking
  ([`aider/args.py:760-764`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L760-L764));
  collected with the file.

No relocation environment variable; everything is `--option` or config-file driven. `pip`/`uv`
install directories are out of scope.

#### Scratch directories

None known: Aider works in the git root or the cwd and makes no working directory of its own; the
only directory it creates is a system temporary directory for an image pasted with `/paste`
([`aider/commands.py:1295-1298`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L1295-L1298)),
outside every catalog line. `/clear` and `/reset` delete no file; what remains is in
[What survives a delete](#what-survives-a-delete).

### 3. Credentials

- `~/.aider/oauth-keys.env`: `OPENROUTER_API_KEY="..."` appended in plaintext
  ([`onboarding.py:365-367`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/onboarding.py#L365-L367)).
- `.aider.conf.yml` at any of the three levels accepts `openai-api-key`, `anthropic-api-key`,
  `api-key: provider=key` and `set-env`
  ([`args.py:69-110`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L69-L110);
  documented example
  [`aider/website/docs/config/aider_conf.md:81-84`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/config/aider_conf.md#L81-L84),[`109`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/config/aider_conf.md#L109)).
- `.env` files at home, git root and cwd carry `*_API_KEY` values by design.
- `.aider.model.settings.yml` has no key field; `extra_params` is passed to litellm and could carry
  one, so flagging it is harmless but not evidence-based.
- `.aider.llm.history` contains full request bodies; keys are not logged.
- No keychain use.

### 4. Exclusions

`.aider/caches` (model price tables, embedding store, version stamp). In repositories:
`.aider.tags.cache.v<N>` tree-sitter tag cache, currently `v3`
([`aider/repomap.py:35`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L35),[`43`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L43),[`186`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L186),[`218`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L218)).

### 5. Project-local files

Defaults placed in the git root, or cwd without git
([`args.py:271-276`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L271-L276),[`422-426`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L422-L426)):
`.aider.input.history` (prompt_toolkit `FileHistory`,
[`aider/io.py:356`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L356)),
`.aider.chat.history.md` (appended per session,
[`io.py:336`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L336)),
`.aider.llm.history` only when `--llm-history-file` is given
([`args.py:296-300`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L296-L300);
written at
[`io.py:755-764`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L755-L764)),
`.aiderignore`, `.aider.tags.cache.v3/`, and per-level `.aider.conf.yml`,
`.aider.model.settings.yml`, `.aider.model.metadata.json`, `.env`. `CONVENTIONS.md` is a documented
convention loaded with `--read`
([`aider/website/docs/usage/conventions.md`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/usage/conventions.md)),
not a hard-coded name. Aider adds `.aider*` and `.env` to the repository `.gitignore` on first run
([`main.py:160-168`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L160-L168)),
so git-based enumeration misses all of this; the collector must walk the directory.

### 6. Where the project path is recorded

Nowhere under home. Aider keeps no index of repositories; `analytics.json` holds only a UUID, and
the chat history lives inside each repository. Discovery sources for other agents (and shell
history) are the only way to find aider projects; the `# aider chat started at <timestamp>` headers
in `.aider.chat.history.md` date the sessions once found.

## Parsing

### 7. Transcript stores

In the git root, else the cwd
([`aider/args.py:271-275`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L271-L275)):
`.aider.chat.history.md` (markdown), `.aider.input.history` (prompt_toolkit `FileHistory` text),
`.aider.llm.history` (text; default `None`, written only when `--llm-history-file` is set,
[`args.py:295-299`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L295-L299)).
One file holds every session in that repository, appended.

#### What survives a delete

Aider has no delete command: `/clear` and `/reset` empty the in-memory chat, leave every file and
write no marker
([`commands.py:439-443`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L439-L443)).
The three files are project-local, in the git root, so they go only with the files themselves or the
repository
([`args.py:270-275`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L270-L275)).
`.aider.input.history` is the per-prompt history file: one entry per prompt with its local time and
no session, which survives the chat history being deleted, truncated or redirected but not the
project ([Past use and secondary sources](#past-use-rows-and-secondary-sources)).
`.aider.llm.history`, written only when `--llm-history-file` is set, is a second copy of every
prompt sent to the model and every response, each with its own time. No other store of past use was
found. The analyzer reads `.aider.chat.history.md` as the primary store and the input and LLM
histories as secondary sources on every run (see
[Secondary sources](../analyzer/docs/output.md#secondary-sources)).

### 8. Record schema

#### .aider.chat.history.md

`.aider.chat.history.md` (append-only,
[`aider/io.py:1117-1136`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L1117-L1136)):

- Session header: `\n# aider chat started at YYYY-MM-DD HH:MM:SS\n\n` (local time,
  [`:335-336`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L335-L336)).
  The only dated line in the file.
- User prompt: `\n#### <line1>  \n#### <line2>  \n`; empty input is `####` followed by a blank
  ([`:775-789`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L775-L789)).
  Slash commands appear the same way (`#### /add foo.py`).
- Tool and system output, including `Applied edit to <path>`, `Commit <hash> <msg>`, errors and
  confirmations: `> text  \n` blockquote lines
  ([`:966-973`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L966-L973),
  [`:995-999`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L995-L999),
  [`base_coder.py:2334`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2334),
  [`repo.py:313`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repo.py#L313)).
- Startup announcements (source review of 2026-10-19): at the start of each run, and again after a
  `/model`, `/weak-model`, `/editor-model` or `/chat-mode` switch, Aider writes its announcement
  lines as blockquotes
  ([`base_coder.py:550-554`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L550-L554),
  [`main.py:1042`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L1042),
  [`1174-1180`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L1174-L1180)):
  `> Aider v<version>`, then `> Model: <name> with <format> edit format` (or `> Main model: ...`
  when a separate weak model is in use), with `, <n> think tokens`, `, reasoning <effort>`,
  `, prompt cache` or `, infinite output` appended when they apply,
  `> Editor model: <name> with <format> edit format` in architect mode, `> Weak model: <name>`, and
  `> Git repo: <dir> with <n> files` or `> Git repo: none`
  ([`base_coder.py:207-260`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L207-L260)).
  `/model <name>` itself is a `#### /model <name>` user line
  ([`commands.py:87-112`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L87-L112)).
- Confirmations (source review of 2026-10-19): `confirm_ask` writes one blockquote line `>
  <question> (Y)es/(N)o[/(A)ll][/(S)kip all][/(D)on't ask again] [<default>]: <answer>`, the answer
  as typed (`y`, `n`, `a`, `s`, `d`, or empty for the default), preceded by the subject (the
  command, path or URL) on blockquote lines of its own
  ([`io.py:807-858`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L807-L858),
  [`903-905`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L903-L905),
  [`922-923`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L922-L923)).
  The questions include `Run shell command?`, `Create new file?`, `Add file to the chat?` and
  `Add URL to the chat?`
  ([`base_coder.py:977`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L977),
  [`1773`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1773),
  [`2207`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2207),
  [`2455`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2455)).
  Under `--yes-always` (`yes-always: true` in a config file,
  [`args.py:760-764`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L760-L764))
  the answer `y` is written without asking, and `n` for a question that requires an explicit yes
  ([`io.py:866-867`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L866-L867)),
  so a line alone does not say whether a person answered. "Don't ask again" adds the question to an
  in-memory set for the run, and a later asking of the same question is declined without a line
  ([`io.py:269`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L269),
  [`821-824`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L821-L824),
  [`903`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L903)).
- Assistant: raw markdown with no prefix, `\n<content>\n\n`
  ([`:793-795`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L793-L795),
  called from
  [`base_coder.py:1829`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1829)),
  so SEARCH/REPLACE edit blocks appear verbatim inside fenced code. The function-call fallback
  writes `json.dumps(args)`
  ([`:1834`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1834)).
- Aider's own reader
  ([`utils.py:148-188`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/utils.py#L148-L188)):
  skip lines starting `# `; `> ` is tool output; `#### ` is user; anything else is assistant.

#### .aider.input.history

`.aider.input.history` (prompt_toolkit `FileHistory`,
[`io.py:19`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L19),[`356`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L356),[`740`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L740);
format `prompt_toolkit/history.py:298-307`): an entry is `\n# YYYY-MM-DD HH:MM:SS.ffffff\n` followed
by one `+<line>` per input line (local time).

#### .aider.llm.history

`.aider.llm.history`
([`io.py:754-764`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L754-L764)):
`TO LLM YYYY-MM-DDTHH:MM:SS\n` followed by `format_messages` output
([`utils.py:112-134`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/utils.py#L112-L134)):
a `-------` separator, then `ROLE <line>` per content line (`SYSTEM`, `USER`, `ASSISTANT`), and
`LLM RESPONSE <ts>\n` plus `ASSISTANT <line>` lines
([`base_coder.py:1793`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1793),
[`:1822-1826`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1822-L1826)).

### 9. Joins and timestamps

The project is the directory containing the files (the git root). There is
no session id; synthesise one per `# aider chat started at` header. Input
history timestamps join to `#### ` prompts by order and text. No branch is
recorded; the model is named only in the startup announcement lines
([section 8](#8-record-schema)), which carry no time of their own and
follow the session header.

### 10. Other stores

None besides the input and LLM histories of [section 7](#7-transcript-stores), and no SQLite
store. `.aider.tags.cache.v*` is a repository-map cache, not chat, and is
excluded by the collector.

### 11. Format versions

None; the format has not changed across sessions.

### 12. Secrets

`.aider.llm.history` contains the complete system prompt with every added
file; `.aider.chat.history.md` contains any pasted secrets. Aider writes no
keys itself; the collector flags `.aider.conf.yml` and the model settings
files.

### 13. Parser plan

Globs: `**/.aider.chat.history.md`, `**/.aider.input.history`,
`**/.aider.llm.history` (project-level, so they arrive through the
collector's project catalog).

Rows: one per `#### ` block (user), per assistant run, per `> ` run
(tool_result); `# aider chat started` becomes `system`.

| Column | Source |
| --- | --- |
| timestamp_utc | last `# aider chat started at` header, or the matching `# ` input-history line, converted from local time |
| session_id | synthesised `<path>#<header timestamp>` |
| project_path | the directory holding the file |
| git_branch | empty |
| model | empty |
| tool_name, tool_use_id | empty |
| text | prompt text, assistant text, blockquote text |

#### Permission rows

Aider's confirmation prompts are written as `> ` blockquote lines
([section 8](#8-record-schema)), which the parser already emits with the
rest of the blockquote run as `tool_result` rows; no separate `permission
decision:` row is derived from them.

From the source review of 2026-10-19 ([Source reviews](#source-reviews)): the confirmation lines
are decisions on disk; a
`permission decision: <answer> (<question>)` `system` row beside the
`tool_result` row would surface them, and a `yes-always` key in a
collected `.aider.conf.yml` is a standing setting
(`permission setting: yes-always=true (from <file>, file mtime)`).

#### Model rows

The model is in the chat history only as the `> Model:`, `> Main
model:`, `> Weak model:` and `> Editor model:` announcement lines
([section 8](#8-record-schema)); the parser does not read them, so it
yields no `model:` rows. From the source review of 2026-10-19: the announcement lines give
`model: <name>` at each session
header and `model: <old> -> <new>` at each later announcement that
names another; not yet parsed.

#### Past-use rows and secondary sources

Sources: `.aider.chat.history.md` is primary; `.aider.input.history` and
`.aider.llm.history` are secondary, parsed on every run, with each row's
own time and the default two-second window.

`.aider.chat.history.md` is the store of record: it is the only file with session headers and
assistant and tool output, and the one Aider itself reads back with `--restore-chat-history`
([`base_coder.py:519-520`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L519-L520)).
The input and LLM histories are secondary sources (files that repeat some of a primary store's
events, in the sense of
[doubleagent issue 122](https://github.com/seanthegeek/doubleagent/issues/122)):

- Every prompt typed at the terminal is written to both: prompt_toolkit's `FileHistory` on the
  prompt session appends it to the input history
  ([`io.py:355-356`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L355-L356)),
  and `get_input` then calls `user_input`, which writes the `#### ` lines
  ([`io.py:732-733`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L732-L733),
  [`:775-789`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L775-L789)).
  A `--message` prompt is added with `add_to_input_history`
  ([`main.py:1126-1127`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L1126-L1127),
  [`io.py:736-745`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L736-L745))
  and written to the chat history by the coder
  ([`base_coder.py:877-879`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L877-L879)).
  The parser stamps the chat row with the matching input-history entry's time, so the two rows carry
  the same text, synthesised session id, project path and timestamp, and pair exactly.
- Input-history entries with no chat twin: a `/run <command>` entry Aider adds when it runs a shell
  command it suggested, whose chat trace is a `> Running <command>` blockquote instead
  ([`base_coder.py:2471-2474`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2471-L2474));
  every prompt after a chat-history write error, which sets `chat_history_file` to `None` for the
  rest of the run
  ([`io.py:1133-1136`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L1133-L1136));
  and every prompt of a run whose `--chat-history-file` pointed elsewhere, since the two paths are
  separate options
  ([`args.py:276-287`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L276-L287)).
  These rows are kept.
- What the input history survives: the chat history being deleted, truncated or redirected. It does
  not survive the project, since both default to the git root
  ([`args.py:270-275`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L270-L275));
  neither is written under the home unless Aider ran there outside any repository.
- The LLM history's `TO LLM` blocks become `system` rows that no chat row repeats. Its
  `LLM RESPONSE` block is timestamped when the response arrived
  ([`io.py:754-764`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py#L754-L764)),
  while the chat history's assistant row inherits the prompt's time and may be split by `> ` lines,
  so an `assistant` row pairs only for a reply of identical text that arrived within the two-second
  window. Expect the LLM history's rows to stay in the timeline.

#### Sync, relay and origin rows

Aider records no sync state, because it uploads no session: no command or setting sends a chat
history, input history, LLM history or conversation title anywhere beyond the prompt sent to the
model provider through litellm (the library Aider calls for every model API). The commands are all
local
([`commands.py`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L87-L1638));
`/save` writes `/add` and `/read-only` lines to a local file
([`commands.py:1497-1522`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L1497-L1522)),
`/copy` uses the clipboard, and `/clear` empties the in-memory message lists without touching the
history files
([`commands.py:435-437`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L435-L437)).
What does leave the host:

- Analytics, through PostHog (a hosted product-analytics service) at `https://us.i.posthog.com`; the
  client for Mixpanel, another such service, is commented out
  ([`analytics.py:55-57`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L55-L57),
  [`analytics.py:101-108`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L101-L108)).
  Opt-in: a random 10% of users are asked once, `--analytics` asks anyone, and analytics stay off
  unless the user said yes
  ([`analytics.py:119-135`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L119-L135),
  [`main.py:642-662`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py#L642-L662)).
  Events carry event names, a model name (redacted to `<provider>/REDACTED` when it is not a known
  model), token counts, costs, edit format and system information
  ([`analytics.py:186-240`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L186-L240),
  [`base_coder.py:2113-2122`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2113-L2122)),
  never prompt or reply text; the exceptions are the `message_send_exception` event's `str(err)`
  ([`base_coder.py:1511`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1511))
  and PostHog's own exception autocapture
  ([`analytics.py:106`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L106)),
  which can carry whatever a provider error message quoted. The opt-in state is
  `~/.aider/analytics.json`, keys `uuid` (string), `permanently_disable` (boolean or `null`) and
  `asked_opt_in` (boolean)
  ([`analytics.py:137-184`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L137-L184)),
  collected by the `.aider` catalog line; it says analytics may have been on, not what any session
  sent. `--analytics-log <file>` appends each event as a JSON line with `event`, `properties`,
  `user_id` and `time` (epoch seconds) to a path the user chooses
  ([`args.py:574-578`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L574-L578),
  [`analytics.py:242-253`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/analytics.py#L242-L253));
  no catalog line can name that path, but an `analytics-log:` key in a collected `.aider.conf.yml`
  does. `--analytics-posthog-host` and `--analytics-posthog-project-api-key` redirect the events to
  another PostHog
  ([`args.py:585-594`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py#L585-L594)).
- Crash and `/report` text, which goes nowhere by itself: Aider builds a prefilled GitHub new-issue
  URL (version, platform, the traceback with file paths reduced to base names, or the startup
  announcements) and opens it in the browser for the user to submit
  ([`report.py:37-90`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/report.py#L37-L90),
  [`report.py:94-151`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/report.py#L94-L151),
  [`commands.py:1555-1567`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L1555-L1567)).

The OpenRouter OAuth flow writes `~/.aider/oauth-keys.env` (see [section 3](#3-credentials)) and
carries no session. Searched for `sync`, `share`, `upload`, `publish`, `cloud`, `remote`, `gist`,
`paste`, `export`, `backup`, `account`, `team`, `session_id`, `conversation_id`, `remote_id` and
outbound `requests`/`httpx` calls in `aider/` (the website tree aside); the only hosts contacted are
the model providers, PostHog, OpenRouter's auth and model-list endpoints, GitHub's Copilot token
endpoint when a `github_copilot/` model is used with `GITHUB_COPILOT_TOKEN`
([`models.py:950-983`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/models.py#L950-L983)),
litellm's price table and pages fetched by `/web`. No other agent's directory is read or written for
this. The parser yields no `session synced:` row.

No session is relayed or of remote origin.

#### Scratch directory rows

None ([Source reviews](#source-reviews)).

#### Deletion rows

No marker; the files outlive `/clear` and `/reset`
([What survives a delete](#what-survives-a-delete)).

#### Bad-line rows

Covered (source review of 2026-10-19).

#### Fixtures

Fixture `.aider.chat.history.md`:

```markdown
# aider chat started at 2026-10-02 12:00:00

#### rename foo to bar  
Here is the change:

a.py
<<<<<<< SEARCH
foo
=======
bar
>>>>>>> REPLACE

> Applied edit to a.py  
> Commit abc1234 refactor: rename foo to bar  
```

The other two files:

- `.aider.input.history`: `\n# 2026-10-02 12:00:05.123456\n+rename foo to bar\n`
- `.aider.llm.history`: `TO LLM 2026-10-02T12:00:05\n-------\nSYSTEM Act as an expert\n-------\nUSER
  rename foo to bar\nLLM RESPONSE 2026-10-02T12:00:09\nASSISTANT Here is the change:\n`

## 14. Confidence

Collection. High: all file names and search orders (source). Medium: whether the collector's
exclusion and secret globs are evaluated against project paths (affects `.aider.tags.cache*` and
project `.aider.conf.yml`). Not determined: nothing material; aider is the simplest layout of the
five.

Parsing. High: chat and LLM history formats (read from the writers).
Medium-high: input history (upstream prompt_toolkit source, not pinned to
Aider's dependency version). Local-time timestamps need the host time zone
to convert exactly.
