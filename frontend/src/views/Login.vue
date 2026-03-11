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
            <el-button class="social-btn wechat-btn" :loading="socialLoading === 'wechat'" @click="handleSocialLogin('wechat')">
              <el-icon><ChatDotRound /></el-icon>
              微信登录
            </el-button>
            <el-button class="social-btn alipay-btn" :loading="socialLoading === 'alipay'" @click="handleSocialLogin('alipay')">
              <el-icon><ChatLineSquare /></el-icon>
              支付宝登录
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

    <el-dialog
      v-model="socialProfileVisible"
      title="首次第三方登录 - 完善资料"
      width="460px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-alert
        type="info"
        show-icon
        :closable="false"
        class="social-alert"
        :title="`欢迎使用${pendingProviderName}登录`"
        :description="`首次登录请补全账号信息，后续可用${pendingProviderName}一键登录，也可用账号密码登录。`"
      />

      <el-form ref="socialFormRef" :model="socialProfileForm" :rules="socialRules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="socialProfileForm.username" clearable />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="socialProfileForm.email" clearable />
        </el-form-item>
        <el-form-item label="登录密码" prop="password">
          <el-input v-model="socialProfileForm.password" type="password" show-password clearable />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="socialProfileForm.confirmPassword" type="password" show-password clearable />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="socialProfileVisible = false">取消</el-button>
        <el-button type="primary" :loading="socialCompleteLoading" @click="handleSocialComplete">完成并登录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginUser, socialCompleteProfile, socialLoginInit } from '../api/auth'

const router = useRouter()
const route = useRoute()

const loginFormRef = ref()
const forgotFormRef = ref()
const socialFormRef = ref()

const loading = ref(false)
const forgotLoading = ref(false)
const socialLoading = ref('')
const socialCompleteLoading = ref(false)

const rememberMe = ref(false)
const forgotPasswordVisible = ref(false)
const socialProfileVisible = ref(false)
const socialTicket = ref('')
const pendingProvider = ref('')

const queryRegistered = computed(() => route.query.registered === 'true')
const queryUsername = computed(() => route.query.username || '')
const pendingProviderName = computed(() => (pendingProvider.value === 'wechat' ? '微信' : '支付宝'))

const loginForm = reactive({
  username: queryUsername.value || '',
  password: ''
})

const forgotForm = reactive({
  email: ''
})

const socialProfileForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
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

const socialRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    {
      validator: (_rule, value, callback) => {
        if (!value) return callback(new Error('请再次输入密码'))
        if (value !== socialProfileForm.password) return callback(new Error('两次输入的密码不一致'))
        callback()
      },
      trigger: 'blur'
    }
  ]
}

const extractError = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  return fallback
}

const persistLogin = (payload, fallbackUsername = '') => {
  const role = payload.role || 'user'
  localStorage.setItem('userRole', role)
  if (role === 'admin') {
    localStorage.setItem('adminToken', payload.access_token)
    localStorage.setItem('adminUsername', payload.username || fallbackUsername)
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  } else {
    localStorage.setItem('token', payload.access_token)
    localStorage.setItem('username', payload.username || fallbackUsername)
    localStorage.removeItem('adminToken')
    localStorage.removeItem('adminUsername')
  }
  router.push(role === 'admin' ? '/admin' : '/dashboard')
}

const goToRegister = () => router.push('/register')

const handleForgotPassword = () => {
  forgotPasswordVisible.value = true
}

const handleSendResetEmail = async () => {
  if (!forgotFormRef.value) return
  try {
    const valid = await forgotFormRef.value.validate()
    if (!valid) return
    forgotLoading.value = true
    await new Promise((resolve) => setTimeout(resolve, 1200))
    ElMessage.success('重置密码邮件已发送，请查收邮箱')
    forgotPasswordVisible.value = false
    forgotFormRef.value.resetFields()
  } catch {
    ElMessage.error('发送失败，请重试')
  } finally {
    forgotLoading.value = false
  }
}

const handleSocialLogin = async (platform) => {
  try {
    socialLoading.value = platform
    const codeKey = `social_mock_code_${platform}`
    let mockAuthCode = localStorage.getItem(codeKey)
    if (!mockAuthCode) {
      mockAuthCode = `${platform}_${Math.random().toString(36).slice(2, 12)}`
      localStorage.setItem(codeKey, mockAuthCode)
    }

    const data = await socialLoginInit({
      provider: platform,
      auth_code: mockAuthCode,
    })

    if (data.need_profile_completion) {
      socialTicket.value = data.social_ticket || ''
      pendingProvider.value = data.social_provider || platform
      socialProfileForm.username = data.suggested_username || ''
      socialProfileForm.email = ''
      socialProfileForm.password = ''
      socialProfileForm.confirmPassword = ''
      socialProfileVisible.value = true
      return
    }

    persistLogin(data, data.username)
    ElMessage.success(`${platform === 'wechat' ? '微信' : '支付宝'}登录成功`)
  } catch (error) {
    ElMessage.error(extractError(error, '第三方登录失败，请重试'))
  } finally {
    socialLoading.value = ''
  }
}

const handleSocialComplete = async () => {
  if (!socialFormRef.value) return
  const valid = await socialFormRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    socialCompleteLoading.value = true
    const payload = await socialCompleteProfile({
      social_ticket: socialTicket.value,
      username: socialProfileForm.username,
      email: socialProfileForm.email,
      password: socialProfileForm.password,
    })
    socialProfileVisible.value = false
    persistLogin(payload, socialProfileForm.username)
    ElMessage.success('资料完善成功，已为您登录')
  } catch (error) {
    ElMessage.error(extractError(error, '资料提交失败，请重试'))
  } finally {
    socialCompleteLoading.value = false
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return
    loading.value = true
    const payload = await loginUser(loginForm)
    persistLogin(payload, loginForm.username)
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error(extractError(error, '登录失败，请重试'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
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
  background: linear-gradient(135deg, #eef7ff 0%, #dceeff 100%);
}

.login-box {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 56px 46px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 480px;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.5s ease;
}

.login-box.show {
  opacity: 1;
  transform: translateY(0);
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-form {
  margin-top: 20px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-form-item__content) {
  width: 100%;
}

.input-wrapper {
  width: 100%;
}

.custom-input {
  width: 100%;
}

.custom-input :deep(.el-input__wrapper) {
  min-height: 46px;
  border-radius: 12px;
  padding: 0 12px;
  box-shadow: 0 0 0 1px #d9e6f5 inset;
  transition: box-shadow 0.2s ease;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset;
}

.remember-forgot {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 22px;
}

.login-button {
  width: 100%;
  height: 52px;
  border-radius: 12px;
  font-weight: 600;
}

.social-login {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
}

.social-btn {
  height: 46px;
  border-radius: 12px;
}

.wechat-btn:hover {
  color: #67c23a;
  border-color: #67c23a;
}

.alipay-btn:hover {
  color: #409eff;
  border-color: #409eff;
}

.register-link {
  text-align: center;
  width: 100%;
  color: #5d6b82;
}

.register-btn {
  margin-left: 5px;
}

.social-alert {
  margin-bottom: 16px;
}

@media (max-width: 480px) {
  .login-box {
    padding: 34px 22px;
  }

  .social-login {
    grid-template-columns: 1fr;
  }
}
</style>