<template>
  <div class="debug-dashboard">
    <header>
      <h1>职业技能等级认证考试系统 - 调试面板</h1>
    </header>
    
    <div class="container">
      <div class="status-panel">
        <h2>系统状态</h2>
        <div class="status-grid">
          <div class="status-item" :class="{ online: backendStatus, offline: !backendStatus }">
            <div class="status-icon">🔌</div>
            <div class="status-name">后端服务</div>
            <div class="status-info">{{ backendStatus ? '在线' : '离线' }}</div>
          </div>
          <div class="status-item" :class="{ online: databaseStatus, offline: !databaseStatus }">
            <div class="status-icon">💾</div>
            <div class="status-name">数据库</div>
            <div class="status-info">{{ databaseStatus ? '已连接' : '未连接' }}</div>
          </div>
        </div>
      </div>

      <div class="environment-panel">
        <h2>环境依赖</h2>
        <div class="deps-grid">
          <div class="deps-section">
            <h3>前端依赖</h3>
            <ul>
              <li>Vue: v3.4.0</li>
              <li>Element Plus: v2.10.4</li>
              <li>Vue Router: v4.2.0</li>
              <li>Pinia: v2.1.0</li>
              <li>Axios: v1.10.0</li>
              <li>TypeScript: v5.0.0</li>
              <li>Vite: v5.0.0</li>
              <li>Sass: v1.89.2</li>
            </ul>
          </div>
          <div class="deps-section">
            <h3>后端依赖</h3>
            <ul>
              <li>Django: v4.2.0+</li>
              <li>DRF: v3.14.0+</li>
              <li>Channels: v4.0.0+</li>
              <li>PostgreSQL: v2.9.6+</li>
              <li>Redis: v4.5.5+</li>
              <li>JWT: v2.7.0+</li>
              <li>Gunicorn: v20.1.0+</li>
              <li>Whitenoise: v6.4.0+</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="dashboard">
        <div class="module-card">
          <h2>用户管理</h2>
          <p>管理系统用户、角色和权限</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/user-management')">打开模块</el-button>
            <el-button type="success" @click="runTests('user')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>试题库</h2>
          <p>管理考试题目和题库</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/question-bank')">打开模块</el-button>
            <el-button type="success" @click="runTests('question')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>考试试卷</h2>
          <p>创建和管理考试试卷</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/exam-paper')">打开模块</el-button>
            <el-button type="success" @click="runTests('paper')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>考试监控</h2>
          <p>实时监控考试进行状态</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/exam-monitor')">打开模块</el-button>
            <el-button type="success" @click="runTests('monitor')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>评分中心</h2>
          <p>批改试卷和评分管理</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/marking-center')">打开模块</el-button>
            <el-button type="success" @click="runTests('marking')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>成绩管理</h2>
          <p>管理和分析考试成绩</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/score-management')">打开模块</el-button>
            <el-button type="success" @click="runTests('score')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>数据分析</h2>
          <p>分析考试数据和统计</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/data-analysis')">打开模块</el-button>
            <el-button type="success" @click="runTests('analysis')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>日志审计</h2>
          <p>系统日志和操作审计</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/log-audit')">打开模块</el-button>
            <el-button type="success" @click="runTests('audit')">运行测试</el-button>
          </div>
        </div>

        <div class="module-card">
          <h2>学生考试</h2>
          <p>学生在线考试界面</p>
          <div class="actions">
            <el-button type="primary" @click="openModule('/student-exam')">打开模块</el-button>
            <el-button type="success" @click="runTests('exam')">运行测试</el-button>
          </div>
        </div>
      </div>

      <div class="tools-section">
        <h2>开发工具</h2>
        <div class="tools-grid">
          <el-button @click="openTool('api-tester')">API 测试工具</el-button>
          <el-button @click="openTool('websocket-tester')">WebSocket 测试</el-button>
          <el-button @click="openTool('log-viewer')">日志查看器</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default defineComponent({
  name: 'DebugDashboard',
  setup() {
    const router = useRouter()
    const backendStatus = ref(false)
    const databaseStatus = ref(false)

    const checkSystemStatus = async () => {
      try {
        const response = await axios.get('/api/debug/system-status/')
        backendStatus.value = response.data.backend_status
        databaseStatus.value = response.data.database_status
      } catch (error) {
        console.error('检查系统状态失败:', error)
        backendStatus.value = false
        databaseStatus.value = false
      }
    }

    const openModule = (path: string) => {
      router.push(path)
    }

    const runTests = async (module: string) => {
      try {
        const response = await axios.post(`/api/tests/run/${module}`)
        console.log(`${module} 测试结果:`, response.data)
      } catch (error) {
        console.error(`运行 ${module} 测试失败:`, error)
      }
    }

    const openTool = (tool: string) => {
      window.open(`/${tool}.html`, '_blank')
    }

    onMounted(() => {
      checkSystemStatus()
      // 每 30 秒检查一次系统状态
      setInterval(checkSystemStatus, 30000)
    })

    return {
      backendStatus,
      databaseStatus,
      openModule,
      runTests,
      openTool
    }
  }
})
</script>

<style lang="scss" scoped>
@use "../assets/styles/debug.scss" as *;
</style>