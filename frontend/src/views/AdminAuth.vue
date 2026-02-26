<template>
  <div class="admin-auth-page">
    <section class="admin-auth-card">
      <header>
        <p class="kicker">ADMIN CONSOLE</p>
        <h1>管理员登录</h1>
        <p>请输入管理员账号后进入系统后台。</p>
      </header>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="handleLogin">
        <el-form-item label="管理员账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>

        <el-button type="primary" class="submit-btn" :loading="loading" @click="handleLogin">登录后台</el-button>
        <el-button text class="back-btn" @click="router.push('/login')">返回用户登录</el-button>
      </el-form>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLoginUser } from '../api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const extractError = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  return fallback
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate()

  loading.value = true
  try {
    const result = await adminLoginUser(form)
    localStorage.setItem('adminToken', result.access_token)
    localStorage.setItem('adminUsername', result.username || form.username)
    localStorage.setItem('userRole', result.role || 'admin')
    localStorage.removeItem('token')
    localStorage.removeItem('username')

    ElMessage.success('管理员登录成功')
    router.push('/admin')
  } catch (error) {
    ElMessage.error(extractError(error, '管理员登录失败'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: radial-gradient(circle at 10% 10%, #ffd6c6 0, transparent 30%),
    radial-gradient(circle at 90% 0, #d4e4ff 0, transparent 30%),
    linear-gradient(135deg, #f7f8fc 0%, #edf0f7 100%);
}

.admin-auth-card {
  width: min(100%, 460px);
  padding: 32px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 16px 40px rgba(22, 36, 66, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.75);
}

.kicker {
  font-size: 12px;
  letter-spacing: 1px;
  color: #7a8498;
  margin-bottom: 8px;
}

h1 {
  font-size: 28px;
  margin-bottom: 8px;
  color: #1f2a44;
}

header > p:last-child {
  color: #667085;
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
}

.back-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
