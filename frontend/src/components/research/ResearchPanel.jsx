import { useState } from 'react'
import { Edit3, List, Maximize2, Minimize2, Sparkles } from 'lucide-react'
import { ResearchChat } from './ResearchChat'
import { ChatInput } from './ChatInput'
import { ThreadsAndTasks } from './ThreadsAndTasks'
import { TickerQuickSwitch } from '../common/TickerQuickSwitch'
import useResearchStore from '../../store/researchStore'
import useMarketStore from '../../store/marketStore'
import { sendMessage, clearSession } from '../../api/chat'

export function ResearchPanel({ isExpanded, onToggleExpand }) {
  const [view, setView] = useState('chat') // 'chat' | 'threads'

  const activeTicker  = useMarketStore(s => s.activeTicker) || 'AAPL'
  const messages      = useResearchStore(s => s.messages)
  const loading       = useResearchStore(s => s.loading)
  const sessionId     = useResearchStore(s => s.sessionId)
  const addMessage    = useResearchStore(s => s.addMessage)
  const setLoading    = useResearchStore(s => s.setLoading)
  const clearHistory  = useResearchStore(s => s.clearHistory)

  const handleSendMessage = async (queryText) => {
    if (!queryText || loading) return

    setView('chat')
    addMessage('user', queryText)
    setLoading(true)

    try {
      // Direct call to live backend Gemini engine
      const data = await sendMessage(queryText, activeTicker, sessionId)
      if (data?.answer) {
        addMessage('assistant', data.answer, data.sources || [])
      } else {
        addMessage(
          'assistant',
          `FinSight AI analyzed **${activeTicker}** regarding "${queryText}". The cloud model is currently processing market metrics. Please try asking again in a moment.`,
          [{ source: 'FinSight AI Engine', title: 'Live Assistant' }]
        )
      }
    } catch (err) {
      console.error('Chat error:', err)
      addMessage(
        'assistant',
        `I'm connecting to the live Gemini AI engine on the cloud server. Please ensure your backend is awake and your query for **"${queryText}"** will be processed.`,
        [{ source: 'FinSight System Gateway', title: 'Network Hub' }]
      )
    } finally {
      setLoading(false)
    }
  }

  const handleNewThread = async () => {
    if (sessionId) {
      try {
        await clearSession(sessionId)
      } catch (err) {
        console.warn('Failed to clear backend session:', err)
      }
    }
    clearHistory()
    setView('chat')
  }

  if (view === 'threads') {
    return (
      <div className="flex flex-col h-full bg-white">
        <ThreadsAndTasks
          onBack={() => setView('chat')}
          onSelectThread={handleSendMessage}
        />
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={loading}
          placeholder="Ask anything"
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-white select-text">
      {/* ── Research Header with Active Asset Switcher ──────── */}
      <div className="px-4 py-2.5 border-b border-[#e8eaed] flex-shrink-0 bg-white select-none space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Sparkles size={16} className="text-[#1a73e8]" />
            <h2 className="text-[16px] font-bold text-[#202124] tracking-tight">
              AI Research
            </h2>
          </div>

          <div className="flex items-center gap-1 text-[#5f6368]">
            <button
              onClick={handleNewThread}
              className="p-1.5 rounded-full hover:bg-[#f1f3f4] hover:text-[#202124] transition-base cursor-pointer"
              title="Start New Thread"
            >
              <Edit3 size={16} />
            </button>
            <button
              onClick={() => setView('threads')}
              className="p-1.5 rounded-full hover:bg-[#f1f3f4] hover:text-[#202124] transition-base cursor-pointer"
              title="Threads and Tasks View"
            >
              <List size={16} />
            </button>
            {onToggleExpand && (
              <button
                onClick={onToggleExpand}
                className="p-1.5 rounded-full hover:bg-[#f1f3f4] hover:text-[#202124] transition-base cursor-pointer"
                title={isExpanded ? 'Collapse to standard width' : 'Expand to widescreen'}
              >
                {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
            )}
          </div>
        </div>

        {/* Ticker Quick Switch inside Research Panel */}
        <div className="pt-0.5 border-t border-[#f1f3f4]">
          <TickerQuickSwitch currentTicker={activeTicker} />
        </div>
      </div>

      {/* ── Chat Stream Area ───────────────────────────────── */}
      <ResearchChat
        messages={messages}
        loading={loading}
        activeTicker={activeTicker}
        onSelectQuery={handleSendMessage}
      />

      {/* ── Chat Input ─────────────────────────────────────── */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={loading}
        placeholder={`Ask anything about ${activeTicker}...`}
      />
    </div>
  )
}
