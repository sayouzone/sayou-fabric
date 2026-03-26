"""
Shared pytest fixtures for the sayou-chunking test suite.
"""

import pytest
from sayou.core.schemas import SayouBlock

# ---------------------------------------------------------------------------
# SayouBlock factories
# ---------------------------------------------------------------------------


def make_block(content: str, **meta) -> SayouBlock:
    """Return a plain text SayouBlock with optional metadata fields."""
    return SayouBlock(type="text", content=content, metadata=meta)


def make_block_with_config(content: str, config: dict, **meta) -> SayouBlock:
    """Return a SayouBlock that embeds a ``config`` dict in its metadata."""
    return SayouBlock(type="text", content=content, metadata={"config": config, **meta})


# ---------------------------------------------------------------------------
# Common content fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def plain_text() -> str:
    return "Hello world.\n\nSecond paragraph.\n\nThird paragraph."


@pytest.fixture
def markdown_text() -> str:
    return (
        "# Title\n"
        "Intro content.\n\n"
        "## Section One\n"
        "Body of section one.\n\n"
        "## Section Two\n"
        "Body of section two.\n"
    )


@pytest.fixture
def python_source() -> str:
    return (
        "import os\n\n"
        "class MyClass:\n"
        "    def __init__(self, value):\n"
        "        self.value = value\n\n"
        "    def get(self):\n"
        "        return self.value\n\n"
        "def standalone():\n"
        "    pass\n"
    )


@pytest.fixture
def javascript_source() -> str:
    return (
        "function greet(name) {\n"
        "    console.log('Hello, ' + name);\n"
        "}\n\n"
        "class Greeter {\n"
        "    constructor(name) {\n"
        "        this.name = name;\n"
        "    }\n"
        "    greet() {\n"
        "        greet(this.name);\n"
        "    }\n"
        "}\n"
    )


@pytest.fixture
def json_list_content() -> str:
    import json

    items = [{"id": i, "value": f"item_{i}"} for i in range(10)]
    return json.dumps(items)


@pytest.fixture
def json_dict_content() -> str:
    import json

    data = {f"key_{i}": f"value_{'x' * 20}_{i}" for i in range(5)}
    return json.dumps(data)
