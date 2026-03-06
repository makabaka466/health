<template>
  <div class="admin-logs-page">
    <el-card shadow="hover">
      <template #header>
        <div class="header-row">
          <span>系统日志</span>
          <div class="header-actions">
            <el-select v-model="query.module" placeholder="按模块筛选" clearable style="width: 180px">
              <el-option label="系统设置" value="system_settings" />
              <el-option label="系统日志" value="system_logs" />
            </el-select>
            <el-button type="primary" @click="loadLogs">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="logs" stripe border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="level" label="级别" width="100" />
        <el-table-column prop="module" label="模块" width="160" />
        <el-table-column prop="action" label="动作" width="120" />
        <el-table-column prop="message" label="描述" min-width="300" />
        <el-table-column prop="operator_id" label="操作人ID" width="120" />
        <el-table-column prop="created_at" label="时间" width="190" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemLogs } from '../../api/adminSystem'

const loading = ref(false)
const logs = ref([])
const query = reactive({
  limit: 100,
  module: ''
})

const loadLogs = async () => {
  loading.value = true
  try {
    logs.value = await getSystemLogs({ ...query })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载系统日志失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.admin-logs-page {
  width: 100%;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}
</style>
