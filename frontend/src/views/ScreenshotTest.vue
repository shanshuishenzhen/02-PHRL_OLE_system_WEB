<template>
  <div class="test-container">
    <h1>截图功能测试</h1>
    
    <div class="exam-area" id="examArea">
      <h2>考试内容区域</h2>
      <p>这是一些模拟的考试内容...</p>
    </div>

    <button @click="testFullPage">测试全屏截图</button>
    <button @click="testExamArea">测试考试区域截图</button>

    <div v-if="previewUrl" class="preview">
      <h3>截图预览</h3>
      <img :src="previewUrl" alt="截图预览"/>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { captureFullPage, captureExamArea } from '@/utils/screenshot'

const previewUrl = ref('')

async function testFullPage() {
  try {
    const blob = await captureFullPage()
    previewUrl.value = URL.createObjectURL(blob)
    console.log('全屏截图成功', blob)
  } catch (error) {
    console.error('全屏截图失败:', error)
  }
}

async function testExamArea() {
  try {
    const blob = await captureExamArea('#examArea') 
    previewUrl.value = URL.createObjectURL(blob)
    console.log('考试区域截图成功', blob)
  } catch (error) {
    console.error('考试区域截图失败:', error)
  }
}
</script>

<style scoped>
.test-container {
  padding: 20px;
}
.exam-area {
  border: 2px dashed #ccc;
  padding: 20px;
  margin: 20px 0;
}
button {
  margin-right: 10px;
  padding: 8px 16px;
}
.preview {
  margin-top: 20px;
}
.preview img {
  max-width: 100%;
  border: 1px solid #eee;
}
</style>