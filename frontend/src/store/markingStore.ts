export const useMarkingStore = defineStore('marking', {
  state: () => ({
    batchProgress: 0,
    currentBatch: null as BatchInfo | null,
    errorPapers: [] as string[]
  }),

  actions: {
    async processBatch(files: File[]) {
      this.batchProgress = 0
      for (const file of files) {
        try {
          await markPaper(file)
          this.batchProgress += (100 / files.length)
        } catch (e) {
          this.errorPapers.push(file.name)
        }
      }
    }
  }
})