import { useState } from 'react'
import { Sparkles, Loader2 } from 'lucide-react'
import useResearchStore from '../../store/researchStore'
import { sendMessage } from '../../api/chat'

export function DiveDeepButton({ title, ticker = 'AAPL' }) {
  const [isProcessing, setIsProcessing] = useState(false)
  const addMessage  = useResearchStore(s => s.addMessage)
  const setLoading  = useResearchStore(s => s.setLoading)
  const sessionId   = useResearchStore(s => s.sessionId)

  const handleDiveDeep = async (e) => {
    e.stopPropagation()
    if (!title || isProcessing) return

    const question = `Summarize this article and its implications for ${ticker}: "${title}"`

    // Add user message to research store
    addMessage('user', question)
    setLoading(true)
    setIsProcessing(true)

    try {
      const data = await sendMessage(question, ticker, sessionId)
      addMessage('assistant', data.answer, data.sources || [])
    } catch (err) {
      console.error('Dive deep chat error:', err)
      addMessage('assistant', `Failed to generate analysis for "${title}". Please try asking in the research panel.`)
    } finally {
      setLoading(false)
      setIsProcessing(false)
    }
  }

  return (
    <button
      onClick={handleDiveDeep}
      disabled={isProcessing}
      className={`
        inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
        border border-border bg-white text-primary hover:bg-surface hover:border-primary/40
        shadow-sm transition-base btn-press select-none
        ${isProcessing ? 'opacity-70 cursor-wait' : 'cursor-pointer'}
      `}
      title="Analyze article in Research AI"
    >
      {isProcessing ? (
        <Loader2 size={13} className="animate-spin text-primary" />
      ) : (
        <Sparkles size={13} className="text-primary fill-primary/20" />
      )}
      <span>{isProcessing ? 'Analyzing...' : 'Dive deeper with AI'}</span>
    </button>
  )
}
