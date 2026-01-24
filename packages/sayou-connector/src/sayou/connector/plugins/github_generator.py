import os
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator

try:
    from github import Auth, Github
except ImportError:
    Github = None


@register_component("generator")
class GithubGenerator(BaseGenerator):
    """
    Scans a GitHub repository for files (code) or issues.
    """

    component_name = "GithubGenerator"
    SUPPORTED_TYPES = ["github"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("github://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        if not Github:
            raise ImportError("Please install PyGithub: pip install PyGithub")

        # 1. Authentication
        token = kwargs.get("token") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GitHub token is required (kwargs or env 'GITHUB_TOKEN')")

        auth = Auth.Token(token)
        g = Github(auth=auth)

        # 2. Parse target repository
        # source: github://owner/repo -> owner/repo
        repo_name = source.replace("github://", "").strip("/")

        self._log(f"🐙 Accessing GitHub Repo: {repo_name}")
        repo = g.get_repo(repo_name)

        # 3. Mode decision (default: code)
        # target='code' (file), 'issues' (issue), 'pr' (pull request)
        target = kwargs.get("target", "code")
        limit = int(kwargs.get("limit", 20))

        count = 0

        if target == "code":
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    # if not file_content.path.endswith(".py"): continue

                    yield SayouTask(
                        uri=f"github-blob://{repo_name}/{file_content.path}",
                        source_type="github",
                        params={
                            "token": token,
                            "repo_name": repo_name,
                            "file_path": file_content.path,
                            "sha": file_content.sha,
                        },
                    )
                    count += 1
                    if limit > 0 and count >= limit:
                        break

        elif target == "issues":
            issues = repo.get_issues(state="open")
            for issue in issues:
                yield SayouTask(
                    uri=f"github-issue://{repo_name}/{issue.number}",
                    source_type="github",
                    params={
                        "token": token,
                        "repo_name": repo_name,
                        "issue_number": issue.number,
                    },
                )
                count += 1
                if limit > 0 and count >= limit:
                    break
