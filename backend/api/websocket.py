"""
backend/api/websocket.py
WebSocket endpoint for live price streaming.

Clients connect to ws://localhost:8000/ws/prices, send a subscribe
message with a list of tickers, and receive price updates every 10 seconds.

Protocol:
    Client → Server: {"action": "subscribe", "tickers": ["AAPL", "MSFT"]}
    Server → Client: {"type": "price_update", "prices": {...}, "timestamp": "..."}
"""

import asyncio
import json
from datetime import datetime, timezone
import yfinance as yf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    """
    Manages active WebSocket connections.

    In production, use Redis pub/sub so multiple backend instances
    can share subscription state.
    """

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


def fetch_prices(tickers: list[str]) -> dict:
    """
    Fetch current prices for a list of tickers.
    Returns {ticker: {price, change, change_pct}} dict.
    """
    prices = {}
    for ticker in tickers:
        try:
            t    = yf.Ticker(ticker)
            info = t.fast_info
            last_price    = float(info.last_price or 0)
            prev_close    = float(info.previous_close or 0)
            change        = round(last_price - prev_close, 2)
            change_pct    = round((change / prev_close * 100), 2) if prev_close else 0

            prices[ticker] = {
                "price":      round(last_price, 2),
                "change":     change,
                "change_pct": change_pct,
            }
        except Exception as e:
            logger.warning(f"Price fetch failed for {ticker}: {e}")
            prices[ticker] = {"price": 0, "change": 0, "change_pct": 0}
    return prices


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    WebSocket endpoint for live price streaming.

    Flow:
        1. Client connects
        2. Client sends subscribe message with ticker list
        3. Server pushes price updates every 10 seconds
        4. Client can update subscription anytime by sending another subscribe message
    """
    await manager.connect(websocket)
    subscribed_tickers = []

    try:
        while True:
            try:
                # Wait for subscription message (non-blocking with 1s timeout)
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=1.0
                )
                msg = json.loads(data)

                if msg.get("action") == "subscribe":
                    subscribed_tickers = msg.get("tickers", [])
                    logger.info(f"WebSocket subscribed to: {subscribed_tickers}")

                    # Send immediate price update on subscribe
                    if subscribed_tickers:
                        prices = fetch_prices(subscribed_tickers)
                        await manager.send(websocket, {
                            "type":      "price_update",
                            "prices":    prices,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })

                elif msg.get("action") == "unsubscribe":
                    subscribed_tickers = []
                    logger.info("WebSocket unsubscribed from all tickers")

            except asyncio.TimeoutError:
                pass  # No message received — continue to price push

            # Push prices every 10 seconds if subscribed
            if subscribed_tickers:
                prices = fetch_prices(subscribed_tickers)
                await manager.send(websocket, {
                    "type":      "price_update",
                    "prices":    prices,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
