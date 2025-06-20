from pydantic import BaseModel, Field
from typing import List, Literal

# The set of events the LLM can identify.
# This can be expanded in the future (e.g., 'footnote', 'header').
EventType = Literal["STARTS", "ENDS", "CONTINUATION"]

# The set of structural levels the LLM can identify.
# This can also be expanded.
LevelType = Literal["section", "table", "list_item", "code_block", "paragraph"]

class Event(BaseModel):
    """
    Represents a single structural event identified by the LLM on a page.
    """
    event: EventType = Field(..., description="The type of event (e.g., STARTS, ENDS).")
    level: LevelType = Field(..., description="The semantic level of the element (e.g., 'section', 'table').")
    title: str | None = Field(None, description="The title of the element, if applicable (e.g., for a new section).")

class LLMResponse(BaseModel):
    """
    A Pydantic model to validate the overall structure of the LLM's JSON output.
    This ensures the response is well-formed before any processing occurs.
    """
    events: List[Event] 