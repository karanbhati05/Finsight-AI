import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { SparklineChart } from '../market/SparklineChart'
import { ArrowUp, ArrowDown } from 'lucide-react'
import { getTopCrypto, getForexRates } from '../../api/advanced'
import useMarketStore from '../../store/marketStore'

const DEFAULT_COINS = [
  {
    id: 'bitcoin',
    symbol: 'BTC',
    name: 'Bitcoin',
    image: 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
    current_price: 64250.00,
    total_volume: 28500000000,
    price_change_percentage_24h: 2.45,
    sparkline: [61500, 61800, 62000, 61800, 62400, 63100, 63800, 64250],
  },
  {
    id: 'ethereum',
    symbol: 'ETH',
    name: 'Ethereum',
    image: 'https://assets.coingecko.com/coins/images/279/large/ethereum.png',
    current_price: 3480.50,
    total_volume: 16200000000,
    price_change_percentage_24h: 1.85,
    sparkline: [3300, 3320, 3350, 3320, 3400, 3420, 3450, 3480],
  },
  {
    id: 'solana',
    symbol: 'SOL',
    name: 'Solana',
    image: 'https://assets.coingecko.com/coins/images/4128/large/solana.png',
    current_price: 162.80,
    total_volume: 4200000000,
    price_change_percentage_24h: 5.12,
    sparkline: [148, 150, 153, 158, 160, 161, 162.8],
  },
  {
    id: 'binancecoin',
    symbol: 'BNB',
    name: 'BNB',
    image: 'https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png',
    current_price: 585.40,
    total_volume: 980000000,
    price_change_percentage_24h: -0.42,
    sparkline: [592, 590, 588, 586, 584, 585.4],
  },
]

export function CryptoHub({ view = 'crypto' }) {
  const [coins, setCoins]     = useState(DEFAULT_COINS)
  const [forex, setForex]     = useState({ USD: 1, EUR: 0.915, GBP: 0.774, INR: 83.95, JPY: 154.2 })
  const [loading, setLoading] = useState(false)
  const [amount, setAmount]   = useState(100)
  const [fromCurr, setFromCurr] = useState('USD')
  const [toCurr, setToCurr]   = useState('EUR')

  const navigate = useNavigate()
  const setActiveTicker = useMarketStore(s => s.setActiveTicker)

  useEffect(() => {
    let cancelled = false

    if (view === 'crypto') {
      getTopCrypto(20)
        .then(res => {
          if (!cancelled && res?.coins && res.coins.length > 0) {
            setCoins(res.coins)
          }
        })
        .catch(() => {})
    } else {
      getForexRates()
        .then(res => {
          if (!cancelled && res?.rates) {
            setForex(res.rates)
          }
        })
        .catch(() => {})
    }

    return () => { cancelled = true }
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
    return (
      <div className="space-y-6 my-4 animate-fade-in">
        {/* Currency Converter Card */}
        <div className="p-5 rounded-2xl border border-[#e8eaed] bg-white shadow-xs space-y-4">
          <h3 className="text-base font-bold text-[#202124]">Global Currency Converter</h3>

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
                  {Object.keys(forex).map(c => <option key={c} value={c}>{c}</option>)}
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
                  {Object.keys(forex).map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Forex Matrix Table */}
        <div className="border border-[#e8eaed] rounded-2xl overflow-hidden bg-white shadow-xs">
          <div className="px-5 py-3.5 bg-[#f8f9fa] border-b border-[#e8eaed] font-bold text-xs text-[#202124]">
            Major World Currency Exchange Rates (Base USD)
          </div>
          <div className="divide-y divide-[#f1f3f4] text-xs">
            {Object.entries(forex).map(([code, rate]) => (
              <div key={code} className="px-5 py-3 flex items-center justify-between hover:bg-[#f8f9fa]">
                <span className="font-bold text-[#202124]">USD / {code}</span>
                <span className="font-semibold text-[#1a73e8]">{typeof rate === 'number' ? rate.toFixed(4) : rate}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const items = coins.length > 0 ? coins : DEFAULT_COINS

  return (
    <div className="space-y-4 my-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-[#202124]">Top Cryptocurrencies by Market Cap</h2>
          <p className="text-xs text-[#5f6368]">Live data powered by CoinGecko</p>
        </div>
      </div>

      <div className="border border-[#e8eaed] rounded-2xl overflow-hidden bg-white shadow-xs divide-y divide-[#f1f3f4]">
        {items.map((c, i) => {
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

              {/* Mini Sparkline */}
              <div className="w-20 h-6 hidden sm:block">
                <SparklineChart data={c.sparkline} height={24} />
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
        })}
      </div>
    </div>
  )
}
