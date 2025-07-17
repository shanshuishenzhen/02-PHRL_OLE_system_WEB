import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import DebugDashboard from './views/DebugDashboard.vue'
import DebugApp from './DebugApp.vue'
import '@/assets/styles/debug.scss'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: DebugDashboard
    }
  ]
})

const app = createApp(DebugApp)
app.use(ElementPlus)
app.use(router)
app.mount('#app')