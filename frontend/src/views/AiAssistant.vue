<template>
  <div class="ai-assistant-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#409EFF"><ChatDotRound /></el-icon>
        </div>
        <div class="header-text">
          <h1>智能健康助手</h1>
          <p>结合知识库、公开健康数据与用户授权的私密数据提供更贴切的回答</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" class="new-chat-btn" @click="startNewChat">
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
      </div>
    </div>

    <div class="chat-container">
      <div class="chat-sidebar">
        <div class="sidebar-header"><h3>对话历史</h3></div>
        <div class="chat-history">
          <div
            v-for="chat in chatHistory"
            :key="chat.id"
            class="chat-item"
            :class="{ active: currentChatId === chat.id }"
            @click="loadChat(chat.id)"
          >
            <div class="chat-icon">
              <el-icon size="16" color="#409EFF"><ChatDotRound /></el-icon>
            </div>
            <div class="chat-info">
              <h4>{{ chat.title }}</h4>
              <p>{{ formatDate(chat.last_message_time) }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-main">
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-content">
              <el-icon size="64" color="#409EFF"><ChatDotRound /></el-icon>
              <h3>欢迎使用智能健康助手</h3>
              <p>你可以：</p>
              <ul>
                <li>分析健康数据并给出建议</li>
                <li>结合知识库回答健康问题</li>
                <li>选择私密健康数据，让回答更贴近个人情况</li>
              </ul>
              <div class="quick-actions">
                <el-button type="primary" plain @click="sendQuickMessage('分析我的健康状况')">分析健康状况</el-button>
                <el-button type="primary" plain @click="sendQuickMessage('如何保持健康的生活方式')">健康生活建议</el-button>
                <el-button type="primary" plain @click="sendQuickMessage('解释一下血压指标')">了解健康指标</el-button>
              </div>
            </div>
          </div>

          <template v-else>
            <div
              v-for="message in messages"
              :key="message.id"
              class="message"
              :class="{ 'user-message': message.is_user, 'ai-message': !message.is_user }"
            >
              <div class="message-avatar">
                <el-icon v-if="message.is_user" size="24" color="#409EFF"><User /></el-icon>
                <el-icon v-else size="24" color="#67C23A"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text">{{ message.message }}</div>
                <div
                  v-if="!message.is_user && (message.personalization_used || message.private_context_used || (message.references && message.references.length))"
                  class="message-extra"
                >
                  <el-tag v-if="message.personalization_used" size="small" effect="plain" type="success">已结合个性化数据</el-tag>
                  <el-tag v-if="message.private_context_used" size="small" effect="plain" type="warning">已使用私密数据</el-tag>
                  <el-tag
                    v-for="(refItem, refIndex) in message.references || []"
                    :key="`${message.id}-ref-${refIndex}`"
                    size="small"
                    effect="light"
                    class="ref-tag"
                  >
                    {{ refItem }}
                  </el-tag>
                </div>
                <div class="message-time">{{ formatTime(message.created_at) }}</div>
              </div>
            </div>

            <div v-if="isTyping && !streamingMessageId" class="message ai-message typing">
              <div class="message-avatar">
                <el-icon size="24" color="#67C23A"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
              </div>
            </div>
          </template>
        </div>

        <div class="chat-input">
          <div class="private-toolbar">
            <div class="private-toolbar-left">
              <el-button class="private-btn" @click="openPrivateContextDialog">
                <el-icon><Lock /></el-icon>
                选择私密数据
              </el-button>
              <span class="private-toolbar-tip">
                {{ selectedPrivateContextIds.length ? `已选择 ${selectedPrivateContextIds.length} 项私密数据` : '未选择私密数据' }}
              </span>
            </div>
            <div v-if="selectedPrivateContextLabels.length" class="selected-private-tags">
              <el-tag
                v-for="item in selectedPrivateContextLabels"
                :key="item.id"
                closable
                size="small"
                effect="plain"
                type="warning"
                @close="removeSelectedPrivateContext(item.id)"
              >
                {{ item.label }}
              </el-tag>
            </div>
          </div>

          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="请输入你的问题..."
              @keydown.enter.ctrl="sendMessage"
              resize="none"
              class="message-input"
            />
            <div class="input-actions">
              <el-button v-if="isTyping" @click="stopStreaming" class="stop-btn">停止生成</el-button>
              <el-button
                type="primary"
                @click="sendMessage"
                :loading="isTyping"
                :disabled="!inputMessage.trim() || isTyping"
                class="send-btn"
              >
                <el-icon><Promotion /></el-icon>
                发送
              </el-button>
            </div>
          </div>

          <div v-if="streamStatusText" class="stream-status" :class="{ active: isTyping }">
            <span class="status-dot"></span>
            <span>{{ streamStatusText }}</span>
          </div>
          <div class="input-tips"><span>按 Ctrl+Enter 快速发送</span></div>
        </div>
      </div>
    </div>

    <el-dialog v-model="privateContextDialogVisible" title="选择用于 AI 问答的私密数据" width="640px">
      <div class="private-dialog-desc">
        你勾选的数据会在本次问答中由系统自动读取并解密，仅作为当前回答的前置上下文使用。
      </div>
      <el-skeleton v-if="loadingPrivateOptions" :rows="5" animated />
      <template v-else>
        <el-empty v-if="!privateContextOptions.length" description="暂无可选的私密数据" />
        <el-checkbox-group v-else v-model="selectedPrivateContextIds" class="private-option-group">
          <div
            v-for="option in privateContextOptions"
            :key="option.id"
            class="private-option-item"
            :class="{ disabled: !option.available }"
          >
            <el-checkbox :label="option.id" :disabled="!option.available">
              <div class="private-option-content">
                <div class="private-option-title">{{ option.label }}</div>
                <div class="private-option-desc">
                  {{ option.description || (option.available ? '可用于当前问答' : '当前不可用') }}
                </div>
              </div>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </template>
      <template #footer>
        <el-button @click="privateContextDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="privateContextDialogVisible = false">确认使用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { aiApi } from '../api/ai'

const messages = ref([])
const chatHistory = ref([])
const currentChatId = ref(null)
const inputMessage = ref('')
const isTyping = ref(false)
const streamingMessageId = ref(null)
const streamStatusText = ref('')
const isStopRequested = ref(false)
const messagesContainer = ref()

const privateContextDialogVisible = ref(false)
const privateContextOptions = ref([])
const selectedPrivateContextIds = ref([])
const loadingPrivateOptions = ref(false)

let streamController = null

const selectedPrivateContextLabels = computed(() => {
  const selectedSet = new Set(selectedPrivateContextIds.value)
  return privateContextOptions.value.filter((item) => selectedSet.has(item.id))
})

const loadChatHistory = async () => {
  try {
    chatHistory.value = await aiApi.getChatHistory()
  } catch {
    ElMessage.error('加载对话历史失败')
  }
}

const loadChat = async (chatId) => {
  try {
    currentChatId.value = chatId
    messages.value = await aiApi.getChatMessages(chatId)
    scrollToBottom()
  } catch {
    ElMessage.error('加载对话内容失败')
  }
}

const loadPrivateContextOptions = async () => {
  loadingPrivateOptions.value = true
  try {
    const result = await aiApi.getPrivateContextOptions()
    privateContextOptions.value = result?.items || []
    const validIds = new Set(privateContextOptions.value.map((item) => item.id))
    selectedPrivateContextIds.value = selectedPrivateContextIds.value.filter((id) => validIds.has(id))
  } catch {
    ElMessage.error('加载私密数据选项失败')
  } finally {
    loadingPrivateOptions.value = false
  }
}

const openPrivateContextDialog = async () => {
  privateContextDialogVisible.value = true
  await loadPrivateContextOptions()
}

const removeSelectedPrivateContext = (id) => {
  selectedPrivateContextIds.value = selectedPrivateContextIds.value.filter((item) => item !== id)
}

const startNewChat = () => {
  if (isTyping.value) stopStreaming()
  currentChatId.value = null
  messages.value = []
  inputMessage.value = ''
}

const getAiErrorMessage = (error) => {
  if (error?.name === 'AbortError') return '已停止生成'
  if (error?.code === 'ECONNABORTED' || String(error?.message || '').toLowerCase().includes('timeout')) {
    return 'AI 回复超时，请稍后重试'
  }
  return error?.response?.data?.detail || error?.message || '发送消息失败，请重试'
}

const stopStreaming = () => {
  isStopRequested.value = true
  streamStatusText.value = '已停止生成'
  if (streamController) streamController.abort()
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isTyping.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({
    id: Date.now(),
    message: userMessage,
    is_user: true,
    created_at: new Date().toISOString()
  })
  scrollToBottom()

  try {
    isTyping.value = true
    isStopRequested.value = false
    streamStatusText.value = selectedPrivateContextIds.value.length
      ? '正在准备你选择的私密数据...'
      : '正在检索知识库...'
    streamController = new AbortController()

    const aiMessageId = Date.now() + 1
    streamingMessageId.value = aiMessageId
    messages.value.push({
      id: aiMessageId,
      message: '',
      is_user: false,
      created_at: new Date().toISOString(),
      references: [],
      personalization_used: false,
      private_context_used: 0
    })

    await aiApi.streamMessage(
      {
        message: userMessage,
        chat_id: currentChatId.value,
        selected_private_context_ids: selectedPrivateContextIds.value
      },
      {
        signal: streamController.signal,
        onMeta: (meta) => {
          streamStatusText.value = '正在生成回答...'
          if (meta?.chat_id) currentChatId.value = meta.chat_id
          const target = messages.value.find((item) => item.id === aiMessageId)
          if (target) {
            target.references = meta?.references || []
            target.personalization_used = !!meta?.personalization_used
            target.private_context_used = meta?.private_context_used || 0
          }
        },
        onStatus: (payload) => {
          if (payload?.text) streamStatusText.value = payload.text
        },
        onDelta: (payload) => {
          const target = messages.value.find((item) => item.id === aiMessageId)
          if (target) {
            target.message += payload?.content || ''
            scrollToBottom()
          }
        },
        onDone: async (payload) => {
          streamStatusText.value = '回答完成'
          const target = messages.value.find((item) => item.id === aiMessageId)
          if (target) {
            target.message = payload?.reply || target.message
            target.created_at = payload?.timestamp || target.created_at
            target.references = payload?.references || target.references || []
            target.personalization_used = !!payload?.personalization_used
            target.private_context_used = payload?.private_context_used || target.private_context_used || 0
          }
          if (payload?.chat_id) currentChatId.value = payload.chat_id
          await loadChatHistory()
        }
      }
    )
  } catch (error) {
    const targetIndex = messages.value.findIndex((item) => item.id === streamingMessageId.value)
    if (targetIndex >= 0 && !messages.value[targetIndex].message) {
      messages.value.splice(targetIndex, 1)
    }
    if (!isStopRequested.value) ElMessage.error(getAiErrorMessage(error))
  } finally {
    streamController = null
    streamingMessageId.value = null
    isTyping.value = false
    if (streamStatusText.value === '回答完成') {
      setTimeout(() => {
        if (!isTyping.value) streamStatusText.value = ''
      }, 1500)
    } else if (!isStopRequested.value) {
      streamStatusText.value = ''
    }
    scrollToBottom()
  }
}

const sendQuickMessage = (message) => {
  inputMessage.value = message
  sendMessage()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatDate = (dateString) => new Date(dateString).toLocaleDateString('zh-CN')
const formatTime = (dateString) => new Date(dateString).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })

onMounted(async () => {
  await Promise.all([loadChatHistory(), loadPrivateContextOptions()])
})
</script>

<style scoped>
.ai-assistant-container { max-width: 1400px; margin: 0 auto; height: calc(100vh - 120px); }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding: 24px; background: linear-gradient(135deg, #409EFF 0%, #36A3F5 100%); border-radius: 16px; color: white; box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2); }
.header-content { display: flex; align-items: center; gap: 16px; }
.header-icon { width: 64px; height: 64px; background: rgba(255,255,255,0.2); border-radius: 16px; display: flex; align-items: center; justify-content: center; }
.header-text h1 { font-size: 28px; font-weight: 700; margin: 0 0 4px; }
.header-text p { margin: 0; opacity: 0.92; }
.new-chat-btn { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.35); color: white; border-radius: 12px; }
.chat-container { display: flex; gap: 24px; height: calc(100% - 120px); }
.chat-sidebar { width: 280px; background: white; border-radius: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); overflow: hidden; }
.sidebar-header { padding: 20px; border-bottom: 1px solid #e2e8f0; }
.sidebar-header h3 { margin: 0; }
.chat-history { height: calc(100% - 60px); overflow-y: auto; }
.chat-item { display: flex; gap: 12px; padding: 16px 20px; cursor: pointer; border-bottom: 1px solid #f1f5f9; }
.chat-item:hover { background: #f8fafc; }
.chat-item.active { background: #e3f2fd; border-left: 3px solid #409EFF; }
.chat-icon { width: 32px; height: 32px; background: #f1f5f9; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.chat-info { min-width: 0; }
.chat-info h4 { margin: 0 0 2px; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chat-info p { margin: 0; font-size: 12px; color: #94a3b8; }
.chat-main { flex: 1; background: white; border-radius: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 24px; }
.welcome-message { height: 100%; display: flex; align-items: center; justify-content: center; }
.welcome-content { text-align: center; max-width: 560px; }
.welcome-content ul { text-align: left; color: #64748b; margin-bottom: 24px; }
.quick-actions { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
.message { display: flex; gap: 12px; margin-bottom: 20px; }
.user-message { flex-direction: row-reverse; }
.message-avatar { width: 40px; height: 40px; background: #f1f5f9; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.user-message .message-avatar { background: #e3f2fd; }
.message-content { max-width: 72%; }
.message-text { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; word-break: break-word; white-space: pre-wrap; }
.user-message .message-text { background: #409EFF; color: white; border-bottom-right-radius: 4px; }
.ai-message .message-text { background: #f8fafc; color: #1e293b; border-bottom-left-radius: 4px; border: 1px solid #e2e8f0; }
.message-time { font-size: 12px; color: #94a3b8; margin-top: 4px; text-align: right; }
.user-message .message-time { text-align: left; }
.message-extra { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
.ref-tag { max-width: 260px; }
.typing-indicator { padding: 12px 16px; background: #f8fafc; border-radius: 16px; border-bottom-left-radius: 4px; border: 1px solid #e2e8f0; display: flex; gap: 4px; }
.typing-indicator span { width: 8px; height: 8px; background: #94a3b8; border-radius: 50%; animation: typing 1.4s infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-8px); } }
.chat-input { border-top: 1px solid #e2e8f0; padding: 18px 20px 20px; }
.private-toolbar { margin-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.private-toolbar-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.private-btn { border-radius: 12px; }
.private-toolbar-tip { font-size: 13px; color: #64748b; }
.selected-private-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.input-container { display: flex; gap: 12px; align-items: flex-end; }
.input-actions { display: flex; gap: 8px; align-items: center; }
.message-input { flex: 1; }
:deep(.message-input .el-textarea__inner) { border-radius: 12px; border: 2px solid #e2e8f0; }
:deep(.message-input .el-textarea__inner:focus) { border-color: #409EFF; box-shadow: 0 0 0 3px rgba(64,158,255,0.1); }
.send-btn, .stop-btn { border-radius: 12px; }
.stream-status { margin-top: 10px; display: flex; align-items: center; gap: 8px; min-height: 20px; color: #64748b; font-size: 13px; }
.stream-status.active { color: #2563eb; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; animation: pulse-dot 1.2s infinite ease-in-out; }
@keyframes pulse-dot { 0%,100% { transform: scale(.9); opacity: .5; } 50% { transform: scale(1.15); opacity: 1; } }
.input-tips { margin-top: 8px; text-align: center; color: #94a3b8; font-size: 12px; }
.private-dialog-desc { margin-bottom: 16px; color: #64748b; line-height: 1.6; }
.private-option-group { display: flex; flex-direction: column; gap: 12px; max-height: 420px; overflow-y: auto; padding-right: 4px; }
.private-option-item { border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; }
.private-option-item.disabled { opacity: .6; background: #fafafa; }
.private-option-content { display: inline-flex; flex-direction: column; gap: 4px; }
.private-option-title { font-weight: 600; color: #1f2937; }
.private-option-desc { font-size: 13px; color: #6b7280; }
@media (max-width: 768px) {
  .chat-container { flex-direction: column; height: auto; }
  .chat-sidebar { width: 100%; height: 200px; }
  .chat-main { height: 600px; }
  .message-content { max-width: 85%; }
}
</style>
