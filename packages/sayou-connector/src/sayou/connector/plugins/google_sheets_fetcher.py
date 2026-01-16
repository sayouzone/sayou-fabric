import csv
import io
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
class GoogleSheetsFetcher(BaseFetcher):
    """
    Fetches data from Google Sheets using Sheets API (v4).
    Iterates through all tabs(sheets) and converts data to CSV format.
    No 10MB limit.
    """

    component_name = "GoogleSheetsFetcher"
    SUPPORTED_TYPES = ["sheets"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gsheets://spreadsheet/") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token_path = task.params.get("token_path")
        spreadsheet_id = task.uri.replace("gsheets://spreadsheet/", "").split("/")[0]

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("sheets", "v4", credentials=creds)

        # 1. Metadata lookup (sheet list confirmation)
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        title = spreadsheet.get("properties", {}).get("title", "Untitled")
        sheets = spreadsheet.get("sheets", [])

        all_content = []

        # 2. Each sheet data lookup
        for sheet in sheets:
            sheet_title = sheet["properties"]["title"]

            # Get all values from the sheet
            result = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=spreadsheet_id,
                    range=sheet_title,
                )
                .execute()
            )

            rows = result.get("values", [])

            if not rows:
                continue

            # 3. CSV format conversion (processing in memory)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerows(rows)
            csv_string = output.getvalue()

            # Sheet separator and text concatenation
            section = {sheet_title: csv_string}
            all_content.append(section)

        return all_content
        # {
        #     "content": final_text,
        #     "meta": {
        #         "source": "google_sheets",
        #         "file_id": spreadsheet_id,
        #         "title": title,
        #         "extension": ".csv",
        #     },
        # }
