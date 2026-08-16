export function ProbabilityGauge({ probability = 0.5 }) {
  const clampProb = Math.max(0, Math.min(1, Number(probability) || 0.5))
  const pct = Math.round(clampProb * 100)

  // Semi-circle parameters
  const radius = 65
  const strokeWidth = 12
  const center = 80
  const circumference = Math.PI * radius // half-circle circumference

  // Needle angle: -90 deg (left/0%) to +90 deg (right/100%)
  const angle = (clampProb - 0.5) * 180

  const gaugeColor = clampProb >= 0.55 ? '#0f9d58' : clampProb <= 0.45 ? '#d93025' : '#5f6368'

  return (
    <div className="flex flex-col items-center justify-center select-none py-1">
      <div className="relative w-40 h-24 flex items-end justify-center overflow-hidden">
        <svg viewBox="0 0 160 90" className="w-40 h-24">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#d93025" />
              <stop offset="45%" stopColor="#f9ab00" />
              <stop offset="55%" stopColor="#f9ab00" />
              <stop offset="100%" stopColor="#0f9d58" />
            </linearGradient>
          </defs>

          {/* Background Arc */}
          <path
            d="M 15 80 A 65 65 0 0 1 145 80"
            fill="none"
            stroke="#e8eaed"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Value Gradient Arc */}
          <path
            d="M 15 80 A 65 65 0 0 1 145 80"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - clampProb)}
            className="transition-all duration-700 ease-out"
          />

          {/* Needle / Pivot Indicator */}
          <g transform={`translate(${center}, 80) rotate(${angle})`} className="transition-transform duration-700 ease-out">
            <line x1="0" y1="0" x2="0" y2={-radius + 4} stroke="#202124" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="0" cy="0" r="5" fill="#202124" />
          </g>
        </svg>
      </div>

      {/* Probability percentage and sub-label */}
      <div className="text-center mt-1">
        <span className="text-xl font-bold tracking-tight" style={{ color: gaugeColor }}>
          {pct}%
        </span>
        <div className="flex justify-between w-36 text-[10px] text-muted font-medium mt-0.5">
          <span>0% (DOWN)</span>
          <span>50%</span>
          <span>100% (UP)</span>
        </div>
      </div>
    </div>
  )
}
