from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ExtractedChunkContent:
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> List[ExtractedChunkContent]:
        """Extract structured text content blocks with page and section metadata from a file."""
        pass
