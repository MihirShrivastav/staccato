"""
Pre-processing module for Staccato.

This module contains the logic for converting various document formats
into a standardized list of Page objects for the engine to consume.
"""
import os
from .base import PreProcessor, Page, Block
from .markup import convert_page_to_markdown
from ..config import PreprocessingConfig

def get_preprocessor(
    document_path: str,
    config: PreprocessingConfig
) -> PreProcessor:
    """
    Factory function to get the appropriate pre-processor for a document.

    Args:
        document_path: The path to the document.
        config: The pre-processing configuration.

    Returns:
        An instance of a PreProcessor subclass.
        
    Raises:
        ValueError: If the file type is unsupported.
    """
    _, ext = os.path.splitext(document_path)
    ext = ext.lower()

    if ext == ".pdf":
        parser_name = config.pdf_parser
        if parser_name == "pdfplumber":
            from .pdfplumber import PdfPlumberPreProcessor
            return PdfPlumberPreProcessor()
        # Add other PDF parsers here as they are implemented
        # elif parser_name == "pymupdf":
        #     from .pymupdf import PyMuPDFPreProcessor
        #     return PyMuPDFPreProcessor()
        else:
            raise ValueError(f"Unsupported PDF parser: {parser_name}")
    
    elif ext == ".docx":
        from .docx import DocxPreProcessor
        return DocxPreProcessor()
        
    elif ext == ".txt":
        from .text import TextPreProcessor
        return TextPreProcessor()
        
    else:
        raise ValueError(f"Unsupported file type: {ext}")

__all__ = ["get_preprocessor", "PreProcessor", "Page", "Block", "convert_page_to_markdown"] 