"""
Pre-processing module for Staccato.

This module contains the logic for converting various document formats
into a standardized list of Page objects for the engine to consume.
"""
from .base import PreProcessor, Page, Block
from .factory import get_preprocessor

__all__ = [
    "get_preprocessor",
    "PreProcessor",
    "Page",
    "Block",
] 