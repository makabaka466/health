import { createHttpClient } from '../core/http'

const api = createHttpClient({ tokenMode: 'both' })

export const healthApi = {
  async getRecords(params = {}) {
    return api.get('/health/records', { params })
  },

  async createRecord(recordData) {
    return api.post('/health/records', recordData)
  },

  async getRecord(recordId, params = {}) {
    return api.get(`/health/records/${recordId}`, { params })
  },

  async updateRecord(recordId, recordData) {
    return api.put(`/health/records/${recordId}`, recordData)
  },

  async deleteRecord(recordId) {
    return api.delete(`/health/records/${recordId}`)
  },

  async getPublicRecords(params = {}) {
    return api.get('/health/public/records', { params })
  },

  async getPublicRecord(recordId) {
    return api.get(`/health/public/records/${recordId}`)
  },

  async getSharedRecords(params = {}) {
    return api.get('/health/shared/records', { params })
  },

  async getSharedRecord(recordId, params = {}) {
    return api.get(`/health/shared/records/${recordId}`, { params })
  },

  async getSummary(params = {}) {
    return api.get('/health/summary', { params })
  },

  async analyzeData(analysisRequest = {}, params = {}) {
    return api.post('/health/analyze', analysisRequest, { params })
  },

  async getGrantableUsers() {
    return api.get('/health/grantable-users')
  },

  async getRecordGrants(recordId) {
    return api.get(`/health/records/${recordId}/grants`)
  },

  async createRecordGrant(recordId, payload) {
    return api.post(`/health/records/${recordId}/grants`, payload)
  },

  async revokeRecordGrant(grantId) {
    return api.delete(`/health/grants/${grantId}`)
  }
}
