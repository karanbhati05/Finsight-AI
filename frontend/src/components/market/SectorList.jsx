import { useState } from 'react'
import { ChevronDown, ChevronUp, RotateCw, AlertCircle } from 'lucide-react'
import { SectorRow } from './SectorRow'
import { SectorRowSkeleton } from '../common/Skeleton'
import useMarketStore from '../../store/marketStore'

export function SectorList({ onRetry }) {
  const [collapsed, setCollapsed] = useState(false)
  const sectors        = useMarketStore(s => s.sectors)
  const sectorsLoading = useMarketStore(s => s.sectorsLoading)
  const sectorsError   = useMarketStore(s => s.sectorsError)
  const activeRegion   = useMarketStore(s => s.activeRegion)

  return (
    <div className="w-full">
      {/* Section Header */}
      <div
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between px-4 py-2 cursor-pointer select-none hover:bg-surface transition-base"
      >
        <span className="text-xs font-semibold uppercase tracking-wider text-subtext">
          Equity sectors
        </span>
        <button className="p-0.5 text-subtext hover:text-text rounded transition-base">
          {collapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
      </div>

      {/* Collapsible Content */}
      {!collapsed && (
        <div className="divide-y divide-border/40">
          {sectorsLoading ? (
            [...Array(6)].map((_, i) => <SectorRowSkeleton key={i} />)
          ) : sectorsError ? (
            <div className="px-4 py-3 text-center bg-surface/50 my-1 rounded flex flex-col items-center gap-1.5">
              <AlertCircle size={16} className="text-loss" />
              <p className="text-2xs text-subtext">{sectorsError}</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-1 inline-flex items-center gap-1 px-2 py-1 text-2xs font-medium bg-white border border-border rounded hover:bg-surface transition-base"
                >
                  <RotateCw size={11} />
                  Retry
                </button>
              )}
            </div>
          ) : sectors.length > 0 ? (
            sectors.map((sector) => (
              <SectorRow key={sector.symbol || sector.name} sector={sector} />
            ))
          ) : (
            <div className="px-4 py-3 text-center text-xs text-muted">
              No sector indices for {activeRegion}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
