# Agent Zero transcript schema

Catalog agent: `agent-zero`. One JSON file per chat holds two parallel
records of the conversation: the UI log (timestamped, truncated, last 1000
items) and each agent's LLM history (full text, no timestamps, compressed
over time). Paths in
[`collectors/research/agent-zero.md`](../../collectors/research/agent-zero.md).

## 1. Source

[agent0ai/agent-zero](https://github.com/agent0ai/agent-zero) at [`e3051fb584b1a36be2b0a0c90606f1c2c2d356ec`](https://github.com/agent0ai/agent-zero/commit/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec),
MIT ([`LICENSE:1-4`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/LICENSE#L1-L4)). Open source, Python. Read only, not run.

- **Source review (2026-10-19).** agent0ai/agent-zero at
  [`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a)
  (committed 2026-10-13), against
  [`e3051fb`](https://github.com/agent0ai/agent-zero/commit/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec)
  cited above; agent0ai/a0-connector at
  [`3741c88`](https://github.com/agent0ai/a0-connector/commit/3741c8809f1f99b4efee2ed1a24234a98bf896d4)
  against
  [`76e834f`](https://github.com/agent0ai/a0-connector/commit/76e834f20e50f6e47954c89ee39dd4c5b50d81b7).
  Read only, nothing run. One line per requirement class; the detail is
  in [section 3](#3-record-schema), [section 5](#5-sqlite-or-binary-stores)
  and [section 8](#8-parser-plan).
  - Permission state: found, not parsed. Tool policies per agent
    profile and project (`plugins/_tool_access/config.json`), a blocked
    call recorded as a `warning` log item, the automatic denial of a
    provider-hosted MCP approval request, and the opt-in Infection Check
    reviewer's verdicts as `warning` items
    ([`helpers/tool_policy.py:197-208`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/tool_policy.py#L197-L208),
    [`agent.py:1325-1346`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/agent.py#L1325-L1346),
    [`plugins/_infection_check/helpers/checker.py:180-197`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_infection_check/helpers/checker.py#L180-L197)).
  - Model: per-message model already covered; the per-chat override
    `data.chat_model_override` (a preset name or a model configuration)
    and an editor session's `data.acp_model_id` are found and not parsed
    ([`plugins/_model_config/api/model_override.py:58`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/api/model_override.py#L58),
    [`plugins/_a0_acp/api/session.py:16`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_a0_acp/api/session.py#L16)).
  - Past use beyond `chat.json`: found, none parsed. The scheduler's
    task list, Telegram's chat map, the time-travel shadow git of `usr`
    and the memory store each outlive a deleted chat
    ([section 5](#5-sqlite-or-binary-stores)).
  - Sync, relay and origin: sync (stored provider responses) and relay
    (Telegram, WhatsApp, email) already covered and unchanged at HEAD;
    no Discord, Slack or other channel (grepped for `discord`, `slack`,
    `mattermost` and `signal-cli`: only an unrelated office helper
    matches). Origin: none on the instance; the host-side connector
    keeps a pointer to a chat that lives on another instance
    (`AGENT_ZERO_LAST_CONTEXT_ID` and `AGENT_ZERO_LAST_CONTEXT_HOST` in
    `~/.agent-zero/.env`,
    [`a0-connector config.py:13-14`](https://github.com/agent0ai/a0-connector/blob/3741c8809f1f99b4efee2ed1a24234a98bf896d4/src/agent_zero_cli/config.py#L13-L14)),
    not parsed.
  - Scratch directories: found. A chat with no project works in
    `usr/workdir`, an editor session in a container transport in its
    `data.workdir_path`, and the host connector keeps computer-use
    screenshots under the system temp directory; the parser writes no
    `scratch directory:` row ([section 8](#8-parser-plan)).
  - Deletion: found. Chat delete removes the chat folder and the
    scheduler tasks bound to it and asks the provider to delete stored
    responses; reset rewrites `chat.json` and removes `messages/`
    ([`api/chat_remove.py:11-26`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/api/chat_remove.py#L11-L26),
    [`api/chat_reset.py:13-19`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/api/chat_reset.py#L13-L19)).
  - Version drift: small. The `chat.json` writer is unchanged, six lines
    lower in `helpers/persist_chat.py` (`_serialize_context` at
    [`185-253`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/persist_chat.py#L185-L253));
    `metadata.responses` gains an optional `history_extras` string
    ([`helpers/llm_result.py:249`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/llm_result.py#L249));
    the scheduler may now keep `usr/scheduler/tasks.yaml` instead of
    `tasks.json`
    ([`helpers/task_scheduler.py:512-515`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/task_scheduler.py#L512-L515)).
    The log, history and tool-result files the parser reads are the
    same. Separately, the parser's path pattern does not match a chat
    collected from a Docker volume, whose paths are relative to the
    volume's `_data` (`chats/<ctxid>/chat.json`), so the `*a0_usr` and
    `a0-launcher-*-usr` volumes are collected and not parsed.
  - Bad lines: already covered; the parser reads no file line by line,
    and a `chat.json` that does not parse yields a whole-file row plus
    the log items it can recover.

## 2. Transcript files

Relative to the install directory (`/a0` in Docker; on the host usually
`~/agent-zero/<instance>/` for installer and launcher setups):

- `usr/chats/<ctxid>/chat.json`, one per chat or task context; background
  contexts are never saved
  ([`helpers/persist_chat.py:17-19`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L17-L19),[`50-60`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L50-L60),[`95-96`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L95-L96)). The file is
  rewritten whole and atomically ([`99-120`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L99-L120)). `ctxid` is 8 random
  alphanumerics ([`agent.py:150-158`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/agent.py#L150-L158)).
- `usr/chats/<ctxid>/messages/<n>.txt`: full text of each tool result of 500
  characters or more; the history record gets a `file` key pointing at it
  ([`extensions/python/hist_add_tool_result/_90_save_tool_call_file.py:23-43`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/extensions/python/hist_add_tool_result/_90_save_tool_call_file.py#L23-L43)).
- Legacy: `usr/chats/<ctxid>.json` (v0.8.0, moved into the folder layout on
  load, [`persist_chat.py:134-140`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L134-L140)) and `tmp/chats/` (moved to
  `usr/chats`, [`helpers/migration.py:24`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/migration.py#L24)).

The catalog globs are therefore `agent-zero/*/usr/chats/*/chat.json`,
`agent-zero/usr/chats/*/chat.json` and the `Desktop/agent-zero` equivalents.
A Docker volume holding `/a0/usr` (`a0_usr`, `a0-launcher-<slug>-usr`)
is collected with its `_data` directory as the base, so its chats are
`chats/<ctxid>/chat.json` relative to that base; the parser's path
pattern requires an `agent-zero` component and does not select them
(2026-10-19 review).

## 3. Record schema

`chat.json` top level ([`persist_chat.py:179-219`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L179-L219)): `id`, `name`,
`created_at`, `last_message` (ISO 8601 with the user's UTC offset,
[`helpers/localization.py:195-212`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/localization.py#L195-L212)), `type` (`user` or `task`,
[`agent.py:50-53`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/agent.py#L50-L53)), `agents`, `streaming_agent`, `agent_profile`, `log`,
`data` (includes `project`), `output_data`.

**`agents[]`** ([`persist_chat.py:222-232`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L222-L232)): agent 0 first, then each
subordinate. Fields `number`, `agent_profile`, `data`, and `history`, which
is a **JSON string** (compact dump, [`helpers/history.py:520-522`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L520-L522),[`810-811`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L810-L811)) that
decodes to `{"_cls":"History","counter","bulks":[],"topics":[],"current":{}}`
([`history.py:512-518`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L512-L518)). A `Topic` is `{_cls, summary, messages}`
([`290-295`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L290-L295)), a `Bulk` is `{_cls, summary, records}` of topics or bulks
([`340-345`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L340-L345)). A `Message` is `{_cls:"Message", id, ai, content, metadata,
sequence, summary, tokens}` ([`138-149`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L138-L149)), no timestamp. Chronological order
is bulks, then topics, then current, messages in list order.

Message content by kind:

- User (`ai=false`): dict from `fw.user_message.md`, `{system_message?,
  user_message, attachments?}` with empty keys removed
  ([`agent.py:746-773`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/agent.py#L746-L773), [`prompts/fw.user_message.md`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/prompts/fw.user_message.md#L1-L7)).
- Assistant (`ai=true`): the model's text, which in the default prompt mode
  is a JSON object `{thoughts, headline, tool_name, tool_args}`
  ([`prompts/agent.system.main.communication.md:9-12`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/prompts/agent.system.main.communication.md#L9-L12)); with native
  function calling it is `{"tool_name","tool_args"}` rendered from the calls,
  or `parallel_tool_calls` wrapping several
  ([`agent.py:775-795`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/agent.py#L775-L795), [`helpers/llm_result.py:197-209`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/llm_result.py#L197-L209)).
  `metadata.responses` carries `response_id`, `provider_model_key`, `usage`
  ([`llm_result.py:227-239`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/llm_result.py#L227-L239)).
- Tool result (`ai=false`): dict `{tool_name, tool_result, file?, ...}`
  ([`agent.py:802-825`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/agent.py#L802-L825)); the message `id` is the tool's log item id
  ([`helpers/tool.py:56`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/tool.py#L56),[`61-68`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/tool.py#L61-L68)).

**`log`** ([`persist_chat.py:235-247`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L235-L247)): `{guid, logs, progress, progress_no}`,
`logs` being the last 1000 items ([`persist_chat.py:18`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L18)). Each item
([`helpers/log.py:199-209`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/log.py#L199-L209)): `no`, `id`, `type`, `heading`, `content`, `kvps`,
`timestamp` (float epoch seconds, `time.time()`, [`log.py:157-162`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/log.py#L157-L162)),
`agentno`. `type` is one of `agent`, `browser`, `code_exe`, `subagent`,
`error`, `hint`, `info`, `progress`, `response`, `tool`, `mcp`, `input`,
`user`, `util`, `warning` ([`log.py:44-60`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/log.py#L44-L60)). Content is cut to 15,000
characters ([`log.py:66`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/log.py#L66),[`124-135`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/log.py#L124-L135)). Keys passed as keyword arguments
are merged into `kvps` ([`log.py:336-340`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/log.py#L336-L340)):

- `user` items: `content` is the message, `id` the history message id
  ([`helpers/message_queue.py:141-147`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/message_queue.py#L141-L147)).
- `agent` items: the streamed generation; `kvps` holds the parsed response
  (`thoughts`, `headline`, `tool_name`, `tool_args`), `step`, `reasoning`
  ([`extensions/python/response_stream/_10_log_from_stream.py:47-69`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/extensions/python/response_stream/_10_log_from_stream.py#L47-L69)).
- `tool` items: `kvps` is the tool arguments plus `_tool_name`; `content`
  is later set to the result ([`helpers/tool.py:56-59`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/tool.py#L56-L59),[`68`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/tool.py#L68)).
- `response` items: the final answer to the user.

Keys in `data` and `agents[].data` that record a remote copy. Context
and agent data are saved without the keys that start with `_`
([`helpers/persist_chat.py:194-195`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L194-L195),[`223`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L223)), so these survive:

- `agents[].data.responses_state`, written after each model reply that
  carries a provider response id ([`agent.py:1062-1082`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/agent.py#L1062-L1082)):
  `{response_id, previous_response_id, provider_model_key, history_counter,
  response_ids: [...]}`, all strings but `history_counter` (the history
  `sequence` of the reply) and `response_ids` (every id the chat has had
  for that model). The Responses API is OpenAI's generation endpoint, which
  can keep each response on the provider's side (`store: true`) so the
  next turn sends only `previous_response_id` and the new input. Agent
  Zero calls providers through the litellm library, and its transport
  sets `store: true` when the model's `responses_state` is `provider`,
  which is the value when none is set, and `store: false` for `local` and
  `off` ([`helpers/litellm_transport.py:889-904`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/litellm_transport.py#L889-L904),[`1554-1556`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/litellm_transport.py#L1554-L1556)).
  It applies only to a model whose `a0_api_mode` is `responses`; every
  stock provider in [`conf/model_providers.yaml`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/conf/model_providers.yaml#L176-L182)
  is `chat`, which sets the state to `off`
  ([`105-112`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/litellm_transport.py#L105-L112)), and the bundled Codex
  (ChatGPT account) provider is `responses` with `responses_state: local`
  ([`plugins/_oauth/conf/model_providers.yaml:9-10`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_oauth/conf/model_providers.yaml#L9-L10)). So a key present
  means the provider returned response ids, not that it stored them; a
  non-empty `previous_response_id` means a turn was chained on a stored
  response. History compression and manual compaction drop `response_id`
  and `previous_response_id` but keep `response_ids`
  ([`helpers/history.py:736-755`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L736-L755), [`extensions/python/message_loop_end/_10_organize_history.py:12`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/extensions/python/message_loop_end/_10_organize_history.py#L12),
  [`plugins/_chat_compaction/helpers/compactor.py:149`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_chat_compaction/helpers/compactor.py#L149)); a branched chat
  drops the whole key ([`plugins/_chat_branching/api/branch_chat.py:142-144`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_chat_branching/api/branch_chat.py#L142-L144)).
  The same id is also in each assistant message's `metadata.responses`
  ([section 3](#3-record-schema), above).
- Telegram chats (the bundled `_telegram_integration` plugin, a bot the
  user runs with a token from Telegram): `data.telegram_bot` (bot name),
  `telegram_chat_id`, `telegram_chat_type`, `telegram_user_id`,
  `telegram_username` and `telegram_bot_cfg`, the bot's whole configuration entry
  ([`plugins/_telegram_integration/helpers/constants.py:5-15`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/helpers/constants.py#L5-L15),
  [`plugins/_telegram_integration/helpers/handler.py:380-400`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/helpers/handler.py#L380-L400)); the chat
  is named `Telegram: @<username>` or `Telegram: <user id>`
  ([`391-392`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/helpers/handler.py#L391-L392)).
- WhatsApp chats (`_whatsapp_integration`): `data.wa_chat_id`,
  `wa_sender_name`, `wa_sender_number`, `wa_is_group`, `wa_active`,
  `wa_last_body`, `wa_last_msg_id`
  ([`plugins/_whatsapp_integration/helpers/handler.py:33-39`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_whatsapp_integration/helpers/handler.py#L33-L39),[`153-159`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_whatsapp_integration/helpers/handler.py#L153-L159)).
- Email chats (`_email_integration`, IMAP in and SMTP out):
  `data.email_handler`, `email_sender`, `email_thread_id`,
  `email_subject`, `email_message_id`, `email_references`,
  `email_last_body`
  ([`plugins/_email_integration/helpers/dispatcher.py:14-21`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_email_integration/helpers/dispatcher.py#L14-L21),[`269-270`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_email_integration/helpers/handler.py#L269-L270)).

Telegram also keeps `usr/plugins/_telegram_integration/state.json`,
`{"chats": {"<bot>:<user id>:<chat id>": "<ctxid>"}}`, written when a
Telegram user's first message creates a chat
([`plugins/_telegram_integration/helpers/constants.py:3`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/helpers/constants.py#L3),
[`plugins/_telegram_integration/helpers/handler.py:57-64`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/helpers/handler.py#L57-L64),[`405-410`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/helpers/handler.py#L405-L410)).

More `data` keys, from the 2026-10-19 source review at
[`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a);
none is read by the parser:

- Editor sessions. ACP, the Agent Client Protocol, lets an editor drive
  an agent; the bundled `_a0_acp` plugin serves it and the host-side
  connector (`a0 acp`) relays the editor's files and terminal. A chat an
  editor opens gets `data.acp_session` (`true`), `acp_cwd` (the editor's
  workspace, a path on the user's host), `acp_additional_directories`
  (a list of paths), `acp_mode` (`default`, `plan` or `act`, anything
  else stored as `default`), `acp_transport` (`connector` or
  `container`), `acp_model_id`, `acp_config_options`, and, for the
  `container` transport with a configured root, `workdir_path` (a
  working directory inside the container); the chat is named after the
  last component of `acp_cwd`
  ([`plugins/_a0_acp/api/session.py:12-20`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_a0_acp/api/session.py#L12-L20),[`41-43`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_a0_acp/api/session.py#L41-L43),[`131-150`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_a0_acp/api/session.py#L131-L150)).
  The keys were already written at the commit this document first
  cited.
- Model override. Choosing a model for one chat stores
  `data.chat_model_override`: `{"preset_name": <name>}` for a preset of
  `usr/plugins/_model_config/presets.yaml`, a whole model configuration
  object for a custom choice, or `null` when cleared
  ([`plugins/_model_config/api/model_override.py:58`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/api/model_override.py#L58),[`81`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/api/model_override.py#L81),[`92`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/api/model_override.py#L92),
  [`plugins/_model_config/helpers/model_config.py:10`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/helpers/model_config.py#L10),[`744-756`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_model_config/helpers/model_config.py#L744-L756));
  the connector's model switcher writes the same key
  ([`plugins/_a0_connector/api/v1/model_switcher.py:211`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_a0_connector/api/v1/model_switcher.py#L211)).
  Only the latest choice is kept, so the history of switches is the
  per-message `provider_model_key`. Whether a custom configuration can
  carry an API key was not traced.

## 4. Joins

- Chat to project: `data.project` is a project name; path
  `/a0/usr/projects/<name>` ([`helpers/projects.py:457`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/projects.py#L457)). Without a project the
  working directory is `usr/workdir`.
- Log to history: `log.logs[].id` equals the history `Message.id` for user
  messages and tool results (above).
- Tool use to result: one `tool` log item holds both; in history the
  assistant message's `tool_name` and the next tool-result message.
- Parent to subordinate: `agents[n]` is the subordinate of `agents[n-1]`
  ([`persist_chat.py:189-194`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L189-L194)); log items carry `agentno`.

## 5. SQLite or binary stores

None for transcripts. Memory is a FAISS index plus a pickled LangChain
docstore (`usr/memory/<subdir>/index.pkl`); reading it means unpickling
untrusted data, so leave it to manual analysis.

Records of past use beyond `chat.json`, from the 2026-10-19 source
review at
[`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a).
None is read by the parser today; the plan marks each one in
[section 8](#8-parser-plan). Paths are relative to the install
directory.

| File | Holds | Survives | Joins `chat.json` on | Kind |
| --- | --- | --- | --- | --- |
| `usr/scheduler/tasks.json`, or `tasks.yaml` when only that exists | One object per scheduled, ad hoc or planned task: `uuid`, `context_id`, `name`, `system_prompt`, `prompt`, `attachments`, `project_name`, `created_at`, `updated_at`, `last_run`, `last_result`, `state`, `type` ([`helpers/task_scheduler.py:163-175`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/task_scheduler.py#L163-L175),[`512-515`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/task_scheduler.py#L512-L515)) | A reset of the task's chat; not a chat delete, which removes the tasks bound to the chat ([`api/chat_remove.py:24-26`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/api/chat_remove.py#L24-L26)) | `context_id` = `id`; `prompt` repeats the task chat's user message, `last_result` its last answer | secondary |
| `usr/plugins/_telegram_integration/state.json` | `chats`, `"<bot>:<user id>:<chat id>"` to `ctxid` ([section 3](#3-record-schema)) | A chat delete, until that Telegram user writes again | the `ctxid` value = `id` | secondary (a deletion marker: an entry with no `chat.json`) |
| `usr/.time_travel/workspaces/` | A shadow git repository per workspace of `usr`, snapshotted automatically; each commit message ends with `A0-Time-Travel-Metadata:` and base64 JSON with `context_id`, `project_name`, `trigger`, `timestamp` and `changed_path_hints` ([`plugins/_time_travel/helpers/time_travel.py:22-28`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_time_travel/helpers/time_travel.py#L22-L28),[`1192-1194`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_time_travel/helpers/time_travel.py#L1192-L1194),[`1206-1220`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_time_travel/helpers/time_travel.py#L1206-L1220)) | A chat delete and the deletion of the files it wrote | `context_id` = `id`, and time | secondary; excluded by the collector (`usr/.time_travel`), so not in a collection |
| `usr/memory/<subdir>/index.pkl` | Memory fragments and solutions the agent summarised at the end of each monologue, with `id`, `timestamp` and `area` and no chat id ([`plugins/_memory/helpers/memory.py:475-487`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_memory/helpers/memory.py#L475-L487)) | A chat delete or reset | time only | secondary; a pickle, left to manual analysis |
| `usr/email/state.json` | The IMAP message ids already processed per handler ([`plugins/_email_integration/helpers/handler.py:38-39`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_email_integration/helpers/handler.py#L38-L39)) | A chat delete | nothing | no events |
| `usr/uploads/`, `usr/email/attachments/`, `usr/whatsapp/media/` and `tmp/whatsapp/media/` | Files received through the web UI, Telegram, email and WhatsApp ([`plugins/_telegram_integration/helpers/constants.py:2`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_telegram_integration/helpers/constants.py#L2), [`plugins/_whatsapp_integration/helpers/handler.py:31`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/helpers/handler.py#L31), [`plugins/_whatsapp_integration/helpers/storage_paths.py:10-11`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/helpers/storage_paths.py#L10-L11)) | A chat delete | file names in `user` log items' `attachments` | evidence files, no events |

The WhatsApp bridge keeps no message store: its only file writes are
media ([`plugins/_whatsapp_integration/whatsapp-bridge/bridge.js:311`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/whatsapp-bridge/bridge.js#L311),[`323`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/whatsapp-bridge/bridge.js#L323)),
and its session directory `tmp/whatsapp/session/` is the linked
device's login state ([section 7](#7-secrets)).

## 6. Format versions

No version field. History compression summarises topics into bulks and drops
the oldest bulk when merging fails
([`history.py:600-607`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/history.py#L600-L607)), so early turns may survive only as
summaries in history and only in the log while it is under 1000 items.
Older chats used `chat.json`-less `<ctxid>.json` files ([section 2](#2-transcript-files)).

## 7. Secrets

Values from `secrets.env` are masked in history content and log items before
storage ([`extensions/python/hist_add_before/_10_mask_content.py:20-28`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/extensions/python/hist_add_before/_10_mask_content.py#L20-L28),
[`log.py:420-435`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/log.py#L420-L435)). API keys in `usr/.env` are not in that set, so any key the
user pastes or a tool prints stays in clear text. `user_message` and tool
`kvps` are the places to look.

A Telegram chat's `data.telegram_bot_cfg` is the bot's configuration
entry as the bot loop holds it, so it carries the bot `token` and, in
webhook mode, `webhook_secret`, in clear text in `chat.json`
([`plugins/_telegram_integration/extensions/python/job_loop/_10_telegram_bot.py:57-59`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/extensions/python/job_loop/_10_telegram_bot.py#L57-L59),[`82-89`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/extensions/python/job_loop/_10_telegram_bot.py#L82-L89),
[`plugins/_telegram_integration/default_config.yaml:2-9`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/default_config.yaml#L2-L9)). The same
values are in the plugin's configuration file,
`usr/plugins/<plugin>/config.json` (or under a project's `.a0proj/` or an
agent profile's directory, [`helpers/plugins.py:838-851`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/plugins.py#L838-L851)).

The WhatsApp bridge (a Node.js process using the Baileys library, which
signs in as a linked WhatsApp device) keeps its login state in
`tmp/whatsapp/session/` through Baileys' `useMultiFileAuthState`
([`plugins/_whatsapp_integration/helpers/storage_paths.py:6-7`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/helpers/storage_paths.py#L6-L7),
[`plugins/_whatsapp_integration/whatsapp-bridge/bridge.js:46`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/whatsapp-bridge/bridge.js#L46),[`108`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_whatsapp_integration/whatsapp-bridge/bridge.js#L108));
those files are the WhatsApp account's device credentials and no
secret glob flags them (2026-10-19 review).

## 8. Parser plan

Rows from `log.logs` (timestamped); when `len(log.logs) == 1000`, also emit
history messages that have no matching log id, with an empty timestamp and
a `system` row saying the log was trimmed.

| Column | Source |
| --- | --- |
| timestamp_utc | log `timestamp` (epoch s) |
| session_id | `chat.json` `id` |
| project_path | `/a0/usr/projects/<data.project>`, else empty |
| git_branch | empty |
| turn_type | `user` → user; `response` → assistant; `agent` → assistant (`kvps.headline`/`thoughts`), and thinking for `kvps.reasoning`; `tool`, `mcp`, `code_exe`, `browser`, `subagent` → tool_use then tool_result from `content`; others → system |
| model | `metadata.responses.provider_model_key` of the matching assistant message, else empty |
| tool_name | `kvps._tool_name` |
| tool_use_id | log item `id` |
| text | `content`; for tool_use the `code`/`command`/`url` key of `kvps`, else `kvps` as JSON |
| source_line | log item `no` |

Model rows (issue 96): before an `agent` log item, or a history-only
assistant message when the log was trimmed, whose
`metadata.responses.provider_model_key` is new for that agent, a `system`
row `model: <key>` at the agent's first model and `model: <old> -> <new>`
on a change, tracked per chat `id` and agent `number` (`agentno` on log
items), with ` agent=<n>` after it for a subordinate agent. The first
research named no permission or approval record in `chat.json`, so the
parser writes no permission rows; the 2026-10-19 source review found
the records below. Proposed rows, one line per class, from source at
[`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a);
none is written by the parser yet:

- Permission, per call. A tool call the profile's policy blocks raises
  `Tool "<name>" is blocked for agent profile "<profile>".`, which the
  agent records as a history warning and a `warning` log item with the
  same id
  ([`helpers/tool_policy.py:197-208`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/tool_policy.py#L197-L208),
  [`extensions/python/_functions/agent/Agent/handle_exception/end/_50_handle_repairable_exception.py:17-22`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/extensions/python/_functions/agent/Agent/handle_exception/end/_50_handle_repairable_exception.py#L17-L22)):
  `permission decision: blocked tool=<name> profile=<profile>`. A
  provider-hosted MCP approval request on the Responses API is always
  denied, logged as a `warning` headed `Responses MCP approval
  required` with a tool result `mcp_approval_request`
  ([`agent.py:1325-1346`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/agent.py#L1325-L1346)):
  `permission decision: denied automatically (provider MCP approval
  request)`. The Infection Check plugin, a reviewer model that audits
  the agent's output before each tool runs, is disabled by default
  (the bundled `plugins/_infection_check/.toggle-0`; a plugin is
  switched by a `.toggle-0` or `.toggle-1` file,
  [`helpers/plugins.py:60-61`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/plugins.py#L60-L61),[`505-510`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/plugins.py#L505-L510));
  when enabled, a pass leaves only a progress line, and a question or a
  stop leaves `warning` items headed `Infection check: requesting
  clarification`, `Infection check: clarification passed` or
  `Infection check: TERMINATED`, the last also replacing the agent's
  last history message with a blocked marker
  ([`plugins/_infection_check/helpers/checker.py:180-197`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_infection_check/helpers/checker.py#L180-L197),[`330-345`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_infection_check/helpers/checker.py#L330-L345)):
  `permission decision: <clarify, passed or terminated> (infection
  check)`. Today all three reach the timeline only as `system` rows
  `warning: <heading> | <content>`.
- Permission, standing. Tool policies are `mode` (`inherit` or
  `custom`), `default` and `mcp_default` (`allow` or `block`),
  `allowed` and `blocked` lists of tool ids
  ([`plugins/_tool_access/default_config.yaml:1-5`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_tool_access/default_config.yaml#L1-L5),
  [`helpers/tool_policy.py:27-37`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/tool_policy.py#L27-L37),[`176-195`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/tool_policy.py#L176-L195)),
  in `usr/agents/<profile>/plugins/_tool_access/config.json`, a
  project's `.a0proj/plugins/_tool_access/config.json` and
  `.a0proj/agents/<profile>/plugins/_tool_access/config.json`
  ([`plugins/_tool_access/README.md:4-9`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_tool_access/README.md#L4-L9)):
  one `permission setting: <scope>.<key>=<value> (from <file>, file
  mtime)` row per key and list entry. The Orchestrator plugin, which
  tells the agent how to run other coding CLIs on the user's host or in
  the container, defaults each to its approval bypass
  (`bypass_sandbox`, `permission_mode: bypassPermissions`, `force`,
  `always_approve`, `yolo`, `auto`,
  [`plugins/_orchestrator/default_config.yaml:7-37`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_orchestrator/default_config.yaml#L7-L37));
  a user override in `usr/plugins/_orchestrator/config.json` gets the
  same `permission setting:` rows. The `.toggle-1` of
  `_infection_check` is one more (`permission setting:
  infection_check=enabled`). An editor session's `data.acp_mode` gives
  `permission mode: <acp_mode> (acp)` after the chat start row.
- Model. Already: `model:` rows from `provider_model_key`. Proposed:
  `model: requested <preset_name or compact JSON> (chat override, as of
  file mtime)` from `data.chat_model_override`, and `model: requested
  <acp_model_id> (acp)`, both after the chat start row.
- Past use. The sources table in
  [section 5](#5-sqlite-or-binary-stores): `usr/scheduler/tasks.json`
  (or `.yaml`) secondary, one `user` row per task `prompt` and one
  `assistant` row per `last_result` at `last_run`, joined on
  `context_id`, plus `system` `scheduled task: <name> type=<type>
  state=<state>` at `created_at`; `state.json` of the Telegram plugin
  secondary, one `session deleted: telegram chat <chat id> user <user
  id> ctxid <ctxid> (from state.json, file mtime)` row for a map entry
  whose `chat.json` is absent from the input. The time-travel git and
  the memory pickle are not parsed.
- Sync, relay and origin. Sync and relay as above, unchanged. Origin:
  the connector's `~/.agent-zero/.env` names the last chat it used on a
  remote instance; a `session origin: remote agent-zero instance
  <AGENT_ZERO_LAST_CONTEXT_HOST> context <AGENT_ZERO_LAST_CONTEXT_ID>
  (from .agent-zero/.env, file mtime)` row would mark it, reading only
  those two keys of a file the collector flags as a secret.
- Scratch directories. A chat with no project runs in
  `/a0/usr/workdir` (the default `workdir_path`,
  [`helpers/settings.py:604`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/helpers/settings.py#L604)),
  and the analyzer's catalog rule cannot class a container path, so the
  parser would write `scratch directory: /a0/usr/workdir (no project)`
  for such a chat and `scratch directory: <data.workdir_path> (acp
  container transport)` for an editor session that sets one. An editor
  session's `data.acp_cwd` is the user's project on the host and is the
  better `project_path` for its rows.
- Deletion. A chat delete also removes the chat's scheduler tasks;
  what survives it is Telegram's `state.json`, the time-travel git, the
  memory store and the received files (the sources table). Nothing
  local says whether the provider deleted its stored responses
  (above).
- Bad lines. No file is read line by line; nothing to add.

Sync: Agent Zero records no sync state. It has no account, cloud
copy, share link or history sync: the web UI is served by the instance
itself, and the features that move chats are local. Backup builds a zip
of `usr/` and sends it to the browser as a download
([`helpers/backup.py:338-432`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/backup.py#L338-L432), [`api/backup_create.py:35-51`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/api/backup_create.py#L35-L51)); chat
export returns the `chat.json` text to the browser
([`api/chat_export.py:5-17`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/api/chat_export.py#L5-L17), [`helpers/persist_chat.py:155-159`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L155-L159)); the
Remote Control tunnels (Serveo, Cloudflare, Microsoft, Tailscale) expose
the web UI and persist nothing
([`helpers/tunnel_manager.py:15-31`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/tunnel_manager.py#L15-L31)); the only call to the vendor's
own service is the update check, which posts the version and a hashed
install id, no chat content, and is on by default
(`update_check_enabled` in `usr/settings.json`,
[`helpers/update_check.py:5-19`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/update_check.py#L5-L19), [`helpers/settings.py:627`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/settings.py#L627),
[`extensions/python/user_message_ui/_10_update_check.py:66`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/extensions/python/user_message_ui/_10_update_check.py#L66)); and the
host-side A0 CLI connector talks to the user's instance and to GitHub for
its own updates ([`a0-connector self_update.py:20-25`](https://github.com/agent0ai/a0-connector/blob/76e834f20e50f6e47954c89ee39dd4c5b50d81b7/src/agent_zero_cli/self_update.py#L20-L25)).
Searched `sync`, `share`, `upload`, `cloud`, `publish`, `remote_id`,
`telemetry`, `analytics`, `agent-zero.ai` and every `https://` host
across both repositories. Two features leave a copy of a chat on a
third party's server, and `chat.json` records each
([section 3](#3-record-schema)):

- Stored responses. With a model set to `a0_api_mode: responses` and no
  `responses_state` (or `provider`), each reply is stored at the
  provider; `agents[].data.responses_state` and
  `metadata.responses.response_id` hold the ids. The parser yields one
  row per agent whose `previous_response_id` is non-empty: `session
  synced: provider response <response_id or -> previous
  <previous_response_id> model <provider_model_key or -> (<n> response
  ids) agent=<number> (from chat.json agents[].data.responses_state, file
  mtime)`, timestamped by the file's modification time, and sets
  `records_sync`. Because `local` mode records the same ids with
  `store: false`, an agent whose `previous_response_id` is empty yields
  no row. Fixture only: no real install has shown the key. On
  chat delete, Agent Zero collects every response id in `chat.json` and
  calls litellm's `delete_responses` for each unless
  `responses_delete_on_chat_delete` is `false` in the model's kwargs or
  the chat data, then deletes the folder
  ([`helpers/persist_chat.py:162-168`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L162-L168),[`390-450`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/persist_chat.py#L390-L450), [`agent.py:941-942`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/agent.py#L941-L942));
  the call passes no provider or key and its error list is discarded
  ([`helpers/litellm_transport.py:1481-1490`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/helpers/litellm_transport.py#L1481-L1490)), so nothing local says
  whether the remote copy went.
- Messaging channels. A Telegram, WhatsApp or email chat is carried by
  that service, which keeps the messages. The parser yields one row per
  chat and channel with the keys: `session relayed: telegram bot
  <telegram_bot> chat <telegram_chat_id> user <telegram_user_id>
  @<telegram_username or -> (from chat.json data, file mtime)`,
  `session relayed: whatsapp chat <wa_chat_id> number <wa_sender_number
  or -> (from chat.json data, file mtime)` or `session relayed: email
  thread <email_thread_id or -> from <email_sender or -> (from chat.json
  data, file mtime)`, timestamped by the file's modification time, and
  never prints `telegram_bot_cfg` (it holds the bot token,
  [section 7](#7-secrets)). Fixture only. Deleting the chat removes the folder,
  but Telegram's `state.json` still maps the user and chat to the old
  `ctxid` until that user writes again
  ([`plugins/_telegram_integration/helpers/handler.py:376-387`](https://github.com/agent0ai/agent-zero/blob/e3051fb584b1a36be2b0a0c90606f1c2c2d356ec/plugins/_telegram_integration/helpers/handler.py#L376-L387)), so a
  `state.json` entry with no `chat.json` is a deleted Telegram chat.

Fixture `usr/chats/AbCd1234/chat.json`:

```json
{"id":"AbCd1234","name":"List files","created_at":"2026-10-01T14:00:00+02:00","type":"user",
 "last_message":"2026-10-01T14:00:05+02:00","streaming_agent":0,"agent_profile":"agent0",
 "data":{"project":"demo"},"output_data":{},
 "agents":[{"number":0,"agent_profile":"agent0","data":{},
   "history":"{\"_cls\":\"History\",\"counter\":3,\"bulks\":[],\"topics\":[],\"current\":{\"_cls\":\"Topic\",\"summary\":\"\",\"messages\":[{\"_cls\":\"Message\",\"id\":\"u1\",\"ai\":false,\"content\":{\"user_message\":\"list files\"},\"metadata\":{},\"sequence\":0,\"summary\":\"\",\"tokens\":5},{\"_cls\":\"Message\",\"id\":\"a1\",\"ai\":true,\"content\":\"{\\\"thoughts\\\":[\\\"list\\\"],\\\"headline\\\":\\\"Listing\\\",\\\"tool_name\\\":\\\"code_execution_tool\\\",\\\"tool_args\\\":{\\\"runtime\\\":\\\"terminal\\\",\\\"code\\\":\\\"ls\\\"}}\",\"metadata\":{},\"sequence\":0,\"summary\":\"\",\"tokens\":30},{\"_cls\":\"Message\",\"id\":\"t1\",\"ai\":false,\"content\":{\"tool_name\":\"code_execution_tool\",\"tool_result\":\"a.txt\"},\"metadata\":{},\"sequence\":0,\"summary\":\"\",\"tokens\":8}]}}"}],
 "log":{"guid":"6b0f0c1e-0000-4000-8000-000000000001","progress":"","progress_no":3,"logs":[
  {"no":0,"id":"u1","type":"user","heading":"","content":"list files","kvps":{"attachments":[]},"timestamp":1759320001.0,"agentno":0},
  {"no":1,"id":"g1","type":"agent","heading":"A0: Listing","content":"","kvps":{"step":"Writing terminal command... (2)","thoughts":["list"],"headline":"Listing","tool_name":"code_execution_tool","tool_args":{"runtime":"terminal","code":"ls"}},"timestamp":1759320002.0,"agentno":0},
  {"no":2,"id":"t1","type":"tool","heading":"A0: Using tool 'code_execution_tool'","content":"a.txt","kvps":{"runtime":"terminal","code":"ls","_tool_name":"code_execution_tool"},"timestamp":1759320003.0,"agentno":0}]}}
```

Confidence. High: file layout, top-level keys, history and log item shapes,
timestamp units, masking. Medium: the exact `type` and `heading` of
`code_execution_tool` items (they come from a tool subclass not traced; the
generic `tool` path is shown). Not determined: content of task-scheduler
contexts beyond `type="task"`; the `responses` metadata for every provider.
