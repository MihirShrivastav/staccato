from abc import ABC, abstractmethod
import json
from .validation import LLMResponse

class LLMAdapter(ABC):
    """
    Abstract Base Class for all LLM provider adapters.
    This defines the standard interface for interacting with different LLMs,
    supporting both synchronous and asynchronous operations.
    """

    # --- Synchronous Methods ---

    def generate_and_validate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> LLMResponse:
        """
        Generates a response and validates it against the expected Pydantic model.
        This is the primary method that should be used by the engine.
        """
        raw_response = self.generate(system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature)
        try:
            # The core validation step
            validated_response = LLMResponse.model_validate_json(raw_response)
            return validated_response
        except Exception as e:
            # Here we would add robust logging of the validation error and raw response
            print(f"LLM response validation failed: {e}")
            raise

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> str:
        """
        Generates a raw string response from the LLM.
        This should typically be called by the `generate_and_validate` method.

        Args:
            system_prompt: The system prompt to send to the LLM.
            user_prompt: The user prompt to send to the LLM.
            max_tokens: The maximum number of tokens to generate.
            temperature: The sampling temperature for generation.

        Returns:
            The raw string response from the LLM.
        """
        pass

    # --- Asynchronous Methods ---

    async def agenerate_and_validate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> LLMResponse:
        """
        Asynchronously generates a response and validates it.
        """
        raw_response = await self.agenerate(system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature)
        try:
            validated_response = LLMResponse.model_validate_json(raw_response)
            return validated_response
        except Exception as e:
            print(f"Async LLM response validation failed: {e}")
            raise

    async def agenerate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> str:
        """
        Asynchronously generates a raw string response from the LLM.
        Subclasses should override this method for async support.
        """
        raise NotImplementedError("This adapter does not support asynchronous generation.")

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Counts the number of tokens in a given text string according to the
        model's tokenizer.

        Args:
            text: The text to be tokenized.

        Returns:
            The number of tokens.
        """
        pass 