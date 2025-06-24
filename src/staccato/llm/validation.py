from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# The set of events the LLM can identify.
# This can be expanded in the future (e.g., 'footnote', 'header').
EventType = Literal["STARTS", "ENDS", "CONTINUATION"]

# The set of structural levels the LLM can identify.
# This can also be expanded.
LevelType = Literal["section", "table", "list_item", "code_block", "paragraph"]

class Event(BaseModel):
    """
    Represents a single structural event identified by the LLM.
    """
    event: Literal["STARTS", "ENDS", "CONTINUATION"] = Field(
        ...,
        description="The type of event (e.g., STARTS, ENDS)."
    )
    level: str = Field(
        ...,
        description="The semantic level of the element (e.g., 'section', 'table')."
    )
    page_number: int = Field(
        ...,
        description="The 1-indexed page number where this event occurred."
    )
    title: Optional[str] = Field(
        None,
        description="The title of the element, if applicable (e.g., for a new section)."
    )
    fingerprint: Optional[str] = Field(
        None,
        description="A short, unique snippet of text that anchors the event's position on the page."
    )

class LLMResponse(BaseModel):
    """
    The root model for the entire JSON response from the LLM.
    """
    events: List[Event] 