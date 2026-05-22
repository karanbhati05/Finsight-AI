# src/utils/helpers.py

import re
import yaml
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "configs/config.yaml") -> dict:
    """
    Load the central YAML config file.
    Every module that needs settings calls this instead of
    hardcoding values or reading env vars directly.
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    logger.info(f"Config loaded from {config_path}")
    return config


def save_dataframe(df: pd.DataFrame, path: str) -> None:
    """Save a DataFrame to CSV, creating parent directories if needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(df)} rows to {path}")


def load_dataframe(path: str) -> pd.DataFrame:
    """Load a CSV with a clear error if the file doesn't exist."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\n"
            f"Have you run the pipeline first? Try: python scripts/run_pipeline.py"
        )
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df


def clean_text(text: str) -> str:
    """
    Basic text cleaning applied before NLP processing.
    Order matters — do URL removal before whitespace collapse.
    """
    if not isinstance(text, str):
        return ""

    text = re.sub(r"http\S+|www\.\S+", "", text)        # remove URLs
    text = re.sub(r"<[^>]+>", "", text)                  # strip HTML tags
    text = re.sub(r"[^\w\s.,!?%$€£\-]", "", text)        # keep financial chars
    text = re.sub(r"\s+", " ", text).strip()             # collapse whitespace

    return text


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """
    Split a long document into overlapping word-level chunks.

    Why overlap? If a key sentence sits at the boundary of two chunks,
    overlap ensures it appears fully in at least one of them.
    Critical for RAG — you don't want to split "revenue grew 40%
    beating estimates" across two chunks and lose the context.

    Args:
        text:       the full document text
        chunk_size: words per chunk (not tokens — approximation)
        overlap:    words repeated at start of next chunk
    """
    words = text.split()
    chunks = []

    step = chunk_size - overlap  # how far to advance each iteration
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


def ensure_dirs(*paths: str) -> None:
    """Create multiple directories at once. Called during project setup."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ready: {path}")