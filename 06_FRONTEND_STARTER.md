# FinSight V2 — Frontend Starter Code

Complete starter files for the React frontend.
Build AFTER the backend is running.

---

## package.json

```json
{
  "name": "finsight-v2",
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev":     "vite",
    "build":   "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react":            "^18.3.1",
    "react-dom":        "^18.3.1",
    "react-router-dom": "^6.23.1",
    "axios":            "^1.7.2",
    "zustand":          "^4.5.2",
    "recharts":         "^2.12.7",
    "lucide-react":     "^0.383.0"
  },
  "devDependencies": {
    "@types/react":          "^18.3.3",
    "@vitejs/plugin-react":  "^4.3.0",
    "autoprefixer":          "^10.4.19",
    "postcss":               "^8.4.38",
    "tailwindcss":           "^3.4.4",
    "vite":                  "^5.2.13"
  }
}
```

---

## vite.config.js

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      }
    }
  }
})
```

---

## tailwind.config.js

```javascript
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        gain:    '#0f9d58',
        loss:    '#d93025',
        primary: '#1a73e8',
        surface: '#f8f9fa',
        border:  '#e8eaed',
        text:    '#202124',
        subtext: '#5f6368',
        muted:   '#80868b',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

---

## src/index.css

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', sans-serif;
  background: #ffffff;
  color: #202124;
  overflow: hidden;
}

/* Scrollbar styling */
::-webkit-scrollbar       { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e8eaed; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #c1c1c1; }

/* Transitions */
.transition-base { transition: all 0.15s ease; }
```

---

## src/api/client.js

```javascript
import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  res => res.data,
  err => {
    console.error('API Error:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default client
```

---

## src/api/market.js

```javascript
import client from './client'

export const getIndices = (region = 'india') =>
  client.get(`/market/indices?region=${region}`)

export const getSectors = (region = 'india') =>
  client.get(`/market/sectors?region=${region}`)

export const searchStocks = (query) =>
  client.get(`/market/search?q=${encodeURIComponent(query)}`)
```

---

## src/api/chat.js

```javascript
import client from './client'

export const sendMessage = (question, ticker, sessionId) =>
  client.post('/chat', { question, ticker, session_id: sessionId })

export const getSuggestions = (ticker) =>
  client.get(`/chat/suggestions/${ticker}`)

export const clearSession = (sessionId) =>
  client.delete(`/chat/${sessionId}`)
```

---

## src/store/marketStore.js

```javascript
import { create } from 'zustand'

const useMarketStore = create((set) => ({
  // State
  activeRegion:   'india',
  activeTicker:   'AAPL',
  indices:        [],
  sectors:        [],
  indicesLoading: false,
  sectorsLoading: false,

  // Actions
  setActiveRegion: (region) => set({ activeRegion: region }),
  setActiveTicker: (ticker) => set({ activeTicker: ticker }),
  setIndices:      (indices) => set({ indices, indicesLoading: false }),
  setSectors:      (sectors) => set({ sectors, sectorsLoading: false }),
  setIndicesLoading: () => set({ indicesLoading: true }),
  setSectorsLoading: () => set({ sectorsLoading: true }),
}))

export default useMarketStore
```

---

## src/store/researchStore.js

```javascript
import { create } from 'zustand'
import { v4 as uuidv4 } from 'uuid'

const useResearchStore = create((set, get) => ({
  // State
  messages:  [],
  sessionId: uuidv4(),
  loading:   false,
  ticker:    'AAPL',

  // Actions
  addMessage: (role, content, sources = []) =>
    set(state => ({
      messages: [...state.messages, { role, content, sources, id: uuidv4() }]
    })),

  setLoading: (loading) => set({ loading }),
  setTicker:  (ticker)  => set({ ticker }),

  clearHistory: () => set({
    messages:  [],
    sessionId: uuidv4(),
  }),
}))

export default useResearchStore
```

---

## src/hooks/useMarketData.js

```javascript
import { useEffect } from 'react'
import { getIndices, getSectors } from '../api/market'
import useMarketStore from '../store/marketStore'

export function useMarketData() {
  const {
    activeRegion,
    setIndices, setSectors,
    setIndicesLoading, setSectorsLoading,
  } = useMarketStore()

  useEffect(() => {
    const fetchData = async () => {
      setIndicesLoading()
      setSectorsLoading()

      try {
        const [indicesData, sectorsData] = await Promise.all([
          getIndices(activeRegion),
          getSectors(activeRegion),
        ])
        setIndices(indicesData.indices || [])
        setSectors(sectorsData.sectors || [])
      } catch (err) {
        console.error('Market data fetch failed:', err)
        setIndices([])
        setSectors([])
      }
    }

    fetchData()

    // Refresh every 60 seconds
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [activeRegion])
}
```

---

## src/hooks/useWebSocket.js

```javascript
import { useEffect, useRef } from 'react'

export function useWebSocket(tickers, onPriceUpdate) {
  const wsRef = useRef(null)

  useEffect(() => {
    if (!tickers || tickers.length === 0) return

    const ws = new WebSocket('ws://localhost:8000/ws/prices')
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: 'subscribe', tickers }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'price_update') {
        onPriceUpdate(data.prices)
      }
    }

    ws.onerror = (err) => console.error('WebSocket error:', err)

    ws.onclose = () => {
      // Reconnect after 5 seconds
      setTimeout(() => {
        if (wsRef.current === ws) {
          wsRef.current = null
        }
      }, 5000)
    }

    return () => ws.close()
  }, [tickers?.join(',')])
}
```

---

## src/components/common/Skeleton.jsx

```jsx
export function Skeleton({ width = '100%', height = 16, className = '' }) {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      style={{ width, height }}
    />
  )
}

export function IndexCardSkeleton() {
  return (
    <div className="border border-border rounded-lg p-4 space-y-2">
      <Skeleton height={14} width="60%" />
      <Skeleton height={22} width="80%" />
      <Skeleton height={12} width="50%" />
      <Skeleton height={40} />
    </div>
  )
}

export function NewsCardSkeleton() {
  return (
    <div className="py-4 border-b border-border space-y-2">
      <Skeleton height={16} width="90%" />
      <Skeleton height={16} width="70%" />
      <Skeleton height={12} width="40%" />
    </div>
  )
}

export function SectorRowSkeleton() {
  return (
    <div className="flex items-center px-4 py-2 gap-3">
      <div className="flex-1 space-y-1">
        <Skeleton height={13} width="70%" />
        <Skeleton height={11} width="40%" />
      </div>
      <Skeleton width={80} height={24} />
      <div className="text-right space-y-1">
        <Skeleton height={13} width={60} />
        <Skeleton height={11} width={50} />
      </div>
    </div>
  )
}
```

---

## src/components/common/PriceChange.jsx

```jsx
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'

export function PriceChange({ change, changePct, showIcon = true, size = 'base' }) {
  const isUp      = change > 0
  const isDown    = change < 0
  const color     = isUp ? 'text-gain' : isDown ? 'text-loss' : 'text-subtext'
  const sizeClass = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm'

  return (
    <span className={`inline-flex items-center gap-0.5 font-medium ${color} ${sizeClass}`}>
      {showIcon && (
        isUp   ? <ArrowUpRight   size={14} /> :
        isDown ? <ArrowDownRight size={14} /> :
                 <Minus          size={14} />
      )}
      {isUp ? '+' : ''}{change?.toFixed(2)} ({isUp ? '+' : ''}{changePct?.toFixed(2)}%)
    </span>
  )
}
```

---

## src/components/market/SparklineChart.jsx

```jsx
import { AreaChart, Area, ResponsiveContainer } from 'recharts'

export function SparklineChart({ data = [], width = 80, height = 40 }) {
  if (!data || data.length === 0) return (
    <div style={{ width, height }} className="bg-gray-100 rounded" />
  )

  const isPositive = data[data.length - 1] >= data[0]
  const chartData  = data.map((value, i) => ({ value, i }))

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <Area
            type="monotone"
            dataKey="value"
            stroke={isPositive ? '#0f9d58' : '#d93025'}
            strokeWidth={1.5}
            fill={isPositive ? '#e6f4ea' : '#fce8e6'}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
```

---

## src/components/news/SentimentBadge.jsx

```jsx
const BADGE_STYLES = {
  positive: 'bg-green-50 text-green-800 border border-green-200',
  negative: 'bg-red-50  text-red-800  border border-red-200',
  neutral:  'bg-gray-50 text-gray-600 border border-gray-200',
}

export function SentimentBadge({ label, score }) {
  const style = BADGE_STYLES[label] || BADGE_STYLES.neutral

  return (
    <span className={`
      inline-flex items-center gap-1 px-2 py-0.5
      rounded-full text-xs font-medium uppercase tracking-wide
      ${style}
    `}>
      {label}
      {score !== undefined && (
        <span className="font-normal opacity-75">
          {score > 0 ? '+' : ''}{score.toFixed(2)}
        </span>
      )}
    </span>
  )
}
```

---

## src/components/layout/AppShell.jsx

```jsx
import { Sidebar }       from './Sidebar'
import { MainFeed }      from './MainFeed'
import { ResearchPanel } from './ResearchPanel'
import { TopBar }        from './TopBar'

export function AppShell() {
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      {/* Top bar */}
      <TopBar />

      {/* Three-column body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar */}
        <aside className="w-[280px] border-r border-border overflow-y-auto flex-shrink-0 hidden lg:block">
          <Sidebar />
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <MainFeed />
        </main>

        {/* Right research panel */}
        <aside className="w-[380px] border-l border-border flex flex-col flex-shrink-0 hidden xl:flex">
          <ResearchPanel />
        </aside>
      </div>
    </div>
  )
}
```

---

## src/App.jsx

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Dashboard }    from './pages/Dashboard'
import { StockDetail }  from './pages/StockDetail'
import { Portfolio }    from './pages/Portfolio'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"          element={<Dashboard />} />
        <Route path="/stock/:symbol" element={<StockDetail />} />
        <Route path="/portfolio" element={<Portfolio />} />
      </Routes>
    </BrowserRouter>
  )
}
```

---

## src/main.jsx

```jsx
import React    from 'react'
import ReactDOM from 'react-dom/client'
import App      from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

---

## Run Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

