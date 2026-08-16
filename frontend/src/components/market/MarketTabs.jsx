import useMarketStore from '../../store/marketStore'

const TABS = [
  { id: 'us',            label: 'US' },
  { id: 'europe',        label: 'Europe' },
  { id: 'india',         label: 'India' },
  { id: 'macro',         label: 'Macro Radar (FRED)' },
  { id: 'currencies',    label: 'Currencies' },
  { id: 'crypto',        label: 'Crypto (CoinGecko)' },
  { id: 'futures',       label: 'Futures' },
]

export function MarketTabs() {
  const activeRegion    = useMarketStore(s => s.activeRegion)
  const setActiveRegion = useMarketStore(s => s.setActiveRegion)

  return (
    <div className="flex items-center gap-2 overflow-x-auto py-2 select-none no-scrollbar">
      {TABS.map(tab => {
        const isActive = activeRegion === tab.id
        return (
          <button
            key={tab.id}
            onClick={() => setActiveRegion(tab.id)}
            className={`
              px-4 py-1.5 rounded-full text-[13px] font-medium whitespace-nowrap transition-base
              ${isActive
                ? 'bg-[#f1f3f4] text-[#202124] border border-[#202124] font-semibold'
                : 'bg-transparent text-[#3c4043] border border-transparent hover:bg-[#f1f3f4]'
              }
            `}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
