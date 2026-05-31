#!/usr/bin/env python3
"""
Sam's Playground - Issue Poller

Polls GitHub for new open issues. When a new issue is found, returns
JSON on stdout. Sentry mode: also labels and closes stale issues.

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

if not TOKEN:
    print("GITHUB_TOKEN not set", file=sys.stderr)
    sys.exit(1)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"seen_issues": [], "in_progress": {}, "done": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def api(method, endpoint, data=None):
    url = f"{API_BASE}{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
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
    issues = api("GET", f"/repos/{REPO}/issues?state=open&per_page=100")
    if issues is None:
        return []
    # Exclude PRs
    return [i for i in issues if "pull_request" not in i]


def add_label(issue_number, label):
    return api("POST", f"/repos/{REPO}/issues/{issue_number}/labels", [label])


def main():
    state = load_state()

    issues = get_open_issues()
    if not issues:
        return

    new_issues = []
    for issue in issues:
        num = str(issue["number"])
        # If already tracked and not in progress, skip
        if num in state["seen_issues"]:
            continue
        if num in state["in_progress"]:
            continue
        new_issues.append(issue)

    if new_issues:
        for issue in new_issues:
            num = str(issue["number"])
            # Add backlog label to the issue
            add_label(issue["number"], "backlog")
            state["seen_issues"].append(num)

            # Output JSON for the pipeline
            print(json.dumps({
                "type": "new_pbi",
                "issue_number": issue["number"],
                "title": issue["title"],
                "body": issue.get("body", ""),
                "html_url": issue["html_url"],
                "created_at": issue["created_at"],
            }))

        save_state(state)


if __name__ == "__main__":
    main()