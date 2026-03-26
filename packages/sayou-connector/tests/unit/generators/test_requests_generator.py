"""
Unit tests for RequestsGenerator.

Covers:
- can_handle: http/https returns 1.0, www. returns 0.8, other returns 0.0.
- Queue initialised with the seed URL at depth 0.
- _do_generate yields tasks from the queue.
- Feedback: new links below max_depth are added to the queue.
- Feedback: links at or beyond max_depth are ignored.
- Feedback: already-visited URLs are not re-queued.
- link_pattern regex filters which links are followed.
- Empty / failed packet feedback does nothing.
"""

import pytest
from sayou.connector.generator.requests_generator import RequestsGenerator
from sayou.core.schemas import SayouPacket, SayouTask


def _generator(
    source: str = "https://example.com",
    link_pattern: str = ".*",
    max_depth: int = 1,
) -> RequestsGenerator:
    gen = RequestsGenerator()
    gen.initialize(source=source, link_pattern=link_pattern, max_depth=max_depth)
    return gen


def _packet(links: list, depth: int = 0, success: bool = True) -> SayouPacket:
    task = SayouTask(
        source_type="requests",
        uri="https://example.com",
        params={"depth": depth},
        meta={},
    )
    data = {"__found_links__": links} if success else None
    return SayouPacket(task=task, data=data, success=success)


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_https_returns_one(self):
        assert RequestsGenerator.can_handle("https://example.com") == 1.0

    def test_http_returns_one(self):
        assert RequestsGenerator.can_handle("http://example.com") == 1.0

    def test_www_prefix_returns_nonzero(self):
        score = RequestsGenerator.can_handle("www.example.com")
        assert 0.0 < score < 1.0

    def test_local_path_returns_zero(self):
        assert RequestsGenerator.can_handle("/local/path") == 0.0


# ---------------------------------------------------------------------------
# Queue initialisation
# ---------------------------------------------------------------------------


class TestInitialisation:
    def test_seed_url_in_queue(self):
        gen = _generator("https://seed.com")
        assert len(gen.queue) == 1
        url, depth = gen.queue[0]
        assert url == "https://seed.com"
        assert depth == 0

    def test_seed_url_in_visited(self):
        gen = _generator("https://seed.com")
        assert "https://seed.com" in gen.visited


# ---------------------------------------------------------------------------
# Task generation
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_yields_one_task_for_single_seed(self):
        gen = _generator()
        tasks = list(gen._do_generate("https://example.com"))
        assert len(tasks) == 1
        assert tasks[0].source_type == "requests"
        assert tasks[0].uri == "https://example.com"

    def test_task_carries_correct_depth(self):
        gen = _generator()
        task = next(gen._do_generate("https://example.com"))
        assert task.params["depth"] == 0


# ---------------------------------------------------------------------------
# Feedback — link discovery
# ---------------------------------------------------------------------------


class TestFeedback:
    def test_new_link_within_depth_added_to_queue(self):
        gen = _generator(max_depth=2)
        # Consume the seed task first
        list(gen._do_generate("https://example.com"))
        gen._do_feedback(_packet(["https://example.com/page"], depth=0))
        urls_in_queue = [url for url, _ in gen.queue]
        assert "https://example.com/page" in urls_in_queue

    def test_link_at_max_depth_not_added(self):
        gen = _generator(max_depth=1)
        # depth=1 is exactly max_depth → should NOT be followed
        gen._do_feedback(_packet(["https://example.com/deep"], depth=1))
        assert "https://example.com/deep" not in [url for url, _ in gen.queue]

    def test_already_visited_link_not_re_queued(self):
        gen = _generator(max_depth=2)
        gen.visited.add("https://example.com/known")
        gen._do_feedback(_packet(["https://example.com/known"], depth=0))
        urls_in_queue = [url for url, _ in gen.queue]
        assert urls_in_queue.count("https://example.com/known") == 0

    def test_link_pattern_filters_links(self):
        gen = _generator(link_pattern=r"/blog/", max_depth=2)
        gen._do_feedback(
            _packet(
                ["https://example.com/blog/post", "https://example.com/about"],
                depth=0,
            )
        )
        urls_in_queue = [url for url, _ in gen.queue]
        assert "https://example.com/blog/post" in urls_in_queue
        assert "https://example.com/about" not in urls_in_queue

    def test_failed_packet_does_nothing(self):
        gen = _generator(max_depth=2)
        before = len(gen.queue)
        gen._do_feedback(_packet(["https://example.com/new"], success=False))
        assert len(gen.queue) == before

    def test_empty_links_does_nothing(self):
        gen = _generator(max_depth=2)
        before = len(gen.queue)  # 1 — seed URL is in queue at initialisation
        gen._do_feedback(_packet([]))
        assert len(gen.queue) == before  # no new links added
