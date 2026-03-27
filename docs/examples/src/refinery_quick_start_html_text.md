!!! abstract "Source"
    Synced from [`packages/sayou-refinery/examples/quick_start_html_text.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-refinery/examples/quick_start_html_text.py).

## Setup

Normalise a `Document` object into Markdown `SayouBlock` objects using
`RefineryPipeline` with `DocMarkdownNormalizer`.

`DocMarkdownNormalizer` accepts the output of `DocumentPipeline` (a Pydantic
`Document` model or its `.model_dump()` dict) and converts each page into
one `SayouBlock` of type `"md"`.  Images become separate `"image_base64"`
blocks that are emitted directly without being merged into the page text.

Element mapping:

| Document element   | Markdown output                      |
|--------------------|--------------------------------------|
| Heading (level N)  | `#`…`#` prefix                      |
| List item (level L)| `  ` × L + `- ` prefix              |
| Plain text         | as-is                                |
| Table              | GFM pipe table                       |
| Image (base64)     | separate `image_base64` SayouBlock   |
| Chart              | `--- Chart Data ---` text block      |

```python
import json

from sayou.core.schemas import SayouBlock

from sayou.refinery.normalizer.doc_markdown_normalizer import \
    DocMarkdownNormalizer
from sayou.refinery.pipeline import RefineryPipeline

pipeline = RefineryPipeline(extra_normalizers=[DocMarkdownNormalizer])

SAMPLE_DOC = {
    "file_name": "report.pdf",
    "file_id": "report",
    "doc_type": "pdf",
    "metadata": {"title": "Sayou Fabric Report", "author": "Platform Team"},
    "page_count": 2,
    "pages": [
        {
            "page_num": 1,
            "elements": [
                {
                    "type": "text",
                    "id": "h1",
                    "text": "Sayou Fabric Overview",
                    "raw_attributes": {"semantic_type": "heading", "heading_level": 1},
                    "meta": {"page_num": 1},
                },
                {
                    "type": "text",
                    "id": "h2",
                    "text": "Architecture",
                    "raw_attributes": {"semantic_type": "heading", "heading_level": 2},
                    "meta": {"page_num": 1},
                },
                {
                    "type": "text",
                    "id": "p1",
                    "text": "Eight libraries coordinate through Brain.",
                    "raw_attributes": {},
                    "meta": {"page_num": 1},
                },
                {
                    "type": "text",
                    "id": "li1",
                    "text": "Connector — data collection",
                    "raw_attributes": {"semantic_type": "list", "list_level": 0},
                    "meta": {"page_num": 1},
                },
                {
                    "type": "text",
                    "id": "li2",
                    "text": "Document — file parsing",
                    "raw_attributes": {"semantic_type": "list", "list_level": 0},
                    "meta": {"page_num": 1},
                },
                {
                    "type": "text",
                    "id": "li3",
                    "text": "PdfParser sub-strategy",
                    "raw_attributes": {"semantic_type": "list", "list_level": 1},
                    "meta": {"page_num": 1},
                },
                {
                    "type": "table",
                    "id": "tbl1",
                    "data": [
                        ["Layer", "Library", "Output"],
                        ["Collect", "Connector", "SayouPacket"],
                        ["Parse", "Document", "Document"],
                    ],
                    "meta": {"page_num": 1},
                },
            ],
            "header_elements": [],
            "footer_elements": [],
        },
        {
            "page_num": 2,
            "elements": [
                {
                    "type": "text",
                    "id": "h2b",
                    "text": "Getting Started",
                    "raw_attributes": {"semantic_type": "heading", "heading_level": 2},
                    "meta": {"page_num": 2},
                },
                {
                    "type": "image",
                    "id": "img1",
                    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQ",
                    "image_format": "png",
                    "ocr_text": "Architecture diagram",
                    "meta": {"page_num": 2},
                },
                {
                    "type": "text",
                    "id": "p2",
                    "text": "Install with pip and run.",
                    "raw_attributes": {},
                    "meta": {"page_num": 2},
                },
            ],
            "header_elements": [],
            "footer_elements": [],
        },
    ],
}
```

## Basic Normalisation

Pass the document dict (or a `Document` Pydantic model) with
`strategy="markdown"`.  Returns one `SayouBlock` per page, plus separate
`image_base64` blocks when the page contains images.

```python
blocks = pipeline.run(SAMPLE_DOC, strategy="markdown")

print("=== Basic Normalisation ===")
print(f"  Total blocks: {len(blocks)}")
for i, b in enumerate(blocks):
    preview = str(b.content)[:60].replace("\n", "↵")
    print(f"  [{i}] type={b.type:14s} page={b.metadata.get('page_num')} {preview!r}")
```

## Markdown Formatting

Inspect the first page block to see the Markdown output:
headings with `#` prefix, list items with `- ` prefix and indentation,
and a GFM pipe table.

```python
md_blocks = [b for b in blocks if b.type == "md"]
print("\n=== Markdown Formatting (page 1) ===")
print(md_blocks[0].content)
```

## Image Blocks

`image_base64` blocks are emitted as separate entries so downstream
processes can handle text and images independently.

```python
img_blocks = [b for b in blocks if b.type == "image_base64"]
print("\n=== Image Blocks ===")
for b in img_blocks:
    print(f"  alt_text : {b.metadata.get('alt_text')!r}")
    print(f"  format   : {b.metadata.get('format')}")
    print(f"  base64   : {str(b.content)[:40]}…")
```

## Include Headers and Footers

By default only body elements are included (`include_headers=True`,
`include_footers=False`).  Pass these flags to control the output.

```python
doc_with_hf = {**SAMPLE_DOC}
doc_with_hf["pages"] = [
    {
        **SAMPLE_DOC["pages"][0],
        "header_elements": [
            {
                "type": "text",
                "id": "hdr1",
                "text": "CONFIDENTIAL",
                "raw_attributes": {},
                "meta": {"page_num": 1},
            }
        ],
        "footer_elements": [
            {
                "type": "text",
                "id": "ftr1",
                "text": "Page 1 of 2",
                "raw_attributes": {},
                "meta": {"page_num": 1},
            }
        ],
    },
    SAMPLE_DOC["pages"][1],
]

blocks_hf = pipeline.run(
    doc_with_hf,
    strategy="markdown",
    include_headers=True,
    include_footers=True,
)
combined = " | ".join(b.content for b in blocks_hf if b.type == "md")
print("\n=== Include Headers and Footers ===")
print(f"  Header present: {'CONFIDENTIAL' in combined}")
print(f"  Footer present: {'Page 1 of 2' in combined}")
```

## Save Results

```python
output = [b.model_dump() for b in blocks]
with open("doc_markdown_blocks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(blocks)} block(s) to 'doc_markdown_blocks.json'")
```