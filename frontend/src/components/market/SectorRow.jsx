import { SparklineChart } from './SparklineChart'
import { useNavigate } from 'react-router-dom'
import useMarketStore from '../../store/marketStore'

export function SectorRow({ sector }) {
  const navigate = useNavigate()
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)

  if (!sector) return null

  const { symbol, name, label, value, change_pct, sparkline } = sector
  const isUp = (change_pct || 0) >= 0
  const displayName = label || name || symbol

  const formattedValue = typeof value === 'number'
    ? value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : value

  const handleClick = () => {
    if (symbol) {
      setActiveTicker(symbol)
      navigate(`/stock/${encodeURIComponent(symbol)}`)
    }
  }

  return (
    <div
      onClick={handleClick}
      className="flex items-center justify-between px-4 py-2 hover:bg-[#f8f9fa] transition-base cursor-pointer group select-none"
    >
      {/* Left: Sector name */}
      <div className="flex-1 min-w-0 pr-2">
        <p className="text-xs font-semibold text-[#202124] truncate group-hover:text-[#1a73e8] transition-base">
          {displayName}
        </p>
      </div>

      {/* Center: 70px clean mini sparkline trend */}
      <div className="w-18 h-5 flex-shrink-0 px-1">
        <SparklineChart data={sparkline} width={70} height={20} isUp={isUp} />
      </div>

      {/* Right: Value + colored change percentage */}
      <div className="text-right flex-shrink-0 min-w-[75px]">
        <p className="text-xs font-medium text-[#202124]">
          {formattedValue}
        </p>
        <p className={`text-2xs font-semibold ${isUp ? 'text-[#0f9d58]' : 'text-[#d93025]'}`}>
          {isUp ? '+' : ''}{typeof change_pct === 'number' ? change_pct.toFixed(2) : change_pct}% {isUp ? '▲' : '▼'}
        </p>
      </div>
    </div>
  )
}
