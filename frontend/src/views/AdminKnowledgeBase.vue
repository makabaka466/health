<template>
  <div class="admin-kb-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="filters.keyword" placeholder="搜索标题/内容/来源" clearable class="search-input" @keyup.enter="loadDocs" />
        <el-input v-model="filters.category" placeholder="分类" clearable class="category-input" @keyup.enter="loadDocs" />
        <el-switch v-model="filters.activeOnly" active-text="仅启用" inactive-text="全部" @change="loadDocs" />
        <el-button type="primary" @click="loadDocs">查询</el-button>
        <el-button type="success" @click="openCreateDialog">新增知识文档</el-button>
      </div>
    </el-card>

    <el-card shadow="hover">
      <el-table :data="docs" v-loading="loading" border>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags || []" :key="`${row.id}-${tag}`" size="small" class="tag-item">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" min-width="160" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text @click="openEditDialog(row)">编辑</el-button>
            <el-button type="danger" text @click="removeDoc(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :total="total"
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          @current-change="loadDocs"
          @size-change="loadDocs"
        />
      </div>
    </el-card>

    <el-dialog v-model="editorVisible" :title="isEditing ? '编辑知识文档' : '新增知识文档'" width="760px">
      <el-form ref="formRef" :model="editor" :rules="rules" label-width="90px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="editor.title" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="editor.category" placeholder="如：高血压、糖尿病、运动处方" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="editor.source" placeholder="如：国家卫健委指南" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="editor.tagsText" placeholder="多个标签用英文逗号分隔" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="editor.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="正文" prop="content">
          <el-input v-model="editor.content" type="textarea" :rows="10" placeholder="请输入知识内容，建议分段描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveDoc">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '../api/knowledge'

const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const docs = ref([])

const filters = reactive({
  keyword: '',
  category: '',
  activeOnly: false
})

const editorVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formRef = ref()
const editor = reactive({
  title: '',
  category: '',
  content: '',
  source: '',
  tagsText: '',
  is_active: true
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category: [{ required: true, message: '请输入分类', trigger: 'blur' }],
  content: [{ required: true, message: '请输入正文', trigger: 'blur' }]
}

const parseTags = (text) =>
  text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

const loadDocs = async () => {
  loading.value = true
  try {
    const data = await knowledgeApi.getRagDocs({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      category: filters.category || undefined,
      active_only: filters.activeOnly || undefined
    })
    docs.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载知识库失败')
  } finally {
    loading.value = false
  }
}

const resetEditor = () => {
  editor.title = ''
  editor.category = ''
  editor.content = ''
  editor.source = ''
  editor.tagsText = ''
  editor.is_active = true
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
  editor.content = row.content
  editor.source = row.source || ''
  editor.tagsText = (row.tags || []).join(',')
  editor.is_active = !!row.is_active
  editorVisible.value = true
}

const saveDoc = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const payload = {
    title: editor.title,
    category: editor.category,
    content: editor.content,
    source: editor.source || null,
    tags: parseTags(editor.tagsText),
    is_active: editor.is_active
  }

  saving.value = true
  try {
    if (isEditing.value && editingId.value) {
      await knowledgeApi.updateRagDoc(editingId.value, payload)
      ElMessage.success('知识文档已更新')
    } else {
      await knowledgeApi.createRagDoc(payload)
      ElMessage.success('知识文档已创建')
    }
    editorVisible.value = false
    await loadDocs()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const removeDoc = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除文档《${row.title}》？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await knowledgeApi.deleteRagDoc(row.id)
    ElMessage.success('删除成功')
    await loadDocs()
  } catch {
    // cancel
  }
}

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadDocs)
</script>

<style scoped>
.toolbar-card {
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.search-input {
  width: 260px;
}

.category-input {
  width: 180px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.tag-item {
  margin-right: 6px;
  margin-bottom: 4px;
}
</style>
