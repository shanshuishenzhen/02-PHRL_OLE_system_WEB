<template>
  <div class="log-audit">
    <h1>日志审计</h1>
    <div class="module-content">
      <el-card class="filter-card">
        <div class="filter-form">
          <el-form :model="filterForm" inline>
            <el-form-item label="日志类型">
              <el-select v-model="filterForm.type" placeholder="选择日志类型">
                <el-option label="系统日志" value="system" />
                <el-option label="操作日志" value="operation" />
                <el-option label="安全日志" value="security" />
                <el-option label="考试日志" value="exam" />
              </el-select>
            </el-form-item>

            <el-form-item label="时间范围">
              <el-date-picker
                v-model="filterForm.dateRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
              />
            </el-form-item>

            <el-form-item label="日志级别">
              <el-select v-model="filterForm.level" placeholder="选择日志级别">
                <el-option label="INFO" value="info" />
                <el-option label="WARNING" value="warning" />
                <el-option label="ERROR" value="error" />
                <el-option label="CRITICAL" value="critical" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="searchLogs">搜索</el-button>
              <el-button @click="resetFilter">重置</el-button>
              <el-button type="success" @click="exportLogs">导出日志</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <el-card class="log-list">
        <template #header>
          <div class="card-header">
            <h3>日志记录</h3>
            <el-switch
              v-model="autoRefresh"
              active-text="自动刷新"
              inactive-text="手动刷新"
              @change="handleAutoRefreshChange"
            />
          </div>
        </template>

        <el-table :data="logs" style="width: 100%">
          <el-table-column prop="timestamp" label="时间" width="180" />
          <el-table-column prop="type" label="类型" width="100" />
          <el-table-column prop="level" label="级别" width="100">
            <template #default="{ row }">
              <el-tag :type="getLogLevelType(row.level)">
                {{ row.level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="user" label="操作用户" width="120" />
          <el-table-column prop="module" label="模块" width="120" />
          <el-table-column prop="message" label="日志内容" show-overflow-tooltip />
          <el-table-column prop="ip" label="IP地址" width="120" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewLogDetail(row)">详情</el-button>
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

      <el-dialog
        v-model="logDetailVisible"
        title="日志详情"
        width="60%"
      >
        <div v-if="selectedLog" class="log-detail">
          <div class="detail-item">
            <span class="label">时间：</span>
            <span class="value">{{ selectedLog.timestamp }}</span>
          </div>
          <div class="detail-item">
            <span class="label">类型：</span>
            <span class="value">{{ selectedLog.type }}</span>
          </div>
          <div class="detail-item">
            <span class="label">级别：</span>
            <span class="value">
              <el-tag :type="getLogLevelType(selectedLog.level)">
                {{ selectedLog.level }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">操作用户：</span>
            <span class="value">{{ selectedLog.user }}</span>
          </div>
          <div class="detail-item">
            <span class="label">模块：</span>
            <span class="value">{{ selectedLog.module }}</span>
          </div>
          <div class="detail-item">
            <span class="label">IP地址：</span>
            <span class="value">{{ selectedLog.ip }}</span>
          </div>
          <div class="detail-item full-width">
            <span class="label">日志内容：</span>
            <div class="value message">{{ selectedLog.message }}</div>
          </div>
          <div class="detail-item full-width">
            <span class="label">详细信息：</span>
            <pre class="value details">{{ selectedLog.details }}</pre>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'LogAudit',
  setup() {
    const filterForm = ref({
      type: '',
      dateRange: [],
      level: ''
    })

    const logs = ref([
      {
        timestamp: '2024-03-15 10:30:15',
        type: '操作日志',
        level: 'INFO',
        user: 'admin',
        module: '用户管理',
        message: '创建新用户：user001',
        ip: '192.168.1.100',
        details: JSON.stringify({
          action: "create_user",
          user_id: "user001",
          role: "student",
          status: "success"
        }, null, 2)
      },
      {
        timestamp: '2024-03-15 10:35:22',
        type: '安全日志',
        level: 'WARNING',
        user: 'user002',
        module: '认证',
        message: '多次登录失败',
        ip: '192.168.1.101',
        details: JSON.stringify({
          action: "login",
          attempts: 3,
          status: "failed",
          reason: "incorrect_password"
        }, null, 2)
      }
    ])

    const currentPage = ref(1)
    const pageSize = ref(10)
    const total = ref(100)
    const autoRefresh = ref(false)
    const logDetailVisible = ref(false)
    const selectedLog = ref(null)

    const searchLogs = () => {
      console.log('搜索日志:', filterForm.value)
    }

    const resetFilter = () => {
      filterForm.value = {
        type: '',
        dateRange: [],
        level: ''
      }
    }

    const exportLogs = () => {
      console.log('导出日志')
    }

    const handleAutoRefreshChange = (val: boolean) => {
      console.log('自动刷新状态:', val)
    }

    const getLogLevelType = (level: string) => {
      const types: { [key: string]: string } = {
        'INFO': 'info',
        'WARNING': 'warning',
        'ERROR': 'danger',
        'CRITICAL': 'danger'
      }
      return types[level] || 'info'
    }

    const viewLogDetail = (log: any) => {
      selectedLog.value = log
      logDetailVisible.value = true
    }

    const handleSizeChange = (val: number) => {
      pageSize.value = val
      searchLogs()
    }

    const handleCurrentChange = (val: number) => {
      currentPage.value = val
      searchLogs()
    }

    return {
      filterForm,
      logs,
      currentPage,
      pageSize,
      total,
      autoRefresh,
      logDetailVisible,
      selectedLog,
      searchLogs,
      resetFilter,
      exportLogs,
      handleAutoRefreshChange,
      getLogLevelType,
      viewLogDetail,
      handleSizeChange,
      handleCurrentChange
    }
  }
})
</script>

<style lang="scss" scoped>
.log-audit {
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
    }
  }

  .log-list {
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

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .log-detail {
    .detail-item {
      margin-bottom: 15px;
      display: flex;

      &.full-width {
        flex-direction: column;

        .value {
          margin-top: 10px;
        }
      }

      .label {
        width: 100px;
        color: #909399;
      }

      .value {
        flex: 1;
        color: #303133;

        &.message {
          white-space: pre-wrap;
          word-break: break-all;
        }

        &.details {
          background: #f5f7fa;
          padding: 10px;
          border-radius: 4px;
          font-family: monospace;
          white-space: pre-wrap;
          word-break: break-all;
        }
      }
    }
  }
}
</style>