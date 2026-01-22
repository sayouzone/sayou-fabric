import json
import os
from typing import List

from dotenv import load_dotenv
from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock
from sayou.refinery.interfaces.base_processor import BaseProcessor

from sayou.brain.pipelines.transfer import TransferPipeline


@register_component("processor")
class NewsletterFilter(BaseProcessor):
    """
    [Refinery] Filters SayouBlocks based on keywords.
    """

    component_name = "NewsletterFilter"

    @classmethod
    def can_handle(cls, blocks: List[SayouBlock]) -> float:
        print(f"   [DEBUG] Filter.can_handle called with {len(blocks)} blocks")
        score = 1.0 if super().can_handle(blocks) > 0 else 0.0
        print(f"   [DEBUG] Filter Score: {score}")
        return score

    def initialize(self, filter_keywords: List[str] = None, **kwargs):
        self.keywords = [k.lower() for k in (filter_keywords or [])]

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        print(f"   [DEBUG] Filter._do_process STARTED with {len(blocks)} blocks")
        if not hasattr(self, "keywords") or not self.keywords:
            return blocks

        filtered_blocks = []
        for block in blocks:
            subject = self._get_subject(block)
            print(f"   [DEBUG] Filter._do_process subject: {subject}")
            if any(k in subject for k in self.keywords):
                filtered_blocks.append(block)
        print(f"   [DEBUG] Filter._do_process ENDED. Remaining: {len(filtered_blocks)}")
        return filtered_blocks

    def _get_subject(self, block: SayouBlock) -> str:
        if block.type == "record" and isinstance(block.content, dict):
            meta = block.content.get("meta", {})
            return meta.get("subject", "").lower()

        meta = block.metadata or {}
        return meta.get("subject", "").lower()


@register_component("processor")
class SummaryMapper(BaseProcessor):
    """
    [Refinery] Transforms SayouBlock into a summary structure.
    """

    component_name = "SummaryMapper"

    @classmethod
    def can_handle(cls, blocks: List[SayouBlock]) -> float:
        print(f"   [DEBUG] Mapper.can_handle called with {len(blocks)} blocks")
        score = 1.0 if super().can_handle(blocks) > 0 else 0.0
        print(f"   [DEBUG] Mapper Score: {score}")
        return score

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        print(f"   [DEBUG] Mapper._do_process STARTED")
        mapped_blocks = []

        for block in blocks:
            data = self._unpack_data(block)
            original_content = data["content"]
            meta = data["meta"]

            summary_data = {
                "title": meta.get("subject", "No Title"),
                "date": meta.get("date"),
                "from": meta.get("sender"),
                "preview": (
                    (str(original_content)[:200].strip() + "...")
                    if original_content
                    else ""
                ),
                "link": f"https://mail.google.com/mail/u/0/#inbox/{meta.get('uid', '')}",
            }

            original_id = getattr(block, "id", "unknown_id")

            new_block = SayouBlock(
                type="record",
                content=summary_data,
                metadata={
                    "original_id": original_id,
                    "processed_by": "SummaryMapper",
                },
            )

            mapped_blocks.append(new_block)

        return mapped_blocks

    def _unpack_data(self, block: SayouBlock) -> dict:
        if block.type == "record" and isinstance(block.content, dict):
            return {
                "content": block.content.get("content", ""),
                "meta": block.content.get("meta", {}),
            }
        return {"content": block.content, "meta": block.metadata or {}}


def run_email_etl_demo():
    # ---------------------------------------------------------
    # 1. Configuration
    # ---------------------------------------------------------
    # Google Account Management > Security > 2-Step Verification > App Passwords.

    load_dotenv()

    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_PASS = os.getenv("GMAIL_PASS")
    OUTPUT_FILE = "./examples/email_archive"
    TARGET_KEYWORDS = ["Medium", "AI", "Data", "Welcome"]

    print(f"🚀 Starting ETL Job: Gmail ({GMAIL_USER}) -> {OUTPUT_FILE}")
    print(f"🚀 Newsletter ETL for keywords: {TARGET_KEYWORDS}")

    # ---------------------------------------------------------
    # 2. Execution Pipeline
    # ---------------------------------------------------------
    pipeline = TransferPipeline(extra_processors=[NewsletterFilter, SummaryMapper])

    result_stats = pipeline.process(
        source="imap://",
        imap_server="imap.gmail.com",
        destination=OUTPUT_FILE,
        username=GMAIL_USER,
        password=GMAIL_PASS,
        limit=5,
        # search_criteria="ALL",
        processors=["NewsletterFilter", "SummaryMapper"],
        filter_keywords=TARGET_KEYWORDS,
        use_refinery=True,
    )

    print("\n=== ETL Execution Stats ===")
    print(json.dumps(result_stats, indent=2))

    # ---------------------------------------------------------
    # 3. Validation
    # ---------------------------------------------------------
    if os.path.exists(OUTPUT_FILE):
        print(f"\n✅ Validated Output: {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        record_count = len(data)
        print(f"   - Total Records Archived: {record_count}")

        print("\n   - Sample Record Preview:")
        for idx, record in enumerate(data[:2]):
            if isinstance(record, dict):
                meta = record.get("meta", {})
                subject = meta.get("subject", "No Subject")
                sender = meta.get("sender", "Unknown")
                print(f"     [{idx+1}] 📧 {subject} (from: {sender})")
            else:
                print(f"     [{idx+1}] 📝 (Raw Text) {str(record)[:50]}...")

    else:
        print(f"\n❌ Output file not found: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_email_etl_demo()
