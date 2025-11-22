#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Content-aware chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

class ContentAwareChunker(BaseChunker):
    """
    Content-aware chunker

    This method adapts chunking based on content characteristics (e.g., chunking text at paragraph level, tables as separate entities).

    When to Use:
    For documents with heterogeneous content, such as eBooks or technical manuals, chunking must vary based on content type.
    """
    
    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "content_aware_chunker"
    
    def chunk(self, text: str) -> List[str]:
        # Applying Content-Aware Chunking
        chunks = self._do_chunk(text)

        for chunk in chunks:
            print(chunk, "\n---\n")
    
    def _do_chunk(self, text: str) -> List[str]:
        chunks = []
        current_chunk = []
        for line in text.splitlines():
            if line.startswith(('##', '###', 'Introduction', 'Conclusion')):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

if __name__ == "__main__":
    # Sample text
    text = """
Introduction

Data Science is an interdisciplinary field that uses scientific methods, processes, 
algorithms and systems to extract knowledge and insights from structured and 
unstructured data. It draws from statistics, computer science, and machine learning 
and various data analysis techniques to discover patterns, make predictions, and 
derive actionable insights.

Data Science can be applied across many industries, including healthcare, finance, 
marketing, and education, where it helps organizations make data-driven decisions, 
optimize processes, and understand customer behaviors.

Overview of Big Data

Big data refers to large, diverse sets of information that grow at ever-increasing 
rates. It encompasses the volume of information, the velocity or speed at which it is 
creatted and collected, and the variety or scope of the data points being covered.

Data Science Methods

There are several important methods used in Data Science:

1. Regression Analysis
2. Classification
3. Clustering
4. Neural Networks

Challenges in Data Science

- Data Quality: Poor data quality can lead to incorrect conclusions.
- Data Privacy: Ensuring the privacy of sensitive information.
- Scalability: Handling massive datasets efficientyly.

Conclusion

Data Science continues to be a driving force in many industries, offering insights 
that can lead to better decisions and optimized outcomes. It remains an evolving 
field that incorporates the latest technological advancements.
"""
    
    chunker = ContentAwareChunker() 
    chunks = chunker.chunk(text)


"""
---

Introduction

Data Science is an interdisciplinary field that uses scientific methods, processes, 
algorithms and systems to extract knowledge and insights from structured and 
unstructured data. It draws from statistics, computer science, and machine learning 
and various data analysis techniques to discover patterns, make predictions, and 
derive actionable insights.

Data Science can be applied across many industries, including healthcare, finance, 
marketing, and education, where it helps organizations make data-driven decisions, 
optimize processes, and understand customer behaviors.

Overview of Big Data

Big data refers to large, diverse sets of information that grow at ever-increasing 
rates. It encompasses the volume of information, the velocity or speed at which it is 
creatted and collected, and the variety or scope of the data points being covered.

Data Science Methods

There are several important methods used in Data Science:

1. Regression Analysis
2. Classification
3. Clustering
4. Neural Networks

Challenges in Data Science

- Data Quality: Poor data quality can lead to incorrect conclusions.
- Data Privacy: Ensuring the privacy of sensitive information.
- Scalability: Handling massive datasets efficientyly.
 
---

Conclusion

Data Science continues to be a driving force in many industries, offering insights 
that can lead to better decisions and optimized outcomes. It remains an evolving 
field that incorporates the latest technological advancements. 
---

"""