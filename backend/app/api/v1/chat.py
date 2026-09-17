import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.retrieval_log import RetrievalLog
from app.api.deps import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse, CitationItem
from app.schemas.common import StandardResponse
from app.services.rag_service import RAGService
from app.repositories.conversation_repository import ConversationRepository

from app.core.exceptions import ConversationNotFoundException

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=StandardResponse[ChatResponse], status_code=status.HTTP_200_OK)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv_repo = ConversationRepository(db)

    # 1. Fetch or create conversation
    if body.conversation_id:
        conversation = await conv_repo.get_by_id_and_user(body.conversation_id, current_user.id)
        if not conversation:
            raise ConversationNotFoundException(str(body.conversation_id))
    else:
        conversation = await conv_repo.create(Conversation(user_id=current_user.id, title=body.message[:40]))


    # 2. Record User Message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.commit()

    # 3. Format history window for multi-turn memory (if existing conversation)
    history_messages = await conv_repo.get_recent_messages(conversation.id, limit=6)
    history_lines = []
    for m in history_messages:
        if m.id != user_msg.id:
            history_lines.append(f"{m.role.capitalize()}: {m.content}")
    conv_history_str = "\n".join(history_lines)

    # 4. Execute RAG pipeline
    rag_service = RAGService(db)
    rag_res = await rag_service.answer_question(
        query=body.message,
        user_id=current_user.id,
        top_k=body.top_k,
        similarity_threshold=body.similarity_threshold,
        document_ids=body.document_ids,
        conversation_history=conv_history_str
    )

    # 5. Record Assistant Message & Retrieval Log
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=rag_res.answer,
        citations=rag_res.citations
    )
    db.add(assistant_msg)

    retrieval_log = RetrievalLog(
        conversation_id=conversation.id,
        query=body.message,
        retrieved_chunk_ids=[str(r.chunk_id) for r in rag_res.search_results],
        latency_ms=100.0  # Placeholder latency metric
    )
    db.add(retrieval_log)
    await db.commit()
    await db.refresh(assistant_msg)

    citations_list = [CitationItem(**c) for c in rag_res.citations]

    return StandardResponse(
        data=ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_msg.id,
            answer=rag_res.answer,
            citations=citations_list
        )
    )
