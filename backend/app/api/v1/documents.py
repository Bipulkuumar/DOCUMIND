import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentChunkResponse, ChunkListResponse
from app.schemas.common import StandardResponse

from app.workers.document_worker import process_document_background

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=StandardResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.upload_document(current_user, file)

    # Dispatch background ingestion task
    background_tasks.add_task(process_document_background, doc.id, current_user.id)

    return StandardResponse(
        message="Document uploaded successfully and queued for processing.",
        data=DocumentResponse.model_validate(doc)
    )



@router.get("", response_model=StandardResponse[DocumentListResponse])
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    docs, total = await service.list_documents(current_user.id, page=page, size=size, status=status)
    
    items = [DocumentResponse.model_validate(d) for d in docs]
    return StandardResponse(
        data=DocumentListResponse(
            items=items,
            total=total,
            page=page,
            size=size
        )
    )


@router.get("/{document_id}", response_model=StandardResponse[DocumentResponse])
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document(current_user.id, document_id)
    return StandardResponse(data=DocumentResponse.model_validate(doc))


@router.delete("/{document_id}", response_model=StandardResponse[dict])
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    await service.delete_document(current_user.id, document_id)
    return StandardResponse(message=f"Document '{document_id}' and associated storage were deleted.")


@router.get("/{document_id}/chunks", response_model=StandardResponse[ChunkListResponse])
async def list_document_chunks(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    chunks = await service.get_document_chunks(current_user.id, document_id)
    items = [DocumentChunkResponse.model_validate(c) for c in chunks]
    return StandardResponse(
        data=ChunkListResponse(
            document_id=document_id,
            total_chunks=len(items),
            chunks=items
        )
    )
