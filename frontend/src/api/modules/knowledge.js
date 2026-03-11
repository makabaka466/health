import { createHttpClient } from '../core/http'

const api = createHttpClient({ tokenMode: 'both' })

export const knowledgeApi = {
  async getArticles(params = {}) {
    return api.get('/knowledge/articles', { params })
  },

  async getArticleDetail(articleId) {
    return api.get(`/knowledge/articles/${articleId}`)
  },

  async favoriteArticle(articleId) {
    return api.post(`/knowledge/articles/${articleId}/favorite`)
  },

  async unfavoriteArticle(articleId) {
    return api.delete(`/knowledge/articles/${articleId}/favorite`)
  },

  async getFavorites(params = {}) {
    return api.get('/knowledge/favorites', { params })
  },

  async getReadHistory(limit = 30) {
    return api.get('/knowledge/read-history', { params: { limit } })
  },

  async getHomepageRecommendations() {
    return api.get('/knowledge/recommendations/home')
  },

  async createArticle(payload) {
    return api.post('/knowledge/admin/articles', payload)
  },

  async updateArticle(articleId, payload) {
    return api.put(`/knowledge/admin/articles/${articleId}`, payload)
  },

  async deleteArticle(articleId) {
    return api.delete(`/knowledge/admin/articles/${articleId}`)
  },

  async getRagDocs(params = {}) {
    return api.get('/knowledge/admin/rag-docs', { params })
  },

  async createRagDoc(payload) {
    return api.post('/knowledge/admin/rag-docs', payload)
  },

  async importRagDocs(formData) {
    return api.post('/knowledge/admin/rag-docs/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  async seedRagDocs() {
    return api.post('/knowledge/admin/rag-docs/seed-defaults')
  },

  async updateRagDoc(docId, payload) {
    return api.put(`/knowledge/admin/rag-docs/${docId}`, payload)
  },

  async deleteRagDoc(docId) {
    return api.delete(`/knowledge/admin/rag-docs/${docId}`)
  }
}
