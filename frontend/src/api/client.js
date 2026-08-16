import axios from 'axios'

// Dynamically resolve base API URL and ensure /api prefix is always present
let envUrl = import.meta.env.VITE_API_URL || '/api'

if (envUrl.startsWith('http')) {
  // Remove any trailing slashes
  envUrl = envUrl.replace(/\/+$/, '')
  // If user pasted backend root without /api, append /api automatically
  if (!envUrl.endsWith('/api')) {
    envUrl = `${envUrl}/api`
  }
}

const client = axios.create({
  baseURL: envUrl,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Unwrap response data automatically
client.interceptors.response.use(
  res => res.data,
  err => {
    console.warn('API Warning:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default client
