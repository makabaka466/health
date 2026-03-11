<template>
  <div class="knowledge-page">
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <el-input
          v-model="filters.keyword"
          :placeholder="labels.keywordPlaceholder"
          class="search-input"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select v-model="filters.category" :placeholder="labels.categoryPlaceholder" class="category-select" clearable>
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
        <el-switch v-model="filters.activeOnly" :active-text="labels.activeOnly" />
        <el-button type="primary" @click="handleSearch">{{ labels.search }}</el-button>
        <el-button @click="handleReset">{{ labels.reset }}</el-button>
        <el-button type="success" @click="openCreateDialog">{{ labels.createDoc }}</el-button>
        <el-button type="warning" @click="openImportDialog">{{ labels.importFiles }}</el-button>
        <el-button type="info" @click="seedDefaultDocs">{{ labels.seedDocs }}</el-button>
      </div>
      <div class="toolbar-tip">{{ summaryText }}</div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="docs" border stripe>
        <el-table-column prop="title" :label="labels.title" min-width="220" />
        <el-table-column prop="category" :label="labels.category" width="140" />
        <el-table-column prop="source" :label="labels.source" min-width="160">
          <template #default="scope">
            <span>{{ scope.row.source || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="labels.tags" min-width="180">
          <template #default="scope">
            <el-tag
              v-for="tag in scope.row.tags || []"
              :key="tag"
              size="small"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
            <span v-if="!(scope.row.tags || []).length">-</span>
          </template>
        </el-table-column>
        <el-table-column :label="labels.status" width="110">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'info'">
              {{ scope.row.is_active ? labels.enabled : labels.disabled }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="labels.updatedAt" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="labels.actions" width="220" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openEditDialog(scope.row)">{{ labels.edit }}</el-button>
            <el-button link type="danger" @click="removeDoc(scope.row)">{{ labels.delete }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50]"
          :total="total"
          @current-change="loadDocs"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="editorVisible" :title="isEditing ? labels.editDoc : labels.createDoc" width="720px">
      <el-form ref="formRef" :model="editor" :rules="rules" label-width="88px">
        <el-form-item :label="labels.title" prop="title">
          <el-input v-model="editor.title" :placeholder="labels.titlePlaceholder" />
        </el-form-item>
        <el-form-item :label="labels.category" prop="category">
          <el-select v-model="editor.category" style="width: 100%" :placeholder="labels.categoryPlaceholder" allow-create filterable default-first-option>
            <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item :label="labels.source">
          <el-input v-model="editor.source" :placeholder="labels.sourcePlaceholder" />
        </el-form-item>
        <el-form-item :label="labels.tags">
          <el-input v-model="editor.tagsText" :placeholder="labels.tagsPlaceholder" />
        </el-form-item>
        <el-form-item :label="labels.status">
          <el-switch v-model="editor.is_active" :active-text="labels.enabled" :inactive-text="labels.disabled" />
        </el-form-item>
        <el-form-item :label="labels.content" prop="content">
          <el-input
            v-model="editor.content"
            type="textarea"
            :rows="12"
            :placeholder="labels.contentPlaceholder"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editorVisible = false">{{ labels.cancel }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveDoc">{{ labels.save }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importVisible" :title="labels.importDialogTitle" width="720px">
      <el-form :model="importForm" label-width="100px">
        <el-form-item :label="labels.category">
          <el-select v-model="importForm.category" style="width: 100%" :placeholder="labels.categoryRequired" allow-create filterable default-first-option>
            <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item :label="labels.source">
          <el-input v-model="importForm.source" :placeholder="labels.importSourcePlaceholder" />
        </el-form-item>
        <el-form-item :label="labels.tags">
          <el-input v-model="importForm.tagsText" :placeholder="labels.tagsPlaceholder" />
        </el-form-item>
        <el-form-item :label="labels.status">
          <el-switch v-model="importForm.is_active" :active-text="labels.enabled" :inactive-text="labels.disabled" />
        </el-form-item>
        <el-form-item :label="labels.fileUpload">
          <el-upload
            ref="uploadRef"
            drag
            multiple
            :auto-upload="false"
            :limit="8"
            accept=".pdf,.docx"
            :on-change="handleUploadChange"
            :on-remove="handleUploadRemove"
            :file-list="importFiles"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">{{ labels.uploadHint }}</div>
            <template #tip>
              <div class="el-upload__tip">{{ labels.uploadTip }}</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeImportDialog">{{ labels.cancel }}</el-button>
        <el-button type="primary" :loading="importing" @click="submitImport">{{ labels.startImport }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '../api/knowledge'

const labels = {
  keywordPlaceholder: '\u8bf7\u8f93\u5165\u6807\u9898\u3001\u5185\u5bb9\u6216\u6765\u6e90\u5173\u952e\u8bcd',
  categoryPlaceholder: '\u8bf7\u9009\u62e9\u5206\u7c7b',
  categoryRequired: '\u8bf7\u9009\u62e9\u6216\u8f93\u5165\u5206\u7c7b',
  activeOnly: '\u4ec5\u770b\u542f\u7528',
  search: '\u67e5\u8be2',
  reset: '\u91cd\u7f6e',
  createDoc: '\u65b0\u589e\u6587\u6863',
  importFiles: '\u5bfc\u5165\u6587\u4ef6',
  seedDocs: '\u5bfc\u5165\u793a\u4f8b\u6570\u636e',
  title: '\u6807\u9898',
  category: '\u5206\u7c7b',
  source: '\u6765\u6e90',
  tags: '\u6807\u7b7e',
  status: '\u72b6\u6001',
  updatedAt: '\u66f4\u65b0\u65f6\u95f4',
  actions: '\u64cd\u4f5c',
  enabled: '\u542f\u7528',
  disabled: '\u505c\u7528',
  edit: '\u7f16\u8f91',
  delete: '\u5220\u9664',
  editDoc: '\u7f16\u8f91\u6587\u6863',
  titlePlaceholder: '\u8bf7\u8f93\u5165\u6587\u6863\u6807\u9898',
  sourcePlaceholder: '\u53ef\u9009\uff0c\u4f8b\u5982\uff1a\u4e34\u5e8a\u6307\u5357\u3001\u56fd\u5bb6\u89c4\u8303',
  importSourcePlaceholder: '\u53ef\u9009\uff0c\u4e0d\u586b\u65f6\u9ed8\u8ba4\u4f7f\u7528\u6587\u4ef6\u540d',
  tagsPlaceholder: '\u591a\u4e2a\u6807\u7b7e\u8bf7\u7528\u82f1\u6587\u9017\u53f7\u5206\u9694',
  content: '\u5185\u5bb9',
  contentPlaceholder: '\u8bf7\u8f93\u5165\u77e5\u8bc6\u5e93\u5185\u5bb9\uff0c\u5efa\u8bae\u6309\u6bb5\u843d\u7ec4\u7ec7',
  save: '\u4fdd\u5b58',
  cancel: '\u53d6\u6d88',
  importDialogTitle: '\u5bfc\u5165 PDF / Word \u6587\u6863',
  fileUpload: '\u9009\u62e9\u6587\u4ef6',
  uploadHint: '\u5c06 PDF \u6216 DOCX \u62d6\u5230\u6b64\u5904\uff0c\u6216\u70b9\u51fb\u9009\u62e9\u6587\u4ef6',
  uploadTip: '\u652f\u6301 PDF(.pdf) \u548c Word(.docx)\uff0c\u5355\u6b21\u6700\u591a 8 \u4e2a\u6587\u4ef6',
  startImport: '\u5f00\u59cb\u5bfc\u5165',
  loadFailed: '\u52a0\u8f7d\u77e5\u8bc6\u5e93\u5931\u8d25',
  createSuccess: '\u77e5\u8bc6\u6587\u6863\u5df2\u521b\u5efa',
  updateSuccess: '\u77e5\u8bc6\u6587\u6863\u5df2\u66f4\u65b0',
  saveFailed: '\u4fdd\u5b58\u5931\u8d25',
  deleteConfirmTitle: '\u5220\u9664\u786e\u8ba4',
  deleteConfirmPrefix: '\u786e\u8ba4\u5220\u9664\u77e5\u8bc6\u6587\u6863\uff1a',
  deleteSuccess: '\u5220\u9664\u6210\u529f',
  importNeedCategory: '\u8bf7\u5148\u9009\u62e9\u5bfc\u5165\u5206\u7c7b',
  importNeedFiles: '\u8bf7\u81f3\u5c11\u9009\u62e9\u4e00\u4e2a\u6587\u4ef6',
  importSuccessSuffix: '\u4e2a\u6587\u6863',
  seedConfirm: '\u786e\u5b9a\u5bfc\u5165\u793a\u4f8b\u77e5\u8bc6\u6570\u636e\u5417\uff1f',
  notice: '\u63d0\u793a',
  confirm: '\u786e\u5b9a',
  sampleSummary: '\u53ef\u4ee5\u5148\u5bfc\u5165\u793a\u4f8b\u6570\u636e\uff0c\u4e5f\u53ef\u901a\u8fc7 PDF / Word \u6587\u6863\u5feb\u901f\u5165\u5e93',
  countSummaryPrefix: '\u5f53\u524d\u5171\u6709',
  countSummarySuffix: '\u6761\u77e5\u8bc6\u6587\u6863',
  importSkippedPrefix: '\u4ee5\u4e0b\u6587\u4ef6\u672a\u5bfc\u5165\uff1a'
}

const categories = [
  '\u6162\u6027\u75c5\u7ba1\u7406',
  '\u996e\u98df\u8425\u517b',
  '\u5fc3\u7406\u5065\u5eb7',
  '\u75be\u75c5\u9884\u9632',
  '\u8fd0\u52a8\u5eb7\u590d',
  '\u4e2d\u533b\u517b\u751f',
  '\u8001\u5e74\u5065\u5eb7',
  '\u513f\u7ae5\u5065\u5eb7'
]

const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
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

const importVisible = ref(false)
const uploadRef = ref()
const importFiles = ref([])
const importForm = reactive({
  category: '',
  source: '',
  tagsText: '',
  is_active: true
})

const rules = {
  title: [{ required: true, message: labels.titlePlaceholder, trigger: 'blur' }],
  category: [{ required: true, message: labels.categoryRequired, trigger: 'change' }],
  content: [{ required: true, message: labels.contentPlaceholder, trigger: 'blur' }]
}

const summaryText = computed(() => {
  if (!total.value) {
    return labels.sampleSummary
  }
  return `${labels.countSummaryPrefix} ${total.value} ${labels.countSummarySuffix}`
})

const parseTags = (text) =>
  (text || '')
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
    ElMessage.error(error?.response?.data?.detail || labels.loadFailed)
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

const resetImportForm = () => {
  importForm.category = ''
  importForm.source = ''
  importForm.tagsText = ''
  importForm.is_active = true
  importFiles.value = []
}

const handleSearch = async () => {
  page.value = 1
  await loadDocs()
}

const handleReset = async () => {
  filters.keyword = ''
  filters.category = ''
  filters.activeOnly = false
  page.value = 1
  await loadDocs()
}

const handlePageSizeChange = async () => {
  page.value = 1
  await loadDocs()
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
      ElMessage.success(labels.updateSuccess)
    } else {
      await knowledgeApi.createRagDoc(payload)
      ElMessage.success(labels.createSuccess)
    }
    editorVisible.value = false
    await loadDocs()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || labels.saveFailed)
  } finally {
    saving.value = false
  }
}

const removeDoc = async (row) => {
  try {
    await ElMessageBox.confirm(
      `${labels.deleteConfirmPrefix}《${row.title}》？`,
      labels.deleteConfirmTitle,
      {
        confirmButtonText: labels.confirm,
        cancelButtonText: labels.cancel,
        type: 'warning'
      }
    )

    await knowledgeApi.deleteRagDoc(row.id)
    ElMessage.success(labels.deleteSuccess)
    await loadDocs()
  } catch {
    return
  }
}

const openImportDialog = () => {
  resetImportForm()
  importVisible.value = true
}

const closeImportDialog = () => {
  importVisible.value = false
  resetImportForm()
}

const handleUploadChange = (_file, fileList) => {
  importFiles.value = fileList
}

const handleUploadRemove = (_file, fileList) => {
  importFiles.value = fileList
}

const submitImport = async () => {
  if (!importForm.category) {
    ElMessage.warning(labels.importNeedCategory)
    return
  }
  if (!importFiles.value.length) {
    ElMessage.warning(labels.importNeedFiles)
    return
  }

  const formData = new FormData()
  importFiles.value.forEach((fileItem) => {
    formData.append('files', fileItem.raw)
  })
  formData.append('category', importForm.category)
  formData.append('source', importForm.source || '')
  formData.append('tags', importForm.tagsText || '')
  formData.append('is_active', String(importForm.is_active))

  importing.value = true
  try {
    const result = await knowledgeApi.importRagDocs(formData)
    ElMessage.success(result.message || `${labels.importFiles}${result.imported_count}${labels.importSuccessSuffix}`)
    if (result.skipped_files?.length) {
      ElMessage.warning(`${labels.importSkippedPrefix} ${result.skipped_files.join('、')}`)
    }
    closeImportDialog()
    await loadDocs()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || labels.saveFailed)
  } finally {
    importing.value = false
  }
}

const seedDefaultDocs = async () => {
  try {
    await ElMessageBox.confirm(labels.seedConfirm, labels.notice, {
      confirmButtonText: labels.confirm,
      cancelButtonText: labels.cancel,
      type: 'info'
    })

    const result = await knowledgeApi.seedRagDocs()
    ElMessage.success(result.message)
    await loadDocs()
  } catch {
    return
  }
}

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadDocs)
</script>

<style scoped>
.knowledge-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar-card {
  border-radius: 16px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-tip {
  margin-top: 12px;
  color: #64748b;
  font-size: 13px;
}

.search-input {
  width: 280px;
}

.category-select {
  width: 200px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.tag-item {
  margin-right: 6px;
}

:deep(.el-upload-dragger) {
  width: 100%;
}

@media (max-width: 768px) {
  .search-input,
  .category-select {
    width: 100%;
  }
}
</style>
