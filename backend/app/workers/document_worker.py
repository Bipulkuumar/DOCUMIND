import uuid
from app.db import session as db_session
from app.services.ingestion_service import IngestionService
from app.core.logging import logger


async def process_document_background(document_id: uuid.UUID, user_id: uuid.UUID):
    logger.info(f"Starting background document processing for doc: {document_id}")
    async with db_session.get_async_session() as db:
        service = IngestionService(db)
        await service.process_document(document_id, user_id)
