# claude-desktop

Catalog agent: `claude-desktop`. Transcript schema is in
[`analyzer/research/claude-desktop.md`](../../analyzer/research/claude-desktop.md).

## 1. Source and evidence level

Closed Electron app; no package inspected. Evidence: **official docs** claude.com/docs/third-party/claude-desktop/data-storage ("User identity and local data", fetched 2026-10-03), modelcontextprotocol.io/docs/tools/debugging (log and config paths), code.claude.com/docs/en/iam and /settings (relation to `~/.claude`); **community/forum**: github.com/aaddrick/claude-desktop-debian README (Linux path), github.com/CodeZeno/Claude-Code-Usage-Monitor/issues/105 and github.com/yhm138/ai-quota-tray/pull/6 (token cache keys and encryption), github.com/blind0wl/dms-ai-usage/issues/8 (Linux `~/.config/Claude/config.json` keys, unanswered). No DFIR write-up found for this app.

**Real install** (issue 73): Claude Desktop 2.31226.1 from the Microsoft Store (package `Claude_pzs8sxrjxfjjc`, version 2.31226.1.0 per `Get-AppxPackage`) on Windows 11 build 26300 arm64, observed 2026-10-10 in a clean VM; directory listings, `main.log`, and one Code-tab and one Chat session were inspected. The Windows Store layout in section 2 comes from that install; the other platforms remain at the documentation level.

## 2. Per-user storage

Standard build (docs MCP debugging; data-storage note that 3p "is separate from standard Claude Desktop"):

- macOS `~/Library/Application Support/Claude/` (e.g. `developer_settings.json`, `claude_desktop_config.json`), logs `~/Library/Logs/Claude/` (`mcp*.log`).
- Windows `%APPDATA%\Claude\` with logs in `%APPDATA%\Claude\logs\` (MCP debugging doc). This is the path the app sees and what an unpackaged (Squirrel) install uses. The Store (MSIX) build observed on the real install keeps `userData` in `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\`: the app logs its paths as `C:\Users\<user>\AppData\Roaming\Claude\...` and MSIX filesystem virtualisation redirects them (`main.log`: `[MSIX] Filesystem virtualization active`, `user_data_location: 'package_localcache'`), so `%APPDATA%\Claude` does not exist on disk and every other process, the collector included, sees only the Packages path. The bundle names a second package family, `AnthropicPBC.Claude_fnn82j28hfe8t` (analyzer research section 5), not observed. Logs on that install are in `%LOCALAPPDATA%\Claude\logs\` (`main.log`, `mcp.log`, `ssh.log`, `cowork_vm_node.log`, `claude.ai-web.log`), not under the data directory, whose own `logs\` is empty. `%LOCALAPPDATA%\Claude-Data\` (the bundle's `Claude-Data\<family, lowercased>` candidate) and `%LOCALAPPDATA%\Claude-3p\` exist and are empty. The data directory holds `ant-did`, `ant-device-registry.json`, `buddy-tokens.json`, `ccd-ids.json`, `claude_desktop_config.json`, `config.json`, `cowork-enabled-cli-ops.json`, `DIPS`, `fcache`, `git-worktrees.json`, `Local State`, `lockfile`, `plan-usage-history.json`, `Preferences`, `window-state.json`, and the directories `claude-code\<version>\<hash>\claude.exe` (247 MB), `claude-code-sessions\`, `local-agent-mode-sessions\`, `spaces-present\`, `IndexedDB\`, `Local Storage\`, `Session Storage\`, `WebStorage\`, `logs\` and the Chromium caches.
- Linux: official `.deb` exists (claude-desktop-debian 3.0.0 "repackages that official Linux .deb"); config at `~/.config/Claude/claude_desktop_config.json` (README). This is the XDG config dir, no `~/.local/share` use reported.

Enterprise/3p build (data-storage doc table): macOS `~/Library/Application Support/Claude-3p/` + `~/Library/Logs/Claude-3p/`; Windows `%LOCALAPPDATA%\Claude-3p\` (logs inside; earlier releases used `%APPDATA%\Claude-3p\`, migrated on first launch); Linux `~/.config/Claude-3p/` (logs inside).

Contents of the application-data directory (data-storage doc, documented for 3p; the same layout names appear in standard builds per the issues above):

- `ant-did` device id; `configLibrary/_meta.json`, `<id>.json`.
- `local-agent-mode-sessions/`: Cowork and Chat history, one `local_<uuid>.json` plus a working dir per session, scoped by account and org id; `uploads/`, `outputs/`, `audit.jsonl` (HMAC-chained event log) with `.audit-key`; `.../cowork_account_settings.json`; `.../memory/CLAUDE.md` and `memory/memory/*.md`; `.../spaces/<projectId>/memory/`.
- `claude-code-sessions/`: Code session records (working folder, settings, title, summary); transcripts are in `~/.claude/projects/`.
- `claude-code/`, `claude-code-vm/` (bundled Claude Code binary and VM workspace), `vm_bundles/` (VM bundle and data disk), `cowork_plugins/`, `IndexedDB/`, `Local Storage/`, `Session Storage/`.
- Logs: `main.log`, `cowork_vm_node.log`, `claude.ai-web.log`, `mcp.log`, `mcp-server-<name>.log`.
- User outputs outside the app dir: `~/Claude/` (legacy `~/Documents/Claude/`).
- `claude_desktop_config.json` (MCP servers, may hold `env` API keys), `developer_settings.json`, `config.json` (see 3), Electron `Local State`, `Preferences`, `Cookies`, `Cache/`, `Code Cache/`, `GPUCache/`, `DawnGraphiteCache/`, `DawnWebGPUCache/`, `sentry/` (standard Chromium/Electron layout; names from prior catalog, consistent with the OSCrypt `Local State` dependency reported in issue 105).

## 3. Credentials

- `config.json` in the app-data dir, keys `oauth:tokenCacheV2` (live grant, includes `refreshToken`, `expiresAt`, `scopes`) and legacy `oauth:tokenCache`; value is base64 OSCrypt `v10` + nonce + AES-256-GCM ciphertext, key from `Local State` (DPAPI on Windows) (issue 105, PR 6). Docs: "OAuth tokens ... encrypted with the operating system's secure storage (Keychain on macOS, DPAPI on Windows)". So `config.json` + `Local State` together are the credential; on Linux the Chromium safe-storage key comes from the keyring or the fixed "peanuts" key.
- Transient files (docs): `host-creds-<random-id>.json` (resolved inference bearer token or API key, 0600), `ccd-session-secrets/<session-id>/` (GCP ADC / AWS files), and the same cloud credential files inside each Cowork session working directory. Deleted on quit/session end but recoverable on image.
- `claude_desktop_config.json` `mcpServers.*.env` can embed API keys (MCP debugging doc example). `configLibrary/<id>.json` can hold an API key saved from the configuration window (docs: not encrypted).
- `.audit-key` per session: HMAC key, OS-keychain encrypted.
- `Cookies` (Chromium cookie DB) holds claude.ai session cookies.
- Not credentials (real install): `buddy-tokens.json` is a daily token-usage counter, and `ccd-ids.json` holds a `salt`. Neither is flagged.
- On the Windows Store build all of the above sit under the Packages data directory (section 2); the secret globs name both package families.

## 4. Exclusions

`*/Claude*/Cache`, `Code Cache`, `GPUCache`, `DawnGraphiteCache`, `DawnWebGPUCache`, `*/Claude*/claude-code`, `*/Claude*/claude-code-vm`, `*/Claude*/vm_bundles` (docs: binary, VM workspace, VM bundle and data disk; observed on macOS 2.31226.1: `claudevm.bundle/rootfs.img` 10 GiB, `sessiondata.img` 29 MiB, kernel and initrds 87 MiB, see [`docs/coverage.md`](../docs/coverage.md) "Cowork VM disks"), `*/Claude*/sentry`. Keep `IndexedDB/`, `Local Storage/`, `Session Storage/` (UI state, recent folders). `local-agent-mode-sessions/*/uploads` can be large but is evidence.

## 5. Project-local files

None written by the desktop app itself. Code sessions run Claude Code, which writes the `.claude/`, `CLAUDE.md`, `.mcp.json` set (see claude-code). Cowork sessions mount the working folder into the VM; attached files are hard-linked into `uploads/`.

## 6. Where the project path is recorded

- `claude-code-sessions/` records "each session's working folder" (docs). File names and keys are not documented; treat as JSON to grep for absolute paths.
- `local-agent-mode-sessions/.../local_<uuid>.json` session state; `spaces/<projectId>/` for Cowork projects (docs). Exact key names undocumented.
- `Local Storage/` holds "recent folders" (docs) in LevelDB.

## 7. Confidence

High: the Windows Store build's data directory under `Packages`, its logs in `%LOCALAPPDATA%\Claude\logs`, the empty `Claude-Data` and `Claude-3p` directories, and the root file names there (real install, 2026-10-10); app-dir and log locations per OS (docs), 3p layout and file names (docs), `config.json` token keys and OSCrypt scheme (two independent community reports plus docs statement on secure storage). Medium: the `AnthropicPBC.Claude_fnn82j28hfe8t` family and the `Claude-Data\<family>` data directory (bundle only, not observed in use); that every 3p subdirectory name also appears in the standard build (docs say the two share a layout but document only 3p); Linux decryption key source. Not determined: where an unpackaged (non-Store) Windows install puts its logs today; IndexedDB schema. The `claude-code-sessions/` record keys are in the analyzer research document. `CLAUDE_USER_DATA_DIR` moves the data and log directories anywhere and is not a catalog line (see [`docs/coverage.md`](../docs/coverage.md)).
