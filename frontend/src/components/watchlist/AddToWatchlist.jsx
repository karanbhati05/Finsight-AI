import { useState, useEffect, useRef } from 'react'
import { Search, X, Loader2, Plus, ArrowDown, ArrowUp } from 'lucide-react'
import { searchStocks } from '../../api/market'
import useWatchlistStore from '../../store/watchlistStore'

const POPULAR_SUGGESTIONS = [
  { symbol: '.DJI',  name: 'Dow Jones Industrial Average', exchange: 'INDEXDJX',  price: 53732.41, change_pct: -0.20 },
  { symbol: 'AAPL',  name: 'Apple Inc',                    exchange: 'NASDAQ (US)', price: 228.60,   change_pct: 0.85 },
  { symbol: 'NVDA',  name: 'NVIDIA Corp',                  exchange: 'NASDAQ (US)', price: 225.16,   change_pct: -0.06 },
  { symbol: 'MSFT',  name: 'Microsoft Corp',               exchange: 'NASDAQ (US)', price: 448.20,   change_pct: 0.42 },
  { symbol: '^NSEI', name: 'NIFTY 50',                     exchange: 'NSE (India)', price: 24366.00, change_pct: -0.12 },
]

export function AddToWatchlist({ onClose }) {
  const [query, setQuery]     = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const addTicker = useWatchlistStore(s => s.addTicker)
  const inputRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

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
    }, 250)

    return () => clearTimeout(timer)
  }, [query])

  const handleSelect = async (symbol) => {
    if (!symbol) return
    await addTicker(symbol)
    onClose && onClose()
  }

  const itemsToShow = results.length > 0 ? results : POPULAR_SUGGESTIONS

  return (
    <div
      ref={containerRef}
      className="bg-[#f8f9fa] border border-[#dadce0] rounded-2xl p-3 my-2 shadow-lg animate-fade-in relative z-30"
    >
      {/* ── Top Row: Header & Done button ───────────────────── */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#e8eaed]">
        <span className="text-xs font-bold text-[#202124]">Add to Watchlist</span>
        <button
          onClick={onClose}
          className="text-xs font-semibold text-[#1a73e8] hover:underline"
        >
          Done
        </button>
      </div>

      {/* ── Search Input Field ──────────────────────────────── */}
      <div className="flex items-center gap-2 bg-white rounded-lg px-3 py-2 border-b-2 border-[#1a73e8] shadow-xs">
        <Search size={16} className="text-[#1a73e8]" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search symbols or company name"
          className="flex-1 bg-transparent text-xs text-[#202124] outline-none placeholder:text-[#5f6368]"
        />
        {query && (
          <button onClick={() => setQuery('')} className="text-[#5f6368] hover:text-[#202124]">
            <X size={15} />
          </button>
        )}
      </div>

      {/* ── Suggestions / Results List ───────────────────────── */}
      <div className="mt-3">
        <p className="text-[11px] font-medium text-[#5f6368] mb-1.5 px-1">
          {results.length > 0 ? 'Search Results' : 'Popular Assets'}
        </p>

        <div className="space-y-1 max-h-56 overflow-y-auto divide-y divide-[#f1f3f4]">
          {itemsToShow.map((item, i) => {
            const isUp = (item.change_pct || 0) >= 0
            return (
              <button
                key={`${item.symbol}-${i}`}
                onClick={() => handleSelect(item.symbol)}
                className="w-full flex items-center justify-between p-2 hover:bg-white rounded-lg text-left transition-base group cursor-pointer"
              >
                {/* Left: + and Name */}
                <div className="flex items-center gap-2.5 min-w-0 pr-2">
                  <Plus size={15} className="text-[#1a73e8] flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-[#202124] truncate">
                      {item.symbol} {item.exchange && <span className="font-normal text-[#5f6368]">: {item.exchange}</span>}
                    </p>
                    <p className="text-[11px] text-[#5f6368] truncate">{item.name}</p>
                  </div>
                </div>

                {/* Right: Price & Colored Indicator */}
                {item.price && (
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-semibold text-[#202124]">
                      {Number(item.price).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </p>
                    <div className={`flex items-center justify-end gap-1 text-[11px] font-bold ${isUp ? 'text-[#0f9d58]' : 'text-[#d93025]'}`}>
                      <span>{isUp ? '+' : ''}{item.change_pct}%</span>
                      <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-white ${isUp ? 'bg-[#0f9d58]' : 'bg-[#d93025]'}`}>
                        {isUp ? <ArrowUp size={8} strokeWidth={3} /> : <ArrowDown size={8} strokeWidth={3} />}
                      </div>
                    </div>
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
