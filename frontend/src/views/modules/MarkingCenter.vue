<template>
  <div class="marking-center">
    <h1>评分中心</h1>
    <div class="module-content">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="exam-list">
            <template #header>
              <div class="card-header">
                <h3>待评阅考试</h3>
                <el-tag>{{ pendingExams.length }}个</el-tag>
              </div>
            </template>
            
            <el-menu
              :default-active="activeExamId"
              class="exam-menu"
              @select="handleExamSelect"
            >
              <el-menu-item
                v-for="exam in pendingExams"
                :key="exam.id"
                :index="exam.id"
              >
                <div class="exam-menu-item">
                  <span class="exam-name">{{ exam.name }}</span>
                  <el-tag size="small" :type="getProgressTagType(exam.progress)">
                    {{ exam.progress }}%
                  </el-tag>
                </div>
              </el-menu-item>
            </el-menu>
          </el-card>
        </el-col>

        <el-col :span="18">
          <template v-if="selectedExam">
            <el-card class="marking-area">
              <template #header>
                <div class="card-header">
                  <h3>{{ selectedExam.name }} - 评阅区</h3>
                  <div class="header-actions">
                    <el-button-group>
                      <el-button :disabled="!hasPrevious" @click="loadPrevious">上一份</el-button>
                      <el-button type="primary" :disabled="!hasNext" @click="loadNext">下一份</el-button>
                    </el-button-group>
                  </div>
                </div>
              </template>

              <div class="marking-content">
                <div class="student-info">
                  <el-descriptions :column="3" border>
                    <el-descriptions-item label="学号">{{ currentPaper.studentId }}</el-descriptions-item>
                    <el-descriptions-item label="姓名">{{ currentPaper.studentName }}</el-descriptions-item>
                    <el-descriptions-item label="班级">{{ currentPaper.className }}</el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="answer-review">
                  <div
                    v-for="question in currentPaper.questions"
                    :key="question.id"
                    class="question-item"
                  >
                    <div class="question-header">
                      <span class="question-number">第{{ question.number }}题</span>
                      <span class="question-type">{{ question.type }}</span>
                      <span class="question-score">满分：{{ question.fullScore }}分</span>
                    </div>

                    <div class="question-content">
                      <div class="student-answer">
                        <h4>学生答案：</h4>
                        <div class="answer-content" v-html="sanitizeHTML(question.answer)"></div>
                      </div>

                      <div class="reference-answer">
                        <h4>参考答案：</h4>
                        <div class="answer-content" v-html="sanitizeHTML(question.referenceAnswer)"></div>
                      </div>

                      <div class="scoring">
                        <h4>评分：</h4>
                        <el-input-number
                          v-model="question.score"
                          :min="0"
                          :max="question.fullScore"
                          :step="0.5"
                          @change="handleScoreChange(question)"
                        />
                        <el-input
                          v-model="question.comment"
                          type="textarea"
                          placeholder="评语（可选）"
                          :rows="2"
                          class="comment-input"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div class="action-bar">
                  <el-button type="primary" @click="savePaper">保存</el-button>
                  <el-button type="success" @click="submitPaper">提交评阅</el-button>
                </div>
              </div>
            </el-card>
          </template>

          <template v-else>
            <el-empty description="请选择要评阅的考试" />
          </template>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import { sanitizeHTML } from '@/utils/sanitize'

export default defineComponent({
  name: 'MarkingCenter',
  setup() {
    const activeExamId = ref('')
    const pendingExams = ref([
      { id: '1', name: '2024春季计算机基础期末考试', progress: 45 },
      { id: '2', name: '软件工程期末考试', progress: 80 },
      { id: '3', name: '数据结构期中考试', progress: 20 }
    ])

    const selectedExam = ref(null)
    const currentPaper = ref({
      studentId: '2024001',
      studentName: '张三',
      className: '计算机2401班',
      questions: [
        {
          id: '1',
          number: 1,
          type: '简答题',
          fullScore: 10,
          answer: '操作系统是计算机系统的核心软件，负责管理计算机硬件和软件资源...',
          referenceAnswer: '操作系统是计算机系统最基本的系统软件，它管理计算机硬件和软件资源...',
          score: 8,
          comment: '回答基本正确，但缺少一些关键点'
        },
        {
          id: '2',
          number: 2,
          type: '编程题',
          fullScore: 20,
          answer: 'def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr',
          referenceAnswer: 'def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        swapped = False\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n                swapped = True\n        if not swapped:\n            break\n    return arr',
          score: 15,
          comment: '实现正确但效率可以优化'
        }
      ]
    })

    const hasPrevious = ref(false)
    const hasNext = ref(true)

    const getProgressTagType = (progress: number) => {
      if (progress >= 80) return 'success'
      if (progress >= 40) return 'warning'
      return 'info'
    }

    const handleExamSelect = (examId: string) => {
      activeExamId.value = examId
      selectedExam.value = pendingExams.value.find(exam => exam.id === examId)
      // 这里应该加载选中考试的第一份试卷
    }

    const handleScoreChange = (question: any) => {
      console.log('分数改变:', question)
    }

    const loadPrevious = () => {
      console.log('加载上一份试卷')
    }

    const loadNext = () => {
      console.log('加载下一份试卷')
    }

    const savePaper = () => {
      console.log('保存当前评阅结果')
    }

    const submitPaper = () => {
      console.log('提交当前评阅结果')
    }

    return {
      activeExamId,
      pendingExams,
      selectedExam,
      currentPaper,
      hasPrevious,
      hasNext,
      getProgressTagType,
      handleExamSelect,
      handleScoreChange,
      loadPrevious,
      loadNext,
      savePaper,
      submitPaper,
      sanitizeHTML
    }
  }
})
</script>

<style lang="scss" scoped>
.marking-center {
  padding: 20px;

  h1 {
    margin-bottom: 20px;
    color: #303133;
  }

  .module-content {
    min-height: calc(100vh - 140px);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      color: #409EFF;
    }
  }

  .exam-menu {
    border-right: none;

    .exam-menu-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;

      .exam-name {
        flex: 1;
        margin-right: 10px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  .marking-content {
    .student-info {
      margin-bottom: 20px;
    }

    .answer-review {
      .question-item {
        margin-bottom: 30px;
        border: 1px solid #DCDFE6;
        border-radius: 4px;

        .question-header {
          background-color: #F5F7FA;
          padding: 10px;
          border-bottom: 1px solid #DCDFE6;
          display: flex;
          gap: 20px;

          .question-number {
            font-weight: bold;
          }

          .question-type {
            color: #909399;
          }

          .question-score {
            color: #F56C6C;
          }
        }

        .question-content {
          padding: 15px;

          h4 {
            margin: 0 0 10px 0;
            color: #606266;
          }

          .answer-content {
            background-color: #F5F7FA;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            white-space: pre-wrap;
            font-family: monospace;
          }

          .scoring {
            display: flex;
            flex-direction: column;
            gap: 10px;

            .comment-input {
              margin-top: 10px;
            }
          }
        }
      }
    }

    .action-bar {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid #DCDFE6;
    }
  }
}
</style>