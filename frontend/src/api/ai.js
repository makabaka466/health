import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000 // AI响应可能需要更长时间
})

// 添加请求拦截器，自动添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
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

export const aiApi = {
  // 发送消息给AI助手
  async sendMessage(messageData) {
    const { data } = await api.post('/ai/chat', messageData)
    return data
  },

  // 获取对话历史
  async getChatHistory() {
    const { data } = await api.get('/ai/chat/history')
    return data
  },

  // 获取特定对话的消息
  async getChatMessages(chatId) {
    const { data } = await api.get(`/ai/chat/${chatId}/messages`)
    return data
  },

  // 删除对话
  async deleteChat(chatId) {
    const { data } = await api.delete(`/ai/chat/${chatId}`)
    return data
  },

  // 获取健康建议
  async getHealthRecommendations(userId) {
    const { data } = await api.get(`/ai/recommendations/${userId}`)
    return data
  },

  // 分析健康数据
  async analyzeHealthData(payload) {
    const { data } = await api.post('/ai/analyze', payload)
    return data
  }
}
