import { API_BASE_URL, createHttpClient } from '../core/http'

const AI_REQUEST_TIMEOUT = Number(import.meta.env.VITE_AI_TIMEOUT || 180000)

const api = createHttpClient({ timeout: AI_REQUEST_TIMEOUT, tokenMode: 'both' })

const resolveChatToken = () => localStorage.getItem('token') || localStorage.getItem('adminToken')

const parseSseEvent = (rawEvent) => {
  const lines = rawEvent.split(/\r?\n/)
  let event = 'message'
  const dataLines = []

  for (const line of lines) {
    if (!line) continue
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }

  if (!dataLines.length) {
    return null
  }

  try {
    return { event, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    return { event, data: { raw: dataLines.join('\n') } }
  }
}

export const aiApi = {
  async sendMessage(messageData) {
    return api.post('/ai/chat', messageData)
  },

  async streamMessage(messageData, handlers = {}) {
    const token = resolveChatToken()
    const response = await fetch(`${API_BASE_URL}/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(messageData),
      signal: handlers.signal
    })

    if (!response.ok) {
      let detail = '流式聊天请求失败'
      try {
        const errorData = await response.json()
        detail = errorData?.detail || detail
      } catch {
        // ignore parse failure
      }
      throw new Error(detail)
    }

    if (!response.body) {
      throw new Error('浏览器不支持流式响应')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let doneReceived = false

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const rawEvent of events) {
        const parsed = parseSseEvent(rawEvent)
        if (!parsed) continue

        const { event, data } = parsed
        if (event === 'meta' && handlers.onMeta) {
          handlers.onMeta(data)
        } else if (event === 'status' && handlers.onStatus) {
          handlers.onStatus(data)
        } else if (event === 'delta' && handlers.onDelta) {
          handlers.onDelta(data)
        } else if (event === 'done' && handlers.onDone) {
          doneReceived = true
          handlers.onDone(data)
        } else if (event === 'error') {
          const error = new Error(data?.detail || '流式输出失败')
          if (handlers.onError) {
            handlers.onError(error)
          }
          throw error
        }
      }
    }

    if (buffer.trim()) {
      const parsed = parseSseEvent(buffer.trim())
      if (parsed?.event === 'done' && handlers.onDone && !doneReceived) {
        handlers.onDone(parsed.data)
      }
    }
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
  },

  async getHomeAdvice() {
    return api.get('/ai/home-advice')
  },

  async getPrivateContextOptions() {
    return api.get('/ai/private-context/options')
  }
}
