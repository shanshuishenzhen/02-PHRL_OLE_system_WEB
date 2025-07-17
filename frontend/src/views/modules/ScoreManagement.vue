<template>
  <div class="score-management">
    <h1>成绩管理</h1>
    <div class="module-content">
      <el-card class="filter-card">
        <div class="filter-form">
          <el-form :model="filterForm" inline>
            <el-form-item label="考试名称">
              <el-select v-model="filterForm.examId" placeholder="选择考试">
                <el-option
                  v-for="exam in examList"
                  :key="exam.id"
                  :label="exam.name"
                  :value="exam.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="班级">
              <el-select v-model="filterForm.classId" placeholder="选择班级">
                <el-option
                  v-for="cls in classList"
                  :key="cls.id"
                  :label="cls.name"
                  :value="cls.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="成绩范围">
              <el-input-number
                v-model="filterForm.minScore"
                :min="0"
                :max="100"
                placeholder="最低分"
              />
              <span class="separator">-</span>
              <el-input-number
                v-model="filterForm.maxScore"
                :min="0"
                :max="100"
                placeholder="最高分"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="searchScores">搜索</el-button>
              <el-button @click="resetFilter">重置</el-button>
              <el-button type="success" @click="exportScores">导出成绩</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <el-row :gutter="20">
        <el-col :span="16">
          <el-card class="score-list">
            <template #header>
              <div class="card-header">
                <h3>成绩列表</h3>
                <div class="header-actions">
                  <el-button type="primary" @click="batchEdit">批量修改</el-button>
                  <el-button @click="refreshScores">刷新</el-button>
                </div>
              </div>
            </template>

            <el-table
              :data="scores"
              style="width: 100%"
              @selection-change="handleSelectionChange"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="studentId" label="学号" width="120" />
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="className" label="班级" width="120" />
              <el-table-column prop="score" label="成绩" width="100">
                <template #default="{ row }">
                  <span :class="getScoreClass(row.score)">{{ row.score }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="rank" label="排名" width="80" />
              <el-table-column prop="submitTime" label="提交时间" width="180" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button size="small" @click="editScore(row)">修改</el-button>
                  <el-button size="small" type="primary" @click="viewDetail(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-container">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :total="total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card class="statistics-card">
            <template #header>
              <h3>成绩统计</h3>
            </template>

            <div class="stat-grid">
              <div class="stat-item">
                <div class="stat-label">平均分</div>
                <div class="stat-value">{{ statistics.average }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">最高分</div>
                <div class="stat-value success">{{ statistics.highest }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">最低分</div>
                <div class="stat-value warning">{{ statistics.lowest }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">及格率</div>
                <div class="stat-value">
                  <el-progress
                    :percentage="statistics.passRate"
                    :color="getProgressColor"
                  />
                </div>
              </div>
            </div>

            <div class="score-chart">
              <!-- 这里将使用 ECharts 显示成绩分布图 -->
              <div class="placeholder-chart">
                <el-empty description="成绩分布图表">
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
import { defineComponent, ref, computed } from 'vue'

export default defineComponent({
  name: 'ScoreManagement',
  setup() {
    const filterForm = ref({
      examId: '',
      classId: '',
      minScore: null,
      maxScore: null
    })

    const examList = ref([
      { id: '1', name: '2024春季计算机基础期末考试' },
      { id: '2', name: '软件工程期末考试' }
    ])

    const classList = ref([
      { id: '1', name: '计算机2401班' },
      { id: '2', name: '计算机2402班' }
    ])

    const scores = ref([
      {
        studentId: '2024001',
        name: '张三',
        className: '计算机2401班',
        score: 85,
        rank: 10,
        submitTime: '2024-03-15 11:30:00',
        status: '已批改'
      },
      {
        studentId: '2024002',
        name: '李四',
        className: '计算机2401班',
        score: 92,
        rank: 5,
        submitTime: '2024-03-15 11:25:00',
        status: '已批改'
      }
    ])

    const statistics = ref({
      average: 78.5,
      highest: 98,
      lowest: 45,
      passRate: 85
    })

    const currentPage = ref(1)
    const pageSize = ref(10)
    const total = ref(100)
    const selectedScores = ref([])

    const getScoreClass = (score: number) => {
      if (score >= 90) return 'score excellent'
      if (score >= 60) return 'score pass'
      return 'score fail'
    }

    const getStatusType = (status: string) => {
      const types: { [key: string]: string } = {
        '已批改': 'success',
        '待批改': 'warning',
        '缺考': 'danger'
      }
      return types[status] || 'info'
    }

    const getProgressColor = (percentage: number) => {
      if (percentage >= 80) return '#67C23A'
      if (percentage >= 60) return '#E6A23C'
      return '#F56C6C'
    }

    const searchScores = () => {
      console.log('搜索成绩:', filterForm.value)
    }

    const resetFilter = () => {
      filterForm.value = {
        examId: '',
        classId: '',
        minScore: null,
        maxScore: null
      }
    }

    const exportScores = () => {
      console.log('导出成绩')
    }

    const batchEdit = () => {
      console.log('批量修改成绩:', selectedScores.value)
    }

    const refreshScores = () => {
      console.log('刷新成绩列表')
    }

    const handleSelectionChange = (val: any[]) => {
      selectedScores.value = val
    }

    const editScore = (score: any) => {
      console.log('修改成绩:', score)
    }

    const viewDetail = (score: any) => {
      console.log('查看成绩详情:', score)
    }

    const handleSizeChange = (val: number) => {
      pageSize.value = val
      searchScores()
    }

    const handleCurrentChange = (val: number) => {
      currentPage.value = val
      searchScores()
    }

    return {
      filterForm,
      examList,
      classList,
      scores,
      statistics,
      currentPage,
      pageSize,
      total,
      getScoreClass,
      getStatusType,
      getProgressColor,
      searchScores,
      resetFilter,
      exportScores,
      batchEdit,
      refreshScores,
      handleSelectionChange,
      editScore,
      viewDetail,
      handleSizeChange,
      handleCurrentChange
    }
  }
})
</script>

<style lang="scss" scoped>
.score-management {
  padding: 20px;

  h1 {
    margin-bottom: 20px;
    color: #303133;
  }

  .module-content {
    display: grid;
    gap: 20px;
  }

  .filter-card {
    .filter-form {
      .el-form-item {
        margin-bottom: 0;
      }

      .separator {
        margin: 0 10px;
      }
    }
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

  .score {
    &.excellent {
      color: #67C23A;
      font-weight: bold;
    }

    &.pass {
      color: #409EFF;
    }

    &.fail {
      color: #F56C6C;
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .statistics-card {
    .stat-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
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

          &.warning {
            color: #E6A23C;
          }
        }
      }
    }

    .score-chart {
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
}
</style>