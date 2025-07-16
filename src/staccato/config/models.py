from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

class LLMConfig(BaseSettings):
    """Configuration for the Language Model provider."""
    provider: Literal["openai", "google"] = Field(
        default="openai",
        description="The LLM provider to use."
    )
    model_name: str = Field(
        default="gpt-4.1-mini",
        description="The specific model name to use for chunking."
    )
    temperature: float = Field(
        default=0.5,
        description="The sampling temperature for the LLM."
    )
    max_tokens: int = Field(
        default=16384,
        description="The maximum number of tokens to generate."
    )
    base_url: str | None = Field(
        default=None,
        description="Custom base URL for the LLM API. If not provided, uses provider defaults."
    )
    api_key_env_var: str | None = Field(
        default=None,
        description="Environment variable name for the API key. If not provided, uses provider defaults."
    )

    reasoning_effort: Literal["low", "medium", "high", None] = Field(
        default=None,
        description="The reasoning effort to use for the LLM."
    )

class RetryConfig(BaseSettings):
    """Configuration for the LLM API retry logic."""
    attempts: int = Field(
        default=3,
        description="The maximum number of times to retry a failed LLM API call."
    )
    min_wait: int = Field(default=1, description="The initial wait time in seconds.")
    max_wait: int = Field(default=10, description="The maximum wait time in seconds.")
    wait_multiplier: int = Field(default=2, description="The multiplier for exponential backoff.")

class PreprocessingConfig(BaseSettings):
    """Configuration for the pre-processing stage."""
    use_layout_analysis: bool = Field(
        True,
        description="Whether to use layout analysis for richer markdown conversion."
    )
    page_batch_size: int = Field(
        default=3,
        description="Number of pages to batch together for a single LLM call."
    )
    pdf_processor: Literal["pdfplumber", "pymupdf4llm"] = Field(
        default="pdfplumber",
        description="The PDF processor to use. 'pymupdf4llm' provides better markdown formatting."
    )

class ChunkingEngineConfig(BaseSettings):
    """
    Master configuration for the Staccato Chunking Engine.
    This model loads settings from a 'staccato.toml' file and environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="STACCATO_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig) 