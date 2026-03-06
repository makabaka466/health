import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

function resolveToken(tokenMode) {
  if (tokenMode === 'admin') {
    return localStorage.getItem('adminToken')
  }
  if (tokenMode === 'user') {
    return localStorage.getItem('token')
  }
  return localStorage.getItem('token') || localStorage.getItem('adminToken')
}

function handleUnauthorized(tokenMode) {
  localStorage.removeItem('token')
  localStorage.removeItem('adminToken')
  localStorage.removeItem('username')
  localStorage.removeItem('adminUsername')
  localStorage.removeItem('userRole')

  if (tokenMode === 'admin') {
    window.location.href = '/admin/login'
    return
  }
  window.location.href = '/login'
}

export function createHttpClient({ timeout = 10000, tokenMode = 'both', unwrapData = true } = {}) {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout
  })

  client.interceptors.request.use((config) => {
    const token = resolveToken(tokenMode)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  client.interceptors.response.use(
    (response) => (unwrapData ? response.data : response),
    (error) => {
      if (error.response?.status === 401) {
        handleUnauthorized(tokenMode)
      }
      return Promise.reject(error)
    }
  )

  return client
}
