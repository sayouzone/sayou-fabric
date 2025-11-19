import math
from typing import List, Callable
from ..interfaces.base_splitter import BaseSplitter
from ..utils.schema import Document, Chunk

class SemanticSplitter(BaseSplitter):
    """
    (Tier 2) 의미 기반 분할기 (The Intelligent Analyst).
    - 역할: 문장 간의 의미적 유사도가 급격히 떨어지는 구간(Breakpoint)을 찾아 자릅니다.
    - 특징: 외부 의존성 없이 동작하는 '유사도 계산 엔진'을 내장하고 있습니다.
    """
    component_name = "SemanticSplitter"
    SUPPORTED_TYPES = ["semantic"]

    def _do_split(self, doc: Document) -> List[Chunk]:
        """
        
        Args:
            doc: 
        
        Returns:
            List: 
        
        Note:

        """
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")
        
        # 1. 문장 단위 분리 (전처리)
        sentences = [s.strip() for s in doc.content.replace("\n", ". ").split(". ") if s.strip()]
        if not sentences: return []

        # 2. 인코더 주입 (없으면 내장 더미 인코더 사용)
        # T3 플러그인이나 런타임에서 이 함수를 OpenAI/HuggingFace 함수로 교체하면 됩니다.
        encoder = config.get("encoder_function", self._simple_frequency_encoder)
        
        # 3. 유사도 기반 그룹핑 실행
        grouped_texts = self._cluster_sentences(sentences, encoder, threshold=0.5) # 임계값 0.5

        # 4. 결과 포장
        return [
            Chunk(
                chunk_content=text,
                metadata={
                    **doc.metadata, 
                    "chunk_id": f"{doc_id}_{i}",
                    "semantic_type": "semantic_group"
                }
            ) for i, text in enumerate(grouped_texts)
        ]

    def _cluster_sentences(self, sentences: List[str], encoder: Callable, threshold: float) -> List[str]:
        """유사도 기반 클러스터링 알고리즘 (Sliding Window)"""
        """
        
        Args:
            sentences: 
            encoder: 
            threshold:
        
        Returns:
            List: 
        
        Note:

        """
        if len(sentences) < 2: return sentences
        
        # 벡터화
        vectors = [encoder(s) for s in sentences]
        
        groups = []
        current_group = [sentences[0]]
        
        for i in range(len(vectors) - 1):
            # 현재 문장 vs 다음 문장 유사도 계산
            sim = self._cosine_similarity(vectors[i], vectors[i+1])
            
            # 유사도가 임계값보다 낮으면 -> 주제가 바뀜 -> 자른다
            if sim < threshold:
                groups.append(". ".join(current_group) + ".")
                current_group = [sentences[i+1]]
            else:
                current_group.append(sentences[i+1])
        
        if current_group:
            groups.append(". ".join(current_group) + ".")
            
        return groups

    # --- 내장 수학 유틸리티 (No Numpy) ---
    def _simple_frequency_encoder(self, text: str) -> List[float]:
        """(Dummy) 글자 빈도 기반 벡터 생성기"""
        """
        
        Args:
            text: 
        
        Returns:
            List: 
        
        Note:

        """
        vec = [0.0] * 10
        for char in text:
            vec[ord(char) % 10] += 1.0
        mag = math.sqrt(sum(x*x for x in vec))
        return [x/mag if mag else 0 for x in vec]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a*b for a, b in zip(v1, v2))
        # v1, v2는 이미 정규화되어 있다고 가정 (encoder 책임)
        return dot