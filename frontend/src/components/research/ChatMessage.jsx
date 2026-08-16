import { useState } from 'react'
import { Sparkles, User, Copy, Check, ExternalLink, ShieldCheck } from 'lucide-react'
import { SourceCitation } from './SourceCitation'

function FormattedContent({ text }) {
  if (!text) return null

  // Split by line breaks
  const lines = text.split('\n')
  const elements = []

  let currentList = []

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="space-y-2 my-2.5 pl-1">
          {currentList.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-[13.5px] leading-relaxed text-[#3c4043]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1a73e8] mt-2 flex-shrink-0" />
              <div className="flex-1">{formatInline(item)}</div>
            </li>
          ))}
        </ul>
      )
      currentList = []
    }
  }

  const formatInline = (str) => {
    // Bold formatting: **text**
    const parts = str.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="font-semibold text-[#202124]">
            {part.slice(2, -2)}
          </strong>
        )
      }
      return part
    })
  }

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i].trim()

    if (!rawLine) {
      flushList()
      continue
    }

    // Header: ### or ## or #
    if (rawLine.startsWith('#')) {
      flushList()
      const title = rawLine.replace(/^#+\s*/, '').replace(/\*\*/g, '')
      elements.push(
        <h4
          key={`h-${i}`}
          className="text-[15px] font-bold text-[#202124] mt-4 mb-2 first:mt-1 pb-1 border-b border-[#f1f3f4] flex items-center gap-2"
        >
          <span>{title}</span>
        </h4>
      )
      continue
    }

    // Bullet points: * or -
    if (rawLine.startsWith('* ') || rawLine.startsWith('- ')) {
      currentList.push(rawLine.substring(2))
      continue
    }

    // Numbered item: 1. or 2.
    if (/^\d+\.\s/.test(rawLine)) {
      flushList()
      elements.push(
        <div key={`num-${i}`} className="flex items-start gap-2.5 my-2 text-[13.5px] leading-relaxed text-[#3c4043]">
          <span className="px-2 py-0.5 rounded-md bg-[#e8f0fe] text-[#1a73e8] font-bold text-xs flex-shrink-0 mt-0.5">
            {rawLine.match(/^\d+/)[0]}
          </span>
          <div className="flex-1 font-medium">{formatInline(rawLine.replace(/^\d+\.\s*/, ''))}</div>
        </div>
      )
      continue
    }

    // Normal paragraph
    flushList()
    elements.push(
      <p key={`p-${i}`} className="text-[13.5px] leading-relaxed text-[#3c4043] my-1.5 font-normal">
        {formatInline(rawLine)}
      </p>
    )
  }

  flushList()
  return <div className="space-y-1">{elements}</div>
}

export function ChatMessage({ message }) {
  const [copied, setCopied] = useState(false)
  if (!message) return null

  const isUser = message.role === 'user'
  const { content, sources } = message

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  return (
    <div className={`flex gap-3 px-4 py-3 transition-base ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant Icon */}
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#1a73e8] to-[#4285f4] flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm text-white">
          <Sparkles size={16} />
        </div>
      )}

      {/* Bubble Container */}
      <div className={`max-w-[90%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`
            text-[13.5px] leading-relaxed rounded-2xl p-4.5 shadow-xs transition-all
            ${isUser
              ? 'bg-[#1a73e8] text-white rounded-br-xs font-medium shadow-sm'
              : 'bg-white text-[#202124] border border-[#e8eaed] rounded-bl-xs hover:border-[#dadce0]'
            }
          `}
        >
          {/* Formatted Content */}
          {isUser ? (
            <div className="whitespace-pre-wrap">{content}</div>
          ) : (
            <div>
              <FormattedContent text={content} />

              {/* Cited sources pills */}
              {sources && sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[#f1f3f4] flex flex-wrap items-center gap-1.5">
                  <span className="text-[11px] font-semibold text-[#5f6368] flex items-center gap-1 mr-1">
                    <ShieldCheck size={13} className="text-[#0f9d58]" />
                    Sources:
                  </span>
                  {sources.map((s, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#f1f3f4] border border-[#e8eaed] text-[11px] font-medium text-[#3c4043]"
                    >
                      {s.source || s.title}
                    </span>
                  ))}
                </div>
              )}

              {/* Copy message button */}
              <div className="mt-3 flex justify-end">
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#5f6368] hover:text-[#1a73e8] transition-base cursor-pointer px-2 py-1 rounded-md hover:bg-[#f1f3f4]"
                  title="Copy analysis to clipboard"
                >
                  {copied ? (
                    <>
                      <Check size={12} className="text-[#0f9d58]" />
                      <span className="text-[#0f9d58]">Copied!</span>
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
        <div className="w-8 h-8 rounded-full bg-[#f1f3f4] border border-[#dadce0] flex items-center justify-center flex-shrink-0 mt-0.5 text-[#5f6368]">
          <User size={15} />
        </div>
      )}
    </div>
  )
}
