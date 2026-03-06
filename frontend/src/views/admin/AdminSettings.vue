<template>
  <div class="admin-settings-page">
    <el-card shadow="hover">
      <template #header>
        <div class="header-row">
          <span>系统设置</span>
          <el-button type="primary" :loading="saving" @click="handleSave">保存设置</el-button>
        </div>
      </template>

      <el-form label-width="220px">
        <el-form-item label="项目名称">
          <el-input v-model="form.project_name" placeholder="请输入系统名称" />
        </el-form-item>

        <el-form-item label="允许用户注册">
          <el-switch v-model="form.allow_user_register" />
        </el-form-item>

        <el-form-item label="启用 AI 功能">
          <el-switch v-model="form.ai_enabled" />
        </el-form-item>

        <el-form-item label="维护模式">
          <el-switch v-model="form.maintenance_mode" />
        </el-form-item>

        <el-form-item label="健康数据默认公开">
          <el-switch v-model="form.default_health_data_public" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemSettings, updateSystemSettings } from '../../api/adminSystem'

const saving = ref(false)
const form = reactive({
  project_name: '健康管理系统',
  allow_user_register: true,
  ai_enabled: true,
  maintenance_mode: false,
  default_health_data_public: false
})

const loadSettings = async () => {
  try {
    const data = await getSystemSettings()
    Object.assign(form, data)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载系统设置失败')
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const data = await updateSystemSettings({ ...form })
    Object.assign(form, data)
    ElMessage.success('系统设置已保存')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存系统设置失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.admin-settings-page {
  max-width: 980px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
