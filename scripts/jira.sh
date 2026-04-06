#!/usr/bin/env bash
# jira.sh — JIRA REST API helper
# Usage: jira.sh <command> [args...]
#
# Commands:
#   get <TICKET_ID>                      Get ticket details
#   get-comments <TICKET_ID>             List comments on a ticket
#   search "<JQL>"                       Search tickets using JQL
#   update <TICKET_ID> <field> <value>   Update a single field (string value)
#   add-comment <TICKET_ID> "<text>"     Add a comment to a ticket
#   transitions <TICKET_ID>             List available transitions
#   transition <TICKET_ID> <ID>          Execute a transition by its ID
#   assign <TICKET_ID> <ACCOUNT_ID>      Assign ticket to a user
#   myself                               Get current user info

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREDS_FILE="$SCRIPT_DIR/../credentials.json"

# ── Credential loading ──────────────────────────────────────────────────────

if [[ ! -f "$CREDS_FILE" ]]; then
  echo "ERROR: credentials.json not found at $CREDS_FILE" >&2
  echo "Run setup.sh first: bash $SCRIPT_DIR/setup.sh" >&2
  exit 1
fi

jira_base_url=$(python3 -c "import json,sys; d=json.load(open('$CREDS_FILE')); print(d['jira_base_url'])")
jira_email=$(python3 -c "import json,sys; d=json.load(open('$CREDS_FILE')); print(d['jira_email'])")
jira_api_token=$(python3 -c "import json,sys; d=json.load(open('$CREDS_FILE')); print(d['jira_api_token'])")

AUTH="$jira_email:$jira_api_token"
BASE="$jira_base_url/rest/api/3"

# ── Helper ──────────────────────────────────────────────────────────────────

jira_get() {
  local path="$1"
  curl -s -u "$AUTH" \
    -H "Accept: application/json" \
    "$BASE$path"
}

jira_post() {
  local path="$1"
  local body="$2"
  curl -s -u "$AUTH" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -X POST \
    -d "$body" \
    "$BASE$path"
}

jira_put() {
  local path="$1"
  local body="$2"
  curl -s -u "$AUTH" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -X PUT \
    -d "$body" \
    "$BASE$path"
}

# ── Commands ────────────────────────────────────────────────────────────────

cmd="${1:-}"

case "$cmd" in

  get)
    ticket="${2:?Usage: jira.sh get <TICKET_ID>}"
    jira_get "/issue/$ticket" | python3 -m json.tool
    ;;

  get-comments)
    ticket="${2:?Usage: jira.sh get-comments <TICKET_ID>}"
    jira_get "/issue/$ticket/comment" | python3 -m json.tool
    ;;

  search)
    jql="${2:?Usage: jira.sh search \"<JQL>\"}"
    max="${3:-20}"
    encoded_jql=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$jql")
    jira_get "/search?jql=$encoded_jql&maxResults=$max&fields=summary,status,assignee,priority,issuetype" \
      | python3 -m json.tool
    ;;

  update)
    ticket="${2:?Usage: jira.sh update <TICKET_ID> <field> <value>}"
    field="${3:?Missing field name}"
    value="${4:?Missing field value}"
    body=$(python3 -c "
import json, sys
field = sys.argv[1]
value = sys.argv[2]
print(json.dumps({'fields': {field: value}}))" "$field" "$value")
    result=$(jira_put "/issue/$ticket" "$body")
    if [[ -z "$result" ]]; then
      echo "Update successful (HTTP 204 No Content)."
    else
      echo "$result" | python3 -m json.tool
    fi
    ;;

  add-comment)
    ticket="${2:?Usage: jira.sh add-comment <TICKET_ID> \"<text>\"}"
    text="${3:?Missing comment text}"
    body=$(python3 -c "
import json, sys
text = sys.argv[1]
payload = {
  'body': {
    'type': 'doc',
    'version': 1,
    'content': [
      {
        'type': 'paragraph',
        'content': [{'type': 'text', 'text': text}]
      }
    ]
  }
}
print(json.dumps(payload))" "$text")
    jira_post "/issue/$ticket/comment" "$body" | python3 -m json.tool
    ;;

  transitions)
    ticket="${2:?Usage: jira.sh transitions <TICKET_ID>}"
    jira_get "/issue/$ticket/transitions" | python3 -m json.tool
    ;;

  transition)
    ticket="${2:?Usage: jira.sh transition <TICKET_ID> <TRANSITION_ID>}"
    transition_id="${3:?Missing transition ID}"
    body=$(python3 -c "import json,sys; print(json.dumps({'transition': {'id': sys.argv[1]}}))" "$transition_id")
    result=$(jira_post "/issue/$ticket/transitions" "$body")
    if [[ -z "$result" ]]; then
      echo "Transition successful."
    else
      echo "$result" | python3 -m json.tool
    fi
    ;;

  assign)
    ticket="${2:?Usage: jira.sh assign <TICKET_ID> <ACCOUNT_ID>}"
    account_id="${3:?Missing account ID}"
    body=$(python3 -c "import json,sys; print(json.dumps({'accountId': sys.argv[1]}))" "$account_id")
    result=$(jira_put "/issue/$ticket/assignee" "$body")
    if [[ -z "$result" ]]; then
      echo "Assigned successfully."
    else
      echo "$result" | python3 -m json.tool
    fi
    ;;

  myself)
    jira_get "/myself" | python3 -m json.tool
    ;;

  *)
    echo "Usage: jira.sh <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  get <TICKET_ID>                     Get ticket details"
    echo "  get-comments <TICKET_ID>            List comments on a ticket"
    echo "  search \"<JQL>\"                      Search tickets using JQL"
    echo "  update <TICKET_ID> <field> <value>  Update a single string field"
    echo "  add-comment <TICKET_ID> \"<text>\"    Add a comment"
    echo "  transitions <TICKET_ID>             List available transitions"
    echo "  transition <TICKET_ID> <ID>         Execute a transition"
    echo "  assign <TICKET_ID> <ACCOUNT_ID>     Assign ticket to user"
    echo "  myself                              Get current user info"
    exit 1
    ;;
esac
