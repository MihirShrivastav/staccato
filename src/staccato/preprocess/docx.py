from ..preprocess.base import PreProcessor, Page, Block
from typing import List
import importlib.util

class DocxPreProcessor(PreProcessor):
    """
    A pre-processor implementation that uses the `python-docx` library
    to extract content from .docx documents.
    """
    def __init__(self):
        if importlib.util.find_spec("docx") is None:
            raise ImportError(
                "The 'python-docx' library is required for this pre-processor. "
                "Please install it with: pip install \"staccato[docx]\""
            )
        import docx
        self.docx = docx

    def extract_pages(self, document_path: str) -> List[Page]:
        """
        Extracts content from a .docx file.
        Since .docx is a flowing format without fixed pages, the entire
        document is treated as a single 'page'.
        """
        doc = self.docx.Document(document_path)
        
        full_text: List[str] = []
        blocks: List[Block] = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
                
                # Treat each paragraph as a block
                # Bbox and font size are placeholders
                blocks.append(Block(
                    text=para.text,
                    bbox=(0, 0, 0, 0),
                    font_size=12,  # Assume default font size
                    font_weight="bold" if self._is_bold(para) else "normal",
                ))

        # The entire document is treated as one page
        page = Page(
            page_number=1,
            text="\n".join(full_text),
            blocks=blocks,
        )
        
        return [page]

    def _is_bold(self, paragraph) -> bool:
        """Helper to check if any run in a paragraph is bold."""
        for run in paragraph.runs:
            if run.bold:
                return True
        return False 