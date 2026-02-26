<template>
  <div class="knowledge-center-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#409EFF">
            <Reading />
          </el-icon>
        </div>
        <div class="header-text">
          <h1>健康知识中心</h1>
          <p>获取专业的健康知识和养生指导</p>
        </div>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索健康知识..."
          class="search-input"
          @keyup.enter="searchKnowledge"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button class="header-btn" @click="loadFavorites">我的收藏</el-button>
        <el-button class="header-btn" @click="loadReadHistory">阅读记录</el-button>
      </div>
    </div>
    
    <div class="content-section">
      <el-row :gutter="24">
        <el-col :xs="24" :sm="8" :md="6" :lg="5">
          <div class="category-sidebar">
            <div class="sidebar-header">
              <h3>知识分类</h3>
            </div>
            <div class="category-list">
              <div 
                v-for="category in categories" 
                :key="category.id"
                class="category-item"
                :class="{ active: selectedCategory === category.id }"
                @click="selectCategory(category.id)"
              >
                <div class="category-icon">
                  <el-icon size="20" :color="category.color">
                    <component :is="category.icon" />
                  </el-icon>
                </div>
                <div class="category-info">
                  <h4>{{ category.name }}</h4>
                  <p>{{ category.count }} 篇文章</p>
                </div>
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="16" :md="18" :lg="19">
          <div class="knowledge-content">
            <div class="content-header">
              <div class="breadcrumb">
                <span>首页</span>
                <el-icon><ArrowRight /></el-icon>
                <span>知识中心</span>
                <el-icon><ArrowRight /></el-icon>
                <span>{{ getCurrentCategoryName() }}</span>
              </div>
              <div class="view-options">
                <el-radio-group v-model="viewMode" size="small">
                  <el-radio-button label="grid">
                    <el-icon><Grid /></el-icon>
                  </el-radio-button>
                  <el-radio-button label="list">
                    <el-icon><List /></el-icon>
                  </el-radio-button>
                </el-radio-group>
              </div>
            </div>
            
            <div v-if="loading" class="loading-container">
              <el-skeleton :rows="3" animated />
            </div>
            
            <div v-else-if="knowledgeItems.length === 0" class="empty-container">
              <el-empty description="暂无相关知识内容">
                <el-button type="primary">推荐内容</el-button>
              </el-empty>
            </div>
            
            <div v-else>
              <!-- 网格视图 -->
              <div v-if="viewMode === 'grid'" class="knowledge-grid">
                <el-card 
                  v-for="item in knowledgeItems" 
                  :key="item.id"
                  class="knowledge-card"
                  shadow="hover"
                  @click="openKnowledgeDetail(item)"
                >
                  <div class="card-image">
                    <img :src="item.cover_image || '/default-health.jpg'" :alt="item.title" />
                  </div>
                  <div class="card-content">
                    <div class="card-category">{{ item.category }}</div>
                    <h3 class="card-title">{{ item.title }}</h3>
                    <p class="card-summary">{{ item.summary }}</p>
                    <div class="card-meta">
                      <span class="meta-item">
                        <el-icon><View /></el-icon>
                        {{ item.view_count }}
                      </span>
                      <span class="meta-item">
                        <el-icon><Star /></el-icon>
                        {{ item.favorite_count }}
                      </span>
                      <span class="meta-item">
                        <el-icon><Clock /></el-icon>
                        {{ formatDate(item.created_at) }}
                      </span>
                    </div>
                  </div>
                </el-card>
              </div>
              
              <!-- 列表视图 -->
              <div v-else class="knowledge-list">
                <el-card 
                  v-for="item in knowledgeItems" 
                  :key="item.id"
                  class="knowledge-list-item"
                  shadow="hover"
                  @click="openKnowledgeDetail(item)"
                >
                  <div class="list-content">
                    <div class="list-image">
                      <img :src="item.cover_image || '/default-health.jpg'" :alt="item.title" />
                    </div>
                    <div class="list-info">
                      <div class="list-category">{{ item.category }}</div>
                      <h3 class="list-title">{{ item.title }}</h3>
                      <p class="list-summary">{{ item.summary }}</p>
                      <div class="list-meta">
                        <span class="meta-item">
                          <el-icon><View /></el-icon>
                          {{ item.view_count }}
                        </span>
                        <span class="meta-item">
                          <el-icon><Star /></el-icon>
                          {{ item.favorite_count }}
                        </span>
                        <span class="meta-item">
                          <el-icon><Clock /></el-icon>
                          {{ formatDate(item.created_at) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </el-card>
              </div>
              
              <!-- 分页 -->
              <div class="pagination-container">
                <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :page-sizes="[12, 24, 48]"
                  :total="totalItems"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleSizeChange"
                  @current-change="handleCurrentChange"
                />
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeApi } from '../api/knowledge'

const router = useRouter()
const searchQuery = ref('')
const selectedCategory = ref('all')
const viewMode = ref('grid')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(12)
const totalItems = ref(0)
const knowledgeItems = ref([])

const categories = ref([
  { id: 'all', name: '全部', count: 0, icon: 'Grid', color: '#409EFF' },
  { id: '慢性病管理', name: '慢性病管理', count: 0, icon: 'FirstAid', color: '#F56C6C' },
  { id: '饮食营养', name: '饮食营养', count: 0, icon: 'Food', color: '#67C23A' },
  { id: '心理健康', name: '心理健康', count: 0, icon: 'ChatDotRound', color: '#909399' },
  { id: '运动健身', name: '运动健身', count: 0, icon: 'TrendCharts', color: '#E6A23C' },
  { id: '老年健康', name: '老年健康', count: 0, icon: 'Clock', color: '#606266' },
  { id: '儿童健康', name: '儿童健康', count: 0, icon: 'User', color: '#409EFF' }
])

const getCurrentCategoryName = () => {
  const category = categories.value.find((item) => item.id === selectedCategory.value)
  return category ? category.name : '全部'
}

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

const selectCategory = (categoryId) => {
  selectedCategory.value = categoryId
  currentPage.value = 1
  loadKnowledgeItems()
}

const searchKnowledge = () => {
  currentPage.value = 1
  loadKnowledgeItems()
}

const loadKnowledgeItems = async () => {
  loading.value = true
  try {
    const response = await knowledgeApi.getArticles({
      page: currentPage.value,
      page_size: pageSize.value,
      category: selectedCategory.value === 'all' ? undefined : selectedCategory.value,
      keyword: searchQuery.value || undefined,
      sort_by: 'latest'
    })

    knowledgeItems.value = response.items || []
    totalItems.value = response.total || 0
    refreshCategoryCount()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载知识内容失败')
  } finally {
    loading.value = false
  }
}

const openKnowledgeDetail = (item) => {
  router.push(`/dashboard/knowledge-center/article/${item.id}`)
}

const loadFavorites = async () => {
  loading.value = true
  try {
    const response = await knowledgeApi.getFavorites({ page: 1, page_size: pageSize.value })
    knowledgeItems.value = response.items || []
    totalItems.value = response.total || 0
    selectedCategory.value = 'all'
    ElMessage.success('已切换到我的收藏')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载收藏失败')
  } finally {
    loading.value = false
  }
}

const loadReadHistory = async () => {
  try {
    const history = await knowledgeApi.getReadHistory(30)
    if (!history.length) {
      ElMessage.info('暂无阅读记录')
      return
    }
    const titles = history.slice(0, 6).map((item) => `《${item.article_title}》`).join('、')
    ElMessage.info(`最近阅读：${titles}`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载阅读记录失败')
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadKnowledgeItems()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  loadKnowledgeItems()
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadKnowledgeItems()
})
</script>

<style scoped>
.knowledge-center-container {
  max-width: 1680px;
  width: 100%;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #409EFF 0%, #36A3F5 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2);
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
  min-width: 420px;
}

.header-btn {
  height: 40px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  backdrop-filter: blur(8px);
}

.header-btn:hover {
  background: rgba(255, 255, 255, 0.28);
  color: #ffffff;
}

.content-section :deep(.el-row) {
  align-items: stretch;
}

.content-section :deep(.el-col) {
  display: flex;
}

.search-input {
  width: 320px;
}

:deep(.search-input .el-input__wrapper) {
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

:deep(.search-input .el-input__inner) {
  color: white;
}

:deep(.search-input .el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.7);
}

.category-sidebar {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.category-list {
  padding: 16px;
  flex: 1;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.3s ease;
  margin-bottom: 8px;
}

.category-item:hover {
  background: #f8fafc;
}

.category-item.active {
  background: #e3f2fd;
  border-left: 3px solid #409EFF;
}

.category-icon {
  width: 40px;
  height: 40px;
  background: #f1f5f9;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.category-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.category-info p {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}

.knowledge-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 24px;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 14px;
}

.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
  align-items: stretch;
}

.knowledge-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 16px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.knowledge-card .el-card__body) {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.knowledge-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-image {
  height: 160px;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.card-category {
  display: inline-block;
  padding: 4px 8px;
  background: #e3f2fd;
  color: #409EFF;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
  line-height: 1.4;
  min-height: 44px;
}

.card-summary {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 16px;
  line-height: 1.5;
  line-clamp: 2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #94a3b8;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.knowledge-list-item {
  cursor: pointer;
  transition: all 0.3s ease;
}

.knowledge-list-item:hover {
  transform: translateX(4px);
}

.list-content {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

.list-image {
  width: 120px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.list-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.list-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.list-category {
  display: inline-block;
  padding: 2px 6px;
  background: #e3f2fd;
  color: #409EFF;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
}

.list-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.list-summary {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
  line-height: 1.4;
  line-clamp: 2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.list-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #94a3b8;
  margin-top: auto;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .header-actions {
    min-width: 0;
    justify-content: stretch;
    gap: 8px;
  }

  .header-btn {
    flex: 1;
  }
  
  .search-input {
    width: 100%;
  }
  
  .knowledge-grid {
    grid-template-columns: 1fr;
  }
  
  .list-content {
    flex-direction: column;
  }
  
  .list-image {
    width: 100%;
    height: 160px;
  }
}
</style>
