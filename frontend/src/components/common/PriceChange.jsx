import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'

export function PriceChange({ change, changePct, showIcon = true, size = 'base' }) {
  const isUp      = change > 0
  const isDown    = change < 0
  const color     = isUp ? 'text-gain' : isDown ? 'text-loss' : 'text-subtext'
  const sizeClass = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm'

  const displayChange = typeof change === 'number' ? change.toFixed(2) : '0.00'
  const displayPct    = typeof changePct === 'number' ? changePct.toFixed(2) : '0.00'

  return (
    <span className={`inline-flex items-center gap-0.5 font-medium ${color} ${sizeClass}`}>
      {showIcon && (
        isUp   ? <ArrowUpRight   size={size === 'sm' ? 12 : 14} /> :
        isDown ? <ArrowDownRight size={size === 'sm' ? 12 : 14} /> :
                 <Minus          size={size === 'sm' ? 12 : 14} />
      )}
      {isUp ? '+' : ''}{displayChange} ({isUp ? '+' : ''}{displayPct}%)
    </span>
  )
}
