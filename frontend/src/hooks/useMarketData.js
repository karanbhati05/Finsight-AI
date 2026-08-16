import { useEffect } from 'react'
import { getIndices, getSectors } from '../api/market'
import useMarketStore from '../store/marketStore'

export function useMarketData() {
  const activeRegion      = useMarketStore(s => s.activeRegion)
  const indices           = useMarketStore(s => s.indices)
  const setIndices        = useMarketStore(s => s.setIndices)
  const setSectors        = useMarketStore(s => s.setSectors)
  const setIndicesLoading = useMarketStore(s => s.setIndicesLoading)
  const setSectorsLoading = useMarketStore(s => s.setSectorsLoading)

  useEffect(() => {
    let cancelled = false

    // Only show skeleton on first empty load
    if (!indices || indices.length === 0) {
      setIndicesLoading()
      setSectorsLoading()
    }

    const fetchData = async () => {
      try {
        const [indicesData, sectorsData] = await Promise.all([
          getIndices(activeRegion),
          getSectors(activeRegion),
        ])
        if (!cancelled) {
          if (indicesData?.indices) setIndices(indicesData.indices)
          if (sectorsData?.sectors) setSectors(sectorsData.sectors)
        }
      } catch (err) {
        console.error('Market data background fetch failed:', err)
      }
    }

    fetchData()

    const interval = setInterval(fetchData, 60000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [activeRegion, setIndices, setSectors])
}
