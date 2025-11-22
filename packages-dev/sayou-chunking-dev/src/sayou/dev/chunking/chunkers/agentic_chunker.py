#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Agentic chunker"""

from sayou.dev.chunking.base_chunker import BaseChunker

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class AgenticChunker(BaseChunker):
    """
    Agentic chunker

    Agentic chunking leverages large language models (LLMs) to determine how to chunk the text based on its context. This is a more dynamic approach where the model itself decides how much and what part of the text should form a chunk.

    Explanation:
    The LLM is tasked with understanding the context of the text and then creating chunks based on the relevance of the information. This technique uses the model's understanding of the content to ensure that chunks are informative and relevant.
    """
    
    def __init__(self):
        # Load the tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained("t5-base")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("t5-base")
    
    @property
    def name(self) -> str:
        return "agentic_chunker"
    
    def chunk(self, text: str) -> List[str]:
        chunks = self._do_chunk(text)

        # Display the chunks
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i + 1}: {chunk}")
        
        return chunks
    
    def _do_chunk(self, 
        text: str, 
        max_length: int = 512, 
        stride: int = 256) -> List[str]:
        
        """Chunks text into smaller pieces based on token and stride
    
        Args:
            text (str): The input text.
            max_length (int, optional): Maximum token length of each chunk. Defaults to 512.
            stride (int, optional): Overlap between chunks. Defaults to 256.

        Returns:
            list: A List of text chunks.
        """
        
        input_ids = self.tokenizer(text, return_tensors="pt").input_ids[0]

        chunks = []
        i = 0
        while i < len(input_ids):
            end_idx = min(i + max_length, len(input_ids))
            chunk_ids = input_ids[i:end_idx]
            chunks.append(self.tokenizer.decode(chunk_ids, skip_special_tokens=True))
            i += stride

        return chunks


if __name__ == "__main__":
    text = "Astronauts travel through space. The journey is difficult. Exploration of Mars is a recent milestone in space science."
    
    chunker = AgenticChunker() 
    chunks = chunker.chunk(text)


"""
config.json: 100%|██████████████████████████████████████████████████████████████████████████████████████████| 1.21k/1.21k [00:00<00:00, 3.74MB/s]
spiece.model: 100%|███████████████████████████████████████████████████████████████████████████████████████████| 792k/792k [00:00<00:00, 1.44MB/s]
tokenizer.json: 100%|███████████████████████████████████████████████████████████████████████████████████████| 1.39M/1.39M [00:00<00:00, 1.91MB/s]
model.safetensors: 100%|██████████████████████████████████████████████████████████████████████████████████████| 892M/892M [00:27<00:00, 32.4MB/s]
generation_config.json: 100%|████████████████████████████████████████████████████████████████████████████████████| 147/147 [00:00<00:00, 637kB/s]
Chunk 1: Astronauts travel through space. The journey is difficult. Exploration of Mars is a recent milestone in space science.
"""