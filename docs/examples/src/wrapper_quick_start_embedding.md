!!! abstract "Source"
    Synced from [`packages/sayou-wrapper/examples/quick_start_embedding.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-wrapper/examples/quick_start_embedding.py).

## Setup

Attach vector embeddings to SayouNodes using `WrapperPipeline` with
`EmbeddingAdapter`.

`EmbeddingAdapter` takes a list of content dicts, creates `SayouNode`
objects, and attaches dense vector embeddings.

Two execution modes are supported:

``external``
    Delegates to a ``client`` (LangChain-style or OpenAI SDK) or a
    custom ``embedding_fn`` callable.
``stub``
    Generates random vectors — useful for testing without API keys.

Install dependencies for real embeddings:

    pip install openai          # OpenAI
    pip install langchain-openai  # LangChain + OpenAI

```python
import json

from sayou.wrapper.pipeline import WrapperPipeline
from sayou.wrapper.plugins.embedding_adapter import EmbeddingAdapter

pipeline = WrapperPipeline(extra_adapters=[EmbeddingAdapter])
```

## Stub Embeddings (no API key needed)

Pass ``provider="stub"`` and ``dimension=N`` to generate random vectors.
Useful for verifying the pipeline structure before connecting a real model.

```python
chunks = [
    {
        "content": "Sayou Connector fetches data from external sources.",
        "metadata": {"chunk_id": "c1", "source": "overview.pdf"},
    },
    {
        "content": "Sayou Chunking splits documents into retrieval-ready pieces.",
        "metadata": {"chunk_id": "c2", "source": "overview.pdf"},
    },
    {
        "content": "Sayou Wrapper maps chunks into the Sayou ontology.",
        "metadata": {"chunk_id": "c3", "source": "overview.pdf"},
    },
]

output = pipeline.run(
    chunks,
    strategy="embedding",
    provider="stub",
    dimension=8,
)

print("=== Stub Embeddings ===")
print(f"  Nodes produced : {len(output.nodes)}")
for node in output.nodes:
    vec = node.attributes.get("vector", [])
    print(
        f"  [{node.node_id}] dim={len(vec)}  vec[:3]={[round(v, 3) for v in vec[:3]]}"
    )
```

## Custom embedding_fn

Supply any callable that accepts a list of strings and returns a
list of float vectors.  This works with sentence-transformers,
Cohere, and any other embedding library.

Example with sentence-transformers (not installed in this example):

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding_fn = lambda texts: model.encode(texts).tolist()

```python
# Deterministic mock: vector = [len(text), len(text)/10, 0.0, 0.0]
def mock_embedding_fn(texts):
    return [[float(len(t)), len(t) / 10.0, 0.0, 0.0] for t in texts]


custom_output = pipeline.run(
    chunks,
    strategy="embedding",
    provider="external",
    embedding_fn=mock_embedding_fn,
)

print("\n=== Custom embedding_fn ===")
for node in custom_output.nodes:
    vec = node.attributes.get("vector", [])
    print(f"  [{node.node_id}] vec={vec}")
```

## Empty content skipped

Nodes with empty or non-string content are created but receive no vector.
This prevents wasted API calls for empty chunks.

```python
mixed_chunks = [
    {"content": "Non-empty content.", "metadata": {"chunk_id": "m1"}},
    {"content": "", "metadata": {"chunk_id": "m2"}},
    {"content": "Another sentence.", "metadata": {"chunk_id": "m3"}},
]

mixed_output = pipeline.run(
    mixed_chunks, strategy="embedding", provider="stub", dimension=4
)

print("\n=== Empty Content Skipped ===")
for node in mixed_output.nodes:
    has_vec = "vector" in node.attributes
    print(f"  [{node.node_id}] has_vector={has_vec}")
```

## OpenAI client (commented — requires OPENAI_API_KEY)

To use the OpenAI client directly:

    import openai
    client = openai.OpenAI()

    output = pipeline.run(
        chunks,
        strategy="embedding",
        provider="external",
        client=client,
        model="text-embedding-3-small",
    )

## Save Results

```python
result = [
    {"id": n.node_id, "vector_dim": n.attributes.get("vector_dim", 0)}
    for n in output.nodes
]
with open("embedding_nodes.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(output.nodes)} node(s) to 'embedding_nodes.json'")
```