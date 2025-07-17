<template>
  <div class="exam-paper">
    <h1>试卷管理</h1>
    <div class="module-content">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card class="paper-list">
            <template #header>
              <div class="card-header">
                <h3>试卷列表</h3>
                <div class="header-actions">
                  <el-button type="success" @click="generatePaper">智能组卷</el-button>
                  <el-button type="primary" @click="createPaper">新建试卷</el-button>
                </div>
              </div>
            </template>
            
            <el-table :data="papers" style="width: 100%">
              <el-table-column prop="name" label="试卷名称" />
              <el-table-column prop="subject" label="科目" width="120" />
              <el-table-column prop="totalScore" label="总分" width="80" />
              <el-table-column prop="duration" label="时长" width="100">
                <template #default="{ row }">
                  {{ row.duration }}分钟
                </template>
              </el-table-column>
              <el-table-column prop="questionCount" label="题目数" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === '已发布' ? 'success' : 'info'">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="250">
                <template #default="{ row }">
                  <el-button size="small" @click="editPaper(row)">编辑</el-button>
                  <el-button size="small" type="success" @click="previewPaper(row)">预览</el-button>
                  <el-button 
                    size="small" 
                    :type="row.status === '已发布' ? 'warning' : 'primary'"
                    @click="togglePaperStatus(row)"
                  >
                    {{ row.status === '已发布' ? '撤回' : '发布' }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card class="paper-stats">
            <template #header>
              <h3>试卷统计</h3>
            </template>
            <div class="stats-content">
              <div class="stat-item">
                <div class="stat-label">试卷总数</div>
                <div class="stat-value">{{ stats.totalPapers }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">已发布</div>
                <div class="stat-value success">{{ stats.publishedPapers }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">草稿</div>
                <div class="stat-value info">{{ stats.draftPapers }}</div>
              </div>
            </div>

            <el-divider>试卷分布</el-divider>
            
            <div class="distribution-chart">
              <!-- 这里将使用 ECharts 显示试卷分布图 -->
              <div class="placeholder-chart">
                <el-empty description="试卷分布图表">
                  <el-button type="primary">加载数据</el-button>
                </el-empty>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'ExamPaper',
  setup() {
    const papers = ref([
      {
        name: '2024春季计算机基础期末考试',
        subject: '计算机基础',
        totalScore: 100,
        duration: 120,
        questionCount: 50,
        status: '已发布'
      },
      {
        name: '软件工程模拟试卷A',
        subject: '软件工程',
        totalScore: 100,
        duration: 90,
        questionCount: 40,
        status: '草稿'
      }
    ])

    const stats = ref({
      totalPapers: 25,
      publishedPapers: 15,
      draftPapers: 10
    })

    const generatePaper = () => {
      console.log('智能组卷')
    }

    const createPaper = () => {
      console.log('新建试卷')
    }

    const editPaper = (paper: any) => {
      console.log('编辑试卷:', paper)
    }

    const previewPaper = (paper: any) => {
      console.log('预览试卷:', paper)
    }

    const togglePaperStatus = (paper: any) => {
      console.log('切换试卷状态:', paper)
    }

    return {
      papers,
      stats,
      generatePaper,
      createPaper,
      editPaper,
      previewPaper,
      togglePaperStatus
    }
  }
})
</script>

<style lang="scss" scoped>
.exam-paper {
  padding: 20px;

  h1 {
    margin-bottom: 20px;
    color: #303133;
  }

  .module-content {
    display: grid;
    gap: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      color: #409EFF;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .stats-content {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 20px;

    .stat-item {
      text-align: center;

      .stat-label {
        color: #909399;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #303133;

        &.success {
          color: #67C23A;
        }

        &.info {
          color: #909399;
        }
      }
    }
  }

  .distribution-chart {
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