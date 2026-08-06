"""Launcher for the Oniesoft MCP server.

Cursor runs this via ``uv run --with-requirements server/requirements.txt``,
which resolves/installs a compatible Python and dependencies before handing off
here — cross-platform, with no bespoke venv-bootstrap code needed in this file.

The API key and any URL overrides arrive in the environment already, substituted
by Cursor from the ``variables`` schema declared in ``.cursor-plugin/plugin.json``
(set per user under Plugins -> Configure). This script only injects the
*per-project* settings that no plugin-level config can know — company/user/project
ID and API URLs, read from the project's own ``config.json``.

Run with ``--bootstrap-only`` (used by the sessionStart hook) to let `uv run`
finish syncing dependencies and exit immediately, so the first tool call isn't
delayed by the install.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import MutableMapping

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ${CURSOR_PLUGIN_DATA} is exported to plugin subprocesses where available; fall
# back to a local dir so a plain checkout still works.
DATA_DIR = os.environ.get("CURSOR_PLUGIN_DATA") or os.path.join(PLUGIN_ROOT, ".data")


def _inject_project_config(env: MutableMapping[str, str], project_dir: str) -> None:
    """Read the project's config.json (in the user's workspace — not the plugin
    directory) and inject company/user/project ID and API URLs.

    These values are per-project, not per-user plugin settings, so they live in a
    config.json that ships with the project folder itself rather than in the
    plugin's own configuration.

    Values already present in the environment win, so a URL set in
    Plugins -> Configure overrides the project file.
    """
    field_env_map = {
        "companyId": "PLATFORM_COMPANY_ID",
        "userId": "PLATFORM_USER_ID",
        "projectId": "PLATFORM_PROJECT_ID",
        "platformApiUrl": "PLATFORM_API_URL",
        "backendUrl": "BACKEND_URL",
    }

    project_config = os.path.join(project_dir, "config.json")
    try:
        with open(project_config, encoding="utf-8") as fh:
            config = json.load(fh)
    except Exception:
        return

    for field, env_var in field_env_map.items():
        val = config.get(field)
        if val and not env.get(env_var):
            env[env_var] = str(val)

    # Persist a fixed-location snapshot of the per-project IDs so server
    # instances spawned WITHOUT workspace context can still resolve them at
    # request time. DATA_DIR is the same fixed path for every process of this
    # plugin, so this healthy launch's snapshot is readable by a context-less
    # one. See client.default_project_id. Only write when we actually have a
    # project id, so a context-less launch never clobbers a good snapshot.
    snapshot = {
        key: config[key]
        for key in ("projectId", "userId", "companyId")
        if config.get(key)
    }
    if snapshot.get("projectId"):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(
                os.path.join(DATA_DIR, "active_project.json"), "w", encoding="utf-8"
            ) as fh:
                json.dump(snapshot, fh)
        except Exception:
            pass


#: Settings that may come from the plugin's Configure UI or the workspace .env.
_OVERRIDABLE = ("PLATFORM_API_KEY", "PLATFORM_API_URL", "BACKEND_URL")


def _is_placeholder(val: str) -> bool:
    """True if `val` is an unsubstituted ``${VAR}`` template rather than a value."""
    return val.startswith("${") and val.endswith("}")


def _promote_configured(env: MutableMapping[str, str]) -> None:
    """Move real ``CONFIGURED_*`` values onto their plain names, highest priority.

    mcp.json deliberately injects the Configure-UI variables under a
    ``CONFIGURED_`` prefix. A server's ``env`` block overrides anything loaded
    from its ``envFile``, so injecting them under the plain names would let an
    *unset* plugin variable — which arrives as the literal string
    ``${PLATFORM_API_KEY}`` — silently clobber a perfectly good key from the
    workspace .env. Promoting here, and only when the value is real, keeps the
    intended precedence: Configure > .env > config.json.
    """
    for name in _OVERRIDABLE:
        configured = env.pop(f"CONFIGURED_{name}", "")
        if configured and not _is_placeholder(configured):
            env[name] = configured


def _load_env_file(env: MutableMapping[str, str], project_dir: str) -> None:
    """Fill any still-unset setting from the workspace's ``.env``.

    Cursor's ``envFile`` already does this for stdio servers, so this is a
    fallback for hosts that don't support it. Only fills gaps — never overrides
    a value that Configure supplied.
    """
    path = os.path.join(project_dir, ".env")
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except Exception:
        return

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key not in _OVERRIDABLE or env.get(key):
            continue
        val = val.strip().strip("'\"")
        if val and not _is_placeholder(val):
            env[key] = val


def _strip_unresolved(env: MutableMapping[str, str]) -> None:
    """Drop env vars still holding an unsubstituted ``${VAR}`` placeholder.

    An optional plugin variable the user left blank can arrive as the literal
    template text. Left in place it would be treated as a real value — an
    unusable API URL, or an API key that fails auth with a confusing 401 instead
    of the accurate "no key configured".
    """
    for key, val in list(env.items()):
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            del env[key]


def main() -> None:
    if "--bootstrap-only" in sys.argv[1:]:
        # `uv run` has already synced the environment by the time this code
        # runs; nothing further to do.
        return

    # Precedence, highest first: Configure UI > workspace .env > config.json.
    _promote_configured(os.environ)
    _strip_unresolved(os.environ)

    # Cursor sets CURSOR_PROJECT_DIR, and also CLAUDE_PROJECT_DIR as a
    # deliberate compatibility alias; either identifies the open workspace.
    project_dir = (
        os.environ.get("CURSOR_PROJECT_DIR")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    _load_env_file(os.environ, project_dir)
    _inject_project_config(os.environ, project_dir)

    if not os.environ.get("PLATFORM_API_KEY"):
        # Fail loudly here rather than let every tool call come back 403 with no
        # hint that the cause is configuration rather than permissions.
        print(
            "auto-pilot: no PLATFORM_API_KEY configured. Set it under "
            "Plugins -> auto-pilot -> Configure, or add PLATFORM_API_KEY=... to "
            f"{os.path.join(project_dir, '.env')}",
            file=sys.stderr,
        )

    sys.path.insert(0, PLUGIN_ROOT)
    os.chdir(PLUGIN_ROOT)
    from server.tools import mcp  # noqa: E402

    mcp.run()  # stdio transport


if __name__ == "__main__":
    main()
