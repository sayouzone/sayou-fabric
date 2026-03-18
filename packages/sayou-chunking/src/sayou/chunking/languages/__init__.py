"""
Language splitter registry.

Adding a new language
─────────────────────
1. Create `languages/<lang>_splitter.py` implementing `BaseLanguageSplitter`.
2. Import it here and add an instance to `LANGUAGE_SPLITTERS`.
3. Done — `CodeSplitter` will automatically pick it up via extension lookup.
"""

from .go_splitter import GoSplitter
from .java_splitter import JavaSplitter
from .javascript_splitter import JavaScriptSplitter
from .python_splitter import PythonSplitter
from .typescript_splitter import TypeScriptSplitter

# Ordered list used by CodeSplitter to build the extension → splitter map.
# Precedence: first match wins (relevant when extensions overlap).
LANGUAGE_SPLITTERS = [
    PythonSplitter(),
    JavaScriptSplitter(),
    TypeScriptSplitter(),
    JavaSplitter(),
    GoSplitter(),
]

__all__ = [
    "LANGUAGE_SPLITTERS",
    "PythonSplitter",
    "JavaScriptSplitter",
    "TypeScriptSplitter",
    "JavaSplitter",
    "GoSplitter",
]
