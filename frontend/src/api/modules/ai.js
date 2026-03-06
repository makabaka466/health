import { createHttpClient } from '../core/http'

const api = createHttpClient({ timeout: 30000, tokenMode: 'user' })

export const aiApi = {
  async sendMessage(messageData) {
    return api.post('/ai/chat', messageData)
  },

  async getChatHistory() {
    return api.get('/ai/chat/history')
  },

  async getChatMessages(chatId) {
    return api.get(`/ai/chat/${chatId}/messages`)
  },

  async deleteChat(chatId) {
    return api.delete(`/ai/chat/${chatId}`)
  },

  async getHealthRecommendations(userId) {
    return api.get(`/ai/recommendations/${userId}`)
  },

  async analyzeHealthData(payload) {
    return api.post('/ai/analyze', payload)
  }
}
