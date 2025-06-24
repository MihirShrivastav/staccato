from ..preprocess.base import PreProcessor, Page, Block
from typing import List, Dict, Any
import importlib.util
from ..config import PreprocessingConfig
import unicodedata
import re

class PyMuPdf4LlmPreProcessor(PreProcessor):
    """
    A pre-processor implementation that uses the `pymupdf4llm` library
    to extract content from PDF documents with markdown formatting.
    
    This processor provides better structural understanding for LLMs by:
    - Preserving markdown formatting (tables, headers, lists)
    - Including metadata about tables, images, and graphics
    - Maintaining structural context across pages
    """
    
    def __init__(self, config: PreprocessingConfig):
        super().__init__(config)
        if importlib.util.find_spec("pymupdf4llm") is None:
            raise ImportError(
                "The 'pymupdf4llm' library is required for this pre-processor. "
                "Please install it with: pip install \"staccato[pymupdf4llm]\""
            )
        import pymupdf4llm
        self.pymupdf4llm = pymupdf4llm

    def extract_pages(self, document_path: str) -> List[Page]:
        """
        Extract pages from a PDF using pymupdf4llm with markdown formatting.
        
        Returns:
            List of Page objects with markdown-formatted text and structural metadata
        """
        pages: List[Page] = []
        
        # Extract markdown content with page chunks
        md_text = self.pymupdf4llm.to_markdown(document_path, page_chunks=True)
        
        for i, page_data in enumerate(md_text):
            # Normalize the markdown text
            normalized_text = unicodedata.normalize("NFKC", page_data["text"])
            
            # Create blocks from the markdown structure
            blocks = self._create_blocks_from_markdown(
                normalized_text, 
                page_data.get("metadata", {}),
                page_data.get("tables", []),
                page_data.get("images", []),
                page_data.get("graphics", [])
            )
            
            pages.append(
                Page(
                    page_number=i + 1,
                    text=normalized_text,
                    blocks=blocks,
                )
            )
        
        return pages
    
    def _create_blocks_from_markdown(
        self, 
        text: str, 
        metadata: Dict[str, Any],
        tables: List[Dict],
        images: List[Dict],
        graphics: List[Dict]
    ) -> List[Block]:
        """
        Create Block objects from markdown text and structural metadata.
        
        This method identifies different types of content (headers, tables, paragraphs)
        and creates appropriately weighted blocks.
        """
        blocks: List[Block] = []
        
        # Split text into lines for analysis
        lines = text.split('\n')
        y_position = 0.0
        line_height = 12.0  # Approximate line height
        
        for line_num, line in enumerate(lines):
            if not line.strip():
                y_position += line_height
                continue
                
            # Determine block properties based on markdown formatting
            font_size, font_weight = self._analyze_markdown_line(line)
            
            # Create bounding box (approximate, since we don't have exact coordinates)
            bbox = (
                0.0,  # x0
                y_position,  # top
                500.0,  # x1 (approximate page width)
                y_position + line_height  # bottom
            )
            
            blocks.append(
                Block(
                    text=unicodedata.normalize("NFKC", line),
                    bbox=bbox,
                    font_size=font_size,
                    font_weight=font_weight,
                )
            )
            
            y_position += line_height
        
        # Add special blocks for tables, images, and graphics metadata
        blocks.extend(self._create_metadata_blocks(tables, images, graphics, y_position))
        
        return blocks
    
    def _analyze_markdown_line(self, line: str) -> tuple[float, str]:
        """
        Analyze a markdown line to determine appropriate font size and weight.
        
        Returns:
            Tuple of (font_size, font_weight)
        """
        stripped = line.strip()
        
        # Headers
        if stripped.startswith('# '):
            return 18.0, "bold"
        elif stripped.startswith('## '):
            return 16.0, "bold"
        elif stripped.startswith('### '):
            return 14.0, "bold"
        elif stripped.startswith('#### '):
            return 13.0, "bold"
        elif stripped.startswith('##### '):
            return 12.0, "bold"
        elif stripped.startswith('###### '):
            return 11.0, "bold"
        
        # Table headers (lines with |---|---|)
        elif re.match(r'^\|[-\s\|]+\|$', stripped):
            return 10.0, "normal"
        
        # Table rows
        elif '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            return 10.0, "normal"
        
        # Bold text
        elif '**' in stripped:
            return 12.0, "bold"
        
        # List items
        elif re.match(r'^\s*[-*+]\s', stripped) or re.match(r'^\s*\d+\.\s', stripped):
            return 12.0, "normal"
        
        # Default paragraph text
        else:
            return 12.0, "normal"
    
    def _create_metadata_blocks(
        self, 
        tables: List[Dict],
        images: List[Dict],
        graphics: List[Dict],
        start_y: float
    ) -> List[Block]:
        """
        Create special metadata blocks for structural elements.
        
        These blocks provide additional context to the LLM about page structure.
        """
        metadata_blocks: List[Block] = []
        current_y = start_y + 20.0  # Offset from main content
        
        # Add table metadata blocks
        for table in tables:
            bbox = table.get('bbox', (0, 0, 500, 20))
            metadata_text = f"[TABLE: {table.get('rows', 0)} rows × {table.get('columns', 0)} columns]"
            
            metadata_blocks.append(
                Block(
                    text=metadata_text,
                    bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
                    font_size=10.0,
                    font_weight="normal",
                )
            )
        
        # Add image metadata blocks
        for image in images:
            bbox = image.get('bbox', (0, current_y, 500, current_y + 20))
            metadata_text = f"[IMAGE: {image.get('width', 0)}×{image.get('height', 0)}]"
            
            metadata_blocks.append(
                Block(
                    text=metadata_text,
                    bbox=bbox,
                    font_size=10.0,
                    font_weight="normal",
                )
            )
            current_y += 25.0
        
        # Add graphics metadata blocks
        for graphic in graphics:
            bbox = graphic.get('bbox', (0, current_y, 500, current_y + 20))
            metadata_text = f"[GRAPHIC: {graphic.get('type', 'unknown')}]"
            
            metadata_blocks.append(
                Block(
                    text=metadata_text,
                    bbox=bbox,
                    font_size=10.0,
                    font_weight="normal",
                )
            )
            current_y += 25.0
        
        return metadata_blocks 