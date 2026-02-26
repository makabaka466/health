<template>
  <div class="auth-page">
    <section class="auth-card">
      <header>
        <h1>健康管理系统登录</h1>
        <p>请选择身份并登录</p>
      </header>

      <el-form ref="loginRef" :model="loginForm" :rules="loginRules" label-position="top" @keyup.enter="handleLogin">
        <el-form-item label="登录身份">
          <el-radio-group v-model="identity" class="identity-switch">
            <el-radio-button label="user">用户登录</el-radio-button>
            <el-radio-button label="admin">管理员登录</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" clearable />
        </el-form-item>

        <el-button type="primary" class="submit-btn" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>

      <div class="quick-users">
        <p>示例账号（点击自动填充）</p>
        <div class="user-grid">
          <button type="button" @click="fillAccount('admin', 'admin123', 'admin')">管理员：admin</button>
          <button type="button" @click="fillAccount('xiaoming', '123456', 'user')">用户：xiaoming</button>
          <button type="button" @click="fillAccount('xiaohong', '123456', 'user')">用户：xiaohong</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLoginUser, loginUser } from '../api/auth'

const router = useRouter()

const identity = ref('user')
const loading = ref(false)
const loginRef = ref()

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const extractError = (error, fallback) => {
  // 统一提取后端返回错误，优先展示服务端 detail 信息
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  return fallback
}

const saveSession = (payload) => {
  // 管理员与普通用户写入不同的本地会话键，配合路由守卫区分跳转
  if (identity.value === 'admin') {
    localStorage.setItem('adminToken', payload.access_token)
    localStorage.setItem('adminUsername', payload.username || loginForm.username)
    localStorage.setItem('userRole', payload.role || 'admin')
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/admin')
    return
  }

  localStorage.setItem('token', payload.access_token)
  localStorage.setItem('username', payload.username || loginForm.username)
  localStorage.setItem('userRole', payload.role || 'user')
  localStorage.removeItem('adminToken')
  localStorage.removeItem('adminUsername')
  router.push('/dashboard')
}

const fillAccount = (username, password, role) => {
  // 一键填充示例账号，便于演示和联调
  identity.value = role
  loginForm.username = username
  loginForm.password = password
}

const handleLogin = async () => {
  // 根据身份选择不同登录接口：user -> /auth/login, admin -> /auth/admin/login
  if (!loginRef.value) return
  await loginRef.value.validate()

  loading.value = true
  try {
    const result = identity.value === 'admin'
      ? await adminLoginUser(loginForm)
      : await loginUser(loginForm)
    saveSession(result)
    ElMessage.success(identity.value === 'admin' ? '管理员登录成功' : '用户登录成功')
  } catch (error) {
    ElMessage.error(extractError(error, '登录失败，请检查账号或密码'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 20px;
}

.auth-card {
  width: min(100%, 440px);
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
}

header h1 {
  font-size: 24px;
  margin-bottom: 6px;
}

header p {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 18px;
}

.identity-switch {
  width: 100%;
}

:deep(.identity-switch .el-radio-button) {
  width: 50%;
}

:deep(.identity-switch .el-radio-button__inner) {
  width: 100%;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
}

.quick-users {
  margin-top: 16px;
  border-top: 1px dashed #e5e7eb;
  padding-top: 12px;
}

.quick-users p {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.user-grid {
  display: grid;
  gap: 8px;
}

.user-grid button {
  text-align: left;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
}

.user-grid button:hover {
  border-color: #93c5fd;
  background: #eff6ff;
}
</style>
