import json
import os
import pickle
from typing import Any

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter


@register_component("writer")
class FileWriter(BaseWriter):
    """
    Writes data to the local file system.

    Automatically handles format serialization:
    - Dict/List -> JSON
    - Str -> Text file
    - Bytes -> Binary file
    - Others -> Pickle
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
        """
        Write data to file. Creates parent directories if they don't exist.
        """
        # 1. Directory Setup
        if destination.endswith(os.sep) or (
            os.path.exists(destination) and os.path.isdir(destination)
        ):
            destination = os.path.join(destination, "output.json")
            self._log(f"Destination is a directory. Defaulting to: {destination}")

        folder = os.path.dirname(destination)
        if folder:
            os.makedirs(folder, exist_ok=True)

        encoding = kwargs.get("encoding", "utf-8")

        try:
            # 2. Wrapped Content Detection
            real_content = None
            metadata = {}

            # 1) Type: List
            if isinstance(input_data, list) and len(input_data) == 1:
                item = input_data[0]
                if isinstance(item, dict) and isinstance(item.get("content"), bytes):
                    real_content = item["content"]
                    metadata = item.get("meta") or item.get("metadata", {})

            # 2) Type: Dict
            elif isinstance(input_data, dict) and isinstance(
                input_data.get("content"), bytes
            ):
                real_content = input_data["content"]
                metadata = input_data.get("meta") or input_data.get("metadata", {})

            # 3) Discovery of a wrapped binary
            if real_content is not None:
                input_data = real_content
                new_ext = metadata.get("extension", "")
                suggested_name = metadata.get("suggested_filename", "")

                if suggested_name:
                    destination = os.path.join(
                        os.path.dirname(destination), suggested_name
                    )
                elif new_ext and destination.endswith(".json"):
                    destination = destination.replace(".json", new_ext)

                self._log(
                    f"📦 Detected Wrapped Binary. Saving as raw file: {destination}"
                )

            ext = os.path.splitext(destination)[1].lower()

            # Case A: Binary Data (Docs, Xlsx, Images...)
            if isinstance(input_data, bytes):
                with open(destination, "wb") as f:
                    f.write(input_data)

            # Case B: JSON
            elif ext == ".json" or isinstance(input_data, (dict, list, tuple)):
                content = json.dumps(
                    input_data, indent=2, ensure_ascii=False, default=str
                )
                with open(destination, "w", encoding=encoding) as f:
                    f.write(content)

            # Case C: Simple String (CSV, TXT)
            elif isinstance(input_data, str):
                with open(destination, "w", encoding=encoding) as f:
                    f.write(input_data)

            # Case D: Fallback
            else:
                if not destination.endswith(".pkl"):
                    destination += ".pkl"
                with open(destination, "wb") as f:
                    pickle.dump(input_data, f)

            self._log(f"💾 Saved to {destination}")
            return True

        except Exception as e:
            self._log(f"Write failed: {e}", level="error")
            raise e

    def _serializer(self, obj):
        """
        Helper: Custom object serializer for JSON.
        Handles SayouBlock, SayouNode, etc.
        """
        if hasattr(obj, "to_dict"):
            return obj.to_dict()

        if hasattr(obj, "__dict__"):
            return obj.__dict__

        return str(obj)
