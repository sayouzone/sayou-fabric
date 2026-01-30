import json

from sayou.brain.pipelines.transfer import TransferPipeline


def run_notion_etl():
    NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "YOUR_NOTION_TOKEN")

    # Mode A: Search (all connected pages)
    SOURCE = "notion://search"
    # Mode B: Specific page (ID)
    # SOURCE = "notion://page/..."
    OUTPUT_DIR = "./notion_archive"

    pipeline = TransferPipeline()

    print(f"🚀 Starting Notion Extraction...")
    stats = pipeline.process(
        source=SOURCE,
        destination=OUTPUT_DIR,
        strategies={"connector": "notion"},
        notion_token=NOTION_TOKEN,
    )

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    run_notion_etl()
