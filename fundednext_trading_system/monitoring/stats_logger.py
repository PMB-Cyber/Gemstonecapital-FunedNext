from loguru import logger

logger.add(
    "logs/performance.log",
    rotation="1 day",
    level="INFO",
    format="{time} | {level} | {message}"
)
