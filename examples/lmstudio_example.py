#!/usr/bin/env python3
"""
LM Studio LLM Provider Example for Staccato

This example demonstrates how to use LM Studio as the LLM provider for Staccato.
LM Studio provides a local OpenAI-compatible API server for running LLMs locally.

Prerequisites:
1. Install and run LM Studio (https://lmstudio.ai/)
2. Load a model in LM Studio
3. Start the local server (usually on http://localhost:1234)
4. Install Staccato with OpenAI dependencies: pip install "staccato[openai]"

LM Studio Configuration:
- Base URL: http://localhost:1234/v1 (default)
- API Key: "lm-studio" (default, can be customized)
- Models: Any model loaded in LM Studio
"""

import os
import asyncio
from staccato import ChunkingEngine
from staccato.config import LLMConfig, ChunkingEngineConfig


def example_1_default_lmstudio_config():
    """Example 1: Using LM Studio with default configuration."""
    print("=== Example 1: Default LM Studio Configuration ===")
    
    # LM Studio uses a default API key, but you can set a custom one if needed
    # os.environ["LMSTUDIO_API_KEY"] = "lm-studio"  # This is the default
    
    # Create LLM config for LM Studio
    llm_config = LLMConfig(
        provider="lmstudio",
        model_name="llama-3.2-3b-instruct",  # Replace with your loaded model name
        temperature=0.7,
        max_tokens=8192,
        reasoning_effort="medium"  # Optional: may not affect local models
    )
    
    # Create the chunking engine configuration
    config = ChunkingEngineConfig(llm=llm_config)
    
    # Initialize the chunking engine
    engine = ChunkingEngine(config)
    
    print(f"LM Studio Engine initialized with model: {llm_config.model_name}")
    print(f"Base URL: http://localhost:1234/v1")
    print(f"API Key: lm-studio (default)")
    
    return engine


def example_2_custom_lmstudio_config():
    """Example 2: Using LM Studio with custom configuration."""
    print("=== Example 2: Custom LM Studio Configuration ===")
    
    # Set custom API key in environment (if you configured LM Studio with a custom key)
    os.environ["MY_LMSTUDIO_API_KEY"] = "my-custom-key"
    
    # Create LLM config with custom settings
    llm_config = LLMConfig(
        provider="lmstudio",
        model_name="mistral-7b-instruct",  # Replace with your model
        base_url="http://localhost:1234/v1",  # Custom port if different
        api_key_env_var="MY_LMSTUDIO_API_KEY",  # Custom env var name
        temperature=0.3,
        max_tokens=16384,
        reasoning_effort="high"  # Optional parameter
    )
    
    # Create the chunking engine configuration
    config = ChunkingEngineConfig(llm=llm_config)
    
    # Initialize the chunking engine
    engine = ChunkingEngine(config)
    
    print(f"Custom LM Studio Engine initialized")
    print(f"Model: {llm_config.model_name}")
    print(f"Base URL: {llm_config.base_url}")
    print(f"API Key Env Var: {llm_config.api_key_env_var}")
    
    return engine


async def example_3_async_chunking():
    """Example 3: Asynchronous document chunking with LM Studio."""
    print("=== Example 3: Async Chunking with LM Studio ===")
    
    # Configure for LM Studio
    llm_config = LLMConfig(
        provider="lmstudio",
        model_name="llama-3.2-3b-instruct",  # Replace with your model
        temperature=0.5,
        max_tokens=12288
    )
    
    config = ChunkingEngineConfig(llm=llm_config)
    engine = ChunkingEngine(config)
    
    # Example document path (replace with your actual document)
    document_path = "path/to/your/document.pdf"
    
    if os.path.exists(document_path):
        print(f"Processing document: {document_path}")
        
        # Process the document asynchronously
        chunks = await engine.achunk_document(document_path)
        
        print(f"Generated {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"\nChunk {i+1}:")
            print(f"Title: {chunk.title}")
            print(f"Content preview: {chunk.content[:200]}...")
    else:
        print(f"Document not found: {document_path}")
        print("Please provide a valid document path to test chunking.")


def example_4_comparison_providers():
    """Example 4: Comparing different provider configurations."""
    print("=== Example 4: Provider Comparison ===")
    
    # OpenAI configuration
    print("OpenAI Configuration:")
    openai_config = LLMConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7
    )
    print(f"  Provider: {openai_config.provider}")
    print(f"  Model: {openai_config.model_name}")
    print(f"  Base URL: {openai_config.base_url or 'Default OpenAI endpoint'}")
    print(f"  API Key Env Var: {openai_config.api_key_env_var or 'OPENAI_API_KEY'}")
    
    print("\nGoogle Configuration:")
    google_config = LLMConfig(
        provider="google",
        model_name="gemini-1.5-flash",
        temperature=0.7
    )
    print(f"  Provider: {google_config.provider}")
    print(f"  Model: {google_config.model_name}")
    print(f"  Base URL: https://generativelanguage.googleapis.com/v1beta/openai/")
    print(f"  API Key Env Var: GOOGLE_API_KEY")
    
    print("\nLM Studio Configuration:")
    lmstudio_config = LLMConfig(
        provider="lmstudio",
        model_name="llama-3.2-3b-instruct",
        temperature=0.7
    )
    print(f"  Provider: {lmstudio_config.provider}")
    print(f"  Model: {lmstudio_config.model_name}")
    print(f"  Base URL: http://localhost:1234/v1")
    print(f"  API Key: lm-studio (default)")


def main():
    """Run all examples."""
    print("LM Studio LLM Provider Examples for Staccato")
    print("=" * 50)
    
    try:
        # Example 1: Default configuration
        engine1 = example_1_default_lmstudio_config()
        print("\n" + "=" * 50 + "\n")
        
        # Example 2: Custom configuration
        engine2 = example_2_custom_lmstudio_config()
        print("\n" + "=" * 50 + "\n")
        
        # Example 3: Async chunking (commented out by default)
        # asyncio.run(example_3_async_chunking())
        # print("\n" + "=" * 50 + "\n")
        
        # Example 4: Provider comparison
        example_4_comparison_providers()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nTo test document chunking:")
        print("1. Make sure LM Studio is running with a model loaded")
        print("2. Uncomment the async example in main()")
        print("3. Provide a valid document path")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure LM Studio is running on http://localhost:1234")
        print("2. Ensure you have a model loaded in LM Studio")
        print("3. Check that the model name matches what's loaded in LM Studio")


if __name__ == "__main__":
    main()
