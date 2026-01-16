import base64
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    build = None


@register_component("fetcher")
class GmailFetcher(BaseFetcher):
    """
    Fetches specific email content using Gmail API.
    Reconstructs the email into a standardized HTML format suitable for Refinery.
    """

    component_name = "GmailFetcher"
    SUPPORTED_TYPES = ["gmail"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gmail-msg://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token_path = task.params.get("token_path")
        msg_id = task.params.get("msg_id")

        if not build:
            raise ImportError("Please install google-api-python-client")

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("gmail", "v1", credentials=creds)

        # 1. Fetch email details (format='full')
        message = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        # 2. Parse headers (Subject, From, Date)
        subject = self._get_header(headers, "Subject", "(No Subject)")
        sender = self._get_header(headers, "From", "Unknown")
        date = self._get_header(headers, "Date", "")

        # 3. Extract body (Recursive)
        body_content = self._extract_body(payload)

        # 4. Reconstruct HTML (User Request Format)
        html_doc = f"""<!DOCTYPE html>
<html>
<head>
    <title>{subject}</title>
    <meta name="sender" content="{sender}">
    <meta name="date" content="{date}">
    <meta name="msg_id" content="{msg_id}">
    <meta name="source" content="gmail">
</head>
<body>
{body_content}
</body>
</html>"""

        return html_doc.strip()

    def _get_header(self, headers: list, name: str, default: str) -> str:
        for h in headers:
            if h["name"].lower() == name.lower():
                return h["value"]
        return default

    def _extract_body(self, payload: dict) -> str:
        body = ""

        # Case A: Single Part
        if "body" in payload and payload["body"].get("data"):
            mime_type = payload.get("mimeType", "")
            data = payload["body"]["data"]
            decoded_text = self._decode_base64url(data)

            if mime_type == "text/html":
                return decoded_text
            elif mime_type == "text/plain":
                return f"<pre>{decoded_text}</pre>"

        # Case B: Multi Part
        if "parts" in payload:
            html_part = None
            text_part = None

            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")

                content = self._extract_body(part)

                if mime_type == "text/html":
                    html_part = content
                elif mime_type == "text/plain":
                    text_part = content
                elif "multipart" in mime_type:
                    if content:
                        html_part = content

            if html_part:
                return html_part
            if text_part:
                return text_part

        return body

    def _decode_base64url(self, data: str) -> str:
        try:
            padding = len(data) % 4
            if padding:
                data += "=" * (4 - padding)
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        except Exception:
            return ""
