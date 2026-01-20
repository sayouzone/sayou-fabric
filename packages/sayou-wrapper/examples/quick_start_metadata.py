import logging

from sayou.wrapper.pipeline import WrapperPipeline
from sayou.wrapper.plugins.metadata_adapter import MetadataAdapter

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_enrichment_logic_test():
    print(">>> 🧪 Sayou Enrichment: Function Injection Test")

    pipeline = WrapperPipeline(extra_adapters=[MetadataAdapter])
    pipeline.initialize()

    chunks_data = [
        {
            "content": "Python is a high-level, general-purpose programming language.",
            "metadata": {"chunk_id": "c1", "source": "wiki"},
        },
        {
            "content": "Sayou Fabric is a data pipeline framework for LLMs.",
            "metadata": {"chunk_id": "c2", "source": "readme"},
        },
    ]

    def my_summarizer(text: str) -> str:
        return f"[Summary] This text is about: {text.split()[0]}"

    def my_keyword_extractor(text: str) -> list:
        words = text.replace(".", "").split()
        return [w for w in words if len(w) > 5]

    try:
        print(f"Running enrichment on {len(chunks_data)} chunks...")

        output = pipeline.run(
            chunks_data,
            strategy="metadata",
            metadata_map={"summary": my_summarizer, "keywords": my_keyword_extractor},
        )

        print("\n✅ Enrichment Completed!")
        print(output)

        for node in output.nodes:
            attrs = node.attributes
            print(f"🔹 ID: {node.node_id}")
            print(f"   Original: {attrs.get('schema:text')[:30]}...")
            print(f"   Summary : {attrs.get('summary')}")
            print(f"   Keywords: {attrs.get('keywords')}")
            print("-" * 40)

    except Exception as e:
        print(f"\n❌ Pipeline Failed: {e}")

    print("\n>>> 🧪 Stub Mode Test")
    output_stub = pipeline.run(chunks_data, strategy="metadata", use_stub=True)
    print(f"   Stub Summary: {output_stub.nodes[0].attributes.get('summary')}")


if __name__ == "__main__":
    run_enrichment_logic_test()
