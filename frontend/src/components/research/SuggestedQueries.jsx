import { useState, useEffect } from 'react'
import { Sparkles, Search } from 'lucide-react'
import { getSuggestions } from '../../api/chat'

export function SuggestedQueries({ ticker = 'AAPL', onSelectQuery }) {
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading]         = useState(false)

  const defaultQueries = [
    "What's going on with the markets today?",
    "What is driving the correction in AI chipmaker stocks?",
    "How are major retail stocks expected to perform this earnings week?",
  ]

  useEffect(() => {
    let cancelled = false
    setLoading(true)

    getSuggestions(ticker)
      .then(data => {
        if (!cancelled) {
          const list = data.suggestions && data.suggestions.length > 0
            ? data.suggestions.slice(0, 3)
            : defaultQueries
          setSuggestions(list)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSuggestions(defaultQueries)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [ticker])

  if (loading) {
    return (
      <div className="space-y-2.5 py-1">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-14 bg-[#f8f9fa] rounded-2xl animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-2.5">
      {suggestions.map((query, i) => (
        <button
          key={i}
          onClick={() => onSelectQuery && onSelectQuery(query)}
          className="flex items-center justify-between gap-3 w-full text-left p-4 rounded-2xl bg-[#f0f4f9]/80 hover:bg-[#f0f4f9] border border-transparent hover:border-[#dadce0] transition-all group cursor-pointer"
        >
          <span className="text-[13px] font-normal text-[#202124] leading-snug flex-1">
            {query}
          </span>
          <div className="w-8 h-8 rounded-full bg-white/80 group-hover:bg-white flex items-center justify-center text-[#202124] shadow-xs flex-shrink-0 transition-base">
            <Sparkles size={14} className="text-[#202124]" />
          </div>
        </button>
      ))}
    </div>
  )
}
