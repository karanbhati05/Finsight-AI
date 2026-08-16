import { useState, useEffect, useRef, useCallback } from 'react'
import useWatchlistStore from '../store/watchlistStore'
import usePortfolioStore from '../store/portfolioStore'
import useMarketStore from '../store/marketStore'

export function useWebSocket() {
  const [isConnected, setIsConnected]     = useState(false)
  const [lastTimestamp, setLastTimestamp] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  const watchlist = useWatchlistStore(s => s.watchlist)
  const holdings  = usePortfolioStore(s => s.holdings)
  const indices   = useMarketStore(s => s.indices)
  const updateWatchlistPrice = useWatchlistStore(s => s.updateLivePrice)
  const updatePortfolioPrice = usePortfolioStore(s => s.updateLivePrice)

  // Collect unique symbols to subscribe
  const allTickers = Array.from(
    new Set([
      ...watchlist.map(w => w.ticker),
      ...holdings.map(h => h.ticker),
      ...indices.map(i => i.symbol),
    ].filter(Boolean))
  )

  const subscribeToTickers = useCallback((tickers) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && tickers.length > 0) {
      try {
        wsRef.current.send(JSON.stringify({
          action: 'subscribe',
          tickers,
        }))
      } catch (err) {
        console.warn('Failed to send subscribe message:', err)
      }
    }
  }, [])

  useEffect(() => {
    let unmounted = false

    const connectWebSocket = () => {
      if (unmounted) return

      // Determine websocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = process.env.NODE_ENV === 'production'
        ? `${protocol}//${window.location.host}/ws/prices`
        : `ws://localhost:8000/ws/prices`

      try {
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          if (!unmounted) {
            setIsConnected(true)
            if (allTickers.length > 0) {
              subscribeToTickers(allTickers)
            }
          }
        }

        ws.onmessage = (event) => {
          if (unmounted) return
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'price_update' && data.prices) {
              setLastTimestamp(data.timestamp || new Date().toISOString())

              // Broadcast prices to watchlist and portfolio stores
              Object.entries(data.prices).forEach(([symbol, quote]) => {
                updateWatchlistPrice(symbol, quote)
                updatePortfolioPrice(symbol, quote)
              })
            }
          } catch (err) {
            console.error('Error parsing WebSocket message:', err)
          }
        }

        ws.onclose = () => {
          if (!unmounted) {
            setIsConnected(false)
            // Auto reconnect after 4 seconds
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, 4000)
          }
        }

        ws.onerror = (err) => {
          console.warn('WebSocket connection error:', err)
          ws.close()
        }
      } catch (err) {
        console.warn('WebSocket init failed, retrying in 5s:', err)
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
      }
    }

    connectWebSocket()

    return () => {
      unmounted = true
      clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  // Re-subscribe when the list of tickers changes
  useEffect(() => {
    if (isConnected && allTickers.length > 0) {
      subscribeToTickers(allTickers)
    }
  }, [isConnected, allTickers.join(','), subscribeToTickers])

  return { isConnected, lastTimestamp }
}
