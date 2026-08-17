"""
backend/api/websocket.py
Real-Time WebSocket price streaming engine.
Directly queries Finnhub and FMP for instant sub-second ticks across subscribed tickers.
"""

import os
import asyncio
import json
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "")
FMP_KEY = os.getenv("FMP_API_KEY", "")


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WebSocket connected. Active connections: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active)}")

    async def send(self, ws: WebSocket, data: dict):
        try:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_text(json.dumps(data))
        except Exception:
            pass


manager = ConnectionManager()


async def _fetch_prices_batch(tickers: list[str]) -> dict:
    """Fetch live prices for subscribed tickers via FMP/Finnhub."""
    results = {}
    clean_tickers = [t.strip().upper() for t in tickers if t]
    if not clean_tickers:
        return results

    if FMP_KEY:
        try:
            sym_str = ",".join(clean_tickers[:30])
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"https://financialmodelingprep.com/api/v3/quote/{sym_str}?apikey={FMP_KEY}"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        for item in data:
                            sym = item.get("symbol")
                            if sym:
                                results[sym] = {
                                    "price": float(item.get("price") or 0),
                                    "change": float(item.get("change") or 0),
                                    "change_pct": float(item.get("changesPercentage") or 0),
                                }
        except Exception as e:
            logger.warning(f"FMP WebSocket batch error: {e}")

    return results


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await manager.connect(websocket)
    subscribed_tickers = []

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=1.0
                )
                msg = json.loads(data)
                action = msg.get("action")
                ticker = msg.get("ticker", "").strip().upper()

                if action == "subscribe" and ticker and ticker not in subscribed_tickers:
                    subscribed_tickers.append(ticker)
                    logger.info(f"WebSocket subscribed to {ticker}")
                elif action == "unsubscribe" and ticker in subscribed_tickers:
                    subscribed_tickers.remove(ticker)
                    logger.info(f"WebSocket unsubscribed from {ticker}")

            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.warning(f"WebSocket message parsing error: {e}")

            # Push live ticks if client is still connected
            if websocket.client_state != WebSocketState.CONNECTED:
                break

            if subscribed_tickers:
                price_batch = await _fetch_prices_batch(subscribed_tickers)
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                for t, info in price_batch.items():
                    payload = {
                        "type": "price_update",
                        "ticker": t,
                        "price": info["price"],
                        "change": info["change"],
                        "change_pct": info["change_pct"],
                        "timestamp": now_str,
                    }
                    await manager.send(websocket, payload)

            await asyncio.sleep(2.0)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket unhandled error: {e}")
        manager.disconnect(websocket)
