<template>
  <div class="admin-logs-page">
    <el-card shadow="hover">
      <template #header>
        <div class="header-row">
          <span>系统日志</span>
          <div class="header-actions">
            <el-select v-model="query.module" placeholder="Filter by module" clearable style="width: 180px">
              <el-option label="auth" value="auth" />
              <el-option label="health_records" value="health_records" />
              <el-option label="user_profile" value="user_profile" />
              <el-option label="admin_users" value="admin_users" />
              <el-option label="system_settings" value="system_settings" />
              <el-option label="system_logs" value="system_logs" />
              <el-option label="knowledge_articles" value="knowledge_articles" />
              <el-option label="knowledge_base" value="knowledge_base" />
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
