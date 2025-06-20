from typing import List
from ..internal.models import CompletedChunk
from ..models import Chunk, Metadata

class FinalAssembler:
    """
    This component is responsible for taking the completed chunk data from
    the StatefulStitcher and transforming it into the final, clean,
    user-facing output format.
    """
    def assemble(
        self,
        completed_chunks: List[CompletedChunk],
        source_document_name: str
    ) -> List[Chunk]:
        """
        Assembles the final list of Chunk objects.

        Args:
            completed_chunks: The list of finalized chunks from the stitcher.
            source_document_name: The name of the original document.

        Returns:
            A list of user-facing Chunk objects.
        """
        final_chunks: List[Chunk] = []
        for completed in completed_chunks:
            # Consolidate page numbers
            pages = list(range(completed.start_page, completed.end_page + 1))

            metadata = Metadata(
                title=completed.title,
                level=completed.level,
                source_document=source_document_name,
                pages=pages,
                parent_hierarchy=completed.parent_hierarchy,
            )
            # Ensure text is not just whitespace before creating a chunk
            if completed.text_content.strip():
                chunk = Chunk(
                    text=completed.text_content.strip(),
                    metadata=metadata,
                )
                final_chunks.append(chunk)
            
        return final_chunks 