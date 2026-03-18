# Contributing

Thank you for your interest in contributing to Sayou Fabric! We use a **Monorepo** structure, meaning multiple libraries (`sayou-core`, `sayou-brain`, etc.) coexist in this single repository.

---

## Quick Start

Since this is a monorepo, install packages in **editable mode** to test changes immediately.

**1. Fork & Clone**

```bash
git clone https://github.com/YOUR_USERNAME/sayou-fabric.git
cd sayou-fabric
```

**2. Install in Editable Mode**

```bash
# Install core dependencies in editable mode
pip install -e ./packages/sayou-core
pip install -e ./packages/sayou-brain

# If working on a specific plugin (e.g., connector)
pip install -e ./packages/sayou-connector
```

**3. Run Tests**

```bash
# Run all tests
pytest

# Run tests for a specific module
pytest tests/connector
```

---

## Pull Request Protocol

1. **Focus** — Keep PRs focused on a single library if possible (e.g., "Add Notion Fetcher to sayou-connector").
2. **Naming** — Start commit messages with the component name.
    - `[connector] Add Notion support`
    - `[core] Fix retry decorator`
3. **Tests** — Add a unit test in `tests/{library_name}/`.

---

## Style Guide

- Follow **PEP 8**.
- Run **Black** and **Isort** before committing.

---

## Templates

=== "Bug Report"

    **Component**

    Which library is causing the issue? (e.g., `sayou-connector`, `sayou-chunking`)

    **Describe the bug**

    A clear and concise description of what the bug is.

    **Configuration / Strategy Used**

    ```python
    pipeline.process(
        source="...",
        strategy="markdown",
        config={"chunk_size": 500}
    )
    ```

    **To Reproduce**

    1. Initialize pipeline...
    2. Run method...
    3. See error

    **Expected behavior**

    A clear and concise description of what you expected to happen.

    **Logs / Traceback**

    ```markdown
    Paste error logs here...
    ```

    **Environment**

    - OS: (e.g., macOS)
    - Python Version: (e.g., 3.11)
    - Sayou Version: (e.g., 0.4.0)

    ---
    [Open a Bug Report →](https://github.com/sayouzone/sayou-fabric/issues/new?template=bug_report.md){ .md-button }

=== "Feature Request"

    **Is your feature request related to a problem?**

    A clear and concise description of the problem. (e.g., "I'm always frustrated when...")

    **Describe the solution you'd like**

    A clear and concise description of what you want to happen.

    **Describe alternatives you've considered**

    Any alternative solutions or features you've considered.

    **Additional context**

    Any other context or screenshots about the feature request.

    ---
    [Open a Feature Request →](https://github.com/sayouzone/sayou-fabric/issues/new?template=feature_request.md){ .md-button }

=== "Pull Request"

    **Description**
    
    A summary of the change and which issue is fixed.

    **Fixes # (issue number)**

    **Affected Components**

    ```markdown
    - [ ] `sayou-core`
    - [ ] `sayou-brain`
    - [ ] `sayou-connector`
    - [ ] `sayou-document`
    - [ ] `sayou-refinery`
    - [ ] `sayou-chunking`
    - [ ] `sayou-wrapper`
    - [ ] `sayou-assembler`
    - [ ] `sayou-loader`
    - [ ] `sayou-extractor`
    - [ ] `sayou-llm`
    - [ ] `sayou-visualizer`
    ```

    **Type of change**

    ```markdown
    - [ ] Bug fix
    - [ ] New feature
    - [ ] Breaking change
    - [ ] Documentation update
    ```

    **Checklist**

    ```markdown
    - [ ] Code follows the style guidelines
    - [ ] Self-review completed
    - [ ] Hard-to-understand areas are commented
    - [ ] Tests added
    - [ ] All tests pass locally
    ```

---

## Code of Conduct

Sayou Fabric follows the [Contributor Covenant v2.0](https://www.contributor-covenant.org/version/2/0/code_of_conduct.html).

The full text is available at [`CODE_OF_CONDUCT.md`](https://github.com/sayouzone/sayou-fabric/blob/main/CODE_OF_CONDUCT.md).