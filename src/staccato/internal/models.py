from pydantic import BaseModel, Field
from typing import List
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class ActiveChunk(BaseModel):
    """
    Represents a semantic element that is currently being built.
    It might span multiple pages.
    """
    id: str = Field(default_factory=generate_uuid)
    level: str
    title: str | None = None
    text_content: str = ""
    start_page: int
    parent_hierarchy: List[str] = Field(default_factory=list)

class CompletedChunk(BaseModel):
    """
    Represents a finalized semantic element, ready for assembly.
    """
    id: str
    level: str
    title: str | None
    text_content: str
    start_page: int
    end_page: int
    parent_hierarchy: List[str] 