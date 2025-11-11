# Architecture

You don't need to understand the architecture to use `BasicRAG`, but it helps to know what's happening under the hood.

The Sayou framework is a composable set of libraries, or "Lego bricks." The `BasicRAG` facade simply assembles these bricks for you in a pre-defined order.

This is the pipeline `BasicRAG` builds for you:

### The `BasicRAG` Pipeline

**1. Connector (`sayou-connector`)**

* **Job:** Fetches raw data.

* **In `BasicRAG`:** `BasicRAG` uses the `ApiFetcher` component. When you pass `data_source=(URL, QUERY)` to `pipeline.run()`, this component executes the API call and returns the raw JSON string.


**2. Wrapper (`sayou-wrapper`)**

* **Job:** Parses and structures the raw data.

* **In `BasicRAG`:** This is the most complex stage, which `BasicRAG` fully automates.
    1.  It receives the single JSON string from the Connector.
    2.  It parses the *outer* JSON (`{"header": ..., "body": ...}`).
    3.  It extracts the `body.paths` field.
    4.  It handles multi-encoded JSON (e.g., if `paths` is a string `"[...]"`) by parsing it again until it gets a true list.
    5.  It passes this list (`[{...}, {...}]`) to the `BaseMapper`'s `map_list` function.
    6.  The `BaseMapper` uses your `map_logic` function (via the internal `LambdaMapper`) to transform each item (`{...}`) into a validated `DataAtom`.


**3. Refinery (`sayou-refinery`)**

* **Job:** Cleans the `DataAtoms`.

* **In `BasicRAG`:** By default, `BasicRAG` loads a `DefaultTextCleaner` to remove HTML tags (like `<b>`) from the `friendly_name` field.


**4. Assembler (`sayou-assembler`)**

* **Job:** Builds the Knowledge Graph (KG) from the `DataAtoms`.

* **In `BasicRAG`:**
    1.  The `SchemaValidator` (auto-loaded) checks if each Atom has an `entity_class` (which you provided in `map_logic`).
    2.  The `DefaultKGBuilder` constructs the graph.
    3.  The `FileStorer` saves the final `final_kg.json` to disk.

**5. RAG Stage (`sayou-rag` + `llm` + `extractor`)**

* **Job:** Uses the KG to answer the query.

* **In `BasicRAG`:**
    1.  The `FileRetriever` (from `sayou-extractor`) reads the `final_kg.json`.
    2.  The `SimpleKGContextFetcher` formats the KG data into a clean text `context`.
    3.  The `LLMPipeline` (from `sayou-llm`) injects this `context` into a prompt for your local LLM.
    4.  The final `answer` is returned.

When you're ready, you can "graduate" from `BasicRAG` and assemble these components yourself. This is covered in the **Library Guides** and **Sayou Agent** sections.