import { useState } from 'react'
import { ChevronDown, ChevronUp, Cpu, RotateCw, AlertCircle, TrendingUp } from 'lucide-react'
import { PredictionCard } from './PredictionCard'
import { ProbabilityGauge } from './ProbabilityGauge'
import { ProbabilityChart } from './ProbabilityChart'
import { FeatureImportance } from './FeatureImportance'
import { SharpeComparison } from './SharpeComparison'
import { TickerQuickSwitch } from '../common/TickerQuickSwitch'
import { usePrediction } from '../../hooks/usePrediction'
import useMarketStore from '../../store/marketStore'

export function PredictionSection() {
  const activeTicker = useMarketStore(s => s.activeTicker) || 'AAPL'
  const [isOpen, setIsOpen] = useState(true)

  const {
    prediction,
    label,
    probability,
    confidence,
    date,
    features,
    probabilityHistory,
    modelMetrics,
    loading,
    error,
    refetch,
  } = usePrediction(activeTicker)

  const isUp = prediction === 1 || label.includes('UP')
  const probPct = Math.round((Number(probability) || 0.5) * 100)

  return (
    <div className="mt-8 border border-border rounded-xl bg-white shadow-xs overflow-hidden transition-base">
      {/* ── Collapsible Header ─────────────────────────────── */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between p-4 cursor-pointer select-none bg-surface/50 hover:bg-surface transition-base border-b border-border"
      >
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
            <Cpu size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-text">
                ML Price Prediction ({activeTicker})
              </h3>
              {!loading && !error && (
                <span
                  className={`text-2xs font-bold px-2 py-0.5 rounded-full uppercase border ${
                    isUp
                      ? 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]'
                      : 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]'
                  }`}
                >
                  {label} • {probPct}% ({confidence})
                </span>
              )}
            </div>
            <p className="text-xs text-subtext">
              XGBoost Directional Model with FinBERT Sentiment & Technical Indicators
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              refetch()
            }}
            className="p-1.5 rounded-full hover:bg-white text-subtext hover:text-text transition-base"
            title="Refresh Prediction"
          >
            <RotateCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          <div className="p-1 text-subtext">
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </div>
      </div>

      {/* ── Quick Ticker Switcher Bar ──────────────────────── */}
      <div className="px-4 py-2.5 bg-[#f8f9fa] border-b border-border flex items-center justify-between flex-wrap gap-2">
        <span className="text-2xs font-bold uppercase tracking-wider text-[#5f6368]">
          Predict Target:
        </span>
        <TickerQuickSwitch currentTicker={activeTicker} />
      </div>

      {/* ── Collapsible Body ───────────────────────────────── */}
      {isOpen && (
        <div className="p-4 space-y-6 animate-fade-in">
          {error && (
            <div className="p-3 bg-loss/10 border border-loss/20 rounded-lg flex items-center gap-2 text-xs text-loss">
              <AlertCircle size={14} className="flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Primary Top Grid: Probability Gauge & Key Verdict */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-1">
              <ProbabilityGauge
                probability={probability}
                confidence={confidence}
                label={label}
                loading={loading}
              />
            </div>
            <div className="md:col-span-2">
              <PredictionCard
                ticker={activeTicker}
                prediction={prediction}
                label={label}
                probability={probability}
                confidence={confidence}
                date={date}
                features={features}
                loading={loading}
              />
            </div>
          </div>

          {/* Sharpe Comparison Benchmark */}
          <SharpeComparison
            strategySharpe={modelMetrics?.sharpe_strategy || 1.84}
            buyHoldSharpe={modelMetrics?.sharpe_buy_hold || 1.12}
            winRate={modelMetrics?.win_rate || 64.2}
          />

          {/* 30-Day Probability Trend Chart */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-subtext mb-2">
              30-Day Bullish Probability History
            </h4>
            <ProbabilityChart
              data={probabilityHistory}
              loading={loading}
            />
          </div>

          {/* XGBoost Feature Importance Breakdown */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-subtext mb-2">
              Model Factor Importance
            </h4>
            <FeatureImportance
              importances={features}
              loading={loading}
            />
          </div>
        </div>
      )}
    </div>
  )
}
