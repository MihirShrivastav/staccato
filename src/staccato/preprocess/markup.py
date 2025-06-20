from typing import List
from collections import Counter
from .base import Page, Block

def convert_page_to_markdown(page: Page) -> str:
    """
    Converts a Page object with its layout information into a simplified
    Markdown representation to be fed to an LLM.

    This function uses heuristics based on font size and weight to identify
    headings and structure the content.

    Args:
        page: A Page object containing a list of Block objects.

    Returns:
        A string containing the Markdown representation of the page.
    """
    if not page.blocks:
        return page.text # Fallback to raw text if no blocks are available

    # 1. Calculate statistics to find the most common "body" text style
    font_sizes = [b.font_size for b in page.blocks if b.font_size > 0]
    if not font_sizes:
        return page.text # Fallback if no font info is present
    
    most_common_size = Counter(font_sizes).most_common(1)[0][0]
    
    # 2. Merge consecutive blocks with similar styling
    merged_blocks: List[Block] = []
    if page.blocks:
        current_block = page.blocks[0]
        for next_block in page.blocks[1:]:
            # Merge if font size and weight are the same
            if (next_block.font_size == current_block.font_size and
                next_block.font_weight == current_block.font_weight):
                current_block.text += " " + next_block.text
            else:
                merged_blocks.append(current_block)
                current_block = next_block
        merged_blocks.append(current_block)

    # 3. Generate Markdown from merged blocks
    markdown_lines: List[str] = []
    for block in merged_blocks:
        text = block.text.strip()
        if not text:
            continue

        # Simple heading heuristic
        is_heading = block.font_size > most_common_size * 1.15
        is_bold = block.font_weight == "bold"

        if is_heading and is_bold:
            # Larger headings get more '#'
            if block.font_size > most_common_size * 1.5:
                markdown_lines.append(f"# {text}")
            else:
                markdown_lines.append(f"## {text}")
        elif is_bold:
            # Bold text that isn't a heading
            markdown_lines.append(f"**{text}**")
        else:
            # Regular paragraph text
            markdown_lines.append(text)
            
    return "\n\n".join(markdown_lines) 