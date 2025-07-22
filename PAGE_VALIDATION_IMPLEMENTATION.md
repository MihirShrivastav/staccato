# Page Number Validation and Retry Implementation

## Problem Statement

The original issue occurred when the LLM returned events with page numbers that were outside the valid range for the current batch being processed. This caused a `KeyError` in `stitcher.py` at line 32:

```python
self._process_page_events(page_num, events_by_page[page_num], page_contents[page_num])
```

When `page_num` was not in the `page_contents` dictionary, the application would crash.

## Solution Overview

I implemented a comprehensive page number validation and retry system that:

1. **Validates page numbers** before passing LLM responses to the stitcher
2. **Automatically retries** with corrective instructions when invalid page numbers are detected
3. **Provides clear error messages** to help the LLM understand the valid page range
4. **Is configurable** through the existing retry configuration system

## Implementation Details

### 1. New Exception Class (`src/staccato/llm/validation.py`)

```python
class PageNumberValidationError(Exception):
    """Raised when LLM response contains invalid page numbers."""
    def __init__(self, message: str, invalid_pages: List[int], valid_range: tuple[int, int]):
        super().__init__(message)
        self.invalid_pages = invalid_pages
        self.valid_range = valid_range
```

### 2. Validation Function (`src/staccato/llm/validation.py`)

```python
def validate_page_numbers(llm_response: LLMResponse, valid_page_numbers: List[int]) -> None:
    """
    Validates that all page numbers in the LLM response are within the valid range.
    
    Raises:
        PageNumberValidationError: If any page numbers are invalid
    """
```

This function:
- Checks each event's page number against the valid page list
- Collects all invalid page numbers
- Raises a detailed error with correction information

### 3. Engine Retry Logic (`src/staccato/core/engine.py`)

The main retry logic was added to the `aprocess_document` method:

```python
# Retry logic for page number validation
max_page_validation_retries = self.config.retry.page_validation_attempts
llm_response = None

for retry_attempt in range(max_page_validation_retries):
    try:
        llm_response = await self.llm_adapter.agenerate_and_validate(...)
        validate_page_numbers(llm_response, page_numbers)
        break  # Success, exit retry loop
        
    except PageNumberValidationError as e:
        if retry_attempt == max_page_validation_retries - 1:
            raise  # Final attempt failed
        
        # Add corrective instructions to the user prompt for retry
        correction_text = (
            f"\n\nIMPORTANT CORRECTION: Your previous response contained invalid page numbers: {e.invalid_pages}. "
            f"You must ONLY use page numbers {min_page} through {max_page} (inclusive). "
            f"Do not reference any page numbers outside this range."
        )
        user_prompt = user_prompt + correction_text
```

### 4. Configuration Option (`src/staccato/config/models.py`)

Added a new configuration parameter to control retry behavior:

```python
class RetryConfig(BaseSettings):
    page_validation_attempts: int = Field(
        default=3,
        description="The maximum number of times to retry when LLM returns invalid page numbers."
    )
```

## How It Works

1. **Normal Processing**: The engine processes document batches as usual
2. **LLM Call**: Makes the LLM call to analyze the batch
3. **Validation**: Validates that all returned page numbers are within the current batch range
4. **Success Path**: If validation passes, continues with normal processing
5. **Retry Path**: If validation fails:
   - Logs the validation error
   - Adds corrective instructions to the prompt
   - Retries the LLM call with the enhanced prompt
   - Repeats up to the configured maximum attempts
6. **Failure Path**: If max retries are exceeded, raises the validation error

## Benefits

1. **Automatic Recovery**: No more crashes due to invalid page numbers
2. **Self-Correcting**: The LLM learns from its mistakes through corrective instructions
3. **Configurable**: Users can adjust retry behavior based on their needs
4. **Preserves Existing Logic**: Original LLM retry logic for API failures remains unchanged
5. **Clear Logging**: Detailed logs help with debugging and monitoring

## Configuration Examples

### Default Configuration
```python
config = ChunkingEngineConfig()  # Uses default page_validation_attempts=3
```

### Custom Configuration
```python
config = ChunkingEngineConfig(
    retry=RetryConfig(
        page_validation_attempts=5,  # More retries for difficult documents
        attempts=3,                  # LLM API retries (unchanged)
        min_wait=1,
        max_wait=10
    )
)
```

### Conservative Configuration
```python
config = ChunkingEngineConfig(
    retry=RetryConfig(
        page_validation_attempts=1,  # Fail fast if LLM returns invalid pages
    )
)
```

## Testing

The implementation includes comprehensive tests:

- `test_page_validation.py`: Unit tests for the validation function
- `test_simple_validation.py`: Integration tests for various scenarios
- `demo_retry_logic.py`: Demonstration of the retry behavior

All tests pass and demonstrate the correct behavior for:
- Valid page numbers (should pass)
- Invalid page numbers (should retry with corrections)
- Max retries exceeded (should fail gracefully)
- Edge cases (empty events, out-of-range pages)

## Backward Compatibility

This implementation is fully backward compatible:
- Existing configurations continue to work
- No changes to the public API
- Original retry logic for LLM API failures is preserved
- Only adds new functionality without breaking existing behavior

## Error Messages

The system provides clear, actionable error messages:

```
LLM response contains invalid page numbers: [5, 10]. Valid page range is 1-3.
```

And generates helpful correction instructions:

```
IMPORTANT CORRECTION: Your previous response contained invalid page numbers: [5, 10]. 
You must ONLY use page numbers 1 through 3 (inclusive). 
Do not reference any page numbers outside this range.
```

This implementation should completely resolve the KeyError issues you were experiencing when the LLM returned invalid page numbers.
