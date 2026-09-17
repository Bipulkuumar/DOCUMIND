import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentStatus
from app.models.chunk import DocumentChunk
from app.repositories.document_repository import DocumentRepository
from app.services.extractors.factory import ExtractorFactory
from app.services.text_cleaner import TextCleaner
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.core.logging import logger


class IngestionService:
    def __init__(self, db: AsyncSession, embedding_service: Optional[EmbeddingService] = None):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.chunker = ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService()


    async def process_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        doc = await self.doc_repo.get_by_id_and_user(document_id, user_id)
        if not doc:
            logger.error(f"Ingestion failed: Document '{document_id}' not found for user '{user_id}'.")
            return False

        try:
            # 1. Update status to PROCESSING
            await self.doc_repo.update_status(document_id, DocumentStatus.PROCESSING)

            # 2. Extract content blocks
            extractor = ExtractorFactory.get_extractor(doc.file_type)
            extracted_blocks = extractor.extract(doc.file_path)

            # 3. Clean extracted text
            for block in extracted_blocks:
                block.text = TextCleaner.clean(block.text)

            # 4. Chunk text blocks with metadata
            processed_chunks = self.chunker.chunk_extracted_content(
                document_id=doc.id,
                filename=doc.filename,
                content_blocks=extracted_blocks
            )

            # 5. Generate vector embeddings in batch
            chunk_texts = [pc.content for pc in processed_chunks]
            embeddings = await self.embedding_service.generate_batch_embeddings(chunk_texts)

            # 6. Create chunk records in DB with embeddings
            db_chunks: List[DocumentChunk] = []
            for pc, emb in zip(processed_chunks, embeddings):
                db_chunk = DocumentChunk(
                    id=pc.chunk_id,
                    document_id=pc.document_id,
                    user_id=user_id,
                    content=pc.content,
                    embedding=emb,
                    chunk_index=pc.chunk_index,
                    page_number=pc.page_number,
                    section=pc.section,
                    token_count=pc.token_count,
                    chunk_metadata=pc.metadata
                )
                db_chunks.append(db_chunk)

            self.db.add_all(db_chunks)
            await self.db.commit()

            # 7. Update status to READY
            await self.doc_repo.update_status(document_id, DocumentStatus.READY)
            logger.info(f"Ingestion succeeded for Document '{doc.filename}' ({len(db_chunks)} chunks with embeddings created).")
            return True


        except Exception as e:
            logger.error(f"Ingestion error for Document '{document_id}': {str(e)}", exc_info=True)
            await self.doc_repo.update_status(document_id, DocumentStatus.FAILED, error_message=str(e))
            return False
