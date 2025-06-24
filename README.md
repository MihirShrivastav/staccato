# Staccato

**An advanced, robust, and fast Python library for semantic document chunking.**

Staccato is an advanced semantic chunking library designed for efficient and accurate document chunking.

---

## Key Features

*   **Layout-Aware Analysis:** Goes beyond plain text, interpreting layout cues (font size, spacing, etc.) from PDFs and DOCX files to create a richer structural representation.
*   **Event-Driven Chunking:** Uses an LLM to generate a stream of structural events (`STARTS`, `ENDS`, `CONTINUATION`), which are then processed by a stateful engine to robustly assemble chunks, even across page boundaries.
*   **Pluggable & Extensible:**
    *   Easily switch between different LLM providers (e.g., OpenAI, Anthropic).
    *   Supports multiple document formats (`.pdf`, `.docx`, `.txt`) with a modular pre-processing pipeline.
*   **Async First:** Built with `asyncio` to handle I/O-bound operations like LLM API calls efficiently.
*   **Stateful Stitching:** Correctly handles multi-page elements (like tables or lists) by maintaining state throughout the document processing lifecycle.
*   **Hierarchical Output:** Produces a structured list of `Chunk` objects, complete with parent-child relationships and rich metadata.

---

## How It Works

Staccato processes documents in a multi-stage pipeline:

1.  **Pre-process:** Extracts text and layout metadata from the source file (`.pdf`, `.docx`, etc.).
2.  **Markup Generation:** Converts the extracted data into a simplified, layout-aware markdown format.
3.  **LLM Analysis:** Sends the markdown to an LLM, which identifies and returns a JSON object of structural "events".
4.  **Stateful Stitching:** A `StatefulStitcher` processes the event stream, building up a list of internal chunk objects.
5.  **Final Assembly:** The internal objects are transformed into the final, clean `Chunk` objects provided to the user.

---

## Installation

```bash
# Coming soon! For now, install from source.
git clone https://github.com/MihirShrivastav/staccato.git
cd staccato
pip install -e .
```

---

## Basic Usage

```python
import asyncio
from staccato import ChunkingEngine

async def main():
    # Initialize the engine (configuration will be loaded from
    # environment variables or a config file)
    engine = ChunkingEngine()

    # Process a document
    chunks = await engine.aprocess_document("path/to/your/document.pdf")

    # Work with the results
    for chunk in chunks:
        print(f"Chunk ID: {chunk.id}, Parent: {chunk.parent_id}")
        print(f"Title: {chunk.title}")
        print("---")
        print(chunk.text)
        print("\n" + "="*20 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Project Status

This project is under active development. Our progress is tracked via the milestones defined in our [Project Plan](project_info/project_plan.md). 