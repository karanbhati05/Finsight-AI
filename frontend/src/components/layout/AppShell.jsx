import { Sidebar }       from './Sidebar'
import { MainFeed }      from './MainFeed'
import { ResearchPanel } from './ResearchPanel'
import { TopBar }        from './TopBar'

export function AppShell() {
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      {/* Top bar — spans full width */}
      <TopBar />

      {/* Three-column body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — 280px, hidden below lg */}
        <aside className="w-[280px] border-r border-border overflow-y-auto flex-shrink-0 hidden lg:block">
          <Sidebar />
        </aside>

        {/* Main content — flexible center */}
        <main className="flex-1 overflow-y-auto">
          <MainFeed />
        </main>

        {/* Right research panel — 380px, hidden below xl */}
        <aside className="w-[380px] border-l border-border flex flex-col flex-shrink-0 hidden xl:flex animate-slide-in">
          <ResearchPanel />
        </aside>
      </div>
    </div>
  )
}
