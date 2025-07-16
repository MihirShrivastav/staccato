import os
import json
from typing import List
from ..config import ChunkingEngineConfig
from ..llm import get_llm_adapter
from ..preprocess.factory import get_preprocessor
from ..preprocess.markup import convert_page_to_markdown
from .stitcher import StatefulStitcher
from .assembler import FinalAssembler
from ..models import Chunk
from ..utils.logging import get_logger
from ..internal.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = get_logger(__name__)

class ChunkingEngine:
    def __init__(self, config: ChunkingEngineConfig = None):
        """
        Initializes the ChunkingEngine.

        Args:
            config: An optional ChunkingEngineConfig object. If not provided,
                    configuration is loaded automatically from 'staccato.toml'
                    and environment variables.
        """
        self.config = config or ChunkingEngineConfig()
        self.llm_adapter = get_llm_adapter(self.config)
        logger.info(f"ChunkingEngine initialized with LLM provider: {self.config.llm.provider}")
        logger.debug("Full configuration", config=self.config.model_dump())

    def process_document(self, document_path: str) -> List[Chunk]:
        """Processes a single document and returns a list of semantic chunks."""
        # This synchronous method is not the primary focus and is not implemented
        # with the full batching and async capabilities.
        # It remains for simple use cases or environments where async is not feasible.
        raise NotImplementedError("Please use the 'aprocess_document' method for full functionality.")

    async def aprocess_document(self, document_path: str) -> List[Chunk]:
        """Asynchronously processes a single document."""
        logger.info("Async processing document", path=document_path)

        preprocessor = get_preprocessor(document_path, self.config.preprocessing)
        pages = preprocessor.extract_pages(document_path)
        logger.info(f"Extracted {len(pages)} pages.")

        stitcher = StatefulStitcher()
        batch_size = self.config.preprocessing.page_batch_size

        for i in range(0, len(pages), batch_size):
            batch_pages = pages[i:i + batch_size]
            page_numbers = list(range(i + 1, i + len(batch_pages) + 1))
            logger.info(f"\n📄 Processing page batch {i//batch_size + 1}: pages {page_numbers[0]}-{page_numbers[-1]}")

            # Create a map of page number to page content for the stitcher
            page_content_map = {
                page_num: convert_page_to_markdown(p) if self.config.preprocessing.use_layout_analysis else p.text
                for page_num, p in zip(page_numbers, batch_pages)
            }

            # Combine page content for the batch, inserting page break markers
            page_contents = []
            for page_num, content in page_content_map.items():
                page_contents.append(f"[PAGE BREAK {page_num}]\n{content}")
            
            combined_page_content = "\n\n".join(page_contents)

            user_prompt = self._construct_user_prompt(combined_page_content, stitcher.active_stack, page_numbers)
            llm_response = await self.llm_adapter.agenerate_and_validate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature,
                reasoning_effort=self.config.llm.reasoning_effort
            )
            
            stitcher.process_events(llm_response, page_content_map)
            
        completed_chunks = stitcher.finalize()
        
        assembler = FinalAssembler()
        doc_name = os.path.basename(document_path)
        final_chunks = assembler.assemble(completed_chunks, doc_name)

        logger.info(f"Successfully generated {len(final_chunks)} async chunks.")

        # Log final token usage summary
        token_summary = self.llm_adapter.get_token_usage_summary()
        logger.info(f"Document processing complete. Token usage summary: {token_summary}")

        return final_chunks

    def _construct_user_prompt(self, page_content: str, active_stack: List, page_numbers: List[int]) -> str:
        """Constructs the user prompt to send to the LLM."""
        # Create page range string
        if len(page_numbers) == 1:
            page_range = f"Page {page_numbers[0]}"
        else:
            page_range = f"Pages {page_numbers[0]}-{page_numbers[-1]}"
        
        # Create JSON representation of active blocks
        if active_stack:
            active_blocks = []
            for chunk in active_stack:
                block_info = {
                    "level": chunk.level,
                    "title": chunk.title,
                    "start_page": chunk.start_page,
                    "parent_hierarchy": chunk.parent_hierarchy
                }
                active_blocks.append(block_info)
            active_blocks_json = json.dumps(active_blocks, indent=2)
        else:
            active_blocks_json = "[]"
            
        return USER_PROMPT_TEMPLATE.format(
            page_range=page_range,
            active_blocks_json=active_blocks_json,
            page_content=page_content
        ) 