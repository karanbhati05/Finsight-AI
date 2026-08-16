import { useState } from 'react'
import { X, CheckSquare, Bell, Clock, TrendingUp, Check } from 'lucide-react'

export function CreateTaskModal({ isOpen, onClose, defaultTicker = 'AAPL' }) {
  const [taskType, setTaskType] = useState('price_alert')
  const [ticker, setTicker]     = useState(defaultTicker)
  const [threshold, setThreshold] = useState(250)
  const [condition, setCondition] = useState('above')
  const [saved, setSaved]       = useState(false)

  if (!isOpen) return null

  const handleSaveTask = (e) => {
    e.preventDefault()
    setSaved(true)

    // Save task to local store
    const existing = JSON.parse(localStorage.getItem('finsight_tasks') || '[]')
    const newTask = {
      id: Date.now(),
      type: taskType,
      ticker: ticker.toUpperCase(),
      threshold,
      condition,
      created_at: new Date().toISOString(),
      status: 'Active',
    }
    localStorage.setItem('finsight_tasks', JSON.stringify([newTask, ...existing]))

    setTimeout(() => {
      setSaved(false)
      onClose()
    }, 1200)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl border border-[#dadce0] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#e8eaed] flex items-center justify-between bg-[#f8f9fa]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#1a73e8] text-white flex items-center justify-center shadow-xs">
              <CheckSquare size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#202124]">Create Automated Task</h3>
              <p className="text-xs text-[#5f6368]">AI monitoring & price trigger alerts</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#5f6368] hover:text-[#202124] hover:bg-[#e8eaed] transition-base cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {saved ? (
          <div className="py-12 px-6 text-center space-y-2 animate-fade-in">
            <div className="w-12 h-12 rounded-full bg-[#e6f4ea] text-[#0f9d58] flex items-center justify-center mx-auto">
              <Check size={24} strokeWidth={3} />
            </div>
            <h4 className="text-base font-bold text-[#202124]">Task Created & Scheduled!</h4>
            <p className="text-xs text-[#5f6368]">FinSight AI is now actively monitoring your condition.</p>
          </div>
        ) : (
          /* Task Form */
          <form onSubmit={handleSaveTask} className="p-6 space-y-4 text-xs">
            {/* Task Type Selector */}
            <div className="space-y-1">
              <label className="font-semibold text-[#202124]">Task Type</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setTaskType('price_alert')}
                  className={`p-3 rounded-xl border flex items-center gap-2 text-left transition-base ${taskType === 'price_alert' ? 'border-[#1a73e8] bg-[#e8f0fe] text-[#1a73e8] font-bold' : 'border-[#dadce0] text-[#3c4043]'}`}
                >
                  <Bell size={16} />
                  <span>Price Target Alert</span>
                </button>

                <button
                  type="button"
                  onClick={() => setTaskType('morning_brief')}
                  className={`p-3 rounded-xl border flex items-center gap-2 text-left transition-base ${taskType === 'morning_brief' ? 'border-[#1a73e8] bg-[#e8f0fe] text-[#1a73e8] font-bold' : 'border-[#dadce0] text-[#3c4043]'}`}
                >
                  <Clock size={16} />
                  <span>Daily AI Briefing</span>
                </button>
              </div>
            </div>

            {/* Target Ticker */}
            <div className="space-y-1">
              <label className="font-semibold text-[#202124]">Target Asset</label>
              <input
                type="text"
                required
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="e.g. AAPL, NVDA, NIFTY 50"
                className="w-full p-2.5 rounded-xl border border-[#dadce0] text-sm font-bold uppercase outline-none focus:border-[#1a73e8]"
              />
            </div>

            {taskType === 'price_alert' && (
              <div className="grid grid-cols-2 gap-3">
                {/* Condition */}
                <div className="space-y-1">
                  <label className="font-semibold text-[#202124]">Trigger Condition</label>
                  <select
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-[#dadce0] text-xs font-semibold bg-white outline-none"
                  >
                    <option value="above">Price rises above</option>
                    <option value="below">Price drops below</option>
                  </select>
                </div>

                {/* Price Threshold */}
                <div className="space-y-1">
                  <label className="font-semibold text-[#202124]">Threshold ($)</label>
                  <input
                    type="number"
                    step="any"
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value))}
                    className="w-full p-2.5 rounded-xl border border-[#dadce0] text-sm font-bold outline-none focus:border-[#1a73e8]"
                  />
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-3 border-t border-[#e8eaed]">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-full text-xs font-semibold text-[#5f6368] hover:bg-[#f1f3f4]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#1a73e8] hover:bg-[#1557b0] text-white font-semibold text-xs shadow-xs transition-base cursor-pointer"
              >
                <Check size={14} />
                <span>Save Monitoring Task</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
