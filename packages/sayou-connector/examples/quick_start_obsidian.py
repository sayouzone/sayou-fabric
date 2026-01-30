import os
import shutil

from sayou.brain.pipelines.transfer import TransferPipeline


def setup_dummy_vault(path):
    """Obsidian test to create fake data"""
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    with open(os.path.join(path, "TestNote.md"), "w", encoding="utf-8") as f:
        f.write("# Hello Obsidian\nThis is a test note for Sayou Connector.")

    print(f"🛠️ [Setup] Created dummy vault at: {path}")


print(">>> 🚀 Initializing Obsidian Test...")

BASE_DIR = "./sayou_archive"
VAULT_DIR = "./test_vault"

setup_dummy_vault(VAULT_DIR)

pipeline = TransferPipeline()

print("\n[1] 💎 Obsidian ETL Start...")
abs_vault_path = os.path.abspath(VAULT_DIR)

stats_obsidian = pipeline.process(
    source=f"obsidian://{abs_vault_path}", destination=f"{BASE_DIR}/obsidian"
)
print(f"   👉 Result: {stats_obsidian['written']} files processed.")
