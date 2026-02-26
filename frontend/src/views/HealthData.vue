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
        <el-button type="primary" class="add-btn" @click="openAddDialog">
          <el-icon><Plus /></el-icon>
          添加数据
        </el-button>
      </div>
    </div>
    
    <div class="content-section">
      <el-row :gutter="24">
        <el-col :span="24">
          <el-card class="stats-card" shadow="hover">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">
                  <el-icon size="24" color="#409EFF"><TrendCharts /></el-icon>
                </div>
                <div class="stat-info">
                  <h3>记录总数</h3>
                  <p class="stat-value">{{ healthSummary.total_records || 0 }}<span class="stat-unit">条</span></p>
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-icon">
                  <el-icon size="24" color="#67C23A"><Calendar /></el-icon>
                </div>
                <div class="stat-info">
                  <h3>本月记录</h3>
                  <p class="stat-value">{{ healthSummary.records_this_month || 0 }}<span class="stat-unit">条</span></p>
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-icon">
                  <el-icon size="24" color="#E6A23C"><Bell /></el-icon>
                </div>
                <div class="stat-info">
                  <h3>平均心率</h3>
                  <p class="stat-value">{{ Math.round(healthSummary.average_heart_rate || 0) }}<span class="stat-unit">bpm</span></p>
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
                <el-table :data="healthRecords.slice(0, 5)" style="width: 100%">
                  <el-table-column prop="recorded_at" label="记录时间" width="180">
                    <template #default="scope">
                      {{ formatDate(scope.row.recorded_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="weight" label="体重(kg)" width="100" />
                  <el-table-column prop="blood_pressure_systolic" label="收缩压" width="100" />
                  <el-table-column prop="blood_pressure_diastolic" label="舒张压" width="100" />
                  <el-table-column prop="heart_rate" label="心率" width="100" />
                  <el-table-column label="操作">
                    <template #default="scope">
                      <el-button type="text" @click="editRecord(scope.row)">编辑</el-button>
                      <el-button type="text" style="color: #f56c6c" @click="deleteRecord(scope.row)">删除</el-button>
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
            <el-form-item label="收缩压" prop="blood_pressure_systolic">
              <el-input-number v-model="healthForm.blood_pressure_systolic" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="舒张压" prop="blood_pressure_diastolic">
              <el-input-number v-model="healthForm.blood_pressure_diastolic" :min="0" style="width: 100%" />
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
        
        <el-form-item label="记录时间" prop="recorded_at">
          <el-date-picker
            v-model="healthForm.recorded_at"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { healthApi } from '../api/health'

const healthRecords = ref([])
const healthSummary = ref({})
const healthAnalysis = ref({})
const dialogVisible = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const healthFormRef = ref()

const healthForm = ref({
  weight: null,
  height: null,
  blood_pressure_systolic: null,
  blood_pressure_diastolic: null,
  heart_rate: null,
  blood_sugar: null,
  recorded_at: new Date()
})

const healthRules = {
  weight: [{ type: 'number', message: '请输入有效的体重', trigger: 'blur' }],
  height: [{ type: 'number', message: '请输入有效的身高', trigger: 'blur' }],
  blood_pressure_systolic: [{ type: 'number', message: '请输入有效的收缩压', trigger: 'blur' }],
  blood_pressure_diastolic: [{ type: 'number', message: '请输入有效的舒张压', trigger: 'blur' }],
  heart_rate: [{ type: 'number', message: '请输入有效的心率', trigger: 'blur' }],
  blood_sugar: [{ type: 'number', message: '请输入有效的血糖', trigger: 'blur' }]
}

const openAddDialog = () => {
  isEditing.value = false
  healthForm.value = {
    weight: null,
    height: null,
    blood_pressure_systolic: null,
    blood_pressure_diastolic: null,
    heart_rate: null,
    blood_sugar: null,
    recorded_at: new Date()
  }
  dialogVisible.value = true
}

const editRecord = (record) => {
  isEditing.value = true
  healthForm.value = { ...record, recorded_at: new Date(record.recorded_at) }
  dialogVisible.value = true
}

const saveHealthData = async () => {
  if (!healthFormRef.value) return
  
  try {
    const valid = await healthFormRef.value.validate()
    if (!valid) return

    saving.value = true
    
    if (isEditing.value) {
      await healthApi.updateRecord(healthForm.value.id, healthForm.value)
      ElMessage.success('健康数据更新成功')
    } else {
      await healthApi.createRecord(healthForm.value)
      ElMessage.success('健康数据添加成功')
    }
    
    dialogVisible.value = false
    await loadHealthData()
  } catch (error) {
    ElMessage.error('操作失败，请重试')
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
      healthApi.getRecords(),
      healthApi.getSummary()
    ])
    healthRecords.value = records
    healthSummary.value = summary
  } catch (error) {
    ElMessage.error('加载健康数据失败')
  }
}

const analyzeHealthData = async () => {
  try {
    const analysis = await healthApi.analyzeData()
    healthAnalysis.value = analysis
    ElMessage.success('健康分析完成')
  } catch (error) {
    ElMessage.error('健康分析失败')
  }
}

const refreshData = () => {
  loadHealthData()
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
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

.content-section {
  margin-bottom: 32px;
}

.stats-card {
  border-radius: 16px;
  border: none;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: #f1f5f9;
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-info h3 {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 4px;
  font-weight: 500;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.stat-unit {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 400;
}

.chart-card, .recent-card {
  border-radius: 16px;
  border: none;
  height: 400px;
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
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;
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
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.recent-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.recent-icon {
  width: 32px;
  height: 32px;
  background: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
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

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-card, .recent-card {
    margin-bottom: 16px;
  }
}
</style>