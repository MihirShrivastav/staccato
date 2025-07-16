# LM Studio LLM Provider Setup

This guide explains how to configure and use LM Studio as the LLM provider for Staccato. LM Studio provides a local OpenAI-compatible API server for running Large Language Models locally on your machine.

## Prerequisites

1. **Install LM Studio**: Download and install LM Studio from [https://lmstudio.ai/](https://lmstudio.ai/)
2. **Install Staccato with OpenAI dependencies**:
   ```bash
   pip install "staccato[openai]"
   ```

## LM Studio Setup

### 1. Download and Load a Model

1. Open LM Studio
2. Go to the "Discover" tab to browse available models
3. Download a model suitable for your hardware (e.g., Llama 3.2 3B, Mistral 7B)
4. Load the model in the "Chat" tab

### 2. Start the Local Server

1. Go to the "Local Server" tab in LM Studio
2. Select your loaded model
3. Click "Start Server"
4. The server will typically start on `http://localhost:1234`
5. Note the model name shown in the server interface

## Basic Configuration

### Python Configuration

```python
from staccato import ChunkingEngine
from staccato.config import LLMConfig, ChunkingEngineConfig

# Create LM Studio LLM configuration
llm_config = LLMConfig(
    provider="lmstudio",
    model_name="llama-3.2-3b-instruct",  # Replace with your loaded model name
    temperature=0.7,
    max_tokens=8192,
)

# Create chunking engine
config = ChunkingEngineConfig(llm=llm_config)
engine = ChunkingEngine(config)

# Process a document
chunks = engine.chunk_document("path/to/your/document.pdf")
```

### Environment Variable Configuration

You can configure LM Studio via environment variables:

```bash
export STACCATO_LLM__PROVIDER="lmstudio"
export STACCATO_LLM__MODEL_NAME="llama-3.2-3b-instruct"
export STACCATO_LLM__TEMPERATURE="0.7"
export STACCATO_LLM__MAX_TOKENS="8192"
```

Then use the default configuration:

```python
from staccato import ChunkingEngine

# Configuration loaded automatically from environment
engine = ChunkingEngine()
```

### Configuration File (staccato.toml)

Create a `staccato.toml` file in your project root:

```toml
[llm]
provider = "lmstudio"
model_name = "llama-3.2-3b-instruct"
temperature = 0.7
max_tokens = 8192

[retry]
attempts = 3
min_wait = 1
max_wait = 10
```

## Advanced Configuration

### Custom Base URL and API Key

If you're running LM Studio on a different port or with custom settings:

```python
import os

# Set custom API key (if configured in LM Studio)
os.environ["LMSTUDIO_API_KEY"] = "your-custom-key"

llm_config = LLMConfig(
    provider="lmstudio",
    model_name="mistral-7b-instruct",
    base_url="http://localhost:8080/v1",  # Custom port
    api_key_env_var="LMSTUDIO_API_KEY",   # Custom env var
    temperature=0.3,
    max_tokens=16384
)
```

### Default Values

LM Studio provider uses these defaults:
- **Base URL**: `http://localhost:1234/v1`
- **API Key**: `"lm-studio"` (LM Studio's default)
- **API Key Environment Variable**: `LMSTUDIO_API_KEY`

### Reasoning Effort Support

The `reasoning_effort` parameter can be set to `"low"`, `"medium"`, `"high"`, or `None`. However, note that:
- **OpenAI**: Only o1 models (like `o1-preview`, `o1-mini`) actually use this parameter
- **Google**: This parameter is accepted but may not affect model behavior
- **LM Studio**: This parameter is accepted but depends on the underlying model's capabilities

Most local models in LM Studio don't have built-in reasoning effort controls, so this parameter may not have any effect.

## Model Selection

### Popular Models for Document Chunking

1. **Llama 3.2 3B Instruct** - Good balance of speed and quality
2. **Mistral 7B Instruct** - Higher quality, requires more resources
3. **Phi-3 Mini** - Very fast, good for simple documents
4. **CodeLlama 7B** - Good for technical documents

### Model Name Format

The model name should match exactly what's shown in LM Studio's server interface. Common formats:
- `llama-3.2-3b-instruct`
- `mistral-7b-instruct-v0.1`
- `phi-3-mini-4k-instruct`

## Troubleshooting

### Common Issues

1. **Connection Error**: 
   - Ensure LM Studio server is running
   - Check the port (default: 1234)
   - Verify the base URL

2. **Model Not Found**:
   - Check the exact model name in LM Studio
   - Ensure the model is loaded and active

3. **Slow Performance**:
   - Try a smaller model
   - Reduce `max_tokens`
   - Increase hardware resources

4. **Memory Issues**:
   - Use a smaller model
   - Reduce batch size in preprocessing config
   - Close other applications

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
from staccato.logging import setup_llm_logging

# Enable debug logging
setup_llm_logging(log_level="DEBUG", file_path="lmstudio_debug.log")
```

## Performance Optimization

### Hardware Recommendations

- **CPU**: Modern multi-core processor
- **RAM**: 16GB+ (32GB+ for larger models)
- **GPU**: NVIDIA GPU with CUDA support (optional but recommended)
- **Storage**: SSD for faster model loading

### Configuration Tips

1. **Adjust temperature**: Lower values (0.1-0.3) for more consistent output
2. **Optimize max_tokens**: Balance between quality and speed
3. **Use appropriate model size**: Smaller models for simple documents
4. **Batch processing**: Process multiple documents in sequence

## Migration from Other Providers

### From OpenAI

```python
# Before (OpenAI)
llm_config = LLMConfig(provider="openai", model_name="gpt-4o-mini")

# After (LM Studio)
llm_config = LLMConfig(provider="lmstudio", model_name="llama-3.2-3b-instruct")
```

### From Google

```python
# Before (Google)
llm_config = LLMConfig(provider="google", model_name="gemini-1.5-flash")

# After (LM Studio)
llm_config = LLMConfig(provider="lmstudio", model_name="mistral-7b-instruct")
```

## Example Usage

See `examples/lmstudio_example.py` for complete working examples including:
- Basic configuration
- Custom settings
- Asynchronous processing
- Provider comparisons

## Benefits of LM Studio

1. **Privacy**: All processing happens locally
2. **No API costs**: No per-token charges
3. **Offline capability**: Works without internet connection
4. **Model variety**: Access to many open-source models
5. **Full control**: Complete control over model and parameters

## Limitations

1. **Hardware requirements**: Needs sufficient local resources
2. **Model size constraints**: Limited by available RAM/VRAM
3. **Setup complexity**: Requires model download and management
4. **Performance**: May be slower than cloud APIs depending on hardware
