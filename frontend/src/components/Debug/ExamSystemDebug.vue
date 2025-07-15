<template>
  <div class="debug-card">
    <h3>考试系统调试</h3>
    <button @click="testPaperGeneration">模拟组卷</button>
    <button @click="testExamStart">模拟开考</button>
    <div class="response-box">{{ response }}</div>
  </div>
</template>

<script setup>
import { useDebugStore } from '@/store/debugStore'

const debugStore = useDebugStore()

const testPaperGeneration = async () => {
  await debugStore.generateTestPaper()
}
</script>
import { useExamStore } from '@/store/exam'

const response = ref('')
const examStore = useExamStore()

const testPaperGeneration = async () => {
  response.value = await examStore.generateTestPaper()
}
</script>