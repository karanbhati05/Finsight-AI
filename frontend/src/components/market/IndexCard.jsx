import { SparklineChart } from './SparklineChart'
import { PriceChange }    from '../common/PriceChange'

export function IndexCard({ index }) {
  const { name, value, change, change_pct, direction, sparkline } = index

  return (
    <div className="border border-border rounded-lg p-4 card-hover cursor-pointer min-w-[140px] flex-1">
      {/* Name */}
      <p className="text-xs font-medium text-subtext truncate">{name}</p>

      {/* Value */}
      <p className="text-lg font-semibold text-text mt-0.5">
        {typeof value === 'number'
          ? value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          : value
        }
      </p>

      {/* Change */}
      <PriceChange change={change} changePct={change_pct} size="sm" />

      {/* Sparkline */}
      <div className="mt-2">
        <SparklineChart data={sparkline} width="100%" height={40} />
      </div>
    </div>
  )
}
