import os
import re
import requests
from datetime import datetime, timezone


def _normalize_github_repo(repo: str) -> str:
    """Accept owner/repo or a full GitHub URL."""
    repo = (repo or "").strip()
    if not repo:
        return "your-org/support-tickets"

    repo = re.sub(r"^https?://github\.com/", "", repo)
    repo = repo.rstrip("/")
    if repo.endswith(".git"):
        repo = repo[:-4]

    return repo


class GitHubTicketClient:
    """Creates support tickets as GitHub Issues."""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.repo = _normalize_github_repo(os.getenv("GITHUB_REPO", ""))
        self.base_url = f"https://api.github.com/repos/{self.repo}/issues"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def create(self, name: str, email: str, summary: str, description: str) -> dict:
        if not self.token:
            return {
                "success": True,
                "ticket_id": "DEMO-001",
                "url": f"https://github.com/{self.repo}/issues",
                "message": "Demo mode: set GITHUB_TOKEN in Space secrets to create real GitHub Issues."
            }

        body = (
            f"**Customer Name:** {name}\n"
            f"**Customer Email:** {email}\n"
            f"**Submitted:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"---\n\n"
            f"## Issue Description\n\n{description}"
        )

        payload = {
            "title": f"[Support] {summary}",
            "body": body,
            "labels": ["support", "customer-request"]
        }

        try:
            response = requests.post(
                self.base_url, json=payload, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "ticket_id": f"#{data['number']}",
                "url": data["html_url"],
                "message": f"Ticket #{data['number']} created successfully!"
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "ticket_id": None,
                "url": None,
                "message": f"Failed to create ticket: {e}"
            }
