import math
import uuid
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.core.logging import logger


@dataclass
class SearchResult:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    content: str
    similarity: float
    page_number: Optional[int]
    section: Optional[str]
    chunk_index: int
    metadata: Dict[str, Any]


class RetrievalService:
    def __init__(self, db: AsyncSession, embedding_service: Optional[EmbeddingService] = None):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()

    @staticmethod
    def _cosine_similarity_python(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def search(
        self,
        query: str,
        user_id: uuid.UUID,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        document_ids: Optional[List[uuid.UUID]] = None
    ) -> List[SearchResult]:
        if not query.strip():
            return []

        # 1. Generate query embedding vector
        query_vector = await self.embedding_service.generate_embedding(query)

        # 2. Build database query joining DocumentChunk and Document
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.user_id == user_id)
        )

        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

        # Check dialect: if PostgreSQL + pgvector, use native vector cosine distance
        dialect_name = self.db.bind.dialect.name if self.db.bind else "postgresql"

        results: List[SearchResult] = []

        if dialect_name == "postgresql":
            # PostgreSQL pgvector native cosine distance: 1 - cosine_distance
            cosine_score = (1 - DocumentChunk.embedding.cosine_distance(query_vector)).label("similarity")
            pg_stmt = (
                select(DocumentChunk, Document.filename, cosine_score)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.user_id == user_id)
            )
            if document_ids:
                pg_stmt = pg_stmt.where(DocumentChunk.document_id.in_(document_ids))
            if similarity_threshold > 0:
                pg_stmt = pg_stmt.where(cosine_score >= similarity_threshold)

            pg_stmt = pg_stmt.order_by(cosine_score.desc()).limit(top_k)
            exec_res = await self.db.execute(pg_stmt)

            for chunk, doc_name, sim in exec_res.all():
                results.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_name=doc_name,
                        content=chunk.content,
                        similarity=round(float(sim), 4),
                        page_number=chunk.page_number,
                        section=chunk.section,
                        chunk_index=chunk.chunk_index,
                        metadata=chunk.chunk_metadata or {}
                    )
                )
        else:
            # Fallback for SQLite in unit tests: compute similarity in Python
            exec_res = await self.db.execute(stmt)
            rows = exec_res.all()

            scored_items = []
            for chunk, doc_name in rows:
                if chunk.embedding and isinstance(chunk.embedding, list):
                    sim = self._cosine_similarity_python(query_vector, chunk.embedding)
                else:
                    # Simple text overlap score if embeddings not serialized as list in test DB
                    q_words = set(query.lower().split())
                    c_words = set(chunk.content.lower().split())
                    overlap = len(q_words.intersection(c_words))
                    sim = min(1.0, overlap / max(1, len(q_words)))

                if sim >= similarity_threshold:
                    scored_items.append((sim, chunk, doc_name))

            scored_items.sort(key=lambda x: x[0], reverse=True)
            for sim, chunk, doc_name in scored_items[:top_k]:
                results.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_name=doc_name,
                        content=chunk.content,
                        similarity=round(float(sim), 4),
                        page_number=chunk.page_number,
                        section=chunk.section,
                        chunk_index=chunk.chunk_index,
                        metadata=chunk.chunk_metadata or {}
                    )
                )

        logger.info(f"Retrieval returned {len(results)} chunks for query: '{query}' (user: {user_id}).")
        return results
