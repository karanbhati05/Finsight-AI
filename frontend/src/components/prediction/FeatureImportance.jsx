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
  { feature: 'RSI (14-day)',          value: 0.284 },
  { feature: 'MA5 / MA20 Ratio',      value: 0.235 },
  { feature: 'News Sentiment Score',  value: 0.182 },
  { feature: 'Price Momentum (10d)',  value: 0.145 },
  { feature: 'Volume Acceleration',   value: 0.098 },
  { feature: 'Realized Volatility',   value: 0.056 },
]

// Harmonious blue palette from highest to lowest importance
const VIRIDIS_COLORS = [
  '#1a73e8',
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

function parseNumericVal(val) {
  if (typeof val === 'number') return Math.abs(val)
  if (!val) return 0.0
  const clean = String(val).replace(/[^0-9.-]/g, '')
  const num = parseFloat(clean)
  return isNaN(num) ? 0.0 : Math.abs(num)
}

export function FeatureImportance({ features = {} }) {
  // Convert features dict to sorted array if present, otherwise use default
  let data = Object.keys(features).length > 0
    ? Object.entries(features)
        .map(([k, v]) => ({
          feature: formatFeatureName(k),
          value:   parseNumericVal(v),
          rawDisplay: v,
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6)
    : DEFAULT_IMPORTANCES

  // Normalize values if raw feature values were passed instead of importances
  const maxVal = Math.max(...data.map(d => d.value), 1)
  const chartData = data.map(d => ({
    feature:    d.feature,
    importance: Number((d.value / (maxVal || 1)).toFixed(3)),
    rawVal:     d.rawDisplay || d.value,
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
            width={140}
          />
          <Tooltip
            formatter={(val, name, item) => [`Value: ${item.payload.rawVal} (${(Number(val) * 100).toFixed(1)}% weight)`, 'Factor Influence']}
            contentStyle={{ borderRadius: '10px', border: '1px solid #dadce0', fontSize: '11px', boxShadow: '0 2px 8px rgba(32,33,36,0.1)' }}
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
