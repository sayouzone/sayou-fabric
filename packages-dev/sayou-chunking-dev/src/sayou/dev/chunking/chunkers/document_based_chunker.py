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

if __name__ == "__main__":
    pdf_file = "./data/Salesforce FY25 Annual Report.pdf"
    
    chunker = DocumentBasedChunker()
    chunks = chunker.chunk(pdf_file)


"""
Document 1 Content:
Salesforce FY25 Annual Report
Need Help? Ask Agentforce.
Leading the
AI Agent Revolution
FY25 Annual Report
© 2025 Salesforce, Inc. All rights reserved. Salesforce and salesforce.com are registered trademarks of Salesforce, Inc.  
Salesforce owns other registered and unregistered trademarks. Other names used herein may be trademarks of their respective owners.
salesforce.com


Document 2 Content:
Worldwide Corporate Headquarters
Salesforce, Inc.
Salesforce Tower
415 Mission Street, 3rd Floor
San Francisco, CA 94105, USA
1-800-NO-SOFTWARE


Document 3 Content:
1  “Remaining Performance Obligation” represents future revenues that are under contract but have not yet been recognized.
2 Non-GAAP operating margin is a non-GAAP financial measure. Refer to page 6 for a reconciliation of GAAP to non-GAAP financial measures.
FY25 Highlights
FY25 marked an important moment of 
opportunity and possibility . AI is reshaping 
business, and Salesforce is leading the way with 
record-breaking momentum. We just delivered 
our highest revenue, operating margin, and ca


"""