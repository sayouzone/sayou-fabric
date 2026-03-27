# ── Setup
"""
Convert YouTube transcript SayouChunks into a Video knowledge graph using
`WrapperPipeline` with `VideoChunkAdapter`.

`VideoChunkAdapter` is the bridge between `sayou-connector`'s YouTube
fetchers and `sayou-assembler`'s `TimelineBuilder`.

It produces two node types:

**sayou:Video** (one per unique ``video_id``)
    Carries all heavy metadata: title, description, author, URL, view count, …
    Created the first time a segment from that video is encountered.

**sayou:VideoSegment** (one per transcript chunk)
    Lightweight — carries only the transcript text, start time, end time,
    and a back-reference to the parent Video node.
    Skipped if the chunk has no ``sayou:startTime`` in its metadata.

This separation keeps the Video node small (metadata only) while letting
the segment chain grow arbitrarily large, and allows `TimelineBuilder` to
link segments into a chronological ``sayou:next`` chain.

``VideoChunkAdapter.can_handle()`` looks for ``video_id`` or
``sayou:startTime`` in the first chunk's metadata and scores 1.0 only when
found, so auto-routing is precise.
"""
import json

from sayou.core.ontology import SayouAttribute, SayouClass
from sayou.core.schemas import SayouChunk

from sayou.wrapper.adapter.video_chunk_adapter import VideoChunkAdapter
from sayou.wrapper.pipeline import WrapperPipeline

pipeline = WrapperPipeline(extra_adapters=[VideoChunkAdapter])


# ── Sample Video Chunks
"""
These chunks replicate the output of `sayou-connector`'s
`YoutubePublicFetcher` → `ChunkingPipeline` (RecordNormalizer path).

In production the YouTube connector populates every metadata key below
automatically.  The minimum required keys are:

- ``video_id``          — identifies the parent Video node
- ``sayou:startTime``   — marks this as a timed segment (float, seconds)
- ``sayou:endTime``     — segment end time
"""
VIDEO_ID = "dQw4w9WgXcQ"
VIDEO_META = {
    "video_id": VIDEO_ID,
    "title": "Sayou Fabric Tutorial — End-to-End LLM Pipeline",
    "author": "Sayou Zone",
    "url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
    "description": "A complete walkthrough of all eight Sayou Fabric libraries.",
    "keywords": ["llm", "rag", "data-pipeline", "python"],
    "view_count": 42000,
    "publish_date": "2024-04-01",
    "thumbnail_url": f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg",
}

# Transcript segments — intentionally out of chronological order
# to demonstrate that VideoChunkAdapter handles ordering correctly.
raw_segments = [
    (45.0, 70.0, "Let me show you how ChunkingPipeline splits text."),
    (0.0, 18.0, "Welcome to this tutorial on Sayou Fabric."),
    (70.0, 95.0, "The WrapperPipeline maps chunks into SayouNodes."),
    (18.0, 45.0, "Today we'll cover the full end-to-end data pipeline."),
    (95.0, 115.0, "Finally, LoaderPipeline writes nodes to your target store."),
]

chunks = [
    SayouChunk(
        content=text,
        metadata={
            **VIDEO_META,
            SayouAttribute.START_TIME: start,
            SayouAttribute.END_TIME: end,
            "chunk_id": f"seg_{int(start):04d}",
        },
    )
    for start, end, text in raw_segments
]


# ── Basic Conversion
"""
Pass the chunk list with ``strategy="video_chunk"``.

Returns one Video root node + one VideoSegment node per chunk.
The adapter skips any chunk that lacks ``sayou:startTime``.
"""
output = pipeline.run(chunks, strategy="video_chunk")

video_nodes = [n for n in output.nodes if n.node_class == SayouClass.VIDEO]
segment_nodes = [n for n in output.nodes if n.node_class == SayouClass.VIDEO_SEGMENT]

print("=== Basic Conversion ===")
print(f"  Input chunks    : {len(chunks)}")
print(f"  Video roots     : {len(video_nodes)}")
print(f"  Video segments  : {len(segment_nodes)}")


# ── Video Root Node
"""
The Video root carries all heavy metadata and is created once per
unique ``video_id``.  Re-running with additional segments for the same
video does not create duplicate roots.
"""
print("\n=== Video Root Node ===")
root = video_nodes[0]
print(f"  node_id    : {root.node_id}")
print(f"  node_class : {root.node_class}")
for key in ["title", "author", "url", "view_count", "keywords"]:
    val = root.attributes.get(key)
    print(f"  {key:12s}: {val}")


# ── Segment Nodes
"""
Each segment node is lightweight:
- ``schema:text``      — transcript text
- ``sayou:startTime``  — segment start (float, seconds)
- ``sayou:endTime``    — segment end   (float, seconds)
- ``meta:video_id``    — back-reference to the parent video
- ``meta:parent_node`` — full URI of the parent Video node (for TimelineBuilder)
"""
print("\n=== Segment Nodes (chronological order of creation) ===")
for seg in segment_nodes:
    start = seg.attributes.get(SayouAttribute.START_TIME)
    end = seg.attributes.get(SayouAttribute.END_TIME)
    text = str(seg.attributes.get(SayouAttribute.TEXT, ""))[:45]
    print(f"  [{start:6.1f}s – {end:6.1f}s]  {text!r}")


# ── Multi-video Handling
"""
Pass chunks from multiple videos in a single call.
The adapter groups them correctly — one root node per video_id,
segments linked to their respective parent.
"""
VIDEO_ID_2 = "xvFZjo5PgG0"
chunks_v2 = [
    SayouChunk(
        content="Introduction to RAG with vector databases.",
        metadata={
            "video_id": VIDEO_ID_2,
            "title": "RAG Deep Dive",
            "author": "Sayou Zone",
            SayouAttribute.START_TIME: 0.0,
            SayouAttribute.END_TIME: 25.0,
            "chunk_id": "v2_seg_0000",
        },
    ),
    SayouChunk(
        content="Choosing the right vector database for your use case.",
        metadata={
            "video_id": VIDEO_ID_2,
            "title": "RAG Deep Dive",
            "author": "Sayou Zone",
            SayouAttribute.START_TIME: 25.0,
            SayouAttribute.END_TIME: 55.0,
            "chunk_id": "v2_seg_0025",
        },
    ),
]

mixed_output = pipeline.run(chunks + chunks_v2, strategy="video_chunk")

roots = [n for n in mixed_output.nodes if n.node_class == SayouClass.VIDEO]
segments = [n for n in mixed_output.nodes if n.node_class == SayouClass.VIDEO_SEGMENT]

print("\n=== Multi-video Handling ===")
print(f"  Total nodes    : {len(mixed_output.nodes)}")
print(f"  Video roots    : {len(roots)}")
print(f"  Total segments : {len(segments)}")
for root in roots:
    segs = [
        n
        for n in segments
        if n.attributes.get("meta:video_id") == root.attributes.get("original_id")
    ]
    print(f"  [{root.attributes.get('title', root.node_id)}]  {len(segs)} segment(s)")


# ── Chunks Without Start Time Are Skipped
"""
Any chunk missing ``sayou:startTime`` is silently skipped.
This is common for metadata-only chunks produced by some connectors.
"""
metadata_only = SayouChunk(
    content="",
    metadata={"video_id": VIDEO_ID, "title": "No timing info"},
)

output_skip = pipeline.run([metadata_only] + chunks[:2], strategy="video_chunk")
seg_count = sum(
    1 for n in output_skip.nodes if n.node_class == SayouClass.VIDEO_SEGMENT
)

print("\n=== Chunks Without Start Time Skipped ===")
print(f"  Input chunks   : 3  (1 metadata-only + 2 timed)")
print(f"  Segment nodes  : {seg_count}  (metadata-only chunk skipped)")


# ── Downstream: feed into TimelineBuilder
"""
Pass the output directly to AssemblerPipeline + TimelineBuilder to build
the temporal CONTAINS / NEXT chain:

    from sayou.assembler.pipeline import AssemblerPipeline
    from sayou.assembler.plugins.timeline_builder import TimelineBuilder

    timeline = AssemblerPipeline.process(
        output,
        strategy="TimelineBuilder",
        extra_builders=[TimelineBuilder],
    )
    # timeline["edges"] now contains sayou:contains and sayou:next edges
"""


# ── Save Results
result = {
    "nodes": [
        {
            "node_id": n.node_id,
            "node_class": n.node_class,
            "attributes": {
                k: v
                for k, v in n.attributes.items()
                if k
                in (
                    "title",
                    "author",
                    SayouAttribute.START_TIME,
                    SayouAttribute.END_TIME,
                    SayouAttribute.TEXT,
                    "meta:parent_node",
                )
            },
        }
        for n in output.nodes
    ]
}
with open("video_chunk_nodes.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

print(f"\nSaved {len(output.nodes)} node(s) to 'video_chunk_nodes.json'")
