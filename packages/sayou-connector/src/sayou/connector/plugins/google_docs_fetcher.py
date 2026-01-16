import html
import io
import re
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    build = None


@register_component("fetcher")
class GoogleDocsFetcher(BaseFetcher):
    """
    Fetches content from Google Docs using the Docs API (v1).
    Extracts text and converts basic styling to Markdown.
    Bypasses the 10MB export limit of Drive API.
    """

    component_name = "GoogleDocsFetcher"
    SUPPORTED_TYPES = ["docs"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gdocs://document/") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token_path = task.params.get("token_path")
        doc_id = task.uri.replace("gdocs://document/", "").split("/")[0]
        original_title = task.meta.get("filename", "Untitled")

        fetch_mode = task.params.get("fetch_mode", "html")

        creds = Credentials.from_authorized_user_file(token_path)

        if fetch_mode == "html":
            return self._fetch_as_html(creds, doc_id, original_title)
        else:
            return self._fetch_as_json(creds, doc_id, original_title)

    # =========================================================
    # Mode 1: JSON (Docs API)
    # =========================================================
    def _fetch_as_json(self, creds, doc_id, title) -> Dict[str, Any]:
        try:
            service = build("docs", "v1", credentials=creds)
            document = service.documents().get(documentId=doc_id).execute()

            tab_count = len(document.get("tabs", [])) if "tabs" in document else 0
            if tab_count > 0:
                self._log(f"ℹ️ Fetched JSON with {tab_count} tabs.")

            return document
            # {
            #     "content": document,
            #     "meta": {
            #         "source": "google_docs",
            #         "doc_id": doc_id,
            #         "title": title,
            #         "extension": ".json",
            #         "mode": "api_json",
            #     },
            # }
        except Exception as e:
            self._log(f"Docs API Failed: {e}", level="error")
            raise e

    # =========================================================
    # Mode 2: HTML (Drive API Export)
    # =========================================================
    def _fetch_as_html(self, creds, doc_id, title) -> Dict[str, Any]:
        try:
            service = build("drive", "v3", credentials=creds)

            request = service.files().export_media(fileId=doc_id, mimeType="text/html")

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            raw_bytes = fh.getvalue()
            html_str = raw_bytes.decode("utf-8", errors="replace")
            decoded_html = html.unescape(html_str)
            formatted_html = re.sub(
                r"(</(p|div|h[1-6]|li|ul|ol|table|tr|blockquote)>)",
                r"\1\n",
                decoded_html,
                flags=re.IGNORECASE,
            )

            return formatted_html
            # {
            #     "content": human_readable_html,
            #     "meta": {
            #         "source": "google_docs",
            #         "doc_id": doc_id,
            #         "title": title,
            #         "extension": ".html",
            #         "mode": "export_html",
            #     },
            # }
        except Exception as e:
            self._log(f"HTML Export Failed: {e}", level="error")
            raise e
