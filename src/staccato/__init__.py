"""
Staccato: An advanced, structure-aware chunking engine for RAG pipelines.
"""
from .core.engine import ChunkingEngine
from .config import (
    ChunkingEngineConfig,
    LLMConfig,
    PreprocessingConfig,
    RetryConfig,
)
from .models import Chunk, Metadata
from .utils.logging import setup_logging, setup_llm_logging

__version__ = "0.1.0"

__all__ = [
    "ChunkingEngine",
    "ChunkingEngineConfig",
    "LLMConfig",
    "PreprocessingConfig",
    "RetryConfig",
    "Chunk",
    "Metadata",
    "setup_logging",
    "setup_llm_logging",
] 