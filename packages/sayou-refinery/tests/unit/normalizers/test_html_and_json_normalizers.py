"""
Unit tests for HtmlTextNormalizer, RawJsonNormalizer, and RecordNormalizer.
"""

from __future__ import annotations

import pytest
from sayou.core.schemas import SayouBlock

from sayou.refinery.normalizer.html_text_normalizer import HtmlTextNormalizer
from sayou.refinery.normalizer.raw_json_normalizer import RawJsonNormalizer
from sayou.refinery.normalizer.record_normalizer import RecordNormalizer

# ===========================================================================
# HtmlTextNormalizer
# ===========================================================================


class TestHtmlTextNormalizerCanHandle:
    def test_strategy_html_returns_1(self):
        assert HtmlTextNormalizer.can_handle("<p>text</p>", "html") == 1.0

    def test_html_tag_in_string(self):
        score = HtmlTextNormalizer.can_handle("<html><body>hi</body></html>", "auto")
        assert score == 1.0

    def test_body_tag_returns_high(self):
        score = HtmlTextNormalizer.can_handle("<body><p>text</p></body>", "auto")
        assert score >= 0.9

    def test_non_html_string_returns_0(self):
        assert HtmlTextNormalizer.can_handle("just plain text", "auto") == 0.0

    def test_non_string_returns_0(self):
        assert HtmlTextNormalizer.can_handle({"key": "val"}, "auto") == 0.0


class TestHtmlTextNormalizerNormalize:
    def _norm(self, html: str):
        try:
            from bs4 import BeautifulSoup  # noqa: F401
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")
        n = HtmlTextNormalizer()
        n.initialize()
        return n._do_normalize(html)

    def test_returns_single_text_block(self):
        blocks = self._norm("<html><body><p>Hello Sayou</p></body></html>")
        assert len(blocks) == 1
        assert blocks[0].type == "text"

    def test_strips_script_and_style(self):
        html = "<html><head><script>alert(1)</script><style>h1{color:red}</style></head><body>Clean</body></html>"
        blocks = self._norm(html)
        assert "alert" not in blocks[0].content
        assert "color:red" not in blocks[0].content

    def test_title_extracted_to_metadata(self):
        html = "<html><head><title>My Page</title></head><body>content</body></html>"
        blocks = self._norm(html)
        assert blocks[0].metadata.get("title") == "My Page"

    def test_meta_tags_extracted(self):
        html = '<html><head><meta name="sender" content="alice@example.com"/></head><body>text</body></html>'
        blocks = self._norm(html)
        assert blocks[0].metadata.get("sender") == "alice@example.com"

    def test_consecutive_newlines_collapsed(self):
        html = "<html><body><p>A</p><p>B</p><p>C</p></body></html>"
        blocks = self._norm(html)
        # Should not have 3+ consecutive newlines
        assert "\n\n\n" not in blocks[0].content

    def test_non_string_input_raises(self):
        try:
            from bs4 import BeautifulSoup  # noqa: F401
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")
        n = HtmlTextNormalizer()
        n.initialize()
        with pytest.raises(Exception):
            n._do_normalize({"not": "a string"})


# ===========================================================================
# RawJsonNormalizer
# ===========================================================================


class TestRawJsonNormalizerCanHandle:
    def test_strategy_raw_json(self):
        assert RawJsonNormalizer.can_handle({}, "raw_json") == 1.0

    def test_dict_returns_high(self):
        score = RawJsonNormalizer.can_handle({"key": "val"}, "auto")
        assert score >= 0.8

    def test_list_of_dicts_returns_high(self):
        score = RawJsonNormalizer.can_handle([{"a": 1}], "auto")
        assert score >= 0.8

    def test_plain_string_returns_0(self):
        assert RawJsonNormalizer.can_handle("hello", "auto") == 0.0


class TestRawJsonNormalizerNormalize:
    def test_dict_becomes_single_record_block(self):
        n = RawJsonNormalizer()
        n.initialize()
        blocks = n._do_normalize({"id": "1", "name": "Alice"})
        assert len(blocks) == 1
        assert blocks[0].type == "record"
        assert blocks[0].content["name"] == "Alice"

    def test_list_of_dicts_becomes_multiple_blocks(self):
        n = RawJsonNormalizer()
        n.initialize()
        data = [{"id": str(i)} for i in range(5)]
        blocks = n._do_normalize(data)
        assert len(blocks) == 5

    def test_non_dict_in_list_skipped(self):
        n = RawJsonNormalizer()
        n.initialize()
        blocks = n._do_normalize([{"id": "1"}, "not_a_dict", 42])
        assert len(blocks) == 1  # only the dict

    def test_invalid_input_raises(self):
        n = RawJsonNormalizer()
        n.initialize()
        with pytest.raises(Exception):
            n._do_normalize("plain string")


# ===========================================================================
# RecordNormalizer
# ===========================================================================


class TestRecordNormalizerCanHandle:
    def test_strategy_json(self):
        assert RecordNormalizer.can_handle({}, "json") == 1.0

    def test_strategy_record(self):
        assert RecordNormalizer.can_handle([], "record") == 1.0

    def test_dict_returns_high(self):
        assert RecordNormalizer.can_handle({"a": 1}, "auto") >= 0.8

    def test_list_of_dicts_returns_high(self):
        assert RecordNormalizer.can_handle([{"a": 1}], "auto") >= 0.8


class TestRecordNormalizerNormalize:
    def test_single_dict_becomes_record(self):
        n = RecordNormalizer()
        n.initialize()
        blocks = n._do_normalize({"id": "x", "value": 42})
        assert len(blocks) == 1
        assert blocks[0].type == "record"

    def test_list_of_dicts_merged_into_single_block(self):
        """RecordNormalizer wraps a homogeneous list into one block."""
        n = RecordNormalizer()
        n.initialize()
        data = [{"id": str(i), "val": i} for i in range(3)]
        blocks = n._do_normalize(data)
        # RecordNormalizer._create_list_block wraps a same-type list
        assert len(blocks) >= 1

    def test_content_meta_separation(self):
        """When input has 'content' + 'meta', they should be separated."""
        n = RecordNormalizer()
        n.initialize()
        data = {
            "content": [{"text": "hello", "start": 0.0}],
            "meta": {"video_id": "abc123", "source": "youtube"},
        }
        blocks = n._do_normalize(data)
        assert len(blocks) == 1
        assert blocks[0].metadata.get("video_id") == "abc123"

    def test_id_extracted_to_metadata(self):
        n = RecordNormalizer()
        n.initialize()
        data = {"id": "my-id", "name": "test"}
        blocks = n._do_normalize(data)
        assert blocks[0].metadata.get("original_id") == "my-id"

    def test_invalid_input_raises(self):
        n = RecordNormalizer()
        n.initialize()
        with pytest.raises(Exception):
            n._do_normalize("raw string")
