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
class GoogleSlidesFetcher(BaseFetcher):
    """
    Fetches content from Google Slides using Slides API (v1).
    Extracts text from shapes and tables on each slide.
    """

    component_name = "GoogleSlidesFetcher"
    SUPPORTED_TYPES = ["slides"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gslides://presentation/") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token_path = task.params.get("token_path")
        presentation_id = task.uri.replace("gslides://presentation/", "").split("/")[0]

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("slides", "v1", credentials=creds)

        # 1. Full structure lookup
        presentation = (
            service.presentations().get(presentationId=presentation_id).execute()
        )
        title = presentation.get("title", "Untitled")
        slides = presentation.get("slides", [])

        extracted_text = [f"# Presentation: {title}\n"]
        extracted_text2 = [f"# Presentation: {title}\n"]

        # 2. Slide traversal
        for i, slide in enumerate(slides):
            slide_number = i + 1
            extracted_text.append(f"\n## Slide {slide_number}")

            page_elements = slide.get("pageElements", [])
            extracted_text2.append(page_elements)

            for element in page_elements:
                # Text box (Shape) processing
                if "shape" in element and "text" in element["shape"]:
                    text_content = self._extract_text_from_element(
                        element["shape"]["text"]
                    )
                    if text_content:
                        extracted_text.append(f"- {text_content}")

                # Table processing
                elif "table" in element:
                    table_text = self._extract_text_from_table(element["table"])
                    if table_text:
                        extracted_text.append(f"\n[Table]\n{table_text}")

        final_text = extracted_text2

        return final_text
        # {
        #     "content": final_text,
        #     "meta": {
        #         "source": "google_slides",
        #         "file_id": presentation_id,
        #         "title": title,
        #         "extension": ".txt",  # Text file storage
        #     },
        # }

    def _extract_text_from_element(self, text_obj: Dict) -> str:
        """Text element internal textRun concatenation"""
        full_text = ""
        for text_element in text_obj.get("textElements", []):
            if "textRun" in text_element:
                full_text += text_element["textRun"].get("content", "")
        return full_text.strip()

    def _extract_text_from_table(self, table_obj: Dict) -> str:
        """Table text extraction"""
        rows_text = []
        for row in table_obj.get("tableRows", []):
            cells_text = []
            for cell in row.get("tableCells", []):
                if "text" in cell:
                    cells_text.append(self._extract_text_from_element(cell["text"]))
            rows_text.append(" | ".join(cells_text))
        return "\n".join(rows_text)
