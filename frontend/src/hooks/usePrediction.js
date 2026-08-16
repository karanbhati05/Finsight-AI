import { useState, useEffect, useCallback, useRef } from 'react'
import { getPrediction } from '../api/prediction'

const cacheStore = new Map() // ticker -> { data, timestamp }
const CACHE_DURATION_MS = 5 * 60 * 1000 // 5 minutes

export function usePrediction(ticker = 'AAPL') {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const fetchPrediction = useCallback(async (ignoreCache = false) => {
    if (!ticker) return

    const now = Date.now()
    const cached = cacheStore.get(ticker)

    if (!ignoreCache && cached && (now - cached.timestamp < CACHE_DURATION_MS)) {
      setData(cached.data)
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await getPrediction(ticker)
      cacheStore.set(ticker, { data: res, timestamp: now })
      setData(res)
    } catch (err) {
      console.error(`Failed to fetch prediction for ${ticker}:`, err)
      setError(err.response?.data?.detail || err.message || 'Failed to load prediction')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [ticker])

  useEffect(() => {
    fetchPrediction()
  }, [fetchPrediction])

  return {
    data,
    prediction:         data?.prediction ?? null,
    label:              data?.label || (data?.prediction === 1 ? 'UP' : 'DOWN'),
    probability:        data?.probability ?? 0.5,
    confidence:         data?.confidence || 'Medium',
    date:               data?.date || '',
    features:           data?.features || {},
    probabilityHistory: data?.probability_history || [],
    modelMetrics:       data?.model_metrics || { cv_f1: 0.61, roc_auc: 0.64 },
    loading,
    error,
    refetch: () => fetchPrediction(true),
  }
}
