# ── Setup
"""
Construct a temporal graph from video transcript segments using
`AssemblerPipeline` with `TimelineBuilder`.

`TimelineBuilder` is purpose-built for the YouTube / video connector
output.  It accepts a `SayouOutput` containing `VIDEO` and
`VIDEO_SEGMENT` nodes and produces:

- ``sayou:contains`` edges — from the video root to each segment
- ``sayou:next`` edges — sequential links between segments in
  chronological order (sorted by ``sayou:startTime``)

This graph models the full transcript as a temporal chain, enabling
queries like "what was said between 2:30 and 5:00?" or "which topic
comes after this one?".
"""
import json

from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.assembler.plugins.timeline_builder import TimelineBuilder

pipeline = AssemblerPipeline(extra_builders=[TimelineBuilder])


# ── Build a Video Timeline
"""
Nodes must have:

- Video root:   ``node_class = SayouClass.VIDEO``
- Segments:     ``node_class = SayouClass.VIDEO_SEGMENT``
                ``attributes[SayouAttribute.START_TIME]`` = float (seconds)
                ``attributes["meta:parent_node"]``       = video root node_id
"""
VIDEO_ID = "dQw4w9WgXcQ"

video_root = SayouNode(
    node_id=f"sayou:video:{VIDEO_ID}",
    node_class=SayouClass.VIDEO,
    friendly_name="RAG Pipeline Tutorial",
    attributes={
        "title": "Building a RAG Pipeline with Sayou Fabric",
        "author": "Sayou Zone",
        "duration": "18:42",
        "video_id": VIDEO_ID,
    },
)

# Segments intentionally out of order to demonstrate sorting
segments_raw = [
    (
        f"sayou:video:{VIDEO_ID}:segment:seg003",
        90.0,
        125.0,
        "Now let's look at the Chunking library.",
    ),
    (
        f"sayou:video:{VIDEO_ID}:segment:seg001",
        0.0,
        30.0,
        "Welcome to this tutorial on Sayou Fabric.",
    ),
    (
        f"sayou:video:{VIDEO_ID}:segment:seg004",
        125.0,
        165.0,
        "The Wrapper converts chunks into SayouNodes.",
    ),
    (
        f"sayou:video:{VIDEO_ID}:segment:seg002",
        30.0,
        90.0,
        "Today we'll cover the end-to-end LLM pipeline.",
    ),
    (
        f"sayou:video:{VIDEO_ID}:segment:seg005",
        165.0,
        210.0,
        "Finally, the Loader writes to your target store.",
    ),
]

segment_nodes = [
    SayouNode(
        node_id=seg_id,
        node_class=SayouClass.VIDEO_SEGMENT,
        friendly_name=f"Segment @ {start:.0f}s",
        attributes={
            SayouAttribute.START_TIME: start,
            SayouAttribute.END_TIME: end,
            SayouAttribute.TEXT: text,
            "meta:parent_node": f"sayou:video:{VIDEO_ID}",
        },
    )
    for seg_id, start, end, text in segments_raw
]

output = SayouOutput(
    nodes=[video_root] + segment_nodes,
    metadata={"source": "youtube", "video_id": VIDEO_ID},
)

result = pipeline.run(output, strategy="TimelineBuilder")

print("=== Build a Video Timeline ===")
contains_edges = [e for e in result["edges"] if e["type"] == SayouPredicate.CONTAINS]
next_edges = [e for e in result["edges"] if e["type"] == SayouPredicate.NEXT]

print(f"  Total nodes           : {len(result['nodes'])}")
print(f"  CONTAINS edges        : {len(contains_edges)}  (video → each segment)")
print(f"  NEXT edges            : {len(next_edges)}  (segment → next segment)")


# ── Chronological Order
"""
Segments are sorted by ``sayou:startTime`` before linking.
The input order does not matter.
"""
print("\n=== Chronological Order (NEXT chain) ===")
for e in next_edges:
    src_id = e["source"].split(":")[-1]
    tgt_id = e["target"].split(":")[-1]
    # Find start times
    src_node = next(n for n in result["nodes"] if n["node_id"] == e["source"])
    tgt_node = next(n for n in result["nodes"] if n["node_id"] == e["target"])
    src_t = src_node["attributes"].get(SayouAttribute.START_TIME, "?")
    tgt_t = tgt_node["attributes"].get(SayouAttribute.START_TIME, "?")
    print(f"  [{src_t:5.1f}s] {src_id} → [{tgt_t:5.1f}s] {tgt_id}")


# ── Transcript Reconstruction
"""
Follow the NEXT chain from the first segment to reconstruct the
transcript in order — without relying on segment insertion order.
"""
# Build adjacency map
next_map = {e["source"]: e["target"] for e in next_edges}

# Find the first segment (has no incoming NEXT edge)
all_targets = set(next_map.values())
first_id = next(e["source"] for e in next_edges if e["source"] not in all_targets)

print("\n=== Transcript Reconstruction ===")
current_id = first_id
order = []
while current_id:
    node = next(n for n in result["nodes"] if n["node_id"] == current_id)
    text = node["attributes"].get(SayouAttribute.TEXT, "")
    t = node["attributes"].get(SayouAttribute.START_TIME, 0)
    print(f"  [{t:5.1f}s] {text}")
    order.append(current_id)
    current_id = next_map.get(current_id)


# ── Multi-Video Timeline
"""
When processing multiple videos, each video's segments have a different
``meta:parent_node``.  TimelineBuilder groups them correctly — one chain
per video root.
"""


# ── Save Results
with open("timeline_output.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

print(f"\nSaved timeline graph to 'timeline_output.json'")
