<template>
  <div class="admin-health-records-page">
    <el-card shadow="hover">
      <template #header>
        <div class="header-row">
          <div>
            <div class="page-title">健康数据上传记录</div>
            <div class="page-subtitle">可查看公开数据详情，私密数据需输入对应私钥后查看</div>
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
              {{ row.is_public ? '公开' : '私密' }}
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
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
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

    <el-dialog v-model="privateKeyDialogVisible" title="输入私钥查看私密数据" width="520px">
      <el-form label-width="90px">
        <el-form-item label="记录信息">
          <span>#{{ pendingRow?.id || '-' }} / {{ pendingRow?.username || '-' }}</span>
        </el-form-item>
        <el-form-item label="私钥">
          <el-input
            v-model="privateKeyInput"
            type="password"
            show-password
            placeholder="请输入该条记录对应用户的钱包私钥"
            @keyup.enter="confirmPrivateView"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="privateKeyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="detailLoading" @click="confirmPrivateView">查看</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" title="健康记录详情" width="760px">
      <template v-if="activeDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="记录ID">{{ activeDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ activeDetail.username }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ recordTypeLabel(activeDetail.file_type) }}</el-descriptions-item>
          <el-descriptions-item label="可见性">{{ activeDetail.is_public ? '公开' : '私密' }}</el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ formatDate(activeDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(activeDetail.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <div class="detail-title">内容</div>

          <template v-if="activeDetail.file_type === 'text'">
            <el-table :data="manualMetricRows" size="small" border>
              <el-table-column prop="label" label="指标" width="180" />
              <el-table-column prop="value" label="数值" />
            </el-table>
            <div class="detail-notes" v-if="manualOtherText">
              <div class="detail-notes__title">其他说明</div>
              <div class="detail-notes__content">{{ manualOtherText }}</div>
            </div>
            <div class="detail-notes" v-else-if="manualRawContent">
              <div class="detail-notes__title">原始文本</div>
              <pre class="detail-content">{{ manualRawContent }}</pre>
            </div>
          </template>

          <template v-else>
            <div class="file-actions">
              <el-button type="primary" @click="downloadAttachment(activeDetail)">下载附件</el-button>
            </div>
          </template>
        </div>

        <div class="detail-section" v-if="activeDetail.onchain_data_id || activeDetail.onchain_verification_message">
          <div class="detail-title">链上校验</div>
          <div class="detail-line">状态：{{ activeDetail.onchain_verification_status || '-' }}</div>
          <div class="detail-line">结果：{{ activeDetail.onchain_verification_message || '-' }}</div>
          <div class="detail-line">Data ID：{{ activeDetail.onchain_data_id || '-' }}</div>
          <div class="detail-line">Tx Hash：{{ activeDetail.onchain_tx_hash || '-' }}</div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminHealthRecordDetail, getAdminHealthRecords } from '../../api/adminSystem'

const loading = ref(false)
const detailLoading = ref(false)
const records = ref([])
const total = ref(0)

const privateKeyDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const privateKeyInput = ref('')
const pendingRow = ref(null)
const activeDetail = ref(null)

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  file_type: ''
})

const parseDataContent = (content) => {
  if (!content) return { metrics: {}, other_text: '', raw_text: '' }
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed === 'object') {
      return {
        metrics: parsed.metrics || {},
        other_text: parsed.other_text || '',
        raw_text: ''
      }
    }
  } catch {
    return { metrics: {}, other_text: '', raw_text: content }
  }
  return { metrics: {}, other_text: '', raw_text: '' }
}

const displayMetric = (value, unit = '') => {
  if (value === null || value === undefined || value === '') return '-'
  return `${value}${unit}`
}

const manualParsed = computed(() => parseDataContent(activeDetail.value?.data_content || ''))

const manualMetricRows = computed(() => {
  const metrics = manualParsed.value.metrics || {}
  const bloodPressure = metrics.blood_pressure || (
    metrics.blood_pressure_diastolic != null && metrics.blood_pressure_systolic != null
      ? `${metrics.blood_pressure_diastolic}/${metrics.blood_pressure_systolic}`
      : ''
  )
  return [
    { label: '身高', value: displayMetric(metrics.height, ' cm') },
    { label: '体重', value: displayMetric(metrics.weight, ' kg') },
    { label: '血压', value: displayMetric(bloodPressure) },
    { label: '血脂', value: displayMetric(metrics.blood_lipid) },
    { label: '心率', value: displayMetric(metrics.heart_rate, ' 次/分') },
    { label: '血糖', value: displayMetric(metrics.blood_sugar) }
  ]
})

const manualOtherText = computed(() => manualParsed.value.other_text || '')
const manualRawContent = computed(() => manualParsed.value.raw_text || '')

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

const fetchDetail = async (recordId, privateKey = '') => {
  detailLoading.value = true
  try {
    const params = privateKey ? { private_key: privateKey } : {}
    const detail = await getAdminHealthRecordDetail(recordId, params)
    if (!detail.is_public && detail.requires_private_key) {
      ElMessage.error('私钥不正确，或无法解锁该隐私数据')
      return
    }
    activeDetail.value = detail
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '查看记录详情失败')
  } finally {
    detailLoading.value = false
  }
}

const handleView = async (row) => {
  pendingRow.value = row
  privateKeyInput.value = ''
  if (row.is_public) {
    await fetchDetail(row.id)
    return
  }
  privateKeyDialogVisible.value = true
}

const confirmPrivateView = async () => {
  const key = privateKeyInput.value.trim()
  if (!key) {
    ElMessage.warning('请输入私钥后再查看')
    return
  }
  const row = pendingRow.value
  if (!row) return
  privateKeyDialogVisible.value = false
  await fetchDetail(row.id, key)
}

const resolveFileExtension = (detail, mimeType) => {
  if (detail.file_type === 'pdf') return 'pdf'
  if (detail.file_type === 'word') {
    if ((mimeType || '').includes('msword')) return 'doc'
    return 'docx'
  }
  return 'bin'
}

const downloadAttachment = (detail) => {
  if (!detail?.pdf_data_base64) {
    ElMessage.warning('未找到附件内容')
    return
  }

  try {
    const parts = detail.pdf_data_base64.split(',')
    if (parts.length < 2) {
      ElMessage.error('附件数据格式不正确')
      return
    }

    const metadata = parts[0]
    const base64Body = parts[1]
    const mimeMatch = metadata.match(/data:(.*?);base64/i)
    const mimeType = detail.file_mime_type || mimeMatch?.[1] || 'application/octet-stream'

    const binary = window.atob(base64Body)
    const len = binary.length
    const bytes = new Uint8Array(len)
    for (let i = 0; i < len; i += 1) {
      bytes[i] = binary.charCodeAt(i)
    }

    const blob = new Blob([bytes], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const extension = resolveFileExtension(detail, mimeType)
    const filename = `${detail.data_title || `health-record-${detail.id}`}.${extension}`

    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('附件下载失败，请稍后重试')
  }
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

.detail-section {
  margin-top: 16px;
}

.detail-title {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.detail-content {
  margin: 0;
  max-height: 260px;
  overflow: auto;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  white-space: pre-wrap;
  word-break: break-word;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-line {
  color: #4b5563;
  line-height: 1.8;
  word-break: break-all;
}

.detail-notes {
  margin-top: 12px;
}

.detail-notes__title {
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 6px;
}

.detail-notes__content {
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
  color: #1f2937;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
