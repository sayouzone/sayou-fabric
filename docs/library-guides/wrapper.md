# sayou-wrapper

`sayou-wrapper` is the "entry point" to the `Sayou Data Platform` data flow. It **validates** raw data (like JSON) and **maps** it into the standardized `Atom` data structure (from `sayou-core`).

---

## 1. Concepts (Core Interfaces)

This library is built on two T1 Interfaces.

* **`BaseMapper` (T1):** The contract for **transforming raw data** (e.g., a complex dictionary) into a structured `Atom` payload.
* **`BaseValidator` (T1):** The contract for **validating** raw data against a set of rules *before* it gets mapped into an `Atom`.

---

## 2. T2 Usage (Default Components)

`sayou-wrapper` provides T2 mappers for common data formats.

### Using `JsonPathMapper` (T2)
(Placeholder for text explaining this is a powerful T2 mapper. It uses JSONPath expressions to pull data from deep within a nested JSON object and map it to specific fields in an `Atom` payload.)

### Using `DictMapper` (T2)
(Placeholder for text explaining this is a simple 1-to-1 mapper that maps top-level dictionary keys to `Atom` payload fields.)

### Using `DefaultValidator` (T2)
(Placeholder for text explaining this T2 validator checks for basic requirements, such as the presence of a unique ID field or non-null values.)

---

## 3. T3 Plugin Development

A T3 plugin is ideal for integrating a formal validation library like Pydantic.

### Tutorial: Building a `PydanticValidator` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `PydanticValidator`.
2.  **Inherit T1:** Make your class inherit from `BaseValidator` (T1).
3.  **Implement `_do_validate`:** Inside this method, take the raw data dictionary, pass it to a pre-defined Pydantic model, and catch any `ValidationError`.
4.  **Use it:** Pass your `PydanticValidator` instance to the `WrapperPipeline` (or `AssemblerPipeline`) to enforce strict schema validation.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseMapper` | `interfaces/base_mapper.py`| Contract for mapping raw data to an `Atom`. |
| `BaseValidator`| `interfaces/base_validator.py`| Contract for validating raw data. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `DictMapper` | `mapper/` | `BaseMapper` |
| `JsonPathMapper`| `mapper/` | `BaseMapper` |
| `DefaultValidator`| `validator/` | `BaseValidator` |