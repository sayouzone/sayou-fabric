from typing import Any, Callable, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class MetadataAdapter(BaseAdapter):
    """
    (Tier 2) Generic Metadata Enricher.
    Applies external functions to content and stores results as node attributes.
    """

    component_name = "MetadataAdapter"
    SUPPORTED_TYPES = ["metadata"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["metadata"]:
            return 1.0
        return 0.0

    def _do_adapt(self, input_data: List[Dict[str, Any]], **kwargs) -> SayouOutput:
        """
        [Stateless Logic]
        Iterates through input data, applies injected functions, and updates attributes.
        """
        metadata_map: Dict[str, Callable[[str], Any]] = kwargs.get("metadata_map", {})

        use_stub = kwargs.get("use_stub", False)

        nodes = []

        for i, item in enumerate(input_data):
            content = item.get("content", "")
            meta = item.get("metadata", {})
            node_id = meta.get("chunk_id") or meta.get("id") or f"chunk_{i}"

            attributes = {"schema:text": content, **meta}

            if content and isinstance(content, str):
                for attr_key, func in metadata_map.items():
                    if callable(func):
                        try:
                            result = func(content)
                            attributes[attr_key] = result
                        except Exception as e:
                            self._log(
                                f"Enrichment failed for '{attr_key}': {e}",
                                level="warning",
                            )
                            attributes[attr_key] = None

                if not metadata_map and use_stub:
                    attributes["summary"] = f"[Stub Summary] {content[:20]}..."
                    attributes["keywords"] = ["stub", "test", "keyword"]

            node = SayouNode(
                node_id=node_id,
                node_class="Chunk",
                friendly_name=meta.get("title") or f"Chunk {i}",
                attributes=attributes,
            )
            nodes.append(node)

        return SayouOutput(nodes=nodes)
