#!/usr/bin/env python3
"""
Sam's Playground - Pipeline Manager

Handles the BOARD.md kanban lifecycle:
  - Moves items between columns (Backlog → In Progress → Awaiting Approval → Done)
  - Reads/lists items in each column
  - Generates PR creation URLs

BOARD.md format:
  ## 🔙 Backlog
  - [#N] Title (@branch-name)
  ## 🏗️ In Progress
  - [#N] Title (@branch-name)
  etc.
"""

import json
import os
import re
import sys

BOARD_PATH = os.path.join(os.path.dirname(__file__), "..", "BOARD.md")

COLUMNS = {
    "backlog": "🔙 Backlog",
    "in-progress": "🏗️ In Progress",
    "awaiting-approval": "👀 Awaiting Approval",
    "done": "✅ Done",
}

COLUMN_ORDER = ["backlog", "in-progress", "awaiting-approval", "done"]


def read_board():
    """Return list of sections with their items."""
    with open(BOARD_PATH) as f:
        content = f.read()

    sections = {}
    current_section = None
    for line in content.split("\n"):
        for col_key, col_name in COLUMNS.items():
            if f"## {col_name}" in line:
                current_section = col_key
                sections[current_section] = []
                break
        else:
            if current_section and line.strip():
                sections.setdefault(current_section, []).append(line)

    return sections


def find_item(sections, issue_number):
    """Find which column contains a given issue number. Returns (column_key, line, index) or (None, None, None)."""
    num = str(issue_number)
    for col_key in COLUMN_ORDER:
        for i, line in enumerate(sections.get(col_key, [])):
            if f"[#{num}]" in line:
                return col_key, line, i
    return None, None, None


def move_item(issue_number, from_col, to_col, branch_name=None):
    """Move an item between columns. Updates BOARD.md in place."""
    sections = read_board()

    col, line, idx = find_item(sections, issue_number)
    if col is None:
        print(f"Issue #{issue_number} not found on board", file=sys.stderr)
        return False

    if branch_name:
        # Update branch name in the line
        line = re.sub(r"\(@[^)]*\)", "", line).strip()
        line = f"{line} (@{branch_name})"

    sections[col].pop(idx)
    sections.setdefault(to_col, []).append(line)

    write_board(sections)
    print(f"Moved #{issue_number}: {col} → {to_col}")
    return True


def add_item(issue_number, title):
    """Add a new item to the Backlog column."""
    sections = read_board()

    # Check if already exists
    col, _, _ = find_item(sections, issue_number)
    if col:
        print(f"Issue #{issue_number} already in {col}", file=sys.stderr)
        return False

    entry = f"- [#{issue_number}] {title}"
    sections.setdefault("backlog", []).append(entry)
    write_board(sections)
    print(f"Added #{issue_number} to Backlog: {title}")
    return True


def write_board(sections):
    """Rebuild BOARD.md from sections dict."""
    with open(BOARD_PATH) as f:
        content = f.read()

    header_end = 0
    for match in re.finditer(r"^## ", content, re.MULTILINE):
        header_end = match.start()
        break

    preamble = content[:header_end] if header_end > 0 else ""

    # Rebuild from COLUMN_ORDER
    lines = [preamble.rstrip()]
    for col_key in COLUMN_ORDER:
        col_name = COLUMNS[col_key]
        items = sections.get(col_key, [])
        lines.append("")
        lines.append(f"## {col_name}")
        lines.append("")
        if items:
            for item in items:
                lines.append(item)
        else:
            lines.append(f"_No items._")
        lines.append("")

    # Append footer (how-it-works) from original if present
    footer_match = re.search(r"^---\n\n## How It Works.*", content, re.DOTALL)
    if footer_match:
        lines.append("")
        lines.append(footer_match.group(0))

    with open(BOARD_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


def pr_url(branch_name):
    """Generate the one-click PR creation URL."""
    return f"https://github.com/EricManintveld/openclaw-website/compare/main...{branch_name}?expand=1"


def list_column(col_key):
    """Print items in a column."""
    sections = read_board()
    items = sections.get(col_key, [])
    for item in items:
        print(item)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage Sam's Playground BOARD.md")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list-backlog", help="List backlog items")
    sub.add_parser("list-in-progress", help="List in-progress items")
    sub.add_parser("list-awaiting", help="List awaiting-approval items")
    sub.add_parser("list-done", help="List done items")

    p_add = sub.add_parser("add", help="Add item to backlog")
    p_add.add_argument("number", type=int)
    p_add.add_argument("title", nargs="+")

    p_move = sub.add_parser("move", help="Move item between columns")
    p_move.add_argument("number", type=int)
    p_move.add_argument("to", choices=COLUMN_ORDER)
    p_move.add_argument("--branch", "-b", help="Branch name to annotate")

    p_pr = sub.add_parser("pr-url", help="Get PR creation URL for a branch")
    p_pr.add_argument("branch")

    p_find = sub.add_parser("find", help="Find which column contains an issue")
    p_find.add_argument("number", type=int)

    args = parser.parse_args()

    if args.command == "list-backlog":
        list_column("backlog")
    elif args.command == "list-in-progress":
        list_column("in-progress")
    elif args.command == "list-awaiting":
        list_column("awaiting-approval")
    elif args.command == "list-done":
        list_column("done")
    elif args.command == "add":
        add_item(args.number, " ".join(args.title))
    elif args.command == "move":
        sections = read_board()
        from_col, _, _ = find_item(sections, args.number)
        if from_col:
            move_item(args.number, from_col, args.to, args.branch)
        else:
            print(f"Issue #{args.number} not on board", file=sys.stderr)
            sys.exit(1)
    elif args.command == "pr-url":
        print(pr_url(args.branch))
    elif args.command == "find":
        sections = read_board()
        col, line, _ = find_item(sections, args.number)
        if col:
            print(json.dumps({"column": col, "line": line.strip()}))
        else:
            sys.exit(1)
    else:
        parser.print_help()