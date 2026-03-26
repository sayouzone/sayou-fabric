"""
Unit tests for CodeSplitter (router) and language-specific splitters.

CodeSplitter contract:
- can_handle returns 1.0 for strategy="code" or an explicit language name.
- can_handle returns 1.0 when metadata["extension"] matches a known extension.
- Routes .py to PythonSplitter (AST-based).
- Routes .js to JavaScriptSplitter (regex-based).
- Falls back to Python splitter when no language can be determined.

PythonSplitter contract (via CodeSplitter):
- Produces one chunk per top-level function and one per class.
- Each method inside a class becomes its own chunk.
- function/method chunks carry: function_name, semantic_type, lineStart, lineEnd.
- class_header chunks carry: class_name, semantic_type="class_header".
- inherits_from is populated for subclasses.
- calls and attribute_calls are lists of strings.

JavaScriptSplitter contract (via CodeSplitter):
- Produces at least one chunk per top-level function / class.
- Each chunk carries language="javascript" and semantic_type="code_block".
"""

import pytest

from sayou.chunking.plugins.code_splitter import CodeSplitter
from sayou.chunking.languages.python_splitter import PythonSplitter
from sayou.chunking.languages.javascript_splitter import JavaScriptSplitter
from sayou.core.schemas import SayouBlock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _block(content: str, extension: str, chunk_size: int = 2000) -> SayouBlock:
    return SayouBlock(
        type="text",
        content=content,
        metadata={
            "source": f"test{extension}",
            "extension": extension,
            "config": {"chunk_size": chunk_size},
        },
    )


def _code_splitter() -> CodeSplitter:
    s = CodeSplitter()
    s.initialize()
    return s


PYTHON_SOURCE = """\
import os

class Animal:
    def __init__(self, name: str):
        self.name = name

    def speak(self):
        raise NotImplementedError

class Dog(Animal):
    def speak(self):
        return "Woof"

def utility(x, y):
    return x + y
"""

JS_SOURCE = """\
function greet(name) {
    console.log('Hello ' + name);
}

class Calculator {
    constructor() {
        this.result = 0;
    }
    add(n) {
        this.result += n;
        return this;
    }
}
"""


# ---------------------------------------------------------------------------
# CodeSplitter.can_handle
# ---------------------------------------------------------------------------


class TestCodeSplitterCanHandle:
    def test_strategy_code_returns_one(self):
        block = _block("x = 1", ".py")
        assert CodeSplitter.can_handle(block, "code") == 1.0

    def test_explicit_python_strategy_returns_one(self):
        block = _block("x = 1", ".py")
        assert CodeSplitter.can_handle(block, "python") == 1.0

    def test_py_extension_in_metadata_returns_one(self):
        block = _block("x = 1", ".py")
        assert CodeSplitter.can_handle(block, "auto") == 1.0

    def test_js_extension_in_metadata_returns_one(self):
        block = _block("var x = 1;", ".js")
        assert CodeSplitter.can_handle(block, "auto") == 1.0

    def test_unknown_extension_returns_zero(self):
        block = _block("hello", ".xyz")
        assert CodeSplitter.can_handle(block, "auto") == 0.0


# ---------------------------------------------------------------------------
# Python — structural chunking
# ---------------------------------------------------------------------------


class TestPythonSplitterViaCodeSplitter:
    def test_functions_get_own_chunks(self):
        s = _code_splitter()
        chunks = s.split(_block(PYTHON_SOURCE, ".py"))
        func_names = [c.metadata.get("function_name") for c in chunks]
        assert "utility" in func_names

    def test_methods_get_own_chunks(self):
        s = _code_splitter()
        chunks = s.split(_block(PYTHON_SOURCE, ".py"))
        method_chunks = [
            c for c in chunks if c.metadata.get("semantic_type") == "method"
        ]
        method_names = [c.metadata.get("function_name") for c in method_chunks]
        assert "speak" in method_names
        assert "__init__" in method_names

    def test_class_header_chunk_has_class_name(self):
        s = _code_splitter()
        chunks = s.split(_block(PYTHON_SOURCE, ".py"))
        headers = [
            c for c in chunks if c.metadata.get("semantic_type") == "class_header"
        ]
        class_names = [c.metadata.get("class_name") for c in headers]
        assert "Animal" in class_names
        assert "Dog" in class_names

    def test_subclass_inherits_from_populated(self):
        s = _code_splitter()
        chunks = s.split(_block(PYTHON_SOURCE, ".py"))
        dog_header = next(
            (c for c in chunks if c.metadata.get("class_name") == "Dog"), None
        )
        assert dog_header is not None
        assert "Animal" in dog_header.metadata.get("inherits_from", [])

    def test_line_numbers_are_positive_integers(self):
        s = _code_splitter()
        chunks = s.split(_block(PYTHON_SOURCE, ".py"))
        for chunk in chunks:
            if "lineStart" in chunk.metadata:
                assert chunk.metadata["lineStart"] >= 1
                assert chunk.metadata["lineEnd"] >= chunk.metadata["lineStart"]

    def test_language_metadata_is_python(self):
        s = _code_splitter()
        chunks = s.split(_block(PYTHON_SOURCE, ".py"))
        for chunk in chunks:
            assert chunk.metadata.get("language") == "python"

    def test_calls_is_a_list(self):
        s = _code_splitter()
        chunks = s.split(_block(PYTHON_SOURCE, ".py"))
        for chunk in chunks:
            calls = chunk.metadata.get("calls")
            if calls is not None:
                assert isinstance(calls, list)


# ---------------------------------------------------------------------------
# JavaScript — structural chunking
# ---------------------------------------------------------------------------


class TestJavaScriptSplitterViaCodeSplitter:
    def test_js_produces_chunks(self):
        s = _code_splitter()
        chunks = s.split(_block(JS_SOURCE, ".js"))
        assert len(chunks) >= 1

    def test_js_language_metadata(self):
        s = _code_splitter()
        chunks = s.split(_block(JS_SOURCE, ".js"))
        for chunk in chunks:
            assert chunk.metadata.get("language") == "javascript"

    def test_js_semantic_type_is_code_block(self):
        s = _code_splitter()
        chunks = s.split(_block(JS_SOURCE, ".js"))
        for chunk in chunks:
            assert chunk.metadata.get("semantic_type") == "code_block"


# ---------------------------------------------------------------------------
# Direct PythonSplitter tests (no router)
# ---------------------------------------------------------------------------


class TestPythonSplitterDirect:
    def _splitter(self):
        return PythonSplitter()

    def _block(self, content: str) -> SayouBlock:
        return SayouBlock(
            type="text",
            content=content,
            metadata={"extension": ".py", "config": {"chunk_size": 2000}},
        )

    def test_import_block_captured(self):
        src = "import os\nimport sys\n"
        chunks = self._splitter().split(self._block(src), chunk_size=2000)
        code_blocks = [
            c for c in chunks if c.metadata.get("semantic_type") == "code_block"
        ]
        assert len(code_blocks) >= 1

    def test_async_function_detected(self):
        src = "async def fetch():\n    pass\n"
        chunks = self._splitter().split(self._block(src), chunk_size=2000)
        funcs = [c for c in chunks if c.metadata.get("function_name") == "fetch"]
        assert len(funcs) == 1
        assert funcs[0].metadata.get("is_async") is True

    def test_generator_function_detected(self):
        src = "def gen():\n    yield 1\n    yield 2\n"
        chunks = self._splitter().split(self._block(src), chunk_size=2000)
        funcs = [c for c in chunks if c.metadata.get("function_name") == "gen"]
        assert len(funcs) == 1
        assert funcs[0].metadata.get("is_generator") is True

    def test_syntax_error_falls_back_to_regex(self):
        src = "def broken(\n    pass\n"  # invalid syntax
        chunks = self._splitter().split(self._block(src), chunk_size=2000)
        # Regex fallback should produce at least one chunk
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.get("language") == "python"
