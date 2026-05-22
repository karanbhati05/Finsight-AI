# scripts/build_vector_store.py
"""
Embed all documents (news + SEC filings) into ChromaDB.

Usage:
    python scripts/build_vector_store.py --ticker AAPL
    python scripts/build_vector_store.py --ticker AAPL --rebuild
    python scripts/build_vector_store.py --tickers AAPL MSFT JPM
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from src.rag.embedder      import DocumentEmbedder, chunk_text
from src.rag.vector_store  import FinancialVectorStore
from src.utils.logger      import get_logger
from src.utils.constants   import PROCESSED_DATA_DIR, RAW_DATA_DIR

logger = get_logger(__name__)


def embed_news(
    ticker:   str,
    embedder: DocumentEmbedder,
    store:    FinancialVectorStore,
) -> int:
    """Embed news articles for a ticker into ChromaDB."""

    news_path = Path(PROCESSED_DATA_DIR) / ticker / "news_enriched.csv"
    if not news_path.exists():
        logger.warning(f"No enriched news found for {ticker} at {news_path}")
        return 0

    df = pd.read_csv(news_path)
    df["published_at"] = pd.to_datetime(
        df["published_at"], utc=True, errors="coerce"
    )

    logger.info(f"Embedding {len(df)} news articles for {ticker}...")

    texts, embeddings, metadatas = embedder.embed_dataframe(
        df            = df,
        text_col      = "content",
        metadata_cols = [
            "ticker", "source", "published_at",
            "url", "sentiment_label",
        ],
    )

    if not texts:
        logger.warning(f"No valid chunks from news for {ticker}")
        return 0

    # Add source type
    for meta in metadatas:
        meta["source_type"] = "news"
        meta["ticker"]      = ticker

    ids = [f"news_{ticker}_{i}" for i in range(len(texts))]
    store.upsert_documents(texts, embeddings, metadatas, ids)

    logger.info(f"News chunks stored: {len(texts)}")
    return len(texts)


def embed_filings(
    ticker:   str,
    embedder: DocumentEmbedder,
    store:    FinancialVectorStore,
) -> int:
    """Embed SEC filings for a ticker into ChromaDB."""

    filings_dir = Path(RAW_DATA_DIR) / ticker / "filings"

    if not filings_dir.exists():
        logger.warning(
            f"No filings directory found for {ticker}. "
            f"Run pipeline with EDGAR enabled first."
        )
        return 0

    txt_files = sorted(filings_dir.glob("*.txt"))
    if not txt_files:
        logger.warning(f"No .txt filing files found in {filings_dir}")
        return 0

    logger.info(f"Found {len(txt_files)} filing files for {ticker}")

    total_chunks = 0

    for txt_file in txt_files:
        # Parse form type and date from filename
        # Format: 10-K_2024-11-01.txt
        stem      = txt_file.stem           # "10-K_2024-11-01"
        parts     = stem.split("_", 1)
        form_type = parts[0] if len(parts) > 0 else "10-K"
        date_str  = parts[1] if len(parts) > 1 else "unknown"

        logger.info(f"Processing: {txt_file.name}")

        # Read filing text
        try:
            text = txt_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Failed to read {txt_file}: {e}")
            continue

        if not text.strip():
            logger.warning(f"Empty filing: {txt_file.name}")
            continue

        word_count = len(text.split())
        logger.info(f"Filing: {form_type} | {date_str} | {word_count:,} words")

        # Chunk the filing
        # Use smaller chunks for filings — they're dense legal text
        chunks = chunk_text(text, chunk_size=400, overlap=60)

        if not chunks:
            continue

        logger.info(f"Created {len(chunks)} chunks from {txt_file.name}")

        # Embed in batches of 50 to avoid memory issues on large filings
        batch_size  = 50
        file_chunks = 0

        for i in range(0, len(chunks), batch_size):
            batch      = chunks[i : i + batch_size]
            batch_embs = embedder.embed_documents(batch, show_progress=False)

            metadatas = [{
                "ticker":          ticker,
                "source":          f"SEC {form_type}",
                "source_type":     "filing",
                "form":            form_type,
                "date":            date_str,
                "published_at":    date_str,
                "sentiment_label": "",
                "url":             "",
                "chunk_idx":       i + j,
                "filing_file":     txt_file.name,
            } for j in range(len(batch))]

            ids = [
                f"filing_{ticker}_{form_type}_{date_str}_{i+j}"
                for j in range(len(batch))
            ]

            store.upsert_documents(batch, batch_embs, metadatas, ids)
            file_chunks  += len(batch)

            logger.info(
                f"  Embedded batch {i//batch_size + 1} | "
                f"chunks {i+1}–{min(i+batch_size, len(chunks))}/{len(chunks)}"
            )

        total_chunks += file_chunks
        logger.info(f"Filing complete: {file_chunks} chunks stored")

    return total_chunks


def build(
    ticker:  str,
    rebuild: bool = False,
) -> dict:
    """
    Build vector store for a single ticker.

    Args:
        ticker:  stock symbol
        rebuild: if True, delete existing chunks and re-embed

    Returns:
        Summary dict
    """
    logger.info(f"{'='*50}")
    logger.info(f"Building vector store for {ticker}")
    logger.info(f"{'='*50}")

    embedder = DocumentEmbedder()
    store    = FinancialVectorStore()

    # Optionally wipe existing data for this ticker
    if rebuild:
        logger.info(f"Rebuilding: deleting existing chunks for {ticker}")
        store.delete_by_ticker(ticker)

    # Embed news
    logger.info("─── Embedding news articles ───")
    news_chunks = embed_news(ticker, embedder, store)

    # Embed filings
    logger.info("─── Embedding SEC filings ───")
    filing_chunks = embed_filings(ticker, embedder, store)

    total = news_chunks + filing_chunks

    summary = {
        "ticker":         ticker,
        "news_chunks":    news_chunks,
        "filing_chunks":  filing_chunks,
        "total_chunks":   total,
        "store_total":    store.count(),
    }

    logger.info(f"\nVector store build complete for {ticker}:")
    logger.info(f"  News chunks:    {news_chunks}")
    logger.info(f"  Filing chunks:  {filing_chunks}")
    logger.info(f"  Total new:      {total}")
    logger.info(f"  Store total:    {store.count()}")

    return summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build ChromaDB vector store from news + SEC filings"
    )
    parser.add_argument(
        "--ticker",  type=str,
        help="Single ticker e.g. AAPL"
    )
    parser.add_argument(
        "--tickers", type=str, nargs="+",
        help="Multiple tickers e.g. AAPL MSFT JPM"
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Delete existing chunks and re-embed from scratch"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.tickers:
        tickers = args.tickers
    elif args.ticker:
        tickers = [args.ticker]
    else:
        tickers = ["AAPL"]

    for ticker in tickers:
        result = build(ticker=ticker, rebuild=args.rebuild)
        print(f"\n{ticker}: {result['total_chunks']} chunks added "
              f"({result['filing_chunks']} from filings)")

    print(f"\nDone. Launch app: streamlit run app/streamlit_app.py")