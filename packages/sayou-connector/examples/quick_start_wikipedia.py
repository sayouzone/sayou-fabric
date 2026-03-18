from sayou.brain.pipelines.transfer import TransferPipeline


def run_wikipedia_demo():
    print(">>> 🚀 Initializing Wikipedia Connector Test...")

    BASE_DIR = "./sayou_archive"

    pipeline = TransferPipeline()

    print("\n[3] 📚 Wikipedia ETL Start...")

    topic = "Python_(programming_language)"

    stats_wiki = pipeline.process(
        source=f"wiki://{topic}",
        destination=f"{BASE_DIR}/wikipedia",
        lang="en",
    )
    print(f"   👉 결과: {stats_wiki['written']}개 위키 문서 저장됨.")


if __name__ == "__main__":
    run_wikipedia_demo()
