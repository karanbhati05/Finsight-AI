import client from './client'

export const getNews = (ticker = 'AAPL', limit = 20, daysBack = 7) =>
  client.get(`/news/${ticker}?limit=${limit}&days_back=${daysBack}`)
