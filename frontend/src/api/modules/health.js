import { createHttpClient } from '../core/http'

const api = createHttpClient({ tokenMode: 'both' })

export const healthApi = {
  async getRecords(params = {}) {
    return api.get('/health/records', { params })
  },

  async createRecord(recordData) {
    return api.post('/health/records', recordData)
  },

  async getRecord(recordId) {
    return api.get(`/health/records/${recordId}`)
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

  async getSummary(params = {}) {
    return api.get('/health/summary', { params })
  },

  async analyzeData(analysisRequest = {}, params = {}) {
    return api.post('/health/analyze', analysisRequest, { params })
  }
}
