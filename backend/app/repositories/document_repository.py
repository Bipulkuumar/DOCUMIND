import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.document import Document
from app.models.chunk import DocumentChunk


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_by_id_and_user(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50, status: Optional[str] = None
    ) -> Tuple[List[Document], int]:
        query = select(Document).where(Document.user_id == user_id)
        if status:
            query = query.where(Document.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        documents = list(result.scalars().all())
        return documents, total

    async def update_status(self, document_id: uuid.UUID, status: str, error_message: Optional[str] = None) -> Optional[Document]:
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document:
            document.status = status
            if error_message:
                document.error_message = error_message
            await self.session.commit()
            await self.session.refresh(document)
        return document

    async def delete(self, document_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        document = await self.get_by_id_and_user(document_id, user_id)
        if not document:
            return False
        await self.session.delete(document)
        await self.session.commit()
        return True

    async def get_chunks_by_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> List[DocumentChunk]:
        # Enforce tenant check
        doc = await self.get_by_id_and_user(document_id, user_id)
        if not doc:
            return []
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id, DocumentChunk.user_id == user_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(result.scalars().all())
