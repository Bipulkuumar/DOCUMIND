from typing import List
from app.services.extractors.base import BaseExtractor, ExtractedChunkContent
from app.core.exceptions import IngestionException


class TXTExtractor(BaseExtractor):
    def extract(self, file_path: str) -> List[ExtractedChunkContent]:
        content = ""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue

        if not content:
            raise IngestionException("Failed to decode TXT document content with supported encodings.")

        # Split content into non-empty paragraphs or blocks
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content.strip()]

        return [
            ExtractedChunkContent(
                text="\n\n".join(paragraphs),
                section="Main Content"
            )
        ]
