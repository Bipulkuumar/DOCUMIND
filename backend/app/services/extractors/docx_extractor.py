import docx
from typing import List
from app.services.extractors.base import BaseExtractor, ExtractedChunkContent
from app.core.exceptions import IngestionException


class DOCXExtractor(BaseExtractor):
    def extract(self, file_path: str) -> List[ExtractedChunkContent]:
        results: List[ExtractedChunkContent] = []
        try:
            doc = docx.Document(file_path)
            current_section = "General"
            current_paragraphs: List[str] = []

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue

                if p.style and p.style.name and p.style.name.startswith("Heading"):
                    if current_paragraphs:
                        results.append(
                            ExtractedChunkContent(
                                text="\n".join(current_paragraphs),
                                section=current_section
                            )
                        )
                        current_paragraphs = []
                    current_section = text
                else:
                    current_paragraphs.append(text)

            if current_paragraphs:
                results.append(
                    ExtractedChunkContent(
                        text="\n".join(current_paragraphs),
                        section=current_section
                    )
                )

            return results
        except Exception as e:
            raise IngestionException(f"Failed to extract text from DOCX document: {str(e)}")
