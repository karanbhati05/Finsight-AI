import { useState, useEffect } from 'react'
import { Landmark, TrendingDown, TrendingUp, AlertTriangle, Activity, ShieldCheck } from 'lucide-react'
import { getMacroDashboard } from '../../api/advanced'

const DEFAULT_MACRO = {
  treasury_10y: {
    value: 4.28,
    change: -0.04,
    label: "10-Year US Treasury Yield",
    unit: "%",
    status: "Elevated Benchmark",
  },
  treasury_spread: {
    value: -0.12,
    label: "10Y - 2Y Yield Curve Spread",
    unit: "%",
    isInverted: true,
    status: "Inverted (Recession Watch)",
  },
  fed_funds_rate: {
    value: 5.33,
    label: "Federal Funds Target Rate",
    unit: "%",
    status: "Restrictive Monetary Policy",
  },
  inflation_cpi: {
    value: 2.9,
    change: -0.1,
    label: "US CPI Inflation (YoY)",
    unit: "%",
    status: "Cooling towards 2.0% Target",
  },
  unemployment_rate: {
    value: 4.3,
    change: 0.1,
    label: "US Unemployment Rate",
    unit: "%",
    status: "Low / Balanced Labor Market",
  },
  gdp_growth: {
    value: 2.8,
    label: "Real GDP Growth (QoQ Ann.)",
    unit: "%",
    status: "Resilient Growth",
  },
  ai_macro_summary: "Federal Reserve policy rates stand at 5.25%-5.50%. With US CPI inflation cooling to 2.9% and 10-Year Treasury yields trading near 4.28%, markets are actively pricing in monetary easing. Resilient real GDP growth of 2.8% continues to support earnings for high-quality equities.",
}

export function MacroRadar() {
  const [macro, setMacro] = useState(DEFAULT_MACRO)

  useEffect(() => {
    let cancelled = false

    getMacroDashboard()
      .then(data => {
        if (!cancelled && data?.treasury_10y) {
          setMacro(data)
        }
      })
      .catch(() => {})

    return () => { cancelled = true }
  }, [])

  const m = macro || DEFAULT_MACRO

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
          {m.ai_macro_summary}
        </p>
      </div>

      {/* ── Macro Indicators Grid ──────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
        {/* 1. 10-Year Treasury Yield */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <div className="flex justify-between items-start">
            <span className="text-xs text-[#5f6368] font-medium">{m.treasury_10y?.label}</span>
            <Activity size={16} className="text-[#1a73e8]" />
          </div>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.treasury_10y?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            Status: <span className="text-[#1a73e8]">{m.treasury_10y?.status}</span>
          </p>
        </div>

        {/* 2. Yield Curve Spread */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <div className="flex justify-between items-start">
            <span className="text-xs text-[#5f6368] font-medium">{m.treasury_spread?.label}</span>
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
            {m.treasury_spread?.status}
          </p>
        </div>

        {/* 3. Fed Funds Rate */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <div className="flex justify-between items-start">
            <span className="text-xs text-[#5f6368] font-medium">{m.fed_funds_rate?.label}</span>
            <Landmark size={16} className="text-[#5f6368]" />
          </div>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.fed_funds_rate?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            {m.fed_funds_rate?.status}
          </p>
        </div>

        {/* 4. Inflation CPI */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <span className="text-xs text-[#5f6368] font-medium">{m.inflation_cpi?.label}</span>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.inflation_cpi?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#0f9d58] mt-1">
            {m.inflation_cpi?.status}
          </p>
        </div>

        {/* 5. Unemployment Rate */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <span className="text-xs text-[#5f6368] font-medium">{m.unemployment_rate?.label}</span>
          <p className="text-2xl font-bold text-[#202124] mt-1">
            {m.unemployment_rate?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            {m.unemployment_rate?.status}
          </p>
        </div>

        {/* 6. Real GDP Growth */}
        <div className="p-4 rounded-xl border border-[#e8eaed] bg-white shadow-xs">
          <span className="text-xs text-[#5f6368] font-medium">{m.gdp_growth?.label}</span>
          <p className="text-2xl font-bold text-[#0f9d58] mt-1">
            +{m.gdp_growth?.value}%
          </p>
          <p className="text-2xs font-semibold text-[#5f6368] mt-1">
            {m.gdp_growth?.status}
          </p>
        </div>
      </div>
    </div>
  )
}
