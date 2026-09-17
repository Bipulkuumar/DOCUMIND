import os
import uuid
from typing import List, Tuple, Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import BaseStorageService, LocalStorageService
from app.core.exceptions import InvalidFileException, DocumentNotFoundException, AppException
from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentService:
    def __init__(self, db: AsyncSession, storage: Optional[BaseStorageService] = None):
        self.db = db
        self.repo = DocumentRepository(db)
        self.storage = storage or LocalStorageService(settings.STORAGE_DIR)

    async def upload_document(self, user: User, file: UploadFile) -> Document:
        if not file.filename:
            raise InvalidFileException("Filename cannot be empty")

        filename = os.path.basename(file.filename)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileException(
                f"Unsupported file type '{ext}'. Allowed file formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        content = await file.read()
        file_size = len(content)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise InvalidFileException(
                f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        document_id = uuid.uuid4()
        relative_path = f"{user.id}/{document_id}{ext}"
        saved_file_path = await self.storage.save_file(content, relative_path)

        document = Document(
            id=document_id,
            user_id=user.id,
            filename=filename,
            file_path=saved_file_path,
            file_type=ext.lstrip("."),
            file_size=file_size,
            status=DocumentStatus.UPLOADED,
            doc_metadata={
                "original_filename": filename,
                "file_extension": ext,
            }
        )
        return await self.repo.create(document)

    async def get_document(self, user_id: uuid.UUID, document_id: uuid.UUID) -> Document:
        doc = await self.repo.get_by_id_and_user(document_id, user_id)
        if not doc:
            raise DocumentNotFoundException(str(document_id))
        return doc

    async def list_documents(
        self, user_id: uuid.UUID, page: int = 1, size: int = 20, status: Optional[str] = None
    ) -> Tuple[List[Document], int]:
        skip = (page - 1) * size
        return await self.repo.list_by_user(user_id, skip=skip, limit=size, status=status)

    async def delete_document(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bool:
        doc = await self.get_document(user_id, document_id)
        # Delete file from storage
        await self.storage.delete_file(doc.file_path)
        # Delete record & associated chunks from DB
        return await self.repo.delete(document_id, user_id)

    async def get_document_chunks(self, user_id: uuid.UUID, document_id: uuid.UUID):
        # Enforce existence and ownership
        await self.get_document(user_id, document_id)
        return await self.repo.get_chunks_by_document(document_id, user_id)
