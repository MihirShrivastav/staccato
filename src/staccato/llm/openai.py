import importlib.util
import os
from ..llm.base import LLMAdapter, TokenUsage
from ..config import LLMConfig
from ..config import RetryConfig
from .response_schema import get_response_format

# A helper to provide a better error message if the required libraries are not installed.
def _check_openai_dependencies():
    if importlib.util.find_spec("openai") is None or importlib.util.find_spec("tiktoken") is None:
        raise ImportError(
            "The 'openai' and 'tiktoken' libraries are required for this adapter. "
            "Please install them with: pip install \"staccato[openai]\""
        )

class OpenAIAdapter(LLMAdapter):
    """
    An adapter for interacting with OpenAI-compatible APIs.
    It supports OpenAI, Google (via OpenAI-compatible endpoint), and LM Studio.
    Supports both synchronous and asynchronous generation.
    """
    def __init__(self, config: LLMConfig, retry_config: RetryConfig = None):
        super().__init__(retry_config)
        _check_openai_dependencies()
        from openai import OpenAI, AsyncOpenAI
        import tiktoken

        self.config = config

        # Determine API key environment variable and get API key
        api_key_env_var = self._get_api_key_env_var()
        api_key = os.getenv(api_key_env_var)

        # For LM Studio, use default API key if not provided in environment
        if not api_key and self.config.provider == "lmstudio":
            api_key = "lm-studio"
        elif not api_key:
            raise ValueError(f"API key not found in environment variable: {api_key_env_var}")

        # Determine base URL
        base_url = self._get_base_url()

        # Initialize clients
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.config.model_name)
        except KeyError:
            # Fallback to a default tokenizer if model not found
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _get_api_key_env_var(self) -> str:
        """Get the appropriate API key environment variable name."""
        if self.config.api_key_env_var:
            return self.config.api_key_env_var

        # Provider-specific defaults
        if self.config.provider == "google":
            return "GOOGLE_API_KEY"
        elif self.config.provider == "lmstudio":
            return "LMSTUDIO_API_KEY"
        else:  # openai
            return "OPENAI_API_KEY"

    def _get_base_url(self) -> str | None:
        """Get the appropriate base URL for the provider."""
        if self.config.base_url:
            return self.config.base_url

        # Provider-specific defaults
        if self.config.provider == "google":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif self.config.provider == "lmstudio":
            return "http://localhost:1234/v1"
        else:  # openai
            return None  # Use OpenAI's default

    def _get_response_format(self) -> dict:
        """Get the appropriate response format for the current provider."""
        return get_response_format(self.config.provider)

    def _extract_token_usage(self, response) -> TokenUsage:
        """Extract token usage from OpenAI API response."""
        if hasattr(response, 'usage') and response.usage:
            return TokenUsage(
                input_tokens=getattr(response.usage, 'prompt_tokens', 0),
                output_tokens=getattr(response.usage, 'completion_tokens', 0),
                total_tokens=getattr(response.usage, 'total_tokens', 0)
            )
        else:
            # Fallback: estimate tokens if usage not available
            return TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)

    def generate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: str = None) -> tuple[str, TokenUsage]:
        """Generates a synchronous response from the OpenAI API."""
        # Build the request parameters
        request_params = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {'type': "json_object"}
        }

        # Add reasoning_effort if supported by the model and provider
        if reasoning_effort:
            request_params["reasoning_effort"] = reasoning_effort

        response = self.client.chat.completions.create(**request_params)

        # Extract token usage
        usage = self._extract_token_usage(response)

        return response.choices[0].message.content or "", usage

    async def agenerate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: str = None) -> tuple[str, TokenUsage]:
        """Generates an asynchronous response from the OpenAI API."""
        # Build the request parameters
        request_params = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {'type': "json_object"}
        }

        # Add reasoning_effort if supported by the model and provider
        if reasoning_effort:
            request_params["reasoning_effort"] = reasoning_effort

        response = await self.async_client.chat.completions.create(**request_params)

        # Extract token usage
        usage = self._extract_token_usage(response)

        return response.choices[0].message.content or "", usage

    def count_tokens(self, text: str) -> int:
        """Counts tokens using the model-specific tiktoken tokenizer."""
        return len(self.tokenizer.encode(text)) 