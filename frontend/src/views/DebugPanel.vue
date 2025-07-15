<template>
  <div class="debug-container">
    <h1><el-icon><Setting /></el-icon> 系统调试面板</h1>
    
    <el-card class="debug-section">
      <template #header>
        <div class="section-header">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </div>
      </template>
      <div class="button-group">
        <el-button @click="handleImportUsers" type="primary">
          <el-icon><Upload /></el-icon>
          导入测试用户
        </el-button>
        <el-button @click="handleGetAllUsers" type="info">
          <el-icon><List /></el-icon>
          查看所有用户
        </el-button>
      </div>
      <el-table :data="users" border style="width: 100%; margin-top: 20px">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="username" label="用户名"></el-table-column>
        <el-table-column prop="role" label="角色"></el-table-column>
      </el-table>
    </el-card>

    <el-card class="debug-section">
      <template #header>
        <div class="section-header">
          <el-icon><Notebook /></el-icon>
          <span>考试管理</span>
        </div>
      </template>
      <div class="button-group">
        <el-button @click="handleGetExamList" type="primary">
          <el-icon><Collection /></el-icon>
          获取考试列表
        </el-button>
        <el-button @click="handleStartExam(1)" type="success">
          <el-icon><VideoPlay /></el-icon>
          开始考试(ID:1)
        </el-button>
        <el-button @click="handleEndExam(1)" type="danger">
          <el-icon><SwitchButton /></el-icon>
          结束考试(ID:1)
        </el-button>
      </div>
      <el-table :data="exams" border style="width: 100%; margin-top: 20px">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="name" label="考试名称"></el-table-column>
        <el-table-column prop="status" label="状态"></el-table-column>
      </el-table>
    </el-card>

    <el-card class="debug-section">
      <template #header>
        <div class="section-header">
          <el-icon><Warning /></el-icon>
          <span>防作弊测试</span>
        </div>
      </template>
      <div class="button-group">
        <el-button @click="handleSendWarning" type="warning">
          <el-icon><Bell /></el-icon>
          发送警告
        </el-button>
        <el-button @click="handleForceSubmit" type="danger">
          <el-icon><CircleClose /></el-icon>
          强制提交
        </el-button>
        <el-button @click="handleInitWebSocket('1')" type="primary">
          <el-icon><Connection /></el-icon>
          初始化WebSocket(考试ID:1)
        </el-button>
      </div>
      <div class="log-container">
        <h3><el-icon><Document /></el-icon> 操作日志</h3>
        <pre>{{ logs }}</pre>
      </div>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { defineExpose } from 'vue'
import {
  Setting,
  User,
  Upload,
  List,
  Notebook,
  Collection,
  VideoPlay,
  SwitchButton,
  Warning,
  Bell,
  CircleClose,
  Connection,
  Document
} from '@element-plus/icons-vue'
import {
  importUsers,
  listAllUsers
} from '@/api/auth'
import {
  initWebSocket,
  testWarning,
  testForceSubmit
} from '@/api/websocket'
import {
  startExam,
  endExam,
  listExams
} from '@/api/exam'

const users = ref<any[]>([])
const exams = ref<any[]>([])
const logs = ref('')

const addLog = (message: string) => {
  logs.value += `[${new Date().toLocaleTimeString()}] ${message}\n`
}

const handleApiCall = async (fn: Function, ...args: any[]) => {
  try {
    addLog(`调用: ${fn.name}(${args.join(', ')})`)
    const result = await fn(...args)
    addLog(`成功: ${JSON.stringify(result, null, 2)}`)
    return result
  } catch (error) {
    addLog(`错误: ${(error as Error).message}`)
    throw error
  }
}

const handleImportUsers = async () => {
  users.value = await handleApiCall(importUsers)
}

const handleGetAllUsers = async () => {
  users.value = await handleApiCall(listAllUsers)
}

const handleGetExamList = async () => {
  exams.value = await handleApiCall(listExams)
}

const handleInitWebSocket = async (examId: string) => {
  await handleApiCall(initWebSocket, examId)
}

const handleStartExam = async (id: number) => {
  await handleApiCall(startExam, id)
}

const handleEndExam = async (id: number) => {
  await handleApiCall(endExam, id)
}

const handleSendWarning = () => {
  handleApiCall(testWarning, '测试警告消息')
}

const handleForceSubmit = () => {
  handleApiCall(testForceSubmit)
}
defineExpose({
  handleImportUsers,
  handleGetAllUsers,
  handleGetExamList,
  handleStartExam,
  handleEndExam,
  handleSendWarning,
  handleForceSubmit,
  handleInitWebSocket
})
</script>

<style scoped>
.debug-container {
  padding: 20px;
}

.debug-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}

.section-header .el-icon {
  font-size: 20px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.button-group .el-icon {
  margin-right: 5px;
}

.log-container {
  margin-top: 20px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>