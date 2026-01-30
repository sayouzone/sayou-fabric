import json
import os

from sayou.brain.pipelines.transfer import TransferPipeline


def run_youtube_etl_demo():
    TARGET_SOURCE = "youtube://rxYhBE91SCk"
    OUTPUT_DIR = "./youtube_archive"

    print(f"🚀 Starting YouTube Extraction for: {TARGET_SOURCE}")

    pipeline = TransferPipeline()

    stats = pipeline.process(
        source=TARGET_SOURCE,
        destination=OUTPUT_DIR,
        strategies={"connector": "youtube"},
        # Connector Config
        # languages=['ko', 'en']
        use_refinery=True,
    )

    print("\n=== Extraction Stats ===")
    print(json.dumps(stats, indent=2))

    expected_filename = "youtube_rxYhBE91SCk.json"
    output_path = os.path.join(OUTPUT_DIR, expected_filename)

    if os.path.exists(output_path):
        print(f"\n✅ Validated Output: {output_path}")

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Confirm Data Structure (SayouBlock List or Raw Dict depends on Pipeline logic)
        if isinstance(data, list) and len(data) > 0:
            record = data[0]
            meta = record.get("meta", {})

            print(f"\n📺 Title: {meta.get('title')}")
            print(f"🔗 URL: {meta.get('url')}")
            print(f"👀 Views: {meta.get('view_count')}")

            transcript = record.get("content", [])
            print(f"\n📝 Transcript Preview ({len(transcript)} lines):")
            for line in transcript[:5]:
                print(f"   [{line['start']:.1f}s] {line['text']}")
    else:
        print(f"\n❌ Output file not found. Check the directory: {OUTPUT_DIR}")
        if os.path.exists(OUTPUT_DIR):
            print(f"   Files found: {os.listdir(OUTPUT_DIR)}")


if __name__ == "__main__":
    run_youtube_etl_demo()
