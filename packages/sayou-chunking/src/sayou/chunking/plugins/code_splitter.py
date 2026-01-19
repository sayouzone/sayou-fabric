import ast
from typing import List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter


@register_component("splitter")
class CodeSplitter(BaseSplitter):
    """
    (Tier 1) Polyglot Code Splitter.
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
        chunk_overlap = int(config.get("chunk_overlap", 0))

        ext = doc.metadata.get("extension", "").lower()
        lang = self.EXTENSION_MAP.get(ext, "default")

        # 1. Python: AST Parser
        if lang == "python":
            return self._split_python_ast(doc, chunk_size)

        # 2. Others: Regex Parser
        return self._split_regex(doc, lang, chunk_size, chunk_overlap)

    # =========================================================================
    # [Logic A] Python AST Splitter
    # =========================================================================
    def _split_python_ast(self, doc: SayouBlock, chunk_size: int) -> List[SayouChunk]:
        try:
            tree = ast.parse(doc.content)
            source_lines = doc.content.splitlines()
        except SyntaxError:
            return self._split_regex(doc, "python", chunk_size, 0)

        chunks = []
        current_chunk_lines = []
        current_size = 0

        for node in tree.body:
            start = node.lineno - 1
            if hasattr(node, "decorator_list") and node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            end = node.end_lineno

            node_lines = source_lines[start:end]
            node_text = "\n".join(node_lines)
            node_len = len(node_text)

            if node_len > chunk_size * 1.5 and isinstance(node, ast.ClassDef):
                if current_chunk_lines:
                    self._flush_chunk(chunks, current_chunk_lines, doc)
                    current_chunk_lines = []
                    current_size = 0

                self._separate_class_structure(
                    node, source_lines, doc, chunk_size, chunks
                )

            else:
                if current_size + node_len > chunk_size:
                    self._flush_chunk(chunks, current_chunk_lines, doc)
                    current_chunk_lines = []
                    current_size = 0

                if current_chunk_lines:
                    current_chunk_lines.append("")
                    current_size += 1

                current_chunk_lines.extend(node_lines)
                current_size += node_len

        if current_chunk_lines:
            self._flush_chunk(chunks, current_chunk_lines, doc)

        return chunks

    def _separate_class_structure(self, node, source_lines, doc, chunk_size, chunks):
        """
        [Advanced Logic] Class structure separated into 3 steps.
        1. Header Chunk: Decorators + Class Def + Docstring
        2. Attribute Chunk: Class Variables
        3. Method Chunks: Functions
        """
        if not node.body:
            return

        # ---------------------------------------------------------
        # 1. Create Header Chunk (Class Def + Docstring)
        # ---------------------------------------------------------

        start_line = node.lineno - 1
        if hasattr(node, "decorator_list") and node.decorator_list:
            start_line = node.decorator_list[0].lineno - 1

        docstring_node = None
        first_real_child_index = 0

        if (
            len(node.body) > 0
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):

            docstring_node = node.body[0]
            first_real_child_index = 1

            header_end_line = docstring_node.end_lineno
        else:
            header_end_line = node.body[0].lineno - 1
            if hasattr(node.body[0], "decorator_list") and node.body[0].decorator_list:
                header_end_line = node.body[0].decorator_list[0].lineno - 1

        header_lines = source_lines[start_line:header_end_line]
        header_chunk_index = len(chunks)
        parent_name = node.name

        self._flush_chunk(
            chunks,
            header_lines,
            doc,
            extra_meta={"semantic_type": "class_header", "class_name": parent_name},
        )

        # ---------------------------------------------------------
        # 2. Body Traversal (Attributes vs Methods)
        # ---------------------------------------------------------

        current_attr_lines = []

        for child in node.body[first_real_child_index:]:

            # [Type A] Attributes
            if isinstance(child, (ast.Assign, ast.AnnAssign)):
                c_start = child.lineno - 1
                c_end = child.end_lineno
                current_attr_lines.extend(source_lines[c_start:c_end])

            # [Type B] Methods or Nested Class
            elif isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                if current_attr_lines:
                    self._flush_chunk(
                        chunks,
                        current_attr_lines,
                        doc,
                        extra_meta={
                            "semantic_type": "class_attributes",
                            "parent_node": parent_name,
                            "parent_chunk_index": header_chunk_index,
                        },
                    )
                    current_attr_lines = []

                self._process_method_node(
                    child,
                    source_lines,
                    doc,
                    chunk_size,
                    chunks,
                    parent_name,
                    header_chunk_index,
                )

            # [Type C] Other (Pass, Comments etc.) -> Attribute or Ignore
            else:
                pass

        if current_attr_lines:
            self._flush_chunk(
                chunks,
                current_attr_lines,
                doc,
                extra_meta={
                    "semantic_type": "class_attributes",
                    "parent_node": parent_name,
                    "parent_chunk_index": header_chunk_index,
                },
            )

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
