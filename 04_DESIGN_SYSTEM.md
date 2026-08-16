# FinSight V2 — Design System

Pixel-perfect specification for every visual element.
Follow this exactly — no deviations.

---

## Colors

```css
/* Primary */
--color-primary:     #1a73e8;   /* Google blue — links, active states */
--color-primary-hover:#1557b0;  /* Darker blue on hover */

/* Financial */
--color-gain:        #0f9d58;   /* Green — positive price change */
--color-gain-bg:     #e6f4ea;   /* Light green background */
--color-loss:        #d93025;   /* Red — negative price change */
--color-loss-bg:     #fce8e6;   /* Light red background */
--color-neutral:     #5f6368;   /* Gray — no change */

/* Backgrounds */
--color-bg:          #ffffff;   /* Page background */
--color-surface:     #f8f9fa;   /* Card background */
--color-surface-hover:#f1f3f4;  /* Card hover state */

/* Borders */
--color-border:      #e8eaed;   /* Default border */
--color-border-focus:#1a73e8;   /* Focused input border */

/* Text */
--color-text:        #202124;   /* Primary text */
--color-text-sub:    #5f6368;   /* Secondary text */
--color-text-muted:  #80868b;   /* Muted/placeholder text */

/* Sentiment badges */
--color-positive-text:#137333;
--color-positive-bg:  #e6f4ea;
--color-negative-text:#c5221f;
--color-negative-bg:  #fce8e6;
--color-neutral-text: #5f6368;
--color-neutral-bg:   #f1f3f4;
```

---

## Typography

```css
/* Import in index.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body { font-family: 'Inter', sans-serif; }

/* Scale */
--text-xs:   11px;  /* Labels, badges */
--text-sm:   12px;  /* Captions, metadata */
--text-base: 14px;  /* Body text */
--text-md:   16px;  /* Subheadings */
--text-lg:   20px;  /* Section titles */
--text-xl:   24px;  /* Index values */
--text-2xl:  28px;  /* Hero numbers */
```

---

## Layout

```css
/* Three-column grid */
.app-shell {
  display: grid;
  grid-template-columns: 280px 1fr 380px;
  grid-template-rows: 64px 1fr;
  height: 100vh;
  overflow: hidden;
}

/* Breakpoints */
/* Mobile  < 768px  → single column, bottom tabs */
/* Tablet  768-1024 → sidebar hidden, no research panel */
/* Desktop > 1024px → full three-column */

/* Sidebar */
.sidebar {
  width: 280px;
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
  padding: 8px 0;
}

/* Main feed */
.main-feed {
  overflow-y: auto;
  padding: 0 24px;
}

/* Research panel */
.research-panel {
  width: 380px;
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}
```

---

## Components

### Index Card
```
┌─────────────────────────────────┐
│ NIFTY 50                        │
│ 24,366.00                       │  ← 20px bold #202124
│ -29.85 (-0.12%) ▼               │  ← 13px #d93025
│ ▁▂▃▂▁▂▃▄▃▂  (sparkline 40px)   │  ← red filled area
└─────────────────────────────────┘
Width: flex (4 fit in row)
Padding: 16px
Border: 1px solid #e8eaed
Border-radius: 8px
Hover: background #f8f9fa, cursor pointer
```

### Sector Row
```
NIFTY_AUTO    ▁▂▃▂▁   29,207.90   -0.63% ▼
Auto

Left: name (14px bold) + label (11px #5f6368)
Center: sparkline 80px wide, 24px tall
Right: value + colored change
Padding: 8px 16px
Hover: background #f8f9fa
```

### Sentiment Badge
```
┌──────────┐   ┌──────────┐   ┌─────────┐
│ POSITIVE │   │ NEGATIVE │   │ NEUTRAL │
└──────────┘   └──────────┘   └─────────┘
  #137333 on     #c5221f on     #5f6368 on
  #e6f4ea        #fce8e6        #f1f3f4

Border-radius: 12px
Padding: 2px 8px
Font-size: 11px
Font-weight: 500
Text-transform: uppercase
```

### News Card
```
┌──────────────────────────────────────────────────┐
│ Apple reports record quarterly revenue beating   │
│ analyst estimates by significant margin          │
│                                                  │
│ Reuters · Bloomberg · 3 sites  •  2h ago        │
│ ──────────────────────────────────────────────── │
│ [Article body expanded on click]                 │
│                                                  │
│ ✨ Dive deeper with AI    [POSITIVE] +0.847      │
└──────────────────────────────────────────────────┘
Border-bottom: 1px solid #e8eaed
Padding: 16px 0
No border-radius (full width items)
```

### Research Panel
```
┌─────────────────────────────────────────┐
│ Research                           ✏️ ≡ │  ← header 56px
├─────────────────────────────────────────┤
│ 🔍 Why are US retail sales impacting...  │  ← suggested Q
│ 🔍 What is driving Brent crude rise?     │  ← suggested Q
├─────────────────────────────────────────┤
│ Explore what's possible                  │
│ [+ Create portfolio]  [⚙ Create task]   │
│ [🔍 Deep Search]      [📈 Analyse]      │
├─────────────────────────────────────────┤
│                                          │
│  [chat messages scroll here]             │
│                                          │
├─────────────────────────────────────────┤
│ 🎤  Ask anything...              [send] │  ← input 56px
└─────────────────────────────────────────┘
```

### Prediction Card (UP)
```
┌─────────────────────────────────────────┐
│              ↑                           │
│             UP                           │  ← #0f9d58
│      67.3% probability                   │
│         High Confidence                  │
│ ─────────────────────────────────────── │
│ Date: 2026-05-13                         │
│ RSI: 58.3  Sentiment: +0.42             │
└─────────────────────────────────────────┘
Border: 2px solid #0f9d58
Border-radius: 12px
Arrow: 48px, bold
```

---

## Sparkline Specification

```jsx
// SparklineChart.jsx — exact implementation
// Use Recharts AreaChart

<AreaChart width={80} height={40} data={data}>
  <Area
    type="monotone"
    dataKey="value"
    stroke={isPositive ? "#0f9d58" : "#d93025"}
    fill={isPositive ? "#e6f4ea" : "#fce8e6"}
    strokeWidth={1.5}
    dot={false}
  />
</AreaChart>

// No axes, no grid, no tooltips
// Container: overflow hidden
// isPositive = last value > first value
```

---

## Loading Skeletons

```jsx
// Skeleton.jsx — pulse animation
<div className="animate-pulse bg-gray-200 rounded" 
     style={{width, height}} />

// Index card skeleton: 4 blocks, each 120px x 80px
// News skeleton: 3 items, title 200px h-4, meta 120px h-3
// Sector skeleton: 5 rows, full width h-10
```

---

## Animations

```css
/* All transitions */
transition: all 0.15s ease;

/* Card hover */
.card:hover { background: #f8f9fa; }

/* Button press */
.btn:active { transform: scale(0.98); }

/* Panel slide in */
.research-panel { 
  animation: slideIn 0.2s ease;
}
@keyframes slideIn {
  from { transform: translateX(20px); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

/* Skeleton pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.5; }
}
```

---

## Icons (Lucide React)
```jsx
import {
  Search, Mic, Settings, Bell, ChevronDown, ChevronUp,
  Plus, Trash2, TrendingUp, TrendingDown, Minus,
  FileText, Zap, BarChart2, List, Star,
  ArrowUpRight, ArrowDownRight, Send, Sparkles,
  RefreshCw, ExternalLink, AlertCircle
} from 'lucide-react'
```

---

## Market Tabs

```jsx
const MARKET_TABS = [
  { id: "us",           label: "US" },
  { id: "europe",       label: "Europe" },
  { id: "india",        label: "India" },
  { id: "latin_america",label: "Latin America" },
  { id: "currencies",   label: "Currencies" },
  { id: "crypto",       label: "Crypto" },
  { id: "futures",      label: "Futures" },
]

// Active tab: border-bottom 2px solid #1a73e8, color #1a73e8
// Inactive: color #5f6368, hover color #202124
```

---

## Indian Market Indices to Show

```javascript
const INDIA_INDICES = [
  { symbol: "^NSEI",    name: "NIFTY 50" },
  { symbol: "^BSESN",   name: "SENSEX" },
  { symbol: "^NSEBANK", name: "Nifty Bank" },
  { symbol: "^CNXIT",   name: "Nifty IT" },
]

const INDIA_SECTORS = [
  { symbol: "NIFTY_AUTO.NS",    name: "NIFTY_AUTO",    label: "Auto" },
  { symbol: "NIFTY_ENERGY.NS",  name: "NIFTY_ENERGY",  label: "Energy & Utilities" },
  { symbol: "NIFTY_FIN_SERV.NS",name: "NIFTY_FIN_SERV",label: "Financials" },
  { symbol: "NIFTY_FMCG.NS",    name: "NIFTY_FMCG",    label: "Consumer Staples" },
  { symbol: "NIFTY_INFRA.NS",   name: "NIFTY_INFRA",   label: "Industrials" },
  { symbol: "NIFTY_IT.NS",      name: "NIFTY_IT",      label: "Technology" },
  { symbol: "NIFTY_METAL.NS",   name: "NIFTY_METAL",   label: "Materials" },
  { symbol: "NIFTY_PHARMA.NS",  name: "NIFTY_PHARMA",  label: "Healthcare" },
]
```

