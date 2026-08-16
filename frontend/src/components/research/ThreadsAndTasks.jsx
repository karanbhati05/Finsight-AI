import { useState } from 'react'
import { ArrowLeft, Trash2, Maximize2, Edit3, Sparkles, ChevronDown, ChevronUp, MoreVertical } from 'lucide-react'

export function ThreadsAndTasks({ onBack, onSelectThread }) {
  const [tasksCollapsed, setTasksCollapsed] = useState(false)

  const recentThreads = [
    { id: '1', title: 'Market Insights Overview' },
    { id: '2', title: 'Compare the S&P 500 to the Dow Jones' },
    { id: '3', title: 'NIFTY 50 and Tech Sector Correlation' },
    { id: '4', title: 'Apple Earnings and Risk Factors Summary' },
  ]

  return (
    <div className="flex flex-col h-full bg-white select-none animate-slide-in">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-[#e8eaed] flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-1 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] hover:text-[#202124] transition-base"
          >
            <ArrowLeft size={18} />
          </button>
          <h2 className="text-[17px] font-medium text-[#202124]">
            Threads and tasks
          </h2>
        </div>

        <div className="flex items-center gap-1 text-[#5f6368]">
          <button className="p-1.5 rounded-full hover:bg-[#f1f3f4] transition-base">
            <Trash2 size={16} />
          </button>
          <button className="p-1.5 rounded-full hover:bg-[#f1f3f4] transition-base">
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      {/* ── Content ────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* New Thread & New Task buttons */}
        <div className="space-y-1">
          <button
            onClick={onBack}
            className="flex items-center gap-3 w-full p-2.5 rounded-xl hover:bg-[#f1f3f4] text-[#202124] text-[14px] font-medium transition-base text-left"
          >
            <Edit3 size={18} className="text-[#5f6368]" />
            <span>New thread</span>
          </button>

          <button
            onClick={() => onSelectThread && onSelectThread("Create a new automated stock research task.")}
            className="flex items-center gap-3 w-full p-2.5 rounded-xl hover:bg-[#f1f3f4] text-[#202124] text-[14px] font-medium transition-base text-left"
          >
            <Sparkles size={18} className="text-[#5f6368]" />
            <span>New task</span>
          </button>
        </div>

        {/* Tasks Section */}
        <div className="pt-2">
          <div
            onClick={() => setTasksCollapsed(!tasksCollapsed)}
            className="flex items-center justify-between cursor-pointer py-1"
          >
            <h3 className="text-[14px] font-medium text-[#202124]">Tasks</h3>
            <button className="text-[#5f6368]">
              {tasksCollapsed ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>

          {!tasksCollapsed && (
            <div className="mt-2 space-y-2">
              <p className="text-[13px] text-[#5f6368] leading-relaxed">
                Let AI work in the background to complete financial tasks for you
              </p>
              <button className="flex items-center gap-1 text-[13px] text-[#1a73e8] font-medium hover:underline">
                <span>Show templates</span>
                <ChevronDown size={14} />
              </button>
            </div>
          )}
        </div>

        {/* Recent Threads Section */}
        <div className="pt-3">
          <h3 className="text-[14px] font-medium text-[#202124] mb-2">
            Recent threads
          </h3>

          <div className="space-y-0.5">
            {recentThreads.map((thread) => (
              <div
                key={thread.id}
                onClick={() => onSelectThread && onSelectThread(thread.title)}
                className="flex items-center justify-between p-2.5 rounded-xl hover:bg-[#f1f3f4] text-[#202124] text-[13px] cursor-pointer group transition-base"
              >
                <span className="truncate flex-1 pr-2 font-normal">
                  {thread.title}
                </span>
                <button
                  onClick={(e) => e.stopPropagation()}
                  className="p-1 rounded-full text-[#80868b] hover:text-[#202124] opacity-0 group-hover:opacity-100 transition-base"
                >
                  <MoreVertical size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
