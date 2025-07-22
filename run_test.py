import asyncio
import logging
import os
from typing import List
from staccato import (
    ChunkingEngine,
    ChunkingEngineConfig,
    LLMConfig,
    PreprocessingConfig,
    Chunk,
    setup_logging,
    setup_llm_logging,
)

# --- Configuration ---
LOG_LEVEL = "DEBUG"
DOCUMENT_PATH = "testfile.pdf"
OUTPUT_DIR = "output"
LOG_FILE = os.path.join(OUTPUT_DIR, "run.log")
LLM_LOG_FILE = os.path.join(OUTPUT_DIR, "llm_outputs.log")
CHUNKS_FILE = os.path.join(OUTPUT_DIR, "chunks.md")

# --- Setup ---
# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging for the Staccato library, saving to a file.
setup_logging(LOG_LEVEL, file_path=LOG_FILE)

# Configure separate LLM logging to capture all LLM interactions
setup_llm_logging(LOG_LEVEL, file_path=LLM_LOG_FILE)


def save_chunks_to_markdown(chunks: List[Chunk], file_path: str):
    """Saves the list of chunks to a markdown file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Staccato Chunking Results for: {DOCUMENT_PATH}\n\n")
        f.write(f"Total chunks generated: {len(chunks)}\n\n")
        
        for i, chunk in enumerate(chunks):
            f.write("---\n\n")
            f.write(f"## Chunk {i+1}: {chunk.metadata.title or 'Untitled'}\n\n")
            f.write(f"**Level:** `{chunk.metadata.level}`\n")
            f.write(f"**Pages:** `{chunk.metadata.pages}`\n")
            f.write(f"**Parent Hierarchy:** `{' -> '.join(chunk.metadata.parent_hierarchy) or 'None'}`\n\n")
            f.write("### Text Content\n")
            f.write("```\n")
            f.write(chunk.text.strip() + "\n")
            f.write("```\n\n")
    logging.info(f"Successfully saved {len(chunks)} chunks to {file_path}")


async def main():
    """The main entry point for the test script."""
    logging.info("--- Initializing Staccato Chunking Engine ---")
    
    # --- Programmatic Configuration ---
    # This is the standard way to configure the Staccato library.
    # Create a config object and modify its parameters.
    logging.info("Creating custom configuration.")
    config = ChunkingEngineConfig(
        preprocessing=PreprocessingConfig(
            use_layout_analysis=False,
            page_batch_size=2,
            pdf_processor="pymupdf4llm",

        ),
        llm=LLMConfig(
            provider="google", 
            model_name="gemini-2.5-flash",
            temperature="0.7",
            reasoning_effort="low"
        ) 
        
    )
    logging.info(f"Layout analysis disabled via programmatic config.")

    # Pass the config object to the engine.
    engine = ChunkingEngine(config=config)
    
    logging.info(f"--- Processing Document: {DOCUMENT_PATH} ---")
    
    try:
        chunks = await engine.aprocess_document(DOCUMENT_PATH)
        
        if chunks:
            save_chunks_to_markdown(chunks, CHUNKS_FILE)
        else:
            logging.warning("No chunks were generated from the document.")

    except FileNotFoundError:
        logging.error(f"Error: The file was not found at '{DOCUMENT_PATH}'. Please ensure it is in the project root.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
    print(f"\n--- Test run complete. ---")
    print(f"Main logs have been saved to: {LOG_FILE}")
    print(f"LLM interaction logs have been saved to: {LLM_LOG_FILE}")
    print(f"Chunk output has been saved to: {CHUNKS_FILE}") 