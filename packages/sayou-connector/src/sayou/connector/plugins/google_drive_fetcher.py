import io
import os
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import chardet
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    build = None
    chardet = None


@register_component("fetcher")
class GoogleDriveFetcher(BaseFetcher):
    """
    Fetches content from Google Drive files.
    - Google Native Formats -> Converted to MS Office formats (.docx, .xlsx, .pptx)
    - Standard Files (PDF, JPG, ZIP...) -> Downloaded as original binary.
    """

    component_name = "GoogleDriveFetcher"
    SUPPORTED_TYPES = ["drive"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gdrive://file/") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token_path = task.params.get("token_path")
        file_id = task.params.get("file_id")
        mime_type = task.params.get("mime_type")
        original_name = task.meta.get("filename", "unknown_file")

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("drive", "v3", credentials=creds)

        request = None
        extension = ""
        is_google_doc = False

        # 1. Google Native Formats
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            extension = ".docx"
            is_google_doc = True
        elif mime_type == "application/vnd.google-apps.spreadsheet":
            request = service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            extension = ".xlsx"
            is_google_doc = True
        elif mime_type == "application/vnd.google-apps.presentation":
            request = service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
            extension = ".pptx"
            is_google_doc = True
        else:
            request = service.files().get_media(fileId=file_id)
            _, ext = os.path.splitext(original_name)
            extension = ext if ext else ""

        # 2. Execute Download
        try:
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            raw_bytes = fh.getvalue()

            final_content = raw_bytes
            is_text_candidate = False

            if mime_type.startswith("text/") or mime_type == "application/json":
                is_text_candidate = True
            elif extension.lower() in [
                ".csv",
                ".txt",
                ".json",
                ".md",
                ".py",
                ".html",
                ".xml",
            ]:
                is_text_candidate = True

            if not is_google_doc and is_text_candidate:
                detected = chardet.detect(raw_bytes)
                encoding = detected.get("encoding")
                confidence = detected.get("confidence", 0)

                # 2) EUC-KR -> UTF-8
                if (
                    encoding
                    and encoding.lower() not in ["utf-8", "ascii"]
                    and confidence > 0.6
                ):
                    try:
                        # Decode (Bytes -> Str)
                        text_content = raw_bytes.decode(encoding)
                        # Encode back to Bytes (Str -> UTF-8 Bytes)
                        final_content = text_content.encode("utf-8")
                        self._log(
                            f"Transcoded {original_name} from {encoding} to utf-8 bytes."
                        )
                    except Exception as e:
                        self._log(
                            f"Encoding conversion failed: {e}. Keeping raw bytes.",
                            level="warning",
                        )
                        final_content = raw_bytes

            # 3. Return
            return {
                "content": final_content,
                "meta": {
                    "source": "google_drive",
                    "file_id": file_id,
                    "mime_type": mime_type,
                    "original_filename": original_name,
                    "suggested_filename": (
                        f"{original_name}{extension}"
                        if not original_name.endswith(extension)
                        else original_name
                    ),
                    "extension": extension,
                    "is_binary": isinstance(final_content, bytes),
                },
            }

        except HttpError as e:
            self._log(f"Drive Download Failed ({file_id}): {e}", level="error")
            return {
                "content": b"",
                "meta": {"source": "google_drive", "error": str(e), "file_id": file_id},
            }
