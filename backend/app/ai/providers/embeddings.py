import hashlib
import math
from typing import List, Optional
import httpx

from app.ai.providers.base import BaseEmbeddingProvider
from app.core.config import settings
from app.core.logging import logger


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic normalized pseudo-embeddings for fast offline testing and fallback."""
    def __init__(self, dim: int = 384):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _generate_vector(self, text: str) -> List[float]:
        # Hash text to generate deterministic pseudo-random normalized vector
        vec = []
        for i in range(self._dim):
            h = hashlib.md5(f"{text}_{i}".encode("utf-8")).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)
        # Normalize vector to unit length
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


class APIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI-compatible embedding provider using httpx."""
    def __init__(
        self,
        api_key: str = "",
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        dim: int = 384
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_text(self, text: str) -> List[float]:
        res = await self.embed_batch([text])
        return res[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            logger.warning("No API key provided for APIEmbeddingProvider. Falling back to mock embeddings.")
            mock = MockEmbeddingProvider(dim=self._dim)
            return await mock.embed_batch(texts)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": texts,
            "model": self.model,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/embeddings", json=payload, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Embedding API error [{resp.status_code}]: {resp.text}")
                mock = MockEmbeddingProvider(dim=self._dim)
                return await mock.embed_batch(texts)
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local SentenceTransformers model wrapper with fallback."""
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", dim: int = 384):
        self.model_name = model_name
        self._dim = dim
        self._model = None
        self._fallback_provider = MockEmbeddingProvider(dim=dim)

    @property
    def dimension(self) -> int:
        return self._dim

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"Could not load local embedding model '{self.model_name}' ({e}). Using deterministic embedding fallback.")
                self._model = False

    async def embed_text(self, text: str) -> List[float]:
        self._load_model()
        if self._model:
            embedding = self._model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        return await self._fallback_provider.embed_text(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        if self._model:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return [e.tolist() for e in embeddings]
        return await self._fallback_provider.embed_batch(texts)


class EmbeddingProviderFactory:
    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> BaseEmbeddingProvider:
        p_type = (provider_type or settings.EMBEDDING_PROVIDER).lower()
        if p_type == "local":
            return LocalEmbeddingProvider(
                model_name=settings.EMBEDDING_MODEL,
                dim=settings.EMBEDDING_DIMENSION
            )
        elif p_type in ("openai", "api"):
            return APIEmbeddingProvider(
                api_key=settings.LLM_API_KEY,
                model=settings.EMBEDDING_MODEL,
                base_url=settings.LLM_BASE_URL,
                dim=settings.EMBEDDING_DIMENSION
            )
        else:
            return MockEmbeddingProvider(dim=settings.EMBEDDING_DIMENSION)
