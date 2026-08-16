import { useState, useEffect } from 'react'
import { ChevronUp, ChevronDown, Sparkles, ExternalLink } from 'lucide-react'
import { MarketTabs } from '../market/MarketTabs'
import { IndexGrid }  from '../market/IndexGrid'
import { NewsCardSkeleton } from '../common/Skeleton'
import useMarketStore from '../../store/marketStore'
import useResearchStore from '../../store/researchStore'
import client from '../../api/client'

/* ── Sentiment Badge ─────────────────────────────────────── */
function SentimentBadge({ label, score }) {
  const styles = {
    positive: 'bg-positive-bg text-positive-text',
    negative: 'bg-negative-bg text-negative-text',
    neutral:  'bg-neutral-bg text-neutral-text',
  }
  const style = styles[label] || styles.neutral

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-2xs font-medium uppercase tracking-wide ${style}`}>
      {label}
      {score !== undefined && (
        <span className="font-normal opacity-75">
          {score > 0 ? '+' : ''}{typeof score === 'number' ? score.toFixed(2) : score}
        </span>
      )}
    </span>
  )
}

/* ── News Card ────────────────────────────────────────────── */
function NewsCard({ article }) {
  const [expanded, setExpanded] = useState(false)
  const addMessage = useResearchStore(s => s.addMessage)

  const timeAgo = (dateStr) => {
    if (!dateStr) return ''
    try {
      const diff = Date.now() - new Date(dateStr).getTime()
      const hours = Math.floor(diff / 3600000)
      if (hours < 1) return 'Just now'
      if (hours < 24) return `${hours}h ago`
      const days = Math.floor(hours / 24)
      return `${days}d ago`
    } catch { return '' }
  }

  const handleDiveDeep = () => {
    addMessage('user', `Tell me more about: "${article.title}"`)
  }

  return (
    <div className="border-b border-border py-4">
      {/* Title row with expand toggle */}
      <div className="flex items-start justify-between gap-3 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-text leading-snug">
            {article.title}
          </h3>
          <div className="flex items-center gap-2 mt-1.5 text-xs text-subtext">
            <span>{article.source}</span>
            {article.source_count > 1 && (
              <>
                <span>·</span>
                <span>{article.source_count} sites</span>
              </>
            )}
            <span>·</span>
            <span>{timeAgo(article.published_at)}</span>
          </div>
        </div>
        <button className="p-1 rounded hover:bg-surface flex-shrink-0 mt-0.5">
          {expanded ? <ChevronUp size={16} className="text-subtext" /> : <ChevronDown size={16} className="text-subtext" />}
        </button>
      </div>

      {/* Expanded body */}
      {expanded && (
        <div className="mt-3 animate-fade-in">
          <p className="text-sm text-subtext leading-relaxed">{article.summary}</p>

          <div className="flex items-center justify-between mt-3">
            <button
              onClick={handleDiveDeep}
              className="flex items-center gap-1.5 text-sm text-text font-medium px-3 py-1.5 rounded-full border border-border hover:bg-surface transition-base btn-press"
            >
              <Sparkles size={14} className="text-primary" />
              Dive deeper with AI
            </button>

            <div className="flex items-center gap-2">
              <SentimentBadge label={article.sentiment_label} score={article.sentiment_score} />
              {article.url && (
                <a href={article.url} target="_blank" rel="noopener noreferrer" className="p-1 hover:bg-surface rounded transition-base">
                  <ExternalLink size={14} className="text-subtext" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── News Feed Section ────────────────────────────────────── */
function NewsFeed({ ticker }) {
  const [articles, setArticles]       = useState([])
  const [summary, setSummary]         = useState('')
  const [loading, setLoading]         = useState(true)
  const [summaryExpanded, setSummaryExpanded] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)

    client.get(`/news/${ticker}?limit=20&days_back=7`)
      .then(data => {
        if (!cancelled) {
          setArticles(data.articles || [])
          setSummary(data.market_summary || '')
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setArticles([])
          setLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [ticker])

  return (
    <div className="mt-6">
      {/* Market summary card */}
      {summary && (
        <div className="mb-4">
          <div
            className="flex items-start justify-between gap-3 cursor-pointer"
            onClick={() => setSummaryExpanded(!summaryExpanded)}
          >
            <h2 className="text-lg font-semibold text-text">Market summary</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-subtext">{articles.length} sites</span>
              <button className="p-1 rounded hover:bg-surface">
                {summaryExpanded ? <ChevronUp size={16} className="text-subtext" /> : <ChevronDown size={16} className="text-subtext" />}
              </button>
            </div>
          </div>
          {summaryExpanded && (
            <p className="mt-2 text-sm text-subtext leading-relaxed animate-fade-in">{summary}</p>
          )}
        </div>
      )}

      {/* News list */}
      {loading ? (
        [...Array(4)].map((_, i) => <NewsCardSkeleton key={i} />)
      ) : articles.length > 0 ? (
        articles.map(article => (
          <NewsCard key={article.id} article={article} />
        ))
      ) : (
        <p className="text-sm text-muted py-8 text-center">No news available for {ticker}.</p>
      )}
    </div>
  )
}

/* ── Main Feed ────────────────────────────────────────────── */
export function MainFeed() {
  const indices        = useMarketStore(s => s.indices)
  const indicesLoading = useMarketStore(s => s.indicesLoading)
  const activeTicker   = useMarketStore(s => s.activeTicker)

  return (
    <div className="px-6 py-4 max-w-4xl">
      {/* Market Tabs */}
      <MarketTabs />

      {/* Index Cards */}
      <div className="mt-4">
        <IndexGrid indices={indices} loading={indicesLoading} />
      </div>

      {/* News Feed */}
      <NewsFeed ticker={activeTicker} />
    </div>
  )
}
