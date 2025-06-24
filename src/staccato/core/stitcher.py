from typing import List
from collections import defaultdict
from ..llm.validation import Event, LLMResponse
from ..internal.models import ActiveChunk, CompletedChunk
from ..utils.logging import get_logger

logger = get_logger(__name__)

class StatefulStitcher:
    """
    The heart of the chunking engine. This class maintains a stack of
    active elements (e.g., sections, tables) and processes document events
    to build chunks statefully across pages. It implements the "Index-Locator"
    pattern, where it uses fingerprints from the LLM to precisely slice text.
    """
    def __init__(self):
        self.active_stack: List[ActiveChunk] = []
        self.completed_chunks: List[CompletedChunk] = []
        logger.info("StatefulStitcher initialized.")

    def process_events(self, llm_response: LLMResponse, page_contents: dict[int, str]):
        """
        Processes a list of events from the LLM, using fingerprints to
        precisely slice text from the page content.
        """
        events_by_page = defaultdict(list)
        for event in llm_response.events:
            events_by_page[event.page_number].append(event)

        sorted_pages = sorted(events_by_page.keys())
        for page_num in sorted_pages:
            self._process_page_events(page_num, events_by_page[page_num], page_contents[page_num])

    def _process_page_events(self, page_num: int, events: List[Event], page_content: str):
        """Processes all events for a single page."""
        
        # --- 1. Locate and sort all fingerprints on the page ---
        located_events = []
        for event in events:
            # The LLM can sometimes return placeholder events with no content.
            if not event.fingerprint:
                logger.warning("Event missing fingerprint, skipping.", event_data=event.model_dump_json())
                continue
            
            try:
                # Strip whitespace from fingerprint for more robust matching
                stripped_fingerprint = event.fingerprint.strip()
                if not stripped_fingerprint:
                    logger.warning("Empty fingerprint after stripping, skipping.", event_data=event.model_dump_json())
                    continue
                
                # First try exact match
                index = page_content.find(event.fingerprint)
                
                # If exact match fails, try with stripped versions
                if index == -1:
                    # Create a stripped version of page content and search in chunks
                    # to handle whitespace differences while preserving original positions
                    lines = page_content.split('\n')
                    current_pos = 0
                    found = False
                    
                    for line in lines:
                        stripped_line = line.strip()
                        if stripped_fingerprint in stripped_line:
                            # Find the position within the original line
                            line_start_in_content = current_pos
                            stripped_index_in_line = stripped_line.find(stripped_fingerprint)
                            
                            # Map back to original content position
                            # Count non-stripped characters before the match
                            original_index_in_line = 0
                            stripped_chars_counted = 0
                            for char in line:
                                if char.strip():  # Non-whitespace character
                                    if stripped_chars_counted == stripped_index_in_line:
                                        break
                                    stripped_chars_counted += 1
                                original_index_in_line += 1
                            
                            index = line_start_in_content + original_index_in_line
                            found = True
                            break
                        current_pos += len(line) + 1  # +1 for the newline character
                    
                    if not found:
                        logger.warning("Fingerprint not found on page (even with whitespace handling), skipping event.", 
                                     fingerprint=event.fingerprint, stripped=stripped_fingerprint, page=page_num)
                        continue
                
                located_events.append({"event": event, "index": index})
            except Exception as e:
                logger.error("Error finding fingerprint", fingerprint=event.fingerprint, page=page_num, error=e)
        
        # Sort events by their appearance on the page
        located_events.sort(key=lambda x: x["index"])

        # --- 2. Process events sequentially, slicing text between fingerprints ---
        last_index = 0
        for i, located in enumerate(located_events):
            current_event = located["event"]
            current_index = located["index"]

            # Determine the text slice for the *previous* state
            # The text for the previous active chunk ends where the current event's fingerprint begins.
            text_slice = page_content[last_index:current_index]
            if self.active_stack:
                self.active_stack[-1].text_content += text_slice

            # Now, process the current event
            if current_event.event == "STARTS":
                self._handle_starts(current_event)
                # For STARTS events, update last_index to point AFTER the fingerprint
                # to avoid including the fingerprint text twice
                last_index = current_index + len(current_event.fingerprint)
            elif current_event.event == "ENDS":
                self._handle_ends(current_event)
                # For ENDS events, the fingerprint marks the boundary, so don't include it
                last_index = current_index
            elif current_event.event == "CONTINUATION":
                # Continuation just means the active chunk continues, no state change.
                # The text was already added.
                last_index = current_index

        # Add the remaining text on the page to the currently active chunk
        if self.active_stack:
            self.active_stack[-1].text_content += page_content[last_index:]


    def _handle_starts(self, event: Event):
        """Handles a STARTS event by pushing a new active chunk onto the stack."""
        parent_hierarchy = [chunk.title for chunk in self.active_stack if chunk.title]
        
        new_chunk = ActiveChunk(
            level=event.level,
            title=event.title,
            start_page=event.page_number,
            parent_hierarchy=parent_hierarchy
        )
        # The content for this new chunk will start accumulating from this point.
        new_chunk.text_content = event.fingerprint
        self.active_stack.append(new_chunk)
        logger.debug("Started new chunk", level=event.level, title=event.title, page=event.page_number)

    def _handle_ends(self, event: Event):
        """Handles an ENDS event by finalizing a chunk and moving it to completed."""
        if not self.active_stack:
            logger.warning("Received ENDS event with no active chunk.", event_data=event.model_dump_json())
            return
        
        # The fingerprint of the ENDS event marks the end of the chunk's content.
        # The text slice up to this point was already added.
        active_chunk = self.active_stack.pop()
        
        completed = CompletedChunk(
            **active_chunk.model_dump(),
            end_page=event.page_number
        )
        self.completed_chunks.append(completed)
        logger.debug("Completed chunk", level=completed.level, title=completed.title, page=event.page_number)

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
            logger.warning("Force-finalized open chunk", level=completed.level, title=active_chunk.title)
        return self.completed_chunks 