<template>
  <div class="ai-chat-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#E6A23C">
            <ChatDotRound />
          </el-icon>
        </div>
        <div class="header-text">
          <h1>AI健康助手</h1>
          <p>获取智能健康建议和咨询</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" class="new-chat-btn">
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
      </div>
    </div>
    
    <div class="chat-layout">
      <el-row :gutter="24">
        <el-col :span="6">
          <el-card class="chat-sidebar" shadow="hover">
            <div class="sidebar-header">
              <h3>对话历史</h3>
              <el-button type="text" size="small">清空</el-button>
            </div>
            <div class="chat-list">
              <div 
                v-for="(chat, index) in chatHistory" 
                :key="index"
                class="chat-item"
                :class="{ active: chat.id === activeChatId }"
                @click="selectChat(chat.id)"
              >
                <div class="chat-icon">
                  <el-icon size="16" color="#E6A23C"><ChatDotRound /></el-icon>
                </div>
                <div class="chat-content">
                  <h4>{{ chat.title }}</h4>
                  <p>{{ chat.preview }}</p>
                </div>
                <span class="chat-time">{{ chat.time }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="18">
          <el-card class="chat-main" shadow="hover">
            <div class="chat-messages">
              <div 
                v-for="(message, index) in messages" 
                :key="index"
                class="message-item"
                :class="message.type"
              >
                <div class="message-avatar">
                  <el-avatar v-if="message.type === 'user'" size="32">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <el-avatar v-else size="32" style="background: linear-gradient(135deg, #E6A23C, #F7BA2A);">
                    <el-icon><ChatDotRound /></el-icon>
                  </el-avatar>
                </div>
                <div class="message-content">
                  <div class="message-bubble">
                    {{ message.content }}
                  </div>
                  <span class="message-time">{{ message.time }}</span>
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
                  resize="none"
                  class="message-input"
                />
                <div class="input-actions">
                  <el-button type="text" size="small">
                    <el-icon><Paperclip /></el-icon>
                  </el-button>
                  <el-button type="primary" class="send-btn" @click="sendMessage">
                    <el-icon><Promotion /></el-icon>
                    发送
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeChatId = ref(1)
const inputMessage = ref('')

const chatHistory = ref([
  {
    id: 1,
    title: '睡眠质量咨询',
    preview: '如何改善睡眠质量...',
    time: '2小时前'
  },
  {
    id: 2,
    title: '饮食建议',
    preview: '健康饮食搭配推荐...',
    time: '昨天'
  },
  {
    id: 3,
    title: '运动计划',
    preview: '适合我的运动方式...',
    time: '3天前'
  }
])

const messages = ref([
  {
    type: 'user',
    content: '您好，我想了解一下如何改善睡眠质量？',
    time: '14:30'
  },
  {
    type: 'ai',
    content: '您好！改善睡眠质量可以从以下几个方面入手：\n\n1. 保持规律的作息时间\n2. 营造舒适的睡眠环境\n3. 避免睡前使用电子设备\n4. 适量运动但避免睡前剧烈运动\n\n您想了解哪个方面的详细信息呢？',
    time: '14:31'
  },
  {
    type: 'user',
    content: '请详细介绍一下营造舒适睡眠环境的方法',
    time: '14:32'
  },
  {
    type: 'ai',
    content: '营造舒适睡眠环境的关键要素：\n\n🌙 **光线控制**：使用遮光窗帘，保持房间黑暗\n\n🌡️ **温度调节**：室温保持在18-22°C\n\n🔇 **噪音减少**：使用耳塞或白噪音机\n\n🛏️ **床品选择**：选择适合的床垫和枕头\n\n这些方法可以帮助您获得更好的睡眠质量。',
    time: '14:33'
  }
])

const selectChat = (chatId) => {
  activeChatId.value = chatId
}

const sendMessage = () => {
  if (!inputMessage.value.trim()) return
  
  const newMessage = {
    type: 'user',
    content: inputMessage.value,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  messages.value.push(newMessage)
  inputMessage.value = ''
  
  // 模拟AI回复
  setTimeout(() => {
    const aiResponse = {
      type: 'ai',
      content: '感谢您的提问，我正在为您分析这个问题...',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    messages.value.push(aiResponse)
  }, 1000)
}
</script>

<style scoped>
.ai-chat-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #E6A23C 0%, #F7BA2A 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 24px rgba(230, 162, 60, 0.2);
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

.chat-layout {
  margin-bottom: 32px;
}

.chat-sidebar {
  border-radius: 16px;
  border: none;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.chat-item:hover {
  background: #f8fafc;
  transform: translateX(4px);
}

.chat-item.active {
  background: linear-gradient(135deg, rgba(230, 162, 60, 0.1), rgba(247, 186, 42, 0.1));
  border-left: 3px solid #E6A23C;
}

.chat-icon {
  width: 32px;
  height: 32px;
  background: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-content {
  flex: 1;
  min-width: 0;
}

.chat-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-content p {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-time {
  font-size: 11px;
  color: #94a3b8;
  flex-shrink: 0;
}

.chat-main {
  border-radius: 16px;
  border: none;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-item.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.ai {
  align-self: flex-start;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-item.ai .message-content {
  align-items: flex-start;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message-item.user .message-bubble {
  background: linear-gradient(135deg, #409EFF, #36A3F5);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-item.ai .message-bubble {
  background: #f8fafc;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #94a3b8;
  padding: 0 4px;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #e2e8f0;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
}

.input-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.send-btn {
  border-radius: 12px;
  padding: 8px 16px;
}

/* 滚动条样式 */
.chat-list::-webkit-scrollbar,
.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-list::-webkit-scrollbar-track,
.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-list::-webkit-scrollbar-thumb,
.chat-messages::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.chat-list::-webkit-scrollbar-thumb:hover,
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .chat-layout .el-col:first-child {
    display: none;
  }
  
  .chat-layout .el-col:last-child {
    flex: 0 0 100%;
  }
  
  .message-item {
    max-width: 90%;
  }
}
</style>