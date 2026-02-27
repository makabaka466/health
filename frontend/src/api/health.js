import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

// 添加请求拦截器，自动添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || localStorage.getItem('adminToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 添加响应拦截器，处理错误
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token过期，跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('userRole')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const healthApi = {
  // 获取健康数据记录
  async getRecords(params = {}) {
    return await api.get('/health/records', { params })
  },

  // 创建健康数据记录
  async createRecord(recordData) {
    return await api.post('/health/records', recordData)
  },

  // 获取单个健康数据记录
  async getRecord(recordId) {
    return await api.get(`/health/records/${recordId}`)
  },

  // 更新健康数据记录
  async updateRecord(recordId, recordData) {
    return await api.put(`/health/records/${recordId}`, recordData)
  },

  // 删除健康数据记录
  async deleteRecord(recordId) {
    return await api.delete(`/health/records/${recordId}`)
  },

  // 获取健康数据摘要
  async getSummary() {
    return await api.get('/health/summary')
  },

  // 分析健康数据
  async analyzeData(analysisRequest = {}) {
    return await api.post('/health/analyze', analysisRequest)
  }
}
