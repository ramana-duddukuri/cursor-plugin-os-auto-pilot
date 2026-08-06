# Oniesoft Cursor Marketplace

A private Cursor **team marketplace** hosting Oniesoft's plugins.

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
    └── AGENTS.md                 # operational rules for the agent
```

## Plugins

| Plugin | What it does |
|---|---|
| [`auto-pilot`](auto-pilot/) | Generate web/API/mobile/performance test cases, run them, and analyze failures on the Oniesoft platform. |

## Publishing this marketplace (admin, one time)

Requires a Cursor **Teams** (1 marketplace) or **Enterprise** (unlimited) plan.

1. Push this repo to GitHub.
2. [cursor.com](https://cursor.com) → **Dashboard → Plugins**
3. **Team Marketplaces → Add Marketplace → Import from Repo**, paste the repo URL
4. **Add to Marketplace** for `auto-pilot`
5. Set access (Organization Groups) and install mode — Default Off / Default On /
   Required. Enable **Auto Refresh** to pick up pushes automatically.

## Installing (teammates)

1. **Customize** → find **auto-pilot** → **Install**
2. **Configure** → paste your Oniesoft **API key** (`PLATFORM_API_KEY`)
3. Add a `config.json` to each test project (see
   [auto-pilot/AGENTS.md](auto-pilot/AGENTS.md) for the format)

`PLATFORM_API_URL` and `BACKEND_URL` are optional overrides — leave them blank and the
per-project `config.json` supplies them.

## Local development

Cursor **rejects symlinks** whose target sits outside `~/.cursor/plugins/local`, so a
dev install must be a real copy of the **plugin folder** (not the marketplace root):

```bash
rsync -a --delete --exclude '.git' --exclude '.venv' --exclude '__pycache__' --exclude '.data' auto-pilot/ ~/.cursor/plugins/local/auto-pilot/
```

Re-run after edits, then Cmd+Shift+P → **Reload Window**.

> Local installs get **no Configure UI** — that only exists for marketplace plugins. For
> local testing, put a literal key in `auto-pilot/mcp.json`'s `env` block, and take care
> not to commit it.

## Requirements

- `uv` on PATH (the server resolves its own Python 3.10+ and dependencies)
- Reachable Oniesoft backends: platform API (`:8000`), backend (`:8088`)
- A personal API key — platform → Users → API Keys
