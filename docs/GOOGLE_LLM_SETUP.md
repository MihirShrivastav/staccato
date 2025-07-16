# Google LLM Provider Setup

Staccato supports Google's Gemini models through their OpenAI-compatible API endpoint. This guide explains how to configure and use Google as your LLM provider.

## Prerequisites

1. **Google AI Studio API Key**: Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **OpenAI Python Library**: Staccato uses the OpenAI Python client to communicate with Google's OpenAI-compatible endpoint

```bash
pip install "staccato[openai]"
```

## Quick Start

### 1. Set Your API Key

```bash
export GOOGLE_API_KEY="your-google-api-key-here"
```

### 2. Configure Staccato for Google

```python
from staccato import ChunkingEngine, LLMConfig, ChunkingEngineConfig

# Create Google LLM configuration
llm_config = LLMConfig(
    provider="google",
    model_name="gemini-2.5-flash",  # or "gemini-1.5-pro"
    temperature=0.5,
    max_tokens=8192
)

# Create engine configuration
config = ChunkingEngineConfig(llm=llm_config)

# Initialize the chunking engine
engine = ChunkingEngine(config)

# Use the engine
chunks = await engine.achunk_document("path/to/your/document.pdf")
```

## Configuration Options

### Available Models

- `gemini-1.5-flash`: Fast, efficient model for most use cases
- `gemini-1.5-pro`: More capable model for complex tasks
- `gemini-1.5-flash-8b`: Smaller, faster variant

### Default Configuration

When you set `provider="google"`, Staccato automatically configures:

- **Base URL**: `https://generativelanguage.googleapis.com/v1beta/openai/`
- **API Key Environment Variable**: `GOOGLE_API_KEY`

### Custom Configuration

You can override the defaults:

```python
llm_config = LLMConfig(
    provider="google",
    model_name="gemini-1.5-pro",
    base_url="https://custom-endpoint.com/v1/",  # Custom endpoint
    api_key_env_var="MY_GOOGLE_API_KEY",         # Custom env var name
    temperature=0.3,
    max_tokens=16384
)
```

## Environment Variable Configuration

You can configure everything via environment variables:

```bash
export GOOGLE_API_KEY="your-api-key"
export STACCATO_LLM__PROVIDER="google"
export STACCATO_LLM__MODEL_NAME="gemini-1.5-flash"
export STACCATO_LLM__TEMPERATURE="0.7"
export STACCATO_LLM__MAX_TOKENS="8192"
```

Then use the default configuration:

```python
from staccato import ChunkingEngine

# Configuration loaded automatically from environment
engine = ChunkingEngine()
```

## Configuration File (staccato.toml)

Create a `staccato.toml` file in your project root:

```toml
[llm]
provider = "google"
model_name = "gemini-1.5-flash"
temperature = 0.7
max_tokens = 8192

[retry]
attempts = 3
min_wait = 1
max_wait = 10
```

## Comparison: OpenAI vs Google

| Feature | OpenAI | Google |
|---------|--------|--------|
| **API Key Env Var** | `OPENAI_API_KEY` | `GOOGLE_API_KEY` |
| **Base URL** | Default OpenAI endpoint | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| **Models** | `gpt-4o`, `gpt-4o-mini`, etc. | `gemini-1.5-flash`, `gemini-1.5-pro`, etc. |
| **API Schema** | Native OpenAI | OpenAI-compatible |

## Error Handling

### Missing API Key

```python
# This will raise: ValueError: API key not found in environment variable: GOOGLE_API_KEY
engine = ChunkingEngine(ChunkingEngineConfig(llm=LLMConfig(provider="google")))
```

**Solution**: Set the `GOOGLE_API_KEY` environment variable.

### Invalid Model Name

```python
llm_config = LLMConfig(
    provider="google",
    model_name="invalid-model-name"
)
```

**Solution**: Use valid Gemini model names like `gemini-1.5-flash` or `gemini-1.5-pro`.

## Best Practices

### 1. Model Selection

- **Use `gemini-1.5-flash`** for most document chunking tasks (faster, cost-effective)
- **Use `gemini-1.5-pro`** for complex documents requiring deeper understanding

### 2. Token Limits

- **Gemini 1.5 Flash**: Up to 1M tokens input, 8K tokens output
- **Gemini 1.5 Pro**: Up to 2M tokens input, 8K tokens output

Set `max_tokens` appropriately:

```python
llm_config = LLMConfig(
    provider="google",
    model_name="gemini-1.5-flash",
    max_tokens=4096  # Adjust based on your needs
)
```

### 3. Rate Limiting

Google has rate limits. Configure retry settings:

```python
from staccato import RetryConfig

config = ChunkingEngineConfig(
    llm=LLMConfig(provider="google", model_name="gemini-1.5-flash"),
    retry=RetryConfig(
        attempts=5,      # More retries for rate limits
        min_wait=2,      # Longer initial wait
        max_wait=30      # Longer max wait
    )
)
```

### 4. Environment Management

Use different API keys for different environments:

```bash
# Development
export GOOGLE_API_KEY="dev-api-key"

# Production
export GOOGLE_API_KEY="prod-api-key"
```

## Troubleshooting

### Common Issues

1. **Authentication Error**: Check your API key is valid and has the correct permissions
2. **Rate Limit Error**: Increase retry wait times or reduce request frequency
3. **Model Not Found**: Ensure you're using valid Gemini model names
4. **Network Error**: Check your internet connection and Google AI service status

### Debug Logging

Enable detailed logging to troubleshoot issues:

```python
from staccato.utils.logging import setup_llm_logging

# Enable debug logging for LLM interactions
setup_llm_logging(log_level="DEBUG", file_path="llm_debug.log")
```

## Migration from OpenAI

To migrate from OpenAI to Google:

1. **Change the provider**:
   ```python
   # Before
   llm_config = LLMConfig(provider="openai", model_name="gpt-4o-mini")
   
   # After
   llm_config = LLMConfig(provider="google", model_name="gemini-1.5-flash")
   ```

2. **Update environment variables**:
   ```bash
   # Remove or keep for other projects
   # export OPENAI_API_KEY="..."
   
   # Add Google API key
   export GOOGLE_API_KEY="your-google-api-key"
   ```

3. **Adjust model-specific parameters** if needed (temperature, max_tokens, etc.)

The rest of your code remains unchanged!
