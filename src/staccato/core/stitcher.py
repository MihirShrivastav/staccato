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

        # --- 1. Separate CONTINUATION events from events that need fingerprint location ---
        continuation_events = []
        location_events = []

        for event in events:
            if event.event == "CONTINUATION":
                # CONTINUATION events don't need fingerprint location - they just indicate
                # that the current active chunk continues across this page
                continuation_events.append(event)
                logger.debug("\nCONTINUATION event", level=event.level, page=page_num)
            else:
                location_events.append(event)

        # --- 2. Locate and sort fingerprints for STARTS/ENDS events ---
        located_events = []
        for event in location_events:
            # The LLM can sometimes return placeholder events with no content.
            if not event.fingerprint:
                logger.warning("\n⚠️ Event missing fingerprint, skipping.", event_data=event.model_dump_json())
                continue

            try:
                # Strip whitespace from fingerprint for more robust matching
                stripped_fingerprint = event.fingerprint.strip()
                if not stripped_fingerprint:
                    logger.warning("\n⚠️ Empty fingerprint after stripping, skipping.", event_data=event.model_dump_json())
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

        # --- 3. Process CONTINUATION events (they don't affect text slicing) ---
        for event in continuation_events:
            # CONTINUATION events just indicate that the active chunk continues
            # No text slicing or state changes needed
            pass

        # --- 4. Process located events sequentially, slicing text between fingerprints ---
        last_index = 0
        for i, located in enumerate(located_events):
            current_event = located["event"]
            current_index = located["index"]

            # Now, process the current event
            if current_event.event == "STARTS":
                # For STARTS events, add text up to the fingerprint to the previous chunk
                text_slice = page_content[last_index:current_index]
                if self.active_stack:
                    self.active_stack[-1].text_content += text_slice

                self._handle_starts(current_event)
                # For STARTS events, update last_index to point AFTER the fingerprint
                # to avoid including the fingerprint text twice
                last_index = current_index + len(current_event.fingerprint)
            elif current_event.event == "ENDS":
                # For ENDS events, the fingerprint contains the last few words of the chunk being ended
                # So we include text up to and including the fingerprint in the current chunk
                fingerprint_end_index = current_index + len(current_event.fingerprint)
                text_slice = page_content[last_index:fingerprint_end_index]
                if self.active_stack:
                    self.active_stack[-1].text_content += text_slice

                # Check for gap between this ENDS and the next STARTS event
                self._check_and_fix_gap_after_ends(i, located_events, page_content, fingerprint_end_index, page_num)

                self._handle_ends(current_event)
                # Set last_index to after the fingerprint for the next iteration
                last_index = fingerprint_end_index

        # --- 5. Add the remaining text on the page to the currently active chunk ---
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
        logger.debug("\n🆕 Started chunk", level=event.level, title=event.title, page=event.page_number)

    def _handle_ends(self, event: Event):
        """Handles an ENDS event by finalizing a chunk and moving it to completed."""
        if not self.active_stack:
            logger.warning("Received ENDS event with no active chunk.", event_data=event.model_dump_json())
            return

        # The fingerprint of the ENDS event contains the last few words of the chunk being ended.
        # The text slice including the fingerprint was already added to the chunk.
        active_chunk = self.active_stack.pop()
        
        completed = CompletedChunk(
            **active_chunk.model_dump(),
            end_page=event.page_number
        )
        self.completed_chunks.append(completed)
        logger.debug("\n✅ Completed chunk", level=completed.level, title=completed.title, page=event.page_number)

    def _check_and_fix_gap_after_ends(self, current_index: int, located_events: list, page_content: str, ends_fingerprint_end: int, page_num: int):
        """
        Checks if there's a gap between an ENDS event and the next STARTS event,
        and adds any missing text to the most recently completed chunk.
        """
        # Look for the next STARTS event
        next_starts_event = None
        next_starts_index = None

        for j in range(current_index + 1, len(located_events)):
            next_event = located_events[j]
            if next_event["event"].event == "STARTS":
                next_starts_event = next_event["event"]
                next_starts_index = next_event["index"]
                break

        if next_starts_event and next_starts_index is not None:
            # Check if there's text between the end of ENDS fingerprint and start of STARTS fingerprint
            gap_text = page_content[ends_fingerprint_end:next_starts_index]

            # Only consider it a gap if there's meaningful content (not just whitespace)
            if gap_text.strip():
                logger.warning(
                    f"\n⚠️ Gap detected between ENDS and STARTS events on page {page_num}",
                    gap_text=repr(gap_text.strip()),
                    ends_event=self.active_stack[-1].title if self.active_stack else "Unknown",
                    starts_event=next_starts_event.title
                )

                # Add the gap text to the current active chunk (which will be completed by the ENDS event)
                if self.active_stack:
                    self.active_stack[-1].text_content += gap_text
                    logger.info(
                        f"✅ Added gap text to chunk '{self.active_stack[-1].title}': {repr(gap_text.strip())}"
                    )

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