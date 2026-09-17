import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation: Conversation) -> Conversation:
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_by_id_and_user(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Conversation]:
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> Tuple[List[Conversation], int]:
        query = select(Conversation).where(Conversation.user_id == user_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        query = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        conversations = list(result.scalars().all())
        return conversations, total

    async def delete(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        conv = await self.get_by_id_and_user(conversation_id, user_id)
        if not conv:
            return False
        await self.session.delete(conv)
        await self.session.commit()
        return True

    async def get_recent_messages(self, conversation_id: uuid.UUID, limit: int = 10) -> List[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages
