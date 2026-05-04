import { createHttpClient } from '../core/http'

const adminSystemApi = createHttpClient({ tokenMode: 'admin' })
const publicSystemApi = createHttpClient({ tokenMode: 'both' })

export async function getSystemSettings() {
  return adminSystemApi.get('/admin/system/settings')
}

export async function updateSystemSettings(payload) {
  return adminSystemApi.put('/admin/system/settings', payload)
}

export async function getSystemLogs(params = {}) {
  return adminSystemApi.get('/admin/system/logs', { params })
}

export async function getAdminHealthRecords(params = {}) {
  return adminSystemApi.get('/admin/system/health-records', { params })
}

export async function getAdminHealthRecordDetail(recordId, params = {}) {
  return adminSystemApi.get(`/admin/system/health-records/${recordId}`, { params })
}

export async function getPublicSystemSettings() {
  return publicSystemApi.get('/admin/system/public-settings')
}
