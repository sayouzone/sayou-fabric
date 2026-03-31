# Contributing to Sayou Fabric

Thank you for your interest in contributing to Sayou Fabric!
We use a **Monorepo** structure, meaning multiple libraries (`sayou-core`,
`sayou-brain`, etc.) coexist in this single repository.

---

## Table of Contents

1. [Quick Start (Development Setup)](#1-quick-start-development-setup)
2. [Running the Tests](#2-running-the-tests)
3. [Writing Example Files](#3-writing-example-files)
4. [Generating Documentation and Notebooks](#4-generating-documentation-and-notebooks)
5. [Style Guide](#5-style-guide)
6. [Pull Request Protocol](#6-pull-request-protocol)

---

## 1. Quick Start (Development Setup)

Since this is a monorepo, install the packages in **editable mode** so your
changes take effect immediately without reinstalling.

### Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/sayou-fabric.git
cd sayou-fabric
```

### Install in Editable Mode

We recommend installing `sayou-brain` (which pulls in most dependencies) or
the specific library you are working on.

```bash
# Install core dependencies in editable mode
pip install -e ./sayou-core
pip install -e ./sayou-brain

# If working on a specific library (e.g., connector)
pip install -e ./sayou-connector
```

---

## 2. Running the Tests

Tests use **pytest**. Each package has its own `tests/` directory with a
`pytest.ini` that configures markers and paths.

```bash
# Run all tests for a specific library
cd sayou-chunking
pytest tests/

# Unit tests only (fast, no I/O — recommended for local iteration)
pytest tests/ -m "not integration"

# Integration tests only (touches file system, real databases)
pytest tests/ -m integration

# Run all packages from the repo root
pytest sayou-*/tests/
```

### Test layout convention

```
sayou-{lib}/
└── tests/
    ├── conftest.py          ← shared fixtures (factories, tmp dirs, DB setup)
    ├── pytest.ini
    ├── unit/
    │   ├── test_pipeline.py
    │   └── {splitters,generators,fetchers}/
    │       └── test_*.py
    └── integration/
        └── test_*_integration.py
```

Rules:

- **Unit tests** must not touch the file system, network, or any real database.
  Use stubs and mocks.
- **Integration tests** must be decorated with `@pytest.mark.integration`.
  They may use temporary directories (via the `tmp_dir` fixture) and
  in-process SQLite.
- Test function names: `test_<what>_<condition>`.
  Use `class Test<Feature>:` grouping when a feature has many related checks.
- All test code must be in **English** (identifiers, docstrings, comments).
- When you fix a bug, add a test that would have caught it.

---

## 3. Writing Example Files

Example files are the primary learning resource for new users. They are also
the **single source of truth** for the official documentation: running
`scripts/gen_examples.py` converts them into Markdown pages and Jupyter
notebooks automatically.

### 3.1 File location and naming

Place example files under `sayou-{lib}/examples/` and use the prefix:

```
quick_start_{topic}.py
```

| File | Generated doc slug |
|------|--------------------|
| `quick_start_code.py` | `chunking_code.md` |
| `quick_start_json.py` | `chunking_json.md` |
| `quick_start_slack.py` | `connector_slack.md` |

The `quick_start_` prefix is **mandatory** — the scanner skips files without it.

### 3.2 Section structure

Each file is divided into **sections**. Every section becomes one `##` heading
in the documentation and one pair of cells (Markdown + code) in the notebook.

```python
# ── Section Title
"""
Optional Markdown description.
Explains what the code block demonstrates.
"""
# actual Python code starts here
result = pipeline.run(...)
print(result)
```

A section has three parts, in this exact order:

#### Section header (required)

```
# ── Section Title
```

- Start with `# ` (hash + single space).
- Follow with **two or more** `─` characters (**U+2500** BOX DRAWINGS LIGHT
  HORIZONTAL — see the tip below).
- Add a single space and the title text.
- The title must not be empty.

> **Tip — inserting U+2500**
> The character `─` is **not** a regular hyphen (`-`), en dash (`–`), or em
> dash (`—`). Copy it directly from here: `─`
>
> | Editor | Shortcut |
> |--------|----------|
> | VS Code | Install the *Sayou Snippets* extension (ships with this repo) |
> | Vim | Insert mode → `Ctrl-V u 2500` |
> | Any | Copy–paste the character above |
>
> If you use the wrong character, `gen_examples.py` will print a warning with
> the exact line number. The section will be skipped until it is corrected.

#### Description (optional)

A triple-quoted string immediately after the header, before any code:

```python
# ── Setup
"""
Initialize the `ChunkingPipeline` with `CodeSplitter`.

`CodeSplitter` routes each file to the appropriate language-specific
splitter based on the file extension — AST for Python, regex for others.
"""
```

Single-line form also works:

```python
# ── Setup
"""Initialize the pipeline."""
```

Omit the block entirely if you have nothing to add — do not leave `""" """`.

#### Code

Everything after the description block until the next `# ──` header is treated
as executable code.

### 3.3 Full example template

```python
# ── Setup
"""
Brief explanation of what is being initialised and why.
"""
from sayou.{lib}.pipeline import {Lib}Pipeline

pipeline = {Lib}Pipeline()
print("Pipeline initialised.")


# ── Basic Usage
"""
Show the simplest possible end-to-end call.
"""
result = pipeline.run({"content": "Hello world"})
print(result)


# ── Save Results
"""
Persist the output for downstream inspection.
"""
import json

with open("output.json", "w") as f:
    json.dump([r.model_dump() for r in result], f, indent=2)

print(f"Saved {len(result)} results.")
```

### 3.4 What to cover

A good `quick_start_*.py` answers three questions in order:

1. **Setup** — What do I install / import / initialise?
2. **Core scenario** — What does the happy path look like?
3. **Save / inspect output** — How do I persist or examine the results?

Additional sections for variations (different strategies, edge cases) are
welcome. Keep each section **self-contained**: a reader should be able to run
any single section after running Setup.

---

## 4. Generating Documentation and Notebooks

After writing or editing a `quick_start_*.py`, regenerate the derived files:

```bash
# From the repo root
python scripts/gen_examples.py
```

This writes:

- `docs/examples/src/{lib}_{topic}.md` — deployed to the documentation site.
- `sayou-{lib}/examples/{stem}.ipynb` — available via Binder / Colab badges.

**Commit both** the `.py` and its generated `.md` and `.ipynb` in the same PR.

### Preview without writing

```bash
python scripts/gen_examples.py --dry-run
```

### CI check

The CI pipeline runs:

```bash
python scripts/gen_examples.py --check
```

This exits with code 1 if any generated file is missing or out of date.
If CI fails because of this, run `gen_examples.py` locally, commit the
outputs, and push again.

---

## 5. Style Guide

- **Formatter**: [Black](https://black.readthedocs.io/) (line length 88).
- **Import sorter**: [isort](https://pycqa.github.io/isort/).
- **Standard**: PEP 8.
- **Python version**: minimum 3.9. Do not use `X | Y` union syntax or
  built-in generic aliases (`list[str]`, `dict[str, int]`) without
  `from __future__ import annotations`.
- **Type hints**: required on all public functions and methods.
- **Docstrings**: Google style, English only.
- **Log messages**: plain ASCII — no emoji in `self._log()` calls.
- **Comments and identifiers**: English only.

Run before committing:

```bash
black .
isort .
```

---

## 6. Pull Request Protocol

1. **Focus** — Keep PRs focused on a single library if possible.
2. **Naming** — Start commit messages with the component name in brackets:
   - `[connector] Add Notion fetcher`
   - `[core] Fix retry decorator`
   - `[chunking] Add SemanticSplitter`
   - `[examples] Add quick_start_json for chunking`
3. **Tests** — Add or update tests in `sayou-{lib}/tests/`.
4. **Examples** — If you added a feature, consider adding an example section
   to `sayou-{lib}/examples/quick_start_*.py` and regenerating the docs.
5. **Generated files** — Commit `.md` and `.ipynb` outputs alongside the
   source `.py` if you touched any example file.