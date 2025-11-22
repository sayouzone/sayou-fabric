#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

from sayou.dev.chunking.base_chunker import BaseChunker

from nltk.tokenize import sent_tokenize
import nltk
import ssl

class SentenceBasedChunker(BaseChunker):
    """
    Sentence-based chunker

    Research papers, news articles
    
    What It Is:
    Sentence-based chunking divides the text into individual sentences, treating each as a chunk. This is useful when working with structured text or datasets where each sentence contains meaningful information and needs to be processed independently.

    Use Case:
    Ideal for processing formal documents (e.g., research papers, news articles) where individual sentences convey significant meaning.
    """
    

    def __init__(self):
        # SSL 인증서 검증 실패 문제 해결을 위한 코드se
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        nltk.download('punkt_tab')

    @property
    def name(self) -> str:
        return "sentence_based_chunker"
    
    def chunk(self, text: str) -> List[str]:
        chunks = self._do_chunk(text)

        # Display the chunks
        for i, chunk in enumerate(chunks):
            print(f"Sentence {i + 1}: {chunk}")

        return chunks
    
    def _do_chunk(self, text: str) -> List[str]:
        # Chunk text into sentences
        chunks = sent_tokenize(text)

        return chunks

if __name__ == "__main__":
    text = "This is a sentence. There is another one. And a third one."
    
    chunker = SentenceBasedChunker()
    chunks = chunker.chunk(text)


"""
[nltk_data] Downloading package punkt_tab to
[nltk_data]     /Users/seongjungkim/nltk_data...
[nltk_data]   Package punkt_tab is already up-to-date!
Sentence 1: This is a sentence.
Sentence 2: There is another one.
Sentence 3: And a third one.
"""