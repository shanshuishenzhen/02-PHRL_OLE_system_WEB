import { createRouter, createWebHashHistory } from 'vue-router'
import ExamSystem from '@/views/ExamSystem.vue'
import { setupRouteGuard } from './guard'
import { useUserStore } from '@/stores/user'
import routes from './routes'

const baseRoutes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/exam-system',
    name: 'ExamSystem',
    component: ExamSystem
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: () => import('@/views/modules/UserManagement.vue')
  },
  {
    path: '/question-bank',
    name: 'QuestionBank',
    component: () => import('@/views/modules/QuestionBank.vue')
  },
  {
    path: '/exam-monitor',
    name: 'ExamMonitor',
    component: () => import('@/views/modules/ExamMonitor.vue')
  },
  {
    path: '/data-analysis',
    name: 'DataAnalysis',
    component: () => import('@/views/modules/DataAnalysis.vue')
  },
  {
    path: '/exam-paper',
    name: 'ExamPaper',
    component: () => import('@/views/modules/ExamPaper.vue')
  },
  {
    path: '/log-audit',
    name: 'LogAudit',
    component: () => import('@/views/modules/LogAudit.vue')
  },
  {
    path: '/marking-center',
    name: 'MarkingCenter',
    component: () => import('@/views/modules/MarkingCenter.vue')
  },
  {
    path: '/score-management',
    name: 'ScoreManagement',
    component: () => import('@/views/modules/ScoreManagement.vue')
  },
  {
    path: '/student-exam',
    name: 'StudentExam',
    component: () => import('@/views/modules/StudentExam.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [...baseRoutes, ...routes]
})

// 全局路由守卫：检查登录状态
// 临时禁用所有路由守卫
router.beforeEach((to, from, next) => {
  next()
})

setupRouteGuard(router)

export default router