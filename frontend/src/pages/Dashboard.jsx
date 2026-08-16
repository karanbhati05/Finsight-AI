import { AppShell }       from '../components/layout/AppShell'
import { useMarketData }  from '../hooks/useMarketData'

export function Dashboard() {
  // Initialize market data fetching
  useMarketData()

  return <AppShell />
}
