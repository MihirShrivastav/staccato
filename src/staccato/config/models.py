from pydantic import BaseModel, Field
from typing import Literal

class LLMConfig(BaseModel):
    """Configuration for the Language Model provider."""
    provider: Literal["openai", "anthropic", "mock"] = Field(
        default="openai",
        description="The LLM provider to use."
    )
    model_name: str = Field(
        default="gpt-4-turbo",
        description="The specific model name to use for chunking."
    )
    temperature: float = Field(
        default=0.0,
        description="The sampling temperature for the LLM."
    )
    max_tokens: int = Field(
        default=2048,
        description="The maximum number of tokens to generate."
    )

class RetryConfig(BaseModel):
    """Configuration for API call retry logic."""
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for a failed API call."
    )
    backoff_factor: float = Field(
        default=2.0,
        description="Factor by which to increase delay between retries."
    )

class PreprocessingConfig(BaseModel):
    """Configuration for the document pre-processing stage."""
    pdf_parser: Literal["pdfplumber", "pymupdf", "pypdf"] = Field(
        default="pdfplumber",
        description="The library to use for parsing PDF documents."
    )
    page_batch_size: int = Field(
        default=3,
        description="Number of pages to batch together for a single LLM call."
    )
    use_layout_analysis: bool = Field(
        default=True,
        description="Whether to use visual/layout cues in pre-processing."
    )

class ChunkingEngineConfig(BaseModel):
    """
    Master configuration for the Staccato Chunking Engine.
    This model holds all tunable parameters for the chunking process.
    """
    llm: LLMConfig = Field(default_factory=LLMConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)

    class Config:
        # This allows for nested models to be loaded from environment variables
        # e.g., STACCATO_LLM__PROVIDER='anthropic'
        nested_model_separator = "__" 