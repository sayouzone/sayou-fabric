import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY
from sayou.core.schemas import SayouOutput

from .core.exceptions import AdaptationError
from .interfaces.base_adapter import BaseAdapter


class WrapperPipeline(BaseComponent):
    """
    Orchestrates the data wrapping process.

    Acts as the final gateway before data storage. Receives processed data
    (usually chunks) and delegates it to a specific Adapter to convert it
    into the standard SayouNode format.
    """

    component_name = "WrapperPipeline"

    def __init__(
        self,
        extra_adapters: Optional[List[Type[BaseAdapter]]] = None,
        **kwargs,
    ):
        """
        Initialize the pipeline with default and optional custom adapters.

        Args:
            extra_adapters: Custom adapter classes to register.
            **kwargs: Global configuration passed to all adapters.
        """
        super().__init__()

        self.adapters_cls_map: Dict[str, Type[BaseAdapter]] = {}

        self._register("sayou.wrapper.adapter")
        self._register("sayou.wrapper.plugins")

        self._load_from_registry()

        if extra_adapters:
            for cls in extra_adapters:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls) -> None:
        """Register a user-provided adapter class."""
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid adapter: {cls!r}. "
                "Pass the class itself (e.g. MyAdapter), not an instance."
            )
        name = getattr(cls, "component_name", cls.__name__)
        self.adapters_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> SayouOutput:
        """
        One-line facade: instantiate the pipeline and run immediately.

        Args:
            input_data: Raw input data (typically List[SayouChunk] or dict).
            strategy: Explicit adapter strategy; 'auto' for score-based selection.
            **kwargs: Configuration forwarded to the pipeline and adapter.

        Returns:
            SayouOutput containing standardised SayouNodes.
        """
        instance = cls(**kwargs)
        return instance.run(input_data, strategy, **kwargs)

    def _register(self, package_name: str) -> None:
        """Auto-discover and import all modules under *package_name*."""
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
                            f"Failed to import module {full_name}: {e}",
                            level="warning",
                        )
        except ImportError as e:
            self._log(f"Package not found: {package_name} ({e})", level="debug")

    def _load_from_registry(self) -> None:
        """Populate the local adapter map from the global component registry."""
        if "adapter" in COMPONENT_REGISTRY:
            self.adapters_cls_map.update(COMPONENT_REGISTRY["adapter"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs) -> None:
        """
        Finalise configuration after all adapters are registered.

        Args:
            **kwargs: Additional configuration merged into global_config.
        """
        self.global_config.update(kwargs)
        n = len(self.adapters_cls_map)
        self._log(f"WrapperPipeline initialised with {n} adapter(s).")

    def run(
        self,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> SayouOutput:
        """
        Execute the wrapping strategy.

        Args:
            input_data: Input data (e.g. List[SayouChunk] or raw dict).
            strategy: Adapter strategy key, or 'auto' for score-based selection.
            **kwargs: Forwarded to the selected adapter.

        Returns:
            SayouOutput with standardised SayouNodes.

        Raises:
            AdaptationError: If no suitable adapter is found or execution fails.
        """
        if not input_data:
            return SayouOutput(nodes=[])

        run_config = {**self.global_config, **kwargs}

        self._emit("on_start", input_data={"strategy": strategy})

        adapter_cls = self._resolve_adapter(input_data, strategy)

        if not adapter_cls:
            msg = f"No suitable adapter found for strategy={strategy!r}."
            self._emit("on_error", error=Exception(msg))
            raise AdaptationError(msg)

        adapter = adapter_cls()
        for cb in self._callbacks:
            adapter.add_callback(cb)
        adapter.initialize(**run_config)

        self._log(f"Routing to adapter: {adapter.component_name}")

        try:
            output = adapter.adapt(input_data, **kwargs)
            self._emit("on_finish", result_data={"output": output}, success=True)
            return output
        except Exception as e:
            self._emit("on_error", error=e)
            raise

    def _resolve_adapter(
        self,
        raw_data: Any,
        strategy: str,
    ) -> Optional[Type[BaseAdapter]]:
        """
        Select the best adapter by explicit name or highest can_handle() score.

        Args:
            raw_data: Input data used for scoring.
            strategy: Requested strategy key.

        Returns:
            The winning adapter class, or None if all scores are zero.
        """
        if strategy in self.adapters_cls_map:
            return self.adapters_cls_map[strategy]

        best_score = 0.0
        best_cls: Optional[Type[BaseAdapter]] = None

        for cls in set(self.adapters_cls_map.values()):
            try:
                score = cls.can_handle(raw_data, strategy)
                if score > best_score:
                    best_score = score
                    best_cls = cls
            except Exception as e:
                self._log(f"{cls.__name__}.can_handle raised: {e}", level="warning")

        if best_cls and best_score > 0.0:
            return best_cls

        self._log("No suitable adapter found (all scores zero).", level="warning")
        return None
