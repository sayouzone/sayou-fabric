import math
from typing import Callable, List

from ..core.schemas import Chunk, InputDocument
from ..interfaces.base_splitter import BaseSplitter


class SemanticSplitter(BaseSplitter):
    """
    (Tier 2) Semantic Similarity Splitter.
    Splits text when the topic changes (cosine similarity drops).
    """

    component_name = "SemanticSplitter"
    SUPPORTED_TYPES = ["semantic"]

    def _do_split(self, doc: InputDocument) -> List[Chunk]:
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")

        # 전처리: 문장 분리 (단순화된 버전)
        sentences = [
            s.strip() for s in doc.content.replace("\n", ". ").split(". ") if s.strip()
        ]
        if not sentences:
            return []

        # 인코더 (기본값: 단순 빈도수 기반)
        encoder = config.get("encoder_function", self._simple_frequency_encoder)
        threshold = config.get("semantic_threshold", 0.5)

        # 그룹핑 실행
        grouped_texts = self._cluster_sentences(sentences, encoder, threshold)

        return [
            Chunk(
                chunk_content=text,
                metadata={
                    **doc.metadata,
                    "chunk_id": f"{doc_id}_{i}",
                    "semantic_type": "semantic_group",
                },
            )
            for i, text in enumerate(grouped_texts)
        ]

    def _cluster_sentences(
        self, sentences: List[str], encoder: Callable, threshold: float
    ) -> List[str]:
        # (기존 로직 동일)
        if len(sentences) < 2:
            return sentences
        vectors = [encoder(s) for s in sentences]
        groups = []
        current_group = [sentences[0]]

        for i in range(len(vectors) - 1):
            sim = self._cosine_similarity(vectors[i], vectors[i + 1])
            if sim < threshold:
                groups.append(". ".join(current_group) + ".")
                current_group = [sentences[i + 1]]
            else:
                current_group.append(sentences[i + 1])
        if current_group:
            groups.append(". ".join(current_group) + ".")
        return groups

    def _simple_frequency_encoder(self, text: str) -> List[float]:
        # (기존 로직 동일)
        vec = [0.0] * 10
        for char in text:
            vec[ord(char) % 10] += 1.0
        mag = math.sqrt(sum(x * x for x in vec))
        return [x / mag if mag else 0 for x in vec]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        return sum(a * b for a, b in zip(v1, v2))
