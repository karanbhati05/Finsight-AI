import { useNavigate } from 'react-router-dom'
import { SparklineChart } from './SparklineChart'
import { ArrowDownRight, ArrowUpRight, ArrowDown, ArrowUp } from 'lucide-react'
import { IndexCardSkeleton } from '../common/Skeleton'
import useMarketStore from '../../store/marketStore'

export function IndexCard({ index, loading = false }) {
  const navigate = useNavigate()
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)

  if (loading || !index) {
    return <IndexCardSkeleton />
  }

  const { symbol, name, value, change, change_pct, sparkline } = index
  const isUp = (change_pct || 0) >= 0

  const formattedValue = typeof value === 'number'
    ? value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : value

  const formattedChange = typeof change === 'number'
    ? (change >= 0 ? `+${change.toFixed(2)}` : change.toFixed(2))
    : change

  const formattedPct = typeof change_pct === 'number'
    ? `${isUp ? '+' : ''}${change_pct.toFixed(2)}%`
    : `${change_pct}%`

  const handleClick = () => {
    if (symbol) {
      setActiveTicker(symbol)
      navigate(`/stock/${encodeURIComponent(symbol)}`)
    }
  }

  return (
    <div
      onClick={handleClick}
      className="bg-[#f8f9fa]/80 hover:bg-[#f8f9fa] border border-[#f1f3f4] hover:border-[#dadce0] rounded-2xl p-3.5 transition-all cursor-pointer flex flex-col justify-between select-none group shadow-xs"
    >
      {/* 1. Header: Index Name */}
      <div>
        <h4 className="text-[13px] font-bold text-[#202124] truncate tracking-tight">
          {name || symbol}
        </h4>

        {/* 2. Value & (Change) */}
        <div className="flex items-baseline gap-1 mt-0.5 text-xs text-[#5f6368]">
          <span className="font-medium text-[#202124]">
            {typeof value === 'number' ? `$${formattedValue}` : formattedValue}
          </span>
          <span className="text-[11px] text-[#5f6368]">
            ({formattedChange})
          </span>
        </div>

        {/* 3. Percentage with circle arrow indicator */}
        <div className="flex items-center gap-1 mt-1.5">
          <span className={`text-[13px] font-bold tracking-tight ${isUp ? 'text-[#0f9d58]' : 'text-[#d93025]'}`}>
            {formattedPct}
          </span>
          <div className={`w-4 h-4 rounded-full flex items-center justify-center text-white ${isUp ? 'bg-[#0f9d58]' : 'bg-[#d93025]'}`}>
            {isUp ? <ArrowUp size={10} strokeWidth={3} /> : <ArrowDown size={10} strokeWidth={3} />}
          </div>
        </div>
      </div>

      {/* 4. Bottom Sparkline with baseline */}
      <div className="mt-3 w-full">
        <SparklineChart data={sparkline} height={42} />
      </div>
    </div>
  )
}
