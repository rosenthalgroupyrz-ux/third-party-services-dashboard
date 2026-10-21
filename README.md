# Third-Party Services Dashboard

A class project that connects Claude Code to five cloud services through each vendor's official MCP server, downloads their data to this computer in a documented format, and searches all of it from a locally run dashboard website.

All accounts and data in this repository are fictional test data for **Project Atlas**: the made-up company Northwind Logistics opening a delivery hub in Lisbon. The same fictional people (Joe Smith, Maria Lopez, Priya Natarajan, Daniel Okafor) appear in every service, so one search returns connected results. No real personal data or credentials are stored here.

## How it works

```
Cloud services  →  official MCP servers  →  Claude Code + download skill  →  dataExports/  →  local dashboard
```

1. **Connect.** `.mcp.json` points Claude Code at each vendor's hosted MCP server.
2. **Download.** The project skill `download-test-data` fetches every item with its metadata and saves one JSON file per item in `dataExports/<service>/`.
3. **Search.** `webapp/` is a small local website that reads those files (never the live services) and searches one service or all of them at once.

## Services and contributions

| Service | Official MCP server | Test items | Owner |
| --- | --- | --- | --- |
| GitHub | `https://api.githubcopilot.com/mcp/` | 10 private `atlas-*` repos | Yoni Pomerantz |
| Notion | `https://mcp.notion.com/mcp` | 10 pages | Yoni Pomerantz |
| Linear | `https://mcp.linear.app/mcp` | 10 issues (ATL-5 to ATL-14) | Yoni Pomerantz |
| Asana | `https://mcp.asana.com/v2/mcp` | 12 tasks | Rafi Cornick |
| Todoist | `https://ai.todoist.net/mcp` | 12 tasks | Zachary Sicklick |

GitHub and Notion are required for every group; each student owns one extra service.

- **Yoni Pomerantz:** test data, MCP setup and downloads for GitHub, Notion and Linear; `localStorageFormats.md`; the `download-test-data` skill; the dashboard; this repository.
- **Rafi Cornick:** Asana test account and data, the Asana MCP app setup, extending the skill and format doc for Asana, the Asana export.
- **Zachary Sicklick:** Todoist test account and data, extending the skill and format doc for Todoist, the Todoist export, the presentation.

## Repository structure

```
dataExports/                       downloaded data, one subfolder per service
  github/  notion/  linear/  asana/  todoist/
.claude/skills/download-test-data/ Claude Code skill for repeatable downloads
  SKILL.md                         step-by-step instructions Claude follows
  scripts/save_items.py            writes one file per item, skips unchanged ones
  scripts/validate.py              checks every file against the format
localStorageFormats.md             the storage format for each service
webapp/                            local dashboard website (Python standard library)
docs/                              screenshots, presentation, demo video
.mcp.json                          MCP server configuration (no secrets)
CLAUDE.md                          project rules Claude Code follows (test accounts only, no secrets)
```

## Local storage format

Every item is one JSON file in `dataExports/<service>/`, named by the item's stable ID from the service (for example `dataExports/linear/<issue-id>.json`). Each file keeps the item's content (README text, page text, description) and its metadata (IDs, URLs, status, priority, due dates, timestamps in ISO 8601 UTC). Missing fields are left out, never invented. The full format for each service, plus known limitations, is in [localStorageFormats.md](localStorageFormats.md).

## Setting up credentials safely

Nothing secret is stored in this repository. Each person signs in on their own computer:

- **Notion, Linear, Todoist:** run `claude` in this folder, type `/mcp`, choose the server, then **Authenticate**, and sign in with the test account in the browser.
- **GitHub:** the official server needs a personal access token for the test account (classic token, `repo` scope). Store it in the macOS Keychain and load it into the `GITHUB_PAT` environment variable, which `.mcp.json` reads:

  ```bash
  security add-generic-password -U -a "$USER" -s GITHUB_PAT -w "$(pbpaste)"
  echo 'export GITHUB_PAT="$(security find-generic-password -a "$USER" -s GITHUB_PAT -w 2>/dev/null)"' >> ~/.zshrc
  ```

  Copy the token before the first command; open a new terminal afterwards. Only the person downloading GitHub data needs this.
- **Asana:** the server requires your own OAuth app. Create an MCP app in Asana's developer console with the redirect URL `http://localhost:8080/callback`, then add the server with your client ID (the secret is prompted for and stored outside the repo):

  ```bash
  claude mcp add --transport http --scope local --client-id YOUR_CLIENT_ID --client-secret --callback-port 8080 asana https://mcp.asana.com/v2/mcp
  ```

## Downloading data with the skill

Open Claude Code in this folder and ask:

```
download any new data using the download-test-data skill
```

Claude Code finds the project skill in `.claude/skills/`, checks that each service is signed in as the test account, downloads new or changed items into `dataExports/`, skips unchanged ones, and validates the result. It was tested in a fresh conversation after `/clear`: it downloaded 1 new GitHub repo, skipped the 33 unchanged items, and every file passed validation.

## Running the dashboard

Requires Python 3.9+ and nothing else (standard library only, no install step).

```
python3 webapp/server.py
```

Then open <http://127.0.0.1:8000/>. Use `--port 8080` to change the port, and Ctrl+C to stop.

- The dashboard reads only the JSON files in `dataExports/` and makes no live API calls. Every service subfolder is picked up automatically, and new files appear after clicking **Reload data**, with no restart needed.
- Choose a service or **All services**, then type to search titles, bodies and metadata. Every word must match. Put a phrase in quotes (`"route plan"`) to match it exactly.
- Each result shows its source service as a colored badge, a highlighted excerpt, its ID, key metadata, and a link to the original.
- Files that can't be read (invalid JSON, not a JSON object) are listed in a warning and skipped. The other results still show.
- The search is saved in the URL, for example `http://127.0.0.1:8000/?q=Atlas&service=linear`. Try `?q=Joe%20Smith` to see results from all five services.

## Running the tests

Check every exported file against the documented format:

```bash
python3 .claude/skills/download-test-data/scripts/validate.py
```

It checks required fields, file names, timestamp format and duplicate IDs, and prints the number of files and invalid files per service. Pass service names to check only some, for example `validate.py github linear`.

## Presentation and demo

- Presentation: [docs/Atlas-Data-Dashboard.pptx](docs/Atlas-Data-Dashboard.pptx) (PDF copy: [docs/Atlas-Data-Dashboard.pdf](docs/Atlas-Data-Dashboard.pdf))
- Screenshots: `docs/<service>-original.png` (the test content in each service) and `docs/<service>-dashboard.png` (the same content in the dashboard), plus `docs/cross-service-search.png`
- Demo video: TODO, add link

## Limitations

- **Gmail is skipped, with the instructor's permission.** Google's official Gmail MCP server (`https://gmailmcp.googleapis.com/mcp/v1`) only works for Google Cloud projects enrolled in the Google Workspace Developer Preview Program, and that enrollment requires a Google Workspace account. Our test account is a regular Gmail address, so the enrollment form rejects it. We got as far as signing in and loading the server's 23 tools, but every tool call returned "Access to this tool requires that your Google Cloud project is enrolled in the Google Workspace Developer Preview Program."
- **Google Calendar and Google Drive were replaced by Todoist and Asana.** Google's official Calendar and Drive MCP servers have the same Developer Preview requirement as Gmail.
- **GitHub** uses a personal access token, because its official server does not support Claude Code's browser sign-in. **Asana** needs a self-created OAuth app for the same reason.
- **Linear** also exports its 4 default onboarding issues (ATL-1 to ATL-4), so its folder has 14 files.
- Service-specific gaps (fields a server does not return, such as Notion's page creation time or Todoist's change time) are listed per service in `localStorageFormats.md`.
