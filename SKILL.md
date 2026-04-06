---
name: jira-rest
description: Access and modify JIRA tickets via REST API. Use when the user mentions JIRA, Jira tickets, or asks to read/update/comment on/transition a ticket.
---

You are equipped to interact with JIRA using its REST API via a local Python helper. No external packages required -- stdlib only.

## Setup

**Credentials file:** `~/.claude/skills/jira-rest/credentials.json`
**Helper:** `~/.claude/skills/jira-rest/scripts/jira.py`

### Step 1 -- Check credentials

Before any JIRA operation, verify credentials exist:

```bash
python3 -c "from pathlib import Path; print('EXISTS' if Path('~/.claude/skills/jira-rest/credentials.json').expanduser().exists() else 'MISSING')"
```

If **MISSING**, run the interactive setup:

```bash
python3 ~/.claude/skills/jira-rest/scripts/setup.py
```

The setup script prompts for:
- Atlassian base URL (e.g. `https://yourcompany.atlassian.net`)
- Atlassian account email
- API token (from https://id.atlassian.com/manage-profile/security/api-tokens)

Credentials are saved to `credentials.json` with permissions `600`. Do **not** read or display the API token.

### Step 2 -- Run commands

```bash
python3 ~/.claude/skills/jira-rest/scripts/jira.py <command> [args...]
```

## Available Commands

| Command | Description |
|---|---|
| `myself` | Verify authenticated user |
| `get <TICKET_ID>` | Fetch full ticket details |
| `get-comments <TICKET_ID>` | List comments |
| `search "<JQL>" [max]` | Search using JQL (default max: 20) |
| `update <TICKET_ID> <field> <value>` | Update a simple string field |
| `add-comment <TICKET_ID> "<text>"` | Post a comment |
| `transitions <TICKET_ID>` | List valid status transitions with IDs |
| `transition <TICKET_ID> <ID>` | Move ticket to a new status |
| `assign <TICKET_ID> <ACCOUNT_ID>` | Assign ticket to a team member |

## Usage Examples

```bash
# Verify setup
python3 ~/.claude/skills/jira-rest/scripts/jira.py myself

# Get a ticket
python3 ~/.claude/skills/jira-rest/scripts/jira.py get PROJ-1234

# Search open tickets
python3 ~/.claude/skills/jira-rest/scripts/jira.py search "project = PROJ AND status != Done ORDER BY updated DESC"

# Add a comment
python3 ~/.claude/skills/jira-rest/scripts/jira.py add-comment PROJ-1234 "Investigated -- root cause is in the auth middleware."

# List transitions, then execute one
python3 ~/.claude/skills/jira-rest/scripts/jira.py transitions PROJ-1234
python3 ~/.claude/skills/jira-rest/scripts/jira.py transition PROJ-1234 31
```

## Notes

- Uses JIRA REST API v3 (`/rest/api/3`).
- `update` handles simple string fields. For array fields (e.g. `labels`) or status changes, use `transition` instead.
- Never print or log the API token. Never include credential values in PRs, commits, or shared docs.
- `credentials.json` is excluded from git via `.gitignore`.
