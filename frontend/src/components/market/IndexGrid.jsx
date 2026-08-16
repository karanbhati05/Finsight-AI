import { RotateCw, AlertCircle } from 'lucide-react'
import { IndexCard } from './IndexCard'
import { IndexCardSkeleton } from '../common/Skeleton'
import useMarketStore from '../../store/marketStore'

export function IndexGrid({ indices, loading, error, onRetry }) {
  const activeRegion = useMarketStore(s => s.activeRegion)

  // Loading state: 4 card skeletons in responsive grid
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <IndexCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  // Error state with retry
  if (error) {
    return (
      <div className="border border-border rounded-lg p-6 text-center bg-surface my-2 flex flex-col items-center justify-center gap-2">
        <AlertCircle size={22} className="text-loss" />
        <p className="text-sm font-medium text-text">Unable to load {activeRegion} market indices</p>
        <p className="text-xs text-subtext">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-border rounded-md text-xs font-medium text-text hover:bg-surface transition-base shadow-sm"
          >
            <RotateCw size={13} />
            Retry
          </button>
        )}
      </div>
    )
  }

  // Empty state
  if (!indices || indices.length === 0) {
    return (
      <div className="border border-dashed border-border rounded-lg p-6 text-center text-sm text-subtext my-2">
        No market indices available for {activeRegion}.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {indices.slice(0, 4).map((idx) => (
        <IndexCard key={idx.symbol || idx.name} index={idx} />
      ))}
    </div>
  )
}
