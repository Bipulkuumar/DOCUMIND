from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_health
from app.schemas.common import HealthResponse, StandardResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_ok = await check_db_health()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        database_connected=db_ok,
        vector_search_ready=db_ok,
    )


@router.get("/metrics", response_model=StandardResponse[dict])
async def get_metrics():
    # Placeholder for application metrics abstraction
    metrics_data = {
        "documents_processed": 0,
        "chunks_indexed": 0,
        "total_queries": 0,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER,
    }
    return StandardResponse(data=metrics_data)
