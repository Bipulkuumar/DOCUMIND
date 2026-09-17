import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(5, ge=1, le=50, description="Maximum number of relevant chunks to retrieve")
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum cosine similarity threshold")
    document_ids: Optional[List[uuid.UUID]] = Field(None, description="Optional array of document IDs to restrict search scope")


class SearchResultItem(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    content: str
    similarity: float
    page_number: Optional[int] = None
    section: Optional[str] = None
    chunk_index: int
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
