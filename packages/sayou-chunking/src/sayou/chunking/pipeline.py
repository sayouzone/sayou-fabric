import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY
from sayou.core.schemas import SayouChunk

from .core.exceptions import SplitterError
from .interfaces.base_splitter import BaseSplitter


class ChunkingPipeline(BaseComponent):
    """
    Orchestrates the text chunking process via dynamic registry.

    This pipeline acts as a factory and dispatcher, routing input data
    to the most appropriate splitter strategy (Recursive, Semantic, Markdown, etc.)
    based on 'can_handle' scores or explicit strategy requests.
    """

    component_name = "ChunkingPipeline"

    def __init__(
        self, extra_splitters: Optional[List[Type[BaseSplitter]]] = None, **kwargs
    ):
        """
        Initialize the pipeline and discover available splitters.

        Args:
            extra_splitters: List of custom splitter CLASSES (not instances).
            **kwargs: Global configuration.
        """
        super().__init__()

        self.splitters_cls_map: Dict[str, Type[BaseSplitter]] = {}

        self._register("sayou.chunking.splitter")
        self._register("sayou.chunking.plugins")

        self._load_from_registry()

        if extra_splitters:
            for cls in extra_splitters:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid splitter: {cls}. "
                f"Please pass the CLASS itself (e.g., MySplitter), not an instance (MySplitter())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.splitters_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> List[SayouChunk]:
        """
        [Facade] One-line execution method.

        Instantiates the pipeline and runs the chunking process immediately.

        Args:
            input_data (Any): Input text or data structure to chunk.
            strategy (str): Splitting strategy hint (default: 'auto').
            **kwargs: Configuration options (chunk_size, etc.).

        Returns:
            List[SayouChunk]: A list of generated text chunks.
        """
        instance = cls(**kwargs)
        return instance.run(input_data, strategy, **kwargs)

    def _register(self, package_name: str):
        """
        Automatically discovers and registers plugins from the specified package.

        Args:
            package_name (str): The dot-separated package path.
        """
        try:
            package = importlib.import_module(package_name)
            if hasattr(package, "__path__"):
                for _, name, _ in pkgutil.iter_modules(package.__path__):
                    full_name = f"{package_name}.{name}"
                    try:
                        importlib.import_module(full_name)
                        self._log(f"Discovered module: {full_name}", level="debug")
                    except Exception as e:
                        self._log(
                            f"Failed to import module {full_name}: {e}", level="warning"
                        )
        except ImportError as e:
            self._log(f"Package not found: {package_name} ({e})", level="debug")

    def _load_from_registry(self):
        """
        Populates local component maps from the global registry.
        """
        if "splitter" in COMPONENT_REGISTRY:
            self.splitters_cls_map.update(COMPONENT_REGISTRY["splitter"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all sub-components (Splitters).

        Updates global configuration and logs status.
        Actual component instantiation happens lazily during run().

        Args:
            **kwargs: Updates to the global configuration.
        """
        self.global_config.update(kwargs)

        n_split = len(self.splitters_cls_map)
        self._log(f"ChunkingPipeline initialized. Available: {n_split} Splitters")

    def run(
        self,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> List[SayouChunk]:
        """
        Execute the chunking strategy on the input data.

        Orchestration Flow:
        1. Merge Configurations (Global + Runtime).
        2. Resolve Splitter (Strategy > Score).
        3. Instantiate & Initialize Splitter.
        4. Execute Splitter.

        Args:
            input_data (Any): Text string, Dict, or SayouBlock list.
            strategy (str): The splitting strategy to use (default: 'auto').
            **kwargs: Runtime configuration options.

        Returns:
            List[SayouChunk]: A list of generated Chunk objects.

        Raises:
            SplitterError: If no suitable splitter is found or execution fails.
        """
        if not input_data:
            return []

        # 1. Config Merge
        run_config = {**self.global_config, **kwargs}

        self._emit("on_start", input_data={"strategy": strategy})

        # 2. Resolve Splitter
        splitter_cls = self._resolve_splitter(input_data, strategy)

        if not splitter_cls:
            error_msg = f"No suitable splitter found for strategy='{strategy}'"
            self._emit("on_error", error=Exception(error_msg))
            raise SplitterError(error_msg)

        # 3. Instantiate & Initialize (Lazy Loading)
        splitter = splitter_cls()
        splitter.initialize(**run_config)

        self._log(f"Routing to splitter: {splitter.component_name}")

        try:
            # 4. Execute
            chunks = splitter.split(input_data)

            self._emit(
                "on_finish", result_data={"chunks_count": len(chunks)}, success=True
            )
            return chunks

        except Exception as e:
            self._emit("on_error", error=e)
            raise e

    def _resolve_splitter(
        self, raw_data: Any, strategy: str
    ) -> Optional[Type[BaseSplitter]]:
        """
        Selects the best splitter based on score or explicit type match.

        Args:
            raw_data (Any): The input data to evaluate.
            strategy (str): The requested strategy name.

        Returns:
            Optional[Type[BaseSplitter]]: The selected splitter class or None.
        """
        best_score = 0.0
        best_cls = None

        # 1. Score-based Check (can_handle)
        for cls in set(self.splitters_cls_map.values()):
            try:
                score = cls.can_handle(raw_data, strategy)
                if score > best_score:
                    best_score = score
                    best_cls = cls
            except Exception:
                continue

        if best_cls and best_score > 0.0:
            return best_cls

        # 2. Type-based Fallback (Explicit String Match via Registry Key)
        if strategy in self.splitters_cls_map:
            return self.splitters_cls_map[strategy]

        return None
