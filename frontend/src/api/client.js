import axios from 'axios'

// Dynamically use VITE_API_URL (e.g. https://finsight-backend.onrender.com/api) or fallback to local proxy /api
const envUrl = import.meta.env.VITE_API_URL
const baseURL = envUrl ? (envUrl.endsWith('/') ? envUrl.slice(0, -1) : envUrl) : '/api'

const client = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Unwrap response data automatically so callers get data directly
client.interceptors.response.use(
  res => res.data,
  err => {
    console.warn('API Warning:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default client
