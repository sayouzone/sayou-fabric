import random
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class EmbeddingAdapter(BaseAdapter):
    """
    (Tier 2) Generic Embedding Adapter.
    Decoupled from specific libraries (OpenAI, etc.).

    Strategies:
    1. 'external' (Default): Uses 'client' or 'embedding_fn' passed via kwargs.
    2. 'stub': Generates random vectors for testing.
    """

    component_name = "EmbeddingAdapter"
    SUPPORTED_TYPES = ["embedding", "vector"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["embedding", "vector"]:
            return 1.0
        if isinstance(input_data, list) and len(input_data) > 0:
            first = input_data[0]
            if isinstance(first, dict) and "content" in first:
                return 0.8
        return 0.0

    def _do_adapt(self, input_data: List[Dict[str, Any]], **kwargs) -> SayouOutput:
        """
        [Stateless Logic]
        - provider="external": Expects 'client' or 'embedding_fn' in kwargs.
        - provider="stub": Internal random vectors (No deps).
        """
        provider = kwargs.get("provider", "external")
        dimension = int(kwargs.get("dimension", 1536))
        external_client = kwargs.get("client")
        embedding_fn = kwargs.get("embedding_fn")

        nodes = []
        texts_to_embed = []
        mapping_indices = []

        # 1. Node transformation (Data normalization)
        for i, item in enumerate(input_data):
            content = item.get("content", "")
            meta = item.get("metadata", {})
            node_id = meta.get("chunk_id") or meta.get("id") or f"chunk_{i}"

            node = SayouNode(
                node_id=node_id,
                node_class="Chunk",
                friendly_name=meta.get("title") or f"Chunk {i}",
                attributes={"schema:text": content, **meta},
            )
            nodes.append(node)

            if content and isinstance(content, str):
                texts_to_embed.append(content.replace("\n", " "))
                mapping_indices.append(i)

        # 2. Embedding execution (Strategy Pattern)
        vectors = []
        if texts_to_embed:
            if provider == "external":
                if embedding_fn and callable(embedding_fn):
                    vectors = embedding_fn(texts_to_embed)
                elif external_client:
                    vectors = self._embed_via_client(
                        external_client, texts_to_embed, **kwargs
                    )
                else:
                    raise ValueError(
                        "[EmbeddingAdapter] Provider is 'external' but no 'client' or 'embedding_fn' provided in kwargs."
                    )

            else:
                self._log(f"Unknown provider '{provider}', falling back to stub.")
                vectors = self._embed_stub(texts_to_embed, dimension)

        # 3. Inject vectors
        for idx, vector in zip(mapping_indices, vectors):
            nodes[idx].attributes["vector"] = vector
            nodes[idx].attributes["vector_dim"] = len(vector)

        return SayouOutput(nodes=nodes)

    def _embed_stub(self, texts: List[str], dimension: int) -> List[List[float]]:
        self._log(f"🧪 [Stub] Generated {len(texts)} vectors (dim={dimension})")
        return [[random.random() for _ in range(dimension)] for _ in texts]

    def _embed_via_client(
        self, client, texts: List[str], **kwargs
    ) -> List[List[float]]:
        """
        External Client Helper.
        Assumes the client has an 'embed_documents' or similar method.
        This is just a helper; for complex logic, use 'embedding_fn'.
        """
        if hasattr(client, "embed_documents"):
            return client.embed_documents(texts)

        if hasattr(client, "embeddings") and hasattr(client.embeddings, "create"):
            model = kwargs.get("model", "text-embedding-3-small")
            try:
                response = client.embeddings.create(input=texts, model=model)
                sorted_data = sorted(response.data, key=lambda x: x.index)
                return [item.embedding for item in sorted_data]
            except Exception as e:
                raise RuntimeError(f"External client failed: {e}")

        raise ValueError(
            f"Unsupported client type: {type(client)}. Use 'embedding_fn' for custom logic."
        )
