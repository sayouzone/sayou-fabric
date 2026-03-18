import json
import os

from sayou.brain.pipelines.transfer import TransferPipeline


def run_github_demo():
    print(">>> 🐙 GitHub Connector Integration Test...")

    import os

    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")
    TARGET_REPO = "sayouzone/sayou-fabric"
    OUTPUT_DIR = "./sayou_archive/github"

    if "ghp_" not in GITHUB_TOKEN:
        print("🚨 Warning: Invalid GitHub token detected.")
        print("   Please set the GITHUB_TOKEN variable in the code.")
        return

    pipeline = TransferPipeline()

    # ---------------------------------------------------------
    # Mission 1: Source Code Collection (Code)
    # ---------------------------------------------------------
    print(f"\n[1] 📂 Fetching Code from '{TARGET_REPO}'...")

    stats_code = pipeline.process(
        source=f"github://{TARGET_REPO}",
        destination=f"{OUTPUT_DIR}/code",
        token=GITHUB_TOKEN,
        path="packages/sayou-connector",
        extensions=[".py", ".md"],
        target="code",
        limit=0,
    )
    print(f"   👉 Code files saved: {stats_code['written']} files")

    # ---------------------------------------------------------
    # Mission 2: Issue Collection (Issues)
    # ---------------------------------------------------------
    print(f"\n[2] 🐞 Fetching Issues from '{TARGET_REPO}'...")

    stats_issue = pipeline.process(
        source=f"github://{TARGET_REPO}",
        destination=f"{OUTPUT_DIR}/issues",
        token=GITHUB_TOKEN,
        target="issues",
        limit=3,
    )
    print(f"   👉 Issue files saved: {stats_issue['written']} files")

    # ---------------------------------------------------------
    # Result Confirmation
    # ---------------------------------------------------------
    print("\n✨ GitHub test completed. Check the saved files:")
    print(f"   📂 {OUTPUT_DIR}")


if __name__ == "__main__":
    run_github_demo()
