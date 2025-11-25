# Chunkers

[RAG Chunking Strategies [Top 11] | Semantic Chunking to LLM Chunking | Learn RAG from Scratch](https://www.youtube.com/watch?v=-hsaiU6fmtQ)

## Fixed Length Chunker

Fixed-size Chunking (Sliding Window)

What It Is:
    Fixed-size chunking divides the text into fixed-length pieces or windows. This is done by splitting the text into chunks of a predetermined size (e.g., 512 tokens). This strategy is simple but can be inefficient for longer texts, especially if chunks cut across meaningful sections (like sentences).

Use Case:
    Best for datasets where text length is fairly uniform or where processing uniform chunks is necessary.

## Sentence Based Chunker

Sentence-based Chunking

Research papers, news articles
    
What It Is:
    Sentence-based chunking divides the text into individual sentences, treating each as a chunk. This is useful when working with structured text or datasets where each sentence contains meaningful information and needs to be processed independently.

Use Case:
    Ideal for processing formal documents (e.g., research papers, news articles) where individual sentences convey significant meaning.

## Document Based Chunker

Document-based Chunking

Articles, reports, or books
    
What It Is:
    Document-based chunking involves treating each document or major section of text as a chunk. This approach is used when the corpus consists of multiple documents that need to be retrieved independently.

Use Case:
    Useful when the corpus is already organized into meaningful documents, such as articles, reports, or books. LlamaIndex (formerly GPT Index) has a built-in feature that can identify document boundaries.

## Semantic Based Chunker

Semantic-based Chunking (Dynamic Chunking)

Meaningful semantic units (e.g., paragraphs, topics)

What It Is:
    Semantic-based chunking involves splitting text into chunks based on the meaning of the content rather than fixed length or sentence boundaries. The idea is to group related information, which may vary in length, into semantic units. This is often done using NLP techniques, such as sentence embeddings or document clustering, to identify the most relevant sections for each chunk.

Use Case:
    Best for use in situations where meaningful semantic units (e.g., paragraphs, topics) should be grouped together regardless of the chunk size. This is useful for document summarization, knowledge extraction, and other advanced NLP tasks.

## Overlapping Chunker

Overlapping Chunking

Machine translation, summarization, or question-answering

What It Is:
    Overlapping chunking involves creating chunks that overlap with each other. For example, one chunk might contain the last few words of the previous chunk. This strategy is used to preserve context between chunks and ensure that no information is lost when dividing long texts.

Use Case:
    Useful when context between sentences is important, such as for tasks like machine translation, summarization, or question-answering where the meaning of adjacent chunks is highly dependent on each other.

## Recursive Chunker

Recursive Chunking

Recursive chunking divides text in a hierarchical, iterative manner using a set of separations (such as newline characters or spaces). This method allows for more structured chunking based on content boundaries.

Explanation:
    The method works by recursively splitting text into smaller chunks by examining separators like \n\n, \n, and spaces. LangChain offers the RecursiveCharacterTextSplitter class, which allows the specification of separators to control how the text is split.

## Agentic Chunker

Agentic chunking leverages large language models (LLMs) to determine how to chunk the text based on its context. This is a more dynamic approach where the model itself decides how much and what part of the text should form a chunk.

Explanation:
    The LLM is tasked with understanding the context of the text and then creating chunks based on the relevance of the information. This technique uses the model's understanding of the content to ensure that chunks are informative and relevant.

## Content-aware Chunker

Content-Aware Chunking

This method adapts chunking based on content characteristics (e.g., chunking text at paragraph level, tables as separate entities).

When to Use:
    For documents with heterogeneous content, such as eBooks or technical manuals, chunking must vary based on content type.

## Token Based Chunker

Token-Based Chunking

Token-based chunking splits text based on a fixed number of tokens rather than words or sentences. It uses tokenizers from NLP models (e.g., Hugging Face's transformers).

When to Use:
    For models that operate on tokens, such as transformer-based models with token limits (e.g., GPT-3 or GPT-4).

Advantages:
    - Works well with transformer-based models.
    - Ensures token limits are respected.

Disadvantages:
    - Tokenization may split sentences or break context.
    - Not always aligned with natural language boundaries.

## Topic Based Chunker

Topic-Based Chunking

This strategy splits the document based on topics using techniques like Latent Dirichlet Allocation (LDA) or other topic modeling algorithms to segment the text.

When to Use:
    For documents that cover multiple topics, such as news articles, research papers, or reports with diverse subject matter.

Advantages:
    - Groups related information together.
    - Helps in focused retrieval based on specific topics.

Disadvantages:
    - Requires additional processing (topic modeling).
    - May not be precise for short documents or overlapping topics.

## Keyword Based Chunker

Keyword-Based Chunking

This method chunks documents based on predefined keywords or phrases that signal topic shifts (e.g., "Introduction", "Conclusion").

When to Use:
    Best for documents that follow a clear structure, such as scientific papers or technical specifications.

Advantages:
    - Captures natural topic breaks based on keywords.
    - Works well for structured documents.

Disadvantages:
    - Requires a predefined set of keywords.
    - Not adaptable to unstructured documents.