from pydantic import BaseModel, Field
from typing import List, Optional

class Metadata(BaseModel):
    """
    Rich metadata associated with a single chunk.
    """
    title: Optional[str] = Field(None, description="The title of the section or element.")
    level: str = Field(..., description="The semantic level of the chunk (e.g., 'section', 'table').")
    source_document: str = Field(..., description="The name of the source document.")
    pages: List[int] = Field(..., description="A list of page numbers the chunk spans.")
    parent_hierarchy: List[str] = Field(
        default_factory=list,
        description="An ordered list of parent titles, from highest to lowest level."
    )

class Chunk(BaseModel):
    """
    The final, user-facing output object for a single semantic chunk.
    """
    text: str = Field(..., description="The clean text content of the chunk.")
    metadata: Metadata = Field(..., description="The rich metadata for the chunk.") 