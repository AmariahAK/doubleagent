<#
.SYNOPSIS
  Forensic collector for AI coding agent artifacts on Windows.

.DESCRIPTION
  Windows counterpart of collect-agent-artifacts.sh. Collects the on-disk state
  of AI coding agents (Claude Code, Gemini CLI, Antigravity, Codex CLI, Copilot
  CLI, Cursor, Windsurf, Continue, Aider, Ollama, ...) for every user profile on
  a host, from Docker and Podman named volumes it can reach on disk, into a
  single tar.gz (via the built-in tar.exe on Windows 10 1803+) or zip, with a JSONL
  manifest. Same catalog, manifest schema and archive layout as the sh script.
  Host state (processes, users, network, shell histories) is left to the EDR
  it supplements.

  Windows PowerShell 5.1 compatible. No modules, no prompts, nothing from stdin.
  Run as:  powershell.exe -ExecutionPolicy Bypass -File Collect-AgentArtifacts.ps1 -OutputDir C:\ir

.PARAMETER OutputDir
  Directory for the archive (default: current directory).
.PARAMETER Root
  Alternate root such as a mounted disk image (image mode).
.PARAMETER Users
  Comma-separated profile names to collect (default: all).
.PARAMETER Project
  Extra project directory to collect (repeatable). A relative path is
  resolved against the current location, and the path is never prefixed
  with -Root.
.PARAMETER Full
  Disable default size exclusions.
.PARAMETER NoSecrets
  Skip credential files instead of collecting them.
.PARAMETER NoProjects
  Skip project-level artifact discovery.
.PARAMETER NoDocker
  Skip Docker and Podman volume enumeration. Docker Desktop keeps Linux volumes
  inside a WSL virtual disk that this script cannot reach; it only notes that.
.PARAMETER MaxFileSizeMB
  Skip files larger than this (default 256, 0 = none).
.PARAMETER KeepStaging
  Keep the staging directory after archiving.
.PARAMETER Inventory
  Write nothing: walk the catalog with file metadata only and print one JSON
  line per user and agent found (file count, bytes, first and last
  modification time) to stdout. -OutputDir is ignored.
.PARAMETER List
  Print the artifact catalog and exit.
.PARAMETER Quiet
  Only print the final summary.
.PARAMETER Version
  Print version and exit.

.NOTES
  Copyright 2026 Sean Whalen
  SPDX-License-Identifier: Apache-2.0
  Exit codes: 0 archive written (per-file errors are in the manifest), or,
                with -Inventory, the walk ran,
              1 usage error, 2 fatal.
#>
[CmdletBinding()]
param(
  [Alias('o')][string]$OutputDir = '.',
  [Alias('r')][string]$Root = '',
  [Alias('u')][string]$Users = '',
  [Alias('p')][string[]]$Project = @(),
  [switch]$Full,
  [switch]$NoSecrets,
  [switch]$NoProjects,
  [switch]$NoDocker,
  [int]$MaxFileSizeMB = 256,
  [Alias('k')][switch]$KeepStaging,
  [switch]$Inventory,
  [switch]$List,
  [Alias('q')][switch]$Quiet,
  [switch]$Version
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'Continue'
$ToolVersion = '1.12.0'
$TOOL = 'collect-agent-artifacts'

# ---------------------------------------------------------------------------
# Artifact catalog. Identical to the tables in collect-agent-artifacts.sh;
# tests/catalog-sync.sh fails if they drift. agent|glob relative to each home.
# ---------------------------------------------------------------------------
$CATALOG = @'
# Anthropic
claude-code|.claude
claude-code|.claude.json*
# Claude Code config homes moved with CLAUDE_CONFIG_DIR (~/.claude-work):
# anchored on Claude-only names, never a bare .claude-*
claude-code|.claude-*/projects
claude-code|.claude-*/file-history
claude-code|.claude-*/history.jsonl
claude-code|.claude-*/.claude.json*
claude-code|.claude-*/.credentials.json
claude-code|.claude-*/hfi-auth.json
claude-code|.claude-*/.session_ingress_token
claude-code|.claude-*/remote/.oauth_token
claude-code|.claude-*/remote/.api_key
claude-code|.local/share/claude
# Claude Code CLI cache: MCP server logs per project (#81). The Windows
# entry names the children of Cache/: the PowerShell exclusion match ignores
# case, so */Claude*/Cache would prune claude-cli-nodejs/Cache itself
claude-code|Library/Caches/claude-cli-nodejs
claude-code|.cache/claude-cli-nodejs
claude-code|AppData/Local/claude-cli-nodejs/Cache/*
claude-desktop|Library/Application Support/Claude
claude-desktop|Library/Application Support/Claude-3p
claude-desktop|Library/Logs/Claude
claude-desktop|Library/Logs/Claude-3p
claude-desktop|.config/Claude
claude-desktop|.config/Claude-3p
claude-desktop|AppData/Roaming/Claude
claude-desktop|AppData/Roaming/Claude-3p
claude-desktop|AppData/Local/Claude-3p
# Claude Desktop MSIX build: userData is virtualised under Packages,
# logs stay in AppData/Local/Claude, Claude-Data is the unpackaged fallback
claude-desktop|AppData/Local/Claude
claude-desktop|AppData/Local/Claude-Data
claude-desktop|AppData/Local/Packages/Claude_*/LocalCache/Roaming/Claude
claude-desktop|AppData/Local/Packages/AnthropicPBC.Claude_*/LocalCache/Roaming/Claude
claude-desktop|Claude
claude-desktop|Documents/Claude
# Google. The antigravity entries nest inside ~/.gemini and claim their
# subtrees: .gemini/antigravity is the data directory of the desktop app
# (2.x, the Electron app), antigravity-cli that of the CLI, antigravity-ide
# that of the separately installed IDE, and antigravity-backup the backup
# the app takes when it migrates IDE data. The Antigravity directory under
# the Electron roots is the user-data directory of the desktop app; its
# logs are in Library/Logs on macOS and in its logs/ subdirectory elsewhere
# (#83). Its Cache exclusion names the three bases: the PowerShell match
# ignores case, so */Antigravity/Cache would also prune
# .gemini/antigravity/cache. The CLI keeps plugin secrets in a file store,
# plugin-secrets.json, in a lower-case antigravity directory under the Go
# os.UserConfigDir() root when no keychain is available (#90)
gemini-cli|.gemini
gemini-cli|.cache/.gemini
antigravity|.gemini/antigravity-cli
antigravity|.gemini/antigravity-ide
antigravity|.gemini/antigravity
antigravity|.gemini/antigravity-backup
antigravity|.gemini/config
antigravity|.antigravity
antigravity|.cache/antigravity
antigravity|.config/Antigravity
antigravity|Library/Application Support/Antigravity
antigravity|Library/Logs/Antigravity
antigravity|AppData/Roaming/Antigravity
antigravity|.config/antigravity/plugin-secrets.json
antigravity|Library/Application Support/antigravity/plugin-secrets.json
antigravity|AppData/Roaming/antigravity/plugin-secrets.json
antigravity|.config/Antigravity IDE/User
antigravity|.config/Antigravity IDE/logs
antigravity|Library/Application Support/Antigravity IDE/User
antigravity|Library/Application Support/Antigravity IDE/logs
antigravity|AppData/Roaming/Antigravity IDE/User
antigravity|AppData/Roaming/Antigravity IDE/logs
# OpenAI
codex-cli|.codex
codex-cli|Library/Application Support/com.openai.codex
chatgpt-desktop|Library/Application Support/com.openai.chat
chatgpt-desktop|AppData/Local/Packages/OpenAI.ChatGPT-Desktop_*/LocalCache/Roaming/ChatGPT
chatgpt-desktop|AppData/Local/Packages/OpenAI.ChatGPT-Desktop_*/LocalState
# GitHub Copilot (CLI, and the OAuth token store used by Copilot plugins)
copilot-cli|.copilot
copilot-cli|.config/.copilot
copilot-cli|.local/state/.copilot
copilot-cli|.cache/copilot
copilot-cli|Library/Caches/copilot
copilot-cli|AppData/Local/copilot
copilot|.config/github-copilot
copilot|AppData/Local/github-copilot
# Cursor
cursor|.cursor
cursor|.config/cursor
cursor|AppData/Roaming/Cursor/auth.json
cursor|.cursor-server/data/User
cursor|Library/Application Support/Cursor/User
cursor|Library/Application Support/Cursor/logs
cursor|.config/Cursor/User
cursor|.config/Cursor/logs
cursor|AppData/Roaming/Cursor/User
cursor|AppData/Roaming/Cursor/logs
# VS Code and VSCodium: globalStorage holds Copilot Chat, Cline, Roo, Kilo, Continue, Augment state
vscode|.vscode*/extensions/extensions.json
vscode|Library/Application Support/Code*/User
vscode|Library/Application Support/Code*/logs
vscode|.config/Code*/User
vscode|.config/Code*/logs
vscode|AppData/Roaming/Code*/User
vscode|AppData/Roaming/Code*/logs
vscode|Library/Application Support/VSCodium*/User
vscode|Library/Application Support/VSCodium*/logs
vscode|.config/VSCodium*/User
vscode|.config/VSCodium*/logs
vscode|AppData/Roaming/VSCodium*/User
vscode|AppData/Roaming/VSCodium*/logs
vscode|Library/Application Support/Positron/User
vscode|.config/Positron/User
vscode|AppData/Roaming/Positron/User
vscode|Library/Application Support/Trae*/User
vscode|.config/Trae*/User
vscode|AppData/Roaming/Trae*/User
vscode|.vscode*/argv.json
vscode|.vscode*/cli/token*.json
# Remote development servers (WSL, SSH, tunnels) keep the same User layout on the remote host
vscode|.vscode-server*/data/User
vscode|.vscode-server*/data/logs
vscode|.vscodium-server*/data/User
vscode|.positron-server/data/User
# VS Code family extension state. Each editor User directory is collected
# above; these nested entries claim the agent extension globalStorage from
# that walk so Cline, Roo, Kilo, Continue, Cody and Twinny files are
# attributed to them.
cline|.config/*/User/globalStorage/saoudrizwan.claude-dev
cline|Library/Application Support/*/User/globalStorage/saoudrizwan.claude-dev
cline|AppData/Roaming/*/User/globalStorage/saoudrizwan.claude-dev
roo-code|.config/*/User/globalStorage/rooveterinaryinc.roo-cline
roo-code|Library/Application Support/*/User/globalStorage/rooveterinaryinc.roo-cline
roo-code|AppData/Roaming/*/User/globalStorage/rooveterinaryinc.roo-cline
kilo-code|.config/*/User/globalStorage/kilocode.kilo-code
kilo-code|Library/Application Support/*/User/globalStorage/kilocode.kilo-code
kilo-code|AppData/Roaming/*/User/globalStorage/kilocode.kilo-code
continue|.config/*/User/globalStorage/continue.continue
continue|Library/Application Support/*/User/globalStorage/continue.continue
continue|AppData/Roaming/*/User/globalStorage/continue.continue
cody|.config/*/User/globalStorage/sourcegraph.cody-ai
cody|Library/Application Support/*/User/globalStorage/sourcegraph.cody-ai
cody|AppData/Roaming/*/User/globalStorage/sourcegraph.cody-ai
twinny|.config/*/User/globalStorage/rjmacarthy.twinny
twinny|Library/Application Support/*/User/globalStorage/rjmacarthy.twinny
twinny|AppData/Roaming/*/User/globalStorage/rjmacarthy.twinny
cline|.*-server*/data/User/globalStorage/saoudrizwan.claude-dev
roo-code|.*-server*/data/User/globalStorage/rooveterinaryinc.roo-cline
kilo-code|.*-server*/data/User/globalStorage/kilocode.kilo-code
continue|.*-server*/data/User/globalStorage/continue.continue
cody|.*-server*/data/User/globalStorage/sourcegraph.cody-ai
twinny|.*-server*/data/User/globalStorage/rjmacarthy.twinny
# Windsurf (rebranding to Devin)
windsurf|.codeium
windsurf|.windsurf
windsurf|.devin
windsurf|.config/devin
windsurf|.local/share/devin
windsurf|AppData/Roaming/devin
windsurf|Library/Application Support/Windsurf/User
windsurf|Library/Application Support/Windsurf/logs
windsurf|.config/Windsurf/User
windsurf|.config/Windsurf/logs
windsurf|AppData/Roaming/Windsurf/User
windsurf|AppData/Roaming/Windsurf/logs
windsurf|Library/Application Support/Devin/User
windsurf|Library/Application Support/Devin/logs
windsurf|.config/Devin/User
windsurf|.config/Devin/logs
windsurf|AppData/Roaming/Devin/User
windsurf|AppData/Roaming/Devin/logs
windsurf|.windsurf-server/data/User
windsurf|.devin-server/data/User
# Cline, Roo Code, Kilo Code
cline|.cline
cline|Documents/Cline
cline|Cline/Rules
roo-code|.roo
roo-code|.roo-code
roo-code|.vscode-mock
roo-code|.local/share/Roo-Code
roo-code|AppData/Roaming/Roo-Code
kilo-code|.kilo
kilo-code|.kilocode
kilo-code|.kilocodemodes
kilo-code|.config/kilo
kilo-code|.local/share/kilo
kilo-code|.local/state/kilo
# Continue
continue|.continue
# Aider (history files live in the repo; these are the home-level ones)
aider|.aider
aider|.aider.conf.yml
aider|.aider.model.settings.yml
aider|.aider.model.metadata.json
aider|.aider.chat.history.md
aider|.aider.input.history
aider|.aider.llm.history
# OpenCode (xdg-basedir: same paths on macOS and Windows)
opencode|.config/opencode
opencode|.opencode
opencode|.local/share/opencode
opencode|.local/state/opencode
# Crush (~/.config on every OS; sessions live in each project .crush/crush.db)
crush|.config/crush
crush|.local/share/crush
crush|AppData/Local/crush
crush|.crush
crush|.cache/crush
# Goose (XDG on macOS too; Electron app dir is separate)
goose|.config/goose
goose|.local/share/goose
goose|.local/state/goose
goose|.config/Goose
goose|Library/Application Support/Goose
goose|AppData/Roaming/Block/goose
goose|Library/Application Support/Block/goose
goose|AppData/Roaming/Goose
goose|.goose
# Zed (config in ~/.config/zed on macOS too; data under Library)
zed|.config/zed
zed|.local/share/zed
zed|Library/Application Support/Zed
zed|Library/Logs/Zed
zed|AppData/Roaming/Zed
zed|AppData/Local/Zed
zed|.var/app/dev.zed.Zed/config/zed
zed|.var/app/dev.zed.Zed/data/zed
zed|.var/app/dev.zed.ZedPreview/config/zed
zed|.var/app/dev.zed.ZedPreview/data/zed
zed|.var/app/dev.zed.ZedNightly/config/zed
zed|.var/app/dev.zed.ZedNightly/data/zed
# Qwen Code
qwen-code|.qwen
# Amp (data dir is ~/.local/share/amp on every OS; threads are server-side)
amp|.config/amp
amp|.local/share/amp
amp|.cache/amp/logs
amp|.cache/amp/terminal
amp|.amp
amp|AppData/Local/amp/logs
# Factory Droid
factory-droid|.factory
# Meta Muse Code (XDG ~/.config/muse and ~/.local/share/muse on every OS; launcher state in its install dir)
muse-code|.config/muse
muse-code|.local/share/muse
muse-code|.muse
muse-code|.local/bin/.muse-*
muse-code|AppData/Local/Programs/muse
muse-code|AppData/LocalLow/muse-shell-sandbox-*
# Augment (auggie CLI; the VS Code extension state is under the vscode entries)
augment|.augment
# Kiro (CLI, legacy Amazon Q CLI, and the Kiro IDE which is a VS Code fork)
kiro|.kiro
kiro|.kiro-server/data/User
kiro|.aws/amazonq
kiro|.aws/sso/cache
kiro|.local/share/kiro-cli
kiro|.local/share/amazon-q
kiro|Library/Application Support/kiro-cli
kiro|Library/Application Support/amazon-q
kiro|AppData/Local/kiro-cli
kiro|AppData/Local/amazon-q
kiro|.config/Kiro/User
kiro|.config/Kiro/logs
kiro|Library/Application Support/Kiro/User
kiro|Library/Application Support/Kiro/logs
kiro|AppData/Roaming/Kiro/User
kiro|AppData/Roaming/Kiro/logs
# PearAI (VS Code fork; ~/.pearai is both the editor extension dir and the Continue fork home)
pearai|.pearai
pearai|.config/PearAI/User
pearai|.config/PearAI/logs
pearai|.config/pearai/User
pearai|Library/Application Support/PearAI/User
pearai|Library/Application Support/PearAI/logs
pearai|AppData/Roaming/PearAI/User
pearai|AppData/Roaming/PearAI/logs
pearai|.pearai-server/data/User
# Sourcegraph Cody (VS Code chat history and token are rows in state.vscdb; JetBrains and agent state under Cody-nodejs)
cody|.vscode/cody.json
cody|.cody
cody|.local/share/Cody-nodejs
cody|.config/Cody-nodejs
cody|.local/state/Cody-nodejs
cody|Library/Application Support/Cody-nodejs
cody|Library/Preferences/Cody-nodejs
cody|Library/Logs/Cody-nodejs
cody|AppData/Local/Cody-nodejs
cody|AppData/Roaming/Cody-nodejs
# Twinny (chats are rows in state.vscdb; embeddings, node and server state under ~/.twinny)
twinny|.twinny
# Tabby (self-hosted server state, editor agent config, JetBrains plugin settings)
tabby|.tabby
tabby|.tabby-client
tabby|.config/JetBrains/*/options/intellij-tabby*.xml
tabby|Library/Application Support/JetBrains/*/options/intellij-tabby*.xml
tabby|AppData/Roaming/JetBrains/*/options/intellij-tabby*.xml
# Open Interpreter (a Codex CLI fork with the Codex layout under ~/.openinterpreter)
open-interpreter|.openinterpreter
open-interpreter|.config/open-interpreter
open-interpreter|.config/Open Interpreter*
open-interpreter|Library/Application Support/open-interpreter
open-interpreter|Library/Application Support/Open Interpreter*
open-interpreter|AppData/Local/open-interpreter
open-interpreter|AppData/Local/Open Interpreter*
open-interpreter|.cache/open-interpreter
# OpenHands (CLI and Agent Server under ~/.openhands; Agent Canvas desktop app)
openhands|.openhands
openhands|Library/Application Support/OpenHands Agent Canvas
openhands|.config/OpenHands Agent Canvas
openhands|AppData/Roaming/OpenHands Agent Canvas
# pi (same path on every OS); little-coder runs pi and its prompt history is a nested entry
pi|.pi
little-coder|.little-coder
little-coder|.config/little-coder
little-coder|.cache/little-coder
little-coder|.pi/agent/little-coder-prompt-history.json
# Letta Code, and the retired Letta (MemGPT) server
letta|.letta
letta|.config/letta
letta|.memgpt
# Hermes Agent (Nous Research; AppData/Local/hermes on Windows, Electron app dir Hermes)
hermes|.hermes
hermes|.hermes_*
hermes|AppData/Local/hermes
hermes|AppData/Local/hermes_*
hermes|.config/Hermes
hermes|Library/Application Support/Hermes
hermes|AppData/Roaming/Hermes
# OpenClaw (formerly Clawdbot and Moltbot; profiles are ~/.openclaw-<profile>, ~/.clawdbot may be a symlink)
openclaw|.openclaw
openclaw|.openclaw-*
openclaw|.clawdbot
openclaw|.moltbot
openclaw|.config/openclaw
openclaw|Library/Application Support/OpenClaw
openclaw|Library/LaunchAgents/ai.openclaw.*
openclaw|.config/systemd/user/openclaw-*
openclaw|.config/systemd/user/clawdbot-*
# nanobot (instances are ~/.nanobot-<name>)
nanobot|.nanobot
nanobot|.nanobot-*
nanobot|Library/LaunchAgents/ai.nanobot.*
nanobot|.config/systemd/user/nanobot-*
# Agent Zero (state is under the install dir, not a dot dir: installer and launcher
# default ~/agent-zero/<instance>/usr, or a clone in ~/agent-zero or ~/Desktop/agent-zero)
agent-zero|agent-zero
agent-zero|Desktop/agent-zero
agent-zero|.agent-zero
agent-zero|.local/share/a0
agent-zero|Library/Application Support/A0
agent-zero|AppData/Local/A0
agent-zero|.config/Agent Zero Launcher
agent-zero|Library/Application Support/Agent Zero Launcher
agent-zero|AppData/Roaming/Agent Zero Launcher
# ShellGPT (~/.config on every OS; chats default to the temp dir, under the home only on Windows)
shellgpt|.config/shell_gpt
shellgpt|AppData/Local/Temp/chat_cache
shellgpt|AppData/Local/Temp/shell_gpt
# Local Deep Research (platformdirs data dir; history is in an encrypted per-user database)
local-deep-research|.local/share/local-deep-research
local-deep-research|Library/Application Support/local-deep-research
local-deep-research|AppData/Local/local-deep-research
local-deep-research|Documents/LocalDeepResearch
# AutoGen Studio (~/.autogenstudio on every OS; the SQLite db settings table can hold API keys)
autogen-studio|.autogenstudio
# CrewAI (appdirs; run data dir is named after the project folder, so file-anchored lines)
crewai|.config/crewai
crewai|.crewai
crewai|.local/share/crewai
crewai|.local/share/*/latest_kickoff_task_outputs.db*
crewai|.local/share/*/flow_states.db*
crewai|.local/share/*/.crewai_user.json
crewai|Library/Application Support/crewai
crewai|Library/Application Support/*/latest_kickoff_task_outputs.db*
crewai|Library/Application Support/*/flow_states.db*
crewai|Library/Application Support/*/.crewai_user.json
crewai|AppData/Local/[Cc]rew[Aa][Ii]
# CAMEL (camel-ai; ~/.camel is shared with Apache Camel JBang, so only CAMEL-specific names)
camel-ai|.camel/gmail_token.json
camel-ai|.camel/skills
camel-ai|.config/camel
# Dify (server state is in bind mounts beside the compose file; difyctl client config)
dify|.config/difyctl
dify|AppData/Roaming/difyctl
dify|AppData/Local/difyctl
# Flowise (~/.flowise on every OS; the README compose bind-mounts it)
flowise|.flowise
# Langflow (platformdirs cache dir; Desktop paths from docs)
langflow|.cache/langflow
langflow|Library/Caches/langflow
langflow|AppData/Local/langflow/langflow/Cache
langflow|.langflow
langflow|Library/Application Support/com.LangflowDesktop
langflow|Library/Logs/com.LangflowDesktop
langflow|AppData/Roaming/com.LangflowDesktop
langflow|AppData/Local/com.LangflowDesktop
# MetaGPT (~/.metagpt on every OS; config2.yaml holds the LLM API key)
metagpt|.metagpt
# n8n (~/.n8n on every OS; computer-use gateway logs every tool call)
n8n|.n8n
n8n|.n8n-local-gateway
n8n|.n8n-gateway
# Pydantic AI CLIs: clai prompt history and the CLAI 2.0 coding agent (~/.config on every OS)
pydantic-clai|.pydantic-ai
pydantic-clai|.config/pydantic-clai2
# Shared cross-agent directories (skills and instructions read by several agents)
shared|.agents
shared|.config/AGENTS.md
shared|.config/agents
# Ollama
ollama|.ollama
ollama|Library/Application Support/Ollama
ollama|AppData/Local/Ollama
'@

$PROJECT_CATALOG = @'
claude-code|.claude
claude-code|CLAUDE.md
claude-code|CLAUDE.local.md
project|.mcp.json
project|AGENTS.md
project|AGENTS.override.md
project|AGENT.md
project|.agents
gemini-cli|GEMINI.md
gemini-cli|.gemini
gemini-cli|.geminiignore
qwen-code|QWEN.md
qwen-code|.qwen
qwen-code|.qwenignore
codex-cli|.codex
cursor|.cursor
cursor|.cursorrules
cursor|.cursorignore
cursor|.cursorindexingignore
windsurf|.windsurf
windsurf|.windsurfrules
windsurf|.windsurfignore
windsurf|.codeiumignore
windsurf|.devin
windsurf|.devinignore
antigravity|.antigravityignore
cline|.clinerules
cline|.clineignore
cline|.cline
roo-code|.roo
roo-code|.roomodes
roo-code|.rooignore
roo-code|.roorules*
roo-code|.rooprotected
kilo-code|.kilo
kilo-code|.kilocode
kilo-code|.kilocodemodes
kilo-code|.kilocodeignore
kilo-code|.kilocoderules
kilo-code|kilo.json*
continue|.continue
continue|.continuerc.json
continue|.continueignore
aider|.aider.chat.history.md
aider|.aider.input.history
aider|.aider.llm.history
aider|.aider.conf.yml
aider|.aider.model.settings.yml
aider|.aider.model.metadata.json
aider|.aiderignore
opencode|.opencode
opencode|opencode.json*
crush|.crush
crush|crush.json
crush|.crush.json
crush|crushrc
crush|.crushrc
crush|.crushignore
crush|CRUSH.md
crush|CRUSH.local.md
crush|crush.md
crush|crush.local.md
crush|Crush.md
crush|Crush.local.md
goose|.goosehints
goose|.goose
zed|.zed
zed|.rules
project|.github/copilot-instructions.md
project|.github/git-commit-instructions.md
copilot-cli|.github/copilot
project|.github/instructions
copilot-cli|.github/mcp.json
copilot-cli|.github/hooks
copilot-cli|.github/skills
copilot-cli|.github/agents
copilot-cli|.github/lsp.json
vscode|.vscode/mcp.json
amp|.amp
factory-droid|.factory
factory-droid|.factory-plugin
factory-droid|.droid.yaml
muse-code|.muse
augment|.augment
augment|.augment-guidelines
augment|.augmentignore
augment|.augment-plugin
kiro|.kiro
kiro|.kiroignore
kiro|.amazonq
kiro|AmazonQ.md
pearai|.pearairc.json
pearai|.pearaiignore
pearai|.pearai-agent
pearai|.pearai-agent-ignore
pearai|.pearai-agent-modes
cody|.cody
cody|.vscode/cody.json
cody|.sourcegraph
open-interpreter|.openinterpreter
open-interpreter|.codewhale
openhands|.openhands
pi|.pi
little-coder|.pi/approved-plan.md
pi|pi-session-*.html
letta|.letta
pydantic-clai|.clai
letta|.skills
hermes|.hermes.md
hermes|HERMES.md
hermes|.hermes
hermes|trajectory_samples.jsonl
hermes|failed_trajectories.jsonl
openclaw|.openclaw
project|SOUL.md
openclaw|IDENTITY.md
project|USER.md
openclaw|TOOLS.md
openclaw|BOOTSTRAP.md
openclaw|MEMORY.md
nanobot|.nanobot
nanobot|HEARTBEAT.md
nanobot|memory/MEMORY.md
nanobot|memory/history.jsonl
nanobot|memory/HISTORY.md
'@

$EXCLUDES = @'
.claude/cache
.claude/plugins/marketplaces
.claude/plugins/cache
.claude/plugins/*/node_modules
.claude/local/node_modules
.claude/image-cache
.claude/paste-cache
.claude/chrome
.claude/worktrees
.claude/checkpoints
.local/share/claude/versions
*/Claude*/Cache
*/Claude*/Code Cache
*/Claude*/GPUCache
*/Claude*/DawnGraphiteCache
*/Claude*/DawnWebGPUCache
*/Claude*/claude-code
*/Claude*/claude-code-vm
*/Claude*/vm_bundles
*/Claude*/sentry
.gemini/whisper_models
.gemini/bin
.gemini/tmp/bin
.gemini/extensions/*/node_modules
.gemini/extensions/*/.git
.gemini/cli-browser-profile
.gemini/antigravity/bin
.gemini/antigravity-cli/bin
.gemini/antigravity-ide/bin
.gemini/antigravity-backup/bin
.gemini/antigravity*/plugin_data/*/bin
.gemini/antigravity*/cache/marketplaces
.gemini/antigravity*/brain/*/.system_generated/worktrees
.gemini/antigravity*/lib/node_modules
.gemini/config/node_modules
*/Antigravity/Code Cache
*/Antigravity/GPUCache
*/Antigravity/DawnGraphiteCache
*/Antigravity/DawnWebGPUCache
*/Antigravity/blob_storage
*/Antigravity/Shared Dictionary
*/Antigravity/CachedData
*/Antigravity/Crashpad
*/Antigravity/Dictionaries
.config/Antigravity/Cache
Library/Application Support/Antigravity/Cache
AppData/Roaming/Antigravity/Cache
.antigravity/extensions
AppData/Local/agy
.codex/packages
.codex/cache
.codex/.tmp
.codex/plugins/cache
.codex/skills/.system
.codex/worktrees
.codex/.sandbox
.codex/.sandbox-bin
.codex/tmp
.codex/visualizations
*/Roaming/ChatGPT/Cache
*/Roaming/ChatGPT/Code Cache
*/Roaming/ChatGPT/GPUCache
*/Roaming/ChatGPT/DawnGraphiteCache
*/Roaming/ChatGPT/DawnWebGPUCache
.copilot/pkg
.copilot/installed-plugins
.cache/copilot/pkg
Library/Caches/copilot/pkg
AppData/Local/copilot/pkg
.cursor/extensions
.cursor/worktrees
.cursor/plugins/marketplaces
.cursor-server/bin
.cursor-server/extensions
*/Cursor/User/globalStorage/state.vscdb.backup
.codeium/windsurf/implicit
.codeium/*/bin
.codeium/bin
.codeium/ws-browser*
.windsurf/extensions
.devin/extensions
AppData/Local/devin/bin
*/User/globalStorage/saoudrizwan.claude-dev/checkpoints
*/User/globalStorage/saoudrizwan.claude-dev/cache
*/User/globalStorage/rooveterinaryinc.roo-cline/checkpoints
*/User/globalStorage/rooveterinaryinc.roo-cline/tasks/*/checkpoints
*/User/globalStorage/rooveterinaryinc.roo-cline/cache
*/User/globalStorage/kilocode.kilo-code/checkpoints
*/User/globalStorage/kilocode.kilo-code/cache
*/User/globalStorage/ms-*
*/User/globalStorage/vscjava*
*/User/globalStorage/redhat*
*/User/globalStorage/eamodio*
*/User/globalStorage/golang*
*/User/globalStorage/rust-lang*
*/User/globalStorage/yzane.markdown-pdf
*/User/globalStorage/github.copilot-chat/logContextRecordings
*/User/globalStorage/github.copilot-chat/workspaceRecordings
*/User/workspaceStorage/*/GitHub.copilot-chat/codebase-external.sqlite*
*/User/workspaceStorage/*/ms-*
*/User/workspaceStorage/*/vscjava*
*/User/workspaceStorage/*/redhat*
*/User/workspaceStorage/*/rust-lang*
.cline/data/checkpoint-scratch
.cline/data/workspaces/chat
.cline/data/agent-plugins
.cline/plugins
.cline/worktrees
.vscode-mock/global-storage/tasks/*/checkpoints
.vscode-mock/global-storage/checkpoints
.roo/worktrees
.roo-code/mcp
.local/share/Roo-Code/MCP
AppData/Roaming/Roo-Code/MCP
.local/share/kilo/snapshot
.local/share/kilo/repos
.local/share/kilo/tool-output
.local/share/kilo/log
.local/share/kilo/worktree
.local/state/kilo/indexing
.local/share/kilo/state/indexing
.kilo/worktrees
.kilo/bin
.continue/index/lancedb
.continue/index/*.sqlite
.continue/.utils
.continue/node_modules
.continue/out
.continue/types
.continue/.diffs
.continue/.migrations
.continue/dev_data/devdata.sqlite
.aider/caches
.aider.tags.cache*
.local/share/opencode/bin
.local/share/opencode/snapshot
.local/share/opencode/worktree
.local/share/opencode/repos
.local/share/opencode/tool-output
.config/opencode/node_modules
.opencode/bin
.opencode/node_modules
.local/share/goose/models
.local/share/goose/model_catalog
.local/state/goose/codex
.config/goose/mcp-apps-cache
AppData/Roaming/Block/goose/data/models
AppData/Roaming/Block/goose/data/model_catalog
AppData/Roaming/Block/goose/data/codex
*/Goose/Cache
*/Goose/Code Cache
*/Goose/GPUCache
*/Goose/DawnGraphiteCache
*/Goose/DawnWebGPUCache
*/Goose/blob_storage
*/[Zz]ed/extensions
*/[Zz]ed/remote_extensions
*/[Zz]ed/node
*/[Zz]ed/languages
*/[Zz]ed/copilot
*/[Zz]ed/debug_adapters
*/[Zz]ed/external_agents
*/[Zz]ed/prettier
*/[Zz]ed/remote_servers
*/[Zz]ed/devcontainer
*/[Zz]ed/embeddings
*/[Zz]ed/server_state
*/[Zz]ed/hang_traces
*/[Zz]ed/build_timings
.qwen/updates
.qwen/extension-store
.qwen/extensions/*/node_modules
.qwen/bin
.qwen/sandbox
.qwen/scratch-workspaces
.qwen/locales
.qwen/arena
.qwen/artifacts
.qwen/resources
.qwen/startup-perf
.cache/amp/runner-desktop
.cache/amp/desktop
.cache/amp/bin
.cache/amp/obelisk-runs
.amp/bin
.factory/updates
.factory/cache/sounds
.factory/bin
.factory/tools
.factory/software-factory/*/*/repos
.factory/software-factory/*/*/worktrees
.factory/temp
.factory/worktrees
.factory/snapshots
.factory/generated-images
.local/share/muse/plugins/cache/builtin
.local/share/muse/skills/bundled
.local/share/muse/plugins/marketplaces
.local/bin/.muse-update.*
AppData/Local/Programs/muse/muse-bin-*.exe
AppData/Local/Programs/muse/.muse-update.*.exe
.muse/worktrees
.augment/binaries
.augment/vfs
.augment/knowledgebase
.augment/uploads
.augment/worktrees
.augment/plugins/marketplaces
.aws/amazonq/cli-checkouts
.aws/amazonq/knowledge_bases
.kiro/extensions
.kiro/cloud-cache
.kiro/sandbox-state
.kiro/sandbox-curl
*/User/globalStorage/kiro.kiroagent/*lance*
*/User/globalStorage/kiro.kiroagent/index
.pearai/extensions
.pearai/index/lancedb
.pearai/index/*.sqlite
.pearai/types
.pearai/out
.pearai/node_modules
.pearai/.diffs
.pearai/.migrations
.pearai/dev_data/devdata.sqlite
*/User/globalStorage/pearai.pearai-roo-cline/checkpoints
*/User/globalStorage/pearai.pearai-roo-cline/tasks/*/checkpoints
*/User/globalStorage/pearai.pearai-roo-cline/cache
*/globalStorage/sourcegraph.cody-ai/symf/symf-*
*/Cody-nodejs/symf/symf-*
*/Cody-nodejs/Data/symf/symf-*
*/Cody-nodejs/dist
*/Cody-nodejs/Config/dist
.twinny/embeddings/*/chunks.lance
.twinny/server/plugins/*/repos/*/checkout
.twinny/server/plugins/*/repos/*/index
.tabby/models
.tabby/index
.tabby/repositories
.openinterpreter/packages
.openinterpreter/cache
.openinterpreter/.tmp
.openinterpreter/tmp
.openinterpreter/plugins/cache
.openinterpreter/skills/.system
.openinterpreter/worktrees
.openinterpreter/.sandbox
.openinterpreter/.sandbox-bin
.openinterpreter/visualizations
.openinterpreter/models-cache
.config/open-interpreter/models
Library/Application Support/open-interpreter/models
AppData/Local/open-interpreter/open-interpreter/models
.openhands/cache
.openhands/agent-canvas/workspaces
.openhands/agent-canvas/tmux
.pi/agent/bin
.pi/agent/tools/fd*
.pi/agent/tools/rg*
.pi/agent/tmp
.pi/agent/npm/node_modules
.pi/agent/git/*/node_modules
.pi/agent/git/*/.git
.pi/npm/node_modules
.pi/git/*/node_modules
.pi/git/*/.git
.pi/server/*.sock
.letta/bin
.letta/mod-cache
.letta/tool_execution_dir
.letta/chroma
.memgpt/chroma
.hermes/hermes-agent/[!.]*
.hermes/hermes-agent/.[!e]*
AppData/Local/hermes/hermes-agent/[!.]*
AppData/Local/hermes/hermes-agent/.[!e]*
.hermes*/models
.hermes*/runtimes
.hermes*/node
.hermes*/installs
.hermes*/tools
.hermes*/sandboxes
.hermes*/checkpoints/store/objects
.hermes*/checkpoints/store/indexes
.hermes*/checkpoints/legacy-*
.hermes*/state-snapshots
.hermes*/backups
.hermes*/browser-profile
.hermes*/browser-profiles
.hermes*/browser_profiles
.hermes*/chrome-debug
.hermes*/bot-desktop/browser-profile
.hermes*/plugins/*/node_modules
.hermes*/plugins/*/.venv
AppData/Local/hermes*/models
AppData/Local/hermes*/runtimes
AppData/Local/hermes*/node
AppData/Local/hermes*/installs
AppData/Local/hermes*/tools
AppData/Local/hermes*/sandboxes
AppData/Local/hermes*/checkpoints/store/objects
AppData/Local/hermes*/checkpoints/store/indexes
AppData/Local/hermes*/checkpoints/legacy-*
AppData/Local/hermes*/state-snapshots
AppData/Local/hermes*/backups
AppData/Local/hermes*/browser-profile
AppData/Local/hermes*/browser-profiles
AppData/Local/hermes*/browser_profiles
AppData/Local/hermes*/chrome-debug
AppData/Local/hermes*/bot-desktop/browser-profile
AppData/Local/hermes*/plugins/*/node_modules
AppData/Local/hermes*/plugins/*/.venv
.config/Hermes/Cache
.config/Hermes/Code Cache
.config/Hermes/GPUCache
Library/Application Support/Hermes/Cache
Library/Application Support/Hermes/Code Cache
Library/Application Support/Hermes/GPUCache
AppData/Roaming/Hermes/Cache
AppData/Roaming/Hermes/Code Cache
AppData/Roaming/Hermes/GPUCache
.openclaw*/dev
.openclaw*/git
.openclaw*/npm
.openclaw*/npm-runtime
.openclaw*/tmp
.openclaw*/tools
.openclaw*/worktrees
.openclaw*/plugin-skills
.openclaw*/extensions/*/node_modules
.openclaw*/sandbox/skills-workspaces
.openclaw*/agents/*/agent/tmp
.openclaw*/agents/*/agent/.tmp
.openclaw*/browser/*/user-data/*/Cache
.openclaw*/browser/*/user-data/*/Code Cache
.openclaw*/browser/*/user-data/*/GPUCache
.openclaw*/browser/*/user-data/*/Service Worker
.clawdbot/tools
.clawdbot/npm
.nanobot*/bin
.nanobot*/run
.nanobot*/cache
agent-zero*/.venv
Desktop/agent-zero*/.venv
agent-zero*/.conda
Desktop/agent-zero*/.conda
agent-zero*/.git
Desktop/agent-zero*/.git
agent-zero*/tmp/playwright
Desktop/agent-zero*/tmp/playwright
agent-zero*/tmp/memory/embeddings
Desktop/agent-zero*/tmp/memory/embeddings
agent-zero*/usr/.time_travel
Desktop/agent-zero*/usr/.time_travel
agent-zero*/usr/workdir/*/.venv
Desktop/agent-zero*/usr/workdir/*/.venv
agent-zero*/usr/workdir/*/node_modules
Desktop/agent-zero*/usr/workdir/*/node_modules
.local/share/a0/browser-profiles
Library/Application Support/A0/Browser Profiles
AppData/Local/A0/Browser Profiles
*/Agent Zero Launcher/Cache
*/Agent Zero Launcher/Code Cache
*/Agent Zero Launcher/GPUCache
*/Agent Zero Launcher/docker_manager/cache
.local/share/local-deep-research/cache
.local/share/local-deep-research/models
.local/share/local-deep-research/journal_data
.local/share/local-deep-research/library
Library/Application Support/local-deep-research/cache
Library/Application Support/local-deep-research/models
Library/Application Support/local-deep-research/journal_data
Library/Application Support/local-deep-research/library
AppData/Local/local-deep-research/local-deep-research/cache
AppData/Local/local-deep-research/local-deep-research/models
AppData/Local/local-deep-research/local-deep-research/journal_data
AppData/Local/local-deep-research/local-deep-research/library
Documents/LocalDeepResearch/Library
.flowise/vectorstore
.langflow/knowledge_bases
AppData/Roaming/com.LangflowDesktop/knowledge_bases
Library/Application Support/com.LangflowDesktop/venv
Library/Application Support/com.LangflowDesktop/python_env
AppData/Local/com.LangflowDesktop/venv
AppData/Local/com.LangflowDesktop/python_env
AppData/Local/com.LangflowDesktop/cache
.cache/langflow/profile_pictures
Library/Caches/langflow/profile_pictures
AppData/Local/langflow/langflow/Cache/profile_pictures
.n8n/nodes/node_modules
.n8n/custom/node_modules
.n8n/node-definitions
.n8n/n8n-sdk-templates
.ollama/models/blobs
AppData/Local/Ollama/updates
Library/Caches/ollama
Library/Caches/com.electron.ollama
.time_travel
usr/.time_travel
workdir/*/.venv
workdir/*/node_modules
usr/workdir/*/.venv
usr/workdir/*/node_modules
tmp/playwright
tmp/memory/embeddings
models
index
repositories
journal_data
library
agent-canvas/workspaces
agent-canvas/tmux
hermes-agent/[!.]*
hermes-agent/.[!e]*
runtimes
node
installs
tools
sandboxes
checkpoints/store/objects
checkpoints/store/indexes
checkpoints/legacy-*
state-snapshots
backups
browser-profile
browser-profiles
browser_profiles
chrome-debug
bot-desktop/browser-profile
plugins/*/node_modules
plugins/*/.venv
npm
npm-runtime
worktrees
extensions/*/node_modules
sandbox/skills-workspaces
browser/*/user-data/*/Cache
browser/*/user-data/*/Code Cache
browser/*/user-data/*/GPUCache
browser/*/user-data/*/Service Worker
bin
mod-cache
tool_execution_dir
chroma
profile_pictures
nodes/node_modules
node-definitions
n8n-sdk-templates
'@

$SECRET_GLOBS = @'
.claude/.credentials.json
.claude/.device-keys.json
.claude/hfi-auth.json
.claude/.session_ingress_token
.claude/remote/.oauth_token
.claude/remote/.api_key
.claude/sessions/*.key
.claude.json
.claude-*/.credentials.json
.claude-*/hfi-auth.json
.claude-*/.session_ingress_token
.claude-*/remote/.oauth_token
.claude-*/remote/.api_key
.claude-*/sessions/*.key
.claude-*/.claude.json
Library/Application Support/Claude*/config.json
Library/Application Support/Claude*/Cookies*
Library/Application Support/Claude*/host-creds-*.json
Library/Application Support/Claude*/ccd-session-secrets/*
.config/Claude*/config.json
.config/Claude*/Cookies*
.config/Claude*/host-creds-*.json
.config/Claude*/ccd-session-secrets/*
AppData/Roaming/Claude*/config.json
AppData/Roaming/Claude*/Cookies*
AppData/Roaming/Claude*/host-creds-*.json
AppData/Roaming/Claude*/ccd-session-secrets/*
AppData/Local/Claude*/config.json
AppData/Local/Claude*/Cookies*
AppData/Local/Claude*/host-creds-*.json
AppData/Local/Claude*/ccd-session-secrets/*
AppData/Local/Packages/Claude_*/LocalCache/Roaming/Claude*/config.json
AppData/Local/Packages/Claude_*/LocalCache/Roaming/Claude*/Cookies*
AppData/Local/Packages/Claude_*/LocalCache/Roaming/Claude*/host-creds-*.json
AppData/Local/Packages/Claude_*/LocalCache/Roaming/Claude*/ccd-session-secrets/*
AppData/Local/Packages/AnthropicPBC.Claude_*/LocalCache/Roaming/Claude*/config.json
AppData/Local/Packages/AnthropicPBC.Claude_*/LocalCache/Roaming/Claude*/Cookies*
AppData/Local/Packages/AnthropicPBC.Claude_*/LocalCache/Roaming/Claude*/host-creds-*.json
AppData/Local/Packages/AnthropicPBC.Claude_*/LocalCache/Roaming/Claude*/ccd-session-secrets/*
*/Claude*/Local State
*/Claude*/claude_desktop_config.json
*/Claude*/local-agent-mode-sessions/*/.audit-key
*/Claude*/spaces-present/*/link-key
*.gemini/oauth_creds.json
*.gemini/gemini-credentials.json
*.gemini/mcp-oauth-tokens.json
*.gemini/a2a-oauth-tokens.json
*.gemini/.env
*.gemini/extensions/*/.env
*.gemini/antigravity-cli/antigravity-oauth-token
*.gemini/antigravity*/plugin_data/*/token.json
.config/[Aa]ntigravity/plugin-secrets.json
Library/Application Support/[Aa]ntigravity/plugin-secrets.json
AppData/Roaming/[Aa]ntigravity/plugin-secrets.json
.qwen/oauth_creds.json
.qwen/mcp-oauth-tokens*.json
.qwen/extension-secrets-v1.json
.qwen/.env
.qwen/settings.json
.qwen/extensions/*/.qwen-extension-git-credentials.json
.qwen/channels/*.json
.codex/auth.json
.codex/.credentials.json
.codex/secrets/*
.codex/.sandbox-secrets/*
.codex/config.toml
.codex/.env
*/Roaming/ChatGPT/Network/Cookies*
*/Roaming/ChatGPT/Local State
.config/github-copilot/*.json
AppData/Local/github-copilot/*.json
.copilot/config.json
.copilot/mcp-oauth-config*
.copilot/mcp-config.json
.cursor/auth.json
.config/cursor/auth.json
AppData/Roaming/Cursor/auth.json
.cursor/mcp.json
.cursor/projects/*/mcp-auth.json
.vscode*/cli/token*.json
*/User/mcp.json
*/User/profiles/*/mcp.json
.codeium/config.json
.codeium/mcp_config.json
.codeium/windsurf/mcp_config.json
.config/devin/mcp_config.json
AppData/Roaming/devin/mcp_config.json
.local/share/devin/credentials.toml
AppData/Roaming/devin/credentials.toml
.cline/data/settings/providers.json
.cline/data/settings/cline_mcp_settings.json
.cline/data/settings/composio/*.json
.cline/data/secrets.json
.cline/data/connectors/settings.json
.cline/data/db/connectors.db*
.vscode-mock/global-storage/secrets.json
.local/share/kilo/auth.json
.local/share/kilo/mcp-auth.json
.local/share/kilo/kilo*.db*
.local/share/kilo/opencode*.db*
.config/kilo/kilo.json*
.config/kilo/opencode.json*
.config/kilo/config.json
.kilocode/cli/config.json
.continue/auth*.json
.continue/.env
.continue/config.yaml
.continue/config.json
.continue/config.ts
.continue/.configs/*/config.js*
.continue/mcpServers/*
.continue/index/globalContext.json
*/globalStorage/continue.continue/*.bin
.aider/oauth-keys.env
.aider.conf.yml
.aider.model.settings.yml
.local/share/opencode/auth.json
.local/share/opencode/mcp-auth.json
.local/share/opencode/opencode*.db*
.config/opencode/opencode.json*
.config/opencode/config.json
.opencode/opencode.json*
.local/share/crush/crush.json
AppData/Local/crush/crush.json
.config/crush/crush.json
.config/crush/crushrc
.config/crush/.crushrc
.crush/crush.json
.config/goose/secrets.yaml
.config/goose/config.yaml
.config/goose/githubcopilot/*
.config/goose/chatgpt_codex/*
.config/goose/gemini_oauth/*
.config/goose/kimicode/*
.config/goose/muse_code/*
.config/goose/huggingface/*
.config/goose/databricks/*
.config/goose/xai_oauth/*
.config/goose/roaming_node_key
.config/goose/tls/*
AppData/Roaming/Block/goose/config/secrets.yaml
AppData/Roaming/Block/goose/config/config.yaml
AppData/Roaming/Block/goose/config/githubcopilot/*
AppData/Roaming/Block/goose/config/chatgpt_codex/*
AppData/Roaming/Block/goose/config/gemini_oauth/*
AppData/Roaming/Block/goose/config/kimicode/*
AppData/Roaming/Block/goose/config/muse_code/*
AppData/Roaming/Block/goose/config/huggingface/*
AppData/Roaming/Block/goose/config/databricks/*
AppData/Roaming/Block/goose/config/xai_oauth/*
AppData/Roaming/Block/goose/config/roaming_node_key
AppData/Roaming/Block/goose/config/tls/*
.local/state/goose/logs/llm_request.*
AppData/Roaming/Block/goose/data/logs/llm_request.*
.config/zed/development_credentials
.config/zed/settings.json
.config/zed/settings_backup.json
.config/zed/global_settings.json
AppData/Roaming/Zed/development_credentials
AppData/Roaming/Zed/settings.json
AppData/Roaming/Zed/settings_backup.json
AppData/Roaming/Zed/global_settings.json
.var/app/dev.zed.Zed*/config/zed/settings.json
.var/app/dev.zed.Zed*/config/zed/development_credentials
.local/share/amp/secrets.json
.local/share/amp/accounts.json
.local/share/amp/accounts/*/secrets.json
.amp/oauth/*
.factory/auth.json
.factory/auth.v2.*
.factory/auth.encrypted
.factory/config.json
.factory/temp/env/*
.factory/prem-auth/*/credentials.*
.factory/mcp-oauth*
.config/muse/auth.json
.config/muse/settings.json
.augment/session.json
.augment/settings.json
.augment/settings.local.json
*/kiro-cli/data.sqlite3*
*/amazon-q/data.sqlite3*
.aws/sso/cache/*.json
.aws/amazonq/mcp.json
.kiro/settings/mcp.json
.kiro/powers/installed/*/mcp.json
.kiro/agents/*.json
.kiro/web-session/*
.kiro/secrets.json
.pearai/config.json
.pearai/config.ts
.pearai/.env
.pearai/.configs/*/config.js*
*/globalStorage/pearai.pearai-roo-cline/settings/pearai_agent_mcp_settings.json
.pearai-agent/mcp.json
*/Cody-nodejs/user-settings.json
*/Cody-nodejs/Config/user-settings.json
*/User/globalStorage/rjmacarthy.twinny/twinny-providers.json
.twinny/node/identity.json
.twinny/server/license
.twinny/server/plugins/*/settings.json
.tabby/config.toml
.tabby-client/agent/config.toml
.openinterpreter/auth.json
.openinterpreter/.credentials.json
.openinterpreter/credentials/*
.openinterpreter/device_id
.openinterpreter/secrets/*
.openinterpreter/.sandbox-secrets/*
.openinterpreter/.env
.openinterpreter/config.toml
.config/open-interpreter/profiles/*
Library/Application Support/open-interpreter/profiles/*
AppData/Local/open-interpreter/open-interpreter/profiles/*
.config/Open Interpreter*/config.yaml
Library/Application Support/Open Interpreter*/config.yaml
AppData/Local/Open Interpreter*/Open Interpreter*/config.yaml
.openhands/agent-canvas/secret-key.txt
.openhands/agent-canvas/api-key.txt
.openhands/settings.json
.openhands/secrets.json
.openhands/profiles/*
.openhands/provider-connections/*
.openhands/auth/*
.openhands/runtime-control/*
.openhands/agent_settings.json
.openhands/cloud/*
.openhands/mcp.json
.openhands/.jwt_secret
.openhands/.keys
.pi/agent/auth.json
.pi/agent/auth.json.*
.pi/agent/mcp-auth.json
.pi/agent/oauth.json*
.pi/agent/models.json
.pi/agent/mcp.json
.pi/mcp.json
.config/little-coder/models.json
.letta/settings.json
.letta/pg_uri
.letta/credentials
.letta/lc-local-backend/providers/auth.json
.letta/channels/*/accounts.json
.letta/channels/whatsapp/auth/*
.letta/agents/*/memory/.git/config
.letta/agents/*/memory/.git/letta-credential-helper.cmd
.config/letta/settings.json
.memgpt/credentials
.hermes*/.env
.hermes*/.env.bak*
.hermes*/.op.env
.hermes*/npmrc
.hermes*/auth.json
.hermes*/auth.json.*
.hermes*/auth/*
.hermes*/.anthropic_oauth.json
.hermes*/.copilot_jwt.json
.hermes*/google_*.json
.hermes*/google_chat_user_tokens/*
.hermes*/slack_tokens.json
.hermes*/honcho.json
.hermes*/mem0.json
.hermes*/webhook_subscriptions.json
.hermes*/teams_pipeline_store.json
.hermes*/mcp-tokens/*
.hermes*/vault/*
.hermes*/browser_auth/*
.hermes*/pairing/*
.hermes*/platforms/pairing/*
.hermes*/whatsapp/session/*
.hermes*/platforms/whatsapp/session/*
.hermes*/matrix/store/*
.hermes*/platforms/matrix/store/*
.hermes*/cache/bws_cache*.json
.hermes*/weixin/accounts/*
.hermes*/runtime/photon-sidecar.json
.hermes*/proxy/*
.hermes*/home/*
AppData/Local/hermes*/.env
AppData/Local/hermes*/.env.bak*
AppData/Local/hermes*/.op.env
AppData/Local/hermes*/npmrc
AppData/Local/hermes*/auth.json
AppData/Local/hermes*/auth.json.*
AppData/Local/hermes*/auth/*
AppData/Local/hermes*/.anthropic_oauth.json
AppData/Local/hermes*/.copilot_jwt.json
AppData/Local/hermes*/google_*.json
AppData/Local/hermes*/google_chat_user_tokens/*
AppData/Local/hermes*/slack_tokens.json
AppData/Local/hermes*/honcho.json
AppData/Local/hermes*/mem0.json
AppData/Local/hermes*/webhook_subscriptions.json
AppData/Local/hermes*/teams_pipeline_store.json
AppData/Local/hermes*/mcp-tokens/*
AppData/Local/hermes*/vault/*
AppData/Local/hermes*/browser_auth/*
AppData/Local/hermes*/pairing/*
AppData/Local/hermes*/platforms/pairing/*
AppData/Local/hermes*/whatsapp/session/*
AppData/Local/hermes*/platforms/whatsapp/session/*
AppData/Local/hermes*/matrix/store/*
AppData/Local/hermes*/platforms/matrix/store/*
AppData/Local/hermes*/cache/bws_cache*.json
AppData/Local/hermes*/weixin/accounts/*
AppData/Local/hermes*/runtime/photon-sidecar.json
AppData/Local/hermes*/proxy/*
AppData/Local/hermes*/home/*
.openclaw*/openclaw.json*
.openclaw*/clawdbot.json*
.openclaw*/.env
.openclaw*/credentials/*
.openclaw*/service-env/*
.openclaw*/agents/*/agent/auth-profiles.json*
.openclaw*/agents/*/agent/models.json
.openclaw*/browser/*/user-data/*/Cookies*
.clawdbot/clawdbot.json*
.clawdbot/.env
.clawdbot/credentials/*
.moltbot/moltbot.json*
.moltbot/.env
.moltbot/credentials/*
.config/openclaw/gateway.env
.nanobot*/config.json
.nanobot*/auth/*
.nanobot*/whatsapp-auth/*
.nanobot*/matrix-store/*
agent-zero*/usr/.env
Desktop/agent-zero*/usr/.env
agent-zero*/usr/secrets.env
Desktop/agent-zero*/usr/secrets.env
agent-zero*/usr/settings.json
Desktop/agent-zero*/usr/settings.json
agent-zero*/usr/projects/*/.a0proj/secrets.env
Desktop/agent-zero*/usr/projects/*/.a0proj/secrets.env
agent-zero*/.env
Desktop/agent-zero*/.env
agent-zero*/tmp/secrets.env
Desktop/agent-zero*/tmp/secrets.env
agent-zero*/tmp/settings.json
Desktop/agent-zero*/tmp/settings.json
agent-zero*/usr/plugins/_desktop/profiles/*/.ssh/*
Desktop/agent-zero*/usr/plugins/_desktop/profiles/*/.ssh/*
agent-zero*/usr/plugins/_desktop/profiles/*/.gnupg/*
Desktop/agent-zero*/usr/plugins/_desktop/profiles/*/.gnupg/*
.agent-zero/.env
.agent-zero/session_cookies.json
*/Agent Zero Launcher/docker_manager/state.json
*/Agent Zero Launcher/Local State
.config/shell_gpt/.sgptrc
.local/share/local-deep-research/.secret_key
Library/Application Support/local-deep-research/.secret_key
AppData/Local/local-deep-research/local-deep-research/.secret_key
.autogenstudio/.env
.autogenstudio/temp_env_vars.env
.config/crewai/settings.json
.local/share/crewai/credentials/*
Library/Application Support/crewai/credentials/*
AppData/Local/[Cc]rew[Aa][Ii]/credentials/*
.camel/gmail_token.json
.config/difyctl/tokens.yml
AppData/Roaming/difyctl/tokens.yml
AppData/Local/difyctl/tokens.yml
.flowise/encryption.key
.flowise/*_secret.key
.cache/langflow/*secret_key
Library/Caches/langflow/*secret_key
AppData/Local/langflow/langflow/Cache/*secret_key
.langflow/data/.env
AppData/Roaming/com.LangflowDesktop/data/.env
.metagpt/config2.yaml
.metagpt/config2.bak
.n8n/config
.n8n/ssh/*
.config/pydantic-clai2/credentials-*
.config/pydantic-clai2/logfire/logfire_credentials.json
.ollama/id_ed25519
.env
secrets.env
settings.json
projects/*/.a0proj/secrets.env
plugins/_desktop/profiles/*/.ssh/*
plugins/_desktop/profiles/*/.gnupg/*
usr/.env
usr/secrets.env
usr/settings.json
usr/projects/*/.a0proj/secrets.env
usr/plugins/_desktop/profiles/*/.ssh/*
usr/plugins/_desktop/profiles/*/.gnupg/*
tmp/secrets.env
tmp/settings.json
config.toml
id_ed25519
.secret_key
agent-canvas/secret-key.txt
agent-canvas/api-key.txt
secrets.json
profiles/*
provider-connections/*
runtime-control/*
agent_settings.json
cloud/*
mcp.json
.jwt_secret
.keys
pg_uri
credentials
lc-local-backend/providers/auth.json
channels/*/accounts.json
channels/whatsapp/auth/*
agents/*/memory/.git/config
agents/*/memory/.git/letta-credential-helper.cmd
.env.bak*
.op.env
npmrc
auth.json
auth.json.*
auth/*
.anthropic_oauth.json
.copilot_jwt.json
google_*.json
google_chat_user_tokens/*
slack_tokens.json
honcho.json
mem0.json
webhook_subscriptions.json
teams_pipeline_store.json
mcp-tokens/*
vault/*
browser_auth/*
pairing/*
platforms/pairing/*
whatsapp/session/*
platforms/whatsapp/session/*
matrix/store/*
platforms/matrix/store/*
cache/bws_cache*.json
weixin/accounts/*
runtime/photon-sidecar.json
proxy/*
home/*
openclaw.json*
clawdbot.json*
moltbot.json*
credentials/*
service-env/*
agents/*/agent/auth-profiles.json*
agents/*/agent/models.json
browser/*/user-data/*/Cookies*
config.json
whatsapp-auth/*
matrix-store/*
secret_key
cache_secret_key
config
ssh/*
'@

# Docker and Podman named volumes, agent|glob matched against the volume name.
$DOCKER_VOLUMES = @'
# Matched against each volume name; the first matching line wins. A matched
# volume is collected whole as user "docker" with its _data directory as the
# home, so EXCLUDES and SECRET_GLOBS apply relative to the volume root.
# Agent Zero: a0_usr in the README docker run (Compose prefixes it as
# <project>_a0_usr) and a0-launcher-<slug>-usr in the A0 Launcher named-volume
# mode; both are mounted at /a0/usr
agent-zero|*a0_usr
agent-zero|a0-launcher-*-usr
# Local Deep Research: ldr_data in docker-compose.yml, mounted at /data
local-deep-research|*ldr_data
# Ollama: ollama in docs/docker.mdx, ollama_data in the Local Deep Research
# compose file; mounted at /root/.ollama
ollama|ollama
ollama|*ollama*
# Dify: dify_agent_local_sandbox_home at /home/dify (shellctl job database and
# output logs under .local/share/shellctl) and dify_agent_local_sandbox_workspace
# at /workspace in docker/docker-compose.yaml; Compose prefixes them (docker_)
dify|*dify_agent_local_sandbox_home
dify|*dify_agent_local_sandbox_workspace
# Langflow: langflow-data in docker_example/docker-compose.yml, mounted at
# /app/langflow, the config dir (LANGFLOW_CONFIG_DIR)
langflow|*langflow-data
# n8n: n8n_data in the README docker run and n8n-data in the get-n8n.sh compose
# file (n8n_n8n-data); both mounted at /home/node/.n8n
n8n|*n8n_data
n8n|*n8n-data
# Inferred names: the documentation of these tools bind-mounts the home directory
# instead of a named volume; a volume replacing it has the same layout (~/.tabby
# at /data, ~/.hermes at /opt/data, ~/.openclaw at /home/node/.openclaw, ...)
tabby|*tabby*
local-deep-research|*local-deep-research*
openhands|*openhands*
letta|*letta*
hermes|*hermes*
openclaw|*openclaw*
openclaw|*clawdbot*
nanobot|*nanobot*
'@


# ===========================================================================
# 3. Shared helpers
# ===========================================================================
# Constants and small functions every later section uses: the table reader,
# logging and notes, JSON string escaping, the glob-to-regex converter,
# extended-length paths, and file-system probes that never throw.

# UTF-8 without a byte order mark, for every file the collector writes
# (Add-Content on 5.1 defaults to ASCII and mangles non-ASCII paths).
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding $false
# \ on Windows, / under PowerShell 7 on Linux or macOS.
$script:Sep = [string][System.IO.Path]::DirectorySeparatorChar

# Takes a table here-string; returns its lines that are neither empty nor a
# # comment.
function Get-TableLines([string]$table) {
  $table -split "`r?`n" | Where-Object { $_ -ne '' -and -not $_.StartsWith('#') }
}

# Takes a message; appends "<UTC time> <message>" to the run log through
# $script:LogWriter when one is open (-Inventory opens none) and writes the
# message alone to stderr unless -Quiet.
function Write-CollectorLog([string]$message) {
  $timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  if ($script:LogWriter) { $script:LogWriter.WriteLine("$timestamp $message") }
  if (-not $Quiet) { [Console]::Error.WriteLine($message) }
}

# Takes a message; appends it to $script:Notes, the notes list of
# collection.json, and logs it as "NOTE: <message>".
$script:Notes = @()
function Add-Note([string]$message) {
  $script:Notes += $message
  Write-CollectorLog "NOTE: $message"
}

# Takes a string; returns its JSON string body (no surrounding quotes) the
# way PowerShell 7's ConvertTo-Json writes it: " and \ escaped, every control
# character below 0x20 escaped (\b \t \n \f \r short, the rest \u00xx), and
# U+0085, U+2028 and U+2029 as \u escapes; everything else, non-ASCII
# included, is kept as is and encoded as UTF-8 by the writer, which turns a
# lone surrogate into U+FFFD as ConvertTo-Json's output does. Windows
# PowerShell 5.1's ConvertTo-Json also escaped < > ' & as \u003c and so on;
# the parsed rows are the same. Write-ManifestRow calls it only for a row
# that holds one of the rare characters ($script:JsonRareRx).
$script:JsonRareRx = New-Object System.Text.RegularExpressions.Regex(
  '[\x00-\x1f\u0085\u2028\u2029]')
$script:JsonInv = [System.Globalization.CultureInfo]::InvariantCulture
function ConvertTo-JsonEscaped([string]$text) {
  $builder = New-Object System.Text.StringBuilder ($text.Length + 16)
  foreach ($char in $text.ToCharArray()) {
    $code = [int]$char
    if ($char -eq '"') { [void]$builder.Append('\"') }
    elseif ($char -eq '\') { [void]$builder.Append('\\') }
    elseif ($code -eq 8) { [void]$builder.Append('\b') }
    elseif ($code -eq 9) { [void]$builder.Append('\t') }
    elseif ($code -eq 10) { [void]$builder.Append('\n') }
    elseif ($code -eq 12) { [void]$builder.Append('\f') }
    elseif ($code -eq 13) { [void]$builder.Append('\r') }
    elseif ($code -lt 0x20 -or $code -eq 0x85 -or $code -eq 0x2028 -or $code -eq 0x2029) {
      [void]$builder.Append('\u').Append($code.ToString('x4', $script:JsonInv))
    }
    else { [void]$builder.Append($char) }
  }
  return $builder.ToString()
}

# Takes a glob and whether * and ? may cross /; returns an anchored regex
# (^...$). Catalog globs are matched one path segment at a time, so their *
# stops at /; exclusion and secret globs are matched against a whole
# relative path, so theirs crosses it. [...] classes are kept, and the sh
# negated class [!...] becomes the regex [^...].
function Convert-GlobToRegex([string]$glob, [bool]$starCrossesSeparator) {
  $builder = New-Object System.Text.StringBuilder
  [void]$builder.Append('^')
  $star = '[^/]*'; $question = '[^/]'
  if ($starCrossesSeparator) { $star = '.*'; $question = '.' }
  $i = 0
  while ($i -lt $glob.Length) {
    $char = $glob[$i]
    switch ($char) {
      '*' { [void]$builder.Append($star) }
      '?' { [void]$builder.Append($question) }
      '[' {
        $close = $glob.IndexOf(']', $i + 1)
        if ($close -gt $i) {
          $class = $glob.Substring($i, $close - $i + 1)
          if ($class.StartsWith('[!')) { $class = '[^' + $class.Substring(2) }
          [void]$builder.Append($class); $i = $close
        }
        else { [void]$builder.Append('\[') }
      }
      default { [void]$builder.Append([regex]::Escape([string]$char)) }
    }
    $i++
  }
  [void]$builder.Append('$')
  $builder.ToString()
}

# Takes the globs of one table; returns one Regex that matches a relative
# path when any glob does. Each table is one alternation of its per-glob
# regexes, tested with one IsMatch per path instead of a PowerShell loop of
# -match. Every per-glob regex is ^body$, so the anchors are hoisted out
# (^(?:b1|b2|...)$) and the engine tries only the start of the path. The
# options give -match's semantics: IgnoreCase with the current culture (no
# CultureInvariant). RegexOptions.Compiled is left off: it is slower here on
# Windows PowerShell 5.1. An empty table (-Full for exclusions) matches
# nothing.
function ConvertTo-TableRegex([string[]]$globs) {
  $bodies = @(foreach ($glob in $globs) {
      $globRegex = Convert-GlobToRegex $glob $true
      $globRegex.Substring(1, $globRegex.Length - 2)
    })
  $pattern = '(?!)'
  if ($bodies.Count -gt 0) { $pattern = '^(?:' + ($bodies -join '|') + ')$' }
  $options = [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
  return (New-Object System.Text.RegularExpressions.Regex($pattern, $options))
}

# Paths longer than 260 characters (#77). Windows PowerShell 5.1 runs on
# .NET Framework, where a plain path past MAX_PATH fails unless the host has
# LongPathsEnabled set; the extended-length form (\\?\C:\... or
# \\?\UNC\server\share\...) works without it, under 5.1 and 7. Every file
# system call (.NET and -LiteralPath alike) gets the extended form on
# Windows; everything the collector writes out (manifest path, archive_path,
# target, collection.json, the log, stdout) keeps the plain form, and tar.exe
# is given plain paths. Elsewhere (PowerShell 7 on Linux or macOS) and for a
# relative path both helpers return their argument unchanged.
$script:UseExtendedPaths = ($env:OS -eq 'Windows_NT')
# A . or .. segment or a doubled separator, which the prefix stops Win32 from
# resolving, so ConvertTo-ExtendedPath resolves it first.
$script:ExtendedNormRx = New-Object System.Text.RegularExpressions.Regex(
  '\\\.{1,2}(?:\\|$)|\\\\')

# Takes a path; returns its extended-length form on Windows (\\?\C:\... for
# a drive path, \\?\UNC\server\share\... for a UNC path) with . and ..
# segments and doubled separators resolved, or the path unchanged elsewhere,
# for a relative path, or when it is already extended.
function ConvertTo-ExtendedPath([string]$path) {
  $ordinal = [System.StringComparison]::Ordinal
  if (-not $script:UseExtendedPaths -or -not $path -or $path.StartsWith('\\?\', $ordinal)) {
    return $path
  }
  $backslashed = $path.Replace('/', '\')
  if ($backslashed.Length -ge 3 -and $backslashed[1] -eq ':' -and $backslashed[2] -eq '\') {
    $prefix = '\\?\'; $body = $backslashed; $keepSegments = 1
  }
  elseif ($backslashed.Length -gt 2 -and $backslashed.StartsWith('\\', $ordinal) -and
    $backslashed[2] -ne '?' -and $backslashed[2] -ne '.') {
    $prefix = '\\?\UNC\'; $body = $backslashed.Substring(2); $keepSegments = 2
  }
  else { return $path }
  if ($script:ExtendedNormRx.IsMatch($body)) {
    # $keepSegments leading segments (the drive, or server and share) are
    # never popped.
    $segments = New-Object System.Collections.ArrayList
    foreach ($segment in $body.Split([char]'\')) {
      if ($segments.Count -lt $keepSegments) { [void]$segments.Add($segment); continue }
      if ($segment -eq '' -or $segment -eq '.') { continue }
      if ($segment -eq '..') {
        if ($segments.Count -gt $keepSegments) { $segments.RemoveAt($segments.Count - 1) }
        continue
      }
      [void]$segments.Add($segment)
    }
    $body = [string]::Join('\', [string[]]$segments.ToArray())
    if ($segments.Count -le $keepSegments) { $body += '\' }
  }
  return $prefix + $body
}

# Takes a path; returns its plain form (\\?\UNC\ becomes \\, \\?\ is
# dropped), or the path unchanged when it is not extended.
function ConvertFrom-ExtendedPath([string]$path) {
  if (-not $path) { return $path }
  if ($path.StartsWith('\\?\UNC\', [System.StringComparison]::OrdinalIgnoreCase)) {
    return '\\' + $path.Substring(8)
  }
  if ($path.StartsWith('\\?\', [System.StringComparison]::Ordinal)) { return $path.Substring(4) }
  return $path
}

# Takes an exception message; returns it with every extended path in it
# turned back into the plain form. An exception names the path it was given,
# so one about an extended path is cleaned before it reaches a row or the log.
function ConvertFrom-ExtendedText([string]$text) {
  if (-not $text -or $text.IndexOf('\\?\', [System.StringComparison]::Ordinal) -lt 0) {
    return $text
  }
  return $text.Replace('\\?\UNC\', '\\').Replace('\\?\', '')
}

# Takes a path and a kind (Leaf, Container, or anything else for either);
# returns whether it exists as that kind. Test-Path throws a real
# UnauthorizedAccessException on protected profiles even with -ErrorAction,
# so this probes through .NET, which never throws.
function Test-PathQuiet([string]$path, [string]$kind) {
  if (-not $path) { return $false }
  $path = ConvertTo-ExtendedPath $path
  try {
    if ($kind -eq 'Leaf') { return [System.IO.File]::Exists($path) }
    if ($kind -eq 'Container') { return [System.IO.Directory]::Exists($path) }
    return ([System.IO.File]::Exists($path) -or [System.IO.Directory]::Exists($path))
  } catch { return $false }
}

# Takes a parent path and a child that may use / or \; returns them joined
# with the platform separator. Join-Path is not used: its three-argument form
# is PowerShell 7 only, and it resolves PowerShell drives.
function Join-PathSafe([string]$parent, [string]$child) {
  $child = $child.Replace('\', $script:Sep).Replace('/', $script:Sep)
  if ($parent.EndsWith('\') -or $parent.EndsWith('/')) { return $parent + $child }
  return $parent + $script:Sep + $child
}

# Takes a base directory and a full path; returns the path relative to the
# base with / separators (the form exclusion and secret globs are matched
# against), or the whole path with / separators when it is not under the
# base. The prefix test ignores case.
function Get-RelPath([string]$base, [string]$full) {
  $trimmedBase = $base.TrimEnd('\', '/')
  $ignoreCase = [System.StringComparison]::OrdinalIgnoreCase
  if ($full.Length -gt $trimmedBase.Length -and $full.StartsWith($trimmedBase, $ignoreCase)) {
    return $full.Substring($trimmedBase.Length).TrimStart('\', '/').Replace('\', '/')
  }
  return $full.Replace('\', '/')
}

# Takes a DateTime; returns Unix epoch seconds, or 0 when it cannot be
# converted.
function Get-Epoch($dateTime) {
  try { return [int64]([DateTimeOffset]::new([DateTime]$dateTime).ToUnixTimeSeconds()) }
  catch { return [int64]0 }
}

# Takes a path; returns its owner as an account name, or its SID when the
# name cannot be resolved, or '' when the security descriptor cannot be read
# (always under PowerShell 7, whose File class has no GetAccessControl). Only
# the owner section is read, and each SID is translated once per run
# ($script:OwnerNames caches SID -> name).
$script:OwnerNames = @{}
function Get-OwnerName([string]$path) {
  try {
    $sections = [System.Security.AccessControl.AccessControlSections]::Owner
    $security = [System.IO.File]::GetAccessControl((ConvertTo-ExtendedPath $path), $sections)
    $sid = $security.GetOwner([System.Security.Principal.SecurityIdentifier])
    $key = $sid.Value
  } catch { return '' }
  if (-not $script:OwnerNames.ContainsKey($key)) {
    $accountName = $key
    try { $accountName = $sid.Translate([System.Security.Principal.NTAccount]).Value } catch { }
    $script:OwnerNames[$key] = $accountName
  }
  return $script:OwnerNames[$key]
}

# Takes a path; returns the lowercase hex SHA-256 of the file, or '' when it
# cannot be read. One SHA256 object serves the run instead of a Get-FileHash
# call per file. Used for the archive; Copy-FileShared hashes each staged
# copy itself.
$script:Sha256 = [System.Security.Cryptography.SHA256]::Create()
$script:ShareReadWriteDelete = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
function Get-FileSha256([string]$path) {
  $stream = $null
  try {
    $stream = New-Object System.IO.FileStream((ConvertTo-ExtendedPath $path),
      [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $script:ShareReadWriteDelete)
    $hash = $script:Sha256.ComputeHash($stream)
    return [System.BitConverter]::ToString($hash).Replace('-', '').ToLowerInvariant()
  } catch { return '' }
  finally { if ($stream) { $stream.Dispose() } }
}

# Takes a directory; returns the total size in bytes of the files under it,
# or 0 when it cannot be listed. Used for skipped_excluded and
# skipped_unmatched_volume rows.
function Get-DirSize([string]$dir) {
  try {
    $listing = @{ LiteralPath = (ConvertTo-ExtendedPath $dir); Recurse = $true; Force = $true }
    $measure = Get-ChildItem @listing -File -ErrorAction SilentlyContinue |
      Measure-Object -Property Length -Sum
    if ($measure.Sum) { return [int64]$measure.Sum } else { return [int64]0 }
  } catch { return [int64]0 }
}

# Takes a FileSystemInfo; returns its link target (several joined with ;),
# or '' when it has none or it cannot be read.
function Get-LinkTarget($item) {
  try {
    $targetProperty = $item.PSObject.Properties['Target']
    if ($targetProperty -and $targetProperty.Value) {
      return ([string[]]$targetProperty.Value) -join ';'
    }
  } catch { }
  return ''
}

# Takes a path; returns whether it is a reparse point (a symlink or
# junction), $false when it cannot be read.
function Test-IsLink([string]$path) {
  try {
    $item = Get-Item -LiteralPath (ConvertTo-ExtendedPath $path) -Force -ErrorAction Stop
    return (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
  } catch { return $false }
}

# Takes a directory; returns whether its entries can be listed.
function Test-DirReadable([string]$path) {
  try {
    [void][System.IO.Directory]::GetFileSystemEntries((ConvertTo-ExtendedPath $path))
    return $true
  } catch { return $false }
}

# ===========================================================================
# 4. Manifest writer
# ===========================================================================
# Every row of manifest.jsonl goes through Write-ManifestRow, which also
# keeps the per-status counts for collection.json and stdout. The fields and
# status values are an interface (collectors/docs/output.md).

# Rows per status, and the bytes of collected files.
$script:Counts = @{
  collected = 0; symlink = 0; skipped_excluded = 0; skipped_size = 0; skipped_secret = 0
  error_copy = 0; skipped_unmatched_volume = 0; error_read = 0; bytes = [int64]0
}
# Homes (and other bases) that gave at least one manifest row.
$script:RowHomes = @{}

# Takes the manifest fields in manifest order (uid and gid are always 0 and
# mode always '' on this side, so they are not parameters); writes one JSON
# line through $script:ManifestWriter, counts the row in $script:Counts and
# marks its home in $script:RowHomes. Rows are written by hand rather than
# through ConvertTo-Json, which is far slower per row and differs between
# 5.1 and 7: the same keys in the same order with the same JSON types, and
# PowerShell 7's ConvertTo-Json string bytes (see ConvertTo-JsonEscaped).
function Write-ManifestRow {
  param([string]$user, [string]$homeDir, [string]$agent, [string]$path, [string]$archivePath,
    [string]$type, [int64]$size, [int64]$mtime, [int64]$atime, [int64]$ctime, [int64]$btime,
    [string]$owner, [string]$attributes, [string]$sha256, [bool]$secret, [string]$status,
    [string]$target, [string]$errorText)
  $fields = [string[]]@($user, $homeDir, $agent, $path, $archivePath, $type, $owner, $attributes,
    $sha256, $status, $target, $errorText)
  if ($script:JsonRareRx.IsMatch([string]::Concat($fields))) {
    for ($i = 0; $i -lt $fields.Length; $i++) { $fields[$i] = ConvertTo-JsonEscaped $fields[$i] }
  } else {
    # No field holds a control character, so U+0000 can separate them while
    # " and \ are escaped in one pass.
    $joined = [string]::Join([string][char]0, $fields)
    $fields = $joined.Replace('\', '\\').Replace('"', '\"').Split([char]0)
  }
  $secretJson = 'false'; if ($secret) { $secretJson = 'true' }
  $culture = $script:JsonInv
  $script:ManifestWriter.WriteLine([string]::Concat([string[]]@(
        '{"user":"', $fields[0], '","home":"', $fields[1], '","agent":"', $fields[2],
        '","path":"', $fields[3], '","archive_path":"', $fields[4], '","type":"', $fields[5],
        '","size":', $size.ToString($culture), ',"mtime":', $mtime.ToString($culture),
        ',"atime":', $atime.ToString($culture), ',"ctime":', $ctime.ToString($culture),
        ',"btime":', $btime.ToString($culture), ',"uid":0,"gid":0,"mode":"","owner":"', $fields[6],
        '","attributes":"', $fields[7], '","sha256":"', $fields[8], '","secret":', $secretJson,
        ',"status":"', $fields[9], '","target":"', $fields[10], '","error":"', $fields[11], '"}')))
  if ($script:Counts.ContainsKey($status)) { $script:Counts[$status]++ }
  # The error_read row for an unreadable home itself does not make it a home
  # with artifacts.
  if (-not ($status -eq 'error_read' -and $path -eq $homeDir)) {
    $script:RowHomes[$homeDir] = $true
  }
  if ($status -eq 'collected') { $script:Counts['bytes'] += $size }
}

# Takes a directory; returns why it cannot be walked (the exception
# message), or '' when it can be listed. On Linux and macOS Get-ChildItem
# also fails on a directory that can be listed but not entered, so this
# matches the sh collector's -r and -x tests.
function Get-DirReadError([string]$dir) {
  try {
    [void]@(Get-ChildItem -LiteralPath (ConvertTo-ExtendedPath $dir) -Force -ErrorAction Stop)
    return ''
  }
  catch { return (ConvertFrom-ExtendedText $_.Exception.Message) }
}

# Takes the user, home, agent, a directory that could not be walked and the
# reason; logs "read failed" and, unless -Inventory, writes one error_read
# row (type dir, size 0) with whatever metadata of the directory itself can
# still be read.
function Write-ReadErrorRow {
  param([string]$user, [string]$homeDir, [string]$agent, [string]$dir, [string]$errorText)
  Write-CollectorLog "read failed: ${dir}: $errorText"
  if ($Inventory) { return }
  $mtime = 0; $atime = 0; $btime = 0; $attributes = ''
  try {
    $dirItem = Get-Item -LiteralPath (ConvertTo-ExtendedPath $dir) -Force -ErrorAction Stop
    $mtime = Get-Epoch $dirItem.LastWriteTimeUtc
    $atime = Get-Epoch $dirItem.LastAccessTimeUtc
    $btime = Get-Epoch $dirItem.CreationTimeUtc
    $attributes = [string]$dirItem.Attributes
  } catch { }
  $owner = ''; if (Test-PathQuiet $dir 'Container') { $owner = Get-OwnerName $dir }
  $row = @($user, $homeDir, $agent, $dir, '', 'dir', 0, $mtime, $atime, 0, $btime, $owner,
    $attributes, '', $false, 'error_read', '', $errorText)
  Write-ManifestRow @row
}

# ===========================================================================
# 5. Staging files
# ===========================================================================
# PowerShell has no worker programs: the sh collector needs them because
# find -exec cannot call shell functions, while here Add-CollectedTree calls
# Add-CollectedFile in this process for every file. Each file is read with
# Get-Item (which does not follow a reparse point) before it is copied, so
# the row holds the pre-copy times; it is copied with shared access into the
# staging tree at fs/<original path>, and the staged copy, not the source,
# is hashed, so the hash matches the archived bytes even when a running
# agent appends to the source mid-collection.

# Takes a full source path; returns its archive path: fs/ plus the path
# relative to -Root in image mode, fs/<drive letter>/... for a drive path,
# or fs/ plus the path with its leading separators removed otherwise.
function Get-ArchivePath([string]$full) {
  if ($Mode -eq 'image') { return 'fs/' + (Get-RelPath $Root $full) }
  if ($full.Length -ge 3 -and $full[1] -eq ':') {
    return 'fs/' + $full.Substring(0, 1).ToUpper() + '/' + $full.Substring(3).Replace('\', '/')
  }
  return 'fs/' + $full.TrimStart('\').Replace('\', '/')
}

# Staging directories already created or found, so each file does not test
# its parent again.
$script:StagedDirs = New-Object 'System.Collections.Generic.HashSet[string]'

# Takes the source path, the staging path and the source's pre-copy
# Get-Item from Add-CollectedFile; creates the staging directory when
# $script:StagedDirs does not have it yet, copies the file and returns the
# SHA-256 of the staged copy ('' when it cannot be read back). Throws when
# the directory or the copy fails. The source is opened with
# FileShare.ReadWrite|Delete so files held open by a running editor (SQLite
# state stores, LevelDB) can still be read.
# The hash reads the staged file back through the handle that wrote it,
# before it is closed: reopening a file just written waits for the
# antivirus scan of it on Windows, which made the hash the slowest step.
# The copy gets the source's timestamps after the hash has read it. Both
# paths are opened in the extended form, so neither side is limited to 260
# characters (#77).
function Copy-FileShared([string]$source, [string]$destination, $item) {
  $inStream = $null; $outStream = $null; $sha256 = ''
  $source = ConvertTo-ExtendedPath $source; $destination = ConvertTo-ExtendedPath $destination
  $stageDir = [System.IO.Path]::GetDirectoryName($destination)
  if (-not $script:StagedDirs.Contains($stageDir)) {
    if (-not (Test-PathQuiet $stageDir 'Any')) {
      [void][System.IO.Directory]::CreateDirectory($stageDir)
    }
    [void]$script:StagedDirs.Add($stageDir)
  }
  try {
    $inStream = New-Object System.IO.FileStream($source, [System.IO.FileMode]::Open,
      [System.IO.FileAccess]::Read, $script:ShareReadWriteDelete)
    $outStream = New-Object System.IO.FileStream($destination, [System.IO.FileMode]::Create,
      [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    $inStream.CopyTo($outStream)
    $inStream.Dispose(); $inStream = $null
    try {
      $outStream.Flush(); $outStream.Position = 0
      $hash = $script:Sha256.ComputeHash($outStream)
      $sha256 = [System.BitConverter]::ToString($hash).Replace('-', '').ToLowerInvariant()
    } catch { $sha256 = '' }
  } finally {
    if ($outStream) { $outStream.Dispose() }
    if ($inStream) { $inStream.Dispose() }
  }
  try {
    [System.IO.File]::SetCreationTimeUtc($destination, $item.CreationTimeUtc)
    [System.IO.File]::SetLastWriteTimeUtc($destination, $item.LastWriteTimeUtc)
    [System.IO.File]::SetLastAccessTimeUtc($destination, $item.LastAccessTimeUtc)
  } catch { }
  return $sha256
}

# ---------------------------------------------------------------------------
# Symlinks are recreated in the staging tree with their target string as
# stored, as the sh collector does with ln -s, so tar archives the link
# itself. PowerShell 7 (.NET 6+) has File/Directory.CreateSymbolicLink;
# Windows PowerShell 5.1 runs cmd.exe's mklink, which keeps the target
# verbatim, accepts one that does not exist, and works unprivileged in
# Developer Mode from Windows 10 1703. New-Item -ItemType SymbolicLink is not
# used: on 5.1 it resolves a relative target against the current directory
# and refuses a target that does not exist. A zip cannot store links, so the
# zip path never has them: none are made when zip is the archiver from the
# start (CAC_ARCHIVER=zip), and they are removed before a fall back to zip.
# Each staged link keeps its target string, which the PowerShell tar writer
# stores as it was given to the link API.
# ---------------------------------------------------------------------------
$script:LinkApi = $null
$script:LinkApiError = ''
$script:LinkFileMethod = $null
$script:LinkDirMethod = $null
$script:CmdExe = ''
# Each staged link as @(plain staging path, is a directory link, target).
$script:StagedLinks = New-Object System.Collections.ArrayList
# Links left out because the archive is a zip, and links that failed.
$script:LinkCounts = @{ zip = 0; failed = 0 }

# Returns the link API this PowerShell has, detected once and cached in
# $script:LinkApi: 'dotnet' (CreateSymbolicLink, PowerShell 7), 'mklink'
# (cmd.exe, Windows PowerShell 5.1), or '' with the reason in
# $script:LinkApiError. The .NET methods are looked up by reflection: they
# do not exist in .NET Framework.
function Get-LinkApi {
  if ($null -ne $script:LinkApi) { return $script:LinkApi }
  $script:LinkApi = ''
  $twoStrings = [Type[]]@([string], [string])
  $script:LinkFileMethod = [System.IO.File].GetMethod('CreateSymbolicLink', $twoStrings)
  $script:LinkDirMethod = [System.IO.Directory].GetMethod('CreateSymbolicLink', $twoStrings)
  if ($null -ne $script:LinkFileMethod -and $null -ne $script:LinkDirMethod) {
    $script:LinkApi = 'dotnet'
  }
  elseif ($env:OS -eq 'Windows_NT') {
    $cmdPath = ''
    if ($env:SystemRoot) { $cmdPath = Join-PathSafe $env:SystemRoot 'System32\cmd.exe' }
    if ($cmdPath -ne '' -and (Test-PathQuiet $cmdPath 'Leaf')) {
      $script:CmdExe = $cmdPath; $script:LinkApi = 'mklink'
    }
    else { $script:LinkApiError = 'cmd.exe not found for mklink' }
  } else { $script:LinkApiError = 'no symlink API in this PowerShell' }
  return $script:LinkApi
}

# Takes the link path, its target and whether it is a directory link; runs
# cmd.exe /d /v:off /c mklink [/D] "link" "target" with an argument string
# built here, so PowerShell's native-argument quoting is not involved.
# Returns '' on success, otherwise mklink's message and exit code.
function Invoke-Mklink([string]$linkPath, [string]$target, [bool]$isDir) {
  # cmd expands %NAME% even inside quotes, and a quote would end the argument.
  if ($linkPath.Contains('%') -or $linkPath.Contains('"') -or $target.Contains('%') -or
    $target.Contains('"')) {
    return 'link path or target contains % or ", which cmd.exe mklink cannot take verbatim'
  }
  $dirSwitch = ''; if ($isDir) { $dirSwitch = '/D ' }
  $startInfo = New-Object System.Diagnostics.ProcessStartInfo
  $startInfo.FileName = $script:CmdExe
  $quotedArgs = '"' + $linkPath + '" "' + $target + '"'
  $startInfo.Arguments = '/d /v:off /c mklink ' + $dirSwitch + $quotedArgs
  # The link path is absolute; a UNC current directory would add a cmd.exe
  # warning to stderr.
  $startInfo.WorkingDirectory = $env:SystemRoot
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  $startInfo.RedirectStandardOutput = $true
  $startInfo.RedirectStandardError = $true
  $process = [System.Diagnostics.Process]::Start($startInfo)
  # mklink's messages are short, so reading one stream to the end cannot
  # block on the other.
  $errText = $process.StandardError.ReadToEnd()
  [void]$process.StandardOutput.ReadToEnd()
  $process.WaitForExit()
  if ($process.ExitCode -eq 0) { return '' }
  $message = ($errText -replace '\s+', ' ').Trim()
  if ($message -eq '') { $message = 'mklink failed' }
  return "$message (mklink exit $($process.ExitCode))"
}

# Takes the plain staging path of a link, its target and whether it is a
# directory link; makes the link and returns '' on success, otherwise the
# reason. The link is made at the extended form of the path (mklink accepts
# it too) and recorded in $script:StagedLinks under the plain one, which the
# tar writer compares with the stage.
function Invoke-CreateSymlink([string]$linkPath, [string]$target, [bool]$isDir) {
  $api = Get-LinkApi
  $extendedLinkPath = ConvertTo-ExtendedPath $linkPath
  try {
    if ($api -eq 'dotnet') {
      $method = $script:LinkFileMethod; if ($isDir) { $method = $script:LinkDirMethod }
      # Plain strings: Invoke rejects PSObject-wrapped arguments.
      $methodArgs = New-Object 'object[]' 2
      $methodArgs[0] = [string]$extendedLinkPath; $methodArgs[1] = [string]$target
      [void]$method.Invoke($null, $methodArgs)
    } elseif ($api -eq 'mklink') {
      $why = Invoke-Mklink $extendedLinkPath $target $isDir
      if ($why -ne '') { return (ConvertFrom-ExtendedText $why) }
    } else { return $script:LinkApiError }
  } catch {
    # Invoke wraps the IOException; report the innermost message.
    $exception = $_.Exception
    while ($null -ne $exception.InnerException) { $exception = $exception.InnerException }
    return (ConvertFrom-ExtendedText $exception.Message)
  }
  [void]$script:StagedLinks.Add(@($linkPath, $isDir, $target))
  return ''
}

# Takes a reparse point's Get-Item and its plain staging path; recreates the
# link there and returns '' or the row's error. Counts zip and failed links
# in $script:LinkCounts and logs a failure.
function Add-StagedLink($item, [string]$stagePath) {
  if (-not $script:LinksInArchive) {
    $script:LinkCounts.zip++
    return 'not recreated in the archive: zip cannot store symlinks'
  }
  $targets = @()
  try {
    $targetProperty = $item.PSObject.Properties['Target']
    if ($targetProperty -and $targetProperty.Value) {
      $targets = @([string[]]$targetProperty.Value)
    }
  } catch { }
  if ($targets.Count -ne 1 -or $targets[0] -eq '') {
    $script:LinkCounts.failed++
    return 'not recreated in the archive: reparse point has no single link target'
  }
  # Only Windows distinguishes file and directory links.
  $isDir = ($env:OS -eq 'Windows_NT') -and
    (($item.Attributes -band [System.IO.FileAttributes]::Directory) -ne 0)
  $why = ''
  try {
    $parentDir = [System.IO.Path]::GetDirectoryName($stagePath)
    if (-not (Test-PathQuiet $parentDir 'Any')) {
      [void][System.IO.Directory]::CreateDirectory((ConvertTo-ExtendedPath $parentDir))
    }
    $why = Invoke-CreateSymlink $stagePath $targets[0] $isDir
  } catch { $why = ConvertFrom-ExtendedText $_.Exception.Message }
  if ($why -eq '') { return '' }
  $script:LinkCounts.failed++
  Write-CollectorLog "symlink not recreated: $(ConvertFrom-ExtendedPath $item.FullName): $why"
  return "not recreated in the archive: $why"
}

# Takes the user, home, agent and the file's Get-Item (from an extended path
# on Windows); stages it and writes its manifest row. A reparse point is
# recreated as a link (status symlink); a secret under -NoSecrets
# (skipped_secret) and a file over -MaxFileSizeMB (skipped_size) get a row
# and no copy; anything else is copied and hashed (collected, or error_copy
# with the exception message). Under -Inventory it only feeds Add-InvFile.
# Runs once per file, so Join-PathSafe and Get-Epoch are inlined and nothing
# here starts a pipeline or another process.
function Add-CollectedFile([string]$user, [string]$homeDir, [string]$agent, $item) {
  if ($Inventory) {
    # Regular files only: reparse points are neither followed nor counted.
    $isLink = (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
    if (-not $isLink -and -not $item.PSIsContainer) { Add-InvFile $agent $item }
    return
  }
  # $extendedPath opens past 260 characters and $path is what the row records.
  $extendedPath = $item.FullName
  $path = ConvertFrom-ExtendedPath $extendedPath
  $homeRel = Get-RelPath $homeDir $path
  $archiveRel = Get-ArchivePath $path
  $stageRel = $script:Sep + $archiveRel.Replace('\', $script:Sep).Replace('/', $script:Sep)
  $stagePath = $script:Stage + $stageRel; $extendedStagePath = $script:XStage + $stageRel
  $isLink = (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
  $size = [int64]0; if (-not $item.PSIsContainer) { try { $size = [int64]$item.Length } catch { } }
  try {
    $mtime = [DateTimeOffset]::new($item.LastWriteTimeUtc).ToUnixTimeSeconds()
    $atime = [DateTimeOffset]::new($item.LastAccessTimeUtc).ToUnixTimeSeconds()
    $btime = [DateTimeOffset]::new($item.CreationTimeUtc).ToUnixTimeSeconds()
  } catch {
    $mtime = Get-Epoch $item.LastWriteTimeUtc; $atime = Get-Epoch $item.LastAccessTimeUtc
    $btime = Get-Epoch $item.CreationTimeUtc
  }
  $owner = Get-OwnerName $path
  $attributes = [string]$item.Attributes
  $secret = $script:SecretRegex.IsMatch($homeRel)
  $type = 'file'; $status = 'collected'; $sha256 = ''; $target = ''; $errorText = ''
  if ($isLink) {
    $type = 'symlink'; $status = 'symlink'; $target = Get-LinkTarget $item
    $errorText = Add-StagedLink $item $stagePath
  } elseif ($secret -and $NoSecrets) {
    $status = 'skipped_secret'
  } elseif ($script:MaxSize -gt 0 -and $size -gt $script:MaxSize) {
    $status = 'skipped_size'
  } else {
    try { $sha256 = Copy-FileShared $extendedPath $extendedStagePath $item }
    catch {
      $status = 'error_copy'; $errorText = ConvertFrom-ExtendedText $_.Exception.Message
      Write-CollectorLog "copy failed: ${path}: $errorText"
      try {
        if (Test-PathQuiet $extendedStagePath 'Any') {
          Remove-Item -LiteralPath $extendedStagePath -Force
        }
      } catch { }
    }
  }
  $archivePath = ''
  if ($status -eq 'collected' -or ($status -eq 'symlink' -and $errorText -eq '')) {
    $archivePath = $archiveRel
  }
  $row = @($user, $homeDir, $agent, $path, $archivePath, $type, $size, $mtime, $atime, 0, $btime,
    $owner, $attributes, $sha256, $secret, $status, $target, $errorText)
  Write-ManifestRow @row
}

# Takes the user, home, agent and the Get-Item of a path that matched
# EXCLUDES; unless -Inventory, writes its skipped_excluded row: a directory
# with the total size of the files under it, a file with its own size.
function Add-ExcludedPath([string]$user, [string]$homeDir, [string]$agent, $item) {
  if ($Inventory) { return }
  $path = ConvertFrom-ExtendedPath $item.FullName
  if ($item.PSIsContainer) { $type = 'dir'; $size = Get-DirSize $path }
  else { $type = 'file'; $size = [int64]0; try { $size = [int64]$item.Length } catch { } }
  $mtime = Get-Epoch $item.LastWriteTimeUtc
  $atime = Get-Epoch $item.LastAccessTimeUtc
  $btime = Get-Epoch $item.CreationTimeUtc
  $row = @($user, $homeDir, $agent, $path, '', $type, $size, $mtime, $atime, 0, $btime, '',
    ([string]$item.Attributes), '', $false, 'skipped_excluded', '', '')
  Write-ManifestRow @row
}

# ===========================================================================
# 6. Catalog walk
# ===========================================================================
# A table (CATALOG for a home or a Docker volume, PROJECT_CATALOG for a
# project) is expanded against a base directory all at once, so a nested
# entry (.gemini/antigravity-cli inside .gemini) claims its subtree before
# the enclosing entry is walked; then each match is collected, a directory
# by walking it without following reparse points, testing every path
# against EXCLUDES on the way down.

# Matched paths of the table being collected, which the walk of an
# enclosing match skips. Keys are compared ordinally (the Dictionary
# default) except on Windows, so pwsh on Linux keeps .config/Cursor/User and
# .config/cursor/User apart; Expand-Glob gives on-disk spellings, so the
# case-sensitive compare still meets the names Get-ChildItem returns on
# macOS.
function Get-ClaimTable {
  if ($env:OS -eq 'Windows_NT') { return @{} }
  return (New-Object 'System.Collections.Generic.Dictionary[string,bool]')
}
$script:ClaimedPaths = Get-ClaimTable
# Paths that could not be walked since the counter was last reset; the
# Docker volume step reads it per volume.
$script:WalkErrors = 0
# Directories a wildcard segment could not list (path -> message), filled by
# Expand-Glob and read by Expand-Catalog.
$script:GlobReadErrors = [ordered]@{}

# Takes a directory and a literal catalog segment; returns the name the
# segment has on disk. On a case-insensitive filesystem (Windows, macOS)
# .config/Goose finds .config/goose; the search pattern returns the stored
# spelling, so two catalog entries that differ only by case expand to one
# path and Expand-Catalog keeps the first. When the pattern does not give
# exactly one entry (two names that differ by case on a case-sensitive
# filesystem, or an error), the segment is kept as written, so distinct
# directories stay distinct.
function Get-OnDiskName([string]$dir, [string]$segment) {
  try {
    $extendedDir = ConvertTo-ExtendedPath $dir
    $found = @([System.IO.Directory]::GetFileSystemEntries($extendedDir, $segment))
    if ($found.Count -eq 1) {
      $name = [System.IO.Path]::GetFileName($found[0])
      $ignoreCase = [System.StringComparison]::OrdinalIgnoreCase
      if ([string]::Equals($name, $segment, $ignoreCase)) { return $name }
    }
  } catch { }
  return $segment
}

# Takes a base directory and a catalog glob (segments split on /, * does
# not cross a separator); returns the full paths of the existing items it
# matches, in on-disk spelling, or nothing when it matches only the base. A
# directory that cannot be listed for a wildcard segment is recorded in
# $script:GlobReadErrors (path -> message), which Expand-Catalog turns into
# error_read rows.
function Expand-Glob([string]$base, [string]$pattern) {
  $current = @($base)
  foreach ($segment in ($pattern -split '/')) {
    if ($segment -eq '') { continue }
    $next = @()
    $isWild = ($segment -match '[\*\?\[]')
    foreach ($dir in $current) {
      if ($isWild) {
        $segmentRegex = Convert-GlobToRegex $segment $false
        $extendedDir = ConvertTo-ExtendedPath $dir
        try { $children = Get-ChildItem -LiteralPath $extendedDir -Force -ErrorAction Stop }
        catch {
          $children = @()
          if (-not $script:GlobReadErrors.Contains($dir)) {
            $script:GlobReadErrors[$dir] = (ConvertFrom-ExtendedText $_.Exception.Message)
          }
        }
        foreach ($child in $children) {
          if ($child.Name -match $segmentRegex) {
            $next += (ConvertFrom-ExtendedPath $child.FullName)
          }
        }
      } else {
        $candidate = Join-PathSafe $dir $segment
        if (Test-PathQuiet $candidate 'Any') {
          $next += (Join-PathSafe $dir (Get-OnDiskName $dir $segment))
        }
      }
    }
    $current = $next
    if ($current.Count -eq 0) { break }
  }
  if ($current.Count -gt 0 -and $current[0] -eq $base) { return @() }
  return $current
}

# Takes a base directory and a table; expands every line first and returns
# @{ Entries; GlobErrors }. Entries lists each match in table order as
# @(agent, path, glob); a path an earlier line already matched (two lines
# that differ only by case meeting one directory on a case-insensitive
# filesystem) is listed as @('', path, 'agent|glob') so the caller logs and
# skips it. Every kept match is claimed in $script:ClaimedPaths, which is
# reset first. GlobErrors maps each directory a wildcard segment could not
# list to @(first agent whose line needed it, message).
function Expand-Catalog([string]$base, [string]$table) {
  $entries = New-Object System.Collections.ArrayList
  $script:ClaimedPaths = Get-ClaimTable
  $globErrors = [ordered]@{}
  foreach ($line in (Get-TableLines $table)) {
    $parts = @($line -split '\|', 2)
    if ($parts.Count -lt 2) { continue }
    $agent = $parts[0]; $pattern = $parts[1]
    $script:GlobReadErrors = [ordered]@{}
    foreach ($matchPath in @(Expand-Glob $base $pattern)) {
      if ($script:ClaimedPaths.ContainsKey($matchPath)) {
        [void]$entries.Add(@('', $matchPath, "$agent|$pattern")); continue
      }
      [void]$entries.Add(@($agent, $matchPath, $pattern))
      $script:ClaimedPaths[$matchPath] = $true
    }
    foreach ($errorDir in @($script:GlobReadErrors.Keys)) {
      if (-not $globErrors.Contains($errorDir)) {
        $globErrors[$errorDir] = @($agent, $script:GlobReadErrors[$errorDir])
      }
    }
  }
  $script:GlobReadErrors = [ordered]@{}
  return @{ Entries = $entries; GlobErrors = $globErrors }
}

# Takes the user, base and the GlobErrors of Expand-Catalog; writes one
# error_read row for each directory, so a catalog match below it is never
# lost silently. The base itself was already checked by Get-DirReadError,
# and a directory at or under a matched path gets its row from
# Add-CollectedTree, so both are skipped. Counts $script:WalkErrors.
function Write-GlobErrorRows([string]$user, [string]$base, $globErrors) {
  $ignoreCase = [System.StringComparison]::OrdinalIgnoreCase
  foreach ($errorDir in @($globErrors.Keys)) {
    if ($errorDir.TrimEnd('\', '/') -eq $base.TrimEnd('\', '/')) { continue }
    $underMatch = $false
    foreach ($claimedPath in $script:ClaimedPaths.Keys) {
      $isUnder = $errorDir.StartsWith($claimedPath + $script:Sep, $ignoreCase)
      if ($errorDir -eq $claimedPath -or $isUnder) { $underMatch = $true; break }
    }
    if ($underMatch) { continue }
    $script:WalkErrors++
    Write-ReadErrorRow $user $base $globErrors[$errorDir][0] $errorDir $globErrors[$errorDir][1]
  }
}

# Takes the user, a base directory, a table and an optional progress header;
# collects every match of the table under the base: Expand-Catalog, the
# error_read rows for unlistable directories, then Add-CollectedPath for
# each match with a "  [agent] path" log line. The header, when given, is
# logged once before the first match, so a home with no matches leaves no
# progress line. Under -Inventory, shared entries still claim their paths
# but are not walked, and every other match is recorded as evidence.
function Add-CatalogMatches([string]$user, [string]$base, [string]$table, [string]$header = '') {
  $expansion = Expand-Catalog $base $table
  Write-GlobErrorRows $user $base $expansion.GlobErrors
  foreach ($entry in $expansion.Entries) {
    $agent = $entry[0]; $matchPath = $entry[1]
    if (-not $agent) {
      if ($header) { Write-CollectorLog $header; $header = '' }
      $duplicate = @($entry[2] -split '\|', 2)
      $lineText = "catalog line $($duplicate[1]) names the same path as an earlier line"
      Write-CollectorLog ("  [$($duplicate[0])] ${matchPath}: $lineText" +
        ' (case-insensitive filesystem), collected there')
      continue
    }
    if ($Inventory) {
      if ($agent -eq 'shared') { continue }
      Add-InvEvidence $agent $entry[2]
    }
    if ($header) { Write-CollectorLog $header; $header = '' }
    Write-CollectorLog "  [$agent] $matchPath"
    Add-CollectedPath $user $base $agent $matchPath
  }
  $script:ClaimedPaths = Get-ClaimTable
}

# Takes the user, home, agent and a matched path; collects it: an excluded
# path gets its skipped_excluded row, a directory that is not a reparse
# point is walked by Add-CollectedTree, anything else is staged by
# Add-CollectedFile. A path that cannot be read is logged ("stat failed")
# and counted in $script:WalkErrors.
function Add-CollectedPath([string]$user, [string]$homeDir, [string]$agent, [string]$path) {
  $item = $null
  try { $item = Get-Item -LiteralPath (ConvertTo-ExtendedPath $path) -Force -ErrorAction Stop }
  catch {
    $script:WalkErrors++
    Write-CollectorLog "stat failed: ${path}: $(ConvertFrom-ExtendedText $_.Exception.Message)"
    return
  }
  $homeRel = Get-RelPath $homeDir $path
  if ($script:ExcludeRegex.IsMatch($homeRel)) {
    Add-ExcludedPath $user $homeDir $agent $item; return
  }
  $isLink = (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
  if ($item.PSIsContainer -and -not $isLink) { Add-CollectedTree $user $homeDir $agent $path }
  else { Add-CollectedFile $user $homeDir $agent $item }
}

# Takes the user, home, agent and a directory; walks it depth first: a
# child another catalog entry claimed is left to that entry, an excluded
# child gets its skipped_excluded row and is not descended, a directory
# that is not a reparse point is walked, and everything else is staged. The
# directory is listed through its extended form, so a tree deeper than 260
# characters is walked on 5.1 without LongPathsEnabled (#77); a directory
# that cannot be listed gets an error_read row, never silence, and counts in
# $script:WalkErrors.
function Add-CollectedTree([string]$user, [string]$homeDir, [string]$agent, [string]$dir) {
  $children = @()
  $extendedDir = ConvertTo-ExtendedPath $dir
  try { $children = @(Get-ChildItem -LiteralPath $extendedDir -Force -ErrorAction Stop) }
  catch {
    $script:WalkErrors++
    Write-ReadErrorRow $user $homeDir $agent $dir (ConvertFrom-ExtendedText $_.Exception.Message)
    return
  }
  foreach ($child in $children) {
    $childPath = ConvertFrom-ExtendedPath $child.FullName
    if ($script:ClaimedPaths.ContainsKey($childPath)) { continue }
    $homeRel = Get-RelPath $homeDir $childPath
    if ($script:ExcludeRegex.IsMatch($homeRel)) {
      Add-ExcludedPath $user $homeDir $agent $child; continue
    }
    $isLink = (($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
    if ($child.PSIsContainer -and -not $isLink) {
      Add-CollectedTree $user $homeDir $agent $childPath
    }
    else { Add-CollectedFile $user $homeDir $agent $child }
  }
}

# ===========================================================================
# 7. Users
# ===========================================================================
# Every profile directory is a base for CATALOG. Each home is a hashtable
# @{ user; home }; $script:UserList holds them in enumeration order.

# Profile names that are never a person's home.
$script:SkipHomes = @('Public', 'Default', 'Default User', 'All Users', 'Shared', 'defaultuser0')
# Transient Windows service profiles: font driver hosts, desktop window
# manager, TEMP.
$script:SkipHomeRe = '^(UMFD-\d+|DWM-\d+|TEMP)(\..*)?$'
# Homes that were listed but could not be entered, in the plain form.
$script:InaccessibleHomes = @()
# The inaccessible homes whose parent lists them (access denied), set by
# Add-UserHomes.
$script:DeniedHomes = @()
$script:UserList = @()

# Returns every candidate home as @{ user; home }, duplicates included. A
# live run reads the registry's ProfileList and then lists Users/* and
# home/* on the system drive; image mode lists the usual Windows and Unix
# home roots under -Root.
function Get-CandidateHomes {
  $candidates = @()
  if ($Mode -eq 'live') {
    $profileList = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'
    try {
      foreach ($key in (Get-ChildItem $profileList -ErrorAction Stop)) {
        $properties = Get-ItemProperty -LiteralPath $key.PSPath -ErrorAction SilentlyContinue
        $profilePath = $properties.ProfileImagePath
        if ($profilePath) {
          $profilePath = [Environment]::ExpandEnvironmentVariables($profilePath)
          $candidates += @{ user = (Split-Path -Leaf $profilePath); home = $profilePath }
        }
      }
    } catch { }
    $drive = $env:SystemDrive; if (-not $drive) { $drive = 'C:' }
    $driveRoot = $drive + $script:Sep; if ($script:Sep -eq '/') { $driveRoot = '/' }
    $roots = @('Users/*', 'home/*'); $base = $driveRoot
  } else {
    $roots = @('Users/*', 'home/*', 'root', 'var/root', 'usr/home/*', 'export/home/*')
    $base = $Root
  }
  foreach ($glob in $roots) {
    foreach ($homeDir in (Expand-Glob $base $glob)) {
      $candidates += @{ user = (Split-Path -Leaf $homeDir); home = $homeDir }
    }
  }
  return $candidates
}

# Returns the homes to collect as @{ user; home }, in enumeration order:
# trailing separators trimmed, skip-listed and transient profiles left out,
# files left out, -Users applied, and each home kept once (compared without
# case). A home that is not a directory .NET can see is appended to
# $script:InaccessibleHomes instead.
function Get-UserHomes {
  $wanted = @(); if ($Users -ne '') { $wanted = @($Users -split ',' | Where-Object { $_ -ne '' }) }
  $seen = @{}; $selected = @()
  foreach ($candidate in (Get-CandidateHomes)) {
    $homePath = $candidate.home.TrimEnd('\', '/')
    if ($script:SkipHomes -contains $candidate.user -or $candidate.user -match $script:SkipHomeRe) {
      continue
    }
    if ([System.IO.File]::Exists((ConvertTo-ExtendedPath $homePath))) { continue }
    if ($wanted.Count -gt 0 -and -not ($wanted -contains $candidate.user)) { continue }
    if (-not (Test-PathQuiet $homePath 'Container')) {
      if (-not ($script:InaccessibleHomes -contains $homePath)) {
        $script:InaccessibleHomes += $homePath
      }
      continue
    }
    $key = $homePath.ToLowerInvariant()
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = $true
    $selected += @{ user = $candidate.user; home = $homePath }
  }
  return $selected
}

# Returns the inaccessible homes that are denied rather than gone: .NET
# reports the home missing although its parent directory lists it (access
# denied; a ProfileList entry for a deleted profile is not counted).
function Get-DeniedHomes {
  foreach ($homePath in $script:InaccessibleHomes) {
    $leaf = Split-Path -Leaf $homePath; $parent = Split-Path -Parent $homePath
    try {
      $listed = @([System.IO.Directory]::GetDirectories((ConvertTo-ExtendedPath $parent), $leaf))
      if ($listed.Count -gt 0) { $homePath }
    } catch { }
  }
}

# Main step: collects CATALOG under every home in $script:UserList. Sets
# $script:DeniedHomes; unless -Inventory, writes one error_read row for each
# denied home and for each listed home that cannot be walked. Under
# -Inventory, each user's accumulator is kept in $script:InvUsers as
# @(home, accumulator) for Write-Inventory.
function Add-UserHomes {
  $script:DeniedHomes = @(Get-DeniedHomes)
  if (-not $Inventory) {
    foreach ($deniedHome in $script:DeniedHomes) {
      $why = 'access denied'
      $extendedHome = ConvertTo-ExtendedPath $deniedHome
      try { [void](Get-Item -LiteralPath $extendedHome -Force -ErrorAction Stop) }
      catch { $why = ConvertFrom-ExtendedText $_.Exception.Message }
      Write-ReadErrorRow (Split-Path -Leaf $deniedHome) $deniedHome '' $deniedHome $why
    }
  }
  foreach ($userHome in $script:UserList) {
    $script:Inv = [ordered]@{}
    if (-not $Inventory) {
      $why = Get-DirReadError $userHome.home
      if ($why) { Write-ReadErrorRow $userHome.user $userHome.home '' $userHome.home $why }
    }
    $header = "User $($userHome.user) ($($userHome.home))"
    Add-CatalogMatches $userHome.user $userHome.home $CATALOG $header
    if ($Inventory) { $script:InvUsers += , @($userHome, $script:Inv) }
  }
}

# ===========================================================================
# 8. Docker and Podman volumes
# ===========================================================================
# Named volumes are enumerated from the filesystem as in the sh collector:
# <volumes dir>/<name>/_data. A volume whose name matches DOCKER_VOLUMES is
# collected whole as user "docker" with _data as its home, through the same
# walk as a catalog match; any other volume gets one skipped_unmatched_volume
# row with its size. This reaches Linux data roots in an image (or under
# PowerShell 7 on Linux) and Windows-container volumes under
# ProgramData\Docker. Docker Desktop keeps Linux volumes inside a WSL
# virtual disk, which is only noted. Failures are noted in collection.json
# and the summary and never stop the collection.

# What the volume step saw, for collection.json and the stdout docker line.
$script:Docker = @{ seen = $false; found = 0; collected = 0; unreadable = 0; desktop = $false }
# DOCKER_VOLUMES as @(agent, name regex, glob), in table order.
$script:DockerVolumeRules = @()
foreach ($line in (Get-TableLines $DOCKER_VOLUMES)) {
  $parts = @($line -split '\|', 2)
  if ($parts.Count -lt 2) { continue }
  $script:DockerVolumeRules += , @($parts[0], (Convert-GlobToRegex $parts[1] $false), $parts[1])
}
# The -Inventory accumulator for matched volumes, reported as user docker.
$script:InvDocker = [ordered]@{}

# Takes a volume name; returns the first DOCKER_VOLUMES rule (agent, regex,
# glob) whose glob matches it, or $null. Volume names are case-sensitive,
# as in the sh collector's case(1) match, so -cmatch.
function Get-DockerVolumeRule([string]$name) {
  foreach ($rule in $script:DockerVolumeRules) { if ($name -cmatch $rule[1]) { return , $rule } }
  return $null
}

# Takes a base directory and a relative volumes path (docker/volumes);
# returns the full volumes directory when it can be listed, otherwise ''.
# Each component is checked on the way down, so a data root the responder
# cannot enter, or a symlinked one, is noted (and counted in
# $script:Docker) rather than skipped silently. A directory that cannot be
# listed may still be searchable; the walk goes on when the next component
# is visible, as the sh collector's -x test would.
function Test-VolumeRoot([string]$base, [string]$rel) {
  $volumesDir = $base
  $segments = @($rel -split '/')
  for ($i = 0; $i -lt $segments.Count; $i++) {
    $volumesDir = Join-PathSafe $volumesDir $segments[$i]
    if (Test-IsLink $volumesDir) {
      $script:Docker.seen = $true
      Add-Note "docker: $volumesDir is a symlink and was not followed; collect its target by hand"
      return ''
    }
    if (-not (Test-PathQuiet $volumesDir 'Container')) { return '' }
    $last = ($i -eq $segments.Count - 1)
    $nextVisible = (-not $last) -and
      (Test-PathQuiet (Join-PathSafe $volumesDir $segments[$i + 1]) 'Container')
    if (-not (Test-DirReadable $volumesDir) -and -not $nextVisible) {
      $script:Docker.seen = $true; $script:Docker.unreadable++
      Add-Note "docker: $volumesDir is not readable; run as root to collect the volumes under it"
      return ''
    }
  }
  return $volumesDir
}

# Takes a base directory and a relative volumes path; collects or records
# every volume directory in it (Add-Volume), skipping files and reparse
# points, and counts each in $script:Docker.found.
function Add-VolumeDir([string]$base, [string]$rel) {
  $volumesDir = Test-VolumeRoot $base $rel
  if (-not $volumesDir) { return }
  $script:Docker.seen = $true
  $listing = @{ LiteralPath = (ConvertTo-ExtendedPath $volumesDir); Force = $true }
  $children = @(Get-ChildItem @listing -ErrorAction SilentlyContinue)
  Write-CollectorLog "Docker volumes in $volumesDir"
  foreach ($volume in $children) {
    if (-not $volume.PSIsContainer) { continue }
    if (($volume.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
    $script:Docker.found++
    Add-Volume $volume
  }
}

# Takes one volume directory's Get-ChildItem entry. An unreadable volume is
# noted, one with no _data directory is logged and skipped, an unmatched one
# gets its skipped_unmatched_volume row (none under -Inventory), and a
# matched one has its _data collected under the rule's agent (under
# -Inventory, into the $script:InvDocker accumulator). A matched volume
# whose walk met unreadable paths ($script:WalkErrors) is noted as well.
function Add-Volume($volume) {
  $name = $volume.Name
  $volumePath = ConvertFrom-ExtendedPath $volume.FullName
  $data = Join-PathSafe $volumePath '_data'
  $rule = Get-DockerVolumeRule $name
  $agent = ''; if ($rule) { $agent = $rule[0] }
  $label = $agent; if (-not $label) { $label = 'unmatched' }
  $dataIsDir = Test-PathQuiet $data 'Container'
  if (-not (Test-DirReadable $volumePath) -or ($dataIsDir -and -not (Test-DirReadable $data))) {
    $script:Docker.unreadable++
    Add-Note ("docker: volume $name ($label) at $volumePath is not readable; " +
      'run as root to collect it')
    return
  }
  if ((Test-IsLink $data) -or -not $dataIsDir) {
    Write-CollectorLog "  volume $name has no _data directory, skipped"
    return
  }
  if (-not $agent) {
    if ($Inventory) { return }
    $attributes = ''
    try {
      $dataItem = Get-Item -LiteralPath (ConvertTo-ExtendedPath $data) -Force -ErrorAction Stop
      $attributes = [string]$dataItem.Attributes
    } catch { }
    $row = @('docker', $data, '', $data, '', 'dir', (Get-DirSize $data), 0, 0, 0, 0, '',
      $attributes, '', $false, 'skipped_unmatched_volume', '', '')
    Write-ManifestRow @row
    return
  }
  Write-CollectorLog "  [$agent] $data"
  $script:WalkErrors = 0
  $script:ClaimedPaths = Get-ClaimTable
  if ($Inventory) {
    $savedInv = $script:Inv; $script:Inv = $script:InvDocker
    Add-InvEvidence $agent $rule[2]
    Add-CollectedPath 'docker' $data $agent $data
    $script:Inv = $savedInv
  } else {
    Add-CollectedPath 'docker' $data $agent $data
  }
  $script:Docker.collected++
  if ($script:WalkErrors -gt 0) {
    $script:Docker.unreadable++
    Add-Note ("docker: volume $name ($agent) could not be walked completely " +
      "($($script:WalkErrors) unreadable paths, see collector.log); run as root to collect it")
  }
}

# Takes the Docker Desktop data directories to look for; notes each that
# exists and is not a link, and sets $script:Docker.desktop. Docker Desktop
# keeps Linux volumes inside a VM disk that no file walk reaches.
function Find-DockerDesktop([string[]]$desktopDirs) {
  foreach ($desktopDir in $desktopDirs) {
    if ((Test-PathQuiet $desktopDir 'Container') -and -not (Test-IsLink $desktopDir)) {
      $script:Docker.seen = $true; $script:Docker.desktop = $true
      Add-Note ("docker: Docker Desktop data at $desktopDir; volumes inside its virtual " +
        'machine disk are not collected')
    }
  }
}

# Main step: the root Docker, root Podman and Windows-container Docker data
# roots (under -Root in image mode, the system drive or / live), then the
# rootless Docker and Podman roots of each selected user, then the Docker
# Desktop data directories.
function Add-DockerVolumes {
  if ($Mode -eq 'image') { $dockerBase = $Root }
  elseif ($script:Sep -eq '/') { $dockerBase = '/' }
  else {
    $dockerBase = $env:SystemDrive; if (-not $dockerBase) { $dockerBase = 'C:' }
    $dockerBase += $script:Sep
  }
  $programData = Join-PathSafe $dockerBase 'ProgramData'
  if ($Mode -eq 'live' -and $env:ProgramData) { $programData = $env:ProgramData }
  $varLib = Join-PathSafe $dockerBase 'var/lib'
  Add-VolumeDir $varLib 'docker/volumes'
  Add-VolumeDir $varLib 'containers/storage/volumes'
  Add-VolumeDir $programData 'Docker/volumes'
  $desktopDirs = @(Join-PathSafe $programData 'DockerDesktop')
  foreach ($userHome in $script:UserList) {
    $localShare = Join-PathSafe $userHome.home '.local/share'
    Add-VolumeDir $localShare 'docker/volumes'
    Add-VolumeDir $localShare 'containers/storage/volumes'
    $desktopDirs += (Join-PathSafe $userHome.home 'Library/Containers/com.docker.docker')
    $desktopDirs += (Join-PathSafe $userHome.home 'AppData/Local/Docker')
  }
  Find-DockerDesktop $desktopDirs
}


# ===========================================================================
# 9. Project discovery
# ===========================================================================
# Project directories are read from the agents' own plain-text state (the
# same sources as the sh collector, in the same order) with a regex per
# format, never a parser: JSON and JSONL values and keys, YAML, JSON5 and
# TOML lines, and whole files that hold one path. Each discovered directory
# is a base for PROJECT_CATALOG. Agents whose project paths live only in
# SQLite are left to the analyzer.

$script:ProjectList = @()
# The home whose sources are being read, for Test-InventorySecret.
$script:DiscoveryHome = ''

# Takes a value read from a discovery source; returns it as a local
# directory path, or $null when it is not an absolute path this host or
# image can hold. file:// URIs are unescaped (file:///c:/x is a drive path;
# file:///home/x keeps its leading slash), JSON-escaped separators are
# undone, and in image mode the path is placed under -Root (a drive path
# without its drive letter).
function ConvertTo-LocalPath([string]$value) {
  $value = $value.Trim()
  if ($value -eq '') { return $null }
  if ($value.StartsWith('file://')) {
    $value = $value.Substring(7); try { $value = [uri]::UnescapeDataString($value) } catch { }
    if ($value -match '^/[A-Za-z]:') { $value = $value.Substring(1) }
  }
  $value = $value.Replace('\\', '\').Replace('\/', '/')
  if ($value -match '^[A-Za-z]:[\\/]') {
    $rest = $value.Substring(1).Replace('/', $script:Sep).Replace('\', $script:Sep)
    $value = $value.Substring(0, 1).ToUpper() + $rest
    if ($Mode -eq 'image') { return $Root + $value.Substring(2) }
    return $value
  }
  if ($value.StartsWith('/')) {
    if ($Mode -eq 'image') { return $Root + $value.Replace('/', $script:Sep) }
    if ($script:Sep -eq '/') { return $value }
    return $null
  }
  return $null
}

# Takes a discovery source path; returns whether -Inventory must skip it.
# -Inventory never opens a credential file: a source whose path relative to
# the home being scanned ($script:DiscoveryHome) matches SECRET_GLOBS
# (.claude.json, the OpenClaw and nanobot configs, Tabby's config.toml) is
# skipped in that mode.
function Test-InventorySecret([string]$file) {
  if (-not $Inventory -or -not $script:DiscoveryHome) { return $false }
  return $script:SecretRegex.IsMatch((Get-RelPath $script:DiscoveryHome $file))
}

# Takes a discovery source path; returns its text, or $null when it is not a
# file, is a credential file under -Inventory, or cannot be read.
function Read-DiscoverySource([string]$file) {
  if (-not $file -or -not (Test-PathQuiet $file 'Leaf')) { return $null }
  if (Test-InventorySecret $file) { return $null }
  try { return [System.IO.File]::ReadAllText((ConvertTo-ExtendedPath $file)) }
  catch { return $null }
}

# Takes a regex and source files; returns capture group 1 of every match in
# every readable file, in file order. The readers below build the regex for
# one format each.
function Get-RegexCaptures([string]$regex, [string[]]$files) {
  foreach ($file in $files) {
    $text = Read-DiscoverySource $file
    if ($null -eq $text) { continue }
    foreach ($match in [regex]::Matches($text, $regex)) { $match.Groups[1].Value }
  }
}

# Takes a JSON key and source files; returns every string value of that key.
function Get-JsonValues([string]$key, [string[]]$files) {
  Get-RegexCaptures ('"' + [regex]::Escape($key) + '"\s*:\s*"((?:[^"\\]|\\.)*)"') $files
}

# Takes a regex for what follows the colon and source files; returns every
# JSON key that is an absolute or drive-letter path (projects keyed by path).
function Get-JsonKeys([string]$suffix, [string[]]$files) {
  Get-RegexCaptures ('"([A-Za-z]:(?:[^"\\]|\\.)*|/(?:[^"\\]|\\.)*)"\s*:\s*' + $suffix) $files
}

# Takes source files; returns every quoted absolute path, drive-letter path
# or file:// URI in them.
function Get-PathStrings([string[]]$files) {
  Get-RegexCaptures '"((?:file:///|/|[A-Za-z]:\\\\)(?:[^"\\]|\\.)*)"' $files
}

# Takes a YAML key and source files; returns the value of every top-level
# "key: value" line, without quotes.
function Get-YamlValues([string]$key, [string[]]$files) {
  $regex = '(?m)^' + [regex]::Escape($key) + ':[ \t]*["'']?([^"''\r\n]+)["'']?[ \t]*$'
  Get-RegexCaptures $regex $files
}

# Takes a key and source files; returns every string value of that key in
# JSON5, which allows unquoted keys and single-quoted strings (OpenClaw
# config).
function Get-Json5Values([string]$key, [string[]]$files) {
  $regex = '(?<![\w$])["'']?' + [regex]::Escape($key) +
    '["'']?\s*:\s*(?:"((?:[^"\\]|\\.)*)"|''([^'']*)'')'
  foreach ($file in $files) {
    $text = Read-DiscoverySource $file
    if ($null -eq $text) { continue }
    foreach ($match in [regex]::Matches($text, $regex)) {
      if ($match.Groups[1].Success) { $match.Groups[1].Value } else { $match.Groups[2].Value }
    }
  }
}

# Takes a TOML key and source files; returns every key = "file://..." value
# (Tabby repositories).
function Get-TomlFileUrls([string]$key, [string[]]$files) {
  $regex = '(?m)^[ \t]*' + [regex]::Escape($key) + '[ \t]*=[ \t]*["''](file://[^"''\r\n]*)["'']'
  Get-RegexCaptures $regex $files
}

# Takes source files that each hold one path (Gemini CLI's .project_root,
# nanobot's .workspace); returns the text of each readable one. Unlike the
# readers above, these are read under -Inventory too.
function Get-FileTexts([string[]]$files) {
  foreach ($file in $files) {
    try { [System.IO.File]::ReadAllText((ConvertTo-ExtendedPath $file)) } catch { }
  }
}

# Takes absolute file paths; returns the deepest directory they share, in
# the raw form for ConvertTo-LocalPath, or $null when they share less than
# two segments (Twinny records indexed files, not the workspace root).
function Get-CommonDir([string[]]$paths) {
  $common = $null
  foreach ($value in $paths) {
    $path = ([string]$value).Replace('\\', '\').Replace('\/', '/')
    if ($path.StartsWith('file://')) { continue }
    $parts = @($path -split '[\\/]')
    if ($parts.Count -lt 3) { continue }
    $parts = @($parts[0..($parts.Count - 2)])
    if ($null -eq $common) { $common = $parts; continue }
    $limit = [Math]::Min($common.Count, $parts.Count); $shared = 0
    while ($shared -lt $limit -and $common[$shared] -eq $parts[$shared]) { $shared++ }
    if ($shared -eq 0) { $common = @() } else { $common = @($common[0..($shared - 1)]) }
  }
  if ($null -eq $common -or $common.Count -lt 2) { return $null }
  return ($common -join '/')
}

# Takes a -Project directory; returns the user whose home contains it, or ''.
function Get-ProjectOwner([string]$projectDir) {
  $ignoreCase = [System.StringComparison]::OrdinalIgnoreCase
  foreach ($userHome in $script:UserList) {
    if ($projectDir.StartsWith($userHome.home + $script:Sep, $ignoreCase)) { return $userHome.user }
  }
  return ''
}

# The six source groups below each take a home and return the raw values
# they read, in source order; Find-Projects calls them in this order.

# Claude Code: the prompt history and .claude.json, also in config homes
# moved with CLAUDE_CONFIG_DIR (.claude-*), which keep .claude.json inside.
function Find-ClaudeCodeProjects([string]$homeDir) {
  Get-JsonValues 'project' @((Join-PathSafe $homeDir '.claude/history.jsonl'))
  Get-JsonKeys '\{' @((Join-PathSafe $homeDir '.claude.json'))
  Get-JsonValues 'project' @(Expand-Glob $homeDir '.claude-*/history.jsonl')
  Get-JsonKeys '\{' @(Expand-Glob $homeDir '.claude-*/.claude.json')
}

# Codex, Qwen Code, Cline CLI, Cursor CLI chats, Continue, Goose sessions,
# OpenCode and Crush.
function Find-CliSessionProjects([string]$homeDir) {
  Get-JsonValues 'cwd' @(Expand-Glob $homeDir '.codex/sessions/*/*/*/*.jsonl')
  Get-JsonValues 'cwd' @(Expand-Glob $homeDir '.qwen/projects/*/chats/*.jsonl')
  Get-JsonValues 'cwd' @(Expand-Glob $homeDir '.cline/data/sessions/*/*.json')
  Get-JsonValues 'workspace_root' @(Expand-Glob $homeDir '.cline/data/sessions/*/*.json')
  Get-JsonValues 'cwd' @(Expand-Glob $homeDir '.cursor/chats/*/*/meta.json')
  Get-JsonValues 'workspaceDirectory' @((Join-PathSafe $homeDir '.continue/sessions/sessions.json'))
  Get-JsonValues 'working_dir' @(Expand-Glob $homeDir '.local/share/goose/sessions/*.jsonl')
  Get-JsonValues 'worktree' @(Expand-Glob $homeDir '.local/share/opencode/storage/project/*.json')
  Get-JsonValues 'path' @((Join-PathSafe $homeDir '.local/share/crush/projects.json'))
}

# Gemini CLI (projects, trusted folders, per-project .project_root files)
# and Antigravity (CLI history, settings and project caches).
function Find-GeminiProjects([string]$homeDir) {
  Get-JsonKeys '"' @((Join-PathSafe $homeDir '.gemini/projects.json'))
  Get-JsonKeys '"' @((Join-PathSafe $homeDir '.gemini/trustedFolders.json'))
  Get-FileTexts @(
    Expand-Glob $homeDir '.gemini/tmp/*/.project_root'
    Expand-Glob $homeDir '.gemini/history/*/.project_root'
  )
  Get-JsonValues 'workspace' @((Join-PathSafe $homeDir '.gemini/antigravity-cli/history.jsonl'))
  Get-PathStrings @(
    Join-PathSafe $homeDir '.gemini/antigravity-cli/settings.json'
    Join-PathSafe $homeDir '.gemini/antigravity-cli/cache/projects.json'
    Expand-Glob $homeDir '.gemini/config/projects/*.json'
  )
}

# Amp, Factory, Kiro, Cursor ACP sessions, Goose recent directories,
# Copilot CLI, Hermes, Letta, pi, muse, Open Interpreter, OpenHands and
# PearAI.
function Find-AgentSessionProjects([string]$homeDir) {
  Get-JsonValues 'cwd' @(
    Join-PathSafe $homeDir '.local/share/amp/history.jsonl'
    Expand-Glob $homeDir '.factory/sessions/*/*.jsonl'
    Expand-Glob $homeDir '.factory/sessions/*.jsonl'
    Expand-Glob $homeDir '.kiro/sessions/cli/*.json'
    Expand-Glob $homeDir '.cursor/acp-sessions/*/meta.json'
  )
  Get-JsonValues 'root' @(Expand-Glob $homeDir '.kiro/workspace-roots/*/.trust-migration.json')
  Get-PathStrings @(
    Expand-Glob $homeDir '.kiro/sessions/*/sess_*/session.json'
    Join-PathSafe $homeDir '.config/Goose/recent-dirs.json'
    Join-PathSafe $homeDir 'Library/Application Support/Goose/recent-dirs.json'
    Join-PathSafe $homeDir 'AppData/Roaming/Goose/recent-dirs.json'
  )
  Get-YamlValues 'cwd' @(Expand-Glob $homeDir '.copilot/session-state/*/workspace.yaml')
  Get-JsonValues 'workdir' @(
    Expand-Glob $homeDir '.hermes/checkpoints/store/projects/*.json'
    Expand-Glob $homeDir '.hermes/profiles/*/checkpoints/store/projects/*.json'
    Expand-Glob $homeDir 'AppData/Local/hermes/checkpoints/store/projects/*.json'
    Expand-Glob $homeDir 'AppData/Local/hermes/profiles/*/checkpoints/store/projects/*.json'
  )
  Get-JsonValues 'project' @((Join-PathSafe $homeDir '.letta/sessions.jsonl'))
  Get-JsonValues 'cwd' @(
    Expand-Glob $homeDir '.letta/lc-local-backend/conversations/*/messages.jsonl'
    Expand-Glob $homeDir '.pi/agent/sessions/*/*.jsonl'
    Expand-Glob $homeDir '.pi/agent/*.jsonl'
    Join-PathSafe $homeDir '.pi/agent/crashes.json'
    Expand-Glob $homeDir '.pi/agent/experimental/sessions/*/meta.json'
  )
  Get-JsonKeys '(?:true|false)' @((Join-PathSafe $homeDir '.pi/agent/trust.json'))
  Get-JsonKeys '\{' @((Join-PathSafe $homeDir '.config/muse/trust.json'))
  $museSessions = '.local/share/muse/sessions/*/*/*/*/session.jsonl'
  Get-JsonValues 'workspace_root' @(Expand-Glob $homeDir $museSessions)
  Get-JsonValues 'cwd' @(
    Expand-Glob $homeDir '.openinterpreter/sessions/*/*/*/rollout-*.jsonl'
    Expand-Glob $homeDir '.openinterpreter/archived_sessions/rollout-*.jsonl'
    Expand-Glob $homeDir '.openinterpreter/archived_sessions/*/*/*/rollout-*.jsonl'
  )
  Get-JsonValues 'path' @((Join-PathSafe $homeDir '.openhands/workspaces.json'))
  Get-JsonValues 'working_dir' @(
    Expand-Glob $homeDir '.openhands/agent-canvas/dev_conversations/*/meta.json'
    Expand-Glob $homeDir '.openhands/agent-canvas/conversations/*/meta.json'
    Expand-Glob $homeDir '.openhands/conversations/*/base_state.json'
  )
  Get-JsonValues 'workspaceDirectory' @((Join-PathSafe $homeDir '.pearai/sessions/sessions.json'))
}

# Configuration files that name a workspace: OpenClaw (and its clawdbot
# name), nanobot, Tabby repositories and Twinny embedding manifests.
function Find-ConfigFileProjects([string]$homeDir) {
  $openClawConfigs = @(
    Expand-Glob $homeDir '.openclaw*/openclaw.json'
    Join-PathSafe $homeDir '.clawdbot/clawdbot.json'
  )
  Get-Json5Values 'workspace' $openClawConfigs
  Get-Json5Values 'agentDir' $openClawConfigs
  Get-FileTexts @(Expand-Glob $homeDir '.nanobot*/sessions/*/.workspace')
  Get-JsonValues 'workspace' @(Expand-Glob $homeDir '.nanobot*/config.json')
  Get-TomlFileUrls 'git_url' @((Join-PathSafe $homeDir '.tabby/config.toml'))
  foreach ($manifest in @(Expand-Glob $homeDir '.twinny/embeddings/*/manifest.json')) {
    $commonDir = Get-CommonDir @(Get-PathStrings @($manifest))
    if ($commonDir) { $commonDir }
  }
}

# VS Code-family editors: every User directory (Code, Cursor, Windsurf and
# the other forks, and remote-server data directories) with its workspace
# storage and the Cline, Roo Code and Kilo Code task indexes.
function Find-EditorProjects([string]$homeDir) {
  $userDirs = @(
    Expand-Glob $homeDir 'AppData/Roaming/*/User'
    Expand-Glob $homeDir '.config/*/User'
    Expand-Glob $homeDir 'Library/Application Support/*/User'
    Expand-Glob $homeDir '.*-server*/data/User'
  )
  foreach ($userDir in $userDirs) {
    Get-JsonValues 'folder' @(Expand-Glob $userDir 'workspaceStorage/*/workspace.json')
    Get-JsonValues 'cwdOnTaskInitialization' @(
      Expand-Glob $userDir 'globalStorage/saoudrizwan.claude-dev/state/taskHistory.json'
      Expand-Glob $userDir 'globalStorage/saoudrizwan.claude-dev/tasks/*/task_metadata.json'
    )
    Get-JsonValues 'workspace' @(
      Expand-Glob $userDir 'globalStorage/rooveterinaryinc.roo-cline/tasks/_index.json'
      Expand-Glob $userDir 'globalStorage/kilocode.kilo-code/tasks/_index.json'
    )
  }
}

# Takes the discovered @{ user; path } entries in discovery order; returns
# each existing directory once (compared without case), dropping the homes
# themselves. A path seen first without a user (a -Project outside every
# home) takes the user of a later entry for it.
function Select-UniqueProjects($found) {
  $seen = @{}; $unique = @()
  $homeKeys = @{}
  foreach ($userHome in $script:UserList) { $homeKeys[$userHome.home.ToLowerInvariant()] = $true }
  foreach ($entry in $found) {
    $key = $entry.path.ToLowerInvariant()
    if ($seen.ContainsKey($key)) {
      if ($seen[$key].user -eq '' -and $entry.user -ne '') { $seen[$key].user = $entry.user }
      continue
    }
    if ($homeKeys.ContainsKey($key)) { continue }
    if (-not (Test-PathQuiet $entry.path 'Container')) { continue }
    $seen[$key] = $entry; $unique += $entry
  }
  return $unique
}

# Returns every project directory to collect as @{ user; path }: the values
# of the six source groups for each home, then each -Project, through
# Select-UniqueProjects.
function Find-Projects {
  $found = @()
  foreach ($userHome in $script:UserList) {
    $homeDir = $userHome.home
    $script:DiscoveryHome = $homeDir
    $values = @(
      Find-ClaudeCodeProjects $homeDir
      Find-CliSessionProjects $homeDir
      Find-GeminiProjects $homeDir
      Find-AgentSessionProjects $homeDir
      Find-ConfigFileProjects $homeDir
      Find-EditorProjects $homeDir
    )
    $script:DiscoveryHome = ''
    foreach ($value in $values) {
      $localPath = ConvertTo-LocalPath ([string]$value)
      if ($localPath) { $found += @{ user = $userHome.user; path = $localPath.TrimEnd('\', '/') } }
    }
  }
  foreach ($projectArg in $Project) {
    $found += @{ user = (Get-ProjectOwner $projectArg); path = $projectArg.TrimEnd('\', '/') }
  }
  return (Select-UniqueProjects $found)
}

# Main step: collects PROJECT_CATALOG under every directory in
# $script:ProjectList. A -Project value that is not a directory was left out
# of the list; it gets a log line and, unless -Inventory, one error_read
# row, so it is never dropped silently. Under -Inventory nothing is walked.
function Add-Projects {
  foreach ($projectArg in $Project) {
    if (Test-PathQuiet $projectArg 'Container') { continue }
    if (Test-PathQuiet $projectArg 'Leaf') { $why = 'Not a directory' }
    else {
      $why = "Cannot find path '$projectArg' because it does not exist."
      $extendedArg = ConvertTo-ExtendedPath $projectArg
      try { [void](Get-Item -LiteralPath $extendedArg -Force -ErrorAction Stop) }
      catch { $why = ConvertFrom-ExtendedText $_.Exception.Message }
    }
    $warning = 'WARNING: project given with -Project is not a directory'
    Write-CollectorLog "${warning}: ${projectArg}: $why"
    if (-not $Inventory) {
      $owner = Get-ProjectOwner $projectArg
      $row = @($owner, $projectArg, '', $projectArg, '', 'dir', 0, 0, 0, 0, 0, '', '', '', $false,
        'error_read', '', $why)
      Write-ManifestRow @row
    }
  }
  if ($Inventory) { return }
  foreach ($projectDir in $script:ProjectList) {
    $userLabel = ''; if ($projectDir.user) { $userLabel = '[' + $projectDir.user + '] ' }
    Write-CollectorLog "Project $userLabel$($projectDir.path)"
    $why = Get-DirReadError $projectDir.path
    if ($why) { Write-ReadErrorRow $projectDir.user $projectDir.path '' $projectDir.path $why }
    Add-CatalogMatches $projectDir.user $projectDir.path $PROJECT_CATALOG
  }
}

# ===========================================================================
# 10. Inventory output
# ===========================================================================
# -Inventory runs the same walk with no writes: Add-CollectedFile feeds
# these accumulators instead of copying, and Write-Inventory prints JSON
# lines on stdout (the host line, one line per user and agent, then the
# Docker volume agents as user docker). Nothing is written to disk.

# The accumulator being filled: agent -> files, bytes, first and last mtime
# (epoch seconds, 0 when unknown) and the matched catalog globs in order of
# first match. Add-UserHomes starts one per user and keeps it in
# $script:InvUsers as @(home, accumulator); matched Docker volumes fill
# $script:InvDocker (declared with the Docker state).
$script:Inv = [ordered]@{}
$script:InvUsers = @()

# Takes an agent; returns its entry in $script:Inv, creating it empty.
function Get-InvEntry([string]$agent) {
  if (-not $script:Inv.Contains($agent)) {
    $script:Inv[$agent] = @{
      files = 0; bytes = [int64]0; first = [int64]0; last = [int64]0
      evidence = (New-Object System.Collections.ArrayList)
    }
  }
  return $script:Inv[$agent]
}

# Takes an agent and the catalog glob that matched; adds the glob to the
# agent's evidence once.
function Add-InvEvidence([string]$agent, [string]$glob) {
  $entry = Get-InvEntry $agent
  if (-not $entry.evidence.Contains($glob)) { [void]$entry.evidence.Add($glob) }
}

# Takes an agent and a regular file's Get-Item; counts the file, its bytes
# and its modification time in the agent's entry.
function Add-InvFile([string]$agent, $item) {
  $entry = Get-InvEntry $agent
  $entry.files++
  try { $entry.bytes += [int64]$item.Length } catch { }
  $mtime = Get-Epoch $item.LastWriteTimeUtc
  if ($mtime -gt 0) {
    if ($entry.first -eq 0 -or $mtime -lt $entry.first) { $entry.first = $mtime }
    if ($mtime -gt $entry.last) { $entry.last = $mtime }
  }
}

# Takes epoch seconds; returns UTC ISO 8601 without fractions, or '' for 0.
function Format-InvTime([int64]$epoch) {
  if ($epoch -le 0) { return '' }
  $culture = [Globalization.CultureInfo]::InvariantCulture
  $utc = [DateTimeOffset]::FromUnixTimeSeconds($epoch).UtcDateTime
  return $utc.ToString('yyyy-MM-ddTHH:mm:ssZ', $culture)
}

# Takes a user, one accumulator and the user's project count; returns the
# agent lines of the accumulator as compressed JSON in the documented key
# order. A match with no files of its own after exclusions and nested
# claims gives no line.
function Write-InventoryLines([string]$user, $accumulator, [int]$projects) {
  foreach ($agent in @($accumulator.Keys)) {
    $entry = $accumulator[$agent]
    if ($entry.files -eq 0) { continue }
    $line = [ordered]@{
      type = 'agent'; host = $script:HostName; user = $user; agent = $agent
      files = [int64]$entry.files; bytes = [int64]$entry.bytes
      first = (Format-InvTime $entry.first); last = (Format-InvTime $entry.last)
      projects = $projects; evidence = (@($entry.evidence) -join ',')
    }
    $line | ConvertTo-Json -Compress
  }
}

# Main step under -Inventory: logs each home that cannot be listed, then
# returns the host line, the agent lines of each user (with that user's
# discovered project count) and the Docker volume agents. A home is
# unreadable when it was denied (see Get-DeniedHomes) or its entries cannot
# be listed.
function Write-Inventory {
  $denied = $script:DeniedHomes
  $unreadable = $denied.Count
  foreach ($userHome in $script:UserList) {
    if (-not (Test-DirReadable $userHome.home)) {
      $unreadable++
      Write-CollectorLog "WARNING: home of $($userHome.user) is not readable: $($userHome.home)"
    }
  }
  $hostLine = [ordered]@{
    type = 'host'; host = $script:HostName; collector = $ToolVersion; mode = $Mode
    at = $script:StartTs; users_scanned = ($script:UserList.Count + $denied.Count)
    users_unreadable = $unreadable; docker_volumes = $script:Docker.found
  }
  Write-Output ($hostLine | ConvertTo-Json -Compress)
  foreach ($pair in $script:InvUsers) {
    $userHome = $pair[0]
    $projectCount = @($script:ProjectList | Where-Object { $_.user -eq $userHome.user }).Count
    Write-InventoryLines $userHome.user $pair[1] $projectCount
  }
  Write-InventoryLines 'docker' $script:InvDocker 0
}
if ($Version) { Write-Output "$TOOL $ToolVersion"; exit 0 }

if ($List) {
  Write-Output '# home artifacts (agent|glob relative to home)'
  $CATALOG -split "`r?`n" | Where-Object { $_ -ne '' } | ForEach-Object { Write-Output $_ }
  Write-Output '# project artifacts (relative to each discovered project)'
  $PROJECT_CATALOG -split "`r?`n" | Where-Object { $_ -ne '' } | ForEach-Object { Write-Output $_ }
  Write-Output '# excluded unless --full'
  $EXCLUDES -split "`r?`n" | Where-Object { $_ -ne '' } | ForEach-Object { Write-Output $_ }
  Write-Output ''
  Write-Output '# credential files (flagged secret, skipped with --no-secrets)'
  $SECRET_GLOBS -split "`r?`n" | Where-Object { $_ -ne '' } | ForEach-Object { Write-Output $_ }
  Write-Output '# docker volumes (agent|volume name glob)'
  $DOCKER_VOLUMES -split "`r?`n" | Where-Object { $_ -ne '' } | ForEach-Object { Write-Output $_ }
  exit 0
}

if ($MaxFileSizeMB -lt 0) { Write-Error 'Invalid -MaxFileSizeMB'; exit 1 }
$MaxSize = [int64]$MaxFileSizeMB * 1024 * 1024

$excludeGlobs = @(Get-TableLines $EXCLUDES); if ($Full) { $excludeGlobs = @() }
$script:ExcludeRegex = ConvertTo-TableRegex $excludeGlobs
$script:SecretRegex = ConvertTo-TableRegex @($SECRET_GLOBS -split "`r?`n" | Where-Object { $_ -ne '' })

# Deletes the staged links themselves, never what they point to, so the
# cleanup does not depend on how each PowerShell version's Remove-Item
# -Recurse treats a directory link.
# Called after the log writer is closed, so it appends to the log directly.
# Returns how many links could not be removed.
function Clear-StagedLinks {
  $left = 0
  foreach ($l in @($script:StagedLinks)) {
    $xl = ConvertTo-ExtendedPath $l[0]
    try { if ($l[1]) { [System.IO.Directory]::Delete($xl) } else { [System.IO.File]::Delete($xl) } }
    catch { $left++; [System.IO.File]::AppendAllText($XLogPath, "could not remove staged link $($l[0]): $(ConvertFrom-ExtendedText $_.Exception.Message)`n", $script:Utf8NoBom) }
  }
  $script:StagedLinks.Clear()
  return $left
}

# After a late fall back to zip the staged links are gone, so their rows lose
# archive_path and say why; the manifest is rewritten before it is archived.
function Clear-LinkArchivePaths([string]$reason) {
  $lines = [System.IO.File]::ReadAllLines($XManifestPath, $script:Utf8NoBom)
  $w = New-Object System.IO.StreamWriter($XManifestPath, $false, $script:Utf8NoBom)
  try {
    foreach ($ln in $lines) {
      if ($ln.Contains('"status":"symlink"')) {
        $o = $ln | ConvertFrom-Json
        if ($o.status -eq 'symlink' -and $o.archive_path) { $o.archive_path = ''; $o.error = $reason; $ln = $o | ConvertTo-Json -Compress -Depth 2 }
      }
      $w.WriteLine($ln)
    }
  } finally { $w.Close() }
}

# ---------------------------------------------------------------------------
# Archivers. tar.exe (the system tar under PowerShell 7 off Windows) is tried
# first; Windows tar.exe exits 0xC0000005 on any name outside the ANSI code
# page (#72), so the PowerShell tar writer below follows it, and a zip is the
# last resort. CAC_ARCHIVER, a test hook, sets the chain: a comma-separated
# list of tar, writer and zip, default tar,writer,zip.
# ---------------------------------------------------------------------------
$ArchiverLabels = @{ tar = 'tar.exe'; writer = 'PowerShell tar writer'; zip = 'ZipFile' }

# Lists the staging tree without following links, as Add-CollectedTree walks the
# source: a reparse point (a staged link) is an entry of its own and never
# descended. Each entry is @(name, FileSystemInfo, kind) with kind d, f or l;
# names are relative to the stage with / separators, and a directory's name
# ends in /. A directory comes before its contents. The tree is listed through
# the extended form of $root, so every FileSystemInfo.FullName is extended
# and opens past 260 characters (#77).
function Get-StageEntries([string]$root) {
  $out = New-Object System.Collections.ArrayList
  $stack = New-Object System.Collections.Stack
  $stack.Push(@('', (New-Object System.IO.DirectoryInfo((ConvertTo-ExtendedPath $root)))))
  $rp = [System.IO.FileAttributes]::ReparsePoint; $dirAttr = [System.IO.FileAttributes]::Directory
  while ($stack.Count -gt 0) {
    $top = $stack.Pop(); $prefix = $top[0]
    foreach ($c in $top[1].GetFileSystemInfos()) {
      $a = $c.Attributes
      if (($a -band $rp) -ne 0) { [void]$out.Add(@(($prefix + $c.Name), $c, 'l')) }
      elseif (($a -band $dirAttr) -ne 0) { $n = $prefix + $c.Name + '/'; [void]$out.Add(@($n, $c, 'd')); $stack.Push(@($n, $c)) }
      else { [void]$out.Add(@(($prefix + $c.Name), $c, 'f')) }
    }
  }
  return , $out
}

# Seconds since the epoch of an item's own last write time; 0 before 1970.
function Get-UnixTime($info) {
  $t = 0
  try { $t = [int64][Math]::Floor(($info.LastWriteTimeUtc.Ticks - 621355968000000000) / 10000000) } catch { }
  if ($t -lt 0) { $t = 0 }
  return $t
}

$script:TarAscii = [System.Text.Encoding]::ASCII
$script:TarUtf8 = New-Object System.Text.UTF8Encoding $false
$script:TarZero = New-Object byte[] 1024
$script:TarNonAscii = New-Object System.Text.RegularExpressions.Regex('[^\x00-\x7f]')
# A ustar header: mode, uid and gid 0, empty uname and gname. $name and
# $prefix are ASCII and fit their fields; the caller decides that. The
# fixed fields come from a template, and the checksum (the byte sum with its
# own field read as eight spaces) is the template's sum plus the bytes of
# the fields written here, which is faster under 5.1 than summing all 512.
$script:TarTemplate = New-Object byte[] 512
[void]$script:TarAscii.GetBytes('0000000', 0, 7, $script:TarTemplate, 108)
[void]$script:TarAscii.GetBytes('0000000', 0, 7, $script:TarTemplate, 116)
[void]$script:TarAscii.GetBytes('ustar', 0, 5, $script:TarTemplate, 257)
$script:TarTemplate[263] = 48; $script:TarTemplate[264] = 48
for ($ti = 148; $ti -lt 156; $ti++) { $script:TarTemplate[$ti] = 32 }
$script:TarTemplateSum = 0
foreach ($tb in $script:TarTemplate) { $script:TarTemplateSum += $tb }
function Get-TarHeader([string]$name, [string]$prefix, [char]$type, [string]$mode, [int64]$size, [int64]$mtime, [string]$link) {
  $h = [byte[]]$script:TarTemplate.Clone()
  $enc = $script:TarAscii
  $sz = [Convert]::ToString($size, 8).PadLeft(11, '0')
  $mt = [Convert]::ToString($mtime, 8).PadLeft(11, '0')
  [void]$enc.GetBytes($name, 0, $name.Length, $h, 0)
  [void]$enc.GetBytes($mode, 0, 7, $h, 100)
  [void]$enc.GetBytes($sz, 0, 11, $h, 124)
  [void]$enc.GetBytes($mt, 0, 11, $h, 136)
  $h[156] = [byte]$type
  if ($link) { [void]$enc.GetBytes($link, 0, $link.Length, $h, 157) }
  if ($prefix) { [void]$enc.GetBytes($prefix, 0, $prefix.Length, $h, 345) }
  $sum = $script:TarTemplateSum + [int]$h[156] + [System.Linq.Enumerable]::Sum([int[]]$enc.GetBytes($name + $mode + $sz + $mt + $link + $prefix))
  $s = [Convert]::ToString($sum, 8).PadLeft(6, '0'); [void]$enc.GetBytes($s, 0, 6, $h, 148)
  $h[154] = 0
  return , $h
}

# One pax record, "<len> key=value\n", where len counts the whole record.
function Get-PaxRecord([string]$key, [string]$value) {
  $body = ' ' + $key + '=' + $value + "`n"
  $n = $script:TarUtf8.GetByteCount($body)
  $len = $n + ([string]$n).Length
  if (([string]$len).Length -ne ([string]$n).Length) { $len = $n + ([string]$len).Length }
  return ([string]$len) + $body
}

# An ASCII stand-in for a name that goes in a pax record, for readers that
# ignore pax headers: other characters become _, and only the end is kept.
function Get-TarAsciiName([string]$name, [int]$max) {
  $a = $script:TarNonAscii.Replace($name, '_')
  if ($a.Length -gt $max) { $a = $a.Substring($a.Length - $max) }
  return $a
}

# Writes one member's header, preceded by a pax extended header (typeflag x)
# when the path or the link target is not ASCII or does not fit the ustar
# fields, or the size does not fit eleven octal digits.
function Write-TarMember($out, [string]$path, [char]$type, [string]$mode, [int64]$size, [int64]$mtime, [string]$link) {
  $name = $path; $prefix = ''; $pax = ''
  if ($script:TarNonAscii.IsMatch($path)) { $pax += Get-PaxRecord 'path' $path; $name = Get-TarAsciiName $path 100 }
  elseif ($path.Length -gt 100) {
    # ustar splits a long name at a / into a prefix of up to 155 bytes and a
    # name of up to 100: the last / at or before byte 155 that leaves a
    # non-empty name.
    $cut = -1
    if ($path.Length -le 256) { $cut = $path.LastIndexOf([char]'/', [Math]::Min(155, $path.Length - 2)) }
    if ($cut -gt 0 -and $cut -ge ($path.Length - 101)) { $prefix = $path.Substring(0, $cut); $name = $path.Substring($cut + 1) }
    else { $pax += Get-PaxRecord 'path' $path; $name = Get-TarAsciiName $path 100 }
  }
  if ($link -and ($link.Length -gt 100 -or $script:TarNonAscii.IsMatch($link))) { $pax += Get-PaxRecord 'linkpath' $link; $link = Get-TarAsciiName $link 100 }
  if ($size -gt 8589934591) { $pax += Get-PaxRecord 'size' ([string]$size); $hsize = 0 } else { $hsize = $size }
  if ($pax) {
    $pb = $script:TarUtf8.GetBytes($pax)
    $ph = Get-TarHeader ('./PaxHeaders/' + (Get-TarAsciiName ($path.TrimEnd('/') -replace '^.*/', '') 87)) '' 'x' '0000644' $pb.Length $mtime ''
    $out.Write($ph, 0, 512); $out.Write($pb, 0, $pb.Length)
    $pad = (512 - $pb.Length % 512) % 512; if ($pad) { $out.Write($script:TarZero, 0, $pad) }
  }
  $h = Get-TarHeader $name $prefix $type $mode $hsize $mtime $link
  $out.Write($h, 0, 512)
}

# Writes $archive as a gzip-compressed POSIX tar of $stage with the member
# names tar -czf $archive -C $stage . gives (./, ./fs/, ./manifest.jsonl):
# directories (mode 0755), regular files (0644) and symlinks (0777, with the
# target string the link was staged with), uid and gid 0. Staged files are
# read with shared access in chunks and links are never followed. Throws on
# failure; the caller removes the partial archive.
function Write-TarGz([string]$stage, [string]$archive) {
  $entries = Get-StageEntries $stage
  $cmp = [StringComparer]::Ordinal; if ($IsWindowsHost) { $cmp = [StringComparer]::OrdinalIgnoreCase }
  $targets = New-Object 'System.Collections.Generic.Dictionary[string,string]' ($cmp)
  foreach ($l in @($script:StagedLinks)) {
    if ($l[0].Length -gt $stage.Length + 1) { $targets[$l[0].Substring($stage.Length + 1).Replace($script:Sep, '/')] = $l[2] }
  }
  $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
  $buf = New-Object byte[] 1048576
  $fs = $null; $out = $null
  try {
    $fs = New-Object System.IO.FileStream((ConvertTo-ExtendedPath $archive), [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None, 65536)
    $gz = New-Object System.IO.Compression.GZipStream($fs, [System.IO.Compression.CompressionLevel]::Optimal)
    # Headers are 512-byte writes; the buffer hands the compressor larger blocks.
    $out = New-Object System.IO.BufferedStream($gz, 1048576)
    Write-TarMember $out './' '5' '0000755' 0 (Get-UnixTime (New-Object System.IO.DirectoryInfo((ConvertTo-ExtendedPath $stage)))) ''
    $fileMode = [System.IO.FileMode]::Open; $readAccess = [System.IO.FileAccess]::Read
    $nonAscii = $script:TarNonAscii
    foreach ($e in $entries) {
      $info = $e[1]; $kind = $e[2]; $path = './' + $e[0]
      $link = ''; $size = 0; $src = $null
      if ($kind -eq 'd') { $type = '5'; $mode = '0000755' }
      elseif ($kind -eq 'l') {
        $type = '2'; $mode = '0000777'
        if ($targets.ContainsKey($e[0])) { $link = $targets[$e[0]] }
        if (-not $link) {
          # Not a link this run staged; read its own target, never through it.
          $p = $info.PSObject.Properties['LinkTarget']
          if ($p -and $p.Value) { $link = [string]$p.Value }
          else { try { $v = @((Get-Item -LiteralPath $info.FullName -Force -ErrorAction Stop).Target); if ($v.Count -eq 1) { $link = [string]$v[0] } } catch { } }
        }
        if (-not $link) { throw "staged link has no target: $(ConvertFrom-ExtendedPath $info.FullName)" }
      } else {
        $type = '0'; $mode = '0000644'
        $src = [System.IO.File]::Open($info.FullName, $fileMode, $readAccess, $share)
      }
      try {
        if ($src) { $size = $src.Length }
        # Inline rather than Get-UnixTime: a function call per member is
        # measurable under 5.1.
        $mt = [int64][Math]::Floor(($info.LastWriteTimeUtc.Ticks - 621355968000000000) / 10000000)
        if ($mt -lt 0) { $mt = 0 }
        # Most members are short ASCII names; Write-TarMember handles the rest.
        if ($path.Length -le 100 -and $link.Length -le 100 -and -not $nonAscii.IsMatch($path) -and -not ($link -and $nonAscii.IsMatch($link)) -and $size -le 8589934591) {
          $h = Get-TarHeader $path '' $type $mode $size $mt $link
          $out.Write($h, 0, 512)
        } else { Write-TarMember $out $path $type $mode $size $mt $link }
        if ($src) {
          $left = $size
          while ($left -gt 0) {
            $want = $buf.Length; if ($left -lt $want) { $want = [int]$left }
            $n = $src.Read($buf, 0, $want)
            if ($n -le 0) { throw "staged file shrank while archiving: $(ConvertFrom-ExtendedPath $info.FullName)" }
            $out.Write($buf, 0, $n); $left -= $n
          }
          $pad = (512 - $size % 512) % 512; if ($pad) { $out.Write($script:TarZero, 0, $pad) }
        }
      } finally { if ($src) { $src.Dispose() } }
    }
    $out.Write($script:TarZero, 0, 1024)
  } finally {
    if ($null -ne $out) { $out.Dispose() } elseif ($null -ne $fs) { $fs.Dispose() }
  }
}

# Writes $archive as a zip of $stage, entry by entry with / separators (the
# .NET Framework ZipFile.CreateFromDirectory writes \), names without a ./
# prefix, and an entry for each empty directory. Called only after the staged
# links are removed; a reparse point found anyway is logged and left out.
function Write-StageZip([string]$stage, [string]$archive) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $entries = Get-StageEntries $stage
  $hasChild = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
  foreach ($e in $entries) { $t = $e[0].TrimEnd('/'); $i = $t.LastIndexOf('/'); if ($i -ge 0) { [void]$hasChild.Add($t.Substring(0, $i + 1)) } }
  $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
  $level = [System.IO.Compression.CompressionLevel]::Optimal
  $zip = $null
  try {
    $zip = [System.IO.Compression.ZipFile]::Open((ConvertTo-ExtendedPath $archive), 'Create')
    foreach ($e in $entries) {
      $info = $e[1]; $kind = $e[2]
      if ($kind -eq 'l') { [System.IO.File]::AppendAllText($XLogPath, "zip: staged link left out: $(ConvertFrom-ExtendedPath $info.FullName)`n", $script:Utf8NoBom); continue }
      if ($kind -eq 'd' -and $hasChild.Contains($e[0])) { continue }
      $ze = $zip.CreateEntry($e[0], $level)
      # A zip time holds 1980 to 2107 only; outside that the entry keeps the default.
      try { $ze.LastWriteTime = [DateTimeOffset]$info.LastWriteTime } catch { }
      if ($kind -eq 'd') { continue }
      $src = [System.IO.File]::Open($info.FullName, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share)
      try { $dst = $ze.Open(); try { $src.CopyTo($dst, 1048576) } finally { $dst.Dispose() } } finally { $src.Dispose() }
    }
  } finally { if ($null -ne $zip) { $zip.Dispose() } }
}

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
# A relative -Project is resolved against the current location, in image mode
# too: -Project is a path on the machine running the collector and is never
# prefixed with the root, as in the sh collector. Repeated values are kept once.
$resolvedProjects = @()
foreach ($p in @($Project)) {
  if (-not $p) { continue }
  $rp = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)
  if ($rp.Length -gt 1) { $rp = $rp.TrimEnd('\', '/') }
  if ($rp.EndsWith(':')) { $rp += '\' }
  if (-not ($resolvedProjects -contains $rp)) { $resolvedProjects += $rp }
}
$Project = $resolvedProjects

$Mode = 'live'
if ($Root -ne '') {
  if (-not (Test-PathQuiet $Root 'Container')) { Write-Error "Root is not a directory: $Root"; exit 2 }
  $Root = (ConvertFrom-ExtendedPath (Resolve-Path -LiteralPath (ConvertTo-ExtendedPath $Root)).ProviderPath).TrimEnd('\', '/')
  $Mode = 'image'
}
# -Inventory writes nothing: no output directory, staging, log or archive.
if (-not $Inventory) {
if (-not (Test-PathQuiet $OutputDir 'Any')) { try { New-Item -ItemType Directory -Path (ConvertTo-ExtendedPath $OutputDir) -Force -ErrorAction Stop | Out-Null } catch { Write-Error "Cannot create output dir: $OutputDir"; exit 2 } }
$OutputDir = (ConvertFrom-ExtendedPath (Resolve-Path -LiteralPath (ConvertTo-ExtendedPath $OutputDir)).ProviderPath).TrimEnd('\', '/')
if ($OutputDir -eq '') { $OutputDir = $script:Sep }
# Same startup check as the sh collector's [ -w ]: create and remove a probe
# file, so a read-only directory fails here rather than after the walk.
$probe = Join-PathSafe $OutputDir ".write-probe-$([guid]::NewGuid().ToString('N'))"
try { $fs = [System.IO.File]::Open((ConvertTo-ExtendedPath $probe), [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write); $fs.Close() }
catch { Write-Error "Output dir not writable: $OutputDir"; exit 2 }
try { [System.IO.File]::Delete((ConvertTo-ExtendedPath $probe)) } catch { }
}

$StartTs = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$HostName = $env:COMPUTERNAME; if (-not $HostName) { $HostName = [System.Net.Dns]::GetHostName() }
$HostSafe = ($HostName -replace '[^A-Za-z0-9._-]', '-')
$Name = "${HostSafe}_${Stamp}_agent-artifacts"
$Stage = Join-PathSafe $OutputDir ".stage-$Name"
$LogPath = Join-PathSafe $OutputDir "$Name.log"
$ManifestPath = Join-PathSafe $OutputDir "$Name.manifest.jsonl"
$SummaryPath = Join-PathSafe $OutputDir "$Name.collection.json"
# The extended forms, for .NET calls; the plain ones are what is printed.
$XStage = ConvertTo-ExtendedPath $Stage
$XLogPath = ConvertTo-ExtendedPath $LogPath
$XManifestPath = ConvertTo-ExtendedPath $ManifestPath
$XSummaryPath = ConvertTo-ExtendedPath $SummaryPath

$TarExe = $null
$tarCmd = $null
$IsWindowsHost = ($env:OS -eq 'Windows_NT')
if ($Inventory) { }
elseif ($IsWindowsHost) { $tarCmd = Get-Command tar.exe -ErrorAction SilentlyContinue } else { $tarCmd = Get-Command tar -ErrorAction SilentlyContinue }
if ($tarCmd) { $TarExe = $tarCmd.Source }
# The archivers to try in order; see "Archivers" above. A tar that is not on
# the PATH is left out. Links are staged unless the zip comes first.
$Archivers = @()
$ArchiverWhy = ''
if (-not $Inventory) {
  $spec = 'tar,writer,zip'
  if ($env:CAC_ARCHIVER) { $spec = $env:CAC_ARCHIVER; $ArchiverWhy = "CAC_ARCHIVER=$spec" }
  foreach ($a in @($spec -split ',')) {
    $a = $a.Trim()
    if (-not $ArchiverLabels.ContainsKey($a)) { Write-Error "CAC_ARCHIVER: unknown archiver '$a' (use tar, writer or zip, comma-separated)"; exit 2 }
    if ($a -eq 'tar' -and -not $TarExe) { if (-not $ArchiverWhy) { $ArchiverWhy = 'tar.exe not found' }; continue }
    if (-not ($Archivers -contains $a)) { $Archivers += $a }
  }
  if ($Archivers.Count -eq 0) { Write-Error "CAC_ARCHIVER: no archiver left to try ($spec, $ArchiverWhy)"; exit 2 }
  if (-not ($Archivers -contains 'tar')) { $TarExe = $null }
}
$script:LinksInArchive = ($Archivers.Count -gt 0 -and $Archivers[0] -ne 'zip')
if ($Archivers.Count -gt 0 -and $Archivers[0] -eq 'zip') { $Archive = Join-PathSafe $OutputDir "$Name.zip" } else { $Archive = Join-PathSafe $OutputDir "$Name.tar.gz" }

$script:LogWriter = $null
$script:ManifestWriter = $null
if (-not $Inventory) {
  [void][System.IO.Directory]::CreateDirectory((Join-PathSafe $XStage 'fs'))
  $script:LogWriter = New-Object System.IO.StreamWriter($XLogPath, $false, $script:Utf8NoBom)
  $script:ManifestWriter = New-Object System.IO.StreamWriter($XManifestPath, $false, $script:Utf8NoBom)
  $script:LogWriter.AutoFlush = $true
}

$script:UserList = @(Get-UserHomes)

Write-CollectorLog "$TOOL $ToolVersion starting on $HostName ($([Environment]::OSVersion.VersionString), PowerShell $($PSVersionTable.PSVersion)) mode=$Mode root=$(if ($Root) { $Root } else { '\' })"
$archiveVia = 'none'; if ($Archivers.Count -eq 0) { } elseif ($Archivers[0] -eq 'zip') { $archiveVia = 'zip' } elseif ($Archivers[0] -eq 'tar') { $archiveVia = 'tar.gz via ' + $TarExe } elseif ($Archivers[0] -eq 'writer') { $archiveVia = 'tar.gz via PowerShell tar writer' }
if ($ArchiverWhy -and $Archivers.Count -gt 0 -and $Archivers[0] -ne 'tar') { $archiveVia += " ($ArchiverWhy)" }
Write-CollectorLog "archive=$archiveVia max_file_size=${MaxFileSizeMB}MB full=$($Full.IsPresent) no_secrets=$($NoSecrets.IsPresent) no_docker=$($NoDocker.IsPresent)"
$IsAdmin = $false
try { $IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) } catch { }
if ($Inventory -and $PSBoundParameters.ContainsKey('OutputDir')) { Write-CollectorLog "NOTE: -Inventory writes nothing; -OutputDir $OutputDir ignored" }
if ($Mode -eq 'live' -and -not $IsAdmin) { Write-CollectorLog "WARNING: not running as Administrator; other users' profiles will probably be unreadable" }
if ($script:UserList.Count -eq 0) { Write-CollectorLog 'WARNING: no user profile directories found' }
foreach ($ih in $script:InaccessibleHomes) { Write-CollectorLog "profile not accessible (skipped): $ih" }

Add-UserHomes

if (-not $NoDocker) { Add-DockerVolumes }

if (-not $NoProjects) {
  $script:ProjectList = @(Find-Projects)
  Add-Projects
}

if ($Inventory) {
  Write-Inventory
  exit 0
}

# ---------------------------------------------------------------------------
# Summary, archive, hashes
# ---------------------------------------------------------------------------
$EndTs = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
# Users whose home gave at least one manifest row, in enumeration order
$ActiveUsers = @($script:UserList | Where-Object { $script:RowHomes.ContainsKey($_.home) })
# 512 -> "512 B", 21868755 -> "20.9 MiB"
function Format-HumanSize([int64]$bytes) {
  $units = @('B', 'KiB', 'MiB', 'GiB', 'TiB')
  $v = [double]$bytes; $i = 0
  while ($v -ge 1024 -and $i -lt 4) { $v /= 1024; $i++ }
  if ($i -eq 0) { return "$bytes B" }
  return $v.ToString('0.0', [Globalization.CultureInfo]::InvariantCulture) + ' ' + $units[$i]
}
if ($script:LinkCounts.zip -gt 0) { Add-Note "$($script:LinkCounts.zip) symlinks are in the manifest only: the zip archive cannot store symlinks" }
if ($script:LinkCounts.failed -gt 0) { Add-Note "$($script:LinkCounts.failed) symlinks could not be recreated in the archive; each row's error says why" }
$summary = [ordered]@{
  tool = $TOOL; version = $ToolVersion; hostname = $HostName; mode = $Mode
  root = $(if ($Root) { $Root } else { '\' })
  platform = "Windows $([Environment]::OSVersion.Version) $env:PROCESSOR_ARCHITECTURE PowerShell $($PSVersionTable.PSVersion)"
  run_as = $(try { [Security.Principal.WindowsIdentity]::GetCurrent().Name } catch { [Environment]::UserDomainName + '\' + [Environment]::UserName })
  run_as_admin = $IsAdmin
  started = $StartTs; finished = $EndTs
  options = [ordered]@{ full = $Full.IsPresent; no_secrets = $NoSecrets.IsPresent; max_file_size_bytes = $MaxSize; users_filter = $Users; no_docker = $NoDocker.IsPresent; no_projects = $NoProjects.IsPresent; projects = @($Project) }
  capabilities = [ordered]@{ hash_tool = 'System.Security.Cryptography.SHA256'; archiver = $ArchiverLabels[$Archivers[0]] }
  users = @($script:UserList | ForEach-Object { $_.user })
  homes = @($script:UserList | ForEach-Object { $_.home })
  users_with_artifacts = @($ActiveUsers | ForEach-Object { $_.user })
  projects = @($script:ProjectList | ForEach-Object { $_.path })
  counts = [ordered]@{ collected = $script:Counts.collected; symlink = $script:Counts.symlink; skipped_excluded = $script:Counts.skipped_excluded; skipped_size = $script:Counts.skipped_size; skipped_secret = $script:Counts.skipped_secret; error_copy = $script:Counts.error_copy; skipped_unmatched_volume = $script:Counts.skipped_unmatched_volume; error_read = $script:Counts.error_read; collected_bytes = $script:Counts.bytes }
  docker = [ordered]@{ volumes_found = $script:Docker.found; volumes_collected = $script:Docker.collected; unreadable = $script:Docker.unreadable; docker_desktop = $script:Docker.desktop }
  notes = @($script:Notes)
  archive = (Split-Path -Leaf $Archive)
}
# Write collection.json and stage a copy. Called again before each fallback
# archiver, so the archived and the on-disk summary name the archive and the
# archiver actually used.
function Write-Summary {
  [System.IO.File]::WriteAllText($XSummaryPath, ($summary | ConvertTo-Json -Depth 4), $script:Utf8NoBom)
  Copy-Item -LiteralPath $XSummaryPath -Destination (Join-PathSafe $XStage 'collection.json') -Force
}
Write-Summary

Write-CollectorLog 'Archiving'
$script:ManifestWriter.Close()
$script:LogWriter.Close()
Copy-Item -LiteralPath $XManifestPath -Destination (Join-PathSafe $XStage 'manifest.jsonl') -Force
Copy-Item -LiteralPath $XLogPath -Destination (Join-PathSafe $XStage 'collector.log') -Force

# Each archiver in $Archivers is tried in turn. A failure is logged with its
# reason, its partial archive removed, and a note added; the summary, log and
# manifest are then restaged so the next archive holds what is written beside it.
function Format-ExitCode($code) {
  if ($null -eq $code) { return 'unknown' }
  if ([int]$code -lt 0) { return '0x' + ([int]$code).ToString('X8') }
  return [string]$code
}
function Clear-PartialArchive {
  try { if (Test-PathQuiet $Archive 'Any') { [System.IO.File]::Delete((ConvertTo-ExtendedPath $Archive)) } }
  catch { [System.IO.File]::AppendAllText($XLogPath, "could not remove partial archive ${Archive}: $($_.Exception.Message)`n", $script:Utf8NoBom) }
}
Clear-PartialArchive
$archiveOk = $false
$failedWhy = ''
for ($ai = 0; $ai -lt $Archivers.Count -and -not $archiveOk; $ai++) {
  $kind = $Archivers[$ai]
  try {
    if ($ai -gt 0) {
      if ($kind -eq 'zip' -and $script:StagedLinks.Count -gt 0) {
        # A zip cannot store the staged links, so they go first, and the
        # manifest is rewritten to say they are not in the archive.
        $nl = $script:StagedLinks.Count
        if ((Clear-StagedLinks) -gt 0) { throw 'staged symlinks could not be removed; not zipping through them' }
        Clear-LinkArchivePaths 'not in the archive: tar failed and zip cannot store symlinks'
        $script:Notes += "tar failed; $nl symlinks were removed from the staging tree before zipping, because zip cannot store symlinks"
        [System.IO.File]::AppendAllText($XLogPath, "NOTE: tar failed; $nl staged symlinks removed before zipping`n", $script:Utf8NoBom)
        Copy-Item -LiteralPath $XManifestPath -Destination (Join-PathSafe $XStage 'manifest.jsonl') -Force
      }
      $script:Notes += "$failedWhy; fell back to $($ArchiverLabels[$kind])"
      [System.IO.File]::AppendAllText($XLogPath, "NOTE: falling back to $($ArchiverLabels[$kind])`n", $script:Utf8NoBom)
      if ($kind -eq 'zip') { $Archive = Join-PathSafe $OutputDir "$Name.zip"; Clear-PartialArchive }
      # Write-Summary writes and restages collection.json with the notes,
      # the archive's name and the archiver.
      $summary.notes = @($script:Notes)
      $summary.archive = (Split-Path -Leaf $Archive)
      $summary.capabilities.archiver = $ArchiverLabels[$kind]
      Write-Summary
      Copy-Item -LiteralPath $XLogPath -Destination (Join-PathSafe $XStage 'collector.log') -Force
    }
  } catch {
    [System.IO.File]::AppendAllText($XLogPath, "FATAL: archive failed: $($_.Exception.Message)`n", $script:Utf8NoBom)
    break
  }
  if ($kind -eq 'tar') {
    $tarName = Split-Path -Leaf $TarExe
    $global:LASTEXITCODE = 0
    & $TarExe -czf $Archive -C $Stage . 2>>$LogPath
    $rcTar = $LASTEXITCODE
    if ($rcTar -eq 0 -and (Test-PathQuiet $Archive 'Any')) { $archiveOk = $true; break }
    if ($rcTar -eq 0) { $failedWhy = "$tarName failed (exit code 0 but no archive was written)" }
    else { $failedWhy = "$tarName failed (exit code $(Format-ExitCode $rcTar))" }
    [System.IO.File]::AppendAllText($XLogPath, "${tarName} failed: exit code $(Format-ExitCode $rcTar)`n", $script:Utf8NoBom)
  } else {
    try {
      if ($kind -eq 'writer') { Write-TarGz $Stage $Archive } else { Write-StageZip $Stage $Archive }
      if (Test-PathQuiet $Archive 'Leaf') { $archiveOk = $true; break }
      $failedWhy = "$($ArchiverLabels[$kind]) failed (no archive was written)"
    } catch {
      $e = $_.Exception; while ($null -ne $e.InnerException) { $e = $e.InnerException }
      $failedWhy = "$($ArchiverLabels[$kind]) failed ($($e.Message))"
      [System.IO.File]::AppendAllText($XLogPath, "$($ArchiverLabels[$kind]) failed: $($e.Message)`n", $script:Utf8NoBom)
    }
  }
  Clear-PartialArchive
}
if (-not $archiveOk) { Write-Error 'FATAL: archive not written'; exit 2 }

$ArchiveSha = Get-FileSha256 $Archive
$ArchiveSize = (Get-Item -LiteralPath (ConvertTo-ExtendedPath $Archive)).Length
[System.IO.File]::WriteAllText((ConvertTo-ExtendedPath "$Archive.sha256"), "$ArchiveSha  $(Split-Path -Leaf $Archive)`n", $script:Utf8NoBom)
[System.IO.File]::AppendAllText($XLogPath, "$EndTs done: $Archive ($ArchiveSize bytes, sha256 $ArchiveSha)`n", $script:Utf8NoBom)
# The archive's size and hash follow on stdout, so stderr gets only "done".
if (-not $Quiet) { [Console]::Error.WriteLine('done') }

if (-not $KeepStaging) {
  # A link that could not be deleted keeps the staging directory, which the log names.
  if ((Clear-StagedLinks) -eq 0) { try { Remove-Item -LiteralPath $XStage -Recurse -Force -ErrorAction Stop } catch { } }
  else { [System.IO.File]::AppendAllText($XLogPath, "staging directory kept because a staged link could not be removed: $Stage`n", $script:Utf8NoBom) }
}

$c = $script:Counts
Write-Output "archive:    $Archive"
Write-Output "size:       $ArchiveSize ($(Format-HumanSize $ArchiveSize))"
Write-Output "sha256:     $ArchiveSha"
Write-Output "manifest:   $ManifestPath"
Write-Output "summary:    $SummaryPath"
Write-Output "log:        $LogPath"
Write-Output "users:      $($ActiveUsers.Count)"
Write-Output "projects:   $($script:ProjectList.Count)"
Write-Output "collected:  $($c.collected) files, $($c.bytes) bytes ($(Format-HumanSize $c.bytes))"
Write-Output "skipped:    $($c.skipped_excluded) excluded, $($c.skipped_size) too large, $($c.skipped_secret) secret"
Write-Output "errors:     $($c.error_copy + $c.error_read) ($($c.error_copy) error_copy, $($c.error_read) error_read)"
if ($script:Docker.seen) {
  $dl = "docker:     $($script:Docker.found) volumes found, $($script:Docker.collected) collected, $($script:Docker.unreadable) unreadable"
  if ($script:Docker.unreadable -gt 0) { $dl += ' (run as root to collect)' }
  if ($script:Docker.desktop) { $dl += '; Docker Desktop VM disk not collected' }
  Write-Output $dl
}
exit 0
