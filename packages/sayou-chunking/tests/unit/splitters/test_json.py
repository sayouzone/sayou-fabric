"""
Unit tests for JsonSplitter.

Contract:
- can_handle returns 1.0 for strategy in SUPPORTED_TYPES.
- can_handle returns 1.0 when block.type is "json" or "record".
- List input: items are batched until the serialised size exceeds chunk_size.
- Dict input: key-value pairs are batched; oversized values are split recursively.
- String input that is valid JSON is parsed and then split.
- Invalid JSON / non-JSON strings return an empty list.
- Each produced chunk carries chunk_type metadata ("json_list" or "json_object").
"""

import json

import pytest

from sayou.chunking.plugins.json_splitter import JsonSplitter
from sayou.core.schemas import SayouBlock


def _block(content, *, chunk_size: int = 100, block_type: str = "text") -> SayouBlock:
    if not isinstance(content, str):
        content = json.dumps(content)
    return SayouBlock(
        type=block_type,
        content=content,
        metadata={"config": {"chunk_size": chunk_size}},
    )


def _splitter() -> JsonSplitter:
    s = JsonSplitter()
    s.initialize()
    return s


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    @pytest.mark.parametrize("strategy", ["json", "dict", "record", "list"])
    def test_supported_strategies_return_one(self, strategy):
        block = SayouBlock(type="text", content="[]", metadata={})
        assert JsonSplitter.can_handle(block, strategy) == 1.0

    def test_json_block_type_returns_one(self):
        block = SayouBlock(type="json", content="{}", metadata={})
        assert JsonSplitter.can_handle(block, "auto") == 1.0

    def test_auto_with_plain_text_returns_zero(self):
        block = SayouBlock(type="text", content="hello", metadata={})
        assert JsonSplitter.can_handle(block, "auto") == 0.0


# ---------------------------------------------------------------------------
# List splitting
# ---------------------------------------------------------------------------


class TestListSplitting:
    def test_small_list_fits_in_one_chunk(self):
        s = _splitter()
        data = [{"id": 1}, {"id": 2}]
        chunks = s.split(_block(data, chunk_size=500))
        assert len(chunks) == 1
        assert chunks[0].metadata["chunk_type"] == "json_list"

    def test_large_list_split_into_multiple_chunks(self):
        s = _splitter()
        # Each item is ~15 chars; chunk_size=40 → 2-3 items per chunk
        data = [{"id": i, "v": i} for i in range(20)]
        chunks = s.split(_block(data, chunk_size=40))
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "json_list"

    def test_item_count_metadata(self):
        s = _splitter()
        data = [{"x": i} for i in range(5)]
        chunks = s.split(_block(data, chunk_size=500))
        total_items = sum(c.metadata["item_count"] for c in chunks)
        assert total_items == 5

    def test_index_range_metadata_covers_all_items(self):
        s = _splitter()
        data = [{"x": i} for i in range(10)]
        chunks = s.split(_block(data, chunk_size=40))
        assert chunks[0].metadata["index_start"] == 0
        assert chunks[-1].metadata["index_end"] == 9


# ---------------------------------------------------------------------------
# Dict splitting
# ---------------------------------------------------------------------------


class TestDictSplitting:
    def test_small_dict_fits_in_one_chunk(self):
        s = _splitter()
        data = {"a": 1, "b": 2}
        chunks = s.split(_block(data, chunk_size=500))
        assert len(chunks) == 1

    def test_large_dict_split_by_keys(self):
        s = _splitter()
        # Each value is ~30 chars; chunk_size=50 → ~1-2 keys per chunk
        data = {f"key{i}": "x" * 30 for i in range(6)}
        chunks = s.split(_block(data, chunk_size=50))
        assert len(chunks) > 1

    def test_chunk_content_is_valid_json(self):
        s = _splitter()
        data = {"a": [1, 2], "b": {"c": 3}}
        chunks = s.split(_block(data, chunk_size=500))
        for chunk in chunks:
            parsed = json.loads(chunk.content)
            assert isinstance(parsed, (dict, list))


# ---------------------------------------------------------------------------
# String input parsing
# ---------------------------------------------------------------------------


class TestStringInput:
    def test_valid_json_string_is_parsed(self):
        s = _splitter()
        raw = json.dumps([{"id": i} for i in range(5)])
        block = SayouBlock(
            type="text", content=raw, metadata={"config": {"chunk_size": 500}}
        )
        chunks = s.split(block)
        assert len(chunks) >= 1

    def test_invalid_string_returns_empty(self):
        s = _splitter()
        block = SayouBlock(
            type="text",
            content="not json at all",
            metadata={"config": {"chunk_size": 500}},
        )
        chunks = s.split(block)
        assert chunks == []
