<template>
  <div class="admin-home-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1 class="welcome-title">
            <span class="title-gradient">管理控制台</span>
          </h1>
          <p class="welcome-subtitle">健康管理系统后台管理中心</p>
          <div class="welcome-stats">
            <div class="stat-item">
              <span class="stat-number">{{ systemStats.totalUsers }}</span>
              <span class="stat-label">总用户数</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ systemStats.todayLogins }}</span>
              <span class="stat-label">今日登录</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ systemStats.systemStatus }}</span>
              <span class="stat-label">系统状态</span>
            </div>
          </div>
        </div>
        <div class="welcome-visual">
          <div class="floating-cards">
            <div class="floating-card card-1">
              <el-icon size="24" color="#F56C6C"><Monitor /></el-icon>
            </div>
            <div class="floating-card card-2">
              <el-icon size="24" color="#67C23A"><DataAnalysis /></el-icon>
            </div>
            <div class="floating-card card-3">
              <el-icon size="24" color="#E6A23C"><Bell /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 快速操作 -->
    <div class="quick-actions">
      <h2 class="section-title">快速操作</h2>
      <div class="action-cards">
        <el-card 
          v-for="(action, index) in quickActions" 
          :key="index"
          class="action-card"
          :class="`action-${index + 1}`"
          shadow="hover"
          @click="handleActionClick(action)"
        >
          <div class="action-content">
            <div class="action-icon">
              <el-icon :size="32" :color="action.color">
                <component :is="action.icon" />
              </el-icon>
            </div>
            <div class="action-info">
              <h3>{{ action.title }}</h3>
              <p>{{ action.description }}</p>
            </div>
            <div class="action-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 系统概览 -->
    <div class="system-overview">
      <h2 class="section-title">系统概览</h2>
      <div class="overview-grid">
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#F56C6C"><User /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-up">+15%</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>用户总数</h3>
            <div class="stat-display">
              <span class="stat-number">{{ systemStats.totalUsers }}</span>
              <span class="stat-unit">人</span>
            </div>
            <p class="overview-desc">较上月增长 150 人</p>
          </div>
        </el-card>
        
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#67C23A"><DataAnalysis /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-stable">稳定</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>健康数据</h3>
            <div class="stat-display">
              <span class="stat-number">{{ systemStats.healthRecords }}</span>
              <span class="stat-unit">条</span>
            </div>
            <p class="overview-desc">累计健康记录</p>
          </div>
        </el-card>
        
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#E6A23C"><ChatDotRound /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-up">+25%</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>AI咨询</h3>
            <div class="stat-display">
              <span class="stat-number">{{ systemStats.aiConsultations }}</span>
              <span class="stat-unit">次</span>
            </div>
            <p class="overview-desc">本月AI咨询次数</p>
          </div>
        </el-card>
        
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#409EFF"><Monitor /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-stable">正常</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>系统运行</h3>
            <div class="stat-display">
              <span class="stat-number">{{ systemStats.uptime }}</span>
              <span class="stat-unit">天</span>
            </div>
            <p class="overview-desc">连续运行时间</p>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 最近活动 -->
    <div class="recent-activities">
      <h2 class="section-title">系统活动</h2>
      <el-card class="activities-card" shadow="hover">
        <div class="activity-list">
          <div 
            v-for="(activity, index) in recentActivities" 
            :key="index"
            class="activity-item"
          >
            <div class="activity-icon" :style="{ backgroundColor: activity.bgColor }">
              <el-icon :size="16" :color="activity.color">
                <component :is="activity.icon" />
              </el-icon>
            </div>
            <div class="activity-content">
              <h4>{{ activity.title }}</h4>
              <p>{{ activity.description }}</p>
            </div>
            <div class="activity-time">
              <span>{{ activity.time }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const systemStats = ref({
  totalUsers: 1248,
  todayLogins: 186,
  systemStatus: '正常',
  healthRecords: 15680,
  aiConsultations: 892,
  uptime: 99
})

const quickActions = ref([
  {
    title: '用户管理',
    description: '管理系统用户和权限',
    icon: 'User',
    color: '#F56C6C',
    route: '/admin/users'
  },
  {
    title: '数据管理',
    description: '查看和管理健康数据',
    icon: 'DataAnalysis',
    color: '#67C23A',
    route: '/admin/health-data'
  },
  {
    title: 'AI管理',
    description: '配置AI助手参数',
    icon: 'ChatDotRound',
    color: '#E6A23C',
    route: '/admin/ai-chat'
  },
  {
    title: '系统设置',
    description: '系统配置和参数设置',
    icon: 'Setting',
    color: '#409EFF',
    route: '/admin/settings'
  }
])

const recentActivities = ref([
  {
    title: '新用户注册',
    description: '用户 "张三" 完成注册',
    icon: 'User',
    color: '#F56C6C',
    bgColor: 'rgba(245, 108, 108, 0.1)',
    time: '10分钟前'
  },
  {
    title: 'AI咨询高峰',
    description: 'AI咨询量达到今日峰值',
    icon: 'ChatDotRound',
    color: '#E6A23C',
    bgColor: 'rgba(230, 162, 60, 0.1)',
    time: '30分钟前'
  },
  {
    title: '数据备份完成',
    description: '系统数据自动备份成功',
    icon: 'Document',
    color: '#67C23A',
    bgColor: 'rgba(103, 194, 58, 0.1)',
    time: '1小时前'
  },
  {
    title: '系统更新',
    description: 'AI模型版本更新至 v2.1.0',
    icon: 'Setting',
    color: '#409EFF',
    bgColor: 'rgba(64, 158, 255, 0.1)',
    time: '2小时前'
  }
])

const handleActionClick = (action) => {
  router.push(action.route)
}

onMounted(() => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in')
      }
    })
  })
  
  document.querySelectorAll('.action-card, .overview-card').forEach(el => {
    observer.observe(el)
  })
})
</script>

<style scoped>
.admin-home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0;
}

/* 欢迎区域 */
.welcome-section {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.welcome-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 300px;
  height: 300px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.welcome-text {
  flex: 1;
  color: white;
}

.welcome-title {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 16px;
  line-height: 1.2;
}

.title-gradient {
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  font-size: 20px;
  margin-bottom: 32px;
  opacity: 0.9;
}

.welcome-stats {
  display: flex;
  gap: 40px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
}

.stat-label {
  font-size: 14px;
  opacity: 0.8;
}

.welcome-visual {
  position: relative;
  width: 200px;
  height: 200px;
}

.floating-cards {
  position: relative;
  width: 100%;
  height: 100%;
}

.floating-card {
  position: absolute;
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: float-card 4s ease-in-out infinite;
}

.card-1 {
  top: 20px;
  right: 40px;
  animation-delay: 0s;
}

.card-2 {
  top: 80px;
  right: 100px;
  animation-delay: 1s;
}

.card-3 {
  bottom: 40px;
  right: 20px;
  animation-delay: 2s;
}

@keyframes float-card {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(5deg);
  }
}

/* 快速操作 */
.quick-actions {
  margin-bottom: 32px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 24px;
  background: linear-gradient(135deg, #F56C6C, #E74C3C);
  border-radius: 2px;
}

.action-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.action-card {
  border-radius: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0;
  transform: translateY(20px);
}

.action-card.animate-in {
  opacity: 1;
  transform: translateY(0);
}

.action-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.action-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px;
}

.action-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 108, 108, 0.1);
  flex-shrink: 0;
}

.action-info {
  flex: 1;
}

.action-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.action-info p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.action-arrow {
  color: #94a3b8;
  transition: all 0.3s ease;
}

.action-card:hover .action-arrow {
  color: #F56C6C;
  transform: translateX(4px);
}

/* 系统概览 */
.system-overview {
  margin-bottom: 32px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.overview-card {
  border-radius: 16px;
  border: none;
  opacity: 0;
  transform: translateY(20px);
}

.overview-card.animate-in {
  opacity: 1;
  transform: translateY(0);
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.overview-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 108, 108, 0.1);
}

.overview-trend {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.trend-up {
  background: rgba(103, 194, 58, 0.1);
  color: #67C23A;
}

.trend-down {
  background: rgba(245, 108, 108, 0.1);
  color: #F56C6C;
}

.trend-stable {
  background: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

.overview-content h3 {
  font-size: 16px;
  color: #64748b;
  margin-bottom: 8px;
  font-weight: 500;
}

.stat-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

.stat-unit {
  font-size: 14px;
  color: #94a3b8;
}

.overview-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

/* 最近活动 */
.recent-activities {
  margin-bottom: 32px;
}

.activities-card {
  border-radius: 16px;
  border: none;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.activity-item:hover {
  background: #f8fafc;
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
}

.activity-content h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.activity-content p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.activity-time {
  font-size: 14px;
  color: #94a3b8;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .welcome-section {
    padding: 24px;
  }
  
  .welcome-content {
    flex-direction: column;
    text-align: center;
    gap: 24px;
  }
  
  .welcome-title {
    font-size: 32px;
  }
  
  .welcome-subtitle {
    font-size: 16px;
  }
  
  .welcome-stats {
    justify-content: center;
  }
  
  .welcome-visual {
    display: none;
  }
  
  .action-cards {
    grid-template-columns: 1fr;
  }
  
  .overview-grid {
    grid-template-columns: 1fr;
  }
  
  .activity-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .activity-time {
    align-self: flex-end;
  }
}

/* 动画 */
@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}
</style>
