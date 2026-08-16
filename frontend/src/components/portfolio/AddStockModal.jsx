import { useState, useEffect, useRef } from 'react'
import { X, Search, Loader2, DollarSign, Layers } from 'lucide-react'
import { searchStocks } from '../../api/market'
import usePortfolioStore from '../../store/portfolioStore'

export function AddStockModal({ isOpen, onClose }) {
  const [ticker, setTicker]         = useState('')
  const [shares, setShares]         = useState('')
  const [buyPrice, setBuyPrice]     = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [isSubmitting, setIsSubmitting]   = useState(false)
  const [error, setError]           = useState('')

  const addPosition = usePortfolioStore(s => s.addPosition)
  const modalRef    = useRef(null)

  // Reset form on open
  useEffect(() => {
    if (isOpen) {
      setTicker('')
      setShares('')
      setBuyPrice('')
      setSearchResults([])
      setError('')
    }
  }, [isOpen])

  // Debounced search
  useEffect(() => {
    if (!ticker || ticker.length < 1) {
      setSearchResults([])
      return
    }

    const timer = setTimeout(async () => {
      setSearchLoading(true)
      try {
        const data = await searchStocks(ticker.trim())
        setSearchResults(data.results || [])
      } catch (err) {
        setSearchResults([])
      } finally {
        setSearchLoading(false)
      }
    }, 250)

    return () => clearTimeout(timer)
  }, [ticker])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!ticker || !shares || !buyPrice) {
      setError('Please fill in all fields.')
      return
    }

    const numShares = Number(shares)
    const numPrice  = Number(buyPrice)

    if (isNaN(numShares) || numShares <= 0 || isNaN(numPrice) || numPrice <= 0) {
      setError('Shares and buy price must be positive numbers.')
      return
    }

    setIsSubmitting(true)
    setError('')

    try {
      await addPosition(ticker.toUpperCase().trim(), numShares, numPrice)
      onClose && onClose()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to add holding.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in">
      <div
        ref={modalRef}
        className="bg-white border border-border rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-slide-in"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border bg-surface/50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
              <Layers size={18} />
            </div>
            <h3 className="text-sm font-bold text-text">Add Holding to Portfolio</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-subtext hover:text-text hover:bg-surface transition-base"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-2.5 rounded-lg bg-[#fce8e6] text-[#c5221f] text-xs font-medium">
              {error}
            </div>
          )}

          {/* Ticker Search */}
          <div className="space-y-1 relative">
            <label className="text-xs font-semibold text-text">Stock Ticker / Company</label>
            <div className="flex items-center gap-2 bg-surface rounded-xl px-3 py-2 border border-border focus-within:border-primary focus-within:bg-white transition-base">
              <Search size={15} className="text-subtext" />
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="e.g. AAPL, MSFT, ^NSEI"
                className="flex-1 bg-transparent text-sm text-text outline-none uppercase font-semibold placeholder:font-normal placeholder:text-muted"
                required
              />
              {searchLoading && <Loader2 size={14} className="animate-spin text-primary" />}
            </div>

            {/* Dropdown Results */}
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-border rounded-xl shadow-lg max-h-40 overflow-y-auto z-50 divide-y divide-border/40">
                {searchResults.map((r, i) => (
                  <button
                    key={`${r.symbol}-${i}`}
                    type="button"
                    onClick={() => {
                      setTicker(r.symbol)
                      setSearchResults([])
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-surface flex items-center justify-between text-xs transition-base"
                  >
                    <div>
                      <span className="font-bold text-text">{r.symbol}</span>
                      <span className="text-2xs text-subtext truncate ml-2">{r.name}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Shares Input */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-text">Number of Shares</label>
            <input
              type="number"
              step="any"
              min="0.0001"
              value={shares}
              onChange={(e) => setShares(e.target.value)}
              placeholder="e.g. 10"
              className="w-full bg-surface rounded-xl px-3.5 py-2 text-sm text-text border border-border focus:border-primary focus:bg-white outline-none transition-base"
              required
            />
          </div>

          {/* Buy Price Input */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-text">Average Buy Price ($)</label>
            <div className="flex items-center gap-1.5 bg-surface rounded-xl px-3 py-2 border border-border focus-within:border-primary focus-within:bg-white transition-base">
              <DollarSign size={15} className="text-subtext" />
              <input
                type="number"
                step="any"
                min="0.01"
                value={buyPrice}
                onChange={(e) => setBuyPrice(e.target.value)}
                placeholder="e.g. 185.50"
                className="flex-1 bg-transparent text-sm text-text outline-none"
                required
              />
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-subtext hover:bg-surface transition-base"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-primary text-white hover:bg-primary-hover shadow-xs transition-base btn-press disabled:opacity-50"
            >
              {isSubmitting ? 'Adding...' : 'Add to Portfolio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
