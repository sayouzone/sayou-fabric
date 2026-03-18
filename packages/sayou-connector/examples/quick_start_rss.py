from sayou.brain.pipelines.transfer import TransferPipeline


def run_rss_demo():
    print(">>> 📰 RSS Connector Integration Test...")

    BASE_DIR = "./sayou_archive"

    pipeline = TransferPipeline()

    print("\n[2] 📰 RSS ETL Start...")
    rss_url = "https://github.blog/category/engineering/feed/"

    stats_rss = pipeline.process(
        source=f"rss://{rss_url}",
        destination=f"{BASE_DIR}/rss",
        limit=5,
    )
    print(f"   👉 Result: {stats_rss['written']} news items saved.")


if __name__ == "__main__":
    run_rss_demo()
