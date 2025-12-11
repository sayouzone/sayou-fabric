import importlib
import pkgutil
from typing import Any, Dict, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY

from .core.exceptions import ParserError
from .interfaces.base_converter import BaseConverter
from .interfaces.base_ocr import BaseOCR
from .interfaces.base_parser import BaseDocumentParser
from .models import Document


class DocumentPipeline(BaseComponent):
    """
    Orchestrates the document parsing process using a dynamic registry system.

    Features:
    - Dynamic Parser Discovery via Registry.
    - Score-based Routing (Magic Bytes detection).
    - Unified Image-to-PDF pre-processing.
    - Runtime OCR Engine Injection.
    """

    component_name = "DocumentPipeline"

    def __init__(self, **kwargs):
        """
        Initializes the pipeline and discovers available parsers.

        Args:
            ocr_engine (Optional[BaseOCR]): Pre-initialized OCR engine instance.
            use_default_ocr (bool): If True, attempts to load TesseractOCR if no engine is provided.
            **kwargs: Additional configuration passed to components.
        """
        super().__init__()

        self.converter_cls_map: Dict[str, Type[BaseConverter]] = {}
        self.ocr_cls_map: Dict[str, Type[BaseOCR]] = {}
        self.parser_cls_map: Dict[str, Type[BaseDocumentParser]] = {}

        self._register("sayou.document.converter")
        self._register("sayou.document.ocr")
        self._register("sayou.document.parser")
        self._register("sayou.document.plugins")

        self._load_from_registry()

        self.global_config = kwargs

    def _register(self, package_name: str):
        """
        Automatically discovers and registers plugins from the specified package.
        """
        try:
            package = importlib.import_module(package_name)
            if hasattr(package, "__path__"):
                for _, name, _ in pkgutil.iter_modules(package.__path__):
                    full_name = f"{package_name}.{name}"
                    try:
                        importlib.import_module(full_name)
                    except Exception as e:
                        self._log(
                            f"Failed to import module {full_name}: {e}", level="warning"
                        )
        except ImportError as e:
            self._log(f"Package not found: {package_name} ({e})", level="debug")

    def _load_from_registry(self):
        """
        Populates local parser map from the global registry.
        """
        if "converter" in COMPONENT_REGISTRY:
            self.converter_cls_map.update(COMPONENT_REGISTRY["converter"])

        if "ocr" in COMPONENT_REGISTRY:
            self.ocr_cls_map.update(COMPONENT_REGISTRY["ocr"])

        if "parser" in COMPONENT_REGISTRY:
            self.parser_cls_map.update(COMPONENT_REGISTRY["parser"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all registered parsers, converter, and the OCR engine.
        """
        self.global_config.update(kwargs)
        total_plugins = (
            len(self.converter_cls_map)
            + len(self.ocr_cls_map)
            + len(self.parser_cls_map)
        )
        self._log(f"DocumentPipeline initialized. Loaded Plugins: {total_plugins}")

    def run(self, file_bytes: bytes, file_name: str, **kwargs) -> Optional[Document]:
        """
        Executes the document parsing pipeline.

        1. Handles Image -> PDF conversion if applicable.
        2. Selects the appropriate Parser class using Score-based routing (can_handle).
        3. Instantiates the Parser and injects the OCR engine.
        4. Parses and returns the Document.

        Args:
            file_bytes (bytes): Binary content of the file.
            file_name (str): Original filename.
            **kwargs: Runtime options (e.g., tesseract_path, ocr_dpi).

        Returns:
            Optional[Document]: The parsed document or None on failure.
        """
        if not file_bytes:
            raise ParserError("Input file bytes are empty.")

        run_config = {**self.global_config, **kwargs}

        self._emit("on_start", input_data={"filename": file_name})

        # ---------------------------------------------------------
        # Phase 1: Pre-processing (Converter)
        # ---------------------------------------------------------
        converter_cls = self._resolve_component(
            self.converter_cls_map, file_bytes, file_name
        )

        if converter_cls:
            self._log(f"Converter selected: {converter_cls.component_name}")
            converter = converter_cls()
            converter.initialize(**run_config)

            try:
                converted = converter.convert(file_bytes, file_name, **run_config)
                if converted:
                    file_bytes = converted
                    file_name = f"{file_name}.pdf"
            except Exception as e:
                self._log(f"Conversion warning: {e}", level="warning")
                raise ParserError(f"Failed to convert image {file_name}: {e}")

        # ---------------------------------------------------------
        # Phase 2: OCR Engine Resolution
        # ---------------------------------------------------------
        ocr_cls = self._resolve_component(self.ocr_cls_map, b"", "default")

        ocr_instance = None
        if ocr_cls:
            self._log(f"OCR Engine selected: {ocr_cls.component_name}")
            ocr_instance = ocr_cls()
            ocr_instance.initialize(**run_config)

        # ---------------------------------------------------------
        # Phase 3: Parser Selection & Execution
        # ---------------------------------------------------------
        parser_cls = self._resolve_component(self.parser_cls_map, file_bytes, file_name)

        if not parser_cls:
            raise ParserError(f"No suitable parser found for {file_name}")

        self._log(f"Routing '{file_name}' to {parser_cls.component_name}...")

        parser = parser_cls(ocr_engine=ocr_instance)
        parser.initialize(**run_config)

        try:
            doc = parser.parse(file_bytes, file_name, **run_config)
            self._emit("on_finish", result_data=doc, success=True)
            return doc
        except Exception as e:
            self._emit("on_error", error=e)
            raise e

    def _resolve_component(
        self, cls_map: Dict[str, Type[Any]], file_bytes: bytes, identifier: str
    ) -> Optional[Type[Any]]:
        """
        Selects the best parser class based on magic bytes and filename.
        """
        best_score = 0.0
        best_cls = None

        for cls in set(cls_map.values()):
            try:
                score = cls.can_handle(file_bytes, identifier)
                if score > best_score:
                    best_score = score
                    best_cls = cls
            except Exception:
                continue

        if best_cls and best_score > 0.1:
            return best_cls

        return None
