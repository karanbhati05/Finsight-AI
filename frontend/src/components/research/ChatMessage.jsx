import { Sparkles, User } from 'lucide-react'
import { SourceCitation } from './SourceCitation'

export function ChatMessage({ message }) {
  if (!message) return null

  const isUser = message.role === 'user'
  const { content, sources } = message

  return (
    <div className={`flex gap-2.5 px-4 py-2.5 transition-base ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
          <Sparkles size={14} className="text-primary" />
        </div>
      )}

      {/* Bubble Container */}
      <div className={`max-w-[88%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`
            text-sm leading-relaxed rounded-2xl px-4 py-3 shadow-xs
            ${isUser
              ? 'bg-primary text-white rounded-br-xs font-normal'
              : 'bg-white text-text border border-border rounded-bl-xs'
            }
          `}
        >
          {/* Multi-paragraph formatting */}
          <div className="space-y-2 whitespace-pre-wrap">
            {content}
          </div>

          {/* Cited sources for Assistant messages */}
          {!isUser && sources && sources.length > 0 && (
            <SourceCitation sources={sources} />
          )}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-surface border border-border flex items-center justify-center flex-shrink-0 mt-0.5 text-subtext">
          <User size={14} />
        </div>
      )}
    </div>
  )
}
