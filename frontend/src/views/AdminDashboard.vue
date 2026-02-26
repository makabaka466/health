<template>
  <div class="admin-dashboard-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="sidebarCollapsed ? '64px' : '260px'" class="sidebar">
        <div class="logo-container">
          <div class="logo-wrapper">
            <el-icon size="32" color="#F56C6C" class="logo-icon">
              <Setting />
            </el-icon>
            <transition name="fade">
              <span v-show="!sidebarCollapsed" class="logo-text">管理后台</span>
            </transition>
          </div>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          :collapse="sidebarCollapsed"
          background-color="#1e293b"
          text-color="#94a3b8"
          active-text-color="#ffffff"
          router
        >
          <el-menu-item index="/admin">
            <el-icon><Monitor /></el-icon>
            <template #title>
              <span class="menu-title">控制台</span>
            </template>
          </el-menu-item>
          
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <template #title>
              <span class="menu-title">用户管理</span>
            </template>
          </el-menu-item>
          
          <el-menu-item index="/admin/health-data">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>
              <span class="menu-title">健康数据</span>
            </template>
          </el-menu-item>
          
          <el-menu-item index="/admin/ai-chat">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>
              <span class="menu-title">AI管理</span>
            </template>
          </el-menu-item>

          <el-menu-item index="/admin/articles">
            <el-icon><Reading /></el-icon>
            <template #title>
              <span class="menu-title">文章管理</span>
            </template>
          </el-menu-item>
          
          <el-menu-item index="/admin/settings">
            <el-icon><Setting /></el-icon>
            <template #title>
              <span class="menu-title">系统设置</span>
            </template>
          </el-menu-item>
          
          <el-menu-item index="/admin/logs">
            <el-icon><Document /></el-icon>
            <template #title>
              <span class="menu-title">系统日志</span>
            </template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-button
              type="text"
              @click="toggleSidebar"
              class="sidebar-toggle"
            >
              <el-icon size="20" class="toggle-icon">
                <Fold v-if="!sidebarCollapsed" />
                <Expand v-else />
              </el-icon>
            </el-button>
            
            <div class="breadcrumb">
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: '/admin' }">控制台</el-breadcrumb-item>
                <el-breadcrumb-item v-if="currentPageName">{{ currentPageName }}</el-breadcrumb-item>
              </el-breadcrumb>
            </div>
          </div>
          
          <div class="header-right">
            <div class="header-actions">
              <el-button type="text" class="action-btn">
                <el-icon size="18"><Bell /></el-icon>
              </el-button>
              <el-button type="text" class="action-btn">
                <el-icon size="18"><Setting /></el-icon>
              </el-button>
            </div>
            
            <el-dropdown @command="handleCommand" class="user-dropdown">
              <div class="user-info">
                <el-avatar :size="36" :src="userAvatar" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <transition name="fade">
                  <div v-show="!sidebarCollapsed" class="user-details">
                    <span class="username">{{ username }}</span>
                    <span class="user-role">超级管理员</span>
                  </div>
                </transition>
                <el-icon class="dropdown-icon">
                  <ArrowDown />
                </el-icon>
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
                  <el-dropdown-item command="userLogin">
                    <el-icon><SwitchButton /></el-icon>
                    切换到用户端
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
        
        <!-- 主要内容 -->
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const sidebarCollapsed = ref(false)

const username = computed(() => localStorage.getItem('adminUsername') || '管理员')
const userAvatar = ref('')
const activeMenu = computed(() => route.path)

const currentPageName = computed(() => {
  const routeMap = {
    '/admin': '控制台',
    '/admin/users': '用户管理',
    '/admin/health-data': '健康数据',
    '/admin/ai-chat': 'AI管理',
    '/admin/articles': '文章管理',
    '/admin/settings': '系统设置',
    '/admin/logs': '系统日志'
  }
  return routeMap[route.path] || ''
})

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人中心功能开发中...')
      break
    case 'settings':
      router.push('/admin/settings')
      break
    case 'userLogin':
      try {
        await ElMessageBox.confirm('确定要切换到用户端吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        })
        localStorage.removeItem('adminToken')
        localStorage.removeItem('adminUsername')
        localStorage.removeItem('userRole')
        ElMessage.success('已切换到用户端')
        router.push('/login')
      } catch {
        // 用户取消
      }
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        localStorage.removeItem('adminToken')
        localStorage.removeItem('adminUsername')
        localStorage.removeItem('userRole')
        ElMessage.success('已退出登录')
        router.push('/admin/login')
      } catch {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped>
.admin-dashboard-container {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #f3f7fc 0%, #eef4fb 100%);
}

.admin-dashboard-container :deep(.el-container) {
  height: 100%;
}

.sidebar {
  background: linear-gradient(180deg, #1f2f46 0%, #16283e 100%);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.1);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 100;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.sidebar::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(255, 255, 255, 0.1), transparent);
}

.logo-container {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.logo-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.logo-icon {
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
}

.sidebar-menu {
  border: none;
  padding: 20px 12px;
  flex: 1;
  overflow-y: auto;
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 0;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.sidebar-menu .el-menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: #F56C6C;
  border-radius: 0 2px 2px 0;
  transition: height 0.3s ease;
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(245, 108, 108, 0.1);
  color: #ffffff;
  transform: translateX(4px);
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.2), rgba(245, 108, 108, 0.1));
  color: #ffffff;
}

.sidebar-menu .el-menu-item.is-active::before {
  height: 24px;
}

.menu-title {
  font-weight: 500;
  margin-left: 8px;
}

.header {
  background: linear-gradient(90deg, #ffffff 0%, #f4f8fd 100%);
  border-bottom: 1px solid #dbe7f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 50;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sidebar-toggle {
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  background: #f1f5f9;
  color: #F56C6C;
}

.toggle-icon {
  transition: transform 0.3s ease;
}

.breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  padding: 8px;
  border-radius: 8px;
  color: #64748b;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: #f1f5f9;
  color: #F56C6C;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  transition: all 0.3s ease;
  background: #f8fafc;
}

.user-info:hover {
  background: #f1f5f9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.user-avatar {
  border: 2px solid #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.username {
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}

.user-role {
  font-size: 12px;
  color: #F56C6C;
  font-weight: 500;
}

.dropdown-icon {
  color: #64748b;
  transition: transform 0.3s ease;
  font-size: 14px;
}

.main-content {
  background: transparent;
  padding: 16px;
  overflow-y: auto;
}

.content-wrapper {
  padding: 24px;
  min-height: 100%;
  overflow: visible;
  background: rgba(255, 255, 255, 0.58);
  backdrop-filter: blur(8px);
  border: 1px solid #e6effa;
  border-radius: 18px;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 滚动条样式 */
.content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.content-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
  }
  
  .sidebar.collapsed {
    transform: translateX(-100%);
  }
  
  .header {
    padding: 0 16px;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .user-details {
    display: none;
  }
  
  .content-wrapper {
    padding: 16px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-menu--collapse) {
  width: 64px;
}

:deep(.el-menu--collapse .el-menu-item) {
  padding: 0 20px;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
}

:deep(.el-breadcrumb__inner) {
  color: #64748b;
  font-weight: 500;
}

:deep(.el-breadcrumb__inner.is-link) {
  color: #F56C6C;
}

:deep(.el-breadcrumb__separator) {
  color: #cbd5e1;
}
</style>
