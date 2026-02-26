import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

export async function registerUser(payload) {
  const { data } = await api.post('/auth/register', payload)
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
