from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class PageNumberValidationError(Exception):
    """Raised when LLM response contains invalid page numbers."""
    def __init__(self, message: str, invalid_pages: List[int], valid_range: tuple[int, int]):
        super().__init__(message)
        self.invalid_pages = invalid_pages
        self.valid_range = valid_range

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

def validate_page_numbers(llm_response: LLMResponse, valid_page_numbers: List[int]) -> None:
    """
    Validates that all page numbers in the LLM response are within the valid range.

    Args:
        llm_response: The LLM response containing events
        valid_page_numbers: List of valid page numbers for the current batch

    Raises:
        PageNumberValidationError: If any page numbers are invalid
    """
    if not valid_page_numbers:
        return

    min_page = min(valid_page_numbers)
    max_page = max(valid_page_numbers)
    valid_page_set = set(valid_page_numbers)

    invalid_pages = []
    for event in llm_response.events:
        if event.page_number not in valid_page_set:
            invalid_pages.append(event.page_number)

    if invalid_pages:
        invalid_pages = sorted(list(set(invalid_pages)))  # Remove duplicates and sort
        message = (
            f"LLM response contains invalid page numbers: {invalid_pages}. "
            f"Valid page range is {min_page}-{max_page}."
        )
        raise PageNumberValidationError(message, invalid_pages, (min_page, max_page))