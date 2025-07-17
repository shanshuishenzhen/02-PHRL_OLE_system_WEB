<template>
  <div class="exam-monitor">
    <h1>考试监控中心</h1>
    <div class="module-content">
      <el-card class="function-card">
        <template #header>
          <div class="card-header">
            <h3>实时考试状态</h3>
            <el-tag type="success">{{ activeExams.length }}场考试进行中</el-tag>
          </div>
        </template>
        <el-table :data="activeExams" style="width: 100%">
          <el-table-column prop="name" label="考试名称" />
          <el-table-column prop="startTime" label="开始时间" width="180" />
          <el-table-column prop="duration" label="持续时间" width="120" />
          <el-table-column prop="participants" label="参考人数" width="120" />
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-tag :type="scope.row.status === '正常' ? 'success' : 'danger'">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button size="small" type="primary" @click="monitorExam(scope.row)">监控</el-button>
              <el-button size="small" type="warning" @click="endExam(scope.row)">结束</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <div class="monitor-grid">
        <el-card class="monitor-card">
          <template #header>
            <h3>异常行为检测</h3>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="event in anomalyEvents"
              :key="event.id"
              :type="event.type"
              :timestamp="event.time"
            >
              {{ event.description }}
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card class="monitor-card">
          <template #header>
            <h3>系统资源监控</h3>
          </template>
          <div class="resource-stats">
            <div class="stat-item">
              <div class="stat-label">CPU 使用率</div>
              <el-progress :percentage="systemStats.cpu" :color="getProgressColor" />
            </div>
            <div class="stat-item">
              <div class="stat-label">内存使用率</div>
              <el-progress :percentage="systemStats.memory" :color="getProgressColor" />
            </div>
            <div class="stat-item">
              <div class="stat-label">网络带宽使用率</div>
              <el-progress :percentage="systemStats.network" :color="getProgressColor" />
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'

export default defineComponent({
  name: 'ExamMonitor',
  setup() {
    const activeExams = ref([
      {
        name: '2024年春季计算机基础考试',
        startTime: '2024-03-15 09:00:00',
        duration: '120分钟',
        participants: 150,
        status: '正常'
      },
      {
        name: '2024年软件工程期末考试',
        startTime: '2024-03-15 10:30:00',
        duration: '90分钟',
        participants: 85,
        status: '异常'
      }
    ])

    const anomalyEvents = ref([
      {
        id: 1,
        type: 'warning',
        time: '10:15:30',
        description: '考生[2024001]切换窗口次数异常'
      },
      {
        id: 2,
        type: 'danger',
        time: '10:18:45',
        description: '考生[2024015]检测到人脸离开画面'
      },
      {
        id: 3,
        type: 'warning',
        time: '10:20:12',
        description: '考生[2024008]网络连接不稳定'
      }
    ])

    const systemStats = ref({
      cpu: 45,
      memory: 60,
      network: 30
    })

    const getProgressColor = (percentage: number) => {
      if (percentage < 50) return '#67C23A'
      if (percentage < 80) return '#E6A23C'
      return '#F56C6C'
    }

    const monitorExam = (exam: any) => {
      console.log('监控考试:', exam)
    }

    const endExam = (exam: any) => {
      console.log('结束考试:', exam)
    }

    return {
      activeExams,
      anomalyEvents,
      systemStats,
      getProgressColor,
      monitorExam,
      endExam
    }
  }
})
</script>

<style lang="scss" scoped>
.exam-monitor {
  padding: 20px;

  h1 {
    margin-bottom: 20px;
    color: #303133;
  }

  .module-content {
    display: grid;
    gap: 20px;
  }

  .function-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        color: #409EFF;
      }
    }
  }

  .monitor-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
  }

  .monitor-card {
    h3 {
      margin: 0;
      color: #409EFF;
    }
  }

  .resource-stats {
    .stat-item {
      margin-bottom: 20px;

      &:last-child {
        margin-bottom: 0;
      }

      .stat-label {
        margin-bottom: 8px;
        color: #606266;
      }
    }
  }
}
</style>