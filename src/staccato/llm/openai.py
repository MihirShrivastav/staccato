import importlib.util
import os
from ..llm.base import LLMAdapter
from ..config import LLMConfig

# A helper to provide a better error message if the required libraries are not installed.
def _check_openai_dependencies():
    if importlib.util.find_spec("openai") is None or importlib.util.find_spec("tiktoken") is None:
        raise ImportError(
            "The 'openai' and 'tiktoken' libraries are required for this adapter. "
            "Please install them with: pip install \"staccato[openai]\""
        )

class OpenAIAdapter(LLMAdapter):
    """
    An adapter for interacting with OpenAI's language models.
    It supports both synchronous and asynchronous generation.
    """
    def __init__(self, config: LLMConfig):
        _check_openai_dependencies()
        from openai import OpenAI, AsyncOpenAI
        import tiktoken

        self.config = config
        # API key is read from the OPENAI_API_KEY environment variable by default
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            self.tokenizer = tiktoken.encoding_for_model(config.model_name)
        except KeyError:
            print(f"Warning: No tiktoken encoding found for model {config.model_name}. Defaulting to cl100k_base.")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

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