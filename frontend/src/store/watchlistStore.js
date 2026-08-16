import { create } from 'zustand'
import { getWatchlist, addToWatchlist, removeFromWatchlist } from '../api/portfolio'

const useWatchlistStore = create((set, get) => ({
  watchlist: [],
  loading:   false,
  error:     null,

  fetchWatchlist: async () => {
    set({ loading: true, error: null })
    try {
      const data = await getWatchlist()
      set({ watchlist: data.watchlist || [], loading: false })
    } catch (err) {
      console.error('Failed to fetch watchlist:', err)
      set({ error: err.message || 'Failed to load watchlist', loading: false })
    }
  },

  addTicker: async (ticker) => {
    if (!ticker) return
    const upper = ticker.toUpperCase()
    try {
      await addToWatchlist(upper)
      await get().fetchWatchlist()
    } catch (err) {
      console.error(`Failed to add ${upper} to watchlist:`, err)
    }
  },

  removeTicker: async (ticker) => {
    if (!ticker) return
    const upper = ticker.toUpperCase()
    // Optimistic UI update
    set(state => ({
      watchlist: state.watchlist.filter(item => item.ticker !== upper)
    }))
    try {
      await removeFromWatchlist(upper)
    } catch (err) {
      console.error(`Failed to remove ${upper} from watchlist:`, err)
      get().fetchWatchlist() // rollback on error
    }
  },

  updateLivePrice: (ticker, { price, change, change_pct }) => {
    set(state => ({
      watchlist: state.watchlist.map(item => {
        if (item.ticker.toUpperCase() === ticker.toUpperCase()) {
          return {
            ...item,
            price:      price !== undefined ? price : item.price,
            change:     change !== undefined ? change : item.change,
            change_pct: change_pct !== undefined ? change_pct : item.change_pct,
            direction:  change >= 0 ? 'up' : 'down',
          }
        }
        return item
      })
    }))
  }
}))

export default useWatchlistStore
