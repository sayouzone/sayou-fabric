# Contributing to Sayou Fabric

Thank you for your interest in contributing to Sayou Fabric! We welcome contributions from everyone.

## How to Contribute

### 1. Reporting Bugs
- Ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/sayouzone/sayou-fabric/issues).
- If you're unable to find an open issue addressing the problem, open a new one. Be sure to include a **title and clear description**, as well as as much relevant information as possible.

### 2. Pull Requests
Sayou Fabric is structured as a **Monorepo**.
- **Core Logic:** Modify `sayou-core` or `sayou-brain`.
- **New Plugin:** Add a new directory in `sayou-connector` or `sayou-loader`.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Issue that pull request!

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## Style Guide
- We follow **PEP 8**.
- Please use **Black** formatter before committing.