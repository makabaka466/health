<template>
  <div class="admin-settings-page">
    <div class="page-header">
      <div>
        <h2>{{ labels.pageTitle }}</h2>
        <p>{{ labels.pageSubtitle }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadSettings">{{ labels.refresh }}</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">{{ labels.save }}</el-button>
      </div>
    </div>

    <div class="overview-grid">
      <el-card shadow="hover" class="metric-card">
        <div class="metric-label">{{ labels.metricRegister }}</div>
        <div class="metric-value">{{ form.allow_user_register ? labels.enabled : labels.disabled }}</div>
        <el-tag :type="form.allow_user_register ? 'success' : 'info'">{{ labels.userAccess }}</el-tag>
      </el-card>
      <el-card shadow="hover" class="metric-card">
        <div class="metric-label">{{ labels.metricAi }}</div>
        <div class="metric-value">{{ form.ai_enabled ? labels.enabled : labels.disabled }}</div>
        <el-tag :type="form.ai_enabled ? 'success' : 'warning'">{{ labels.aiService }}</el-tag>
      </el-card>
      <el-card shadow="hover" class="metric-card">
        <div class="metric-label">{{ labels.metricMaintenance }}</div>
        <div class="metric-value">{{ form.maintenance_mode ? labels.maintenanceOn : labels.maintenanceOff }}</div>
        <el-tag :type="form.maintenance_mode ? 'danger' : 'success'">{{ labels.systemStatus }}</el-tag>
      </el-card>
      <el-card shadow="hover" class="metric-card">
        <div class="metric-label">{{ labels.metricSession }}</div>
        <div class="metric-value">{{ form.session_timeout_minutes }} {{ labels.minutes }}</div>
        <el-tag type="info">{{ labels.security }}</el-tag>
      </el-card>
    </div>

    <div class="settings-layout">
      <div class="settings-main">
        <el-card shadow="hover" class="section-card">
          <template #header>
            <div class="section-title">{{ labels.basicSection }}</div>
          </template>
          <el-form label-width="120px">
            <el-form-item :label="labels.projectName">
              <el-input v-model="form.project_name" />
            </el-form-item>
            <el-form-item :label="labels.projectSubtitle">
              <el-input v-model="form.project_subtitle" />
            </el-form-item>
            <el-form-item :label="labels.welcomeMessage">
              <el-input v-model="form.welcome_message" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item :label="labels.supportEmail">
              <el-input v-model="form.support_email" />
            </el-form-item>
            <el-form-item :label="labels.supportPhone">
              <el-input v-model="form.support_phone" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="hover" class="section-card">
          <template #header>
            <div class="section-title">{{ labels.accessSection }}</div>
          </template>
          <div class="switch-grid">
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.allowRegister }}</div>
                <div class="switch-desc">{{ labels.allowRegisterDesc }}</div>
              </div>
              <el-switch v-model="form.allow_user_register" />
            </div>
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.socialLogin }}</div>
                <div class="switch-desc">{{ labels.socialLoginDesc }}</div>
              </div>
              <el-switch v-model="form.allow_social_login" />
            </div>
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.maintenanceMode }}</div>
                <div class="switch-desc">{{ labels.maintenanceDesc }}</div>
              </div>
              <el-switch v-model="form.maintenance_mode" />
            </div>
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.defaultPublic }}</div>
                <div class="switch-desc">{{ labels.defaultPublicDesc }}</div>
              </div>
              <el-switch v-model="form.default_health_data_public" />
            </div>
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.operationLog }}</div>
                <div class="switch-desc">{{ labels.operationLogDesc }}</div>
              </div>
              <el-switch v-model="form.enable_operation_log" />
            </div>
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.blockchainSync }}</div>
                <div class="switch-desc">{{ labels.blockchainSyncDesc }}</div>
              </div>
              <el-switch v-model="form.enable_blockchain_sync" />
            </div>
          </div>

          <div class="number-grid">
            <el-form label-width="140px">
              <el-form-item :label="labels.sessionTimeout">
                <el-input-number v-model="form.session_timeout_minutes" :min="15" :max="1440" />
              </el-form-item>
              <el-form-item :label="labels.passwordMinLength">
                <el-input-number v-model="form.password_min_length" :min="6" :max="32" />
              </el-form-item>
              <el-form-item :label="labels.logRetention">
                <el-input-number v-model="form.log_retention_days" :min="7" :max="365" />
              </el-form-item>
            </el-form>
          </div>
        </el-card>

        <el-card shadow="hover" class="section-card">
          <template #header>
            <div class="section-title">{{ labels.contentSection }}</div>
          </template>
          <div class="switch-grid">
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.aiEnabled }}</div>
                <div class="switch-desc">{{ labels.aiEnabledDesc }}</div>
              </div>
              <el-switch v-model="form.ai_enabled" />
            </div>
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.knowledgeImport }}</div>
                <div class="switch-desc">{{ labels.knowledgeImportDesc }}</div>
              </div>
              <el-switch v-model="form.knowledge_import_enabled" />
            </div>
            <div class="switch-item">
              <div>
                <div class="switch-title">{{ labels.articleAutoPublish }}</div>
                <div class="switch-desc">{{ labels.articleAutoPublishDesc }}</div>
              </div>
              <el-switch v-model="form.article_auto_publish" />
            </div>
          </div>

          <el-form label-width="140px">
            <el-form-item :label="labels.maxUploadSize">
              <el-input-number v-model="form.max_upload_size_mb" :min="1" :max="200" />
            </el-form-item>
            <el-form-item :label="labels.defaultArticleCover">
              <el-input v-model="form.default_article_cover" :placeholder="labels.coverPlaceholder" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="hover" class="section-card">
          <template #header>
            <div class="section-title">{{ labels.homeSection }}</div>
          </template>
          <el-form label-width="120px">
            <el-form-item :label="labels.bannerTitle">
              <el-input v-model="form.homepage_banner_title" />
            </el-form-item>
            <el-form-item :label="labels.bannerSubtitle">
              <el-input v-model="form.homepage_banner_subtitle" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <div class="settings-side">
        <el-card shadow="hover" class="section-card preview-card">
          <template #header>
            <div class="section-title">{{ labels.previewSection }}</div>
          </template>
          <div class="preview-box">
            <h3>{{ form.project_name }}</h3>
            <p class="preview-subtitle">{{ form.project_subtitle }}</p>
            <div class="preview-banner">
              <strong>{{ form.homepage_banner_title }}</strong>
              <span>{{ form.homepage_banner_subtitle }}</span>
            </div>
            <el-alert :title="form.welcome_message" type="success" :closable="false" show-icon />
            <div class="preview-contact">
              <div>{{ labels.supportEmail }}：{{ form.support_email }}</div>
              <div>{{ labels.supportPhone }}：{{ form.support_phone }}</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="section-card">
          <template #header>
            <div class="section-title">{{ labels.recentLogs }}</div>
          </template>
          <div v-if="logsLoading" class="logs-loading">{{ labels.loadingLogs }}</div>
          <el-timeline v-else>
            <el-timeline-item
              v-for="item in recentLogs"
              :key="item.id"
              :timestamp="formatDateTime(item.created_at)"
              placement="top"
            >
              <div class="log-item-title">{{ item.action }} · {{ item.module }}</div>
              <div class="log-item-message">{{ item.message }}</div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="!logsLoading && !recentLogs.length" :description="labels.noLogs" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemLogs, getSystemSettings, updateSystemSettings } from '../../api/adminSystem'

const labels = {
  pageTitle: '系统设置',
  pageSubtitle: '统一管理平台基础信息、访问控制、内容能力与首页展示配置。',
  refresh: '重新加载',
  save: '保存设置',
  enabled: '启用',
  disabled: '停用',
  metricRegister: '用户注册',
  metricAi: 'AI 服务',
  metricMaintenance: '维护状态',
  metricSession: '会话时长',
  userAccess: '访问控制',
  aiService: '智能服务',
  systemStatus: '运行状态',
  security: '安全策略',
  maintenanceOn: '维护中',
  maintenanceOff: '正常运行',
  minutes: '分钟',
  basicSection: '基础信息',
  accessSection: '访问与安全',
  contentSection: '内容与能力',
  homeSection: '首页展示',
  previewSection: '实时预览',
  recentLogs: '最近操作日志',
  projectName: '项目名称',
  projectSubtitle: '项目副标题',
  welcomeMessage: '欢迎语',
  supportEmail: '支持邮箱',
  supportPhone: '联系电话',
  allowRegister: '允许用户注册',
  allowRegisterDesc: '关闭后仅管理员可创建用户。',
  socialLogin: '允许社交登录',
  socialLoginDesc: '控制微信、支付宝等快捷登录入口。',
  maintenanceMode: '维护模式',
  maintenanceDesc: '开启后可限制普通用户访问。',
  defaultPublic: '健康数据默认公开',
  defaultPublicDesc: '新建健康记录时默认采用公开权限。',
  operationLog: '记录操作日志',
  operationLogDesc: '关闭后将减少后台操作日志写入。',
  blockchainSync: '区块链同步',
  blockchainSyncDesc: '启用后可配合链上服务同步关键记录。',
  sessionTimeout: '会话超时',
  passwordMinLength: '密码最短长度',
  logRetention: '日志保留天数',
  aiEnabled: '启用 AI 功能',
  aiEnabledDesc: '控制 AI 助手与分析能力开关。',
  knowledgeImport: '启用知识库导入',
  knowledgeImportDesc: '控制 PDF / Word 导入知识库能力。',
  articleAutoPublish: '文章自动发布',
  articleAutoPublishDesc: '新增文章后是否默认直接上架。',
  maxUploadSize: '最大上传大小',
  defaultArticleCover: '默认文章封面',
  coverPlaceholder: '可填写默认封面图片地址',
  bannerTitle: '首页主标题',
  bannerSubtitle: '首页副标题',
  loadingLogs: '正在加载日志...',
  noLogs: '暂无日志记录',
  loadFailed: '加载系统设置失败',
  saveSuccess: '系统设置已保存',
  saveFailed: '保存系统设置失败',
  logLoadFailed: '加载日志失败'
}

const saving = ref(false)
const logsLoading = ref(false)
const recentLogs = ref([])

const form = reactive({
  project_name: '健康管理系统',
  project_subtitle: '智能健康数据与知识服务平台',
  welcome_message: '欢迎使用健康管理系统，请根据角色进入对应工作台。',
  support_email: 'support@health.local',
  support_phone: '400-800-2026',
  allow_user_register: true,
  allow_social_login: true,
  ai_enabled: true,
  knowledge_import_enabled: true,
  article_auto_publish: false,
  enable_operation_log: true,
  enable_blockchain_sync: false,
  maintenance_mode: false,
  default_health_data_public: false,
  default_article_cover: '',
  session_timeout_minutes: 120,
  max_upload_size_mb: 20,
  homepage_banner_title: '科学管理健康，智能辅助决策',
  homepage_banner_subtitle: '聚合健康数据、知识内容与 AI 分析能力',
  password_min_length: 6,
  log_retention_days: 30
})

const loadSettings = async () => {
  try {
    const data = await getSystemSettings()
    Object.assign(form, data)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || labels.loadFailed)
  }
}

const loadLogs = async () => {
  logsLoading.value = true
  try {
    recentLogs.value = await getSystemLogs({ limit: 6 })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || labels.logLoadFailed)
  } finally {
    logsLoading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const data = await updateSystemSettings({ ...form })
    Object.assign(form, data)
    ElMessage.success(labels.saveSuccess)
    await loadLogs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || labels.saveFailed)
  } finally {
    saving.value = false
  }
}

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(async () => {
  await loadSettings()
  await loadLogs()
})
</script>

<style scoped>
.admin-settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #1f2937;
}

.page-header p {
  margin: 6px 0 0;
  color: #64748b;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  border-radius: 18px;
}

.metric-label {
  color: #64748b;
  font-size: 13px;
}

.metric-value {
  margin: 10px 0 14px;
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.settings-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(320px, 0.95fr);
  gap: 16px;
  align-items: start;
}

.settings-main,
.settings-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  border-radius: 18px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.switch-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.switch-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e5edf6;
  border-radius: 14px;
  background: linear-gradient(180deg, #fbfdff 0%, #f6f9fc 100%);
}

.switch-title {
  font-weight: 600;
  color: #1f2937;
}

.switch-desc {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
}

.preview-box {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.preview-box h3 {
  margin: 0;
  font-size: 22px;
  color: #0f172a;
}

.preview-subtitle {
  margin: 0;
  color: #64748b;
}

.preview-banner {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
}

.preview-contact {
  color: #475569;
  font-size: 14px;
  line-height: 1.8;
}

.log-item-title {
  font-weight: 600;
  color: #1f2937;
}

.log-item-message {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.logs-loading {
  color: #64748b;
}

@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .settings-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .overview-grid,
  .switch-grid {
    grid-template-columns: 1fr;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions :deep(.el-button) {
    flex: 1;
  }
}
</style>
