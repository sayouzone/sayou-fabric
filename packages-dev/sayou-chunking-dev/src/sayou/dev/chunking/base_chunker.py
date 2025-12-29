#
# Copyright (c) 2025, Sayouzone
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Base chunker

This module provides a abstract base chunker class for chunking text.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

class BaseChunker(ABC):
    """Abstract base chunker.
    
    
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the chunker
        
        Returns:
            Name of the chunker
        """
        pass

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """Chunk the text"""
        raise NotImplementedError
    
    # TODO: add more methods