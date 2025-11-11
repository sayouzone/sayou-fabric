# Installation

Getting started with Sayou is straightforward. The `sayou-rag` package is the main "umbrella package" that includes all the core components you need to build your first pipeline.

---

### Install with pip
We recommend installing `sayou-rag` in a virtual environment.

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the main package
pip install sayou-rag
```

This single command installs `sayou-rag` and all its core library dependencies, such as:
* `sayou-core`
* `sayou-connector`
* `sayou-wrapper`
* `sayou-assembler`
* `sayou-extractor`
* `sayou-llm`

### Requirements
* Python 3.9 or higher.