# Third-Party Services Dashboard

A class project that connects Claude Code to third-party services through each vendor's official MCP server, downloads their data into `dataExports/`, and searches it from a locally run dashboard website.

All accounts and data in this repository are fictional test data ("Project Atlas"). No real personal data or credentials are stored here.

## Services

| Service | Official MCP server | Owner |
| --- | --- | --- |
| GitHub | `https://api.githubcopilot.com/mcp/` | Group |
| Notion | `https://mcp.notion.com/mcp` | Group |
| Linear | `https://mcp.linear.app/mcp` | TODO: student name |
| Google Calendar | `https://calendarmcp.googleapis.com/mcp/v1` | TODO: student name |
| Google Drive | `https://drivemcp.googleapis.com/mcp/v1` | TODO: student name |

## Repository structure

```
dataExports/      downloaded data, one subfolder per service
.claude/skills/   Claude Code skill for repeatable downloads
webapp/           local dashboard website
docs/             screenshots, PowerPoint, demo video
.mcp.json         MCP server configuration (no secrets)
```

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
