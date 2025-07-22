# Page Formatting Changes

## Summary

Updated the page formatting in the engine to provide much clearer page boundaries for the LLM. Instead of subtle `[PAGE BREAK X]` markers, the system now uses prominent, impossible-to-miss headers with clear visual separation.

## Changes Made

### Engine Update (`src/staccato/core/engine.py`)

**Before:**
```python
# Combine page content for the batch, inserting page break markers
page_contents = []
for page_num, content in page_content_map.items():
    page_contents.append(f"[PAGE BREAK {page_num}]\n{content}")

combined_page_content = "\n\n".join(page_contents)
```

**After:**
```python
# Combine page content for the batch, inserting clear page headers
page_contents = []
for page_num, content in page_content_map.items():
    page_header = f"THIS IS PAGE NUMBER {page_num}"
    separator_line = "=" * len(page_header)
    page_contents.append(f"{separator_line}\n{page_header}\n{separator_line}\n\n{content}")

combined_page_content = "\n\n\n".join(page_contents)
```

## Visual Comparison

### Old Format (Subtle)
```
[PAGE BREAK 1]
Introduction to safety procedures...

[PAGE BREAK 2]
Emergency procedures are outlined below...
```

### New Format (Clear and Prominent)
```
=====================
THIS IS PAGE NUMBER 1
=====================

Introduction to safety procedures...


=====================
THIS IS PAGE NUMBER 2
=====================

Emergency procedures are outlined below...
```

## Key Improvements

### 1. **Impossible to Miss Headers**
- Large, all-caps "THIS IS PAGE NUMBER X" text
- Surrounded by separator lines made of equals signs
- Consistent formatting regardless of page number length

### 2. **Clear Visual Separation**
- Triple newlines (`\n\n\n`) between pages
- Separator lines above and below each header
- Distinct visual blocks for each page

### 3. **Reduced LLM Confusion**
- No ambiguity about which page content belongs to
- Clear boundaries make it obvious where one page ends and another begins
- Helps prevent the LLM from returning invalid page numbers

### 4. **Consistent Formatting**
- Works for single-digit page numbers: `THIS IS PAGE NUMBER 5`
- Works for multi-digit page numbers: `THIS IS PAGE NUMBER 15`
- Separator lines automatically adjust to header length

## Example Output

When processing pages 5-7 in a batch, the LLM receives:

```
=====================
THIS IS PAGE NUMBER 5
=====================

Chapter 3: Advanced Techniques

This chapter covers advanced methods...


=====================
THIS IS PAGE NUMBER 6
=====================

The first technique involves statistical modeling...


=====================
THIS IS PAGE NUMBER 7
=====================

The second technique uses machine learning...
```

## Benefits

### 1. **Error Prevention**
- Dramatically reduces the likelihood of LLM returning invalid page numbers
- Makes it crystal clear which pages are available in the current batch
- Works synergistically with the page validation retry logic

### 2. **Improved LLM Performance**
- Clearer context helps the LLM make better chunking decisions
- Easier to identify which page events should reference
- Better understanding of document structure across pages

### 3. **Debugging and Monitoring**
- Much easier to see page boundaries when reviewing LLM inputs
- Clear visual structure makes it easier to trace issues
- Consistent formatting aids in log analysis

### 4. **Robustness**
- Reduces dependency on LLM's ability to parse subtle markers
- More resilient to different LLM models and their parsing capabilities
- Future-proof formatting that's unlikely to be misinterpreted

## Testing

Comprehensive tests verify:
- ✅ Correct header formatting for all page numbers
- ✅ Proper separator line generation
- ✅ Appropriate spacing between pages
- ✅ Content preservation and correct placement
- ✅ Consistent formatting across different scenarios

## Integration with Existing Features

This change works seamlessly with:
- **Page Validation Retry Logic**: Clearer page boundaries reduce validation errors
- **Batch Processing**: Each batch clearly shows which pages are included
- **Error Messages**: When validation fails, it's obvious which pages were valid
- **Logging**: Page boundaries are clearly visible in debug logs

## Backward Compatibility

This is an internal formatting change that doesn't affect:
- Public APIs or configuration options
- Existing chunk output format
- User-facing functionality
- Integration with other components

The change only affects the internal prompt formatting sent to the LLM, making it more robust and reliable.

## Performance Impact

- **Minimal overhead**: Slightly longer prompts due to headers and separators
- **Improved reliability**: Fewer retry attempts due to clearer formatting
- **Net positive**: Reduced errors outweigh the small increase in prompt length

## Future Considerations

This formatting approach provides a foundation for:
- Adding additional page metadata if needed
- Implementing page-specific instructions
- Enhanced debugging and monitoring capabilities
- Better integration with different LLM providers
