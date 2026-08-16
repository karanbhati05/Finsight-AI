import { Plus, ListTodo, Search, LineChart } from 'lucide-react'

export function QuickActions({ onActionClick }) {
  const actions = [
    {
      id:    'create_portfolio',
      label: 'Create a portfolio',
      icon:  Plus,
      query: 'Help me construct a diversified portfolio based on current market sentiment.',
    },
    {
      id:    'create_task',
      label: 'Create task',
      icon:  ListTodo,
      query: 'Set up an automated monitoring task for stock price movements and SEC 8-K filings.',
    },
    {
      id:    'deep_search',
      label: 'Deep Search',
      icon:  Search,
      query: 'Perform a comprehensive SEC 10-K deep search on key risk factors and competitive headwinds.',
    },
    {
      id:    'analyse',
      label: 'Analyse watchlist',
      icon:  LineChart,
      query: 'Analyse technical momentum indicators and FinBERT sentiment across major indices.',
    },
  ]

  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-subtext uppercase tracking-wider mb-2.5">
        Explore what's possible
      </p>
      <div className="grid grid-cols-2 gap-2">
        {actions.map((act) => {
          const Icon = act.icon
          return (
            <button
              key={act.id}
              onClick={() => onActionClick && onActionClick(act.query)}
              className="flex items-center gap-2 px-3 py-2.5 rounded-xl border border-border bg-surface hover:bg-white hover:border-border hover:shadow-xs text-xs font-medium text-text transition-base btn-press text-left select-none"
            >
              <Icon size={14} className="text-primary flex-shrink-0" />
              <span className="truncate">{act.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
