import { useState, useEffect, useRef } from 'react'
import { Trash2 } from 'lucide-react'
import { SparklineChart } from '../market/SparklineChart'
import useMarketStore from '../../store/marketStore'
import useWatchlistStore from '../../store/watchlistStore'

export function WatchlistRow({ item }) {
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)
  const activeTicker    = useMarketStore(s => s.activeTicker)
  const removeTicker    = useWatchlistStore(s => s.removeTicker)

  const [flashClass, setFlashClass] = useState('')
  const prevPriceRef = useRef(item?.price)

  const { ticker, name, price, change, change_pct, sparkline } = item || {}
  const isSelected = activeTicker?.toUpperCase() === ticker?.toUpperCase()
  const isUp = (change_pct || 0) >= 0

  // Flash animation trigger on price mutation
  useEffect(() => {
    if (prevPriceRef.current !== undefined && price !== undefined && prevPriceRef.current !== price) {
      const isGain = price > prevPriceRef.current
      setFlashClass(isGain ? 'flash-green' : 'flash-red')

      const timer = setTimeout(() => setFlashClass(''), 1200)
      prevPriceRef.current = price
      return () => clearTimeout(timer)
    }
    prevPriceRef.current = price
  }, [price])

  if (!item) return null

  const formattedPrice = typeof price === 'number'
    ? price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : price

  const handleRowClick = () => {
    setActiveTicker(ticker)
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    removeTicker(ticker)
  }

  return (
    <div
      onClick={handleRowClick}
      className={`
        flex items-center justify-between px-3 py-2 transition-base cursor-pointer group rounded-md
        ${flashClass}
        ${isSelected ? 'bg-primary/5 border-l-2 border-primary pl-2.5' : 'hover:bg-surface'}
      `}
    >
      {/* Ticker & Name */}
      <div className="min-w-0 flex-1 pr-1.5">
        <p className="text-xs font-bold text-text truncate group-hover:text-primary transition-base">
          {ticker}
        </p>
        <p className="text-2xs text-subtext truncate">
          {name || ticker}
        </p>
      </div>

      {/* 40px mini sparkline */}
      <div className="w-12 h-6 flex-shrink-0 px-1">
        <SparklineChart data={sparkline} width={48} height={20} />
      </div>

      {/* Price & Change */}
      <div className="text-right flex-shrink-0 min-w-[65px] pl-1">
        <p className="text-xs font-semibold text-text">
          {formattedPrice}
        </p>
        <p className={`text-2xs font-semibold ${isUp ? 'text-gain' : 'text-loss'}`}>
          {isUp ? '+' : ''}{typeof change_pct === 'number' ? change_pct.toFixed(2) : change_pct}%
        </p>
      </div>

      {/* Hover Remove button */}
      <button
        onClick={handleDelete}
        className="p-1 rounded text-subtext hover:text-loss opacity-0 group-hover:opacity-100 transition-base ml-1 flex-shrink-0"
        title={`Remove ${ticker} from watchlist`}
      >
        <Trash2 size={13} />
      </button>
    </div>
  )
}
