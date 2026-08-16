import client from './client'

export const getIndices = (region = 'india') =>
  client.get(`/market/indices?region=${region}`)

export const getSectors = (region = 'india') =>
  client.get(`/market/sectors?region=${region}`)

export const searchStocks = (query) =>
  client.get(`/market/search?q=${encodeURIComponent(query)}`)
