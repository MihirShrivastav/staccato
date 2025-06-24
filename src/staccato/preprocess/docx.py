from ..preprocess.base import PreProcessor, Page, Block
from typing import List
import importlib.util
from ..config import PreprocessingConfig
import unicodedata

class DocxPreProcessor(PreProcessor):
    """
    A pre-processor implementation that uses the `python-docx` library
    to extract content from .docx documents.
    """
    def __init__(self, config: PreprocessingConfig):
        super().__init__(config)
        if importlib.util.find_spec("docx") is None:
            raise ImportError(
                "The 'python-docx' library is required for this pre-processor. "
                "Please install it with: pip install \"staccato[docx]\""
            )
        import docx
        self.docx = docx

    def extract_pages(self, file_path: str) -> List[Page]:
        """
        Extracts content from a .docx file.
        Since .docx is a flowing format without fixed pages, the entire
        document is treated as a single 'page'.
        """
        from docx import Document
        
        document = Document(file_path)
        
        # In DOCX, we treat the entire document as one "page" for simplicity.
        # A more advanced implementation could try to split by actual page breaks.
        full_text = "\n".join([para.text for para in document.paragraphs])
        normalized_text = unicodedata.normalize("NFKC", full_text)
        
        # Since we don't have page/block structure, we create one page with one block.
        page = Page(
            page_number=1,
            text=normalized_text,
            blocks=[
                Block(
                    text=normalized_text,
                    bbox=(0, 0, 0, 0),  # No bbox available
                    font_size=0,         # No font size available
                    font_weight="normal"
                )
            ]
        )
        return [page]

    def _is_bold(self, paragraph) -> bool:
        """Helper to check if any run in a paragraph is bold."""
        for run in paragraph.runs:
            if run.bold:
                return True
        return False 