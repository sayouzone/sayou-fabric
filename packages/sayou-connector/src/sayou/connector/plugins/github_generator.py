import os
import time
from collections import deque
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
    Supports recursive scanning, extension filtering, and issue collection.
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

        start_path = kwargs.get("path", "")

        self._log(f"🐙 Accessing GitHub Repo: {repo_name} (Path: '{start_path}')")
        repo = g.get_repo(repo_name)

        # 3. Parameters
        target = kwargs.get("target", "code")  # 'code' or 'issues'
        limit = int(kwargs.get("limit", 0))
        extensions = kwargs.get("extensions", [])

        count = 0

        # =========================================================
        # Case A: Code (File Traversal)
        # =========================================================
        if target == "code":
            self._log(f"   -> Mode: Code (Path: '{start_path}')")

            queue = deque()

            try:
                self._log(f"   -> Fetching contents from '{start_path}'...")
                root_contents = repo.get_contents(start_path)
                if isinstance(root_contents, list):
                    self._log(f"   -> Found {len(root_contents)} items in root path.")
                    queue.extend(root_contents)
                else:
                    self._log(
                        f"   -> Path points to a single file: {root_contents.path}"
                    )
                    queue.append(root_contents)
            except Exception as e:
                self._log(f"Failed to access path '{start_path}': {e}", level="error")
                return

            while queue:
                if limit > 0 and count >= limit:
                    self._log(f"🛑 Limit reached ({limit}). Stopping traversal.")
                    break

                try:
                    file_content = queue.popleft()

                    if file_content.type == "dir":
                        try:
                            items = repo.get_contents(file_content.path)
                            if isinstance(items, list):
                                queue.extend(items)
                            else:
                                queue.append(items)
                            time.sleep(0.1)
                        except Exception as e:
                            self._log(
                                f"Skipping dir {file_content.path}: {e}",
                                level="warning",
                            )

                    else:
                        if extensions and not any(
                            file_content.path.endswith(ext) for ext in extensions
                        ):
                            continue

                        # Calculate Parent Path
                        path_parts = file_content.path.split("/")
                        parent_path = (
                            "/".join(path_parts[:-1]) if len(path_parts) > 1 else ""
                        )

                        yield SayouTask(
                            uri=f"github-blob://{repo_name}/{file_content.path}",
                            source_type="github",
                            params={
                                "token": token,
                                "repo_name": repo_name,
                                "file_path": file_content.path,
                                "file_name": file_content.name,
                                "parent_path": parent_path,
                                "sha": file_content.sha,
                                "type": "code",
                            },
                        )
                        count += 1

                except Exception as e:
                    self._log(f"Error processing item: {e}", level="error")

        # =========================================================
        # Case B: Issues
        # =========================================================
        elif target == "issues":
            state = kwargs.get("state", "open")  # open, closed, all
            self._log(f"   -> Mode: Issues (State: {state})")

            issues = repo.get_issues(state=state)

            for issue in issues:
                if limit > 0 and count >= limit:
                    self._log(f"🛑 Limit reached ({limit}). Stopping issue scan.")
                    break

                yield SayouTask(
                    uri=f"github-issue://{repo_name}/{issue.number}",
                    source_type="github",
                    params={
                        "token": token,
                        "repo_name": repo_name,
                        "issue_number": issue.number,
                        "title": issue.title,
                        "type": "issue",
                    },
                )
                count += 1
