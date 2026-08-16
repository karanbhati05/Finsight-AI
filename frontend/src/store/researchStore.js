import { create } from 'zustand'

let msgCounter = 0
const generateId = () => `msg_${Date.now()}_${++msgCounter}`
const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`

const useResearchStore = create((set, get) => ({
  // State
  messages:     [],
  sessionId:    generateSessionId(),
  loading:      false,
  activeTicker: 'AAPL',

  // Actions
  addMessage: (role, content, sources = []) => {
    const newMessage = {
      id:        generateId(),
      role,      // 'user' | 'assistant'
      content,
      sources:   Array.isArray(sources) ? sources : [],
      timestamp: new Date().toISOString(),
    }
    set(state => ({
      messages: [...state.messages, newMessage],
    }))
    return newMessage.id
  },

  setLoading: (loading) => set({ loading: Boolean(loading) }),

  setActiveTicker: (ticker) => {
    const currentTicker = get().activeTicker
    if (ticker && ticker !== currentTicker) {
      // Clear conversation & assign a fresh session when ticker changes
      set({
        activeTicker: ticker,
        messages:     [],
        sessionId:    generateSessionId(),
        loading:      false,
      })
    }
  },

  clearHistory: () => set({
    messages:  [],
    sessionId: generateSessionId(),
    loading:   false,
  }),
}))

export default useResearchStore
