from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator

try:
    from atlassian import Jira
except ImportError:
    Jira = None


@register_component("generator")
class JiraGenerator(BaseGenerator):
    """
    Scans Jira issues using JQL.
    """

    component_name = "JiraGenerator"
    SUPPORTED_TYPES = ["jira"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("jira://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        if not Jira:
            raise ImportError("Please install atlassian-python-api")

        url = kwargs.get("url")
        username = kwargs.get("username")
        token = kwargs.get("token")

        if not (url and username and token):
            raise ValueError("Jira requires 'url', 'username', and 'token'.")

        jira = Jira(url=url, username=username, password=token)

        # source: jira://PROJ (PROJ is project key)
        project_key = source.replace("jira://", "").strip()

        limit = int(kwargs.get("limit", 20))

        self._log(f"Accessing Jira project: {project_key or 'All Assigned'}")

        # Create JQL
        if project_key:
            jql = f'project = "{project_key}" ORDER BY created DESC'
        else:
            jql = "assignee = currentUser() ORDER BY updated DESC"

        # Call Jira API
        issues = jira.jql(jql, limit=limit)

        if "issues" not in issues:
            self._log("No issues found.", level="warning")
            return

        for issue in issues["issues"]:
            key = issue["key"]
            fields = issue["fields"]
            summary = fields.get("summary", "No Summary")

            yield SayouTask(
                uri=f"jira-issue://{key}",
                source_type="jira",
                params={
                    "url": url,
                    "username": username,
                    "token": token,
                    "issue_key": key,
                    "summary": summary,
                },
            )
