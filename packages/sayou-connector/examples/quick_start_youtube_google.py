import json
import os

from sayou.brain.pipelines.transfer import TransferPipeline


def run_youtube_real_test():
    print(">>> 📺 Sayou YouTube Connector Real-World Test...")

    TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "YOUR_TOKEN_PATH")
    OUTPUT_DIR = "./youtube_archive"

    if not os.path.exists(TOKEN_PATH):
        print(
            f"🚨 Error: Token file not found ({TOKEN_PATH}). Run get_universal_token.py first."
        )
        return

    pipeline = TransferPipeline()

    try:
        stats = pipeline.process(
            source="youtube://me",
            destination=OUTPUT_DIR,
            token_path=TOKEN_PATH,
            target="liked",  # 'liked' or 'uploads'
            limit=5,
        )

        print("\n📊 [Execution Report]")
        print(json.dumps(stats, indent=2, ensure_ascii=False))

        if stats.get("written", 0) > 0:
            print(f"\n✅ Success! '{OUTPUT_DIR}' folder created.")
            print(f"👉 Check: ls -l {OUTPUT_DIR}")
        else:
            print("\n⚠️ No files saved.")
            print("1. 'liked' videos exist?")
            print("2. Token has 'YouTube Data API' permissions?")

    except Exception as e:
        print(f"\n❌ Test failed (Exception): {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_youtube_real_test()
