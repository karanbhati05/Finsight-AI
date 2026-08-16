import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, Plus, Briefcase, TrendingUp, TrendingDown } from 'lucide-react'
import { PortfolioRow } from './PortfolioRow'
import { AddStockModal } from './AddStockModal'
import usePortfolioStore from '../../store/portfolioStore'

export function PortfolioList() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const holdings        = usePortfolioStore(s => s.holdings)
  const totalValue      = usePortfolioStore(s => s.totalValue)
  const totalPnL        = usePortfolioStore(s => s.totalPnL)
  const totalPnLPct     = usePortfolioStore(s => s.totalPnLPct)
  const loading         = usePortfolioStore(s => s.loading)
  const isAddModalOpen  = usePortfolioStore(s => s.isAddModalOpen)
  const setAddModalOpen = usePortfolioStore(s => s.setAddModalOpen)
  const fetchPortfolio  = usePortfolioStore(s => s.fetchPortfolio)

  useEffect(() => {
    fetchPortfolio()
  }, [fetchPortfolio])

  const isGain = totalPnL >= 0
  const formattedTotalValue = `$${Number(totalValue || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  const formattedPnL = `${isGain ? '+' : ''}$${Math.abs(Number(totalPnL || 0)).toFixed(2)}`
  const formattedPnLPct = `${isGain ? '+' : ''}${Number(totalPnLPct || 0).toFixed(2)}%`

  return (
    <div className="w-full">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2 select-none hover:bg-surface/50 transition-base">
        <div
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center gap-1.5 cursor-pointer flex-1"
        >
          <Briefcase size={14} className="text-primary" />
          <span className="text-xs font-bold uppercase tracking-wider text-subtext">
            Portfolios
          </span>
          {holdings.length > 0 && (
            <span className="text-[10px] bg-surface text-subtext px-1.5 py-0.2 rounded-full border border-border">
              {holdings.length}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setAddModalOpen(true)}
            className="p-1 rounded text-subtext hover:text-text hover:bg-surface transition-base"
            title="Add stock to portfolio"
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
          {/* Total Value & P&L Card */}
          {holdings.length > 0 && (
            <div className="mx-2 my-1.5 p-2.5 rounded-lg bg-surface/70 border border-border/80 flex items-center justify-between">
              <div>
                <p className="text-[10px] uppercase font-bold text-muted tracking-wider">Total Value</p>
                <p className="text-xs font-black text-text">{formattedTotalValue}</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] uppercase font-bold text-muted tracking-wider">Total P&L</p>
                <p className={`text-xs font-bold ${isGain ? 'text-gain' : 'text-loss'}`}>
                  {formattedPnL} ({formattedPnLPct})
                </p>
              </div>
            </div>
          )}

          {/* Holdings List */}
          {loading && holdings.length === 0 ? (
            <div className="px-3 py-2 space-y-2">
              <div className="h-8 bg-surface rounded animate-pulse" />
              <div className="h-8 bg-surface rounded animate-pulse" />
            </div>
          ) : holdings.length > 0 ? (
            <div className="divide-y divide-border/30">
              {holdings.map((h) => (
                <PortfolioRow key={h.ticker} holding={h} />
              ))}
            </div>
          ) : (
            <div className="px-3 py-2 text-xs text-muted">
              <button
                onClick={() => setAddModalOpen(true)}
                className="flex items-center gap-1.5 text-primary text-xs font-semibold hover:underline btn-press"
              >
                <Plus size={13} />
                Create portfolio position
              </button>
            </div>
          )}
        </div>
      )}

      {/* Modal */}
      <AddStockModal
        isOpen={isAddModalOpen}
        onClose={() => setAddModalOpen(false)}
      />
    </div>
  )
}
