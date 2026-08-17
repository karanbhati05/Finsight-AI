import { useState, useEffect } from 'react'
import { Landmark, TrendingDown, TrendingUp, AlertTriangle, Activity, ShieldCheck } from 'lucide-react'
import { getMacroDashboard } from '../../api/advanced'

export function MacroRadar() {
  const [macro, setMacro] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)

    getMacroDashboard()
      .then(data => {
        if (!cancelled && data && data.treasury_10y) {
          setMacro(data)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [])

  if (loading && !macro) {
    return (
      <div className="space-y-6 my-4 animate-pulse">
        <div className="p-5 rounded-2xl bg-[#f8f9fa] border border-[#e8eaed] h-28" />
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="p-4 rounded-xl border border-[#e8eaed] bg-white h-28" />
          ))}
        </div>
      </div>
    )
  }

  const m = macro || {}

  return (
    <div className="space-y-6 my-4 animate-fade-in">
      {/* ── Macro Radar Hero Banner ────────────────────────── */}
      <div className="p-5 rounded-2xl bg-gradient-to-br from-[#f8f9fa] to-[#e8f0fe]/50 border border-[#e8eaed] space-y-3 shadow-xs">
        <div className="flex items-center gap-2 text-[#1a73e8]">
          <Landmark size={20} />
          <h2 className="text-base font-bold text-[#202124]">
            Global Macroeconomic Radar
          </h2>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#1a73e8] text-white">
            FRED LIVE
          </span>
        </div>

        <p className="text-xs text-[#3c4043] leading-relaxed">
          {m.ai_macro_summary || "Tracking Federal Reserve monetary policy, inflation metrics, and Treasury yield spreads live."}
        </p>
      </div>

      {/* ── Macro Indicators Grid ──────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
        {/* 1. 10-Year Treasury Yield */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <div className="flex justify-between items-start">
            <span className="text-xs text-[#5f6368] font-medium">{m.treasury_10y?.label || "10-Year US Treasury"}</span>
            <Activity size={16} className="text-[#1a73e8]" />
          </div>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.treasury_10y?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            Status: <span className="text-[#1a73e8]">{m.treasury_10y?.status || "Elevated"}</span>
          </p>
        </div>

        {/* 2. Yield Curve Spread */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <div className="flex justify-between items-start">
            <span className="text-xs text-[#5f6368] font-medium">{m.treasury_spread?.label || "10Y - 2Y Spread"}</span>
            {m.treasury_spread?.isInverted ? (
              <AlertTriangle size={16} className="text-[#d93025]" />
            ) : (
              <ShieldCheck size={16} className="text-[#0f9d58]" />
            )}
          </div>
          <p className={`text-2xl font-bold mt-1 ${m.treasury_spread?.isInverted ? 'text-[#d93025]' : 'text-[#0f9d58]'}`}>
            {m.treasury_spread?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            {m.treasury_spread?.status || "Normal Spread"}
          </p>
        </div>

        {/* 3. Fed Funds Rate */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <div className="flex justify-between items-start">
            <span className="text-xs text-[#5f6368] font-medium">{m.fed_funds_rate?.label || "Fed Funds Rate"}</span>
            <Landmark size={16} className="text-[#5f6368]" />
          </div>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.fed_funds_rate?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            {m.fed_funds_rate?.status || "Policy Rate"}
          </p>
        </div>

        {/* 4. Inflation CPI */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <span className="text-xs text-[#5f6368] font-medium">{m.inflation_cpi?.label || "CPI Inflation (YoY)"}</span>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.inflation_cpi?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#0f9d58] mt-1">
            {m.inflation_cpi?.status || "Annual Rate"}
          </p>
        </div>

        {/* 5. Unemployment Rate */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <span className="text-xs text-[#5f6368] font-medium">{m.unemployment_rate?.label || "US Unemployment"}</span>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.unemployment_rate?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            {m.unemployment_rate?.status || "Labor Market"}
          </p>
        </div>

        {/* 6. Real GDP Growth */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <span className="text-xs text-[#5f6368] font-medium">{m.gdp_growth?.label || "Real GDP Growth"}</span>
          <p className="text-2xl font-bold text-[#0f9d58] mt-1">
            +{m.gdp_growth?.value || 2.8}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            {m.gdp_growth?.status || "Resilient Growth"}
          </p>
        </div>
      </div>
    </div>
  )
}
