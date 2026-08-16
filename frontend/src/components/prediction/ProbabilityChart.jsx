import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const prob = Number(payload[0].value)
    const pct = Math.round(prob * 100)
    const isUp = prob >= 0.5

    return (
      <div className="bg-white border border-border p-2.5 rounded-lg shadow-md text-xs space-y-1">
        <p className="font-semibold text-text">{label}</p>
        <p className={`font-bold ${isUp ? 'text-gain' : 'text-loss'}`}>
          P(Up): {pct}% ({prob.toFixed(3)})
        </p>
        <p className="text-[10px] text-subtext">
          {prob >= 0.65 ? '🟢 Strong Buy Signal' : prob <= 0.35 ? '🔴 Strong Sell Signal' : '⚪ Neutral / Hold'}
        </p>
      </div>
    )
  }
  return null
}

export function ProbabilityChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-muted bg-surface rounded-lg">
        Historical probability data unavailable
      </div>
    )
  }

  // Format history array [{ date, probability }]
  const formattedData = data.map((d) => ({
    date:        d.date ? d.date.substring(5) : '', // 'MM-DD'
    fullDate:    d.date,
    probability: Number(d.probability) || 0.5,
  }))

  return (
    <div className="w-full h-52 pt-2">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="probGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#1a73e8" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#1a73e8" stopOpacity={0.0} />
            </linearGradient>
          </defs>

          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: '#80868b' }}
            axisLine={{ stroke: '#e8eaed' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            ticks={[0.2, 0.5, 0.8]}
            tickFormatter={(v) => `${Math.round(v * 100)}%`}
            tick={{ fontSize: 10, fill: '#80868b' }}
            axisLine={false}
            tickLine={false}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Reference Zones */}
          <ReferenceLine y={0.65} stroke="#0f9d58" strokeDasharray="3 3" label={{ value: 'Strong Buy (>65%)', fill: '#0f9d58', fontSize: 9, position: 'insideTopRight' }} />
          <ReferenceLine y={0.5} stroke="#80868b" strokeDasharray="2 2" />
          <ReferenceLine y={0.35} stroke="#d93025" strokeDasharray="3 3" label={{ value: 'Strong Sell (<35%)', fill: '#d93025', fontSize: 9, position: 'insideBottomRight' }} />

          <Area
            type="monotone"
            dataKey="probability"
            stroke="#1a73e8"
            strokeWidth={2}
            fill="url(#probGradient)"
            dot={{ r: 2, fill: '#1a73e8' }}
            activeDot={{ r: 4, fill: '#1a73e8' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
