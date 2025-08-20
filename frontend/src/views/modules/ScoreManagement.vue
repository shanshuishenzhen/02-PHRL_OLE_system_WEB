<template>
  <div class="score-management">
    <h1>成绩管理</h1>
    <div class="module-content">
      <el-card class="filter-card">
        <div class="filter-form">
          <el-form :model="filterForm" inline>
            <el-form-item label="考试名称">
              <el-select v-model="filterForm.exam" placeholder="选择考试" clearable>
                <el-option
                  v-for="exam in examList"
                  :key="exam.id"
                  :label="exam.name"
                  :value="exam.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="成绩范围">
              <el-input-number
                v-model="filterForm.total_score__gte"
                :min="0"
                :max="100"
                placeholder="最低分"
              />
              <span class="separator">-</span>
              <el-input-number
                v-model="filterForm.total_score__lte"
                :min="0"
                :max="100"
                placeholder="最高分"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="searchScores" :loading="isLoading">搜索</el-button>
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
              v-loading="isLoading"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="exam_record.student.username" label="学号" width="120" />
              <el-table-column prop="exam_record.student.username" label="姓名" width="100" />
              <el-table-column prop="exam.name" label="考试科目" width="180" />
              <el-table-column prop="total_score" label="成绩" width="100">
                <template #default="{ row }">
                  <span :class="getScoreClass(row.total_score)">{{ row.total_score }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="is_passed" label="是否及格" width="100">
                <template #default="{ row }">
                    <el-tag :type="row.is_passed ? 'success' : 'danger'">
                        {{ row.is_passed ? '是' : '否' }}
                    </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="marked_at" label="批改时间" width="180" />
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
import { defineComponent, ref, computed, onMounted } from 'vue'
import { getScoreSheets, exportScores, ScoreSheet } from '@/api/score';
import { ElMessage } from 'element-plus';

export default defineComponent({
  name: 'ScoreManagement',
  setup() {
    const filterForm = ref({
      exam: '',
      // classId: '', // Filtering by class might need a separate API
      total_score__gte: null,
      total_score__lte: null
    })

    // Mock data for filters - in a real app, this would come from an API
    const examList = ref([
      { id: '1', name: '2024春季计算机基础期末考试' },
      { id: '2', name: '软件工程期末考试' }
    ])

    const scores = ref<ScoreSheet[]>([])
    const isLoading = ref(false);

    const statistics = computed(() => {
        if (scores.value.length === 0) {
            return { average: 0, highest: 0, lowest: 0, passRate: 0 };
        }
        const totalScores = scores.value.map(s => s.total_score);
        const highest = Math.max(...totalScores);
        const lowest = Math.min(...totalScores);
        const average = totalScores.reduce((a, b) => a + b, 0) / scores.value.length;
        const passCount = scores.value.filter(s => s.is_passed).length;
        const passRate = (passCount / scores.value.length) * 100;
        return {
            average: parseFloat(average.toFixed(1)),
            highest,
            lowest,
            passRate: parseFloat(passRate.toFixed(1))
        };
    });

    const currentPage = ref(1)
    const pageSize = ref(10)
    const total = ref(0)
    const selectedScores = ref<ScoreSheet[]>([])

    const getScoreClass = (score: number) => {
      if (score >= 90) return 'score excellent'
      if (score >= 60) return 'score pass'
      return 'score fail'
    }

    const getStatusType = (status: string) => {
      const types: { [key: string]: string } = {
        'completed': 'success',
        'reviewed': 'success',
        'in_progress': 'warning',
        'pending': 'info'
      }
      return types[status] || 'info'
    }

    const getProgressColor = (percentage: number) => {
      if (percentage >= 80) return '#67C23A'
      if (percentage >= 60) return '#E6A23C'
      return '#F56C6C'
    }

    const searchScores = async () => {
        isLoading.value = true;
        try {
            // Remove null/empty values from filter
            const validFilters = Object.entries(filterForm.value).reduce((acc, [key, value]) => {
                if (value !== null && value !== '') {
                    acc[key] = value;
                }
                return acc;
            }, {} as Record<string, any>);

            const response = await getScoreSheets(validFilters);
            scores.value = response;
            total.value = response.length; // Assuming API does not support pagination for now
        } catch (error) {
            ElMessage.error('搜索成绩失败');
            console.error(error);
        } finally {
            isLoading.value = false;
        }
    }

    const resetFilter = () => {
      filterForm.value = {
        exam: '',
        total_score__gte: null,
        total_score__lte: null
      }
      searchScores();
    }

    const handleExportScores = async () => {
        try {
            const blob = await exportScores(filterForm.value);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'scores.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            ElMessage.success('导出成功');
        } catch (error) {
            ElMessage.error('导出失败');
            console.error(error);
        }
    }

    onMounted(() => {
        searchScores();
    });

    const batchEdit = () => {
      console.log('批量修改成绩:', selectedScores.value)
      ElMessage.info('此功能待开发');
    }

    const refreshScores = () => {
      searchScores();
    }

    const handleSelectionChange = (val: ScoreSheet[]) => {
      selectedScores.value = val
    }

    const editScore = (score: ScoreSheet) => {
      console.log('修改成绩:', score)
      ElMessage.info('此功能待开发');
    }

    const viewDetail = (score: ScoreSheet) => {
      console.log('查看成绩详情:', score)
      ElMessage.info('此功能待开发');
    }

    const handleSizeChange = (val: number) => {
      pageSize.value = val
      // searchScores() // Re-enable if API supports pagination
    }

    const handleCurrentChange = (val: number) => {
      currentPage.value = val
      // searchScores() // Re-enable if API supports pagination
    }

    return {
      filterForm,
      examList,
      scores,
      statistics,
      currentPage,
      pageSize,
      total,
      isLoading,
      getScoreClass,
      getStatusType,
      getProgressColor,
      searchScores,
      resetFilter,
      exportScores: handleExportScores,
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