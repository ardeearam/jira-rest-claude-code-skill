#!/usr/bin/env python3
"""
setup.py -- Save JIRA/Atlassian credentials encrypted to credentials.json.enc.

Usage:
    JIRA_PASSWORD='your-password' JIRA_API_TOKEN='your-token' python3 setup.py <base_url> <email>

Arguments:
    base_url   Atlassian base URL (e.g. https://yourcompany.atlassian.net)
    email      Atlassian account email

Environment variables:
    JIRA_API_TOKEN   Atlassian API token (never passed as CLI arg to avoid process-list exposure)
    JIRA_PASSWORD    Encryption password (never stored — required on every run)

If the password is lost, re-run this script with fresh credentials to re-encrypt.
"""

import json
import os
import stat
import subprocess
import sys
import urllib.error
import urllib.request
from base64 import b64encode
from pathlib import Path

ENC_FILE = Path(__file__).parent.parent / "credentials.json.enc"


def _get_password():
    pw = os.environ.get("JIRA_PASSWORD", "")
    if not pw:
        sys.exit(
            "ERROR: JIRA_PASSWORD environment variable not set.\n"
            "Prepend it to the command: JIRA_PASSWORD='...' JIRA_API_TOKEN='...' python3 setup.py ..."
        )
    return pw


def _get_api_token():
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not token:
        sys.exit(
            "ERROR: JIRA_API_TOKEN environment variable not set.\n"
            "Prepend it to the command: JIRA_PASSWORD='...' JIRA_API_TOKEN='...' python3 setup.py ..."
        )
    return token


def save_credentials(creds):
    pw = _get_password()
    ENC_FILE.parent.mkdir(parents=True, exist_ok=True)
    json_bytes = (json.dumps(creds, indent=2) + "\n").encode()
    env = os.environ.copy()
    env["_JIRA_PW"] = pw
    result = subprocess.run(
        [
            "openssl", "enc", "-aes-256-cbc", "-pbkdf2",
            "-out", str(ENC_FILE),
            "-pass", "env:_JIRA_PW",
        ],
        input=json_bytes,
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        sys.exit(f"ERROR: Encryption failed.\n{result.stderr.decode().strip()}")
    ENC_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


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
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    base_url = sys.argv[1].strip().rstrip("/")
    email = sys.argv[2].strip()
    api_token = _get_api_token()

    print("Testing connection to JIRA...")
    ok, detail = test_connection(base_url, email, api_token)
    if ok:
        print(f"Connection successful. Authenticated as: {detail}")
    else:
        print(f"WARNING: Connection test failed -- {detail}")
        print("Saving credentials anyway, but verify your URL, email, and token.")

    creds = {
        "jira_base_url": base_url,
        "jira_email": email,
        "jira_api_token": api_token,
    }

    save_credentials(creds)

    print(f"Credentials encrypted and saved to: {ENC_FILE}")
    print("File permissions set to 600 (owner read/write only).")
    print("The password is NOT stored. You will need it for every JIRA operation.")


if __name__ == "__main__":
    main()
