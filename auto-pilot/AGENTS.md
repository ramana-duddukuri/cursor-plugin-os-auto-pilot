# Oniesoft Auto-Pilot — agent instructions

This plugin integrates Cursor with the Oniesoft test automation platform. It lets the
agent author, push, run, and analyze test cases via MCP tools. Three layers:

- **`server/`** — FastMCP server exposing ~31 typed REST wrapper tools
- **`skills/`** — Skill playbooks (SKILL.md) that guide multi-step workflows
- **`agents/`** — Specialist subagents delegated to for heavy lifting

## Project Connection Details

Company ID, user ID, project ID, and the API URLs are per-project settings, stored in a
`config.json` in the workspace folder (read it directly, like any other file).

**At the start of each session, read `config.json` from the workspace root and keep
`companyId`/`projectId`/`userId` in mind for the rest of the conversation.** Pass them
explicitly as `projectId` / `companyId` / `userId` (or `registerId` where a tool asks
for the user's ID) on every tool call that accepts them — do not assume they are
auto-injected. (`server/launch.py` also injects them as environment variables at
startup as a fallback, but that depends on the workspace being open when the server
launches — don't depend on it.)

The **API key** is the only credential held at plugin level: set it once under
**Plugins → Configure** (`PLATFORM_API_KEY`). It is injected automatically — never
read or pass it.

If `config.json` is missing a value you need, or a tool call fails with "No project_id
given and no default configured" (or similar), ask the user for the missing value
directly — never go hunting through other config files for identifiers.

**Project `config.json` format**:
```json
{
  "companyId": "43e4f7c3-1a17-4627-8d95-49fd59076851",
  "projectId": "248af507-c75c-4590-95b8-4145891df8d0",
  "userId": "15eb541f-2dbe-403f-8191-9e1ad15fc0ef",
  "platformApiUrl": "http://localhost:8000",
  "backendUrl": "http://localhost:8088"
}
```

## Author / created_by Fields

`save_claude_utils` (`userName`) and `save_claude_test_cases` (`created_by`) require a
**plain human display name**, e.g. `"Surya"` — never an email address, never a UUID.
Resolve it via `get_user_details_by_id_or_email_or_unique_key` and use **`empName`**
from the response. Passing an email (contains `@`) or a UUID does not raise a
validation error — the backend silently drops the entire batch and returns a generic
`{"detail": "No test cases were saved"}` with no indication of which field caused it.
Full detail and other backend quirks (bare-tag CSS selectors, a ~300-char `description`
limit) are in `skills/push-to-autopilot/SKILL.md` under "Known backend quirks".

> The `save_claude_*` tool names come from the platform's REST API, which names that
> endpoint family after the agent-authored (zero-LLM) push path. They are backend
> identifiers — do not rename them.

`get_user_details_by_id_or_email_or_unique_key` requires a real `companyId` — read it
from `config.json`. Never pass a placeholder/zero-filled UUID for any required ID just
to make a call succeed structurally — a wrong ID produces a misleading "not found"
error instead of the real problem (a missing config value).

## Tool Scope Rules

`get_autopilot_steps` — **only call this tool from within the `analyze-requirements`
skill**, during Step 2c before writing any autopilot steps. Never call it in any other
skill, agent, or inline conversation.

## Agent Delegation Rules

When the user asks to analyze an Oniesoft test run (why it failed, compare runs,
interpret a stack trace), always delegate to the `failure-analyst` subagent instead of
calling MCP tools inline in the main conversation.

## Three-Phase Test Case Workflow

| Phase | Skill | What happens |
|---|---|---|
| 1 | `analyze-requirements` | Analyze requirement docs / Swagger / codebase → generate markdown test cases + utils |
| 2 | `element-discoverer` agent | Enrich markdown with real element locators (Playwright or codebase grep) |
| 3 | `push-to-autopilot` | Read enriched markdown → call `save_claude_utils` then `save_claude_test_cases` |

## Performance Test Case Workflow

A separate, standalone workflow — not part of the three-phase pipeline above (no `el:`
elements, no Phase 2 discovery):

| Step | Skill/Tool | What happens |
|---|---|---|
| 1 (only if CSV-driven) | `create-datafile` | Generate + validate a CSV, upload via `upload_datafile` → returns a file `id` |
| 2 | `performance-testing` | Author load-test steps from a Swagger doc (single endpoint, or multi-endpoint flow with correlation) |
| 3 | `save_claude_test_cases` | Push with `test_mode="Performance"`, `file_ids` set when a CSV was created |

Author all performance-test content yourself — this workflow never calls the platform's
separate AI-driven performance-test-generation endpoint. `create-datafile` is also
usable standalone.

## Utils (Reusable Test Components)

Utils are reusable test flows (login, logout, create user, etc.) callable from multiple
test cases. Key rules:

- A util is identified when a setup/teardown flow appears in 2+ test cases
- Utils are always referenced in test case steps by **UUID**, never by name:
  `execute util "3fa85f64-..."`
- Utils are created via `save_claude_utils` **before** `save_claude_test_cases`
- **A util can never call another util.** `execute util "<uuid>"` is only valid inside a
  test case's own steps — never inside a UTIL-NNN section's Autopilot Steps. Nested util
  calls are not supported by the backend. Inline the steps instead.
- Utils have their own test data. A test case can optionally override it using
  `<field>_i<N>_<util-uuid>` where N = invocation number (1 = first call). Not mandatory.
- Before creating new utils, always call `fetch_util_details` to check for reuse

### Test Data Override Example

Login util (id: `3fa85f64-5717-4562-b3fc-2c963f66afa6`) has fields `email` and
`password`. A test case calling it twice with different credentials:

```
Step 1: execute util "3fa85f64-5717-4562-b3fc-2c963f66afa6"   ← first call
Step 2: [do something]
Step 3: execute util "3fa85f64-5717-4562-b3fc-2c963f66afa6"   ← second call
```

Test data in the test case:
```
email_i1_3fa85f64-5717-4562-b3fc-2c963f66afa6    = admin@example.com
email_i2_3fa85f64-5717-4562-b3fc-2c963f66afa6    = user@example.com
password_i1_3fa85f64-5717-4562-b3fc-2c963f66afa6 = AdminPass@1
```

## Key Files

| File | Purpose |
|---|---|
| `server/tools.py` | All MCP tool definitions |
| `server/request_response_model.py` | All Pydantic request/response models |
| `server/client.py` | Thin HTTP client (no business logic) |
| `skills/analyze-requirements/SKILL.md` | Phase 1 — requirement analysis + util/test case generation |
| `skills/push-to-autopilot/SKILL.md` | Phase 3 — push markdown to backend |
| `skills/run-tests/SKILL.md` | Run test cases or test runs (incl. Performance load profile) |
| `skills/schedule-test-run/SKILL.md` | Schedule an existing test run for a future date/time + environment |
| `skills/analyze-run/SKILL.md` | Failure analysis workflow |
| `agents/element-discoverer.md` | Phase 2 — enrich markdown with real locators |
| `agents/failure-analyst.md` | Deep failure triage (delegated, not inline) |
| `skills/create-datafile/SKILL.md` | Generate + upload a CSV data file (standalone) |
| `skills/performance-testing/SKILL.md` | Author performance/load test cases |

## MCP Tool Reference (most-used)

| Tool | What it does |
|---|---|
| `save_claude_utils` | Batch-create utils; returns UUIDs — call before `save_claude_test_cases` |
| `save_claude_test_cases` | Batch-create agent-authored test cases; no LLM re-analysis |
| `fetch_util_details` | Search/filter existing utils by name, module, feature, testMode |
| `create_util` | Create a single util directly (use `save_claude_utils` for batches) |
| `fetch_test_run_results` | Get all results for a completed run |
| `fetch_test_run_failure_details` | Get stack traces for failed cases |
| `get_feature_id_by_name_or_unique_key` | Resolve feature UUID — needed before pushing |
| `upload_datafile` | Upload a CSV to `datafiles/v1/upload`; returns the `id` for `file_ids` |
| `run_test_case` | Start one test case; carries the load profile for Performance cases |
| `get_environments_assigned_to_user` | List a user's environments — the source for any environment prompt |
| `schedule_test_run` | Set an existing test run to execute later; `environment` is a **name**, not a UUID |

## Performance Run Profile

Virtual users, ramp pattern, and duration are **run-time config**, never authored into steps
(see `performance-testing/SKILL.md`). Defaults live in the backend's `LoadProfileValidator`
and are applied there when a field is omitted — **100** VUs, **linear**, **1m**. Send only what
the user explicitly chose so those defaults stay the single source of truth.

Field names on the wire must match the backend's `TestCaseRunDto` exactly — `virtualUsers`
(plural), `duration`, `rampPattern`. A misspelled field is dropped silently by Jackson and the
run falls back to defaults with no error, so a "why did it run with 100 users?" bug looks like
a backend problem when it's a typo.

Duration from this plugin is capped at **3 minutes**; longer runs belong on
https://www.osautopilot.com. `RunTestCaseInput` enforces the cap, but `run-tests` should catch
it first so the user gets an explanation instead of a validation error.

## Pending Backend Work

`POST /api/utils/create-from-claude` needs to be implemented on the Platform API
(`agentic_ai_be`). Full spec in `docs/backend-utils-create-from-claude.md`. Until that
endpoint exists, `save_claude_utils` returns a 404/500 — the rest of the plugin works.
