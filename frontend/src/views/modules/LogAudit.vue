<template>
  <div class="log-audit">
    <h1>日志审计</h1>
    <div class="module-content">
      <el-card class="filter-card">
        <div class="filter-form">
          <el-form :model="filterForm" inline>
            <el-form-item label="日志类型">
              <el-select v-model="filterForm.action_type" placeholder="选择日志类型" clearable>
                <el-option
                  v-for="item in logActionTypes"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="时间范围">
              <el-date-picker
                v-model="dateRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
              />
            </el-form-item>

            <el-form-item label="IP地址">
              <el-input v-model="filterForm.ip_address" placeholder="输入IP地址" clearable />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="searchLogs" :loading="isLoading">搜索</el-button>
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
          </div>
        </template>

        <el-table :data="logs" style="width: 100%" v-loading="isLoading">
          <el-table-column prop="action_time" label="时间" width="180" />
          <el-table-column prop="action_type_display" label="类型" width="100" />
          <el-table-column prop="status" label="结果" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作用户" width="120">
            <template #default="{ row }">
              {{ row.user ? row.user.username : 'System' }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="日志内容" show-overflow-tooltip />
          <el-table-column prop="ip_address" label="IP地址" width="150" />
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
            <span class="label">时间:</span>
            <span class="value">{{ selectedLog.action_time }}</span>
          </div>
          <div class="detail-item">
            <span class="label">类型:</span>
            <span class="value">{{ selectedLog.action_type_display }}</span>
          </div>
          <div class="detail-item">
            <span class="label">结果:</span>
            <span class="value">
              <el-tag :type="getStatusTagType(selectedLog.status)">
                {{ selectedLog.status }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">操作用户:</span>
            <span class="value">{{ selectedLog.user ? selectedLog.user.username : 'System' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">操作对象:</span>
            <span class="value">{{ selectedLog.target_model }} (ID: {{ selectedLog.target_id }})</span>
          </div>
          <div class="detail-item">
            <span class="label">IP地址:</span>
            <span class="value">{{ selectedLog.ip_address }}</span>
          </div>
          <div class="detail-item full-width">
            <span class="label">日志内容:</span>
            <div class="value message">{{ selectedLog.description }}</div>
          </div>
          <div class="detail-item full-width">
            <span class="label">设备信息:</span>
            <pre class="value details">{{ selectedLog.user_agent }}</pre>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { getLogs, exportLogs, Log } from '@/api/log';
import { ElMessage } from 'element-plus';

export default defineComponent({
  name: 'LogAudit',
  setup() {
    const filterForm = ref({
      action_type: '',
      action_time__gte: '',
      action_time__lte: '',
      user: '',
      ip_address: ''
    });

    const dateRange = ref<[Date, Date] | null>(null);

    const logActionTypes = [
        { value: 'login', label: '用户登录' },
        { value: 'logout', label: '用户登出' },
        { value: 'create', label: '创建操作' },
        { value: 'update', label: '更新操作' },
        { value: 'delete', label: '删除操作' },
        { value: 'export', label: '导出操作' },
        { value: 'import', label: '导入操作' },
        { value: 'system', label: '系统事件' },
        { value: 'error', label: '错误日志' },
    ];

    const logs = ref<Log[]>([]);
    const isLoading = ref(false);
    const currentPage = ref(1);
    const pageSize = ref(10);
    const total = ref(0);
    const logDetailVisible = ref(false);
    const selectedLog = ref<Log | null>(null);

    const searchLogs = async () => {
        isLoading.value = true;

        const params = { ...filterForm.value };
        if (dateRange.value) {
            params.action_time__gte = dateRange.value[0].toISOString();
            params.action_time__lte = dateRange.value[1].toISOString();
        } else {
            delete params.action_time__gte;
            delete params.action_time__lte;
        }

        try {
            const response = await getLogs(params);
            logs.value = response;
            total.value = response.length; // Assuming no pagination from API for now
        } catch (error) {
            ElMessage.error('获取日志失败');
            console.error(error);
        } finally {
            isLoading.value = false;
        }
    };

    const resetFilter = () => {
      filterForm.value = {
        action_type: '',
        action_time__gte: '',
        action_time__lte: '',
        user: '',
        ip_address: ''
      };
      dateRange.value = null;
      searchLogs();
    };

    const handleExportLogs = async () => {
        try {
            const blob = await exportLogs(filterForm.value);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'logs.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            ElMessage.success('导出成功');
        } catch (error) {
            ElMessage.error('导出失败');
            console.error(error);
        }
    };

    onMounted(searchLogs);

    const getStatusTagType = (status: string) => {
      return status === 'success' ? 'success' : 'danger';
    };

    const viewLogDetail = (log: Log) => {
      selectedLog.value = log;
      logDetailVisible.value = true;
    };

    const handleSizeChange = (val: number) => {
      pageSize.value = val;
      // searchLogs(); // Re-enable if API supports pagination
    };

    const handleCurrentChange = (val: number) => {
      currentPage.value = val;
      // searchLogs(); // Re-enable if API supports pagination
    };

    return {
      filterForm,
      dateRange,
      logActionTypes,
      logs,
      isLoading,
      currentPage,
      pageSize,
      total,
      logDetailVisible,
      selectedLog,
      searchLogs,
      resetFilter,
      exportLogs: handleExportLogs,
      getStatusTagType,
      viewLogDetail,
      handleSizeChange,
      handleCurrentChange
    };
  }
});
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