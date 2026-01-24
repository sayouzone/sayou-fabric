from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from github import Auth, Github
except ImportError:
    Github = None


@register_component("fetcher")
class GithubFetcher(BaseFetcher):
    """
    Fetches raw content of a file or issue from GitHub.
    """

    component_name = "GithubFetcher"
    SUPPORTED_TYPES = ["github"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return (
            1.0
            if uri.startswith("github-blob://") or uri.startswith("github-issue://")
            else 0.0
        )

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token = task.params["token"]
        repo_name = task.params["repo_name"]

        auth = Auth.Token(token)
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)

        # Case A: Code (File Blob)
        if "github-blob://" in task.uri:
            file_path = task.params["file_path"]

            content_file = repo.get_contents(file_path)
            raw_data = content_file.decoded_content

            try:
                content = raw_data.decode("utf-8")
                is_binary = False
            except UnicodeDecodeError:
                content = raw_data
                is_binary = True

            return {
                "content": content,
                "meta": {
                    "source": "github_code",
                    "file_id": file_path,
                    "title": file_path.split("/")[-1],
                    "path": file_path,
                    "repo": repo_name,
                },
            }

        # Case B: Issue
        elif "github-issue://" in task.uri:
            issue_num = task.params["issue_number"]
            issue = repo.get_issue(issue_num)

            formatted_md = f"""# [Issue #{issue.number}] {issue.title}

**Author:** {issue.user.login}
**State:** {issue.state}
**Created:** {issue.created_at}
**URL:** {issue.html_url}

---
{issue.body}
"""
            return {
                "content": formatted_md,
                "meta": {
                    "source": "github_issue",
                    "file_id": f"issue_{issue_num}",
                    "title": f"Issue {issue_num}: {issue.title}",
                    "extension": ".md",
                },
            }
