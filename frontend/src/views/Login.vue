<template>
  <div class="login-container">
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
          <el-button type="primary" class="login-button" :loading="loading" @click="handleLogin">
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

    <el-dialog v-model="forgotPasswordVisible" title="找回密码" width="400px" append-to-body>
      <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules" label-position="top">
        <el-form-item label="邮箱地址" prop="email">
          <el-input v-model="forgotForm.email" placeholder="请输入注册时使用的邮箱" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="forgotPasswordVisible = false">取消</el-button>
          <el-button type="primary" :loading="forgotLoading" @click="handleSendResetEmail">发送重置邮件</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="socialProfileVisible" title="首次第三方登录" width="460px" append-to-body>
      <el-form ref="socialFormRef" :model="socialProfileForm" :rules="socialProfileRules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="socialProfileForm.username" placeholder="请设置用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="socialProfileForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="socialProfileForm.password" type="password" show-password placeholder="请设置登录密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="socialProfileForm.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="socialProfileVisible = false">取消</el-button>
          <el-button type="primary" :loading="socialCompleteLoading" @click="handleSocialComplete">完成并登录</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginUser, socialCompleteProfile, socialLoginInit } from '../api/auth'

const router = useRouter()
const route = useRoute()
const loginFormRef = ref()
const forgotFormRef = ref()
const socialFormRef = ref()
const loading = ref(false)
const forgotLoading = ref(false)
const rememberMe = ref(false)
const forgotPasswordVisible = ref(false)
const socialLoading = ref('')
const socialProfileVisible = ref(false)
const socialCompleteLoading = ref(false)
const socialTicket = ref('')

const queryRegistered = computed(() => route.query.registered === 'true')
const queryUsername = computed(() => route.query.username || '')

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

const socialProfileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
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
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #ecf5ff 0%, #dcebff 50%, #f7fbff 100%);
}

.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.12), rgba(103, 194, 58, 0.08));
  animation: float 8s ease-in-out infinite;
}

.circle-1 { width: 300px; height: 300px; top: -120px; left: -80px; }
.circle-2 { width: 220px; height: 220px; bottom: -100px; right: -40px; animation-delay: 2s; }
.circle-3 { width: 160px; height: 160px; top: 18%; right: 16%; animation-delay: 4s; }

.bg-particles { position: absolute; inset: 0; }
.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(64, 158, 255, 0.35);
  animation: particle-float 6s linear infinite;
  animation-delay: var(--delay);
}
.particle:nth-child(odd) { left: 12%; top: 18%; }
.particle:nth-child(even) { right: 18%; bottom: 22%; }

.login-box {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 50px 42px;
  box-shadow: 0 20px 50px rgba(64, 158, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.85);
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

.logo {
  margin-bottom: 20px;
}

.logo-animation {
  width: 86px;
  height: 86px;
  margin: 0 auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.12), rgba(54, 163, 245, 0.18));
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.18);
}

.login-header h2 {
  margin: 0 0 8px;
  font-size: 30px;
  color: #303133;
}

.login-header p {
  margin: 0;
  color: #7f8c8d;
  font-size: 15px;
}

.quick-login-tip {
  margin-bottom: 20px;
}

.login-form {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.input-wrapper,
.remember-forgot,
.register-link,
.social-login {
  width: 100%;
  max-width: 360px;
}

.remember-forgot {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.custom-checkbox {
  color: #606266;
}

.forgot-link {
  font-weight: 500;
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
  box-shadow: 0 10px 22px rgba(64, 158, 255, 0.24);
}

.divider {
  margin: 24px 0;
}

.divider-text {
  color: #909399;
  font-size: 14px;
}

.social-login {
  display: flex;
  gap: 12px;
  margin: 0 auto;
}

.social-btn {
  flex: 1;
  height: 48px;
  border-radius: 10px;
  border: 1px solid #dcdfe6;
  background: white;
  color: #606266;
}

.wechat-btn:hover {
  border-color: #67c23a;
  color: #67c23a;
}

.alipay-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.register-link {
  text-align: center;
  color: #7f8c8d;
  font-size: 14px;
  margin-top: 16px;
}

.register-btn {
  margin-left: 5px;
  font-weight: 600;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 18px 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.9);
  height: 54px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.25);
  border-color: #409EFF;
}

:deep(.el-form-item) {
  width: 100%;
  margin-bottom: 26px;
}

:deep(.el-form-item__content) {
  width: 100%;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-18px); }
}

@keyframes particle-float {
  0% { transform: translateY(0); opacity: 0; }
  10%, 90% { opacity: 1; }
  100% { transform: translateY(-80px); opacity: 0; }
}

@media (max-width: 480px) {
  .login-box {
    padding: 40px 26px;
    margin: 10px;
    border-radius: 20px;
  }

  .social-login {
    flex-direction: column;
  }

  .bg-circle {
    display: none;
  }
}
</style>
