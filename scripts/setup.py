#!/usr/bin/env python3
"""
setup.py -- Collects JIRA credentials and saves them to credentials.json.
Run this if credentials.json does not exist yet.
"""

import getpass
import json
import stat
import sys
import urllib.error
import urllib.request
from base64 import b64encode
from pathlib import Path

CREDS_FILE = Path(__file__).parent.parent / "credentials.json"


def test_connection(base_url, email, token):
    auth = b64encode(f"{email}:{token}".encode()).decode()
    req = urllib.request.Request(
        f"{base_url}/rest/api/3/myself",
        headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return True, data.get("displayName", "unknown")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} {e.reason}"
    except Exception as e:
        return False, str(e)


def main():
    print()
    print("=== JIRA REST Skill -- Credentials Setup ===")
    print()
    print("You will need:")
    print("  1. Your Atlassian base URL  (e.g. https://yourcompany.atlassian.net)")
    print("  2. Your Atlassian account email")
    print("  3. An API token from https://id.atlassian.com/manage-profile/security/api-tokens")
    print()

    base_url = input("Atlassian base URL (no trailing slash): ").strip().rstrip("/")
    email = input("Atlassian account email: ").strip()
    token = getpass.getpass("Atlassian API token (input hidden): ").strip()

    if not all([base_url, email, token]):
        sys.exit("ERROR: All fields are required. Aborting.")

    creds = {
        "jira_base_url": base_url,
        "jira_email": email,
        "jira_api_token": token,
    }

    CREDS_FILE.write_text(json.dumps(creds, indent=2) + "\n")
    # chmod 600 -- owner read/write only
    CREDS_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)

    print()
    print(f"Credentials saved to: {CREDS_FILE}")
    print("File permissions set to 600 (owner read/write only).")
    print()

    print("Testing connection to JIRA...")
    ok, detail = test_connection(base_url, email, token)
    if ok:
        print(f"Connection successful. Authenticated as: {detail}")
    else:
        print(f"WARNING: Connection test failed -- {detail}")
        print("Credentials saved, but verify your URL, email, and token.")


if __name__ == "__main__":
    main()
