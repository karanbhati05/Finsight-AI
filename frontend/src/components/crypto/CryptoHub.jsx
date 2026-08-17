import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { SparklineChart } from '../market/SparklineChart'
import { ArrowUp, ArrowDown, RefreshCw } from 'lucide-react'
import { getTopCrypto, getForexRates } from '../../api/advanced'
import useMarketStore from '../../store/marketStore'

export function CryptoHub({ view = 'crypto' }) {
  const [coins, setCoins]     = useState([])
  const [forex, setForex]     = useState({})
  const [loading, setLoading] = useState(true)
  const [amount, setAmount]   = useState(100)
  const [fromCurr, setFromCurr] = useState('USD')
  const [toCurr, setToCurr]   = useState('EUR')

  const navigate = useNavigate()
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)

  const fetchData = () => {
    setLoading(true)
    if (view === 'crypto') {
      getTopCrypto(20)
        .then(res => {
          if (res?.coins && res.coins.length > 0) {
            setCoins(res.coins)
          }
          setLoading(false)
        })
        .catch(() => setLoading(false))
    } else {
      getForexRates()
        .then(res => {
          if (res?.rates) {
            setForex(res.rates)
          }
          setLoading(false)
        })
        .catch(() => setLoading(false))
    }
  }

  useEffect(() => {
    fetchData()
  }, [view])

  const handleCoinClick = (symbol) => {
    setActiveTicker(symbol)
    navigate(`/stock/${symbol}`)
  }

  // Currency Converter calculation
  const fromRate = forex[fromCurr] || 1.0
  const toRate = forex[toCurr] || 1.0
  const convertedValue = ((amount / fromRate) * toRate).toFixed(2)

  if (view === 'currencies') {
    const currencyCodes = Object.keys(forex).length > 0 ? Object.keys(forex) : ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'SGD']

    return (
      <div className="space-y-6 my-4 animate-fade-in">
        {/* Currency Converter Card */}
        <div className="p-5 rounded-2xl border border-[#e8eaed] bg-white shadow-xs space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-[#202124]">Global Live Currency Converter</h3>
            <span className="text-2xs font-semibold px-2 py-0.5 rounded-full bg-[#e8f0fe] text-[#1a73e8]">
              Live FX Feeds
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
            {/* Amount & From */}
            <div className="space-y-1">
              <label className="text-xs text-[#5f6368] font-medium">Amount</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl border border-[#dadce0] text-sm font-semibold outline-none focus:border-[#1a73e8]"
                />
                <select
                  value={fromCurr}
                  onChange={(e) => setFromCurr(e.target.value)}
                  className="p-2.5 rounded-xl border border-[#dadce0] text-sm font-semibold bg-white outline-none"
                >
                  {currencyCodes.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            {/* Converted Output */}
            <div className="space-y-1 sm:col-span-2">
              <label className="text-xs text-[#5f6368] font-medium">Converted To ({toCurr})</label>
              <div className="flex items-center gap-3">
                <div className="flex-1 p-2.5 rounded-xl bg-[#f8f9fa] border border-[#e8eaed] text-lg font-bold text-[#1a73e8]">
                  {convertedValue} {toCurr}
                </div>
                <select
                  value={toCurr}
                  onChange={(e) => setToCurr(e.target.value)}
                  className="p-2.5 rounded-xl border border-[#dadce0] text-sm font-semibold bg-white outline-none"
                >
                  {currencyCodes.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Forex Matrix Table */}
        <div className="border border-[#e8eaed] rounded-2xl overflow-hidden bg-white shadow-xs">
          <div className="px-5 py-3.5 bg-[#f8f9fa] border-b border-[#e8eaed] font-bold text-xs text-[#202124] flex justify-between items-center">
            <span>Major World Currency Exchange Rates (Base USD)</span>
            <button onClick={fetchData} className="text-xs text-[#1a73e8] flex items-center gap-1 hover:underline cursor-pointer">
              <RefreshCw size={12} /> Refresh
            </button>
          </div>
          <div className="divide-y divide-[#f1f3f4] text-xs">
            {Object.entries(forex).length > 0 ? (
              Object.entries(forex).map(([code, rate]) => (
                <div key={code} className="px-5 py-3 flex items-center justify-between hover:bg-[#f8f9fa] transition-colors">
                  <span className="font-bold text-[#202124]">USD / {code}</span>
                  <span className="font-semibold text-[#1a73e8] font-mono">{typeof rate === 'number' ? rate.toFixed(4) : rate}</span>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-[#5f6368]">Loading live foreign exchange rates...</div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 my-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-[#202124]">Top Cryptocurrencies by Market Cap</h2>
          <p className="text-xs text-[#5f6368]">Live real-time market data powered by CoinGecko</p>
        </div>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#f1f3f4] hover:bg-[#e8eaed] text-xs font-semibold text-[#3c4043] transition-base cursor-pointer"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="border border-[#e8eaed] rounded-2xl overflow-hidden bg-white shadow-xs divide-y divide-[#f1f3f4]">
        {coins.length > 0 ? (
          coins.map((c, i) => {
            const isUp = (c.price_change_percentage_24h || 0) >= 0
            return (
              <div
                key={c.id || i}
                onClick={() => handleCoinClick(`${c.symbol}-USD`)}
                className="p-3.5 sm:px-5 flex items-center justify-between hover:bg-[#f8f9fa] transition-base cursor-pointer group"
              >
                {/* Rank & Coin Identity */}
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-xs font-semibold text-[#80868b] w-4">{c.market_cap_rank || i + 1}</span>
                  {c.image && <img src={c.image} alt={c.name} className="w-7 h-7 rounded-full flex-shrink-0" />}
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-[#202124] truncate group-hover:text-[#1a73e8]">
                      {c.name} <span className="font-normal text-[#5f6368]">({c.symbol})</span>
                    </p>
                    <p className="text-2xs text-[#5f6368]">
                      Vol: ${(Number(c.total_volume || 0) / 1e6).toFixed(0)}M
                    </p>
                  </div>
                </div>

                {/* Dynamic Scaled Sparkline */}
                <div className="w-24 h-7 hidden sm:block">
                  <SparklineChart data={c.sparkline} height={28} isUp={isUp} />
                </div>

                {/* Price & 24h Change */}
                <div className="text-right flex-shrink-0">
                  <p className="text-xs font-bold text-[#202124]">
                    ${Number(c.current_price || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </p>
                  <div className={`flex items-center justify-end gap-1 text-[11px] font-bold ${isUp ? 'text-[#0f9d58]' : 'text-[#d93025]'}`}>
                    <span>{isUp ? '+' : ''}{c.price_change_percentage_24h}%</span>
                    <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-white ${isUp ? 'bg-[#0f9d58]' : 'bg-[#d93025]'}`}>
                      {isUp ? <ArrowUp size={8} strokeWidth={3} /> : <ArrowDown size={8} strokeWidth={3} />}
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        ) : (
          <div className="p-8 text-center text-[#5f6368] space-y-2">
            <RefreshCw size={20} className="animate-spin mx-auto text-[#1a73e8]" />
            <p className="text-xs">Fetching real-time cryptocurrency feeds...</p>
          </div>
        )}
      </div>
    </div>
  )
}
