---
name: create-defect
description: Create an Oniesoft defect from a test failure or manual triage. Resolves assignees via project user lookup, groups duplicate failures into one defect with test-case unique keys in dependency. Use when the user asks to log a bug, create a defect, or file an issue — including after analyze-run when failures should become defects.
---

# Create Defect

Log a defect on the Oniesoft platform via `create_defect`.

> **User names, not UUIDs:** `createdBy`, `assignedTo`, `updatedBy`, `developedBy`,
> `verifiedBy`, `automatedBy`, and `reviewedBy` all take plain display names (`empName`)
> — never an email or UUID. Resolve names with `get_user_details_by_id_or_email_or_unique_key`.

---

## Step 1 — Resolve the creator

Read `config.json` for `userId`, `companyId`, and `projectId`.

Call `get_user_details_by_id_or_email_or_unique_key` with:
- `identifier` → `userId` from config
- `companyId` → from config

Use the returned `empName` as `createdBy` and all other creator/updater name fields
(`updatedBy`, `developedBy`, `verifiedBy`, `automatedBy`, `reviewedBy`).

---

## Step 2 — Choose assignee

Call `get_users_assigned_to_project` with `projectId` from config. Present every returned
user in a table:

| # | Name | Email | Role |
|---|---|---|---|

Ask who should own the defect — **ask even when only one user is returned**.

If the list is empty, fall back to `get_user_details_by_id_or_email_or_unique_key` with
`companyId` from config and a name/email search term.

Use the chosen user's:
- `empName` → `assignedTo` and the other name fields above (same as creator when self-assigned)
- `userId` → `assignedToUUID`

---

## Step 3 — Module and feature

`create_defect` requires `module` and `feature` as **UUIDs**.

Failed cases from `fetch_test_run_results` already carry `module` and `feature` on each
`failed_cases` entry. Use those values first — **do not look up when the value is already
a UUID**:

1. Pick module/feature from a representative case in the failure group (first case, or the
   largest shared module+feature pair across the group).
2. For each value:
   - **Valid UUID** → pass it straight to `create_defect`.
   - **Name or unique key** (e.g. `"Authentication"`, `"FEAT-0042"`) → resolve once:

     | Field | Tool |
     |---|---|
     | Module | `get_module_id_by_name_or_unique_key` with `identifier` = module value |
     | Feature | `get_feature_id_by_name_or_unique_key` with `identifier` = feature value |

     Use the returned `.id` UUID.

3. If the run payload also has `moduleId` / `featureId` fields on a failed case, prefer
   those over `module` / `feature` when present.

If cases in one group span different modules/features, use the pair from the largest
sub-group, or ask the user.

---

## Step 4 — Defect content

Collect or draft:

| Field | Guidance |
|---|---|
| `title` | Short, specific summary of the failure (≤ 120 chars) |
| `description` | Root cause, failing step, trace excerpt, environment, run name/ID |
| `priority` | Default `Minor`. Map test `severity` when known: Blocker→Blocker, Critical→Critical, Major→Major |
| `dependency` | Comma-separated test-case unique keys, e.g. `TC-89765,TC-89099` — no spaces |
| `testMode` | `Web`, `API`, `Mobile`, or `CLI` from the failing case(s) |
| `testType` | `Automation` for automated test failures; `Manual` otherwise |
| `rootCause` | Default `Other`; set a more specific value when clear from triage |

Leave `status`, `state`, `sprint`, and `story` unset unless the user specifies them.

---

## Step 5 — Create

Call `create_defect` with all required fields:

```
title, description, assignedTo, assignedToUUID, userId, createdBy,
updatedBy, developedBy, verifiedBy, automatedBy, reviewedBy,
module, feature, projectId, companyId
```

Plus optional: `priority`, `dependency`, `testMode`, `testType`, `rootCause`,
`environment`, `browser`, `comments`.

Report back: defect `uniqueKey`, `title`, assignee, and linked test cases (`dependency`).

---

## From test-run analysis — group unique failures

Use this when the user confirms defect creation after `analyze-run` / `failure-analyst`.

1. **Group failures by root cause** — cases that failed for the same reason (same assertion,
   same missing element, same API error) belong in one group. Normalize trace text before
   comparing (strip timestamps, run IDs, and volatile URLs).

2. **One defect per group** — if 3 test cases failed with the same reason, create **one**
   defect, not three.

3. **`dependency`** — comma-join every `uniqueKey` in the group
   (from `failed_cases` in `fetch_test_run_results`). Skip cases with no unique key.

4. **Title** — summarize the shared failure, e.g.
   `Login button not found on checkout page`.

5. **Description** — list all affected test case names and unique keys, the shared root cause,
   and one representative trace. Note the test run name/ID.

6. **Skip non-defect failures** unless the user asks to include them — do not create defects
   for pure environment/setup issues (auth failure, missing test data, network timeout) unless
   the user explicitly wants those logged too.

7. **Confirm before creating** — show a table of planned defects:

   | # | Title | Test cases (unique keys) | Priority | Assignee |
   |---|---|---|---|---|
   | 1 | … | TC-001, TC-002, TC-003 | Major | … |

   Ask the user to confirm or adjust assignee/priority, then create each row via Step 5.

---

## Examples

**Single manual defect**

User: "Create a defect for the login failure, assign to Priya"

→ Resolve Priya via `get_user_details_by_id_or_email_or_unique_key`, resolve module/feature,
draft title/description from context, call `create_defect`.

**After run analysis — 5 failures, 2 unique causes**

| Group | Cases | Action |
|---|---|---|
| Element `#submit` not found | TC-101, TC-102, TC-103 | 1 defect, `dependency: TC-101,TC-102,TC-103` |
| API 500 on `/orders` | TC-201, TC-202 | 1 defect, `dependency: TC-201,TC-202` |

→ 2 `create_defect` calls total.
