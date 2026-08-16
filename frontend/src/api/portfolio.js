import client from './client'

// ── Watchlist API ──────────────────────────────────────────
export const getWatchlist = () =>
  client.get('/watchlist')

export const addToWatchlist = (ticker) =>
  client.post('/watchlist', { ticker: ticker.toUpperCase() })

export const removeFromWatchlist = (ticker) =>
  client.delete(`/watchlist/${ticker.toUpperCase()}`)

// ── Portfolio API ──────────────────────────────────────────
export const getPortfolio = () =>
  client.get('/portfolio')

export const addPortfolioHolding = (ticker, shares, buyPrice) =>
  client.post('/portfolio', {
    ticker:    ticker.toUpperCase(),
    shares:    Number(shares),
    buy_price: Number(buyPrice),
  })

export const removePortfolioHolding = (ticker) =>
  client.delete(`/portfolio/${ticker.toUpperCase()}`)
