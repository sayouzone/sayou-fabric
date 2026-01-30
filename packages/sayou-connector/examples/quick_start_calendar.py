import json
import os

from sayou.brain.pipelines.transfer import TransferPipeline


def run_calendar_etl():
    TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", "YOUR_TOKEN_PATH")
    OUTPUT_DIR = "./calendar_archive"

    stats = TransferPipeline().process(
        source="gcal://primary",
        destination=OUTPUT_DIR,
        strategies={"connector": "google_calendar"},
        google_token_path=TOKEN_PATH,
    )

    print("\n📊 Execution Result:")
    print(json.dumps(stats, indent=2))

    if stats["written"] > 0:
        print(f"\n✅ Success! Check '{OUTPUT_DIR}' folder.")

        import glob

        files = glob.glob(os.path.join(OUTPUT_DIR, "*.json"))
        if files:
            latest = max(files, key=os.path.getctime)
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and isinstance(data, list):
                    cnt = len(data[0].get("content", []))
                    print(f"📅 Collected Event Count: {cnt}개")
    else:
        print("\n❌ No data collected. Check token permissions and date range.")


if __name__ == "__main__":
    run_calendar_etl()
