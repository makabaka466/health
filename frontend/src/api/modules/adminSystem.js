import { createHttpClient } from '../core/http'

const adminSystemApi = createHttpClient({ tokenMode: 'admin' })

export async function getSystemSettings() {
  return adminSystemApi.get('/admin/system/settings')
}

export async function updateSystemSettings(payload) {
  return adminSystemApi.put('/admin/system/settings', payload)
}

export async function getSystemLogs(params = {}) {
  return adminSystemApi.get('/admin/system/logs', { params })
}
