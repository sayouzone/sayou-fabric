---
name: Bug report
about: Create a report to help us improve
title: '[Component] Brief description of the bug'
labels: bug
assignees: ''
---

**Component**
Which library is causing the issue? (e.g., `sayou-connector`, `sayou-chunking`)

**Describe the bug**
A clear and concise description of what the bug is.

**Configuration / Strategy Used**
Please provide the strategy and config used. **If you used default settings, please state "Default".**

    # Paste your config/code snippet here
    pipeline.process(
        source="...",
        strategy="markdown", 
        config={"chunk_size": 500} 
    )

**To Reproduce**
Steps to reproduce the behavior:
1. Initialize pipeline...
2. Run method...
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Logs / Traceback**

    Paste error logs here...

**Environment:**
 - OS: [e.g. macOS]
 - Python Version: [e.g. 3.10]
 - Sayou Version: [e.g. 0.5.0]