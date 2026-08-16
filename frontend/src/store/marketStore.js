import { create } from 'zustand'

const useMarketStore = create((set) => ({
  // State
  activeRegion:   'india',
  activeTicker:   'AAPL',
  indices:        [],
  sectors:        [],
  indicesLoading: false,
  sectorsLoading: false,

  // Actions
  setActiveRegion:  (region)  => set({ activeRegion: region }),
  setActiveTicker:  (ticker)  => set({ activeTicker: ticker }),
  setIndices:       (indices) => set({ indices, indicesLoading: false }),
  setSectors:       (sectors) => set({ sectors, sectorsLoading: false }),
  setIndicesLoading: ()       => set({ indicesLoading: true }),
  setSectorsLoading: ()       => set({ sectorsLoading: true }),
}))

export default useMarketStore
