<template>
  <div class="debug-card">
    <h3>阅卷系统调试</h3>
    <input type="file" @change="handleUpload">
    <div v-if="scoringResult">
      <h4>评分结果：</h4>
      <pre>{{ scoringResult }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { markPaper } from '@/api/marking'

const scoringResult = ref(null)

const handleUpload = async (e) => {
  const file = e.target.files[0]
  scoringResult.value = await markPaper(file)
}
</script>