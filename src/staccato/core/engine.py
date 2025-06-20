import os
from typing import List
from ..config import ChunkingEngineConfig
from ..llm import get_llm_adapter
from ..preprocess import get_preprocessor, convert_page_to_markdown
from .stitcher import StatefulStitcher
from .assembler import FinalAssembler
from ..models import Chunk
from ..utils.logging import get_logger
from ..internal.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = get_logger(__name__)

class ChunkingEngine:
    def __init__(self, config: ChunkingEngineConfig = None):
        self.config = config or ChunkingEngineConfig()
        self.llm_adapter = get_llm_adapter(self.config.llm)
        logger.info(f"ChunkingEngine initialized with LLM provider: {self.config.llm.provider}")

    def process_document(self, document_path: str) -> List[Chunk]:
        """Processes a single document and returns a list of semantic chunks."""
        logger.info("Processing document", path=document_path)
        
        preprocessor = get_preprocessor(document_path, self.config.preprocessing)
        pages = preprocessor.extract_pages(document_path)
        logger.info(f"Extracted {len(pages)} pages.")

        stitcher = StatefulStitcher()
        for i, page in enumerate(pages):
            page_content = convert_page_to_markdown(page) if self.config.preprocessing.use_layout_analysis else page.text
            
            user_prompt = self._construct_user_prompt(page_content, stitcher.active_stack)
            llm_response = self.llm_adapter.generate_and_validate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature
            )
            stitcher.process_page(llm_response, page_content, page_number=i + 1)
        
        completed_chunks = stitcher.finalize()
        
        assembler = FinalAssembler()
        doc_name = os.path.basename(document_path)
        final_chunks = assembler.assemble(completed_chunks, doc_name)

        logger.info(f"Successfully generated {len(final_chunks)} chunks.")
        return final_chunks

    async def aprocess_document(self, document_path: str) -> List[Chunk]:
        """Asynchronously processes a single document."""
        logger.info("Async processing document", path=document_path)

        preprocessor = get_preprocessor(document_path, self.config.preprocessing)
        pages = preprocessor.extract_pages(document_path)
        logger.info(f"Extracted {len(pages)} pages.")

        stitcher = StatefulStitcher()
        for i, page in enumerate(pages):
            page_content = convert_page_to_markdown(page) if self.config.preprocessing.use_layout_analysis else page.text
            
            user_prompt = self._construct_user_prompt(page_content, stitcher.active_stack)
            llm_response = await self.llm_adapter.agenerate_and_validate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature
            )
            stitcher.process_page(llm_response, page_content, page_number=i + 1)
            
        completed_chunks = stitcher.finalize()
        
        assembler = FinalAssembler()
        doc_name = os.path.basename(document_path)
        final_chunks = assembler.assemble(completed_chunks, doc_name)

        logger.info(f"Successfully generated {len(final_chunks)} async chunks.")
        return final_chunks

    def _construct_user_prompt(self, page_content: str, active_stack: List) -> str:
        """Constructs the user prompt to send to the LLM."""
        if active_stack:
            context = " ".join([f"Currently in a {chunk.level} titled '{chunk.title}'." for chunk in active_stack if chunk.title])
        else:
            context = "You are at the beginning of the document."
            
        return USER_PROMPT_TEMPLATE.format(context=context, page_content=page_content) 