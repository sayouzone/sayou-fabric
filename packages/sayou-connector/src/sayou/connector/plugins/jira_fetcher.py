from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from atlassian import Jira
except ImportError:
    Jira = None


@register_component("fetcher")
class JiraFetcher(BaseFetcher):
    """
    Fetches Jira issue details including comments.
    """

    component_name = "JiraFetcher"
    SUPPORTED_TYPES = ["jira"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("jira-issue://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        params = task.params
        jira = Jira(
            url=params["url"], username=params["username"], password=params["token"]
        )

        key = params["issue_key"]

        # Get issue details (including comments)
        issue = jira.issue(key)
        fields = issue["fields"]

        # 1. Basic field extraction
        summary = fields.get("summary", "")
        description = fields.get("description", "") or "(No description)"
        status = fields.get("status", {}).get("name", "Unknown")
        priority = fields.get("priority", {}).get("name", "None")
        assignee = fields.get("assignee", {})
        assignee_name = (
            assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
        )
        reporter = fields.get("reporter", {}).get("displayName", "Unknown")
        created = fields.get("created", "")
        web_link = f"{params['url']}/browse/{key}"

        # 2. Extract comments
        comments_section = ""
        if "comment" in fields and "comments" in fields["comment"]:
            comments_section = "\n## Comments\n"
            for c in fields["comment"]["comments"]:
                author = c.get("author", {}).get("displayName", "Unknown")
                body = c.get("body", "")
                comments_section += f"- **{author}**: {body}\n"

        # 3. Markdown formatting
        formatted_md = f"""# [{key}] {summary}

**Status:** {status} | **Priority:** {priority}
**Assignee:** {assignee_name} | **Reporter:** {reporter}
**Created:** {created}
**Link:** {web_link}

---
## Description
{description}

---
{comments_section}
"""

        return {
            "content": formatted_md,
            "meta": {
                "source": "jira",
                "file_id": key,
                "title": f"[{key}] {summary}",
                "url": web_link,
                "status": status,
                "extension": ".md",
            },
        }
