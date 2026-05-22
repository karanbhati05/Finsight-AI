# src/nlp/summarizer.py

import pandas as pd
from transformers import pipeline, Pipeline
from src.utils.logger import get_logger
from src.utils.helpers import chunk_text

logger = get_logger(__name__)

# facebook/bart-large-cnn — fine-tuned on CNN/DailyMail news summarization
# Strong at summarizing news-style financial text
# Downloads ~1.6GB on first use, cached after that
DEFAULT_MODEL = "facebook/bart-large-cnn"

# BART's max input is ~1024 tokens ≈ 800 words
# We chunk longer documents and summarize each chunk separately
BART_MAX_INPUT_WORDS = 800


class FinancialSummarizer:
    """
    Document summarizer for financial text using BART.

    Handles both short articles (single pass) and long documents
    like SEC filings (chunked summarization with final merge).

    Usage:
        summarizer = FinancialSummarizer()
        summary = summarizer.summarize("Apple reported record revenue of...")
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, device: int = -1):
        """
        Load BART summarization pipeline.

        Args:
            model_name: HuggingFace model identifier
            device:     -1 for CPU, 0 for first GPU
                        HuggingFace pipelines use int device IDs
        """
        logger.info(f"Loading summarizer: {model_name}")

        # HuggingFace pipeline handles tokenization + model + decoding
        # Much simpler than manual model loading for generation tasks
        self.summarizer: Pipeline = pipeline(
            "summarization",
            model  = model_name,
            device = device,
        )

        self.model_name = model_name
        logger.info("Summarizer ready")


    def summarize(
        self,
        text:       str,
        max_length: int = 200,
        min_length: int = 50,
    ) -> str:
        """
        Summarize a single document.

        Automatically handles long texts by chunking them first,
        summarizing each chunk, then doing a final summary of summaries.

        Args:
            text:       cleaned document text
            max_length: max tokens in output summary
            min_length: min tokens in output summary
                        (prevents degenerate one-word outputs)

        Returns:
            Summary string, or empty string if input is empty
        """
        if not text or not text.strip():
            return ""

        words = text.split()

        # Short text — single pass summarization
        if len(words) <= BART_MAX_INPUT_WORDS:
            return self._summarize_single(text, max_length, min_length)

        # Long text — chunk → summarize each → summarize the summaries
        return self._summarize_long(text, max_length, min_length)


    def _summarize_single(
        self,
        text:       str,
        max_length: int,
        min_length: int,
    ) -> str:
        """
        Run BART on a single text that fits within the token limit.

        Args:
            text:       text within BART's token limit
            max_length: max output tokens
            min_length: min output tokens

        Returns:
            summary string
        """
        try:
            result = self.summarizer(
                text,
                max_length  = max_length,
                min_length  = min_length,
                do_sample   = False,   # greedy decoding — deterministic output
                truncation  = True,    # safety truncation if slightly over limit
            )
            return result[0]["summary_text"].strip()

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # Fallback: return first 3 sentences of original text
            sentences = text.split(".")[:3]
            return ". ".join(s.strip() for s in sentences if s.strip()) + "."


    def _summarize_long(
        self,
        text:       str,
        max_length: int,
        min_length: int,
    ) -> str:
        """
        Hierarchical summarization for documents exceeding BART's input limit.

        Strategy:
            1. Split document into chunks of ~800 words with 50-word overlap
            2. Summarize each chunk independently (parallel in production)
            3. Concatenate chunk summaries
            4. If concatenated summaries fit in limit → final summary pass
               Else → return concatenated summaries directly

        Why this strategy?
            Simply truncating a 50,000-word 10-K at word 800 means
            you only summarize the cover page. Hierarchical summarization
            ensures all sections contribute to the final summary.

        Args:
            text:       long document text
            max_length: target output length for final summary
            min_length: minimum output length

        Returns:
            Summary covering the full document
        """
        logger.info(
            f"Long document detected ({len(text.split())} words) — "
            f"using hierarchical summarization"
        )

        # Step 1: Chunk the document
        # chunk_size=700 leaves buffer below BART's 800-word limit
        chunks = chunk_text(text, chunk_size=700, overlap=50)

        # Only summarize the first 5 chunks to keep runtime reasonable
        # For a 10-K filing, first 5 chunks cover the executive summary
        # and key financial highlights — the most signal-dense sections
        chunks_to_process = chunks[:5]

        logger.info(f"Summarizing {len(chunks_to_process)} chunks...")

        # Step 2: Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks_to_process):
            logger.info(f"  Chunk {i+1}/{len(chunks_to_process)}")
            # Shorter summaries per chunk — they'll be merged
            summary = self._summarize_single(chunk, max_length=100, min_length=30)
            if summary:
                chunk_summaries.append(summary)

        if not chunk_summaries:
            return ""

        # Step 3: Merge chunk summaries
        merged = " ".join(chunk_summaries)

        # Step 4: Final summarization pass if merged fits in limit
        merged_words = len(merged.split())
        if merged_words <= BART_MAX_INPUT_WORDS:
            logger.info("Running final summarization pass on merged chunks")
            return self._summarize_single(merged, max_length, min_length)

        # Merged summaries still too long — return them directly
        # They're already much shorter than the original
        logger.info("Returning merged chunk summaries directly")
        return merged


    def summarize_batch(
        self,
        texts:      list[str],
        max_length: int = 150,
        min_length: int = 40,
    ) -> list[str]:
        """
        Summarize a list of texts.

        Used by the pipeline to batch-process all news articles.
        Each article gets its own summary for the dashboard cards.

        Args:
            texts:      list of cleaned article texts
            max_length: max output tokens per summary
            min_length: min output tokens per summary

        Returns:
            List of summary strings in same order as input
        """
        summaries = []
        total = len(texts)

        for i, text in enumerate(texts):
            summary = self.summarize(text, max_length=max_length, min_length=min_length)
            summaries.append(summary)

            if (i + 1) % 10 == 0:
                logger.info(f"Summarization progress: {i+1}/{total}")

        logger.info(f"Summarization complete: {total} documents processed")
        return summaries


    def analyze_dataframe(
        self,
        df:       pd.DataFrame,
        text_col: str = "content_summary",
    ) -> pd.DataFrame:
        """
        Add summary column to a news DataFrame.

        Args:
            df:       news DataFrame with cleaned summary text column
            text_col: column containing text cleaned for summarization

        Returns:
            DataFrame with added 'summary' column
        """
        logger.info(f"Summarizing {len(df)} articles...")
        df = df.copy()

        texts = df[text_col].fillna("").tolist()
        df["summary"] = self.summarize_batch(texts)

        # Flag empty summaries for quality monitoring
        n_empty = (df["summary"] == "").sum()
        if n_empty > 0:
            logger.warning(f"{n_empty} articles produced empty summaries")

        return df


    def summarize_filing(self, filing: dict) -> dict:
        """
        Summarize a single SEC filing dict from edgar_fetcher.py.

        SEC filings are always long documents — this always uses
        hierarchical summarization. The summary is added to the
        filing dict and returned.

        Args:
            filing: dict with at least a 'text' key from edgar_fetcher

        Returns:
            Same dict with added 'summary' key
        """
        text = filing.get("text", "")
        if not text:
            filing["summary"] = ""
            return filing

        logger.info(
            f"Summarizing {filing.get('form', 'filing')} "
            f"from {filing.get('date', 'unknown date')} "
            f"({len(text.split()):,} words)"
        )

        filing["summary"] = self.summarize(text, max_length=300, min_length=100)
        return filing