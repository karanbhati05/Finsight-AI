export function SentimentBadge({ label = 'neutral', score }) {
  const normLabel = (label || 'neutral').toLowerCase()

  const styles = {
    positive: 'bg-[#e6f4ea] text-[#137333] border border-[#ceead6]',
    negative: 'bg-[#fce8e6] text-[#c5221f] border border-[#fad2cf]',
    neutral:  'bg-[#f1f3f4] text-[#5f6368] border border-[#e8eaed]',
  }

  const badgeStyle = styles[normLabel] || styles.neutral
  const hasScore = score !== undefined && score !== null && !isNaN(score)
  const formattedScore = hasScore ? (score > 0 ? `+${Number(score).toFixed(2)}` : Number(score).toFixed(2)) : null

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-2xs font-semibold uppercase tracking-wider ${badgeStyle}`}
    >
      <span>{normLabel}</span>
      {formattedScore && (
        <span className="font-medium opacity-80 text-[10px]">
          {formattedScore}
        </span>
      )}
    </span>
  )
}
