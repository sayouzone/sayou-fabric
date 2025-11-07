# Sayou Core

**The foundational layer of the Sayou Data Platform — shared data model, lifecycle control, and exception handling.**

---

## 💡 Why Sayou Core?

`sayou_core` defines the *DataAtom* abstraction and *BaseComponent* interfaces used by every Sayou module.  
It ensures type consistency, lifecycle control, and standard error management across the entire framework.

- **Unified Data Model:** Every module speaks the same Atom language.  
- **Extensible Base Classes:** Build your own Sayou-compatible pipelines easily.  
- **Lightweight & Dependency-Free.**

---

## 🚀 Quick Start

```bash
pip install sayou-core
```

## 🏗️ Core Concepts

- DataAtom – The smallest data unit passed through all Sayou pipelines.
- BaseComponent – Shared init/run/teardown lifecycle for all processing classes.
- Exceptions – Unified error layer for all Sayou modules.

## 📜 License

Apache 2.0 License © 2025 Sayouzone