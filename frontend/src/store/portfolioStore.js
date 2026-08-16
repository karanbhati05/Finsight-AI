import { create } from 'zustand'
import { getPortfolio, addPortfolioHolding, removePortfolioHolding } from '../api/portfolio'

const usePortfolioStore = create((set, get) => ({
  holdings:       [],
  totalValue:     0,
  totalPnL:       0,
  totalPnLPct:    0,
  loading:        false,
  error:          null,
  isAddModalOpen: false,

  setAddModalOpen: (isOpen) => set({ isAddModalOpen: Boolean(isOpen) }),

  fetchPortfolio: async () => {
    set({ loading: true, error: null })
    try {
      const data = await getPortfolio()
      set({
        holdings:    data.holdings || [],
        totalValue:  data.total_value || 0,
        totalPnL:    data.total_pnl || 0,
        totalPnLPct: data.total_pnl_pct || 0,
        loading:     false,
      })
    } catch (err) {
      console.error('Failed to fetch portfolio:', err)
      set({ error: err.message || 'Failed to load portfolio', loading: false })
    }
  },

  addPosition: async (ticker, shares, buyPrice) => {
    try {
      await addPortfolioHolding(ticker, shares, buyPrice)
      await get().fetchPortfolio()
      set({ isAddModalOpen: false })
    } catch (err) {
      console.error('Failed to add portfolio holding:', err)
      throw err
    }
  },

  removePosition: async (ticker) => {
    if (!ticker) return
    const upper = ticker.toUpperCase()
    // Optimistic UI update
    set(state => ({
      holdings: state.holdings.filter(h => h.ticker !== upper)
    }))
    try {
      await removePortfolioHolding(upper)
      await get().fetchPortfolio()
    } catch (err) {
      console.error('Failed to remove portfolio holding:', err)
      get().fetchPortfolio()
    }
  },

  updateLivePrice: (ticker, { price }) => {
    if (!price) return
    set(state => {
      let totalVal = 0
      let totalCost = 0

      const updatedHoldings = state.holdings.map(item => {
        if (item.ticker.toUpperCase() === ticker.toUpperCase()) {
          const current = Number(price)
          const marketValue = Number((item.shares * current).toFixed(2))
          const cost = item.shares * item.buy_price
          const pnl = Number((marketValue - cost).toFixed(2))
          const pnlPct = cost > 0 ? Number(((pnl / cost) * 100).toFixed(2)) : 0

          totalVal += marketValue
          totalCost += cost

          return {
            ...item,
            current,
            market_value: marketValue,
            pnl,
            pnl_pct:      pnlPct,
            direction:    pnl >= 0 ? 'up' : 'down',
          }
        }

        const cost = item.shares * item.buy_price
        totalVal += (item.market_value || 0)
        totalCost += cost
        return item
      })

      const totalPnL = Number((totalVal - totalCost).toFixed(2))
      const totalPnLPct = totalCost > 0 ? Number(((totalPnL / totalCost) * 100).toFixed(2)) : 0

      return {
        holdings:    updatedHoldings,
        totalValue:  Number(totalVal.toFixed(2)),
        totalPnL,
        totalPnLPct,
      }
    })
  }
}))

export default usePortfolioStore
