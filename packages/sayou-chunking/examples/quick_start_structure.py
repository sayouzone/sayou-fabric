# ── Setup
"""
Split structured text and record lists using `StructureSplitter`.

`StructureSplitter` has two operating modes selected automatically based on
the block's `type` and `content`:

| Mode          | Trigger                                    | Use case                         |
|---------------|--------------------------------------------|----------------------------------|
| **Text mode** | `content` is a string                      | Legal text, contracts, articles  |
| **Record mode** | `type="record"` and `content` is a list  | Transcripts, log lines, CSV rows |

**Text mode** — splits on a user-defined regex pattern first
(`structure_pattern`), then applies `RecursiveSplitter` on any section
that still exceeds `chunk_size`.

**Record mode** — groups list records by either:
- `chapter_intervals`: explicit `(start, end, title)` time ranges
- `window_size`:       a rolling time window (e.g., every 300 seconds)
"""
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.splitter.structure_splitter import StructureSplitter

pipeline = ChunkingPipeline(extra_splitters=[StructureSplitter])
print("Pipeline initialized.")


# ── Text Mode: Article-based Split
"""
Legal and regulatory documents often use numbered articles as primary
structural boundaries.  Pass a regex `structure_pattern` that matches
those boundaries; `StructureSplitter` splits there first and then handles
any oversized sections with recursive sub-splitting.

Each chunk carries:
- `metadata.parent_structure_idx` — zero-based section index
- `metadata.chunk_id`             — `{doc_id}_s{section}` or `{doc_id}_s{section}_p{part}`
"""
legal_text = """\
제1조 (목적)
이 약관은 Sayou Fabric 플랫폼의 이용 조건을 규정합니다.
모든 이용자는 본 약관에 동의하는 것으로 간주됩니다.

제2조 (이용 범위)
이용자는 상업적 제품에 플랫폼을 통합할 수 있으며,
문서 및 사용자 접점에서 출처 표기를 유지해야 합니다.

제3조 (금지 행위)
역설계, 무단 배포, 재라이선싱은 엄격히 금지됩니다.
위반 시 즉각적인 이용 정지 조치가 취해집니다.

제4조 (면책 조항)
플랫폼은 현 상태로 제공되며 운영사는 특정 목적 적합성을
보증하지 않습니다.
"""

text_chunks = pipeline.run(
    {
        "content": legal_text,
        "metadata": {"id": "contract"},
        "config": {
            "chunk_size": 300,
            "chunk_overlap": 0,
            "structure_pattern": r"제\d+조",
        },
    },
    strategy="structure",
)

print("=== Text Mode: Article-based Split ===")
for chunk in text_chunks:
    idx = chunk.metadata.get("parent_structure_idx", "?")
    print(f"  [section {idx}] {chunk.content[:70]!r}")


# ── Text Mode: HTML / Code Fence Detection
"""
`StructureSplitter` auto-selects for HTML and code-fence content when
`strategy="auto"` and the block type is `"html"` or content starts with
`<html`.  Pass `strategy="structure"` explicitly to force selection.
"""
html_content = """\
<html>
<body>
<h1>Introduction</h1>
<p>This document covers the basics of RAG pipelines.</p>
<h2>Chunking</h2>
<p>Chunking divides documents into retrieval-ready pieces.</p>
</body>
</html>
"""

html_chunks = pipeline.run(
    {
        "content": html_content,
        "metadata": {"id": "html_doc"},
        "config": {"chunk_size": 200, "chunk_overlap": 0},
    },
    strategy="structure",
)

print("\n=== Text Mode: HTML ===")
for chunk in html_chunks:
    print(f"  [{chunk.metadata.get('chunk_id')}] {chunk.content[:60]!r}")


# ── Record Mode: Chapter Intervals
"""
Transcript cues (from YouTube or podcast) are a list of timed records.
Define chapter boundaries as `(start_sec, end_sec, title)` tuples.
`StructureSplitter` assigns each cue to the chapter whose time range
contains its `start` value and merges the cue texts.

Each chunk carries:
- `metadata.chapter_title`    — chapter name
- `metadata.sayou:startTime`  — start time of the first cue
- `metadata.sayou:endTime`    — end time of the last cue
- `metadata.record_count`     — number of cues merged
"""
from sayou.core.schemas import SayouBlock

transcript_cues = [
    {"text": "Welcome to the session.", "start": 0.0, "duration": 3.0},
    {"text": "Today we cover chunking.", "start": 3.0, "duration": 4.0},
    {"text": "Recursive splitting is flexible.", "start": 65.0, "duration": 5.0},
    {"text": "Fixed length is predictable.", "start": 70.0, "duration": 4.0},
    {"text": "Semantic splitting groups ideas.", "start": 130.0, "duration": 5.0},
    {"text": "Choose based on your use case.", "start": 135.0, "duration": 3.0},
    {"text": "Thanks for joining us today.", "start": 185.0, "duration": 3.0},
]

chapter_intervals = [
    (0, 60, "Introduction"),
    (60, 120, "Text Splitting Strategies"),
    (120, 180, "Semantic Splitting"),
    (180, 240, "Closing"),
]

record_block = SayouBlock(
    type="record",
    content=transcript_cues,
    metadata={
        "id": "lecture_001",
        "config": {"chapter_intervals": chapter_intervals},
    },
)

chapter_chunks = pipeline.run(record_block, strategy="structure")

print("\n=== Record Mode: Chapter Intervals ===")
for chunk in chapter_chunks:
    m = chunk.metadata
    print(
        f"  [{m.get('chapter_title'):30s}]  "
        f"cues={m.get('record_count')}  "
        f"start={m.get('sayou:startTime')}s  "
        f"end={m.get('sayou:endTime')}s"
    )
    print(f"    {chunk.content[:80]!r}")


# ── Record Mode: Time Window
"""
When chapter boundaries are unknown, use `window_size` (seconds) to group
cues into fixed-duration chunks.  Consecutive cues are accumulated until
the window duration is reached, then a new chunk begins.
"""
window_block = SayouBlock(
    type="record",
    content=transcript_cues,
    metadata={
        "id": "lecture_002",
        "config": {"window_size": 60, "window_key": "start"},
    },
)

window_chunks = pipeline.run(window_block, strategy="structure")

print("\n=== Record Mode: Time Window (60s) ===")
for chunk in window_chunks:
    m = chunk.metadata
    print(
        f"  cues={m.get('record_count')}  "
        f"start={m.get('sayou:startTime')}s  "
        f"duration={m.get('sayou:duration', 0):.1f}s  "
        f"text={chunk.content[:60]!r}"
    )


# ── Save Results
"""
Serialise text-mode and record-mode chunks to JSON.
"""
output = {
    "text_mode": [c.model_dump() for c in text_chunks],
    "record_chapters": [c.model_dump() for c in chapter_chunks],
    "record_windows": [c.model_dump() for c in window_chunks],
}
with open("structure_chunks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved to structure_chunks.json")
