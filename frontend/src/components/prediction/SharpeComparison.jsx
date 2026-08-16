import { HelpCircle, TrendingUp, Award } from 'lucide-react'

export function SharpeComparison({
  strategySharpe = 1.84,
  buyHoldSharpe  = 1.12,
  winRate        = 63.5,
}) {
  const delta = Number((strategySharpe - buyHoldSharpe).toFixed(2))
  const isOutperforming = delta > 0

  return (
    <div className="bg-surface rounded-xl p-4 border border-border">
      {/* Header with Explanatory Tooltip */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5">
          <Award size={15} className="text-primary" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-text">
            Risk-Adjusted Performance (Sharpe Ratio)
          </h4>
        </div>
        <div className="group relative">
          <HelpCircle size={14} className="text-muted hover:text-text cursor-pointer" />
          <div className="absolute right-0 bottom-full mb-1.5 hidden group-hover:block w-56 p-2 bg-text text-white text-[10px] leading-relaxed rounded shadow-lg z-20">
            The Sharpe ratio measures risk-adjusted return. A higher ratio indicates greater returns per unit of total risk/volatility.
          </div>
        </div>
      </div>

      {/* Side-by-side metric comparison */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {/* Strategy Sharpe Card */}
        <div className="bg-white p-3 rounded-lg border border-border">
          <p className="text-2xs text-subtext font-medium">FinSight AI Strategy</p>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-lg font-black text-primary">
              {Number(strategySharpe).toFixed(2)}
            </span>
            <span className="text-2xs font-semibold text-gain">Sharpe</span>
          </div>
        </div>

        {/* Buy & Hold Benchmark */}
        <div className="bg-white p-3 rounded-lg border border-border">
          <p className="text-2xs text-subtext font-medium">Buy & Hold Benchmark</p>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-lg font-bold text-text">
              {Number(buyHoldSharpe).toFixed(2)}
            </span>
            <span className="text-2xs text-subtext">Sharpe</span>
          </div>
        </div>

        {/* Delta Outperformance Badge */}
        <div className="bg-white p-3 rounded-lg border border-border col-span-2 sm:col-span-1 flex flex-col justify-between">
          <p className="text-2xs text-subtext font-medium">Alpha Generation</p>
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp size={14} className="text-gain" />
            <span className="text-sm font-bold text-gain">
              +{delta} ({isOutperforming ? 'Outperforming' : 'Lagging'})
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
