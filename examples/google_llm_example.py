"""
Example demonstrating how to use Google's Gemini models with Staccato.

This example shows different ways to configure Google as the LLM provider:
1. Using default Google configuration
2. Using custom base URL and API key environment variable
3. Using environment variables and configuration files
"""

import os
from staccato import ChunkingEngine, LLMConfig, ChunkingEngineConfig


def example_1_default_google_config():
    """Example 1: Using Google with default configuration."""
    print("=== Example 1: Default Google Configuration ===")
    
    # Set the Google API key in environment
    # In practice, you'd set this in your shell or .env file
    os.environ["GOOGLE_API_KEY"] = "your-google-api-key-here"
    
    # Create LLM config for Google
    llm_config = LLMConfig(
        provider="google",
        model_name="gemini-1.5-flash",  # or "gemini-1.5-pro"
        temperature=0.7,
        max_tokens=8192
    )
    
    # Create chunking engine config
    config = ChunkingEngineConfig(llm=llm_config)
    
    # Initialize the chunking engine
    engine = ChunkingEngine(config)
    
    print(f"✓ Engine initialized with Google provider")
    print(f"  Model: {config.llm.model_name}")
    print(f"  Base URL: {config.llm.base_url or 'Default Google endpoint'}")
    print(f"  API Key Env Var: {config.llm.api_key_env_var or 'GOOGLE_API_KEY'}")
    print()


def example_2_custom_google_config():
    """Example 2: Using Google with custom configuration."""
    print("=== Example 2: Custom Google Configuration ===")
    
    # Set custom API key in environment
    os.environ["MY_GOOGLE_API_KEY"] = "your-google-api-key-here"
    
    # Create LLM config with custom settings
    llm_config = LLMConfig(
        provider="google",
        model_name="gemini-1.5-pro",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # Custom endpoint
        api_key_env_var="MY_GOOGLE_API_KEY",  # Custom env var name
        temperature=0.3,
        max_tokens=16384
    )
    
    # Create chunking engine config
    config = ChunkingEngineConfig(llm=llm_config)
    
    # Initialize the chunking engine
    engine = ChunkingEngine(config)
    
    print(f"✓ Engine initialized with custom Google configuration")
    print(f"  Model: {config.llm.model_name}")
    print(f"  Base URL: {config.llm.base_url}")
    print(f"  API Key Env Var: {config.llm.api_key_env_var}")
    print()


def example_3_environment_variables():
    """Example 3: Using environment variables for configuration."""
    print("=== Example 3: Environment Variable Configuration ===")
    
    # Set configuration via environment variables
    os.environ.update({
        "GOOGLE_API_KEY": "your-google-api-key-here",
        "STACCATO_LLM__PROVIDER": "google",
        "STACCATO_LLM__MODEL_NAME": "gemini-1.5-flash",
        "STACCATO_LLM__TEMPERATURE": "0.5",
        "STACCATO_LLM__MAX_TOKENS": "12288"
    })
    
    # Create config - it will automatically load from environment variables
    config = ChunkingEngineConfig()
    
    # Initialize the chunking engine
    engine = ChunkingEngine(config)
    
    print(f"✓ Engine initialized from environment variables")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Model: {config.llm.model_name}")
    print(f"  Temperature: {config.llm.temperature}")
    print(f"  Max Tokens: {config.llm.max_tokens}")
    print()


def example_4_comparison_openai_vs_google():
    """Example 4: Comparing OpenAI vs Google configuration."""
    print("=== Example 4: OpenAI vs Google Comparison ===")
    
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
    print(f"  Base URL: {google_config.base_url or 'Default Google endpoint'}")
    print(f"  API Key Env Var: {google_config.api_key_env_var or 'GOOGLE_API_KEY'}")
    print()


async def example_5_async_processing():
    """Example 5: Async processing with Google."""
    print("=== Example 5: Async Processing with Google ===")
    
    # Set up Google configuration
    os.environ["GOOGLE_API_KEY"] = "your-google-api-key-here"
    
    config = ChunkingEngineConfig()
    config.llm.provider = "google"
    config.llm.model_name = "gemini-1.5-flash"
    
    engine = ChunkingEngine(config)
    
    print(f"✓ Engine ready for async processing with Google")
    print(f"  Use: chunks = await engine.achunk_document('path/to/document.pdf')")
    print()


if __name__ == "__main__":
    print("Staccato Google LLM Configuration Examples")
    print("=" * 50)
    print()
    
    # Note: These examples won't actually run without valid API keys
    # They're meant to demonstrate configuration patterns
    
    try:
        example_1_default_google_config()
        example_2_custom_google_config()
        example_3_environment_variables()
        example_4_comparison_openai_vs_google()
        
        print("✓ All configuration examples completed successfully!")
        print("\nTo use these configurations with real API keys:")
        print("1. Set your GOOGLE_API_KEY environment variable")
        print("2. Replace 'your-google-api-key-here' with your actual API key")
        print("3. Run: python examples/google_llm_example.py")
        
    except Exception as e:
        print(f"Note: Examples completed with expected configuration errors: {e}")
        print("This is normal when API keys are not set.")
