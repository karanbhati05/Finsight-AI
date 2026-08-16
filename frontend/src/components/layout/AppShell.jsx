import { useState } from 'react'
import { Sidebar }       from './Sidebar'
import { MainFeed }      from './MainFeed'
import { ResearchPanel } from './ResearchPanel'
import { TopBar }        from './TopBar'
import { AddPortfolioModal } from '../portfolio/AddPortfolioModal'
import { TrendingUp, Newspaper, Sparkles, Briefcase, X } from 'lucide-react'

export function AppShell() {
  const [isResearchDrawerOpen, setIsResearchDrawerOpen] = useState(false)
  const [isResearchExpanded, setIsResearchExpanded]     = useState(false)
  const [mobileTab, setMobileTab] = useState('main') // 'main' | 'portfolio' | 'research'

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      {/* ── Top Bar ─────────────────────────────────────────── */}
      <TopBar
        isResearchOpen={isResearchDrawerOpen}
        onToggleResearch={() => setIsResearchDrawerOpen(!isResearchDrawerOpen)}
      />

      {/* ── Main 3-Column Layout ────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* 1. Left Sidebar (280px, desktop) */}
        <aside className="w-[280px] border-r border-[#e8eaed] overflow-y-auto flex-shrink-0 hidden lg:block bg-white">
          <Sidebar />
        </aside>

        {/* 2. Center Content Feed */}
        <main className={`flex-1 overflow-y-auto ${mobileTab === 'portfolio' ? 'hidden md:block' : mobileTab === 'research' ? 'hidden md:block' : 'block'}`}>
          <MainFeed />
        </main>

        {/* Mobile View: Portfolio Replacement */}
        {mobileTab === 'portfolio' && (
          <div className="flex-1 overflow-y-auto md:hidden p-4">
            <Sidebar />
          </div>
        )}

        {/* Mobile View: Research Replacement */}
        {mobileTab === 'research' && (
          <div className="flex-1 overflow-y-auto md:hidden bg-white">
            <ResearchPanel />
          </div>
        )}

        {/* 3. Right Research Panel (Dynamic width: 380px or 620px expanded) */}
        <aside
          className={`
            border-l border-[#e8eaed] flex flex-col flex-shrink-0 hidden xl:flex transition-all duration-200 bg-white
            ${isResearchExpanded ? 'w-[620px]' : 'w-[380px]'}
          `}
        >
          <ResearchPanel
            isExpanded={isResearchExpanded}
            onToggleExpand={() => setIsResearchExpanded(!isResearchExpanded)}
          />
        </aside>

        {/* Slide-over Drawer for Research on medium screens (md to xl) */}
        {isResearchDrawerOpen && (
          <div className="fixed inset-y-0 right-0 z-40 w-[380px] max-w-full bg-white shadow-2xl border-l border-[#e8eaed] flex flex-col xl:hidden animate-slide-in">
            <div className="flex justify-end p-2 bg-[#f8f9fa] border-b border-[#e8eaed]">
              <button
                onClick={() => setIsResearchDrawerOpen(false)}
                className="p-1 rounded-lg text-[#5f6368] hover:text-[#202124] hover:bg-white cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <ResearchPanel />
            </div>
          </div>
        )}
      </div>

      {/* Global Add Portfolio Modal */}
      <AddPortfolioModal />

      {/* ── Bottom Navigation Bar for Mobile (below md) ─────── */}
      <nav className="md:hidden h-14 border-t border-[#e8eaed] bg-white flex items-center justify-around flex-shrink-0 z-30 select-none">
        <button
          onClick={() => setMobileTab('main')}
          className={`flex flex-col items-center gap-1 text-[11px] font-semibold transition-base ${
            mobileTab === 'main' ? 'text-[#1a73e8]' : 'text-[#5f6368]'
          }`}
        >
          <TrendingUp size={18} />
          <span>Market</span>
        </button>

        <button
          onClick={() => setMobileTab('portfolio')}
          className={`flex flex-col items-center gap-1 text-[11px] font-semibold transition-base ${
            mobileTab === 'portfolio' ? 'text-[#1a73e8]' : 'text-[#5f6368]'
          }`}
        >
          <Briefcase size={18} />
          <span>Portfolio</span>
        </button>

        <button
          onClick={() => setMobileTab('research')}
          className={`flex flex-col items-center gap-1 text-[11px] font-semibold transition-base ${
            mobileTab === 'research' ? 'text-[#1a73e8]' : 'text-[#5f6368]'
          }`}
        >
          <Sparkles size={18} />
          <span>Research AI</span>
        </button>
      </nav>
    </div>
  )
}
