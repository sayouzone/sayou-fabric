import json
import logging

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.json_splitter import JsonSplitter

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_json_demo():
    print(">>> Initializing Sayou JSON Chunking Pipeline...")

    pipeline = ChunkingPipeline(extra_splitters=[JsonSplitter])

    # ---------------------------------------------------------
    # Scenario 1: List of Records (YouTube Subtitle Style)
    # ---------------------------------------------------------
    print("\n=== [1] YouTube Subtitle Batching ===")

    youtube_records = [
        {"text": "안녕하세요.", "start": 0.0, "duration": 1.5},
        {"text": "Sayou Fabric 데모입니다.", "start": 1.8, "duration": 2.5},
        {"text": "이것은 JSON 청킹 테스트입니다.", "start": 4.5, "duration": 3.0},
        {"text": "문장이 짧아도...", "start": 7.8, "duration": 1.2},
        {"text": "설정된 크기만큼 묶입니다.", "start": 9.2, "duration": 2.0},
        {"text": "다음 챕터로 넘어갑니다.", "start": 12.5, "duration": 2.0},
        {"text": "여기서부터는 새로운 청크가 되겠죠.", "start": 15.0, "duration": 3.5},
    ]

    request_youtube = {
        "type": "record",  # SayouBlock type
        "content": youtube_records,
        "metadata": {
            "source": "video_transcript.json",
            "video_id": "v12345",
        },
        "config": {
            "chunk_size": 100,
            "min_chunk_size": 10,
        },
    }

    chunks_list = pipeline.run(request_youtube, strategy="record")

    for i, chunk in enumerate(chunks_list):
        meta = chunk.metadata
        time_info = f"Time: {meta.get('sayou:startTime')} ~ {meta.get('sayou:endTime')}"
        count_info = f"Items: {meta.get('item_count')}"

        print(f"[{i}] {time_info} | {count_info}")
        print("-" * 40)
        print(chunk.content.strip())
        print("-" * 40)

    # ---------------------------------------------------------
    # Scenario 2: Nested Dictionary (Complex JSON)
    # ---------------------------------------------------------
    print("\n=== [2] Complex Nested JSON Splitting ===")

    complex_data = {
        "meta": {"api_version": "v1", "environment": "production"},
        "data": {
            "users": [
                {"id": k, "name": f"User_{k}", "log": "Action data..." * 5}
                for k in range(1, 6)
            ],
            "settings": {"theme": "dark", "notifications": True},
        },
    }

    request_dict = {
        "type": "json",
        "content": complex_data,
        "metadata": {
            "source": "api_response.json",
        },
        "config": {
            "chunk_size": 200,
        },
    }

    chunks_dict = pipeline.run(request_dict, strategy="json")

    for i, chunk in enumerate(chunks_dict):
        meta = chunk.metadata
        path_info = f"Path: {meta.get('json_path', 'root')}"
        type_info = f"Type: {meta.get('chunk_type')}"

        print(f"[{i}] {type_info} | {path_info}")
        print(f"    Content Preview: {chunk.content[:60].replace(chr(10), ' ')}...")

    # ---------------------------------------------------------
    # [Save Result]
    # ---------------------------------------------------------
    output_data = [c.model_dump() for c in chunks_list + chunks_dict]

    with open("json_chunk_result_demo.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(output_data)} chunks to json_chunk_result_demo.json")


if __name__ == "__main__":
    run_json_demo()
