import json

from sayou.brain.pipelines.transfer import TransferPipeline


def run_gmail_etl():
    import os

    TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", "YOUR_TOKEN_PATH")
    OUTPUT_DIR = "./gmail_archive"

    stats = TransferPipeline().process(
        source="gmail://me",
        destination=OUTPUT_DIR,
        strategies={"connector": "gmail"},
        token_path=TOKEN_PATH,
    )

    print("\n📊 Execution Result:")
    print(json.dumps(stats, indent=2))

    if stats["written"] > 0:
        print(f"\n✅ Success! Check '{OUTPUT_DIR}' folder.")

    else:
        print("\n❌ No data collected. Check token permissions and date range.")


if __name__ == "__main__":
    run_gmail_etl()
