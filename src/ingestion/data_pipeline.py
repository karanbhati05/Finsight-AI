# src/ingestion/data_pipeline.py

import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from src.ingestion.finnhub_fetcher import fetch_company_news, save_finnhub_news
from src.ingestion.yfinance_fetcher import fetch_and_save as fetch_price
from src.ingestion.news_fetcher      import fetch_news, save_news
from src.ingestion.edgar_fetcher     import fetch_and_save_filings
from src.utils.logger   import get_logger
from src.utils.helpers  import load_config, ensure_dirs, save_dataframe
from src.utils.constants import TICKER_COMPANY_MAP, RAW_DATA_DIR, PROCESSED_DATA_DIR

load_dotenv()   # loads .env file so API keys are available as os.getenv(...)
logger = get_logger(__name__)


def run_ingestion(
    tickers:      list[str] = None,
    fetch_news_:  bool = True,
    fetch_price_: bool = True,
    fetch_edgar_: bool = True,
    days_back:    int  = 30,
) -> dict:
    """
    Run the full data ingestion pipeline for all tickers.

    This is the single function called by scripts/run_pipeline.py.
    Each fetch step is independently toggleable — useful when debugging
    or when you want to re-run only one data source.

    Args:
        tickers:       list of stock symbols. If None, uses config watchlist.
        fetch_news_:   whether to fetch news articles
        fetch_price_:  whether to fetch price + technical indicator data
        fetch_edgar_:  whether to fetch SEC filings
        days_back:     news lookback window

    Returns:
        Summary dict with counts of what was fetched
    """
    config = load_config()

    # Use config watchlist if no tickers provided
    if tickers is None:
        tickers = config["data"]["tickers"]

    logger.info(f"Starting ingestion pipeline | tickers={tickers}")

    # Ensure all data directories exist before writing
    ensure_dirs(RAW_DATA_DIR, PROCESSED_DATA_DIR)
    for ticker in tickers:
        ensure_dirs(
            f"{RAW_DATA_DIR}/{ticker}",
            f"{RAW_DATA_DIR}/{ticker}/filings",
            f"{PROCESSED_DATA_DIR}/{ticker}",
        )

    summary = {
        "tickers":          tickers,
        "news_articles":    {},
        "price_rows":       {},
        "edgar_filings":    {},
        "errors":           [],
    }

    # ── Step 1: Price Data ───────────────────────────────────────────────────
    if fetch_price_:
        logger.info("─── Step 1/3: Fetching price data ───")
        for ticker in tickers:
            try:
                df = fetch_price(
                    ticker   = ticker,
                    period   = "1y",
                    save_dir = RAW_DATA_DIR,
                )
                summary["price_rows"][ticker] = len(df)
                logger.info(f"  {ticker}: {len(df)} price rows")
            except Exception as e:
                logger.error(f"  {ticker} price fetch failed: {e}")
                summary["errors"].append(f"price:{ticker}:{e}")

    # ── Step 2: News Articles ────────────────────────────────────────────────
    if fetch_news_:
        logger.info("─── Step 2/3: Fetching news articles ───")
        max_articles = config["data"].get("max_articles_per_ticker", 200)

        for ticker in tickers:
            all_news = []

            # Source A: Finnhub (primary — 1 year history)
            try:
                finnhub_df = fetch_company_news(
                    ticker       = ticker,
                    days_back    = days_back,
                    max_articles = max_articles,
                )
                if not finnhub_df.empty:
                    save_finnhub_news(finnhub_df, ticker)
                    all_news.append(finnhub_df)
                    logger.info(f"  {ticker}: {len(finnhub_df)} Finnhub articles")
            except Exception as e:
                logger.error(f"  {ticker} Finnhub fetch failed: {e}")

            # Source B: NewsAPI (secondary — recent 30 days)
            try:
                newsapi_df = fetch_news(
                    ticker       = ticker,
                    days_back    = min(days_back, 30),
                    max_articles = 50,
                )
                if not newsapi_df.empty:
                    save_news(newsapi_df, ticker)
                    all_news.append(newsapi_df)
                    logger.info(f"  {ticker}: {len(newsapi_df)} NewsAPI articles")
            except Exception as e:
                logger.error(f"  {ticker} NewsAPI fetch failed: {e}")

            # Combine both sources
            if all_news:
                combined = pd.concat(all_news, ignore_index=True)

            # Deduplicate by URL
                combined = combined.drop_duplicates(subset=["url"]).reset_index(drop=True)

            # Save combined
                save_dataframe(combined, f"{RAW_DATA_DIR}/{ticker}/news.csv")
                summary["news_articles"][ticker] = len(combined)
                logger.info(
                    f"  {ticker}: {len(combined)} total articles "
                    f"(after deduplication)"
                )
            else:
                logger.warning(f"  {ticker}: no articles from any source")
                summary["news_articles"][ticker] = 0
    # ── Step 3: SEC Filings ──────────────────────────────────────────────────
    if fetch_edgar_:
        logger.info("─── Step 3/3: Fetching SEC filings ───")
        for ticker in tickers:
            try:
                filings = fetch_and_save_filings(
                    ticker    = ticker,
                    form_type = "10-K",
                    limit     = 2,        # 2 years of annual reports
                    save_dir  = RAW_DATA_DIR,
                )
                summary["edgar_filings"][ticker] = len(filings)
                logger.info(f"  {ticker}: {len(filings)} 10-K filings")
            except Exception as e:
                logger.error(f"  {ticker} EDGAR fetch failed: {e}")
                summary["errors"].append(f"edgar:{ticker}:{e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    total_articles = sum(summary["news_articles"].values())
    total_filings  = sum(summary["edgar_filings"].values())
    total_errors   = len(summary["errors"])

    logger.info(
        f"Ingestion complete | "
        f"articles={total_articles} | "
        f"filings={total_filings} | "
        f"errors={total_errors}"
    )

    if summary["errors"]:
        logger.warning(f"Errors encountered: {summary['errors']}")

    return summary


def load_raw_news(ticker: str) -> pd.DataFrame:
    """Load previously fetched news CSV for a ticker."""
    path = f"{RAW_DATA_DIR}/{ticker}/news.csv"
    if not Path(path).exists():
        raise FileNotFoundError(f"No news data for {ticker}. Run ingestion first.")
    return pd.read_csv(path, parse_dates=["published_at"])


def load_raw_prices(ticker: str) -> pd.DataFrame:
    """Load previously fetched price CSV for a ticker."""
    path = f"{RAW_DATA_DIR}/{ticker}/price_data.csv"
    if not Path(path).exists():
        raise FileNotFoundError(f"No price data for {ticker}. Run ingestion first.")
    return pd.read_csv(path, parse_dates=["date"])