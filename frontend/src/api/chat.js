import client from './client'

export const sendMessage = (question, ticker, sessionId) =>
  client.post('/chat', { question, ticker, session_id: sessionId })

export const getSuggestions = (ticker) =>
  client.get(`/chat/suggestions/${ticker}`)

export const clearSession = (sessionId) =>
  client.delete(`/chat/${sessionId}`)
