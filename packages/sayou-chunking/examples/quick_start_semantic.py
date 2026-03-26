# ── Setup
"""
Split text by semantic coherence using `SemanticSplitter`.

`SemanticSplitter` identifies topic shifts by measuring the similarity
between adjacent sentences.  When similarity drops below `semantic_threshold`,
a new chunk begins.  Sentences above the threshold are grouped together.

The splitter is encoder-agnostic: it accepts any callable that maps a
sentence string to a float vector.  In production, supply a real embedding
model (e.g. a sentence-transformers model).  By default it uses a
character-frequency mock encoder — useful for pipeline testing without GPU
or API dependencies.

This example demonstrates:
1. Default mock encoder — pipeline dry-run, no external dependencies.
2. Custom encoder — plug in any embedding function.
3. Threshold tuning — how `semantic_threshold` affects granularity.
"""
import json
import math

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.splitter.semantic_splitter import SemanticSplitter

pipeline = ChunkingPipeline(extra_splitters=[SemanticSplitter])
print("Pipeline initialized.")

TEXT = """\
Retrieval-Augmented Generation combines a retrieval system with a language model.
The retriever finds passages relevant to the user's query.
Those passages are injected into the model's context window.
The model then generates an answer grounded in the retrieved evidence.

Chunking is a critical preprocessing step in RAG.
How you divide documents directly affects what the retriever can find.
Chunks that are too large dilute the relevance signal.
Chunks that are too small lose surrounding context.

Semantic chunking groups sentences by topic similarity.
Adjacent sentences with high cosine similarity are kept together.
A sharp drop in similarity signals a topic change and starts a new chunk.
This produces chunks that are coherent in meaning, not just in length.
"""


# ── Default Mock Encoder
"""
The built-in `_simple_frequency_encoder` converts each sentence to a
10-dimensional character-frequency vector and normalises it.  It is a
placeholder for testing — it does not produce meaningful semantic clusters.

`packet.data["metadata"]["semantic_type"]` is always `"semantic_group"`.
`chunk_id` follows the pattern `{doc_id}_{index}`.
"""
chunks = pipeline.run(
    {
        "content": TEXT,
        "metadata": {"id": "rag_intro"},
        "config": {"semantic_threshold": 0.8},
    },
    strategy="semantic",
)

print("=== Default Mock Encoder ===")
for i, chunk in enumerate(chunks):
    print(f"  [{i}] {len(chunk.content):4d} chars | {chunk.content[:70]!r}")


# ── Custom Encoder
"""
Pass any function as `encoder_function` via `config`.

The encoder must accept a sentence string and return a list of floats.
The splitter computes cosine similarity between adjacent sentence vectors
and inserts a chunk boundary when similarity < `semantic_threshold`.

This example uses a simple word-overlap encoder to illustrate the interface.
In production, replace it with `sentence_transformers` or an API call:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def embed(text: str) -> list:
    return model.encode(text).tolist()
```
"""


def word_overlap_encoder(text: str) -> list:
    """
    Encodes text as a 50-dim binary bag-of-words vector (hashed).
    Sentences with shared vocabulary score higher similarity.
    """
    dim = 50
    vec = [0.0] * dim
    for word in text.lower().split():
        vec[hash(word) % dim] += 1.0
    magnitude = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / magnitude for x in vec]


custom_chunks = pipeline.run(
    {
        "content": TEXT,
        "metadata": {"id": "rag_intro_custom"},
        "config": {
            "encoder_function": word_overlap_encoder,
            "semantic_threshold": 0.3,
        },
    },
    strategy="semantic",
)

print("\n=== Custom Word-Overlap Encoder (threshold=0.3) ===")
for i, chunk in enumerate(custom_chunks):
    print(f"  [{i}] {len(chunk.content):4d} chars | {chunk.content[:70]!r}")


# ── Threshold Tuning
"""
`semantic_threshold` controls chunk granularity:

- High threshold (e.g. 0.9) → many chunk boundaries → fine-grained chunks
- Low threshold  (e.g. 0.1) → few chunk boundaries → coarse-grained chunks

Run the same text at several threshold values and compare chunk counts.
"""
print("\n=== Threshold Tuning ===")
for threshold in [0.1, 0.3, 0.5, 0.7, 0.9]:
    result = pipeline.run(
        {
            "content": TEXT,
            "config": {
                "encoder_function": word_overlap_encoder,
                "semantic_threshold": threshold,
            },
        },
        strategy="semantic",
    )
    print(f"  threshold={threshold:.1f}  →  {len(result):2d} chunk(s)")


# ── Save Results
"""
Save both encoder results to JSON for comparison.
"""
output = {
    "mock_encoder": [c.model_dump() for c in chunks],
    "custom_encoder": [c.model_dump() for c in custom_chunks],
}
with open("semantic_chunks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved to semantic_chunks.json")
