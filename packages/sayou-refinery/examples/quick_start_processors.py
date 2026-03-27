# ── Setup
"""
Apply Refinery processors to normalised `SayouBlock` objects.

Processors run **after** normalisation and operate on the block list.
Each processor is selected by `component_name` and executed in the order
given to `processors=`.

Available processors:

| Processor            | Works on         | Effect                                       |
|----------------------|------------------|----------------------------------------------|
| `WhiteSpaceProcessor`| text, record     | Collapse tabs/spaces; preserve paragraphs    |
| `TextCleaner`        | text, md         | Remove regex patterns; normalise whitespace  |
| `PiiMasker`          | text, md         | Mask emails → `[EMAIL]`, phones → `[PHONE]` |
| `LinkProcessor`      | text             | Extract URLs to metadata; optionally remove  |
| `Deduplicator`       | any              | Drop blocks with identical content           |
| `Imputer`            | record (dict)    | Fill `None` fields with default values       |
| `OutlierHandler`     | record (dict)    | Drop or clamp out-of-range numerical values  |
| `RecursivePruner`    | any              | Remove `None`, `""`, `[]`, `{}`, `"NULL"`    |
"""
import json

from sayou.refinery.normalizer.doc_markdown_normalizer import \
    DocMarkdownNormalizer
from sayou.refinery.normalizer.html_text_normalizer import HtmlTextNormalizer
from sayou.refinery.normalizer.record_normalizer import RecordNormalizer
from sayou.refinery.pipeline import RefineryPipeline
from sayou.refinery.plugins.link_processor import LinkProcessor
from sayou.refinery.plugins.white_space_processor import WhiteSpaceProcessor
from sayou.refinery.processor.deduplicator import Deduplicator
from sayou.refinery.processor.imputer import Imputer
from sayou.refinery.processor.outlier_handler import OutlierHandler
from sayou.refinery.processor.pii_masker import PiiMasker
from sayou.refinery.processor.recursive_pruner import RecursivePruner
from sayou.refinery.processor.text_cleaner import TextCleaner

# ── TextCleaner
"""
Removes regex patterns from `text` and `md` blocks, then collapses
multiple spaces and tabs to a single space.

Pair with `DocMarkdownNormalizer` to clean up parsed document text,
or with `HtmlTextNormalizer` to strip ad tags from web content.

Config:
- `patterns`        — list of regex strings to remove
- `normalize_space` — collapse whitespace (default `True`)
"""
cleaner_pipeline = RefineryPipeline(
    extra_normalizers=[DocMarkdownNormalizer],
    extra_processors=[TextCleaner],
)

md_doc = "# Title\n\n[AD] This   product   is   amazing. [AD] Buy now."

clean_blocks = cleaner_pipeline.run(
    md_doc,
    strategy="markdown",
    processors=["TextCleaner"],
    patterns=[r"\[AD\]"],
)

print("=== TextCleaner ===")
for b in clean_blocks:
    print(f"  {b.content!r}")


# ── PiiMasker
"""
Replaces email addresses with `[EMAIL]` and phone numbers with `[PHONE]`
using regex.  Operates on `text` and `md` blocks only.

Config:
- `mask_email` — default `True`
- `mask_phone` — default `True`
"""
pii_pipeline = RefineryPipeline(
    extra_normalizers=[HtmlTextNormalizer],
    extra_processors=[PiiMasker],
)

html = (
    "<html><body>"
    "<p>Contact alice@example.com or call 010-1234-5678.</p>"
    "<p>Billing: billing@corp.com</p>"
    "</body></html>"
)

try:
    pii_blocks = pii_pipeline.run(
        html,
        strategy="html",
        processors=["PiiMasker"],
    )
    print("\n=== PiiMasker ===")
    for b in pii_blocks:
        print(f"  {b.content.strip()!r}")
except Exception:
    # BeautifulSoup not installed
    print("\n=== PiiMasker === (install beautifulsoup4 to run)")


# ── LinkProcessor
"""
Scans `text` blocks for raw URLs and Markdown links, extracts them to
`block.metadata["links"]`, and optionally removes them from the text.

Each entry in `metadata["links"]`: `{"title": str, "url": str}`

Config:
- `remove_links` — strip matched links from content (default `False`)
"""
link_pipeline = RefineryPipeline(
    extra_normalizers=[DocMarkdownNormalizer],
    extra_processors=[LinkProcessor],
)

link_md = (
    "Read the [docs](https://docs.sayouzone.com) for details. "
    "Source: https://github.com/sayouzone/sayou-fabric"
)

link_blocks = link_pipeline.run(
    link_md,
    strategy="markdown",
    processors=["LinkProcessor"],
    remove_links=False,
)

print("\n=== LinkProcessor ===")
for b in link_blocks:
    for lk in b.metadata.get("links", []):
        print(f"  [{lk['title']:30s}] → {lk['url']}")


# ── WhiteSpaceProcessor
"""
Cleans invisible characters (`\xa0`, `\u200b`), collapses consecutive
spaces and tabs to one, and limits consecutive newlines to two.

Works on `text` blocks and `record` blocks (cleans all string fields).

Config:
- `preserve_newlines` — keep paragraph breaks (default `True`).
                        Set `False` to flatten everything to one line.
"""
ws_pipeline = RefineryPipeline(
    extra_normalizers=[RecordNormalizer],
    extra_processors=[WhiteSpaceProcessor],
)

messy_record = {
    "id": "r-001",
    "bio": "loves  coding\xa0and\u200b data\t\tpipelines",
    "note": "paragraph one\n\n\n\nparagraph two",
}

ws_blocks = ws_pipeline.run(
    messy_record,
    strategy="record",
    processors=["WhiteSpaceProcessor"],
)

print("\n=== WhiteSpaceProcessor ===")
for b in ws_blocks:
    if isinstance(b.content, dict):
        print(f"  bio  : {b.content.get('bio')!r}")
        print(f"  note : {b.content.get('note')!r}")


# ── Deduplicator
"""
Hashes the content of each block and drops duplicates on sight.
Blocks shorter than 5 characters bypass hashing and are always kept.

Useful after collecting from multiple sources that may overlap.
"""
dedup_pipeline = RefineryPipeline(
    extra_normalizers=[DocMarkdownNormalizer],
    extra_processors=[Deduplicator],
)

duped_md = (
    "# Introduction\n\nSayou Fabric processes data for LLM pipelines.\n\n"
    "# Introduction\n\nSayou Fabric processes data for LLM pipelines.\n\n"
    "# Architecture\n\nEight libraries coordinate through Brain."
)

dedup_blocks = dedup_pipeline.run(
    duped_md,
    strategy="markdown",
    processors=["Deduplicator"],
)

print("\n=== Deduplicator ===")
print(f"  Unique blocks : {len(dedup_blocks)}")
for b in dedup_blocks:
    print(f"  {b.content[:60]!r}")


# ── Imputer
"""
Fills `None` values in `record`-type blocks using field → default rules.
Non-record blocks and fields with existing values are left unchanged.

Pair with `RecordNormalizer` for database rows with optional fields.

Config:
- `imputation_rules` — `{field_name: default_value, …}`
"""
impute_pipeline = RefineryPipeline(
    extra_normalizers=[RecordNormalizer],
    extra_processors=[Imputer],
)

sparse_rows = [
    {"id": "1", "name": "Alice", "category": None, "score": 95},
    {"id": "2", "name": "Bob", "category": "A", "score": None},
    {"id": "3", "name": "Carol", "category": None, "score": None},
]

imputed_blocks = impute_pipeline.run(
    sparse_rows,
    strategy="record",
    processors=["Imputer"],
    imputation_rules={"category": "Unknown", "score": 0},
)

print("\n=== Imputer ===")
for b in imputed_blocks:
    if isinstance(b.content, list):
        for row in b.content:
            print(
                f"  id={row.get('id')}  category={row.get('category')!r}  score={row.get('score')}"
            )
    elif isinstance(b.content, dict):
        print(
            f"  id={b.content.get('id')}  category={b.content.get('category')!r}  score={b.content.get('score')}"
        )


# ── OutlierHandler
"""
Validates numerical fields against `min`/`max` rules and either
drops the block (`action="drop"`) or clamps the value (`action="clamp"`).

Only `record`-type blocks with `dict` content are processed.

Config:
- `outlier_rules` — `{field: {"min": …, "max": …, "action": "drop"|"clamp"}}`
"""
outlier_pipeline = RefineryPipeline(
    extra_normalizers=[RecordNormalizer],
    extra_processors=[OutlierHandler],
)

score_rows = [
    {"id": "1", "name": "Alice", "score": 95},
    {"id": "2", "name": "Bob", "score": -5},  # violates min=0 → clamped
    {"id": "3", "name": "Carol", "score": 200},  # violates max=100 → clamped
    {"id": "4", "name": "Dave", "score": 80},
]

outlier_blocks = outlier_pipeline.run(
    score_rows,
    strategy="record",
    processors=["OutlierHandler"],
    outlier_rules={"score": {"min": 0, "max": 100, "action": "clamp"}},
)

print("\n=== OutlierHandler (clamp) ===")
for b in outlier_blocks:
    rows = b.content if isinstance(b.content, list) else [b.content]
    for row in rows:
        if isinstance(row, dict):
            print(f"  id={row.get('id')}  score={row.get('score')}")


# ── RecursivePruner
"""
Walks the entire content tree and removes:
- `None` values
- Empty strings `""`
- Empty lists `[]` and dicts `{}`
- Strings equal to `"NULL"`, `"NONE"`, `"NAN"` (case-insensitive)

Blocks whose content is entirely pruned away are dropped.
"""
prune_pipeline = RefineryPipeline(
    extra_normalizers=[RecordNormalizer],
    extra_processors=[RecursivePruner],
)

dirty_rows = [
    {"id": "1", "name": "Alice", "address": None, "tags": []},
    {"id": "2", "name": "NULL", "address": None},  # will be dropped
    {"id": "3", "name": "Bob", "address": "Seoul", "extra": {"x": None}},
]

pruned_blocks = prune_pipeline.run(
    dirty_rows,
    strategy="record",
    processors=["RecursivePruner"],
)

print("\n=== RecursivePruner ===")
print(f"  Input rows    : {len(dirty_rows)}")
print(f"  Output blocks : {len(pruned_blocks)}")
for b in pruned_blocks:
    rows = b.content if isinstance(b.content, list) else [b.content]
    for row in rows:
        if isinstance(row, dict):
            print(f"  {row}")


# ── Chaining Multiple Processors
"""
Pass an ordered list to `processors=` to apply them in sequence.
The output of each processor becomes the input of the next.
"""
chain_pipeline = RefineryPipeline(
    extra_normalizers=[RecordNormalizer],
    extra_processors=[Imputer, OutlierHandler, RecursivePruner],
)

raw = [
    {"id": "1", "name": "Alice", "score": 95, "note": None},
    {"id": "2", "name": "Bob", "score": -10, "note": ""},
    {"id": "3", "name": "Carol", "score": 150, "note": "top performer"},
]

chained = chain_pipeline.run(
    raw,
    strategy="record",
    processors=["Imputer", "OutlierHandler", "RecursivePruner"],
    imputation_rules={"note": "n/a"},
    outlier_rules={"score": {"min": 0, "max": 100, "action": "clamp"}},
)

print("\n=== Chaining Multiple Processors ===")
for b in chained:
    rows = b.content if isinstance(b.content, list) else [b.content]
    for row in rows:
        if isinstance(row, dict):
            print(f"  {row}")


# ── Save Results
output = [b.model_dump() for b in imputed_blocks]
with open("processors_output.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved to 'processors_output.json'")
