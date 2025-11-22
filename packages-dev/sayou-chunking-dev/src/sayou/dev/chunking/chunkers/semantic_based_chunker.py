#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Semantic-based chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np

class SemanticBasedChunker(BaseChunker):
    """
    Semantic-based chunker

    Semantic-based Chunking (Dynamic Chunking)
    Meaningful semantic units (e.g., paragraphs, topics)

    What It Is:
    Semantic-based chunking involves splitting text into chunks based on the meaning of the content rather than fixed length or sentence boundaries. The idea is to group related information, which may vary in length, into semantic units. This is often done using NLP techniques, such as sentence embeddings or document clustering, to identify the most relevant sections for each chunk.

    Use Case:
    Best for use in situations where meaningful semantic units (e.g., paragraphs, topics) should be grouped together regardless of the chunk size. This is useful for document summarization, knowledge extraction, and other advanced NLP tasks.
    """
    
    def __init__(self):
        # Initialize a model for sentence embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    @property
    def name(self) -> str:
        return "semantic_based_chunker"
    
    def chunk(self, text: str) -> List[str]:
        # Add text splitter
        #return self._do_chunk(text)
        return []
    
    def _do_chunk(self, sentences: List[str]) -> List[str]:
        # Create embeddings for each sentence
        embeddings = self.model.encode(sentences)

        # Use clustering to group semantically similar sentences
        kmeans = KMeans(n_clusters=2, random_state=0)
        labels = kmeans.fit_predict(embeddings)

        # Group sentences by their cluster label
        chunks = {}
        for i, label in enumerate(labels):
            if label not in chunks:
                chunks[label] = []
            chunks[label].append(sentences[i])

        # Display the documents to check their structure
        for label, chunk in chunks.items():
            print(f"Semantic Chunk {label + 1}: {', '.join(chunk)}")

        
        return [' '.join(chunk) for chunk in chunks.values()]

if __name__ == "__main__":
    text = "This is a sentence. There is another one. And a third one."
    
    chunker = SemanticBasedChunker()
    chunks = chunker.chunk(text)
