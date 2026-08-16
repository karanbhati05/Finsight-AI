import { useState, useEffect, useCallback } from 'react'
import { getNews } from '../api/news'

export function useNews(ticker = 'AAPL') {
  const [articles, setArticles]           = useState([])
  const [marketSummary, setMarketSummary] = useState('')
  const [avgSentiment, setAvgSentiment]   = useState(0)
  const [loading, setLoading]             = useState(true)
  const [error, setError]                 = useState(null)

  const fetchNewsData = useCallback(async () => {
    if (!ticker) return
    setLoading(true)
    setError(null)

    try {
      const data = await getNews(ticker, 20, 7)
      setArticles(data.articles || [])
      setMarketSummary(data.market_summary || '')
      setAvgSentiment(data.avg_sentiment || 0)
    } catch (err) {
      console.error(`Failed to fetch news for ${ticker}:`, err)
      setError(err.response?.data?.detail || err.message || 'Failed to load news')
      setArticles([])
    } finally {
      setLoading(false)
    }
  }, [ticker])

  useEffect(() => {
    fetchNewsData()

    // 5-minute auto-refresh interval
    const interval = setInterval(fetchNewsData, 300000)
    return () => clearInterval(interval)
  }, [fetchNewsData])

  return {
    articles,
    marketSummary,
    avgSentiment,
    loading,
    error,
    refetch: fetchNewsData,
  }
}
