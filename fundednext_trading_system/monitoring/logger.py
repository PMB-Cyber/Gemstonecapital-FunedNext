from loguru import logger
import sys
from pathlib import Path

# Define log directory path
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Remove default logger
logger.remove()

# Standard output logging configuration
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}",
    enqueue=True,  # Ensures threadsafety in case of multi-threading
)

# Main system log for general information and warnings
logger.add(
    LOG_DIR / "system.log",
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    rotation="5 MB",  # Rotates logs when the size exceeds 5 MB
    retention="7 days",  # Retains logs for 7 days
    compression="zip",  # Compress old logs to zip files
    enqueue=True,  # Thread safety
)

# Error log for tracking issues, warnings, or failures
logger.add(
    LOG_DIR / "errors.log",
    level="ERROR",
    format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | <level>{level}</level> | {message}",
    rotation="5 MB",  # Rotates logs when the size exceeds 5 MB
    retention="14 days",  # Retains logs for 14 days
    enqueue=True,  # Thread safety
)

# Trade log for success scenarios such as order completions, executions, etc.
logger.add(
    LOG_DIR / "trades.log",
    level="SUCCESS",  # Log success level for trades
    format="<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> | <level>{level}</level> | {message}",
    rotation="2 MB",  # Rotates logs when the size exceeds 2 MB
    retention="30 days",  # Retains logs for 30 days
    enqueue=True,  # Thread safety
)

# Debug log for capturing low-level information during development or troubleshooting
logger.add(
    LOG_DIR / "debug.log",
    level="DEBUG",  # Allows DEBUG level logs
    format="<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | <level>{level}</level> | {message}",
    rotation="2 MB",  # Rotates logs when the size exceeds 2 MB
    retention="30 days",  # Retains logs for 30 days
    enqueue=True,  # Thread safety
)

# Example of adding loggers for more granular control (optional)
# Example for critical logs
logger.add(
    LOG_DIR / "critical.log",
    level="CRITICAL",
    format="<magenta>{time:YYYY-MM-DD HH:mm:ss}</magenta> | <level>{level}</level> | {message}",
    rotation="10 MB",  # Rotates logs when the size exceeds 10 MB
    retention="30 days",  # Retains logs for 30 days
    enqueue=True,  # Thread safety
)
