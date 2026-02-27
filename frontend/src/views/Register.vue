<template>
  <div class="register-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
      <div class="bg-circle circle-4"></div>
    </div>
    
    <div class="register-box">
      <div class="register-header">
        <div class="logo">
          <div class="logo-animation">
            <el-icon size="50" color="#67C23A">
              <UserFilled />
            </el-icon>
          </div>
        </div>
        <h2>创建账号</h2>
        <p>加入健康管理系统，开启智能健康生活</p>
      </div>
      
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
        size="large"
      >
        <el-form-item prop="username">
          <div class="input-wrapper">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              clearable
              class="custom-input"
            />
          </div>
        </el-form-item>

        <el-form-item prop="role">
          <div class="input-wrapper">
            <el-select v-model="registerForm.role" placeholder="请选择注册身份" class="custom-input">
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </div>
        </el-form-item>

        <el-form-item v-if="registerForm.role === 'admin'" prop="admin_register_key">
          <div class="input-wrapper">
            <el-input
              v-model="registerForm.admin_register_key"
              placeholder="请输入管理员注册密钥"
              prefix-icon="Key"
              show-password
              clearable
              class="custom-input"
            />
          </div>
        </el-form-item>
        
        <el-form-item prop="email">
          <div class="input-wrapper">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱地址"
              prefix-icon="Message"
              clearable
              class="custom-input"
            />
          </div>
        </el-form-item>
        
        <el-form-item prop="password">
          <div class="input-wrapper">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              clearable
              class="custom-input"
            />
          </div>
          <div class="password-strength">
            <div class="strength-bar">
              <div 
                class="strength-fill" 
                :class="passwordStrengthClass"
                :style="{ width: passwordStrengthWidth }"
              ></div>
            </div>
            <span class="strength-text">{{ passwordStrengthText }}</span>
          </div>
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <div class="input-wrapper">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              prefix-icon="Lock"
              show-password
              clearable
              @keyup.enter="handleRegister"
              class="custom-input"
            />
          </div>
        </el-form-item>
        
        <el-form-item prop="agreement">
          <div class="agreement-wrapper">
            <el-checkbox v-model="agreeTerms" class="custom-checkbox">
              我已阅读并同意
              <el-link type="primary" :underline="false" @click="showTerms">《用户服务协议》</el-link>
              和
              <el-link type="primary" :underline="false" @click="showPrivacy">《隐私政策》</el-link>
            </el-checkbox>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="register-button"
            :loading="loading"
            :disabled="!agreeTerms"
            @click="handleRegister"
          >
            <span v-if="!loading">立即注册</span>
            <span v-else>注册中...</span>
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <div class="login-link">
            <span>已有账号？</span>
            <el-link type="primary" :underline="false" class="login-btn" @click="goToLogin">立即登录</el-link>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 服务协议对话框 -->
    <el-dialog
      v-model="termsDialogVisible"
      title="用户服务协议"
      width="600px"
      append-to-body
    >
      <div class="terms-content">
        <h3>1. 服务条款</h3>
        <p>欢迎使用健康管理系统。使用本系统即表示您同意遵守以下条款...</p>
        
        <h3>2. 用户责任</h3>
        <p>用户应对其账户下的所有活动负责，并承诺提供真实、准确的信息...</p>
        
        <h3>3. 隐私保护</h3>
        <p>我们重视用户隐私，将按照隐私政策保护您的个人信息...</p>
        
        <h3>4. 知识产权</h3>
        <p>本系统的所有内容受知识产权法保护，未经授权不得使用...</p>
      </div>
      <template #footer>
        <el-button @click="termsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 隐私政策对话框 -->
    <el-dialog
      v-model="privacyDialogVisible"
      title="隐私政策"
      width="600px"
      append-to-body
    >
      <div class="privacy-content">
        <h3>1. 信息收集</h3>
        <p>我们收集您主动提供的信息，包括但不限于用户名、邮箱、健康数据等...</p>
        
        <h3>2. 信息使用</h3>
        <p>收集的信息将用于提供更好的服务体验和个性化健康建议...</p>
        
        <h3>3. 信息保护</h3>
        <p>我们采用行业标准的安全措施保护您的个人信息...</p>
        
        <h3>4. 信息共享</h3>
        <p>未经您的同意，我们不会向第三方共享您的个人信息...</p>
      </div>
      <template #footer>
        <el-button @click="privacyDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { registerUser } from '../api/auth'

const router = useRouter()
const registerFormRef = ref()
const loading = ref(false)
const agreeTerms = ref(false)
const termsDialogVisible = ref(false)
const privacyDialogVisible = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  role: 'user',
  admin_register_key: '',
  password: '',
  confirmPassword: ''
})

// 密码强度计算
const passwordStrength = computed(() => {
  const password = registerForm.password
  if (!password) return 0
  
  let strength = 0
  
  // 长度检查
  if (password.length >= 8) strength += 1
  if (password.length >= 12) strength += 1
  
  // 复杂度检查
  if (/[a-z]/.test(password)) strength += 1
  if (/[A-Z]/.test(password)) strength += 1
  if (/[0-9]/.test(password)) strength += 1
  if (/[^a-zA-Z0-9]/.test(password)) strength += 1
  
  return Math.min(strength, 4)
})

const passwordStrengthClass = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 1) return 'weak'
  if (strength <= 2) return 'medium'
  if (strength <= 3) return 'good'
  return 'strong'
})

const passwordStrengthWidth = computed(() => {
  return `${(passwordStrength.value / 4) * 100}%`
})

const passwordStrengthText = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 1) return '弱'
  if (strength <= 2) return '中等'
  if (strength <= 3) return '良好'
  return '强'
})

const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
    return
  }

  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }

  callback()
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择注册身份', trigger: 'change' }],
  admin_register_key: [
    {
      validator: (_rule, value, callback) => {
        if (registerForm.role === 'admin' && !value) {
          callback(new Error('管理员注册必须填写密钥'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
    { 
      validator: (_rule, value, callback) => {
        if (value && passwordStrength.value < 2) {
          callback(new Error('密码强度太弱，请使用更复杂的密码'))
          return
        }
        callback()
      }, 
      trigger: 'blur' 
    }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  agreement: [
    { 
      validator: (_rule, value, callback) => {
        if (!agreeTerms.value) {
          callback(new Error('请阅读并同意服务协议和隐私政策'))
          return
        }
        callback()
      }, 
      trigger: 'change' 
    }
  ]
}

watch(
  () => registerForm.role,
  (newRole) => {
    if (newRole !== 'admin') {
      registerForm.admin_register_key = ''
    }
  }
)

const extractError = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  return fallback
}

const showTerms = () => {
  termsDialogVisible.value = true
}

const showPrivacy = () => {
  privacyDialogVisible.value = true
}

const goToLogin = () => {
  router.push('/login')
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return

    loading.value = true

    await registerUser({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      role: registerForm.role,
      admin_register_key: registerForm.role === 'admin' ? registerForm.admin_register_key : null
    })

    ElMessage.success('注册成功！正在跳转到登录页面...')
    
    // 延迟跳转，让用户看到成功消息
    setTimeout(() => {
      router.push({
        path: '/login',
        query: { username: registerForm.username, registered: 'true' }
      })
    }, 1500)
    
  } catch (error) {
    ElMessage.error(extractError(error, '注册失败，请重试'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 添加页面加载动画
  setTimeout(() => {
    document.querySelector('.register-box')?.classList.add('show')
  }, 100)
})
</script>

<style scoped>
.register-container {
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
  animation: float 8s ease-in-out infinite;
}

.circle-1 {
  width: 250px;
  height: 250px;
  top: 5%;
  left: 5%;
  animation-delay: 0s;
}

.circle-2 {
  width: 180px;
  height: 180px;
  top: 60%;
  right: 8%;
  animation-delay: 2s;
}

.circle-3 {
  width: 120px;
  height: 120px;
  bottom: 15%;
  left: 15%;
  animation-delay: 4s;
}

.circle-4 {
  width: 80px;
  height: 80px;
  top: 25%;
  right: 25%;
  animation-delay: 6s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
  }
}

.register-box {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 60px 50px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  width: 100%;
  max-width: 520px;
  position: relative;
  z-index: 10;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.register-box.show {
  opacity: 1;
  transform: translateY(0);
}

.register-header {
  text-align: center;
  margin-bottom: 35px;
}

.logo {
  margin-bottom: 20px;
}

.logo-animation {
  display: inline-block;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.register-header h2 {
  color: #2c3e50;
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #67C23A, #85CE61);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.register-header p {
  color: #7f8c8d;
  font-size: 15px;
  font-weight: 400;
  line-height: 1.5;
}

.register-form {
  margin-top: 25px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.input-wrapper {
  position: relative;
  width: 100%;
  max-width: 380px;
  margin: 0 auto;
}

.custom-input {
  width: 100%;
}

.password-strength {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 380px;
  margin-left: auto;
  margin-right: auto;
}

.strength-bar {
  flex: 1;
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.strength-fill {
  height: 100%;
  border-radius: 3px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.strength-fill.weak {
  background: linear-gradient(90deg, #f56c6c, #ff7875);
}

.strength-fill.medium {
  background: linear-gradient(90deg, #e6a23c, #ebb563);
}

.strength-fill.good {
  background: linear-gradient(90deg, #409eff, #66b1ff);
}

.strength-fill.strong {
  background: linear-gradient(90deg, #67c23a, #85ce61);
}

.strength-text {
  font-size: 13px;
  color: #909399;
  min-width: 40px;
  font-weight: 500;
  text-align: right;
}

.agreement-wrapper {
  margin: 20px 0;
  width: 100%;
  max-width: 380px;
}

.custom-checkbox {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.register-button {
  width: 100%;
  max-width: 380px;
  height: 54px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #67C23A, #85CE61);
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.register-button:hover::before {
  left: 100%;
}

.register-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #85CE61, #67C23A);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.3);
}

.register-button:active:not(:disabled) {
  transform: translateY(0);
}

.register-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  color: #7f8c8d;
  font-size: 14px;
  margin-top: 20px;
  width: 100%;
  max-width: 380px;
}

.login-btn {
  margin-left: 5px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.login-btn:hover {
  color: #67C23A;
  transform: translateX(3px);
}

/* 对话框内容样式 */
.terms-content,
.privacy-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
  line-height: 1.6;
}

.terms-content h3,
.privacy-content h3 {
  color: #303133;
  margin: 20px 0 10px 0;
  font-size: 16px;
}

.terms-content p,
.privacy-content p {
  color: #606266;
  margin-bottom: 15px;
  font-size: 14px;
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
  border-color: rgba(103, 194, 58, 0.2);
  transform: translateY(-1px);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 6px 20px rgba(103, 194, 58, 0.25);
  border-color: #67C23A;
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
  margin-bottom: 26px;
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

:deep(.el-dialog) {
  border-radius: 16px;
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px 20px;
  border-top: 1px solid #f0f0f0;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .register-box {
    padding: 40px 30px;
    margin: 10px;
    border-radius: 20px;
  }
  
  .register-header h2 {
    font-size: 22px;
  }
  
  .register-header p {
    font-size: 14px;
  }
  
  .bg-circle {
    display: none;
  }
}

/* 暗色模式适配 */
@media (prefers-color-scheme: dark) {
  .register-box {
    background: rgba(30, 30, 30, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .register-header h2 {
    background: linear-gradient(135deg, #67C23A, #85CE61);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .register-header p {
    color: #a8abb2;
  }
  
  .login-link {
    color: #a8abb2;
  }
}
</style>
