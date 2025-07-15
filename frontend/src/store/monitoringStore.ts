export const useMonitoringStore = defineStore('monitoring', {
  state: () => ({
    wsStatus: 'disconnected',
    liveEvents: [] as MonitoringEvent[],
    alertCount: 0
  }),

  actions: {
    handleNewEvent(event: MonitoringEvent) {
      if (event.severity === 'high') this.alertCount++
      this.liveEvents.unshift(event)
    }
  }
})