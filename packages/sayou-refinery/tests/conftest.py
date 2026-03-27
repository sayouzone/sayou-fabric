"""
Shared pytest fixtures for the sayou-refinery test suite.
"""

from __future__ import annotations

import pytest
from sayou.core.schemas import SayouBlock


def make_text_block(content: str, **meta) -> SayouBlock:
    return SayouBlock(type="text", content=content, metadata=meta)


def make_md_block(content: str, **meta) -> SayouBlock:
    return SayouBlock(type="md", content=content, metadata=meta)


def make_record_block(content: dict | list, **meta) -> SayouBlock:
    return SayouBlock(type="record", content=content, metadata=meta)


@pytest.fixture
def text_blocks():
    return [
        make_text_block("Hello world", page_num=1),
        make_text_block("Foo bar baz", page_num=2),
    ]


@pytest.fixture
def md_blocks():
    return [
        make_md_block("# Title\n\nSome content.", page_num=1),
        make_md_block("## Section\n\nMore content.", page_num=2),
    ]


@pytest.fixture
def record_blocks():
    return [
        make_record_block({"id": "1", "name": "Alice", "score": 95}),
        make_record_block({"id": "2", "name": "Bob", "score": 80}),
    ]


@pytest.fixture
def minimal_doc_dict():
    """Minimal sayou-document dict format for DocMarkdownNormalizer."""
    return {
        "file_name": "test.pdf",
        "file_id": "test.pdf",
        "doc_type": "pdf",
        "metadata": {"title": "Test Document", "author": "Tester"},
        "page_count": 2,
        "pages": [
            {
                "page_num": 1,
                "elements": [
                    {
                        "type": "text",
                        "id": "t1",
                        "text": "Introduction paragraph.",
                        "raw_attributes": {},
                        "meta": {"page_num": 1},
                    },
                    {
                        "type": "table",
                        "id": "tbl1",
                        "data": [["Name", "Value"], ["A", "1"]],
                        "meta": {"page_num": 1},
                    },
                ],
                "header_elements": [],
                "footer_elements": [],
            },
            {
                "page_num": 2,
                "elements": [
                    {
                        "type": "text",
                        "id": "t2",
                        "text": "Conclusion paragraph.",
                        "raw_attributes": {
                            "semantic_type": "heading",
                            "heading_level": 2,
                        },
                        "meta": {"page_num": 2},
                    },
                ],
                "header_elements": [],
                "footer_elements": [],
            },
        ],
    }
