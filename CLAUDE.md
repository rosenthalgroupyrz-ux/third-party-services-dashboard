# Project rules for Claude

This repository is **public**. Everything in it must be fictional test data.

## Accounts

- Use only the group's **test accounts**:
  - GitHub: `rosenthalgroupyrz-ux`
  - Notion, Linear and other services: `rosenthalgroupyrz@gmail.com`
- **Never use the `gh` CLI or any other locally signed-in GitHub login.** They may belong to a personal account. Reach GitHub only through the `github` MCP server in `.mcp.json`, which authenticates as the test account with the `GITHUB_PAT` environment variable.
- If a task needs the GitHub test data and `GITHUB_PAT` is empty, stop that task and say so. Do not fall back to another GitHub account.
- `GITHUB_PAT` is only needed for downloading the GitHub test data. Group members working on other services (Todoist, Asana) do not need it: the `github` server failing to connect on their machine is expected, and they should carry on with their own service. Pushing to this repo uses each member's own GitHub login, not this token.
- If any service turns out to be connected to an account other than the test accounts above, stop and report it.

## Secrets and personal data

- Never write tokens, API keys, OAuth client IDs or secrets, or passwords into any file.
- Never write a group member's personal username, email address or name into any file unless they asked for it (for example, the README's contributions section).
- Before any commit, scan staged files for secrets and personal data.

## Services

- Gmail is skipped, with the instructor's permission (see README, Limitations).
- Downloads go in `dataExports/<service>/` and must follow `localStorageFormats.md`. Use the `download-test-data` skill.
