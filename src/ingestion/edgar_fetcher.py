# src/ingestion/edgar_fetcher.py

import json
import time
import requests
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import clean_text

logger = get_logger(__name__)

# SEC EDGAR public API — no API key required
EDGAR_BASE    = "https://data.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# SEC requires a descriptive User-Agent header — they block generic ones
# Format: "Company/App contact@email.com"
HEADERS = {
    "User-Agent":      "FinSightAI research@finsight.ai",
    "Accept-Encoding": "gzip, deflate",
    "Host":            "data.sec.gov",
}

# Be polite to the SEC servers — they will block you if you hammer them
REQUEST_DELAY = 0.5


def get_cik(ticker: str) -> str:
    """
    Convert a stock ticker to its SEC CIK (Central Index Key).

    Every company registered with the SEC has a unique CIK number.
    EDGAR uses CIK, not ticker symbols, for all lookups.
    e.g. Apple Inc → CIK 0000320193

    Args:
        ticker: stock symbol e.g. "AAPL"

    Returns:
        10-digit zero-padded CIK string e.g. "0000320193"
    """
    logger.info(f"Looking up CIK for {ticker}...")

    response = requests.get(
        COMPANY_TICKERS_URL,
        headers={"User-Agent": "FinSightAI research@finsight.ai"},
        timeout=10,
    )
    response.raise_for_status()
    companies = response.json()

    # Response is a dict of dicts: {"0": {"cik_str": 320193, "ticker": "AAPL", ...}, ...}
    for entry in companies.values():
        if entry.get("ticker", "").upper() == ticker.upper():
            # CIK must be zero-padded to 10 digits for EDGAR API calls
            cik = str(entry["cik_str"]).zfill(10)
            logger.info(f"Found CIK for {ticker}: {cik}")
            return cik

    raise ValueError(
        f"CIK not found for ticker '{ticker}'.\n"
        f"Check if the ticker is listed on a US exchange and registered with the SEC."
    )


def get_recent_filings(
    cik:       str,
    form_type: str = "10-K",
    limit:     int = 5,
) -> list[dict]:
    """
    Get a list of recent SEC filings for a company.

    Args:
        cik:       10-digit CIK string
        form_type: "10-K" (annual), "10-Q" (quarterly), "8-K" (event)
        limit:     max number of filings to return

    Returns:
        List of dicts with keys: form, accession_number, date, cik
    """
    url = f"{EDGAR_BASE}/submissions/CIK{cik}.json"
    logger.info(f"Fetching filing list | CIK={cik} | form={form_type}")

    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    # Recent filings are in data["filings"]["recent"] as parallel arrays
    # Each index i corresponds to the same filing across all arrays
    recent   = data.get("filings", {}).get("recent", {})
    forms    = recent.get("form",            [])
    accnums  = recent.get("accessionNumber", [])
    dates    = recent.get("filingDate",      [])
    documents= recent.get("primaryDocument", [])

    results = []
    for form, accession, date, doc in zip(forms, accnums, dates, documents):
        if form == form_type and len(results) < limit:
            results.append({
                "form":             form,
                "accession_number": accession,
                # Remove dashes for URL construction: 0001193125-23-277362 → 0001193125232773623
                "accession_clean":  accession.replace("-", ""),
                "date":             date,
                "primary_document": doc,
                "cik":              cik,
            })

    logger.info(f"Found {len(results)} {form_type} filings for CIK {cik}")
    time.sleep(REQUEST_DELAY)
    return results


def fetch_filing_text(cik: str, accession_clean: str, primary_document: str) -> str:
    """
    Download the raw text content of a specific SEC filing.

    EDGAR stores each filing as a folder of documents.
    The primary document is usually an .htm or .txt file
    containing the actual report text.

    Args:
        cik:               10-digit CIK
        accession_clean:   accession number with dashes removed
        primary_document:  filename of the main document e.g. "aapl-20230930.htm"

    Returns:
        Raw text content of the filing (HTML stripped)
    """
    # EDGAR filing URL format:
    # https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION}/{DOCUMENT}
    cik_int = str(int(cik))  # EDGAR Archives uses non-padded CIK in path
    url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_int}/{accession_clean}/{primary_document}"
    )

    logger.info(f"Downloading filing: {url}")

    headers = {"User-Agent": "FinSightAI research@finsight.ai"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    raw = response.text

    # Strip HTML tags — filings are often in .htm format
    # We want clean text for NLP, not HTML markup
    import re
    text = re.sub(r"<[^>]+>",  " ", raw)   # remove HTML tags
    text = re.sub(r"&\w+;",    " ", text)  # remove HTML entities (&amp; &nbsp; etc)
    text = re.sub(r"\s+",      " ", text)  # collapse whitespace
    text = text.strip()

    logger.info(f"Downloaded {len(text):,} characters from filing")
    time.sleep(REQUEST_DELAY)
    return text


def fetch_and_save_filings(
    ticker:    str,
    form_type: str = "10-K",
    limit:     int = 3,
    save_dir:  str = "data/raw",
) -> list[dict]:
    """
    Full pipeline: ticker → CIK → filing list → download text → save.

    Each filing is saved as a JSON file containing both metadata
    and the cleaned text content.

    Args:
        ticker:    stock symbol
        form_type: SEC form type
        limit:     max filings to download
        save_dir:  base directory for saving

    Returns:
        List of filing metadata dicts (with text included)
    """
    logger.info(f"Starting EDGAR fetch | ticker={ticker} | form={form_type}")

    # Step 1: Get CIK
    cik = get_cik(ticker)

    # Step 2: Get list of recent filings
    filings = get_recent_filings(cik, form_type=form_type, limit=limit)

    if not filings:
        logger.warning(f"No {form_type} filings found for {ticker}")
        return []

    # Step 3: Download text for each filing
    save_path = Path(save_dir) / ticker / "filings"
    save_path.mkdir(parents=True, exist_ok=True)

    results = []
    for filing in filings:
        try:
            text = fetch_filing_text(
                cik               = filing["cik"],
                accession_clean   = filing["accession_clean"],
                primary_document  = filing["primary_document"],
            )

            filing["text"]          = text
            filing["ticker"]        = ticker
            filing["char_count"]    = len(text)
            filing["word_count"]    = len(text.split())

            # Save individual filing as JSON
            filename = save_path / f"{form_type}_{filing['date']}.json"
            with open(filename, "w", encoding="utf-8") as f:
                # Don't save full text in JSON listing — save separately
                meta = {k: v for k, v in filing.items() if k != "text"}
                json.dump(meta, f, indent=2)

            # Save text separately for easy loading
            text_file = save_path / f"{form_type}_{filing['date']}.txt"
            text_file.write_text(text, encoding="utf-8")

            results.append(filing)
            logger.info(
                f"Saved {form_type} filing | date={filing['date']} | "
                f"words={filing['word_count']:,}"
            )

        except Exception as e:
            # Don't let one bad filing kill the whole batch
            logger.error(f"Failed to fetch filing {filing['accession_number']}: {e}")
            continue

    logger.info(f"EDGAR fetch complete | {len(results)}/{len(filings)} filings saved")
    return results


def load_saved_filings(ticker: str, form_type: str = "10-K", data_dir: str = "data/raw") -> list[dict]:
    """
    Load previously downloaded filing texts from disk.
    Used by build_vector_store.py to avoid re-downloading.

    Returns:
        List of dicts with 'text', 'date', 'form', 'ticker' keys
    """
    filings_dir = Path(data_dir) / ticker / "filings"

    if not filings_dir.exists():
        logger.warning(f"No filings directory found for {ticker}. Run fetch_and_save_filings first.")
        return []

    results = []
    for txt_file in sorted(filings_dir.glob(f"{form_type}_*.txt")):
        date = txt_file.stem.replace(f"{form_type}_", "")
        text = txt_file.read_text(encoding="utf-8")
        results.append({
            "ticker":    ticker,
            "form":      form_type,
            "date":      date,
            "text":      text,
            "source":    f"SEC {form_type}",
            "word_count": len(text.split()),
        })
        logger.info(f"Loaded filing: {txt_file.name} | {len(text.split()):,} words")

    return results