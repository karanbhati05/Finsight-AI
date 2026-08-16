import { create } from 'zustand'

let idCounter = 0
const genId = () => `msg_${++idCounter}_${Date.now()}`

const useResearchStore = create((set, get) => ({
  // State
  messages:  [],
  sessionId: `session_${Date.now()}`,
  loading:   false,
  ticker:    'AAPL',

  // Actions
  addMessage: (role, content, sources = []) =>
    set(state => ({
      messages: [...state.messages, { role, content, sources, id: genId() }]
    })),

  setLoading: (loading) => set({ loading }),
  setTicker:  (ticker)  => set({ ticker }),

  clearHistory: () => set({
    messages:  [],
    sessionId: `session_${Date.now()}`,
  }),
}))

export default useResearchStore
