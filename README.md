# Third-Party Services Dashboard

A class project that connects Claude Code to third-party services through each vendor's official MCP server, downloads their data into `dataExports/`, and searches it from a locally run dashboard website.

All accounts and data in this repository are fictional test data ("Project Atlas"). No real personal data or credentials are stored here.

## Services

| Service | Official MCP server | Owner |
| --- | --- | --- |
| GitHub | `https://api.githubcopilot.com/mcp/` | Group |
| Notion | `https://mcp.notion.com/mcp` | Group |
| Linear | `https://mcp.linear.app/mcp` | TODO: student name |
| Todoist | `https://ai.todoist.net/mcp` | TODO: student name |
| Asana | `https://mcp.asana.com/v2/mcp` | TODO: student name |

## Repository structure

```
dataExports/      downloaded data, one subfolder per service
.claude/skills/   Claude Code skill for repeatable downloads
webapp/           local dashboard website
docs/             screenshots, PowerPoint, demo video
.mcp.json         MCP server configuration (no secrets)
```

## Running the dashboard

Requires Python 3.9+ and nothing else (standard library only, no install step).

```
python3 webapp/server.py
```

Then open <http://127.0.0.1:8000/>. Use `--port 8080` to change the port, and Ctrl+C to stop.

- The dashboard reads only the JSON files in `dataExports/` and makes no live API calls. Every service subfolder is picked up automatically, and new files appear after clicking **Reload data**, with no restart needed.
- Choose a service or **All services**, then type to search titles, bodies and metadata. Every word must match. Put a phrase in quotes (`"route plan"`) to match it exactly.
- Files that can't be read (invalid JSON, not a JSON object) are listed in a warning and skipped. The other results still show.
- The search is saved in the URL, for example `http://127.0.0.1:8000/?q=Atlas&service=linear`.

## TODO

- [ ] Setup: credentials and authentication for each service
- [ ] Test data: 10+ items per service
- [ ] Data exports and `localStorageFormats.md`
- [ ] Claude Code download skill
- [ ] Dashboard: how to run and how to search
- [ ] Group member contributions
- [ ] Limitations

## Limitations

**Gmail is skipped, with the instructor's permission.** Google's official Gmail MCP server (`https://gmailmcp.googleapis.com/mcp/v1`) only works for Google Cloud projects enrolled in the Google Workspace Developer Preview Program, and that enrollment requires a Google Workspace account. Our test account is a regular Gmail address, so the enrollment form rejects it. We got as far as signing in and loading the server's 23 tools, but every tool call returned "Access to this tool requires that your Google Cloud project is enrolled in the Google Workspace Developer Preview Program."

**Google Calendar and Google Drive were replaced by Todoist and Asana.** Google's official Calendar and Drive MCP servers have the same Developer Preview requirement as Gmail, so they could not be used with our test account.
