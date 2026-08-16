import { create } from 'zustand'

const useMarketStore = create((set) => ({
  // State
  activeRegion: 'india',
  activeTicker: 'AAPL',
  indices: [],
  sectors: [],
  indicesLoading: false,
  sectorsLoading: false,
  indicesError: null,
  sectorsError: null,

  // Actions
  setActiveRegion: (region) => set({ activeRegion: region, indicesError: null, sectorsError: null }),
  setActiveTicker: (ticker) => set({ activeTicker: ticker }),
  setIndices: (indices) => set({ indices, indicesLoading: false, indicesError: null }),
  setSectors: (sectors) => set({ sectors, sectorsLoading: false, sectorsError: null }),
  setIndicesLoading: (loading = true) => set({ indicesLoading: loading, indicesError: null }),
  setSectorsLoading: (loading = true) => set({ sectorsLoading: loading, sectorsError: null }),
  setIndicesError: (error) => set({ indicesError: error, indicesLoading: false }),
  setSectorsError: (error) => set({ sectorsError: error, sectorsLoading: false }),
}))

export default useMarketStore
