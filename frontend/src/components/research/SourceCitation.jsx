import { useState } from 'react'
import { ChevronDown, ChevronUp, FileText, Newspaper, ExternalLink, ShieldCheck } from 'lucide-react'

export function SourceCitation({ sources = [] }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-2.5 pt-2 border-t border-border/60">
      {/* Expand Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-2xs font-semibold text-subtext hover:text-text hover:bg-surface border border-border/80 transition-base select-none"
      >
        <ShieldCheck size={12} className="text-primary" />
        <span>
          {sources.length} {sources.length === 1 ? 'source' : 'sources'} cited
        </span>
        {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {/* Expanded Sources List */}
      {isExpanded && (
        <div className="mt-2 space-y-1.5 animate-fade-in">
          {sources.map((src, i) => {
            const isFiling = (src.source_type || src.source || '').toLowerCase().includes('filing') ||
                             (src.source || '').toLowerCase().includes('10-k') ||
                             (src.source || '').toLowerCase().includes('10-q')
            const relevancePct = src.relevance ? Math.round(Number(src.relevance) * 100) : null

            return (
              <div
                key={i}
                className="flex items-start justify-between gap-2 p-2 rounded-lg bg-surface border border-border/60 text-xs"
              >
                <div className="flex items-start gap-2 min-w-0">
                  <div className="p-1 rounded bg-white border border-border/60 mt-0.5 flex-shrink-0">
                    {isFiling ? (
                      <FileText size={12} className="text-primary" />
                    ) : (
                      <Newspaper size={12} className="text-subtext" />
                    )}
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-text truncate">
                        {src.source || `Source ${i + 1}`}
                      </span>
                      {isFiling && (
                        <span className="text-[9px] font-bold uppercase tracking-wider bg-primary/10 text-primary px-1.5 py-0.2 rounded border border-primary/20">
                          SEC Filing
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mt-0.5 text-2xs text-muted">
                      {src.date && <span>{src.date}</span>}
                      {src.ticker && <span>• {src.ticker}</span>}
                      {relevancePct !== null && (
                        <span className="text-[#137333] font-medium">• {relevancePct}% relevance</span>
                      )}
                    </div>
                  </div>
                </div>

                {src.url && (
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-subtext hover:text-text rounded transition-base flex-shrink-0"
                    title="View source"
                  >
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
