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
                <el-option label="待审核" value="pending" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="searchForm.role" placeholder="用户角色" clearable>
                <el-option label="全部" value="" />
                <el-option label="普通用户" value="user" />
                <el-option label="管理员" value="admin" />
                <el-option label="超级管理员" value="super_admin" />
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
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="loginTime" label="最后登录" width="160" />
          <el-table-column prop="createdAt" label="注册时间" width="160" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="text" size="small" @click="handleView(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button type="text" size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button 
                type="text" 
                size="small" 
                :class="{ 'danger-btn': row.status === 'active' }"
                @click="handleToggleStatus(row)"
              >
                <el-icon v-if="row.status === 'active'"><Lock /></el-icon>
                <el-icon v-else><Unlock /></el-icon>
                {{ row.status === 'active' ? '禁用' : '启用' }}
              </el-button>
              <el-button type="text" size="small" class="danger-btn" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const searchForm = reactive({
  keyword: '',
  status: '',
  role: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

const users = ref([
  {
    id: 1,
    username: 'admin',
    email: 'admin@health.com',
    role: 'super_admin',
    status: 'active',
    loginTime: '2024-01-15 14:30',
    createdAt: '2024-01-01 10:00',
    avatar: ''
  },
  {
    id: 2,
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    role: 'user',
    status: 'active',
    loginTime: '2024-01-15 13:20',
    createdAt: '2024-01-05 09:30',
    avatar: ''
  },
  {
    id: 3,
    username: 'lisi',
    email: 'lisi@example.com',
    role: 'user',
    status: 'disabled',
    loginTime: '2024-01-14 16:45',
    createdAt: '2024-01-03 14:20',
    avatar: ''
  },
  {
    id: 4,
    username: 'wangwu',
    email: 'wangwu@example.com',
    role: 'admin',
    status: 'pending',
    loginTime: '2024-01-15 12:10',
    createdAt: '2024-01-08 11:15',
    avatar: ''
  }
])

pagination.total = users.value.length

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
    'super_admin': '超级管理员',
    'admin': '管理员',
    'user': '普通用户'
  }
  return textMap[role] || '未知'
}

const getStatusType = (status) => {
  const typeMap = {
    'active': 'success',
    'disabled': 'danger',
    'pending': 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'active': '正常',
    'disabled': '禁用',
    'pending': '待审核'
  }
  return textMap[status] || '未知'
}

const handleSearch = () => {
  ElMessage.success('搜索功能开发中...')
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  searchForm.role = ''
  ElMessage.success('已重置搜索条件')
}

const handleExport = () => {
  ElMessage.success('导出功能开发中...')
}

const handleRefresh = () => {
  ElMessage.success('数据已刷新')
}

const handleView = (row) => {
  ElMessage.info(`查看用户: ${row.username}`)
}

const handleEdit = (row) => {
  ElMessage.info(`编辑用户: ${row.username}`)
}

const handleToggleStatus = async (row) => {
  const action = row.status === 'active' ? '禁用' : '启用'
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
    row.status = row.status === 'active' ? 'disabled' : 'active'
    ElMessage.success(`用户已${action}`)
  } catch {
    // 用户取消
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    ElMessage.success('用户已删除')
  } catch {
    // 用户取消
  }
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  ElMessage.success(`每页显示 ${size} 条`)
}

const handleCurrentChange = (page) => {
  pagination.currentPage = page
  ElMessage.success(`当前第 ${page} 页`)
}
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
