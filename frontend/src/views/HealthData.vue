<template>
  <div class="health-data-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#409EFF">
            <DataAnalysis />
          </el-icon>
        </div>
        <div class="header-text">
          <h1>健康数据</h1>
          <p>管理和查看您的健康数据记录</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button v-if="hasLockedPrivateRecords" class="unlock-btn" @click="unlockPrivateData">
          {{ unlockButtonText }}
        </el-button>
        <el-button v-if="unlockedPrivateKey" class="unlock-btn" @click="clearUnlockedPrivateData">
          {{ clearUnlockText }}
        </el-button>
        <el-button type="primary" class="add-btn" @click="openManualDialog">
          <el-icon><Plus /></el-icon>
          手动录入
        </el-button>
        <el-button class="upload-btn" @click="openPdfDialog">
          <el-icon><UploadFilled /></el-icon>
          上传PDF
        </el-button>
      </div>
    </div>
    
    <div class="content-section">
      <el-row :gutter="24">
        <el-col :span="24">
          <el-card class="stats-card" shadow="hover">
            <div class="stats-grid">
              <div v-for="item in statsCards" :key="item.title" class="stat-item">
                <div class="stat-icon" :style="{ color: item.color }">
                  <el-icon size="22"><component :is="item.icon" /></el-icon>
                </div>
                <div class="stat-info">
                  <h3>{{ item.title }}</h3>
                  <p class="stat-value">{{ item.value }}<span class="stat-unit">{{ item.unit }}</span></p>
                  <p class="stat-desc">{{ item.desc }}</p>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="24" style="margin-top: 24px;">
        <el-col :span="16">
          <el-card class="chart-card" shadow="hover">
            <div class="card-header">
              <h3>健康趋势</h3>
              <el-button type="text" @click="refreshData">刷新</el-button>
            </div>
            <div class="chart-placeholder">
              <div class="placeholder-content" v-if="healthRecords.length === 0">
                <el-icon size="48" color="#cbd5e1"><TrendCharts /></el-icon>
                <p>暂无数据，请添加健康记录</p>
              </div>
              <div v-else>
                <el-table :data="healthRecords" style="width: 100%" max-height="320">
                  <el-table-column prop="recorded_at" label="记录时间" width="180">
                    <template #default="scope">
                      {{ formatDate(scope.row.recorded_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="height" label="身高(cm)" width="100" />
                  <el-table-column prop="weight" label="体重(kg)" width="100" />
                  <el-table-column prop="blood_pressure" label="血压(舒/收)" width="120" />
                  <el-table-column prop="blood_lipid" label="血脂" width="100" />
                  <el-table-column prop="heart_rate" label="心率" width="100" />
                  <el-table-column prop="blood_sugar" label="血糖" width="100" />
                  <el-table-column :label="privacyColumnText" width="150">
                    <template #default="scope">
                      <el-space :size="6" wrap>
                        <el-tag :type="scope.row.is_private ? 'warning' : 'success'" size="small">
                          {{ scope.row.is_private ? privateText : publicText }}
                        </el-tag>
                        <el-tag v-if="scope.row.requires_private_key" type="danger" size="small">
                          {{ lockedTagText }}
                        </el-tag>
                      </el-space>
                    </template>
                  </el-table-column>
                  <el-table-column label="记录类型" width="100">
                    <template #default="scope">
                      <el-tag :type="scope.row.record_type === 'pdf' ? 'info' : 'primary'" size="small">
                        {{ scope.row.record_type === 'pdf' ? 'PDF' : '手动' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="PDF文件" width="120">
                    <template #default="scope">
                      <el-button v-if="scope.row.health_data_file" type="primary" text @click="openPdf(scope.row)">
                        查看PDF
                      </el-button>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="actionsColumnText">
                    <template #default="scope">
                      <el-button v-if="scope.row.requires_private_key" type="primary" text @click="unlockPrivateData">
                        {{ unlockButtonText }}
                      </el-button>
                      <el-button type="text" @click="editRecord(scope.row)">
                        {{ scope.row.record_type === 'pdf' ? replacePdfText : editText }}
                      </el-button>
                      <el-button type="text" style="color: #f56c6c" @click="deleteRecord(scope.row)">{{ deleteText }}</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card class="recent-card" shadow="hover">
            <div class="card-header">
              <h3>数据分析</h3>
              <el-button type="text" @click="analyzeHealthData">分析</el-button>
            </div>
            <div class="analysis-result" v-if="healthAnalysis.recommendations">
              <div class="analysis-item">
                <h4>健康建议</h4>
                <ul>
                  <li v-for="recommendation in healthAnalysis.recommendations" :key="recommendation">
                    {{ recommendation }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="placeholder-content" v-else>
              <el-icon size="48" color="#cbd5e1"><DataAnalysis /></el-icon>
              <p>点击分析获取健康建议</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 添加/编辑健康数据对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑健康数据' : '添加健康数据'"
      width="600px"
    >
      <el-form :model="healthForm" :rules="healthRules" ref="healthFormRef" label-width="120px">
        <template v-if="formMode === 'manual'">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="体重(kg)" prop="weight">
              <el-input-number v-model="healthForm.weight" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身高(cm)" prop="height">
              <el-input-number v-model="healthForm.height" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="血压(舒/收)" prop="blood_pressure">
              <el-input
                v-model="healthForm.blood_pressure"
                placeholder="例如 80/120（前舒张压，后收缩压）"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="血脂" prop="blood_lipid">
              <el-input-number v-model="healthForm.blood_lipid" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="心率" prop="heart_rate">
              <el-input-number v-model="healthForm.heart_rate" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="血糖" prop="blood_sugar">
              <el-input-number v-model="healthForm.blood_sugar" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="其他说明" prop="other_text">
          <el-input
            v-model="healthForm.other_text"
            type="textarea"
            :rows="3"
            placeholder="可填写如：睡眠情况、饮食变化、服药信息等"
          />
        </el-form-item>
        
        <el-form-item label="记录时间" prop="recorded_at">
          <el-date-picker
            v-model="healthForm.recorded_at"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="隐私保护">
          <el-switch
            v-model="healthForm.is_private"
            active-text="保密"
            inactive-text="公开"
          />
        </el-form-item>
        </template>

        <template v-else>
        <el-form-item label="记录时间" prop="recorded_at">
          <el-date-picker
            v-model="healthForm.recorded_at"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="隐私保护">
          <el-switch
            v-model="healthForm.is_private"
            active-text="保密"
            inactive-text="公开"
            disabled
          />
        </el-form-item>

        <el-form-item label="健康数据PDF">
          <div class="upload-row">
            <el-upload
              accept="application/pdf"
              :show-file-list="false"
              :auto-upload="false"
              :on-change="handlePdfFileChange"
            >
              <el-button type="primary" plain>上传 PDF</el-button>
            </el-upload>
            <el-button v-if="healthForm.health_data_file" text type="danger" @click="removeFile">
              移除文件
            </el-button>
          </div>
          <el-alert
            title="仅支持 PDF，文件会单独作为一条记录入库，且默认保密"
            type="info"
            show-icon
            :closable="false"
            style="margin-top: 10px"
          />
          <div v-if="healthForm.health_data_file" class="upload-preview">
            <el-tag type="info">{{ healthForm.health_data_file_name || '已上传PDF' }}</el-tag>
          </div>
        </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveHealthData" :loading="saving">
            {{ isEditing ? '更新' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { healthApi } from '../api/health'

const healthRecords = ref([])
const healthSummary = ref({})
const healthAnalysis = ref({})
const dialogVisible = ref(false)
const isEditing = ref(false)
const formMode = ref('manual')
const saving = ref(false)
const healthFormRef = ref()
const unlockedPrivateKey = ref('')

const healthForm = ref({
  weight: null,
  height: null,
  blood_pressure: '',
  blood_lipid: null,
  heart_rate: null,
  blood_sugar: null,
  other_text: '',
  record_type: 'manual',
  is_private: false,
  health_data_file_name: null,
  health_data_file: null,
  recorded_at: new Date()
})

const unlockButtonText = '\u89e3\u9501\u79c1\u5bc6\u6570\u636e'
const clearUnlockText = '\u6e05\u9664\u89e3\u9501'
const unlockSuccessText = '\u5df2\u89e3\u9501\u79c1\u5bc6\u5065\u5eb7\u6570\u636e'
const unlockRequiredText = '\u8bf7\u8f93\u5165\u6ce8\u518c\u65f6\u4fdd\u5b58\u7684\u79c1\u94a5\u4ee5\u89e3\u9501\u79c1\u5bc6\u6570\u636e'
const unlockDialogTitle = '\u89e3\u9501\u79c1\u5bc6\u6570\u636e'
const unlockPlaceholder = '\u8bf7\u8f93\u5165 0x \u5f00\u5934\u7684\u79c1\u94a5'
const unlockCanceledText = '\u5df2\u53d6\u6d88\u89e3\u9501'
const lockedRecordText = '\u8be5\u8bb0\u5f55\u4e3a\u79c1\u5bc6\u6570\u636e\uff0c\u9700\u5148\u89e3\u9501'
const unlockClearedText = '\u5df2\u6e05\u9664\u79c1\u94a5\u89e3\u9501\u72b6\u6001'
const unlockInvalidText = '\u79c1\u94a5\u65e0\u6548\uff0c\u5df2\u6e05\u9664\u89e3\u9501\u72b6\u6001'
const lockedTagText = '\u672a\u89e3\u9501'
const privacyColumnText = '\u9690\u79c1'
const privateText = '\u4fdd\u5bc6'
const publicText = '\u516c\u5f00'
const actionsColumnText = '\u64cd\u4f5c'
const editText = '\u7f16\u8f91'
const replacePdfText = '\u66ff\u6362PDF'
const deleteText = '\u5220\u9664'
const loadFailedText = '\u52a0\u8f7d\u5065\u5eb7\u6570\u636e\u5931\u8d25'
const analysisSuccessText = '\u5065\u5eb7\u5206\u6790\u5b8c\u6210'
const analysisFailedText = '\u5065\u5eb7\u5206\u6790\u5931\u8d25'

const requestParams = computed(() => (
  unlockedPrivateKey.value ? { private_key: unlockedPrivateKey.value } : {}
))

const healthRules = {
  weight: [{ type: 'number', message: '请输入有效的体重', trigger: 'blur' }],
  height: [{ type: 'number', message: '请输入有效的身高', trigger: 'blur' }],
  blood_pressure: [{
    validator: (_rule, value, callback) => {
      if (!value) {
        callback()
        return
      }
      if (!/^\s*\d{2,3}\s*\/\s*\d{2,3}\s*$/.test(value)) {
        callback(new Error('血压格式应为 舒张压/收缩压，例如 80/120'))
        return
      }
      callback()
    },
    trigger: 'blur'
  }],
  blood_lipid: [{ type: 'number', message: '请输入有效的血脂', trigger: 'blur' }],
  heart_rate: [{ type: 'number', message: '请输入有效的心率', trigger: 'blur' }],
  blood_sugar: [{ type: 'number', message: '请输入有效的血糖', trigger: 'blur' }],
  other_text: [{ max: 1000, message: '其他说明最多1000字', trigger: 'blur' }]
}

const parseBloodPressure = (value) => {
  if (!value || typeof value !== 'string') {
    return { diastolic: null, systolic: null }
  }
  const normalized = value.replace(/\s+/g, '')
  const parts = normalized.split('/')
  if (parts.length !== 2) {
    return { diastolic: null, systolic: null }
  }

  const diastolic = Number(parts[0])
  const systolic = Number(parts[1])
  if (Number.isNaN(diastolic) || Number.isNaN(systolic)) {
    return { diastolic: null, systolic: null }
  }

  return { diastolic, systolic }
}

const parseDataContent = (content) => {
  if (!content) {
    return { metrics: {}, other_text: '' }
  }
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed === 'object') {
      return {
        metrics: parsed.metrics || {},
        other_text: parsed.other_text || ''
      }
    }
  } catch {
    return { metrics: {}, other_text: content }
  }
  return { metrics: {}, other_text: '' }
}

const toViewRecord = (record) => {
  const parsed = parseDataContent(record.data_content)
  const metrics = parsed.metrics || {}
  const fileType = record.file_type === 'pdf' ? 'pdf' : 'manual'
  const bloodPressure = metrics.blood_pressure || (
    metrics.blood_pressure_diastolic != null && metrics.blood_pressure_systolic != null
      ? `${metrics.blood_pressure_diastolic}/${metrics.blood_pressure_systolic}`
      : ''
  )
  return {
    ...record,
    record_type: fileType,
    is_private: !record.is_public,
    requires_private_key: !!record.requires_private_key,
    health_data_file: record.pdf_data_base64 || null,
    health_data_file_name: fileType === 'pdf' ? (record.data_title || '健康数据PDF') : null,
    recorded_at: record.created_at,
    weight: metrics.weight ?? null,
    height: metrics.height ?? null,
    blood_pressure: bloodPressure,
    blood_lipid: metrics.blood_lipid ?? null,
    heart_rate: metrics.heart_rate ?? null,
    blood_sugar: metrics.blood_sugar ?? null,
    other_text: parsed.other_text || ''
  }
}

const statsCards = computed(() => {
  const averageHeartRate = healthSummary.value.average_heart_rate
  return [
    {
      title: '记录总数',
      value: totalRecords.value,
      unit: '条',
      icon: 'TrendCharts',
      color: '#2f6fd6',
      desc: `手动 ${manualRecords.value} / PDF ${pdfRecords.value}`
    },
    {
      title: '本月记录',
      value: healthSummary.value.records_this_month || 0,
      unit: '条',
      icon: 'Calendar',
      color: '#2ea56b',
      desc: latestRecordLabel.value
    },
    {
      title: '平均心率',
      value: averageHeartRate ? Math.round(averageHeartRate) : '-',
      unit: averageHeartRate ? 'bpm' : '',
      icon: 'Bell',
      color: '#cc8a1b',
      desc: `保密 ${privateRecords.value} / 公开 ${publicRecords.value}`
    },
    {
      title: '最近记录',
      value: latestRecordDate.value,
      unit: '',
      icon: 'DataAnalysis',
      color: '#5d6d7e',
      desc: '按时间倒序展示全部记录'
    }
  ]
})

const totalRecords = computed(() => healthRecords.value.length)
const pdfRecords = computed(() => healthRecords.value.filter((item) => item.record_type === 'pdf').length)
const manualRecords = computed(() => healthRecords.value.filter((item) => item.record_type !== 'pdf').length)
const privateRecords = computed(() => healthRecords.value.filter((item) => item.is_private).length)
const publicRecords = computed(() => healthRecords.value.filter((item) => !item.is_private).length)
const hasLockedPrivateRecords = computed(() => healthRecords.value.some((item) => item.requires_private_key))
const latestRecordDate = computed(() => {
  if (!healthRecords.value.length) return '-'
  return formatDate(healthRecords.value[0].recorded_at)
})
const latestRecordLabel = computed(() => (healthRecords.value.length ? '已同步最近记录' : '暂无记录'))

const requestPrivateKey = async () => {
  try {
    const { value } = await ElMessageBox.prompt(unlockRequiredText, unlockDialogTitle, {
      confirmButtonText: '\u786e\u5b9a',
      cancelButtonText: '\u53d6\u6d88',
      inputPlaceholder: unlockPlaceholder,
      inputValidator: (inputValue) => {
        if (!inputValue || !inputValue.trim()) {
          return unlockRequiredText
        }
        return true
      }
    })
    return value?.trim() || ''
  } catch {
    ElMessage.info(unlockCanceledText)
    return ''
  }
}

const ensureUnlockedPrivateData = async () => {
  if (unlockedPrivateKey.value) {
    return unlockedPrivateKey.value
  }

  const privateKey = await requestPrivateKey()
  if (!privateKey) {
    return ''
  }

  unlockedPrivateKey.value = privateKey
  ElMessage.success(unlockSuccessText)
  return privateKey
}

const clearUnlockedPrivateData = () => {
  unlockedPrivateKey.value = ''
  ElMessage.success(unlockClearedText)
  loadHealthData()
}

const unlockPrivateData = async () => {
  const privateKey = await ensureUnlockedPrivateData()
  if (!privateKey) {
    return
  }
  await loadHealthData()
}

const openManualDialog = () => {
  formMode.value = 'manual'
  isEditing.value = false
  healthForm.value = {
    weight: null,
    height: null,
    blood_pressure: '',
    blood_lipid: null,
    heart_rate: null,
    blood_sugar: null,
    other_text: '',
    record_type: 'manual',
    is_private: false,
    health_data_file_name: null,
    health_data_file: null,
    recorded_at: new Date()
  }
  dialogVisible.value = true
}

const openPdfDialog = () => {
  formMode.value = 'pdf'
  isEditing.value = false
  healthForm.value = {
    weight: null,
    height: null,
    blood_pressure: '',
    blood_lipid: null,
    heart_rate: null,
    blood_sugar: null,
    other_text: '',
    record_type: 'pdf',
    is_private: true,
    health_data_file_name: null,
    health_data_file: null,
    recorded_at: new Date()
  }
  dialogVisible.value = true
}

const editRecord = async (record) => {
  if (record.requires_private_key) {
    const privateKey = await ensureUnlockedPrivateData()
    if (!privateKey) {
      return
    }
    await loadHealthData()
    const unlockedRecord = healthRecords.value.find((item) => item.id === record.id)
    if (!unlockedRecord) {
      return
    }
    record = unlockedRecord
  }

  const parsed = parseDataContent(record.data_content)
  const metrics = parsed.metrics || {}
  const bloodPressure = metrics.blood_pressure || (
    metrics.blood_pressure_diastolic != null && metrics.blood_pressure_systolic != null
      ? `${metrics.blood_pressure_diastolic}/${metrics.blood_pressure_systolic}`
      : ''
  )
  formMode.value = record.record_type === 'pdf' ? 'pdf' : 'manual'
  isEditing.value = true
  healthForm.value = {
    ...record,
    weight: metrics.weight ?? null,
    height: metrics.height ?? null,
    blood_pressure: bloodPressure,
    blood_lipid: metrics.blood_lipid ?? null,
    heart_rate: metrics.heart_rate ?? null,
    blood_sugar: metrics.blood_sugar ?? null,
    other_text: parsed.other_text || '',
    record_type: record.record_type || 'manual',
    is_private: Boolean(record.is_private),
    health_data_file_name: record.health_data_file_name || null,
    health_data_file: record.health_data_file || null,
    recorded_at: new Date(record.recorded_at)
  }
  dialogVisible.value = true
}

const handlePdfFileChange = (uploadFile) => {
  const file = uploadFile?.raw || uploadFile
  if (!file) return

  const isPdfByType = file.type === 'application/pdf'
  const isPdfByName = file.name?.toLowerCase().endsWith('.pdf')
  if (!isPdfByType && !isPdfByName) {
    ElMessage.error('仅支持 PDF 文件')
    return
  }

  if (file.size > 6 * 1024 * 1024) {
    ElMessage.error('PDF 不能超过 6MB')
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    healthForm.value.health_data_file = reader.result
    healthForm.value.health_data_file_name = file.name
    healthForm.value.is_private = true
  }
  reader.readAsDataURL(file)
}

const removeFile = () => {
  healthForm.value.health_data_file_name = null
  healthForm.value.health_data_file = null
}

const extractErrorDetail = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  return fallback
}

const saveHealthData = async () => {
  if (!healthFormRef.value) return
  
  try {
    const valid = await healthFormRef.value.validate()
    if (!valid) return

    saving.value = true
    
    const metrics = {
      weight: healthForm.value.weight,
      height: healthForm.value.height,
      blood_pressure: healthForm.value.blood_pressure,
      blood_lipid: healthForm.value.blood_lipid,
      heart_rate: healthForm.value.heart_rate,
      blood_sugar: healthForm.value.blood_sugar
    }

    const parsedPressure = parseBloodPressure(healthForm.value.blood_pressure)
    metrics.blood_pressure_diastolic = parsedPressure.diastolic
    metrics.blood_pressure_systolic = parsedPressure.systolic

    const payload = {
      data_title: formMode.value === 'pdf' ? (healthForm.value.health_data_file_name || '健康数据PDF') : '手动健康记录',
      file_type: formMode.value === 'pdf' ? 'pdf' : 'text',
      is_public: !healthForm.value.is_private,
      data_content: formMode.value === 'pdf'
        ? null
        : JSON.stringify({ metrics, other_text: healthForm.value.other_text || '' }),
      pdf_data_base64: formMode.value === 'pdf' ? healthForm.value.health_data_file : null
    }

    if (formMode.value === 'pdf') {
      if (!payload.pdf_data_base64) {
        ElMessage.error('请先上传PDF文件')
        return
      }

      payload.data_content = null
    }

    if (healthForm.value.is_private) {
      const privateKey = await ensureUnlockedPrivateData()
      if (!privateKey) {
        saving.value = false
        return
      }
      payload.private_key = privateKey
    }
    
    if (isEditing.value) {
      await healthApi.updateRecord(healthForm.value.id, payload)
      ElMessage.success('健康数据更新成功')
    } else {
      await healthApi.createRecord(payload)
      ElMessage.success('健康数据添加成功')
    }
    
    dialogVisible.value = false
    await loadHealthData()
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, '操作失败，请重试'))
  } finally {
    saving.value = false
  }
}

const deleteRecord = async (record) => {
  try {
    await healthApi.deleteRecord(record.id)
    ElMessage.success('健康数据删除成功')
    await loadHealthData()
  } catch (error) {
    ElMessage.error('删除失败，请重试')
  }
}

const loadHealthData = async () => {
  try {
    const [records, summary] = await Promise.all([
      healthApi.getRecords(requestParams.value),
      healthApi.getSummary(requestParams.value)
    ])
    healthRecords.value = records.map(toViewRecord)
    healthSummary.value = summary
  } catch (error) {
    if (unlockedPrivateKey.value && [400, 401, 403].includes(error?.response?.status)) {
      unlockedPrivateKey.value = ''
      ElMessage.error(unlockInvalidText)
      return
    }
    ElMessage.error(extractErrorDetail(error, loadFailedText))
  }
}


const analyzeHealthData = async () => {
  try {
    if (hasLockedPrivateRecords.value && !unlockedPrivateKey.value) {
      const privateKey = await ensureUnlockedPrivateData()
      if (!privateKey) {
        return
      }
      await loadHealthData()
    }
    const analysis = await healthApi.analyzeData({}, requestParams.value)
    healthAnalysis.value = analysis
    ElMessage.success(analysisSuccessText)
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, analysisFailedText))
  }
}


const refreshData = () => {
  loadHealthData()
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const openPdf = async (record) => {
  if (record.requires_private_key) {
    ElMessage.warning(lockedRecordText)
    const privateKey = await ensureUnlockedPrivateData()
    if (!privateKey) {
      return
    }
    await loadHealthData()
    const unlockedRecord = healthRecords.value.find((item) => item.id === record.id)
    if (!unlockedRecord) {
      return
    }
    record = unlockedRecord
  }

  if (!record.health_data_file) return
  window.open(record.health_data_file, '_blank', 'noopener,noreferrer')
}

onMounted(() => {
  loadHealthData()
})
</script>

<style scoped>
.health-data-container {
  max-width: 1400px;
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
  gap: 10px;
}

.add-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.add-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.upload-btn {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.upload-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.content-section {
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stats-card {
  border-radius: 16px;
  border: none;
  min-height: auto;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.chart-card, .recent-card {
  border-radius: 16px;
  border: 1px solid #e5eefb;
  min-height: 400px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.recent-card {
  height: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.chart-placeholder {
  min-height: 300px;
  display: block;
  background: linear-gradient(180deg, #f8fbff 0%, #f4f8ff 100%);
  border-radius: 12px;
  border: 1px dashed #d6e4f8;
  padding: 12px;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-preview {
  margin-top: 12px;
}

.placeholder-content {
  text-align: center;
  color: #94a3b8;
}

.placeholder-content p {
  margin-top: 12px;
  font-size: 14px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recent-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fbff 0%, #f5f9ff 100%);
  border-radius: 12px;
  border: 1px solid #e4ecfb;
  transition: all 0.25s ease;
}

.recent-item:hover {
  background: #eef5ff;
  transform: translateY(-2px);
}

.recent-icon {
  width: 42px;
  height: 42px;
  background: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}

.recent-content {
  flex: 1;
}

.recent-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.recent-content p {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.recent-time {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fbff 0%, #f5f9ff 100%);
  border-radius: 12px;
  border: 1px solid #e4ecfb;
  transition: all 0.25s ease;
}

.stat-item:hover {
  background: #eef5ff;
  transform: translateY(-2px);
}

.stat-icon {
  width: 42px;
  height: 42px;
  background: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 2px 0;
}

.stat-unit {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 400;
}

.stat-desc {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-card, .recent-card {
    margin-bottom: 16px;
  }
}

@media (max-width: 576px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
