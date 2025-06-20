"""
LLM abstraction module for Staccato.

This module provides a standardized interface for interacting with various
Large Language Models and a factory to get the correct adapter based on config.
"""
from ..config import LLMConfig
from .base import LLMAdapter

def get_llm_adapter(config: LLMConfig) -> LLMAdapter:
    """
    Factory function to get the appropriate LLM adapter.

    Args:
        config: The LLM configuration.

    Returns:
        An instance of an LLMAdapter subclass.
    """
    provider = config.provider
    if provider == "mock":
        from .mock import MockLLMAdapter
        return MockLLMAdapter()
    elif provider == "openai":
        from .openai import OpenAIAdapter
        return OpenAIAdapter(config)
    # Add other providers here as they are implemented
    # elif provider == "anthropic":
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

__all__ = ["get_llm_adapter", "LLMAdapter"] 