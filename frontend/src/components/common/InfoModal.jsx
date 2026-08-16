import { X, HelpCircle, Shield, FileText, AlertCircle, MessageSquare } from 'lucide-react'

export function InfoModal({ type, isOpen, onClose }) {
  if (!isOpen || !type) return null

  const modalContent = {
    help: {
      title: 'Help & Knowledge Center',
      icon: <HelpCircle size={18} className="text-[#1a73e8]" />,
      body: (
        <div className="space-y-3 text-xs text-[#3c4043] leading-relaxed">
          <p className="font-bold text-[#202124]">Quick Terminal Navigation:</p>
          <ul className="list-disc pl-4 space-y-1">
            <li><b>Search Bar:</b> Type any stock ticker or company name (e.g. AAPL, NVDA, ^NSEI).</li>
            <li><b>Market Tabs:</b> Switch between US, Europe, India, FRED Macro Radar, and CoinGecko Crypto.</li>
            <li><b>AI Research Panel:</b> Ask real-time questions grounded in SEC 10-K filings and financial statements.</li>
            <li><b>✨ AI Summary:</b> Click to generate instant Gemini valuation and technical overviews.</li>
          </ul>
        </div>
      ),
    },
    feedback: {
      title: 'Send Feedback to Engineering',
      icon: <MessageSquare size={18} className="text-[#1a73e8]" />,
      body: (
        <div className="space-y-3 text-xs text-[#3c4043]">
          <p>Have an idea or spotted a data bug? We continuously update our financial integrations.</p>
          <textarea
            rows={3}
            placeholder="Type your feedback..."
            className="w-full p-2.5 rounded-xl border border-[#dadce0] outline-none text-xs text-[#202124] resize-none focus:border-[#1a73e8]"
          />
          <button
            onClick={onClose}
            className="w-full py-2 bg-[#1a73e8] hover:bg-[#1557b0] text-white rounded-full font-semibold text-xs transition-base"
          >
            Submit Feedback
          </button>
        </div>
      ),
    },
    privacy: {
      title: 'Institutional Privacy Policy',
      icon: <Shield size={18} className="text-[#0f9d58]" />,
      body: (
        <div className="space-y-2.5 text-xs text-[#3c4043] leading-relaxed">
          <p><b>Data Confidentiality:</b> FinSight AI processes your queries with end-to-end encryption.</p>
          <p><b>API Key Security:</b> Financial API keys (FRED, FMP, Alpha Vantage, CoinGecko) are securely stored in server-side environment variables.</p>
          <p><b>Zero Tracking:</b> We do not sell user search history or personal portfolio metrics to third-party data brokers.</p>
        </div>
      ),
    },
    terms: {
      title: 'Terms of Service',
      icon: <FileText size={18} className="text-[#1a73e8]" />,
      body: (
        <div className="space-y-2.5 text-xs text-[#3c4043] leading-relaxed">
          <p>By using FinSight AI, you agree to access live data feeds for research, analysis, and personal decision support.</p>
          <p>All data feeds are subject to exchange operating hours and API provider rate limits.</p>
        </div>
      ),
    },
    disclaimer: {
      title: 'Regulatory & Financial Disclaimer',
      icon: <AlertCircle size={18} className="text-[#d93025]" />,
      body: (
        <div className="space-y-2.5 text-xs text-[#3c4043] leading-relaxed">
          <p className="font-bold text-[#d93025]">Not Investment Advice:</p>
          <p>The information, AI summaries, and price targets provided on FinSight AI are for informational and educational purposes only.</p>
          <p>FinSight AI is not a registered investment advisor or broker-dealer. Always consult a licensed financial professional before making investment decisions.</p>
        </div>
      ),
    },
  }

  const current = modalContent[type] || modalContent.help

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl border border-[#dadce0] overflow-hidden">
        <div className="px-6 py-4 border-b border-[#e8eaed] flex items-center justify-between bg-[#f8f9fa]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white border border-[#e8eaed] flex items-center justify-center shadow-xs">
              {current.icon}
            </div>
            <h3 className="text-base font-bold text-[#202124]">{current.title}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#5f6368] hover:text-[#202124] hover:bg-[#e8eaed] transition-base cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6">
          {current.body}
        </div>

        <div className="px-6 py-3 border-t border-[#e8eaed] bg-[#f8f9fa] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#1a73e8] hover:bg-[#1557b0] text-white rounded-full text-xs font-semibold transition-base cursor-pointer"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  )
}
