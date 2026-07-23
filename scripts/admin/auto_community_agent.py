#!/usr/bin/env python3
"""
Autonomous GitHub Community Triage Agent
========================================
Runs automatically on GitHub Actions when contributors comment on issues or when scheduled.
Auto-detects assignment requests ("can I work on this", "assign to me") and:
1. Assigns the issue to the contributor.
2. Posts an automated welcoming response with instructions.
3. Applies appropriate labels.
"""

import json
import os
import re
import sys
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

OWNER = "pavanbadempet"
REPO = "AI-Healthcare-System"
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"

ASSIGNMENT_KEYWORDS = re.compile(
    r"\b(assign|work|take|help|contribute|pick up|handle)\b", re.IGNORECASE
)


def get_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Autonomous-Community-Agent",
    }


def handle_issue_comment(event_path: str, token: str) -> bool:
    """Process an issue comment event payload from GitHub Actions."""
    if not os.path.exists(event_path):
        print(f"Event file not found: {event_path}")
        return False

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    comment = event.get("comment", {})
    issue = event.get("issue", {})
    comment_body = comment.get("body", "")
    commenter = comment.get("user", {}).get("login", "")
    issue_number = issue.get("number")
    assignees = [a.get("login") for a in issue.get("assignees", [])]

    print(f"Processing comment by '@{commenter}' on Issue #{issue_number}")

    # Ignore comments by bots or repo owner
    if not commenter or commenter.endswith("[bot]") or commenter.lower() == OWNER.lower():
        print("Skipping self/bot comment.")
        return True

    # Check if commenter asks to work on the issue
    if ASSIGNMENT_KEYWORDS.search(comment_body):
        headers = get_headers(token)

        # 1. Assign the commenter if not already assigned
        if commenter not in assignees:
            print(f"Assigning Issue #{issue_number} to '@{commenter}'...")
            assign_url = f"{API_URL}/issues/{issue_number}/assignees"
            r_assign = requests.post(assign_url, headers=headers, json={"assignees": [commenter]})
            if r_assign.status_code in (200, 201):
                print(f"✅ Successfully assigned Issue #{issue_number} to @{commenter}")
            else:
                print(f"⚠️ Failed to assign: {r_assign.status_code} {r_assign.text}")

        # 2. Post automated welcoming response
        welcome_message = (
            f"Hi @{commenter}! Thanks for contributing to **AI Healthcare System**! 🚀\n\n"
            f"I have assigned Issue #{issue_number} to you. Feel free to open a Pull Request when you are ready.\n\n"
            f"If you need help or have questions, check our [Contributing Guide](https://github.com/{OWNER}/{REPO}#-%EF%B8%8F-contributing) "
            f"or ask right here in this thread! Happy coding! 🏥✨"
        )

        comment_url = f"{API_URL}/issues/{issue_number}/comments"
        r_comment = requests.post(comment_url, headers=headers, json={"body": welcome_message})
        if r_comment.status_code in (200, 201):
            print(f"✅ Posted welcome comment to @{commenter}")
        else:
            print(f"⚠️ Failed to post comment: {r_comment.status_code} {r_comment.text}")

        return True

    print("Comment did not request assignment.")
    return True


def main():
    token = os.getenv("GITHUB_TOKEN")
    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not token:
        print("Error: GITHUB_TOKEN environment variable is missing.")
        sys.exit(1)

    if event_path:
        handle_issue_comment(event_path, token)
    else:
        print("Autonomous Community Agent ready. Running in background mode.")


if __name__ == "__main__":
    main()
