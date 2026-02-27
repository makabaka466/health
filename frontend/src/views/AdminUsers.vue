<template>
  <div class="admin-users-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#F56C6C">
            <User />
          </el-icon>
        </div>
        <div class="header-text">
          <h1>用户管理</h1>
          <p>管理系统用户和权限设置</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" class="add-btn">
          <el-icon><Plus /></el-icon>
          添加用户
        </el-button>
      </div>
    </div>
    
    <div class="content-section">
      <!-- 搜索和筛选 -->
      <el-card class="search-card" shadow="hover">
        <div class="search-form">
          <el-row :gutter="16">
            <el-col :span="6">
              <el-input
                v-model="searchForm.keyword"
                placeholder="搜索用户名、邮箱..."
                prefix-icon="Search"
                clearable
              />
            </el-col>
            <el-col :span="4">
              <el-select v-model="searchForm.status" placeholder="用户状态" clearable>
                <el-option label="全部" value="" />
                <el-option label="正常" value="active" />
                <el-option label="禁用" value="disabled" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="searchForm.role" placeholder="用户角色" clearable>
                <el-option label="全部" value="" />
                <el-option label="普通用户" value="user" />
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-button type="primary" @click="handleSearch">
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
              <el-button @click="handleReset">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </el-col>
          </el-row>
        </div>
      </el-card>
      
      <!-- 用户列表 -->
      <el-card class="users-card" shadow="hover">
        <div class="card-header">
          <h3>用户列表</h3>
          <div class="header-actions">
            <el-button type="text" @click="handleExport">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button type="text" @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
        
        <el-table :data="users" stripe class="users-table">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" min-width="120">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :size="32" :src="row.avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span>{{ row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="role" label="角色" width="120">
            <template #default="{ row }">
              <el-tag :type="getRoleType(row.role)" size="small">
                {{ getRoleText(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.is_active)" size="small">
                {{ getStatusText(row.is_active) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="最后更新" width="180">
            <template #default="{ row }">
              {{ formatDate(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button type="text" size="small" @click="handleView(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button 
                type="text" 
                size="small" 
                :class="{ 'danger-btn': row.is_active }"
                @click="handleToggleStatus(row)"
              >
                <el-icon v-if="row.is_active"><Lock /></el-icon>
                <el-icon v-else><Unlock /></el-icon>
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button type="text" size="small" class="danger-btn" @click="handleResetPassword(row)">
                <el-icon><Refresh /></el-icon>
                重置密码
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            :total="pagination.total"
            :page-size="pagination.pageSize"
            layout="total, prev, pager, next, jumper"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <el-dialog v-model="detailVisible" title="用户信息" width="520px">
      <el-descriptions :column="1" border v-if="currentUser">
        <el-descriptions-item label="用户ID">{{ currentUser.id }}</el-descriptions-item>
        <el-descriptions-item label="账号">{{ currentUser.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ currentUser.email }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ getRoleText(currentUser.role) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ getStatusText(currentUser.is_active) }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ formatDate(currentUser.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="最后更新时间">{{ formatDate(currentUser.updated_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminUserDetail,
  getAdminUsers,
  resetAdminUserPassword,
  updateAdminUserStatus
} from '../api/auth'

const searchForm = reactive({
  keyword: '',
  status: '',
  role: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 12,
  total: 0
})

const users = ref([])
const detailVisible = ref(false)
const currentUser = ref(null)
const loading = ref(false)

const getRoleType = (role) => {
  const typeMap = {
    'super_admin': 'danger',
    'admin': 'warning',
    'user': 'success'
  }
  return typeMap[role] || 'info'
}

const getRoleText = (role) => {
  const textMap = {
    'admin': '管理员',
    'user': '普通用户'
  }
  return textMap[role] || '未知'
}

const getStatusType = (isActive) => {
  const typeMap = {
    true: 'success',
    false: 'danger'
  }
  return typeMap[isActive] || 'info'
}

const getStatusText = (isActive) => {
  const textMap = {
    true: '正常',
    false: '禁用'
  }
  return textMap[isActive] || '未知'
}

const loadUsers = async () => {
  loading.value = true
  try {
    const data = await getAdminUsers({
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      status: searchForm.status,
      role: searchForm.role
    })
    users.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
  loadUsers()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  searchForm.role = ''
  pagination.currentPage = 1
  loadUsers()
}

const handleExport = () => {
  ElMessage.info('导出功能暂未开放')
}

const handleRefresh = () => {
  loadUsers()
}

const handleView = async (row) => {
  try {
    const detail = await getAdminUserDetail(row.id)
    currentUser.value = detail
    detailVisible.value = true
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载用户详情失败')
  }
}

const handleToggleStatus = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户 "${row.username}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await updateAdminUserStatus(row.id, !row.is_active)
    ElMessage.success(`用户已${action}`)
    await loadUsers()
  } catch {
    // 用户取消
  }
}

const handleResetPassword = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定将用户 "${row.username}" 的密码重置为 123456 吗？`,
      '重置密码',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await resetAdminUserPassword(row.id)
    ElMessage.success('密码已重置为 123456')
  } catch {
    // 用户取消
  }
}

const handleCurrentChange = (page) => {
  pagination.currentPage = page
  loadUsers()
}

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.admin-users-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #F56C6C 0%, #E74C3C 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 24px rgba(245, 108, 108, 0.2);
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

.search-card, .users-card {
  border-radius: 16px;
  border: none;
  margin-bottom: 24px;
}

.search-form {
  padding: 20px;
}

.users-table {
  margin-bottom: 20px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.danger-btn {
  color: #F56C6C !important;
}

.danger-btn:hover {
  background-color: rgba(245, 108, 108, 0.1) !important;
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

.header-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .search-form .el-col {
    margin-bottom: 16px;
  }
}
</style>
