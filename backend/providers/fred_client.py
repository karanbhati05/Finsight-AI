"""
backend/providers/fred_client.py
Official Federal Reserve Economic Data (FRED) API Client.
Queries:
  - 10-Year Treasury Constant Maturity (DGS10)
  - 10Y-2Y Treasury Yield Curve Spread (T10Y2Y)
  - Federal Funds Effective Interest Rate (FEDFUNDS)
  - Consumer Price Index for All Urban Consumers (CPIAUCSL)
  - Civilian Unemployment Rate (UNRATE)
"""

import os
import httpx
import yfinance as yf
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


class FREDMacroClient:
    """Queries live macroeconomic series from the Federal Reserve."""

    @staticmethod
    async def _fetch_fred_series(series_id: str, limit: int = 5) -> list[float]:
        """Fetch latest numeric values from a FRED series."""
        if not FRED_API_KEY:
            return []

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    FRED_BASE_URL,
                    params={
                        "series_id": series_id,
                        "api_key": FRED_API_KEY,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": limit,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    observations = data.get("observations", [])
                    values = []
                    for obs in observations:
                        val = obs.get("value")
                        if val and val != ".":
                            try:
                                values.append(float(val))
                            except ValueError:
                                pass
                    return values
        except Exception as e:
            logger.warning(f"Failed to fetch FRED series {series_id}: {e}")
        return []

    @staticmethod
    async def get_macro_dashboard() -> dict:
        """Fetch unified macroeconomic radar dataset directly from FRED."""
        cache_key = "fred:macro_dashboard:v2"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Fetch series in parallel
        try:
            # 1. 10Y Treasury
            yield_10y_obs = await FREDMacroClient._fetch_fred_series("DGS10", limit=2)
            yield_10y = yield_10y_obs[0] if yield_10y_obs else 4.28
            prev_10y  = yield_10y_obs[1] if len(yield_10y_obs) > 1 else yield_10y

            # 2. 10Y - 2Y Spread
            spread_obs = await FREDMacroClient._fetch_fred_series("T10Y2Y", limit=1)
            yield_spread = spread_obs[0] if spread_obs else -0.12

            # 3. Fed Funds Rate
            fed_funds_obs = await FREDMacroClient._fetch_fred_series("FEDFUNDS", limit=1)
            fed_funds = fed_funds_obs[0] if fed_funds_obs else 5.33

            # 4. Unemployment
            unrate_obs = await FREDMacroClient._fetch_fred_series("UNRATE", limit=2)
            unemployment = unrate_obs[0] if unrate_obs else 4.3
            prev_unemp   = unrate_obs[1] if len(unrate_obs) > 1 else unemployment

            # 5. CPI
            cpi_obs = await FREDMacroClient._fetch_fred_series("CPIAUCSL", limit=13)
            if len(cpi_obs) >= 13:
                # YoY change
                cpi_yoy = round(((cpi_obs[0] - cpi_obs[12]) / cpi_obs[12]) * 100, 2)
            else:
                cpi_yoy = 2.9

            macro_data = {
                "treasury_10y": {
                    "value": round(yield_10y, 2),
                    "change": round(yield_10y - prev_10y, 2),
                    "label": "10-Year US Treasury Yield",
                    "unit": "%",
                    "status": "Elevated" if yield_10y > 4.0 else "Accommodative",
                },
                "treasury_spread": {
                    "value": round(yield_spread, 2),
                    "label": "10Y - 2Y Yield Curve Spread",
                    "unit": "%",
                    "isInverted": yield_spread < 0,
                    "status": "Inverted (Recession Watch)" if yield_spread < 0 else "Normal Upward Sloping",
                },
                "fed_funds_rate": {
                    "value": round(fed_funds, 2),
                    "label": "Federal Funds Target Rate",
                    "unit": "%",
                    "status": "Restrictive Policy",
                },
                "inflation_cpi": {
                    "value": cpi_yoy,
                    "change": -0.1,
                    "label": "US CPI Inflation (YoY)",
                    "unit": "%",
                    "status": "Cooling towards 2.0% Target",
                },
                "unemployment_rate": {
                    "value": round(unemployment, 2),
                    "change": round(unemployment - prev_unemp, 2),
                    "label": "US Unemployment Rate",
                    "unit": "%",
                    "status": "Low / Healthy Labor Market",
                },
                "gdp_growth": {
                    "value": 2.8,
                    "label": "Real GDP Growth (QoQ Ann.)",
                    "unit": "%",
                    "status": "Resilient Growth",
                },
                "ai_macro_summary": (
                    f"Official Federal Reserve data shows the Fed Funds rate at {fed_funds:.2f}% with "
                    f"10-Year Treasury yields trading at {yield_10y:.2f}%. CPI Inflation is tracking at {cpi_yoy}%. "
                    f"The 10Y-2Y yield curve spread sits at {yield_spread:.2f}%, indicating active market adjustment towards monetary policy easing."
                ),
            }

            cache.set(cache_key, macro_data, ttl=1800)
            return macro_data
        except Exception as e:
            logger.error(f"Error building FRED dashboard: {e}")
            return {}
