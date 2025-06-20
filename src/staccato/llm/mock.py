import json
from ..llm.base import LLMAdapter

# A pre-defined, structured response to simulate the real LLM's output.
# This helps in developing and testing the downstream components (like the Stitcher)
# without making actual API calls.
MOCK_LLM_RESPONSE = {
    "events": [
        {"event": "STARTS", "level": "section", "title": "Chapter 1: Introduction"},
        {"event": "CONTINUATION", "level": "section"},
        {"event": "STARTS", "level": "table", "title": "Table 1-1: Key Metrics"},
        {"event": "CONTINUATION", "level": "table"},
        {"event": "ENDS", "level": "table"},
        {"event": "CONTINUATION", "level": "section"},
        {"event": "ENDS", "level": "section"}
    ]
}

class MockLLMAdapter(LLMAdapter):
    """
    A mock LLM adapter for testing and development.
    It returns a pre-defined, structured JSON response.
    """
    def generate(self, prompt: str, *, max_tokens: int, temperature: float) -> str:
        """
        Returns a mock JSON response, ignoring the prompt and other parameters.
        """
        return json.dumps(MOCK_LLM_RESPONSE)

    def count_tokens(self, text: str) -> int:
        """
        Provides a simple, approximate token count for testing purposes.
        A common rule of thumb is ~4 characters per token.
        """
        return len(text) // 4 