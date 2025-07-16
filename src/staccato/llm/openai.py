import importlib.util
import os
from ..llm.base import LLMAdapter
from ..config import LLMConfig
from ..config import RetryConfig

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
    It supports both OpenAI and Google (via OpenAI-compatible endpoint).
    Supports both synchronous and asynchronous generation.
    """
    def __init__(self, config: LLMConfig, retry_config: RetryConfig = None):
        super().__init__(retry_config)
        _check_openai_dependencies()
        from openai import OpenAI, AsyncOpenAI
        import tiktoken

        self.config = config

        # Determine API key environment variable
        api_key_env_var = self._get_api_key_env_var()
        api_key = os.getenv(api_key_env_var)

        if not api_key:
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
        else:  # openai
            return "OPENAI_API_KEY"

    def _get_base_url(self) -> str | None:
        """Get the appropriate base URL for the provider."""
        if self.config.base_url:
            return self.config.base_url

        # Provider-specific defaults
        if self.config.provider == "google":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        else:  # openai
            return None  # Use OpenAI's default

    def generate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> str:
        """Generates a synchronous response from the OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    async def agenerate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> str:
        """Generates an asynchronous response from the OpenAI API."""
        response = await self.async_client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    def count_tokens(self, text: str) -> int:
        """Counts tokens using the model-specific tiktoken tokenizer."""
        return len(self.tokenizer.encode(text)) 