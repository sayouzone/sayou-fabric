!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_obsidian.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_obsidian.py).

## Setup

Transfer an Obsidian vault to a local archive using `TransferPipeline`.

`ObsidianGenerator` recursively walks a vault directory and yields one task
per Markdown file.  `ObsidianFetcher` reads each `.md` file as UTF-8 text.

No external dependencies or credentials are required — the vault is a
local directory on disk.  The example below creates a temporary vault so
it runs without any existing Obsidian installation.

```bash
python quick_start_obsidian.py
```

```python
import json
import os
import tempfile

from sayou.brain.pipelines.transfer import TransferPipeline


def setup_demo_vault() -> str:
    """Create a temporary vault directory with sample notes."""
    vault = tempfile.mkdtemp(prefix="obsidian_vault_")

    notes = {
        "index.md": "# Index\n\nWelcome to the vault.\n",
        "projects/sayou_fabric.md": "# Sayou Fabric\n\n## Overview\n\nLLM data pipeline library.\n\n## Status\n\nActive development.\n",
        "projects/chunking.md": "# Chunking\n\n## Splitters\n\n- RecursiveSplitter\n- MarkdownSplitter\n- CodeSplitter\n",
        "daily/2024-04-01.md": "# 2024-04-01\n\n## Done\n\n- Completed PR review\n- Updated docs\n",
        "daily/2024-04-02.md": "# 2024-04-02\n\n## Done\n\n- Merged chunking PR\n- Tagged v0.4.0\n",
        "references/rag_patterns.md": "# RAG Patterns\n\nRetrieve-Augment-Generate patterns for production.\n",
    }

    for path, content in notes.items():
        full = os.path.join(vault, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    return vault


VAULT_PATH = setup_demo_vault()
OUTPUT_DIR = "./sayou_archive/obsidian"
```

## Transfer a Vault

`source` format: `obsidian://{absolute_path_to_vault}`

`ObsidianGenerator` walks the vault recursively and yields one task per
`.md` file.  `ObsidianFetcher` reads the raw Markdown content.

Each note is written as a separate file in `destination`.

```python
stats = TransferPipeline.process(
    source=f"obsidian://{VAULT_PATH}",
    destination=OUTPUT_DIR,
    strategies={"connector": "obsidian"},
)

print("=== Transfer a Vault ===")
print(json.dumps(stats, indent=2))
```

## Transfer a Sub-directory

Point `source` at a sub-directory of the vault to collect only a subset
of notes — useful for large vaults with many templates or attachments.

```python
projects_path = os.path.join(VAULT_PATH, "projects")

stats_sub = TransferPipeline.process(
    source=f"obsidian://{projects_path}",
    destination=f"{OUTPUT_DIR}/projects",
    strategies={"connector": "obsidian"},
)

print("=== Transfer a Sub-directory ===")
print(json.dumps(stats_sub, indent=2))
```

## Validate Output

Each `.md` note produces one archive file preserving the raw Markdown.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} note(s) in '{OUTPUT_DIR}'.")
    if files:
        sample = os.path.join(OUTPUT_DIR, files[0])
        with open(sample, encoding="utf-8") as f:
            print(f.read(300))

import shutil

shutil.rmtree(VAULT_PATH, ignore_errors=True)
```