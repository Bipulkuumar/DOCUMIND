import uuid
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.retrieval_service import RetrievalService, SearchResult
from app.services.citation_service import CitationService
from app.ai.prompts.rag import SYSTEM_PROMPT, RAGPromptBuilder
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.llm import LLMProviderFactory
from app.core.logging import logger


@dataclass
class RAGResponse:
    answer: str
    citations: List[Dict[str, Any]]
    search_results: List[SearchResult]


class RAGService:
    def __init__(
        self,
        db: AsyncSession,
        llm_provider: Optional[BaseLLMProvider] = None,
        retrieval_service: Optional[RetrievalService] = None,
    ):
        self.db = db
        self.retrieval_service = retrieval_service or RetrievalService(db)
        self.llm_provider = llm_provider or LLMProviderFactory.get_provider()

    async def answer_question(
        self,
        query: str,
        user_id: uuid.UUID,
        top_k: int = 5,
        similarity_threshold: float = 0.20,
        document_ids: Optional[List[uuid.UUID]] = None,
        conversation_history: str = ""
    ) -> RAGResponse:
        logger.info(f"Processing RAG query: '{query}' for user: {user_id}")

        # 1. Retrieve vector search matches
        search_results = await self.retrieval_service.search(
            query=query,
            user_id=user_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            document_ids=document_ids
        )

        # 2. Check for empty context fallback
        if not search_results:
            logger.info("No relevant document chunks found above threshold. Returning zero-hallucination fallback.")
            return RAGResponse(
                answer="I couldn't find this information in the uploaded documents.",
                citations=[],
                search_results=[]
            )

        # 3. Build grounded prompt
        prompt = RAGPromptBuilder.build_prompt(
            query=query,
            search_results=search_results,
            conversation_history=conversation_history
        )

        # 4. Generate completion from LLM Provider
        answer = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.2
        )

        # 5. Extract citations
        citations = CitationService.build_citations(search_results)

        return RAGResponse(
            answer=answer,
            citations=citations,
            search_results=search_results
        )
