from typing import List, Optional
from app.ai.providers.base import BaseEmbeddingProvider
from app.ai.providers.embeddings import EmbeddingProviderFactory
from app.core.logging import logger


class EmbeddingService:
    def __init__(self, provider: Optional[BaseEmbeddingProvider] = None):
        self.provider = provider or EmbeddingProviderFactory.get_provider()

    async def generate_embedding(self, text: str) -> List[float]:
        return await self.provider.embed_text(text)

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        logger.info(f"Generating embeddings for {len(texts)} text chunks using {self.provider.__class__.__name__}...")
        return await self.provider.embed_batch(texts)
