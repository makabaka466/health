<template>
  <div class="home-container">
    <section class="hero-section">
      <div class="hero-copy">
        <span class="hero-kicker">SMART HEALTH</span>
        <h1>欢迎回来，{{ greeting }}</h1>
        <p>
          今天是 {{ todayDate }}，这里为你聚合健康知识推荐、AI 个性化建议与快捷入口，
          让日常健康管理更轻松、更直观。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" round @click="router.push('/dashboard/health-data')">查看健康数据</el-button>
          <el-button size="large" round @click="router.push('/dashboard/knowledge-center')">进入知识中心</el-button>
        </div>
        <div class="hero-metrics">
          <div class="metric-card">
            <strong>{{ todayDate }}</strong>
            <span>今日日期</span>
          </div>
          <div class="metric-card">
            <strong>{{ pushedArticles.length }}</strong>
            <span>推荐文章</span>
          </div>
          <div class="metric-card">
            <strong>{{ aiHomeAdvice.recommendations.length }}</strong>
            <span>AI 建议</span>
          </div>
        </div>
      </div>

      <div class="hero-visual">
        <div class="visual-card primary">
          <span>健康趋势</span>
          <strong>稳定向好</strong>
        </div>
        <div class="visual-card secondary">
          <span>知识阅读</span>
          <strong>建议每天 10 分钟</strong>
        </div>
        <div class="floating-icon icon-heart"><el-icon><Heart /></el-icon></div>
        <div class="floating-icon icon-trend"><el-icon><TrendCharts /></el-icon></div>
        <div class="floating-icon icon-bell"><el-icon><Bell /></el-icon></div>
      </div>
    </section>

    <section class="panel-section">
      <div class="section-head">
        <div>
          <h2 class="section-title">健康知识推荐</h2>
          <p class="section-subtitle">大图轮播结合热门榜单，帮你更快找到值得阅读的内容。</p>
        </div>
        <el-button type="primary" plain @click="router.push('/dashboard/knowledge-center')">查看更多</el-button>
      </div>

      <div v-if="pushedArticles.length" class="recommend-showcase">
        <div class="recommend-carousel-wrap">
          <el-carousel :interval="5000" trigger="click" arrow="always" height="320px">
            <el-carousel-item v-for="article in pushedArticles" :key="article.id">
              <div class="recommend-slide" :style="getArticleBannerStyle(article)" @click="goArticle(article.id)">
                <div class="slide-overlay"></div>
                <div class="slide-content">
                  <div class="recommend-header">
                    <el-tag size="small" effect="dark">{{ article.category }}</el-tag>
                    <span class="recommend-meta">{{ article.view_count }} 阅读 · {{ article.favorite_count }} 收藏</span>
                  </div>
                  <h3>{{ article.title }}</h3>
                  <p>{{ article.summary || '点击查看完整文章，获取更系统的健康建议。' }}</p>
                  <div class="slide-actions">
                    <el-button type="primary" size="large" round @click.stop="goArticle(article.id)">立即阅读</el-button>
                    <span class="slide-tip">持续更新的健康精选内容</span>
                  </div>
                </div>
              </div>
            </el-carousel-item>
          </el-carousel>
        </div>

        <div class="recommend-side">
          <div class="side-panel-title">本周热门</div>
          <button
            v-for="(article, index) in pushedArticles.slice(0, 3)"
            :key="`side-${article.id}`"
            type="button"
            class="side-article"
            @click="goArticle(article.id)"
          >
            <span class="side-rank">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="side-info">
              <strong>{{ article.title }}</strong>
              <small>{{ article.category }} · {{ article.view_count }} 阅读</small>
            </span>
          </button>
        </div>
      </div>

      <el-card v-else class="recommend-empty" shadow="never">
        <p>暂无推荐文章，去知识中心看看最新内容吧。</p>
        <el-button type="primary" plain @click="router.push('/dashboard/knowledge-center')">前往知识中心</el-button>
      </el-card>
    </section>

    <section class="panel-grid">
      <el-card class="panel-card" shadow="hover">
        <div class="section-head compact">
          <div>
            <h2 class="section-title">AI 个性化建议</h2>
            <p class="section-subtitle">基于公开记录生成的轻量建议</p>
          </div>
          <el-tag type="success" effect="plain">{{ aiHomeAdvice.based_on_public_records }} 条记录</el-tag>
        </div>
        <p class="advice-summary">{{ aiHomeAdvice.summary }}</p>
        <ul class="advice-list">
          <li v-for="(item, idx) in aiHomeAdvice.recommendations" :key="`advice-${idx}`">{{ item }}</li>
        </ul>
        <div v-if="aiHomeAdvice.insights.length" class="insight-list">
          <el-tag v-for="(insight, idx) in aiHomeAdvice.insights" :key="`insight-${idx}`" effect="light">{{ insight }}</el-tag>
        </div>
      </el-card>

      <el-card class="panel-card" shadow="hover">
        <div class="section-head compact">
          <div>
            <h2 class="section-title">快捷操作</h2>
            <p class="section-subtitle">常用功能一键直达</p>
          </div>
        </div>
        <div class="action-cards">
          <button v-for="action in quickActions" :key="action.title" type="button" class="action-card" @click="handleActionClick(action)">
            <div class="action-icon" :style="{ color: action.color, background: `${action.color}18` }">
              <el-icon><component :is="action.icon" /></el-icon>
            </div>
            <div class="action-info">
              <strong>{{ action.title }}</strong>
              <span>{{ action.description }}</span>
            </div>
            <el-icon class="action-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
      </el-card>
    </section>

    <section class="panel-grid two-equal">
      <el-card class="panel-card" shadow="hover">
        <div class="section-head compact">
          <div>
            <h2 class="section-title">健康概览</h2>
            <p class="section-subtitle">用更直观的指标观察日常健康状态</p>
          </div>
        </div>
        <div class="overview-grid">
          <div v-for="item in overviewCards" :key="item.title" class="overview-card">
            <div class="overview-icon" :style="{ background: item.bg }">
              <el-icon :color="item.color"><component :is="item.icon" /></el-icon>
            </div>
            <strong>{{ item.value }}</strong>
            <span>{{ item.title }}</span>
            <small>{{ item.description }}</small>
          </div>
        </div>
      </el-card>

      <el-card class="panel-card" shadow="hover">
        <div class="section-head compact">
          <div>
            <h2 class="section-title">最近动态</h2>
            <p class="section-subtitle">最近一次使用系统的重点轨迹</p>
          </div>
        </div>
        <div class="activity-list">
          <div v-for="activity in recentActivities" :key="activity.title" class="activity-item">
            <div class="activity-icon" :style="{ background: activity.bgColor, color: activity.color }">
              <el-icon><component :is="activity.icon" /></el-icon>
            </div>
            <div class="activity-content">
              <strong>{{ activity.title }}</strong>
              <p>{{ activity.description }}</p>
            </div>
            <span class="activity-time">{{ activity.time }}</span>
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeApi } from '../api/knowledge'
import { aiApi } from '../api/ai'

const router = useRouter()

const quickActions = ref([
  { title: '健康趋势', description: '查看你的健康数据趋势', icon: 'TrendCharts', color: '#409EFF', route: '/dashboard/health-data' },
  { title: '健康记录', description: '补充和整理每日健康信息', icon: 'Calendar', color: '#67C23A', route: '/dashboard/health-data' },
  { title: 'AI 助手', description: '获取个性化健康建议', icon: 'ChatDotRound', color: '#E6A23C', route: '/dashboard/ai-chat' },
  { title: '个人中心', description: '查看资料与系统设置', icon: 'User', color: '#F56C6C', route: '/dashboard/profile' }
])

const overviewCards = ref([
  { title: '数据记录', value: '128', description: '已累计录入健康数据', icon: 'DataAnalysis', color: '#409EFF', bg: 'rgba(64, 158, 255, 0.14)' },
  { title: '文章阅读', value: '24', description: '本周已阅读健康文章', icon: 'Reading', color: '#67C23A', bg: 'rgba(103, 194, 58, 0.14)' },
  { title: 'AI 咨询', value: '12', description: '本月与 AI 的咨询次数', icon: 'ChatDotRound', color: '#E6A23C', bg: 'rgba(230, 162, 60, 0.14)' },
  { title: '提醒计划', value: '6', description: '当前生效的健康提醒', icon: 'Bell', color: '#F56C6C', bg: 'rgba(245, 108, 108, 0.14)' }
])

const recentActivities = ref([
  { title: '完成今天的健康记录', description: '已补充体重、血压和睡眠时长。', icon: 'DataAnalysis', color: '#409EFF', bgColor: 'rgba(64, 158, 255, 0.12)', time: '今天' },
  { title: '阅读营养饮食文章', description: '查看了适合工作日的轻食搭配建议。', icon: 'Reading', color: '#67C23A', bgColor: 'rgba(103, 194, 58, 0.12)', time: '2 小时前' },
  { title: '完成 AI 问答', description: '咨询了关于作息调整和运动安排的问题。', icon: 'ChatDotRound', color: '#E6A23C', bgColor: 'rgba(230, 162, 60, 0.12)', time: '昨天' }
])

const pushedArticles = ref([])
const aiHomeAdvice = ref({
  summary: '正在生成个性化建议...',
  recommendations: [],
  insights: [],
  based_on_public_records: 0
})

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

const getArticleBannerStyle = (article) => ({
  backgroundImage: article?.cover_image
    ? `linear-gradient(135deg, rgba(20, 42, 84, 0.72), rgba(36, 99, 235, 0.55)), url(${article.cover_image})`
    : 'linear-gradient(120deg, #2f6fd6 0%, #36a3f5 50%, #5ec7b9 100%)',
  backgroundSize: 'cover',
  backgroundPosition: 'center'
})

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

const loadAiHomeAdvice = async () => {
  try {
    const data = await aiApi.getHomeAdvice()
    aiHomeAdvice.value = {
      summary: data?.summary || '暂无建议',
      recommendations: data?.recommendations || [],
      insights: data?.insights || [],
      based_on_public_records: data?.based_on_public_records || 0
    }
  } catch {
    aiHomeAdvice.value = {
      summary: '个性化建议加载失败，请稍后重试。',
      recommendations: [],
      insights: [],
      based_on_public_records: 0
    }
  }
}

onMounted(() => {
  loadRecommendations()
  loadAiHomeAdvice()
})
</script>

<style scoped>
.home-container {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.hero-section {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.9fr);
  gap: 24px;
  padding: 32px;
  border-radius: 28px;
  color: #fff;
  background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 48%, #0ea5e9 100%);
  box-shadow: 0 24px 50px rgba(59, 130, 246, 0.22);
  overflow: hidden;
}

.hero-copy,
.hero-visual {
  position: relative;
  z-index: 1;
}

.hero-kicker {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 12px;
  letter-spacing: 1px;
}

.hero-copy h1 {
  margin: 14px 0 10px;
  font-size: 42px;
  line-height: 1.2;
}

.hero-copy p {
  margin: 0;
  max-width: 680px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.92);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 28px;
}

.metric-card,
.visual-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(12px);
}

.metric-card strong,
.visual-card strong {
  display: block;
  font-size: 22px;
}

.metric-card span,
.visual-card span {
  display: block;
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.84);
  font-size: 13px;
}

.hero-visual {
  min-height: 280px;
}

.visual-card {
  position: absolute;
  width: 220px;
}

.visual-card.primary {
  top: 18px;
  right: 0;
}

.visual-card.secondary {
  left: 24px;
  bottom: 22px;
}

.floating-icon {
  position: absolute;
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  font-size: 22px;
}

.icon-heart {
  left: 10px;
  top: 20px;
}

.icon-trend {
  right: 84px;
  top: 132px;
}

.icon-bell {
  right: 34px;
  bottom: 24px;
}

.panel-section,
.panel-card {
  border-radius: 24px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.section-head.compact {
  margin-bottom: 12px;
}

.section-title {
  margin: 0;
  font-size: 26px;
  color: #0f172a;
}

.section-subtitle {
  margin: 8px 0 0;
  color: #64748b;
}

.recommend-showcase {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.9fr);
  gap: 18px;
  margin-top: 16px;
}

.recommend-carousel-wrap {
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.16);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.recommend-slide {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 32px;
  cursor: pointer;
  display: flex;
  align-items: flex-end;
  background-repeat: no-repeat;
}

.slide-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.08) 0%, rgba(15, 23, 42, 0.48) 100%), radial-gradient(circle at 85% 25%, rgba(255, 255, 255, 0.22), transparent 40%);
}

.slide-content {
  position: relative;
  z-index: 1;
  max-width: 720px;
  color: #ffffff;
}

.recommend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.slide-content h3 {
  margin: 0 0 10px;
  font-size: 32px;
  line-height: 1.35;
}

.slide-content p {
  margin: 0;
  max-width: 620px;
  line-height: 1.75;
  color: rgba(255, 255, 255, 0.94);
}

.slide-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 18px;
}

.slide-tip,
.recommend-meta {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.recommend-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
}

.side-panel-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.side-article {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e5edf8;
  border-radius: 18px;
  background: #f8fbff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.side-article:hover,
.action-card:hover,
.activity-item:hover,
.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.08);
}

.side-rank {
  min-width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb, #60a5fa);
  color: #fff;
  font-weight: 700;
}

.side-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.side-info strong {
  color: #0f172a;
  line-height: 1.5;
}

.side-info small {
  color: #64748b;
}

.recommend-empty {
  margin-top: 16px;
  border-radius: 18px;
  border: 1px dashed #d8e4f6;
  background: #f8fbff;
  text-align: center;
}

.panel-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.95fr);
  gap: 18px;
}

.panel-grid.two-equal {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.panel-card {
  border: none;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
}

.advice-summary {
  margin: 6px 0 0;
  color: #334155;
  line-height: 1.8;
}

.advice-list {
  margin: 16px 0 0;
  padding-left: 18px;
  color: #334155;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.insight-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.action-cards,
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-card,
.activity-item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 16px;
  border: 1px solid #e5edf7;
  border-radius: 18px;
  background: #f8fbff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-icon,
.activity-icon,
.overview-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  font-size: 20px;
}

.action-info,
.activity-content {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.action-info strong,
.activity-content strong {
  color: #0f172a;
}

.action-info span,
.activity-content p,
.activity-time {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.action-arrow {
  color: #94a3b8;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.overview-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid #e8eef7;
  background: #f8fbff;
  transition: all 0.2s ease;
}

.overview-card strong {
  display: block;
  margin-top: 14px;
  font-size: 28px;
  color: #0f172a;
}

.overview-card span {
  display: block;
  margin-top: 6px;
  color: #334155;
  font-weight: 600;
}

.overview-card small {
  display: block;
  margin-top: 6px;
  color: #64748b;
  line-height: 1.6;
}

@media (max-width: 1200px) {
  .hero-section,
  .recommend-showcase,
  .panel-grid,
  .panel-grid.two-equal {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .home-container {
    gap: 20px;
  }

  .hero-section {
    padding: 22px;
  }

  .hero-copy h1 {
    font-size: 32px;
  }

  .hero-metrics,
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .slide-content h3 {
    font-size: 24px;
  }
}
</style>
