import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import (
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
    MessageResponse,
)
from app.schemas.common import StandardResponse
from app.core.exceptions import ConversationNotFoundException

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=StandardResponse[ConversationListResponse])
async def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    skip = (page - 1) * size
    conversations, total = await repo.list_by_user(current_user.id, skip=skip, limit=size)
    items = [ConversationResponse.model_validate(c) for c in conversations]
    return StandardResponse(
        data=ConversationListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
        )
    )


@router.get("/{conversation_id}", response_model=StandardResponse[ConversationDetailResponse])
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id_and_user(conversation_id, current_user.id)
    if not conv:
        raise ConversationNotFoundException(str(conversation_id))

    messages = await repo.get_recent_messages(conversation_id, limit=100)
    msg_responses = [MessageResponse.model_validate(m) for m in messages]

    return StandardResponse(
        data=ConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=msg_responses,
        )
    )


@router.delete("/{conversation_id}", response_model=StandardResponse[dict])
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    deleted = await repo.delete(conversation_id, current_user.id)
    if not deleted:
        raise ConversationNotFoundException(str(conversation_id))

    return StandardResponse(message=f"Conversation '{conversation_id}' was successfully deleted.")
