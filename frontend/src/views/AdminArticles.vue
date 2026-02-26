<template>
  <div class="admin-articles-container">
    <div class="page-header">
      <div>
        <h1>文章管理</h1>
        <p>创建、编辑和删除健康科普文章</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建文章
      </el-button>
    </div>

    <el-card shadow="hover" class="filter-card">
      <el-row :gutter="12">
        <el-col :span="8">
          <el-input v-model="filters.keyword" placeholder="按标题/摘要搜索" clearable @keyup.enter="loadArticles" />
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="分类" clearable style="width: 100%">
            <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.sortBy" style="width: 100%">
            <el-option label="最新发布" value="latest" />
            <el-option label="热门浏览" value="hot" />
          </el-select>
        </el-col>
        <el-col :span="4" class="filter-actions">
          <el-button type="primary" @click="loadArticles">查询</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="hover">
      <el-table :data="articles" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="category" label="分类" width="130" />
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" class="tag-item">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="90" />
        <el-table-column prop="favorite_count" label="收藏" width="90" />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadArticles"
        />
      </div>
    </el-card>

    <el-dialog v-model="editorVisible" :title="isEditing ? '编辑文章' : '新建文章'" width="760px">
      <el-form ref="editorRef" :model="editor" :rules="rules" label-position="top">
        <el-row :gutter="12">
          <el-col :span="14">
            <el-form-item label="标题" prop="title">
              <el-input v-model="editor.title" placeholder="请输入文章标题" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="分类" prop="category">
              <el-select v-model="editor.category" style="width: 100%" placeholder="请选择分类">
                <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="摘要" prop="summary">
          <el-input v-model="editor.summary" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>

        <el-form-item label="封面图URL">
          <el-input v-model="editor.cover_image" placeholder="https://..." />
        </el-form-item>

        <el-form-item label="标签（英文逗号分隔）">
          <el-input v-model="editor.tagsText" placeholder="例如：血压,控盐,中老年" />
        </el-form-item>

        <el-form-item label="正文" prop="content">
          <el-input v-model="editor.content" type="textarea" :rows="10" maxlength="20000" show-word-limit />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveArticle">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '../api/knowledge'

const categories = ['慢性病管理', '饮食营养', '心理健康', '运动健身', '老年健康', '儿童健康']

const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const articles = ref([])

const filters = reactive({
  keyword: '',
  category: '',
  sortBy: 'latest'
})

const editorVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const editorRef = ref()
const editor = reactive({
  title: '',
  category: '',
  summary: '',
  content: '',
  cover_image: '',
  tagsText: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  summary: [{ required: true, message: '请输入摘要', trigger: 'blur' }],
  content: [{ required: true, message: '请输入正文', trigger: 'blur' }]
}

const parseTags = (text) =>
  text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

const loadArticles = async () => {
  loading.value = true
  try {
    const data = await knowledgeApi.getArticles({
      page: page.value,
      page_size: pageSize.value,
      category: filters.category || undefined,
      keyword: filters.keyword || undefined,
      sort_by: filters.sortBy
    })
    articles.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载文章失败')
  } finally {
    loading.value = false
  }
}

const resetEditor = () => {
  editor.title = ''
  editor.category = ''
  editor.summary = ''
  editor.content = ''
  editor.cover_image = ''
  editor.tagsText = ''
  editingId.value = null
}

const openCreateDialog = () => {
  isEditing.value = false
  resetEditor()
  editorVisible.value = true
}

const openEditDialog = (row) => {
  isEditing.value = true
  editingId.value = row.id
  editor.title = row.title
  editor.category = row.category
  editor.summary = row.summary || ''
  editor.content = row.content
  editor.cover_image = row.cover_image || ''
  editor.tagsText = (row.tags || []).join(',')
  editorVisible.value = true
}

const saveArticle = async () => {
  if (!editorRef.value) return
  const valid = await editorRef.value.validate().catch(() => false)
  if (!valid) return

  const payload = {
    title: editor.title,
    category: editor.category,
    summary: editor.summary,
    content: editor.content,
    cover_image: editor.cover_image || null,
    tags: parseTags(editor.tagsText)
  }

  saving.value = true
  try {
    if (isEditing.value && editingId.value) {
      await knowledgeApi.updateArticle(editingId.value, payload)
      ElMessage.success('文章已更新')
    } else {
      await knowledgeApi.createArticle(payload)
      ElMessage.success('文章已创建')
    }
    editorVisible.value = false
    await loadArticles()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除文章《${row.title}》？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await knowledgeApi.deleteArticle(row.id)
    ElMessage.success('删除成功')
    await loadArticles()
  } catch {
    // ignore cancel
  }
}

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadArticles)
</script>

<style scoped>
.admin-articles-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 26px;
}

.page-header p {
  margin: 6px 0 0;
  color: #64748b;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
}

.tag-item {
  margin-right: 6px;
  margin-bottom: 4px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
