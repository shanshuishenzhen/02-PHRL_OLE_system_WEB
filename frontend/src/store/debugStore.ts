import { defineStore } from 'pinia'

export const useDebugStore = defineStore('debug', {
  state: () => ({
    examSimulation: {
      status: 'idle',
      paperData: null as any,
      error: ''
    },
    monitoringEvents: [] as string[],
    scoringResults: [] as any[]
  }),

  actions: {
    async generateTestPaper() {
      try {
        this.examSimulation.status = 'loading'
        const res = await simulateExamStart({ /*...*/ })
        this.examSimulation.paperData = res.data
      } catch (e) {
        this.examSimulation.error = e.message
      }
    }
  },

  getters: {
    formattedEvents: (state) => {
      return state.monitoringEvents.map((e, i) => `${i + 1}. ${e}`)
    }
  }
})