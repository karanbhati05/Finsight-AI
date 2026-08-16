import { useState } from 'react'
import { X, Briefcase, Plus, DollarSign, Hash, Check } from 'lucide-react'
import usePortfolioStore from '../../store/portfolioStore'

export function AddPortfolioModal() {
  const isAddModalOpen  = usePortfolioStore(s => s.isAddModalOpen)
  const setAddModalOpen = usePortfolioStore(s => s.setAddModalOpen)
  const addPosition     = usePortfolioStore(s => s.addPosition)

  const [ticker, setTicker]     = useState('AAPL')
  const [shares, setShares]     = useState(10)
  const [buyPrice, setBuyPrice] = useState(220)
  const [submitting, setSubmitting] = useState(false)

  if (!isAddModalOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!ticker.trim() || shares <= 0 || buyPrice <= 0) return

    setSubmitting(true)
    try {
      await addPosition(ticker.trim().toUpperCase(), Number(shares), Number(buyPrice))
      setAddModalOpen(false)
      setTicker('')
    } catch (err) {
      console.error('Add position failed:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl border border-[#dadce0] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#e8eaed] flex items-center justify-between bg-[#f8f9fa]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#1a73e8] text-white flex items-center justify-center shadow-xs">
              <Briefcase size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#202124]">Add Portfolio Holding</h3>
              <p className="text-xs text-[#5f6368]">Track performance & live P&L</p>
            </div>
          </div>
          <button
            onClick={() => setAddModalOpen(false)}
            className="p-1.5 rounded-full text-[#5f6368] hover:text-[#202124] hover:bg-[#e8eaed] transition-base cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {/* Symbol */}
          <div className="space-y-1">
            <label className="font-semibold text-[#202124]">Stock Symbol</label>
            <input
              type="text"
              required
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g. AAPL, NVDA, TSLA, INFY"
              className="w-full p-2.5 rounded-xl border border-[#dadce0] text-sm font-bold uppercase outline-none focus:border-[#1a73e8]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Shares */}
            <div className="space-y-1">
              <label className="font-semibold text-[#202124]">Number of Shares</label>
              <div className="relative">
                <input
                  type="number"
                  step="any"
                  min="0.01"
                  required
                  value={shares}
                  onChange={(e) => setShares(e.target.value)}
                  className="w-full p-2.5 pl-7 rounded-xl border border-[#dadce0] text-sm font-semibold outline-none focus:border-[#1a73e8]"
                />
                <Hash size={14} className="absolute left-2.5 top-3 text-[#5f6368]" />
              </div>
            </div>

            {/* Buy Price */}
            <div className="space-y-1">
              <label className="font-semibold text-[#202124]">Average Buy Price ($)</label>
              <div className="relative">
                <input
                  type="number"
                  step="any"
                  min="0.01"
                  required
                  value={buyPrice}
                  onChange={(e) => setBuyPrice(e.target.value)}
                  className="w-full p-2.5 pl-7 rounded-xl border border-[#dadce0] text-sm font-semibold outline-none focus:border-[#1a73e8]"
                />
                <DollarSign size={14} className="absolute left-2.5 top-3 text-[#5f6368]" />
              </div>
            </div>
          </div>

          {/* Quick suggestions */}
          <div className="pt-1">
            <span className="text-[11px] text-[#5f6368]">Quick add:</span>
            <div className="flex gap-1.5 mt-1">
              {['AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOGL'].map(s => (
                <button
                  type="button"
                  key={s}
                  onClick={() => setTicker(s)}
                  className="px-2 py-0.5 rounded-md bg-[#f1f3f4] hover:bg-[#e8eaed] text-[11px] font-semibold text-[#3c4043]"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-3 border-t border-[#e8eaed]">
            <button
              type="button"
              onClick={() => setAddModalOpen(false)}
              className="px-4 py-2 rounded-full text-xs font-semibold text-[#5f6368] hover:bg-[#f1f3f4]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#1a73e8] hover:bg-[#1557b0] text-white font-semibold text-xs shadow-xs transition-base cursor-pointer disabled:opacity-50"
            >
              <Plus size={14} />
              <span>{submitting ? 'Saving...' : 'Add to Portfolio'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
