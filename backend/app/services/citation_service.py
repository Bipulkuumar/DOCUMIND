import uuid
from typing import List, Dict, Any
from app.services.retrieval_service import SearchResult


class CitationService:
    @staticmethod
    def build_citations(search_results: List[SearchResult]) -> List[Dict[str, Any]]:
        citations = []
        seen_chunks = set()

        for res in search_results:
            if str(res.chunk_id) in seen_chunks:
                continue
            seen_chunks.add(str(res.chunk_id))

            citation = {
                "document_id": str(res.document_id),
                "document_name": res.document_name,
                "chunk_id": str(res.chunk_id),
                "page": res.page_number,
                "section": res.section,
                "similarity": res.similarity,
                "snippet": res.content[:200] + ("..." if len(res.content) > 200 else "")
            }
            citations.append(citation)

        return citations
