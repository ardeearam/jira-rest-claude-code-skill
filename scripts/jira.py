#!/usr/bin/env python3
"""
jira.py -- JIRA REST API helper (stdlib only, no pip required)

Usage:
    python3 jira.py <command> [args...]

Commands:
    myself                               Get current authenticated user
    get <TICKET_ID>                      Get ticket details
    get-comments <TICKET_ID>             List comments on a ticket
    search "<JQL>" [max_results]         Search tickets using JQL (default: 20)
    update <TICKET_ID> <field> <value>   Update a single string field
    add-comment <TICKET_ID> "<text>"     Add a comment to a ticket
    transitions <TICKET_ID>             List available status transitions
    transition <TICKET_ID> <ID>          Execute a transition by its ID
    assign <TICKET_ID> <ACCOUNT_ID>      Assign ticket to a user
"""

import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from base64 import b64encode

# ── Credentials ──────────────────────────────────────────────────────────────

CREDS_FILE = Path(__file__).parent.parent / "credentials.json"


def load_credentials():
    if not CREDS_FILE.exists():
        sys.exit(
            f"ERROR: credentials.json not found at {CREDS_FILE}\n"
            f"Run setup first: python3 {Path(__file__).parent / 'setup.py'}"
        )
    with CREDS_FILE.open() as f:
        creds = json.load(f)
    for key in ("jira_base_url", "jira_email", "jira_api_token"):
        if not creds.get(key):
            sys.exit(f"ERROR: Missing '{key}' in credentials.json")
    return creds


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def make_auth_header(email, token):
    raw = f"{email}:{token}".encode()
    return {"Authorization": f"Basic {b64encode(raw).decode()}"}


def request(method, url, auth_header, body=None):
    headers = {**auth_header, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        sys.exit(f"HTTP {e.code} {e.reason}: {body_text}")


def get(base_url, path, auth):
    return request("GET", f"{base_url}{path}", auth)


def post(base_url, path, auth, body):
    return request("POST", f"{base_url}{path}", auth, body)


def put(base_url, path, auth, body):
    return request("PUT", f"{base_url}{path}", auth, body)


def print_json(data):
    if data is None:
        print("OK (no content)")
    else:
        print(json.dumps(data, indent=2))


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_myself(base_url, auth, _args):
    print_json(get(base_url, "/rest/api/3/myself", auth))


def cmd_get(base_url, auth, args):
    if not args:
        sys.exit("Usage: jira.py get <TICKET_ID>")
    print_json(get(base_url, f"/rest/api/3/issue/{args[0]}", auth))


def cmd_get_comments(base_url, auth, args):
    if not args:
        sys.exit("Usage: jira.py get-comments <TICKET_ID>")
    print_json(get(base_url, f"/rest/api/3/issue/{args[0]}/comment", auth))


def cmd_search(base_url, auth, args):
    if not args:
        sys.exit('Usage: jira.py search "<JQL>" [max_results]')
    jql = args[0]
    max_results = int(args[1]) if len(args) > 1 else 20
    params = urllib.parse.urlencode({
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,status,assignee,priority,issuetype",
    })
    print_json(get(base_url, f"/rest/api/3/search/jql?{params}", auth))


def cmd_update(base_url, auth, args):
    if len(args) < 3:
        sys.exit("Usage: jira.py update <TICKET_ID> <field> <value>")
    ticket, field, value = args[0], args[1], args[2]
    result = put(base_url, f"/rest/api/3/issue/{ticket}", auth, {"fields": {field: value}})
    print_json(result) if result else print("Update successful.")


def cmd_add_comment(base_url, auth, args):
    if len(args) < 2:
        sys.exit('Usage: jira.py add-comment <TICKET_ID> "<text>"')
    ticket, text = args[0], args[1]
    body = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]}
            ],
        }
    }
    print_json(post(base_url, f"/rest/api/3/issue/{ticket}/comment", auth, body))


def cmd_transitions(base_url, auth, args):
    if not args:
        sys.exit("Usage: jira.py transitions <TICKET_ID>")
    data = get(base_url, f"/rest/api/3/issue/{args[0]}/transitions", auth)
    # Print a readable summary alongside the raw JSON
    if data and "transitions" in data:
        print(f"{'ID':<6}  {'Name'}")
        print("-" * 40)
        for t in data["transitions"]:
            print(f"{t['id']:<6}  {t['name']}")
        print()
    print_json(data)


def cmd_transition(base_url, auth, args):
    if len(args) < 2:
        sys.exit("Usage: jira.py transition <TICKET_ID> <TRANSITION_ID>")
    ticket, transition_id = args[0], args[1]
    result = post(
        base_url,
        f"/rest/api/3/issue/{ticket}/transitions",
        auth,
        {"transition": {"id": transition_id}},
    )
    print_json(result) if result else print("Transition successful.")


def cmd_assign(base_url, auth, args):
    if len(args) < 2:
        sys.exit("Usage: jira.py assign <TICKET_ID> <ACCOUNT_ID>")
    ticket, account_id = args[0], args[1]
    result = put(
        base_url, f"/rest/api/3/issue/{ticket}/assignee", auth, {"accountId": account_id}
    )
    print_json(result) if result else print("Assigned successfully.")


# ── Dispatch ─────────────────────────────────────────────────────────────────

COMMANDS = {
    "myself":       cmd_myself,
    "get":          cmd_get,
    "get-comments": cmd_get_comments,
    "search":       cmd_search,
    "update":       cmd_update,
    "add-comment":  cmd_add_comment,
    "transitions":  cmd_transitions,
    "transition":   cmd_transition,
    "assign":       cmd_assign,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)

    creds = load_credentials()
    base_url = creds["jira_base_url"].rstrip("/")
    auth = make_auth_header(creds["jira_email"], creds["jira_api_token"])

    command = sys.argv[1]
    args = sys.argv[2:]
    COMMANDS[command](base_url, auth, args)


if __name__ == "__main__":
    main()
