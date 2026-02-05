# Contributing to Sayou Fabric

Thank you for your interest in contributing to Sayou Fabric! We use a **Monorepo** structure, meaning multiple libraries (`sayou-core`, `sayou-brain`, etc.) coexist in this single repository.

## 🚀 Quick Start (Development Setup)

Since this is a monorepo, you need to install the packages in **editable mode** to test your changes immediately.

### 1. Fork & Clone

    git clone https://github.com/YOUR_USERNAME/sayou-fabric.git
    cd sayou-fabric

### 2. Install in Editable Mode
We recommend installing `sayou-brain` (which pulls in most dependencies) or the specific library you are working on.

    # Install core dependencies in editable mode
    pip install -e ./sayou-core
    pip install -e ./sayou-brain
   
    # If working on a specific plugin (e.g., connector)
    pip install -e ./sayou-connector

### 3. Run Tests
You can run tests for the entire project or a specific module.

    # Run all tests
    pytest

    # Run tests for a specific module (Recommended)
    pytest tests/connector

## 📝 Pull Requests Protocol

1. **Focus**: Keep PRs focused on a single library if possible (e.g., "Add Notion Fetcher to sayou-connector").
2. **Naming**: Start commit messages with the component name.
    * Good: `[connector] Add Notion support`
    * Good: `[core] Fix retry decorator`
3. **Tests**: Ensure you added a unit test in `tests/{library_name}/`.

## 🎨 Style Guide
- We follow **PEP 8**.
- Please run **Black** and **Isort** before committing.