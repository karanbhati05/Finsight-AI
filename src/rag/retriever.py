# src/rag/retriever.py

import re
import pandas as pd
from src.rag.embedder import DocumentEmbedder
from src.rag.vector_store import FinancialVectorStore
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Maximum characters to include in context passed to the LLM
# GPT-3.5-turbo has a ~16k token context window
# We use a conservative limit to leave room for the prompt and answer
MAX_CONTEXT_CHARS = 6000

# Minimum similarity score to include a chunk in context
# Chunks below this threshold are likely irrelevant noise
MIN_SIMILARITY_THRESHOLD = 0.3


class FinancialRetriever:
    """
    Retrieves relevant financial document chunks for a given query.

    The retriever is responsible for the R in RAG:
        1. Embed the user's query
        2. Search ChromaDB for similar chunks
        3. Filter low-quality results
        4. Format chunks into a context string for the LLM

    Usage:
        retriever = FinancialRetriever()
        context, sources = retriever.retrieve("What were Apple's Q3 revenues?",
                                              ticker="AAPL")
    """

    def __init__(
        self,
        embedder:     DocumentEmbedder     = None,
        vector_store: FinancialVectorStore = None,
    ):
        """
        Args:
            embedder:     DocumentEmbedder instance (created if None)
            vector_store: FinancialVectorStore instance (created if None)
        """
        self.embedder     = embedder     or DocumentEmbedder()
        self.vector_store = vector_store or FinancialVectorStore()
        logger.info("Retriever initialized")


    def retrieve(
        self,
        query:      str,
        top_k:      int  = 5,
        ticker:     str  = None,
        sentiment:  str  = None,
        min_similarity: float = MIN_SIMILARITY_THRESHOLD,
    ) -> tuple[str, list[dict]]:
        """
        Main retrieval function — query → context string + sources.

        Pipeline:
            1. Embed the query
            2. Search ChromaDB (with optional filters)
            3. Filter chunks below similarity threshold
            4. Deduplicate near-identical chunks
            5. Format into a context string with source citations

        Args:
            query:          user's natural language question
            top_k:          how many chunks to retrieve
            ticker:         optional: only search documents for this ticker
            sentiment:      optional: filter by sentiment label
            min_similarity: minimum score to include a chunk

        Returns:
            Tuple of:
                context:  formatted string to pass to the LLM
                sources:  list of source metadata dicts for citations
        """
        if not query or not query.strip():
            return "", []

        logger.info(f"Retrieving context | query='{query[:80]}...' | ticker={ticker}")

        # Step 1: Embed the query
        query_embedding = self.embedder.embed_query(query)

        # Step 2: Search ChromaDB
        raw_results = self.vector_store.query(
            query_embedding = query_embedding,
            top_k           = top_k,
            ticker          = ticker,
            sentiment       = sentiment,
        )

        # Step 3: Format and filter results
        chunks = self.vector_store.format_results(raw_results)

        # Filter below similarity threshold
        chunks = [c for c in chunks if c["similarity"] >= min_similarity]

        if not chunks:
            logger.warning(
                f"No chunks above similarity threshold {min_similarity} "
                f"for query: '{query[:60]}'"
            )
            return "", []

        # Step 4: Deduplicate near-identical chunks
        chunks = self._deduplicate_chunks(chunks)

        # Step 5: Format context for LLM
        context = self._format_context(chunks)
        sources = [c["metadata"] for c in chunks]

        logger.info(
            f"Retrieved {len(chunks)} chunks | "
            f"top similarity: {chunks[0]['similarity']:.3f}"
        )

        return context, sources


    def _deduplicate_chunks(
        self,
        chunks:    list[dict],
        threshold: float = 0.95,
    ) -> list[dict]:
        """
        Remove near-duplicate chunks from retrieval results.

        Why duplicates happen:
            A news article and an SEC filing might both contain the phrase
            "revenue increased 12% year-over-year". If both were chunked and
            embedded, both will score highly for a revenue query.
            Passing both to the LLM wastes context window space.

        Strategy:
            Compare the start of each chunk text. If two chunks share
            more than 90% of their first 200 characters, keep only
            the one with higher similarity.

        Args:
            chunks:    list of formatted chunk dicts
            threshold: similarity above which chunks are considered duplicates

        Returns:
            Deduplicated list of chunks
        """
        if len(chunks) <= 1:
            return chunks

        seen_prefixes = []
        unique_chunks = []

        for chunk in chunks:
            # Use first 200 chars as fingerprint
            prefix = chunk["text"][:200].lower().strip()
            prefix = re.sub(r"\s+", " ", prefix)

            # Check if this chunk is too similar to an already-kept chunk
            is_duplicate = False
            for seen in seen_prefixes:
                overlap = self._char_overlap(prefix, seen)
                if overlap > threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_prefixes.append(prefix)
                unique_chunks.append(chunk)

        if len(unique_chunks) < len(chunks):
            logger.info(
                f"Deduplication: {len(chunks)} → {len(unique_chunks)} chunks"
            )

        return unique_chunks


    def _char_overlap(self, a: str, b: str) -> float:
        """
        Compute character-level overlap between two strings.
        Simple approximation of string similarity.

        Returns:
            Float 0.0 (no overlap) to 1.0 (identical)
        """
        if not a or not b:
            return 0.0

        shorter = min(len(a), len(b))
        matches = sum(ca == cb for ca, cb in zip(a[:shorter], b[:shorter]))
        return matches / shorter


    def _format_context(
        self,
        chunks: list[dict],
    ) -> str:
        """
        Format retrieved chunks into a context string for the LLM.

        Format designed to:
            1. Give the LLM clear source attribution for each chunk
            2. Separate chunks visually so the LLM doesn't blend them
            3. Stay within MAX_CONTEXT_CHARS to avoid token limit errors

        Each chunk is prefixed with:
            [Source N | Ticker | Date | Source Name | Similarity: X.XX]

        Args:
            chunks: deduplicated, filtered chunk list

        Returns:
            Formatted context string
        """
        context_parts = []
        total_chars   = 0

        for i, chunk in enumerate(chunks, 1):
            meta       = chunk.get("metadata", {})
            similarity = chunk.get("similarity", 0.0)

            # Build source header
            ticker  = meta.get("ticker",          "Unknown")
            date    = meta.get("published_at", meta.get("date", "Unknown"))[:10]
            source  = meta.get("source",           "Unknown")
            sent    = meta.get("sentiment_label",  "")

            header = (
                f"[Source {i} | {ticker} | {date} | {source}"
                f"{' | ' + sent if sent else ''}"
                f" | relevance: {similarity:.2f}]"
            )

            chunk_text = chunk["text"].strip()

            # Truncate individual chunks to avoid one chunk dominating context
            if len(chunk_text) > 1500:
                chunk_text = chunk_text[:1500] + "..."

            formatted_chunk = f"{header}\n{chunk_text}"

            # Stop adding chunks if we'd exceed the context limit
            if total_chars + len(formatted_chunk) > MAX_CONTEXT_CHARS:
                logger.info(
                    f"Context limit reached after {i-1} chunks "
                    f"({total_chars} chars)"
                )
                break

            context_parts.append(formatted_chunk)
            total_chars += len(formatted_chunk)

        return "\n\n---\n\n".join(context_parts)


    def retrieve_for_summary(self, ticker: str, top_k: int = 10) -> str:
        """
        Retrieve and format a broad context about a ticker
        for generating an overall company summary.

        Uses a general query rather than a specific question
        to get a diverse set of recent documents.

        Args:
            ticker: stock symbol to summarize
            top_k:  number of chunks to retrieve

        Returns:
            Formatted context string
        """
        # Broad query captures general company information
        query = (
            f"{ticker} company overview revenue earnings growth "
            f"financial performance outlook risks"
        )

        context, sources = self.retrieve(
            query  = query,
            top_k  = top_k,
            ticker = ticker,
        )

        return context