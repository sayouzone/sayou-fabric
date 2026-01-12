import os
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
class GoogleDriveGenerator(BaseGenerator):
    """
    Generates tasks for files in Google Drive.
    URI Schema:
      - gdrive://root       (My Drive Root)
      - gdrive://{folderID} (Specific Folder)
    """

    component_name = "GoogleDriveGenerator"
    SUPPORTED_TYPES = ["drive"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gdrive://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        # 1. Certification
        token_path = kwargs.get("google_token_path")

        if not os.path.exists(token_path):
            raise FileNotFoundError(
                f"Google Token not found at {token_path}. Run authentication script first."
            )

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("drive", "v3", credentials=creds)

        # 2. Search Query
        root_id = source.replace("gdrive://", "") or "root"

        query_override = None
        if "?" in root_id:
            root_id, query_part = root_id.split("?", 1)

        # 3. File Search (Recursive or Flat Search)
        query = f"'{root_id}' in parents and trashed = false"
        if root_id == "root":
            pass

        results = (
            service.files()
            .list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, webViewLink, createdTime, modifiedTime)",
            )
            .execute()
        )

        files = results.get("files", [])

        for file in files:
            mime_type = file.get("mimeType")
            file_id = file["id"]
            file_name = file["name"]

            if mime_type == "application/vnd.google-apps.document":
                target_uri = f"gdocs://document/{file_id}"
                source = "docs"

            elif mime_type == "application/vnd.google-apps.spreadsheet":
                target_uri = f"gsheets://spreadsheet/{file_id}"
                source = "sheets"

            elif mime_type == "application/vnd.google-apps.presentation":
                target_uri = f"gslides://presentation/{file_id}"
                source = "slides"

            elif mime_type == "application/vnd.google-apps.folder":
                continue

            else:
                target_uri = f"gdrive://file/{file_id}"
                source = "drive"

            yield SayouTask(
                uri=target_uri,
                source_type=source,
                params={
                    "file_id": file_id,
                    "mime_type": mime_type,
                    "token_path": token_path,
                },
                meta={
                    "source": source,
                    "filename": file_name,
                    "file_id": file_id,
                    "mime_type": mime_type,
                    "link": file.get("webViewLink"),
                },
            )
