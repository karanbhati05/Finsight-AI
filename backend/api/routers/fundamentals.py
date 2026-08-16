"""
backend/api/routers/fundamentals.py
Financial Statements, Valuation Ratios, and Balance Sheet endpoints (Powered by FMP).
"""

from fastapi import APIRouter
from backend.providers.fmp_client import FMPClient

router = APIRouter()


@router.get("/income-statement/{ticker}")
async def get_income_statement(ticker: str, limit: int = 5):
    """Get annual income statement history (Revenue, Gross Profit, Operating Income, Net Income, EPS)."""
    statements = await FMPClient.get_income_statement(ticker, limit=limit)
    return {"ticker": ticker.upper(), "statements": statements}


@router.get("/balance-sheet/{ticker}")
async def get_balance_sheet(ticker: str, limit: int = 5):
    """Get annual balance sheet history (Cash, Assets, Debt, Net Debt, Equity)."""
    statements = await FMPClient.get_balance_sheet(ticker, limit=limit)
    return {"ticker": ticker.upper(), "statements": statements}


@router.get("/ratios/{ticker}")
async def get_financial_ratios(ticker: str):
    """Get valuation multiples (P/E, P/S, EV/EBITDA), margins, and analyst price targets."""
    ratios = await FMPClient.get_financial_ratios(ticker)
    return ratios
