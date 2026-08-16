import { useState } from 'react'
import { Edit3, List, Maximize2, Minimize2 } from 'lucide-react'
import { ResearchChat } from './ResearchChat'
import { ChatInput } from './ChatInput'
import { ThreadsAndTasks } from './ThreadsAndTasks'
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
      const data = await sendMessage(queryText, activeTicker, sessionId)
      addMessage('assistant', data.answer, data.sources || [])
    } catch (err) {
      console.error('Chat API Error:', err)
      addMessage(
        'assistant',
        'I encountered an error retrieving or analyzing the documents. Please verify the backend is running and try again.'
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
      {/* ── Research Header (Screenshot 1: Research ✏️ ≡ ⛶) ───── */}
      <div className="h-14 flex items-center justify-between px-5 border-b border-[#e8eaed] flex-shrink-0 bg-white select-none">
        <h2 className="text-[17px] font-medium text-[#202124] tracking-tight">
          Research
        </h2>

        <div className="flex items-center gap-1 text-[#5f6368]">
          <button
            onClick={handleNewThread}
            className="p-1.5 rounded-full hover:bg-[#f1f3f4] hover:text-[#202124] transition-base cursor-pointer"
            title="Start New Thread"
          >
            <Edit3 size={18} />
          </button>
          <button
            onClick={() => setView('threads')}
            className="p-1.5 rounded-full hover:bg-[#f1f3f4] hover:text-[#202124] transition-base cursor-pointer"
            title="Threads and Tasks View"
          >
            <List size={18} />
          </button>
          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-1.5 rounded-full hover:bg-[#f1f3f4] hover:text-[#202124] transition-base cursor-pointer"
              title={isExpanded ? "Collapse Sidebar" : "Expand Fullscreen"}
            >
              {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
            </button>
          )}
        </div>
      </div>

      {/* ── Scrollable Chat Messages & Discovery View ────────── */}
      <ResearchChat
        messages={messages}
        loading={loading}
        activeTicker={activeTicker}
        onSelectQuery={handleSendMessage}
      />

      {/* ── Floating Gemini/Google Style Prompt Box at Bottom ── */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={loading}
        placeholder="Ask anything"
      />
    </div>
  )
}
