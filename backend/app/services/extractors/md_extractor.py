import re
from typing import List
from app.services.extractors.base import BaseExtractor, ExtractedChunkContent
from app.core.exceptions import IngestionException


class MDExtractor(BaseExtractor):
    def extract(self, file_path: str) -> List[ExtractedChunkContent]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        results: List[ExtractedChunkContent] = []
        current_section = "Overview"
        current_lines: List[str] = []

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in content.splitlines():
            match = heading_pattern.match(line.strip())
            if match:
                if current_lines:
                    text_block = "\n".join(current_lines).strip()
                    if text_block:
                        results.append(
                            ExtractedChunkContent(text=text_block, section=current_section)
                        )
                    current_lines = []
                current_section = match.group(2).strip()
            else:
                current_lines.append(line)

        if current_lines:
            text_block = "\n".join(current_lines).strip()
            if text_block:
                results.append(
                    ExtractedChunkContent(text=text_block, section=current_section)
                )

        if not results and content.strip():
            results.append(ExtractedChunkContent(text=content.strip(), section="Main Content"))

        return results
