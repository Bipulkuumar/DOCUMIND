import fitz  # PyMuPDF
from typing import List
from app.services.extractors.base import BaseExtractor, ExtractedChunkContent
from app.core.exceptions import IngestionException


class PDFExtractor(BaseExtractor):
    def extract(self, file_path: str) -> List[ExtractedChunkContent]:
        results: List[ExtractedChunkContent] = []
        try:
            doc = fitz.open(file_path)
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_text = page.get_text("text").strip()
                if page_text:
                    results.append(
                        ExtractedChunkContent(
                            text=page_text,
                            page_number=page_idx + 1,
                            section=f"Page {page_idx + 1}"
                        )
                    )
            doc.close()
            return results
        except Exception as e:
            raise IngestionException(f"Failed to extract text from PDF document: {str(e)}")
