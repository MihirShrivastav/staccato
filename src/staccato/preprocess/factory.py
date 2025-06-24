import os
from .base import PreProcessor
from .docx import DocxPreProcessor
from .pdfplumber import PdfPlumberPreProcessor
from .pymupdf4llm import PyMuPdf4LlmPreProcessor
from .text import TextPreProcessor
from ..config import PreprocessingConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)

def get_preprocessor(file_path: str, config: PreprocessingConfig) -> PreProcessor:
    """
    Factory function to get the appropriate pre-processor for the given file type.
    """
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    logger.info("Getting pre-processor for file type", extension=extension)

    if extension == ".pdf":
        if config.pdf_processor == "pymupdf4llm":
            return PyMuPdf4LlmPreProcessor(config)
        else:
            return PdfPlumberPreProcessor(config)
    elif extension == ".docx":
        return DocxPreProcessor(config)
    elif extension == ".txt":
        return TextPreProcessor(config)
    else:
        logger.warning(
            "No specific pre-processor for file type, falling back to TextPreProcessor.",
            extension=extension
        )
        return TextPreProcessor(config) 