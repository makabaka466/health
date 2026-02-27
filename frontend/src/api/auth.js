import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

const adminApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

adminApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('adminToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

adminApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminUsername')
      if (window.location.pathname.startsWith('/admin')) {
        window.location.href = '/admin/login'
      }
    }
    return Promise.reject(error)
  }
)

export async function registerUser(payload) {
  const { data } = await api.post('/auth/register', payload)
  return data
}

export async function getCurrentUserProfile() {
  const token = localStorage.getItem('token') || localStorage.getItem('adminToken')
  const headers = token ? { Authorization: `Bearer ${token}` } : {}
  const { data } = await api.get('/auth/me', { headers })
  return data
}

export async function getAdminUsers(params = {}) {
  const { data } = await adminApi.get('/auth/admin/users', { params })
  return data
}

export async function getAdminUserDetail(userId) {
  const { data } = await adminApi.get(`/auth/admin/users/${userId}`)
  return data
}

export async function updateAdminUserStatus(userId, isActive) {
  const { data } = await adminApi.patch(`/auth/admin/users/${userId}/status`, null, {
    params: { is_active: isActive }
  })
  return data
}

export async function resetAdminUserPassword(userId) {
  const { data } = await adminApi.post(`/auth/admin/users/${userId}/reset-password`)
  return data
}

export async function loginUser(payload) {
  const form = new URLSearchParams()
  form.append('username', payload.username)
  form.append('password', payload.password)

  const { data } = await api.post('/auth/login', form, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })

  return data
}

export async function adminLoginUser(payload) {
  const form = new URLSearchParams()
  form.append('username', payload.username)
  form.append('password', payload.password)

  const { data } = await api.post('/auth/admin/login', form, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })

  return data
}
