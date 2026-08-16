import { useState } from 'react'
import {
  Sparkles,
  User,
  Copy,
  Check,
  TrendingUp,
  ShieldCheck,
  Volume2,
  VolumeX,
  ExternalLink,
  ChevronRight,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function FormattedAssistantContent({ text, onNavigateSymbol }) {
  if (!text) return null

  const lines = text.split('\n')
  const elements = []
  let currentList = []

  const formatInline = (str) => {
    const parts = str.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const inner = part.slice(2, -2)
        // Highlight numbers, currency, percentages
        const isStat = /[$€₹%0-9]/.test(inner) && inner.length < 25
        return (
          <span
            key={i}
            className={`font-semibold ${isStat ? 'text-[#1a73e8] bg-[#e8f0fe]/60 px-1.5 py-0.5 rounded-md font-mono text-[13px]' : 'text-[#202124]'}`}
          >
            {inner}
          </span>
        )
      }
      return part
    })
  }

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <div key={`list-${elements.length}`} className="grid grid-cols-1 gap-2 my-3">
          {currentList.map((item, idx) => {
            // Split title and content if formatted as `**Title:** Description`
            const match = item.match(/^\*\*(.*?)\*\*:(.*)$/)
            if (match) {
              const [_, title, rest] = match
              return (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[#f8f9fa] border border-[#e8eaed] hover:border-[#dadce0] hover:bg-white transition-all shadow-2xs group"
                >
                  <div className="flex items-center gap-1.5 font-bold text-xs text-[#202124] mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1a73e8] group-hover:scale-125 transition-transform" />
                    <span>{title}</span>
                  </div>
                  <p className="text-xs text-[#3c4043] leading-relaxed pl-3 font-normal">
                    {formatInline(rest.trim())}
                  </p>
                </div>
              )
            }

            return (
              <div
                key={idx}
                className="flex items-start gap-2.5 p-2.5 rounded-xl bg-[#f8f9fa] border border-[#e8eaed] text-xs text-[#3c4043] leading-relaxed"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#1a73e8] mt-1.5 flex-shrink-0" />
                <div className="flex-1">{formatInline(item)}</div>
              </div>
            )
          })}
        </div>
      )
      currentList = []
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i].trim()

    if (!rawLine) {
      flushList()
      continue
    }

    // Title Header (# or ## or ###)
    if (rawLine.startsWith('#')) {
      flushList()
      const title = rawLine.replace(/^#+\s*/, '').replace(/\*\*/g, '')
      elements.push(
        <div key={`h-${i}`} className="mt-3 mb-2 pb-1.5 border-b border-[#e8eaed] flex items-center justify-between">
          <h4 className="text-sm font-bold text-[#202124] flex items-center gap-2">
            <span className="w-2 h-2 rounded-xs bg-[#1a73e8]" />
            <span>{title}</span>
          </h4>
        </div>
      )
      continue
    }

    // Bullet item (* or -)
    if (rawLine.startsWith('* ') || rawLine.startsWith('- ')) {
      currentList.push(rawLine.substring(2))
      continue
    }

    // Numbered step (1. or 2.)
    if (/^\d+\.\s/.test(rawLine)) {
      flushList()
      const num = rawLine.match(/^\d+/)[0]
      const textAfter = rawLine.replace(/^\d+\.\s*/, '')
      elements.push(
        <div
          key={`num-${i}`}
          className="p-3 rounded-xl bg-[#f8f9fa] border border-[#e8eaed] my-2 text-xs leading-relaxed text-[#3c4043]"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="w-5 h-5 rounded-full bg-[#e8f0fe] text-[#1a73e8] font-bold text-[11px] flex items-center justify-center">
              {num}
            </span>
            <span className="font-bold text-[#202124] text-xs">Section {num}</span>
          </div>
          <p className="pl-7">{formatInline(textAfter)}</p>
        </div>
      )
      continue
    }

    // Normal paragraph
    flushList()
    elements.push(
      <p key={`p-${i}`} className="text-xs text-[#3c4043] leading-relaxed my-1.5 font-normal">
        {formatInline(rawLine)}
      </p>
    )
  }

  flushList()
  return <div className="space-y-1">{elements}</div>
}

export function ChatMessage({ message }) {
  const [copied, setCopied] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const navigate = useNavigate()

  if (!message) return null

  const isUser = message.role === 'user'
  const { content, sources } = message

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  const handleSpeak = () => {
    if ('speechSynthesis' in window) {
      if (isSpeaking) {
        window.speechSynthesis.cancel()
        setIsSpeaking(false)
      } else {
        const utterance = new SpeechSynthesisUtterance(content.replace(/[*#]/g, ''))
        utterance.onend = () => setIsSpeaking(false)
        utterance.onerror = () => setIsSpeaking(false)
        window.speechSynthesis.speak(utterance)
        setIsSpeaking(true)
      }
    }
  }

  return (
    <div className={`flex gap-2.5 px-4 py-3 transition-base ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant Icon */}
      {!isUser && (
        <div className="w-8 h-8 rounded-2xl bg-gradient-to-tr from-[#1a73e8] to-[#4285f4] flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm text-white">
          <Sparkles size={15} />
        </div>
      )}

      {/* Bubble Container */}
      <div className={`max-w-[92%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`
            rounded-2xl transition-all
            ${isUser
              ? 'bg-[#1a73e8] text-white px-4 py-2.5 text-xs font-medium rounded-br-xs shadow-xs max-w-sm'
              : 'bg-white text-[#202124] border border-[#e8eaed] p-4 rounded-bl-xs shadow-xs'
            }
          `}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap leading-relaxed">{content}</div>
          ) : (
            <div>
              <FormattedAssistantContent text={content} />

              {/* Source Verification Badge */}
              {sources && sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[#f1f3f4] flex flex-wrap items-center gap-1.5">
                  <span className="text-[11px] font-semibold text-[#5f6368] flex items-center gap-1 mr-1">
                    <ShieldCheck size={13} className="text-[#0f9d58]" />
                    Sources:
                  </span>
                  {sources.map((s, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#f8f9fa] border border-[#e8eaed] text-[11px] font-medium text-[#3c4043]"
                    >
                      {s.source || s.title}
                    </span>
                  ))}
                </div>
              )}

              {/* Action Toolbar (Copy, Read Aloud TTS) */}
              <div className="mt-3 pt-2 flex items-center justify-between border-t border-[#f8f9fa] text-2xs text-[#5f6368]">
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSpeak}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-md hover:bg-[#f1f3f4] text-[#5f6368] hover:text-[#202124] transition-base cursor-pointer"
                    title={isSpeaking ? 'Stop reading' : 'Read aloud (TTS)'}
                  >
                    {isSpeaking ? <VolumeX size={12} className="text-[#d93025]" /> : <Volume2 size={12} />}
                    <span>{isSpeaking ? 'Stop' : 'Listen'}</span>
                  </button>
                </div>

                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md hover:bg-[#f1f3f4] text-[#5f6368] hover:text-[#1a73e8] transition-base cursor-pointer"
                  title="Copy analysis to clipboard"
                >
                  {copied ? (
                    <>
                      <Check size={12} className="text-[#0f9d58]" />
                      <span className="text-[#0f9d58] font-bold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-[#f1f3f4] border border-[#dadce0] flex items-center justify-center flex-shrink-0 mt-0.5 text-[#5f6368]">
          <User size={14} />
        </div>
      )}
    </div>
  )
}
