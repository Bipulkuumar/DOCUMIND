import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = Field(None, description="Optional conversation ID to continue multi-turn chat")
    message: str = Field(..., min_length=1, description="Natural language user question")
    document_ids: Optional[List[uuid.UUID]] = Field(None, description="Optional array of document IDs to restrict search scope")
    top_k: int = Field(5, ge=1, le=20)
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0)



class CitationItem(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    page: Optional[int] = None
    section: Optional[str] = None
    similarity: float
    snippet: str


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: List[CitationItem]
