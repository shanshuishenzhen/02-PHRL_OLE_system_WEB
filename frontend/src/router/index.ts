import { createRouter, createWebHistory } from 'vue-router'
import ExamSystem from '@/views/ExamSystem.vue'

const routes = [
  {
    path: '/',
    redirect: '/exam-system'
  },
  {
    path: '/exam-system',
    name: 'ExamSystem',
    component: ExamSystem
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router