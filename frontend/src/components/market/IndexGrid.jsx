import { IndexCard } from './IndexCard'
import { IndexCardSkeleton } from '../common/Skeleton'

export function IndexGrid({ indices, loading }) {
  if (loading) {
    return (
      <div className="flex gap-3 overflow-x-auto pb-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="min-w-[160px] flex-1">
            <IndexCardSkeleton />
          </div>
        ))}
      </div>
    )
  }

  if (!indices || indices.length === 0) {
    return (
      <div className="text-center py-8 text-subtext text-sm">
        No market data available for this region.
      </div>
    )
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {indices.map((index) => (
        <IndexCard key={index.symbol} index={index} />
      ))}
    </div>
  )
}
