import client from './client'

export const sendMessage = (question, ticker, sessionId) =>
  client.post('/chat', { question, ticker, session_id: sessionId })

export const uploadAttachment = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return client.post('/chat/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getSuggestions = (ticker) =>
  client.get(`/chat/suggestions/${ticker}`)

export const clearSession = (sessionId) =>
  client.delete(`/chat/${sessionId}`)
