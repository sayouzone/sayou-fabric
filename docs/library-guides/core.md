# sayou-core

`sayou-core` provides the foundational abstract classes and shared utilities used across the entire Sayou Data Platform.

---

## 1. Concepts

`sayou-core` is the blueprint that ensures all Platform components operate consistently. It enforces a common component lifecycle, standardized logging, and a unified data structure.

* **`BaseComponent`**: The abstract class that all Tier 1, 2, and 3 components must inherit from. It provides the `.initialize()` lifecycle hook, a standardized `._log()` interface, and a `component_name` attribute.

* **`Atom`**: The standard, immutable data structure (wrapper) passed between data processing modules (e.g., from `Wrapper` to `Refinery` to `Assembler`).

---

## 2. Usage (Building Modules)

You do not use `sayou-core` directly. You use it as the foundation for building components in other libraries.

All `sayou` components, whether T1, T2, or T3, must inherit from `BaseComponent` to integrate with the ecosystem's lifecycle and logging.

(Placeholder for a code example showing a T2 class inheriting from `BaseComponent` and using `self._log()` in its `initialize()` method.)

---

## 3. Extension Guidelines

-   Always inherit from `BaseComponent` for lifecycle consistency.
-   Configuration should be passed via `initialize(**kwargs)`.
-   Avoid global state; manage state within the component instance.

---

## 4. API Reference

### Key Components

| Class | Description |
| :--- | :--- |
| `BaseComponent` | Base class for all modules; provides logging and lifecycle. |
| `Atom` | Immutable data wrapper for inter-module data transfer. |
| `BaseConfig` | (TBD) Configuration class for validation and environment binding. |