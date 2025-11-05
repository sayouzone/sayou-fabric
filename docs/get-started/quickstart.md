# Quickstart

This page provides a high-level, conceptual example of how `sayou-fabric` components are composed.

For a complete, runnable End-to-End example, please see the `/examples` folder in the main repository.

---

## Conceptual Example

```bash
from sayou.connector import ApiFetcher
from sayou.refinery import RefineryPipeline
from sayou.rag import RAGExecutor

fetcher = ApiFetcher(base_url="https://api.example.com")
data = fetcher.fetch({"endpoint": "/posts/latest"})
refined = RefineryPipeline().process(data)

executor = RAGExecutor()
result = executor.run("Summarize the latest updates", context=refined)

print(result)
```

## Next Steps

[→ **Learn about our Design Philosophy**](philosophy.md)