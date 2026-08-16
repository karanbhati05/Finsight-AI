import { AreaChart, Area, ResponsiveContainer, ReferenceLine } from 'recharts'

export function SparklineChart({ data = [], width = '100%', height = 45 }) {
  if (!data || data.length === 0) {
    return <div style={{ width: typeof width === 'number' ? `${width}px` : width, height: `${height}px` }} className="bg-[#f8f9fa] rounded-lg" />
  }

  const firstValue = Number(data[0]) || 0
  const lastValue  = Number(data[data.length - 1]) || 0
  const isPositive = lastValue >= firstValue

  const strokeColor = isPositive ? '#0f9d58' : '#d93025'
  const gradId = `spark-grad-${isPositive ? 'up' : 'down'}-${Math.random().toString(36).substr(2, 5)}`

  const chartData = data.map((val, i) => ({ value: Number(val), i }))

  return (
    <div style={{ width: typeof width === 'number' ? `${width}px` : width, height: `${height}px` }} className="overflow-hidden">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 4, right: 0, bottom: 2, left: 0 }}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity={0.22} />
              <stop offset="100%" stopColor={strokeColor} stopOpacity={0.0} />
            </linearGradient>
          </defs>

          {/* Dotted horizontal baseline */}
          <ReferenceLine y={firstValue} stroke="#bdc1c6" strokeDasharray="2 2" strokeWidth={1} />

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
