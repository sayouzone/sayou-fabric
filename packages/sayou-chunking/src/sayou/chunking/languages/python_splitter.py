"""
Python AST-based language splitter.

Improvements over the original CodeSplitter inline logic
─────────────────────────────────────────────────────────
1. Metadata keys are fully standardised (lineStart / lineEnd everywhere).
2. _flush_chunk is defined exactly once.
3. Call-graph raw data is extracted from every function / method body:
     calls           — direct calls:  foo(), Bar()
     attribute_calls — attr calls:    obj.method()   (duck-typing signals)
     type_refs       — annotation + isinstance() type names
4. Inheritance info is captured for class headers.
5. Dead code (_process_method_node) has been removed.
6. `import re` is present (was missing in original).
"""

import ast
import re
import textwrap
from typing import Any, Dict, List, Optional, Set

from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_language_splitter import BaseLanguageSplitter


class PythonSplitter(BaseLanguageSplitter):
    """Full structural splitter for Python source files using the stdlib AST."""

    language = "python"
    extensions = [".py", ".pyw"]

    # ── public entry point ────────────────────────────────────────────

    def split(self, doc: SayouBlock, chunk_size: int) -> List[SayouChunk]:
        content = doc.content
        source_lines = content.splitlines()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            try:
                dedented = textwrap.dedent(content)
                tree = ast.parse(dedented)
                source_lines = dedented.splitlines()
            except SyntaxError:
                return self._regex_fallback(doc, chunk_size)

        return self._walk_module(tree, source_lines, doc, chunk_size)

    # ── module-level walker ───────────────────────────────────────────

    def _walk_module(
        self,
        tree: ast.Module,
        source_lines: List[str],
        doc: SayouBlock,
        chunk_size: int,
    ) -> List[SayouChunk]:
        chunks: List[SayouChunk] = []
        base_meta = doc.metadata.copy()

        # Buffer for loose top-level nodes (imports, assignments, …)
        loose_lines: List[str] = []
        loose_start: Optional[int] = None
        loose_end: Optional[int] = None
        accumulated_imports: List[Dict[str, Any]] = []

        def flush_loose():
            nonlocal loose_lines, loose_start, loose_end
            if not loose_lines:
                return
            extra = {
                "semantic_type": "code_block",
                "lineStart": loose_start,
                "lineEnd": loose_end,
            }
            if accumulated_imports:
                extra["imports"] = list(accumulated_imports)
            self._flush(chunks, loose_lines, base_meta, extra)
            loose_lines = []
            loose_start = None
            loose_end = None

        for node in tree.body:
            start = node.lineno - 1
            if hasattr(node, "decorator_list") and node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            end = node.end_lineno  # exclusive for slice, but 1-based lineEnd value

            node_lines = source_lines[start:end]

            if isinstance(node, (ast.Import, ast.ImportFrom)):
                accumulated_imports.extend(self._extract_import_objects(node))
                if not loose_lines:
                    loose_start = start + 1
                loose_end = end
                loose_lines.extend(node_lines)

            elif isinstance(node, ast.ClassDef):
                flush_loose()
                self._walk_class(node, source_lines, doc, chunks, base_meta)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                flush_loose()
                calls, attr_calls, type_refs = self._extract_calls(node)
                self._flush(
                    chunks,
                    node_lines,
                    base_meta,
                    {
                        "semantic_type": "function",
                        "function_name": node.name,
                        "lineStart": start + 1,
                        "lineEnd": end,
                        "calls": calls,
                        "attribute_calls": attr_calls,
                        "type_refs": type_refs,
                    },
                )

            else:
                if not loose_lines:
                    loose_start = start + 1
                loose_end = end
                loose_lines.extend(node_lines)

        flush_loose()
        return chunks

    # ── class walker ──────────────────────────────────────────────────

    def _walk_class(
        self,
        node: ast.ClassDef,
        source_lines: List[str],
        doc: SayouBlock,
        chunks: List[SayouChunk],
        base_meta: dict,
    ) -> None:
        class_name = node.name
        base_classes = self._extract_base_classes(node)

        # ---- 1. Header chunk (decorators + class def + optional docstring) ----
        header_start = node.lineno - 1
        if node.decorator_list:
            header_start = node.decorator_list[0].lineno - 1

        first_child_idx = 0
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):
            header_end = node.body[0].end_lineno
            first_child_idx = 1
        else:
            if node.body:
                first = node.body[0]
                header_end = first.lineno - 1
                if hasattr(first, "decorator_list") and first.decorator_list:
                    header_end = first.decorator_list[0].lineno - 1
            else:
                header_end = node.end_lineno

        header_extra: Dict[str, Any] = {
            "semantic_type": "class_header",
            "class_name": class_name,
            "lineStart": header_start + 1,
            "lineEnd": header_end,
        }
        if base_classes:
            header_extra["inherits_from"] = base_classes

        self._flush(
            chunks,
            source_lines[header_start:header_end],
            base_meta,
            header_extra,
        )

        # ---- 2. Body: attributes vs methods ----
        attr_lines: List[str] = []
        attr_start: Optional[int] = None
        attr_end: Optional[int] = None

        def flush_attrs():
            nonlocal attr_lines, attr_start, attr_end
            if not attr_lines:
                return
            self._flush(
                chunks,
                attr_lines,
                base_meta,
                {
                    "semantic_type": "class_attributes",
                    "parent_node": class_name,
                    "lineStart": attr_start,
                    "lineEnd": attr_end,
                },
            )
            attr_lines = []
            attr_start = None
            attr_end = None

        for child in node.body[first_child_idx:]:
            c_start = child.lineno - 1
            if hasattr(child, "decorator_list") and child.decorator_list:
                c_start = child.decorator_list[0].lineno - 1
            c_end = child.end_lineno

            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                flush_attrs()
                calls, attr_calls, type_refs = self._extract_calls(child)
                self._flush(
                    chunks,
                    source_lines[c_start:c_end],
                    base_meta,
                    {
                        "semantic_type": "method",
                        "function_name": child.name,
                        "parent_node": class_name,
                        "lineStart": c_start + 1,
                        "lineEnd": c_end,
                        "calls": calls,
                        "attribute_calls": attr_calls,
                        "type_refs": type_refs,
                    },
                )
            elif isinstance(child, ast.ClassDef):
                # Nested class — recurse
                flush_attrs()
                self._walk_class(child, source_lines, doc, chunks, base_meta)
            else:
                if not attr_lines:
                    attr_start = c_start + 1
                attr_end = c_end
                attr_lines.extend(source_lines[c_start:c_end])

        flush_attrs()

    # ── call graph extraction ─────────────────────────────────────────

    def _extract_calls(
        self, func_node: ast.FunctionDef
    ) -> tuple[List[str], List[str], List[str]]:
        """
        Walk the body of a function/method and return:
          calls           — direct symbol calls: foo(), Bar()
          attribute_calls — attribute method calls: obj.do_something()
          type_refs       — names from annotations + isinstance() checks
        """
        direct_calls: Set[str] = set()
        attr_calls: Set[str] = set()
        type_refs: Set[str] = set()

        for node in ast.walk(func_node):
            # ---- call sites ----
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    direct_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    attr_calls.add(node.func.attr)
                    # isinstance(x, SomeClass) → type reference
                    if (
                        isinstance(node.func, ast.Name)
                        and node.func.id == "isinstance"
                        and len(node.args) == 2
                    ):
                        self._collect_type_names(node.args[1], type_refs)

                # Also catch standalone isinstance() call
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "isinstance"
                    and len(node.args) == 2
                ):
                    self._collect_type_names(node.args[1], type_refs)

            # ---- annotations ----
            elif isinstance(node, ast.AnnAssign) and node.annotation:
                self._collect_type_names(node.annotation, type_refs)
            elif isinstance(node, ast.arg) and node.annotation:
                self._collect_type_names(node.annotation, type_refs)
            elif isinstance(node, ast.FunctionDef) and node.returns:
                self._collect_type_names(node.returns, type_refs)

        # Remove built-ins that pollute the graph
        _BUILTINS = {
            "print",
            "len",
            "range",
            "enumerate",
            "zip",
            "map",
            "filter",
            "sorted",
            "list",
            "dict",
            "set",
            "tuple",
            "str",
            "int",
            "float",
            "bool",
            "bytes",
            "type",
            "super",
            "getattr",
            "setattr",
            "hasattr",
            "isinstance",
            "issubclass",
            "callable",
            "iter",
            "next",
            "any",
            "all",
            "sum",
            "min",
            "max",
            "abs",
            "round",
            "open",
            "repr",
            "vars",
            "dir",
            "id",
            "hash",
            "hex",
            "bin",
            "oct",
            "chr",
            "ord",
        }
        direct_calls -= _BUILTINS
        type_refs -= _BUILTINS

        return sorted(direct_calls), sorted(attr_calls), sorted(type_refs)

    def _collect_type_names(self, node: ast.expr, out: Set[str]) -> None:
        """Recursively collect Name identifiers from a type expression node."""
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            out.add(node.attr)
        elif isinstance(node, ast.Subscript):
            self._collect_type_names(node.value, out)
            self._collect_type_names(node.slice, out)
        elif isinstance(node, ast.Tuple):
            for elt in node.elts:
                self._collect_type_names(elt, out)
        elif isinstance(node, ast.BinOp):  # X | Y  (Python 3.10+)
            self._collect_type_names(node.left, out)
            self._collect_type_names(node.right, out)

    # ── import parsing ────────────────────────────────────────────────

    def _extract_import_objects(self, node: ast.stmt) -> List[Dict[str, Any]]:
        imports: List[Dict[str, Any]] = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "type": "absolute",
                        "module": alias.name,
                        "name": None,
                        "alias": alias.asname,
                        "level": 0,
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level
            for alias in node.names:
                imports.append(
                    {
                        "type": "relative" if level > 0 else "absolute",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "level": level,
                        "raw_path": (
                            f"{'.' * level}{module}.{alias.name}"
                            if module
                            else f"{'.' * level}{alias.name}"
                        ),
                    }
                )
        return imports

    def _extract_base_classes(self, node: ast.ClassDef) -> List[str]:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                parts = []
                cur = base
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                bases.append(".".join(reversed(parts)))
        return bases

    # ── regex fallback ────────────────────────────────────────────────

    _REGEX_SEPS = [
        r"(\n\s*class\s+)",
        r"(\n\s*def\s+)",
        r"(\n\s*async\s+def\s+)",
        r"(\n\n+)",
        r"(\n+)",
    ]

    def _regex_fallback(self, doc: SayouBlock, chunk_size: int) -> List[SayouChunk]:
        """Used when AST parsing completely fails (e.g. invalid syntax)."""
        chunks: List[SayouChunk] = []
        base_meta = doc.metadata.copy()
        texts = self._recursive_split(doc.content, self._REGEX_SEPS, chunk_size)
        for i, text in enumerate(texts):
            if text.strip():
                meta = base_meta.copy()
                meta.update(
                    {
                        "chunk_index": i,
                        "semantic_type": "code_block",
                        "language": self.language,
                        "parse_method": "regex_fallback",
                    }
                )
                chunks.append(SayouChunk(content=text, metadata=meta))
        return chunks

    def _recursive_split(
        self, text: str, separators: List[str], chunk_size: int
    ) -> List[str]:
        if len(text) <= chunk_size or not separators:
            return [text]

        pattern = separators[0]
        rest = separators[1:]

        try:
            splits = re.split(pattern, text)
        except Exception:
            return self._recursive_split(text, rest, chunk_size)

        if len(splits) < 3:
            return self._recursive_split(text, rest, chunk_size)

        merged = [splits[0]] if splits[0] else []
        for i in range(1, len(splits), 2):
            sep = splits[i]
            content = splits[i + 1] if i + 1 < len(splits) else ""
            merged.append(sep + content)

        result: List[str] = []
        buf: List[str] = []
        buf_len = 0

        for s in merged:
            if len(s) > chunk_size:
                if buf:
                    result.append("".join(buf))
                    buf, buf_len = [], 0
                result.extend(self._recursive_split(s, rest, chunk_size))
            elif buf_len + len(s) > chunk_size:
                result.append("".join(buf))
                buf, buf_len = [s], len(s)
            else:
                buf.append(s)
                buf_len += len(s)

        if buf:
            result.append("".join(buf))

        return result
