import { useState } from 'react'
import { ChevronUp, ChevronDown, RotateCw, AlertCircle, Sparkles } from 'lucide-react'
import { NewsCard } from './NewsCard'
import { NewsCardSkeleton } from '../common/Skeleton'
import { SentimentBadge } from './SentimentBadge'
import { useNews } from '../../hooks/useNews'
import useMarketStore from '../../store/marketStore'

export function NewsFeed() {
  const activeTicker = useMarketStore(s => s.activeTicker) || 'AAPL'
  const { articles, marketSummary, avgSentiment, loading, error, refetch } = useNews(activeTicker)
  const [summaryExpanded, setSummaryExpanded] = useState(true)

  return (
    <div className="mt-8">
      {/* ── Market Summary Card (Google Finance Style) ──────── */}
      {marketSummary && (
        <div className="mb-6 p-4 rounded-xl bg-surface border border-border transition-base">
          <div
            onClick={() => setSummaryExpanded(!summaryExpanded)}
            className="flex items-center justify-between cursor-pointer select-none"
          >
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-primary" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-text">
                {activeTicker} Market summary
              </h2>
              {avgSentiment !== undefined && (
                <SentimentBadge
                  label={avgSentiment > 0.15 ? 'positive' : avgSentiment < -0.15 ? 'negative' : 'neutral'}
                  score={avgSentiment}
                />
              )}
            </div>

            <div className="flex items-center gap-2">
              {articles.length > 0 && (
                <span className="text-xs text-subtext font-medium">
                  {articles.length} sources analysed
                </span>
              )}
              <button className="p-1 text-subtext hover:text-text rounded transition-base">
                {summaryExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
            </div>
          </div>

          {summaryExpanded && (
            <p className="mt-2.5 text-sm text-subtext leading-relaxed font-normal animate-fade-in">
              {marketSummary}
            </p>
          )}
        </div>
      )}

      {/* ── Section Title ──────────────────────────────────── */}
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-base font-bold text-text">
          Top stories for {activeTicker}
        </h2>
        <button
          onClick={refetch}
          className="p-1.5 rounded-full hover:bg-surface text-subtext hover:text-text transition-base"
          title="Refresh news"
        >
          <RotateCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* ── News List States ───────────────────────────────── */}
      {loading ? (
        <div className="divide-y divide-border/50">
          {[...Array(4)].map((_, i) => (
            <NewsCardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <div className="border border-border rounded-lg p-6 text-center bg-surface my-4 flex flex-col items-center justify-center gap-2">
          <AlertCircle size={22} className="text-loss" />
          <p className="text-sm font-medium text-text">Unable to load news for {activeTicker}</p>
          <p className="text-xs text-subtext">{error}</p>
          <button
            onClick={refetch}
            className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-border rounded-md text-xs font-medium text-text hover:bg-surface transition-base shadow-sm"
          >
            <RotateCw size={13} />
            Try again
          </button>
        </div>
      ) : articles.length > 0 ? (
        <div className="divide-y divide-border/50">
          {articles.map((article) => (
            <NewsCard key={article.id || article.title} article={article} ticker={activeTicker} />
          ))}
        </div>
      ) : (
        <div className="border border-dashed border-border rounded-lg p-8 text-center text-sm text-subtext my-4">
          No news articles found for {activeTicker}.
        </div>
      )}
    </div>
  )
}
