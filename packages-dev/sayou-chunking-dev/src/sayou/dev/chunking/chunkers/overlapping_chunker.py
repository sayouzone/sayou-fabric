#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Overlapping chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

class OverlappingChunker(BaseChunker):
    """
    Overlapping chunker

    Machine translation, summarization, or question-answering

    What It Is:
    Overlapping chunking involves creating chunks that overlap with each other. For example, one chunk might contain the last few words of the previous chunk. This strategy is used to preserve context between chunks and ensure that no information is lost when dividing long texts.

    Use Case:
    Useful when context between sentences is important, such as for tasks like machine translation, summarization, or question-answering where the meaning of adjacent chunks is highly dependent on each other.
    """
    
    def __init__(self):
        pass
    
    @property
    def name(self) -> str:
        return "overlapping_chunker"
    
    def chunk(self, text: str) -> List[str]:
        chunks = self._do_chunk(text, chunk_size=5, overlap=2)

        # Display the documents to check their structure
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i + 1}: {chunk}")

        return chunks
    
    def _do_chunk(self, 
        text: str, 
        chunk_size: int = 5, 
        overlap: int = 2) -> List[str]:
        
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = words[i:i + chunk_size]
            chunks.append(' '.join(chunk))
        
        return chunks

if __name__ == "__main__":
    text = "This is an example of overlapping chunking to maintain context between chunks."
    
    chunker = OverlappingChunker() 
    chunks = chunker.chunk(text)


"""
Chunk 1: This is an example of
Chunk 2: example of overlapping chunking to
Chunk 3: chunking to maintain context between
Chunk 4: context between chunks.
"""