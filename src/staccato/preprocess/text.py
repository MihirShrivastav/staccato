from ..preprocess.base import PreProcessor, Page, Block
from typing import List

class TextPreProcessor(PreProcessor):
    """
    A pre-processor for plain text (.txt) files.
    """
    def extract_pages(self, document_path: str) -> List[Page]:
        """
        Extracts content from a .txt file. The entire document is treated
        as a single 'page', and each line is treated as a 'block'.
        """
        blocks: List[Block] = []
        lines: List[str] = []
        
        with open(document_path, "r", encoding="utf-8") as f:
            for line in f:
                line_text = line.strip()
                if line_text:
                    lines.append(line_text)
                    # Use placeholder values for layout attributes
                    blocks.append(Block(
                        text=line_text,
                        bbox=(0, 0, 0, 0),
                        font_size=12,
                        font_weight="normal",
                    ))

        # The entire document is treated as one page
        page = Page(
            page_number=1,
            text="\n".join(lines),
            blocks=blocks,
        )

        return [page] 