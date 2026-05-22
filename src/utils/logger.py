# src/utils/logger.py

import logging
from pathlib import Path
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Call this at the top of every module like:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)

    __name__ auto-resolves to the module path e.g. "src.nlp.sentiment"
    so every log line tells you exactly which file it came from.
    """

    Path("logs").mkdir(exist_ok=True)  # create logs/ folder if missing

    logger = logging.getLogger(name)

    # Guard: if handlers already exist, don't add them again
    # (happens if the same module is imported multiple times)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Format: 2024-01-15 10:23:01 | INFO     | src.nlp.sentiment | Loading model...
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — force UTF-8 on Windows
    console_handler = logging.StreamHandler(
        stream=open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    )
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # File handler — always UTF-8
    file_handler = logging.FileHandler("logs/finsight.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger