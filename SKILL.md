---
name: jira-rest
description: Access and modify JIRA tickets via REST API. Use when the user mentions JIRA, Jira tickets, or asks to read/update/comment on/transition a ticket.
---

You are equipped to interact with JIRA using its REST API via a local Python helper. No external packages required -- stdlib only.

---

## !! CRITICAL RULES — READ THIS BEFORE ANYTHING ELSE !!

**YOU MUST USE `AskUserQuestion` TO COLLECT ALL INPUT FROM THE USER.**

**NEVER assume, guess, or infer values for URLs, emails, tokens, passwords, ticket IDs, or any other user-provided data.**

**ALWAYS use `AskUserQuestion`. ALWAYS. ALWAYS. ALWAYS.**

If you do not use `AskUserQuestion` and instead make assumptions or read from context, **YOU ARE DOING IT WRONG.** Stop. Go back. Ask explicitly using `AskUserQuestion`.

This is non-negotiable. No exceptions.

---

**YOU ARE THE WORKER. NEVER DELEGATE TASKS BACK TO THE USER.**

Do not tell the user to run scripts. Do not say "run this command". Do not instruct the user to open a terminal.

You run all scripts. You execute all commands. You do the work.

The only thing you ask the user for is information you cannot know: credentials, passwords, ticket IDs, JQL queries. Everything else — you handle.

---

**NEVER READ, USE, OR REFERENCE `credentials.json` (PLAIN, UNENCRYPTED).**

If a plain `credentials.json` exists, ignore it entirely. It is a stale artifact and may contain credentials in plaintext.

The **only** valid credentials source is `credentials.json.enc` (AES-256 encrypted). If it is not found, run the setup flow yourself.

---

## Setup

**Credentials file:** `~/.claude/skills/jira-rest/credentials.json.enc`
**Scripts:** `~/.claude/skills/jira-rest/scripts/`

---

## Step 1 — Check credentials

Run this yourself:

```bash
python3 -c "from pathlib import Path; print('EXISTS' if Path('~/.claude/skills/jira-rest/credentials.json.enc').expanduser().exists() else 'MISSING')"
```

### If MISSING — collect credentials and run setup

Ask for each value one at a time using `AskUserQuestion`:

**Question 1:** Ask for their Atlassian base URL.
> "What is your Atlassian base URL? (e.g. https://yourcompany.atlassian.net)"

**Question 2:** Ask for their Atlassian email.
> "What is the email address on your Atlassian account?"

**Question 3:** Ask for their Atlassian API token.
> "Please enter your Atlassian API token. You can generate one at https://id.atlassian.com/manage-profile/security/api-tokens — it will not be stored in plaintext."

**Question 4:** Ask for an encryption password.
> "Choose a password to encrypt your JIRA credentials. You will need to enter this each time a JIRA operation runs. It is never stored anywhere — if you forget it, you will need to re-enter your API token to re-encrypt."

Then run setup yourself (never show or log the token or password):

```bash
JIRA_PASSWORD="<PASSWORD>" JIRA_API_TOKEN="<API_TOKEN>" python3 ~/.claude/skills/jira-rest/scripts/setup.py "<BASE_URL>" "<EMAIL>"
```

### If EXISTS — proceed directly

Use `AskUserQuestion` to ask for the password before every API call:
> "Enter your JIRA credentials password to continue."

---

## Step 2 — Run API commands

Before every `jira.py` call, ask for the password via `AskUserQuestion`:
> "Enter your JIRA credentials password to continue."

Then run commands yourself:

```bash
JIRA_PASSWORD="<PASSWORD>" python3 ~/.claude/skills/jira-rest/scripts/jira.py <command> [args...]
```

### Available commands

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

### Example invocations (you run these, not the user)

```bash
# Verify setup
JIRA_PASSWORD="<PW>" python3 ~/.claude/skills/jira-rest/scripts/jira.py myself

# Get a ticket
JIRA_PASSWORD="<PW>" python3 ~/.claude/skills/jira-rest/scripts/jira.py get PROJ-1234

# Search open tickets
JIRA_PASSWORD="<PW>" python3 ~/.claude/skills/jira-rest/scripts/jira.py search "project = PROJ AND status != Done ORDER BY updated DESC"

# Add a comment
JIRA_PASSWORD="<PW>" python3 ~/.claude/skills/jira-rest/scripts/jira.py add-comment PROJ-1234 "Investigated -- root cause is in the auth middleware."

# List transitions, then execute one
JIRA_PASSWORD="<PW>" python3 ~/.claude/skills/jira-rest/scripts/jira.py transitions PROJ-1234
JIRA_PASSWORD="<PW>" python3 ~/.claude/skills/jira-rest/scripts/jira.py transition PROJ-1234 31
```

---

## Notes

- Uses JIRA REST API v3 (`/rest/api/3`).
- `update` handles simple string fields. For array fields (e.g. `labels`) or status changes, use `transition` instead.
- `credentials.json.enc` is excluded from git via `.gitignore`. The password is never stored.
- Never print, log, or display the API token, the encryption password, or decrypted credential values.
