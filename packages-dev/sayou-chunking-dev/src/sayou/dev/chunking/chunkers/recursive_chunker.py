#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Recursive chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

from langchain_text_splitters import RecursiveCharacterTextSplitter

class RecursiveChunker(BaseChunker):
    """
    Recursive chunker

    Recursive chunking divides text in a hierarchical, iterative manner using a set of separations (such as newline characters or spaces). This method allows for more structured chunking based on content boundaries.

    Explanation:
    The method works by recursively splitting text into smaller chunks by examining separators like \n\n, \n, and spaces. LangChain offers the RecursiveCharacterTextSplitter class, which allows the specification of separators to control how the text is split.
    """
    
    def __init__(self):
        pass
    
    @property
    def name(self) -> str:
        return "recursive_chunker"
    
    def chunk(self, text: str) -> List[str]:
        chunks = self._do_chunk(text, chunk_size=50, chunk_overlap=10)

        # Display the chunks
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i + 1}: {chunk}")
        
        return chunks
    
    def _do_chunk(self, 
        text: str, 
        chunk_size: int = 50, 
        chunk_overlap: int = 10) -> List[str]:

        # Initialize the RecursiveCharacterTextSplitter with separators
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " "],
            chunk_size=chunk_size,     # Adjust chunk size as necessary
            chunk_overlap=chunk_overlap   # Optional: overlap chunks for context preservation
        )

        # Split the text
        chunks = splitter.split_text(text)

        return chunks

if __name__ == "__main__":
    # Sample text
    text = """This is a paragraph \n. This is another paragraph. This is a new paragraph.

Here is some additional content.\n"""
    
    chunker = RecursiveChunker() 
    chunks = chunker.chunk(text)


"""
Chunk 1: This is a paragraph
Chunk 2: . This is another paragraph. This is a new
Chunk 3: is a new paragraph.
Chunk 4: Here is some additional content.
"""