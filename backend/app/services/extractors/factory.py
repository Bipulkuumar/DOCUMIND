from typing import Dict, Type
from app.services.extractors.base import BaseExtractor
from app.services.extractors.pdf_extractor import PDFExtractor
from app.services.extractors.docx_extractor import DOCXExtractor
from app.services.extractors.txt_extractor import TXTExtractor
from app.services.extractors.md_extractor import MDExtractor
from app.core.exceptions import IngestionException


class ExtractorFactory:
    _extractors: Dict[str, Type[BaseExtractor]] = {
        "pdf": PDFExtractor,
        "docx": DOCXExtractor,
        "txt": TXTExtractor,
        "md": MDExtractor,
        "markdown": MDExtractor,
    }

    @classmethod
    def get_extractor(cls, file_type: str) -> BaseExtractor:
        normalized_type = file_type.lower().lstrip(".")
        extractor_cls = cls._extractors.get(normalized_type)
        if not extractor_cls:
            raise IngestionException(
                f"No extractor registered for document type '{file_type}'."
            )
        return extractor_cls()
