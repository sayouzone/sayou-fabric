import json
import os
import shutil
import tempfile
import unittest

from sayou.chunking.plugins.markdown_splitter import MarkdownSplitter

from sayou.brain.pipelines.standard import StandardPipeline


class TestStandardPipeline(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_file = os.path.join(self.test_dir, "output.json")
        os.makedirs(self.input_dir)

        self.brain = StandardPipeline(extra_splitters=[MarkdownSplitter()])
        self.brain.initialize(config={"chunking": {"chunk_size": 50}})

    def test_markdown_smart_routing(self):
        """
        MD 파일이 Document 파서를 건너뛰고,
        주입된 MarkdownSplitter에 의해 구조적으로 분할되는지 통합 테스트
        """
        # 1. MD 파일 생성
        md_text = "# Header\nBody content here."
        with open(os.path.join(self.input_dir, "test.md"), "w", encoding="utf-8") as f:
            f.write(md_text)

        # 2. Ingest 실행
        stats = self.brain.ingest(
            source=self.input_dir,
            destination=self.output_file,
            strategies={
                "connector": "file",
                "chunking": "markdown",
                "assembler": "graph",
                "loader": "file",
            },
        )

        # 3. 성공 여부 확인
        self.assertEqual(stats["processed"], 1)
        self.assertEqual(stats["failed"], 0)

        # 4. 결과 파일 내용 확인
        with open(self.output_file, "r", encoding="utf-8") as f:
            result = json.load(f)

        topics = [n for n in result["nodes"] if n["node_class"] == "sayou:Topic"]
        self.assertTrue(len(topics) > 0, "Markdown header was not detected as Topic")


if __name__ == "__main__":
    unittest.main()
