from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..splitter.recursive_splitter import RecursiveSplitter


class LangChainRecursiveSplitter(RecursiveSplitter):

    component_name = "LangChainRecursiveSplitter"
    SUPPORTED_TYPES = ["recursive_char_langchain"]

    def initialize(self, **kwargs):
        self._log("LangChainRecursiveSplitter (Plugin) is ready.")

    def _execute_split_logic(
        self, text: str, chunk_size: int, chunk_overlap: int, separators: List[str]
    ) -> List[str]:
        self._log(f"Executing LangChain recursive split...")

        lc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=separators
        )

        return lc_splitter.split_text(text)
