# Local storage formats

How downloaded test data is stored in `dataExports/`. The download skill (`.claude/skills/download-test-data/`) writes and validates files in exactly this format.

Gmail is skipped (see README). Asana is not covered yet; its section will be added by the group member who owns it.

## Rules for every service

- **One JSON file per item**, at `dataExports/<service>/<id>.json`, where `<id>` is the item's stable ID from the service. Characters other than `A-Z a-z 0-9 . _ -` are replaced with `_` (none of the current IDs need this).
- Files are UTF-8, pretty-printed with 2-space indentation, one top-level object.
- Every file has `"service"` (the folder name) and `"exported_at"` (when this file's content was last written).
- **Timestamps** (`*_at`, `*_time`) are ISO 8601 in UTC with a `Z` suffix: `YYYY-MM-DDTHH:MM:SSZ`, or with milliseconds when the source gives them (`2026-10-13T20:10:56.686Z`). Date-only values (`due_date`) are `YYYY-MM-DD`.
- **Nothing is invented.** A field the source does not provide at all is left out of the file. A field the source provides as empty (a repo without a description, an issue without a due date) is stored as `null`.
- **Re-runs:** a file is rewritten only when its content (ignoring `exported_at`) changed, so `exported_at` shows when the item last changed locally.

## GitHub: `dataExports/github/`

Scope: every repository named `atlas-*` on the test account.

Filename: the repository's GraphQL node ID, e.g. `R_kgDOxxxxxx.json`. It stays the same if the repo is renamed, which the name does not.

| Field | Type | Source |
| --- | --- | --- |
| `id` | string | repository node ID |
| `database_id` | number | numeric REST repository ID |
| `name` | string | e.g. `atlas-route-optimizer` |
| `full_name` | string | `owner/name` |
| `owner` | string | account login |
| `description` | string or null | repository description |
| `html_url` | string | web URL |
| `clone_url` | string | HTTPS clone URL |
| `ssh_url` | string | SSH clone URL |
| `homepage_url` | string or null | homepage field |
| `visibility` | string | `public` or `private` |
| `is_fork`, `is_archived` | boolean | |
| `default_branch` | string or null | |
| `primary_language` | string or null | |
| `topics` | string[] | |
| `license` | string or null | SPDX ID |
| `stargazers_count`, `forks_count` | number | |
| `created_at`, `updated_at`, `pushed_at` | timestamp | repository dates |
| `readme_path` | string or null | path of the README in the default branch |
| `readme_text` | string or null | full README text, decoded; `null` if the repo has no README |
| `exported_at` | timestamp | |

## Notion: `dataExports/notion/`

Scope: every page found by the Notion search for "Atlas" or "Lisbon" (results merged, duplicates removed).

Filename: the page ID in dashed UUID form, e.g. `3f84a0df-c34b-8104-b504-d83d98d0e54c.json`.

| Field | Type | Source |
| --- | --- | --- |
| `id` | string | page ID (dashed UUID) |
| `type` | string | always `page` |
| `title` | string | title property, without the icon |
| `icon` | object or null | `{"type": "emoji", "emoji": "🧭"}` |
| `cover` | object or null | `null` means the page has no cover |
| `url` | string | `https://app.notion.com/p/<id without dashes>` |
| `ancestor_path` | array | parent pages/databases; `[]` for top-level workspace pages |
| `properties` | object | page properties as returned by Notion |
| `verification_state` | string | e.g. `unverified` |
| `workspace` | object | `{"id", "name"}` of the workspace |
| `last_edited_time` | timestamp | page last edited |
| `content_snapshot_at` | timestamp | the "as of" time Notion reported for the fetched content |
| `body_format` | string | `notion-enhanced-markdown` |
| `body_markdown` | string | full page body in Notion's enhanced Markdown (tables appear as `<table>` tags) |
| `exported_at` | timestamp | |

## Linear: `dataExports/linear/`

Scope: every issue in the team with key `ATL`, including completed and canceled issues.

Filename: the issue's UUID, e.g. `9b1c...-....json`. The human identifier (`ATL-12`) is stored in the file but not used as the filename, because it changes if the issue moves to another team.

| Field | Type | Source |
| --- | --- | --- |
| `id` | string | issue UUID |
| `identifier` | string | e.g. `ATL-12` |
| `title` | string | |
| `description` | string or null | Markdown description |
| `status` | string | workflow state name, e.g. `In Progress` |
| `status_type` | string | state category: `backlog`, `unstarted`, `started`, `completed`, `canceled` |
| `priority` | number | 0 none, 1 urgent, 2 high, 3 medium, 4 low |
| `priority_label` | string | label Linear shows for `priority` |
| `due_date` | date or null | `YYYY-MM-DD` |
| `estimate` | number or null | points |
| `url` | string | issue URL |
| `team_key` | string | `ATL` |
| `assignee`, `labels`, `project`, `cycle` | as returned | kept when the server returns them |
| `created_at`, `updated_at` | timestamp | |
| `started_at`, `completed_at`, `canceled_at` | timestamp or null | when the server returns them |
| `exported_at` | timestamp | |

## Todoist: `dataExports/todoist/`

Scope: every task (open and completed) in the project `Project Atlas` on the test account.

Filename: the task ID, e.g. `6hp6fwP8qC3W8JXm.json`.

| Field | Type | Source |
| --- | --- | --- |
| `id` | string | task ID |
| `content` | string | task title |
| `description` | string or null | task description; the task owner is written here too |
| `due_date` | date or null | `YYYY-MM-DD` |
| `is_recurring` | boolean | |
| `priority` | string | `p1` (highest) to `p4` (default) |
| `labels` | string[] | label names; used for the task owner (e.g. `joe-smith`) |
| `project_id`, `project_name` | string | project the task belongs to |
| `section_id`, `section_name` | string or null | section (`To Do`, `In Progress`, `Done`); used as the status |
| `checked` | boolean | `true` once completed |
| `added_at` | timestamp | when the task was created |
| `completed_at` | timestamp or null | when it was completed; `null` while open |
| `exported_at` | timestamp | |

## Limitations

- **Current export status (2026-10-16):** Notion: 10 pages. GitHub: 10 repositories. Linear: 14 issues (10 Project Atlas issues plus Linear's 4 default onboarding issues, ATL-1 to ATL-4). Todoist: 12 tasks (2026-10-18). All files pass `validate.py`.
- **Notion has no creation time.** The Notion MCP `fetch` tool returns `last_edited_time` but not `created_time` or the page author, so those fields are left out.
- **Notion search is keyword-based** and capped at 50 results per query. A page that mentions Atlas or Lisbon only in a way the search index misses would not be exported. Search timestamps are rounded to the minute, so the skill uses the fetched `last_edited_time` as the authoritative edit time.
- **Notion bodies are Markdown, not Notion blocks.** Formatting maps to enhanced Markdown; comments and discussions are not exported. Uploaded files are referenced, not downloaded.
- **GitHub README** is the one GitHub picks for the default branch; READMEs in subfolders or other branches are not included. Issues, pull requests and code are not exported.
- **Linear** fields depend on what the official Linear MCP server returns; fields it omits are left out rather than filled in. Comments, attachments and sub-issue trees are not exported.
- **Todoist** returns no last-changed time and no task URL, so neither is stored and every task is re-listed on each run (unchanged files are still left alone). Free personal projects have no assignees, so the owner is a label plus a line in the description. Status is the section; completed tasks have `checked: true`. Comments, reminders and subtasks are not exported.
- **Deletions are not mirrored.** If an item is deleted at the source, its old file stays in `dataExports/` until removed by hand.
