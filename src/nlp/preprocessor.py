# src/nlp/preprocessor.py

import re
import string
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

# NewsAPI truncates article content at 260 chars and appends this marker
# We strip it because it's not real content
NEWSAPI_TRUNCATION_MARKER = r"\[\+\d+ chars\]"

# Maximum characters to pass to a transformer model
# FinBERT tokenizes to max 512 tokens ≈ ~2000 characters
# Feeding more doesn't help and slows inference
MAX_CHARS_FOR_MODEL = 2000


def remove_html(text: str) -> str:
    """Strip HTML tags and decode common HTML entities."""
    text = re.sub(r"<[^>]+>", " ", text)        # <b>, <p>, <div class="x"> etc
    text = re.sub(r"&amp;",   "&", text)
    text = re.sub(r"&lt;",    "<", text)
    text = re.sub(r"&gt;",    ">", text)
    text = re.sub(r"&nbsp;",  " ", text)
    text = re.sub(r"&#\d+;",  " ", text)         # numeric HTML entities &#160;
    return text


def remove_urls(text: str) -> str:
    """Remove http/https URLs and bare www. links."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+",     "", text)
    return text


def remove_newsapi_artifacts(text: str) -> str:
    """
    Remove NewsAPI-specific truncation markers.
    NewsAPI free tier truncates content and appends e.g. "[+4521 chars]"
    This is metadata about truncation, not actual content.
    """
    text = re.sub(NEWSAPI_TRUNCATION_MARKER, "", text)
    return text


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces, tabs, newlines into a single space."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keep_financial_chars(text: str) -> str:
    """
    Remove special characters while preserving financially meaningful ones.

    Characters we KEEP and why:
        $ £ € ¥  — currency symbols
        %        — percentage (e.g. "revenue grew 12%")
        .        — decimal points and sentence endings
        ,        — number formatting (e.g. "$1,200,000")
        -        — negative numbers and hyphenated words
        +        — positive indicators
        /        — ratios (e.g. "P/E ratio")

    Characters we REMOVE:
        Everything else that isn't alphanumeric or the above
    """
    allowed = set(string.ascii_letters + string.digits + " $£€¥%.,\-+/!?'\"")
    return "".join(c if c in allowed else " " for c in text)


def truncate_for_model(text: str, max_chars: int = MAX_CHARS_FOR_MODEL) -> str:
    """
    Truncate text to a safe length for transformer models.

    Why truncate by characters not tokens?
    Tokenization is slow. Character count is a fast approximation.
    At ~4 chars per token on average, 2000 chars ≈ 500 tokens — safely
    under FinBERT's 512 token limit.
    """
    if len(text) > max_chars:
        # Truncate at a sentence boundary if possible
        truncated = text[:max_chars]
        last_period = truncated.rfind(".")
        if last_period > max_chars * 0.8:   # only use sentence boundary if close to limit
            return truncated[:last_period + 1]
        return truncated
    return text


def clean_for_sentiment(text: str) -> str:
    """
    Full cleaning pipeline for sentiment analysis input.
    Applies all cleaning steps in the correct order.

    Order matters:
    1. Remove HTML first (before URL removal — URLs can be inside href attributes)
    2. Remove URLs (before character filtering — URLs contain lots of special chars)
    3. Remove NewsAPI artifacts
    4. Keep only financial characters
    5. Normalize whitespace (always last — previous steps create extra spaces)
    6. Truncate for model

    Args:
        text: raw article text

    Returns:
        Cleaned text ready for FinBERT
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    text = remove_html(text)
    text = remove_urls(text)
    text = remove_newsapi_artifacts(text)
    text = keep_financial_chars(text)
    text = normalize_whitespace(text)
    text = truncate_for_model(text)

    return text


def clean_for_ner(text: str) -> str:
    """
    Cleaning pipeline for Named Entity Recognition.

    NER needs slightly different cleaning than sentiment:
    - Keep MORE punctuation (colons, parentheses) — they help spaCy
      identify entity boundaries e.g. "CEO: Tim Cook" or "Apple (AAPL)"
    - Don't truncate as aggressively — NER benefits from more context
    - Keep numbers intact — "acquired for $3.2 billion" is a money entity

    Args:
        text: raw article text

    Returns:
        Cleaned text ready for spaCy NER
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    text = remove_html(text)
    text = remove_urls(text)
    text = remove_newsapi_artifacts(text)

    # Less aggressive character filtering for NER — keep colons, parens, quotes
    text = re.sub(r"[^\w\s$£€%.,\-+/:()\"']", " ", text)
    text = normalize_whitespace(text)

    # NER can handle longer texts — truncate less aggressively
    return text[:5000]


def clean_for_summarization(text: str) -> str:
    """
    Cleaning pipeline for BART summarization.

    Summarization needs the cleanest, most readable text:
    - Remove all special characters
    - Preserve sentence structure (periods, commas)
    - Longer input is fine — BART handles chunking internally

    Args:
        text: raw filing or article text

    Returns:
        Clean text ready for BART summarizer
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    text = remove_html(text)
    text = remove_urls(text)
    text = remove_newsapi_artifacts(text)
    text = re.sub(r"[^\w\s.,!?$%\-]", " ", text)
    text = normalize_whitespace(text)

    return text


def preprocess_dataframe(
    df:         pd.DataFrame,
    text_col:   str = "content",
    title_col:  str = "title",
) -> pd.DataFrame:
    """
    Apply all cleaning pipelines to a news DataFrame.

    Creates three cleaned columns from the raw text:
        {text_col}_sentiment  — for FinBERT
        {text_col}_ner        — for spaCy
        {text_col}_summary    — for BART

    Also creates a 'combined_text' column that merges title + content
    for richer NLP input (title is often the most signal-dense sentence).

    Args:
        df:        DataFrame with raw news articles
        text_col:  name of the main text column
        title_col: name of the title column

    Returns:
        DataFrame with additional cleaned columns
    """
    df = df.copy()

    logger.info(f"Preprocessing {len(df)} articles...")

    # Combine title + content for richer input
    # Title repeated twice because it's the most information-dense part
    df["combined_text"] = (
        df[title_col].fillna("") + ". " +
        df[title_col].fillna("") + ". " +   # weight title more heavily
        df[text_col].fillna("")
    )

    # Apply each cleaning pipeline
    df[f"{text_col}_sentiment"] = df["combined_text"].apply(clean_for_sentiment)
    df[f"{text_col}_ner"]       = df["combined_text"].apply(clean_for_ner)
    df[f"{text_col}_summary"]   = df[text_col].fillna("").apply(clean_for_summarization)

    # Flag empty results — useful for debugging data quality
    n_empty = (df[f"{text_col}_sentiment"] == "").sum()
    if n_empty > 0:
        logger.warning(f"{n_empty} articles produced empty text after cleaning")

    logger.info("Preprocessing complete")
    return df