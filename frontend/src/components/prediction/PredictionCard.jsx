import { ArrowUp, ArrowDown, Sparkles, TrendingUp, TrendingDown, Calendar } from 'lucide-react'
import { Skeleton } from '../common/Skeleton'

export function PredictionCard({
  ticker = 'AAPL',
  prediction = 1,
  label = 'UP',
  probability = 0.67,
  confidence = 'High',
  date = '',
  features = {},
  loading = false,
}) {
  if (loading) {
    return (
      <div className="border border-border rounded-xl p-5 bg-white space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton width="40%" height={18} />
          <Skeleton width="20%" height={20} className="rounded-full" />
        </div>
        <div className="flex items-center gap-4 py-2">
          <Skeleton width={48} height={48} className="rounded-xl" />
          <div className="space-y-1.5 flex-1">
            <Skeleton width="60%" height={24} />
            <Skeleton width="40%" height={14} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border">
          <Skeleton height={28} />
          <Skeleton height={28} />
        </div>
      </div>
    )
  }

  const isUp = prediction === 1 || label.toUpperCase().includes('UP')
  const pct = Math.round((Number(probability) || 0.5) * 100)

  const theme = isUp
    ? {
        border:   'border-[#ceead6]',
        bg:       'bg-[#f6fbf8]',
        color:    'text-[#0f9d58]',
        badgeBg:  'bg-[#e6f4ea] text-[#137333] border-[#ceead6]',
        arrowBg:  'bg-[#e6f4ea]',
        ArrowIcon: ArrowUp,
      }
    : {
        border:   'border-[#fad2cf]',
        bg:       'bg-[#fdf7f7]',
        color:    'text-[#d93025]',
        badgeBg:  'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]',
        arrowBg:  'bg-[#fce8e6]',
        ArrowIcon: ArrowDown,
      }

  const Arrow = theme.ArrowIcon

  const rsi = features['RSI (14-day)'] || features.rsi_14 || null
  const sentimentScore = features['News Sentiment Polarity'] || features.sentiment_score || null
  const maRatio = features['MA5 / MA20 Ratio'] || features.ma5_ma20_ratio || null

  return (
    <div
      className={`
        border ${theme.border} rounded-xl p-5 bg-white hover:shadow-md transition-base
        flex flex-col justify-between relative overflow-hidden
      `}
    >
      {/* Header Line */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-subtext uppercase tracking-wider">
          <Sparkles size={14} className="text-primary" />
          <span>Next Day Direction</span>
        </div>

        <span className={`text-2xs font-bold px-2 py-0.5 rounded-full border uppercase tracking-wide ${theme.badgeBg}`}>
          {confidence} Confidence
        </span>
      </div>

      {/* Main Prediction Display */}
      <div className="flex items-center gap-4 my-4">
        <div className={`w-14 h-14 rounded-2xl ${theme.arrowBg} flex items-center justify-center flex-shrink-0 shadow-xs`}>
          <Arrow size={32} className={`${theme.color} stroke-[2.5]`} />
        </div>

        <div>
          <div className="flex items-baseline gap-2">
            <h3 className={`text-2xl font-black tracking-tight ${theme.color}`}>
              {isUp ? 'PREDICTED UP' : 'PREDICTED DOWN'}
            </h3>
          </div>
          <p className="text-xs text-subtext font-medium mt-0.5">
            <span className="font-bold text-text">{pct}%</span> probability of price increase
          </p>
        </div>
      </div>

      {/* Footer Feature Snapshot */}
      <div className="pt-3 border-t border-border/60 flex items-center justify-between text-xs text-subtext flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          {rsi && (
            <span className="bg-surface px-2 py-1 rounded border border-border/80 text-2xs font-medium">
              RSI (14): <strong className="text-text">{rsi}</strong>
            </span>
          )}
          {maRatio && (
            <span className="bg-surface px-2 py-1 rounded border border-border/80 text-2xs font-medium">
              MA5/20: <strong className="text-text">{maRatio}</strong>
            </span>
          )}
          {sentimentScore && (
            <span className="bg-surface px-2 py-1 rounded border border-border/80 text-2xs font-medium">
              Sentiment: <strong className="text-text">{sentimentScore}</strong>
            </span>
          )}
        </div>

        {date && (
          <div className="flex items-center gap-1 text-2xs text-muted">
            <Calendar size={11} />
            <span>{date}</span>
          </div>
        )}
      </div>
    </div>
  )
}
