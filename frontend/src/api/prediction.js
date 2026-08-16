import client from './client'

export const getPrediction = (ticker = 'AAPL') =>
  client.get(`/predict/${ticker}`)
