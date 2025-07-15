export const useUserStore = defineStore('user', {
  state: () => ({
    currentRole: 'guest',
    permissions: {
      canDebug: false,
      canMonitor: false
    },
    debugHistory: [] as string[]
  }),

  actions: {
    updatePermissions(role: string) {
      this.currentRole = role
      this.permissions = role === 'admin' 
        ? { canDebug: true, canMonitor: true }
        : { canDebug: false, canMonitor: false }
    }
  }
})