from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseEmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return vector dimension count (e.g., 384 for bge-small-en-v1.5)."""
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single string into a float vector."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of strings into float vectors."""
        pass


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> str:
        """Generate LLM text completion."""
        pass
