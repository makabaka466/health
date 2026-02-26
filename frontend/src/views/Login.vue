<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
      <div class="bg-particles">
        <div v-for="i in 20" :key="i" class="particle" :style="{ '--delay': i * 0.2 + 's' }"></div>
      </div>
    </div>
    
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <div class="logo-animation">
            <el-icon size="50" color="#409EFF">
              <Heart />
            </el-icon>
          </div>
        </div>
        <h2>健康管理系统</h2>
        <p>您的智能健康管理助手</p>
      </div>
      
      <!-- 快速登录提示 -->
      <div v-if="queryRegistered" class="quick-login-tip">
        <el-alert
          title="注册成功！"
          type="success"
          :description="`欢迎 ${queryUsername}，请使用您的账号密码登录`"
          show-icon
          :closable="false"
        />
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        size="large"
      >
        <el-form-item prop="username">
          <div class="input-wrapper">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              clearable
              class="custom-input"
            />
          </div>
        </el-form-item>
        
        <el-form-item prop="password">
          <div class="input-wrapper">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              clearable
              @keyup.enter="handleLogin"
              class="custom-input"
            />
          </div>
        </el-form-item>
        
        <el-form-item>
          <div class="remember-forgot">
            <el-checkbox v-model="rememberMe" class="custom-checkbox">记住我</el-checkbox>
            <el-link type="primary" :underline="false" class="forgot-link" @click="handleForgotPassword">忘记密码？</el-link>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            <span v-if="!loading">登录</span>
            <span v-else>登录中...</span>
          </el-button>
        </el-form-item>
        
        <el-divider class="divider">
          <span class="divider-text">或</span>
        </el-divider>
        
        <el-form-item>
          <div class="social-login">
            <el-button class="social-btn wechat-btn" @click="handleSocialLogin('wechat')">
              <el-icon><ChatDotRound /></el-icon>
              微信登录
            </el-button>
            <el-button class="social-btn qq-btn" @click="handleSocialLogin('qq')">
              <el-icon><ChatLineSquare /></el-icon>
              QQ登录
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item>
          <div class="register-link">
            <span>还没有账号？</span>
            <el-link type="primary" :underline="false" class="register-btn" @click="goToRegister">立即注册</el-link>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 忘记密码对话框 -->
    <el-dialog
      v-model="forgotPasswordVisible"
      title="找回密码"
      width="400px"
      append-to-body
    >
      <el-form
        ref="forgotFormRef"
        :model="forgotForm"
        :rules="forgotRules"
        label-position="top"
      >
        <el-form-item label="邮箱地址" prop="email">
          <el-input 
            v-model="forgotForm.email" 
            placeholder="请输入注册时使用的邮箱" 
            clearable 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="forgotPasswordVisible = false">取消</el-button>
          <el-button type="primary" :loading="forgotLoading" @click="handleSendResetEmail">
            发送重置邮件
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginUser } from '../api/auth'

const router = useRouter()
const route = useRoute()
const loginFormRef = ref()
const forgotFormRef = ref()
const loading = ref(false)
const forgotLoading = ref(false)
const rememberMe = ref(false)
const forgotPasswordVisible = ref(false)

// 从URL参数获取注册成功信息
const queryRegistered = computed(() => route.query.registered === 'true')
const queryUsername = computed(() => route.query.username || '')

const loginForm = reactive({
  username: queryUsername.value || '',
  password: ''
})

const forgotForm = reactive({
  email: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const forgotRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const extractError = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  return fallback
}

const goToRegister = () => {
  router.push('/register')
}

const handleForgotPassword = () => {
  forgotPasswordVisible.value = true
}

const handleSendResetEmail = async () => {
  if (!forgotFormRef.value) return

  try {
    const valid = await forgotFormRef.value.validate()
    if (!valid) return

    forgotLoading.value = true
    
    // 模拟发送重置邮件
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success('重置密码邮件已发送，请查收邮箱')
    forgotPasswordVisible.value = false
    forgotFormRef.value.resetFields()
  } catch (error) {
    ElMessage.error('发送失败，请重试')
  } finally {
    forgotLoading.value = false
  }
}

const handleSocialLogin = (platform) => {
  ElMessage.info(`${platform === 'wechat' ? '微信' : 'QQ'}登录功能开发中...`)
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const payload = await loginUser(loginForm)
    localStorage.setItem('token', payload.access_token)
    localStorage.setItem('username', payload.username || loginForm.username)
    localStorage.setItem('userRole', payload.role || 'user')
    localStorage.removeItem('adminToken')
    localStorage.removeItem('adminUsername')

    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(extractError(error, '登录失败，请重试'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 添加页面加载动画
  setTimeout(() => {
    document.querySelector('.login-box')?.classList.add('show')
  }, 100)
})
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #eef7ff 0%, #dceeff 100%);
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 150px;
  height: 150px;
  top: 70%;
  right: 10%;
  animation-delay: 2s;
}

.circle-3 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

/* 粒子效果 */
.bg-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  animation: particle-float 10s linear infinite;
}

.particle:nth-child(odd) {
  animation-delay: var(--delay);
  left: 10%;
  top: 90%;
}

.particle:nth-child(even) {
  animation-delay: var(--delay);
  right: 10%;
  top: 10%;
}

@keyframes particle-float {
  0% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) translateX(50px);
    opacity: 0;
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.login-box {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 60px 50px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  width: 100%;
  max-width: 480px;
  position: relative;
  z-index: 10;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-box.show {
  opacity: 1;
  transform: translateY(0);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo {
  margin-bottom: 25px;
}

.logo-animation {
  display: inline-block;
  animation: heartbeat 2s ease-in-out infinite;
}

@keyframes heartbeat {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.login-header h2 {
  color: #2c3e50;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-header p {
  color: #7f8c8d;
  font-size: 16px;
  font-weight: 400;
}

.quick-login-tip {
  margin-bottom: 20px;
}

.login-form {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.input-wrapper {
  position: relative;
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
}

.custom-input {
  width: 100%;
}

.remember-forgot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 360px;
  margin: 20px 0;
}

.custom-checkbox {
  color: #606266;
}

.forgot-link {
  font-weight: 500;
  transition: all 0.3s ease;
}

.forgot-link:hover {
  color: #409EFF;
  transform: translateX(2px);
}

.login-button {
  width: 100%;
  max-width: 360px;
  height: 54px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #409EFF, #36A3F5);
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.login-button:hover::before {
  left: 100%;
}

.login-button:hover {
  background: linear-gradient(135deg, #36A3F5, #409EFF);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
}

.login-button:active {
  transform: translateY(0);
}

.divider {
  margin: 25px 0;
}

:deep(.divider .el-divider__text) {
  background: transparent;
  padding: 0 15px;
}

.divider-text {
  color: #909399;
  font-size: 14px;
}

.social-login {
  display: flex;
  gap: 12px;
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
}

.social-btn {
  flex: 1;
  height: 50px;
  border-radius: 10px;
  border: 1px solid #dcdfe6;
  background: white;
  color: #606266;
  font-size: 14px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.social-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.wechat-btn:hover {
  border-color: #67c23a;
  color: #67c23a;
}

.qq-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.register-link {
  text-align: center;
  color: #7f8c8d;
  font-size: 14px;
  margin-top: 20px;
  width: 100%;
  max-width: 360px;
}

.register-btn {
  margin-left: 5px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.register-btn:hover {
  color: #409EFF;
  transform: translateX(3px);
}

/* Element Plus 样式覆盖 */
:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 18px 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.9);
  height: 54px;
  display: flex;
  align-items: center;
  width: 100%;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
  transform: translateY(-1px);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.25);
  border-color: #409EFF;
  transform: translateY(-1px);
}

:deep(.el-input__inner) {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
  line-height: 1.2;
}

:deep(.el-input__inner::placeholder) {
  color: #a8abb2;
  font-size: 16px;
}

:deep(.el-input__prefix) {
  color: #909399;
  font-size: 20px;
  margin-right: 8px;
}

:deep(.el-input__suffix) {
  color: #909399;
  margin-left: 8px;
}

:deep(.el-form-item) {
  width: 100%;
  margin-bottom: 30px;
}

:deep(.el-form-item__content) {
  line-height: normal;
  width: 100%;
}

:deep(.el-checkbox__label) {
  font-size: 14px;
  line-height: 1.5;
}

:deep(.el-loading-mask) {
  border-radius: 12px;
}

:deep(.el-alert) {
  border-radius: 8px;
}

:deep(.el-divider) {
  margin: 30px 0;
}

:deep(.el-divider__text) {
  background: transparent;
  padding: 0 20px;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-box {
    padding: 40px 30px;
    margin: 10px;
    border-radius: 20px;
  }
  
  .login-header h2 {
    font-size: 24px;
  }
  
  .login-header p {
    font-size: 14px;
  }
  
  .social-login {
    flex-direction: column;
  }
  
  .bg-circle {
    display: none;
  }
}

/* 暗色模式适配 */
@media (prefers-color-scheme: dark) {
  .login-box {
    background: rgba(30, 30, 30, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .login-header h2 {
    background: linear-gradient(135deg, #409EFF, #36A3F5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .login-header p {
    color: #a8abb2;
  }
  
  .register-link {
    color: #a8abb2;
  }
}
</style>