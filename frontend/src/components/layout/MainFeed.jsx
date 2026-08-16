import { MarketTabs } from '../market/MarketTabs'
import { IndexGrid }  from '../market/IndexGrid'
import { NewsFeed }   from '../news/NewsFeed'
import { PredictionSection } from '../prediction/PredictionSection'
import { MacroRadar } from '../macro/MacroRadar'
import { CryptoHub }  from '../crypto/CryptoHub'
import useMarketStore from '../../store/marketStore'

export function MainFeed() {
  const activeRegion   = useMarketStore(s => s.activeRegion)
  const indices        = useMarketStore(s => s.indices)
  const indicesLoading = useMarketStore(s => s.indicesLoading)

  return (
    <div className="px-4 sm:px-8 py-5 max-w-4xl pb-16 space-y-4">
      {/* ── Market Tabs (US, Europe, India, Macro, Currencies, Crypto, Futures) */}
      <MarketTabs />

      {/* ── Dynamic Tab View Rendering ────────────────────────── */}
      {activeRegion === 'crypto' ? (
        <CryptoHub view="crypto" />
      ) : activeRegion === 'currencies' ? (
        <CryptoHub view="currencies" />
      ) : activeRegion === 'macro' ? (
        <MacroRadar />
      ) : (
        <>
          {/* Index Cards Grid */}
          <div className="mt-2">
            <IndexGrid
              indices={indices}
              loading={indicesLoading}
            />
          </div>

          {/* FinSight News Feed with FinBERT AI */}
          <NewsFeed />

          {/* ML Price Prediction & Sharpe Comparison Section */}
          <PredictionSection />
        </>
      )}
    </div>
  )
}
