# ENDS Event Logic Changes

## Summary

Updated the ENDS event logic so that the fingerprint now contains the **last few words of the chunk being ended** rather than the first few words of the next chunk. This provides clearer semantic boundaries and makes it easier for the LLM to identify where chunks should end.

## Changes Made

### 1. Stitcher Logic Update (`src/staccato/core/stitcher.py`)

**Before:**
```python
elif current_event.event == "ENDS":
    self._handle_ends(current_event)
    # For ENDS events, the fingerprint marks the boundary, so don't include it
    last_index = current_index
```

**After:**
```python
elif current_event.event == "ENDS":
    # For ENDS events, the fingerprint contains the last few words of the chunk being ended
    # So we include text up to and including the fingerprint in the current chunk
    fingerprint_end_index = current_index + len(current_event.fingerprint)
    text_slice = page_content[last_index:fingerprint_end_index]
    if self.active_stack:
        self.active_stack[-1].text_content += text_slice
    
    self._handle_ends(current_event)
    # Set last_index to after the fingerprint for the next iteration
    last_index = fingerprint_end_index
```

**Key Changes:**
- Text slicing now includes the fingerprint in the ending chunk
- `last_index` is set to after the fingerprint (not at the beginning)
- Proper handling of text boundaries between chunks

### 2. Prompt Example Update (`src/staccato/internal/prompts.py`)

**Before:**
```json
{
  "events": [
    { "event": "ENDS", "level": "section", "page_number": 5, "fingerprint": "Safety Procedures Overview" },
    { "event": "STARTS", "level": "list", "title": "Emergency Shutdown Process", "page_number": 5, "fingerprint": "Safety Procedures Overview" }
  ]
}
```

**After:**
```json
{
  "events": [
    { "event": "ENDS", "level": "section", "page_number": 5, "fingerprint": "procedures are complete." },
    { "event": "STARTS", "level": "list", "title": "Emergency Shutdown Process", "page_number": 5, "fingerprint": "1. Turn off" }
  ]
}
```

**Key Changes:**
- ENDS fingerprint now shows the ending words of the section: "procedures are complete."
- STARTS fingerprint shows the beginning words of the new list: "1. Turn off"
- No more duplicate fingerprints between ENDS and STARTS events

### 3. Updated Comments

Updated comments in `_handle_ends` method to reflect the new logic:

**Before:**
```python
# The fingerprint of the ENDS event marks the end of the chunk's content.
# The text slice up to this point was already added.
```

**After:**
```python
# The fingerprint of the ENDS event contains the last few words of the chunk being ended.
# The text slice including the fingerprint was already added to the chunk.
```

## How It Works Now

### Text Slicing Logic

1. **STARTS Event:**
   - Add text from `last_index` to start of fingerprint to previous chunk
   - Create new chunk starting with the fingerprint
   - Set `last_index` to after the fingerprint

2. **ENDS Event:**
   - Add text from `last_index` to end of fingerprint to current chunk
   - Complete the current chunk
   - Set `last_index` to after the fingerprint

### Example Scenario

Given this text:
```
This is section content. Section ends here.

New list starts:
1. First item
2. Second item
```

With events:
```json
[
  { "event": "ENDS", "level": "section", "fingerprint": "Section ends here." },
  { "event": "STARTS", "level": "list", "title": "Items", "fingerprint": "1. First item" }
]
```

**Result:**
- **Section chunk:** "This is section content. Section ends here."
- **List chunk:** "1. First item\n2. Second item"

## Benefits

1. **Clearer Semantics:** The LLM can more easily identify where content naturally concludes
2. **Better Boundaries:** Chunks end at logical conclusion points rather than arbitrary split points
3. **Improved Accuracy:** Easier for the LLM to identify the actual ending words of content
4. **No Overlap:** Clear separation between where one chunk ends and another begins

## Testing

Comprehensive tests verify:
- ✅ ENDS events correctly include fingerprint in ending chunk
- ✅ Text boundaries are properly handled
- ✅ Works with pre-existing active chunks from previous pages
- ✅ Multiple ENDS/STARTS sequences work correctly
- ✅ No text is lost or duplicated between chunks

## Backward Compatibility

This change affects the internal logic but maintains the same external API. Existing configurations and usage patterns continue to work. The change only affects how the LLM should structure its responses, which is guided by the updated prompts.

## Migration Notes

If you have any custom prompts or LLM training that references the old ENDS logic, update them to reflect that:
- ENDS fingerprints should contain the **last few words** of the chunk being ended
- STARTS fingerprints should contain the **first few words** of the new chunk
- No need for duplicate fingerprints between consecutive ENDS/STARTS events
