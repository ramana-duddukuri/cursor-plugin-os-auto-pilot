# Oniesoft Cursor Marketplace

A local Cursor marketplace for Oniesoft's **auto-pilot** plugin. Works on **Cursor individual plan** — clone this repo, register it as a marketplace from disk, and install the plugin from **Settings** or **Customize**.

```
oniesoft-cursor-marketplace/
├── .cursor-plugin/
│   └── marketplace.json          # lists the plugins in this repo
└── auto-pilot/
    ├── .cursor-plugin/plugin.json
    ├── mcp.json                  # MCP server registration
    ├── hooks/hooks.json          # sessionStart dependency pre-warm
    ├── skills/                   # 8 workflow playbooks
    ├── agents/                   # 3 specialist subagents
    ├── server/                   # bundled FastMCP server (~31 tools)
    ├── docs/INSTALLATION.md      # full install guide
    └── AGENTS.md                 # operational rules for the agent
```

## Plugins

| Plugin | What it does |
|---|---|
| [`auto-pilot`](auto-pilot/) | Generate web/API/mobile/performance test cases, run them, and analyze failures on the Oniesoft platform. |

## Installation

**Full step-by-step guide:** [auto-pilot/docs/INSTALLATION.md](auto-pilot/docs/INSTALLATION.md)

### Quick start

```bash
# 1. Clone
git clone https://bitbucket.org/onie-soft/auto-pilot-cursor-plugin.git ~/oniesoft-cursor-marketplace
```

2. Cursor → **Settings** or **Customize** → **Add Marketplace from disk** → select `~/oniesoft-cursor-marketplace`
3. **Install** → **auto-pilot by Oniesoft**
4. In each test project workspace, create `.env`:

```env
PLATFORM_API_KEY=your-personal-api-key-here
```

5. Add `config.json` to the project root (see [AGENTS.md](auto-pilot/AGENTS.md) for the format)
6. **Restart Cursor**

### Updating

After `git pull`, you must **reinstall the marketplace**, **reinstall the plugin**, and **restart Cursor** — Cursor caches installed plugins and does not pick up disk changes automatically.

```bash
cd ~/oniesoft-cursor-marketplace && git pull
```

Then in Cursor: remove & re-add marketplace from disk → uninstall & reinstall **auto-pilot** → quit and reopen Cursor.

## API key and configuration

| Setting | Where | Notes |
|---|---|---|
| **API key** | Workspace `.env` → `PLATFORM_API_KEY` | Required. Generate in platform → Users → API Keys. **Never commit `.env`.** |
| **Company / project / user IDs** | Workspace `config.json` | Per test project |
| **API URLs** | `config.json` (or optional `.env` overrides) | `platformApiUrl`, `backendUrl` |

Do **not** rely on the plugin **Configure** UI for the API key — set it in `.env` for each workspace.

If no key is found, the MCP server logs a clear error at startup rather than failing with a confusing 403.

## Requirements

- [Cursor](https://cursor.com) (individual plan is sufficient)
- [Git](https://git-scm.com/downloads)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) on PATH (resolves Python 3.10+ and dependencies)
- Reachable Oniesoft backends: platform API (`:8000`), backend (`:8088`)
- A personal API key — platform → Users → API Keys
