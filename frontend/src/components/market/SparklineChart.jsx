import { AreaChart, Area, ResponsiveContainer } from 'recharts'

export function SparklineChart({ data = [], width = 80, height = 40 }) {
  if (!data || data.length === 0) {
    return <div style={{ width, height }} className="bg-gray-100 rounded" />
  }

  const isPositive = data[data.length - 1] >= data[0]
  const chartData  = data.map((value, i) => ({ value, i }))

  return (
    <div style={{ width, height }} className="overflow-hidden">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <Area
            type="monotone"
            dataKey="value"
            stroke={isPositive ? '#0f9d58' : '#d93025'}
            strokeWidth={1.5}
            fill={isPositive ? '#e6f4ea' : '#fce8e6'}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
