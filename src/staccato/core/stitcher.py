from typing import List
from ..llm.validation import Event, LLMResponse
from ..internal.models import ActiveChunk, CompletedChunk
from ..utils.logging import get_logger

logger = get_logger(__name__)

class StatefulStitcher:
    """
    The heart of the chunking engine. This class maintains a stack of
    active elements (e.g., sections, tables) and processes document events
    to build chunks statefully across pages.
    """
    def __init__(self):
        self.active_stack: List[ActiveChunk] = []
        self.completed_chunks: List[CompletedChunk] = []
        logger.info("StatefulStitcher initialized.")

    def process_page(self, llm_response: LLMResponse, page_content: str, page_number: int):
        """Processes the events for a single page."""
        logger.info(
            "Processing page",
            page_number=page_number,
            event_count=len(llm_response.events)
        )
        
        # This is a simplification. A real implementation would need to correlate
        # page content fragments with the events that describe them.
        current_content_ptr = 0
        for event in llm_response.events:
            # For now, we'll assign the whole page content to any event that needs it.
            # This is a key area for future refinement.
            content_for_event = page_content 

            if event.event == "STARTS":
                self._handle_starts(event, page_number)
            elif event.event == "ENDS":
                self._handle_ends(event, page_number, content_for_event)
            elif event.event == "CONTINUATION":
                self._handle_continuation(content_for_event)
        
    def _handle_starts(self, event: Event, page_number: int):
        """Handles a STARTS event by pushing a new active chunk onto the stack."""
        parent_hierarchy = [chunk.title for chunk in self.active_stack if chunk.title]
        
        new_chunk = ActiveChunk(
            level=event.level,
            title=event.title,
            start_page=page_number,
            parent_hierarchy=parent_hierarchy
        )
        self.active_stack.append(new_chunk)
        logger.debug("Started new chunk", level=event.level, title=event.title)

    def _handle_ends(self, event: Event, page_number: int, content: str):
        """Handles an ENDS event by finalizing a chunk and moving it to completed."""
        if not self.active_stack or self.active_stack[-1].level != event.level:
            logger.warning("Received ENDS event for non-active level", expected=self.active_stack[-1].level if self.active_stack else "None", received=event.level)
            return

        active_chunk = self.active_stack.pop()
        active_chunk.text_content += content + "\n"
        
        completed = CompletedChunk(
            **active_chunk.model_dump(),
            end_page=page_number
        )
        self.completed_chunks.append(completed)
        logger.debug("Completed chunk", level=completed.level, title=completed.title)

    def _handle_continuation(self, page_content: str):
        """Handles a CONTINUATION event by appending content to the active chunk."""
        if not self.active_stack:
            logger.warning("Received CONTINUATION event with no active chunk.")
            return
        
        self.active_stack[-1].text_content += page_content + "\n"
        logger.debug("Continued chunk", level=self.active_stack[-1].level)

    def finalize(self) -> List[CompletedChunk]:
        """Finalizes any remaining open chunks on the stack."""
        if not self.completed_chunks and not self.active_stack:
            return []
            
        while self.active_stack:
            last_page = self.completed_chunks[-1].end_page if self.completed_chunks else 1
            active_chunk = self.active_stack.pop()
            completed = CompletedChunk(
                **active_chunk.model_dump(),
                end_page=last_page
            )
            self.completed_chunks.append(completed)
            logger.warning("Force-finalized open chunk", level=completed.level)
        return self.completed_chunks 