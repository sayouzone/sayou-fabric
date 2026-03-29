!!! abstract "Source"
    Synced from [`packages/sayou-assembler/examples/quick_start_vector.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-assembler/examples/quick_start_vector.py).

## Setup

Build vector payloads from SayouNodes using `AssemblerPipeline` with
`VectorBuilder`.

`VectorBuilder` reads the ``schema:text`` attribute from each node,
computes embeddings via an injected ``embedding_fn``, and produces a
list of vector payloads ready for vector databases (Chroma, Qdrant,
Pinecone, Weaviate, …).

Each payload contains:
- ``id``       — the node_id
- ``vector``   — the embedding vector (empty list if no embedding_fn)
- ``text``     — the raw text content
- ``metadata`` — node_class, friendly_name, and all node attributes

The typical data flow:

    ChunkingPipeline → WrapperPipeline (EmbeddingAdapter)
                     → AssemblerPipeline (VectorBuilder)
                     → LoaderPipeline (ChromaWriter / ElasticsearchWriter)

```python
import json

from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.builder.vector_builder import VectorBuilder
from sayou.assembler.pipeline import AssemblerPipeline

pipeline = AssemblerPipeline(extra_builders=[VectorBuilder])
```

## Basic Vector Payload Generation

Pass a ``SayouOutput`` where nodes already carry ``schema:text`` attributes.
Provide ``embedding_fn`` to compute vectors.

``embedding_fn`` signature: ``(text: str) -> List[float]``

```python
def mock_embed(text: str):
    """Return a 4-dim vector based on text length (deterministic stub)."""
    n = len(text)
    return [n / 100.0, n / 200.0, n / 400.0, n / 800.0]


nodes = [
    SayouNode(
        node_id="sayou:doc:guide_pdf:c001",
        node_class="sayou:Text",
        friendly_name="Intro paragraph",
        attributes={"schema:text": "Sayou Fabric is a modular LLM data pipeline."},
    ),
    SayouNode(
        node_id="sayou:doc:guide_pdf:c002",
        node_class="sayou:Topic",
        friendly_name="Architecture heading",
        attributes={"schema:text": "Architecture overview of the eight libraries."},
    ),
    SayouNode(
        node_id="sayou:doc:guide_pdf:c003",
        node_class="sayou:Table",
        friendly_name="Library table",
        attributes={"schema:text": "Connector | Collection | SayouPacket"},
    ),
]

output = SayouOutput(nodes=nodes)
payloads = pipeline.run(output, strategy="VectorBuilder", embedding_fn=mock_embed)

print("=== Basic Vector Payload Generation ===")
print(f"  Payloads produced : {len(payloads)}")
for p in payloads:
    print(
        f"  [{p['id'].split(':')[-1]:6s}] dim={len(p['vector'])}  "
        f"vec={[round(v, 3) for v in p['vector']]}"
    )
```

## Nodes Without Text Are Skipped

Nodes with empty or absent ``schema:text`` are excluded from the output.
This prevents zero-vector noise in the vector store.

```python
mixed_nodes = [
    SayouNode(
        node_id="n1", node_class="Node", attributes={"schema:text": "Has content."}
    ),
    SayouNode(node_id="n2", node_class="Node", attributes={}),  # no text
    SayouNode(
        node_id="n3", node_class="Node", attributes={"schema:text": "Also has content."}
    ),
]

mixed_payloads = pipeline.run(
    SayouOutput(nodes=mixed_nodes),
    strategy="VectorBuilder",
    embedding_fn=mock_embed,
)

print("\n=== Nodes Without Text Skipped ===")
print(f"  Input nodes    : 3")
print(f"  Output payloads: {len(mixed_payloads)}  (n2 skipped — no schema:text)")
```

## Metadata in Payload

Each payload's ``metadata`` field includes the node class and friendly name,
plus all node attributes.  This metadata is stored alongside the vector in
the vector database for filtered search.

```python
payload = payloads[0]
print("\n=== Metadata in Payload ===")
print(f"  id            : {payload['id']}")
print(f"  text[:40]     : {payload['text'][:40]!r}")
print(f"  metadata keys : {list(payload['metadata'].keys())}")
print(f"  node_class    : {payload['metadata']['node_class']}")
```

## No embedding_fn — Empty Vectors

If no ``embedding_fn`` is supplied, vectors are empty lists.
This is valid for inspecting the payload structure without API calls.

```python
no_embed_payloads = pipeline.run(
    SayouOutput(nodes=nodes[:2]),
    strategy="VectorBuilder",
)

print("\n=== No embedding_fn (Empty Vectors) ===")
for p in no_embed_payloads:
    print(f"  [{p['id'].split(':')[-1]:6s}] vector={p['vector']}")
```

## Real embedding_fn examples (commented — require external packages)

sentence-transformers:

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding_fn = lambda text: model.encode(text).tolist()

OpenAI:

    import openai
    client = openai.OpenAI()
    def embedding_fn(text):
        resp = client.embeddings.create(input=[text], model="text-embedding-3-small")
        return resp.data[0].embedding

## Save Results

```python
with open("vector_payloads.json", "w", encoding="utf-8") as f:
    json.dump(payloads, f, indent=2, ensure_ascii=False, default=str)

print(f"\nSaved {len(payloads)} vector payload(s) to 'vector_payloads.json'")
```