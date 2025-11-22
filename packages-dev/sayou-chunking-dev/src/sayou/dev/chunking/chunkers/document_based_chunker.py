#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Document-based chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

from langchain_community.document_loaders import PyPDFLoader

class DocumentBasedChunker(BaseChunker):
    """
    Document-based chunker

    Articles, reports, or books
    
    What It Is:
    Document-based chunking involves treating each document or major section of text as a chunk. This approach is used when the corpus consists of multiple documents that need to be retrieved independently.

    Use Case:
    Useful when the corpus is already organized into meaningful documents, such as articles, reports, or books. LlamaIndex (formerly GPT Index) has a built-in feature that can identify document boundaries.
    """
    
    def __init__(self):
        pass
    
    @property
    def name(self) -> str:
        return "document_based_chunker"
    
    def chunk(self, text: str) -> List[str]:
        return self._do_chunk(text)
    
    def _do_chunk(self, text: str) -> List[str]:
        pdf_loader = PyPDFLoader(text)

        # Load the PDF into documents
        pdf_documents = pdf_loader.load()

        # Display the documents to check their structure
        for i, doc in enumerate(pdf_documents[:3]):
            print(f"Document {i + 1} Content:")
            print(doc.page_content[:500])
            print("\n")
        
        chunks = []
        for doc in pdf_documents:
            chunks.append(doc.page_content)
        
        return chunks