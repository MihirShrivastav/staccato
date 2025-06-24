from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel, Field
from ..config import PreprocessingConfig


class Block(BaseModel):
    """A block is a contiguous chunk of text on a page."""
    text: str
    bbox: tuple[float, float, float, float]  # (x0, top, x1, bottom)
    font_size: float
    font_weight: str


class Page(BaseModel):
    """Represents a single page in a document."""
    page_number: int
    text: str
    blocks: List[Block] = Field(default_factory=list)


class PreProcessor(ABC):
    """Abstract Base Class for all document pre-processors."""

    def __init__(self, config: PreprocessingConfig):
        self.config = config

    @abstractmethod
    def extract_pages(self, file_path: str) -> List[Page]:
        """
        Extracts content and layout information from a document.

        Args:
            file_path: The file path to the source document.

        Returns:
            A list of Page objects.
        """
        pass 