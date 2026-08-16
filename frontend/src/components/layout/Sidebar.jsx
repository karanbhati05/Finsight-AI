import { List } from 'lucide-react'
import { PortfolioList } from '../portfolio/PortfolioList'
import { WatchlistPanel } from '../watchlist/WatchlistPanel'
import { SectorList } from '../market/SectorList'

export function Sidebar() {
  return (
    <div className="py-2 flex flex-col justify-between min-h-full">
      <div className="space-y-1">
        {/* Lists header */}
        <div className="px-4 py-2 flex items-center gap-2 text-text font-bold text-sm select-none">
          <List size={16} className="text-subtext" />
          <span>Lists</span>
        </div>

        {/* ── 1. Portfolio Management ──────────────────────── */}
        <PortfolioList />

        <div className="border-b border-border mx-3 my-1" />

        {/* ── 2. Real-time Watchlist ────────────────────────── */}
        <WatchlistPanel />

        <div className="border-b border-border mx-3 my-1" />

        {/* ── 3. Equity Sectors ─────────────────────────────── */}
        <SectorList />
      </div>

      {/* ── Footer Disclaimer ────────────────────────────────── */}
      <div className="mt-8 px-4 py-3 border-t border-border">
        <p className="text-2xs text-muted leading-relaxed">
          AI content may include mistakes.{' '}
          <a href="#" className="text-primary hover:underline">Learn more</a>
        </p>
      </div>
    </div>
  )
}
