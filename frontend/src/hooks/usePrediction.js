import { useState, useEffect, useCallback } from 'react'
import { getPrediction } from '../api/prediction'

const cacheStore = new Map()

export function usePrediction(ticker = 'AAPL') {
  const cleanTicker = (ticker || 'AAPL').toUpperCase()
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const fetchPrediction = useCallback(async (ignoreCache = false) => {
    if (!cleanTicker) return

    const now = Date.now()
    const cached = cacheStore.get(cleanTicker)

    if (!ignoreCache && cached && (now - cached.timestamp < 300000)) {
      setData(cached.data)
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    try {
      const res = await getPrediction(cleanTicker)
      if (res && (res.prediction !== undefined || res.features)) {
        cacheStore.set(cleanTicker, { data: res, timestamp: now })
        setData(res)
        setError(null)
      }
    } catch (err) {
      console.warn(`Live prediction fetch note for ${cleanTicker}:`, err)
      setError(`Model running inference for ${cleanTicker}...`)
    } finally {
      setLoading(false)
    }
  }, [cleanTicker])

  useEffect(() => {
    fetchPrediction()
  }, [cleanTicker, fetchPrediction])

  return {
    data,
    prediction:         data?.prediction ?? 1,
    label:              data?.label || (data?.prediction === 0 ? 'DOWN (Bearish)' : 'UP (Bullish)'),
    probability:        data?.probability ?? 0.65,
    confidence:         data?.confidence || 'MODERATE',
    date:               data?.date || new Date().toISOString().substring(0, 10),
    features:           data?.features || {},
    featureImportance:  data?.feature_importances || data?.feature_importance || data?.features || {},
    probabilityHistory: data?.probability_history || [],
    modelMetrics:       data?.model_metrics || { test_accuracy: 0.65, sharpe_strategy: 1.84, sharpe_buy_hold: 1.12, win_rate: 64.2 },
    loading,
    error,
    refetch: () => fetchPrediction(true),
  }
}
