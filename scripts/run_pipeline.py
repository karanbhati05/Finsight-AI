# scripts/run_pipeline.py
"""
FinSight AI — Master Pipeline Orchestrator

Runs the complete pipeline for one or more tickers:
    1. Data Ingestion    (price, news, SEC filings)
    2. NLP Processing   (sentiment, NER, summarization)
    3. ML Training      (feature engineering + XGBoost)
    4. Vector Store     (embed documents into ChromaDB)

Usage:
    python scripts/run_pipeline.py --ticker AAPL
    python scripts/run_pipeline.py --ticker AAPL --skip-edgar
    python scripts/run_pipeline.py --tickers AAPL MSFT JPM
    python scripts/run_pipeline.py --ticker AAPL --no-train
"""

import argparse
import time
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from src.ingestion.data_pipeline     import run_ingestion, load_raw_news, load_raw_prices
from src.ingestion.edgar_fetcher     import load_saved_filings
from src.nlp.preprocessor            import preprocess_dataframe
from src.nlp.sentiment               import FinBERTSentiment
from src.nlp.ner                     import FinancialNER
from src.nlp.summarizer              import FinancialSummarizer
from src.ml.feature_engineering      import build_feature_matrix
from src.ml.train                    import train
from src.rag.embedder                import DocumentEmbedder
from src.rag.vector_store            import FinancialVectorStore
from src.utils.logger                import get_logger
from src.utils.helpers               import save_dataframe, load_config
from src.utils.constants             import PROCESSED_DATA_DIR

logger = get_logger(__name__)


def run_nlp_pipeline(
    ticker:         str,
    news_df,
    run_summarizer: bool = True,
):
    """
    Run the full NLP pipeline on raw news DataFrame.

    Steps:
        1. Preprocess text (clean for each model type)
        2. FinBERT sentiment analysis
        3. spaCy Named Entity Recognition
        4. BART summarization (optional — slowest step)

    Args:
        ticker:         stock symbol for logging
        news_df:        raw news DataFrame from ingestion
        run_summarizer: whether to run BART (slow on CPU)

    Returns:
        Enriched DataFrame with sentiment, NER, summary columns
    """
    logger.info(f"─── NLP Pipeline | ticker={ticker} ───")

    # Step 1: Preprocess
    logger.info("Step 2a: Preprocessing text...")
    df = preprocess_dataframe(news_df)

    # Step 2: Sentiment
    logger.info("Step 2b: Running FinBERT sentiment...")
    sentiment_model = FinBERTSentiment()
    df = sentiment_model.analyze_dataframe(df, text_col="content_sentiment")

    # Step 3: NER
    logger.info("Step 2c: Running spaCy NER...")
    ner_model = FinancialNER()
    df = ner_model.analyze_dataframe(df, text_col="content_ner")

    # Step 4: Summarization (optional — BART is slow on CPU)
    if run_summarizer:
        logger.info("Step 2d: Running BART summarization...")
        summarizer = FinancialSummarizer()
        df = summarizer.analyze_dataframe(df, text_col="content_summary")
    else:
        logger.info("Step 2d: Skipping summarization (--no-summarize flag set)")
        df["summary"] = ""

    # Save enriched DataFrame
    out_path = f"{PROCESSED_DATA_DIR}/{ticker}/news_enriched.csv"
    save_dataframe(df, out_path)
    logger.info(f"Enriched news saved: {out_path}")

    return df


def run_vector_store_pipeline(
    ticker:   str,
    news_df,
    filings:  list,
    embedder: DocumentEmbedder     = None,
    store:    FinancialVectorStore = None,
) -> int:
    """
    Embed all documents and store in ChromaDB.

    Processes both news articles and SEC filings.
    Uses upsert to avoid duplicates on re-runs.

    Args:
        ticker:   stock symbol
        news_df:  enriched news DataFrame (with sentiment)
        filings:  list of filing dicts from edgar_fetcher
        embedder: shared embedder instance
        store:    shared vector store instance

    Returns:
        Total number of chunks stored
    """
    logger.info(f"─── Vector Store Pipeline | ticker={ticker} ───")

    embedder = embedder or DocumentEmbedder()
    store    = store    or FinancialVectorStore()

    total_chunks = 0

    # ── Embed news articles ──────────────────────────────────────────────────
    if not news_df.empty:
        logger.info(f"Embedding {len(news_df)} news articles...")

        texts, embeddings, metadatas = embedder.embed_dataframe(
            df            = news_df,
            text_col      = "content",
            metadata_cols = [
                "ticker", "source", "published_at",
                "url", "sentiment_label",
            ],
        )

        # Add source_type so we can filter news vs filings later
        for meta in metadatas:
            meta["source_type"] = "news"
            meta["ticker"]      = ticker

        if texts:
            # Generate stable IDs: ticker + source + chunk position
            ids = [
                f"news_{ticker}_{i}"
                for i in range(len(texts))
            ]
            store.upsert_documents(texts, embeddings, metadatas, ids)
            total_chunks += len(texts)
            logger.info(f"News chunks stored: {len(texts)}")

    # ── Embed SEC filings ────────────────────────────────────────────────────
    if filings:
        logger.info(f"Embedding {len(filings)} SEC filings...")

        for filing in filings:
            filing_text = filing.get("text", "")
            if not filing_text:
                continue

            from src.utils.helpers import chunk_text
            chunks = chunk_text(filing_text, chunk_size=512, overlap=50)

            if not chunks:
                continue

            chunk_embeddings = embedder.embed_documents(chunks)

            metadatas = [{
                "ticker":      ticker,
                "source":      f"SEC {filing.get('form', '10-K')}",
                "source_type": "filing",
                "date":        filing.get("date", ""),
                "published_at": filing.get("date", ""),
                "form":        filing.get("form", ""),
                "sentiment_label": "",
            } for _ in chunks]

            ids = [
                f"filing_{ticker}_{filing.get('date', 'unknown')}_{i}"
                for i in range(len(chunks))
            ]

            store.upsert_documents(chunks, chunk_embeddings, metadatas, ids)
            total_chunks += len(chunks)
            logger.info(
                f"Filing chunks stored: {len(chunks)} | "
                f"{filing.get('form')} {filing.get('date')}"
            )

    logger.info(f"Vector store total chunks for {ticker}: {total_chunks}")
    return total_chunks


def run(
    tickers:        list[str],
    skip_edgar:     bool = False,
    skip_train:     bool = False,
    skip_summarize: bool = False,
    days_back:      int  = 30,
) -> dict:
    """
    Run the complete FinSight AI pipeline for a list of tickers.

    Args:
        tickers:        list of stock symbols to process
        skip_edgar:     skip SEC filing download (saves time)
        skip_train:     skip ML model training
        skip_summarize: skip BART summarization (saves time on CPU)
        days_back:      how many days of news to fetch

    Returns:
        Summary dict with results for each ticker
    """
    start_time = time.time()
    logger.info(f"{'='*60}")
    logger.info(f"FinSight AI Pipeline Starting")
    logger.info(f"Tickers: {tickers}")
    logger.info(f"{'='*60}")

    # Shared components — load once, reuse for all tickers
    embedder = DocumentEmbedder()
    store    = FinancialVectorStore()

    overall_summary = {}

    for ticker in tickers:
        ticker_start = time.time()
        logger.info(f"\n{'─'*50}")
        logger.info(f"Processing: {ticker}")
        logger.info(f"{'─'*50}")

        ticker_summary = {"ticker": ticker, "errors": []}

        try:
            # ── Step 1: Data Ingestion ───────────────────────────────────────
            logger.info(f"Step 1: Data Ingestion")
            ingestion_summary = run_ingestion(
                tickers      = [ticker],
                fetch_edgar_ = not skip_edgar,
                days_back    = days_back,
            )
            ticker_summary["ingestion"] = ingestion_summary

            # ── Step 2: NLP Pipeline ─────────────────────────────────────────
            logger.info(f"Step 2: NLP Pipeline")
            news_df = load_raw_news(ticker)
            enriched_df = run_nlp_pipeline(
                ticker         = ticker,
                news_df        = news_df,
                run_summarizer = not skip_summarize,
            )
            ticker_summary["articles_processed"] = len(enriched_df)

            # ── Step 3: ML Training ──────────────────────────────────────────
            if not skip_train:
                logger.info(f"Step 3: ML Model Training")
                try:
                    price_df = load_raw_prices(ticker)
                    feature_df = build_feature_matrix(price_df, enriched_df)
                    ml_results = train(feature_df, ticker=ticker)
                    ticker_summary["ml"] = {
                        "cv_f1":    round(ml_results["cv_mean_f1"], 3),
                        "test_acc": round(
                            ml_results["test_metrics"].get("accuracy", 0), 3
                        ),
                    }
                    logger.info(
                        f"Model trained | "
                        f"CV F1={ml_results['cv_mean_f1']:.3f} | "
                        f"Test Acc={ml_results['test_metrics'].get('accuracy', 0):.3f}"
                    )
                except Exception as e:
                    logger.error(f"ML training failed for {ticker}: {e}")
                    ticker_summary["errors"].append(f"ml_train: {e}")
            else:
                logger.info("Step 3: Skipping ML training (--no-train flag)")

            # ── Step 4: Vector Store ─────────────────────────────────────────
            logger.info(f"Step 4: Building Vector Store")
            filings = []
            if not skip_edgar:
                filings = load_saved_filings(ticker)

            n_chunks = run_vector_store_pipeline(
                ticker   = ticker,
                news_df  = enriched_df,
                filings  = filings,
                embedder = embedder,
                store    = store,
            )
            ticker_summary["vector_store_chunks"] = n_chunks

        except Exception as e:
            logger.error(f"Pipeline failed for {ticker}: {e}")
            ticker_summary["errors"].append(str(e))

        ticker_time = time.time() - ticker_start
        ticker_summary["time_seconds"] = round(ticker_time, 1)
        overall_summary[ticker] = ticker_summary

        logger.info(
            f"Ticker {ticker} complete in {ticker_time:.1f}s"
        )

    # ── Final Summary ────────────────────────────────────────────────────────
    total_time = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"Pipeline Complete | Total time: {total_time:.1f}s")
    logger.info(f"Vector store total: {store.count()} chunks")
    logger.info(f"\nNext step: streamlit run app/streamlit_app.py")
    logger.info(f"{'='*60}")

    return overall_summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="FinSight AI — End-to-end financial intelligence pipeline"
    )
    parser.add_argument(
        "--ticker",  type=str,
        help="Single ticker to process e.g. AAPL"
    )
    parser.add_argument(
        "--tickers", type=str, nargs="+",
        help="Multiple tickers e.g. AAPL MSFT JPM"
    )
    parser.add_argument(
        "--skip-edgar", action="store_true",
        help="Skip SEC EDGAR filing download"
    )
    parser.add_argument(
        "--no-train", action="store_true",
        help="Skip ML model training"
    )
    parser.add_argument(
        "--no-summarize", action="store_true",
        help="Skip BART summarization (faster on CPU)"
    )
    parser.add_argument(
        "--days-back", type=int, default=30,
        help="Days of news to fetch (default: 30)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Resolve ticker list
    if args.tickers:
        tickers = args.tickers
    elif args.ticker:
        tickers = [args.ticker]
    else:
        # Default to config watchlist
        config  = load_config()
        tickers = config["data"]["tickers"]

    run(
        tickers        = tickers,
        skip_edgar     = args.skip_edgar,
        skip_train     = args.no_train,
        skip_summarize = args.no_summarize,
        days_back      = args.days_back,
    )