import { createRouter, createWebHistory } from 'vue-router'
import ScreenshotTest from '@/views/ScreenshotTest.vue'
import ExamSystem from '@/views/ExamSystem.vue'

const routes = [
  {
    path: '/',
    redirect: '/exam-system'  // 修改为正式考试系统路径
  },
  {
    path: '/exam-system',
    name: 'ExamSystem',
    component: ExamSystem
  },
  {
    path: '/screenshot-test',
    name: 'ScreenshotTest',
    component: ScreenshotTest
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router