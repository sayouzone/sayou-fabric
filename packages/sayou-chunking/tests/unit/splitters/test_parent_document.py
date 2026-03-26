"""
Unit tests for ParentDocumentSplitter.

Contract:
- Produces two tiers of chunks: doc_level="parent" and doc_level="child".
- Every child chunk carries a parent_id equal to the chunk_id of its parent.
- Every parent chunk carries a child_ids list that contains the IDs of its children.
- parent_chunk_size > chunk_size (children are smaller windows of parents).
- can_handle returns 1.0 only for strategy="parent_document".
"""

import pytest
from sayou.chunking.splitter.parent_document_splitter import \
    ParentDocumentSplitter
from sayou.core.schemas import SayouBlock


def _block(
    content: str, parent_chunk_size: int = 200, chunk_size: int = 50
) -> SayouBlock:
    return SayouBlock(
        type="text",
        content=content,
        metadata={
            "id": "testdoc",
            "config": {
                "parent_chunk_size": parent_chunk_size,
                "chunk_size": chunk_size,
                "chunk_overlap": 0,
            },
        },
    )


def _splitter() -> ParentDocumentSplitter:
    s = ParentDocumentSplitter()
    s.initialize()
    return s


LONG_TEXT = "The quick brown fox jumps over the lazy dog. " * 20  # ~900 chars


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_parent_document_strategy_returns_one(self):
        block = SayouBlock(type="text", content="x", metadata={})
        assert ParentDocumentSplitter.can_handle(block, "parent_document") == 1.0

    def test_auto_strategy_returns_zero(self):
        block = SayouBlock(type="text", content="x", metadata={})
        assert ParentDocumentSplitter.can_handle(block, "auto") == 0.0


# ---------------------------------------------------------------------------
# Tier structure
# ---------------------------------------------------------------------------


class TestTierStructure:
    def test_produces_both_parents_and_children(self):
        s = _splitter()
        chunks = s.split(_block(LONG_TEXT))
        parents = [c for c in chunks if c.metadata.get("doc_level") == "parent"]
        children = [c for c in chunks if c.metadata.get("doc_level") == "child"]
        assert len(parents) >= 1
        assert len(children) >= 1

    def test_every_child_has_valid_parent_id(self):
        s = _splitter()
        chunks = s.split(_block(LONG_TEXT))
        parent_ids = {
            c.metadata["chunk_id"]
            for c in chunks
            if c.metadata.get("doc_level") == "parent"
        }
        children = [c for c in chunks if c.metadata.get("doc_level") == "child"]
        for child in children:
            assert (
                child.metadata.get("parent_id") in parent_ids
            ), f"child.parent_id={child.metadata.get('parent_id')} not in parent ids"

    def test_every_parent_lists_its_children(self):
        s = _splitter()
        chunks = s.split(_block(LONG_TEXT))
        parents = [c for c in chunks if c.metadata.get("doc_level") == "parent"]
        child_ids_all = {
            c.metadata["chunk_id"]
            for c in chunks
            if c.metadata.get("doc_level") == "child"
        }
        for parent in parents:
            listed = parent.metadata.get("child_ids", [])
            assert isinstance(listed, list)
            for cid in listed:
                assert cid in child_ids_all

    def test_children_are_smaller_than_parents(self):
        s = _splitter()
        chunks = s.split(_block(LONG_TEXT, parent_chunk_size=200, chunk_size=50))
        parents = [c for c in chunks if c.metadata.get("doc_level") == "parent"]
        children = [c for c in chunks if c.metadata.get("doc_level") == "child"]
        if parents and children:
            avg_parent = sum(len(p.content) for p in parents) / len(parents)
            avg_child = sum(len(c.content) for c in children) / len(children)
            assert avg_child <= avg_parent

    def test_chunk_ids_are_unique(self):
        s = _splitter()
        chunks = s.split(_block(LONG_TEXT))
        ids = [c.metadata.get("chunk_id") for c in chunks if c.metadata.get("chunk_id")]
        assert len(ids) == len(set(ids)), "Duplicate chunk_ids found"
