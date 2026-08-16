"""
backend/api/routers/macro.py
Macroeconomic Radar (Powered by FRED - Federal Reserve Economic Data).
"""

from fastapi import APIRouter
from backend.providers.fred_client import FREDMacroClient

router = APIRouter()


@router.get("/dashboard")
async def get_macro_dashboard():
    """Get Treasury Yields, Fed Funds Rate, Inflation, Unemployment, and Macro Assessment."""
    data = await FREDMacroClient.get_macro_dashboard()
    return data
