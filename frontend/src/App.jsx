import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"             element={<Dashboard />} />
        <Route path="/stock/:symbol" element={<Dashboard />} />
        <Route path="/portfolio"    element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
