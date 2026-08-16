import { useState, useRef, useEffect } from 'react'
import {
  Mic,
  MicOff,
  Plus,
  ArrowUp,
  Loader2,
  FileText,
  Landmark,
  Activity,
  Image as ImageIcon,
  Upload,
  X,
  FileSpreadsheet,
} from 'lucide-react'
import { uploadAttachment } from '../../api/chat'

export function ChatInput({ onSendMessage, disabled = false, placeholder = 'Ask anything' }) {
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [showAttachMenu, setShowAttachMenu] = useState(false)
  const [attachments, setAttachments] = useState([])
  const [uploading, setUploading] = useState(false)

  const inputRef      = useRef(null)
  const recognitionRef = useRef(null)
  const attachRef     = useRef(null)
  const fileInputRef  = useRef(null)
  const imageInputRef = useRef(null)

  // Voice speech recognition setup
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = 'en-US'

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        if (transcript) {
          setInput(prev => (prev ? `${prev} ${transcript}` : transcript))
        }
        setIsListening(false)
      }

      recognition.onerror = () => setIsListening(false)
      recognition.onend   = () => setIsListening(false)

      recognitionRef.current = recognition
    }
  }, [])

  // Close attach menu on outside click
  useEffect(() => {
    const handleDocClick = (e) => {
      if (attachRef.current && !attachRef.current.contains(e.target)) {
        setShowAttachMenu(false)
      }
    }
    document.addEventListener('mousedown', handleDocClick)
    return () => document.removeEventListener('mousedown', handleDocClick)
  }, [])

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.')
      return
    }

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      try {
        recognitionRef.current.start()
        setIsListening(true)
      } catch (err) {
        console.error('Speech recognition error:', err)
      }
    }
  }

  const handleFileUpload = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    setShowAttachMenu(false)

    for (const file of files) {
      try {
        const res = await uploadAttachment(file)
        setAttachments(prev => [
          ...prev,
          {
            name: file.name,
            size: `${(file.size / 1024).toFixed(0)} KB`,
            type: file.type.includes('image') ? 'image' : 'doc',
            text: res.data?.extracted_text || `[Attached: ${file.name}]`,
          },
        ])
      } catch (err) {
        console.warn('Upload fallback applied:', err)
        setAttachments(prev => [
          ...prev,
          {
            name: file.name,
            size: `${(file.size / 1024).toFixed(0)} KB`,
            type: file.type.includes('image') ? 'image' : 'doc',
            text: `[Attached File: ${file.name}]`,
          },
        ])
      }
    }

    setUploading(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (imageInputRef.current) imageInputRef.current.value = ''
  }

  const handleRemoveAttachment = (idx) => {
    setAttachments(prev => prev.filter((_, i) => i !== idx))
  }

  const handleAttachChip = (chipText) => {
    setInput(prev => (prev ? `${prev} ${chipText}` : chipText))
    setShowAttachMenu(false)
    if (inputRef.current) inputRef.current.focus()
  }

  const handleSubmit = (e) => {
    e?.preventDefault()
    if ((!input.trim() && attachments.length === 0) || disabled) return

    let finalPrompt = input.trim()
    if (attachments.length > 0) {
      const attachNotes = attachments.map(a => `${a.text}`).join('\n')
      finalPrompt = `${finalPrompt}\n\n[Context Attachments]:\n${attachNotes}`
    }

    onSendMessage(finalPrompt)
    setInput('')
    setAttachments([])
    setShowAttachMenu(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const hasText = input.trim().length > 0 || attachments.length > 0

  return (
    <div className="p-4 bg-white flex-shrink-0 relative select-none">
      {/* Hidden File Inputs */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        accept=".pdf,.doc,.docx,.txt,.csv"
        multiple
        className="hidden"
      />
      <input
        type="file"
        ref={imageInputRef}
        onChange={handleFileUpload}
        accept="image/png,image/jpeg,image/webp,image/jpg"
        multiple
        className="hidden"
      />

      {/* ── Attach Financial Context Menu ────────────────────── */}
      {showAttachMenu && (
        <div
          ref={attachRef}
          className="absolute bottom-28 left-6 bg-white border border-[#e8eaed] rounded-2xl shadow-xl p-3 z-50 animate-fade-in w-72 space-y-2 text-xs text-[#202124]"
        >
          <div className="flex items-center justify-between font-bold pb-1.5 border-b border-[#f1f3f4]">
            <span>Attach Financial Media & Context</span>
            <button onClick={() => setShowAttachMenu(false)} className="text-[#5f6368] hover:text-[#202124] cursor-pointer">
              <X size={14} />
            </button>
          </div>

          <div className="space-y-1">
            {/* 1. Upload PDF / Document */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full p-2 rounded-xl hover:bg-[#f8f9fa] flex items-center gap-2 text-left cursor-pointer transition-base"
            >
              <Upload size={14} className="text-[#1a73e8]" />
              <div>
                <span className="font-bold">Upload PDF / Document</span>
                <p className="text-[10px] text-[#5f6368]">10-K, 10-Q, annual reports (.pdf, .docx, .txt)</p>
              </div>
            </button>

            {/* 2. Upload Chart / Screenshot Image */}
            <button
              type="button"
              onClick={() => imageInputRef.current?.click()}
              className="w-full p-2 rounded-xl hover:bg-[#f8f9fa] flex items-center gap-2 text-left cursor-pointer transition-base"
            >
              <ImageIcon size={14} className="text-[#0f9d58]" />
              <div>
                <span className="font-bold">Upload Chart / Image</span>
                <p className="text-[10px] text-[#5f6368]">Technical charts, balance sheet slides (.png, .jpg)</p>
              </div>
            </button>

            <div className="border-t border-[#f1f3f4] my-1" />

            {/* 3. Pre-connected data contexts */}
            <button
              type="button"
              onClick={() => handleAttachChip('Analyze SEC 10-K Risk Factors & Disclosures')}
              className="w-full p-1.5 px-2 rounded-lg hover:bg-[#f8f9fa] flex items-center gap-2 text-left cursor-pointer transition-base text-[11px]"
            >
              <FileText size={13} className="text-[#1a73e8]" />
              <span>Attach SEC 10-K Filings</span>
            </button>

            <button
              type="button"
              onClick={() => handleAttachChip('Compare Federal Reserve (FRED) 10-Yr Yield & Fed Funds Rate')}
              className="w-full p-1.5 px-2 rounded-lg hover:bg-[#f8f9fa] flex items-center gap-2 text-left cursor-pointer transition-base text-[11px]"
            >
              <Landmark size={13} className="text-[#0f9d58]" />
              <span>Attach FRED Macro Rates</span>
            </button>

            <button
              type="button"
              onClick={() => handleAttachChip('Review FMP 5-Year Income Statement Margins')}
              className="w-full p-1.5 px-2 rounded-lg hover:bg-[#f8f9fa] flex items-center gap-2 text-left cursor-pointer transition-base text-[11px]"
            >
              <Activity size={13} className="text-[#f29900]" />
              <span>Attach FMP Financials</span>
            </button>
          </div>
        </div>
      )}

      {/* ── Chat Prompt Form Container ────────────────────────── */}
      <form
        onSubmit={handleSubmit}
        className="bg-[#f0f4f9] rounded-[24px] p-3.5 flex flex-col justify-between min-h-[96px] border border-transparent focus-within:border-[#dadce0] focus-within:bg-[#ffffff] focus-within:shadow-[0_1px_6px_rgba(32,33,36,0.18)] transition-all"
      >
        {/* Uploading progress indicator */}
        {uploading && (
          <div className="flex items-center gap-1.5 pb-2 text-xs font-semibold text-[#1a73e8]">
            <Loader2 size={13} className="animate-spin" />
            <span>Processing document for Gemini analysis...</span>
          </div>
        )}

        {/* Attached File Preview Chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pb-2">
            {attachments.map((att, idx) => (
              <div
                key={idx}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#e8f0fe] border border-[#d2e3fc] text-2xs font-semibold text-[#1a73e8]"
              >
                {att.type === 'image' ? <ImageIcon size={12} /> : <FileText size={12} />}
                <span className="max-w-[160px] truncate">{att.name} ({att.size})</span>
                <button
                  type="button"
                  onClick={() => handleRemoveAttachment(idx)}
                  className="p-0.5 hover:bg-black/10 rounded-full cursor-pointer ml-0.5"
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Top line: Textarea + Mic */}
        <div className="flex items-start gap-2 select-text">
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={isListening ? 'Listening... speak now' : placeholder}
            className="flex-1 bg-transparent resize-none outline-none text-[14px] text-[#202124] placeholder:text-[#5f6368] leading-relaxed max-h-24"
          />
          <button
            type="button"
            onClick={toggleListening}
            className={`p-1.5 rounded-full transition-base flex-shrink-0 cursor-pointer ${
              isListening
                ? 'bg-[#d93025] text-white animate-pulse'
                : 'text-[#5f6368] hover:text-[#202124] hover:bg-black/5'
            }`}
            title={isListening ? 'Stop recording' : 'Voice input (Speech-to-Text)'}
          >
            {isListening ? <MicOff size={16} /> : <Mic size={18} />}
          </button>
        </div>

        {/* Bottom line: + and Submit arrow */}
        <div className="flex items-center justify-between mt-2 pt-1 select-none">
          <button
            type="button"
            onClick={() => setShowAttachMenu(!showAttachMenu)}
            className={`p-1.5 rounded-full transition-base cursor-pointer ${
              showAttachMenu ? 'bg-[#e8f0fe] text-[#1a73e8]' : 'text-[#5f6368] hover:text-[#202124] hover:bg-black/5'
            }`}
            title="Upload PDFs, Docs, Images or attach live financial context"
          >
            <Plus size={18} />
          </button>

          <button
            type="submit"
            disabled={!hasText || disabled}
            className={`
              w-8 h-8 rounded-full flex items-center justify-center transition-all btn-press
              ${hasText && !disabled
                ? 'bg-[#1a73e8] text-white hover:bg-[#1557b0] shadow-sm cursor-pointer'
                : 'bg-[#dadce0] text-[#5f6368] cursor-not-allowed opacity-70'
              }
            `}
            title="Send query"
          >
            {disabled ? (
              <Loader2 size={16} className="animate-spin text-white" />
            ) : (
              <ArrowUp size={18} strokeWidth={2.5} />
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
