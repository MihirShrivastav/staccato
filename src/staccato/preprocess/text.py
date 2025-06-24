from ..preprocess.base import PreProcessor, Page, Block
from typing import List
from ..config import PreprocessingConfig
import unicodedata

class TextPreProcessor(PreProcessor):
    """
    A pre-processor for plain text (.txt) files.
    """
    def __init__(self, config: PreprocessingConfig):
        super().__init__(config)

    def extract_pages(self, file_path: str) -> List[Page]:
        """
        Reads a .txt file and treats the entire content as a single page.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            normalized_text = unicodedata.normalize("NFKC", content)
        except Exception as e:
            # Fallback for encoding errors
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
            normalized_text = unicodedata.normalize("NFKC", content)
        
        page = Page(
            page_number=1,
            text=normalized_text,
            blocks=[
                Block(
                    text=normalized_text,
                    bbox=(0, 0, 0, 0),
                    font_size=0,
                    font_weight="normal"
                )
            ]
        )
        return [page] 