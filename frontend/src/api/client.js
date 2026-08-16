import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Unwrap response data automatically so callers get data directly
client.interceptors.response.use(
  res => res.data,
  err => {
    console.error('API Error:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default client
