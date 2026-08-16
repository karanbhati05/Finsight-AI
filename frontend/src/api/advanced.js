import client from './client'

/**
 * 📊 Financial Modeling Prep (FMP) APIs
 */
export async function getIncomeStatement(ticker, limit = 5) {
  const clean = encodeURIComponent(ticker)
  const res = await client.get(`/fundamentals/income-statement/${clean}?limit=${limit}`)
  return res.data
}

export async function getBalanceSheet(ticker, limit = 5) {
  const clean = encodeURIComponent(ticker)
  const res = await client.get(`/fundamentals/balance-sheet/${clean}?limit=${limit}`)
  return res.data
}

export async function getFinancialRatios(ticker) {
  const clean = encodeURIComponent(ticker)
  const res = await client.get(`/fundamentals/ratios/${clean}`)
  return res.data
}

/**
 * 📈 Alpha Vantage / Twelve Data Technicals
 */
export async function getCandlesticks(ticker, period = '3mo', interval = '1d') {
  const clean = encodeURIComponent(ticker)
  const res = await client.get(`/technicals/candlesticks/${clean}?period=${period}&interval=${interval}`)
  return res.data
}

export async function getTechnicalIndicators(ticker) {
  const clean = encodeURIComponent(ticker)
  const res = await client.get(`/technicals/indicators/${clean}`)
  return res.data
}

/**
 * 🏛️ FRED Macroeconomic Radar
 */
export async function getMacroDashboard() {
  const res = await client.get('/macro/dashboard')
  return res.data
}

/**
 * 🪙 CoinGecko & Forex Hub
 */
export async function getTopCrypto(limit = 20) {
  const res = await client.get(`/crypto/top?limit=${limit}`)
  return res.data
}

export async function getForexRates() {
  const res = await client.get('/crypto/forex')
  return res.data
}

/**
 * ⚡ AI Stock Summary Generator
 */
export async function generateResearchReport(ticker) {
  const clean = encodeURIComponent(ticker)
  const res = await client.get(`/analyst/report/${clean}`)
  return res.data
}
