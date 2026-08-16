import { useState } from 'react'
import { ChevronUp, ChevronDown, ExternalLink, Globe } from 'lucide-react'
import { SentimentBadge } from './SentimentBadge'
import { DiveDeepButton } from './DiveDeepButton'

function formatTimeAgo(dateStr) {
  if (!dateStr) return ''
  try {
    const published = new Date(dateStr).getTime()
    if (isNaN(published)) return ''
    const diffMs = Date.now() - published
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    if (diffHours < 1) {
      const diffMins = Math.max(1, Math.floor(diffMs / (1000 * 60)))
      return `${diffMins}m ago`
    }
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  } catch {
    return ''
  }
}

export function NewsCard({ article, ticker = 'AAPL' }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!article) return null

  const {
    title,
    summary,
    source,
    source_count = 1,
    published_at,
    url,
    sentiment_label,
    sentiment_score,
    entities,
  } = article

  const timeAgo = formatTimeAgo(published_at)
  const companies = entities?.companies || []

  return (
    <div className="border-b border-border py-4 transition-base hover:bg-surface/30 px-1 rounded-sm">
      {/* Header Row: Title & expand toggle */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-start justify-between gap-3 cursor-pointer select-none group"
      >
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-text group-hover:text-primary transition-base leading-snug line-clamp-2">
            {title}
          </h3>

          {/* Metadata info line */}
          <div className="flex items-center flex-wrap gap-2 mt-1.5 text-xs text-subtext">
            <span className="font-medium text-text/80">{source || 'News'}</span>
            {source_count > 1 && (
              <>
                <span>·</span>
                <span className="inline-flex items-center gap-0.5 text-2xs bg-surface px-1.5 py-0.5 rounded border border-border">
                  <Globe size={10} className="text-subtext" />
                  {source_count} sites
                </span>
              </>
            )}
            {timeAgo && (
              <>
                <span>·</span>
                <span>{timeAgo}</span>
              </>
            )}
          </div>
        </div>

        {/* Toggle chevron */}
        <button
          className="p-1 rounded text-subtext group-hover:text-text hover:bg-surface transition-base flex-shrink-0 mt-0.5"
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Expanded Details Body */}
      {isExpanded && (
        <div className="mt-3 pt-2 border-t border-border/50 animate-fade-in space-y-3">
          {/* Article Summary text */}
          <p className="text-sm text-subtext leading-relaxed font-normal">
            {summary || title}
          </p>

          {/* Company / Entity Tags if present */}
          {companies.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-2xs text-muted font-medium">Entities:</span>
              {companies.slice(0, 4).map((c, i) => (
                <span
                  key={i}
                  className="text-2xs bg-surface text-subtext px-2 py-0.5 rounded-full border border-border"
                >
                  {c}
                </span>
              ))}
            </div>
          )}

          {/* Action Row: AI Dive Deep, Sentiment Badge, External Link */}
          <div className="flex items-center justify-between pt-1 gap-2">
            <DiveDeepButton title={title} ticker={ticker} />

            <div className="flex items-center gap-2">
              <SentimentBadge label={sentiment_label} score={sentiment_score} />
              {url && (
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="p-1.5 rounded-full hover:bg-surface text-subtext hover:text-text border border-transparent hover:border-border transition-base"
                  title="Open source article"
                >
                  <ExternalLink size={13} />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
