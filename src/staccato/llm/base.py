from abc import ABC, abstractmethod
import json
from .validation import LLMResponse
from ..config import RetryConfig
from ..utils.logging import get_llm_logger
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from typing import Literal, Dict, Any
from dataclasses import dataclass, field

@dataclass
class TokenUsage:
    """Tracks token usage for a single LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens

@dataclass
class CumulativeTokenUsage:
    """Tracks cumulative token usage across all LLM calls."""
    total_input_tokens: int = field(default=0)
    total_output_tokens: int = field(default=0)
    total_tokens: int = field(default=0)
    call_count: int = field(default=0)

    def add_usage(self, usage: TokenUsage):
        """Add token usage from a single call."""
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_tokens += usage.total_tokens
        self.call_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of token usage."""
        avg_input = self.total_input_tokens / self.call_count if self.call_count > 0 else 0
        avg_output = self.total_output_tokens / self.call_count if self.call_count > 0 else 0
        avg_total = self.total_tokens / self.call_count if self.call_count > 0 else 0

        return {
            "total_calls": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "average_input_tokens": round(avg_input, 2),
            "average_output_tokens": round(avg_output, 2),
            "average_total_tokens": round(avg_total, 2)
        }

class LLMAdapter(ABC):
    """
    Abstract Base Class for all LLM provider adapters.
    This defines the standard interface for interacting with different LLMs,
    supporting both synchronous and asynchronous operations.
    """
    def __init__(self, retry_config: RetryConfig = None):
        self.retry_config = retry_config or RetryConfig()
        self.llm_logger = get_llm_logger()

        # Initialize token usage tracking
        self.token_usage = CumulativeTokenUsage()

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

    # --- Token Usage Tracking Methods ---

    def _log_token_usage(self, usage: TokenUsage, call_type: str = ""):
        """Log token usage for a single call and update cumulative tracking."""
        self.token_usage.add_usage(usage)

        # Log individual call usage (more concise)
        self.llm_logger.info(
            f"Token Usage {call_type}- In: {usage.input_tokens}, Out: {usage.output_tokens}, Total: {usage.total_tokens}"
        )

        # Log cumulative usage (only every 5 calls to reduce clutter)
        summary = self.token_usage.get_summary()
        if summary['total_calls']:
            self.llm_logger.info(
                f"Cumulative Usage - {summary['total_calls']} calls, "
                f"Total: {summary['total_tokens']} tokens "
                f"(In: {summary['total_input_tokens']}, Out: {summary['total_output_tokens']})"
            )

    def get_token_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of cumulative token usage."""
        return self.token_usage.get_summary()

    def reset_token_usage(self):
        """Reset the cumulative token usage tracking."""
        self.token_usage = CumulativeTokenUsage()
        self.llm_logger.info("LLM token usage tracking reset")

    # --- Synchronous Methods ---

    def generate_and_validate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: Literal["low", "medium", "high", None] = None) -> LLMResponse:
        """
        Generates a response and validates it against the expected Pydantic model.
        This is the primary method that should be used by the engine.
        It includes retry logic.
        """
        try:
            # Log the input prompts (more concise)
            self.llm_logger.info(f"\nLLM Request (Sync)")
            self.llm_logger.info(f"System prompt: {len(system_prompt)} chars")
            self.llm_logger.info(f"User prompt: {len(user_prompt)} chars")
            self.llm_logger.info(f"LLM Parameters - max_tokens: {max_tokens}, temperature: {temperature}, reasoning_effort: {reasoning_effort}")

            decorated_generate = self.retry_decorator(self._generate_with_usage)
            raw_response, token_usage = decorated_generate(
                system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature, reasoning_effort=reasoning_effort
            )

            # Log token usage
            self._log_token_usage(token_usage, "(Sync) ")

            validated_response = LLMResponse.model_validate_json(raw_response)

            # Log successful validation
            self.llm_logger.info(f"Validation: SUCCESS - {len(validated_response.events)} events\n")
            
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

    def _generate_with_usage(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: Literal["low", "medium", "high", None] = None) -> tuple[str, TokenUsage]:
        """Wrapper that calls generate and extracts token usage."""
        response, usage = self.generate(system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature, reasoning_effort=reasoning_effort)
        return response, usage

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: Literal["low", "medium", "high", None] = None) -> tuple[str, TokenUsage]:
        """
        Generates a raw string response from the LLM and returns token usage.
        This should typically be called by the `generate_and_validate` method.
        Subclasses MUST implement this method.

        Returns:
            tuple: (response_text, token_usage)
        """
        pass

    # --- Asynchronous Methods --- 

    async def agenerate_and_validate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: Literal["low", "medium", "high", None] = None) -> LLMResponse:
        """
        Asynchronously generates a response and validates it.
        It includes retry logic.
        """
        try:
            # Log the input prompts (more concise)
            self.llm_logger.info(f"\n LLM Request (Async)")
            self.llm_logger.info(f" System prompt: {len(system_prompt)} chars")
            self.llm_logger.info(f" User prompt: {len(user_prompt)} chars")
            self.llm_logger.info(f"LLM Parameters (Async) - max_tokens: {max_tokens}, temperature: {temperature}, reasoning_effort: {reasoning_effort}")

            decorated_agenerate = self.async_retry_decorator(self._agenerate_with_usage)
            raw_response, token_usage = await decorated_agenerate(
                system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature, reasoning_effort=reasoning_effort
            )

            # Log token usage
            self._log_token_usage(token_usage, "(Async) ")

            validated_response = LLMResponse.model_validate_json(raw_response)

            # Log successful validation
            self.llm_logger.info(f" Validation: SUCCESS - {len(validated_response.events)} events\n")
            
            return validated_response
        except RetryError as e:
            self.llm_logger.error(f"Async LLM call failed after multiple retries: {e}")
            print(f"Async LLM call failed after multiple retries: {e}")
            raise
        except Exception as e:
            self.llm_logger.error(f"Async LLM response validation failed: {e}")
            print(f"Async LLM response validation failed: {e}")
            raise

    async def _agenerate_with_usage(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: Literal["low", "medium", "high", None] = None) -> tuple[str, TokenUsage]:
        """Wrapper that calls agenerate and extracts token usage."""
        response, usage = await self.agenerate(system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature, reasoning_effort=reasoning_effort)
        return response, usage

    @abstractmethod
    async def agenerate(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float, reasoning_effort: Literal["low", "medium", "high", None] = None) -> tuple[str, TokenUsage]:
        """
        Asynchronously generates a raw string response from the LLM and returns token usage.
        Subclasses should override this method for async support.

        Returns:
            tuple: (response_text, token_usage)
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Counts the number of tokens in a given text string according to the
        model's tokenizer.
        """
        pass 