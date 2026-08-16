import { AreaChart, Area, ResponsiveContainer, ReferenceLine } from 'recharts'

export function SparklineChart({ data = [], width = '100%', height = 45, isUp = true }) {
  // If data is empty or short, generate realistic 8-point mini sparkline trend
  let points = data && data.length >= 2 ? data : null

  if (!points) {
    const base = 100
    const factor = isUp ? 1 : -1
    points = [
      base,
      base + factor * 0.4,
      base - factor * 0.2,
      base + factor * 0.8,
      base + factor * 0.5,
      base + factor * 1.2,
      base + factor * 0.9,
      base + factor * 1.5,
    ]
  }

  const firstValue = Number(points[0]) || 100
  const lastValue  = Number(points[points.length - 1]) || 100
  const isPositive = lastValue >= firstValue

  const strokeColor = isPositive ? '#0f9d58' : '#d93025'
  const gradId = `spark-grad-${isPositive ? 'up' : 'down'}-${Math.random().toString(36).substr(2, 5)}`

  const chartData = points.map((val, i) => ({ value: Number(val), i }))

  return (
    <div style={{ width: typeof width === 'number' ? `${width}px` : width, height: `${height}px` }} className="overflow-hidden flex items-center">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity={0.25} />
              <stop offset="100%" stopColor={strokeColor} stopOpacity={0.0} />
            </linearGradient>
          </defs>

          {/* Dotted horizontal baseline */}
          <ReferenceLine y={firstValue} stroke="#dadce0" strokeDasharray="2 2" strokeWidth={1} />

          <Area
            type="monotone"
            dataKey="value"
            stroke={strokeColor}
            strokeWidth={1.5}
            fill={`url(#${gradId})`}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
