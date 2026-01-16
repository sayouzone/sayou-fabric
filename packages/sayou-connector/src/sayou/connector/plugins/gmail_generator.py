from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    build = None


@register_component("generator")
class GmailGenerator(BaseGenerator):
    """
    Scans Gmail inbox using Gmail API (OAuth) and generates tasks.
    """

    component_name = "GmailGenerator"
    SUPPORTED_TYPES = ["gmail"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("gmail://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        """
        Connects to Gmail API -> Search (List) -> Yield Tasks.
        source example: gmail://me (default) or gmail://me?q=is:unread
        """
        if not build:
            raise ImportError(
                "Please install google-api-python-client google-auth-oauthlib"
            )

        token_path = kwargs.get("token_path")
        if not token_path:
            raise ValueError("GmailGenerator requires 'token_path' in kwargs.")

        # 1. Parsing Parameters
        query = kwargs.get("query", "is:inbox")
        max_results = int(kwargs.get("limit", 10))

        # 2. Connect to Gmail API
        creds = Credentials.from_authorized_user_file(token_path)
        service = build("gmail", "v1", credentials=creds)

        try:
            # 3. Fetch email list
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])

            self._log(f"📧 Found {len(messages)} emails. Generating tasks...")

            # 4. Generate tasks
            for msg in messages:
                msg_id = msg["id"]
                thread_id = msg["threadId"]
                task_uri = f"gmail-msg://{msg_id}"

                yield SayouTask(
                    uri=task_uri,
                    source_type="gmail",
                    params={
                        "token_path": token_path,
                        "msg_id": msg_id,
                        "thread_id": thread_id,
                    },
                )

        except Exception as e:
            self._log(f"Gmail API List failed: {e}", level="error")
            raise e
