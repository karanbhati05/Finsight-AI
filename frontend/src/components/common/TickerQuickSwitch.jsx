import { useState, useRef, useEffect } from 'react'
import { Search, ChevronDown, X, Sparkles } from 'lucide-react'
import { searchStocks } from '../../api/market'
import useMarketStore from '../../store/marketStore'
import useResearchStore from '../../store/researchStore'

const POPULAR_TICKERS = [
  { symbol: 'AAPL', label: 'Apple' },
  { symbol: 'NVDA', label: 'NVIDIA' },
  { symbol: 'TSLA', label: 'Tesla' },
  { symbol: 'MSFT', label: 'Microsoft' },
  { symbol: 'AMZN', label: 'Amazon' },
  { symbol: 'GOOGL', label: 'Google' },
  { symbol: 'BTC-USD', label: 'Bitcoin' },
  { symbol: '^NSEI', label: 'NIFTY 50' },
]

export function TickerQuickSwitch({ currentTicker, onSelect, className = '' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const setActiveTicker = useMarketStore(s => s.setActiveTicker)
  const setResearchTicker = useResearchStore(s => s.setActiveTicker)
  const wrapperRef = useRef(null)

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setLoading(false)
      return
    }

    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await searchStocks(query.trim())
        setResults(data.results || [])
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 200)

    return () => clearTimeout(timer)
  }, [query])

  // Close on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleChoose = (sym) => {
    const clean = sym.toUpperCase()
    setActiveTicker(clean)
    setResearchTicker(clean)
    if (onSelect) onSelect(clean)
    setIsOpen(false)
    setQuery('')
  }

  const displayTicker = currentTicker || 'AAPL'

  return (
    <div ref={wrapperRef} className={`relative flex items-center flex-wrap gap-1.5 ${className}`}>
      {/* Quick Pills */}
      <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
        {POPULAR_TICKERS.map((t) => {
          const isSelected = displayTicker.toUpperCase() === t.symbol.toUpperCase()
          return (
            <button
              key={t.symbol}
              onClick={() => handleChoose(t.symbol)}
              className={`
                px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-base cursor-pointer
                ${isSelected
                  ? 'bg-[#1a73e8] text-white shadow-xs'
                  : 'bg-[#f1f3f4] text-[#3c4043] hover:bg-[#e8eaed] hover:text-[#202124]'
                }
              `}
            >
              {t.symbol}
            </button>
          )
        })}

        {/* Search More Trigger Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[#e8f0fe] hover:bg-[#d2e3fc] text-[#1a73e8] text-xs font-bold transition-base cursor-pointer shadow-2xs"
        >
          <Search size={12} />
          <span>Switch / Search Any Ticker</span>
          <ChevronDown size={11} />
        </button>
      </div>

      {/* Floating Instant Search Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-1.5 w-72 sm:w-80 bg-white border border-[#e8eaed] rounded-2xl shadow-xl z-50 p-3 animate-fade-in space-y-2">
          <div className="flex items-center justify-between border-b border-[#f1f3f4] pb-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#202124]">
              <Sparkles size={13} className="text-[#1a73e8]" />
              <span>Select Active Stock / Asset</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-[#5f6368] hover:text-[#202124]">
              <X size={14} />
            </button>
          </div>

          <div className="flex items-center gap-2 bg-[#f8f9fa] border border-[#dadce0] rounded-xl px-2.5 py-1.5 focus-within:border-[#1a73e8] focus-within:bg-white">
            <Search size={14} className="text-[#5f6368]" />
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search e.g. TSLA, RELIANCE, BTC"
              className="w-full bg-transparent text-xs text-[#202124] outline-none"
            />
          </div>

          {/* Results list */}
          <div className="max-h-48 overflow-y-auto divide-y divide-[#f1f3f4] text-xs">
            {loading ? (
              <div className="p-3 text-center text-[#5f6368]">Searching live markets...</div>
            ) : results.length > 0 ? (
              results.map((r, i) => (
                <button
                  key={`${r.symbol}-${i}`}
                  onClick={() => handleChoose(r.symbol)}
                  className="w-full p-2 flex items-center justify-between hover:bg-[#f8f9fa] text-left transition-colors cursor-pointer rounded-lg"
                >
                  <div>
                    <span className="font-bold text-[#202124]">{r.symbol}</span>
                    <p className="text-2xs text-[#5f6368] truncate">{r.name}</p>
                  </div>
                  <span className="text-2xs text-[#80868b]">{r.exchange || 'GLOBAL'}</span>
                </button>
              ))
            ) : query ? (
              <div className="p-3 text-center text-[#5f6368]">No matching stocks found.</div>
            ) : (
              <div className="p-2 text-2xs text-[#80868b] text-center">Type any company name or ticker above</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
