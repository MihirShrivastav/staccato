import logging
import sys
import structlog
from typing import Optional

def setup_logging(log_level: str = "INFO", file_path: Optional[str] = None):
    """
    Configures structured logging for the Staccato library.
    This sets up structlog to produce JSON-formatted logs for the 'staccato'
    logger specifically, avoiding verbose output from other libraries.

    Args:
        log_level: The minimum log level to output (e.g., "DEBUG", "INFO").
        file_path: Optional path to a file to save logs to.
    """
    log_level = log_level.upper()

    # Silence noisy loggers from dependencies
    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    # Get the logger for the 'staccato' package.
    staccato_logger = logging.getLogger("staccato")
    staccato_logger.setLevel(log_level)
    staccato_logger.propagate = False  # Prevent logs from going to the root logger

    # Clear existing handlers to avoid duplication
    if staccato_logger.hasHandlers():
        staccato_logger.handlers.clear()

    # Add a handler to write to the console.
    console_handler = logging.StreamHandler(sys.stdout)
    staccato_logger.addHandler(console_handler)
    
    # If a file path is provided, add a file handler.
    if file_path:
        file_handler = logging.FileHandler(file_path, mode='w')
        staccato_logger.addHandler(file_handler)

    # Configure structlog to process logs from the 'staccato' logger.
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def setup_llm_logging(log_level: str = "INFO", file_path: Optional[str] = None):
    """
    Configures a separate logger specifically for LLM interactions.
    This logger captures all LLM inputs and outputs for debugging and analysis.

    Args:
        log_level: The minimum log level to output (e.g., "DEBUG", "INFO").
        file_path: Optional path to a file to save LLM logs to.
    """
    log_level = log_level.upper()

    # Get the logger for LLM interactions
    llm_logger = logging.getLogger("staccato.llm")
    llm_logger.setLevel(log_level)
    llm_logger.propagate = False  # Prevent logs from going to the root logger

    # Clear existing handlers to avoid duplication
    if llm_logger.hasHandlers():
        llm_logger.handlers.clear()

    # If a file path is provided, add a file handler.
    if file_path:
        file_handler = logging.FileHandler(file_path, mode='w')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        llm_logger.addHandler(file_handler)
    else:
        # Add console handler if no file path is provided
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        llm_logger.addHandler(console_handler)

def get_logger(name: str):
    """
    Returns a configured structlog logger instance.

    Args:
        name: The name of the logger (typically __name__).
    """
    return structlog.get_logger(name)

def get_llm_logger():
    """
    Returns the dedicated LLM logger for capturing LLM interactions.
    """
    return logging.getLogger("staccato.llm") 