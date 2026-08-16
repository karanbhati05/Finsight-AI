import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, Plus, List, Star } from 'lucide-react'
import { SparklineChart } from '../market/SparklineChart'
import { SectorRowSkeleton } from '../common/Skeleton'
import useMarketStore from '../../store/marketStore'

function SectionHeader({ title, icon: Icon, collapsed, onToggle, actions }) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5">
      <div className="flex items-center gap-2">
        {Icon && <Icon size={16} className="text-subtext" />}
        <span className="text-sm font-semibold text-text">{title}</span>
      </div>
      <div className="flex items-center gap-1">
        {actions}
        <button
          onClick={onToggle}
          className="p-1 rounded hover:bg-surface transition-base"
        >
          {collapsed ? <ChevronDown size={16} className="text-subtext" /> : <ChevronUp size={16} className="text-subtext" />}
        </button>
      </div>
    </div>
  )
}

function SectorRow({ sector }) {
  const changePct = sector.change_pct
  const isUp = changePct >= 0

  return (
    <div className="flex items-center px-4 py-2 gap-3 card-hover cursor-pointer">
      {/* Name + label */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text truncate">{sector.name}</p>
        <p className="text-2xs text-subtext">{sector.label}</p>
      </div>

      {/* Sparkline */}
      <SparklineChart data={sector.sparkline} width={60} height={24} />

      {/* Value + change */}
      <div className="text-right flex-shrink-0 min-w-[80px]">
        <p className="text-sm font-medium text-text">
          {typeof sector.value === 'number'
            ? sector.value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            : sector.value
          }
        </p>
        <p className={`text-xs font-medium ${isUp ? 'text-gain' : 'text-loss'}`}>
          {isUp ? '+' : ''}{changePct?.toFixed(2)}%
          <span className="ml-0.5">{isUp ? '↑' : '↓'}</span>
        </p>
      </div>
    </div>
  )
}

function WatchlistEmpty() {
  return (
    <div className="px-4 py-3">
      <p className="text-xs text-muted italic">This list is empty</p>
    </div>
  )
}

export function Sidebar() {
  const [portfoliosOpen, setPortfoliosOpen] = useState(true)
  const [watchlistOpen, setWatchlistOpen]   = useState(true)
  const [sectorsOpen, setSectorsOpen]       = useState(true)

  const sectors        = useMarketStore(s => s.sectors)
  const sectorsLoading = useMarketStore(s => s.sectorsLoading)

  return (
    <div className="py-2">
      {/* Lists header */}
      <div className="px-4 py-2 flex items-center gap-2">
        <List size={16} className="text-subtext" />
        <span className="text-sm font-semibold text-text">Lists</span>
        <ChevronDown size={14} className="text-subtext ml-0.5" />
      </div>

      {/* Portfolios */}
      <SectionHeader
        title="Portfolios"
        collapsed={!portfoliosOpen}
        onToggle={() => setPortfoliosOpen(!portfoliosOpen)}
        actions={
          <button className="p-1 rounded hover:bg-surface transition-base">
            <Plus size={16} className="text-subtext" />
          </button>
        }
      />
      {portfoliosOpen && (
        <div className="px-4 py-2">
          <button className="flex items-center gap-2 text-primary text-sm font-medium hover:underline btn-press">
            <Plus size={14} />
            Create a portfolio
          </button>
        </div>
      )}

      <div className="border-b border-border mx-4 my-1" />

      {/* Watchlist */}
      <SectionHeader
        title="Watchlist"
        collapsed={!watchlistOpen}
        onToggle={() => setWatchlistOpen(!watchlistOpen)}
        actions={
          <button className="p-1 rounded hover:bg-surface transition-base">
            <Plus size={16} className="text-subtext" />
          </button>
        }
      />
      {watchlistOpen && <WatchlistEmpty />}

      <div className="border-b border-border mx-4 my-1" />

      {/* Equity Sectors */}
      <SectionHeader
        title="Equity sectors"
        collapsed={!sectorsOpen}
        onToggle={() => setSectorsOpen(!sectorsOpen)}
      />
      {sectorsOpen && (
        <div>
          {sectorsLoading ? (
            [...Array(5)].map((_, i) => <SectorRowSkeleton key={i} />)
          ) : sectors.length > 0 ? (
            sectors.map(sector => (
              <SectorRow key={sector.symbol} sector={sector} />
            ))
          ) : (
            <p className="px-4 py-3 text-xs text-muted">No sector data available</p>
          )}
        </div>
      )}

      {/* Footer disclaimer */}
      <div className="mt-4 px-4 py-3 border-t border-border">
        <p className="text-2xs text-muted leading-relaxed">
          AI content may include mistakes.{' '}
          <a href="#" className="text-primary hover:underline">Learn more</a>
        </p>
      </div>
    </div>
  )
}
