<template>
  <div class="admin-login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>
    
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <div class="logo-animation">
            <el-icon size="50" color="#F56C6C">
              <Setting />
            </el-icon>
          </div>
        </div>
        <h2>管理员登录</h2>
        <p>健康管理系统后台</p>
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
              placeholder="请输入管理员账号"
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
              placeholder="请输入管理员密码"
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
            <el-link type="primary" :underline="false" class="forgot-link">忘记密码？</el-link>
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
        
        <el-form-item>
          <div class="back-link">
            <el-link type="info" :underline="false" @click="goToUserLogin">
              <el-icon><ArrowLeft /></el-icon>
              返回用户登录
            </el-link>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loginFormRef = ref()
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入管理员账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入管理员密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return
    
    loading.value = true
    
    // 模拟管理员登录请求
    setTimeout(() => {
      if (loginForm.username === 'admin' && loginForm.password === 'admin123') {
        localStorage.setItem('adminToken', 'admin-token-' + Date.now())
        localStorage.setItem('adminUsername', loginForm.username)
        localStorage.setItem('userRole', 'admin')
        
        ElMessage.success('管理员登录成功')
        router.push('/admin')
      } else {
        ElMessage.error('管理员账号或密码错误')
      }
      loading.value = false
    }, 1000)
    
  } catch (error) {
    loading.value = false
    ElMessage.error('登录失败，请重试')
  }
}

const goToUserLogin = () => {
  router.push('/login')
}

onMounted(() => {
  setTimeout(() => {
    document.querySelector('.login-box')?.classList.add('show')
  }, 100)
})
</script>

<style scoped>
.admin-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
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
  background: rgba(255, 255, 255, 0.05);
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
  padding: 50px 40px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  width: 100%;
  max-width: 420px;
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
  animation: rotate 4s linear infinite;
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.login-header h2 {
  color: #1e293b;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #F56C6C, #E74C3C);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-header p {
  color: #64748b;
  font-size: 16px;
  font-weight: 400;
}

.login-form {
  margin-top: 30px;
}

.input-wrapper {
  position: relative;
}

.custom-input {
  width: 100%;
}

.remember-forgot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
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
  color: #F56C6C;
  transform: translateX(2px);
}

.login-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #F56C6C, #E74C3C);
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
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
  background: linear-gradient(135deg, #E74C3C, #F56C6C);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(245, 108, 108, 0.3);
}

.login-button:active {
  transform: translateY(0);
}

.back-link {
  text-align: center;
  margin-top: 20px;
}

.back-link .el-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.back-link .el-link:hover {
  transform: translateX(-4px);
}

/* Element Plus 样式覆盖 */
:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.8);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  border-color: rgba(245, 108, 108, 0.2);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 6px 16px rgba(245, 108, 108, 0.2);
  border-color: #F56C6C;
}

:deep(.el-input__inner) {
  font-size: 15px;
  color: #303133;
}

:deep(.el-input__inner::placeholder) {
  color: #a8abb2;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-checkbox__label) {
  font-size: 14px;
}

:deep(.el-loading-mask) {
  border-radius: 12px;
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
    background: linear-gradient(135deg, #F56C6C, #E74C3C);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .login-header p {
    color: #a8abb2;
  }
}
</style>
