import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from app.services.extractors.base import ExtractedChunkContent


@dataclass
class ProcessedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    page_number: Optional[int]
    section: Optional[str]
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChunkingService:
    def __init__(self, target_chunk_tokens: int = 800, overlap_tokens: int = 120):
        self.target_chunk_tokens = target_chunk_tokens
        self.overlap_tokens = overlap_tokens
        # Approximate 4 characters per token
        self.target_chunk_chars = target_chunk_tokens * 4
        self.overlap_chars = overlap_tokens * 4

    def _estimate_tokens(self, text: str) -> int:
        # Standard token estimation: max(1, len(text) // 4) or word count approximation
        words = text.split()
        return max(1, len(words) * 4 // 3)

    def chunk_extracted_content(
        self,
        document_id: uuid.UUID,
        filename: str,
        content_blocks: List[ExtractedChunkContent]
    ) -> List[ProcessedChunk]:
        processed_chunks: List[ProcessedChunk] = []
        global_chunk_index = 0

        for block in content_blocks:
            raw_text = block.text.strip()
            if not raw_text:
                continue

            # If text block fits in target chunk size, output as single chunk
            if len(raw_text) <= self.target_chunk_chars:
                token_cnt = self._estimate_tokens(raw_text)
                processed_chunks.append(
                    ProcessedChunk(
                        chunk_id=uuid.uuid4(),
                        document_id=document_id,
                        chunk_index=global_chunk_index,
                        content=raw_text,
                        page_number=block.page_number,
                        section=block.section,
                        token_count=token_cnt,
                        metadata={
                            "source_filename": filename,
                            "estimated_tokens": token_cnt,
                            **block.metadata
                        }
                    )
                )
                global_chunk_index += 1
            else:
                # Sliding window chunking with overlap
                start = 0
                step = self.target_chunk_chars - self.overlap_chars
                if step <= 0:
                    step = self.target_chunk_chars // 2

                while start < len(raw_text):
                    end = start + self.target_chunk_chars
                    slice_text = raw_text[start:end].strip()

                    # Find clean space or line break near end slice boundary
                    if end < len(raw_text):
                        last_space = slice_text.rfind(" ")
                        if last_space > self.target_chunk_chars // 2:
                            slice_text = slice_text[:last_space].strip()
                            start += last_space - self.overlap_chars
                        else:
                            start += step
                    else:
                        start += step

                    if slice_text:
                        token_cnt = self._estimate_tokens(slice_text)
                        processed_chunks.append(
                            ProcessedChunk(
                                chunk_id=uuid.uuid4(),
                                document_id=document_id,
                                chunk_index=global_chunk_index,
                                content=slice_text,
                                page_number=block.page_number,
                                section=block.section,
                                token_count=token_cnt,
                                metadata={
                                    "source_filename": filename,
                                    "estimated_tokens": token_cnt,
                                    **block.metadata
                                }
                            )
                        )
                        global_chunk_index += 1

        return processed_chunks
