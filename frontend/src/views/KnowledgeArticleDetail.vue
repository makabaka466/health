<template>
  <div class="knowledge-detail-page">
    <div class="detail-header-card">
      <el-button class="back-btn" text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回知识中心
      </el-button>

      <div class="header-main" v-if="article">
        <span class="category-chip">{{ article.category }}</span>
        <h1>{{ article.title }}</h1>
        <div class="meta-row">
          <span><el-icon><Clock /></el-icon>{{ formatDate(article.created_at) }}</span>
          <span><el-icon><View /></el-icon>{{ article.view_count }} 阅读</span>
          <span><el-icon><Star /></el-icon>{{ article.favorite_count }} 收藏</span>
        </div>
      </div>
    </div>

    <el-card class="detail-content-card" shadow="never" v-loading="loading">
      <template v-if="article">
        <div class="article-content" v-html="article.content"></div>
        <div class="actions-row">
          <el-button type="primary" @click="favoriteArticle">
            <el-icon><Star /></el-icon>
            收藏文章
          </el-button>
          <el-button @click="goBack">返回列表</el-button>
        </div>
      </template>
      <el-empty v-else-if="!loading" description="文章不存在或已删除" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeApi } from '../api/knowledge'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const article = ref(null)

const loadDetail = async () => {
  const articleId = Number(route.params.id)
  if (!articleId) {
    article.value = null
    return
  }

  loading.value = true
  try {
    article.value = await knowledgeApi.getArticleDetail(articleId)
  } catch (error) {
    article.value = null
    ElMessage.error(error?.response?.data?.detail || '加载文章详情失败')
  } finally {
    loading.value = false
  }
}

const favoriteArticle = async () => {
  if (!article.value) return
  try {
    await knowledgeApi.favoriteArticle(article.value.id)
    article.value.favorite_count += 1
    ElMessage.success('收藏成功')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '收藏失败')
  }
}

const goBack = () => {
  router.push('/dashboard/knowledge-center')
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

onMounted(loadDetail)
watch(() => route.params.id, loadDetail)
</script>

<style scoped>
.knowledge-detail-page {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.detail-header-card {
  border-radius: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #5ea8ff 0%, #7fc2ff 100%);
  color: #ffffff;
  box-shadow: 0 12px 28px rgba(64, 158, 255, 0.25);
}

.back-btn {
  color: #ffffff;
  margin-bottom: 8px;
}

.header-main h1 {
  margin: 8px 0 10px;
  font-size: 30px;
  line-height: 1.35;
}

.category-chip {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 12px;
}

.meta-row {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  opacity: 0.95;
}

.meta-row span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.detail-content-card {
  border-radius: 16px;
  border: 1px solid #e6effa;
}

.article-content {
  color: #334155;
  line-height: 1.9;
  font-size: 16px;
}

.actions-row {
  margin-top: 24px;
  display: flex;
  gap: 10px;
}

@media (max-width: 768px) {
  .detail-header-card {
    padding: 18px;
  }

  .header-main h1 {
    font-size: 24px;
  }
}
</style>
