#!/usr/bin/env python3
"""
Sam's Playground - Issue Poller

Polls GitHub for new open issues on the openclaw-website repo.
Tracks seen issues in state.json. When a new issue is found, triggers
a system event so Sam picks it up.

Usage: python3 poll_issues.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

REPO = "EricManintveld/openclaw-website"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
STATE_FILE = os.path.join(os.path.dirname(__file__), "pipeline_state.json")
API_BASE = "https://api.github.com"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"seen_issues": [], "in_progress": {}, "done": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def api_request(endpoint):
    url = f"{API_BASE}{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "Sam-Playground-Bot")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API error: {e.code} {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return None


def get_open_issues():
    """Get open issues, excluding PRs (issues with pull_request field)."""
    issues = api_request(f"/repos/{REPO}/issues?state=open&per_page=100")
    if issues is None:
        return []
    return [i for i in issues if "pull_request" not in i]


def format_for_system_event(issue):
    """Format an issue into a system event message."""
    return json.dumps({
        "type": "new_pbi",
        "issue_number": issue["number"],
        "title": issue["title"],
        "body": issue.get("body", ""),
        "html_url": issue["html_url"],
        "created_at": issue["created_at"],
    })


def main():
    state = load_state()

    issues = get_open_issues()
    if not issues:
        return

    new_issues = []
    for issue in issues:
        num = str(issue["number"])
        if num not in state["seen_issues"] and num not in state["in_progress"]:
            new_issues.append(issue)

    if new_issues:
        print(f"Found {len(new_issues)} new issue(s)")
        for issue in new_issues:
            print(format_for_system_event(issue))
            state["seen_issues"].append(str(issue["number"]))

        save_state(state)
    else:
        # Quiet exit when nothing new
        pass


if __name__ == "__main__":
    main()