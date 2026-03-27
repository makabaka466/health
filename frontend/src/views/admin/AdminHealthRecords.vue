<template>
  <div class="admin-health-records-page">
    <el-card shadow="hover">
      <template #header>
        <div class="header-row">
          <div>
            <div class="page-title">健康数据上传记录</div>
            <div class="page-subtitle">仅展示上传摘要与时间，不展示具体健康内容。</div>
          </div>
          <div class="header-actions">
            <el-input
              v-model="query.keyword"
              placeholder="按用户名搜索"
              clearable
              style="width: 220px"
              @keyup.enter="handleSearch"
            />
            <el-select v-model="query.file_type" placeholder="记录类型" clearable style="width: 160px">
              <el-option label="手动录入" value="text" />
              <el-option label="PDF" value="pdf" />
              <el-option label="Word" value="word" />
            </el-select>
            <el-button type="primary" @click="handleSearch">查询</el-button>
          </div>
        </div>
      </template>

      <el-table :data="records" stripe border v-loading="loading">
        <el-table-column prop="id" label="记录ID" width="90" />
        <el-table-column prop="user_id" label="用户ID" width="90" />
        <el-table-column prop="username" label="用户名" min-width="160" />
        <el-table-column label="记录摘要" min-width="180">
          <template #default="{ row }">
            <el-tag :type="recordTypeTagType(row.file_type)" size="small">
              {{ recordTypeLabel(row.file_type) }}
            </el-tag>
            <el-tag :type="row.is_public ? 'success' : 'warning'" size="small" style="margin-left: 8px">
              {{ row.is_public ? '公开' : '保密' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="附件" width="100">
          <template #default="{ row }">
            {{ row.has_attachment ? '有' : '无' }}
          </template>
        </el-table-column>
        <el-table-column label="链上存证" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_onchain ? 'success' : 'info'" size="small">
              {{ row.is_onchain ? '已存证' : '未存证' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="最近更新" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminHealthRecords } from '../../api/adminSystem'

const loading = ref(false)
const records = ref([])
const total = ref(0)
const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  file_type: ''
})

const recordTypeLabel = (fileType) => {
  if (fileType === 'pdf') return 'PDF 上传'
  if (fileType === 'word') return 'Word 上传'
  return '手动录入'
}

const recordTypeTagType = (fileType) => {
  if (fileType === 'pdf') return 'info'
  if (fileType === 'word') return 'warning'
  return 'primary'
}

const formatDate = (value) => (value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-')

const loadRecords = async () => {
  loading.value = true
  try {
    const data = await getAdminHealthRecords({ ...query })
    records.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载健康数据上传记录失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.page = 1
  loadRecords()
}

onMounted(loadRecords)
</script>

<style scoped>
.admin-health-records-page {
  width: 100%;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.page-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #6b7280;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}
</style>
