import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, Plus, Star, AlertCircle } from 'lucide-react'
import { WatchlistRow } from './WatchlistRow'
import { AddToWatchlist } from './AddToWatchlist'
import useWatchlistStore from '../../store/watchlistStore'

export function WatchlistPanel() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isAdding, setIsAdding]       = useState(false)
  const watchlist      = useWatchlistStore(s => s.watchlist)
  const loading        = useWatchlistStore(s => s.loading)
  const error          = useWatchlistStore(s => s.error)
  const fetchWatchlist = useWatchlistStore(s => s.fetchWatchlist)

  useEffect(() => {
    fetchWatchlist()
  }, [fetchWatchlist])

  return (
    <div className="w-full">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2 select-none hover:bg-surface/50 transition-base">
        <div
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center gap-1.5 cursor-pointer flex-1"
        >
          <Star size={14} className="text-primary fill-primary/10" />
          <span className="text-xs font-bold uppercase tracking-wider text-subtext">
            Watchlist
          </span>
          {watchlist.length > 0 && (
            <span className="text-[10px] bg-surface text-subtext px-1.5 py-0.2 rounded-full border border-border">
              {watchlist.length}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              setIsAdding(!isAdding)
              setIsCollapsed(false)
            }}
            className="p-1 rounded text-subtext hover:text-text hover:bg-surface transition-base"
            title="Add stock to watchlist"
          >
            <Plus size={15} />
          </button>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-0.5 text-subtext hover:text-text rounded transition-base"
          >
            {isCollapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
          </button>
        </div>
      </div>

      {/* ── Content ────────────────────────────────────────── */}
      {!isCollapsed && (
        <div className="px-1">
          {/* Add Stock Input */}
          {isAdding && (
            <AddToWatchlist onClose={() => setIsAdding(false)} />
          )}

          {/* List or Empty */}
          {loading && watchlist.length === 0 ? (
            <div className="px-3 py-2 space-y-2">
              <div className="h-8 bg-surface rounded animate-pulse" />
              <div className="h-8 bg-surface rounded animate-pulse" />
            </div>
          ) : error ? (
            <div className="px-3 py-2 text-center text-xs text-loss flex items-center justify-center gap-1">
              <AlertCircle size={13} />
              <span>Failed to load watchlist</span>
            </div>
          ) : watchlist.length > 0 ? (
            <div className="divide-y divide-border/30">
              {watchlist.map((item) => (
                <WatchlistRow key={item.ticker} item={item} />
              ))}
            </div>
          ) : (
            !isAdding && (
              <div className="px-3 py-2 text-xs text-muted italic">
                This list is empty
              </div>
            )
          )}
        </div>
      )}
    </div>
  )
}
