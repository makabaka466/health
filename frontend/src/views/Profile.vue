<template>
  <div class="profile-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#409EFF">
            <User />
          </el-icon>
        </div>
        <div class="header-text">
          <h1>个人中心</h1>
          <p>管理您的个人信息和系统设置</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button v-if="needsPrivateKeyUnlock" class="save-btn" @click="unlockProfile">
          <el-icon><Lock /></el-icon>
          解锁私密资料
        </el-button>
        <el-button type="primary" class="save-btn" :loading="saving" @click="handleSave">
          <el-icon><Check /></el-icon>
          保存更改
        </el-button>
      </div>
    </div>
    
    <div class="content-section">
      <el-row :gutter="24">
        <el-col :span="8">
          <el-card class="profile-card" shadow="hover">
            <div class="profile-avatar-section">
              <div class="avatar-container">
                <el-avatar :size="80" :src="userAvatar" class="user-avatar">
                  <el-icon size="40"><User /></el-icon>
                </el-avatar>
                <el-button type="primary" size="small" class="change-avatar-btn">
                  更换头像
                </el-button>
              </div>
              <div class="user-info">
                <h2>{{ profileData.username || '用户' }}</h2>
                <p class="user-role">{{ roleText }}</p>
                <p class="user-email">{{ profileData.email || '-' }}</p>
                <p class="user-email">钱包地址：{{ walletAddress || '-' }}</p>
              </div>
            </div>
          </el-card>
          
          <el-card class="stats-card" shadow="hover">
            <div class="card-header">
              <h3>账户统计</h3>
            </div>
            <div class="stats-list">
              <div class="stat-item">
                <div class="stat-icon">
                  <el-icon size="16" color="#409EFF"><Calendar /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">注册时间</span>
                  <span class="stat-value">{{ formatDate(profileData.created_at, true) }}</span>
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-icon">
                  <el-icon size="16" color="#67C23A"><TrendCharts /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">健康记录</span>
                  <span class="stat-value">{{ stats.healthRecords }} 条</span>
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-icon">
                  <el-icon size="16" color="#E6A23C"><ChatDotRound /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">AI咨询</span>
                  <span class="stat-value">{{ stats.aiConsultations }} 次</span>
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-icon">
                  <el-icon size="16" color="#F56C6C"><Bell /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">提醒事项</span>
                  <span class="stat-value">{{ stats.reminders }} 个</span>
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="private-key-card" shadow="hover">
            <div class="card-header">
              <h3>私钥查看</h3>
            </div>
            <p class="private-key-tip">点击查看时需验证登录密码，请妥善保管私钥。</p>
            <el-button type="warning" plain :loading="revealingPrivateKey" @click="handleRevealPrivateKey">
              查看私钥
            </el-button>
            <el-input
              v-if="privateKeyText"
              v-model="privateKeyText"
              type="textarea"
              :rows="2"
              readonly
              class="private-key-input"
            />
            <el-button v-if="privateKeyText" text @click="copyPrivateKey">复制私钥</el-button>
          </el-card>
        </el-col>
        
        <el-col :span="16">
          <el-card class="form-card" shadow="hover">
            <div class="card-header">
              <h3>基本信息</h3>
            </div>
            <el-form :model="userForm" label-width="100px" class="profile-form">
              <el-form-item label="用户名">
                <el-input v-model="userForm.username" disabled />
              </el-form-item>
              
              <el-form-item label="真实姓名">
                <el-input v-model="userForm.realName" placeholder="请输入真实姓名" />
              </el-form-item>
              
              <el-form-item label="邮箱">
                <el-input v-model="userForm.email" placeholder="请输入邮箱地址" />
              </el-form-item>
              
              <el-form-item label="手机号">
                <el-input v-model="userForm.phone" placeholder="请输入手机号" />
              </el-form-item>
              
              <el-form-item label="性别">
                <el-radio-group v-model="userForm.gender">
                  <el-radio label="male">男</el-radio>
                  <el-radio label="female">女</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="生日">
                <el-date-picker
                  v-model="userForm.birthday"
                  type="date"
                  placeholder="选择生日"
                  style="width: 100%"
                />
              </el-form-item>
              
              <el-form-item label="个人简介">
                <el-input
                  v-model="userForm.bio"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入个人简介"
                />
              </el-form-item>

              <el-form-item label="资料可见性">
                <el-switch
                  v-model="profileIsPublic"
                  active-text="公开（他人可查看）"
                  inactive-text="私密（需私钥）"
                />
              </el-form-item>
            </el-form>
          </el-card>
          
          <el-card class="settings-card" shadow="hover" style="margin-top: 24px;">
            <div class="card-header">
              <h3>通知设置</h3>
            </div>
            <div class="settings-list">
              <div class="setting-item">
                <div class="setting-info">
                  <h4>健康提醒</h4>
                  <p>接收健康数据记录和用药提醒</p>
                </div>
                <el-switch v-model="settings.healthReminder" />
              </div>
              
              <div class="setting-item">
                <div class="setting-info">
                  <h4>AI咨询回复</h4>
                  <p>AI助手回复时通知我</p>
                </div>
                <el-switch v-model="settings.aiNotification" />
              </div>
              
              <div class="setting-item">
                <div class="setting-info">
                  <h4>系统更新</h4>
                  <p>系统功能更新和维护通知</p>
                </div>
                <el-switch v-model="settings.systemUpdate" />
              </div>
              
              <div class="setting-item">
                <div class="setting-info">
                  <h4>邮件通知</h4>
                  <p>通过邮件接收重要通知</p>
                </div>
                <el-switch v-model="settings.emailNotification" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCurrentUserProfile, getMyProfileData, revealMyPrivateKey, upsertMyProfileData } from '../api/auth'
import { healthApi } from '../api/health'
import { aiApi } from '../api/ai'

const userAvatar = ref('')
const profileData = ref({
  username: '',
  email: '',
  role: 'user',
  created_at: null
})

const stats = ref({
  healthRecords: 0,
  aiConsultations: 0,
  reminders: 0
})

const saving = ref(false)
const walletAddress = ref('')
const profileIsPublic = ref(false)
const needsPrivateKeyUnlock = ref(false)
const privateKeyText = ref('')
const revealingPrivateKey = ref(false)

const roleText = computed(() => (profileData.value.role === 'admin' ? '管理员' : '普通用户'))

const userForm = ref({
  username: '',
  realName: '',
  email: '',
  phone: '',
  gender: 'male',
  birthday: '',
  bio: ''
})

const settings = ref({
  healthReminder: true,
  aiNotification: true,
  systemUpdate: false,
  emailNotification: true
})

const toDateInputValue = (value) => {
  if (!value) return ''
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return value.toISOString().slice(0, 10)
  }
  return String(value).slice(0, 10)
}

const handleRevealPrivateKey = async () => {
  try {
    const promptResult = await ElMessageBox.prompt('请输入当前登录密码后查看私钥', '查看私钥', {
      inputType: 'password',
      inputPlaceholder: '请输入登录密码',
      confirmButtonText: '查看',
      cancelButtonText: '取消'
    })

    revealingPrivateKey.value = true
    const result = await revealMyPrivateKey(promptResult.value)
    privateKeyText.value = result?.private_key || ''
    ElMessage.success('私钥已显示，请注意安全')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error.response?.data?.detail || error.message || '查看私钥失败')
  } finally {
    revealingPrivateKey.value = false
  }
}

const copyPrivateKey = async () => {
  if (!privateKeyText.value) return
  try {
    await navigator.clipboard.writeText(privateKeyText.value)
    ElMessage.success('私钥已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

const normalizeSettings = (value = {}) => ({
  healthReminder: value.healthReminder ?? true,
  aiNotification: value.aiNotification ?? true,
  systemUpdate: value.systemUpdate ?? false,
  emailNotification: value.emailNotification ?? true
})

const applyProfilePayload = (rawProfileData) => {
  if (!rawProfileData) return

  try {
    const parsed = JSON.parse(rawProfileData)
    const basic = parsed?.basic || {}
    userForm.value.realName = basic.realName || ''
    userForm.value.phone = basic.phone || ''
    userForm.value.gender = basic.gender || 'male'
    userForm.value.birthday = toDateInputValue(basic.birthday)
    userForm.value.bio = basic.bio || ''
    settings.value = normalizeSettings(parsed?.settings)
  } catch {
    userForm.value.bio = rawProfileData
  }
}

const buildProfilePayload = () => {
  const payload = {
    basic: {
      realName: userForm.value.realName || '',
      phone: userForm.value.phone || '',
      gender: userForm.value.gender || 'male',
      birthday: toDateInputValue(userForm.value.birthday),
      bio: userForm.value.bio || ''
    },
    settings: normalizeSettings(settings.value)
  }

  return JSON.stringify(payload)
}

const formatDate = (value, dateOnly = false) => {
  if (!value) return '-'
  const date = new Date(value)
  return dateOnly ? date.toLocaleDateString('zh-CN') : date.toLocaleString('zh-CN')
}

const loadProfile = async () => {
  try {
    const user = await getCurrentUserProfile()
    profileData.value = user
    userForm.value.username = user.username || ''
    userForm.value.email = user.email || ''

    const profile = await getMyProfileData()
    profileIsPublic.value = !!profile?.profile_is_public
    walletAddress.value = profile?.wallet_address || ''
    needsPrivateKeyUnlock.value = false
    applyProfilePayload(profile?.profile_data)
  } catch (error) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.includes('private_key')) {
      needsPrivateKeyUnlock.value = true
      ElMessage.warning('当前资料是私密的，请先解锁后查看详情')
      return
    }
    ElMessage.error(detail || '加载个人信息失败')
  }
}

const unlockProfile = async () => {
  try {
    const { value: privateKey } = await ElMessageBox.prompt('请输入注册时保存的私钥以解锁资料', '解锁私密资料', {
      inputType: 'password',
      inputPlaceholder: '0x 开头私钥',
      confirmButtonText: '解锁',
      cancelButtonText: '取消'
    })

    const profile = await getMyProfileData(privateKey)
    profileIsPublic.value = !!profile?.profile_is_public
    walletAddress.value = profile?.wallet_address || ''
    needsPrivateKeyUnlock.value = false
    applyProfilePayload(profile?.profile_data)
    ElMessage.success('资料已解锁')
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.response?.data?.detail || error.message || '解锁失败')
  }
}

const handleSave = async () => {
  try {
    saving.value = true
    let response
    try {
      response = await upsertMyProfileData({
        profile_data: buildProfilePayload(),
        is_public: profileIsPublic.value
      })
    } catch (error) {
      const detail = error?.response?.data?.detail
      if (typeof detail === 'string' && detail.includes('private_key')) {
        const promptResult = await ElMessageBox.prompt('当前数据需原始私钥，请输入后继续保存', '验证身份', {
          inputType: 'password',
          inputPlaceholder: '0x 开头私钥',
          confirmButtonText: '保存',
          cancelButtonText: '取消'
        })

        response = await upsertMyProfileData({
          profile_data: buildProfilePayload(),
          private_key: promptResult.value,
          is_public: profileIsPublic.value
        })
      } else {
        throw error
      }
    }

    walletAddress.value = response?.wallet_address || walletAddress.value
    profileIsPublic.value = !!response?.profile_is_public
    needsPrivateKeyUnlock.value = false
    ElMessage.success('个人中心已保存')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error.response?.data?.detail || error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const loadStats = async () => {
  try {
    const [summary, chatHistory] = await Promise.all([
      healthApi.getSummary(),
      aiApi.getChatHistory()
    ])

    stats.value.healthRecords = summary?.total_records || 0
    stats.value.aiConsultations = Array.isArray(chatHistory) ? chatHistory.length : 0
    stats.value.reminders = summary?.records_this_month || 0
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载账户统计失败')
  }
}

onMounted(() => {
  loadProfile()
  loadStats()
})
</script>

<style scoped>
.profile-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #5ea8ff 0%, #7fc2ff 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 14px 28px rgba(64, 158, 255, 0.22);
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

.save-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.save-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.content-section {
  margin-bottom: 32px;
}

.profile-card, .form-card, .settings-card, .stats-card {
  border-radius: 16px;
  border: 1px solid #e8f2ff;
  margin-bottom: 24px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.private-key-card {
  border-radius: 16px;
  border: 1px solid #ffe4bf;
  margin-bottom: 0;
  box-shadow: 0 10px 24px rgba(245, 158, 11, 0.12);
}

.private-key-tip {
  color: #92400e;
  font-size: 13px;
  line-height: 1.6;
  margin: 0 0 12px;
}

.private-key-input {
  margin-top: 12px;
}

.profile-avatar-section {
  text-align: center;
  padding: 20px;
  background: linear-gradient(180deg, #f4f9ff 0%, #ffffff 100%);
  border-radius: 12px;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.user-avatar {
  border: 4px solid #ffffff;
  box-shadow: 0 8px 18px rgba(64, 158, 255, 0.2);
}

.change-avatar-btn {
  border-radius: 20px;
  padding: 6px 16px;
  box-shadow: 0 6px 14px rgba(64, 158, 255, 0.2);
}

.user-info {
  margin-top: 16px;
}

.user-info h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.user-role {
  font-size: 14px;
  color: #409EFF;
  font-weight: 500;
  margin-bottom: 4px;
}

.user-email {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.card-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fbff;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: #eef6ff;
  transform: translateX(4px);
}

.stat-icon {
  width: 32px;
  height: 32px;
  background: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.profile-form {
  padding: 20px;
}

.settings-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fbff;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.setting-item:hover {
  background: #eef6ff;
}

.setting-info {
  flex: 1;
}

.setting-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.setting-info p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .content-section .el-col:first-child {
    margin-bottom: 24px;
  }
  
  .content-section .el-col {
    width: 100%;
  }
}
</style>
