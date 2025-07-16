from abc import ABC, abstractmethod
import json
from .validation import LLMResponse
from ..config import RetryConfig
from ..utils.logging import get_llm_logger
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from typing import Literal
from typing import Literal

class LLMAdapter(ABC):
    """
    Abstract Base Class for all LLM provider adapters.
    This defines the standard interface for interacting with different LLMs,
    supporting both synchronous and asynchronous operations.
    """
    def __init__(self, retry_config: RetryConfig = None):
        self.retry_config = retry_config or RetryConfig()
        self.llm_logger = get_llm_logger()
        
        # Configure the retry decorator dynamically
        self.retry_decorator = retry(
            stop=stop_after_attempt(self.retry_config.attempts),
            wait=wait_exponential(
                multiplier=self.retry_config.wait_multiplier,
                min=self.retry_config.min_wait,
                max=self.retry_config.max_wait
            )
        )
        
        # Configure the async retry decorator
        self.async_retry_decorator = retry(
            stop=stop_after_attempt(self.retry_config.attempts),
            wait=wait_exponential(
                multiplier=self.retry_config.wait_multiplier,
                min=self.retry_config.min_wait,
                max=self.retry_config.max_wait
            )
        )

    # --- Synchronous Methods ---

    def generate_and_validate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: Literal["low", "medium", "high", None] = None) -> LLMResponse:
        """
        Generates a response and validates it against the expected Pydantic model.
        This is the primary method that should be used by the engine.
        It includes retry logic.
        """
        try:
            # Log the input prompts
            self.llm_logger.info(
                f"LLM Input - System: {system_prompt[:200]}..." if len(system_prompt) > 200 else f"LLM Input - System: {system_prompt}"
            )
            self.llm_logger.info(
                f"LLM Input - User: {user_prompt[:500]}..." if len(user_prompt) > 500 else f"LLM Input - User: {user_prompt}"
            )
            self.llm_logger.info(f"LLM Parameters - max_tokens: {max_tokens}, temperature: {temperature}")
            
            decorated_generate = self.retry_decorator(self.generate)
            raw_response = decorated_generate(
                system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature
            )
            
            # Log the raw response
            self.llm_logger.info(f"LLM Raw Response: {raw_response}")
            
            validated_response = LLMResponse.model_validate_json(raw_response)
            
            # Log successful validation
            self.llm_logger.info(f"LLM Validation: SUCCESS - {len(validated_response.events)} events")
            
            return validated_response
        except RetryError as e:
            # The function failed after all retries.
            self.llm_logger.error(f"LLM call failed after multiple retries: {e}")
            print(f"LLM call failed after multiple retries: {e}")
            raise
        except Exception as e:
            # This could be a validation error or another unexpected issue.
            self.llm_logger.error(f"LLM response validation failed: {e}")
            print(f"LLM response validation failed: {e}")
            raise

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> str:
        """
        Generates a raw string response from the LLM.
        This should typically be called by the `generate_and_validate` method.
        Subclasses MUST implement this method.
        """
        pass

    # --- Asynchronous Methods ---

    async def agenerate_and_validate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> LLMResponse:
        """
        Asynchronously generates a response and validates it.
        It includes retry logic.
        """
        try:
            # Log the input prompts
            self.llm_logger.info(
                f"LLM Input (Async) - System: {system_prompt[:200]}..." if len(system_prompt) > 200 else f"LLM Input (Async) - System: {system_prompt}"
            )
            self.llm_logger.info(
                f"LLM Input (Async) - User: {user_prompt[:500]}..." if len(user_prompt) > 500 else f"LLM Input (Async) - User: {user_prompt}"
            )
            self.llm_logger.info(f"LLM Parameters (Async) - max_tokens: {max_tokens}, temperature: {temperature}")
            
            decorated_agenerate = self.async_retry_decorator(self.agenerate)
            raw_response = await decorated_agenerate(
                system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature
            )
            
            # Log the raw response
            self.llm_logger.info(f"LLM Raw Response (Async): {raw_response}")
            
            validated_response = LLMResponse.model_validate_json(raw_response)
            
            # Log successful validation
            self.llm_logger.info(f"LLM Validation (Async): SUCCESS - {len(validated_response.events)} events")
            
            return validated_response
        except RetryError as e:
            self.llm_logger.error(f"Async LLM call failed after multiple retries: {e}")
            print(f"Async LLM call failed after multiple retries: {e}")
            raise
        except Exception as e:
            self.llm_logger.error(f"Async LLM response validation failed: {e}")
            print(f"Async LLM response validation failed: {e}")
            raise
            
    @abstractmethod
    async def agenerate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> str:
        """
        Asynchronously generates a raw string response from the LLM.
        Subclasses should override this method for async support.
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Counts the number of tokens in a given text string according to the
        model's tokenizer.
        """
        pass 