!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_wikipedia.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_wikipedia.py).

## Setup

Fetch Wikipedia articles and archive them as plain-text files using
`TransferPipeline`.

`WikipediaGenerator` resolves an article title and yields a single task.
`WikipediaFetcher` retrieves the full article text via the `wikipedia-api`
library.  Any language edition is supported through the `lang` keyword.

Install the dependency before running with real articles:

```bash
pip install wikipedia-api
python quick_start_wikipedia.py
```

The example below mocks the library for offline testing.
Remove `setup_mock()` and substitute a real `wiki://` title to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/wikipedia"
```

## Mock Setup

`WikipediaGenerator` and `WikipediaFetcher` both call
`wikipediaapi.Wikipedia(language=…).page(title)`.  The mock returns a page
object with `.exists()`, `.title`, and `.text` so the full pipeline path
is exercised.

To switch to live mode: delete this function and its call below.

```python
def setup_mock(title: str = "Artificial intelligence"):
    mock_page = MagicMock()
    mock_page.exists.return_value = True
    mock_page.title = title
    mock_page.fullurl = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    mock_page.summary = "AI is intelligence demonstrated by machines."
    mock_page.text = (
        f"{title}\n\n"
        "Artificial intelligence (AI) is intelligence demonstrated by machines, "
        "as opposed to the natural intelligence displayed by animals including humans.\n\n"
        "AI research has been defined as the field of study of intelligent agents, "
        "which refers to any system that perceives its environment and takes actions "
        "that maximize its chance of achieving its goals.\n"
    )

    mock_wiki_instance = MagicMock()
    mock_wiki_instance.page.return_value = mock_page

    mock_wapi = MagicMock()
    mock_wapi.Wikipedia.return_value = mock_wiki_instance
    sys.modules["wikipediaapi"] = mock_wapi
```

## Fetch a Single Article

Use the `wiki://` prefix followed by the article title (spaces are allowed).
The `lang` keyword selects the language edition — default is `"ko"` (Korean).
Set `lang="en"` for English, `"ja"` for Japanese, and so on.

`packet.data` is the full plain-text content of the article.

```python
setup_mock("Artificial intelligence")

stats = TransferPipeline.process(
    source="wiki://Artificial intelligence",
    destination=OUTPUT_DIR,
    strategies={"connector": "wikipedia"},
    lang="en",
)

print("=== Fetch a Single Article ===")
print(json.dumps(stats, indent=2))
```

## Fetch Multiple Articles

Run the pipeline once per topic.  Each article is written to a separate
file whose name is derived from the article title.

```python
topics = [
    "wiki://Machine learning",
    "wiki://Natural language processing",
    "wiki://Knowledge graph",
]

total = {"read": 0, "written": 0, "failed": 0}
for topic in topics:
    title = topic.replace("wiki://", "")
    setup_mock(title)  # re-mock with the correct title each time
    s = TransferPipeline.process(
        source=topic,
        destination=f"{OUTPUT_DIR}/batch",
        strategies={"connector": "wikipedia"},
        lang="en",
    )
    for k in total:
        total[k] += s.get(k, 0)

print("=== Fetch Multiple Articles ===")
print(json.dumps(total, indent=2))
```

## Validate Output

Inspect the archived article to confirm it was written correctly.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} article(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(300))
```