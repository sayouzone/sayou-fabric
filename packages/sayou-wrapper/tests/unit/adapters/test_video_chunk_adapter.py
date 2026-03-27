"""
Unit tests for VideoChunkAdapter.

Covers:
- can_handle(): video_id / sayou:startTime detection, non-match returns 0
- _do_adapt():
  - Video root node (one per video_id, deduplication)
  - VideoSegment node per timed chunk
  - Chunks without startTime skipped
  - Root node carries heavy metadata
  - Segment node carries lightweight attributes + parent reference
  - Multi-video: segments linked to correct roots
"""

import pytest
from sayou.core.ontology import SayouAttribute, SayouClass
from sayou.core.schemas import SayouChunk, SayouOutput

from sayou.wrapper.adapter.video_chunk_adapter import VideoChunkAdapter

VID = "abc123"


def _seg(start, end, text="transcript text", video_id=VID, **extra):
    meta = {
        "video_id": video_id,
        "title": "Test Video",
        SayouAttribute.START_TIME: start,
        SayouAttribute.END_TIME: end,
        "chunk_id": f"seg_{int(start):04d}",
    }
    meta.update(extra)
    return SayouChunk(content=text, metadata=meta)


def _adapter():
    import logging

    a = VideoChunkAdapter()
    a.logger = logging.getLogger("test")
    a._callbacks = []
    a.config = {}
    return a


def _roots(output):
    return [n for n in output.nodes if n.node_class == SayouClass.VIDEO]


def _segments(output):
    return [n for n in output.nodes if n.node_class == SayouClass.VIDEO_SEGMENT]


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_video_id_in_metadata_returns_1(self):
        chunks = [_seg(0.0, 10.0)]
        assert VideoChunkAdapter.can_handle(chunks, "auto") == 1.0

    def test_start_time_key_in_metadata_returns_1(self):
        chunks = [SayouChunk(content="x", metadata={SayouAttribute.START_TIME: 0.0})]
        assert VideoChunkAdapter.can_handle(chunks, "auto") == 1.0

    def test_non_sayou_chunk_returns_zero(self):
        assert VideoChunkAdapter.can_handle([{"video_id": "x"}], "auto") == 0.0

    def test_chunk_without_video_metadata_returns_zero(self):
        plain = SayouChunk(content="hello", metadata={"source": "doc.pdf"})
        assert VideoChunkAdapter.can_handle([plain], "auto") == 0.0

    def test_empty_list_returns_zero(self):
        assert VideoChunkAdapter.can_handle([], "auto") == 0.0


# ---------------------------------------------------------------------------
# Video root node
# ---------------------------------------------------------------------------


class TestVideoRootNode:
    def test_one_root_created(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 10.0), _seg(10.0, 20.0)])
        assert len(_roots(output)) == 1

    def test_root_node_id_contains_video_id(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 10.0)])
        assert VID in _roots(output)[0].node_id

    def test_root_node_class(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 10.0)])
        assert _roots(output)[0].node_class == SayouClass.VIDEO

    def test_root_carries_title(self):
        a = _adapter()
        chunks = [_seg(0.0, 5.0)]
        chunks[0].metadata["title"] = "My Tutorial"
        output = a._do_adapt(chunks)
        assert _roots(output)[0].attributes.get("title") == "My Tutorial"

    def test_root_deduplication_across_segments(self):
        """Multiple segments from the same video → only one root."""
        a = _adapter()
        chunks = [_seg(float(i * 10), float(i * 10 + 10)) for i in range(5)]
        output = a._do_adapt(chunks)
        assert len(_roots(output)) == 1

    def test_two_videos_produce_two_roots(self):
        a = _adapter()
        chunks = [_seg(0.0, 10.0, video_id="vid1"), _seg(0.0, 10.0, video_id="vid2")]
        output = a._do_adapt(chunks)
        assert len(_roots(output)) == 2


# ---------------------------------------------------------------------------
# VideoSegment nodes
# ---------------------------------------------------------------------------


class TestVideoSegmentNodes:
    def test_one_segment_per_timed_chunk(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 10.0), _seg(10.0, 20.0), _seg(20.0, 30.0)])
        assert len(_segments(output)) == 3

    def test_segment_carries_start_time(self):
        a = _adapter()
        output = a._do_adapt([_seg(42.5, 60.0)])
        seg = _segments(output)[0]
        assert seg.attributes.get(SayouAttribute.START_TIME) == 42.5

    def test_segment_carries_end_time(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 15.5)])
        seg = _segments(output)[0]
        assert seg.attributes.get(SayouAttribute.END_TIME) == 15.5

    def test_segment_carries_text(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 5.0, text="Hello everyone.")])
        seg = _segments(output)[0]
        assert seg.attributes.get(SayouAttribute.TEXT) == "Hello everyone."

    def test_segment_parent_node_attribute_set(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 5.0)])
        seg = _segments(output)[0]
        parent_ref = seg.attributes.get("meta:parent_node")
        assert parent_ref is not None
        assert VID in parent_ref

    def test_segment_node_id_contains_video_id(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 5.0)])
        seg = _segments(output)[0]
        assert VID in seg.node_id

    def test_segment_node_class(self):
        a = _adapter()
        output = a._do_adapt([_seg(0.0, 5.0)])
        assert _segments(output)[0].node_class == SayouClass.VIDEO_SEGMENT


# ---------------------------------------------------------------------------
# Chunk without startTime is skipped
# ---------------------------------------------------------------------------


class TestSkipWithoutStartTime:
    def test_chunk_without_start_time_skipped(self):
        a = _adapter()
        meta_only = SayouChunk(
            content="",
            metadata={"video_id": VID, "title": "No timing"},
        )
        output = a._do_adapt([meta_only, _seg(0.0, 10.0)])
        # Only 1 segment — the metadata-only chunk is skipped
        assert len(_segments(output)) == 1

    def test_all_chunks_without_start_time_produces_no_segments(self):
        a = _adapter()
        chunks = [
            SayouChunk(content="x", metadata={"video_id": VID}),
            SayouChunk(content="y", metadata={"video_id": VID}),
        ]
        output = a._do_adapt(chunks)
        assert len(_segments(output)) == 0
        # Root is also not created (no valid segments)
        assert len(_roots(output)) == 0


# ---------------------------------------------------------------------------
# Multi-video
# ---------------------------------------------------------------------------


class TestMultiVideo:
    def test_segments_linked_to_correct_root(self):
        a = _adapter()
        chunks = [
            _seg(0.0, 10.0, video_id="v1"),
            _seg(10.0, 20.0, video_id="v1"),
            _seg(0.0, 15.0, video_id="v2"),
        ]
        output = a._do_adapt(chunks)
        assert len(_roots(output)) == 2
        assert len(_segments(output)) == 3

        v1_segs = [
            s for s in _segments(output) if s.attributes.get("meta:video_id") == "v1"
        ]
        v2_segs = [
            s for s in _segments(output) if s.attributes.get("meta:video_id") == "v2"
        ]
        assert len(v1_segs) == 2
        assert len(v2_segs) == 1
