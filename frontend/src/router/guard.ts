import { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useUserStore } from '@/stores/user'

export const setupRouteGuard = (router: any) => {
  router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
    const userStore = useUserStore()
    
    // 调试面板允许所有用户访问
    if (to.path === '/debug-dashboard') {
      return next()
    }
    
    // 检查登录状态(token是否存在)
    if (!userStore.token && to.path !== '/login') {
      return next('/login')
    }
    
    next()
  })
}