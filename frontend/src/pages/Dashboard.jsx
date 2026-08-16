import { AppShell }       from '../components/layout/AppShell'
import { useMarketData }  from '../hooks/useMarketData'
import { useWebSocket }   from '../hooks/useWebSocket'

export function Dashboard() {
  // Initialize polling and live WebSocket stream
  useMarketData()
  useWebSocket()

  return <AppShell />
}
