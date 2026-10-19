# copilot (GitHub Copilot OAuth token store shared by editor plugins)

## 1. Source and evidence level

**Source/bundle**: [github/copilot.vim](https://github.com/github/copilot.vim), shallow clone at `scratchpad/repos/copilot.vim`, HEAD [a12fd5672110c8aa7e3c8419e28c96943ca179be](https://github.com/github/copilot.vim/commit/a12fd5672110c8aa7e3c8419e28c96943ca179be) (2026-01-09). The plugin vendors the closed `@github/copilot-language-server` 1.408.0 ([`copilot-language-server/package.json`](https://github.com/github/copilot.vim/blob/a12fd5672110c8aa7e3c8419e28c96943ca179be/copilot-language-server/package.json)) as a minified bundle [`copilot-language-server/dist/main.js`](https://github.com/github/copilot.vim/blob/a12fd5672110c8aa7e3c8419e28c96943ca179be/copilot-language-server/dist/main.js) (7.2 MB); the token-store code is in that bundle (readable JS, cited by function name). [`autoload/copilot/client.vim:514-515`](https://github.com/github/copilot.vim/blob/a12fd5672110c8aa7e3c8419e28c96943ca179be/autoload/copilot/client.vim#L514-L515) names the bundle. Confirmed names-only that `~/.config/github-copilot` is absent on this host (no editor Copilot installed), so no local confirmation.

- **Source review (2026-10-19)**: HEAD of github/copilot.vim is still [`a12fd56`](https://github.com/github/copilot.vim/commit/a12fd5672110c8aa7e3c8419e28c96943ca179be), vendoring the same language server 1.408.0, so the bundle is the one cited above (`dist/main.js`, sha256 `580e594aa8305d73e5af1f6e54124ccfc35f2aed6e5af3cb7b57546049e8b81f`; offsets below are byte offsets into it). The language server is closed source; everything here rests on that bundle. One line per class:
  - Permission: none on disk. The terminal, edit and MCP auto-approve rules reach the server as editor configuration (`tools.terminal.autoApprove`, `tools.edit.autoApprove`, `tools.mcp.autoApprove`; `copilot-language-server 1.408.0 dist/main.js` `applyTerminalAutoApproveConfiguration`, `applyEditAutoApproveConfiguration`, `applyMCPAutoApproveConfiguration`) and are not written by it; they live in each editor's own settings.
  - Model: none on disk from the server.
  - Past use: none. No quoted `.jsonl` file name and no conversation file occurs in the bundle (grepped for quoted `*.json`, `*.jsonl`, `*.db` and `*.log` names, and for `persistConversation` and `saveConversation`); chat history is the editor's.
  - Sync, relay and origin: none on disk.
  - Scratch directories: none. A workspace index lives in a cache directory outside the catalog ([section 2](#2-per-user-storage)).
  - Deletion: the server keeps no session, so there is nothing for a delete to leave behind.
  - Version drift: none (same commit); the earlier statement that `versions.json` is not written was wrong ([section 2](#2-per-user-storage)).
  - Bad lines: not a collector concern.

The "nothing to parse" verdict stands.

## 2. Per-user storage

[`main.js`](https://github.com/github/copilot.vim/blob/a12fd5672110c8aa7e3c8419e28c96943ca179be/copilot-language-server/dist/main.js) `function Alt()` ("getXdgConfigPath"):

```text
XDG_CONFIG_HOME set and absolute → $XDG_CONFIG_HOME/github-copilot
win32                            → %USERPROFILE%\AppData\Local\github-copilot
else                             → $HOME/.config/github-copilot
```

So macOS and Linux use the XDG config dir `~/.config/github-copilot` (no Library path), Windows uses `AppData\Local`. The only relocation variable is `XDG_CONFIG_HOME`. Files written there (same function's caller in [`main.js`](https://github.com/github/copilot.vim/blob/a12fd5672110c8aa7e3c8419e28c96943ca179be/copilot-language-server/dist/main.js)):

- `apps.json`: current store, object keyed `"<host>:<githubAppId>"` → `{user, oauth_token, githubAppId}`.
- `hosts.json`: legacy store keyed by host → `{user, oauth_token}`; on startup entries are copied into `apps.json` and `hosts.json` is deleted (`writeFile(join(l,"apps.json"))` then `rm(join(l,"hosts.json"),{force:true})`).
- `versions.json` and `oauth.json` (correction, source review 2026-10-19): the literal `versions.json` is not in the bundle, but the store is a `FilePersistenceManager` that writes each setting to `<directory>/<setting>.json` (`copilot-language-server 1.408.0 dist/main.js @5030498` `static{a(this,"FilePersistenceManager")}`, `@5030696` ``let s=`${this.directory}/${r}.json` ``), and two settings use it: `versions`, the editor plugin's name mapped to its installed version (`@6728429` `get(Hn).read("versions",r.name)`), and `oauth`, the OAuth sessions of an authentication provider keyed by provider id, `https://github.com/login/oauth` for GitHub (`@6928563` `static{this.providerId="https://github.com/login/oauth"}`, `@6928865` `read("oauth",this.id)`). Both match the `*.json` secret glob for this directory.

The server also has a cache root, `$XDG_CACHE_HOME/github-copilot` when that is absolute, else `%USERPROFILE%\AppData\Local\Temp\github-copilot` on Windows and `~/.cache/github-copilot` elsewhere (`@6043578` `a(wEt,"getXdgCachePath")`). Under it `project-index/<folder name>.<first 8 hex of SHA-256 of the folder path>/` holds the workspace index databases `local-index.db` and `workspace-chunks.db` (`@6181541` `"project-index"`, `@6181570` `a(x8e,"getWorkspaceCachePath")`, `@6208330` `"local-index.db"`, `@6182984` `"workspace-chunks.db"`). It is a rebuildable code index, not collected; its directory names give a workspace's folder name but not its path. When the server builds the index was not determined.
The language server also creates `$TMPDIR/github-copilot-<rand>` temp dirs on non-Windows (same code), outside home. Logs go to the editor (Vim `:Copilot log`), not to this directory. The same store is read by Copilot plugins for Neovim, JetBrains, Xcode and Vim because they embed the same language server; the GitHub Copilot CLI does not use it (see copilot-cli). VS Code's Copilot Chat state lives in `User/globalStorage` (covered by the vscode entries) and its token in the VS Code secret store, not here.

## 3. Credentials

`apps.json` and `hosts.json` hold the GitHub OAuth token in plaintext (`oauth_token` field) with the GitHub login (`user`). `oauth.json` holds an authentication provider's OAuth sessions ([section 2](#2-per-user-storage)); already flagged by the directory's `*.json` secret glob. No keychain use in this path. No config file embeds API keys.

## 4. Exclusions

None; the directory holds only small JSON files.

## 5. Project-local files

Read only: `.github/copilot-instructions.md`, `.github/git-commit-instructions.md`, `.github/instructions/` ([`main.js`](https://github.com/github/copilot.vim/blob/a12fd5672110c8aa7e3c8419e28c96943ca179be/copilot-language-server/dist/main.js) constants `QNi`, `jNi`, `Ckr`). Nothing written.

## 6. Where the project path is recorded

Not recorded; the store is per host, not per workspace.

## 7. Confidence

High: path resolution and both file names with their fields (readable code in the shipped bundle, version pinned). Medium: that JetBrains/Xcode plugins use the same store (same language server, but their bundles were not inspected). Not determined: whether a `versions.json` or terms-acceptance file is written by other editor hosts.
