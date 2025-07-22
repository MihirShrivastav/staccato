from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class PageNumberValidationError(Exception):
    """Raised when LLM response contains invalid page numbers."""
    def __init__(self, message: str, invalid_pages: List[int], valid_range: tuple[int, int]):
        super().__init__(message)
        self.invalid_pages = invalid_pages
        self.valid_range = valid_range

class FingerprintValidationError(Exception):
    """Raised when LLM response contains fingerprints that cannot be found in the page content."""
    def __init__(self, message: str, missing_fingerprints: List[dict], page_number: int):
        super().__init__(message)
        self.missing_fingerprints = missing_fingerprints  # List of {"fingerprint": str, "event": Event}
        self.page_number = page_number

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

def validate_fingerprints(llm_response: LLMResponse, page_content_map: dict[int, str]) -> None:
    """
    Validates that all fingerprints in the LLM response can be found in their respective page content.

    Args:
        llm_response: The LLM response containing events
        page_content_map: Dictionary mapping page numbers to their content

    Raises:
        FingerprintValidationError: If any fingerprints cannot be found
    """
    missing_fingerprints = []

    for event in llm_response.events:
        # Skip events that don't need fingerprints
        if event.event == "CONTINUATION" or not event.fingerprint:
            continue

        page_content = page_content_map.get(event.page_number, "")
        if not page_content:
            continue

        # Try to find the fingerprint in the page content
        fingerprint = event.fingerprint.strip()
        if not fingerprint:
            continue

        # First try exact match
        if fingerprint in page_content:
            continue

        # Try with whitespace normalization
        found = False
        lines = page_content.split('\n')
        for line in lines:
            if fingerprint in line.strip():
                found = True
                break

        if not found:
            missing_fingerprints.append({
                "fingerprint": event.fingerprint,
                "event": event,
                "page_number": event.page_number
            })

    if missing_fingerprints:
        # Group by page for clearer error messages
        pages_with_errors = {}
        for item in missing_fingerprints:
            page_num = item["page_number"]
            if page_num not in pages_with_errors:
                pages_with_errors[page_num] = []
            pages_with_errors[page_num].append(item["fingerprint"])

        error_details = []
        for page_num, fingerprints in pages_with_errors.items():
            error_details.append(f"Page {page_num}: {fingerprints}")

        message = f"Fingerprints not found in page content: {'; '.join(error_details)}"

        # Use the first page with errors for the exception
        first_page = min(pages_with_errors.keys())
        raise FingerprintValidationError(message, missing_fingerprints, first_page)