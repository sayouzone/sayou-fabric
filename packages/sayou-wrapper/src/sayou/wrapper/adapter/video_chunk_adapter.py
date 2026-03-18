from typing import Any, Dict, List

from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.registry import register_component
from sayou.core.schemas import SayouChunk, SayouNode, SayouOutput

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class VideoChunkAdapter(BaseAdapter):
    """
    (Tier 2) Specialized Adapter for YouTube Video Chunks.

    Splits metadata into a Root 'Video' Node and creates lightweight
    'VideoSegment' Nodes for each transcript chunk.
    """

    component_name = "VideoChunkAdapter"
    SUPPORTED_TYPES = ["video_chunk"]

    HEAVY_KEYS = [
        "description",
        "keywords",
        "thumbnail_url",
        "author",
        "publish_date",
        "view_count",
        "url",
        "json_path",
        "chunk_type",
        "chunk_id_suffix",
        "item_count",
        "index_start",
        "index_end",
    ]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if isinstance(input_data, list) and input_data:
            first_item = input_data[0]
            if isinstance(first_item, SayouChunk):
                meta = first_item.metadata
                if "video_id" in meta or "sayou:startTime" in meta:
                    return 1.0
        return 0.0

    def _do_adapt(self, input_data: List[SayouChunk], **kwargs) -> SayouOutput:
        """
        Converts chunks to Video/VideoSegment nodes.
        """
        nodes = []
        created_video_roots = set()

        for chunk in input_data:
            meta = chunk.metadata.copy()

            if SayouAttribute.START_TIME not in meta:
                continue

            video_id = meta.get("video_id", "unknown")
            chunk_suffix = meta.get("chunk_id", f"{id(chunk)}")

            # ---------------------------------------------------------
            # 1. Create Root Video Node
            # ---------------------------------------------------------
            if video_id not in created_video_roots:
                root_attrs = {
                    k: v
                    for k, v in meta.items()
                    if k not in [SayouAttribute.START_TIME, SayouAttribute.END_TIME]
                }
                root_attrs["original_id"] = video_id

                root_node = SayouNode(
                    node_id=f"sayou:video:{video_id}",
                    node_class=SayouClass.VIDEO,
                    friendly_name=f"VIDEO [{meta.get('title', video_id)}]",
                    attributes=root_attrs,
                )
                nodes.append(root_node)
                created_video_roots.add(video_id)

            # ---------------------------------------------------------
            # 2. Create Child Segment Node (Lightweight)
            # ---------------------------------------------------------
            segment_attrs = {
                SayouAttribute.TEXT: chunk.content,
                SayouAttribute.START_TIME: meta.get(SayouAttribute.START_TIME),
                SayouAttribute.END_TIME: meta.get(SayouAttribute.END_TIME),
                "meta:video_id": video_id,
                "meta:parent_node": f"sayou:video:{video_id}",
            }

            start_s = meta.get(SayouAttribute.START_TIME, 0)

            node = SayouNode(
                node_id=f"sayou:video:{video_id}:segment:{chunk_suffix}",
                node_class=SayouClass.VIDEO_SEGMENT,
                friendly_name=f"SEGMENT [{start_s}s]",
                attributes=segment_attrs,
            )
            nodes.append(node)

        return SayouOutput(nodes=nodes)
