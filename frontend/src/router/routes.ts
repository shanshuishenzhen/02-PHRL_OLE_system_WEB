import { RouteRecordRaw } from 'vue-router';
import DebugDashboard from '@/views/DebugDashboard.vue';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/debug-dashboard',
    name: 'DebugDashboard',
    component: DebugDashboard,
    meta: {
      title: '调试面板',
      requiresAuth: false
    }
  }
];

export default routes;