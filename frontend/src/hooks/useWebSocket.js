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

      const envApi = import.meta.env.VITE_API_URL || ''
      let wsUrl = 'ws://localhost:8000/ws/prices'

      if (envApi.startsWith('http')) {
        // Strip http(s)://, strip /api, strip trailing slashes
        const cleanHost = envApi
          .replace(/^https?:\/\//, '')
          .replace(/\/api\/?$/, '')
          .replace(/\/+$/, '')
        const protocol = envApi.startsWith('https') ? 'wss:' : 'ws:'
        wsUrl = `${protocol}//${cleanHost}/ws/prices`
      } else if (window.location.protocol === 'https:') {
        wsUrl = `wss://${window.location.host}/ws/prices`
      }

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
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
          }
        }

        ws.onerror = () => {
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close()
          }
        }
      } catch (err) {
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

  useEffect(() => {
    if (isConnected && allTickers.length > 0) {
      subscribeToTickers(allTickers)
    }
  }, [isConnected, allTickers.join(','), subscribeToTickers])

  return { isConnected, lastTimestamp }
}
