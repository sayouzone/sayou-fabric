from typing import Any, Dict, List

from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.registry import register_component
from sayou.core.schemas import SayouOutput

from ..interfaces.base_builder import BaseBuilder


@register_component("builder")
class TimelineBuilder(BaseBuilder):
    """
    Constructs a Temporal Graph (Timeline).
    Links segments sequentially and connects them to their parent container.
    """

    component_name = "TimelineBuilder"
    SUPPORTED_TYPES = ["timeline"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if isinstance(input_data, SayouOutput):
            if any(n.node_class == SayouClass.VIDEO_SEGMENT for n in input_data.nodes):
                return 1.0
        elif isinstance(input_data, dict) and "nodes" in input_data:
            nodes = input_data.get("nodes", [])
            if nodes and isinstance(nodes[0], dict):
                if nodes[0].get("node_class") == SayouClass.VIDEO_SEGMENT:
                    return 1.0
        return 0.0

    def _do_build(self, data: SayouOutput) -> Dict[str, Any]:
        nodes = data.nodes
        edges = []

        # 1. Grouping by Parent
        grouped_segments: Dict[str, List] = {}

        for node in nodes:
            if node.node_class == SayouClass.VIDEO_SEGMENT:
                parent = node.attributes.get("meta:parent_node")
                if parent:
                    if parent not in grouped_segments:
                        grouped_segments[parent] = []
                    grouped_segments[parent].append(node)

        # 2. Sort & Linking
        for parent_id, group in grouped_segments.items():
            group.sort(
                key=lambda x: float(x.attributes.get(SayouAttribute.START_TIME) or 0.0)
            )

            for i, segment in enumerate(group):
                # Relation 1: Parent -> Segment (CONTAINS)
                edges.append(
                    {
                        "source": parent_id,
                        "target": segment.node_id,
                        "type": SayouPredicate.CONTAINS,
                    }
                )

                # Relation 2: Segment -> Next Segment (NEXT)
                if i < len(group) - 1:
                    edges.append(
                        {
                            "source": segment.node_id,
                            "target": group[i + 1].node_id,
                            "type": SayouPredicate.NEXT,
                        }
                    )

        return {
            "nodes": [n.model_dump(exclude={"relationships"}) for n in nodes],
            "edges": edges,
            "metadata": data.metadata,
        }
