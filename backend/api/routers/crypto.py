"""
backend/api/routers/crypto.py
Cryptocurrency Market and Forex Currency Rates (Powered by CoinGecko).
"""

from fastapi import APIRouter
from backend.providers.coingecko_client import CryptoForexClient

router = APIRouter()


@router.get("/top")
async def get_top_crypto(limit: int = 20):
    """Get top cryptocurrencies by market capitalization with 24h volume and 7d sparkline."""
    coins = await CryptoForexClient.get_top_crypto(limit=limit)
    return {"coins": coins}


@router.get("/forex")
async def get_forex_rates():
    """Get live foreign exchange rates against USD."""
    rates = await CryptoForexClient.get_forex_rates()
    return {"base": "USD", "rates": rates}
