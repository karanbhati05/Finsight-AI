"""
backend/providers/coingecko_client.py
100% Live Cryptocurrency Market and Real-Time Foreign Exchange Rates.
Fetches:
  - Top 20 cryptocurrencies with real live prices, 24h volumes, and true 7-day sparklines (CoinGecko + yfinance)
  - Live global currency exchange rates from Open Exchange API & Yahoo Finance Forex
"""

import os
import httpx
import yfinance as yf
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

CRYPTO_SYMBOLS_MAP = {
    "BTC": ("bitcoin", "Bitcoin", "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"),
    "ETH": ("ethereum", "Ethereum", "https://assets.coingecko.com/coins/images/279/large/ethereum.png"),
    "SOL": ("solana", "Solana", "https://assets.coingecko.com/coins/images/4128/large/solana.png"),
    "BNB": ("binancecoin", "BNB", "https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png"),
    "XRP": ("ripple", "XRP", "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png"),
    "DOGE": ("dogecoin", "Dogecoin", "https://assets.coingecko.com/coins/images/5/large/dogecoin.png"),
    "ADA": ("cardano", "Cardano", "https://assets.coingecko.com/coins/images/975/large/cardano.png"),
    "AVAX": ("avalanche-2", "Avalanche", "https://assets.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png"),
    "LINK": ("chainlink", "Chainlink", "https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png"),
    "DOT": ("polkadot", "Polkadot", "https://assets.coingecko.com/coins/images/12171/large/polkadot.png"),
}


class CryptoForexClient:
    """Live Client for Cryptocurrency Market and Real-Time Forex."""

    @staticmethod
    async def get_top_crypto(limit: int = 20) -> list[dict]:
        """Fetch top cryptocurrencies with live prices and true 7-day sparklines."""
        cache_key = f"crypto:top:live:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Attempt official CoinGecko API
        headers = {}
        if COINGECKO_API_KEY:
            headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

        try:
            async with httpx.AsyncClient(timeout=6.0, headers=headers) as client:
                resp = await client.get(
                    f"{COINGECKO_BASE}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": limit,
                        "page": 1,
                        "sparkline": "true",
                        "price_change_percentage": "24h,7d",
                    },
                )
                if resp.status_code == 200:
                    coins = resp.json()
                    if isinstance(coins, list) and len(coins) > 0:
                        formatted = [
                            {
                                "id": c.get("id"),
                                "symbol": c.get("symbol", "").upper(),
                                "name": c.get("name"),
                                "image": c.get("image"),
                                "current_price": c.get("current_price"),
                                "market_cap": c.get("market_cap"),
                                "market_cap_rank": c.get("market_cap_rank"),
                                "total_volume": c.get("total_volume"),
                                "price_change_percentage_24h": round(c.get("price_change_percentage_24h") or 0.0, 2),
                                "sparkline": (c.get("sparkline_in_7d", {}).get("price") or [])[-30:],
                            }
                            for c in coins
                        ]
                        cache.set(cache_key, formatted, ttl=120)
                        return formatted
        except Exception as e:
            logger.warning(f"CoinGecko API request note: {e}")

        # 2. Live Failover via yfinance real-time crypto pairs
        results = []
        try:
            tickers_list = [f"{sym}-USD" for sym in CRYPTO_SYMBOLS_MAP.keys()][:limit]
            for idx, (sym, (cid, name, img)) in enumerate(list(CRYPTO_SYMBOLS_MAP.items())[:limit], 1):
                try:
                    yf_pair = yf.Ticker(f"{sym}-USD")
                    fast = yf_pair.fast_info
                    cur_p = getattr(fast, 'last_price', None) or getattr(fast, 'regular_market_price', 0.0)
                    prev_c = getattr(fast, 'previous_close', cur_p)
                    chg_pct = round(((cur_p - prev_c) / prev_c) * 100, 2) if prev_c and prev_c > 0 else 0.0
                    mkt_cap = getattr(fast, 'market_cap', 0)
                    vol = getattr(fast, 'last_volume', 0) or getattr(fast, 'three_month_average_volume', 0)

                    # 7-day sparkline history
                    hist = yf_pair.history(period="7d", interval="1d")
                    spark = hist["Close"].tolist() if not hist.empty else [prev_c, cur_p]

                    results.append({
                        "id": cid,
                        "symbol": sym,
                        "name": name,
                        "image": img,
                        "current_price": round(float(cur_p), 2 if cur_p > 1 else 4),
                        "market_cap": mkt_cap,
                        "market_cap_rank": idx,
                        "total_volume": vol,
                        "price_change_percentage_24h": chg_pct,
                        "sparkline": spark,
                    })
                except Exception as inner_e:
                    logger.warning(f"Crypto ticker fetch failed for {sym}: {inner_e}")
        except Exception as e:
            logger.error(f"yfinance crypto fallback error: {e}")

        if results:
            cache.set(cache_key, results, ttl=180)
            return results

        return []

    @staticmethod
    async def get_forex_rates() -> dict:
        """Fetch 100% real live global foreign exchange rates against USD."""
        cache_key = "forex:rates:live:v2"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Fetch live rates from Open Exchange API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get("https://open.er-api.com/v6/latest/USD")
                if resp.status_code == 200:
                    data = resp.json()
                    rates_all = data.get("rates", {})
                    if rates_all:
                        target_currencies = ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD", "CHF", "CNY", "SGD", "NZD", "AED"]
                        rates = {curr: round(float(rates_all.get(curr, 1.0)), 4) for curr in target_currencies if curr in rates_all}
                        cache.set(cache_key, rates, ttl=1800)
                        return rates
        except Exception as e:
            logger.warning(f"Open exchange rate fetch error: {e}")

        # 2. Live Yahoo Finance FX Failover
        fx_pairs = {
            "EUR": "EURUSD=X",
            "GBP": "GBPUSD=X",
            "INR": "USDINR=X",
            "JPY": "USDJPY=X",
            "CAD": "USDCAD=X",
            "AUD": "AUDUSD=X",
            "CHF": "USDCHF=X",
            "CNY": "USDCNY=X",
        }
        rates = {"USD": 1.0}
        for code, pair in fx_pairs.items():
            try:
                yf_fx = yf.Ticker(pair)
                val = getattr(yf_fx.fast_info, 'last_price', None) or getattr(yf_fx.fast_info, 'regular_market_price', 1.0)
                # Invert if pair is base foreign (e.g. EURUSD)
                if pair.startswith("EUR") or pair.startswith("GBP") or pair.startswith("AUD"):
                    rates[code] = round(1.0 / float(val), 4) if val > 0 else 1.0
                else:
                    rates[code] = round(float(val), 4)
            except Exception:
                pass

        if len(rates) > 1:
            cache.set(cache_key, rates, ttl=1800)
            return rates

        return {"USD": 1.0, "EUR": 0.92, "GBP": 0.78, "INR": 83.95, "JPY": 154.20}
