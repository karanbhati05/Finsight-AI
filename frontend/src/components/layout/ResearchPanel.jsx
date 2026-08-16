import { useState, useEffect, useRef } from 'react'
import { Send, Plus, Sparkles, BarChart2, FileText, Search, Edit3, SlidersHorizontal, Mic } from 'lucide-react'
import { sendMessage, getSuggestions } from '../../api/chat'
import { ChatMessageSkeleton } from '../common/Skeleton'
import useResearchStore from '../../store/researchStore'

/* ── Chat Message Bubble ──────────────────────────────────── */
function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-2.5 px-4 py-2 ${isUser ? 'justify-end' : ''}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Sparkles size={14} className="text-primary" />
        </div>
      )}
      <div className={`max-w-[85%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`text-sm leading-relaxed rounded-2xl px-3.5 py-2.5 ${
            isUser
              ? 'bg-primary text-white rounded-br-md'
              : 'bg-surface text-text rounded-bl-md'
          }`}
        >
          {message.content}
        </div>
        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {message.sources.slice(0, 3).map((src, i) => (
              <span key={i} className="text-2xs px-2 py-0.5 bg-surface rounded-full text-subtext">
                {src.source || `Source ${i + 1}`}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Suggested Question Chip ──────────────────────────────── */
function SuggestionChip({ text, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 w-full text-left px-3 py-2.5 rounded-lg hover:bg-surface transition-base group"
    >
      <span className="text-sm text-text leading-snug flex-1">{text}</span>
      <Search size={14} className="text-subtext opacity-0 group-hover:opacity-100 transition-base flex-shrink-0" />
    </button>
  )
}

/* ── Quick Action Button ──────────────────────────────────── */
function QuickAction({ icon: Icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-text hover:bg-surface transition-base btn-press"
    >
      <Icon size={14} className="text-primary" />
      {label}
    </button>
  )
}

/* ── Research Panel ───────────────────────────────────────── */
export function ResearchPanel() {
  const messages    = useResearchStore(s => s.messages)
  const loading     = useResearchStore(s => s.loading)
  const ticker      = useResearchStore(s => s.ticker)
  const sessionId   = useResearchStore(s => s.sessionId)
  const addMessage  = useResearchStore(s => s.addMessage)
  const setLoading  = useResearchStore(s => s.setLoading)

  const [input, setInput]           = useState('')
  const [suggestions, setSuggestions] = useState([])
  const messagesEndRef = useRef(null)

  // Fetch suggestions on mount / ticker change
  useEffect(() => {
    getSuggestions(ticker)
      .then(data => setSuggestions(data.suggestions || []))
      .catch(() => setSuggestions([]))
  }, [ticker])

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text) => {
    const question = text || input
    if (!question.trim()) return

    addMessage('user', question)
    setInput('')
    setLoading(true)

    try {
      const data = await sendMessage(question, ticker, sessionId)
      addMessage('assistant', data.answer, data.sources || [])
    } catch (err) {
      addMessage('assistant', 'Sorry, I encountered an error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border flex-shrink-0">
        <h2 className="text-base font-semibold text-text">Research</h2>
        <div className="flex items-center gap-1">
          <button className="p-1.5 rounded hover:bg-surface transition-base">
            <Edit3 size={16} className="text-subtext" />
          </button>
          <button className="p-1.5 rounded hover:bg-surface transition-base">
            <SlidersHorizontal size={16} className="text-subtext" />
          </button>
        </div>
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto">
        {!hasMessages ? (
          /* Empty state — greeting + suggestions + quick actions */
          <div className="px-4 py-4">
            {/* Greeting */}
            <p className="text-base font-semibold text-text mb-1">
              Hi, ask any financial question
            </p>

            {/* Suggested questions */}
            <div className="mt-4 space-y-0.5">
              {suggestions.map((q, i) => (
                <SuggestionChip
                  key={i}
                  text={q}
                  onClick={() => handleSend(q)}
                />
              ))}
            </div>

            {/* Explore section */}
            <div className="mt-6">
              <p className="text-sm font-medium text-subtext mb-3">Explore what's possible</p>
              <div className="grid grid-cols-2 gap-2">
                <QuickAction icon={Plus} label="Create a portfolio" />
                <QuickAction icon={FileText} label="Create a task" />
                <QuickAction icon={Search} label="Deep Search" />
                <QuickAction icon={BarChart2} label="Analyse" />
              </div>
            </div>
          </div>
        ) : (
          /* Chat messages */
          <div className="py-3">
            {messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {loading && <ChatMessageSkeleton />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-border p-3 flex-shrink-0">
        <div className="flex items-center gap-2 bg-surface rounded-2xl px-3 py-2 border border-transparent focus-within:border-primary focus-within:bg-white transition-base">
          <button className="p-1 rounded hover:bg-white transition-base flex-shrink-0">
            <Plus size={16} className="text-subtext" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            className="flex-1 bg-transparent outline-none text-sm text-text placeholder:text-muted"
          />
          <button className="p-1 rounded hover:bg-white transition-base flex-shrink-0">
            <Mic size={16} className="text-subtext" />
          </button>
          {input.trim() ? (
            <button
              onClick={() => handleSend()}
              className="p-1.5 rounded-full bg-primary text-white hover:bg-primary-hover transition-base btn-press flex-shrink-0"
            >
              <Send size={14} />
            </button>
          ) : (
            <div className="w-8" />
          )}
        </div>
      </div>
    </div>
  )
}
