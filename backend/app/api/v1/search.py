from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.schemas.common import StandardResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=StandardResponse[SearchResponse])
async def search_documents(
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    retrieval_service = RetrievalService(db)
    results = await retrieval_service.search(
        query=body.query,
        user_id=current_user.id,
        top_k=body.top_k,
        similarity_threshold=body.similarity_threshold,
        document_ids=body.document_ids,
    )

    items = [
        SearchResultItem(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            document_name=r.document_name,
            content=r.content,
            similarity=r.similarity,
            page_number=r.page_number,
            section=r.section,
            chunk_index=r.chunk_index,
            metadata=r.metadata,
        )
        for r in results
    ]

    return StandardResponse(
        data=SearchResponse(
            query=body.query,
            total_results=len(items),
            results=items,
        )
    )
