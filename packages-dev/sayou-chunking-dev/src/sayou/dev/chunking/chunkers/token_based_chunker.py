#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Token-based chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

from transformers import GPT2Tokenizer

class TokenBasedChunker(BaseChunker):
    """
    Token-based chunker

    Token-based chunking splits text based on a fixed number of tokens rather than words or sentences. It uses tokenizers from NLP models (e.g., Hugging Face's transformers).

    When to Use:
    For models that operate on tokens, such as transformer-based models with token limits (e.g., GPT-3 or GPT-4).

    Advantages:
    - Works well with transformer-based models.
    - Ensures token limits are respected.
    
    Disadvantages:
    - Tokenization may split sentences or break context.
    - Not always aligned with natural language boundaries.
    """
    
    def __init__(self):
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    
    @property
    def name(self) -> str:
        return "token_based_chunker"
    
    def chunk(self, text: str) -> List[str]:
        # Applying Token-Based Chunking
        chunks = self._do_chunk(text)

        for chunk in chunks:
            print(chunk, "\n---\n")
    
    def _do_chunk(self, 
        text: str,
        max_tokens: int = 200) -> List[str]:

        tokens = self.tokenizer(text)["input_ids"]
        chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
        return [self.tokenizer.decode(chunk) for chunk in chunks]

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
    
    chunker = TokenBasedChunker() 
    chunks = chunker.chunk(text)


"""
tokenizer_config.json: 100%|██████████████████████████████████████████████████████████████████████████████████| 26.0/26.0 [00:00<00:00, 94.5kB/s]
vocab.json: 100%|███████████████████████████████████████████████████████████████████████████████████████████| 1.04M/1.04M [00:00<00:00, 1.88MB/s]
merges.txt: 100%|█████████████████████████████████████████████████████████████████████████████████████████████| 456k/456k [00:00<00:00, 1.22MB/s]
tokenizer.json: 100%|███████████████████████████████████████████████████████████████████████████████████████| 1.36M/1.36M [00:00<00:00, 12.0MB/s]
config.json: 100%|██████████████████████████████████████████████████████████████████████████████████████████████| 665/665 [00:00<00:00, 4.13MB/s]

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

 
---

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
 
---

"""