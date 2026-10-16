---
name: download-test-data
description: Download the Project Atlas test data from GitHub, Notion and Linear into dataExports/<service>/ as one JSON file per item, skipping items that have not changed, then validate the files. Use when asked to download, refresh, re-export or sync the test data or dataExports.
---

# Download test data

Downloads the Project Atlas test data into `dataExports/` in the format defined in `localStorageFormats.md` (read it first; it is the source of truth for field names). Gmail, Google Calendar and Google Drive are out of scope.

Scripts (run from the project root):

- `python3 .claude/skills/download-test-data/scripts/save_items.py <service> <records.json>` writes one file per record and leaves unchanged files untouched.
- `python3 .claude/skills/download-test-data/scripts/validate.py [service ...]` checks every file.

Write each service's records as a JSON array to a scratch file (not inside the project), then pass that file to `save_items.py`.

## 0. Check access

Use the project's MCP servers from `.mcp.json` (`github`, `notion`, `linear`). If one is not connected or signed in, skip that service, tell the user which one and why, and continue with the others. Never type tokens or passwords; the user sets `GITHUB_PAT` and signs in through `/mcp`.

Confirm each server is signed in as the test account (`rosenthalgroupyrz@gmail.com` / its GitHub login). Notion: `notion-get-self`.

## 1. Skip unchanged items

For each service, first list the items, then compare each listed item's last-changed time with the saved file:

| Service | Listed change time | Saved field |
| --- | --- | --- |
| GitHub | `updated_at` and `pushed_at` | same fields |
| Notion | search result `timestamp` (rounded to the minute) | `last_edited_time`, truncated to the minute |
| Linear | `updatedAt` | `updated_at` |

Only fetch full details (README, page body, issue description) for items that are new or whose time differs. Include only those in the records file. `save_items.py` also refuses to rewrite identical content, so a wasted fetch never changes a file.

## 2. GitHub: repos named `atlas-*`

1. Search repositories owned by the test account with `atlas-` in the name; keep only names that start with `atlas-`. Page through all results.
2. For each repo needing a fetch, get the README from the default branch (try `README.md`, then any `README*` at the root). Decode it to text. If none exists, `readme_text` and `readme_path` are `null`.
3. Build records with the fields in `localStorageFormats.md`. `id` is the repository node ID (`R_...`). Convert all dates to `YYYY-MM-DDTHH:MM:SSZ`.

## 3. Notion: pages about "Atlas" or "Lisbon"

1. Run `notion-search` with query `Atlas`, then `Lisbon`, `page_size` 50, `max_highlight_length` 0. Merge by `id`; keep only `type: page`.
2. For each page needing a fetch, call `notion-fetch` with the page ID.
3. Build the record:
   - `title`: the `title` property (not the fetch title, which has the icon prepended)
   - `icon`, `cover`: from the fetch result (`cover: null` means no cover)
   - `url`: `https://app.notion.com/p/<id without dashes>` (drop `?pvs=...`)
   - `ancestor_path`: contents of `<ancestor-path>` (empty → `[]`)
   - `properties`: the `<properties>` JSON
   - `verification_state`, `workspace` (from `notion-get-self`)
   - `last_edited_time`: `page_last_edited_at`; `content_snapshot_at`: the "as of" time in the fetch text
   - `body_format`: `notion-enhanced-markdown`; `body_markdown`: everything between `<content>` and `</content>`, exactly, with surrounding newlines trimmed
   - Do not add `created_time`; the fetch does not return it.

## 4. Linear: issues in team ATL

1. Find the team whose key is `ATL`. List all its issues, including completed and canceled ones, paging until done.
2. For each issue needing a fetch, get the full issue.
3. Build records with the fields in `localStorageFormats.md`: `id` is the UUID, `identifier` is `ATL-n`, `status` is the state name, `priority` is the 0–4 number, `due_date` is `YYYY-MM-DD` or `null`, `estimate` is a number or `null`. Keep extra fields the server returns (assignee, labels, project, cycle, started/completed/canceled times) using snake_case names. Leave out anything it does not return.

## 5. Save and validate

1. For each service with records: `save_items.py <service> <records.json>`.
2. Run `validate.py`. Fix any failure and re-run until all pass.
3. Report per service: items found, new, updated, unchanged, skipped services and why. Do not commit unless the user asks.
