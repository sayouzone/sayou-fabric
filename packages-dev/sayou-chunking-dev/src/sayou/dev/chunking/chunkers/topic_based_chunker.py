#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Topic-based chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

class TopicBasedChunker(BaseChunker):
    """
    Topic-based chunker

    This strategy splits the document based on topics using techniques like Latent Dirichlet Allocation (LDA) or other topic modeling algorithms to segment the text.

    When to Use:
    For documents that cover multiple topics, such as news articles, research papers, or reports with diverse subject matter.

    Advantages:
    - Groups related information together.
    - Helps in focused retrieval based on specific topics.

    Disadvantages:
    - Requires additional processing (topic modeling).
    - May not be precise for short documents or overlapping topics.
    """
    
    def __init__(self):
        pass
    
    @property
    def name(self) -> str:
        return "topic_based_chunker"
    
    def chunk(self, text: str) -> List[str]:
        # Get topic-based chunks
        chunks = self._do_chunk(text)

        # Display results
        for topic, chunk in chunks:
            print(f"{topic}:{chunk}\n")

        return chunks
    
    def _do_chunk(self, 
        text: str,
        num_topics: int = 3) -> List[str]:
        
        # Split the text into sentences for chunking
        sentences = text.split('. ')

        # Vectorize the sentences
        vectorizer = CountVectorizer()
        sentence_vectors = vectorizer.fit_transform(sentences)

        # Apply LDA for topic modeling
        lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
        lda.fit(sentence_vectors)

        # Get the topic-word distribution
        topic_word = lda.components_
        vocabulary = vectorizer.get_feature_names_out()

        # Identify the top words for each topic
        topics = []
        for topic_idx, topic in enumerate(topic_word):
            top_words_idx = topic.argsort()[:-6:-1]
            topic_keywords = [vocabulary[i] for i in top_words_idx]
            topics.append("Topic {}: {}".format(topic_idx + 1, ', '.join(topic_keywords)))

        # Generate chunks with topics
        chunks_with_topics = []
        for i, sentence in enumerate(sentences):
            topic_assignments = lda.transform(vectorizer.transform([sentence]))
            assignment_topic = np.argmax(topic_assignments)
            chunks_with_topics.append((topics[assignment_topic], sentence))

        return chunks_with_topics

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
    
    chunker = TopicBasedChunker() 
    chunks = chunker.chunk(text)


"""
Topic 2: data, and, to, science, that:
Introduction

Data Science is an interdisciplinary field that uses scientific methods, processes, 
algorithms and systems to extract knowledge and insights from structured and 
unstructured data

Topic 2: data, and, to, science, that:It draws from statistics, computer science, and machine learning 
and various data analysis techniques to discover patterns, make predictions, and 
derive actionable insights.

Data Science can be applied across many industries, including healthcare, finance, 
marketing, and education, where it helps organizations make data-driven decisions, 
optimize processes, and understand customer behaviors.

Overview of Big Data

Big data refers to large, diverse sets of information that grow at ever-increasing 
rates

Topic 3: the, it, data, methods, of:It encompasses the volume of information, the velocity or speed at which it is 
creatted and collected, and the variety or scope of the data points being covered.

Data Science Methods

There are several important methods used in Data Science:

1

Topic 3: the, it, data, methods, of:Regression Analysis
2

Topic 2: data, and, to, science, that:Classification
3

Topic 1: clustering, classification, analysis, regression, an:Clustering
4

Topic 2: data, and, to, science, that:Neural Networks

Challenges in Data Science

- Data Quality: Poor data quality can lead to incorrect conclusions.
- Data Privacy: Ensuring the privacy of sensitive information.
- Scalability: Handling massive datasets efficientyly.

Conclusion

Data Science continues to be a driving force in many industries, offering insights 
that can lead to better decisions and optimized outcomes

Topic 3: the, it, data, methods, of:It remains an evolving 
field that incorporates the latest technological advancements.

"""