import { useEffect } from 'react'
import { getIndices, getSectors } from '../api/market'
import useMarketStore from '../store/marketStore'

export function useMarketData() {
  const activeRegion     = useMarketStore(s => s.activeRegion)
  const setIndices       = useMarketStore(s => s.setIndices)
  const setSectors       = useMarketStore(s => s.setSectors)
  const setIndicesLoading = useMarketStore(s => s.setIndicesLoading)
  const setSectorsLoading = useMarketStore(s => s.setSectorsLoading)

  useEffect(() => {
    const fetchData = async () => {
      setIndicesLoading()
      setSectorsLoading()

      try {
        const [indicesData, sectorsData] = await Promise.all([
          getIndices(activeRegion),
          getSectors(activeRegion),
        ])
        setIndices(indicesData.indices || [])
        setSectors(sectorsData.sectors || [])
      } catch (err) {
        console.error('Market data fetch failed:', err)
        setIndices([])
        setSectors([])
      }
    }

    fetchData()

    // Refresh every 60 seconds
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [activeRegion])
}
