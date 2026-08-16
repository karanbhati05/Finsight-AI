import { useState, useEffect, useRef } from 'react'
import { Trash2 } from 'lucide-react'
import useMarketStore from '../../store/marketStore'
import usePortfolioStore from '../../store/portfolioStore'

export function PortfolioRow({ holding }) {
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)
  const activeTicker    = useMarketStore(s => s.activeTicker)
  const removePosition  = usePortfolioStore(s => s.removePosition)

  const [flashClass, setFlashClass] = useState('')
  const prevPriceRef = useRef(holding?.current)

  const { ticker, name, shares, buy_price, current, pnl, pnl_pct, market_value } = holding || {}
  const isSelected = activeTicker?.toUpperCase() === ticker?.toUpperCase()
  const isGain = (pnl || 0) >= 0

  useEffect(() => {
    if (prevPriceRef.current !== undefined && current !== undefined && prevPriceRef.current !== current) {
      const isUp = current > prevPriceRef.current
      setFlashClass(isUp ? 'flash-green' : 'flash-red')

      const timer = setTimeout(() => setFlashClass(''), 1200)
      prevPriceRef.current = current
      return () => clearTimeout(timer)
    }
    prevPriceRef.current = current
  }, [current])

  if (!holding) return null

  const formattedMarketValue = typeof market_value === 'number'
    ? `$${market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : `$${market_value}`

  const formattedPnl = typeof pnl === 'number'
    ? `${isGain ? '+' : ''}$${Math.abs(pnl).toFixed(2)}`
    : pnl

  const formattedPnlPct = typeof pnl_pct === 'number'
    ? `${isGain ? '+' : ''}${pnl_pct.toFixed(2)}%`
    : pnl_pct

  const handleRowClick = () => {
    setActiveTicker(ticker)
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    removePosition(ticker)
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
      {/* Ticker & Shares */}
      <div className="min-w-0 flex-1 pr-2">
        <p className="text-xs font-bold text-text truncate group-hover:text-primary transition-base">
          {ticker}
        </p>
        <p className="text-2xs text-subtext truncate">
          {shares} shares @ ${Number(buy_price).toFixed(2)}
        </p>
      </div>

      {/* Market Value & Unrealized P&L */}
      <div className="text-right flex-shrink-0 min-w-[80px]">
        <p className="text-xs font-semibold text-text">
          {formattedMarketValue}
        </p>
        <p className={`text-2xs font-semibold ${isGain ? 'text-gain' : 'text-loss'}`}>
          {formattedPnl} ({formattedPnlPct})
        </p>
      </div>

      {/* Delete position */}
      <button
        onClick={handleDelete}
        className="p-1 rounded text-subtext hover:text-loss opacity-0 group-hover:opacity-100 transition-base ml-1 flex-shrink-0"
        title={`Remove position in ${ticker}`}
      >
        <Trash2 size={13} />
      </button>
    </div>
  )
}
