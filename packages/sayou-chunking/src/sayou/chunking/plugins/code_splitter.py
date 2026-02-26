import ast
import textwrap
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter


@register_component("splitter")
class CodeSplitter(BaseSplitter):
    """
    Polyglot Code Splitter.
    - Python: Uses AST for structural splitting (Preserves Decorators & Context).
    - Others: Uses Regex with indentation awareness.
    """

    component_name = "CodeSplitter"
    SUPPORTED_TYPES = [
        "code",
        "python",
        "javascript",
        "typescript",
        "java",
        "go",
        "cpp",
    ]

    EXTENSION_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".cpp": "cpp",
        ".c": "cpp",
        ".h": "cpp",
    }

    REGEX_SEPARATORS = {
        "javascript": [
            r"(\n\s*class\s+)",
            r"(\n\s*function\s+)",
            r"(\n\s*const\s+)",
            r"(\n\s*let\s+)",
            r"(\n\s*var\s+)",
            r"(\n+)",
        ],
        "typescript": [
            r"(\n\s*interface\s+)",
            r"(\n\s*type\s+)",
            r"(\n\s*class\s+)",
            r"(\n\s*function\s+)",
            r"(\n\s*const\s+)",
            r"(\n+)",
        ],
        "java": [
            r"(\n\s*class\s+)",
            r"(\n\s*public\s+)",
            r"(\n\s*protected\s+)",
            r"(\n\s*private\s+)",
            r"(\n+)",
        ],
        "go": [r"(\n\s*func\s+)", r"(\n\s*type\s+)", r"(\n+)"],
        "cpp": [r"(\n\s*class\s+)", r"(\n\s*struct\s+)", r"(\n\s*void\s+)", r"(\n+)"],
        "default": [r"(\n\n+)", r"(\n+)", r"( )", ""],
    }

    @classmethod
    def can_handle(cls, input_data: dict, strategy: str = "auto") -> float:
        if strategy == "code":
            return 1.0
        meta = (
            getattr(input_data, "metadata", {})
            if not isinstance(input_data, dict)
            else input_data.get("metadata", {})
        )
        ext = meta.get("extension", "").lower()
        return 1.0 if ext in cls.EXTENSION_MAP else 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        config = doc.metadata.get("config", {})
        chunk_size = int(config.get("chunk_size", 1000))

        ext = doc.metadata.get("extension", "").lower()
        lang = self.EXTENSION_MAP.get(ext, "default")

        if lang == "python":
            self._log(
                f"\n[DEBUG] 🐍 Python AST Splitter Start (Size: {len(doc.content)} chars)"
            )
            return self._split_python_ast(doc, chunk_size)

        return self._split_regex(doc, lang, chunk_size, 0)

    # =========================================================================
    # [Logic A] Python AST Splitter
    # =========================================================================
    def _split_python_ast(self, doc: SayouBlock, chunk_size: int) -> List[SayouChunk]:
        content = doc.content
        source_lines = content.splitlines()

        try:
            tree = ast.parse(content)
            self._log("[DEBUG] ✅ AST Parse Success (Raw Content)")
        except SyntaxError as e:
            self._log(f"❌ [AST Fail] SyntaxError in {doc.metadata.get('source')}: {e}")
            try:
                dedented_content = textwrap.dedent(content)
                tree = ast.parse(dedented_content)
                source_lines = dedented_content.splitlines()
                self._log("[DEBUG] ✅ AST Parse Success (After Dedent)")
            except SyntaxError as e2:
                self._log(f"[DEBUG] ❌ AST Parse Failed Completely: {e2}")
                self._log("[DEBUG] -> Falling back to Regex Splitter")
                return self._split_regex(doc, "python", chunk_size, 0)
            except Exception:
                self._log("⚠️ [AST Fail] Falling back to Regex.")
                return self._split_regex(doc, "python", chunk_size, 0)

        chunks = []
        current_chunk_lines = []
        current_size = 0
        current_imports = []

        self._log(f"[DEBUG] Top-level nodes found: {len(tree.body)}")

        for i, node in enumerate(tree.body):
            node_type = type(node).__name__
            start = node.lineno - 1
            if hasattr(node, "decorator_list") and node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            end = node.end_lineno

            node_lines = source_lines[start:end]
            node_text = "\n".join(node_lines)
            node_len = len(node_text)

            self._log(
                f"[DEBUG] Node {i} [{node_type}]: Lines {start+1}~{end} (Len: {node_len})"
            )

            # [CASE 0] Import
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                extracted_imports = self._extract_import_objects(node)
                current_imports.extend(extracted_imports)

            # [CASE 1] ClassDef
            if isinstance(node, ast.ClassDef):
                self._log(f"   -> Found Class '{node.name}'. Processing structure...")

                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_classes.append(f"{base.value.id}.{base.attr}")

                self._separate_class_structure(
                    node,
                    source_lines,
                    doc,
                    chunk_size,
                    chunks,
                    inheritance_info=base_classes,
                )

            # [CASE 2] FunctionDef
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._log(
                    f"   -> Found Function '{node.name}'. Creating independent chunk."
                )

                if current_chunk_lines:
                    self._flush_chunk(chunks, current_chunk_lines, doc)
                    current_chunk_lines = []
                    current_size = 0
                    current_buffer_start = None

                self._flush_chunk(
                    chunks,
                    node_lines,
                    doc,
                    extra_meta={
                        "semantic_type": "function",
                        "function_name": node.name,
                        "lineStart": start + 1,  # 1-based index
                        "lineEnd": end,
                    },
                )

            # [CASE 3] Others (Imports, Variables...)
            else:
                self._log(f"   -> Found Minor Node ({node_type}). Merging...")

                if not current_chunk_lines:
                    current_buffer_start = start + 1

                if current_size + node_len > chunk_size:
                    self._log("      -> Buffer full. Flushing previous chunk.")
                    self._flush_chunk(
                        chunks,
                        current_chunk_lines,
                        doc,
                        extra_meta={
                            "lineStart": current_buffer_start,
                            "lineEnd": start,
                        },
                    )
                    current_chunk_lines = []
                    current_size = 0
                    current_buffer_start = start + 1

                current_chunk_lines.extend(node_lines)
                current_size += node_len

        if current_chunk_lines:
            extra_meta = {"lineStart": current_buffer_start, "lineEnd": end}
            if current_imports:
                extra_meta["imports"] = current_imports
            self._flush_chunk(chunks, current_chunk_lines, doc, extra_meta=extra_meta)

        self._log(f"[DEBUG] AST Split Finished. Total chunks: {len(chunks)}")
        return chunks

    def _extract_import_objects(self, node) -> List[Dict[str, Any]]:
        """
        Extracts detailed information from AST Import nodes.
        This includes relative path levels and module/type information, rather than just strings.
        """
        imports = []

        # Case A: import os, sys
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

        # Case B: from .core import BaseComponent
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

    def _separate_class_structure(
        self, node, source_lines, doc, chunk_size, chunks, inheritance_info=None
    ):
        """
        [Advanced Logic] Class structure separated into 3 steps.
        1. Header Chunk: Decorators + Class Def + Docstring
        2. Attribute Chunk: Class Variables
        3. Method Chunks: Functions
        """
        parent_name = node.name

        # ---------------------------------------------------------
        # 1. Create Header Chunk (Class Def + Docstring)
        # ---------------------------------------------------------
        start_line = node.lineno - 1
        if hasattr(node, "decorator_list") and node.decorator_list:
            start_line = node.decorator_list[0].lineno - 1

        header_end_line = node.lineno

        if (
            len(node.body) > 0
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):
            header_end_line = node.body[0].end_lineno
            first_child_idx = 1
        else:
            if len(node.body) > 0:
                first_child = node.body[0]
                header_end_line = first_child.lineno - 1
                if (
                    hasattr(first_child, "decorator_list")
                    and first_child.decorator_list
                ):
                    header_end_line = first_child.decorator_list[0].lineno - 1
            else:
                header_end_line = node.end_lineno
            first_child_idx = 0

        header_lines = source_lines[start_line:header_end_line]
        header_meta = {
            "semantic_type": "class_header",
            "class_name": node.name,
            "start_line": start_line + 1,
            "end_line": header_end_line,
        }
        if inheritance_info:
            header_meta["inherits_from"] = inheritance_info

        self._flush_chunk(chunks, header_lines, doc, extra_meta=header_meta)
        header_chunk_index = len(chunks) - 1

        # ---------------------------------------------------------
        # 2. Body Traversal (Attributes vs Methods)
        # ---------------------------------------------------------

        current_attr_lines = []
        attr_start_line = None
        attr_end_line = None

        for child in node.body[first_child_idx:]:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):

                if current_attr_lines:
                    self._flush_chunk(
                        chunks,
                        current_attr_lines,
                        doc,
                        extra_meta={
                            "semantic_type": "class_attributes",
                            "parent_node": parent_name,
                            "start_line": attr_start_line,
                            "end_line": attr_end_line,
                        },
                    )
                    current_attr_lines = []
                    attr_start_line = None

                c_start = child.lineno - 1
                if hasattr(child, "decorator_list") and child.decorator_list:
                    c_start = child.decorator_list[0].lineno - 1
                c_end = child.end_lineno

                method_lines = source_lines[c_start:c_end]

                self._flush_chunk(
                    chunks,
                    method_lines,
                    doc,
                    extra_meta={
                        "semantic_type": "method",
                        "parent_node": parent_name,
                        "function_name": child.name,
                        "start_line": c_start + 1,
                        "end_line": c_end,
                    },
                )

            else:
                c_start = child.lineno - 1
                c_end = child.end_lineno

                if not current_attr_lines:
                    attr_start_line = c_start + 1
                attr_end_line = c_end

                current_attr_lines.extend(source_lines[c_start:c_end])

        if current_attr_lines:
            self._flush_chunk(
                chunks,
                current_attr_lines,
                doc,
                extra_meta={
                    "semantic_type": "class_attributes",
                    "parent_node": parent_name,
                    "start_line": attr_start_line,
                    "end_line": attr_end_line,
                },
            )

    def _flush_chunk(self, chunks, lines, doc, extra_meta=None):
        content = "\n".join(lines).strip()
        if content:
            meta = doc.metadata.copy()
            meta["chunk_index"] = len(chunks)
            if extra_meta:
                meta.update(extra_meta)
            chunks.append(SayouChunk(content=content, metadata=meta))

    def _process_method_node(
        self, child, source_lines, doc, chunk_size, chunks, parent_name, parent_index
    ):
        c_start = child.lineno - 1
        if hasattr(child, "decorator_list") and child.decorator_list:
            c_start = child.decorator_list[0].lineno - 1
        c_end = child.end_lineno

        child_lines = source_lines[c_start:c_end]
        child_text = "\n".join(child_lines)

        if len(child_text) > chunk_size:
            self._flush_chunk(
                chunks,
                child_lines,
                doc,
                extra_meta={
                    "semantic_type": "method",
                    "parent_node": parent_name,
                    "parent_chunk_index": parent_index,
                },
            )

        else:
            self._flush_chunk(
                chunks,
                child_lines,
                doc,
                extra_meta={
                    "semantic_type": "method",
                    "parent_node": parent_name,
                    "parent_chunk_index": parent_index,
                },
            )

    def _flush_chunk(self, chunks, lines, doc, extra_meta=None):
        content = "\n".join(lines).strip()
        if content:
            meta = doc.metadata.copy()
            meta["chunk_index"] = len(chunks)
            if extra_meta:
                meta.update(extra_meta)

            chunks.append(SayouChunk(content=content, metadata=meta))

    # =========================================================================
    # [Logic B] Regex Splitter (Recursive)
    # =========================================================================
    def _split_regex(
        self, doc: SayouBlock, lang: str, chunk_size: int, chunk_overlap: int
    ) -> List[SayouChunk]:
        separators = self.REGEX_SEPARATORS.get(lang, self.REGEX_SEPARATORS["default"])
        if lang != "default":
            separators = separators + self.REGEX_SEPARATORS["default"]

        final_chunks_text = self._recursive_regex_split(
            doc.content, separators, chunk_size
        )

        results = []
        for i, text in enumerate(final_chunks_text):
            if not text.strip():
                continue
            chunk_meta = doc.metadata.copy()
            chunk_meta.update({"chunk_index": i, "language": lang})
            results.append(SayouChunk(content=text, metadata=chunk_meta))
        return results

    def _recursive_regex_split(
        self, text: str, separators: List[str], chunk_size: int
    ) -> List[str]:
        """
        Regex based recursive split (separator retention logic included)
        """
        if len(text) <= chunk_size:
            return [text]

        if not separators:
            return [text]

        pattern = separators[0]
        next_separators = separators[1:]

        # 1. Split
        if pattern == "":
            splits = list(text)
        else:
            try:
                splits = re.split(pattern, text)
            except Exception:
                splits = [text]

        if len(splits) < 3:
            return self._recursive_regex_split(text, next_separators, chunk_size)

        # 2. Merge
        merged = []

        if splits[0]:
            merged.append(splits[0])

        for i in range(1, len(splits), 2):
            sep = splits[i]
            content = splits[i + 1] if i + 1 < len(splits) else ""
            merged.append(sep + content)

        # 3. Grouping
        final_result = []
        _doc = []
        _len = 0

        for s in merged:
            if len(s) > chunk_size:
                if _doc:
                    final_result.append("".join(_doc))
                    _doc = []
                    _len = 0
                final_result.extend(
                    self._recursive_regex_split(s, next_separators, chunk_size)
                )
            else:
                if _len + len(s) > chunk_size:
                    final_result.append("".join(_doc))
                    _doc = [s]
                    _len = len(s)
                else:
                    _doc.append(s)
                    _len += len(s)

        if _doc:
            final_result.append("".join(_doc))

        return final_result
