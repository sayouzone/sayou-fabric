import logging

from sayou.wrapper.pipeline import WrapperPipeline
from sayou.wrapper.plugins.embedding_adapter import EmbeddingAdapter

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_pure_logic_test():
    print(">>> 🧪 Sayou Wrapper: Logic & Stub Test (No API Required)")

    pipeline = WrapperPipeline(extra_adapters=[EmbeddingAdapter])
    pipeline.initialize()

    chunks_data = [
        {
            "content": "class TestClass:",
            "metadata": {"chunk_id": "c0", "semantic_type": "class_header"},
        },
        {
            "content": "    def test_method(self): pass",
            "metadata": {
                "chunk_id": "c1",
                "semantic_type": "method",
                "parent_id": "c0",
            },
        },
    ]

    try:
        print(f"Running pipeline with {len(chunks_data)} chunks...")

        output = pipeline.run(
            chunks_data, strategy="embedding", provider="stub", dimension=4
        )

        print("\n✅ Pipeline Logic Verified!")
        print(f"   - Total Nodes: {len(output.nodes)}")

        # 검증 로직
        for node in output.nodes:
            vec = node.attributes.get("vector")
            vec_dim = node.attributes.get("vector_dim")

            print(
                f"   🔹 ID: {node.node_id} | Type: {node.attributes.get('semantic_type')}"
            )

            if vec and isinstance(vec, list) and len(vec) == 4:
                print(f"      [OK] Vector Generated: {vec}")
            else:
                print(f"      [FAIL] Invalid Vector: {vec}")

    except Exception as e:
        print(f"\n❌ Pipeline Failed: {e}")

    # ----------------------------------------------------------------
    # Dependency Injection Simulation
    # ----------------------------------------------------------------
    print("\n>>> 💉 Dependency Injection Test (Custom Function)")

    def my_custom_embedder(texts):
        print(f"      [Custom] Embedding {len(texts)} texts...")
        return [[0.99] * 4 for _ in texts]

    try:
        output_custom = pipeline.run(
            chunks_data,
            strategy="embedding",
            embedding_fn=my_custom_embedder,
        )

        vec = output_custom.nodes[0].attributes["vector"]
        if vec[0] == 0.99:
            print("   ✅ Custom Injection Success!")
        else:
            print(f"   ❌ Injection Failed. Value: {vec[0]}")

    except Exception as e:
        print(f"   ❌ Injection Error: {e}")


if __name__ == "__main__":
    run_pure_logic_test()
