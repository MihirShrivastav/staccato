from ..preprocess.base import PreProcessor, Page, Block
from typing import List
import importlib.util
from ..config import PreprocessingConfig
import unicodedata

# Helper to check for bold font
def is_bold(fontname: str) -> bool:
    """Checks if a font name suggests a bold weight."""
    return "bold" in fontname.lower() or "black" in fontname.lower()

class PdfPlumberPreProcessor(PreProcessor):
    """
    A pre-processor implementation that uses the `pdfplumber` library
    to extract content from PDF documents.
    """
    def __init__(self, config: PreprocessingConfig):
        super().__init__(config)
        if importlib.util.find_spec("pdfplumber") is None:
            raise ImportError(
                "The 'pdfplumber' library is required for this pre-processor. "
                "Please install it with: pip install \"staccato[pdfplumber]\""
            )
        import pdfplumber
        self.pdfplumber = pdfplumber

    def extract_pages(self, document_path: str) -> List[Page]:
        pages: List[Page] = []
        with self.pdfplumber.open(document_path) as pdf:
            for i, page_obj in enumerate(pdf.pages):
                # Extract text and normalize it immediately.
                page_text = page_obj.extract_text(x_tolerance=2, y_tolerance=2) or ""
                normalized_text = unicodedata.normalize("NFKC", page_text)

                blocks: List[Block] = []

                # Extract words and treat them as fine-grained blocks
                words = page_obj.extract_words(
                    keep_blank_chars=False,
                    use_text_flow=True,
                    extra_attrs=["fontname", "size"],
                    x_tolerance=2,
                    y_tolerance=2
                )
                for word in words:
                    fontname = word.get("fontname", "unknown")
                    # Also normalize text within blocks for consistency.
                    normalized_block_text = unicodedata.normalize("NFKC", word["text"])
                    blocks.append(
                        Block(
                            text=normalized_block_text,
                            bbox=(word["x0"], word["top"], word["x1"], word["bottom"]),
                            font_size=word.get("size", 0),
                            font_weight="bold" if is_bold(fontname) else "normal",
                        )
                    )

                pages.append(
                    Page(
                        page_number=i + 1,
                        text=normalized_text,
                        blocks=blocks,
                    )
                )
        return pages 