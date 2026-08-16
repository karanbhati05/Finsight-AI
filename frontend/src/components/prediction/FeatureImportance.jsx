import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

const DEFAULT_IMPORTANCES = [
  { feature: 'Sentiment Score',       value: 0.284 },
  { feature: 'RSI (14-day)',          value: 0.212 },
  { feature: 'Rolling Sentiment (3d)',value: 0.175 },
  { feature: 'Price MA5 / MA20',      value: 0.138 },
  { feature: 'Volume Change %',       value: 0.106 },
  { feature: 'Daily Return',          value: 0.085 },
]

// Viridis-inspired color palette from highest to lowest importance
const VIRIDIS_COLORS = [
  '#1a73e8', // Primary Blue
  '#2a85ea',
  '#429bf0',
  '#6baef4',
  '#94c4f7',
  '#bdd9fb',
]

function formatFeatureName(rawName = '') {
  return rawName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function FeatureImportance({ features = {} }) {
  // Convert features dict to sorted array if present, otherwise use default
  let data = Object.keys(features).length > 0
    ? Object.entries(features)
        .map(([k, v]) => ({
          feature: formatFeatureName(k),
          value:   Math.abs(Number(v) || 0),
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6)
    : DEFAULT_IMPORTANCES

  // Normalize values if raw feature values were passed instead of importances
  const maxVal = Math.max(...data.map(d => d.value), 1)
  const chartData = data.map(d => ({
    feature:    d.feature,
    importance: Number((d.value / (maxVal || 1)).toFixed(3)),
    rawVal:     d.value,
  }))

  return (
    <div className="w-full h-64 select-none">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis type="number" domain={[0, 1]} hide />
          <YAxis
            type="category"
            dataKey="feature"
            tick={{ fontSize: 11, fill: '#202124', fontWeight: 500 }}
            axisLine={false}
            tickLine={false}
            width={130}
          />
          <Tooltip
            formatter={(val) => [`${(Number(val) * 100).toFixed(1)}%`, 'Relative Weight']}
            contentStyle={{ borderRadius: '8px', border: '1px solid #e8eaed', fontSize: '11px' }}
          />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]} barSize={16}>
            {chartData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={VIRIDIS_COLORS[index % VIRIDIS_COLORS.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
