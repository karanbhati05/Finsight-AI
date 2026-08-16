import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  Mic,
  Settings,
  MessageSquarePlus,
  LayoutGrid,
  X,
  Sparkles,
  TrendingUp,
  Landmark,
  Coins,
  Cpu,
  FileSpreadsheet,
  Moon,
  Sun,
  Shield,
  Trash2,
  ExternalLink,
  Check,
} from 'lucide-react'
import { searchStocks } from '../../api/market'
import useMarketStore from '../../store/marketStore'
import { useWebSocket } from '../../hooks/useWebSocket'

export function TopBar({ onToggleResearch, isResearchOpen }) {
  const [query, setQuery]             = useState('')
  const [results, setResults]         = useState([])
  const [showResults, setShowResults] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [activeMenu, setActiveMenu]   = useState(null) // 'settings' | 'feedback' | 'tools' | 'profile' | null
  const [feedbackSent, setFeedbackSent] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')

  const navigate = useNavigate()
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)
  const setActiveRegion = useMarketStore(s => s.setActiveRegion)
  const { isConnected } = useWebSocket()

  const inputRef   = useRef(null)
  const wrapperRef = useRef(null)
  const menuRef    = useRef(null)

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setShowResults(false)
      return
    }

    const timer = setTimeout(async () => {
      try {
        const data = await searchStocks(query.trim())
        setResults(data.results || [])
        setShowResults(true)
        setSelectedIndex(-1)
      } catch {
        setResults([])
      }
    }, 250)

    return () => clearTimeout(timer)
  }, [query])

  // Close menus on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowResults(false)
      }
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setActiveMenu(null)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleSelect = (symbol) => {
    if (!symbol) return
    setActiveTicker(symbol.toUpperCase())
    setQuery('')
    setShowResults(false)
    navigate(`/stock/${encodeURIComponent(symbol.toUpperCase())}`)
  }

  const handleKeyDown = (e) => {
    if (!showResults || results.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (selectedIndex >= 0 && selectedIndex < results.length) {
        handleSelect(results[selectedIndex].symbol)
      } else if (query.trim()) {
        handleSelect(query.trim().toUpperCase())
      }
    } else if (e.key === 'Escape') {
      setShowResults(false)
    }
  }

  const handleSendFeedback = (e) => {
    e.preventDefault()
    if (!feedbackText.trim()) return
    setFeedbackSent(true)
    setTimeout(() => {
      setFeedbackSent(false)
      setFeedbackText('')
      setActiveMenu(null)
    }, 1800)
  }

  return (
    <header className="h-16 border-b border-[#e8eaed] flex items-center px-4 sm:px-6 gap-3 sm:gap-6 flex-shrink-0 bg-white z-30 select-none relative">
      {/* ── FinSight Brand ─────────────────────────────────── */}
      <div
        className="flex items-center gap-2 cursor-pointer flex-shrink-0"
        onClick={() => {
          setActiveTicker('AAPL')
          setActiveRegion('us')
          navigate('/')
        }}
      >
        <div className="w-8 h-8 rounded-lg bg-[#1a73e8] flex items-center justify-center text-white shadow-xs">
          <TrendingUp size={18} strokeWidth={2.5} />
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-[20px] font-bold tracking-tight text-[#202124]">
            FinSight
          </span>
          <span className="text-[13px] font-semibold text-[#1a73e8]">
            AI
          </span>
        </div>
      </div>

      {/* ── Search Bar (Clean Pill Container) ──────────────── */}
      <div ref={wrapperRef} className="flex-1 max-w-2xl relative">
        <div className="flex items-center gap-3 bg-[#f1f3f4] hover:bg-[#e8eaed]/80 focus-within:bg-white focus-within:shadow-[0_1px_6px_rgba(32,33,36,0.28)] rounded-full px-4 py-2.5 border border-transparent focus-within:border-transparent transition-all">
          <Search size={18} className="text-[#5f6368] flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search for stocks, ETFs, indices and crypto (e.g. AAPL, NVDA, NIFTY 50)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => query.trim() && setShowResults(true)}
            className="flex-1 bg-transparent outline-none text-[14px] text-[#202124] placeholder:text-[#5f6368]"
          />
          {query && (
            <button
              onClick={() => {
                setQuery('')
                setShowResults(false)
              }}
              className="p-0.5 text-[#5f6368] hover:text-[#202124] rounded-full"
            >
              <X size={16} />
            </button>
          )}
          <Mic size={18} className="text-[#5f6368] cursor-pointer hover:text-[#202124] flex-shrink-0" />
        </div>

        {/* Autocomplete Dropdown */}
        {showResults && results.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-[#e8eaed] rounded-2xl shadow-xl z-50 overflow-hidden animate-fade-in divide-y divide-[#f1f3f4]">
            {results.map((r, i) => (
              <button
                key={`${r.symbol}-${i}`}
                onMouseEnter={() => setSelectedIndex(i)}
                onClick={() => handleSelect(r.symbol)}
                className={`
                  w-full flex items-center justify-between px-4 py-3 text-left transition-base cursor-pointer
                  ${selectedIndex === i ? 'bg-[#f8f9fa] text-[#1a73e8]' : 'hover:bg-[#f8f9fa] text-[#202124]'}
                `}
              >
                <div className="min-w-0 pr-3">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm">{r.symbol}</span>
                    {r.type && (
                      <span className="text-[10px] font-medium px-1.5 py-0.2 rounded bg-[#f1f3f4] text-[#5f6368]">
                        {r.type}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[#5f6368] truncate mt-0.5">{r.name}</p>
                </div>
                {r.exchange && (
                  <span className="text-xs text-[#80868b] font-normal flex-shrink-0">{r.exchange}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── Right Actions & Interactive Menus ────────────────── */}
      <div ref={menuRef} className="flex items-center gap-1 sm:gap-2 ml-auto relative">
        {/* Live WebSocket Status Pill */}
        <div
          className={`
            hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border select-none
            ${isConnected
              ? 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]'
              : 'bg-[#f8f9fa] text-[#5f6368] border-[#e8eaed]'
            }
          `}
          title={isConnected ? 'Connected to live price stream' : 'Polling live price stream'}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isConnected ? 'bg-[#0f9d58] animate-pulse' : 'bg-[#80868b]'
            }`}
          />
          <span>{isConnected ? 'LIVE' : 'POLLING'}</span>
        </div>

        {/* 1. Settings Gear Button */}
        <button
          onClick={() => setActiveMenu(activeMenu === 'settings' ? null : 'settings')}
          className={`p-2 rounded-full transition-base ${activeMenu === 'settings' ? 'bg-[#e8f0fe] text-[#1a73e8]' : 'hover:bg-[#f1f3f4] text-[#5f6368]'}`}
          title="Terminal Settings"
        >
          <Settings size={20} />
        </button>

        {/* 2. Feedback Button */}
        <button
          onClick={() => setActiveMenu(activeMenu === 'feedback' ? null : 'feedback')}
          className={`p-2 rounded-full transition-base ${activeMenu === 'feedback' ? 'bg-[#e8f0fe] text-[#1a73e8]' : 'hover:bg-[#f1f3f4] text-[#5f6368]'}`}
          title="Send Feedback"
        >
          <MessageSquarePlus size={20} />
        </button>

        {/* 3. Apps / Tools Grid Button */}
        <button
          onClick={() => setActiveMenu(activeMenu === 'tools' ? null : 'tools')}
          className={`p-2 rounded-full transition-base ${activeMenu === 'tools' ? 'bg-[#e8f0fe] text-[#1a73e8]' : 'hover:bg-[#f1f3f4] text-[#5f6368]'}`}
          title="Financial Tools & Hubs"
        >
          <LayoutGrid size={20} />
        </button>

        {/* 4. Research Drawer Trigger (Mobile/Tablet) */}
        {onToggleResearch && (
          <button
            onClick={onToggleResearch}
            className={`
              xl:hidden p-2 rounded-full transition-base border border-transparent
              ${isResearchOpen ? 'bg-[#e8f0fe] text-[#1a73e8]' : 'hover:bg-[#f1f3f4] text-[#5f6368]'}
            `}
            title="Open Research AI"
          >
            <Sparkles size={20} />
          </button>
        )}

        {/* 5. User Avatar Circle */}
        <div
          onClick={() => setActiveMenu(activeMenu === 'profile' ? null : 'profile')}
          className="ml-1 w-9 h-9 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-xs font-bold shadow-xs cursor-pointer hover:ring-2 hover:ring-[#1a73e8]/30 transition-base"
          title="Account Profile"
        >
          K
        </div>

        {/* ── DROPDOWN: 1. SETTINGS ───────────────────────────── */}
        {activeMenu === 'settings' && (
          <div className="absolute right-0 top-14 w-80 bg-white border border-[#e8eaed] rounded-2xl shadow-xl p-4 space-y-3 z-50 animate-fade-in text-xs text-[#202124]">
            <div className="flex items-center justify-between border-b border-[#f1f3f4] pb-2 font-bold text-sm">
              <span>Terminal Preferences</span>
              <button onClick={() => setActiveMenu(null)} className="text-[#5f6368] hover:text-[#202124]"><X size={16} /></button>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-[#5f6368]">Live Price WebSockets</span>
              <span className="text-[#0f9d58] font-bold">Enabled (10s sync)</span>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-[#5f6368]">AI Model Engine</span>
              <span className="text-[#1a73e8] font-bold">Gemini 2.5 Flash</span>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-[#5f6368]">NLP Sentiment</span>
              <span className="text-[#202124] font-semibold">ProsusAI / FinBERT</span>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-[#5f6368]">Macro Radar Provider</span>
              <span className="text-[#202124] font-semibold">Federal Reserve (FRED)</span>
            </div>

            <div className="pt-2 border-t border-[#f1f3f4] text-center">
              <button
                onClick={() => {
                  localStorage.clear()
                  window.location.reload()
                }}
                className="text-2xs text-[#d93025] hover:underline inline-flex items-center gap-1"
              >
                <Trash2 size={12} />
                <span>Clear Local Cache & Reset State</span>
              </button>
            </div>
          </div>
        )}

        {/* ── DROPDOWN: 2. FEEDBACK ───────────────────────────── */}
        {activeMenu === 'feedback' && (
          <div className="absolute right-0 top-14 w-80 bg-white border border-[#e8eaed] rounded-2xl shadow-xl p-4 space-y-3 z-50 animate-fade-in text-xs">
            <div className="flex items-center justify-between border-b border-[#f1f3f4] pb-2 font-bold text-sm text-[#202124]">
              <span>Send Feedback</span>
              <button onClick={() => setActiveMenu(null)} className="text-[#5f6368] hover:text-[#202124]"><X size={16} /></button>
            </div>

            {feedbackSent ? (
              <div className="py-6 text-center text-[#0f9d58] font-semibold space-y-1">
                <Check size={24} className="mx-auto" />
                <p>Thank you! Your feedback was recorded.</p>
              </div>
            ) : (
              <form onSubmit={handleSendFeedback} className="space-y-3">
                <textarea
                  rows={3}
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Describe an issue or request a new financial data feature..."
                  className="w-full p-2.5 rounded-xl border border-[#dadce0] outline-none text-xs text-[#202124] resize-none focus:border-[#1a73e8]"
                />
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveMenu(null)}
                    className="px-3 py-1.5 rounded-full text-[#5f6368] hover:bg-[#f1f3f4]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-full bg-[#1a73e8] hover:bg-[#1557b0] text-white font-semibold shadow-xs"
                  >
                    Submit
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* ── DROPDOWN: 3. APPS / FINANCIAL TOOLS ────────────── */}
        {activeMenu === 'tools' && (
          <div className="absolute right-0 top-14 w-72 bg-white border border-[#e8eaed] rounded-2xl shadow-xl p-3 z-50 animate-fade-in text-xs select-none">
            <div className="px-2 py-1 font-bold text-sm text-[#202124] border-b border-[#f1f3f4] mb-2">
              Financial Suites
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => {
                  setActiveRegion('us')
                  navigate('/')
                  setActiveMenu(null)
                }}
                className="p-3 rounded-xl hover:bg-[#f8f9fa] border border-transparent hover:border-[#e8eaed] text-left transition-base flex flex-col items-center text-center gap-1.5"
              >
                <div className="w-8 h-8 rounded-lg bg-[#e8f0fe] text-[#1a73e8] flex items-center justify-center">
                  <TrendingUp size={16} />
                </div>
                <span className="font-bold text-[#202124]">Market Feed</span>
              </button>

              <button
                onClick={() => {
                  setActiveRegion('macro')
                  navigate('/')
                  setActiveMenu(null)
                }}
                className="p-3 rounded-xl hover:bg-[#f8f9fa] border border-transparent hover:border-[#e8eaed] text-left transition-base flex flex-col items-center text-center gap-1.5"
              >
                <div className="w-8 h-8 rounded-lg bg-[#e6f4ea] text-[#0f9d58] flex items-center justify-center">
                  <Landmark size={16} />
                </div>
                <span className="font-bold text-[#202124]">FRED Macro</span>
              </button>

              <button
                onClick={() => {
                  setActiveRegion('crypto')
                  navigate('/')
                  setActiveMenu(null)
                }}
                className="p-3 rounded-xl hover:bg-[#f8f9fa] border border-transparent hover:border-[#e8eaed] text-left transition-base flex flex-col items-center text-center gap-1.5"
              >
                <div className="w-8 h-8 rounded-lg bg-[#fef7e0] text-[#f29900] flex items-center justify-center">
                  <Coins size={16} />
                </div>
                <span className="font-bold text-[#202124]">CoinGecko</span>
              </button>

              <button
                onClick={() => {
                  navigate('/stock/AAPL')
                  setActiveMenu(null)
                }}
                className="p-3 rounded-xl hover:bg-[#f8f9fa] border border-transparent hover:border-[#e8eaed] text-left transition-base flex flex-col items-center text-center gap-1.5"
              >
                <div className="w-8 h-8 rounded-lg bg-[#fce8e6] text-[#d93025] flex items-center justify-center">
                  <FileSpreadsheet size={16} />
                </div>
                <span className="font-bold text-[#202124]">FMP Financials</span>
              </button>
            </div>
          </div>
        )}

        {/* ── DROPDOWN: 4. USER PROFILE ───────────────────────── */}
        {activeMenu === 'profile' && (
          <div className="absolute right-0 top-14 w-64 bg-white border border-[#e8eaed] rounded-2xl shadow-xl p-4 space-y-3 z-50 animate-fade-in text-xs text-[#202124]">
            <div className="flex items-center gap-3 border-b border-[#f1f3f4] pb-3">
              <div className="w-10 h-10 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-sm font-bold shadow-xs">
                K
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-bold text-sm text-[#202124] truncate">Karan Bhati</p>
                <p className="text-2xs text-[#5f6368] truncate">Institutional Terminal Pro</p>
              </div>
            </div>

            <div className="space-y-1.5 text-xs text-[#5f6368]">
              <div className="flex justify-between py-0.5">
                <span>Account Status:</span>
                <span className="text-[#0f9d58] font-bold">Active</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span>API Keys:</span>
                <span className="text-[#1a73e8] font-bold">6 Connected</span>
              </div>
            </div>

            <button
              onClick={() => {
                setActiveMenu(null)
                navigate('/')
              }}
              className="w-full py-2 bg-[#f8f9fa] hover:bg-[#e8eaed] text-[#202124] rounded-xl font-semibold transition-base text-center block mt-2"
            >
              Terminal Dashboard
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
