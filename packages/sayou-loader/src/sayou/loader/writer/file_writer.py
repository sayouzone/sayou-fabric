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
        # 1. Handle Directory Destination
        if destination.endswith(os.sep) or (
            os.path.exists(destination) and os.path.isdir(destination)
        ):
            destination = os.path.join(destination, "output.json")
            self._log(f"Destination is a directory. Appended filename: {destination}")

        # 2. Create Parent Directory
        folder = os.path.dirname(destination)
        if folder:
            os.makedirs(folder, exist_ok=True)

        mode = kwargs.get("mode", "w")
        encoding = kwargs.get("encoding", "utf-8")

        ext = os.path.splitext(destination)[1].lower()

        try:
            # 3. Determine Content & Mode

            # Case A: Binary Data
            if isinstance(input_data, bytes):
                content = input_data
                mode = "wb"
                encoding = None

            # Case B: JSON (Explicit .json extension OR Dict/List structure)
            elif ext == ".json" or isinstance(input_data, (dict, list, tuple)):
                content = json.dumps(
                    input_data, indent=2, ensure_ascii=False, default=self._serializer
                )

            # Case C: Simple String (Not targeting JSON)
            elif isinstance(input_data, str):
                content = input_data

            # Case D: Fallback (Pickle)
            else:
                if not destination.endswith(".pkl"):
                    destination += ".pkl"

                self._log(
                    f"Unknown type {type(input_data)}. Falling back to pickle: {destination}"
                )
                with open(destination, "wb") as f:
                    pickle.dump(input_data, f)
                return True

            # 4. Write File (Text/JSON/Bytes)
            with open(destination, mode, encoding=encoding) as f:
                f.write(content)

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
