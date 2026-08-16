import { useState, useEffect, useRef } from 'react'
import { Search, Mic, Settings, LayoutGrid } from 'lucide-react'
import { searchStocks } from '../../api/market'

export function TopBar() {
  const [query, setQuery]       = useState('')
  const [results, setResults]   = useState([])
  const [showResults, setShowResults] = useState(false)
  const inputRef  = useRef(null)
  const wrapperRef = useRef(null)

  // Debounced search
  useEffect(() => {
    if (query.length < 1) {
      setResults([])
      setShowResults(false)
      return
    }

    const timer = setTimeout(async () => {
      try {
        const data = await searchStocks(query)
        setResults(data.results || [])
        setShowResults(true)
      } catch {
        setResults([])
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query])

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowResults(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <header className="h-16 border-b border-border flex items-center px-6 gap-4 flex-shrink-0 bg-white">
      {/* Logo */}
      <div className="flex items-center gap-2 mr-4">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-primary">
          <path d="M3 3h7v7H3V3zm11 0h7v7h-7V3zM3 14h7v7H3v-7zm11 0h7v7h-7v-7z" fill="currentColor" opacity="0.2"/>
          <path d="M4 4h5v5H4V4zm11 0h5v5h-5V4zM4 15h5v5H4v-5zm11 0h5v5h-5v-5z" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
        <span className="text-lg font-semibold text-text hidden sm:inline">FinSight</span>
      </div>

      {/* Search bar */}
      <div ref={wrapperRef} className="flex-1 max-w-2xl relative">
        <div className="flex items-center gap-2 bg-surface rounded-full px-4 py-2 border border-transparent focus-within:border-primary focus-within:bg-white transition-base">
          <Search size={18} className="text-subtext flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search for stocks, ETFs and more"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent outline-none text-sm text-text placeholder:text-muted"
          />
          <Mic size={18} className="text-subtext cursor-pointer hover:text-text flex-shrink-0" />
        </div>

        {/* Search results dropdown */}
        {showResults && results.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-border rounded-lg shadow-lg z-50 overflow-hidden animate-fade-in">
            {results.map((r, i) => (
              <button
                key={`${r.symbol}-${i}`}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-surface text-left transition-base"
                onClick={() => {
                  setQuery(r.symbol)
                  setShowResults(false)
                }}
              >
                <span className="font-medium text-sm text-text">{r.symbol}</span>
                <span className="text-xs text-subtext truncate flex-1">{r.name}</span>
                <span className="text-2xs text-muted">{r.exchange}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-3 ml-4">
        <button className="p-2 rounded-full hover:bg-surface transition-base">
          <Settings size={18} className="text-subtext" />
        </button>
        <button className="p-2 rounded-full hover:bg-surface transition-base">
          <LayoutGrid size={18} className="text-subtext" />
        </button>
        {/* User avatar */}
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm font-medium cursor-pointer">
          K
        </div>
      </div>
    </header>
  )
}
