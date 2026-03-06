import { createHttpClient } from '../core/http'

const userApi = createHttpClient({ tokenMode: 'both' })
const adminApi = createHttpClient({ tokenMode: 'admin' })

export async function registerUser(payload) {
  return userApi.post('/auth/register', payload)
}

export async function getCurrentUserProfile() {
  return userApi.get('/auth/me')
}

export async function getMyProfileData(privateKey) {
  const params = {}
  if (privateKey) {
    params.private_key = privateKey
  }
  return userApi.get('/auth/me/profile', { params })
}

export async function upsertMyProfileData(payload) {
  return userApi.post('/auth/me/profile', payload)
}

export async function revealMyPrivateKey(password) {
  return userApi.post('/auth/me/private-key', { password })
}

export async function getAdminUsers(params = {}) {
  return adminApi.get('/auth/admin/users', { params })
}

export async function getAdminUserDetail(userId) {
  return adminApi.get(`/auth/admin/users/${userId}`)
}

export async function updateAdminUserStatus(userId, isActive) {
  return adminApi.patch(`/auth/admin/users/${userId}/status`, null, {
    params: { is_active: isActive }
  })
}

export async function resetAdminUserPassword(userId) {
  return adminApi.post(`/auth/admin/users/${userId}/reset-password`)
}

export async function loginUser(payload) {
  const form = new URLSearchParams()
  form.append('username', payload.username)
  form.append('password', payload.password)

  return userApi.post('/auth/login', form, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}

export async function adminLoginUser(payload) {
  const form = new URLSearchParams()
  form.append('username', payload.username)
  form.append('password', payload.password)

  return userApi.post('/auth/admin/login', form, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}
