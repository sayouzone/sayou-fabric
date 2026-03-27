import random
from typing import Any, Callable, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class EmbeddingAdapter(BaseAdapter):
    """
    Generic embedding adapter — decoupled from specific providers.

    Strategies
    ----------
    ``external`` (default)
        Delegates to a ``client`` or ``embedding_fn`` supplied via kwargs.
    ``stub``
        Generates random vectors; useful for local testing without API keys.
    """

    component_name = "EmbeddingAdapter"
    SUPPORTED_TYPES = ["embedding", "vector"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["embedding", "vector"]:
            return 1.0
        if isinstance(input_data, list) and input_data:
            first = input_data[0]
            if isinstance(first, dict) and "content" in first:
                return 0.8
        return 0.0

    def _do_adapt(self, input_data: List[Dict[str, Any]], **kwargs) -> SayouOutput:
        """
        Embed input chunks and attach vectors to the resulting SayouNodes.

        Kwargs
        ------
        provider : str
            ``"external"`` (default) or ``"stub"``.
        dimension : int
            Vector dimension used by the stub (default 1536).
        client : object
            External client with ``embed_documents()`` or OpenAI-compatible API.
        embedding_fn : Callable[[List[str]], List[List[float]]]
            Custom embedding function; takes priority over ``client``.
        """
        provider = kwargs.get("provider", "external")
        dimension = int(kwargs.get("dimension", 1536))
        external_client = kwargs.get("client")
        embedding_fn: Callable = kwargs.get("embedding_fn")

        nodes: List[SayouNode] = []
        texts_to_embed: List[str] = []
        mapping_indices: List[int] = []

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

        vectors: List[List[float]] = []
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
                        "Provider is 'external' but neither 'client' nor "
                        "'embedding_fn' was supplied in kwargs."
                    )
            else:
                self._log(
                    f"Unknown provider '{provider}', falling back to stub.",
                    level="warning",
                )
                vectors = self._embed_stub(texts_to_embed, dimension)

        for idx, vector in zip(mapping_indices, vectors):
            nodes[idx].attributes["vector"] = vector
            nodes[idx].attributes["vector_dim"] = len(vector)

        return SayouOutput(nodes=nodes)

    def _embed_stub(self, texts: List[str], dimension: int) -> List[List[float]]:
        """Generate random unit vectors for testing (no external dependencies)."""
        self._log(f"[Stub] Generated {len(texts)} random vector(s) (dim={dimension}).")
        return [[random.random() for _ in range(dimension)] for _ in texts]

    def _embed_via_client(
        self, client: Any, texts: List[str], **kwargs
    ) -> List[List[float]]:
        """
        Delegate embedding to an external client object.

        Supports LangChain-style ``embed_documents()`` and OpenAI SDK clients.
        For other APIs, prefer supplying ``embedding_fn`` directly.
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
                raise RuntimeError(f"External client failed: {e}") from e

        raise ValueError(
            f"Unsupported client type: {type(client)}. "
            "Use 'embedding_fn' for custom embedding logic."
        )
