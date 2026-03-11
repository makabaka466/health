<template>
  <div class="knowledge-center-container">
    <section class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="30"><Reading /></el-icon>
        </div>
        <div class="header-text">
          <h1>健康知识中心</h1>
          <p>浏览健康文章、管理个人收藏，并查看更细致的阅读轨迹。</p>
        </div>
      </div>

      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索文章标题、摘要或正文"
          class="search-input"
          @keyup.enter="searchKnowledge"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button class="header-btn" @click="showAllArticles">全部文章</el-button>
        <el-button class="header-btn" @click="loadFavorites">我的收藏</el-button>
        <el-button class="header-btn" @click="openReadHistory">阅读记录</el-button>
      </div>
    </section>

    <section class="content-section">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="8" :md="6">
          <aside class="category-sidebar">
            <div class="sidebar-header">
              <h3>知识分类</h3>
              <span>{{ totalItems }} 篇</span>
            </div>
            <div class="category-list">
              <button
                v-for="category in categories"
                :key="category.id"
                type="button"
                class="category-item"
                :class="{ active: selectedCategory === category.id }"
                @click="selectCategory(category.id)"
              >
                <div class="category-icon" :style="{ color: category.color }">
                  <el-icon><component :is="category.icon" /></el-icon>
                </div>
                <div class="category-info">
                  <strong>{{ category.name }}</strong>
                  <span>{{ category.count }} 篇文章</span>
                </div>
              </button>
            </div>
          </aside>
        </el-col>

        <el-col :xs="24" :sm="16" :md="18">
          <section class="knowledge-content">
            <div class="content-header">
              <div>
                <div class="content-title">{{ currentModeLabel }}</div>
                <p class="content-subtitle">{{ currentCategoryLabel }} · 共 {{ totalItems }} 篇</p>
              </div>
              <div class="content-actions">
                <el-radio-group v-model="viewMode" size="small">
                  <el-radio-button label="grid">卡片</el-radio-button>
                  <el-radio-button label="list">列表</el-radio-button>
                </el-radio-group>
              </div>
            </div>

            <div class="content-stats">
              <div class="stats-chip">
                <span class="chip-label">当前分类</span>
                <span class="chip-value">{{ currentCategoryLabel }}</span>
              </div>
              <div class="stats-chip">
                <span class="chip-label">内容模式</span>
                <span class="chip-value">{{ currentModeLabel }}</span>
              </div>
              <div class="stats-chip">
                <span class="chip-label">分页大小</span>
                <span class="chip-value">{{ pageSize }} 篇</span>
              </div>
            </div>

            <div v-if="loading" class="loading-container">
              <el-skeleton :rows="5" animated />
            </div>

            <div v-else-if="knowledgeItems.length === 0" class="empty-container">
              <el-empty description="没有找到符合条件的文章">
                <el-button type="primary" @click="showAllArticles">返回全部文章</el-button>
              </el-empty>
            </div>

            <template v-else>
              <div v-if="viewMode === 'grid'" class="knowledge-grid">
                <article
                  v-for="item in knowledgeItems"
                  :key="item.id"
                  class="knowledge-card"
                  @click="openKnowledgeDetail(item)"
                >
                  <div class="card-image">
                    <img :src="item.cover_image || '/default-health.jpg'" :alt="item.title" />
                    <button
                      type="button"
                      class="favorite-toggle"
                      :class="{ active: item.is_favorited }"
                      :disabled="isFavoriteLoading(item.id)"
                      @click.stop="toggleFavorite(item)"
                    >
                      <el-icon><Star /></el-icon>
                    </button>
                  </div>
                  <div class="card-content">
                    <div class="card-category-row">
                      <span class="card-category">{{ item.category }}</span>
                      <span class="card-date">{{ formatDate(item.created_at) }}</span>
                    </div>
                    <h3 class="card-title">{{ item.title }}</h3>
                    <p class="card-summary">{{ item.summary || '暂无摘要' }}</p>
                    <div class="card-meta">
                      <span class="meta-item"><el-icon><View /></el-icon>{{ item.view_count }}</span>
                      <span class="meta-item"><el-icon><Star /></el-icon>{{ item.favorite_count }}</span>
                      <span class="meta-item favorite-text">{{ item.is_favorited ? '已收藏' : '点击收藏' }}</span>
                    </div>
                  </div>
                </article>
              </div>

              <div v-else class="knowledge-list">
                <article
                  v-for="item in knowledgeItems"
                  :key="item.id"
                  class="knowledge-list-item"
                  @click="openKnowledgeDetail(item)"
                >
                  <div class="list-image">
                    <img :src="item.cover_image || '/default-health.jpg'" :alt="item.title" />
                  </div>
                  <div class="list-info">
                    <div class="list-top-row">
                      <span class="list-category">{{ item.category }}</span>
                      <button
                        type="button"
                        class="favorite-inline"
                        :class="{ active: item.is_favorited }"
                        :disabled="isFavoriteLoading(item.id)"
                        @click.stop="toggleFavorite(item)"
                      >
                        <el-icon><Star /></el-icon>
                        {{ item.is_favorited ? '已收藏' : '收藏' }}
                      </button>
                    </div>
                    <h3 class="list-title">{{ item.title }}</h3>
                    <p class="list-summary">{{ item.summary || '暂无摘要' }}</p>
                    <div class="list-meta">
                      <span class="meta-item"><el-icon><View /></el-icon>{{ item.view_count }}</span>
                      <span class="meta-item"><el-icon><Star /></el-icon>{{ item.favorite_count }}</span>
                      <span class="meta-item"><el-icon><Clock /></el-icon>{{ formatDate(item.created_at) }}</span>
                    </div>
                  </div>
                </article>
              </div>

              <div class="pagination-container">
                <el-pagination
                  v-model:current-page="currentPage"
                  :page-size="pageSize"
                  :total="totalItems"
                  layout="total, prev, pager, next"
                  @current-change="handleCurrentChange"
                />
              </div>
            </template>
          </section>
        </el-col>
      </el-row>
    </section>

    <el-drawer v-model="historyDrawerVisible" title="阅读记录" size="420px">
      <div v-loading="historyLoading" class="history-drawer">
        <div class="history-summary">
          <div>
            <strong>{{ readHistory.length }}</strong>
            <span>最近阅读条目</span>
          </div>
          <div>
            <strong>{{ totalReadCount }}</strong>
            <span>累计阅读次数</span>
          </div>
        </div>

        <el-empty v-if="!historyLoading && !readHistory.length" description="还没有阅读记录" />

        <div v-else class="history-list">
          <div v-for="item in readHistory" :key="`${item.article_id}-${item.last_read_at}`" class="history-item">
            <div class="history-item-main">
              <div class="history-title">{{ item.article_title }}</div>
              <div class="history-category">{{ item.category }}</div>
              <div class="history-meta">
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeApi } from '../api/knowledge'

const router = useRouter()
const searchQuery = ref('')
const selectedCategory = ref('all')
const viewMode = ref('grid')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(9)
const totalItems = ref(0)
const knowledgeItems = ref([])
const contentMode = ref('all')
const favoritePendingIds = ref([])
const historyDrawerVisible = ref(false)
const historyLoading = ref(false)
const readHistory = ref([])

const categories = ref([
  { id: 'all', name: '全部', count: 0, icon: 'Grid', color: '#409EFF' },
  { id: '慢性病管理', name: '慢性病管理', count: 0, icon: 'FirstAidKit', color: '#f56c6c' },
  { id: '营养饮食', name: '营养饮食', count: 0, icon: 'Food', color: '#67c23a' },
  { id: '心理健康', name: '心理健康', count: 0, icon: 'ChatDotRound', color: '#909399' },
  { id: '运动健身', name: '运动健身', count: 0, icon: 'TrendCharts', color: '#e6a23c' },
  { id: '老年健康', name: '老年健康', count: 0, icon: 'Timer', color: '#606266' },
  { id: '儿童健康', name: '儿童健康', count: 0, icon: 'User', color: '#5b8ff9' }
])

const currentCategoryLabel = computed(() => {
  return categories.value.find((item) => item.id === selectedCategory.value)?.name || '全部'
})

const currentModeLabel = computed(() => (contentMode.value === 'favorites' ? '我的收藏' : '全部文章'))

const totalReadCount = computed(() => readHistory.value.reduce((sum, item) => sum + (item.read_count || 0), 0))

const refreshCategoryCount = () => {
  const counts = {}
  for (const item of knowledgeItems.value) {
    counts[item.category] = (counts[item.category] || 0) + 1
  }

  categories.value = categories.value.map((category) => {
    if (category.id === 'all') {
      return { ...category, count: totalItems.value }
    }
    return { ...category, count: counts[category.id] || 0 }
  })
}

const normalizeItems = (items = []) => items.map((item) => ({
  ...item,
  is_favorited: Boolean(item.is_favorited)
}))

const loadKnowledgeItems = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      category: selectedCategory.value === 'all' ? undefined : selectedCategory.value,
      keyword: searchQuery.value || undefined,
      sort_by: 'latest'
    }

    const response = contentMode.value === 'favorites'
      ? await knowledgeApi.getFavorites({ page: params.page, page_size: params.page_size })
      : await knowledgeApi.getArticles(params)

    knowledgeItems.value = normalizeItems(response.items || [])
    totalItems.value = response.total || 0
    refreshCategoryCount()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载知识内容失败')
  } finally {
    loading.value = false
  }
}

const selectCategory = (categoryId) => {
  selectedCategory.value = categoryId
  currentPage.value = 1
  contentMode.value = 'all'
  loadKnowledgeItems()
}

const searchKnowledge = () => {
  currentPage.value = 1
  contentMode.value = 'all'
  loadKnowledgeItems()
}

const showAllArticles = () => {
  contentMode.value = 'all'
  selectedCategory.value = 'all'
  currentPage.value = 1
  loadKnowledgeItems()
}

const loadFavorites = async () => {
  contentMode.value = 'favorites'
  selectedCategory.value = 'all'
  currentPage.value = 1
  await loadKnowledgeItems()
  ElMessage.success('已切换到我的收藏')
}

const openKnowledgeDetail = (item) => {
  router.push(`/dashboard/knowledge-center/article/${item.id}`)
}

const isFavoriteLoading = (articleId) => favoritePendingIds.value.includes(articleId)

const toggleFavorite = async (item) => {
  if (isFavoriteLoading(item.id)) return

  favoritePendingIds.value = [...favoritePendingIds.value, item.id]
  try {
    const result = item.is_favorited
      ? await knowledgeApi.unfavoriteArticle(item.id)
      : await knowledgeApi.favoriteArticle(item.id)

    item.is_favorited = result.is_favorited
    item.favorite_count = result.favorite_count ?? item.favorite_count

    if (contentMode.value === 'favorites' && !result.is_favorited) {
      knowledgeItems.value = knowledgeItems.value.filter((entry) => entry.id !== item.id)
      totalItems.value = Math.max(0, totalItems.value - 1)
    }

    refreshCategoryCount()
    ElMessage.success(result.is_favorited ? '收藏成功' : '已取消收藏')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '收藏操作失败')
  } finally {
    favoritePendingIds.value = favoritePendingIds.value.filter((id) => id !== item.id)
  }
}

const openReadHistory = async () => {
  historyDrawerVisible.value = true
  historyLoading.value = true
  try {
    readHistory.value = await knowledgeApi.getReadHistory(50)
  } catch (error) {
    readHistory.value = []
    ElMessage.error(error?.response?.data?.detail || '加载阅读记录失败')
  } finally {
    historyLoading.value = false
  }
}

const openHistoryArticle = (articleId) => {
  historyDrawerVisible.value = false
  router.push(`/dashboard/knowledge-center/article/${articleId}`)
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  loadKnowledgeItems()
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadKnowledgeItems)
</script>

<style scoped>
.knowledge-center-container {
  max-width: 1680px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 28px;
  border-radius: 20px;
  color: #fff;
  background: linear-gradient(135deg, #409eff 0%, #4f8cff 40%, #6dc8ff 100%);
  box-shadow: 0 16px 36px rgba(64, 158, 255, 0.22);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 64px;
  height: 64px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
}

.header-text h1 {
  margin: 0 0 6px;
  font-size: 30px;
}

.header-text p {
  margin: 0;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.search-input {
  width: 300px;
}

.header-btn {
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.header-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.24);
}

.category-sidebar,
.knowledge-content {
  height: 100%;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
}

.category-sidebar {
  padding: 18px;
}

.sidebar-header,
.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.sidebar-header h3,
.content-title {
  margin: 0;
  font-size: 20px;
  color: #0f172a;
}

.sidebar-header span,
.content-subtitle {
  color: #64748b;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px;
  border: 1px solid #e5edf9;
  border-radius: 14px;
  background: #f8fbff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-item.active,
.category-item:hover {
  border-color: #93c5fd;
  background: #eef6ff;
  transform: translateY(-1px);
}

.category-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: rgba(64, 158, 255, 0.12);
}

.category-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.category-info strong {
  color: #0f172a;
}

.category-info span {
  color: #64748b;
  font-size: 13px;
}

.knowledge-content {
  padding: 20px;
}

.content-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0 20px;
}

.stats-chip {
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #f1f7ff 100%);
  border: 1px solid #e4eefb;
}

.chip-label {
  display: block;
  font-size: 12px;
  color: #64748b;
}

.chip-value {
  display: block;
  margin-top: 6px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.knowledge-card,
.knowledge-list-item {
  background: #fff;
  border: 1px solid #e8eef7;
  border-radius: 18px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.knowledge-card:hover,
.knowledge-list-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 32px rgba(15, 23, 42, 0.08);
}

.card-image {
  position: relative;
  height: 180px;
}

.card-image img,
.list-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.favorite-toggle,
.favorite-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.favorite-toggle {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #94a3b8;
}

.favorite-inline {
  padding: 8px 12px;
  border-radius: 999px;
  background: #fff7ed;
  color: #f59e0b;
}

.favorite-toggle.active,
.favorite-inline.active {
  color: #f59e0b;
  background: #fff1c2;
}

.favorite-toggle:disabled,
.favorite-inline:disabled {
  cursor: wait;
  opacity: 0.7;
}

.card-content {
  padding: 18px;
}

.card-category-row,
.list-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.card-category,
.list-category {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eef6ff;
  color: #2563eb;
  font-size: 12px;
}

.card-date {
  font-size: 12px;
  color: #64748b;
}

.card-title,
.list-title {
  margin: 14px 0 10px;
  color: #0f172a;
  font-size: 18px;
  line-height: 1.5;
}

.card-summary,
.list-summary {
  margin: 0;
  color: #475569;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta,
.list-meta,
.history-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 14px;
  color: #64748b;
  font-size: 13px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.favorite-text {
  color: #f59e0b;
}

.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.knowledge-list-item {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
}

.list-image {
  min-height: 180px;
}

.list-info {
  padding: 18px 20px;
}

.loading-container,
.empty-container {
  padding: 24px 0;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.history-drawer {
  min-height: 100%;
}

.history-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.history-summary > div {
  padding: 14px;
  border-radius: 14px;
  background: #f8fbff;
  border: 1px solid #e4eefb;
}

.history-summary strong {
  display: block;
  font-size: 22px;
  color: #0f172a;
}

.history-summary span {
  color: #64748b;
  font-size: 13px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid #e8eef7;
}

.history-title {
  font-weight: 600;
  color: #0f172a;
}

.history-category {
  margin-top: 4px;
  color: #2563eb;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .knowledge-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .page-header,
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    width: 100%;
  }

  .content-stats {
    grid-template-columns: 1fr;
  }

  .knowledge-list-item {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .knowledge-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .knowledge-content,
  .category-sidebar {
    padding: 16px;
  }
}
</style>
