from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List

class Block(BaseModel):
    """Represents a block of text with associated layout metadata."""
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    font_weight: str # e.g., "bold", "normal"

class Page(BaseModel):
    """Represents a single page extracted from a document."""
    page_number: int
    text: str
    blocks: List[Block]

class PreProcessor(ABC):
    """
    Abstract Base Class for all document pre-processors.
    This defines the standard interface for converting source documents
    into a list of Page objects.
    """

    @abstractmethod
    def extract_pages(self, document_path: str) -> List[Page]:
        """
        Extracts all pages from a source document.

        Args:
            document_path: The file path to the source document.

        Returns:
            A list of Page objects, each representing a page from the document.
        """
        pass 