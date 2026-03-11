<template>
  <div class="dashboard-container">
    <el-container>
      <el-aside :width="sidebarCollapsed ? '72px' : '260px'" class="sidebar">
        <div class="logo-container">
          <el-icon size="30" color="#60a5fa"><Heart /></el-icon>
          <span v-show="!sidebarCollapsed" class="logo-text">健康管理系统</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          :collapse="sidebarCollapsed"
          background-color="#10233d"
          text-color="#94a3b8"
          active-text-color="#ffffff"
          router
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <template #title>首页</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/health-data">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>健康数据</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/ai-chat">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>AI 健康助手</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/knowledge-center">
            <el-icon><Reading /></el-icon>
            <template #title>健康知识中心</template>
          </el-menu-item>
          <el-menu-item index="/dashboard/profile">
            <el-icon><User /></el-icon>
            <template #title>个人中心</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-button text class="sidebar-toggle" @click="toggleSidebar">
              <el-icon size="18">
                <Fold v-if="!sidebarCollapsed" />
                <Expand v-else />
              </el-icon>
            </el-button>

            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="currentPageName">{{ currentPageName }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <div class="header-actions">
              <el-tooltip content="最近阅读" placement="bottom">
                <el-button text class="action-btn" @click="openNotifications">
                  <el-icon size="18"><Bell /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="个人设置" placement="bottom">
                <el-button text class="action-btn" @click="openSettings">
                  <el-icon size="18"><Setting /></el-icon>
                </el-button>
              </el-tooltip>
            </div>

            <el-dropdown @command="handleCommand" class="user-dropdown">
              <div class="user-info">
                <el-avatar :size="36" :src="userAvatar" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <div v-show="!sidebarCollapsed" class="user-details">
                  <span class="username">{{ username }}</span>
                  <span class="user-role">健康用户</span>
                </div>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人中心
                  </el-dropdown-item>
                  <el-dropdown-item command="settings">
                    <el-icon><Setting /></el-icon>
                    设置
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main class="main-content">
          <div class="content-wrapper">
            <router-view v-slot="{ Component }">
              <transition name="fade-slide" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </div>
        </el-main>
      </el-container>
    </el-container>

    <el-drawer v-model="notificationDrawerVisible" title="最近阅读" size="420px">
      <div v-loading="historyLoading" class="notification-drawer">
        <el-empty v-if="!historyLoading && !recentReadHistory.length" description="暂时没有阅读记录" />
        <div v-else class="notification-list">
          <div v-for="item in recentReadHistory" :key="`${item.article_id}-${item.last_read_at}`" class="notification-item">
            <div class="notification-main">
              <div class="notification-title">{{ item.article_title }}</div>
              <div class="notification-subtitle">{{ item.category }}</div>
              <div class="notification-meta">
                <span>最近阅读：{{ formatDateTime(item.last_read_at) }}</span>
                <span>阅读次数：{{ item.read_count }}</span>
              </div>
            </div>
            <el-button text type="primary" @click="openHistoryArticle(item.article_id)">查看</el-button>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '../api/knowledge'
import { clearAuthStorage, redirectToLogin } from '../utils/auth'

const router = useRouter()
const route = useRoute()
const sidebarCollapsed = ref(false)
const userAvatar = ref('')
const notificationDrawerVisible = ref(false)
const historyLoading = ref(false)
const recentReadHistory = ref([])

const username = computed(() => localStorage.getItem('username') || '用户')
const activeMenu = computed(() => route.path.startsWith('/dashboard/knowledge-center/article/') ? '/dashboard/knowledge-center' : route.path)
const currentPageName = computed(() => {
  if (route.path.startsWith('/dashboard/knowledge-center/article/')) return '文章详情'

  const routeMap = {
    '/dashboard': '首页',
    '/dashboard/health-data': '健康数据',
    '/dashboard/ai-chat': 'AI 健康助手',
    '/dashboard/knowledge-center': '健康知识中心',
    '/dashboard/profile': '个人中心'
  }
  return routeMap[route.path] || ''
})

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', { hour12: false })
}

const openNotifications = async () => {
  notificationDrawerVisible.value = true
  historyLoading.value = true
  try {
    recentReadHistory.value = await knowledgeApi.getReadHistory(12)
  } catch (error) {
    recentReadHistory.value = []
    ElMessage.error(error?.response?.data?.detail || '加载阅读记录失败')
  } finally {
    historyLoading.value = false
  }
}

const openSettings = () => {
  router.push('/dashboard/profile')
}

const openHistoryArticle = (articleId) => {
  notificationDrawerVisible.value = false
  router.push(`/dashboard/knowledge-center/article/${articleId}`)
}

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/dashboard/profile')
      break
    case 'settings':
      openSettings()
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        clearAuthStorage()
        ElMessage.success('已退出登录')
        await router.push('/login')
        redirectToLogin(false)
      } catch {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #f4f9ff 0%, #eef6ff 100%);
}

.dashboard-container :deep(.el-container) {
  height: 100%;
}

.sidebar {
  background: linear-gradient(180deg, #12243e 0%, #0d1b30 100%);
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.12);
}

.logo-container {
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-text {
  font-weight: 700;
  letter-spacing: 0.5px;
}

.sidebar-menu {
  border-right: none;
  padding-top: 10px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.header-left,
.header-right,
.header-actions,
.user-info {
  display: flex;
  align-items: center;
}

.header-left,
.header-right {
  gap: 14px;
}

.action-btn,
.sidebar-toggle {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: #f8fbff;
  color: #334155;
}

.action-btn:hover,
.sidebar-toggle:hover {
  background: #e8f1ff;
  color: #2563eb;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  gap: 10px;
  padding: 8px 12px;
  border-radius: 16px;
  background: #f8fbff;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.username {
  color: #0f172a;
  font-weight: 600;
}

.user-role {
  color: #64748b;
  font-size: 12px;
}

.dropdown-icon {
  color: #64748b;
}

.main-content {
  padding: 0;
}

.content-wrapper {
  height: 100%;
  overflow: auto;
  padding: 20px;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid #e5edf7;
  background: #f8fbff;
}

.notification-title {
  font-weight: 600;
  color: #0f172a;
}

.notification-subtitle {
  margin-top: 4px;
  color: #2563eb;
  font-size: 13px;
}

.notification-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 900px) {
  .header {
    padding: 0 16px;
  }

  .content-wrapper {
    padding: 16px;
  }

  .user-details,
  .logo-text {
    display: none;
  }
}
</style>
