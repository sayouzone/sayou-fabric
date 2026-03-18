from sayou.brain.pipelines.transfer import TransferPipeline


def run_trafilatura_demo():
    print(">>> 🚀 Initializing Trafilatura Connector Test...")

    BASE_DIR = "./sayou_archive"

    pipeline = TransferPipeline()

    print("\n[4] 🕸️ Trafilatura ETL Start...")

    target_url = "https://www.python.org/about/"

    stats_web = pipeline.process(
        source=f"trafilatura://{target_url}",
        destination=f"{BASE_DIR}/trafilatura",
    )
    print(f"   👉 Result: {stats_web['written']} webpages extracted.")


if __name__ == "__main__":
    run_trafilatura_demo()
