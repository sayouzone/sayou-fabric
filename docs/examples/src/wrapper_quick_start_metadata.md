!!! abstract "Source"
    Synced from [`packages/sayou-wrapper/examples/quick_start_metadata.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-wrapper/examples/quick_start_metadata.py).

## Setup

Enrich SayouNodes with computed metadata using `WrapperPipeline` with
`MetadataAdapter`.

`MetadataAdapter` accepts content dicts and a ``metadata_map`` — a mapping
of attribute names to callables.  Each callable receives the chunk text and
returns a value stored in the node's attributes.

Use this adapter to attach:
- Keyword lists (NLP / KeyBERT)
- Sentiment scores (VADER / transformers)
- Language tags (langdetect)
- Custom classification labels
- Summarisation results (LLM)

Install dependencies for real enrichment functions:

    pip install keybert langdetect

```python
import json

from sayou.wrapper.pipeline import WrapperPipeline
from sayou.wrapper.plugins.metadata_adapter import MetadataAdapter

pipeline = WrapperPipeline(extra_adapters=[MetadataAdapter])
```

## Custom Enrichment Functions

Pass a ``metadata_map`` dict where each key is the attribute name to store
and each value is a callable ``(text: str) -> Any``.

Functions are applied independently — if one raises, only that attribute is
set to None and the others continue.

```python
chunks = [
    {
        "content": "Sayou Fabric processes data for LLM retrieval pipelines.",
        "metadata": {"chunk_id": "c1"},
    },
    {
        "content": "The Connector library fetches data from 27 external sources.",
        "metadata": {"chunk_id": "c2"},
    },
    {
        "content": "Chunking splits documents into retrieval-ready SayouChunk objects.",
        "metadata": {"chunk_id": "c3"},
    },
]


# Simple deterministic enrichment functions (no external deps)
def word_count(text: str) -> int:
    return len(text.split())


def keyword_stub(text: str) -> list:
    """Return the 3 longest words as a keyword proxy."""
    words = sorted(text.split(), key=len, reverse=True)
    return [w.strip(".,;") for w in words[:3]]


def starts_with_capital(text: str) -> bool:
    return bool(text) and text[0].isupper()


output = pipeline.run(
    chunks,
    strategy="metadata",
    metadata_map={
        "word_count": word_count,
        "keywords": keyword_stub,
        "is_sentence": starts_with_capital,
    },
)

print("=== Custom Enrichment Functions ===")
for node in output.nodes:
    print(f"  [{node.node_id}]")
    print(f"    word_count  : {node.attributes.get('word_count')}")
    print(f"    keywords    : {node.attributes.get('keywords')}")
    print(f"    is_sentence : {node.attributes.get('is_sentence')}")
```

## Stub Mode

Pass ``use_stub=True`` with no ``metadata_map`` to generate placeholder
attributes for quick pipeline testing.

Stub output:
- ``summary``: first 20 chars of content + "..."
- ``keywords``: ["stub", "test", "keyword"]

```python
stub_output = pipeline.run(
    chunks[:2],
    strategy="metadata",
    use_stub=True,
)

print("\n=== Stub Mode ===")
for node in stub_output.nodes:
    print(f"  [{node.node_id}]")
    print(f"    summary  : {node.attributes.get('summary')!r}")
    print(f"    keywords : {node.attributes.get('keywords')}")
```

## Enrichment Error Handling

If an enrichment function raises, the attribute is set to None and
processing continues.  Other attributes on the same node are unaffected.

```python
def always_fails(text: str):
    raise RuntimeError("enrichment service unavailable")


def always_works(text: str) -> str:
    return "ok"


safe_output = pipeline.run(
    [{"content": "test", "metadata": {"chunk_id": "err-1"}}],
    strategy="metadata",
    metadata_map={
        "status": always_works,
        "broken_attr": always_fails,
    },
)

print("\n=== Enrichment Error Handling ===")
node = safe_output.nodes[0]
print(f"  status       : {node.attributes.get('status')!r}")
print(f"  broken_attr  : {node.attributes.get('broken_attr')!r}  (None = failed)")
```

## Integration with Real NLP (commented — requires external packages)

Example with KeyBERT for keyword extraction:

    from keybert import KeyBERT
    kw_model = KeyBERT()

    def extract_keywords(text: str) -> list:
        kws = kw_model.extract_keywords(text, top_n=5)
        return [kw for kw, _ in kws]

    output = pipeline.run(
        chunks,
        strategy="metadata",
        metadata_map={"keywords": extract_keywords},
    )

## Save Results

```python
result = [
    {
        "id": n.node_id,
        "attrs": {k: v for k, v in n.attributes.items() if k not in {"schema:text"}},
    }
    for n in output.nodes
]
with open("metadata_nodes.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

print(f"\nSaved {len(output.nodes)} node(s) to 'metadata_nodes.json'")
```