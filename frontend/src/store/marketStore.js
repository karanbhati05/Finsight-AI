import { create } from 'zustand'

const INITIAL_INDICES = [
  {
    symbol: '^NSEI',
    name: 'NIFTY 50',
    value: 24366.00,
    change: -29.85,
    change_pct: -0.12,
    direction: 'down',
    sparkline: [24410, 24380, 24350, 24320, 24340, 24360, 24395, 24366],
  },
  {
    symbol: '^BSESN',
    name: 'SENSEX',
    value: 79800.25,
    change: -71.40,
    change_pct: -0.09,
    direction: 'down',
    sparkline: [79950, 79900, 79820, 79750, 79810, 79880, 79800.25],
  },
  {
    symbol: '^NSEBANK',
    name: 'Nifty Bank',
    value: 50450.10,
    change: 120.30,
    change_pct: 0.24,
    direction: 'up',
    sparkline: [50200, 50280, 50350, 50410, 50450.10],
  },
  {
    symbol: '^CNXIT',
    name: 'Nifty IT',
    value: 41200.80,
    change: -180.50,
    change_pct: -0.44,
    direction: 'down',
    sparkline: [41500, 41420, 41350, 41280, 41200.80],
  },
]

const INITIAL_SECTORS = [
  { symbol: 'NIFTY_AUTO.NS', label: 'Auto', value: 29207.90, change_pct: -0.63, direction: 'down' },
  { symbol: 'NIFTY_ENERGY.NS', label: 'Energy & Utilities', value: 38554.20, change_pct: -0.35, direction: 'down' },
  { symbol: 'NIFTY_FIN_SERV.NS', label: 'Financials', value: 26213.65, change_pct: -0.43, direction: 'down' },
  { symbol: 'NIFTY_FMCG.NS', label: 'Consumer Staples', value: 48615.05, change_pct: 0.15, direction: 'up' },
  { symbol: 'NIFTY_INFRA.NS', label: 'Industrials', value: 8420.30, change_pct: -0.22, direction: 'down' },
  { symbol: 'NIFTY_IT.NS', label: 'Technology', value: 41200.80, change_pct: -0.44, direction: 'down' },
]

const useMarketStore = create((set) => ({
  // State
  activeRegion: 'india',
  activeTicker: 'AAPL',
  indices: INITIAL_INDICES,
  sectors: INITIAL_SECTORS,
  indicesLoading: false,
  sectorsLoading: false,
  indicesError: null,
  sectorsError: null,

  // Actions
  setActiveRegion: (region) => set({ activeRegion: region, indicesError: null, sectorsError: null }),
  setActiveTicker: (ticker) => set({ activeTicker: ticker }),
  setIndices: (indices) => set({ indices: indices?.length > 0 ? indices : INITIAL_INDICES, indicesLoading: false, indicesError: null }),
  setSectors: (sectors) => set({ sectors: sectors?.length > 0 ? sectors : INITIAL_SECTORS, sectorsLoading: false, sectorsError: null }),
  setIndicesLoading: (loading = true) => set({ indicesLoading: loading, indicesError: null }),
  setSectorsLoading: (loading = true) => set({ sectorsLoading: loading, sectorsError: null }),
  setIndicesError: (error) => set({ indicesError: error, indicesLoading: false }),
  setSectorsError: (error) => set({ sectorsError: error, sectorsLoading: false }),
}))

export default useMarketStore
