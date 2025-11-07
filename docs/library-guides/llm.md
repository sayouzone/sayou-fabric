# sayou-llm

`sayou-llm` is the universal **LLM Adapter** for the Sayou Data Platform. It provides a single, standardized interface (`BaseLLMClient`) to interact with *any* LLM, whether it's a remote API (like OpenAI) or a local model (like GGUF or Transformers).

---

## 1. Concepts (Core Interfaces)

### `BaseLLMClient` (T1)

This is the **single "socket"** for all LLMs. It defines the standard `invoke()` and `stream()` methods that the entire `sayou-rag` library relies on. By conforming to this T1 interface, any LLM can be "plugged into" the RAG system.

---

## 2. T2 Usage (Default Adapters)

T2 components are the "official" adapters for popular LLM providers and local formats, found in the `llm_client/` directory.

### Using `OpenAIClient` (T2 - Remote API)
(Placeholder for text explaining this T2 component connects to the OpenAI API (or Azure). It requires an `OPENAI_API_KEY`.)

### Using `LlamaCppClient` (T2 - Local Load)
(Placeholder for text explaining this T2 component loads `GGUF` formatted models directly into memory using `llama-cpp-python`. It requires the `sayou-llm[gguf]` extra.)

### Using `TransformersClient` (T2 - Local Load)
(Placeholder for text explaining this T2 component loads original Hugging Face `safetensors` models (like Gemma, Llama 3) directly into memory using the `transformers` library. It requires the `sayou-llm[transformers]` extra.)

---

## 3. T3 Plugin Development

A T3 plugin can either **wrap** a T2 adapter to add functionality (like logging) or be a **custom** adapter for a non-supported model.

### Tutorial: Building a `LoggingLLMClient` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `LoggingLLMClient`.
2.  **Inherit T2:** Make your class inherit from `OpenAIClient` (T2).
3.  **Override `invoke`:** Override the `invoke` method. Add your logging logic (e.g., start timer), then call `super().invoke()` to run the original T2 logic, and finally log the duration.
4.  **Use it:** Pass your `LoggingLLMClient` instance (instead of the `OpenAIClient`) to the `sayou-rag` generator.

### Tutorial: Building an `HFNativeClient` (T3)
(Placeholder for text explaining this (from `plugins/hf_native_client.py`) is an advanced T3 plugin that inherits T1 directly to provide fine-grained control over HF model generation, including custom chat templates.)

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseLLMClient`| `interfaces/base_llm_client.py`| The single contract for all LLM interactions. |

### Tier 2: Default Components

| Component | Directory | Description |
| :--- | :--- | :--- |
| `OpenAIClient` | `llm_client/` | Connects to OpenAI/Azure API. |
| `AnthropicClient`| `llm_client/` | Connects to Anthropic Claude API. |
| `GeminiClient` | `llm_client/` | Connects to Google Gemini API. |
| `OllamaClient` | `llm_client/` | Connects to a local Ollama server API. |
| `LlamaCppClient` | `llm_client/` | Loads GGUF models directly. |
| `TransformersClient`| `llm_client/` | Loads HF `safetensors` models directly. |

### Tier 3: Official Plugins

| Plugin | Directory | Implements/Wraps |
| :--- | :--- | :--- |
| `HFNativeClient` | `plugins/` | `BaseLLMClient` (T1) |
| `LoggingLLMClient`| `plugins/` | `OpenAIClient` (T2) |