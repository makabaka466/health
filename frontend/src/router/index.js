import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import AdminAuth from '../views/AdminAuth.vue'
import Dashboard from '../views/Dashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminAuth
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/Home.vue')
      },
      {
        path: 'health-data',
        name: 'HealthData',
        component: () => import('../views/HealthData.vue')
      },
      {
        path: 'ai-chat',
        name: 'AIChat',
        component: () => import('../views/AIChat.vue')
      },
      {
        path: 'ai-assistant',
        name: 'AiAssistant',
        component: () => import('../views/AiAssistant.vue')
      },
      {
        path: 'knowledge-center',
        name: 'KnowledgeCenter',
        component: () => import('../views/KnowledgeCenter.vue')
      },
      {
        path: 'knowledge-center/article/:id',
        name: 'KnowledgeArticleDetail',
        component: () => import('../views/KnowledgeArticleDetail.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue')
      }
    ]
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminHome',
        component: () => import('../views/AdminHome.vue')
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/AdminUsers.vue')
      },
      {
        path: 'health-data',
        name: 'AdminHealthData',
        component: () => import('../views/HealthData.vue')
      },
      {
        path: 'ai-chat',
        name: 'AdminAIChat',
        component: () => import('../views/AIChat.vue')
      },
      {
        path: 'articles',
        name: 'AdminArticles',
        component: () => import('../views/AdminArticles.vue')
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('../views/Profile.vue')
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('../views/Profile.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const adminToken = localStorage.getItem('adminToken')
  const userRole = localStorage.getItem('userRole')
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !token && !adminToken) {
    next('/login')
    return
  }
  
  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !adminToken) {
    next('/admin/login')
    return
  }
  
  // 普通用户访问管理员页面
  if (to.path.startsWith('/admin') && !adminToken) {
    next('/admin/login')
    return
  }
  
  // 管理员访问普通用户页面
  if (!to.path.startsWith('/admin') && userRole === 'admin' && adminToken) {
    next('/admin')
    return
  }
  
  // 登录页面重定向
  if (to.path === '/login' && token) {
    next('/dashboard')
  } else if (to.path === '/register' && token) {
    next('/dashboard')
  } else if (to.path === '/admin/login' && adminToken) {
    next('/admin')
  } else {
    next()
  }
})

export default router
