<template>
  <div class="home-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1 class="welcome-title">
            <span class="title-gradient">健康管理系统</span>
          </h1>
          <p class="welcome-subtitle">您的智能健康管理助手</p>
          <div class="welcome-stats">
            <div class="stat-item">
              <span class="stat-number">{{ todayDate }}</span>
              <span class="stat-label">今日日期</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ greeting }}</span>
              <span class="stat-label">问候语</span>
            </div>
          </div>
        </div>
        <div class="welcome-visual">
          <div class="floating-cards">
            <div class="floating-card card-1">
              <el-icon size="24" color="#409EFF"><Heart /></el-icon>
            </div>
            <div class="floating-card card-2">
              <el-icon size="24" color="#67C23A"><TrendCharts /></el-icon>
            </div>
            <div class="floating-card card-3">
              <el-icon size="24" color="#E6A23C"><Bell /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="home-recommendations">
      <h2 class="section-title">健康知识推送</h2>
      <div v-if="pushedArticles.length" class="recommend-carousel-wrap">
        <el-carousel :interval="5000" trigger="click" arrow="always" height="260px">
          <el-carousel-item v-for="article in pushedArticles" :key="article.id">
            <div class="recommend-slide" @click="goArticle(article.id)">
              <div class="slide-overlay"></div>
              <div class="slide-content">
                <div class="recommend-header">
                  <el-tag size="small" effect="dark">{{ article.category }}</el-tag>
                  <span class="recommend-meta">{{ article.view_count }} 阅读</span>
                </div>
                <h3>{{ article.title }}</h3>
                <p>{{ article.summary }}</p>
              </div>
            </div>
          </el-carousel-item>
        </el-carousel>
      </div>
      <el-card v-else class="recommend-empty" shadow="never">
        <p>暂无推送文章，去知识中心看看最新内容</p>
        <el-button type="primary" plain @click="router.push('/dashboard/knowledge-center')">前往知识中心</el-button>
      </el-card>
    </div>
    
    <!-- 快速操作卡片 -->
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
    
    <!-- 健康概览 -->
    <div class="health-overview">
      <h2 class="section-title">健康概览</h2>
      <div class="overview-grid">
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#409EFF"><DataAnalysis /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-up">+12%</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>健康评分</h3>
            <div class="score-display">
              <span class="score-number">85</span>
              <span class="score-max">/100</span>
            </div>
            <p class="overview-desc">较上月提升 5 分</p>
          </div>
        </el-card>
        
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#67C23A"><Calendar /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-stable">稳定</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>运动记录</h3>
            <div class="stat-display">
              <span class="stat-number">156</span>
              <span class="stat-unit">次</span>
            </div>
            <p class="overview-desc">本月累计运动</p>
          </div>
        </el-card>
        
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#E6A23C"><ChatDotRound /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-up">+8</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>AI咨询</h3>
            <div class="stat-display">
              <span class="stat-number">24</span>
              <span class="stat-unit">次</span>
            </div>
            <p class="overview-desc">本月智能咨询</p>
          </div>
        </el-card>
        
        <el-card class="overview-card" shadow="hover">
          <div class="overview-header">
            <div class="overview-icon">
              <el-icon size="28" color="#F56C6C"><Bell /></el-icon>
            </div>
            <div class="overview-trend">
              <span class="trend-down">-2</span>
            </div>
          </div>
          <div class="overview-content">
            <h3>健康提醒</h3>
            <div class="stat-display">
              <span class="stat-number">12</span>
              <span class="stat-unit">个</span>
            </div>
            <p class="overview-desc">活跃提醒事项</p>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 最近活动 -->
    <div class="recent-activities">
      <h2 class="section-title">最近活动</h2>
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
import { knowledgeApi } from '../api/knowledge'

const router = useRouter()

const quickActions = ref([
  {
    title: '健康趋势',
    description: '查看您的健康数据趋势',
    icon: 'TrendCharts',
    color: '#409EFF',
    route: '/dashboard/health-data'
  },
  {
    title: '健康记录',
    description: '记录每日健康数据',
    icon: 'Calendar',
    color: '#67C23A',
    route: '/dashboard/health-data'
  },
  {
    title: 'AI助手',
    description: '获取智能健康建议',
    icon: 'ChatDotRound',
    color: '#E6A23C',
    route: '/dashboard/ai-chat'
  },
  {
    title: '健康提醒',
    description: '个性化健康提醒',
    icon: 'Bell',
    color: '#F56C6C',
    route: '/dashboard/profile'
  }
])

const pushedArticles = ref([])

const recentActivities = ref([
  {
    title: '完成今日运动',
    description: '跑步 5 公里，消耗 300 卡路里',
    icon: 'TrendCharts',
    color: '#409EFF',
    bgColor: 'rgba(64, 158, 255, 0.1)',
    time: '2小时前'
  },
  {
    title: 'AI健康咨询',
    description: '询问关于睡眠质量的建议',
    icon: 'ChatDotRound',
    color: '#E6A23C',
    bgColor: 'rgba(230, 162, 60, 0.1)',
    time: '4小时前'
  },
  {
    title: '记录血压数据',
    description: '血压 120/80 mmHg，正常范围',
    icon: 'DataAnalysis',
    color: '#67C23A',
    bgColor: 'rgba(103, 194, 58, 0.1)',
    time: '昨天'
  },
  {
    title: '设置用药提醒',
    description: '每日 9:00 服用维生素',
    icon: 'Bell',
    color: '#F56C6C',
    bgColor: 'rgba(245, 108, 108, 0.1)',
    time: '2天前'
  }
])

const todayDate = computed(() => {
  const now = new Date()
  return `${now.getMonth() + 1}月${now.getDate()}日`
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '凌晨好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const handleActionClick = (action) => {
  router.push(action.route)
}

const goArticle = (articleId) => {
  router.push(`/dashboard/knowledge-center/article/${articleId}`)
}

const loadRecommendations = async () => {
  try {
    const data = await knowledgeApi.getHomepageRecommendations()
    const merged = [...(data.hot_articles || []), ...(data.latest_articles || [])]
    const seen = new Set()
    pushedArticles.value = merged.filter((item) => {
      if (seen.has(item.id)) return false
      seen.add(item.id)
      return true
    }).slice(0, 5)
  } catch {
    pushedArticles.value = []
  }
}

onMounted(() => {
  loadRecommendations()
  // 添加页面加载动画
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
.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0;
}

/* 欢迎区域 */
.welcome-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.welcome-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 300px;
  height: 300px;
  background: rgba(255, 255, 255, 0.1);
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
  background: rgba(255, 255, 255, 0.2);
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

.home-recommendations {
  margin-bottom: 32px;
}

.recommend-carousel-wrap {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.14);
}

.recommend-slide {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 28px;
  cursor: pointer;
  background: linear-gradient(120deg, #2f6fd6 0%, #36a3f5 50%, #5ec7b9 100%);
  display: flex;
  align-items: flex-end;
}

.slide-overlay {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 85% 25%, rgba(255, 255, 255, 0.28), transparent 40%);
}

.slide-content {
  position: relative;
  z-index: 1;
  max-width: 760px;
  color: #ffffff;
}

.recommend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.slide-content h3 {
  margin: 0 0 8px;
  font-size: 30px;
  color: #ffffff;
  line-height: 1.4;
  text-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

.slide-content p {
  margin: 0;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.5;
  line-clamp: 2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.recommend-meta {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.recommend-carousel-wrap :deep(.el-carousel__button) {
  width: 18px;
  border-radius: 999px;
}

.recommend-carousel-wrap :deep(.el-carousel__arrow) {
  background: rgba(0, 0, 0, 0.25);
}

.recommend-empty {
  border-radius: 14px;
  border: 1px dashed #cbd5e1;
  text-align: center;
}

.recommend-empty p {
  margin: 0 0 12px;
  color: #64748b;
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
  background: linear-gradient(135deg, #409EFF, #36A3F5);
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
  background: rgba(64, 158, 255, 0.1);
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
  color: #409EFF;
  transform: translateX(4px);
}

/* 健康概览 */
.health-overview {
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
  background: rgba(64, 158, 255, 0.1);
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

.score-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.score-number {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

.score-max {
  font-size: 16px;
  color: #94a3b8;
}

.stat-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.stat-number {
  font-size: 28px;
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

  .recommend-slide {
    padding: 20px;
    height: 230px;
  }

  .slide-content h3 {
    font-size: 22px;
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
