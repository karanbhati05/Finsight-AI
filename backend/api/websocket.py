"""
backend/api/websocket.py
WebSocket endpoint for live price streaming with non-blocking thread pool execution.
"""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import yfinance as yf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
ws_executor = ThreadPoolExecutor(max_workers=5)


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
        await ws.send_text(json.dumps(data))


manager = ConnectionManager()


def _fetch_single_price(ticker: str) -> tuple[str, dict]:
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        last_price = float(info.last_price or 0)
        prev_close = float(info.previous_close or 0)
        change = round(last_price - prev_close, 2)
        change_pct = round((change / prev_close * 100), 2) if prev_close else 0

        return ticker, {
            "price": round(last_price, 2),
            "change": change,
            "change_pct": change_pct,
        }
    except Exception:
        return ticker, {"price": 0, "change": 0, "change_pct": 0}


async def fetch_prices_async(tickers: list[str]) -> dict:
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(ws_executor, _fetch_single_price, t) for t in tickers]
    results = await asyncio.gather(*tasks)
    return dict(results)


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

                if msg.get("action") == "subscribe":
                    subscribed_tickers = msg.get("tickers", [])
                    if subscribed_tickers:
                        prices = await fetch_prices_async(subscribed_tickers)
                        await manager.send(websocket, {
                            "type": "price_update",
                            "prices": prices,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })

                elif msg.get("action") == "unsubscribe":
                    subscribed_tickers = []

            except asyncio.TimeoutError:
                pass

            if subscribed_tickers:
                prices = await fetch_prices_async(subscribed_tickers)
                await manager.send(websocket, {
                    "type": "price_update",
                    "prices": prices,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
