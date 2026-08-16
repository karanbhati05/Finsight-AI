import useMarketStore from '../../store/marketStore'

const TABS = [
  { id: 'us',         label: 'US' },
  { id: 'europe',     label: 'Europe' },
  { id: 'india',      label: 'India' },
  { id: 'currencies', label: 'Currencies' },
  { id: 'crypto',     label: 'Crypto' },
  { id: 'futures',    label: 'Futures' },
]

export function MarketTabs() {
  const activeRegion    = useMarketStore(s => s.activeRegion)
  const setActiveRegion = useMarketStore(s => s.setActiveRegion)

  return (
    <div className="flex items-center gap-1 border-b border-border overflow-x-auto">
      {TABS.map(tab => {
        const isActive = activeRegion === tab.id
        return (
          <button
            key={tab.id}
            onClick={() => setActiveRegion(tab.id)}
            className={`
              px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-base btn-press
              border-b-2 -mb-px
              ${isActive
                ? 'text-primary border-primary'
                : 'text-subtext border-transparent hover:text-text hover:bg-surface'
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
