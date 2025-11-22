#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Fixed length chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

class FixedLengthChunker(BaseChunker):
    """
    Fixed length chunker
    
    Fixed-size Chunking (Sliding Window)

    What It Is:
    Fixed-size chunking divides the text into fixed-length pieces or windows. This is done by splitting the text into chunks of a predetermined size (e.g., 512 tokens). This strategy is simple but can be inefficient for longer texts, especially if chunks cut across meaningful sections (like sentences).

    Use Case:
    Best for datasets where text length is fairly uniform or where processing uniform chunks is necessary.
    """
    
    def __init__(self, chunk_size: int = 512):
        self.chunk_size = chunk_size
    
    @property
    def name(self) -> str:
        return "fixed_length_chunker"
    
    def chunk(self, text: str) -> List[str]:
        """
        Chunk the text
        
        Args:
            text: Text to chunk
        
        Returns:
            List of chunks
        """

        chunks = self._do_chunk(text, self.chunk_size)

        # Display the chunks
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i + 1}: {chunk}")
        
        return chunks

    def _do_chunk(self, 
        text: str, 
        chunk_size: int = 512) -> List[str]:
        
        """
        Split text into words and chunk them into fixed-size parts
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
        
        Returns:
            List of chunks
        """
        words = text.split()
        chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
        chunks = [' '.join(chunk) for chunk in chunks]
        return chunks

if __name__ == "__main__":
    text = "This is a very long text that should be chunked into smaller pieces for efficient processing."
    
    chunker = FixedLengthChunker()
    chunks = chunker.chunk(text)


"""
Chunk 1: This is a very long
Chunk 2: text that should be chunked
Chunk 3: into smaller pieces for efficient
Chunk 4: processing.
"""