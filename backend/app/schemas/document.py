import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    doc_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    size: int


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    token_count: int
    chunk_metadata: Dict[str, Any]
    created_at: datetime


class ChunkListResponse(BaseModel):
    document_id: uuid.UUID
    total_chunks: int
    chunks: List[DocumentChunkResponse]
