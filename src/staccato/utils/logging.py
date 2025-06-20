import logging
import sys
import structlog

def setup_logging(log_level: str = "INFO"):
    """
    Configures structured logging for the Staccato library.

    This sets up structlog to produce JSON-formatted logs, which are
    machine-readable and easy to process.

    Args:
        log_level: The minimum log level to output (e.g., "DEBUG", "INFO").
    """
    log_level = log_level.upper()

    # Configure the standard logging library to route to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog processors
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

def get_logger(name: str):
    """
    Returns a configured structlog logger instance.

    Args:
        name: The name of the logger (typically __name__).
    """
    return structlog.get_logger(name) 