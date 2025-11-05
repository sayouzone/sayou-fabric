# sayou-connector

`sayou-connector` provides a standardized framework for **ingesting data** from external sources. It includes interfaces for "pulling" data (Fetching), "crawling" (Generating), and "seeding" (Seeding) data pipelines.

---

## 1. Concepts (Core Interfaces)

This library is built on three T1 Interfaces, managed by the `ConnectorPipeline`.

* **`BaseFetcher` (T1):** The primary interface for "pulling" data from a source (e.g., an API, a database table). This is the most common interface.
* **`BaseGenerator` (T1):** Defines a contract for "crawling" or "generating" new data requests from a seed input (e.g., scraping links from a base URL).
* **`BaseSeeder` (T1):** Defines a contract for providing initial "seed" data to a Generator (e.g., reading a list of URLs from a file).

---

## 2. T2 Usage (Default Components)

`sayou-connector` provides default T2 implementations for common tasks.

### Using `ApiFetcher` (T2)
(Placeholder for text explaining this is the default T2 for `BaseFetcher`. It handles standard HTTP GET/POST requests and is configured via the `ConnectorPipeline`'s `initialize()` method.)

### Using `DbFetcher` (T2)
(Placeholder for text explaining this T2 component (which likely wraps `sayou-extractor`'s `SqlQuerier`) provides a simple way to fetch data from standard SQL databases.)

### Using `HtmlLinkGenerator` (T2)
(Placeholder for text explaining this T2 component implements `BaseGenerator` to crawl a given URL and extract a list of new links to be fetched.)

---

## 3. T3 Plugin Development

A T3 plugin is used to connect to a non-standard source, like a proprietary API or a specific file storage system (e.g., S3).

### Tutorial: Building an `S3Fetcher` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `S3Fetcher` in the `plugins/` folder.
2.  **Inherit T1:** Make your class inherit from `BaseFetcher` (T1).
3.  **Implement `_do_fetch`:** Inside this method, write the logic to connect to the S3 bucket (using `boto3`) and download the requested file.
4.  **Use it:** Pass your `S3Fetcher` instance to the `fetchers=[]` list in the `ConnectorPipeline` constructor.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseFetcher` | `interfaces/base_fetcher.py` | Contract for "pulling" data from a source. |
| `BaseGenerator`| `interfaces/base_generator.py`| Contract for "crawling" or generating new requests. |
| `BaseSeeder` | `interfaces/base_seeder.py` | Contract for providing "seed" data to a Generator. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `ApiFetcher` | `fetcher/` | `BaseFetcher` |
| `DbFetcher` | `fetcher/` | `BaseFetcher` |
| `HtmlLinkGenerator` | `generator/` | `BaseGenerator` |
| `FileSeeder` | `seeder/` | `BaseSeeder` |

### Tier 3: Official Plugins

| Plugin | Directory | Implements/Wraps |
| :--- | :--- | :--- |
| `S3Fetcher` | `plugins/` | `BaseFetcher` (T1) |
| `SfFetcher` | `plugins/` | `BaseFetcher` (T1) |