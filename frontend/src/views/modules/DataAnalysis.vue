<template>
  <div class="data-analysis">
    <h1>数据分析中心</h1>
    <div class="module-content">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <h3>考试成绩分布</h3>
            </template>
            <div class="chart-container">
              <!-- 这里将使用 ECharts 显示成绩分布图 -->
              <div class="placeholder-chart">
                <el-empty description="成绩分布图表">
                  <el-button type="primary">加载数据</el-button>
                </el-empty>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <h3>题型正确率分析</h3>
            </template>
            <div class="chart-container">
              <!-- 这里将使用 ECharts 显示题型正确率分析图 -->
              <div class="placeholder-chart">
                <el-empty description="题型分析图表">
                  <el-button type="primary">加载数据</el-button>
                </el-empty>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="analysis-card">
        <template #header>
          <div class="card-header">
            <h3>考试数据统计</h3>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="handleDateChange"
            />
          </div>
        </template>
        <el-table :data="statisticsData" style="width: 100%">
          <el-table-column prop="examName" label="考试名称" />
          <el-table-column prop="totalStudents" label="参考人数" width="120" />
          <el-table-column prop="avgScore" label="平均分" width="120" />
          <el-table-column prop="passRate" label="及格率" width="120">
            <template #default="{ row }">
              {{ row.passRate }}%
            </template>
          </el-table-column>
          <el-table-column prop="maxScore" label="最高分" width="120" />
          <el-table-column prop="minScore" label="最低分" width="120" />
        </el-table>
      </el-card>

      <el-card class="analysis-card">
        <template #header>
          <h3>知识点掌握情况</h3>
        </template>
        <el-table :data="knowledgePoints" style="width: 100%">
          <el-table-column prop="point" label="知识点" />
          <el-table-column prop="mastery" label="掌握程度" width="200">
            <template #default="{ row }">
              <el-progress :percentage="row.mastery" :color="getMasteryColor(row.mastery)" />
            </template>
          </el-table-column>
          <el-table-column prop="recommendation" label="建议" show-overflow-tooltip />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'DataAnalysis',
  setup() {
    const dateRange = ref([])

    const statisticsData = ref([
      {
        examName: '2024年春季计算机基础考试',
        totalStudents: 150,
        avgScore: 75.5,
        passRate: 85,
        maxScore: 98,
        minScore: 45
      },
      {
        examName: '2024年软件工程期末考试',
        totalStudents: 85,
        avgScore: 82.3,
        passRate: 92,
        maxScore: 100,
        minScore: 60
      }
    ])

    const knowledgePoints = ref([
      {
        point: '操作系统基本概念',
        mastery: 85,
        recommendation: '建议复习进程管理相关内容'
      },
      {
        point: '计算机网络协议',
        mastery: 70,
        recommendation: '需要加强TCP/IP协议栈的学习'
      },
      {
        point: '数据结构与算法',
        mastery: 60,
        recommendation: '建议多做算法练习，特别是树和图的相关题目'
      }
    ])

    const handleDateChange = (val: any) => {
      console.log('日期范围改变:', val)
      // 这里将根据日期范围更新统计数据
    }

    const getMasteryColor = (percentage: number) => {
      if (percentage >= 80) return '#67C23A'
      if (percentage >= 60) return '#E6A23C'
      return '#F56C6C'
    }

    return {
      dateRange,
      statisticsData,
      knowledgePoints,
      handleDateChange,
      getMasteryColor
    }
  }
})
</script>

<style lang="scss" scoped>
.data-analysis {
  padding: 20px;

  h1 {
    margin-bottom: 20px;
    color: #303133;
  }

  .module-content {
    display: grid;
    gap: 20px;
  }

  .chart-card,
  .analysis-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    h3 {
      margin: 0;
      color: #409EFF;
    }
  }

  .chart-container {
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .placeholder-chart {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>