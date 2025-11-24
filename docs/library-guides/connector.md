# Library Guide: sayou-connector

`sayou-connector` serves as the **entry point** of the RAG pipeline. Its mission is to bring external data into the Sayou ecosystem, regardless of where it lives or how it is structured.

It acts as a **Recursive Harvesting Machine**, capable of discovering data dynamically rather than just reading a static list.

---

## 1. Core Concepts & Architecture

The library uses a **Generator-Fetcher Pattern** to handle complex collection logic.

### Tier 1: Interfaces
* **`BaseGenerator`**: The brain. It implements the `generate()` method (Iterator) to produce `FetchTask`s. It also receives `feedback()` from Fetchers to decide the next move (e.g., adding discovered URLs to the queue).
* **`BaseFetcher`**: The hands. It implements the `fetch()` method to execute a `FetchTask` and return a `FetchResult`.

### Tier 2: Templates (Strategies)
* **Generators:**
    * `PathWalkerGenerator`: Recursively scans local directories.
    * `WebCrawlGenerator`: Manages a URL queue and filters links via Regex.
    * `SqlGenerator`: Manages SQL `LIMIT` and `OFFSET` for pagination.
* **Fetchers:**
    * `FileFetcher`: Reads binary/text files.
    * `SimpleWebFetcher`: Uses `requests` and `BeautifulSoup` to scrape content.
    * `SqliteFetcher`: Executes queries against SQLite databases.

---

## 2. Usage Examples

### 2.1. Local File Scanning

Ideal for ingesting a folder of PDFs or Markdown files.

```python
pipeline.run(
    source="./documents",
    strategy="local_scan",
    recursive=True,
    extensions=[".pdf", ".docx"],
    name_pattern="*report*"
)
```

### 2.2. Database Ingestion (RDB)

Ideal for pulling structured data from legacy systems.

```python
pipeline.run(
    source="my_database.db", # Connection String
    strategy="sql_scan",
    query="SELECT * FROM users WHERE active=1",
    batch_size=1000
)
```

### 2.3. Smart Web Crawling

Crawls a website, following links that match specific patterns.

```python
pipeline.run(
    source="https://example.com/blog",
    strategy="web_crawl",
    link_pattern=r"/blog/post/\d+",
    selectors={"title": "h1", "body": "div.content"},
    max_depth=2
)
```

---

## 3. Logic Deep Dive: The Feedback Loop

The power of `sayou-connector` lies in its feedback loop.

1.  **Generate:** Generator creates a Task (e.g., Fetch `Page 1`).
2.  **Fetch:** Fetcher downloads `Page 1` and extracts links (`Page 2`, `Page 3`).
3.  **Feedback:** Fetcher passes these links back to the Generator via `result.data`.
4.  **Update:** Generator adds new links to its internal Queue.
5.  **Repeat:** The loop continues until the Queue is empty or `max_depth` is reached.

This allows the pipeline to handle dynamic data sources without hardcoding every single target.