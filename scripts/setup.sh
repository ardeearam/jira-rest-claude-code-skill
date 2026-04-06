#!/usr/bin/env bash
# setup.sh — Collects JIRA credentials and saves to credentials.json
# Run this if credentials.json does not exist yet.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREDS_FILE="$SCRIPT_DIR/../credentials.json"

echo ""
echo "=== JIRA REST Skill — Credentials Setup ==="
echo ""
echo "You will need:"
echo "  1. Your Atlassian base URL (e.g. https://yourcompany.atlassian.net)"
echo "  2. Your Atlassian account email"
echo "  3. An API token from https://id.atlassian.com/manage-profile/security/api-tokens"
echo ""

read -rp "Atlassian base URL (no trailing slash): " jira_base_url
read -rp "Atlassian account email: " jira_email
read -rsp "Atlassian API token (input hidden): " jira_api_token
echo ""

# Validate inputs
if [[ -z "$jira_base_url" || -z "$jira_email" || -z "$jira_api_token" ]]; then
  echo "ERROR: All fields are required. Aborting." >&2
  exit 1
fi

# Strip trailing slash from base URL
jira_base_url="${jira_base_url%/}"

# Write credentials.json with restricted permissions
cat > "$CREDS_FILE" <<EOF
{
  "jira_base_url": "$jira_base_url",
  "jira_email": "$jira_email",
  "jira_api_token": "$jira_api_token"
}
EOF

chmod 600 "$CREDS_FILE"

echo ""
echo "Credentials saved to: $CREDS_FILE"
echo "File permissions set to 600 (owner read/write only)."
echo ""

# Quick connectivity test
echo "Testing connection to JIRA..."
http_status=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "$jira_email:$jira_api_token" \
  "$jira_base_url/rest/api/3/myself")

if [[ "$http_status" == "200" ]]; then
  echo "Connection successful. Setup complete."
else
  echo "WARNING: Connection test returned HTTP $http_status."
  echo "Credentials saved, but verify your URL, email, and token are correct."
fi
