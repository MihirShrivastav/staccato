"""
Staccato: An advanced, structure-aware chunking engine for RAG pipelines.
"""
from .core.engine import ChunkingEngine
from .config import ChunkingEngineConfig
from .models import Chunk, Metadata
from .utils.logging import setup_logging

__version__ = "0.1.0"

__all__ = [
    "ChunkingEngine",
    "ChunkingEngineConfig",
    "Chunk",
    "Metadata",
    "setup_logging",
] 