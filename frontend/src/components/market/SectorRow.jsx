import { SparklineChart } from './SparklineChart'
import { useNavigate } from 'react-router-dom'
import useMarketStore from '../../store/marketStore'

export function SectorRow({ sector }) {
  const navigate = useNavigate()
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)

  if (!sector) return null

  const { symbol, name, label, value, change_pct, sparkline } = sector
  const isUp = (change_pct || 0) >= 0

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
      className="flex items-center justify-between px-4 py-2 hover:bg-surface transition-base cursor-pointer group"
    >
      {/* Left: Sector name + label */}
      <div className="flex-1 min-w-0 pr-2">
        <p className="text-xs font-semibold text-text truncate group-hover:text-primary transition-base">
          {name}
        </p>
        <p className="text-2xs text-subtext truncate">
          {label || name}
        </p>
      </div>

      {/* Center: 80px sparkline */}
      <div className="w-20 h-6 flex-shrink-0 px-1">
        <SparklineChart data={sparkline} width={80} height={24} />
      </div>

      {/* Right: Value + colored change percentage */}
      <div className="text-right flex-shrink-0 min-w-[75px]">
        <p className="text-xs font-medium text-text">
          {formattedValue}
        </p>
        <p className={`text-2xs font-semibold ${isUp ? 'text-gain' : 'text-loss'}`}>
          {isUp ? '+' : ''}{typeof change_pct === 'number' ? change_pct.toFixed(2) : change_pct}% {isUp ? '▲' : '▼'}
        </p>
      </div>
    </div>
  )
}
