<template>
  <div class="ai-assistant-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#409EFF">
            <ChatDotRound />
          </el-icon>
        </div>
        <div class="header-text">
          <h1>智能健康助手</h1>
          <p>您的专业健康顾问，随时为您提供健康建议</p>
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
        <div class="sidebar-header">
          <h3>对话历史</h3>
        </div>
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
              <p>我可以帮助您：</p>
              <ul>
                <li>分析健康数据并提供建议</li>
                <li>回答健康相关问题</li>
                <li>提供个性化的健康指导</li>
                <li>推荐适合的健康知识</li>
              </ul>
              <div class="quick-actions">
                <el-button type="primary" plain @click="sendQuickMessage('分析我的健康状况')">
                  分析健康状况
                </el-button>
                <el-button type="primary" plain @click="sendQuickMessage('如何保持健康的生活方式')">
                  健康生活建议
                </el-button>
                <el-button type="primary" plain @click="sendQuickMessage('解释一下血压指标')">
                  了解健康指标
                </el-button>
              </div>
            </div>
          </div>
          
          <div v-else>
            <div 
              v-for="message in messages" 
              :key="message.id"
              class="message"
              :class="{ 'user-message': message.is_user, 'ai-message': !message.is_user }"
            >
              <div class="message-avatar">
                <el-icon v-if="message.is_user" size="24" color="#409EFF">
                  <User />
                </el-icon>
                <el-icon v-else size="24" color="#67C23A">
                  <ChatDotRound />
                </el-icon>
              </div>
              <div class="message-content">
                <div class="message-text">{{ message.message }}</div>
                <div class="message-time">{{ formatTime(message.created_at) }}</div>
              </div>
            </div>
            
            <div v-if="isTyping" class="message ai-message typing">
              <div class="message-avatar">
                <el-icon size="24" color="#67C23A">
                  <ChatDotRound />
                </el-icon>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="chat-input">
          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="请输入您的问题..."
              @keydown.enter.ctrl="sendMessage"
              resize="none"
              class="message-input"
            />
            <div class="input-actions">
              <el-button 
                type="primary" 
                @click="sendMessage"
                :loading="isTyping"
                :disabled="!inputMessage.trim()"
                class="send-btn"
              >
                <el-icon><Promotion /></el-icon>
                发送
              </el-button>
            </div>
          </div>
          <div class="input-tips">
            <span>按 Ctrl+Enter 快速发送</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { aiApi } from '../api/ai'

const messages = ref([])
const chatHistory = ref([])
const currentChatId = ref(null)
const inputMessage = ref('')
const isTyping = ref(false)
const messagesContainer = ref()

const loadChatHistory = async () => {
  try {
    const history = await aiApi.getChatHistory()
    chatHistory.value = history
  } catch (error) {
    ElMessage.error('加载对话历史失败')
  }
}

const loadChat = async (chatId) => {
  try {
    currentChatId.value = chatId
    const chatMessages = await aiApi.getChatMessages(chatId)
    messages.value = chatMessages
    scrollToBottom()
  } catch (error) {
    ElMessage.error('加载对话内容失败')
  }
}

const startNewChat = () => {
  currentChatId.value = null
  messages.value = []
  inputMessage.value = ''
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isTyping.value) return
  
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 添加用户消息
  const userMsg = {
    id: Date.now(),
    message: userMessage,
    is_user: true,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  
  scrollToBottom()
  
  try {
    isTyping.value = true
    
    // 发送消息到AI
    const response = await aiApi.sendMessage({
      message: userMessage,
      chat_id: currentChatId.value
    })
    
    // 添加AI回复
    const aiMsg = {
      id: Date.now() + 1,
      message: response.reply,
      is_user: false,
      created_at: response.timestamp
    }
    messages.value.push(aiMsg)
    
    // 更新当前对话ID
    if (response.chat_id) {
      currentChatId.value = response.chat_id
    }
    
    // 刷新对话历史
    await loadChatHistory()
    
  } catch (error) {
    ElMessage.error('发送消息失败，请重试')
  } finally {
    isTyping.value = false
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

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadChatHistory()
})
</script>

<style scoped>
.ai-assistant-container {
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 120px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #409EFF 0%, #36A3F5 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.header-text h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.header-text p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.new-chat-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.new-chat-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.chat-container {
  display: flex;
  gap: 24px;
  height: calc(100% - 120px);
}

.chat-sidebar {
  width: 280px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.chat-history {
  height: calc(100% - 60px);
  overflow-y: auto;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid #f1f5f9;
}

.chat-item:hover {
  background: #f8fafc;
}

.chat-item.active {
  background: #e3f2fd;
  border-left: 3px solid #409EFF;
}

.chat-icon {
  width: 32px;
  height: 32px;
  background: #f1f5f9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-info {
  flex: 1;
  min-width: 0;
}

.chat-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-info p {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}

.chat-main {
  flex: 1;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.welcome-message {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-content {
  text-align: center;
  max-width: 500px;
}

.welcome-content h3 {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}

.welcome-content p {
  font-size: 16px;
  color: #64748b;
  margin-bottom: 12px;
}

.welcome-content ul {
  text-align: left;
  color: #64748b;
  margin-bottom: 24px;
}

.welcome-content li {
  margin-bottom: 8px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  background: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: #e3f2fd;
}

.message-content {
  max-width: 70%;
  flex: 1;
}

.message-text {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.user-message .message-text {
  background: #409EFF;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-text {
  background: #f8fafc;
  color: #1e293b;
  border-bottom-left-radius: 4px;
  border: 1px solid #e2e8f0;
}

.message-time {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
  text-align: right;
}

.user-message .message-time {
  text-align: left;
}

.typing {
  margin-bottom: 20px;
}

.typing-indicator {
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  border: 1px solid #e2e8f0;
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #94a3b8;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.chat-input {
  border-top: 1px solid #e2e8f0;
  padding: 20px;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
}

:deep(.message-input .el-textarea__inner) {
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
}

:deep(.message-input .el-textarea__inner:focus) {
  border-color: #409EFF;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.send-btn {
  border-radius: 12px;
  padding: 12px 20px;
  font-weight: 600;
}

.input-tips {
  margin-top: 8px;
  text-align: center;
}

.input-tips span {
  font-size: 12px;
  color: #94a3b8;
}

@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
    height: auto;
  }
  
  .chat-sidebar {
    width: 100%;
    height: 200px;
  }
  
  .chat-main {
    height: 600px;
  }
  
  .message-content {
    max-width: 85%;
  }
}
</style>
