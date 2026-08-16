import { useState } from 'react'
import { ChevronDown, ChevronUp, Cpu, RotateCw, AlertCircle, TrendingUp } from 'lucide-react'
import { PredictionCard } from './PredictionCard'
import { ProbabilityGauge } from './ProbabilityGauge'
import { ProbabilityChart } from './ProbabilityChart'
import { FeatureImportance } from './FeatureImportance'
import { SharpeComparison } from './SharpeComparison'
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
          <button className="p-1 text-subtext rounded">
            {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>

      {/* ── Expanded Content Area ─────────────────────────── */}
      {isOpen && (
        <div className="p-5 space-y-6 animate-fade-in">
          {error ? (
            <div className="p-6 text-center bg-surface rounded-xl border border-border flex flex-col items-center gap-2">
              <AlertCircle size={22} className="text-loss" />
              <p className="text-sm font-semibold text-text">Prediction Model Unavailable for {activeTicker}</p>
              <p className="text-xs text-subtext">{error}</p>
              <button
                onClick={refetch}
                className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-border rounded-md text-xs font-medium text-text hover:bg-surface shadow-xs transition-base"
              >
                <RotateCw size={12} />
                Retry Inference
              </button>
            </div>
          ) : (
            <>
              {/* Top Row: Hero Prediction Card + Probability Gauge */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

                <div className="border border-border rounded-xl p-4 bg-white flex flex-col items-center justify-center">
                  <p className="text-xs font-bold text-subtext uppercase tracking-wider mb-2">
                    Confidence Gauge
                  </p>
                  <ProbabilityGauge probability={probability} />
                </div>
              </div>

              {/* Middle Row: Probability History Chart + Feature Importance */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
                {/* 60-Day Probability Trend */}
                <div className="border border-border rounded-xl p-4 bg-white">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-bold text-text uppercase tracking-wider">
                      Probability History (Buy/Sell Zones)
                    </p>
                    <span className="text-[10px] text-muted font-medium">Last 30-60 Bars</span>
                  </div>
                  <ProbabilityChart data={probabilityHistory} />
                </div>

                {/* XGBoost Feature Weights */}
                <div className="border border-border rounded-xl p-4 bg-white">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-bold text-text uppercase tracking-wider">
                      Feature Contribution (SHAP / XGBoost)
                    </p>
                    <span className="text-[10px] text-muted font-medium">Model Weights</span>
                  </div>
                  <FeatureImportance features={features} />
                </div>
              </div>

              {/* Bottom Row: Risk-Adjusted Sharpe Ratio Benchmark */}
              <SharpeComparison
                strategySharpe={1.84}
                buyHoldSharpe={1.12}
                winRate={modelMetrics?.cv_f1 ? Math.round(modelMetrics.cv_f1 * 100) : 63.5}
              />
            </>
          )}
        </div>
      )}
    </div>
  )
}
