import { useState, useEffect, useRef } from 'react'
import { Sparkles, Plus, CheckSquare, FileText } from 'lucide-react'
import { ChatMessage } from './ChatMessage'
import { SuggestedQueries } from './SuggestedQueries'
import { ResearchMemoModal } from '../analyst/ResearchMemoModal'
import { CreateTaskModal } from './CreateTaskModal'
import { InfoModal } from '../common/InfoModal'
import usePortfolioStore from '../../store/portfolioStore'

export function ResearchChat({
  messages = [],
  loading = false,
  activeTicker = 'AAPL',
  onSelectQuery,
}) {
  const scrollRef = useRef(null)
  const setAddModalOpen = usePortfolioStore(s => s.setAddModalOpen)
  const [isMemoOpen, setIsMemoOpen]       = useState(false)
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false)
  const [activeInfoModal, setActiveInfoModal] = useState(null) // 'help' | 'feedback' | 'privacy' | 'terms' | 'disclaimer' | null

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading])

  const hasMessages = messages.length > 0

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col justify-between select-text">
      {!hasMessages ? (
        /* ── Discovery State (Matches Google Finance / FinSight) ── */
        <div className="p-5 space-y-6">
          {/* Greeting */}
          <h3 className="text-[20px] font-medium text-[#202124] tracking-tight leading-snug">
            Hi Karan, ask any financial question
          </h3>

          {/* 3 Suggested Queries */}
          <SuggestedQueries
            ticker={activeTicker}
            onSelectQuery={onSelectQuery}
          />

          {/* Explore what's possible */}
          <div className="space-y-3 pt-2">
            <h4 className="text-[14px] font-medium text-[#202124]">
              Explore what's possible
            </h4>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setIsMemoOpen(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#e8f0fe] hover:bg-[#d2e3fc] text-[13px] font-semibold text-[#1a73e8] transition-base btn-press cursor-pointer shadow-2xs"
              >
                <Sparkles size={14} />
                AI Summary
              </button>

              <button
                onClick={() => setAddModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#f1f3f4] hover:bg-[#e8eaed] text-[13px] font-medium text-[#202124] transition-base btn-press cursor-pointer shadow-2xs"
              >
                <Plus size={15} />
                Create a portfolio
              </button>

              <button
                onClick={() => setIsTaskModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#f1f3f4] hover:bg-[#e8eaed] text-[13px] font-medium text-[#202124] transition-base btn-press cursor-pointer shadow-2xs"
              >
                <CheckSquare size={14} className="text-[#5f6368]" />
                Create a task
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* ── Conversation Stream ─────────────────────────────── */
        <div className="py-3 space-y-1">
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {loading && (
            <div className="flex gap-2.5 px-4 py-2.5 items-start animate-fade-in">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Sparkles size={14} className="text-primary" />
              </div>
              <div className="bg-white border border-[#e8eaed] rounded-2xl rounded-bl-xs px-4 py-3 shadow-xs">
                <div className="flex items-center gap-1.5 h-4">
                  <span className="w-2 h-2 rounded-full bg-[#1a73e8] animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-2 h-2 rounded-full bg-[#1a73e8] animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-2 h-2 rounded-full bg-[#1a73e8] animate-bounce" />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI Summary Modal */}
      <ResearchMemoModal
        ticker={activeTicker}
        isOpen={isMemoOpen}
        onClose={() => setIsMemoOpen(false)}
      />

      {/* Create Task Modal */}
      <CreateTaskModal
        defaultTicker={activeTicker}
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
      />

      {/* Info Modals (Help, Feedback, Privacy, Terms, Disclaimer) */}
      <InfoModal
        type={activeInfoModal}
        isOpen={Boolean(activeInfoModal)}
        onClose={() => setActiveInfoModal(null)}
      />

      {/* ── Footer Interactive Links ─────────────────────────── */}
      <div className="p-4 pt-6 text-center text-[11px] text-[#5f6368] space-x-3 select-none flex-shrink-0">
        <button onClick={() => setActiveInfoModal('help')} className="hover:underline hover:text-[#202124] cursor-pointer">Help</button>
        <button onClick={() => setActiveInfoModal('feedback')} className="hover:underline hover:text-[#202124] cursor-pointer">Send feedback</button>
        <button onClick={() => setActiveInfoModal('privacy')} className="hover:underline hover:text-[#202124] cursor-pointer">Privacy</button>
        <button onClick={() => setActiveInfoModal('terms')} className="hover:underline hover:text-[#202124] cursor-pointer">Terms</button>
        <button onClick={() => setActiveInfoModal('disclaimer')} className="hover:underline hover:text-[#202124] cursor-pointer">Disclaimer</button>
      </div>
    </div>
  )
}
