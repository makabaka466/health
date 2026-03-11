import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
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
        component: () => import('../views/AiAssistant.vue')
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
        path: 'ai-chat',
        name: 'AdminAIChat',
        component: () => import('../views/AiAssistant.vue')
      },
      {
        path: 'knowledge-base',
        name: 'AdminKnowledgeBase',
        component: () => import('../views/AdminKnowledgeBase.vue')
      },
      {
        path: 'articles',
        name: 'AdminArticles',
        component: () => import('../views/AdminArticles.vue')
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('../views/admin/AdminSettings.vue')
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('../views/admin/AdminLogs.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const adminToken = localStorage.getItem('adminToken')
  const userRole = localStorage.getItem('userRole')

  if (to.meta.requiresAuth && !token && !adminToken) {
    next('/login')
    return
  }

  if (to.meta.requiresAdmin && !adminToken) {
    next('/login')
    return
  }

  if (to.path.startsWith('/admin') && !adminToken) {
    next('/login')
    return
  }

  if (!to.path.startsWith('/admin') && userRole === 'admin' && adminToken) {
    next('/admin')
    return
  }

  if (to.path === '/login' && adminToken) {
    next('/admin')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
