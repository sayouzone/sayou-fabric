import json
import os
import pickle
import re
from typing import Any

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter


@register_component("writer")
class FileWriter(BaseWriter):
    """
    Writes data to the local filesystem with intelligent extension detection.
    Robustly handles raw data even without metadata using content sniffing.
    """

    component_name = "FileWriter"
    SUPPORTED_TYPES = ["file", "local", "json", "pickle"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if not destination:
            return 0.0

        if "://" not in destination:
            if destination.endswith(".jsonl"):
                return 0.5
            return 0.9

        if destination.startswith("file://"):
            return 1.0

        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        # 1. Directory Setup
        if destination.endswith(os.sep) or (
            os.path.exists(destination) and os.path.isdir(destination)
        ):
            destination = os.path.join(destination, "output")

        folder = os.path.dirname(destination)
        if folder:
            os.makedirs(folder, exist_ok=True)

        mode = kwargs.get("mode", "w")
        encoding = kwargs.get("encoding", "utf-8")

        try:
            # 2. Unwrap Data & Metadata extraction
            real_content = input_data
            metadata = {}

            # Sayou Dictionary Wrapper processing
            if isinstance(input_data, dict) and "content" in input_data:
                real_content = input_data["content"]
                metadata = input_data.get("meta") or input_data.get("metadata", {})

            # SayouBlock List processing (Refinery result)
            elif (
                isinstance(input_data, list)
                and len(input_data) > 0
                and hasattr(input_data[0], "type")
            ):
                metadata["extension"] = ".json"

            # 3. Intelligent Detection
            filename, current_ext = self.split_path_smart(destination)

            if not current_ext:
                detected_ext = self._detect_extension(real_content, metadata)
                destination = f"{filename}{detected_ext}"

            # 4. Save Logic (Type-based Writing)

            # Case A: Binary (Bytes)
            if isinstance(real_content, bytes):
                write_mode = "wb"
                final_data = real_content

            # Case B: JSON Structure (Dict/List)
            elif isinstance(real_content, (dict, list, tuple)):
                write_mode = "w"
                final_data = json.dumps(
                    real_content, indent=2, ensure_ascii=False, default=str
                )

            # Case C: String (Text/HTML/CSV/Markdown)
            elif isinstance(real_content, str):
                write_mode = "w"
                final_data = real_content

            # Case D: Others (Pickle Fallback)
            else:
                write_mode = "wb"
                final_data = pickle.dumps(real_content)
                if not destination.endswith(".pkl"):
                    destination += ".pkl"

            with open(
                destination,
                write_mode,
                encoding=None if "b" in write_mode else encoding,
            ) as f:
                f.write(final_data)

            self._log(
                f"💾 Saved to {destination} ({len(final_data) if isinstance(final_data, (bytes, str)) else 'obj'} bytes)"
            )
            return True

        except Exception as e:
            self._log(f"Write failed: {e}", level="error")
            raise e

    def split_path_smart(self, path: str):
        root, ext = os.path.splitext(path)
        if not re.match(r"^\.[a-zA-Z0-9]{1,10}$", ext):
            return path, ""

        return root, ext

    def _detect_extension(self, data: Any, metadata: dict) -> str:
        # 1. Metadata Priority
        if metadata.get("extension"):
            ext = metadata["extension"]
            return ext if ext.startswith(".") else f".{ext}"

        mime = metadata.get("mime_type", "")
        if "json" in mime:
            return ".json"
        if "csv" in mime:
            return ".csv"
        if "html" in mime:
            return ".html"
        if "pdf" in mime:
            return ".pdf"
        if "spreadsheet" in mime or "excel" in mime:
            return ".xlsx"

        # 2. Content Sniffing

        # [String Sniffing]
        if isinstance(data, str):
            sample = data[:1000].strip()

            # HTML Check
            if (
                "<html" in sample.lower()
                or "<!doctype html" in sample.lower()
                or "<body" in sample.lower()
            ):
                return ".html"

            # Markdown Check
            if sample.startswith("# ") or sample.startswith("---") or "\n# " in sample:
                return ".md"

            if any(
                t in sample.lower() for t in ["<div", "<p", "<a href", "<br", "<span"]
            ):
                return ".html"

            # CSV Check
            if "\n" in sample and "," in sample:
                lines = sample.splitlines()
                if len(lines) > 1:
                    first_line_commas = lines[0].count(",")
                    second_line_commas = lines[1].count(",")
                    if (
                        first_line_commas > 0
                        and first_line_commas == second_line_commas
                    ):
                        return ".csv"

            # JSON String Check
            if (sample.startswith("{") and sample.endswith("}")) or (
                sample.startswith("[") and sample.endswith("]")
            ):
                try:
                    json.loads(data)
                    return ".json"
                except:
                    pass

            return ".txt"

        # [Binary Sniffing]
        if isinstance(data, bytes):
            # Magic Numbers (File Header Signature)
            if data.startswith(b"PK\x03\x04"):
                # ZIP format (xlsx, docx, pptx, zip all included)
                return ".zip"
            if data.startswith(b"%PDF"):
                return ".pdf"
            if data.startswith(b"\x89PNG"):
                return ".png"
            if data.startswith(b"\xff\xd8\xff"):
                return ".jpg"
            if data.startswith(b"GIF8"):
                return ".gif"

            return ".bin"

        # [Object Sniffing]
        if isinstance(data, (dict, list)):
            return ".json"

        return ".dat"
