# Installing the Oniesoft Auto-Pilot Cursor Plugin

This guide covers installing **auto-pilot by Oniesoft** in Cursor on an **individual plan** — no Teams or Enterprise subscription required.

Distribution works by cloning this repository to your machine, registering it as a **local marketplace from disk**, and installing the plugin from **Settings** or **Customize**. Your Oniesoft **API key** goes in a workspace **`.env`** file.

---

## What you need before you start

| Requirement | Why | Download / docs |
|---|---|---|
| **Cursor IDE** (individual plan) | Hosts the plugin, agent, and MCP server | [cursor.com](https://cursor.com) |
| **Git** | Clone and pull plugin updates | [git-scm.com](https://git-scm.com/downloads) |
| **uv** | The MCP server is launched with `uv run` | [uv installation](https://docs.astral.sh/uv/getting-started/installation/) |
| **Python 3.10+** | Required by the MCP server | Auto-installed by `uv` on first run; manual: [python.org](https://www.python.org/downloads/) |
| **Oniesoft platform access** | The plugin calls your platform API | Cloud or self-hosted instance |
| **Personal API key** | Authenticates every API call (`x-api-key` header) | Platform → **Users → API Keys** |

### Install Cursor

Download and install from [cursor.com](https://cursor.com). An individual (Pro) plan is sufficient.

Plugin docs: [cursor.com/docs/plugins](https://cursor.com/docs/plugins)

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:

```bash
uv --version
```

Full details: [docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/)

### Python 3.10+

You do **not** need to pre-install Python. On session start the plugin bootstraps via:

```bash
uv run --with-requirements server/requirements.txt --python ">=3.10" ...
```

`uv` downloads a compatible Python automatically if needed.

---

## Step 1 — Clone the marketplace repository

Clone the repo to a fixed location on your machine. You will point Cursor at this folder as the marketplace source.

```bash
git clone https://bitbucket.org/onie-soft/auto-pilot-cursor-plugin.git ~/oniesoft-cursor-marketplace
cd ~/oniesoft-cursor-marketplace
```

The folder you clone must contain `.cursor-plugin/marketplace.json` at its root:

```
oniesoft-cursor-marketplace/          ← point Cursor at this folder
├── .cursor-plugin/
│   └── marketplace.json
└── auto-pilot/
    ├── .cursor-plugin/plugin.json
    ├── mcp.json
    └── ...
```

---

## Step 2 — Add the marketplace from disk

1. Open **Cursor**.
2. Go to **Settings** → **Plugins**, or open **Customize** from the sidebar.
3. Click on **Browser Marketplace**. 
4. Choose **Add Marketplace** (or equivalent) → **From disk** / **Local path**.
4. Select the **cloned repository root** — the folder that contains `.cursor-plugin/marketplace.json` (e.g. `~/oniesoft-cursor-marketplace`).
5. Confirm the marketplace is registered. You should see the **oniesoft/Personal** marketplace with the **auto-pilot** plugin listed.

---

## Step 3 — Install the plugin

From **Settings → Plugins** or **Customize**:

1. Open the **oniesoft** marketplace you just added.
2. Find **auto-pilot by Oniesoft**.
3. Click **Install/Add**.

After install, the plugin provides MCP tools, skills, agents, and hooks. You do **not** need to enter the API key in the plugin Configure UI — use a workspace `.env` file instead (next step).

---

## Step 4 — Set your API key in `.env`

Create a `.env` file in the **root of each test project workspace** (the folder you open in Cursor):

```env
PLATFORM_API_KEY=your-personal-api-key-here
```

> **Never commit `.env`** — it is gitignored. Each developer keeps their own key locally.

**Generate a key:** In the Oniesoft platform UI, go to **Profile → API Keys**. Create a key. A `401` from any tool means the key is missing or expired; a `403` means it lacks the required scope.

If the key is missing, the MCP server logs:

```
auto-pilot: no PLATFORM_API_KEY configured. Add PLATFORM_API_KEY=... to /path/to/project/.env
```

---

## Step 5 — Add `config.json` to your project

Per-project IDs and API URLs live in `config.json` at the workspace root:

The API key is the **only** global plugin setting. Everything else is **per-project** and lives in a `config.json` file in the root of the project you are working in.

Download `config.json` and place it in your project folder. The downloaded file looks like this:

```json
{
  "companyId": "your-company-uuid",
  "projectId": "your-project-uuid",
  "userId": "your-user-uuid",
  "platformApiUrl": "https://your-platform-api.example.com",
  "backendUrl": "https://your-backend.example.com"
}
```

| Field | Description |
|---|---|
| `companyId` | Your Oniesoft company UUID |
| `projectId` | The test project UUID |
| `userId` | Your user/register UUID |
| `platformApiUrl` | Platform API base URL (e.g. `http://localhost:8000` for local dev) |
| `backendUrl` | Execution backend URL (e.g. `http://localhost:8088` for local dev) |

Cursor reads this file at the start of each session. Pass these IDs explicitly on MCP tool calls — they are not auto-injected into every request.

To Download `config.json`:

1. Go to your Oniesoft platform and navigate to the project (Workspace) you want to work on.
2. Click the **Download config** button to download `config.json`.

---

## Step 6 — Restart Cursor

After the first install (or any reinstall), **fully quit and restart Cursor** — do not rely on **Reload Window** alone for marketplace/plugin changes to take effect.

On first start, the plugin's sessionStart hook bootstraps Python dependencies via `uv`.

---

## Updating to a new plugin version

Cursor caches marketplace and plugin installs. After every update you must **pull, reinstall, and restart**.

### 1. Pull the latest code

```bash
cd ~/oniesoft-cursor-marketplace
git pull
```

### 2. Reinstall the marketplace

In **Settings → Plugins** or **Customize**:

1. **Remove** the existing **oniesoft** marketplace (from disk).
2. **Add** it again **from disk**, pointing at the same cloned folder (now with the updated files).

### 3. Reinstall the plugin

1. **Uninstall** **auto-pilot by Oniesoft**.
2. **Install** it again from the freshly re-added marketplace.

### 4. Restart Cursor

**Quit Cursor completely** and open it again so the new plugin version loads.

Repeat this full cycle whenever you are told a new version is available or after you `git pull` changes you want to use.

---

## Verify the installation

### 1. Plugin is installed

**Customize** or **Settings → Plugins** → **auto-pilot by Oniesoft** appears as installed.

### 2. MCP tools are available

In the Cursor agent chat:

> List the available auto-pilot MCP tools.

You should see `save_claude_test_cases`, `run_test_case`, `fetch_test_run_results`, etc.

### 3. Smoke-test an API call

With `.env` and `config.json` in your workspace:

> Call `get_projects_assigned_to_user` for my user.

A successful response confirms the API key and project config are correct.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Marketplace not listed | Wrong folder selected | Point at the **repo root** containing `.cursor-plugin/marketplace.json`, not the `auto-pilot/` subfolder |
| Plugin not visible | Marketplace not added | Re-add marketplace from disk |
| `uv: command not found` | uv missing from PATH | Install uv, restart Cursor |
| `no PLATFORM_API_KEY configured` | Missing `.env` | Add `PLATFORM_API_KEY=...` to workspace root `.env` |
| `401` on tool calls | Bad or expired key | Regenerate key in platform, update `.env`, restart Cursor |
| `403` on tool calls | Key lacks scope | Regenerate with `generate` / `run` / `read` scopes |
| `No project_id given...` | Missing `config.json` | Add `config.json` to workspace root |
| Old behavior after `git pull` | Cached plugin copy | Reinstall marketplace + plugin, then **restart Cursor** |
| MCP server won't start | Deps not bootstrapped | Restart Cursor; or from `auto-pilot/`: `uv run --with-requirements server/requirements.txt --python ">=3.10" server/launch.py --bootstrap-only` |

---

## Quick reference

```bash
# Prerequisites
curl -LsSf https://astral.sh/uv/install.sh | sh

# One-time setup
git clone https://bitbucket.org/onie-soft/auto-pilot-cursor-plugin.git ~/oniesoft-cursor-marketplace
```

Then in Cursor:

1. **Settings** or **Customize** → **Add Marketplace from disk** → select `~/oniesoft-cursor-marketplace`
2. **Install** → **auto-pilot by Oniesoft**
3. Add `.env` (`PLATFORM_API_KEY=...`) and `config.json` to each test project
4. **Restart Cursor**

**On every update:**

```bash
cd ~/oniesoft-cursor-marketplace && git pull
```

→ remove & re-add marketplace from disk → uninstall & reinstall plugin → **restart Cursor**
