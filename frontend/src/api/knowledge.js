import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || localStorage.getItem('adminToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('adminToken')
      localStorage.removeItem('username')
      localStorage.removeItem('adminUsername')
      localStorage.removeItem('userRole')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const knowledgeApi = {
  async getArticles(params = {}) {
    const { data } = await api.get('/knowledge/articles', { params })
    return data
  },

  async getArticleDetail(articleId) {
    const { data } = await api.get(`/knowledge/articles/${articleId}`)
    return data
  },

  async favoriteArticle(articleId) {
    const { data } = await api.post(`/knowledge/articles/${articleId}/favorite`)
    return data
  },

  async unfavoriteArticle(articleId) {
    const { data } = await api.delete(`/knowledge/articles/${articleId}/favorite`)
    return data
  },

  async getFavorites(params = {}) {
    const { data } = await api.get('/knowledge/favorites', { params })
    return data
  },

  async getReadHistory(limit = 30) {
    const { data } = await api.get('/knowledge/read-history', { params: { limit } })
    return data
  },

  async getHomepageRecommendations() {
    const { data } = await api.get('/knowledge/recommendations/home')
    return data
  },

  async createArticle(payload) {
    const { data } = await api.post('/knowledge/admin/articles', payload)
    return data
  },

  async updateArticle(articleId, payload) {
    const { data } = await api.put(`/knowledge/admin/articles/${articleId}`, payload)
    return data
  },

  async deleteArticle(articleId) {
    const { data } = await api.delete(`/knowledge/admin/articles/${articleId}`)
    return data
  }
}
